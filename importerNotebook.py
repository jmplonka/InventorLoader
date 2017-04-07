#!/usr/bin/env python

'''
importerNotebook.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader, ReadChildRef, ReadParentRef, checkReadAll, skipBlockSize
from importerClasses import NotebookNode
from importerUtils import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class NotebookReader(SegmentReader):
	def __init__(self):
		super(NotebookReader, self).__init__(False)

	def createNewNode(self):
		return NotebookNode()

	def skipDumpRawData(self):
		return True

	def Read_386e04f0(self, node, block):
		'''
		Rich Text Block
		TODO:
			convert RTF to HTML/TEXT
		'''
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_1D_CHAR_, 'lst0')

		checkReadAll(node, i, len(block))
		return

	def Read_3c95b7ce(self, node, block):
		'''
		Notebook
		'''
		node.typeName = 'Notebook'

		i = self.Read_Header0(block, node)
		i = self.ReadUInt32A(block, i, 2, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_X_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_4c415964(self, node, block):
		'''
		Notice
		'''
		node.typeName = 'Notice'

		i = self.Read_Header0(block, node)
		i = self.ReadUInt32A(block, i, 2, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst1')
		i = self.ReadUInt16A(block, i, 2, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_74e34413(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt32A(block, i, 2, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt32A(block, i, 7, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_7abdf905(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUUID(block, i, node, 'uid0')
		i = ReadChildRef(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_8115e243(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt8A(block, i, 7, node, 'a0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_1D_UINT32_, 'lst0')
		i = ReadChildRef(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_cc253bb7(self, node, block):
		'''
		Comment
		'''
		node.typeName = 'Comment'

		i = self.Read_Header0(block, node)
		i = self.ReadUInt32A(block, i, 6, node, 'a0')
		i = self.ReadLen32Text16(block, i, node)
		i = ReadChildRef(block, i, node)
		i = self.ReadUInt8A(block, i, 8, node, 'a2')
		i = self.ReadLen32Text16(block, i, node, 'author')

		checkReadAll(node, i, len(block))
		return

	def Read_d8705bc7(self, node, block):
		'''
		View
		'''
		node.typeName = 'View'

		i = self.Read_Header0(block, node)
		i = self.ReadUInt32A(block, i, 6, node, 'a0')
		i = self.ReadLen32Text16(block, i, node)
		i = self.ReadFloat64A(block, i, 7, node, 'a1')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadFloat64A(block, i, 12, node, 'a2')
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_e23e5ae6(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt32A(block, i, 2, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = ReadParentRef(block, i, node)

		checkReadAll(node, i, len(block))
		return

	def HandleBlock(self, file, block, node, seg):
		ntid = node.typeID.time_low
		if (ntid == 0x386e04f0):
			self.Read_386e04f0(node, block)
		elif (ntid == 0x3c95b7ce):
			self.Read_3c95b7ce(node, block)
		elif (ntid == 0x4c415964):
			self.Read_4c415964(node, block)
		elif (ntid == 0x74e34413):
			self.Read_74e34413(node, block)
		elif (ntid == 0x7abdf905):
			self.Read_7abdf905(node, block)
		elif (ntid == 0x8115e243):
			self.Read_8115e243(node, block)
		elif (ntid == 0xcc253bb7):
			self.Read_cc253bb7(node, block)
		elif (ntid == 0xd8705bc7):
			self.Read_d8705bc7(node, block)
		elif (ntid == 0xe23e5ae6):
			self.Read_e23e5ae6(node, block)
		else:
			self.ReadUnknownBlock(file, node, block, True)

		return node
