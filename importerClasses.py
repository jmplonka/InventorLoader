# -*- coding: utf-8 -*-

'''
importerClasses.py:
Collection of classes necessary to read and analyse Autodesk (R) Invetor (R) files.
'''

import sys, os, Part
from importerUtils import IntArr2Str, FloatArr2Str, logWarning, logError, getInventorFile, getUInt16, getUInt16A, isEqual, isEqual1D
from math          import degrees, radians, pi
from FreeCAD       import Vector as VEC
from PySide.QtCore import *
from PySide.QtGui  import *

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

model = None

PART_LINE = Part.Line
if (hasattr(Part, "LineSegment")):
	PART_LINE = Part.LineSegment

SEG_APP             = 'AppSegmentType'
SEG_APP_AM          = 'AmAppSegmentType'
SEG_APP_PM          = 'PmAppSegmentType'
SEG_BREP_AM         = 'AmBREPSegmentType'
SEG_BREP_MB         = 'MbBrepSegmentType'
SEG_BREP_PM         = 'PmBrepSegmentType'
SEG_BROWSER_AM      = 'AmBRxSegmentType'
SEG_BROWSER_DL      = 'DlBRxSegmentType'
SEG_BROWSER_DX      = 'DxBRxSegmentType'
SEG_BROWSER_PM      = 'PmBRxSegmentType'
SEG_BROWSER_PM_OLD  = 'PmBrowserSegment'
SEG_DC_AM           = 'AmDcSegmentType'
SEG_DC_DL           = 'DlDocDcSegmentType'
SEG_DC_DX           = 'DxDcSegmentType'
SEG_DC_PM           = 'PmDcSegmentType'
SEG_DESIGN_VIEW     = 'FWxDesignViewType'
SEG_DESIGN_VIEW_MGR = 'FWxDesignViewManagerType'
SEG_DIRECTORY_DL    = 'DlDirectorySegmentType'
SEG_EE_DATA         = 'EeDataSegmentType'
SEG_EE_SCENE        = 'EeSceneSegmentType'
SEG_FB_ATTRIBUTE    = 'FBAttributeSegment'
SEG_GRAPHICS_AM     = 'AmGRxSegmentType'
SEG_GRAPHICS_MB     = 'MbGRxSegmentType'
SEG_GRAPHICS_PM     = 'PmGRxSegmentType'
SEG_NOTEBOOK        = 'NotebookSegmentType'
SEG_RESULT_AM       = 'AmRxSegmentType'
SEG_RESULT_PM       = 'PmResultSegmentType'
SEG_SHEET_DC_DL     = 'DlSheetDcSegmentType'
SEG_SHEET_DL_DL     = 'DlSheetDlSegmentType'
SEG_SHEET_SM_DL     = 'DlSheetSmSegmentType'

SEGMENTS_APP = [SEG_APP, SEG_APP_AM, SEG_APP_PM]
SEGMENTS_BRP = [SEG_BREP_AM, SEG_BREP_MB, SEG_BREP_PM]
SEGMENTS_BRX = [SEG_BROWSER_AM, SEG_BROWSER_DL, SEG_BROWSER_DX, SEG_BROWSER_PM]
SEGMENTS_DOC = [SEG_DC_AM, SEG_DC_DL, SEG_DC_DX, SEG_DC_PM]
SEGMENTS_DVW = [SEG_DESIGN_VIEW, SEG_DESIGN_VIEW_MGR]
SEGMENTS_DIR = [SEG_DIRECTORY_DL]
SEGMENTS_EED = [SEG_EE_DATA]
SEGMENTS_EES = [SEG_EE_SCENE]
SEGMENTS_FBA = [SEG_FB_ATTRIBUTE]
SEGMENTS_GRX = [SEG_GRAPHICS_AM, SEG_GRAPHICS_MB, SEG_GRAPHICS_PM]
SEGMENTS_NTB = [SEG_NOTEBOOK]
SEGMENTS_RSX = [SEG_RESULT_AM, SEG_RESULT_PM]
SEGMENTS_SHT = [SEG_SHEET_DC_DL, SEG_SHEET_DL_DL, SEG_SHEET_SM_DL]

class VersionInfo(object):
	def __init__(self):
		self.revision = 0
		self.minor    = 0
		self.major    = 0
		self.data     = (0, 0, 0, 0, 0)
	def getDisplayName(self):
		if (self.major > 11):
			return "Version %d.%d%d" %(self.major + 1996, self.minor, self.revision)
		return "Version %d.%d%d" %(self.major, self.minor, self.revision)
	def getBits(self): return 64 if ((self.data[0] & 0x40)) > 0 else 32
	def __str__(self): return "Version %d.%d.%d [%s]" %(self.major, self.minor, self.revision, IntArr2Str(self.data, 2))
	def __repr__(self): return self.__str__()

class RSeDatabase(object):
	def __init__(self):
		self.segInfo = RSeSegInformation()
		self.uid     = None # Internal-Name of the object
		self.schema  = -1
		self.vers1   = None
		self.dat1    = None
		self.arr2    = []
		self.vers2   = None
		self.dat2    = None
		self.txt     = u""

class RSeSegInformation(object):
	def __init__(self):
		self.text     = u""
		self.vers     = []
		self.date     = None
		self.uid      = None
		self.arr2     = []
		self.arr3     = []
		self.u16      = 0
		self.text2    = u""
		self.arr4     = []
		self.segments = {}
		self.val      = []      # UInt16[2]
		self.uidList1 = []
		self.uidList2 = []

class RSeSegmentObject(object):
	def __init__(self):
		self.revisionRef = None # reference to RSeDbRevisionInfo
		self.values      = []
		self.segRef      = None
		self.value1      = 0
		self.value2      = 0

	def __str__(self):
		return '[%s],%02X,%02X' % (IntArr2Str(self.values, 4), self.value1, self.value2)

class RSeSegmentValue2(object):
	def __init__(self):
		self.index         = -1
		self.indexSegList1 = -1
		self.indexSegList2 = -1
		self.values        = []
		self.number        = -1

	def __str__(self):
		return '%02X,%02X,%X,[%s],%04X' % (self.indexSegList1, self.indexSegList2, self.index, IntArr2Str(self.values, 4), self.number)

class RSeSegment(object):
	def __init__(self):
		self.name        = ''
		self.ID          = None
		self.revisionRef = None # reference to RSeDbRevisionInfo
		self.value1      = 0
		self.count1      = 0
		self.count2      = 0
		self.type        = ''
		self.metaData    = None
		self.arr1        = [] # ???, ???, ???, numSec1, ???
		self.arr2        = []
		self.version     = None
		self.value2      = 0
		self.objects     = []
		self.nodes       = []

	def __str__(self):
		return u"%s:%s, count=(%d/%d), ID={%s}, value1=%04X, arr1=[%s], arr2=[%s], value2=%04X, %s" %(self.type, self.name, self.count1, self.count2, self.ID, self.value1, IntArr2Str(self.arr1, 4), IntArr2Str(self.arr2, 4), self.value2, self.version)

	def __repr__(self):
		return self.__str__()

	def __lt__(self, other):
		return self.name < other.name

class RSeStorageBlockSize(object):
	'''
	# The first section in the RSeMetaStream (Mxyz-files) contains the information
	# about the block lengths in the RSeBinaryData (Bxyz-files).
	# length = The length in bytes of one of the MetaData blocks
	# flags  = The flags of one of the MetaData blocks.
	# parent = The segments the
	'''
	def __init__(self, parent, value):
		self.parent = parent
		self.length = (value & 0x7FFFFFFF)
		self.flags  = ((value & 0x80000000) > 0)

	def __str__(self):
		return 'f=%X, l=%X' %(self.flags, self.length)

class RSeStorageSection2(object):
	'''
	 # arr[1] = RSeDbRevisionInfo.data[0]
	 # arr[3] = RSeDbRevisionInfo.data[2]
	 # arr[4] = RSeDbRevisionInfo.data[3]
	'''
	def __init__(self, parent):
		self.parent   = parent
		self.revision = None    # reference to RSeDbRevisionInfo
		self.flag     = None
		self.val      = 0
		self.arr      = []

	def __str__(self):
		a = ''
		u = ''
		if (len(self.arr) > 0):
			a = ' [%s]' %(IntArr2Str(self.arr, 4))
		if (self.revision is not None):
			u = ' - %s' %(self.revision)
		return '%X, %X%s%s' %(self.flag, self.val, u, a)

class RSeStorageSection3(object):
	def __init__(self, parent):
		self.uid         = None
		self.parent      = parent
		self.arr         = []      # UInt16[6]

	def __str__(self):
		return '%s: [%s]' %(self.uid, IntArr2Str(self.arr, 4))

class RSeStorageSection4Data(object):
	def __init__(self):
		self.num         = 0       # UInt16
		self.val         = 0       # UInt32

	def __str__(self):
		return '(%04X,%08X)' %(self.num, self.val)

class RSeStorageBlockType(object):
	def __init__(self, parent):
		self.parent = parent
		self.uid    = None
		self.arr    = []      # RSeStorageSection4Data[2]

	def __str__(self):
		return '%s: [%s,%s]' %(self.uid, self.arr[0], self.arr[1])

class RSeStorageSection4Data1(object):
	def __init__(self, uid, val):
		self.uid         = uid
		self.val         = val

	def __str__(self):
		return '[%s,%d]' %(self.uid, self.val)

class RSeStorageSection5(object):
	def __init__(self, parent):
		self.parent      = parent
		self.indexSec4   = []

class RSeStorageSection6(object):
	def __init__(self, parent):
		self.parent      = parent
		self.arr1        = []
		self.arr2        = []

class RSeStorageSection7(object):
	def __init__(self, parent):
		self.parent      = parent
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
			return u"'%s'" %(self.segName)
		if (self.segName is None):
			return '[%s] [%s] [%s] [%s] %r %r %r' %(self.segRef, self.arr1, self.arr2, self.arr3, self.txt1, self.txt2, self.txt3)
		return '[%s] [%s] [%s] [%s] %r %r %r' %(self.segName, self.arr1, self.arr2, self.arr3, self.txt1, self.txt2, self.txt3)

class RSeStorageSection8(object):
	def __init__(self, parent):
		self.parent      = parent
		self.dbRevisionInfoRef = None
		self.arr         = []      # UInt16[2]

	def __str__(self):
		return '[%s]' %(IntArr2Str(self.arr, 4))

class RSeStorageSection9(object):
	def __init__(self, parent):
		self.parent      = parent
		self.uid         = None
		self.arr         = []      # UInt16[3]

	def __str__(self):
		return '%s: [%s]' %(self.uid, IntArr2Str(self.arr, 4))

class RSeStorageSectionA(object):
	def __init__(self, parent):
		self.parent      = parent
		self.uid         = None
		self.arr         = []      # UInt16[4]

	def __str__(self):
		return '[%s]' %(IntArr2Str(self.arr, 4))

class RSeStorageSectionB(object):
	def __init__(self, parent):
		self.parent      = parent
		self.uid         = None
		self.arr         = []      # UInt16[2]

	def __str__(self):
		return '[%s]' %(IntArr2Str(self.arr, 4))

class RSeRevisions(object):
	def __init__(self):
		self.mapping = {}
		self.infos   = []
	def __del__(self):
		self.mapping.clear()
		self.infos[:] = []

class Inventor(object):
	def __init__(self):
		self.UFRxDoc            = None
		self.RSeDb              = RSeDatabase()
		self.RSeRevisions       = RSeRevisions()
		self.iProperties        = {}
		self.RSeMetaData        = {}
	def __del__(self):
		self.iProperties.clear()
		self.RSeMetaData.clear()

	def __repr__(self):
		if (getInventorFile() is None): return u"#NV#"
		return u"[%d]: %s" %(self.RSeDb.vers1.DisplayName(), os.path.split(os.path.abspath(getInventorFile()))[-1])

	def getApp(self):
		'''
		Returns the segment that contains the application settings.
		'''
		for seg in self.RSeMetaData.values():
			if (seg.isApp()): return seg
		return EMPTY_SEGMENT

	def getBRep(self):
		'''
		Returns the segment that contains the boundary representation.
		'''
		for seg in self.RSeMetaData.values():
			if (seg.isBRep()): return seg
		return EMPTY_SEGMENT

	def getBrowser(self):
		for seg in self.RSeMetaData.values():
			if (seg.isBrowser()): return seg
		return EMPTY_SEGMENT

	def getDC(self):
		'''
		Returns the segment that contains the 3D-objects.
		'''
		for seg in self.RSeMetaData.values():
			if (seg.isDC()): return seg
		return EMPTY_SEGMENT

	def getDesignViews(self):
		views = []
		for seg in self.RSeMetaData.values():
			if (seg.isDesignView()):
				views.append(seg)
		return views

	def getDirectory(self):
		for seg in self.RSeMetaData.values():
			if (seg.isDirectory()): return seg
		return EMPTY_SEGMENT

	def getEeData(self):
		for seg in self.RSeMetaData.values():
			if (seg.isEeData()): return seg
		return EMPTY_SEGMENT

	def getEeScene(self):
		for seg in self.RSeMetaData.values():
			if (seg.isEeScene()): return seg
		return EMPTY_SEGMENT

	def getFBAttribute(self):
		for seg in self.RSeMetaData.values():
			if (seg.isFBAttribute()): return seg
		return EMPTY_SEGMENT

	def getGraphics(self):
		'''
		Returns the segment that contains the graphic objects.
		'''
		for seg in self.RSeMetaData.values():
			if (seg.isGraphics()): return seg
		return EMPTY_SEGMENT

	def getNBNotebook(self):
		for seg in self.RSeMetaData.values():
			if (seg.isNBNotebook()): return seg
		return EMPTY_SEGMENT

	def getResult(self):
		for seg in self.RSeMetaData.values():
			if (seg.isResult()): return seg
		return EMPTY_SEGMENT

	def getSheets(self):
		sheets = []
		for seg in self.RSeMetaData.values():
			if (seg.isSheet()):
				sheets.append(seg)
		return sheets

class DbInterface(object):
	TYPE_MAPPING = {
		0x01: 'BOOL',
		0x04: 'SINT',
		0x10: 'UUID',
		0x30: 'FLOAT[]',
		0x54: 'MAP'
	}
	def __init__(self, name):
		self.name        = name
		self.type        = 0
		self.data        = []
		self.uid         = None
		self.value       = None

	def __str__(self):
		typeName = DbInterface.TYPE_MAPPING.get(self.type, '%4X' % self.type)
		return '%s=%s:\t%s\t%s' % (self.name, self.value, typeName, self.uid)

class RSeDbRevisionInfo(object):
	def __init__(self):
		self.ID     = ''
		self.flags  = 0
		self.type   = 0
		self.b      = 0
		self.a      = []
	def __repr__(self):
		return "%s" %(self.ID)

	def __str__(self):
		if len(self.a) == 2: return u"{%s},%06X,%04X,%02X,[%g,%08X]" %(str(self.ID).upper(), self.flags, self.type, self.b, self.a[0], self.a[1])
		if len(self.a) == 4: return u"{%s},%06X,%04X,%02X,[%g,%08X]" %(str(self.ID).upper(), self.flags, self.type, self.b, self.a[0], self.a[1])
		return u"{%s},%06X,%04X,%02X,%s" %(str(self.ID).upper(), self.flags, self.type, self.b, self.a)

	def __repr__(self):
		return self.__str__()

class ResultItem4(object):
	a0 = None
	def __init__(self):
		self.a0          = []
		self.a1          = []
		self.a2          = []

	def __str__(self):
		return '[%s] (%s)-(%s)' %(IntArr2Str(self.a0, 4), FloatArr2Str(self.a1), FloatArr2Str(self.a2))

class GraphicsFont(object):
	def __init__(self):
		self.number      = -1      # UInt32
		self.ukn1        = 0       # UInt16[4]
		self.ukn2        = []      # UInt8[2]
		self.ukn3        = []      # UInt16[2]
		self.name        = []      # getLen32Text16
		self.ukn4        = []      # Float32[2]
		self.ukn5        = []      # UInt8[3]

	def __str__(self):
		return u"(%d) %s %r %r %r %r %r" %(self.number, self.name, self.ukn1, self.ukn2, self.ukn3, self.ukn4, self.ukn5)

class Lightning(object):
	def __init__(self):
		self.n1 = 0
		self.c1 = None
		self.c2 = None
		self.c3 = None
		self.a1 = []
		self.a2 = []
	def __str__(self):
		return '%d: %s, %s, %s, [%s], [%s]' %(self.n1, self.c1, self.c2, self.c3, FloatArr2Str(self.a1), FloatArr2Str(self.a2))

class AbstractValue(object):
	def __init__(self, x, factor, offset, unit):
		self.x      = x
		self.factor = factor
		self.offset = offset
		self.unit   = unit
	def __str__(self):  return u"%g%s" %(self.x / self.factor - self.offset, self.unit)
	def __repr__(self): return self.toStandard()
	def toStandard(self):  return self.__str__()
	def getNominalValue(self):
		return self.x / self.factor + self.offset
	def __sub__(self):
		return self.__class__(-self.x, self.factor, self.unit)
	def __neg__(self):
		return self.__class__(-self.x, self.factor, self.unit)
	def __sub__(self, other):
		if (isinstance(other, AbstractValue)):
			return self.__class__(self.x - other.x, self.factor, self.unit)
		return self.__class__(self.x - other, self.factor, self.unit)
	def __add__(self, other):
		if (isinstance(other, AbstractValue)):
			return self.__class__(self.x + other.x, self.factor, self.unit)
		return self.__class__(self.x + other, self.factor, self.unit)
	def __mul__(self, other):
		if (isinstance(other, AbstractValue)):
			return self.__class__(self.x * other.x, self.factor, self.unit)
		return self.__class__(self.x * other, self.factor, self.unit)

class Length(AbstractValue):
	def __init__(self, x, factor = 0.1, unit = 'mm'):
		super(Length, self).__init__(x, factor, 0.0, unit)
	def getMM(self):      return self.x / 0.1
	def toStandard(self): return '%g mm' %(self.x / 0.1)

class Angle(AbstractValue):
	def __init__(self, a, factor, unit):
		super(Angle, self).__init__(a, factor, 0.0, unit)
	def getRAD(self):     return self.x
	def getGRAD(self):    return degrees(self.x)
	def toStandard(self): return '%g\xC2\xB0' %(self.getGRAD())

class Mass(AbstractValue):
	def __init__(self, m, factor, unit):
		super(Mass, self).__init__(m, factor, 0.0, unit)
	def getGram(self):    return self.x
	def toStandard(self): return '%ggr' %(self.getGram())

class Time(AbstractValue):
	def __init__(self, t, factor, unit):
		super(Time, self).__init__(t, factor, 0.0, unit)

class Temperature(AbstractValue):
	def __init__(self, t, factor, offset, unit):
		super(Temperature, self).__init__(t, factor, offset, unit)
	def toStandard(self): return '%g K' %(self.x)

class Velocity(AbstractValue):
	def __init__(self, v, factor, unit):
		super(Velocity, self).__init__(v, factor, 0.0, unit)

class Area(AbstractValue):
	def __init__(self, a, factor, unit):
		super(Area, self).__init__(a, factor, 0.0, unit)

class Volume(AbstractValue):
	def __init__(self, v, factor, unit):
		super(Volume, self).__init__(v, factor, 0.0, unit)

class Force(AbstractValue):
	def __init__(self, F, factor, unit):
		super(Force, self).__init__(F, factor, 0.0, unit)

class Pressure(AbstractValue):
	def __init__(self, p, factor, unit):
		super(Pressure, self).__init__(p, factor, 0.0, unit)

class Power(AbstractValue):
	def __init__(self, p, factor, unit):
		super(Power, self).__init__(p, factor, 0.0, unit)

class Work(AbstractValue):
	def __init__(self, w, factor, unit):
		super(Work, self).__init__(w, factor, 0.0, unit)

class Electrical(AbstractValue):
	def __init__(self, l, factor, unit):
		super(Electrical, self).__init__(l, factor, 0.0, unit)

class Luminosity(AbstractValue):
	def __init__(self, l, unit):
		super(Luminosity, self).__init__(l, 1.0, 0.0, unit)

class Substance(AbstractValue):
	def __init__(self, s, unit):
		super(Substance, self).__init__(s, 1.0, 0.0, unit)

class Scalar(AbstractValue):
	def __init__(self, s):
		super(Scalar, self).__init__(s, 1.0, 0.0, u'')

class Derived(AbstractValue):
	def __init__(self, s, unit):
		super(Derived, self).__init__(s, 1.0, 0.0, unit)

class DataNode(object):
	def __init__(self, data):
		## data must be an instance of AbstractData!
		if (data):
			assert isinstance(data, AbstractData), 'Data is not a AbstractData (%s)!' %(data.__class__.__name__)
		self.data = data
		self.isRef = False
		self.children = []

	@property
	def typeName(self):
		if (self.data): return self.data.typeName
		return ''

	@property
	def index(self):
		if (self.data): return self.data.index
		return -1

	@property
	def handled(self):
		if (self.data): return self.data.handled
		return False
	@handled.setter
	def handled(self, handled):
		if (self.data): self.data.handled = handled

	@property
	def valid(self):
		if (self.data): return self.data.valid
		return False
	@valid.setter
	def valid(self, valid):
		if (self.data): self.data.valid = valid

	@property
	def geometry(self):
		if (self.data): return self.data.geometry
		return None

	@property
	def segment(self):
		if (self.data): return self.data.segment
		return None

	def size(self):
		return len(self.children)

	def isLeaf(self):
		return self.size() == 0

	@property
	def name(self):
		if (self.data): return self.data.getName()
		return None

	@property
	def sketchIndex(self):
		if (self.data): return self.data.sketchIndex
		return None

	def setGeometry(self, geometry, index=1):
		if (self.data):
			self.data.geometry = geometry
			self.data.sketchIndex = index

	def append(self, node):
		self.children.append(node)
		node.parent = self
		return node

	@property
	def next(self):
		p = self.parent
		if (p is None):
			return None
		for i, e in enumerate(p.children):
			if (e.index == self.index):
				if (i < p.size()-1):
					return p.children[i+1]
		return None

	def getFirstChild(self, key):
		for child in self.children:
			if (child.typeName == key): return child
		return None

	def get(self, name):
		if (self.data): return self.data.get(name)
		return None

	def set(self, name, value):
		if (self.data): self.data.set(name, value)

	def getSegment(self):
		if (self.data): return self.data.segment
		return None

	def getRefText(self): # return unicode
		name = self.name
		if (name):
			return u"(%04X): %s '%s'" %(self.index, self.typeName, name)
		return u"(%04X): %s" %(self.index, self.typeName)

	def getUnitName(self): # return unicode
		if (self.data): return self.data.getUnitName()
		return u''

	def getDerivedUnitName(self):
		if (self.data): return self.data.getDerivedUnitName()
		return u''

	def __str__(self):
		node = self.data
		if (node is not None):
			content = node.content
			if (sys.version_info.major < 3) and (not isinstance(content, unicode)):
				content = unicode(content)
			name = node.name
			if (name):
				if (sys.version_info.major < 3) and (not isinstance(name, unicode)):
					name = unicode(name)
				return u"(%04X): %s '%s'%s" %(node.index, node.typeName, name, content)
			return u'(%04X): %s%s' %(node.index, node.typeName, content)
		return "<NONE>"

	def __repr__(self):
		return self.__str__()

	def getSubTypeName(self):
		node = self.data
		if (node is not None):
			return node.typeName
		return None

	def getParticipants(self):
		label = self
		while (label.typeName != 'Label'):
			label = label.get('next')
			if (label is None):
				logError(u"    (%04X): %s - has no required next attribute!", label.index, label.typeName)
				return []
		return label.get('participants')

class ParameterNode(DataNode):
	def __init__(self, data):
		super(ParameterNode, self).__init__(data)

	def getValueRaw(self):
		return self.get('valueNominal')

	def getRefText(self): # return unicode
		x = self.getValue()
		try:
			if (isinstance(x, Angle)):  return u"(%04X): %s '%s'=%s" %(self.index, self.typeName, self.name, x)
			if (isinstance(x, Length)): return u"(%04X): %s '%s'=%s" %(self.index, self.typeName, self.name, x)
			return u"(%04X): %s '%s'=%s" %(self.index, self.typeName, self.name, x)
		except Exception as e:
			return u"(%04X): %s '%s'=%s - %s" %(self.index, self.typeName, self.name, x, e)

	def getParameterFormula(self, parameterData, asText):
		subFormula = ''
		typeName   = parameterData.typeName

		if (typeName == 'ParameterValue'):
			type   = parameterData.get('type')
			unitName = ''
			if (asText):
				unitName = parameterData.getUnitName()
				if (len(unitName) > 0): unitName = ' ' + unitName
			if (type == 0xFFFF):
				subFormula = '%g%s' %(parameterData.get('value'), unitName)
			else:
				value  = parameterData.get('value')
				offset = parameterData.getUnitOffset()
				factor = parameterData.getUnitFactor()
				if (type == 0x0000): # Integer value!
					subFormula = '%d%s' %(round((value / factor) - offset, 0), unitName)
				else: # floating point value!
					subFormula = '%g%s' %((value / factor) - offset, unitName)
		elif (typeName == 'ParameterConstant'):
			unitName = ''
			if (asText):
				unitName = parameterData.getUnitName()
				if (len(unitName) > 0): unitName = ' ' + unitName
			subFormula = '%s%s' %(parameterData.name, unitName)
		elif (typeName == 'ParameterRef'):
			target = parameterData.get('operand1')
			if (asText):
				subFormula = target.name
			else:
				subFormula = '%s_' %(target.name)
		elif (typeName == 'ParameterFunction'):
			function          = parameterData.name
			operandRefs = parameterData.get('operands')
			subFormula = "%s(%s)" %(function, ';'.join(["%s" %(self.getParameterFormula(ref, asText)) for ref in operandRefs]))
			if ((function in FunctionsNotSupported) and (not asText)):
				nominalValue = self.getValue().getNominalValue()
				logWarning(u"Function '%s' not supported in formula of '%s' (%s) - using nominal value %g!", function, self.name, subFormula, nominalValue)
				subFormula = '%g' %(nominalValue)
		elif (typeName == 'ParameterOperatorUnaryMinus'):
			subFormula = '-' + self.getParameterFormula(parameterData.get('operand1'), asText)
		elif (typeName == 'ParameterOperatorPowerIdent'):
			subFormula = self.getParameterFormula(parameterData.get('operand1'), asText)
		elif (typeName.startswith('ParameterOperator')):
			operation = parameterData.name
			operand1 = self.getParameterFormula(parameterData.get('operand1'), asText)
			operand2 = self.getParameterFormula(parameterData.get('operand2'), asText)
			subFormula = '(%s %s %s)' %(operand1, operation, operand2)
			if ((not asText) and (operation == '%')):
				subFormula = 'mod(%s, %s)' %(operand1, operand2)
		else:
			logError(u"    Don't now how to build formula for %s: %s!", typeName, parameterData)

		return subFormula

	def getFormula(self, asText):
		data = self.data
		if (data):
			refValue = data.get('value')
			if (refValue):
				if (asText):
					return u"'" + self.getParameterFormula(refValue, asText)
				try:
					return u"=" + self.getParameterFormula(refValue, asText)
				except BaseException as be:
					# replace by nominal value and unit!
					value = self.getValue()
					logWarning(u"    %s - replacing by nominal value %s!" %(be, value))
			else:
				value = self.getValue()
			if (asText):
				return u"'%s" %(value)
			return u"=%s" %(value.getNominalValue())

		return u''

	def getValue(self):
		x = self.getValueRaw()
		#unitRef = self.get('unit')
		#type = unitRef.get('type')

		type = self.getUnitName()
		# Length
		if (type == 'km')    : return Length(x,  100000.00000, type)
		if (type == 'm')     : return Length(x,     100.00000, type)
		if (type == 'dm')    : return Length(x,      10.00000, type)
		if (type == 'cm')    : return Length(x,       1.00000, type)
		if (type == 'mm')    : return Length(x,       0.10000, type)
		if (type == u'\xB5m'): return Length(x,       0.00100, type)
		if (type == 'in')    : return Length(x,       2.54000, type)
		if (type == 'ft')    : return Length(x,      30.48000, type)
		if (type == 'sm')    : return Length(x,  185324.52180, type)
		if (type == 'mil')   : return Length(x,       0.00254, type)
		# Mass
		if (type == 'kg')    : return Mass(x,       1.0000000, type)
		if (type == 'g')     : return Mass(x,       0.0010000, type)
		if (type == 'slug')  : return Mass(x,      14.5939000, type)
		if (type == 'lb')    : return Mass(x,       0.4535920, type)
		if (type == 'oz')    : return Mass(x,       0.0283495, type)
		# Time
		if (type == 's')     : return Time(x,       1.0000000, type)
		if (type == 'min')   : return Time(x,      60.0000000, type)
		if (type == 'h')     : return Time(x,    3600.0000000, type)
		# Temperature
		if (type == 'K')     : return Temperature(x,     1.0,   0.00, type)
		if (type == u'\xB0C'): return Temperature(x,     1.0, 273.15, type)
		if (type == u'\xB0F'): return Temperature(x, 5.0/9.0, 523.67, type)
		# Angularity
		if (type == 'rad')   : return Angle(x, 1.0     , type)
		if (type == u'\xb0') : return Angle(x, pi/180.0, type)
		if (type == 'gon')   : return Angle(x, pi/200.0, type)
		# Velocity
		if (type == 'm/s')   : return Velocity(x, 100.0     , type)
		# Area
		if (type == 'mm^2')  : return Area(x, 1.0           , type)
		# Volume
		if (type == 'l')     : return Volume(x, 1.0         , type)
		# Force
		if (type == 'N')     : return Force(x, 1.0          , type)
		if (type == 'dyn')   : return Force(x, 1.0          , type)
		if (type == 'ozf')   : return Force(x, 0.278013851  , type)
		# Pressure
		if (type == 'psi')   : return Pressure(x,    6890.0 , type)
		if (type == 'ksi')   : return Pressure(x, 6890000.0 , type)
		# Work
		if (type == 'J')     : return Work(x,         1.0   , type)
		if (type == 'erg')   : return Work(x,         1.0   , type)
		if (type == 'Cal')   : return Work(x,         4.184 , type)
		# Electrical
		if (type == 'A')     : return Electrical(x,   1.0   , type)
		# Luminosity
		if (type == 'cd')    : return Luminosity(x, type)
		# Substance
		if (type == 'mol')   : return Substance(x, type)
		# without Unit
		if (type == '')      : return Scalar(x) # parameter has no unit
		derivedUnit = self.getDerivedUnitName()
		if (derivedUnit is not None):
			# Length
			# Mass
			# Temperature
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
			logWarning(u"    found unsuppored derived unit - [%s] using [%s] instead!", derivedUnit, type)
		else:
			logWarning(u"WARNING: unknown unit (%04X): '%s' - [%s]", self.index, self.typeName, type)
		return Derived(x, type)

class ParameterTextNode(DataNode):
	def __init__(self, data):
		super(ParameterTextNode, self).__init__(data)

	def getValueRaw(self):
		return self.get('value')

	def getUnitName(self): # return unicode
		return u''

	def getRefText(self): # return unicode
		return u"(%04X): %s '%s'='%s'" %(self.index, self.typeName, self.name, self.getValue())

	def getValue(self):
		x = self.getValueRaw()
		return x

class ParameterValue(object):
	def __init__(self, value):
		self.value = value

	def getValue(self):
		return self.value

	def getName(self):
		return ''

	def getTypeName(self):
		return 'Parameter'

class EnumNode(DataNode):
	def __init__(self, data):
		super(EnumNode, self).__init__(data)

	def getValueText(self):
		enum = self.get('Values')
		value = self.get('value')
		if (type(enum) is list):
			if (value < len(enum)):
				return u"'%s'" % enum[value]
			return value
		assert (type(enum) is dict), "Expected %s to contain dict or list as enum values!"
		if (value in enum.keys()):
			return u"'%s'" % enum[value]
		return value

	def getRefText(self): # return unicode
		return u'(%04X): %s=%s' %(self.index, self.get('Enum'), self.getValueText())

	def __str__(self):
		node = self.data
		name = self.get('Enum')
		return '(%04X): %s %s%s' %(node.index, node.typeName, name, node.content)

class DirectionNode(DataNode):
	def __init__(self, data):
		super(DirectionNode, self).__init__(data)

	def getDirection(self):
		dir = self.get('dir')
		if (dir):
			return dir
		face = self.get('face')
#		if (face):
		return None

	def getRefText(self): # return unicode
		dir = self.getDirection()
		pt  = self.get('point')
		if (dir):
			if(pt):
				return u'(%04X): %s start=(%g,%g,%g), dir=(%g,%g,%g)' %(self.index, self.typeName, pt.x, pt.y, pt.z, dir.x, dir.y, dir.z)
			return u'(%04X): %s dir=(%g,%g,%g)' %(self.index, self.typeName, dir.x, dir.y, dir.z)
		if (pt):
			return u'(%04X): %s start=(%g,%g,%g)' %(self.index, self.typeName, pt.x, pt.y, pt.z)
		return u'(%04X): %s' %(self.index, self.typeName)

class BendEdgeNode(DataNode):
	def __init__(self, data):
		super(BendEdgeNode, self).__init__(data)

	def getRefText(self): # return unicode
		p1 = self.get('from')
		p2 = self.get('to')
		return u'(%04X): %s - (%g,%g,%g)-(%g,%g,%g)' %(self.index, self.typeName, p1.x, p1.y, p1.z, p2.x, p2.y, p2.z)

class SketchNode(DataNode):
	def __init__(self, data):
		super(SketchNode, self).__init__(data)
		data.sketchEdges = {}
		data.associativeIDs = {}

class BlockPointNode(DataNode):
	def __init__(self, data):
		super(BlockPointNode, self).__init__(data)

	def getRefText(self):
		p = self.get('point')
		return u"(%04X): %s - (%s)" %(self.index, self.typeName, p.typeName)

class Block2DNode(DataNode):
	def __init__(self, data):
		super(Block2DNode, self).__init__(data)

	def getRefText(self):
		sketch = self.get('source')
		return u"(%04X): %s '%s'" %(self.index, self.typeName, sketch.name)

class FeatureNode(DataNode):
	def __init__(self, data):
		super(FeatureNode, self).__init__(data)

	def _getPropertyName(self, index):
		properties = self.get('properties')
		if (properties):
			if (index < len(properties)):
				typ = properties[index]
				if (typ):
					return typ.typeName
		return None

	def _getPropertyEnumName(self, index):
		properties = self.get('properties')
		if (properties):
			if (index < len(properties)):
				typ = properties[index]
				if (typ):
					return typ.get('Enum')
		return None

	def getSubTypeName(self):
		subTypeName = self.get('Feature')
		if (subTypeName): return subTypeName

		p0 = self._getPropertyName(0)
		p1 = self._getPropertyName(1)
		p4 = self._getPropertyName(4)

		if (p4 == 'FaceItem'):
			if (p1 == 'FaceExtend'):                return 'FaceExtend'
			return 'Rip'
		if (p0 == 'EdgeCollection'):
			p4 = self._getPropertyEnumName(4)
			if (p4 == 'ChamferType'):               return 'Chamfer'
			if (p1 == 'Parameter'):                 return 'Bend'
			if (p1 == 'FaceExtend'):                return 'FaceExtend'
		elif (p0 == 'BodyCollection'):
			if (p1 == 'ObjectCollection'):          return 'Combine'
			if (p1 == 'SurfaceBody'):               return 'AliasFreeform'
			if (p1 == 'BodyCollection'):            return 'CoreCavity'
			if (p1 == 'FaceItem'):
				p7 = self._getPropertyEnumName(7)
				if (p7 == 'EBB23D6E_Enum'):         return 'Refold'
				if (p7 == '4688EBA3_Enum'):         return 'Unfold'
		elif (p0 == 'SurfaceBody'):
			if (p1 == 'FaceItem'):
				p7 = self._getPropertyEnumName(7)
				if (p7 == 'EBB23D6E_Enum'):         return 'Refold'
				if (p7 == '4688EBA3_Enum'):         return 'Unfold'
			if (p1 == 'FaceBoundProxy'):            return 'LoftedFlangeDefinition'
			if (p1 == 'SurfaceBody'):               return 'Reference'
		elif (p0 == 'Enum'):
			p2 = self._getPropertyName(2)
			p3 = self._getPropertyName(3)
			if (p1 == 'BoundaryPatch'):
				p6 = self._getPropertyName(6)
				if (p2 == 'Line3D'):
					if (p6 is None):                return 'Revolve'
					if (p6 == 'ExtentType'):        return 'Cut'
					return 'Coil'
				elif (p2 == 'DirectionAxis'):
					if (p6 == 'Parameter'):         return 'Emboss'
					p10 = self._getPropertyName(0x10)
					if (p10 == 'Boolean'):          return 'Cut'
					p21 = self._getPropertyName(0x21)
					if (p21 == 'Boolean'):          return 'Cut'
					return 'Extrude'
				return 'Coil'
			if (p1 == 'FaceCollection'):            return 'Shell'
			if (p1 == 'Parameter'):                 return 'Hole'
			if (p1 == 'Boolean'):
				if (p3 == 'Enum'):                  return 'Split'
				if (p2 == 'Boolean'):               return 'Fold'
				if (p2 == 'Parameter'):            	return 'CornerGap'
			if (p2 == 'Boolean'):                   return 'SnapFit'
		elif (p0 == 'FxFilletEdgeSetsConstantR'):
			p8 = self._getPropertyName(8)
			if (p8 == 'Boolean'):                   return 'Fillet'
			if (p8 == 'Enum'):                      return 'Fillet'
		elif (p1 == 'FxFilletEdgeSetsVariableR'):   return 'Fillet'
		elif (p0 == 'FaceCollection'):
			if (p1 == 'Enum'):                      return 'FaceMove'
			if (p1 == 'FaceCollection'):            return 'FaceReplace'
			if (p1 == 'Boolean'):
				p3 = self._getPropertyName(3)
				if (p3 == 'BodyCollection'):        return 'FaceDelete'
				if (p3 == 'Parameter'):             return 'Thread'
		elif (p0 == 'BoundaryPatch'):
			p2 = self._getPropertyName(2)
			if (p2 == 'BoundaryPatch'):             return 'Grill'
			if (p1 == 'FaceBoundOuterProxy'):       return 'Sweep'
			if (p1 == 'FaceBoundProxy'):            return 'Sweep'
			if (p1 == 'DirectionAxis'):             return 'Extrude'
			if (p1 == 'BoundaryPatch'):             return 'Rib'
			if (p1 == 'SurfaceBody'):               return 'BoundaryPatch'
			if (p1 == 'Parameter'):
				if (p2 == 'Enum'):                  return 'Rest' # Enum == Shell-Direction!
				return 'BendPart'
			p4 = self._getPropertyName(4)
			if (p4 == 'SurfaceBody'):               return 'BoundaryPatch'
		elif (p0 == 'DirectionAxis'):
			if (p1 == 'EdgeCollection'):            return 'Lip'
			if (p1 == 'FaceCollection'):            return 'FaceDraft'
		elif (p0 == 'CA02411F'):                    return 'NonParametricBase'
		elif (p0 == 'EB9E49B0'):                    return 'Freeform'
		elif (p0 == 'Freeform'):                    return 'Freeform'
		elif (p0 == 'FaceBoundOuterProxy'):
			if (p4 == 'EdgeCollection'):            return 'Hem'
			return 'Plate'
		elif (p0 == 'ObjectCollection'):
			p2 = self._getPropertyName(2)
			if (p1 == '0800FE29'):                  return 'Move'
			if (p2 == 'SurfaceBody'):               return 'Stitch'
			if (p1 == 'BodyCollection'):            return 'Stitch'
		elif (p0 == 'SculptSurfaceCollection'):     return 'Sculpt'
		elif (p0 == 'TrimType'):                    return 'Trim'
		elif (p0 == 'CornerSeam'):                  return 'CornerSeam'
		elif (p0 == 'AFD8A8E0'):                    return 'Corner'
		elif (p0 == 'LoftSections'):                return 'Loft'
#		elif (p0 == 'Parameter'):                   return 'Loft'
		elif (p0 == 'SurfaceSelection'):            return 'Thicken'
		elif (p0 == 'Transformation'):
			if (p1 == '8D6EF0BE'):                  return 'PatternRectangular'
			# FIXME: This only works for the intersection example (e.g. Shaft1.ipt has other properties)!!!!
			return 'iFeature'
		elif (p0 is None):
			p10 = self._getPropertyName(10)
			if (p1 == 'Enum'):                      return 'Thicken'
			if (p1 == '671CE131'):                  return 'RuledSurface'
			if (p1 == '8B2B8D96'):                  return 'BoundaryPatch'
			if (p1 == 'EdgeCollection'):            return 'Lip'
			if (p1 == 'FaceBoundOuterProxy'):       return 'ContourRoll'
			if (p1 == 'SurfaceBody'):               return 'BoundaryPatch'
			if (p10 == 'FilletFullRoundSet'):       return 'Fillet'
		elif (p0 == 'D70E9DDA'):                    return 'FilletRule'
		elif (p0 == 'Boolean'):                     return 'Boss'
		elif (p0 == 'Parameter'):
			if (p1 == 'Parameter'):                 return 'Link2Body' # link between Feature and Body
		# Missing Features:
		# - (Cosmetic-)Weld - only IAM files???
		# - SurfaceMid -> FEM!
		# - SurfaceRuled
		# - PatternMove -> PatternRectangular
		# - MeshPresentation
		# - FaceOffset -> same as thicken but without solid fill!
		return 'Unknown'

	def getRefText(self): # return unicode
		return u"(%04X): Fx%s '%s'" %(self.data.index, self.getSubTypeName(), self.name)

	def __str__(self):
		return u"(%04X): Fx%s '%s'%s" %(self.data.index, self.getSubTypeName(), self.name, self.data.content)

class ValueNode(DataNode):
	def __init__(self, data):
		super(ValueNode, self).__init__(data)

	def getRefText(self): # return unicode
		try:
			value = self.data.properties['value']
		except:
			value = None
		name = self.data.name
		if (name):
			name = ' ' + name
		else:
			name = ''
		if (value is not None):
			if (type(value) is int):
				return u'(%04X): %s%s=%X' %(self.index, self.typeName, name, value)
			if (type(value) is float):
				return u'(%04X): %s%s=%g' %(self.index, self.typeName, name, value)
			return u'(%04X): %s%s=%s' %(self.index, self.typeName, name, value)
		logError(u"    (%04X): %s has no value defined!", self.index, self.typeName)
		return u'(%04X): %s' %(self.index, self.typeName)

class PointNode(DataNode): # return unicoe
	def __init__(self, data):
		super(PointNode, self).__init__(data)

	def getRefText(self): # return unicode
		pos = self.get('pos')
		if (pos is None):
			return u'(%04X): %s' %(self.index, self.typeName)
		if (self.typeName[-2:] == '2D'):
			return u'(%04X): %s - (%g,%g)' %(self.index, self.typeName, pos.x, pos.y)
		return u'(%04X): %s - (%g,%g,%g)' %(self.index, self.typeName, pos.x, pos.y, pos.z)

class LineNode(DataNode):
	def __init__(self, data):
		super(LineNode, self).__init__(data)

	def getRefText(self): # return unicode
		if (self.typeName[-2:] == '2D'):
			p0 = self.get('points')[0]
			if (p0 is None):
				p0 = self.get('pos')
			else:
				p0 = p0.get('pos')
			p1 = self.get('points')[1]
			p1 = p1.get('pos')
			return u"(%04X): %s - (%g,%g) - (%g,%g)" %(self.index, self.typeName, p0.x, p0.y, p1.x, p1.y)
		p1 = self.get('pos')
		if (p1 is None):
			p1 = VEC(0,0,0)
			p2 = VEC(0,0,0)
		else:
			p2 = self.get('dir') + p1
		return u"(%04X): %s (%g,%g,%g)-(%g,%g,%g)" %(self.index, self.typeName, p1.x, p1.y, p1.z, p2.x, p2.y, p2.z)

class CircleNode(DataNode):
	def __init__(self, data):
		super(CircleNode, self).__init__(data)

	def getRefText(self): # return unicode
		r = self.get('r')
		points = ''
		for i in self.get('points'):
			if (i):
				p = i.get('pos')
				if (self.typeName[-2:] == '2D'):
					points += ', (%g,%g)' %(p.x, p.y)
				else:
					points += u", (%g,%g,%g)" %(p.x, p.y, p.z)
		if (self.typeName[-2:] == '2D'):
			c = self.get('center')
			#return u"(%04X): %s" %(self.index, self.typeName)
			p = c.get('pos')
			return u"(%04X): %s - (%g,%g), r=%g%s" %(self.index, self.typeName, p.x, p.y, r, points)
		p = self.get('pos')
		return u"(%04X): %s - (%g,%g,%g), r=%g%s" %(self.index, self.typeName, p.x, p.y, p.z, r, points)

class GeometricRadius2DNode(DataNode):
	def __init__(self, data):
		super(GeometricRadius2DNode, self).__init__(data)

	def getRefText(self): # return unicode
		o = self.get('entity')
		c = self.get('center')
		return u'(%04X): %s - o=(%04X): %s, c=(%04X)' %(self.index, self.typeName, o.index, o.typeName, c.index)

class GeometricCoincident2DNode(DataNode):
	def __init__(self, data):
		super(GeometricCoincident2DNode, self).__init__(data)

	def getRefText(self): # return unicode
		e1 = self.get('entity1')
		e2 = self.get('entity2')
		if (e1.typeName == 'Point2D'):
			p = e1.get('pos')
			return u"(%04X): %s - (%g,%g)\t(%04X): %s" %(self.index, self.typeName, p.x, p.y, e2.index, e2.typeName)
		if (e2.typeName == 'Point2D'):
			p = e2.get('pos')
			return u"(%04X): %s - (%g,%g)\t(%04X): %s" %(self.index, self.typeName, p.x, p.y, e1.index, e1.typeName)
		return u'(%04X): %s - e1=(%04X): %s, e2=(%04X): %s' %(self.index, self.typeName, e1.index, e1.typeName, e2.index, e2.typeName)

class DimensionAngleNode(DataNode):
	def __init__(self, data):
		super(DimensionAngleNode, self).__init__(data)

	def getRefText(self): # return unicode
		d = self.get('parameter')
		if (self.typeName == 'Dimension_Angle2Line2D'):
			l1 = self.get('line1')
			l2 = self.get('line2')
			return u"(%04X): %s - d='%s', l1=(%04X): %s, l2=(%04X): %s" %(self.index, self.typeName, d.name, l1.index, l1.typeName, l2.index, l2.typeName)
		p1 = self.get('point1')
		p2 = self.get('point2')
		p3 = self.get('point3')
		return u"(%04X): %s - d='%s', p1=(%04X): %s, p2=(%04X): %s, p3=(%04X): %s" %(self.index, self.typeName, d.name, p1.index, p1.typeName, p2.index, p2.typeName, p3.index, p3.typeName)

class DimensionDistance2DNode(DataNode):
	def __init__(self, data):
		super(DimensionDistance2DNode, self).__init__(data)

	def getRefText(self): # return unicode
		d = self.get('parameter')
		e1 = self.get('entity1')
		e2 = self.get('entity2')
		if (e1.typeName == 'Point2D'):
			p1 = e1.get('pos')
			if (e2.typeName == 'Point2D'):
				p2 = e2.get('pos')
				return u"(%04X): %s - d='%s', (%g,%g), (%g,%g)" %(self.index, self.typeName, d.name, p1.x, p1.y, p2.x, p2.y)
			return u"(%04X): %s - d='%s', (%g,%g)\t(%04X): %s" %(self.index, self.typeName, d.name, p1.x, p1.y, e2.index, e2.typeName)
		if (e2.typeName == 'Point2D'):
			p2 = e2.get('pos')
			return u"(%04X): %s - d='%s', (%g,%g)\t(%04X): %s" %(self.index, self.typeName, d.name, p2.x, p2.y, e1.index, e1.typeName)
		return u"(%04X): %s - d='%s', e1=(%04X): %s, e2=(%04X): %s" %(self.index, self.typeName, d.name, e1.index, e1.typeName, e2.index, e2.typeName)

class ObjectCollectionNode(DataNode):
	def __init__(self, data):
		super(ObjectCollectionNode, self).__init__(data)

	def getRefText(self): # return unicode
		bodies = self.get('items')
		names = ','.join([u"'%s'" %(b.name) for b in bodies])
		return u'(%04X): %s %s' %(self.index, self.typeName, names)

class Segment(object):
	def __init__(self):
		self.txt1         = ''
		self.ver          = 0
		self.name         = ''
		self.dat1         = ''
		self.val1         = 0
		self.dat2         = ''
		self.arr1         = []
		self.arr2         = []
		self.segID        = None
		self.segment      = None
		self.arr3         = []
		self.sec1         = []
		self.sec2         = []
		self.sec3         = []
		self.secBlkTyps   = {}
		self.sec5         = []
		self.sec6         = []
		self.sec7         = []
		self.sec8         = []
		self.sec9         = []
		self.secA         = []
		self.secB         = []
		self.uid2         = None # should always be '9744e6a4-11d1-8dd8-0008-2998bedddc09'
		self.nodes        = None
		self.elementNodes = {}
		self.indexNodes   = {}
		self.tree         = DataNode(None)
		self.acis         = None
		self.bodies       = {}

	def getDcSatAttributes(self):
		if (self.acis is None): return []
		return self.acis.get('dcAttributes')

	@property
	def type(self):
		if (self.segment): return self.segment.type
		return self.name

	def __repr__(self):
		return self.name

	def isApp(self): # Application settings/options
		return (self.type in SEGMENTS_APP)

	def isBRep(self): # ACIS data and meta information
		return (self.type in SEGMENTS_BRP)

	def isBrowser(self): # Model navigator (browser) settings
		return (self.type in SEGMENTS_BRX)

	def isDC(self): # Model definition
		return (self.type in SEGMENTS_DOC)

	def isDesignView(self):
		return (self.type in SEGMENTS_DVW)

	def isDirectory(self):
		return (self.name in SEGMENTS_DIR)

	def isEeData(self):
		return (self.type in SEGMENTS_EED)

	def isEeScene(self):
		return (self.type in SEGMENTS_EES)

	def isFBAttribute(self):
		return (self.type in SEGMENTS_FBA)

	def isGraphics(self): # Model graphics definition
		return (self.type in SEGMENTS_GRX)

	def isNBNotebook(self):
		return (self.type in SEGMENTS_NTB)

	def isResult(self):
		return (self.type in SEGMENTS_RSX)

	def isSheet(self):
		return (self.type in SEGMENTS_SHT)

EMPTY_SEGMENT = Segment()

class _AbstractEdge_(object):
	def p2v(self, p, f = 1.0):
		return VEC(p[0], p[1], p[2]) * f
	def __repr__(self):
		return self.__str__()

class PointEdge(_AbstractEdge_):
	def __init__(self, a):
		super(PointEdge, self).__init__()
		self.p = self.p2v(a, 10.0)
	def __str__(self):
		return u"Point:(%g,%g,%g)" %(self.p.x, self.p.y, self.p.z)

class LineEdge(_AbstractEdge_):
	def __init__(self, a):
		super(LineEdge, self).__init__()
		self.p1 = self.p2v(a[0:3], 10.0)
		self.p2 = self.p2v(a[3:6], 10.0) + self.p1
	def __str__(self):
		return u"Line:(%g,%g,%g)-(%g,%g,%g)" %(self.p1.x, self.p1.y, self.p1.z, self.p2.x, self.p2.y, self.p2.z)
	def __repr__(self):
		return self.__str__()
	def getGeometry(self):
		return PART_LINE(self.p1, self.p2)
	def matches(self, edge):
		if (isinstance(edge.Curve, Part.Line)):
			p1 = edge.Vertexes[0].Point
			p2 = edge.Vertexes[-1].Point
			if (isEqual(p1, self.p1) and isEqual(p2, self.p2)):
				return True
			if (isEqual(p2, self.p1) and isEqual(p1, self.p2)):
				return True
		return False

class ArcOfConicEdge(_AbstractEdge_):
	def __init__(self, center, dir, major, a, b): # Center, dir, m, radius, startAngle, sweepAngle
		super(ArcOfConicEdge, self).__init__()
		self.center = self.p2v(center, 10.0)
		self.dir    = self.p2v(dir, 1.0)
		self.major  = self.p2v(major, 10.0)
		self.a      = a
		self.b      = b
	def isArc(self):
		if (isEqual1D(abs(self.a), pi) == False):
			return True
		return (isEqual1D(abs(self.b), pi) == False)

class ArcOfCircleEdge(ArcOfConicEdge):
	def __init__(self, a): # Center, dir, m, radius, startAngle, sweepAngle
		super(ArcOfCircleEdge, self).__init__(a[0:3], a[3:6], a[6:9], a[10], a[11])
		self.radius = a[9] * 10.0
	def __str__(self):
		return u"Circle:(%g,%g,%g), (%g,%g,%g), (%g,%g,%g), %g, %g, %g" %(self.center.x, self.center.y, self.center.z, self.dir.x, self.dir.y, self.dir.z, self.major.x, self.major.y, self.major.z, self.radius, self.a, self.b)
	def getGeometry(self):
		if (self.isArc()):
			return Part.ArcOfCircle(Part.Circle(self.center, self.dir, self.radius), self.a, self.b)
		return Part.Circle(self.center, self.dir, self.radius)
	def matches(self, edge):
		curve = edge.Curve
		if (self.isArc()):
			if (isinstance(curve, Part.Circle)):
				return  (isEqual(curve.Center, self.center) and isEqual1D(curve.Radius, self.radius))
		else:
			if (isinstance(curve, Part.ArcOfCircle)):
				if (isEqual(curve.Center, self.center)):
					if (isEqual1D(curve.Radius, self.radius)):
						return  (isEqual1D(edge.FirstParmeter, self.a) and isEqual1D(edge.LastParameter, self.b))
		return False

class ArcOfEllipseEdge(ArcOfConicEdge):
	def __init__(self, a): # Center, dirMajor, dirMinor, rMajor, rMinor, startAngle, sweepAngle
		super(ArcOfEllipseEdge, self).__init__(a[0:3], a[3:6], a[6:9], a[11], a[12])
		self.majorRadius = a[9]
		self.minorRadius = a[10]
	def __str__(self):
		return u"Circle:(%g,%g,%g), (%g,%g,%g), (%g,%g,%g), %g, %g, %g, %g" %(self.center.x, self.center.y, self.center.z, self.dir.x, self.dir.y, self.dir.z, self.major.x, self.major.y, self.major.z, self.majorRadius, self.minorRadius, self.a, self.b)
	def getGeometry(self):
		if (self.isArc()):
			return Part.ArcOfEllipse(Part.Ellipse(self.center, self.majorRadius, self.minorRadius), self.a, self.b)
		return Part.Ellipse(self.center, self.majorRadius, self.minorRadius)
	def matches(self, edge):
		curve = edge.Curve
		if (self.isArc()):
			if (isinstance(curve, Part.Ellipse)):
				return  (isEqual(curve.Center, self.center) and isEqual1D(curve.MajorRadius, self.majorRadius) and isEqual1D(curve.MinorRadius, self.minorRadius))
		else:
			if (isinstance(curve, Part.ArcOfEllipse)):
				if (isEqual(curve.Center, self.center) and isEqual1D(curve.MajorRadius, self.majorRadius) and isEqual1D(curve.MinorRadius, self.minorRadius)):
					return  (isEqual1D(edge.FirstParmeter, self.a) and isEqual1D(edge.LastParameter, self.b))
		return False

class BSplineEdge(_AbstractEdge_):
	def __init__(self, a0, a1, a2, a3, a4):
		super(BSplineEdge, self).__init__()
		self.a0 = a0 + a4 # LLLd + dLLdd
		self.a1 = a1[0]
		self.a2 = a2[1]
		self.a3 = a2[0]
		self.a4 = a2[1]
		self.a5 = a3[0]
		self.a6 = a3[1]
	def __str__(self):
		return u"BSpline:(%s),[%s],[%s],[%s],[%s],[%s],[%s]" %(FloatArr2Str(self.a0), FloatArr2Str(self.a1), FloatArr2Str(self.a2), FloatArr2Str(self.a3), FloatArr2Str(self.a4), FloatArr2Str(self.a5), u",".join([u"(%g,%g,%g)"%(p[0], p[1], p[2]) for p in self.a6]))
	def getGeometry(self):
		bsc = Part.BSplineCurve()
		d   = self.a0[2] # TODO get degrees from a0[2 ???]
		p   = self.a6    #
		m   = []         # TODO get mults from ???
		k   = []         # TODO get knots from ???
		w   = []         # TODO get weights from ???
		rat = False      # TODO get Rational from a0[]
		if (rat):
			bsc.buildFromPolesMultsKnots( \
				poles         = p,        \
				mults         = m,        \
				knots         = k,        \
				periodic      = False,    \
				degree        = d,        \
				weights       = w
			)
		else:
			bsc.buildFromPolesMultsKnots( \
				poles         = p,        \
				mults         = m,        \
				knots         = k,        \
				periodic      = False,    \
				degree        = d
			)
		return bsc

class BezierEdge(_AbstractEdge_):
	def __init__(self, a0, a1):
		super(BezierEdge, self).__init__()
		self.a0 = a0
		self.a1 = a1
	def __str__(self):
		return u"Bezier:(%s: %s)" %(IntArr2Str(self.a0[1:], 3), ",".join([u"(%g,%g,%g)" %a for a in self.a1]))

class Header0(object):
	def __init__(self, m, x):
		self.m = m
		self.x = x

	def __str__(self):  return 'm=%X x=%03X' %(self.m, self.x)
	def __repr__(self): return '(%04X,%03X)' %(self.m, self.x)

class ModelerTxnMgr(object):
	def __init__(self):
		self.node  = 0  # DC.node
		self.dcIdx = 0  # DC-index ref
		self.lst = []   # 1st= ref BRep.node.ref_1,byte,key; 2nd = ref to Result.node,byte,key => mapping

	def __str__(self):
		s = ",".join(["(%04X,%02X,%04X)" %a for a in self.lst])
		return '%04X %04X [%s]' %(self.node, self.dcIdx, s)
	def __repr__(self): return self.__str__()

class AbstractData(object):
	def __init__(self):
		self.uid          = None
		self.name         = None
		self.index        = -1
		self.content      = ''
		self.references   = []
		self.properties   = {}
		self.size         = 0
		self.visible      = False
		self.construction = False
		self.segment      = None
		self.geometry     = None
		self.sketchIndex  = None
		self.sketchPos    = None
		self.valid        = True
		self.handled      = False
		self.node         = None

	def set(self, name, value):
		'''
		Sets the value for the property name.
		name:  The name of the property.
		value: The value of the property.
		'''
		if (name):
			self.properties[name] = value

	def get(self, name):
		'''
		Returns the value of the property given by the name.
		name: The name of the property.
		Returns None if the property is not yet set.
		'''
		return self.properties.get(name)

	def delete(self, name):
		'''
		Removes the value from the property given by the name.
		name: The name of the property.
		'''
		if (name in self.properties):
			del self.properties[name]

	def getName(self):
		if (hasattr(self, 'nameSet')): return self.name
		if (self.name is None):
			label = self.get('next')
			if (not label is None):
				self.nameSet = True
				self.name = label.name
		return self.name

	def __str__(self): # return unicode
		if (self.name is None):
			return u"(%04X): %s%s" %(self.index, self.uid, self.content.encode(sys.getdefaultencoding()))
		return u"(%04X): %s '%s'%s" %(self.index, self.uid, self.name, self.content.encode(sys.getdefaultencoding()))

	def __repr__(self):
		if (self.node is None):
			if (self.name is None):
				return u"(%04X): %s" %(self.index, self.uid)
			return u"(%04X): %s '%s'" %(self.index, self.uid, self.name)
		return self.node.getRefText()

class Enum(tuple): __getattr__ = tuple.index

Tolerances = Enum(['NOMINAL', 'LOWER', 'UPPER', 'MEDIAN'])

Functions  = Enum([
	''       ,
	'cos'    ,
	'sin'    ,
	'tan'    ,
	'acos'   ,
	'asin'   ,
	'atan'   ,
	'cosh'   ,
	'sinh'   ,
	'tanh'   ,
	'sqrt'   ,
	'exp'    ,
	'pow'    ,
	'log'    ,
	'log10'  ,
	'floor'  ,
	'ceil'   ,
	'round'  ,
	'abs'    ,
	'sign'   ,
	'max'    ,
	'min'    ,
	'random' ,
	'acosh'  ,
	'asinh'  ,
	'atanh'  ,
	'isolate'])

FunctionsNotSupported = ['sign', 'random', 'acosh', 'asinh', 'atanh', 'isolate']

def createNewModel():
	global model
	model = Inventor()

def getModel():
	global model
	if ('model' in globals()):
		return model
	return None

def releaseModel():
	global model
	if ('model' in globals()):
		del model

class NtEntry(object):
	def __init__(self, nameTable, key):
		self.nameTable = nameTable & 0x7FFFFFFF
		self.key       = key
		self.entry     = None
	def __repr__(self):
		if (self.nameTable is None):
			return u""
		return u"%04X[%04X]" %(self.nameTable, self.key)

class TableModel(QAbstractTableModel):
	def __init__(self, parent, mylist, header, *args):
		QAbstractTableModel.__init__(self, parent, *args)
		self.mylist = mylist
		self.header = header
		parent.setModel(self)

	def rowCount(self, parent):
		return len(self.mylist)

	def columnCount(self, parent):
		cols = [len(row) for row in self.mylist]
		if (len(cols) == 0):
			return 0
		return max(cols)

	def data(self, index, role):
		if (index.isValid()):
			value = self.mylist[index.row()][index.column()]
			if (hasattr(value, 'Value')):
				value = value.Value
			if (type(value) == bool):
				if (role == Qt.CheckStateRole):
					if value:
						return Qt.Checked
					return Qt.Unchecked
			else:
				if (role in [Qt.EditRole, Qt.DisplayRole]):
					return value
		return None

	def setData(self, index, value, role):
		if (index.isValid()):
			orgVal = self.mylist[index.row()][index.column()]
			if (role == Qt.CheckStateRole):
				value = (value == Qt.Checked)
			if (hasattr(orgVal, 'Value')):
				orgVal.Value = value
			else:
				self.mylist[index.row()][index.column()] = value
			return True
		return False

	def headerData(self, position, orientation, role):
		if ((role == Qt.DisplayRole) and (orientation == Qt.Horizontal)):
			return self.header[position]
		return QAbstractTableModel.headerData(self, position, orientation, role)

	def setHeaderData(self, position, orientation, header, role): # int, orientation, QVariant, int = Qt.EditRole
		if ((role == Qt.DisplayRole) and (orientation == Qt.Horizontal)):
			self.header[position] = header
			return True
		return QAbstractTableModel.setHeaderData(self, position, orientation, header, role)

	def insertRow(self, row, index=QModelIndex()):
		'''Insert a row into the model.'''
		self.beginInsertRows(index, row, row)
		data = ['' for c in range(self.columnCount(self.parent))]
		self.mylist.insert(row, data)
		self.endInsertRows()
		return True

	def insertRows(self, position, rows=1, index=QModelIndex()):
		'''Insert a row into the model.'''
		self.beginInsertRows(index, position, position + rows - 1)
		for row in range(rows):
			data = ['' for c in range(self.columnCount(self.parent))]
			self.mylist.insert(position + row, data)
		self.endInsertRows()
		return True

	def removeRow(self, row, index=QModelIndex()):
		'''Remove a row from the model.'''
		self.beginRemoveRows(index, row, row)
		del self.mylist[row]
		self.endRemoveRows()
		return True

	def removeRows(self, position, rows=1, index=QModelIndex()):
		'''Remove rows from the model.'''
		self.beginRemoveRows(index, position, position + rows - 1)
		del self.mylist[position:position+rows]
		self.endRemoveRows()
		return True

	def insertColumn(self, column, index=QModelIndex()):
		'''Insert a column into the model.'''
		self.beginInsertColumns(index, column, column)
		self.header.insert(column, '')
		for row in self.mylist:
			row.insert(column, '')
		self.endInsertColumns()
		return True

	def insertColumns(self, position, column=1, index=QModelIndex()):
		'''Insert a row into the model.'''
		self.beginInsertColumns(index, position, position + column - 1)
		for col in range(column):
			self.header.insert(position + col, '')
		for row in self.mylist:
			for col in range(column):
				row.insert(position + column, '')
		self.endInsertColumns()
		return True

	def removeColumn(self, column, index=QModelIndex()):
		'''Remove a column from the model.'''
		self.beginRemoveColumns(index, column, column)
		del self.header[column]
		for row in self.mylist:
			del row[column]
		self.endRemoveColumns()
		return True

	def removeColumns(self, position, column=1, index=QModelIndex()):
		'''Remove columns from the model.'''
		self.beginRemoveColumns(index, position, position + column - 1)
		for col in range(column):
			del self.header[position]
		for row in self.mylist:
			del row[position:position+column]
		self.endRemoveColumns()
		return True

	def flags(self, index):
		'''Returns the item flags for the given index.
		The base class implementation returns a combination of flags that enables the item
		and allows it to be selected.'''
		if not index.isValid():
			return Qt.NoItemFlags
		return Qt.ItemIsEnabled | Qt.ItemIsSelectable

class ParameterTableModel(TableModel):
	def __init__(self, parent, mylist, *args):
		TableModel.__init__(self, parent, mylist, ['Variant', 'Source', 'Property', 'Parameter', 'Value', 'Units'], *args)
	def flags(self, index):
		if (index.column() == 0):
			return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsUserCheckable
		if (index.column() in [1, 2, 5]): # make object's name and property and unit column read only!
			return Qt.ItemIsEnabled
		return Qt.ItemIsEnabled |Qt.ItemIsEditable

class VariantTableModel(TableModel):
	def __init__(self, parent, values, *args):
		TableModel.__init__(self, parent, values[1:], values[0], *args)
	def flags(self, index):
		return Qt.ItemIsEnabled | Qt.ItemIsEditable
