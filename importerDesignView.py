# -*- coding: utf-8 -*-

'''
importerDesignView.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader
from importerUtils   import *
from importerSegNode import _TYP_NODE_REF_, _TYP_UINT32_, _TYP_LIST_UINT32_A_

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__status__      = 'In-Development'

class DesignViewReader(SegmentReader):
	def __init__(self, segment):
		super(DesignViewReader, self).__init__(segment)

	def Read_08823621(self, node):
		i = node.Read_Header0('Camera')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64_3D(i, 'target')
		i = node.ReadFloat64_3D(i, 'eye')
		i = node.ReadFloat64_3D(i, 'a0')
		i = node.ReadFloat64(i, 'angle')
		i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadFloat64_3D(i, 'up')
		return i

	def Read_216B3A55(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, _TYP_UINT32_, 'lst0')
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_328FC2EA(self, node): # ViewDirectionCollection
		i = node.Read_Header0('ViewDirectionCollection')
		i = node.ReadList2(i, _TYP_NODE_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_301D4138(self, node): # member of ViewDirection.lst0
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt8A(i, 2, 'a0')
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_47C98A81(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_71C22321(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		return i

	def Read_9B043321(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref0')
		i = self.skipBlockSize(i)
		if (self.version < 2020):
			i = node.ReadLen32Text16(i)
		else:
			i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2012): i += 4 # skip ?? ?? ?? ??
		return i

	def Read_551FB1BF(self, node):
		i = node.Read_Header0('ViewScale')
		i = node.ReadFloat64(i, 'scale')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_8902B593(self, node): # member of ViewDirection.lst0
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'flags')
		return i

	def Read_987C5D0F(self, node):
		i = node.ReadUInt16A(0, 3, 'a0')
		i = self.skipBlockSize(i, 2)
		i = node.ReadUUID(i, 'uid0')
		i = node.ReadList2(i, _TYP_LIST_UINT32_A_, 'lst0')
		return i

	def Read_9DC2A241(self, node): # ViewDirection
		i = node.Read_Header0('ViewDirection')
		i = node.ReadLen32Text16(i)
		i = node.ReadList2(i, _TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt32(i, 'flags')
		i = node.ReadUInt16(i, 'CodePage')
		# list2 of what?
		return i

	def Read_6E2FE45A(self, node):
		i = node.Read_Header0()
		return i

	def Read_BDA7138D(self, node):
		i = node.Read_Header0()
		return i

	def Read_D4DDE1F5(self, node): # member of ViewDirection.lst0
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_D8B8F230(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_D9980532(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref0')
		i = self.skipBlockSize(i)
		i = node.ReadBoolean(i, 'b0')
		i = self.skipBlockSize(i)
		if (self.version > 2011):
				b, i = getBoolean(node.data, i)
				i = node.ReadUInt32(i, 'u32_0')
				i = node.ReadUInt8(i, 'u8_1')
				if (not b):
					i = node.ReadLen32Text16(i, 'txt0')
					i = node.ReadLen32Text16(i, 'txt1')
					i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadUInt32(i, 'u32_1')
		if (self.version > 2017): i += 4
		return i

	def Read_E3684E1C(self, node):
		i = node.Read_Header0()
		i = self.ReadTransformation3D(node, i)
		return i

	def Read_EBA31E2E(self, node):
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		n, i = getUInt32(node.data, i)
		i = node.ReadUInt16A(i, n, 'a0')
		return i

	def Read_F2E6BC0B(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_0')
		i = node.ReadBoolean(i, 'b0')
		return i