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

TokenTranslations = {
	'0x0A':       0x0A,
	'0x0B':       0x0B,
	'reversed':   0x0A,
	'reverse_v':  0x0A,
	'in':         0x0A,
	'double':     0x0A,
	'rotate':     0x0A,
	'reflect':    0x0A,
	'shear':      0x0A,
	'F':          0x0A,
	'forward':    0x0B,
	'forward_v':  0x0B,
	'out':        0x0B,
	'single':     0x0B,
	'no_rotate':  0x0B,
	'no_reflect': 0x0B,
	'no_shear':   0x0B,
	'I':          0x0B,
	'{':          0x0F,
	'}':          0x10,
	'#':          0x11
}
def translateToken(data, token):
	if (token.startswith('@')):
		count = int(token[1:])
		text = data[0:count]
		data = data[count + 1:]
		return data, 0x08, text
	if (token.startswith('$')):
		ref = int(token[1:])
		return data, 0x0C, AcisRef(ref)
	if (token == '('):
		tokX, data  = getNextToken(data)
		tokY, data  = getNextToken(data)
		tokZ, data  = getNextToken(data)
		dummy, data = getNextToken(data)
		assert (dummy == ')'), "Expected ')' but found '%s'!" %(dummy)
		return data, 0x13, [float(tokX), float(tokY), float(tokZ)]
	tag = TokenTranslations.get(token, None)
	val = token
	if (tag is None):
		tag = 0x07
		try:
			val = float(val)
			tag = 0x06
		except:
			pass
	return data, tag, val

_entities = None
def getEntities():
	global _entities
	return _entities
def setEntities(entites):
	global _entities
	_entities = entites

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
		self.tag = key
		self.val = val
		self.typ = '@'

	def __str__(self):
		if (self.tag == 0x04): return "%d "      %(self.val)
		if (self.tag == 0x06): return "%g "      %(self.val)
		if (self.tag == 0x07): return "%s%d %s " %(self.typ, len(self.val), self.val)# STRING
		if (self.tag == 0x08): return "%s"       %(self.val)                         # STRING
		if (self.tag == 0x0A): return "%s "      %(self.val)
		if (self.tag == 0x0B): return "%s "      %(self.val)
		if (self.tag == 0x0C): return "%s "      %(self.val)                         # ENTITY_POINTER
		if (self.tag == 0x0D): return "%s "      %(self.val)                         # CLASS_IDENTIFYER
		if (self.tag == 0x0E): return "%s-"      %(self.val)                         # SUBCLASS_IDENTIFYER
		if (self.tag == 0x0F): return "%s "      %(self.val)                         # SUBTYP_START
		if (self.tag == 0x10): return "%s "      %(self.val)                         # SUBTYP_END
		if (self.tag == 0x11): return "%s\n"     %(self.val)                         # TERMINATOR
		if (self.tag == 0x12): return "%s%d %s " %(self.typ, len(self.val), self.val)# STRING
		if (self.tag == 0x13): return "(%s) "      %(" ".join(["%g" %(f) for f in self.val]))
		if (self.tag == 0x14): return "(%s) "      %(" ".join(["%g" %(f) for f in self.val])) # somthing to do with scale
		if (self.tag == 0x15): return "%d "      %(self.val)
		if (self.tag == 0x16): return "(%s) "      %(" ".join(["%g" %(f) for f in self.val]))
		return ''

class AcisEntity():
	def __init__(self, name):
		self.chunks = []
		self.name   = name
		self.index  = -1
		self.node   = None

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
		if (token.startswith('{') and (len(token) > 1)):
			remaining = token[1:] + ' ' + m.group(2)
			token = '{'
		elif (token.endswith('}') and (len(token) > 1)):
			token = token[0:-1]
			remaining = '} ' + m.group(2)
		elif (token.startswith('(') and (len(token) > 1)):
			remaining = token[1:] + ' ' + m.group(2)
			token = '('
		elif (token.endswith(')') and (len(token) > 1)):
			token = token[0:-1]
			remaining = ') ' + m.group(2)
		else:
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
		data, tag, val = translateToken(data, token)
		entity.add(tag, val)

	entity.add(0x11, '#')

	return entity, index + 1

def resolveEntityReferences(entities, lst):
	for entity in lst:
		for chunk in entity.chunks:
			if (chunk.tag == 0x0C):
				ref = chunk.val
				if (ref.index >= 0):
					ref.entity = entities[ref.index]
	return

def resolveNode(entity, version):
	try:
		if (len(entity.name) > 0):
			Acis.createNode(entity.index, entity.name, entity, version)
	except Exception as e:
		logError("Can't resolve '%s' - %s" %(entity, e))
		logError('>E: ' + traceback.format_exc())
	return

def resolveNodes():
	Acis.references = {}
	bodies = []
	header = getHeader()
	model = getEntities()
	for entity in model:
		resolveNode(entity, header.version)
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

	buildWires(wire.getCoEdges(), doc, root, name, transform)
	buildFaces(wire.getShells(), doc, root, name, transform)

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

def importModel(root, doc):
	global lumps, wires
	wires = 0
	lumps = 0
	bodies = resolveNodes()
	for body in bodies:
		buildBody(root, doc, body)

	return

def read(doc, fileName):
	header = Header()
	entities = {}
	lst      = []
	index    = 0
	Acis.clearEntities()

	with open(fileName, 'rU') as file:
		header.read(file)
		data = file.read()
		lines = re.sub('[ \t\r\n]+', ' ', data).split('#')

		for line in lines:
			entity, index = readEntity(line, index)
			lst.append(entity)
			entities[entity.index] = entity
	resolveEntityReferences(entities, lst)
	setHeader(header)
	setEntities(lst)
	return

def create3dModel(group, doc):
	importModel(group, doc)
	viewAxonometric(doc)
	return

def readEntities(asm):
	header = Header()
	lst = asm.get('SAT')
	setHeader(header)
	setEntities(lst[6:])
	bodies = 0
	for entity in lst[6:]:
		if (entity.name == "body"):
			bodies += 1
	header.version = 7.0 # all Inventor Versions uses internally ACIS-Version 7.0!
	header.records = 0
	header.bodies  = bodies
	header.flags   = 0
	header.prodId  = lst[0].val
	header.prodVer = lst[1].val
	header.date    = lst[2].val
	header.scale   = lst[3].val
	header.resabs  = lst[4].val
	header.resnor  = lst[5].val
	Acis.setScale(header.scale)
	return
