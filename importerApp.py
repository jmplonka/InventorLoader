# -*- coding: utf-8 -*-

'''
importerApp.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment import SegmentReader, getNodeType
from importerSegNode import AbstractNode, AppNode
from importerUtils   import *

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class AppReader(SegmentReader):
	def __init__(self):
		super(AppReader, self).__init__(False)
		self.defStyle = None

	def createNewNode(self):
		return AppNode()

	def skipDumpRawData(self):
		return True

	def Read_10389219(self, node): return 0

	def Read_10D6C06B(self, node): return 0

	def Read_11FBECCD(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'material')
		i = node.ReadChildRef(i, 'renderingStyle')
		i = node.ReadChildRef(i, 'cld_2')
		i = node.ReadChildRef(i, 'cld_3')
		i = node.ReadChildRef(i, 'cld_4')
		i = node.ReadChildRef(i, 'cld_5')
		i = node.ReadChildRef(i, 'cld_6')
		i = node.ReadChildRef(i, 'cld_7')
		i = node.ReadChildRef(i, 'cld_8')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		if (getFileVersion() == 2011):
			dummy, i = getUInt32(node.data, i)
		i = node.ReadChildRef(i, 'cld_9')

		self.defStyle = node.get('renderingStyle')

		return i

	def Read_1C4CFF13(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = node.ReadCrossRef(i, 'xref_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i, 'txt_2')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_1E5CBB86(self, node):
		node.typeName = 'Lighting'
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = node.ReadCrossRef(i, 'xref_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32A(i, 4, 'a2')
		i = self.skipBlockSize(i)
		return i

	def Read_2433ABAD(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_276E3074(self, node): return 0

	def Read_2AE52C91(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 2, 'u16_0')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadLen32Text16(i, 'txt_1')
		i = node.ReadLen32Text16(i, 'txt_2')
		return i

	def Read_2F6A0C3F(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_3214005D(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_3235A9B8(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
		i = node.ReadChildRef(i, 'cld_0')
		if (getFileVersion() > 2010):
			i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_345EB9B1(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUUID(i, 'uid_1')
		return i

	def Read_36BC43F4(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = node.ReadCrossRef(i, 'xref_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xref_0')
		i = self.skipBlockSize(i)

		return i

	def Read_37186901(self, node):
		i = node.Read_Header0()
		# i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		# i = self.skipBlockSize(i)
		# i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_422ECBCE(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		return i

	def Read_42A65DAA(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_440F63D1(self, node):
		i = node.Read_Header0()
		return i

	def Read_461E402F(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_473180FD(self, node): return 0

	def Read_55231213(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_5C30CDF2(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_5C30CDF6(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_5C30CE1D(self, node):
		i = node.Read_Header0()
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_5F9D0021(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst1')
		return i

	def Read_5F9D0025(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_5F9D0026(self, node):
		i = node.Read_Header0()
		return i

	def Read_5F9D0029(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_5F9D002B(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_61B5E2D1(self, node):
		i = node.ReadList2(0, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_6759D86E(self, node):
		node.typeName = 'Material'
		vers = getFileVersion()
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadLen32Text16(i)
		if (vers < 2013):
			i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = self.skipBlockSize(i)
		if (vers > 2012):
			i = node.ReadUInt16(i, 'u16_0')
			i = node.ReadLen32Text16(i, 'txt_1')
			i = node.ReadLen32Text16(i, 'txt_2')
			i = node.ReadLen32Text16(i, 'txt_3')
			i = node.ReadLen32Text16(i, 'txt_4')
			i = node.ReadUInt16A(i, 2, 'a2')
			i = node.ReadUUID(i, 'uid_0')
			node.content += ' u16_0=0000 txt_1=\'\' txt_2=\'\' txt_3=\'\' txt_4=\'\' a2=[0000,0000] uid_0=None'
		i = node.ReadFloat64A(i, 4, 'a3')
		i = node.ReadFloat64A(i, 4, 'a4')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'xref_0')

		if (vers > 2011):
			i = node.ReadLen32Text16(i, 'txt_5')

		a0, j = getUInt8A(node.data, i, len(node.data) - i)
		if (len(a0) > 0):
			logError(u"%s\t%s\t%s", getInventorFile()[0:getInventorFile().index('\\')], node.typeName, ' '.join(['%0{0}X'.format(2) %(h) for h in a0]))

		return i

	def Read_6759D86F(self, node):
		node.typeName = 'RenderingStyle'

		vers = getFileVersion()
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadLen32Text16(i)
		if (vers < 2013):
			i = node.ReadUInt16A(i, 3, 'a1')
		else:
			node.content += ' a0=[0000,0000,0000]'
		i = node.ReadLen32Text16(i, 'txt_0')
		i = self.skipBlockSize(i)
		if (vers > 2012):
			i = node.ReadUInt16(i, 'u16_0')
			i = node.ReadLen32Text16(i, 'txt_1')
			i = node.ReadLen32Text16(i, 'txt_2')
			i = node.ReadLen32Text16(i, 'txt_3')
			i = node.ReadLen32Text16(i, 'txt_4')
			i = node.ReadUInt16A(i, 2, 'a2')
			i = node.ReadUUID(i, 'uid_0')
		else:
			node.content += ' u16_0=0000 txt_1=\'\' txt_2=\'\' txt_3=\'\' txt_4=\'\' a2=[0000,0000] uid_0=None'
		i = node.ReadColorRGBA(i, 'color')
		i = node.ReadColorRGBA(i, 'c1')
		i = node.ReadColorRGBA(i, 'c2')
		i = node.ReadColorRGBA(i, 'c3')
		i = node.ReadFloat32(i, 'f32_0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i, 'FileMapTexture')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadFloat32A(i, 4, 'vec4d_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32A(i, 2, 'vec2d_0')
		i = node.ReadSInt32A(i, 2, 'a3')
		l = len(node.data)
		i = node.ReadUInt8A(i, 5, 'a4')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadFloat64(i, 'f32_1')
		i = node.ReadLen32Text16(i, 'FileMapBump')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadFloat64A(i, 3, 'vec2d_1')
		i = node.ReadLen32Text16(i, 'txt_7')
		if (vers > 2010 and vers < 2013):
			i = node.ReadLen32Text16(i, 'txt_8')
		if (vers > 2010 and vers < 2013):
			i = node.ReadFloat32A(i, 2, 'a5')
		if (vers > 2012):
			i = node.ReadFloat32A(i, 2, 'a6')
		if (vers > 2014):
			i = node.ReadLen32Text16(i, 'txt_9')
			i = node.ReadUInt8(i, 'u8_2')
		if (vers > 2016):
			i = node.ReadFloat32(i, 'f32_2')
			i = node.ReadUInt8A(i, 3, 'a7')
			i = node.ReadFloat32A(i, 3, 'a8')
			i = node.ReadUInt8(i, 'u8_3')
			i = node.ReadFloat32A(i, 10, 'a8')
			i = node.ReadUInt8(i, 'u8_4')
			i = node.ReadFloat32A(i, 7, 'a9')
		color = node.get('color')
		setColor(node.name, color.red, color.green, color.blue)
		return i

	def Read_6759D870(self, node):
		node.typeName = 'Settings'
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		if (getFileVersion() < 2013):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_TEXT8_REF_, 'lst0')
		else:
			i = node.ReadList7(i, AbstractNode._TYP_MAP_TEXT8_REF_, 'lst0')
		return i

	def Read_6B4C0C42(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text16(i)
		# i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_1')
		# i = node.ReadUInt16A(i, 3, 'a0')
		# i = self.skipBlockSize(i)
		# i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_6D8A4AC7(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_6D8A4AC8(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_6D8A4AC9(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_6DD8F4A0(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text8(i)
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadParentRef(i)
		i = node.ReadUInt16A(i, 8, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadChildRef(i, 'cld_1')
		if (i == len(node.data) - 4):
			i = node.ReadUInt32(i, 'codpage')
		else:
			i = node.ReadLen32Text16(i, 'txt_1')
#			i = node.ReadChildRef(i, 'cld_2')
#			i = node.ReadUInt32(i, 'codpage')

		i = self.skipBlockSize(i)
		return i

	def Read_6EAE8DFD(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_7313FAC3(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt16A(i, 17, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 20, 'a1')
		i = self.skipBlockSize(i)
		return i

	def Read_7E23DD2F(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_7F644248(self, node):
		node.typeName = 'Text'
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32A(i, 3, 'a2')
		i = node.ReadLen32Text16(i, 'FontName')
		return i

	def Read_81A9D693(self, node): return 0

	def Read_81AFC10F(self, node):
		i = node.Read_Header0()
		return i

	def Read_8C8E316C(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i, 'txt_2')
		return i

	def Read_958DB976(self, node):
		# i = self.skipBlockSize(i, 8)
		i = 0
		return i

	def Read_9E11F9F6(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		return i

	def Read_9F81E4C8(self, node):
		node.typeName = 'FeatureControlFrame'
		i = node.Read_Header0()
		return i

	def Read_A7A4FD41(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text8(i)
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadParentRef(i)
		i = node.ReadList6(i, AbstractNode._TYP_MAP_TEXT16_REF_, 'lst0')
		i = node.ReadUInt8A(i, 4, 'a0')
		i = self.skipBlockSize(i)

		return i

	def Read_ADAF9728(self, node):
		i = node.Read_Header0()
		return i

	def Read_AEB2BD47(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_BA93BB36(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'cld_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 12, 'u16_0')
		i = node.ReadLen32Text16(i, 'txt_1')
		i = node.ReadLen32Text16(i, 'txt_2')
		return i

	def Read_BF2030AB(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		return i

	def Read_CCA8D815(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_CEA6CA2D(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_D0A64ABB(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a1')

		if (getFileVersion() > 2010):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadFloat64A(i, 2, 'a2')
		else:
			node.content += ' u32_0=000000 a2=(0.25, 0.1)'

		return i

	def Read_D0A64ABC(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_D0A64ABD(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_D4227E2D(self, node):
		i = node.Read_Header0()
		n, i = getUInt32(node.data, i)
		i = node.ReadFloat64A(i, n, 'a0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_D72E4F21(self, node):
		node.typeName = 'Leader'
		i = node.Read_Header0()
		return i

	def Read_D8577FC4(self, node):
		i = self.skipBlockSize(0, 8)
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8A(i, 9, 'a0')
		i = node.ReadLen32Text8(i, 'txt_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text8(i, 'txt_1')
		# i = node.ReadUInt16A(i, 6, 'a1')

		return i

	def Read_DA6B0B3E(self, node): return 0

	def Read_DD4C4D3A(self, node): return 0

	def Read_E454FA4D(self, node):
		i = node.Read_Header0()
#		i = node.ReadUInt16A(i, 10, 'a0')
#		i = node.ReadLen32Text16(i)
#		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_E5DDE747(self, node):
		i = node.Read_Header0()
		i = node.ReadFloat64(i, 'f64_0')
		#i = self.ReadUInt16
		return i

	def Read_E9874A94(self, node):
		i = node.Read_Header0()
		return i

	def Read_EBEE69CA(self, node):
		i = node.Read_Header0()
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_EBEE69CB(self, node):
		i = node.Read_Header0()
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_EBEE69D0(self, node):
		i = node.Read_Header0()
		i = node.ReadList3(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_ED6CD739(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_EFB5BE1A(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_F4DD03EC(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		return i

	def Read_F8A779F1(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_F8A779F3(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_F8A779F5(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_F8A779F6(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_F8A779F8(self, node):
		i = node.Read_Header0()
		return i

	def Read_F8A779F9(self, node):
		i = node.Read_Header0()
#		i = node.ReadLen32Text8(i)
#		type, j = getUInt16(node.data, i)
#		node.typeName = 'ObjectDefault_%02X' % (type)
#		subType = 0
#		if (type == 0x01):
#			i = node.ReadUInt8(j, 'u8_0')
#			i = node.ReadUInt16A(i, 8, 'a0')
#			if (getFileVersion() > 2017):
#				i = node.ReadUInt32(i, 'u32_0')
#				i = node.ReadUInt16(i, 'u16_0')
#			i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
#			i = node.ReadUInt32(i, 'u32_0')
#		elif (type == 0x02):
#			i = self.skipBlockSize(j)
#			i = node.ReadChildRef(i, 'cld_0')
#			i = node.ReadChildRef(i, 'cld_1')
#		elif (type == 0x0A):
#			i = node.ReadUInt32(j, 'u32_0')
#			i = node.ReadFloat32(i, 'f32_0')
#			i = node.ReadList6(i, AbstractNode._TYP_MAP_TEXT8_X_REF_, 'lst0')
#			subType, i = getUInt32(node.data, i)
#			i = node.ReadUInt32(i, 'u32_1')
#			i = node.ReadUInt16(i, 'u16_0')
#			if (subType < 0x110):
#				i = node.ReadUInt8(i, 'u8_0')
#				i = node.ReadUInt16A(i, 7, 'a1')
#				i = node.ReadParentRef(i)
#				i = node.ReadLen32Text16(i, 'txt_0')
#				i = node.ReadLen32Text16(i, 'txt_1')
#				i = node.ReadUInt16(i, 'u16_1')
#				i = node.ReadLen32Text16(i, 'txt_2')
#				i = node.ReadLen32Text16(i, 'txt_3')
#				i = node.ReadLen32Text16(i, 'txt_4')
#				i = node.ReadLen32Text16(i, 'txt_5')
#				i = node.ReadUInt32(i, 'u32_1')
#				i = node.ReadUUID(i, 'uid_0')
#				i = node.ReadFloat64A(i, 8, 'a2')
#				i = node.ReadUInt8(i, 'u8_1')
#				i = node.ReadUInt16A(i, 2, 'a3')
#				i = node.ReadLen32Text16(i, 'txt_6')
#			elif (subType >= 0x0110 and subType < 0x0120):
#				i = node.ReadFloat64A(i, 14, 'a0')
#				i = node.ReadUUID(i, 'uid_0')
#				i = node.ReadUInt8(i, 'u8_0')
#				i = node.ReadFloat64A(i, 2, 'a1')
#				i = node.ReadUInt8A(i, 2, 'a2')
#				i = node.ReadFloat64A(i, 6, 'a3')
#			elif (subType > 0x0121):
#				i = node.ReadUInt8(i, 'u8_0')
#				i = node.ReadUInt16A(i, 7, 'a0')
#				i = node.ReadParentRef(i)
#				i = node.ReadLen32Text16(i, 'txt_0')
#				i = node.ReadLen32Text16(i, 'txt_1')
#				i = node.ReadUInt16(i, 'u16_1')
#				i = node.ReadLen32Text16(i, 'txt_2')
#				i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
#		else:
#			logError(u"Unknown type: %04X", type)
		return i

	def Read_F8A779FD(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_F8D07626(self, node):
		i = node.Read_Header0()
		return i

	def Read_F94FEEE2(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_FD1E8992(self, node): return 0

	def Read_FD1E8995(self, node): return 0

	def Read_FD1E8997(self, node): return 0

	def Read_FD1E899A(self, node): return 0

	def Read_FD1E899B(self, node): return 0

	def Read_FD1E899D(self, node): return 0

	def Read_FD1F3F21(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_FDA6D020(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text8(i)
		i = node.ReadCrossRef(i, 'ref_Setup')
		i = node.ReadParentRef(i)
		i = node.ReadList6(i, AbstractNode._TYP_MAP_TEXT16_REF_, 'lst0')
		return i

	def postRead(self, segment):
		color = self.defStyle.get('color')
		setColorDefault(color.red, color.green, color.blue)

	# override importerSegment.setNodeData
	def setNodeData(self, node, data):
		offset = node.offset
		nodeTypeID, i = getUInt8(data, offset - 4)
		node.typeID = getNodeType(nodeTypeID, node.segment)
		if (isinstance(node.typeID, UUID)):
			node.typeName = '%08X' % (node.typeID.time_low)
			i = offset + node.size
			s, dummy = getUInt32(data, i)
			if ((s != node.size) and (node.typeID.time_low == 0xF8A779F9)):
				s, dummy = getUInt32(data, i)
				while ((s != node.size) and (i < len(data))):
					i += 1
					s, dummy = getUInt32(data, i)
				node.size = i - offset
		else:
			node.typeName = '%08X' % (node.typeID)

		node.data = data[offset:offset + node.size]
