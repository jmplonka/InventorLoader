# -*- coding: utf-8 -*-

'''
importerDesignView.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader
from importerUtils   import *
import importerSegNode

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class DesignViewReader(SegmentReader):
	def __init__(self):
		super(DesignViewReader, self).__init__()

	def Read_08823621(self, node):
		i = node.Read_Header0()
		i = node.ReadFloat64A(i, 14, 'a0')
		return i

	def Read_328FC2EA(self, node): # ViewDirectionCollection
		i = node.Read_Header0('ViewDirectionCollection')
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_551FB1BF(self, node):
		i = node.Read_Header0()
		i = node.ReadFloat64(i, 'f_0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_9B043321(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_9DC2A241(self, node): # ViewDirection
		i = node.Read_Header0('ViewDirection')
		i = node.ReadLen32Text16(i)
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_301D4138(self, node): # member of ViewDirection.lst0
		return 0

	def Read_8902B593(self, node): # member of ViewDirection.lst0
		 return 0

	def Read_D9980532(self, node): # member of ViewDirection.lst0
		return 0

	def Read_E3684E1C(self, node):
		i = node.Read_Header0()
		i = self.ReadTransformation(node, i)
		return i

	def Read_EBA31E2E(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		n, i = getUInt32(node.data, i)
		i = node.ReadUInt16A(i, n, 'a0')
		return i
