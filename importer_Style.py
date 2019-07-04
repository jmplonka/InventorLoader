# -*- coding: utf-8 -*-

import importerSegNode

from importerSegment import SegmentReader
from importerUtils   import *

'''
importer_Style.py:
'''

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class StyleReader(SegmentReader):
	def __init__(self, segment):
		super(StyleReader, self).__init__(segment)

	def ReadHeaderStyle(self, node, typeName=None):
		if (typeName is not None): node.typeName = typeName
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_48EB8607(self, node):
		node.typeName = "ObjctStyles"
		i = self.skipBlockSize(0)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'styles')
		return i

	def Read_0AE12F04(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_0AE12F04')
		i = node.ReadFloat64_3D(i, 'vec_1')
		i = node.ReadFloat64_3D(i, 'vec_2')
		i = node.ReadLen32Text16(i)
		return i

	def Read_440D2B29(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_440D2B29')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_48EB8608(self, node): # Line color style
		i = self.ReadHeaderStyle(node, 'Style_LineColor')
		i = node.ReadColorRGBA(i, 'c0')
		i = node.ReadColorRGBA(i, 'c1')
		i = node.ReadColorRGBA(i, 'c2')
		i = node.ReadColorRGBA(i, 'c3')
		i = node.ReadColorRGBA(i, 'c4')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_6E176BB6(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_B32BF6A7')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadFloat64_3D(i, 'vec')
		i = node.ReadFloat64(i, 'f64_1')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_7333F86D(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_7333F86D')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 4, 'a0')
		if (getFileVersion() > 2018):
			i = node.ReadFloat64_2D(i, 'a1')
			i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_824D8FD9(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_824D8FD9')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_7AE0E1A3(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_7AE0E1A3')
		i = node.ReadFloat64_2D(i, 'a0')
		return i

	def Read_89CE3F34(self, node):
		i = self.ReadHeaderStyle(node, 'Style_89CE3F34')
		return i # '<LdddddLB'

	def Read_8F0B160B(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_8F0B160B')
		i = node.ReadColorRGBA(i, 'c0')
		i = node.ReadColorRGBA(i, 'c1')
		i = node.ReadColorRGBA(i, 'c2')
		i = node.ReadColorRGBA(i, 'c3')
		i = node.ReadColorRGBA(i, 'c4')
		i = node.ReadUInt16A(i, 2, 'a10')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 10, 'a11')
		return i

	def Read_8F0B160C(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_8F0B160C')
		i = node.ReadUInt16A(i, 10, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 3, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_9795E56A(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_9795E56A')
		i = node.ReadFloat64_3D(i, 'vec')
		if (getFileVersion() > 2013):
			i = node.ReadFloat64_3D(i, 'dir')
		return i

	def Read_AF48560F(self, node): # Primary color attribute style
		i = self.ReadHeaderStyle(node, 'Style_PrimColorAttr')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_B255D907(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_B255D907')
		i = node.ReadFloat64_3D(i, 'vec')
		return i

	def Read_B32BF6A2(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_B32BF6A2')
		i = node.ReadFloat32A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32A(i, 4, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32A(i, 4, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32A(i, 4, 'a3')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32(i, 'f32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_B32BF6A3(self, node): # visibility style
		i = self.ReadHeaderStyle(node, 'Style_Visibility')
		i = node.ReadBoolean(i, 'visible')
		return i

	def Read_B32BF6A5(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_B32BF6A5')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_B32BF6A6(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_Solid')
		i = node.ReadBoolean(i, 'solid')
		return i

	def Read_B32BF6A7(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_B32BF6A7')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadFloat64_3D(i, 'vec')
		i = node.ReadFloat64(i, 'f64_1')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_B32BF6A8(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_B32BF6A8')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_B32BF6A9(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_B32BF6A9')
		i = node.ReadUInt16(i, 'u16_1') # Enm???
		return i

	def Read_B32BF6AB(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_B32BF6AB')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_B32BF6AC(self, node): # line style
		i = self.ReadHeaderStyle(node, 'Style_Line')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat32(i, 'width')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_1')
		cnt, i = getUInt16(node.data, i)
		a1 = []
		for j in range(cnt):
			u, i = getUInt32(node.data, i)
			f, i = getFloat32(node.data, i)
			a1.append((u, f))
		node.content += u" a1=[%s]" %(u",".join(["(%04X,%g)" %(x[0], x[1]) for x in a1]))
		node.set('a1', a1)
		i = node.ReadFloat32_3D(i, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a3')
		return i

	def Read_B32BF6AE(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_B32BF6AE')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64_3D(i , 'a0')
		i = node.ReadFloat64_3D(i , 'a1')
		i = node.ReadFloat64_3D(i , 'a2')
		return i

	def Read_BBC99377(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_BBC99377')
#		i = node.ReadUInt16A(i, 4, 'a1')
#		i = node.ReadUInt8A(i, 5, 'a2')
#		i = node.ReadFloat64_3D(i, 'a3')
#		i = node.ReadFloat64_3D(i, 'a4')
#		i = node.ReadUInt32(i, 'u32_0')
#		i = self.skipBlockSize(i)
#		i = node.ReadCrossRef(i, 'xref_0')
#		i = self.skipBlockSize(i)
#		i = node.ReadUInt8A(i, 3, 'a5')
#		if (node.get('u32_0') == 0):
#			i = node.ReadFloat64_3D(i, 'a6')
#			node.get('a6').insert(0, 0.0)
#		else:
#			i = node.ReadFloat64A(i, 4, 'a6')
#		i = node.ReadUInt8(i, 'u8_0')
#		u8_0 = node.get('u8_0')
#		if (u8_0 == 0x74):
#			i = node.ReadFloat64A(i, 0x0B, 'a7')
#		elif (u8_0 == 0x72):
#			i = node.ReadFloat64A(i, 0x10, 'a7')
#		elif (u8_0 == 0x7D):
#			i = node.ReadFloat64A(i, 0x07, 'a7')
#		i = node.ReadUInt8(i, 'u8_1')
#		i = node.ReadUInt16A(i , 2, 'a8')
#		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
#		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
#		i = node.ReadUInt8(i, 'u8_2')
		return i

	def Read_C29D5C11(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_C29D5C11')
		i = node.ReadFloat64_3D(i, 'a0')
		return i

	def Read_F2FB355D(self, node): # Object style ...
		i = self.ReadHeaderStyle(node, 'Style_F2FB355D')
		i = node.ReadUInt32(i,  'u32_1')
		i = node.ReadSInt32(i,  's32_1')
		i = node.ReadFloat32(i, 'f32_1')
		i = node.ReadBoolean(i, 'b1')
		return i
