#!/usr/bin/env python
"""
Import_IPT.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) files.
"""

import FreeCAD
import FreeCADGui
import Spreadsheet
from importerClasses import *
from importerReader  import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

def ReadIgnorable(fname, data):
	logMessage('\t>>> IGNORED: %r' % ('/'.join(fname)))
	StdoutWriteChunked(HexAsciiDump(data))
	return len(data)

def skip(data):
	return len(data)

def ReadElement(ole, fname, doc, readProperties):
	end = 0

	name = fname[-1]
	if (len(fname) > 1):
		parent = fname[-2]
	else:
		parent = ''
	path = PrintableName(fname)
	stream = ole.openstream(fname).read()
	if (len(fname) == 1):
		if (name.startswith('\x05')):
			if (readProperties):
				if (name == '\x05Aaalpg0m0wzvuhc41dwauxbwJc'):
					ReadInventorDocumentSummaryInformation(doc, ole.getproperties(fname, convert_time=True), fname)
				elif (name == '\x05Zrxrt4arFafyu34gYa3l3ohgHg'):
					ReadInventorSummaryInformation(doc, ole.getproperties(fname, convert_time=True), fname)
				else:
					ReadOtherProperties(ole.getproperties(fname, convert_time=True), fname)
			end = len(stream)
		elif (name == 'UFRxDoc'):
			end = ReadUFRxDoc(stream)
		elif (name == 'Protein'):
			end = ReadProtein(stream)
		else:
			end = ReadIgnorable(fname, stream)
	elif (fname[0]=='CacheGraphics'):
		end = skip(stream)
	elif (fname[0]=='RSeStorage'):
		if (isEmbeddings(fname)):
			if (name.startswith('\x05')):
				end = skip(stream)
			elif (name == '\x01Ole'):
#				end = ReadRSeEmbeddingsOle(stream)
				end = skip(stream)
			elif (name == '\x01CompObj'):
				end = ReadRSeEmbeddingsCompObj(stream)
			elif (name == 'DatabaseInterfaces'):
				end = ReadRSeEmbeddingsDatabaseInterfaces(stream)
			elif (name == 'Contents'):
				end = skip(stream)
			elif (name == 'Workbook'):
				end = ReadWorkbook(doc, stream, fname[-2], name)
			else:
				logMessage('%2d: %s' % (counter, path))
				end = ReadIgnorable(fname, stream)
		else:
			if (name == 'RSeDb'):
				end = ReadRSeDb(stream)
			elif (name == 'RSeSegInfo'):
				if (model.RSeDb.version == 0x1D):
					end = ReadRSeSegInfo1D(stream)
				else:
					end = ReadRSeSegInfo1F(stream)
			elif (name == 'RSeDbRevisionInfo'):
				end = ReadRSeDbRevisionInfo(stream)
			elif (name.startswith('B')):
				# Skip! will be handled in 'ReadRSeStorageData'
				end = skip(stream)
			elif (name.startswith('M')):
				fnameB = []
				for n in (fname):
					fnameB.append(n)
				fnameB[-1] = 'B' + name[1:]
				end = ReadRSeStorageData(stream, ole.openstream(fnameB).read(), fnameB[-1])
			else:
				end = ReadIgnorable(fname, stream)
	else:
		end = ReadIgnorable(fname, stream)


def analyseModel(doc):
	global model
	sketches = {}
	if (model is None):
		return

	segInfo = model.RSeSegInfo
	if (segInfo is None):
		return

	if (SEG_PM_GRAPHICS in segInfo.segments):
		pmGraphics = segInfo.segments[SEG_PM_GRAPHICS]
	elif (SEG_AM_GRAPHICS in segInfo.segments):
		pmGraphics = segInfo.segments[SEG_AM_GRAPHICS]
	else:
		pmGraphics = None

	if (pmGraphics is not None):
		for node in pmGraphics.nodes:
			index = node.index
			item1 = segInfo.uidList1[node.indexSegList1]
			item2 = segInfo.uidList2[node.indexSegList2]
			# node.value
			# node.number
			if ((item2 == 'UCxWorkaxisNode') or (item2 == 'UCxWorkpointNode')):
				logMessage('>>>Ignoring actions on Workplane!', LOG.LOG_INFO)
			elif (item1 == 'RDxPlanarSketch'):
				if (item1 not in sketches):
					name = 'Sketch%03d' % len(sketches)
					sketches[index] = name
					logMessage('>>>adding %s: %s' %(name, node), LOG.LOG_INFO)
				else:
					name = sketches[index]
			elif (item2 == 'SCxSketchNode'):
				if(item1 == 'RDxPoint2'):
					logMessage('\tdrawing Point: %s' %(node), LOG.LOG_INFO)
				elif(item1 == 'RDxLine2'):
					logMessage('\tdrawing Line: %s' %(node), LOG.LOG_INFO)
				elif(item1 == 'RDxArc2'):
					logMessage('\tdrawing Circle: %s' %(node), LOG.LOG_INFO)
				elif(item1 == 'RDxDistanceDimension2'):
					logMessage('\tadding  Constraint \'Distance\': %s' %(node), LOG.LOG_INFO)
				elif(item1 == 'RDxDiameter2'):
					logMessage('\tadding  Constraint \'Radius\': %s' %(node), LOG.LOG_INFO)
				else:
					logMessage('\tdown\'t know how to add %s: %s!' %(item1, node), LOG.LOG_INFO)
			else:
				logMessage('>>>down\'t know how to %s, %s: %s!' %(item1, item2, node), LOG.LOG_WARNING)
	else:
		logMessage('>>>INFO - No content to be displayed!', LOG.LOG_WARNING)

def ReadFile(doc, readProperties):
	first = 0
	list = {}
	counters = {}

	LOG.LOG_FILTER = LOG.LOG_FILTER | LOG.LOG_DEBUG

	if (olefile.isOleFile(getInventorFile())):
		ole = olefile.OleFileIO(getInventorFile())
		elements = ole.listdir(streams=True, storages=False)
		list = []

		for fname in elements:
			if (len(fname) == 1):
				list.append(fname)
			else:
				if (fname[-1].startswith('RSe')):
					list.insert(first, fname)
					if (fname[-1] == 'RSeDb'):
						first += 1
				elif (not fname[-1].startswith('B')):
					list.append(fname)

		for fname in list:
			ReadElement(ole, fname, doc, readProperties)
		ole.close()

		if (FreeCAD.GuiUp):
			FreeCADGui.SendMsgToActiveView("ViewFit")

		if (len(doc.Comment) > 0):
			doc.Comment += '\n'
		now = datetime.datetime.now()
		doc.Comment = '# %s: read from %s' %(now.strftime('%Y-%m-%d %H:%M:%S'), getInventorFile())
		doc.recompute()

		return True
	else:
		print >>sys.stderr, 'Error - %s is not a valid Autodesk Inventor file.' % infile
		return False

def insert(filename, docname, skip=[], only=[], root=None):
	"""
	opens an Autodesk Inventor file in the current document
	"""

	if (canImport()):
		doc = FreeCAD.getDocument(docname)
		print "Importing: %s" %(filename)

		setInventorFile(filename)

		if (ReadFile(doc, False)):
			print "DONE!"

def open(filename, skip=[], only=[], root=None):
	"""
	opens an Autodesk Inventor file in a new document
	In addtion to insert (import), the iProperties are as well added to the document.
	"""

	if (canImport()):
		print "Reading: %s" %(filename)
		docname = os.path.splitext(os.path.basename(filename))[0]
		docname = decode(docname, utf=True)
		doc = FreeCAD.newDocument(docname)
		doc.Label = docname

		setInventorFile(filename)
		
		if (ReadFile(doc, True)):
			print "DONE!"

