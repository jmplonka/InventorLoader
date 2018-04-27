# -*- coding: utf-8 -*-

'''
Import_IPT.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

import os, FreeCAD, FreeCADGui, importerBRep, importerSAT
from olefile           import isOleFile, OleFileIO
from importerUtils     import *
from importerReader    import *
from importerFreeCAD   import FreeCADImporter, createGroup

def ReadIgnorable(fname, data):
	logMessage("\t>>> IGNORED: %r" % ('/'.join(fname)))
#	logMessage(HexAsciiDump(data), LOG.LOG_DEBUG)
	return len(data)

def skip(data):
	return

def ReadElement(ole, fname, doc, counter, readProperties):
	name = fname[-1]
	if (len(fname) > 1):
		parent = fname[-2]
	else:
		parent = ''
	path = PrintableName(fname)
	stream = ole.openstream(fname).read()

	folder = getInventorFile()[0:-4]

	if (len(stream)>0):
#		if (name.startswith('\x01') or name.startswith('\x02') or name.startswith('\x05')):
#			binFile = open ('%s\\%s.bin' %(folder, name[1:]), 'wb')
#		else:
#			binFile = open ('%s\\%s.bin' %(folder, name), 'wb')
#			binFile.write(stream)
#			binFile.close()

		if (len(fname) == 1):
			logMessage("%2d: %s" % (counter, path), LOG.LOG_DEBUG)
			if (name.startswith('\x05')):
				if (readProperties):
					props = ole.getproperties(fname, convert_time=True)
					if (name == '\x05Aaalpg0m0wzvuhc41dwauxbwJc'):
						ReadInventorDocumentSummaryInformation(doc, props, fname)
					elif (name == '\x05Zrxrt4arFafyu34gYa3l3ohgHg'):
						ReadInventorSummaryInformation(doc, props, fname)
					elif (name == '\x05Qz4dgm1gRjudbpksAayal4qdGf'):
						ReadOtherProperties(props, fname, Design_Tracking_Control)
					elif (name == '\x05PypkizqiUjudbposAayal4qdGf'):
						ReadOtherProperties(props, fname, Design_Tracking_Properties)
					elif (name == '\x05Qm0qv30hP3udrkgvAaitm1o20d'):
						ReadOtherProperties(props, fname, Private_Model_Information)
					elif (name == '\x05Ynltsm4aEtpcuzs1Lwgf30tmXf'):
						ReadOtherProperties(props, fname, Inventor_User_Defined_Properties)
					else:
						ReadOtherProperties(props, fname)
			elif (name == 'UFRxDoc'):
				ReadUFRxDoc(stream)
			elif (name == 'Protein'):
				ReadProtein(stream)
			else:
				ReadIgnorable(fname, stream)
		elif (fname[0]=='CacheGraphics'):
			skip(stream)
		elif (fname[0]=='RSeStorage'):
			if (isEmbeddings(fname)):
				if (name.startswith('\x05')):
					# ReadOtherProperties(ole.getproperties(fname, convert_time=True), fname)
					skip(stream)
				elif (name == '\x01Ole'):
#					ReadRSeEmbeddingsOle(stream)
					skip(stream)
				elif (name == '\x01CompObj'):
					ReadRSeEmbeddingsCompObj(stream)
				elif (name == 'DatabaseInterfaces'):
					ReadRSeEmbeddingsDatabaseInterfaces(stream)
				elif (name == 'Contents'):
#					ReadRSeEmbeddingsContents(stream)
					skip(stream)
				elif (name == 'Workbook'):
					ReadWorkbook(doc, stream, fname[-2], name)
				else:
					ReadIgnorable(fname, stream)
			else:
				if (name == 'RSeDb'):
					ReadRSeDb(stream)
				elif (name == 'RSeSegInfo'):
					if ((model) and (model.RSeDb) and (model.RSeDb.version == 0x1D)):
						ReadRSeSegInfo1D(stream)
					else:
						ReadRSeSegInfo1F(stream)
				elif (name == 'RSeDbRevisionInfo'):
					ReadRSeDbRevisionInfo(stream)
				elif (name.startswith('B')):
					# Skip! will be handled in 'M'
					skip(stream)
				elif (name.startswith('M')):
					fnameB = []
					for n in (fname):
						fnameB.append(n)
					fnameB[-1] = 'B' + name[1:]
					seg = ReadRSeMetaDataM(stream, name[1:])
					dataB = ole.openstream(fnameB).read()
					ReadRSeMetaDataB(dataB, seg)
				else:
					ReadIgnorable(fname, stream)
		else:
			ReadIgnorable(fname, stream)

	return

def ListElement(ole, fname, counter):
	name = fname[-1]

	path = PrintableName(fname)
	stream = ole.openstream(fname).read()
	logMessage("%2d: %s size=%s" % (counter, path, len(stream)), LOG.LOG_ALWAYS)

def read(doc, filename, readProperties):
	first = 0
	list = {}
	counters = {}

	# LOG.LOG_FILTER = LOG.LOG_FILTER | LOG.LOG_DEBUG
	if (isOleFile(filename)):
		setInventorFile(filename)
		ole = OleFileIO(filename)
		setFileVersion(ole)
		setThumbnail(ole)
		strategy = chooseImportStrategy()

		elements = ole.listdir(streams=True, storages=False)

		counter = 1
		list = []
		for fname in elements:
			if (len(fname) == 1):
				list.append(fname)
			else:
				#Ensure that RSe* files will be parsed first
				if (fname[-1].startswith('RSe')):
					#ensure RSeDb is the very first "file" to be parsed
					list.insert(first, fname)
					if (fname[-1] == 'RSeDb'):
						first += 1
				elif (not fname[-1].startswith('B')):
					list.append(fname)

		for fname in list:
			ReadElement(ole, fname, doc, counter, readProperties)
			counter += 1
		ole.close()

		now = datetime.datetime.now()
		if (len(doc.Comment) > 0):
			doc.Comment += '\n'
		doc.Comment = '# %s: read from %s' %(now.strftime('%Y-%m-%d %H:%M:%S'), filename)

		logMessage("Dumped data to folder: '%s'" %(filename[0:-4]), LOG.LOG_INFO)

		return True
	logError("Error - '%s' is not a valid Autodesk Inventor file." %(filename))
	return False

def create3dModel(root, doc):
	global model
	if (model):
		storage = model.RSeStorageData
		strategy = getStrategy()
		if (strategy == STRATEGY_NATIVE):
			dc = FreeCADImporter.findDC(storage)
			if (dc is not None):
				creator = FreeCADImporter()
				creator.importModel(root, doc, dc)
		elif (strategy == STRATEGY_SAT):
			brep = FreeCADImporter.findBRep(storage)
			if (brep):
				for asm in brep.AcisList:
					importerSAT.readEntities(asm)
					importerSAT.importModel(root, doc)
		else:
			logError("WRONG STRATEGY!")

	viewAxonometric(doc)

	return
