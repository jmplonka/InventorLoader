# -*- coding: utf-8 -*-

'''
importerEeData.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment    import checkReadAll
from importer_NameTable import NameTableReader
from importerUtils      import *
from importerConstants  import VAL_UINT32
import importerSegNode

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class EeDataReader(NameTableReader):
	def __init__(self, segment):
		super(EeDataReader, self).__init__(segment)

	def ReadU32Arr(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			a, i = getUInt32A(node.data, i, 3) # list-index, ASM-ref, number
			lst.append(a)
		node.set('lst0', lst, VAL_UINT32)
		return i

	def Read_4E75F025(self, node):
		i = node.Read_Header0()
		return i

	def Read_CB0ADCAF(self, node): # Collector
		i = node.Read_Header0('Collector')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.ReadU32Arr(node, i, 'lst0')
		i = node.ReadUInt32A(i, 6, 'a2')
		return i
