# -*- coding: utf8 -*-

'''
importerFreeCAD.py
'''
import sys
import Draft
import Part
import Sketcher
import FreeCAD
import traceback
import re
from importerUtils   import logMessage, logWarning, logError, LOG, IFF, IntArr2Str, FloatArr2Str, getFileVersion
from importerClasses import RSeMetaData, Angle, Length, ParameterNode, ParameterTextNode, ValueNode, FeatureNode, AbstractValue, DataNode
from importerSegNode import AbstractNode
from math            import sqrt, fabs, tan, acos, atan2, degrees, radians, pi

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.4.0'
__status__      = 'In-Development'

SKIP_GEO_ALIGN_HORIZONTAL    = 1 <<  0
SKIP_GEO_ALIGN_VERTICAL      = 1 <<  1
SKIP_GEO_COINCIDENT          = 1 <<  2
SKIP_GEO_COLLINEAR           = 1 <<  3 # Workaround required
SKIP_GEO_EQUAL_LENGTH        = 1 <<  4
SKIP_GEO_EQUAL_RADIUS        = 1 <<  5
SKIP_GEO_FIX                 = 1 <<  6 # Workaround required
SKIP_GEO_HORIZONTAL          = 1 <<  7
SKIP_GEO_OFFSET              = 1 <<  8 # Workaround required
SKIP_GEO_PARALLEL            = 1 <<  9
SKIP_GEO_PERPENDICULAR       = 1 << 10
SKIP_GEO_POLYGON             = 1 << 11
SKIP_GEO_RADIUS              = 1 << 12
SKIP_GEO_SPLINEFITPOINT      = 1 << 13 # not supported
SKIP_GEO_SYMMETRY_LINE       = 1 << 14
SKIP_GEO_SYMMETRY_POINT      = 1 << 15
SKIP_GEO_TANGENTIAL          = 1 << 16
SKIP_GEO_VERTICAL            = 1 << 17
SKIP_DIM_ANGLE_2_LINE        = 1 << 18
SKIP_DIM_ANGLE_3_POINT       = 1 << 19 # Workaround required
SKIP_DIM_RADIUS              = 1 << 20
SKIP_DIM_DIAMETER            = 1 << 21 # Workaround required
SKIP_DIM_DISTANCE            = 1 << 22
SKIP_DIM_DISTANCE_X          = 1 << 23
SKIP_DIM_DISTANCE_Y          = 1 << 24
SKIP_DIM_OFFSET_SPLINE       = 1 << 25 # not supported

INVALID_NAME = re.compile('^[0-9].*')

# x 10                        2   2   1   1   0   0   0
# x  1                        4   0   6   2   8   4   0
#SKIP_CONSTRAINS_DEFAULT = 0b11111111111111111111111111
#SKIP_CONSTRAINS_DEFAULT = 0b00000000000000000000000100 # Only geometric coincidens
SKIP_CONSTRAINS_DEFAULT  = 0b01111100110001111010110111 # default values: no workarounds, nor unsupported constrains!
SKIP_CONSTRAINS = SKIP_CONSTRAINS_DEFAULT # will be updated by stored preferences!

def _enableConstraint(params, name, bit, preset):
	global SKIP_CONSTRAINS
	b = params.GetBool(name, preset)
	# clear the bit if already set.
	SKIP_CONSTRAINS &= ~bit
	if (b): SKIP_CONSTRAINS |= bit
	params.SetBool(name, b)
	return

def _initPreferences():
	global SKIP_CONSTRAINS
	SKIP_CONSTRAINS = 0x0
	params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/InventorLoader")
	_enableConstraint(params, 'Sketch.Constraint.Geometric.AlignHorizontal', SKIP_GEO_ALIGN_HORIZONTAL , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.AlignVertical',   SKIP_GEO_ALIGN_VERTICAL   , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Coincident',      SKIP_GEO_COINCIDENT       , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Colinear',        SKIP_GEO_COLLINEAR        , False)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.EqualLength',     SKIP_GEO_EQUAL_LENGTH     , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.EqualRadius',     SKIP_GEO_EQUAL_RADIUS     , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Fix',             SKIP_GEO_FIX              , False)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Horizontal',      SKIP_GEO_HORIZONTAL       , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Offset',          SKIP_GEO_OFFSET           , False)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Parallel',        SKIP_GEO_PARALLEL         , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Perpendicular',   SKIP_GEO_PERPENDICULAR    , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Polygon',         SKIP_GEO_POLYGON          , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Radius',          SKIP_GEO_RADIUS           , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.SplineFitPoint',  SKIP_GEO_SPLINEFITPOINT   , False)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.SymmetryLine',    SKIP_GEO_SYMMETRY_LINE    , False)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.SymmetryPoint',   SKIP_GEO_SYMMETRY_POINT   , False)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Tangential',      SKIP_GEO_TANGENTIAL       , True)
	_enableConstraint(params, 'Sketch.Constraint.Geometric.Vertical',        SKIP_GEO_VERTICAL         , True)
	_enableConstraint(params, 'Sketch.Constraint.Dimension.Angle2Line',      SKIP_DIM_ANGLE_2_LINE     , False)
	_enableConstraint(params, 'Sketch.Constraint.Dimension.Angle3Point',     SKIP_DIM_ANGLE_3_POINT    , False)
	_enableConstraint(params, 'Sketch.Constraint.Dimension.Radius',          SKIP_DIM_RADIUS           , True)
	_enableConstraint(params, 'Sketch.Constraint.Dimension.Diameter',        SKIP_DIM_DIAMETER         , True)
	_enableConstraint(params, 'Sketch.Constraint.Dimension.Distance',        SKIP_DIM_DISTANCE         , True)
	_enableConstraint(params, 'Sketch.Constraint.Dimension.DistanceX',       SKIP_DIM_DISTANCE_X       , True)
	_enableConstraint(params, 'Sketch.Constraint.Dimension.DistanceY',       SKIP_DIM_DISTANCE_Y       , True)
	_enableConstraint(params, 'Sketch.Constraint.Dimension.OffsetSpline',    SKIP_DIM_OFFSET_SPLINE    , False)

def ignoreBranch(node):
	return None

def notSupportedNode(node):
	logWarning('        ... %s not supported (yet?) - sorry' %(node.typeName))
	node.setSketchEntity(-1, None)
	return None

def notYetImplemented(node):
	logWarning('        ... %s not implemented yet - sorry' %(node.typeName))
	node.setSketchEntity(-1, None)
	return None

def createVector(x, y, z):
	return FreeCAD.Vector(x, y, z)

def newObject(doc, className, name):
	if (INVALID_NAME.match(name)):
		obj = doc.addObject(className, '_' + name.encode('utf8'))
	else:
		obj = doc.addObject(className, name.encode('utf8'))
	if (obj):
		obj.Label = name
	return obj

def createGroup(doc, name):
	if (doc):
		return newObject(doc, 'App::DocumentObjectGroup', name)
	return None

def isConstructionMode(node):
	if (node):
		s0 = node.get('s16_0')
		s1 = node.get('s16_1')
		if (s0 is None):
			logError('FATAL> (%04X): %s has no s16_0 parameter!' %(node.index, node.typeName))
		else:
			if ((s0 & 0x0040) > 0): return True
		if (s1 is None):
			logError('FATAL> (%04X): %s has no s16_0 parameter!' %(node.index, node.typeName))
		else:
			if ((s1 & 0x0008) > 0): return True
			if ((s1 & 0x0400) > 0): return True # Spline handle
	return False

def calcAngle2D(p1, p2):
	if ((p1 is not None) and (p2 is not None)):
		x1 = getX(p1)
		y1 = getY(p1)
		x2 = getX(p2)
		y2 = getY(p2)

		dx = (x2 - x1)
		dy = (y2 - y1)
		angle = atan2(dy, dx)
		if (angle < 0):
			angle += radians(360.0)
		return Angle(angle, pi/180.0, u'\xb0')
	return None

def calcAngle3D(x1, y1, z1, x2, y2, z2):
	s = (x1*x2 + y1*y2 + z1*z2)
	l1 = sqrt(x1*x1 + y1*y1 + z1*z1)
	l2 = sqrt(x2*x2 + y2*y2 + z2*z2)
	if ((l1 != 0) and (l2 != 0)):
		angle = acos(s/l1/l2)
	else:
		angle = radians(90.0)
	return Angle(angle, pi/180.0, u'\xb0')

def getCoord(point, coordName):
	c = point.get(coordName)
	if (c is None):
		logError('ERROR - (%04X): %s has no \'%s\' property!' %(point.index, point.typeName, coordName))
		return 0.0
	return c * 10.0

def getX(point):
	return getCoord(point, 'x')

def getY(point):
	return getCoord(point, 'y')

def getZ(point):
	return getCoord(point, 'z')

def getDistanceX(p, q):
	return 	getX(q) - getX(p)

def getDistanceY(p, q):
	return getY(q) - getY(p)

def getDistancePointPoint(p, q):
	dx = getDistanceX(p, q)
	dy = getDistanceY(p, q)
	return sqrt(dx*dx + dy*dy)

def getDistanceLinePoint(line, point):
	p = line.get('points')[0]
	q = line.get('points')[1]
	# Adjust vectors relative to P
	# Q becomes relative vector from P to end of segment
	qx = getDistanceX(p, q)
	qy = getDistanceY(p, q)
	# A becomes relative vector from P to test point
	ax = getDistanceX(p, point)
	ay = getDistanceY(p, point)
	dotProd = ax * qx + ay * qy
	# dotProd is the length of A
	# projected on P=>Q times the length of P=>Q
	projLenSq = dotProd * dotProd / (qx * qx + qy * qy)
	# Distance to line is now the length of the relative point
	# vector minus the length of its projection onto the line
	lenSq = ax * ax + ay * ay - projLenSq
	if (lenSq < 0):
	    lenSq = 0
	return sqrt(lenSq);

def getDistanceCircleLine(circle, line):
	point    = circle.get('refCenter')
	distance = getDistanceLinePoint(line, point)
	return distance - getCoord(circle, 'r')

def getDistanceCirclePoint(circle, point):
	center   = circle.get('refCenter')
	distance = getDistancePointPoint(center, point)
	return distance - getCoord(circle, 'r')

def getDistanceCircleCircle(circle1, circle2):
	center    = circle2.get('refCenter')
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
	raise BaseException('Don\'t know how to determine the distance between \'%s\' and \'%s\'!' %(type1, type2))

def getLengthLine(line):
	point1 = line.get('points')[0]
	point2 = line.get('points')[1]
	return getLengthPoints(point1, point2)

def addSketch2D(sketchObj, geometrie, mode, entityNode):
	index = sketchObj.addGeometry(geometrie, mode)
	entityNode.setSketchEntity(index, geometrie)
	return geometrie

def addSketch3D(edges, geometrie, mode, entityNode):
	geometrie.Construction = mode
	edges.append(geometrie)
	entityNode.setSketchEntity(-1, geometrie)
	return geometrie

def addEqualRadius2d(sketchObj, arc1, arc2):
	if (arc1 is not None):
		constraint = Sketcher.Constraint('Equal', arc1, arc2)
		sketchObj.addConstraint(constraint)
	return

def findEntityVertex(entity, point):
	entityName = entity.typeName
	if (entityName == 'Point2D'):
		return 1

	x = point.get('x')
	y = point.get('y')

	if (entityName == 'Circle2D' or entityName == 'Ellipse2D'):
		p2 = entity.get('refCenter')
		if ((x == p2.get('x')) and (y == p2.get('y'))):
			return 3
		points = getCirclePoints(entity)
	else:
		points = entity.get('points')

	if (not points is None):
		j = 0
		while (j < len(points)):
			point = points[j]
			if (point): # Might be None for closed circles
				if ((x == point.get('x')) and (y == point.get('y'))):
					return j + 1
			j += 1
	else:
		logError('FATAL: (%04X): %s has not attribute points!' %(entity.index, entityName))
	return -1

def getProperty(properties, index):
	if (index < len(properties)): return properties[index]
	return None

def getPropertyValue(properties, index, name):
	property = getProperty(properties, index)
	if (property): return property.get(name)
	return None

def getDimension(node, varName):
	dimension  = node.get(varName)

	if (dimension.typeName == 'Line2D'):
		dimension = DimensionValue(Length(getLengthLine(dimension)))
	elif (dimension.typeName == 'Point2D'):
		dimension = DimensionValue(Length(0))

	if (dimension.typeName != 'Parameter'):
		logError('Expected Dimension for (%04X): %s - NOT %s' %(node.index, node.typeName, dimension.typeName))

	return dimension

def getNextLineIndex(coincidens, startIndex):
	i = startIndex
	if (i < len(coincidens)):
		ref = coincidens[i]
		if (ref.typeName == 'Line2D'):
			return i
		return getNextLineIndex(coincidens, i + 1)
	return len(coincidens)

def getPlacement(placement):
	transformation = placement.get('transformation')
	matrix4x4      = transformation.getMatrix()

	# convert centimeter to millimeter
	matrix4x4.A14  *= 10.0
	matrix4x4.A24  *= 10.0
	matrix4x4.A34  *= 10.0

	return FreeCAD.Placement(matrix4x4)

def calcPointKey(point):
	if (point.typeName == 'BlockPoint2D'):
		point = point.get('refPoint')
	assert (point.typeName == 'Point2D'), 'point data is not Point2D <> (%04X): %s' %(point.index, point.typeName)
	return ('K%g_%g' %(getX(point), getY(point))).replace('-', '_').replace('.', '_')

def getCirclePoints(circle):
	points      = circle.get('points')
	center      = circle.get('refCenter')
	x_old       = None
	y_old       = None
	map         = {}
	j           = 0
	list        = []
	angleOffset = None

	while (j < len(points)):
		point = points[j]
		if (point):
			angle = calcAngle2D(center, point)
			if (angleOffset is None):
				angleOffset = angle.x
			angle.x -= angleOffset
			if (not angle.x in map):
				map[angle.x] = point
		j += 1

	if (len(map) > 0):
		keys = map.keys()
		keys.sort()
		while (keys[0] != 0.0):
			key = keys[0]
			keys.append(key)
			del keys[0]
		for key in keys:
			point = map[key]
			x_new = point.get('x')
			y_new = point.get('y')
			if ((x_new != x_old) or (y_new != y_old)):
				list.append(point)
				x_old = x_new
				y_old = y_new

	return list

def addCoincidentEntity(coincidens, entity):
	if (entity.typeName == 'Point2D'):
		entities = entity.get('entities')
		for ref in entities:
			addCoincidentEntity(coincidens, ref)
	else:
		for ref in coincidens:
			if (ref.index == entity.index): return # already added -> done!

		coincidens.append(entity)
	return

def getFirstBodyName(ref):
	name = ''

	if (ref):
		bodies = ref.get('bodies')
		if ((bodies) and (len(bodies) > 0)):
			name = bodies[0].name

	return name

def getNominalValue(node):
	assert (node is not None), 'Expected a parameter and not None!'
	value = node.get('valueNominal')
	assert (value is not None), 'Expected a ParameterValue and not %s' %(node.typeName)
	return value

#def getDistanceAndDir(node):
#	assert (node is not None), 'Expected a A5977BAA and not None!'
#	assert (node.typeName == 'A5977BAA'), 'Expected a A5977BAA and not %s!' %(node.typeName)
#	distance = 10.0
#	dir = createVector()
#	return dir, distance

def setDefaultViewObject(geo):
	if (geo  is None): return
	geo.ViewObject.DisplayMode  = 'Shaded' # Flat Lines, Shaded, Wireframe or Points
	geo.ViewObject.DrawStyle    = 'Solid'
	geo.ViewObject.Lighting     = 'Two side'
	geo.ViewObject.LineColor    = (1.0, 1.0, 1.0)
	geo.ViewObject.LineWidth    = 1.00
	geo.ViewObject.PointColor   = (1.0, 1.0, 1.0)
	geo.ViewObject.PointSize    = 1.00
	geo.ViewObject.ShapeColor   = (0.80, 0.80, 0.80)
	geo.ViewObject.Transparency = 0

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

def getEdges(wire):
	edges = []
	if (wire is not None):
		count = len(wire.Shape.Edges) + 1
		i = 1
		while (i < count):
			edges.append('Edge%i' %(i))
			i += 1

	return edges

def getValidName(node):
	name = node.name
	return name

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

	def __init__(self, root, doc):
		self.root           = root
		self.doc            = doc
		self.mapConstraints = None
		self.pointDataDict  = None
		self.bodyNodes      = {}
		self.sketchEdges    = {}
		_initPreferences()


	def getEntity(self, node):
		if (node):
			try:
				if (not isinstance(node, DataNode)): node = node.node
				if ((node.handled == False) and (node.valid)):
					node.handled = True
					importObject = getattr(self, 'Create_%s' %(node.typeName))
					importObject(node)
			except Exception as e:
				logError('Error in creating (%04X): %s - %s'  %(node.index, node.typeName, e))
				logError('>E: ' + traceback.format_exc())
				node.valid = False
			return node.sketchEntity
		return None

	def checkSketchIndex(self, sketchObj, node):
		if (node):
			if (not isinstance(node, DataNode)): node = node.node
			if ((node.handled == False) and (node.valid)):
				self.Create_Sketch2D_Node(sketchObj, node)
			if (node.valid):
				if (node.sketchIndex is None):
					logError('        ... Failed to create (%04X): %s' %(node.index, node.typeName))
				return  node.sketchIndex
		return None

	def addConstraint(self, sketchObj, constraint, key):
		index = sketchObj.addConstraint(constraint)
		self.mapConstraints[key] = constraint
		return index

	def hide(self, sections):
		for section in sections:
			section.ViewObject.Visibility = False
		return

	def addSolidBody(self, fxNode, obj3D, solid):
		fxNode.setSketchEntity(-1, obj3D)

		if (solid):
			bodies = solid.get('bodies')
			if ((bodies) and (len(bodies) > 0)):
				body = bodies[0]
				# overwrite previously added solids with the same name!
				self.bodyNodes[body.name] = fxNode
		return

	def addSurfaceBody(self, fxNode, obj3D, surface):
		fxNode.setSketchEntity(-1, obj3D)
		# overwrite previously added sourfaces with the same name!
		self.bodyNodes[surface.name] = fxNode
		return

	def addBody(self, fxNode, body, solidIdx, surfaceIdx):
		properties = fxNode.get('properties')
		solid = getProperty(properties, solidIdx)
		if (solid):
			self.addSolidBody(fxNode, body, solid)
		else:
			sourface = getProperty(properties, surfaceIdx)
			if(sourface):
				self.addSurfaceBody(fxNode, body, sourface)
		return

	def findBase(self, baseNode):
		if (baseNode is not None):
			assert (baseNode.typeName == 'FaceCollectionProxy'), 'FATA> Expected FaceCollectionProxy not (%04X): %s!' %(baseNode.index, baseNode.typeName)
			base = baseNode.get('refSolidBody')
			if (base):
				return self.findBase2(base)
			logError('ERROR> Base (%04X): %s not defined!' %(baseNode.index, baseNode.typeName))
		return None

	def findBase2(self, base):
		baseGeo = None
		if (base is not None):
			name = getFirstBodyName(base)
			if (name in self.bodyNodes):
				baseGeo = self.bodyNodes[name].sketchEntity
				if (baseGeo is None):
					logWarning('    Base2 (%04X): %s -> (%04X): %s not yet created!' %(base.index, baseNode.typeName, bodyNode.index, bodyNode.typeName))
				else:
					logMessage('        ... Base2 = \'%s\'' %(name), LOG.LOG_INFO)
			else:
				logWarning('    Base2 (%04X): %s -> \'%s\' nod found!' %(base.index, base.typeName, name))
		else:
			logWarning('    Base2: ref is None!')

		return baseGeo

	def findSurface(self, node):
		name = node.name
		if (name in self.bodyNodes):
			return self.getEntity(self.bodyNodes[name])
		return None

	def findGeometries(self, node):
		geometries = []
		if (node is not None):
			assert (node.typeName == 'FaceCollectionProxy'), 'FATA> (%04X): %s expected FaceCollectionProxy ' %(node.index, node.typeName)
			faces = node.get('faces')
			if (faces):
				for tool in faces:
					name = getFirstBodyName(tool)
					if (name in self.bodyNodes):
						toolGeo = self.bodyNodes[name].sketchEntity
						if (toolGeo is None):
							logWarning('        Tool (%04X): %s -> (%04X): %s not yet created' %(node.index, node.typeName, toolData.index, toolData.typeName))
						else:
							geometries.append(toolGeo)
							logMessage('        ... Tool = \'%s\'' %(name), LOG.LOG_INFO)
					else:
						logWarning('    Tool (%04X): %s -> \'%s\' nod found!' %(node.index, node.typeName, name))
			else:
				logError('ERROR> faces (%04X): %s not defined!' %(node.index, node.typeName))
		else:
			logWarning('    Tool: ref is None!')
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

	def getGeometryIndex(self, sketchObj, node, name):
		child = node.get(name)
		return self.checkSketchIndex(sketchObj, child)

	def addPoint2Dictionary(self, point):
		key = calcPointKey(point)

		if (not key in self.pointDataDict):
			entities = []
			entities.append(point)
			self.pointDataDict[key] = entities

		return

	def adjustIndexPos(self, data, index, pos, point):
		if ((data.typeName == 'Circle2D') or (data.typeName == 'Ellipse2D')):
			x = point.get('x')
			y = point.get('y')
			points = data.get('points')
			for ref in points:
				if (ref):
					if ((ref.get('x') == x) and (ref.get('y') == y) and (ref.sketchIndex != -1)):
						if (ref.sketchIndex is not None):
							index = ref.sketchIndex
						pos = ref.sketchPos
		return index, pos

	def addCoincidentConstraint(self, fixIndex, fixPos, fixName, move, sketchObj, point):
		constraint = None
		if (move):
			movName  = move.typeName
			movIndex = self.checkSketchIndex(sketchObj, move)

			if (movIndex is not None):
				movPos   = findEntityVertex(move, point)

				if (movPos < 0):
					if (fixPos < 0):
						logWarning('        ... can\'t add object on object coincident: between (%04X): %s and (%04X): %s failed - Feature not supported by FreeCAD!!!' %(fixIndex, fixName, movIndex, movName))
					else:
						constraint = Sketcher.Constraint('PointOnObject', fixIndex, fixPos, movIndex)
						logMessage('        ... added point on object constraint between %s %s/%s and %s %s' %(fixName[0:-2], fixIndex, fixPos, movName[0:-2], movIndex), LOG.LOG_INFO)
				else:
					movIndex, movPos = self.adjustIndexPos(move, movIndex, movPos, point)
					if (fixPos < 0):
						constraint = Sketcher.Constraint('PointOnObject', movIndex, movPos, fixIndex)
						logMessage('        ... added point on object constraint between %s %s/%s and %s %s' %(movName[0:-2], movIndex, movPos, fixName[0:-2], fixIndex), LOG.LOG_INFO)
					else:
						constraint = Sketcher.Constraint('Coincident', fixIndex, fixPos, movIndex, movPos)
						logMessage('        ... added coincident constraint between %s %s/%s and %s %s/%s' %(fixName[0:-2], fixIndex, fixPos, movName[0:-2], movIndex, movPos), LOG.LOG_INFO)
		return constraint

	def addSketch_ConstructionPoint2D(self, point, sketchObj):
		index = point.sketchIndex
		if ((index is None) or (index == -2)):
			mode = True
			x = getX(point)
			y = getY(point)
			part = Part.Point(createVector(x, y, 0))
			addSketch2D(sketchObj, part, mode, point)
		return point.sketchIndex

	def getPointIndexPos(self, sketchObj, point):
		key = calcPointKey(point)
		if (key in self.pointDataDict):
			entities = self.pointDataDict[key]
		else:
			entities = []
		# the first element is a point!
		if (len(entities) > 1):
			entity = entities[1]
			index  = self.checkSketchIndex(sketchObj, entity)
			pos    = findEntityVertex(entity, point)
		else:
			index  = self.addSketch_ConstructionPoint2D(point, sketchObj)
			pos    = 1
		return index, pos

	def getSketchEntityInfo(self, sketchObj, entity):
		if (entity.typeName == 'Point2D'):
			return self.getPointIndexPos(sketchObj, entity)
		entityIndex = self.checkSketchIndex(sketchObj, entity)
		return entityIndex, -1

	def fix2D(self, sketchObj, point):
		key = 'Fix_%X' %(point.index)
		if (not key in self.mapConstraints):
			x = getX(point)
			y = getY(point)
			index, pos = self.getSketchEntityInfo(sketchObj, point)
			if (index is not None):
				constraintX = Sketcher.Constraint('DistanceX', index, pos, x)
				constraintY = Sketcher.Constraint('DistanceY', index, pos, y)
				indexX = self.addConstraint(sketchObj, constraintX, key)
				indexY = self.addConstraint(sketchObj, constraintY, key)
		return

	def getCirclePointRefs(self, sketchObj, point, circleIndex):
		count = 0
		entities = point.get('entities')
		for entityRef in entities:
			if (entityRef.index != circleIndex):
				if (self.checkSketchIndex(sketchObj, entityRef) >= 0):
					count += 1
		return count

	def addDistanceConstraint(self, sketchObj, dimensionNode, skipMask, name, prefix):
		if (SKIP_CONSTRAINS & skipMask == 0): return
		entity1 = dimensionNode.get('refEntity1')
		entity2 = dimensionNode.get('refEntity2')
		entity1Name = entity1.typeName[0:-2]
		entity2Name = entity2.typeName[0:-2]
		index1, pos1 = self.getSketchEntityInfo(sketchObj, entity1)
		index2, pos2 = self.getSketchEntityInfo(sketchObj, entity2)

		prefix = IFF(len(prefix)>0, '%s ' %(prefix), '')

		if (index1 is None):
			logWarning('        ... skipped %sdimension beween %s and %s - entity 1 (%04X) has no index!' %(prefix, entity1Name, entity2Name, entity1.index))
		elif (index2 is None):
			logWarning('        ... skipped %sdimension beween %s and %s - entity 2 (%04X) has no index!' %(prefix, entity1Name, entity2Name, entity2.index))
		else:
			constraint = None
			key = '%s_%s_%s' %(constraint, index1, index2)
			if (not key in self.mapConstraints):
				lengthMM = getLengthPoints(entity1, entity2)
				if (pos1 < 0):
					if (pos2 < 0):
						# other distances are not supported by FreeCAD!
						if ((entity1.typeName == 'Line2D') and (entity2.typeName == 'Line2D')):
							# hope that both lines are parallel!!!
							constraint = Sketcher.Constraint(name, index1, 1, index2, lengthMM)
					else:
						constraint = Sketcher.Constraint(name, index2, pos2, index1, lengthMM)
				elif  (pos2 < 0):
					constraint = Sketcher.Constraint(name, index1, pos1, index2, lengthMM)
				else:
					constraint = Sketcher.Constraint(name, index1, pos1, index2, pos2, lengthMM)

				if (constraint):
					dimension = getDimension(dimensionNode, 'refParameter')
					index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
					dimensionNode.setSketchEntity(index, constraint)
					length = Length(lengthMM, 1.0, 'mm')
					logMessage('        ... added %sdistance \'%s\' = %s' %(prefix, constraint.Name, length), LOG.LOG_INFO)
				else:
					logWarning('        ... can\'t create dimension constraint between (%04X): %s and (%04X): %s - not supported by FreeCAD!' %(entity1.index, entity1Name, entity2.index, entity2Name))
		return

	def profile2Section(self, participant):
		face      = participant.get('refFace')
		surface   = participant.data.segment.indexNodes[face.get('indexRefs')[0]]
#		wireIndex = surface.get('wireIndex')
		wireIndex = participant.get('number')
		body      = surface.get('refBody')
		node      = None

		if (body.name in self.bodyNodes):
			node = self.bodyNodes[body.name]
		else:
			label = surface.get('label')
			node  = self.getEntity(participant.data.segment.indexNodes[label.get('idxCreator')])

		entity  = self.getEntity(node)
		if (entity is not None):
			# create an entity that can be featured (e.g. loft, sweep, ...)
			section = newObject(self.doc, 'Part::Feature', participant.name)
			self.doc.recompute()

			# Convert Inventor-Index to FreeCAD-Index
			if (wireIndex == 0):   wireIndex = 1
			elif (wireIndex == 1): wireIndex = 0

			section.Shape = entity.Shape.Wires[wireIndex]
			return section
		return None

	def collectSection(self, participant):
		if (participant.typeName == 'Sketch2D'):           return self.getEntity(participant)
		elif (participant.typeName == 'Sketch3D'):         return self.getEntity(participant)
		elif (participant.typeName == 'ProfileSelection'): return self.profile2Section(participant)
		return None

	def createBoundary(self, boundaryPatch):
		boundary = None
		next = boundaryPatch.node.next
		shapeEdges = []
		cnt = 0
		if ((next.typeName == 'F9884C43') or (next.typeName == '424EB7D7')):
			sketch   = next.get('refSketch')
			boundary = self.getEntity(sketch)
			for sketchEdges in next.get('lst0'):
				if (sketchEdges.typeName == 'A3277869'):
					cnt += len(sketchEdges.get('lst0'))
					for sketchEdge in sketchEdges.get('lst0'): # should be SketchEntityRef
						sketch = sketchEdge.get('refSketch')
						id = sketchEdge.get('associativeID')
						if (sketch.name in self.sketchEdges):
							edges = self.sketchEdges[sketch.name]
							try:
								shapeEdges.append(edges[id])
							except:
								print "ID=%d not in %s (%s)" %(id, edges, sketch.name)
			if (len(shapeEdges) > 0):
				edges = self.sketchEdges[next.get('refSketch').name]
				if (len(edges) != cnt):
					print "DEBUG %d != %d for %s" %(len(edges), cnt, next.get('refSketch').name)
					boundary = newObject(self.doc, 'Part::Feature', '%s_bp' %sketch.name)
					boundary.Shape = Part.Shape(shapeEdges)
					boundary.Placement = FreeCAD.Placement(sketch.sketchEntity.Placement.Base, sketch.sketchEntity.Placement.Rotation)
		return boundary

	def collectSections(self, fxNode, action, skip): #
		participants = fxNode.getParticipants()
		sections     = []

		for participant in participants:
			if (participant.index not in skip):
				section = self.collectSection(participant)
				if (section is not None):
					sections.append(section)
				else:
					logWarning('        ... don\'t know how to %s (%04X): %s \'%s\' - IGNORED!' %(action, participant.index, participant.typeName, participant.name))

		return sections

	def createBoolean(self, className, name, baseGeo, tools):
		booleanGeo = baseGeo
		if ((baseGeo is not None) and (len(tools) > 0)):
			booleanGeo = newObject(self.doc, 'Part::%s' %(className), name)
			if (className == 'Cut'):
				booleanGeo.Base = baseGeo
				booleanGeo.Tool = tools[0]
			else:
				booleanGeo.Shapes = [baseGeo] + tools
			adjustViewObject(booleanGeo, baseGeo)
		return booleanGeo

	def createCone(self, name, diameter2, angle, diameter1):
		R1 = 0.0
		R2 = 0.0
		if (diameter1):
			R1 = diameter1.getValue().getMM() / 2
		if (diameter2):
			R2 = diameter2.getValue().getMM() / 2
		h  = fabs(R1 - R2) / tan(angle.getValue().getRAD() / 2)
		conGeo = newObject(self.doc, 'Part::Cone', name)
		conGeo.Radius1 = R1
		conGeo.Radius2 = R2
		conGeo.Height = h
		conGeo.Placement.Base.z = -h
		return conGeo, h

	def createCylinder(self, name, diameter, height, drillPoint):
		r = diameter.getValue().getMM() / 2
		h1 = height.getValue().getMM()
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

	def CreateEntity(self, node, className):
		name = node.name
		if (len(name) == 0): name = node.typeName
		entity = newObject(self.doc, className, name)
		return entity

########################
	def addSketch_Geometric_Fix2D(self, constraintNode, sketchObj):
		'''
		A fix constraint doesn't exists in FreeCAD.
		Workaround: two distance constraints (X and Y)
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_FIX == 0): return
		return

	def addSketch_Geometric_PolygonCenter2D(self, constraintNode, sketchObj):
		# handled together with addSketch_Geometric_PolygonEdge2D
		return ignoreBranch(constraintNode)

	def addSketch_Geometric_PolygonEdge2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINS & SKIP_GEO_POLYGON == 0): return
		ref1 = constraintNode.get('ref_1')
		ref2 = constraintNode.get('ref_2')
		if ((ref1) and (ref1.typeName == 'Line2D') and (ref2) and (ref2.typeName == 'Line2D')):
			line1Index = self.checkSketchIndex(sketchObj, ref1)
			center   = constraintNode.get('refCenter')
			polygon  = constraintNode.get('refPolygonCenter1')

			if ((center) and (polygon)):
				if (center.typeName == 'Point2D'):
					circleIndex = polygon.get('circle')
					if (circleIndex is None):
						r = getDistanceLinePoint(ref1, center)
						x = getX(center)
						y = getY(center)
						circle = Part.Circle(createVector(x, y, 0), createVector(0, 0, 1), r)
						circleIndex = sketchObj.addGeometry(circle, True)
						polygon.set('circle', circleIndex)
						logMessage('        ... added \'polygon\' constraint', LOG.LOG_INFO)
					# it's sufficient to create only one Point On Object constraint.
					constraint = Sketcher.Constraint('PointOnObject', line1Index, 1, circleIndex)
					sketchObj.addConstraint(constraint)
				# TODO: What else could this be????
			# make the the two lines the same length
			line2Index = self.checkSketchIndex(sketchObj, ref2)
			constraint = Sketcher.Constraint('Equal', line1Index, line2Index)
			sketchObj.addConstraint(constraint)
		return

	def addSketch_Geometric_Coincident2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINS & SKIP_GEO_COINCIDENT == 0): return
		point = constraintNode.get('refPoint')
		if (point.typeName != 'Point2D'):
			entity = point
			point  = constraintNode.get('refObject')
		else:
			entity = constraintNode.get('refObject')
		key = calcPointKey(point)
		if (key in self.pointDataDict):
			coincidens = self.pointDataDict[key]
			addCoincidentEntity(coincidens, point)
			addCoincidentEntity(coincidens, entity)
		return

	def addSketch_Geometric_SymmetryPoint2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINS & SKIP_GEO_SYMMETRY_POINT == 0): return
		point = constraintNode.get('refPoint')
		symmetryIdx, symmetryPos = self.getPointIndexPos(sketchObj, point)

		moving = constraintNode.get('refObject')
		lineIdx =  self.checkSketchIndex(sketchObj, moving)

		if ((lineIdx is None) or (lineIdx < 0)):
			logWarning('        ... can\'t added symmetric constraint between Point and %s - no line index for (%04X)!' %(moving.typeName[0:-2], moving.index))
		elif ((symmetryIdx is None) or (symmetryIdx < 0) or (symmetryPos < -1)):
			logWarning('        ... can\'t added symmetric constraint between Point and %s - no point index for (%04X)!' %(moving.typeName[0:-2], constraintNode.get('refPoint').index))
		else:
			key = 'SymmetryPoint_%s_%s' %(lineIdx, symmetryIdx)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Symmetric', lineIdx, 1, lineIdx, 2, symmetryIdx, symmetryPos)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added symmetric constraint between Point %s and %s %s' %(symmetryIdx, moving.typeName[0:-2], lineIdx), LOG.LOG_INFO)
		return

	def addSketch_Geometric_SymmetryLine2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINS & SKIP_GEO_SYMMETRY_LINE == 0): return
		symmetry    = constraintNode.get('refLineSym')
		symmetryIdx =  self.checkSketchIndex(sketchObj, symmetry)

		line1 = constraintNode.get('refLine1')
		line2 = constraintNode.get('refLine2')
		line1Idx =  self.getPointIndexPos(sketchObj, line1)
		line2Idx =  self.getPointIndexPos(sketchObj, line2)

		if ((symmetryIdx is None) or (symmetryIdx < 0)):
			logWarning('        ... skipped symmetric constraint between lines - symmetry (%04X) has no index!' %(symmetry.index))
		elif ((line1Idx is None) or (line1Idx < 0)):
			logWarning('        ... skipped symmetric constraint between lines - line 1 (%04X) has no index!' %(line1.index))
		elif ((line2Idx is None) or (line2Idx < 0)):
			logWarning('        ... skipped symmetric constraint between lines - line 2 (%04X) has no index!' %(line2.index))
		else:
			key = 'SymmetricLine_%s_%s_%s' %(line1Idx, line2Idx, symmetryIdx)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Symmetric',line1Idx, 1, line2Idx, 1, symmetryIdx)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added symmetric constraint between lines %s, %s and %s' %(symmetryIdx, line1Idx, line2Idx), LOG.LOG_INFO)
		return

	def addSketch_Geometric_Parallel2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_PARALLEL == 0): return
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine2')
		if (index1 is None):
			logWarning('        ... skipped parallel constraint between lines - line 1 (%04X) has no index!' %(constraintNode.get('refLine1').index))
		elif (index2 is  None):
			logWarning('        ... skipped parallel constraint between lines - line 2 (%04X) has no index!' %(constraintNode.get('refLine2').index))
		else:
			key = 'Parallel_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Parallel', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added parallel constraint between lines %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch_Geometric_Perpendicular2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idxMov: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_PERPENDICULAR == 0): return
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine2')

		if (index1 is None):
			logMessage('        ... skipped perpendicular constraint between lines - line 1 (%04X) has no index!' %(constraintNode.get('refLine1').index))
		elif (index2 is  None):
			logMessage('        ... skipped perpendicular constraint between lines - line 2 (%04X) has no index!' %(constraintNode.get('refLine2').index))
		else:
			key = 'Perpendicular_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Perpendicular', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added perpendicular constraint between lines %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch_Geometric_Collinear2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_COLLINEAR == 0): return
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine2')
		if (index1 is None):
			logMessage('        ... skipped collinear constraint between lines - line 1 (%04X) has no index!' %(constraintNode.get('refLine1').index))
		elif (index2 is  None):
			logMessage('        ... skipped collinear constraint between lines - line 2 (%04X) has no index!' %(constraintNode.get('refLine2').index))
		else:
			key = 'Collinear_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Tangent', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added collinear constraint between Line %s and Line %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch_Geometric_Tangential2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_TANGENTIAL == 0): return
		entity1Node = constraintNode.get('refEntity1')
		entity2Node = constraintNode.get('refEntity2')
		entity1Name = entity1Node.typeName[0:-2]
		entity2Name = entity2Node.typeName[0:-2]
		index1 = self.checkSketchIndex(sketchObj, entity1Node)
		index2 = self.checkSketchIndex(sketchObj, entity2Node)
		if (index1 is None):
			logWarning('        ... skipped tangential constraint between %s and %s - entity 1 (%04X) has no index!' %(entity1Name, entity2Name, entity1Node.index))
		elif (index2 is None):
			logWarning('        ... skipped tangential constraint between %s and %s - entity 2 (%04X) has no index!' %(entity1Name, entity2Name, entity2Node.index))
		else:
			key = 'Tangent_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Tangent', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added tangential constraint between %s %s and %s %s' %(entity1Name, index1, entity2Name, index2), LOG.LOG_INFO)
		return

	def addSketch_Geometric_Vertical2D(self, constraintNode, sketchObj):
		'''
		index: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_VERTICAL == 0): return
		index = self.getGeometryIndex(sketchObj, constraintNode, 'refLine')
		if (index is not None):
			key = 'Vertical_%s' %(index)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Vertical', index)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added vertical constraint to line %s' %(index), LOG.LOG_INFO)
		return

	def addSketch_Geometric_Horizontal2D(self, constraintNode, sketchObj):
		'''
		index: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_HORIZONTAL == 0): return
		index = self.getGeometryIndex(sketchObj, constraintNode, 'refLine')
		if (index is not None):
			key = 'Horizontal_%s' %(index)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Horizontal', index)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added horizontal constraint to line %s' %(index), LOG.LOG_INFO)
		return

	def addSketch_Geometric_EqualLength2D(self, constraintNode, sketchObj):
		'''
		Create a  equal legnth constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_EQUAL_LENGTH == 0): return
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine2')
		if (index1 is None):
			logWarning('        ... skipped equal length constraint between lines - line 1 (%04X) has no index!' %(constraintNode.get('refLine1').index))
		elif (index2 is None):
			logWarning('        ... skipped equal length constraint between lines - line 2 (%04X) has no index!' %(constraintNode.get('refLine2').index))
		else:
			key = 'Equal_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Equal', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added equal length constraint between line %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch_Geometric_EqualRadius2D(self, constraintNode, sketchObj):
		'''
		Create a  equal radius constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_EQUAL_RADIUS == 0): return
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refCircle1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refCircle2')
		if (index1 is None):
			logWarning('        ... skipped equal radius constraint between circles - circle 1 (%04X) has no index!' %(constraintNode.get('refCircle1').index))
		elif (index2 is None):
			logWarning('        ... skipped equal radius constraint between circles - circle 2 (%04X) has no index!' %(constraintNode.get('refCircle2').index))
		else:
			key = 'Equal_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Equal', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added equal radius constraint between circle %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch_Point2D(self, pointNode, sketchObj):
		x = pointNode.get('x')
		y = pointNode.get('y')
		if ((x == 0) and (y == 0)):
			pointNode.setSketchEntity(-1, sketchObj.getPoint(-1, 1))
		else:
			pointNode.setSketchEntity(-2, None)
		return

	def addSketch_BlockPoint2D(self, node, sketchObj):
		point = node.get('refPoint')
		self.addSketch_Point2D(point, sketchObj)
		node.setSketchEntity(point.sketchIndex, point.sketchEntity)
		return

	def addSketch_Point3D(self, pointNode, edges): return

	def removeFromPointRef(self, point, index):
		key = calcPointKey(point)
		entities = self.pointDataDict[key]
		j = 1
		while (j < len(entities)):
			entity = entities[j]
			if (entity.index == index):
				del entities[j]
			else:
				j += 1
		return

	def invalidateLine2D(self, lineNode):
		lineNode.valid = False
		index = lineNode.index
		points = lineNode.get('points')
		self.removeFromPointRef(points[0], lineNode.index)
		self.removeFromPointRef(points[1], lineNode.index)

	def createLine2D(self, sketchObj, point1, point2, mode, line):
		if (point1):
			x1 = getX(point1)
			y1 = getY(point1)
		else:
			x1 = getX(line)
			y1 = getY(line)
		x2 = getX(point2)
		y2 = getY(point2)
		if(('%g'%x1 != '%g'%x2) or ('%g'%y1 != '%g'%y2)):
			part = Part.Line(createVector(x1, y1, 0), createVector(x2, y2, 0))
			addSketch2D(sketchObj, part, mode, line)
			return True
		return False

	def createLine3D(self, edges, line):
		points = line.get('points')
		if (len(points) > 1):
			point1 = points[0]
			point2 = points[1]
			x1 = getX(point1)
			y1 = getY(point1)
			z1 = getY(point1)
			x2 = getX(point2)
			y2 = getY(point2)
			z2 = getY(point2)
		else:
			x1 = getCoord(line, 'x')
			y1 = getCoord(line, 'y')
			z1 = getCoord(line, 'z')
			x2 = getCoord(line, 'dirX') + x1
			y2 = getCoord(line, 'dirY') + y1
			z2 = getCoord(line, 'dirZ') + z1
		if(('%g'%x1 != '%g'%x2) or ('%g'%y1 != '%g'%y2) or ('%g'%z1 != '%g'%z2)):
			part = Part.Line(createVector(x1, y1, z1), createVector(x2, y2, z1))
			addSketch3D(edges, part, isConstructionMode(line), line)
			return True
		return False

	def createRevolve(self, name, alpha, beta, source, axis, base, solid):
		revolution = newObject(self.doc, 'Part::Revolution', name)
		revolution.Angle = alpha + beta
		revolution.Source = source
		revolution.Axis = axis
		revolution.Base = base
		revolution.Solid = solid
		revolution.Placement.Rotation = FreeCAD.Rotation(axis, -beta)
		setDefaultViewObject(revolution)
		source.ViewObject.Visibility = False
		return revolution

	def addSketch_Line2D(self, lineNode, sketchObj):
		points = lineNode.get('points')
		mode = isConstructionMode(lineNode)
		if (self.createLine2D(sketchObj, points[0], points[1], mode, lineNode) == False):
			logWarning('        ... can\'t add line with length = 0.0!')
			self.invalidateLine2D(lineNode)
		else:
			x1 = getX(lineNode)
			y1 = getY(lineNode)
			x2 = getX(points[1])
			y2 = getY(points[1])
			logMessage('        ... added line (%g|%g)-(%g|%g) %r = %s' %(x1, y1, x2, y2, mode, lineNode.sketchIndex), LOG.LOG_INFO)
		return

	def addSketch_Line3D(self, lineNode, edges):
		points = lineNode.get('points')
		if (len(points) > 1):
			if (self.createLine3D(edges, lineNode) == False):
				logWarning('        ... can\'t add line with length = 0.0!')
			else:
				x1 = getX(points[0])
				y1 = getY(points[0])
				z1 = getZ(points[0])
				x2 = getX(points[1])
				y2 = getY(points[1])
				z2 = getZ(points[1])
				logMessage('        ... added line (%g|%g|%g)-(%g|%g|%g) %r' %(x1, y1, z1, x2, y2, z2, isConstructionMode(lineNode)), LOG.LOG_INFO)
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
		if (len(points)>2):
			self.createLine2D(sketchObj, points[0], points[2], mode, splineNode)
			i = 2
			while (i < len(points) - 1):
				self.createLine2D(sketchObj, points[i], points[i+1], mode, splineNode)
				i += 1
			self.createLine2D(sketchObj, points[len(points) - 1], points[1], mode, splineNode)
		else:
			self.createLine2D(sketchObj, points[0], points[1], mode, splineNode)
			logMessage('        ... added spline = %s' %(splineNode.sketchIndex), LOG.LOG_INFO)

		return

	def addSketch_Arc2D(self, arcNode, sketchObj):
		center = arcNode.get('refCenter')
		x = getX(center)
		y = getY(center)
		r = getCoord(arcNode, 'r')
		points = getCirclePoints(arcNode)
		mode = isConstructionMode(arcNode)

		part = Part.Circle(createVector(x, y, 0), createVector(0, 0, 1), r)

		# There shell be 3 points to draw a 2D arc.
		point0 = points[0] # Start-Point
		point1 = points[1] # End-Point
		# the 3rd point defines the a point on the circle between start and end! -> scip, as it is a redundant information to calculate the radius!
		a = calcAngle2D(center, point0)
		b = calcAngle2D(center, point1)
		radA = a.getRAD()
		radB = b.getRAD()
		arc = Part.ArcOfCircle(part, radA, radB)
		logMessage('        ... added Arc-Circle M=(%g/%g) R=%gmm, from %s to %s ...' %(x, y, r, degrees(radA), degrees(radB)), LOG.LOG_INFO)
		addSketch2D(sketchObj, arc, mode, arcNode)
		point0.sketchPos = 1
		point1.sketchPos = 2
		point0.sketchIndex = arcNode.sketchIndex
		point1.sketchIndex = point0.sketchIndex
		return

	def addSketch_Circle2D(self, circleNode, sketchObj):
		center = circleNode.get('refCenter')
		x = getX(center)
		y = getY(center)
		r = getCoord(circleNode, 'r')
		points = getCirclePoints(circleNode)
		mode = (circleNode.next.typeName == '64DE16F3') or isConstructionMode(circleNode)

		part = Part.Circle(createVector(x, y, 0), createVector(0, 0, 1), r)

		# There has to be at least 2 points to draw an arc.
		# Everything else will be handled as a circle!
		if (len(points) < 2):
			addSketch2D(sketchObj, part, mode, circleNode)
			logMessage('        ... added Circle M=(%g/%g) R=%g...' %(x, y, r), LOG.LOG_INFO)
		else:
			j = 1
			draw = True
			arc1 = None
			while (j < len(points)):
				point1 = points[j - 1]
				point2 = points[j]
				if (draw):
					a = calcAngle2D(center, point1)
					b = calcAngle2D(center, point2)
					radA = a.getRAD()
					radB = b.getRAD()
					arc = Part.ArcOfCircle(part, radA, radB)
					logMessage('        ... added Arc-Circle M=(%g/%g) R=%gmm, from %s to %s ...' %(x, y, r, degrees(radA), degrees(radB)), LOG.LOG_INFO)
					addSketch2D(sketchObj, arc, mode, circleNode)
					point1.sketchPos = 1
					point2.sketchPos = 2
					point1.sketchIndex = circleNode.sketchIndex
					point2.sketchIndex = point1.sketchIndex
					arc2 = circleNode.sketchIndex
					addEqualRadius2d(sketchObj, arc1, arc2)
					arc1 = arc2
				if (self.getCirclePointRefs(sketchObj, point2, circleNode.index) > 0):
					draw = not draw
				j += 1
		return

	def addSketch_Circle3D(self, circleNode, edges):
		x      = getCoord(circleNode, 'x')
		y      = getCoord(circleNode, 'y')
		z      = getCoord(circleNode, 'z')
		r      = getCoord(circleNode, 'r')
		normal = circleNode.get('normal')
		points = circleNode.get('points')

		part = Part.Circle(createVector(x, y, z), createVector(normal[0], normal[1], normal[2]), r)

		# There has to be at least 2 points to draw an arc.
		# Everything else will be handled as a circle!
		if (len(points) < 2):
			addSketch3D(edges, part, isConstructionMode(circleNode), circleNode)
			logMessage('        ... added Circle M=(%g/%g/%g) R=%g...' %(x, y, z, r), LOG.LOG_INFO)
		if (len(points) == 2):
			angleStart = Angle(circleNode.get('startAngle'), pi/180.0, u'\xb0')
			angleSweep = Angle(circleNode.get('sweepAngle'), pi/180.0, u'\xb0')
			radA = angleStart.getRAD()
			radB = angleSweep.getRAD()
			arc = Part.ArcOfCircle(part, radA, radB)
			logMessage('        ... added Arc-Circle M=(%g/%g/%g) R=%gmm, from %s to %s ...' %(x, y, z, r, angleStart, angleSweep), LOG.LOG_INFO)
			addSketch3D(edges, arc, isConstructionMode(circleNode), circleNode)
		else:
			logMessage('        ... can\'t Arc-Circle more than 2 points - SKIPPED!' %(x, y, r, angleStart, angleSweep), LOG.LOG_INFO)
		return

	def addSketch_Ellipse2D(self, ellipseNode, sketchObj):
		center = ellipseNode.get('refCenter')
		if (center.typeName == 'Circle2D'):
			#add concentric constraint
			center = center.get('refCenter')

		c_x = getX(center)
		c_y = getY(center)
		d = ellipseNode.get('dA')

		x = getCoord(ellipseNode, 'a')
		a_x = c_x + (x * d[0])
		a_y = c_y + (x * d[1])

		x = getCoord(ellipseNode, 'b')
		b_x = c_x - (x * d[1])
		b_y = c_y + (x * d[0])

		vecA = createVector(a_x, a_y, 0.0)
		vecB = createVector(b_x, b_y, 0.0)
		vecC = createVector(c_x, c_y, 0.0)

		try:
			part = Part.Ellipse(vecA, vecB, vecC)
		except:
			part = Part.Ellipse(vecB, vecA, vecC)

		a = ellipseNode.get('alpha')
		b = ellipseNode.get('beta')
		if ((a is None) and (b is None)):
			logMessage('        ... added 2D-Ellipse  c=(%g/%g) a=(%g/%g) b=(%g/%g) ...' %(c_x, c_y, a_x, a_y, b_x, b_y), LOG.LOG_INFO)
		else:
			a = Angle(a, pi/180.0, u'\xb0')
			b = Angle(b, pi/180.0, u'\xb0')
			logMessage('        ... added 2D-Arc-Ellipse  c=(%g/%g) a=(%g/%g) b=(%g/%g) from %s to %s ...' %(c_x, c_y, a_x, a_y, b_x, b_y, a, b), LOG.LOG_INFO)
			part = Part.ArcOfEllipse(part, a.getGRAD(), b.getGRAD())
		addSketch2D(sketchObj, part, isConstructionMode(ellipseNode), ellipseNode)
		return

	def addSketch_Ellipse3D(self, ellipseNode, edges):
		a_x = getCoord(ellipseNode, 'a_x')
		a_y = getCoord(ellipseNode, 'a_y')
		a_z = getCoord(ellipseNode, 'a_z')
		vecA = createVector(a_x, a_y, a_z)
		b_x = getCoord(ellipseNode, 'b_x')
		b_y = getCoord(ellipseNode, 'b_y')
		b_z = getCoord(ellipseNode, 'b_z')
		vecB = createVector(b_x, b_y, b_z)
		c_x = getCoord(ellipseNode, 'c_x')
		c_y = getCoord(ellipseNode, 'c_y')
		c_z = getCoord(ellipseNode, 'c_z')
		vecC = createVector(c_x, c_y, c_z)
		part = Part.Ellipse(vecA, vecB, vecC)

		a = ellipseNode.get('startAngle')
		b = ellipseNode.get('sweepAngle')
		if ((a is None) and (b is None)):
			logMessage('        ... added 3D-Ellipse  c=(%g/%g/%g) a=(%g/%g/%g) b=(%g/%g/%g) ...' %(c_x, c_y, c_z, a_x, a_y, a_z, b_x, b_y, b_z), LOG.LOG_INFO)
		else:
			a = Angle(a, pi/180.0, u'\xb0')
			b = Angle(b, pi/180.0, u'\xb0')
			logMessage('        ... added 3D-Arc-Ellipse  c=(%g/%g/%g) a=(%g/%g/%g) b=(%g/%g/%g) from %s to %s ...' %(c_x, c_y, c_z, a_x, a_y, a_z, b_x, b_y, b_z, a, b), LOG.LOG_INFO)
			arc = Part.ArcOfEllipse(part, a.getGRAD(), b.getGRAD())
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
		if (SKIP_CONSTRAINS & SKIP_GEO_OFFSET == 0): return
		return
	def addSketch_Geometric_AlignHorizontal2D(self, node, sketchObj):
		'''
		Create an horizontal align constraint.
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_ALIGN_HORIZONTAL == 0): return
		return
	def addSketch_Geometric_AlignVertical2D(self, node, sketchObj):
		'''
		Create an vertical align constraint.
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_ALIGN_VERTICAL == 0): return
		return
	def addSketch_Transformation(self, transformationNode, sketchObj):   return ignoreBranch(transformationNode)
	def addSketch_String(self, stringNode, sketchObj):                   return ignoreBranch(stringNode)

	def addSketch_Dimension_Distance_Horizontal2D(self, dimensionNode, sketchObj):
		'''
		Create a horizontal dimension constraint
		'''
		self.addDistanceConstraint(sketchObj, dimensionNode, SKIP_DIM_DISTANCE_X, 'DistanceX', 'horizontal')
		return

	def addSketch_Dimension_Distance_Vertical2D(self, dimensionNode, sketchObj):
		'''
		Create a vertical dimension constraint
		'''
		self.addDistanceConstraint(sketchObj, dimensionNode, SKIP_DIM_DISTANCE_Y, 'DistanceY', 'vertical')
		return

	def addSketch_Dimension_Distance2D(self, dimensionNode, sketchObj):
		'''
		Create a distance constraint
		'''
		self.addDistanceConstraint(sketchObj, dimensionNode, SKIP_DIM_DISTANCE, 'Distance', '')
		return

	def addSketch_Dimension_Radius2D(self, dimensionNode, sketchObj):
		'''
		Create a radius constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_DIM_RADIUS == 0): return
		circle    = dimensionNode.get('refCircle')
		index     = self.checkSketchIndex(sketchObj, circle)
		dimension = getDimension(dimensionNode, 'refParameter')
		if (index is not None):
			key = 'Radius_%s' %(index)
			if (not key in self.mapConstraints):
				radius = circle.sketchEntity.Radius
				constraint = Sketcher.Constraint('Radius',  index, radius)
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added radius \'%s\' = %s' %(constraint.Name, dimension.getValue()), LOG.LOG_INFO)
		return

	def addSketch_Dimension_RadiusA2D(self, dimensionNode, sketchObj):
		if (SKIP_CONSTRAINS & SKIP_DIM_RADIUS == 0): return
		dimension = getDimension(dimensionNode, 'refParameter')
		circle    = dimensionNode.get('refEllipse')
		index     = self.checkSketchIndex(sketchObj, circle)
		if (index is not None):
			pass

		return

	def addSketch_Dimension_RadiusB2D(self, dimensionNode, sketchObj):
		if (SKIP_CONSTRAINS & SKIP_DIM_RADIUS == 0): return
		dimension = getDimension(dimensionNode, 'refParameter')
		circle    = dimensionNode.get('refEllipse')
		index     = self.checkSketchIndex(sketchObj, circle)
		if (index is not None):
			pass

		return

	def addSketch_Dimension_Diameter2D(self, dimensionNode, sketchObj):
		'''
		Create a diameter (not available in FreeCAD) constraint
		Workaround: Radius and Center constraint.
		'''
		if (SKIP_CONSTRAINS & SKIP_DIM_DIAMETER == 0): return
		circle = dimensionNode.get('refCircle')
		index  = self.checkSketchIndex(sketchObj, circle)
		if (index is not None):
			key = 'Diameter_%s' %(index)
			if (not key in self.mapConstraints):
				#TODO: add a 2D-construction-line, pin both ends to the circle, pin circle's center on this 2D-line and add dimension constraint to 2D-construction-line
				radius = circle.sketchEntity.Radius
				constraint = Sketcher.Constraint('Radius',  index, radius)
				dimension = getDimension(dimensionNode, 'refParameter')
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key, False)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added diameter \'%s\' = %s (r = %s mm)' %(constraint.Name, dimension.getValue(), radius), LOG.LOG_INFO)
		return

	def addSketch_Dimension_Angle3Point2D(self, dimensionNode, sketchObj):
		'''
		Create an angle constraint between the three points.
		'''
		if (SKIP_CONSTRAINS & SKIP_DIM_ANGLE_3_POINT == 0): return
		pt1Ref = dimensionNode.get('refPoint1')
		pt2Ref = dimensionNode.get('refPoint2') # the center point
		pt3Ref = dimensionNode.get('refPoint3')
		return

	def addSketch_Dimension_Angle2Line2D(self,  dimensionNode, sketchObj):
		'''
		Create a angle constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_DIM_ANGLE_2_LINE == 0): return
		line1 = dimensionNode.get('refLine1')
		line2 = dimensionNode.get('refLine2')
		index1 = self.checkSketchIndex(sketchObj, line1)
		index2 = self.checkSketchIndex(sketchObj, line2)

		if (index1 is None):
			logWarning('        ... skipped dimension angle \'%s\' = %s - line 1 (%04X) has no index!' %(constraint.Name, dimension.getValue(), line1.index))
		elif (index2 is None):
			logWarning('        ... skipped dimension angle \'%s\' = %s - line 2 (%04X) has no index!' %(constraint.Name, dimension.getValue(), line2.index))
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
				dimension  = getDimension(dimensionNode, 'refParameter')
				angle      = dimension.getValue()
				constraint = Sketcher.Constraint('Angle', index1, pos1, index2, pos2, angle.getRAD())
				index      = self.addDimensionConstraint(sketchObj, dimension, constraint)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added dimension angle \'%s\' = %s' %(constraint.Name, dimension.getValue()), LOG.LOG_INFO)
		return

	def addSketch_Dimension_OffsetSpline2D(self, dimensionNode, sketchObj):
		'''
		Create distnace contraint for an offset spline.
		'''
		if (SKIP_CONSTRAINS & SKIP_DIM_OFFSET_SPLINE == 0): return
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
	def addSketch_ControlPointSpline2D(self, splineNode, sketchObj):
		splineNode.setSketchEntity(-1, None)
		return
	def addSketch_Image2D(self, imageNode, sketchObj):
		imageNode.setSketchEntity(-1, None)
		return

	def addSketch_5D8C859D(self, node, sketchObj): return
	def addSketch_8EC6B314(self, node, sketchObj): return
	def addSketch_8FEC335F(self, node, sketchObj): return
	def addSketch_F2568DCF(self, node, sketchObj): return

	def handleAssociativeID(self, node, sketchObj):
		label  = node.get('label')
		sketch = node.get('refSketch')

		if (label is not None):
			if (label.typeName == '90874D15'):
				if (label.get('u32_1') == 2): # Only Edges generated by Lines, Arcs, .. but not Points!
					id = label.get('associativeID')
					if (sketch.name not in self.sketchEdges):
						self.sketchEdges[sketch.name] = {}
					edges = self.sketchEdges[sketch.name]
					if (node.sketchIndex > -1):
						if (sketchObj.Geometry[node.sketchIndex].Construction == False):
							edges[id] = sketchObj.Geometry[node.sketchIndex]

	def Create_Sketch2D_Node(self, sketchObj, node):
		if ((node.handled == False) and node.valid):
			node.handled = True
			name  = node.typeName
			index = node.index
			try:
				addSketchObj = getattr(self, 'addSketch_%s' %(name))
				addSketchObj(node, sketchObj)
				self.handleAssociativeID(node, sketchObj)

			except Exception as e:
				logError('ERROR: (%04X): %s - %s' %(index, name, e))
				logError('>E: ' + traceback.format_exc())
		return

	def addSketch_PostCreateCoincidences(self, sketchObj):
		for key in self.pointDataDict.keys():
			entities = self.pointDataDict[key]
			l = len(entities)
			j = 2
			if (l > j):
				point     = entities[0]
				fix       = entities[1]
				fixIndex  = self.checkSketchIndex(sketchObj, fix)
				fixPos    = findEntityVertex(fix, point)
				fixName   = fix.typeName
				fixIndex, fixPos = self.adjustIndexPos(fix, fixIndex, fixPos, point)

				while (j < l):
					movData  = entities[j]
					constraint = self.addCoincidentConstraint(fixIndex, fixPos, fixName, movData, sketchObj, point)
					if (constraint):
						self.addConstraint(sketchObj, constraint, key)
					j += 1
		return

	def Create_Sketch2D(self, sketchNode):
		transformation      = sketchNode.get('refTransformation')
		placement           = getPlacement(transformation)

		sketchObj           = self.CreateEntity(sketchNode, 'Sketcher::SketchObject')
		logMessage('    adding 2D-Sketch \'%s\' ...' %(sketchObj.Label), LOG.LOG_INFO)
		sketchObj.Placement = FreeCAD.Placement(placement)
		sketchNode.setSketchEntity(-1, sketchObj)


		# Clean up Points
		lst = sketchNode.get('entities')
		self.pointDataDict = {}
		for child in lst:
			if (child.typeName == 'Point2D'):
				self.addPoint2Dictionary(child)

		for child in lst:
			self.Create_Sketch2D_Node(sketchObj, child.node)

		self.addSketch_PostCreateCoincidences(sketchObj)

		if (self.root):
			self.root.addObject(sketchObj)

		self.pointDataDict = None

		return

	def Create_FxExtrude_New(self, padNode, sectionNode, name):
		properties = padNode.get('properties')
		boundary   = getProperty(properties, 0x01)               # The selected edges from a sketch
		direction  = getProperty(properties, 0x02)               # The direction of the extrusion
		reversed   = getPropertyValue(properties, 0x03, 'value') # If the extrusion direction is inverted
		dimLength  = getProperty(properties, 0x04)               # The length of the extrusion in direction 1
		dimAngle   = getProperty(properties, 0x05)               # The taper outward angle  (doesn't work properly in FreeCAD)
		midplane   = getPropertyValue(properties, 0x07, 'value')
		# The output is either solid (= True) or surface (=False)
		solid      = getProperty(properties, 0x1A)
		dimLength2 = getProperty(properties, 0x1B)               # The length of the extrusion in direction 2

		# Extents 1x distance, 2x distance, to, to next, between, all

		pad = None
		if (dimLength):
			sketchName = sectionNode.name
			sketch = self.createBoundary(boundary)
			len1 = dimLength.getValue()
			if (isinstance(len1, Length)):
				len1 = len1.getMM()
			else:
				len1 = len1 * 10.0
			if (midplane): len1 = len1 / 2.0
			taperAngle = dimAngle.getValue()

			pad = newObject(self.doc, 'Part::Extrusion', name)
			pad.Base = sketch
			pad.Solid = solid is not None
			pad.TaperAngle = taperAngle.getGRAD()

			setDefaultViewObject(pad)


			if (midplane):
				len2 = len1
				logMessage('        creating pad \'%s\' based on \'%s\' (symmetric len=%s) ...' %(name, sketchName, len1), LOG.LOG_INFO)
			elif (dimLength2 is not None):
				len2 = dimLength2.getValue()
				logMessage('        creating pad \'%s\' based on \'%s\' (rev=%s, len=%s, len2=%s) ...' %(name, sketchName, reversed, len1, len2), LOG.LOG_INFO)
				#if (direction.get('x') == 1.0): pad.setExpression('Dir.x', '(' + dimLength.get('alias') + '+' + dimLength.get('alias') + ') / 1mm')
				#if (direction.get('y') == 1.0): pad.setExpression('Dir.y', '(' + dimLength.get('alias') + '+' + dimLength.get('alias') + ') / 1mm')
				#if (direction.get('z') == 1.0): pad.setExpression('Dir.z', '(' + dimLength.get('alias') + '+' + dimLength.get('alias') + ') / 1mm')
			else:
				len2 = 0
				logMessage('        creating pad \'%s\' based on \'%s\' (rev=%s, len=%s) ...' %(name, sketchName, reversed, len1), LOG.LOG_INFO)

			x    = direction.get('x') * (len1 + len2)
			y    = direction.get('y') * (len1 + len2)
			z    = direction.get('z') * (len1 + len2)
			if (reversed):
				#if (dimLength2 is not None)
				#	if (direction.get('x') == 1.0): pad.setExpression('Dir.x', dimLength.get('alias') + ' / -1mm')
				#	if (direction.get('y') == 1.0): pad.setExpression('Dir.y', dimLength.get('alias') + ' / -1mm')
				#	if (direction.get('z') == 1.0): pad.setExpression('Dir.z', dimLength.get('alias') + ' / -1mm')
				#else:
				#	if (direction.get('x') == 1.0): pad.setExpression('Dir.x', '(' + dimLength.get('alias') + '+' + dimLength.get('alias') + ') / -1mm')
				#	if (direction.get('y') == 1.0): pad.setExpression('Dir.y', '(' + dimLength.get('alias') + '+' + dimLength.get('alias') + ') / -1mm')
				#	if (direction.get('z') == 1.0): pad.setExpression('Dir.z', '(' + dimLength.get('alias') + '+' + dimLength.get('alias') + ') / -1mm')
				pad.Dir = (-x, -y, -z)
			else:
				#if (dimLength2 is not None)
				#	if (direction.get('x') == 1.0): pad.setExpression('Dir.x', dimLength.get('alias') + ' / 1mm')
				#	if (direction.get('y') == 1.0): pad.setExpression('Dir.y', dimLength.get('alias') + ' / 1mm')
				#	if (direction.get('z') == 1.0): pad.setExpression('Dir.z', dimLength.get('alias') + ' / 1mm')
				#else:
				#	if (direction.get('x') == 1.0): pad.setExpression('Dir.x', '(' + dimLength.get('alias') + '+' + dimLength.get('alias') + ') / 1mm')
				#	if (direction.get('y') == 1.0): pad.setExpression('Dir.y', '(' + dimLength.get('alias') + '+' + dimLength.get('alias') + ') / 1mm')
				#	if (direction.get('z') == 1.0): pad.setExpression('Dir.z', '(' + dimLength.get('alias') + '+' + dimLength.get('alias') + ') / 1mm')
				pad.Dir = (x, y, z)
			pad.Placement.Base.x -= direction.get('x') * len2
			pad.Placement.Base.y -= direction.get('y') * len2
			pad.Placement.Base.z -= direction.get('z') * len2
			self.hide([sketch])
			self.addBody(padNode, pad, 0x11, 0x10)
		else:
			logWarning('        Failed create new extrusion \'%s\' - (%04X): %s properties[04] is None!' %(name, padNode.index, padNode.typeName))
		return pad

	def createFxExtrure_Operation(self, padNode, sectionNode, name, nameExtension, className):
		properties = padNode.get('properties')
		baseData   = getProperty(properties, 0x1A)
		boolean    = None

		if (baseData is None):
			logError('ERROR> (%04X): %s - can\'t find base info (not yet created)!' %(padNode.index, name))
		else:
			tool = self.Create_FxExtrude_New(padNode, sectionNode, name + nameExtension)
			base    = self.findBase(baseData.next)
			if (base is not None):
				if (tool is not None): # no need to raise a warning as it's already done!
					boolean = self.createBoolean(className, name, base, [tool])
				else:
					logWarning('        FxExtrude \'%s\': can\'t find/create tools object - executing %s!' %(name, className))
			else:
				logWarning('        FxExtrude \'%s\': can\'t find/create base object - executing %s!' %(name, className))
		return boolean

	def Create_FxRevolve(self, revolveNode):
		participants = revolveNode.getParticipants()
		revolution = None

		if (participants):
			properties = revolveNode.get('properties')
			pathName   = participants[0].name
			operation  = getProperty(properties, 0x00) # PartFeatureOperation
			boundary   = getProperty(properties, 0x01) # FxBoundaryPatch
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

			path          = self.createBoundary(boundary)

			x1         = getCoord(lineAxis, 'x')
			y1         = getCoord(lineAxis, 'y')
			z1         = getCoord(lineAxis, 'z')
			dx         = getCoord(lineAxis, 'dirX')
			dy         = getCoord(lineAxis, 'dirY')
			dz         = getCoord(lineAxis, 'dirZ')
			lAxis      = sqrt(dx*dx + dy*dy + dz*dz)
			axis       = createVector(dx/lAxis, dy/lAxis, dz/lAxis)
			base       = createVector(x1, y1, z1)
			solid      = (isSurface.get('value') == False)

			if (extend1.get('value') == 1): # 'Direction' => AngleExtent
				alpha = angle1.getValue().getGRAD()
				if (angle2 is None):
					if (direction.get('value') == 0): # positive
						logMessage('    ... based on \'%s\' (alpha=%s) ...' %(pathName, angle1.getValue()), LOG.LOG_INFO)
						revolution = self.createRevolve(revolveNode.name, alpha, 0, path, axis, base, solid)
					elif (direction.get('value') == 1): # negative
						logMessage('    ... based on \'%s\' (alpha=%s, inverted) ...' %(pathName, angle1.getValue()), LOG.LOG_INFO)
						revolution = self.createRevolve(revolveNode.name, 0, alpha, path, axis, base, solid)
					elif (direction.get('value') == 2): # symmetric
						logMessage('    ... based on \'%s\' (alpha=%s, symmetric) ...' %(pathName, angle1.getValue()), LOG.LOG_INFO)
						revolution = self.createRevolve(revolveNode.name, alpha / 2.0, alpha / 2.0, path, axis, base, solid)
				else:
					logMessage('    ... based on \'%s\' (alpha=%s, beta=%s) ...' %(pathName, angle1.getValue(), angle2.getValue()), LOG.LOG_INFO)
					beta = angle2.getValue().getGRAD()
					revolution = self.createRevolve(revolveNode.name, alpha, beta, path, axis, base, solid)
			elif (extend1.get('value') == 3): # 'Path' => FullSweepExtend
				logMessage('    ... based on \'%s\' (full) ...' %(pathName), LOG.LOG_INFO)
				revolution = self.createRevolve(revolveNode.name, 360.0, path, axis, base, solid)

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
				properties = extrudeNode.get('properties')
				operation = getPropertyValue(properties, 0x00, 'value')
				if (operation == FreeCADImporter.FX_EXTRUDE_NEW):
					padGeo = self.Create_FxExtrude_New(extrudeNode, sectionNode, name)
				elif (operation == FreeCADImporter.FX_EXTRUDE_CUT):
					padGeo = self.createFxExtrure_Operation(extrudeNode, sectionNode, name, '_Cut', 'Cut')
				elif (operation == FreeCADImporter.FX_EXTRUDE_JOIN):
					padGeo = self.createFxExtrure_Operation(extrudeNode, sectionNode, name, '_Join', 'MultiFuse')
				elif (operation == FreeCADImporter.FX_EXTRUDE_INTERSECTION):
					padGeo = self.createFxExtrure_Operation(extrudeNode, sectionNode, name, '_Intersection', 'MultiCommon')
				elif (operation == FreeCADImporter.FX_EXTRUDE_SURFACE):
					padGeo = self.Create_FxExtrude_New(extrudeNode, sectionNode, name)
				else:
					padGeo = None
					logError('    ERROR Don\'t know how to operate PAD=%s for (%04X): %s ' %(operation, extrudeNode.index, extrudeNode.typeName))

				if (padGeo):
					self.addBody(extrudeNode, padGeo, 0x1A, 0x10)
					if (self.root):
						self.root.addObject(padGeo)

	def Create_FxPatternCircular(self, patternNode):
		name         = patternNode.name
		properties   = patternNode.get('properties')
		participants = patternNode.get('participants')
		fxDimData    = getProperty(properties, 0x05)
		solidRef     = getProperty(properties, 0x09)
		countRef     = getProperty(properties, 0x0C)
		angleRef     = getProperty(properties, 0x0D)
		axisData     = getProperty(properties, 0x0E)
		patternGeo   = None
		if (len(participants) > 0):
			geos  = []
			count = getNominalValue(countRef)
			fxDimensions = fxDimData.get('lst0')
			if ((fxDimensions is None) or len(fxDimensions) < 1):
				logError('        FxPatternCircular \'%s\' - (%04X): %s has no attribute lst0!' %(name, fxDimData.index, fxDimData.typeName))
			else:
				anchor = fxDimensions[0].get('anchors')[0]
				angle = Angle(getNominalValue(angleRef), pi/180.0, u'\xb0')
				center  = createVector(anchor[0] * 10.0, anchor[1] * 10.0, anchor[2] * 10.0)
				axis  = createVector(getX(axisData), getY(axisData), getZ(axisData))
				logMessage('    adding FxPatternPolar \'%s\' (count=%d, angle=%s) ...' %(name, count, angle), LOG.LOG_INFO)
				if(len(participants) > 1):
					namePart = name + '_0'
				else:
					namePart = name
				for baseRef in participants:
					baseGeo = baseRef.sketchEntity
					if (baseGeo is None):
						baseGeo = self.findBase2(baseRef)
					else:
						logMessage('        .... Base = \'%s\'' %(baseRef.name), LOG.LOG_INFO)
					if (baseGeo is not None):
						patternGeo = Draft.makeArray(baseGeo, center, angle.getGRAD(), count, None, namePart)
						patternGeo.Axis = axis
						setDefaultViewObject(patternGeo)
						geos.append(patternGeo)
					namePart = '%s_%d' % (name, len(geos))
				if (len(geos) > 1):
					patternGeo = self.CreateEntity(patternNode, 'Part::MultiFuse')
					patternGeo.Shapes = geos
				if (patternGeo is not None):
					self.addSolidBody(patternNode, patternGeo, solidRef)
		return

	def Create_FxPatternRectangular(self, patternNode):
		name         = patternNode.name
		properties   = patternNode.get('properties')
		participants = patternNode.get('participants')
		offset = 0
		if (getFileVersion() > 2016):
			offset = 6
		solidRef    = getProperty(properties, 0x09 + offset)
		count1Ref   = getProperty(properties, 0x0C + offset)
		count2Ref   = getProperty(properties, 0x0D + offset)
		distanc1Ref = getProperty(properties, 0x0E + offset)
		distanc2Ref = getProperty(properties, 0x0F + offset)
		dir1Ref     = getProperty(properties, 0x10 + offset)
		dir2Ref     = getProperty(properties, 0x11 + offset)
		count2      = None
		dir2        = None
		patternGeo  = None
		if (len(participants) > 0):
			geos  = []
			count1 = getNominalValue(count1Ref)
			if (distanc1Ref is None):
				#dir1, distance1 = getDistanceAndDir(dir1Ref)
				logWarning('    FxPatternRectangular \'%s\': Can\'t create array along a spline in 1st direction!' %(name))
				return
			else:
				distance1 = getNominalValue(distanc1Ref)
				if (count1 > 1):
					distance1 = distance1 / (count1 - 1)
				if (dir1Ref.typeName == 'A5977BAA'):
					dir1Ref = dir1Ref.get('refEntity')
				x1 = getX(dir1Ref)
				y1 = getY(dir1Ref)
				z1 = getZ(dir1Ref)
				dir1   = createVector(x1 * distance1, y1 * distance1, z1 * distance1)
			if ((dir2Ref is not None) and (count2Ref is not None)):
				count2 = getNominalValue(count2Ref)
				if (distanc2Ref is None):
					dir2, distance2 = getDistanceAndDir(dir2Ref)
					logWarning('    FxPatternRectangular \'%s\': Can\'t create array along a spline 2nd direction!' %(name))
					return
				else:
					distance2 = getNominalValue(distanc2Ref)
					if (count2 > 1):
						distance2 = distance2 / (count2 - 1)
					if (dir2Ref.typeName == 'A5977BAA'):
						dir2Ref = dir2Ref.get('refEntity')
					x2 = getX(dir2Ref)
					y2 = getY(dir2Ref)
					z2 = getZ(dir2Ref)
					dir2   = createVector(x2 * distance2, y2 * distance2, z2 * distance2)
			if (count2 is None):
				logMessage('    adding FxPatternRectangular \'%s\' (count=%d, dir=(%g/%g/%g)) ...' %(name, count1, dir1.x, dir1.y, dir1.z), LOG.LOG_INFO)
			else:
				logMessage('    adding FxPatternRectangular \'%s\' (count1=%d, dir1=(%g/%g/%g) and count2=%d, dir2=(%g/%g/%g)) ...' %(name, count1, dir1.x, dir1.y, dir1.z, count2, dir2.x, dir2.y, dir2.z), LOG.LOG_INFO)
			if (len(participants) > 1):
				namePart = name + '_0'
			else:
				namePart = name
			for baseRef in participants:
				baseGeo = baseRef.sketchEntity
				if (baseGeo is None):
					baseGeo = self.findBase2(baseRef)
				else:
					logMessage('        .... Base = \'%s\'' %(baseRef.name), LOG.LOG_INFO)
				if (baseGeo is not None):
					patternGeo = Draft.makeArray(baseGeo, dir1, dir2, count1, count2, namePart)
					setDefaultViewObject(patternGeo)
					geos.append(patternGeo)
				namePart = '%s_%d' % (name, len(geos))
			if (len(geos) > 1):
				patternGeo = self.CreateEntity(patternNode, 'Part::MultiFuse')
				patternGeo.Shapes = geos
			if (patternGeo is not None):
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
			logWarning('        FxCombine: don\'t know how to \'%s\' - (%04X): %s!' %(operationData.node.getValueText(), combineNode.index, combineNode.typeName))
			return
		logMessage('    adding FxCombin \'%s\': %s ...' %(name, className), LOG.LOG_INFO)
		baseGeo       = self.findBase2(bodyRef)
		toolGeos      = self.findGeometries(sourceData.next)
		if ((baseGeo is not None) and (len(toolGeos) > 0)):
			cmbineGeo = self.createBoolean(className, name, baseGeo, toolGeos)
			if (cmbineGeo is None):
				logError('        ....Failed to create combination!')
			else:
				self.addSolidBody(combineNode, cmbineGeo, bodyRef)
		return

	def Create_FxMirror(self, mirrorNode):
		name          = mirrorNode.name
		participants  = mirrorNode.get('participants')
		properties    = mirrorNode.get('properties')
		planeRef      = getProperty(properties, 0x0C)
		b_x = getCoord(planeRef, 'b_x')
		b_y = getCoord(planeRef, 'b_y')
		b_z = getCoord(planeRef, 'b_z')
		n_x = getCoord(planeRef, 'n_x')
		n_y = getCoord(planeRef, 'n_y')
		n_z = getCoord(planeRef, 'n_z')
		logMessage('    adding FxMirror \'%s\' ...' %(name), LOG.LOG_INFO)

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
				mirrorGeo.Base   = (b_x, b_y, b_z)
				mirrorGeo.Normal = (n_x, n_y, n_z)
				adjustViewObject(mirrorGeo, baseGeo)
				mirrors.append(mirrorGeo)
			nameGeo = '%s_%d' %(name, len(mirrors))
		if (len(mirrors) > 1):
			mirrorGeo = self.createBoolean('MultiCommon', name, mirrors[0], mirrors[1:])
			if (mirrorGeo is None):
				logError('        ....Failed to create combination!')
		if (mirrorGeo):
			self.addSolidBody(mirrorNode, mirrorGeo, getProperty(properties, 0x09))

		return

	def Create_FxHole(self, holeNode):
		name          = holeNode.name
		defRef        = holeNode.get('label')
		properties    = holeNode.get('properties')
		holeType      = getProperty(properties, 0x00)
		holeDiam_1    = getProperty(properties, 0x01)
		holeDepth_1   = getProperty(properties, 0x02)
		holeDiam_2    = getProperty(properties, 0x03)
		holeDepth_2   = getProperty(properties, 0x04)
		holeAngle_2   = getProperty(properties, 0x05)
		pointAngle    = getProperty(properties, 0x06)
		#    = getProperty(properties, 0x07)	# <=> placement == "by Sketch"
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

		if (holeType is not None):
			base = self.findBase(baseData.next)

			if (base is None):
				logError('ERROR> (%04X): %s - can\'t find base info (not yet created)!' %(holeNode.index, name))
			else:
				placement = getPlacement(transformation)
				holeGeo   = None
				if (holeType.get('value') == FreeCADImporter.FX_HOLE_DRILLED):
					logMessage('    adding drilled FxHole \'%s\' ...' %(name), LOG.LOG_INFO)
					geos, h = self.createCylinder(name + '_l', holeDiam_1, holeDepth_1, pointAngle)
					if (len(geos) > 1):
						geo1 = self.createBoolean('MultiFuse', name + '_h', geos[0], geos[1:])
						geo1.Placement = FreeCAD.Placement(placement)
						holeGeo = self.createBoolean('Cut', name, base, [geo1])
					else:
						geos[0].Placement = FreeCAD.Placement(placement)
						holeGeo = self.createBoolean('Cut', name, base, geos[0:1])
					if (holeGeo is None):
						logError('        ... Failed to create hole!')
				else:
					geos, h1 = self.createCylinder(name + '_l', holeDiam_1, holeDepth_1, pointAngle)
					if (holeType.get('value') == FreeCADImporter.FX_HOLE_SINK):
						logMessage('    adding counter sink FxHole \'%s\' ...' %(name), LOG.LOG_INFO)
						geo2, h2 = self.createCone(name + '_2', holeDiam_2, holeAngle_2, holeDiam_1)
						holeGeo = self.createBoolean('MultiFuse', name + '_h', geo2, geos)
						holeGeo.Placement = FreeCAD.Placement(placement)
						holeGeo = self.createBoolean('Cut', name, base, [holeGeo])
						if (holeGeo is None):
							logError('        ... Failed to create counter sink hole!')
					elif (holeType.get('value') == FreeCADImporter.FX_HOLE_BORED):
						logMessage('    adding counter bored FxHole \'%s\' ...' %(name), LOG.LOG_INFO)
						geo2, h2 = self.createCylinder(name + '_2', holeDiam_2, holeDepth_2, None)
						holeGeo = self.createBoolean('MultiFuse', name + '_h', geo2[0], geos)
						holeGeo.Placement = FreeCAD.Placement(placement)
						holeGeo = self.createBoolean('Cut', name, base, [holeGeo])
						if (holeGeo is None):
							logError('        ... Failed to create counter bored hole!')
					elif (holeType.get('value') == FreeCADImporter.FX_HOLE_SPOT):
						logMessage('    adding spot face FxHole \'%s\' ...' %(name), LOG.LOG_INFO)
						geo2, h2 = self.createCylinder(name + '_2', holeDiam_2, holeDepth_2, None)
						holeGeo = self.createBoolean('MultiFuse', name + '_h', geo2[0], geos)
						holeGeo.Placement = FreeCAD.Placement(placement)
						holeGeo = self.createBoolean('Cut', name, base, [holeGeo])
						if (holeGeo is None):
							logError('        ... Failed to create spot face hole!')
					else:
						logError('ERROR> Unknown hole type %s!' %(holeType.get('value')))

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

		sections = self.collectSections(loftNode, 'loft', [])

		if (len(sections) > 0):
			if (loftType.get('value') == 1): # Centerline
				# this is a sweep between two surfaces!
				loftGeo            = self.CreateEntity(loftNode, 'Part::Sweep')
				loftGeo.Sections   = sections[0:1] + sections[2:]
				loftGeo.Spine      = (sections[1], ["Edge1"])
				loftGeo.Frenet     = False
				loftGeo.Transition = 'Transformed'
			else:
			#elif (loftType.get('value') == 0): # Rails
			#elif (loftType.get('value') == 2): # AreaLoft
			#elif (loftType.get('value') == 3): # RegularLoft
				loftGeo          = self.CreateEntity(loftNode, 'Part::Loft')
				loftGeo.Sections = sections[-1:] + sections[0:-2] + sections[-2:-1]
				loftGeo.Ruled    = ruled.get('value') != 0
				loftGeo.Closed   = closed.get('value') != 0
			loftGeo.Solid    = surface is None
			self.hide(sections)
			setDefaultViewObject(loftGeo)
			self.addBody(loftNode, loftGeo, 0x0D, 0x06)
		return

	def Create_FxSweep(self, sweepNode):
		properties    = sweepNode.get('properties')
		definitionRef = sweepNode.get('label')
		solid         = (definitionRef.typeName == 'Label')
		boundary      = getProperty(properties, 0x00)
		profile1      = getProperty(properties, 0x01) # ProfilePath
		fxOrientation = getProperty(properties, 0x02) # PartFeatureOperation=Cut
		taperAngle    = getProperty(properties, 0x03) # Parameter
		#= getProperty(properties, 0x04) # ExtentType
		#= getProperty(properties, 0x05) # ???
		#= getProperty(properties, 0x07) # FeatureDimensions
		#= getProperty(properties, 0x08) # SweepType=Path
		frenet        = getProperty(properties, 0x09) # SweepProfileOrientation, e.g. 'NormalToPath', other not yet supported by FreeCAD
		scaling       = getProperty(properties, 0x0A) # SweepProfileScaling, e.g. 'XY', other not yet supported by FreeCAD
		profile2      = getProperty(properties, 0x0B) # ProfilePath
		#= getProperty(properties, 0x0C): ???
		#= getProperty(properties, 0x0D): ???
		skip   = []

		path = self.getEntity(self.createBoundary(profile1))
		edges = getEdges(path)

		if (len(edges) > 0):
			sweepGeo          = self.CreateEntity(sweepNode, 'Part::Sweep')
			sweepGeo.Sections = [self.createBoundary(boundary)]
			sweepGeo.Spine    = (path, edges)
			sweepGeo.Solid    = solid
			#sweepGeo.Frenet   = (frenet.getValueText() == 'ParallelToOriginalProfile')
			self.hide(sections)
			setDefaultViewObject(sweepGeo)
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
		distance        = featureDim.get('lst0')[0].get('refParameter')
		verticalSurface = getProperty(properties, 0x0A) # boolean parameter
		aprxTol         = getProperty(properties, 0x0C) # approximation tolerance
		aprxType        = getProperty(properties, 0x0D) # approximation type
		#= getProperty(properties, 0x0E) # Enum_637B1CC1
		solid           = getProperty(properties, 0x0F) # solid
		blending        = getProperty(properties, 0x10) # boolean parameter
		#= getProperty(properties, 0x11) # boolean parameter
		#= getProperty(properties, 0x12) # ???

		sourceGeos = {}
		if (useInputSurface.get('value')):
			inputSurface    = getProperty(properties, 0x05) # SurfaceBody => "Quilt"
			source = self.findSurface(inputSurface)
			if (source):
				sourceGeos[source.Label] = source
		else:
			faceOffsets   = getProperty(properties, 0x00) # faceOffsets
			for faceOffset in faceOffsets.get('lst0'):
				if (faceOffset.typeName == 'FacesOffset'):
					face = faceOffset.get('refFaces').get('faces')[0]
					dim  = faceOffset.get('refThickness')
					surface = thickenNode.segment.indexNodes[face.get('indexRefs')[0]]
					surface = surface.get('refSurface')
				source = self.findSurface(surface)
				if (source):
					sourceGeos[source.Label] = source
		sourceGeos = sourceGeos.values()
		for source in sourceGeos:
			thickenGeo = self.CreateEntity(thickenNode, 'Part::Offset')
			thickenGeo.Source = source
			#thickenGeo = self.CreateEntity(thickenNode, 'Part::Thickness')
			#thickenGeo.Faces = source
			if (negativeDir.get('value')):
				thickenGeo.Value = getCoord(distance, 'valueNominal')
			else:
				#TODO: symmetricDir - create a fusion of two thicken geometries
				thickenGeo.Value = -getCoord(distance, 'valueNominal')
			thickenGeo.Mode = 'Skin'          # {Skin, Pipe, RectoVerso}
			thickenGeo.Join = 'Intersection'  # {Arc, Tangent, Intersection}
			thickenGeo.Intersection = False
			thickenGeo.SelfIntersection = False
			thickenGeo.Fill = solid is not None
			adjustViewObject(thickenGeo, source)
			if (verticalSurface.get('value') == True):
				self.addBody(thickenNode, thickenGeo, 0x0F, 0x08)
			else:
				self.addBody(thickenNode, thickenGeo, 0x0F, 0x0B)
		self.hide(sourceGeos)
		return

	def Create_FxBoss(self, bossNode):                           return notYetImplemented(bossNode) # MultiFuse Geometry
	def Create_FxBoundaryPatch(self, boundaryPatchNode):         return notYetImplemented(boundaryPatchNode) # Sketches, Edges
	def Create_FxChamfer(self, chamferNode):                     return notYetImplemented(chamferNode)
	def Create_FxCoil(self, coilNode):                           return notYetImplemented(coilNode)
	def Create_FxCoreCavity(self, coreCavityNode):               return notYetImplemented(coreCavityNode)
	def Create_FxCornerRound(self, cornerNode):                  return notYetImplemented(cornerNode)
	def Create_FxCut(self, cutNode):                             return notYetImplemented(cutNode)
	def Create_FxDecal(self, decalNode):                         return notYetImplemented(decalNode)
	def Create_FxDeleteFace(self, deleteFaceNode):               return notYetImplemented(deleteFaceNode)
	def Create_FxDirectEdit(self, directEditNode):               return notYetImplemented(directEditNode)
	def Create_FxEmboss(self, embossNode):                       return notYetImplemented(embossNode)
	def Create_FxExtend(self, extendNode):                       return notYetImplemented(extendNode)
	def Create_FxFaceDraft(self, faceDraftNode):                 return notYetImplemented(faceDraftNode)
	def Create_FxFaceOffset(self, faceOffsetNode):               return notYetImplemented(faceOffsetNode)
	def Create_FxFillet(self, filletNode):                       return notYetImplemented(filletNode)
	def Create_FxFilletConstant(self, filletNode):               return notYetImplemented(filletNode)
	def Create_FxFilletVariable(self, filletNode):               return notYetImplemented(filletNode)
	def Create_FxFilletRule(self, filletNode):                   return notYetImplemented(filletNode)
	def Create_FxFreeform(self, freeformNode):                   return notYetImplemented(freeformNode)
	def Create_FxGrill(self, grillNode):                         return notYetImplemented(grillNode)
	def Create_FxiFeature(self, iFeatureNode):                   return notYetImplemented(iFeatureNode)
	def Create_FxLip(self, lipNode):                             return notYetImplemented(lipNode)
	def Create_FxMesh(self, meshNode):                           return notYetImplemented(meshNode)
	def Create_FxMidSurface(self, midSurfaceNode):               return notYetImplemented(midSurfaceNode)
	def Create_FxMove(self, moveNode):                           return notYetImplemented(moveNode)
	def Create_FxMoveFace(self, moveFaceNode):                   return notYetImplemented(moveFaceNode)
	def Create_FxNonParametricBase(self, nonParametricBaseNode): return notYetImplemented(nonParametricBaseNode)
	def Create_FxPatternSketchDriven(self, patternNode):         return notYetImplemented(patternNode)
	def Create_FxPresentationMesh(self, presentationMeshNode):   return notYetImplemented(presentationMeshNode)
	def Create_FxReference(self, referenceNode):                 return notYetImplemented(referenceNode)
	def Create_FxReplaceFace(self, replaceFaceNode):             return notYetImplemented(replaceFaceNode)
	def Create_FxRest(self, restNode):                           return notYetImplemented(restNode)
	def Create_FxRib(self, ribNode):                             return notYetImplemented(ribNode)
	def Create_FxRuledSurface(self, ruledSurfaceNode):           return notYetImplemented(ruledSurfaceNode)
	def Create_FxSculpt(self, sculptNode):                       return notYetImplemented(sculptNode)
	def Create_FxShell(self, shellNode):                         return notYetImplemented(shellNode)
	def Create_FxSnapFit(self, snapFitNode):                     return notYetImplemented(snapFitNode) # Cut Geometry (Wedge - Cube)
	def Create_FxThread(self, threadNode):                       return notSupportedNode(threadNode) # https://www.freecadweb.org/wiki/Thread_for_Screw_Tutorial/de
	def Create_FxTrim(self, trimNode):                           return notYetImplemented(trimNode)

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
	def Create_FxFlangeLofted(self, flangeNode):                 return notYetImplemented(flangeNode)
	def Create_FxFold(self, foldNode):                           return notYetImplemented(foldNode)
	def Create_FxHem(self, hemNode):                             return notYetImplemented(hemNode)
	def Create_FxKnit(self, knitNode):                           return notYetImplemented(knitNode)
	def Create_FxPunchTool(self, punchToolNode):                 return notYetImplemented(punchToolNode)
	def Create_FxRefold(self, refoldNode):                       return notYetImplemented(refoldNode)
	def Create_FxRip(self, ripNode):                             return notYetImplemented(ripNode)
	def Create_FxUnfold(self, unfoldNode):                       return notYetImplemented(unfoldNode)

	def Create_FxUnknown(self, unknownNode):
		logError('   Can\'t process unknown Feature \'%s\' - probably an unsupported iFeature!' %(unknownNode.name))
		return

	def Create_Feature(self, featureNode):
		name  = featureNode.getSubTypeName()
		index = featureNode.index
		logMessage('    adding Fx%s \'%s\' ...' %(name, featureNode.name), LOG.LOG_INFO)
		createFxObj = getattr(self, 'Create_Fx%s' %(name))
		createFxObj(featureNode)
		self.doc.recompute()
		return

	def addSketch_Spline3D_Curve(self, bezierNode, edges):
		points=[]
		for entity in bezierNode.get('entities'):
			if (entity.typeName == 'Point3D'):
				points.append(createVector(getX(entity), getY(entity), getZ(entity)))
		if (len(points) > 2):
			pass
			#bezier = Part.BezierCurve()
			#bezier.setPoles(points)
			#addSketch3D(edges, part, isConstructionMode(bezierNode), bezierNode)
		else:
			logError('ERROR> Bezier requires at least 3 points - found only %d!' %(len(points)))
		return

	def addSketch_BSpline3D(self, bsplineNode, edges):
		points=[]
		for p in bsplineNode.get('points'):
			points.append(createVector(getX(p), getY(p), getZ(p)))

		bspline = Part.BSplineCurve()
		bspline.interpolate(points, False)
		addSketch3D(edges, bspline, isConstructionMode(bsplineNode), bsplineNode)
		return

	def addSketch_Bezier3D(self, bezierNode, edges):
		# handled together with either Spline3D_Curve or BSpline3D
		return

	def addSketch_Plane(self, lineNode, edges):                          return
	def addSketch_Spline3D_Fixed(self, splineNode, edges):               return
	def addSketch_Spiral3D_Curve(self, spiralNode, edges):               return

	def addSketch_Dimension_Length3D(self, dimensionNode, edges):        return notSupportedNode(dimensionNode)
	def addSketch_Dimension_Angle2Planes3D(self, dimensionNode, edges):  return notSupportedNode(dimensionNode)

	def addSketch_Geometric_Bend3D(self, geometricNode, edges):          return notSupportedNode(geometricNode)
	def addSketch_Geometric_Custom3D(self, geometricNode, edges):        return notSupportedNode(geometricNode)
	def addSketch_Geometric_Coincident3D(self, geometricNode, edges):    return notSupportedNode(geometricNode)
	def addSketch_Geometric_Collinear3D(self, geometricNode, edges):     return notSupportedNode(geometricNode)
	def addSketch_Geometric_Helical3D(self, geometricNode, edges):       return notSupportedNode(geometricNode)
	def addSketch_Geometric_Horizontal3D(self, geometricNode, edges):    return notSupportedNode(geometricNode)
	def addSketch_Geometric_Smooth3D(self, geometricNode, edges):        return notSupportedNode(geometricNode)
	def addSketch_Geometric_Parallel3D(self, geometricNode, edges):      return notSupportedNode(geometricNode)
	def addSketch_Geometric_Perpendicular3D(self, geometricNode, edges): return notSupportedNode(geometricNode)
	def addSketch_Geometric_Radius3D(self, geometricNode, edges):        return notSupportedNode(geometricNode)
	def addSketch_Geometric_Tangential3D(self, geometricNode, edges):    return notSupportedNode(geometricNode)
	def addSketch_Geometric_Vertical3D(self, geometricNode, edges):      return notSupportedNode(geometricNode)

	def addSketch_4F240E1C(self, node, edges): return

	def Create_Sketch3D(self, sketchNode):
		# Workaround: Create a Part.Feature from wires => not editable afterwards :(
		# or Part.MultiFuse => change all addSketch_.*3D!!!
		edges = []

#		sketchObj = self.CreateEntity(sketchNode, 'Part::MultiFuse')
		sketchObj = self.CreateEntity(sketchNode, 'Part::Feature')
		logMessage('   adding 3D-Sketch \'%s\' ...' %(sketchObj.Label), LOG.LOG_INFO)

		if (self.root):
			self.root.addObject(sketchObj)

		for ref in sketchNode.get('entities'):
			child = ref.node
			if (child.handled == False):
				try:
					addSketchObj = getattr(self, 'addSketch_%s' %(child.typeName))
					addSketchObj(child, edges)
				except AttributeError as e:
					logError('Warning: Don\'t know how to add %s to sketch - %s'  %(child.typeName, e))
					logError('>E: ' + traceback.format_exc())
				except:
					logError('>E: ' + traceback.format_exc())
			child.handled = True
			child = child.next
#		if (len(edges) > 1):
#			sketchObj.Shapes = edges
#			self.hide(edges)
#			sketchNode.setSketchEntity(-1, sketchObj)
#		elif (len(edges) == 1):
#			sketchNode.setSketchEntity(-1, edges[0])
		shape = Part.Shape(edges)
		sketchObj.Shape = shape
		sketchNode.setSketchEntity(-1, sketchObj)

		return

	def Create_BrowserFolder(self, originNode):
		'''
		Skip creation of origin objects.
		'''
		child = originNode.first
		while (child):
			child.handled = True
			child = child.next

		return

	def Create_Line3D(self, lineNode):
		self.addSketch_Line3D(lineNode, None)

	def Create_Plane(self, planeNode):                             return ignoreBranch(planeNode)
	def Create_Body(self, bodyNode):                               return ignoreBranch(bodyNode)
	def Create_Circle3D(self, radiusNode):                         return ignoreBranch(radiusNode)
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

	def Create_Blocks(self, blocksNode):                   return
	def Create_DerivedAssembly(self, derivedAssemblyNode): return
	def Create_DerivedPart(self, derivedPartNode):         return
	def Create_DeselTable(self, deselTableNode):           return
	def Create_Dimension(self, dimensionNode):             return
	def Create_Direction(self, directionNode):             return
	def Create_Label(self, labelNode):                     return
	def Create_ModelAnnotations(self, modelNode):          return
	def Create_Transformation(self, transformationNode):   return
	def Create_UserCoordinateSystem(self, usrCrdSysNode):  return
	def Create_MeshFolder(self, meshFolderNode):           return

	def Create_2B48A42B(self, node): return
	def Create_3902E4D1(self, node): return
	def Create_5844C14D(self, node): return
	def Create_CADC79F0(self, node): return
	def Create_EBA98FD3(self, node): return
	def Create_FBC6C635(self, node): return
	def Create_F3DBA9D8(self, node): return

	@staticmethod
	def findDC(storage):
		'''
		storage The map of defined RSeStorageDatas
		Returns the segment that contains the 3D-objects.
		'''
		if (storage):
			for name in storage.keys():
				seg = storage[name]
				if (RSeMetaData.isDC(seg)):
					return seg
		return None

	def addParameterTableTolerance(self, table, r, tolerance):
		if (tolerance):
			table.set('D%d' %(r), tolerance)
			return u'; D%d=\'%s\'' %(r, tolerance)
		return u''

	def addParameterTableComment(self, table, r, commentRef):
		if (commentRef):
			comment = commentRef.name
			if (comment):
				table.set('E%d' %(r), comment)
				return u'; E%d=\'%s\'' %(r, comment)
		return u''

	def addOperandParameter(self, table, nextRow, parameters, operandRef):
		if (operandRef):
			return self.addReferencedParameters(table, nextRow, parameters, operandRef)
		return nextRow

	def addReferencedParameters(self, table, r, parameters, value):
		nextRow = r
		typeName   = value.typeName

		if (typeName == 'ParameterRef'):
			parameterData = value.get('refParameter').data
			nextRow = self.addParameterToTable(table, nextRow, parameters, parameterData.name)
		elif (typeName.startswith('ParameterOperation')):
			nextRow = self.addOperandParameter(table, nextRow, parameters, value.get('refOperand1'))
			nextRow = self.addOperandParameter(table, nextRow, parameters, value.get('refOperand2'))
		elif (typeName == 'ParameterValue'):
			pass # Nothing to do here!
		else:
			value = value.get('refValue')
			if (value):
				typeName   = value.typeName

				if (typeName == 'ParameterUnaryMinus'):
					nextRow = self.addReferencedParameters(table, nextRow, parameters, value)
				elif (typeName == 'ParameterRef'):
					parameterData = value.get('refParameter').data
					nextRow = self.addParameterToTable(table, nextRow, parameters, parameterData.name)
				elif (typeName == 'ParameterFunction'):
					operandRefs = value.get('operands')
					j = 0
					sep = '('
					n = len(operandRefs)
					if (n > 0):
						while (j < n):
							nextRow = self.addReferencedParameters(table, nextRow, parameters, operandRefs[j])
							j += 1
				elif (typeName.startswith('ParameterOperation')):
					nextRow = self.addOperandParameter(table, nextRow, parameters, value.get('refOperand1'))
					nextRow = self.addOperandParameter(table, nextRow, parameters, value.get('refOperand2'))
				elif (typeName == 'ParameterOperationPowerIdent'):
					nextRow = self.addReferencedParameters(table, nextRow, parameters, value.get('refOperand1'))
		return nextRow

	def addParameterToTable(self, table, r, parameters, key):
		if (key in parameters):
			valueNode = parameters[key].node

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
				mdlValue = u''
				tlrValue = u''
				remValue = u''
				valueNode.set('alias', 'T_Parameters.%s_' %(key))
				typeName = valueNode.typeName

				if (typeName == 'Parameter'):
					r = self.addReferencedParameters(table, r, parameters, valueNode)
					#nominalValue = getNominalValue(valueNode)
					#nominalFactor = valueNode.getUnitFactor()
					#nominalOffset = valueNode.getUnitOffset()
					#nominalUnit  = valueNode.data.getUnitName()
					#if (len(nominalUnit) > 0): nominalUnit = ' ' + nominalUnit
					#formula = '%s%s' %((nominalValue / nominalFactor)  - nominalOffset, nominalUnit)
					value   = valueNode.getValue().__str__()
					formula = valueNode.getFormula(True)
					table.set('A%d' %(r), key.encode('utf8'))
					table.set('B%d' %(r), value.encode('utf8'))
					table.set('C%d' %(r), formula.encode('utf8'))
					mdlValue = '; C%s=%s' %(r, formula)
					tlrValue = self.addParameterTableTolerance(table, r, valueNode.get('tolerance'))
					remValue = self.addParameterTableComment(table, r, valueNode.get('label'))
				elif (typeName == 'ParameterText'):
					value = valueNode.get('value')
					table.set('A%d' %(r), key.encode('utf8'))
					table.set('B%d' %(r), '\'%s' %(value.encode('utf8')))
					remValue = self.addParameterTableComment(table, r, valueNode.get('label'))
				elif (typeName == 'ParameterBoolean'):
					value = valueNode.get('value')
					table.set('A%d' %(r), key.encode('utf8'))
					table.set('B%d' %(r), value.encode('utf8'))
					remValue = self.addParameterTableComment(table, r, valueNode.get('label'))
				else: #if (key.find('RDxVar') != 0):
					value = valueNode
					table.set('A%d' %(r), '%s' %(key.encode('utf8')))
					table.set('B%d' %(r), '%s' %(value.encode('utf8')))
					remValue = self.addParameterTableComment(table, r, valueNode.get('label'))

				if (key.find('RDxVar') != 0):
					try:
						aliasValue = '%s_' %(key.replace(':', '_'))
						table.setAlias('B%d' %(r), aliasValue.encode('utf8'))
					except Exception as e:
						logError(u'    >ERROR: Can\'t set alias name for B%d - invalid name \'%s\' - %s!' %(r, aliasValue, e))

					logMessage(u'        A%d=\'%s\'; B%d=\'%s\'%s\'%s%s' %(r, key, r, value, mdlValue, tlrValue, remValue), LOG.LOG_INFO)
					return r + 1
		else:
			assert False, 'ERROR: %s not found in parameters!' %(key)
		return r

	def createParameterTable(self, partNode):
		parameterRefs = partNode.get('parameters')
		table = newObject(self.doc, 'Spreadsheet::Sheet', u'T_Parameters')
		logMessage('    adding parameters table...', LOG.LOG_INFO)
		table.set('A1', 'Parameter')
		table.set('B1', 'Value')
		table.set('C1', 'Fromula')
		table.set('D1', 'Tolerance')
		table.set('E1', 'Comment')
		r = 2
		keys = parameterRefs.keys()
		for key in keys:
			r = self.addParameterToTable(table, r, parameterRefs, key)
		return

	def importModel(self, model):
		if (model):
			storage = model.RSeStorageData

			grx = FreeCADImporter.findDC(storage)

			if (grx):
				self.mapConstraints = {}
				root = grx.tree.getFirstChild('Document')
				label = root.get('label')
				self.createParameterTable(root.get('refElements').node)
				lst = label.get('lst0')
				for ref in lst:
					self.getEntity(ref)
				if (self.doc):
					self.doc.recompute()
			else:
				logWarning('>>>No content to be displayed<<<')

		return
