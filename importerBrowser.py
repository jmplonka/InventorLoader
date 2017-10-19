# -*- coding: utf8 -*-

'''
importerBrowser.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader, checkReadAll
from importerSegNode import AbstractNode, BrowserNode
from importerUtils   import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.1'
__status__      = 'In-Development'

class BrowserReader(SegmentReader):

	def __init__(self):
		super(BrowserReader, self).__init__(True)

	def createNewNode(self):
		return BrowserNode()

	def skipDumpRawData(self):
		return True

	def Read_Str53(self, node):
		i = node.ReadLen32Text16(0)
		i = node.ReadUInt8A(i, 5, 'Str53.a0')
		if (node.get('Str53.a0')[4] == 0):
			node.set('Str53.u16_0', 0)
		else:
			i = node.ReadUInt16(i, 'Str53.u16_0')
		i = node.ReadUInt16A(i, 3, 'Str53.a1')

		i = self.skipBlockSize(i)

		return i

	def Read_Str01(self, offset, node):
		i = node.ReadLen32Text16(offset)
		i = node.ReadLen32Text16(i, 'Str01.str1')
		i = node.ReadUInt8(i, 'Str01.u8_0')

		return i

	def Read_Str23(self, offset, node):
		i = node.ReadLen32Text16(offset, 'Str23.str0')
		i = node.ReadLen32Text16(i, 'Str23.str1')
		i = node.ReadSInt32A(i, 3, 'Str23.a0')
		i = self.skipBlockSize(i)

		return i

	def Read_664(self, offset, node):
		i = node.ReadUInt32(offset, 'key')
		i = node.ReadUInt16A(i, 4, '664.a0')
		i = node.ReadUInt8(i, '664.u8_0')
		i = node.ReadUInt16A(i, 6, '664.a1')
		i = node.ReadUInt8(i, '664.u8_1')
		i = node.ReadUInt16A(i, 4, '664.a2')
		i = node.ReadUInt8(i, '664.u8_2')
		i = self.skipBlockSize(i)

		return i

	def Read_09CB9718(self, node):
		i = node.ReadUInt32A(0, 3, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)

		return i

	def Read_0E7F99A4(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.Read_Str23(i, node)

		return i

	def Read_0F590179(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.Read_Str23(i, node)

		return i

	def Read_11D83D80(self, node):
		vers = getFileVersion()

		if (vers < 2011):
			node.content += ' \'\' Str53.a0=[00,00,00,00,00] Str53.a1=[0000,0000,0000] lst0={'
			a0, i = getUInt32A(node.data, 0, 3)
			if (a0[0] > 0):
				node.content += (IntArr2Str(a0[1:], 4))
			sep = ''
			lst0 = []
			j = 0
			while (j < a0[0]):
				j += 1
				a2, i = getUInt16A(node.data, i, 4)
				node.content += sep + IntArr2Str(a2, 4)
				sep = ','
				lst0.append(a2)
			node.content += '}'
			node.set('lst0', lst0)
		else:
			i = self.Read_Str53(node)
			i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')

		if (vers < 2011):
			dummy, i = getUInt8A(node.data, i, 15)

		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_189B3560(self, node):
		vers = getFileVersion()
		i = 0

		i = node.ReadUInt16A(i, 3, 'a0')
		if (vers < 2011):
			if (node.get('a0')[0] == 0):
				a1 = [0, 0, 0]
			else:
				i = node.ReadUInt8A(i, 3, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_18BAA333(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)

		return i

	def Read_19910142(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_1B16984A(self, node):
		i = node.ReadUInt16A(0, 3, 'a0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_1D8866A4(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_240BF169(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_2AC37C16(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_2B398DFB(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_33DDFC82(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_3E54E601(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)

		return i

	def Read_44664C6F(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_44DBCB35(self, node):
		i = node.ReadUInt32(0, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)

		return i

	def Read_4A156CBC(self, node):
		node.typeName = '3dSketch'

		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_50C73580(self, node):
		node.typeName = '3dObject'

		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_5')

		if (getFileVersion() > 2016):
			dummy, i = getUInt32A(node.data, i, 2)

		return i

	def Read_67361CCF(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.Read_Str23(i, node)

		return i

	def Read_69A4ED42(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.Read_Str23(i, node)

		return i

	def Read_6CDD3AB0(self, node):
		node.typeName = 'BrowserFolder'

		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_716B5CD1(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a0')

		return i

	def Read_74EEF6B7(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_761C4FA0(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_7DFCC817(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)

		return i

	def Read_7DFCC818(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadLen32Text16(i, 'str0')
		i = node.ReadUInt32A(i, 2, 'a0')

		return i

	def Read_82EBFBD9(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_84FA6B6C(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8A(i, 3, 'a0')
		i = node.ReadLen32Text16(i, 'str0')

		return i

	def Read_8BF242F4(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 2, 'a0')

		return i

	def Read_8C5986A1(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a0')

		return i

	def Read_9B451345(self, node):
		i = node.ReadUInt32(0, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = node.ReadParentRef(i)

		return i

	def Read_9E77CCC1(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)

		return i

	def Read_9E77CCC3(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a4')
		i = self.skipBlockSize(i)

		return i

	def Read_9E77CCC5(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)

		return i

	def Read_9E77CCC7(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)

		return i

	def Read_A1DF3B79(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_B251BFC0(self, node):
		'''
		Entry Manager
		'''
		node.typeName = 'EntryManager'
		i = node.Read_Header0()
		i = node.ReadList7(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_B4278FFF(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = node.ReadUInt32A(i, 2, 'a0')

		return i

	def Read_B75AE9EF(self, node):
		i = 0

		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8(i, 'u8_0')
		if (node.get('u8_0') > 0):
			i = node.ReadUInt16A(i, 1084, 'aX')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i, 'str0')
		i = node.ReadLen32Text16(i, 'str1')
		i = node.ReadSInt32A(i, 4, 'a1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadLen32Text16(i, 'str2')
		i = node.ReadLen32Text16(i, 'str3')
		i = node.ReadSInt32A(i, 2, 'a2')

		return i

	def Read_BAF2D1C6(self, node):
		node.typeName = 'SpiralCurve'

		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_CBBCFA51(self, node):
		# Only found in Bauteil001 and Bauteil002
		i = 0

		i = node.ReadParentRef(i)
		i = node.ReadUInt16A(i, 8, 'a0')

		return i

	def Read_CF604E8B(self, node):
		# Only found in Part7-bida-megalh!
		i = node.Read_Header0()
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadList2(i,  AbstractNode._TYP_1D_UINT32_, 'lst0')
		i = node.ReadSInt32A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_D2B2DF09(self, node):
		# Only found in Bauteil001 and Bauteil002
		i = node.Read_Header0()
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList2(i,  AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_D81CDE47(self, node):
		node.typeName = 'NBxEntry'
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'str0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 3, 'a4')
		i = node.ReadUInt8(i, 'u8_4')

		return i

	def Read_D95A2DF2(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadLen32Text16(i, 'str2')
		i = node.ReadLen32Text16(i, 'str3')
		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_DD1ADF96(self, node):
		node.typeName = 'Solid'

		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a5')

		return i

	def Read_DF9CA7B0(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadList4(i, AbstractNode._TYP_STRING16_, 'lst0')
		i = node.ReadUInt16A(i, 3, 'a1')

		return i

	def Read_E82BC461(self, node):
		vers = getFileVersion()

		i = node.ReadUInt32(0, 'u32_0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst1')
		if (vers > 2015):
			i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst2')
		else:
			i = node.ReadChildRef(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8A(i, 5, 'a1')
		if (node.get('a1')[4] == 0):
			node.set('u16_0', 0)
		else:
			i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt16A(i, 3, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst3')
		i = node.ReadUInt16A(i, 6, 'a3')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 6, 'a4')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadUInt16A(i, 4, 'a5')
		i = node.ReadUInt8(i, 'u8_3')
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		if (vers != 2011):
			i = node.ReadSInt32A(i, 2, 'a5')
		else:
			node.set('a5', [0, 0])

		return i

	def Read_F757BC76(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i)
		i = node.ReadChildRef(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadChildRef(i)
		i = node.ReadUInt16A(i, 8, 'a2')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'str1')
		i = node.ReadLen32Text16(i, 'str2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt8A(i, 10, 'a4')

		return i

	def Read_F7676AB0(self, node):
		node.typeName = 'Sketch'

		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_F7676AB1(self, node):
		i = node.ReadUInt32(0, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 5, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_F7676AB2(self, node):
		node.typeName = 'Feature'

		vers = getFileVersion()
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32(i, 'u32_0')
		if (vers > 2011):
			i = node.ReadSInt32A(i, 2, 'a5')
		else:
			node.set('a5', [0, 0])

		return i

	def Read_F99B4BFD(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_FCF044C3(self, node):
		i = self.Read_Str53(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)

		return i
