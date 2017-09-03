#!/usr/bin/env python

'''
importerFreeCAD.py
'''
import Draft
import Part
import Sketcher
import FreeCAD
import traceback
from importerUtils   import logMessage, logWarning, logError, LOG, IFF, IntArr2Str, FloatArr2Str, getFileVersion
from importerClasses import RSeMetaData, Angle, Length, ParameterNode, ParameterTextNode, ValueNode, FeatureNode, AbstractValue
from importerSegNode import AbstractNode
from math            import sqrt, sin, cos, acos, atan2, degrees, radians, pi

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.3.1'
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

# x 10                2   2   1   1   0   0   0
# x  1                4   0   6   2   8   4   0
#SKIP_CONSTRAINS = 0b11111111111111111111111111
#SKIP_CONSTRAINS = 0b00000000000000000000000100 # Only geometric coincidens
SKIP_CONSTRAINS  = 0b11111100110001111010110111 # no workarounds, nor unsupported constrains!

def ignoreBranch(node):
	return None

def notSupportedNode(node):
	return None

def createVector(x, y, z):
	return FreeCAD.Vector(x, y, z)

def createRotation(axis, angle):
	return FreeCAD.Rotation(axis, angle)

def createGroup(doc, name):
	grp = None
	if (doc):
		grp = doc.addObject('App::DocumentObjectGroup', name)
	return grp

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

def calcAngle2D(p1Data, ref2):
	p2 = None
	if (p1Data):
		if (ref2):
			p2 = ref2.node
			if (p2 is not None):
				x1 = getX(p1Data)
				y1 = getY(p1Data)
				x2 = getX(p2)
				y2 = getY(p2)

				dx = (x2 - x1)
				dy = (y2 - y1)
				angle = atan2(dy, dx)
				if (angle < 0):
					angle += radians(360.0)
				return Angle(angle, pi/180.0, '\xC2\xB0')
	return None

def calcAngle3D(x1, y1, z1, x2, y2, z2):
	s = (x1*x2 + y1*y2 + z1*z2)
	l1 = sqrt(x1*x1 + y1*y1 + z1*z1)
	l2 = sqrt(x2*x2 + y2*y2 + z2*z2)
	if ((l1 != 0) and (l2 != 0)):
		angle = acos(s/l1/l2)
	else:
		angle = radians(90.0)
	return Angle(angle, pi/180.0, '\xC2\xB0')

def getCoord(pData, coordName):
	c = pData.get(coordName)
	if (c is None):
		logError('ERROR - (%04X): %s has no \'%s\' property!' %(pData.index, pData.typeName, coordName))
		return 0.0
	return c * 10.0

def getX(pData):
	return getCoord(pData, 'x')

def getY(pData):
	return getCoord(pData, 'y')

def getZ(pData):
	return getCoord(pData, 'z')

def getDistanceX(pData, qData):
	px = getX(pData)
	qx = getX(qData)
	return 	qx - px

def getDistanceY(pData, qData):
	return getY(qData) - getY(pData)

def getDistancePointPoint(pData, qData):
	dx = getDistanceX(pData, qData)
	dy = getDistanceY(pData, qData)
	return sqrt(dx*dx + dy*dy)

def getDistanceLinePoint(lineData, pointData):
	pData = lineData.get('points')[0].node
	qData = lineData.get('points')[1].node
	# Adjust vectors relative to P
	# Q becomes relative vector from P to end of segment
	qx = getDistanceX(pData, qData)
	qy = getDistanceY(pData, qData)
	# A becomes relative vector from P to test point
	ax = getDistanceX(pData, pointData)
	ay = getDistanceY(pData, pointData)
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

def getDistanceCircleLine(circleData, lineData):
	pointData = circleData.get('refCenter').node
	distance = getDistanceLinePoint(lineData, pointData)
	return distance - getCoord(circleData, 'r')

def getDistanceCirclePoint(circleData, pointData):
	centerData = circleData.get('refCenter').node
	distance = getDistancePointPoint(centerData, pointData)
	return distance - getCoord(circleData, 'r')

def getDistanceCircleCircle(circle1Data, circle2Data):
	pointData = circle2Data.get('refCenter').node
	distance = getDistanceCirclePoint(circle1Data, pointData)
	return distance - getCoord(circle2Data, 'r')

def getLengthPoints(entity1Data, entity2Data):
	type1 = entity1Data.typeName
	type2 = entity2Data.typeName

	if (type1 == 'Point2D'):
		if (type2 == 'Point2D'):
			return getDistancePointPoint(entity1Data, entity2Data)
		if (type2 == 'Line2D'):
			return getDistanceLinePoint(entity2Data, entity1Data)
		if (type2 == 'Circle2D'):
			return getDistanceCirclePoint(entity2Data, entity1Data)
	if (type1 == 'Line2D'):
		if (type2 == 'Point2D'):
			return getDistanceLinePoint(entity1Data, entity2Data)
		if (type2 == 'Line2D'):
			# Hope that the lines are parallel!
			return getDistanceLinePoint(entity1Data, entity2Data.get('points')[0].node)
		if (type2 == 'Circle2D'):
			return getDistanceCircleLine(entity2Data, entity1Data)
	if (type1 == 'Circle2D'):
		if (type2 == 'Point2D'):
			return getDistanceCirclePoint(entity1Data, entity2Data)
		if (type2 == 'Line2D'):
			# Hope that the lines are parallel!
			return getDistanceCircleLine(entity1Data, entity2Data)
		if (type2 == 'Circle2D'):
			return getDistanceCircleCircle(entity1Data, entity2Data)
	raise BaseException('Don\'t know how to determine the distance between \'%s\' and \'%s\'!' %(type1, type2))

def getLengthLine(lineNode):
	point1 = lineNode.get('points')[0].node
	point2 = lineNode.get('points')[1].node
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

def getNode(sourceNode, varName):
	if (sourceNode):
		ref = sourceNode.get(varName)
		if (ref):
			return ref.getBranchNode()
	return None

def findEntityVertex(entityData, pointData):
	entityName = entityData.typeName
	if (entityName == 'Point2D'):
		return 1

	x = pointData.get('x')
	y = pointData.get('y')

	if (entityName == 'Circle2D' or entityName == 'Ellipse2D'):
		p2Data = entityData.get('refCenter').node
		if ((x == p2Data.get('x')) and (y == p2Data.get('y'))):
			return 3
		pointRefs = getCirclePoints(entityData.node)
	else:
		pointRefs = entityData.get('points')

	if (not pointRefs is None):
		j = 0
		while (j < len(pointRefs)):
			pointRef = pointRefs[j]
			if (pointRef): # Might be None for closed circles
				p2Data = pointRef.node
				if (p2Data):
					if ((x == p2Data.get('x')) and (y == p2Data.get('y'))):
						return j + 1
			j += 1
	else:
		logError('FATAL: (%04X): %s has not attribute points!' %(entityData.index, entityName))
	return -1

def getPropertyValue(properties, index, name):
	if (index < len(properties)):
		ref = properties[index]
		if (ref):
			node = ref.node
			if (node):
				return node.get(name)
	return None

def getDimension(node, varName):
	dimension  = getNode(node, varName)

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
		if (ref.node.typeName == 'Line2D'):
			return i
		return getNextLineIndex(coincidens, i + 1)
	return len(coincidens)

def getListNode(list, index):
	if (index < len(list)):
		ref = list[index]
		if (ref):
			return ref.node
	return None

def getPlacement(placementData):
	transformation = placementData.get('transformation')
	matrix4x4      = transformation.getMatrix()

	# convert centimeter to millimeter
	matrix4x4.A14  *= 10.0
	matrix4x4.A24  *= 10.0
	matrix4x4.A34  *= 10.0

	return FreeCAD.Placement(matrix4x4)

def calcPointKey(pointData):
	point = pointData
	if (pointData.typeName == '18A9717E'):
		point = pointData.get('refPoint')
	assert (point.typeName == 'Point2D'), 'point data is not Point2D <> (%04X): %s' %(pointData.index, pointData.typeName)
	return ('K%g_%g' %(getX(point), getY(point))).replace('-', '_').replace('.', '_')

def getCirclePoints(circleNode):
	pointRefs   = circleNode.get('points')
	centerRef   = circleNode.get('refCenter')
	x_old       = None
	y_old       = None
	map         = {}
	j           = 0
	points      = []
	angleOffset = None

	while (j < len(pointRefs)):
		pointRef = pointRefs[j]
		if (pointRef):
			angle = calcAngle2D(centerRef.node, pointRef)
			if (angleOffset is None):
				angleOffset = angle.x
			angle.x -= angleOffset
			if (not angle.x in map):
				map[angle.x] = pointRef
		j += 1

	if (len(map) > 0):
		keys = map.keys()
		keys.sort()
		while (keys[0] != 0.0):
			key = keys[0]
			keys.append(key)
			del keys[0]
		for key in keys:
			pointRef = map[key]
			x_new = pointRef.get('x')
			y_new = pointRef.get('y')
			if ((x_new != x_old) or (y_new != y_old)):
				points.append(pointRef)
				x_old = x_new
				y_old = y_new

	return points

def addCoincidentEntity(coincidens, entityRef):
	if (entityRef.typeName == 'Point2D'):
		entities = entityRef.get('entities')
		for ref in entities:
			addCoincidentEntity(coincidens, ref)
	else:
		entityData = entityRef.node
		for entity in coincidens:
			if (entity.index == entityData.index):
				# already added -> done!
				return

		coincidens.append(entityData)
	return

def getFirstBodyName(ref):
	name = ''

	if (ref):
		bodies = ref.get('bodies')
		if ((bodies) and (len(bodies) > 0)):
			name = bodies[0].getName()

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

def adjustViewObject(newGeo, baseGeo):
	if ((FreeCAD.GuiUp) and (baseGeo is not None)):	
		baseGeo.ViewObject.hide()
		newGeo.ViewObject.ShapeColor  = baseGeo.ViewObject.ShapeColor
		newGeo.ViewObject.DisplayMode = baseGeo.ViewObject.DisplayMode
		newGeo.ViewObject.LineColor   = baseGeo.ViewObject.LineColor
		newGeo.ViewObject.PointColor  = baseGeo.ViewObject.PointColor

class FreeCADImporter:
	FX_EXTRUDE_NEW          = 0x0001
	FX_EXTRUDE_CUT          = 0x0002
	FX_EXTRUDE_JOIN         = 0x0003
	FX_EXTRUDE_INTERSECTION = 0x0004
	FX_EXTRUDE_SURFACE      = 0x0005

	FX_DRILL_DRILLED        = 0x0000
	FX_DRILL_SINK           = 0x0001
	FX_DRILL_BORED          = 0x0002
	FX_DRILL_SPOT           = 0x0003

	def __init__(self, root, doc):
		self.root             = root
		self.doc              = doc
		self.mapConstraints   = None
		self.pointDataDict    = None
		self.bodyNodes   = {}

	def checkSketchIndex(self, sketchObj, entityNode):
		if (entityNode):
			if (entityNode.isHandled() == False):
				self.Create_Sketch2D_Node(sketchObj, entityNode)
				if (entityNode.getSketchIndex() is None and entityNode.isValid()):
					logError('        ... Failed to create (%04X): %s' %(entityNode.index, entityNode.typeName))
			if (entityNode.isValid()):
				return  entityNode.getSketchIndex()
		return None

	def addConstraint(self, sketchObj, constraint, key):
		index = sketchObj.addConstraint(constraint)
		self.mapConstraints[key] = constraint
		return index

	def addSolidBody(self, fxNode, obj3D, solidRef):
		fxNode.setSketchEntity(-1, obj3D)

		if (solidRef):
			bodies = solidRef.get('bodies')
			if ((bodies) and (len(bodies) > 0)):
				bodyRef = bodies[0]
				baseName = bodyRef.getName()
				# overwrite previously added solids with the same name!
				self.bodyNodes[baseName] = fxNode
		return

	def addSurfaceBody(self, fxNode, obj3D, surfaceRef):
		fxNode.setSketchEntity(-1, obj3D)
		name = surfaceRef.getName()
		# overwrite previously added sourfaces with the same name!
		self.bodyNodes[name] = fxNode
		return

	def addBody(self, fxNode, body, solidIdx, surfaceIdx):
		properties = fxNode.get('properties')
		solidRef = properties[solidIdx]
		if (solidRef):
			self.addSolidBody(fxNode, body, solidRef)
		else:
			sourfaceRef = properties[surfaceIdx]
			if(sourfaceRef):
				self.addSurfaceBody(fxNode, body, sourfaceRef)
		return

	def findBase(self, baseNode):
		assert (baseNode.typeName == '90874D74'), 'FATA> Expected 90874D74 not (%04X): %s!' %(baseNode.index, baseNode.typeName)
		baseGeo = None
		if (baseNode is not None):
			baseRef = baseNode.get('refBase')
			if (baseRef):
				return self.findBase2(baseRef)
			else:
				logError('ERROR> Base (%04X): %s not defined!' %(baseNode.index, baseNode.typeName))
		return baseGeo

	def findBase2(self, baseRef):
		baseGeo = None
		if (baseRef is not None):
			baseName = getFirstBodyName(baseRef)
			if (baseName in self.bodyNodes):
				bodyNode = self.bodyNodes[baseName]
				baseGeo  = bodyNode.getSketchEntity()
				if (baseGeo is None):
					logWarning('    Base2 (%04X): %s -> (%04X): %s not yet created!' %(baseRef.index, baseNode.typeName, bodyNode.index, bodyNode.typeName))
				else:
					logMessage('        ... Base2 = \'%s\'' %(baseName), LOG.LOG_INFO)
			else:
				logWarning('    Base2 (%04X): %s -> \'%s\' nod found!' %(baseRef.index, baseRef.typeName, baseName))
		else:
			logWarning('    Base2: ref is None!')

		return baseGeo

	def findGeometries(self, baseNode):
		geometries = []
		if (baseNode is not None):
			baseData = baseNode.data
			assert (baseData.typeName == '90874D74'), 'FATA> (%04X): %s expected 90874D74 ' %(baseData.index, baseData.typeName)
			tools = baseData.get('tools')
			if (tools):
				for toolRef in tools:
					toolName = getFirstBodyName(toolRef)
					if (toolName in self.bodyNodes):
						bodyNode = self.bodyNodes[toolName]
						toolGeo  = bodyNode.getSketchEntity()
						if (toolGeo is None):
							logWarning('        Tool (%04X): %s -> (%04X): %s not yet created' %(baseData.index, baseData.typeName, toolData.index, toolData.typeName))
						else:
							geometries.append(toolGeo)
							logMessage('        ... Tool = \'%s\'' %(toolName), LOG.LOG_INFO)
					else:
						logWarning('    Tool (%04X): %s -> \'%s\' nod found!' %(baseNode.index, baseNode.typeName, toolName))
			else:
				logError('ERROR> Tools (%04X): %s not defined!' %(baseNode.index, baseNode.typeName))
		else:
			logWarning('    Tool: ref is None!')
		return geometries

	def addDimensionConstraint(self, sketchObj, dimension, constraint, key, useExpression = True):
		number = sketchObj.ConstraintCount
		index = self.addConstraint(sketchObj, constraint, key)
		name = dimension.getName()
		if (len(name)):
			constraint.Name = name
			sketchObj.renameConstraint(index, name)
			if (useExpression):
				expression = dimension.get('alias')
				sketchObj.setExpression('Constraints[%d]' %(number), expression)
		else:
			constraint.Name = 'Constraint%d' %(index)
		return index

	def getGeometryIndex(self, sketchObj, node, varName):
		target = getNode(node, varName)
		if (target.isValid()):
			return self.checkSketchIndex(sketchObj, target)
		return None

	def addPoint2Dictionary(self, pointRef):
		pointData = pointRef.node
		key = calcPointKey(pointData)

		if (not key in self.pointDataDict):
			entities = []
			entities.append(pointData)
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
						index = ref.sketchIndex
						pos = ref.sketchPos
		return index, pos

	def addCoincidentConstraint(self, fixIndex, fixPos, fixName, movData, sketchObj, pointData):
		constraint = None
		if (movData):
			movName  = movData.typeName
			movIndex = self.checkSketchIndex(sketchObj, movData.node)

			if (movIndex is None):
				logWarning('        ... can\'t create 2D \'coincident\' constraint between %s %s/%s and %s -  %s has no index!' %(fixName[0:-2], fixIndex, fixPos, movName[0:-2], movName[0:-2]))
			else:
				movPos   = findEntityVertex(movData, pointData)

				if (movPos < 0):
					if (fixPos < 0):
						logWarning('        ... 2D \'object on object\' coincident: between (%04X): %s and (%04X): %s failed - Feature not supported by FreeCAD!!!' %(fixIndex, fixName, movIndex, movName))
					else:
						constraint = Sketcher.Constraint('PointOnObject', fixIndex, fixPos, movIndex)
						logMessage('        ... added 2D \'point on object\' constraint between %s %s/%s and %s %s' %(fixName[0:-2], fixIndex, fixPos, movName[0:-2], movIndex), LOG.LOG_INFO)
				else:
					movIndex, movPos = self.adjustIndexPos(movData, movIndex, movPos, pointData)
					if (fixPos < 0):
						constraint = Sketcher.Constraint('PointOnObject', movIndex, movPos, fixIndex)
						logMessage('        ... added 2D \'point on object\' constraint between %s %s/%s and %s %s' %(movName[0:-2], movIndex, movPos, fixName[0:-2], fixIndex), LOG.LOG_INFO)
					else:
						constraint = Sketcher.Constraint('Coincident', fixIndex, fixPos, movIndex, movPos)
						logMessage('        ... added 2D \'coincident\' constraint (%g, %g) between %s %s/%s and %s %s/%s' %(pointData.get('x')*10, pointData.get('y')*10, fixName[0:-2], fixIndex, fixPos, movName[0:-2], movIndex, movPos), LOG.LOG_INFO)
		return constraint

	def addSketch2D_ConstructionPoint2D(self, pointNode, sketchObj):
		pointData = pointNode.data
		index = pointData.sketchIndex
		if ((index is None) or (index == -2)):
			mode = True
			x = getX(pointData)
			y = getY(pointData)
			part = Part.Point(createVector(x, y, 0))
			addSketch2D(sketchObj, part, mode, pointNode)
			index = pointNode.getSketchIndex()
		return index

	def getPointIndexPos(self, sketchObj, pointData):
		key = calcPointKey(pointData)
		if (key in self.pointDataDict):
			entities = self.pointDataDict[key]
		else:
			entities = []
		# the first element is a point!
		if (len(entities) > 1):
			entityData = entities[1]
			index = self.checkSketchIndex(sketchObj, entityData.node)
			pos   = findEntityVertex(entityData, pointData)
		else:
			index = self.addSketch2D_ConstructionPoint2D(pointData.node, sketchObj)
			pos   = 1
		return index, pos

	def getSketchEntityInfo(self, sketchObj, entityData):
		if (entityData.typeName == 'Point2D'):
			entityIndex, entityPos = self.getPointIndexPos(sketchObj, entityData)
		else:
			entityIndex = self.checkSketchIndex(sketchObj, entityData.node)
			entityPos   = -1
		return entityIndex, entityPos

	def fix2D(self, sketchObj, pointData):
		key = 'Fix_%X' %(pointData.index)
		if (not key in self.mapConstraints):
			x = getX(pointData)
			y = getY(pointData)
			index, pos = self.getSketchEntityInfo(sketchObj, pointData)
			if (index is not None):
				constraintX = Sketcher.Constraint('DistanceX', index, pos, x)
				constraintY = Sketcher.Constraint('DistanceY', index, pos, y)
				indexX = self.addConstraint(sketchObj, constraintX, key)
				indexY = self.addConstraint(sketchObj, constraintY, key)
		return

	def getCirclePointRefs(self, sketchObj, pointRef, circleIndex):
		count = 0
		entities = pointRef.get('entities')
		for entityRef in entities:
			if (entityRef.index != circleIndex):
				if (self.checkSketchIndex(sketchObj, entityRef.getBranchNode()) >= 0):
					count += 1
		return count

	def addDistanceConstraint(self, sketchObj, dimensionNode, skipMask, name, prefix):
		if (SKIP_CONSTRAINS & skipMask == 0): return
		entity1Ref = dimensionNode.get('refEntity1')
		entity2Ref = dimensionNode.get('refEntity2')
		entity1Data = entity1Ref.node
		entity2Data = entity2Ref.node
		entity1Name = entity1Data.typeName[0:-2]
		entity2Name = entity2Data.typeName[0:-2]
		index1, pos1 = self.getSketchEntityInfo(sketchObj, entity1Data)
		index2, pos2 = self.getSketchEntityInfo(sketchObj, entity2Data)

		prefix = IFF(len(prefix)>0, '%s ' %(prefix), '')

		if (index1 is None):
			logWarning('        ... skipped 2D %sdimension beween %s and %s - entity 1 (%04X) has no index!' %(prefix, entity1Name, entity2Name, entity1Data.index))
		elif (index2 is None):
			logWarning('        ... skipped 2D %sdimension beween %s and %s - entity 2 (%04X) has no index!' %(prefix, entity1Name, entity2Name, entity2Data.index))
		else:
			constraint = None
			key = '%s_%s_%s' %(constraint, index1, index2)
			if (not key in self.mapConstraints):
				lengthMM = getLengthPoints(entity1Data, entity2Data)
				if (pos1 < 0):
					if (pos2 < 0):
						# other distances are not supported by FreeCAD!
						if ((entity1Ref.typeName == 'Line2D') and (entity2Ref.typeName == 'Line2D')):
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
					logMessage('        ... added 2D %sdistance \'%s\' = %s' %(prefix, constraint.Name, length), LOG.LOG_INFO)
				else:
					logWarning('        ... can\'t create dimension constraint between (%04X): %s and (%04X): %s - not supported by FreeCAD!' %(entity1Ref.index, entity1Name, entity2Ref.index, entity2Name))
		return

	def CreateObject(self, node):
		try:
			importObject = getattr(self, 'Create_%s' %(node.typeName))
			importObject(node)
			node.setHandled(True)
		except Exception as e:
			logError('Error in creating (%04X): %s - %s'  %(node.index, node.typeName, e))
			logError('>E: ' + traceback.format_exc())
		return node.getSketchEntity()

	def collectSection(self, fxNode, action):#
		definitionRef = fxNode.get('label')
		sections      = []
		solid         = (definitionRef.typeName == 'Label')
		if (solid == False):
			definitionRef = definitionRef.get('label')
		name          = definitionRef.getName()
		lst0 = definitionRef.get('lst0')

		logMessage('    adding Fx%s \'%s\' for %d sections...' %(fxNode.getSubTypeName, name, len(lst0)), LOG.LOG_INFO)
		for sectionRef in lst0:
			# only Sketch2D's are supported!
			if (sectionRef.typeName == 'Sketch2D'):
				sketchNode = sectionRef.getBranchNode()
				if (sketchNode.getSketchEntity() is None):
					self.CreateObject(sketchNode)
				sections.append(sketchNode.getSketchEntity())
			if (sectionRef.typeName == 'Sketch3D'):
				sketchNode = sectionRef.getBranchNode()
				if (sketchNode.getSketchEntity() is None):
					self.CreateObject(sketchNode)
				sections.append(sketchNode.getSketchEntity())
			else:
				logWarning('        ... don\'t know how to %s (%04X): %s \'%s\' - IGNORED!' %(action, sectionRef.index, sectionRef.typeName, sectionRef.getName()))
		return solid, sections

########################
	def addSketch2D_Geometric_Fix2D(self, constraintNode, sketchObj):
		'''
		A fix constraint doesn't exists in FreeCAD.
		Workaround: two distance constraints (X and Y)
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_FIX == 0): return
		return

	def addSketch2D_Geometric_PolygonCenter2D(self, constraintNode, sketchObj):
		# handled together with addSketch2D_Geometric_PolygonEdge2D
		return ignoreBranch(constraintNode)

	def addSketch2D_Geometric_PolygonEdge2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINS & SKIP_GEO_POLYGON == 0): return
		ref1 = constraintNode.get('ref_1')
		ref2 = constraintNode.get('ref_2')
		if ((ref1) and (ref1.typeName == 'Line2D') and (ref2) and (ref2.typeName == 'Line2D')):
			line1Data  = ref1.node
			line1Index = self.checkSketchIndex(sketchObj, line1Data.node)
			centerRef  = constraintNode.get('refCenter')
			polygonRef = constraintNode.get('refPolygonCenter1')
			edgeData   = line1Data.get('points')[0].node # for lines: 'points' should never be None or empty

			if ((centerRef) and (polygonRef)):
				centerData  = centerRef.node
				if (centerData.typeName == 'Point2D'):
					polygonData = polygonRef.node
					circleIndex = polygonData.get('circle')
					if (circleIndex is None):
						r = getDistanceLinePoint(line1Data, centerData)
						x = getX(centerData)
						y = getY(centerData)
						circle = Part.Circle(createVector(x, y, 0), createVector(0, 0, 1), r)
						circleIndex = sketchObj.addGeometry(circle, True)
						polygonData.set('circle', circleIndex)
						logMessage('        ... added 2D \'polygon\' constraint', LOG.LOG_INFO)
					# it's sufficient to create only one Point On Object constraint.
					constraint = Sketcher.Constraint('PointOnObject', line1Index, 1, circleIndex)
					sketchObj.addConstraint(constraint)
				# TODO: What else could this be????
			# make the the two lines the same length
			line2Data  = ref2.node
			line2Index = self.checkSketchIndex(sketchObj, line2Data.node)
			constraint = Sketcher.Constraint('Equal', line1Index, line2Index)
			sketchObj.addConstraint(constraint)
		return

	def addSketch2D_Geometric_Coincident2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINS & SKIP_GEO_COINCIDENT == 0): return
		pointRef = constraintNode.get('refPoint')
		if (pointRef.typeName != 'Point2D'):
			entityRef = pointRef
			pointRef  = constraintNode.get('refObject')
		else:
			entityRef = constraintNode.get('refObject')
		key = calcPointKey(pointRef.node)
		if (key in self.pointDataDict):
			coincidens = self.pointDataDict[key]
			addCoincidentEntity(coincidens, pointRef)
			addCoincidentEntity(coincidens, entityRef)
		return

	def addSketch2D_Geometric_SymmetryPoint2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINS & SKIP_GEO_SYMMETRY_POINT == 0): return
		pointRef = constraintNode.get('refPoint')
		symmetryIdx, symmetryPos = self.getPointIndexPos(sketchObj, pointRef.node)

		moving = getNode(constraintNode, 'refObject')
		lineIdx =  self.checkSketchIndex(sketchObj, moving)

		if (lineIdx is None):
			logWarning('        ... can\'t added 2D symmetric constraint between Point and %s - no line index for (%04X)!' %(moving.typeName[0:-2], moving.index))
		elif (symmetryIdx is None):
			logWarning('        ... can\'t added 2D symmetric constraint between Point and %s - no point index for (%04X)!' %(moving.typeName[0:-2], constraintNode.get('refPoint').index))
		else:
			key = 'SymmetryPoint_%s_%s' %(lineIdx, symmetryIdx)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Symmetric', lineIdx, 1, lineIdx, 2, symmetryIdx, symmetryPos)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D symmetric constraint between Point %s and %s %s' %(symmetryIdx, moving.typeName[0:-2], lineIdx), LOG.LOG_INFO)
		return

	def addSketch2D_Geometric_SymmetryLine2D(self, constraintNode, sketchObj):
		if (SKIP_CONSTRAINS & SKIP_GEO_SYMMETRY_LINE == 0): return
		symmetry    = getNode(constraintNode, 'refLineSym')
		symmetryIdx =  self.checkSketchIndex(sketchObj, symmetry)

		line1 = getNode(constraintNode, 'refLine1')
		line2 = getNode(constraintNode, 'refLine2')
		line1Idx =  self.checkSketchIndex(sketchObj, line1)
		line2Idx =  self.checkSketchIndex(sketchObj, line2)

		if (symmetryIdx is None):
			logWarning('        ... skipped 2D symmetric constraint between lines - symmetry (%04X) has no index!' %(symmetry.index))
		elif (line1Idx is None):
			logWarning('        ... skipped 2D symmetric constraint between lines - line 1 (%04X) has no index!' %(line1.index))
		elif (line2Idx is None):
			logWarning('        ... skipped 2D symmetric constraint between lines - line 2 (%04X) has no index!' %(line2.index))
		else:
			key = 'SymmetricLine_%s_%s_%s' %(line1Idx, line2Idx, symmetryIdx)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Symmetric',line1Idx, 1, line2Idx, 1, symmetryIdx)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D symmetric constraint between lines %s, %s and %s' %(symmetryIdx, line1Idx, line2Idx), LOG.LOG_INFO)
		return

	def addSketch2D_Geometric_Parallel2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_PARALLEL == 0): return
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine2')
		if (index1 is None):
			logWarning('        ... skipped 2D parallel constraint between lines - line 1 (%04X) has no index!' %(constraintNode.get('refLine1').index))
		elif (index2 is  None):
			logWarning('        ... skipped 2D parallel constraint between lines - line 2 (%04X) has no index!' %(constraintNode.get('refLine2').index))
		else:
			key = 'Parallel_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Parallel', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D parallel constraint between lines %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch2D_Geometric_Perpendicular2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idxMov: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_PERPENDICULAR == 0): return
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine2')

		if (index1 is None):
			logMessage('        ... skipped 2D perpendicular constraint between lines - line 1 (%04X) has no index!' %(constraintNode.get('refLine1').index))
		elif (index2 is  None):
			logMessage('        ... skipped 2D perpendicular constraint between lines - line 2 (%04X) has no index!' %(constraintNode.get('refLine2').index))
		else:
			key = 'Perpendicular_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Perpendicular', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D perpendicular constraint between lines %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch2D_Geometric_Collinear2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_COLLINEAR == 0): return
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine2')
		if (index1 is None):
			logMessage('        ... skipped 2D collinear constraint between lines - line 1 (%04X) has no index!' %(constraintNode.get('refLine1').index))
		elif (index2 is  None):
			logMessage('        ... skipped 2D collinear constraint between lines - line 2 (%04X) has no index!' %(constraintNode.get('refLine2').index))
		else:
			key = 'Collinear_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Tangent', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D collinear constraint between Line %s and Line %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch2D_Geometric_Tangential2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_TANGENTIAL == 0): return
		entity1Node = getNode(constraintNode, 'refEntity1')
		entity2Node = getNode(constraintNode, 'refEntity2')
		entity1Name = entity1Node.typeName[0:-2]
		entity2Name = entity2Node.typeName[0:-2]
		index1 = self.checkSketchIndex(sketchObj, entity1Node)
		index2 = self.checkSketchIndex(sketchObj, entity2Node)
		if (index1 is None):
			logWarning('        ... skipped 2D tangential constraint between %s and %s - entity 1 (%04X) has no index!' %(entity1Name, entity2Name, entity1Node.index))
		elif (index2 is None):
			logWarning('        ... skipped 2D tangential constraint between %s and %s - entity 2 (%04X) has no index!' %(entity1Name, entity2Name, entity2Node.index))
		else:
			key = 'Tangent_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Tangent', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D tangential constraint between %s %s and %s %s' %(entity1Name, index1, entity2Name, index2), LOG.LOG_INFO)
		return

	def addSketch2D_Geometric_Vertical2D(self, constraintNode, sketchObj):
		'''
		index: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_VERTICAL == 0): return
		index = self.getGeometryIndex(sketchObj, constraintNode, 'refLine')
		if (index is None):
			logWarning('        ... skipped 2D vertical constraint to line - line (%04X) has no index!' %(constraintNode.get('refLine').index))
		else:
			key = 'Vertical_%s' %(index)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Vertical', index)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D vertical constraint to line %s' %(index), LOG.LOG_INFO)
		return

	def addSketch2D_Geometric_Horizontal2D(self, constraintNode, sketchObj):
		'''
		index: The index of the sketch object, that will change by applying the constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_HORIZONTAL == 0): return
		index = self.getGeometryIndex(sketchObj, constraintNode, 'refLine')
		if (index is None):
			logWarning('        ... skipped 2D horizontal constraint to line - line (%04X) has no index!' %(constraintNode.get('refLine').index))
		else:
			key = 'Horizontal_%s' %(index)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Horizontal', index)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D horizontal constraint to line %s' %(index), LOG.LOG_INFO)
		return

	def addSketch2D_Geometric_EqualLength2D(self, constraintNode, sketchObj):
		'''
		Create a  equal legnth constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_EQUAL_LENGTH == 0): return
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine2')
		if (index1 is None):
			logWarning('        ... skipped 2D equal length constraint between lines - line 1 (%04X) has no index!' %(constraintNode.get('refLine1').index))
		elif (index2 is None):
			logWarning('        ... skipped 2D equal length constraint between lines - line 2 (%04X) has no index!' %(constraintNode.get('refLine2').index))
		else:
			key = 'Equal_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Equal', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D equal length constraint between line %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch2D_Geometric_EqualRadius2D(self, constraintNode, sketchObj):
		'''
		Create a  equal radius constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_EQUAL_RADIUS == 0): return
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refCircle1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refCircle2')
		if (index1 is None):
			logWarning('        ... skipped 2D equal radius constraint between circles - circle 1 (%04X) has no index!' %(constraintNode.get('refCircle1').index))
		elif (index2 is None):
			logWarning('        ... skipped 2D equal radius constraint between circles - circle 2 (%04X) has no index!' %(constraintNode.get('refCircle2').index))
		else:
			key = 'Equal_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Equal', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D equal radius constraint between circle %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch2D_Point2D(self, pointNode, sketchObj):
		x = pointNode.get('x')
		y = pointNode.get('y')
		if ((x == 0) and (y == 0)):
			pointNode.setSketchEntity(-1, sketchObj.getPoint(-1, 1))
		else:
			pointNode.setSketchEntity(-2, None)
		return

	def addSketch3D_Point3D(self, pointNode, edges): return

	def removeFromPointRef(self, pointRef, index):
		key = calcPointKey(pointRef.node)
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
		lineNode.setValid(False)
		index = lineNode.index
		points = lineNode.get('points')
		self.removeFromPointRef(points[0], lineNode.index)
		self.removeFromPointRef(points[1], lineNode.index)

	def createLine2D(self, sketchObj, point1Ref, point2Ref, mode, lineNode):
		if (point1Ref):
			x1 = getX(point1Ref.node)
			y1 = getY(point1Ref.node)
		else:
			x1 = getX(lineNode)
			y1 = getY(lineNode)
		x2 = getX(point2Ref.node)
		y2 = getY(point2Ref.node)
		if(('%g'%x1 != '%g'%x2) or ('%g'%y1 != '%g'%y2)):
			part = Part.Line(createVector(x1, y1, 0), createVector(x2, y2, 0))
			addSketch2D(sketchObj, part, mode, lineNode)
			return True
		return False

	def createLine3D(self, edges, lineNode):
		points = lineNode.get('points')
		if (len(points) > 1):
			point1Data = points[0].node
			point2Data = points[1].node
			x1 = getX(point1Data)
			y1 = getY(point1Data)
			z1 = getY(point1Data)
			x2 = getX(point2Data)
			y2 = getY(point2Data)
			z2 = getY(point2Data)
			if(('%g'%x1 != '%g'%x2) or ('%g'%y1 != '%g'%y2) or ('%g'%z1 != '%g'%z2)):
				part = Part.Line(createVector(x1, y1, z1), createVector(x2, y2, z1))
				addSketch3D(edges, part, isConstructionMode(lineNode), lineNode)
				return True
		return False

	def addSketch2D_Line2D(self, lineNode, sketchObj):
		points = lineNode.get('points')
		mode = isConstructionMode(lineNode)
		if (self.createLine2D(sketchObj, points[0], points[1], mode, lineNode) == False):
			logWarning('        ... can\'t add Line with length = 0.0!')
			self.invalidateLine2D(lineNode)
		else:
			x1 = getX(lineNode)
			y1 = getY(lineNode)
			x2 = getX(points[1].node)
			y2 = getY(points[1].node)
			logMessage('        ... added Line (%g|%g)-(%g|%g) %r = %s' %(x1, y1, x2, y2, mode, lineNode.getSketchIndex()), LOG.LOG_INFO)
		return

	def addSketch3D_Line3D(self, lineNode, edges):
		points = lineNode.get('points')
		if (len(points) > 1):
			if (self.createLine3D(edges, lineNode) == False):
				logWarning('        ... can\'t add Line with length = 0.0!')
			else:
				x1 = getX(points[0].node)
				y1 = getY(points[0].node)
				z1 = getZ(points[0].node)
				x2 = getX(points[1].node)
				y2 = getY(points[1].node)
				z2 = getZ(points[1].node)
				logMessage('        ... added Line (%g|%g|%g)-(%g|%g|%g) %r' %(x1, y1, z1, x2, y2, z2, isConstructionMode(lineNode)), LOG.LOG_INFO)
		return

	def addSketch2D_Spline2D(self, splineNode, sketchObj):
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
			logMessage('        ... added 2D spline = %s' %(splineNode.getSketchIndex()), LOG.LOG_INFO)

		return

	def addSketch2D_Circle2D(self, circleNode, sketchObj):
		centerData = circleNode.get('refCenter').node
		x = getX(centerData)
		y = getY(centerData)
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
				point1Ref = points[j - 1]
				point2Ref = points[j]
				if (draw):
					a = calcAngle2D(centerData, point1Ref)
					b = calcAngle2D(centerData, point2Ref)
					radA = a.x
					radB = b.x
					arc = Part.ArcOfCircle(part, radA, radB)
					logMessage('        ... added Arc-Circle M=(%g/%g) R=%gmm, from %s to %s ...' %(x, y, r, degrees(radA), degrees(radB)), LOG.LOG_INFO)
					addSketch2D(sketchObj, arc, mode, circleNode)
					point1Ref.sketchPos = 1
					point2Ref.sketchPos = 2
					point1Ref.sketchIndex = circleNode.getSketchIndex()
					point2Ref.sketchIndex = point1Ref.sketchIndex
					arc2 = circleNode.getSketchIndex()
					addEqualRadius2d(sketchObj, arc1, arc2)
					arc1 = arc2
				if (self.getCirclePointRefs(sketchObj, point2Ref, circleNode.index) > 0):
					draw = not draw
				j += 1
		return

	def addSketch3D_Circle3D(self, circleNode, edges):
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
			angleStart = Angle(circleNode.get('startAngle'), pi/180.0, '\xC2\xB0')
			angleSweep = Angle(circleNode.get('sweepAngle'), pi/180.0, '\xC2\xB0')
			radA = angleStart.x
			radB = angleSweep.x
			arc = Part.ArcOfCircle(part, radA, radB)
			logMessage('        ... added Arc-Circle M=(%g/%g/%g) R=%gmm, from %s to %s ...' %(x, y, z, r, angleStart, angleSweep), LOG.LOG_INFO)
			addSketch3D(edges, arc, isConstructionMode(circleNode), circleNode)
		else:
			logMessage('        ... can\'t Arc-Circle more than 2 points - SKIPPED!' %(x, y, r, angleStart, angleSweep), LOG.LOG_INFO)
		return

	def addSketch2D_Ellipse2D(self, ellipseNode, sketchObj):
		centerData = ellipseNode.get('refCenter').node
		if (centerData.typeName == 'Circle2D'):
			#add 2D concentric constraint
			centerData = centerData.get('refCenter').node

		c_x = getX(centerData)
		c_y = getY(centerData)
		x = getCoord(ellipseNode, 'a')
		d = ellipseNode.get('dA')
		a_x = c_x + (x * d[0])
		a_y = c_y + (x * d[1])

		x = ellipseNode.get('b')
		b_x = c_x - (x * d[1])
		b_y = c_y + (x * d[0])

		vecA = createVector(a_x, a_y, 0.0)
		vecB = createVector(b_x, b_y, 0.0)
		vecC = createVector(c_x, c_y, 0.0)
		part = Part.Ellipse(vecA, vecB, vecC)

		a = ellipseNode.get('alpha')
		b = ellipseNode.get('beta')
		if ((a is None) and (b is None)):
			logMessage('        ... added 2D-Ellipse  c=(%g/%g) a=(%g/%g) b=(%g/%g) ...' %(c_x, c_y, a_x, a_y, b_x, b_y), LOG.LOG_INFO)
		else:
			a = Angle(a, pi/180.0, '\xC2\xB0')
			b = Angle(b, pi/180.0, '\xC2\xB0')
			logMessage('        ... added 2D-Arc-Ellipse  c=(%g/%g) a=(%g/%g) b=(%g/%g) from %s to %s ...' %(c_x, c_y, a_x, a_y, b_x, b_y, a, b), LOG.LOG_INFO)
			part = Part.ArcOfEllipse(part, a.getGRAD(), b.getGRAD())
		addSketch2D(sketchObj, part, isConstructionMode(ellipseNode), ellipseNode)
		return

	def addSketch3D_Ellipse3D(self, ellipseNode, edges):
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
			a = Angle(a, pi/180.0, '\xC2\xB0')
			b = Angle(b, pi/180.0, '\xC2\xB0')
			logMessage('        ... added 3D-Arc-Ellipse  c=(%g/%g/%g) a=(%g/%g/%g) b=(%g/%g/%g) from %s to %s ...' %(c_x, c_y, c_z, a_x, a_y, a_z, b_x, b_y, b_z, a, b), LOG.LOG_INFO)
			arc = Part.ArcOfEllipse(part, a.getGRAD(), b.getGRAD())
			addSketch3D(edges, arc, isConstructionMode(ellipseNode), ellipseNode)
		return

	def addSketch2D_Text2D(self, textNode, sketchObj): return notSupportedNode(textNode)

	def addSketch2D_Direction(self, directionNode, sketchObj):             return ignoreBranch(directionNode)
	def addSketch2D_Geometric_TextBox2D(self, frameNode, sketchObj):       return ignoreBranch(frameNode)
	def addSketch2D_Geometric_Radius2D(self, radiusNode, sketchObj):       return ignoreBranch(radiusNode)
	def addSketch2D_Geometric_SplineFitPoint2D(self, infoNode, sketchObj): return ignoreBranch(infoNode)
	def addSketch2D_Geometric_Offset2D(self, node, sketchObj):
		'''
		Create an offset constraint.
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_OFFSET == 0): return
		return
	def addSketch2D_Geometric_AlignHorizontal2D(self, node, sketchObj):
		'''
		Create an horizontal align constraint.
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_ALIGN_HORIZONTAL == 0): return
		return
	def addSketch2D_Geometric_AlignVertical2D(self, node, sketchObj):
		'''
		Create an vertical align constraint.
		'''
		if (SKIP_CONSTRAINS & SKIP_GEO_ALIGN_VERTICAL == 0): return
		return
	def addSketch2D_Transformation(self, transformationNode, sketchObj):   return ignoreBranch(transformationNode)
	def addSketch2D_String(self, stringNode, sketchObj):                   return ignoreBranch(stringNode)

	def addSketch2D_Arc2D(self, arcNode, sketchObj): return

	def addSketch2D_Dimension_Distance_Horizontal2D(self, dimensionNode, sketchObj):
		'''
		Create a horizontal dimension constraint
		'''
		self.addDistanceConstraint(sketchObj, dimensionNode, SKIP_DIM_DISTANCE_X, 'DistanceX', 'horizontal')
		return

	def addSketch2D_Dimension_Distance_Vertical2D(self, dimensionNode, sketchObj):
		'''
		Create a vertical dimension constraint
		'''
		self.addDistanceConstraint(sketchObj, dimensionNode, SKIP_DIM_DISTANCE_Y, 'DistanceY', 'vertical')
		return

	def addSketch2D_Dimension_Distance2D(self, dimensionNode, sketchObj):
		'''
		Create a distance constraint
		'''
		self.addDistanceConstraint(sketchObj, dimensionNode, SKIP_DIM_DISTANCE, 'Distance', '')
		return

	def addSketch2D_Dimension_Radius2D(self, dimensionNode, sketchObj):
		'''
		Create a radius constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_DIM_RADIUS == 0): return
		circleRef = getNode(dimensionNode, 'refCircle')
		index     = self.checkSketchIndex(sketchObj, circleRef)
		dimension = getDimension(dimensionNode, 'refParameter')
		if (index is None):
			logMessage('        ... skipped 2D radius = %s - circle (%04X) has no index!' %(dimension.getValue(), circleRef.index))
		else:
			key = 'Radius_%s' %(index)
			if (not key in self.mapConstraints):
				radius = circleRef.getSketchEntity().Radius
				constraint = Sketcher.Constraint('Radius',  index, radius)
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D radius \'%s\' = %s' %(constraint.Name, dimension.getValue()), LOG.LOG_INFO)
		return

	def addSketch2D_Dimension_Diameter2D(self, dimensionNode, sketchObj):
		'''
		Create a diameter (not available in FreeCAD) constraint
		Workaround: Radius and Center constraint.
		'''
		if (SKIP_CONSTRAINS & SKIP_DIM_DIAMETER == 0): return
		circleRef = getNode(dimensionNode, 'refCircle')
		index  = self.checkSketchIndex(sketchObj, circleRef)
		if (index is None):
			logMessage('        ... skipped 2D diameter \'%s\' = %s - circle (%04X) has no index!' %(constraint.Name, dimension.getValue(), circleRef.index))
		else:
			key = 'Diameter_%s' %(index)
			if (not key in self.mapConstraints):
				#TODO: add a 2D-construction-line, pin both ends to the circle, pin circle's center on this 2D-line and add dimension constraint to 2D-construction-line
				radius = circleRef.getSketchEntity().Radius
				constraint = Sketcher.Constraint('Radius',  index, radius)
				dimension = getDimension(dimensionNode, 'refParameter')
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key, False)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D diameter \'%s\' = %s (r = %s mm)' %(constraint.Name, dimension.getValue(), radius), LOG.LOG_INFO)
		return

	def addSketch2D_Dimension_Angle3Point2D(self, dimensionNode, sketchObj):
		'''
		Create an angle constraint between the three points.
		'''
		if (SKIP_CONSTRAINS & SKIP_DIM_ANGLE_3_POINT == 0): return
		pt1Ref = getNode(dimensionNode, 'refPoint1')
		pt2Ref = getNode(dimensionNode, 'refPoint2') # the center point
		pt3Ref = getNode(dimensionNode, 'refPoint3')
		return

	def addSketch2D_Dimension_Angle2Line2D(self,  dimensionNode, sketchObj):
		'''
		Create a angle constraint
		'''
		if (SKIP_CONSTRAINS & SKIP_DIM_ANGLE_2_LINE == 0): return
		line1Ref = getNode(dimensionNode, 'refLine1')
		line2Ref = getNode(dimensionNode, 'refLine2')
		index1 = self.checkSketchIndex(sketchObj, line1Ref)
		index2 = self.checkSketchIndex(sketchObj, line2Ref)

		if (index1 is None):
			logWarning('        ... skipped 2D dimension angle \'%s\' = %s - line 1 (%04X) has no index!' %(constraint.Name, dimension.getValue(), line1Ref.index))
		elif (index2 is None):
			logWarning('        ... skipped 2D dimension angle \'%s\' = %s - line 2 (%04X) has no index!' %(constraint.Name, dimension.getValue(), line2Ref.index))
		else:
			points1 = line1Ref.get('points')
			points2 = line2Ref.get('points')

			pt11 = points1[0].node
			pt12 = points1[1].node
			pt21 = points2[0].node
			pt22 = points2[1].node

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
				dimension = getDimension(dimensionNode, 'refParameter')
				angle = dimension.getValue()
				constraint = Sketcher.Constraint('Angle', index1, pos1, index2, pos2, angle.getRAD())
				index = self.addDimensionConstraint(sketchObj, dimension, constraint)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D dimension angle \'%s\' = %s' %(constraint.Name, dimension.getValue()), LOG.LOG_INFO)
		return

	def addSketch2D_Dimension_OffsetSpline2D(self, node, sketchObj):
		'''
		Create distnace contraint for an offset spline.
		'''
		if (SKIP_CONSTRAINS & SKIP_DIM_OFFSET_SPLINE == 0): return
		return

	def addSketch2D_OffsetSpline2D(self, node, sketchObj):
		'''
		Create an offset spline.
		'''
		return
	def addSketch2D_SplineHandle2D(self, splineHandleNode, sketchObj):
		'''
		Create a spline handle.
		'''
		return
	def addSketch3D_SplineHandle3D(self, splineHandleNode, edges): return

	def addSketch2D_ControlPointSpline2D(self, splineNode, sketchObj): return

	def addSketch2D_18A9717E(self, node, sketchObj): return
	def addSketch2D_4CF1124C(self, node, sketchObj): return
	def addSketch2D_5D8C859D(self, node, sketchObj): return
	def addSketch2D_8EC6B314(self, node, sketchObj): return
	def addSketch2D_8FEC335F(self, node, sketchObj): return
	def addSketch2D_A789EEB0(self, node, sketchObj): return
	def addSketch2D_B4964E90(self, node, sketchObj): return
	def addSketch2D_DC93DB08(self, node, sketchObj): return
	def addSketch2D_F2568DCF(self, node, sketchObj): return

	def Create_Sketch2D_Node(self, sketchObj, node):
		if (node.isHandled() == False):
			node.setHandled(True)
			name  = node.typeName
			index = node.index
			try:
				addSketchObj = getattr(self, 'addSketch2D_%s' %(name))
				addSketchObj(node, sketchObj)
			except Exception as e:
				logError('ERROR: (%04X): %s - %s' %(index, name, e))
				logError('>E: ' + traceback.format_exc())
		return

	def addSketch2D_PostCreateCoincidences(self, sketchObj):
		for key in self.pointDataDict.keys():
			entities = self.pointDataDict[key]
			l = len(entities)
			j = 2
			if (l > j):
				pointData = entities[0]
				fixData   = entities[1]
				fixIndex  = self.checkSketchIndex(sketchObj, fixData.node)
				fixPos    = findEntityVertex(fixData, pointData)
				fixName   = fixData.typeName
				fixIndex, fixPos = self.adjustIndexPos(fixData, fixIndex, fixPos, pointData)

				while (j < l):
					movData  = entities[j]
					constraint = self.addCoincidentConstraint(fixIndex, fixPos, fixName, movData, sketchObj, pointData)
					if (constraint):
						self.addConstraint(sketchObj, constraint, key)
					j += 1
		return

	def Create_Sketch2D(self, sketchNode):
		name = sketchNode.getName()
		sketchObj           = self.doc.addObject('Sketcher::SketchObject', name)
		transformationRef   = sketchNode.get('refTransformation')
		placement           = getPlacement(transformationRef.node)
		sketchObj.Placement = FreeCAD.Placement(placement)

		sketchNode.setSketchEntity(-1, sketchObj)

		logMessage('        adding 2D-Sketch \'%s\'...' %(name), LOG.LOG_INFO)

		# Clean up Points
		lst = sketchNode.get('entities')
		self.pointDataDict = {}
		for ref in lst:
			if (ref.node.typeName == 'Point2D'):
				self.addPoint2Dictionary(ref)

		for child in lst:
			self.Create_Sketch2D_Node(sketchObj, child.getBranchNode())

		self.addSketch2D_PostCreateCoincidences(sketchObj)

		if (self.root):
			self.root.addObject(sketchObj)

		self.pointDataDict = None

		return

	def Create_FxPad_New(self, padNode, sketchNode, name):
		properties = padNode.get('properties')
		direction  = getListNode(properties, 0x02)               # The direction of the extrusion
		reversed   = getListNode(properties, 0x03).get('value')  # If the extrusion direction is inverted
		dimLenRef  = getListNode(properties, 0x04)               # The length of the extrusion in direction 1
		dimAngle   = getListNode(properties, 0x05).node          # The taper outward angle  (doesn't work properly in FreeCAD)
		midplane   = getListNode(properties, 0x07).get('value')
		# The output is either solid (= True) or surface (=False)
		solid      = getListNode(properties, 0x1A)
		dimLen2Ref = getListNode(properties, 0x1B)               # The length of the extrusion in direction 2


		# Extents 1x distance, 2x distance, to, to next, between, all

		pad = None
		if (dimLenRef):
			sketchName = sketchNode.getName()
			sketch = sketchNode.getSketchEntity()
			dimLenNode = dimLenRef.node
			if (isinstance(dimLenNode, ParameterNode)):
				len1 = dimLenNode.getValue()
				alias = dimLenRef.get('alias')
				if (isinstance(len1, Length)):
					len1 = len1.getMM()
				else:
					len1 = len1 * 10.0
				x          = direction.get('x') * len1
				y          = direction.get('y') * len1
				z          = direction.get('z') * len1
				taperAngle = dimAngle.getValue()

				# pad = self.doc.addObject('Part::Extrusion', name)
				# pad.Base = sketch
				# pad.Dir = (x, y, z)
				# pad.Solid = solid is not None
				# pad.TaperAngle = taperAngle.getGRAD()
				# adjustViewObject(pad, sketch)

				pad = self.doc.addObject('PartDesign::Pad', name)
				pad.Sketch = sketch
				pad.UpToFace = None
				pad.Reversed = reversed
				pad.Midplane = midplane
				pad.Length = len1
				pad.setExpression('Length', dimLenNode.get('alias'))
				# Workaround with taperAngle: Add draft on outward face!?!

				if (dimLen2Ref):
					dimLen2Node = dimLen2Ref.node
					len2 = dimLen2Node.getValue()
					logMessage('        creating pad \'%s\' based on \'%s\' (rev=%s, sym=%s, len=%s, len2=%s) ...' %(name, sketchName, reversed, midplane, len1, len2), LOG.LOG_INFO)
					pad.Type = 4
					pad.Length2 = len2.getMM()
					pad.setExpression('Length2', dimLen2Node.get('alias'))
				else:
					logMessage('        creating pad \'%s\' based on \'%s\' (rev=%s, sym=%s, len=%s) ...' %(name, sketchName, reversed, midplane, len1), LOG.LOG_INFO)
					pad.Type = 0
					pad.Length2 = 0.0

				padNode.setSketchEntity(-1, pad)
			else:
				logWarning('        Failed create new extrusion \'%s\' - (%04X): %s properties[04] is not a parameter!' %(name, padNode.index, padNode.typeName))
		else:
			logWarning('        Failed create new extrusion \'%s\' - (%04X): %s properties[04] is None!' %(name, padNode.index, padNode.typeName))
		return pad

	def createBoolean(self, className, name, baseGeo, tools):
		booleanGeo = baseGeo
		if ((baseGeo is not None) and (len(tools) > 0)):
			booleanGeo = self.doc.addObject('Part::%s' %(className), name)
			if (className == 'Cut'):
				booleanGeo.baseGeo = baseGeo
				booleanGeo.Tool = tools[0]
			else:
				booleanGeo.Shapes = [baseGeo] + tools
			adjustViewObject(booleanGeo, baseGeo)
		return booleanGeo

	def createFxPad_Operation(self, padNode, sketchNode, name, nameExtension, className):
		properties = padNode.get('properties')
		baseData   = getListNode(properties, 0x1A)
		boolean    = None

		if (baseData is None):
			logError('ERROR> (%04X): %s - can\'t find base info!' %(padNode.index, name))
		else:
			tool = self.Create_FxPad_New(padNode, sketchNode, name + nameExtension)
			base    = self.findBase(baseData.node.next)
			if (base is not None):
				if (tool is not None): # no need to raise a warning as it's already done!
					boolean = self.createBoolean(className, name, base, [tool])
				else:
					logWarning('        FxExtrude \'%s\': can\'t find/create tools object - executing %s!' %(name, className))
			else:
				logWarning('        FxExtrude \'%s\': can\'t find/create base object - executing %s!' %(name, className))
		return boolean

	def Create_FxRevolve(self, revolveNode):
		label = revolveNode.get('label').node
		name = label.name
		refSketch = label.get('lst0')
		logMessage('    adding FxRevolve \'%s\' ...' %(name), LOG.LOG_INFO)
		revolution = None

		if (refSketch):
			refSketch = refSketch[0]
			sketchNode = refSketch.getBranchNode()
			if (sketchNode.getSketchEntity() is None):
				self.CreateObject(sketchNode)
			sketchName = sketchNode.getName()
			properties = revolveNode.get('properties')
			reversed = 0
			val3 = getPropertyValue(properties, 0x3, 'u16_0')
			x1 = getPropertyValue(properties, 0x2, 'x')
			y1 = getPropertyValue(properties, 0x2, 'y')
			z1 = getPropertyValue(properties, 0x2, 'z')
			dx = getPropertyValue(properties, 0x2, 'dirX')
			dy = getPropertyValue(properties, 0x2, 'dirY')
			dz = getPropertyValue(properties, 0x2, 'dirZ')
			lAxis = sqrt(dx*dx + dy*dy + dz*dz)
			val5 = getPropertyValue(properties, 0x5, 'u16_0')
			midplane =  IFF(val5 == 2, 1, 0)
			angle1   = getPropertyValue(properties, 0x4, 'valueNominal')

			if (angle1):
				sketch = sketchNode.getSketchEntity()
				alpha = Angle(angle1, pi/180.0, '\xC2\xB0')

				#revolution = self.doc.addObject('PartDesign::Revolution', name)
				#revolution.Sketch = sketch
				#revolution.Reversed = reversed

				revolution = self.doc.addObject('Part::Revolution', name)
				revolution.Source = sketch
				revolution.Axis = (dx/lAxis, dy/lAxis, dz/lAxis)
				revolution.Base = (x1 * 10, y1 * 10, z1 * 10)

				angle2   = getPropertyValue(properties, 0x12, 'valueNominal')
				if (angle2 is None):
					logMessage('        adding revolution \'%s\' (%s)-(%s) based on \'%s\' (rev=%s, sym=%s, alpha=%s) ...' %(name, revolution.Base, revolution.Axis, sketchName, reversed, midplane, alpha), LOG.LOG_INFO)
				else:
					beta = Angle(angle2, pi/180.0, '\xC2\xB0')
					midplane = True
					logMessage('        adding revolution \'%s\' based on \'%s\' (rev=%s, sym=%s, alpha=%s, beta=%s) #BUGGY#...' %(name, sketchName, reversed, midplane, alpha, beta), LOG.LOG_INFO)
					alpha.x += beta.x

				revolution.Angle = alpha.getGRAD()
				revolution.Solid = getListNode(properties, 0x11) is not None
				adjustViewObject(revolution, sketch)
				#revolution.Midplane = midplane

				revolveNode.setSketchEntity(-1, revolution)

				self.addBody(revolveNode, revolution, 0x11, 0x08)
		return revolution

	def Create_FxExtrude(self, extrudeNode):
		label = extrudeNode.get('label').node
		name = label.name
		refSketch = label.get('lst0')
		logMessage('    adding FxExtrusion \'%s\' ...' %(name), LOG.LOG_INFO)

		if (refSketch):
			refSketch = refSketch[0]
			sketchNode = refSketch.getBranchNode()
			if (sketchNode.getSketchEntity() is None):
				self.CreateObject(sketchNode)

			properties = extrudeNode.get('properties')
			typ = getListNode(properties, 0x02)
			obj3D = None
			if (typ):
				# Operation new (0x0001), cut/difference (0x002), join/union (0x003) intersection (0x0004) or surface(0x0005)
				properties = extrudeNode.get('properties')
				fxNode = getListNode(properties, 0x00)
				operation = fxNode.get('value')
				if (operation == FreeCADImporter.FX_EXTRUDE_NEW):
					padGeo = self.Create_FxPad_New(extrudeNode, sketchNode, name)
				elif (operation == FreeCADImporter.FX_EXTRUDE_CUT):
					padGeo = self.createFxPad_Operation(extrudeNode, sketchNode, name, '_Cut', 'Cut')
				elif (operation == FreeCADImporter.FX_EXTRUDE_JOIN):
					padGeo = self.createFxPad_Operation(extrudeNode, sketchNode, name, '_Join', 'MultiFuse')
				elif (operation == FreeCADImporter.FX_EXTRUDE_INTERSECTION):
					padGeo = self.createFxPad_Operation(extrudeNode, sketchNode, name, '_Intersection', 'MultiCommon')
				elif (operation == FreeCADImporter.FX_EXTRUDE_SURFACE):
					padGeo = self.Create_FxPad_New(extrudeNode, sketchNode, name) # FIXME: Use Part::Extrusion instead!
				else:
					padGeo = None
					logError('    ERROR Don\'t know how to operate PAD=%s for (%04X): %s ' %(operation, extrudeNode.index, extrudeNode.typeName))

				if (padGeo):
					self.addBody(extrudeNode, padGeo, 0x1A, 0x10)
					if (self.root):
						self.root.addObject(padGeo)
					adjustViewObject(padGeo, sketchNode.getSketchEntity())

	def Create_FxChamfer(self, chamferNode):
		#baseGeo = ???
		#chamferGeo = self.doc.addObject('Part::Chamfer', name)
		#chamferGeo.Base = baseGeo
		#edges = []
		#edges.append(????)
		#chamferGeo.Edges = edges
		#del edges
		#adjustViewObject(chamferGeo, baseGeo)
		return

	def Create_FxFilletConstant(self, filletNode):
		#baseGeo = filletNode.getSketchEntity()
		#filletGeo = self.doc.addObject('Part::Fillet', name)
		#filletGeo.Base = baseGeo
		#edges = []
		#edges.append(???)
		#filletGeo.Edges = edges
		#del edges
		#adjustViewObject(filletGeo, baseGeo)
		return

	def Create_FxFilletVariable(self, filletNode):
		#baseGeo = 
		#filletGeo = self.doc.addObject('Part::Fillet', name)
		#filletGeo.Base = baseGeo
		#edges = []
		#edges.append(???)
		#filletGeo.Edges = edges
		#del edges
		#adjustViewObject(filletGeo, baseGeo)
		return

	def Create_FxPatternCircular(self, patternNode):
		name       = patternNode.getName()
		properties = patternNode.get('properties')
		originals  = patternNode.get('lst1')
		fxDimData  = getListNode(properties, 0x05)
		solidRef   = properties[0x09]
		countRef   = getListNode(properties, 0x0C)
		angleRef   = getListNode(properties, 0x0D)
		axisData   = getListNode(properties, 0x0E)
		patternGeo  = None
		if (len(originals) > 0):
			geos  = []
			count = getNominalValue(countRef)
			lst0 = fxDimData.get('lst0')
			if ((lst0 is None) or len(lst0) < 1):
				logError('        FxPatternCircular \'%s\' - (%04X): %s has no lst0!' %(name, fxDimData.index, fxDimData.typeName))
			else:
				anchor = lst0[0].get('anchors')[0]
				angle = Angle(getNominalValue(angleRef), pi/180.0, '\xC2\xB0')
				center  = createVector(anchor[0] * 10.0, anchor[1] * 10.0, anchor[2] * 10.0)
				axis  = createVector(getX(axisData), getY(axisData), getZ(axisData))
				logMessage('    adding FxPatternPolar \'%s\' (count=%d, angle=%s) ...' %(name, count, angle), LOG.LOG_INFO)
				namePart = name
				for baseRef in originals:
					baseGeo = baseRef.getSketchEntity()
					if (baseGeo is None):
						baseGeo = self.findBase2(baseRef)
					else:
						logMessage('        .... Base = \'%s\'' %(baseRef.getName()), LOG.LOG_INFO)
					if (baseGeo is not None):
						patternGeo = Draft.makeArray(baseGeo, center, angle.getGRAD(), count, None, namePart)
						patternGeo.Axis = axis
						geos.append(patternGeo)
					namePart = '%s_%d' % (name, len(geos))
				if (len(geos) > 1):
					patternGeo = self.doc.addObject("Part::MultiFuse","Union")
					patternGeo.Shapes = geos
				if (patternGeo is not None):
					self.addSolidBody(patternNode, patternGeo, solidRef)
		return

	def Create_FxPatternRectangular(self, patternNode):
		name        = patternNode.getName()
		properties  = patternNode.get('properties')
		originals   = patternNode.get('lst1')
		offset = 0
		if (getFileVersion() > 2016):
			offset = 6
		solidRef    = properties[0x09 + offset]
		count1Ref   = properties[0x0C + offset]
		count2Ref   = properties[0x0D + offset]
		distanc1Ref = properties[0x0E + offset]
		distanc2Ref = properties[0x0F + offset]
		dir1Ref     = properties[0x10 + offset]
		dir2Ref     = properties[0x11 + offset]
		count2      = None
		dir2        = None
		patternGeo  = None
		if (len(originals) > 0):
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
			namePart = name
			for baseRef in originals:
				baseGeo = baseRef.getSketchEntity()
				if (baseGeo is None):
					baseGeo = self.findBase2(baseRef)
				else:
					logMessage('        .... Base = \'%s\'' %(baseRef.getName()), LOG.LOG_INFO)
				if (baseGeo is not None):
					patternGeo = Draft.makeArray(baseGeo, dir1, dir2, count1, count2, namePart)
					geos.append(patternGeo)
				namePart = '%s_%d' % (name, len(geos))
			if (len(geos) > 1):
				patternGeo = self.doc.addObject("Part::MultiFuse","Union")
				patternGeo.Shapes = geos
			if (patternGeo is not None):
				self.addSolidBody(patternNode, patternGeo, solidRef)
		return

	def Create_FxCombine(self, combineNode):
		name          = combineNode.getName()
		properties    = combineNode.get('properties')
		bodyRef       = properties[0x00]
		sourceData    = getListNode(properties, 0x01)
		operationData = getListNode(properties, 0x02)
		keepToolData  = getListNode(properties, 0x03) # not used
		operation = operationData.get('value')
		if (operation == FreeCADImporter.FX_EXTRUDE_CUT):
			className = 'Cut'
		elif (operation == FreeCADImporter.FX_EXTRUDE_JOIN):
			className = 'MultiFuse'
		elif (operation == FreeCADImporter.FX_EXTRUDE_INTERSECTION):
			className = 'MultiCommon'
		else:
			logWarning('        FxCombine: don\'t know how to \'%s\' - (%04X): %s!' %(operationData.node.getValueText(), combineNode.getIndex, combineNode.typeName))
			return
		logMessage('    adding FxCombin \'%s\': %s ...' %(name, className), LOG.LOG_INFO)
		baseGeo       = self.findBase2(bodyRef)
		toolGeos      = self.findGeometries(sourceData.node.next)
		if ((baseGeo is not None) and (len(toolGeos) > 0)):
			cmbineGeo = self.createBoolean(className, name, baseGeo, toolGeos)
			if (cmbineGeo is None):
				logError('        ....Failed to create combination!')
			else:
				self.addSolidBody(combineNode, cmbineGeo, bodyRef)
		return

	def Create_FxLoft(self, loftNode):
		name          = loftNode.getName()
		properties    = loftNode.get('properties')
		lofTypeData   = getListNode(properties, 0x0A)

		solid, sections = self.collectSection(loftNode, 'loft')

		if (len(sections) > 0):
			loftGeo          = self.doc.addObject('Part::Loft', name)
			loftGeo.Sections = sections
			loftGeo.Solid    = solid
			loftGeo.Ruled    = False
			loftGeo.Closed   = solid
			self.addBody(loftNode, loftGeo, 0x0D, 0x06)
		return

	def Create_FxSweep(self, sweepNode):
		name          = sweepNode.getName()
		properties    = sweepNode.get('properties')
		definitionRef = sweepNode.get('label')
		solid         = (definitionRef.typeName == 'Label')

		solid, sections = self.collectSection(sweepNode, 'sweep')

		if (len(sections) > 0):
			sweepGeo          = self.doc.addObject('Part::Sweep', name)
			sweepGeo.Sections = sections
			#sweepGeo.Spine    = (path, ["Edge1"])
			sweepGeo.Solid    = solid
			sweepGeo.Frenet   = False
			self.addBody(sweepNode, sweepGeo, 0x0F, 0x06)

		return
	
	def Create_FxMirror(self, mirrorNode):
		name          = mirrorNode.getName()
		defRef        = mirrorNode.get('label')
		properties    = mirrorNode.get('properties')
		planeRef      = properties[0x0C]
		b_x = getCoord(planeRef, 'b_x')
		b_y = getCoord(planeRef, 'b_y')
		b_z = getCoord(planeRef, 'b_z')
		n_x = getCoord(planeRef, 'n_x')
		n_y = getCoord(planeRef, 'n_y')
		n_z = getCoord(planeRef, 'n_z')
		logMessage('    adding FxMirror \'%s\' ...' %(name), LOG.LOG_INFO)

		mirrors = []
		mirrorGeo = None
		nameGeo = name
		for ref in defRef.get('lst0'):
			if (ref.getSketchEntity() is None):
				self.CreateObject(ref.getBranchNode())
			baseGeo = ref.getSketchEntity()
			if (baseGeo is not None):
				mirrorGeo = self.doc.addObject('Part::Mirroring', nameGeo)
				mirrorGeo.Source = baseGeo
				mirrorGeo.Base   = (b_x, b_y, b_z)
				mirrorGeo.Normal = (n_x, n_y, n_z)
				adjustViewObject(mirrorGeo, baseGeo)
				mirrors.append(mirrorGeo)
			nameGeo = '%s%d' %(name, len(mirrors))
		if (len(mirrors) > 1):
			mirrorGeo = self.createBoolean(className, name, mirrors[0], mirrors[1:])
			if (mirrorGeo is None):
				logError('        ....Failed to create combination!')
			else:
				self.addBody(mirrorNode, mirrorGeo, 0x09)
		elif (mirrorGeo):
			self.addBody(mirrorNode, mirrorGeo, 0x09)
				
		return

	def Create_FxDrill(self, drillNode):
		name          = drillNode.getName()
		defRef        = drillNode.get('label')
		properties    = drillNode.get('properties')
		holeType      = getListNode(properties, 0x00)
		drillDiam_1   = getListNode(properties, 0x01)
		drillDepth_1  = getListNode(properties, 0x02)
		drillDiam_2   = getListNode(properties, 0x03)
		drillDepth_2  = getListNode(properties, 0x04)
		sinkAngle     = getListNode(properties, 0x05)
		drillAngle    = getListNode(properties, 0x06)
		#    = getListNode(properties, 0x07)	# <=> placement == "by Sketch"
		transformation = getListNode(properties, 0x08)
		termination    = getListNode(properties, 0x09)
		#    = getListNode(properties, 0x0E)    # <=> termination = "To"
		#    = getListNode(properties, 0x0F)    # <=> termination = "To"
		direction     = getListNode(properties, 0x10)
		#    = getListNode(properties, 0x11)    # boolParam
		fxDimensions  = getListNode(properties, 0x13)
		threadDiam    = getListNode(properties, 0x14)
		#    = getListNode(properties, 0x15)	# <=> placement == "linear"
		
		drillGeo = None
		if (holeType is not None):
			if (holeType.get('value') == FreeCADImporter.FX_DRILL_DRILLED):
				# a) create cylinder with l=drillDepth_1 and D=drillDiam_1
				# b) cut it from body
			elif (holeType.get('value') == FreeCADImporter.FX_DRILL_SINK):
				# a) create cylinder with l=drillDepth_1 and D=drillDiam_1
				# b) create cone with R1=drillDiam_2/2, R2=0 and H=R1/sin(Angle/2)
				# c) cut them from body
			elif (holeType.get('value') == FreeCADImporter.FX_DRILL_BORED):
				# a) create cylinder 1 with l=drillDepth_1 and D=drillDiam_1
				# b) create cylinder 2 with l=drillDepth_2 and D=drillDiam_2
				# c) cut them from body
			elif (holeType.get('value') == FreeCADImporter.FX_DRILL_SPOT):
				# a) create cylinder 1 with l=drillDepth_1 and D=drillDiam_1
				# b) create cylinder 2 with l=drillDepth_2 and D=drillDiam_2
				# c) cut them from body
		
		self.addBody(drillNode, drillGeo, 0x18)

		return

	def Create_FxAliasFreeform(self, aliasFreeformNode):         return
	def Create_FxBend(self, bendNode):                           return
	def Create_FxBendCosmetic(self, bendNode):                   return
	def Create_FxBoss(self, bossNode):
		name = bossNode.getName()
		properties = bossNode.get('properties')
		# Sketch/dimension a circle on that face
		# then Extrude that circle
		# then create a hole in the center of that circle
		return
	def Create_FxBoundaryPatch(self, boundaryPatchNode):         return
	def Create_FxClient(self, clientNode):                       return
	def Create_FxCoil(self, coilNode):                           return
	def Create_FxContourRoll(self, contourRollNode):             return
	def Create_FxCoreCavity(self, coreCavityNode):               return
	def Create_FxCorner(self, cornerNode):                       return
	def Create_FxCornerChamfer(self, cornerNode):                return
	def Create_FxCornerRound(self, cornerNode):                  return
	def Create_FxCut(self, cutNode):                             return
	def Create_FxDecal(self, decalNode):                         return
	def Create_FxDeleteFace(self, deleteFaceNode):               return
	def Create_FxDirectEdit(self, directEditNode):               return
	def Create_FxEmboss(self, embossNode):                       return
	def Create_FxExtend(self, extendNode):                       return
	def Create_FxFace(self, faceNode):                           return
	def Create_FxFaceDraft(self, faceDraftNode):                 return
	def Create_FxFaceOffset(self, faceOffsetNode):               return
	def Create_FxFillet(self, filletNode):                       return
	def Create_FxFilletRule(self, filletNode):                   return
	def Create_FxFlange(self, flangeNode):                       return
	def Create_FxFlangeContour(self, flangeNode):                return
	def Create_FxFlangeLofted(self, flangeNode):                 return
	def Create_FxFold(self, foldNode):                           return
	def Create_FxFreeform(self, freeformNode):                   return
	def Create_FxGrill(self, grillNode):                         return
	def Create_FxHem(self, hemNode):                             return
	def Create_FxHole(self, holeNode):                           return
	def Create_FxiFeature(self, iFeatureNode):                   return
	def Create_FxKnit(self, knitNode):                           return
	def Create_FxLip(self, lipNode):                             return
	def Create_FxMesh(self, meshNode):                           return
	def Create_FxMidSurface(self, midSurfaceNode):               return
	def Create_FxMove(self, moveNode):                           return
	def Create_FxMoveFace(self, moveFaceNode):                   return
	def Create_FxNonParametricBase(self, nonParametricBaseNode): return
	def Create_FxPatternSketchDriven(self, patternNode):         return
	def Create_FxPresentationMesh(self, presentationMeshNode):   return
	def Create_FxPunchTool(self, punchToolNode):                 return
	def Create_FxReference(self, referenceNode):                 return
	def Create_FxRefold(self, refoldNode):                       return
	def Create_FxReplaceFace(self, replaceFaceNode):             return
	def Create_FxRest(self, restNode):                           return
	def Create_FxRib(self, ribNode):                             return
	def Create_FxRip(self, ripNode):                             return
	def Create_FxRuledSurface(self, ruledSurfaceNode):           return
	def Create_FxSculpt(self, sculptNode):                       return
	def Create_FxShell(self, shellNode):                         return
	def Create_FxSnapFit(self, snapFitNode):                     return
	def Create_FxSplit(self, splitNode):                         return
	def Create_FxThicken(self, thickenNode):                     return
	def Create_FxThread(self, threadNode):                       return notSupportedNode(threadNode) # https://www.freecadweb.org/wiki/Thread_for_Screw_Tutorial/de
	def Create_FxTrim(self, trimNode):                           return
	def Create_FxUnfold(self, unfoldNode):                       return
	def Create_FxUnknown(self, unknownNode):
		logError('   Can\'t process unknown Feature \'%s\' - probably an unsupported iFeature!' %(unknownNode.getName()))
		return

	def Create_Feature(self, featureNode):
		if (featureNode.isHandled() == False):
			featureNode.setHandled(True)
			name  = featureNode.getSubTypeName()
			index = featureNode.index
			try:
				createFxObj = getattr(self, 'Create_Fx%s' %(name))
				createFxObj(featureNode)
			except Exception as e:
				logError('ERROR: (%04X): %s - %s' %(index, name, e))
				logError('>E: ' + traceback.format_exc())
		return

	def addSketch3D_Spline3D_Curve(self, bezierNode, edges):
		points=[]
		for entity in bezierNode.get('entities'):
			if (entity.typeName == 'Point3D'):
				p = entity.node
				points.append(createVector(getX(p), getY(p), getZ(p)))
		if (len(points) > 2):
			pass
			#bezier = Part.BezierCurve()
			#bezier.setPoles(points)
			#addSketch3D(edges, part, isConstructionMode(bezierNode), bezierNode)
		else:
			logError('ERROR> Bezier requires at least 3 points - found only %d!' %(len(points)))
		return

	def addSketch3D_BSpline3D(self, bsplineNode, edges):
		points=[]
		for p in bsplineNode.get('points'):
			points.append(createVector(getX(p.node), getY(p.node), getZ(p.node)))

		bspline = Part.BSplineCurve()
		bspline.interpolate(points, False)
		addSketch3D(edges, bspline, isConstructionMode(bsplineNode), bsplineNode)
		return

	def addSketch3D_Bezier3D(self, bezierNode, edges):
		# handled together with either Spline3D_Curve or BSpline3D
		return

	def addSketch3D_Plane(self, lineNode, edges):                          return
	def addSketch3D_Spline3D_Fixed(self, splineNode, edges):               return
	def addSketch3D_Spiral3D_Curve(self, spiralNode, edges):               return

	def addSketch3D_Dimension_Length3D(self, dimensionNode, edges):        return notSupportedNode(dimensionNode)
	def addSketch3D_Dimension_Angle2Planes3D(self, dimensionNode, edges):  return notSupportedNode(dimensionNode)

	def addSketch3D_Geometric_Bend3D(self, geometricNode, edges):          return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Custom3D(self, geometricNode, edges):        return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Coincident3D(self, geometricNode, edges):    return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Collinear3D(self, geometricNode, edges):     return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Helical3D(self, geometricNode, edges):       return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Horizontal3D(self, geometricNode, edges):    return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Smooth3D(self, geometricNode, edges):        return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Parallel3D(self, geometricNode, edges):      return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Perpendicular3D(self, geometricNode, edges): return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Radius3D(self, geometricNode, edges):        return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Tangential3D(self, geometricNode, edges):    return notSupportedNode(geometricNode)
	def addSketch3D_Geometric_Vertical3D(self, geometricNode, edges):      return notSupportedNode(geometricNode)

	def addSketch3D_4F240E1C(self, node, edges): return

	def Create_Sketch3D(self, sketchNode):
		# Workaround: Create a Part.Feature from wires => not editable afterwards :(
		edges = []
		# for each entity in entities:
		#     edges.append(entityObj)
		# Wire=Group.newObject('Part::Feature', 'Wire')
		# # add objects with the shape
		# W=Part.Wire(edges)
		# sketchObj.Shape=W

		name = sketchNode.getName()
		logMessage('       adding 3D-Sketch \'%s\'...' %(name), LOG.LOG_INFO)
		sketchObj = self.doc.addObject('Part::Feature', name)
		if (self.root):
			self.root.addObject(sketchObj)

		for ref in sketchNode.get('entities'):
			child = ref.getBranchNode()
			if (child.isHandled() == False):
				try:
					addSketchObj = getattr(self, 'addSketch3D_%s' %(child.typeName))
					addSketchObj(child, edges)
				except AttributeError as e:
					logError('Warning: Don\'t know how to add %s to 3D sketch - %s'  %(child.typeName, e))
					logError('>E: ' + traceback.format_exc())
				except:
					logError('>E: ' + traceback.format_exc())
			child.setHandled(True)
			child = child.next
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
			child.setHandled(True)
			child = child.next

		return

	def Create_Line3D(self, lineNode):
		self.addSketch3D_Line3D(lineNode, None)

	def Create_Plane(self, planeNode):
		return notSupportedNode(planeNode)
#		name = planeNode.getName()
#		plane = self.doc.addObject('Part::Plane', name)
#		l = 10.0
#		w = 10.0
#		x = 0.0
#		y = 0.0
#		z = 0.0
#		plane.Length = l
#		plane.Width = w
#		plane.Placement = FreeCAD.Placement(createVector(x, y, z), createRotation(createVector(0, 0, 1), 45))
#		if (self.root):
#			self.root.addObject(plane)
#
#		return

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
			return '; D%d=\'%s\'' %(r, tolerance)
		return ''

	def addParameterTableComment(self, table, r, commentRef):
		if (commentRef):
			comment = commentRef.getName()
			if (comment):
				table.set('E%d' %(r), comment)
				return '; E%d=\'%s\'' %(r, comment)
		return ''

	def addOperandParameter(self, table, nextRow, parameterRefs, operandRef):
		if (operandRef):
			return self.addReferencedParameters(table, nextRow, parameterRefs, operandRef.getBranchNode())
		return nextRow

	def addReferencedParameters(self, table, r, parameterRefs, valueNode):
		nextRow = r
		typeName   = valueNode.typeName

		if (typeName == 'ParameterRef'):
			parameterData = valueNode.get('refParameter').node
			nextRow = self.addParameterToTable(table, nextRow, parameterRefs, parameterData.name)
		elif (typeName.startswith('ParameterOperation')):
			nextRow = self.addOperandParameter(table, nextRow, parameterRefs, valueNode.get('refOperand1'))
			nextRow = self.addOperandParameter(table, nextRow, parameterRefs, valueNode.get('refOperand2'))
		elif (typeName == 'ParameterValue'):
			pass # Nothing to do here!
		else:
			valueRef = valueNode.get('refValue')
			if (valueRef):
				valueData = valueRef.node
				typeName   = valueData.typeName

				if (typeName == 'ParameterUnaryMinus'):
					nextRow = self.addReferencedParameters(table, nextRow, parameterRefs, valueData.node)
				elif (typeName == 'ParameterRef'):
					parameterData = valueData.get('refParameter').node
					nextRow = self.addParameterToTable(table, nextRow, parameterRefs, parameterData.name)
				elif (typeName == 'ParameterFunction'):
					operandRefs = valueData.get('operands')
					j = 0
					sep = '('
					n = len(operandRefs)
					if (n > 0):
						while (j < n):
							nextRow = self.addReferencedParameters(table, nextRow, parameterRefs, operandRefs[j].getBranchNode())
							j += 1
				elif (typeName.startswith('ParameterOperation')):
					nextRow = self.addOperandParameter(table, nextRow, parameterRefs, valueData.get('refOperand1'))
					nextRow = self.addOperandParameter(table, nextRow, parameterRefs, valueData.get('refOperand2'))
				elif (typeName == 'ParameterOperationPowerIdent'):
					nextRow = self.addReferencedParameters(table, nextRow, parameterRefs, valueData.get('refOperand1').getBranchNode())
		return nextRow

	def addParameterToTable(self, table, r, parameterRefs, key):
		if (key in parameterRefs):
			valueNode = parameterRefs[key].getBranchNode()

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
				mdlValue = ''
				tlrValue = ''
				remValue = ''
				valueNode.setVariable('alias', 'T_Parameters.%s_' %(key))
				typeName = valueNode.typeName

				if (typeName == 'Parameter'):
					key = '%s' %(key)

					r = self.addReferencedParameters(table, r, parameterRefs, valueNode)
					#nominalValue = getNominalValue(valueNode)
					#nominalFactor = valueNode.data.getUnitFactor()
					#nominalOffset = valueNode.data.getUnitOffset()
					#nominalUnit  = valueNode.data.getUnitName()
					#if (len(nominalUnit) > 0): nominalUnit = ' ' + nominalUnit
					#formula = '%s%s' %((nominalValue / nominalFactor)  - nominalOffset, nominalUnit)
					value   = valueNode.getFormula(False).replace(':', '_')
					formula = valueNode.getFormula(True)
					table.set('A%d' %(r), '%s' %(key))
					table.set('B%d' %(r), '%s' %(value))
					table.set('C%d' %(r), '%s' %(formula))
					mdlValue = '; C%s=%s' %(r, formula)
					tlrValue = self.addParameterTableTolerance(table, r, valueNode.get('tolerance'))
					remValue = self.addParameterTableComment(table, r, valueNode.get('label'))
				elif (typeName == 'ParameterText'):
					key = '%s' %(key)
					value = valueNode.get('value')
					table.set('A%d' %(r), '%s' %(key))
					table.set('B%d' %(r), '\'%s' %(value))
					remValue = self.addParameterTableComment(table, r, valueNode.get('label'))
				elif (typeName == 'ParameterBoolean'):
					key = '%s' %(key)
					value = valueNode.get('value')
					table.set('A%d' %(r), '%s' %(key))
					table.set('B%d' %(r), '%s' %(value))
					remValue = self.addParameterTableComment(table, r, valueNode.get('label'))
				else: #if (key.find('RDxVar') != 0):
					value = valueNode
					table.set('A%d' %(r), '%s' %(key))
					table.set('B%d' %(r), '%s' %(value))
					remValue = self.addParameterTableComment(table, r, valueNode.get('label'))

				if (key.find('RDxVar') != 0):
					try:
						aliasValue = '%s_' %(key.replace(':', '_'))
						table.setAlias('B%d' %(r), aliasValue)
					except Exception as e:
						logError('    >ERROR: Can\'t set alias name for B%d - invalid name \'%s\'!' %(r, aliasValue))
					logMessage('        A%d=\'%s\'; B%d=\'%s\'%s\'%s%s' %(r, key, r, value, mdlValue, tlrValue, remValue), LOG.LOG_INFO)
					return r + 1
		else:
			assert False, 'ERROR: %s not found in parameterRefs!' %(key)
		return r

	def createParameterTable(self, partNode):
		parameterRefs = partNode.get('parameters')
		table = self.doc.addObject('Spreadsheet::Sheet', 'T_Parameters')
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
				label = root.get('label').node
				self.createParameterTable(root.get('refElements').getBranchNode())
				lst = label.get('lst0')
				for ref in lst:
					child = ref.getBranchNode()
					if (child):
						self.CreateObject(child)

				if (self.doc):
					self.doc.recompute()
			else:
				logWarning('>>>No content to be displayed<<<')

		return
