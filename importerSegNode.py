# -*- coding: utf-8 -*-

'''
importerSegNode.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerClasses        import AbstractData, AbstractValue, Header0, Angle, GraphicsFont, Lightning, ModelerTxnMgr, NtEntry, ParameterNode
from importerConstants      import REF_CHILD, REF_CROSS, REF_PARENT, VAL_UINT8, VAL_UINT16, VAL_UINT32, VAL_REF, VAL_STR8, VAL_STR16, VAL_ENUM
from importerUtils          import *
from math                   import log10, pi
from importerTransformation import Transformation3D

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

F_2010   = Struct('<fL').unpack_from
APP_4_A  = Struct('<LHLff').unpack_from
APP_4_B1 = Struct('<ffHB').unpack_from
APP_4_B2 = Struct('<ffHH').unpack_from
APP_5_A  = Struct('<ddL').unpack_from
APP_5_B  = Struct('<BBH').unpack_from
MTM_LST  = Struct('<LBL').unpack_from

def isList(data, code):
	return ((data[-1] == 0x3000) and (data[-2] == code))

def CheckList(data, offset, type):
	lst, i = getUInt16A(data, offset, 2)
	if (getFileVersion() < 2015):
		if (lst[0] == 0 and (lst[1] == 0)):
			return i - 4 # keep fingers crossed that this is really the number of bytes!
	assert (isList(lst, type)), 'Expected list %d - not [%s]' %(type, IntArr2Str(lst, 4))
	return i

def getIndex(ref):
	if (ref is None): return u'None'
	return u'%04X' %ref.index

_TYP_CHAR_                  = 0x0010
_TYP_UINT8_                 = 0x0011
_TYP_SINT8_                 = 0x0012
_TYP_UINT16_                = 0x0013
_TYP_SINT16_                = 0x0014
_TYP_UINT32_                = 0x0015
_TYP_SINT32_                = 0x0016
_TYP_FLOAT32_               = 0x0017
_TYP_FLOAT64_               = 0x0018
_TYP_NODE_REF_              = 0x0019
_TYP_NODE_X_REF_            = 0x001A
_TYP_STRING8_               = 0x001B
_TYP_STRING16_              = 0x001C

_TYP_UINT8_A_               = 0x0020
_TYP_SINT8_A_               = 0x0021
_TYP_UINT16_A_              = 0x0022
_TYP_SINT16_A_              = 0x0023
_TYP_UINT32_A_              = 0x0024
_TYP_SINT32_A_              = 0x0025
_TYP_FLOAT32_A_             = 0x0026
_TYP_FLOAT64_A_             = 0x0027

_TYP_FONT_                  = 0x0040
_TYP_2D_F64_U32_4D_U8_      = 0x0041
_TYP_LIGHTNING_             = 0x0042
_TYP_RESULT_ITEM4_          = 0x0043
_TYP_U32_TXT_TXT_DATA_      = 0x0044
_TYP_U32_TXT_U32_LST2_      = 0x0045
_TYP_APP_1_                 = 0x0046
_TYP_F64_F64_U32_U8_U8_U16_ = 0x0047
_TYP_NT_ENTRY_              = 0x0048
_TYP_2D_UINT32_             = 0x0049
_TYP_MTM_LST_               = 0x004A
_TYP_NODE_LST2_X_REF_       = 0x004B
_TYP_TRANSFORMATIONS_       = 0x004C
_TYP_U16_COLOR_             = 0x004D

_TYP_LIST_UINT16_A_         = 0x8001
_TYP_LIST_SINT16_A_         = 0x8002
_TYP_LIST_UINT32_A_         = 0x8003
_TYP_LIST_SINT32_A_         = 0x8004
_TYP_LIST_FLOAT32_A_        = 0x8005
_TYP_LIST_FLOAT64_A_        = 0x8006
_TYP_LIST_FONT_             = 0x8007
_TYP_LIST_X_REF_            = 0x8008
_TYP_LIST_CHAR_             = 0x8009

_TYP_MAP_U32_U8_            = 0x7001
_TYP_MAP_U32_U32_           = 0x7002
_TYP_MAP_U32_F64_           = 0x7003
_TYP_MAP_KEY_REF_           = 0x7004
_TYP_MAP_KEY_X_REF_         = 0x7005
_TYP_MAP_REF_REF_           = 0x7006
_TYP_MAP_TEXT8_REF_         = 0x7007
_TYP_MAP_TEXT8_X_REF_       = 0x7008
_TYP_MAP_TEXT8_3D_F32_      = 0x7009
_TYP_MAP_TEXT16_REF_        = 0x700A
_TYP_MAP_TEXT16_X_REF_      = 0x700B
_TYP_MAP_TEXT16_UINT32_     = 0x700C
_TYP_MAP_X_REF_REF_         = 0x700D
_TYP_MAP_X_REF_FLOAT64_     = 0x700E
_TYP_MAP_X_REF_2D_UINT32_   = 0x700F
_TYP_MAP_X_REF_X_REF_       = 0x7010
_TYP_MAP_U32_LIST2_XREF_    = 0x7011
_TYP_MAP_X_REF_LIST2_XREF_  = 0x7012
_TYP_MAP_UID_UINT32_        = 0x7013
_TYP_MAP_UID_X_REF_         = 0x7014
_TYP_MAP_UID_REF_           = 0x7015
_TYP_MAP_U16_U16_           = 0x7016
_TYP_MAP_U16_XREF_          = 0x7017
_TYP_MAP_KEY_APP_1_         = 0x7018
_TYP_MAP_KEY_MAP_APP_1_     = 0x7019
_TYP_MAP_TXT16_UINT32_7_    = 0x7020

_TYP_MAP_MDL_TXN_MGR_       = 0x6001

_TYP_RESULT_1_              = 0x5001
_TYP_RESULT_2_              = 0x5002
_TYP_RESULT_3_              = 0x5003
_TYP_RESULT_4_              = 0x5004
_TYP_RESULT_5_              = 0x5005

TYP_LIST_FUNC = {
	_TYP_CHAR_:                  'getListChars',
	_TYP_NODE_REF_:              'getList2Childs',
	_TYP_NODE_X_REF_:            'getListXRefs',
	_TYP_STRING8_:               'getListString8s',
	_TYP_STRING16_:              'getListString16s',
	_TYP_UINT8_:                 'getListUInt8s',
	_TYP_SINT8_:                 'getList2SInt8s',
	_TYP_UINT16_:                'getListUInt16s',
	_TYP_SINT16_:                'getListSInt16s',
	_TYP_UINT32_:                'getListUInt32s',
	_TYP_SINT32_:                'getListSInt32s',
	_TYP_FLOAT32_:               'getListFloat32s',
	_TYP_FLOAT64_:               'getListFloat64s',
	_TYP_UINT8_A_:               'getListUInt8sA',
	_TYP_SINT8_A_:               'getListSInt8sA',
	_TYP_UINT16_A_:              'getListUInt16sA',
	_TYP_SINT16_A_:              'getListSInt16sA',
	_TYP_UINT32_A_:              'getListUInt32sA',
	_TYP_SINT32_A_:              'getListSInt32sA',
	_TYP_FLOAT32_A_:             'getListFloat32sA',
	_TYP_FLOAT64_A_:             'getListFloat64sA',
	_TYP_FONT_:                  'getListFonts',
	_TYP_LIGHTNING_:             'getListLightnings',
	_TYP_2D_F64_U32_4D_U8_:      'getListApp1',
	_TYP_U32_TXT_TXT_DATA_:      'getListApp2',
	_TYP_U32_TXT_U32_LST2_:      'getListApp3',
	_TYP_APP_1_:                 'getListApp4',
	_TYP_F64_F64_U32_U8_U8_U16_: 'getListApp5',
	_TYP_NT_ENTRY_:              'getListNtEntries',
	_TYP_MTM_LST_:               'getListMdlrTxnMgr',
	_TYP_NODE_LST2_X_REF_:       'getListList2XRef',
	_TYP_TRANSFORMATIONS_:       'getListTransformations',
	_TYP_U16_COLOR_:             'getListUInt16Colors',
	_TYP_LIST_UINT16_A_:         'getListListUInt16sA',
	_TYP_LIST_SINT16_A_:         'getListListSInt16sA',
	_TYP_LIST_UINT32_A_:         'getListListUInt32sA',
	_TYP_LIST_SINT32_A_:         'getListListSInt32sA',
	_TYP_LIST_FLOAT32_A_:        'getListListFloats32sA',
	_TYP_LIST_FLOAT64_A_:        'getListListFloats64sA',
	_TYP_LIST_FONT_:             'getListListFonts',
	_TYP_LIST_X_REF_:            'getListListXRefs',
	_TYP_LIST_CHAR_:             'getListListChars',
}

TYP_04_FUNC = {
	_TYP_NODE_REF_:              'getList2Childs',
	_TYP_NODE_X_REF_:            'getListXRefs',
	_TYP_RESULT_ITEM4_:          'getListResults',
	_TYP_SINT32_A_:              'getListSInt32sA',
	_TYP_STRING16_:              'getListString16s',
	_TYP_STRING8_:               'getListString8s',
	_TYP_UINT32_:                'getListUInt32s',
	_TYP_UINT32_A_:              'getListUInt32sA',
	_TYP_2D_UINT32_:             'getList2DUInt32s',
	_TYP_RESULT_1_:              'getListResult1',
	_TYP_RESULT_2_:              'getListResult2',
	_TYP_RESULT_3_:              'getListResult3',
	_TYP_RESULT_4_:              'getListResult4',
	_TYP_RESULT_5_:              'getListResult5',
}

TYP_ARRAY_FUNC = {
	_TYP_UINT32_:                'getArrayU32',
	_TYP_NODE_REF_:              'getArrayRef',
	_TYP_NODE_X_REF_:            'getArrayXRef',
}

TYP_MAP_FUNC = {
	_TYP_MAP_U16_U16_:          'getMapU16U16',
	_TYP_MAP_U16_XREF_:         'getMapU16XRef',
	_TYP_MAP_U32_U8_:           'getMapU32U8',
	_TYP_MAP_U32_U32_:          'getMapU32U32',
	_TYP_MAP_U32_F64_:          'getMapU32F64',
	_TYP_MAP_KEY_REF_:          'getMapU32Ref',
	_TYP_MAP_KEY_X_REF_:        'getMapU32XRef',
	_TYP_MAP_REF_REF_:          'getMapRefRef',
	_TYP_MAP_X_REF_REF_:        'getMapXRefRef',
	_TYP_MAP_X_REF_FLOAT64_:    'getMapXRefF64',
	_TYP_MAP_X_REF_X_REF_:      'getMapXRefXRef',
	_TYP_MAP_X_REF_2D_UINT32_:  'getMapXRefU2D',
	_TYP_MAP_U32_LIST2_XREF_:   'getMapU32XRefL',
	_TYP_MAP_X_REF_LIST2_XREF_: 'getMapXRefXRefL',
	_TYP_MAP_UID_UINT32_:       'getMapUidU32',
	_TYP_MAP_UID_REF_:          'getMapUidCRef',
	_TYP_MAP_UID_X_REF_:        'getMapUidXRef',
	_TYP_MAP_TEXT8_REF_:        'getMapT8Ref',
	_TYP_MAP_TEXT8_X_REF_:      'getMapT8XRef',
	_TYP_MAP_TEXT8_3D_F32_:     'getMapT83dF64',
	_TYP_MAP_TEXT16_REF_:       'getMapT16Ref',
	_TYP_MAP_TEXT16_X_REF_:     'getMapT16XRef',
	_TYP_MAP_TEXT16_UINT32_:    'getMapT16U32',
	_TYP_MAP_TXT16_UINT32_7_:   'getMapTxt16UInt32_7',
	_TYP_MAP_MDL_TXN_MGR_:      'getMapMdlTxnMgr',
	_TYP_MAP_KEY_APP_1_:        'getMapKeyApp1',
	_TYP_MAP_KEY_MAP_APP_1_:    'getMapKeyMapApp1',
}

class SecNode(AbstractData):

	def __init__(self):
		super(SecNode, self).__init__()
		self.analysed = False

	def ReadUInt8(self, offset, name):
		x, i = getUInt8(self.data, offset)
		self.set(name, x, VAL_UINT8)
		return i

	def ReadUInt8A(self, offset, n, name):
		x, i = getUInt8A(self.data, offset, n)
		self.set(name, x, VAL_UINT8)
		return i

	def ReadUInt16(self, offset, name):
		x, i = getUInt16(self.data, offset)
		self.set(name, x, VAL_UINT16)
		return i

	def ReadUInt16A(self, offset, n, name):
		x, i = getUInt16A(self.data, offset, n)
		self.set(name, x, VAL_UINT16)
		return i

	def ReadSInt16(self, offset, name):
		x, i = getSInt16(self.data, offset)
		self.set(name, x)
		return i

	def ReadSInt16A(self, offset, n, name):
		x, i = getSInt16A(self.data, offset, n)
		self.set(name, x)
		return i

	def ReadUInt32(self, offset, name):
		x, i = getUInt32(self.data, offset)
		self.set(name, x, VAL_UINT32)
		return i

	def ReadUInt32A(self, offset, n, name):
		x, i = getUInt32A(self.data, offset, n)
		self.set(name, x, VAL_UINT32)
		return i

	def ReadSInt32(self, offset, name):
		x, i = getSInt32(self.data, offset)
		self.set(name, x)
		return i

	def ReadSInt32A(self, offset, n, name):
		x, i = getSInt32A(self.data, offset, n)
		self.set(name, x)
		return i

	def ReadFloat32(self, offset, name):
		x, i = getFloat32(self.data, offset)
		self.set(name, x)
		return i

	def ReadFloat32A(self, offset, n, name):
		x, i = getFloat32A(self.data, offset, n)
		self.set(name, x)
		return i

	def ReadFloat32_2D(self, offset, name):
		x, i = getFloat32_2D(self.data, offset)
		self.set(name, x)
		return i

	def ReadFloat32_3D(self, offset, name):
		x, i = getFloat32_3D(self.data, offset)
		self.set(name, x)
		return i

	def ReadFloat64(self, offset, name):
		x, i = getFloat64(self.data, offset)
		self.set(name, x)
		return i

	def ReadFloat64A(self, offset, n, name):
		x, i = getFloat64A(self.data, offset, n)
		self.set(name, x)
		return i

	def ReadFloat64_2D(self, offset, name):
		v, i = getFloat64_2D(self.data, offset)
		self.set(name, v)
		return i

	def ReadFloat64_3D(self, offset, name):
		v, i = getFloat64_3D(self.data, offset)
		self.set(name, v)
		return i

	def ReadVec3D(self, offset, name, scale = 1.0):
		v, i = getFloat64_3D(self.data, offset)
		v *= scale
		self.set(name, v)
		return i

	def ReadUUID(self, offset, name):
		x, i = getUUID(self.data, offset)
		self.set(name, x)
		return i

	def ReadColorRGBA(self, offset, name):
		x, i = getColorRGBA(self.data, offset)
		self.set(name, x)
		i += getBlockSize()
		return i

	def ReadMaterial(self, offset, count):
		i = self.ReadColorRGBA(offset, 'Color.c0')
		i = self.ReadColorRGBA(i, 'Color.diffuse')
		for j in range(count):
			i = self.ReadColorRGBA(i, 'Color.c%d' %(j+1))
		i = self.ReadFloat32(i, 'Color.f')
		i += getBlockSize()
		return i

	def ReadBoolean(self, offset, name):
		x, i = getBoolean(self.data, offset)
		self.set(name, x)
		return i

	def ReadEnum16(self, offset, name, enumName, enumValues):
		index, i = getUInt16(self.data, offset)
		self.set('Enum', enumName, None)
		self.set('Values', enumValues, None)
		self.set(name, index, VAL_ENUM)
		return i

	def ReadEnum32(self, offset, name, enumName, enumValues):
		index, i = getUInt32(self.data, offset)
		self.set('Enum', enumName, None)
		self.set('Values', enumValues, None)
		self.set(name, index, VAL_ENUM)
		return i

	def ReadAngle(self, offset, name):
		x, i = getFloat64(self.data, offset)
		x = Angle(x, pi/180.0, u'\xb0')
		self.set(name, x)
		return i

	def ReadLen32Text8(self, offset, name = None):
		x, i = getLen32Text8(self.data, offset)
		if (name):
			self.set(name, x, VAL_STR8)
		else:
			self.name = x
		return i

	def ReadText8(self, offset, l, name = None):
		x, i = getText8(self.data, offset, l)
		if (name):
			self.set(name, x, VAL_STR8)
		else:
			self.name = x
		return i

	def ReadLen32Text16(self, offset, name = None):
		x, i = getLen32Text16(self.data, offset)
		if (name):
			self.set(name, x, VAL_STR16)
		else:
			self.name = x
		return i

	def ReadNodeRef(self, offset, name, number, type):
		m, i = getUInt32(self.data, offset)
		ref = SecNodeRef(m, type, name)

		if (ref.index > 0):
			ref.number = number
			if (ref.index == self.index):
				logError(u"ERROR> Found self-ref '%s' for (%04X): %s", name, self.index, self.typeName)
			else:
				self.references.append(ref)
		else:
			ref = None
		self.set(name, ref, VAL_REF)
		return i

	def ReadChildRef(self, offset, name = 'ref', number = None):
		return self.ReadNodeRef(offset, name, number , REF_CHILD)

	def ReadCrossRef(self, offset, name = 'ref', number = None):
		return self.ReadNodeRef(offset, name, number, REF_CROSS)

	def ReadParentRef(self, offset):
		return self.ReadNodeRef(offset, 'parent', None, REF_CROSS)

	def __getListStrings(self, name, offset, cnt, mtd, cls):
		lst = []
		i   = offset
		for j in range(cnt):
			t, i = mtd(self.data, i)
			lst.append(t)
		self.set(name, lst, cls)
		return i

	def __getList2Nums(self, name, offset, cnt, s, w, fmt, skipLen = True):
		if (skipLen):
			lst = Struct('<' + s * cnt).unpack_from(self.data, offset)
			i   = offset + cnt * w
		else:
			val = Struct('<' + (s+'L')*cnt).unpack_from(self.data, offset)
			i   = offset + (w+4)*cnt # 4Bytes float 4Byte blocklen
			lst = val[0::2]

		self.set(name, lst)
		return i

	def __getList2NumsA(self, name, offset, cnt, arraysize, s, w, fmt, skipLen = True):
		if (skipLen):
			val = Struct('<' + s*arraysize*cnt).unpack_from(self.data, offset)
			lst = reshape(val, arraysize)
			i   = offset + (w * arraysize) * cnt
		else:
			val = Struct('<' + (s*arraysize+'L')*cnt).unpack_from(self.data, offset)
			lst = reshape([n for i, n in enumerate(val) if (i % (arraysize + 1)) != arraysize], arraysize)
			i   = offset + (w * arraysize + 4) * cnt # w + 4Bytes for blocklen

		self.set(name, lst)
		return i

	def __getListListIntsA(self, name, typ, offset, cnt, arraysize, fmt):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, typ, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')

		self.set(name, lst)
		return i

	def __getListListFloatsA(self, name, typ, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, typ, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')

		self.set(name, lst)
		return i

	def getListChars(self, name, offset, cnt, arraysize):
		try:
			t, i = getText8(self.data, offset, cnt)
			self.set(name, t)
			return i
		except:
			t, i = getUInt8A(self.data, offset, cnt)
			self.set(name, t, VAL_UINT8)
			return offset+cnt

	def getList2Childs(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadChildRef(i, name, j)
			lst.append(self.get(name))
		self.set(name, lst, VAL_REF)
		return i

	def getListXRefs(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			lst.append(self.get(name))
		self.set(name, lst, VAL_REF)
		return i

	def getListString8s(self, name, offset, cnt, arraysize):
		return  self.__getListStrings(name, offset, cnt, getLen32Text8, VAL_STR8)

	def getListString16s(self, name, offset, cnt, arraysize):
		return  self.__getListStrings(name, offset, cnt, getLen32Text16, VAL_STR16)

	def getListUInt8s(self, name, offset, cnt, arraysize):
		return self.__getList2Nums(name, offset, cnt, 'B', 1, u"%02X")

	def getListSInt16s(self, name, offset, cnt, arraysize):
		return self.__getList2Nums(name, offset, cnt, 'b', 1, u"%d")

	def getListUInt16s(self, name, offset, cnt, arraysize):
		return self.__getList2Nums(name, offset, cnt, 'H', 2, u"%03X")

	def getListSInt16s(self, name, offset, cnt, arraysize):
		return self.__getList2Nums(name, offset, cnt, 'h', 2, u"%d")

	def getListUInt32s(self, name, offset, cnt, arraysize):
		return self.__getList2Nums(name, offset, cnt, 'L', 4, u"%04X")

	def getListSInt32s(self, name, offset, cnt, arraysize):
		return self.__getList2Nums(name, offset, cnt, 'l', 4, u"%d")

	def getListFloat32s(self, name, offset, cnt, arraysize):
		return self.__getList2Nums(name, offset, cnt, 'f', 4, u"%g")

	def getListFloat64s(self, name, offset, cnt, arraysize):
		return self.__getList2Nums(name, offset, cnt, 'd', 8, u"%g")

	def getListUInt8sA(self, name, offset, cnt, arraysize):
		return self.__getList2NumsA(name, offset, cnt, arraysize, 'B', 1, u"%02X")

	def getListSInt8sA(self, name, offset, cnt, arraysize):
		return self.__getList2NumsA(name, offset, cnt, arraysize, 'b', 1, u"%d")

	def getListUInt16sA(self, name, offset, cnt, arraysize):
		return self.__getList2NumsA(name, offset, cnt, arraysize, 'H', 2, u"%03X")

	def getListSInt16sA(self, name, offset, cnt, arraysize):
		return self.__getList2NumsA(name, offset, cnt, arraysize, 'h', 2, u"%d", (getFileVersion() > 2010))

	def getListUInt32sA(self, name, offset, cnt, arraysize):
		return self.__getList2NumsA(name, offset, cnt, arraysize, 'L', 4, u"%04X")

	def getListSInt32sA(self, name, offset, cnt, arraysize):
		return self.__getList2NumsA(name, offset, cnt, arraysize, 'l', 4, u"%d")

	def getListFloat32sA(self, name, offset, cnt, arraysize):
		return self.__getList2NumsA(name, offset, cnt, arraysize, 'f', 4, u"%g", (getFileVersion() > 2010))

	def getListFloat64sA(self, name, offset, cnt, arraysize):
		return self.__getList2NumsA(name, offset, cnt, arraysize, 'd', 8, u"%g")

	def getListFonts(self, name, offset, cnt, arraysize):
		lst    = []
		i      = offset
		skip   = 2 * getBlockSize()
		if (self.segment.segment.version.major >= 25): skip += 1 # skip 00
		FONT_A = Struct('<LHHHHBBHH').unpack_from
		FONT_B = Struct('<ffBBB').unpack_from
		for j in range(cnt):
			val = GraphicsFont()
			a   = FONT_A(self.data, i)
			val.number = a[0]
			val.ukn1   = a[1:5]
			val.ukn2   = a[5:7]
			val.ukn3   = a[7:]
			i += 18
			val.name, i   = getLen32Text16(self.data, i)
			a = FONT_B(self.data, i)
			val.ukn4 = a[0:2]
			val.ukn5 = a[2:]
			i += 11
			lst.append(val)
			i += skip
		self.set(name, lst)
		return i

	def getListLightnings(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		if (getFileVersion() > 2010):
			LIGHTNING = Struct('<Hffffffffffffddddddfffffff').unpack_from
			for j in range(cnt):
				vals = LIGHTNING(self.data, i)
				i += 126
				val = Lightning()
				val.n1 = vals[0]
				val.c1 = Color(vals[1], vals[2], vals[3], vals[4])
				val.c2 = Color(vals[5], vals[6], vals[7], vals[8])
				val.c3 = Color(vals[9], vals[10], vals[11], vals[12])
				val.a1 = vals[13:19]
				val.a2 = vals[19:]
				lst.append(val)
		else:
			LIGHTNING = Struct('<HffffLffffLffffLddddddfffffffL').unpack_from
			for j in range(cnt):
				vals = LIGHTNING(self.data, i)
				i += 142
				val = Lightning()
				val.n1 = vals[0]
				val.c1 = Color(vals[1], vals[2], vals[3], vals[4])
				val.c2 = Color(vals[6], vals[7], vals[8], vals[9])
				val.c3 = Color(vals[11], vals[12], vals[13], vals[14])
				val.a1 = vals[16:22]
				val.a2 = vals[22:-1]
				lst.append(val)
		self.set(name, lst)
		return i

	def getListApp1(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		skip = (getFileVersion() < 2011)
		if (skip):
			APP_1 = Struct('<ddLLBBBBL').unpack_from
		else:
			APP_1 = Struct('<ddLBBBB').unpack_from
		for j in range(cnt):
			val = APP_1(self.data, i)
			if (skip):
				val = val[0:3] + val[4:8]
				i += 32
			else:
				i += 24
			lst.append(val)
		self.set(name, lst)
		return i

	def getListApp2(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		skip = getBlockSize()
		for j in range(cnt):
			n1, i = getUInt32(self.data, i)
			t1, i = getLen32Text16(self.data, i)
			t2, i = getLen32Text16(self.data, i)
			l1 = []
			while (True):
				m, i = getSInt16(self.data, i)
				if (m == -1):
					break
				l1.append(m)
			a1, i = getUInt8A(self.data, i, 3)
			m, i  = getUInt16(self.data, i)
			l2, i = getFloat64A(self.data, i, m)
			l3, i = getFloat32_2D(self.data, i)
			n2, i = getUInt32(self.data, i)
			i += skip
			c1, i = getColorRGBA(self.data, i)
			i += skip
			n3, i = getUInt32(self.data, i)
			n4, i = getUInt8(self.data, i)
			i += (skip + skip)
			lst.append((n1, t1, t2, l1, a1, l2, l3, n2, c1, n3, n4))
		self.set(name, lst)
		return i

	def getListApp3(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip = getBlockSize()
		for j in range(cnt):
			n1, i = getUInt32(self.data, i)
			t1, i = getLen32Text16(self.data, i)
			t2, i = getLen32Text16(self.data, i)
			i = self.ReadList2(i, _TYP_FLOAT64_, '_tmp')
			l1 = self.get('_tmp')
			self.delete('_tmp')
			n3, i = getUInt8(self.data, i)
			i += skip
			lst.append((n1, t1, t2, l1, n3))
		self.set(name, lst)
		return i

	def getListApp4(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset

		if (self.segment.segment.version.major >= 25):
			APP_4_B = APP_4_B2
			block_size = 12 + 2 * getBlockSize()
		else:
			APP_4_B = APP_4_B1
			block_size = 11 + 2 * getBlockSize()

		for j in range(cnt):
			n1, n2, n3, f1, f2 = APP_4_A(self.data, i)
			i += 18
			t1, i = getLen32Text16(self.data, i)
			f3, f4, n4, n5 = APP_4_B(self.data, i)
			i += block_size
			lst.append((n1, n2,  n3,  f1, f2,  t1,  f3, f4, n4, n5))

		self.set(name, lst)
		return i

	def getListApp5(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip = getBlockSize()
		for j in range(cnt):
			f1, f2, n1 = APP_5_A(self.data, i)
			i += 20
			i += skip
			n2, n3, n4 = APP_5_B(self.data, i)
			i += 4
			i += skip
			lst.append((f1, f2, n1, n2,  n3,  n4))
		self.set(name, lst)
		return i

	def getListNtEntries(self, name, offset, cnt, arraysize):
		lst = []
		i  = offset
		for j in range(cnt):
			nt, i  = getUInt32(self.data, i)
			idx, i = getUInt32(self.data, i)
			lst.append(NtEntry(nt, idx))
		self.set(name, lst)
		return i

	def getListMdlrTxnMgr(self, name, offset, cnt, arraysize):
		lst = []
		i = offset
		skip1 = getBlockSize()
		skip2 = 1 if (getFileVersion() > 2018) else 0
		structLen = 9 + skip1 + skip2 # 2 x UInt32 + 1 x UInt8
		for j in range(cnt):
			a = MTM_LST(self.data, i)
			lst.append(a)
			i += structLen
		self.set(name, lst)
		return i

	def getListList2XRef(self, name, offset, cnt, arraysize):
		lst = []
		i = offset
		for j in range(cnt):
			i = self.ReadList2(i, _TYP_LIST_X_REF_, name, 1)
			a = self.get(name)
			self.delete(name)
			i = self.ReadCrossRef(i, name)
			b = self.get(name)
			self.delete(name)
			lst.append((a, b))
		self.set(name, lst, VAL_REF)
		return i

	def getListUInt16Colors(self, name, offset, cnt, arraysize):
		lst = []
		i = offset
		skip = getBlockSize()
		for j in range(cnt):
			h,  i = getUInt16(self.data, i)
			c1, i = getColorRGBA(self.data, i)
			i += skip
			c2, i = getColorRGBA(self.data, i)
			i += skip
			c3, i = getColorRGBA(self.data, i)
			i += skip
			a1, i = getFloat64A(self.data, i, 6)
			a2, i = getFloat32A(self.data, i, 3)
			c4, i = getColorRGBA(self.data, i)
			i += skip
			a = [h, c1, c2, c3]
			a += a1
			a += a2
			a.append(c4)
			lst.append(a)
		self.set(name, lst)
		return i

	def getListTransformations(self, name, offset, cnt, arraysize):
		lst = []
		i = offset
		for j in range(cnt):
			t = Transformation3D()
			i = t.read(self.data, i)
			lst.append(t)
		self.set(name, lst)
		return i

	def getList2DUInt32s(self, name, offset, cnt, arraysize):
		lst = []
		i  = offset
		for j in range(cnt):
			u, i  = getUInt32A(self.data, i, 2)
			lst.append(u)
		self.set(name, lst, VAL_UINT32)
		return i

	def getListResult1(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip = getBlockSize()
		for j in range(cnt):
			u1, i = getUInt32(self.data, i)
			i = self.ReadList4(i, _TYP_UINT32_, name)
			l1 = self.get(name)
			self.delete(name)
			u2, i = getUInt32(self.data, i)
			u3, i = getUInt32(self.data, i)
			i = self.ReadList4(i, _TYP_UINT32_, name)
			l2 = self.get(name)
			self.delete(name)
			a1, i = getFloat64_3D(self.data, i)
			a2, i = getFloat64_3D(self.data, i)
			i += skip
			lst.append((u1, l1, u2, u3, l2, a1, a2))
		self.set(name, lst)
		return i

	def getListResult2(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip = getBlockSize()
		for j in range(cnt):
			d, i = getUInt32A(self.data, i, 2)
			i += skip
			lst.append(d)
		self.set(name, lst, VAL_UINT32)
		return i

	def getListResult3(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		RESULT_3 = Struct('<LHBBdddddd').unpack_from
		skip = getBlockSize()
		for j in range(cnt):
			d = RESULT_3(self.data, i)
			i += 56 + skip
			lst.append(d)
		self.set(name, lst)
		return i

	def getListResult4(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip = getBlockSize()
		for j in range(cnt):
			u, i = getUInt32(self.data, i)
			i = self.ReadList4(i, _TYP_UINT32_, name)
			i += skip
			l = self.get(name)
			self.delete(name)
			lst.append((u, l))
		self.set(name, lst, VAL_UINT32)
		return i

	def getListResult5(self, name, offset, cnt, arraysize):
		lst   = []
		i     = offset
		skip1 = getBlockSize()
		skip2 = 1 if (getFileVersion() > 2017) else 0
		for j in range(cnt):
			u1, i = getUInt32(self.data, i)
			i += skip2 # skip 00
			u2, i = getUInt16(self.data, i)
			i = self.ReadList4(i, _TYP_UINT32_, name)
			u3, i = getUInt32(self.data, i)
			i += skip1
			l = self.get(name)
			self.delete(name)
			lst.append((u1, u2, u3, l))
		self.set(name, lst, VAL_UINT32)
		return i

	def getListListUInt16sA(self, name, offset, cnt, arraysize):
		return self.__getListListIntsA(name, _TYP_UINT16_A_, offset, cnt, arraysize, u"%03X")

	def getListListSInt16sA(self, name, offset, cnt, arraysize):
		return self.__getListListIntsA(name, _TYP_SINT16_A_, offset, cnt, arraysize, u"%d")

	def getListListUInt32sA(self, name, offset, cnt, arraysize):
		return self.__getListListIntsA(name, _TYP_UINT32_A_, offset, cnt, arraysize, u"%04X")

	def getListListSInt32sA(self, name, offset, cnt, arraysize):
		return self.__getListListIntsA(name, _TYP_SINT32_A_, offset, cnt, arraysize, u"%d")

	def getListListFloats32sA(self, name, offset, cnt, arraysize):
		return self.__getListListFloatsA(name, _TYP_FLOAT32_A_, offset, cnt, arraysize)

	def getListListFloats64sA(self, name, offset, cnt, arraysize):
		return self.__getListListFloatsA(name, _TYP_FLOAT64_A_, offset, cnt, arraysize)

	def getListListFonts(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			tmp = u"%s[%02X][0]" %(name, j)
			i = self.ReadList2(i, _TYP_FONT_, tmp, arraysize)
			lst.append(self.get(tmp))
			self.delete(tmp)
		self.set(name, lst)
		return i

	def getListListXRefs(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip = getBlockSize()
		for j in range(cnt):
			i += skip
			tmp0 = u"%s[%02X][0]" %(name, j)
			i = self.ReadList2(i, _TYP_UINT32_, tmp0)
			tmp1 = u"%s[%02X][1]" %(name, j)
			i = self.ReadCrossRef(i, tmp1)
			i += skip
			lst.append((self.get(tmp0), self.get(tmp1)))
			self.delete(tmp0)
			self.delete(tmp1)
		self.set(name, lst)
		return i

	def getListListChars(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, _TYP_CHAR_, 'tmp')
			lst.append(self.get('tmp'))
			self.delete('tmp')
		self.set(name, lst)
		return i

	def getListResults(self, name, offset, cnt, arraysize):
		lst  = []
		skip = getBlockSize()
		for j in range(cnt):
			r = ResultItem4()
			r.a0, i = getUInt16A(self.data, i, 4)
			r.a1, i = getFloat64_3D(self.data, i)
			r.a2, i = getFloat64_3D(self.data, i)
			i += skip
			lst.append(r)
		self.set(name, list, VAL_UINT16)
		return i

	def __getArrayNodes(self, name, offset, cnt, typ):
		i   = offset
		lst = []
		for j in range(cnt):
			i = self.ReadNodeRef(i, name, j, typ)
			lst.append(self.get(name))
		self.set(name, lst, VAL_REF)
		return i

	def getArrayU32(self, name, offset, cnt):
		lst, i = getUInt32A(self.data, offset, cnt)
		self.set(name, lst, VAL_UINT32)
		return i

	def getArrayRef(self, name, offset, cnt):
		return self.__getArrayNodes(name, offset, cnt, REF_CHILD)

	def getArrayXRef(self, name, offset, cnt):
		return self.__getArrayNodes(name, offset, cnt, REF_CROSS)

	def ReadMetaData_LIST(self, offset, name, typ, arraySize = 1):
		cnt, i = getUInt32(self.data, offset)
		func = getattr(self, TYP_LIST_FUNC[typ])
		if (cnt > 0):
			arr32, i = getUInt32A(self.data, i, 2)
		i = func(name, i, cnt, arraySize)
		return i

	def ReadMetaData_04(self, name, offset, typ, method = getUInt16A):
		cnt, i = getUInt32(self.data, offset)
		func = getattr(self, TYP_04_FUNC[typ])
		if (cnt > 0):
			arr16, i = method(self.data, i, 2)
		i = func(name, i, cnt, 1) # arraysize = 1 => dummy value has to be ignored by any function in TYP_04_FUNC's
		return i

	def ReadMetaData_ARRAY(self, name, offset, typ):
		cnt, i = getUInt32(self.data, offset)
		func = getattr(self, TYP_ARRAY_FUNC[typ])
		if (cnt > 0):
			arr16, i = getUInt16A(self.data, i, 2)
		i = func(name, i, cnt)
		return i

	def ReadMetaData_MAP(self, name, offset, typ):
		cnt, i = getUInt32(self.data, offset)
		func = getattr(self, TYP_MAP_FUNC[typ])
		if (cnt > 0):
			arr32, i = getUInt32A(self.data, i, 2)
		i = func(name, i, cnt)
		return i

	def	getMapU16U16(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt16(self.data, i)
			val, i = getUInt16(self.data, i)
			lst[key] = val
		self.set(name, lst, VAL_UINT16)
		return i

	def	getMapU16XRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt16(self.data, i)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapU32U8(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			val, i = getUInt8(self.data, i)
			lst[key] = val
		self.set(name, lst, VAL_UINT8)
		return i

	def	getMapU32U32(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			val, i = getUInt32(self.data, i)
			lst[key] = val
		self.set(name, lst, VAL_UINT32)
		return i

	def	getMapU32F64(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			val, i = getFloat64(self.data, i)
			lst[key] = val
		self.set(name, lst)
		return i

	def	getMapU32Ref(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapU32XRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapRefRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadChildRef(i, name, j)
			key = self.get(name)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapXRefRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			key = self.get(name)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapXRefXRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			key = self.get(name)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapXRefU2D(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			key = self.get(name)
			val, i = getUInt32A(self.data, i, 2)
			lst[key] = val
		self.set(name, lst, VAL_UINT32)
		return i

	def	getMapXRefF64(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			key = self.get(name)
			val, i = getFloat64(self.data, i)
			lst[key] = val
		self.set(name, lst)
		return i

	def	getMapU32XRefL(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			tmp = u"%s[%04X]" %(name, key)
			i = self.ReadList2(i, _TYP_NODE_X_REF_, tmp)
			lst[key] = self.get(tmp)
			self.delete(tmp)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapXRefXRefL(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			key = self.get(name)
			self.delete(name)
			tmp = u"%s[%s]" %(name, key.index)
			i = self.ReadList2(i, _TYP_NODE_X_REF_, tmp)
			lst[key] = self.get(tmp)
			self.delete(tmp)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapUidU32(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUUID(self.data, i)
			val, i = getUInt32(self.data, i)
			lst[key] = val
		self.set(name, lst, VAL_UINT32)
		return i

	def	getMapUidCRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUUID(self.data, i)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapUidXRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUUID(self.data, i)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapT8Ref(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text8(self.data, i)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapT8XRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text8(self.data, i)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapT83dF64(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text8(self.data, i)
			val, i = getFloat32_3D(self.data, i)
			lst[key] = val
		self.set(name, lst)
		return i

	def	getMapT16Ref(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text16(self.data, i)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapT16XRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text16(self.data, i)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst, VAL_REF)
		return i

	def	getMapT16U32(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text16(self.data, i)
			val, i = getUInt32(self.data, i)
			lst[key] = val
		self.set(name, lst, VAL_UINT32)
		return i

	def	getMapMdlTxnMgr(self, name, offset, cnt):
		lst = []
		i   = offset
		skip = getBlockSize()
		for j in range(cnt):
			val = ModelerTxnMgr()
			val.node, i  = getUInt32(self.data, i)
			val.dcIdx, i = getUInt32(self.data, i)
			i =  self.ReadList2(i, _TYP_MTM_LST_, 'tmp')
			i += skip
			val.lst = self.get('tmp')
			self.delete('tmp')
			lst.append(val)
		self.set(name, lst)
		return i

	def getMapKeyApp1(self, name, offset, cnt):
		lst = {}
		i   = offset
		self.set(name, lst)
		APP_1 = Struct('<Bffffffffffff').unpack_from
		skip  = 50 if (getFileVersion() > 2017) else 49
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			val = APP_1(self.data, i)
			i += skip
			lst[key] = val
		return i

	def getMapKeyMapApp1(self, name, offset, cnt):
		lst = {}
		i   = offset
		self.set(name, lst)
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			u, i = getUInt8(self.data, i)
			i = self.ReadList6(i, _TYP_MAP_KEY_APP_1_, name)
			m = self.get(name)
			lst[key] = (u, m)
		return i

	def getMapTxt16UInt32_7(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text16(self.data, i)
			a, i = getUInt32A(self.data, i, 7)
			lst[key] = a
		self.set(name, lst, VAL_UINT32)
		return i

	def ReadList2(self, offset, typ, name, arraySize = 1):
		i = CheckList(self.data, offset, 0x0002)
		return self.ReadMetaData_LIST(i, name, typ, arraySize)

	def ReadList3(self, offset, typ, name):
		i = CheckList(self.data, offset, 0x0003)
		return self.ReadMetaData_ARRAY(name, i, typ)

	def ReadList4(self, offset, typ, name = 'lst4', method = getUInt16A):
		i = CheckList(self.data, offset, 0x0004)
		return self.ReadMetaData_04(name, i, typ, method)

	def ReadList6(self, offset, typ, name = 'lst6'):
		i = CheckList(self.data, offset, 0x0006)
		return self.ReadMetaData_MAP(name, i, typ)

	def ReadList7(self, offset, typ, name = 'lst7'):
		i = CheckList(self.data, offset, 0x0007)
		return self.ReadMetaData_MAP(name, i, typ)

	def ReadList8(self, offset, typ, name = 'lst8'):
		i = CheckList(self.data, offset, 0x0008)
		return self.ReadMetaData_ARRAY(name, i, typ)

	def Read_Header0(self, typeName = None):
		u32_0, i = getUInt32(self.data, 0)
		u16_0, i = getUInt16(self.data, i)
		i += getBlockSize()

		hdr = Header0(u32_0, u16_0)
		self.set('hdr', hdr, None)
		if (typeName is not None): self.typeName = typeName

		return i

	def updateTypeId(self, uid):
		self.uid = UUID(uid)
		self.typeName = '%08X' %(self.uid.time_low)

	def getUnitOffset(self):
		unitRef = self.get('unit')
		if (unitRef):
			numerators = unitRef.get('numerators')
			if (numerators):
				offset = numerators[0].get('UnitOffset')
				if (offset is not None):
					return offset
		return 0.0

	def getUnitFactors(self, units):
		factor = 1.0
		for j in range(len(units)):
			unit = units[j]
			magniture  = unit.get('magnitude')
			unitFactor = unit.get('UnitFactor')
			if (unitFactor is None):
				logError(u"ERROR> (%04X) - %s has no UnitFactor defined!", unit.index, unit.typeName)
			factor *= magniture * unitFactor
		return factor

	def getUnitFactor(self):
		factor = 1.0
		unitRef = self.get('unit')
		if (unitRef):
			numerators = self.getUnitFactors(unitRef.get('numerators'))
			denominators = self.getUnitFactors(unitRef.get('denominators'))
			factor = numerators / denominators

			derivedRef = unitRef.get('derived')
			if (derivedRef):
				numerators = self.getUnitFactors(derivedRef.get('numerators'))
				denominators = self.getUnitFactors(derivedRef.get('denominators'))
				factor = factor * numerators / denominators
		return factor

	def getUnitFormula(self, units): # return unicode
		formula = u''
		sep     = ''

		lastUnit     = 'XXXXX' # choose any unit that is not defined!
		unitExponent = 1       # by default (e.g.): m^1 => m

		for j in range(len(units)):
			unit = units[j]
			subformula = unit.get('Unit')

			if (len(subformula) > 0):
				factor = log10(unit.get('magnitude'))
				if   (factor ==  18): factor = u'E'    # Exa
				elif (factor ==  15): factor = u'P'    # Peta
				elif (factor ==  12): factor = u'T'    # Tera
				elif (factor ==   9): factor = u'G'    # Giga
				elif (factor ==   6): factor = u'M'    # Mega
				elif (factor ==   3): factor = u'k'    # Kilo
				elif (factor ==   2): factor = u'h'    # Hecto
				elif (factor ==   1): factor = u'da'   # Deca
				elif (factor ==   0): factor = u''
				elif (factor ==  -1): factor = u'd'    # Deci
				elif (factor ==  -2): factor = u'c'    # Centi
				elif (factor ==  -3): factor = u'm'    # Milli
				elif (factor ==  -6): factor = u'\xB5' # Micro
				elif (factor ==  -9): factor = u'n'    # Nano
				elif (factor == -12): factor = u'p'    # Pico
				elif (factor == -15): factor = u'f'    # Femto
				elif (factor == -18): factor = u'a'    # Atto
				subformula = "%s%s" %(factor, subformula)
				if (subformula == lastUnit):
					unitExponent += 1
				else:
					if(lastUnit != 'XXXXX'):
						if (unitExponent > 1):
							formula = u'%s%s%s^%d' %(formula, sep, lastUnit, unitExponent)
							unitExponent = 1
						else:
							formula = u'%s%s%s' %(formula, sep, lastUnit)
						sep =' '
					lastUnit = subformula
		if (len(units) > 0):
			if (unitExponent > 1):
				formula = u'%s%s%s^%d' %(formula, sep, subformula, unitExponent)
			else:
				formula = u'%s%s%s' %(formula, sep, subformula)
		return formula

	def getUnitName(self): # return unicode
		'''
		TODO:
		Derived units are not supported in FreeCAD.
		Add a new derived unit! But how?
		Meanwhile the derived units are ignored!
		'''
		unit  = self.get('unit')
		unitName = u''
		if (unit):
			unitName     = self.getUnitFormula(unit.get('numerators'))
			denominators = self.getUnitFormula(unit.get('denominators'))
			if (len(denominators) > 0):
				unitName += '/' + denominators

		return unitName

	def getDerivedUnitName(self):
		unit = self.get('unit')
		if (unit):
			derived = unit.get('derived')
			if (derived):
				unitName     = self.getUnitFormula(derived.get('numerators'))
				denominators = self.getUnitFormula(derived.get('denominators'))
				if (len(denominators) > 0):
					unitName += '/' + denominators

				return unitName
		return None

class SecNodeRef(object):

	def __init__(self, m, refType, name):
		self.index    = (m & 0x7FFFFFFF)
		self.mask     = (m & 0x80000000) >> 31
		self.type     = refType
		self.number   = 0
		self._data    = None
		self.analysed = False
		self.attrName = name

	@property
	def data(self):
		return self._data

	@data.setter
	def data(self, data):
		if (data): assert isinstance(data, SecNode), 'Data reference is not a AbstractNode (%s)!' %(data.__class__.__name__)
		self._data = data

	@property
	def typeName(self):
		if (self._data): return self._data.typeName
		return None

	@property
	def handled(self):
		if (self._data): return self._data.handled
		return False
	@handled.setter
	def handled(self, handled):
		if (self._data): self._data.handled = handled

	@property
	def valid(self):
		if (self._data): return self._data.valid
		return False
	@valid.setter
	def valid(self, valid):
		if (self._data): self._data.valid = valid

	@property
	def node(self):
		if (self._data): return self._data.node
		return None

	@property
	def name(self):
		if (self._data): return self._data.getName()
		return None

	def get(self, name):
		if (self._data): return self._data.get(name)
		return None

	def set(self, name, value):
		if (self._data): self._data.set(name, value, None)

	@property
	def geometry(self):
		if (self._data): return self._data.geometry
		return None

	@property
	def sketchIndex(self):
		if (self._data): return self._data.sketchIndex
		return None

	@property
	def sketchPos(self):
		if (self._data): return self._data.sketchPos
		return None

	@property
	def segment(self):
		if (self._data): return self._data.segment
		return None

	def setGeometry(self, geometry, index = -1):
		if (self._data):
			self._data.geometry = geometry
			self._data.sketchIndex = index

	def getValue(self):
		node = self.node
		if (node): return node.getValue()
		return None

	def getNominalValue(self):
		value = self.getValue()
		if (value): return value.getNominalValue()
		return None

	def getSubTypeName(self):
		node = self.node
		if (node): return node.getSubTypeName()
		return None

	def getParticipants(self):
		node = self.node
		if (node): return node.getParticipants()
		return None

	def getUnitName(self): # return unicode
		if (self._data): return self._data.getUnitName()
		return u''

	def getUnitOffset(self):
		if (self._data): return self._data.getUnitOffset()
		return 0.0

	def getUnitFactor(self):
		if (self._data): return self._data.getUnitFactor()
		return 1.0

	def __str__(self): # return unicode
		return u'[%04X,%X]' %(self.index, self.mask)

	def __repr__(self):
		if (self.node is None): return self.__str__()
		return self.node.getRefText()

def getParameterValue(parameter, formula = None):
	prm   = parameter
	value = None
	if (isinstance(prm, SecNodeRef)):
		prm = prm.node
	if (isinstance(prm, ParameterNode)):
		prm = prm.getValue()
	if (isinstance(prm, AbstractValue)):
		if (formula is None):
			return prm.getNominalValue()
		return formula(prm)

	if (formula):
		return formula(prm)
	return prm

def getExpression(parameter):
	alias = None
	if (hasattr(parameter, 'get')):
		alias = parameter.get('alias')
	return alias

def setParameter(geometry, attribute, parameter, formula = None, factor=1.0):
	aliases = []
	if (type(parameter) in [list, tuple]):
		value   = 0
		for p in parameter:
			value += getParameterValue(p, formula)
			alias = getExpression(p)
			if (alias):
				aliases.append(alias)
		if (len(aliases) > 0):
			expression = "+".join(aliases)
		else:
			expression = None
	else:
		value = getParameterValue(parameter, formula)
		expression = getExpression(parameter)

	try:
		setattr(geometry, attribute, value * factor)
	except:
		pass
	if (expression is not None):
		if (isEqual1D(factor, 1.0)):
			geometry.setExpression(attribute, expression)
		else:
			geometry.setExpression(attribute, "(%s) * %s" %(expression, factor))
	return value
