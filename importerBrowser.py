# -*- coding: utf-8 -*-

'''
importerBrowser.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment import SegmentReader, checkReadAll
from importerUtils   import *
import importerSegNode

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class BrowserReader(SegmentReader):

	def __init__(self):
		super(BrowserReader, self).__init__(True)

	def createNewNode(self):
		return importerSegNode.BrowserNode()

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
		i = node.ReadUInt32(offset, 'index')
		i = node.ReadUInt16A(i, 4, '664.a0')
		i = node.ReadUInt8(i, '664.u8_0')
		i = node.ReadUInt16A(i, 6, '664.a1')
		i = node.ReadUInt8(i, '664.u8_1')
		i = node.ReadUInt16A(i, 4, '664.a2')
		i = node.ReadUInt8(i, '664.u8_2')
		i = self.skipBlockSize(i)
		return i

	def ReadHeaderStr664(self, node, typeName = None):
		if (typeName is not None):
			node.typeName = typeName
		i = self.Read_Str53(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.Read_664(i, node)
		return i

	def ReadHeader0_664(self, node, typeName = None):
		i = node.Read_Header0(typeName)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		return i

	def Read_09CB9718(self, node):
		i = node.ReadUInt32A(0, 3, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_09CB971A(self, node):
		i = node.ReadUInt32A(0, 2, 'a0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadSInt32A(i, 2, 'a1')
		return i

	def Read_0C775998(self, node):
		i = node.ReadLen32Text16(0)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2018):
			i = node.ReadUInt16(i, 'u16_0')
		else:
			node.content += ' u16_0=001'
			node.set('u16_0', 1)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_0E7F99A4(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.Read_Str23(i, node)
		return i

	def Read_0F590179(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.Read_Str23(i, node)
		return i

	def Read_10B2DF6C(self, node): return 0

	def Read_11D83D80(self, node): # EndOfPart ???
		i = node.ReadLen32Text16(0, 'txt')
		i = node.ReadUInt16A(i, 4, 'a0')
		if (node.get('a0')[2] == 1):
			i = node.ReadUInt16(i, 'u16_0')
		else:
			node.content += u" u16_0=000"
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32A(i, 3, 'a2')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadUInt8(i, 'u8_3')
		i = self.skipBlockSize(i, 8)
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
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_18BAA333(self, node):
		i = self.ReadHeaderStr664(node)
		return i

	def Read_19910142(self, node):
		i = self.ReadHeader0_664(node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		return i

	def Read_1B16984A(self, node):
		i = node.ReadUInt16A(0, 3, 'a0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_1D8866A4(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		return i

	def Read_240BF169(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		return i

	def Read_2AC37C16(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		return i

	def Read_2B398DFB(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		return i

	def Read_330C8EC7(self, node): return 0

	def Read_33DDFC82(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		return i

	def Read_363E8E7D(self, node):
		i = node.ReadLen32Text16(0, 'str0')
		return i

	def Read_3E54E601(self, node):
		i = self.ReadHeaderStr664(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_420BDF59(self, node): return 0

	def Read_44664C6F(self, node):
		i = self.ReadHeader0_664(node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		return i

	def Read_44DBCB35(self, node):
		i = node.ReadUInt32(0, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i, 8)
		i = node.ReadParentRef(i)
		return i

	def Read_46DE5489(self, node): return 0

	def Read_4A156CBC(self, node):
		i = self.ReadHeaderStr664(node, '3dSketch')
		i = self.skipBlockSize(i)
		return i

	def Read_4D0B0CC5(self, node):
		i = node.ReadLen32Text16(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		if (node.get('u8_0') == 1):
			i = node.ReadUInt16(i, 'u16_0')
		else:
			node.content += ' u16_0=000'
			node.set('u16_0', 0)
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_50C73580(self, node):
		i = self.ReadHeaderStr664(node, '3dObject')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_5')

		if (getFileVersion() > 2016):
			dummy, i = getUInt32A(node.data, i, 2)
		return i

	def Read_52879851(self, node): return 0

	def Read_58B90125(self, node):
		i = node.ReadUInt32A(0, 2, 'a0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadSInt32A(i, 2, 'a1')
		return i

	def Read_6531C640(self, node): return 0

	def Read_67361CCF(self, node):
		i = self.ReadHeader0_664(node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.Read_Str23(i, node)
		return i

	def Read_69A4ED42(self, node):
		i = self.ReadHeader0_664(node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.Read_Str23(i, node)
		return i

	def Read_6CDD3AB0(self, node):
		i = self.ReadHeaderStr664(node, 'BrowserFolder')
		i = self.skipBlockSize(i)
		return i

	def Read_716B5CD1(self, node):
		i = self.ReadHeader0_664(node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a0')
		return i

	def Read_74AD7D3C(self, node): return 0

	def Read_74EEF6B7(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		return i

	def Read_761C4FA0(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_7DFCC817(self, node):
		i = self.ReadHeader0_664(node)
		i = self.Read_Str01(i, node)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_7DFCC818(self, node):
		i = self.ReadHeader0_664(node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadLen32Text16(i, 'str0')
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_7FC32FE5(self, node):
		i = node.ReadLen32Text16(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_82EBFBD9(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		return i

	def Read_84FA6B6C(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8A(i, 3, 'a0')
		i = node.ReadLen32Text16(i, 'str0')
		return i

	def Read_87E10017(self, node):
		i = node.ReadLen32Text16(0, 'str0')
		return i

	def Read_89B87C6F(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_8BF242F4(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 2, 'a0')
		return i

	def Read_8C5986A1(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a0')
		return i

	def Read_8E50B102(self, node): return 0

	def Read_93C65F8A(self, node): return 0

	def Read_9632B3FA(self, node): return 0

	def Read_9B451345(self, node):
		i = node.ReadUInt32(0, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = node.ReadParentRef(i)
		return i

	def Read_9C599498(self, node): return 0

	def Read_9E77CCC1(self, node):
		i = self.ReadHeader0_664(node)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_9E77CCC3(self, node):
		i = self.ReadHeader0_664(node, 'PartInterfaceMate')
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a4')
		i = self.skipBlockSize(i)
		return i

	def Read_9E77CCC4(self, node): return 0

	def Read_9E77CCC5(self, node):
		i = self.ReadHeader0_664(node, 'PartInterfaceAngle')
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_9E77CCC6(self, node):
		i = self.ReadHeader0_664(node, 'PartInterfaceTangent')
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_9E77CCC7(self, node):
		i = self.ReadHeader0_664(node, 'PartInterfaceInsert')
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_A1DF3B79(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		return i

	def Read_AC1898AD(self, node): return 0

	def Read_AF64BA30(self, node): return 0

	def Read_B251BFC0(self, node):
		i = node.Read_Header0('EntryManager')
		i = node.ReadList7(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_B4278FFF(self, node):
		i = self.ReadHeaderStr664(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_B75AE9EF(self, node):
		i = node.ReadLen32Text16(0)
		i = node.ReadUInt8(i, 'u8_0')
#		if (node.get('u8_0') > 0):
#			i = node.ReadUInt16A(i, 1084, 'aX')
#		i = node.ReadUInt16(i, 'u16_0')
#		i = node.ReadLen32Text16(i, 'str0')
#		i = node.ReadLen32Text16(i, 'str1')
#		i = node.ReadSInt32A(i, 4, 'a1')
#		i = node.ReadUInt8(i, 'u8_1')
#		i = node.ReadUInt16(i, 'u16_1')
#		i = node.ReadLen32Text16(i, 'str2')
#		i = node.ReadLen32Text16(i, 'str3')
#		i = node.ReadSInt32A(i, 2, 'a2')
		return i

	def Read_BAF2D1C6(self, node):
		i = self.ReadHeaderStr664(node, 'SpiralCurve')
		i = self.skipBlockSize(i)
		return i

	def Read_BF03D5B6(self, node): return 0

	def Read_C0465062(self, node): return 0

	def Read_CBBCFA51(self, node):
		i = node.ReadParentRef(0)
		i = node.ReadUInt16A(i, 8, 'a0')
		return i

	def Read_CF604E8B(self, node):
		# Only found in Part7-bida-megalh!
		i = node.Read_Header0()
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadList2(i,  importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadSInt32A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_D2B2DF09(self, node):
		# Only found in Bauteil001 and Bauteil002
		i = node.Read_Header0()
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList2(i,  importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_D81CDE47(self, node):
		i = self.ReadHeader0_664(node, 'NBxEntry')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'str0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 3, 'a4')
		i = node.ReadUInt8(i, 'u8_4')
		return i

	def Read_D9389A04(self, node): return 0

	def Read_D95A2DF2(self, node):
		i = self.ReadHeader0_664(node)
		i = self.Read_Str01(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadLen32Text16(i, 'str2')
		i = node.ReadLen32Text16(i, 'str3')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_DCB9673A(self, node): return 0

	def Read_DD1ADF96(self, node):
		i = self.ReadHeaderStr664(node, 'Solid')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a5')
		return i

	def Read_DDC7ED24(self, node): return 0

	def Read_DF9CA7B0(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadList4(i, importerSegNode._TYP_STRING8_, 'lst0')
		i = node.ReadUInt16(i, 'u16')
		i = node.ReadLen32Text16(i, 'val')
		return i

	def Read_E079A121(self, node): return 0

	def Read_E14BDF12(self, node): return 0

	def Read_E4B915DD(self, node): return 0

	def Read_E7A52E09(self, node): return 0

	def Read_E7E4F967(self, node): return 0

	def Read_E7EE0A91(self, node): return 0

	def Read_E82BC461(self, node):
		vers = getFileVersion()

		i = node.ReadUInt32(0, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		if (vers > 2015):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst2')
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
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst3')
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

	def Read_E84595D1(self, node): return 0

	def Read_EAFCF33F(self, node): return 0

	def Read_F1EDED3E(self, node): return 0

	def Read_F757BC76(self, node):
		i = node.Read_Header0()
#		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
#		i = node.ReadUInt16A(i, 4, 'a0')
#		i = node.ReadUInt8(i, 'u8_0')
#		i = node.ReadParentRef(i)
#		i = node.ReadChildRef(i)
#		i = node.ReadChildRef(i)
#		i = node.ReadUInt8(i, 'u8_1')
#		i = node.ReadChildRef(i)
#		i = node.ReadUInt16A(i, 8, 'a2')
#		i = node.ReadUInt8(i, 'u8_2')
#		i = node.ReadLen32Text16(i)
#		i = node.ReadLen32Text16(i, 'str1')
#		i = node.ReadLen32Text16(i, 'str2')
#		i = node.ReadUInt32(i, 'u32_0')
#		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
#		i = node.ReadUInt8A(i, 10, 'a4')
		return i

	def Read_F7676AB0(self, node):
		i = self.ReadHeaderStr664(node, 'Sketch')
		i = self.skipBlockSize(i)
		return i

	def Read_F7676AB1(self, node):
		i = node.ReadUInt32(0, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 5, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.Read_664(i, node)
		i = self.skipBlockSize(i)
		return i

	def Read_F7676AB2(self, node):
		i = self.ReadHeaderStr664(node, 'Feature')
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2011):
			i = node.ReadSInt32A(i, 2, 'a5')
		else:
			node.set('a5', [0, 0])
		return i

	def Read_F8EEAD15(self, node):
		i = node.ReadLen32Text16(0, 'txt0')
		return i

	def Read_F99B4BFD(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		return i

	def Read_FCF044C3(self, node):
		i = self.ReadHeaderStr664(node)
		i = self.skipBlockSize(i)
		return i
