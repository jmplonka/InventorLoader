# -*- coding: utf-8 -*-

'''
importerSAT.py:
Collection of classes necessary to read and analyse Autodesk (R) Invetor (R) files.
'''

import tokenize, sys, FreeCAD, Part, re, Acis, traceback, datetime, ImportGui
from importerUtils import logInfo, logWarning, logError, viewAxonometric, getUInt8A, chooseImportStrategyAcis, STRATEGY_SAT
from Acis          import AcisRef, AcisEntity, readNextSabChunk
from Acis2Step     import export
from math          import fabs

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

LENGTH_TEXT = re.compile('[ \t]*(\d+) +(.*)')
NEXT_TOKEN  = re.compile('[ \t]*([^ \t]+) +(.*)')
lumps = 0
wires = 0

_fileName = None

class Tokenizer():
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
			return 0x08, text
		if (token.startswith('$')):
			ref = int(token[1:])
			return 0x0C, AcisRef(ref)
		if (token == '('):
			tokX  = self.getNextToken()
			tokY  = self.getNextToken()
			tokZ  = self.getNextToken()
			dummy = self.getNextToken()
			assert (dummy == ')'), "Expected ')' but found '%s'!" %(dummy)
			return 0x13, [float(tokX), float(tokY), float(tokZ)]
		tag = TokenTranslations.get(token, None)
		val = token
		if (tag is None):
			tag = 0x07
			try:
				val = float(val)
				tag = 0x06
			except:
				pass
		return tag, val

def int2version(num):
	return float("%d.%d" %(num / 100, num % 100))

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

_entities = None
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

_header = None
def getHeader():
	global _header
	return _header
def setHeader(header):
	global _header
	_header = header

class Header():
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
		Acis.setVersion(self.version)
		return
	def readBinary(self, data):
		tag, self.version, i = readNextSabChunk(data, 0)
		tag, self.records, i = readNextSabChunk(data, i)
		tag, self.bodies, i  = readNextSabChunk(data, i)
		tag, self.flags, i   = readNextSabChunk(data, i)
		tag, self.prodId, i  = readNextSabChunk(data, i)
		tag, self.prodVer, i = readNextSabChunk(data, i)
		tag, self.date, i    = readNextSabChunk(data, i)
		tag, self.scale, i   = readNextSabChunk(data, i)
		tag, self.resabs, i  = readNextSabChunk(data, i)
		tag, self.resnor, i  = readNextSabChunk(data, i)
		self.version = int2version(self.version)
		logInfo(u"    product: '%s'", self.prodId)
		logInfo(u"    version: '%s'", self.prodVer)
		logInfo(u"    date:    %s",   self.date)
		Acis.setVersion(self.version)
		return i

def getNextText(data):
	m = LENGTH_TEXT.match(data)
	count = int(m.group(1))
	text  = m.group(2)[0:count]
	remaining = m.group(2)[count+1:]
	return text, remaining

def readEntityBinary(data, index, end):
	names = []
	eIndex = -1
	tag, val, i = readNextSabChunk(data, index)
	if (not tag in (0x0D, 0x0E)):
		eIndex = val
		tag, val, i = readNextSabChunk(data, i)
	names.append(val)
	while (tag != 0x0D):
		tag, val, i = readNextSabChunk(data, i)
		if (val == 'ASM'): val = 'ACIS'
		names.append(val)

	entity = AcisEntity('-'.join(names))
	entity.index = eIndex
	if (not entity.name.startswith('End-of-')):
		while ((tag != 0x11) and (i < end)):
			tag, val, i = readNextSabChunk(data, i)
			entity.add(tag, val)

	return entity, i

def readEntityText(tokenizer, index):
	id = index
	name = tokenizer.getNextToken()
	if (name is None):
		return None, id
	if (name.startswith('-')):
		id = int(name[1:])
		name = tokenizer.getNextToken()
	entity = AcisEntity(name)
	entity.index = id
	while (tokenizer.hasNext()):
		token = tokenizer.getNextToken()
		if (token):
			tag, val = tokenizer.translateToken(token)
			entity.add(tag, val)
			if (tag == 0x11):
				break;

	return entity, id + 1

def resolveEntityReferences(entities, lst):
	progress = FreeCAD.Base.ProgressIndicator()
	progress.start("Resolving references...", len(lst))
	for entity in lst:
		progress.next()
		for chunk in entity.chunks:
			if (chunk.tag == 0x0C):
				ref = chunk.val
				try:
					ref.entity = entities[ref.index]
				except:
					ref.entity = None
	progress.stop()
	return

def resolveNode(entity):
	try:
		if (len(entity.name) > 0):
			return Acis.createNode(entity)
	except Exception as e:
#		logError(u"ERROR: Can't resolve '%s' - %s", entity, e)
		logError(traceback.format_exc())
	return

def resolveNodes():
	Acis.init()

	bodies = []
	faces  = []
	model = getEntities()
	for entity in model:
		if (entity.valid):
			node = resolveNode(entity)
			if (entity.name == 'body'):
				bodies.append(entity)
			elif (entity.name == 'face'):
				faces.append(node)

	# try to resolve surface references...
	for face in faces:
		refs  = face.getSurfaceRefs()
		srfs  = face.getSurfaceDefinitions()
		j = 0
		for ref in refs:
			if (Acis.subtypeTableSurfaces.get(ref) is None):
				id = -1
				n = 0
				while (j < len(srfs)):
					s = srfs[j]
					if ((id == -1) or (s.getIndex() == id)):
						Acis.addSubtypeNodeSurface(s, ref + n)
						j += 1
						n += 1
						id = s.getIndex()
					else:
						break
	return bodies

_currentColor = (0xBE/255.0, 0xBE/255.0, 0xBE/255.0)
def setCurrentColor(entity):
	if (entity is not None):
		color = entity.getColor()
		if (color is not None):
			global _currentColor
			_currentColor = color

def createBody(doc, root, name, shape, transform):
	if (shape is not None):
		body = doc.addObject("Part::Feature", name)
		if (root is not None):
			root.addObject(body)
		body.Shape = shape
		if (transform is not None):
			body.Placement = transform.getPlacement()

def buildFaces(shells, doc, root, name, transform):
	faces = []
	i = 1
	for shell in shells:
		for face in shell.getFaces():
			surface = face.build(doc)
			if (surface is not None):
				faces.append(surface)
				createBody(doc, root, "%s_%d" %(name, i), surface, transform)
				i += 1
		for wire in shell.getWires():
			buildWire(root, doc, wire, transform)

	if (len(faces) > 0):
		logInfo(u"    ... %d face(s)!", len(faces))
#		shell = faces[0] if (len(faces) == 1) else Part.Shell(faces)
#		createBody(doc, root, name, shell, transform)

	return

def buildWires(coedges, doc, root, name, transform):
	edges = []

	for coedge in coedges:
		edge = coedge.build(doc)
		if (edge is not None):
			edges.append(edge)

	if (len(edges) > 0):
		logInfo(u"        ... %d edges!", len(edges))
		createBody(doc, root, name, edges[0].fuse(edges[1:]) if (len(edges) > 1) else edges[0], transform)
	return

def buildLump(root, doc, lump, transform):
	global lumps
	lumps += 1
	name = "Lump%02d" %lumps
	logInfo(u"    building lump '%s'...", name)

	setCurrentColor(lump)

	buildFaces(lump.getShells(), doc, root, name, transform)

	return True

def buildWire(root, doc, wire, transform):
	global wires
	wires += 1
	name = "Wire%02d" %wires
	logInfo(u"    building wire '%s'...", name)

	buildWires(wire.getCoEdges(), doc, root, name, transform)
	buildFaces(wire.getShells(), doc, root, name, transform)

	return True

def buildBody(root, doc, entity):
	if (entity.index >= 0 ):
		node = entity.node
		transform = node.getTransform()
		setCurrentColor(node)

		for lump in node.getLumps():
			buildLump(root, doc, lump, transform)
		for wire in node.getWires():
			buildWire(root, doc, wire, transform)
	return

def importModel(root, doc):
	global lumps, wires
	wires = 0
	lumps = 0
	bodies = resolveNodes()
	for body in bodies:
		buildBody(root, doc, body)

	return

def convertModel(group, doc):
	global _fileName
	header = getHeader()
	bodies = resolveNodes()
	stepfile = export(_fileName, header, bodies)
	ImportGui.insert(stepfile, doc.Name)

def readText(doc, fileName):
	global _fileName
	_fileName = fileName
	header = Header()
	entities = {}
	lst      = []
	index    = 0
	valid    = True
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
			#TODO: update progress indocator for tokenizer.pos
			if (entity is not None):
				lst.append(entity)
				entities[entity.index] = entity
				if (entity.name == "Begin-of-ACIS-History-Data"):
					valid = False
				if (entity.name == "End-of-ACIS-data"):
					valid = False
				entity.valid = valid
		#progress.stop() # DONE reading file
	resolveEntityReferences(entities, lst)
	setHeader(header)
	setEntities(lst)
	return True

def readBinary(doc, fileName):
	global _fileName
	_fileName = fileName
	header = Header()
	entities = {}
	lst      = []
	index    = 0
	Acis.clearEntities()

	with open(fileName, 'rU') as file:
		data = file.read()
		header.readBinary(data)
		index = 0
		entities = {}
		while (i < e):
			entity, i = readEntityBinary(data, i, e)
			entity.index = index
			entities[index] = entity
			lst.append(entity)
			index += 1
			if (entity.name == "End-of-ACIS-data"):
				entity.index = -2
				break
	resolveEntityReferences(entities, lst)
	setHeader(header)
	setEntities(lst)
	return

def create3dModel(group, doc):
	strategy = chooseImportStrategyAcis()
	if (strategy == STRATEGY_SAT):
		importModel(group, doc)
	else:
		convertModel(group, doc)
	viewAxonometric()
	setEntities(None)
	setHeader(None)
	return

def readEntities(asm):
	header, lst = asm.get('SAT')
	setHeader(header)
	setEntities(lst)
	bodies = 0
	for entity in lst:
		if (entity.name == "body"):
			bodies += 1
	header.bodies  = bodies
	Acis.setScale(header.scale)
	return
