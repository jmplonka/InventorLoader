# -*- coding: utf-8 -*-

'''
importerEeScene.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment import SegmentReader, checkReadAll
import importerSegNode
from importerUtils   import *

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class EeSceneReader(SegmentReader):
	def __init__(self):
		super(EeSceneReader, self).__init__(False)

	def createNewNode(self):
		return importerSegNode.EeSceneNode()

	def skipDumpRawData(self):
		return True

	def Read_120284EF(self, node):
		i = node.ReadUInt32(0, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_13FC8170(self, node): return 0

	def Read_48EB8607(self, node):
		node.typeName = "ObjctStyles"
		i = self.skipBlockSize(0)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'styles')
		return i

	def Read_48EB8608(self, node):
		i = self.ReadHeaderSU32S(node, 'StyleLine2dColor')
		i = node.ReadColorRGBA(i, 'c0')
		i = node.ReadColorRGBA(i, 'c1')
		i = node.ReadColorRGBA(i, 'c2')
		i = node.ReadColorRGBA(i, 'c3')
		i = node.ReadColorRGBA(i, 'c4')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_5194E9A3(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 6, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64A(i, 6, 'a1')
		i = node.ReadUInt32A(i, 3, 'a2')
		return i

	def Read_6C6322EB(self, node):
		i = self.ReadHeaderSU32S(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_2')
		i = self.skipBlockSize(i)
		return i

	def Read_950A4A74(self, node):
		i = node.ReadUInt32A(0, 3, 'a0')
		return i

	def Read_A529D1E2(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_A79EACCB(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'lst0', 3)
		return i

	def Read_A79EACCF(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'flags')
		i = node.ReadChildRef(i, 'ref0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_A79EACD2(self, node):
		i = node.Read_Header0()
		return i

	def Read_AF48560F(self, node):
		i = 0
		return i

	def Read_B32BF6A3(self, node):
		i = 0
		return i

	def Read_B32BF6A2(self, node):
		i = self.ReadHeaderSU32S(node)
		i = node.ReadFloat32A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32A(i, 4, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32A(i, 4, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32A(i, 4, 'a3')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32(i, 'f0')
		i = self.skipBlockSize(i)
		return i

	def Read_B32BF6A6(self, node):
		i = self.ReadHeaderSU32S(node)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_B32BF6A9(self, node):
		i = self.ReadHeaderSU32S(node)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_B91E695F(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32A(i, 4, 'a2')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32A(i, 5, 'a3')
		i = node.ReadList2(i, importerSegNode._TYP_F64_F64_U32_U8_U8_U16_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'a4')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0')
		return i
