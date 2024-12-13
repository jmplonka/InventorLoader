# -*- coding: utf-8 -*-

'''
importerDC.py:
Importer for the Document's components
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''
from importerEeData         import EeDataReader
from importerUtils          import *
from importerClasses        import Tolerances, Functions, VAL_UINT8, VAL_UINT16, VAL_UINT32, VAL_REF, VAL_STR16, VAL_ENUM
from xlrd                   import open_workbook
import importerSegNode, re

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

def addEmptyLists(node, indexes):
	for i in indexes:
		node.set('lst%d' %(i), [])

class DCReader(EeDataReader):
	DOC_ASSEMBLY     = 1
	DOC_DRAWING      = 2
	DOC_PART         = 3
	DOC_PRESENTATION = 4

	def __init__(self, segment):
		super(DCReader, self).__init__(segment)
		segment.ntKeys = {}

########################################
# usability functions
	def ReadClassInfo(self, node, offset, refName, idx = ''):
		internal, i = getBoolean(node.data, offset) # internal reference ?
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, refName)
		if (not internal):
			if (len(idx) == 0):
				i = node.ReadLen32Text16(i)
			else:
				i = node.ReadLen32Text16(i, 'txt_0')
			i = node.ReadLen32Text16(i, 'txt_1')
			i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		return i

	def Read2RefList(self, node, offset, name, type1 = importerSegNode.REF_CROSS, type2 = importerSegNode.REF_CROSS):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref1, i = self.ReadNodeRef(node, i, [j,0], type1, name)
			ref2, i = self.ReadNodeRef(node, i, [j,1], type2, name)
			lst.append([ref1, ref2])
		node.set(name, lst)
		return i

	def ReadRefU32U8List(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref, i = self.ReadNodeRef(node, i, [j, 0], importerSegNode.REF_CROSS, name)
			val, i = getUInt32(node.data, i)
			u8, i  = getUInt8(node.data, i)
			lst.append([ref, val, u8])
		node.set(name, lst, VAL_UINT32)
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
		node.set(name, lst, VAL_UINT32)
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
			tol = 0
			if (len(lst) > 0):
				tol, i = getFloat64(node.data, i)
		else:
			tol = None
		node.set(key, {'meta': meta, 'values': lst, 'tolerance': tol})
		return i
	'''
	next: -> ReadHeaderLinkedElement
	parameters: -> ReadHeaderParameter

	H0 R s                                                                                                -> ReadHeaderParameter
	H0 R s R s                                                                                            -> ReadOperatorUnary
	H0 R s R s R s                                                                                        -> ReadOperator
	H0 R L s P L                                                                                          -> ReadHeaderContent
	H0 R L s P L s   l        s R (L6 L6)>2012 ss R                                                       -> ReadHeaderConstraint2D
	H0 R L s P L s   l        s R s                                                                       -> ReadHeaderCntSLRS
	H0 R L s P L s   l        s R s L2 B R (L6 L6)>2012 s                                                 -> ReadHeaderConstraint3D
	H0 R L s P L s   l        ss                                                                          -> ReadHeadersS32ss
	H0 R L s P L s   l        ss                                                                          -> ReadHeaderFeature
	H0 R L s P L s   l        ss L L2 s L s L2 R R R R R B                                                -> ReadHeaderPattern
	H0 R L s P L s   l        ss L R R R R R R R (R L)>2017 s                                             -> ReadHeaderBendExtent
	H0 R L s P L s   l        ss R R R R R R R R R R L2 (L)>2017 R                                        -> ReadHeaderHemShape
	H0 R L s P L s   l        ss L2 L s R H H T B L L L s                                                 -> ReadHeaderComponentDerived
	H0 R L s P L s   l        ss CI L (L)>2017 s L s L8 L8 L8 s                                           -> ReadHeaderEdgeId
	H0 R L s P L s   l        sss L2 L2 L2 L L (R)>2011 s                                                 -> ReadHeaderFaceBound
	H0 R L s P L s   (l)>2018 R                                                                           -> ReadCntHdr1SCross
	H0 R L s P L ss  (l)>2018                                                                             -> ReadCntHdr2S
	H0 R L s P L ss  (l)>2018 R                                                                           -> ReadCntHdr2SCross/Child
	H0 R L s P L sss (l)>2018                                                                             -> ReadCntHdr3S
	H0 R L s P L sss (l)>2018 L2 (S32)?                                                                   -> ReadHeaderIndexRefs
	H0 R L s P L sss (l)>2018 h H s                                                                       -> ReadHeaderEnum
	H0 R L s P L sss (l)>2018 L s                                                                         -> ReadHeadersss2S16s
	H0 R L s P L sss (l)>2018 L s R R (L)>2017 s                                                          -> ReadHeaderSketch3DEntity
	H0 R L s P L sss (l)>2018 L s s d d L2 L2 (L L2)>2012 (L2)>2019                                       -> ReadHeaderSketch2DEntity
	H0 R L s P L sss (l)>2018 L s s d d L2 L2 (L L2)>2012 (L2)>2019 s L2 ((L L)>2019 L2 (L2)>2019)>2019 s -> ReadHeader2DEdge
	H0 R L s UID T L2 L L L s R R s R R R R s                                                             -> ReadHeaderDocument
	'''

	#######################
	# Parameter sections
	def ReadHeaderParameter(self, node, typeName):
		i = node.Read_Header0(typeName)
		i = node.ReadChildRef(i, 'unit')
		i = self.skipBlockSize(i)
		return i

	def Read_0AA8AF46(self, node): # ParameterConstant
		i = self.ReadHeaderParameter(node, 'ParameterConstant')
		i = node.ReadFloat64(i, 'value')
		i = node.ReadSInt16(i, 's16_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		if (node.name == 'PI') : node.name = 'pi'
		elif (node.name == 'E'): node.name = 'e'
		return i

	def Read_F8A77A03(self, node): # ParameterFunction
		i = self.ReadHeaderParameter(node, 'ParameterFunction')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'operands')
		i = self.skipBlockSize(i)
		i = node.ReadEnum16(i, 'name', None, Functions)
		i = node.ReadUInt16(i, 'u16_0')
		ref = node.get('operands')
		if (len(ref) > 0):
			node.set('operand', ref[0])
		return i

	def Read_F8A77A04(self, node): # ParameterValue
		i = self.ReadHeaderParameter(node, 'ParameterValue')
		i = node.ReadFloat64(i, 'value')
		i = node.ReadUInt16(i, 'type')
		if (self.version > 2010): i += 4
		return i

	def Read_F8A77A05(self, node): # ParameterRef
		i = self.ReadHeaderParameter(node, 'ParameterRef')
		i = node.ReadCrossRef(i, 'operand1')
		return i

	#######################
	# unary Operator sections
	def ReadOperatorUnary(self, node, typeName, name):
		i = self.ReadHeaderParameter(node, typeName)
		i = node.ReadChildRef(i, 'operand1')
		i = self.skipBlockSize(i)
		node.name = name
		return i

	def Read_F8A77A0C(self, node): return self.ReadOperatorUnary(node, 'ParameterOperatorUnaryMinus', '-')
	def Read_F8A77A0D(self, node): return self.ReadOperatorUnary(node, 'ParameterOperatorPowerIdent', '^')

	#######################
	# Operator sections
	def ReadOperator(self, node, typeName, name):
		i = self.ReadOperatorUnary(node, typeName, name)
		i = node.ReadChildRef(i, 'operand2')
		i = self.skipBlockSize(i)
		return i

	def Read_F8A77A06(self, node): return self.ReadOperator(node, 'ParameterOperatorPlus'  , '+')
	def Read_F8A77A07(self, node): return self.ReadOperator(node, 'ParameterOperatorMinus' , '-')
	def Read_F8A77A08(self, node): return self.ReadOperator(node, 'ParameterOperatorMul'   , '*')
	def Read_F8A77A09(self, node): return self.ReadOperator(node, 'ParameterOperatorDiv'   , '/')
	def Read_F8A77A0A(self, node): return self.ReadOperator(node, 'ParameterOperatorModulo', '%')
	def Read_F8A77A0B(self, node): return self.ReadOperator(node, 'ParameterOperatorPower' , '^')

	#######################
	# content sections
	def ReadHeaderContent(self, node, typeName = None, name = 'next'):
		'''
		Read the header for content objects like Sketch2D, Pads, ...
		'''
		i = node.Read_Header0(typeName)
		if (name in ['next', 'creator']):
			i = node.ReadChildRef(i, name)
		else:
			i = node.ReadCrossRef(i, name)
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadCrossRef(i)
		i = node.ReadUInt32(i, 'index')

		flags = node.get('flags')
		node.visible             = (flags & 0x00000400) > 0
		node.dimensioningVisible = (flags & 0x00800000) > 0
		self.segment.indexNodes[node.get('index')] = node
		node.Item = True
		return i

	def Read_033E027B(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_07910C0A(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_B4F8F817(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_0A576361(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		return i

	def Read_0AD21008(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_4B2376C4(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_9C9E3CB3(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i, 'container') # CAT-Container path
		return i

	def Read_DD80AC37(self, node): # something to do with text-alignment
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'faces')
		i = node.ReadCrossRef(i, 'refEdge')
		i = node.ReadCrossRef(i, 'refString')
		return i

	def Read_DE172BCF(self, node): # ModelToleranceFeature {CEBC9A45-2058-4537-9D52-5E11419267DE}
		i = self.ReadHeaderContent(node, 'ModelToleranceFeature')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'faces')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'clientId')
		i = node.ReadCrossRef(i, 'parentToleranceFeature')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2018): i += 4 # skip 02 00 00 00
		return i

	def Read_0BA398EA(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'surface')
		i = node.ReadCrossRef(i, 'bendType')    # Relief
		i = node.ReadCrossRef(i, 'useDefault')
		return i

	def Read_0CA07988(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_0E64A759(self, node): # ModelGeneralNote {88C68B3A-B9B0-45DD-873C-FA0187B80E62}
		i = self.ReadHeaderContent(node, 'ModelGeneralNote')
		return i

	def Read_1128AE62(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_UINT32_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_UINT32_, 'lst1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_UINT32_, 'lst2')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_15A5FF92(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_15E7211A(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_16DE1A75(self, node): # DimensionAnnotation
		i = self.ReadHeaderContent(node, 'AnnonatationDimension')
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		if not((self.version == 2018) and (getFileBeta() > 0)):
			i = node.ReadCrossRef(i, 'ref0')
		i = node.ReadCrossRef(i, 'ref1')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2024):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref2')
		i = node.ReadCrossRef(i, 'ref4')
		i = node.ReadCrossRef(i, 'ref5')
		i = node.ReadCrossRef(i, 'ref6')
		i = node.ReadCrossRef(i, 'ref7')
		return i

	def Read_19573122(self, node): # new in 2019
		i = self.ReadHeaderContent(node)
		if (self.version > 2017): i += 4 # skip FF,FF,FF,FF
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadCrossRef(i, 'ref_1') # -> E70647C4
		return i

	def Read_1A1C8265(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32A(i, 2, 'a0') # (0002, 0000)
		return i

	def Read_220226D5(self, node): # Blocks
		i = self.ReadHeaderContent(node, 'Blocks')
		return i

	def Read_223360AD(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		return i

	def Read_23BA0568(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_26287E96(self, node): # iPart
		i = self.ReadHeaderContent(node, 'iPart')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'excelWorkbook')
		i = node.ReadSInt32(i, 'rowIndex')
		i = node.ReadUUID(i, 'uid')
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'refParent')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'iParts')
		i = node.ReadBoolean(i, 'selected')
		return i

	def Read_274E16CD(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i, 2)
		i = node.ReadUUID(i, 'uid')
		return i

	def Read_288D7986(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_28BE2D5B(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_28E17530(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_2AF9B62B(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'f0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_2B241309(self, node): # BrowserFolder {9D063FDB-B597-49B0-8DBC-7EB3D5F715B8}
		i = self.ReadHeaderContent(node, 'BrowserFolder')
		i = self.skipBlockSize(i)
		return i

	def Read_2B60D993(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_2D06CAD3(self, node): # ProjectCutEdges
		i = self.ReadHeaderContent(node, 'ProjectCutEdges')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadCrossRef(i, 'sketch')
		i = self.Read2RefList(node, i, 'lst0', importerSegNode.REF_CHILD, importerSegNode.REF_CROSS)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		return i

	def Read_2D86FC26(self, node): # ReferenceEdgeLoopId
		i = self.ReadHeaderContent(node, 'ReferenceEdgeLoopId')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst1')
		return i

	def Read_30F71B26(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt16A(i, 3, 'a0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_0334499C(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'part')
		i = node.ReadList4(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadChildRef(i, 'ref_3')
		if (self.version > 2016): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadLen32Text8(i, 'txt_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUUID(i, 'uid')
		i = node.ReadChildRef(i, 'ref_4')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT8_3D_F32_, 'lst2')
		i = node.ReadFloat32A(i, 14, 'a1')
		i = node.ReadLen32Text16(i)
		return i

	def Read_338634AC(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'part')
		i = node.ReadList4(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadChildRef(i, 'ref_3')
		if (self.version > 2016): i += 4
		i = node.ReadChildRef(i, 'ref_4')
		return i

	def Read_33B05D59(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'bend')
		i = node.ReadCrossRef(i, 'surface')
		return i

	def Read_346F5947(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_381AF8C4(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_3AB895E9(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'document')
		return i

	def Read_3B13313C(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		return i

	def Read_3BD61A2C(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadLen32Text16(i, 'equation')
		return i

	def Read_3C7F67AA(self, node): # Bodies folder
		i = self.ReadHeaderContent(node, 'BodiesFolder')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_3F4FA55F(self, node): # OffsetSplineDimConstraint {BBCEA345-055B-4625-ABCA-582C6BF7E440}
		i = self.ReadHeaderContent(node, 'Dimension_OffsetSpline2D')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 'flags2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'group')
		i = self.skipBlockSize(i, 2)
		if (self.version > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
		else:
			node.set('lst0', {}, VAL_REF)
			node.set('lst1', {}, VAL_REF)
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_402A8F9F(self, node):
		i = self.ReadHeaderContent(node, 'RotateClockwise')
		if (self.version > 2010):
			i += 8
		else:
			i += 12
		i = node.ReadBoolean(i, 'value')
		i = self.skipBlockSize(i)
		if (self.version > 2018): i += 4 # skip 00 00 00 00
		if (self.version > 2020): i += 4 # skip 00 00 00 00
		return i

	def Read_405AB2C6(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_440C98C9(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUUID(i, 'id')
		return i

	def Read_4580CAF0(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadCrossRef(i, 'ref1')
		i = node.ReadCrossRef(i, 'param1')
		i = node.ReadCrossRef(i, 'param2')
		return i

	def Read_45825754(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'entity3D')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_48C52258(self, node): # BSpline3D
		i = self.ReadHeaderContent(node, 'BSpline3D')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 'flags2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'group')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'sketch')
		if (self.version > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst2')
		else:
			i = self.skipBlockSize(i)
			node.set('lst1', {}, VAL_REF)
			node.set('lst2', {}, VAL_REF)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'bezier')
		return i

	def Read_4B050ACA(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'plane')
		i = node.ReadCrossRef(i, 'source')
		i = node.ReadCrossRef(i, 'target')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'transformation')
		return i

	def Read_4E86F047(self, node): # Assembly: Placement-Constaint
		i = self.ReadHeaderContent(node, 'Constraint')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1') # participants
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'style') # 1: mate, 2: flush, 3: angle, 14: symmetry
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'selection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'values') # 0=offset, 1=min, 2=max
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2010): i += 4 # skip 00 00 00 00
		if (self.version > 2012): i += 1 # skip 03
		return i

	def Read_4E8F7EE5(self, node): # ModelFeatureControlFrame
		i = self.ReadHeaderContent(node, 'ModelFeatureControlFrame')
		return i

	def Read_54846913(self, node):
		i = self.ReadHeaderContent(node, 'Drawing')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadFloat64(i, 'f64_1')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_5499A4B9(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_55CE9B23(self, node):
		i = self.ReadHeadersS32ss(node)
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_1')
		dummy, k = getUInt32(node.data, i)
		if (dummy == 0):
			i = k
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_5844C14D(self, node): # Folder for Point Clouds
		i = self.ReadHeaderContent(node, 'PointCloudFolder')
		return i

	def Read_598AACFE(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_5A6B6124(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_5B708411(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_5D8C859D(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 'flags2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'group')
		if (self.version > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
		else:
			node.set('lst0', {}, VAL_REF)
			node.set('lst1', {}, VAL_REF)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		return i

	def Read_5E464B13(self, node): # ModelSurfaceTextureSymbol
		i = self.ReadHeaderContent(node, 'ModelSurfaceTextureSymbol')
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		return i

	def Read_63D9BDC4(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_6489E49C(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2018): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_6514096C(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		i = self.ReadClassInfo(node, i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_6566C3E1(self, node): # LinearModelDimension
		i = self.ReadHeaderContent(node, 'ModelDimensionLinear')
		return i

	def Read_65897E4A(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_66B388ED(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_671CE131(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_6C5CD68F(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_6C5CD690(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_6BE30AF0(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'faces')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'edges')
		return i

	def Read_6F7A6F97(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_6FB0D4A7(self, node): # ModelLeaderNote {5194100D-435F-4C85-A922-6BD3E4CC9C36}
		i = self.ReadHeaderContent(node, 'ModelLeaderNote')
		return i

	def Read_6FD9928E(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_71C0D0C6(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_72E450AC(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_76BDB118(self, node): # new in 2015
		i = self.ReadHeaderContent(node, 'Freeform')
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		if (self.version > 2020): i += 4 # skip FF FF FF FF
		i = node.ReadChildRef(i, 'wrapper')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'wrappers')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_7C321197(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_7DA7F733(self, node):
		i = self.ReadHeaderContent(node)
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

	def Read_7E15AA39(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		if (self.version > 2020):
			i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0') # really UINT32???
		return i

	def Read_7F7F05AC(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64_3D(i, 'p1')
		i = node.ReadFloat64_3D(i, 'p2')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadUInt32(i, 'u32')
		return i

	def Read_81E94AB7(self, node):
		i = self.ReadHeaderContent(node, 'SurfaceDetails')
		if (self.version > 2018): i += 4 # skip FF FF FF FF
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

	def Read_86A4AAC4(self, node): # SketchBlock
		i = self.ReadHeaderContent(node, 'SketchBlock')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt32(i, 'numEntities')
		i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'direction')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'blocks')
		if (self.version > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		else:
			node.set('lst1', [], VAL_REF)
		i = node.ReadCrossRef(i, 'anchor')
		i = node.ReadUUID(i, 'id')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_86CF7D57(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_8740B863(self, node):
		i = self.ReadHeaderContent(node, 'EquationCurve2D')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_8946E9E8(self, node): # MeshPart
		i = self.ReadHeaderContent(node, 'MeshPart')
		if (self.version > 2018):i += 4 # 0xFFFFFF
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_8B1E9A97(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		if (self.version < 2012):
			i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadFloat64(i, 'd0')
		return i

	def Read_8EE901B9(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_8EC6B314(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'group')
		if (self.version > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst2')
		else:
			i = self.skipBlockSize(i, 2)
			node.set('lst1', {}, VAL_REF)
			node.set('lst2', {}, VAL_REF)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'spline')
		i = node.ReadCrossRef(i, 'line')
		return i

	def Read_90874D40(self, node): # Mapping of parameters
		i = self.ReadHeaderContent(node, 'ParameterMappings')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'target')
		i = node.ReadList3(i, importerSegNode._TYP_NODE_REF_, 'mapping')
		i = node.ReadFloat64(i, 'f')
		i = node.ReadCrossRef(i, 'paramRef')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_90874D48(self, node): # BodySet
		i = self.ReadHeaderContent(node, 'BodySet')
		i = self.skipBlockSize(i)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		if (self.version > 2020): i += 4 # skip FF FF FF FF
		return i

	def Read_90874D61(self, node):
		i = self.ReadCntHdr2S(node) # 'ref' contains IPT document!
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'value')
		return i

	def Read_90874D67(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		if (self.version > 2020): i += 4 # skip FF FF FF FF
		return i

	def Read_9574000C(self, node): # Hole Annotation
		i = self.ReadHeaderContent(node, 'AnnotationHole')
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		if not((self.version == 2018) and (getFileBeta() > 0)):
			i = node.ReadCrossRef(i, 'ref0')
		i = node.ReadCrossRef(i, 'plane')
		i = node.ReadUInt32(i, 'u32_0')
		if not((self.version == 2018) and (getFileBeta() > 0)):
			if (self.version > 2023):
				i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref2')
		i = node.ReadCrossRef(i, 'ref3')
		i = node.ReadCrossRef(i, 'ref4')
		i = node.ReadCrossRef(i, 'ref5')
		i = node.ReadCrossRef(i, 'ref6')
		i = node.ReadCrossRef(i, 'ref7')
		i = node.ReadCrossRef(i, 'ref8')
		# 01 04 00 00 00 00
		return i

	def Read_99B938B0(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i, 2)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		if (self.version > 2020): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32A(i, 18, 'a0')

		i = node.ReadUInt32(i, 'typ')
		typ = node.get('typ')
		if (typ == 0x03):
			i = node.ReadUInt16A(i, 3, 'a1')
		elif (typ == 0x23):
			i = node.ReadUInt16A(i, 1, 'a1')
		else:
			node.set('a1', [], VAL_UINT16)
		i = node.ReadFloat64_2D(i, 'a2')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadFloat64A(i, 6, 'a4')
		i = node.ReadUInt16A(i, 6, 'a5')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadUInt32A(i, 2, 'a6')
		i = node.ReadUInt32A(i, 2, 'a7')
		i = node.ReadUInt32A(i, 2, 'a8')
		return i

	def Read_9C38036E(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_9C8C1297(self, node):
		i = self.ReadHeaderContent(node, 'UserCoordinateSystemValues')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ucs')
		i = node.ReadCrossRef(i, 'point')
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

	def Read_9ED6024F(self, node): # AngularModelDimension
		i = self.ReadHeaderContent(node, 'ModelDimensionAngular')
		return i

	def Read_A5428F7A(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_A7E650BC(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_ABF19878(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_AE8FDC73(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'drawing')
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		return i

	def Read_B3EAA9EC(self, node): # new in 2019
		i = self.ReadHeaderContent(node)
		i = node.ReadUInt32(i, 'u23_0')
		i = node.ReadCrossRef(i, 'plane')
		i = node.ReadCrossRef(i, 'line')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadFloat64_2D(i, 'f64_0')
		return i

	def Read_B4124F0C(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_B5DFF07E(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i, 2)
		if (self.version > 2020): i += 4 # skip FF FF FF FF
		i = node.ReadUUID(i, 'uid_0')
		return i

	def Read_B690EF36(self, node):
		i = self.ReadHeaderContent(node, 'BendTransitionDef', 'ref_1')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'surface')
		i = node.ReadCrossRef(i, 'type')
		i = node.ReadCrossRef(i, 'ref_2')     # bool
		return i

	def Read_B71CBEC9(self, node): # HelicalConstraint3D {33E293A8-9DD6-4B9A-8274-E436A3BB3876}
		i = self.ReadHeaderContent(node, 'Geometric_Helical3D')
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'group')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'sketch')
		i = self.skipBlockSize(i)
		if (self.version > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst2')
		else:
			node.set('lst1', {}, VAL_REF)
			node.set('lst2', {}, VAL_REF)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version < 2019):
			i = node.ReadCrossRef(i, 'parameter0')
			i = node.ReadCrossRef(i, 'parameter1')
			i = node.ReadCrossRef(i, 'parameter2')
			i = node.ReadCrossRef(i, 'parameter3')
			i = node.ReadCrossRef(i, 'parameter4')
		i = node.ReadUInt16A(i, 7, 'a0')
		if (self.version > 2018):
			i += 4 # skip 00 00 00 00
			if (self.version > 2019): i += 3 # skip 00 00 00
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst3')
		i = node.ReadChildRef(i, 'parameter5')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_B8CB3560(self, node): # ModelAnnotations
		i = self.ReadHeaderContent(node, 'ModelAnnotations')
		i = node.ReadSInt32(i, 's32_0')
		return i

	def Read_BE8CEB3C(self, node): # RadiusModelDimension
		i = self.ReadHeaderContent(node, 'ModelDimensionRadius')
		return i

	def Read_BEE5961F(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		return i

	def Read_C2D0676B(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i, 2)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_C6435233(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_CA02411F(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		if (node.get('next') is None):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		else:
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		return i

	def Read_CAB7E237(self, node): # General Surface Profile Tolerance
		i = self.ReadHeaderContent(node, 'GenSurfProfTol')
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		# workaround for 2018 BETA1:
		if not((self.version == 2018) and (getFileBeta() > 0)):
			i = node.ReadCrossRef(i, 'annoDim')
		i = node.ReadCrossRef(i, 'plane')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref2')
		i = node.ReadCrossRef(i, 'ref3')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_ , 'lst1') # 02 00 00 30 00 00 00 00
		i = node.ReadUInt32(i, 'u32_4' ) # 00 00 00 00
		i = node.ReadFloat64A(i, 9, 'a1')
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst2')
		return i

	def Read_CC90BCDA(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadList2(i, importerSegNode._TYP_LIST_SINT16_A_, 'lst0', 2)
		return i

	def Read_CDFF1D93(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_CFB519D1(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32(i, 'u32_0')
		i = self.ReadNtEntryList(node, i, 'entries')
		return i

	def Read_D3F71C7A(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i, 2)
		return i

	def Read_D5929B31(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_D739EDBB(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_DD7D4B84(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2017): i += 4
		i = node.ReadCrossRef(i, 'plane')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_DDCF0E1C(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32A(i, 26, 'a0')
		i = node.ReadFloat64A(i, 7, 'a1')
		return i

	def Read_DEBD4124(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_E1D8C31B(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		return i

	def Read_E70647C4(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 3, 'a0')
		if (self.version > 2014): i += 4 # skip 00 00 00 00
		i = node.ReadFloat64_3D(i, 'm0')
		i = node.ReadFloat64_3D(i, 'm1')
		i = node.ReadFloat64_3D(i, 'm2')
		i = node.ReadFloat64_3D(i, 'center')
		i = node.ReadFloat64(i, 'angleStart')
		i = node.ReadFloat64(i, 'angleSweep')
		return i

	def Read_E8313971(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_EB9E49B0(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		if (self.version > 2018): i += 4
		flags = node.get('flags')
		if (flags & 0x2000000) > 0:
			i = node.ReadUInt32(i, 'u32_1')
		else:
			i = node.ReadChildRef(i, 'wrapper')
			node.set('u32_1', 0, VAL_UINT32)
		return i

	def Read_EC7B8A2B(self, node):
		i = self.ReadHeaderContent(node)
		if (self.version > 2017): i += 4 # skip FF FF FF FF
		i = node.ReadCrossRef(i, 'ref0')
		i = node.ReadCrossRef(i, 'ref1')
		i = node.ReadCrossRef(i, 'point')
		return i

	def Read_EEF10748(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 4, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_F0769408(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_F076940B(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_F3F435A1(self, node):
		i = self.ReadHeaderContent(node)
		return i

	def Read_F94FF0D9(self, node): # Spline3D_Curve
		i = self.ReadHeaderContent(node, 'Spline3D_Curve')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'flags2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'group')
		i = self.skipBlockSize(i, 2)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'sketch')
		if (self.version > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst2')
		else:
			node.set('lst1', {}, VAL_REF)
			node.set('lst2', {}, VAL_REF)
		return i

	def Read_F7763F69(self, node):
		i = self.ReadHeaderContent(node) #, '')
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'parameters')
		i = node.ReadCrossRef(i, 'sets')
		i = node.ReadCrossRef(i, 'fx')
		return i

	def Read_8C1A567D(self, node):
		i = self.ReadHeaderContent(node, 'ThreadDefinition')
		i = self.skipBlockSize(i, 2)
		if (self.version > 2018): i += 4
		i = node.ReadCrossRef(i, 'proxy')
		i = node.ReadCrossRef(i, 'faces')
		i = node.ReadCrossRef(i, 'edges')
		i = node.ReadCrossRef(i, 'fullDepth')
		i = node.ReadCrossRef(i, 'reversed')
		i = node.ReadCrossRef(i, 'length')
		i = node.ReadCrossRef(i, 'offset')
		i = node.ReadBoolean(i,  'fully')
		return i

	def Read_213C9A4C(self, node): # DerivedAssemblyComponent properties
		i = self.ReadHeaderContent(node, 'DerivedAssemblyComponentDefinition')
		return i

	#######################
	# Content header skip FF's
	def ReadCntHdrFF(self, node, typeName = None):
		i = self.ReadHeaderContent(node)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		if (self.version > 2020): i += 4 # skip FF FF FF FF
		return i

	def Read_0800FE29(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'transformations')
		return i

	def Read_0CAC6298(self, node):
		i = self.ReadCntHdrFF(node, 'SnapFitAnchors')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		return i

	def Read_42BC8C9A(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_1345015C(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadCrossRef(i, 'param')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'faces')
		return i

	def Read_37889260(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadFloat64A(i, 4, 'a0')
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64_2D(i, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		return i

	def Read_4DC465DF(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		return i

	def Read_502678E7(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadFloat64A(i, 4, 'a0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8A(i, 7, 'a1')
		i = node.ReadFloat64A(i, 6, 'a2')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadFloat64A(i, 4, 'a3')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_51CA84E2(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		return i

	def Read_5ABD7468(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_617931B4(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadFloat64_3D(i, 'pos')
		e, i = self.ReadEdge(node, i)
		node.set('e', e)
		return i

	def Read_660DEE07(self, node): # ??? FilletSetback ???
		i = self.ReadCntHdrFF(node)
		i = node.ReadCrossRef(i, 'edgeProxies')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'radii')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'booleans')
		return i

	def Read_7312DB35(self, node):
		i = self.ReadCntHdrFF(node)
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

	def Read_7414D5CA(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_,     'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_,     'lst2')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_,  'lst3', 3)
		return i

	def Read_7DF60748(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		return i

	def Read_8B2B8D96(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_8BE7021F(self, node):
		i = self.ReadCntHdrFF(node)
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

	def Read_91B99A2C(self, node): # FilletIntermediateRadius
		i = self.ReadCntHdrFF(node, 'FilletIntermediateRadius')
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadCrossRef(i, 'radius')
		i = node.ReadCrossRef(i, 'edgeProxy')
		return i

	def Read_955501BC(self, node): # Fillets variable radius position
		i = self.ReadCntHdrFF(node, 'FilletIntermediateRadius')
		i = node.ReadCrossRef(i, 'edge')
		i = node.ReadCrossRef(i, 'param')  # Parameter that controls the position of the point along the edge.
		i = node.ReadCrossRef(i, 'radius')
		return i

	def Read_B799E9B2(self, node): # Fillet set with variable radiii
		i = self.ReadCntHdrFF(node, 'FilletVariableRadiusEdgeSet')
		i = node.ReadCrossRef(i, 'edges')
		i = node.ReadCrossRef(i, 'radii')
		i = node.ReadCrossRef(i, 'continuityG1')
		return i

	def Read_BE175768(self, node):
		i = self.ReadCntHdrFF(node)
		cnt, i = getUInt32(node.data, i)
		lst = []
		for j in range(cnt):
			txt, i = getLen32Text16(node.data, i)
			lst.append(txt)
		node.set('lst0', lst, VAL_STR16)
		return i

	def Read_D70E9DDA(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_D9F7441B(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'features')
		return i

	def Read_CAFE99DF(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadUInt32A(i, 3, 'a0')
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		i = node.ReadUInt32A(i, 8, 'a1')
		i = node.ReadUInt32A(i, 3, 'a2')
		i = self.ReadFloat64A(node, i, node.get('a2')[0], 'knots', 3)
		i = node.ReadUInt32A(i, 3, 'a3')
		i = node.ReadFloat64A(i, node.get('a3')[0], 'mults')
		i = node.ReadFloat64(i, 'tol1')
		i = node.ReadUInt32A(i, 3, 'a4')
		i = node.ReadFloat64A(i, node.get('a4')[0], 'weights')
		i = node.ReadFloat64(i, 'tol2')
		i = node.ReadUInt32A(i, 3, 'a5')
		i = node.ReadFloat64A(i, node.get('a5')[0], 'a6')
		return i

	def Read_E1913A46(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_F145279A(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_FCDC569A(self, node):
		i = self.ReadCntHdrFF(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_6')
		return i

	#######################
	# Content header 3xskip sections
	def ReadCntHdr3S(self, node, typeName = None):
		i = self.ReadHeaderContent(node, typeName)
		i = self.skipBlockSize(i, 3)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		if (self.version > 2020): i += 4 # skip FF FF FF FF
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

	def Read_0D798B55(self, node): #
		i = self.ReadCntHdr3S(node)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_0E6870AE(self, node): # ObjectCollection
		i = self.ReadCntHdr3S(node, 'ObjectCollection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'items')
		return i

	def Read_1B48E9DA(self, node): # Fillet sets with constant radii
		i = self.ReadCntHdr3S(node, 'FxFilletEdgeSetsConstantR')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'sets')
		return i

	def Read_22947391(self, node): # BoundaryPatchFeature {16B36EBE-2DFA-4474-B11B-DF3D57C109B0}
		i = self.ReadCntHdr3S(node, 'BoundaryPatch')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_24BCB2F1(self, node):
		i = self.ReadCntHdr3S(node, 'FaceCollection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'items')
		return i

	def Read_2801D6C6(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_299B2DCE(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_312F9E50(self, node):
		i = self.ReadCntHdr3S(node, 'LoftSections')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'items')
		return i

	def Read_4949374A(self, node):
		i = self.ReadCntHdr3S(node, 'Enum')
		i = node.ReadUInt32(i, 'type')
		i = self.skipBlockSize(i)
		i = node.ReadEnum32(i, 'value', 'FilletConstantRSelectMode', ['Edge', 'Loop', 'Feature'])
		return i

	def Read_4BB00236(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		if (self.version > 2014):
			i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_51C2DDF1(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_557C2ED5(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_5FB25A7E(self, node):
		i = self.ReadCntHdr3S(node, 'SculptSurfaceCollection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'items')
		return i

	def Read_76CF355F(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		i = node.ReadUUID(i, 'uid')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_7C6D7B13(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_831EBCE9(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_833687A1(self, node): #
		i = self.ReadCntHdr3S(node)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_833D1B91(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_8367B125(self, node): # ParameterText
		i = self.ReadCntHdr3S(node, 'ParameterText')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'isKey')
		i = node.ReadLen32Text16(i, 'value')
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

	def Read_866CBE44(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_866CBE45(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_90874D26(self, node): # Parameter
		i = self.ReadCntHdr3S(node, 'Parameter')
		i = node.ReadLen32Text16(i)            # parameter's name
		i += 4
		i = node.ReadChildRef(i, 'unit')
		i = node.ReadChildRef(i, 'formula')
		i = node.ReadFloat64(i, 'valueNominal')
		i = node.ReadFloat64(i, 'valueModel')
		i = node.ReadEnum16(i, 'tolerance', None, Tolerances)
		i = node.ReadSInt16(i, 'u16_0')
		return i

	def Read_90874D28(self, node): # Boolean
		i = self.ReadCntHdr3S(node, 'Boolean')
		if (self.version > 2010):
			i = node.ReadLen32Text16(i)
			i += 4
		i = node.ReadBoolean(i, 'value')
		return i

	def Read_90874D51(self, node):
		i = self.ReadCntHdr3S(node, 'EdgeCollection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'items')
		return i

	def Read_936522B1(self, node):
		i = self.ReadCntHdr3S(node, 'HoleCenterPoints')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		return i

	def Read_99684A5A(self, node):
		i = self.ReadCntHdr3S(node)
		if (self.version > 2010):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadUInt32(i, 'u32_1')
		else:
			node.set('u32_0', 0, VAL_UINT32)
			node.set('u32_1', 0, VAL_UINT32)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_AA805A06(self, node):
		i = self.ReadCntHdr3S(node)
		return i

	def Read_AAD64116(self, node): # Fillet set with constant radius
		i = self.ReadCntHdr3S(node, 'FilletEdgeSetConstantR')
		i = node.ReadCrossRef(i, 'edges')
		i = node.ReadCrossRef(i, 'radius')
		i = node.ReadCrossRef(i, 'select')
		i = node.ReadCrossRef(i, 'continuityG1')
		if (self.version > 2018): i += 4
		return i

	def Read_AE101F92(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadUInt16A(i,   3, 'a2')
		if (self.version > 2016):
			i += 1
		else:
			i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 21, 'a3')
		i = node.ReadUInt32A(i,   3, 'a4')
		i = node.ReadFloat64A(i, 20, 'a5')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i,   6, 'a6')
		i = node.ReadFloat64A(i,  4, 'a7')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadFloat64A(i, 6, 'a8')
		i = node.ReadFloat64A(i, 15, 'a9')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat64A(i, 45, 'a10')
		node.isAttr = True
		return i

	def Read_B382A87C(self, node): # MatchedLoop
		i = self.ReadCntHdr3S(node, 'ProfileSelection')
		i = node.ReadCrossRef(i, 'face')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'number') # The numbber of the selection
		return i

	def Read_BA6E3112(self, node): # Fillet edge with variable radii
		i = self.ReadCntHdr3S(node, 'FilletEdgeVariableR')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'extrema') # start and end radius
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'additional') # additional radii -> FilletVariableRadius
		return i

	def Read_BB1DD5DF(self, node): # RDxVar
		i = self.ReadCntHdr3S(node, 'Parameter')
		i = node.ReadLen32Text16(i)
		i += 4
		i = node.ReadUInt32(i, 'valueNominal')
		i = node.ReadUInt32(i, 'valueModel')
		return i

	def Read_BB3762C8(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_BF8B8868(self, node):
		i = self.ReadCntHdr3S(node, 'FacesOffset')
		i = node.ReadCrossRef(i, 'faces')
		i = node.ReadCrossRef(i, 'offset')
		return i

	def Read_C1887310(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		if (len(node.get('lst0')) > 0):
			i = node.ReadSInt32(i, 's32_0')
		return i

	def Read_CA7AA850(self, node): # Fillet sets with variable radii
		i = self.ReadCntHdr3S(node, 'FxFilletEdgeSetsVariableR')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'sets')
		return i

	def Read_D2DA2CF0(self, node):
		i = self.ReadCntHdr3S(node)
		return i

	def Read_D524C30A(self, node):
		i = self.ReadCntHdr3S(node, 'FilletFullRoundSet')
		i = node.ReadCrossRef(i, 'facesSide1')
		i = node.ReadCrossRef(i, 'facesCenter')
		i = node.ReadCrossRef(i, 'facesSide2')
		return i

	def Read_D656B956(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_E0EA12F2(self, node): # ImageCollection
		i = self.ReadCntHdr3S(node, 'ImageCollection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'images')
		return i

	def Read_E558F428(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_EFF2257A(self, node):
		i = self.ReadCntHdr3S(node, 'SurfaceSelection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_F076940A(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		i = node.ReadUUID(i, 'uid')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_F338E84B(self, node):
		i = self.ReadCntHdr3S(node, 'PathAndSectionTwist')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'coords', 3)
		return i

	def Read_FA7C9C79(self, node):
		i = self.ReadCntHdr3S(node)
		i = node.ReadCrossRef(i, 'edgeItem')
		return i

	#######################
	# Index reference sections
	def ReadHeaderIndexRefs(self, node, typeName = None):
		i = self.ReadCntHdr3S(node, typeName)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'indexRefs')
		if (len(node.get('indexRefs')) > 0):
			i = node.ReadSInt32(i, 's32_0')
		else:
			node.set('s32_0', -1)
		return i

	def Read_375C6982(self, node): # EdgeItem
		i = self.ReadHeaderIndexRefs(node, 'EdgeItem')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_3BA63938(self, node):
		i = self.ReadHeaderIndexRefs(node)
		return i

	def Read_509FB5CC(self, node): # FaceItem
		i = self.ReadHeaderIndexRefs(node, 'FaceItem')
		return i

	#######################
	# Enum sections
	def ReadHeaderEnum(self, node, enumName=None, enumValues={}):
		if (enumName is None): enumName = node.typeName + '_Enum'
		i = self.ReadCntHdr3S(node, 'Enum')
		i = node.ReadSInt16(i, 'type')
		i = node.ReadEnum16(i, 'value', enumName, enumValues)
		i = self.skipBlockSize(i)
		return i

	def Read_06262CC1(self, node):
		i = self.ReadHeaderEnum(node, 'BendLocation', ['Centerline', 'Start', 'End'])
		return i

	def Read_0A077221(self, node):
		i = self.ReadHeaderEnum(node)
		return i

	def Read_0C7F6742(self, node):
		i = self.ReadHeaderEnum(node)
		return i

	def Read_115F4501(self, node): # Enum
		i = self.ReadHeaderEnum(node, 'RipType', ['SinglePoint', 'PointToPoint', 'FaceExtents'])
		return i

	def Read_15729F01(self, node):
		i = self.ReadHeaderEnum(node, 'SnapFitType', ['Beam', 'Clip'])
		return i

	def Read_2B3E0C72(self, node): # relief shape enum
		i = self.ReadHeaderEnum(node, 'Relief', {
			0: 'Round',	               # Bend
			1: 'Straight',             # Bend
			2: 'Tear',                 # Bend
#			3: ??? -> "Curved Shape Hole Pattern_CC.ipt".Bend3 -> only default value
			4: 'LinearWeld',           # Corner
			5: 'ArcWeld',              # Corner
#			6: ???
			7: 'LaserWeld',            # Corner
			100: 'RoundVertex',        # Corner
			101: 'SquareVertex',       # Corner
			102: 'Tear',               # Corner
			103: 'Trim2Bend',          # Corner
#			104: ???
#			105: ???
			106: 'RoundIntersection',  # Corner
			107: 'RoundTangent',       # Corner
			108: 'SquareIntersection', # Corner
#			301: ??? -> "Hard Drive Bracket.ipt".Corner1
#			302: ??? -> "SheetMetal/*.ipt".Corner1
#			303: ??? -> "electrical box.ipt".Corner3 (*Default*)
		})
		return i

	def Read_3061A607(self, node):
		return self.ReadHeaderEnum(node, 'BendTransition', {0: 'None', 1: 'Intersection', 2: 'straightLine', 3:'Arc', 4:'Trim2Bend'})

	def Read_31F02EED(self, node): # SweepProfileOrientationEnum {3F4CAC01-D038-490D-9061-9EF6DB007D48}
		return self.ReadHeaderEnum(node, 'SweepProfileOrientation', ['NormalToPath', 'ParallelToOriginalProfile'])

	def Read_3BCC6772(self, node):
		i = self.ReadHeaderEnum(node)
		i = self.skipBlockSize(i)
		return i

	def Read_3C6C1C6C(self, node): #
		return self.ReadHeaderEnum(node, 'LoftCondition', ['Free', 'Tangent', 'Angle', 'Smooth', 'SharpPoint', 'TangentToPlane', 'Direction'])

	def Read_43CD7C11(self, node): # HoleTypeEnum
		return self.ReadHeaderEnum(node, 'HoleType', ['Drilled', 'CounterSink', 'CounterBore', 'SpotFace'])

	def Read_4668C201(self, node): # HeadStyle
		return self.ReadHeaderEnum(node, 'HeadStyle', ['CounterBore', 'CounterSink', 'None'])

	def Read_4688EBA3(self, node):
		return self.ReadHeaderEnum(node)

	def Read_4FB10CB8(self, node):
		i = self.ReadHeaderEnum(node, 'EnumCoilType', ["PitchAndRevolution","RevolutionAndHeight","PitchAndHeight","Spiral"])
		i = node.ReadUInt32(i,'u32_0')
		return i

	def Read_5CB011E2(self, node): # SweepProfileScalingEnum {B791B822-BA66-44DD-BD99-09D2CFD9D307}
		return self.ReadHeaderEnum(node, 'SweepProfileScaling', ['XY', 'X', 'No'])

	def Read_5E50B969(self, node):
		return self.ReadHeaderEnum(node, 'FlipOffset', {0: 'Side1', 1: 'Side2', 2: 'Both'})

	def Read_637B1CC1(self, node):
		return self.ReadHeaderEnum(node, 'ApproximationOptimized', {0: True, 1: False})

	def Read_729ABE28(self, node): # PartFeatureOperationEnum {5E441A99-F1EE-472B-A356-383075A9303D}
		# extrusoins like pad, pocket, revolution, groove, ...
		return self.ReadHeaderEnum(node, 'PartFeatureOperation', ['*UNDEFINED*', 'NewBody', 'Cut', 'Join', 'Intersection', 'Surface'])

	def Read_7777785F(self, node):
		return self.ReadHeaderEnum(node, 'UnrollMethod', ['CentroidCylinder', 'CustomCylinder', 'DevelopedLength', 'NeutralRadius'])

	def Read_78F28827(self, node): # FilletTypeEnum
		return self.ReadHeaderEnum(node, 'FilletType', ['Edge', 'Face', 'FullRound'])

	def Read_7DAA0032(self, node): # ChamferDefinitionType enum
		i = self.ReadHeaderEnum(node, 'ChamferType', {0: 'Distance', 1: 'DistanceAndAngle', 2: 'TwoDistances'})
		i += 4 # skip 00 00 00 00
		return i

	def Read_8B2BE62E(self, node):
		return self.ReadHeaderEnum(node, 'ComputeType', {1: 'Identical', 2: 'AdjustToModel', 3: 'Optimized'})

	def Read_92637D29(self, node):
		return self.ReadHeaderEnum(node, 'ExtentType', ['0', 'Dimension', '2_Dimensions', 'Path', 'ToNext', 'All', 'FromTo', 'To'])

	def Read_9DA736B0(self, node):
		return self.ReadHeaderEnum(node)

	def Read_A29C84B7(self, node): # SweepTypeEnum {F2AAA202-7B46-45B9-963D-3DAFAB862AF5}
		return self.ReadHeaderEnum(node, 'SweepType', ['Path', 'PathAndGuideRail', 'PathAndGuideSurface', 'PathAndSectionTwist'])

	def Read_A2DF48D4(self, node): # FacetControl
		return self.ReadHeaderEnum(node, 'FacetControl', ['FacetDistance', 'CordTolerance', 'FacetAngle'])

	def Read_A3B0404C(self, node): # FeatureApproximationTypeEnum {C08F2078-986C-4043-A70B-643FA906968B}
		return self.ReadHeaderEnum(node, 'FeatureApproximationType', ['No', 'NeverTooThin', 'NeverTooThick', 'Mean'])

	def Read_AFD8A8E0(self, node):
		return self.ReadHeaderEnum(node, 'CornerGapType', {3: 'Symetric', 5: 'No Overlap/Seam', 6: 'Overlap', 7: 'ReverseOverlap'})

	def Read_B3A169E4(self, node): # ShellDirectionEnum {796E2726-2926-48C7-802A-5CAF83C3078D}
		return self.ReadHeaderEnum(node, 'ShellDirection', ['Inside', 'Outside', 'BothSides'])

	def Read_B8E19017(self, node): # SplitToolTypeEnum {F7304638-1AF5-4E5D-8704-D9DE52F1A8B4}
		return self.ReadHeaderEnum(node, 'SplitToolType', ['Path', 'WorkPlane', 'WorkSurface', 'SurfaceBody'])

	def Read_B8E19019(self, node): # SplitTypeEnum {E23EA9A1-7B9F-465F-A902-542F8E8A49EE}
		return self.ReadHeaderEnum(node, 'SplitType', ['SplitPart', 'SplitFaces', 'SplitBody' , 'TrimSolid'])

	def Read_C7A06AC2(self, node): # PartFeatureExtentDirectionEnum {D56C4513-7B52-4020-8FFB-E531EF8C69BF}
		return self.ReadHeaderEnum(node, 'PartFeatureExtentDirection', ['Positive', 'Negative', 'Symmetric', 'Angle'])

	def Read_CA70D2C6(self, node): # ThreadType
		return self.ReadHeaderEnum(node, 'ThreadType', ['Depth','Full Depth','Through'])

	def Read_CE59B7F5(self, node):
		return self.ReadHeaderEnum(node)

	def Read_CEFD3973(self, node):
		return self.ReadHeaderEnum(node)

	def Read_D4CCA953(self, node):
		return self.ReadHeaderEnum(node)

	def Read_D776DFD1(self, node):
		return self.ReadHeaderEnum(node)

	def Read_E0E3E202(self, node): # LoftTypeEnum {B6B5F55A-D2A1-4B96-A022-830865255CBF}
		return self.ReadHeaderEnum(node, 'LoftType', ['Rails', 'Centerline', 'AreaLoft', 'RegularLoft'])

	def Read_EA680672(self, node):
		return self.ReadHeaderEnum(node, 'TrimType')

	def Read_EBB23D6E(self, node): # SystemOfMeasureEnum {50131E62-D297-11D3-B7A0-0060B0F159EF}:
		return self.ReadHeaderEnum(node)

	def Read_EE767654(self, node):
		return self.ReadHeaderEnum(node, 'SculptSurfaceExtentDirection', ['Symmetric', 'Positive', 'Negative'])

	def Read_EF8279FB(self, node): # FaceMoveTypeEnum
		return self.ReadHeaderEnum(node, 'FaceMoveType', ['DirectionAndDistance', 'Planar', 'Free'])

	def Read_F4DAD621(self, node):
		return self.ReadHeaderEnum(node)

	#######################
	# 2D-sketch constraint sections
	def ReadHeaderConstraint2D(self, node, typeName = None):
		'''
		Read the header for 2D constraints
		'''
		i = self.ReadHeaderContent(node, typeName)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 'flags2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'group')
		if (self.version > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
		else:
			i = self.skipBlockSize(i, 2)
			node.set('lst0', {}, None)
			node.set('lst1', {}, None)
		i = node.ReadCrossRef(i, 'parameter')
		return i

	def Read_00ACC000(self, node): # TwoPointDistanceDimConstraint {C173A079-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Distance_Horizontal2D')
		i = node.ReadCrossRef(i, 'entity1')
		i = node.ReadCrossRef(i, 'entity2')
		i = self.skipBlockSize(i)
		node.delete('parameter')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_0DDD7C10(self, node): # SymmetryConstraint {8006A08E-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_SymmetryLine2D')
		i = node.ReadCrossRef(i, 'entity1')
		i = node.ReadCrossRef(i, 'entity2')
		i = node.ReadCrossRef(i, 'symmetry')
		return i

	def Read_0F177BB0(self, node): # GroundConstraint {8006A082-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Fix2D')
		i = node.ReadCrossRef(i, 'point')
		return i

	def Read_11058558(self, node): # OffsetDimConstraint {C173A077-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Distance2D')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'entity1')
		i = node.ReadCrossRef(i, 'entity2')
		i = node.ReadUInt32A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_2D(i, 'a1')
		i = node.ReadFloat64_2D(i, 'a2')
		return i

	def Read_21E870BF(self, node): # MidpointConstraint {8006A088-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadHeaderConstraint2D(node, 'Geometric_SymmetryPoint2D')
		i = node.ReadCrossRef(i, 'entity')
		i = node.ReadCrossRef(i, 'point')
		if (self.version > 2015): i += 4
		return i

	def Read_3683FF40(self, node): # TwoPointDistanceDimConstraint {C173A079-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Distance_Vertical2D')
		i = node.ReadCrossRef(i, 'entity1')
		i = node.ReadCrossRef(i, 'entity2')
		i = self.skipBlockSize(i)
		node.delete('parameter')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_442C7DD0(self, node): # EqualRadiusConstraint {8006A080-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadHeaderConstraint2D(node, 'Geometric_EqualRadius2D')
		i = node.ReadCrossRef(i, 'circle1')
		i = node.ReadCrossRef(i, 'circle2')
		return i

	def Read_4E4B14BC(self, node): # OffsetConstraint {8006A07C-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Offset2D')
		i = node.ReadCrossRef(i, 'entity1')
		i = node.ReadCrossRef(i, 'entity2')
		i = node.ReadCrossRef(i, 'entity3')
		i = node.ReadCrossRef(i, 'entity4')
		return i

	def Read_590D0A10(self, node): # TwoLineAngleDimConstraint {C173A07B-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Angle2Line2D')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'line1')
		i = node.ReadCrossRef(i, 'line2')
		i = node.ReadFloat64_2D(i, 'pos')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_5A9A7BE0(self, node): # CollinearConstraint {8006A076-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Collinear2D')
		i = node.ReadCrossRef(i, 'line1')
		i = node.ReadCrossRef(i, 'line2')
		i = node.ReadUInt16(i, 's16_0')
		return i

	def Read_64DA5250(self, node): # VerticalAlignConstraint {8006A094-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_AlignVertical2D')
		i = node.ReadCrossRef(i, 'point1')
		i = node.ReadCrossRef(i, 'point2')
		i = self.skipBlockSize(i)
		return i

	def Read_671BB700(self, node): # RadiusDimConstraint {C173A081-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Radius2D')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'circle')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_74DF96E0(self, node): # DiameterDimConstraint {C173A07F-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Diameter2D')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'circle')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_7A98AD0E(self, node): # TextBoxConstraint {037C3FDB-8A3C-443F-8CF6-993D3295335C}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_TextBox2D')
		i = node.ReadCrossRef(i, 'line1')
		i = node.ReadCrossRef(i, 'line2')
		i = node.ReadCrossRef(i, 'line3')
		i = node.ReadCrossRef(i, 'line4')
		i = node.ReadCrossRef(i, 'point1')
		i = node.ReadCrossRef(i, 'point2')
		i = node.ReadCrossRef(i, 'point3')
		i = node.ReadCrossRef(i, 'point4')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64(i, 'x')
		return i

	def Read_7C6D149E(self, node): # SplineFitPointConstraint {8006A07A-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadHeaderConstraint2D(node, 'Geometric_SplineFitPoint2D')
		i = node.ReadCrossRef(i, 'spline')
		i = node.ReadCrossRef(i, 'point')
		return i

	def Read_8F55A3C0(self, node): # HorizontalAlignConstraint {8006A086-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_AlignHorizontal2D')
		i = node.ReadCrossRef(i, 'point1')
		i = node.ReadCrossRef(i, 'point2')
		i = self.skipBlockSize(i)
		return i

	def Read_90874D94(self, node): # CoincidentConstraint {8006A074-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Coincident2D')
		i = node.ReadCrossRef(i, 'entity1')
		i = node.ReadCrossRef(i, 'entity2')
		return i

	def Read_90874D95(self, node): # ParallelConstraint {8006A08A-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Parallel2D')
		i = node.ReadCrossRef(i, 'line1')
		i = node.ReadCrossRef(i, 'line2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_90874D96(self, node): # PerpendicularConstraint {8006A08C-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Perpendicular2D')
		i = node.ReadCrossRef(i, 'line1')
		i = node.ReadCrossRef(i, 'line2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_90874D97(self, node): # TangentConstraint {0A73D068-AC6B-4B51-8B6D-913B90A77741}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Tangential2D')
		i = node.ReadCrossRef(i, 'entity1')
		i = node.ReadCrossRef(i, 'entity2')
		if (self.version > 2012):
			i += 4
		return i

	def Read_90874D98(self, node): # HorizontalConstraint {8006A084-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Horizontal2D')
		i = node.ReadCrossRef(i, 'line')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_90874D99(self, node): # VerticalConstraint {8006A092-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Vertical2D')
		i = node.ReadCrossRef(i, 'line')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_A789EEB0(self, node): # MajorRadius2D
		i = self.ReadHeaderConstraint2D(node, 'Dimension_RadiusA2D')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ellipse')
		return i

	def Read_B4964E90(self, node): # MinorRadius2
		i = self.ReadHeaderConstraint2D(node, 'Dimension_RadiusB2D')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ellipse')
		return i

	def Read_BF3B5C84(self, node): # ThreePointAngleDimConstraint {C173A07D-012F-11D5-8DEA-0010B541CAA8}:
		i = self.ReadHeaderConstraint2D(node, 'Dimension_Angle3Point2D')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'point1')
		i = node.ReadCrossRef(i, 'point2')
		i = node.ReadCrossRef(i, 'point3')
		i = node.ReadFloat64_2D(i, 'pos')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_C681C2E0(self, node): # EqualLengthConstraint {8006A07E-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_EqualLength2D')
		i = node.ReadCrossRef(i, 'line1')
		i = node.ReadCrossRef(i, 'line2')
		return i

	def Read_E1108C00(self, node): # ConcentricConstraint {8006A078-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadHeaderConstraint2D(node, 'Geometric_Radius2D')
		i = node.ReadCrossRef(i, 'entity')
		i = node.ReadCrossRef(i, 'center')
		return i

	def Read_FBDB891F(self, node): # PatternConstraint {C173A073-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderConstraint2D(node, 'Geometric_PolygonEdge2D')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'center')
		i = node.ReadCrossRef(i, 'polygonCenter1')
		i = node.ReadCrossRef(i, 'polygonCenter2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	#######################
	# 3D-sketch constraint sections
	def ReadHeaderConstraint3D(self, node, typeName = None):
		'''
		Read the header for 3D constraints
		'''
		i = self.ReadHeaderContent(node, typeName)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 'flags2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'group')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'sketch')
		if (self.version > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_FLOAT64_, 'lst2')
		else:
			i = self.skipBlockSize(i)
		return i

	def Read_0E8C5360(self, node): # SplineHandle3D
		i = self.ReadHeaderConstraint3D(node, 'SplineHandle3D')
		return i

	def Read_10B6ADEF(self, node): # LineLengthDimConstraint3D {04A196FD-3FBB-43EF-9A79-2735B3B99214}
		i = self.ReadHeaderConstraint3D(node, 'Dimension_Length3D')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'fxDims')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_2574C505(self, node): # ConcentricConstraint3D {EF118F14-C2D2-4DF4-910A-3438FBEC2817}
		i = self.ReadHeaderConstraint3D(node, 'Geometric_Radius3D')
		return i

	def Read_33EC1003(self, node): # ParallelConstraint3D {73919DC1-220E-4EC9-B716-072D6046A3AD}
		i = self.ReadHeaderConstraint3D(node, 'Geometric_Parallel3D')
		if (self.version > 2016): i += 4
		return i

	def Read_63266191(self, node): # PerpendicularConstraint3D {2035E584-09E7-4B18-9698-014DEF44B10E}
		i = self.ReadHeaderConstraint3D(node, 'Geometric_Perpendicular3D')
		return i

	def Read_6A3EEA31(self, node): # Angle2PlanesDimConstraint {????}
		i = self.ReadHeaderConstraint3D(node, 'Dimension_Angle2Planes3D')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_7457BB19(self, node): # TangentConstraint3D {0456FF0D-196E-4C72-989D-D86E3DD32955}
		i = self.ReadHeaderConstraint3D(node, 'Geometric_Tangential3D')
		if (self.version < 2013): i += 1
		i = node.ReadCrossRef(i, 'parameter')
		if (self.version < 2013): i += 1
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_C5538931(self, node): # CoincidentConstraint3D {843FEEB5-A0EF-4C5B-8939-4F9B574119D8}
		i = self.ReadHeaderConstraint3D(node, 'Geometric_Coincident3D')
		if (self.version > 2016): i += 4
		return i

	def Read_D13107FE(self, node): # CollinearConstraint3D {E8BE2118-716C-40FD-8BC0-2517B253E4F9}
		i = self.ReadHeaderConstraint3D(node, 'Geometric_Collinear3D')
		return i

	def Read_DE818CC0(self, node): # BendConstraint3D {AE27E3D2-63C8-4D39-B2CA-A6387AE5D7B3}
		i = self.ReadHeaderConstraint3D(node, 'Geometric_Bend3D')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_E8D30910(self, node): # SmoothConstraint3D  {281176E3-4EDC-4F4E-9804-6716B7B9059D}
		i = self.ReadHeaderConstraint3D(node, 'Geometric_Smooth3D')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	##########################
	# Content + S l S S sections
	def ReadHeadersS32ss(self, node, typeName = None, name = 'next'):
		i = self.ReadHeaderContent(node, typeName, name)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_029DAD70(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'line')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_03EF48B3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = self.skipBlockSize(i)
		i = self.ReadClassInfo(node, i, 'plane')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		i = self.skipBlockSize(i)
		return i

	def Read_065FFFB3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
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
		i = self.skipBlockSize(i, 2)
		return i

	def Read_07910C0B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'point')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'line')
		i = node.ReadCrossRef(i, 'plane')
		i = node.ReadFloat64A(i, 5, 'a0')
		return i

	def Read_07B89A4F(self, node): # Bend Transition Radius Proxy
		i = self.ReadHeadersS32ss(node, ' BendTransitionProxy')
		i = node.ReadCrossRef(i, 'type')
		i = node.ReadCrossRef(i, 'ref_3')       # ref to 265034E9
		i = node.ReadCrossRef(i, 'radius')
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

	def Read_0C12CBF2(self, node):
		i = self.ReadHeadersS32ss(node, 'LoftProfileCondition')
		i = node.ReadCrossRef(i, 'section')
		i = node.ReadCrossRef(i, 'impact')
		i = node.ReadCrossRef(i, 'angle')
		i = node.ReadCrossRef(i, 'plane')
		return i

	def Read_0C48B860(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = self.ReadClassInfo(node, i, 'body')
		i = node.ReadUInt32(i, 'wireIndex')
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		i = self.skipBlockSize(i)
		return i

	def Read_0D0F9548(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'mapping')
		return i

	def Read_0D28D8C0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'plane1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'plane2')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_13F4E5A3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
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
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'varRDx')
		return i

	def Read_18951917(self, node): # RevolutionTransformation
		i = self.ReadHeadersS32ss(node, 'RevolutionTransformation')
		i = node.ReadCrossRef(i, 'ref2D')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'ref3D')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_18D844B8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_1A26FF54(self, node):
		i = self.ReadHeadersS32ss(node)
		if (self.version > 2020):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_LIST2_XREF_, 'lst0')
		else:
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_LIST2_XREF_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'fx')
		return i

	def Read_1B48AD11(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_1CB24874(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_1D92FF4F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'parameter')
		i = self.skipBlockSize(i)
		if (self.version > 2011):
			i += 8+4 # F64 + U32
		return i

	def Read_1EF28758(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_2510347F(self, node): # TextBox {A907AE99-A78F-11D5-8DF8-0010B541CAA8}
		i = self.ReadHeadersS32ss(node, 'Text2D')
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadCrossRef(i, 'text')
		i = node.ReadUInt32A(i, 2, 'a0')
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

	def Read_262EA00C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		if (self.version > 2017): i += 4
		return i

	def Read_26445303(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_27ECB60E(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadList4(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		if (self.version < 2013):
			i = node.ReadUInt32(i, 'u32_1')
			i = self.skipBlockSize(i)
			i = node.ReadList6(i, importerSegNode._TYP_MAP_REF_REF_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_X_REF_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_REF_REF_, 'lst2')
			cnt, i = getUInt16(node.data, i)
			lst = []
			for j in range(cnt):
				ref, i = self.ReadNodeRef(node, i, [j, 0], importerSegNode.REF_CROSS, 'lst3')
				txt, i = getLen32Text16(node.data, i)
				u8, i  = getUInt8(node.data, i)
				lst.append([ref, txt, u8])
			node.set('lst3', lst, VAL_REF)
			i = node.ReadUInt32(i, 'u32_2')
		else:
			i = node.ReadChildRef(i, 'ref_6')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_2AB534B2(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		return i

	def Read_2B1F0409(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_2B48CE72(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_2E692E29(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'surface')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_2FA5918B(self, node): # Mesh part
		i = self.ReadHeadersS32ss(node, 'MeshPart')
		i = node.ReadCrossRef(i, 'fx')
		return i

	def Read_317CDB03(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt16(i, 'u16_1')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_31DBA503(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadChildRef(i, 'document')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadChildRef(i, 'fx')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadChildRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'ref_6')
		return i

	def Read_3384E515(self, node): # Geometric_Custom3D
		i = self.ReadHeadersS32ss(node, 'Geometric_Custom3D')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		if (self.version > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst2')
		else:
			i = self.skipBlockSize(i)
			node.set('lst1', {}, None)
			node.set('lst2', {}, None)
		i = node.ReadLen32Text16(i)
		return i

	def Read_339807AC(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_33F69125(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt16(i, 'u16_0')
		if (node.get('u16_0') == 0x200):
			i = node.ReadUInt32(i, 'u32_3')
			i = node.ReadLen32Text16(i)
			i = node.ReadUInt16(i, 'u16_1')
		else:
			i = node.ReadUInt32(i, 'u32_3')
			i = node.ReadChildRef(i, 'ref_2')
		i = self.skipBlockSize(i, 2)
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

	def Read_38C2654E(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUUID(i, 'uid')
		i = self.skipBlockSize(i)
		return i

	def Read_38C74735(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'sketch')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'direction')
		return i

	def Read_3A083C7B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'transformation')
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
		if (self.version > 2011):
			i = node.ReadCrossRef(i, 'ref_9')
			i = node.ReadCrossRef(i, 'ref_10')
			i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_3A7CFA26(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'corner') # ref to CornerSeam
		i = node.ReadCrossRef(i, 'reliefSize')
		i = node.ReadCrossRef(i, 'gapSize')
		i = node.ReadCrossRef(i, 'reliefType')
		i = node.ReadCrossRef(i, 'gapType')
		i = node.ReadCrossRef(i, 'relief_2')
		i = node.ReadCrossRef(i, 'jacobiRadius')
		return i

	def Read_3AE9D8DA(self, node): # Sketch3D {E4C09561-E779-4A00-A835-E8D43E08A290}
		i = self.ReadHeadersS32ss(node, 'Sketch3D')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'numEntities')
		i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32_2D(i, 'a0')
		if (self.version > 2011):
			#i = node.ReadFloat64A(i, 6, 'a1')
			i += 6*8
		return i

	def Read_3D64CCF0(self, node): # Sketch2DPlacementPlane
		i = self.ReadHeadersS32ss(node, 'Sketch2DPlacementPlane')
		i = node.ReadCrossRef(i, 'transformation1')
		i = node.ReadCrossRef(i, 'transformation2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 7, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'plane')
		return i

	def Read_3E710428(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_3F36349F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'transformation')
		return i

	def Read_3F3634A0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadList4(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		if (self.version < 2013):
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
			node.set('lst5', lst5)
			i = node.ReadCrossRef(i, 'ref_5')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst6')
			i = node.ReadUInt8(i, 'u8_1')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst7')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst8')
			i = node.ReadCrossRef(i, 'ref_6')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst9')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst10')
			i = node.ReadUInt8(i, 'u8_2')
			i = node.ReadUInt16(i, 'u16_0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst11')
		else:
			i = node.ReadChildRef(i, 'ref_5')
			if (self.version > 2016): i += 4
		return i

	def Read_4AC78A71(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'plane')
		b, i = getBoolean(node.data, i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'direction')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2017): i += 4
		i = self.skipBlockSize(i)
		b, i = getBoolean(node.data, i)
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadCrossRef(i, 'transformation')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2017): i += 4
		i = self.skipBlockSize(i)
		return i

	def Read_4D223225(self, node):
		i = self.ReadHeadersS32ss(node)
		return i

	def Read_4F240E1C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'group')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'sketch')
		return i

	def Read_4FD0DC2A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'section')
		i = node.ReadCrossRef(i, 'boundaryPatch')
		return i

	def Read_51C016F7(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i = self.ReadClassInfo(node, i, 'body')
		i = node.ReadUInt32(i, 'wireIndex')
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		i = self.skipBlockSize(i)
		return i

	def Read_526B3F3D(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_53DCDF19(self, node):
		i = self.ReadHeadersS32ss(node, 'FaceBendCollection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'bends')
		return i

	def Read_55279EE0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_572DBC7C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		i = self.skipBlockSize(i)
		return i

	def Read_574EF622(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'coords', 3)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_578432A6(self, node): # NMx_FFColor_Entity
		i = self.ReadHeadersS32ss(node, 'NMx_FFColor_Entity', 'creator')
		i = node.ReadCrossRef(i, 'fx')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i)
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
		i = node.ReadCrossRef(i, 'plane')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'enty1')
		i = node.ReadCrossRef(i, 'enty2')
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

	def Read_5CB9BB58(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'sketch')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_5D0B89FE(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'reliefWidth')
		i = node.ReadCrossRef(i, 'reliefDepth')
		i = node.ReadCrossRef(i, 'bendType')    # Relief
		i = node.ReadCrossRef(i, 'minRemnant')
		i = node.ReadCrossRef(i, 'definition')  # ref to 96058864
		i = node.ReadCrossRef(i, 'seamGap')
		return i

	def Read_5D93312C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_5E040F0D(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_603428AE(self, node, typeName = None):
		i = self.ReadHeadersS32ss(node, typeName)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'parts')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'proxy')
		return i

	def Read_60406697(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
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

	def Read_64DE16F3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'entity')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'edge')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_668BF011(self, node):
		i = self.ReadHeadersS32ss(node)
		return i

	def Read_6B6A06E7(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_6BF0A0AA(self, node): # Spape of flange
		i = self.ReadHeadersS32ss(node, 'FlangeShape')
		i = node.ReadCrossRef(i, 'extent')
		i = node.ReadCrossRef(i, 'angle')
		i = node.ReadCrossRef(i, 'thickness')
		i = node.ReadCrossRef(i, 'flipDir')
		i = node.ReadCrossRef(i, 'reliefWidth')
		i = node.ReadCrossRef(i, 'ref_2')
		if (self.version < 2016):
			i = node.ReadCrossRef(i, 'body')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'radius')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'plane')
		i = node.ReadCrossRef(i, 'direction')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_A')
		if (self.version > 2015):
			i = node.ReadCrossRef(i, 'body')
		if (self.version > 2020): i += 4 # skip 00 00 00 00
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

	def Read_6F7A6F9C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt16(i, 'u16_0')
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
		if (self.version > 2017): i += 8
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadCrossRef(i, 'ref_A')
		i = node.ReadCrossRef(i, 'ref_B')
		return i

	def Read_720E6C90(self, node):# Fillets variable radius position definition
		i = self.ReadHeadersS32ss(node, 'FilletIntermediateRadiusDef')
		i = node.ReadCrossRef(i, 'edge')
		i = node.ReadCrossRef(i, 'param')  # Parameter that controls the position of the point along the edge.
		i = node.ReadCrossRef(i, 'radius')
		i = node.ReadCrossRef(i, 'def')    # -> FilletVariableRadius
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
				ref, i = self.ReadNodeRef(node, i, [r, c], importerSegNode.REF_CHILD, 'lst2')
				tmp.append(ref)
			lst.append(tmp)
		node.set('lst2', lst, VAL_REF)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadSInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadUInt16(i, 'u16_1')
		if (self.version > 2024): i += 14 # skip 00..00
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadCrossRef(i, 'ref_9')
		i = node.ReadFloat64_2D(i, 'a1')
		return i

	def Read_7325290E(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'body')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'entity')
		return i

	def Read_7325290F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'body')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
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
		i = node.ReadCrossRef(i, 'direction')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'entity')
		i = node.ReadCrossRef(i, 'transformation')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst0', 2)
		i = node.ReadUInt8(i, 'u8_0')
		if (node.get('u8_0') != 0):
			i = node.ReadSInt32(i, 's32_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'plane')
		return i

	def Read_74E6F48A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'plane1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'entity')
		i = node.ReadCrossRef(i, 'plane2')
		i = node.ReadCrossRef(i, 'parameter')
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
		i = node.ReadCrossRef(i, 'sketch')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		return i

	def Read_76EC185B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_778752C6(self, node): # CurveToSurfaceProjection
		i = self.ReadHeadersS32ss(node, 'CurveToSurfaceProjection')
		i = node.ReadCrossRef(i, 'sketch')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'direction')
		if (self.version > 2016): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = self.Read2RefList(node, i, 'lst0', importerSegNode.REF_CHILD, importerSegNode.REF_CROSS)
#		i = node.ReadChildRef(i, 'ref_3')
#		i = node.ReadCrossRef(i, 'ref_4')
#		i = node.ReadChildRef(i, 'ref_5')
#		i = node.ReadCrossRef(i, 'point')
#		i = node.ReadCrossRef(i, 'ref_6')
#		i = node.ReadCrossRef(i, 'ref_7')
		return i

	def Read_7911B59E(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadChildRef(i, 'ref_5')
		return i

	def Read_9F58C23C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'section')
		i = node.ReadCrossRef(i, 'boundaryPatch')
		if (self.version > 2018):
			i = node.ReadCrossRef(i, 'bodies')
		return i

	def Read_A71E4CB3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_0')
		return  i

	def Read_8324D282(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUUID(i, 'uid2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadSInt32(i, 's32_2')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.skipBlockSize(i, 2)
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_83D31932(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'line')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'point1')
		i = node.ReadCrossRef(i, 'point2')
		return i

	def Read_841B40DB(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_8AF0E725(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'entity')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'transformation')
		return i

	def Read_8AFFBE5A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'plane')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'line1')
		i = node.ReadCrossRef(i, 'line2')
		return i

	def Read_8F41FD24(self, node): # EndOfFeatures {A89E388A-13C9-4FFA-B777-9C0E1C81F136}
		i = self.ReadHeadersS32ss(node, 'EndOfFeatures')
		return i

	def Read_8F02799B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'entity')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_2D(i, 'v0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 2, 'a_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		return i

	def Read_8FEC335F(self, node):
		# TODO: constraint together with Geometric_TextBox2D and DC93DB08 <-> Hairdryer: Sketch47, Sketch48, Speedometer: Sketch3, Sketch10
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'point1')
		i = node.ReadCrossRef(i, 'line1')
		i = node.ReadCrossRef(i, 'line2')
		i = node.ReadCrossRef(i, 'line3')
		i = node.ReadCrossRef(i, 'line4')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'point2')
		return i

	def Read_90874D11(self, node): # PlanarSketch {2C16787F-83FF-11D4-8DDB-0010B541CAA8}
		i = self.ReadHeadersS32ss(node, 'Sketch2D')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'numEntities')
		i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'direction')
		i = node.ReadUInt32A(i, 2, 'a0')
		if (self.version > 2012):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		return i

	def Read_90874D21(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i,    'ref_1')
		i = node.ReadCrossRef(i,    'transformation')
		i = node.ReadCrossRef(i,    'parameter1')
		i = node.ReadCrossRef(i,    'parameter2')
		i = node.ReadCrossRef(i,    'parameter3')
		return i

	def Read_90874D23(self, node): # Sketch2DPlacement
		i = self.ReadHeadersS32ss(node, 'Sketch2DPlacement')
		i = node.ReadCrossRef(i, 'transformation1')
		i = node.ReadCrossRef(i, 'transformation2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'direction')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadCrossRef(i, 'transformation3')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst0', 2)
		i = node.ReadUInt8(i, 'u8_0')
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
		if (node.get('u16_0') == 0x200):
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadLen32Text16(i)
			i = node.ReadUInt16(i, 'u16_1')
		else:
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadChildRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		return i

	def Read_90874D62(self, node): # Group2D
		i = self.ReadHeadersS32ss(node, 'Group2D')
		i = node.ReadSInt32(i, 's32_1')
		i = self.skipBlockSize(i, 3)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'constrains')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'entries')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_5A7CB7BF(self, node):
		# new since 2025
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16A(i, 2,'a1')
		return i

	def Read_90874D74(self, node): # ObjectCollectionDef
		i = self.ReadHeadersS32ss(node, 'ObjectCollectionDef')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'items')
		i = node.ReadCrossRef(i, 'collection') # -> ObjectCollection
		return i

	def Read_90874D91(self, node): # Feature
		i = self.ReadHeadersS32ss(node, 'Feature')
		i = node.ReadUInt32(i, 'outlineItem')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
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

	def Read_9A444CCC(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_9D71D698(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_9E9570C8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_A0564E4F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList8(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		return i

	def Read_A1D74A3C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_A200FB76(self, node):
		i = self.ReadHeadersS32ss(node)
		return i

	def Read_A244457B(self, node): # edge pattern direction
		i = self.ReadHeadersS32ss(node, 'DirectionEdge')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'entity')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadFloat64_3D(i, 'dir')
		i = node.ReadFloat64_3D(i, 'point') # should be same values as entity!
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'edge')
		i = node.ReadCrossRef(i, 'face')
		return i

	def Read_A31E29E0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList8(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'owner')
		i = node.ReadCrossRef(i, 'body')
		i = self.skipBlockSize(i)
		return i

	def Read_A5977BAA(self, node): # pattern direction normal to face
		i = self.ReadHeadersS32ss(node, 'DirectionFace')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'entity')
		i = self.ReadEdgeList(node, i)
		i = node.ReadFloat64_3D(i, 'point')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'face')
		return i

	def Read_A6118E11(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'plane')
		i = self.skipBlockSize(i)
		return i

	def Read_A7175431(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_A96B5993(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'thickness')
		i = node.ReadCrossRef(i, 'radius')
		i = node.ReadCrossRef(i, 'definition')
		i = node.ReadCrossRef(i, 'reliefWidth')
		i = node.ReadCrossRef(i, 'minRemnant')
		i = node.ReadCrossRef(i, 'ref_2')       # bool
		i = node.ReadCrossRef(i, 'ref_3')       # bool
		return i

	def Read_ABC2E4ED(self, node):
		i = self.ReadHeadersS32ss(node)
		return i

	def Read_AD416CEA(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'face')
		i = node.ReadCrossRef(i, 'edge')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'direction')
		i = node.ReadUInt8(i, 'u8_1')
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

	def Read_B5D4DEE6(self, node):
		i = self.ReadHeadersS32ss(node)
		i = self.skipBlockSize(i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = self.ReadNodeRefs(node, i, 'lst2', importerSegNode.REF_CROSS)
		i = node.ReadCrossRef(i, 'center')
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadCrossRef(i, 'angle1')
		i = node.ReadCrossRef(i, 'polygonCenter')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'count')
		i = node.ReadFloat64(i, 'angle2')
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
		i = self.Read2RefList(node, i, 'lst0')
		return i

	def Read_BE175765(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'fx')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.ReadU32RefList(node, i, 'params')
		return i

	def Read_BFB5EB93(self, node): # DerivedOccFeature
		i = self.ReadHeadersS32ss(node, 'DerivedOccFeature')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		if (self.version < 2013):
			i = node.ReadUInt8A(i, 2, 'a0')
		else:
			i = node.ReadChildRef(i, 'ref_1')
			i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_C3183C48(self, node): #
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'point')
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

	def Read_C6E21E1A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_C9A8BC23(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadSInt32(i, 'flags2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadCrossRef(i, 'dir')
		i = node.ReadCrossRef(i, 'curve')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'dcx')
		return i

	def Read_CADC79F0(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_CB6C0A56(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_CD56EAAA(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'point')
		return i

	def Read_CD7C1C53(self, node): # DerivedOccDataCollector
		i = self.ReadHeadersS32ss(node, 'DerivedOccDataCollector')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_CE7F937A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'line')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadCrossRef(i, 'plane')
		return i

	def Read_CFB519C2(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_D035D8A8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_D1DE893F(self, node):
		i = self.ReadHeadersS32ss(node)
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		i = node.ReadCrossRef(i, 'ref_0')
		return i

	def Read_D2D440C0(self, node): # pattern direction along path
		i = self.ReadHeadersS32ss(node, 'DirectionPath')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'entity')
		i = node.ReadCrossRef(i, 'document')
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
		i = node.ReadFloat64_3D(i, 'point')

		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_4')
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

	def Read_D5F9E1E0(self, node): # ContourRollDef
		i = self.ReadHeadersS32ss(node, 'ContourRollDef')
		i = node.ReadCrossRef(i, 'thickness')
		i = node.ReadCrossRef(i, 'profile')
		i = node.ReadCrossRef(i, 'asm')
		i = node.ReadCrossRef(i, 'axis')
		i = node.ReadCrossRef(i, 'bendRadius')
		i = node.ReadCrossRef(i, 'offsetSide')
		i = node.ReadCrossRef(i, 'rolledDir')
		i = node.ReadCrossRef(i, 'solid')
		return i

	def Read_DA4970B5(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst')
		i = node.ReadCrossRef(i,'profileSelection')
		i = self.skipBlockSize(i)
		return i

	def Read_DB04EB11(self, node): # Group3D
		i = self.ReadHeadersS32ss(node, 'Group3D')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 3)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		if (self.version > 2016):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		else:
			node.set('lst1', {}, VAL_REF)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst2')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_DEB6F91B(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_DED39DA8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst1')
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2015):
			i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_DFB2586A(self, node): # IntersectionCurve
		i = self.ReadHeadersS32ss(node, 'IntersectionCurve')
		i = node.ReadCrossRef(i, 'ref_1a')
		i = node.ReadCrossRef(i, 'ref_1b')
		i = node.ReadCrossRef(i, 'ref_1c')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_2a')
		i = node.ReadCrossRef(i, 'ref_2b')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadCrossRef(i, 'ref_4')
		i = self.Read2RefList(node, i, 'lst0')
		return i

	def Read_E28A0597(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_E2C566C3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadBoolean(i, 'b_0')
		return i

	def Read_E4E57EF8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'Curves')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'ref_8')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadBoolean(i, 'b_0')
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

	def Read_E562B07C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'plane1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'plane2')
		i = node.ReadCrossRef(i, 'value')
		return i

	def Read_E94FB6D9(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'transformation1')
		i = node.ReadCrossRef(i, 'transformation2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'transformation3')
		return i

	def Read_E9821C66(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
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
		if (self.version > 2015):
			i = node.ReadCrossRef(i, 'ref_A')
		return i

	def Read_EBA98FD3(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_EC2D4C66(self, node): # MeshFolder
		i = self.ReadHeadersS32ss(node, 'MeshFolder')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'meshes')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version < 2017):
			i = node.ReadLen32Text16(i, 'meshId')
			i = node.ReadLen32Text16(i, 'meshTyp')
		return i

	def Read_EE09D055(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_EE792053(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i, 2)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_4')
		return i

	def Read_EFE47BB4(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_F0677096(self, node):
		i = self.ReadHeadersS32ss(node)
		return i

	def Read_F2568DCF(self, node): # BlockInserts
		i = self.ReadHeadersS32ss(node, 'BlockInserts')
		i = node.ReadCrossRef(i, 'group')
		if (self.version > 2012):
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst1')
		else:
			node.set('lst0', {})
			node.set('lst1', {})
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
		return i

	def Read_F27502FD(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_F393AC92(self, node):
		i = self.ReadHeadersS32ss(node, 'Scene')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'doc')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 4, 'a0')
		i = node.ReadFloat64A(i, 11, 'a1')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadChildRef(i, 'ref_4')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadFloat32A(i, 4, 'a2')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u0_0')
		i = node.ReadUInt32(i, 'u32_4')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadUInt16(i, 'u16_1')
		i = self.skipBlockSize(i)
		if (self.version > 2016):
			i = node.ReadChildRef(i, 'ref_5')
			i = node.ReadChildRef(i, 'ref_6')
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

	def Read_F778A7DC(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst_1')
		i = self.ReadClassInfo(node, i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2017): i += 4
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		b, i = getBoolean(node.data, i)
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadCrossRef(i, 'ref_2')
		if (not b):
			i = node.ReadLen32Text16(i, 'txt2')
			i = node.ReadLen32Text16(i, 'txt3')
			i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16(i, 'u16_2')
		if (self.version > 2017): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst_2')
		return i

	def Read_F9DB9290(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'plane1')
		i = node.ReadCrossRef(i, 'entity1')
		i = node.ReadCrossRef(i, 'plane2')
		i = node.ReadCrossRef(i, 'entity2')
		if (self.version > 2014):
			i = node.ReadCrossRef(i, 'entity3')
#			i = node.ReadFloat64(i, 'x')
		return i

	def Read_FABE1977(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_LIST_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'transformation')
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

	def Read_FEB0D977(self, node): # Representation3DPoint
		i = self.ReadHeadersS32ss(node, 'Representation3DPoint')
		i = node.ReadCrossRef(i, 'point2D')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'point3D')
		return i

	def Read_FF15793D(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'entity1')
		i = node.ReadCrossRef(i, 'transformation')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'entity2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_FFD270B8(self, node): # SketchFragment
		i = self.ReadHeadersS32ss(node, 'SketchFragment')
		i = node.ReadUUID(i, 'uid')
		return i

	##########################
	# Features
	def ReadHeaderFeature(self, node, name): # if changing the name => change importerFreeCAD.Create_Fx... accordingly!
		i = self.ReadHeadersS32ss(node, 'Feature')
		node.set('Feature', name)
		return i

	def Read_03CC1996(self, node):
		i = self.ReadHeaderFeature(node, 'LoftedFlange')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'outlineItem')
		return i

	def Read_1A21362E(self, node):
		i = self.ReadHeaderFeature(node, 'Mesh')
		if (self.version > 2016):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst3')
		else:
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadLen32Text16(i, 'meshId')
			i = node.ReadLen32Text16(i, 'meshTyp')
			i = node.ReadUInt8(i, 'u8_0')
			i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
			i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst2')
			i = node.ReadUInt32A(i, 3, 'a0')
			i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_1F6D59F6(self, node): # DirectEditFeature {602389D5-6C6A-4368-A6F2-47D54FA1FBA4}
		i = self.ReadHeaderFeature(node, 'DirectEdit')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_3902E4D1(self, node): # FxRefold
		i = self.ReadHeaderFeature(node, 'Refold')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'refolds')
		i = node.ReadUInt32(i, 'u32_0')
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
		if (self.version > 2011):
			i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_7F936BAA(self, node): # DecalFeature {9C693BB0-7C99-4D06-961E-99936273C492}
		i = self.ReadHeaderFeature(node, 'Decal')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'images')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'sketch')
		return i

	def Read_A03874B0(self, node): # ContourFlangeFeature {2390C0D0-A03F-4526-B4B1-7FBFC3C9A66E}
		i = self.ReadHeaderFeature(node, 'FlangeContour')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_A37B053C(self, node):
		i = self.ReadHeaderFeature(node, 'PatternSketchDriven')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadCrossRef(i, 'transformation')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'fxDims')
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
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadCrossRef(i, 'ref_20')
		i = node.ReadCrossRef(i, 'ref_21')
		i = node.ReadCrossRef(i, 'ref_22')
		i = node.ReadCrossRef(i, 'ref_23')
		i = node.ReadCrossRef(i, 'ref_24')
		i = node.ReadFloat64_2D(i, 'pos')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'coords', 3)
		return i

	def Read_C098D3CF(self, node): # PunchToolFeature {0DC3C610-F23D-44AD-B688-A47CAB5B04CB}
		i = self.ReadHeaderFeature(node, 'PunchTool')
		i = node.ReadUInt32(i, 'outlineItem')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_C2EF1CC7(self, node):
		i = self.ReadHeaderFeature(node, 'NonParametricBase')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_C3DDDC08(self, node): # FlangeFeature {5475DDC1-3397-46D6-A7A3-E1C34FA5BD7E}
		i = self.ReadHeaderFeature(node, 'Flange')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_C4C14B90(self, node): # FaceFeature {600E3CEE-1600-4999-ACE4-7CED6483BECE}
		i = self.ReadHeaderFeature(node, 'Face')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		return i

	def Read_F3DBA9D8(self, node): # FxUnfold
		i = self.ReadHeaderFeature(node, 'Unfold')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'unfolds')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	#######################
	# pattern sections
	def ReadHeaderPattern(self, node, patternName):
		i = self.ReadHeaderFeature(node, patternName)
		i = node.ReadUInt32(i, 'outlineItem')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'properties')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'participants')
		properties = node.get('properties')
		for j in range(0, 6):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
			properties.append(ref)
		i = node.ReadUInt8(i, 'u8_0')
		return properties, i

	def Read_06977131(self, node): # PolarPatternFeature {7BB0E824-4852-4F1B-B43C-7F729A3D7EB8}
		properties, i = self.ReadHeaderPattern(node, 'PatternPolar')
		for j in range(6, 12):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
			properties.append(ref)
		if (self.version > 2016):
			i += 24
		else:
			i = self.skipBlockSize(i)
		for j in range(12, 18):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
			properties.append(ref)
		if (self.version > 2016):
			for j in range(18, 20):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
				properties.append(ref)
		return i

	def Read_20673244(self, node): # RectangularPatternFeature {58B0C13D-27CC-4F06-93FD-0524B69E6578}
		properties, i = self.ReadHeaderPattern(node, 'PatternRectangular')
		for j in range(6, 12):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
			properties.append(ref)
		i = self.skipBlockSize(i)
		for j in range(12, 26):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
			properties.append(ref)
		if (self.version > 2016):
			for j in range(26, 32):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
				properties.append(ref)
		return i

	def Read_FAD9A9B5(self, node): # MirrorFeature {12BF1F8A-5679-468F-A820-DA5532624CEA}
		properties, i = self.ReadHeaderPattern(node, 'Mirror')
		for j in range(6, 11):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
			properties.append(ref)
		if (self.version > 2016):
			i += 24 #???
		else:
			i = self.skipBlockSize(i)
		for j in range(11, 13):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
			properties.append(ref)
		return i

	#######################
	# bend extend sections
	def ReadHeaderBendExtent(self, node, typ):
		i = self.ReadHeadersS32ss(node, u"BendExtend%s" %(typ))
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'surface')
		i = node.ReadCrossRef(i, 'edgeItem')
		i = node.ReadCrossRef(i, 'width')
		i = node.ReadCrossRef(i, 'direction')
		i = node.ReadCrossRef(i, 'thickness')
		i = node.ReadCrossRef(i, 'reliefWidth')
		i = node.ReadCrossRef(i, 'edge')
		if (self.version > 2017):
			i = node.ReadCrossRef(i, 'body')
			i += 4
		else:
			i = self.skipBlockSize(i)
		return i

	def Read_30892938(self, node): # Bend extent type 'Width'
		i = self.ReadHeaderBendExtent(node, 'Width')
		i = node.ReadCrossRef(i, 'point')       # reference point for offset
		i = node.ReadCrossRef(i, 'offset1')     # length for the offset
		i = node.ReadCrossRef(i, 'extentWidth') # extent witdth
		i = node.ReadCrossRef(i, 'ref_3')       # bool
		i = node.ReadCrossRef(i, 'ref_4')       # bool
		return i

	def Read_843A19FE(self, node): # Bend extent type 'Offset'
		i = self.ReadHeaderBendExtent(node, 'Offset')
		i = node.ReadCrossRef(i, 'p1')      # reference point for 1st offset
		i = node.ReadCrossRef(i, 'p2')      # reference point for 2nd offset
		i = node.ReadCrossRef(i, 'offset1')	# length for 1st offset
		i = node.ReadCrossRef(i, 'offset2')	# length for 2nd offset
		return i

	def Read_97DBCF9C(self, node): # Bend extent type 'Edge'
		i = self.ReadHeaderBendExtent(node, 'Edge')
		return i

	#######################
	# hem-shape sections
	def ReadHeaderHemShape(self, node, name):
		i = self.ReadHeadersS32ss(node, 'HemShape' + name)
		i = node.ReadCrossRef(i, 'length')
		i = node.ReadCrossRef(i, 'gap')
		i = node.ReadCrossRef(i, 'angle')
		i = node.ReadCrossRef(i, 'thickness')
		i = node.ReadCrossRef(i, 'radius')
		i = node.ReadCrossRef(i, 'flip')
		i = node.ReadCrossRef(i, 'edge')
		i = node.ReadCrossRef(i, 'surface')
		i = node.ReadCrossRef(i, 'plane')
		i = node.ReadCrossRef(i, 'boundaryPatch')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		if (self.version > 2017): i += 4
		i = node.ReadCrossRef(i, 'surfaces')
		return i

	def Read_72E8B3EB(self, node):
		i = self.ReadHeaderHemShape(node, 'Teardrop')
		return i

	def Read_77C03471(self, node):
		i = self.ReadHeaderHemShape(node, 'Doubled')
		return i

	def Read_914B3439(self, node):
		i = self.ReadHeaderHemShape(node, 'Single')
		return i

	def Read_FD4843EB(self, node):
		i = self.ReadHeaderHemShape(node, 'Rolled')
		return i

	#######################
	# derived component sections
	def ReadHeaderComponentDerived(self, node, typeName):
		i = self.ReadHeadersS32ss(node, typeName)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_255D7ED7(self, node): # DerivedPartComponent {6D7C8AC8-722D-46C8-B6D9-F6001F1EDD2D}
		i = self.ReadHeaderComponentDerived(node, 'DerivedPart')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_27ECB60F(self, node): # DerivedAssemblyComponent {A1D2EAAD-28A1-4692-BC13-883879C68894}
		i = self.ReadHeaderComponentDerived(node, 'DerivedAssembly')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2023):
			i = node.ReadCrossRef(i, 'ref_2')
		elif (self.version > 2017): i += 36 # skip LdddL{10}
		return i

	#######################
	# edge identifyer sections
	def ReadHeaderEdgeId(self, node, typeName = None, name = 'creator'):
		i = self.ReadHeadersS32ss(node, typeName, name) # The edge
		i = self.ReadClassInfo(node, i, 'body')
		i = node.ReadUInt32(i, 'wireIndex')
		if (self.version > 2017): i += 4
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0') # dcIndex
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_2')
		i = self.skipBlockSize(i)
		return i

	def Read_03AA812C(self, node): # FaceId
		i = self.ReadHeaderEdgeId(node, 'FaceId', 'creator')
		if (self.version < 2011):
			i = node.ReadCrossRef(i, 'owner')
			i = self.ReadNtEntry(node, i, 'ntFace')
			i = self.ReadNtEntryList(node, i, 'ntEdges')
		else:
			i = self.ReadNtEntry(node, i, 'ntFace')
			i = self.ReadNtEntryList(node, i, 'ntEdges')
			i = node.ReadCrossRef(i, 'owner')
		return i

	def Read_1DEE2CF3(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_27E9A56F(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'axis')
		i = self.ReadNtEntry(node, i, 'ntEntry1')
		i = self.ReadNtEntry(node, i, 'ntEntry2')
		i = self.ReadNtEntry(node, i, 'ntEntry3')
		i = node.ReadUInt16(i, 'u16_1')
		return i

	def Read_28B21FD5(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'axis')
		i = node.ReadCrossRef(i, 'param')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_38F3CAAA(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadUInt8(i, 'u8_3')
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_4C06C4D0(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		i = self.ReadNtEntryList(node, i, 'entries')
		return i

	def Read_56BE90F5(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'direction')
		i = self.ReadNtEntry(node, i, 'ntEntry1')
		return i

	def Read_6CA92D02(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'entity')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_723BA8B3(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadUInt8(i, 'u8_3')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_748FBD64(self, node): # FaceSurfaceId
		i = self.ReadHeaderEdgeId(node, 'FaceSurfaceId')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_76CF355E(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.ReadNtEntry(node, i, 'ntEntry0')
		i = self.skipBlockSize(i)
		i = self.ReadNtEntry(node, i, 'ntEntry1')
		return i

	def Read_88FA65CA(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_8EB19F04(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadUInt8(i, 'u8_3')
		i = node.ReadCrossRef(i, 'curve')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		i = node.ReadUInt8(i, 'u8_4')
		i = self.ReadNtEntryList(node, i, 'entries')
		return i

	def Read_90874D53(self, node): # EdgeId
		i = self.ReadHeaderEdgeId(node, 'EdgeId')
		i = node.ReadCrossRef(i, 'owner')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_90874D55(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'owner')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_90874D56(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadUInt8(i, 'u8_3')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_B045E1CC(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'point')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		i = self.ReadNtEntryList(node, i, 'entries')
		i = node.ReadUInt8(i, 'u8_3')
		return i

	def Read_B10D8B80(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'axis')
		i = node.ReadCrossRef(i, 'param')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_B884A1E1(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'entity')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_B8DBEF70(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'owner')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_CA674C90(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'point')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_D80CE357(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadUInt8(i, 'u8_3')
		i = node.ReadCrossRef(i, 'owner')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		i = self.ReadNtEntryList(node, i, 'ntEntries')
		return i

	def Read_D8A9C970(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'point')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_E2CCC3B7(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadCrossRef(i, 'point')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		i = node.ReadFloat64(i, 'f64_1')
		return i

	def Read_EDAEAC7B(self, node):
		i = self.ReadHeaderEdgeId(node)
		i = node.ReadUInt8(i, 'u8_3')
		i = node.ReadCrossRef(i, 'point')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	#######################
	# face bound sections
	def ReadHeaderFaceBound(self, node, typeName = None):
		i = self.ReadHeadersS32ss(node, typeName)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'parts')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		i = node.ReadUInt32A(i, 2, 'a1')
		if (self.version > 2011):
			i = node.ReadCrossRef(i, 'sketch')
		else:
			i = self.skipBlockSize(i)
		return i

	def Read_424EB7D7(self, node, typeName = 'FaceBound'): # Face Bound
		i = self.ReadHeaderFaceBound(node, 'FaceBound')
		i = node.ReadCrossRef(i, 'proxy')
		return i

	def Read_D61732C1(self, node):
		i = self.ReadHeaderFaceBound(node, 'FaceBounds')
		i = node.ReadCrossRef(i, 'proxy1')
		i = node.ReadCrossRef(i, 'proxy2')
		i = node.ReadCrossRef(i, 'parameter1')
		i = node.ReadCrossRef(i, 'body')
		i = node.ReadCrossRef(i, 'parameter2')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'parameter3')
		i = node.ReadCrossRef(i, 'fx')
		i = node.ReadCrossRef(i, 'parameter4')
		i = node.ReadCrossRef(i, 'parameter5')
		i = node.ReadCrossRef(i, 'parameter6')
		return i

	def Read_F9884C43(self, node): # Face Outer Bound
		i = self.ReadHeaderFaceBound(node, 'FaceBoundOuter')
		i = node.ReadCrossRef(i, 'proxy')
		return i

	#######################
	# content header 2xskip cross reference sections
	def ReadCntHdr1SCross(self, node, typeName = None, name = 'ref_1'):
		i = self.ReadHeaderContent(node, typeName)
		i = self.skipBlockSize(i)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		if (self.version > 2020): i += 4 # skip FF FF FF FF
		i = node.ReadCrossRef(i, name)
		return i

	def Read_4ACA204D(self, node): # UserCoordinateSystem {F0854465-652D-4375-98A4-7C875BFE7A9C}
		i = self.ReadCntHdr1SCross(node, 'UserCoordinateSystem', 'transformation')
		i = node.ReadCrossRef(i, 'planeXY')
		i = node.ReadCrossRef(i, 'planeXZ')
		i = node.ReadCrossRef(i, 'planeYZ')
		i = node.ReadCrossRef(i, 'axisX')
		i = node.ReadCrossRef(i, 'axisY')
		i = node.ReadCrossRef(i, 'axisZ')
		i = node.ReadCrossRef(i, 'origin')
		i = node.ReadCrossRef(i, 'ref_9')
		return i

	def Read_4CF1124C(self, node): # Block2D
		i = self.ReadCntHdr1SCross(node, 'Block2D')
		i = node.ReadCrossRef(i, 'sketch')
		i = node.ReadCrossRef(i, 'source')
		i = node.ReadCrossRef(i, 'placement')
		i = self.ReadTransformation2D(node, i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_68821F22(self, node):
		i = self.ReadCntHdr1SCross(node)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'thickness')
		i = node.ReadCrossRef(i, 'reliefShahpe')
		i = node.ReadCrossRef(i, 'reliefPosition')
		i = node.ReadCrossRef(i, 'bendTransition')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		return i

	#######################
	# content header 2xskip sections
	def ReadCntHdr2S(self, node, typeName = None):
		i = self.ReadHeaderContent(node, typeName)
		i = self.skipBlockSize(i, 2)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		if (self.version > 2020): i += 4 # skip FF FF FF FF
		return i

	def Read_0675182E(self, node):
		i = self.ReadCntHdr2S(node)
		return i

	def Read_1D9FF49B(self, node):
		i = self.ReadCntHdr2S(node)
		return i

	def Read_1FBB3C01(self, node): # The content of the RTF formatted text {rtf1 [:RtfContent:]}
		i = self.ReadCntHdr2S(node, 'RtfContent')
		i = node.ReadVec3D(i, 'loc', 10.0)
		i = node.ReadUInt16A(i, 18, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		if (self.version > 2015):
			i = node.ReadUInt32(i, 'u32_0')
			if (self.version > 2024): i += 17 # 00 00 00 00 .. 00
			i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 4, 'a2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadVec3D(i, 'vec1', 1.0)
		i = node.ReadVec3D(i, 'vec2', 1.0)
		i = node.ReadUInt16A(i, 3, 'a3')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		i = node.ReadLen32Text16(i, 'txt0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		if (self.version > 2016 and self.version < 2025): i += 17
		return i

	def Read_262B3A9F(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadFloat64_3D(i, 'pos')
		return i

	def Read_2640F4EB(self, node):
		i = self.ReadCntHdr2S(node)
		return i

	def Read_28BE2D59(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'cnt_lst0')
		if (self.version < 2024):
			a0 = Struct("<LddbH").unpack_from(node.data, i)
			i += 23
		else:
			a0 = Struct("<LddbB").unpack_from(node.data, i)
			i += 22
		node.set('a0', a0)
		i = node.ReadCrossRef(i, 'ref_0')
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		return i

	def Read_39A41830(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 13, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadUInt32A(i,  5, 'a4')
		i = node.ReadFloat64A(i, 6, 'a5')
		i = node.ReadUInt16A(i,  6, 'a6')
		i = node.ReadCrossRef(i, 'parameter1')
		i = node.ReadCrossRef(i, 'parameter2')
		i = node.ReadUInt32(i,  'u32_0')
		i = node.ReadUInt32A(i,  2, 'a7')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i,  2, 'a8')
		i = node.ReadCrossRef(i, 'sketch')
		return i

	def Read_3D8924FD(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadBoolean(i, 'value')
		return i

	def Read_4C478499(self, node):
		i = self.ReadCntHdr2S(node, 'ThreadProxy')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat64_3D(i, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadCrossRef(i, 'definition')
		return i

	def Read_4CFBE477(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadFloat64A(i, 4, 'a0')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a1')
		i = node.ReadUInt32A(i, 11, 'a2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		if (self.version > 2016): i += 4 # skip 00 00 00 00
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32A(i, 7, 'a3')
		i = self.skipBlockSize(i)
		if (self.version < 2011):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_4F3DEE08(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_5CBF4E92(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst2')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst3')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst4')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_71274EAC(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_7F614712(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_88A7DE77(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadFloat64A(i, 8, 'v0')
		return i

	def Read_8B253EF4(self, node):
		i = self.ReadCntHdr2S(node)
		e, i = self.ReadEdge(node, i)
		node.set('e', e)
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadBoolean(i, 'b')
		return i

	def Read_8D6EF0BE(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadList4(i, importerSegNode._TYP_2D_UINT32_, 'lst0', getUInt32A)
		return i

	def Read_90874D18(self, node): # Transformation
		i = self.ReadCntHdr2S(node, 'Transformation')
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_90874D47(self, node): # SurfaceBody {5DF86089-6B16-11D3-B794-0060B0F159EF}
		i = self.ReadCntHdr2S(node, 'SurfaceBody')
		i = node.ReadCrossRef(i, 'ref_0')
		return i

	def Read_90B64134(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2017): i += 1 # skip 01
		return i

	def Read_99B938AE(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadFloat64_2D(i, 'a1')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2011):
			i = node.ReadUInt32(i, 'u32_1')
		else:
			node.set('u32_1', 0, VAL_UINT32)
		return i

	def Read_CCD87CBA(self, node):
		i = self.ReadCntHdr2S(node)
		i = node.ReadFloat64_2D(i, 'v0')
		return i

	def Read_D5DAAA83(self, node): # SurfaceBodies {5DF860AE-6B16-11D3-B794-0060B0F159EF}
		i = self.ReadCntHdr2S(node, 'BodyCollection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'items')
		return i

	def Read_D83EF271(self, node):
		i = self.ReadCntHdr2S(node, 'FeatureDimensions')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'fxDimensions')
		return i

	def Read_E5721705(self, node):
		i = self.ReadCntHdr2S(node)
		i = self.Read2RefList(node, i, 'sideCorners', importerSegNode.REF_CHILD, importerSegNode.REF_CROSS)
		return i

	#######################
	# content header 2xskip cross reference sections
	def ReadCntHdr2SCross(self, node, typeName = None, name = 'ref_1'):
		i = self.ReadCntHdr2S(node, typeName)
		i = node.ReadCrossRef(i, name)
		return i

	def Read_0455B440(self, node):
		i = self.ReadCntHdr2SCross(node, 'A96B5993_Def')
		i = node.ReadCrossRef(i, 'thickness')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = node.ReadCrossRef(i, 'ref_6')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'radius')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'reliefWidth')
		i = node.ReadCrossRef(i, 'minRemnant')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8A(i, 3, 'a0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_20976662(self, node):
		i = self.ReadCntHdr2SCross(node, 'SculptSurface', 'body')
		i = node.ReadCrossRef(i, 'operation')
		return i

	def Read_2148C03C(self, node): # ReferenceFeature {298849A9-ECAB-4234-9675-6FAA66A95E4D}
		i = self.ReadCntHdr2SCross(node, 'Reference')
		return i

	def Read_265034E9(self, node): # Bend Transition Radius Definition
		i = self.ReadCntHdr2SCross(node, 'BendTransition', 'type')
		i = node.ReadCrossRef(i, 'ref_2')  # bool
		i = node.ReadCrossRef(i, 'radius')
		return i

	def Read_324C58BF(self, node):
		i = self.ReadCntHdr2SCross(node)
		return i

	def Read_7256922C(self, node):
		i = self.ReadCntHdr2SCross(node, 'Placement', 'transformation')
		i = node.ReadCrossRef(i, 'point')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_7270F478(self, node):
		i = self.ReadCntHdr2SCross(node)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_8677CE83(self, node): # CornerSeam
		i = self.ReadCntHdr2SCross(node, 'CornerSeam')
		i = node.ReadCrossRef(i, 'gapDim')       # dim-parameter
		i = node.ReadCrossRef(i, 'reliefSize')   # dim-parameter
		i = node.ReadCrossRef(i, 'reliefType')   # relief
		i = node.ReadCrossRef(i, 'gapType')      # CornerGapType
		i = node.ReadCrossRef(i, 'relief_2')     # relief
		i = node.ReadCrossRef(i, 'jacobiRadius') # dim-parameter
		i = node.ReadCrossRef(i, 'gapOverlap')   # gap overlap percentage
		i = node.ReadCrossRef(i, 'ref_2')        # bool-parameter
		return i

	def Read_8F2822F9(self, node): # bending edge
		i = self.ReadCntHdr2SCross(node, 'BendEdge', name='proxy')
		i = node.ReadFloat64_3D(i, 'from')
		i = node.ReadFloat64_3D(i, 'to')
		return i

	def Read_96058864(self, node):
		i = self.ReadCntHdr2SCross(node, name='useDefault')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'reliefWidth')
		i = node.ReadCrossRef(i, 'reliefDepth')
		i = node.ReadCrossRef(i, 'bendType')    # Relief
		i = node.ReadCrossRef(i, 'minRemnant')
		i = node.ReadCrossRef(i, 'seamGap')
		return i

	def Read_A96B5992(self, node):
		i = self.ReadCntHdr2SCross(node, 'PlateDef')
		i = node.ReadCrossRef(i, 'thickness')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'dir1')
		i = node.ReadCrossRef(i, 'dir2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'radius')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'reliefWidth')
		i = node.ReadCrossRef(i, 'minRemnant')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadUInt8A(i, 3, 'a0')
		i = node.ReadCrossRef(i, 'ref_5')
		return i

	def Read_B310B8E5(self, node): # HemFeature {D9AB7AE5-6A67-4165-9E0B-0F008C9135B0}
		i = self.ReadCntHdr2SCross(node, 'HemDef')
		i = node.ReadCrossRef(i, 'thickness')
		i = node.ReadCrossRef(i, 'ref_3')        # Enum
		i = node.ReadCrossRef(i, 'axis')
		i = node.ReadCrossRef(i, 'dir')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'radius')
		i = node.ReadCrossRef(i, 'ref_7')        # Enum
		i = node.ReadCrossRef(i, 'ref_8')        # Parameter
		i = node.ReadCrossRef(i, 'ref_9')        # Parameter
		i = node.ReadCrossRef(i, 'ref_A')        # bool
		i = node.ReadUInt8A(i, 3, 'a0')
		i = node.ReadCrossRef(i, 'ref_B')        # bool
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_BFBAAFA8(self, node):
		i = self.ReadCntHdr2SCross(node)
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_CDF78EC0(self, node):
		i = self.ReadCntHdr2SCross(node)
		i = node.ReadFloat64(i, 'f64_0')
		return i

	def Read_D01E2BB0(self, node):
		i = self.ReadCntHdr2SCross(node)
		return i

	def Read_D30E5235(self, node):
		i = self.ReadCntHdr2SCross(node)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_DC93DB08(self, node): # RDxPicture
		i = self.ReadCntHdr2SCross(node, 'Picture', 'sketch') # The image is def
		i = node.ReadFloat64(i, 'width')
		i = node.ReadFloat64(i, 'height')
		i = node.ReadFloat64_2D(i, 'pos')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt16A(i, 3, 'a1')
		i = node.ReadFloat64(i, 'scale')
		i = node.ReadUInt8(i, 'refIndex') # UFRxDoc.fRefs[refIndex]
		return i

	def Read_F83F79DA(self, node):
		i = self.ReadCntHdr2SCross(node)
		return i

	#######################
	# content header 2xskip child reference sections
	def ReadCntHdr2SChild(self, node, typeName = None, name = 'ref_1'):
		i = self.ReadCntHdr2S(node, typeName)
		i = node.ReadChildRef(i, name)
		return i

	def Read_4B3150E8(self, node):
		i = self.ReadCntHdr2SChild(node, 'LoftSection', 'refWrapper')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadCrossRef(i, 'condition')
		i = node.ReadCrossRef(i, 'impact')
		i = node.ReadCrossRef(i, 'angle')
		i = node.ReadCrossRef(i, 'tangentPlane')
		i = node.ReadList7(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'directionReversed')
		return i

	def Read_A477243B(self, node): # Profile to Asm mapping
		i = self.ReadCntHdr2SChild(node, 'FaceBoundProxy', 'refWrapper')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_FC203F47(self, node): # FaceBoundOuterProxy
		i = self.ReadCntHdr2SChild(node, 'FaceBoundOuterProxy', 'refWrapper')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	#######################
	# H0 3xskip U32 skip sections
	def ReadHeadersss2S16s(self, node, typeName = None):
		i = self.ReadCntHdr3S(node, typeName)
		i = node.ReadUInt32(i, 'flags2')
		i = self.skipBlockSize(i)
		return i

	def Read_0B85010C(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_151280F0(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2017): i += 4
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_2')
		cnt, i = getUInt32(node.data, i)
		if (cnt == 1):
			i = node.ReadUInt32(i, 'u32_4')
		elif (cnt == 0):
			node.set('u32_4', 0, VAL_UINT32)
		i = node.ReadFloat64_3D(i, 'pos') # start z
		i = node.ReadFloat64_3D(i, 'dir') # direction
		i = node.ReadFloat64_3D(i, 'point') # start point
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

	def Read_3170E5B0(self, node): # FaceDraftFeature {EA1D0D38-93AD-48BB-84AC-7707FAC29BAF}
		i = self.ReadHeadersss2S16s(node, 'FaceDraft')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_34FAB548(self, node):
		i = self.ReadHeadersss2S16s(node, 'FaceExtend')
		return i

	def Read_4116DA9E(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2017): i += 4
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64A(i, 10, 'a2')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32A(i, 6, 'a5') # ???????
		i = node.ReadFloat64_2D(i, 'a6') # Angle (e.g.: -pi ... +pi)
		return i

	def Read_46D500AA(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_528A064A(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		if (self.version > 2017): i += 4
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_0')
		if (node.get('u32_0') > 0):
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadFloat64_3D(i, 'a2')
			i = node.ReadFloat64(i, 'f64_0')
			i = node.ReadFloat64A(i, 10, 'a3')
			i = node.ReadUInt32A(i, 2, 'a4') # ???????
			i = node.ReadUInt8A(i, 16, 'blob')
			i = node.ReadFloat64_2D(i, 'a5') # Angle (e.g.: -pi ... +pi)
		return i

	def Read_7F4A3E30(self, node):
		i = self.ReadHeadersss2S16s(node)
		node.isAttr = True
		node.delete('next')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadUInt16A(i, 3, 'a0')
		if (self.version > 2016): i += 1 # skip 01
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 6, 'a1')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadFloat64A(i, 6, 'a2')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadFloat64A(i, 24, 'a3')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt16A(i, 3, 'a4')
		i = node.ReadUInt8A(i, 2, 'b')
		i = node.ReadFloat64A(i, 6, 'a5')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 3, 'a6')
		i = node.ReadFloat64A(i, 18, 'a7')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadFloat64A(i, 18, 'a8')
		i = node.ReadUInt8(i, 'u8_3')
		if (self.version > 2010):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		else:
			node.set('lst0', [], VAL_REF)
			i += 4 # skip 0x000002F5
		i = node.ReadFloat64A(i, 12, 'a9')
		i = node.ReadUInt8(i, 'u8_4')
		i = node.ReadUInt16A(i, 5, 'a10')
		i = node.ReadFloat64A(i, 7, 'a11')
		return i

	def Read_AD0D42B2(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_B58135C4(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_CE52DF40(self, node): # plain pattern direction
		i = self.ReadHeadersss2S16s(node, 'DirectionAxis')
		i = node.ReadFloat64(i, 'a')
		i = self.skipBlockSize(i)
		if (self.version > 2017): i += 4
		i = node.ReadFloat64_3D(i, 'dir')
		return i

	def Read_CE52DF42(self, node): # Plane
		i = self.ReadHeadersss2S16s(node, 'Plane')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i, 2)
		if (self.version > 2017): i += 4
		i = node.ReadUInt32(i, 'u32_1')
		if (node.get('u32_1') > 1):
			i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat64_3D(i, 'center')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat64_3D(i, 'normal')
		return i

	def Read_E1D3D023(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadFloat32_3D(i, 'a1')
		i = node.ReadUInt16A(i, 3, 'a2')
		if (self.version > 2016):
			i += 1
		else:
			i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'a3')
		i = node.ReadUInt16A(i, 3, 'a4')
		i = node.ReadFloat64_2D(i, 'a5')
		i = node.ReadUInt16A(i, 3, 'a6')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadFloat64A(i, 31, 'a7')
		i = node.ReadUInt8A(i, 18, 'a8')
		i = node.ReadFloat64A(i, 6, 'a9')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 3, 'a10')
		i = node.ReadFloat64A(i, 18, 'a11')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadFloat64A(i, 12, 'a12')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadFloat64A(i, 6, 'a13')
		if (self.version > 2010):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		node.isAttr = True
		return i

	def Read_E70647C2(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2017): i += 4
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64A(i, 12, 'a2')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadUInt16A(i, 4, 'a4')
		i = node.ReadFloat64_3D(i, 'a5')
		return i

	def Read_E70647C3(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2017): i += 4
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_1')
		if (node.get('u32_2') == 1):
			cnt, i = getUInt32(node.data, i)
			if (cnt == 1):
				i = node.ReadUInt32(i, 'u32_4')
			elif (cnt == 0):
				node.set('u32_4', 0, VAL_UINT32)
			i = node.ReadFloat64A(i, (len(node.data) - i) / 8, 'a1')
		return i

	def Read_EAC2875A(self, node):
		i = self.ReadHeadersss2S16s(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64(i, 'f1')
		i = node.ReadUInt16A(i, 3, 'a0')
		if (self.version > 2016):
			i += 1
		else:
			i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 4, 'a1')
		i = node.ReadUInt16A(i, 4, 'a2')
		i = node.ReadFloat64A(i, 25, 'a3')
		i = node.ReadUInt16A(i, 3, 'a4')
		i = node.ReadFloat64A(i, 2, 'a5')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64(i, 'f2')
		i = node.ReadFloat64A(i, 12, 'a6')
		if (self.version > 2012):
			i += 3*8 # same as a4[-3:]
		node.isAttr = True
		return i

	#######################
	# 3D-sketch entity sections
	def ReadHeaderSketch3DEntity(self, node, typeName = None):
		i = self.ReadHeadersss2S16s(node, typeName)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'sketch')
		if (self.version > 2017): i += 4
		i = self.skipBlockSize(i)
		return i

	def Read_0B86AD43(self, node): # SketchFixedSpline3D {7A5B2F53-5756-4261-B6F1-4B5C3CDE1226}
		i = self.ReadHeaderSketch3DEntity(node, 'Spline3D_Fixed')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_7C44ABDE(self, node): # Bezier3D
		i = self.ReadHeaderSketch3DEntity(node, 'Bezier3D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a2')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32A(i, 3, 'a3')
		cnt = node.get('a3')[0]
		i = node.ReadFloat64A(i, cnt, 'a4')
		i = node.ReadUInt32A(i, 6, 'a5')
		cnt = node.get('a5')[3]
		i = self.ReadFloat64A(node, i, cnt, 'points2', 3)
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

	def Read_8EF06C89(self, node): # SketchLine3D {87056D9A-B0B2-4BD0-A6EC-51E9D893A502}
		i = self.ReadHeaderSketch3DEntity(node, 'Line3D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		if (len(node.data) - i == 6*8 + 1 + 4):
			i += 4
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadFloat64_3D(i, 'dir')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_9E43716A(self, node): # Circle3D
		i = self.ReadHeaderSketch3DEntity(node, 'Circle3D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadFloat64_3D(i, 'normal')
		i = node.ReadFloat64_3D(i, 'm')
		i = node.ReadFloat64(i, 'r')
		i = node.ReadFloat64(i, 'startAngle')
		i = node.ReadFloat64(i, 'sweepAngle')
		i = node.ReadCrossRef(i, 'center')
		return i

	def Read_9E43716B(self, node): # Ellipse3D
		i = self.ReadHeaderSketch3DEntity(node, 'Ellipse3D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'center')
		i = node.ReadFloat64_3D(i, 'major')
		i = node.ReadFloat64_3D(i, 'minor')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadFloat64(i, 'b')
		i = node.ReadFloat64(i, 'startAngle')
		i = node.ReadFloat64(i, 'sweepAngle')
		return i

	def Read_C1A45D98(self, node): # SplineHandle3D
		i = self.ReadHeaderSketch3DEntity(node, 'SplineHandle3D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 6, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_CE52DF3E(self, node): # SketchPoint3D {2307500B-D075-4F5D-815D-7A1B8E90B20C}
		i = self.ReadHeaderSketch3DEntity(node, 'Point3D')
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'endPointOf')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'centerOf')
		endPointOf = node.get('endPointOf')
		centerOf   = node.get('centerOf')
		entities   = []
		entities.extend(endPointOf)
		entities.extend(centerOf)
		node.set('entities', entities, VAL_REF)
		return i

	#######################
	# 2D-sketch entity sections
	def ReadHeaderSketch2DEntity(self, node, typeName = None):
		i = self.ReadHeadersss2S16s(node, typeName)
		i = node.ReadCrossRef(i, 'sketch')
		return i

	def Read_18A9717E(self, node):
		i = self.ReadHeaderSketch2DEntity(node, 'BlockPoint2D')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'centerOf')
		i = node.ReadCrossRef(i, 'point')
		node.set('points', node.get('centerOf'), None)
		return i

	def Read_52534838(self, node): # PatternConstraint {C173A073-012F-11D5-8DEA-0010B541CAA8}
		i = self.ReadHeaderSketch2DEntity(node, 'Geometric_PolygonCenter2D')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'center')
		i = node.ReadCrossRef(i, 'construction')
		return i

	def Read_CE52DF35(self, node): # SketchPoint {8006A022-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadHeaderSketch2DEntity(node, 'Point2D')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_2D(i, 'pos')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'endPointOf')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'centerOf')
		if (self.version > 2012):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_, 'lst1')
		else:
			node.set('u32_0', 0, VAL_UINT32)
			node.set('lst1', [])
		if (self.version > 2019):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_LST2_X_REF_, 'lst2')
		endPointOf = node.get('endPointOf')
		centerOf   = node.get('centerOf')
		entities   = []
		entities.extend(endPointOf)
		entities.extend(centerOf)
		node.set('entities', entities, None)
		return i

	#######################
	# 2D-edge sections
	def ReadHeader2DEdge(self, node, typeName = None):
		i = self.ReadHeaderSketch2DEntity(node, typeName)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'points')
		if (self.version > 2012):
			if (self.version > 2019):
				a, i = getUInt32A(node.data, i, 2) # skip 01 00 00 00 00 00 00 00
			else:
				a = (1, 0)
			if (a[0] == 1):
				i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
				if (self.version > 2019):
					i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		else:
			i = self.skipBlockSize(i)
		return i

	def Read_160915E2(self, node): # SketchArc {8006A046-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeader2DEdge(node, 'Arc2D')
		i = node.ReadCrossRef(i, 'center')
		i = node.ReadFloat64(i, 'r')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_317B7346(self, node): # SketchSpline {8006A048-ECC4-11D4-8DE9-0010B541CAA8}:
		i = self.ReadHeader2DEdge(node, 'Spline2D')
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2012):
			i = node.ReadUInt32(i, 's')
		else:
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

	def Read_3E55D947(self, node): # SketchOffsetSpline {063D7617-E630-4D35-B809-64D6695F57C0}:
		i = self.ReadHeader2DEdge(node, 'OffsetSpline2D')
		i = node.ReadCrossRef(i, 'entity')
		i = node.ReadFloat64(i, 'x')
		return i

	def Read_4507D460(self, node): # SketchEllipse {8006A04A-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeader2DEdge(node, 'Ellipse2D')
		i = node.ReadCrossRef(i, 'center')
		i = node.ReadFloat64_2D(i, 'dA')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadFloat64(i, 'b')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_A644E76A(self, node): # SketchSplineHandle {1236D237-9BAC-4399-8CFB-66CB6B7FD5CA}
		i = self.ReadHeader2DEdge(node, 'SplineHandle2D')
		i = node.ReadFloat64A(i, 4, 'a1')
		i = self.skipBlockSize(i)
		return i

	def Read_CE52DF3A(self, node): # SketchLine {8006A016-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeader2DEdge(node, 'Line2D')
		# RootPoint
		i = node.ReadFloat64_2D(i, 'pos')
		# Direction
		i = node.ReadFloat64_2D(i, 'dir')
		return i

	def Read_CE52DF3B(self, node): # SketchCircle {8006A04C-ECC4-11D4-8DE9-0010B541CAA8}
		i = self.ReadHeader2DEdge(node, 'Circle2D')
		i = node.ReadCrossRef(i, 'center')
		i = node.ReadFloat64(i, 'r')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_F9372FD4(self, node): # SketchControlPointSpline {D5F8CF99-AF1F-4089-A638-F6889762C1D6}
		i = self.ReadHeader2DEdge(node, 'BSplineCurve2D')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16A(i, 5, 'a0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt16A(i, 5, 'a1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'ptIdcs')

		a2 = Struct('<LLLd').unpack_from(node.data, i)
		i += 20
		node.set('a2', a2, VAL_UINT32)
		i = self.readTypedList(node, i, 'a3',    3, 1, False)
		i = self.readTypedList(node, i, 'a4',    3, 1, False)
		i = self.readTypedList(node, i, 'poles', 3, 2, True)
		i = self.readTypedList(node, i, 'a5',    2, 2, False)
		i = self.readTypedList(node, i, 'a6',    3, 2, True)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'handles')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'arcs')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadFloat64(i, 'f64_1')
		a7 = Struct('<LBLLLd').unpack_from(node.data, i)
		i += 25
		node.set('a7', a7)
		i = self.readTypedList(node, i, 'a3_',    3, 1, False)
		i = self.readTypedList(node, i, 'a4_',    3, 1, False)
		i = self.readTypedList(node, i, 'poles_', 3, 2, True)
		i = self.readTypedList(node, i, 'a5_',    2, 2, False)
		i = self.readTypedList(node, i, 'a6_',    3, 2, True)
		a8 = Struct('<Ldddd').unpack_from(node.data, i)
		i += 36
		node.set('a8', a8, VAL_UINT32)
		return i

	#######################
	# Document sections
	def ReadHeaderDocument(self, node, docType):
		self.type = docType
		i = node.Read_Header0('Document')
		i = node.ReadChildRef(i,    'next')
		i = node.ReadUInt32(i,      'u32_0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadUUID(i,        'uid_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32A(i, 3,  'a0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i,    'component')
		i = node.ReadChildRef(i,    'nameTable')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i,    'ref_1')
		i = node.ReadChildRef(i,    'workbook') # embedded Excel file
		i = node.ReadChildRef(i,    'display')
		i = node.ReadChildRef(i,    'ref_2')
		i = self.skipBlockSize(i)
		return i

	def Read_90874D16(self, node): # Document
		i = self.ReadHeaderDocument(node, DCReader.DOC_PART)
		i = node.ReadCrossRef(i,    'ref_3')
		i = node.ReadUInt32(i,      'u32_1')
		i = node.ReadChildRef(i,    'faceMerges')
		i = node.ReadUInt32(i,      'u32_2')
		i = node.ReadChildRef(i,    'mdlTxnMgr') # -> ModelerTxnMgr
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i,    'ref_4')
		i = node.ReadLen32Text16(i, 'segName')
		i = node.ReadFloat64(i,     'f64_0')
		i = node.ReadChildRef(i,    'ref_5')
		return i

	def Read_90874D46(self, node): # Document
		i = self.ReadHeaderDocument(node, DCReader.DOC_ASSEMBLY)
		i = node.ReadCrossRef(i,    'ref_3')
		i = node.ReadUInt32(i,      'u32_1')
		i = node.ReadChildRef(i,    'faceMerges')
		i = node.ReadUInt32(i,      'u32_2')
		i = node.ReadChildRef(i,    'mdlTxnMgr') # -> ModelerTxnMgr
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i,      'u32_3')
		i = node.ReadChildRef(i,    'ref_4')
		i = node.ReadUInt32(i,      'u32_4')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadChildRef(i,    'ref_5')
		i = node.ReadChildRef(i,    'ref_6')
		i = node.ReadChildRef(i,    'ref_7')
		if (self.version > 2014):
			i = node.ReadChildRef(i, 'ref_8')
			if (self.version > 2016): i += 4 # skip 00 00 00 00
		return i

	def Read_D37C90CB(self, node): # Document
		i = self.ReadHeaderDocument(node, DCReader.DOC_DRAWING)
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt32A(i, 7,  'a1')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst2')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst3')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst4')
		i = node.ReadUInt32A(i, 3,  'a2')
		i = node.ReadFloat64_2D(i,  'a3')
		i = node.ReadUInt32A(i, 2,  'a4')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst5')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst6')
		i = node.ReadUInt32(i,      'u32_1')
		i = node.ReadBoolean(i,     'b0')
		i = node.ReadChildRef(i,    'ref_3')
		i = node.ReadChildRef(i,    'ref_4')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst7')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst8')
		i = node.ReadUInt32(i,      'u32_2')
		i = node.ReadChildRef(i,    'ref_5')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst9')
		i = node.ReadCrossRef(i,    'ref_6')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst10')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst11')
		i = node.ReadUInt32(i,      'u32_3')
		if (self.version > 2010): i += 4  # skip 1B 00 00 00
		return i

	def Read_F14FD076(self, node): # Document
		i = self.ReadHeaderDocument(node, DCReader.DOC_PRESENTATION)
		i = node.ReadCrossRef(i,    'ref_3')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadCrossRef(i,    'ref_4')
		i = node.ReadLen32Text16(i, 'segName')
		i = node.ReadChildRef(i,    'faceMerges')
		i = node.ReadList2(i,       importerSegNode._TYP_NODE_REF_, 'lst2')
		return i

	##########################
	# Linked element sections => FX-Attributes
	def ReadHeaderLinkedElement(self, node, typeName = None):
		'''
		Read the default header a0=UInt32[2], owner=SecNodeRef, next=SecNodeRef
		'''
		tn = typeName
		if (tn is None): tn = "FxAttr_" + node.typeName
		i = node.Read_Header0(tn)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i+= 4 # skip 00 00 00 00
		i = node.ReadCrossRef(i, 'owner')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'next')
		i = self.skipBlockSize(i)
		node.isAttr = True
		return i

	def Read_01E7910C(self, node):
		i = self.ReadHeaderLinkedElement(node)
		if (self.version > 2015):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		else:
			ref, i = self.ReadNodeRef(node, i, 0, importerSegNode.REF_CROSS, 'lst0')
			node.set('lst0', [ref], VAL_REF)
		i = node.ReadList2(i, importerSegNode._TYP_LIST_FLOAT64_A_, 'lst1', 3)
		i = self.ReadEdgeList(node, i)
		return i

	def Read_0229768D(self, node): # FX-Attrirbute Parameter-Comment
		i = self.ReadHeaderLinkedElement(node, 'FxAttrParameterComment')
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_025C7CD8(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUUID(i, 'uid')
		i = node.ReadSInt32A(i, 3, 'a1')
		return i

	def Read_03D6552D(self, node): # FX-Attrirbute Sketch2D-Pre-Style
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'entity2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_086E7238(self, node):
		i =	self.ReadHeaderLinkedElement(node)
		i = node.ReadLen32Text16(i, 'txtUID')
		i = node.ReadLen32Text16(i, 'txt1')
		return i

	def Read_0A3BA89C(self, node): # FX-Attrirbute Sketch2D-Pre-Style
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'entity2')
		return i

	def Read_0E6B7F33(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadLen32Text16(i)
		return i

	def Read_10587822(self, node): # FX-Attrirbute Faces
		i = self.ReadHeaderLinkedElement(node, 'FxAttrFaces')
		i = self.ReadNtEntryList(node, i, 'entries')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 3, 'a2')
		return i

	def Read_109727B0(self, node): # iFeatureTemplateDescriptor {3C69FF6F-6ADD-4CF5-8E9B-32CBD2B6BBF7}
		i = self.ReadHeaderLinkedElement(node, 'iFeatureTemplateDescriptor')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_10DC334C(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_1249FE41(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_1488B839(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat64_3D(i, 'a2')
		return i

	def Read_21004CF2(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadFloat64(i, 'f64_0')
		return i

	def Read_26F369B7(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64_2D(i, 'a2')
		i = self.skipBlockSize(i)
		if (self.version > 2010):
			#i = node.ReadFloat64A(i, 6, 'a3')
			i += 6*8 # ref. Sketch3D origin
		return i

	def Read_29AC9292(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUUID(i, 'id')
		return i

	def Read_2A34F1AD(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_2A636E60(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_2AB13E5B(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_2CE86835(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'line1')
		i = node.ReadCrossRef(i, 'line2')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64_2D(i, 'pos')
		i = self.skipBlockSize(i)
		if (self.version > 2010):
			i = node.ReadFloat64_3D(i, 'p0')
			i = node.ReadFloat64_3D(i, 'p1')
			i = node.ReadFloat64_3D(i, 'p2')
			i = node.ReadFloat64_3D(i, 'p3')
			i = node.ReadFloat64_3D(i, 'p4')
		return i

	def Read_2F39A056(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_2F402FD0(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_30317C9B(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_327D097B(self, node): # FX-Attrirbute FlatPatternPunchRepresentation
		i = self.ReadHeaderLinkedElement(node, 'FxAttrFlatPatternPunchRepresentation')
		# (01|00) (00|01) 00
		return i

	def Read_39AD9666(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_3A98DCE3(self, node): # FX-Attrirbute EntityReference
		i = self.ReadHeaderLinkedElement(node, 'FxAttrEntityReference')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_454C24A9(self, node): # FX-Attrirbute Line style
		i = self.ReadHeaderLinkedElement(node, 'FxAttrStyleLine')
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

	def Read_46407F70(self, node): # FX-Attrirbute ClearanceHole
		i = self.ReadHeaderLinkedElement(node, 'FxAttrClearanceHole')
		i = node.ReadLen32Text16(i, 'standard')
		i = node.ReadLen32Text16(i, 'fastener')
		i = node.ReadLen32Text16(i, 'size')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'fit') # 0=Close; 1=Normal; 2=Close
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_464ECA8A(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a1')
		return i

	def Read_475E7861(self, node): # FX-Attrirbute DimensionState
		i = self.ReadHeaderLinkedElement(node, 'FxAttrDimensionState')
		i = node.ReadChildRef(i, 'attr')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadCrossRef(i, 'fxDims')
		return i

	def Read_48CF71CA(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_4F8A6797(self, node): # FX-Attrirbute Sketch2D-Pre-Style
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_52D04C41(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_54829655(self, node): # FX-Attrirbute NameTableKeyDef
		i = self.ReadHeaderLinkedElement(node, 'NameTableKeyDef')
		i = node.ReadUInt32(i, 'ntKey') # the key that is referenced by the name table entry.
		key = node.get('ntKey')
		self.segment.ntKeys[key] = node
		return i

	def Read_56970DFA(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_59C3DD6C(self, node): # FX-Attrirbute Label
		i = self.ReadHeaderLinkedElement(node, 'FxAttrLabel')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadChildRef(i, 'ref_4')
		i = node.ReadChildRef(i, 'ref_5')
		i = node.ReadChildRef(i, 'ref_6')
		return i

	def Read_606708CF(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_5A5D8DBF(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_5DD3A2D3(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_5ECA65C0(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadLen32Text16(i, 'txt_1')
		i = node.ReadUInt8A(i, 3, 'a1')
		return i

	def Read_5F425538(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_60452313(self, node): # FX-Attrirbute UserSettingsAttribute
		i = self.ReadHeaderLinkedElement(node, 'FxAttrUserSettings')
		properties = []
		for j in range(12):
			ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
			properties.append(ref)
		if (self.version > 2015):
			if (self.version < 2021):
				for j in range (12, 18):
					ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
					properties.append(ref)
				i = node.ReadUInt32(i, 'u32_0')
				i = node.ReadUInt32(i, 'u32_1')
				i = node.ReadUInt8(i, 'u8_0')
				i = node.ReadUInt16(i, 'u16_0')
				for j in range (18, 21):
					ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
					properties.append(ref)
				i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
				if (self.version > 2017):
					i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		else:
			for j in range (12, 15):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
				properties.append(ref)
			i = node.ReadList6(i, importerSegNode._TYP_MAP_U16_XREF_, 'lst0')
			for j in range (15, 21):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
				properties.append(ref)
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadUInt32(i, 'u32_1')
			i = node.ReadUInt8(i, 'u8_0')
			i = node.ReadUInt16(i, 'u16_0')
			for j in range (21, 24):
				ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
				properties.append(ref)
			if (self.version == 2015):
				i += 4
		return i

	def Read_614A01F1(self, node): # FX-Attrirbute SurfaceTexture
		i = self.ReadHeaderLinkedElement(node, 'FX-Attr-SurfaceTexture')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadLen32Text8(i, 'txt_0')
		i = self.skipBlockSize(i)
		return i

	def Read_63E209F9(self, node): # FX-Attrirbute Sketch2D-Pre-Style
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_656DD01E(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_6C69E7B8(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst3')
		return i

	def Read_6D6BE9B7(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		cnt, i = getUInt32(node.data, i)
		for j in range(cnt):
			i = node.ReadLen32Text16(i, 'txt%i' %(j+1))
		return i

	def Read_6DFCBEE5(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = self.skipBlockSize(i)
		return i

	def Read_75F64419(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_7A1BCDC6(self, node): # FX-Attribute Flange
		i = self.ReadHeaderLinkedElement(node, 'FxAttrFlange')
		i = node.ReadCrossRef(i, 'flange') # Feature
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'extent') # Parameter
		i = node.ReadCrossRef(i, 'angle')  # Parameter
		return i

	def Read_7C340AFD(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_7C39DC59(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_7D981698(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_7DFE2BF1(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_7E36DE81(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_STRING16_, 'lst0')
		return i

	def Read_8227E5B8(self, node): #
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_F64_, 'lst0')
		return i

	def Read_828E73A6(self, node):
		i = self.ReadHeaderLinkedElement(node)
		cnt, i = getUInt32(node.data, i)
		lst = []
		for j in range(cnt):
			u32, i = getUInt32(node.data, i)
			f64, i = getFloat64(node.data, i)
			lst.append([u32, f64])
		node.set('lst1', lst, VAL_UINT32)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_852F60CB(self, node): # new in 2018
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_871D6F71(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadFloat32_3D(i, 'a1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadFloat64A(i, 4, 'a2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_878BD512(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_8C702CD5(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadFloat64_3D(i, 'a1')
		i = self.skipBlockSize(i)
		if (self.version > 2010): i += 48 # skip trailing 0x00's !
		return i

	def Read_903F453F(self, node): # FX-Attribute ExtrusionSurface
		i = self.ReadHeaderLinkedElement(node, 'FxAttrExtrusionSurface')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_90874D15(self, node): # FX-Attribute Styles
		i = self.ReadHeaderLinkedElement(node, 'FxAttrStyles')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'associativeID') # Number of the entity inside the sketch
		i = node.ReadUInt32(i, 'typEntity')
		return i

	def Read_91637937(self, node):
		i = self.ReadHeaderLinkedElement(node)
		cnt, i = getUInt32(node.data, i)
		i = self.ReadUInt32A(node, i, cnt, 'a1', 2)
		i = node.ReadUInt32A(i, 2, 'a2')
		return i

	def Read_9271AB29(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i, 'fmt1')
		i = node.ReadLen32Text16(i, 'fmt2')
		i = node.ReadChildRef(i, 'param1')
		i = node.ReadChildRef(i, 'param2')
		return i

	def Read_938BED94(self, node):
		i = self.ReadHeaderLinkedElement(node)
		cnt, i = getUInt32(node.data, i)
		lst0 = {}
		for j in range(cnt):
			key, i = getLen32Text16(node.data, i)
			val, i = getLen32Text16(node.data, i)
			lst0[key] = val
		node.set('lst0', lst0)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_9A94E347(self, node): # FX-Attribute ToolBodyCache
		i = self.ReadHeaderLinkedElement(node, 'FxAttrToolBodyCache')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		cnt, i = getUInt32(node.data, i)
		i = self.ReadUInt32A(node, i, cnt, 'lst1', 4)
		return i

	def Read_A4087E1F(self, node): # FX-Attribute TappedHole
		i = self.ReadHeaderLinkedElement(node, 'FxAttrTappedHole')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadLen32Text16(i, 'standard')
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

	def Read_A5410F0A(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_A917F560(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_A9AEB67F(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadChildRef(i, 'brep')
		return i

	def Read_A9F6B271(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'participant')
		return i

	def Read_A98906A7(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'arr')
		return i

	def Read_AE5E4082(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_B269ACEF(self, node): # FX-Attrbute TaperTappedHole
		i = self.ReadHeaderLinkedElement(node, 'FxAttrTaperTappedHole')
		i = node.ReadLen32Text16(i, 'size')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadUInt32A(i, 5, 'a1')
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

	def Read_B447E0DC(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadFloat64_2D(i, 'a2')
		if (self.version > 2010):
			#i = node.ReadFloat64A(i, 9, 'a3')
			i += 9*8
		else:
			i += 4
		return i

	def Read_B59F6734(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt16A(i, 5, 'a1')
		return i

	def Read_B6482AF8(self, node):
		i = self.ReadHeaderLinkedElement(node)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'lst0')
		return i

	def Read_B6A36C30(self, node):
		i = self.ReadHeaderLinkedElement(node)
		cnt, i = getUInt32(node.data, i)
		lst = []
		for j in range(cnt):
			u32, i = getUInt32(node.data, i)
			u8, i  = getUInt8(node.data, i)
			tmp = u"lst0[%02X][2]" %(j)
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_, tmp)
			lst.append([u32, u8, node.get(tmp)])
			node.delete(tmp)
		node.set('lst0', lst, VAL_UINT32)
		return i

	def Read_B6C5116B(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_BB2150BF(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'parameter')
		return i

	def Read_BFD09C43(self, node): # FX-Attribute Sketch2D-Pre-Style
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'entity2')
		i = node.ReadFloat64A(i, 4, 'a1')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_C102267B(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_C6BE489C(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_C89EF3C0(self, node): # FX-Attribute Sketch2D-Pre-Style
		i = self.ReadHeaderLinkedElement(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64_2D(i, 'pos')
		return i

	def Read_CB71CED6(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_CCCB9A78(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadChildRef(i, 'ref_6')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_D5F19E40(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64_2D(i, 'pos')
		i = node.ReadFloat64_2D(i, 'dir')
		return i

	def Read_D5F19E41(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64_3D(i, 'a1')
		return i

	def Read_D5F19E42(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64A(i, 6, 'a1')
		return i

	def Read_D7F4C16F(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt16A(i, 5, 'a1')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_D938B973(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadList2(i, importerSegNode._TYP_LIST_SINT32_A_, 'lst0', 2)
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_D94F1914(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = self.ReadNtEntry(node, i, 'ntEntry1')
		i = self.ReadNtEntry(node, i, 'ntEntry2')
		return i

	def Read_DE9C63BD(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'participant')
		return i

	def Read_E047663E(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_E6158074(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUUID(i, 'uid')
		return i

	def Read_EB663664(self, node): #
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_ED3175C6(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadLen32Text16(i)
		return i

	def Read_ED7D8445(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'target')
		i = self.skipBlockSize(i)
		return i

	def Read_EE558505(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		return i

	def Read_EE558506(self, node):
		i = self.ReadHeaderLinkedElement(node)
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
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'ref_5')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_6')
		i = node.ReadCrossRef(i, 'ref_7')
		i = node.ReadCrossRef(i, 'offset1')
		i = node.ReadCrossRef(i, 'offset2')
		i = node.ReadCrossRef(i, 'ref_A')
		return i

	def Read_EE558508(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'parameter1')
		i = node.ReadCrossRef(i, 'direction')
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadCrossRef(i, 'parameter2')
		i = node.ReadCrossRef(i, 'parameter3')
		return i

	def Read_EEE03AF5(self, node): # FX-Attribute Sketch2D-Pre-Style
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadChildRef(i, 'entity2')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'entity3')
		i = node.ReadCrossRef(i, 'entity4')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64_2D(i, 'a1')
		i = self.skipBlockSize(i)
		if (self.version > 2010):
			i = node.ReadFloat64_3D(i, 'p1')
			i = node.ReadFloat64_3D(i, 'p2')
			i = node.ReadFloat64_2D(i, 'a2')
		return i

	def Read_F0B5F252(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'ref_0')
		return i

	def Read_F4B6001D(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		return i

	def Read_F8371DBE(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_FA6E9782(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64_2D(i, 'p1')
		i = node.ReadFloat64_2D(i, 'p2')
		return i

	def Read_FC9AAE10(self, node):
		i = self.ReadHeaderLinkedElement(node)
		return i

	def Read_FD590AA5(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_FD7702B0(self, node):
		i = self.ReadHeaderLinkedElement(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 9, 'a1')
		return i

	########################################
	# name table sections
	def Read_009A1CC4(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		cnt, i = getUInt32(node.data, i)
		lst = []
		#<LLHBdHHHBdHH (4+4+2+1+8+2+2+2+1+8+2+2 = 38 Bytes)
		s = Struct("<LLHBdHHHBdHH").unpack_from
		for j in range(cnt):
			a = s(node.data, i)
			i += 38
			lst.append(a)
		node.set('lst2', lst)
		return i

	def Read_0645C2A5(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadNtEntryList(node, i, 'entries')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 4, 'a1')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a2')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a3')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a4')
		i = node.ReadUInt32A(i, 3, 'a5')
		return i

	def Read_07BA7419(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8A(i, 4, 'a1')
		i = node.ReadUInt32A(i, 3, 'a2')
		return i

	def Read_081D7F77(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_0B7296C1(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 14, 'a2') # L L L L L L L L L L L L L L
		return i

	def Read_0BDC96E0(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_167018B8(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a2')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a3')
		i = node.ReadUInt32A(i, 2, 'a4')
		return i

	def Read_197F7DBE(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		return i

	def Read_1CC0C585(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_2169ED74(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		a1 = Struct("<LLLBLH").unpack_from(node.data, i)
		i += 19
		return i

	def Read_2892C3E0(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_357D669C(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadNtEntryList(node, i, 'entries')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'satAtrs', 5) # [asmKey, atrKey, type, 0, 0]
		return i

	def Read_4400CB30(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUUID(i, 'id')
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_45741FAF(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_4A944F03(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 4, 'a1')
		return i

	def Read_4DAB0A79(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_537799E0(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadNtEntryList(node, i, 'entries')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'f64_1')
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_56A95F20(self, node):
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadNtEntryList(node, i, 'entries')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 4, 'a2')
		return i

	def Read_6250D222(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_6CA15972(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		return i

	def Read_6F891B34(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 9, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_736C138D(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		cnt, i = getUInt32(node.data, i)
		i = self.ReadUInt32A(node, i, cnt, 'a1', 1)
		return i

	def Read_77D10C74(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		return i

	def Read_7E5D2868(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_821ACB9E(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_9C3D6A2F(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 3, 'a2')
		if (node.get('a2')[2] == 1):
			i = node.ReadUInt32A(i, 3, 'a3')
		else:
			node.set('a3', (0,0,0), VAL_UINT32)
		return i

	def Read_9D2E8361(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_A040D1B1(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 5, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		return i

	def Read_A13A1C3E(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		return i

	def Read_AF5EF9D0(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		return i

	def Read_AE0E267A(self, node):
		i = self.ReadList2U32(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		if (node.get('u32_1') == 1):
			i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadUInt32(i, 'u32_2')
			i = node.ReadUInt16A(i, 3, 'a1')
		else:
			i = node.ReadUInt32(i, 'u32_2')
			i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_AFD4E6A3(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadNtEntryList(node, i, 'entries')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst2', 7)
		return i

	def Read_B292F94A(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32U8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_CE4A0723(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt32(i, 'u32_2')
		lst = []
		cnt, i = getUInt32(node.data, i)
		s = Struct('<BdHH').unpack_from
		for j in range(cnt):
			a = s(node.data, i)
			i += 13
			lst.append(a)
		node.set('lst2', lst)
		return i

	def Read_D4A52F3A(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt8A(i, 2, 'a2')
		return i

	def Read_D7BE5663(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_DBD67510(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b1')
		i = node.ReadUInt32A(i, 3, 'a1') # if b1 == 0 => (0,0,0)
		i = node.ReadUInt32A(i, 2, 'a2') # if b1 == 1 => (0,0)
		return i

	def Read_DD64FF02(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a1')
		return i

	def Read_E70272F7(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_E9132E94(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32A(i, 4, 'a1')
		return i

	########################################
	# other Functions sections (TODO)

	def Read_01E0570C(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016): i += 4
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		return i

	def Read_2F1C7025(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 5, 'a0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_588B9053(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016): i += 4
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_207C8609(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016): i += 4
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u23_0')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		return i

	def Read_253BE3EB(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_4571AC37(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'sketch')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst0')
		return i

	def Read_470BB79E(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_4')
		if (self.version > 2016): i += 4
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_4CAA281F(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_5246A008(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		if (self.version > 2016): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_5BE20B76(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i)
		if (self.version > 2016): i += 4
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_D92A619C(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_5CE72F63(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		if (self.version > 2016): i += 4
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_4')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt8(i, 'u8_1')
		if(node.get('u8_1') == 1):
			i = self.ReadTransformation3D(node, i)
		return i

	def Read_0326C921(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		cnt, i = getUInt32(node.data, i)
		lst0={}
		for j in range(cnt):
			key, i = getLen32Text16(node.data, i)
			val, i = getLen32Text16(node.data, i)
			lst0[key] = val
		node.set('lst0', lst0, VAL_STR16)
		i = node.ReadUInt16(i, 'u16_1')
		return i

	def Read_040D7FB2(self, node):
		i = node.Read_Header0()
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
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
		node.set('lst0', lst0, VAL_UINT16)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_2')
		return i

	def Read_05520360(self, node): # FxCount
		i = node.Read_Header0('FxCount')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'anchors', 3)
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'parameter')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'center')
		return i

	def Read_077D9583(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		return i

	def Read_07AB2269(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadCrossRef(i, 'surface')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUUID(i, 'uid')
		return i

	def Read_0A52ED98(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016):
			i += 4
		i = node.ReadUInt16A(i, 3, 'a0')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_117806EE(self, node):
		i = node.Read_Header0()
		return i

	def Read_19F763CB(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'idx')
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = self.ReadEdgeList(node, i)
		i = node.ReadCrossRef(i, 'sketch')
		i = node.ReadFloat64_3D(i, 'a1')
		return i

	def Read_182D1C40(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_182D1C8A(self, node): # EmbeddedExcel
		i = node.Read_Header0('EmbeddedExcel')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_2')
		b, i = getBoolean(node.data, i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_1')
		if (not b):
			i = node.ReadLen32Text16(i)
			i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_2')
		hdr, i = getUInt32A(node.data, i, 2) # 30000002, Len, XXXXXXXX, XXXXXXXX, len x [bytes] => Excel-Workbook
		size = hdr[1]
		if (size > 0):
			i += 8
			buffer = node.data[i:i+size]
			dumpFolder = getDumpFolder()
			if (not (dumpFolder is None)):
				filename = u"%s/%s_%04X.xls" %(dumpFolder, node.typeName, node.index)
				with open(filename, 'wb') as xls:
					xls.write(buffer)
					node.set('filename', filename, None)
					try:
						node.set('workbook', open_workbook(file_contents=buffer), None)
					except Exception as ex:
						logWarning("Can't read Excel-Workbook '%s' - %s!", filename, ex)
			# logInfo(u"    INFO - found workbook: stored as %s!", filename)
		i += size
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		if (self.version > 2012): i += 16
		if (self.version > 2023): i += 1
		return i

	def Read_1C0E2EA7(self, node): # new in 2019
		i = node.Read_Header0()
		# ref_2
		# 00,00,00,00
		# 09,02,00,00
		# ref_1
		# 00
		return i

	def Read_1CAEFC09(self, node):
		i = node.Read_Header0()
#		i = node.ReadCrossRef(i, 'ref_1')
#		i = node.ReadCrossRef(i, 'ref_2')
#		i = node.ReadCrossRef(i, 'ref_3')
#		i = self.skipBlockSize(i)
#		i = node.ReadColorRGBA(i, 'color')
		return i

	def Read_258EC6E1(self, node): # Parameter Reference
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'n_0') # 3=length, 4=angle, 5=factor
		if (self.version > 2010):
			i = node.ReadUInt8(i, 'n_1')
		else:
			node.set('idx', 0, VAL_UINT8)
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadUInt32(i, 'n_2')
		return i

	def Read_27ECB60D(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt8A(i, 2, 'a0')
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_2B48A42B(self, node):
		i = node.Read_Header0()

		if (node.get('hdr').m == 0x12):
			i = 0
			node.delete('hdr')
			i = node.ReadLen32Text8(i, 'type')
			i = node.ReadUInt32A(i, 2, 'a0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT8_X_REF_, 'lst0')
			i = node.ReadUInt32(i, 'u32_2')
			i = node.ReadUInt32(i, 'u32_3')
			i = node.ReadUInt16(i, 'u16_3')
			i = node.ReadChildRef(i, 'next')
			i = node.ReadUInt32(i, 'flags')
			i = node.ReadParentRef(i)
			i = node.ReadUInt32(i, 'index')
			self.segment.indexNodes[node.get('index')] = node
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
								ref, i = self.ReadNodeRef(node, i, j, importerSegNode.REF_CROSS, 'properties')
								properties.append(ref)
							boolVal, i = getBoolean(node.data, i)
							boolData = importerSegNode.SecNode()
							boolData.uid  = UID('90874d28-11d0-d1f8-0008-cabc0663dc09}')
							boolData.segment = self.segment
							boolData.typeName = 'Boolean'
							boolData.set('value', boolVal)
							boolRef = importerSegNode.SecNodeRef(0xFFFFFFFF, importerSegNode.REF_CROSS)
							boolRef.data = boolData
							boolRef.number = 0x18
							ref, i = self.ReadNodeRef(node, i , len(properties), importerSegNode.REF_CROSS, 'properties')
							properties.append(ref)
							properties.append(None)
							properties.append(None)
							ref, i = self.ReadNodeRef(node, i , len(properties), importerSegNode.REF_CROSS, 'properties')
							properties.append(ref)
							i = node.ReadUInt32(i, 'u32_4')
							ref, i = self.ReadNodeRef(node, i , len(properties), importerSegNode.REF_CROSS, 'properties')
							properties.append(ref)
							i = node.ReadUInt32(i, 'u32_5')
							for j in range(11, 26):
								ref, i = self.ReadNodeRef(node, i, len(properties), importerSegNode.REF_CROSS, 'properties')
								properties.append(ref)
							node.references.append(boolRef)
							properties.append(boolRef)
							node.set('properties', properties, None)
					elif( t == 0x30000008):
						node.typeName = 'Sketch2D'
						i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_,'entities')
						i = node.ReadCrossRef(i, 'transformation')
						i = node.ReadCrossRef(i, 'direction')
			elif (u16_2 == 0x0003):
				node.typeName = 'Enum'
				node.set('Enum', 'PartFeatureOperation')
				node.set('Values', ['*UNDEFINED*', 'NewBody', 'Cut', 'Join', 'Intersection', 'Surface'])
				node.set('type', u16_1)
				node.set('value', 0, VAL_ENUM)
			elif (u16_2 == 0x0080):
				i = node.ReadUInt32(i, 'u32_2')
				if (self.version > 2017): i += 4
				i = node.ReadUInt32(i, 'u32_4')
				if (node.get('u16_1') == 0x2000):
					node.typeName = 'Point3D'
					i = node.ReadFloat64_3D(i, 'pos')
					i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'endPointOf')
					i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'centerOf')
				else:
					node.typeName = 'Plane'
					i = node.ReadUInt32(i, 'u32_5')
					i = node.ReadFloat64_3D(i, 'center')
					i = node.ReadFloat64_3D(i, 'a1')
					i = node.ReadFloat64_3D(i, 'normal')
			elif (u16_2 == 0xFFFF):
				pass
#				if (node.get('next') is not None):
#					node.typeName = 'Sketch3D'
#					node.set('numEntities', 0, None)
#					node.set('entities', [], None)
#				i = node.ReadUInt32(i, 'numEntities')
#				i = node.ReadList8(i, importerSegNode._TYP_NODE_X_REF_, 'entities')
#				i = node.ReadUInt32A(i, 2, 'a1')
#				i = node.ReadFloat64A(i, 6, 'a2')
			elif (u16_2 == 0x0010):
				if (u16_1 == 0x2000):
					i = node.ReadFloat64A(i, 6, 'a1')
		else:
			node.delete('hdr')
			i = self.ReadHeaderLinkedElement(node, 'FxAttrLabel')
			i = node.ReadUInt32(i, 'index')
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'participants')
			i = node.ReadLen32Text16(i)
			i = node.ReadUUID(i, 'uid')
		return i

	def Read_2C1BCAEA(self, node): # Helical3D_Parameters
		i = node.Read_Header0('Helical3D_Parameters')
		i = node.ReadCrossRef(i, 'param0')
		i = node.ReadCrossRef(i, 'param1')
		i = node.ReadCrossRef(i, 'param2')
		i = node.ReadCrossRef(i, 'param3')
		i = node.ReadCrossRef(i, 'param4')
		return i

	def Read_315C9CC8(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_31C98504(self, node):
		i = node.Read_Header0()
		#		00 00 00 00
		#		00 00 00 00
#		i = node.ReadCrossRef(i, 'ref_0')
#		i = node.ReadCrossRef(i, 'ref_1')
		#		00 00 00 00
		#		06 00 00 30 05 00 00 00 00 00 00 00 00 00 00 00
		#			A6 14 00 80:A2 14 00 80
		#			53 14 00 80:19 14 00 80
		#			5A 14 00 80:56 14 00 80
		#			5F 14 00 80:5B 14 00 80
		#			A1 14 00 80:9D 14 00 80
		return i

	def Read_3344C951(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt8A(i, 3, 'a0') # 00 02 00
		i = node.ReadLen32Text16(i)
		i = node.ReadChildRef(i, 'ref_1')
		# 00 00 00 00 00]
		return i

	def Read_3689CC91(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'lst0', 3)
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'parameter')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'parameter1')
		i = node.ReadCrossRef(i, 'parameter2')
		i = node.ReadCrossRef(i, 'parameter3')
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
		i = node.ReadList2(i, importerSegNode._TYP_TRANSFORMATIONS_, 'transformations')
		i = node.ReadUInt8(i, 'u8_2')
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
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_3A205AB4(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2015):
			i = node.ReadLen32Text16(i, 'txt0')
			i = node.ReadCrossRef(i, 'ref_2')
		else:
			node.set('txt0', 'FlatPattern')
		return i

	def Read_4E2F2EF0(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_58D705D0(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid')
		i = node.ReadLen32Text16(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 4, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 2, 'a4')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadChildRef(i, 'ref_4')
		i = node.ReadFloat64(i, 'f0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_3E863C3E(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		if (self.version < 2024):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_2D_UINT32_, 'lst1')
		else:
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_1D_UINT32_, 'lst1')
		return i

	def Read_B2D25560(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadUInt32(i, 'u32_0') # vgl. 3E863C3E.u_32 <=> version < 2024
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_4028CCAA(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_79D4DD11(self, node):
		i = self.Read_603428AE(node, None)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'matches')
		return i

	def Read_43CAB9D6(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadRefU32AList(node, i, 'ls0', 3, importerSegNode.REF_CHILD)
		return i

	def Read_452121B6(self, node): # Modeler Transaction Manager
		i = node.Read_Header0('ModelerTxnMgr')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'asm')
		if (node.get('asm') is not None):
			i = node.ReadUInt32(i, 'u32_0')
			if ((self.version > 2011) and (self.type == DCReader.DOC_PART)): i += 4 # skip 00 00 00 00
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_MDL_TXN_MGR_, 'lst_1') # <-> sat delta_states refs
#		if (self.version < 2013): i += 4
		i = node.ReadUInt32(i, 'u32_2')
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

	def Read_48C5F41A(self, node):
		i = node.Read_Header0()
		return i

	def Read_48CF47FA(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadUInt32A(i, 3, 'edge') # 0, edge ai-index, type (should be 2)
		i = node.ReadUInt32A(i, 3, 'pt1')  # 0, start-point ai-index, type (should be 1)
		i = node.ReadUInt32A(i, 3, 'pt2')  # 0, end-point ai-index, type (should be 1)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'sketch')
		i = node.ReadCrossRef(i, 'curve')
		i = node.ReadCrossRef(i, 'point1')
		i = node.ReadCrossRef(i, 'point2')
		return i

	def Read_534DD87E(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_55180D7F(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_553DA303(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadFloat64(i, 'x')
		return i

	def Read_57BF6FCE(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUUID(i, 'id')
		i = node.ReadFloat64A(i, 6, 'a0')
		return i

	def Read_6145BAFB(self, node):
		i = node.Read_Header0()
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_616DCA98(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
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

	def Read_61B56690(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_66085B35(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst0')
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

	def Read_6C7D97A9(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_6D1C07D1(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadChildRef(i, 'ref_4')
		i = node.ReadChildRef(i, 'ref_5')
		i = node.ReadChildRef(i, 'ref_6')
		i = node.ReadChildRef(i, 'ref_7')
		i = node.ReadChildRef(i, 'ref_8')
		i = node.ReadChildRef(i, 'ref_9')
		i = node.ReadChildRef(i, 'ref_10')
		i = node.ReadChildRef(i, 'ref_11')
		i = node.ReadChildRef(i, 'ref_12')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadChildRef(i, 'ref_13')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadChildRef(i, 'ref_14')
		return i

	def Read_0B857D8D(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text8(i, 'txt_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadLen32Text16(i, 'path')
		return i

	def Read_CE5C2D27(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text8(i, 'txt0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadLen32Text16(i, 'path')
		i = node.ReadLen32Text8(i, 'txt2')
		if (self.version > 2018):
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		else:
			node.set('lst0', [])
		return i

	def Read_72A7D774(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text8(i, 'txt0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		return i

	def Read_746BB6E6(self, node):
		i = node.Read_Header0('CornerSides')
		i = node.ReadCrossRef(i, 'side1')
		i = node.ReadCrossRef(i, 'side2')
		return i

	def Read_774572D4(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		if (self.version > 2016):
			i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_797737B1(self, node): # FxDimension
		i = node.Read_Header0('FxDimension')
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'anchors', 3)
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'parameter')
		return i

	def Read_7E0E4CA9(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016):
			i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUUID(i, 'id1')
		i = node.ReadUUID(i, 'id2')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_055674FF(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'owner')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version >  2012):
			i += 1 # skip 00
			if (self.version >  2017):
				i += 4
		i = self.Read2RefList(node, i, 'a1', importerSegNode.REF_CHILD, importerSegNode.REF_CHILD)
		i = node.ReadList4(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_1DCBFBA7(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'owner')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version >  2012):
			i += 1 # skip 00
			if (self.version >  2017):
				i += 4
		i = self.Read2RefList(node, i, 'a1', importerSegNode.REF_CHILD, importerSegNode.REF_CHILD)
		return i

	def Read_80102AC1(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'owner')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadChildRef(i, 'ref_2')
		if (self.version > 2012): i += 1 # skip 00
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		return i

	def Read_8398E8EC(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_845212C7(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 3)
		i = node.ReadCrossRef(i, 'component')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_855B1557(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		if (self.version > 2018): i += 4 # skip 00 00 00 00
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_86197AE1(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016): i += 4
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_872AC9CA(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2024): i += 4
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadBoolean(i, 'b_0')
		return i

	def Read_889E21C1(self, node):
		i = node.Read_Header0()
		return i

	def Read_30FDF0B9(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_8B3E95F7(self, node):
		i = node.Read_Header0('SurfaceDetail')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		return i

	def Read_DF3B2C5B(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_8DFFE0CD(self, node):
		i = node.Read_Header0()
		return i

	def Read_8EDEE6CB(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i, 3)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_907EAD2B(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016):
			i += 4
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_90874D13(self, node): # SketchEntityRef
		i = node.Read_Header0('SketchEntityRef')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i,  'u32_0')
		if (self.version > 2023): i+=4 # skip 00 00 00 00
		i = node.ReadUInt32(i,  'entityAI')  # association number of the entity inside the referenced sketch
		i = node.ReadUInt32(i,  'typEntity') # type of the entity (should be 2)
		i = node.ReadUInt32(i,  'u32_1')
		i = node.ReadUInt32(i,  'point1AI')  # association number of the start point inside the referenced sketch
		i = node.ReadUInt32(i,  'typPt1')    # type of the entity (should be 1)
		i = node.ReadUInt32(i,  'u32_2')
		i = node.ReadUInt32(i,  'point2AI')  # association number of the start point inside the referenced sketch
		i = node.ReadUInt32(i,  'typPt2')    # type of the entity (should be 1)
		i = node.ReadBoolean(i, 'posDir')    # Indicator for the orientation of edge (required for e.g. circles)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'sketch')
		return i

	def Read_90874D63(self, node): # PartComponentDefinition {DA33F1A3-7C3F-11D3-B794-0060B0F159EF}
		i = node.Read_Header0()
		if ((self.version > 2014) and (node.get('hdr').m == 36)):
			node.delete('hdr')
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
						i = node.ReadChildRef(i, 'next')
						i = node.ReadChildRef(i, 'unit')
						i = node.ReadChildRef(i, 'value')
						i = node.ReadFloat64(i, 'valueNominal')
						i = node.ReadFloat64(i, 'valueModel')
						i = node.ReadEnum16(i, 'tolerance', None, Tolerances)
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
			node.typeName = 'PartComponent'
			i = node.ReadChildRef(i, 'ref_0')
			i = node.ReadUInt16A(i, 2, 'a0')
			i = self.skipBlockSize(i)
			if (self.version > 2023): i += 4 # skip 00 00 00 00
			i = node.ReadChildRef(i, 'ref_1')
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'objects')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_X_REF_, 'parameters')
			i = node.ReadUInt32A(i, 2, 'a1')
			if (self.version > 2012): i += 4
			i = node.ReadUInt32(i, 'index')
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadList6(i, importerSegNode._TYP_MAP_UID_UINT32_, 'lst1') # used classID with count
			i = node.ReadList6(i, importerSegNode._TYP_MAP_UID_X_REF_, 'lst2')
			i = node.ReadCrossRef(i, 'ref_2')
			i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst3')
			i = node.ReadCrossRef(i, 'ref_3')
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

	def Read_95DC570D(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'value')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_9B043321(self, node):
		i = node.Read_Header0()
		return i

	def Read_1E3A132C(self, node, ln = 'Loop'):
		i = node.Read_Header0(ln)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'operation') # 8 = Fuse, 0 = Cut
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'edges') #
		i = node.ReadUInt32(i, 'faceIndex')
		return i

	def Read_A3277869(self, node): # Loop
		i = self.Read_1E3A132C(node, 'Loop3D')
		if (self.version > 2019): i += 4 # skip 00 00 00 00
		return i

	def Read_A78639EE(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_FLOAT64_A_, 'ls0', 3)
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'parameter')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'parameter1')
		i = node.ReadCrossRef(i, 'parameter2')
		i = node.ReadCrossRef(i, 'parameter3')
		i = node.ReadCrossRef(i, 'parameter4')
		i = node.ReadUInt16A(i, 3, 'a0')
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_A99F1B26(self, node):
		i = node.Read_Header0()
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
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_ACA8C0A4(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 4, 'a0')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a1')
		return i

	def Read_AF779E6E(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = self.ReadNtEntry(node, i, 'ntEntry1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadNtEntry(node, i, 'ntEntry2')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_B0B886C5(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_0')
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
		if (self.version > 2023):
			# ref -> ???
			# ref-list -> ???
			pass
		return i

	def Read_B1DFB58A(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_5')
		cnt, i = getUInt32(node.data, i)
		lst = []
		for j in range(cnt):
			i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0[%d]' %(cnt))
			l = node.get('lst0[%d]' %(cnt))
			a, i = getUInt16(node.data, i)
			b, i = getUInt16(node.data, i)
			if (a == 0x100):
				c, i = getFloat64A(node.data, i, 6)
			elif (a == 0x111):
				c, i = getFloat64A(node.data, i, 4)
			lst.append((l, a, b, c))
		return i

	def Read_B835A483(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_B91FCE52(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'dir')
		i = node.ReadCrossRef(i, 'ref_3')
		i = self.skipBlockSize(i)
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

	def Read_CADD6468(self, node): # BrepComponent
		i = node.Read_Header0('BrepComponent')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		if (self.version < 2024):
			i = node.ReadLen32Text16(i, 'unit_0')
			i = node.ReadLen32Text16(i, 'unit_2')
		else:
			i = node.ReadUInt32(i, 'key_0')
			i = node.ReadUInt32(i, 'key_1')
		return i

	def Read_1F213DE0(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 3)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_1F535F68(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid')
		i = node.ReadLen32Text16(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32A(i, 3, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 4, 'a2')
		i = self.skipBlockSize(i)
		return i

	def Read_CB072B3B(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadFloat64A(i, 5, 'a1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64A(i, 6, 'a2')
		if (self.version > 2014):
			i = node.ReadUUID(i, 'uid1')
			i = node.ReadUUID(i, 'uid2')
			i = node.ReadUUID(i, 'uid3')
			i = node.ReadUUID(i, 'uid4')
			if (self.version > 2023): i += 33 # skip 00...
		return i

	def Read_CB370222(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_CC0F7521(self, node): # AsmEntityWrapper
		i = node.Read_Header0('AsmEntityWrapper')
		i = node.ReadUInt32(i, 'index')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'asm')
		i = node.ReadUInt32(i, 'u32_1')
		i += 4
		return i

	def Read_CCE264C4(self, node):
		i = node.Read_Header0()
		return i

	def Read_CD1423D9(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		if (self.version > 2024): i += 4 # skip 00 00 00 00
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadList2(i, importerSegNode._TYP_STRING16_, 'lst1')
		return i

	def Read_D589D818(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016):
			i += 4
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt8(i, 'u8_0')

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
		i = node.ReadUInt32A(i, 2, 'a2')
		i = node.ReadUInt16A(i, 3, 'a3')
		if (self.version > 2024): i += 3 # skip 01 00 00
		i = node.ReadUInt8A(i, 2, 'a5')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadLen32Text16(i, 'txt2')
		i = node.ReadUInt32A(i, 11, 'a4')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_D95B951A(self, node): # Display decimals
		i = node.Read_Header0('DisplayDecimals')
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt16(i, 'length')
		i = node.ReadUInt16(i, 'angle')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_DA2C89C5(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		if (self.version > 2016):
			i += 4
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_DBA6E2CF(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64_3D(i, 'p1')
		i = node.ReadFloat64_3D(i, 'p2')
		cnt, i = getUInt32(node.data, i)
		lst = []
		s = Struct("<HLddddddddd").unpack_from
		for j in range(cnt):
			ref, i = self.ReadNodeRef(node, i, [j, 0], importerSegNode.REF_CHILD, 'lst0')
			a = s(node.data, i)
			i += 78
			lst.append((ref, a[0], a[1], a[2:5], a[5:8], a[8:11]))
		node.set('lst0', lst)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_DBDD00E3(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32(i, 'numEntities')
		i = node.ReadCrossRef(i, 'sketch')
		cnt, i = getUInt32(node.data, i)
		lst = []
		for j in range(cnt):
			ref, i = self.ReadNodeRef(node, i, [j, 0], importerSegNode.REF_CHILD, 'lst0')
			a, i = getUInt32A(node.data, i, 3)
			lst.append([ref, a])
		node.set('lst0', lst)
		return i

	def Read_DDBFFD2F(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadSInt32A(i, 3, 'a0')
		return i

	def Read_E192FA73(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'parameters')
		return i

	def Read_E28D3B3F(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 3, 'a0')
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

	def Read_E75FF898(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		cntJ, i = getUInt32(node.data, i)
		lstJ = []
		s1   = Struct("<dddLddddddddd").unpack_from
		s2   = Struct("<BL").unpack_from
		for j in range(cntJ):
			a1 = s1(node.data, i)
			i += 100
			cntM, i = getUInt32(node.data, i)
			lstM = []
			dummy = []
			for m in range(cntM):
				cntN, i = getUInt32(node.data, i)
				lstN = []
				for n in range(cntN):
					a2 = s2(node.data, i)
					i += 5
					lstN.append(a2)
				dummy.append(",".join(["(%s,%s)" %(a2[0], a2[1]) for a2 in lstN]))
				lstM.append(lstN)
			lstJ.append(a1 + (lstM,))
		node.set('lst', lstJ)
		return i

	def Read_EE311CA5(self, node): # new in 2019
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst1')
		return i

	def Read_F0F5EB21(self, node): # new in 2019
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_F10C26A4(self, node):
		i = node.Read_Header0()
		return i

	def Read_F2C761B8(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_F3FC69C6(self, node): # SurfaceCreator
		i = node.Read_Header0('SurfaceCreator')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		if (self.version > 2023): i += 4 # skip 00 00 00 00
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'surface')
		i = node.ReadChildRef(i, 'ref_3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadUInt16(i, 'idxCreator')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_F5E51520(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i, 2)
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_F8A779F9(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_F90DC646(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.Read2RefList(node, i, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U32_, 'lst1')
		return i

	def Read_FC86960C(self, node):
		cnt, i = getUInt32(node.data, 0)
		lst    = []
		for j in range(0, cnt):
			t, i = getUInt16(node.data, i)
			if (t == 0):
				f, i = self.ReadEdge(node, i)
				lst.append(f)
			elif (t == 1):
				f, i = getUInt32A(node.data, i, 2)
				lst.append(f)
		node.set('edges', lst, VAL_UINT32)
		return i

	def Read_216B3A55(self, node, typeName = None):
		i = node.Read_Header0(typeName)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version < 2015):
			i = node.ReadUInt32A(i, 2, 'a0')
		else:
			i = node.ReadLen32Text16(i)
			i = node.ReadUUID(i, 'uid1')
			i = node.ReadUUID(i, 'uid2')
		return i

	def Read_E273976D(self, node):
		i = self.Read_216B3A55(node)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64A(i, 6, 'a2')
		i = node.ReadUUID(i, 'uid3')
		return i

	def ReadHeaderCntSLRS(self, node, typeName = None):
		if (not typeName is None):
			node.typeName = typeName
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.skipBlockSize(i)
		return i

	def Read_1E9612BA(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_0')
		i += 4
		return i

	def Read_4E86F048(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_0')
		i += 4
		if (self.version > 2012): i += 1
		return i

	def Read_4E86F04A(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_0')
		i += 4
		if (self.version > 2012): i += 1
		return i

	def Read_4E86F04B(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_0')
		i += 4
		if (self.version > 2012): i += 1
		return i

	def Read_5B10BF5B(self, node):
		i = self.ReadHeaderCntSLRS(node)#
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_0')
		i += 4
		return i

	def Read_668BF010(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_0')
		i += 4
		i = self.skipBlockSize(i)
		return i

	def Read_AE1C96C9(self, node): # Harness
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_B2D4290F(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_0')
		i += 4
		if (self.version > 2012): i += 1
		return i

	def Read_FA0306F9(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32(i, 'u32_0')
		i += 4
		if (self.version > 2012): i += 1
		i = node.ReadLen32Text16(i)
		return i

	def Read_32C3DC38(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_6B19C0D9(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_B8E70BB5(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		return i

	def Read_2EBC1160(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		if (self.version > 2017):
			i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_659BE14E(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_X_REF_, 'lst1')
		return i

	def Read_34AACB53(self, node):
		i = self.ReadHeaderCntSLRS(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt32(i, 'cnt_lst1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	#######################
	# header + reference + class info + UInt32 sections
	def ReadHeaderRefClsInfU32(self, node, typeName = None, ref1 = 'ref_0', ref2 = 'ref_1', u32 = 'u32_0'):
		i = self.ReadHeadersS32ss(node, typeName)
		i = node.ReadCrossRef(i, ref1)
		i = self.skipBlockSize(i)
		i = self.ReadClassInfo(node, i, ref2)
		i = node.ReadUInt32(i, u32)
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		i = self.skipBlockSize(i)
		return i

	def Read_0C48B861(self, node):
		i = self.ReadHeaderRefClsInfU32(node, ref1='plane0', ref2='plane1')
		return i

	def Read_A76B22A0(self, node):
		i = self.ReadHeaderRefClsInfU32(node, ref2='body', u32='wireIndex')
		return i

	#######################
	# header + reference + class info + UInt32 + list2 sections
	def ReadHeaderRefClsInfU32L2(self, node, typeName = None, ref1 = 'ref_0', ref2 = 'ref_1', u32 = 'u32_0', lst='lst0'):
		i = self.ReadHeaderRefClsInfU32(node, typeName, ref1, ref2, u32)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, lst)

	def Read_0830C1B0(self, node): # Location of a 2D-Point
		i = self.ReadHeaderRefClsInfU32L2(node, typeName='LocationPoint2D', ref1='point3D', ref2='point2D')
		return i

	def Read_1638E00D(self, node):
		i = self.ReadHeaderRefClsInfU32L2(node)
		return i

	def Read_93C7EE68(self, node):
		i = self.ReadHeaderRefClsInfU32L2(node, ref1='entity3D', ref2='entity2D')
		return i

	#######################
	# header + class info + UInt32 sections
	def ReadHeaderClsInfU32(self, node, typeName = None, ref = 'ref_1', u32 = 'u32_0'):
		i = self.ReadHeadersS32ss(node, typeName)
		i = self.ReadClassInfo(node, i, ref)
		i = node.ReadUInt32(i, u32)
		if (self.version > 2017): i += 4 # skip 00 00 00 00
		i = self.skipBlockSize(i)
		return i

	def Read_5D807360(self, node):
		i = self.ReadHeaderClsInfU32(node, ref='plane')
		i = node.ReadCrossRef(i, 'direction')
		return i

	def Read_618C9E00(self, node):
		i = self.ReadHeaderClsInfU32(node, ref='entity')
		i = node.ReadCrossRef(i, 'parameter')
		i = node.ReadCrossRef(i, 'direction')
		return i

	def Read_F0769409(self, node):
		i = self.ReadHeaderClsInfU32(node, ref='body', u32='wireIndex')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt8(i, 'u8_2')
		return i

	def Read_222D217D(self, node):
		i = self.ReadHeaderClsInfU32(node, ref='body', u32='wireIndex')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt16(i, 'u16_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'direction')
		i = self.ReadNtEntry(node, i, 'ntEntry1')
		return i

	def Read_36286857(self, node):
		i = self.ReadHeaderClsInfU32(node, ref='body', u32='wireIndex')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadList8(i, importerSegNode._TYP_UINT32_, 'lst1')
		i = node.ReadUInt16(i, 'u16_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.ReadNtEntry(node, i, 'ntEntry')
		return i

	def Read_35624AC4(self, node):
		# 01 01 00 00 00 00 00 00 01 00 00 00 00 00 00 00 00 00
		i = node.ReadUInt16A(0, 9, 'a0')
		return i

	def Read_5CC350B8(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadParentRef(i)
		i = node.ReadSInt32(i, 's32_1')
		return i

	def Read_CF5DF2C4(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		if (self.version > 2016):
			i += node.ReadChildRef(i, 'ref_3')
		return i

	def Read_8B21126C(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_AF3FD35E(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32A(i, 3, 'a0')
		if (self.version > 2015):
			i = node.ReadLen32Text16(i, 'txt')
		else:
			node.set('txt', '')
		return i

	def Read_98A24D9A(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadParentRef(i)
		return i

	def Read_8840FC91(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		return i

	def Read_8840FC92(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		return i

	def Read_8840FC94(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 5, 'a0')
		if (self.version > 2015): i += 4 # skip 00 00 00 00
		if (self.version > 2016): i = node.ReadChildRef(i, 'ref_3')
		return i

	def Read_5CC8ED7F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1') # < BHB
		i = node.ReadFloat64(i, 'f0')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'b0')
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadCrossRef(i, 'ref_3')
		if (self.version > 2016): i = len(node.data)
		return i

	def Read_AF3FD35F(self, node):
		i = self.ReadHeadersS32ss(node)
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'description')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'ref_0')
		# 01 00 00 00 19 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 F0 3F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 F0 3F 00 00 00 00 00 00 00 00 00
		# 02 00 00 30 00 00 00 00
		return i

	def Read_F5A5AA8A(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadUInt32A(i, 6, 'a0')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadFloat64A(i, 10, 'a1')
		i = node.ReadUInt32A(i, 2, 'a2')
		i = node.ReadBoolean(i, 'b1')
		i = node.ReadCrossRef(i, 'ref_2')
		if (self.version > 2015):
			i = node.ReadLen32Text16(i, 'txt')
			i += 8 # skip 01 00 00 00 00 00 00 00
		else:
			node.set('txt', '', VAL_STR16)
		return i

	def Read_25096F44(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i, 2)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 6, 'a0')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadFloat64A(i, 3, 'a1')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadFloat64(i, 'f')
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_381FAE32(self, node):
		i = self.ReadHeaderContent(node)
		n, j = getSInt32(node.data, i)
		if (n == -1): i = j
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = node.ReadUInt32A(i, 4, 'a0')
		return i

	def Read_8840FC97(self, node):
		i = self.ReadHeaderContent(node)
		i = self.skipBlockSize(i, 2)
		n, j = getSInt32(node.data, i)
		if (n == -1): i = j
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_C903C161(self, node):
		i = self.ReadHeaderContent(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt32(i, 'flags2')
		i = node.ReadUInt16A(i, 3, 'a0')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		return i

	def Read_976169A3(self, node):
		i = self.ReadHeaderContent(node)
		n, j = getSInt32(node.data, i)
		if (n == -1): i = j
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadFloat64A(i, 15, 'a0')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadFloat64_3D(i, 'pos')
		if (self.version > 2017): i += 4 # skip ref i = node.ReadChildRef(i, 'ref_4')
		return i

	def Read_A21C387B(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst1')
		return i

	def Read_8F70B280(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'a0') # 00 00 00 00 00 00 00 00
		i = node.ReadChildRef(i, 'ref_2')
		return i

	def Read_CCC5085A(self, node): # Assembly/Part-FaceMergeData
		i = node.Read_Header0('FaceMergeData')
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'nameTable')
		i = self.ReadRefU32AList(node, i, 'lst0', 2, importerSegNode.REF_CROSS)
		i = self.ReadRefU32ARefU32List(node, i, 'lst1', 2)
		i = self.ReadRefU32ARefU32List(node, i, 'lst2', 1)
		cnt, i = getUInt32(node.data, i)
		lst = []
		# remember node content as it will be overwritten by ReadList2!
		for j in range(cnt):
			u32_0, i = getUInt32(node.data, i)
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'tmp', 2)
			lst0 = node.get('tmp')
			u32_1, i = getUInt32(node.data, i)
			i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'tmp', 2) # this is ref + uint!
			lst1 = node.get('tmp')
			lst.append([u32_0, lst0, u32_1, lst1])
		node.delete('tmp')
		node.set('lst3', lst, VAL_UINT32)
		return i

	def ReadHeaderI32RefBol(self, node, typeName = None):
		i = node.Read_Header0(typeName)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		return i

	def Read_5DDB6DAF(self, node): # Presentation-FaceMergeData
		i = self.ReadHeaderI32RefBol(node, 'FaceMergeData')
		i = node.ReadList3(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadCrossRef(i, 'default')
		return i

	def Read_8EA39F26(self, node):
		i = self.ReadHeaderI32RefBol(node)
		i = node.ReadList3(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadBoolean(i, 'b1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		return i

	def Read_A014A2CF(self, node):
		i = self.ReadHeaderI32RefBol(node)
		i = node.ReadList3(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'scene')
		return i

	def Read_D5F5CCA1(self, node):
		i = self.ReadHeaderI32RefBol(node)
		i = self.ReadTransformation3D(node, i)
		i = self.ReadClassInfo(node, i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_A79EACCF(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_4E17C8BC(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadFloat32(i, 'f')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		return i

	def Read_A79EACC7(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'min')
		i = node.ReadFloat64_3D(i, 'max')
		return i

	def Read_A79EACCC(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'pos')
		i = node.ReadFloat64A(i, 9, 'a1')
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_8840FC95(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'index')
		i = self.skipBlockSize(i, 2)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 6, 'a2')
		return i

	def Read_4EABC45E(self, node):
		i = node.Read_Header0()
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_6759D870(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		if (self.version > 2012):
			i = node.ReadList7(i, importerSegNode._TYP_MAP_TEXT8_REF_, 'lst0')
		else:
			i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT8_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_UID_REF_, 'lst1')
		i = node.ReadFloat64A(i, 24, 'a0')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		if (self.version > 2010): i += 4*4 + 15*8 + 5*4 + 3*1 # 2011: d d d d d d d d d d b f f f f f b b d L d L d d d L L]
		if (self.version > 2011): i += 4                      # L
		if (self.version > 2010): i += 3*4 + 1                # L L L b
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version > 2012): i += 1 # 2013: [b]
		if (self.version > 2016): # 2016: [b L d d d d L f f f f f b @]
			i += 1+4+4+4+4+4+4+4+4+4+4+4+1
			i = node.ReadLen32Text16(i)
			if (self.version > 2017): i += 4 # 2017: [f]
			if (self.version > 2017): i += 1 # 2018: [b]
		else:
			node.name = 'GreyRoom'
		return i

	def Read_F3A02CB6(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'index')
		i = self.skipBlockSize(i, 2)
		if (self.version > 2018): i += 4 # skip FF FF FF FF
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadParentRef(i)
		i = self.ReadTransformation3D(node, i, 'xform1')
		i = self.ReadTransformation3D(node, i, 'xform2')
		i = node.ReadBoolean(i, 'b0')
		if (self.version < 2017): i += 18*4
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadChildRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		if (self.version < 2017): i += 1 # skip bool
		if (self.version > 2012):
			if (self.version < 2017):
				i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT8_REF_, 'lst0')
				i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT8_REF_, 'lst1')
			else:
				i += 12 # skip L f f f
				i = node.ReadChildRef(i, 'ref_4')
				if (self.version > 2017):
					i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		return i

	def Read_CBCD9A31(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst2')
		return i

	def Read_CBCD9A32(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		return i

	def Read_FDA6D020(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text8(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadParentRef(i)
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2012): i += 4 # skip 00 00 00 00
		return i

	def Read_6759D86F(self, node):
		i = node.Read_Header0()
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadLen32Text16(i, 'txt_1')
		i = self.skipBlockSize(i)
		if (self.version > 2012):
			t, i = getLen32Text16(node.data, i) # -> UID_2
			t, i = getLen32Text16(node.data, i) # -> txt_0
			t, i = getLen32Text16(node.data, i) # -> UID_1
#		i = node.ReadColorRGBA(i, 'Color1.c0')
#		i = node.ReadColorRGBA(i, 'Color1.c1')
#		i = node.ReadColorRGBA(i, 'Color1.c2')
#		i = node.ReadColorRGBA(i, 'Color1.c3')
#		i = node.ReadFloat32(i, 'f32_0')
#		i = self.skipBlockSize(i)
#		i = node.ReadLen32Text16(i, 'txt_2')
#		i = node.ReadBoolean(i, 'b1')
#		i = node.ReadColorRGBA(i, 'Color2.c0')
#		a = Struct('<dllLbld').unpack_from(node.data, i)
#		node.set('a1', a)
#		i += 33
#		i = node.ReadLen32Text16(i, 'txt_3')
#		i = node.ReadUInt32(i, 'u32_2')
#		i = node.ReadFloat64_3D(i, 'a2')
#		i = node.ReadLen32Text16(i, 'txt_4')
#		if (self.version > 2010):
#			i = node.ReadLen32Text16(i, 'txt_5')
#			i = node.ReadFloat32_2D(i, 'a3')
		return i

	def Read_1E5CBB86(self, node):
		i = node.Read_Header0()
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = self.skipBlockSize(i)
		i = node.ReadColorRGBA(i, 'color')
		i = node.ReadList2(i, importerSegNode._TYP_U16_COLOR_, 'lights')
		i = node.ReadFloat32A(i, 3, 'a1')
		i = len(node.data)
		return i

	def Read_8AF12C98(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_0')
		if (self.version > 2016):
			i = node.ReadChildRef(i, 'ref_1')
			i = node.ReadChildRef(i, 'ref_2')
			i = node.ReadChildRef(i, 'ref_3')
		return i

	def Read_F393AC93(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		return i

	def Read_A2A5CCEC(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 5, 'a0')
		return i

	def Read_52426994(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_3235A9B8(self, node):
		i = node.Read_Header0()
		i = node.ReadUUID(i, 'uid')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_TEXT16_UINT32_, 'lst1')
		i = node.ReadChildRef(i, 'cld_0')
		if (self.version > 2010): i += 4 # skip 01 00 00 00
		if (self.version > 2017): i += 8
		return i

	def Read_E454FA4D(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_U32_TXT_TXT_DATA_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, importerSegNode._TYP_U32_TXT_U32_LST2_, 'lst1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT16_A_, 'lst2', 2)
		return i

	def Read_20E5921B(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'scene')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_UID_REF, 'lst0')
		i = node.ReadUInt32A(i, 5, 'a0')
		i = node.ReadLen32Text16(i)
		return i


	def Read_34210B4B(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'scene')
		i = node.ReadUUID(i, 'uid')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i, 'txt0')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_X_REF_REF_, 'lst0')
		i = node.ReadFloat64A(i, 11, 'a0')
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_179808F1(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U8_, 'lst0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_U32_U8_, 'lst1')
		return i

	def Read_9B49FAA0(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a0')
		return i

	def Read_948FD019(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = self.ReadTransformation3D(node, i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt8A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_2578E638(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_120284EF(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_022AC1B5(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadColorRGBA(i, 'c0')
		i = node.ReadColorRGBA(i, 'c1')
		i = node.ReadColorRGBA(i, 'c2')
		i = node.ReadColorRGBA(i, 'c4')
		i = node.ReadFloat32(i, 'f')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_48EB8608(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadColorRGBA(i, 'c0')
		i = node.ReadColorRGBA(i, 'c1')
		i = node.ReadColorRGBA(i, 'c2')
		i = node.ReadColorRGBA(i, 'c3')
		i = node.ReadColorRGBA(i, 'c4')
		i = node.ReadFloat32(i, 'f')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_48EB8607(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_B32BF6A3(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_B32BF6AB(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_76986821(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_2E56FF78(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.ReadClassInfo(node, i, 'ref_2')
		return i

	def Read_022AC1B1(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadBoolean(i, 'b0')
		i = self.ReadClassInfo(node, i, 'ref_1')
		return i
