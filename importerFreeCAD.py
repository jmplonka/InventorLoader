# -*- coding: utf-8 -*-

'''
importerFreeCAD.py
'''
import sys, FreeCAD, Draft, Part, Sketcher, traceback, Mesh, InventorViewProviders, importerSAT, Acis, re

from importerClasses import *
from importerUtils   import *
from importerSegNode import SecNode, SecNodeRef, setParameter
from math            import sqrt, tan, degrees, pi
from FreeCAD         import Vector as VEC, Rotation as ROT, Placement as PLC, Version, ParamGet

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

BIT_GEO_ALIGN_HORIZONTAL    = 1 <<  0
BIT_GEO_ALIGN_VERTICAL      = 1 <<  1
BIT_GEO_BEND                = 1 <<  2
BIT_GEO_COINCIDENT          = 1 <<  3
BIT_GEO_EQUAL               = 1 <<  4
BIT_GEO_FIX                 = 1 <<  5 # not supported
BIT_GEO_HORIZONTAL          = 1 <<  6
BIT_GEO_VERTICAL            = 1 <<  7
BIT_GEO_OFFSET              = 1 <<  8 # not supported
BIT_GEO_PARALLEL            = 1 <<  9
BIT_GEO_TANGENTIAL          = 1 << 10
BIT_GEO_PERPENDICULAR       = 1 << 11
BIT_GEO_POLYGON             = 1 << 12
BIT_GEO_RADIUS              = 1 << 13
BIT_GEO_SPLINEFITPOINT      = 1 << 14 # not supported
BIT_GEO_SYMMETRY_LINE       = 1 << 15
BIT_GEO_SYMMETRY_POINT      = 1 << 16 # not supported
BIT_DIM_ANGLE_2_LINE        = 1 << 17
BIT_DIM_ANGLE_3_POINT       = 1 << 18 # Workaround required: 2 construction lines
BIT_DIM_RADIUS              = 1 << 19
BIT_DIM_DIAMETER            = 1 << 20 # Workaround required: radius constraint
BIT_DIM_DISTANCE            = 1 << 21
BIT_DIM_OFFSET_SPLINE       = 1 << 22 # not supported

CENTER = VEC(0.0, 0.0, 0.0)
DIR_X  = VEC(1.0, 0.0, 0.0)
DIR_Y  = VEC(0.0, 1.0, 0.0)
DIR_Z  = VEC(0.0, 0.0, 1.0)

IS_CELL_REF = re.compile('^[a-z](\d+)?$', re.IGNORECASE)

# x 10                      2   2   1   1   0   0   0
# x  1                      4   0   6   2   8   4   0
#SKIP_CONSTRAINTS_DEFAULT = 0b11111111111111111111111
#SKIP_CONSTRAINTS_DEFAULT = 0b00000000000000000001000 # Only geometric coincidens
SKIP_CONSTRAINTS_DEFAULT  = 0b00110000001111011011111 # default values: no workarounds, nor unsupported constraints!
SKIP_CONSTRAINTS = SKIP_CONSTRAINTS_DEFAULT # will be updated by stored preferences!
PART_LINE = Part.Line
if (hasattr(Part, "LineSegment")):
	PART_LINE = Part.LineSegment

IMPLEMENTED_COMPONENTS = [
	u"Sketch2D",
	u"Sketch3D",
	u"SketchBlock",
	u"Feature",
	u"MeshFolder",
	u"iPart",
	u"Blocks",
]

def _enableConstraint(name, bit, preset):
	global SKIP_CONSTRAINTS
	SKIP_CONSTRAINTS &= ~bit        # clear the bit if already set.
	enable = ParamGet("User parameter:BaseApp/Preferences/Mod/InventorLoader").GetBool(name, preset)
	if (enable):
		SKIP_CONSTRAINTS |= bit # now set the bit if desired.
	ParamGet("User parameter:BaseApp/Preferences/Mod/InventorLoader").SetBool(name, enable)
	return

def getCoord(point, coordName):
	if (point is None): return 0.0
	c = point.get(coordName)
	if (c is None): return 0.0
	return c * 10.0

def getX(point):
	return getCoord(point, 'x')

def getY(point):
	return getCoord(point, 'y')

def getZ(point):
	return getCoord(point, 'z')

def p2v(p, x='x', y='y', z='z'):
	return VEC(getCoord(p, x), getCoord(p, y), getCoord(p, z))

def createConstructionPoint(sketchObj, point):
	part = Part.Point(p2v(point))
	addSketch2D(sketchObj, part, True, point)
	return point.sketchIndex

def createLine(p1, p2):
	return PART_LINE(p1, p2)

def createCircle(c, n, r):
	return Part.Circle(p2v(c), VEC(n), r)

def createArc(p1, p2, p3):
	return Part.ArcOfCircle(p2v(p1), p2v(p2), p2v(p3))

def _initPreferences():
	_enableConstraint('Sketch.Constraint.Geometric.AlignHorizontal', BIT_GEO_ALIGN_HORIZONTAL , True)
	_enableConstraint('Sketch.Constraint.Geometric.AlignVertical',   BIT_GEO_ALIGN_VERTICAL   , True)
	_enableConstraint('Sketch.Constraint.Geometric.Bend',            BIT_GEO_BEND             , True)
	_enableConstraint('Sketch.Constraint.Geometric.Coincident',      BIT_GEO_COINCIDENT       , True)
	_enableConstraint('Sketch.Constraint.Geometric.Equal',           BIT_GEO_EQUAL            , True)
	_enableConstraint('Sketch.Constraint.Geometric.Fix',             BIT_GEO_FIX              , False)
	_enableConstraint('Sketch.Constraint.Geometric.Horizontal',      BIT_GEO_HORIZONTAL       , True)
	_enableConstraint('Sketch.Constraint.Geometric.Offset',          BIT_GEO_OFFSET           , False)
	_enableConstraint('Sketch.Constraint.Geometric.Parallel',        BIT_GEO_PARALLEL         , True)
	_enableConstraint('Sketch.Constraint.Geometric.Perpendicular',   BIT_GEO_PERPENDICULAR    , True)
	_enableConstraint('Sketch.Constraint.Geometric.Polygon',         BIT_GEO_POLYGON          , True)
	_enableConstraint('Sketch.Constraint.Geometric.Radius',          BIT_GEO_RADIUS           , True)
	_enableConstraint('Sketch.Constraint.Geometric.SplineFitPoint',  BIT_GEO_SPLINEFITPOINT   , False)
	_enableConstraint('Sketch.Constraint.Geometric.SymmetryLine',    BIT_GEO_SYMMETRY_LINE    , False)
	_enableConstraint('Sketch.Constraint.Geometric.SymmetryPoint',   BIT_GEO_SYMMETRY_POINT   , False)
	_enableConstraint('Sketch.Constraint.Geometric.Tangential',      BIT_GEO_TANGENTIAL       , True)
	_enableConstraint('Sketch.Constraint.Geometric.Vertical',        BIT_GEO_VERTICAL         , True)
	_enableConstraint('Sketch.Constraint.Dimension.Angle2Line',      BIT_DIM_ANGLE_2_LINE     , True)
	_enableConstraint('Sketch.Constraint.Dimension.Angle3Point',     BIT_DIM_ANGLE_3_POINT    , False)
	_enableConstraint('Sketch.Constraint.Dimension.Radius',          BIT_DIM_RADIUS           , True)
	_enableConstraint('Sketch.Constraint.Dimension.Diameter',        BIT_DIM_DIAMETER         , True)
	_enableConstraint('Sketch.Constraint.Dimension.Distance',        BIT_DIM_DISTANCE         , True)
	_enableConstraint('Sketch.Constraint.Dimension.OffsetSpline',    BIT_DIM_OFFSET_SPLINE    , False)

def ignoreBranch(node):
	return None

def unsupportedNode(node):
	if (node.typeName == 'Feature'):
		logWarning(u"        ... %s '%s' not supported (yet?) - please use SAT or STEP instead!", node.typeName, node.getSubTypeName())
	else:
		logWarning(u"        ... %s not supported (yet?) - please use SAT or STEP instead!", node.typeName)
	node.setGeometry(None)
	return None

def notYetImplemented(node):
	if (node.typeName == 'Feature'):
		logWarning(u"        ... %s '%s' not implemented yet - please use SAT or STEP instead!", node.typeName, node.getSubTypeName())
	else:
		logWarning(u"        ... %s not implemented yet - please use SAT or STEP instead!", node.typeName)
	node.setGeometry(None)
	return None

def newObject(className, name):
	obj = FreeCAD.ActiveDocument.addObject(className, InventorViewProviders.getObjectName(name))
	if (obj is not None):
		obj.Label = name
	return obj

def createGroup(name):
	return newObject('App::DocumentObjectGroup', name)

def isConstructionMode(node):
	if (node):
		flags2 = node.get('flags2')
		if (flags2 is None):
			logError(u"FATAL> (%04X): %s has no flags2 parameter!", node.index, node.typeName)
		else:
			if ((flags2 & 0x04080040) > 0): return True # 0x40 => This is a Reference!!!
	return False

def isOrigo2D(vec2D):
	return vec2D == (0,0)

def getDistancePointPoint(p, q):
	return p2v(p).distanceToPoint(p2v(q))

def getDistanceLinePoint(line, point):
	return p2v(point).distanceToLine(p2v(line.get('points')[0]), p2v(line.get('points')[1]))

def getDistanceCircleLine(circle, line):
	point    = circle.get('center')
	distance = getDistanceLinePoint(line, point)
	return distance - getCoord(circle, 'r')

def getDistanceCirclePoint(circle, point):
	center   = circle.get('center')
	distance = getDistancePointPoint(center, point)
	return distance - getCoord(circle, 'r')

def getDistanceCircleCircle(circle1, circle2):
	center    = circle2.get('center')
	distance = getDistanceCirclePoint(circle1, center)
	return distance - getCoord(circle2, 'r')

def getLengthPoints(entity1, entity2):
	type1 = entity1.typeName
	type2 = entity2.typeName

	if (type1 == 'Point2D'):
		if (type2 == 'Point2D'):  return getDistancePointPoint(entity1, entity2)
		if (type2 == 'Line2D'):   return getDistanceLinePoint(entity2, entity1)
		if (type2 == 'Circle2D'): return getDistanceCirclePoint(entity2, entity1)
	if (type1 == 'Line2D'):
		if (type2 == 'Point2D'):  return getDistanceLinePoint(entity1, entity2)
		if (type2 == 'Line2D'):   return getDistanceLinePoint(entity1, entity2.get('points')[0]) # Hope that the lines are parallel!
		if (type2 == 'Circle2D'): return getDistanceCircleLine(entity2, entity1)
	if (type1 == 'Circle2D'):
		if (type2 == 'Point2D'):  return getDistanceCirclePoint(entity1, entity2)
		if (type2 == 'Line2D'):   return getDistanceCircleLine(entity1, entity2) # Hope that the lines are parallel!
		if (type2 == 'Circle2D'): return getDistanceCircleCircle(entity1, entity2)
	raise BaseException("Don't know how to determine the distance between '%s' and '%s'!" %(entity1.node.getRefText(), entity2.node.getRefText()))

def getLengthLine(line):
	point1 = line.get('points')[0]
	point2 = line.get('points')[1]
	return getLengthPoints(point1, point2)

def isSamePoint(point1, point2):
	if (point1 is None): return point2 is None
	if (point2 is None): return False
	return isEqual(p2v(point1), p2v(point2))

def getCoincidentPos(sketchObj, point, entity):
	if (entity.sketchIndex is None): return -1
	entityType = entity.typeName
	if (entityType == 'Point2D'): return 1
	if (isSamePoint(point, entity.get('points')[0])): return 1
	if (isSamePoint(point, entity.get('points')[1])): return 2
	if (isSamePoint(point, entity.get('center'))): return 3
	if (sketchObj.isPointOnCurve(entity.sketchIndex, getX(point), getY(point))): return None
	return -1

def addSketch2D(sketchObj, geometry, mode, entityNode):
	geometry.Construction = mode
	index = sketchObj.addGeometry(geometry, mode)
	newGeo = sketchObj.Geometry[index]
	entityNode.setGeometry(newGeo, index)
	return newGeo

def addSketch3D(sketchObj, geometry, mode, entityNode):
#	geometry.Construction = mode
	index = sketchObj.addGeometry(geometry, mode)
	newGeo = sketchObj.Geometry[index]
	entityNode.setGeometry(geometry, index)
	return geometry

def addEqualRadius2d(sketchObj, arc1, arc2):
	if (arc1 is not None):
		constraint = Sketcher.Constraint('Equal', arc1, arc2)
		sketchObj.addConstraint(constraint)
	return

def getProperty(properties, index):
	try:
		return properties[index]
	except:
		return None

def getPropertyValue(properties, index, name):
	property = getProperty(properties, index)
	try:
		return property.get(name)
	except:
		return None

def getDimension(node, varName):
	dimension  = node.get(varName)

	if (dimension.typeName == 'Line2D'):
		dimension = DimensionValue(Length(getLengthLine(dimension)))
	elif (dimension.typeName == 'Point2D'):
		dimension = DimensionValue(Length(0))

	if (dimension.typeName != 'Parameter'):
		logError(u"Expected Dimension for (%04X): %s - NOT %s", node.index, node.typeName, dimension.typeName)

	return dimension

def getNextLineIndex(coincidens, startIndex):
	i = startIndex
	try:
		ref = coincidens[i]
		if (ref.typeName == 'Line2D'):
			return i
		return getNextLineIndex(coincidens, i + 1)
	except:
		return len(coincidens)

def getPlacement(node):
	transformation = node.get('transformation')
	matrix4x4      = transformation.getMatrix()

	# convert centimeter to millimeter
	matrix4x4.A14  *= 10.0
	matrix4x4.A24  *= 10.0
	matrix4x4.A34  *= 10.0

	return PLC(matrix4x4)

def getFirstBodyName(ref):
	try:
		bodies = ref.get('bodies')
		return bodies[0].name
	except:
		return ref.name

def getNominalValue(node):
	if (node):
		value = node.get('valueNominal')
		if (value): return value
	return 0.0

def getDirection(node, name, distance):
	dir = node.get(name)
	if (dir == 0): return 0.0
	return distance * dir/abs(dir)

def getCountDir(length, count, direction, fitted):
	if (length is None):    return 1, CENTER
	if (count is None):     return 1, CENTER
	if (direction is None): return 1, CENTER

	distance = getMM(length)

	if (direction.typeName == 'D2D440C0'):
		logWarning(u"    ... don't know how to apply pattern along curve - ignored!")
		# have to calculate the normal vector for each point of the curve!
		return 1, CENTER # 1: no pattern copy!
	if (direction.typeName not in ['Direction', 'A244457B', 'A5977BAA']):
		logWarning(u"    ... don't know how to get direction from (%04X) %s (pattern along curves are not supported) - ignoring pattern!", direction.index, direction.typeName)
		return 1, CENTER # 1 means: no pattern copy.

	x = getDirection(direction, 'dirX', distance)
	y = getDirection(direction, 'dirY', distance)
	z = getDirection(direction, 'dirZ', distance)

	cnt = getNominalValue(count)
	if (isTrue(fitted) and (cnt > 1)):
		x = x / (cnt - 1)
		y = y / (cnt - 1)
		z = z / (cnt - 1)

	return cnt, VEC(x, y, z)

def setDefaultViewObjectValues(geo):
	if (geo  is None): return
	geo.ViewObject.AngularDeflection = 28.5                    # double
	geo.ViewObject.BoundingBox       = False                   # bool
	geo.ViewObject.Deviation         = 0.5                     # double
	geo.ViewObject.DisplayMode       = 0                       # enum {0: u"Flat Lines", 1: u"Shaded", 2: u"Wireframe", 3: u"Points"}
	geo.ViewObject.DrawStyle         = 0                       # enum {0: u"Solid", 1: u"Dahed", 2: u"Dotted", 3: u"Dashdot"}
	geo.ViewObject.Lighting          = 1                       # enum {0: u"One side", 1: u"Two side"}
	geo.ViewObject.LineColor         = (0.1, 0.1, 0.1, 0.0)    # double[4]
	geo.ViewObject.LineWidth         = 1.0                     # double
	geo.ViewObject.PointColor        = (0.1, 0.1, 0.1, 0.0)    # double[4]
	geo.ViewObject.PointSize         = 2.0                     # double
	geo.ViewObject.Selectable        = True                    # bool
	geo.ViewObject.SelectionStyle    = 0                       # enum {0: u"Shape", 1: u"BoundBox"}
	geo.ViewObject.ShapeColor        = (0.75, 0.75, 0.75, 0.0) # double[4]
	geo.ViewObject.Transparency      = 0                       # int 0..100
	geo.ViewObject.Visibility        = True                    # bool

def adjustViewObject(newGeo, baseGeo):
	if (newGeo  is None): return
	if (baseGeo is None): return
	newGeo.ViewObject.DisplayMode  = baseGeo.ViewObject.DisplayMode
	newGeo.ViewObject.DrawStyle    = baseGeo.ViewObject.DrawStyle
	newGeo.ViewObject.Lighting     = baseGeo.ViewObject.Lighting
	newGeo.ViewObject.LineColor    = baseGeo.ViewObject.LineColor
	newGeo.ViewObject.LineWidth    = baseGeo.ViewObject.LineWidth
	newGeo.ViewObject.PointColor   = baseGeo.ViewObject.PointColor
	newGeo.ViewObject.PointSize    = baseGeo.ViewObject.PointSize
	newGeo.ViewObject.ShapeColor   = baseGeo.ViewObject.ShapeColor
	newGeo.ViewObject.Transparency = baseGeo.ViewObject.Transparency

def getMM(length):
	if (length is None): return 0.0
	if (type(length) == float): return length
	if (isinstance(length, AbstractValue)):
		val = length
	else:
		val = length.getValue()
	if (isinstance(val, Length)): return val.getMM()
	if (isinstance(val, Scalar)): return val.x * 10
	return val * 10.0

def getGRAD(angle):
	if (angle is None): return 0.0
	if (type(angle) == float): return angle
	if (isinstance(angle, AbstractValue)):
		val = angle
	else:
		val = angle.getValue()
	if (isinstance(val, Angle)): return val.getGRAD()
	if (isinstance(val, Scalar)): return val.x
	return val

def getRAD(angle):
	if (angle is None): return 0.0
	if (type(angle) == float): return angle
	if (isinstance(angle, AbstractValue)):
		val = angle
	else:
		val = angle.getValue()
	if (isinstance(val, Angle)): return val.getRAD()
	if (isinstance(val, Scalar)): return val.x
	return val

def isTrue(param):
	if (param is None): return False
	return param.get('value')

def setPlacement(geo, placement, base):
	geo.Placement = placement
	if (base is not None): geo.Placement.Base = base
	return

def replaceGeometry(sketchObj, node, geo):
	node.data.geometry = geo
	sketchObj.Geometry[node.sketchIndex] = geo
	return geo

def replacePoint(sketchObj, pOld, line, pNew):
	l = line.geometry
	if (l is None): return None
	if (isEqual(p2v(pOld), l.StartPoint)):
		return replaceGeometry(sketchObj, line, createLine(p2v(pNew), l.EndPoint))
	return replaceGeometry(sketchObj, line, createLine(l.StartPoint, p2v(pNew)))

def setAssociatedSketchEntity(sketchNode, node, ai, entityType):
	if (not ai in sketchNode.data.associativeIDs):
		idMap = {}
		sketchNode.data.associativeIDs[ai] = idMap
	idMap = sketchNode.data.associativeIDs[ai]
	idMap[entityType] = node

def getAssociatedSketchEntity(sketchNode, ai, entityType):
	if (not ai in sketchNode.data.associativeIDs):
		return None
	idMap = sketchNode.data.associativeIDs[ai]
	return idMap.get(entityType, None)

def getBodyColor(bodyNode):
	attributes = bodyNode.get('attrs')
	for attribute in attributes.get('attributes'):
		if (attribute.typeName == 'AttrPartDraw'):
			return attribute.get('c0')
	return None

def adjustColor(entity, color):
	if (color is not None):
		if (type(entity) is list):
			for child in entity:
				adjustColor(child, color)
		else:
			entity.ViewObject.ShapeColor = color.getRGB()
	return

def adjustFxColor(entity, nodColor):
	if (entity is not None):
		if nodColor is not None:
			color = getColor(nodColor.name)
			if (color is not None):
				if (type(entity) is list):
					for child in entity:
						child.ViewObject.ShapeColor = color
				else:
					entity.ViewObject.ShapeColor = color
	return

def __hide__(geo):
	if (geo is not None):
		geo.ViewObject.Visibility = False
	return

def hide(geos):
	if (type(geos) == list):
		for geo in geos:
			__hide__(geo)
	else:
		__hide__(geos)
	return

def resolveNameTableItem(item, vk):
	if (hasattr(vk, 'entry') and (vk.entry is None)):
		nt  = item.segment.elementNodes.get(vk.nameTable)
		if (nt is not None):
			vk.entry = nt.get('entries')[vk.key]
		return vk.entry
	return None

def getNameTableEntry(node):
	ntEntry = node.get('ntEntry')
	if (ntEntry.entry is None):
		entry = resolveNameTableItem(node, ntEntry)
		resolveNameTableItem(node, entry.get('from'))
		resolveNameTableItem(node, entry.get('to'))
		resolveNameTableItem(node, entry.get('edge'))
		lst2 = entry.get('lst2')
		for i, vk in enumerate(lst2):
			resolveNameTableItem(node, vk)
	return ntEntry.entry

def checkPoints(fcEdge, acisPoints):
	pt1 = fcEdge.firstVertex().Point
	pt2 = fcEdge.lastVertex().Point
	for pt in acisPoints:
		if (not isEqual(pt, pt1)) and (not isEqual(pt, pt2)):
			return False
	return True

def checkCircles(fcCurve, acisCurve):
	if (not isEqual1D(fcCurve.Radius, acisCurve.major.Length)): return False
	if (not (isEqual(fcCurve.Axis, acisCurve.normal) or isEqual(fcCurve.Axis, acisCurve.normal.negative()))): return False
	if (not isEqual(fcCurve.Center, acisCurve.center)): return False
	return True

def checkEllipses(fcCurve, acisCurve):
	if (not isEqual1D(fcCurve.MajorRadius, acisCurve.major.Length)): return False
	if (not isEqual1D(fcCurve.MinorRadius, acisCurve.major.Length * acisCurve.ratio)): return False
	if (not (isEqual(fcCurve.Axis, acisCurve.normal) or isEqual(fcCurve.Axis, acisCurve.normal.negative()))): return False
	if (not isEqual(fcCurve.Center, acisCurve.center)): return False
	return True

def checkSplines(fcCurve, acisCurve):
	# TODO
	return False

def checkProjectedCurves(fcCurve, acisCurve):
	# TODO
	return False

def checkComposedCurves(fcCurve, acisCurve):
	# TODO
	return False

def checkDegenerateCurves(fcCurve, acisCurve):
	# TODO
	return False

def checkDegenerateCurves(fcCurve, acisCurve):
	# TODO
	return False

def isEqualCurve(fcEdge, acisEdge):
	c = fcEdge.Curve
	acisPoints = acisEdge.getPoints()
	if (not checkPoints(fcEdge, acisPoints)): return False
	acisCurve = acisEdge.getCurve()
	cn = c.__class__.__name__
	if (isinstance(acisCurve, Acis.CurveStraight)):
		return (cn in ['Line', 'LineSegment'])
	if (isinstance(acisCurve, Acis.CurveEllipse)):
		if (isEqual1D(acisCurve.ratio, 1)):
			if (cn in ['Circle', 'Arc', 'ArcOfCircle']):
				return (checkCircles(fcEdge.Curve, acisCurve))
		else:
			if (cn in ['Ellipse', 'ArcOfEllipse', 'ArcOfConic']):
				return (checkEllipses(fcEdge.Curve, acisCurve))
	elif (isinstance(acisCurve, Acis.CurveInt)):
		if (cn in []):
			return (checkSplines(fcEdge.Curve, acisCurve))
	elif (isinstance(acisCurve, Acis.CurveP)):
		if (cn in []):
			return (checkProjectedCurves(fcEdge.Curve, acisCurve))
	elif (isinstance(acisCurve, Acis.CurveComp)):
		if (cn in []):
			return (checkComposedCurves(fcEdge.Curve, acisCurve))
	elif (isinstance(acisCurve, Acis.CurveDegenerate)):
		if (cn in []):
			return (checkDegenerateCurves(fcEdge.Curve, acisCurve))
	return False

def findFcEdgeIndex(fcShape, acisEdges):
	for idx, fcEdge in enumerate(fcShape.Edges):
		if (not fcEdge.Degenerated):
			for acisEdge in acisEdges:
				if (isEqualCurve(fcEdge, acisEdge)):
					return idx

	return None

class FreeCADImporter(object):
	FX_EXTRUDE_NEW          = 0x0001
	FX_EXTRUDE_CUT          = 0x0002
	FX_EXTRUDE_JOIN         = 0x0003
	FX_EXTRUDE_INTERSECTION = 0x0004
	FX_EXTRUDE_SURFACE      = 0x0005

	FX_HOLE_DRILLED         = 0x0000
	FX_HOLE_SINK            = 0x0001
	FX_HOLE_BORED           = 0x0002
	FX_HOLE_SPOT            = 0x0003

	def __init__(self):
		self.root           = None
		self.mapConstraints = None
		self.pointDataDict  = None
		self.bodyNodes      = {}
		#_initPreferences()
		# override user selected Constraints!
		SKIP_CONSTRAINTS = SKIP_CONSTRAINTS_DEFAULT

	def getGeometry(self, node):
		if (node):
			try:
				if (not isinstance(node, DataNode)): node = node.node
				if (node.handled == False):
					node.handled = True
					if (node.valid):
						importObject = getattr(self, 'Create_%s' %(node.typeName))
						importObject(node)

						# apply colors stored in graphics segment
						entity = node.geometry
						if (entity is not None):
							gr = getModel().getGraphics()
							grNode = gr.indexNodes.get(node.get('index'), None)
							if (grNode is not None):
								color  = getBodyColor(grNode)
								adjustColor(entity, color)
			except Exception as e:
				logError(u"Error in creating (%04X): %s - %s", node.index, node.typeName, e)
				logError(traceback.format_exc())
				node.valid = False
			return node.geometry
		return None

	def addConstraint(self, sketchObj, constraint, key):
		index = sketchObj.addConstraint(constraint)
		self.mapConstraints[key] = constraint
		return index

	def addSolidBody(self, fxNode, obj3D, solid):
		fxNode.setGeometry(obj3D)

		if (solid is not None):
			bodies = solid.get('bodies')
			body = bodies[0]
			body.setGeometry(obj3D)
			# overwrite previously added solids with the same name!
			self.bodyNodes[body.name] = fxNode
			self.lastActiveBody = fxNode
		return

	def addSurfaceBody(self, fxNode, obj3D, surface):
		fxNode.setGeometry(obj3D)
		if (surface is not None):
			# overwrite previously added sourfaces with the same name!
			self.bodyNodes[surface.name] = fxNode
		return

	def getBodyNode(self, ref):
		if (ref.typeName == 'ObjectCollection'):
			bodies = ref.get('bodies')
			try:
				body = bodies[0]
			except:
				body = None
		else:
			body = ref

		try:
			return self.bodyNodes[body.name]
		except:
			return None

	def addBody(self, fxNode, body, solidIdx, surfaceIdx):
		properties = fxNode.get('properties')
		solid = getProperty(properties, solidIdx)
		if (solid is not None):
			self.addSolidBody(fxNode, body, solid)
		else:
			sourface = getProperty(properties, surfaceIdx)
			self.addSurfaceBody(fxNode, body, sourface)
		return

	def findBase(self, base):
		baseGeo = None
		if (base is not None):
			name = getFirstBodyName(base)
			if (name in self.bodyNodes):
				baseGeo = self.getGeometry(self.bodyNodes[name])
				if (baseGeo is None):
					logWarning(u"    Base2 (%04X): %s -> (%04X): %s can't be created!", base.index, baseNode.typeName, bodyNode.index, bodyNode.typeName)
				else:
					logInfo(u"        ... Base2 = '%s'", name)
			else:
				logWarning(u"    Base2 (%04X): %s '%s' nod created!", base.index, base.getSubTypeName(), base.name)
		else:
			logWarning(u"    Base2: ref is None!")

		return baseGeo

	def findSurface(self, node):
		try:
			return self.getGeometry(self.bodyNodes[node.name])
		except:
			return None

	def findGeometries(self, node):
		geometries = []
		if (node is not None):
			assert (node.typeName == 'ObjectCollectionDef'), 'FATA> (%04X): %s expected FaceCollectionProxy ' %(node.index, node.typeName)
			edges = node.get('bodies')
			if (edges is not None):
				for edge in edges:
					name = getFirstBodyName(edge)
					if (name in self.bodyNodes):
						# ensure that the sketch is already created!
						toolGeo = self.getGeometry(self.bodyNodes[name])
						if (toolGeo is None):
							logWarning(u"        Tool (%04X): %s -> (%04X): %s can't be created", node.index, node.typeName, toolData.index, toolData.typeName)
						else:
							geometries.append(toolGeo)
							logInfo(u"        ... Tool = '%s'", name)
					else:
						logWarning(u"    Tool (%04X): %s -> 'bodies' nod found!", node.index, node.typeName)
			else:
				logError(u"ERROR> edges (%04X): %s not defined!", node.index, node.typeName)
		else:
			logWarning(u"    Tool: ref is None!")
		return geometries

	def addDimensionConstraint(self, sketchObj, dimension, constraint, key, useExpression = True):
		number = sketchObj.ConstraintCount
		index = self.addConstraint(sketchObj, constraint, key)
		name = dimension.name
		if (name):
			constraint.Name = str(name)
			sketchObj.renameConstraint(index, name)
			if (useExpression):
				expression = dimension.get('alias')
				sketchObj.setExpression('Constraints[%d]' %(number), expression)
		else:
			constraint.Name = 'Constraint%d' %(index)
		return index

	def adjustIndexPos(self, data, index, pos, point):
		if ((data.typeName == 'Circle2D') or (data.typeName == 'Ellipse2D')):
			x = point.get('x')
			y = point.get('y')
			points = data.get('points')
			for ref in points:
				if (ref):
					if (isEqual1D(ref.get('x'), x) and isEqual1D(ref.get('y'), y) and (ref.sketchIndex != -1)):
						if (ref.sketchIndex is not None):
							index = ref.sketchIndex
						pos = ref.sketchPos
		return index, pos

	def addCoincidentEntity(self, sketchObj, point, entity, pos):
		if (entity.typeName != 'Point2D'):
			vec2D = (getX(point), getY(point))
			if (vec2D not in self.pointDataDict):
				self.pointDataDict[vec2D] = []
			coincidens = self.pointDataDict[vec2D]
			for t in coincidens:
				if (entity.index == t[0].index): return # already added -> done!
			if (pos < 0):
				pos = getCoincidentPos(sketchObj, point, entity)
			if (pos != -1):
				coincidens.append([entity, entity.sketchIndex, pos])
		return

	def addCoincidentConstraint(self, fix, move, sketchObj):
		constraint = None
		if (move is not None):
			if (move[1] is not None):
				typ1 = 'Point'
				if (isinstance(fix[0], SecNodeRef)): typ1 = fix[0].typeName[0:-2]
				if (move[2] is None):
					logInfo(u"        ... added point on object constraint between %s %s/%s and %s %s", typ1, fix[1], fix[2], move[0].typeName[0:-2], move[1])
					constraint = Sketcher.Constraint('PointOnObject', fix[1], fix[2], move[1])
				else:
					logInfo(u"        ... added coincident constraint between %s %s/%s and %s %s/%s", typ1, fix[1], fix[2], move[0].typeName[0:-2], move[1], move[2])
					constraint = Sketcher.Constraint('Coincident', fix[1], fix[2], move[1], move[2])
		return constraint

	def getSketchEntityInfo(self, sketchObj, entity):
		try:
			if (entity.typeName == 'Point2D'):
				entities = entity.get('entities')
				return entities[0].sketchIndex
		except:
			return entity.sketchIndex

	def findEntityPos(self, sketchObj, entity):
		if (entity.typeName == 'Point2D'):
			vec2D = (getX(entity), getY(entity))
			if (isOrigo2D(vec2D)): return (-1, 1)
			if (vec2D in self.pointDataDict):
				coincidens = self.pointDataDict[vec2D]
				if (len(coincidens) > 0):
					return (coincidens[0][1], coincidens[0][2])
			return (createConstructionPoint(sketchObj, entity), 1)
		return (entity.sketchIndex, None)

	def getPointIndexPos(self, sketchObj, point, entity):
		if (entity.typeName == 'Line2D'):   return self.findEntityPos(sketchObj, point) + (entity.sketchIndex, None)
		# if (entity.typeName == 'Circle2D'): return self.findEntityPos(sketchObj, point) + (entity.sketchIndex, 3) #Not supported
		vec2Dp = (getX(point), getY(point))
		if (isOrigo2D(vec2Dp)): return (-1, 1) + self.findEntityPos(sketchObj, entity)

		if (entity.typeName == 'Point2D'):
			vec2De = (getX(entity), getY(entity))
			if (isOrigo2D(vec2De)): return (-1, 1) + self.findEntityPos(sketchObj, point)
			# check if both point belongs to the same line
			if ((vec2Dp in self.pointDataDict) and (vec2De in self.pointDataDict)):
				lstP = self.pointDataDict[vec2Dp]
				lstE = self.pointDataDict[vec2De]
				for p in lstP:
					if (p[0].typeName == 'Line2D'):
						for e in lstE:
							if (p[0].index == e[0].index):
								return p[1], None, p[1], None
			return self.findEntityPos(sketchObj, point) + self.findEntityPos(sketchObj, entity)
		return None, None, None, None

	def getIndexPos(self, sketchObj, entity1, entity2):
		if (entity1.typeName == 'Point2D'):      return self.getPointIndexPos(sketchObj, entity1, entity2)
		if (entity2.typeName == 'Point2D'):      return self.getPointIndexPos(sketchObj, entity2, entity1)

		if (entity1.typeName == 'Line2D'):
			if (entity2.typeName == 'Line2D'):   return entity1.sketchIndex, 1, entity2.sketchIndex, None # Hope that both lines are parallel
#			if (entity2.typeName == 'Circle2D'): return entity2.sketchIndex, 3, entity1.sketchIndex, None # Not supported!
		if (entity1.typeName == 'Circle2D'):
			if (entity2.typeName == 'Line2D'):   return entity1.sketchIndex, 3, entity2.sketchIndex, None # Not supported!
#			if (entity2.typeName == 'Circle2D'): return entity1.sketchIndex, 3, entity2.sketchIndex, 3    # Not supported!

		return None, None, None, None

	def addDistanceConstraint(self, sketchObj, dimensionNode, skipMask, name, prefix):
		if (SKIP_CONSTRAINTS & skipMask == 0): return

		entity1   = dimensionNode.get('entity1')
		entity2   = dimensionNode.get('entity2')
		index1, pos1, index2, pos2 = self.getIndexPos(sketchObj, entity1, entity2)
		prefix    = '%s ' %(prefix) if (len(prefix) > 0) else ''

		if ((index1 is None) or (index2 is None)):
			logWarning(u"        ... skipped %sdimension between %s and %s - not (yet) supported!", prefix, entity1.node.getRefText(), entity2.node.getRefText())
		else:
			if (pos1 is None and entity1.typeName == 'Point2D' and index1 != index2):
				logWarning(u"        ... skipped %sdimension - can't find geometry for %s (entity2: %s,%s)!", prefix, entity1.node.getRefText(), index2, pos2)
				return
			constraint = None
			key = 'Distance%s_%s_%s' %(prefix, index1, index2)
			if (not key in self.mapConstraints):
				dimension = getDimension(dimensionNode, 'parameter')
				distance = getMM(dimension)
				if (index1 == index2):
					constraint = Sketcher.Constraint(name, index1, distance)
				elif (pos1 is None):
					if (pos2 is not None):
						constraint = Sketcher.Constraint(name, index2, pos2, index1, distance)
				elif (pos2 is None):
					constraint = Sketcher.Constraint(name, index1, pos1, index2, distance)
				else:
					constraint = Sketcher.Constraint(name, index1, pos1, index2, pos2, distance)

				if (constraint):
					index = self.addDimensionConstraint(sketchObj, dimension, constraint, key, (pos1 != 3) and (pos2 != 3))
					dimensionNode.setGeometry(constraint, index)
					logInfo(u"        ... added %sdistance '%s' = %s", prefix, constraint.Name, dimension.getValue())
				else:
					logWarning(u"        ... can't create dimension constraint between (%04X): %s and (%04X): %s - not supported by FreeCAD!", entity1.index, entity1.typeName[0:-2], entity2.index, entity2.typeName[0:-2])
		return

	def profile2Section(self, participant):
		face      = participant.get('face')
		surface   = participant.segment.indexNodes[face.get('indexRefs')[0]]
		wireIndex = participant.get('number')
		body      = surface.get('body')
		node      = None

		if (body.name in self.bodyNodes):
			node = self.bodyNodes[body.name]
		else:
			label   = surface.get('label')
			creator = label.get('idxCreator')
			if (creator in participant.segment.indexNodes):
				entity = participant.segment.indexNodes[creator]
				node   = self.getGeometry(entity)
			else:
				logError(u"        ... can't create profile for creator (%04X): %s - creator = %04X", label.index, label.typeName, creator)

		entity  = self.getGeometry(node)
		if (entity is not None):
			# create an entity that can be featured (e.g. loft, sweep, ...)
			section = newObject('Part::Feature', participant.name)
			FreeCAD.ActiveDocument.recompute()

			# FIXME: Howto convert Inventor-Indices to FreeCAD-Indices?
			if (wireIndex == 0):   wireIndex = 1
			elif (wireIndex == 1): wireIndex = 2
			if (wireIndex < len(entity.Shape.Wires)):
				section.Shape = entity.Shape.Wires[wireIndex]
			return section
		return None

	def matchedEdge2Section(self, matchedEdge):
		indexRefs = matchedEdge.get('indexRefs')
		edges = []
		if ((indexRefs is not None) and (len(indexRefs) > 0)):
			for index in indexRefs:
				edgeId = matchedEdge.segment.indexNodes[index]
				wireIndex = edgeId.get('wireIndex')
				creatorIdx = edgeId.get('creator').get('idxCreator')
				creator = matchedEdge.segment.indexNodes[creatorIdx]
				node   = self.getGeometry(creator)
				if (node is not None):
					if (wireIndex < len(node.Shape.Wires)):
						edge = node.Shape.Wires[wireIndex]
						edges.append(edge)

		if (len(edges) > 0):
			section = newObject('Part::Feature', matchedEdge.name)
			section.Shape = Part.Compound(edges)
			return section

		return None

	def collectSection(self, participant):
		if (participant.typeName   == 'Sketch2D'):         return self.getGeometry(participant)
		elif (participant.typeName == 'Sketch3D'):         return self.getGeometry(participant)
		elif (participant.typeName == 'ProfileSelection'): return self.profile2Section(participant)
		elif (participant.typeName == 'MatchedEdge'):      return self.matchedEdge2Section(participant)
		return self.getGeometry(participant) # Not part of the section!

	def addGeometryFromNode(self, boundarySketch, sketchEdge):
		sketch = sketchEdge.get('sketch')
		e      = sketchEdge.get('curve')
		p1     = sketchEdge.get('point1')
		p2     = sketchEdge.get('point2')
		if (e is None):  e  = getAssociatedSketchEntity(sketch, sketchEdge.get('entityAI'), sketchEdge.get('typEntity'))
		if (p1 is None): p1 = getAssociatedSketchEntity(sketch, sketchEdge.get('point1AI'), sketchEdge.get('typPt1'))
		if (p2 is None): p2 = getAssociatedSketchEntity(sketch, sketchEdge.get('point2AI'), sketchEdge.get('typPt2'))
		if (e is None):  return
		edge   = None
		entity = e.geometry
		if (isinstance(entity, Part.Line) or isinstance(entity, Part.LineSegment)):
			if (isSamePoint(p1, p2) == False):
				edge = createLine(p2v(p1), p2v(p2))
		elif (isinstance(entity, Part.ArcOfCircle)):
			edge = Part.Circle(entity.Center, entity.Axis, entity.Radius)
			if (isSamePoint(p1, p2) == False):
				alpha   = edge.parameter(p2v(p1))
				beta    = edge.parameter(p2v(p2))
				if (sketchEdge.get('posDir')):
					edge = Part.ArcOfCircle(edge, alpha, beta)
				else:
					edge = Part.ArcOfCircle(edge, beta, alpha)
#				print (u"Circle r=%g, c=(%g,%g) from %g to %g" %(entity.Radius, entity.Center.x, entity.Center.y, alpha, beta))
		elif (isinstance(entity, Part.ArcOfEllipse)):
			edge = entity
			if (isSamePoint(p1, p2) == False):
				alpha   = entity.parameter(p2v(p1))
				beta    = entity.parameter(p2v(p2))
				if (sketchEdge.get('posDir')):
					edge = Part.ArcOfEllipse(edge, alpha, beta)
				else:
					edge = Part.ArcOfEllipse(edge, beta, alpha)
		elif (isinstance(entity, Part.Circle)):
			edge = entity
			if (isSamePoint(p1, p2) == False):
				alpha   = edge.parameter(p2v(p1))
				beta    = edge.parameter(p2v(p2))
				if (sketchEdge.get('posDir')):
					edge = Part.ArcOfCircle(edge, alpha, beta)
				else:
					edge = Part.ArcOfCircle(edge, beta, alpha)
		elif (isinstance(entity, Part.Ellipse)):
			edge = entity
			if (isSamePoint(p1, p2) == False):
				alpha   = edge.parameter(p2v(p1))
				beta    = edge.parameter(p2v(p2))
				if (sketchEdge.get('posDir')):
					edge = Part.ArcOfEllipse(edge, alpha, beta)
				else:
					edge = Part.ArcOfEllipse(edge, beta, alpha)
		elif (isinstance(entity, Part.BSplineCurve)):
			a = entity.parameter(p2v(p1))
			b = entity.parameter(p2v(p2))
			if (a > b):
				old = a
				a = b
				b = old
			if not (isEqual1D(a, 0.0) and isEqual1D(b, 1.0)):
				try:
					edge = entity.trim(a, b)
				except:
					logWarning(u"    Can't trim BSpline for a=%g and b=%g!", a, b)
					edge = entity.copy()
			else:
				edge = entity.copy()
	#	elif (typ[0: 4] == 'Text'):
	#	elif (typ[0:12] == 'OffsetSpline'):
	#	elif (typ[0:12] == 'SplineHandle'):
	#	elif (typ[0: 5] == 'Block'):
	#	elif (typ[0: 5] == 'Image'):
		else:
			logWarning(u"    ... Don't know how to create edge from %s.%s" %(edge.__class__.__module__, edge.__class__.__name__))
		if (edge is not None):
			if (hasattr(boundarySketch, 'addGeometry')):
				boundarySketch.addGeometry(edge)
			else:
				sketchEdge.setGeometry(edge)
				boundarySketch.Shape = Part.Shape(boundarySketch.Shape.Edges + [edge])
		return

	def addBoundaryPart(self, boundarySketch, part):
		if (part.typeName in ['Loop', 'Loop3D']):
			for sketchEdge in part.get('edges'): # should be SketchEntityRef
				sketchNode = sketchEdge.get('sketch')
				if (boundarySketch is None):
					if (sketchNode is not None):
						if (sketchNode.geometry is None): self.getGeometry(sketchNode)
						if (sketchNode.typeName == 'Sketch2D'):
							boundarySketch = newObject('Sketcher::SketchObject', u"%s_bp" %(sketchNode.name))
							boundarySketch.Placement = sketchNode.geometry.Placement
						elif (sketchNode.typeName == 'Sketch3D'):
							boundarySketch = InventorViewProviders.makeSketch3D()
							boundarySketch.Placement = sketchNode.geometry.Placement
				if (boundarySketch is not None):
					self.addGeometryFromNode(boundarySketch, sketchEdge)
		else:
			logError(u"    Error:  unknown boundaryPart (%04X): %s!", part.index, part.typeName)
		return boundarySketch

	def createBoundary(self, boundaryPatch):
		if (boundaryPatch is not None):
			profile  = boundaryPatch.get('profile')
			if (profile is not None):
				if (profile.typeName in ['FaceBound', '603428AE', '79D4DD11', 'FaceBounds', 'FaceBoundOuter']):
					sketch = profile.get('sketch')
					boundary = None
					if (sketch is not None):
						boundary = newObject('Sketcher::SketchObject', u"%s_bp" %(sketch.name))
						if (sketch.geometry is None): self.getGeometry(sketch)
						boundary.Placement = sketch.geometry.Placement
						hide(sketch.geometry)
					# create all parts of the profile
					parts = profile.get('parts')
					if (len(parts) == 1):
						boundary = self.addBoundaryPart(boundary, parts[0])
					else:
						for part in parts:
							if (part.get('operation') & 0x08):
								boundary = self.addBoundaryPart(boundary, part)
					return boundary
				else:
					logError(u"        ... can't create boundary from (%04X): %s - expected next node type (%s) unknown!", boundaryPatch.index, boundaryPatch.typeName, profile.typeName)
			else:
				if (boundaryPatch.typeName in ['MatchedEdge']):
					boundary = self.matchedEdge2Section(boundaryPatch)
					return boundary
				else:
					logWarning(u"    Error:  boundaryPatch (%04X): %s has no 'profile' property!", boundaryPatch.index, boundaryPatch.typeName)
		return None

	def getEdgeFromProxy(self, matchedEdge):
		assert matchedEdge.typeName in ['MatchedEdge', '3BA63938'], u"found '%s'!" %(matchedEdge.typeName)
		acis = getModel().getBRep().getDcSatAttributes() #  ref. importerSegment.Read_F645595C
		for idxRef in matchedEdge.get('indexRefs'):
			edgeId = matchedEdge.segment.indexNodes[idxRef]
			assert (edgeId.typeName == 'EdgeId'),  u"found '%s'!" %(edgeId.typeName)
			creator = edgeId.get('creator')
			if (creator is not None):
				idxCreator = creator.get('idxCreator')
				creator    = matchedEdge.segment.indexNodes[idxCreator]
				geometry   = self.getGeometry(creator) # ensure that the creator is already available!
				if (geometry is not None):
					edgeAttrs  = acis[idxRef]
					acisEdges  = edgeAttrs.getEdges()
					return idxCreator, findFcEdgeIndex(geometry.Shape, acisEdges)
		return None

	def getEdgesFromSet(self, edgeSet):
		all_edges = {} #
		if (edgeSet is not None):
			for matchedEdge in edgeSet.get('edges'):
				edge = self.getEdgeFromProxy(matchedEdge)
				if (edge is not None):
					idxEdge    = edge[1]
					if (idxEdge is not None):
						idxCreator = edge[0]
						if (idxCreator in all_edges):
							all_edges[idxCreator].append(idxEdge)
						else:
							all_edges[idxCreator] = [idxEdge]
		return all_edges

	def collectSections(self, fxNode, action): #
		participants = fxNode.getParticipants()
		sections     = []

		for participant in participants:
			section = self.collectSection(participant)
			if (section is not None):
				sections.append(section)
			else:
				logWarning(u"        ... don't know how to %s (%04X): %s '%s' - IGNORED!", action, participant.index, participant.typeName, participant.name)

		return sections

	def createBoolean(self, className, name, baseGeo, tools):
		booleanGeo = baseGeo
		if ((baseGeo is not None) and (len(tools) > 0)):
			booleanGeo = newObject('Part::%s' %(className), name)
			if (className == 'Cut'):
				booleanGeo.Base = baseGeo
				booleanGeo.Tool = tools[0]
			else:
				# FreeCAD can't combine solids and shells!
				# All shapes must have same solid status as solid!
				if (hasattr(baseGeo, 'Solid')):
					solid = baseGeo.Solid
				else:
					solid = True
				for tool in tools:
					if (hasattr(tool, 'Solid')):
						tool.Solid = solid
				booleanGeo.Shapes = [baseGeo] + tools
			adjustViewObject(booleanGeo, baseGeo)
		return booleanGeo

	def createCone(self, name, diameter2, angle, diameter1):
		conGeo = newObject('Part::Cone', name)
		R1 = setParameter(conGeo, 'Radius1', diameter1, getMM, 0.5)
		R2 = setParameter(conGeo, 'Radius2', diameter2, getMM, 0.5)
		h  = abs(R1 - R2) / tan(angle.getValue().getRAD() / 2)
		conGeo.setExpression('Height', "abs(Radius2 - Radius1)/tan(%s*pi/180)/2" %(angle.get('alias')))
		conGeo.Placement.Base.z = -h
		return conGeo, h

	def createCylinder(self, name, diameter, height, drillPoint):
		cylGeo = newObject('Part::Cylinder', name)
		r  = setParameter(cylGeo, 'Radius', diameter, getMM, 0.5)
		h1 = setParameter(cylGeo, 'Height', height)
		cylGeo.Placement.Base.z = -h1

		if (drillPoint):
			angle = drillPoint.getValue().getRAD()
			if (angle > 0):
				conGeo, h2 = self.createCone(name + 'T', diameter, drillPoint, None)
				conGeo.Placement.Base.z -= h1
				return [cylGeo, conGeo], h1

		return [cylGeo], h1

	def createEntity(self, node, className):
		name = node.name
		if ((name is None) or (len(name) == 0)): name = node.typeName
		entity = newObject(className, name)
		return entity

	def getEdges(self, wire):
		if (wire is not None):
			FreeCAD.ActiveDocument.recompute()
			count = len(wire.Shape.Edges)
			return ['Edge%i' %(i) for i in range(1, count + 1)]

		return []

	def getLength(self, body, dir):
		lx, ly, lz = 0, 0, 0
		node = self.getBodyNode(body)
		if (node):
			box = node.geometry.Shape.BoundBox
			if (not isEqual1D(dir.x, 0)): lx = box.XLength * box.XLength
			if (not isEqual1D(dir.y, 0)): ly = box.YLength * box.YLength
			if (not isEqual1D(dir.z, 0)): lz = box.ZLength * box.ZLength
		return sqrt(lx + ly + lz)

	def resolveParticiants(self, fxNode):
		geos = []
		for participant in fxNode.getParticipants():
			fxGeo = self.getGeometry(participant)
			if (fxGeo is not None):
				geos.append(fxGeo)
		return geos

	def combineGeometries(self, geometries, fxNode):
		if (len(geometries) > 1):
			geometry = self.createEntity(fxNode, 'Part::MultiFuse')
			geometry.Shapes = geometries
			return geometry
		if (len(geometries) == 1):
			return geometries[0]
		return None

########################
	def addSketch_Geometric_Fix2D(self, constraintNode, sketchObj):
		'''
		A fix constraint doesn't exists in FreeCAD.
		Workaround: two distance constraints (X and Y)
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_FIX == 0): return
		return

	def addSketch_Geometric_PolygonCenter2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINTS & BIT_GEO_POLYGON == 0): return
		center = constraintNode.get('center')
		construction = constraintNode.get('construction')
		if (construction):
#			for polygonEdge in construction.get('lst2'):
				pass
		return

	def addSketch_Geometric_PolygonEdge2D(self, constraintNode, sketchObj):
		# handled together with addSketch_Geometric_PolygonCenter2D
		return ignoreBranch(constraintNode)

	def addSketch_Geometric_Coincident2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINTS & BIT_GEO_COINCIDENT == 0): return
		entity1 = constraintNode.get('entity1')
		entity2 = constraintNode.get('entity2')
		if (entity1.typeName == 'Point2D'):
			self.addCoincidentEntity(sketchObj, entity1, entity2, -1)
		elif (entity2.typeName == 'Point2D'):
			self.addCoincidentEntity(sketchObj, entity2, entity1, -1)
		return

	def addSketch_Geometric_SymmetryPoint2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINTS & BIT_GEO_SYMMETRY_POINT == 0): return
		point = constraintNode.get('point')
		symmetryIdx = point.sketchIndex

		moving = constraintNode.get('entity')
		lineIdx =  moving.sketchIndex

		if ((lineIdx is None) or (lineIdx < 0)):
			logWarning(u"        ... can't added symmetric constraint between Point and %s - no line index for (%04X)!", moving.typeName[0:-2], moving.index)
		elif ((symmetryIdx is None) or (symmetryIdx < 0) or (symmetryPos < -1)):
			logWarning(u"        ... can't added symmetric constraint between Point and %s - no point index for (%04X)!", moving.typeName[0:-2], constraintNode.get('point').index)
		else:
			key = 'SymmetryPoint_%s_%s' %(lineIdx, symmetryIdx)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Symmetric', lineIdx, 1, lineIdx, 2, symmetryIdx, symmetryPos)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setGeometry(constraint, index)
				logInfo(u"        ... added symmetric constraint between Point %s and %s %s", symmetryIdx, moving.typeName[0:-2], lineIdx)
		return

	def addSketch_Geometric_SymmetryLine2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINTS & BIT_GEO_SYMMETRY_LINE == 0): return
		entity1    = constraintNode.get('entity1')
		entity2    = constraintNode.get('entity2')
		symmetry   = constraintNode.get('symmetry')

		idx1, pos1 = self.findEntityPos(sketchObj, entity1)
		idx2, pos2 = self.findEntityPos(sketchObj, entity2)
		idxSym     = symmetry.sketchIndex

		if (idxSym is None):
			logWarning(u"        ... skipped symmetric line constraint - can't find iindex for symmetry line (%04X) %s!", symmetry.index, symmetry.typeName)
		elif (idx1 is None):
			logWarning(u"        ... skipped symmetric line constraint - can't find index for 1st entity (%04X) %s!", entity1.index, entity1.typeName)
		elif (pos1 is None):
			logWarning(u"        ... skipped symmetric line constraint - can't find vertex for 1st entity (%04X) %s!", entity1.index, entity1.typeName)
		elif (idx2 is None):
			logWarning(u"        ... skipped symmetric line constraint - can't find index for 2nd entity (%04X) %s!", entity2.index, entity2.typeName)
		elif (pos2 is None):
			logWarning(u"        ... skipped symmetric line constraint - can't find vertex for 2nd entity (%04X) %s!", entity2.index, entity2.typeName)
		else:
			key = 'SymmetricLine_%d_%s_%d_%s_%d' %(idx1, pos1, idx2, pos2, idxSym)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Symmetric',idx1, pos1, idx2, pos2, idxSym)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setGeometry(constraint, index)
				logInfo(u"        ... added symmetric line constraint between %s %d/%d and %s %d/%d, symmetry is %s %d", entity1.typeName[0:-2], idx1, pos1, entity2.typeName[0:-2], idx2, pos2, symmetry.typeName[0:-2], idxSym)
		return

	def addSketch_Geometric_Parallel2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_PARALLEL == 0): return
		index1 = constraintNode.get('line1').sketchIndex
		if (index1 is None): return
		index2 = constraintNode.get('line2').sketchIndex
		if (index2 is None): return
		key = 'Parallel_%s_%s' %(index1, index2)
		if (not key in self.mapConstraints):
			constraint = Sketcher.Constraint('Parallel', index1, index2)
			index = self.addConstraint(sketchObj, constraint, key)
			constraintNode.setGeometry(constraint, index)
			logInfo(u"        ... added parallel constraint between lines %s and %s", index1, index2)
		return

	def addSketch_Geometric_Perpendicular2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idxMov: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_PERPENDICULAR == 0): return
		index1 = constraintNode.get('line1').sketchIndex
		index2 = constraintNode.get('line2').sketchIndex
		if (index1 is None):
			logWarning(u"        ... skipped perpendicular constraint between lines - line 1 (%04X) has no index!", constraintNode.get('line1').index)
		elif (index2 is  None):
			logWarning(u"        ... skipped perpendicular constraint between lines - line 2 (%04X) has no index!", constraintNode.get('line2').index)
		else:
			key = 'Perpendicular_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Perpendicular', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setGeometry(constraint, index)
				logInfo(u"        ... added perpendicular constraint between lines %s and %s", index1, index2)
		return

	def addSketch_Geometric_Collinear2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_TANGENTIAL == 0): return
		index1 = constraintNode.get('line1').sketchIndex
		index2 = constraintNode.get('line2').sketchIndex
		if (index1 is None):
			logWarning(u"        ... skipped collinear constraint between lines - line 1 (%04X) has no index!", constraintNode.get('line1').index)
		elif (index2 is  None):
			logWarning(u"        ... skipped collinear constraint between lines - line 2 (%04X) has no index!", constraintNode.get('line2').index)
		else:
			key = 'Collinear_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Tangent', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setGeometry(constraint, index)
				logInfo(u"        ... added collinear constraint between Line %s and Line %s", index1, index2)
		return

	def addSketch_Geometric_Tangential2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_TANGENTIAL == 0): return
		entity1Node = constraintNode.get('entity1')
		entity2Node = constraintNode.get('entity2')
		entity1Name = entity1Node.typeName[0:-2]
		entity2Name = entity2Node.typeName[0:-2]
		index1 = entity1Node.sketchIndex
		index2 = entity2Node.sketchIndex
		if (index1 is None):
			logWarning(u"        ... skipped tangential constraint between %s and %s - entity 1 (%04X) has no index!", entity1Name, entity2Name, entity1Node.index)
		elif (index2 is None):
			logWarning(u"        ... skipped tangential constraint between %s and %s - entity 2 (%04X) has no index!", entity1Name, entity2Name, entity2Node.index)
		else:
			key = 'Tangent_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Tangent', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setGeometry(constraint, index)
				logInfo(u"        ... added tangential constraint between %s %s and %s %s", entity1Name, index1, entity2Name, index2)
		return

	def addSketch_Geometric_Vertical2D(self, constraintNode, sketchObj):
		'''
		index: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_VERTICAL == 0): return
		index = constraintNode.get('line').sketchIndex
		if (index is not None):
			key = 'Vertical_%s' %(index)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Vertical', index)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setGeometry(constraint, index)
				logInfo(u"        ... added vertical constraint to line %s", index)
		return

	def addSketch_Geometric_Horizontal2D(self, constraintNode, sketchObj):
		'''
		index: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_HORIZONTAL == 0): return
		entity = constraintNode.get('line')
		if (entity.typeName == 'Line2D'):
			index = entity.sketchIndex
			if (index is not None):
				key = 'Horizontal_%s' %(index)
				if (not key in self.mapConstraints):
					constraint = Sketcher.Constraint('Horizontal', index)
					index = self.addConstraint(sketchObj, constraint, key)
					constraintNode.setGeometry(constraint, index)
					logInfo(u"        ... added horizontal constraint to line %s", index)
		else:
			logWarning(u"        ... can't add a horizontal constraint to (%04x): %s", entity.index, entity.typeName)
		return

	def addSketch_Geometric_EqualLength2D(self, constraintNode, sketchObj):
		'''
		Create a  equal legnth constraint
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_EQUAL == 0): return
		index1 = constraintNode.get('line1').sketchIndex
		index2 = constraintNode.get('line2').sketchIndex
		if (index1 is None):
			logWarning(u"        ... skipped equal length constraint between lines - line 1 (%04X) has no index!", constraintNode.get('line1').index)
		elif (index2 is None):
			logWarning(u"        ... skipped equal length constraint between lines - line 2 (%04X) has no index!", constraintNode.get('line2').index)
		else:
			key = 'Equal_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Equal', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setGeometry(constraint, index)
				logInfo(u"        ... added equal length constraint between line %s and %s", index1, index2)
		return

	def addSketch_Geometric_EqualRadius2D(self, constraintNode, sketchObj):
		'''
		Create a  equal radius constraint
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_EQUAL == 0): return
		index1 = constraintNode.get('circle1').sketchIndex
		index2 = constraintNode.get('circle2').sketchIndex
		if (index1 is None):
			logWarning(u"        ... skipped equal radius constraint between circles - circle 1 (%04X) has no index!", constraintNode.get('circle1').index)
		elif (index2 is None):
			logWarning(u"        ... skipped equal radius constraint between circles - circle 2 (%04X) has no index!", constraintNode.get('circle2').index)
		else:
			key = 'Equal_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Equal', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setGeometry(constraint, index)
				logInfo(u"        ... added equal radius constraint between circle %s and %s", index1, index2)
		return

	def addSketch_Point2D(self, pointNode, sketchObj):
		vec2D = (getX(pointNode), getY(pointNode))
		if (vec2D not in self.pointDataDict):
			self.pointDataDict[vec2D] = []
		pointNode.valid = False
		return

	def addSketch_BlockPoint2D(self, node, sketchObj): return

	def addSketch_Point3D(self, pointNode, sketchObj): return

	def removeFromPointRef(self, point, index):
		vec2D = (getX(point), getY(point))
		if (vec2D in self.pointDataDict):
			constraints = self.pointDataDict[vec2D]
			for j in range(len(constraints)):
				entity, index, pos = constraints[j]
				if (entity.index == index):
					del constraints[j]
					return # there can only exists one element in the list!
		return

	def invalidateLine2D(self, lineNode):
		lineNode.valid = False
		points = lineNode.get('points')
		self.removeFromPointRef(points[0], lineNode.index)
		self.removeFromPointRef(points[1], lineNode.index)

	def createLine2D(self, sketchObj, point1, point2, mode, line):
		if (isSamePoint(point1, point2)):
			return False
		part = createLine(p2v(point1), p2v(point2))
		addSketch2D(sketchObj, part, mode, line)
		return True

	def createLine3D(self, sketchObj, line):
		p1 = p2v(line)
		p2 = p2v(line, 'dirX', 'dirY', 'dirZ')
		if (p2.Length == 0): return False
		part = createLine(p1, p1 + p2)
		addSketch3D(sketchObj, part, isConstructionMode(line), line)
		return True

	def createRevolve(self, name, angle1, angle2, source, axis, base, solid, positive):
		revolution = newObject('Part::Revolution', name)
		setParameter(revolution, 'Angle', (angle1, angle2), getGRAD)
		revolution.Source = source
		if (positive):
			revolution.Axis = axis
		else:
			revolution.Axis = -axis
		revolution.Base = base
		revolution.Solid = solid and source.Shape.isClosed()
		revolution.Placement = PLC(CENTER, ROT(axis, -getGRAD(angle2)), base)
		setDefaultViewObjectValues(revolution)
		source.ViewObject.Visibility = False
		return revolution

	def addSketch_Line2D(self, lineNode, sketchObj):
		points = lineNode.get('points')
		mode = isConstructionMode(lineNode)
		if (self.createLine2D(sketchObj, points[0], points[1], mode, lineNode) == False):
			logWarning(u"        ... can't add %s: length = 0.0!", lineNode.getRefText())
			self.invalidateLine2D(lineNode)
		else:
			x1 = getX(points[0])
			y1 = getY(points[0])
			x2 = getX(points[1])
			y2 = getY(points[1])
			logInfo(u"        ... added line (%g,%g)-(%g,%g) %r = %s", x1, y1, x2, y2, mode, lineNode.sketchIndex)
		return

	def addSketch_Line3D(self, lineNode, sketchObj):
		if (self.createLine3D(sketchObj, lineNode) == False):
			logWarning(u"        ... Can't add line (%04X) with length = 0.0!", lineNode.index)
			lineNode.valid = False
		else:
			x1 = lineNode.get('x')
			y1 = lineNode.get('y')
			z1 = lineNode.get('z')
			x2 = lineNode.get('dirX') + x1
			y2 = lineNode.get('dirY') + y1
			z2 = lineNode.get('dirZ') + z1
			logInfo(u"        ... added line (%g,%g,%g)-(%g,%g,%g) %r", x1, y1, z1, x2, y2, z2, isConstructionMode(lineNode))
		return

	def addSketch_Spline2D(self, splineNode, sketchObj):
		'''
		Workaround: As FreeCAD doesn't support Splines, they are converted to simple lines.
		x_c = (x1^2 + x2^2 + x2^2) / 3.0
		y_c = (y1^2 + y2^2 + y2^2) / 3.0
		'''
		# p0 = startPoint
		# p1 = endPoint
		points = splineNode.get('points')
		mode = isConstructionMode(splineNode)
		if (len(points) > 2):
			self.createLine2D(sketchObj, points[0], points[2], mode, splineNode)
			i = 2
			while (i < len(points) - 1):
				self.createLine2D(sketchObj, points[i], points[i+1], mode, splineNode)
				i += 1
			self.createLine2D(sketchObj, points[len(points) - 1], points[1], mode, splineNode)
		else:
			self.createLine2D(sketchObj, points[0], points[1], mode, splineNode)
			logInfo(u"        ... added spline = %s", splineNode.sketchIndex)

		return

	def addSketch_Arc2D(self, arcNode, sketchObj):
		points = arcNode.get('points')
		mode   = isConstructionMode(arcNode)

		# There shell be 3 points to draw a 2D arc.
		# the 3rd point defines the a point on the circle between start and end! -> scip, as it is a redundant information to calculate the radius!
		arc = createArc(points[0], points[1], points[2])
		logInfo(u"        ... added Arc-Circle start=%s, end=%s and %s ...", points[0], points[1], points[2])
		addSketch2D(sketchObj, arc, mode, arcNode)
		return

	def addSketch_Circle2D(self, circleNode, sketchObj):
		center = circleNode.get('center')
		x = getX(center)
		y = getY(center)
		r = getCoord(circleNode, 'r')
		points = circleNode.get('points')
		mode = isConstructionMode(circleNode)
		if (not mode):
			nextNode = circleNode.segment.elementNodes.get(circleNode.index+1, None)
			if (nextNode is not None):
				mode = (nextNode.typeName == '64DE16F3')
		point1 = None
		point2 = None
		circle = createCircle(center, DIR_Z, r)
		if (len(points) > 0): point1 = points[0]
		if (len(points) > 1): point2 = points[1]

		# There has to be at least 2 points to draw an arc.
		# Everything else will be handled as a circle!
		if ((point1 is None) and (point2 is None) or (isSamePoint(point1, point2))):
			addSketch2D(sketchObj, circle, mode, circleNode)
			logInfo(u"        ... added Circle M=(%g,%g) R=%g...", x, y, r)
		else:
			a = circle.parameter(p2v(point1))
			b = circle.parameter(p2v(point2))
			arc = Part.ArcOfCircle(circle, a, b)
			logInfo(u"        ... added Arc-Circle M=(%g,%g) R=%g, from %s to %s ...", x, y, r, a, b)
			addSketch2D(sketchObj, arc, mode, circleNode)

		return

	def addSketch_Circle3D(self, circleNode, sketchObj):
		x      = getCoord(circleNode, 'x')
		y      = getCoord(circleNode, 'y')
		z      = getCoord(circleNode, 'z')
		r      = getCoord(circleNode, 'r')
		normal = circleNode.get('normal')
		points = circleNode.get('points')

		part = createCircle(circleNode, normal, r)

		# There has to be at least 2 points to draw an arc.
		# Everything else will be handled as a circle!
		if (len(points) < 2):
			addSketch3D(sketchObj, part, isConstructionMode(circleNode), circleNode)
			logInfo(u"        ... added Circle M=(%g,%g,%g) R=%g...", x, y, z, r)
		if (len(points) == 2):
			a = Angle(circleNode.get('startAngle'), pi/180.0, u'\xb0')
			b = Angle(circleNode.get('sweepAngle'), pi/180.0, u'\xb0')
			arc = Part.ArcOfCircle(part, a.getRAD(), b.getRAD())
			logInfo(u"        ... added Arc-Circle M=(%g,%g,%g) R=%g, from %s to %s ...", x, y, z, r, a, b)
			addSketch3D(sketchObj, arc, isConstructionMode(circleNode), circleNode)
		else:
			logWarning(u"        ... can't Arc-Circle more than 2 points - SKIPPED!", x, y, r, a, b)
		return

	def addSketch_Ellipse2D(self, ellipseNode, sketchObj):
		center = ellipseNode.get('center')
		if (center.typeName == 'Circle2D'):
			#add concentric constraint
			center = center.get('center')

		c_x = getX(center)
		c_y = getY(center)
		d = ellipseNode.get('dA')

		x = getCoord(ellipseNode, 'a')
		a_x = c_x + (x * d[0])
		a_y = c_y + (x * d[1])

		x = getCoord(ellipseNode, 'b')
		b_x = c_x - (x * d[1])
		b_y = c_y + (x * d[0])

		vecA = VEC(a_x, a_y, 0.0)
		vecB = VEC(b_x, b_y, 0.0)
		vecC = VEC(c_x, c_y, 0.0)

		try:
			part = Part.Ellipse(vecA, vecB, vecC)
		except:
			part = Part.Ellipse(vecB, vecA, vecC)

		a = ellipseNode.get('alpha')
		b = ellipseNode.get('beta')
		if (isEqual1D(a, b)):
			logInfo(u"        ... added 2D-Ellipse  c=(%g,%g) a=(%g,%g) b=(%g,%g) ...", c_x, c_y, a_x, a_y, b_x, b_y)
		else:
			a = Angle(a, pi/180.0, u'\xb0')
			b = Angle(b, pi/180.0, u'\xb0')
			logInfo(u"        ... added 2D-Arc-Ellipse  c=(%g,%g) a=(%g,%g) b=(%g,%g) from %s to %s ...", c_x, c_y, a_x, a_y, b_x, b_y, a, b)
			part = Part.ArcOfEllipse(part, a.getGRAD(), b.getGRAD())
		addSketch2D(sketchObj, part, isConstructionMode(ellipseNode), ellipseNode)
		return

	def addSketch_Ellipse3D(self, ellipseNode, sketchObj):
		a = p2v(ellipseNode, 'a_x', 'a_y', 'a_z')
		b = p2v(ellipseNode, 'b_x', 'b_y', 'b_z')
		c = p2v(ellipseNode, 'c_x', 'c_y', 'c_z')
		part = Part.Ellipse(a, b, c)

		a1 = ellipseNode.get('startAngle')
		a2 = ellipseNode.get('sweepAngle')
		if (isEqual1D(a1, a2)):
			logInfo(u"        ... added 3D-Ellipse  c=(%g,%g,%g) a=(%g,%g,%g) b=(%g,%g,%g) ...", c.x, c.y, c.z, a.x, a.y, a.z, b.x, b.y, b.z)
		else:
			a1 = Angle(a1, pi/180.0, u'\xb0')
			a2 = Angle(a2, pi/180.0, u'\xb0')
			logInfo(u"        ... added 3D-Arc-Ellipse  c=(%g,%g,%g) a=(%g,%g,%g) b=(%g,%g,%g) from %s to %s ...", c.x, c.y, c.z, a.x, a.y, a.z, b.x, b.y, b.z, a1, a2)
			part = Part.ArcOfEllipse(part, a1.getGRAD(), a2.getGRAD())
		addSketch3D(sketchObj, part, isConstructionMode(ellipseNode), ellipseNode)
		return

	def addSketch_Text2D(self, textNode, sketchObj): return unsupportedNode(textNode)

	def addSketch_Direction(self, directionNode, sketchObj):             return ignoreBranch(directionNode)
	def addSketch_Geometric_TextBox2D(self, frameNode, sketchObj):       return ignoreBranch(frameNode)
	def addSketch_Geometric_Radius2D(self, radiusNode, sketchObj):       return ignoreBranch(radiusNode)
	def addSketch_Geometric_SplineFitPoint2D(self, infoNode, sketchObj): return ignoreBranch(infoNode)
	def addSketch_Geometric_Offset2D(self, node, sketchObj):
		'''
		Create an offset constraint.
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_OFFSET == 0): return
		return
	def addSketch_Geometric_AlignHorizontal2D(self, node, sketchObj):
		'''
		Create an horizontal align constraint.
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_ALIGN_HORIZONTAL == 0): return
		return
	def addSketch_Geometric_AlignVertical2D(self, node, sketchObj):
		'''
		Create an vertical align constraint.
		'''
		if (SKIP_CONSTRAINTS & BIT_GEO_ALIGN_VERTICAL == 0): return
		return
	def addSketch_Transformation(self, transformationNode, sketchObj):   return ignoreBranch(transformationNode)
	def addSketch_RtfContent(self, stringNode, sketchObj):               return ignoreBranch(stringNode)

	def addSketch_Dimension_Distance_Horizontal2D(self, dimensionNode, sketchObj):
		'''
		Create a horizontal dimension constraint
		'''
		self.addDistanceConstraint(sketchObj, dimensionNode, BIT_DIM_DISTANCE, 'DistanceX', 'horizontal')
		return

	def addSketch_Dimension_Distance_Vertical2D(self, dimensionNode, sketchObj):
		'''
		Create a vertical dimension constraint
		'''
		self.addDistanceConstraint(sketchObj, dimensionNode, BIT_DIM_DISTANCE, 'DistanceY', 'vertical')
		return

	def addSketch_Dimension_Distance2D(self, dimensionNode, sketchObj):
		'''
		Create a distance constraint
		'''
		self.addDistanceConstraint(sketchObj, dimensionNode, BIT_DIM_DISTANCE, 'Distance', '')
		return

	def addSketch_Dimension_Radius2D(self, dimensionNode, sketchObj):
		'''
		Create a radius constraint
		'''
		if (SKIP_CONSTRAINTS & BIT_DIM_RADIUS == 0): return
		circle    = dimensionNode.get('circle')
		index     = circle.sketchIndex
		dimension = getDimension(dimensionNode, 'parameter')
		if (index is not None):
			key = 'Radius_%s' %(index)
			if (not key in self.mapConstraints):
				radius = circle.geometry.Radius
				constraint = Sketcher.Constraint('Radius',  index, radius)
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setGeometry(constraint, index)
				logInfo(u"        ... added radius '%s' = %s", constraint.Name, dimension.getValue())
		return

	def addSketch_Dimension_RadiusA2D(self, dimensionNode, sketchObj):
		if (SKIP_CONSTRAINTS & BIT_DIM_RADIUS == 0): return
		dimension = getDimension(dimensionNode, 'parameter')
		circle    = dimensionNode.get('ellipse')
		index     = circle.sketchIndex
		if (index is not None):
			pass

		return

	def addSketch_Dimension_RadiusB2D(self, dimensionNode, sketchObj):
		if (SKIP_CONSTRAINTS & BIT_DIM_RADIUS == 0): return
		dimension = getDimension(dimensionNode, 'parameter')
		circle    = dimensionNode.get('ellipse')
		index     = circle.sketchIndex
		if (index is not None):
			pass

		return

	def addSketch_Dimension_Diameter2D(self, dimensionNode, sketchObj):
		'''
		Create a diameter (not available in FreeCAD) constraint
		Workaround: Radius and Center constraint.
		'''
		if (SKIP_CONSTRAINTS & BIT_DIM_DIAMETER == 0): return
		circle = dimensionNode.get('circle')
		index  = circle.sketchIndex
		if (index is not None):
			key = 'Diameter_%s' %(index)
			if (not key in self.mapConstraints):
				#TODO: add a 2D-construction-line, pin both ends to the circle, pin circle's center on this 2D-line and add dimension constraint to 2D-construction-line
				radius = circle.geometry.Radius
				constraint = Sketcher.Constraint('Radius',  index, radius)
				dimension = getDimension(dimensionNode, 'parameter')
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key, False)
				dimensionNode.setGeometry(constraint, index)
				logInfo(u"        ... added diameter '%s' = %s (r = %s mm)", constraint.Name, dimension.getValue(), radius)
		return

	def addSketch_Dimension_Angle3Point2D(self, dimensionNode, sketchObj):
		'''
		Create an angle constraint between the three points.
		'''
		if (SKIP_CONSTRAINTS & BIT_DIM_ANGLE_3_POINT == 0): return
		pt1Ref = dimensionNode.get('point1')
		pt2Ref = dimensionNode.get('point2') # the center point
		pt3Ref = dimensionNode.get('point3')
		return

	def addSketch_Dimension_Angle2Line2D(self,  dimensionNode, sketchObj):
		'''
		Create a angle constraint
		'''
		if (SKIP_CONSTRAINTS & BIT_DIM_ANGLE_2_LINE == 0): return
		line1 = dimensionNode.get('line1')
		line2 = dimensionNode.get('line2')
		index1 = line1.sketchIndex
		index2 = line2.sketchIndex

		if (index1 is None):
			logWarning(u"        ... skipped dimension angle '%s' = %s - line 1 (%04X) has no index!", constraint.Name, dimension.getValue(), line1.index)
		elif (index2 is None):
			logWarning(u"        ... skipped dimension angle '%s' = %s - line 2 (%04X) has no index!", constraint.Name, dimension.getValue(), line2.index)
		else:
			points1 = line1.get('points')
			points2 = line2.get('points')

			pt11 = points1[0]
			pt12 = points1[1]
			pt21 = points2[0]
			pt22 = points2[1]

			d1121 = getDistancePointPoint(pt11, pt21)
			d1122 = getDistancePointPoint(pt11, pt22)
			d1221 = getDistancePointPoint(pt12, pt21)
			d1222 = getDistancePointPoint(pt12, pt22)

			if ((d1121 < d1122) and (d1121 < d1221) and (d1121 < d1222)):
				pos1 = 1
				pos2 = 1
			elif ((d1122 < d1121) and (d1122 < d1221) and (d1122 < d1222)):
				pos1 = 1
				pos2 = 2
			elif ((d1221 < d1121) and (d1221 < d1122) and (d1221 < d1222)):
				pos1 = 2
				pos2 = 1
			else:
				pos1 = 2
				pos2 = 2

			key = 'Angle_%s_%s_%s_%s' %(index1, pos1, index2, pos2)
			if (not key in self.mapConstraints):
				dimension  = getDimension(dimensionNode, 'parameter')
				angle      = dimension.getValue()
				constraint = Sketcher.Constraint('Angle', index1, pos1, index2, pos2, angle.getRAD())
				index      = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setGeometry(constraint, index)
				logInfo(u"        ... added dimension angle '%s' = %s (%s)", constraint.Name, angle, key)
		return

	def addSketch_Dimension_OffsetSpline2D(self, dimensionNode, sketchObj):
		'''
		Create distance constraint for an offset spline.
		'''
		if (SKIP_CONSTRAINTS & BIT_DIM_OFFSET_SPLINE == 0): return
		dimensionNode.setGeometry(None)
		return

	def addSketch_OffsetSpline2D(self, offsetSplineNode, sketchObj):
		offsetSplineNode.setGeometry(None)
		return
	def addSketch_SplineHandle2D(self, splineHandleNode, sketchObj):
		splineHandleNode.setGeometry(None)
		return
	def addSketch_SplineHandle3D(self, splineHandleNode, sketchObj):
		splineHandleNode.setGeometry(None)
		return
	def addSketch_Block2D(self, blockNode, sketchObj):
		sourceSketch = blockNode.get('source')
		transformation = blockNode.get('transformation')
		if (sourceSketch.geometry is None): self.getGeometry(sourceSketch)
		for geo in sourceSketch.geometry.Geometry:
			entity = geo.copy()
			entity.transform(transformation.getMatrix())
			sketchObj.addGeometry(geo, geo.Construction)
		blockNode.setGeometry(None)
		logInfo(u"        ... added Block '%s'", blockNode.name)
		return

	def addSketch_BSplineCurve2D(self, splineNode, sketchObj):
		ptIndices = splineNode.get('ptIdcs')
		poleInfo  = splineNode.get('poles')
		poles     = [VEC(p[0] * 10.0, p[1] * 10.0, 0.0) for p in poleInfo['values']]
		mode      = isConstructionMode(splineNode)

		weights  = None
		knots    = None
		periodic = (ptIndices[0] == ptIndices[-1])
		degree   = 3
		multiplicities = None
		checkrational  = False
		bsc = Part.BSplineCurve(poles, weights, knots, periodic, degree, multiplicities, checkrational)
		addSketch2D(sketchObj, bsc, mode, splineNode)
		sketchObj.exposeInternalGeometry(splineNode.sketchIndex)

		logInfo(u"        ... added BSpline = %s", splineNode.sketchIndex)
		return

	def addSketch_Picture(self, imageNode, sketchObj):
		imageNode.setGeometry(None)
		return

	def addSketch_BlockInserts(self, node, sketchObj): return

	def addSketch_5D8C859D(self, node, sketchObj): return
	def addSketch_8EC6B314(self, node, sketchObj): return
	def addSketch_8FEC335F(self, node, sketchObj): return
	def addSketch_DD80AC37(self, node, sketchObj): return

	def handleAssociativeID(self, node):
		label  = node.get('label')
		if (label is None): return
		if (label.typeName == 'BFD09C43'):
			label = label.get('label')
			if (label is None): return
		if (label.typeName == 'Styles'):
			id = label.get('associativeID')
			sketch = node.get('sketch')
			entity = node.geometry
			if (entity is not None):
				if (hasattr(entity, 'Construction') and (entity.Construction == False)):
					sketch.data.sketchEdges[id]  = entity
			setAssociatedSketchEntity(sketch, node, id, label.get('typEntity'))

	def Create_Sketch_Node(self, sketchObj, node):
		if ((node.handled == False) and (node.valid)):
			node.handled = True
			try:
				addSketchObj = getattr(self, u"addSketch_%s" %(node.typeName))
				addSketchObj(node, sketchObj)
				self.handleAssociativeID(node)

			except Exception as e:
				logError(u"ERROR> (%04X): %s - %s", node.index, node.typeName, e)
				logError(traceback.format_exc())
		return

	def addSketch_PostCreateCoincidences(self, sketchObj):
		for vec2D in self.pointDataDict.keys():
			constraints = self.pointDataDict[vec2D]
			if (isOrigo2D(vec2D)):
				fix = (sketchObj.getPoint(-1, 0), -1, 1)
			elif (len(constraints) > 1):
				i = 0
				while ((i < len(constraints)) and ((constraints[i][1] is None) or (constraints[i][2] is None))):
					i += 1
				if (i < len(constraints)):
					fix = constraints[i]
					constraints = constraints[0:i] + constraints[i+1:]
				else:
					point = Part.Point(VEC(vec2D[0], vec2D[1], 0))
					index = sketchObj.addGeometry(point, True)
					fix = (point, index, 1)
			if (len(constraints) > 1):
				for mov in constraints:
					constraint = self.addCoincidentConstraint(fix, mov, sketchObj)
					if (constraint):
						key = ('K%g#%g' %vec2D).replace('-', '_').replace('.', '_')
						self.addConstraint(sketchObj, constraint, key)
		return

	def createSketch(self, sketchNode, strType):
		sketch = self.createEntity(sketchNode, 'Sketcher::SketchObject')
		logInfo(u"    adding %s '%s' ...", strType, sketch.Label)
		sketchNode.setGeometry(sketch)
		geos = []
		dims = []

		for child in sketchNode.get('entities'):
			if (child.typeName.startswith('Geometric_')):
				geos.append(child)
			elif (child.typeName.startswith('Dimension_')):
				dims.append(child)
			else:
				self.Create_Sketch_Node(sketch, child.node)

		for g in geos:
			self.Create_Sketch_Node(sketch, g.node)

		# need to recompute otherwise FreeCAD messes up directions for other constraints!
		FreeCAD.ActiveDocument.recompute()

		for d in dims:
			self.Create_Sketch_Node(sketch, d.node)

		self.addSketch_PostCreateCoincidences(sketch)

		return sketch

	def Create_Point3D(self, ptNode):
		pt = p2v(ptNode)
		point = InventorViewProviders.makePoint(pt, u"Point_%04X" %(ptNode.index))
		ptNode.setGeometry(point)

	def Create_Line3D(self, lnNode):
		pt1 = p2v(lnNode)
		pt2 = p2v(lnNode, 'dirX', 'dirY', 'dirZ')
		line = InventorViewProviders.makeLine(pt1, pt2, u"Line_%04X" %(lnNode.index))
		lnNode.setGeometry(line)

	def Create_Plane(self, plnNode):
		c = p2v(plnNode, 'b_x', 'b_y', 'b_z')
		n = VEC(plnNode.get('n_x'), plnNode.get('n_y'), plnNode.get('n_z'))
		part = InventorViewProviders.makePlane(c, n, u"Plane_%04X" %(plnNode.index))
		plnNode.setGeometry(part)

	def Create_SketchBlock(self, sketchNode):
		if (self.pointDataDict is None):
			self.pointDataDict = {}
			sketch2D = self.createSketch(sketchNode, '2D-Sketch')
			self.pointDataDict = None
		else:
			sketchBlock = self.createSketch(sketchNode, 'Sketch-Block')
			hide(sketchBlock)
		return

	def Create_Sketch2D(self, sketchNode):
		self.pointDataDict = {}
		sketch2D = self.createSketch(sketchNode, '2D-Sketch')
		self.pointDataDict = None

		if (self.root): self.root.addObject(sketch2D)

		sketch2D.Placement = getPlacement(sketchNode.get('transformation'))

		return

	def Create_Sketch3D(self, sketchNode):
		sketch3D = InventorViewProviders.makeSketch3D(sketchNode.name)
		logInfo(u"    adding 3D-Sketch '%s' ...", sketch3D.Label)
		sketchNode.setGeometry(sketch3D)
		sketch3D.Placement = PLC(CENTER, ROT(DIR_Z, 0.0), CENTER)
		geos = []
		dims = []
		self.pointDataDict = {}

		for child in sketchNode.get('entities'):
			if (child.typeName.startswith('Geometric_')):
				geos.append(child)
			elif (child.typeName.startswith('Dimension_')):
				dims.append(child)
			else:
				self.Create_Sketch_Node(sketch3D, child.node)

		for g in geos:
			self.Create_Sketch_Node(sketch3D, g.node)

## TODO: add Constraints to Sketch3D
#		for d in dims:
#			self.Create_Sketch_Node(edges, d.node)

		if (self.root):
			self.root.addObject(sketch3D)

		self.pointDataDict = None

		return

	def Create_FxExtrude_New(self, padNode, sectionNode, name):
		properties = padNode.get('properties')
		patch      = getProperty(properties, 0x01)               # The selected edges from a sketch
		direction  = getProperty(properties, 0x02)               # The direction of the extrusion
		reversed   = getPropertyValue(properties, 0x03, 'value') # If the extrusion direction is inverted
		dimLength1 = getProperty(properties, 0x04)               # The length of the extrusion in direction 1
		dimAngle   = getProperty(properties, 0x05)               # The taper outward angle  (doesn't work properly in FreeCAD)
		extend     = getPropertyValue(properties, 0x06, 'value') #
		midplane   = getPropertyValue(properties, 0x07, 'value')
		# = getProperty(properties, 0x0F)#               FeatureDimensions
		surface    = getProperty(properties, 0x10)               # SurfaceBody
		# = getProperty(properties, 0x13)#               Parameter 'RDxVar0'=1
		# = getPropertyValue(properties, 0x14, 'value')# ParameterBoolean=False
		# = getProperty(properties, 0x15)#               CEFD3973_Enum=0
		# = getPropertyValue(properties, 0x16, 'value')# ParameterBoolean=True
		# = getProperty(properties, 0x17)#               BoundaryPatch
		solid      = getProperty(properties, 0x1A)
		dimLength2 = getProperty(properties, 0x1B)               # The length of the extrusion in direction 2

		# Extends 1x distance, 2x distance, to, to next, between, all

		dir = VEC(direction.get('dirX'), direction.get('dirY'), direction.get('dirZ'))

		len1 = getMM(dimLength1)
		len2 = getMM(dimLength2)
		pad = None
		if (extend == 5): # 'ALL'
			if (solid is not None):
				len1 = self.getLength(solid, dir)
			else:
				len1 = self.getLength(surface, dir)
		if (len1 > 0):
			baseName = sectionNode.name
			pad = newObject('Part::Extrusion', name)

			if (midplane):
				len1 = len1 / 2.0
				len2 = len1
				logInfo(u"        ... based on '%s' (symmetric len=%s mm) ...", baseName, len1)
			elif (len2 > 0):
				logInfo(u"        ... based on '%s' (rev=%s, len=%s mm, len2=%s mm) ...", baseName, reversed, len1, len2)
			else:
				logInfo(u"        ... based on '%s' (rev=%s, len=%s mm) ...", baseName, reversed, len1)

			pad.Base      = self.createBoundary(patch)
			pad.Solid     = solid is not None # FIXME!!
			pad.Reversed  = reversed
			pad.Dir       = dir
			pad.Symmetric = midplane
			angle = setParameter(pad, 'TaperAngle', dimAngle, getGRAD)
			if (extend == 5):
				pad.LengthFwd = len1
				pad.LengthRev = len2
			else:
				len1  = setParameter(pad, 'LengthFwd',  dimLength1, getMM)
				len2  = setParameter(pad, 'LengthRev',  dimLength2, getMM)
			setDefaultViewObjectValues(pad)

			pad.Placement.Base -= dir * len2

			hide(pad.Base)
		else:
			logWarning(u"        can't create new extrusion '%s' - (%04X): %s properties[04] is None!", name, padNode.index, padNode.typeName)
		return pad

	def createFxExtrude_Operation(self, padNode, sectionNode, name, nameExtension, className):
		properties = padNode.get('properties')
		baseRef   = getProperty(properties, 0x1A)
		boolean    = None

		if (baseRef is None):
			logWarning(u"    Can't find base info for (%04X): %s - not yet created!", padNode.index, name)
			return None
		tool = self.Create_FxExtrude_New(padNode, sectionNode, name + nameExtension)
		base = self.findBase(baseRef)
		if (base is not None):
			if (tool is not None): # no need to raise a warning as it's already done!
				return self.createBoolean(className, name, base, [tool])
			logWarning(u"        FxExtrude '%s': can't find/create tools object - executing %s!", name, className)
			return base
		logWarning(u"        FxExtrude '%s': can't find/create base object - executing %s!", name, className)
		return tool

	def Create_FxLink2Body(self, fxNode):
		properties = fxNode.get('properties')
		number     = getProperty(properties, 0x00) # Parameter 'RDxVar3'=0002 # number for the body
		idxFx1     = getProperty(properties, 0x01) # Parameter 'RDxVar4'=0350
		idxSource  = getProperty(properties, 0x02) # Parameter 'RDxVar5'=0351
		body       = getProperty(properties, 0x03) # SurfaceBody 'Srf5'

		fx1 = fxNode.segment.indexNodes[idxFx1.getValue().x]
		source = fxNode.segment.indexNodes[idxSource.getValue().x]

		surface = None
		if (surface is not None):
			self.addSurfaceBody(fxNode, surface, body)

		return surface

	def Create_FxRevolve(self, revolveNode):
		participants = revolveNode.getParticipants()
		revolution = None

		if (participants):
			properties = revolveNode.get('properties')
			pathName   = participants[0].name
			operation  = getProperty(properties, 0x00) # PartFeatureOperation
			profile1   = getProperty(properties, 0x01) # BoundaryPatch
			lineAxis   = getProperty(properties, 0x02) # Line3D
			extend1    = getProperty(properties, 0x03) # ExtentType
			angle1     = getProperty(properties, 0x04) # Parameter
			direction  = getProperty(properties, 0x05) # PartFeatureExtentDirection
			#= getProperty(properties, 0x06) # ???
			#= getProperty(properties, 0x07) # FeatureDimensions
			surface    = getProperty(properties, 0x08) # SurfaceBody
			#= getProperty(properties, 0x09) # CEFD3973_Enum
			#= getProperty(properties, 0x0A) # ParameterBoolean
			#= getProperty(properties, 0x0B) # BoundaryPatch
			#= getProperty(properties, 0x0C) # ParameterBoolean
			#= getProperty(properties, 0x0D) # ???
			#= getProperty(properties, 0x0E) # ???
			#= getProperty(properties, 0x0F) # ???
			#= getProperty(properties, 0x10) # ParameterBoolean
			angle2     = getProperty(properties, 0x12) # Parameter
			extend2    = getProperty(properties, 0x13) # ExtentType

			boundary   = self.createBoundary(profile1)

			base       = p2v(lineAxis)
			axis       = p2v(lineAxis, 'dirX', 'dirY', 'dirZ')
			solid      = (surface is None)

			if (boundary):
				FreeCAD.ActiveDocument.recompute()
				if (extend1.get('value') == 1): # 'Direction' => AngleExtent
					if (angle2 is None):
						if (direction.get('value') == 0): # positive
							logInfo(u"    ... based on '%s' (alpha=%s) ...", pathName, angle1.getValue())
							revolution = self.createRevolve(revolveNode.name, angle1, 0.0, boundary, axis, base, solid, True)
						elif (direction.get('value') == 1): # negative
							logInfo(u"    ... based on '%s' (alpha=%s, inverted) ...", pathName, angle1.getValue())
							revolution = self.createRevolve(revolveNode.name, 0.0, angle1, boundary, axis, base, solid, False)
						elif (direction.get('value') == 2): # symmetric
							alpha = getGRAD(angle1) / 2
							logInfo(u"    ... based on '%s' (alpha=%s, symmetric) ...", pathName, angle1.getValue())
							revolution = self.createRevolve(revolveNode.name, alpha, alpha, boundary, axis, base, solid, True)
					else:
						logInfo(u"    ... based on '%s' (alpha=%s, beta=%s) ...", pathName, angle1.getValue(), angle2.getValue())
						revolution = self.createRevolve(revolveNode.name, angle1, angle2, boundary, axis, base, solid, True)
				elif (extend1.get('value') == 3): # 'Path' => FullSweepExtend
					logInfo(u"    ... based on '%s' (full) ...", pathName)
					revolution = self.createRevolve(revolveNode.name, 360.0, 0.0, boundary, axis, base, solid, True)
			else:
				logError(u"    Can't create revolution '%s' out of boundary (%04X)!", revolveNode.name,  profile1.index)
			if (revolution is not None): self.addBody(revolveNode, revolution, 0x11, 0x08)
		return revolution

	def Create_FxExtrude(self, extrudeNode):
		name = extrudeNode.name

		participants = extrudeNode.getParticipants()

		if (participants):
			sectionNode = participants[0].node
			properties = extrudeNode.get('properties')
			typ = getProperty(properties, 0x02)
			obj3D = None
			if (typ):
				# Operation new (0x0001), cut/difference (0x002), join/union (0x003) intersection (0x0004) or surface(0x0005)
				operation = getPropertyValue(properties, 0x00, 'value')
				if (operation == FreeCADImporter.FX_EXTRUDE_NEW):
					padGeo = self.Create_FxExtrude_New(extrudeNode, sectionNode, name)
				elif (operation == FreeCADImporter.FX_EXTRUDE_CUT):
					padGeo = self.createFxExtrude_Operation(extrudeNode, sectionNode, name, '_Cut', 'Cut')
				elif (operation == FreeCADImporter.FX_EXTRUDE_JOIN):
					padGeo = self.Create_FxExtrude_New(extrudeNode, sectionNode, name)
				elif (operation == FreeCADImporter.FX_EXTRUDE_INTERSECTION):
					padGeo = self.createFxExtrude_Operation(extrudeNode, sectionNode, name, '_Intersection', 'MultiCommon')
				elif (operation == FreeCADImporter.FX_EXTRUDE_SURFACE):
					padGeo = self.Create_FxExtrude_New(extrudeNode, sectionNode, name)
				else:
					padGeo = None
					logError(u"    ERROR Don't know how to operate PAD=%s for (%04X): %s", operation, extrudeNode.index, extrudeNode.typeName)

				if (padGeo):
					self.addBody(extrudeNode, padGeo, 0x1A, 0x10)
					if (self.root):
						self.root.addObject(padGeo)

	def Create_FxPatternPolar(self, patternNode):
		name         = patternNode.name
		properties   = patternNode.get('properties')
		participants = patternNode.get('participants')
		fxDimData    = getProperty(properties, 0x05) # FeatureDimensions
		solidRef     = getProperty(properties, 0x09) # ObjectCollection
		countRef     = getProperty(properties, 0x0C) # Parameter
		angleRef     = getProperty(properties, 0x0D) # Parameter
		axisData     = getProperty(properties, 0x0E) # AxisEntity

		if (len(participants) == 0):
			participants = []
			label = patternNode.get('label')
			ref2 = label.get('ref_2')
			lst0 = ref2.get('lst0') or []
			for ref in lst0:
				if (ref.name in self.bodyNodes):
					participants.append(self.bodyNodes[lst0[0].name])
		if (len(participants) > 0):
			geos  = []
			count = getNominalValue(countRef)
			angle = Angle(getNominalValue(angleRef), pi/180.0, u'\xb0')
			center = p2v(axisData)
			axis   = p2v(axisData, 'dirX', 'dirY', 'dirZ')
			logInfo(u"        ... count=%d, angle=%s ...", count, angle)
			namePart = name
			if (len(participants) > 1):
				namePart = name + '_0'

			for baseRef in participants:
				cutGeo = None
				logInfo(u"        .... Base = '%s'", baseRef.name)
				baseGeo = self.getGeometry(baseRef)
				if (baseGeo is None):
					baseGeo = self.findBase(baseRef)
				if (baseGeo is not None):
					if (baseGeo.isDerivedFrom('Part::Cut')):
						cutGeo = baseGeo
						baseGeo = cutGeo.Tool
					patternGeo = Draft.makeArray(baseGeo, center, angle.getGRAD(), count, None, namePart)
					setParameter(patternGeo, 'NumberPolar', countRef)
					setParameter(patternGeo, 'Angle', angle, getGRAD)
					patternGeo.Axis = axis
					setDefaultViewObjectValues(patternGeo)
					geos.append(patternGeo)
				namePart = '%s_%d' % (name, len(geos))
			patternGeo = self.combineGeometries(geos, patternNode)
			if (patternGeo is not None):
				if (cutGeo):
					cutGeo.Tool = patternGeo
				else:
					self.addSolidBody(patternNode, patternGeo, solidRef)
		return

	def adjustMidplane(self, pattern, direction, distance, fitted, count):
		d = getNominalValue(distance)
		base = p2v(direction, 'dirX', 'dirY', 'dirZ') * d
		pattern.Placement.Base = pattern.Placement.Base - base
		return

	def Create_FxPatternRectangular(self, patternNode):
		offset = 0
		if (getFileVersion() > 2016): offset = 6
		name          = patternNode.name
		properties    = patternNode.get('properties')
		participants  = patternNode.get('participants')
		solidRef      = getProperty(properties, 0x09 + offset)
		count1Ref     = getProperty(properties, 0x0C + offset)
		count2Ref     = getProperty(properties, 0x0D + offset)
		distance1Ref  = getProperty(properties, 0x0E + offset)
		distance2Ref  = getProperty(properties, 0x0F + offset)
		dir1Ref       = getProperty(properties, 0x10 + offset)
		dir2Ref       = getProperty(properties, 0x11 + offset)
		fitted1Ref    = getProperty(properties, 0x12 + offset)
		fitted2Ref    = getProperty(properties, 0x13 + offset)
		#= getProperty(properties, 0x14 + offset)
		#= getProperty(properties, 0x15 + offset)
		adjustDir1Ref = getProperty(properties, 0x16 + offset)
		adjustDir2Ref = getProperty(properties, 0x17 + offset)
		midplane1Ref  = getProperty(properties, 0x18 + offset)
		midplane2Ref  = getProperty(properties, 0x19 + offset)

		if (len(participants) == 0):
			participants = []
			label = patternNode.get('label')
			ref2 = label.get('ref_2')
			lst0 = ref2.get('lst0') or []
			for ref in lst0:
				if (ref.name in self.bodyNodes):
					participants.append(self.bodyNodes[lst0[0].name])
		if (len(participants) > 0):
			geos  = []
			if (distance1Ref is None):
				logWarning(u"    FxPatternRectangular '%s': Can't create array along a spline in 1st direction!", name)
				return
			count1, dir1 = getCountDir(distance1Ref, count1Ref, dir1Ref, fitted1Ref)
			count2, dir2 = getCountDir(distance2Ref, count2Ref, dir2Ref, fitted2Ref)

			if (count2 == 1):
				logInfo(u"        .... 1. %d x (%g,%g,%g) ...", count1, dir1.x, dir1.y, dir1.z)
			else:
				logInfo(u"        .... 1. %d x (%g,%g,%g); 2. %d x (%g,%g,%g) ...", count1, dir1.x, dir1.y, dir1.z, count2, dir2.x, dir2.y, dir2.z)

			namePart = name
			if (len(participants) > 1):
				namePart = name + '_0'

			for baseRef in participants:
				cutGeo = None
				logInfo(u"        .... Base = '%s'", baseRef.name)
				baseGeo = self.getGeometry(baseRef)
				if (baseGeo is None): baseGeo = self.findBase(baseRef)
				if (baseGeo is not None):
					if (baseGeo.isDerivedFrom('Part::Cut')):
						cutGeo = baseGeo
						if (cutGeo.Tool): baseGeo = cutGeo.Tool
					patternGeo = Draft.makeArray(baseGeo, dir1, dir2, count1, count2, namePart)
					setParameter(patternGeo, 'NumberX', count1Ref)
					setParameter(patternGeo, 'NumberY', count2Ref)

					if (isTrue(midplane1Ref)): self.adjustMidplane(patternGeo, dir1Ref, distance1Ref, fitted1Ref, count1Ref)
					if (isTrue(midplane2Ref)): self.adjustMidplane(patternGeo, dir2Ref, distance2Ref, fitted2Ref, count2Ref)

					setDefaultViewObjectValues(patternGeo)
					geos.append(patternGeo)
				namePart = '%s_%d' % (name, len(geos))
			patternGeo = self.combineGeometries(geos, patternNode)
			if (patternGeo is not None):
				if (cutGeo):
					cutGeo.Tool = patternGeo
				else:
					self.addSolidBody(patternNode, patternGeo, solidRef)
		return

	def Create_FxCombine(self, combineNode):
		name          = combineNode.name
		properties    = combineNode.get('properties')
		bodyRef       = getProperty(properties, 0x00)
		sourceData    = getProperty(properties, 0x01)
		operationData = getProperty(properties, 0x02)
		keepToolData  = getProperty(properties, 0x03) # Boolean
		operation = operationData.get('value')
		if (operation == FreeCADImporter.FX_EXTRUDE_CUT):
			className = 'Cut'
		elif (operation == FreeCADImporter.FX_EXTRUDE_JOIN):
			className = 'MultiFuse'
		elif (operation == FreeCADImporter.FX_EXTRUDE_INTERSECTION):
			className = 'MultiCommon'
		else:
			logWarning(u"        FxCombine: don't know how to %s - (%04X): %s!", operationData.node.getValueText(), combineNode.index, combineNode.typeName)
			return
		baseGeo       = self.findBase(bodyRef)
		toolGeos      = self.findGeometries(sourceData.get('objectCollection'))
		if ((baseGeo is not None) and (len(toolGeos) > 0)):
			cmbineGeo = self.createBoolean(className, name, baseGeo, toolGeos)
			if (cmbineGeo is None):
				logError(u"        ....Failed to create combination!")
			else:
				self.addSolidBody(combineNode, cmbineGeo, bodyRef)
		return

	def Create_FxMirror(self, mirrorNode):
		name          = mirrorNode.name
		properties    = mirrorNode.get('properties')
		planeRef      = getProperty(properties, 0x0C)
		base          = p2v(planeRef, 'b_x', 'b_y', 'b_z')
		normal        = p2v(planeRef, 'n_x', 'n_y', 'n_z')
		logInfo(u"    adding FxMirror '%s' ...", name)

		mirrors = []
		mirrorGeo = None

		participants = self.resolveParticiants(mirrorNode)
		for n, baseGeo in enumerate(participants):
			if (baseGeo is not None):
				nameGeo = u"%s_%d" %(name, n)
				mirrorGeo = newObject('Part::Mirroring', nameGeo)
				mirrorGeo.Source = baseGeo
				mirrorGeo.Base   = base
				mirrorGeo.Normal = normal
				adjustViewObject(mirrorGeo, baseGeo)
				mirrors.append(mirrorGeo)
		if (len(mirrors) > 1):
			mirrorGeo = self.createBoolean('MultiCommon', name, mirrors[0], mirrors[1:])
			if (mirrorGeo is None):
				logError(u"        ....Failed to create combination!")
		if (mirrorGeo):
			self.addSolidBody(mirrorNode, mirrorGeo, getProperty(properties, 0x09))

		return

	def Create_FxHole(self, holeNode):
		name           = holeNode.name
		definition     = holeNode.get('label')
		properties     = holeNode.get('properties')
		holeType       = getProperty(properties, 0x00)
		holeDiam_1     = getProperty(properties, 0x01) # Parameter
		holeDepth_1    = getProperty(properties, 0x02) # Parameter
		holeDiam_2     = getProperty(properties, 0x03) # Parameter
		holeDepth_2    = getProperty(properties, 0x04) # Parameter
		holeAngle_2    = getProperty(properties, 0x05) # Parameter
		pointAngle     = getProperty(properties, 0x06) # Parameter
		centerPoints   = getProperty(properties, 0x07)	# <=> HoleCenterPoints == "by Sketch"
		transformation = getProperty(properties, 0x08)
		termination    = getProperty(properties, 0x09)
		# 0x0A ???
		# 0x0B ???
		# 0x0C ???
		#    = getProperty(properties, 0x0D)    # <=> Plane
		#    = getProperty(properties, 0x0E)    # <=> termination = "To"
		#    = getProperty(properties, 0x0F)    # <=> termination = "To"
		direction     = getProperty(properties, 0x10)
		#    = getProperty(properties, 0x11)    # boolParam
		# 0x12 ???
		fxDimensions  = getProperty(properties, 0x13)
		threadDiam    = getProperty(properties, 0x14) # Parameter
		#    = getProperty(properties, 0x15)	# <=> placement == "linear"
		#    = getProperty(properties, 0x16)	#
		# 0x17 ???
		baseRef      = getProperty(properties, 0x18)
		vec3D         = None

		self.resolveParticiants(holeNode) # No need to take further care on created objectes.

		if (holeType is not None):
			base = self.findBase(baseRef)

			if (base is None):
				logWarning(u"    Can't find base info for (%04X): %s - not yet created!", holeNode.index, name)
			else:
				#TODO: InventorViewProviders.makeHole()
				placement = getPlacement(transformation)
				holeGeo   = None
				if (centerPoints):
					offset = centerPoints.get('points')[0]
					vec3D = placement.toMatrix().multiply(p2v(offset))
				if (holeType.get('value') == FreeCADImporter.FX_HOLE_DRILLED):
					logInfo(u"    adding drilled FxHole '%s' ...", name)
					geos, h = self.createCylinder(name + '_l', holeDiam_1, holeDepth_1, pointAngle)
					if (len(geos) > 1):
						geo1 = self.createBoolean('MultiFuse', name + '_h', geos[0], geos[1:])
						setPlacement(geo1, placement, vec3D)
						holeGeo = self.createBoolean('Cut', name, base, [geo1])
					else:
						setPlacement(geos[0], placement, vec3D)
						holeGeo = self.createBoolean('Cut', name, base, geos[0:1])
					if (holeGeo is None):
						logError(u"        ... Failed to create hole!")
				else:
					geos, h1 = self.createCylinder(name + '_l', holeDiam_1, holeDepth_1, pointAngle)
					if (holeType.get('value') == FreeCADImporter.FX_HOLE_SINK):
						logInfo(u"    adding counter sink FxHole '%s' ...", name)
						geo2, h2 = self.createCone(name + '_2', holeDiam_2, holeAngle_2, holeDiam_1)
						holeGeo = self.createBoolean('MultiFuse', name + '_h', geo2, geos)
						setPlacement(holeGeo, placement, vec3D)
						holeGeo = self.createBoolean('Cut', name, base, [holeGeo])
						if (holeGeo is None):
							logError(u"        ... Failed to create counter sink hole!")
					elif (holeType.get('value') == FreeCADImporter.FX_HOLE_BORED):
						logInfo(u"    adding counter bored FxHole '%s' ...", name)
						geo2, h2 = self.createCylinder(name + '_2', holeDiam_2, holeDepth_2, None)
						holeGeo = self.createBoolean('MultiFuse', name + '_h', geo2[0], geos)
						setPlacement(holeGeo, placement, vec3D)
						holeGeo = self.createBoolean('Cut', name, base, [holeGeo])
						if (holeGeo is None):
							logError(u"        ... Failed to create counter bored hole!")
					elif (holeType.get('value') == FreeCADImporter.FX_HOLE_SPOT):
						logInfo(u"    adding spot face FxHole '%s' ...", name)
						geo2, h2 = self.createCylinder(name + '_2', holeDiam_2, holeDepth_2, None)
						holeGeo = self.createBoolean('MultiFuse', name + '_h', geo2[0], geos)
						setPlacement(holeGeo, placement, vec3D)
						holeGeo = self.createBoolean('Cut', name, base, [holeGeo])
						if (holeGeo is None):
							logError(u"        ... Failed to create spot face hole!")
					else:
						logError(u"ERROR> Unknown hole type %s!", holeType.get('value'))

				if (holeGeo is not None):
					self.addSolidBody(holeNode, holeGeo, getProperty(properties, 0x18))

		return

	def Create_FxClient(self, clientNode):
		# create a subfolder
		name = InventorViewProviders.getObjectName(clientNode.name)
		if ((name is None) or (len(name) == 0)):
			name = node.typeName

		fx = createGroup(name)
		# add/move all objects to this folder
		for geo in self.resolveParticiants(clientNode):
			fx.addObject(geo)
		return

	def Create_FxLoft(self, loftNode):
		properties    = loftNode.get('properties')
		sections1     = getProperty(properties, 0x00) # LoftSections
		operation     = getProperty(properties, 0x01) # PartFeatureOperation=Surface
		closed        = getProperty(properties, 0x02) # ParameterBoolean =0
		#= getProperty(properties, 0x03) #
		#= getProperty(properties, 0x04) #
		#= getProperty(properties, 0x05) #
		surface       = getProperty(properties, 0x06) #
		sections2     = getProperty(properties, 0x07) # LoftSections
		#= getProperty(properties, 0x08) #
		ruled          = getProperty(properties, 0x09) # ParameterBoolean =0
		loftType       = getProperty(properties, 0x0A) # LoftType=AreaLoft
		#= getProperty(properties, 0x0B) # E558F428
		#= getProperty(properties, 0x0C) # FeatureDimensions

		sections = self.collectSections(loftNode, 'loft')

		if (len(sections) > 0):
			if (loftType.get('value') == 1): # Centerline
				# this is a sweep between two surfaces!
				loftGeo            = self.createEntity(loftNode, 'Part::Sweep')
				loftGeo.Sections   = sections[0:1] + sections[2:]
				loftGeo.Spine      = (sections[1], ['Edge1'])
				loftGeo.Frenet     = False
				loftGeo.Transition = 'Transformed'
			else:
			#elif (loftType.get('value') == 0): # Rails
			#elif (loftType.get('value') == 2): # AreaLoft
			#elif (loftType.get('value') == 3): # RegularLoft
				loftGeo          = self.createEntity(loftNode, 'Part::Loft')
				loftGeo.Sections = sections[-1:] + sections[0:-2] + sections[-2:-1]
				loftGeo.Ruled    = isTrue(ruled)
				loftGeo.Closed   = isTrue(closed)
			loftGeo.Solid    = surface is None
			hide(sections)
			setDefaultViewObjectValues(loftGeo)
			self.addBody(loftNode, loftGeo, 0x0D, 0x06)
		return

	def Create_FxLoftedFlange(self, fxNode):
		defNode = fxNode.get('properties')[0]
		defNode.handled = True
		bendNode   = fxNode.get('properties')[0]
		properties     = defNode.get('properties')
		surface        = getProperty(properties, 0x00) # SurfaceBody 'Solid1'
		proxy1         = getProperty(properties, 0x01) # FaceBoundProxy
		proxy2         = getProperty(properties, 0x02) # FaceBoundProxy
		#= getProperty(properties, 0x03) # Parameter 'Thickness'=4mm
		bendRadius     = getProperty(properties, 0x04) # Parameter 'd11'=4mm
		#= getProperty(properties, 0x05) # 5E50B969_Enum=1
		#= getProperty(properties, 0x06) # ParameterBoolean=False
		#= getProperty(properties, 0x07) # FacetControl=1
		facetTolerance = getProperty(properties, 0x08) # Parameter 'd6'=4mm
		#= getProperty(properties, 0x09)
		#= getProperty(properties, 0x0A) # ParameterBoolean=False
		#= getProperty(properties, 0x0B)
		#= getProperty(properties, 0x0C) # FeatureDimensions
		#= getProperty(properties, 0x0D) # A96B5992
		#= getProperty(properties, 0x0E) # 90B64134
#		edgeSet        = getProperty(properties, 0x0F) # EdgeCollectionProxy

		boundary1 = self.createBoundary(proxy1)
		boundary2 = self.createBoundary(proxy2)
#		edges     = self.getEdgesFromSet(edgeSet)

		sections         = [boundary1, boundary2]
		loftGeo          = self.createEntity(defNode, 'Part::Loft')
		loftGeo.Sections = sections
		loftGeo.Ruled    = True  #isTrue(ruled)
		loftGeo.Closed   = False #isTrue(closed)
		loftGeo.Solid    = False #

		hide(sections)
		setDefaultViewObjectValues(loftGeo)
		self.addSurfaceBody(defNode, loftGeo, surface)
		return

	def Create_FxSweep(self, sweepNode):
		properties = sweepNode.get('properties')
		definition  = sweepNode.get('label')
		solid      = (definition.typeName == 'Label')
		boundary   = getProperty(properties, 0x00)
		proxy1     = getProperty(properties, 0x01) # FaceBoundProxy or FaceBoundOuterProxy
		#= getProperty(properties, 0x02) # PartFeatureOperation or 90874D63
		taperAngle = getProperty(properties, 0x03) # Parameter
		#= getProperty(properties, 0x04) # ExtentType
		#= getProperty(properties, 0x05) # ???
		#= getProperty(properties, 0x07) # FeatureDimensions
		#= getProperty(properties, 0x08) # SweepType=Path
		frenet     = getProperty(properties, 0x09) # SweepProfileOrientation, e.g. 'NormalToPath', other not yet supported by FreeCAD
		scaling    = getProperty(properties, 0x0A) # SweepProfileScaling, e.g. 'XY', other not yet supported by FreeCAD
		proxy2     = getProperty(properties, 0x0B) # FaceBoundProxy
		#= getProperty(properties, 0x0C): ???
		#= getProperty(properties, 0x0D): ???

		skip   = []

		path = self.createBoundary(proxy1)
		if (path is None):
			profile = sweepNode.getParticipants()[1]
			path = self.getGeometry(profile)

		edges = self.getEdges(path)
		if (len(edges) > 0):
			sections          = [self.createBoundary(boundary)]
			sweepGeo          = self.createEntity(sweepNode, 'Part::Sweep')
			sweepGeo.Sections = sections
			sweepGeo.Spine    = (path, edges)
			sweepGeo.Solid    = solid
			#sweepGeo.Frenet   = (frenet.getValueText() == u"'ParallelToOriginalProfile'")
			hide(sections)
			hide(path)
			setDefaultViewObjectValues(sweepGeo)
			self.addBody(sweepNode, sweepGeo, 0x0F, 0x06)
		return

	def Create_FxThicken(self, thickenNode):
		properties      = thickenNode.get('properties')
		operation       = getProperty(properties, 0x01) # operation
		negativeDir     = getProperty(properties, 0x02) # negative direction
		symmetricDir    = getProperty(properties, 0x03) # symmetric direction
		# = getProperty(properties, 0x04) # boolean parameter
		#distance        = getProperty(properties, 0x06) # distance (may be None -> get from feature dimension]
		useInputSurface = getProperty(properties, 0x07) # boolean parameter (True if 0x00 is None!]
		featureDim      = getProperty(properties, 0x09) # feature dimension
		distance        = featureDim.get('fxDimensions')[0].get('parameter')
		verticalSurface = getProperty(properties, 0x0A) # boolean parameter
		aprxTol         = getProperty(properties, 0x0C) # approximation tolerance
		aprxType        = getProperty(properties, 0x0D) # approximation type
		aprxOptimize    = getProperty(properties, 0x0E) # Enum_637B1CC1
		solid           = getProperty(properties, 0x0F) # solid
		blending        = getProperty(properties, 0x10) # boolean parameter
		#= getProperty(properties, 0x11) # boolean parameter
		#= getProperty(properties, 0x12) # ???
		sourceGeos    = {}
		sourceOffsets = {}
		if (isTrue(useInputSurface)):
			inputSurface    = getProperty(properties, 0x05) # SurfaceBody => "Quilt"
			source = self.findSurface(inputSurface)
			if (source):
				sourceGeos[source.Label]    = source
				sourceOffsets[source.Label] = 0.0
		else:
			faceOffsets   = getProperty(properties, 0x00) # faceOffsets
			for faceOffset in faceOffsets.get('lst0'):
				if (faceOffset.typeName == 'FacesOffset'):
					face    = faceOffset.get('faces').get('faces')[0]
					surface = thickenNode.segment.indexNodes[face.get('indexRefs')[0]]
					surface = surface.get('surface')
					source = self.findSurface(surface)
					if (source):
						sourceGeos[source.Label]    = source
						sourceOffsets[source.Label] = getMM(faceOffset.get('offset'))
		for key in sourceGeos.keys():
			source = sourceGeos[key]
			thickenGeo = self.createEntity(thickenNode, 'Part::Offset')
			thickenGeo.Source = source
			if (isTrue(negativeDir)):
				setParameter(thickenGeo, 'Value', distance, getMM, -1.0)
			else:
				#TODO: symmetricDir - create a fusion of two thicken geometries
				setParameter(thickenGeo, 'Value', distance, getMM)
			thickenGeo.Mode = 'Skin'          # {Skin, Pipe, RectoVerso}
			thickenGeo.Join = 'Intersection'  # {Arc, Tangent, Intersection}
			thickenGeo.Intersection = False
			thickenGeo.SelfIntersection = False
			if (hasattr(thickenGeo, 'Fill')): thickenGeo.Fill = solid is not None
			offset = -sourceOffsets[key]
			if ((offset != 0.0) and (len(source.Shape.Faces)>0)):
				normal = source.Shape.Faces[0].normalAt(0,0)
				thickenGeo.Placement.Base += source.Placement.Base - normal * offset
			adjustViewObject(thickenGeo, source)
			if (isTrue(verticalSurface)):
				self.addBody(thickenNode, thickenGeo, 0x0F, 0x08)
			else:
				self.addBody(thickenNode, thickenGeo, 0x0F, 0x0B)
		hide(list(sourceGeos.values()))
		return

	def Create_FxCoil(self, coilNode):
		properties  = coilNode.get('properties')
		operation   = getProperty(properties, 0x00) # PartFeatureOperation=Join
		profile     = getProperty(properties, 0x01) # BoundaryPatch
		axis        = getProperty(properties, 0x02) # Line3D - (-1.49785,-1.08544,1.11022e-16) - (-1.49785,-0.085438,1.11022e-16)
		negative    = getProperty(properties, 0x03) # ParameterBoolean 'AxisDirectionReversed'
		rotate      = getProperty(properties, 0x04) # RotateClockwise clockwise=0
		coilType    = getProperty(properties, 0x05) # EnumCoilType=010003, u32_0=0
		pitch       = getProperty(properties, 0x06) # Parameter 'd21'=1.1176mm
		height      = getProperty(properties, 0x07) # Parameter 'd22'=25.4mm
		revolutions = getProperty(properties, 0x08) # Parameter 'd23'=2
		taperAngle  = getProperty(properties, 0x09) # Parameter 'd24'=0°
		startIsFlat = getProperty(properties, 0x0A) # ParameterBoolean=False
		startTrans  = getProperty(properties, 0x0B) # Parameter 'd15'=90°
		startFlat   = getProperty(properties, 0x0C) # Parameter 'd16'=90°
		endIsFlat   = getProperty(properties, 0x0D) # ParameterBoolean=False
		endTrans    = getProperty(properties, 0x0E) # Parameter 'd17'=0°
		endFlat     = getProperty(properties, 0x0F) # Parameter 'd18'=0°
		# = getProperty(properties, 0x10) # ???
		surface     = getProperty(properties, 0x11) # SurfaceBody 'Surface1'
		# = getProperty(properties, 0x12) # FeatureDimensions
		solid       = getProperty(properties, 0x13) # SolidBody 'Solid1'

		boundary = self.createBoundary(profile)
		base    = p2v(axis)
		dir     = p2v(axis, 'dirX', 'dirY', 'dirZ').normalize()
		if (isTrue(negative)): dir = dir.negative()

		sweepGeo = self.createEntity(coilNode, 'Part::Sweep')
		r = revolutions.getValue().x
		if (coilType.get('value') == 3):
			coilGeo = newObject('Part::Spiral', sweepGeo.Name + '_coil')
			setParameter(coilGeo, 'Growth', pitch, getMM)
			setParameter(coilGeo, 'Rotations', revolutions)
			if (isTrue(rotate)): dir = dir.negative()
		else:
			coilGeo = newObject('Part::Helix', sweepGeo.Name + '_coil')
			if (coilType.get('value') == 0):   # PitchAndRevolution
				setParameter(coilGeo, 'Pitch', pitch, getMM)
				coilGeo.Height = getMM(pitch) * revolutions.getValue().x
				coilGeo.setExpression('Height', "%s * %s" %(pitch.get('alias'), revolutions.get('alias')))
			elif (coilType.get('value') == 1): # RevolutionAndHeight
				coilGeo.Pitch  = height.getNominalValue() /  revolutions.getNominalValue()
				coilGeo.setExpression("Pitch", "%s / %s" %(height.get('alias'), revolutions.get('alias')))
				setParameter(coilGeo, 'Height', height, getMM)
			else:
				setParameter(coilGeo, 'Pitch', pitch, getMM)
				setParameter(coilGeo, 'Height', height, getMM)
			coilGeo.LocalCoord = 1 - rotate.get('clockwise') # 0 = "Left handed"; 1= "Right handed"
			setParameter(coilGeo, 'Angle', taperAngle, getGRAD)
		c   = boundary.Shape.BoundBox.Center
		r   = c.distanceToLine(base, dir) # Helix-Radius
		b   = CENTER.projectToLine(c-base, dir).normalize()
		z   = DIR_Z
		rot = ROT(z.cross(dir), degrees(z.getAngle(dir)))
		p1  = PLC((c + b*r), rot, CENTER)
		x   = rot.multVec(-DIR_X)
		p2  = PLC(CENTER, ROT(z, degrees(x.getAngle(b))), CENTER)
		coilGeo.Radius    = r
		coilGeo.Placement = p1.multiply(p2)

		#TODO: add flat start / end to coil wire
		if (isTrue(startIsFlat)):
			pass
		if (isTrue(endIsFlat)):
			pass

		sweepGeo.Sections = [boundary]
		sweepGeo.Spine    = (coilGeo, [])
		sweepGeo.Solid    = surface is None
		sweepGeo.Frenet   = True
		setDefaultViewObjectValues(sweepGeo)

		self.addBody(coilNode, sweepGeo, 0x13, 0x11)
		hide(coilGeo)

		return

	def Create_FxChamfer(self, chamferNode):
		properties  = chamferNode.get('properties')
		edgeSet     = getProperty(properties, 0x00) # edge proxies
		faceProxies = getProperty(properties, 0x01) # base faces for the edges
		dim1        = getProperty(properties, 0x02) # first distance
		dim2        = getProperty(properties, 0x03) # second distance
		chamferType = getProperty(properties, 0x04) # chamfer type
		flip        = getProperty(properties, 0x05) # flip directions
		#           = getProperty(properties, 0x06) # corner setback (boolean) => not supported!
		dimensions  = getProperty(properties, 0x08) # FeatureDimensions
		preserve    = getProperty(properties, 0x09) # preserve all features
		angle       = getProperty(properties, 0x0A) # Angle
		body        = getProperty(properties, 0x0B) # SolidBody

		dist1 = getMM(dim1) # 1st distance
		dist2 = getMM(dim2) # 2nd distance
		geos  = []
		edges = self.getEdgesFromSet(edgeSet)
		value = chamferType.node.getValueText()
		i = 0
		for idxCreator in edges:
			i += 1
			if (value == u"'Distance'"):
				chamfers = [(idx + 1, dist1, dist1) for idx in edges[idxCreator]]
			elif (value == u"'TwoDistances'"):
				chamfers = [(idx + 1, dist1, dist2) for idx in edges[idxCreator]]
			else:
				logWarning("   Chamfer %s: %s not supported - using 2nd distances", chamferNode.name, value)
				chamfers = [(idx + 1, dist1, dist2) for idx in edges[idxCreator]]
			name = chamferNode.name
			if (len(edges) > 1):
				name += u"_%d" %(i)

			fx = chamferNode.segment.indexNodes[idxCreator].geometry
			chamferGeo = newObject('Part::Chamfer', name)
			chamferGeo.Base  = fx
			chamferGeo.Edges = chamfers
			geos.append(chamferGeo)
			hide(fx)

		chamferGeo = self.combineGeometries(geos, chamferNode)
		if (chamferGeo is not None):
			self.addSolidBody(chamferNode, chamferGeo, body)

		return

	def getFilletsContantR(self, fillets, constantR):
		if (constantR is not None):
			sets = constantR.get('sets')
			for set in sets:
				edges  = self.getEdgesFromSet(set.get('edges')) # EdgeCollectionProxy
				radius = getMM(set.get('radius'))               # Parameter
				# mode = set.get('select')                      # FilletConstantRSelectMode
				# isG2 = set.get('continuityG1')	            # boolean - not supported by FreeCAD
				for creator in edges:
					if creator not in fillets:
						fillets[creator] = [(idx + 1, radius, radius) for idx in edges[creator]]
					else:
						lst = fillets[creator]
						lst += [(idx + 1, radius, radius) for idx in edges[creator]]
		return fillets

	def getFilletsVariableR(self, fillets, variableR):
		if (variableR is not None):
			sets = variableR.get('sets')
			for set in sets:
				edges = self.getEdgesFromSet(set.get('edges'))# EdgeCollectionProxy
				radii = set.get('radii')
				extrema = radii.get('extrema')
				if (len(radii.get('additional')) > 0):
					logWarning("Fillet: intermediate radii are not supported by FreeCAD - IGNORED!")
				radius1 = getMM(extrema[0].get('radius'))
				radius2 = getMM(extrema[-1].get('radius'))
				for creator in edges:
					if creator not in fillets:
						fillets[creator] = [(idx + 1, radius1, radius2) for idx in edges[creator]]
					else:
						lst = fillets[creator]
						lst += [(idx + 1, radius1, radius2) for idx in edges[creator]]

		return fillets

	def Create_FxFillet(self, filletNode):
		properties = filletNode.get('properties')
		constantR  = getProperty(properties, 0x00) # FxFilletConstant
		variableR  = getProperty(properties, 0x01) # FxFilletVariable
		# autoEdgeChain       = getProperty(properties, 0x02) # boolean - Automatic Edge chain
		# rolling             = getProperty(properties, 0x03) # boolean - Rolling ball where possible
		# smooth              = getProperty(properties, 0x04) # boolean - Smooth radius transition
		# = getProperty(properties, 0x05) # boolean
		# = getProperty(properties, 0x06) # (always None)
		# dimension           = getProperty(properties, 0x07) # FeatureDimensions
		# rollAlongSharpEdges = getProperty(properties, 0x08) # boolean - roll along sharp edges
		# = getProperty(properties, 0x09) # 660DEE07 => FilletSetback ??? -> organic-skulpture.ipt
		# = getProperty(properties, 0x0A) # FilletFullRoundSet <=> type!='Edge'
		# filletType          = getProperty(properties, 0x0B) # 'Edge', 'Face' or 'FullRound'
		faceRadius  = getProperty(properties, 0x0C) # Parameter 'd144'=54.1mm
		# noOptimice          = getProperty(properties, 0x0D) # boolean
		# = getProperty(properties, 0x0E) # None (always)
		body = getProperty(properties, 0x0F) # SolidBody 'Solid1'
		if (body is None):
			body = getProperty(properties, 0x10) # SolidBody 'Solid1'

		geos  = []
		fillets = {} # key = creator_index, values = index of the edges
		self.getFilletsContantR(fillets, constantR)
		self.getFilletsVariableR(fillets, variableR)

		i = 0
		for idxCreator in fillets:
			i += 1
			name = filletNode.name
			if (len(fillets) > 1):
				name += u"_%d" %(i)
			fx = filletNode.segment.indexNodes[idxCreator].geometry
			filletGeo = newObject('Part::Fillet', name)
			filletGeo.Base  = fx
			filletGeo.Edges = fillets[idxCreator]
			geos.append(filletGeo)
			hide(fx)

		filletGeo = self.combineGeometries(geos, filletNode)
		if (filletGeo is not None):
			self.addSolidBody(filletNode, filletGeo, body)

		return

	def Create_MeshFolder(self, meshFolderNode):
		logInfo(u"    creating MeshFolder '%s' ...", meshFolderNode.name)
		folder = createGroup(meshFolderNode.name)

		index = meshFolderNode.get('index')
		gr = getModel().getGraphics()
		dc = meshFolderNode.segment
		grMeshFolderNode = gr.indexNodes[index]
		for meshDC in meshFolderNode.get('meshes'):
			meshDC.handled = True
			meshId = meshDC.get('meshId')
			if (meshId is None):
				meshGR = gr.indexNodes[meshDC.get('index')]
			else:
				meshGR = gr.meshes[meshId]
			for p, partGR in enumerate(meshGR.get('parts')):
				obj3D  = partGR.get('object3D')
				for f, facetGR in enumerate(obj3D.get('objects')):
					name = u"%s_%d" %(meshDC.name, (f + 1))
					logInfo(u"        addign Mesh '%s_%d' ...", name)
					points  = facetGR.get('points').get('points')
					indices = facetGR.get('pointIndices').get('indices')
					if (facetGR.get('normals') is not None):
						# create a new empty mesh
						triangles = [[x * 10.0 for x in points[i]] for i in indices]
						m = Mesh.Mesh(triangles)
						# add the mesh to the active document
						geo = newObject('Mesh::Feature', name)
						folder.addObject(geo)
						geo.Mesh = m
		return

	def Create_FxMesh(self, meshNode): return ignoreBranch(meshNode) # created with Create_MeshFolder!

	def Create_FxRuledSurface(self, ruledSurfaceNode):
		properties = ruledSurfaceNode.get('properties')
		# = getProperty(properties, 0x00)     # ???
		# = getProperty(properties, 0x01)     # 671CE131
		# = getProperty(properties, 0x02)     # 9C38036E
		dist = getProperty(properties, 0x03)  # distance
		# = getProperty(properties, 0x04)     # flipped
		# = getProperty(properties, 0x05)     # bool
		# = getProperty(properties, 0x06)     # bool
		dir = getProperty(properties, 0x07)   # direction
		# = getProperty(properties, 0x08)     # base surface
		# = getProperty(properties, 0x09)     # bool
		surf = getProperty(properties, 0x0A)  # resulting surface
		# = getProperty(properties, 0x0B)     # ???
		# = getProperty(properties, 0x0C)     # param
		angle = getProperty(properties, 0x0D) # angle
		return notYetImplemented(extendNode)

	def Create_FxFaceExtend(self, extendNode):
		properties = extendNode.get('properties')
#		edgeSet    = getProperty(properties, 0x00) # EdgeCollectionProxy
		# = getProperty(properties, 0x01) # FaceExtend
		fxType     = getProperty(properties, 0x02) # ExtentType=To
		dist       = getProperty(properties, 0x03) # Parameter 'd2'=1.75mm
		face       = getProperty(properties, 0x04) # Face <=> extendType == to
		# = getProperty(properties, 0x06) # bool
		surf       = getProperty(properties, 0x07) # SurfaceBody 'Fläche2'

#		edges = self.getEdgesFromSet(edgeSet)

		return notYetImplemented(extendNode)

	def Create_FxBoundaryPatch(self, fxNode):
		properties = fxNode.get('properties')
		profile    = getProperty(properties, 0) # BoundaryPatch
		profiles   = getProperty(properties, 1) # 8B2B8D96
		value      = getProperty(properties, 3) # Parameter
		surface    = getProperty(properties, 4) # SurfaceBody 'Srf4'

		features = []
		if ((profiles is not None) and (profiles.typeName == "8B2B8D96")):
			lst = profiles.get('lst0')
			for profile in lst:
				for loop in profile.get('lst0'):
					for edge in loop.get('lst0'):
						fx = self.createBoundary(edge.get('ref_1'))
						if (fx is not None): features.append(fx)
		else:
			fx = self.createBoundary(profile)
			if (fx is not None): features.append(fx)

		edges = []
		for fx in features:
			edges += [g.toShape() for g in fx.Geometry]
			FreeCAD.ActiveDocument.removeObject(fx.Name)

		if (len(edges) > 0):
			boundaryPatch = InventorViewProviders.makeBoundaryPatch(edges, fxNode.name)
			self.addSurfaceBody(fxNode, boundaryPatch, surface)

	def Create_FxCoreCavity(self, coreCavityNode):
		properties = coreCavityNode.get('properties')
#		getProperty(properties, 0) # SurfaceBodies 'None'
#		getProperty(properties, 1) # SurfaceBodies 'None'
#		getProperty(properties, 2) # SolidBody 'Srf29','Srf34'
#		getProperty(properties, 3) # SolidBody 'Srf1','Srf2','Srf3','Srf4','Srf5','Srf6','Srf7','Srf8','Srf9','Srf10','Srf11','Srf24','Srf25','Srf26','Srf27'
		dir   =	getProperty(properties, 5) # Direction - (0,0,1)
		value = getProperty(properties, 6) # Parameter 'RDxVar5'=0.001
#		getProperty(properties, 7) # SolidBody 'Solid3','Solid4'
		return notYetImplemented(coreCavityNode)

	def Create_FxDecal(self, decalNode):
		properties = decalNode.get('properties')

		images = getProperty(properties, 0) # ImageCollection
		face   = getProperty(properties, 1) # Face
#		       = getProperty(properties, 2) # Boolean
		solids = getProperty(properties, 3) # SurfaceBodies 'Solid1'
#		       = getProperty(properties, 4) # 7C6D7B13 (opt.)

#		images = decalNode.get('images') # same as properties[0]!
		sketch   = decalNode.get('sketch')

		return notYetImplemented(decalNode)

	def Create_FxDirectEdit(self, fxNode):
		properties = fxNode.get('properties')
		return notYetImplemented(fxNode)

	def Create_FxEmboss(self, embossNode):
		properties = embossNode.get('properties')
		operation  = getProperty(properties, 0)  # PartFeatureOperation='Cut'
		profile    = getProperty(properties, 1)  # BoundaryPatch
		dir        = getProperty(properties, 2)  # Direction - (-0.0238873,-6.12323e-17,0.999715)
#		getProperty(properties, 3)  # Boolean
#		getProperty(properties, 4)  # Boolean
		depth      = getProperty(properties, 5)  # Parameter 'd474'=0.25mm
		taperAngle = getProperty(properties, 6)  # Parameter 'd475'=0°
#		getProperty(properties, 7)  # Boolean
#		getProperty(properties, 8)  # Boolean
		faces      = getProperty(properties, 9)  # FaceCollection
		bodies     = getProperty(properties, 10) # SurfaceBodies 'Solid1'
		fxDim      = getProperty(properties, 11) # FeatureDimensions
#		getProperty(properties, 12) # Boolean
		text       = getProperty(properties, 13) # RtfContent 'Default'

		base     = self.createBoundary(profile)

		return notYetImplemented(embossNode)

	def Create_FxFaceDelete(self, faceNode):
		properties = faceNode.get('properties')
		faces      = getProperty(properties, 0) # FaceCollection
#		getProperty(properties, 1) # ParameterBoolean=False
#		getProperty(properties, 2) # ParameterBoolean=False
		body       = getProperty(properties, 3) # SurfaceBodies 'Solid1'
		return notYetImplemented(faceNode)

	def Create_FxFaceDraft(self, faceNode):
		properties = faceNode.get('properties')
		dir        = getProperty(properties,  0) #  Direction - (-2.96059e-16,1,0)
		faces      = getProperty(properties,  1) #  FaceCollection
#		edgeSet    = getProperty(properties,  2) #  EdgeCollectionProxy
		angle      = getProperty(properties,  3) #  Parameter (opt.)
		bodies     = getProperty(properties,  4) #  SurfaceBodies 'Solid1'
		fxDim      = getProperty(properties,  5) #  FeatureDimensions
		draft      = getProperty(properties,  6) #  FaceDraft
#		getProperty(properties,  7) #  Boolean
#		getProperty(properties,  9) #  0B85010C
#		getProperty(properties, 14) #  Boolean
		splitType  = getProperty(properties, 15) #  SplitToolType='Path'
#		getProperty(properties, 16) #  1A1C8265
#		getProperty(properties, 17) #  Boolean
#		getProperty(properties, 18) #  Boolean
#		getProperty(properties, 20) #  Boolean

#		edges = self.getEdgesFromSet(edgeSet)

		return notYetImplemented(faceNode)

	def Create_FxFaceMove(self, faceNode):
		properties = faceNode.get('properties')
		faces      = getProperty(properties, 0) # FaceCollection
		moveType   = getProperty(properties, 1) # FaceMoveType
		direction  = getProperty(properties, 2) # Direction
		distandce  = getProperty(properties, 3) # Parameter
#		getProperty(properties, 4) # ParameterBoolean=False
		bodies     = getProperty(properties, 8) # SurfaceBodies
		fxDim      = getProperty(properties, 9) # FeatureDimensions
#		getProperty(properties,11) # ParameterBoolean=False
		matrix     = getProperty(properties,12) # Transformation

		return notYetImplemented(faceNode)

	def Create_FxFaceReplace(self, faceNode):
		properties = faceNode.get('properties')
		oldFaces   = getProperty(properties, 0) # FaceCollection
		newFaces   = getProperty(properties, 1) # FaceCollection
		bodies     = getProperty(properties, 2) # SurfaceBodies
#		getProperty(properties, 4) # Boolean
		return notYetImplemented(faceNode)

	def Create_FxFreeform(self, freeformNode):
		properties = freeformNode.get('properties')
#		getProperty(properties, 0) # EB9E49B0
#		getProperty(properties, 1) # EB9E49B0
#		getProperty(properties, 2) # Boolean
		return notYetImplemented(freeformNode)

	def Create_FxMove(self, moveNode):
		properties = moveNode.get('properties')
		sources    = getProperty(properties, 0) # ObjectCollection
		trans      = getProperty(properties, 1) # 0800FE29
		dim        = getProperty(properties, 2) # FeatureDimensions
		return notYetImplemented(moveNode)

	def Create_FxNonParametricBase(self, nonParametricBaseNode):
		properties = nonParametricBaseNode.get('properties')
		base = getProperty(properties, 0) # Feature, CA02411F
#		 = getProperty(properties, 1) # CA02411F 'Srf2'
#		 = getProperty(properties, 2) # ParameterBoolean=False
		return notYetImplemented(nonParametricBaseNode)

	def Create_FxPatternSketchDriven(self, patternNode):
		properties = patternNode.get('properties')
		return notYetImplemented(patternNode)

	def Create_FxReference(self, referenceNode):
		properties = referenceNode.get('properties')
#		getProperty(properties, 0) # SurfaceBody
#		getProperty(properties, 1) # SurfaceBody 'Srf8'
#		getProperty(properties, 2) # Boolean (opt.)
		return notYetImplemented(referenceNode)

	def Create_FxSculpt(self, sculptNode):
		properties = sculptNode.get('properties')
#		getProperty(properties, 0) # SurfacesSculpt
#		getProperty(properties, 1) # ParameterBoolean=False
#		getProperty(properties, 2) # SurfaceBodies 'Solid1'
#		getProperty(properties, 3) # ParameterBoolean=False

		return notYetImplemented(sculptNode)

	def Create_FxShell(self, shellNode):
		properties = shellNode.get('properties')
#		getProperty(properties, 0) # ShellDirection='Inside'
		faces      = getProperty(properties, 1) # FaceCollection
#		getProperty(properties, 2) # SurfaceSelection
#		getProperty(properties, 3) # Parameter 'Shell_Thickness'=2mm
#		getProperty(properties, 5) # FeatureDimensions
#		getProperty(properties, 6) # Parameter 'RDxVar5'=10
#		getProperty(properties, 7) # FeatureApproximationType='No'
#		getProperty(properties, 8) # 637B1CC1_Enum=0
#		getProperty(properties, 9) # SolidBody 'Solid1'

		return notYetImplemented(shellNode)

	def Create_FxTrim(self, trimNode):
		properties = trimNode.get('properties')
#		getProperty(properties, 0) # TrimType
#		getProperty(properties, 1) # SolidBody 'Srf31'
		profile    = getProperty(properties, 2) # BoundaryPatch
#		getProperty(properties, 3) # Plane 'Work Plane11'
#		getProperty(properties, 5) # SurfaceBody 'Srf29'
#		getProperty(properties, 6) # F0677096

		boundary = self.createBoundary(profile)

		return notYetImplemented(trimNode)

	# Features requiring Nurbs
	def Create_FxAliasFreeform(self, aliasFreeformNode):
		properties = aliasFreeformNode.get('properties')
#		getProperty(properties, 0) # SurfaceBodies 'Solid1'
#		getProperty(properties, 1) # SurfaceBody
#		getProperty(properties, 2) # ParameterBoolean=False
		return notYetImplemented(aliasFreeformNode)

	# Features requiring BOPTools
	def Create_FxSplit(self, splitNode):
		properties = splitNode.get('properties')
#		getProperty(properties, 0) # SplitType='SplitFaces'
#		getProperty(properties, 1) # ParameterBoolean=False
#		getProperty(properties, 3) # SplitToolType='WorkSurface'
		profile    = getProperty(properties, 4) # BoundaryPatch
#		getProperty(properties, 5) # Plane 'YZ Plane'
#		getProperty(properties, 6) # RotateClockwise
		solid      = getProperty(properties, 7) # SurfaceBodies 'Solid1'

		base     = self.createBoundary(profile) if (profile.get('profile') is not None) else None

		return notYetImplemented(splitNode)

	# Features for Platis Parts
	def Create_FxBoss(self, bossNode):
		properties   = bossNode.get('properties')
#		getProperty(properties, 0)  # Boolean
#		getProperty(properties, 1)  # Direction - (0,1,0)
#		getProperty(properties, 2)  # Boolean
#		getProperty(properties, 3)  # Direction - (1,0,0)
#		getProperty(properties, 4)  # Boolean
#		getProperty(properties, 5)  # Parameter =0.3mm
#		getProperty(properties, 6)  # HeadStyle
#		getProperty(properties, 7)  # Parameter =8mm
#		getProperty(properties, 8)  # Parameter =1.5mm
#		getProperty(properties, 9)  # Parameter =0.5mm
#		getProperty(properties, 10) # Parameter =7mm
#		getProperty(properties, 11) # Parameter =1.5mm
#		getProperty(properties, 12) # Parameter =3mm
#		getProperty(properties, 13) # Parameter =2.5°
#		getProperty(properties, 14) # Parameter =2.5°
#		getProperty(properties, 15) # Parameter =2.5°
#		getProperty(properties, 16) # Parameter =2.5°
#		getProperty(properties, 17) # Parameter =90°
#		getProperty(properties, 18) # Boolean
#		getProperty(properties, 19) # ThreadType='Full Depth'
#		getProperty(properties, 20) # Parameter =8mm
#		getProperty(properties, 21) # Parameter =3mm
#		getProperty(properties, 22) # Parameter =9.5mm
#		getProperty(properties, 23) # Parameter =2°
#		getProperty(properties, 24) # Parameter =1°
#		getProperty(properties, 25) # Boolean
#		getProperty(properties, 26) # Parameter =2
#		getProperty(properties, 27) # Parameter =2mm
#		getProperty(properties, 28) # Parameter =2mm
#		getProperty(properties, 29) # Parameter =10mm
#		getProperty(properties, 30) # Parameter =0mm
#		getProperty(properties, 31) # Parameter =10°
#		getProperty(properties, 32) # Parameter =2.5°
#		getProperty(properties, 33) # Parameter =0mm
#		getProperty(properties, 34) # Parameter =0mm
#		getProperty(properties, 35) # Parameter =0°
#		getProperty(properties, 36) # 0A077221_Enum=1
#		getProperty(properties, 37) # 0CAC6298
#		getProperty(properties, 38) # Transformation
#		getProperty(properties, 39) # Direction - (0,1,0)
#		getProperty(properties, 40) # 4DC465DF
#		getProperty(properties, 41) # SurfaceBodies
#		getProperty(properties, 42) # Parameter =0mm
#		getProperty(properties, 43) # Parameter =360°
#		getProperty(properties, 44) # Direction - (1,0,0)

		return notYetImplemented(bossNode) # MultiFuse Geometry

	def Create_FxRib(self, ribNode): # Belongs to FxBoss!
		properties = ribNode.get('properties')
		profile1   = getProperty(properties, 0)  # BoundaryPatch
		profile2   = getProperty(properties, 1)  # BoundaryPatch
#		getProperty(properties, 2)  # ParameterBoolean=False
#		getProperty(properties, 3)  # Parameter 'rib_thickness'=2.38125mm
#		getProperty(properties, 4)  # ExtentType='2_Dimensions'
#		getProperty(properties, 5)  # ParameterBoolean=False
#		getProperty(properties, 6)  # Parameter 'd31'=2.54mm
#		getProperty(properties, 7)  # Direction - (0,1,0)
#		getProperty(properties, 8)  # SurfaceBodies 'Solid1'
#		getProperty(properties, 9)  # FeatureDimensions
#		getProperty(properties, 10) # ParameterBoolean=True
#		getProperty(properties, 11) # Parameter 'rib_draft_dont_use'=0°
#		getProperty(properties, 12) # ParameterBoolean=False
#		getProperty(properties, 17) # Transformation

		boundary1 = self.createBoundary(profile1)
		boundary2 = self.createBoundary(profile2)

		return notYetImplemented(ribNode)

	def Create_FxFilletRule(self, filletNode):
		properties = filletNode.get('properties')
#		getProperty(properties, 0)  # D70E9DDA
#		getProperty(properties, 3)  # ParameterBoolean=True
#		getProperty(properties, 4)  # ParameterBoolean=True
#		getProperty(properties, 5)  # ParameterBoolean=False
#		getProperty(properties, 6)  # ParameterBoolean=False
#		getProperty(properties, 7)  # ParameterBoolean=False
#		getProperty(properties, 8)  # ParameterBoolean=True
#		getProperty(properties, 9)  # SolidBody 'None'
#		getProperty(properties, 10) # FeatureDimensions
#		getProperty(properties, 11) # Parameter 'RDxVar8'=1
		return notYetImplemented(filletNode)

	def Create_FxGrill(self, grillNode):
		properties = grillNode.get('properties')
		prflBoundary  = getProperty(properties, 0)  # BoundaryPatch 'Boundary'
		prflIsland    = getProperty(properties, 1)  # BoundaryPatch 'Island'
		prflRib1      = getProperty(properties, 2)  # BoundaryPatch 'Rib'
		prflRib2      = getProperty(properties, 3)  # BoundaryPatch 'Rib'
		prflSpare1    = getProperty(properties, 4)  # BoundaryPatch 'Spare'
		prflSpare2    = getProperty(properties, 5)  # BoundaryPatch 'Spare'
#		getProperty(properties, 6)  # Parameter 'd136'=2mm
#		getProperty(properties, 7)  # Parameter 'd137'=0mm
#		getProperty(properties, 8)  # Parameter 'd138'=0mm
#		getProperty(properties, 9)  # Parameter 'd145'=0mm
#		getProperty(properties, 10) # Parameter 'd140'=0.2mm
#		getProperty(properties, 11) # Parameter 'd139'=1.3mm
#		getProperty(properties, 12) # Parameter 'd141'=2.5mm
#		getProperty(properties, 13) # Parameter 'd142'=0.5mm
#		getProperty(properties, 14) # Parameter 'd143'=0mm
#		getProperty(properties, 15) # Parameter 'd144'=5mm
		draftAngle = getProperty(properties, 16) # Parameter 'd146'=0°
#		getProperty(properties, 17) # Boolean
#		getProperty(properties, 18) # Parameter 'd147'=0mm
		bodies     = getProperty(properties, 19) # SurfaceBodies 'None'
#		getProperty(properties, 20) # Parameter 'd148'=11.9994mm^2

		boundary = self.createBoundary(prflBoundary)
		island   = self.createBoundary(prflIsland)
		rib1     = self.createBoundary(prflRib1)
		rib2     = self.createBoundary(prflRib2)
		spare1   = self.createBoundary(prflSpare1)
		spare2   = self.createBoundary(prflSpare2)

		return notYetImplemented(grillNode)

	def Create_FxLip(self, lipNode):
		properties = lipNode.get('properties')
		dir        = getProperty(properties, 0)  # Direction - (0,1,0)
#		edgeSet    = getProperty(properties, 1)  # EdgeCollectionProxy
#		getProperty(properties, 2)  # Boolean
		faces      = getProperty(properties, 3)  # FaceCollection
#		getProperty(properties, 4)  # 7414D5CA -> Workplanes ?!?
		width      = getProperty(properties, 5)  # Parameter 'd424'=6.35mm
		height     = getProperty(properties, 6)  # Parameter 'd425'=6.35mm
		outerOffset= getProperty(properties, 7)  # Parameter 'd426'=0mm
		innerAngle = getProperty(properties, 8)  # Parameter 'd427'=0°
		outerAngle = getProperty(properties, 9)  # Parameter 'd428'=0°
		grooveDepth= getProperty(properties, 10) # Parameter 'd429'=0mm
		bottom     = getProperty(properties, 11) # Boolean
		bodies     = getProperty(properties, 12) # SurfaceBodies 'Solid63'

#		edges = self.getEdgesFromSet(edgeSet)

		return notYetImplemented(lipNode)

	def Create_FxRest(self, restNode):
		properties     = restNode.get('properties')
		profile        = getProperty(properties, 0)  # BoundaryPatch
#		getProperty(properties, 1)  # Parameter 'd157'=1.5mm
		direction      = getProperty(properties, 2)  # ShellDirection='Inside'
		extentWhat     = getProperty(properties, 3)  # ExtentType='All'
		extentType     = getProperty(properties, 4)  # ExtentType='Dimension'
		width          = getProperty(properties, 5)  # Parameter 'd151'=5mm
#		getProperty(properties, 6)  # Parameter 'd152'=0mm
#		getProperty(properties, 7)  # Parameter 'd153'=0mm
#		getProperty(properties, 8)  # Parameter 'd154'=0mm
		direction      = getProperty(properties, 11) # Direction - (0,1,0)
#		getProperty(properties, 12) # Boolean
#		getProperty(properties, 13) # Boolean
		landingTaper   = getProperty(properties, 14) # Parameter 'd155'=0°
		clearanceTaper = getProperty(properties, 15) # Parameter 'd156'=0°
		bodies         = getProperty(properties, 16) # SurfaceBodies 'None'
		fxDim          = getProperty(properties, 17) # FeatureDimensions

		boundary = self.createBoundary(profile)

		return notYetImplemented(restNode)

	def Create_FxSnapFit(self, snapFitNode):
		properties = snapFitNode.get('properties')
#		getProperty(properties, 0)  # SnapFitType='Beam'
#		getProperty(properties, 1)  # Direction - (1.17886e-15,-1,0)
#		getProperty(properties, 2)  # ParameterBoolean=False
#		getProperty(properties, 3)  # Direction - (1,0,0)
#		getProperty(properties, 4)  # ParameterBoolean=True
#		getProperty(properties, 5)  # Parameter 'd92'=5.5mm
#		getProperty(properties, 6)  # Parameter 'd94'=2mm
#		getProperty(properties, 7)  # Parameter 'd95'=1.4mm
#		getProperty(properties, 8)  # Parameter 'd96'=2.5mm
#		getProperty(properties, 9)  # Parameter 'd97'=2mm
#		getProperty(properties, 10) # Parameter 'd93'=2.5mm
#		getProperty(properties, 11) # Parameter 'd98'=1mm
#		getProperty(properties, 12) # Parameter 'd99'=1mm
#		getProperty(properties, 13) # Parameter 'd100'=50°
#		getProperty(properties, 14) # Parameter 'd101'=50°
#		getProperty(properties, 15) # Parameter 'd186'=4mm
#		getProperty(properties, 16) # Parameter 'd189'=5mm
#		getProperty(properties, 17) # Parameter 'd187'=0.5mm
#		getProperty(properties, 18) # Parameter 'd188'=0.3mm
#		getProperty(properties, 19) # Parameter 'd190'=2mm
#		getProperty(properties, 20) # Parameter 'd191'=0.5mm
#		getProperty(properties, 21) # Parameter 'd192'=0.5mm
#		getProperty(properties, 22) # Parameter 'd193'=0.5mm
#		getProperty(properties, 23) # 0A077221_Enum=0
#		getProperty(properties, 24) # 0CAC6298
#		getProperty(properties, 25) # Transformation
#		getProperty(properties, 26) # Direction - (-0.214923,0.976631,4.62593e-17)
#		getProperty(properties, 27) # 4DC465DF
#		getProperty(properties, 28) # SurfaceBodies 'None'

		return notYetImplemented(snapFitNode) # Cut Geometry (Wedge - Cube)

	# Features requiring SheetMetal
	def Create_FxPlate(self, trimNode):
		properties = trimNode.get('properties')
#		getProperty(properties, 0) # FaceBoundOuterProxy
#		getProperty(properties, 1) # Direction - (0,0,1)
#		getProperty(properties, 2) # ParameterBoolean=False
#		getProperty(properties, 3) # Parameter 'Thickness'=1.524mm
#		getProperty(properties, 4) # PlateDef
#		edgeSet1 = getProperty(properties, 5) # EdgeCollectionProxy
#		getProperty(properties, 6) # SurfaceBody 'Solid1'
#		edgeSet2 = getProperty(properties, 7) # EdgeCollectionProxy
#		getProperty(properties, 8) # FeatureDimensions

#		edges1 = self.getEdgesFromSet(edgeSet1)
#		edges2 = self.getEdgesFromSet(edgeSet2)

		return notYetImplemented(trimNode)

	def Create_FxBend(self, bendNode):
		properties = bendNode.get('properties')
#		edgeSet    = getProperty(properties, 0) # EdgeCollectionProxy
#		getProperty(properties, 1) # Parameter 'd9'=1.524mm
#		getProperty(properties, 2) # Parameter 'Thickness'=1.524mm
#		getProperty(properties, 3) # PlateDef, 0455B440
#		getProperty(properties, 4) # 96058864
#		getProperty(properties, 5) # SurfaceBody 'Solid1'
#		getProperty(properties, 6) # FeatureDimensions
#		getProperty(properties, 7) # BendTransition
#		getProperty(properties, 8) # 90B64134

#		edges = self.getEdgesFromSet(edgeSet)	# for what is it good for??

		return notYetImplemented(bendNode)

	def Create_FxCut(self, cutNode):
		properties = cutNode.get('properties')
#		getProperty(properties, 0)  # PartFeatureOperation='Cut'
		profile    = getProperty(properties, 1)  # BoundaryPatch
#		getProperty(properties, 2)  # Direction - (0,1,0)
#		getProperty(properties, 3)  # ParameterBoolean=True
#		getProperty(properties, 4)  # Parameter 'd15'=3mm
#		getProperty(properties, 5)  # Parameter 'd16'=0°
#		getProperty(properties, 6)  # ExtentType='Dimension'
#		getProperty(properties, 7)  # ParameterBoolean=False
		solid      = getProperty(properties, 14) # SurfaceBody 'Solid1'
#		getProperty(properties, 15) # FeatureDimensions
#		getProperty(properties, 16) # ParameterBoolean=False
#		getProperty(properties, 18) # ParameterBoolean=False
#		getProperty(properties, 26) # ObjectCollection 'Solid1'
#		getProperty(properties, 31) # ParameterBoolean=False
#		getProperty(properties, 33) # ParameterBoolean=False

		boundary = self.createBoundary(profile)

		return notYetImplemented(cutNode)

	def Create_FxContourRoll(self, contourRollNode):
		properties = contourRollNode.get('properties')
#		getProperty(properties, 1)  # FaceBoundOuterProxy
#		getProperty(properties, 2)  # Line3D - (19.33,3.434,-22.9) - (18.33,3.434,-22.9)
#		getProperty(properties, 3)  # Parameter 'd161'=90°
#		getProperty(properties, 4)  # Parameter 'Thickness'=0.5mm
#		getProperty(properties, 5)  # FlipOffset='Side1'
#		getProperty(properties, 6)  # Direction - (-6.84788e-31,5.3904e-15,-1)
#		getProperty(properties, 7)  # UnrollMethod='CentroidCylinder'
#		getProperty(properties, 8)  # Parameter 'd162'=37.1616mm
#		getProperty(properties, 9)  # Parameter 'd163'=23.6578mm
#		getProperty(properties, 10) # Line3D - (0,0,0) - (1,0,0)
#		getProperty(properties, 11) # 90B64134
#		getProperty(properties, 12) # FeatureDimensions
#		getProperty(properties, 13) # SolidBody 'Solid1'
#		getProperty(properties, 14) # PartFeatureOperation='Join'

		return notYetImplemented(contourRollNode)

	def Create_FxCorner(self, cornerNode):
		properties = cornerNode.get('properties')
#		getProperty(properties, 0) # CornerSeam
#		getProperty(properties, 1) # SurfaceBody 'Solid1'
#		getProperty(properties, 2) # FeatureDimensions
#		getProperty(properties, 3) # 299B2DCE
#		getProperty(properties, 4) # FaceBoundOuterProxy
#		getProperty(properties, 6) # ObjectCollection 'Solid1'
		return notYetImplemented(cornerNode)

	def Create_FxFace(self, faceNode):
		properties = faceNode.get('properties')
#		getProperty(properties, 0) # FxPlate 'Plate1'

		return notYetImplemented(faceNode)

	def Create_FxFlange(self, flangeNode):
		properties = flangeNode.get('properties')
		plate      = getProperty(properties, 0) # FxPlate
		bend       = getProperty(properties, 1) # FxBend
		corner     = getProperty(properties, 2) # FxCorner
		return notYetImplemented(flangeNode)

	def Create_FxFlangeContour(self, flangeNode):
		properties = flangeNode.get('properties')
		plate      = getProperty(properties, 0) # FxPlate
		bend       = getProperty(properties, 1) # FxBend
		corner     = getProperty(properties, 2) # FxCorner
		return notYetImplemented(flangeNode)

	def Create_FxFold(self, foldNode):
		properties = foldNode.get('properties')
#		getProperty(properties, 0) # BendLocation='Centerline'
#		getProperty(properties, 1) # ParameterBoolean=True
#		getProperty(properties, 2) # ParameterBoolean=False
#		getProperty(properties, 3) # Parameter 'd24'=90°
#		getProperty(properties, 4) # Parameter 'd25'=0.25mm
#		getProperty(properties, 5) # 833D1B91
#		getProperty(properties, 6) # 96058864
#		getProperty(properties, 7) # SurfaceBodies 'Solid1'
#		getProperty(properties, 8) # ParameterBoolean=False
#		getProperty(properties, 10) # Parameter 'd32'=0.25mm
#		getProperty(properties, 12) # ParameterBoolean=True
#		getProperty(properties, 13) # BendTransition
#		getProperty(properties, 14) # 90B64134

		return notYetImplemented(foldNode)

	def Create_FxHem(self, hemNode):
		properties = hemNode.get('properties')
#		getProperty(properties, 0) # FaceBoundOuterProxy
#		getProperty(properties, 1) # Direction - (9.15804e-17,-1,2.51846e-16)
#		getProperty(properties, 2) # Parameter 'd227'=1mm
#		getProperty(properties, 3) # HemDef
#		edgeSet    = getProperty(properties, 4) # EdgeCollectionProxy
#		getProperty(properties, 5) # 96058864
#		getProperty(properties, 6) # SurfaceBodies 'Solid1'
#		getProperty(properties, 7) # FeatureDimensions
#		getProperty(properties, 8) # BendTransition
#		getProperty(properties, 9) # 90B64134

#		edges = self.getEdgesFromSet(edgeSet)

		return notYetImplemented(hemNode)

	def Create_FxStitch(self, fxNode):
		properties = fxNode.get('properties')
		collection = getProperty(properties, 0) # ObjectCollection 'Srf1', 'Srf2', ...
		result     = getProperty(properties, 1) # SurfaceBodies 'Solid1'
		surface    = getProperty(properties, 3) # ParameterBoolean=False
		tolerance  = getProperty(properties, 4) # Parameter 'd317'=0.0254
#		getProperty(properties, 5) # ParameterBoolean=False

		faces = [self.bodyNodes[face.name].geometry for face in collection.get('bodies') if face.name in self.bodyNodes]
		stitch = InventorViewProviders.makeStitch(faces, fxNode.name, not surface)
		if (surface):
			self.addSurfaceBody(fxNode, stitch, result)
		else:
			self.addSolidBody(fxNode, stitch, result)

	def Create_FxRip(self, ripNode):
		properties = ripNode.get('properties')
#		getProperty(properties, 0) # SurfaceBody 'Solid1'
#		getProperty(properties, 1) # Parameter 'd13'=4mm
#		getProperty(properties, 2) # Point3D - (2.2318,-2.1818,10.225)
#		getProperty(properties, 2) # Point3D - (-7.10543e-15,30,200)
		face       = getProperty(properties, 4) # Face
#		getProperty(properties, 5) # RipType='PointToPoint'
#		getProperty(properties, 6) # FlipOffset=2
		return notYetImplemented(ripNode)

	def Create_FxUnfold(self, unfoldNode):
		unfolds = unfoldNode.get('unfolds')
		if (unfolds is None):
			properties = unfoldNode.get('properties')
#			getProperty(properties, 0) # SurfaceBod(ies|y) 'Solid1'
			face       = getProperty(properties, 1) # Face
			faces      = getProperty(properties, 2) # FaceCollection
#			getProperty(properties, 3) # ParameterBoolean=True
#			getProperty(properties, 4) # 7E15AA39
#			getProperty(properties, 7) # 4688EBA3_Enum=1
			return notYetImplemented(unfoldNode)
		for unfold in unfolds:
			self.getGeometry(unfold)

	def Create_FxRefold(self, refoldNode):
		refolds = refoldNode.get('unfolds')
		if (refolds is None):
			properties = refoldNode.get('properties')
#			getProperty(properties, 0) # SurfaceBodies 'Solid1'
			face       = getProperty(properties, 1) # Face
			faces      = getProperty(properties, 2) # FaceCollection
#			getProperty(properties, 3) # ParameterBoolean=True
#			getProperty(properties, 4) # 7E15AA39
#			getProperty(properties, 5) # MatchedEdge
#			getProperty(properties, 6) # MatchedEdge
#			getProperty(properties, 7) # EBB23D6E_Enum=2
			return notYetImplemented(refoldNode)
		for refold in refolds:
			self.getGeometry(refold)

	def Create_FxLoftedFlangeDefinition(self, fxNode):
		properties = fxNode.get('properties')
#		getProperty(properties, 0)  # SurfaceBody 'Solid1'
#		getProperty(properties, 1)  # A477243B
#		getProperty(properties, 2)  # A477243B
#		getProperty(properties, 3)  # Parameter 'Thickness'=5mm
#		getProperty(properties, 4)  # Parameter 'd6'=5mm
#		getProperty(properties, 5)  # FlipOffset='No'
#		getProperty(properties, 6)  # ParameterBoolean=False
#		getProperty(properties, 7)  # A2DF48D4_Enum=1, FacetControl='CordTolerance'
#		getProperty(properties, 8)  # Parameter 'd5'=0.5mm
#		getProperty(properties, 10) # ParameterBoolean=False
#		getProperty(properties, 12) # FeatureDimensions
#		getProperty(properties, 13) # PlateDef
#		getProperty(properties, 14) # 90B64134
#		edgeSet    = getProperty(properties, 15) # EdgeCollectionProxy

#		edges = self.getEdgesFromSet(edgeSet)

		return notYetImplemented(fxNode)

	def Create_FxBendPart(self, bendPartNode):
		properties = bendPartNode.get('properties')
		profile    = getProperty(properties, 0) # BoundaryPatch
#		getProperty(properties, 1) # Parameter 'd11'=2mm
#		getProperty(properties, 2) # Parameter 'd12'=35°
#		getProperty(properties, 4) # ParameterBoolean=False
#		getProperty(properties, 5) # ParameterBoolean=True
#		getProperty(properties, 6) # ParameterBoolean=False
#		getProperty(properties, 7) # ParameterBoolean=True
#		getProperty(properties, 8) # SurfaceBodies 'Solid1'
#		getProperty(properties, 9) # FeatureDimensions

		boundary = self.createBoundary(profile)

		return notYetImplemented(bendPartNode)

	# not supported features as too much work to implement additional readers or workarounds
	def Create_FxThread(self, threadNode):
		properties = threadNode.get('properties')
#		faces      = getProperty(properties, 0) # FaceCollection
#		getProperty(properties, 1) # ParameterBoolean=True
#		getProperty(properties, 2) # ParameterBoolean=True
#		getProperty(properties, 3) # Parameter 'd16'=0mm
#		getProperty(properties, 4) # Parameter 'd17'=0mm
#		edgeSet    = getProperty(properties, 5) # EdgeCollectionProxy
#		getProperty(properties, 6) # ParameterBoolean=False
#		getProperty(properties, 7) # SurfaceBodies 'Solid1'
#		getProperty(properties, 8) # FeatureDimensions

#		edges = self.getEdgesFromSet(edgeSet)

		return unsupportedNode(threadNode) # https://www.freecadweb.org/wiki/Thread_for_Screw_Tutorial/de

	def Create_FxPunchTool(self, node):     return unsupportedNode(node) # Special iFeature and requires the punch tool file -> additional parser!
	def Create_FxiFeature(self, node):      return unsupportedNode(node)

	def Create_FxUnknown(self, fxNode):
		logWarning(u"    Can't process unknown Feature '%s' - probably an unsupported iFeature:", fxNode.name)
		for idx, property in enumerate(fxNode.get('properties')):
			if (property is not None):
				logWarning(u"[%02d] - %s", idx, property.node) # -> 3rdParty/150107-ohne_freiform-pa.ipt!!! Umgrenzungsfläche2..3..4
		return

	def Create_Feature(self, fxNode):
		name  = fxNode.getSubTypeName()
		index = fxNode.index
		logInfo(u"    adding Fx%s '%s' ...", name, fxNode.name)
		createFxObj = getattr(self, 'Create_Fx%s' %(name))
		createFxObj(fxNode)

		adjustFxColor(fxNode.geometry, fxNode.get('fxColor'))

		FreeCAD.ActiveDocument.recompute()
		return

	def addSketch_Spline3D_Curve(self, bezierNode, sketchObj):
		points=[]
		for entity in bezierNode.get('entities'):
			if (entity.typeName == 'Point3D'):
				points.append(p2v(entity))

		if (len(points) > 1):
			spline = Part.BSplineCurve()
			spline.interpolate(points)
			addSketch3D(sketchObj, spline, isConstructionMode(bezierNode), bezierNode)
		else:
			logError(u"ERROR> Bezier requires at least 2 points - found only %d!", len(points))
		return

	def addSketch_BSpline3D(self, bsplineNode, sketchObj):
		points=[]
		for p in bsplineNode.get('points'):
			points.append(p2v(p))

		bspline = Part.BSplineCurve()
		bspline.interpolate(points, False)
		addSketch3D(sketchObj, bspline, isConstructionMode(bsplineNode), bsplineNode)
		bezierNode = bsplineNode.get('bezier')
		bezierNode.setGeometry(bspline)
		return

	def addSketch_Bezier3D(self, bezierNode, sketchObj):
		# handled together with either Spline3D_Curve or BSpline3D
		return

	def addSketch_Plane(self, lineNode, sketchObj):                      return
	def addSketch_Spline3D_Fixed(self, splineNode, sketchObj):           return
	def addSketch_Spiral3D_Curve(self, spiralNode, sketchObj):           return

	def addSketch_Dimension_Length3D(self, dimensionNode, sketchObj):       return None # notSupportedNode(dimensionNode)
	def addSketch_Dimension_Angle2Planes3D(self, dimensionNode, sketchObj):  return None # notSupportedNode(dimensionNode)
	def addSketch_Geometric_Bend3D(self, geometricNode, sketchObj):
		if (SKIP_CONSTRAINTS & BIT_GEO_BEND == 0): return
		entities = geometricNode.get('lst0')
		p1  = entities[0] # connection point of Line 1 and 2
		l1  = entities[1] # 1st line
		l2  = entities[2] # 2nd line
		arc = entities[3] # bend arc
		p2  = entities[4] # new end point of 1st line and start angle of arc
		p3  = entities[5] # new start point of 2nd line and sweep angle of arc

		replacePoint(sketchObj, p1, l1, p2)
		replacePoint(sketchObj, p1, l2, p3)
		entity = arc.geometry
		circle = Part.Circle(entity.Center, entity.Axis, entity.Radius)
		a = circle.parameter(p2v(p2))
		b = circle.parameter(p2v(p3))
		replaceGeometry(sketchObj, arc, Part.ArcOfCircle(circle, a, b))
		return

	def addSketch_Geometric_Custom3D(self, geometricNode, sketchObj):        return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Coincident3D(self, geometricNode, sketchObj):    return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Collinear3D(self, geometricNode, sketchObj):     return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Helical3D(self, geometricNode, sketchObj):       return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Horizontal3D(self, geometricNode, sketchObj):    return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Smooth3D(self, geometricNode, sketchObj):        return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Parallel3D(self, geometricNode, sketchObj):      return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Perpendicular3D(self, geometricNode, sketchObj): return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Radius3D(self, geometricNode, sketchObj):        return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Tangential3D(self, geometricNode, sketchObj):    return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Vertical3D(self, geometricNode, sketchObj):      return None # notSupportedNode(geometricNode)

	def addSketch_4F240E1C(self, node, sketchObj): return

	def Create_iPart(self, iPartNode):
		# create a iPart Table if it's not a sub-group.
		parent = iPartNode.get('refParent')
		if (parent is None):
			excel = iPartNode.get('excelWorkbook')
			if (excel is not None):
				wb = excel.get('workbook')
				if (wb is not None):
					sheet = wb.sheet_by_index(0)
					cols = range(0, sheet.ncols)
					# get member column
					colMember = 0
					for col in range(0, sheet.ncols):
						header = sheet.cell(0, col).value
						if (re.search("Member", header)):
							colMember = col
							break;
					variants = [str(sheet.cell(row, colMember).value) for row in range(1, sheet.nrows)]
					iPart = InventorViewProviders.makePartVariants(iPartNode.name, variants)
					table = iPart.Values
					# get selected part variant
					defRow = sheet.cell(0, 0).value # Series<defaultRow>2</defaultRow>
					match = re.search(u"<defaultRow>(\d+)</defaultRow>", defRow)
					selValue = variants[0]
					if (match):
						defRow   = int(match.group(1))
						selValue = variants[defRow]
					# build the header for the variants table
					for col in range(0, sheet.ncols):
						header = sheet.cell(0, col).value
						xml = header.find('<')
						if (xml>0):
							header = header[0:xml]
						setTableValue(table, col+1, 1, header)
					for row in range(1, sheet.nrows):
						iPartValue = []
						for col in cols:
							try:
								value = sheet.cell(row, col).value
								iPartValue.append(value)
								setTableValue(table, col+1, row + 1, value)
							except:
								pass
					iPart.Variant = selValue
		return

	def Create_Blocks(self, blocksNode):
		return

	def addParameterTableTolerance(self, table, r, tolerance):
		if (tolerance):
			setTableValue(table, 'D', r, tolerance)
			return u"; D%d='%s'" %(r, tolerance)
		return u''

	def addParameterTableComment(self, table, r, commentRef):
		if (commentRef):
			comment = commentRef.name
			if (comment):
				setTableValue(table, 'E', r, comment)
				return u"; E%d='%s'" %(r, comment)
		return u''

	def addOperandParameter(self, table, nextRow, operandRef):
		if (operandRef):
			return self.addReferencedParameters(table, nextRow, operandRef)
		return nextRow

	def addReferencedParameters(self, table, r, value):
		nextRow = r
		typeName   = value.typeName

		if (typeName == 'ParameterRef'):
			nextRow = self.addParameterToTable(table, nextRow, value.get('target'))
		elif (typeName.startswith('ParameterOperation')):
			nextRow = self.addOperandParameter(table, nextRow, value.get('operand1'))
			nextRow = self.addOperandParameter(table, nextRow, value.get('operand2'))
		elif (typeName == 'ParameterValue'):
			pass # Nothing to do here!
		elif (typeName == 'ParameterConstant'):
			pass # Nothing to do here!
		else:
			value = value.get('value')
			if (value):
				typeName   = value.typeName

				if (typeName == 'ParameterUnaryMinus'):
					nextRow = self.addReferencedParameters(table, nextRow, value)
				elif (typeName == 'ParameterRef'):
					nextRow = self.addParameterToTable(table, nextRow, value.get('target'))
				elif (typeName == 'ParameterFunction'):
					operandRefs = value.get('operands')
					for operandRef in operandRefs:
						nextRow = self.addReferencedParameters(table, nextRow, operandRef)
				elif (typeName.startswith('ParameterOperation')):
					nextRow = self.addOperandParameter(table, nextRow, value.get('operand1'))
					nextRow = self.addOperandParameter(table, nextRow, value.get('operand2'))
				elif (typeName == 'ParameterOperationPowerIdent'):
					nextRow = self.addReferencedParameters(table, nextRow, value.get('operand1'))
		return nextRow

	def addParameterToTable(self, table, r, ref):
		valueNode = ref.node

		if (isinstance(valueNode, ParameterNode)):
			pass
		elif (isinstance(valueNode, ParameterTextNode)):
			pass
		elif (isinstance(valueNode, ValueNode)):
			pass
		else:
			return r

		if ((valueNode is not None) and (valueNode.handled != True)):
			valueNode.handled = True
			key      = ref.name
			mdlValue = u''
			tlrValue = u''
			remValue = u''
			typeName = valueNode.typeName

			if (typeName == 'Parameter'):
				r = self.addReferencedParameters(table, r, valueNode)
				value   = valueNode.getFormula(False)
				formula = valueNode.getFormula(True)
				setTableValue(table, 'A', r, key)
				setTableValue(table, 'B', r, value)
				setTableValue(table, 'C', r, formula)
				mdlValue = '; C%s=%s' %(r, formula)
				tlrValue = self.addParameterTableTolerance(table, r, valueNode.get('tolerance'))
				remValue = self.addParameterTableComment(table, r, valueNode.get('label'))
			elif (typeName == 'ParameterText'):
				value = valueNode.get('value')
				setTableValue(table, 'A', r, key)
				setTableValue(table, 'B', r, "'%s" %(value))
				remValue = self.addParameterTableComment(table, r, valueNode.get('label'))
			elif (typeName == 'ParameterBoolean'):
				value = valueNode.get('value')
				setTableValue(table, 'A', r, key)
				setTableValue(table, 'B', r, value)
				remValue = self.addParameterTableComment(table, r, valueNode.get('label'))
			else: #if (key.find('RDxVar') != 0):
				value = valueNode
				setTableValue(table, 'A', r, key)
				setTableValue(table, 'B', r, value)
				remValue = self.addParameterTableComment(table, r, valueNode.get('label'))

			if (key.find('RDxVar') != 0):
				try:
					aliasName = key.replace(':', '_')
					if (IS_CELL_REF.search(key)):
						aliasName = '%s_' %(aliasName)
					else:
						aliasName = ''.join([i if (ord(i) < 128) and (ord(i) > 32) else '_' for i in aliasName])
					table.setAlias(u"B%d" %(r), aliasName)
					valueNode.set('alias', 'T_Parameters.%s' %(aliasName))
				except Exception as e:
					logError(u"    Can't set alias name for B%d - invalid name '%s' - %s!", r, aliasName, e)

				logInfo(u"        A%d='%s'; B%d='%s'%s'%s%s", r, key, r, value, mdlValue, tlrValue, remValue)
				return r + 1
		return r

	def createParameterTable(self, partNode):
		parameters = partNode.get('parameters')
		table = newObject('Spreadsheet::Sheet', u'T_Parameters')
		logInfo(u"    adding parameters table...")
		setTableValue(table, 'A', 1, 'Parameter')
		setTableValue(table, 'B', 1, 'Value')
		setTableValue(table, 'C', 1, 'Fromula')
		setTableValue(table, 'D', 1, 'Tolerance')
		setTableValue(table, 'E', 1, 'Comment')
		r = 2
		keys = parameters.keys()
		for key in keys:
			r = self.addParameterToTable(table, r, parameters[key])
		return

	def importModel(self, root):
		dc = getModel().getDC()
		doc = dc.tree.getFirstChild('Document')
		if (doc is not None):
			self.root           = root
			self.mapConstraints = {}

			component = doc.get('component')
			self.createParameterTable(component)

			objects = component.get('objects')
			for obj in objects:
				if (obj.typeName in IMPLEMENTED_COMPONENTS):
					self.getGeometry(obj)

			FreeCAD.ActiveDocument.recompute()

			# apply colors stored in graphics segment
			gr = getModel().getGraphics()
			for indexDC in gr.indexNodes:
				dcNode = dc.indexNodes[indexDC]
				geometry = dcNode.geometry
				if (geometry is not None):
					grNode = gr.indexNodes[indexDC]
					color  = getBodyColor(grNode)
					adjustColor(geometry, color)
		else:
			logWarning(u">>>No content to be displayed for DC<<<")
