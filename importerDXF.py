# -*- coding: utf-8 -*-

import io, os, Acis, importerSAT

from importerUtils import setDumpFolder, getDumpFolder, chooseImportStrategyAcis, STRATEGY_SAT, STRATEGY_STEP, STRATEGY_NATIVE
from dxfgrabber    import readfile
from importerSAT   import dumpSat, importModel, convertModel
from Acis          import setReader, setVersion, AcisReader
from dxfgrabber.dxfentities import Body

_3dSolids = []

def _getSatFileName(name):
	return  os.path.join(getDumpFolder(), "%s.sat" %(name))

def read(filename):
	global _3dSolids

	_3dSolids = []

	setDumpFolder(filename)
	doc = readfile(filename)
	for entry in doc.entities:
		if (isinstance(entry, Body)):
			if (entry.is_sab):
				stream = io.BytesIO(entry.acis)
				reader = AcisReader(stream)
				reader.name = entry.handle
				if (reader.readBinary()):
					_3dSolids.append(reader)
			elif (entry.is_sat):
				sat = u"\n".join(entry.acis)
				stream = io.StringIO(sat)
				reader = AcisReader(stream)
				reader.name = entry.handle
				if (reader.readText()):
					_3dSolids.append(reader)
	return True

def create3dModel(group, doc):
	global _3dSolids

	strategy = chooseImportStrategyAcis()
	for reader in _3dSolids:
		setReader(reader)
		if (strategy in (STRATEGY_SAT, STRATEGY_NATIVE)):
			importModel(group)
		elif (strategy == STRATEGY_STEP):
			convertModel(group, doc.Name)
		satFile = _getSatFileName(reader.name)
		if (not os.path.exists(satFile)):
			dumpSat(satFile, reader, False)
		setReader(None)
	return
