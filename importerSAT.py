# -*- coding: utf-8 -*-

'''
importerSAT.py:
Collection of classes necessary to read and analyse Autodesk (R) Invetor (R) files.
'''

import os, sys, tokenize, FreeCAD, Part, re, traceback, datetime, ImportGui, io
from importerUtils   import logInfo, logWarning, logError, logAlways, getUInt8A, getUInt32, chooseImportStrategyAcis, STRATEGY_SAT, setDumpFolder, getDumpFolder
from Acis2Step       import export
from math            import fabs
from Acis            import TAG_ENTITY_REF, getReader, setReader, AcisReader, AcisChunkPosition, setVersion, createNode, init

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

lumps = 0
wires = 0

def _getSatFileName(name):
	return  os.path.join(getDumpFolder(), name)

def resolveEntityReferences(entities, lst, history):
#	progress = FreeCAD.Base.ProgressIndicator()
#	progress.start("Resolving references...", len(lst))
	map = entities
	for entity in lst:
#		progress.next()
		if (entity.name == "Begin-of-ACIS-History-Data"):
			map = history.delta_states # History shell never be None at this point!
		elif (entity.name == "End-of-ACIS-History-Section"):
			map = entities
		for chunk in entity.chunks:
			if (chunk.tag == TAG_ENTITY_REF):
				ref = chunk.val
				try:
					ref.entity = map[ref.index]
				except:
					ref.entity = None
#	progress.stop()
	return

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
	for shell in shells:
		for face in shell.getFaces():
			surface = face.build()
			if (surface):
				faces.append(surface)
		for wire in shell.getWires():
			buildWire(root, wire, transform)

	if (len(faces) > 0):
		shell = faces[0]
		if (len(faces) > 1):
			try:
				shell = Part.Shell(faces)
			except:
				try:
					shell = shell.fuse(faces[1:])
				except:
					shell = None
		if (shell):
			createBody(root, name, shell, transform)
		else:
			for face in faces:
				createBody(root, name, face, transform)
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

def resolveNodes(acis):
	global lumps, wires

	init()
	wires = 0
	lumps = 0
	bodies = []
	doAdd  = True
	setReader(acis)
	for entity in acis.getEntities():
		node = createNode(entity)
		if (node):
			if (doAdd and (entity.name == 'body')):
				bodies.append(node)
			if (entity.name in ['Begin-of-ACIS-History-Data', 'End-of-ACIS-data']):
				doAdd = False

	if (getDumpFolder()[-3:].lower() != 'sat'):
		name = _getSatFileName(acis.name)
		dumpSat(name, acis)

	return bodies

def importModel(root):
	global lumps, wires
	wires = 0
	lumps = 0

	acis = getReader()
	bodies = resolveNodes(acis)
	for body in bodies:
		buildBody(root, body)
	return

def convertModel(group, docName):
	acis = getReader()
	bodies = resolveNodes(acis)

	stepfile = export(acis.name, acis.header, bodies)
	ImportGui.insert(stepfile, docName)

def readText(fileName):
	global _fileName
	_fileName = fileName

	result = False
	setDumpFolder(fileName)
	with open(fileName, 'rU') as file:
		reader = AcisReader(file)
		reader.name, trash = os.path.splitext(os.path.basename(fileName))
		result = reader.readText()
	return result

def readBinary(fileName):
	global _fileName
	_fileName = fileName

	result = False
	setDumpFolder(fileName)
	with open(fileName, 'rb') as file:
		reader = AcisReader(file)
		reader.name, trash = os.path.splitext(os.path.basename(fileName))
		result = reader.readBinary()
	return result

def create3dModel(group, doc):
	strategy = chooseImportStrategyAcis()
	if (strategy == STRATEGY_SAT):
		importModel(group)
	else:
		convertModel(group, doc.Name)
	setReader(None)
	return

def dumpSat(name, acis, use_dump_folder = True):
	header     = acis.header
	history    = acis.history
	entities   = acis.getEntities()
	dumpFolder = getDumpFolder()
	historyIdx = None

	if (history):
		historyIdx = history.index

	if (dumpFolder):
		if (use_dump_folder):
			satFile = os.path.join(dumpFolder, "%s.sat" %(name))
		else:
			satFile = name
		with io.open(satFile, 'wt', encoding='utf-8') as sat:
			sat.write(header.__str__())
			for record in entities:
				if (record.index == historyIdx):
					sat.write(u"%r\n"%(history.getRecord()))
					for ds in history.delta_states:
						sat.write(u"%s\n"%(ds.getRecord()))
					sat.write(u"End-of-ACIS-History-Section\n")
				sat.write(u"%s\n"%(record))
			sat.write(u"End-of-ACIS-data\n")
	return
