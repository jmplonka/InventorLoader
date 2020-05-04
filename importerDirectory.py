# -*- coding: utf-8 -*-

'''
importerDirectory.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) drawing's (IDW) directory data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment import SegmentReader, checkReadAll
from importerUtils   import *
import importerSegNode

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class DirectoryReader(SegmentReader):

	def __init__(self, segment):
		super(DirectoryReader, self).__init__(segment)

	def Read_685F7AF4(self, node):
		i = node.Read_Header0()
		return i

	def Read_3E9F410E(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_APP_1_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i
