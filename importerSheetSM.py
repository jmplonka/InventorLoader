# -*- coding: utf-8 -*-

from importerSegment   import SegmentReader
from importerUtils     import *
from importerConstants import VAL_UINT16, VAL_UINT32

import importerSegNode

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class SheetSmReader(SegmentReader):
	def __init__(self, segment):
		super(SheetSmReader, self).__init__(segment)

	def ReadHeaderSM(self, node, typeName = None):
		i = node.Read_Header0(typeName)
		i = node.ReadUInt32(i, 'flags')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		return i

	def Read_F4A2F948(self, node):
		i = self.ReadHeaderSM(node)
		i = node.ReadList3(i, importerSegNode._TYP_NODE_REF_, 'objects')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64A(i, 4, 'a1')
		return i

	####################
	def ReadHeaderSmObject(self, node, typeName = None):
		i = self.ReadHeaderSM(node, typeName)
		i = node.ReadList3(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def ReadHeaderSmObjRef(self, node, typeName = None):
		i = self.ReadHeaderSmObject(node, typeName)
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_CDB613FA(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_025E3388(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_B2D41A36(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		return i

	def Read_5E4E86C7(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_F5A6ED7A(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_35ECB98A(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 3)
		return i

	def Read_D8727CE0(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 3)
		return i

	def Read_028C9254(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_C0CA9B69(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_45A1B92D(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_5EB510C2(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_4B13984A(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_59ACDE3F(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_C2607F03(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_EA9293EA(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_FE56BF50(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_FE44386F(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_9B3499D1(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_648CD16A(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_B86459E3(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_8FB07810(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_1513AE96(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_EF7D412D(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_8DEAF986(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_5CBE01A1(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_F3F435A2(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_502678E8(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_D0EEE1BA(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_4E52B139(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b2')
		i = self.skipBlockSize(i)
		if (self.version < 2012): i += 8 # skip U32[2]
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_FFCFCF1F(self, node):
		i = self.ReadHeaderSmObjRef(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b2')
		return i

	def Read_EA9293EA(self, node):
		i = self.ReadHeaderSmObjRef(node)
		return i

	def ReadHeaderSmObjU32(self, node, typeName = None):
		i = self.ReadHeaderSmObject(node, typeName)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_69C12B31(self, node):
		i = self.ReadHeaderSmObjU32(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_05A6BF7B(self, node):
		i = self.ReadHeaderSmObjU32(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_8466CB8A(self, node):
		i = self.ReadHeaderSmObjU32(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_8A6D1381(self, node):
		i = self.ReadHeaderSmObjU32(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		if (self.version < 2019):
			u, i = getUInt16(node.data, i)
		else:
			u, i = getUInt32(node.data, i)
		node.set('u16_0', u, VAL_UINT16)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		if (self.version < 2019):
			i += 2 # skip U16
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadFloat64A(i, 6, 'a0')
		if (self.version < 2019):
			i += 1 # skip BOOL
			if (self.version > 2011): i += 1 # skip BOOL
		return i

	def Read_82303D42(self, node):
		i = self.ReadHeaderSmObjU32(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_D2D8DC28(self, node):
		i = self.ReadHeaderSmObjU32(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_3')
		i = self.skipBlockSize(i)
		return i

	def Read_576520B3(self, node):
		i = self.ReadHeaderSmObjU32(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_6589A70E(self, node):
		i = self.ReadHeaderSmObjU32(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_41122E26(self, node):
		i = self.ReadHeaderSmObjU32(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_F04E03FE(self, node):
		i = self.ReadHeaderSmObjU32(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		return i

	###############################
	def ReadHeaderSmItem(self, node, typeName = None):
		i = node.Read_Header0(typeName)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		return i

	def Read_A79EACCF(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		b, i = getBoolean(node.data, i)
		if (b):
			i = self.ReadTransformation3D(node, i)
		return i

	def Read_5194E9A3(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		b, i = getBoolean(node.data, i)
		if (b):
			i = self.ReadTransformation3D(node, i)
		i = self.skipBlockSize(i, 2)
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a2')
		return i

	def Read_41305114(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat32(i, 'f1')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		return i

	def Read_A79EACD2(self, node):
		i = self.ReadHeaderSmItem(node)
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'lst0', 3)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'indices')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'lst1', 3)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst3')
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_A79EACCB(self, node):
		i = self.ReadHeaderSmItem(node)
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'lst0', 3)
		return i

	def Read_A79EACD5(self, node):
		i = self.ReadHeaderSmItem(node)
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_A79EACC7(self, node):
		i = self.ReadHeaderSmItem(node)
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		return i

	def Read_A79EACCC(self, node):
		i = self.ReadHeaderSmItem(node)
		i = node.ReadFloat64A(i, 12, 'a1')
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_A79EACCD(self, node):
		i = self.ReadHeaderSmItem(node)
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat64(i, 'f')
		i = node.ReadBoolean(i, 'b')
		return i

	###############################
	def Read_120284EF(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_31C56502(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_48EB8607(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_440D2B29(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_48EB8608(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadColorRGBA(i, 'Corlor.c0')
		i = node.ReadColorRGBA(i, 'Corlor.diffuse')
		i = node.ReadColorRGBA(i, 'Corlor.c1')
		i = node.ReadColorRGBA(i, 'Corlor.c2')
		i = node.ReadColorRGBA(i, 'Corlor.c3')
		i = node.ReadFloat32(i, 'f')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_B32BF6A3(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_B32BF6A5(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_B32BF6A6(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_B32BF6A9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_4AD05620(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_A8E5AF56(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_B32BF6AB(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_76986821(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b1')
		return i

	def Read_BD1091BF(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b1')
		return i

	def Read_F2FB355D(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadFloat32(i, 'f')
		i = node.ReadBoolean(i, 'b')
		return i

	def Read_B32BF6AC(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat32(i, 'f0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadUInt16(i, 'u16_1')
		n, i = getUInt16(node.data, i)
		i = node.ReadFloat64A(i, n, 'a1')
		i = node.ReadFloat64(i, 'f1')
		i = node.ReadFloat32(i, 'f2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a2')
		return i

	def Read_2398B4EF(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_46DFA29A(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a0')
		if (self.version > 2010):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_093834F3(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadChildRef(i, 'ref_4')
		return i

	def Read_02F8872D(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt8A(i, 2, 'a0')
		r, i = getUInt32(node.data, i)
		c, i = getUInt32(node.data, i)
		a = []
		while (r > 0):
			b, i = getUInt32A(node.data, i, c) # RGBA color information
			a.append(b)
			r -= 1
		node.set('a1', a, VAL_UINT32)
		i = node.ReadUInt16A(i, 3, 'a2')
		return i

	def Read_EF1E3BE5(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_FONT_, 'lst0')
		return i

	def Read_946501D5(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'attrs')
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32A(i, 5, 'a1')
		if (self.version < 2024):
			i = node.ReadList2(i, importerSegNode._TYP_F64_F64_U32_U8_U8_U16_, 'lst0')
		else:
			i = node.ReadList2(i, importerSegNode._TYP_F64_F64_U32_U8_U8_U16_U8_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_2D(i, 'a2')
		i = self.skipBlockSize(i, 2)
		i = self.ReadTransformation3D(node, i)
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b1')
		i = node.ReadFloat32A(i, 4, 'a4')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64_3D(i, 'a5')
		i = node.ReadFloat32A(i, 5, 'a6')
		i = node.ReadUInt32A(i, 2, 'a7')
		i = node.ReadFloat64_2D(i, 'a8')
		# f f f f f f f f f f f f f f f f f
		return i
