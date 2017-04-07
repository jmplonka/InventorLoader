#!/usr/bin/env python

'''
importerBrowser.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader, checkReadAll, ReadChildRef, ReadParentRef, skipBlockSize
from importerClasses import BrowserNode
from importerUtils   import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class BrowserReader(SegmentReader):

	def __init__(self):
		super(BrowserReader, self).__init__(True)

	def createNewNode(self):
		return BrowserNode()

	def skipDumpRawData(self):
		return True

	def Read_Str53(self, block, node):
		i = self.ReadLen32Text16(block, 0, node)
		i = self.ReadUInt8A(block, i, 5, node, 'Str53.a0')
		if (node.get('Str53.a0')[4] == 0):
			node.set('Str53.u16_0', 0)
		else:
			i = self.ReadUInt16(block, i, node, 'Str53.u16_0')
		i = self.ReadUInt16A(block, i, 3, node, 'Str53.a1')

		i = skipBlockSize(block, i)

		return i

	def Read_Str01(self, block, offset, node):
		i = offset

		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadLen32Text16(block, i, node, 'Str01.str1')
		i = self.ReadUInt8(block, i, node, 'Str01.u8_0')

		return i

	def Read_Str23(self, block, offset, node):
		i = offset

		i = self.ReadLen32Text16(block, i, node, 'Str23.str0')
		i = self.ReadLen32Text16(block, i, node, 'Str23.str1')
		i = self.ReadSInt32A(block, i, 3, node, 'Str23.a0')

		i = skipBlockSize(block, i)

		return i

	def Read_664(self, block, offset, node):
		i = offset

		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadUInt16A(block, i, 4, node, '664.a0')
		i = self.ReadUInt8(block, i, node, '664.u8_0')
		i = self.ReadUInt16A(block, i, 6, node, '664.a1')
		i = self.ReadUInt8(block, i, node, '664.u8_1')
		i = self.ReadUInt16A(block, i, 4, node, '664.a2')
		i = self.ReadUInt8(block, i, node, '664.u8_2')

		i = skipBlockSize(block, i)

		return i

	def Read_09cb9718(self, node, block):
		i = self.ReadUInt32A(block, 0, 3, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_0e7f99a4(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadSInt32(block, i, node, 's32_0')
		i = self.Read_Str23(block, i, node)

		checkReadAll(node, i, len(block))
		return

	def Read_0f590179(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadSInt32(block, i, node, 's32_0')
		i = self.Read_Str23(block, i, node)

		checkReadAll(node, i, len(block))
		return

	def Read_11d83d80(self, node, block):
		vers = getFileVersion()

		if (vers < 2011):
			i = self.ReadUInt32A(block, 0, 3, node, 'a0')
			a0 = node.get('a0')
			if (a0[0] > 0):
				node.content += ' {' + (IntArr2Str(a0[1:], 4))
			sep = ''
			lst0 = []
			j = 0
			while (j < a0[0]):
				j += 1
				a2, i = getUInt16A(block, i, 4)
				node.content += sep + IntArr2Str(a2, 4)
				sep = ','
				lst0.append(a2)
			if (a0[0] > 0):
				node.content += '}'
			node.set('lst0', lst0)
		else:
			i = self.Read_Str53(block, node)
			i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')

		if (vers < 2011):
			dummy, i = getUInt8A(block, i, 15)

		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_189b3560(self, node, block):
		vers = getFileVersion()
		i = 0

		i = self.ReadUInt16A(block, i, 3, node, 'a0')
		if (vers < 2011):
			if (node.get('a0')[0] == 0):
				a1 = [0, 0, 0]
			else:
				i = self.ReadUInt8A(block, i, 3, node, 'a1')
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_18baa333(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)

		checkReadAll(node, i, len(block))
		return

	def Read_19910142(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_1b16984a(self, node, block):
		i = self.ReadUInt16A(block, 0, 3, node, 'a0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadList6(block, i, node, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_1d8866a4(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_240bf169(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_2ac37c16(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_2b398dfb(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_33ddfc82(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_3e54e601(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_44664c6f(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_44dbcb35(self, node, block):
		i = self.ReadUInt32(block, 0, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = ReadParentRef(block, i, node)

		checkReadAll(node, i, len(block))
		return

	def Read_4a156cbc(self, node, block):
		node.typeName = '3dSketch'

		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_50c73580(self, node, block):
		node.typeName = '3dObject'

		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_5')

		if (getFileVersion() > 2016):
			dummy, i = getUInt32A(block, i, 2)

		checkReadAll(node, i, len(block))
		return

	def Read_67361ccf(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadSInt32(block, i, node, 's32_0')
		i = self.Read_Str23(block, i, node)

		checkReadAll(node, i, len(block))
		return

	def Read_69a4ed42(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadSInt32(block, i, node, 's32_0')
		i = self.Read_Str23(block, i, node)

		checkReadAll(node, i, len(block))
		return

	def Read_6cdd3ab0(self, node, block):
		node.typeName = 'Origin'

		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_716b5cd1(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_74eef6b7(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_761c4fa0(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_7dfcc817(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = self.ReadSInt32(block, i, node, 's32_0')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_7dfcc818(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadSInt32(block, i, node, 's32_0')
		i = self.ReadLen32Text16(block, i, node, 'str0')
		i = self.ReadUInt32A(block, i, 2, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_82ebfbd9(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_84fa6b6c(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt8A(block, i, 3, node, 'a0')
		i = self.ReadLen32Text16(block, i, node, 'str0')

		checkReadAll(node, i, len(block))
		return

	def Read_8bf242f4(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 2, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_8c5986a1(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_9b451345(self, node, block):
		i = self.ReadUInt32(block, 0, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = ReadParentRef(block, i, node)

		checkReadAll(node, i, len(block))
		return

	def Read_9e77ccc1(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.ReadUInt16A(block, i, 2, node, 'a0')
		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_9e77ccc3(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 4, node, 'a4')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_9e77ccc5(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_9e77ccc7(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_a1df3b79(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_b251bfc0(self, node, block):
		'''
		Entry Manager
		'''
		i = self.Read_Header0(block, node)
		i = self.ReadList7(block, i, node, 'lst0')
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_b4278fff(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.ReadUInt32A(block, i, 2, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_b75ae9ef(self, node, block):
		i = 0

		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		if (node.get('u8_0') > 0):
			i = self.ReadUInt16A(block, i, 1084, node, 'aX')
		i = self.ReadUInt16(block, i, node, 'u16_0')
		i = self.ReadLen32Text16(block, i, node, 'str0')
		i = self.ReadLen32Text16(block, i, node, 'str1')
		i = self.ReadSInt32A(block, i, 4, node, 'a1')
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = self.ReadUInt16(block, i, node, 'u16_1')
		i = self.ReadLen32Text16(block, i, node, 'str2')
		i = self.ReadLen32Text16(block, i, node, 'str3')
		i = self.ReadSInt32A(block, i, 2, node, 'a2')

		checkReadAll(node, i, len(block))
		return

	def Read_baf2d1c6(self, node, block):
		node.typeName = 'SpiralCurve'

		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_cbbcfa51(self, node, block):
		# Only found in Bauteil001 and Bauteil002
		i = 0

		i = ReadParentRef(block, i, node)
		i = self.ReadUInt16A(block, i, 8, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_cf604e8b(self, node, block):
		# Only found in Part7-bida-megalh!
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16(block, i, node, 'u16_1')
		i = self.ReadList2(block, i, node,  SegmentReader._TYP_1D_UINT32_, 'lst0')
		i = self.ReadSInt32A(block, i, 2, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_d2b2df09(self, node, block):
		# Only found in Bauteil001 and Bauteil002
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16(block, i, node, 'u16_0')
		i = self.ReadList2(block, i, node,  SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_d81cde47(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadLen32Text16(block, i, node, 'str0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 3, node, 'a4')
		i = self.ReadUInt8(block, i, node, 'u8_4')

		checkReadAll(node, i, len(block))
		return

	def Read_d95a2df2(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = self.Read_Str01(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadSInt32(block, i, node, 's32_0')
		i = self.ReadLen32Text16(block, i, node, 'str2')
		i = self.ReadLen32Text16(block, i, node, 'str3')
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_dd1adf96(self, node, block):
		node.typeName = 'Solid'

		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32A(block, i, 3, node, 'a5')

		checkReadAll(node, i, len(block))
		return

	def Read_df9ca7b0(self, node, block):
		i = self.Read_Header0(block, node)
		i = ReadParentRef(block, i, node)
		i = ReadChildRef(block, i, node)
		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadList4(block, i, node, SegmentReader._TYP_STRING16_, 'lst0')
		i = self.ReadUInt16A(block, i, 3, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_e82bc461(self, node, block):
		vers = getFileVersion()

		i = self.ReadUInt32(block, 0, node, 'u32_0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst1')
		if (vers > 2015):
			i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst2')
		else:
			i = ReadChildRef(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadUInt8A(block, i, 5, node, 'a1')
		if (node.get('a1')[4] == 0):
			node.set('u16_0', 0)
		else:
			i = self.ReadUInt16(block, i, node, 'u16_0')
		i = self.ReadUInt16A(block, i, 3, node, 'a2')
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst3')
		i = self.ReadUInt16A(block, i, 6, node, 'a3')
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = self.ReadUInt16A(block, i, 6, node, 'a4')
		i = self.ReadUInt8(block, i, node, 'u8_2')
		i = self.ReadUInt16A(block, i, 4, node, 'a5')
		i = self.ReadUInt8(block, i, node, 'u8_3')
		i = self.ReadUUID(block, i, node, 'uid0')
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = skipBlockSize(block, i)
		if (vers != 2011):
			i = self.ReadSInt32A(block, i, 2, node, 'a5')
		else:
			node.set('a5', [0, 0])

		checkReadAll(node, i, len(block))
		return

	def Read_f757bc76(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = ReadParentRef(block, i, node)
		i = ReadChildRef(block, i, node)
		i = ReadChildRef(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = ReadChildRef(block, i, node)
		i = self.ReadUInt16A(block, i, 8, node, 'a2')
		i = self.ReadUInt8(block, i, node, 'u8_2')
		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadLen32Text16(block, i, node, 'str1')
		i = self.ReadLen32Text16(block, i, node, 'str2')
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst1')
		i = self.ReadUInt8A(block, i, 10, node, 'a4')

		checkReadAll(node, i, len(block))
		return

	def Read_f7676ab0(self, node, block):
		node.typeName = 'Sketch'

		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_f7676ab1(self, node, block):
		i = self.ReadUInt32(block, 0, node, 'u32_0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = self.ReadUInt16A(block, i, 5, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_f7676ab2(self, node, block):
		node.typeName = 'Extrusion'

		vers = getFileVersion()
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUUID(block, i, node, 'uid_0')
		i = self.ReadUInt32(block, i, node, 'u32_0')
		if (vers > 2011):
			i = self.ReadSInt32A(block, i, 2, node, 'a5')
		else:
			node.set('a5', [0, 0])

		checkReadAll(node, i, len(block))
		return

	def Read_f99b4bfd(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_fcf044c3(self, node, block):
		i = self.Read_Str53(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def HandleBlock(self, file, block, node, seg):
		ntid = node.typeID.time_low
		if (ntid == 0x09cb9718):
			self.Read_09cb9718(node, block)
		elif (ntid == 0x0e7f99a4):
			self.Read_0e7f99a4(node, block)
		elif (ntid == 0x0f590179):
			self.Read_0f590179(node, block)
		elif (ntid == 0x11d83d80):
			self.Read_11d83d80(node, block)
		elif (ntid == 0x189b3560):
			self.Read_189b3560(node, block)
		elif (ntid == 0x18baa333):
			self.Read_18baa333(node, block)
		elif (ntid == 0x19910142):
			self.Read_19910142(node, block)
		elif (ntid == 0x1b16984a):
			self.Read_1b16984a(node, block)
		elif (ntid == 0x1d8866a4):
			self.Read_1d8866a4(node, block)
		elif (ntid == 0x240bf169):
			self.Read_240bf169(node, block)
		elif (ntid == 0x2ac37c16):
			self.Read_2ac37c16(node, block)
		elif (ntid == 0x2b398dfb):
			self.Read_2b398dfb(node, block)
		elif (ntid == 0x33ddfc82):
			self.Read_33ddfc82(node, block)
		elif (ntid == 0x3e54e601):
			self.Read_3e54e601(node, block)
		elif (ntid == 0x44664c6f):
			self.Read_44664c6f(node, block)
		elif (ntid == 0x44dbcb35):
			self.Read_44dbcb35(node, block)
		elif (ntid == 0x4a156cbc):
			self.Read_4a156cbc(node, block)
		elif (ntid == 0x50c73580):
			self.Read_50c73580(node, block)
		elif (ntid == 0x67361ccf):
			self.Read_67361ccf(node, block)
		elif (ntid == 0x69a4ed42):
			self.Read_69a4ed42(node, block)
		elif (ntid == 0x6cdd3ab0):
			self.Read_6cdd3ab0(node, block)
		elif (ntid == 0x716b5cd1):
			self.Read_716b5cd1(node, block)
		elif (ntid == 0x74eef6b7):
			self.Read_74eef6b7(node, block)
		elif (ntid == 0x761c4fa0):
			self.Read_761c4fa0(node, block)
		elif (ntid == 0x7dfcc817):
			self.Read_7dfcc817(node, block)
		elif (ntid == 0x7dfcc818):
			self.Read_7dfcc818(node, block)
		elif (ntid == 0x82ebfbd9):
			self.Read_82ebfbd9(node, block)
		elif (ntid == 0x84fa6b6c):
			self.Read_84fa6b6c(node, block)
		elif (ntid == 0x8bf242f4):
			self.Read_8bf242f4(node, block)
		elif (ntid == 0x8c5986a1):
			self.Read_8c5986a1(node, block)
		elif (ntid == 0x9b451345):
			self.Read_9b451345(node, block)
		elif (ntid == 0x9e77ccc1):
			self.Read_9e77ccc1(node, block)
		elif (ntid == 0x9e77ccc3):
			self.Read_9e77ccc3(node, block)
		elif (ntid == 0x9e77ccc5):
			self.Read_9e77ccc5(node, block)
		elif (ntid == 0x9e77ccc7):
			self.Read_9e77ccc7(node, block)
		elif (ntid == 0xa1df3b79):
			self.Read_a1df3b79(node, block)
		elif (ntid == 0xb251bfc0):
			self.Read_b251bfc0(node, block)
		elif (ntid == 0xb4278fff):
			self.Read_b4278fff(node, block)
		elif (ntid == 0xb75ae9ef):
			self.Read_b75ae9ef(node, block)
		elif (ntid == 0xbaf2d1c6):
			self.Read_baf2d1c6(node, block)
		elif (ntid == 0xcbbcfa51):
			self.Read_cbbcfa51(node, block)
		elif (ntid == 0xcf604e8b):
			self.Read_cf604e8b(node, block)
		elif (ntid == 0xd2b2df09):
			self.Read_d2b2df09(node, block)
		elif (ntid == 0xd81cde47):
			self.Read_d81cde47(node, block)
		elif (ntid == 0xd95a2df2):
			self.Read_d95a2df2(node, block)
		elif (ntid == 0xdd1adf96):
			self.Read_dd1adf96(node, block)
		elif (ntid == 0xdf9ca7b0):
			self.Read_df9ca7b0(node, block)
		elif (ntid == 0xe82bc461):
			self.Read_e82bc461(node, block)
		elif (ntid == 0xf757bc76):
			self.Read_f757bc76(node, block)
		elif (ntid == 0xf7676ab0):
			self.Read_f7676ab0(node, block)
		elif (ntid == 0xf7676ab1):
			self.Read_f7676ab1(node, block)
		elif (ntid == 0xf7676ab2):
			self.Read_f7676ab2(node, block)
		elif (ntid == 0xf99b4bfd):
			self.Read_f99b4bfd(node, block)
		elif (ntid == 0xfcf044c3):
			self.Read_fcf044c3(node, block)
		else:
			self.ReadUnknownBlock(file, node, block, True)
		return