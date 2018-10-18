# -*- coding: utf-8 -*-

'''
Import_IPT.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

import os, FreeCAD, FreeCADGui, importerBRep, importerSAT
from olefile           import OleFileIO
from importerUtils     import *
from importerReader    import *
from importerFreeCAD   import FreeCADImporter, createGroup
from importerSAT       import readEntities, importModel, convertModel

def ReadIgnorable(fname, data):
	logInfo(u'    IGNORED!')

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

	if (len(stream)>0):
		if (len(fname) == 1):
			logInfo(u"%2d: %s", counter, path)
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
						setDescription(getProperty(props, 29))
					elif (name == '\x05Qm0qv30hP3udrkgvAaitm1o20d'):
						ReadOtherProperties(props, fname, Private_Model_Information)
					elif (name == '\x05Ynltsm4aEtpcuzs1Lwgf30tmXf'):
						ReadOtherProperties(props, fname, Inventor_User_Defined_Properties)
					else:
						ReadOtherProperties(props, fname)
			elif (name == 'UFRxDoc'):
#				ReadUFRxDoc(stream)
				ReadIgnorable(fname, stream)
			elif (name == 'Protein'):
#				ReadProtein(stream)
				ReadIgnorable(fname, stream)
			else:
				ReadIgnorable(fname, stream)
		elif (fname[0]=='CacheGraphics'):
			skip(stream)
		elif (fname[0]=='RSeStorage'):
			if (isEmbeddings(fname)):
				if (name == 'Workbook'):
					ReadWorkbook(doc, stream, fname[-2], name)
				else:
					skip(stream)
			else:
				if (name.startswith('M')):
					fnameB = []
					for n in (fname):
						fnameB.append(n)
					fnameB[-1] = 'B' + name[1:]
					seg = ReadRSeMetaDataM(stream, name[1:])
					seg.file = name[1:]
					seg.index = counter
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
	logAlways(u"%2d: %s size=%s", counter, path, len(stream))

def read(doc, filename, readProperties):
	global model

	ole = OleFileIO(filename)
	setInventorFile(filename)
	setFileVersion(ole)
	setThumbnail(ole)
	chooseImportStrategy()

	elements = ole.listdir(streams=True, storages=False)

	counter = 1
	list = []
	for fname in elements:
		#ensure RSeDb is the very first "file" to be parsed
		if (fname[-1] == 'RSeDb'):
			stream = ole.openstream(fname).read()
			ReadRSeDb(stream)
		elif (fname[-1] == 'RSeSegInfo'):
			stream = ole.openstream(fname).read()
			if ((model.RSeDb is None) or (model.RSeDb.version != 0x1D)):
				ReadRSeSegInfo1F(stream)
			else:
				ReadRSeSegInfo1D(stream)
		elif (fname[-1] == 'RSeDbRevisionInfo'):
			stream = ole.openstream(fname).read()
			ReadRSeDbRevisionInfo(stream)
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

	logInfo(u"Dumped data to folder: '%s'", filename[0:-4])

	return True

def create3dModel(root, doc):
	global model
	if (model):
		storage = model.RSeStorageData
		strategy = getStrategy()
		if (strategy == STRATEGY_NATIVE):
			dc = model.getDC()
			if (dc is not None):
				creator = FreeCADImporter()
				creator.importModel(root, doc, dc)
		else:
			brep = model.getBRep()
			importerSAT._fileName = getInventorFile()
			if (brep is not None):
				for asm in brep.AcisList:
					readEntities(asm)
					if (strategy == STRATEGY_SAT):
						importModel(root, doc)
					elif (strategy == STRATEGY_STEP):
						convertModel(root, doc)

	return
