# -*- coding: utf-8 -*-

'''
importerClasses.py:
Collection of classes necessary to read and analyse Autodesk (R) Invetor (R) files.
'''

import sys
from importerUtils import IntArr2Str, FloatArr2Str, logWarning, logError, getInventorFile, getUInt16, getUInt16A, getFileVersion
from math          import degrees, radians, pi
from FreeCAD       import ParamGet

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

model = None

class RSeDatabase():
	def __init__(self):
		self.segInfo = RSeSegInformation()
		self.uid     = None # Internal-Name of the object
		self.schema  = -1
		self.arr1    = []
		self.dat1    = None
		self.arr2    = []
		self.dat2    = None
		self.txt     = u""

class RSeSegInformation():
	def __init__(self):
		self.text     = u""
		self.arr1     = []
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
		return u"%s, count=(%d/%d), ID={%s}, value1=%04X, arr1=[%s], arr2=[%s]" %(self.name, self.count1, self.count2, self.ID, self.value1, IntArr2Str(self.arr1, 4), IntArr2Str(self.arr2, 4))

	def __repr__(self):
		return self.__str__()

class RSeStorageBlockSize():
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

class RSeStorageSection2():
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
		self.parent = parent
		self.uid    = None
		self.arr    = []      # RSeStorageSection4Data[2]

	def __str__(self):
		return '%s: [%s,%s]' %(self.uid, self.arr[0], self.arr[1])

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
		self.parent      = parent
		self.uid         = None
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
	SEG_APP_ASSEMBLY      = 'AmAppSegment'
	SEG_APP_PART          = 'PmAppSegment'
	SEG_APP_DL            = 'DlAppSegment'
	SEG_B_REP_ASSEMBLY    = 'AmBREPSegment'
	SEG_B_REP_MB          = 'MbBrepSegment'
	SEG_B_REP_PART        = 'PmBRepSegment'
	SEG_BROWSER_ASSEMBLY  = 'AmBrowserSegment'
	SEG_BROWSER_PART      = 'PmBrowserSegment'
	SEG_BROWSER_DL        = 'DlBrowserSegment'
	SEG_D_C_ASSEMBLY      = 'AmDcSegment'
	SEG_D_C_PART          = 'PmDCSegment'
	SEG_DIR_DL            = 'DlDirectorySegment'
	SEG_DOC_DL            = 'DlDocDCSegment'
	SEG_GRAPHICS_ASSEMBLY = 'AmGraphicsSegment'
	SEG_GRAPHICS_MB       = 'MbGraphicsSegment'
	SEG_GRAPHICS_PART     = 'PmGraphicsSegment'
	SEG_RESULT_ASSEMBLY   = 'AmRxSegment'
	SEG_RESULT_PART       = 'PmResultSegment'
	SEG_DESIGN_VIEW       = 'DesignViewSegment'
	SEG_DATA_EE           = 'EeDataSegment'
	SEG_SCENE_EE          = 'EeSceneSegment'
	SEG_SHT14_DC_DL       = 'DLSheet14DCSegment'
	SEG_SHT14_DL_DL       = 'DLSheet14DLSegment'
	SEG_SHT14_SM_DL       = 'DLSheet14SMSegment'
	SEG_ATTR_FB           = 'FBAttributeSegment'
	SEG_NOTEBOOK_NB       = 'NBNotebookSegment'
	SEG_DEFAULT           = 'Default'

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
		self.secBlkTyps  = {}
		self.sec5        = []
		self.sec6        = []
		self.sec7        = []
		self.sec8        = []
		self.sec9        = []
		self.secA        = []
		self.secB        = []
		self.uid2        = None # should always be '9744e6a4-11d1-8dd8-0008-2998bedddc09'
		self.nodes       = None
		self.elementNodes = {}
		self.indexNodes  = {}
		self.tree        = DataNode(None, False)
	def __repr__(self):
		return self.name

	def isApp(self): # Application settings/options
		return (self.name in [RSeMetaData.SEG_APP_PART, RSeMetaData.SEG_APP_ASSEMBLY, RSeMetaData.SEG_APP_DL])

	def isBRep(self): # ACIS representation
		return (self.name in [RSeMetaData.SEG_B_REP_PART, RSeMetaData.SEG_B_REP_ASSEMBLY, RSeMetaData.SEG_B_REP_MB])

	def isBrowser(self): # Model broweser settings
		return (self.name in [RSeMetaData.SEG_BROWSER_PART, RSeMetaData.SEG_BROWSER_ASSEMBLY, RSeMetaData.SEG_BROWSER_DL])

	def isDefault(self):
		return (self.name == RSeMetaData.SEG_DEFAULT)

	def isDC(self): # Model definition
		return (self.name in [RSeMetaData.SEG_D_C_PART, RSeMetaData.SEG_D_C_ASSEMBLY, RSeMetaData.SEG_SHT14_DC_DL])

	def isGraphics(self): # Model graphics definition
		return (self.name in [RSeMetaData.SEG_GRAPHICS_PART, RSeMetaData.SEG_GRAPHICS_ASSEMBLY, RSeMetaData.SEG_GRAPHICS_MB])

	def isResult(self):
		return (self.name in [RSeMetaData.SEG_RESULT_PART, RSeMetaData.SEG_RESULT_ASSEMBLY])

	def isDesignView(self):
		return (self.name == RSeMetaData.SEG_DESIGN_VIEW)

	def isEeData(self):
		return (self.name == RSeMetaData.SEG_DATA_EE)

	def isEeScene(self):
		return (self.name == RSeMetaData.SEG_SCENE_EE)

	def isFBAttribute(self):
		return (self.name == RSeMetaData.SEG_ATTR_FB)

	def isNBNotebook(self):
		return (self.name == RSeMetaData.SEG_NOTEBOOK_NB)

class RSeRevisions():
	def __init__(self, *args, **kwargs):
		self.mapping = {}
		self.infos   = []

class Inventor():
	def __init__(self):
		self.UFRxDoc            = None
		self.RSeDb              = RSeDatabase()
		self.RSeRevisions       = RSeRevisions()
		self.DatabaseInterfaces = None
		self.iProperties        = {}
		self.RSeMetaData        = {}

	def getDC(self):
		'''
		Returns the segment that contains the 3D-objects.
		'''
		for seg in self.RSeMetaData.values():
			if (seg.isDC()): return seg
		return None

	def getBRep(self):
		'''
		Returns the segment that contains the boundary representation.
		'''
		for seg in self.RSeMetaData.values():
			if (seg.isBRep()): return seg
		return None

	def getGraphics(self):
		'''
		Returns the segment that contains the graphic objects.
		'''
		for seg in self.RSeMetaData.values():
			if (seg.isGraphics()): return seg
		return None

class DbInterface():
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

class RSeDbRevisionInfo():
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
		self.number      = -1      # UInt32
		self.ukn1        = 0       # UInt16[4]
		self.ukn2        = []      # UInt8[2]
		self.ukn3        = []      # UInt16[2]
		self.name        = []      # getLen32Text16
		self.ukn4        = []      # Float32[2]
		self.ukn5        = []      # UInt8[3]

	def __str__(self):
		return u"(%d) %s %r %r %r %r %r" %(self.number, self.name, self.ukn1, self.ukn2, self.ukn3, self.ukn4, self.ukn5)

class Lightning():
	def __init__(self):
		self.n1 = 0
		self.c1 = None
		self.c2 = None
		self.c3 = None
		self.a1 = []
		self.a2 = []
	def __str__(self):
		return '%d: %s, %s, %s, [%s], [%s]' %(self.n1, self.c1, self.c2, self.c3, FloatArr2Str(self.a1), FloatArr2Str(self.a2))

class AbstractValue():
	def __init__(self, x, factor, offset, unit):
		self.x      = x
		self.factor = factor
		self.offset = offset
		self.unit   = unit
	def __str__(self):  return u"%g%s" %(self.x / self.factor - self.offset, self.unit)
	def __repr__(self): return self.toStandard()
	def toStandard(self):  return self.__str__()

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
		AbstractValue.__init__(self, s, 1.0, 0.0, u'')

class Derived(AbstractValue):
	def __init__(self, s, unit):
		AbstractValue.__init__(self, s, 1.0, 0.0, unit)

class DataNode():
	def __init__(self, data, isRef):
		## data must bean instance of AbstractData!
		if (data):
			assert isinstance(data, AbstractData), 'Data is not a AbstractData (%s)!' %(data.__class__.__name__)
			if (isRef == False): data.node = self
		self.data = data
		self.isRef = isRef
		self.children = []
		self._map = {}
		self.parent = None
		self.first = None
		self.previous = None
		self.next = None

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
	def sketchEntity(self):
		if (self.data): return self.data.sketchEntity
		return None

	@property
	def segment(self):
		if (self.data): return self.data.segment
		return None

	def size(self):
		return len(self.children)

	def isLeaf(self):
		return self.size() == 0

	def getRef(self, ref):
		if (ref): return self.getChild(ref.index)
		return None

	@property
	def name(self):
		if (self.data): return self.data.getName()
		return None

	@property
	def sketchIndex(self):
		if (self.data): return self.data.sketchIndex
		return None

	def setSketchEntity(self, index, entity):
		if (self.data):
			self.data.sketchIndex = index
			self.data.sketchEntity = entity

	def append(self, node):
		if (self.size() > 0):
			previous = self.children[len(self.children) -1]
			previous.next = node
			node.previous = previous
		else:
			self.first = node
			node.previous = None
		self.children.append(node)
		self._map[node.index] = node
		node.next = None
		node.parent = self

		return node

	def getChild(self, index):
		try:
			return self._map[index]
		except:
			return None

	def getFirstChild(self, key):
		child = self.first
		while (child):
			if (child.typeName == key): return child
			child = child.next
		return None

	def getChildren(self, key):
		lst = []
		child = self.first
		while (child):
			if (child.typeName == key): lst.append(child)
			child = child.next
		return lst

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
		if ((name) and (len(name) > 0)):
			return u'(%04X): %s \'%s\'' %(self.index, self.typeName, name)
		return u'(%04X): %s' %(self.index, self.typeName)

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
				return u'(%04X): %s \'%s\'%s' %(node.index, node.typeName, name, content)
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
		label = self.get('label')
		if (label is None):
			logError(u"    (%04X): %s - has no required label attribute!", self.index, self.typeName)
			return []
		while (label.typeName != 'Label'):
			dummy = label
			label = label.get('label')
			if (label is None):
				logError(u"    (%04X): %s - has no required label attribute!", dummy.index, dummy.typeName)
		return label.get('participants')

class ParameterNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)
		self.asText  = False

	def getValueRaw(self):
		return self.get('valueNominal')

	def getRefText(self): # return unicode
		x = self.getValue()
		try:
			if (isinstance(x, Angle)):  return u'(%04X): %s \'%s\'=%s' %(self.index, self.typeName, self.name, x)
			if (isinstance(x, Length)): return u'(%04X): %s \'%s\'=%s' %(self.index, self.typeName, self.name, x)
			return u'(%04X): %s \'%s\'=%s' %(self.index, self.typeName, self.name, x)
		except Exception as e:
			return u'(%04X): %s \'%s\'=%s - %s' %(self.index, self.typeName, self.name, x, e)

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
				subFormula = '%g%s' %(parameterData.get('value'), unitName)
			else:
				value  = parameterData.get('value')
				offset = parameterData.getUnitOffset()
				factor = parameterData.getUnitFactor()
				if (type == 0x0000): # Integer value!
					subFormula = '%d%s' %(round((value / factor) - offset, 0), unitName)
				else: # floating point value!
					subFormula = '%g%s' %((value / factor) - offset, unitName)
		elif (typeName == 'ParameterUnaryMinus'):
			subFormula = '-' + self.getParameterFormula(parameterData.get('value'), withUnits)
		elif (typeName == 'ParameterConstant'):
			unitName = ''
			if (self.asText or withUnits):
				unitName = parameterData.getUnitName()
				if (len(unitName) > 0): unitName = ' ' + unitName
			subFormula = '%s%s' %(parameterData.name, unitName)
		elif (typeName == 'ParameterRef'):
			target = parameterData.get('target')
			if (self.asText):
				subFormula = target.name
			else:
				subFormula = '%s_' %(target.name)
		elif (typeName == 'ParameterFunction'):
			function          = parameterData.name
			functionSupported = (function not in FunctionsNotSupported)
			if (self.asText or functionSupported):
				operandRefs = parameterData.get('operands')
				# WORKAROUND:
				# There seems to be a bug in the 'tanh' function regarding units! => ignore units!
				ignoreUnits = (parameterData.name == 'tanh')
				subFormula = "(%s)" %(';'.join(["%s" %(self.getParameterFormula(ref, withUnits and not ignoreUnits)) for ref in operandRefs]))

			else:
				# Modulo operation not supported by FreeCAD
				raise UserWarning('Function \'%s\' not supported' %function)
		elif (typeName == 'ParameterOperationPowerIdent'):
			operand1 = self.getParameterFormula(parameterData.get('operand1'), withUnits)
			subFormula = operand1
		elif (typeName.startswith('ParameterOperation')):
			operation = parameterData.name
			if (self.asText or (operation != '%')):
				operand1 = self.getParameterFormula(parameterData.get('operand1'), withUnits)
				operand2 = self.getParameterFormula(parameterData.get('operand2'), withUnits)
				subFormula = '(%s %s %s)' %(operand1, operation, operand2)
			else:
				# Modulo operation not supported by FreeCAD
				raise UserWarning('Modulo operator not supported')
		else:
			logError(u"    Don't now how to build formula for %s: %s!", typeName, parameterData)

		return subFormula

	def getFormula(self, asText):
		data = self.data
		self.asText = asText
		if (data):
			refValue = data.get('value')
			if (refValue):
				if (asText):
					return u'\'' + self.getParameterFormula(refValue, True)
				try:
					return u'=' + self.getParameterFormula(refValue, True)
				except BaseException as be:
					# replace by nominal value and unit!
					value = self.getValue()
					if (sys.version_info.major < 3):
						value = unicode(value)
					logWarning(u"    %s - replacing by nominal value %s!" %(be, value))
			else:
				value = data.get('valueModel')
				if (sys.version_info.major < 3):
					value = unicode(value)
			return u'=%s' %(value)
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
		# Temperatur
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
			logWarning(u"    found unsuppored derived unit - [%s] using [%s] instead!", derivedUnit, type)
		else:
			logWarning(u"WARNING: unknown unit (%04X): '%s' - [%s]", self.index, self.typeName, type)
		return Derived(x, type)

class ParameterTextNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getValueRaw(self):
		return self.get('value')

	def getUnitName(self): # return unicode
		return u''

	def getRefText(self): # return unicode
		return u'(%04X): %s \'%s\'=\'%s\'' %(self.index, self.typeName, self.name, self.getValue())

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

class EnumNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

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
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		return u'(%04X): %s - (%g,%g,%g)' %(self.index, self.typeName, self.get('dirX'), self.get('dirY'), self.get('dirZ'))

class BendEdgeNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		p1 = self.get('from')
		p2 = self.get('to')
		return u'(%04X): %s - (%g,%g,%g)-(%g,%g,%g)' %(self.index, self.typeName, p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])

class SketchNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)
		data.sketchEdges = {}
		data.associativeIDs = {}
		return

class BlockPointNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		p = self.get('point')
		return u"(%04X): %s - (%g,%g)" %(self.index, self.typeName, p.get('x'), p.get('y'))

class Block2DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self):
		sketch = self.get('source')
		return u"(%04X): %s '%s'" %(self.index, self.typeName, sketch.name)

class FeatureNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

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

		if (p4 == 'Face'):
			if (p1 == 'FxExtend'):                  return 'Extend'
			return 'Rip'
		if (p0 == 'EdgeCollectionProxy'):
			p4 = self._getPropertyName(4)
			if (p4 == '7DAA0032'):                  return 'Chamfer'
			if (p1 == 'Parameter'):                 return 'Bend'
			if (p1 == 'FxExtend'):                  return 'Extend'
			if (p1 is None):                        return 'CornerChamfer'
		elif (p0 == 'SurfaceBodies'):
			if (p1 == 'ObjectCollection'):          return 'Combine'
			if (p1 == 'SurfaceBody'):               return 'AliasFreeform'
			if (p1 == 'SurfaceBodies'):             return 'CoreCavity'
			if (p1 == 'Face'):
				p7 = self._getPropertyEnumName(7)
				if (p7 == 'EBB23D6E_Enum'):         return 'Refold'
				if (p7 == '4688EBA3_Enum'):         return 'Unfold'
		elif (p0 == 'SurfaceBody'):
			if (p1 == 'Face'):
				p7 = self._getPropertyEnumName(7)
				if (p7 == 'EBB23D6E_Enum'):         return 'Refold'
				if (p7 == '4688EBA3_Enum'):         return 'Unfold'
		elif (p0 == 'Enum'):
			p2 = self._getPropertyName(2)
			p3 = self._getPropertyName(3)
			if (p1 == 'BoundaryPatch'):
				p6 = self._getPropertyName(6)
				if (p2 == 'Line3D'):
					if (p6 is None):                return 'Revolve'
					if (p6 == 'ExtentType'):        return 'Cut'
					return 'Coil'
				elif (p2 == 'Direction'):
					if (p6 == 'Parameter'):         return 'Emboss'
					p10 = self._getPropertyName(0x10)
					if (p10 == 'ParameterBoolean'): return 'Cut'
					p21 = self._getPropertyName(0x21)
					if (p21 == 'ParameterBoolean'): return 'Cut'
					return 'Extrude'
				return 'Coil'
			if (p1 == 'FaceCollection'):            return 'Shell'
			if (p1 == 'Parameter'):                 return 'Hole'
			if (p1 == 'ParameterBoolean'):
				if (p3 == 'Enum'):                  return 'Split'
				if (p2 == 'ParameterBoolean'):      return 'Fold'
			if (p2 == 'ParameterBoolean'):          return 'SnapFit'
		elif (p0 == 'FxFilletConstant'):
			p8 = self._getPropertyName(8)
			if (p8 == 'ParameterBoolean'):          return 'Fillet'
			if (p8 == 'Enum'):                      return 'Fillet'
		elif (p1 == 'FxFilletVariable'):            return 'Fillet'
		elif (p0 == 'FaceCollection'):
			if (p1 == 'Enum'):                      return 'FaceMove'
			if (p1 == 'FaceCollection'):            return 'FaceReplace'
			if (p1 == 'ParameterBoolean'):
				p3 = self._getPropertyName(3)
				if (p3 == 'SurfaceBodies'):         return 'FaceDelete'
				if (p3 == 'Parameter'):             return 'Thread'
		elif (p0 == 'BoundaryPatch'):
			p2 = self._getPropertyName(2)
			if (p2 == 'BoundaryPatch'):             return 'Grill'
			if (p1 == 'FaceBoundOuterProxy'):       return 'Sweep'
			if (p1 == 'FaceBoundProxy'):            return 'Sweep'
			if (p1 == 'Direction'):                 return 'Extrude'
			if (p1 == 'BoundaryPatch'):             return 'Rib'
			if (p1 == 'SurfaceBody'):               return 'BoundaryPatch'
			if (p1 == 'Parameter'):
				if (p2 == 'ShellDirection'):        return 'Rest'
				return 'BendPart'
			p4 = self._getPropertyName(4)
			if (p4 == 'SurfaceBody'):               return 'BoundaryPatch'
		elif (p0 == 'Direction'):
			if (p1 == 'EdgeCollectionProxy'):       return 'Lip'
			if (p1 == 'FaceCollection'):            return 'FaceDraft'
		elif (p0 == 'CA02411F'):                    return 'NonParametricBase'
		elif (p0 == 'EB9E49B0'):                    return 'Freeform'
		elif (p0 == 'FaceBoundOuterProxy'):
			if (p4 == 'EdgeCollectionProxy'):       return 'Hem'
			return 'Plate'
		elif (p0 == 'ObjectCollection'):            return 'Knit'
		elif (p0 == 'SurfacesSculpt'):              return 'Sculpt'
		elif (p0 == 'TrimType'):                    return 'Trim'
		elif (p0 == 'SurfaceBody'):
			if (p1 == 'FaceBoundProxy'):            return 'LoftedFlangeDefinition'
			if (p1 == 'SurfaceBody'):               return 'Reference'
		elif (p0 == 'CornerSeam'):                  return 'Corner'
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
			if (p1 == 'EdgeCollectionProxy'):       return 'Lip'
			if (p1 == 'FaceBoundOuterProxy'):       return 'ContourRoll'
			if (p1 == 'SurfaceBody'):               return 'BoundaryPatch'
			if (p10 == 'FilletFullRoundSet'):       return 'Fillet'
		elif (p0 == 'D70E9DDA'):                    return 'FilletRule'
		elif (p0 == 'ParameterBoolean'):            return 'Boss'

		# Missing Features:
		# - (Cosmetic-)Weld - only IAM files???
		# - SurfaceMid -> FEM!
		# - SurfaceRuled
		# - PatternMove -> PatternRectangular
		# - MeshPresentation
		# - FaceOffset -> same as thicken but without solid fill!
		return 'Unknown'

	def getRefText(self): # return unicode
		return u'(%04X): Fx%s \'%s\'' %(self.data.index, self.getSubTypeName(), self.name)

	def __str__(self):
		return u"(%04X): Fx%s '%s'%s" %(self.data.index, self.getSubTypeName(), self.name, self.data.content)

class ValueNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		try:
			value = self.data.properties['value']
		except:
			value = None
		name = self.data.name
		if (name is None or len(name) == 0):
			name = ''
		else:
			name = ' ' + name
		if (value is not None):
			if (type(value) is int):
				return u'(%04X): %s%s=%X' %(self.index, self.typeName, name, value)
			if (type(value) is float):
				return u'(%04X): %s%s=%g' %(self.index, self.typeName, name, value)
			return u'(%04X): %s%s=%s' %(self.index, self.typeName, name, value)
		logError(u"    (%04X): %s has no value defined!", self.index, self.typeName)
		return u'(%04X): %s' %(self.index, self.typeName)

class PointNode(DataNode): # return unicoe
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		if (self.typeName[-2:] == '2D'):
			point = self
			if (point.typeName != 'Point2D'):
				return u'(%04X): %s' %(self.index, self.typeName)
			return u'(%04X): %s - (%g,%g)' %(self.index, self.typeName, point.get('x'), point.get('y'))
		return u'(%04X): %s - (%g,%g,%g)' %(self.index, self.typeName, self.get('x'), self.get('y'), self.get('z'))

class LineNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		if (self.typeName[-2:] == '2D'):
			p0 = self.get('points')[0]
			if (p0 is None):
				x0 = self.get('x')
				y0 = self.get('y')
			else:
				x0 = p0.get('x')
				y0 = p0.get('y')
			p1 = self.get('points')[1]
			x1 = p1.get('x')
			y1 = p1.get('y')
			return u'(%04X): %s - (%g,%g) - (%g,%g)' %(self.index, self.typeName, x0, y0, x1, y1)
		x0 = self.get('x')
		y0 = self.get('y')
		z0 = self.get('z')
		x1 = self.get('dirX') + x0
		y1 = self.get('dirY') + y0
		z1 = self.get('dirZ') + z0
		return u'(%04X): %s - (%g,%g,%g) - (%g,%g,%g)' %(self.index, self.typeName, x0, y0, z0, x1, y1, z1)

class CircleNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		r = self.get('r')
		p = self.get('points')
		points = ''
		for i in p:
			if (i):
				if (self.typeName[-2:] == '2D'):
					try:
						points += ', (%g,%g)' %(i.get('x'), i.get('y'))
					except:
						logError(u"ERROR> (%04X): %s - x=%s, y=%s, r=%s, points=%s", i.index, i.typeName, i.get('x'), i.get('y'), r, points)
				else:
					points += ', (%g,%g,%g)' %(i.get('x'), i.get('y'), i.get('z'))
		if (self.typeName[-2:] == '2D'):
			c = self.get('center')
			return u'(%04X): %s - (%g,%g), r=%g%s' %(self.index, self.typeName, c.get('x'), c.get('y'), r, points)
		return u'(%04X): %s - (%g,%g,%g), r=%g%s' %(self.index, self.typeName, self.get('x'), self.get('y'), self.get('z'), r, points)

class GeometricRadius2DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		o = self.get('entity')
		c = self.get('center')
		return u'(%04X): %s - o=(%04X): %s, c=(%04X)' %(self.index, self.typeName, o.index, o.typeName, c.index)

class GeometricCoincident2DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		e1 = self.get('entity1')
		e2 = self.get('entity2')
		if (e1.typeName == 'Point2D'):
			return u'(%04X): %s - (%g,%g)\t(%04X): %s' %(self.index, self.typeName, e1.get('x'), e1.get('y'), e2.index, e2.typeName)
		if (e2.typeName == 'Point2D'):
			return u'(%04X): %s - (%g,%g)\t(%04X): %s' %(self.index, self.typeName, e2.get('x'), e2.get('y'), e1.index, e1.typeName)
		return u'(%04X): %s - e1=(%04X): %s, e2=(%04X): %s' %(self.index, self.typeName, e1.index, e1.typeName, e2.index, e2.typeName)

class DimensionAngleNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		d = self.get('parameter')
		if (self.typeName == 'Dimension_Angle2Line2D'):
			l1 = self.get('line1')
			l2 = self.get('line2')
			return u'(%04X): %s - d=\'%s\', l1=(%04X): %s, l2=(%04X): %s' %(self.index, self.typeName, d.name, l1.index, l1.typeName, l2.index, l2.typeName)
		p1 = self.get('point1')
		p2 = self.get('point2')
		p3 = self.get('point3')
		return u'(%04X): %s - d=\'%s\', p1=(%04X): %s, p2=(%04X): %s, p3=(%04X): %s' %(self.index, self.typeName, d.name, p1.index, p1.typeName, p2.index, p2.typeName, p3.index, p3.typeName)

class DimensionDistance2DNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		d = self.get('parameter')
		e1 = self.get('entity1')
		e2 = self.get('entity2')
		if (e1.typeName == 'Point2D'):
			if (e2.typeName == 'Point2D'):
				return u'(%04X): %s - d=\'%s\', (%g,%g), (%g,%g)' %(self.index, self.typeName, d.name, e1.get('x'), e1.get('y'), e2.get('x'), e2.get('y'))
			return u'(%04X): %s - d=\'%s\', (%g,%g)\t(%04X): %s' %(self.index, self.typeName, d.name, e1.get('x'), e1.get('y'), e2.index, e2.typeName)
		if (e2.typeName == 'Point2D'):
			return u'(%04X): %s - d=\'%s\', (%g,%g)\t(%04X): %s' %(self.index, self.typeName, d.name, e2.get('x'), e2.get('y'), e1.index, e1.typeName)
		return u'(%04X): %s - d=\'%s\', e1=(%04X): %s, e2=(%04X): %s' %(self.index, self.typeName, d.name, e1.index, e1.typeName, e2.index, e2.typeName)

class SurfaceBodiesNode(DataNode):
	def __init__(self, data, isRef):
		DataNode.__init__(self, data, isRef)

	def getRefText(self): # return unicode
		bodies = self.get('bodies')
		names = ','.join([u"'%s'" %(b.name) for b in bodies])
		return u'(%04X): %s %s' %(self.index, self.typeName, names)

class Header0():
	def __init__(self, m, x):
		self.m = m
		self.x = x

	def __str__(self):
		return 'm=%X x=%04X' %(self.m, self.x)
	def __repr__(self): return self.__str__()

class ModelerTxnMgr():
	def __init__(self):
		self.ref_1 = None
		self.ref_2 = None
		self.lst   = []
		self.u32_0 = 0
		self.u8_0  = 0
		self.u32_1 = 0
		self.u8_1  = 0
		self.s32_0 = 0

	def __str__(self):
		s = ",".join(["[%s]" %IntArr2Str(a, 4) for a in self.lst])
		return 'ref1=%s ref2=%s lst=[%s] [(%04X,%02X),(%04X,%02X)] %d' %(self.ref_1, self.ref_2, s, self.u32_0, self.u8_0, self.u32_1, self.u8_1, self.s32_0)

class AbstractData():
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
		self.sketchEntity = None
		self.sketchIndex  = None
		self.sketchPos    = None
		self.valid        = True
		self.handled      = False

	def set(self, name, value):
		'''
		Sets the value for the property name.
		name:  The name of the property.
		value: The value of the property.
		'''
		oldVal = self.properties.get(name)
		if (name): self.properties[name] = value
		return oldVal

	def get(self, name):
		'''
		Returns the value fo the property given by the name.
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
		if (self.name is None):
			label = self.get('label')
			if (label): return label.name
		return self.name

	def __str__(self): # return unicode
		if (self.name is None):
			return u"(%04X): %s%s" %(self.index, self.uid, self.content.encode(sys.getdefaultencoding()))
		return u"(%04X): %s '%s'%s" %(self.index, self.uid, self.name, self.content.encode(sys.getdefaultencoding()))

	def __repr__(self):
		if (self.name is None):
			return u"(%04X): %s" %(self.index, self.uid)
		return u"(%04X): %s '%s'" %(self.index, self.uid, self.name)

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

def createNewModel():
	global model
	model = Inventor()

def getModel():
	global model
	return model
