# -*- coding: utf-8 -*-

import io, os

from importerUtils import setDumpFolder, getDumpFolder, chooseImportStrategyAcis, STRATEGY_SAT, STRATEGY_STEP, STRATEGY_NATIVE
from importerSAT   import dumpSat, importModel, convertModel
from Acis          import setReader, AcisReader
from ezdxf         import readfile
from ezdxf.entities.acis import Solid3d

_3dSolids = []

def _getSatFileName(name):
	return  os.path.join(getDumpFolder(), "%s.sat" %(name))

def __is_binary__(entry):
	return hasattr(entry, 'sab') and len(getattr(entry, 'sab'))>0

def __is_text__(entry):
	return hasattr(entry, 'sat') and len(getattr(entry, 'sat'))>0

def __read_binary__(sab, name):
	global _3dSolids
	stream = io.BytesIO(sab)
	reader = AcisReader(stream)
	if (reader.readBinary()):
		reader.name = name
		_3dSolids.append(reader)

def __read_text__(sat, name):
	global _3dSolids
	stream = io.StringIO('\n'.join(sat))
	reader = AcisReader(stream)
	if (reader.readText()):
		reader.name = name
		_3dSolids.append(reader)

def read(filename):
	global _3dSolids

	_3dSolids = []
	name      = os.path.basename(os.path.splitext(filename)[0])
	i         = 0

	setDumpFolder(filename)
	doc = readfile(filename)
	for entry in doc.entities:
		if (__is_binary__(entry)):
			__read_binary__(entry.sab, '%s_%d' %(name, i))
			i += 1
		elif (__is_text__(entry)):
			__read_text__(entry.sat, '%s_%d' %(os.path.basename(os.path.splitext(filename)[0]), i))
			i += 1
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
