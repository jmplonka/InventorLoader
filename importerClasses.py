#!/usr/bin/env python

'''
importerClasses.py:

Collection of classes necessary to read and analyse Autodesk (R) Invetor (R) files.
'''

import traceback
from importerUtils import IntArr2Str, FloatArr2Str, logMessage, logWarning, logError, getInventorFile, getUInt16, getUInt16A
from math          import degrees, radians, pi

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.2.0'
__status__      = 'In-Development'

def writeThumbnail(data):
	folder = getInventorFile()[0:-4]
	filename = folder + '/_.png'
	with open(filename, 'wb') as thumbnail:
		# skip thumbnail class header (-1, -1, 03, 00, 08, width, height, 00)
		thumbnail.write(data[0x10:])
	filename = folder + '/_.log'
	with open(filename, 'wb') as thumbnail:
		# skip thumbnail class header (-1, -1, 03, 00, 08, width, height, 00)
		arr, i = getUInt16A(data, 0, 8)
		thumbnail.write(IntArr2Str(arr, 2))
	thmb = Thumbnail()
	thmb.width, i = getUInt16(data, 10)
	thmb.height, i = getUInt16(data, i)
	return thmb

class UFRxDocument():
	def __init__(self):
		self.arr1        = []   # UInt16[]
		self.arr2        = []   # UInt16[4]
		self.dat1        = None # DateTime
		self.arr3        = []   # UInt16[4]
		self.dat2        = None # DateTime
		self.comment     = ''
		self.arr4        = []   # UInt16[8]
		self.arr5        = []   # UInt16[4]
		self.dat3        = None # DateTime
		self.revisionRef = None # reference to RSeDbRevisionInfo
		self.ui1         = 0
		self.dbRef       = None # reference to RSeDb
		self.filename    = ''
		self.arr6        = []   # UInt16[3]
		self.prps        = {}
		self.ui2         = 0
		self.txt3        = ''
		self.ui3         = 0
		self.arr7        = []   # UInt16[9]
		self.minVec3D    = []   # float32[3] <=> Point3D_min ???
		self.maxVec3D    = []   # float32[3] <=> Point3D_max ???

class RSeDatabase():
	def __init__(self):
		self.uid         = None # Internal-Name of the object
		self.version     = -1
		self.arr1        = []   # UInt16A[4]
		self.dat1        = None # datetime
		self.arr2        = []   # UInt16A[4]
		self.dat2        = None # datetime
		self.arr3        = []   # UInt16A[4]
		self.dat3        = None # datetime
		self.arr4        = []   # UInt16A[4]
		self.arr5        = []   # UInt16A[8]
		self.txt         = ''
		self.comment     = ''

class RSeSegmentObject():
	def __init__(self):
		self.revisionRef = None # reference to RSeDbRevisionInfo
		self.values      = []
		self.segRef      = None
		self.value1      = 0
		self.value2      = 0

	def __str__(self):
		return '[%s],%02X,%02X' % (IntArr2Str(self.values, 4), self.value1, self.value2)

class RSeSegmentValue2():
	def __init__(self):
		self.index         = -1
		self.indexSegList1 = -1
		self.indexSegList2 = -1
		self.values        = []
		self.number        = -1

	def __str__(self):
		return '%02X,%02X,%X,[%s],%04X' % (self.indexSegList1, self.indexSegList2, self.index, IntArr2Str(self.values, 4), self.number)

class RSeSegment():
	def __init__(self):
		self.name        = ''
		self.ID          = None
		self.revisionRef = None # reference to RSeDbRevisionInfo
		self.value1      = 0
		self.count1      = 0
		self.count2      = 0
		self.type        = ''
		self.metaData    = None
		self.arr1        = []
		self.arr2        = []
		self.objects     = []
		self.nodes       = []

	def __str__(self):
		return '{0:<24}: count=({1}/{2}) {4} - [{5}]'.format(self.name, self.count1, self.count2, self.ID, self.value1, IntArr2Str(self.values, 4))

class RSeSegInformation():
	def __init__(self):
		self.segments    = {}
		self.val         = []      # UInt16[2]
		self.uidList1    = []
		self.uidList2    = []

class RSeStorageBlockSize():
	'''
	# The first section in the RSeMetaStream (Mxyz-files) contains the information
	# about the block lengths in the RSeBinaryData (Bxyz-files).
	# length = The length in bytes of one of the MetaData blocks
	# flags  = The flags of one of the MetaData blocks.
	# parent = The segments the
	'''

	def __init__(self, parent):
		self.parent      = parent
		self.length      = 0       # UInt31
		self.flags       = 0       # UInt1

	def __str__(self):
		return 'f=%X, l=%X' %(self.flags, self.length)

class RSeStorageSection2():
	'''
	 # arr[1] = RSeDbRevisionInfo.data[0]
	 # arr[3] = RSeDbRevisionInfo.data[2]
	 # arr[4] = RSeDbRevisionInfo.data[3]
	'''
	def __init__(self, parent):
		self.revisionRef = None    # reference to RSeDbRevisionInfo
		self.flag        = None
		self.val         = 0
		self.parent      = parent
		self.arr         = []

	def __str__(self):
		a = ''
		u = ''
		if (len(self.arr) > 0):
			a = ' [%s]' %(IntArr2Str(self.arr, 4))
		if (self.revisionRef is not None):
			u = ' - %s' %(self.revisionRef)

		return '%X, %X%s%s' %(self.flag, self.val, u, a)

class RSeStorageSection3():
	def __init__(self, parent):
		self.uid         = None
		self.parent      = parent
		self.arr         = []      # UInt16[6]

	def __str__(self):
		return '%s: [%s]' %(self.uid, IntArr2Str(self.arr, 4))

class RSeStorageSection4Data():
	def __init__(self):
		self.num         = 0       # UInt16
		self.val         = 0       # UInt32

	def __str__(self):
		return '(%04X,%08X)' %(self.num, self.val)

class RSeStorageBlockType():
	def __init__(self, parent):
		self.parent      = parent
		self.typeID      = None
		self.arr         = []      # RSeStorageSection4Data[2]

	def __str__(self):
		return '%s: [%s,%s]' %(self.typeID, self.arr[0], self.arr[1])

class RSeStorageSection4Data1():
	def __init__(self, uid, val):
		self.uid         = uid
		self.val         = val

	def __str__(self):
		return '[%s,%d]' %(self.uid, self.val)

class RSeStorageSection5():
	def __init__(self, parent):
		self.parent      = parent
		self.indexSec4   = []

class RSeStorageSection6():
	def __init__(self, parent):
		self.parent      = parent
		self.arr1        = []
		self.arr2        = []

class RSeStorageSection7():
	def __init__(self, parent):
		self.parent = parent
		self.segRef      = None
		self.segName     = None
		self.revisionRef = None
		self.dbRef       = None
		self.arr1        = []
		self.txt1        = ''
		self.arr2        = []
		self.txt2        = ''
		self.arr3        = []
		self.txt3        = ''

	def __str__(self):
		if (self.dbRef is None):
			if (self.segName is None):
				return '%r' %(self.segRef)
			return '\'%s\'' %(self.segName)
		if (self.segName is None):
			return '[%s] [%s] [%s] [%s] %r %r %r' %(self.segRef, self.arr1, self.arr2, self.arr3, self.txt1, self.txt2, self.txt3)
		return '[%s] [%s] [%s] [%s] %r %r %r' %(self.segName, self.arr1, self.arr2, self.arr3, self.txt1, self.txt2, self.txt3)

class RSeStorageSection8():
	def __init__(self, parent):
		self.parent      = parent
		self.dbRevisionInfoRef = None
		self.arr         = []      # UInt16[2]

	def __str__(self):
		return '[%s]' %(IntArr2Str(self.arr, 4))

class RSeStorageSection9():
	def __init__(self, parent):
		self.parent      = parent
		self.uid         = None
		self.arr         = []      # UInt16[3]

	def __str__(self):
		return '%s: [%s]' %(self.uid, IntArr2Str(self.arr, 4))

class RSeStorageSectionA():
	def __init__(self, parent):
		self.uid         = None
		self.parent      = parent
		self.arr         = []      # UInt16[4]

	def __str__(self):
		return '[%s]' %(IntArr2Str(self.arr, 4))

class RSeStorageSectionB():
	def __init__(self, parent):
		self.parent      = parent
		self.uid         = None
		self.arr         = []      # UInt16[2]

	def __str__(self):
		return '[%s]' %(IntArr2Str(self.arr, 4))

class RSeMetaData():
	AM_APP       = 'AmAppSegment'
	PM_APP       = 'PmAppSegment'
	DL_APP       = 'DlAppSegment'
	AM_B_REP     = 'AmBREPSegment'
	PM_B_REP     = 'PmBRepSegment'
	AM_BROWSER   = 'AmBrowserSegment'
	PM_BROWSER   = 'PmBrowserSegment'
	DL_BROWSER   = 'DlBrowserSegment'
	AM_D_C       = 'AmDcSegment'
	PM_D_C       = 'PmDCSegment'
	DL_D_C       = 'DLSheet14DCSegment'
	DL_D_L       = 'DLSheet14DLSegment'
	DL_DIRECTORY = 'DlDirectorySegment'
	DL_DOC       = 'DlDocDCSegment'
	AM_GRAPHICS  = 'AmGraphicsSegment'
	PM_GRAPHICS  = 'PmGraphicsSegment'
	AM_RESULT    = 'AmRxSegment'
	PM_RESULT    = 'PmResultSegment'
	DEFAULT      = 'Default'
	DESIGN_VIEW  = 'DesignViewSegment'
	EE_DATA      = 'EeDataSegment'
	EE_SCENE     = 'EeSceneSegment'
	DL_S_M       = 'DLSheet14SMSegment'
	FB_ATTRIBUTE = 'FBAttributeSegment'
	NB_NOTEBOOK  = 'NBNotebookSegment'

	def __init__(self):
		self.txt1        = ''
		self.ver         = 0
		self.name        = ''
		self.dat1        = ''
		self.val1        = 0
		self.dat2        = ''
		self.arr1        = []
		self.arr2        = []
		self.segRef      = None
		self.arr3        = []
		self.sec1        = []
		self.sec2        = []
		self.sec3        = []
		self.sec4        = {}
		self.sec5        = []
		self.sec6        = []
		self.sec7        = []
		self.sec8        = []
		self.sec9        = []
		self.secA        = []
		self.secB        = []
		self.uid2        = None # should always be '9744e6a4-11d1-8dd8-0008-2998bedddc09'
		self.nodes       = None

	@staticmethod
	def isApp(seg):
		return (seg) and ((seg.name == RSeMetaData.PM_APP) or (seg.name == RSeMetaData.AM_APP) or (seg.name == RSeMetaData.DL_APP))

	@staticmethod
	def isBRep(seg):
		return (seg) and ((seg.name == RSeMetaData.PM_B_REP) or (seg.name == RSeMetaData.AM_B_REP))

	@staticmethod
	def isBrowser(seg):
		return (seg) and ((seg.name == RSeMetaData.PM_BROWSER) or (seg.name == RSeMetaData.AM_BROWSER) or (seg.name == RSeMetaData.DL_BROWSER))

	@staticmethod
	def isDefault(seg):
		return (seg) and (seg.name == RSeMetaData.DEFAULT)

	@staticmethod
	def isDC(seg):
		return (seg) and ((seg.name == RSeMetaData.PM_D_C) or (seg.name == RSeMetaData.AM_D_C) or (seg.name == RSeMetaData.DL_D_C))

	@staticmethod
	def isGraphics(seg):
		return (seg) and ((seg.name == RSeMetaData.PM_GRAPHICS) or (seg.name == RSeMetaData.AM_GRAPHICS))

	@staticmethod
	def isResult(seg):
		return (seg) and ((seg.name == RSeMetaData.PM_RESULT) or (seg.name == RSeMetaData.AM_RESULT))

	@staticmethod
	def isDesignView(seg):
		return (seg) and (seg.name == RSeMetaData.DESIGN_VIEW)

	@staticmethod
	def isEeData(seg):
		return (seg) and (seg.name == RSeMetaData.EE_DATA)

	@staticmethod
	def isEeScene(seg):
		return (seg) and (seg.name == RSeMetaData.EE_SCENE)

	@staticmethod
	def isFBAttribute(seg):
		return (seg and (seg.name == RSeMetaData.FB_ATTRIBUTE))

	@staticmethod
	def isNBNotebook(seg):
		return (seg and (seg.name == RSeMetaData.NB_NOTEBOOK))

class Inventor():
	def __init__(self):
		self.UFRxDoc               = None
		self.RSeDb                 = None
		self.RSeSegInfo            = None
		self.RSeDbRevisionInfoMap  = None
		self.RSeDbRevisionInfoList = None
		self.DatabaseInterfaces    = None
		self.iProperties           = {}
		self.RSeStorageData        = {}

class DbInterface():
	def __init__(self, name):
		self.name        = name
		self.type        = 0
		self.data        = []
		self.uid         = None
		self.value       = None

	def __str__(self):
		if (self.type   == 0x01):
			typ = 'BOOL'
		elif (self.type == 0x04):
			typ = 'SINT'
		elif (self.type == 0x10):
			typ = 'UUID'
		elif (self.type == 0x30):
			typ = 'FLOAT[]'
		elif (self.type == 0x54):
			typ = 'MAP'
		else:
			typ = '%4X' % self.type
		return '%s=%s:\t%s\t%s' % (self.name, self.value, typ, self.uid)

class RSeDbRevisionInfo():
	def __init__(self):
		self.ID          = ''      # UUID
		self.value1      = 0       # UINT16
		self.value2      = 0       # UINT16
		self.value3      = None    # UINT16
		# If type = 0xFFFF:
		#	BYTE + [UInt16]{8 <=> BYTE=0, 4 <=> BYTE==0}
		self.data        = []

	def __str__(self):
		if (self.value3 is None):
			v = '(%04X/%04X)' %(self.value1, self.value2)
		else:
			v = '(%04X/%04X/%04)' %(self.value1, self.value2, self.value3)
		if (len(self.data) > 0):
			return '%s,%s,[%s]' % (self.ID, v, IntArr2Str(self.data, 8))
		else:
			return '%s,%s)' % (self.ID, v)

class Thumbnail():
	def __init__(self):
		self.type        = 'PNG'
		self.width       = 0
		self.height      = 0
		self.data        = None

	def __str__(self):
		return '%s width=%d, height=%d' % (self.type, self.width, self.height)

class BrowserNodeHandler():
	def __init__(self):
		self.map         = []
		self.nodes       = []
		self.refs        = []

	def getByRef(self, ref):
		idx = 0
		if (self.map is not None):
			while (idx < len(self.map)):
				arr16 = self.map[idx]
				if (ref == self.map[0]):
					return self.nodes[idx]
		return None

class BrowserRef():
	def __init__(self):
		self.data1       = None
		self.data2       = None
		self.data3       = None
		self.data4       = None

class ResultItem4():
	a0 = None
	def __init__(self):
		self.a0          = []
		self.a1          = []
		self.a2          = []

	def __str__(self):
		return '[%s] (%s)-(%s)' %(IntArr2Str(self.a0, 4), FloatArr2Str(self.a1), FloatArr2Str(self.a2))

class GraphicsFont():
	def __init__(self):
		self.f           = 0.0     # Float64
		self.number      = -1      # UInt32
		self.ukn1        = []      # UInt16[4]
		self.ukn2        = []      # UInt8[2]
		self.ukn3        = []      # UInt16[2]
		self.name        = []      # getLen32Text16
		self.ukn4        = []      # UInt8[3]

	def __str__(self):
		return '(%d) %s (%s) %r %r %r %r' %(self.number, self.name, FloatArr2Str(self.f), self.ukn1, self.ukn2, self.ukn3, self.ukn4)

class AbstractValue():
	def __init__(self, x, factor, offset, unit):
		self.x      = x
		self.factor = factor
		self.offset = offset
		self.unit   = unit

	def __str__(self): return '%g%s' %(self.x / self.factor - self.offset, self.unit)
	def toStandard(self):  return self.__str__

class Length(AbstractValue):
	def __init__(self, x, factor = 0.1, unit = 'mm'):
		AbstractValue.__init__(self, x, factor, 0.0, unit)

	def getMM(self):      return self.x / 0.1
	def toStandard(self): return '%g mm' %(self.x / 0.1)

class Angle(AbstractValue):
	def __init__(self, a, factor, unit):
		AbstractValue.__init__(self, a, factor, 0.0, unit)

	def getRAD(self):     return self.x
	def getGRAD(self):    return degrees(self.x)
	def toStandard(self): return '%g\xC2\xB0' %(self.getGRAD())

class Mass(AbstractValue):
	def __init__(self, m, factor, unit):
		AbstractValue.__init__(self, m, factor, 0.0, unit)

	def getGram(self):    return self.x
	def toStandard(self): return '%ggr' %(self.getGram())

class Time(AbstractValue):
	def __init__(self, t, factor, unit):
		AbstractValue.__init__(self, t, factor, 0.0, unit)

class Temperature(AbstractValue):
	def __init__(self, t, factor, offset, unit):
		AbstractValue.__init__(self, t, factor, offset, unit)

	def toStandard(self): return '%g K' %(self.x)

class Velocity(AbstractValue):
	def __init__(self, v, factor, unit):
		AbstractValue.__init__(self, v, factor, 0.0, unit)

class Area(AbstractValue):
	def __init__(self, a, factor, unit):
		AbstractValue.__init__(self, a, factor, 0.0, unit)

class Volume(AbstractValue):
	def __init__(self, v, factor, unit):
		AbstractValue.__init__(self, v, factor, 0.0, unit)

class Force(AbstractValue):
	def __init__(self, F, factor, unit):
		AbstractValue.__init__(self, F, factor, 0.0, unit)

class Pressure(AbstractValue):
	def __init__(self, p, factor, unit):
		AbstractValue.__init__(self, p, factor, 0.0, unit)

class Power(AbstractValue):
	def __init__(self, p, factor, unit):
		AbstractValue.__init__(self, p, factor, 0.0, unit)

class Work(AbstractValue):
	def __init__(self, w, factor, unit):
		AbstractValue.__init__(self, w, factor, 0.0, unit)

class Electrical(AbstractValue):
	def __init__(self, l, factor, unit):
		AbstractValue.__init__(self, l, factor, 0.0, unit)

class Luminosity(AbstractValue):
	def __init__(self, l, unit):
		AbstractValue.__init__(self, l, 1.0, 0.0, unit)

class Substance(AbstractValue):
	def __init__(self, s, unit):
		AbstractValue.__init__(self, s, 1.0, 0.0, unit)

class Scalar(AbstractValue):
	def __init__(self, s):
		AbstractValue.__init__(self, s, 1.0, 0.0, '')

class Derived(AbstractValue):
	def __init__(self, s, unit):
		AbstractValue.__init__(self, s, 1.0, 0.0, unit)

class DataNode():
	def __init__(self, data, isRef):
		self.children = []
		self._map = {}
		## data must bean instance of AbstractNode!
		self.data = data
		self.isRef = isRef
		self.first = None
		self.previous = None
		self.parent = None
		self.next = None
		if (data):
			data.handled = False
			data.sketchIndex = None
			if (isRef == False):
				data.node = self

	def size(self):
		return len(self.children)

	def isLeaf(self):
		return self.size() == 0

	def getIndex(self):
		if (self.data):
			return self.data.index
		return -1

	def getRef(self, ref):
		if (ref):
			return self.getChild(ref.index)
		return None

	def getName(self):
		if (self.data):
			if (self.data.name):
				return self.data.name
		ref = self.getVariable('label')
		if (ref):
			return ref.node.name
		return ''

	def getTypeName(self):
		if (self.data):
			return self.data.typeName
		return ''

	def isHandled(self):
		if (self.data):
			return self.data.handled
		return false

	def setHandled(self, handled):
		if (self.data):
			self.data.handled = handled

	def getSketchIndex(self):
		if (self.data):
			return self.data.sketchIndex
		return None

	def setSketchEntity(self, index, entity):
		if (self.data):
			self.data.sketchIndex = index
			self.data.sketchEntity = entity

	def getSketchEntity(self):
		if (self.data):
			return self.data.sketchEntity
		return None

	def append(self, node):
		if (self.size() > 0):
			previous = self.children[len(self.children) -1]
			previous.next = node
			node.previous = previous
		else:
			self.first = node
			node.previous = None
		self.children.append(node)
		self._map[node.getIndex()] = node
		node.next = None
		node.parent = self

		return node

	def getChild(self, index):
		if (index in self._map):
			return self._map[index]
		return None

	def getFirstChild(self, key):
		child = self.first
		while (child):
			if (child.getTypeName() == key):
				return child
			child = child.next
		return None

	def getChildren(self, key):
		lst = []
		child = self.first
		while (child):
			if (child.getTypeName() == key):
				lst.append(child)
			child = child.next
		return lst

	def getVariable(self, name):
		if (self.data):
			return self.data.get(name)
		return None

	def setVariable(self, name, value):
		if (self.data):
			self.data.set(name, value)

	def getSegment(self):
		if (self.data):
			return self.data.segment
		return None

	def getRefText(self):
		name = self.getName()
		if ((name) and (len(name) > 0)):
			return '(%04X): %s \'%s\'' %(self.getIndex(), self.getTypeName(), name)
		return '(%04X): %s' %(self.getIndex(), self.getTypeName())

	def setValid(self, valid):
		if (self.data):
			self.data.valid = valid
	def isValid(self):
		if (self.data):
			return self.data.valid
		return False

	def getUnitName(self):
		if (self.data):
			return self.data.getUnitName()
		return ''

	def getDerivedUnitName(self):
		if (self.data):
			return self.data.getDerivedUnitName()
		return ''

	def __str__(self):
		node = self.data
		if (node and (node.name is None)):
			return '(%04X): %s%s' %(node.index, node.typeName, node.content)
		return '(%04X): %s \'%s\'%s' %(node.index, node.typeName, node.name, node.content)

class ParameterNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)
		self.asText = False

	def getValueRaw(self):
		return self.getVariable('valueNominal')

	def getRefText(self):
		x = self.getValue()
		try:
			if (isinstance(x, Angle)):
				return '(%04X): %s \'%s\'=%s' %(self.getIndex(), self.getTypeName(), self.getName(), x)
			if (isinstance(x, Length)):
				return '(%04X): %s \'%s\'=%s' %(self.getIndex(), self.getTypeName(), self.getName(), x)
			return '(%04X): %s \'%s\'=%s' %(self.getIndex(), self.getTypeName(), self.getName(), x)
		except Exception as e:
			return '(%04X): %s \'%s\'=%s - %s' %(self.getIndex(), self.getTypeName(), self.getName(), x, e)

	def getParameterFormula(self, parameterData, withUnits):
		subFormula = ''
		typeName   = parameterData.typeName

		if (typeName == 'ParameterValue'):
			type   = parameterData.get('type')
			unitName = ''
			if (self.asText or withUnits):
				unitName = parameterData.getUnitName()
				if (len(unitName) > 0): unitName = ' ' + unitName
			if (type == 0xFFFF):
				subFormula = unitName
			else:
				value  = parameterData.get('value')
				offset = parameterData.getUnitOffset()
				factor = parameterData.getUnitFactor()
				if (type == 0x0000): # Integer value!
					subFormula = '%d%s' %(round((value / factor) - offset, 0), unitName)
				else: # floating point value!
					subFormula = '%g%s' %((value / factor) - offset, unitName)
		elif (typeName == 'ParameterUnaryMinus'):
			subFormula = '-' + self.getParameterFormula(parameterData.get('refValue').node, withUnits)
		elif (typeName == 'ParameterConstant'):
			unitName = ''
			if (self.asText or withUnits):
				unitName = parameterData.getUnitName()
				if (len(unitName) > 0): unitName = ' ' + unitName
			subFormula = '%s%s' %(parameterData.name, unitName)
		elif (typeName == 'ParameterRef'):
			if (self.asText):
				subFormula = parameterData.get('refParameter').node.name
			else:
				subFormula = '%s_' %(parameterData.get('refParameter').node.name)
		elif (typeName == 'ParameterFunction'):
			function          = parameterData.name
			functionSupported = (function not in FunctionsNotSupported)
			if (self.asText or functionSupported):
				operandRefs = parameterData.get('operands')
				j = 0
				sep = '('
				n = len(operandRefs)
				subFormula = function
				# WORKAROUND:
				# There seems to be a bug in the 'tanh' function regarding units! => ignore units!
				ignoreUnits = (parameterData.name == 'tanh')
				if (n > 0):
					while (j < n):
						operand = self.getParameterFormula(operandRefs[j].node, withUnits and not ignoreUnits)
						j += 1
						subFormula += (sep + operand)
						sep = ';'
				else:
					subFormula += sep
				subFormula += ')'

			else:
				# Modulo operation not supported by FreeCAD
				raise UserWarning('Function \'%s\' not supported' %function)
		elif (typeName == 'ParameterOperationPowerIdent'):
			operand1 = self.getParameterFormula(parameterData.get('refOperand1').node, withUnits)
			subFormula = operand1
		elif (typeName.startswith('ParameterOperation')):
			operation = parameterData.name
			if (self.asText or (operation != '%')):
				operand1 = self.getParameterFormula(parameterData.get('refOperand1').node, withUnits)
				operand2 = self.getParameterFormula(parameterData.get('refOperand2').node, withUnits)
				subFormula = '(%s %s %s)' %(operand1, operation, operand2)
			else:
				# Modulo operation not supported by FreeCAD
				raise UserWarning('Modulo operator not supported')
		else:
			logError('>>>> ERROR don\'t now how to build formula for %s: %s!' %(typeName, parameterData.node))

		return subFormula

	def getFormula(self, asText):
		data = self.data
		self.asText = asText
		if (data):
			if (asText):
				return '\'' + self.getParameterFormula(data.get('refValue').node, True)
			try:
				return '=' + self.getParameterFormula(data.get('refValue').node, True)
			except BaseException as be:
				# replace by nominal value and unit!
				value = self.getValue()
				logWarning('    >WARNING: %s - replacing by nominal value %s!' %(be, value) )
				return '=%s' %(value)
		return ''

	def getValue(self):
		x = self.getValueRaw()
		#unitRef = self.getVariable('refUnit')
		#type = unitRef.getVariable('type')

		type = self.getUnitName()
		# Length
		if (type == 'km')       : return Length(x,  100000.00000, type)
		if (type == 'm')        : return Length(x,     100.00000, type)
		if (type == 'dm')       : return Length(x,      10.00000, type)
		if (type == 'cm')       : return Length(x,       1.00000, type)
		if (type == 'mm')       : return Length(x,       0.10000, type)
		if (type == '\xC2\xB5m'): return Length(x,       0.00100, type)
		if (type == 'in')       : return Length(x,       2.54000, type)
		if (type == 'ft')       : return Length(x,      30.48000, type)
		if (type == 'sm')       : return Length(x,  185324.52180, type)
		if (type == 'mil')      : return Length(x,       0.00254, type)
		# Mass
		if (type == 'kg')       : return Mass(x,       1.0000000, type)
		if (type == 'g')        : return Mass(x,       0.0010000, type)
		if (type == 'slug')     : return Mass(x,      14.5939000, type)
		if (type == 'lb')       : return Mass(x,       0.4535920, type)
		if (type == 'oz')       : return Mass(x,       0.0283495, type)
		# Time
		if (type == 's')        : return Time(x,       1.0000000, type)
		if (type == 'min')      : return Time(x,      60.0000000, type)
		if (type == 'h')        : return Time(x,    3600.0000000, type)
		# Temperatur
		if (type == 'K')        : return Temperature(x,     1.0,   0.00, type)
		if (type == '\xC2\xB0C'): return Temperature(x,     1.0, 273.15, type)
		if (type == '\xC2\xB0F'): return Temperature(x, 5.0/9.0, 523.67, type)
		# Angularity
		if (type == 'rad')      : return Angle(x, 1.0     , type)
		if (type == '\xC2\xB0') : return Angle(x, pi/180.0, type)
		if (type == 'gon')      : return Angle(x, pi/200.0, type)
		# Velocity
		if (type == 'm/s')      : return Velocity(x, 100.0     , type)
		# Area
		if (type == 'mm^2')     : return Area(x, 1.0           , type)
		# Volume
		if (type == 'l')        : return Volume(x, 1.0         , type)
		# Force
		if (type == 'N')        : return Force(x, 1.0          , type)
		if (type == 'dyn')      : return Force(x, 1.0          , type)
		if (type == 'ozf')      : return Force(x, 0.278013851  , type)
		# Pressure
		if (type == 'psi')      : return Pressure(x,    6890.0 , type)
		if (type == 'ksi')      : return Pressure(x, 6890000.0 , type)
		# Work
		if (type == 'J')        : return Work(x,         1.0   , type)
		if (type == 'erg')      : return Work(x,         1.0   , type)
		if (type == 'Cal')      : return Work(x,         4.184 , type)
		# Electrical
		if (type == 'A')        : return Electrical(x,   1.0   , type)
		# Luminosity
		if (type == 'cd')       : return Luminosity(x, type)
		# Substance
		if (type == 'mol')      : return Substance(x, type)
		# without Unit
		if (type == '')         : return Scalar(x) # parameter has no unit
		derivedUnit = self.getDerivedUnitName()
		if (derivedUnit is not None):
			# Length
			# Mass
			# Temperatur
			# Angularity
			if (derivedUnit == 'sr')       : return Angle(x   ,   1.0, type)
			# Velocity
			if (derivedUnit == 'f/s')      : return Velocity(x,   1.0, type)
			if (derivedUnit == 'mil/h')    : return Velocity(x,   1.0, type)
			if (derivedUnit == '1/min')    : return Velocity(x,   1.0, type)
			# Area
			if (derivedUnit == 'circ.mil') : return Area(x,       1.0, type)
			# Volume
			if (derivedUnit == 'gal')      : return Volume(x,     1.0, type)
			# Force
			if (derivedUnit == 'lbf')      : return Force(x,      1.0, type)
			# Pressure
			if (derivedUnit == 'Pa')       : return Pressure(x,   1.0, type)
			# Power
			if (derivedUnit == 'W')        : return Power(x,      1.0, type)
			if (derivedUnit == 'hp')       : return Power(x,      1.0, type)
			# Work
			if (derivedUnit == 'BTU')      : return Work(x,       1.0, type)
			# Electrical
			if (derivedUnit == 'V')        : return Electrical(x, 1.0, type)
			if (derivedUnit == 'ohm')      : return Electrical(x, 1.0, type)
			if (derivedUnit == 'C')        : return Electrical(x, 1.0, type)
			if (derivedUnit == 'F')        : return Electrical(x, 1.0, type)
			if (derivedUnit == 'y')        : return Electrical(x, 1.0, type)
			if (derivedUnit == 'Gs')       : return Electrical(x, 1.0, type)
			if (derivedUnit == 'H')        : return Electrical(x, 1.0, type)
			if (derivedUnit == 'Hz')       : return Electrical(x, 1.0, type)
			if (derivedUnit == 'maxwell')  : return Electrical(x, 1.0, type)
			if (derivedUnit == 'mho')      : return Electrical(x, 1.0, type)
			if (derivedUnit == 'Oe')       : return Electrical(x, 1.0, type)
			if (derivedUnit == 'S')        : return Electrical(x, 1.0, type)
			if (derivedUnit == 'T')        : return Electrical(x, 1.0, type)
			if (derivedUnit == 'Wb')       : return Electrical(x, 1.0, type)
			# Luminosity
			if (derivedUnit == 'lx')       : return Luminosity(x, type)
			if (derivedUnit == 'lm')       : return Luminosity(x, type)
			logError('>>>WARNING: found unsuppored derived unit - [%s] using [%s] instead!' %(derivedUnit, type))
		else:
			logError('>>>WARNING: unknown unit (%04X): \'%s\' - [%s]' %(self.getIndex(), self.getTypeName(), type))
		return Derived(x, type)

class ParameterTextNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getValueRaw(self):
		return self.getVariable('value')

	def getUnitName(self):
		return ''

	def getRefText(self):
		x = self.getValue()
		return '(%04X): %s \'%s\'=\'%s\'' %(self.getIndex(), self.getTypeName(), self.getName(), x)

	def getValue(self):
		x = self.getValueRaw()
		return x

class ParameterValue():
	def __init__(self, value):
		self.value = value

	def getValue(self):
		return self.value

	def getName(self):
		return ''

	def getTypeName(self):
		return 'Parameter'

class FeatureNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getTypeName(self):
		properties = self.getVariable('properties')
		if (properties):
			typ0 = properties[0]
			if (typ0):
				if (typ0.node.typeName == 'FxExtrusion'):
					typ1 = properties[1]
					if (typ1):
						if (typ1.node.typeName == 'FxBoundaryPatch'):
							typ5 = properties[5]
							if (typ5):
								if (typ5.node.typeName == 'Parameter'):
									if (properties[0x08] is None):
										return 'FxExtrusion'
									return 'FxEmboss'
								return typ5.node.typeName
							return typ1.node.typeName
				elif ((typ0.node.typeName == 'FxBoundaryPatch') and (len(properties) >= 8)):
					typ8 = properties[8]
					if (typ8):
						return typ8.node.typeName
				return typ0.node.typeName
		else:
			logError(' >ERROR (%04X) has no properties!' %(self.data.index))

		return self.data.typeName

	def getSubTypeName(self):
		typ = self.getVariable('properties')[1]
		if (typ):
			return typ.node.typeName
		return None

class ValueNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		if ('value' in self.data.properties):
			value = self.data.properties['value']
		else:
			value = None
		name  = self.data.name
		if (name is None):
			name = ''
		else:
			name = ' %s' %(name)
		if (value is not None):
			return '(%04X): %s%s=%X' %(self.getIndex(), self.getTypeName(), name, value)
		else:
			logError('ERROR: (%04X): %s has no value defined!' %(self.getIndex(), self.getTypeName()))
			return '(%04X): %s' %(self.getIndex(), self.getTypeName())

class Point2DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		return '(%04X): %s - x=%g, y=%g' %(self.getIndex(), self.getTypeName(), self.getVariable('x'), self.getVariable('y'))

class Point3DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		return '(%04X): %s - x=%g, y=%g, z=%g' %(self.getIndex(), self.getTypeName(), self.getVariable('x'), self.getVariable('y'), self.getVariable('z'))

class Line2DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		p = self.getVariable('points')
		return '(%04X): %s - (%04X), (%04X)' %(self.getIndex(), self.getTypeName(), p[0].index, p[1].index)

class Circle2DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		c = self.getVariable('refCenter').node
		r = self.getVariable('r')
		p = self.getVariable('points')
		points = []
		for i in p:
			if (i):
				points.append('(%04X)' %(i.index))
		return '(%04X): %s - (%04X), r=%g, %s' %(self.getIndex(), self.getTypeName(), c.index, r, ', '.join(points))

class GeometricRadius2DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		o = self.getVariable('refObject').node
		c = self.getVariable('refCenter').node
		return '(%04X): %s - o=(%04X): %s, c=(%04X)' %(self.getIndex(), self.getTypeName(), o.index, o.typeName, c.index)

class GeometricCoincident2DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		o = self.getVariable('refObject').node
		p = self.getVariable('refPoint').node
		return '(%04X): %s - o=(%04X): %s, p=(%04X): %s' %(self.getIndex(), self.getTypeName(), o.index, o.typeName, p.index, p.typeName)

class DimensionAngleNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		d = self.getVariable('refParameter').node
		l1 = self.getVariable('refLine1').node
		l2 = self.getVariable('refLine2').node
		return '(%04X): %s - d=\'%s\', l1=(%04X): %s, l2=(%04X): %s' %(self.getIndex(), self.getTypeName(), d.name, l1.index, l1.typeName, l2.index, l2.typeName)

class DimensionDistance2DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		d = self.getVariable('refParameter').node
		o1 = self.getVariable('refEntity1').node
		o2 = self.getVariable('refEntity2').node
		return '(%04X): %s - d=\'%s\', l1=(%04X): %s, l2=(%04X): %s' %(self.getIndex(), self.getTypeName(), d.name , o1.index, o1.typeName, o2.index, o2.typeName)

class B32BF6AC():
	def __init__(self, m, x):
		self.m = m
		self.x = x

	def __str__(self):
		return '%X:%g' %(self.m, self.x)

class Header0():
	def __init__(self, m, x):
		self.m = m
		self.x = x

	def __str__(self):
		return 'm=%X x=%04X' %(self.m, self.x)

class _32RRR2():
	def __init__(self, i, f, n):
		self.i = i
		self.f = f
		self.n = n

	def __str__(self):
		return 'i=%X f=%X n=%X' %(self.i, self.f, self.n)

class _32RA():
	def __init__(self, i, f, n):
		self.i = i
		self.f = f
		self.n = n

	def __str__(self):
		return 'i=%X f=%X n=%X' %(self.i, self.f, self.n)

class BRepChunk():
	def __init__(self, key, val):
		self.key = key
		self.val = val

	def __str__(self):
		if (self.key == 0x04):
			return '%X' %(self.val)
		elif (self.key == 0x06):
			return '(%s)' %(FloatArr2Str(self.val))
		elif (self.key == 0x07):
			return '\'%s\'' %(self.val)
		elif (self.key == 0x0B):
			str = '['
			sep = ''
			for x in self.val:
				str += sep
				str += '%s' %(x)
				sep = ','
			str += ']'
			return str
		elif (self.key == 0x0C):
			return '%X' %(self.val)
		elif (self.key == 0x0D):
			return '\'%s\'' %(self.val)
		elif (self.key == 0x0E):
			return '\'%s\'' %(self.val)
		elif (self.key == 0x11):
			return '\n'
		return ''

class ViewObject():
	def __init__(self):
		self.ShapeColor = None
		self.LineColor  = None
		self.PointColor = None
	def hide(self):
		pass
	def show(self):
		pass

class ModelerTxnMgr():
	def __init(self):
		self.ref_1 = None
		self.ref_2 = None
		self.lst   = []
		self.u8_0  = 0
		self.u32_0 = 0
		self.u8_1  = 0
		self.s32_0 = 0

	def __str__(self):
		return 'ref1=%s' %(self.ref_1)

class Enum(tuple): __getattr__ = tuple.index

Tolerances = Enum(['NOMINAL', 'LOWER', 'UPPER', 'MEDIAN'])

Functions  = Enum([''        , \
                   'cos'     , \
                   'sin'     , \
                   'tan'     , \
                   'acos'    , \
                   'asin'    , \
                   'atan'    , \
                   'cosh'    , \
                   'sinh'    , \
                   'tanh'    , \
                   'sqrt'    , \
                   'exp'     , \
                   'pow'     , \
                   'log'     , \
                   'log10'   , \
                   'floor'   , \
                   'ceil'    , \
                   'round'   , \
                   'abs'     , \
                   'sign'    , \
                   'max'     , \
                   'min'     , \
                   'random'  , \
                   'acosh'   , \
                   'asinh'   , \
                   'atanh'   , \
                   'isolate'])

FunctionsNotSupported = ['sign', 'random', 'acosh', 'asinh', 'atanh', 'isolate']