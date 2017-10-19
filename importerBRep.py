# -*- coding: utf8 -*-

'''
importerNotebook.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader, checkReadAll, Read_F645595C_chunk
from importerSegNode import AbstractNode, BRepNode
from importerClasses import BRepChunk
from importerUtils   import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class BRepReader(SegmentReader):
	def __init__(self):
		super(BRepReader, self).__init__(False)

	def createNewNode(self):
		return BRepNode()

	def skipDumpRawData(self):
		return True

	def Read_09780457(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadParentRef(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_0BDC96E0(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_632A4BBA(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 11, 'a1')
		return i

	def Read_66085B35(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		return i

	def Read_766EA5E5(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 10, 'a0')
		return i

	def Read_ABD292FD(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_BA0B8C23(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)

		return i

	def Read_CADD6468(self, node):
		i = node.Read_Header0()
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		return i

	def Read_CC0F7521(self, node):
		node.typeName = 'AcisEntityWrapper'
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 6, 'a0')
		return i

	def Read_CCC5085A(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		# i = node.ReadChildRef(i, 'chld_0')
		return i

	def Read_CCE92042(self, node):
		i = node.Read_Header0()
		return i

	def Read_D797B7B9(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_EA7DA988(self, node):
		i = node.Read_Header0()
		return i

	def Read_F645595C(self, node):
		node.typeName = 'TransactablePartition'
		l = len(node.data)
		e = l - 17
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		node.name, i = getText8(node.data, i, 15)
		i = node.ReadUInt32A(i, 4, 'a0')

		lst = []
		node.content += ' lst0={'
		sep = ''
		while (i < e):
			chunk, i = Read_F645595C_chunk(i, node)
			node.content += '%s%s' %(sep, chunk)

			sep = ','
			lst.append(chunk)
		i = self.skipBlockSize(i)
		return i

	def Read_F78B08D5(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
		return i
