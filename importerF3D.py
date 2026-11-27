# -*- coding: utf-8 -*-

from importerUtils     import *
from datetime          import datetime
from importerSAT       import dumpSat, importModel, convertModel, buildBody, resolveNodes
from Acis2Step         import export
from zipfile           import is_zipfile, ZipFile
from FreeCAD           import ParamGet
from Acis              import AcisReader
from importerFreeCAD   import createGroup
from ImportGui         import insert
from importerConstants import REF_CHILD, REF_CROSS, REF_PARENT
from importerConstants import VAL_DATETIME, VAL_ENUM, VAL_GUESS, VAL_REF, VAL_STR8, VAL_STR16, VAL_UINT8, VAL_UINT16, VAL_UINT32, VAL_UINT64, VAL_FORMAT
import traceback

smb_files = []
smb_only  = []
_label    = None # imported solids are labelled after the .f3d file
bulk_data = None
meta_data = None

CONSTRAINT_TXPE = {
	0x00000000001: 'Coincident',
	0x00000000002: 'Colinear',
	0x00000000004: 'Concntric',
	0x00000000010: 'Parallel',
	0x00000000020: 'Perpendicular',
	0x00000000040: 'Horizontal',
	0x00000000080: 'Vertical',
	0x00000000100: 'Tangential',
	0x00000000200: 'Curvature',
	0x00000000400: 'Symmetry',
	0x00000000800: 'Equal',
	0x00000001000: 'Midpoint',
	0x00000002000: 'Polygon',
	0x00010000000: 'Pattern_Circular',
	0x00020000000: 'Pattern_Rect',
	0x10000000000: 'Text_Frame',
	0x20000000000: 'Text_Path'
}
refs = []
sketches = []
MISSING_METHODS = {}
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
				if (name[-3:].lower() != 'smb'):
					smb_files.append(reader)
				else:
					smb_only.append(reader) # newer Fusion files store the B-rep only as .smb
	return result

def get_manifest_item(data, offset):
	t1, i = getLen32Text16(data, offset)
	t2, i = getLen32Text16(data, i)
	t3, i = getLen32Text16(data, i)
	t4, i = getLen32Text16(data, i)
	a1, i = getUInt32A(data, i, 4)
	cnt, i = getUInt32(data, i)
	a2 = {}
	for j in range(cnt):
		k, i = getLen32Text16(data, i)
		v, i = getLen32Text16(data, i)
		a2[k] = v
	return (t1, t2, t3, t4, a1, a2), i

def get_manifest_items(data, offset):
	a = []
	n1, i = getUInt8(data, offset)
	if (n1):
		cnt, i = getUInt32(data, i)
		for j in range(cnt):
			mi, i = get_manifest_item(data, i)
			a.append(mi)
	return a, i

def read_manifest(f3d, path):
	name = path.split('/')[-1]
	if (name):
		with f3d.open(path) as manifest:
			data = manifest.read()
			t1,  i = getLen32Text8(data, 0)
			t2,  i = getLen32Text8(data, i)  # fusion doc type
			t3,  i = getLen32Text16(data, i) # .f3d
			t4,  i = getLen32Text16(data, i) # Fusion Document
			t5,  i = getLen32Text16(data, i) # A Fusion Document
			t6,  i = getLen32Text16(data, i) # UID
			t7,  i = getLen32Text16(data, i) # UID
			a1,  i = getUInt32A(data, i, 2)  # ???
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
			l3, i = get_manifest_items(data, i)
			t8, i = getLen32Text16(data, i)  # UID
			n1, i = getUInt32(data, i) # 1
			folder, i = getLen32Text16(data, i) # -> folder name
			n2, i = getUInt32(data, i)
			n3, i = getUInt8(data, i)
	# dump
	dumpFolder = getDumpFolder()
	with open(u"%s/Manifest.log" %(dumpFolder), 'w') as log:
		log.write(f"t1 = '{t1}'\n")
		log.write(f"t2 = '{t2}'\n")
		log.write(f"t3 = '{t3}'\n")
		log.write(f"t4 = '{t4}'\n")
		log.write(f"t5 = '{t5}'\n")
		log.write(f"t6 = {t6}\n")
		log.write(f"t7 = {t7}\n")
		log.write("a1 = (%s)\n" % (",".join([f"{t:04X}" for t in a1])))
		log.write("l1 = (%s)\n" % (",".join([f"{t}={v:04X}" for t, v in l1])))
		log.write("l2 = (%s)\n" % (",".join([f"'{t}'" for t in l2])))
		log.write("l3 = %s\n" % (l3))
		log.write("t8 = '%s'\n"%(t8))
		log.write(f"n1 = {n1:08X}\n")
		log.write(f"n2 = {n2:08X}\n")
		log.write(f"n3 = {n3:02X}\n")

		log.write(" ".join(["%02X"%(c) for c in data[i:]]))

	return folder

def _zip_without_zstd(filename):
	'''Fusion files saved since 2025 compress entries with Zstandard (zip method 93), which Python's
	zipfile only reads from 3.14 on. Rewrite such archives as an uncompressed copy in the temp folder.'''
	import os, struct, tempfile, zipfile
	with zipfile.ZipFile(filename) as src:
		infos = src.infolist()
		if (not any(i.compress_type == 93 for i in infos)):
			return filename
		try:
			from compression import zstd # Python 3.14+
			decompress = lambda data, size: zstd.decompress(data)
		except ImportError:
			try:
				import zstandard
			except ImportError:
				raise ImportError("This Fusion file uses Zstandard compression (zip method 93): install the Python package 'zstandard' for FreeCAD, or use a FreeCAD built with Python 3.14 or newer.")
			dctx = zstandard.ZstdDecompressor()
			decompress = lambda data, size: dctx.decompress(data, max_output_size=max(size, 1))
		root = os.path.join(tempfile.gettempdir(), u"InventorLoader")
		os.makedirs(root, exist_ok=True)
		out = os.path.join(root, os.path.basename(filename))
		with open(filename, 'rb') as raw, zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED) as dst:
			for i in infos:
				if (i.compress_type == 93):
					raw.seek(i.header_offset)
					nlen, xlen = struct.unpack('<HH', raw.read(30)[26:30])
					raw.seek(i.header_offset + 30 + nlen + xlen)
					data = decompress(raw.read(i.compress_size), i.file_size)
				else:
					data = src.read(i)
				dst.writestr(zipfile.ZipInfo(i.filename, date_time=i.date_time), data)
	return out

def read(filename):
	global smb_files, smb_only, bulk_data, sketches, refs, _label
	_label = filename.replace('\\', '/').split('/')[-1].rsplit('.', 1)[0]
	smb_files.clear()
	smb_only.clear()
	sketches.clear()
	refs = []
	result = is_zipfile(filename)
	if (result):
		filename = _zip_without_zstd(filename)
	data = None
	meta = None
	if (result):
		setDumpFolder(filename)
		f3d = ZipFile(filename)
		try:
			folder = read_manifest(f3d, 'Manifest.dat')
		except Exception:
			folder = None # newer (assembly) manifests are not understood
		if (not folder) or (not any(n.startswith(folder + '[Active]/') for n in f3d.namelist())):
			active = [n for n in f3d.namelist() if '[Active]/' in n]
			folder = active[0].split('[Active]/')[0] if (active) else 'FusionAssetName'
		folderPreview = folder + '[Active]/Previews/'
		folderBreps   = folder + '[Active]/Breps.BlobParts/'
		fileBulk      = folder + '[Active]/Design1/BulkStream.dat'
		fileMeta      = folder + '[Active]/Design1/MetaStream.dat'
		for name in f3d.namelist():
			if (name.startswith(folderPreview)):
				_set_thumbnail(f3d, name)
			elif (name.startswith(folderBreps)):
				if (_dump_SMB(f3d, name)):
					result = True

		if (not smb_files):
			smb_files.extend(smb_only)
		bulk_data = (data, meta)
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

def _insert_as_solids(stepfile, docName):
	'''The ACIS->STEP export writes loose faces: sew them into closed solids where possible.'''
	import os, FreeCAD, Part
	shape = Part.read(stepfile)
	sewn = shape.copy()
	sewn.sewShape()
	solids = [Part.Solid(shell) for shell in sewn.Shells if shell.isClosed()]
	doc = FreeCAD.getDocument(docName)
	name = _label or os.path.splitext(os.path.basename(stepfile))[0]
	finite = lambda shape: shape.BoundBox.isValid() and shape.BoundBox.DiagonalLength < 1e5 # mm; broken thread geometry can be 'infinite'
	solids = [solid for solid in solids if finite(solid)]
	for i, solid in enumerate(solids):
		if (solid.Volume < 0):
			solid.reverse()
		obj = doc.addObject('Part::Feature', name if (len(solids) == 1) else '%s_%d' %(name, i))
		obj.Shape = solid
	open_faces = [face for shell in sewn.Shells if not shell.isClosed() for face in shell.Faces if finite(face)]
	if (open_faces):
		obj = doc.addObject('Part::Feature', name + '_open_faces')
		obj.Shape = Part.makeCompound(open_faces)
	doc.recompute()

def convertModel(docName):
	global smb_files
	for acis in smb_files:
		bodies = resolveNodes(acis)
		stepfile = export(acis.name, acis.header, bodies)
		_insert_as_solids(stepfile, docName)

def create3dModel(root, doc):
	strategy = chooseImportStrategyAcis()
	if (strategy in (STRATEGY_SAT, STRATEGY_NATIVE)):
		importModel(root)
	elif (strategy == STRATEGY_STEP):
		convertModel(doc.Name)
	return
