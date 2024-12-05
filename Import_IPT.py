# -*- coding: utf-8 -*-

'''
Import_IPT.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

import os, FreeCAD, FreeCADGui, importerBRep, importerSAT, io, importerUFRxDoc
from olefile           import OleFileIO
from importerUtils     import *
from importerReader    import *
from importerClasses   import Inventor
from importerFreeCAD   import FreeCADImporter
from importerSAT       import importModel, convertModel
from Acis              import setReader
from PySide.QtGui      import QMessageBox
from struct            import unpack

VT_EMPTY=0; VT_NULL=1; VT_I2=2; VT_I4=3; VT_R4=4; VT_R8=5; VT_CY=6;
VT_DATE=7; VT_BSTR=8; VT_DISPATCH=9; VT_ERROR=10; VT_BOOL=11;
VT_VARIANT=12; VT_UNKNOWN=13; VT_DECIMAL=14; VT_I1=16; VT_UI1=17;
VT_UI2=18; VT_UI4=19; VT_I8=20; VT_UI8=21; VT_INT=22; VT_UINT=23;
VT_VOID=24; VT_HRESULT=25; VT_PTR=26; VT_SAFEARRAY=27; VT_CARRAY=28;
VT_USERDEFINED=29; VT_LPSTR=30; VT_LPWSTR=31; VT_FILETIME=64;
VT_BLOB=65; VT_STREAM=66; VT_STORAGE=67; VT_STREAMED_OBJECT=68;
VT_STORED_OBJECT=69; VT_BLOB_OBJECT=70; VT_CF=71; VT_CLSID=72;
VT_VECTOR=0x1000;

VT = dict([(v, k) for k, v in list(vars().items()) if k[:3] == "VT_"])

# For Python 3.x, need to redefine long as int:
if str is not bytes:
    long = int

# [PL]: Defect levels to classify parsing errors - see OleFileIO._raise_defect()
DEFECT_UNSURE =    10    # a case which looks weird, but not sure it's a defect
DEFECT_POTENTIAL = 20    # a potential defect
DEFECT_INCORRECT = 30    # an error according to specifications, but parsing can go on
DEFECT_FATAL =     40    # an error which cannot be ignored, parsing is impossible

def ReadIgnorable(fname):
	logInfo(u"    IGNORED: '%s'" %(fname[-1]))

def skip():
	return

def ReadElement(ole, fname, counter):
	name        = fname[-1]
	path        = PrintableName(fname)

	if (fname[0] == 'Protein'):
#		ReadProtein(ole.openstream(fname).read())
		ReadIgnorable(fname)
	elif (fname[0]=='CacheGraphics'):
		skip()
	elif (fname[0]=='RSeStorage'):
		if (isEmbeddings(fname)):
			if (name == 'Workbook'):
				ReadWorkbook(ole.openstream(fname).read(), fname[-2], name)
			elif (name.endswith('Ole10Native')):
				ReadOle10Native(ole.openstream(fname).read(), fname)
			else:
				skip()
		elif (name.startswith('M')):
			if not ('Templates' in fname):
				fnameB = []
				for n in (fname):
					fnameB.append(n)
				fnameB[-1] = 'B' + name[1:]
				seg = ReadRSeMetaDataM(ole.openstream(fname).read(), name[1:])
				seg.file = name[1:]
				seg.index = counter
				getModel().RSeMetaData[seg.name] = seg
				dataB = ole.openstream(fnameB).read()
				ReadRSeMetaDataB(dataB, seg)
			else:
				skip()
		else:
			ReadIgnorable(fname)
	return

def dumpRSeDBFile(db, log):
	log.write(u"Schema: %d\n"   %(db.schema))
	log.write(u"UID:    {%s}\n" %(db.uid))
	log.write(u"Vrs1:   %s\n"   %(db.vers1)) # last saved with
	log.write(u"Date1:  %s\n"   %(db.dat1))  # last saved
	log.write(u"Vrs2:   %s\n"   %(db.vers2)) # created with
	log.write(u"Date2:  %s\n"   %(db.dat2))  # created
	log.write(u"%s\n" %(db.txt))

	log.write(u"segInfo:\n")
	log.write(u"\tUID:   {%s}\n" %(db.segInfo.uid))
	log.write(u"\tDate:  %s\n"   %(db.segInfo.date))
	log.write(u"\tText:  '%s'\n" %(db.segInfo.text))
	log.write(u"\tU16:   %03X\n" %(db.segInfo.u16))
	log.write(u"\tText2: '%s'\n" %(db.segInfo.text2)) # original file path
	log.write(u"\tarr1:  [%s]\n" %(IntArr2Str(db.segInfo.arr1, 3)))
	log.write(u"\tarr2:  [%s]\n" %(IntArr2Str(db.segInfo.arr2, 4)))
	log.write(u"\tarr3:  [%s]\n" %(IntArr2Str(db.segInfo.arr3, 4)))
	log.write(u"\tarr4:  [%s]\n" %(IntArr2Str(db.segInfo.arr4, 4)))
	log.write(u"\tUID1:\n")
	for n, txt in enumerate(db.segInfo.uidList1):
		log.write(u"\t\t[%02X]: '%s'\n" %(n, txt))
	log.write(u"\tUID2:\n")
	for n, txt in enumerate(db.segInfo.uidList2):
		log.write(u"\t\t[%02X]: '%s'\n" %(n, txt))
	log.write(u"\tSegments:\n")
	segments = sorted(db.segInfo.segments.values())
	for seg in segments:
		log.write(u"\t\t%s\n" %(seg))
	return

def dumpRSeDB(db):
	dumpFolder = getDumpFolder()
	if (not (dumpFolder is None)):
		with io.open(u"%s/RSeDb.log" %(dumpFolder), mode='w', encoding='utf-8') as log:
			dumpRSeDBFile(db, log)
	return

def dumpiProperties(iProps):
	dumpFolder = getDumpFolder()
	if (not (dumpFolder is None)):
		with io.open(u"%s/iProperties.log" %(dumpFolder), mode='w', encoding="utf-8") as file:
			setNames = sorted(iProps.keys())
			for setName in setNames:
				file.write(u"%s:\n" %(setName))
				setProps = iProps[setName]
				prpNames = sorted(setProps.keys())
				for prpNum in prpNames:
					val = setProps[prpNum]
					prpName = val[0]
					prpVal  = val[1]
					if (isinstance(prpVal, datetime.datetime)):
						if (prpVal.year > 1900):
							file.write(u"%3d - %26s: %s\n" %(prpNum, prpName, prpVal.strftime("%Y/%m/%d %H:%M:%S.%f")))
					else:
						file.write(u"%3d - %26s: %r\n" %(prpNum, prpName, prpVal))
				file.write(u"\n")
	return

def dumpRevisionInfo(revisions):
	dumpFolder = getDumpFolder()
	if (not (dumpFolder is None)):
		with io.open(u"%s/RSeDbRevisionInfo.log" %(dumpFolder), mode='w', encoding="utf-8") as file:
			for rev in revisions.infos:
				file.write(u"%s\n" %(rev))
	return

def checkVersion(file):
	vrs = None
	filename = os.path.abspath(file)
	ole = OleFileIO(filename)
	elements = ole.listdir(streams=True, storages=False)
	for e in elements:
		if (e[-1] == 'RSeDb'):
			data = ole.openstream(e).read()
			version, i  = getVersionInfo(data, 20)
			if (version.major >= 14):
				setDumpFolder(file)
				return ole
			break

	if (version):
		vrsName = version.major
		if (version.major >= 11): vrsName += 1996
		QMessageBox.critical(FreeCAD.ActiveDocument, 'FreeCAD: Inventor workbench...', 'Can\'t load file created with Inventor v%d' %(vrsName))
		logError('Can\'t load file created with Inventor v%d' %(vrsName))
	else:
		QMessageBox.critical(FreeCAD.ActiveDocument, 'FreeCAD: Inventor workbench...', 'Can\'t determine Inventor version file was created with')
		logError('Can\'t determine Inventor version file was created with!')
	return None

def read(ole):
	ufrxDoc        = None
	rSeDb          = None
	rSeSegInfo     = None
	rSeDbRevisions = None

	createNewModel()

	elements = ole.listdir(streams=True, storages=False)
	counter  = 1
	list     = []
	handled  = {}

	for fname in elements:
		name = fname[-1]
		if (name == 'UFRxDoc'):
			ufrxDoc = ole.openstream(fname).read()
#			getModel().UFRxDoc = importerUFRxDoc.read(ufrxDoc)
			handled[PrintableName(fname)] = True
		elif (name.startswith('\x05')):
			props = GetProperties(ole, fname)
			if (name == '\x05Aaalpg0m0wzvuhc41dwauxbwJc'):
				ReadOtherProperties(props, fname, Inventor_Document_Summary_Information)
				setCompany(getProperty(props, KEY_DOC_SUM_INFO_COMPANY))
			elif (name == '\x05Zrxrt4arFafyu34gYa3l3ohgHg'):
				ReadInventorSummaryInformation(props, fname)
			elif (name == '\x05Qz4dgm1gRjudbpksAayal4qdGf'):
				ReadOtherProperties(props, fname, Design_Tracking_Control)
			elif (name == '\x05PypkizqiUjudbposAayal4qdGf'):
				ReadOtherProperties(props, fname, Design_Tracking_Properties)
				setDescription(getProperty(props, 29))
			elif (name == '\x05Qm0qv30hP3udrkgvAaitm1o20d'):
				ReadOtherProperties(props, fname, Private_Model_Information)
			elif (name == '\x05Ynltsm4aEtpcuzs1Lwgf30tmXf'):
				ReadOtherProperties(props, fname, Inventor_User_Defined_Properties)
			elif (name == '\x05C3vnhh4uFrpeuhcsBpg4yptkTb'):
				ReadOtherProperties(props, fname, Inventor_Piping_Style_Properties)
			else:
				ReadOtherProperties(props, fname, {})
			handled[PrintableName(fname)] = True
		elif (name == 'RSeDb'):
			rSeDb = ole.openstream(fname).read()
			handled[PrintableName(fname)] = True
		elif (name == 'RSeSegInfo'):
			rSeSegInfo = ole.openstream(fname).read()
			handled[PrintableName(fname)] = True
		elif (name == 'RSeDbRevisionInfo'):
			rSeDbRevisions = ole.openstream(fname).read()
			handled[PrintableName(fname)] = True

	if (rSeDb):
		db = getModel().RSeDb
		ReadRSeDb(db, rSeDb)

		if (rSeSegInfo):
			if ((db.schema == 0x1F)):
				ReadRSeSegInfo1F(db, rSeSegInfo)
			elif (db.schema == 0x1E):
				ReadRSeSegInfo1E(db, rSeSegInfo)
			else:
				ReadRSeSegInfo1D(db, rSeSegInfo)
		dumpRSeDB(db)

	if (rSeDbRevisions):
		ReadRSeDbRevisionInfo(getModel().RSeRevisions, rSeDbRevisions)
#		dumpRevisionInfo(getModel().RSeRevisions)

	chooseImportStrategy()

	for fname in elements:
		if (handled.get(PrintableName(fname), False) == False):
			if (not fname[-1].startswith('B')):
				list.append(fname)

	dumpiProperties(getModel().iProperties)

	for fname in list:
		ReadElement(ole, fname, counter)
		counter += 1
	ole.close()

	now = datetime.datetime.now()
	comment = getComment()
	if (len(comment) > 0):
		comment += '\n'
	comment += '# %s: read from %s' %(now.strftime('%Y-%m-%d %H:%M:%S'), getInventorFile())
	setComment(comment)

	dumpFolder = getDumpFolder()
	if (not (dumpFolder is None)):
		logInfo(u"Dumped data to folder: '%s'", dumpFolder)

	return True

def resolveLinks():
	gr = getModel().getGraphics()
	dc = getModel().getDC()
	grp = gr.elementNodes.get(0x0001)
	if (grp is not None):
		parts = grp.get('parts')
		if (parts is not None):
			for part in parts:
				outlines = part.get('outlines')
				if (outlines is not None):
					for dcIndex in  outlines:
						outline = outlines[dcIndex]
						creator = dc.indexNodes.get(dcIndex, None)
						if (creator is not None):
							creator.outline = outline
						else:
							logWarning(u"    No outline-creator found for index=%04X!" %(dcIndex))
	return

def create3dModel(root, doc):
	strategy = getStrategy()
	if (strategy == STRATEGY_NATIVE):
		creator = FreeCADImporter()
		creator.importModel(root)
	else:
		brep = getModel().getBRep()
		for asm in brep.AcisList:
			setReader(asm.SAT)
			if (strategy == STRATEGY_SAT):
				importModel(root)
			elif (strategy == STRATEGY_STEP):
				convertModel(root, doc.Name)
	return

def GetProperties(ole, filename):
	streampath = filename
	if not isinstance(streampath, str):
		streampath = '/'.join(streampath)
	fp = ole.openstream(filename)
	data = {}
	try:
		# header
		s = fp.read(28)
		clsid, i = getUUID(s, 8)
		# format id
		s = fp.read(20)
		fmtid, i = getUUID(s, 0)
		offset, i = getUInt32(s, i)
		fp.seek(offset)
		# get section
		b_size = fp.read(4)
		size = UINT32(b_size, 0)
		s = b_size + fp.read(size-4)
		# number of properties:
		num_props = UINT32(s, 4)
	except BaseException as exc:
		# catch exception while parsing property header, and only raise
		# a DEFECT_INCORRECT then return an empty dict, because this is not
		# a fatal error when parsing the whole file
		msg = f"Error while parsing properties header in stream {repr(streampath)}: {exc}"
		raise Exception(DEFECT_INCORRECT, msg, type(exc))
		return data
	# clamp num_props based on the data length
	num_props = min(num_props, int(len(s) / 8))
	for i in range(num_props):
		property_id = 0 # just in case of an exception
		try:
			property_id, j = getUInt32(s, 8+i*8)
			offset, j = getUInt32(s, j)
			property_type, j = getUInt32(s, offset)

			vt_name = VT.get(property_type, 'UNKNOWN')
			logInfo('property id=%d: type=%d/%s offset=%X' % (property_id, property_type, vt_name, offset))

			value = _parse_property(s, offset+4, property_id, property_type)
			data[property_id] = value
		except BaseException as exc:
			# catch exception while parsing each property, and only raise
			# a DEFECT_INCORRECT, because parsing can go on
			msg = 'Error while parsing property id %d in stream %s: %s' % (property_id, repr(streampath), exc)
			raise Exception(msg, type(exc))

	return data

def _parse_property(s, offset, property_id, property_type):
	v = None
	if property_type <= VT_BLOB or property_type in (VT_CLSID, VT_CF):
		v, _ = _parse_property_basic(s, offset, property_id, property_type)
	elif property_type == VT_VECTOR | VT_VARIANT:
		logWarning('property_type == VT_VECTOR | VT_VARIANT')
		off = 4
		count = UINT32(s, offset)
		values = []
		for _ in range(count):
			property_type = UINT32(s, offset + off)
			v, sz  = _parse_property_basic(s, offset + off + 4, property_id, property_type)
			values.append(v)
			off = sz + 4
		v = values

	elif property_type & VT_VECTOR:
		property_type_base = property_type & ~VT_VECTOR
		logWarning('property_type == VT_VECTOR | %s' % VT.get(property_type_base, 'UNKNOWN'))
		off = 4
		count = UINT32(s, offset)
		values = []
		for _ in range(count):
			v, off = _parse_property_basic(s, offset + off, property_id, property_type & ~VT_VECTOR)
			values.append(v)
		v = values
	else:
		logWarning('property id=%d: type=%d not implemented in parser yet' % (property_id, property_type))
	return v

def Property_VT_NULL(s, offset):
	return None, offset
def Property_VT_EMPTY(s, offset):
	return None, offset
def Property_VT_I1(s, offset): # 8-bit signed integer
	return getSInt8(s, offset)
def Property_VT_I2(s, offset): # 16-bit signed integer
	return getSInt16(s, offset)
def Property_VT_UI22(s, offset): # 2-byte unsigned integer
	return  getUInt16(s, offset)
def Property_VT_I4(s, offset):# VT_I4: 32-bit signed integer
	return getSInt32(s, offset)
def Property_VT_INT(s, offset):
	return getSInt32(s, offset)
def Property_VT_ERROR(s, offset): # VT_ERROR: HRESULT, similar to 32-bit signed integer
	# see https://msdn.microsoft.com/en-us/library/cc230330.aspx
	return getUInt32(s, offset)
def Property_VT_I8(s, offset): # 8-byte signed integer
	return  getSInt64(s, offset)
def Property_VT_UI8(s, offset): # 8-byte unsigned integer
	return getUInt64(s, offset)
def Property_VT_UI4(s, offset):
	return getUInt32(s, offset)
def Property_VT_UINT2(s, offset): # 4-byte unsigned integer
	return getUInt32(s, offset)
def Property_VT_BSTR(s, offset): # CodePageString, see https://msdn.microsoft.com/en-us/library/dd942354.aspx
	# size is a 32 bits integer, including the null terminator, and
	# possibly trailing or embedded null chars
	# TODO: if codepage is unicode, the string should be converted as such
	value, i = getLen32Text8(s, offset)
	return  value.replace(b'\x00', b''), i
def Property_VT_LPSTR(s, offset):
	return Property_VT_LPSTR(s, offset)
def Property_VT_BLOB(s, offset): # binary large object (BLOB)
	# see https://msdn.microsoft.com/en-us/library/dd942282.aspx
	count, i = getUInt32(s, offset)
	return getUInt8A(s, i, count)
def Property_VT_LPWSTR(s, offset): # UnicodeString
	# see https://msdn.microsoft.com/en-us/library/dd942313.aspx
	# "the string should NOT contain embedded or additional trailing null characters."
	return getLen32Text16(s, offset)
def Property_VT_FILETIME(s, offset): # FILETIME is a 64-bit int: "number of 100ns periods since Jan 1,1601".
	value, i = getUInt64(s, offset)
	logWarning('Converting property VT_FILETIME2 to python datetime, value=%d=%fs' %(value, float(value)/10000000))
	# convert FILETIME to Python datetime.datetime
	# inspired from https://code.activestate.com/recipes/511425-filetime-to-datetime/
	_FILETIME_null_date = datetime.datetime(1601, 1, 1, 0, 0, 0)
	logInfo('timedelta days=%d' % (value//(10*1000000*3600*24)))
	return _FILETIME_null_date + datetime.timedelta(microseconds=value//10), i
def Property_VT_UI1(s, offset): # 1-byte unsigned integer
	return getUInt8(s, offset)
def Property_VT_CLSID(s, offset):
	return getUUID(s, offset)
def Property_VT_CF(s, offset): # PropertyIdentifier or ClipboardData??
	# see https://msdn.microsoft.com/en-us/library/dd941945.aspx
	cnt, i = getUInt32(s, offset)
	fmt, i = getUInt32(s, i)
	dat =  s[i:i+cnt-4]
	return (fmt, dat), i+cnt-4
def Property_VT_BOOL(s, offset): # VARIANT_BOOL, 16 bits bool, 0x0000=Fals, 0xFFFF=True
	# see https://msdn.microsoft.com/en-us/library/cc237864.aspx
	value, i = getUInt16(s, offset)
	return bool(value), i
def Property_VT_R4(s, offset): # 32 bit single precision
	return getFloat32(s, offset)
def Property_VT_R8(s, offset): # 64 bit double precision
	return getFloat64(s, offset)
def Property_VT_CY(s, offset): # 8 Byte Currency
	value, i = getSInt64(s, offset)
	return value / 1000.0, i
def Property_VT_DECIMAL(s, offset): # 96 bit Decimal
	reserved, i = getSInt16(s, offset)
	scale, i = getUInt8(s, i)
	sign, i = getUInt8(s, i)
	hi32, i = getUInt32(s, i)
	hi64, i = getUInt64(s, i)
	value = (hi32 << 64 + hi64) * scale
	if (sign):
		value *= -1;
	return value, i
def Property_VT_DATE(s, offset): # B byte floating point
	return  getFloat64(s, offset) # FIXME convert to datetime!


def _parse_property_basic(s, offset, property_id, property_type):
		# test for common types first (should perhaps use
		# a dictionary instead?)
		fkt_name = f"Property_{VT.get(property_type, 'UNKNOWN')}"
		fkt = getattr(sys.modules[__name__], fkt_name, None)
		if (fkt is None):
			logError('property id=%d: type=%d not implemented in parser yet' % (property_id, property_type))
			# see https://msdn.microsoft.com/en-us/library/dd942033.aspx
			return None, offset
		return fkt(s, offset)
