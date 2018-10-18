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

_TYP_GUESS_                 = 0x0000

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

_TYP_LIST_GUESS_            = 0x8000
_TYP_LIST_UINT16_A_         = 0x8001
_TYP_LIST_SINT16_A_         = 0x8002
_TYP_LIST_UINT32_A_         = 0x8003
_TYP_LIST_SINT32_A_         = 0x8004
_TYP_LIST_FLOAT32_A_        = 0x8005
_TYP_LIST_FLOAT64_A_        = 0x8006
_TYP_LIST_FONT_             = 0x8007
_TYP_LIST_X_REF_            = 0x8008

_TYP_MAP_KEY_KEY_           = 0x7001
_TYP_MAP_KEY_REF_           = 0x7002
_TYP_MAP_KEY_X_REF_         = 0x7003
_TYP_MAP_REF_REF_           = 0x7004
_TYP_MAP_TEXT8_REF_         = 0x7005
_TYP_MAP_TEXT8_X_REF_       = 0x7006
_TYP_MAP_TEXT16_REF_        = 0x7007
_TYP_MAP_TEXT16_X_REF_      = 0x7008
_TYP_MAP_X_REF_KEY_         = 0x7009
_TYP_MAP_X_REF_FLOAT64_     = 0x700A
_TYP_MAP_X_REF_2D_UINT32_   = 0x700B
_TYP_MAP_X_REF_X_REF_       = 0x700C
_TYP_MAP_X_REF_LIST2_XREF_  = 0x700D
_TYP_MAP_UUID_UINT32_       = 0x700E
_TYP_MAP_UUID_X_REF         = 0x700F
_TYP_MAP_U16_U16_           = 0x7010

_TYP_MAP_MDL_TXN_MGR_1_     = 0x6001
_TYP_MAP_MDL_TXN_MGR_2_     = 0x6002

TYP_2_FUNC = {
	_TYP_CHAR_:                  'getList2Chars',
	_TYP_NODE_REF_:              'getList2Childs',
	_TYP_NODE_X_REF_:            'getList2Xrefs',
	_TYP_STRING8_:               'getList2String8s',
	_TYP_STRING16_:              'getList2String16s',
	_TYP_UINT8_:                 'getList2UInt8s',
	_TYP_SINT8_:                 'getList2SInt8s',
	_TYP_UINT16_:                'getList2UInt16s',
	_TYP_SINT16_:                'getList2SInt16s',
	_TYP_UINT32_:                'getList2UInt32s',
	_TYP_SINT32_:                'getList2SInt32s',
	_TYP_FLOAT32_:               'getList2Float32s',
	_TYP_FLOAT64_:               'getList2Float64s',
	_TYP_UINT8_A_:               'getList2UInt8sA',
	_TYP_SINT8_A_:               'getList2SInt8sA',
	_TYP_UINT16_A_:              'getList2UInt16sA',
	_TYP_SINT16_A_:              'getList2SInt16sA',
	_TYP_UINT32_A_:              'getList2UInt32sA',
	_TYP_SINT32_A_:              'getList2SInt32sA',
	_TYP_FLOAT32_A_:             'getList2Float32sA',
	_TYP_FLOAT64_A_:             'getList2Float64sA',
	_TYP_FONT_:                  'getList2Fonts',
	_TYP_LIGHTNING_:             'getList2Lightnings',
	_TYP_2D_F64_U32_4D_U8_:      'getList2App1',
	_TYP_U32_TXT_TXT_DATA_:      'getList2App2',
	_TYP_U32_TXT_U32_LST2_:      'getList2App3',
	_TYP_APP_1_:                 'getList2App4',
	_TYP_F64_F64_U32_U8_U8_U16_: 'getList2App5',
	_TYP_LIST_GUESS_:            'getList2Guess',
	_TYP_LIST_UINT16_A_:         'getList2ListUInt16sA',
	_TYP_LIST_SINT16_A_:         'getList2ListSInt16sA',
	_TYP_LIST_UINT32_A_:         'getList2ListUInt32sA',
	_TYP_LIST_SINT32_A_:         'getList2ListSInt32sA',
	_TYP_LIST_FLOAT32_A_:        'getList2ListFloats32sA',
	_TYP_LIST_FLOAT64_A_:        'getList2ListFloats64sA',
	_TYP_LIST_FONT_:             'getList2ListFonts',
	_TYP_LIST_X_REF_:            'getList2ListXRefs',
	_TYP_MAP_X_REF_KEY_:         'getList2ListXRefKeys'
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
		self.content += ' %s=%r' %(name, x)
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

	def ReadNodeRef(self, offset, name, type, number = -1, dump = False):
		u32, i = getUInt32(self.data, offset)
		ref = SecNodeRef(u32, type)

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
		if (dump):
			self.content  += ' %s=%s' %(name, ref)
		return i

	def ReadChildRef(self, offset, name = 'ref', number = -1, dump = True):
		return self.ReadNodeRef(offset, name , SecNodeRef.TYPE_CHILD, number, dump)

	def ReadCrossRef(self, offset, name = 'ref', number = -1, dump = True):
		return self.ReadNodeRef(offset, name, SecNodeRef.TYPE_CROSS, number, dump)

	def ReadParentRef(self, offset):
		return self.ReadNodeRef(offset, 'parent', SecNodeRef.TYPE_CROSS, -1, False)

	def getList2Chars(self, offset, cnt, arraysize):
		try:
			t, i = getText8(self.data, offset, cnt)
			return [t], i, u"'%s'" %(t)
		except:
			t, i = getUInt8A(self.data, offset, cnt)
			return t, i+cnt, IntArr2Str(t, 2)

	def getList2Childs(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadChildRef(i, 'tmp', j, False)
			lst.append(self.get('tmp'))
		return lst, i, u"%d" %(cnt)

	def getList2Xrefs(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadCrossRef(i, 'tmp', j, False)
			lst.append(self.get('tmp'))
		return lst, i, u"%d" %(cnt)

	def getList2String8s(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		sep = u""
		s   = u""
		for j in range(cnt):
			val, i = getLen32Text8(self.data, i)
			lst.append(val)
			s += u"%s'%s'" %(sep, val)
			sep = u","
		return lst, i, s

	def getList2String16s(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		sep = u""
		s   = u""
		for j in range(cnt):
			val, i = getLen32Text16(self.data, i)
			lst.append(val)
			s += u"%s'%s'" %(sep, val)
			sep = u","
		return lst, i, s

	def getList2UInt8s(self, offset, cnt, arraysize):
		lst = Struct('<' + 'B'*cnt).unpack_from(self.data, offset)
		i   = offset + cnt
		return list(lst), i, u",".join([u"%02X" %(u8) for u8 in lst])

	def getList2SInt16s(self, offset, cnt, arraysize):
		lst = Struct('<' + 'b'*cnt).unpack_from(self.data, offset)
		i   = offset + cnt
		return list(lst), i, u",".join([u"%d" %(s8) for s8 in lst])

	def getList2UInt16s(self, offset, cnt, arraysize):
		lst = Struct('<' + 'H'*cnt).unpack_from(self.data, offset)
		i   = offset + 2*cnt
		return list(lst), i, u",".join([u"%03X" %(u16) for u16 in lst])

	def getList2SInt16s(self, offset, cnt, arraysize):
		lst = Struct('<' + 'H'*cnt).unpack_from(self.data, offset)
		i   = offset + 2*cnt
		return list(lst), i, u",".join([u"%d" %(s16) for s16 in lst])

	def getList2UInt32s(self, offset, cnt, arraysize):
		lst = Struct('<' + 'L'*cnt).unpack_from(self.data, offset)
		i   = offset + 4*cnt
		return list(lst), i, u",".join([u"%06X" %(s32) for s32 in lst])

	def getList2SInt32s(self, offset, cnt, arraysize):
		lst = Struct('<' + 'l'*cnt).unpack_from(self.data, offset)
		i   = offset + 4*cnt
		return list(lst), i, u",".join([u"%d" %(s32) for s32 in lst])

	def getList2Float32s(self, offset, cnt, arraysize):
		if (getFileVersion() > 2010):
			val = Struct('<' + 'f'*cnt).unpack_from(self.data, offset)
			lst = list(val)
			i   = offset + 4*cnt
		else:
			val = Struct('<' + 'fL'*cnt).unpack_from(self.data, offset)
			lst = list(val)[0::2]
			i   = offset + 8*cnt # 4Bytes float 4Byte blocklen
		return lst, i, u",".join([u"%g" %(f32) for f32 in lst])

	def getList2Float64s(self, offset, cnt, arraysize):
		lst = Struct('<' + 'd'*cnt).unpack_from(self.data, offset)
		i   = offset + 8*cnt
		return list(lst), i, u",".join([u"%g" %(f64) for f64 in lst])

	def getList2UInt8sA(self, offset, cnt, arraysize):
		val = np.reshape(Struct('<' + 'B'*arraysize*cnt).unpack_from(self.data, offset), (-1, arraysize))
		lst = val.tolist()
		i   = offset + arraysize*cnt
		return lst, i, str(lst)

	def getList2SInt8sA(self, offset, cnt, arraysize):
		val = np.reshape(Struct('<' + 'h'*arraysize*cnt).unpack_from(self.data, offset), (-1, arraysize))
		i   = offset + arraysize * cnt
		lst = val.tolist()
		return lst, i, str(lst)

	def getList2UInt16sA(self, offset, cnt, arraysize):
		val = np.reshape(Struct('<' + 'H'*arraysize*cnt).unpack_from(self.data, offset), (-1, arraysize))
		lst = val.tolist()
		i   = offset + (2*arraysize)*cnt
		return lst, i, str(lst)

	def getList2SInt16sA(self, offset, cnt, arraysize):
		if (getFileVersion() > 2010):
			val = np.reshape(Struct('<' + 'h'*arraysize*cnt).unpack_from(self.data, offset), (-1, arraysize))
			i   = offset + (arraysize*2) * cnt
		else:
			val = Struct('<' + ('h'*arraysize+'L')*cnt).unpack_from(self.data, offset)
			val = np.reshape([s16 for i, s16 in enumerate(val) if (i % (arraysize + 1)) != arraysize], (-1, arraysize))
			i   = offset + (2*arraysize + 4) * cnt # 2Bytes for Word + 4Bytes for blocklen
		lst = val.tolist()
		return lst, i, str(lst)

	def getList2UInt32sA(self, offset, cnt, arraysize):
		val = np.reshape(Struct('<' + 'L'*arraysize*cnt).unpack_from(self.data, offset), (-1, arraysize))
		i   = offset + (4*arraysize)*cnt
		lst = val.tolist()
		return lst, i, str(lst)

	def getList2SInt32sA(self, offset, cnt, arraysize):
		val = np.reshape(Struct('<' + 'l'*arraysize*cnt).unpack_from(self.data, offset), (-1, arraysize))
		i   = offset + (arraysize*4) * cnt
		lst = val.tolist()
		return lst, i, str(lst)

	def getList2Float32sA(self, offset, cnt, arraysize):
		if (getFileVersion() > 2010):
			val = np.reshape(Struct('<' + 'f'*arraysize*cnt).unpack_from(self.data, offset), (-1, arraysize))
			i   = offset + (arraysize*4) * cnt
		else:
			val = Struct('<' + ('f'*arraysize+'L')*cnt).unpack_from(self.data, offset)
			val = np.reshape([f32 for i, f32 in enumerate(val) if (i % (arraysize + 1)) != arraysize], (-1, arraysize))
			i   = offset + (arraysize*4 + 4) * cnt # 2Bytes for Word + 4Bytes for blocklen
		lst = val.tolist()
		return lst, i, str(lst)

	def getList2Float64sA(self, offset, cnt, arraysize):
		val = np.reshape(Struct('<' + 'd'*arraysize*cnt).unpack_from(self.data, offset), (-1, arraysize))
		i   = offset + (arraysize*8) * cnt
		lst = val.tolist()
		return lst, i, str(lst)

	def getList2Fonts(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		sep = u""
		s   = u""
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
			s += u"%s(%s)" %(sep, val)
			sep = u","
		return lst, i, s

	def getList2Lightnings(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		sep = u""
		s   = u""
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
				s += u"%s%s" %(sep, val)
				sep = u","
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
				s += u"%s%s" %(sep, val)
				sep = u","
		return lst, i, s

	def getList2App1(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		sep = u""
		s   = u""
		skip = (getFileVersion() < 2011)
		for j in range(cnt):
			if (skip):
				a = Struct('<ddLLBBBBL').unpack_from(self.data, i)
				val = a[0:3] + a[4:8]
				i += 32
			else:
				val = Struct('<ddLBBBB').unpack_from(self.data, i)
				i += 24
			s += u"%s%g,%g,%06X,%02X,%02X,%02X,%02X" %(sep, val[0], val[1], val[2], val[3], val[4], val[5], val[6])
			sep = u","
			lst.append(val)
		return lst, i, s

	def getList2App2(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		s   = u""
		sep = u""
		skip = (getFileVersion() < 2011)
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
			m, i = getUInt16(self.data, i)
			l2, i = getFloat64A(self.data, i, m)
			l3, i = getFloat32_2D(self.data, i)
			n2, i = getUInt32(self.data, i)
			if (skip): i += 4
			c1, i = getColorRGBA(self.data, i)
			if (skip): i += 4
			n3, i = getUInt32(self.data, i)
			n4, i = getUInt8(self.data, i)
			if (skip): i += 8
			s += u"\n\t%d,'%s','%s',[%s],[%s],[%s],%04X,%s,%d,%X" %(n1, t1, t2, IntArr2Str(l1, 4), IntArr2Str(a1, 2), FloatArr2Str(l2), n2, c1, n3, n4)
			lst.append((n1, t1, t2, l1, a1, l2, l3, n2, c1, n3, n4))
		return lst, i, s

	def getList2App3(self, offset, cnt, arraysize):
		lst  = []
		i    = offset
		sep  = u""
		s    = u""
		skip = (getFileVersion() < 2011)
		for j in range(cnt):
			n1, i = getUInt32(self.data, i)
			t1, i = getLen32Text16(self.data, i)
			n2, i = getUInt32(self.data, i)
			c = self.content
			self.content = ""
			i = self.ReadList2(i, _TYP_FLOAT64_, 'tmp')
			l1 = self.get('tmp')
			self.content = c
			n3, i = getUInt8(self.data, i)
			if (skip): i += 4
			lst.append((n1, t1, n2, l1, n3))
			s += u"%s[%d,'%s',%06X,%s,%02X]" %(sep, n1, t1, n2, FloatArr2Str(l1), n3)
			sep = u","
		self.delete('_tmp')
		return lst, i, s

	def getList2App4(self, offset, cnt, arraysize):
		lst    = []
		i      = offset
		sep    = u""
		s      = u""
		skip   = (getFileVersion() < 2011)
		for j in range(cnt):
			n1, n2, n3, f1, f2 = APP_4_A(self.data, i)
			i += 18
			t1, i = getLen32Text16(self.data, i)
			f3, f4, n4, n5 = APP_4_B(self.data, i)
			i += 11
			if (skip): i += 8
			lst.append((n1, n2,  n3,  f1, f2,  t1,  f3, f4, n4, n5))
			s += u"%s[%d, %d, %04X, %g, %g, '%s', %g, %g, %03X, %02X]" %(sep, n1, n2, n3, f1, f2, t1,  f3, f4, n4, n5)
			sep = u","
		return lst, i, s

	def getList2App5(self, offset, cnt, arraysize):
		lst    = []
		i      = offset
		sep    = u""
		s      = u""
		skip = (getFileVersion() < 2011)
		for j in range(cnt):
			f1, f2, n1 = APP_5_A(self.data, i)
			i += 20
			if (skip): i += 4
			n2, n3, n4 = APP_5_B(self.data, i)
			i += 4
			if (skip): i += 4
			lst.append((f1, f2, n1, n2,  n3,  n4))
			s += u"%s[%g, %g, %04X, %02X, %02X, %03X]" %(sep, f1, f2, n1, n2, n3, n4)
			sep = u","
		return lst, i, s

	def getList2Guess(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, _TYP_GUESS_, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')
		return lst, i, u""

	def getList2ListUInt16sA(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, _TYP_UINT16_A_, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')
		return lst, i, u""

	def getList2ListSInt16sA(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, _TYP_SINT16_A_, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')
		return lst, i, u""

	def getList2ListUInt32sA(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, _TYP_UINT32_A_, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')
		return lst, i, u""

	def getList2ListSInt32sA(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, _TYP_SINT32_A_, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')
		return lst, i, u""

	def getList2ListFloats32sA(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, _TYP_FLOAT32_A_, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')
		return lst, i, u""

	def getList2ListFloats64sA(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, _TYP_FLOAT64_A_, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')
		return lst, i, u""

	def getList2ListFonts(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		for j in range(cnt):
			i = self.ReadList2(i, _TYP_FONT_, 'lst_tmp', arraysize)
			lst.append(self.get('lst_tmp'))
		self.delete('lst_tmp')
		return lst, i, u""

	def getList2ListXRefs(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		skip = (getFileVersion() < 2011)
		for j in range(cnt):
			if (skip): i += 4
			i = self.ReadList2(i, _TYP_UINT32_, 'lst_tmp')
			i = self.ReadCrossRef(i, 'tmp')
			if (skip): i += 4
			lst.append((self.get('lst_tmp'), self.get('tmp')))
		self.delete('tmp')
		self.delete('lst_tmp')
		return lst, i, u""

	def getList2ListXRefKeys(self, offset, cnt, arraysize):
		lst = []
		i   = offset
		sep = u""
		s   = u""
		for j in range(cnt):
			i = self.ReadCrossRef(i, 'tmp', j, False)
			key = self.get('tmp')
			val, i = getUInt32(self.data, i)
			s += u"%s[%s:%X]" %(sep, getIndex(key), val)
			lst.append((key, val))
		self.delete('tmp')
		return lst, i, s

	def ReadMetaData_02(self, offset, typ, arraySize = 1):
		cnt, i = getUInt32(self.data, offset)
		if (cnt > 0):
			arr32, i = getUInt32A(self.data, i, 2)
			if (typ == _TYP_GUESS_):
				t = arr32[1]
				if (t == 0x0107):
					t = _TYP_2D_F64_U32_4D_U8_
				elif (t >= 0x0114 and t <= 0x0126):
					t = _TYP_FLOAT32_A_
					arraySize = 3
				elif (t >= 0x0129 and t <= 0x013F) or (t == 0x0146):
					t = _TYP_FLOAT32_A_
					arraySize = 2
				elif (t == 0x0142):
					t = _TYP_FONT_
				else:
					t = _TYP_NODE_REF_
			else:
				t = typ
			func = getattr(self, TYP_2_FUNC[t])
			return func(i, cnt, arraySize)
		return [], i, u""

	def ReadMetaData_04(self, offset, typ, arraySize = 0):
		sep = ''
		lst = []
		skipBlockSize = (getFileVersion() < 2011)

		cnt, i = getUInt32(self.data, offset)
		if (cnt > 0):
			arr16, i = getUInt16A(self.data, i, 2)
			t = typ
			if (t == _TYP_GUESS_):
				if ((arr16[0] == 0x0101) and (arr16[0]==0x0000)):
					t = _TYP_RESULT_ITEM4_
				else:
					t = _TYP_NODE_REF_
			for j in range(cnt):
				if (t == _TYP_NODE_REF_):
					i = self.ReadChildRef(i, 'tmp', j, False)
					val = self.get('tmp')
					s = ''
				elif (t == _TYP_NODE_X_REF_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					s = ''
				elif (t == _TYP_STRING16_):
					val, i = getLen32Text16(self.data, i)
					s = '\"%s\"' %(val)
				elif (t == _TYP_STRING8_):
					val, i = getLen32Text8(self.data, i)
					s = '\"%s\"' %(val)
				elif (t == _TYP_SINT32_A_):
					val, i = getSInt32A(self.data, i, arraySize)
					s = '[%s]' %(",".join(["%d" %(d) for d in val]))
				elif (t == _TYP_UINT32_A_):
					val, i = getUInt32A(self.data, i, arraySize)
					if (skipBlockSize): i += 4
					s = '[%s]' %(IntArr2Str(val, 8))
				elif (t == _TYP_RESULT_ITEM4_):
					val = ResultItem4()
					val.a0, i = getUInt16A(self.data, i, 4)
					val.a1, i = getFloat64_3D(self.data, i)
					val.a2, i = getFloat64_3D(self.data, i)
					if (skipBlockSize): i += 4
					s = '%s' %(val)
				lst.append(val)
				if (len(s) > 0):
					self.content += '%s%s' %(sep, s)
					sep = ','
			self.delete('tmp')
		return lst, i

	def ReadMetaData_ARRAY(self, offset, typ):
		lst = []

		cnt, i = getUInt32(self.data, offset)
		if (cnt > 0):
			arr16, i = getUInt16A(self.data, i, 2)
			for j in range(cnt):
				if (typ == _TYP_UINT32_):
					i = self.ReadUInt32(i, 'tmp')
				elif (typ == _TYP_NODE_X_REF_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
				else:
					i = self.ReadChildRef(i, 'tmp', j, False)
				lst.append(self.get('tmp'))
			self.delete('tmp')
		return lst, i

	def ReadMetaData_MAP(self, offset, typ):
		lst = {}
		sep = ''
		skipBlockSize = (getFileVersion() < 2011)

		cnt, i = getUInt32(self.data, offset)
		if (cnt > 0):
			arr32, i = getUInt32A(self.data, i, 2)
			for j in range(cnt):
				if (typ == _TYP_MAP_KEY_KEY_):
					key, i = getUInt32(self.data, i)
					val, i = getUInt32(self.data, i)
					self.content += '%s[%04X:%04X]' %(sep, key, val)
				elif (typ == _TYP_MAP_U16_U16_):
					key, i = getUInt16(self.data, i)
					val, i = getUInt16(self.data, i)
					self.content += '%s[%03X:%03X]' %(sep, key, val)
				elif (typ == _TYP_MAP_KEY_REF_):
					key, i = getUInt32(self.data, i)
					i = self.ReadChildRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[%04X: (%s)]' %(sep, key, val)
				elif (typ == _TYP_MAP_KEY_X_REF_):
					key, i = getUInt32(self.data, i)
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[%04X: (%s)]' %(sep, key, val)
				elif (typ == _TYP_MAP_REF_REF_):
					i = self.ReadChildRef(i, 'tmp', j, False)
					key = self.get('tmp')
					i = self.ReadChildRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[(%s): (%s)]' %(sep, key, val)
				elif (typ == _TYP_MAP_X_REF_KEY_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					key = self.get('tmp')
					val, i = getUInt32(self.data, i)
					self.content += '%s[%s: (%X)]' %(sep, getIndex(key), val)
				elif (typ == _TYP_MAP_X_REF_2D_UINT32_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					key = self.get('tmp')
					val, i = getUInt32A(self.data, i, 2)
					self.content += '%s[%s: (%s)]' %(sep, getIndex(key), IntArr2Str(val, 4))
				elif (typ == _TYP_MAP_X_REF_X_REF_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					key = self.get('tmp')
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[%s: %s]' %(sep, getIndex(key), getIndex(val))
				elif (typ == _TYP_MAP_X_REF_LIST2_XREF_):
					c = self.content
					i = self.ReadCrossRef(i, 'tmp', j, False)
					key = self.get('tmp')
					i = self.ReadList2(i, _TYP_NODE_X_REF_, 'tmp')
					val = self.get('tmp')
					self.content = c + '%s[%s: (%s)]' %(sep, getIndex(key), '),('.join(['%s,' %(getIndex(h)) for h in val]))
				elif (typ == _TYP_MAP_X_REF_FLOAT64_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					key = self.get('tmp')
					val, i = getFloat64(self.data, i)
					self.content += '%s[%s: %s]' %(sep, getIndex(key), val)
				elif (typ == _TYP_MAP_UUID_UINT32_):
					key, i = getUUID(self.data, i)
					val, i = getUInt32(self.data, i)
					self.content += '%s[%s: %s]' %(sep, key, val)
				elif (typ == _TYP_MAP_UUID_X_REF):
					key, i = getUUID(self.data, i)
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[%s: %s]' %(sep, key, getIndex(val))
				elif (typ == _TYP_MAP_TEXT8_REF_):
					key, i = getLen32Text8(self.data, i)
					i = self.ReadChildRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				elif (typ == _TYP_MAP_TEXT8_X_REF_):
					key, i = getLen32Text8(self.data, i)
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				elif (typ == _TYP_MAP_TEXT16_REF_):
					key, i = getLen32Text16(self.data, i)
					i = self.ReadChildRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				elif (typ == _TYP_MAP_MDL_TXN_MGR_1_):
					key = len(lst)
					val = ModelerTxnMgr()
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val.ref_1 = self.get('tmp')
					val.u32_0, i = getUInt32(self.data, i)
					c = self.content
					self.content = u""
					i =  self.ReadList2(i, _TYP_UINT16_A_, 'tmp', 2)
					self.content = c
					val.lst = self.get('tmp')
					val.u8_0, i  = getUInt8(self.data, i)
					if (skipBlockSize): i += 4
					if (getFileVersion() > 2018): i += 1
					val.u32_1, i  = getUInt32(self.data, i)
					val.u8_1, i   = getUInt8(self.data, i)
					val.s32_0, i  = getSInt32(self.data, i)
					if (skipBlockSize): i += 8
					if (getFileVersion() > 2018): i += 1
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				elif (typ == _TYP_MAP_MDL_TXN_MGR_2_):
					key = len(lst)
					val = ModelerTxnMgr()
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val.ref_1 = self.get('tmp')
					val.u32_0, i = getUInt32(self.data, i)
					c = self.content
					self.content = u""
					i =  self.ReadList2(i, _TYP_UINT16_A_, 'tmp', 2)
					self.content = c
					val.lst = self.get('tmp')
					val.u8_0, i  = getUInt8(self.data, i)
					val.s32_0, i  = getSInt32(self.data, i)
					if (skipBlockSize): i += 8
					if (getFileVersion() > 2018): i += 1
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				elif (typ == _TYP_MAP_TEXT16_X_REF_):
					key, i = getLen32Text16(self.data, i)
					key = translate(key)
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				lst[key] = val
				sep = ','
			self.delete('tmp')
		return lst, i

	def ReadList2(self, offset, typ, name, arraySize = 1):
		i = CheckList(self.data, offset, 0x0002)
		self.content += ' %s={' %(name)
		lst, i, s = self.ReadMetaData_02(i, typ, arraySize)
		self.content += s
		self.content += '}'
		self.set(name, lst)
		return i

	def ReadList3(self, offset, typ, name):
		i = CheckList(self.data, offset, 0x0003)
		self.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_ARRAY(i, typ)
		self.content += '}'
		self.set(name, lst)
		return i

	def ReadList4(self, offset, typ, name = 'lst4', arraySize = 1):
		i = CheckList(self.data, offset, 0x0004)
		self.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_04(i, typ, arraySize)
		self.content += '}'
		self.set(name, lst)
		return i

	def ReadList6(self, offset, typ, name = 'lst6'):
		i = CheckList(self.data, offset, 0x0006)
		self.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_MAP(i, typ)
		self.content += '}'
		self.set(name, lst)
		return i

	def ReadList7(self, offset, typ, name = 'lst7'):
		i = CheckList(self.data, offset, 0x0007)
		self.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_MAP(i, typ)
		self.content += '}'
		self.set(name, lst)
		return i

	def ReadList8(self, offset, typ, name = 'lst8'):
		i = CheckList(self.data, offset, 0x0008)
		self.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_ARRAY(i, typ)
		self.content += '}'
		self.set(name, lst)
		return i

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
		unitRef = self.get('refUnit')
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
		unitRef = self.get('refUnit')
		if (unitRef):
			numerators = self.getUnitFactors(unitRef.get('numerators'))
			denominators = self.getUnitFactors(unitRef.get('denominators'))
			factor = numerators / denominators

			derivedRef = unitRef.get('refDerived')
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
		unit  = self.get('refUnit')
		unitName = u''
		if (unit):
			unitName     = self.getUnitFormula(unit.get('numerators'))
			denominators = self.getUnitFormula(unit.get('denominators'))
			if (len(denominators) > 0):
				unitName += '/' + denominators

		return unitName

	def getDerivedUnitName(self):
		unit = self.get('refUnit')
		if (unit):
			derived = unit.get('refDerived')
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

	def __init__(self, m, refType):
		self.index    = (m & 0x7FFFFFFF)
		self.mask     = (m & 0x80000000) >> 31
		self.type     = refType
		self.number   = 0
		self._data    = None
		self.analysed = False

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

	@property
	def first(self):
		node = self.node
		if (node): return node.first
		return None

	@property
	def next(self):
		node = self.node
		if (node): return node.next
		return None

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
		return self.__str__()
