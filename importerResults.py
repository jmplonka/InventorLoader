#!/usr/bin/env python

'''
importerResults.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader, ReadChildRef, ReadParentRef, checkReadAll, skipBlockSize
from importerClasses import ResultNode, ResultItem4
from importerUtils import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class ResultReader(SegmentReader):
	def __init__(self):
		super(ResultReader, self).__init__(True)

	def createNewNode(self):
		return ResultNode()

	def skipDumpRawData(self):
		return True

	def Read_09780457(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadSInt32(block, i, node, 's32_0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')

		checkReadAll(node, i, len(block))
		return

	def Read_0e70af5c(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 4, node,'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_128aaf24(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadUInt16A(block, i, 4, node, 'a1')
		# if (node.get('a1')[2] > 0):
		# 	a2, i = getUInt16A(block, i, 4)
		# else:
		# 	a2 = [0, 0, 0, 0]

		# i = self.ReadList4(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		# lst0 = node.get('lst0', )
		# l0 = len(lst0)
		# if (l0 > 0):
		# 	a3,    i = getUInt32A(block, i, 2)
		# else:
		# 	a3 = [0, 0]
		# node.set('', )

		# i = self.ReadList4(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst1')
		# lst1 = node.get('lst1')
		# l1 = len(lst1)
		#
		# if (l0 > 0):
		# 	i = self.ReadFloat64A(block, i, 3, node, 'a2')
		# 	i = Float64A(block, i, 3, node, 'a3')
		# else:
		# 	a2 = (0.0, 0.0, 0.0)
		# 	a3 = (0.0, 0.0, 0.0)
		# node.set('a2', a2)
		# node.set('a3', a3)
		#
		# i = skipBlockSize(block, i)

		# lst3,  i = self.ReadList4(block, i, node, SegmentReader._TYP_2D_UINT32_)
		# l3 = len(lst3)
		#
		# if (l3 > 0):
		# 	lst4,  i = self.ReadList4(block, i, node, SegmentReader._TYP_RESULT_ITEM4_)
		# else:
		# 	lst4 = []
		# l4 = len(lst4)
		#
		# if (l4 == 0):
		# 	u8_1,  i = getUInt8(block, i)
		# else:
		# 	u8_1 = 0
		#
		# if (getFileVersion() > 2011):
		# 	dummy, i = self.ReadList4(block, i, node, SegmentReader._TYP_2D_UINT32_)
		# i = skipBlockSize(block, i)
		#
		# if (l4 > 0):
		# 	u8_2,  i = getUInt8(block, i)
		# else:
		# 	u8_2 = 0
		#
		# lst5,  i = self.ReadList4(block, i, node, SegmentReader._TYP_NODE_REF_)
		# l5 = len(lst5)
		#
		# if (l5 > 0):
		# 	u8_3,  i = getUInt8(block, i)
		# else:
		# 	u8_3 = 0
		# u8_4,  i = getUInt8(block, i)
		#
		# lst6,  i = self.ReadList4(block, i, node, SegmentReader._TYP_NODE_REF_)
		# l6 = len(lst6)
		#
		# if (l6 > 0):
		# 	u32_0, i = getUInt16(block, i)
		# 	i = skipBlockSize(block, i)
		#
		# 	u16_1, i = getUInt16(block, i)
		#
		# 	lst7,  i = self.ReadList4(block, i, node, SegmentReader._TYP_NODE_REF_)
		#
		# 	u8_2,  i = getUInt8(block, i)
		#
		# 	lst8,  i = self.ReadList4(block, i, node, SegmentReader._TYP_NODE_REF_)
		# else:
		# 	u32_0 = 0
		# 	u16_1 = 0
		# 	u8_2  = 0
		# u8_3,  i = getUInt8(block, i)
		#
		# i = skipBlockSize(block, i)
		i += self.ReadUnknown(node, block[i:], None, False, False)

		checkReadAll(node, i, len(block))
		return

	def Read_21830ced(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 10, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_36246381(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 8, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_3e0040fd(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 6, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_69c3a76f(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 16, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_6b9a3c47(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt32A(block, i, 2, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 5, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_809be56f(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 3, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_80caecf1(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 3, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_9147489a(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 5, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_e065e15a(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 8, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_e9b04618(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 3, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_f434c70b(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 10, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_f645595c(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16A(block, i, 2, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 2, node, 'a1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 2, node, 'a2')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadSInt32(block, i, node, 's32_0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = self.ReadSInt32(block, i, node, 's32_1')

		checkReadAll(node, i, len(block))
		return

	def Read_f78b08d5(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16A(block, i, 2, node, 'a0')
		i = skipBlockSize(block, i)
		i = ReadParentRef(block, i, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_1D_UINT32_, 'lst0')
		i = self.ReadList6(block, i, node, 'lst1')
		i = ReadChildRef(block, i, node)

		checkReadAll(node, i, len(block))
		return

	def Read_f8dd2c9d(self, node, block):
		i = self.Read_Header1(block, node)
		i = self.ReadUInt16A(block, i, 8, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def HandleBlock(self, file, block, node, seg):
		ntid = node.typeID.time_low
		if (ntid == 0x09780457):
			self.Read_09780457(node, block)
		elif (ntid == 0x0e70af5c):
			self.Read_0e70af5c(node, block)
		elif (ntid == 0x128aaf24):
			self.Read_128aaf24(node, block)
		elif (ntid == 0x21830ced):
			self.Read_21830ced(node, block)
		elif (ntid == 0x36246381):
			self.Read_36246381(node, block)
		elif (ntid == 0x3e0040fd):
			self.Read_3e0040fd(node, block)
		elif (ntid == 0x69c3a76f):
			self.Read_69c3a76f(node, block)
		elif (ntid == 0x6b9a3c47):
			self.Read_6b9a3c47(node, block)
		elif (ntid == 0x809be56f):
			self.Read_809be56f(node, block)
		elif (ntid == 0x80caecf1):
			self.Read_80caecf1(node, block)
		elif (ntid == 0x9147489a):
			self.Read_9147489a(node, block)
		elif (ntid == 0xe065e15a):
			self.Read_e065e15a(node, block)
		elif (ntid == 0xe9b04618):
			self.Read_e9b04618(node, block)
		elif (ntid == 0xf434c70b):
			self.Read_f434c70b(node, block)
		elif (ntid == 0xf645595c):
			self.Read_f645595c(node, block)
		elif (ntid == 0xf78b08d5):
			self.Read_f78b08d5(node, block)
		elif (ntid == 0xf8dd2c9d):
			self.Read_f8dd2c9d(node, block)
		else:
			self.ReadUnknownBlock(file, node, block, True)

		return node
