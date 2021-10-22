# -*- coding: utf-8 -*-

from importerSegment   import SegmentReader
from importerUtils     import *
from importerConstants import VAL_UINT32

import importerSegNode

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class SheetDcReader(SegmentReader):
	def __init__(self, segment):
		super(SheetDcReader, self).__init__(segment)

	'''
	R: Reference to section
	L: unsigned int 32 bit (UInt32)
	H: unsigned int 16 bit (UInt16)
	B: boolean
	U: UID
	@: UTF-16LE encoded Text with UInt32 bit length information at the beginning
	x: UInt32 block size info (only v2010)

	'''
	def ReadHeaderDc(self, node, typeName = None):
		# [L H x R L x]
		i = node.Read_Header0(typeName)
		if (node.get('hdr').x > 0):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadUInt32(i, 'flags')
		else:
			i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		return i

	def Read_D37C90CD(self, node):
		# [L H x R L x U @ 2[R] L L L x R L x x L 2[R] R R L B B 2[R] 2[R] 2[R] R L]
		i = self.ReadHeaderDc(node)
		i = node.ReadUUID(i, 'uid')
		i = node.ReadLen32Text16(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadBoolean(i, 'b1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst3')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst4')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadUInt32(i, 'u32_4')
		return i

	def Read_90874D75(self, node):
		#[L H x R L x U R L]
		i = self.ReadHeaderDc(node)
		i = node.ReadUUID(i, 'uid')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def ReadHeaderDcObject(self, node, typeName = None):
		## [L H x R L x R L x x (L)?2019 ]
		i = self.ReadHeaderDc(node, typeName)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i, 2)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		return i

	def Read_0675182E(self, node):
		# [L H x R L x R L x x (L)?2019 L]
		i = self.ReadHeaderDcObject(node)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_2640F4EB(self, node):
		# [L H x R L x R L x x (L)?2019 L]
		i = self.ReadHeaderDcObject(node)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_1D9FF49F(self, node):
		# [L H x R L x R L x x (L)?2019 L L L]
		i = self.ReadHeaderDcObject(node)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_D7D20B65(self, node):
		# [L H x R L x R L x x (L)?2019 L L L]
		i = self.ReadHeaderDcObject(node)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadUInt32(i, 'u32_4')
		return i

	def Read_1FBB3C01(self, node):
		# [L H x R L x R L x x (L)?2019 d d d d L L L f f f f x B @ L L L L 2[R] 2[R] @ L[13] B[3] 2[R] H H]
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i, 2)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadFloat64A(i, 4, 'a0')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadFloat32A(i, 4, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		if (self.version > 2015): i += 12 # skip Float32[3]
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadUInt32A(i, 4, 'a3')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadUInt32A(i, 13, 'a4')
		i = node.ReadUInt8A(i, 3, 'a5')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		i = node.ReadLen32Text16(i, 'txt_1')
		i = node.ReadUInt32A(i, 2, 'a6')
		i = self.skipBlockSize(i)
		return i

	def Read_62A8E6A6(self, node):
		# [L H x R L x R L x L x x L 2[R] x L B x B x L d d d L H 2[R] L L L L L L L L L L B R L L L L L L x d d d d x (2[R]?2011]
		i = self.ReadHeaderDc(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i, 2)
		n,j = getUInt32(node.data, i)
		if (n == 0xFFFFFFFF): i += 4
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_5')
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadUInt32(i, 'u32_6')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt32A(i, 10, 'a1')
		i = node.ReadBoolean(i, 'b2')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 6, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 4, 'a3')
		i = self.skipBlockSize(i)
		if (self.version > 2010):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		return i

	def Read_E679C2B1(self, node):
		# [L H x R L x R L x L x x L 2[R] x L B x B x L d d d L H 2[R] L L L L L L L L L L B R L L L L L L x L]
		i = self.ReadHeaderDc(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_5')
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadUInt32(i, 'u32_6')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt32A(i, 10, 'a1')
		i = node.ReadBoolean(i, 'b2')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 6, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_7')
		return i

	def Read_90874D63(self, node):
		# [L H x (RL|H) x R 2[R] 6[@:R] L L (L)?2013 L L 6[U:L] 6[U:R] R 2[R] R]
		i = self.ReadHeaderDc(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'objects')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_X_REF_, 'parameters')
		i = node.ReadUInt32A(i, 2, 'a1')
		if (self.version > 2012): i += 4
		i = node.ReadUInt32A(i, 2, 'a2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_UID_UINT32_, 'lst1') # used classID with count
		i = node.ReadList6(i, importerSegNode._TYP_MAP_UID_X_REF_, 'lst2')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst3')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_866CBE44(self, node):
		# [L H x R L x R L x x x (l)?2019 L x]
		i = self.ReadHeaderDc(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i, 3)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		return i

	def Read_866CBE45(self, node):
		# [L H x R L x R L x x x (l)?2019 L x]
		i = self.ReadHeaderDc(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i, 3)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		return i

	def Read_CE52DF3E(self, node):
		# [L H x R L x R L x x x L x L R d d d 2[R] 2[R]]
		i = self.ReadHeaderDc(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i, 3)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		if (self.version > 2017): i+= 4 # skip 00 00 00 00
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		return i

	def Read_90874D26(self, node):
		# [L H x R L x R L x x x (l)?2019 @ L R R d d H H ]
		i = self.ReadHeaderDc(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i, 3)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadLen32Text16(i, 'txt_0')
		i += 4
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadFloat64_2D(i, 'a1')
		i = node.ReadUInt16A(i, 2, 'a2')
		return i

	def Read_BB1DD5DF(self, node):
		# [L H x R L x R L x x x (l)?2019 @ L L L ]
		i = self.ReadHeaderDc(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i, 3)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadLen32Text16(i, 'txt_0')
		i += 4
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_90874D28(self, node):
		# [L H x R L x R L x x x (L L)?2011 B]
		i = self.ReadHeaderDc(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i, 3)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		if (self.version > 2010):
			i = node.ReadUInt32A(i, 2, 'u32')
		else:
			node.set('u32', (0, 0), VAL_UINT32)
		i = node.ReadUInt8(i, 'b0')
		return i

	def Read_22CB4259(self, node):
		# [L H x R L x l x x L 2[R] x B L x B x L @ @ L L L 2[R] 2[R] 2[R] 2[R] 2[R] 2[R] 2[R] L L R 2[R] L @ R L L L d d d d R d d d d d d d L x d d d d d d d d d x d d d d d x R R L L x 6[L:L] x R R L H L @ H x L L L d d d]
		i = self.ReadHeaderDc(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadUInt32(i, 'u32_3')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		i = node.ReadLen32Text16(i, 'iam') # assembly file path
		i = node.ReadLen32Text16(i, 'txt_1')
		if (self.version < 2016): i += 4 # skip UInt32
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst3')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst4')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst5')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst6')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst7')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst8')
		i = node.ReadUInt32(i, 'u32_5')
		i = node.ReadLen32Text16(i, 'txt_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 3, 'a3')
		i = node.ReadFloat64A(i, 4, 'a4')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadFloat64A(i, 7, 'a5')
		i = node.ReadUInt32(i, 'u32_6')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 9, 'a6')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 5, 'a7')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadUInt32A(i, 2, 'a8')
		i = self.skipBlockSize(i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst9')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadUInt32(i, 'u32_7')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_8')
		i = node.ReadLen32Text16(i, 'txt_3')
		i = node.ReadUInt16(i, 'u16_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a9')
		i = node.ReadFloat64_3D(i, 'a10')
		if (self.version > 2010): i += 4
		return i

	def Read_F8A77A04(self, node):
		# [L H x L x f f H (L)?2011]
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'x')
		i = node.ReadUInt16(i, 'u16_0')
		if (self.version > 2010):
			i = node.ReadUInt32(i, 'u32_1')
		else:
			node.set('u32_1', 0, VAL_UINT32)
		return i

	def Read_E3CF2678(self, node):
		# [L H x 6[] 6[] 6[]
		i = node.Read_Header0()
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst2')
		return i