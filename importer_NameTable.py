# -*- coding: utf-8 -*-

'''
importer_NameTable.py:
'''

import importerSegNode

from importerSegment import SegmentReader
from importerUtils   import *
from importerSegNode import _TYP_NODE_REF_, _TYP_NODE_X_REF_, _TYP_UINT32_A_, _TYP_NT_ENTRY_, REF_CHILD, REF_CROSS
from importerClasses import NtEntry, VAL_UINT32, VAL_REF

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

#TODO:
#    E9132E94 is a name table entry

class NameTableReader(SegmentReader): # for BRep and DC
	def __init__(self, segment):
		super(NameTableReader, self).__init__(segment)

	def getNtEntry(self, node, offset):
		entry = None
		nt, i  = getUInt32(node.data, offset)
		idx, i = getUInt32(node.data, i)
		if (nt>0):
			entry  = NtEntry(nt, idx)
		return entry, i

	def ReadNtEntry(self, node, offset, name):
		entry, i = self.getNtEntry(node, offset)
		node.set(name, entry)
		return i

	def ReadNtEntryList(self, node, offset, name):
		lst = []
		cnt, i = getSInt32(node.data, offset)
		for j in range(cnt):
			entry, i = self.getNtEntry(node, i)
			lst.append(entry)
		node.set(name, lst)
		return i

	def Read2NtEntryList(self, node, offset, name):
		lst = []
		cnt, i = getUInt32(node.data, offset)
		for j in range(cnt):
			e1, i = self.getNtEntry(node, i)
			e2, i = self.getNtEntry(node, i)
			lst.append((e1, e2))
		node.set(name, lst)
		return i

	def ReadNtEntryU8List(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			entry, i = self.getNtEntry(node, i)
			val, i  = getUInt8(node.data, i)
			lst.append([entry, val])
		node.set(name, lst)
		return i

	def ReadNtEntryD64List(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			entry, i = self.getNtEntry(node, i)
			val, i = getFloat64(node.data, i)
			lst.append([entry, val])
		node.set(name, lst)
		return i

	def ReadList2U32(self, node):
		i = self.ReadHeaderNameTableChild1Node(node)
		i = node.ReadSInt32A(i, 6, 'a0')
		i = node.ReadSInt32(i, 's32_1')
		i = self.skipBlockSize(i)
		return i

	def ReadHeaderNameTableRootNode(self, node, typeName = None):
		if (typeName is not None):
			node.typeName = typeName
		i = self.ReadList2U32(node)
		i = self.ReadNtEntry(node, i, 'from') # or is it face 1?
		i = self.ReadNtEntry(node, i, 'to')   # or is it face 2?
		i = node.ReadUInt8(i, 'u8_0')      # direction 2 = positive, 1 = negative
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadNtEntryU8List(node, i, 'lst2')
		i = self.skipBlockSize(i)
		return i

	def ReadRefU32ARefU32List(self, node, offset, name, size):
		cnt, i = getUInt32(node.data, offset)
		s = Struct('<LLL')
		lst = []
		for j in range(cnt):
			a1, i = getUInt32A(node.data, i, 3)
			a2, i = getUInt32A(node.data, i, size)
			lst.append([a1, a2])
		node.set(name, lst, VAL_UINT32)
		return i

	def ReadHeaderNameTableOtherNode(self, node, typeName = None):
		if (typeName is not None):
			node.typeName = typeName
		i = self.ReadList2U32(node)
		i = self.skipBlockSize(i)
		return i

	def Read_05C619B6(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadBoolean(i, 'b1')
		i = self.ReadNtEntryList(node, i, 'entries')
		i = self.ReadNtEntry(node, i, 'edge')
		i = self.ReadNtEntryU8List(node, i, 'lst2')
		i = self.ReadNtEntryD64List(node, i, 'a5')
		i = self.ReadNtEntryD64List(node, i, 'a6')
		if (self.version > 2010): i += 16
		return i

	def Read_22916CC1(self, node): # Name table root node
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		return i

	def Read_2D0AE083(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 5, 'a1')
		return i

	def Read_436D821A(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'satAtrs', 5) # -> LoftSection.label.u32_4
		return i

	def Read_47BDD5FD(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a2')
		return i

	def Read_8E5D4198(self, node):
		i = self.ReadHeaderNameTableOtherNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst1', 2)
		i = self.ReadNtEntryList(node, i, 'entries')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a1')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a2')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32A(i, 2, 'a3')
		return i

	def Read_DE0996B8(self, node): # Name table root node
		i = self.ReadHeaderNameTableOtherNode(node)
		return i

	# The name table itself

	def Read_CCE92042(self, node): # NameTable
		i = node.Read_Header0('NameTable')
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'lastIdx')
		cnt, i = getUInt32(node.data, i) # strange mapping of U32 and REF
		lst = {}
		for j in range(cnt):
			key, i = getUInt32(node.data, i)
			val, i = self.ReadNodeRef(node, i, key, REF_CHILD, 'entries')
			lst[key] = val
		node.set('entries', lst, VAL_REF)
		return i

	def Read_CCC5085A(self, node): # FaceMergeData
		i = node.Read_Header0('FaceMergeData')
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'nameTable')
		i = self.ReadRefU32AList(node, i, 'lst0', 2, REF_CROSS)
		i = self.ReadRefU32ARefU32List(node, i, 'lst1', 2)
		i = self.ReadRefU32ARefU32List(node, i, 'lst2', 1)
		cnt, i = getUInt32(node.data, i)
		sep = ''
		lst = []
		# remember node content as it will be overwritten by ReadList2!
		for j in range(cnt):
			u32_0, i = getUInt32(node.data, i)
			i = node.ReadList2(i, _TYP_UINT32_A_, 'tmp', 2)
			lst0 = node.get('tmp')
			u32_1, i = getUInt32(node.data, i)
			i = node.ReadList2(i, _TYP_UINT32_A_, 'tmp', 2) # this is ref + uint!
			lst1 = node.get('tmp')
			lst.append([u32_0, lst0, u32_1, lst1])
			sep = ','
		node.delete('tmp')
		node.set('lst3', lst, VAL_UINT32)
		return i

	# Root name table entries

	def Read_00E41C0E(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_3')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt8(i, 'u8_2')
		i = node.ReadUInt32A(i, 5, 'a2')
		i = node.ReadFloat64_3D(i, 'a3')
		return i

	def Read_139358BF(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_14340ADB(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst4', 7)
		return i

	def Read_22178C64(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2) # same as lst1 ?!?
		i = self.ReadNtEntry(node, i, 'edge')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'satAtrs', 5) # [asmKey, atrKey, type, 0, 0]
		return i

	def Read_40236C89(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32A(i, 3, 'a2')
		return i

	def Read_488C5309(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt32A(i, 4, 'a1')
		return i

	def Read_606D9AB1(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = self.skipBlockSize(i)
		return i

	def Read_6E2BCB60(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		i = node.ReadUInt32(i, 'u32_5')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_9BB4281C(self, node): # Name table root node for Fillet-Chamfer
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a2')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a3')
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a4')
		i = node.ReadUInt32A(i, 3, 'a5')
		if (self.version > 2019): i += 4 # skip 00 00 00 00
		return i

	def Read_F4360D18(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		node.set('a2', (), VAL_UINT32)
		node.set('a3', (), VAL_UINT32)
		node.set('a4', (), VAL_UINT32)
		node.set('a5', (0,0,0), VAL_UINT32)
		return i

	def Read_BF32E0A6(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = self.ReadNtEntryList(node, i, 'entries')
		return i

	def Read_D4BDEE88(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = node.ReadUInt32A(i, 3, 'a2')
		return i

	def Read_F7693D55(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		return i

	def Read_FF46726C(self, node): # Name table root node
		i = self.ReadHeaderNameTableRootNode(node)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst3', 2)
		i = self.ReadNtEntry(node, i, 'edge')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	####################
	# 1x Child name table entries
	def ReadHeaderNameTableChild1Node(self, node, typeName = None):
		i = node.Read_Header0(typeName)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, _TYP_NODE_REF_, 'lst0')
		return i

	def Read_B1ED010F(self, node): # Name table child node
		i = self.ReadHeaderNameTableChild1Node(node)
		i = node.ReadSInt32A(i, 7, 'a0')
		i = self.skipBlockSize(i, 2)
		i = self.ReadNtEntry(node, i, 'from') # or is it face 1?
		i = self.ReadNtEntryList(node, i, 'entries')
		return i

	def Read_BDE13180(self, node): # Name table child node
		i = self.ReadHeaderNameTableChild1Node(node)
		return i

	####################
	# 2x Child name table entries
	def ReadHeaderNameTableChild2Node(self, node, typeName = None):
		i = self.ReadHeaderNameTableChild1Node(node, typeName)
		i = node.ReadSInt32A(i, 6, 'a0')
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadList2(i, _TYP_UINT32_A_, 'lst1', 2)
		return i

	def Read_0811C56E(self, node): # Name table child node
		i = self.ReadHeaderNameTableChild2Node(node)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32A(i, 4, 'a1')
		if (self.version > 2011): i += 1
		return i

	def Read_31D7A200(self, node): # Name table child node
		i = self.ReadHeaderNameTableChild2Node(node)
		i = self.ReadNtEntryList(node, i, 'entries')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_36895B07(self, node): # Name table child node
		i = self.ReadHeaderNameTableChild2Node(node)
		return i

	def Read_896A9790(self, node): # Name table child node
		i = self.ReadHeaderNameTableChild2Node(node)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_2E04A208(self, node): # Name table child node for points (last-vertex)
		i = self.ReadHeaderNameTableChild2Node(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = node.ReadUInt32A(i, 2, 'a2')   # always (0,0)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'a3')
		i = node.ReadUInt32A(i, 3, 'a4')   # always (0,0,0)
		return i

	def Read_90F4820A(self, node): # Name table child node for points (first-vertex)
		i = self.ReadHeaderNameTableChild2Node(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		return i

	def Read_A170F6B6(self, node): # Name table child node
		i = self.ReadHeaderNameTableChild2Node(node)
		i = node.ReadSInt32A(i, 7, 'a1')
		i = node.ReadUInt32(i, 'u32_1')
		cnt, i = getUInt32(node.data, i)
		lst = []
		for j in range(cnt):
			a, i = getUInt32A(node.data, i, 7)
			lst.append(a)
		node.set('lst2', lst, VAL_UINT32)
		return i

	def Read_E5289C69(self, node): # Name table child node
		i = self.ReadHeaderNameTableChild2Node(node)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	# unknown name table entries
