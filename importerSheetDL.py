# -*- coding: utf-8 -*-

from importerSegment import SegmentReader
from importerUtils   import *
import importerSegNode

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class SheetDlReader(SegmentReader):
	def __init__(self, segment):
		super(SheetDlReader, self).__init__(segment)

	def Read_48EB8607(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_48EB8608(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadMaterial(i, 3)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_4D6F55DA(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_B32BF6A3(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_F2FB355D(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadFloat32(i, 'f0')
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_B32BF6A5(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_B32BF6AB(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_B32BF6AC(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat32(i, 'f0')
		i = node.ReadSInt16A(i, 2, 'a0')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadUInt16(i, 'u16_1')
		n, i = getUInt16(node.data, i)
		i = node.ReadFloat64A(i, n, 'a1')
		i = node.ReadFloat32_3D(i, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32A(i, 2, 'a3')
		return i

	def Read_580A7D6D(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst0')
		return i

	def Read_A8E5AF56(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_4AD05620(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_57DC00F8(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadSInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		e = None
		if (self.version < 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
			i = node.ReadChildRef(i, 'ref_0')
			### l L l R B L l 2[R] d d L
			i += 1 # skip BOOL
			b, i = getBoolean(node.data, i)
			if (b):
				e, i = self.ReadEdge(node, i)
				node.set('e', e)
			s1, i = getSInt32(node.data, i)
			u1, i = getUInt32(node.data, i)
			i += 4 # skip FF FF FF FF
			i = node.ReadChildRef(i, 'ref_1')
			i += 1 # skip BOOL
			u2, i = getUInt32(node.data, i)
			s0, i = getSInt32(node.data, i)
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
			a0, i = getFloat64A(node.data, i, 2)
			u3, i = getUInt32(node.data, i)
		else:
			i = node.ReadChildRef(i, 'ref_0')
			u1, i = getUInt32(node.data, i)
			i = node.ReadChildRef(i, 'ref_1')
			u2, i = getUInt32(node.data, i)
			s0, i = getSInt32(node.data, i)
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
			u3, i = getUInt32(node.data, i)
			s1, i = getSInt32(node.data, i)
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
			a0, i = getFloat64A(node.data, i, 2)
			b, i = getBoolean(node.data, i)
			if (b):
				e, i = self.ReadEdge(node, i)
				node.set('e', e)
		if (e):
			node.content += u" s32_0=%s s32_1=%s u32_1=%04X u32_2=%04X u32_3=%04X a0=(%g,%g) e=%s" %(s0, s1, u1, u2, u3, a0[0], a0[1], e)
		else:
			node.content += u" s32_0=%s s32_1=%s u32_1=%04X u32_2=%04X u32_3=%04X a0=(%g,%g)" %(s0, s1, u1, u2, u3, a0[0], a0[1])
		node.set('s32_0', s0)
		node.set('s32_1', s1)
		node.set('u32_1', u1)
		node.set('u32_2', u2)
		node.set('u32_3', u3)
		node.set('a0', a0)
		return i

	def Read_46DFA29A(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadSInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		if (self.version > 2010):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0') # ref to parent???
		return i

	def Read_73271607(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadSInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0') # ref to parent???
		return i

	def Read_F8109235(self, node):
		i = self.skipBlockSize(0, 2)
		i = node.ReadSInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_371C2497(self, node):
		i = self.skipBlockSize(0, 3)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	####################
	def Read_837EFBB8(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_00')
		i = node.ReadChildRef(i, 'ref_01')
		i = node.ReadChildRef(i, 'ref_02')
		i = node.ReadChildRef(i, 'ref_03')
		i = node.ReadChildRef(i, 'ref_04')
		i = node.ReadChildRef(i, 'ref_05')
		i = node.ReadChildRef(i, 'ref_06')
		i = node.ReadChildRef(i, 'ref_07')
		i = node.ReadChildRef(i, 'ref_08')
		i = node.ReadChildRef(i, 'ref_09')
		i = node.ReadChildRef(i, 'ref_10')
		i = node.ReadChildRef(i, 'ref_11')
		i = node.ReadChildRef(i, 'ref_12')
		i = node.ReadChildRef(i, 'ref_13')
		i = node.ReadChildRef(i, 'ref_14')
		i = node.ReadChildRef(i, 'ref_15')
		i = node.ReadChildRef(i, 'ref_16')
		i = node.ReadChildRef(i, 'ref_17')
		i = node.ReadChildRef(i, 'ref_18')
		i = node.ReadChildRef(i, 'ref_19')
		i = node.ReadChildRef(i, 'ref_20')
		return i

	def Read_98536631(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 5, 'a0')
		return i

	def Read_CFCE885D(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_SINT32_A_, 'lst0', 2)
		i = node.ReadList2(i, importerSegNode._TYP_UINT16_, 'lst0')
		return i

	def Read_9EC607A4(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_, 'lst0')
		return i

	def Read_9943DE5B(self, node):
		i = node.Read_Header0()
		if (self.version < 2012):
			b0, i = getBoolean(node.data, i)
			i = node.ReadChildRef(i, 'ref_0')
			b1, i = getBoolean(node.data, i)
			a1, i = getFloat64A(node.data, i, 3)
			a2, i = getFloat64A(node.data, i, 3)
			b2, i = getBoolean(node.data, i)
			a0, i = getFloat64A(node.data, i, 3)
			u0, i = getUInt32(node.data, i)
		else:
			b0, i = getBoolean(node.data, i)
			i = node.ReadChildRef(i, 'ref_0')
			b2, i = getBoolean(node.data, i)
			b1, i = getBoolean(node.data, i)
			a0, i = getFloat64A(node.data, i, 3)
			u0, i = getUInt32(node.data, i)
			i += 4 #u1, i = getUInt32(node.data, i)
			a1, i = getFloat64A(node.data, i, 3)
			a2    = (0., 0., 0.)
		node.set('b0', b0)
		node.set('b1', b1)
		node.set('b2', b2)
		node.set('u32_0', u0)
		node.set('a0', a0)
		node.set('a1', a1)
		node.set('a2', a2)
		node.content += u" b0=%s b1=%s b2=%s u32_0=%04X a0=(%g,%g,%g) a1=(%g,%g,%g) a2=(%g,%g,%g)" %(b0, b1, b2, u0, a0[0], a0[1], a0[2], a1[0], a1[1], a1[2], a2[0], a2[1], a2[2])
		i = node.ReadList2(i, importerSegNode._TYP_SINT32_A_, 'lst0', 2)
		return i

	def Read_4B57DC56(self, node):
		i = node.Read_Header0('Ellipse2D')
		i = node.ReadUInt32(i, 'flags')
		i = node.ReadChildRef(i, 'styles')
		i = node.ReadChildRef(i, 'numRef')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_2D(i, 'c')
		i = node.ReadFloat64(i, 'b')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadFloat64_2D(i, 'dB')
		i = node.ReadFloat64_2D(i, 'dA')
		i = node.ReadFloat64(i, 'startAngle')
		i = node.ReadFloat64(i, 'sweepAngle')
		return i

	####################
	def ReadHeaderDL(self, node, typeName = None):
		i = node.Read_Header0(typeName)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_A79EACCB(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'lst0', 3)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_A79EACD2(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'lst0', 3)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst3')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst4')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_41305114(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat32(i, 'f0')
		i = node.ReadUInt16A(i, 3, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_A79EACCC(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadFloat64A(i, 12, 'a1')
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_A79EACCD(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadFloat64A(i, 7, 'a1')
		i = node.ReadBoolean(i, 'b1')
		return i

	def Read_AFD5CEEB(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadFloat64A(i, 13, 'a1')
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_A79EACC7(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat64_3D(i, 'a2')
		return i

	def Read_87E26131(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat64_3D(i, 'a2')
		i = self.skipBlockSize(i)
		n, i = getUInt32(node.data, i)
		i = node.ReadFloat64A(i, n, 'a3')
		i = node.ReadFloat64(i, 'f0')
		return i

	def Read_A79EACD5(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat64_3D(i, 'a2')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_D3A55701(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadUInt32A(i, 3, 'a1') # 01 00 00 00 00 00 00 00 03 00 00 00 d
		i = node.ReadFloat64(i, 'tolerance')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadFloat64A(i, cnt, 'a4')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, 2, 'a5')
		i = node.ReadFloat64A(i, cnt, 'a6')
		i = self.ReadFloat64Arr(node, i, 2, 'knots') # knots
		i = node.ReadFloat64(i, 'f0')
		i = node.ReadUInt32A(i, 2, 'a')
		i = node.ReadFloat64A(i, 3, 'a9')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_D3A55702(self, node):
		i = self.ReadHeaderDL(node)
		i = node.ReadUInt32A(i, 3, 'a1') # 01 00 00 00 00 00 00 00 03 00 00 00 d
		i = node.ReadFloat64(i, 'tolerance')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadFloat64A(i, cnt, 'a4')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, 2, 'a5')
		i = node.ReadFloat64A(i, cnt, 'a6')
		i = self.ReadFloat64Arr(node, i, 3, 'knots') # knots
		i = node.ReadFloat64(i, 'f0')
		i = node.ReadUInt32A(i, 2, 'a')
		i = node.ReadFloat64A(i, 2, 'a9')
		return i

	####################
	def ReadHeaderTransform(self, node, typeName = None):
		i = self.ReadHeaderDL(node, typeName)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		b, i = getBoolean(node.data, i)
		if (b):
			i = self.ReadTransformation3D(node, i)
		return i

	def Read_A79EACCF(self, node):
		i = self.ReadHeaderTransform(node)
		return i

	def Read_A979CDC5(self, node):
		i = self.ReadHeaderTransform(node)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadBoolean(i, 'b0')
		return i
