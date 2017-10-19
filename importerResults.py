# -*- coding: utf8 -*-

'''
importerResults.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader, checkReadAll
from importerSegNode import AbstractNode, ResultNode
from importerClasses import ResultItem4
from importerUtils   import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.2.0'
__status__      = 'In-Development'

class ResultReader(SegmentReader):
	def __init__(self):
		super(ResultReader, self).__init__(True)

	def createNewNode(self):
		return ResultNode()

	def skipDumpRawData(self):
		return True

	def Read_Header1(self, node):
		i = self.skipBlockSize(0)
		i = node.ReadParentRef(i)
		return i

	def Read_09780457(self, node):
		i = self.Read_Header1(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')

		return i

	def Read_0E70AF5C(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4,'a1')

		return i

	def Read_128AAF24(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 4, 'a1')
		# if (node.get('a1')[2] > 0):
		# 	a2, i = getUInt16A(node.data, i, 4)
		# else:
		# 	a2 = [0, 0, 0, 0]

		# i = node.ReadList4(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		# lst0 = node.get('lst0', )
		# l0 = len(lst0)
		# if (l0 > 0):
		# 	a3,    i = getUInt32A(node.data, i, 2)
		# else:
		# 	a3 = [0, 0]
		# node.set('', )

		# i = node.ReadList4(i, AbstractNode._TYP_NODE_REF_, 'lst1')
		# lst1 = node.get('lst1')
		# l1 = len(lst1)
		#
		# if (l0 > 0):
		# 	i = node.ReadFloat64A(i, 3, 'a2')
		# 	i = Float64A(node.data, i, 3, node, 'a3')
		# else:
		# 	a2 = (0.0, 0.0, 0.0)
		# 	a3 = (0.0, 0.0, 0.0)
		# node.set('a2', a2)
		# node.set('a3', a3)
		#
		# i = self.skipBlockSize(i)

		# lst3,  i = node.ReadList4(i, AbstractNode._TYP_UINT32A_, 'lst0', 2)
		# l3 = len(lst3)
		#
		# if (l3 > 0):
		# 	lst4,  i = node.ReadList4(i, AbstractNode._TYP_RESULT_ITEM4_)
		# else:
		# 	lst4 = []
		# l4 = len(lst4)
		#
		# if (l4 == 0):
		# 	u8_1,  i = getUInt8(node.data, i)
		# else:
		# 	u8_1 = 0
		#
		# if (getFileVersion() > 2011):
		# 	dummy, i = node.ReadList4(i, AbstractNode._TYP_UINT32A_, 'lst0', 2)
		# i = self.skipBlockSize(i)
		#
		# if (l4 > 0):
		# 	u8_2,  i = getUInt8(node.data, i)
		# else:
		# 	u8_2 = 0
		#
		# lst5,  i = node.ReadList4(i, AbstractNode._TYP_NODE_REF_)
		# l5 = len(lst5)
		#
		# if (l5 > 0):
		# 	u8_3,  i = getUInt8(node.data, i)
		# else:
		# 	u8_3 = 0
		# u8_4,  i = getUInt8(node.data, i)
		#
		# lst6,  i = node.ReadList4(i, AbstractNode._TYP_NODE_REF_)
		# l6 = len(lst6)
		#
		# if (l6 > 0):
		# 	u32_0, i = getUInt16(node.data, i)
		# 	i = self.skipBlockSize(i)
		#
		# 	u16_1, i = getUInt16(node.data, i)
		#
		# 	lst7,  i = node.ReadList4(i, AbstractNode._TYP_NODE_REF_)
		#
		# 	u8_2,  i = getUInt8(node.data, i)
		#
		# 	lst8,  i = node.ReadList4(i, AbstractNode._TYP_NODE_REF_)
		# else:
		# 	u32_0 = 0
		# 	u16_1 = 0
		# 	u8_2  = 0
		# u8_3,  i = getUInt8(node.data, i)
		#
		# i = self.skipBlockSize(i)

		return i

	def Read_21830CED(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 10, 'a0')

		return i

	def Read_36246381(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 8, 'a0')

		return i

	def Read_3E0040FD(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 6, 'a1')

		return i

	def Read_69C3A76F(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 16, 'a0')

		return i

	def Read_6B9A3C47(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 5, 'a1')

		return i

	def Read_809BE56F(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 3, 'a1')

		return i

	def Read_80CAECF1(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 3, 'a1')

		return i

	def Read_9147489A(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 5, 'a1')

		return i

	def Read_E065E15A(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 8, 'a1')

		return i

	def Read_E9B04618(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 3, 'a1')

		return i

	def Read_F434C70B(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 10, 'a0')

		return i

	def Read_F645595C(self, node):
		node.typeName = 'TransactablePartition'
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 2, 'a2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i)
		i = node.ReadSInt32(i, 's32_1')
		return i

	def Read_F78B08D5(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_REF_, 'lst1')
		i = node.ReadChildRef(i)
		return i

	def Read_F8DD2C9D(self, node):
		i = self.Read_Header1(node)
		i = node.ReadUInt16A(i, 8, 'a0')

		return i
