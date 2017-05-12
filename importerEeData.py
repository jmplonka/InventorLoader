#!/usr/bin/env python

'''
importerEeData.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''

from importerSegment import SegmentReader, checkReadAll
from importerSegNode import AbstractNode, EeDataNode
from importerUtils   import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class EeDataReader(SegmentReader):
	def __init__(self):
		super(EeDataReader, self).__init__(False)

	def createNewNode(self):
		return EeDataNode()

	def skipDumpRawData(self):
		return True
