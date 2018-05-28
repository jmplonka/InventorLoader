# -*- coding: utf-8 -*-

'''
importerGraphics.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) graphics data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

import traceback
from importerSegment        import SegmentReader, checkReadAll
from importerSegNode        import AbstractNode, GraphicsNode
from importerClasses        import B32BF6AC, _32RRR2, _32RA
from importerTransformation import Transformation
from importerUtils          import *

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class GraphicsReader(SegmentReader):

	def __init__(self):
		super(GraphicsReader, self).__init__(True)

	def createNewNode(self):
		return GraphicsNode()

	def skipDumpRawData(self):
		return True

	def Read_32RA(self, node):
		i = node.Read_Header0()
		u16_0, i = getUInt16(node.data, i)
		u16_1, i = getUInt16(node.data, i)
		i = node.ReadChildRef(i)
		u8_0, i = getUInt8(node.data, i)
		i = self.skipBlockSize(i)

		val = _32RA(u16_0, u16_1, u8_0)
		node.set('32RRR2', val)
		node.content += ' 32RR2={%s}' %(val)

		return i

	def Read_32RRR2(self, node):
		i = node.Read_Header0()
		u16_0, i = getUInt16(node.data, i)
		u16_1, i = getUInt16(node.data, i)
		i = node.ReadChildRef(i)
		i = node.ReadChildRef(i)
		i = node.ReadParentRef(i)
		u32_0, i = getUInt32(node.data, i)
		i = self.skipBlockSize(i)

		val = _32RRR2(u16_0, u16_1, u32_0)
		node.set('32RA', val)
		node.content += ' 32RA={%s}' %(val)

		return i

	def Read_ColorAttr(self, offset, node):
		i = self.skipBlockSize(offset)
		i = node.ReadUInt8A(i, 2, 'ColorAttr.a0')
		i = node.ReadColorRGBA(i, 'ColorAttr.c0')
		i = node.ReadColorRGBA(i, 'ColorAttr.c1')
		i = node.ReadColorRGBA(i, 'ColorAttr.c2')
		i = node.ReadColorRGBA(i, 'ColorAttr.c3')
		i = node.ReadUInt16A(i, 2, 'ColorAttr.a5')

		return i

	def Read_HeaderParent(self, node):
		i = self.skipBlockSize(0, 8)
		i = node.ReadParentRef(i)
		i = self.skipBlockSize(i)
		return i

	def Read_TypedFloat(self, offset, node):
		cnt, i = getUInt32(node.data, offset)
		lst0 = []
		j = 0
		node.content += ' {'
		while (j < cnt):
			j += 1
			t, i = getUInt32(node.data, i)
			if (t == 0x0B):
				a0, i = getFloat64A(node.data, i, 0x0C)
				lst0.append(a0)
				node.content += ' %d: (%s)' %(j, FloatArr2Str(a0))
			elif (t == 0x11):
				a0, i = getFloat64A(node.data, i, 0x0D)
				lst0.append(a0)
				node.content += ' %d: (%s)' %(j, FloatArr2Str(a0))
			elif (t == 0x17):
				a0, i = getFloat64A(node.data, i, 0x06) # X, Y, Z, n, m, k
				lst0.append(a0)
				node.content += ' %d: (%s)' %(j, FloatArr2Str(a0))
			else:
				logError(u"ERROR> Don't know how to handle %X in {%s}!", t, node.typeID)
		node.content += '}'
		node.set('TypedFloat.lst0', lst0)
		return i

	def ReadTransformation(self, node, offset):
		'''
		Read the transformation matrix
		'''
		val = Transformation()
		node.set('transformation', val)
		i = val.read(node.data, offset)
		node.content += '%s' %(val)
		return i

	def Read_Float32Arr(self, offset, node, name):
		cnt0, i = getUInt32(node.data, offset)
		i = node.ReadUInt32A(i, 2, 'Float32Arr_' + name)

		lst = []
		l2 = []
		j = 0
		while (j < cnt0):
			j += 1
			a1, i = getFloat32A(node.data, i, 2)
			lst.append(a1)
			vec = FloatArr2Str(a1)
			l2.append('(%s)' %(vec))

		if (len(l2) > 0):
			node.content += ' {%s}' %(','.join(l2))
		node.set(name, lst)

		return i

	def Read_Float64Arr(self, offset, node, l, name):
		cnt0, i = getUInt32(node.data, offset)
		i = node.ReadUInt32A(i, 2, 'Float64Arr_' + name)

		lst = []
		l2 = []
		j = 0
		while (j < cnt0):
			j += 1
			a1, i = getFloat64A(node.data, i, l)
			lst.append(a1)
			vec = FloatArr2Str(a1)
			l2.append('(%s)' %(vec))

		if (len(l2) > 0):
			node.content += ' {%s}' %(','.join(l2))
		node.set(name, lst)

		return i

	def Read_022AC1B1(self, node):
		i = node.ReadUInt8(0, 'u8')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')

		return i

	def Read_022AC1B5(self, node):
		'''
		Part drawing Attribute
		'''
		node.typeName = 'PDrwAttr'
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')

		if (getFileVersion() >= 2015):
			i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		else:
			i = node.ReadUInt16A(i, 2, 'a1')

		i = node.ReadUInt16A(i, 3, 'a2')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 2, 'a0')

		return i

	def Read_0244393C(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'keyRef')

		return i

	def Read_0270FFC7(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_2')

		return i

	def Read_03E3D90B(self, node):
		i = self.Read_HeaderParent(node)
		i = node.ReadList2(i, AbstractNode._TYP_UINT32A_, 'lst0', 2)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 3, 'vec3d_1')
		i = node.ReadFloat64A(i, 3, 'vec3d_2')

		return i

	def Read_0AE12F04(self, node):
		i = node.ReadUInt32(0, 'u32_0')
		i = node.ReadFloat64A(i, 3, 'vec3d_1')
		i = node.ReadFloat64A(i, 3, 'vec3d_2')
		i = node.ReadLen32Text16(i)

		return i

	def Read_0B2C8AE9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt16A(i, 4, 'a0')
		return i

	def Read_0BC8EA6D(self, node):
		'''
		ParentKeyRef
		'''
		node.typeName = 'KeyRef'
		i = self.Read_HeaderParent(node)
		i = node.ReadUInt32(i, 'key')
		return i

	def Read_0DE8E459(self, node):
		i = self.Read_32RA(node)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64A(i, 3, 'a3')
		i = node.ReadUInt32(i, 'u32_1')

		return i

	def Read_120284EF(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)

		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')

		return i

	def Read_12A31E33(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 5, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 8, 'a1')
		i = self.skipBlockSize(i, 8)

		return i

	def Read_13FC8170(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def Read_14533D82(self, node):
		'''
		Workplane
		'''
		node.typeName = 'WrkPlane'
		i = self.Read_32RA(node)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 6, 'a3')
		i = node.ReadFloat64A(i, 3, 'a4')
		i = node.ReadFloat64A(i, 3, 'a5')

		return i

	def Read_184FDA9C(self, node): return 0

	def Read_189725D1(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadSInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i  = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')

		return i

	def Read_23ADA14E(self, node): return 0

	def Read_2C7020F6(self, node):
		'''
		Workaxis
		'''
		node.typeName = 'WrkAxis'
		i = self.Read_32RA(node)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 6, 'a0')
		i = self.ReadTransformation(node, i)
		i = node.ReadUInt8A(i, 3, 'a3')

		return i

	def Read_2C7020F8(self, node):
		'''
		Workpoint
		'''
		node.typeName = 'WrkPoint'
		i = self.Read_32RA(node)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 6, 'a3')
		i = self.ReadTransformation(node, i)
		i = node.ReadUInt16(i, 'u16_0')

		return i

	def Read_37DB9D1E(self, node):
#		i = self.Read_HeaderParent(node)
#		i  = node.ReadList2(i, AbstractNode._TYP_2D_SINT32_, 'lst0')
#		i = node.ReadSInt32(i, 'u32_0')
#		i = node.ReadUInt8(i, 'u8_0')
		i = len(node.data)

		return i

	def Read_3D953EB2(self, node):
		i = self.Read_HeaderParent(node)
		i = node.ReadUInt32A(i, 2, 'a1')

		return i

	def Read_3DA2C291(self, node):
		i = self.Read_32RA(node)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8A(i, 4, 'a2')

		return i

	def Read_3EA856AC(self, node):
		i = self.Read_HeaderParent(node)
		i = node.ReadUInt32A(i, 2, 'a0')

		return i

	def Read_41305114(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat32(i, 'f32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat32A(i, 5, 'a0')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')

		return i

	def Read_438452F0(self, node):
		i = node.ReadUInt16A(0, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 5, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 8, 'a1')
		i = self.skipBlockSize(i, 8)

		return i

	def Read_440D2B29(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')

		return i

	def Read_48EB8607(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_48EB8608(self, node):
		node.typeName = '2dLineColor'
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadColorRGBA(i, 'c0')
		i = node.ReadColorRGBA(i, 'c1')
		i = node.ReadColorRGBA(i, 'c2')
		i = node.ReadColorRGBA(i, 'c3')
		i = node.ReadColorRGBA(i, 'c4')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_4AD05620(self, node):
		'''
		ParentKeyRef
		'''
		node.typeName = 'KeyRef'
		i = self.Read_HeaderParent(node)
		i = node.ReadUInt32(i, 'key')
		return i

	def Read_4B57DC55(self, node):
		node.typeName = '2dCircle'
		i = self.Read_32RRR2(node)
		i = node.ReadFloat64A(i, 3, 'm')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadFloat64(i, 'r')
		# start angle
		i = node.ReadAngle(i, 'alpha')
		# stop angle
		i = node.ReadAngle(i, 'beta')

		return i

	def Read_4B57DC56(self, node):
		node.typeName = '2dEllipse'

		i = self.Read_32RRR2(node)
		i = node.ReadFloat64A(i, 2, 'c')
		i = node.ReadFloat64(i, 'b')      # length for point B
		i = node.ReadFloat64(i, 'a')      # length for point A
		i = node.ReadFloat64A(i, 2, 'dB') # direction vector-2D for point B
		i = node.ReadFloat64A(i, 2, 'dA') # direction vector-2D for point A
		# start angle
		i = node.ReadAngle(i, 'alpha')
		# stop angle
		i = node.ReadAngle(i, 'beta')

		return i

	def Read_4E951290(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')

		return i

	def Read_4E951291(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_50E809CD(self, node):
		'''
		2D-Point
			GUID = {50e809cd-11d2-7827-6000-75b72c39cdb0}
		'''
		node.typeName = '2dPoint'
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_3D_FLOAT32_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst1')

		return i

	def Read_5194E9A2(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadFloat64A(i, 3, 'a0')
		i = node.ReadFloat64A(i, 3, 'a1')

		return i

	def Read_5194E9A3(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
#		i = node.ReadUInt8(i, 'u8_0')
#		i = self.skipBlockSize(i, 8)
#		i = node.ReadFloat64A(i, 3, 'a2')
#		i = node.ReadFloat64A(i, 3, 'a3')
#		i = self.skipBlockSize(i)
#		i = node.ReadUInt32A(i, 3, 'a4')
		i = len(node.data)
		return i

	def Read_591E9565(self, node):
		i = self.Read_HeaderParent(node)
		i = node.ReadUInt32A(i, 2, 'a0')

		return i

	def Read_5D916CE9(self, node):
		'''
		ParentKeyRef
		'''
		node.typeName = 'KeyRef'
		i = self.Read_HeaderParent(node)
		i = node.ReadUInt32(i, 'key')
		return i

	def Read_5EDE1890(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 6, 'a1')

		return i

	def Read_60FD1845(self, node):
		'''
		2D-Sketch
			GUID = {60fd1845-11d0-d79d-0008-bfbb21eddc09}
			lst1 map with elements
			lst3 map with spezial elements (e.g. Text)
		'''
		node.typeName = '2dSketch'
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')

		lst0 = node.get('lst0')
		assert (len(lst0) == 0 or len(lst0) == 1), '%s: unknown format for list length = %d!' %(node.typeID, len(lst0))

		i = self.skipBlockSize(i)

		if (len(lst0) == 0):
			i = node.ReadChildRef(i)
		elif (len(lst0) == 1):
			i = node.ReadChildRef(i)
			i = node.ReadChildRef(i)

		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'key')
		i = self.ReadTransformation(node, i)
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst2')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst3')
		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_6266D8CD(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_3D_FLOAT32_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8A(i, 13, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32A(i, 3, 'a3')
		i = self.skipBlockSize(i)

		return i

	def Read_6A6931DC(self, node):
#		i = self.skipBlockSize(0)
#		i = node.ReadUInt32(i, 'u32_0')
#		i = self.Read_TypedFloat(i, node)
#		i = node.ReadList2(i, AbstractNode._TYP_LIST_3D_FLOAT64_, 'lst0')
#		i = node.ReadFloat64A(i, 6, 'a0')
		i = len(node.data)
		return i

	def Read_6C6322EB(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i  = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def Read_6C8A5C53(self, node):
		i = self.Read_32RA(node)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64A(i, 6, 'a4')
		i = node.ReadUInt8A(i, 4, 'a5')

		return i

	def Read_7333F86D(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadFloat64A(i, 2, 'a1')
		i = node.ReadUInt32(i, 'u32_2')

		return i

	def Read_76986821(self, node): return 0

	def Read_7AE0E1A3(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'a0')

		return i

	def Read_7DFC2448(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'key')

		return i

	def Read_824D8FD9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i  = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')

		return i

	def Read_8DA49A23(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 5, 'a1')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt16A(i, 4, 'a2')

		return i

	def Read_8F0B160B(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
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

	def Read_8F0B160C(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 10, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 3, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')

		return i

	def Read_9215A162(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt16A(i, 2, 'a2')

		return i

	def Read_9360CF4D(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadFloat64(i, 'f64_0')

		if (getFileVersion() > 2013):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
		else:
			node.set('lst1', [])

		return i

	def Read_9516E3A1(self, node):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def Read_9795E56A(self, node):
#		i = node.ReadUInt32(0, 'u32')
#		i = node.ReadFloat64A(i, 3, 'a0')
		i = len(node.data)
		return i

	def Read_9A676A50(self, node):
		'''
		Body
		'''
		node.typeName = 'Body'
		i = self.Read_32RA(node)
		i = node.ReadParentRef(i)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadChildRef(i)
		i = node.ReadUInt16A(i, 7, 'a1')
		i = node.ReadCrossRef(i)
		i = node.ReadCrossRef(i)
		i = node.ReadChildRef(i)
		i = node.ReadChildRef(i)
		i = node.ReadChildRef(i)
		i = node.ReadList2(i, AbstractNode._TYP_2D_F64_U32_4D_U8_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'a2')
		i = self.skipBlockSize(i, 8)
		i = node.ReadList7(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
#		i = node.ReadUInt16A(i, 4, 'a3')
#
#		a4, dummy = getUInt16A(node.data, i, 2)
#		if (a4[0] == 0x02 and a4[1] == 0x3000):
#			i = node.ReadList2(i, AbstractNode._TYP_1D_UINT32_, 'lst0')
#			i = node.ReadList2(i, AbstractNode._TYP_1D_UINT32_, 'lst0')
#			i = node.ReadUInt16A(i, 2, 'a4')
#		else:
#			node.set('lst2', [])
#			node.set('lst3', [])
#			i = dummy
#
#		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_A3EBE198(self, node): return 0

	def Read_A529D1E2(self, node):
		i = self.Read_32RA(node)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')

		return i

	def Read_A6DD2FCC(self, node): return 0

	def Read_A79EACC7(self, node):
		'''
		2D-Line
		'''
		node.typeName = '2dLine'
		i = self.Read_32RRR2(node)
		i = node.ReadFloat64A(i, 3, 'p1')
		i = node.ReadFloat64A(i, 3, 'p2')

		return i

	def Read_A79EACCB(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_3D_FLOAT32_, 'lst0')
		i = node.ReadUInt8(i, 'u8')

		return i

	def Read_A79EACCC(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadFloat64A(i, 12, 'a2')
		i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_A79EACCF(self, node):
		'''
		3D-Object
		'''
		node.typeName = '3dObject'
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		if (node.get('u8_0') == 1):
			i = node.ReadUInt8A(i, 4, 'a0')
			i = node.ReadFloat64A(i, 3, 'a1')

		return i

	def Read_A79EACD2(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_3D_FLOAT32_, 'lst0')
		i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst1')
		i = node.ReadList2(i, AbstractNode._TYP_3D_FLOAT32_, 'lst2')
		i = node.ReadList2(i, AbstractNode._TYP_2D_FLOAT32_, 'lst3')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst4')
		i = node.ReadFloat32A(i, 2, 'a1')

		return i

	def Read_A79EACD3(self, node):
		'''
		LinePoint
		'''
		node.typeName = 'LinePoint'
		i = self.Read_32RRR2(node)
		i = node.ReadFloat64A(i, 3, 'vec')
		i = node.ReadFloat32(i, 'f32_0')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt16(i, 'u16_0')

		return i

	def Read_A79EACD5(self, node):
		'''
		2D-Text
		'''
		node.typeName = '2dText'
		i = self.Read_32RRR2(node)
		i = node.ReadLen32Text16(i )
		i = node.ReadFloat64A(i , 3, 'vec')
		i = node.ReadFloat64A(i , 3, 'a0')
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_A94779E0(self, node):
		'''
		SingleFeatureOutline
		'''
		node.typeName = 'SingleFeatureOutline'
		i = self.skipBlockSize(0)

		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadFloat64A(i, 3, 'a1')
		i = node.ReadFloat64A(i, 3, 'a2')
		i = self.Read_TypedFloat(i, node)
		#i = node.ReadList2(i, AbstractNode._TYP_LIST_3D_FLOAT64_, 'lst0')

		return i

	def Read_A94779E2(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt16A(i, 4, 'a2')
		i = node.ReadFloat64A(i, 3, 'a3')
		i = node.ReadFloat64A(i, 3, 'a4')

		if (node.get('a1')[2] == 1):
			i = node.ReadFloat64A(i, 3, 'a5_0')
			i = node.ReadFloat64A(i, 3, 'a5_1')
			i = node.ReadFloat64A(i, 3, 'a5_2')
			i = node.ReadFloat64A(i, 3, 'a5_3')

		if (node.get('a2')[2] == 1):
			i = node.ReadFloat64A(i, 3, 'a6_0')

		i = node.ReadUInt8A(i, 2, 'a7')
		i = self.Read_TypedFloat(i, node)
		i = node.ReadList2(i, AbstractNode._TYP_LIST_3D_FLOAT64_, 'lst1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'cnt3')
		i = node.ReadFloat64A(i, 4, 'a8')
		i = node.ReadUInt8A(i, 6, 'a9')
		i = node.ReadUInt32(i, 'cnt4')
		i = node.ReadFloat64A(i, 4, 'a10')
		i = node.ReadUInt8A(i, 5, 'a11')
		cnt1, i = getUInt32(node.data, i)
		j = 0
		lst2 = []
		while (j < cnt1):
			j += 1
			i = self.ReadTransformation(node, i)
			lst2.append(node.get('transformation'))
		node.set('lst2', lst2)
		node.delete('CodedFloatB.a0')
		node.delete('CodedFloatB.a1')
		return i

	def Read_A94779E3(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32A(i, 5, 'a1')
		i = node.ReadFloat64A(i, 3, 'a2')
		i = node.ReadFloat64A(i, 3, 'a3')
		i = node.ReadUInt8A(i, 2, 'a4')
		i = self.Read_TypedFloat(i, node)
		i = node.ReadList2(i, AbstractNode._TYP_LIST_3D_FLOAT64_, 'lst1')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 7, 'a6')
		if (getFileVersion() > 2016):
			i = node.ReadUInt16A(i, 13, 'a7')
		else:
			i = node.ReadUInt8A(i, 1, 'a7')

		return i

	def Read_A94779E4(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadUInt32(i, 'u32_0')

		if (node.get('u32_0') != 0):
			i = node.ReadFloat64A(i, 12, 'a2')
		else:
			node.set('a2', [])
			node.content += ' ()'

		i = node.ReadUInt32(i, 'u32_1')
		if (node.get('u32_1') != 0):
			i = node.ReadFloat64A(i, 12, 'a3')
		else:
			node.set('a3', [])
			node.content += ' ()'

		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat64A(i, 6, 'a4')
		i = node.ReadUInt16A(i, 3, 'a5')
		i   = node.ReadList2(i, AbstractNode._TYP_GUESS_, 'lst1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 7, 'a6')
		i = node.ReadFloat64A(i, 3, 'a7')
		i = node.ReadFloat64A(i, 3, 'a8')

		return i

	def Read_A98235C4(self, node):
		i = self.Read_32RA(node)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 2, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8A(i, 4, 'a3')
		i = node.ReadUInt32(i, 'u32_0')

		if (getFileVersion() < 2012):
			i = node.ReadUInt16A(i, 5, 'a4')
		else:
			i = node.ReadUInt16A(i, 7, 'a4')

		if (node.get('u32_0') == 1):
			i = node.ReadUInt16A(i, 3, 'a5')
			i = node.ReadFloat64(i, 'f64_0')
		else:
			node.set('a5', [])
			node.set('f64_0', 0.0)
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def Read_AF48560F(self, node):
		'''
		ColorStyle primary Attribute
		'''
		node.typeName = 'PrmColorAttr'
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 7, 'a0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def Read_AFD5CEEB(self, node): return 0

	def Read_B01025BF(self, node):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def Read_B069BC6A(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadUInt16A(i, 8, 'a0')

		return i

	def Read_B1057BE1(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 13, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)

		return i

	def Read_B1057BE2(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 13, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)

		return i

	def Read_B1057BE3(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 13, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)

		return i

	def Read_B247B180(self, node): return 0

	def Read_B255D907(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 3, 'a0')

		return i

	def Read_B32BF6A2(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt16(i, 'u16_0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)

		return i

	def Read_B32BF6A3(self, node):
		node.typeName = 'Visibility'
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_B32BF6A5(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')

		return i

	def Read_B32BF6A6(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_B32BF6A7(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadFloat64A(i, 3, 'vec')
		i = node.ReadFloat64(i, 'f64_1')
		i = node.ReadUInt32(i, 'u32_1')

		return i

	def Read_B32BF6A8(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')

		return i

	def Read_B32BF6A9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')

		return i

	def Read_B32BF6AB(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_B32BF6AC(self, node):
		node.typeName = 'LineStyle'
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat32(i, 'width')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_1')
		cnt, i = getUInt16(node.data, i)
		j = 0
		a1 = []
		while (j < cnt):
			j += 1
			u32_0, i = getUInt32(node.data, i)
			f32_0, i = getFloat32(node.data, i)
			x = B32BF6AC(u32_0, f32_0)
			a1.append(x)
		node.set('a1', a1)
		i = node.ReadFloat32A(i, 3, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a3')

		return i

	def Read_B32BF6AE(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64A(i , 3, 'a0')
		i = node.ReadFloat64A(i , 3, 'a1')
		i = node.ReadFloat64A(i , 3, 'a2')

		return i

	def Read_B3895BC2(self, node):
		i = node.ReadUInt32A(0, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(i, node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 5, 'a1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 8, 'a2')
		i = self.skipBlockSize(i, 8)

		return i

	def Read_B9274CE3(self, node):
		i = self.Read_HeaderParent(node)
		i = node.ReadUInt32(i, 'key')
		return i

	def Read_BBC99377(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a1')
		i = node.ReadUInt8A(i, 5, 'a2')
		i = node.ReadFloat64A(i, 3, 'a3')
		i = node.ReadFloat64A(i, 3, 'a4')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xref_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8A(i, 3, 'a5')
		if (node.get('u32_0') == 0):
			i = node.ReadFloat64A(i, 3, 'a6')
			node.get('a6').insert(0, 0.0)
		else:
			i = node.ReadFloat64A(i, 4, 'a6')

		i = node.ReadUInt8(i, 'u8_0')
		u8_0 = node.get('u8_0')
		if (u8_0 == 0x74):
			i = node.ReadFloat64A(i, 0x0B, 'a7')
		elif (u8_0 == 0x72):
			i = node.ReadFloat64A(i, 0x10, 'a7')
		elif (u8_0 == 0x7D):
			i = node.ReadFloat64A(i, 0x07, 'a7')

		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i , 2, 'a8')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_2')

		return i

	def Read_BCC1E889(self, node):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def Read_BD5BB62B(self, node):
		i = self.Read_HeaderParent(node)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_C0014C89(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'a1')
		i = node.ReadUInt8A(i, 4, 'a2')
		i = self.ReadTransformation(node, i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 7, 'a5')

		return i

	def Read_C29D5C11(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 3, 'a0')

		return i

	def Read_C2F1F8ED(self, node):
		'''
		dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def Read_C46B45C9(self, node):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def Read_C9DA5109(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, AbstractNode._TYP_GUESS_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')

		return i

	def Read_CA7163A3(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadChildRef(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
		i = self.skipBlockSize(i)
		i = node.ReadColorRGBA(i, 'c0')
		i = node.ReadColorRGBA(i, 'c1')
		i = node.ReadColorRGBA(i, 'c2')
		i = node.ReadColorRGBA(i, 'c3')
		i = node.ReadFloat32(i, 'f32_0')
		i = self.skipBlockSize(i)

		return i

	def Read_D1071D57(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		a3, i = getUInt16A(node.data, i, 2)
		i = self.ReadTransformation(node, i)

		return i

	def Read_D3A55701(self, node):
		'''
		2D-Spline
		'''
		node.typeName = '2dSpline'
		i = self.Read_32RRR2(node)
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadUInt8A(i, 8, 'a1')
		i = self.Read_Float32Arr(i, node, 'lst0')
		i = self.Read_Float32Arr(i, node, 'lst1')
		i = self.Read_Float64Arr(i, node, 2, 'lst2')
		i = node.ReadUInt8A(i, 8, 'a2')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadFloat64A(i, 2, 'a4')
		i = self.Read_Float64Arr(i, node, 2, 'lst3')

		return i

	def Read_D3A55702(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadUInt8A(i, 8, 'a1')
		i = self.Read_Float32Arr(i, node, 'lst0')
		i = self.Read_Float32Arr(i, node, 'lst1')
		i = self.Read_Float64Arr(i, node, 3, 'lst2')
		i = node.ReadUInt8A(i, 8, 'a2')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadFloat64A(i, 2, 'a4')

		return i

	def Read_D4824069(self, node): return 0

	def Read_D79AD3F3(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_3D_FLOAT32_, 'lst0')
		i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst1')
		i = node.ReadList2(i, AbstractNode._TYP_3D_FLOAT32_, 'lst2')
		i = node.ReadList2(i, AbstractNode._TYP_2D_FLOAT32_, 'lst3')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst4')
#		i = node.ReadFloat32A(i, 2, 'a1')
#		i = self.skipBlockSize(i)
#		i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst5')
# 		i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst6')
# 		i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst7')
		i = len(node.data)
		return i

	def Read_DA58AA0E(self, node):
		'''
		3D-Sketch
		'''
		node.typeName = '3dSketch'
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_3')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst2')
		i = node.ReadUInt8(i, 'u8_4')

		return i

	def Read_DBE41D91(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 3, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 14, 'a2')

		return i

	def Read_DEF9AD02(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_3D_FLOAT32_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')

		if (getFileVersion() > 2013):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
		else:
			node.set('lst1', [])

		return i

	def Read_DEF9AD03(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')

		if (getFileVersion() > 2013):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
		else:
			node.set('lst1', [])

		return i

	def Read_E1EB685C(self, node):
		i = self.Read_32RRR2(node)
		i = node.ReadUInt32A(i, 9, 'a0')
		i = node.ReadList2(i, AbstractNode._TYP_GUESS_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a1')

		return i

	def Read_EF1E3BE5(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_FONT_, 'lst0')
		return i

	def Read_F6ADCC68(self, node):
		i = self.Read_HeaderParent(node)
		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_F6ADCC69(self, node):
		i = self.Read_HeaderParent(node)
		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_FB96D24A(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64A(i, 3, 'f64_0')
		i = node.ReadUInt32(i, 'u32_0')

		return i

	def Read_FF084971(self, node):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def Read_FFB5643C(self, node):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(node)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'key')
		i = node.ReadUInt8(i, 'u8_1')

		return i

	def HandleBlock(self, file, node):
		i = 0
		ntid = node.typeID.time_low
		if (ntid == 0x6e176bb6):
			node.updateTypeId('B32BF6A7-11D2-09F4-6000-F99AC5361AB0')
			ntid = 0xB32BF6A7
		elif (ntid == 0xb255d907):
			node.updateTypeId('C29D5C11-11D3-7C12-0000-279800000000')
			ntid = 0xC29D5C11
		try:
			readType = getattr(self, 'Read_%08X' %(ntid))
			i = readType(node)
		except AttributeError:
			logError(u"ERROR> %s.Read_%08X not defined!", self.__class__.__name__, ntid)
		except:
			logError(traceback.format_exc())

		if (i < len(node.data)):
			i = node.ReadUInt8A(i, len(node.data) - i, '\taX')

		return
