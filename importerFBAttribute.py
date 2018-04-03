# -*- coding: utf-8 -*-

'''
importerFBAttribute.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader, checkReadAll
from importerSegNode import AbstractNode, FBAttributeNode
from importerUtils   import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class FBAttributeReader(SegmentReader):
	def __init__(self):
		super(FBAttributeReader, self).__init__(False)

	def createNewNode(self):
		return FBAttributeNode()

	def skipDumpRawData(self):
		return True

	def Read_080ED92F(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_28C25C43(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_28C25C44(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_28C25C45(self, node):
		i = node.Read_Header0()
		i = node.ReadLen32Text16(i)
		return i
