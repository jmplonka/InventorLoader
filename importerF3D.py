# -*- coding: utf-8 -*-

from importerUtils   import *
from importerSAT     import dumpSat, importModel, convertModel, buildBody, resolveNodes
from Acis2Step       import export
from zipfile         import is_zipfile, ZipFile
from FreeCAD         import ParamGet
from Acis            import AcisReader
from importerFreeCAD import createGroup
from ImportGui       import insert

smb_files = []

def _set_thumbnail(f3d, path):
	result = False
	name = path.split('/')[-1]
	if (name):
		with f3d.open(path) as thunbnail:
			data = thunbnail.read()
			thumbnail = Thumbnail()
			thumbnail.setIconData(data)
			dumpFolder = getDumpFolder()
			if ((not (dumpFolder is None)) and ParamGet("User parameter:BaseApp/Preferences/Mod/InventorLoader").GetBool('Others.DumpThumbnails', True)):
				with open(u"%s/%s" %(dumpFolder, name), 'wb') as png:
					png.write(data)
			setThumbnail(thumbnail)
			result = True
	return result

def _dump_SMB(f3d, path):
	global smb_files
	result = False
	name = path.split('/')[-1]
	if (name):
		logAlways('    ... parsing \'%s\''%(path))
		with f3d.open(path) as stream:
			dumpFolder = getDumpFolder()
			if (not (dumpFolder is None)):
				with open('%s/%s' %(dumpFolder, name), 'wb') as sab:
					data = stream.read()
					sab.write(data)
		with f3d.open(path) as stream:
			reader = AcisReader(stream)
			reader.name = name
			result = reader.readBinary()
			if (result):
				dumpSat(name[0:name.rfind('.')], reader)
				if (name[-4:].lower() != 'smbh'):
					smb_files.append(reader)
	return result

def read_manifest(f3d, path):
	name = path.split('/')[-1]
	if (name):
		with f3d.open(path) as manifest:
			data = manifest.read()
			t1,  i = getLen32Text8(data, 0)
			t2,  i = getLen32Text8(data, i) # fusion doc type
			t3,  i = getLen32Text16(data, i) # .f3d
			t4,  i = getLen32Text16(data, i) # Fusion Document
			t5,  i = getLen32Text16(data, i) # A Fusion Document
			t6,  i = getLen32Text16(data, i) # UID
			t7,  i = getLen32Text16(data, i) # UID
			a1,  i = getUInt32A(data, i, 2) # ???
			cnt, i = getUInt32(data, i)
			l1 = []
			for j in range(cnt):
				t, i = getLen32Text8(data, i)
				v, i = getUInt32(data, i)
				l1.append((t, v))
			cnt, i = getUInt32(data, i)
			l2 = []
			for j in range(cnt):
				t, i = getLen32Text16(data, i)
				l2.append(t)
			n1, i = getUInt8(data, i)
			t8,  i = getLen32Text16(data, i) # UID
			n2, i = getUInt32(data, i)
			t9,  i = getLen32Text16(data, i) # FusionAssetName
			n3, i = getUInt32(data, i)
			n4, i = getUInt8(data, i)
	return

def read(filename):
	global smb_files
	smb_files.clear()
	result = is_zipfile(filename)
	if (result):
		setDumpFolder(filename)
		f3d = ZipFile(filename)
		for name in f3d.namelist():
			if (name.startswith('FusionAssetName[Active]/Previews/')):
				_set_thumbnail(f3d, name)
			elif (name.startswith('FusionAssetName[Active]/Breps.BlobParts/')):
				if (_dump_SMB(f3d, name)):
					result = True
			elif (name == 'Manifest.dat'):
				read_manifest(f3d, name)
		f3d.close()
	return result

def importModel(root):
	global lumps, wires, smb_files
	for acis in smb_files:
		wires = 0
		lumps = 0
		bodies = resolveNodes(acis)
		group = createGroup(acis.name)
		if (root):
			root.addObject(group)
		for body in bodies:
			buildBody(group, body)
	return

def convertModel(docName):
	global smb_files
	for acis in smb_files:
		bodies = resolveNodes(acis)
		stepfile = export(acis.name, acis.header, bodies)
		insert(stepfile, docName)

def create3dModel(root, doc):
	strategy = chooseImportStrategyAcis()
	if (strategy == STRATEGY_SAT):
		importModel(root)
	else:
		convertModel(doc.Name)
	return
