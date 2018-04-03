# -*- coding: utf-8 -*-

'''
importerNotebook.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment import SegmentReader, checkReadAll
from importerSegNode import AbstractNode, BRepNode, NodeRef
from importerUtils   import *

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class BRepReader(SegmentReader):
	def __init__(self):
		super(BRepReader, self).__init__(False)

	def createNewNode(self):
		return BRepNode()

	def skipDumpRawData(self):
		return False

	def Read_009A1CC4(self, node): return 0

	def Read_0645C2A5(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_07BA7419(self, node): return 0

	def Read_0811C56E(self, node): return 0

	def Read_09780457(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadParentRef(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_09DABAE0(self, node): return 0

	def Read_0BDC96E0(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_167018B8(self, node): return 0

	def Read_1CC0C585(self, node): return 0

	def Read_2169ED74(self, node): return 0

	def Read_2892C3E0(self, node): return 0

	def Read_31D7A200(self, node): return 0

	def Read_357D669C(self, node): return 0

	def Read_3DE78F81(self, node): return 0

	def Read_481DFC84(self, node):
		i = node.Read_Header0()
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_X_REF_, 'lst0')
		return i

	def Read_4DAB0A79(self, node): return 0

	def Read_5363C623(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_537799E0(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_56A95F20(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_632A4BBA(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt16A(i, 5, 'a1')
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_66085B35(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		return i

	def Read_6985F652(self, node):
		i = node.Read_Header0()
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_X_REF_, 'lst0')
		return i

	def Read_6D0B7807(self, node):
		i = node.Read_Header0()
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_X_REF_, 'lst0')
		return i

	def Read_6F891B34(self, node): return 0

	def Read_6F891B34(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_736C138D(self, node): return 0

	def Read_766EA5E5(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 10, 'a0')
		return i

	def Read_7E5D2868(self, node): return 0

	def Read_821ACB9E(self, node): return 0

	def Read_896A9790(self, node): return 0

	def Read_8E5D4198(self, node): return 0

	def Read_9D2E8361(self, node): return 0

	def Read_D4A52F3A(self, node): return 0

	def Read_A618B833(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, AbstractNode._TYP_UINT32A_, 'lst0', 2)
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_ABD292FD(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_AE0E267A(self, node): return 0

	def Read_AFD4E6A3(self, node): return 0

	def Read_B292F94A(self, node): return 0

	def Read_BA0B8C23(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_0')
		return i

	def Read_BFED36A9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		return i

	def Read_C620657B(self, node):
		i = self.skipBlockSize(0)
		return i

	def Read_CADD6468(self, node):
		i = node.Read_Header0()
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_CC0F7521(self, node):
		node.typeName = 'AcisEntityWrapper'
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_CCC5085A(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_0')
		return i

	def Read_CCE92042(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		cnt, i = getUInt32(node.data, i)
		lst = {}
		j = 0
		while j < cnt:
			u, i = getUInt32(node.data, i)
			r, i = self.ReadNodeRef(node, i, u, NodeRef.TYPE_CHILD)
			lst[u] = r
			j += 1
		return i

	def Read_D797B7B9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_DDA265D6(self, node): return 0

	def Read_E70272F7(self, node): return 0

	def Read_E9132E94(self, node): return 0

	def Read_EA7DA988(self, node):
		i = node.Read_Header0()
		i = node.ReadList8(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_F78B08D5(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
		return i
