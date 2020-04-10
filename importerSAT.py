# -*- coding: utf-8 -*-

'''
importerSAT.py:
Collection of classes necessary to read and analyse Autodesk (R) Invetor (R) files.
'''

import tokenize, sys, FreeCAD, Part, re, Acis, traceback, datetime, ImportGui
from importerUtils import logInfo, logWarning, logError, getUInt8A, getUInt32, chooseImportStrategyAcis, STRATEGY_SAT, setDumpFolder
from Acis2Step     import export
from math          import fabs

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

LENGTH_TEXT = re.compile('[ \t]*(\d+) +(.*)')

TokenTranslations = {
	'0x0A':       0x0A,
	'0x0B':       0x0B,
	'reversed':   0x0A,
	'forward':    0x0B,
	'reverse_v':  0x0A,
	'forward_v':  0x0B,
	'in':         0x0A,
	'out':        0x0B,
	'double':     0x0A,
	'single':     0x0B,
	'rotate':     0x0A,
	'no_rotate':  0x0B,
	'reflect':    0x0A,
	'no_reflect': 0x0B,
	'shear':      0x0A,
	'no_shear':   0x0B,
	'F':          0x0A,
	'I':          0x0B,
	'{':          0x0F,
	'}':          0x10,
	'#':          0x11
}

lumps = 0
wires = 0

_fileName = None

_entities = None

class Tokenizer(object):
	def __init__(self, content):
		self.content = content
		self.pos = 0
	def hasNext(self):
		return self.pos < len(self.content)
	def skipWhiteSpace(self):
		while (self.hasNext()):
			if (not self.content[self.pos] in ' \t\n\b\f'):
				break
			self.pos += 1
	def findEnd(self):
		while (self.hasNext()):
			if (self.content[self.pos] in ' \t\n\b\f#(){}'):
				break
			self.pos += 1
	def isSingleChar(self):
		if (self.hasNext()):
			return (self.content[self.pos] in '#(){}')
		return False
	def getNextToken(self):
		self.skipWhiteSpace()
		if (self.isSingleChar()):
			token = self.content[self.pos]
			self.pos += 1
		else:
			start = self.pos
			self.findEnd()
			token = self.content[start:self.pos] if (start < self.pos) else None
		return token
	def translateToken(self, token):
		if (token.startswith('@')):
			count = int(token[1:])
			self.skipWhiteSpace()
			text = self.content[self.pos:self.pos+count]
			self.pos += count + 1
			return Acis.TAG_UTF8_U16, text
		if (token.startswith('$')):
			ref = int(token[1:])
			return Acis.TAG_ENTITY_REF, Acis.AcisRef(ref)
		if (token == '('):
			tokX  = self.getNextToken()
			tokY  = self.getNextToken()
			tokZ  = self.getNextToken()
			if (tokZ == ')'): return Acis.TAG_VECTOR_2D, [float(tokX), float(tokY)]
			dummy = self.getNextToken()
			assert (dummy == ')'), "Expected ')' but found '%s'!" %(dummy)
			return Acis.TAG_VECTOR_3D, [float(tokX), float(tokY), float(tokZ)]
		tag = TokenTranslations.get(token, None)
		val = token
		if (tag is None):
			tag = Acis.TAG_UTF8_U8
			try:
				val = float(val)
				tag = Acis.TAG_DOUBLE
			except:
				pass
		return tag, val

def int2version(num):
	return float("%d.%d" %(num / 100, num % 100))

def getEntities():
	global _entities
	return _entities

def setEntities(entities):
	global _entities
	if (entities is None):
		if (_entities is not None):
			del _entities[:]
		Acis.clearEntities()
	_entities = entities

def resolveHistoryLink(history, ref):
	if (ref.index >= 0):
		return Acis.AcisRef(ref.index, history.delta_states[ref.index])
	return Acis.AcisRef(ref.index)

class Header(object):
	def __init__(self):
		self.version = 7.0
		self.records = 0
		self.bodies  = 0
		self.flags   = 0
		self.prodId  = 'FreeCAD'
		self.prodVer = "%s.%s  Build: %s" %(FreeCAD.ConfigGet('BuildVersionMajor'), FreeCAD.ConfigGet('BuildVersionMinor'), FreeCAD.ConfigGet('BuildRevision'))
		self.date    = datetime.datetime.now().strftime("%a, %b %d %H:%M:%S %Y")
		self.scale   = 1.0
		self.resabs  = 1e-06
		self.resnor  = 1e-10

	def __str__(self):
		sat = "%d %d %d %d\n" %(int(self.version * 100), self.records, self.bodies, self.flags)
		sat += "%d %s %d %s %d %s\n" %(len(self.prodId), self.prodId, len(self.prodVer), self.prodVer, len(self.date), self.date)
		sat += "%g %g %g\n" %(self.scale, self.resabs, self.resnor)
		return sat

	def readText(self, file):
		data   = file.readline()
		tokens   = data.replace('\r', '').replace('\n', '').split(' ')
		self.version = int2version(int(tokens[0]))
		self.records = int(tokens[1])
		self.bodies  = int(tokens[2])
		self.flags   = int(tokens[3])
		if (self.version >= 2.0):
			data = file.readline()
			self.prodId, data = getNextText(data)
			self.prodVer, data = getNextText(data)
			self.date, data = getNextText(data)
			data = file.readline()
			tokens = data.split(' ')
			self.scale  = fabs(float(tokens[0])) # prevent STEP importer from handling negative scales -> "Cannot compute Inventor representation for the shape of Part__Feature"
			self.resabs = float(tokens[1])
			self.resnor = float(tokens[2])
			if (self.version > 24.0):
				file.readline() # skip T @52 E94NQRBTUCKCWQWFE_HB5PSXH48CGGNH9CMMPASCFADVJGQAYC84
			Acis.setScale(self.scale)
			logInfo(u"    product: '%s'", self.prodId)
			logInfo(u"    version: '%s'", self.prodVer)
			logInfo(u"    date:    %s",   self.date)
		if (self.prodId == 'Inventor'):
			Acis.setVersion(7.0)
		else:
			Acis.setVersion(self.version)
		return
	def readBinary(self, data):
		if (data[0:16] == b'ACIS BinaryFile('):
#			c, i = Acis.readNextSabChunk(data, 0)
#			self.version = c.val
#			c, i = Acis.readNextSabChunk(data, i)
#			self.records = c.val
#			c, i = Acis.readNextSabChunk(data, i)
#			self.bodies  = c.val
#			c, i = Acis.readNextSabChunk(data, i)
#			self.flags   = c.val
			self.version = 100
			c, i = Acis.readNextSabChunk(data, 0x1F)
		else:
			self.version = 700
			c, i = Acis.readNextSabChunk(data, 0)
		self.prodId  = c.val
		c, i = Acis.readNextSabChunk(data, i)
		self.prodVer = c.val
		c, i = Acis.readNextSabChunk(data, i)
		self.date    = c.val
		c, i = Acis.readNextSabChunk(data, i)
		self.scale   = c.val
		c, i = Acis.readNextSabChunk(data, i)
		self.resabs  = c.val
		c, i = Acis.readNextSabChunk(data, i)
		self.resnor  = c.val
		self.version = int2version(self.version)
		logInfo(u"    product: '%s'", self.prodId)
		logInfo(u"    version: '%s'", self.prodVer)
		logInfo(u"    date:    %s",   self.date)
		Acis.setVersion(self.version)
		return i

class Bulletin(object):
	def __init__(self, old, new):
		self.old = old
		self.new = new
	def __str__(self):
		if (self.old.index == -1):
			return u"$-1   $%-4d // inserted:   %s" %(self.new.index, self.new.entity)
		if (self.new.index == -1):
			return u"$%-4d $-1   // deleted:    %s" %(self.old.index, self.old.entity)
		return u"$%-4d $%-4d // updated id: %s" %(self.old.index, self.new.index, self.new.entity)
	def __repr__(self):
		return str(self)

class BulletinBoard(object):
	def __init__(self, owner, number):
		super(BulletinBoard, self).__init__()
		self.owner  = owner
		self.number = number
		self.bulletins = []
	def __str__(self):
		return u"BulletinBoard: %d" %(self.number)
	def __repr__(self):
		return str(self)

class DeltaState(object):
	def __init__(self, history, entity, entities):
		super(DeltaState, self).__init__()
		self.history = history
		self.index = entity.index
		chunks = entity.chunks
		self.id       , i = Acis.getInteger(chunks, 0) # Number of this state
		self.rollbacks, i = Acis.getInteger(chunks, i) # Number of states that can be rolled back
		self.hidden   , i = Acis.getInteger(chunks, i)
		self.previous , i = Acis.getValue(chunks, i)   # previous delta state with respect to roll back
		self.next     , i = Acis.getValue(chunks, i)   # next delta state with respect to roll back
		self.partner  , i = Acis.getValue(chunks, i)   # partner delta state; if no branches, points to itself
		self.merged   , i = Acis.getValue(chunks, i)   # delta state this is merged with
		self.owner    , i = Acis.getValue(chunks, i)   # the owner stream
		self.unknown  , i = Acis.getValue(chunks, i)   # == 0x0B
		self.bulletin_boards = []
		next, i = Acis.getInteger(chunks, i)
		while (next):
			bb = BulletinBoard(chunks[i].val, chunks[i+1].val)
			self.bulletin_boards.append(bb)
			next, i = Acis.getInteger(chunks, i + 2)
			while (next):
				refOld = chunks[i+0].val
				if (refOld.index >= 0): refOld.entity = entities[refOld.index]
				refNew = chunks[i+1].val
				if (refNew.index >= 0): refNew.entity = entities[refNew.index]
				b = Bulletin(refOld, refNew)
				bb.bulletins.append(b)
				next, i = Acis.getInteger(chunks, i + 2)
			next, i = Acis.getInteger(chunks, i)
	def getPrevious(self): return self.previous.entity
	def getNext(self):     return self.next.entity
	def getPartner(self):  return self.partner.entity
	def getMerged(self):   return self.merged.entity
	def resolveLinks(self):
		self.previous = resolveHistoryLink(self.history, self.previous)
		self.next     = resolveHistoryLink(self.history, self.next)
		self.partner  = resolveHistoryLink(self.history, self.partner)
		self.merged   = resolveHistoryLink(self.history, self.merged)
	def __str__(self):
		return u"delta_state %d %d %d %s %s %s %s %s %s" %(self.id, self.rollbacks, self.hidden, self.previous, self.next, self.partner, self.merged, self.owner, self.unknown)
	def __repr__(self):
		return u"%d delta_state %d %d %d %s %s %s %s %s %s" %(self.index, self.id, self.rollbacks, self.hidden, self.previous, self.next, self.partner, self.merged, self.owner, self.unknown)

class History(object):
	def __init__(self, entity):
		super(History, self).__init__()
		entity.index = -1
		self.history_stream , i = Acis.getValue(entity.chunks, 0)
		self.current_state  , i = Acis.getInteger(entity.chunks, i) # current delta_state
		self.next_state     , i = Acis.getInteger(entity.chunks, i) # next state to with respect to roll back
		self.keep_max_states, i = Acis.getInteger(entity.chunks, i) # max number of states to keep
		self.unknown        , i = Acis.getInteger(entity.chunks, i)
		self.ds_current     , i = Acis.getValue(entity.chunks, i)   # current delta state, a.k. "working state"
		self.ds_root        , i = Acis.getValue(entity.chunks, i)   # root delta state
		self.ds_active      , i = Acis.getValue(entity.chunks, i)   # the most recent delta state
		self.attribute      , i = Acis.getValue(entity.chunks, i)   # history's attributes.
		self.delta_states = {}
	def resolveDeltaStates(self, entities):
		for key in self.delta_states:
			entity = self.delta_states[key]
			ds = DeltaState(self, entity, entities)
			self.delta_states[key] = ds
		self.ds_current = resolveHistoryLink(self, self.ds_current)
		self.ds_root    = resolveHistoryLink(self, self.ds_root)
		self.ds_active  = resolveHistoryLink(self, self.ds_active)
		for key in self.delta_states:
			ds = self.delta_states[key]
			ds.resolveLinks()
	def getRoot(self):
		return self.ds_root.entity
	def __str__(self):
		return "SAT %s: %d %d %d %d %s %s %s %s" %(self.history_stream, self.current_state, self.next_state, self.keep_max_states, self.unknown, self.ds_current, self.ds_root, self.ds_active, self.attribute)
	def __repr__(self):
		return "%s: %d %d %d %d %s %s %s %s" %(self.history_stream, self.current_state, self.next_state, self.keep_max_states, self.unknown, self.ds_current, self.ds_root, self.ds_active, self.attribute)

def getNextText(data):
	m = LENGTH_TEXT.match(data)
	count = int(m.group(1))
	text  = m.group(2)[0:count]
	remaining = m.group(2)[count+1:]
	return text, remaining

def readEntityBinary(data, index, end):
	names = []
	eIndex = -1
	c, i = Acis.readNextSabChunk(data, index)
	if (c.tag not in (Acis.TAG_IDENT, Acis.TAG_SUBIDENT)):
		eIndex = c.val
		c, i = Acis.readNextSabChunk(data, i)
	names.append(c.val)
	while (c.tag != Acis.TAG_IDENT):
		c, i = Acis.readNextSabChunk(data, i)
		if (c.val == 'ASM'): c.val = 'ACIS'
		names.append(c.val)

	entity = Acis.AcisEntity('-'.join(names))
	entity.index = eIndex
	if (not entity.name.startswith('End-of-')):
		while ((c.tag != Acis.TAG_TERMINATOR) and (i < end)):
			c, i = Acis.readNextSabChunk(data, i)
			if (c is not None):
				entity.chunks.append(c)

	return entity, i

def readEntityText(tokenizer, index):
	id = index
	name = tokenizer.getNextToken()
	if (name is None):
		return None, id
	if (name.startswith('-')):
		id = int(name[1:])
		name = tokenizer.getNextToken()
	entity = Acis.AcisEntity(name)
	entity.index = id
	while (tokenizer.hasNext()):
		token = tokenizer.getNextToken()
		if (token):
			tag, val = tokenizer.translateToken(token)
			entity.add(tag, val)
			if (tag == Acis.TAG_TERMINATOR):
				break;

	return entity, id + 1

def resolveEntityReferences(entities, lst, history):
#	progress = FreeCAD.Base.ProgressIndicator()
#	progress.start("Resolving references...", len(lst))
	map = entities
	for entity in lst:
#		progress.next()
		if (entity.name == "Begin-of-ACIS-History-Data"):
			if (history is None):
				map = {}
			else:
				map = history.delta_states
		elif (entity.name == "End-of-ACIS-History-Section"):
			map = entities
		for chunk in entity.chunks:
			if (chunk.tag == Acis.TAG_ENTITY_REF):
				ref = chunk.val
				try:
					ref.entity = map[ref.index]
				except:
					ref.entity = None
#	progress.stop()
	return

def resolveNode(entity):
	try:
		if (len(entity.name) > 0):
			return Acis.createNode(entity)
	except Exception as e:
		logError(u"ERROR: Can't resolve '%s' - %s", entity, e)
	return

def resolveSurfaceRefs(face):
	refs  = face.getSurfaceRefs()
	srfs  = face.getSurfaceDefinitions()
	j = 0

	for ref in refs:
		if (Acis.subtypeTableSurfaces.get(ref) is None):
			id = -1
			n = 0
			while (j < len(srfs)):
				s = srfs[j]
				if ((id == -1) or (s.index == id)):
					Acis.addSubtypeNodeSurface(s, ref + n)
					j += 1
					n += 1
					id = s.index
				else:
					break

def resolveNodes():
	Acis.init()
	bodies = []
	faces  = []
	model = getEntities()
	for entity in model:
		node = resolveNode(entity)
		if (entity.name == 'body'):
			bodies.append(node)
		elif (entity.name == 'face'):
			faces.append(node)

	# try to resolve surface references...
	for face in faces:
		resolveSurfaceRefs(face)

	return bodies

_currentColor = (0xBE/255.0, 0xBE/255.0, 0xBE/255.0)
def setCurrentColor(entity):
	if (entity is not None):
		color = entity.getColor()
		if (color is not None):
			global _currentColor
			_currentColor = color

def createBody(root, name, shape, transform):
	if (shape is not None):
		body = FreeCAD.ActiveDocument.addObject("Part::Feature", name)
		if (root is not None):
			root.addObject(body)
		body.Shape = shape
		if (transform is not None):
			body.Placement = transform.getPlacement()

def buildFaces(shells, root, name, transform):
	faces = []
	i = 1
	for shell in shells:
		for face in shell.getFaces():
			surface = face.build()
			if (surface is not None):
				faces.append(surface)
				createBody(root, "%s_%d" %(name, i), surface, transform)
				i += 1
		for wire in shell.getWires():
			buildWire(root, wire, transform)

	if (len(faces) > 0):
		logInfo(u"    ... %d face(s)!", len(faces))
#		shell = faces[0] if (len(faces) == 1) else Part.Shell(faces)
#		createBody(root, name, shell, transform)

	return

def buildWires(coedges, root, name, transform):
	edges = []

	for index in coedges:
		coedge = coedges[index]
		edge = coedge.build()
		if (edge is not None):
			edges.append(edge)

	if (len(edges) > 0):
		logInfo(u"        ... %d edges!", len(edges))
		createBody(root, name, edges[0].fuse(edges[1:]) if (len(edges) > 1) else edges[0], transform)
	return

def buildLump(root, lump, transform):
	global lumps
	lumps += 1
	name = "Lump%02d" %lumps
	logInfo(u"    building lump '%s'...", name)

	setCurrentColor(lump)

	buildFaces(lump.getShells(), root, name, transform)

	return True

def buildWire(root, wire, transform):
	global wires
	wires += 1
	name = "Wire%02d" %wires
	logInfo(u"    building wire '%s'...", name)

	buildWires(wire.getCoEdges(), root, name, transform)

	return True

def buildBody(root, node):
	if (node.index >= 0 ):
		transform = node.getTransform()
		setCurrentColor(node)

		for lump in node.getLumps():
			buildLump(root, lump, transform)
		for wire in node.getWires():
			buildWire(root, wire, transform)
	return

def importModel(root):
	global lumps, wires
	wires = 0
	lumps = 0
	bodies = resolveNodes()
	for body in bodies:
		buildBody(root, body)

	return

def convertModel(group, docName):
	global _fileName
	header = Acis.getHeader()
	bodies = resolveNodes()
	stepfile = export(_fileName, header, bodies)
	ImportGui.insert(stepfile, docName)

def readText(fileName):
	global _fileName

	_fileName = fileName
	setDumpFolder(fileName)
	header    = Header()
	history   = None
	index     = 0
	entities  = {}
	map       = entities
	lst       = []

	Acis.setHeader(header)
	Acis.clearEntities()

	with open(fileName, 'rU') as file:
		header.readText(file)
		content   = file.read()
		#TODO: add progress indicator for reading file for len(content)
		#progress = FreeCAD.Base.ProgressIndicator()
		#progress.start("Reading file...", len(content)) # that locks python console, so use with scripts only
		tokenizer = Tokenizer(content)
		while (tokenizer.hasNext()):
			entity, index = readEntityText(tokenizer, index)
			if (entity):
				#TODO: update progress indocator for tokenizer.pos
				if (entity.index < 0): entity.index = index
				map[entity.index] = entity
				lst.append(entity)
				if (entity.name == "Begin-of-ACIS-History-Data"):
					del map[entity.index]
					entityIdx = entity.index
					entity.index = -1
					history = History(entity)
					index = 0
					map = history.delta_states
				elif (entity.name == "End-of-ACIS-History-Section"):
					del map[entity.index]
					entity.index = -1
					index = entityIdx
					map = entities
				elif (entity.name == "End-of-ACIS-data"):
					del map[entity.index]
					entity.index = -1
		#progress.stop() # DONE reading file
	resolveEntityReferences(entities, lst, history)
	setEntities(lst)
	return True

def readBinary(fileName):
	global _fileName

	_fileName = fileName
	setDumpFolder(fileName)
	header    = Header()
	history   = None
	index     = 0
	entities  = {}
	map       = entities
	lst       = []

	Acis.setHeader(header)
	Acis.clearEntities()

	with open(fileName, 'rb') as file:
		data = file.read()
		e = len(data)
		i = header.readBinary(data)
		index = 0
		entities = {}
		while (i < e):
			entity, i = readEntityBinary(data, i, e)
			entity.index = index
			entities[index] = entity
			index += 1
			lst.append(entity)
			if (entity.name == "Begin-of-ACIS-History-Data"):
				del map[entity.index]
				entityIdx = entity.index
				entity.index = -1
				history = History(entity)
				index = 0
				map = history.delta_states
			elif (entity.name == "End-of-ACIS-History-Section"):
				del map[entity.index]
				entity.index = -1
				index = entityIdx
				map = entities
			elif (entity.name == "End-of-ACIS-data"):
				entity.index = -1
				try:
					del map[entity.index]
				except:
					pass
				break
	resolveEntityReferences(entities, lst, history)
	setEntities(lst)
	return True

def create3dModel(group, doc):
	strategy = chooseImportStrategyAcis()
	if (strategy == STRATEGY_SAT):
		importModel(group)
	else:
		convertModel(group, doc.Name)
	setEntities(None)
	Acis.setHeader(None)
	return

def readEntities(asm):
	header, lst, history = asm.get('SAT')
	Acis.setHeader(header)
	setEntities(lst)
	bodies = 0
	for entity in lst:
		if (entity.name == "body"):
			bodies += 1
	header.bodies  = bodies
	Acis.setScale(header.scale)
	return
