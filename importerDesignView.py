# -*- coding: utf-8 -*-

'''
importerDesignView.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader
from importerSegNode import AbstractNode, DesignViewNode
from importerUtils   import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class DesignViewReader(SegmentReader):
	def __init__(self):
		super(DesignViewReader, self).__init__(False)

	def createNewNode(self):
		return DesignViewNode()

	def skipDumpRawData(self):
		return True

	def Read_08823621(self, node):
		i = node.Read_Header0()
		return i

	def Read_328FC2EA(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadLen32Text16(i)
		return i

	def Read_9DC2A241(self, node):
		i = node.Read_Header0()
		return i

	def Read_EBA31E2E(self, node):
		i = node.Read_Header0()
		return i
