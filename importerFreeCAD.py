# -*- coding: utf-8 -*-

'''
importerFreeCAD.py
'''
import sys, Draft, Part, Sketcher, traceback, re, Mesh

from importerUtils   import *
from importerClasses import *
from importerSegNode import SecNode, SecNodeRef
from math            import sqrt, fabs, tan, degrees, pi
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

INVALID_NAME = re.compile('^[0-9].*')

DIR_Z = VEC(0, 0, 1)

# x 10                      2   2   1   1   0   0   0
# x  1                      4   0   6   2   8   4   0
#SKIP_CONSTRAINTS_DEFAULT = 0b11111111111111111111111
#SKIP_CONSTRAINTS_DEFAULT = 0b00000000000000000001000 # Only geometric coincidens
SKIP_CONSTRAINTS_DEFAULT  = 0b00110000001111011011111 # default values: no workarounds, nor unsupported constraints!
SKIP_CONSTRAINTS = SKIP_CONSTRAINTS_DEFAULT # will be updated by stored preferences!
PART_LINE = Part.Line
if (hasattr(Part, "LineSegment")):
	PART_LINE = Part.LineSegment

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

def createCircle(c, x2, y2, z2, r):
	return Part.Circle(p2v(c), VEC(x2, y2, z2), r)

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

def notSupportedNode(node):
	if (node.typeName == 'Feature'):
		logWarning(u"        ... %s '%s' not supported (yet?) - please use SAT or STEP instead!", node.typeName, node.getSubTypeName())
	else:
		logWarning(u"        ... %s not supported (yet?) - please use SAT or STEP instead!", node.typeName)
	node.setSketchEntity(-1, None)
	return None

def notYetImplemented(node):
	if (node.typeName == 'Feature'):
		logWarning(u"        ... %s '%s' not implemented yet - sorry!", node.typeName, node.getSubTypeName())
	else:
		logWarning(u"        ... %s not implemented yet - sorry!", node.typeName)
	node.setSketchEntity(-1, None)
	return None

def newObject(doc, className, name):
	v = name
	if (sys.version_info.major < 3):
		v = v.encode('utf8')
		v = v.strip()
	if (INVALID_NAME.match(name)):
		obj = doc.addObject(className, u"_%s" %(v))
	else:
		obj = doc.addObject(className, v)
	if (obj):
		obj.Label = v
	return obj

def createGroup(doc, name):
	if (doc):
		return newObject(doc, 'App::DocumentObjectGroup', name)
	return None

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
	entityNode.setSketchEntity(index, newGeo)
	return newGeo

def addSketch3D(edges, geometry, mode, entityNode):
	geometry.Construction = mode
	edges[entityNode.index] = geometry
	entityNode.setSketchEntity(-1, geometry)
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
	return distance * dir/fabs(dir)

def getCountDir(length, count, direction, fitted):
	if (length is None):    return 1, VEC()
	if (count is None):     return 1, VEC()
	if (direction is None): return 1, VEC()

	distance = getMM(length)

	if (direction.typeName == 'A244457B'):
		midplane = direction.get('parameter')
	elif (direction.typeName == 'A5977BAA'):
		pass
	elif (direction.typeName == 'D2D440C0'):
		logWarning(u"    ... don't know how to apply pattern along curve - ignored!")
		# have to calculate the normal vector for each point of the curve!
		return 1, VEC() # 1: no pattern copy!
	elif (direction.typeName != 'Direction'):
		logWarning(u"    ... don't know how to get direction from (%04X) %s (pattern along curves are not supported) - ignoring pattern!", direction.index, direction.typeName)
		return 1, VEC() # 1 means: no pattern copy.

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
	val = length.getValue()
	if (isinstance(val, Length)): return val.getMM()
	if (isinstance(val, Scalar)): return val.x * 10
	return val * 10.0

def getGRAD(angle):
	if (angle is None): return 0.0
	val = angle.getValue()
	if (isinstance(val, Angle)): return val.getGRAD()
	if (isinstance(val, Scalar)): return val.x
	return val

def isTrue(param):
	if (param is None): return False
	return param.get('value')

def setPlacement(geo, placement, base):
	geo.Placement = placement
	if (base is not None): geo.Placement.Base = base
	return

def replaceEntity(edges, node, geo):
	node.data.sketchEntity = geo
	edges[node.index] = geo
	return geo

def replacePoint(edges, pOld, line, pNew):
	l = line.sketchEntity
	if (l is None): return None
	if (isEqual(p2v(pOld), l.StartPoint)):
		return replaceEntity(edges, line, createLine(p2v(pNew), l.EndPoint))
	return replaceEntity(edges, line, createLine(l.StartPoint, p2v(pNew)))

def int2col(c):
	m = c // 26
	n = c % 26
	if (m > 0):
		return chr(ord('A') + (m - 1)) + chr(ord('A') + n)
	return chr(ord('A') + n)

def setTableValue(table, c, row, val):
	if (type(c) is int):
		col = int2col(c)
	else:
		col = c

	if (type(val) == str):
		table.set(u"%s%d" %(col, row), val)
	else:
		if ((sys.version_info.major <= 2) and (type(val) == unicode)):
			table.set(u"%s%d" %(col, row), "%s" %(val.encode("utf8")))
		else:
			table.set(u"%s%d" %(col, row), str(val))

def setAssociatedSketchEntity(sketchNode, node, ai, entityType):
	idMap = sketchNode.data.associativeIDs.get(ai)
	if (idMap is None):
		idMap = {}
		sketchNode.data.associativeIDs[ai] = idMap
	idMap[entityType] = node
	return

def getAssociatedSketchEntity(sketchNode, ai, entityType):
	idMap = sketchNode.data.associativeIDs.get(ai)
	if (idMap is None):
		return None
	return idMap.get(entityType)

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

class FreeCADImporter:
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
		self.doc            = None
		self.mapConstraints = None
		self.pointDataDict  = None
		self.bodyNodes      = {}
		#_initPreferences()
		# override user selected Constraints!
		SKIP_CONSTRAINTS = SKIP_CONSTRAINTS_DEFAULT

	def getEntity(self, node):
		if (node):
			try:
				if (not isinstance(node, DataNode)): node = node.node
				if (node.handled == False):
					node.handled = True
					if (node.valid):
						importObject = getattr(self, 'Create_%s' %(node.typeName))
						importObject(node)
			except Exception as e:
				logError(u"Error in creating (%04X): %s - %s", node.index, node.typeName, e)
				logError(traceback.format_exc())
				node.valid = False
			return node.sketchEntity
		return None

	def addConstraint(self, sketchObj, constraint, key):
		index = sketchObj.addConstraint(constraint)
		self.mapConstraints[key] = constraint
		return index

	def hide(self, sections):
		for section in sections:
			if (section): section.ViewObject.Visibility = False
		return

	def addSolidBody(self, fxNode, obj3D, solid):
		fxNode.setSketchEntity(-1, obj3D)

		if (solid is not None):
			bodies = solid.get('bodies')
			body = bodies[0]
			body.setSketchEntity(-1, obj3D)
			# overwrite previously added solids with the same name!
			self.bodyNodes[body.name] = fxNode
			self.lastActiveBody = fxNode
		return

	def addSurfaceBody(self, fxNode, obj3D, surface):
		fxNode.setSketchEntity(-1, obj3D)
		if (surface is not None):
			# overwrite previously added sourfaces with the same name!
			self.bodyNodes[surface.name] = fxNode
		return

	def getBodyNode(self, ref):
		if (ref.typeName == 'SolidBody'):
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

	def findBase(self, baseNode):
		if (baseNode is not None):
			assert (baseNode.typeName == 'FaceCollectionProxy'), 'FATA> Expected FaceCollectionProxy not (%04X): %s!' %(baseNode.index, baseNode.typeName)
			base = baseNode.get('proxyDef')
			if (base):
				return self.findBase2(base)
			logError(u"ERROR> Base (%04X): %s not defined!", baseNode.index, baseNode.typeName)
		return None

	def findBase2(self, base):
		baseGeo = None
		if (base is not None):
			name = getFirstBodyName(base)
			if (name in self.bodyNodes):
				# ensure that the sketch is already created!
				baseGeo = self.getEntity(self.bodyNodes[name])
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
			return self.getEntity(self.bodyNodes[node.name])
		except:
			return None

	def findGeometries(self, node):
		geometries = []
		if (node is not None):
			assert (node.typeName == 'FaceCollectionProxy'), 'FATA> (%04X): %s expected FaceCollectionProxy ' %(node.index, node.typeName)
			edges = node.get('faces')
			if (edges is not None):
				for edge in edges:
					name = getFirstBodyName(edge)
					if (name in self.bodyNodes):
						# ensure that the sketch is already created!
						toolGeo = self.getEntity(self.bodyNodes[name])
						if (toolGeo is None):
							logWarning(u"        Tool (%04X): %s -> (%04X): %s can't be created", node.index, node.typeName, toolData.index, toolData.typeName)
						else:
							geometries.append(toolGeo)
							logInfo(u"        ... Tool = '%s'", name)
					else:
						logWarning(u"    Tool (%04X): %s -> '%s' nod found!", node.index, node.typeName, name)
			else:
				logError(u"ERROR> edges (%04X): %s not defined!", node.index, node.typeName)
		else:
			logWarning(u"    Tool: ref is None!")
		return geometries

	def addDimensionConstraint(self, sketchObj, dimension, constraint, key, useExpression = True):
		number = sketchObj.ConstraintCount
		index = self.addConstraint(sketchObj, constraint, key)
		name = dimension.name
		if (len(name)):
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
					dimensionNode.setSketchEntity(index, constraint)
					logInfo(u"        ... added %sdistance '%s' = %s", prefix, constraint.Name, dimension.getValue())
				else:
					logWarning(u"        ... can't create dimension constraint between (%04X): %s and (%04X): %s - not supported by FreeCAD!", entity1.index, entity1.typeName[0:-2], entity2.index, entity2.typeName[0:-2])
		return

	def profile2Section(self, participant):
		face      = participant.get('face')
		surface   = participant.data.segment.indexNodes[face.get('indexRefs')[0]]
		wireIndex = participant.get('number')
		body      = surface.get('body')
		node      = None

		if (body.name in self.bodyNodes):
			node = self.bodyNodes[body.name]
		else:
			label   = surface.get('label')
			creator = label.get('idxCreator')
			if (creator in participant.data.segment.indexNodes):
				entity = participant.data.segment.indexNodes[creator]
				node   = self.getEntity(entity)
			else:
				logError(u"        ... can't create profile for creator (%04X): %s - creator = %04X", label.index, label.typeName, creator)

		entity  = self.getEntity(node)
		if (entity is not None):
			# create an entity that can be featured (e.g. loft, sweep, ...)
			section = newObject(self.doc, 'Part::Feature', participant.name)
			self.doc.recompute()

			# FIXME: Howto convert Inventor-Indices to FreeCAD-Indices?
			if (wireIndex == 0):   wireIndex = 1
			elif (wireIndex == 1): wireIndex = 2
			if (wireIndex < len(entity.Shape.Wires)):
				section.Shape = entity.Shape.Wires[wireIndex]
			return section
		return None

	def collectSection(self, participant):
		if (participant.typeName   == 'Sketch2D'):         return self.getEntity(participant)
		elif (participant.typeName == 'Sketch3D'):         return self.getEntity(participant)
		elif (participant.typeName == 'ProfileSelection'): return self.profile2Section(participant)
		return None

	def createEdgeFromNode(self, wires, sketchEdge, direct):
		sketch = sketchEdge.get('sketch')
		# ensure that the sketch is already created!
		self.getEntity(sketch)
		e      = sketchEdge.get('curve')
		p1     = sketchEdge.get('point1')
		p2     = sketchEdge.get('point2')
		if (e is None):
			e    = getAssociatedSketchEntity(sketch, sketchEdge.get('entityAI'), sketchEdge.get('typEntity'))
		if (p1 is None):
			p1     = getAssociatedSketchEntity(sketch, sketchEdge.get('point1AI'), sketchEdge.get('typPt1'))
		if (p2 is None):
			p2     = getAssociatedSketchEntity(sketch, sketchEdge.get('point2AI'), sketchEdge.get('typPt2'))
		if (e is None):
			return
		edge   = e.sketchEntity
		if (isinstance(edge, Part.Line)):
			edge = None
			if (isSamePoint(p1, p2) == False):
				edge = createLine(p2v(p1), p2v(p2))
		elif (isinstance(edge, Part.LineSegment)):
			edge = None
			if (isSamePoint(p1, p2) == False):
				edge = createLine(p2v(p1), p2v(p2))
		elif (isinstance(edge, Part.ArcOfCircle)):
			c = e.sketchEntity.Center
			edge = Part.Circle(c, edge.Axis, edge.Radius)
			if (isSamePoint(p1, p2) == False):
				alpha   = edge.parameter(p2v(p1))
				beta    = edge.parameter(p2v(p2))
				if (sketchEdge.get('posDir')):
					edge = Part.ArcOfCircle(edge, alpha, beta)
				else:
					edge = Part.ArcOfCircle(edge, beta, alpha)
		elif (isinstance(edge, Part.ArcOfEllipse)):
			edge = edge.Ellipse
			if (isSamePoint(p1, p2) == False):
				alpha   = edge.parameter(p2v(p1))
				beta    = edge.parameter(p2v(p2))
				if (sketchEdge.get('posDir')):
					edge = Part.ArcOfEllipse(edge, alpha, beta)
				else:
					edge = Part.ArcOfEllipse(edge, beta, alpha)
		elif (isinstance(edge, Part.Circle)):
			if (isSamePoint(p1, p2) == False):
				alpha   = edge.parameter(p2v(p1))
				beta    = edge.parameter(p2v(p2))
				if (sketchEdge.get('posDir')):
					edge = Part.ArcOfCircle(edge, alpha, beta)
				else:
					edge = Part.ArcOfCircle(edge, beta, alpha)
		elif (isinstance(edge, Part.Ellipse)):
			if (isSamePoint(p1, p2) == False):
				alpha   = edge.parameter(p2v(p1))
				beta    = edge.parameter(p2v(p2))
				if (sketchEdge.get('posDir')):
					edge = Part.ArcOfEllipse(edge, alpha, beta)
				else:
					edge = Part.ArcOfEllipse(edge, beta, alpha)
		elif (isinstance(edge, Part.BSplineCurve)):
			a = edge.parameter(p2v(p1))
			b = edge.parameter(p2v(p2))
			if (a > b):
				old = a
				a = b
				b = old
			if not (isEqual1D(a, 0.0) and isEqual1D(b, 1.0)):
				try:
					edge = edge.trim(a, b)
				except:
					logWarning(u"    Can't trim BSpline for a=%g and b=%g!", a, b)
					edge = edge.copy()
			else:
				edge = edge.copy()
	#	elif (typ[0: 4] == 'Text'):
	#	elif (typ[0:12] == 'OffsetSpline'):
	#	elif (typ[0:12] == 'SplineHandle'):
	#	elif (typ[0: 5] == 'Block'):
	#	elif (typ[0: 5] == 'Image'):
		else:
			logWarning(u"    ... Don't know how to create edge from %s.%s" %(edge.__class__.__module__, edge.__class__.__name__))
		if (edge is not None):
			wire = edge.toShape()
			wire.Placement = sketch.sketchEntity.Placement.copy()
			wires.append(wire)

		return

	def createBoundaryPart(self, part, solid):
		if (part.typeName in ['1E3A132C', 'Loop']):
			partEdges = []
			for sketchEdge in part.get('edges'): # should be SketchEntityRef
				sketch = sketchEdge.get('sketch')
				if (sketch is not None):
					self.getEntity(sketch) # ensure that the sketch is already created!
				self.createEdgeFromNode(partEdges, sketchEdge, part.typeName == '1E3A132C')

			if (len(partEdges) > 0):
				try:
					w = Part.Wire(partEdges)
					if (solid):
						if (w.isClosed()):
							return Part.Face(w)
						else:
							logError(u"    BoundaryPart (%04X): %s is not closed!", part.index, part.typeName)
					return w
				except:
					s = u",".join([u"%s([%g,%g,%g] - [%g,%g,%g])" %(e.Curve.__class__.__name__, e.Vertexes[0].Point.x, e.Vertexes[0].Point.y, e.Vertexes[0].Point.z,e.Vertexes[-1].Point.x, e.Vertexes[-1].Point.y, e.Vertexes[-1].Point.z) for e in partEdges])
					logError(u"Can't create wire from edges: [%s]", s)
					w = partEdges[0].multiFuse(partEdges[1:])
					Part.show(w)
		else:
			logError(u"    Error:  unknown boundaryPart (%04X): %s!", part.index, part.typeName)
		return None

	def createBoundary(self, boundaryPatch, solid):
		''' Returns a Part.Wire if solid is False, otherwise a Part.Face '''

		profile  = boundaryPatch.get('profile')
		if (profile is not None):
			if (profile.typeName in ['Wire', '603428AE', 'D61732C1', 'Profile']):
				shape = None
				# create all parts of the profile
				for part in profile.get('parts'):
					partBoundary = self.createBoundaryPart(part, solid)
					if (shape is None):
						shape = partBoundary
					else:
						operation = part.get('operation')
						if (operation is None):
							logError(u"    BoundaryPart (%04X): %s has not operation attribute!", part.index, part.typeName)
						if (operation in [0x00, 0x10]):
							shape = shape.cut(partBoundary)
						elif (operation in [0x08, 0x18]):
							shape = shape.fuse(partBoundary)
							shape = shape.removeSplitter()
						else:
							logError(u"    BoundaryPart (%04X): %s has an unknown operation %X!", part.index, part.typeName, operation)
				if (shape is not None):
					fx = profile.get('sketch')
					if (fx is None):
						fx = profile.get('fx')
					else:
						self.hide([fx.sketchEntity])
					boundary = newObject(self.doc, 'Part::Feature', '%s_bp' %fx.name)
					boundary.Shape = shape
					return boundary
			else:
				logError(u"        ... can't create boundary from (%04X): %s - expected next node type (%s) unknown!", boundaryPatch.index, boundaryPatch.typeName, profile.typeName)
		else:
			logError(u"    Error:  boundaryPatch (%04X): %s has no 'profile' property!", boundaryPatch.index, boundaryPatch.typeName)
		return None

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
			booleanGeo = newObject(self.doc, 'Part::%s' %(className), name)
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
		R1 = getMM(diameter1) / 2
		R2 = getMM(diameter2) / 2
		h  = fabs(R1 - R2) / tan(angle.getValue().getRAD() / 2)
		conGeo = newObject(self.doc, 'Part::Cone', name)
		conGeo.Radius1 = R1
		conGeo.Radius2 = R2
		conGeo.Height = h
		conGeo.Placement.Base.z = -h
		return conGeo, h

	def createCylinder(self, name, diameter, height, drillPoint):
		r  = getMM(diameter) / 2
		h1 = getMM(height)
		cylGeo = newObject(self.doc, 'Part::Cylinder', name)
		cylGeo.Radius = r
		cylGeo.Height = h1
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
		if (len(name) == 0): name = node.typeName
		entity = newObject(self.doc, className, name)
		return entity

	def getEdges(self, wire):
		if (wire is not None):
			self.doc.recompute()
			count = len(wire.Shape.Edges)
			return ['Edge%i' %(i) for i in range(1, count + 1)]

		return []

	def getLength(self, body, dirX, dirY, dirZ):
		lx, ly, lz = 0, 0, 0
		node = self.getBodyNode(body)
		if (node):
			box = node.sketchEntity.Shape.BoundBox
			if (not isEqual1D(dirX, 0)): lx = box.XLength
			if (not isEqual1D(dirY, 0)): ly = box.YLength
			if (not isEqual1D(dirZ, 0)): lz = box.ZLength
		return sqrt(lx*lx + ly*ly + lz*lz)

	def getBasesAndEdges(self, edgeRefs):
		bases       = []
		edges       = []
		idxCreators = []

		for edgeRef in edgeRefs:
			for idxRef in edgeRef.get('indexRefs'):
				edgeProxy  = edgeRef.data.segment.indexNodes[idxRef]
				creator    = edgeProxy.get('creator')
				if (creator is not None):
					idxCreator = creator.get('idxCreator')
					edges.append(edgeProxy.get('edgeIdx'))
					if (idxCreator not in idxCreators):
						idxCreators.append(idxCreator)
						baseNode = edgeRef.data.segment.indexNodes[idxCreator]
						base = self.getEntity(baseNode)
						bases.append(base)
		return bases, edges

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
				constraintNode.setSketchEntity(index, constraint)
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
				constraintNode.setSketchEntity(index, constraint)
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
			constraintNode.setSketchEntity(index, constraint)
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
				constraintNode.setSketchEntity(index, constraint)
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
				constraintNode.setSketchEntity(index, constraint)
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
				constraintNode.setSketchEntity(index, constraint)
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
				constraintNode.setSketchEntity(index, constraint)
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
					constraintNode.setSketchEntity(index, constraint)
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
				constraintNode.setSketchEntity(index, constraint)
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
				constraintNode.setSketchEntity(index, constraint)
				logInfo(u"        ... added equal radius constraint between circle %s and %s", index1, index2)
		return

	def addSketch_Point2D(self, pointNode, sketchObj):
		vec2D = (getX(pointNode), getY(pointNode))
		if (vec2D not in self.pointDataDict):
			self.pointDataDict[vec2D] = []
		pointNode.valid = False
		return

	def addSketch_BlockPoint2D(self, node, sketchObj):
		point = node.get('point')
		self.addSketch_Point2D(point, sketchObj)
		node.setSketchEntity(point.sketchIndex, point.sketchEntity)
		return

	def addSketch_Point3D(self, pointNode, edges): return

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
		index = lineNode.index
		points = lineNode.get('points')
		self.removeFromPointRef(points[0], lineNode.index)
		self.removeFromPointRef(points[1], lineNode.index)

	def createLine2D(self, sketchObj, point1, point2, mode, line):
		if (isSamePoint(point1, point2)):
			return False
		part = createLine(p2v(point1), p2v(point2))
		addSketch2D(sketchObj, part, mode, line)
		return True

	def createLine3D(self, edges, line):
		p1 = p2v(line)
		p2 = p2v(line, 'dirX', 'dirY', 'dirZ')
		if (p2.Length == 0): return False
		part = createLine(p1, p1 + p2)
		addSketch3D(edges, part, isConstructionMode(line), line)
		return True

	def createRevolve(self, name, alpha, beta, source, axis, base, solid):
		revolution = newObject(self.doc, 'Part::Revolution', name)
		revolution.Angle = alpha + beta
		revolution.Source = source
		revolution.Axis = axis
		revolution.Base = base
		revolution.Solid = solid
		revolution.Placement = PLC(VEC(), ROT(axis, -beta), base)
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

	def addSketch_Line3D(self, lineNode, edges):
		if (self.createLine3D(edges, lineNode) == False):
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
		p1 = p2v(points[0])
		p2 = p2v(points[1])
		p3 = p2v(points[2])
		arc = Part.ArcOfCircle(p1, p3, p2)
		logInfo(u"        ... added Arc-Circle start=%s, end=%s and %s ...", p1, p2, p3)
		addSketch2D(sketchObj, arc, mode, arcNode)
		return

	def addSketch_Circle2D(self, circleNode, sketchObj):
		center = circleNode.get('center')
		x = getX(center)
		y = getY(center)
		r = getCoord(circleNode, 'r')
		points = circleNode.get('points')
		mode = (circleNode.next.typeName == '64DE16F3') or isConstructionMode(circleNode)
		point1 = None
		point2 = None
		circle = createCircle(center, 0, 0, 1, r)
		if (len(points) > 0): point1 = points[0]
		if (len(points) > 1): point2 = points[1]

		# There has to be at least 2 points to draw an arc.
		# Everything else will be handled as a circle!
		if ((point1 is None) and (point2 is None)):
			addSketch2D(sketchObj, circle, mode, circleNode)
			logInfo(u"        ... added Circle M=(%g,%g) R=%g...", x, y, r)
		else:
			a = circle.parameter(p2v(point1))
			b = circle.parameter(p2v(point2))
			arc = Part.ArcOfCircle(circle, a, b)
			logInfo(u"        ... added Arc-Circle M=(%g,%g) R=%g, from %s to %s ...", x, y, r, a, b)
			addSketch2D(sketchObj, arc, mode, circleNode)

		return

	def addSketch_Circle3D(self, circleNode, edges):
		x      = getCoord(circleNode, 'x')
		y      = getCoord(circleNode, 'y')
		z      = getCoord(circleNode, 'z')
		r      = getCoord(circleNode, 'r')
		normal = circleNode.get('normal')
		points = circleNode.get('points')

		part = createCircle(circleNode, normal[0], normal[1], normal[2], r)

		# There has to be at least 2 points to draw an arc.
		# Everything else will be handled as a circle!
		if (len(points) < 2):
			addSketch3D(edges, part, isConstructionMode(circleNode), circleNode)
			logInfo(u"        ... added Circle M=(%g,%g,%g) R=%g...", x, y, z, r)
		if (len(points) == 2):
			a = Angle(circleNode.get('startAngle'), pi/180.0, u'\xb0')
			b = Angle(circleNode.get('sweepAngle'), pi/180.0, u'\xb0')
			arc = Part.ArcOfCircle(part, a.getRAD(), b.getRAD())
			logInfo(u"        ... added Arc-Circle M=(%g,%g,%g) R=%g, from %s to %s ...", x, y, z, r, a, b)
			addSketch3D(edges, arc, isConstructionMode(circleNode), circleNode)
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

	def addSketch_Ellipse3D(self, ellipseNode, edges):
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
			arc = Part.ArcOfEllipse(part, a1.getGRAD(), a2.getGRAD())
			addSketch3D(edges, arc, isConstructionMode(ellipseNode), ellipseNode)
		return

	def addSketch_Text2D(self, textNode, sketchObj): return notSupportedNode(textNode)

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
				radius = circle.sketchEntity.Radius
				constraint = Sketcher.Constraint('Radius',  index, radius)
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setSketchEntity(index, constraint)
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
				radius = circle.sketchEntity.Radius
				constraint = Sketcher.Constraint('Radius',  index, radius)
				dimension = getDimension(dimensionNode, 'parameter')
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key, False)
				dimensionNode.setSketchEntity(index, constraint)
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
				dimensionNode.setSketchEntity(index, constraint)
				logInfo(u"        ... added dimension angle '%s' = %s (%s)", constraint.Name, angle, key)
		return

	def addSketch_Dimension_OffsetSpline2D(self, dimensionNode, sketchObj):
		'''
		Create distance constraint for an offset spline.
		'''
		if (SKIP_CONSTRAINTS & BIT_DIM_OFFSET_SPLINE == 0): return
		dimensionNode.setSketchEntity(-1, None)
		return

	def addSketch_OffsetSpline2D(self, offsetSplineNode, sketchObj):
		offsetSplineNode.setSketchEntity(-1, None)
		return
	def addSketch_SplineHandle2D(self, splineHandleNode, sketchObj):
		splineHandleNode.setSketchEntity(-1, None)
		return
	def addSketch_SplineHandle3D(self, splineHandleNode, edges):
		splineHandleNode.setSketchEntity(-1, None)
		return
	def addSketch_Block2D(self, blockNode, sketchObj):
		blockNode.setSketchEntity(-1, None)
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
	def addSketch_Image2D(self, imageNode, sketchObj):
		imageNode.setSketchEntity(-1, None)
		return

	def addSketch_5D8C859D(self, node, sketchObj): return
	def addSketch_8EC6B314(self, node, sketchObj): return
	def addSketch_8FEC335F(self, node, sketchObj): return
	def addSketch_DD80AC37(self, node, sketchObj): return
	def addSketch_F2568DCF(self, node, sketchObj): return

	def handleAssociativeID(self, node):
		label  = node.get('label')
		if (label is None): return
		if (label.typeName == 'BFD09C43'):
			label = label.get('label')
			if (label is None): return
		if (label.typeName == 'Styles'):
			id = label.get('associativeID')
			sketch = node.get('sketch')
			entity = node.sketchEntity
			if ((entity is not None) and (entity.Construction == False)):
				sketch.data.sketchEdges[id]  = entity
			setAssociatedSketchEntity(sketch, node, id, label.get('typEntity'))

	def Create_Sketch2D_Node(self, sketchObj, node):
		if ((node.handled == False) and (node.valid)):
			node.handled = True
			try:
				addSketchObj = getattr(self, 'addSketch_%s' %(node.typeName))
				addSketchObj(node, sketchObj)
				self.handleAssociativeID(node)

			except Exception as e:
				logError(u"ERROR> (%04X): %s - %s", node.index, node.typeName, e)
				logError(traceback.format_exc())
		return

	def Create_Sketch3D_Node(self, edges, node):
		if ((node.handled == False) and (node.valid)):
			node.handled = True
			try:
				addSketchObj = getattr(self, "addSketch_%s" %(node.typeName))
				addSketchObj(node, edges)
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

	def Create_Sketch2D(self, sketchNode):
		sketch2D = self.createEntity(sketchNode, 'Sketcher::SketchObject')
		logInfo(u"    adding 2D-Sketch '%s' ...", sketch2D.Label)
		sketch2D.Placement = getPlacement(sketchNode.get('transformation'))
		sketchNode.setSketchEntity(-1, sketch2D)
		geos = []
		dims = []
		self.pointDataDict = {}

		for child in sketchNode.get('entities'):
			if (child.typeName.startswith('Geometric_')):
				geos.append(child)
			elif (child.typeName.startswith('Dimension_')):
				dims.append(child)
			else:
				self.Create_Sketch2D_Node(sketch2D, child.node)

		for g in geos:
			self.Create_Sketch2D_Node(sketch2D, g.node)

		# need to recompute otherwise FreeCAD messes up directions for other constraints!
		if (self.doc): self.doc.recompute()

		for d in dims:
			self.Create_Sketch2D_Node(sketch2D, d.node)

		self.addSketch_PostCreateCoincidences(sketch2D)

		if (self.root):
			self.root.addObject(sketch2D)

		self.pointDataDict = None

		return

	def Create_Sketch3D(self, sketchNode):
		sketch3D = self.createEntity(sketchNode, 'Part::Feature')
		logInfo(u"    adding 3D-Sketch '%s' ...", sketch3D.Label)
		sketchNode.setSketchEntity(-1, sketch3D)
		geos = []
		dims = []
		edges = {}
		self.pointDataDict = {}

		for child in sketchNode.get('entities'):
			if (child.typeName.startswith('Geometric_')):
				geos.append(child)
			elif (child.typeName.startswith('Dimension_')):
				dims.append(child)
			else:
				self.Create_Sketch3D_Node(edges, child.node)

		for g in geos:
			self.Create_Sketch3D_Node(edges, g.node)

## 3DConstraints not supported in FreeCAD
#		for d in dims:
#			self.Create_Sketch3D_Node(edges, d.node)
#			# need to recompute otherwise FreeCAD messes up directions for other constraints!
#			if (self.doc): self.doc.recompute()

		sketch3D.Shape = Part.Shape(edges.values())
		sketch3D.ViewObject.LineColor  = (0.0, 1.0, 0.0)
		sketch3D.ViewObject.LineWidth  = 1.0
		sketch3D.ViewObject.PointColor = (0.0, 1.0, 0.0)
		sketch3D.ViewObject.PointSize  = 2.0

		if (self.root):
			self.root.addObject(sketch3D)

		self.pointDataDict = None

		return

	def Create_FxExtrude_New(self, padNode, sectionNode, name):
		properties = padNode.get('properties')
		boundary   = getProperty(properties, 0x01)               # The selected edges from a sketch
		direction  = getProperty(properties, 0x02)               # The direction of the extrusion
		reversed   = getPropertyValue(properties, 0x03, 'value') # If the extrusion direction is inverted
		dimLength  = getProperty(properties, 0x04)               # The length of the extrusion in direction 1
		dimAngle   = getProperty(properties, 0x05)               # The taper outward angle  (doesn't work properly in FreeCAD)
		extend     = getPropertyValue(properties, 0x06, 'value') #
		midplane   = getPropertyValue(properties, 0x07, 'value')
		# = getProperty(properties, 0x0F)#               FeatureDimensions
		surface    = getProperty(properties, 0x10)               # SurfaceBody
		# = getProperty(properties, 0x13)#               Parameter 'RDxVar0'=1
		# = getPropertyValue(properties, 0x14, 'value')# ParameterBoolean=False
		# = getProperty(properties, 0x15)#               CEFD3973_Enum=0
		# = getPropertyValue(properties, 0x16, 'value')# ParameterBoolean=True
		# = getProperty(properties, 0x17)#               FxBoundaryPatch
		solid      = getProperty(properties, 0x1A)
		dimLength2 = getProperty(properties, 0x1B)               # The length of the extrusion in direction 2

		# Extends 1x distance, 2x distance, to, to next, between, all

		dirX = direction.get('dirX')
		dirY = direction.get('dirY')
		dirZ = direction.get('dirZ')

		len1 = getMM(dimLength)
		pad = None
		if (extend == 5): # 'ALL'
			if (isEqual1D(len1, 0)):
				if (solid is not None):
					len1 = self.getLength(solid, dirX, dirY, dirZ)
				else:
					len1 = self.getLength(surface, dirX, dirY, dirZ)
		if (len1 > 0):
			baseName = sectionNode.name
			base     = self.createBoundary(boundary, solid is not None)
			if (midplane): len1 = len1 / 2.0

			pad = newObject(self.doc, 'Part::Extrusion', name)
			pad.Base = base
			pad.Solid = solid is not None # FIXME!!
			pad.TaperAngle = -getGRAD(dimAngle) # Taper angle is in FreeCAD inverted!

			setDefaultViewObjectValues(pad)

			if (midplane):
				len2 = len1
				logInfo(u"        ... based on '%s' (symmetric len=%s) ...", baseName, len1)
			elif (dimLength2 is not None):
				len2 = getMM(dimLength2)
				logInfo(u"        ... based on '%s' (rev=%s, len=%s, len2=%s) ...", baseName, reversed, len1, len2)
			else:
				len2 = 0.0
				logInfo(u"        ... based on '%s' (rev=%s, len=%s) ...", baseName, reversed, len1)

			x    = dirX * (len1 + len2)
			y    = dirY * (len1 + len2)
			z    = dirZ * (len1 + len2)
			pad.Dir = (x, y, z)
			if (reversed):
				pad.Dir = (-x, -y, -z)
			pad.Placement.Base.x -= dirX * len2
			pad.Placement.Base.y -= dirY * len2
			pad.Placement.Base.z -= dirZ * len2
			self.hide([base])
		else:
			logWarning(u"        can't create new extrusion '%s' - (%04X): %s properties[04] is None!", name, padNode.index, padNode.typeName)
		return pad

	def createFxExtrude_Operation(self, padNode, sectionNode, name, nameExtension, className):
		properties = padNode.get('properties')
		baseData   = getProperty(properties, 0x1A)
		boolean    = None

		if (baseData is None):
			logWarning(u"    Can't find base info for (%04X): %s - not yet created!", padNode.index, name)
			return None
		tool = self.Create_FxExtrude_New(padNode, sectionNode, name + nameExtension)
		base    = self.findBase(baseData.next)
		if (base is not None):
			if (tool is not None): # no need to raise a warning as it's already done!
				return self.createBoolean(className, name, base, [tool])
			logWarning(u"        FxExtrude '%s': can't find/create tools object - executing %s!", name, className)
			return base
		logWarning(u"        FxExtrude '%s': can't find/create base object - executing %s!", name, className)
		return tool

	def Create_FxRevolve(self, revolveNode):
		participants = revolveNode.getParticipants()
		revolution = None

		if (participants):
			properties = revolveNode.get('properties')
			pathName   = participants[0].name
			operation  = getProperty(properties, 0x00) # PartFeatureOperation
			profile1   = getProperty(properties, 0x01) # FxBoundaryPatch
			lineAxis   = getProperty(properties, 0x02) # Line3D
			extend1    = getProperty(properties, 0x03) # ExtentType
			angle1     = getProperty(properties, 0x04) # Parameter
			direction  = getProperty(properties, 0x05) # PartFeatureExtentDirection
			#= getProperty(properties, 0x06) # ???
			#= getProperty(properties, 0x07) # FeatureDimensions
			#= getProperty(properties, 0x09) # CEFD3973_Enum
			#= getProperty(properties, 0x0A) # ParameterBoolean
			#= getProperty(properties, 0x0B) # FxBoundaryPatch
			#= getProperty(properties, 0x0C) # ParameterBoolean
			#= getProperty(properties, 0x0D) # ???
			#= getProperty(properties, 0x0E) # ???
			#= getProperty(properties, 0x0F) # ???
			isSurface  = getProperty(properties, 0x10) # ParameterBoolean
			angle2     = getProperty(properties, 0x12) # Parameter
			extend2    = getProperty(properties, 0x13) # ExtentType

			boundary   = self.createBoundary(profile1, not isSurface.get('value'))

			base       = p2v(lineAxis)
			axis       = p2v(lineAxis, 'dirX', 'dirY', 'dirZ')
			solid      = (isTrue(isSurface) == False)

			if (boundary):
				if (extend1.get('value') == 1): # 'Direction' => AngleExtent
					alpha = getGRAD(angle1)
					if (angle2 is None):
						if (direction.get('value') == 0): # positive
							logInfo(u"    ... based on '%s' (alpha=%s) ...", pathName, angle1.getValue())
							revolution = self.createRevolve(revolveNode.name, alpha, 0.0, boundary, axis, base, solid)
						elif (direction.get('value') == 1): # negative
							logInfo(u"    ... based on '%s' (alpha=%s, inverted) ...", pathName, angle1.getValue())
							revolution = self.createRevolve(revolveNode.name, 0.0, alpha, boundary, axis, base, solid)
						elif (direction.get('value') == 2): # symmetric
							logInfo(u"    ... based on '%s' (alpha=%s, symmetric) ...", pathName, angle1.getValue())
							revolution = self.createRevolve(revolveNode.name, alpha / 2.0, alpha / 2.0, boundary, axis, base, solid)
					else:
						logInfo(u"    ... based on '%s' (alpha=%s, beta=%s) ...", pathName, angle1.getValue(), angle2.getValue())
						beta = getGRAD(angle2)
						revolution = self.createRevolve(revolveNode.name, alpha, beta, boundary, axis, base, solid)
				elif (extend1.get('value') == 3): # 'Path' => FullSweepExtend
					logInfo(u"    ... based on '%s' (full) ...", pathName)
					revolution = self.createRevolve(revolveNode.name, 360.0, 0.0, boundary, axis, base, solid)
			else:
				logError(u"    Can't create revolution '%s' out of boundary (%04X)!", revolveNode.name,  profile1.index)
			if (revolution is not None): self.addBody(revolveNode, revolution, 0x11, 0x08)
		return revolution

	def Create_FxExtrude(self, extrudeNode):
		name = extrudeNode.name
		participants = extrudeNode.getParticipants()

		if (participants):
			sectionNode = participants[0].node
			self.getEntity(participants[0])

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
		fxDimData    = getProperty(properties, 0x05)
		solidRef     = getProperty(properties, 0x09)
		countRef     = getProperty(properties, 0x0C)
		angleRef     = getProperty(properties, 0x0D)
		axisData     = getProperty(properties, 0x0E)
		patternGeo   = None

		if (len(participants) == 0):
			participants = []
			label = patternNode.get('label')
			ref2 = label.get('ref_2')
			lst0 = ref2.get('lst0')
			if (lst0):
				for ref in lst0:
					if (ref.name in self.bodyNodes):
						participants.append(self.bodyNodes[lst0[0].name])
		if (len(participants) > 0):
			geos  = []
			count = getNominalValue(countRef)
			angle = Angle(getNominalValue(angleRef), pi/180.0, u'\xb0')
			center = p2v(axisData)
			axis   = center - p2v(axisData, 'dirX', 'dirY', 'dirZ')
			logInfo(u"        ... count=%d, angle=%s ...", count, angle)
			namePart = name
			if (len(participants) > 1):
				namePart = name + '_0'

			for baseRef in participants:
				cutGeo = None
				logInfo(u"        .... Base = '%s'", baseRef.name)
				baseGeo = self.getEntity(baseRef)
				if (baseGeo is None):
					baseGeo = self.findBase2(baseRef)
				if (baseGeo is not None):
					if (baseGeo.isDerivedFrom('Part::Cut')):
						cutGeo = baseGeo
						baseGeo = cutGeo.Tool
					patternGeo = Draft.makeArray(baseGeo, center, angle.getGRAD(), count, None, namePart)

					patternGeo.Axis = axis

					setDefaultViewObjectValues(patternGeo)
					geos.append(patternGeo)
				namePart = '%s_%d' % (name, len(geos))
			if (len(geos) > 1):
				patternGeo = self.createEntity(patternNode, 'Part::MultiFuse')
				patternGeo.Shapes = geos
			if (patternGeo is not None):
				if (cutGeo):
					cutGeo.Tool = patternGeo
				else:
					self.addSolidBody(patternNode, patternGeo, solidRef)
		return

	def adjustMidplane(self, pattern, direction, distance, fitted, count):
		d = getMM(distance) / 2.0
		if (isTrue(fitted) == False):
			d *= getNominalValue(count) - 1
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
		patternGeo    = None

		if (len(participants) == 0):
			participants = []
			label = patternNode.get('label')
			ref2 = label.get('ref_2')
			lst0 = ref2.get('lst0')
			if (lst0):
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
				# ensure that the sketch is already created!
				baseGeo = self.getEntity(baseRef)
				logInfo(u"        .... Base = '%s'", baseRef.name)
				if (baseGeo is None):
					baseGeo = self.findBase2(baseRef)
				if (baseGeo is not None):
					if (baseGeo.isDerivedFrom('Part::Cut')):
						cutGeo = baseGeo
						if (cutGeo.Tool): baseGeo = cutGeo.Tool
					patternGeo = Draft.makeArray(baseGeo, dir1, dir2, count1, count2, namePart)

					if (isTrue(midplane1Ref)): self.adjustMidplane(patternGeo, dir1Ref, distance1Ref, fitted1Ref, count1Ref)
					if (isTrue(midplane2Ref)): self.adjustMidplane(patternGeo, dir2Ref, distance2Ref, fitted2Ref, count2Ref)

					setDefaultViewObjectValues(patternGeo)
					geos.append(patternGeo)
				namePart = '%s_%d' % (name, len(geos))
			if (len(geos) > 1):
				patternGeo = self.createEntity(patternNode, 'Part::MultiFuse')
				patternGeo.Shapes = geos
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
		keepToolData  = getProperty(properties, 0x03) # not used
		operation = operationData.get('value')
		if (operation == FreeCADImporter.FX_EXTRUDE_CUT):
			className = 'Cut'
		elif (operation == FreeCADImporter.FX_EXTRUDE_JOIN):
			className = 'MultiFuse'
		elif (operation == FreeCADImporter.FX_EXTRUDE_INTERSECTION):
			className = 'MultiCommon'
		else:
			logWarning(u"        FxCombine: don't know how to '%s' - (%04X): %s!", operationData.node.getValueText(), combineNode.index, combineNode.typeName)
			return
		baseGeo       = self.findBase2(bodyRef)
		toolGeos      = self.findGeometries(sourceData.next)
		if ((baseGeo is not None) and (len(toolGeos) > 0)):
			cmbineGeo = self.createBoolean(className, name, baseGeo, toolGeos)
			if (cmbineGeo is None):
				logError(u"        ....Failed to create combination!")
			else:
				self.addSolidBody(combineNode, cmbineGeo, bodyRef)
		return

	def Create_FxMirror(self, mirrorNode):
		name          = mirrorNode.name
		participants  = mirrorNode.get('participants')
		properties    = mirrorNode.get('properties')
		planeRef      = getProperty(properties, 0x0C)
		base          = p2v(planeRef, 'b_x', 'b_y', 'b_z')
		normal        = p2v(planeRef, 'n_x', 'n_y', 'n_z')
		logInfo(u"    adding FxMirror '%s' ...", name)

		mirrors = []
		mirrorGeo = None
		if (len(participants) > 1):
			nameGeo = name + '_0'
		else:
			nameGeo = name

		for ref in participants:
			baseGeo = self.getEntity(ref)
			if (baseGeo is not None):
				mirrorGeo = newObject(self.doc, 'Part::Mirroring', nameGeo)
				mirrorGeo.Source = baseGeo
				mirrorGeo.Base   = base
				mirrorGeo.Normal = normal
				adjustViewObject(mirrorGeo, baseGeo)
				mirrors.append(mirrorGeo)
			nameGeo = '%s_%d' %(name, len(mirrors))
		if (len(mirrors) > 1):
			mirrorGeo = self.createBoolean('MultiCommon', name, mirrors[0], mirrors[1:])
			if (mirrorGeo is None):
				logError(u"        ....Failed to create combination!")
		if (mirrorGeo):
			self.addSolidBody(mirrorNode, mirrorGeo, getProperty(properties, 0x09))

		return

	def Create_FxHole(self, holeNode):
		name           = holeNode.name
		defRef         = holeNode.get('label')
		properties     = holeNode.get('properties')
		holeType       = getProperty(properties, 0x00)
		holeDiam_1     = getProperty(properties, 0x01)
		holeDepth_1    = getProperty(properties, 0x02)
		holeDiam_2     = getProperty(properties, 0x03)
		holeDepth_2    = getProperty(properties, 0x04)
		holeAngle_2    = getProperty(properties, 0x05)
		pointAngle     = getProperty(properties, 0x06)
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
		threadDiam    = getProperty(properties, 0x14)
		#    = getProperty(properties, 0x15)	# <=> placement == "linear"
		#    = getProperty(properties, 0x16)	#
		# 0x17 ???
		baseData      = getProperty(properties, 0x18)
		vec3D         = None

		if (holeType is not None):
			base = self.findBase(baseData.next)

			if (base is None):
				logWarning(u"    Can't find base info for (%04X): %s - not yet created!", holeNode.index, name)
			else:
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
		clients = clientNode.getParticipants()
		# create a subfolder
		name = clientNode.name
		if (len(name) == 0):
			name = node.typeName
		if (INVALID_NAME.match(name)):
			fx = createGroup(self.doc, '_' + name)
		else:
			fx = createGroup(self.doc, name)
		# add/move all objects to this folder
		for client in clients:
			clientGeo = self.getEntity(client)
			if (clientGeo is not None):
				fx.addObject(client.sketchEntity)
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
			self.hide(sections)
			setDefaultViewObjectValues(loftGeo)
			self.addBody(loftNode, loftGeo, 0x0D, 0x06)
		return

	def Create_FxLoftedFlange(self, node):
		defNode = node.get('properties')[0]
		defNode.handled = True
		bendNode   = node.get('properties')[0]
		properties     = defNode.get('properties')
		surface        = getProperty(properties, 0x00) # SurfaceBody 'Solid1'
		profile1       = getProperty(properties, 0x01) # A477243B
		profile2       = getProperty(properties, 0x02) # A477243B
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
		edgeProxies    = getProperty(properties, 0x0F) # EdgeCollectionProxy
		boundary1 = self.createBoundary(profile1, surface is None)
		boundary2 = self.createBoundary(profile2, surface is None)
		sections         = [boundary1, boundary2]
		loftGeo          = self.createEntity(defNode, 'Part::Loft')
		loftGeo.Sections = sections
		loftGeo.Ruled    = True  #isTrue(ruled)
		loftGeo.Closed   = False #isTrue(closed)
		loftGeo.Solid    = False #
		self.hide(sections)
		setDefaultViewObjectValues(loftGeo)
		self.addSurfaceBody(defNode, loftGeo, surface)
		return

	def Create_FxSweep(self, sweepNode):
		properties    = sweepNode.get('properties')
		definitionRef = sweepNode.get('label')
		solid         = (definitionRef.typeName == 'Label')
		boundary      = getProperty(properties, 0x00)
		profile1      = getProperty(properties, 0x01) # A477243B or FC203F47
		#= getProperty(properties, 0x02) # PartFeatureOperation or 90874D63
		taperAngle    = getProperty(properties, 0x03) # Parameter
		#= getProperty(properties, 0x04) # ExtentType
		#= getProperty(properties, 0x05) # ???
		#= getProperty(properties, 0x07) # FeatureDimensions
		#= getProperty(properties, 0x08) # SweepType=Path
		frenet        = getProperty(properties, 0x09) # SweepProfileOrientation, e.g. 'NormalToPath', other not yet supported by FreeCAD
		scaling       = getProperty(properties, 0x0A) # SweepProfileScaling, e.g. 'XY', other not yet supported by FreeCAD
		profile2      = getProperty(properties, 0x0B) # A477243B
		#= getProperty(properties, 0x0C): ???
		#= getProperty(properties, 0x0D): ???
		skip   = []

		path = self.createBoundary(profile1, solid is not None)
		if (path is None):
			profile = sweepNode.getParticipants()[1]
			path = self.getEntity(profile)

		edges = self.getEdges(path)
		if (len(edges) > 0):
			sections          = [self.createBoundary(boundary, solid is not None)]
			sweepGeo          = self.createEntity(sweepNode, 'Part::Sweep')
			sweepGeo.Sections = sections
			sweepGeo.Spine    = (path, edges)
			sweepGeo.Solid    = solid
			#sweepGeo.Frenet   = (frenet.getValueText() == 'ParallelToOriginalProfile')
			self.hide(sections)
			self.hide([path])
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
		#= getProperty(properties, 0x0E) # Enum_637B1CC1
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
				thickenGeo.Value = - getCoord(distance, 'valueNominal')
			else:
				#TODO: symmetricDir - create a fusion of two thicken geometries
				thickenGeo.Value = getCoord(distance, 'valueNominal')
			thickenGeo.Mode = 'Skin'          # {Skin, Pipe, RectoVerso}
			thickenGeo.Join = 'Intersection'  # {Arc, Tangent, Intersection}
			thickenGeo.Intersection = False
			thickenGeo.SelfIntersection = False
			if (hasattr(thickenGeo, 'Fill')): thickenGeo.Fill = solid is not None
			offset = -sourceOffsets[key]
			if ((offset != 0.0) and (len(source.Shape.Faces)>0)):
				normal = source.Shape.Faces[0].normalAt(0,0)
				thickenGeo.Placement.Base.x += source.Placement.Base.x - normal.x * offset
				thickenGeo.Placement.Base.y += source.Placement.Base.y - normal.y * offset
				thickenGeo.Placement.Base.z += source.Placement.Base.z - normal.z * offset
			adjustViewObject(thickenGeo, source)
			if (isTrue(verticalSurface)):
				self.addBody(thickenNode, thickenGeo, 0x0F, 0x08)
			else:
				self.addBody(thickenNode, thickenGeo, 0x0F, 0x0B)
		self.hide(sourceGeos.values())
		return

	def Create_FxCoil(self, coilNode):
		properties  = coilNode.get('properties')
		operation   = getProperty(properties, 0x00) # PartFeatureOperation=Join
		profile     = getProperty(properties, 0x01) # FxBoundaryPatch
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

		boundary = self.createBoundary(profile, solid is not None)
		base    = p2v(axis)
		dir     = p2v(axis, 'dirX', 'dirY', 'dirZ').normalize()
		if (isTrue(negative)): dir = dir.negative()

		sweepGeo = self.createEntity(coilNode, 'Part::Sweep')
		r = revolutions.getValue().x
		if (coilType.get('value') == 3):
			coilGeo = newObject(self.doc, 'Part::Spiral', sweepGeo.Name + '_coil')
			coilGeo.Growth = getMM(pitch)
			coilGeo.Rotations = revolutions.getValue().x
			if (isTrue(rotate)): dir = dir.negative()
		else:
			coilGeo = newObject(self.doc, 'Part::Helix', sweepGeo.Name + '_coil')
			coilGeo.Pitch  = getMM(pitch)
			coilGeo.Height = getMM(height)
			if (coilType.get('value') == 0):   # PitchAndRevolution
				coilGeo.Height = getMM(pitch) * revolutions.getValue().x
			elif (coilType.get('value') == 1): # RevolutionAndHeight
				coilGeo.Pitch  = getMM(height) /  revolutions.getValue().x
			coilGeo.LocalCoord = 1 - rotate.get('clockwise') # 0 = "Left handed"; 1= "Right handed"
			coilGeo.Angle      = getGRAD(taperAngle)
		c   = boundary.Shape.BoundBox.Center
		r   = c.distanceToLine(base, dir) # Helix-Radius
		b   = VEC().projectToLine(c-base, dir).normalize()
		z   = VEC(0,0,1) # zAxis
		rot = ROT(z.cross(dir), degrees(z.getAngle(dir)))
		p1  = PLC((c + b*r), rot)
		x   = rot.multVec(VEC(-1, 0, 0))
		p2  = PLC(VEC(), ROT(z, degrees(x.getAngle(b))))
		coilGeo.Radius     = r

		coilGeo.Placement  = p1.multiply(p2)

		#TODO: add flat start / end to coil wire
		if (isTrue(startIsFlat)):
			pass
		if (isTrue(endIsFlat)):
			pass

		sweepGeo.Sections  = [boundary]
		sweepGeo.Spine     = (coilGeo, [])
		sweepGeo.Solid     = surface is None
		sweepGeo.Frenet    = True
		setDefaultViewObjectValues(sweepGeo)

		self.addBody(coilNode, sweepGeo, 0x13, 0x11)
		self.hide([coilGeo])

		return

	def Create_FxChamfer(self, chamferNode):
		properties  = chamferNode.get('properties')
		edgeProxies = getProperty(properties, 0x00) # edge proxies
		faceProxies = getProperty(properties, 0x01) # base faces for the edges
		dim1        = getProperty(properties, 0x02) # dimension start
		dim2        = getProperty(properties, 0x03) # dimension end
		#           = getProperty(properties, 0x04) # boolean 'True'
		flip        = getProperty(properties, 0x05) # flip directions
		#           = getProperty(properties, 0x06) # corner setback (boolean) => not supported!
		#           = getProperty(properties, 0x07) # !!!never seen!!!
		dimensions  = getProperty(properties, 0x08) # FeatureDimensions
		preserve    = getProperty(properties, 0x09) # preserve all features
		angle       = getProperty(properties, 0x0A) # Angle
		body        = getProperty(properties, 0x0B) # SolidBody

		mmDim1      = getMM(dim1)
		mmDim2      = getMM(dim2)

		bases, edges = self.getBasesAndEdges(edgeProxies.get('edges'))
		if (len(bases) < 1):
			logWarning("    .... Can't apply FxCamfer \'%s\' for no bases (using last active body)!", chamferNode.name)
			bases.append(self.lastActiveBody.sketchEntity)
		geos = []

		for base in bases:
			chamferGeo = self.createEntity(chamferNode, 'Part::Chamfer')
			chamferGeo.Base = bases[0]
			chamferGeo.Edges = [(edgeIdx, mmDim1, mmDim2) for edgeIdx in edges]
			setDefaultViewObjectValues(chamferGeo)
			geos.append(chamferGeo)

		if (len(geos) > 1):
			chamferGeo = geos[0].Shape.multiFuse([part.Shape for part in geos[1:]])
			chamferGeo = newObject(self.doc, 'Part::Feature', '%s' %(chamferNode.name))
		else:
			chamferGeo = geos[0]

		self.addSolidBody(chamferNode, chamferGeo, body)
		self.hide(bases)
		return

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
		# = getProperty(properties, 0x0F) # SolidBody 'Solid1'
		# = getProperty(properties, 0x10) # SolidBody 'Solid1'

#		self.addSolidBody(filletNode, filletGeo, body)
#		self.hide(bases)

		return

	def Create_MeshFolder(self, meshFolderNode):
		logInfo(u"    creating MeshFolder '%s' ...", meshFolderNode.name)
		folder = createGroup(self.doc, meshFolderNode.name)

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
						geo = newObject(self.doc, 'Mesh::Feature', name)
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

	def Create_FxExtend(self, extendNode):
		properties = extendNode.get('properties')
		edges  = getProperty(properties, 0x00) # EdgeCollectionProxy
		# = getProperty(properties, 0x01) # FxExtend
		fxType = getProperty(properties, 0x02) # ExtentType=To
		dist   = getProperty(properties, 0x03) # Parameter 'd2'=1.75mm
		face   = getProperty(properties, 0x04) # Face <=> extendType == to
		# = getProperty(properties, 0x06) # bool
		surf   = getProperty(properties, 0x07) # SurfaceBody 'Fläche2'
		return notYetImplemented(extendNode)

	def Create_FxBoss(self, bossNode):                           return notYetImplemented(bossNode) # MultiFuse Geometry
	def Create_FxBoundaryPatch(self, boundaryPatchNode):         return notYetImplemented(boundaryPatchNode) # Sketches, Edges
	def Create_FxCoreCavity(self, coreCavityNode):               return notYetImplemented(coreCavityNode)
	def Create_FxCut(self, cutNode):                             return notYetImplemented(cutNode)
	def Create_FxDecal(self, decalNode):                         return notYetImplemented(decalNode)
	def Create_FxDirectEdit(self, directEditNode):               return notYetImplemented(directEditNode)
	def Create_FxEmboss(self, embossNode):                       return notYetImplemented(embossNode)
	def Create_FxFaceDelete(self, faceNode):                     return notYetImplemented(faceNode)
	def Create_FxFaceDraft(self, faceNode):                      return notYetImplemented(faceNode)
	def Create_FxFaceMove(self, faceNode):                       return notYetImplemented(faceNode)
	def Create_FxFaceOffset(self, faceNode):                     return notYetImplemented(faceNode)
	def Create_FxFaceReplace(self, faceNode):                    return notYetImplemented(faceNode)
	def Create_FxFilletRule(self, filletNode):                   return notYetImplemented(filletNode)
	def Create_FxFreeform(self, freeformNode):                   return notYetImplemented(freeformNode)
	def Create_FxGrill(self, grillNode):                         return notYetImplemented(grillNode)
	def Create_FxLip(self, lipNode):                             return notYetImplemented(lipNode)
	def Create_FxMidSurface(self, midSurfaceNode):               return notYetImplemented(midSurfaceNode)
	def Create_FxMove(self, moveNode):                           return notYetImplemented(moveNode)
	def Create_FxNonParametricBase(self, nonParametricBaseNode): return notYetImplemented(nonParametricBaseNode)
	def Create_FxPatternSketchDriven(self, patternNode):         return notYetImplemented(patternNode)
	def Create_FxPresentationMesh(self, presentationMeshNode):   return notYetImplemented(presentationMeshNode)
	def Create_FxReference(self, referenceNode):                 return notYetImplemented(referenceNode)
	def Create_FxRest(self, restNode):                           return notYetImplemented(restNode)
	def Create_FxRib(self, ribNode):                             return notYetImplemented(ribNode)
	def Create_FxSculpt(self, sculptNode):                       return notYetImplemented(sculptNode)
	def Create_FxShell(self, shellNode):                         return notYetImplemented(shellNode)
	def Create_FxSnapFit(self, snapFitNode):                     return notYetImplemented(snapFitNode) # Cut Geometry (Wedge - Cube)
	def Create_FxTrim(self, trimNode):                           return notYetImplemented(trimNode)
	def Create_FxPlate(self, trimNode):                          return notYetImplemented(trimNode)

	# Features requiring Nurbs
	def Create_FxAliasFreeform(self, aliasFreeformNode):         return notYetImplemented(aliasFreeformNode)

	# Features requiring BOPTools
	def Create_FxSplit(self, splitNode):                         return notYetImplemented(splitNode)

	# Features requiring SheetMetal
	def Create_FxBend(self, bendNode):                           return notYetImplemented(bendNode)
	def Create_FxBendCosmetic(self, bendNode):                   return notYetImplemented(bendNode)
	def Create_FxContourRoll(self, contourRollNode):             return notYetImplemented(contourRollNode)
	def Create_FxCorner(self, cornerNode):                       return notYetImplemented(cornerNode)
	def Create_FxCornerChamfer(self, cornerNode):                return notYetImplemented(cornerNode)
	def Create_FxFace(self, faceNode):                           return notYetImplemented(faceNode)
	def Create_FxFlange(self, flangeNode):                       return notYetImplemented(flangeNode)
	def Create_FxFlangeContour(self, flangeNode):                return notYetImplemented(flangeNode)
	def Create_FxFold(self, foldNode):                           return notYetImplemented(foldNode)
	def Create_FxHem(self, hemNode):                             return notYetImplemented(hemNode)
	def Create_FxKnit(self, knitNode):                           return notYetImplemented(knitNode)
	def Create_FxRefold(self, refoldNode):                       return notYetImplemented(refoldNode)
	def Create_FxRip(self, ripNode):                             return notYetImplemented(ripNode)
	def Create_FxUnfold(self, unfoldNode):                       return notYetImplemented(unfoldNode)
	def Create_FxLoftedFlangeDefinition(self, fxNode):           return notYetImplemented(fxNode)

	def Create_FxThread(self, threadNode):                       return notSupportedNode(threadNode) # https://www.freecadweb.org/wiki/Thread_for_Screw_Tutorial/de
	def Create_FxPunchTool(self, punchToolNode):                 return notSupportedNode(punchToolNode)
	def Create_FxiFeature(self, iFeatureNode):                   return notSupportedNode(iFeatureNode)

	def Create_FxUnknown(self, unknownNode):
		logWarning(u"    Can't process unknown Feature '%s' - probably an unsupported iFeature!", unknownNode.name)
		return

	def Create_Feature(self, featureNode):
		name  = featureNode.getSubTypeName()
		index = featureNode.index
		logInfo(u"    adding Fx%s '%s' ...", name, featureNode.name)
		createFxObj = getattr(self, 'Create_Fx%s' %(name))
		createFxObj(featureNode)

		adjustFxColor(featureNode.sketchEntity, featureNode.get('fxColor'))

		self.doc.recompute()
		return

	def addSketch_Spline3D_Curve(self, bezierNode, edges):
		points=[]
		for entity in bezierNode.get('entities'):
			if (entity.typeName == 'Point3D'):
				points.append(p2v(entity))

		if (len(points) > 1):
			spline = Part.BSplineCurve()
			spline.interpolate(points)
			addSketch3D(edges, spline, isConstructionMode(bezierNode), bezierNode)
		else:
			logError(u"ERROR> Bezier requires at least 2 points - found only %d!", len(points))
		return

	def addSketch_BSpline3D(self, bsplineNode, edges):
		points=[]
		for p in bsplineNode.get('points'):
			points.append(p2v(p))

		bspline = Part.BSplineCurve()
		bspline.interpolate(points, False)
		addSketch3D(edges, bspline, isConstructionMode(bsplineNode), bsplineNode)
		bezierNode = bsplineNode.get('bezier')
		bezierNode.setSketchEntity(-1, bspline)
		return

	def addSketch_Bezier3D(self, bezierNode, edges):
		# handled together with either Spline3D_Curve or BSpline3D
		return

	def addSketch_Plane(self, lineNode, edges):                          return
	def addSketch_Spline3D_Fixed(self, splineNode, edges):               return
	def addSketch_Spiral3D_Curve(self, spiralNode, edges):               return

	def addSketch_Dimension_Length3D(self, dimensionNode, edges):        return notSupportedNode(dimensionNode)
	def addSketch_Dimension_Angle2Planes3D(self, dimensionNode, edges):  return notSupportedNode(dimensionNode)

	def addSketch_Geometric_Bend3D(self, geometricNode, edges):
		if (SKIP_CONSTRAINTS & BIT_GEO_BEND == 0): return
		entities = geometricNode.get('lst0')
		p1  = entities[0] # connection point of Line 1 and 2
		l1  = entities[1] # 1st line
		l2  = entities[2] # 2nd line
		arc = entities[3] # bend arc
		p2  = entities[4] # new end point of 1st line and start angle of arc
		p3  = entities[5] # new start point of 2nd line and sweep angle of arc

		replacePoint(edges, p1, l1, p2)
		replacePoint(edges, p1, l2, p3)
		entity = arc.sketchEntity
		circle = Part.Circle(entity.Center, entity.Axis, entity.Radius)
		a = circle.parameter(p2v(p2))
		b = circle.parameter(p2v(p2))
		replaceEntity(edges, arc, Part.ArcOfCircle(circle, a, b))
		return

	def addSketch_Geometric_Custom3D(self, geometricNode, edges):        return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Coincident3D(self, geometricNode, edges):    return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Collinear3D(self, geometricNode, edges):     return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Helical3D(self, geometricNode, edges):       return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Horizontal3D(self, geometricNode, edges):    return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Smooth3D(self, geometricNode, edges):        return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Parallel3D(self, geometricNode, edges):      return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Perpendicular3D(self, geometricNode, edges): return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Radius3D(self, geometricNode, edges):        return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Tangential3D(self, geometricNode, edges):    return None # notSupportedNode(geometricNode)
	def addSketch_Geometric_Vertical3D(self, geometricNode, edges):      return None # notSupportedNode(geometricNode)

	def addSketch_4F240E1C(self, node, edges): return

	def Create_BrowserFolder(self, originNode):
		# Skip creation of origin objects.
		child = originNode.first
		while (child):
			child.handled = True
			child = child.next

		return

	def Create_Line3D(self, lineNode):
#		#work axis not supported!
#		sketchObj = self.createEntity(lineNode, 'Part::Feature')
#		logInfo(u"    adding 3D-Line '%s' ...", sketchObj.Label)
#		edges = {}
#		self.addSketch_Line3D(lineNode, edges)
#		sketchObj.Shape = Part.Shape(edges.values())
#		if (self.root): self.root.addObject(sketchObj)
		return

	def Create_Plane(self, planeNode):                             return ignoreBranch(planeNode)
	def Create_BodiesFolder(self, folderNode):                     return ignoreBranch(folderNode)
	def Create_Circle3D(self, radiusNode):                         return ignoreBranch(radiusNode)
	def Create_DerivedAssembly(self, derivedAssemblyNode):         return notSupportedNode(derivedAssemblyNode)
	def Create_DerivedPart(self, derivedPartNode):                 return notSupportedNode(derivedPartNode)
	def Create_EndOfFeatures(self, stopNode):                      return ignoreBranch(stopNode)
	def Create_Group2D(self, groupNode):                           return ignoreBranch(groupNode)
	def Create_Group3D(self, groupNode):                           return ignoreBranch(groupNode)
	def Create_Point3D(self, pointNode):                           return ignoreBranch(pointNode)
	def Create_RDxVar(self, varNode):                              return ignoreBranch(varNode)
	def Create_RevolutionTransformation(self, transformationNode): return ignoreBranch(transformationNode)
	def Create_Sketch2DPlacementPlane(self, placementNode):        return ignoreBranch(surfaceNode)
	def Create_Sketch2DPlacement(self, placementNode):             return ignoreBranch(placementNode)
	def Create_SurfaceBody(self, surfaceBodyNode):                 return ignoreBranch(surfaceBodyNode)
	def Create_Text2D(self, textNode):                             return notSupportedNode(textNode)
	def Create_ParameterBoolean(self, valueNode):                  return ignoreBranch(valueNode)
	def Create_Blocks(self, blocksNode):                           return notYetImplemented(blocksNode)

	def Create_iPart(self, iPartNode):
		# create a iPart Table
		table = newObject(self.doc, 'Spreadsheet::Sheet', iPartNode.name)
		excel = iPartNode.get('excelWorkbook')
		wb = excel.get('workbook')
		if (wb is not None):
			sheet = wb.sheet_by_index(0)
			cols = range(0, sheet.ncols)
			for row in range(0, sheet.ncols):    # Iterate through rows
				for col in cols:    # Iterate through cols
					try:
						cell = sheet.cell(row, col)  # Get cell object by row, col
						setTableValue(table, col, row + 1, cell.value)
						# TODO: Add iPart feature to FreeCAD!!!
					except:
						pass
		return


	def Create_Dimension(self, dimensionNode):             return
	def Create_Direction(self, directionNode):             return
	def Create_Label(self, labelNode):                     return
	def Create_ModelAnnotations(self, modelNode):          return
	def Create_Transformation(self, transformationNode):   return
	def Create_UserCoordinateSystem(self, usrCrdSysNode):  return

	def Create_2B48A42B(self, node): return
	def Create_3902E4D1(self, node): return
	def Create_5844C14D(self, node): return
	def Create_CADC79F0(self, node): return
	def Create_EBA98FD3(self, node): return
	def Create_FBC6C635(self, node): return
	def Create_F3DBA9D8(self, node): return

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
			key      = translate(ref.name)
			mdlValue = u''
			tlrValue = u''
			remValue = u''
			valueNode.set('alias', 'T_Parameters.%s_' %(key))
			typeName = valueNode.typeName

			if (typeName == 'Parameter'):
				r = self.addReferencedParameters(table, r, valueNode)
				#nominalValue = getNominalValue(valueNode)
				#nominalFactor = valueNode.getUnitFactor()
				#nominalOffset = valueNode.getUnitOffset()
				#nominalUnit  = valueNode.data.getUnitName()
				#if (len(nominalUnit) > 0): nominalUnit = ' ' + nominalUnit
				#formula = '%s%s' %((nominalValue / nominalFactor)  - nominalOffset, nominalUnit)
				value   = valueNode.getValue().__str__()
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
					aliasValue = '%s_' %(key.replace(':', '_'))
					table.setAlias(u"B%d" %(r), aliasValue)
				except Exception as e:
					logError(u"    Can't set alias name for B%d - invalid name '%s' - %s!", r, aliasValue, e)

				logInfo(u"        A%d='%s'; B%d='%s'%s'%s%s", r, key, r, value, mdlValue, tlrValue, remValue)
				return r + 1
		return r

	def createParameterTable(self, partNode):
		parameters = partNode.get('parameters')
		table = newObject(self.doc, 'Spreadsheet::Sheet', u'T_Parameters')
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

	def importModel(self, root, fcDoc):
		dc = getModel().getDC()
		if (dc is not None):
			self.root           = root
			self.doc            = fcDoc
			self.mapConstraints = {}

			doc = dc.tree.getFirstChild('Document')

			elements = doc.get('elements')
			self.createParameterTable(elements.node)

			label = doc.get('label')
			lst = label.get('lst0') or []
			for ref in lst:
				self.getEntity(ref)
			if (self.doc):
				self.doc.recompute()

			# apply colors stored in graphics segment
			gr = getModel().getGraphics()
			if (gr is not None):
				for indexDC in gr.indexNodes:
					dcNode = dc.indexNodes[indexDC]
					entity = dcNode.sketchEntity
					if (entity is not None):
						grNode = gr.indexNodes[indexDC]
						color  = getBodyColor(grNode)
						adjustColor(entity, color)
		else:
			logWarning(u">>>No content to be displayed for DC<<<")
