# -*- coding: utf-8 -*-

'''
importerSegNode.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerClasses import AbstractData, Header0, Angle, GraphicsFont, Lightning, ModelerTxnMgr
from importerUtils   import *
from math            import log10, pi
import numpy as np

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

def isList(data, code):
	return ((data[-1] == 0x3000) and (data[-2] == code))

F_2010  = Struct('<fL').unpack_from
APP_4_A = Struct('<LHLff').unpack_from
APP_4_B = Struct('<ffHB').unpack_from
APP_5_A = Struct('<ddL').unpack_from
APP_5_B = Struct('<BBH').unpack_from

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

_TYP_LIST_UINT16_A_         = 0x8001
_TYP_LIST_SINT16_A_         = 0x8002
_TYP_LIST_UINT32_A_         = 0x8003
_TYP_LIST_SINT32_A_         = 0x8004
_TYP_LIST_FLOAT32_A_        = 0x8005
_TYP_LIST_FLOAT64_A_        = 0x8006
_TYP_LIST_FONT_             = 0x8007
_TYP_LIST_X_REF_            = 0x8008

_TYP_MAP_U32_U32_           = 0x7001
_TYP_MAP_KEY_REF_           = 0x7002
_TYP_MAP_KEY_X_REF_         = 0x7003
_TYP_MAP_REF_REF_           = 0x7004
_TYP_MAP_TEXT8_REF_         = 0x7005
_TYP_MAP_TEXT8_X_REF_       = 0x7006
_TYP_MAP_TEXT16_REF_        = 0x7007
_TYP_MAP_TEXT16_X_REF_      = 0x7008
_TYP_MAP_X_REF_REF_         = 0x7009
_TYP_MAP_X_REF_FLOAT64_     = 0x700A
_TYP_MAP_X_REF_2D_UINT32_   = 0x700B
_TYP_MAP_X_REF_X_REF_       = 0x700C
_TYP_MAP_X_REF_LIST2_XREF_  = 0x700D
_TYP_MAP_UUID_UINT32_       = 0x700E
_TYP_MAP_UUID_X_REF         = 0x700F
_TYP_MAP_U16_U16_           = 0x7010
_TYP_MAP_KEY_APP_1_         = 0x7011
_TYP_MAP_KEY_MAP_APP_1_     = 0x7012

_TYP_MAP_MDL_TXN_MGR_1_     = 0x6001
_TYP_MAP_MDL_TXN_MGR_2_     = 0x6002

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
	_TYP_LIST_UINT16_A_:         'getListListUInt16sA',
	_TYP_LIST_SINT16_A_:         'getListListSInt16sA',
	_TYP_LIST_UINT32_A_:         'getListListUInt32sA',
	_TYP_LIST_SINT32_A_:         'getListListSInt32sA',
	_TYP_LIST_FLOAT32_A_:        'getListListFloats32sA',
	_TYP_LIST_FLOAT64_A_:        'getListListFloats64sA',
	_TYP_LIST_FONT_:             'getListListFonts',
	_TYP_LIST_X_REF_:            'getListListXRefs',
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
	_TYP_MAP_U32_U32_:          'getMapU32U32',
	_TYP_MAP_KEY_REF_:          'getMapU32Ref',
	_TYP_MAP_KEY_X_REF_:        'getMapU32XRef',
	_TYP_MAP_REF_REF_:          'getMapRefRef',
	_TYP_MAP_X_REF_REF_:        'getMapXRefRef',
	_TYP_MAP_X_REF_FLOAT64_:    'getMapXRefF64',
	_TYP_MAP_X_REF_X_REF_:      'getMapXRefXRef',
	_TYP_MAP_X_REF_2D_UINT32_:  'getMapXRefU2D',
	_TYP_MAP_X_REF_LIST2_XREF_: 'getMapXRefXRefL',
	_TYP_MAP_UUID_UINT32_:      'getMapUidU32',
	_TYP_MAP_UUID_X_REF:        'getMapUidXRef',
	_TYP_MAP_TEXT8_REF_:        'getMapT8Ref',
	_TYP_MAP_TEXT8_X_REF_:      'getMapT8XRef',
	_TYP_MAP_TEXT16_REF_:       'getMapT16Ref',
	_TYP_MAP_TEXT16_X_REF_:     'getMapT16XRef',
	_TYP_MAP_MDL_TXN_MGR_1_:    'getMapMdlTxnMgr1',
	_TYP_MAP_MDL_TXN_MGR_2_:    'getMapMdlTxnMgr2',
	_TYP_MAP_KEY_APP_1_:        'getMapKeyApp1',
	_TYP_MAP_KEY_MAP_APP_1_:    'getMapKeyMapApp1',
}

class SecNode(AbstractData):

	def __init__(self):
		AbstractData.__init__(self)

	def ReadUInt8(self, offset, name):
		x, i = getUInt8(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%02X' %(name, x)
		return i

	def ReadUInt8A(self, offset, n, name):
		x, i = getUInt8A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=[%s]' %(name, ",".join(["%02X" % h for h in x]))
		return i

	def ReadUInt16(self, offset, name):
		x, i = getUInt16(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%04X' %(name, x)
		return i

	def ReadUInt16A(self, offset, n, name):
		x, i = getUInt16A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=[%s]' %(name, ",".join(["%04X" % h for h in x]))
		return i

	def ReadSInt16(self, offset, name):
		x, i = getSInt16(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%d' %(name, x)
		return i

	def ReadSInt16A(self, offset, n, name):
		x, i = getSInt16A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=[%s]' %(name, ",".join(["%d" % d for d in x]))
		return i

	def ReadUInt32(self, offset, name):
		x, i = getUInt32(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%06X' %(name, x)
		return i

	def ReadUInt32A(self, offset, n, name):
		x, i = getUInt32A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=[%s]' %(name, ",".join(["%06X" % h for h in x]))
		return i

	def ReadSInt32(self, offset, name):
		x, i = getSInt32(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%d' %(name, x)
		return i

	def ReadSInt32A(self, offset, n, name):
		x, i = getSInt32A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=[%s]' %(name, ",".join(["%d" % d for d in x]))
		return i

	def ReadFloat32(self, offset, name):
		x, i = getFloat32(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%g' %(name, x)
		return i

	def ReadFloat32A(self, offset, n, name):
		x, i = getFloat32A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=(%s)' %(name, ",".join(["%g" % g for g in x]))
		return i

	def ReadFloat32_2D(self, offset, name):
		x, i = getFloat32_2D(self.data, offset)
		self.set(name, x)
		self.content += ' %s=(%g,%g)' %(name, x[0], x[1])
		return i

	def ReadFloat32_3D(self, offset, name):
		x, i = getFloat32_3D(self.data, offset)
		self.set(name, x)
		self.content += ' %s=(%g,%g,%g)' %(name, x[0], x[1], x[1])
		return i

	def ReadFloat64(self, offset, name):
		x, i = getFloat64(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%g' %(name, x)
		return i

	def ReadFloat64A(self, offset, n, name):
		x, i = getFloat64A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=(%s)' %(name, ",".join(["%g" % g for g in x]))
		return i

	def ReadFloat64_2D(self, offset, name):
		x, i = getFloat64_2D(self.data, offset)
		self.set(name, x)
		self.content += ' %s=(%g,%g)' %(name, x[0], x[1])
		return i

	def ReadFloat64_3D(self, offset, name):
		x, i = getFloat64_3D(self.data, offset)
		self.set(name, x)
		self.content += ' %s=(%g,%g,%g)' %(name, x[0], x[1], x[1])
		return i

	def ReadVec3D(self, offset, name, scale = 1.0):
		p, i = getFloat64_3D(self.data, offset)
		v = VEC(p[0], p[1], p[2]) * scale
		self.set(name, v)
		self.content += ' %s=%s' %(name, v)
		return i

	def ReadUUID(self, offset, name):
		x, i = getUUID(self.data, offset)
		self.set(name, x)
		self.content += ' %s={%s}' %(name, x)
		return i

	def ReadColorRGBA(self, offset, name):
		x, i = getColorRGBA(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%s' %(name, x)
		i = self.reader.skipBlockSize(i)
		return i

	def ReadBoolean(self, offset, name):
		x, i = getBoolean(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%s' %(name, x)
		return i

	def ReadEnum16(self, offset, name, enum):
		index, i = getUInt16(self.data, offset)
		e = enum[index]
		if (name == 'name'):
			self.name = e
		else:
			self.set(name, e)
			self.content += ' %s=%s' %(name, e)
		return i

	def ReadAngle(self, offset, name):
		x, i = getFloat64(self.data, offset)
		x = Angle(x, pi/180.0, u'\xb0')
		self.set(name, x)
		self.content += ' %s=%s' %(name, x)
		return i

	def ReadLen32Text8(self, offset, name = None):
		x, i = getLen32Text8(self.data, offset)
		if (name):
			self.set(name, x)
			self.content += ' %s=\'%s\'' %(name, x)
		else:
			self.name = x
		return i

	def ReadText8(self, offset, l, name = None):
		x, i = getText8(self.data, offset, l)
		if (name):
			self.set(name, x)
			self.content += ' %s=\'%s\'' %(name, x)
		else:
			self.name = x
		return i

	def ReadLen32Text16(self, offset, name = None):
		x, i = getLen32Text16(self.data, offset)
		if (name):
			self.set(name, x)
			self.content += ' %s=\'%s\'' %(name, x)
		else:
			self.name = x
		return i

	def ReadNodeRef(self, offset, name, number, type):
		m, i = getUInt32(self.data, offset)
		ref = SecNodeRef(m, type, name)

		self.set(name, None)

		if (ref.index > 0):
			ref.number = number
			if (ref.index == self.index):
				logError(u"ERROR> Found self-ref '%s' for (%04X): %s", name, self.index, self.typeName)
			else:
				self.references.append(ref)
		else:
			ref = None
		self.set(name, ref)
		return i

	def ReadChildRef(self, offset, name = 'ref', number = None):
		return self.ReadNodeRef(offset, name, number , SecNodeRef.TYPE_CHILD)

	def ReadCrossRef(self, offset, name = 'ref', number = None):
		return self.ReadNodeRef(offset, name, number, SecNodeRef.TYPE_CROSS)

	def ReadParentRef(self, offset):
		return self.ReadNodeRef(offset, 'parent', None, SecNodeRef.TYPE_CROSS)

	def __getListStrings(self, name, offset, cnt, mtd):
		lst = []
		i   = offset
		for j in range(cnt):
			t, i = mtd(self.data, i)
			lst.append(t)
		self.content += u" %s=[%s]" %(name, ",".join([u"'%s'" %(t) for t in lst ]))
		self.set(name, lst)
		return i

	def __getList2Nums(self, name, offset, cnt, s, w, fmt, skipLen = True):
		if (skipLen):
			lst = Struct('<' + s * cnt).unpack_from(self.data, offset)
			i   = offset + cnt * w
		else:
			val = Struct('<' + (s+'L')*cnt).unpack_from(self.data, offset)
			i   = offset + (w+4)*cnt # 4Bytes float 4Byte blocklen
			lst = list(val)[0::2]
		lst = list(lst)
		if (len(lst) > 100):
			self.content += u" %s=[%s,...]" %(name, u",".join([fmt %(n) for n in lst]))
		else:
			self.content += u" %s=[%s]" %(name, u",".join([fmt %(n) for n in lst]))

		self.set(name, lst)
		return i

	def __getList2NumsA(self, name, offset, cnt, arraysize, s, w, fmt, skipLen = True):
		if (skipLen):
			val = Struct('<' + s*arraysize*cnt).unpack_from(self.data, offset)
			val = np.reshape(val, (-1, arraysize))
			i   = offset + (w * arraysize) * cnt
		else:
			val = Struct('<' + (s*arraysize+'L')*cnt).unpack_from(self.data, offset)
			val = np.reshape([n for i, n in enumerate(val) if (i % (arraysize + 1)) != arraysize], (-1, arraysize))
			i   = offset + (w * arraysize + 4) * cnt # w + 4Bytes for blocklen
		lst = val.tolist()

		if (arraysize > 1):
			if (len(lst) > 100):
				self.content += u" %s=[%s,...]" %(name, u",".join([u",".join([u"[%s]" %(u",".join([fmt %(n) for n in a]))]) for a in lst[:100]]))
			else:
				self.content += u" %s=[%s]" %(name, u",".join([u",".join([u"[%s]" %(u",".join([fmt %(n) for n in a]))]) for a in lst] ) )
		else:
			if (len(lst) > 100):
				self.content += u" %s=[%s,...]" %(name, u",".join([fmt %(n) for n in lst[:100]]))
			else:
				self.content += u" %s=[%s]" %(name, u",".join([fmt %(n) for n in lst]))
		self.set(name, lst)
		return i

	def __getListListIntsA(self, name, typ, offset, cnt, arraysize, fmt):
		lst = []
		i   = offset
		c   = self.content
		for j in range(cnt):
			i = self.ReadList2(i, typ, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')
		if (arraysize == 1):
			self.content = c + u" %s={%s}" %(name, u",".join([u"(%s)" %(u",".join([fmt %(x) for x in l])) for l in lst]))
		else:
			self.content = c + u" %s={%s}" %(name, u",".join([u"(%s)" %(u",".join([u"[%s]" %(FloatArr2Str(x)) for x in l])) for l in lst]))
		self.set(name, lst)
		return i

	def __getListListFloatsA(self, name, typ, offset, cnt, arraysize):
		lst = []
		i   = offset
		c   = self.content
		for j in range(cnt):
			i = self.ReadList2(i, typ, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')
		if (arraysize == 1):
			self.content = c + u" %s={%s}" %(name, u",".join([u"(%s)" %(u",".join([u"%g" %(x) for x in l])) for l in lst]))
		else:
			self.content = c + u" %s={%s}" %(name, u",".join([u"(%s)" %(u",".join([u"[%s]" %(FloatArr2Str(x)) for x in l])) for l in lst]))
		self.set(name, lst)
		return i

	def getListChars(self, name, offset, cnt, arraysize):
		try:
			t, i = getText8(self.data, offset, cnt)
			self.set(name, t)
			self.content += u" %s='%s'" %(name, t)
			return i
		except:
			t, i = getUInt8A(self.data, offset, cnt)
			self.set(name, t)
			self.content += u" %s=%s" %(name, IntArr2Str(t, 2))
			return offset+cnt

	def getList2Childs(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadChildRef(i, name, j)
			lst.append(self.get(name))
		self.set(name, lst)
		return i

	def getListXRefs(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			lst.append(self.get(name))
		self.set(name, lst)
		return i

	def getListString8s(self, name, offset, cnt, arraysize):
		return  self.__getListStrings(name, offset, cnt, getLen32Text8)

	def getListString16s(self, name, offset, cnt, arraysize):
		return  self.__getListStrings(name, offset, cnt, getLen32Text16)

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
		return self.__getList2Nums(name, offset, cnt, 'f', 4, u"%g", (getFileVersion() > 2010))

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
		lst = []
		i   = offset
		for j in range(cnt):
			val = GraphicsFont()
			a   = Struct('<LHHHHBBHH').unpack_from(self.data, i)
			val.number = a[0]
			val.ukn1   = a[1:5]
			val.ukn2   = a[5:7]
			val.ukn3   = a[7:]
			i += 18
			val.name, i   = getLen32Text16(self.data, i)
			a = Struct('<ffBBB').unpack_from(self.data, i)
			val.ukn4 = a[0:2]
			val.ukn5 = a[2:]
			i += 11
			lst.append(val)
		self.content += u" %s={%s}" %(name, u",".join([u"(%s)" %(l) for l in lst]))
		self.set(name, lst)
		return i

	def getListLightnings(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		if (getFileVersion() > 2010):
			fmt = '<Hffffffffffffddddddfffffff'
			for j in range(cnt):
				vals = Struct(fmt).unpack_from(self.data, i)
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
			fmt = '<HffffLffffLffffLddddddfffffffL'
			for j in range(cnt):
				vals = Struct(fmt).unpack_from(self.data, i)
				i += 142
				val = Lightning()
				val.n1 = vals[0]
				val.c1 = Color(vals[1], vals[2], vals[3], vals[4])
				val.c2 = Color(vals[6], vals[7], vals[8], vals[9])
				val.c3 = Color(vals[11], vals[12], vals[13], vals[14])
				val.a1 = vals[16:22]
				val.a2 = vals[22:-1]
				lst.append(val)
		self.content += u" %s={%s}" %(name, u",".join([u"(%s)" %(l) for l in lst]))
		self.set(name, lst)
		return i

	def getListApp1(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		skip = (getFileVersion() < 2011)
		for j in range(cnt):
			if (skip):
				a = Struct('<ddLLBBBBL').unpack_from(self.data, i)
				val = a[0:3] + a[4:8]
				i += 32
			else:
				val = Struct('<ddLBBBB').unpack_from(self.data, i)
				i += 24
			lst.append(val)
		self.content += u" %s={%s}" %(name, u",".join([u"(%g,%g,%06X,%02X,%02X,%02X,%02X)" %(a[0], a[1], a[2], a[3], a[4], a[5], a[6]) for a in lst]))
		self.set(name, lst)
		return i

	def getListApp2(self, name, offset, cnt, arraysize):
		lst = []
		i   = offset
		skip = 4 if (getFileVersion() < 2011) else 0
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
			self.content += u"\n\t%d,'%s','%s',[%s],[%s],[%s],%04X,%s,%d,%X" %(n1, t1, t2, IntArr2Str(l1, 4), IntArr2Str(a1, 2), FloatArr2Str(l2), n2, c1, n3, n4)
			lst.append((n1, t1, t2, l1, a1, l2, l3, n2, c1, n3, n4))
		self.set(name, lst)
		return i

	def getListApp3(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		c    = self.content
		skip = 4 if (getFileVersion() < 2011) else 0
		for j in range(cnt):
			n1, i = getUInt32(self.data, i)
			t1, i = getLen32Text16(self.data, i)
			n2, i = getUInt32(self.data, i)
			c = self.content
			i = self.ReadList2(i, _TYP_FLOAT64_, 'tmp')
			l1 = self.get('tmp')
			self.delete('_tmp')
			n3, i = getUInt8(self.data, i)
			i += skip
			lst.append((n1, t1, n2, l1, n3))
		self.content = c + u" %s={%s}" %(name, u",".join([u"(%d,'%s',%06X,%s,%02X)" %(a[0], a[1], a[2], FloatArr2Str(a[3]), a[4]) for a in lst]))
		self.set(name, lst)
		return i

	def getListApp4(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip = 8 if (getFileVersion() < 2011) else 0
		for j in range(cnt):
			n1, n2, n3, f1, f2 = APP_4_A(self.data, i)
			i += 18
			t1, i = getLen32Text16(self.data, i)
			f3, f4, n4, n5 = APP_4_B(self.data, i)
			i += 11
			i += skip
			lst.append((n1, n2,  n3,  f1, f2,  t1,  f3, f4, n4, n5))
		self.content += u" %s={%s}" %(name, u",".join([u"(%d, %d, %04X, %g, %g, '%s', %g, %g, %03X, %02X)" %(a[0], a[1], a[2], a[3], a[4], a[5],  a[6], a[7], a[8], a[9]) for a in lst]))
		self.set(name, lst)
		return i

	def getListApp5(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip = 4 if (getFileVersion() < 2011) else 0
		for j in range(cnt):
			f1, f2, n1 = APP_5_A(self.data, i)
			i += 20
			i += skip
			n2, n3, n4 = APP_5_B(self.data, i)
			i += 4
			i += skip
			lst.append((f1, f2, n1, n2,  n3,  n4))
		self.content += u" %s={%s}" %(name, u",".join([u"(%g, %g, %04X, %02X, %02X, %03X)" %(a[0], a[1], a[2], a[3], a[4], a[5])for a in lst]))
		self.set(name, lst)
		return i

	def getListResult1(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		c    = self.content
		skip = 4 if (getFileVersion() < 2011) else 0
		for j in range(cnt):
			u1, i = getUInt32(self.data, i)
			i = self.ReadList4(i, _TYP_UINT32_, name)
			l1 = self.get(name)
			u2, i = getUInt32(self.data, i)
			u3, i = getUInt32(self.data, i)
			i = self.ReadList4(i, _TYP_UINT32_, name)
			l2 = self.get(name)
			a1, i = getFloat64_3D(self.data, i)
			a2, i = getFloat64_3D(self.data, i)
			i += skip
			lst.append((u1, l1, u2, u3, l2, a1, a2))
		self.content = u"%s %s={%s}" %(c, name, u",".join([u"(%04X,[%s],%04X,%04X,[%s],(%s)-(%s))" %(a[0], IntArr2Str(a[1], 4), a[2], a[3], IntArr2Str(a[4], 4), FloatArr2Str(a[5]), FloatArr2Str(a[6])) for a in lst]))
		self.set(name, lst)
		return i

	def getListResult2(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip = 4 if (getFileVersion() < 2011) else 0
		for j in range(cnt):
			d, i = getUInt32A(self.data, i, 2)
			i += skip
			lst.append(d)
		self.content += u" %s={%s}" %(name, u",".join([u"[%04X,%04X]" %(a[0], a[1]) for a in lst]))
		self.set(name, lst)
		return i

	def getListResult3(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		RESULT_3 = Struct('<LHBBdddddd').unpack_from
		skip = 4 if (getFileVersion() < 2011) else 0
		for j in range(cnt):
			d = RESULT_3(self.data, i)
			i += 56 + skip
			lst.append(d)
		self.content += u" %s={%s}" %(name, u",".join([u"(%04X,%03X,%02X,%02X,(%g,%g,%g)-(%g,%g,%g))" %(a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9]) for a in lst]))
		self.set(name, lst)
		return i

	def getListResult4(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip1 = 4 if (getFileVersion() < 2011) else 0
		skip2 = 1 if (getFileVersion() > 2017) else 0
		c    = self.content
		for j in range(cnt):
			u1, i = getUInt32(self.data, i)
			i += skip2 # skip 00
			u2, i = getUInt16(self.data, i)
			i = self.ReadList4(i, _TYP_UINT32_, name)
			u3, i = getUInt32(self.data, i)
			i += skip1
			l = self.get(name)
			lst.append((u1, u2, u3, l))
		self.content = u"%s %s={%s}" %(c, name, u",".join([u"(%04X,%03X,%04X,%s)" %(a[0], a[1], a[2], a[3]) for a in lst]))
		self.set(name, lst)
		return i

	def getListResult5(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip1 = 4 if (getFileVersion() < 2011) else 0
		c    = self.content
		for j in range(cnt):
			u, i = getUInt32(self.data, i)
			i = self.ReadList4(i, _TYP_UINT32_, name)
			i += skip1
			l = self.get(name)
			lst.append((u, l))
		self.content = u"%s %s={%s}" %(c, name, u",".join([u"(%04X,[%s])" %(a[0], IntArr2Str(a[1], 3)) for a in lst]))
		self.set(name, lst)
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
		c   = self.content
		for j in range(cnt):
			tmp = u"%s[%02X][0]" %(name, j)
			i = self.ReadList2(i, _TYP_FONT_, tmp, arraysize)
			lst.append(self.get(tmp))
			self.delete(tmp)
		self.content = c + u" %s=(%s)" %(name, u",".join([u"(%s)" %(l) for l in lst]))
		self.set(name, lst)
		return i

	def getListListXRefs(self, name, offset, cnt, arraysize):
		lst  = []
		i    = offset
		skip = 4 if (getFileVersion() < 2011) else 0
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

	def getListResults(self, name, offset, cnt, arraysize):
		lst  = []
		skip = 4 if (getFileVersion() < 2011) else 0
		for j in range(cnt):
			r = ResultItem4()
			r.a0, i = getUInt16A(self.data, i, 4)
			r.a1, i = getFloat64_3D(self.data, i)
			r.a2, i = getFloat64_3D(self.data, i)
			i += skip
			lst.append(r)
		self.set(name, list)
		self.content += u" %s={%s}" %(name, u",".join([u"(%s)" %(r) for r in lst]))
		return i

	def __getArrayNodes(self, name, offset, cnt, typ):
		i   = offset
		lst = []
		for j in range(cnt):
			i = self.ReadNodeRef(i, name, j, typ)
			lst.append(self.get(name))
		self.set(name, lst)
		return i

	def getArrayU32(self, name, offset, cnt):
		lst, i = getUInt32A(self.data, offset, cnt)
		self.content += u" %s=[%s]" %(name, u",".join([u"%04X" %(n) for n in lst]))
		self.set(name, lst)
		return i

	def getArrayRef(self, name, offset, cnt):
		return self.__getArrayNodes(name, offset, cnt, SecNodeRef.TYPE_CHILD)

	def getArrayXRef(self, name, offset, cnt):
		return self.__getArrayNodes(name, offset, cnt, SecNodeRef.TYPE_CROSS)

	def ReadMetaData_LIST(self, offset, name, typ, arraySize = 1):
		cnt, i = getUInt32(self.data, offset)
		func = getattr(self, TYP_LIST_FUNC[typ])
		if (cnt > 0):
			arr32, i = getUInt32A(self.data, i, 2)
		return func(name, i, cnt, arraySize)

	def ReadMetaData_04(self, name, offset, typ, arraySize = 1):
		cnt, i = getUInt32(self.data, offset)
		func = getattr(self, TYP_04_FUNC[typ])
		if (cnt > 0):
			arr16, i = getUInt16A(self.data, i, 2)
		return func(name, i, cnt, arraySize)

	def ReadMetaData_ARRAY(self, name, offset, typ):
		cnt, i = getUInt32(self.data, offset)
		func = getattr(self, TYP_ARRAY_FUNC[typ])
		if (cnt > 0):
			arr16, i = getUInt16A(self.data, i, 2)
		return func(name, i, cnt)

	def	getMapU16U16(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt16(self.data, i)
			val, i = getUInt16(self.data, i)
			lst[key] = val
		self.content += u" %s=[%s]" % (name, u",".join([u"[%03X:%03X]" %(key, lst[key]) for key in lst]))
		self.set(name, lst)
		return i

	def	getMapU32U32(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			val, i = getUInt32(self.data, i)
			lst[key] = val
		self.content += u" %s=[%s]" % (name, u",".join([u"[%04X:%04X]" %(key, lst[key]) for key in lst]))
		self.set(name, lst)
		return i

	def	getMapU32Ref(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst)
		return i

	def	getMapU32XRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst)
		return i

	def	getMapRefRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadChildRef(i, name, j)
			key = self.get(name)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst)
		return i

	def	getMapXRefRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			key = self.get(name)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst)
		return i

	def	getMapXRefXRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			key = self.get(name)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst)
		return i

	def	getMapXRefU2D(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			key = self.get(name)
			val, i = getUInt32A(self.data, i, 2)
			lst[key] = val
		self.content += u" %s=[%s]" % (name, u",".join([u"[%s:(%s)]" %(key, IntArr2Str(lst[key], 4)) for key in lst]))
		self.set(name, lst)
		return i

	def	getMapXRefF64(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			key = self.get(name)
			val, i = getFloat64(self.data, i)
			lst[key] = val
		self.content += u" %s=[%s]" % (name, u",".join([u"[%s: %g]" %(key, lst[key]) for key in lst]))
		self.set(name, lst)
		return i

	def	getMapXRefXRefL(self, name, offset, cnt):
		lst = {}
		i   = offset
		c = self.content
		self.content = u""
		for j in range(cnt):
			i = self.ReadCrossRef(i, name, j)
			key = self.get(name)
			tmp = u"%s[%s]" %(name, key.index)
			i = self.ReadList2(i, _TYP_NODE_X_REF_, tmp)
			lst[key] = self.get(tmp)
			self.delete(tmp)
		self.content = c + u" %s=[%s]" % (name, u",".join([u"[%s: (%s)]" %(getIndex(key), u"),(".join([u"%s" %(getIndex(h)) for h in lst[key]])) for key in lst]))
		self.set(name, lst)
		return i

	def	getMapUidU32(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUUID(self.data, i)
			val, i = getUInt32(self.data, i)
			lst[key] = val
		self.content += u" %s=[%s]" % (name, u" %s={%s}" %(name, u",".join([u"[{%s}:%04X]" %(key, lst[key]) for key in lst])))
		self.set(name, lst)
		return i

	def	getMapUidXRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getUUID(self.data, i)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst)
		return i

	def	getMapT8Ref(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text8(self.data, i)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst)
		return i

	def	getMapT8XRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text8(self.data, i)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst)
		return i

	def	getMapT16Ref(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text16(self.data, i)
			i = self.ReadChildRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst)
		return i

	def	getMapT16XRef(self, name, offset, cnt):
		lst = {}
		i   = offset
		for j in range(cnt):
			key, i = getLen32Text16(self.data, i)
			i = self.ReadCrossRef(i, name, key)
			lst[key] = self.get(name)
		self.set(name, lst)
		return i

	def	getMapMdlTxnMgr1(self, name, offset, cnt):
		lst = {}
		i   = offset
		c = self.content
		self.content = u""
		skip1 = 4 if (getFileVersion() < 2011) else 0
		skip2 = 1 if (getFileVersion() > 2018) else 0
		for j in range(cnt):
			key = len(lst)
			tmp = u"%s[%02x]" %(name, key)
			val = ModelerTxnMgr()
			i = self.ReadCrossRef(i, tmp, j)
			val.ref_1 = self.get(tmp)
			val.u32_0, i = getUInt32(self.data, i)

			i =  self.ReadList2(i, _TYP_UINT16_A_, tmp, 2)
			val.lst = self.get(tmp)
			val.u8_0, i  = getUInt8(self.data, i)
			i += skip1 + skip2
			val.u32_1, i  = getUInt32(self.data, i)
			val.u8_1, i   = getUInt8(self.data, i)
			val.s32_0, i  = getSInt32(self.data, i)
			i += skip1 + skip1 + skip2
			self.delete(tmp)
		self.content = c + u" %s=[%s]" % (name, u",".join([u"[\'%s\': (%s)]" %(key, lst[val]) for key in lst]))
		self.set(name, lst)
		return i

	def	getMapMdlTxnMgr2(self, name, offset, cnt):
		lst = {}
		i   = offset
		c = self.content
		self.content = u""
		skip1 = 8 if (getFileVersion() < 2011) else 0
		skip2 = 1 if (getFileVersion() > 2018) else 0
		for j in range(cnt):
			key = len(lst)
			val = ModelerTxnMgr()
			tmp = u"[%02X].ref_1" %(j)
			i = self.ReadCrossRef(i, name, tmp)
			val.ref_1 = self.get(tmp)
			self.delete(tmp)
			val.u32_0, i = getUInt32(self.data, i)
			i =  self.ReadList2(i, _TYP_UINT16_A_, 'tmp', 2)
			val.lst = self.get('tmp')
			val.u8_0, i  = getUInt8(self.data, i)
			val.s32_0, i  = getSInt32(self.data, i)
			i += skip1 + skip2
		self.content += u" %s=[%s]" % (name, u",".join([u"[\'%s\': (%s)]" %(key, lst[val]) for key in lst]))
		self.delete('tmp')
		self.set(name, lst)
		return i

	def getMapKeyApp1(self, name, offset, cnt):
		lst = {}
		i   = offset
		self.set(name, lst)
		APP_1 = Struct('<BffffffffffffB').unpack_from
		for j in range(cnt):
			key, i = getUInt32(self.data, i)
			val = APP_1(self.data, i)
			i += 50
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
		self.content += u" %s={%s}" %(name, ",".join([u"(%04X:%r" %(key, val) for key, val in lst.items()]))
		return i

	def ReadMetaData_MAP(self, name, offset, typ):
		cnt, i = getUInt32(self.data, offset)
		func = getattr(self, TYP_MAP_FUNC[typ])
		if (cnt > 0):
			arr32, i = getUInt32A(self.data, i, 2)
		return func(name, i, cnt)

	def ReadList2(self, offset, typ, name, arraySize = 1):
		i = CheckList(self.data, offset, 0x0002)
		return self.ReadMetaData_LIST(i, name, typ, arraySize)

	def ReadList3(self, offset, typ, name):
		i = CheckList(self.data, offset, 0x0003)
		return self.ReadMetaData_ARRAY(name, i, typ)

	def ReadList4(self, offset, typ, name = 'lst4', arraySize = 1):
		i = CheckList(self.data, offset, 0x0004)
		return self.ReadMetaData_04(name, i, typ, arraySize)

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
		i = self.reader.skipBlockSize(i)

		hdr = Header0(u32_0, u16_0)
		self.set('hdr', hdr)
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

		lastUnit     = 'XXXXX' # choos any unit that is not defined!
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

class SecNodeRef():
	TYPE_PARENT = 1
	TYPE_CHILD  = 2
	TYPE_CROSS  = 3

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
		if (self._data): self._data.set(name, value)

	@property
	def sketchEntity(self):
		if (self._data): return self._data.sketchEntity
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

	def setSketchEntity(self, index, entity):
		if (self._data):
			self._data.sketchIndex = index
			self._data.sketchEntity = entity

	def getValue(self):
		node = self.node
		if (node): return node.getValue()
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
