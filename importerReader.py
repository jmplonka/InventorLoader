# -*- coding: utf-8 -*-

'''
importerReader.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

import sys, os, uuid, datetime, re, zlib, operator, glob, struct, codecs, xlrd, FreeCAD, Import_IPT
from importerClasses     import *
from importerSegment     import SegmentReader
from importerBRep        import BRepReader
from importerDC          import DCReader
from importerApp         import AppReader
from importerBrowser     import BrowserReader
from importerDesignView  import DesignViewReader
from importerEeData      import EeDataReader
from importerEeScene     import EeSceneReader
from importerFBAttribute import FBAttributeReader
from importerGraphics    import GraphicsReader
from importerNotebook    import NotebookReader
from importerResults     import ResultReader
from importerUtils       import *
from xlutils.copy        import copy

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

# The model representing the content of the imported file
model = Inventor()

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
def getProperty(properties, key):
	value = properties.get(key, '')
	if (type(value) is str):
		if ((len(value) > 0) and (value[-1] == '\0')):
			value = value[0:-1]
	return value

def getPropertySetName(properties, path, model):
	name = getProperty(properties, KEY_SET_NAME)

	if (len(name)==0):
		name = path[-1][1:]

	languageCode = properties[KEY_LANGUAGE_CODE] if (KEY_LANGUAGE_CODE in properties) else 1031 # en_EN
	logInfo(u"\t'%s': (LC = %X)", name, languageCode)

	if (name not in model.iProperties):
		model.iProperties[name] = {}

	keys = properties.keys()
	keys = sorted(keys)

	return name, keys

def ReadInventorSummaryInformation(doc, properties, path):
	global model

	name, keys = getPropertySetName(properties, path, model)

	if (doc):
		setAuthor(getProperty(properties, KEY_SUM_INFO_AUTHOR))
		doc.CreatedBy = getAuthor()
		doc.Comment = getProperty(properties, KEY_SUM_INFO_COMMENT)
		doc.LastModifiedBy = getProperty(properties, KEY_SUM_INFO_MODIFYER)

	for key in keys:
		if ((key != KEY_CODEPAGE) and (key != KEY_SET_NAME) and (key != KEY_LANGUAGE_CODE)):
			val = getProperty(properties, key)
			if (val is not None):
				if (key == KEY_THUMBNAIL_1):
					val = writeThumbnail(val)
				elif (key == KEY_THUMBNAIL_2):
					val = writeThumbnail(val)
				if (type(val) == str):
					if (sys.version_info.major < 3):
						logInfo(u"\t\t%s = %s", Inventor_Summary_Information.get(key, key), val.decode('utf8'))
					else:
						logInfo(u"\t\t%s = %s", Inventor_Summary_Information.get(key, key), val)
				else:
					logInfo(u"\t\t%s = %s", Inventor_Summary_Information.get(key, key), val)
				model.iProperties[name][key] = (Inventor_Summary_Information.get(key, key), val)
	return

def ReadInventorDocumentSummaryInformation(doc, properties, path):
	global model

	name, keys = getPropertySetName(properties, path, model)

	if (doc):
		doc.Company = getProperty(properties, KEY_DOC_SUM_INFO_COMPANY)

	for key in keys:
		if ((key != KEY_CODEPAGE) and (key != KEY_SET_NAME) and (key != KEY_LANGUAGE_CODE)):
			val = getProperty(properties, key)
			if (val is not None):
				if (type(val) == str):
					if (sys.version_info.major < 3):
						logInfo(u"\t\t%s = %s", Inventor_Document_Summary_Information.get(key, key), val.decode('utf8'))
					else:
						logInfo(u"\t\t%s = %s", Inventor_Document_Summary_Information.get(key, key), val)
				else:
					logInfo(u"\t\t%s = %s", Inventor_Document_Summary_Information.get(key, key), val)
				model.iProperties[name][key] = (Inventor_Document_Summary_Information.get(key, key), val)
	return

def ReadOtherProperties(properties, path, keynames={}):
	global model

	name, keys = getPropertySetName(properties, path, model)

	for key in keys:
		if ((key != KEY_CODEPAGE) and (key != KEY_SET_NAME) and (key != KEY_LANGUAGE_CODE)):
			val = getProperty(properties, key)
			if (val is not None):
				keyName = keynames.get(key, key)
				if (keyName == 'PartIcon'):
					logInfo(u"\t\t%s = [ICON]", keyName)
				elif (type(val) == str):
					try:
						if (sys.version_info.major < 3):
							logInfo(u"\t\t%s = %s", keyName, val.decode('utf8'))
						else:
							logInfo(u"\t\t%s = %s", keyName, val)
					except:
						logInfo(u"\t\t%s = %r", keyName, val)
				else:
					logInfo(u"\t\t%s = %s", keyName, val)

				model.iProperties[name][key] = (keyName, val)

	return

def ReadProtein(data):
	size, i = getSInt32(data, 0)
	zip = data[4: size]

	folder = getInventorFile()[0:-4]
	protein = open ('%s\\Protein.zip' %(folder), 'wb')
	protein.write(zip)
	protein.close()
	return size + 4

def ReadWorkbook(doc, data, name, stream):
	##create a new Spreadsheet in new document
	folder = getInventorFile()[0:-4]
	filename = '%s\\%s.xls' %(folder, name)

	wbk = xlrd.book.open_workbook_xls(file_contents=data, formatting_info=True)
	for name in wbk.name_obj_list:
		r = name.area2d()

	for idx in range(0, wbk.nsheets):
		sht = wbk.sheet_by_index(idx)
		rows = sht.nrows
		cols = sht.ncols
		shtName = stream + '_' + sht.name
		#TODO handle merged cells
		#TODO handle cell names
		for c in range(0, cols):
			#spreadsheet.setColumnWidth(chr(0x41+c), sht.computed_column_width(c))
			for r in range(0, rows):
				rng = '%s%d' %(chr(0x41+c), r+1)
		idx += 1

	xls = copy(wbk)
	xls.save(filename)
	# logInfo(u">>>INFO - found workook: stored as %r!", filename)
	return len(data)

def ReadRSeSegment(data, offset, idx, count):
	global model

	seg = RSeSegment()
	seg.name, i = getLen32Text16(data, offset)
	seg.ID, i = getUUID(data, i)
	seg.revisionRef, i = getUUID(data, i)
	seg.value1, i = getUInt32(data, i)
	seg.count1, i = getUInt32(data, i)
	seg.arr1, i = getUInt32A(data, i, 5) # ???, ???, ???, numSec1, ???
	seg.count2, i = getUInt32(data, i)
	seg.type, i = getLen32Text16(data, i)
	seg.arr2, i = getUInt16A(data, i, count)
	seg.objects = []
	seg.nodes = []

	model.RSeSegInfo.segments[seg.ID] = seg

	return seg, i

def ReadRSeSegmentObject(data, offset, seg, idx):
	obj = RSeSegmentObject()
	obj.revisionRef, i = getUUID(data, offset)
	obj.values, i = getUInt8A(data, i, 9)
	obj.segRef, i = getUUID(data, i)
	obj.value1, i = getUInt32(data, i)
	obj.value2, i = getUInt32(data, i)
	seg.objects.append(obj)

	return obj, i

def ReadRSeSegmentNode(data, offset, seg, count, idx):
	node = RSeSegmentValue2()
	node.index, i = getUInt32(data, offset)
	node.indexSegList1, i = getSInt16(data, i)
	node.indexSegList2, i = getSInt16(data, i)
	node.values, i = getUInt16A(data, i, count)
	node.number, i = getUInt16(data, i)
	seg.nodes.append(node)

	return node, i

def ReadRSeSegmentType10(data, offset, seg):
	i = offset
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(data, i, seg, idx)
	return i

def ReadRSeSegmentType15(data, offset, seg):
	i = offset
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(data, i, seg, idx)
	cnt, i = getUInt32(data, i)
	for idx in range(1, cnt):
		node, i = ReadRSeSegmentNode(data, i, seg, 4, idx)
	return i

def ReadRSeSegmentType1A(data, offset, seg):
	i = offset
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(data, i, seg, idx)
	cnt, i = getUInt32(data, i)
	for idx in range(1, cnt):
		node, i = ReadRSeSegmentNode(data, i, seg, 4, idx)
	return i

def ReadRSeSegmentType1D(data, offset, seg):
	i = offset
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(data, i, seg, idx)
	cnt, i = getUInt32(data, i)
	for idx in range(1, cnt):
		node, i = ReadRSeSegmentNode(data, i, seg, 4, idx)
	return i

def ReadRSeSegmentType1F(data, offset, seg):
	i    = offset
	cnt2 = 0
	for idx in range(seg.count1):
		obj, i = ReadRSeSegmentObject(data, i, seg, idx)
		cnt2 = obj.value2
	for idx in range(1, cnt2):
		node, i = ReadRSeSegmentNode(data, i, seg, 6, idx)
	return i

def ReadRSeSegInfo10(data, offset):
	global model

	model.RSeSegInfo = RSeSegInformation()

	cnt, i = getSInt32(data, offset)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, 6)
		i = ReadRSeSegmentType10(data, i, seg)
		model.RSeSegInfo.segments[seg.name] = seg
	return	 i

def ReadRSeSegInfo15(data, offset):
	global model

	model.RSeSegInfo = RSeSegInformation()
	cnt, i = getSInt32(data, offset)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, 6)
		i = ReadRSeSegmentType15(data, i, seg)
		model.RSeSegInfo.segments[seg.name] = seg
	model.RSeSegInfo.val, i = getUInt16A(data, i, 2)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		model.RSeSegInfo.uidList1.append(txt)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		model.RSeSegInfo.uidList2.append(txt)
	return	 i

def ReadRSeSegInfo1A(data, offset):
	global model

	model.RSeSegInfo = RSeSegInformation()
	cnt, i = getSInt32(data, offset)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, 8)
		i = ReadRSeSegmentType1A(data, i, seg)
		model.RSeSegInfo.segments[seg.name] = seg
	model.RSeSegInfo.val, i = getUInt16A(data, i, 2)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		model.RSeSegInfo.uidList1.append(txt)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		model.RSeSegInfo.uidList2.append(txt)
	return i

def ReadRSeSegInfo1D(data):
	global model

	model.RSeSegInfo = RSeSegInformation()
	cnt, i = getSInt32(data, 0)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, 8)
		i = ReadRSeSegmentType1D(data, i, seg)
		model.RSeSegInfo.segments[seg.name] = seg
	model.RSeSegInfo.val, i = getUInt16A(data, i, 2)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		model.RSeSegInfo.uidList1.append(txt)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		txt, i = getLen32Text16(data, i)
		model.RSeSegInfo.uidList2.append(txt)
	return i

def ReadRSeSegInfo1F(data):
	global model

	model.RSeSegInfo = RSeSegInformation()
	cnt, i = getSInt32(data, 0)
	for idx in range(cnt):
		seg, i = ReadRSeSegment(data, i, idx, 10)
		i = ReadRSeSegmentType1F(data, i, seg)
		model.RSeSegInfo.segments[seg.name] = seg
	model.RSeSegInfo.val, i = getUInt16A(data, i, 2)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		uid, i = getUUID(data, i)
		txt = getUidText(uid)
		model.RSeSegInfo.uidList1.append(txt)
	cnt, i = getUInt32(data, i)
	for idx in range(cnt):
		uid, i = getUUID(data, i)
		txt = getUidText(uid)
		model.RSeSegInfo.uidList2.append(txt)
	return i

def ReadRSeDb10(db, data, offset):
	db.arr3, i = getUInt16A(data, offset, 8)
	db.arr2, i = getUInt16A(data, i, 4)
	db.dat2, i = getDateTime(data, i)
	db.uid2, i = getUUID(data, i)
	db.arr4, i = getUInt32A(data, i, 2)
	db.txt, i  = getLen32Text16(data, i)
	db.arr5, i = getUInt32A(data, i, 6)

	logInfo(u"\t%r: %s", db.txt, db.comment)
	logInfo(u"\t%s [%X]", db.uid, db.version)
	logInfo(u"\t[%s]", IntArr2Str(db.arr1, 4))
	logInfo(u"\t[%s]", IntArr2Str(db.arr2, 4))

	return i

def ReadRSeDb15(db, data, offset):
	db.arr2, i = getUInt16A(data, offset, 4)
	db.dat2, i = getDateTime(data, i)
	db.arr3, i = getUInt16A(data, i, 14)
	db.dat3, i = getDateTime(data, i)
	db.uid2, i = getUUID(data, i)
	db.arr4, i = getUInt32A(data, i, 2)
	db.txt, i = getLen32Text16(data, i)
	db.arr5, i = getUInt32A(data, i, 6)

	logInfo(u"\t%r: %s", db.txt, db.comment)
	logInfo(u"\t%s [%X]", db.uid, db.version)
	logInfo(u"\t[%s]", IntArr2Str(db.arr1, 4))
	logInfo(u"\t[%s]", IntArr2Str(db.arr2, 4))
	logInfo(u"\t[%s]: %s", IntArr2Str(db.arr3, 4), db.uid2)
	logInfo(u"\t[%s]", IntArr2Str(db.arr4, 4))
	logInfo(u"\t[%s]", IntArr2Str(db.arr5, 4))

	return i

def ReadRSeDb1A(db, data, offset):
	db.arr2, i = getUInt16A(data, offset, 4)
	db.dat2, i = getDateTime(data, i)
	db.txt2, i = getLen32Text16(data, i)
	db.arr3, i = getUInt16A(data, i, 12)
	db.dat3, i = getDateTime(data, i)
	db.uid2, i = getUUID(data, i)
	db.u16, i  = getUInt16(data, i)
	db.arr4, i = getUInt32A(data, i, 2)
	db.txt, i  = getLen32Text16(data, i)
	db.arr5, i = getUInt32A(data, i, 2)
	db.txt3, i = getLen32Text16(data, i)
	db.arr6, i = getUInt32A(data, i, 4)

	logInfo(u"\t%r: %s", db.txt, db.txt2)
	logInfo(u"\t%s [%X]", db.uid, db.version)
	logInfo(u"\t[%s]", IntArr2Str(db.arr1, 4))
	logInfo(u"\t[%s]", IntArr2Str(db.arr2, 4))
	logInfo(u"\t[%s]: %s", IntArr2Str(db.arr3, 4), db.uid2)
	logInfo(u"\t%d: [%s]", db.u16, IntArr2Str(db.arr4, 4))
	logInfo(u"\t[%s]", IntArr2Str(db.arr5, 4))
	logInfo(u"\t%r", db.txt3)
	logInfo(u"\t[%s]", IntArr2Str(db.arr6, 4))

	return i

def ReadRSeDb(data):
	global model

	db = RSeDatabase()
	db.uid, i     = getUUID(data, 0)
	db.version, i = getUInt32(data, i)
	db.arr1, i    = getUInt16A(data, i, 4)
	db.dat1, i    = getDateTime(data, i)

	if (db.version in [0x1D, 0x1F]):
		db.arr2, i = getUInt16A(data, i, 4)
		db.dat2, i = getDateTime(data, i)
		db.txt, i  = getLen32Text16(data, i)
	elif (db.version == 0x10):
		i = ReadRSeDb10(db, data, i)
		i = ReadRSeSegInfo10(data, i)
	elif (db.version == 0x15):
		i = ReadRSeDb15(db, data, i)
		i = ReadRSeSegInfo15(data, i)
	elif (db.version == 0x1A):
		i = ReadRSeDb1A(db, data, i)
		i = ReadRSeSegInfo1A(data, i)
	else:
		logError(u"ERROR> Reading RSeDB version %X - unknown format!", model.RSeDb.version)

	model.RSeDb = db

	return i

def ReadRSeDbRevisionInfo(data):
	global model

	version, i = getSInt32(data, 0)
	model.RSeDbRevisionInfoMap = {}
	model.RSeDbRevisionInfoList = []
	cnt, i = getSInt32(data, i)
	for n in range(cnt):
		info = RSeDbRevisionInfo()
		info.ID, i = getUUID(data, i)
		info.value1, i = getUInt16(data, i)
		info.value2, i = getUInt16(data, i)
		if (version == 3):
			info.type, i = getUInt16(data, i)
		elif (version == 2):
			info.data, i = getUInt16A(data, i, 8)
			info.type = 0
		else:
			info.type = 0
		if (info.type == 0xFFFF):
			b, i = getBoolean(data, i)
			f, i = getFloat32(data, i)
			if (b):
				info.data, i = getUInt16A(data, i, 4)
			else:
				info.data, i = getUInt32A(data, i, 4)
			info.data = (f, n)
		else:
			info.data = (0.0, 0)
		model.RSeDbRevisionInfoMap[info.ID] = info
		model.RSeDbRevisionInfoList.append(info)
	return i

def getRevisionInfoByUID(revUID):
	global model

	if ((model.RSeDbRevisionInfoMap is not None) and (revUID in model.RSeDbRevisionInfoMap)):
		return model.RSeDbRevisionInfoMap[revUID]

	return revUID

def getRevisionInfoByIndex(revIdx):
	global model

	if ((model.RSeDbRevisionInfoList is not None) and (len(model.RSeDbRevisionInfoList) > revIdx)):
		return model.RSeDbRevisionInfoList[revIdx]

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
	global model

	return model.RSeSegInfo.segments.get(segRef)

def getReader(seg):
	logInfo(u"%2d: '%s' ('%s')", seg.index, seg.file, seg.name)
	reader = None
	seg.AcisList = []
	if (seg.isBRep()): # BoundaryRepresentation for SAT/STEP based import
		if (isStrategySat() or isStrategyStep()):
			reader = BRepReader()
	elif (seg.isDC()):
		if (isStrategyNative()):   # DocumentComponent for featured base import
			reader = DCReader()
	elif (seg.isApp()): # ApplicationSettings for colors
		reader = AppReader()
#	elif (seg.isBrowser():
#		reader = BrowserReader()
#	elif (seg.isDefault()):
#		reader = DefaultReader()
#	elif (seg.isGraphics()): # required for Meshes
#		reader = GraphicsReader()
#	elif (seg.isResult()):
#		reader = ResultReader()
#	elif (seg.isDesignView()):
#		reader = DesignViewReader()
#	elif (seg.isEeData()):
#		reader = EeDataReader()
#	elif (seg.isEeScene()):
#		reader = EeSceneReader()
#	elif (seg.isFBAttribute()):
#		reader = FBAttributeReader()
#	elif (seg.isNBNotebook()):
#		reader = NotebookReader()
	if (reader is None):
		logInfo(u"    IGNORED!")
		#reader = SegmentReader()
	return reader

def ReadRSeMetaDataB(dataB, seg):
	reader = getReader(seg)
	if (reader):
		folder = getInventorFile()[0:-4]

		filename = '%s\\%sB.log' %(folder, seg.name)
		newFile = codecs.open(filename, 'wb', 'utf8')

		newFile.write('[%s]\n' %(getFileVersion()))
		i = 0
		uid, i = getUUID(dataB, i)
		n, i = getUInt16(dataB, i)
		z = zlib.decompressobj()
		data = z.decompress(dataB[i:])

		reader.ReadSegmentData(newFile, data, seg)

		newFile.close()

	return len(dataB)

def ReadRSeMetaDataM(dataM, name):
	global model

	i = 0
	folder = getInventorFile()[0:-4]

	value = RSeMetaData()
	value.txt1, i = getLen32Text8(dataM, i)
	value.ver, i = getUInt16(dataM, i)
	value.arr1, i = getUInt16A(dataM, i, 8)
	if (value.arr1[0] + value.arr1[1] + value.arr1[2] + value.arr1[3] + value.arr1[4] == 0):
		value.name = name
		value.segRef = None
		value.arr2 = []
		return value
	value.name, i = getLen32Text16(dataM, i)
	value.segRef, i = getUUID(dataM, i)
	value.arr2, i = getUInt32A(dataM, i, 0x3)
	seg = findSegment(value.segRef)
	if (seg is not None):
		seg.metaData = value

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

	# dataM[i] should always be '\0x01' !!!
	x01, i = getUInt8(dataM, i)

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
	model.RSeStorageData[value.name] = value
	return value
