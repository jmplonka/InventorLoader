# -*- coding: utf-8 -*-
from __future__                 import unicode_literals

'''
importerSegment.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

import re, traceback, io
from importerClasses        import *
from importerTransformation import Transformation2D, Transformation3D
from importerSegNode        import isList, CheckList, SecNode, SecNodeRef, _TYP_NODE_REF_, _TYP_UINT32_A_, REF_PARENT, REF_CHILD, REF_CROSS
from importerUtils          import *
from Acis                   import clearEntities, AcisReader, setVersion, TAG_ENTITY_REF, getInteger, createNode, getNameMatchAttributes, getDcAttributes
from importerSAT            import dumpSat
from uuid                   import UUID
import importerUtils

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

_listPattern = re.compile('[^\x00]\x00\x00\x30')

_fmt_new = False

def resolveEntityReferences(node):
	acis = node.get('SAT')
	try:
		# create a node for each entity
		for entity in acis.getEntities():
			createNode(entity)

		dumpSat("%04X" %(node.index), acis)
		# resolve the roll-back information from the history
		acis.history.resolveDeltaStates()
		dumpHistory(node.index, acis.history)
	except:
		logError(traceback.format_exc())

def Read_Dummy(self, node): return 0

def dumpHistory(nodeIdx, history):
	dumpFolder = getDumpFolder()
	if (not (dumpFolder is None)):
		with open(u"%s/%04X_sat.history" %(dumpFolder, nodeIdx), 'wb') as dump:
			dump.write((u"%s:\n" %(history)).encode('utf8'))
			ds = history.getRoot()
			while (ds):
				dump.write((u"%r\n" %(ds)).encode('utf8'))
				for bb in ds.bulletin_boards:
					dump.write((u"\t%s\n" %(bb)).encode('utf8'))
					for b in bb.bulletins:
						dump.write((u"\t\t%s\n" %(b)).encode('utf8'))
				ds = ds.getNext()
	return

def checkReadAll(node, i, l):
	assert (i == l), '%s: Have not read all data (%d <> %d)' %(node.uid, i, l)

	return

def dumpData(file, data, offset, end):
	if (offset < end):
		arr8, dummy = getUInt8A(data, offset, end - offset)
		if (not file is None):
			file.write('\t[%s]\n' %(IntArr2Str(arr8, 2)))
	return

def getNodeUID(index, seg):
	assert (index in seg.secBlkTyps), "Index %X not defined in segment's section block types!" %(index)
	blockType = seg.secBlkTyps[index]
	return blockType.uid

def getStart(m, data, offset):
	if (m):
		return m.start() - offset
	return len(data)

BRANCH_NODES = {
	'Parameter':                       ParameterNode,
	'ParameterText':                   ParameterTextNode,
	'Boolean':                         ValueNode,
	'RotateClockwise':                 ValueNode,
	'3D8924FD':                        ValueNode,
	'Enum':                            EnumNode,
	'Feature':                         FeatureNode,
	'Point2D':                         PointNode,
	'Point3D':                         PointNode,
	'Line2D':                          LineNode,
	'Line3D':                          LineNode,
	'Arc2D':                           CircleNode,
	'Circle2D':                        CircleNode,
	'Circle3D':                        CircleNode,
	'Geometric_Radius2D':              GeometricRadius2DNode,
	'Geometric_Coincident2D':          GeometricCoincident2DNode,
	'Dimension_Distance2D':            DimensionDistance2DNode,
	'Dimension_Distance_Horizontal2D': DimensionDistance2DNode,
	'Dimension_Distance_Vertical2D':   DimensionDistance2DNode,
	'Dimension_Angle2Line2D':          DimensionAngleNode,
	'Dimension_Angle3Point2D':         DimensionAngleNode,
	'BodyCollection':                  ObjectCollectionNode,
	'ObjectCollection':                ObjectCollectionNode,
	'DirectionAxis':                   DirectionNode,
	'DirectionEdge':                   DirectionNode,
	'DirectionFace':                   DirectionNode,
	'DirectionPath':                   DirectionNode,
	'BendEdge':                        BendEdgeNode,
	'SketchBlock':                     SketchNode,
	'Sketch2D':                        SketchNode,
	'Sketch3D':                        SketchNode,
	'BlockPoint2D':                    BlockPointNode,
	'Block2D':                         Block2DNode,
}

def getBranchNode(data):
	nodeCls = BRANCH_NODES.get(data.typeName, DataNode)
	data.node = nodeCls(data)

def __dumpBranch(file, ref, branch, level, prefix):
	if (not file is None):
		# branch can be either an branch node or an text representation!
		file.write('\t' * level)
		file.write(prefix)
		if (ref is not None):
			file.write(ref.attrName)
			if (ref.number is not None):
				t = type(ref.number)
				if ((t is list) or (t is dict)):
					file.write(u"%s = " %(ref.number))
				elif (isString(t)):
					file.write(u"['%s'] = " %(ref.number))
				elif (t is UUID):
					file.write(u"[{%s}] = " %(str(ref.number).upper()))
				elif (t is int):
					file.write(u"[%04X] = " %(ref.number))
				elif (t is tuple):
					file.write(u"[%s] =" %(",".join("%s" %(n) for n in ref.number)))
				else:
					file.write(u"[%s] = " %(ref.number))
			else:
				file.write(u" = ")

		file.write(branch)
		file.write(u"\n")
	return

def buildBranch(parent, file, data, level, ref):
	parent.append(data.node)

	if (data.analysed == False):
		__dumpBranch(file, ref, data.node.__str__(), level, '')
		data.analysed = True
		for childRef in data.references:
			if (not childRef.analysed):
				childRef.analysed = True
				child = childRef._data
				if (child is not None):
					if (childRef.type == REF_CHILD):
						buildBranch(data.node, file, child, level + 1, childRef)
					elif (childRef.type == REF_CROSS):
						node = childRef.node
						if (node is not None):
							parent.append(childRef.node)
							__dumpBranch(file, childRef, node.getRefText(), level + 1, '*')
	else:
		__dumpBranch(file, ref, data.node.getRefText(), level, '*')
	return

def resolveReferences(nodes):
	for node in nodes.values():
		getBranchNode(node)
		node.handled = False
		node.sketchIndex = None
		node.parent = None
		isRadius2D = (node.typeName == 'Dimension_Radius2D')
		for ref in node.references:
			if (ref.index in nodes):
				ref._data = nodes[ref.index]
				if (ref.type == REF_PARENT):
					node.parent = ref._data
			elif (ref.index > -1):
				logError(u"ERROR> %s.py - index out of range for %s.%s = %X!", node.__module__, node.typeName, ref.attrName, ref.index)
			if (isRadius2D and (ref.typeName in ['Circle2D', 'Ellipse2D', 'Arc2D'])):
				radius = SecNodeRef(ref.index or 0x80000000, REF_CROSS, 'radius')
				radius._data = node
				ref._data.set(radius.name, radius)

		if (node.typeName in ['FaceBound', '603428AE', '79D4DD11', 'FaceBoundOuter']):
			refFx = node.get('proxy')
			refFx.set('profile', node)
		elif (node.typeName in ['FaceBounds']):
			refFx = node.get('proxy1')
			refFx.set('profile', node)
			refFx = node.get('proxy2')
			refFx.set('profile', node)
		elif (node.typeName == 'NMx_FFColor_Entity'):
			refFx = node.get('fx')
			refFx.set('fxColor', node)
		elif (node.typeName == 'ObjectCollectionDef'):
			definition = node.get('collection')
			definition.set('objectCollection', node)
	return

def isParent(ref, parent):
	node = ref.get('parent')
	if (node is None): return False
	return node.index == parent.index

def resolveParentNodes(nodes):
	for parent in nodes.values():
		for ref in parent.references:
			child = ref._data
			if (isParent(ref, parent)):
				ref.type = REF_CHILD
				child.parent = parent
			elif (ref.index > parent.index):
				if (ref.type == REF_CHILD):
					if (child is not None and child.parent is None):
						child.parent = parent
					else:
						ref.type = REF_CROSS
			elif (parent.parent is not None) and (parent.parent.index == ref.index):
				ref.type = REF_PARENT
			elif (ref.type == REF_PARENT) and (parent.parent.index != ref.index):
				ref.type = REF_CROSS
	return

def buildTree(file, nodes):
	# link the node's references with the corresponding nodes
	resolveReferences(nodes)

	# set the parent property for each node
	resolveParentNodes(nodes)

	# now the tree can be build
	roots = DataNode(None)
	for node in nodes.values():
		if (node.parent is None):
			buildBranch(roots, file, node, 0, None)
	return roots

def readTypedFloatArr(data, offset, size = 1):
	n, i = getUInt32(data, offset)
	a, i = getUInt32A(data, i, 2)
	b, i = getFloat64A(data, i, n * size)
	if (size > 1):
		b = reshape(b, size)
	return (a, b), i

class SegmentReader(object):

	def __init__(self, segment):
		self.segment = segment
		self.nodeCounter = 0

	def postRead(self):
		for node in self.segment.elementNodes.values():
			node.data = None

	def ReadNodeRef(self, node, offset, number, type, name):
		m, i = getUInt32(node.data, offset)
		ref = SecNodeRef(m, type, name)
		if (ref.index > 0):
			ref.number = number
			node.references.append(ref)
		else:
			ref = None
		return ref, i

	def ReadNodeRefs(self, node, offset, name, type):
		n, i = getUInt32(node.data, offset)
		lst  = []
		for j in range(n):
			ref, i = self.ReadNodeRef(node, i, j, type, name)
			if (not ref is None):
				lst.append(ref)
		node.set(name, lst)
		return i

	def ReadU32RefList(self, node, offset, name):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			val, i = getUInt32(node.data, i)
			ref, i = self.ReadNodeRef(node, i, val, REF_CROSS, name)
			lst.append([val, ref])
		node.set(name, lst)
		return i

	def ReadHeaderSU32S(self, node, typeName=None):
		if (typeName is not None): node.typeName = typeName
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def ReadHeaderU32RefU8List3(self, node, typeName = None, lstName='lst0'):
		i = node.Read_Header0(typeName)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'attrs')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, _TYP_NODE_REF_, lstName)
		i = self.skipBlockSize(i)
		return i

	def ReadFloat32Arr(self, node, offset, name):
		cnt0, i = getUInt32(node.data, offset)
		i = node.ReadUInt32A(i, 2, 'Float32Arr_' + name)

		lst = []
		l2  = []
		for j in range(cnt0):
			a1, i = getFloat32_2D(node.data, i)
			lst.append(a1)
			vec = FloatArr2Str(a1)
			l2.append('(%s)' %(vec))

		if (len(l2) > 0):
			node.content += ' {%s}' %(','.join(l2))
		node.set(name, lst)
		return i

	def ReadFloat64A(self, node, i, cnt, name, size):
		lst = []
		for j in range(cnt):
			a, i = getFloat64A(node.data, i, size)
			lst.append(a)
		node.content += ' %s=[%s]' %(name, ','.join(['(%s)' %(FloatArr2Str(a)) for a in lst]))
		node.set(name, lst)
		return i

	def ReadFloat64Arr(self, node, offset, size, name):
		cnt0, i = getUInt32(node.data, offset)
		i = node.ReadUInt32A(i, 2, 'Float64Arr_' + name)

		lst = []
		l2 = []
		for j in range(cnt0):
			a1, i = getFloat64A(node.data, i, size)
			lst.append(a1)
			vec = FloatArr2Str(a1)
			l2.append('(%s)' %(vec))

		if (len(l2) > 0):
			node.content += ' {%s}' %(','.join(l2))
		node.set(name, lst)
		return i

	def ReadEdge(self, node, offset):
		n, i = getUInt16(node.data, offset)
		if (n != 0):
			i = offset
		t, i = getUInt32(node.data, i)

		if (t == 0x0203): t, i = getUInt32(node.data, i)

		if (t == 0x05): # Point: Center
			a, i = getFloat64A(node.data, i, 3)
			return PointEdge(a), i
		if (t == 0x0B): # 3D-Circle: Center, normal, m, radius, startAngle, sweepAngle
			a, i = getFloat64A(node.data, i, 12)
			return ArcOfCircleEdge(a), i
		if (t == 0x13): # ???: 		objects[02D3] = (10B3): 617931B4 flags=0200 index=0C1D pos=(-2.75,-2.22045e-16,-0.6)	aX=[t ffffff
			a, i = getFloat64A(node.data, i, 6)
			return LineEdge(a), i
		if (t == 0x11): # 3D-Ellipse: Center, dirMajor, dirMinor, rMajor, rMinor, startAngle, sweepAngle
			a, i = getFloat64A(node.data, i, 13)
			return ArcOfEllipseEdge(a), i
		if (t == 0x17): # 3D-Line: Point1, Point2
			a, i = getFloat64A(node.data, i, 6)
			return LineEdge(a), i
		if (t == 0x28): # ??? Bezier ???
			a, i = getUInt32A(node.data, i, 3)
			b = []
			for j in range(a[0]):
				c, i = getFloat64A(node.data, i, 3)
				b.append(c)
			return BezierEdge(a, b), i
		if (t == 0x2A): # 3D-BSpline
			a0 = Struct(u"<LLLd").unpack_from(node.data, i)
			i  += 20
			a1, i = readTypedFloatArr(node.data, i)
			a2, i = readTypedFloatArr(node.data, i)
			a3, i = readTypedFloatArr(node.data, i, 3)
			a4 = Struct(u"<dLLdd").unpack_from(node.data, i)
			i  += 32
			return BSplineEdge(a0, a1, a2, a3, a4), i
		raise AssertionError("Unknown array type %02X in (%04X): %s" %(t, node.index, node.typeName))

	def ReadEdgeList(self, node, offset):
		cnt, i = getUInt32(node.data, offset)
		lst    = []
		for j in range(cnt):
			edge, i = self.ReadEdge(node, i)
			lst.append(edge)
		node.content += ' edges=[%s]' %(','.join(['(%s)' %(e) for e in lst]))
		node.set('edges', lst)
		node.delete('tmp')
		return i

	def ReadTransformation2D(self, node, offset):
		'''
		Read the 2D transformation matrix
		'''
		val = Transformation2D()
		i = val.read(node.data, offset)
		node.set('transformation', val)
		node.content += u" transformation=%r" %(val)
		return i

	def ReadTransformation3D(self, node, offset, name='transformation'):
		'''
		Read the 3D transformation matrix
		'''
		val = Transformation3D()
		i = val.read(node.data, offset)
		node.set(name, val)
		node.content += u" %s=%r" %(name, val)
		return i

	def Read_5F9D0021(self, node): # SystemOfUnitsCollection
		i = node.Read_Header0('SystemOfUnitsCollection')
		i = node.ReadCrossRef(i, 'selected')
		i = node.ReadList3(i, _TYP_NODE_REF_, 'customUnitSystems')
		i = node.ReadList3(i, _TYP_NODE_REF_, 'predefinedUnitSystems')
		return i

	def ReadHeaderSysOfUnits(self, node, typeName):
		i = node.Read_Header0(typeName)
		i = node.ReadList3(i, _TYP_NODE_REF_, 'units')
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_5C30CE1D(self, node): # SystemOfUnitsMGS
		i = self.ReadHeaderSysOfUnits(node, 'SystemOfUnitsMGS')
		return i

	def Read_EBEE69CA(self, node): # SystemOfMeasureEnum
		i = self.ReadHeaderSysOfUnits(node, 'SystemOfUnitsCGS')
		return i

	def Read_EBEE69CB(self, node): # SystemOfMeasureEnum
		i = self.ReadHeaderSysOfUnits(node, 'SystemOfUnitsImperial')
		return i

	def Read_EBEE69D0(self, node): # SystemOfMeasureEnum
		i = self.ReadHeaderSysOfUnits(node, 'SystemOfUnitsCGS')
		return i

	def Read_5F9D0022(self, node): # UnitRef
		i = node.Read_Header0('UnitRef')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'magnitude')
		i = node.ReadFloat64(i, 'factor')
		i = self.skipBlockSize(i)
		node.set('Unit', '')
		node.set('UnitOffset', 0.0)
		node.set('UnitFactor', 1.0)
		node.set('UnitSupportet', True)
		return i

	def Read_Unit(self, node, abbreviation, unitName, offset, factor, supported = False):
		'''
		Reads the parameter's unit information
		TODO: Handle units not supported by FreeCAD
		List of SI units
		LENGTH:                    [1,0,0,0,0,0,0] 'm'
		MASS:                      [0,1,0,0,0,0,0] 'g'
		TIME:                      [0,0,1,0,0,0,0] 's'
		ELECTRIC CURRENT:          [0,0,0,1,0,0,0] 'A'
		THERMODYNAMIC TEMPERATURE: [0,0,0,0,1,0,0] 'K'
		AMOUNT OF SUBSTANCE:       [0,0,0,0,0,1,0] 'mol'
		LUMINOUS INTENSITY:        [0,0,0,0,0,0,1] 'cd'
		'''
		i = node.Read_Header0(u'Unit' + unitName)
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'magnitude')
		i = node.ReadFloat64(i, 'factor')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		node.set('Unit', abbreviation)
		if (sys.version_info.major < 3) and (not isinstance(abbreviation, unicode)):
			node.set('Unit', unicode(abbreviation))
		node.set('UnitOffset', offset)
		node.set('UnitFactor', factor)
		node.set('UnitSupportet', supported)
		return i

	###
	# The unit's symbol must match with the known unit symbols of FreeCAD!
	# Length (default 'cm'):
	def Read_624120BC(self, node): return self.Read_Unit(node, 'mm'       , 'MilliMeter'                , 0.0,      0.1    , True)
	def Read_F8A779F5(self, node): return self.Read_Unit(node, 'm'        , 'Meter'                     , 0.0,    100.0    , True)
	def Read_F8A779F6(self, node): return self.Read_Unit(node, 'in'       , 'Inch'                      , 0.0,      2.54   , True)
	def Read_F8A779F7(self, node): return self.Read_Unit(node, 'ft'       , 'Foot'                      , 0.0,     30.48   , True)
	def Read_5DFE5E70(self, node): return self.Read_Unit(node, 'mil'      , 'Mile'                      , 0.0,      0.00254, True)
	def Read_5C30CE17(self, node): return self.Read_Unit(node, 'sm'       , 'SeaMile'                   , 0.0, 185324.5218 , True)
	# Mass (default 'kg'):
	def Read_F8A779F1(self, node): return self.Read_Unit(node, 'g'        , 'Gram'                      , 0.0,  0.001      , True)
	def Read_F8A779F2(self, node): return self.Read_Unit(node, 'slug'     , 'Slug'                      , 0.0, 14.5939     , True)
	def Read_F8A779F3(self, node): return self.Read_Unit(node, 'lb'       , 'Pound'                     , 0.0,  0.428334865, True)
	def Read_5C30CE22(self, node): return self.Read_Unit(node, 'oz'       , 'Ounze'                     , 0.0,  0.028349525, True)
	# Time (default 's'):
	def Read_5F9D0025(self, node): return self.Read_Unit(node, 's'        , 'Second'                    , 0.0,    1.0      , True)
	def Read_5F9D0026(self, node): return self.Read_Unit(node, 'min'      , 'Minute'                    , 0.0,   60.0      , True)
	def Read_5F9D0027(self, node): return self.Read_Unit(node, 'h'        , 'Hour'                      , 0.0, 3600.0      , True)
	# Temperature (default 'K'):
	def Read_5F9D0029(self, node): return self.Read_Unit(node, 'K'        , 'Kelvin'                    ,   0.0 , 1.0      , True)
	def Read_5F9D002A(self, node): return self.Read_Unit(node, u'\xB0C'   , 'Celsius'                   , 273.15, 1.0      , True)
	def Read_5F9D002B(self, node): return self.Read_Unit(node, u'\xB0F'   , 'Fahrenheit'                , 459.67, 5.0/9    , True)
	# Angularity (default ''):
	def Read_5C30CDF2(self, node): return self.Read_Unit(node, 'rad'      , 'Radian'                    , 0.0, 1.0         , True)
	def Read_5C30CDF0(self, node): return self.Read_Unit(node, u'\xb0'    , 'Degree'                    , 0.0, pi/180.0    , True)
	def Read_3D0B9C8D(self, node): return self.Read_Unit(node, 'gon'      , 'Gradiant'                  , 0.0, pi/200.0    , True)
	def Read_5C30CDF6(self, node): return self.Read_Unit(node, u'\xb0'    , 'Grad'                      , 0.0, pi/180.0    , True)
	def Read_D7155C2A(self, node): return self.Read_Unit(node, 'sr'       , 'Steradian'                 , 0.0, 1.0)
	# Velocity (default 'cm/s'):
	def Read_4D4F962F(self, node): return self.Read_Unit(node, 'm/s'      , 'Meter/Second'              , 0.0, 100.0       , True)
	def Read_A116EF37(self, node): return self.Read_Unit(node, 'f/s'      , 'Feet/Second'               , 0.0,  30.48      , True)
	def Read_4D4F9631(self, node): return self.Read_Unit(node, 'mil/h'    , 'Miles/Hour'                , 0.0,  44.72399926, True)
	def Read_E18489FC(self, node): return self.Read_Unit(node, '1/min'    , 'Revolution/Minute'         , 0.0,  pi/30.0    , True)
	#Area:
	def Read_F0F5A577(self, node): return self.Read_Unit(node, 'circ.mil' , 'CircularMile'              , 0.0, 1/1973525004.0)     # not supported
	# Volume (default 'l'):
	def Read_40AFEBA9(self, node): return self.Read_Unit(node, 'gal'      , 'Galon'                     , 0.0, 1.0/264.1706)	   # not supported
	def Read_40AFEBAA(self, node): return self.Read_Unit(node, 'dm^3'     , 'Liter'                     , 0.0, 1.0         , True) # Workaround
	# Force (default 'N'):
	def Read_40AFEBA3(self, node): return self.Read_Unit(node, 'N'        , 'Newton'                    , 0.0, 1.0         , True)
	def Read_40AFEBA2(self, node): return self.Read_Unit(node, 'dyn'      , 'Dyn'                       , 0.0, 1.0)	               # not supported
	def Read_40AFEBA1(self, node): return self.Read_Unit(node, 'lbf'      , 'PoundForce'                , 0.0, 4.44822301540537, True)
	def Read_40AFEBA0(self, node): return self.Read_Unit(node, 'ozf'      , 'OunzeForce'                , 0.0, 0.278013851)	       # not supported
	# Pressure (default 'Pa'):
	def Read_23663C43(self, node): return self.Read_Unit(node, 'Pa'       , 'Pascal'                    , 0.0,       1.0   , True)
	def Read_40AFEBA5(self, node): return self.Read_Unit(node, 'psi'      , 'PoundForce/SquareInch'     , 0.0,    6890.0   , True)
	def Read_40AFEBA4(self, node): return self.Read_Unit(node, 'ksi'      , 'KiloPoundFource/SquareInch', 0.0, 6890000.0   , True)
	# Power (default 'W'):
	def Read_40AFEB9F(self, node): return self.Read_Unit(node, 'W'        , 'Watt'                      , 0.0,   1.0       , True)
	def Read_40AFEB9E(self, node): return self.Read_Unit(node, 'hp'       , 'HorsePower'                , 0.0, 745.7)	           # not supported
	# Work (default 'J'):
	def Read_40AFEB9D(self, node): return self.Read_Unit(node, 'J'        , 'Joule'                     , 0.0,    1.0      , True)
	def Read_40AFEB9C(self, node): return self.Read_Unit(node, 'erg'      , 'Erg'                       , 0.0,    1.0)	           # not supported
	def Read_40AFEB9B(self, node): return self.Read_Unit(node, 'Cal'      , 'Calories'                  , 0.0,    4.184)	       # not supported
	def Read_40AFEB9A(self, node): return self.Read_Unit(node, 'BTU'      , 'BritishThermalUnit'        , 0.0, 1054.6)	           # not supported
	# Electrical (default depends):
	def Read_CEA6CA2D(self, node): return self.Read_Unit(node, 'A'        , 'Ampere'                    , 0.0, 1.0         , True)
	def Read_9E5A8E15(self, node): return self.Read_Unit(node, 'V'        , 'Volt'                      , 0.0, 1.0)                # not supported
	def Read_BD378B6A(self, node): return self.Read_Unit(node, 'ohm'      , 'Ohm'                       , 0.0, 1.0)                # not supported
	def Read_E7A9656E(self, node): return self.Read_Unit(node, 'C'        , 'Coulomb'                   , 0.0, 1.0)                # not supported
	def Read_28FEBA33(self, node): return self.Read_Unit(node, 'F'        , 'Farad'                     , 0.0, 1.0)                # not supported
	def Read_45BD8053(self, node): return self.Read_Unit(node, 'y'        , 'Gamma'                     , 0.0, 1.0e-9)             # not supported
	def Read_5F9F2379(self, node): return self.Read_Unit(node, 'Gs'       , 'Gauss'                     , 0.0, 0.0001)             # not supported
	def Read_DA430213(self, node): return self.Read_Unit(node, 'H'        , 'Henry'                     , 0.0, 1.0)                # not supported
	def Read_11EB21E7(self, node): return self.Read_Unit(node, 'Hz'       , 'Hertz'                     , 0.0, 1.0)                # not supported
	def Read_26072ECF(self, node): return self.Read_Unit(node, 'maxwell'  , 'Maxwell'                   , 0.0, 1.0e-8)             # not supported
	def Read_7D8BC1F7(self, node): return self.Read_Unit(node, 'mho'      , 'Mho'                       , 0.0, 1.0)                # not supported
	def Read_9E064B0C(self, node): return self.Read_Unit(node, 'Oe'       , 'Oersted'                   , 0.0, 79.577472)          # not supported
	def Read_3D793814(self, node): return self.Read_Unit(node, 'S'        , 'Siemens'                   , 0.0, 1.0)                # not supported
	def Read_FB4E31FB(self, node): return self.Read_Unit(node, 'T'        , 'Tesla'                     , 0.0, 1.0)                # not supported
	def Read_660F65B6(self, node): return self.Read_Unit(node, 'Wb'       , 'Weber'                     , 0.0, 1.0)                # not supported
	# Luminosity (default 'cd'):
	def Read_B7A5131F(self, node): return self.Read_Unit(node, 'lx'       , 'Lux'                       , 0.0, 1.0)                # not supported
	def Read_E9D0671D(self, node): return self.Read_Unit(node, 'lm'       , 'Lumen'                     , 0.0, 1.0)                # not supported
	def Read_F94FEEE2(self, node): return self.Read_Unit(node, 'cd'       , 'Candela'                   , 0.0, 1.0         , True)
	# Substance (default 'mol'):
	def Read_2F6A0C3F(self, node): return self.Read_Unit(node, 'mol'      , 'Mol'                       , 0.0, 1.0         , True)
	# without Unit:
	def Read_5F9D0023(self, node): return self.Read_Unit(node, ''         , 'Empty'                     , 0.0, 1.0         , True)

	def Read_791C333D(self, node): return self.Read_Unit(node, 'XXX',     'User'                        , 0.0, 0.0) # not supported -> Tuner.iam?

	def HandleBlock(self, node):
		i = 0
		try:
			readType = getattr(self, 'Read_%s' %(node.typeName))
			i = readType(node)
		except AttributeError:
			if (self.__class__.__name__ != 'SegmentReader'):
				logError(u"ERROR> %s.py missing 'def Read_%s(self, node)'!", self.__module__, node.typeName)
				setattr(self.__class__, 'Read_%s' %(node.typeName), Read_Dummy)
		except:
			logError(traceback.format_exc())

		try:
			node.data = node.data[i:]
			if (len(node.data) > 0):
				if (sys.version_info.major < 3):
					s = " ".join(["%02X" % ord(c) for c in node.data])
				else:
					s = " ".join(["%02X" % c for c in node.data])
				node.content += u"\taX=[%s]" %(s)
		except:
			logError(u"ERROR in %s.Read_%s: %s", self.__module____name__, node.typeName, traceback.format_exc())

		return

	def ReadBlock(self, data, offset, size):
		self.nodeCounter += 1
		node = SecNode()
		node.index = self.nodeCounter
		node.size  = size
		node.offset = offset
		node.reader = self
		node.segment = self.segment
		self.segment.elementNodes[node.index] = node
		# set node's data
		n, i = getUInt32(data, node.offset)
		node.uid = getNodeUID((n & 0xFF), self.segment)
		node.typeName = '%08X' % (node.uid.time_low)
		node.data = data[i:i + node.size]
		self.HandleBlock(node)
		return node

	def skipBlockSize(self, offset, l = 1):
		return offset + l * importerUtils._block_size

	def ReadRefU32AList(self, node, offset, name, size, type):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref, i = self.ReadNodeRef(node, i, j, type, name)
			ref.number, i = getUInt32A(node.data, i, size)
			lst.append(ref)
		node.set(name, lst)
		return i

	def ReadRefU32List(self, node, offset, name, lType=REF_CHILD):
		cnt, i = getUInt32(node.data, offset)
		lst = []
		for j in range(cnt):
			ref, i = self.ReadNodeRef(node, i, None, lType, name)
			ref.number, i = getUInt32(node.data, i)
			lst.append(ref)
		node.set(name, lst)
		return i

	def Read_F645595C(self, node):
		# Spatial's (A)CIS (S)olid (M)odeling
		i = node.Read_Header0('ASM')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'schema')
		if (getFileVersion() > 2010):
			if (i == len(node.data)): return i
		else:
			if (i + 4 == len(node.data)): return i + 4
		txt, ignore = getText8(node.data, i, 15) # 'ACIS BinaryFile' or from 20214 on 'ASM BinaryFile4'
		node.content += " fmt='%s'" %(txt)
		node.set('fmt', txt)
		e = len(node.data) - 17
		vers = getFileVersion()
		if (vers > 2018): e -=1
		if (vers < 2011): e -=8

		stream = io.BytesIO(node.data[i:e])
		reader = AcisReader(stream)
		reader.name = "%04X" %(node.index)
		if (reader.readBinary()):
			i = e
			node.set('SAT', reader)
			resolveEntityReferences(node)
			node.set('nameMatches', getNameMatchAttributes())
			node.set('dcAttributes', getDcAttributes())
			self.segment.AcisList.append(node)
			i = self.skipBlockSize(i)
			i = node.ReadUInt32(i, 'selectedKey')
			i += 1 # skip 00
			i = node.ReadSInt32(i, 'delta_state') # active delta-state
			i = self.skipBlockSize(i)
			if (getFileVersion() > 2018): i += 1 # skip 00
			i = node.ReadChildRef(i, 'history')
			i += 4 # skip FF FF FF FF
			if (self.segment.acis is None):
				self.segment.acis = node
		return i

	def Read_F8A779F8(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadUInt16A(i, 2, 'a1')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadUInt16A(i, 9, 'a2')
		i = node.ReadUInt8(i, 'u8_2')
		if (getFileVersion() > 2017):
			i = node.ReadUInt16A(i, 3, 'a3')
		else:
			node.content += u" a3=[000,000,000]"
			node.set('a3', [0,0,0])
		return i

	def Read_F8A779FD(self, node): # Unit
		i = node.Read_Header0('Unit')
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, _TYP_NODE_REF_, 'numerators')
		i = node.ReadList3(i, _TYP_NODE_REF_, 'denominators')
		i = node.ReadBoolean(i, 'visible')
		i = node.ReadChildRef(i, 'derived')
		return i

	def ReadTrailer(self, buffer, offset):
		i = offset
		if (getFileVersion() > 2014):
			trailing, i = getBoolean(buffer, i)
			if (trailing):
				n, i = getUInt32(buffer, i)
				txt = []
				if ((n & 0x80000000) > 0):
					pass # check Sec-Ref???
				else:
					for j in range(n):
						k, i = getLen32Text8(buffer, i)
						u32_1, i = getUInt32(buffer, i)
						if (u32_1   == 0b0001):
							v, i = getUInt8A(buffer, i, 3)
						elif (u32_1 == 0b0011):
							v, i = getUInt16A(buffer, i, 2)
						elif (u32_1 == 0b0111):
							v, i = getUInt16A(buffer, i, 2)
						elif (u32_1 == 0b1000):
							v, i = getUInt16A(buffer, i, 3)
						elif (u32_1 == 0b1010):
							v, i = getUInt16A(buffer, i, 3)
						elif (u32_1 == 0b1011):
							v, i = getUInt16A(buffer, i, 5)
						elif (u32_1 == 0b1110):
							typ, i = getUInt16(buffer, i)
							cnt, i = getUInt32(buffer, i)
							dat, i = getUInt8A(buffer, i, cnt)
							v = (typ, dat)
						else:
							raise ValueError(u"Unknown property value type 0x%02X in '%s'!" %(u32_1, getInventorFile()))
						txt.append((k,v))
					i = CheckList(buffer, i, 0x0006)
					cnt, i = getUInt32(buffer, i)
					if (cnt > 0):
						arr32, i = getUInt32A(buffer, i, 2)
						values = []
						for j in range(cnt):
							txt, i = getLen32Text8(buffer, i)
							m, i = getUInt32(buffer, i)
							ref = SecNodeRef(m, REF_CROSS, txt)
							values.append(ref)
		return i

	def ReadSegmentData(self, file, buffer):
		self.nodeCounter = 0
		self.segment.elementNodes = {}
		self.segment.indexNodes   = {}

		i = 0

		for sec in self.segment.sec1:
			if (sec.flags == 1):
				start = i
				data = self.ReadBlock(buffer, i, sec.length)
				i += data.size + 4
				l, i = getUInt32(buffer, i)
				i = self.ReadTrailer(buffer, i)
				if ((l != 0) and (sec.length != l)):
					logError('%s: BLOCK[%04X] - incorrect block size %X != 	%X found for offset %X for %s!' %(self.__class__.__name__, data.index, l, u32_0, start, data.typeName))

		self.segment.tree = buildTree(file, self.segment.elementNodes)
		self.postRead()

		return
