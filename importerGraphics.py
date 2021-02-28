# -*- coding: utf-8 -*-

'''
importerGraphics.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) graphics data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

import traceback, importerSegNode
from importerSegment        import checkReadAll
from importerEeScene        import EeSceneReader
from importerTransformation import Transformation3D
from importerUtils          import *
from math import fabs

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class GraphicsReader(EeSceneReader):

	def __init__(self, segment):
		super(GraphicsReader, self).__init__(segment)
		segment.meshes = {}

	def ReadIndexDC(self, node, i):
		i = node.ReadUInt32(i, 'indexDC')
		self.segment.indexNodes[node.get('indexDC')] = node
		return i

	#########################
	# U32 Ref U8 L3 sections
	def Read_05CE4AC7(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		return i

	def Read_088AA9BE(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'outlines') # list of outlines: key <=> DC-Index!
		i = self.skipBlockSize(i	)
		node.object3D = True
		return i

	def Read_0DE8E459(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadChildRef(i, 'object3D')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64_3D(i, 'a3')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_27DFC9F5(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadChildRef(i, 'object3D')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_3DA2C291(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8A(i, 4, 'a2')
		return i

	def Read_4B26ED59(self, node): # Mesh
		i = self.ReadHeaderU32RefU8List3(node, 'Mesh', 'parts')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadIndexDC(node, i)
		if (self.version > 2017): i += 4 # FF,FF,FF,FF
		return i

	def Read_5EDE1890(self, node): # Mesh
		i = self.ReadHeaderU32RefU8List3(node, 'Mesh', 'parts')
		i = node.ReadLen32Text16(i, 'meshId')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'ref_1')
		self.segment.meshes[node.get('meshId')] = node
		return i

	def Read_60FD1845(self, node): # Sketch2D
		i = self.ReadHeaderU32RefU8List3(node, 'Sketch2D')
		i = node.ReadChildRef(i, 'obj')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'index')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst2')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst3')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_61530B1E(self, node): # Assembly
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadChildRef(i, 'obj')
		i = self.skipBlockSize(i)
		i = self.ReadIndexDC(node, i)
		if (self.version < 2015):
			i += 2
		else:
			i += 4
		i = node.ReadUInt32(i, 'index')
		return i

	def Read_6A05AA75(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadUInt32(i, 'index')
		return i

	def Read_6C8A5C53(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64A(i, 6, 'a4')
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_733CA999(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadChildRef(i, 'ref0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'ref1')
		i = node.ReadChildRef(i, 'ref2')
		if (i < len(node.data)): # > 2018 Beta 1!!!
			i = node.ReadUInt32(i, 'index')
		return i

	def Read_9215A162(self, node): # NoteGlyphGroup
		i = self.ReadHeaderU32RefU8List3(node, 'NoteGlyphGroup')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_9823F7FF(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		return i

	def Read_995AA46F(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadChildRef(i, 'ref0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'ref1')
		i = node.ReadChildRef(i, 'ref2')
		if (i < len(node.data)): # > 2018 Beta 1!!!
			i = node.ReadChildRef(i, 'ref3')
		return i

	def Read_9A5F40BC(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		return i

	def Read_9EA0717F(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadChildRef(i, 'ref0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'ref1')
		i = node.ReadChildRef(i, 'ref2')
		if not(self.version == 2018 and getFileBeta() >= 0):
			i = node.ReadUInt32(i, 'index')
		return i

	def Read_A98235C4(self, node):
		i = self.ReadHeaderU32RefU8List3(node, 'MeshPart')
		i = node.ReadChildRef(i, 'object3D')
		i = self.skipBlockSize(i)
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt32(i, 'u32_1')

		if (self.version < 2012):
			i = node.ReadUInt16A(i, 5, 'a2')
		else:
			i = node.ReadLen32Text16(i, 'txt0')
			i = node.ReadLen32Text16(i, 'txt1')

		if (node.get('u32_1') == 1):
			i = node.ReadUInt32A(i, 3, 'a3')
			i = node.ReadFloat64(i, 'f64_0')
			i = node.ReadUInt8(i, 'u8_1')
		else:
			node.set('a3', [0, 0, 0])
			node.set('f64_0', 0.0)
			node.content += u" a3=[0000,0000,0000] f64_0=0.0"
#			i = node.ReadLen32Text16(i, 'txt2')
		return i

	def Read_AC007F7A(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		return i

	def Read_B9D0D00A(self, node): # Assembly
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'obj')
		return i

	def Read_B9D0D008(self, node): # Assembly
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'obj')
		return i

	def Read_C18CE1AF(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		return i

	def Read_C2A055C9(self, node): # MeshFolder
		i = self.ReadHeaderU32RefU8List3(node, 'MeshFolder', 'meshes')
		i = node.ReadUInt32(i, 'index')
		i = self.ReadIndexDC(node, i)
		if (self.version > 2017):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		else:
			node.content += u" lst0={}"
		return i

	def Read_C3608DE7(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		return i

	def Read_C84E693F(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		return i

	def Read_CA7163A3(self, node): # PartNode
		i = self.ReadHeaderU32RefU8List3(node, 'PartNode', lstName = 'items')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'outlines') # list of outlines: key <=> DC-Index!
		i = self.skipBlockSize(i)
		i = node.ReadMaterial(i, 2)
		return i

	def Read_D4824069(self, node): # ClientFeatureNode
		i = self.ReadHeaderU32RefU8List3(node, 'ClientFeatureNode', 'meshes')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'index')
		i = self.ReadIndexDC(node, i)
		return i

	def Read_DA58AA0E(self, node): # Sketch3D
		i = self.ReadHeaderU32RefU8List3(node, 'Sketch3D')
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst2')
		i = node.ReadUInt8(i, 'u8_3')
		return i

	def Read_F96556CB(self, node): # MeshPart
		i = self.ReadHeaderU32RefU8List3(node, 'MeshPart')
		i = node.ReadChildRef(i, 'object3D')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8A(i, 2, 'a1')
		i = self.ReadIndexDC(node, i)
		if (self.version > 2017):
			i = node.ReadList2(i, importerSegNode._TYP_SINT32_, 'lst1')
		else:
			node.content += u" lst1=[]"
		return i

	def Read_F9C49549(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		return i

	def Read_FB11E67E(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadChildRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i += 4 # skip redundant information
		i = node.ReadUInt32(i, 'index')
		return i

	def Read_FE59A112(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		return i

	#########################
	# object sections
	def ReadHeaderObject(self, node, typeName = None):
		i = self.ReadHeaderU32RefU8List3(node, typeName)
		i = node.ReadChildRef(i, 'obj')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'index')
		i = self.ReadIndexDC(node, i)
		return i

	def Read_14533D82(self, node): # WrkPlane
		i = self.ReadHeaderObject(node, 'WrkPlane')
		i = node.ReadFloat64A(i, 6, 'a1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt8A(i, 3, 'a3')
		return i

	def Read_2C7020F6(self, node): # WrkAxis
		i = self.ReadHeaderObject(node, 'WkrAxis')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt8A(i, 3, 'a3')
		return i

	def Read_2C7020F8(self, node): # WrkPoint
		i = self.ReadHeaderObject(node, 'WrkPoint')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt8A(i, 2, 'a3')
		return i

	def Read_698CF98E(self, node): # Wrk???
		i = self.ReadHeaderObject(node)
		i = self.ReadTransformation3D(node, i)
		i = node.ReadBoolean(i, 'b0')
		return i

	#########################
	# attribute sections
	def Read_022AC1B5(self, node): # Part-Draw attribute
		i = self.ReadHeaderAttribute(node, 'AttrPartDraw')
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2014):
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		else:
			lst = []
			u32, i = getUInt32(node.data, i)
			lst.append(u32)
			node.set('lst0', lst)
			node.content += u" lst0=[%04X]" %(u32)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a2')
		i = node.ReadColorRGBA(i,  'Color.c0')
		i = node.ReadColorRGBA(i,  'Color.diffuse')
		i = node.ReadColorRGBA(i,  'Color.c2')
		i = node.ReadColorRGBA(i,  'Color.c3')
		i = node.ReadUInt16A(i, 2, 'Color.a5')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 2, 'a0')
		return i

	def Read_0244393C(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_0270FFC7(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_2')
		return i

	def Read_04F234D9(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8A(i, 2, 'a0')
		i = node.ReadFloat32A(i, 17, 'a1')
		i = node.ReadUInt8A(i, 2, 'a2')
		i = node.ReadFloat32(i, 'f1')
		i = node.ReadUInt16A(i, 2, 'a3')
		i = node.ReadUInt8(i, 'b0')
		i = node.ReadFloat32A(i, 4, 'a4')
		return i

	def Read_097A6824(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8A(i, 2, 'a1')
		return i

	def Read_12A31E33(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 5, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 8, 'a1')
		i = self.skipBlockSize(i, 2)
		return i

#	def Read_13FC8170(self, node): # Attribute ...
#		i = self.ReadHeaderAttribute(node)
#		i = node.ReadUInt32(i, 'u32_1')
#		return i

	def Read_184FDA9C(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadFloat64A(i, 16, 'a0')
		return i

	def Read_189725D1(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i  = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_23974603(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8A(i, 2, 'a0')
		i = node.ReadFloat32A(i, 17, 'a1')
		i = node.ReadUInt8A(i, 2, 'a2')
		i = node.ReadFloat32(i, 'f1')
		i = node.ReadUInt16A(i, 2, 'a3')
		i = node.ReadUInt8(i, 'b0')
		i = node.ReadFloat32A(i, 4, 'a4')
		return i

	def Read_2E56FF78(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'body')
		i = self.skipBlockSize(i)
		return i

	def Read_337E7C53(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_35E93051(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_56235A51(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_5A972561(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_6399C27C(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadCrossRef(i, 'group')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		return i

	def Read_76986821(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_913D5CD2(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_9E2FB889(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8A(i, 2, 'a0')
		i = node.ReadFloat32A(i, 17, 'a1')
		i = node.ReadUInt8A(i, 2, 'a2')
		i = node.ReadFloat32(i, 'f1')
		i = node.ReadUInt16A(i, 2, 'a3')
		return i

	def Read_B1057BE1(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 13, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		return i

	def Read_B1057BE2(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 13, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		return i

	def Read_B1057BE3(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 13, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		return i

	def Read_C9DA5109(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_D28CA9B4(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		a = Struct('<ffffhfhhfffBLLL').unpack_from(node.data, i)
		i += 47
		node.content += u" a0=(%g,%g,%g,%g,%03X,%g,%03X,%03X,%g,%g,%g,%02X,%04X,%04X,%04X)" %a
		node.set('a0', a)
		return i

	def Read_D95D32FC(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_DFDFCB84(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_F9437786(self, node): # Attribute ...
		i = self.ReadHeaderAttribute(node)
		return i

	#########################
	# 3D object sections
	def Read_5194E9A2(self, node):
		i = self.ReadHeader3dObject(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		return i

	def Read_A79EACD1(self, node):
		i = self.ReadHeader3dObject(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		b, i = getBoolean(node.data, i) # has Transforamtion
		if (b):
			i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'lst1', 3)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		if (self.version > 2018):
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst3')
		else:
			cnt, i = getUInt32(node.data, i)
			lst3, i = getUInt8A(node.data, i, cnt)
			node.content += " lst3=[%s]" %(','.join('%04X' %(n) for n in lst3))
			node.set('lst3', lst3)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat64(i, 'f0')
		return i

	#########################
	# attribute sections
	def Read_022AC1B1(self, node): # PersistentScenePath
		node.typeName = 'PersistentScenePath'
		b, i = getBoolean(node.data, 0)
		if (b):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		else:
			b, i = getBoolean(node.data, i)
			i = node.ReadUInt8(i, 'u8_0')
			if (b == False):
				i = node.ReadUInt32(i, 'u32_0')
				i = node.ReadLen32Text16(i, 'txt0')
				i = node.ReadLen32Text16(i, 'txt1')
				i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_0B2C8AE9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt16A(i, 4, 'a0')
		return i

	def Read_438452F0(self, node): # Color attributes
		node.typeName = 'Attr_Colors'
		i = node.ReadUInt32A(0, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		a1 = Struct('<HfHh').unpack_from(node.data, i)
		node.content += " a1=[%03X,%g,%03X,%d]" %(a1[0], a1[1], a1[2], a1[3])
		i += 10
		node.set('a1', a1)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 8, 'a2')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_B3895BC2(self, node): # Color attributes ...
		node.typeName = 'Attr_Colors'
		i = node.ReadUInt32A(0, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		a1 = Struct('<HfHh').unpack_from(node.data, i)
		node.content += " a1=[%03X,%g,%03X,%d]" %(a1[0], a1[1], a1[2], a1[3])
		i += 10
		node.set('a1', a1)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 8, 'a2')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_27F6DF59(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version < 2020): i += 8 # skip 00 00 00 00 00 00 00 00
		a = Struct('<LHLLLLL').unpack_from(node.data, i)
		i += 26
		node.content += u" a1=[%04X,%03X,%04X,%04X,%04X,%04X,%04X]" %a
		node.set('a1', a)
		i = node.ReadList2(i, importerSegNode._TYP_F64_F64_U32_U8_U8_U16_, 'lst0')
		i = node.ReadFloat64_2D(i, 'a2')
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_4E951290(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_4E951291(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_651117CE(self, node): # MeshTriangleNormals
		i = node.Read_Header0('MeshTriangleNormals')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'normals', 3)
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2013):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst1')
		else:
			node.set('lst1', [])
		return i

	def Read_B9D0D007(self, node): # Assembly
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'attrs')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_CA7163A2(self, node): # Assembly
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'attrs')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadUInt32(i, 'u32_1')
		if (node.get('u8_1') == 0):
			i = node.ReadLen32Text16(i)
			i = node.ReadUInt16(i, 'u16_1')
			i = self.skipBlockSize(i, 2)
			i = node.ReadUInt32(i, 'u32_2')
			i = node.ReadCrossRef(i, 'obj')
			i = node.ReadUInt32(i, 'u32_3')
		else:
			i = node.ReadChildRef(i, 'ref1')
			i = self.skipBlockSize(i, 2)
			k, i = getUInt32(node.data, i)
			i = node.ReadCrossRef(i, 'ref2', k)
			i = node.ReadUInt32(i, 'u32_2')
		if (self.version < 2015): i += 4 # skip ????
		i = len(node.data) # skip ????
		return i

	def Read_F440100C(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'attrs')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'obj')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_3')
		if (self.version < 2015): i += 4 # skip ????
		i = node.ReadFloat64A(i, 6, 'a1')
		i = self.skipBlockSize(i)
		return i

	def Read_6A6931DC(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.ReadEdgeList(node, i)
		i = node.ReadList2(i, importerSegNode._TYP_LIST_FLOAT64_A_, 'points', 3)
		i = node.ReadFloat64_3D(i, 'p1')
		i = node.ReadFloat64_3D(i, 'p2')
		return i

	def Read_8974BA73(self, node):
		i = node.ReadUInt32(0, 'u32_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_8DA49A23(self, node): # InstanceNode
		i = node.Read_Header0( 'InstanceNode')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 5, 'a1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt16A(i, 4, 'a2')
		return i

	def Read_9360CF4D(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadFloat64(i, 'f64_0')
		if (self.version > 2013):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst1')
		else:
			node.set('lst1', [])
		return i

	def Read_9A676A50(self, node): # Body
		i = node.Read_Header0('Body')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'attrs')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = self.ReadIndexDC(node, i) # SurfaceBody's index in DC-Segment
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'index')
		i = node.ReadChildRef(i, 'obj')
		if (self.version < 2020): i += 8 # skip 00 00 00 00 00 00 00 00
		i = node.ReadUInt32(i , 'u32_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadChildRef(i, 'shell')
		i = node.ReadChildRef(i, 'wire')
		i = node.ReadChildRef(i, 'ref4')
		i = node.ReadChildRef(i, 'ref5')
		i = node.ReadChildRef(i, 'ref6')
		i = node.ReadList2(i, importerSegNode._TYP_2D_F64_U32_4D_U8_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_2D(i, 'a2')
		i = self.skipBlockSize(i, 2)
		i = node.ReadList7(i, importerSegNode._TYP_MAP_U32_U32_, 'faces2edges') # mapping of face's key to mapping edge object's key
		i = node.ReadSInt32A(i, 2, 'a3')
		tst, j = getUInt32(node.data, i)
		if (tst == 0x30000002):
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		i = node.ReadChildRef(i, 'ref7') # -> 6A6931DC with
		self.segment.bodies[node.get('indexDC')] = node
		return i

	def Read_A3EBE198(self, node): #  BodyNode
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'attributes')
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadBoolean(i, 'b1')
		i = node.ReadChildRef(i, 'object3D')
		if (self.version < 2020): i += 8 # skip 00 00 00 00 00 00 00 00
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadUInt32A(i, 5, 'a2')
		i = node.ReadList2(i, importerSegNode._TYP_F64_F64_U32_U8_U8_U16_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_2D(i, 'a3')
		i = self.skipBlockSize(i, 2)
		i = node.ReadList7(i, importerSegNode._TYP_MAP_U32_U32_, 'faces2edges') # mapping of face's key to mapping edge object's key
		i = node.ReadUInt32A(i, 4, 'a4')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		if (self.version > 2013): i += 1 # skip Boolean
		return i

	def Read_A6DD2FCC(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref0')
		i = node.ReadBoolean(i, 'b0')
		i = self.ReadTransformation3D(node, i	)
		i = node.ReadBoolean(i, 'b1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'sketch')
		i = node.ReadChildRef(i, 'ref1')
		return i

	def Read_C0014C89(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_2D(i, 'a1')
		i = node.ReadUInt8A(i, 4, 'a2')
		i = self.ReadTransformation3D(node, i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 7, 'a5')
		return i

	def Read_DBE41D91(self, node): # CompInterfaceNode
		i = node.Read_Header0('CompInterfaceNode')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 14, 'a2')
		return i

	def Read_DEF9AD02(self, node): # MeshTrianglePoints
		i = node.Read_Header0('MeshTrianglePoints')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'points', 3)
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2013):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst1')
		else:
			node.set('lst1', [])
		return i

	def Read_DEF9AD03(self, node): # MeshTriangleIndices
		i = node.Read_Header0('MeshTriangleIndices')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'indices')
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2013):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst1')
		else:
			node.set('lst1', [])
		return i

	def Read_EF1E3BE5(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_FONT_, 'lst0')
		return i

	def Read_FB96D24A(self, node): # NoteGlyphNode
		i = node.Read_Header0('NoteGlyphNode')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64_3D(i, 'f64_0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	####################
	# Outline sections
	def ReadHeaderOutline(self, node, typeName = None):
		if (typeName == None):
			node.typeName = 'Outline_%s' %(node.typeName)
		else:
			node.typeName = typeName
		i = self.skipBlockSize(0)
		i = node.ReadParentRef(i)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_5FA87956(self, node): # Group feature outline
		i = self.ReadHeaderOutline(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'outlines')
		i = node.ReadUInt32(i, 'index')
		return i

	def Read_7DFC2448(self, node): # Composite feature outline
		i = self.ReadHeaderOutline(node, 'OutlineCompositeFx')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'outlines')
		i = node.ReadUInt32(i, 'index')
		return i

	def Read_9E8CE961(self, node): # Transformation feature outline
		i = self.ReadHeaderOutline(node, 'OutlineTransformationFx')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'outlines')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'index')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64A(i, 6, 'box') # bounding box
		a = Struct('<dHHH').unpack_from(node.data, i)
		i += 8+6
		node.content += u" a0=(%g,%03X,%03X,%03X)" %a
		node.set('a1', a)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'outlines')
		i = node.ReadList2(i, importerSegNode._TYP_TRANSFORMATIONS_, 'transformations')
		return i

	def Read_A94779E0(self, node): # Single feature outline
		i = self.ReadHeaderOutline(node, 'OutlineSingleFx')
		i = node.ReadUInt32(i, 'index')
		i = node.ReadFloat64A(i, 6, 'box') # bounding box
		i = self.ReadEdgeList(node, i)
		i = node.ReadList2(i, importerSegNode._TYP_LIST_FLOAT64_A_, 'points', 3)
		return i

	def Read_A94779E2(self, node): # Pattern feature outline
		i = self.ReadHeaderOutline(node, 'OutlinePatternFx')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'outlines')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'index')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt16A(i, 4, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		i = node.ReadFloat64_3D(i, 'a4')
		return i

	def Read_A94779E3(self, node): # Group feature outline
		i = self.ReadHeaderOutline(node, 'OutlineGroupFx')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt16A(i, 2, 'a1')
		i = node.ReadUInt32(i, 'key')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		if (node.get('u32_1') == 1):
			i = node.ReadFloat64A(i, 6, 'a2')
		else:
			node.content += ' a2=()'
		cnt, i = getUInt32(node.data, i)
		i = self.ReadFloat64A(node, i, cnt, 'a3', 3)
		i = node.ReadFloat64A(i, 6, 'box')
		i = node.ReadUInt8A(i, 2, 'a4')
		i = self.ReadEdgeList(node, i)
		return i

	def Read_A94779E4(self, node): # Multi feature outline
		i = self.ReadHeaderOutline(node, 'OutlineMultiFx')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a1')
		cnt, i = getUInt32(node.data, i)
		i = self.ReadFloat64A(node, i, cnt, 'a2', 12)
		cnt, i = getUInt32(node.data, i)
		i = self.ReadFloat64A(node, i, cnt, 'a3', 6)
		cnt, i = getUInt32(node.data, i)
		i = self.ReadFloat64A(node, i, cnt, 'a4', 3)
		i = node.ReadFloat64A(i, 6, 'box')
		i = node.ReadUInt8A(i, 2, 'a5')
		i = self.ReadEdgeList(node, i)
		i = node.ReadList2(i, importerSegNode._TYP_LIST_FLOAT64_A_, 'lst2', 3)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64A(i, 9, 'a6')
		return i
