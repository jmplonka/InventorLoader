# -*- coding: utf-8 -*-

'''
importerFBAttribute.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader, checkReadAll
from importerUtils   import *
import importerSegNode

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class FBAttributeReader(SegmentReader):
	def __init__(self):
		super(FBAttributeReader, self).__init__()

	def Read_080ED92F(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, importerSegNode._TYP_UINT8_, 'data')
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid')
		return i

	def Read_28C25C43(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadList2(i, importerSegNode._TYP_UINT8_, 'data')
		i = node.ReadUInt8A(i, 2, 'a0')
		i = node.ReadUInt16A(i, 2, 'a1')
		i = node.ReadUUID(i, 'uid')
		return i

	def Read_28C25C44(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, importerSegNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_28C25C45(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text16(i)
		t, i = getUInt8(node.data, i)
		i = node.ReadUInt16(i,'u16_0')
		i = node.ReadUInt8(i, 'u8_0')
		if (t == 1):
			i = node.ReadSInt32(i, 'data')
		elif (t == 2):
			i = node.ReadFloat64(i, 'data')
		elif (t == 3):
			i = node.ReadLen32Text16(i, 'data')
		elif (t == 4):
			i = node.ReadList2(i, importerSegNode._TYP_UINT8_, 'data')
		else:
			logError("    ERROR> Don't know what to do with %d in Read_28C25C45!" %(t))
		return i
