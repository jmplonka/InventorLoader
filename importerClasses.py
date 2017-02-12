#!/usr/bin/env python

"""
importerClasses.py:

Collection of classes necessary to read and analyse Autodesk (R) Invetor (R) files.
"""

from importerUtils import IFF
from importerUtils import IntArr2Str

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

SEG_PM_GRAPHICS = 'PmGraphicsSegment'
SEG_AM_GRAPHICS = 'AmGraphicsSegment'

class UFRxDocument():
	arr1 = []          # UInt16[]
	arr2 = []          # UInt16[4]
	dat1 = None        # DateTime
	arr3 = []          # UInt16[4]
	dat2 = None        # DateTime
	txt1 = ''
	arr4 = []          # UInt16[8]
	arr5 = []          # UInt16[4]
	dat3 = None        # DateTime
	revisionRef = None # reference to RSeDbRevisionInfo
	ui1  = 0
	dbRef = None       # reference to RSeDb
	txt2 = ''
	arr6 = []          # UInt16[3]
	prps = {}
	ui2 = 0
	txt3 = ''
	ui3 = 0
	arr7 = []          # UInt16[9]
	# ????
	minVec3D = []      # float32[3] <=> Point3D_min ???
	maxVec3D = []      # float32[3] <=> Point3D_max ???
	# ????

class RSeDatabase():
	uid = None  # Internal-Name of the object
	version = -1
	arr1 = []   # UInt16A[4]
	dat1 = None # datetime
	arr2 = []   # UInt16A[4]
	dat2 = None # datetime
	arr4 = []   # UInt16A[8]
	arr4 = []   # UInt16A[4]
	txt = ''
	txt2 = ''

class RSeSegmentObject():
	revisionRef = None # reference to RSeDbRevisionInfo
	values = []
	value1 = 0
	value2 = 0

	def __str__(self):
		return '[%s],%02X,%02X' % (IntArr2Str(self.values, 4), self.value1, self.value2)

class RSeSegmentValue2():
	index = -1
	indexSegList1 = -1
	indexSegList2 = -1
	values = None
	number = -1

	def __init__(self):
		values = []

	def __str__(self):
		return '%02X,%02X,%X,[%s],%04X' % (self.indexSegList1, self.indexSegList2, self.index, IntArr2Str(self.values, 4), self.number)

class RSeSegment():
	name = ''
	ID = None
	revisionRef = None # reference to RSeDbRevisionInfo
	value1 = 0
	count1 = 0
	arr1 = None
	count2 = 0
	type = ''
	arr2 = None
	metaData = None
	objects = None
	nodes = None

	def __init__(self):
		self.arr1 = []
		self.arr2 = []
		self.objects = []
		self.nodes = []

	def __str__(self):
		return '{0:<24}: count=({1}/{2}) {4} - [{5}]'.format(self.name, self.count1, self.count2, self.ID, self.value1, IntArr2Str(self.values, 4))

class RSeSegInformation():
	segments = {}
	val      = [] # UInt16[2]
	uidList1 = []
	uidList2 = []

class RSeStorageSection1():
	arr = [] # UInt16[2]
	parent = None

	def __init__(self, parent):
		self.parent = parent
		self.arr = []

	def __str__(self):
		return '[%s]' %(IntArr2Str(self.arr, 4))

class RSeStorageSection2():
	"""
	 # arr[1] = RSeDbRevisionInfo.data[0]
	 # arr[3] = RSeDbRevisionInfo.data[2]
	 # arr[4] = RSeDbRevisionInfo.data[3]
	"""
	revisionRef = None # reference to RSeDbRevisionInfo
	flag = None
	val = 0
	arr = None
	parent = None

	def __init__(self, parent):
		self.parent = parent
		self.arr = []

	def __str__(self):
		a = ''
		u = ''
		if (len(self.arr) > 0):
			a = ' [%s]' %(IntArr2Str(self.arr, 4))
		if (self.revisionRef is not None):
			u = ' - %s' %(self.revisionRef)

		return '%X, %X%s%s' %(self.flag, self.val, u, a)

class RSeStorageSection3():
	uid = None
	arr = [] # UInt16[6]
	parent = None

	def __init__(self, parent):
		self.parent = parent
		self.arr = []

	def __str__(self):
		return '%s: [%s]' %(self.uid, IntArr2Str(self.arr, 4))

class RSeStorageSection4Data():
	num = 0 # UInt16
	val = 0 # UInt32

	def __str__(self):
		return '(%04X,%08X)' %(self.num, self.val)

class RSeStorageSection4():
	uid = None
	arr = [] # RSeStorageSection4Data[2]
	parent = None

	def __init__(self, parent):
		self.parent = parent
		self.arr = []

	def __str__(self):
		return '%s: [%s,%s]' %(self.uid, self.arr[0], self.arr[1])

class RSeStorageSection4Data1():
	uid = None
	val = 0

	def __init__(self, uid, val):
		self.uid = uid
		self.val = val

	def __str__(self):
		return '[%s,%d]' %(self.uid, self.val)

class RSeStorageSection5():
	indexSec4 = None
	parent = None

	def __init__(self, parent):
		self.parent = parent
		self.indexSec4 = []

class RSeStorageSection6():
	arr1 = None
	arr2 = None
	parent = None

	def __init__(self, parent):
		self.parent = parent
		self.arr1 = []
		self.arr2 = []

class RSeStorageSection7():
	segRef      = None
	revisionRef = None
	dbRef       = None
	txt1        = ''
	arr1        = []
	txt2        = ''
	arr2        = []
	txt3        = ''
	arr3        = []
	parent      = None

	def __init__(self, parent):
		self.parent = parent
		self.arr1 = []
		self.arr2 = []
		self.arr3 = []

	def __str__(self):
		if (self.dbRef is None):
			return '[%s]' %(self.segRef)
		else:
			return '[%s] [%s] [%s] [%s] %r %r %r' %(self.segRef, self.arr1, self.arr2, self.arr3, self.txt1, self.txt2, self.txt3)

class RSeStorageSection8():
	dbRevisionInfoRef = None
	arr = [] # UInt16[2]
	parent = None

	def __init__(self, parent):
		self.parent = parent
		self.arr = []

	def __str__(self):
		return '[%s]' %(IntArr2Str(self.arr, 4))

class RSeStorageSection9():
	uid = None
	arr = [] # UInt16[3]
	parent = None

	def __init__(self, parent):
		self.parent = parent
		self.arr = []

	def __str__(self):
		return '%s: [%s]' %(self.uid, IntArr2Str(self.arr, 4))

class RSeStorageSectionA():
	uid = None
	arr = [] # UInt16[4]
	parent = None

	def __init__(self, parent):
		self.parent = parent
		self.arr = []

	def __str__(self):
		return '[%s]' %(IntArr2Str(self.arr, 4))

class RSeStorageSectionB():
	uid = None
	arr = [] # UInt16[2]
	parent = None

	def __init__(self, parent):
		self.parent = parent
		self.arr = []

	def __str__(self):
		return '[%s]' %(IntArr2Str(self.arr, 4))

class RSeMetaData():
	txt1 = ''
	ver = 0
	arr1 = []
	txt2 = ''
	arr2 = []
	dat1 = ''
	val1 = 0
	dat2 = ''
	segRef = None
	arr3 = []
	sec1 = []
	sec2 = []
	sec3 = []
	sec4 = []
	sec5 = []
	sec6 = []
	sec7 = []
	sec8 = []
	sec9 = []
	secA = []
	secB = []
	uid2 = None # should alwas be '9744e6a4-11d1-8dd8-0008-2998bedddc09'

class Inventor():
	iProperties = None
	UFRxDoc = None
	RSeDb = None
	RSeSegInfo = None
	RSeDbRevisionInfoMap = None
	RSeDbRevisionInfoList = None
	RSeStorageData = None
	DatabaseInterfaces = None

	def __init__(self):
		self.iProperties = {}
		self.RSeStorageData = {}

class DbInterface():
	name = ''
	type = 0
	data = []
	uid = None
	value = None

	def __init__(self, name):
		self.name = name

	def __str__(self):
		if(self.type   == 0x01):
			typ = 'BOOL'
		elif(self.type == 0x04):
			typ = 'SINT'
		elif(self.type == 0x10):
			typ = 'UUID'
		elif(self.type == 0x30):
			typ = 'FLOAT[]'
		elif(self.type == 0x54):
			typ = 'MAP'
		else:
			typ = '%4X' % self.type
		return '%s=%s:\t%s\t%s' % (self.name, self.value, typ, self.uid)

class RSeDbRevisionInfo():
	ID    = '' # UUID
	value1 = 0  # UINT16
	value2 = 0  # UINT16
	type   = 0  # UINT16
	# If type = 0xFFFF:
	#	BYTE + [UInt16]{8 <=> BYTE=0, 4 <=> BYTE==0}
	data   = []
	def __str__(self):
		if (self.type == 0xFFFF):
			return '%s,(%04X/%04X),[%s]' % (self.ID, self.value1, self.value2, IntArr2Str(self.data, 4))
		else:
			return '%s,(%04X/%04X),[%04X]' % (self.ID, self.value1, self.value2, self.type)

class Thumbnail():
	width = 0
	height = 0
	data = None

	def __init__(self):
		self.type = 'PNG'

	def __str__(self):
		return '%s width=%d, height=%d' % (self.type, self.width, self.height)
