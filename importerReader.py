# -*- coding: utf-8 -*-

'''
importerReader.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

import sys, os, uuid, datetime, re, zlib, operator, glob, struct, codecs, xlrd, FreeCAD, Import_IPT
from importerClasses     import *
from importerSegment     import SegmentReader
from importerApp         import AppReader
from importerBRep        import BRepReader
from importerBrowser     import BrowserReader
from importerDC          import DCReader
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
	logMessage("\t'%s': (LC = %X)" %(name, languageCode), LOG.LOG_ALWAYS)

	if (name not in model.iProperties):
		model.iProperties[name] = {}

	keys = properties.keys()
	keys.sort()

	return name, keys

def ReadInventorSummaryInformation(doc, properties, path):
	global model

	name, keys = getPropertySetName(properties, path, model)

	if (doc):
		doc.CreatedBy = getProperty(properties, KEY_SUM_INFO_AUTHOR)
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
				logMessage("\t\t%s = %s" %(Inventor_Summary_Information.get(key, key), val), LOG.LOG_DEBUG)
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
				logMessage("\t\t%s = %s" %(Inventor_Document_Summary_Information.get(key, key), val), LOG.LOG_DEBUG)
				model.iProperties[name][key] = (Inventor_Document_Summary_Information.get(key, key), val)
	return

def ReadOtherProperties(properties, path, keynames={}):
	global model

	name, keys = getPropertySetName(properties, path, model)

	for key in keys:
		if ((key != KEY_CODEPAGE) and (key != KEY_SET_NAME) and (key != KEY_LANGUAGE_CODE)):
			val = getProperty(properties, key)
			if (val is not None):
				logMessage("\t\t%s = %s" %(keynames.get(key, key), val), LOG.LOG_DEBUG)
				model.iProperties[name][key] = (keynames.get(key, key), val)

	return

def ReadUFRxDoc(data):
	global model

#	try:
	model.UFRxDoc = UFRxDocument()
	model.UFRxDoc.version, i = getUInt16(data, 0)
	cnt, i = getUInt16(data, i)
	model.UFRxDoc.arr1, i = getUInt16A(data, i, cnt)
	logMessage('\t[%s]' % (IntArr2Str(model.UFRxDoc.arr1, 4)), LOG.LOG_DEBUG)
	model.UFRxDoc.arr2, i = getUInt16A(data, i, 4)
	logMessage('\t[%s]' % (IntArr2Str(model.UFRxDoc.arr2, 4)), LOG.LOG_DEBUG)
	model.UFRxDoc.dat1, i = getDateTime(data, i)
	# logMessage('\t%s' %(model.UFRxDoc.dat1))
	model.UFRxDoc.arr3, i = getUInt16A(data, i, 4)
	logMessage('\t[%s]' % (IntArr2Str(model.UFRxDoc.arr3, 4)), LOG.LOG_DEBUG)
	model.UFRxDoc.dat2, i = getDateTime(data, i)
	# logMessage('\t%s' %(model.UFRxDoc.dat2))
	model.UFRxDoc.comment, i  = getLen32Text16(data, i)
	logMessage('\t%r' %(model.UFRxDoc.comment), LOG.LOG_DEBUG)
	model.UFRxDoc.arr4, i = getUInt16A(data, i, 8)
	logMessage('\t[%s]' % (IntArr2Str(model.UFRxDoc.arr4, 4)), LOG.LOG_DEBUG)
	model.UFRxDoc.arr5, i = getUInt16A(data, i, 4)
	logMessage('\t[%s]' % (IntArr2Str(model.UFRxDoc.arr5, 4)), LOG.LOG_DEBUG)
	model.UFRxDoc.dat3, i = getDateTime(data, i)
	# logMessage('\t%s' % (model.UFRxDoc.dat3))
	model.UFRxDoc.revisionRef, i = getUUID(data, i, 'UFRxDoc.revisionRef')
	# logMessage('\t%s' % (model.UFRxDoc.revisionRef))
	if (model.UFRxDoc.version == 0x08):
		model.UFRxDoc.ui1, i  = getUInt16(data, i)
	else:
		model.UFRxDoc.ui1, i  = getUInt32(data, i)
	logMessage('\t%X' % (model.UFRxDoc.ui1), LOG.LOG_DEBUG)
	model.UFRxDoc.dbRef, i = getUUID(data, i, 'UFRxDoc.dbRef')
	# logMessage('\t%s' % (model.UFRxDoc.dbRef))
	model.UFRxDoc.filename, i  = getLen32Text16(data, i)
	logMessage('\t%r' % (model.UFRxDoc.filename), LOG.LOG_DEBUG)
	model.UFRxDoc.arr6, i = getUInt16(data, i)

	cnt, i = getUInt32(data, i)
	if (cnt>0):
		return i-4

	logMessage('\t%04X' % (model.UFRxDoc.arr6), LOG.LOG_DEBUG)
	cnt, i = getUInt32(data, i)
	j = 1
	while (j <= cnt):
		txt, i = getLen32Text16(data, i)
		key, i = getLen32Text16(data, i)
		model.UFRxDoc.prps[key] = txt
		logMessage('\t%d: %s=%r' % (j, key, txt))
		j += 1

	# cnt, i = getUInt32(data, i)
	# j = 1
	# while (j <= cnt):
	# 	txt, i = getLen32Text16(data, i)
	# 	key, i = getLen32Text16(data, i)
	# 	model.UFRxDoc.prps[key] = txt
	# 	logMessage('\t%d: %s=%r' % (j, key, txt))
	# 	j += 1
	# model.UFRxDoc.ui2, i  = getUInt32(data, i)
	# logMessage('\t\t%d' % (model.UFRxDoc.ui2))
	# model.UFRxDoc.txt3, i  = getLen32Text16(data, i)
	# logMessage('\t%r' % (model.UFRxDoc.txt3))
	# model.UFRxDoc.ui3, i  = getUInt32(data, i)
	# logMessage('\t\t%d' % (model.UFRxDoc.ui3))
	# model.UFRxDoc.arr7, i = getUInt16A(data, i, 9)
	# logMessage('\t[%s]' % (IntArr2Str(model.UFRxDoc.arr7, 4)))
	# if (model.UFRxDoc.arr7[0] == 0x17):
	# 	uid1, i =  getUUID(data, i , 'UFRxDoc.uid1')
	# 	uid2, i =  getUUID(data, i , 'UFRxDoc.uid2')
	# 	u16, i = getUInt16(data, i)
	# 	logMessage('\t%s,%s,%04X' %(uid1, uid1, u16))
	# model.UFRxDoc.arr8, i = getUInt32A(data, i, 4)
	# logMessage('\t[%s]' % (IntArr2Str(model.UFRxDoc.arr8, 4)))
	# cnt, i = getUInt32(data, i)
	# j = 1
	# while (j <= cnt):
	# 	#01 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00,'Embedding 1:{00020820-0000-0000-C000-000000000046}\',                   FF FF FF FF,'',         00 00,'',              00 00 00 00 00 00 00 00
	# 	arr1, i = getUInt32A(data, i, 5)
	# 	txt1, i = getLen32Text16(data, i)
	# 	u32, i  = getUInt32(data, i)
	# 	txt2, i = getLen32Text16(data, i)
	# 	u16, i = getUInt16(data, i)
	# 	txt3, i = getLen32Text16(data, i)
	# 	arr2, i = getUInt32A(data, i, 2)
	# 	logMessage('\t\t%d: [%s],\'%s\',%08X,\'%s\',%04X,\'%s\',[%s]' %(j, IntArr2Str(arr1, 1), txt1, u32, txt2, u16, txt3, IntArr2Str(arr2, 4)))
	# 	j += 1
	# model.UFRxDoc.arr9, i = getUInt32A(data, i, 4)
	# logMessage('\t[%s]' % (IntArr2Str(model.UFRxDoc.arr9, 4)))
	# model.UFRxDoc.arrA, i = getUInt8A(data, i, 9)
	# logMessage('\t[%s]' % (IntArr2Str(model.UFRxDoc.arrA, 2)))
	# next = True
	# while (next):
	# 	u8, i = getUInt8(data, i)
	# 	if (u8 == 0x1D):
	# 		u8, i = getUInt8(data, i)
	# 		logMessage('\t1D,%02X' % (u8))
	# 	elif ((u8 == 0) or (u8 == 1)):
	# 		i -= 1
	# 		next = False
	# 	else:
	# 		uid1, i = getUUID(data, i, 'UFRxDoc[%X].uid1' % (u8))
	# 		if ((u8 == 0x11) or (u8 == 0x13) or (u8 == 0x16) or (u8 == 0x17) or (u8 == 0x18) or (u8 == 0x1F) or (u8 == 0x24) or (u8 == 0x25)):
	# 			uid2, i = getUUID(data, i, 'UFRxDoc[%X].uid2' % (u8))
	# 			logMessage('\t%02X,%s,%s' % (u8, uid1, uid2))
	# 		else:
	# 			logMessage('\t%02X,%s' % (u8, uid1))
	# u16, i = getUInt16(data, i)
	# logMessage('\t%04X' % (u16))
	# cnt, i = getUInt32(data, i)
	# j = 1
	# while (j <= cnt):
	# 	uid3, i = getUUID(data, i, 'UFRxDoc[%d].uid3' % (j))
	# 	logMessage('\t%02X: %s' % (j, uid3))
	# 	j += 1
	# cnt, i = getUInt32(data, i)
	# j = 1
	# while (j <= cnt):
	# 	uid4, i = getUUID(data, i, 'UFRxDoc[%d].uid4' % (j))
	# 	u8a, i = getUInt8A(data, i, 11)
	# 	txt1, i = getLen32Text16(data, i)
	# 	logMessage('\t%02X: %s,[%s],\'%s\'' % (j, uid4, IntArr2Str(u8a, 2), txt1))
	# 	j += 1
#	except Exception as err:
#		exc_type, exc_obj, exc_tb = sys.exc_info()
#		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#		logMessage('>>>ERROR in %s, line %d: %s' %(fname, exc_tb.tb_lineno, err), LOG.LOG_INFO)
	return i

def ReadProtein(data):
	size, i = getSInt32(data, 0)
	zip = data[4: size]

	folder = getInventorFile()[0:-4]
	protein = open ('%s\\Protein.zip' %(folder), 'wb')
	protein.write(zip)
	protein.close()
	# logMessage('\t>>>INFO: found protein - stored as \'%s\\%s\'!' %(folder, 'Protein.zip'), LOG_INFO)
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
	# logMessage('>>>INFO - found workook: stored as %r!' %(filename), LOG.LOG_INFO)
	return len(data)

def ReadRSeSegment(data, offset, idx, count):
	global model

	seg = RSeSegment()
	seg.name, i = getLen32Text16(data, offset)
	seg.ID, i = getUUID(data, i, 'RSeSegment[%d].ID'  %(idx))
	seg.revisionRef, i = getUUID(data, i, 'RSeSegment.revisionRef')
	seg.value1, i = getUInt32(data, i)
	seg.count1, i = getUInt32(data, i)
	seg.arr1, i = getUInt32A(data, i, 5) # ???, ???, ???, numSec1, ???
	seg.count2, i = getUInt32(data, i)
	seg.type, i = getLen32Text16(data, i)
	seg.arr2, i = getUInt16A(data, i, count)
	seg.objects = []
	seg.nodes = []

	model.RSeSegInfo.segments[seg.ID] = seg

	logMessage('\t%s' %(seg.name))
	logMessage('\t\t[{0},{1}]'.format(seg.value1, IntArr2Str(seg.arr1, 4)))
	logMessage('\t\t{0}: [{1}]'.format(seg.type, IntArr2Str(seg.arr2, 4)))

	return seg, i

def ReadRSeSegmentObject(data, offset, seg, idx):
	i = offset

	obj = RSeSegmentObject()
	obj.revisionRef, i = getUUID(data, i, 'RSeSegmentType.revisionRef')
	obj.values, i = getUInt8A(data, i, 9)
	obj.segRef, i = getUUID(data, i, 'RSeSegmentType.segRef')
	obj.value1, i = getUInt32(data, i)
	obj.value2, i = getUInt32(data, i)
	seg.objects.append(obj)

	return obj, i

def ReadRSeSegmentNode(data, offset, seg, count, idx):
	i = offset

	node = RSeSegmentValue2()
	node.index, i = getUInt32(data, i)
	node.indexSegList1, i = getSInt16(data, i)
	node.indexSegList2, i = getSInt16(data, i)
	node.values, i = getUInt16A(data, i, count)
	node.number, i = getUInt16(data, i)
	seg.nodes.append(node)

	logMessage('\t\t%2X: %s' %(idx, node))

	return node, i

def ReadRSeSegmentType10(data, offset, seg):
	i = offset

	cnt = seg.count1
	idx = 0
	while (idx < cnt):
		obj, i = ReadRSeSegmentObject(data, i, seg, idx)
		idx += 1
	return i

def ReadRSeSegmentType15(data, offset, seg):
	i = offset

	cnt = seg.count1
	idx = 0
	while (idx < cnt):
		obj, i = ReadRSeSegmentObject(data, i, seg, idx)
		idx += 1

	cnt, i = getUInt32(data, i)
	idx = 1
	while (idx < cnt):
		node, i = ReadRSeSegmentNode(data, i, seg, 4, idx)
		idx += 1

	return i

def ReadRSeSegmentType1A(data, offset, seg):
	i = offset

	cnt = seg.count1
	idx = 0
	while (idx < cnt):
		obj, i = ReadRSeSegmentObject(data, i, seg, idx)
		idx += 1

	cnt, i = getUInt32(data, i)
	idx = 1
	while (idx < cnt):
		node, i = ReadRSeSegmentNode(data, i, seg, 4, idx)
		idx += 1

	return i

def ReadRSeSegmentType1D(data, offset, seg):
	i = offset

	cnt = seg.count1
	idx = 0
	while (idx < cnt):
		obj, i = ReadRSeSegmentObject(data, i, seg, idx)
		idx += 1

	cnt, i = getUInt32(data, i)
	idx = 1
	while (idx < cnt):
		node, i = ReadRSeSegmentNode(data, i, seg, 4, idx)
		idx += 1

	return i

def ReadRSeSegmentType1F(data, offset, seg):
	i = offset
	cnt2 = 0

	cnt = seg.count1
	idx = 0
	while (idx < cnt):
		obj, i = ReadRSeSegmentObject(data, i, seg, idx)
		idx += 1
		cnt2 = obj.value2

	idx = 1
	while (idx < cnt2):
		node, i = ReadRSeSegmentNode(data, i, seg, 6, idx)
		idx += 1
	return i

def ReadRSeSegInfo10(data, offset):
	global model

	model.RSeSegInfo = RSeSegInformation()

	cnt, i = getSInt32(data, offset)
	idx = 0
	while (idx < cnt):
		seg, i = ReadRSeSegment(data, i, idx, 6)

		i = ReadRSeSegmentType10(data, i, seg)

		model.RSeSegInfo.segments[seg.name] = seg

		idx += 1

	return	 i

def ReadRSeSegInfo15(data, offset):
	global model

	model.RSeSegInfo = RSeSegInformation()

	cnt, i = getSInt32(data, offset)
	idx = 0
	while (idx < cnt):
		seg, i = ReadRSeSegment(data, i, idx, 6)

		i = ReadRSeSegmentType15(data, i, seg)

		model.RSeSegInfo.segments[seg.name] = seg

		idx += 1

	model.RSeSegInfo.val, i = getUInt16A(data, i, 2)
	logMessage('\t[%s]' %(IntArr2Str(model.RSeSegInfo.val, 4)))
	cnt, i = getUInt32(data, i)
	idx = 0
	logMessage('\tList 1')
	while (idx < cnt):
		txt, i = getLen32Text16(data, i)
		logMessage('\t\t%02X: %r' % (idx, txt))
		model.RSeSegInfo.uidList1.append(txt)
		idx += 1

	cnt, i = getUInt32(data, i)
	idx = 0
	logMessage('\tList 2')
	while (idx < cnt):
		txt, i = getLen32Text16(data, i)
		logMessage('\t\t%02X: %r' % (idx, txt))
		model.RSeSegInfo.uidList2.append(txt)
		idx += 1

	return	 i

def ReadRSeSegInfo1A(data, offset):
	global model

	model.RSeSegInfo = RSeSegInformation()
	cnt, i = getSInt32(data, offset)
	idx = 0
	while (idx < cnt):
		seg, i = ReadRSeSegment(data, i, idx, 8)

		i = ReadRSeSegmentType1A(data, i, seg)

		model.RSeSegInfo.segments[seg.name] = seg

		idx += 1

	model.RSeSegInfo.val, i = getUInt16A(data, i, 2)
	logMessage('\t[%s]' %(IntArr2Str(model.RSeSegInfo.val, 4)))
	cnt, i = getUInt32(data, i)
	idx = 0
	logMessage('\tList 1')
	while (idx < cnt):
		txt, i = getLen32Text16(data, i)
		logMessage('\t\t%02X: %r' % (idx, txt))
		model.RSeSegInfo.uidList1.append(txt)
		idx += 1

	cnt, i = getUInt32(data, i)
	idx = 0
	logMessage('\tList 2')
	while (idx < cnt):
		txt, i = getLen32Text16(data, i)
		logMessage('\t\t%02X: %r' % (idx, txt))
		model.RSeSegInfo.uidList2.append(txt)
		idx += 1

	return i

def ReadRSeSegInfo1D(data):
	global model

	model.RSeSegInfo = RSeSegInformation()
	cnt, i = getSInt32(data, 0)
	idx = 0
	while (idx < cnt):
		seg, i = ReadRSeSegment(data, i, idx, 8)

		i = ReadRSeSegmentType1D(data, i, seg)

		model.RSeSegInfo.segments[seg.name] = seg

		idx += 1

	model.RSeSegInfo.val, i = getUInt16A(data, i, 2)
	logMessage('\t[%s]' %(IntArr2Str(model.RSeSegInfo.val, 4)))
	cnt, i = getUInt32(data, i)
	idx = 0
	logMessage('\tList 1')
	while (idx < cnt):
		txt, i = getLen32Text16(data, i)
		logMessage('\t\t%02X: %r' % (idx, txt))
		model.RSeSegInfo.uidList1.append(txt)
		idx += 1

	cnt, i = getUInt32(data, i)
	idx = 0
	logMessage('\tList 2')
	while (idx < cnt):
		txt, i = getLen32Text16(data, i)
		logMessage('\t\t%02X: %r' % (idx, txt))
		model.RSeSegInfo.uidList2.append(txt)
		idx += 1

	return i

def ReadRSeSegInfo1F(data):
	global model

	model.RSeSegInfo = RSeSegInformation()
	cnt, i = getSInt32(data, 0)
	idx = 0
	while (idx < cnt):
		seg, i = ReadRSeSegment(data, i, idx, 10)

		i = ReadRSeSegmentType1F(data, i, seg)

		model.RSeSegInfo.segments[seg.name] = seg

		idx += 1

	model.RSeSegInfo.val, i = getUInt16A(data, i, 2)
	logMessage('\t[%s]' %(IntArr2Str(model.RSeSegInfo.val, 4)))

	cnt, i = getUInt32(data, i)
	idx = 0
	logMessage('\tList 1')
	while (idx < cnt):
		uid, i = getUUID(data, i,'RSeSegInfo.List1[%X].uid' % idx)
		txt = getUidText(uid)
		model.RSeSegInfo.uidList1.append(txt)
		logMessage('\t\t%02X: %r' % (idx, txt))
		idx += 1

	cnt, i = getUInt32(data, i)
	idx = 0
	logMessage('\tList 2')
	while (idx < cnt):
		uid, i = getUUID(data, i, 'RSeSegInfo.List2[%X].uid' % idx)
		txt = getUidText(uid)
		model.RSeSegInfo.uidList2.append(txt)
		logMessage('\t\t%02X: %r' % (idx, txt))
		idx += 1

	return i

def ReadRSeDb10(data, offset):
	global model

	i = offset
	model.RSeDb.arr3, i = getUInt16A(data, i, 8)
	model.RSeDb.arr2, i = getUInt16A(data, i, 4)
	model.RSeDb.dat2, i = getDateTime(data, i)
	model.RSeDb.uid2, i = getUUID(data, i, 'RSeDb[1].uid')
	model.RSeDb.arr4, i = getUInt32A(data, i, 2)
	model.RSeDb.txt, i = getLen32Text16(data, i)
	model.RSeDb.arr5, i = getUInt32A(data, i, 6)

	logMessage('\t%r: %s' %(model.RSeDb.txt, model.RSeDb.comment))
	logMessage('\t%s [%X]' %(model.RSeDb.uid, model.RSeDb.version))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr1, 4)))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr2, 4)))

	i = ReadRSeSegInfo10(data, i)

	return i

def ReadRSeDb15(data, offset):
	global model

	i = offset

	model.RSeDb.arr2, i = getUInt16A(data, i, 4)
	model.RSeDb.dat2, i = getDateTime(data, i)
	model.RSeDb.arr3, i = getUInt16A(data, i, 14)
	model.RSeDb.dat3, i = getDateTime(data, i)
	model.RSeDb.uid2, i = getUUID(data, i, 'RSeDb[1].uid')
	model.RSeDb.arr4, i = getUInt32A(data, i, 2)
	model.RSeDb.txt, i = getLen32Text16(data, i)
	model.RSeDb.arr5, i = getUInt32A(data, i, 6)

	logMessage('\t%r: %s' %(model.RSeDb.txt, model.RSeDb.comment))
	logMessage('\t%s [%X]' %(model.RSeDb.uid, model.RSeDb.version))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr1, 4)))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr2, 4)))
	logMessage('\t[%s]: %s' %(IntArr2Str(model.RSeDb.arr3, 4), model.RSeDb.uid2))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr4, 4)))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr5, 4)))

	i = ReadRSeSegInfo15(data, i)

	return i

def ReadRSeDb1A(data, offset):
	global model

	i = offset

	model.RSeDb.arr2, i = getUInt16A(data, i, 4)
	model.RSeDb.dat2, i = getDateTime(data, i)
	model.RSeDb.txt2, i  = getLen32Text16(data, i)
	model.RSeDb.arr3, i = getUInt16A(data, i, 12)
	model.RSeDb.dat3, i = getDateTime(data, i)
	model.RSeDb.uid2, i = getUUID(data, i, 'RSeDb[1].uid')
	model.RSeDb.u16, i  = getUInt16(data, i)
	model.RSeDb.arr4, i = getUInt32A(data, i, 2)
	model.RSeDb.txt, i = getLen32Text16(data, i)
	model.RSeDb.arr5, i = getUInt32A(data, i, 2)
	model.RSeDb.txt3, i = getLen32Text16(data, i)
	model.RSeDb.arr6, i = getUInt32A(data, i, 4)

	logMessage('\t%r: %s' %(model.RSeDb.txt, model.RSeDb.txt2))
	logMessage('\t%s [%X]' %(model.RSeDb.uid, model.RSeDb.version))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr1, 4)))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr2, 4)))
	logMessage('\t[%s]: %s' %(IntArr2Str(model.RSeDb.arr3, 4), model.RSeDb.uid2))
	logMessage('\t%d: [%s]' %(model.RSeDb.u16, IntArr2Str(model.RSeDb.arr4, 4)))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr5, 4)))
	logMessage('\t%r' %(model.RSeDb.txt3))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr6, 4)))

	i = ReadRSeSegInfo1A(data, i)

	return i

def ReadRSeDb1D(data, offset):
	global model

	i = offset

	model.RSeDb.arr2, i = getUInt16A(data, i, 4)
	model.RSeDb.dat2, i = getDateTime(data, i)
	model.RSeDb.txt, i = getLen32Text16(data, i)

	logMessage('\t%r: %s' %(model.RSeDb.txt, model.RSeDb.comment))
	logMessage('\t%s [%X]' %(model.RSeDb.uid, model.RSeDb.version))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr1, 4)))
	logMessage('\t[%s]' %(IntArr2Str(model.RSeDb.arr2, 4)))

	return i

def ReadRSeDb(data):
	global model

	model.RSeDb = RSeDatabase()
	i = 0
	model.RSeDb.uid, i = getUUID(data, i, 'RSeDb.uid')
	model.RSeDb.version, i = getUInt32(data, i)
	model.RSeDb.arr1, i = getUInt16A(data, i, 4)
	model.RSeDb.dat1, i = getDateTime(data, i)

	if (model.RSeDb.version == 0x10):
		i = ReadRSeDb10(data, i)
	elif (model.RSeDb.version == 0x15):
		i = ReadRSeDb15(data, i)
	elif (model.RSeDb.version == 0x1A):
		i = ReadRSeDb1A(data, i)
	elif (model.RSeDb.version == 0x1D):
		i = ReadRSeDb1D(data, i)
	elif (model.RSeDb.version == 0x1F):
		i = ReadRSeDb1D(data, i)
	else:
		logError('>>> ERROR - reading RSeDB version %X: unknown format!' %(model.RSeDb.version))

	return i

def ReadRSeDbRevisionInfo(data):
	global model

	i = 0
	version, i = getSInt32(data, i)
	model.RSeDbRevisionInfoMap = {}
	model.RSeDbRevisionInfoList = []
	cnt, i = getSInt32(data, i)
	logMessage('\tversion = %s' % (version))
	n = 0
	while (n < cnt):
		info = RSeDbRevisionInfo()
		info.ID, i = getUUID(data, i, 'RSeDbRevisionInfo.ID')
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
			b, i = getUInt8(data, i)
			if (b == 0):
				info.data, i = getUInt32A(data, i, 4)
			elif (b == 1):
				info.data, i = getUInt32A(data, i, 2)
			else:
				logError('>>>ERROR - Don\'t know how to handle DbRevisionInfo.type=%02X!' % b)
		else:
			info.data = []
		model.RSeDbRevisionInfoMap[info.ID] = info
		model.RSeDbRevisionInfoList.append(info)

		# logMessage('\t%4X: %s' % (n, info))
		n += 1
	return i

def getRevisionRef(revIdx):
	global model

	revRef = revIdx

	if ((model.RSeDbRevisionInfoList is not None) and (len(model.RSeDbRevisionInfoList) > revIdx)):
		revRef = model.RSeDbRevisionInfoList[revIdx]

	return revRef

def ReadRSeMetaDataSectionSizeArray(data, offset):
	size, i = getUInt32(data, offset)
	return i

def ReadRSeMetaDataBlocksSize(value, data, offset):
	cnt, i = getUInt32(data, offset)
	j = 0
	while (j < cnt):
		j += 1
		sec = RSeStorageBlockSize(value)
		u32, i = getUInt32(data, i)
		sec.length = (u32 & 0x7FFFFFFF)
		sec.flags = ((u32 & 0x80000000) > 0)

		value.sec1.append(sec)

	i = ReadRSeMetaDataSectionSizeArray(data, i)

	return i

def ReadRSeMetaDataSection2(value, data, offset):
	cnt, i = getUInt32(data, offset)
	j = 0
	while (j < cnt):
		j += 1
		sec = RSeStorageSection2(value)
		if (value.ver == 3):
			sec.revisionRef, i = getUUID(data, i, '%s.Sec2[%X].uidRef' % (value.name, j))
			sec.flag, i = getUInt32(data, i)
			sec.val, i = getUInt16(data, i)
			sec.arr, i = getUInt16A(data, i, 5)
		elif (value.ver == 4):
			idx, i = getUInt32(data, i)
			sec.revisionRef = getRevisionRef(idx)
			sec.flag, i = getUInt32(data, i)
			sec.val, i = getUInt16(data, i)
			sec.arr, i = getUInt16A(data, i, 5)
		else:
			idx, i = getUInt32(data, i)
			sec.revisionRef = getRevisionRef(idx)
			sec.flag, i = getUInt32(data, i)
			sec.val, i = getUInt16(data, i)
		value.sec2.append(sec)
	i = ReadRSeMetaDataSectionSizeArray(data, i)
	return i

def ReadRSeMetaDataSection3(value, data, offset):
	cnt, i = getUInt32(data, offset)
	j = 0
	while (j < cnt):
		j += 1
		sec = RSeStorageSection3(value)
		sec.uid, i = getUUID(data, i, '%s.Sec3[%X].uidRef' % (value.name, j))
		sec.arr, i = getUInt16A(data, i, 6)
		value.sec3.append(sec)
	i = ReadRSeMetaDataSectionSizeArray(data, i)
	return i

def ReadRSeMetaDataSection4Data(data, offset):
	val = RSeStorageSection4Data()
	val.num, i = getUInt16(data, offset)
	val.val, i = getUInt32(data, i)
	return val, i

def ReadRSeMetaDataBlocksType(value, data, offset):
	cnt, i = getUInt32(data, offset)
	j = 0
	while (j < cnt):
		sec = RSeStorageBlockType(value)
		uid, i = getUUID(data, i, '%s.Sec4[%X].uidRef' % (value.name, j))
		sec.typeID = uid
		val, i = ReadRSeMetaDataSection4Data(data, i)
		sec.arr.append(val)
		val, i = ReadRSeMetaDataSection4Data(data, i)
		sec.arr.append(val)
		value.sec4[j] = sec
		j += 1
	i = ReadRSeMetaDataSectionSizeArray(data, i)

	return i

def ReadRSeMetaDataSection5(value, data, offset, size):
	#index section 4
	sec = RSeStorageSection5(value)
	sec.indexSec4, i = getUInt16A(data, offset, size / 2)
	i = ReadRSeMetaDataSectionSizeArray(data, i)
	return i

def ReadRSeMetaDataSection6(value, data, offset, size, cnt):
	sec = RSeStorageSection6(value)

	i = offset
	# ???
	# arr32, i = getUInt32A(data, i, 2)
	# n16, i = getUInt16(data, i)
	# arrU = []
	# while (n16>0)
	# 	uid, i = getUUID(data, i, '%s.Sec6[%X].uidRef' % (value.name, n))
	# 	arr2, i = getUInt16A(data, i, 2)
	#   arrU.append(sec7(uid, arr2))
	#   n16 -= 1
	# n16, i = getUInt16(data, i)
	# arrV = []
	# while (n16>0)
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
	#uid, dummy = getUUID(data, j + 0x02, '%s.Sec6[%X].uidRef' % (value.name, len(sec.arr1)))
	#u32, dummy = getUInt32(data, j + 0x12)
	#sec.arr1.append(RSeStorageSection4Data1(uid, u32))
	#while (n16 != len(sec.arr1)):
	#	j -= 0x14
	#	n16, dummy = getUInt16(data, j)
	#	uid, dummy = getUUID(data, j + 0x02, '%s.Sec6[%X].uidRef' % (value.name, len(sec.arr1)))
	#	u32, dummy = getUInt32(data, j + 0x12)
	#	sec.arr1.insert(0, RSeStorageSection4Data1(uid, u32))
	#
	#setDumpLineLength(0x20)

	i = ReadRSeMetaDataSectionSizeArray(data, i)
	return i

def ReadRSeMetaDataSection7(value, data, offset, size, cnt):
	i = offset
	j = 0
	while (j<cnt):
		j += 1
		sec = RSeStorageSection7(value)
		if (size/cnt >= 0x4C):
			sec.segRef, i = getUUID(data, i, '%s.Sec7[%X].segRef' % (value.name, j))
			sec.revisionRef, i    = getUUID(data, i, '%s.Sec7[%X].revisionRef' % (value.name, j))
			sec.dbRef, i  = getUUID(data, i, '%s.Sec7[%X].dbRef' % (value.name, j))
			sec.txt1, i   = getLen32Text16(data, i)
			sec.arr1, i   = getUInt16A(data, i, 4)
			sec.txt2, i   = getLen32Text16(data, i)
			sec.arr2, i   = getUInt16A(data, i, 2)
			sec.txt3, i   = getLen32Text16(data, i)
			sec.arr3, i   = getUInt16A(data, i, 2)
		else:
			sec.segRef, i = getUUID(data, i, '%s.Sec7[%X].segRef' % (value.name, j))
			sec.revisionRef, i    = getUUID(data, i, '%s.Sec7[%X].revisionRef' % (value.name, j))
		seg = findSegment(sec.segRef)
		if (seg is not None):
			sec.segName = seg.name

		value.sec7.append(sec)
	i = ReadRSeMetaDataSectionSizeArray(data, i)
	return i

def ReadRSeMetaDataSection8(value, data, offset, size, cnt):
	i = offset
	j = 0
	while (j < cnt):
		j += 1
		sec = RSeStorageSection8(value)
		sec.dbRevisionInfoRef, i = getUUID(data, i, '%s.Sec8[%X].dbRevisionInfoRef' % (value.name, j))
		sec.arr, i = getUInt16A(data, i, 2)
		value.sec8.append(sec)
	i = ReadRSeMetaDataSectionSizeArray(data, i)
	return i

def ReadRSeMetaDataSection9(value, data, offset, size, cnt):
	i = offset
	j = 0
	while (j<cnt):
		j += 1
		sec = RSeStorageSection9(value)
		sec.uid, i = getUUID(data, i, '%s.Sec9[%X].uidRef' % (value.name, j))
		sec.arr, i = getUInt8A(data, i, 3)
		value.sec9.append(sec)
	i = ReadRSeMetaDataSectionSizeArray(data, i)
	return i

def ReadRSeMetaDataSectionA(value, data, offset, size, cnt):
	'''
	Same values as in RSeSegmentType
	'''
	i = offset
	j = 0
	while (j<cnt):
		j += 1
		sec = RSeStorageSectionA(value)
		sec.arr, i = getUInt16A(data, i, 4)
		value.secA.append(sec)
	i = ReadRSeMetaDataSectionSizeArray(data, i)
	return i

def ReadRSeMetaDataSectionB(value, data, offset, size, cnt):
	i = offset
	j = 0
	while (j<cnt):
		j += 1
		sec = RSeStorageSectionB(value)
		sec.arr, i = getUInt16A(data, i, 2)
		value.secB.append(sec)
	return i

def findSegment(segRef):
	global model

	return model.RSeSegInfo.segments.get(segRef)

def getReader(seg):
	reader = None
	seg.AcisList = []
	if (RSeMetaData.isApp(seg)): # ApplicationSettings
		# reader = AppReader()
		pass
	elif (RSeMetaData.isBRep(seg)): # BoundaryRepresentation
		if (isStrategySat()):
			reader = BRepReader()
		pass
	elif (RSeMetaData.isBrowser(seg)):
		# reader = BrowserReader()
		pass
	elif (RSeMetaData.isDefault(seg)):
		# reader = DefaultReader()
		pass
	elif (RSeMetaData.isDC(seg)):
		if (isStrategyNative()):
			reader = DCReader()
	elif (RSeMetaData.isGraphics(seg)):
		# reader = GraphicsReader()
		pass
	elif (RSeMetaData.isResult(seg)):
		# reader = ResultReader()
		pass
	elif (RSeMetaData.isDesignView(seg)):
		# reader = DesignViewReader()
		pass
	elif (RSeMetaData.isEeData(seg)):
		# reader = EeDataReader()
		pass
	elif (RSeMetaData.isEeScene(seg)):
		# reader = EeSceneReader()
		pass
	elif (RSeMetaData.isFBAttribute(seg)):
		# reader = FBAttributeReader()
		pass
	elif (RSeMetaData.isNBNotebook(seg)):
		# reader = NotebookReader()
		pass
	elif (seg.segRef is not None):
		logWarning('>W: %s will be read, but not considered!' %(seg.name))
	return reader

def ReadRSeMetaDataB(dataB, seg):
	reader = getReader(seg)
	if (reader):
		folder = getInventorFile()[0:-4]

		filename = '%s\\%sB.log' %(folder, seg.name)
		newFile = codecs.open(filename, 'wb', 'utf8')

		newFile.write('[%s]\n' %(getFileVersion()))
		i = 0
		uid, i = getUUID(dataB, i, '%sB.uid' %(seg.name))
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
	if (value.arr1[0] + value.arr1[1] + value.arr1[2] + value.arr1[3] + value.arr1[4] > 0):
		value.name, i = getLen32Text16(dataM, i)
		value.segRef, i = getUUID(dataM, i, '%s.segRef' %(value.name))
		value.arr2, i = getUInt32A(dataM, i, 0x3)
		seg = findSegment(value.segRef)
		if (seg is not None):
			seg.metaData = value
	else:
		value.name = name
		value.segRef = None
		value.arr2 = []
		return value

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
	bak = getDumpLineLength()
	setDumpLineLength(0x30)

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
				setDumpLineLength(l / c)
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

	value.uid2, i = getUUID(data, len(data)-0x10, '%s.uid2' % (value.name))
	#if (value.uid2.bytes != uuid.UUID('9744e6a4-11d1-8dd8-0008-2998bedddc09').bytes:
	# logError('>>>ERROR - STREAM CORRUPTED')
	setDumpLineLength(bak)
	model.RSeStorageData[value.name] = value
	logMessage('\t>>> SEE %s\\%sM.txt <<<' % (folder, value.name), LOG.LOG_DEBUG)
	return value

def ReadRSeEmbeddingsDatabaseInterfaces(data):
	global model

	model.DatabaseInterfaces = {}
	i = 0
	uid1, i = getUUID(data, i, 'RSeEmbeddings.DatabaseInterfaces.uid1')
	cnt, i  = getUInt16(data, i)
	uid2, i = getUUID(data, i, 'RSeEmbeddings.DatabaseInterfaces.uid2')
	logMessage('\t%s %4X %s' % (uid1, cnt, uid2))
	n = 0
	while i < len(data):
		name, i = getLen32Text8(data, i)
		dbInterface = DbInterface(name)
		dbInterface.type, i = getSInt32(data, i)
		dbInterface.data = data[i:i+dbInterface.type]
		i += dbInterface.type
		dbInterface.uid, i = getUUID(data, i, 'RSeEmbeddings.DatabaseInterfaces[%X].uid' % (n))
		if (dbInterface.type  == 0x01):
			dbInterface.value = 'YES' if (struct.unpack('<?', dbInterface.data)[0]) else 'NO'
		elif (dbInterface.type== 0x04):
			dbInterface.value = struct.unpack('<i', dbInterface.data)[0]
		elif (dbInterface.type== 0x10):
			dbInterface.value = getUUID(dbInterface.data, 0, 'RSeEmbeddings.DatabaseInterfaces.Item.uidRef')
#		elif (dbInterface.type== 0x30):
#			dbInterface.value = getFloat64A(dbInterface.data, 0, 6)
		else:
			dbInterface.value = '[%s]' % (', '.join(['%02X' % ord(h) for h in dbInterface.data]))

		model.DatabaseInterfaces[dbInterface.name] = dbInterface
		n += 1

	# To return a new list, use the sorted() built-in function...
	for dbi in (sorted(model.DatabaseInterfaces.values(), key=operator.attrgetter('name'))):
		logMessage('\t%s' % (dbi))

	return i

def ReadRSeEmbeddingsCompObj(data):
	i = 0
	reserved1, i    = getUInt32(data, i)
	version, i      = getUInt32(data, i)
	val4, i         = getSInt32(data, i)
	clsId, i        = getUUID(data, i, 'CompObj.CLSID')
	ansiName, i     = getLen32Text8(data, i)
	ansiFmt, i      = getLen32Text8(data, i)
	ansiKey, i      = getLen32Text8(data, i)
	marker, i       = getUInt32(data, i)
	unicodeName, i  = getLen32Text8(data, i)
	unicodeFmt, i   = getLen32Text8(data, i)
	unicodeKey, i   = getLen32Text8(data, i)
	logMessage('\t%s:' %(clsId))
	logMessage('\t\t%s: %s=\'%s\'' %(ansiFmt, ansiKey, ansiName))
	logMessage('\t\t%s: %s=\'%s\'' %(unicodeFmt, unicodeKey, unicodeName))

	return i

def ReadRSeEmbeddingsContentsText16(data, offset):
	len, i = getUInt8A(data, offset, 4)
	end = i + len[3]*2
	buf = data[i: end]
	txt = buf.decode('UTF-16LE').encode(ENCODING_FS)
	return txt, end

def ReadRSeEmbeddingsContents(data):
	p = re.compile('\xFF\xFE\xFF.')

	arr1, i = getUInt32A(data, 0, 4)
	logMessage('\t[%s]' %IntArr2Str(arr1, 4))
	m = p.search(data, i)
	while (m):
		iOld = i
		i = m.start()
		logMessage(HexAsciiDump(data[iOld:i], 0), LOG.LOG_ALWAYS)
		txt, i = ReadRSeEmbeddingsContentsText16(data, i)
		logMessage('\t%r' %(txt))
		m = p.search(data, i)

	logMessage(HexAsciiDump(data[i:len(data)], i), LOG.LOG_ALWAYS)

def dumpRemaining(data, offset):
	i = offset

	p1 = re.compile('\x00\x00[^\x00]\x00[^\x00]\x00[^\x00]\x00[^\x00]\x00')
	p2 = re.compile('\x00\x00\x00[ 0-z][ 0-z][ 0-z][ 0-z]')

	m1 = p1.search(data, i)
	m2 = p2.search(data, i)
	while (m1 or m2):
		iOld = i
		if (m1):
			i1 = m1.start() - 2
		else:
			i1 = len(data)
		if (m2):
			i2 = m2.start() - 1
		else:
			i2 = len(data)

		if (i1 <= i2):
			logMessage(HexAsciiDump(data[iOld:i1], iOld, False), LOG.LOG_DEBUG)
			txt, i = getLen32Text16(data, i1)
			m1 = p1.search(data, i)
		else:
			logMessage(HexAsciiDump(data[iOld:i2], iOld, False), LOG.LOG_DEBUG)
			txt, i = getLen32Text8(data, i2)
			m2 = p2.search(data, i)

		logMessage('\t%r' %(txt))

	logMessage(HexAsciiDump(data[i:len(data)], i, False), LOG.LOG_DEBUG)
