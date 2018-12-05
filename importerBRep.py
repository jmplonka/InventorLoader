# -*- coding: utf-8 -*-

'''
importerNotebook.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment import SegmentReader, checkReadAll
from importerUtils   import *
import importerSegNode

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class BRepReader(SegmentReader):
	def __init__(self, segment):
		super(BRepReader, self).__init__(segment)

	def Read_009A1CC4(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_0645C2A5(self, node): # EntityWrapperNode
		i = self.ReadHeaderEntityWrapperNode(node)
		return i

	def Read_31D7A200(self, node): # EntityWrapperNode
		i = self.ReadHeaderEntityWrapperNode(node)
		return i

	def Read_36895B07(self, node): # EntityWrapperNode
		i = self.ReadHeaderEntityWrapperNode(node)
		return i

	def Read_07BA7419(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_56A95F20(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_6F891B34(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_0811C56E(self, node): return 0

	def Read_09780457(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadParentRef(i)
		i = node.ReadSInt32(i, 'key')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_09DABAE0(self, node): return 0

	def Read_0BDC96E0(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_167018B8(self, node): return 0

	def Read_1CC0C585(self, node): return 0

	def Read_2169ED74(self, node): return 0

	def Read_2892C3E0(self, node): return 0

	def Read_357D669C(self, node): return 0

	def Read_3DE78F81(self, node): return 0

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

	def Read_4DAB0A79(self, node): return 0

	def Read_5363C623(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_537799E0(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_632A4BBA(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadCrossRef(i, 'root')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt16A(i, 5, 'a1')
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_66085B35(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'dcCreatorIdx') # the creator' index in 'DC' segment
		if (getFileVersion() > 2009):
			i = node.ReadUInt16(i, 'u16_0')
		else:
			i = node.ReadUInt8(i, 'u16_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		return i

	def Read_6985F652(self, node):
		i = node.Read_Header0()
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_6D0B7807(self, node):
		i = node.Read_Header0()
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		return i

	def Read_736C138D(self, node): return 0

	def Read_766EA5E5(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 10, 'a0')
		return i

	def Read_77D10C74(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_7E5D2868(self, node): return 0

	def Read_821ACB9E(self, node): return 0

	def Read_896A9790(self, node): return 0

	def Read_8E5D4198(self, node): return 0

	def Read_9D2E8361(self, node): return 0

	def Read_D4A52F3A(self, node): return 0

	def Read_A618B833(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_A_, 'lst0', 2)
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_ABD292FD(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadFloat64_3D(i, 'a1')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_AE0E267A(self, node): return 0

	def Read_AFD4E6A3(self, node): return 0

	def Read_B292F94A(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_BA0B8C23(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadCrossRef(i, 'root')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_BFED36A9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_C620657B(self, node):
		i = self.skipBlockSize(0)
		return i

	def Read_CADD6468(self, node): # BrepComponent
		i = node.Read_Header0('BrepComponent')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_CC0F7521(self, node): # AsmEntityWrapper
		i = node.Read_Header0('AsmEntityWrapper')
		i = node.ReadUInt32(i, 'index')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadChildRef(i, 'asm')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'lenFooter')
		return i

	def Read_CCC5085A(self, node): # FaceMergeData
		i = node.Read_Header0('FaceMergeData')
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
		node.delete('tmp')
		node.content = c +']'
		node.set('lst3', lst)
		return i

	def Read_CCE92042(self, node): # NameTable
		i = node.Read_Header0('NameTable')
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'lastIdx')
		cnt, i = getUInt32(node.data, i) # strange mapping of U32 and REF
		lst = {}
		for j in range(cnt):
			key, i = getUInt32(node.data, i)
			val, i = self.ReadNodeRef(node, i, key, importerSegNode.SecNodeRef.TYPE_CHILD, 'entries')
			lst[key] = val
		node.set('entries', lst)
		return i

	def Read_D797B7B9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'dcCreatorIdx')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_DDA265D6(self, node): return 0

	def Read_E70272F7(self, node): return 0

	def Read_E9132E94(self, node): return 0

	def Read_EA7DA988(self, node): # AcisEntityContainer
		i = node.Read_Header0('AcisEntityContainer')
		i = node.ReadList8(i, importerSegNode._TYP_NODE_REF_, 'wrappers')
		return i

	def Read_F78B08D5(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'keys')
		i = node.ReadList6(i, importerSegNode._TYP_MAP_KEY_REF_, 'mapping')
		i = node.ReadChildRef(i, 'ref_1')
		return i
