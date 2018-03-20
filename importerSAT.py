# -*- coding: utf8 -*-

'''
importerSAT.py:
Collection of classes necessary to read and analyse Autodesk (R) Invetor (R) files.
'''

import tokenize, sys, FreeCAD, Part, re, Acis, traceback, datetime
from importerUtils import LOG, logMessage, logWarning, logError, viewAxonometric

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

LENGTH_TEXT = re.compile('[ \t]*(\d+) +(.*)')
NEXT_TOKEN  = re.compile('[ \t]*([^ \t]+) +(.*)')
lumps = 0
wires = 0

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
		sat += "%d %s %d %s %d %s\n" %(len(self.prodId), prodId, len(self.prodVer), prodVer, lend(self.date), self.date)
		sat += "%g %g %g\n" %(self.scale, self.resabs, self.resnor)

	def read(self, file):
		data   = file.readline()
		tokens   = data.replace('\r', '').replace('\n', '').split(' ')
		self.version = float(tokens[0]) / 100.0
		self.records = int(tokens[1])
		self.bodies  = int(tokens[2])
		self.flags   = int(tokens[3])
		logMessage("Reading ACIS file version %s" %(self.version), LOG.LOG_INFO)
		if (self.version > 1.0):
			data = file.readline()
			self.prodId, data = getNextText(data)
			self.prodVer, data = getNextText(data)
			self.date, data = getNextText(data)
			logMessage("    product: %s" %(self.prodId), LOG.LOG_INFO)
			logMessage("    version: %s" %(self.prodVer), LOG.LOG_INFO)
			logMessage("    date: %s" %(self.date), LOG.LOG_INFO)
			data = file.readline()
			tokens = data.split(' ')
			self.scale  = float(tokens[0])
			Acis.setScale(self.scale)
			self.resabs = float(tokens[1])
			self.resnor = float(tokens[2])
			if (self.version > 24.0):
				file.readline() # skip T @52 E94NQRBTUCKCWQWFE_HB5PSXH48CGGNH9CMMPASCFADVJGQAYC84

class AcisChunk():
	def __init__(self, key, val):
		self.key = key
		self.val = val
		self.str = '@'

	def __str__(self):
		if (self.key == 0x04): return "%d "      %(self.val)
		if (self.key == 0x06): return "%g "      %(self.val)
		if (self.key == 0x07): return "%s%d %s " %(self.str, len(self.val), self.val)# STRING
		if (self.key == 0x08): return "%s"       %(self.val)                         # STRING
		if (self.key == 0x0A): return "%s "      %(self.val)
		if (self.key == 0x0B): return "%s "      %(self.val)
		if (self.key == 0x0C): return "%s "      %(self.val)                         # ENTITY_POINTER
		if (self.key == 0x0D): return "%s "      %(self.val)                         # CLASS_IDENTIFYER
		if (self.key == 0x0E): return "%s-"      %(self.val)                         # SUBCLASS_IDENTIFYER
		if (self.key == 0x0F): return "%s "      %(self.val)                         # SUBTYP_START
		if (self.key == 0x10): return "%s "      %(self.val)                         # SUBTYP_END
		if (self.key == 0x11): return "%s\n"     %(self.val)                         # TERMINATOR
		if (self.key == 0x12): return "%s%d %s " %(self.str, len(self.val), self.val)# STRING
		if (self.key == 0x13): return "(%s) "      %(" ".join(["%g" %(f) for f in self.val]))
		if (self.key == 0x14): return "(%s) "      %(" ".join(["%g" %(f) for f in self.val])) # somthing to do with scale
		if (self.key == 0x15): return "%d "      %(self.val)
		if (self.key == 0x16): return "(%s) "      %(" ".join(["%g" %(f) for f in self.val]))
		return ''

class AcisEntity():
	def __init__(self, name):
		self.chunks = []
		self.name   = name
		self.index  = -1
		self.node   = None
		Acis.addEntity(self)

	def add(self, key, val):
		self.chunks.append(AcisChunk(key, val))
	def getStr(self):
		return "-%d %s %s" %(self.index, self.name,''.join('%s' %c for c in self.chunks))
	def __str__(self):
		return self.getStr() if (self.index != -1) else ""

class AcisRef():
	def __init__(self, index):
		self.index = index
		self.entity = None

	def __str__(self):
		if (self.entity is None or self.entity.index < 0):
			return "$%d" % self.index
		return "$%d" %(self.entity.index)

def getNextText(data):
	m = LENGTH_TEXT.match(data)
	count = int(m.group(1))
	text  = m.group(2)[0:count]
	remaining = m.group(2)[count+1:]
	return text, remaining

def getNextToken(data):
	m = NEXT_TOKEN.match(data)
	if (m is not None):
		token = m.group(1)
		remaining = m.group(2)
		return token, remaining
	return '', ''

def readEntity(line, i):
	index = i
	token, data = getNextToken(line)
	if (token.startswith('-')):
		index = int(token[1:])
		name, data = getNextToken(data)
	else:
		name = token
	entity = AcisEntity(name)
	entity.index = index
	while (len(data) > 0):
		token, data = getNextToken(data)
		if (token.startswith('@')):
			count = int(token[1:])
			text = data[0:count]
			data = data[count + 1:]
			entity.add(0x08, text)
		elif (token == '0x0A'):
			entity.add(0x0A, token)
		elif (token == '0x0B'):
			entity.add(0x0B, token)
		elif (token.startswith('(')):
			tok1, data = getNextToken(data)
			tok2, data = getNextToken(data)
			assert tok2.endswith(')'), "Expected ')' but found '%s'!" %(dummy.val)
			entity.add(0x13, [float(token[1:]), float(tok1), float(tok2[:-1])])
		elif (token == 'reversed'):
			entity.add(0x0A, token)
		elif (token == 'reverse_v'):
			entity.add(0x0A, token)
		elif (token == 'in'):
			entity.add(0x0A, token)
		elif (token == 'double'):
			entity.add(0x0A, token)
		elif (token == 'rotate'):
			entity.add(0x0A, token)
		elif (token == 'reflect'):
			entity.add(0x0A, token)
		elif (token == 'shear'):
			entity.add(0x0A, token)
		elif (token == 'F'):
			entity.add(0x0A, token)
		elif (token == 'forward'):
			entity.add(0x0B, token)
		elif (token == 'forward_v'):
			entity.add(0x0B, token)
		elif (token == 'out'):
			entity.add(0x0B, token)
		elif (token == 'single'):
			entity.add(0x0B, token)
		elif (token == 'no_rotate'):
			entity.add(0x0B, token)
		elif (token == 'no_reflect'):
			entity.add(0x0B, token)
		elif (token == 'no_shear'):
			entity.add(0x0B, token)
		elif (token == 'I'):
			entity.add(0x0B, token)
		elif (token.startswith('$')):
			entity.add(0x0C, AcisRef(int(token[1:])))
		elif (token.startswith('{')):
			entity.add(0x0F, token)
		elif (token.startswith('}')):
			entity.add(0x10, token)
		else:
			try:
				entity.add(0x06, float(token))
			except:
				entity.add(0x07, token)

	entity.add(0x11, '#')

	return entity, index + 1

def resolveEntityReferences(entities, lst):
	for entity in lst:
		for chunk in entity.chunks:
			if (chunk.key == 0x0C):
				ref = chunk.val
				if (ref.index >= 0):
					ref.entity = entities[ref.index]
	return

def resolveNode(entity, version):
	try:
		type = entity.name
		if (len(type) > 0):
			node = Acis.createNode(entity.index, type, entity, version)
	except Exception as e:
		logError("Can't resolve '%s' - %s" %(entity, e))
		logError('>E: ' + traceback.format_exc())
	return

def resolveNodes(model, version):
	Acis.references = {}
	bodies = []
	for entity in model:
		resolveNode(entity, version)
		if (entity.name == "body"):
			bodies.append(entity)
	return bodies

def getName(attrib):
	name = ''
	a = attrib
	while (a is not None) and (a.getIndex() >= 0):
		if (a.__class__.__name__ == "AttribGenName"):
			return a.text
		a = a.getNext()
	return name

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
			surfaces = face.build(doc)
			if (len(surfaces) > 0):
				faces += surfaces
			for f in surfaces:
				createBody(doc, root, "%s_%d" %(name, i), f, transform)
				i += 1

	if (len(faces) > 0):
		logMessage("    ... %d face(s)!" %(len(faces)), LOG.LOG_INFO)
#		shell = faces[0] if (len(faces) == 1) else Part.Shell(faces)
#		createBody(doc, root, name, shell, transform)

	return

def buildWires(coedges, doc, root, name, transform):
	edges = []

	for coedge in coedges:
		edge = coedge.build(doc)
		if (edge is not None): edges.append(edge)

	if (len(edges) > 0):
		logMessage("    ... %d edges!" %(len(edges)), LOG.LOG_INFO)
		wires = [Part.Wire(cluster) for cluster in Part.getSortedClusters(edges)]
		createBody(doc, root, name, wires[0].fuse(wires[1:]) if (len(wires) > 1) else wires[0], transform)

	return

def buildLump(root, doc, lump, transform):
	global lumps
	lumps += 1
	name = "Lump%02d" %lumps
	logMessage("    building lump '%s'..." %(name), LOG.LOG_INFO)

	buildFaces(lump.getShells(), doc, root, name, transform)

	return True

def buildWire(root, doc, wire, transform):
	global wires
	wires += 1
	name = "Wire%02d" %wires
	logMessage("    building wire '%s'..." %(name), LOG.LOG_INFO)

	buildWires(wire.getCoEdges(), doc, root, name)
	buildFaces(wire.getShells(), doc, root, name)

	return True

def buildBody(root, doc, entity):
	if (entity.index >= 0 ):
		node = entity.node
		transform = node.getTransform()
		for lump in node.getLumps():
			buildLump(root, doc, lump, transform)
		for wire in node.getWires():
			buildWire(root, doc, wire, transform)
	return

def importModel(root, doc, model, header):
	global lumps, wires
	wires = 0
	lumps = 0
	bodies = resolveNodes(model, header.version)
	for body in bodies:
		buildBody(root, doc, body)

	return

def read(doc, fileName):
	entities = {}
	lst      = []
	index    = 0
	Acis.clearEntities()

	with open(fileName, 'rU') as file:
		header = Header()
		header.read(file)
		data = file.read().replace('\n', '').replace('\r', '').split('#')

		for line in data:
			entity, index = readEntity(line, index)
			lst.append(entity)
			entities[entity.index] = entity
	resolveEntityReferences(entities, lst)
	importModel(None, doc, lst, header)

	viewAxonometric(doc)

	return

def getHeader(asm):
	header = Header()
	lst = asm.get('SAT')
	header.version = 7.0 # all Inventor Versions uses internally ACIS-Version 7.0!
	header.records = 0
	header.bodies  = -1 # TODO count all bodies in lst
	header.flags   = 0
	header.prodId  = lst[0].val
	header.prodVer = lst[1].val
	header.date    = lst[2].val
	header.scale   = lst[3].val
	header.resabs  = lst[4].val
	header.resnor  = lst[5].val
	Acis.setScale(header.scale)
	return header, lst[6:]

