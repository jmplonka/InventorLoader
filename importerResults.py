# -*- coding: utf-8 -*-

'''
importerResults.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment import SegmentReader, checkReadAll
from importerClasses import ResultItem4, AbstractData
from importerUtils   import *
import importerSegNode

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class ResultReader(SegmentReader):
	def __init__(self, segment):
		super(ResultReader, self).__init__(segment)

	def Read_128AAF24(self, node):
		i = node.Read_Header0()
		if (self.version > 2016):
			i += 4
		else:
			i += 1
		i = node.ReadList4(i, importerSegNode._TYP_RESULT_1_, 'lst1')
		i = node.ReadList4(i, importerSegNode._TYP_RESULT_2_, 'lst2')
		i = node.ReadList4(i, importerSegNode._TYP_RESULT_3_, 'lst3')
		i = self.skipBlockSize(i)
		if (self.version > 2011):
			i = node.ReadList4(i, importerSegNode._TYP_RESULT_4_, 'lst4')
			if (self.version > 2016):
				i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_MAP_APP_1_, 'lst5')
			else:
				node.set('lst5', {})
				i += 1
		else:
			node.set('lst4', [])
			node.set('lst5', {})
			i += 1
		i = node.ReadList4(i, importerSegNode._TYP_RESULT_5_, 'lst6')
		i = node.ReadList4(i, importerSegNode._TYP_RESULT_4_, 'lst7')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadList4(i, importerSegNode._TYP_RESULT_4_, 'lst8')
		i = node.ReadUInt8(i, 'u8_2')
		i = self.skipBlockSize(i)
		return i

	def Read_F645595C(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'schema')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		if (self.version > 2018): i += 1
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadSInt32(i, 'lastKey')
		return i

	def Read_F78B08D5(self, node):
		i = node.Read_Header0('SatHistory')
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'delta_states') # see "*_sat.history" file for details
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'delta_mapping')
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_EC60C64B(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst2')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_7313FAC3(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadList4(i, importerSegNode._TYP_RESULT_1_, 'lst1')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_LIST_CHAR_, 'lst2')
		i = self.skipBlockSize(i)
		return i

	def Read_232792BC(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i = self.ReadTransformation3D(node, i)
		i = node.ReadFloat64A(i, 9, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64_3D(i, 'v1')
		if (self.version > 2014): i += 3
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a2')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'ref_1')
		if (self.version > 2014): i += 4 # skip ???
		return i

	def Read_3B7812B7(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt16(i, 'u16_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		if (self.version > 2014): i = len(node.data) # skip ???
		return i

	def Read_6B2A0553(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt16(i, 'u16_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		if (self.version > 2014): i = len(node.data) # skip ???
		return i

	def Read_E5DDE747(self, node):
		i = node.Read_Header0()
		i = node.ReadFloat64A(i, 14, 'a0')
		i = node.ReadUInt8A(i, 17, 'u8_0')
		i = node.ReadFloat64A(i, 2, 'a1')
		i = node.ReadUInt8A(i, 2, 'a2')
		i = node.ReadFloat64A(i, 6, 'a3')
		return i

	def Read_1729C2F5(self, node):
		i = node.Read_Header0()
		return i

	def Read_F17A4562(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		return i

	def Read_2238DCC5(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = self.ReadTransformation3D(node, i)
		i = node.ReadFloat64A(i, 9, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		return i

	def Read_46C5CF3F(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64A(i, 6, 'box')
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a2')
		i = node.ReadUUID(i, 'uid_1')
		return i

	def Read_4E32D51B(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_1F4A6D7D(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_246184A0(self, node):
		i = node.Read_Header0()
		if (self.version < 2012): i += 4 #skip REF
		i = node.ReadLen32Text16(i)
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_4028969E(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt0')
		if (self.version < 2011):
			i = node.ReadLen32Text16(i, 'txt1')
		else:
			i = node.ReadFloat64(i, 'f64')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_56222A8B(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_0')
		if (node.get('u16_0') == 0x200):
			i = node.ReadLen32Text16(i)
			i =	node.ReadUInt16(i, 'u16_1')
		else:
			i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		if (self.version > 2014): i += 60 # skip 6xFloat + List6
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_F115B4D0(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_0')
		if (node.get('u16_0') == 0x200):
			i = node.ReadLen32Text16(i)
			i =	node.ReadUInt16(i, 'u16_1')
		else:
			i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_0')
		if (self.version > 2014): i += 60 # Skip 6*Float64 + List6
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		n, i  = getUInt16(node.data, i)
		lst = []
		D = Struct('<Lddd').unpack_from
		while (n > 0):
			d = D(node.data, i)
			i += 28
			lst.append(d)
			n -= 1
		node.set('a1', lst)
		return i

	def Read_FDCD32FE(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_0')
		if (node.get('u16_0') == 0x200):
			i = node.ReadLen32Text16(i)
			i =	node.ReadUInt16(i, 'u16_1')
		else:
			i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_0')
		if (self.version > 2014):  i = len(node.data) # skip!!!
		return i

	def Read_ADAF9728(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_0')
		return i

	def Read_3F89DC90(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadChildRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_461E402F(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadChildRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		return i

	def Read_290EDEE2(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadChildRef(i, 'ref_0')
		return i

	def Read_4C4787F7(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
#		i = node.ReadUInt32(i, 'u32_1')
#		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_72218F3A(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TXT16_UINT32_7_, 'lst0')
		return i

	def Read_724167CA(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		return i

	def Read_BE8C212C(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadFloat64(i, 'f0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_A20D9DC5(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_09D767B3(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_2B4F628E(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version < 2021):
			i = node.ReadParentRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid')
		if (self.version > 2017): i += 8 # skip 00 00 00 00 0(0|1) 00 00 00
		return i

	def Read_5C32D0F7(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_BC55EDF9(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_77A37AC2(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadUUID(i, 'uid')
		return i

	def Read_958DB976(self, node):
		i = self.skipBlockSize(0, 2)
		return i

	def Read_C435E97C(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadLen32Text16(i)
		return i

	def Read_8BE6129C(self, node):
		i = self.skipBlockSize(0, 2)
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_E017EC15(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_F48B3596(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		return i

	def Read_08B9DB46(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadParentRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid')
		i = node.ReadUInt16A(i, 6, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_0')
		if (node.get('u16_0') == 0x200):
			i = node.ReadLen32Text16(i, 'txt')
			i = node.ReadUInt16(i, 'u16_1')
		i = self.skipBlockSize(i)
		return i

	def Read_48894274(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadChildRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_82B9E07A(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadLen32Text16(i)
		i = node.ReadUUID(i, 'uid')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_FB8CD1C8(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadLen32Text16(i)
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	####################
	# U32 Text sections
	def ReadHeaderU32Txt(self, node, typeName = None):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_7DD5B203(self, node):
		i = self.ReadHeaderU32Txt(node)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		return i

	####################
	#
	def Read_Header1(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadParentRef(i)
		return i

	def Read_09780457(self, node):
		i = self.Read_Header1(node)
		i = node.ReadSInt32(i, 'delta_state') # the number of the delta_states in the sat file
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_21830CED(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 10, 'a0')
		return i

	def Read_36246381(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 8, 'a0')
		return i

	def Read_69C3A76F(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 16, 'a0')
		return i

	def Read_F434C70B(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 10, 'a0')
		return i

	def Read_F8DD2C9D(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 8, 'a0')
		return i

	####################
	# int Parent int int sections
	def Read_Header2(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'root')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'ref_0')
		return i

	def Read_0E70AF5C(self, node):
		i = self.Read_Header2(node)
		i = node.ReadUInt32(i, 'dcBodyIdx')
		return i

	def Read_3E0040FD(self, node):
		i = self.Read_Header2(node)
		i = node.ReadUInt32(i, 'dcBodyIdx')
		i = node.ReadUInt32(i, 'dcCreatorIdx')
		return i

	def Read_6B9A3C47(self, node):
		i = self.Read_Header2(node)
		i = node.ReadUInt32(i, 'dcBodyIdx')
		return i

	def Read_809BE56F(self, node):
		i = self.Read_Header2(node)
		return i

	def Read_80CAECF1(self, node):
		i = self.Read_Header2(node)
		return i

	def Read_9147489A(self, node):
		i = self.Read_Header2(node)
		i = node.ReadUInt32(i, 'dcBodyIdx')
		return i

	def Read_A4645884(self, node):
		i = self.Read_Header2(node)
		return i

	def Read_E065E15A(self, node):
		i = self.Read_Header2(node)
		i = node.ReadUInt32(i, 'dcBodyIdx')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'dcCreatorIdx')
		return i

	def Read_E9B04618(self, node):
		i = self.Read_Header2(node)
		return i
