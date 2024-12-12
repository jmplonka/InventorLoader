# -*- coding: utf-8 -*-

'''
importerNotebook.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader, checkReadAll
import importerSegNode
from importerUtils   import *
from importerConstants import VAL_UINT32

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.1'
__status__      = 'In-Development'

class NotebookReader(SegmentReader):
	def __init__(self, segment):
		super(NotebookReader, self).__init__(segment)

	def Read_386E04F0(self, node): # RtfContent
		i = node.Read_Header0('RtfContent')
		i = node.ReadList2(i, importerSegNode._TYP_CHAR_, 'rtf')
		# TODO: convert RTF to HTML/TEXT
		return i

	def Read_7ABDF905(self, node):
		i = node.Read_Header0()
		i = node.ReadList3(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_8115E243(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt8A(i, 6, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT32_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt8(i, 'u8_1')
		i = self.skipBlockSize(i)
		return i

	def ReadArea(self, node, ta = None): # ???Area
		if (ta is None): ta = 'Area_' + node.typeName
		i = node.Read_Header0(ta)
		i = node.ReadUInt32(i, 'u32_0')
		if (self.version < 2024): i += 4 # skip UInt32
		i = self.skipBlockSize(i, 2)
		i = node.ReadUInt32A(i, 4, 'a1')
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_B33B66CF(self, node): # ???Area
		i = self.ReadArea(node)
		return i

	def Read_CC253BB7(self, node): # TextArea
		i = self.ReadArea(node, 'TextArea')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt8A(i, 8, 'a2')
		i = node.ReadLen32Text16(i, 'author')
		return i

	def Read_D8705BC7(self, node): # GraphicsArea
		i = self.ReadArea(node, 'GraphicsArea')
		i = node.ReadFloat64A(i, 7, 'a2')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadFloat64A(i, 12, 'a3')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_E23E5AE6(self, node):
		i = self.ReadHeaderU32RefU8List3(node)
		i = node.ReadParentRef(i)
		return i

	####################
	# Int List2 sections
	def ReadHeaderU32Lst2(self, node, typeName = None):
		i = node.Read_Header0(typeName)
		if (self.version < 2024):
			i = node.ReadUInt32A(i, 2, 'a0')
		else:
			n, i = getUInt32(node.data, i)
			node.set('a0', (n, 0), VAL_UINT32)
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, importerSegNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_3C95B7CE(self, node): # Notebook
		i = self.ReadHeaderU32Lst2(node, 'Notebook')
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt32(i, 'self') # looks like self ref!
		i = node.ReadUInt8(i, 'u8_1')
		return i

	def Read_4C415964(self, node): # Note
		i = self.ReadHeaderU32Lst2(node, 'Note')
		i = node.ReadLen32Text16(i)
		i = node.ReadList3(i, importerSegNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt16A(i, 2, 'a1')
		return i

	def Read_74E34413(self, node): # Folder
		i = self.ReadHeaderU32Lst2(node, 'Folder')
		i = node.ReadUInt32(i, 'l1')
		i = node.ReadFloat64_3D(i, 'a1')
		return i
