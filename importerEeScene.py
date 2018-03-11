# -*- coding: utf8 -*-

'''
importerEeScene.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
'''

from importerSegment import SegmentReader, checkReadAll
from importerSegNode import AbstractNode, EeSceneNode
from importerUtils   import *

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class EeSceneReader(SegmentReader):
	def __init__(self):
		super(EeSceneReader, self).__init__(False)

	def createNewNode(self):
		return EeSceneNode()

	def skipDumpRawData(self):
		return True

	def Read_48EB8608(self, node):
		i = node.Read_Header0()
		return i

	def Read_5194E9A3(self, node):
		#i = node.Read_Header0()
		i = 0
		return i

	def Read_A79EACCB(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 3, 'a0')
		i = node.ReadCrossRef(i, 'ref_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, AbstractNode._TYP_3D_FLOAT32_, 'lst0')
		return i

	def Read_A79EACD2(self, node):
		i = node.Read_Header0()
		return i

	def Read_B32BF6A6(self, node):
		i = node.Read_Header0()
		return i

	def Read_B32BF6A9(self, node):
		i = node.Read_Header0()
		return i
