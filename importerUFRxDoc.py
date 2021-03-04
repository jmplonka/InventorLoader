# -*- coding: utf-8 -*-
'''
importerUFRxDoc.py:
UFRxDoc files were introduced with Inventor v11 in 2006!
'''

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

import traceback, io, re
from importerUtils   import *
from importerClasses import VersionInfo
from FreeCAD import BoundBox

_magic  = []
__fv__ = None

def getFileVersion():
	global __fv__
	return __fv__

def getUFRxVersion(sectionIndex):
	global _magic
	#   11: 0x08 [1D 10 06 10 00 02 02 02 01 03 01 02 06 02 02 01 00 01 02}
	# 2008: 0x08 [1E 11 08 10 00 02 03 02 01 03 01 02 06 02 02 03 00 01 02]
	# 2009: 0x09 [1E 12 09 12 00 02 03 02 01 03 01 02 06 02 02 03 00 01 02 00]
	# 2010: 0x0A [1F 12 0B 12 01 02 03 02 01 03 01 02 06 02 02 05 00 01 02 00 00]
	# 2011: 0x0A [1F 12 0B 12 01 02 03 02 01 03 01 02 06 02 02 05 00 01 02 00 00]
	# 2012: 0x0B [1F 13 0C 12 01 02 04 02 01 03 01 02 06 02 02 05 00 01 02 00 00 00 00]
	# 2013: 0x0B [1F 13 0C 12 01 02 04 02 01 03 01 02 06 02 02 05 00 01 02 00 00 00 00]
	# 2014: 0x0B [1F 13 0C 12 01 02 04 02 01 05 01 02 06 02 02 05 00 01 02 00 00 00 00]
	# 2015: 0x0C [1F 14 0D 14 02 03 05 03 01 05 01 02 07 02 03 06 00 02 03 00 01 00 01 00]
	# 2016: 0x0C [1F 14 0D 14 02 03 05 03 01 05 01 02 07 02 03 07 00 02 03 00 01 00 01 00]
	# 2017: 0x0C [1F 14 0D 15 02 03 05 03 01 05 01 02 07 02 03 07 00 02 03 00 01 00 01 00]
	# 2018: 0x0C [1F 15 0D 15 02 03 05 03 01 05 01 02 07 02 03 07 00 02 03 00 01 00 01 00]
	# 2019: 0x0C [1F 15 0D 15 02 03 05 03 01 05 01 02 07 02 03 07 00 02 03 00 01 00 01 00]
	# 2020: 0x0C [1F 15 0D 15 02 03 05 03 01 05 01 02 07 02 03 07 00 02 03 00 01 00 01 00]
	# 2021: 0x0C [1F 15 0D 15 02 03 05 03 01 05 01 02 07 02 03 07 00 02 03 00 01 00 01 00]
	#                   |  |  |              |                 |        |     |
	# 2: HEADER_2 ------+  |  |              |                 |        |     |
	# 3: OCCURENCES--------+  |              |                 |        |     |
	# 4: INVENTOR_FILES-------+              |                 |        |     |
	# 9: PROPERTIES--------------------------+                 |        |     |
	# 15: OLE_FILES--------------------------------------------+        |     |
	# 18: I_PROPERTIES--------------------------------------------------+     |
	# 20: APPENDIX------------------------------------------------------------+
	if (sectionIndex < len(_magic)): return _magic[sectionIndex]
	return -1

class UFRxObject(object):
	def __repr__(self): return self.__str__()

class UFRxExport(UFRxObject):
	def __init__(self):
		self.type_name  = ''
		self.name       = ''
		self.guid       = None
		self.flags      = 0
		self.unknown    = 0
		self.properties = []
		self.settings   = []

class UFRxDocument(UFRxObject):
	def __init__(self):
		self.header1       = None
		self.lodToc        = None
		self.header2       = None
		self.lod_list      = None
		self.inventorFiles = None
		self.partFiles     = None
		self.occurences    = None
		self.properties    = None
		self.abschnitt1    = None
		self.abschnitt2    = None
		self.unknown2      = None
		self.bomRecord     = None
		self.unknown3      = None
		self.exportBlocks  = None
		self.rangeBox      = None
		self.iProperties   = None
		self.appendix      = None

class UFRxHeader1(UFRxObject):
	def __init__(self):
		self.schema     = 0
		self.magic      = []
		self.vrs_inf_1  = None
		self.dat1       = None
		self.vrs_inf_2  = None # Version ????
		self.dat2       = None
		self.comment    = ''
		self.vrs_inf_3  = None # Version ????
		self.dat3       = None
		self.vrs_inf_4  = None # Version the file was created
		self.dat4       = None
		self.revision   = None
		self.padding    = 0
		self.name_ntrnl = None # InternalName
		self.fName      = ''   # original file name
		self.iPartFlags = 0

class UFRxLodToc(UFRxObject):
	def __init__(self):
		self.n1 = 0
		self.n2 = 0
		self.t  = ''
		self.n3 = 0
		self.n4 = 0
	def __str__(self): return "%03X,%03X,'%s',%02X,%02X" %(self.n1, self.n2, self.t, self.n3, self.n4)

class UFRxHeader2(UFRxObject):
	def __init__(self):
		self.pairs = []
		self.lastActiveLOD_1   = (0, 0)
		self.activeDesignView  = ''
		self.lastActiveLOD_2   = (0, 0)
		self.version_Flag      = 0
		self.maxOccRc          = 0
		self.next_LOD_to_apply = 0
		self.always_1          = 0
		self.max_inv_file_ref  = 0
		self.max_ole_file_ref  = 0
		self.doc_Sub_Typ_1     = None
		self.doc_Sub_Typ_2     = None

class UFRxInvFiles(UFRxObject):
	def __init__(self):
		self.caption = ''
		self.padding = 0
		self.fils    = []

class UFRxInvFile(UFRxObject):
	def __init__(self):
		self.path       = ''
		self.lib_id     = 0
		self.lib_name   = ''
		self.i_1        = 0
		self.t_1        = ''
		self.buf        = ()
		self.name       = None
		self.db         = None
		self.id         = 0
		self.occurences = 0
		self.version    = 0
		self.flags      = 0
	def __str__(self): return "'%s', %d, '%s', %d, '%s', [%s], {%s}, {%s}, %d, %d, %04X, %04X\n" %(self.path, self.lib_id, self.lib_name, self.i_1, self.t_1, IntArr2Str(self.buf, 2), self.name, self.db, self.id, self.occurences, self.version, self.flags)

class UFRxOleFile(UFRxObject):
	def __init__(self):
		self.n1 = 0
		self.d1 = None
		self.n2 = 0
		self.n3 = 0
		self.t1 = ''
		self.n4 = 0
		self.t2 = ''
		self.n5 = 0
		self.t3 = ''
		self.a1 = (0, 0, 0, 0)
	def __str__(self): return "%04x, %s, %04x, %04x, '%s', %d, '%s', %03X, '%s', [%s]\n" %(self.n1, self.d1, self.n2, self.n3, self.t1, self.n4, self.t2, self.n3, self.t3, IntArr2Str(self.a1, 3))

class UFRxOccSecProperty(UFRxObject):
	TYP_STRING  = (0x05, 0x1E)
	TYP_UINT_8  = (0x07, 0x0D, 0x0F, 0x10, 0x1D)
	TYP_UINT_32 = (0x19, )
	TYP_UID     = (0x02, 0x03, 0x11, 0x12, 0x13, 0x15, 0x16, 0x17, 0x18, 0x1C, 0x1F, 0x20, 0x22, 0x23, 0x24, 0x25, 0x2A, 0x2B)
	def __init__(self):
		super(UFRxOccSecProperty, self).__init__()
		self.b  = False
		self.t  = 0
		self.n1 = 0
		self.v  = None
		self.n2 = 0
	def readValues(self, data, offset):
		self.b, i  = getBoolean(data, offset)
		self.t, i  = getUInt8(data, i)
		self.n1, i = getUInt32(data, i)
		t, i    = getUInt8(data, i)
		assert t == self.t, "UFRxOccSecProperty.readValues(): expected %02X, but found %02X!"%(self.t, t)
		if (t in UFRxOccSecProperty.TYP_STRING):
			self.v, i = getLen32Text16(data, i)
		elif (t in UFRxOccSecProperty.TYP_UINT_8):
			self.v, i = getUInt8(data, i)
		elif (t in UFRxOccSecProperty.TYP_UINT_32):
			self.v, i = getUInt32(data, i)
		elif (t in UFRxOccSecProperty.TYP_UID):
			self.v, i  = getUUID(data, i)
		else:
			raise ValueError(u"Unknown type %02X for array element in Occurence Section 1!" %(t))
		self.n2, i = getUInt32(data, i)
		return i
	def getValueAsStr(self):
		if (self.t in UFRxOccSecProperty.TYP_STRING):
			return "'%s'" %(self.v)
		if (self.t in UFRxOccSecProperty.TYP_UINT_8):
			return "%d" %(self.v)
		if (self.t in UFRxOccSecProperty.TYP_UINT_32):
			return "%04X" %(self.v)
		if (self.t in UFRxOccSecProperty.TYP_UID):
			return "{%s}" %(self.v)
		return "%s" %(self.v)
	def __str__(self):  return u"%02X, %5s, %04X, %s, %04X" %(self.t, self.b, self.n1, self.getValueAsStr(), self.n2)

class UFRxOccSection(UFRxObject):
	def __init__(self):
		self.n = 0
		self.properties = {}

class UFRxOccSecItem(UFRxObject):
	TYP_UID = (0x12, 0x16, 0x17, 0x18, 0x23, 0x24, 0x25, 0x2A)
	TYP_UINT_8  = (0x07,)
	TYP_UINT_32 = (0x19,)
	def __init__(self):
		self.b = False
		self.t = 0
		self.p = 0
		self.l = []
	def readValues(self, data, offset):
		self.b, i = getBoolean(data, offset)
		self.t, i = getUInt8(data, i)
		cnt, i = getUInt32(data, i)
		for j in range(cnt):
			t, i = getUInt8(data, i)
			assert t == self.t
			if (t in UFRxOccSecItem.TYP_UID):
				v, i = getUUID(data, i)
			elif (t in UFRxOccSecItem.TYP_UINT_8):
				v, i = getUInt8(data, i)
			elif (t in UFRxOccSecItem.TYP_UINT_32):
				v, i = getUInt32(data, i)
			else:
				raise ValueError(u"Unknown type %02X for array element in readOccSetItem!" %(t))
			self.l.append(v)
		self.p, i = getUInt32(data, i)
		return i
	def __val_2_str__(self, v):
		if (self.t in UFRxOccSecItem.TYP_UID): return "{%s}" %(v)
		elif (self.t in UFRxOccSecItem.TYP_UINT_8): return "%d" %(v)
		elif (self.t in UFRxOccSecItem.TYP_UINT_32): return "%04X" %(v)
		return "%s" %(v)
	def __str__(self):
	    return "%s, %02X, %d, (%s)" %(self.b, self.t, self.p, ",".join([self.__val_2_str__(v) for v in self.l]))

class UFRxOccSetting(UFRxObject):
	def __init__(self):
		self.num = 0
		self.values = []

class UFRxOccSettingValue(UFRxObject):
	def __init__(self):
		self.t1 = ''
		self.id = None
		self.t2 = ''
	def __str__(self): return "'%s', {%s}, '%s'" %(self.t1, self.id, self.t2)

class UFRxOccExport(UFRxObject):
	def __init__(self):
		self.buf  = ()
		self.val = None

class UFRxIProperty(UFRxObject):
	def __init__(self):
		self.b  = False
		self.t1 = ''
		self.t2 = ''
		self.n1 = 0
		self.id = None
		self.p  = (0, 0)
	def __str__(self): return "%s, '%s', '%s', %04X, {%s}, [%s]" %(self.b, self.t1, self.t2, self.n1, self.id, IntArr2Str(self.p, 2))

class UFRxIProperties(UFRxObject):
	def __init__(self):
		self.selected   = ''
		self.properties = []
		self.b = False

class UFRxOccurence(UFRxObject):
	def __init__(self):
		self.a1   = (0, 0, 0, 0) # (EndStringFlag, Ref2IDFromSection5, OccurrenceID, Unknown_1)
		self.size = 0
		self.a2   = ''
		self.a3   = (0, 0, 0, 0, 0)
		self.sec1 = None
		self.sec2 = None
		self.set  = None
		self.exp  = None
	def __str__(self): return "[%s], %s, '%s', [%s]" %(IntArr2Str(self.a1, 4), self.size, self.a2, IntArr2Str(self.a3, 2))

class UFRxAppendix(UFRxObject):
	def __init__(self):
		self.p1 = ()
		self.p2 = 0

class UFRxBOM(UFRxObject):
	def __init__(self):
		self.unit  = ''
		self.name  = ''
		self.repr  = ''
		self.value = 0.0
		self.pad   = 0
	def __str__(self): return "BOM: %s = %s (%04X)" %(self.name, self.repr, self.pad)

def readBoolean(data, offset, log, txt):
	v, i = getBoolean(data, offset)
	log.write("\t%s:\t%s\n" %(txt, v))
	return v, i

def readDateTime(data, offset, log, txt):
	v, i = getDateTime(data, offset)
	log.write("\t%s:\t%s\n" %(txt, v))
	return v, i

def readVersionInfo(data, offset, log, txt):
	v = VersionInfo() # [00 00 18 40 00 00 A0 41]
	v.revision, i = getUInt8(data, offset)
	v.minor,    i = getUInt8(data, i)
	v.major,    i = getUInt8(data, i)
	v.data,     i = getUInt8A(data, i, 5)
	log.write("\t%s:\t%s\n" %(txt, v))
	return v, i

def readFloat32_3D(data, offset, log, txt):
	v, i = getFloat32_3D(data, offset)
	log.write("\t%s:\t(%s)\n" %(txt, FloatArr2Str(v)))
	return v, i

def readFloat64(data, offset, log, txt):
	v, i = getFloat64(data, offset)
	log.write("\t%s:\t%s\n" %(txt, v))
	return v, i

def readUInt8(data, offset, log, txt):
	v, i = getUInt8(data, offset)
	log.write("\t%s:\t%02X\n" %(txt, v))
	return v, i

def readUInt8A(data, offset, log, txt, cnt):
	v, i = getUInt8A(data, offset, cnt)
	log.write("\t%s:\t[%s]\n" %(txt, IntArr2Str(v, 2)))
	return v, i

def readUInt16(data, offset, log, txt):
	v, i = getUInt16(data, offset)
	log.write("\t%s:\t%03X\n" %(txt, v))
	return v, i

def readUInt16A(data, offset, log, txt, cnt):
	v, i = getUInt16A(data, offset, cnt)
	log.write("\t%s:\t[%s]\n" %(txt, IntArr2Str(v, 3)))
	return v, i

def readUInt32(data, offset, log, txt):
	v, i = getUInt32(data, offset)
	log.write("\t%s:\t%04X\n" %(txt, v))
	return v, i

def readUInt32A(data, offset, log, txt, cnt):
	v, i = getUInt32A(data, offset, cnt)
	log.write("\t%s:\t[%s]\n" %(txt, IntArr2Str(v, 4)))
	return v, i

def readUID(data, offset, log, txt):
	v, i = getUUID(data, offset)
	log.write("\t%s:\t{%s}\n" %(txt, v))
	return v, i

def readText16(data, offset, log, txt):
	v, i = getLen32Text16(data, offset)
	log.write("\t%s:\t'%s'\n" %(txt, v))
	return v, i

def readHeader1(data, offset, log):
	global _magic, __fv__
	header = UFRxHeader1()
	log.write("HEADER_1\n")
	header.schema,     i = readUInt16(data,       offset, log, 'schema')
	cnt,               i = getUInt16(data,        i)
	header.magic,      i = readUInt16A(data,      i, log, 'magic', cnt)
	header.vrs_inf_1,  i = readVersionInfo(data,  i, log, 'VersionInfo_1_1') # Version the file was saved
	header.dat1,       i = readDateTime(data,     i, log, 'FileTime_1_1')
	header.vrs_inf_2,  i = readVersionInfo(data,  i, log, 'VersionInfo_1_2') # Version ????
	header.dat2,       i = readDateTime(data,     i, log, 'FileTime_1_1')
	header.comment,    i = readText16(data,       i, log, 'Comment')
	header.vrs_inf_3,  i = readVersionInfo(data,  i, log, 'VersionInfo_2_1') # Version ????
	header.dat3,       i = readDateTime(data,     i, log, 'FileTime_2_1')
	header.vrs_inf_4,  i = readVersionInfo(data,  i, log, 'VersionInfo_2_2') # Version the file was created
	header.dat4,       i = readDateTime(data,     i, log, 'FileTime_2_2')
	header.revision,   i = readUID(data,          i, log, 'DataBaseRevisionID')
	header.padding,    i = readUInt32(data,       i, log, 'Padding')         # schema >=0x09, < 0x09: UInt16!
	header.name_ntrnl, i = readUID(data,          i, log, 'InternalName')
	header.fName,      i = readText16(data,       i, log, 'OriginalFileName')
	header.iPartFlags, i = readUInt16(data,       i, log, 'iPartFlag')
	_magic = header.magic
	__fv__ = header.vrs_inf_1.major
	if (__fv__ > 11): __fv__ += 1996
	log.write("\n")
	return header, i

def readLodToc(data, offset, log):
	secVrs = getUFRxVersion(1)
	log.write("LOD-TOCs\n")
	lod_toc = []
	cnt, i = readUInt32(data, offset, log, 'count')
	for j in range(cnt):
		lodToc = UFRxLodToc()
		lodToc.n1, i = getUInt16(data, i)
		lodToc.n2, i = getUInt16(data, i)
		lodToc.t, i  = getLen32Text16(data, i)
		lodToc.n3, i = getUInt8(data, i)
		lodToc.n4, i = getUInt8(data, i)
		lod_toc.append(lodToc)
		log.write(u"\t\tLOD-TOC[%02X]: %s\n" %(j, lodToc))
	log.write("\n")
	return lod_toc, i

def readHeader2(data, offset, log):
	header = UFRxHeader2()
	log.write("HEADER_2\n")
	secVrs = getUFRxVersion(2)

	cnt, i = readUInt32(data, offset, log, 'string_pairs')
	for j in range(cnt):
		k, i = getLen32Text16(data, i)
		v, i = getLen32Text16(data, i)
		header.pairs.append((k, v))
		log.write(u"\t\t'%s'='%s'\n" %(k, v))
	header.lastActiveLOD_1,   i = readUInt16A(data, i, log, 'LastActiveLOD_1', 2)
	if (secVrs >= 0x0C): header.activeDesignView, i = readText16(data, i, log, 'ActiveDesignView')
	if (secVrs >= 0x07): header.lastActiveLOD_2,   i = readUInt16A(data, i, log, 'LastActiveLOD_2', 2)
	header.version_Flag,      i = readUInt16(data, i, log, 'VersionFlag')
	header.maxOccRc,          i = readUInt32(data, i, log, 'HighestOccRecID')
	header.next_LOD_to_apply, i = readUInt16(data, i, log, 'NextLODID2apply')
	header.always_1,          i = readUInt16(data, i, log, 'Always_1')
	if (header.always_1 != 1): logError("    NOT 1")
	header.max_inv_file_ref,  i = readUInt32(data, i, log, 'HighestInvFileRefID')
	header.max_ole_file_ref,  i = readUInt32(data, i, log, 'NextOtherFileRefID')
	if (secVrs >= 0x0D):
		header.doc_Sub_Typ_1, i = getUUID(data,    i)
		header.doc_Sub_Typ_2, i = getUUID(data,    i)
	else:
		header.doc_Sub_Typ_1 = UID('4d29b490-11d0-49b2-077e-c39300000006') # IPT, IAM={E60F81E1-11D0-49B3-077E-C39300000006}, IPN={?}, IDW={?}
		header.doc_Sub_Typ_2 = UID('4d29b490-11d0-49b2-077e-c39300000006') # IPT, IAM={E60F81E1-11D0-49B3-077E-C39300000006}, IPN={?}, IDW={?}
	log.write(u"\tDocumentSubTypeID_1:\t{%s}\n" %(header.doc_Sub_Typ_1))
	log.write(u"\tDocumentSubTypeID_2:\t{%s}\n" %(header.doc_Sub_Typ_2))
	log.write("\n")
	return header, i

def readLODs(data, offset, log):
	log.write("LOD\n")
	lods = []
	cnt, i = readUInt32(data, offset, log, 'count')
	#for j in range(cnt):
	if (cnt>0): logError("    Don't know how to read LOD's")
	log.write("\n")
	return lods, i

def readInvFile(data, offset, log):
	inv = UFRxInvFile()
	inv.path,       i = getLen32Text16(data, offset)
	inv.lib_id,     i = getUInt32(data,      i)
	inv.lib_name,   i = getLen32Text16(data, i)
	inv.i_1,        i = getUInt16(data,      i)
	inv.t_1,        i = getLen32Text16(data, i)
	inv.buf,        i = getUInt16A(data,     i, 4)
	inv.name,       i = getUUID(data,        i)
	inv.db,         i = getUUID(data,        i)
	inv.id,         i = getUInt32(data,      i)
	inv.occurences, i = getUInt32(data,      i)
	inv.version,    i = getUInt32(data,      i)
	inv.flags,      i = getUInt32(data,      i)
	return inv, i

def readInvFiles(data, offset, log):
	invFiles = UFRxInvFiles()
	log.write("INVENTOR-FILES\n")
	secVrs = getUFRxVersion(4)

	cnt, i = readUInt32(data, offset, log, 'count')
	invFiles.caption, i = readText16(data, i, log, 'Caption')
	invFiles.padding, i = readUInt32(data, i, log, 'Padding')
	for j in range(cnt):
		invFile, i = readInvFile(data, i, log)
		invFiles.fils.append(invFile)
		log.write(u"\t\tINV-FILE[%02X]: %s\n" %(j, invFile))
	if (secVrs >= 0x02): i += 1 # skip 00
	log.write("\n")
	return invFiles, i

def readOleFile(data, offset, log):
	ole = UFRxOleFile()
	secVrs = getUFRxVersion(15)

	ole.n1, i = getUInt32(data, offset)
	ole.d1, i = getDateTime(data, i)
	ole.n2, i = getUInt32(data, i)
	if (secVrs >= 0x07): i += 4 # skip 00 00 00 00
	ole.n3, i = getUInt32(data, i)
	ole.t1, i = getLen32Text16(data, i)
	ole.n4, i = getSInt32(data, i)
	ole.t2, i = getLen32Text16(data, i)
	ole.n5, i = getUInt16(data, i)
	ole.t3, i = getLen32Text16(data, i)
	ole.a1, i = getUInt16A(data, i, 4)

	return ole, i

def readOleFiles(data, offset, log):
	oleFiles = []
	secVrs = getUFRxVersion(15)
	log.write("OLE-FILES\n")

	cnt, i = readUInt32(data, offset, log, 'count')
	for j in range(cnt):
		ole, i = readOleFile(data, i, log)
		oleFiles.append(ole)
		log.write(u"\t\tOLE-FILE[%02X]: %s\n" %(j, ole))
	if (secVrs >= 0x06): i += 1 # skip 00
	log.write("\n")
	return oleFiles, i

def readOccSection(data, offset, log, index):
	occSec = UFRxOccSection()

	occSec.n, i = getUInt32(data, offset)
	cnt, i = getUInt32(data, i)
	log.write("\t\tSection %d: count = %d\n" %(index, cnt))
	for j in range(cnt):
		prp = UFRxOccSecProperty()
		i = prp.readValues(data, i)
		occSec.properties[prp.t] = prp
		log.write("\t\t\tOCC-Section-Property[%02X]: %s\n" %(j, prp))
	return occSec, i

def readOccSettingValue(data, offset):
	value = UFRxOccSettingValue()
	value.t1, i = getLen32Text16(data, offset)
	value.id, i = getUUID(data, i)
	value.t2, i = getLen32Text8(data, i)
	return value, i

def readOccSettings(data, offset, log):
	set = UFRxOccSetting()
	cnt, i = getUInt32(data, offset )
	log.write("\t\tSettings: count = %d\n" %(cnt))
	for j in range(cnt):
		v, i = readOccSettingValue(data, i)
		set.values.append(v)
		log.write("\t\tSettings-Value[%d]:%s" %(j, v))
	return set, i

def readOccExport(data, offset, log):
	exp = UFRxOccExport()

	exp.buf, i = getUInt8A(data, offset, 10)
	log.write("\t\tValue: [%s]" %(IntArr2Str(exp.buf, 1)))
	if (getFileVersion() >= 2015): i += 1 # skip 00
	val, j  = getUInt32(data, i)
	val2, k = getUInt32(data, j)
	if (val > 1) or (val==1 and (val2 > 1)):
		if (val2 > 0xFFFF):
			st1, i = getLen32Text16(data, i)
			su1, i = getUUID(data, i)
			st2, i = getLen32Text8(data, i)
			exp.val = (st1, su1, st2)
			log.write(", '%s', {%s}, '%s'\n" %(st1, su1, st2))
		else:
			log.write(", count = %d\n" %(val))
			exp.val = []
			i = j
			for k in range(val):
				t, i = getLen32Text16(data, i)
				l, i = readExportItems(data, i, log)
				p, i = getUInt32A(data, i, 3)
				exp.val.append((t, l))
				if (getFileVersion() >= 2018): i += 1 # skip 00
	else:
		i = j
		log.write(", count = %d\n" %(val))
	return exp, i

def readOccHeader(data, offset, log):
	occ = UFRxOccurence()
	secVrs = getUFRxVersion(3)

	occ.a1,   i = getUInt32A(data, offset, 4) # (EndStringFlag, Ref2IDFromSection5, OccurrenceID, Unknown_1)
	occ.size, i = getUInt32(data, i) # Unknown_2:  [UInt32]
	# Title:      [Text16]
	# Unknown_3:  [UInt32]
	# Unknown_4:  [UInt16r]
	# Padding_21: [UInt8]
	if (occ.size == 1):
		occ.a2, i = getLen32Text16(data, i)
	elif (occ.size > 1):
		occ.a2, i = getLen32Text16(data, i - 4)
	occ.a3,   i = getUInt8A(data, i, 5)
	if (secVrs >= 0x14): i += 1 # skip 00 00
	if (secVrs >= 0x15): i += 1 # skip 00 00
	return occ, i

def readOccurences(data, offset, log):
	secVrs = getUFRxVersion(3)
	occurences = []
	cnt, i = getUInt32(data, offset)
	log.write("OCCURENCES: count = %d\n" %(cnt))
	for j in range(cnt):
		occ, i = readOccHeader(data, i, log)
		log.write("\tOccurence[%02X]: %s\n" %(j, occ))
		occ.sec1, i = readOccSection(data, i, log, 1)
		occ.sec2, i = readOccSection(data, i, log, 2)
		occ.set, i  = readOccSettings(data, i, log)
		occ.exp, i  = readOccExport(data, i, log)
		occurences.append(occ)
	if (cnt == 0):
		padding, i = readUInt32(data, i, log, 'Padding')
	log.write("\n")
	return occurences, i

def readProperties(data, offset, log):
	secVrs = getUFRxVersion(9)
	log.write("PROPERTIES:\n")
	version, i = readUInt32(data, offset, log, 'Version')
	cnt,     i = readUInt32(data, i, log, 'Count')
	# 0x11: ModelGeometryVersions
	# 0x12: GeometricRevision
	# 0x13: MassPropRevisions
	# 0x15: DocumentSubType
	# 0x16, 0x17, 0x18, 0x24, 0x25: DesignView
	# 0x1C: BOMRevision
	# 0x1F: ActiveLODonSaveCheckSum
	if (secVrs >= 0x05):
		SINGLES = [0x12, 0x15, 0x1A, 0x1B, 0x1C, 0x20, 0x23, 0x28, 0x29, 0x2B]
		DOUBLES = [0x11, 0x13, 0x1F, 0x16, 0x17, 0x24, 0x25, 0x18, 0x2A]
	else:
		SINGLES = [0x11, 0x12, 0x15, 0x1A, 0x1B, 0x1C, 0x20, 0x23, 0x28, 0x29, 0x2B]
		DOUBLES = [0x13, 0x1F, 0x16, 0x17, 0x24, 0x25, 0x18, 0x2A]
	d = {}
	for j in range(cnt):
		t, i = getUInt8(data, i)
		log.write("\t[%02X]: " %(t))
		if (t in [0x04]):
			v, i = getLen32Text16(data, i)
			log.write("'%s'\n" %(v))
		elif (t in [0x0F, 0x10, 0x1D]): # (AdaptivelyUsedInAssembly, LastSavedWithoutUpdating, BOMUpdatePending)
			v, i = getUInt8(data, i)
			log.write("%d\n" %(v))
		elif (t in SINGLES):
			v, i = getUUID(data, i)
			log.write("{%s}\n" %(v))
		elif (t in DOUBLES):
			u1, i = getUUID(data, i)
			u2, i = getUUID(data, i)
			log.write("({%s},{%s})\n" %(u1, u2))
			v = (u1, u2)
		else:
			raise ValueError(u"Unknown type %02X for array element in readProperties!" %(t))
		d[t] = v

	log.write("\n")
	return (version, d), i

def readNextAbschnitt1(data, offset, log):
	log.write("NEXT Abschnitt 1:\n")
	n, i = readUInt16(data, offset, log, 'unknown_1')
	cnt, i = readUInt32(data, i, log, 'UIDS')
	l = []
	for j in range(cnt):
		u, i = getUUID(data, i)
		log.write("\t\t[%02X] - {%s}\n" %(j, u))
	log.write("\n")
	return (n, l), i

def readNextAbschnitt2(data, offset, log):
	cnt, i = getUInt32(data, offset)
	log.write("NEXT Abschnitt 2: count  = %d\n" %(cnt))
	l = []
	for j in range(cnt): # UID L L h B ""
		u, i = getUUID(data, i)
		a, i = getUInt32A(data, i, 2)
		h, i = getUInt16(data, i)
		b, i = getUInt8(data, i)
		t, i = getLen32Text16(data, i)
		log.write("\t\t[%02X] - {%s},[%s],%03X,%02X,'%s'\n" %(j, u, IntArr2Str(a,4), h, b, t))
	log.write("\n")
	return l, i

def readUnknown2(data, offset, log):
	log.write("UNKNOWN 2:\n")
	l =	 []
	a = ()
	if (getFileVersion() >= 2012):
		n1,  i = readUInt32(data, offset, log, 'Data')
		cnt, i = getUInt32(data, i)
		for j in range(cnt):
			t1, i = getLen32Text16(data, i)
			t2 = ''
			if (len(t1)):
				t2, i = getLen32Text16(data, i)
			log.write("\tText[%02X]: '%s'='%s'\n" %(j, t1, t2))
		n2, i = getUInt8(data, i)
	else:
		i = offset
		n1 = 0
		n2 = 0
		l.append(('',))
	log.write('\tPadding: %d\n' %(n2))
	return (n1, l, n2), i

def readBomRecord(data, offset, log):
	bom = None
	log.write("BOM-RECORD:\n")
	b, i = readBoolean(data, offset, log, 'Has-BOM')
	if (b):
		bom = UFRxBOM()
		bom.unit, i  = getLen32Text16(data, i)
		bom.name, i  = getLen32Text16(data, i)
		bom.repr, i  = getLen32Text16(data, i)
		bom.value, i = getFloat64(data, i)
		bom.pad, i   = getUInt16(data, i)
		log.write("\t%s\n" %(bom))
	log.write("\n")
	return bom, i

def readUnknown3(data, offset, log):
	log.write("UNKNOWN_3\n")
	a, i = readUInt8A(data, offset, log, 'Padding1', 3)
	n1 = 6
	if (getFileVersion() >= 2015):
		n1, i = getUInt16(data, i)
	n2 = 0
	if (getFileVersion() >= 2012):
		n2, i = getUInt8(data, i)
	log.write("\tUnknown: %03X, %02X\n\n" %(n1, n1))
	return (a, n1, n2), i

def readExportBlock(data, offset, log):
	export = UFRxExport()
	export.type_name, i = getLen32Text8(data, offset)
	export.name,      i = getLen32Text16(data, i)
	export.guid,      i = getUUID(data, i)
	if (getFileVersion() >= 2012):
		export.flags, i = getUInt16(data, i)
	else:
		export.flags, i = getUInt8(data, i)
	export.unknown,   i = getUInt32(data, i)
	return export, i

def readExportProperty(data, offset):
	if (getUFRxVersion(9) >= 4):
		SINGLES = [0x22, 0x29]
		DOUBLES = [0x16, 0x17, 0x18, 0x24, 0x25, 0x2A]
	else:
		SINGLES = [0x16, 0x17, 0x18, 0x22, 0x24, 0x25, 0x29]
		DOUBLES = [0x2A]

	t, i   = getUInt8(data, offset)
	if (t in [0x27]):
		v, i = getUInt32(data, i)
	elif (t in SINGLES):
		v, i = getUUID(data, i)
	elif (t in DOUBLES):
		u1, i = getUUID(data, i)
		u2, i = getUUID(data, i)
		v = (u1, u2)
	else:
		raise ValueError(u"Unknown type %02X for array element in readExportProperty!" %(t))
	return (t, v), i

def readExportItems(data, offset, log):
	m, i = getUInt32A(data, offset, 2)
	assert m[0] == m[1]
	lst = []
	for j in range(m[0]):
		osi = UFRxOccSecItem()
		i = osi.readValues(data, i)
		lst.append(osi)
		log.write("\t\t\t\t[%02X] - %s,\n" %(j, osi))
	return lst, i

def readExportBlocks(data, offset, log):
	cnt, i = getUInt32(data, offset)
	log.write("EXPORTS: count = %d\n" %(cnt))
	exports = []
	for j in range(cnt):
		export, i = readExportBlock(data, i, log)
		exports.append(export)
		log.write("\tExport[%02X]\n" %(j))
		log.write("\t\tType:       %s {%s}\n" %(export.type_name, export.guid))
		log.write("\t\tName:       '%s'\n" %(export.name))
		log.write("\t\tFlags:      %s\n" %(export.flags))
		log.write("\t\tUnknown:    %s\n" %(export.unknown))
		cnt, i = getUInt32(data, i)
		log.write("\t\tProperties: count = %d\n" %(cnt))
		for j in range(cnt):
			property, i = readExportProperty(data, i)
			log.write("\t\t\tProperty[%02X]: %s\n" %(j, property))
			export.properties.append(property)
		cnt = 6 if (getFileVersion() >= 2015) else 5
		log.write("\t\tSettings:   count = %d\n" %(cnt))
		for j in range(cnt):
			log.write("\t\t\tSetting[%02X]: ")
			b, i = getBoolean(data, i)
			if b:
				l1, i = readExportItems(data, i, log)
				l2, i = readExportItems(data, i, log)
				export.settings.append((l1, l2))
			else:
				export.settings.append(None)
				log.write("None\n")
	log.write("\n")
	return exports, i

def readBoundBox(data, offset, log):
	a, i = getFloat32A(data, offset, 6)
	log.write("BOUND-BOX: (%g,%g,%g)-(%g,%g,%g)\n\n" %(a[0], a[1], a[2], a[3], a[4], a[5]))
	return BoundBox(VEC(a[0: 3]), VEC(a[3:])), i

def readIProperty(data, offset):
	iProp = UFRxIProperty()
	iProp.b, i  = getBoolean(data, offset)
	iProp.t1, i = getLen32Text16(data, i)
	iProp.t2, i = getLen32Text16(data, i)
	iProp.b,  i = getUInt8(data, i)
	iProp.u,  i = getUUID(data, i)
	iProp.p,  i = getUInt32A(data, i, 2)
	return iProp, i

def readiProperties(data, offset, log):
	secVrs = getUFRxVersion(18)
	log.write("I-PROPERTIES:\n")
	iProperties = UFRxIProperties()
	i = offset
	if ((len(data) - i) > 9):
		cnt, i = getUInt32(data, i)
		for j in range(cnt):
			iPrp, i = readIProperty(data, i)
			log.write("\t\tValue[%02X]: %s\n" %(j, iPrp))
			iProperties.properties.append(iPrp)
		iProperties.selected, i = readText16(data, i, log, 'Selected')
		if (secVrs >= 0x03):
			iProperties.b, i = readBoolean(data, i, log, 'Unknown4')
		else:
			log.writelines("\tUnknown4: False\n")
	log.write("\n")
	return iProperties, i

def readAppendix(data, offset, log):
	secVrs = getUFRxVersion(20)
	log.write("APPENDIX:\n")
	appendix = UFRxAppendix()
	appendix.p1, i = readUInt32A(data, offset, log, 'Data', 2)
	if (secVrs >= 0x01):
		appendix.p2, i = readUInt8(data, i, log, 'Unknown')
	else:
		log.write("\tUnknown: 00\n")
	log.write("\n")
	return appendix, i

def read(data):
#	dumpFolder = getDumpFolder()
#	if (not (dumpFolder is None)):
#		ufrx = UFRxDocument()
#		with io.open(u"%s/UFRxDoc.log" %(dumpFolder), 'w', encoding='utf8') as log:
#			i = 0
#			try:
#				ufrx.header1,       i = readHeader1(data,        i, log)
#				ufrx.lodToc,        i = readLodToc(data,         i, log)
#				ufrx.header2,       i = readHeader2(data,        i, log)
#				ufrx.lod_list,      i = readLODs(data,           i, log)
#				ufrx.inventorFiles, i = readInvFiles(data,       i, log)
#				ufrx.partFiles,     i = readOleFiles(data,       i, log)
#				ufrx.occurences,    i = readOccurences(data,     i, log)
#				ufrx.properties,    i = readProperties(data,     i, log)
#				ufrx.abschnitt1,    i = readNextAbschnitt1(data, i, log)
#				ufrx.abschnitt2,    i = readNextAbschnitt2(data, i, log)
#				ufrx.unknown2,      i = readUnknown2(data,       i, log)
#				ufrx.bomRecord,     i = readBomRecord(data,      i, log)
#				ufrx.unknown3,      i = readUnknown3(data,       i, log)
#				ufrx.exportBlocks,  i = readExportBlocks(data,   i, log)
#				ufrx.rangeBox,      i = readBoundBox(data,       i, log)
#				ufrx.iProperties,   i = readiProperties(data,    i, log)
#				ufrx.appendix,      i = readAppendix(data,       i, log)
#			except Exception as ex:
#				Beep(880, 250)
#				logError(traceback.format_exc())
#				logError(str(ex))
#				log.write('\n')
#			if (i < len(data)):
#				if (sys.version_info.major < 3):
#					b = " ".join(["%02X" %(ord(c)) for c in data[i:]])
#				else:
#					b = " ".join(["%02X" %(c) for c in data[i:]])
#				l = 0x20*3
#				for j in range(0, len(b), l):
#					log.write(b[j:j+l])
#					log.write('\n')
#				with io.open(u"%s/UFRxDoc.ax" %(dumpFolder), 'w', encoding='utf8') as ax:
#					ax.write(b)
#					ax.write('\n')
#		return ufrx
	return None