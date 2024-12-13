# -*- coding: utf-8 -*-

'''
importerReader.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

import zlib, codecs, xlrd, importerOle10Nateive
from importerClasses     import *
from importerSegment     import SegmentReader
from importerApp         import AppReader
from importerBRep        import BRepReader
from importerBrowser     import BrowserReader
from importerDC          import DCReader
from importerDirectory   import DirectoryReader
from importerDesignView  import DesignViewReader
from importerEeData      import EeDataReader
from importerEeScene     import EeSceneReader
from importerFBAttribute import FBAttributeReader
from importerGraphics    import GraphicsReader
from importerNotebook    import NotebookReader
from importerSheetDC     import SheetDcReader
from importerSheetDL     import SheetDlReader
from importerSheetSM     import SheetSmReader
from importerResults     import ResultReader
from importerUtils       import *
from xlutils.copy        import copy

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

# The model representing the content of the imported file
model = None

KEY_SUM_INFO_AUTHOR      = 0x04
KEY_SUM_INFO_COMMENT     = 0x06
KEY_SUM_INFO_MODIFYER    = 0x08

KEY_THUMBNAIL_1          = 0x11
KEY_THUMBNAIL_2          = 0x1C

KEY_DOC_SUM_INFO_COMPANY = 0x0F

KEY_CODEPAGE             = 0x01
KEY_SET_NAME             = 0xFF
KEY_LANGUAGE_CODE        = 0x80000000

KEY_DTP_VERSION          = 43
KEY_DTP_BUILD            = 0

SEG_TYPE_READERS = {
	SEG_APP            : AppReader,
	SEG_APP_AM         : AppReader,
	SEG_APP_PM         : AppReader,
	SEG_BREP_AM        : BRepReader,
	SEG_BREP_MB        : BRepReader,
	SEG_BREP_PM        : BRepReader,
	SEG_BROWSER_AM     : BrowserReader,
	SEG_BROWSER_DL     : BrowserReader,
	SEG_BROWSER_DX     : BrowserReader,
	SEG_BROWSER_PM     : BrowserReader,
	SEG_BROWSER_PM_OLD : BrowserReader,
	SEG_DC_AM          : DCReader,
	SEG_DC_DL          : DCReader,
	SEG_DC_DX          : DCReader,
	SEG_DC_PM          : DCReader,
	SEG_DESIGN_VIEW    : DesignViewReader,
	SEG_DESIGN_VIEW_MGR: DesignViewReader,
	SEG_DIRECTORY_DL   : DirectoryReader,
	SEG_EE_DATA        : EeDataReader,
	SEG_EE_SCENE       : EeSceneReader,
	SEG_FB_ATTRIBUTE   : FBAttributeReader,
	SEG_GRAPHICS_AM    : GraphicsReader,
	SEG_GRAPHICS_MB    : GraphicsReader,
	SEG_GRAPHICS_PM    : GraphicsReader,
	SEG_NOTEBOOK       : NotebookReader,
	SEG_RESULT_AM      : ResultReader,
	SEG_RESULT_PM      : ResultReader,
	SEG_SHEET_DC_DL    : SheetDcReader,
	SEG_SHEET_DL_DL    : SheetDlReader,
	SEG_SHEET_SM_DL    : SheetSmReader,
}

# F29F85E0-4FF9-1068-AB91-08002B27B3D9
Inventor_Summary_Information = {
	 2: "Title",
	 3: "Subject",
	 4: "Author",
	 5: "Keywords",
	 6: "Comments",
	 8: "LastSavedBy",
	 9: "Revision",
	12: "CreationTime",
	17: "Thumbnail",
}
# D5CDD502-2E9C-101B-9397-08002B2CF9AE
Inventor_Document_Summary_Information = {
	 2: "Category",
	14: "Manager",
	15: "Company",
}

Design_Tracking_Control = {
	 5: "CheckedOutBy",
	 6: "CheckedOutDate",
	 7: "CheckInBy",
	 8: "CheckInDate",
	 9: "CheckOutWorkGroup",
	11: "CheckOutWorkSpace",
	12: "CheckOutVersion",
	13: "NextVersion",
	14: "CurrentVersion",
	15: "PreviousVersion",
	16: "LastSavedBy",
	17: "LastSavedDate",
	19: "DrawingDeferUpdate",
	22: "BuildVersion"
}
# 32853F0F-3444-11D1-9E93-0060B03C1CA6
Design_Tracking_Properties = {
	 4: "CreationDate",
	 5: "PartNumber",
	 7: "Project",
	 9: "CostCenter",
	10: "CheckedBy",
	11: "DateChecked",
	12: "EngrApprovedBy",
	13: "DateEngrApproved",
	17: "UserStatus",
	20: "Material",
	21: "PartPropRevId",
	23: "CatalogWebLink",
	28: "PartIcon",
	29: "Description",
	30: "Vendor",
	31: "DocSubType",
	32: "DocSubTypeName",
	33: "ProxyRefreshDate",
	34: "MfgApprovedBy",
	35: "DateMfgApproved",
	36: "Cost",
	37: "Standard",
	40: "DesignStatus",
	41: "Designer",
	42: "Engineer",
	43: "Authority",
	44: "ParameterizedTemplate",
	45: "TemplateRow",
	46: "ExternalPropRevId",
	47: "StandardRevision",
	48: "Manufacturer",
	49: "StandardsOrganization",
	50: "Language",
	51: "DrawingDeferUpdate",
	52: "DesignationSize",
	55: "StockNumber",
	56: "Categories",
	57: "WeldMaterial",
	58: "Mass",
	59: "SurfaceArea",
	60: "Volume",
	61: "Density",
	62: "ValidMassProps",
	63: "FlatPatternExtentsWidth",
	64: "FlatPatternExtentsLength",
	65: "FlatPatternExtentsArea",
	66: "SheetMetalRule",
	67: "LastUpdatedWith",
	71: "MaterialIdentifier",
	72: "Appearance",
	73: "FlatPatternDeferUpdate",
}
Private_Model_Information = {
	 8: "LengthUnits",
	 9: "AngleUnits",
	11: "MassUnits",
	10: "TimeUnits",
	12: "LengthDisplayPrecision",
	13: "AngleDisplayPrecision",
	14: "Compacted",
	15: "AssemblyAvailablePvs",
	16: "PartActiveColorStyle",
}
Inventor_User_Defined_Properties = {
}
Inventor_Piping_Style_Properties = {
	3: u"Name"
}

def getProperty(properties, key):
	value = properties.get(key, '')
	if (type(value) is str):
		if ((len(value) > 0) and (value[-1] == '\0')):
			value = value[0:-1]
	return value

def getPropertySetName(properties, path):
	name = getProperty(properties, KEY_SET_NAME)

	if ((name is None ) or (len(name)==0)):
		name = path[-1][1:]

	languageCode = properties[KEY_LANGUAGE_CODE] if (KEY_LANGUAGE_CODE in properties) else 1031 # en_EN
	logInfo(u"\t'%s': (LC = %X)", name, languageCode)

	if (name not in getModel().iProperties):
		getModel().iProperties[name] = {}

	keys = properties.keys()
	keys = sorted(keys)

	return name, keys

def ReadInventorSummaryInformation(properties, path):
	name, keys = getPropertySetName(properties, path)

	setAuthor(getProperty(properties, KEY_SUM_INFO_AUTHOR))
	setComment(getProperty(properties, KEY_SUM_INFO_COMMENT))
	setLastModifiedBy(getProperty(properties, KEY_SUM_INFO_MODIFYER))

	for key in keys:
		if ((key != KEY_CODEPAGE) and (key != KEY_SET_NAME) and (key != KEY_LANGUAGE_CODE)):
			val = getProperty(properties, key)
			if (val is not None):
				if (key == KEY_THUMBNAIL_1):
					val = writeThumbnail(val)
				elif (key == KEY_THUMBNAIL_2):
					val = writeThumbnail(val)
				getModel().iProperties[name][key] = (Inventor_Summary_Information.get(key, key), val)
	return

def ReadOtherProperties(properties, path, keynames={}):
	name, keys = getPropertySetName(properties, path)

	for key in keys:
		if ((key != KEY_CODEPAGE) and (key != KEY_SET_NAME) and (key != KEY_LANGUAGE_CODE)):
			val = getProperty(properties, key)
			if (val is not None):
				getModel().iProperties[name][key] = (keynames.get(key, key), val)

	return

def ReadProtein(data):
	size, i = getSInt32(data, 0)
	zip = data[4: size]
	dumpFolder = getDumpFolder()
	if (not (dumpFolder is None)):
		with open (u"%s/Protein.zip" %(dumpFolder), 'wb') as protein:
			protein.write(zip)

	return size + 4

def ReadWorkbook(data, name, stream):
	dumpFolder = getDumpFolder()
	if (dumpFolder):
		##create a new Spreadsheet in new document
		wbk = xlrd.book.open_workbook_xls(file_contents=data, formatting_info=True)
		xls = copy(wbk)
		xls.save(f"{dumpFolder}/{name}.xls")
	return len(data)

def ReadOle10Native(stream, fnames):
	dumpFolder = getDumpFolder()
	if (not (dumpFolder is None)):
		ole = importerOle10Nateive.olenative()
		ole.read(stream)
		with open(u"%s/%s" %(dumpFolder, ole.label), 'wb') as f:
			f.write(ole.data)
	return

def ReadRSeSegment(data, offset, idx, schema):
	seg = RSeSegment()
	seg.name,        i = getLen32Text16(data, offset)
	seg.ID,          i = getUUID(data, i)
	seg.revisionRef, i = getUUID(data, i)
	seg.value1,      i = getUInt32(data, i)
	seg.count1,      i = getUInt32(data, i)
	seg.arr1,        i = getUInt32A(data, i, 5) # ???, ???, ???, numSec1, ???
	seg.count2,      i = getUInt32(data, i)
	seg.type,        i = getLen32Text16(data, i)
	if (schema < 0x11):
		seg.arr2, i = getUInt32A(data, i, 1)
		seg.arr2 += (0, )
	else:
		seg.arr2, i = getUInt32A(data, i, 2)
	seg.version, i = getVersionInfo(data, i)
	if (schema > 0x10):
		seg.value2, i = getUInt32(data, i)
	seg.objects = []
	seg.nodes = []
	getModel().RSeDb.segInfo.segments[seg.ID] = seg
	return seg, i

def ReadRSeSegmentObject(seg, data, offset, idx):
	obj = RSeSegmentObject()
	obj.revisionRef, i = getUUID(data, offset)
	obj.values, i = getUInt8A(data, i, 9)
	obj.segRef, i = getUUID(data, i)
	obj.value1, i = getUInt32(data, i)
	obj.value2, i = getUInt32(data, i)
	seg.objects.append(obj)
	return obj, i

def ReadRSeSegmentNode(seg, data, offset, count, idx):
	node = RSeSegmentValue2()
	node.index, i = getUInt32(data, offset)
	node.indexSegList1, i = getSInt16(data, i)
	node.indexSegList2, i = getSInt16(data, i)
	node.values, i = getUInt16A(data, i, count)
	node.number, i = getUInt16(data, i)
	seg.nodes.append(node)
	return i

def getVersionInfo(data, offset):
	v = VersionInfo() # getUInt8A(data, i, 8) # Rev_u8,Min_u8,Maj_u8,Flg_u8, Unknown_u32 [00 00 18 40 00 00 A0 41]
	v.revision, i = getUInt8(data, offset)
	v.minor,    i = getUInt8(data, i)
	v.major,    i = getUInt8(data, i)
	v.data,     i = getUInt8A(data, i, 5)
	return v, i

def ReadRSeSegmentType10(seg, data, offset):
	i = offset
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(seg, data, i, idx)
	return i

def ReadRSeSegmentType15(seg, data, offset):
	i = offset
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(seg, data, i, idx)
	cnt, i = getUInt32(data, i)
	for idx in range(1, cnt):
		i = ReadRSeSegmentNode(seg, data, i, 4, idx)
	return i

def ReadRSeSegmentType1A(seg, data, offset):
	i = offset
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(seg, data, i, idx)
	cnt, i = getUInt32(data, i)
	for idx in range(1, cnt):
		i = ReadRSeSegmentNode(seg, data, i, 4, idx)
	return i

def ReadRSeSegmentType1D(seg, data, offset):
	i = offset
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(seg, data, i, idx)
	cnt2, i = getUInt32(data, i)
	for idx in range(1, cnt2):
		i = ReadRSeSegmentNode(seg, data, i, 4, idx)
	return i

def ReadRSeSegmentType1E(seg, data, offset):
	i = offset
	cnt2 = 0
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(seg, data, i, idx)
		cnt2 = obj.value2
	for idx in range(1, cnt2):
		i = ReadRSeSegmentNode(seg, data, i, 6, idx)
	return i

def ReadRSeSegmentType1F(seg, data, offset):
	i    = offset
	cnt2 = 0
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(seg, data, i, idx)
		cnt2 = obj.value2
	for idx in range(1, cnt2):
		i = ReadRSeSegmentNode(seg, data, i, 6, idx)
	return i

def ReadRSeSegInfo10(db, data, offset):
	cnt, i = getSInt32(data, offset)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, db.schema)
		i = ReadRSeSegmentType10(seg, data, i)
	return i

def ReadRSeSegInfo15(db, data, offset):
	cnt, i = getSInt32(data, offset)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, db.schema)
		i = ReadRSeSegmentType15(seg, data, i)
	db.segInfo.val, i = getUInt16A(data, i, 2)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		db.segInfo.uidList1.append(txt)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		db.segInfo.uidList2.append(txt)
	return i

def ReadRSeSegInfo1A(db, data, offset):
	cnt, i = getSInt32(data, offset)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, db.schema)
		i = ReadRSeSegmentType1A(seg, data, i)
	db.segInfo.arr1, i = getUInt16A(data, i, 2)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		db.segInfo.uidList1.append(txt)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		db.segInfo.uidList2.append(txt)
	return i

def ReadRSeSegInfo1D(db, data):
	cnt, i = getSInt32(data, 0)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, db.schema)
		i = ReadRSeSegmentType1D(seg, data, i)
	db.segInfo.arr1, i = getUInt16A(data, i, 2)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		db.segInfo.uidList1.append(txt)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		db.segInfo.uidList2.append(txt)
	return i

def ReadRSeSegInfo1E(db, data):
	cnt, i = getSInt32(data, 0)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, db.schema)
		i = ReadRSeSegmentType1E(seg, data, i)
	db.segInfo.arr1, i = getUInt16A(data, i, 2)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		if (txt not in UUID_NAMES.values()):
			logAlways('\t' + txt)
		db.segInfo.uidList1.append(txt)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		if (txt not in UUID_NAMES.values()):
			logAlways('\t' + txt)
		db.segInfo.uidList2.append(txt)
	return i

def ReadRSeSegInfo1F(db, data):
	cnt, i = getSInt32(data, 0)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, db.schema)
		i = ReadRSeSegmentType1F(seg, data, i)
	db.segInfo.arr1, i = getUInt16A(data, i, 2)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		uid, i = getUUID(data, i)
		txt = getUidText(uid)
		db.segInfo.uidList1.append(txt)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		uid, i = getUUID(data, i)
		txt = getUidText(uid)
		db.segInfo.uidList2.append(txt)
	return i

def ReadRSeDb10(db, data, offset):
	db.segInfo.arr1, i = getUInt16A(data, offset, 8)
	db.vers2,        i = getVersionInfo(data, i)
	db.dat2,         i = getDateTime(data, i)
	db.segInfo.uid,  i = getUUID(data, i)
	db.segInfo.arr2, i = getUInt32A(data, i, 2)
	db.txt,          i = getLen32Text16(data, i)
	db.segInfo.arr3, i = getUInt32A(data, i, 6)
	return i

def ReadRSeDb15(db, data, offset):
	db.vers2,        i = getVersionInfo(data, offset)
	db.dat2,         i = getDateTime(data, i)
	db.segInfo.arr1, i = getUInt16A(data, i, 14)
	db.segInfo.date, i = getDateTime(data, i)
	db.segInfo.uid,  i = getUUID(data, i)
	db.segInfo.arr2, i = getUInt32A(data, i, 2)
	db.txt,       i = getLen32Text16(data, i)
	db.segInfo.arr3, i = getUInt32A(data, i, 6)
	return i

def ReadRSeDb1A(db, data, offset):
	db.vers2,         i = getVersionInfo(data, offset)
	db.dat2,          i = getDateTime(data, i)
	db.segInfo.text,  i = getLen32Text16(data, i)
	db.segInfo.arr1,  i = getUInt16A(data, i, 12)
	db.segInfo.date,  i = getDateTime(data, i)
	db.segInfo.uid,   i = getUUID(data, i)
	db.segInfo.u16,   i = getUInt16(data, i)
	db.segInfo.arr2,  i = getUInt32A(data, i, 2)
	db.txt,           i = getLen32Text16(data, i)
	db.segInfo.arr3,  i = getUInt32A(data, i, 2)
	db.segInfo.text2, i = getLen32Text16(data, i)
	db.segInfo.arr4,  i = getUInt32A(data, i, 4)
	return i

def ReadRSeDb1F(db, data, offset):
	db.vers2, i = getVersionInfo(data, offset)
	db.dat2, i  = getDateTime(data, i)
	db.txt, i   = getLen32Text16(data, i)
	return i

def ReadRSeDb(db, data):
	db.uid, i    = getUUID(data, 0)
	db.schema, i = getUInt32(data, i)
	db.vers1, i  = getVersionInfo(data, i)
	db.dat1, i   = getDateTime(data, i)

	if (db.schema in [0x1D, 0x1E, 0x1F]):
		i = ReadRSeDb1F(db, data, i)  # Inventor 2009 and later
	elif (db.schema == 0x10):
		i = ReadRSeDb10(db, data, i)
		i = ReadRSeSegInfo10(db, data, i)
	elif (db.schema == 0x15):
		i = ReadRSeDb15(db, data, i)
		i = ReadRSeSegInfo15(db, data, i)
	elif (db.schema == 0x1A):         # Inventor version v10
		i = ReadRSeDb1A(db, data, i)
		i = ReadRSeSegInfo1A(db, data, i)
	else:
		logError(u"ERROR> Reading RSeDB version %X - unknown format!", getModel().RSeDb.schema)

	return db

def ReadRSeDbRevisionInfo(revisions, data):
	version, i = getSInt32(data, 0)
	cnt, i = getSInt32(data, i)
	for n in range(cnt):
		info = RSeDbRevisionInfo()
		info.ID, i = getUUID(data, i)
		info.flags, i = getUInt32(data, i)
		if (version == 3):
			info.type, i = getUInt16(data, i)
			if (info.type == 0xFFFF):
				info.b, i = getBoolean(data, i)
				if (info.b):
					info.a = Struct('<fL').unpack_from(data, i)
					i += 8
				else:
					info.a = Struct('<fLfL').unpack_from(data, i)
					i += 16
		elif (version == 2):
			info.a, i = getUInt16A(data, i, 8)
		revisions.mapping[info.ID] = info
		revisions.infos.append(info)
	return i

def getRevisionInfoByUID(revUID):
	return getModel().RSeRevisions.mapping.get(revUID, revUID)

def getRevisionInfoByIndex(revIdx):
	revisions = getModel().RSeRevisions
	if (revIdx < len(revisions.infos)):
		return revisions.infos[revIdx]
	return revIdx

def ReadRSeMetaDataBlocksSize(value, data, offset):
	cnt, i = getUInt32(data, offset)
	for n in range(cnt):
		u32, i = getUInt32(data, i)
		sec = RSeStorageBlockSize(value, u32)
		value.sec1.append(sec)

	size, i = getUInt32(data, i)

	return i

def ReadRSeMetaDataSection2(value, data, offset):
	cnt, i = getUInt32(data, offset)
	for j in range(cnt):
		sec = RSeStorageSection2(value)
		if (value.ver == 3):
			uid, i = getUUID(data, i)
			sec.revision = getRevisionInfoByUID(uid)
			sec.flag, i = getUInt32(data, i)
			sec.val, i = getUInt16(data, i)
			sec.arr, i = getUInt16A(data, i, 5)
		elif (value.ver == 4):
			idx, i = getUInt32(data, i)
			sec.revision = getRevisionInfoByIndex(idx)
			sec.flag, i = getUInt32(data, i)
			sec.val, i = getUInt16(data, i)
			sec.arr, i = getUInt16A(data, i, 5)
		else:
			idx, i = getUInt32(data, i)
			sec.revision = getRevisionInfoByIndex(idx)
			sec.flag, i = getUInt32(data, i)
			sec.val, i = getUInt16(data, i)
			sec.arr = []
		value.sec2.append(sec)
	size, i = getUInt32(data, i)
	return i

def ReadRSeMetaDataSection3(value, data, offset):
	cnt, i = getUInt32(data, offset)
	for j in range(cnt):
		sec = RSeStorageSection3(value)
		sec.uid, i = getUUID(data, i)
		sec.arr, i = getUInt16A(data, i, 6)
		value.sec3.append(sec)
	size, i = getUInt32(data, i)
	return i

def ReadRSeMetaDataBlocksType(value, data, offset):
	cnt, i = getUInt32(data, offset)
	ARR = Struct('<HLHL').unpack_from
	for j in range(cnt):
		sec = RSeStorageBlockType(value)
		sec.uid, i = getUUID(data, i)
		sec.arr = ARR(data, i)
		i += 12
		value.secBlkTyps[j] = sec
	size, i = getUInt32(data, i)

	return i

def ReadRSeMetaDataSection5(value, data, offset, size):
	#index section 4
	sec = RSeStorageSection5(value)
	sec.indexSec4, i = getUInt16A(data, offset, size / 2)
	secSize, i = getUInt32(data, i)
	return i

def ReadRSeMetaDataSection6(value, data, offset, size, cnt):
	sec = RSeStorageSection6(value)

	i = offset
	# ???
	# arr32, i = getUInt32A(data, i, 2)
	# n16, i = getUInt16(data, i)
	# arrU = []
	# for n in range(n16)
	# 	uid, i = getUUID(data, i)
	# 	arr2, i = getUInt16A(data, i, 2)
	#   arrU.append(sec7(uid, arr2))
	# n16, i = getUInt16(data, i)
	# arrV = []
	# for n in range(n16)
	# 	arr1, i = getUInt16A(data, i, 3)
	#	arr.append(arr1)
	j = i + size - 8
	#n16, dummy = getUInt16(data, j)
	#arr, dummy = getUInt16A(data, j + 2, 3)
	#n2, dummy = getUInt16(data, j-6)
	#sec.arr2.append(arr)
	#while ((n16 != len(sec.arr2)) or (n2 < 0x1000)):
	#	j -= 6
	#	n16, dummy = getUInt16(data, j)
	#	arr, dummy = getUInt16A(data, j + 2, 3)
	#	n2, dummy = getUInt16(data, j-6)
	#	sec.arr2.insert(0, arr)
	#
	#j -= 0x16
	#n16, dummy = getUInt16(data, j)
	#uid, dummy = getUUID(data, j + 0x02)
	#u32, dummy = getUInt32(data, j + 0x12)
	#sec.arr1.append(RSeStorageSection4Data1(uid, u32))
	#while (n16 != len(sec.arr1)):
	#	j -= 0x14
	#	n16, dummy = getUInt16(data, j)
	#	uid, dummy = getUUID(data, j + 0x02)
	#	u32, dummy = getUInt32(data, j + 0x12)
	#	sec.arr1.insert(0, RSeStorageSection4Data1(uid, u32))
	#
	#size, i = getUInt32(data, i)
	return i

def ReadRSeMetaDataSection7(value, data, offset, size, cnt):
	i = offset
	for j in range(cnt):
		sec = RSeStorageSection7(value)
		if (size/cnt >= 0x4C):
			sec.segRef, i = getUUID(data, i)
			sec.revisionRef, i    = getUUID(data, i)
			sec.dbRef, i  = getUUID(data, i)
			sec.txt1, i   = getLen32Text16(data, i)
			sec.arr1, i   = getUInt16A(data, i, 4)
			sec.txt2, i   = getLen32Text16(data, i)
			sec.arr2, i   = getUInt16A(data, i, 2)
			sec.txt3, i   = getLen32Text16(data, i)
			sec.arr3, i   = getUInt16A(data, i, 2)
		else:
			sec.segRef, i = getUUID(data, i)
			sec.revisionRef, i    = getUUID(data, i)
		seg = findSegment(sec.segRef)
		if (seg is not None):
			sec.segName = seg.name

		value.sec7.append(sec)
	size, i = getUInt32(data, i)
	return i

def ReadRSeMetaDataSection8(value, data, offset, size, cnt):
	i = offset
	for j in range(cnt):
		sec = RSeStorageSection8(value)
		sec.dbRevisionInfoRef, i = getUUID(data, i)
		sec.arr, i = getUInt16A(data, i, 2)
		value.sec8.append(sec)
	size, i = getUInt32(data, i)
	return i

def ReadRSeMetaDataSection9(value, data, offset, size, cnt):
	i = offset
	for j in range(cnt):
		sec = RSeStorageSection9(value)
		sec.uid, i = getUUID(data, i)
		sec.arr, i = getUInt8A(data, i, 3)
		value.sec9.append(sec)
	size, i = getUInt32(data, i)
	return i

def ReadRSeMetaDataSectionA(value, data, offset, size, cnt):
	'''
	Same values as in RSeSegmentType
	'''
	i = offset
	for j in range(cnt):
		sec = RSeStorageSectionA(value)
		sec.arr, i = getUInt16A(data, i, 4)
		value.secA.append(sec)
	size, i = getUInt32(data, i)
	return i

def ReadRSeMetaDataSectionB(value, data, offset, size, cnt):
	i = offset
	for j in range(cnt):
		sec = RSeStorageSectionB(value)
		sec.arr, i = getUInt16A(data, i, 2)
		value.secB.append(sec)
	return i

def findSegment(segRef):
	return getModel().RSeDb.segInfo.segments.get(segRef)

def getReader(seg):
	logInfo(u"%2d: '%s' ('%s')", seg.index, seg.file, seg.name)
	seg.AcisList = []
	reader = SEG_TYPE_READERS.get(seg.type, None)
	if (reader is None):
		logError(u"    NO READER DEFINED FOR %s '%s'" %(seg.type, seg.name))
		return SegmentReader(seg)
	return reader(seg)

def ReadRSeMetaDataB(dataB, seg):
	reader = getReader(seg)
	if (reader):
		newFile = None
		dumpFolder = getDumpFolder()
		if (not (dumpFolder is None)):
			newFile = codecs.open(u"%s/%s.log" %(dumpFolder, seg.name), 'wb', 'utf8')
			newFile.write('[%s]\n' %(reader.version))
		i = 0
		uid, i = getUUID(dataB, i)
		n, i = getUInt16(dataB, i)
		z = zlib.decompressobj()
		data = z.decompress(dataB[i:])

		reader.ReadSegmentData(newFile, data)
		if (not (newFile is None)):
			newFile.close()
	return

def ReadRSeMetaDataM(dataM, name):
	i = 0
	value = Segment()
	value.txt1,  i = getLen32Text8(dataM, i)
	value.ver,   i = getUInt16(dataM, i)
	value.arr1,  i = getUInt16A(dataM, i, 8)
	value.name,  i = getLen32Text16(dataM, i)
	value.segID, i = getUUID(dataM, i)

	value.segment = findSegment(value.segID)
	if (value.segment is not None):
		value.segment.metaData = value

	value.arr2,   i = getUInt32A(dataM, i, 0x3)
	if (value.ver < 0x07):
		value.val1, i = getUInt32(dataM, i)
		value.dat1, i = getLen32Text8(dataM, i)
		value.val2, i = getUInt32(dataM, i)
		value.dat2, i = getLen32Text8(dataM, i)
	else:
		value.val1    = 0
		value.dat1, i = getLen32Text8(dataM, i)
		value.val2    = 0
		value.dat2, i = getLen32Text8(dataM, i)

	bTrue, i = getBoolean(dataM, i) # should always be True!!!

	z = zlib.decompressobj()
	data = z.decompress(dataM[i:])

	i = 0
	value.arr3, i = getUInt16A(data, i, 7)

	i = ReadRSeMetaDataBlocksSize(value, data, i)
	i = ReadRSeMetaDataSection2(value, data, i)
	i = ReadRSeMetaDataSection3(value, data, i)
	i = ReadRSeMetaDataBlocksType(value, data, i)

	l = 0x48
	i = len(data) - l - 0x18
	k = 11
	while (k > 4):
		s, j = getUInt32(data, i)
		c, j = getUInt32(data, j)
		if (c > 0):
			if (c < 0xFFFF):
				n = 0
				if (k==6):
					ReadRSeMetaDataSection6(value, data, j, l, c)
				elif (k==7):
					ReadRSeMetaDataSection7(value, data, j, l, c)
				elif (k==8):
					ReadRSeMetaDataSection8(value, data, j, l, c)
				elif (k==9):
					ReadRSeMetaDataSection9(value, data, j, l, c)
				elif (k==10):
					ReadRSeMetaDataSectionA(value, data, j, l, c)
				elif (k==11):
					ReadRSeMetaDataSectionB(value, data, j, l, c)
			else:
				ReadRSeMetaDataSection5(value, data, j, l)
		l = s - 4
		i -= (s + 4)
		k -= 1

	value.uid2, i = getUUID(data, len(data)-0x10)
	return value
