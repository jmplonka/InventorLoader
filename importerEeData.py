# -*- coding: utf-8 -*-

'''
importerEeData.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment import SegmentReader, checkReadAll
from importerUtils   import *
import importerSegNode

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class EeDataReader(SegmentReader):
	def __init__(self):
		super(EeDataReader, self).__init__()

	def Read_4E75F025(self, node):
		i = node.Read_Header0()
		return i

	def Read_CB0ADCAF(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadLen32Text16(i, 'txt_0')
		# 7F,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00
		return i
