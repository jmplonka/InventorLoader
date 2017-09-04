#!/usr/bin/env python

'''
importerSegNode.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

import traceback
from importerClasses import Header0, Angle, GraphicsFont, ModelerTxnMgr
from importerUtils   import *
from math            import log10

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.3.1'
__status__      = 'In-Development'

def isList(data, code):
	return ((data[-1] == 0x3000) and (data[-2] == code))

def CheckList(data, offset, type):
	lst, i = getUInt16A(data, offset, 2)
	if (getFileVersion() < 2015):
		if (lst[0] == 0 and (lst[1] == 0)):
			return i - 4 # keep fingers crossed that this is really the number of bytes!
	assert (isList(lst, type)), 'Expected list %d - not [%s]' %(type, IntArr2Str(lst, 4))
	return i

class AbstractNode():
	_TYP_GUESS_                = 0x0000
	_TYP_2D_UINT16_            = 0x0001
	_TYP_2D_SINT16_            = 0x0002
	_TYP_2D_SINT32_            = 0x0003
	_TYP_2D_FLOAT32_           = 0x0004
	_TYP_2D_FLOAT64_           = 0x0005
	_TYP_3D_UINT16_            = 0x0006
	_TYP_3D_SINT16_            = 0x0007
	_TYP_3D_SINT32_            = 0x0008
	_TYP_UINT32A_              = 0x0009
	_TYP_3D_FLOAT32_           = 0x000B
	_TYP_3D_FLOAT64_           = 0x000C
	_TYP_1D_UINT32_            = 0x000D
	_TYP_1D_CHAR_              = 0x000E
	_TYP_1D_FLOAT32_           = 0x000F

	_TYP_FONT_                 = 0x0011
	_TYP_2D_F64_U32_4D_U8_     = 0x0012
	_TYP_NODE_REF_             = 0x0013
	_TYP_STRING16_             = 0x0014
	_TYP_RESULT_ITEM4_         = 0x0015
	_TYP_NODE_X_REF_           = 0x0016

	_TYP_LIST_GUESS_           = 0x8000
	_TYP_LIST_2D_UINT16_       = 0x8001
	_TYP_LIST_2D_SINT16_       = 0x8002
	_TYP_LIST_2D_UINT32_       = 0x8003
	_TYP_LIST_2D_SINT32_       = 0x8004
	_TYP_LIST_2D_FLOAT32_      = 0x8005
	_TYP_LIST_2D_FLOAT64_      = 0x8006
	_TYP_LIST_3D_UINT16_       = 0x8007
	_TYP_LIST_3D_SINT16_       = 0x8008
	_TYP_LIST_3D_UINT32_       = 0x8009
	_TYP_LIST_3D_SINT32_       = 0x800A
	_TYP_LIST_3D_FLOAT32_      = 0x800B
	_TYP_LIST_3D_FLOAT64_      = 0x800C
	_TYP_LIST_FONT_            = 0x8011
	_TYP_LIST_X_REF_           = 0x8012

	_TYP_MAP_KEY_KEY_          = 0x7001
	_TYP_MAP_KEY_REF_          = 0x7002
	_TYP_MAP_KEY_X_REF_        = 0x7003
	_TYP_MAP_REF_REF_          = 0x7004
	_TYP_MAP_TEXT8_REF_        = 0x7005
	_TYP_MAP_TEXT8_X_REF_      = 0x7006
	_TYP_MAP_TEXT16_REF_       = 0x7007
	_TYP_MAP_TEXT16_X_REF_     = 0x7008
	_TYP_MAP_X_REF_KEY_        = 0x7009
	_TYP_MAP_X_REF_FLOAT64_    = 0x700A
	_TYP_MAP_X_REF_2D_UINT32_  = 0x700B
	_TYP_MAP_X_REF_X_REF_      = 0x700C
	_TYP_MAP_X_REF_LIST2_XREF_ = 0x700D
	_TYP_MAP_UUID_UINT32_      = 0x700E
	_TYP_MAP_UUID_X_REF        = 0x700F
	_TYP_MAP_U16_U16_          = 0x7010

	_TYP_MAP_MDL_TXN_MGR_1_    = 0x6001
	_TYP_MAP_MDL_TXN_MGR_2_    = 0x6002

	def __init__(self):
		self.typeID       = None
		self.name         = None
		self.index        = -1
		self.parentIndex  = None
		self.hasParent    = False
		self.content      = ''
		self.childIndexes = []
		self.properties   = {}
		self.size         = 0
		self.visible      = False
		self.construction = False
		self.segment      = None
		self.sketchIndex  = None
		self.sketchEntity = None
		self.valid        = True

	def set(self, name, value):
		'''
		Sets the value for the property name.
		name:  The name of the property.
		value: The value of the property.
		'''
		oldVal = None

		if (name):
			if (name in self.properties):
				# logMessage('>W0005: name already defined in %08X[%d]!' %(self.typeID.time_low, self.index))
				oldVal = self.properties[name]
			self.properties[name] = value
		return oldVal

	def get(self, name):
		'''
		Returns the value fo the property given by the name.
		name: The name of the property.
		Returns None if the property is not yet set.
		'''
		if (name in self.properties):
			return self.properties[name]
		return None

	def delete(self, name):
		'''
		Removes the value from the property given by the name.
		name: The name of the property.
		'''
		if (name in self.properties):
			del self.properties[name]

	def ReadUInt8(self, offset, name):
		x, i = getUInt8(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%02X' %(name, x)
		return i

	def ReadUInt8A(self, offset, n, name):
		x, i = getUInt8A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=[%s]' %(name, IntArr2Str(x, 2))
		return i

	def ReadUInt16(self, offset, name):
		x, i = getUInt16(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%04X' %(name, x)
		return i

	def ReadUInt16A(self, offset, n, name):
		x, i = getUInt16A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=[%s]' %(name, IntArr2Str(x, 4))
		return i

	def ReadSInt16(self, offset, name):
		x, i = getSInt16(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%04X' %(name, x)
		return i

	def ReadSInt16A(self, offset, n, name):
		x, i = getSInt16A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=[%s]' %(name, IntArr2Str(x, 4))
		return i

	def ReadUInt32(self, offset, name):
		x, i = getUInt32(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%06X' %(name, x)
		return i

	def ReadUInt32A(self, offset, n, name):
		x, i = getUInt32A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=[%s]' %(name, IntArr2Str(x, 4))
		return i

	def ReadSInt32(self, offset, name):
		x, i = getSInt32(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%X' %(name, x)
		return i

	def ReadSInt32A(self, offset, n, name):
		x, i = getSInt32A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=[%s]' %(name, IntArr2Str(x, 4))
		return i

	def ReadFloat32(self, offset, name):
		x, i = getFloat32(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%g' %(name, x)
		return i

	def ReadFloat32A(self, offset, n, name):
		x, i = getFloat32A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=(%s)' %(name, FloatArr2Str(x))
		return i

	def ReadFloat64(self, offset, name):
		x, i = getFloat64(self.data, offset)
		self.set(name, x)
		self.content += ' %s=%g' %(name, x)
		return i

	def ReadFloat64A(self, offset, n, name):
		x, i = getFloat64A(self.data, offset, n)
		self.set(name, x)
		self.content += ' %s=(%s)' %(name, FloatArr2Str(x))
		return i

	def ReadUUID(self, offset, name):
		x, i = getUUID(self.data, offset, '%08X[%d]' %(self.typeID.time_low, self.index))
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
		x, i = getUInt8(self.data, offset)
		x = (x != 0)
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
		x = Angle(x, pi/180.0, '\xC2\xB0')
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
		u16_0, i = getUInt16(self.data, offset)
		u16_1, i = getUInt16(self.data, i)
		ref = NodeRef(u16_0, u16_1, type)

		self.set(name, None)

		if (ref.index > 0):
			ref.number = number
			if (ref.index == self.index):
				logError('ERROR: Found self-ref \'%s\' for (%04X): %s' %(name, self.index, self.typeName))
			else:
				if (type == NodeRef.TYPE_PARENT):
					self.parentIndex = ref
				else:
					self.childIndexes.append(ref)
		else:
			ref = None
		self.set(name, ref)
		if (dump):
			self.content  += ' %s=%s' %(name, ref)
		return i

	def ReadChildRef(self, offset, name = 'ref', number = -1, dump = True):
		i = self.ReadNodeRef(offset, name, NodeRef.TYPE_CHILD, number, dump)
		ref = self.get(name)
		if (ref):
			if (self.index > ref.index):
				#logError('    >FATAL: child \'%s\' (%04X) is smaller - (%04X): %s!' %(name, ref.index, self.index, self.typeName))
				ref.type = NodeRef.TYPE_CROSS
		return i

	def ReadCrossRef(self, offset, name = 'xref', number = -1, dump = True):
		i = self.ReadNodeRef(offset, name, NodeRef.TYPE_CROSS, number, dump)
		return i

	def ReadParentRef(self, offset):
		return self.ReadNodeRef(offset, 'parent', NodeRef.TYPE_PARENT, -1, False)

	def ReadMetaData_02(self, offset, typ, arraySize = 1):
		sep = ''
		skipBlockSize = (getFileVersion() < 2011)
		cnt, i = getUInt32(self.data, offset)
		lst = []

		if (cnt > 0):
			arr32, i = getUInt32A(self.data, i, 2)

			if (typ == AbstractNode._TYP_GUESS_):
				t = arr32[1]
				if (t == 0x0107):
					t = AbstractNode._TYP_2D_F64_U32_4D_U8_
				elif (t >= 0x0114 and t <= 0x0126):
					t = AbstractNode._TYP_3D_FLOAT32_
				elif (t >= 0x0129 and t <= 0x013F) or (t == 0x0146):
					t = AbstractNode._TYP_2D_FLOAT32_
				elif (t == 0x0142):
					t = AbstractNode._TYP_FONT_
				else:
					t = AbstractNode._TYP_NODE_REF_
			else:
				t = typ

			if (t == AbstractNode._TYP_1D_CHAR_):
				val, i = getText8(self.data, i, cnt)
				lst.append(val)
				self.content += val
			else:
				j = 0
				while (j < cnt):
					str = ''
					if (t == AbstractNode._TYP_NODE_REF_):
						i = self.ReadChildRef(i, 'tmp', j, False)
						val = self.get('tmp')
						str = ''
					elif (t == AbstractNode._TYP_NODE_X_REF_):
						i = self.ReadCrossRef(i, 'tmp', j, False)
						val = self.get('tmp')
						str = ''
					elif (t == AbstractNode._TYP_STRING16_):
						val, i = getLen32Text16(self.data, i)
						str = '\"%s\"' %(val)
					elif (t == AbstractNode._TYP_1D_UINT32_):
						val, i = getUInt32(self.data, i)
						str = '%04X' %(val)
					elif (t == AbstractNode._TYP_1D_FLOAT32_):
						if (getFileVersion() < 2011):
							val, i = getFloat32(self.data, i)
						else:
							val = unpack('<f', self.data[i+2:i+4]+self.data[i:i+2])[0]
							i += 4
						str = '%g' %(val)
					elif (t == AbstractNode._TYP_2D_UINT16_):
						val, i = getUInt16A(self.data, i, 2)
						str = '(%s)' %(IntArr2Str(val, 4))
					elif (t == AbstractNode._TYP_2D_SINT16_):
						val, i = getSInt16A(self.data, i, 2)
						if (skipBlockSize):
							i += 4
						str = '(%s)' %(IntArr2Str(val, 4))
					elif (t == AbstractNode._TYP_UINT32A_):
						val, i = getUInt32A(self.data, i, arraySize)
						str = '(%s)' %(IntArr2Str(val, 8))
					elif (t == AbstractNode._TYP_2D_SINT32_):
						val, i = getSInt32A(self.data, i, 2)
						str = '(%s)' %(IntArr2Str(val, 8))
					elif (t == AbstractNode._TYP_2D_FLOAT32_):
						val, i = getFloat32A(self.data, i, 2)
						if (skipBlockSize):
							i += 4
						str = '(%s)' %(FloatArr2Str(val))
					elif (t == AbstractNode._TYP_2D_FLOAT64_):
						val, i = getFloat64A(self.data, i, 2)
						if (skipBlockSize):
							i += 4
						str = '(%s)' %(FloatArr2Str(val))
					elif (t == AbstractNode._TYP_3D_UINT16_):
						val, i = getUInt16A(self.data, i, 3)
						if (skipBlockSize):
							i += 4
						str = '(%s)' %(IntArr2Str(val, 4))
					elif (t == AbstractNode._TYP_3D_SINT16_):
						val, i = getSInt16A(self.data, i, 3)
						if (skipBlockSize):
							i += 4
						str = '(%s)' %(IntArr2Str(val, 4))
					elif (t == AbstractNode._TYP_3D_SINT32_):
						val, i = getSInt32A(self.data, i, 3)
						if (skipBlockSize):
							i += 4
						str = '(%s)' %(IntArr2Str(val, 8))
					elif (t == AbstractNode._TYP_3D_FLOAT32_): # 3D-Float32
						val, i = getFloat32A(self.data, i, 3)
						if (skipBlockSize):
							i += 4
						str = '(%s)' %(FloatArr2Str(val))
					elif (t == AbstractNode._TYP_3D_FLOAT64_):
						val, i = getFloat64A(self.data, i, 3)
						str = '(%s)' %(FloatArr2Str(val))
					elif (t == AbstractNode._TYP_FONT_): # Font settings
						val = GraphicsFont()
						val.number, i = getUInt32(self.data, i)
						val.ukn1, i = getUInt16A(self.data, i, 4)
						val.ukn2, i = getUInt8A(self.data, i, 2)
						val.ukn3, i = getUInt16A(self.data, i, 2)
						val.name, i = getLen32Text16(self.data, i)
						val.f, i = getFloat32A(self.data, i, 2)
						val.ukn4, i = getUInt8A(self.data, i, 3)
						str = '%s' %(val)
					elif (t == AbstractNode._TYP_2D_F64_U32_4D_U8_):
						val = []
						f, i = getFloat64A(self.data, i, 2)
						val.append(f)
						u, i = getUInt32(self.data, i)
						val.append(u)
						if (skipBlockSize):
							i += 4
						a, i = getUInt8A(self.data, i, 4)
						val.append(a)
						if (skipBlockSize):
							i += 4
						str = '(%s) %X [%s]' %(FloatArr2Str(f), u, IntArr2Str(a, 1))
					elif (t == AbstractNode._TYP_LIST_GUESS_):
						i = self.ReadList2(i, AbstractNode._TYP_GUESS_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_2D_UINT16_):
						i = self.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_2D_SINT16_):
						i = self.ReadList2(i, AbstractNode._TYP_2D_SINT16_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_2D_UINT32_ ):
						i = self.ReadList2(i, AbstractNode._TYP_UINT32A_, 'lst_tmp', 2)
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_2D_SINT32_ ):
						i = self.ReadList2(i, AbstractNode._TYP_2D_SINT32_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_2D_FLOAT32_):
						i = self.ReadList2(i, AbstractNode._TYP_2D_FLOAT32_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_2D_FLOAT64_):
						i = self.ReadList2(i, AbstractNode._TYP_2D_FLOAT64_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_3D_UINT16_):
						i = self.ReadList2(i, AbstractNode._TYP_3D_UINT16_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_3D_SINT16_):
						i = self.ReadList2(i, AbstractNode._TYP_3D_SINT16_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_3D_UINT32_):
						i = self.ReadList2(i, AbstractNode._TYP_UINT32A_, 'lst_tmp', 3)
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_3D_SINT32_):
						i = self.ReadList2(i, AbstractNode._TYP_3D_SINT32_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_3D_FLOAT32_):
						i = self.ReadList2(i, AbstractNode._TYP_3D_FLOAT32_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_3D_FLOAT64_):
						i = self.ReadList2(i, AbstractNode._TYP_3D_FLOAT64_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_FONT_):
						i = self.ReadList2(i, AbstractNode._TYP_FONT_, 'lst_tmp')
						val = self.get('lst_tmp')
						self.delete('lst_tmp')
					elif (t == AbstractNode._TYP_LIST_X_REF_):
						if (skipBlockSize):
							i += 4
						i = self.ReadList2(i, AbstractNode._TYP_1D_UINT32_, 'lst_tmp')
						i = self.ReadCrossRef(i, 'tmp')
						val = [self.get('lst_tmp'), self.get('tmp')]
						if (skipBlockSize):
							i += 4
						self.delete('lst_tmp')
					elif (typ == AbstractNode._TYP_MAP_X_REF_KEY_):
						i = self.ReadCrossRef(i, 'tmp', j, False)
						key = self.get('tmp')
						val, i = getUInt32(self.data, i)
						self.content += '%s[%04X: (%X)]' %(sep, key.index, val)
					else:
						val, i = getUInt16A(self.data, i, 2)
						str = '[%s]' %(IntArr2Str(val[0], 1))
					lst.append(val)

					if (len(str) > 0):
						self.content += '%s%s' %(sep, str)
					sep = ','
					j += 1
			self.delete('tmp')
		return lst, i

	def ReadMetaData_04(self, offset, typ, arraySize = 0):
		lst = []
		skipBlockSize = (getFileVersion() < 2011)

		cnt, i = getUInt32(self.data, offset)
		if (cnt > 0):
			arr16, i = getUInt16A(self.data, i, 2)
			t = typ
			if (t == AbstractNode._TYP_GUESS_):
				if ((arr16[0] == 0x0101) and (arr16[0]==0x0000)):
					t = AbstractNode._TYP_RESULT_ITEM4_
				else:
					t = AbstractNode._TYP_NODE_REF_
			j = 0
			while (j < cnt):
				if (t == AbstractNode._TYP_NODE_REF_):
					i = self.ReadChildRef(i, 'tmp', j, False)
					val = self.get('tmp')
					str = ''
				elif (t == AbstractNode._TYP_NODE_X_REF_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					str = ''
				elif (t == AbstractNode._TYP_STRING16_):
					val, i = getLen32Text16(self.data, i)
					str = '\"%s\"' %(val)
				elif (t == AbstractNode._TYP_2D_SINT32_):
					val, i = getSInt32A(self.data, i, 2)
					str = '[%s]' %(IntArr2Str(val, 8))
				elif (t == AbstractNode._TYP_UINT32A_):
					val, i = getUInt32A(self.data, i, arraySize)
					if (skipBlockSize):
						i += 4
					str = '[%s]' %(IntArr2Str(val, 8))
				elif (t == AbstractNode._TYP_RESULT_ITEM4_):
					val = ResultItem4()
					val.a0, i = getUInt16A(self.data, i, 4)
					val.a1, i = getFloat64A(self.data, i, 3)
					val.a2, i = getFloat64A(self.data, i, 3)
					if (skipBlockSize):
						i += 4
					str = '%s' %(val)
				j += 1
				lst.append(val)
				if (len(str) > 0):
					self.content += '%s%s' %(sep, str)

		return lst, i

	def ReadMetaData_ARRAY(self, offset, typ):
		lst = []

		cnt, i = getUInt32(self.data, offset)
		if (cnt > 0):
			arr16, i = getUInt16A(self.data, i, 2)
			j = 0
			while (j < cnt):
				if (typ == AbstractNode._TYP_1D_UINT32_):
					val, i = getUInt32(self.data, i)
				elif (typ == AbstractNode._TYP_NODE_X_REF_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
				else:
					i = self.ReadChildRef(i, 'tmp', j, False)
				j += 1
				tmp = self.get('tmp')
				lst.append(tmp)
			self.delete('tmp')
		return lst, i

	def ReadMetaData_MAP(self, offset, typ):
		lst = {}
		sep = ''
		skipBlockSize = (getFileVersion() < 2011)

		cnt, i = getUInt32(self.data, offset)
		if (cnt > 0):
			arr32, i = getUInt32A(self.data, i, 2)
			j = 0
			while (j < cnt):
				if (typ == AbstractNode._TYP_MAP_KEY_KEY_):
					key, i = getUInt32(self.data, i)
					val, i = getUInt32(self.data, i)
					self.content += '%s[%04X:%04X]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_U16_U16_):
					key, i = getUInt16(self.data, i)
					val, i = getUInt16(self.data, i)
					self.content += '%s[%03X:%03X]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_KEY_REF_):
					key, i = getUInt32(self.data, i)
					i = self.ReadChildRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[%04X: (%s)]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_KEY_X_REF_):
					key, i = getUInt32(self.data, i)
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[%04X: (%s)]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_REF_REF_):
					i = self.ReadChildRef(i, 'tmp', j, False)
					key = self.get('tmp')
					i = self.ReadChildRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[(%s): (%s)]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_X_REF_KEY_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					key = self.get('tmp')
					val, i = getUInt32(self.data, i)
					self.content += '%s[%04X: (%X)]' %(sep, key.index, val)
				elif (typ == AbstractNode._TYP_MAP_X_REF_2D_UINT32_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					key = self.get('tmp')
					val, i = getUInt32A(self.data, i, 2)
					self.content += '%s[%04X: (%s)]' %(sep, key.index, IntArr2Str(val, 4))
				elif (typ == AbstractNode._TYP_MAP_X_REF_X_REF_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					key = self.get('tmp')
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[%04X: %04X]' %(sep, key.index, val.index)
				elif (typ == AbstractNode._TYP_MAP_X_REF_LIST2_XREF_):
					c = self.content
					i = self.ReadCrossRef(i, 'tmp', j, False)
					key = self.get('tmp')
					i = self.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'tmp')
					val = self.get('tmp')
					self.content = c + '%s[%04X: (%s)]' %(sep, key.index, '),('.join(['%04X' %(h.index) for h in val]))
				elif (typ == AbstractNode._TYP_MAP_X_REF_FLOAT64_):
					i = self.ReadCrossRef(i, 'tmp', j, False)
					key = self.get('tmp')
					val, i = getFloat64(self.data, i)
					self.content += '%s[%04X: %s]' %(sep, key.index, val)
				elif (typ == AbstractNode._TYP_MAP_UUID_UINT32_):
					key, i = getUUID(self.data, i, '%08X[%d]' %(self.typeID.time_low, self.index))
					val, i = getUInt32(self.data, i)
					self.content += '%s[%s: %s]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_UUID_X_REF):
					key, i = getUUID(self.data, i, '%08X[%d]' %(self.typeID.time_low, self.index))
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[%s: %04X]' %(sep, key, val.index)
				elif (typ == AbstractNode._TYP_MAP_TEXT8_REF_):
					key, i = getLen32Text8(self.data, i)
					i = self.ReadChildRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_TEXT8_X_REF_):
					key, i = getLen32Text8(self.data, i)
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_TEXT16_REF_):
					key, i = getLen32Text16(self.data, i)
					i = self.ReadChildRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_MDL_TXN_MGR_1_):
					key = len(lst)
					val = ModelerTxnMgr()
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val.ref_1 = self.get('tmp')
					val.u32_0, i = getUInt32(self.data, i)
					i =  self.ReadList2(i, AbstractNode._TYP_1D_UINT32_, 'tmp')
					val.lst = self.get('tmp')
					val.u8_0, i  = getUInt8(self.data, i)
					if (skipBlockSize):
						i += 4
					val.u32_1, i = getUInt32(self.data, i)
					val.u8_1, i  = getUInt8(self.data, i)
					val.s32_0, i  = getSInt32(self.data, i)
					if (skipBlockSize):
						i += 8
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_MDL_TXN_MGR_2_):
					key = len(lst)
					val = ModelerTxnMgr()
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val.ref_1 = self.get('tmp')
					val.u32_0, i = getUInt32(self.data, i)
					i =  self.ReadList2(i, AbstractNode._TYP_1D_UINT32_, 'tmp')
					val.lst = self.get('tmp')
					val.u8_0, i  = getUInt8(self.data, i)
					val.s32_0, i  = getSInt32(self.data, i)
					if (skipBlockSize):
						i += 8
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				elif (typ == AbstractNode._TYP_MAP_TEXT16_X_REF_):
					key, i = getLen32Text16(self.data, i)
					key = translate(key)
					i = self.ReadCrossRef(i, 'tmp', j, False)
					val = self.get('tmp')
					self.content += '%s[\'%s\': (%s)]' %(sep, key, val)
				j += 1
				lst[key] = val
				sep = ','
			self.delete('tmp')
		return lst, i

	def ReadList2(self, offset, typ, name, arraySize = 1):
		i = CheckList(self.data, offset, 0x0002)
		self.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_02(i, typ, arraySize)
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

	def Read_Header0(self):
		u32_0, i = getUInt32(self.data, 0)
		u16_0, i = getUInt16(self.data, i)
		i = self.reader.skipBlockSize(i)

		hdr = Header0(u32_0, u16_0)
		self.set('hdr', hdr)
		#self.content += ' hdr={%s}' %(hdr)

		return i

	def updateTypeId(self, uid):
		self.typeID = UUID(uid)
		self.typeName = '%08X' %(self.typeID.time_low)

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
		j      = 0
		n      = len(units)

		while (j < n):
			unit = units[j].node

			#unitSupported    = unit.get('UnitSupportet')
			#if (not unitSupported):
			#	return 1.0

			magniture  = unit.get('magnitude')
			unitFactor = unit.get('UnitFactor')
			if (unitFactor is None):
				logError('>ERROR: (%04X): %s has no UnitFactor defined!' %(unit.index, unit.typeName))
			factor *= magniture * unitFactor
			j += 1

		return factor

	def getUnitFactor(self):
		factor = 1.0
		unitRef = self.get('refUnit')
		if (unitRef):
			typ   = unitRef.node
			numerators = self.getUnitFactors(typ.get('numerators'))
			denominators = self.getUnitFactors(typ.get('denominators'))
			factor = numerators / denominators

			derivedRef = typ.get('refDerived')
			if (derivedRef):
				typ = derivedRef.node
				numerators = self.getUnitFactors(typ.get('numerators'))
				denominators = self.getUnitFactors(typ.get('denominators'))
				factor = factor * numerators / denominators
		return factor

	def getUnitFormula(self, units):
		formula = ''
		sep     = ''
		j       = 0
		n       = len(units)

		lastUnit     = 'XXXXX' # choos any unit that is not defined!
		unitExponent = 1       # by default (e.g.): m^1 => m

		while (j < n):
			unit = units[j].node
			j += 1
			subformula = unit.get('Unit')

			if (len(subformula) > 0):
				factor = log10(unit.get('magnitude'))
				if   (factor ==  18): factor = 'E'        # Exa
				elif (factor ==  15): factor = 'P'        # Peta
				elif (factor ==  12): factor = 'T'        # Tera
				elif (factor ==   9): factor = 'G'        # Giga
				elif (factor ==   6): factor = 'M'        # Mega
				elif (factor ==   3): factor = 'k'        # Kilo
				elif (factor ==   2): factor = 'h'        # Hecto
				elif (factor ==   1): factor = 'da'       # Deca
				elif (factor ==   0): factor = ''
				elif (factor ==  -1): factor = 'd'        # Deci
				elif (factor ==  -2): factor = 'c'        # Centi
				elif (factor ==  -3): factor = 'm'        # Milli
				elif (factor ==  -6): factor = '\xC2\xB5' # Micro
				elif (factor ==  -9): factor = 'n'        # Nano
				elif (factor == -12): factor = 'p'        # Pico
				elif (factor == -15): factor = 'f'        # Femto
				elif (factor == -18): factor = 'a'        # Atto
				subformula = factor + subformula
				if (subformula == lastUnit):
					unitExponent += 1
				else:
					if(lastUnit != 'XXXXX'):
						if (unitExponent > 1):
							formula = '%s%s%s^%d' %(formula, sep, lastUnit, unitExponent)
							unitExponent = 1
						else:
							formula = '%s%s%s' %(formula, sep, lastUnit)
						sep =' '
					lastUnit = subformula
		if (j > 0):
			if (unitExponent > 1):
				formula = '%s%s%s^%d' %(formula, sep, subformula, unitExponent)
			else:
				formula = '%s%s%s' %(formula, sep, subformula)
		return formula

	def getUnitName(self):
		'''
		TODO:
		Derived units are not supported in FreeCAD.
		Add a new derived unit! But how?
		Meanwhile the derived units are ignored!
		'''
		unitRef  = self.get('refUnit')
		unitName = ''
		if (unitRef):
			unitData = unitRef.node

#			derivedRef = unitData.get('refDerived')
#			if (derivedRef):
#				unitData = derivedRef.node

			unitName     = self.getUnitFormula(unitData.get('numerators'))
			denominators = self.getUnitFormula(unitData.get('denominators'))
			if (len(denominators) > 0):
				unitName += '/' + denominators

		return unitName

	def getDerivedUnitName(self):
		unitData = self.get('refUnit').node
		derivedRef = unitData.get('refDerived')
		if (derivedRef):
			unitData = derivedRef.node

			unitName     = self.getUnitFormula(unitData.get('numerators'))
			denominators = self.getUnitFormula(unitData.get('denominators'))
			if (len(denominators) > 0):
				unitName += '/' + denominators

			return unitName
		return None

	def getName(self):
		if (self.name is None):
			ref = self.get('label')
			if (ref):
				return ref.getName()
		return self.name

	def __str__(self):
		if (self.name is None):
			return '(%04X): %s%s' %(self.index, self.typeID, self.content)
		return '(%04X): %s \'%s\'%s' %(self.index, self.typeID, self.name, self.content)

class AppNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class BinaryNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class BRepNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class BrowserNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class DCNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class DesignViewNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class EeDataNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class EeSceneNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class FBAttributeNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class GraphicsNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)
		self.key    = 0
		self.keyRef = 0

class NotebookNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class ResultNode(AbstractNode):
	def __init__(self):
		AbstractNode.__init__(self)

class NodeRef():
	TYPE_PARENT = 1
	TYPE_CHILD  = 2
	TYPE_CROSS  = 3

	def __init__(self, n, m, refType):
		self.index        = n + ((m & 0x7FFF) << 16)
		self.mask         = (m & 0x8000) >> 15
		self.type         = refType
		self.number       = 0
		self.node         = None
		self.sketchPos    = -1
		self.sketchIndex  = -1

	@property
	def node(self):
		return self.node

	@node.setter
	def node(self, node):
		self.node = node
		if (node):
			assert isinstance(node, AbstractNode), 'Node reference is not a AbstractNode (%s)!' %(node.__class__.__name__)

	@property
	def typeName(self):
		if (self.node):
			return self.node.typeName
		return None

	@property
	def index(self):
		if (self.node):
			return self.node.index
		return -1

	def getBranchNode(self):
		if (self.node):
			return self.node.node
		return None

	def getName(self):
		if (self.node):
			return self.node.getName()
		return None

	def get(self, name):
		if (self.node):
			return self.node.get(name)
		return None

	def getSketchEntity(self):
		if (self.node):
			return self.node.sketchEntity
		return None

	def getSketchIndex(self):
		if (self.node):
			return self.node.sketchIndex
		return None

	def setSketchEntity(self, index, entity):
		if (self.node):
			self.node.sketchIndex = index
			self.node.sketchEntity = entity

	def __str__(self):
		return '[%04X,%X]' %(self.index, self.mask)
