# -*- coding: utf-8 -*-

'''
importerEeScene.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importer_Style import StyleReader
from importerUtils  import *
import importerSegNode

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

def __checkRef__(ref, attrName):
	if ((ref is not None) and (hasattr(ref.data, attrName) == False)):
		logError(u"    Read_%s should be an %s!", ref.typeName, attrName)

def __checkList__(node, lstName, attrName):
	lst = node.get(lstName)
	if (lst is not None):
		for ref in lst:
			__checkRef__(ref, attrName)
	else:
		logError("Read_%s hat no '%s' property!", node.typeName, lstName)

class EeSceneReader(StyleReader):
	def __init__(self, segment):
		super(EeSceneReader, self).__init__(segment)
		self.faces = []
		self.objects3D = []

	def Read_32RRR2(self, node, typeName = None):
		i = node.Read_Header0(typeName)
		i = node.ReadUInt32(i, 'flags') # until 2019 this is always 0 otherwise it references the element with sketch's index in DC-Segment
		i = node.ReadChildRef(i, 'styles')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_ColorAttr(self, offset, node):
		i = self.skipBlockSize(offset)
		i = node.ReadUInt8A(i, 2,  'ColorAttr.a0')
		i = node.ReadColorRGBA(i,  'ColorAttr.c0')
		i = node.ReadColorRGBA(i,  'ColorAttr.c1')
		i = node.ReadColorRGBA(i,  'ColorAttr.c2')
		i = node.ReadColorRGBA(i,  'ColorAttr.c3')
		i = node.ReadUInt16A(i, 2, 'ColorAttr.a5')
		node.object3D = True
		return i

	def ReadHeader3dObject(self, node, typeName = None, ref1Name = 'numRef'):
		i = node.Read_Header0(typeName)
		i = node.ReadUInt32(i, 'flags')
		i = node.ReadChildRef(i, 'styles')
		i = node.ReadChildRef(i, ref1Name)
		i = node.ReadCrossRef(i, 'ref2')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		node.object3D = True
		return i

	def ReadHeaderDimensioning(self, node, typeName = None):
		i = self.ReadHeader3dObject(node, typeName)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def ReadHeaderSurface(self, node, typeName  =None):
		if (typeName is None):
			typeName = 'Edge_%s' %(node.typeName)
		node.typeName = typeName
		i = self.skipBlockSize(0, 8)
		i = node.ReadParentRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_SINT32_A_, 'lst0', 2)
		node.surface = True
		return i

	def ReadHeaderEdge(self, node, typeName=None):
		if (typeName is None):
			typeName = 'Edge_%s' %(node.typeName)
		i = self.ReadHeader3dObject(node, typeName)
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'points', 3)
		node.edge = True
		return i

	def ReadHeaderParent(self, node, typeName = None):
		if (typeName is not None): node.typeName = typeName
		i = self.skipBlockSize(0, 8)
		i = node.ReadParentRef(i)
		i = self.skipBlockSize(i)
		return i

	def ReadHeaderNumRef(self, node, typeName, name):
		i = self.ReadHeaderParent(node, typeName)
		i = node.ReadUInt32(i, name)
		node.numref = True
		return i

	def ReadOptionalTransformation(self, node, offset):
		b, i = getBoolean(node.data, offset)
		if (b):
			i = self.ReadTransformation(node, i)
		return i

	def Read_120284EF(self, node):
		i = self.ReadHeaderSU32S(node, 'Attributes')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'attributes')
		return i

	def Read_13FC8170(self, node):
		i = self.ReadHeaderSU32S(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_5194E9A3(self, node): # Face
		i = self.ReadHeader3dObject(node, 'Face', ref1Name='surface')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'edges')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadFloat64A(i, 3, 'a2')
		i = node.ReadFloat64A(i, 3, 'a3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'index')
		i = node.ReadUInt32A(i, 2, 'a4')
		self.faces.append(node)
		return i

	def Read_6266D8CD(self, node): # Edge ...
		i = self.ReadHeaderEdge(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat32_3D(i, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32_3D(i, 'a3')
		i = self.skipBlockSize(i)
		return i

	def Read_D79AD3F3(self, node): # Edge ...
		i = self.ReadHeaderEdge(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT16_A_,  'lst1', 2)
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'lst2', 3)
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'lst3', 2)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst4')
		i = node.ReadFloat32_2D(i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst5')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst6')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst7')
		return i

	def Read_A79EACCB(self, node): # Edge ...
		i = self.ReadHeaderEdge(node)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_A79EACD2(self, node): # Edge ...
		i = self.ReadHeaderEdge(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT16_A_,  'lst1', 2)
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'lst2', 3)
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'lst3', 2)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst4')
		i = node.ReadFloat32_2D(i, 'a1')
		return i

	def Read_37DB9D1E(self, node): # Plane surface
		i = self.ReadHeaderSurface(node, 'SurfacePlane')
		return i

	def Read_03E3D90B(self, node):
		i = self.ReadHeaderSurface(node, 'SurfaceCylinder')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'center')
		i = node.ReadFloat64_3D(i, 'normal')
		return i

	def Read_6C6322EB(self, node):
		i = self.ReadHeaderSU32S(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		return i

	def Read_950A4A74(self, node):
		i = node.ReadUInt32A(0, 3, 'a0')
		return i

	def Read_A529D1E2(self, node): # GroupNode
		i = self.ReadHeaderU32RefU8List3(node, 'GroupNode')
		return i

	def Read_41305114(self, node):
		i = self.ReadHeader3dObject(node)
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat32_3D(i, 'a1')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_A79EACCF(self, node): # 3D-Object
		i = self.ReadHeader3dObject(node, '3dObject')
		if (node.get('ref2') is None):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'objects')
		else:
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'objects')
		i = self.ReadOptionalTransformation(node, i)
		self.objects3D.append(node)
		return i

	def Read_A79EACD3(self, node): # Point 3D-Object
		i = self.ReadHeader3dObject(node, 'Point3D')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')
		i = node.ReadFloat32(i, 'f32_0')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_50E809CD(self, node): # Points 3D-Object
		i = self.ReadHeader3dObject(node, 'Points')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_A_, 'points', 3)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT16_A_, 'lst1', 2)
		return i

	def Read_A79EACC7(self, node): # Line 3D-Object
		i = self.ReadHeader3dObject(node, 'Line3D')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')
		i = node.ReadFloat64(i, 'dirX')
		i = node.ReadFloat64(i, 'dirY')
		i = node.ReadFloat64(i, 'dirZ')
		return i

	def Read_4B57DC55(self, node): # Arc 3D-Object
		i = self.ReadHeader3dObject(node, 'Arc3D')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadFloat64(i, 'r')
		i = node.ReadAngle(i, 'startAngle')
		i = node.ReadAngle(i, 'sweepAngle')
		return i

	def Read_A79EACCC(self, node): # Circle 3D-Object
		i = self.ReadHeader3dObject(node, 'Circle3D')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')
		i = node.ReadFloat64_3D(i, 'normal')
		i = node.ReadFloat64_3D(i, 'm')
		i = node.ReadFloat64(i, 'r')
		i = node.ReadFloat64(i, 'startAngle')
		i = node.ReadFloat64(i, 'sweepAngle')
		node.set('points', [])
		return i

	def Read_4B57DC56(self, node): # Ellipse2D
		i = self.ReadHeader3dObject(node, 'Ellipse2D')
		i = node.ReadFloat64_2D(i, 'c')       # center of the ellipse
		i = node.ReadFloat64(i, 'b')          # length for point B
		i = node.ReadFloat64(i, 'a')          # length for point A
		i = node.ReadFloat64_2D(i, 'dB')      # direction vector-2D for point B
		i = node.ReadFloat64_2D(i, 'dA')      # direction vector-2D for point A
		i = node.ReadFloat64(i, 'startAngle')
		i = node.ReadFloat64(i, 'sweepAngle')
		return i

	def Read_D3A55701(self, node): # Spline2D 3D-Object
		i = self.ReadHeader3dObject(node, 'Spline2D_Curve')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadUInt8A(i, 8, 'a1')
		i = self.Read_Float32Arr(i, node, 'lst0')
		i = self.Read_Float32Arr(i, node, 'lst1')
		i = self.Read_Float64Arr(i, node, 2, 'lst2')
		i = node.ReadUInt8A(i, 8, 'a2')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadFloat64_2D(i, 'a4')
		i = self.Read_Float64Arr(i, node, 2, 'lst3')
		return i

	def Read_D3A55702(self, node): # Spline3D 3D-Object
		i = self.ReadHeader3dObject(node, 'Spline3D_Curve')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadUInt8A(i, 8, 'a1')
		i = self.Read_Float32Arr(i, node, 'lst0')
		i = self.Read_Float32Arr(i, node, 'lst1')
		i = self.Read_Float64Arr(i, node, 3, 'knots') # knots
		i = node.ReadUInt8A(i, 8, 'a2')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadFloat64_2D(i, 'a4')
		return i

	def Read_A79EACD5(self, node): # Text 3D-Object
		i = self.ReadHeader3dObject(node, 'Text3D')
		i = node.ReadLen32Text16(i)
		i = node.ReadFloat64_3D(i , 'vec')
		i = node.ReadFloat64_3D(i , 'a0')
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_E1EB685C(self, node): # MeshFacets 3D-Object
		i = self.ReadHeader3dObject(node, 'MeshFacets')
		i = node.ReadChildRef(i, 'points')
		i = node.ReadChildRef(i, 'pointIndices')
		i = node.ReadChildRef(i, 'normals')
		i = node.ReadChildRef(i, 'normalIndices')
		i = node.ReadUInt32A(i, 5, 'a0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_D1071D57(self, node): # Constraint 3D imension Item
		i = self.ReadHeader3dObject(node, 'Constraint3DimensionItem')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		a3, i = getUInt16A(node.data, i, 2)
#		i = self.ReadTransformation(node, i)
		return i

	def Read_3A5FA872(self, node): # ??? 3D-Object
		i = self.ReadHeader3dObject(node)
		return i

	def Read_A79EACCD(self, node): # ??? 3D-Object
		i = self.ReadHeader3dObject(node)
		i = node.ReadFloat32A(i, 10, 'a0') # ffffffffff
		i = node.ReadFloat64A(i, 2, 'a1')
		return i

	def Read_AFD5CEEB(self, node): # ??? 3D-Object
		i = self.ReadHeader3dObject(node)
		i = node.ReadFloat64A(i, 13, 'a0')
		return i


	def Read_B069BC6A(self, node): # ??? 3D-Object
		i = self.ReadHeader3dObject(node)
		i = node.ReadUInt16A(i, 8, 'a0')
		return i

	def Read_B247B180(self, node): # ??? 3D-Object
		return self.ReadHeaderDimensioning(node)
		return i

	def Read_23ADA14E(self, node): # ??? 3D-Object
		return self.ReadHeaderDimensioning(node)

	def Read_9516E3A1(self, node): # ??? 3D-Object
		return self.ReadHeaderDimensioning(node)

	def Read_B01025BF(self, node): # ??? 3D-Object
		return self.ReadHeaderDimensioning(node)

	def Read_BCC1E889(self, node): # ??? 3D-Object
		return self.ReadHeaderDimensioning(node)

	def Read_C2F1F8ED(self, node): # ??? 3D-Object
		return self.ReadHeaderDimensioning(node)

	def Read_C46B45C9(self, node): # ??? 3D-Object
		return self.ReadHeaderDimensioning(node)

	def Read_FF084971(self, node): # ??? 3D-Object
		return self.ReadHeaderDimensioning(node)

	def Read_FFB5643C(self, node): # ??? 3D-Object
		return self.ReadHeaderDimensioning(node)

	def Read_B91E695F(self, node): # MultiBodyNode
		i = node.Read_Header0('MultiBodyNode')
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
		i = node.ReadFloat64_2D(i, 'a4')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_0BC8EA6D(self, node): # key reference
		i = self.ReadHeaderNumRef(node, 'RefByKey_1', 'key')
		return i

	def Read_4AD05620(self, node): # key reference
		i = self.ReadHeaderNumRef(node, 'RefByKey_2', 'key')
		return i

	def Read_5D916CE9(self, node): # key reference
		i = self.ReadHeaderNumRef(node, 'RefByKey_3', 'key')
		return i

	def Read_B9274CE3(self, node): # key reference
		i = self.ReadHeaderNumRef(node, 'RefByKey_4', 'key')
		return i

	def Read_F6ADCC68(self, node): # Index definition
		i = self.ReadHeaderNumRef(node, 'DefIndexPoint', 'index')
		return i

	def Read_F6ADCC69(self, node): # Index definition
		i = self.ReadHeaderNumRef(node, 'DefIndexLine', 'index')
		return i

# _______________________________________

	def Read_3D953EB2(self, node):
		i = self.ReadHeaderParent(node, 'RefByIndexPoint')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'index') # reference to a Work-Points's index
		node.numref = True
		return i

	def Read_3EA856AC(self, node):
		i = self.ReadHeaderParent(node, 'RefByIndexAxis')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'index') # reference to a Work-Axis's index
		node.numref = True
		return i

	def Read_591E9565(self, node): # Index reference
		i = self.ReadHeaderParent(node, 'RefByIndexPlane')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'index') # reference to a Work-Plane's index
		node.numref = True
		return i

	def Read_0BBBEBC8(self, node):
		i = self.ReadHeaderParent(node, 'DefIndex_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'index') # reference to a Work-Plane's index
		node.numref = True
		return i

	def postRead(self):
		for face in self.faces:
			__checkRef__(face.get('surface'), 'surface')
			__checkList__(face, 'edges', 'edge')
		for obj in self.objects3D:
			__checkRef__(obj.get('numRef'), 'numref')
			__checkList__(obj, 'objects', 'object3D')
		return super(EeSceneReader, self).postRead()