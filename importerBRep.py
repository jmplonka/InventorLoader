# -*- coding: utf-8 -*-

'''
importerNotebook.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegNode    import _TYP_UINT32_, _TYP_UINT32_A_, _TYP_NODE_REF_, _TYP_MAP_U32_U32_, _TYP_TRANSFORMATIONS_, _TYP_MAP_KEY_REF_, REF_CHILD, REF_CROSS
from importerSegment    import checkReadAll
from importer_NameTable import NameTableReader
from importerUtils      import *
from importerConstants  import VAL_UINT16
import importerSegNode

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class BRepReader(NameTableReader):
	def __init__(self, segment):
		super(BRepReader, self).__init__(segment)

	def ReadHeaderNameTableChild3Node(self, node, typeName = None):
		i = self.ReadHeaderNameTableChild1Node(node, typeName)
		i = node.ReadSInt32A(i, 7, 'a0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadList2(i, _TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadRefU32List(node, i, 'a2', REF_CROSS)
		i = self.skipBlockSize(i)
		return i

	def Read_E9132E94(self, node):
		i = self.ReadHeaderNameTableChild1Node(node)
		return i

	def Read_009A1CC4(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		i = node.ReadUInt32(i, 'u32_1')
		s = Struct('<LLBHdHHHBdHH').unpack_from
		cnt, i = getUInt32(node.data, i)
		lst = []
		for j in range(cnt):
			a = s(node.data, i)
			i += 38
			lst.append(a)
		node.set('a1', lst)
		return i

	def Read_0645C2A5(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, _TYP_UINT32_, 'lst0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUUID(i, 'uid')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadList2(i, _TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 10, 'a1')
		return i

	def Read_07BA7419(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_0BDC96E0(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_167018B8(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_1CC0C585(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_2169ED74(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_2892C3E0(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_357D669C(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_4DAB0A79(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_537799E0(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_56A95F20(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		i = node.ReadUInt32A(i, 4, 'a1')
		return i

	def Read_0B7296C1(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		i = node.ReadUInt32A(i, 4,  'a1')
		i = node.ReadUInt32A(i, 10, 'a3')
		return i

	def Read_6F891B34(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_736C138D(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_77D10C74(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_7E5D2868(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_821ACB9E(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_9D2E8361(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_AE0E267A(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_AFD4E6A3(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_B292F94A(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_D4A52F3A(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_E70272F7(self, node):
		i = self.ReadHeaderNameTableChild3Node(node)
		return i

	def Read_CC0F7521(self, node): # AsmEntityWrapper
		i = node.Read_Header0('AsmEntityWrapper')
		i = node.ReadUInt32(i, 'indexDC')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadChildRef(i, 'asm')
		i = node.ReadUInt32(i, 'wrapperIdx')
		i += 4
		return i

	def Read_EA7DA988(self, node): # AcisEntityContainer
		i = node.Read_Header0('AcisEntityContainer')
		i = node.ReadList8(i, _TYP_NODE_REF_, 'wrappers')
		return i

	#######################
	# BRep component

	def Read_CADD6468(self, node): # BrepComponent
		i = node.Read_Header0('BrepComponent')
		i = node.ReadList6(i, _TYP_MAP_KEY_REF_, 'components')
		if (self.version < 2023):
			i = node.ReadLen32Text16(i, 'length')
			i = node.ReadLen32Text16(i, 'angle')
		else:
			i = node.ReadUInt32(i, 'length')
			i = node.ReadUInt32(i, 'angle')
		return i

	def ReadHeaderBRepComponent(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'dcCreatorIdx') # the creator' index in 'DC' segment
		i = node.ReadUInt16(i, 'u16_0')
#		i = node.ReadList6(i, _TYP_MAP_U32_U32_, 'components')
		i = node.ReadList6(i, _TYP_MAP_KEY_REF_, 'components')
		i = self.skipBlockSize(i)
		return  i

	def Read_09DABAE0(self, node):
		i = self.ReadHeaderBRepComponent(node)
		i = node.ReadList2(i, _TYP_TRANSFORMATIONS_, 'transformations')
		return i

	def Read_3DE78F81(self, node):
		i = self.ReadHeaderBRepComponent(node)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadLen32Text16(i)
		i = node.ReadBoolean(i, 'b1')
		i = node.ReadFloat64A(i, 9, 'a0')
		i = node.ReadUInt32A(i, 11, 'a1')
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUUID(i, 'uid_1')
		cnt, i = getUInt32(node.data, i)
		lst = []
		s = Struct('<LLd').unpack_from
		for k in range(cnt):
			a = s(node.data, i)
			i += 16
			lst.append(a)
		node.set('a2', lst)
		cnt, i = getUInt32(node.data, i)
		lst = []
		for k in range(cnt):
			j, i = getUInt32(node.data, i)
			t, i = getLen32Text8(node.data, i)
			a, i = getFloat64A(node.data, i, 6)
			lst.append((j, t, a))
		node.set('a3', lst)
		return i

	def Read_481DFC84(self, node):
		i = self.ReadHeaderBRepComponent(node)
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadBoolean(i, 'b1')
		i = node.ReadFloat64_3D(i, 'axis')
		i = node.ReadFloat64_3D(i, 'center')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64_2D(i, 'a2')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadList2(i, _TYP_UINT32_, 'lst0')
		return i

	def Read_66085B35(self, node):
		i = self.ReadHeaderBRepComponent(node)
		return i

	def Read_6985F652(self, node):
		i = self.ReadHeaderBRepComponent(node)
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64(i, 'f0')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadList2(i, _TYP_UINT32_, 'lst0')
		return i

	def Read_6D0B7807(self, node):
		i = self.ReadHeaderBRepComponent(node)
		i = node.ReadFloat64(i, 'f0')
		i = node.ReadUInt16(i, 'u16_1')
		cnt, i = getUInt32(node.data, i)
		lst = []
		for k in range(cnt):
			a, i = getUInt16(node.data, i)
			lst.append(a)
		node.set('a0', lst, VAL_UINT16)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt16(i, 'u16_2')
		i = node.ReadBoolean(i, 'b0')
		i = node.ReadFloat64A(i, 8, 'a1')
		return i

	def Read_ABD292FD(self, node):
		i = self.ReadHeaderBRepComponent(node)
		# Array of [<LHH[d]...]
		return i

	def Read_BFED36A9(self, node):
		i = self.ReadHeaderBRepComponent(node)
		t, i = getUInt32(node.data, i)
		if (t == 0x0203): t, i = getUInt32(node.data, i)
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadFloat64_3D(i, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		i = node.ReadList2(i, _TYP_UINT32_, 'lst0')
		return i

	def Read_D797B7B9(self, node):
		i = self.ReadHeaderBRepComponent(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = node.ReadLen32Text16(i, 'txt1')
		i = node.ReadFloat64A(i, 5, 'a1')
		i = node.ReadLen32Text16(i, 'txt2')
		i = node.ReadFloat64_3D(i, 'a2')
		i = node.ReadUInt32A(i, 2, 'a3')
		i = node.ReadUInt16A(i, 3, 'a4')
		if (self.version > 2024): i += 3 # skip 01 00 00
		i = node.ReadUInt8A(i, 2, 'a5')
		i = node.ReadLen32Text16(i, 'txt3')
		i = node.ReadLen32Text16(i, 'txt4')
		return i

	def Read_DDA265D6(self, node):
		i = self.ReadHeaderBRepComponent(node)
		i = node.ReadParentRef(i)
		return i

	####################
	# SAT History

	def Read_F78B08D5(self, node):
		i = node.Read_Header0('SatHistory')
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, _TYP_UINT32_, 'numbers') # see "*_sat.history" file for details
		i = node.ReadList6(i, _TYP_MAP_KEY_REF_, 'delta_states')
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def ReadHeaderDeltaStateItem(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadCrossRef(i, 'root')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i,'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'nameTable')
		return i

	def Read_09780457(self, node):
		node.TypeName = 'DeltaState'
		i = self.skipBlockSize(0)
		i = node.ReadParentRef(i)
		i = node.ReadSInt32(i, 'data_set') # the number of the data_set in the sat file
		i = node.ReadList2(i, _TYP_NODE_REF_, 'items')
		return i

	def Read_5363C623(self, node): # delta state item ???
		i = self.ReadHeaderDeltaStateItem(node)
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_632A4BBA(self, node): # delta state item ???
		i = self.ReadHeaderDeltaStateItem(node)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadChildRef(i, 'ref_1')
		i = self.ReadRefU32List(node, i, 'a2', REF_CHILD)
		return i

	def Read_766EA5E5(self, node): # delta state item ???
		i = self.ReadHeaderDeltaStateItem(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadCrossRef(i, 'asm')
		i = node.ReadUInt32(i, 'wrapperIdx')
		return i

	def Read_A618B833(self, node): # delta state item ???
		i = self.ReadHeaderDeltaStateItem(node)
		i = node.ReadList2(i, _TYP_UINT32_A_, 'lst0', 2)
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_BA0B8C23(self, node): # delta state item ???
		i = self.ReadHeaderDeltaStateItem(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.ReadRefU32List(node, i, 'a2', REF_CROSS)
		ref, i = self.ReadNodeRef(node, i, None, REF_CROSS, 'a3')
		number, i = getUInt32(node.data, i)
		if (ref): ref.number = number
		i = self.ReadRefU32List(node, i, 'a3', REF_CROSS)

		i = node.ReadUInt32A(i, 3, 'a4')
		ref, i = self.ReadNodeRef(node, i, None, REF_CROSS, 'a5')
		number, i = getUInt32(node.data, i)
		if (ref): ref.number = number
		i = self.ReadRefU32List(node, i, 'a6', REF_CROSS)
		return i

	def Read_C620657B(self, node): # delta state item ???
		i = self.ReadHeaderDeltaStateItem(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList2(i, _TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.ReadRefU32List(node, i, 'a2', REF_CROSS)
		i = node.ReadUInt32(i, 'u32_3')
		i = node.ReadList2(i, _TYP_UINT32_A_, 'lst2', 2)
		i = node.ReadUInt32(i, 'u32_4')
		i = self.ReadRefU32List(node, i, 'nameTables', REF_CROSS)
		return i
