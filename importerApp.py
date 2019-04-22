# -*- coding: utf-8 -*-

'''
importerApp.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment import SegmentReader
from importerUtils   import *
import importerSegNode

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class AppReader(SegmentReader):
	def __init__(self, segment):
		super(AppReader, self).__init__(segment)
		self.defStyle = None

	def readHeaderStyle(self, node, typeName = None, ref1Name = 'collection'):
		vers = getFileVersion()
		i = node.Read_Header0(typeName)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		if (vers > 2019): i += 2 # skip 00 00
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadUInt32(i, 'default')
		i = node.ReadUInt32(i, 'u32')
		i = node.ReadCrossRef(i, ref1Name)
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'comment')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadLen32Text16(i, 'longName')
		i = self.skipBlockSize(i)
		return i

	def Read_10389219(self, node):
		i = node.Read_Header0()
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_, 'lst0')
		return i

	def Read_10D6C06B(self, node): # SheetMetalRule
		i = self.readHeaderStyle(node, 'SheetMetalRule', )
		i = node.ReadLen32Text16(i, 'txt_1')
		i = node.ReadLen32Text16(i, 'txt_2')
		i = node.ReadLen32Text16(i, 'txt_3')
		i = node.ReadLen32Text16(i, 'txt_4')
		i = node.ReadLen32Text16(i, 'txt_5')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadLen32Text16(i, 'txt_6')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i, 'txt_7')
		return i

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

	def Read_1C4CFF13(self, node): # TextStyleCollection
		i = self.readHeaderStyle(node, 'TextStyleCollection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_1DA4647D(self, node):
		i = node.Read_Header0()
		return i

	def Read_1E5CBB86(self, node): # Lighting
		i = self.readHeaderStyle(node, 'Lighting')
		i = node.ReadColorRGBA(i, 'a2')
		i = node.ReadList2(i, importerSegNode._TYP_LIGHTNING_, 'lst0')
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
		i = node.ReadParentRef(i)
		return i

	def Read_3214005D(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_3235A9B8(self, node):
		vers = getFileVersion()
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst1')
		i = node.ReadChildRef(i, 'cld_0')
		if (vers > 2010): i += 4 # skip 01 00 00 00
		if (vers > 2017): i += 8
		return i

	def Read_345EB9B1(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUUID(i, 'uid_1')
		return i

	def Read_36BC43F4(self, node):
		i = self.readHeaderStyle(node)
		i = node.ReadChildRef(i, 'ref_0')
		i = self.skipBlockSize(i)

		return i

	def Read_37186901(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_APP_1_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_3F89DC90(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_4028969E(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		if (getFileVersion() < 2011):
			i = node.ReadLen32Text16(i, 'length')
		else:
			i = node.ReadFloat64(i, 'length')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_422ECBCE(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2	, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_42A65DAA(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_440F63D1(self, node):
		i = self.readHeaderStyle(node)
		i = node.ReadUInt32A(i, 4, 'a2')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_461E402F(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_473180FD(self, node): # bound equation for bend compensation
		i = node.Read_Header0('BoundEquation')
		i = node.ReadLen32Text16(i, 'lBound')
		i = node.ReadLen32Text16(i, 'uBound')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = node.ReadLen32Text16(i, 'equation')
		return i

	def Read_55231213(self, node): # MateInterfaceDef
		i = node.Read_Header0('iMate')
		i = node.ReadUUID(i, 'uid_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 4, 'a2')
		return i

	def Read_553C5021(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_61B5E2D1(self, node):
		node.typeName = 'iMates'
		i = self.skipBlockSize(0)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'imates')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_6759D86E(self, node): # MaterialName
		vers = getFileVersion()
		i = self.readHeaderStyle(node, 'MaterialName', 'materials')
		if (vers > 2012):
			i = node.ReadLen32Text16(i, 'txt_1') # UUID's
			i = node.ReadLen32Text16(i, 'txt_2') #
			i = node.ReadLen32Text16(i, 'txt_3') # UUID's
			i = node.ReadUInt16A(i, 2, 'a2')
			i = node.ReadUUID(i, 'uid_0')
		else:
			node.content += ' txt_1=\'\' txt_2=\'\' txt_3=\'\' txt_4=\'\' a2=[0000,0000] uid_0=None '
		i = node.ReadFloat64A(i, 8, 'a3')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_0')
		if (vers > 2011):
			i = node.ReadLen32Text16(i, 'txt_4')
		a0, j = getUInt8A(node.data, i, len(node.data) - i)
		if (len(a0) > 0):
			logError(u"%s\t%s\t%s", getInventorFile()[0:getInventorFile().rindex('/')], node.typeName, ' '.join(['%0{0}X'.format(2) %(h) for h in a0]))
		return i

	def Read_6759D86F(self, node): # RenderingStyle
		vers = getFileVersion()
		i = node.Read_Header0('RenderingStyle')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		if (vers > 2019):
			i += 2 # skip 00 00
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadUInt32(i, 'default')
		i = node.ReadUInt32(i, 'u32')
		i = node.ReadCrossRef(i, 'ref1Name')
		i = node.ReadLen32Text16(i)
		if (vers < 2013):
			i = node.ReadLen32Text16(i, 'comment')
			i = node.ReadUInt16(i, 'u16_0')
		else:
			node.content += u" comment='' u16_0=0000"
			node.set('comment', '')
			node.set('u16_0', 0)
		i = node.ReadLen32Text16(i, 'longName')
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
		i = node.ReadFloat32_2D(i, 'vec2d_0')
		i = node.ReadSInt32A(i, 2, 'a3')
		l = len(node.data)
		i = node.ReadUInt8A(i, 5, 'a4')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadFloat64(i, 'f32_1')
		i = node.ReadLen32Text16(i, 'FileMapBump')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadFloat64_3D(i, 'vec2d_1')
		i = node.ReadLen32Text16(i, 'txt_7')
		if (vers > 2010 and vers < 2013):
			i = node.ReadLen32Text16(i, 'txt_8')
		if (vers > 2010 and vers < 2013):
			i = node.ReadFloat32_2D(i, 'a5')
		if (vers > 2012):
			i = node.ReadFloat32_2D(i, 'a6')
		if (vers > 2014):
			i = node.ReadLen32Text16(i, 'txt_9')
			i = node.ReadUInt8(i, 'u8_2')
		if (vers > 2016):
			i = node.ReadFloat32(i, 'f32_2')
			i = node.ReadUInt8A(i, 3, 'a7')
			i = node.ReadFloat32_3D(i, 'a8')
			i = node.ReadUInt8(i, 'u8_3')
			i = node.ReadFloat32A(i, 10, 'a8')
			i = node.ReadUInt8(i, 'u8_4')
			i = node.ReadFloat32A(i, 7, 'a9')
		color = node.get('color')
		setColor(node.name, color.red, color.green, color.blue)
		return i

	def Read_6759D870(self, node): # Settings
		vers = getFileVersion()
		i = node.Read_Header0('Settings')
		node.name = 'GreyRoom'
		if (vers < 2013):
			i = self.skipBlockSize(i)
			i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT8_REF_, 'lst0')
		else:
			i = node.ReadList7(i, importerSegNode._TYP_MAP_TEXT8_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT8_REF_, 'lst1')
		i = node.ReadFloat64A(i, 24, 'a0')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		if (vers > 2010):
			i = node.ReadUInt32A(i, 20, 'a1')
			i = node.ReadUInt8(i, 'u8_1')
			i = node.ReadColorRGBA(i, 'c_0')
			i = node.ReadFloat32(i, 'f_0')
			i = node.ReadUInt16(i, 'u16_0')
			if (vers > 2019): i += 3 # skip 00 00 00
			i = node.ReadFloat64(i, 'f_1')
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadFloat64(i, 'f_2')
			i = node.ReadUInt32(i, 'u32_2')
			i = node.ReadFloat64(i, 'f_3')
			if (vers > 2019): i += 1 # skip 00
			i = node.ReadFloat64_2D(i, 'a3')
			i = node.ReadUInt32A(i, 2, 'a4')
			if (vers > 2011):
				i = node.ReadUInt32(i, 'u32_4')
			else:
				node.content += ' u8_4=00'
			i = node.ReadUInt32A(i, 3, 'a4')
			i = node.ReadUInt8(i, 'u8_2')
			i = node.ReadUInt32(i, 'u32_3')
			if (vers > 2012):
				i = node.ReadUInt8(i, 'u8_3')
				if (vers > 2015):
					i = node.ReadUInt8(i, 'u8_4')
					i = node.ReadUInt32(i, 'u32_5')
					i = node.ReadColorRGBA(i, 'c_1')
					i = node.ReadUInt32(i, 'u32_6')
					i = node.ReadFloat32A(i, 5, 'f_4')
					i = node.ReadUInt8(i, 'u8_5')
					i = node.ReadLen32Text16(i)
					if (vers > 2016):
						i = node.ReadFloat32(i, 'f_5')
						if (vers > 2017):
							i += 1
		else:
			i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_6B4C0C42(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text16(i)
		i = node.ReadParentRef(i)
		return i

	def Read_6D8A4AC7(self, node): # AngleInterfaceDef
		i = node.Read_Header0('AngleInterfaceDef')
		i = node.ReadUUID(i, 'uid_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		return i

	def Read_6D8A4AC8(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_6D8A4AC9(self, node): # InsertInterfaceDef
		i = node.Read_Header0('InsertInterfaceDef')
		i = node.ReadUUID(i, 'uid_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_6DD8F4A0(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text8(i)
		i = node.ReadCrossRef(i, 'cld_0')
		i = node.ReadParentRef(i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_REF_, 'lst0')
		i = node.ReadUInt32(i, 'codpage')
		i = self.skipBlockSize(i)
		return i

	def Read_6EAE8DFD(self, node):
		i = self.readHeaderStyle(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadChildRef(i, 'ref_4')
		i = node.ReadChildRef(i, 'ref_5')
		i = node.ReadChildRef(i, 'ref_6')
		i = node.ReadChildRef(i, 'ref_7')
		i = node.ReadChildRef(i, 'ref_8')
		i = node.ReadChildRef(i, 'ref_9')
		i = node.ReadChildRef(i, 'ref_A')
		i = node.ReadChildRef(i, 'ref_B')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadChildRef(i, 'ref_C')
		return i

	def Read_7313FAC3(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
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

	def Read_7F644248(self, node): # Text
		i = self.readHeaderStyle(node, 'Text')
		i = node.ReadSInt32A(i, 3, 'a2')
		i = node.ReadLen32Text16(i, 'FontName')
		return i

	def Read_81A9D693(self, node): return 0

	def Read_81AFC10F(self, node): # CompositeInterfaceDef
		i = node.Read_Header0('CompositeInterfaceDef')
		i = node.ReadUUID(i, 'uid_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_8C8E316C(self, node):
		i = self.readHeaderStyle(node)
		return i

	def Read_958DB976(self, node):
		i = self.skipBlockSize(0, 8)
		return i

	def Read_9E11F9F6(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32A(i, 6, 'a0')
		i = node.ReadUUID(i, 'brepUID')
		i = node.ReadUUID(i, 'graphicsUID')
		i = node.ReadParentRef(i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_)
		if (getFileVersion() < 2012):
			node.content += u" u32_0=000005"
			node.set('u32_0', 5)
		else:
			i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		return i

	def Read_9F81E4C8(self, node): # FeatureControlFrame
		i = self.readHeaderStyle(node, 'FeatureControlFrame')
		i = node.ReadFloat64_2D(i, 'a2')
		i = node.ReadUInt32A(i, 6, 'a3')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_A7A4FD41(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text8(i)
		i = node.ReadCrossRef(i, 'default')
		i = node.ReadParentRef(i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_REF_, 'lst0')
		i = node.ReadUInt8A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_A3C6F29E(self, node):
		i = node.Read_Header0()
		return i

	def Read_ADAF9728(self, node):
		i = node.Read_Header0()
		return i

	def Read_AEB2BD47(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_B5731134(self, node):
		i = node.Read_Header0()
		return i

	def Read_B8610156(self, node):
		i = node.Read_Header0()
		return i

	def Read_BA93BB36(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text16(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 12, 'u16_0')
		i = node.ReadLen32Text16(i, 'txt_1')
		i = node.ReadLen32Text16(i, 'txt_2')
		return i

	def Read_BF2030AB(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_C435E97C(self, node):
		i = self.skipBlockSize(0, 8)
		i = node.ReadLen32Text16(i)
		return i

	def Read_CCA8D815(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_D0A64ABB(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		node.set('u32_1', 0x0E)
		if (getFileVersion() > 2010):
			i = node.ReadUInt32(i, 'u32_0')
			if (getFileVersion() > 2011):
				i = node.ReadUInt32(i, 'u32_1')
			else:
				node.content += u" u32_1=000E"
			i = node.ReadFloat64_2D(i, 'a2')
		else:
			node.content += ' u32_0=0013 u32_1=000E a2=(0.25, 0.1)'
		i = node.ReadFloat64_2D(i, 'a3')
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

	def Read_D72E4F21(self, node): # Leader
		i = self.readHeaderStyle(node, 'Leader')
		i = node.ReadFloat64A(i, 4, 'a1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat32(i, 'f0')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadFloat32_3D(i, 'a0')
		i = node.ReadUInt8(i, 'u8_3')
		i = node.ReadFloat32_3D(i, 'a1')
		return i

	def Read_D8577FC4(self, node):
		node.typeName = 'TextStyle'
		i = self.skipBlockSize(0, 8)
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8A(i, 9, 'a0')
		i = node.ReadLen32Text8(i, 'txt_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text8(i, 'txt_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_DA6B0B3E(self, node): # SheetMetalUnfold
		i = self.readHeaderStyle(node, 'SheetMetalUnfold')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i, 'txt_1')
		i = node.ReadLen32Text16(i, 'facK')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'bendAngleType') # 3 = 'Open Angle', 2 = 'Bend Angle'
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'equations')
		i = node.ReadLen32Text16(i, 'facSpline')
		return i

	def Read_DD4C4D3A(self, node): # ASMFlatPatternPartRepresentation
		i = node.Read_Header0('ASMFlatPatternPartRepresentation')
		i = node.ReadUUID(i, 'uid_0')
		return i

	def Read_E454FA4D(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_U32_TXT_TXT_DATA_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_U32_TXT_U32_LST2_, 'lst1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT16_A_, 'lst2', 2)
		return i

	def Read_E5DDE747(self, node):
		i = node.Read_Header0()
		i = node.ReadFloat64A(i, 14, 'a0')
		return i

	def Read_E9874A94(self, node):
		i = self.readHeaderStyle(node)
		i = node.ReadUInt8A(i, 4, 'a2')
		i = node.ReadFloat64(i, 'f_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'ref_1')
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

	def Read_F447C040(self, node):
		i = node.Read_Header0()
		return i

	def Read_F4DD03EC(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		return i

	def Read_F8A779F9(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref1')
		i = node.ReadChildRef(i, 'ref2')
		return i
		return i

	def Read_F8D07626(self, node):
		i = node.Read_Header0()
		return i

	def Read_FD1E8992(self, node):
		i = self.skipBlockSize(0, 8)
		i = node.ReadColorRGBA(i, 'color')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_FD1E8995(self, node):
		i = self.skipBlockSize(0, 8)
		return i

	def Read_FD1E8997(self, node):
		i = self.skipBlockSize(0, 8)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_FD1E899A(self, node): # Analysis Style Draft
		i = self.readHeaderStyle(node, 'AnalysisStyleDraft')
		return i

	def Read_FD1E899B(self, node): # Analysis Style Zebra
		i = self.readHeaderStyle(node, 'AnalysisStyleZebra')
		return i

	def Read_FD1E899D(self, node): # Analysis Setup
		i = self.readHeaderStyle(node, 'AnalysisSetup')
		return i

	def Read_FD1F3F21(self, node): # FlushInterfaceDef
		i = node.Read_Header0('FlushInterfaceDef')
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_FDA6D020(self, node): # LeaderCollection
		i = node.Read_Header0('LeaderCollection')
		i = node.ReadLen32Text8(i)
		i = node.ReadCrossRef(i, 'default')
		i = node.ReadParentRef(i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_REF_, 'lst0')
		return i

	def postRead(self):
		color = self.defStyle.get('color')
		if (color is not None):
			setColorDefault(color.red, color.green, color.blue)
