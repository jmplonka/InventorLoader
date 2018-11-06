# -*- coding: utf-8 -*-

'''
importerDC.py:
Importer for the Document's components
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''
from importerSegment        import convert2Version7, resolveEntityReferences, dumpSat
from importerEeData         import EeDataReader
from importerUtils          import *
from importerClasses        import Tolerances, Functions
from math                   import pi
from Acis                   import clearEntities, setVersion
from importerSAT            import Header, readNextSabChunk, readEntityBinary
from xlrd                   import open_workbook
from uuid                   import UUID
import importerSegNode, re

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

def _addEmpty(node, indexes, list):
	for i in indexes:
		name = 'lst%d' %(i)
		node.content += ' %s={}' %(name)
		node.set(name, list)

def addEmptyLists(node, indexes):
	_addEmpty(node, indexes, [])

def addEmptyMaps(node, indexes):
	_addEmpty(node, indexes, {})

class DCReader(EeDataReader):
	DOC_ASSEMBLY     = 1
	DOC_DRAWING      = 2
	DOC_PART         = 3
	DOC_PRESENTATION = 4

	def __init__(self, segment):
		super(DCReader, self).__init__(segment)

########################################
# usability functions

	def ReadContentHeader(self, node, typeName = None, name='label'):
		'''
		Read the header for content objects like Sketch2D, Pads, ...
		'''
		i = node.Read_Header0(typeName)
		if (name != 'label'):
			i = node.ReadCrossRef(i, name)
		else:
			i = node.ReadChildRef(i, name)
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'index')

		flags = node.get('flags')
		node.visible             = (flags & 0x00000400) > 0
		node.dimensioningVisible = (flags & 0x00800000) > 0
		self.segment.indexNodes[node.get('index')] = node
		return i

	def ReadHeadersS32ss(self, node, typeName = None, name='label'):
		i = self.ReadContentHeader(node, typeName, name)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i, 8)
		return i

	def ReadHeaderFeature(self, node, name):
		i = self.ReadHeadersS32ss(node, 'Feature')
		node.set('Feature', name)
		return i

	def ReadCntHdr1SRef(self, node, typeName = None, name = 'ref_1'):
		i = self.ReadContentHeader(node, typeName)
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadCrossRef(i, name)
		return i

	def ReadCntHdr2S(self, node, typeName = None):
		i = self.ReadContentHeader(node, typeName)
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		return i

	def ReadCntHdr2SRef(self, node, typeName = None, name = 'ref_1'):
		i = self.ReadCntHdr2S(node, typeName)
		i = node.ReadCrossRef(i, name)
		return i

	def ReadCntHdr2SChild(self, node, typeName = None, name = 'ref_1'):
		i = self.ReadCntHdr2S(node, typeName)
		i = node.ReadChildRef(i, name)
		return i

	def ReadCntHdr3S(self, node, typeName = None):
		i = self.ReadContentHeader(node, typeName)
		i = self.skipBlockSize(i, 12)
		if (getFileVersion() > 2018): i += 4
		return i

	def ReadHeadersss2S16s(self, node, typeName = None):
		i = self.ReadCntHdr3S(node, typeName)
		i = node.ReadUInt32(i, 'flags2')
		i = self.skipBlockSize(i)
		return i

	def ReadHeaderPattern(self, node, patternName):
		i = self.ReadHeaderFeature(node, patternName)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'participants')
		properties = node.get('properties')
		for j in range(0, 6):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			properties.append(ref)
		i = node.ReadUInt8(i, 'u8_0')
		return properties, i

	def ReadSketch2DEntityHeader(self, node, typeName = None):
		i = self.ReadHeadersss2S16s(node, typeName)
		i = node.ReadCrossRef(i, 'refSketch')
		return i

	def ReadSketch3DEntityHeader(self, node, typeName = None):
		i = self.ReadHeadersss2S16s(node, typeName)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		return i

	def ReadHeaderEnum(self, node, enumName, values = []):
		i = self.ReadCntHdr3S(node, 'Enum')
		i = node.ReadSInt16(i, 'type')
		i = node.ReadUInt16(i, 'value')
		i = self.skipBlockSize(i)
		node.set('Enum', enumName)
		node.set('Values', values)
		return i

	def ReadHeaderConstraint2D(self, node, typeName):
		'''
		Read the header for 2D constraints
		'''
		i = self.ReadContentHeader(node, typeName)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
		else:
			addEmptyLists(node, [0, 1])
			i = self.skipBlockSize(i, 8)
		i = node.ReadCrossRef(i, 'refParameter')
		return i

	def ReadConstraintHeader3D(self, node, typeName = None):
		'''
		Read the header for 3D constraints
		'''
		i = self.ReadContentHeader(node, typeName)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst2')
		else:
			i = self.skipBlockSize(i)
			addEmptyLists(node, [1, 2])
		return i

	def ReadDerivedComponent(self, node, typeName):
		i = self.ReadHeadersS32ss(node, typeName)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadLen32Text16(i)
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt8A(i, 5, 'a0')
		return i

	def ReadChildHeader1(self, node, typeName = None, ref1Name = 'ref_1', ref2Name = 'ref_2'):
		'''
		Read the default header a0=UInt32[2], ref_1=NodeRef, ref_2=NodeRef
		'''
		i = node.Read_Header0(typeName)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, ref1Name)
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, ref2Name)
		return i

	def ReadRefList(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			lst.append(ref)
		node.content += ' %s=[%s]' %(name, ','.join(['(%s)' %(r) for r in lst]))
		node.set(name, lst)
		return i

	def Read2RefList(self, node, offset, name, refType):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref1, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CHILD)
			ref2, i = self.ReadNodeRef(node, i, j, refType)
			lst.append([ref1, ref2])
		node.content += ' %s=[%s]' %(name, ','.join(['(%s,%s)' %(r[0], r[1]) for r in lst]))
		node.set(name, lst)
		return i

	def ReadU32U32List(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref, i = getUInt32(node.data, i)
			u32, i = getUInt32(node.data, i)
			lst.append([ref, u32])
		node.content += ' %s=[%s]' %(name, ','.join(['(%04X,%04X)' %(r[0], r[1]) for r in lst]))
		node.set(name, lst)
		return i

	def ReadRefU32List(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			u32, i = getUInt32(node.data, i)
			lst.append([ref, u32])
		node.content += ' %s=[%s]' %(name, ','.join(['(%s,%04X)' %(r[0], r[1]) for r in lst]))
		node.set(name, lst)
		return i

	def ReadU32U32U8List(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref, i = getUInt32(node.data, i)
			val, i = getUInt32(node.data, i)
			u8, i  = getUInt8(node.data, i)
			lst.append([ref, val, u8])
		node.content += ' %s=[%s]' %(name, ','.join(['(%04X,%04X,%02X)' %(r[0], r[1], r[2]) for r in lst]))
		node.set(name, lst)
		return i

	def ReadRefU32U8List(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			val, i = getUInt32(node.data, i)
			u8, i  = getUInt8(node.data, i)
			lst.append([ref, val, u8])
		node.content += ' %s=[%s]' %(name, ','.join(['(%s,%04X,%02X)' %(r[0], r[1], r[2]) for r in lst]))
		node.set(name, lst)
		return i

	def ReadU32U32D64List(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref, i = getUInt32(node.data, i)
			val, i = getUInt32(node.data, i)
			f64, i = getFloat64(node.data, i)
			lst.append([ref, val, f64])
		node.content += ' %s=[%s]' %(name, ','.join(['(%04X,%04X,%g)' %(r[0], r[1], r[2]) for r in lst]))
		node.set(name, lst)
		return i

	def ReadU32XRefList(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			val, i = getUInt32(node.data, i)
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			lst.append([val, ref])
		node.content += ' %s=[%s]' %(name, ','.join(['(%04X,%s)' %(r[0], r[1]) for r in lst]))
		node.set(name, lst)
		return i

	def ReadList2U32(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32A(i, 7, 'a0')
		i = self.skipBlockSize(i)
		return i

	def ReadUInt32A(self, node, i, cnt, name, size):
		lst = []
		c = []
		for j in range(cnt):
			if (size > 1):
				a, i = getUInt32A(node.data, i, size)
				c.append('(%s)' %(IntArr2Str(a, 4)))
			else:
				a, i = getUInt32(node.data, i)
				c.append('(%04X)' %(a))
			lst.append(a)
		node.content += ' %s=[%s]' % (name, ','.join(c))
		node.set(name, lst)
		return i

	def readTypedList(self, node, index, key, count, size, tolerance):
		meta, i = getUInt32A(node.data, index, count)
		lst = []
		s = ''
		sep = ''
		for j in range(meta[0]):
			if (size == 1):
				f, i = getFloat64(node.data, i)
				s += "%s%g" %(sep, f)
			else:
				f, i = getFloat64A(node.data, i, size)
				s += "%s[%s]" %(sep, FloatArr2Str(f))
			sep = ','
			lst.append(f)
		if (tolerance):
			tol, i = getFloat64(node.data, i)
			node.content += " %s=(%s,[%s],%g)" %(key, IntArr2Str(meta[1:], 2), s, tol)
		else:
			tol = None
			node.content += " %s=(%s,[%s])" %(key, IntArr2Str(meta[1:], 2), s)
		node.set(key, {'meta': meta, 'values': lst, 'tolerance': tol})
		return i

########################################
# Functions for reading sections

	def Read_009A1CC4(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		cnt, i = getUInt32(node.data, i)
		lst = []
		sep = ''
		node.content += ' lst2=['
		for j in range(cnt):
			#u32,u32,u16,u8,f64,u16,u16,u16,u8,f64,u16,u16
			u32_0, i = getUInt32(node.data, i)
			u32_1, i = getUInt32(node.data, i)
			u16_0, i = getUInt16(node.data, i)
			u8_0,  i = getUInt8(node.data, i)
			f64_0, i = getFloat64(node.data, i)
			u16_1, i = getUInt16(node.data, i)
			u16_2, i = getUInt16(node.data, i)
			u16_3, i = getUInt16(node.data, i)
			u8_1,  i = getUInt8(node.data, i)
			f64_1, i = getFloat64(node.data, i)
			u16_2, i = getUInt16(node.data, i)
			u16_3, i = getUInt16(node.data, i)
			lst.append([u32_0, u32_1, u16_0, u8_0, f64_0, u16_1, u16_2, u16_3, u8_1, f64_1, u16_2, u16_3])
			node.content += '%s(%04X,%04X,%03X,%02X,%g,%03X,%03X,%03X,%02X,%g,%03X,%03X)' %(sep, u32_0, u32_1, u16_0, u8_0, f64_0, u16_1, u16_2, u16_3, u8_1, f64_1, u16_2, u16_3)
			sep = ','
		node.content += ']'
		node.set('lst2', lst)
		return i

	def Read_00ACC000(self, node): # TwoPointDistanceDimConstraint {C173A079-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Distance_Horizontal2D')
		i = node.ReadCrossRef(i, 'refEntity1')
		i = node.ReadCrossRef(i, 'refEntity2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_00E41C0E(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadUInt32A(i, 5, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		return i

	def Read_01E0570C(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		return i

	def Read_01E7910C(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2015):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		else:
			ref, i = self.ReadNodeRef(node, i, 0, importerSegNode.SecNodeRef.TYPE_CROSS)
			node.content += ' lst0={1}'
			node.set('lst0', [ref])
		i = node.ReadList2(i, importerSegNode._TYP_LIST_FLOAT64_A_, 'lst1', 3)
		i = self.ReadTypedFloatsList(node, i, 'a1')
		return i

	def Read_0229768D(self, node): # ParameterComment
		i = node.Read_Header0('ParameterComment')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_025C7CD8(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid')
		i = node.ReadSInt32A(i, 3, 'a1')
		return i

	def Read_029DAD70(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refLine')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_0326C921(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		lst0={}
		for j in range(cnt):
			key, i = getLen32Text16(node.data, i)
			val, i = getLen32Text16(node.data, i)
			lst0[key] = val
		node.content += ' lst0={%s}' %(','.join(["('%s': '%s')" %(k, v) for k, v in lst0.items()]))
		node.set('lst0', lst0)
		i = node.ReadUInt16(i, 'u16_1')
		return i

	def Read_033E027B(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_03AA812C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'refSurface')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_2')
		i = self.skipBlockSize(i)
		if (getFileVersion() < 2011):
			i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_2a')
		i = node.ReadUInt32(i, 'u32_2b')
		i = self.ReadU32U32List(node, i, 'edges')
		if (getFileVersion() > 2010):
			i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_03CC1996(self, node):
		i = self.ReadHeaderFeature(node, 'LoftedFlange')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_03D6552D(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refEntity')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_040D7FB2(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_0455B440(self, node):
		i = self.ReadCntHdr2SRef(node)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_A')
		i = node.ReadUInt8A(i, 3, 'a0')
		i = node.ReadCrossRef(i, 'ref_B')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_04B1FCF0(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_04D026D2(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_053C4810(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32A(i, 3, 'a1')
		cnt, i = getUInt16(node.data, i)
		lst0 = []
		for j in range(cnt):
			f, i = getFloat64(node.data, i)
			a, i = getUInt16A(node.data, i, 2)
			lst0.append([f, a[0], a[1]])
		node.content += ' lst0=[%s]' %(','.join(['(%g,%03X,%03X)' %(r[0], r[1], r[2]) for r in lst0]))
		node.set('lst0', lst0)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_2')
		return i

	def Read_05520360(self, node): # FxCount
		i = node.Read_Header0('FxCount')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'anchors', 3)
		i = self.ReadTransformation(node, i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refParameter')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'center')
		return i

	def Read_05C619B6(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.ReadU32U32List(node, i, 'a1')
		i = node.ReadUInt32(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadU32U32U8List(node, i, 'a2')
		i = self.ReadU32U32D64List(node, i, 'a3')
		i = self.ReadU32U32D64List(node, i, 'a4')
		if (getFileVersion() > 2010):
			i += 16
		return i

	def Read_06262CC1(self, node):
		i = self.ReadHeaderEnum(node, 'BendLocation', ['Centerline', 'Start', 'End'])
		return i

	def Read_0645C2A5(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 10, 'a1')
		a1 = node.get('a1')
#		if (a1[5] != 0):
#			i = node.ReadUInt32(i, 'u32_1')
#		if ((a1[6] & 0xFF) != 0):
#			i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_065FFFB3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_06977131(self, node): # CircularPatternFeature {7BB0E824-4852-4F1B-B43C-7F729A3D7EB8}
		properties, i = self.ReadHeaderPattern(node, 'PatternCircular')
		for j in range(6, 12):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			properties.append(ref)
		if (getFileVersion() > 2016):
			i += 24
		else:
			i = self.skipBlockSize(i)
		for j in range(12, 18):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			properties.append(ref)
		if (getFileVersion() > 2016):
			for j in range(18, 20):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
				properties.append(ref)
		return i

	def Read_06DCEFA9(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadUInt16(i, 'u16_2')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt16(i, 'u16_3')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_077D9583(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		return i

	def Read_07910C0A(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_07910C0B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadFloat64A(i, 5, 'a0')
		return i

	def Read_07AB2269(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'refSurfaceBody')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUUID(i, 'uid')
		return i

	def Read_07B89A4F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'refParameter')
		return i

	def Read_07BA7419(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8A(i, 4, 'a0')
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_0800FE29(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # ???
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'transformations')
		return i

	def Read_0811C56E(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 4, 'a1')
		if (getFileVersion() > 2011):
			i += 1
		return i

	def Read_0830C1B0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_09429287(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_09429289(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_0942928A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_0A077221(self, node):
		i = self.ReadHeaderEnum(node, '0A077221_Enum', [])
		return i

	def Read_0A3BA89C(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_0A52ED98(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt16A(i, 3, 'a0')
		i = self.ReadTransformation(node, i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_0A576361(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # skip FF FF FF FF
		return i

	def Read_0AA8AF46(self, node): # ParameterConstant
		i = node.Read_Header0('ParameterConstant')
		i = node.ReadChildRef(i, 'refUnit')
		i = node.ReadFloat64(i, 'value')
		i = node.ReadSInt16(i, 's16_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		if (node.name == 'PI') : node.name = 'pi'
		elif (node.name == 'E'): node.name = 'e'
		return i

	def Read_0B85010C(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_0B86AD43(self, node): # SketchFixedSpline3D {7A5B2F53-5756-4261-B6F1-4B5C3CDE1226}
		i = self.ReadSketch3DEntityHeader(node, 'Spline3D_Fixed')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_0BA398EA(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_0BDC96E0(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_0C12CBF2(self, node):
		i = self.ReadHeadersS32ss(node, 'LoftProfileCondition')
		i = node.ReadCrossRef(i, 'refSection')
		i = node.ReadCrossRef(i, 'refImpact')
		i = node.ReadCrossRef(i, 'refAngle')
		i = node.ReadCrossRef(i, 'refPlane')
		return i

	def Read_0C48B860(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		return i

	def Read_0C48B861(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refPlane')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		if (node.get('u8_0') == 0):
			i = node.ReadLen32Text16(i, 'txt0')
			i = node.ReadLen32Text16(i, 'txt1')
			i = node.ReadUInt16(i, 'u16_0')
			i = self.skipBlockSize(i)
			i = node.ReadUInt32(i, 'u32_0')
			i = self.skipBlockSize(i)
		else:
			i = node.ReadUInt32(i, 'u32_0')
			if (getFileVersion() > 2017):
				i += 4
			else:
				i = self.skipBlockSize(i, 8)
		return i

	def Read_0C7F6742(self, node):
		i = self.ReadHeaderEnum(node, '0C7F6742_Enum', [])
		return i

	def Read_0CAC6298(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		return i

	def Read_0D0F9548(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_0D28D8C0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refPlane1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPlane2')
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_0DDD7C10(self, node): # SymmetryConstraint {8006A08E-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_SymmetryLine2D')
		i = node.ReadCrossRef(i, 'refEntity1')
		i = node.ReadCrossRef(i, 'refEntity2')
		i = node.ReadCrossRef(i, 'refSymmetry')
		return i

	def Read_0E64A759(self, node): # ModelGeneralNote {88C68B3A-B9B0-45DD-873C-FA0187B80E62}
		i = self.ReadContentHeader(node, 'ModelGeneralNote')
		return i

	def Read_0E6870AE(self, node): # SolidBody
		i = self.ReadCntHdr3S(node, 'SolidBody')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'bodies')
		return i

	def Read_0E6B7F33(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadLen32Text16(i)
		return i

	def Read_0E8C5360(self, node): # SplineHandle3D
		i = self.ReadContentHeader(node, 'SplineHandle3D')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst1')
		else:
			i = self.skipBlockSize(i)
		return i

	def Read_0F177BB0(self, node): # GroundConstraint {8006A082-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Fix2D')
		i = node.ReadCrossRef(i, 'refPoint')
		return i

	def Read_10587822(self, node): # Faces
		i = node.Read_Header0('Faces')
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'label')
		i = self.skipBlockSize(i)
		i = self.ReadRefU32List(node, i, 'a1')
		i = node.ReadUInt16A(i, 3, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_109727B0(self, node): # iFeatureTemplateDescriptor {3C69FF6F-6ADD-4CF5-8E9B-32CBD2B6BBF7}
		i = node.Read_Header0('iFeatureTemplateDescriptor')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i += 4
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_10B6ADEF(self, node): # LineLengthDimConstraint3D {04A196FD-3FBB-43EF-9A79-2735B3B99214}
		i = self.ReadConstraintHeader3D(node, 'Dimension_Length3D')
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_10DC334C(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_11058558(self, node): # OffsetDimConstraint {C173A077-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Distance2D')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refEntity1')
		i = node.ReadCrossRef(i, 'refEntity2')
		i = node.ReadUInt32A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_2D(i, 'a1')
		i = node.ReadFloat64_2D(i, 'a2')
		return i

	def Read_115F4501(self, node): # Enum
		i = self.ReadHeaderEnum(node, 'RipType', ['SinglePoint', 'PointToPoint', 'FaceExtents'])
		return i

	def Read_117806EE(self, node):
		i = node.Read_Header0()
		return i

	def Read_1249FE41(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_1345015C(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4
		i = node.ReadCrossRef(i, 'param')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'faces')
		return i

	def Read_13F4E5A3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_14340ADB(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_3')
		if (node.get('u32_1') == 1):
			i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst2', 2)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_4')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 7)
		return i

	def Read_1488B839(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadFloat64A(i, cnt, 'a1')
		return i

	def Read_151280F0(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_2')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i, 8)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_3')
		cnt, i = getUInt32(node.data, i)
		if (cnt == 1):
			i = node.ReadUInt32(i, 'u32_4')
		elif (cnt == 0):
			node.set('u32_4', 0)
			node.content += ' u32_4=000000'
		i = node.ReadFloat64A(i, (len(node.data) - i) / 8, 'a1')
		return i

	def Read_15729F01(self, node):
		i = self.ReadHeaderEnum(node, '15729F01_Enum', [])
		return i

	def Read_15A5FF92(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_15E7211A(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_160915E2(self, node): # SketchArc {8006A046-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadSketch2DEntityHeader(node, 'Arc2D')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		else:
			i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refCenter')
		i = node.ReadFloat64(i, 'r')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_167018B8(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a1')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a2')
		i = node.ReadUInt32A(i, 2, 'a3')
		return i

	def Read_16DE1A75(self, node): # DimensionAnnotation
		i = self.ReadContentHeader(node, 'AnnonatationDimension')
		if (getFileVersion() > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadCrossRef(i, 'ref0')
		i = node.ReadCrossRef(i, 'ref1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref2')
		i = node.ReadCrossRef(i, 'ref4')
		i = node.ReadCrossRef(i, 'ref5')
		i = node.ReadCrossRef(i, 'ref6')
		i = node.ReadCrossRef(i, 'ref7')
		return i

	def Read_173E51F4(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_17B3E814(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'refRDxVar')
		return i

	def Read_182D1C40(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_182D1C8A(self, node): # EmbeddedExcel
		i = node.Read_Header0('EmbeddedExcel')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt16A(i, 3, 'a0')
		if (node.get('ref_2') is None):
			i = node.ReadLen32Text16(i)
			i = node.ReadUInt16(i, 'u16')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_1')
		hdr, i = getUInt32A(node.data, i, 2) # 30000002, Len, XXXXXXXX, XXXXXXXX, len x [bytes] => Excel-Workbook
		size = hdr[1]
		if (size > 0):
			i += 8
			buffer = node.data[i:i+size]
			folder = getInventorFile()[0:-4]
			filename = '%s\\%s_%04X.xls' %(folder, node.typeName, node.index)
			with open(filename, 'wb') as xls:
				xls.write(buffer)
				node.set('filename', filename)
				node.set('workbook', open_workbook(file_contents=buffer))
			# logInfo(u"    INFO - found workbook: stored as %s!", filename)
		i += size
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		if (getFileVersion() > 2012):
			i += 16
		return i

	def Read_18951917(self, node): # RevolutionTransformation
		i = self.ReadHeadersS32ss(node, 'RevolutionTransformation')
		i = node.ReadCrossRef(i, 'ref2D')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = node.ReadCrossRef(i, 'ref3D')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_18A9717E(self, node):
		i = self.ReadSketch2DEntityHeader(node, 'BlockPoint2D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'centerOf')
		i = node.ReadCrossRef(i, 'refPoint')
		node.set('points', node.get('centerOf'))
		return i

	def Read_18D844B8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_197F7DBE(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		return i

	def Read_19573122(self, node): # new in 2019
		i = node.Read_Header0()
		# 00,00,00,00
		# 00,02,00,00
		# 03,00,00,80
		# 02,02,00,00
		# FF,FF,FF,FF
		# 1D,00,00,80
		# D4,01,00,80
		return i

	def Read_19F763CB(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'idx')
		i = node.ReadUInt32(i, 'cnt')
		cnt = node.get('cnt')
		lst = []
		sep = ''
		node.content += ' lst0=['
		for j in range(cnt):
			typ, i = getUInt32(node.data, i)
			if (typ == 0x17):
				a, i = getFloat64A(node.data, i, 6)
				lst.append(a)
				node.content += '%s(%s)' %(sep, FloatArr2Str(a))
			elif (typ == 0x2A):
				#00 00 00 00 00 00 00 00 02 00 00 00 95 D6 26 E8 0B 2E 11 3E
				a1, i = getUInt32A(node.data, i, 3)
				f1, i = getFloat64(node.data, i)
				#	[06 00 00 00,06 00 00 00,08 00 00 00,00 00 00 00,00 00 00 00],[00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 F0 3F 00 00 00 00 00 00 F0 3F 00 00 00 00 00 00 F0 3F 00 00 00 00 00 00 00 00]
				a2, i = getUInt32A(node.data, i, 5)
				a3, i = getFloat64A(node.data, i, a2[1])
				#	[08 00 00 00,03 00 00 00,03 00 00 00,08 00 00 00],[00 63 B2 54 5E 0A EC BF,E8 FB A9 F1 12 2C B4 BC,AD 9A C9 E6 29 98 F4 BF,98 D3 0B 30 DD 7E ED BF,E8 FB A9 F1 12 2C B4 BC,CA A3 3E 32 72 6C F5 BF,98 D3 0B 30 DD 7E ED BF,E8 FB A9 F1 12 2C B4 BC,FF EA 6F 3A DB A0 F6 BF,11 EA 2D 81 99 97 71 3D]
				a4, i = getUInt32A(node.data, i, 4)
				a5, i = getFloat64A(node.data, i, a4[1]*3)
				#	[01 00 00 00,01 00 00 00,00 00 00 00,00 00 00 00],[00 00 00 00 00 00 F0 3F]
				f2, i = getFloat64(node.data, i)
				a6, i = getUInt32A(node.data, i, 4)
				a7, i = getFloat64A(node.data, i, a6[1])
				lst.append([a1, f1, a2, a3, a4, a5, a6, a7])
				node.content += '%s(%s,%g,%s,%s,%s,%s,%g,%s,%s)' %(sep, IntArr2Str(a1, 2), f1, IntArr2Str(a2, 2), FloatArr2Str(a3), IntArr2Str(a4, 2), FloatArr2Str(a5), f2, IntArr2Str(a6, 2), FloatArr2Str(a7))
			else:
				logError(u"    ERROR in Read_%s: Unknown block type %X!", node.typeName, typ)
				return i
			sep = ','
		node.content += ']'

		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadFloat64_3D(i, 'a1')
		return i

	def Read_1A1C8265(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_1A21362E(self, node):
		i = self.ReadHeaderFeature(node, 'Mesh')
		if (getFileVersion() > 2016):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst3')
		else:
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadLen32Text16(i, 'txt0')
			i = node.ReadLen32Text16(i, 'txt1')
			i = node.ReadUInt8(i, 'u8_0')
			i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
			i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst2')
			i = node.ReadUInt32A(i, 3, 'a0')
			i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_1A26FF54(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_LIST2_XREF_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'refFX')
		return i

	def Read_1B48AD11(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_1B48E9DA(self, node): # FilletFeature {7DE603B3-DAA7-4364-BC8B-77295B53D1DB}
		i = self.ReadCntHdr3S(node, 'FxFilletConstant')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'radiusEdgeSets')
		return i

	def Read_1C0E2EA7(self, node): # new in 2019
		i = node.Read_Header0()
		# AE,0B,00,80
		# 00,00,00,00
		# 09,02,00,00
		# 63,04,00,80
		# 00
		return i

	def Read_1CC0C585(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_1D92FF4F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refParameter')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2011):
			i += 8+4 # F64 + U32
		return i

	def Read_1DCBFBA7(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadChildRef(i, 'ref_2')
		if (len(node.name) == 0):
			i = node.ReadUInt8(i, 'u8_1')
		else:
			node.content += ' u8_1=0'
			node.set('u8_1', 0)
#		if (getFileVersion() >  2017):
#			i += 4
#		i = self.Read2RefList(node, i, 'a1', importerSegNode.SecNodeRef.TYPE_CHILD)
		return i

	def Read_1DEE2CF3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		u8 = node.get('u8_0')
		if (u8 == 0):
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadLen32Text16(i, 'txt0')
			i = node.ReadLen32Text16(i, 'txt1')
			i = node.ReadUInt16(i, 'u16_0')
		elif (u8 ==1):
			i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_1E3A132C(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'operation') # 8 = Fuse, 0 = Cut
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'edges') #
		i = node.ReadUInt32(i, 'faceIndex')
		return i

	def Read_1EF28758(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_1F6D59F6(self, node): # DirectEditFeature {602389D5-6C6A-4368-A6F2-47D54FA1FBA4}
		i = self.ReadHeaderFeature(node, 'DirectEdit')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_1FBB3C01(self, node): # The content of the RTF formatted text {rtf1 [:RtfContent:]}
		i = self.ReadContentHeader(node, 'RtfContent')
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadVec3D(i, 'loc', 10.0)
		i = node.ReadUInt16A(i, 18, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2015):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 4, 'a2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadVec3D(i, 'vec1', 1.0)
		i = node.ReadVec3D(i, 'vec2', 1.0)
		i = node.ReadUInt16A(i, 3, 'a3')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		i = node.ReadLen32Text16(i, 'txt0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		if (getFileVersion() > 2016):
			i += 17
		return i

	def Read_20673244(self, node): # RectangularPatternFeature {58B0C13D-27CC-4F06-93FD-0524B69E6578}
		properties, i = self.ReadHeaderPattern(node, 'PatternRectangular')
		for j in range(6, 12):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			properties.append(ref)
		i = self.skipBlockSize(i)
		for j in range(12, 26):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			properties.append(ref)
		if (getFileVersion() > 2016):
			for j in range(26, 32):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
				properties.append(ref)
		return i

	def Read_207C8609(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt16A(i, 3, 'a0')
		i = self.ReadTransformation(node, i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		return i

	def Read_20976662(self, node):
		i = self.ReadCntHdr2SRef(node, 'SculptSurface', 'refBody')
		i = node.ReadCrossRef(i, 'refOperation')
		return i

	def Read_21004CF2(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i += 4
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'f64_0')
		return i

	def Read_2148C03C(self, node): # ReferenceFeature {298849A9-ECAB-4234-9675-6FAA66A95E4D}
		i = self.ReadCntHdr2SRef(node, 'FxReference')
		return i

	def Read_2169ED74(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'lst1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16A(i, 7, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_216B3A55(self, node):
		i = node.Read_Header0()
		return i

	def Read_2B1F0409(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_21E870BF(self, node): # MidpointConstraint {8006A088-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadHeaderConstraint2D(node, 'Geometric_SymmetryPoint2D')
		i = node.ReadCrossRef(i, 'refObject')
		i = node.ReadCrossRef(i, 'refPoint')
		if (getFileVersion() > 2015):
			i += 4
		return i

	def Read_220226D5(self, node): # Blocks
		i = self.ReadContentHeader(node, 'Blocks')
		return i

	def Read_22178C64(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadUInt32(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadU32U32U8List(node, i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst2', 2)
		i = node.ReadUInt32(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 5)
		return i

	def Read_222D217D(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_223360AD(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # skip FF FF FF FF
		return i

	def Read_22947391(self, node): # BoundaryPatchFeature {16B36EBE-2DFA-4474-B11B-DF3D57C109B0}
		i = self.ReadCntHdr3S(node, 'FxBoundaryPatch')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_23BA0568(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_24BCB2F1(self, node):
		i = self.ReadCntHdr3S(node, 'FaceCollection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'faces')
		return i

	def Read_2510347F(self, node): # TextBox {A907AE99-A78F-11D5-8DF8-0010B541CAA8}
		i = self.ReadHeadersS32ss(node, 'Text2D')
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'refText')
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_253BE3EB(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_255D7ED7(self, node): # DerivedPartComponent {6D7C8AC8-722D-46C8-B6D9-F6001F1EDD2D}
		i = self.ReadDerivedComponent(node, 'DerivedPart')
		if (getFileVersion() > 2011):
			i = node.ReadUInt32(i, 'u32_1')
			node.content += ' u8_0=00'
			node.set('u8_0', 0)
		if (getFileVersion() < 2013):
			i = self.skipBlockSize(i)
			node.content += ' u32_1=000000'
			node.set('u32_0', 0)
			i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_2574C505(self, node): # ConcentricConstraint3D {EF118F14-C2D2-4DF4-910A-3438FBEC2817}
		i = self.ReadContentHeader(node, 'Geometric_Radius3D')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst2')
		else:
			node.content += ' lst1={} lst0={}'
		return i

	def Read_258EC6E1(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_25E6AD96(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadList4(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_26287E96(self, node): # iPart
		i = self.ReadContentHeader(node, 'iPart')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'excelWorkbook')
		i = node.ReadSInt32(i, 'rowIndex')
		i = node.ReadUUID(i, 'uid')
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'refParent')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'iParts')
		i = node.ReadUInt8(i, 'selected')
		return i

	def Read_265034E9(self, node):
		i = self.ReadCntHdr2SRef(node)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_262EA00C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		if (getFileVersion() > 2017):
			i += 4
		return i

	def Read_26F369B7(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'cld_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64_2D(i, 'a2')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2010):
			#i = node.ReadFloat64A(i, 6, 'a3')
			i += 6*8 # ref. Sketch3D origin
		return i

	def Read_27E9A56F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'refBody')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refDirection')
		i = node.ReadUInt32(i, 'u32_1a')
		i = node.ReadUInt32(i, 'u32_1b')
		i = node.ReadUInt32(i, 'u32_2a')
		i = node.ReadUInt32(i, 'u32_2b')
		i = node.ReadUInt32(i, 'u32_3a')
		i = node.ReadUInt32(i, 'u32_3bmd')
		i = node.ReadUInt16(i, 'u16_1')
		return i

	def Read_27ECB60D(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.ReadTransformation(node, i)
		i = node.ReadUInt8A(i, 2, 'a0')
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_27ECB60E(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadList4(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		if (getFileVersion() < 2013):
			i = node.ReadUInt32(i, 'u32_0')
			i = self.skipBlockSize(i)
			i = node.ReadList6(i, importerSegNode._TYP_MAP_REF_REF_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_REF_REF_, 'lst2')
			i = node.ReadUInt16(i, 'cnt')
			cnt = node.get('cnt')
			lst = []
			for j in range(cnt):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
				txt, i = getLen32Text16(node.data, i)
				u8, i  = getUInt8(node.data, i)
				lst.append([ref, txt, u8])
			node.content += ' lst3=[%s]' %(','.join(["[%s,'%s',%02X]" %(r[0], r[1], r[2]) for r in lst]))
			node.set('lst3', lst)
			i = node.ReadUInt32(i, 'u32_2')
		else:
			i = node.ReadChildRef(i, 'ref_6')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_27ECB60F(self, node): # DerivedAssemblyComponent {A1D2EAAD-28A1-4692-BC13-883879C68894}
		i = self.ReadDerivedComponent(node, 'DerivedAssembly')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadUInt32A(i, 3, 'a1')
		if (getFileVersion() > 2017):
			i += 36
		return i

	def Read_2801D6C6(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_288D7986(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_2892C3E0(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_28B21FD5(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadUInt32(i, 'u32_4')
		return i

	def Read_28BE2D59(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # skip FF FF FF FF
		return i

	def Read_28BE2D5B(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadFloat64_3D(i, 'a1')
		return i

	def Read_28CB7150(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt8A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadFloat32A(i, 4, 'a2')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadFloat32A(i, 4, 'a4')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT32_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		i = node.ReadFloat64A(i, 4, 'a5')
		i = node.ReadCrossRef(i, 'reference')
		return i

	def Read_299B2DCE(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_29AC9292(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'label')
		i = node.ReadUUID(i, 'id')
		return i

	def Read_2A34F1AD(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadChildRef(i, 'label')
		i = self.skipBlockSize(i)
		return i

	def Read_2A636E60(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_2AB13E5B(self, node):
		i = self.ReadChildHeader1(node)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_2AB534B2(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		return i

	def Read_2AF9B62B(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_2B241309(self, node): # BrowserFolder {9D063FDB-B597-49B0-8DBC-7EB3D5F715B8}
		i = self.ReadContentHeader(node, 'BrowserFolder')
		i = self.skipBlockSize(i)
		return i

	def Read_2B3E0C72(self, node):
		# i = self.ReadEnumValue(node, '', ['']) # 60452313.properties[2]; 60452313.properties[5] and 60452313.properties[13h]
		i = self.ReadHeadersss2S16s(node) # 60452313.properties[2]; 60452313.properties[5] and 60452313.properties[13h]
		return i

	def Read_2B48A42B(self, node):
		i = node.Read_Header0()

		if (node.get('hdr').m == 0x12):
			i = 0
			node.delete('hdr')
			node.content = ''
			i = node.ReadLen32Text8(i, 'type')
			i = node.ReadUInt32A(i, 2, 'a0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT8_X_REF_, 'lst0')
			i = node.ReadUInt32(i, 'u32_2')
			i = node.ReadUInt32(i, 'u32_3')
			i = node.ReadUInt16(i, 'u16_3')
			i = node.ReadChildRef(i, 'label')
			i = node.ReadUInt32(i, 'flags')
			i = node.ReadParentRef(i)
			i = node.ReadUInt32(i, 'index')
			self.segment.indexNodes[node.get('index')] = node
			content = node.content
			j = i
			i = node.ReadUInt16(i, 'u16_1')
			i = node.ReadUInt16(i, 'u16_2')
			u16_2 = node.get('u16_2')
			u16_1 = node.get('u16_1')
			if (u16_2 == 0x000):
				if (u16_1 == 0x2000):
					i = node.ReadFloat64A(i, 6, 'a1')
				elif (u16_1 == 0x8000):
					i = node.ReadUInt32A(i, 3, 'a1')
					i = node.ReadFloat64A(i, 9, 'a2')
				else:
					node.content = content
					i = j
					i = node.ReadSInt32(i, 's32_0')
					i = node.ReadUInt32(i, 'u32_0')
					t, j = getUInt32(node.data, i)
					if (t == 0x30000002):
						node.typeName = 'Feature'
						i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
						i = node.ReadUInt32(i, 'u32_1')
						if (len(node.get('properties')) == 0):
							i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'participants')
							properties = []
							for j in range(6):
								ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
								properties.append(ref)
							boolVal, i = getBoolean(node.data, i)
							boolData = importerSegNode.SecNode()
							boolData.uid  = UUID('{90874d28-11d0-d1f8-0008-cabc0663dc09}')
							boolData.content = ' value=%s' %(boolVal)
							boolData.segment = self.segment
							boolData.typeName = 'ParameterBoolean'
							boolData.set('value', boolVal != 0)
							boolRef = importerSegNode.SecNodeRef(0xFFFFFFFF, importerSegNode.SecNodeRef.TYPE_CROSS)
							boolRef.data = boolData
							boolRef.number = 0x18
							ref, i = self.ReadNodeRef(node, i , len(properties), importerSegNode.SecNodeRef.TYPE_CROSS)
							properties.append(ref)
							properties.append(None)
							properties.append(None)
							ref, i = self.ReadNodeRef(node, i , len(properties), importerSegNode.SecNodeRef.TYPE_CROSS)
							properties.append(ref)
							i = node.ReadUInt32(i, 'u32_4')
							ref, i = self.ReadNodeRef(node, i , len(properties), importerSegNode.SecNodeRef.TYPE_CROSS)
							properties.append(ref)
							i = node.ReadUInt32(i, 'u32_5')
							for j in range(11, 26):
								ref, i = self.ReadNodeRef(node, i, len(properties), importerSegNode.SecNodeRef.TYPE_CROSS)
								properties.append(ref)
							node.references.append(boolRef)
							properties.append(boolRef)
							node.set('properties', properties)
					elif( t == 0x30000008):
						node.typeName = 'Sketch2D'
						node.sketchEdges = {}
						node.associativeIDs = {}
						i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_,'entities')
						i = node.ReadCrossRef(i, 'refTransformation')
						i = node.ReadCrossRef(i, 'refDirection')
			elif (u16_2 == 0x0003):
				node.typeName = 'Enum'
				node.set('Enum', 'PartFeatureOperation')
				node.set('Values', ['*UNDEFINED*', 'NewBody', 'Cut', 'Join', 'Intersection', 'Surface'])
				node.set('type', u16_1)
				node.set('value', 0)
				# node.set('value', ????)
			elif (u16_2 == 0x0080):
				i = node.ReadUInt32(i, 'u32_2')
				if (getFileVersion() > 2017):
					i += 4
				i = node.ReadUInt32(i, 'u32_4')
				if (node.get('u16_1') == 0x2000):
					node.typeName = 'Point3D'
					i = node.ReadFloat64(i, 'x')
					i = node.ReadFloat64(i, 'y')
					i = node.ReadFloat64(i, 'z')
					i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'endPointOf')
					i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'centerOf')
				else:
					node.typeName = 'Plane'
					i = node.ReadUInt32(i, 'u32_5')
					i = node.ReadFloat64(i, 'b_x')
					i = node.ReadFloat64(i, 'b_y')
					i = node.ReadFloat64(i, 'b_z')
					i = node.ReadFloat64_3D(i, 'a1')
					i = node.ReadFloat64(i, 'n_x')
					i = node.ReadFloat64(i, 'n_y')
					i = node.ReadFloat64(i, 'n_z')
			elif (u16_2 == 0xFFFF):
				pass
#				if (node.get('label') is not None):
#					node.typeName = 'Sketch3D'
#					node.set('numEntities', 0)
#					node.set('entities', [])
#					node.sketchEdges = {}
#					node.associativeIDs = {}
#				i = node.ReadUInt32(i, 'numEntities')
#				i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
#				i = node.ReadUInt32A(i, 2, 'a1')
#				i = node.ReadFloat64A(i, 6, 'a2')
			elif (u16_2 == 0x0010):
				if (u16_1 == 0x2000):
					i = node.ReadFloat64A(i, 6, 'a1')
		else:
			node.typeName = 'Label'
			i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadUInt32(i, 'flags')
			i = self.skipBlockSize(i)
			i = node.ReadParentRef(i)
			i = node.ReadCrossRef(i, 'refRoot')
			i = node.ReadChildRef(i, 'ref_2')
			i = self.skipBlockSize(i)
			i = node.ReadUInt32(i, 'index')
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
			i = node.ReadLen32Text16(i)
			i = node.ReadUUID(i, 'uid')
		return i

	def Read_2B48CE72(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_2B60D993(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_2C1BCAEA(self, node): # Helical3D_Parameters
		i = node.Read_Header0('Helical3D_Parameters')
		i = node.ReadCrossRef(i, 'refParam0')
		i = node.ReadCrossRef(i, 'refParam1')
		i = node.ReadCrossRef(i, 'refParam2')
		i = node.ReadCrossRef(i, 'refParam3')
		i = node.ReadCrossRef(i, 'refParam4')
		return i

	def Read_2CE86835(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2010):
			i = node.ReadFloat64_3D(i, 'p0')
			i = node.ReadFloat64_3D(i, 'p1')
			i = node.ReadFloat64_3D(i, 'p2')
			i = node.ReadFloat64_3D(i, 'p3')
			i = node.ReadFloat64_3D(i, 'p4')
		return i

	def Read_2D06CAD3(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadCrossRef(i, 'refSketch')
		i = self.Read2RefList(node, i, 'lst0', importerSegNode.SecNodeRef.TYPE_CROSS)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		return i

	def Read_2D86FC26(self, node): # ReferenceEdgeLoopId
		i = self.ReadContentHeader(node, 'ReferenceEdgeLoopId')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst1')
		return i

	def Read_2E04A208(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 5, 'a1')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a2')
		i = node.ReadUInt32A(i, 3, 'a3')
		return i

	def Read_2E692E29(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refSurface')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_2F39A056(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_2FA5918B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refFX')
		return i

	def Read_30317C9B(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_3061A607(self, node):
		# i = self.ReadEnumValue(node, '', ['']) # 60452313.properties[10h]
		i = self.ReadHeadersss2S16s(node) # 60452313.properties[10h]
		return i

	def Read_30892938(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2017):
			i = node.ReadCrossRef(i, 'refBody')
			i += 4
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_A')
		i = node.ReadCrossRef(i, 'ref_B')
		i = node.ReadCrossRef(i, 'ref_C')
		return i

	def Read_312F9E50(self, node):
		i = self.ReadCntHdr3S(node, 'LoftSections')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_315C9CC8(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_3170E5B0(self, node): # FaceDraftFeature {EA1D0D38-93AD-48BB-84AC-7707FAC29BAF}
		i = self.ReadHeadersss2S16s(node, 'FxFaceDraft')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_317B7346(self, node): # SketchSpline {8006A048-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadSketch2DEntityHeader(node, 'Spline2D')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadUInt32(i, 's')
		else:
			addEmptyLists(node, [0])
			i = self.skipBlockSize(i)
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadUInt8(i, 's')
		i = node.ReadUInt32(i, 'u32_1')
		if (node.get('u32_0') == 0):
			i = node.ReadUInt32(i, 'u32_2')
			i = node.ReadFloat64(i, 'f64_0')
			i = node.ReadUInt32A(i, 3, 'a0')
			i = node.ReadFloat64A(i, node.get('a0')[0], 'a1')
			i = node.ReadFloat64(i, 'f64_1')
			i = node.ReadUInt32A(i, 4, 'a2')
#			i = self.ReadFloat64A(node, i, node.get('a2')[0], 'a3', 2)
#			i = node.ReadFloat64(i, 'f64_2')
#			i = node.ReadUInt32A(i, 2, 'a4')
#			i = self.ReadFloat64A(node, i, node.get('a4')[1], 'a5', 2)
#			i = node.ReadFloat64(i, 'f64_3')
#			i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_31C98504(self, node):
		i = node.Read_Header0()
		return i

	def Read_31D7A200(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_31DBA503(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadChildRef(i, 'refDoc')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadChildRef(i, 'refFX')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadChildRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_31F02EED(self, node): # SweepProfileOrientationEnum {3F4CAC01-D038-490D-9061-9EF6DB007D48}
		i = self.ReadHeaderEnum(node, 'SweepProfileOrientation', ['NormalToPath', 'ParallelToOriginalProfile'])
		return i

	def Read_324C58BF(self, node):
		i = self.ReadCntHdr2SRef(node)
		return i

	def Read_3384E515(self, node): # Geometric_Custom3D
		i = self.ReadHeadersS32ss(node, 'Geometric_Custom3D')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
		else:
			addEmptyLists(node, [0, 1])
			i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		return i

	def Read_338634AC(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = node.ReadCrossRef(i, 'refPart')
		i = node.ReadList4(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadChildRef(i, 'ref_3')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadChildRef(i, 'ref_4')
		return i

	def Read_339807AC(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_33B05D59(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_33EC1003(self, node): # ParallelConstraint3D {73919DC1-220E-4EC9-B716-072D6046A3AD}
		i = self.ReadConstraintHeader3D(node, 'Geometric_Parallel3D')
		if (getFileVersion() > 2016):
			i += 4
		return i

	def Read_346F5947(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_34FAB548(self, node):
		i = self.ReadHeadersss2S16s(node, 'FxExtend')
		return i

	def Read_357D669C(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst2', 5)
		return i

	def Read_3683FF40(self, node): # TwoPointDistanceDimConstraint {C173A079-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Distance_Vertical2D')
		i = node.ReadCrossRef(i, 'refEntity1')
		i = node.ReadCrossRef(i, 'refEntity2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_3689CC91(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'lst0', 3)
		i = self.ReadTransformation(node, i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refParameter')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refParameter1')
		i = node.ReadCrossRef(i, 'refParameter2')
		i = node.ReadCrossRef(i, 'refParameter3')
		return i

	def Read_36C24A82(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		return i

	def Read_36CD0B5B(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadSInt16(i, 's16_0')
		return i

	def Read_375C6982(self, node):
		i = self.ReadCntHdr3S(node, 'EdgeProxy')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'indexRefs')
		if (len(node.get('indexRefs')) > 0):
			i = node.ReadSInt32(i, 's32_0')
		else:
			node.content +=' s32_0=-1'
			node.set('s32_0', -1)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_375EAEE5(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 2, 'a1')
		if (node.get('u8_0') == 0):
			i = node.ReadLen32Text16(i)
			i = node.ReadLen32Text16(i, 'txt0')
			i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_37635605(self, node):
		i = node.Read_Header0()
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst2')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.ReadTransformation(node, i)
		return i

	def Read_37889260(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadFloat64A(i, 4, 'a0')
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadChildRef(i, 'ref1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64_2D(i, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		return i

	def Read_381AF8C4(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_38C2654E(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUUID(i, 'uid')
		i = self.skipBlockSize(i)
		return i

	def Read_38C74735(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refDirection')
		return i

	def Read_3902E4D1(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_39A41830(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 13, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadUInt32A(i,  5, 'a4')
		i = node.ReadFloat64A(i, 6, 'a5')
		i = node.ReadUInt16A(i,  6, 'a6')
		i = node.ReadCrossRef(i, 'refParameter1')
		i = node.ReadCrossRef(i, 'refParameter2')
		i = node.ReadUInt32A(i,  5, 'a7')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		return i

	def Read_39AD9666(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		return i

	def Read_3A083C7B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refTransformation')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadSInt32(i, 's32_2')
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		if (getFileVersion() > 2011):
			i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadCrossRef(i, 'ref_2')
			i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_3A205AB4(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2015):
			i = node.ReadLen32Text16(i, 'txt0')
			i = node.ReadCrossRef(i, 'ref_2')
		else:
			node.content += " txt0='FlatPattern'"
			node.set('txt0', 'FlatPattern')
		return i

	def Read_3A7CFA26(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		return i

	def Read_3A98DCE3(self, node): # EntityReference
		i = node.Read_Header0('EntityReference')
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refEntity')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_3AB895E9(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refDoc')
		return i

	def Read_3AE9D8DA(self, node): # Sketch3D {E4C09561-E779-4A00-A835-E8D43E08A290}
		i = self.ReadHeadersS32ss(node, 'Sketch3D')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'numEntities')
		i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32_2D(i, 'a0')
		if (getFileVersion() > 2011):
			#i = node.ReadFloat64A(i, 6, 'a1')
			i += 6*8
		node.sketchEdges = {}
		node.associativeIDs = {}
		return i

	def Read_3B13313C(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		return i

	def Read_3BA63938(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i, 12)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_3BCC6772(self, node):
		i = self.ReadHeaderEnum(node, '3BCC6772_Enum', [])
		i = self.skipBlockSize(i)
		return i

	def Read_3C6C1C6C(self, node): #
		i = self.ReadHeaderEnum(node, 'LoftCondition', ['Free', 'Tangent', 'Angle', 'Smooth', 'SharpPoint', 'TangentToPlane', 'Direction'])
		return i

	def Read_3C7F67AA(self, node): # Body
		i = self.ReadContentHeader(node, 'Body')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_3D64CCF0(self, node): # Sketch2DPlacementPlane
		i = self.ReadHeadersS32ss(node, 'Sketch2DPlacementPlane')
		i = node.ReadCrossRef(i, 'refTransformation1')
		i = node.ReadCrossRef(i, 'refTransformation2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 7, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPlane')
		return i

	def Read_3D8924FD(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_3E55D947(self, node): # SketchOffsetSpline {063D7617-E630-4D35-B809-64D6695F57C0}:
		i = self.ReadSketch2DEntityHeader(node, 'OffsetSpline2D')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		else:
			i = self.skipBlockSize(i)
			addEmptyLists(node, [0])
		i = node.ReadCrossRef(i, 'refEntity')
		i = node.ReadFloat64(i, 'x')
		return i

	def Read_3E710428(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_3E863C3E(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_2D_UINT32_, 'lst0')
		return i

	def Read_3F36349F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'refTransformation')
		return i

	def Read_3F3634A0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadList4(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		if (getFileVersion() < 2013):
			i = node.ReadUInt32(i, 'u32_0')
			i = self.skipBlockSize(i)
			i = node.ReadUInt8(i, 'u8_0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst2')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst3')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst4')
			cnt, i = getUInt32(node.data, i)
			lst5 = []
			for j in range(cnt):
				id1, i = getUUID(node.data, i)
				id2, i = getUUID(node.data, i)
				u32, i = getUInt32(node.data, i)
				lst5.append([id1, id2, u32])
			node.content += ' lst5=[%s]' %(','.join(['(%s,%s,%04X)' %(r[0], r[1], r[2]) for r in lst5]))
			i = node.ReadCrossRef(i, 'ref_5')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst6')
			i = node.ReadUInt8(i, 'u8_1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst7')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst8')
			i = node.ReadCrossRef(i, 'ref_5')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst9')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst10')
			i = node.ReadUInt8(i, 'u8_2')
			i = node.ReadUInt16(i, 'u16_0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst11')
		else:
			i = node.ReadChildRef(i, 'ref_5')
			if (getFileVersion() > 2016):
				i += 4
		return i

	def Read_3F4FA55F(self, node): # OffsetSplineDimConstraint {BBCEA345-055B-4625-ABCA-582C6BF7E440}
		i = self.ReadContentHeader(node, 'Dimension_OffsetSpline2D')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
		else:
			addEmptyLists(node, [0, 1])
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_40236C89(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32A(i, 3, 'a2')
		return i

	def Read_4028CCAA(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_402A8F9F(self, node):
		i = self.ReadContentHeader(node, 'RotateClockwise')
		if (getFileVersion() > 2010):
			i += 8
		else:
			i += 12
		i = node.ReadUInt8(i, 'clockwise')
		i = self.skipBlockSize(i)
		return i

	def Read_405AB2C6(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_4116DA9E(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64A(i, 10, 'a1')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32A(i, 6, 'a5') # ???????
		i = node.ReadFloat64_2D(i, 'a6') # Angle (e.g.: -pi ... +pi)
		return i

	def Read_424EB7D7(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'parts')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		if (getFileVersion() > 2011):
			i = node.ReadCrossRef(i, 'refSketch')
		else:
			i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFX')

		return i

	def Read_42BC8C9A(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # ???
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_436D821A(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst2', 2)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 5, 'a1')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_43CAB9D6(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadRefU32AList(node, i, 'ls0', 3, importerSegNode.SecNodeRef.TYPE_CHILD)
		return i

	def Read_43CD7C11(self, node): # HoleTypeEnum
		i = self.ReadHeaderEnum(node, 'HoleType', ['Drilled', 'CounterSink', 'CounterBore', 'SpotFace'])
		return i

	def Read_4400CB30(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUUID(i, 'id')
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_442C7DD0(self, node): # EqualRadiusConstraint {8006A080-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadHeaderConstraint2D(node, 'Geometric_EqualRadius2D')
		i = node.ReadCrossRef(i, 'refCircle1')
		i = node.ReadCrossRef(i, 'refCircle2')

		return i

	def Read_4507D460(self, node): # SketchEllipse {8006A04A-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadSketch2DEntityHeader(node, 'Ellipse2D')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		else:
			addEmptyLists(node, [1])
		i = node.ReadCrossRef(i, 'refCenter')
		i = node.ReadFloat64_2D(i, 'dA')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadFloat64(i, 'b')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_452121B6(self, node): # ModelerTxnMgr
		i = node.Read_Header0('ModelerTxnMgr')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		if (node.get('ref_2') is not None):
			if ((getFileVersion() > 2011) and (self.type == DCReader.DOC_PART)):
				i += 4
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_MDL_TXN_MGR_1_, 'lst_1') # <-> BRep.F78B08D5 keys
		else:
			i = node.ReadList6(i, importerSegNode._TYP_MAP_MDL_TXN_MGR_2_, 'lst_1') # <-> BRep.F78B08D5 keys
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_454C24A9(self, node): # Line style
		i = self.ReadChildHeader1(node, 'StyleLine')
		i = self.skipBlockSize(i)
		i = node.ReadColorRGBA(i, 'color')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat32(i, 'width')
		i = node.ReadUInt16A(i, 2, 'a2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_1')
		cnt, i = getUInt16(node.data, i)
		i = node.ReadFloat64A(i, cnt, 'a3')
		i = node.ReadFloat32_3D(i, 'a4')
		i = self.skipBlockSize(i)
		i = node.ReadSInt16A(i, 2, 'a5')
		return i

	def Read_45741FAF(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_4571AC37(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst0')
		return i

	def Read_4580CAF0(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadCrossRef(i, 'ref0')
		i = node.ReadCrossRef(i, 'ref1')
		i = node.ReadCrossRef(i, 'ref2')
		i = node.ReadCrossRef(i, 'ref3')
		return i

	def Read_45825754(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'refEntity3D')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_46407F70(self, node):
		i = self.ReadChildHeader1(node, 'ClearanceHole')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i, 'standard')
		i = node.ReadLen32Text16(i, 'fastener')
		i = node.ReadLen32Text16(i, 'size')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'fit') # 0=Close; 1=Normal; 2=Close
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_464ECA8A(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a0')
		return i

	def Read_4668C201(self, node):
		i = self.ReadHeaderEnum(node, '4668C201_Enum', [])
		return i

	def Read_4688EBA3(self, node):
		i = self.ReadHeaderEnum(node, '4688EBA3_Enum', [])
		return i

	def Read_46D500AA(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_470BB79E(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_4')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_475E7861(self, node):
		i = self.ReadChildHeader1(node, ref1Name='refFX', ref2Name='label')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_4')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadCrossRef(i, 'refFxDims')
		return i

	def Read_481DFC84(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadFloat64A(i, 6, 'a0')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64_2D(i, 'a2')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		return i

	def Read_488C5309(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst2', 2)
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadUInt32(i, 'u32_4')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32A(i, 4, 'a1')
		return i

	def Read_081D7F77(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		return i

	def Read_4A944F03(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		return i

	def Read_D4BDEE88(self, node):
		i = self.ReadList2U32(node)
		return i

	def Read_48C52258(self, node): # BSpline3D
		i = self.ReadContentHeader(node, 'BSpline3D')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'flags2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst2')
		else:
			i = self.skipBlockSize(i)
			addEmptyLists(node, [1, 2])
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refBezier')
		return i

	def Read_48C5F41A(self, node):
		i = node.Read_Header0()
		return i

	def Read_48CF47FA(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 9, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadCrossRef(i, 'refCurve')
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')
		return i

	def Read_48CF71CA(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_4949374A(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadUInt16(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_4AC78A71(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refPlane')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'refDirection')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		return i

	def Read_4ACA204D(self, node): # UserCoordinateSystem {F0854465-652D-4375-98A4-7C875BFE7A9C}
		i = self.ReadCntHdr1SRef(node, 'UserCoordinateSystem', 'refTransformation')
		i = node.ReadCrossRef(i, 'refPlaneXY')
		i = node.ReadCrossRef(i, 'refPlaneXZ')
		i = node.ReadCrossRef(i, 'refPlaneYZ')
		i = node.ReadCrossRef(i, 'refAxisX')
		i = node.ReadCrossRef(i, 'refAxisY')
		i = node.ReadCrossRef(i, 'refAxisZ')
		i = node.ReadCrossRef(i, 'refOrigin')
		i = node.ReadCrossRef(i, 'ref_9')
		return i

	def Read_4B3150E8(self, node):
		i = self.ReadCntHdr2SRef(node, 'LoftSection', 'refWrapper')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadCrossRef(i, 'refCondition')
		i = node.ReadCrossRef(i, 'refImpact')
		i = node.ReadCrossRef(i, 'refAngle')
		i = node.ReadCrossRef(i, 'refTangentPlane')
		i = node.ReadList7(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'refDirectionReversed')
		return i

	def Read_4BB00236(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		if (getFileVersion() > 2014):
			i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_4C06C4D0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = self.ReadRefU32List(node, i, 'lst2')
		return i

	def Read_4CAA281F(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i  = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_4CF1124C(self, node): # SketchBlock
		i = self.ReadCntHdr1SRef(node, 'Block2D')
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadCrossRef(i, 'refBlockDef')
		i = node.ReadCrossRef(i, 'refBlocks')
		i = node.ReadUInt16A(i, 2, 'a0')
		if (node.get('a0')[1] == 0xCA):
			i = node.ReadFloat64_2D(i, 'a1')
		else:
			if (node.get('a0')[0] == 0x0111):
				i = node.ReadFloat64A(i, 4, 'a1')
			else:
				i = node.ReadFloat64A(i, 6, 'a1')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_4D223225(self, node):
		i = self.ReadHeadersS32ss(node)
		return i

	def Read_4DAB0A79(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_4DC465DF(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # ???
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		return i

	def Read_4E4B14BC(self, node): # OffsetConstraint {8006A07C-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Offset2D')
		i = node.ReadCrossRef(i, 'refEntity1')
		i = node.ReadCrossRef(i, 'refEntity2')
		i = node.ReadCrossRef(i, 'refEntity3')
		i = node.ReadCrossRef(i, 'refEntity4')
		return i

	def Read_4E86F047(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_4E86F048(self, node):
		# Not found in PartModel
		i = self.ReadContentHeader(node)
		return i

	def Read_4E86F04A(self, node):
		# Not found in PartModel
		i = self.ReadContentHeader(node)
		return i

	def Read_4E8F7EE5(self, node): # ModelFeatureControlFrame
		i = self.ReadContentHeader(node, 'ModelFeatureControlFrame')
		return i

	def Read_4EF32EF0(self, node): # ClientFeature {BB91C845-BD7E-4470-948F-C5A069B21BBC}
		i = self.ReadHeaderFeature(node, 'Client')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadLen32Text16(i, 'txt2')
		if (getFileVersion() > 2011):
			i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_4F240E1C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refGroup')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refSketch')
		return i

	def Read_4F3DEE08(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_4F8A6797(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_4FB10CB8(self, node):
		i = self.ReadHeaderEnum(node, 'EnumCoilType', ["PitchAndRevolution","RevolutionAndHeight","PitchAndHeight","Spiral"])
		i = node.ReadUInt32(i,'u32_0')
		return i

	def Read_4FD0DC2A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_502678E7(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadFloat64A(i, 4, 'a0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8A(i, 7, 'a1')
		i = node.ReadFloat64A(i, 6, 'a2')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadFloat64A(i, 4, 'a2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_509FB5CC(self, node):
		i = self.ReadCntHdr3S(node, 'Face')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'indexRefs')
		indexes = node.get('indexRefs')
		if (len(indexes) > 0):
			index, i = getUInt32(node.data, i)
			indexes.append(index)
		return i

	def Read_51CA84E2(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # ???
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		return i

	def Read_5246A008(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_52534838(self, node): # PatternConstraint {C173A073-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadSketch2DEntityHeader(node, 'Geometric_PolygonCenter2D')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refCenter')
		i = node.ReadCrossRef(i, 'refConstruction')
		return i

	def Read_526B3F3D(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_528A064A(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0')
		if (node.get('u32_0') > 0):
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadFloat64_3D(i, 'a2')
			i = node.ReadFloat64(i, 'f64_0')
			i = node.ReadFloat64A(i, 10, 'a3')
			i = node.ReadUInt32A(i, 6, 'a4') # ???????
			i = node.ReadFloat64_2D(i, 'a5') # Angle (e.g.: -pi ... +pi)
		return i

	def Read_52D04C41(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refRoot')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_534DD87E(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_537799E0(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_54829655(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		return i

	def Read_55180D7F(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_55279EE0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_553DA303(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadFloat64(i, 'x')
		return i

	def Read_56970DFA(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_56A95F20(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 4, 'a1')
		return i

	def Read_572DBC7C(self, node):
		# not in PartModel
		i = self.ReadContentHeader(node)
		return i

	def Read_574EF622(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'coords', 3)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_578432A6(self, node): # NMx_FFColor_Entity
		i = self.ReadHeadersS32ss(node, 'NMx_FFColor_Entity')
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_57BF6FCE(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUUID(i, 'id')
		i = node.ReadFloat64A(i, 6, 'a0')
		return i

	def Read_5838B762(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64A(i, 9, 'a0')
		return i

	def Read_5838B763(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refPlane')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refEnty1')
		i = node.ReadCrossRef(i, 'refEnty2')
		return i

	def Read_5844C14D(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_588B9053(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_590D0A10(self, node): # TwoLineAngleDimConstraint {C173A07B-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Angle2Line2D')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_598AACFE(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_5A5D8DBF(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i += 4
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_5A6B6124(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_5A9A7BE0(self, node): # CollinearConstraint {8006A076-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Collinear2D')
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadUInt16(i, 's16_0')
		return i

	def Read_5ABD7468(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # ???
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_5B10BF5B(self, node):
		i = node.Read_Header0()
		return i

	def Read_5B708411(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = self.ReadTransformation(node, i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_5B8EC461(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		return i

	def Read_5BE20B76(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_5CB9BB58(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_5CBF4E92(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst3')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst4')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_5CE72F63(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		if(node.get('u8_1') == 1):
			i = self.ReadTransformation(node, i)
		return i

	def Read_5CB011E2(self, node): # SweepProfileScalingEnum {B791B822-BA66-44DD-BD99-09D2CFD9D307}
		i = self.ReadHeaderEnum(node, 'SweepProfileScaling', ['XY', 'X', 'No'])
		return i

	def Read_5D0B89FE(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_5D807360(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refDirection')
		return i

	def Read_5D8C859D(self, node):
		# TODO: only in Assemblies ?!?
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
		else:
			addEmptyLists(node, [0, 1])
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		return i

	def Read_5D93312C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_5DD3A2D3(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		return i

	def Read_5E040F0D(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_5E464B13(self, node): # ModelSurfaceTextureSymbol
		i = self.ReadContentHeader(node, 'ModelSurfaceTextureSymbol')
		if (getFileVersion() > 2017) : i += 4 # skip FF FF FF FF
		return i

	def Read_5E50B969(self, node):
		i = self.ReadHeaderEnum(node, '5E50B969_Enum', [])
		return i

	def Read_5F425538(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_5FB25A7E(self, node):
		i = self.ReadCntHdr3S(node, 'SurfacesSculpt')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_603428AE(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'parts')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFX')
		return i

	def Read_60406697(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_60452313(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		node.content += 'properties={}'
		properties = []
		for j in range(12):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			properties.append(ref)
		if (getFileVersion() > 2015):
			for j in range (12, 18):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
				properties.append(ref)
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadUInt8(i, 'u8_0')
			i = node.ReadUInt16(i, 'u16_0')
			for j in range (18, 21):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
				properties.append(ref)
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
			if (getFileVersion() > 2017):
				i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		else:
			for j in range (12, 15):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
				properties.append(ref)
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
			for j in range (15, 21):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
				properties.append(ref)
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadUInt8(i, 'u8_0')
			i = node.ReadUInt16(i, 'u16_0')
			for j in range (21, 24):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
				properties.append(ref)
			if (getFileVersion() == 2015):
				i += 4
		return i

	def Read_606D9AB1(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		return i

	def Read_614A01F1(self, node):
		i = node.Read_Header0('SurfaceTexture')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadLen32Text8(i, 'txt_0')
		return i

	def Read_616DCA98(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat32_3D(i, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadUInt32(i, 'u32_1')
		cnt, i = getUInt16(node.data, i)
		i = node.ReadFloat64A(i, cnt, 'a4')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a5')
		return i

	def Read_617931B4(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadFloat64_3D(i, 'p1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64_3D(i, 'p2')
		return i

	def Read_618C9E00(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'refEntity')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'refDirection')
		return i

	def Read_61B56690(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_6250D222(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_63266191(self, node): # PerpendicularConstraint3D {2035E584-09E7-4B18-9698-014DEF44B10E}
		i = self.ReadConstraintHeader3D(node, 'Geometric_Perpendicular3D')
		return i

	def Read_637B1CC1(self, node):
		i = self.ReadHeaderEnum(node, 'Enum_637B1CC1', [])
		return i

	def Read_63D9BDC4(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_63E209F9(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		return i

	def Read_6480700A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_6489E49C(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_64DA5250(self, node): # VerticalAlignConstraint {8006A094-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_AlignVertical2D')
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')
		i = self.skipBlockSize(i)
		return i

	def Read_64DE16F3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refEntity')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_6566C3E1(self, node): # LinearModelDimension
		i = self.ReadContentHeader(node, 'ModelDimensionLinear')
		return i

	def Read_656DD01E(self, node):
		i = self.ReadChildHeader1(node, ref1Name='refFX', ref2Name='label')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_65897E4A(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_66085B35(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst0')
		return i

	def Read_660DEE07(self, node): # ??? FilletSetback ???
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # ???
		i = node.ReadCrossRef(i, 'refEdgeProxies')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'radii')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'booleans')
		return i

	def Read_66398149(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadUInt8(i, 'u32_0')
		return i

	def Read_66B388ED(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_671BB700(self, node): # RadiusDimConstraint {C173A081-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Radius2D')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'refCircle')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_671CE131(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_68821F22(self, node): # new since 2018
		i = self.ReadCntHdr1SRef(node)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		return i

	def Read_6985F652(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 6, 'a0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		return i

	def Read_6CA15972(self, node): # new in 2019
		i = node.Read_Header0()
		# 01,00,00,00
		# 02,00,00,30,00,00,00,00
		# 00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,64,00,00,00,00,00,00,00
		# 02,00,00,30,02,00,00,00,02,00,00,00,00,00,00,10
		#       D9,00,00,00,FF,FF,FF,FF
		#       CA,00,00,00,FF,FF,FF,FF
		# 02,01,00,00
		# 00,27,00,00
		# 00,00,00,00
		# 00,02,00,00
		# 00,00,00,00
		# 00,00
		return i

	def Read_6A3EEA31(self, node):
		i = self.ReadContentHeader(node, 'Dimension_Angle2Planes3D')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst1')
		else:
			addEmptyLists(node, [0, 1])
			i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_6B6A06E7(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_6BE30AF0(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'faces')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'edges')
		return i

	def Read_6BF0A0AA(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		if (getFileVersion() < 2016):
			i = node.ReadCrossRef(i, 'refBody')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_A')
		i = node.ReadCrossRef(i, 'ref_B')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_C')
		i = node.ReadCrossRef(i, 'ref_D')
		i = node.ReadCrossRef(i, 'ref_E')
		i = node.ReadCrossRef(i, 'ref_F')
		i = node.ReadCrossRef(i, 'ref_G')
		i = node.ReadCrossRef(i, 'ref_H')
		if (getFileVersion() > 2015):
			i = node.ReadCrossRef(i, 'refBody')
		return i

	def Read_6C5CD68F(self, node):
		i = node.Read_Header0()
		return i

	def Read_6C5CD690(self, node):
		i = node.Read_Header0()
		return i

	def Read_6C69E7B8(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst3')
		return i

	def Read_6C7D97A9(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_6CA92D02(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_1')
		if (self.type == DCReader.DOC_ASSEMBLY):
			i = node.ReadLen32Text16(i, 'txt')
		else:
			i = self.skipBlockSize(i)
			i = node.ReadUInt32(i, 'u32_1')
			if (getFileVersion() > 2017):
				i += 4
			else:
				i = self.skipBlockSize(i)
			i = node.ReadUInt32(i, 'u32_2')
			i = self.skipBlockSize(i)
			i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
			i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
			i = node.ReadUInt8(i, 'u8_1')
			i = self.skipBlockSize(i)
			i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadCrossRef(i, 'ref_2')
			i = node.ReadUInt32(i, 'u32_3')
			i = node.ReadUInt8(i, 'u8_2')
		return i

	def Read_6DC1CDC3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadUInt8(i, 'u8_2')
		return i

	def Read_6D6BE9B7(self, node):
		i = self.ReadChildHeader1(node)
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		cnt, i = getUInt32(node.data, i)
		for j in range(cnt):
			i = node.ReadLen32Text16(i, 'txt%i' %(j+1))
		return i

	def Read_6DFCBEE5(self, node):
		# This is not a parameter comment!!! -> validate with 20-004Z1.ipt Parameter 'd47'
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_6E2BCB60(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		i = node.ReadUInt32(i, 'u32_5')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_6F7A6F97(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_6F7A6F9C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_6F891B34(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 9, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_6FB0D4A7(self, node): # ModelLeaderNote {5194100D-435F-4C85-A922-6BD3E4CC9C36}
		i = self.ReadContentHeader(node, 'ModelLeaderNote')
		return i

	def Read_6FD9928E(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_716090B3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		if (getFileVersion() > 2017):
			i += 8
		else:
			i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_A')
		i = node.ReadCrossRef(i, 'ref_B')
		return i

	def Read_720E6C90(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_723BA8B3(self, node):
		i = node.Read_Header0()
		return i

	def Read_7256922C(self, node):
		i = self.ReadCntHdr2SRef(node, 'refTransformation')
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_7270F478(self, node):
		i = self.ReadCntHdr2SRef(node)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_729ABE28(self, node): # PartFeatureOperationEnum {5E441A99-F1EE-472B-A356-383075A9303D}
		# extrusoins like pad, pocket, revolution, groove, ...
		i = self.ReadHeaderEnum(node, 'PartFeatureOperation', ['*UNDEFINED*', 'NewBody', 'Cut', 'Join', 'Intersection', 'Surface'])
		return i

	def Read_72A7D774(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text8(i, 'txt0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		return i

	def Read_72C97D63(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		rows, i = getUInt32(node.data, i)
		cols, i = getUInt32(node.data, i)
		lst = []
		for r in range(rows):
			tmp = []
			for c in range(cols):
				ref, i = self.ReadNodeRef(node, i, r, importerSegNode.SecNodeRef.TYPE_CROSS)
				tmp.append(ref)
			lst.append(tmp)
		node.set('lst2', lst)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadSInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadFloat64_2D(i, 'a1')
		return i

	def Read_7312DB35(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadFloat64A(i, 4, 'a0')
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadChildRef(i, 'ref1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64_2D(i, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
# 00 00 00 00 00 00 00 00 00 00 01 00
# CrossRef
# 00 00 00 00
		return i

	def Read_7325290E(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'refBody')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'refEntity')
		return i

	def Read_7325290F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'refBody')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_736C138D(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		cnt, i = getUInt32(node.data, i)
		i = self.ReadUInt32A(node, i, cnt, 'lst1', 1)
		return i

	def Read_73CAC628(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_73F35CD0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refDirection')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'refEntity')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst0', 2)
		i = node.ReadUInt8(i, 'u8_0')
		if (node.get('u8_0') != 0):
			i = node.ReadSInt32(i, 's32_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPlane')
		return i

	def Read_7414D5CA(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # ???
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_,     'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_,     'lst2')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_,  'lst3', 3)
		return i

	def Read_7457BB19(self, node): # TangentConstraint3D {0456FF0D-196E-4C72-989D-D86E3DD32955}
		i = self.ReadConstraintHeader3D(node, 'Geometric_Tangential3D')
		if (getFileVersion() < 2013):
			i += 1
		i = node.ReadCrossRef(i, 'refParameter')
		if (getFileVersion() < 2013):
			i += 1
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_746BB6E6(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_748FBD64(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		u8 = node.get('u8_0')
		if (u8 == 0):
			i = node.ReadUInt32(i, 'u32_4')
			i = node.ReadLen32Text16(i, 'txt0')
			i = node.ReadLen32Text16(i, 'txt1')
			i = node.ReadUInt16(i, 'u16_0')
		else:
			i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_74DF96E0(self, node): # DiameterDimConstraint {C173A07F-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Diameter2D')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'refCircle')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_74E6F48A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refPlane1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refEntity')
		i = node.ReadCrossRef(i, 'refPlane2')
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadUInt16A(i, 3, 'a0')
		i = node.ReadFloat64A(i, 9, 'a1')
		return i

	def Read_75A6689B(self, node): # Geometric_PolygonPattern2D
		i = self.ReadHeadersS32ss(node, 'Geometric_PolygonPattern2D')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 3)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'pattern')
		i = node.ReadUInt16A(i, 4, 'a1')
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		return i

	def Read_75F64419(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		return i

	def Read_76BDB118(self, node): # new in 2019
		i = node.Read_Header0()
		# 00,00,00,00,00,42,00,19
		# 03,00,00,80
		# 71,06,00,00
		# FF,FF,FF,FF
		# 07,0F,00,80
		# 02,00,00,30,01,00,00,00,01,00,00,00,00,00,00,00
		#       08,0F,00,80
		# 00,00,00,00
		return i

	def Read_76EC185B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_774572D4(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		if (getFileVersion() > 2016):
			i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_7777785F(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_778752C6(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'refDirection')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt32(i, 'u32_0')
		cnt, i = getUInt32(node.data, i)
		lst0 = []
		for j in range(cnt):
			r1, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CHILD)
			r2, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			lst0.append([r1, r2])
		node.content += ' lst0=[%s]' %(','.join(['[%s,%s]' %(r[0], r[1]) for r in lst0]))
		return i
		node.set('lst0', lst0)
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadChildRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		return i

	def Read_77D10C74(self, node): # new in 2019
		i = node.Read_Header0()
		# 05,00,00,00
		# 02,00,00,30,00,00,00,00
		# 00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,B4,00,00,00,00,00,00,00
		# 02,00,00,30,02,00,00,00,02,00,00,00,00,00,00,10
		#        18,00,00,00,FF,FF,FF,FF
		#        21,09,00,00,FF,FF,FF,FF
		# 00,00,00,00
		# 2A,09,00,00
		return i

	def Read_78F28827(self, node): # FilletTypeEnum
		i = self.ReadHeaderEnum(node, 'FilletType', ['Edge', 'Face', 'FullRound'])
		return i

	def Read_7911B59E(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadChildRef(i, 'ref_5')
		return i

	def Read_797737B1(self, node): # FxDimension
		i = node.Read_Header0('FxDimension')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'anchors', 3)
		i = self.ReadTransformation(node, i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refParameter')
		return i

	def Read_79D4DD11(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		return i

	def Read_7A1BCDC6(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		return i

	def Read_7A98AD0E(self, node): # TextBoxConstraint {037C3FDB-8A3C-443F-8CF6-993D3295335C}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_TextBox2D')
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadCrossRef(i, 'refLine3')
		i = node.ReadCrossRef(i, 'refLine4')
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')
		i = node.ReadCrossRef(i, 'refPoint3')
		i = node.ReadCrossRef(i, 'refPoint4')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64(i, 'x')
		return i

	def Read_7C321197(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_7C340AFD(self, node):
		i = self.ReadChildHeader1(node, ref1Name='refFX', ref2Name='label')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_7C39DC59(self, node):
		i = self.ReadChildHeader1(node)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_7C44ABDE(self, node): # Bezier3D
		i = self.ReadSketch3DEntityHeader(node, 'Bezier3D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'refPoints')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a2')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32A(i, 3, 'a3')
		cnt = node.get('a3')[0]
		i = node.ReadFloat64A(i, cnt, 'a4')
		i = node.ReadUInt32A(i, 6, 'a5')
		cnt = node.get('a5')[3]
		i = self.ReadFloat64A(node, i, cnt, 'points', 3)
		i = node.ReadFloat64(i, 'f64_1')
		i = node.ReadUInt32A(i, 2, 'a6')
		cnt = node.get('a6')[0]
		i = self.ReadFloat64A(node, i, cnt, 'lst1', 3)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 3, 'a7')
		i = node.ReadFloat64(i, 'f64_2')
		i = node.ReadUInt32A(i, 3, 'a8')
		cnt = node.get('a8')[0]
		i = node.ReadFloat64A(i, cnt, 'a9')
		i = node.ReadUInt32A(i, 6, 'a10')
		cnt = node.get('a10')[3]
		i = self.ReadFloat64A(node, i, cnt, 'lst3', 3)
		i = node.ReadFloat64(i, 'f64_3')
		i = node.ReadUInt32A(i, 2, 'a11')
		cnt = node.get('a11')[0]
		i = self.ReadFloat64A(node, i, cnt, 'lst4', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64A(i, 6, 'a12')
		return i

	def Read_7C6D149E(self, node): # SplineFitPointConstraint {8006A07A-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadHeaderConstraint2D(node, 'Geometric_SplineFitPoint2D')
		i = node.ReadCrossRef(i, 'refSpline')
		i = node.ReadCrossRef(i, 'refPoint')
		return i

	def Read_7C6D7B13(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_7DA7F733(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadUInt16A(i, 9, 'a0')
		i = node.ReadCrossRef(i, 'ref_7')
		return i

	def Read_7DAA0032(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_7DF60748(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i+= 4 # skip FF FF FF FF
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		return i

	def Read_7E0E4CA9(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUUID(i, 'id1')
		i = node.ReadUUID(i, 'id2')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_7E15AA39(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		return i

	def Read_7E36DE81(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_STRING16_, 'lst0')
		return i

	def Read_7E5D2868(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_7F4A3E30(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadUInt16A(i, 3, 'a0')
		if (getFileVersion() > 2016):
			i = node.ReadUInt8(i, 'u8_0')
		else:
			node.content += ' u8_0=01'
			node.set('u8_0', 1)
			i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 6, 'a1')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadFloat64A(i, 6, 'a2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadFloat64A(i, 24, 'a3')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt16A(i, 4, 'a4')
		i = node.ReadFloat64A(i, 6, 'a5')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 3, 'a6')
		i = node.ReadFloat64A(i, 18, 'a7')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadFloat64A(i, 18, 'a8')
		i = node.ReadUInt8(i, 'u8_3')
		if (getFileVersion() > 2010):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		else:
			addEmptyLists(node, [0])
			i += 4 # skipt 0x000002F5
		i = node.ReadFloat64A(i, 12, 'a9')
		i = node.ReadUInt8(i, 'u8_4')
		i = node.ReadUInt16A(i, 5, 'a10')
		i = node.ReadFloat64A(i, 7, 'a11')
		return i

	def Read_7F7F05AC(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i+= 4 # skip FF FF FF FF
		return i

	def Read_7F936BAA(self, node): # DecalFeature {9C693BB0-7C99-4D06-961E-99936273C492}
		i = self.ReadHeaderFeature(node, 'Decal')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'refSketch')
		return i

	def Read_80102AC1(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i)
		if (node.get('u8_0') > 0):
			i = node.ReadUInt8(i, 'u8_1')
#		if (getFileVersion() > 2017):
#			i += 4
		return i

	def Read_81E94AB7(self, node):
		i = self.ReadContentHeader(node, 'SurfaceDetails')
		if (getFileVersion() > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadFloat64A(i, 4, 'a0')
		i = node.ReadUInt8A(i, 11, 'a1')
		i = node.ReadFloat64A(i, 6, 'a2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref0')
		i = node.ReadChildRef(i, 'ref1')
		i = node.ReadChildRef(i, 'ref2')
		i = node.ReadChildRef(i, 'ref3')
		i = node.ReadChildRef(i, 'ref4')
		i = node.ReadChildRef(i, 'ref5')
		i = node.ReadChildRef(i, 'ref6')
		i = node.ReadChildRef(i, 'ref7')
		i = node.ReadChildRef(i, 'ref8')
		i = node.ReadChildRef(i, 'ref9')
		i = node.ReadChildRef(i, 'refA')
		i = node.ReadChildRef(i, 'refB')
		i = node.ReadChildRef(i, 'refC')
		i = node.ReadChildRef(i, 'refD')
		return i

	def Read_821ACB9E(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_828E73A6(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		lst = []
		for j in range(cnt):
			u32, i = getUInt32(node.data, i)
			f64, i = getFloat64(node.data, i)
			lst.append([u32, f64])
		node.content += ' lst1=[%s]' %(','.join(['(%04X,%g)'%(r[0], r[1]) for r in lst]))
		node.set('lst1', lst)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_831EBCE9(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_833D1B91(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_8367B125(self, node): # ParameterText
		i = self.ReadContentHeader(node, 'ParameterText')
		if (getFileVersion() > 2018): i += 4 # ???
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'isKey')
		i = node.ReadLen32Text16(i, 'value')
		return i

	def Read_8398E8EC(self, node):
		i = node.Read_Header0()
		return i

	def Read_83D31932(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refLine')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')
		return i

	def Read_841B40DB(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_843A19FE(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		if (getFileVersion() > 2017):
			i = node.ReadCrossRef(i, 'refBody')
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_A')
		i = node.ReadCrossRef(i, 'ref_B')
		return i

	def Read_845212C7(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i, 12)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_855B1557(self, node): # new in 2019
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'arr_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_86173E3F(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadFloat64_3D(i, 'a0')
		return i

	def Read_86197AE1(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_8677CE83(self, node):
		i = self.ReadCntHdr2SRef(node)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		return i

	def Read_86A4AAC4(self, node): # SketchBlock
		i = self.ReadContentHeader(node, 'SketchBlock')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = node.ReadCrossRef(i, 'refDirection')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		else:
			addEmptyLists(node, [2])
		i = node.ReadCrossRef(i, 'refCenter')
		i = node.ReadUUID(i, 'id')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_871D6F71(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadFloat32_3D(i, 'a1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat64A(i, 4, 'a2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_889E21C1(self, node):
		i = node.Read_Header0()
		return i

	def Read_88FA65CA(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		if (getFileVersion() > 2017):
			i+= 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')

		return i

	def Read_8946E9E8(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018):i += 4 # 0xFFFFFF
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_896A9790(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		return i

	def Read_8AF0E725(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refEntity')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refTransformation')
		return i

	def Read_8AFFBE5A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refPlane')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		return i

	def Read_8B1E9A97(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadFloat64(i, 'f64_0')
		i  =node.ReadList6(i, importerSegNode._TYP_MAP_U16_U16_)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_8B2B8D96(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_8B2BE62E(self, node):
		# i = self.ReadEnumValue(node, '')
		i = self.ReadHeadersss2S16s(node)
		return i

	def Read_8B3E95F7(self, node):
		i = node.Read_Header0('SurfaceDetail')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_8BE7021F(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32A(i, 14, 'a0') # 26 - 6 -1 = 19
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadUInt32A(i, 5, 'a2') # 26 - 6 -1 = 19
		i = node.ReadFloat64A(i, 6, 'a3')
		i = node.ReadUInt32A(i, 3, 'a4')
		i = node.ReadCrossRef(i, 'ref1')
		i = node.ReadCrossRef(i, 'ref2')
		i = node.ReadUInt32A(i, 6, 'a5')
		i = node.ReadChildRef(i, 'ref3')
		i = node.ReadLen32Text16(i)
		return i

	def Read_8C702CD5(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadFloat64_3D(i, 'a1')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2010): i += 48 # skip trailing 0x00's !
		return i

	def Read_8D6EF0BE(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadList4(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_8DFFE0CD(self, node):
		i = node.Read_Header0()
		return i

	def Read_8E5D4198(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		if (node.get('u32_1') == 0):
			i = node.ReadUInt8(i, 'u8_0')
			cnt, i = getUInt32(node.data, i)
			i = node.ReadUInt32A(i, cnt, 'a1')
			cnt, i = getUInt32(node.data, i)
			i = node.ReadUInt32A(i, cnt, 'a2')
			i = node.ReadUInt32A(i, 2, 'a3')
			i = node.ReadUInt8(i, 'u8_1')
		else:
			if(getFileVersion() > 2010):
				i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadUInt32(i, 'u32_0')
			i = self.skipBlockSize(i)
		return i

	def Read_8EB19F04(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadUInt8(i, 'u8_3')
		i = self.ReadRefU32List(node, i, 'lst2')
		return i

	def Read_8EC6B314(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'group')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst2')
		else:
			i = self.skipBlockSize(i, 8)
			addEmptyLists(node, [1, 2])
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'spline')
		i = node.ReadCrossRef(i, 'line')
		return i

	def Read_8EDEE6CB(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i, 12)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_8EE901B9(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_8EF06C89(self, node): # SketchLine3D {87056D9A-B0B2-4BD0-A6EC-51E9D893A502}
		i = self.ReadSketch3DEntityHeader(node, 'Line3D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		if (len(node.data) - i == 6*8 + 1 + 4):
			i += 4
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')
		i = node.ReadFloat64(i, 'dirX')
		i = node.ReadFloat64(i, 'dirY')
		i = node.ReadFloat64(i, 'dirZ')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_8F2822F9(self, node):
		i = self.ReadCntHdr2SRef(node)
		i = node.ReadFloat64A(i, 6, 'a0')
		return i

	def Read_8F41FD24(self, node): # EndOfFeatures {A89E388A-13C9-4FFA-B777-9C0E1C81F136}
		i = self.ReadHeadersS32ss(node, 'EndOfFeatures')
		return i

	def Read_8F55A3C0(self, node): # HorizontalAlignConstraint {8006A086-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_AlignHorizontal2D')
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')
		i = self.skipBlockSize(i)
		return i

	def Read_8FEC335F(self, node):
		# TODO: constraint together with Geometric_TextBox2D and DC93DB08 <-> Hairdryer: Sketch47, Sketch48, Speedometer: Sketch3, Sketch10
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadCrossRef(i, 'refLine3')
		i = node.ReadCrossRef(i, 'refLine4')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'refPoint2')
		return i

	def Read_903F453F(self, node): # ExtrusionSurface
		i = node.Read_Header0('ExtrusionSurface')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'label')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_907EAD2B(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_90874D11(self, node): # PlanarSketch {2C16787F-83FF-11D4-8DDB-0010B541CAA8}
		i = self.ReadHeadersS32ss(node, 'Sketch2D')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'numEntities')
		i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refTransformation')
		i = node.ReadCrossRef(i, 'refDirection')
		i = node.ReadUInt32A(i, 2, 'a0')
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		else:
			addEmptyLists(node, [1])
		node.sketchEdges = {}
		node.associativeIDs = {}
		return i

	def Read_90874D13(self, node): # SketchEntityRef
		i = node.Read_Header0('SketchEntityRef')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'entityAI')  # association number of the entity inside the referenced sketch
		i = node.ReadUInt32(i, 'typEntity') # type of the entity (should be 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'point1AI')  # association number of the start point inside the referenced sketch
		i = node.ReadUInt32(i, 'typPt1')    # type of the entity (should be 1)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt32(i, 'point2AI')  # association number of the start point inside the referenced sketch
		i = node.ReadUInt32(i, 'typPt2')    # type of the entity (should be 1)
		i = node.ReadUInt8(i,  'posDir')    # Indicator for the orientation of edge (required for e.g. circles)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		return i

	def Read_90874D15(self, node): # Styles
		i = node.Read_Header0('Styles')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'refEntityReference')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'associativeID') # Number of the entity inside the sketch
		i = node.ReadUInt32(i, 'typEntity')
		return i

	def Read_90874D16(self, node): # Document
		self.type = DCReader.DOC_PART
		i = node.Read_Header0('Document')
		i = node.ReadChildRef(i, 'label')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i,        'uid_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt16A(i, 6,  'a0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i,    'refElements')
		i = node.ReadChildRef(i,    'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i,    'ref_2')
		i = node.ReadChildRef(i,    'refWorkbook') # embedded Excel file
		i = node.ReadChildRef(i,    'cld_1')
		i = node.ReadChildRef(i,    'cld_2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i,    'ref_3')
		#i = node.ReadChildRef(i,    'ref_4')
		i = node.ReadUInt16A(i, 2,  'a0')
		i = node.ReadChildRef(i,    'ref_5')
		i = node.ReadUInt32(i,      'u32_2')
		i = node.ReadChildRef(i,    'red_6')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i,    'ref_7')
		i = node.ReadLen32Text16(i, 'refSegName')
		i = node.ReadFloat64(i,     'f64_0')
		i = node.ReadChildRef(i,    'ref_8')
		return i

	def Read_90874D18(self, node): # Transformation
		i = self.ReadContentHeader(node, 'Transformation')
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = self.ReadTransformation(node, i)
		return i

	def Read_90874D21(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i,    'ref_1')
		i = node.ReadCrossRef(i,    'refTransformation')
		i = node.ReadCrossRef(i,    'refParameter1')
		i = node.ReadCrossRef(i,    'refParameter2')
		i = node.ReadCrossRef(i,    'refParameter3')
		return i

	def Read_90874D23(self, node): # Sketch2DPlacement
		i = self.ReadHeadersS32ss(node, 'Sketch2DPlacement')
		i = node.ReadCrossRef(i, 'refTransformation1')
		i = node.ReadCrossRef(i, 'refTransformation2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refDirection')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'refTransformation2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst0', 2)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_90874D26(self, node): # Parameter
		i = self.ReadCntHdr3S(node, 'Parameter')
		i = node.ReadLen32Text16(i)            # name of the parameter
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'refUnit')
		i = node.ReadChildRef(i, 'refValue')
		i = node.ReadFloat64(i, 'valueNominal')
		i = node.ReadFloat64(i, 'valueModel')
		i = node.ReadEnum16(i, 'tolerance', Tolerances)
		i = node.ReadSInt16(i, 'u16_0')
		return i

	def Read_90874D28(self, node): # ParameterBoolean
		i = self.ReadContentHeader(node, 'ParameterBoolean')
		if (getFileVersion() > 2010):
			if (getFileVersion() > 2018): i += 4
			i = node.ReadLen32Text16(i)
			i += 4
		else:
			node.name = ''
			i += 12
		i = node.ReadBoolean(i, 'value')
		return i

	def Read_90874D40(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadList3(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadFloat64(i, 'f')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_90874D46(self, node): # Document
		self.type = DCReader.DOC_ASSEMBLY
		i = node.Read_Header0('Document')
		i = node.ReadChildRef(i, 'label')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i,        'uid_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32A(i, 3,  'a0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i,    'refElements')
		i = node.ReadChildRef(i,    'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i,    'ref_2')
		i = node.ReadChildRef(i,    'refWorkbook') # embedded Excel file
		i = node.ReadChildRef(i,    'ref_3')
		i = node.ReadChildRef(i,    'ref_4')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2,  'a2')
		i = node.ReadChildRef(i,    'ref_5')
		i = node.ReadUInt32(i,      'u32_2')
		i = node.ReadChildRef(i, 'ref_6')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadChildRef(i, 'ref_7')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadChildRef(i, 'ref_8')
		i = node.ReadChildRef(i, 'ref_9')
		i = node.ReadChildRef(i, 'ref_A')
		if (getFileVersion() > 2012):
			i = node.ReadChildRef(i, 'ref_B')
		return i

	def Read_90874D47(self, node): # SurfaceBody {5DF86089-6B16-11D3-B794-0060B0F159EF}
		i = self.ReadContentHeader(node, 'SurfaceBody')
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadSInt32(i, 's32_0')
		return i

	def Read_90874D48(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		return i

	def Read_90874D51(self, node):
		i = self.ReadCntHdr3S(node, 'EdgeCollectionProxy')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'edges')
		return i

	def Read_90874D53(self, node):
		i = self.ReadHeadersS32ss(node, None, 'creator')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'refBody')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'wireIndex')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)

		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refOwner')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'edgeIdx')
		return i

	def Read_90874D55(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'refBody')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'wireIndex')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFace')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_90874D56(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		if (node.get('u8_0') == 0):
			i = node.ReadLen32Text16(i)
			i = node.ReadLen32Text16(i, 'txt0')
			i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_90874D60(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		return i

	def Read_90874D61(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_90874D62(self, node): # Group2D
		i = self.ReadHeadersS32ss(node, 'Group2D')
		i = node.ReadSInt32(i, 's32_1')
		i = self.skipBlockSize(i, 12)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_X_REF_, 'lst1')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_90874D63(self, node): # PartComponentDefinition {DA33F1A3-7C3F-11D3-B794-0060B0F159EF}
		i = node.Read_Header0()
		if ((getFileVersion() > 2014) and (node.get('hdr').m == 36)):
			node.delete('hdr')
			node.content = ''
			i = node.ReadLen32Text8(0)
			i = node.ReadUInt16A(i, 7, 'a0')
			i = node.ReadLen32Text8(i, 'txt0')
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadUInt16(i, 'u16_1')
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_X_REF_, 'parameters')
			i = node.ReadUInt32A(i, 4, 'a1')
			if (node.get('a1')[3] > 0):
				i = node.ReadUInt16(i, 'u16_2')
				i = node.ReadParentRef(i)
				i = node.ReadSInt32(i, 's32_0')
				l, j = getSInt32(node.data, i)
				if (l != -1):
					i = node.ReadLen32Text16(i)
					if (len(node.name) > 0):
						node.typeName = 'Parameter'
						i = node.ReadChildRef(i, 'label')
						i = node.ReadChildRef(i, 'refUnit')
						i = node.ReadChildRef(i, 'refValue')
						i = node.ReadFloat64(i, 'valueNominal')
						i = node.ReadFloat64(i, 'valueModel')
						i = node.ReadEnum16(i, 'tolerance', Tolerances)
						i = node.ReadSInt16(i, 'u16_0')
					else:
						pass
#						i = node.ReadUInt32(i, 'u32_2')
#						i = node.ReadUInt8(i, 'u8_0')
				else:
					node.typeName = 'Group2D'
					i = j
					i = node.ReadSInt32(i, 'u32_3')
#					i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'constraints')
#					i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'entities')
#					i = node.ReadSInt32(i, 'u32_4')
		else:
			i = node.ReadChildRef(i, 'cld_0')
			i = node.ReadUInt16A(i, 2, 'a0')
			i = self.skipBlockSize(i)
			i = node.ReadParentRef(i)
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_X_REF_, 'parameters')
			i = node.ReadUInt32A(i, 2, 'a1')
			if (getFileVersion() > 2012):
				i += 4
			i = node.ReadUInt32A(i, 2, 'a2')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_UUID_UINT32_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_UUID_X_REF, 'lst2')
			i = node.ReadParentRef(i)
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst3')
			i = node.ReadUInt16A(i, 2, 'a3')
		return i

	def Read_90874D67(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		return i

	def Read_90874D74(self, node): # FaceCollectionProxy
		i = self.ReadHeadersS32ss(node, 'FaceCollectionProxy')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'edges')
		i = node.ReadCrossRef(i, 'edgesProxy')
		return i

	def Read_90874D91(self, node): # Feature
		i = self.ReadHeadersS32ss(node, 'Feature')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_90874D94(self, node): # CoincidentConstraint {8006A074-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Coincident2D')
		i = node.ReadCrossRef(i, 'refEntity1')
		i = node.ReadCrossRef(i, 'refEntity2')
		return i

	def Read_90874D95(self, node): # ParallelConstraint {8006A08A-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Parallel2D')
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_90874D96(self, node): # PerpendicularConstraint {8006A08C-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Perpendicular2D')
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_90874D97(self, node): # TangentConstraint {0A73D068-AC6B-4B51-8B6D-913B90A77741}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Tangential2D')
		i = node.ReadCrossRef(i, 'refEntity1')
		i = node.ReadCrossRef(i, 'refEntity2')
		if (getFileVersion() > 2012):
			i += 4
		return i

	def Read_90874D98(self, node): # HorizontalConstraint {8006A084-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Horizontal2D')
		i = node.ReadCrossRef(i, 'refLine')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_90874D99(self, node): # VerticalConstraint {8006A092-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Vertical2D')
		i = node.ReadCrossRef(i, 'refLine')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_90B64134(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 1
		return i

	def Read_90F4820A(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_914B3439(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_A')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		if (getFileVersion() > 2017):
			i += 4
		i = node.ReadCrossRef(i, 'ref_B')
		return i

	def Read_91637937(self, node):
		i = self.ReadChildHeader1(node, ref1Name='refFX')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		i = self.ReadUInt32A(node, i, cnt, 'a1', 2)
		i = node.ReadUInt32A(i, 2, 'a2')
		return i

	def Read_91B99A2C(self, node): # FilletIntermediateRadius
		i = self.ReadContentHeader(node, 'FilletIntermediateRadius')
		if (getFileVersion() > 2017): i += 4 # skipp 0xFFFFFFFF (-1)
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'refRadius')
		i = node.ReadCrossRef(i, 'refEdgeProxy')
		return i

	def Read_92637D29(self, node):
		i = self.ReadHeaderEnum(node, 'ExtentType', ['0', 'Dimension', '2_Dimensions', 'Path', 'ToNext', 'All', 'FromTo', 'To'])
		return i

	def Read_9271AB29(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i, 'fmt1')
		i = node.ReadLen32Text16(i, 'fmt2')
		i = node.ReadChildRef(i, 'param1')
		i = node.ReadChildRef(i, 'param2')
		return i

	def Read_936522B1(self, node):
		i = self.ReadCntHdr3S(node, 'HoleCenterPoints')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		return i

	def Read_938BED94(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadParentRef(i)
		if (getFileVersion() < 2011):
			i = node.ReadCrossRef(i, 'refCircle')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		lst0 = {}
		for j in range(cnt):
			key, i = getLen32Text16(node.data, i)
			val, i = getLen32Text16(node.data, i)
			lst0[key] = val
		node.content += ' lst0={%s}' %(','.join(['%s:%s' %(k, v) for k, v in lst0.items()]))
		node.set('lst0', lst0)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_93C7EE68(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_951388CF(self, node):
		i = self.skipBlockSize(0)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 12, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 9, 'a1')
		return i

	def Read_955501BC(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # ???
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_9574000C(self, node): # Hole Annotation
		i = self.ReadContentHeader(node, 'AnnotationHole')
		if (getFileVersion() > 2017): i += 4 # skip FF FF FF FF
		return i

	def Read_95DC570D(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'refValue')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_98EA1C87(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		return i

	def Read_99684A5A(self, node):
		i = self.ReadCntHdr3S(node)
		if (getFileVersion() > 2010):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadUInt32(i, 'u32_1')
		else:
			node.set('u32_0', 0)
			node.set('u32_1', 0)
			node.content += " u32_0=000000 u32_1=000000"
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i, 4)
		return i

	def Read_96058864(self, node):
		i = self.ReadCntHdr2SRef(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_97DBCF9C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		if (getFileVersion() > 2017):
			i = node.ReadCrossRef(i, 'ref_8')
			i += 4
		return i

	def Read_99B938AE(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadFloat64_2D(i, 'a1')
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2011):
			i = node.ReadUInt32(i, 'u32_1')
		else:
			node.content += ' u32_1=000000'
			node.set('u32_1', 0)
		return i

	def Read_99B938B0(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadUInt32A(i, 18, 'a0')

		i = node.ReadUInt32(i, 'typ')
		typ = node.get('typ')
		if (typ == 0x03):
			i = node.ReadUInt16A(i, 3, 'a1')
		elif (typ == 0x23):
			i = node.ReadUInt16A(i, 1, 'a1')
		else:
			node.set('a1', [])
		i = node.ReadFloat64_2D(i, 'a2')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadFloat64A(i, 6, 'a4')
		i = node.ReadUInt16A(i, 6, 'a5')
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadUInt32A(i, 6, 'a6')
		return i

	def Read_9A444CCC(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_9A94E347(self, node):
		i = self.ReadChildHeader1(node, ref1Name='refFX', ref2Name='label')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		cnt, i = getUInt32(node.data, i)
		i = self.ReadUInt32A(node, i, cnt, 'lst1', 4)
		return i

	def Read_9B043321(self, node):
		i = node.Read_Header0()
		return i

	def Read_9BB4281C(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadUInt32A(i, 2, 'val_key_1')
		i = node.ReadUInt32A(i, 2, 'val_key_2')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadU32U32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = node.ReadUInt32A(i, 2, 'val_key_3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a2')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a3')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a4')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a5')
		i = node.ReadUInt32A(i, 3, 'a5')
		return i

	def Read_9C38036E(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_9C3D6A2F(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 3, 'a2')
		if (node.get('a2')[2] == 1):
			i = node.ReadUInt32A(i, 3, 'a3')

		else:
			node.content += ' a3=[0000,0000,0000]'
			node.set('a3', [0,0,0])
		return i

	def Read_9C8C1297(self, node):
		i = self.ReadContentHeader(node, 'UserCoordinateSystemValues')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'refUCS')
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'refParamXOffset')
		i = node.ReadCrossRef(i, 'refParamYOffset')
		i = node.ReadCrossRef(i, 'refParamZOffset')
		i = node.ReadCrossRef(i, 'refParamXAngle')
		i = node.ReadCrossRef(i, 'refParamYAngle')
		i = node.ReadCrossRef(i, 'refParamZAngle')
		return i

	def Read_9D2E8361(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_9D71D698(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_9DA736B0(self, node):
		# i = self.ReadEnumValue(node, '') # not found in features
		i = self.ReadHeadersss2S16s(node)
		return i

	def Read_9DC2A241(self, node):
		i = node.Read_Header0()
		return i

	def Read_9E43716A(self, node): # Circle3D
		i = self.ReadSketch3DEntityHeader(node, 'Circle3D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')
		i = node.ReadFloat64_3D(i, 'normal')
		i = node.ReadFloat64_3D(i, 'm')
		i = node.ReadFloat64(i, 'r')
		i = node.ReadFloat64(i, 'startAngle')
		i = node.ReadFloat64(i, 'sweepAngle')
		i = node.ReadCrossRef(i, 'refCenter')
		return i

	def Read_9E43716B(self, node):
		i = self.ReadSketch3DEntityHeader(node, 'Ellipse3D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'c_x')
		i = node.ReadFloat64(i, 'c_y')
		i = node.ReadFloat64(i, 'c_z')
		i = node.ReadFloat64(i, 'a_x')
		i = node.ReadFloat64(i, 'a_y')
		i = node.ReadFloat64(i, 'a_z')
		i = node.ReadFloat64(i, 'b_x')
		i = node.ReadFloat64(i, 'b_y')
		i = node.ReadFloat64(i, 'b_z')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadFloat64(i, 'b')
		i = node.ReadFloat64(i, 'startAngle')
		i = node.ReadFloat64(i, 'sweepAngle')
		return i

	def Read_9E9570C8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_9ED6024F(self, node): # AngularModelDimension
		i = self.ReadContentHeader(node, 'ModelDimensionAngular')
		return i

	def Read_A03874B0(self, node): # ContourFlangeFeature {2390C0D0-A03F-4526-B4B1-7FBFC3C9A66E}
		i = self.ReadHeaderFeature(node, 'FlangeContour')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_A040D1B1(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 5, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		return i

	def Read_A1D74A3C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_A244457B(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'refEntity')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')
		i = node.ReadFloat64(i, 'dirX')
		i = node.ReadFloat64(i, 'dirY')
		i = node.ReadFloat64(i, 'dirZ')
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_A29C84B7(self, node): # SweepTypeEnum {F2AAA202-7B46-45B9-963D-3DAFAB862AF5}
		i = self.ReadHeaderEnum(node, 'SweepType', ['Path', 'PathAndGuideRail', 'PathAndGuideSurface', 'PathAndSectionTwist'])
		return i

	def Read_A2DF48D4(self, node): # Enum
		i = self.ReadHeaderEnum(node, 'A2DF48D4_Enum', [])
		return i

	def Read_A31E29E0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList8(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_A3277869(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'operation') # 8 = Fuse, 0 = Cut
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'edges') #
		i = node.ReadUInt32(i, 'faceIndex')
		return i

	def Read_A37B053C(self, node):
		i = self.ReadHeaderFeature(node, 'PatternSketchDriven')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_10')
		i = node.ReadCrossRef(i, 'ref_11')
		i = node.ReadCrossRef(i, 'ref_12')
		i = node.ReadCrossRef(i, 'ref_13')
		i = node.ReadCrossRef(i, 'ref_14')
		i = node.ReadCrossRef(i, 'ref_15')
		i = node.ReadCrossRef(i, 'ref_16')
		i = node.ReadCrossRef(i, 'ref_17')
		i = node.ReadCrossRef(i, 'ref_18')
		i = node.ReadCrossRef(i, 'ref_19')
		i = node.ReadCrossRef(i, 'ref_20')
		i = node.ReadCrossRef(i, 'ref_21')
		i = node.ReadCrossRef(i, 'ref_22')
		i = node.ReadCrossRef(i, 'ref_23')
		i = node.ReadCrossRef(i, 'ref_24')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'coords', 3)

		return i

	def Read_A3B0404C(self, node): # FeatureApproximationTypeEnum {C08F2078-986C-4043-A70B-643FA906968B}
		i = self.ReadHeaderEnum(node, 'FeatureApproximationType', ['No', 'NeverTooThin', 'NeverTooThick', 'Mean'])
		return i

	def Read_A4087E1F(self, node):
		i = self.ReadChildHeader1(node, 'TappedHole')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadLen32Text16(i, 'txt2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadLen32Text16(i, 'txt3')
		i = node.ReadLen32Text16(i, 'txt4')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i, 'txt5')
		i = node.ReadLen32Text16(i, 'txt6')
		i = node.ReadLen32Text16(i, 'txt7')
		i = node.ReadLen32Text16(i, 'txt8')
		i = node.ReadLen32Text16(i, 'txt9')
		i = node.ReadLen32Text16(i, 'txtA')
		i = node.ReadLen32Text16(i, 'txtB')
		i = node.ReadLen32Text16(i, 'txtC')
		i = node.ReadLen32Text16(i, 'txtD')
		return i

	def Read_A477243B(self, node):
		i = self.ReadCntHdr2SChild(node, None, 'refWrapper')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_FC203F47(self, node):
		i = self.Read_A477243B(node)
		return i

	def Read_A5410F0A(self, node):
		i = self.ReadChildHeader1(node)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_A5428F7A(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_A5977BAA(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'refEntity')
		i = node.ReadUInt32(i, 'cnt1')
		cnt = node.get('cnt1')
		lst = []
		sep = ''
		node.content += ' lst0=['
		for j in range(cnt):
			u16, i  = getUInt16(node.data, i)
			typ, i = getUInt32(node.data, i)
			if (typ == 0x17):
				a, i = getFloat64A(node.data, i, 6)
				lst.append([typ, u16, a])
				node.content += '%s(%d,%s)' %(sep, u16, FloatArr2Str(a))
			elif (typ == 0x2A):
				a1, i = getUInt32A(node.data, i, 3)
				f1, i = getFloat64(node.data, i)
				c1, i = getUInt32A(node.data, i, 3)
				l1, i = getFloat64A(node.data, i, c1[0])
				c2, i = getUInt32A(node.data, i, 3)
				l2 = []
				c3, i = getUInt32A(node.data, i, 3)
				for k in range(c3[0]):
					a, i = getFloat64_3D(node.data, i)
					l2.append(a)
				f2, i = getFloat64(node.data, i)
				a2, i = getUInt32A(node.data, i, 2)
				a3, i = getFloat64_2D(node.data, i)
				lst.append([typ, u16, a1, f1, c1, l1, c2, l2, c3, f2, a2, a3])
				node.content += '%s(%d,%s,%g)' %(sep, u16, IntArr2Str(a1, 2), f1)
			else:
				logError(u"    ERROR in Read_%s: Unknown block type %X!", node.typeName, typ)
				return i
			sep = ','
		node.content += ']'
		node.set('lst0', lst)
		i = node.ReadFloat64(i, 'dirX')
		i = node.ReadFloat64(i, 'dirY')
		i = node.ReadFloat64(i, 'dirZ')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_A6118E11(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refPlane')
		i = self.skipBlockSize(i)
		return i

	def Read_A644E76A(self, node): # SketchSplineHandle {1236D237-9BAC-4399-8CFB-66CB6B7FD5CA}
		i = self.ReadSketch2DEntityHeader(node, 'SplineHandle2D')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		else:
			i = self.skipBlockSize(i)
			addEmptyLists(node, [0])
		i = node.ReadFloat64A(i, 4, 'a1')
		i = self.skipBlockSize(i)
		return i

	def Read_A7175431(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_A76B22A0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		return i

	def Read_A78639EE(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'ls0', 3)
		i = self.ReadTransformation(node, i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refParameter')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refParameter1')
		i = node.ReadCrossRef(i, 'refParameter2')
		i = node.ReadCrossRef(i, 'refParameter3')
		i = node.ReadCrossRef(i, 'refParameter4')
		i = node.ReadUInt16A(i, 3, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_A789EEB0(self, node):
		i = self.ReadHeaderConstraint2D(node, 'Dimension_RadiusA2D') # Major radius
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'refEllipse')
		return i

	def Read_A917F560(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadUInt16A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_A96B5992(self, node):
		i = self.ReadCntHdr2SRef(node)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadChildRef(i, 'ref_4')
		i = node.ReadChildRef(i, 'ref_5')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_6')
		i = node.ReadChildRef(i, 'ref_7')
		i = node.ReadChildRef(i, 'ref_8')
		i = node.ReadChildRef(i, 'ref_9')
		i = node.ReadChildRef(i, 'ref_A')
		i = node.ReadUInt8A(i, 3, 'a0')
		i = node.ReadChildRef(i, 'ref_B')
		return i

	def Read_A96B5993(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		return i

	def Read_A98906A7(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'arr')
		return i

	def Read_A99F1B26(self, node):
		i = node.Read_Header0()
		return i

	def Read_A9AEB67F(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_3')
		return i

	def Read_A9F6B271(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'cld_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		return i

	def Read_AA805A06(self, node):
		i = self.ReadCntHdr3S(node)
		return i

	def Read_AAD64116(self, node): # FilletConstantRadiusEdgeSet
		i = self.ReadCntHdr3S(node, 'FilletConstantRadiusEdgeSet')
		i = node.ReadCrossRef(i, 'edges')
		i = node.ReadCrossRef(i, 'radius')
		i = node.ReadCrossRef(i, 'allFillets')
		i = node.ReadCrossRef(i, 'continuityG2')
		if (getFileVersion() > 2018): i += 4
		return i

	def Read_ABD292FD(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_ACA8C0A4(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 4, 'a0')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a1')
		return i

	def Read_AD0D42B2(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_AD416CEA(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_AE0E267A(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		if (node.get('u32_1') == 1):
			i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadUInt32(i, 'u32_2')
			i = node.ReadUInt16A(i, 3, 'a0')
		else:
			i = node.ReadUInt32(i, 'u32_2')
			i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_AE101F92(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16A(i,   2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i,   2, 'a1')
		i = self.skipBlockSize(i, 12)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadUInt16A(i,   3, 'a2')
		if (getFileVersion() > 2016):
			i += 1
		else:
			i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 21, 'a3')
		i = node.ReadUInt32A(i,   3, 'a4')
		i = node.ReadFloat64A(i, 20, 'a5')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i,   6, 'a6')
		i = node.ReadFloat64A(i,  4, 'a7')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadFloat64A(i, 21, 'a8')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat64A(i, 45, 'a9')
		return i

	def Read_AE1C96C9(self, node):
		# Not found in PartModel
		i = self.ReadContentHeader(node)
		return i

	def Read_AE5E4082(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadChildRef(i, 'label')
		i = self.skipBlockSize(i)
		return i

	def Read_AF779E6E(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 2, 'u32_0')
		return i

	def Read_AFD4E6A3(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		if (node.get('u32_1') == 1):
			i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadUInt32(i, 'u32_2')
#		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		return i

	def Read_AFD8A8E0(self, node):
		# i = self.ReadEnumValue(node, '')
		i = self.ReadHeadersss2S16s(node)
		return i

	def Read_B045E1CC(self, node): # new in 2019
		i = node.Read_Header0()
		# DD,07,00,80
		# 00,02,10,00
		# 03,00,00,80
		# CE,06,00,00,00,00,00,00,01,05
		# 0B,00,00,80
		# 02,00,00,00,00,00,00,00,02,00,00,00
		# 08,00,00,30,01,00,00,00,00,00,00,00,5C,00,00,00
		# 08,00,00,30,00,00,00,00
		# 00
		# 16,04,00,80
		# 04,00,00,80
		# 0B,00,00,00
		# 02,00,00,00
		# 04,00,00,80
		# E1,8F,00,00
		# 04,00,00,80
		# AA,81,00,00
		# 00
		return i

	def Read_B0B886C5(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_B10D8B80(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_B1CF069E(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadChildRef(i, 'ref_4')
		i = node.ReadChildRef(i, 'ref_5')
		i = node.ReadChildRef(i, 'ref_6')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64(i, 'x')
		return i

	def Read_B1DFB58A(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_5')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadFloat64A(i, 6, 'a1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadUInt16A(i, 2, 'a2')
		i = node.ReadFloat64A(i, 6, 'a3')
		return i

	def Read_B1ED010F(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadUInt32A(i, 6, 'a0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadRefU32List(node, i, 'lst0')
		return i

	def Read_B269ACEF(self, node):
		i = self.ReadChildHeader1(node, 'TaperTappedHole')
		i = node.ReadLen32Text16(i, 'size')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadUInt32A(i, 5, 'a0')
		i = node.ReadLen32Text16(i, 'txt2')
		i = node.ReadLen32Text16(i, 'txt3')
		i = node.ReadLen32Text16(i, 'txt4')
		i = node.ReadLen32Text16(i, 'txt5')
		i = node.ReadLen32Text16(i, 'txt6')
		i = node.ReadLen32Text16(i, 'txt7')
		i = node.ReadLen32Text16(i, 'txt8')
		i = node.ReadLen32Text16(i, 'txt9')
		i = node.ReadLen32Text16(i, 'txt10')
		i = node.ReadLen32Text16(i, 'txt11')
		i = node.ReadLen32Text16(i, 'txt12')
		i = node.ReadLen32Text16(i, 'txt13')
		i = node.ReadLen32Text16(i, 'txt14')
		i = node.ReadLen32Text16(i, 'txt15')
		i = node.ReadLen32Text16(i, 'txt16')
		i = node.ReadLen32Text16(i, 'txt17')
		i = node.ReadLen32Text16(i, 'txt18')
		i = node.ReadLen32Text16(i, 'txt19')
		return i

	def Read_B292F94A(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_B310B8E5(self, node): # HemFeature {D9AB7AE5-6A67-4165-9E0B-0F008C9135B0}
		i = self.ReadCntHdr2SRef(node, 'FxHem')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_A')
		i = node.ReadUInt8A(i, 3, 'a0')
		i = node.ReadCrossRef(i, 'ref_B')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_B382A87C(self, node):
		i = self.ReadCntHdr3S(node, 'ProfileSelection')
		i = node.ReadCrossRef(i, 'refFace')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'number') # The numbber of the selection
		return i

	def Read_B3A169E4(self, node): # ShellDirectionEnum {796E2726-2926-48C7-802A-5CAF83C3078D}
		i = self.ReadHeaderEnum(node, 'ShellDirection', ['Inside', 'Outside', 'BothSides'])
		return i

	def Read_B3EAA9EC(self, node): # new in 2019
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadFloat64(i, 'f64_1')
		return i

	def Read_B3EAA9EE(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadFloat64(i, 'f64_1')
		return i

	def Read_B4124F0C(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_B447E0DC(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadFloat64_2D(i, 'a2')
		if (getFileVersion() > 2010):
			#i = node.ReadFloat64A(i, 9, 'a3')
			i += 9*8
		else:
			i += 4
		return i

	def Read_B4964E90(self, node):
		i = self.ReadHeaderConstraint2D(node, 'Dimension_RadiusB2D') # MinorRadius
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'refEllipse')
		return i

	def Read_B58135C4(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_B59F6734(self, node):
		i = self.ReadChildHeader1(node)
		i = node.ReadUInt16A(i, 5, 'a0')
		return i

	def Read_B5D4DEE6(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = self.ReadRefList(node, i, 'lst2')
		i = node.ReadCrossRef(i, 'refCenter')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'refAngle')
		i = node.ReadCrossRef(i, 'refPolygonCenter')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'refCount')
		i = node.ReadFloat64(i, 'angle')
		return i

	def Read_B5DFF07E(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadUUID(i, 'uid_0')
		return i

	def Read_B6482AF8(self, node):
		i = self.ReadChildHeader1(node, ref1Name = 'refFX')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'lst0')
		return i

	def Read_B690EF36(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_B6A36C30(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		lst = []
		sep = ''
		node.content += ' lst0=['
		for j in range(cnt):
			u32, i = getUInt32(node.data, i)
			u8, i  = getUInt8(node.data, i)
			node.content += '%s[%04X,%02X,' %(sep, u32, u8)
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'tmp')
			lst.append([u32, u8, node.get('tmp')])
			sep = ','
			node.content += ']'
		node.delete('tmp')
		node.content += ']'
		node.set('lst0', lst)
		return i

	def Read_B6C5116B(self, node):
		i = self.ReadChildHeader1(node)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_B71CBEC9(self, node): # HelicalConstraint3D {33E293A8-9DD6-4B9A-8274-E436A3BB3876}
		i = self.ReadContentHeader(node, 'Geometric_Helical3D')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refSketch')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst2')
		else:
			addEmptyLists(node, [1, 2])
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() < 2019):
			i = node.ReadCrossRef(i, 'refParameter0')
			i = node.ReadCrossRef(i, 'refParameter1')
			i = node.ReadCrossRef(i, 'refParameter2')
			i = node.ReadCrossRef(i, 'refParameter3')
			i = node.ReadCrossRef(i, 'refParameter4')
		i = node.ReadUInt16A(i, 7, 'a0')
		if (getFileVersion() > 2018):
			i += 4
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst3')
		i = node.ReadChildRef(i, 'refParameter5')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_B799E9B2(self, node): # FilletVariableRadiusEdgeSet
		i = self.ReadContentHeader(node, 'FilletVariableRadiusEdgeSet')
		if (getFileVersion() > 2017): i += 4 # skipp 0xFFFFFFFF (-1)
		i = node.ReadCrossRef(i, 'edges')
		i = node.ReadCrossRef(i, 'radii')
		i = node.ReadCrossRef(i, 'refValue')
		return i

	def Read_B835A483(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_B884A1E1(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_B8CB3560(self, node): # ModelAnnotations
		i = self.ReadContentHeader(node, 'ModelAnnotations')
		i = node.ReadSInt32(i, 's32_0')
		return i

	def Read_B8DBEF70(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_B8E19017(self, node): # SplitToolTypeEnum {F7304638-1AF5-4E5D-8704-D9DE52F1A8B4}
		i = self.ReadHeaderEnum(node, 'SplitToolType', ['Path', 'WorkPlane', 'WorkSurface', 'SurfaceBody'])
		return i

	def Read_B8E19019(self, node): # SplitTypeEnum {E23EA9A1-7B9F-465F-A902-542F8E8A49EE}
		i = self.ReadHeaderEnum(node, 'SplitType', ['SplitPart', 'SplitFaces', 'SplitBody' , 'TrimSolid'])
		return i

	def Read_B91FCE52(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		return i

	def Read_BA6E3112(self, node): # FilletVariableRadiusEdges
		i = self.ReadCntHdr3S(node, 'FilletVariableRadiusEdges')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'intermediateRadii')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_BB1DD5DF(self, node): # RDxVar
		i = self.ReadCntHdr3S(node, 'Parameter')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'valueNominal')
		i = node.ReadUInt32(i, 'valueModel')
		return i

	def Read_BB2150BF(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refParameter')
		return i

	def Read_BCBBAD85(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_BCDCC62C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_BDE13180(self, node):
		i = node.Read_Header0()
		return i

	def Read_BE175765(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.ReadU32XRefList(node, i, 'lst0')
		return i

	def Read_BE175768(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # ???
		cnt, i = getUInt32(node.data, i)
		lst = []
		node.content += u" txt=["
		sep = u""
		for j in range(cnt):
			txt, i = getLen32Text16(node.data, i)
			node.content += u"%s\'%s\'" %(sep, txt)
			sep = u","
			lst.append(txt)
		node.content += u"]"
		return i

	def Read_BE8CEB3C(self, node): # RadiusModelDimension
		i = self.ReadContentHeader(node, 'ModelDimensionRadius')
		return i

	def Read_BEE5961F(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4 # skip FF FF FF FF
		return i

	def Read_BF32E0A6(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadUInt32(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadU32U32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = self.ReadU32U32List(node, i, 'lst3')
		return i

	def Read_BF3B5C84(self, node): # ThreePointAngleDimConstraint {C173A07D-012F-11D5-8DEA-0010B541CAA8}:
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Angle3Point2D')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')
		i = node.ReadCrossRef(i, 'refPoint3')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_BF8B8868(self, node):
		i = self.ReadCntHdr3S(node, 'FacesOffset')
		i = node.ReadCrossRef(i, 'refFaces')
		i = node.ReadCrossRef(i, 'refOffset')
		return i

	def Read_BFB5EB93(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		if (getFileVersion() < 2013):
			i = node.ReadUInt8A(i, 2, 'a0')
		else:
			i = node.ReadChildRef(i, 'ref_1')
			i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_BFBAAFA8(self, node):
		i = self.ReadCntHdr2SRef(node)
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_BFD09C43(self, node):
		i = self.ReadChildHeader1(node, ref2Name='label')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadFloat64A(i, 4, 'a1')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_BFED36A9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64A(i, 9, 'a1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		return i

	def Read_C098D3CF(self, node): # PunchToolFeature {0DC3C610-F23D-44AD-B688-A47CAB5B04CB}
		i = self.ReadHeaderFeature(node, 'PunchTool')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_C1887310(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		if (len(node.get('lst0')) > 0):
			i = node.ReadSInt32(i, 's32_0')
		return i

	def Read_C1A45D98(self, node):
		i = self.ReadSketch3DEntityHeader(node, 'SplineHandle3D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 6, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_C2D0676B(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_C2EF1CC7(self, node):
		i = self.ReadHeaderFeature(node, 'NonParametricBase')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_C3DDDC08(self, node): # FlangeFeature {5475DDC1-3397-46D6-A7A3-E1C34FA5BD7E}
		i = self.ReadHeaderFeature(node, 'Flange')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_C428DB42(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_C4C14B90(self, node): # FaceFeature {600E3CEE-1600-4999-ACE4-7CED6483BECE}
		i = self.ReadHeaderFeature(node, 'Face')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		return i

	def Read_C5538931(self, node): # CoincidentConstraint3D {843FEEB5-A0EF-4C5B-8939-4F9B574119D8}
		i = self.ReadConstraintHeader3D(node, 'Geometric_Coincident3D')
		if (getFileVersion() > 2016):
			i += 4
		return i

	def Read_C681C2E0(self, node): # EqualLengthConstraint {8006A07E-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_EqualLength2D')
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		return i

	def Read_C6E21E1A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_C7A06AC2(self, node): # PartFeatureExtentDirectionEnum {D56C4513-7B52-4020-8FFB-E531EF8C69BF}
		i = self.ReadHeaderEnum(node, 'PartFeatureExtentDirection', ['Positive', 'Negative', 'Symmetric'])
		return i

	def Read_C89EF3C0(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64_2D(i, 'a1')
		return i

	def Read_CA02411F(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i, 8)
		if (node.get('label') is None):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		else:
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		return i

	def Read_CA674C90(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = self.ReadRefU32List(node, i, 'lst2')
		return i

	def Read_CA70D2C6(self, node):
		i = self.ReadHeaderEnum(node, 'CA70D2C6_Enum', [])
		return i

	def Read_CA7AA850(self, node): # FxFilletVariable
		i = self.ReadCntHdr3S(node, 'FxFilletVariable')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'radiusEdgeSets')
		return i

	def Read_CADC79F0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_CADD6468(self, node):
		i = node.Read_Header0()
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt0')
		return i

	def Read_CAB7E237(self, node): # General Surface Profile Tolerance
		i = self.ReadContentHeader(node, 'GenSurfProfTol')
		if (getFileVersion() > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadCrossRef(i, 'refAnnoDim')
		i = node.ReadCrossRef(i, 'refPlane')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref2')
		i = node.ReadCrossRef(i, 'ref3')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_ , 'lst1') # 02 00 00 30 00 00 00 00
		i = node.ReadUInt32(i, 'u32_4' ) # 00 00 00 00
		i = node.ReadFloat64A(i, 9, 'a1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst2')
		return i

	def Read_CAFE99DF(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_CB072B3B(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadFloat64A(i, 11, 'a1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		if (getFileVersion() > 2014):
			i += 8*8
		return i

	def Read_CB370222(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_CB6C0A56(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_CB71CED6(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_CC0F7521(self, node): # AcisEntityWrapper
		i = node.Read_Header0('AcisEntityWrapper')
		i = node.ReadUInt32(i, 'index')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refAsm')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'lenFooter')
		return i

	def Read_CC90BCDA(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadList2(i, importerSegNode._TYP_LIST_SINT16_A_, 'lst0', 2)
		return i

	def Read_CCC5085A(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = self.ReadRefU32AList(node, i, 'lst0', 2, importerSegNode.SecNodeRef.TYPE_CHILD)
		i = self.ReadRefU32ARefU32List(node, i, 'lst1', 2)
		i = self.ReadRefU32ARefU32List(node, i, 'lst2', 1)
		cnt, i = getUInt32(node.data, i)
		sep = ''
		node.content += ' lst3=['
		lst = []
		# remember node content as it will be overwritten by ReadList2!
		c = node.content
		for j in range(cnt):
			u32_0, i = getUInt32(node.data, i)
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'tmp', 2)
			lst0 = node.get('tmp')
			u32_1, i = getUInt32(node.data, i)
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'tmp', 2) # this is ref + uint!
			lst1 = node.get('tmp')
			c += '%s[%04X,%s,%04X,%s]' %(sep, u32_0, Int2DArr2Str(lst0, 4), u32_1, Int2DArr2Str(lst1, 4))
			lst.append([u32_0, lst0, u32_1, lst1])
			sep = ','
		node.content = c +']'
		node.set('lst3', lst)
		node.delete('tmp')
		return i

	def Read_CCCB9A78(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_5')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadChildRef(i, 'ref_6')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_CCD87CBA(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4 # skipp FF FF FF FF
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadFloat64(i, 'f64_1')
		return i

	def Read_CCE264C4(self, node):
		i = node.Read_Header0()
		return i

	def Read_CCE92042(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'lastIdx')
		cnt, i = getUInt32(node.data, i)
		lst = {}
		for j in range(cnt):
			key, i = getUInt32(node.data, i)
			val, i = self.ReadNodeRef(node, i, key, importerSegNode.SecNodeRef.TYPE_CHILD,)
			lst[key] = val
		node.content += ' lst={%s}' %(len(lst))
		node.set('lst', lst)
		return i

	def Read_CD1423D9(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadList2(i, importerSegNode._TYP_STRING16_, 'lst1')
		return i

	def Read_CD7C1C53(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_CDF78EC0(self, node):
		i = self.ReadCntHdr2SRef(node)
		i = node.ReadFloat64(i, 'f64_0')
		return i

	def Read_CE4A0723(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8(i, 'u8')
		i = node.ReadUInt32A(i, 3, 'a1')
		#cnt*{u8 f64 u16 u16}
		cnt, i = getUInt32(node.data, i)
		lst = []
		for j in range(cnt):
			u1 , i = getUInt8(node.data, i)
			f64, i = getFloat64(node.data, i)
			u2 , i = getUInt16(node.data, i)
			u3 , i = getUInt16(node.data, i)
			lst.append([u1, f64, u2, u3])
		node.content += ' lst1=[%s]' %(','.join(['(%02X,%g,%03X,%03X)' %(r[0], r[1], r[2], r[3]) for r in lst]))
		node.set('lst1', lst)
		return i

	def Read_CE52DF35(self, node): # SketchPoint {8006A022-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadSketch2DEntityHeader(node, 'Point2D')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'endPointOf')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'centerOf')
		if (getFileVersion() > 2012):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		else:
			node.content += ' u32_0=000000 lst2={}'
			node.set('u32_0', 0)
			node.set('lst2', [])
		endPointOf = node.get('endPointOf')
		centerOf   = node.get('centerOf')
		entities   = []
		entities.extend(endPointOf)
		entities.extend(centerOf)
		node.set('entities', entities)
		return i

	def Read_CE52DF3A(self, node): # SketchLine {8006A016-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadSketch2DEntityHeader(node, 'Line2D')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		else:
			addEmptyLists(node, [0])
		# RootPoint
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		# Direction
		i = node.ReadFloat64(i, 'dirX')
		i = node.ReadFloat64(i, 'dirY')

		return i

	def Read_CE52DF3B(self, node): # SketchCircle {8006A04C-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadSketch2DEntityHeader(node, 'Circle2D')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		else:
			addEmptyLists(node, [1])
		i = node.ReadCrossRef(i, 'refCenter')
		i = node.ReadFloat64(i, 'r')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_CE52DF3E(self, node): # SketchPoint3D {2307500B-D075-4F5D-815D-7A1B8E90B20C}
		i = self.ReadSketch3DEntityHeader(node, 'Point3D')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'endPointOf')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'centerOf')
		endPointOf = node.get('endPointOf')
		centerOf   = node.get('centerOf')
		entities   = []
		entities.extend(endPointOf)
		entities.extend(centerOf)
		node.set('entities', entities)
		return i

	def Read_CE52DF40(self, node): # Direction
		i = self.ReadHeadersss2S16s(node, 'Direction')
		i = node.ReadFloat64(i, 'a')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2017):
			i += 4
		i = node.ReadFloat64(i, 'dirX')
		i = node.ReadFloat64(i, 'dirY')
		i = node.ReadFloat64(i, 'dirZ')
		return i

	def Read_CE52DF42(self, node): # Plane
		i = self.ReadHeadersss2S16s(node, 'Plane')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2017):
			i += 4
		i = node.ReadUInt32(i, 'u32_1')
		if (node.get('u32_1') > 1):
			i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat64(i, 'b_x')
		i = node.ReadFloat64(i, 'b_y')
		i = node.ReadFloat64(i, 'b_z')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat64(i, 'n_x')
		i = node.ReadFloat64(i, 'n_y')
		i = node.ReadFloat64(i, 'n_z')
		return i

	def Read_CE59B7F5(self, node):
		# i = self.ReadEnumValue(node, '', ['']) # 60452313.properties[17h]
		i = self.ReadHeadersss2S16s(node) # 60452313.properties[17h]
		return i

	def Read_CE7F937A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refLine')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'refPlane')
		return i

	def Read_CEFD3973(self, node):
		i = self.ReadHeaderEnum(node, 'CEFD3973_Enum', [])
		return i

	def Read_CFB519C2(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_CFB519D1(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_D01E2BB0(self, node):
		i = self.ReadCntHdr2SRef(node)
		return i

	def Read_D13107FE(self, node): # CollinearConstraint3D {E8BE2118-716C-40FD-8BC0-2517B253E4F9}
		i = self.ReadConstraintHeader3D(node, 'Geometric_Collinear3D')
		return i

	def Read_D2D440C0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'refDocument')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')

		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadFloat64A(i, node.get('a0')[1], 'a1')
		i = node.ReadFloat64(i, 'f64_0')

		i = node.ReadUInt32A(i, 3, 'a2')
		i = node.ReadFloat64A(i, node.get('a2')[1], 'a3')
		i = node.ReadFloat64(i, 'f64_2')

		i = node.ReadUInt32A(i, 4, 'a4')
		i = self.ReadFloat64A(node, i, node.get('a4')[1], 'a5', 3)
		i = node.ReadFloat64(i, 'f64_4')

		i = node.ReadUInt32A(i, 2, 'a6')
		i = self.ReadFloat64A(node, i, node.get('a6')[1], 'a7', 2)
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')

		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_D2DA2CF0(self, node):
		i = self.ReadCntHdr3S(node)
		return i

	def Read_D2DB6A4F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		return i

	def Read_D30E5235(self, node):
		i = self.ReadCntHdr2SRef(node)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_D3F71C7A(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_D4A52F3A(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt8A(i, 2, 'a2')
		return i

	def Read_D4CCA953(self, node):
		i = self.ReadHeaderEnum(node, 'D4CCA953_Enum', [])
		return i

	def Read_D524C30A(self, node):
		i = self.ReadCntHdr3S(node, 'FilletFullRoundSet')
		i = node.ReadCrossRef(i, 'facesSide1')
		i = node.ReadCrossRef(i, 'facesCenter')
		i = node.ReadCrossRef(i, 'facesSide2')
		return i

	def Read_D589D818(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_0')

		return i

	def Read_D5DAAA83(self, node): # SurfaceBodies {5DF860AE-6B16-11D3-B794-0060B0F159EF}
		i = self.ReadContentHeader(node, 'SurfaceBodies')
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'bodies')
		return i

	def Read_D5F19E40(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'dirX')
		i = node.ReadFloat64(i, 'dirY')
		return i

	def Read_D5F19E41(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64_3D(i, 'a0')
		return i

	def Read_D5F19E42(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64A(i, 6, 'a0')
		return i

	def Read_D5F9E1E0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		return i

	def Read_D61732C1(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'parts')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		if (getFileVersion()> 2011):
			i = node.ReadCrossRef(i, 'refSketch')
		else:
			node.content += ' refSketch=None'
		i = node.ReadCrossRef(i, 'refPatch1')
		i = node.ReadCrossRef(i, 'refPatch2')
		i = node.ReadCrossRef(i, 'refParameter1')
		i = node.ReadCrossRef(i, 'refBody')
		i = node.ReadCrossRef(i, 'refParameter2')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'refParameter3')
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadCrossRef(i, 'refParameter4')
		i = node.ReadCrossRef(i, 'refParameter5')
		i = node.ReadCrossRef(i, 'refParameter6')
		return i

	def Read_D70E9DDA(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_D739EDBB(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_D776DFD1(self, node):
		# i = self.ReadEnumValue(node, '') # 60452313.properties[12h]
		i = self.ReadHeadersss2S16s(node) # 60452313.properties[12h]
		return i

	def Read_D77CC069(self, node):
		i = node.Read_Header0()
		return i

	def Read_D77CC06A(self, node):
		i = node.Read_Header0()
		return i

	def Read_D77CC06B(self, node):
		i = node.Read_Header0()
		return i

	def Read_D797B7B9(self, node):
		i = node.Read_Header0()
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadLen32Text16(i)
		i = node.ReadFloat64A(i, 5, 'a0')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadUInt32A(i, 4, 'a2')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadLen32Text16(i, 'txt2')
		i = node.ReadUInt32A(i, 11, 'a3')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_D7BE5663(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_D7F4C16F(self, node):
		i = self.ReadChildHeader1(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt16A(i, 5, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_D80CE357(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = self.ReadRefU32List(node, i, 'lst2')
		return i

	def Read_D83EF271(self, node):
		i = self.ReadContentHeader(node, 'FeatureDimensions')
		i = self.skipBlockSize(i, 8)
		if (getFileVersion() > 2018): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_D8A9C970(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_D92A619C(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_D938B973(self, node): # new in 2019
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadList2(i, importerSegNode._TYP_LIST_SINT32_A_, 'lst0', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64A(i, 11, 'a1')
		return i

	def Read_D94F1914(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_D95B951A(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt16(i, 'decimalsLength')
		i = node.ReadUInt16(i, 'decimalsAngle')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_D9F7441B(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # ???
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'features')
		return i

	def Read_DA2C89C5(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2016):
			i += 4
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_DA4970B5(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst')
		i = node.ReadCrossRef(i,'refProfileSelection')
		i = self.skipBlockSize(i)
		return i

	def Read_DB04EB11(self, node): # Group3D
		i = self.ReadHeadersS32ss(node, 'Group3D')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 12)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		if (getFileVersion() > 2016):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		else:
			addEmptyLists(node, [1])
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst2')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_DBDD00E3(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'numEntities')
		i = node.ReadCrossRef(i, 'refSketch')
		cnt, i = getUInt32(node.data, i)
		lst = []
		for j in range(cnt):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CHILD)
			a, i = getUInt32A(node.data, i, 3)
			lst.append([ref, a])
		node.content += ' lst0={%s}' %(','.join(['[%s,%s]' %(r[0], IntArr2Str(r[1],4)) for r in lst]))
		node.set('lst0', lst)
		return i

	def Read_DC93DB08(self, node):
		# TODO: constraint together with Geometric_TextBox2D and 8FEC335F <-> Hairdryer: Sketch47, Sketch48, Speedometer: Sketch3, Sketch10
		i = self.ReadCntHdr2SRef(node, 'Image2D', 'refSketch')
		i = node.ReadFloat64A(i, 4, 'a0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.ReadTransformation(node, i)
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_DD64FF02(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a1')
		return i

	def Read_DD7D4B84(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4
		i = node.ReadCrossRef(i, 'plane')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_DD80AC37(self, node): # something to do with text-alignment
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'faces')
		i = node.ReadCrossRef(i, 'refEdge')
		i = node.ReadCrossRef(i, 'refString')
		return i

	def Read_DDCF0E1C(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32A(i, 26, 'a0')
		i = node.ReadFloat64A(i, 7, 'a1')
		return i

	def Read_DE172BCF(self, node): # ModelToleranceFeature {CEBC9A45-2058-4537-9D52-5E11419267DE}
		i = self.ReadContentHeader(node, 'ModelToleranceFeature')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'faces')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'clientId')
		i = node.ReadCrossRef(i, 'refParentToleranceFeature')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2018): i += 4 # skip 02 00 00 00
		return i

	def Read_DE818CC0(self, node): # BendConstraint3D {AE27E3D2-63C8-4D39-B2CA-A6387AE5D7B3}
		i = self.ReadConstraintHeader3D(node, 'Geometric_Bend3D')
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_DE9C63BD(self, node): # new in 2019
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_DEB6F91B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_DEBD4124(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_DED39DA8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst1')
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2015):
			i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_DF3B2C5B(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_DFB2586A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1a')
		i = node.ReadCrossRef(i, 'ref_1b')
		i = node.ReadCrossRef(i, 'ref_1c')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_2a')
		i = node.ReadCrossRef(i, 'ref_2b')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadCrossRef(i, 'ref_4')
		cnt, i = getUInt32(node.data, i)
		lst0 = []
		for j in range(cnt):
			r1, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CHILD)
			r2, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			lst0.append([r1, r2])
		return i
		node.content += ' lst0=[%s]' %(','.join(['[%s,%s]' %(r[0], r[1]) for r in lst0]))
		node.set('lst0', lst0)

	def Read_E047663E(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_E0E3E202(self, node): # LoftTypeEnum {B6B5F55A-D2A1-4B96-A022-830865255CBF}
		i = self.ReadHeaderEnum(node, 'LoftType', ['Rails', 'Centerline', 'AreaLoft', 'RegularLoft'])
		return i

	def Read_E0EA12F2(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_E1108C00(self, node): # ConcentricConstraint {8006A078-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Radius2D')
		i = node.ReadCrossRef(i, 'refObject')
		i = node.ReadCrossRef(i, 'refCenter')
		return i

	def Read_E192FA73(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'parameters')
		return i

	def Read_E1D3D023(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadFloat32_3D(i, 'a1')
		i = node.ReadUInt16A(i, 3, 'a2')
		if (getFileVersion() > 2016):
			i += 1
		else:
			i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'a3')
		i = node.ReadFloat64_3D(i, 'a4')
		i = node.ReadSInt32A(i, 2, 'a5')
		i = node.ReadFloat64A(i, 31, 'a6')
		i = node.ReadUInt8A(i, 18, 'a7')
		i = node.ReadFloat64A(i, 6, 'a8')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64A(i, 19, 'a9')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadFloat64A(i, 12, 'a10')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadFloat64A(i, 6, 'a11')
		if (getFileVersion() > 2010):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_E1D8C31B(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		return i

	def Read_E273976D(self, node):
		i = node.Read_Header0()
		return i

	def Read_E28A0597(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_E28D3B3F(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 3, 'a0')
		return i

	def Read_E2CCC3B7(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'f64_1')
		return i

	def Read_E2D83380(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadParentRef(i)
		i = node.ReadUInt8(i, 'u8_8')
		return i

	def Read_E524B878(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_E558F428(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_E562B07C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refPlane1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPlane2')
		i = node.ReadCrossRef(i, 'refValue')
		return i

	def Read_E5721705(self, node):
		i = self.ReadCntHdr2SRef(node)
		if (node.get('ref_1')):
			i = node.ReadChildRef(i, 'ref_2')
			i = node.ReadCrossRef(i, 'ref_3')
			i = node.ReadChildRef(i, 'ref_4')
			i = node.ReadCrossRef(i, 'ref_5')
			i = node.ReadChildRef(i, 'ref_6')
			i = node.ReadCrossRef(i, 'ref_7')
			i = node.ReadChildRef(i, 'ref_8')
			i = node.ReadCrossRef(i, 'ref_9')
		return i

	def Read_E6158074(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid')
		return i

	def Read_E70272F7(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_E70647C2(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64A(i, 12, 'a2')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32A(i, 2, 'a2')
		i = node.ReadUInt16A(i, 4, 'a3')
		i = node.ReadFloat64_3D(i, 'a4')
		return i

	def Read_E70647C3(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64A(i, 15, 'a2')
		return i

	def Read_E70647C4(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadUInt32A(i, 5, 'a0')
		i = node.ReadFloat64_3D(i, 'm0')
		i = node.ReadFloat64_3D(i, 'm1')
		i = node.ReadFloat64_3D(i, 'm2')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')
		i = node.ReadFloat64(i, 'angleStart')
		i = node.ReadFloat64(i, 'angleSweep')
		return i

	def Read_E75FF898(self, node):
		i = node.Read_Header0()
		return i

	def Read_E8D30910(self, node): # SmoothConstraint3D  {281176E3-4EDC-4F4E-9804-6716B7B9059D}
		i = self.ReadConstraintHeader3D(node, 'Geometric_Smooth3D')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_E9132E94(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32A(i, 4, 'a1')
		return i

	def Read_E94FB6D9(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refTransformation1')
		i = node.ReadCrossRef(i, 'refTransformation2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refTransformation3')
		return i

	def Read_E9821C66(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_EA680672(self, node): #
		i = self.ReadHeadersss2S16s(node)
		return i

	def Read_EAA82E7B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		if (getFileVersion() > 2015):
			i = node.ReadCrossRef(i, 'ref_A')
		return i

	def Read_EAC2875A(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64(i, 'f1')
		i = node.ReadUInt16A(i, 3, 'a0')
		if (getFileVersion() > 2016):
			i += 1
		else:
			i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 26, 'a1')
		i = node.ReadUInt16A(i, 3, 'a2')
		i = node.ReadFloat64A(i, 6, 'a3')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64A(i, 13, 'a4')
		if (getFileVersion() > 2012):
			i += 3*8 # same as a4[-3:]
		return i

	def Read_EB9E49B0(self, node):
		i = self.ReadCntHdr1SRef(node)
		return i

	def Read_EBA98FD3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_EBB23D6E(self, node): # SystemOfMeasureEnum {50131E62-D297-11D3-B7A0-0060B0F159EF}:
		i = self.ReadHeaderEnum(node, 'EBB23D6E_Enum', [])
		return i

	def Read_EC2D4C66(self, node): # MeshFolder
		i = self.ReadHeadersS32ss(node, 'MeshFolder')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_EC7B8A2B(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadCrossRef(i, 'ref0')
		i = node.ReadCrossRef(i, 'ref1')
		i = node.ReadCrossRef(i, 'refPoint')
		return i

	def Read_ED3175C6(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'refFX')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_5')
		i = node.ReadLen32Text16(i)
		return i

	def Read_ED7D8445(self, node):
		i = self.ReadChildHeader1(node)
		i = node.ReadCrossRef(i, 'refOwnedBy')
		return i

	def Read_EDAEAC7B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_3')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')

		return i

	def Read_EE09D055(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_EE311CA5(self, node): # new in 2019
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst1')
		return i

	def Read_EE558505(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		return i

	def Read_EE558506(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		return i

	def Read_EE558507(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_A')
		return i

	def Read_EE558508(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refParameter1')
		i = node.ReadCrossRef(i, 'refDirection')
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'refParameter2')
		i = node.ReadCrossRef(i, 'refParameter3')
		return i

	def Read_EE767654(self, node):
		i = self.ReadHeaderEnum(node, 'SculptSurfaceExtentDirection', ['Positive', 'Negative', 'Symmetric'])
		return i

	def Read_EE792053(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i, 8)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_EEE03AF5(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refEntity1')
		i = node.ReadCrossRef(i, 'refEntity2')
		#i = node.ReadUInt32A(i, 4, 'a2')
		#i = node.ReadUInt32(i, 'u32_0')
		#i = self.skipBlockSize(i)
		#if (getFileVersion() > 2010):
		#	i = node.ReadFloat64A(i, 8, 'a3')
		return i

	def Read_EEF10748(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_EF8279FB(self, node): # FaceMoveTypeEnum
		i = self.ReadHeaderEnum(node, 'FaceMoveType', ['DirectionAndDistance', 'Planar', 'Free'])
		return i

	def Read_EFE47BB4(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_EFF2257A(self, node):
		i = self.ReadCntHdr3S(node, 'SurfaceSelection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_F0677096(self, node):
		i = self.ReadHeadersS32ss(node)
		return i

	def Read_F0F5EB21(self, node): # new in 2019
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_F10C26A4(self, node):
		i = node.Read_Header0()
		return i

	def Read_F145279A(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion()> 2018): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_F2568DCF(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst1')
		else:
			addEmptyMaps(node, [0, 1])
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		return i

	def Read_F27502FD(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_F338E84B(self, node):
		i = self.ReadCntHdr3S(node, 'PathAndSectionTwist')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'coords', 3)
		return i

	def Read_F3DBA9D8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_F3F435A1(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_F3FC69C6(self, node): # SurfaceCreator
		i = node.Read_Header0('SurfaceCreator')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadUInt16(i, 'idxCreator')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_F4360D18(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadUInt32A(i, 2, 'val_key_1')
		i = node.ReadUInt32A(i, 2, 'val_key_2')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadU32U32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = node.ReadUInt32A(i, 2, 'val_key_3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a3')
		return i

	def Read_F4B6001D(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_5')
		i = node.ReadChildRef(i, 'ref_6')
		i = node.ReadChildRef(i, 'ref_7')
		i = node.ReadChildRef(i, 'ref_8')
		return i

	def Read_F4DAD621(self, node):
		i = self.ReadHeaderEnum(node, 'F4DAD621_Enum', [])
		return i

	def Read_F5E51520(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_0a')
		i = node.ReadUInt32(i, 'u32_0b')
		return i

	def Read_F645595C(self, node): # ASM
		i = node.Read_Header0('ASM')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'lenFooter')
		txt, i = getText8(node.data, i, 15)
		index = 0
		clearEntities()
		entities = {}
		lst = []
		e = len(node.data) - node.get('lenFooter') + 0x17

		setVersion(7.0)
		header = Header()
		header.version, i = getUInt32(node.data, i)
		header.records, i = getUInt32(node.data, i)
		header.bodies , i = getUInt32(node.data, i)
		header.flags  , i = getUInt32(node.data, i)
		tag, header.prodId, i   = readNextSabChunk(node.data, i)
		tag, header.prodVers, i = readNextSabChunk(node.data, i)
		tag, header.date, i     = readNextSabChunk(node.data, i)
		tag, header.scale, i    = readNextSabChunk(node.data, i)
		tag, header.resabs, i   = readNextSabChunk(node.data, i)
		tag, header.resnor, i   = readNextSabChunk(node.data, i)
		node.content += "\n%s" %(header)
		header.version = 7.0
		while (i < e):
			entity, i = readEntityBinary(node.data, i, e)
			entity.index = index
			entities[index] = entity
			lst.append(entity)
			convert2Version7(entity)
			index += 1
			if (entity.name in ('End-of-ACIS-data')):
				break
		resolveEntityReferences(entities, lst)
		i = self.skipBlockSize(i)
		node.set('SAT', [header, lst])
		self.segment.AcisList.append(node)
		dumpSat(node)

		return i

	def Read_F67F0488(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'a0')
		return i

	def Read_F7693D55(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadUInt32(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadU32U32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = node.ReadUInt32(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		return i

	def Read_F8371DBE(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFx')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'label')
		i = self.skipBlockSize(i)
		return i

	def Read_F83F79DA(self, node):
		i = self.ReadCntHdr2SRef(node)
		return i

	def Read_F8A779F9(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_F8A77A03(self, node): # ParameterFunction
		i = node.Read_Header0('ParameterFunction')
		i = node.ReadChildRef(i, 'refUnit')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'operands')
		i = self.skipBlockSize(i)
		i = node.ReadEnum16(i, 'name', Functions)
		i = node.ReadUInt16(i, 'u16_0')
		ref = node.get('operands')
		if (len(ref) > 0):
			node.set('refOperand', ref[0])
		else:
			node.set('refOperand', None)
		return i

	def Read_F8A77A04(self, node): # ParameterValue
		i = node.Read_Header0('ParameterValue')
		i = node.ReadChildRef(i, 'refUnit')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'value')
		i = node.ReadUInt16(i, 'type')
		if (getFileVersion() > 2010):
			i += 4
		return i

	def Read_F8A77A05(self, node): # ParameterRef
		i = node.Read_Header0('ParameterRef')
		i = node.ReadChildRef(i, 'refUnit')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refParameter')
		return i

	def Read_F8A77A0C(self, node): # ParameterUnaryMinus
		i = node.Read_Header0('ParameterUnaryMinus')
		i = node.ReadChildRef(i, 'refUnit')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refValue')
		i = self.skipBlockSize(i)
		return i

	def Read_F8A77A0D(self, node): # ParameterOperationPowerIdent
		node.name = '^'
		i = node.Read_Header0('ParameterOperationPowerIdent')
		i = node.ReadChildRef(i, 'refUnit')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refOperand1')
		i = self.skipBlockSize(i)
		return i

	def Read_F90DC646(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.Read2RefList(node, i, 'lst0', importerSegNode.SecNodeRef.TYPE_CHILD)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst1')
		return i

	def Read_F9372FD4(self, node): # SketchControlPointSpline {D5F8CF99-AF1F-4089-A638-F6889762C1D6}
		i = self.ReadSketch2DEntityHeader(node, 'BSplineCurve2D')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		else:
			addEmptyLists(node, [0])
			i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16A(i, 5, 'a0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt16A(i, 5, 'a1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'ptIdcs')

		i = self.readTypedList(node, i, 'a2',    3, 1, True)  # really 1?
		i = self.readTypedList(node, i, 'a3',    3, 1, False)
		i = self.readTypedList(node, i, 'a4',    3, 1, False) # really 1?
		i = self.readTypedList(node, i, 'poles', 3, 2, True)  # poles
		i = self.readTypedList(node, i, 'a5',    2, 2, False)
		i = self.readTypedList(node, i, 'a6',    3, 1, False) # really 1?

#		i = node.ReadUInt8(i, 'u8_0')
#		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'handles')
#		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'arcs')
#		i = node.ReadUInt8(i, 'u8_1')
#		i = node.ReadFloat64(i, 'f64_6')
#		i = node.ReadUInt32(i, 'u32_6')
#		i = node.ReadUInt8(i, 'u8_2')
#
#		# redundant information of a2..a6:
#		i = self.readTypedList(node, i, 'a7',  3, 1, True)
#		i = self.readTypedList(node, i, 'a8',  3, 1, False)
#		i = self.readTypedList(node, i, 'a9',  3, 1, False)
#		i = self.readTypedList(node, i, 'a10', 3, 2, True)
#		i = self.readTypedList(node, i, 'a11', 2, 2, False)
#		i = self.readTypedList(node, i, 'a12', 3, 2, False)

		return i

	def Read_F94FF0D9(self, node): # Spline3D_Curve
		i = self.ReadContentHeader(node, 'Spline3D_Curve')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'flags2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = self.skipBlockSize(i, 8)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst2')
		else:
			addEmptyLists(node, [1, 2])
		return i

	def Read_F9884C43(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'parts')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2011):
			i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadCrossRef(i, 'refFX')
		return i

	def Read_F9DB9290(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2017): i += 4 # skip FF FF FF FF
		if (getFileVersion() > 2018): i += 8 # skip 00 00 00 00 00 00 00 00
		i = node.ReadCrossRef(i, 'ref1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'refPlane1')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadCrossRef(i, 'refPlane2')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadCrossRef(i, 'refPoint')
		return i

	def Read_FA6E9782(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64_2D(i, 'p1')
		i = node.ReadFloat64_2D(i, 'p2')
		return i

	def Read_FA7C9C79(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_FABE1977(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_LIST_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'refParameter')
		i = node.ReadCrossRef(i, 'refTransformation')
		return i

	def Read_FAD9A9B5(self, node): # MirrorFeature {12BF1F8A-5679-468F-A820-DA5532624CEA}
		properties, i = self.ReadHeaderPattern(node, 'Mirror')
		for j in range(6, 11):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			properties.append(ref)
		if (getFileVersion() > 2016):
			i += 24 #???
		else:
			i = self.skipBlockSize(i)
		for j in range(11, 13):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.SecNodeRef.TYPE_CROSS)
			properties.append(ref)
		return i

	def Read_FB73FDDF(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_FBC6C635(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_FBDB891F(self, node): # PatternConstraint {C173A073-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_PolygonEdge2D')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'refCenter')
		i = node.ReadCrossRef(i, 'refPolygonCenter1')
		i = node.ReadCrossRef(i, 'refPolygonCenter2')
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_FC86960C(self, node):
		n, i = getUInt32(node.data, 0)
		for k in range(0, n):
			t, i = getUInt16(node.data, i)
			if (t == 0):
				i = self.ReadTypedFloats(node, i, "a%d" % k)
			elif (t == 1):
				i = node.ReadUInt32A(i, 2, "a%d" % k)
		return i

	def Read_FC9AAE10(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		return i

	def Read_FCDC569A(self, node):
		i = self.ReadContentHeader(node)
		if (getFileVersion() > 2017): i += 4
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_FD590AA5(self, node): # MeshFeature
		i = node.Read_Header0('MeshFeature')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref1')
		i = node.ReadCrossRef(i, 'ref1')
		i = node.ReadChildRef(i, 'label')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFolder')

		return i

	def Read_FD7702B0(self, node):
		i = self.ReadChildHeader1(node)
		i = self.skipBlockSize(i, 8)
		i = node.ReadUInt32A(i, 9, 'a1')
		return i

	def Read_FEB0D977(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refPoint2D')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = node.ReadCrossRef(i, 'refPoint3D')
		return i

	def Read_FF15793D(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'refEntity1')
		i = node.ReadCrossRef(i, 'refTransformation')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'refEntity2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_FF46726C(self, node):
		i = self.ReadList2U32(node)
		return i

	def Read_FFD270B8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUUID(i, 'uid')
		return i

	def Read_Operation(self, node, operation, name):
		'''
		Reads the operation section
		'''
		i = self.Read_F8A77A0D(node)
		i = node.ReadChildRef(i, 'refOperand2')
		i = self.skipBlockSize(i)
		node.typeName = 'ParameterOperation' + operation
		node.name = name
		return i

	def Read_F8A77A06(self, node): return self.Read_Operation(node, 'Plus'  , '+')
	def Read_F8A77A07(self, node): return self.Read_Operation(node, 'Minus' , '-')
	def Read_F8A77A08(self, node): return self.Read_Operation(node, 'Mul'   , '*')
	def Read_F8A77A09(self, node): return self.Read_Operation(node, 'Div'   , '/')
	def Read_F8A77A0A(self, node): return self.Read_Operation(node, 'Modulo', '\x25')
	def Read_F8A77A0B(self, node): return self.Read_Operation(node, 'Power' , '^')
