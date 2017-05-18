#!/usr/bin/env python

'''
importerFreeCAD.py
'''
import Draft
import Part
import Sketcher
import FreeCAD
import traceback
from importerUtils   import logMessage, logWarning, logError, LOG, IFF
from importerClasses import RSeMetaData, Angle, Length, DimensionNode, DimensionValue, FeatureNode
from math            import sqrt, acos, atan2, degrees

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.2'
__status__      = 'In-Development'

def ignoreBranch(node):
	return None

def notSupportedNode(node):
	return None

def getOrientationCode(sketch):
	orientation = sketch.getVariable('refOrientation').node
	a0 = 0
	if (orientation):
		a0 = orientation.get('CodedFloat.a0')
		a0 = a0[1] << 16 | a0[0]
	return a0

def isXYPlane(sketch):
	orientation = getOrientationCode(sketch)
	return (orientation == 0x7DEB8214)

def isXZPlane(sketch):
	orientation = getOrientationCode(sketch)
	return (orientation == 0x7DBF8241)

def isYZPlane(sketch):
	orientation = getOrientationCode(sketch)
	return (orientation == 0x7BDE8421)

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
		var = node.getVariable('s32_0')
		if (var):
			if ((var & 0x80000) > 0):
				return True
	return False

def calcAngle2D(p1, ref2):
	p2 = None
	if (p1):
		if (ref2):
			p2 = ref2.node
			if ((p1 is not None) and (p2 is not None)):
				x1 = p1.getVariable('x')
				y1 = p1.getVariable('y')
				x2 = p2.get('x')
				y2 = p2.get('y')

				dx = (x2 - x1)
				dy = (y2 - y1)
				angle = atan2(dy, dx)
				return Angle(angle)
	return None

def calcAngle3D(x1, y1, z1, x2, y2, z2):
	s = (x1*x2 + y1*y2 + z1*z2)
	l1 = sqrt(x1*x1 + y1*y1 + z1*z1)
	l2 = sqrt(x2*x2 + y2*y2 + z2*z2)
	if ((l1 != 0) and (l2 != 0)):
		angle = acos(s/l1/l2)
	else:
		angle = Angle.grad2rad(90.0)
	return Angle(angle)

def getX(p):
	if (p):
		if hasattr(p, 'X'):
			return p.X
		return p.x
	return 0.0

def getY(p):
	if (p):
		if hasattr(p, 'Y'):
			return p.Y
		return p.y
	return 0.0

def getZ(p):
	if (p):
		if hasattr(p, 'Z'):
			return p.Z
		return p.z
	return 0.0

def getDistanceX(p, q):
	return getX(q) - getX(p)

def getDistanceY(p, q):
	return getY(q) - getY(p)

def getDistancePointPoint(p, q):
	dx = getDistanceX(p, q)
	dy = getDistanceY(p, q)
	return sqrt(dx*dx + dy*dy)

def getDistanceLinePoint(line, a):
	p = line.StartPoint
	q = line.EndPoint
	# Adjust vectors relative to P
	# Q becomes relative vector from P to end of segment
	qx = getDistanceX(p, q)
	qy = getDistanceY(p, q)
	# A becomes relative vector from P to test point
	ax = getDistanceX(p, a)
	ay = getDistanceY(p, a)
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
	distance = getDistanceLinePoint(line, circle.Center)
	return distance - circle.Radius

def getDistanceCirclePoint(circle, p):
	distance = getDistancePointPoint(circle.Center, p)
	return distance - circle.Radius

def getDistanceCircleCircle(circle1, circle2):
	distance = getDistancePointPoint(circle1.Center, circle2.Center)
	return distance - circle1.Radius - circle2.Radius

def getLengthPoints(node1, node2):
	entity1 = node1.getSketchEntity()
	entity2 = node2.getSketchEntity()
	if (node1.getTypeName() == 'Point2D'):
		if (node2.getTypeName() == 'Point2D'):
			return getDistancePointPoint(entity1, entity2)
		if (node2.getTypeName() == 'Line2D'):
			return getDistanceLinePoint(entity2, entity1)
		if (node2.getTypeName() == 'Circle2D'):
			return getDistanceCirclePoint(entity2, entity1)
	if (node1.getTypeName() == 'Line2D'):
		if (node2.getTypeName() == 'Point2D'):
			return getDistanceLinePoint(entity1, entity2)
		if (node2.getTypeName() == 'Line2D'):
			# Hope that the lines are parallel!
			return getDistanceLinePoint(entity1, entity2.StartPoint)
		if (node2.getTypeName() == 'Circle2D'):
			return getDistanceCircleLine(entity2, entity1)
	if (node1.getTypeName() == 'Circle2D'):
		if (node2.getTypeName() == 'Point2D'):
			return getDistanceCirclePoint(entity1, entity2)
		if (node2.getTypeName() == 'Line2D'):
			# Hope that the lines are parallel!
			return getDistanceCircleLine(entity1, entity2)
		if (node2.getTypeName() == 'Circle2D'):
			return getDistanceCircleCircle(entity1, entity2)
	raise BaseException('Don\'t know how to determine the distance between \'%s\' and \'%s\'!' %(node1.getTypeName(), node2.getTypeName()))

def getLengthLine(lineNode):
	point1 = lineNode.getVariable('points')[0].node
	point2 = lineNode.getVariable('points')[1].node
	return getLengthPoints(point1.node, point2.node)

def addSketch2D(sketchObj, geometrie, mode, entityNode):
	index = sketchObj.addGeometry(geometrie, mode)
	entityNode.setSketchEntity(index, geometrie)
	return geometrie

def getNode(sourceNode, varName):
	if (sourceNode):
		ref = sourceNode.getVariable(varName)
		if (ref):
			return ref.getBranchNode()
	return None

def getRefPoint(node):
	point = getNode(node, 'refPoint')
	while (point.getTypeName() == 'Circle2D'):
		point = getNode(point, 'refCenter')
	assert point.getTypeName() == 'Point2D', 'Referenced Point: Point2D <> %s!' %(point.getTypeName())
	return point

def findEntityVertex(entityNode, fixNode):
	idxFix = fixNode.getIndex()
	points = entityNode.getVariable('points')
	i = 0
	while (i < len(points)):
		point = points[i]
		if ((point) and (point.index == idxFix)):
			return i + 1
		i += 1
	return -1

def getNodeName(node):
	label = node.getVariable('label')
	if (label):
		return label.node.name
	return ''

def getDistance(pt1, pt2):
	x1 = pt1.get('x')
	y1 = pt1.get('y')
	x2 = pt2.get('x')
	y2 = pt2.get('y')
	dx = (x2 - x1)
	dy = (y2 - y1)
	return sqrt((dx*dx) + (dy*dy))

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

	if (dimension.getTypeName() == 'Line2D'):
		dimension = DimensionValue(Length(getLengthLine(dimension)))
	elif (dimension.getTypeName() == 'Point2D'):
		dimension = DimensionValue(Length(0))

	if (dimension.getTypeName() != 'Dimension'):
		logError('Expected Dimension for (%04X): %s - NOT %s' %(node.getIndex(), node.getTypeName(), dimension.getTypeName()))

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

def getOrigin(placementNode):
	if (placementNode.getTypeName() == 'Sketch2DPlacementPlane'):
		plane  = placementNode.getVariable('refPlane').node
		origin = plane.get('origin')
		return createVector(origin[0] * 10.0, origin[1] * 10.0, origin[2] * 10.0)
	elif (placementNode.getTypeName() == 'Sketch2DPlacement'):
		ref = placementNode.getVariable('refPoint')
		if (ref):
			point = ref.node
			return createVector(point.get('x') * 10.0, point.get('y') * 10.0, point.get('z') * 10.0)
	logWarning('WARNING - don\'t know where to place (%04X): %s - setting to (0,0,0)!' %(placementNode.getIndex(), placementNode.getTypeName()))
	return createVector(0.0, 0.0, 0.0)

class FreeCADImporter:

	def __init__(self, root, doc):
		self.root      = root
		self.doc       = doc
		self.mapConstraints = None

	def checkSketchIndex(self, sketchObj, node):
		if (node.isHandled() == False):
			if (node.getTypeName() == 'Circle2D'):
				radius = node.getVariable('refRadius')
				if (radius):
					node = node.getVariable('refRadius').getBranchNode()
			self.Create_Sketch2D_Node(sketchObj, node)
			if (node.getSketchIndex() is not None):
				logError('    ... Failed to create (%04X): %s' %(node.getIndex(), node.getTypeName()))
		return  node.getSketchIndex()

	def addConstraint(self, sketchObj, constraint, key):
		index = sketchObj.addConstraint(constraint)
		self.mapConstraints[key] = constraint
		return index

	def addDimensionConstraint(self, sketchObj, dimension, constraint, key):
		index = self.addConstraint(sketchObj, constraint, key)
		if (len(dimension.getName()) > 0):
			constraint.Name = dimension.getName()
			sketchObj.renameConstraint(index, dimension.getName())
		else:
			constraint.Name = 'Constraint%d' %(index)
		return index

	def getGeometryIndex(self, sketchObj, node, varName):
		target = getNode(node, varName)
		return self.checkSketchIndex(sketchObj, target)

	def fix2D(self, sketchObj, point):
		key = 'Fix_%X' %(point.getIndex())
		if (not key in self.mapConstraints):
			x = getX(point.getSketchEntity())
			y = getY(point.getSketchEntity())
			index  = self.checkSketchIndex(sketchObj, point)
			if (index is not None):
				constraintX = Sketcher.Constraint('DistanceX', index, 1, x)
				constraintY = Sketcher.Constraint('DistanceY', index, 1, y)
				indexX = self.addConstraint(sketchObj, constraintX, key)
				indexY = self.addConstraint(sketchObj, constraintY, key)
				logMessage('        ... added 2D horizontal distance to %s %s' %(point.getSketchEntity().Name, indexX), LOG.LOG_INFO)
				logMessage('        ... added 2D vertical distance to %s %s' %(point.getSketchEntity().Name, indexY), LOG.LOG_INFO)
		return

########################
	def addSketch2D_Constraint_Fix2D(self, constraintNode, sketchObj):
		'''
		A fix constraint doesn't exists in FreeCAD.
		Workaround: two distance constraints (X and Y)
		'''
		ref   = getNode(constraintNode, 'refPoint')
		if (ref.getTypeName() == 'Line2D'):
			self.fix2D(sketchObj, ref.getVariable('points')[0].getBranchNode())
			self.fix2D(sketchObj, ref.getVariable('points')[1].getBranchNode())
		else:
			point = getRefPoint(constraintNode)
			self.fix2D(sketchObj, point)
		return

	def addSketch2D_Constraint_PolygonCenter2D(self, constraintNode, sketchObj): return

	def addSketch2D_Constraint_Coincident2D(self, constraintNode, sketchObj):
		'''
		idxFix: The index of the sketch object, that will not change by applying the constraint
		idxMov: The index of the sketch object, that will change by applying the constraint
		vtxMov: The number of the vertex (1..n) of sketch object, that has to fulfilled the constraint
		'''
		point    = getNode(constraintNode, 'refPoint')
		moving = getNode(constraintNode, 'refObject')

		if (point.getTypeName() != 'Point2D'):
			point  = getNode(constraintNode, 'refObject')
			moving = getNode(constraintNode, 'refPoint')

		index1 =  self.checkSketchIndex(sketchObj, point)
		index2 =  self.checkSketchIndex(sketchObj, moving)

		if (point.getTypeName() == 'Point2D'):
			pos = -1
#			if (moving.getTypeName() == 'Point2D'):
#				pos = 1
#			elif (moving.getTypeName() == 'Line2D'):
#				pos = findEntityVertex(moving, point)
#			elif (moving.getTypeName() == 'Spline2D'):
#				pos = findEntityVertex(moving, point)
#			elif (moving.getTypeName() == 'Circle2D'):
#				pos = findEntityVertex(moving, point)
#			elif (moving.getTypeName() == 'Ellipse2D'):
#				pos = findEntityVertex(moving, point)
#			else:
#				# Leads to redundant constraints!
#				# Workaround: if point2d has coincidens
#				return

			if (pos != -1):
				key = 'Coincident_%s_%s_%s' %(index1, pos, index2)
				if (not key in self.mapConstraints):
					constraint = Sketcher.Constraint('Coincident', index1, 1, index2, pos)
					index = self.addConstraint(sketchObj, constraint, key)
					constraintNode.setSketchEntity(index, constraint)
					logMessage('        ... added 2D coincident constraint between Point %s and %s %s' %(index2, moving.getTypeName()[0:-2], index1), LOG.LOG_INFO)
					return
#		elif (moving.getTypeName() == 'Point2D'):
#			key = 'PointOnObject_%s_%s' %(index1, index2)
#			if (not key in self.mapConstraints):
#				constraint = Sketcher.Constraint('PointOnObject', index1, 1, index2)
#				index = self.addConstraint(sketchObj, constraint, key)
#				constraintNode.setSketchEntity(index, constraint)
#				logMessage('        ... added 2D point on object constraint between Point %s and %s %s)' %(index2, moving.getTypeName()[0:-2], index1), LOG.LOG_INFO)
#				return
		else:
			logError('        ... (%04X) Constraint_Coincident2D: between %s (%04X) and %s (%04X) failed!!!' %(constraintNode.getIndex(), point.getTypeName(), point.getIndex(), moving.getTypeName(), moving.getIndex()))
		return

	def addSketch2D_Constraint_SymmetryPoint2D(self, constraintNode, sketchObj):
		point    = getRefPoint(constraintNode)
		idxSymmetry =  self.checkSketchIndex(sketchObj, point)

		moving = getNode(constraintNode, 'refObject')
		indexLine =  self.checkSketchIndex(sketchObj, moving)

		if ((indexLine is not None) and (idxSymmetry is not None)):
			key = 'SymmetryPoint_%s_%s' %(indexLine, idxSymmetry)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Symmetric', indexLine, 1, indexLine, 2, idxSymmetry, 1)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D symmetric constraint between Point %s and %s %s' %(idxSymmetry, moving.getTypeName()[0:-2], indexLine), LOG.LOG_INFO)
		return

	def addSketch2D_Constraint_SymmetryLine2D(self, constraintNode, sketchObj):
		symmetry    = getNode(constraintNode, 'refLineSym')
		idxSymmetry =  self.checkSketchIndex(sketchObj, symmetry)

		line1 = getNode(constraintNode, 'refLine1')
		indexLine1 =  self.checkSketchIndex(sketchObj, line1)

		line2 = getNode(constraintNode, 'refLine2')
		indexLine2 =  self.checkSketchIndex(sketchObj, line2)

		if ((idxSymmetry is not None) and (indexLine1 is not None) and (indexLine2 is not None)):
			key = 'SymmetricLine_%s_%s_%s' %(indexLine1, indexLine2, idxSymmetry)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Symmetric',indexLine1, 1, indexLine2, 1, idxSymmetry)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D symmetric constraint between lines %s, %s and %s' %(idxSymmetry, indexLine1, indexLine2), LOG.LOG_INFO)
		return

	def addSketch2D_Constraint_Parallel2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine2')
		if ((index1 is not None) and (index2 is not None)):
			key = 'Parallel_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Parallel', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D parallel constraint between lines %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch2D_Constraint_Perpendicular2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idxMov: The index of the sketch object, that will change by applying the constraint
		'''
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refLine2')
		if ((index1 is not None) and (index2 is not None)):
			key = 'Perpendicular_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Perpendicular', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D perpendicular constraint between lines %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch2D_Constraint_Colinear2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		line1 = getNode(constraintNode, 'refLine1')
		line2 = getNode(constraintNode, 'refLine2')
		index1 = self.checkSketchIndex(sketchObj, line1)
		index2 = self.checkSketchIndex(sketchObj, line2)
		if ((index1 is not None) and (index2 is not None)):
			key = 'Colinear_%s_%s' %(index1, index2)
			#if (not key in self.mapConstraints):
			#	constraint = Sketcher.Constraint('Tangent', index1, index2)
			#	index = self.addConstraint(sketchObj, constraint, key)
			#	constraintNode.setSketchEntity(index, constraint)
			#	logMessage('        ... added 2D colinear constraint between %s %s and %s %s' %(line1.getTypeName(), index1, line2.getTypeName(), index2), LOG.LOG_INFO)
		return

	def addSketch2D_Constraint_Tangential2D(self, constraintNode, sketchObj):
		'''
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the sketch object, that will change by applying the constraint
		'''
		line1 = getNode(constraintNode, 'refLine1')
		line2 = getNode(constraintNode, 'refLine2')
		index1 = self.checkSketchIndex(sketchObj, line1)
		index2 = self.checkSketchIndex(sketchObj, line2)
		if ((index1 is not None) and (index2 is not None)):
			key = 'Tangent_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Tangent', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D tangential constraint between %s %s and %s %s' %(line1.getTypeName(), index1, line2.getTypeName(), index2), LOG.LOG_INFO)
		return

	def addSketch2D_Constraint_Vertical2D(self, constraintNode, sketchObj):
		'''
		index: The index of the sketch object, that will change by applying the constraint
		'''
		index = self.getGeometryIndex(sketchObj, constraintNode, 'refLine')
		if (index is not None):
			key = 'Vertical_%s' %(index)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Vertical', index)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D vertical constraint to line %s' %(index), LOG.LOG_INFO)
		return

	def addSketch2D_Constraint_Horizontal2D(self, constraintNode, sketchObj):
		'''
		index: The index of the sketch object, that will change by applying the constraint
		'''
		index = self.getGeometryIndex(sketchObj, constraintNode, 'refLine')
		if (index is not None):
			key = 'Horizontal_%s' %(index)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Horizontal', index)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D horizontal constraint to line %s' %(index), LOG.LOG_INFO)
		return

	def addSketch2D_Coincident_Circle2D(self, constraintNode, sketchObj):
		'''
		Create a circle coincident constraint
		'''
		index1 = self.getGeometryIndex(sketchObj, constraintNode, 'refCircle1')
		index2 = self.getGeometryIndex(sketchObj, constraintNode, 'refCircle2')
		if ((index1 is not None) and (index2 is not None)):
			key = 'Equal_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				constraint = Sketcher.Constraint('Equal', index1, index2)
				index = self.addConstraint(sketchObj, constraint, key)
				constraintNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D circle constraint between circle %s and %s' %(index1, index2), LOG.LOG_INFO)
		return

	def addSketch2D_Constraint_PolygonEdge2D(self, constraintNode, sketchObj): return

	def addSketch2D_Radius2D(self, radiusNode, sketchObj):
		center = getNode(radiusNode, 'refCenter')
		if (center.getTypeName() == 'Circle2D'):
			#add 2D concentric constraint
			center = getNode(center, 'refCenter')
		type = getNode(radiusNode, 'refObject')
 		x = center.getVariable('x') * 10.0
 		y = center.getVariable('y') * 10.0
		if (type.getTypeName() == 'Circle2D'):
			circle = type
			r = circle.getVariable('r') * 10.0
			points = circle.getVariable('points')
			mode = isConstructionMode(circle)
			part = Part.Circle(createVector(x, y, 0), createVector(0, 0, 1), r)
			a = calcAngle2D(center, points[0])
			b = calcAngle2D(center, points[1])
			if ((a is None) and (b is None)):
				logMessage('        ... added Circle M=(%g/%g) R=%g ...' %(x, y, r), LOG.LOG_INFO)
			else:
				radA = 0;
				radB = 0;
				if (a is not None):
					radA = Angle.grad2rad(a.x)
				if (b is not None):
					radB = Angle.grad2rad(b.x)

	 			logMessage('        ... added Arc-Circle M=(%g/%g) R=%g alpha=%s beta=%s ...' %(x, y, r, a, b), LOG.LOG_INFO)
				part = Part.ArcOfCircle(part, radA, radB)
		elif (type.getTypeName() == 'Ellipse2D'):
			c_x = x
			c_y = y
			ellipse = type
			x = ellipse.getVariable('a')
			d = ellipse.getVariable('dA')
			a_x = c_x + (x * d[0] * 10.0)
			a_y = c_y + (x * d[1] * 10.0)

			x = ellipse.getVariable('b')
			b_x = c_x - (x * d[1] * 10.0)
			b_y = c_y + (x * d[0] * 10.0)

			a = ellipse.getVariable('alpha')
			b = ellipse.getVariable('beta')
			if ((a is None) and (b is None)):
				logMessage('        ... added 2D-Ellipse  c=(%g/%g) a=(%g/%g) b=(%g/%g) ...' %(c_x, c_y, a_x, a_y, b_x, b_y), LOG.LOG_INFO)
			else:
				logMessage('        ... added 2D-Arc-Ellipse  c=(%g/%g) a=(%g/%g) b=(%g/%g) alpha=%s beta=%s ...' %(c_x, c_y, a_x, a_y, b_x, b_y, a, b), LOG.LOG_INFO)

			vecA = createVector(a_x, a_y, 0.0)
			vecB = createVector(b_x, b_y, 0.0)
			vecC = createVector(c_x, c_y, 0.0)
			part = Part.Ellipse(vecA, vecB, vecC)

			mode = isConstructionMode(ellipse)
			if ((a is not None) or (b is not None)):
				part = Part.ArcOfEllipse(part, Angle.grad2rad(a.x), Angle.grad2rad(b.x))
		else:
			logWarning('>W1131: ... unknown 2D-Circle \'%s\' M=(%g/%g)!' %(type.getTypeName(), x, y))
			return
		addSketch2D(sketchObj, part, mode, radiusNode)
		type.setSketchEntity(radiusNode.getSketchIndex(), part)
		sketchObj.addConstraint(Sketcher.Constraint('Coincident', center.getSketchIndex(), 1, radiusNode.getSketchIndex(), 3))
		return

	def addSketch2D_Point2D(self, pointNode, sketchObj):
		flags = pointNode.getVariable('flags')
		isOrigin = (flags & 0x10000) > 0

		if (isOrigin):
			pointNode.setSketchEntity(-1, sketchObj.getPoint(-1, 1))
		else:
			x = pointNode.getVariable('x') * 10.0
			y = pointNode.getVariable('y') * 10.0
			mode = isConstructionMode(pointNode)
			part = Part.Point(createVector(x, y, 0))
			addSketch2D(sketchObj, part, mode, pointNode)
			logMessage('        ... added Point (%g/%g) = %s' %(x, y, pointNode.getSketchIndex()), LOG.LOG_INFO)

		coincidens = pointNode.getVariable('refCoincidences')
		if (coincidens):
			count = len(coincidens)
			if (count > 0):
				i = getNextLineIndex(coincidens, 0)
				if (i < count):
					fix = coincidens[i].getBranchNode()
					idxFix = self.checkSketchIndex(sketchObj, fix)
					posFix = findEntityVertex(fix, pointNode)

					mov = pointNode
					idxMov = mov.getSketchIndex()
					posMov = 1
					key = 'Coincident_%s_%s_%s_%s' %(idxMov, posMov, idxFix, posFix)
					if (not key in self.mapConstraints):
						constraint = Sketcher.Constraint('Coincident', idxMov, posMov, idxFix, posFix)
						index = self.addConstraint(sketchObj, constraint, key)
						logMessage('        ... added 2D coincident constraint between %s %s and %s %s' %(idxMov, mov.getTypeName()[0:-2], idxFix, fix.getTypeName()[0:-2]), LOG.LOG_INFO)

					i  = getNextLineIndex(coincidens, i + 1)
					while (i < count):
						mov = coincidens[i].getBranchNode()

						idxMov = self.checkSketchIndex(sketchObj, mov)
						posMov = findEntityVertex(mov, pointNode)
						key = 'Coincident_%s_%s_%s_%s' %(idxMov, posMov, idxFix, posFix)
						if (not key in self.mapConstraints):
							constraint = Sketcher.Constraint('Coincident', idxMov, posMov, idxFix, posFix)
							index = self.addConstraint(sketchObj, constraint, key)
							logMessage('        ... added 2D coincident constraint between %s %s and %s %s' %(idxMov, mov.getTypeName()[0:-2], idxFix, fix.getTypeName()[0:-2]), LOG.LOG_INFO)
						i = getNextLineIndex(coincidens, i + 1)
		return

	def addSketch2D_Line2D(self, lineNode, sketchObj):
		points = lineNode.getVariable('points')
		x1 = getPropertyValue(points, 0x00, 'x') * 10.0
		y1 = getPropertyValue(points, 0x00, 'y') * 10.0
		x2 = getPropertyValue(points, 0x01, 'x') * 10.0
		y2 = getPropertyValue(points, 0x01, 'y') * 10.0

		mode = isConstructionMode(lineNode)
		if((x1 != x2) or (y1 != y2)):
			part = Part.Line(createVector(x1, y1, 0), createVector(x2, y2, 0))
			addSketch2D(sketchObj, part, mode, lineNode)
			logMessage('        ... added Line (%g|%g)-(%g|%g) %r = %s' %(x1, y1, x2, y2, mode, lineNode.getSketchIndex()), LOG.LOG_INFO)
		else:
			logWarning('        ... can\'t add Line (%g|%g)-(%g|%g) when points equal!' %(x1, y1, x2, y2))
		return

	def addSketch2D_Spline2D(self, splineNode, sketchObj):
		'''
		Workaround: As FreeCAD doesn't support Splines, they are converted to simple lines.
		'''
		points = splineNode.getVariable('points')
		mode = isConstructionMode(splineNode)
		logMessage('        ... added Spline %r ...' %(mode), LOG.LOG_INFO)
		i = 1
		while (i < len(points) - 1):
			x1 = getPropertyValue(points, i + 0, 'x') * 10.0
			y1 = getPropertyValue(points, i + 0, 'y') * 10.0
			x2 = getPropertyValue(points, i + 1, 'x') * 10.0
			y2 = getPropertyValue(points, i + 1, 'y') * 10.0
			part = Part.Line(createVector(x1, y1, 0), createVector(x2, y2, 0))
			addSketch2D(sketchObj, part, mode, splineNode)
			i += 1

	def addSketch2D_Circle2D(self, radiusNode, sketchObj):
		# Handled in addSketch2D_Radius2D!!!
		return

	def addSketch2D_Ellipse2D(self, ellipseNode, sketchObj):
		# Handled in addSketch2D_Radius2D!!!
		return

	def addSketch2D_Text2D(self, textNode, sketchObj): return notSupportedNode(textNode)

	def addSketch2D_Frame2D(self, frameNode, sketchObj): return ignoreBranch(frameNode)

	def addSketch2D_Direction(self, directionNode, sketchObj): return

	def addSketch2D_Dimension_Horizonzal_Distance2D(self, dimensionNode, sketchObj):
		'''
		Create a horizontal distance constraint
		'''
		point1 = getNode(dimensionNode, 'refPoint1')
		point2 = getNode(dimensionNode, 'refPoint2')
		index1  = self.checkSketchIndex(sketchObj, point1)
		index2  = self.checkSketchIndex(sketchObj, point2)
		if ((index1 is not None) and (index2 is not None)):
			key = 'DistanceX_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				dx = getDistanceX(point1.getSketchEntity(), point2.getSketchEntity())
				if (dx < 0):
					constraint = Sketcher.Constraint('DistanceX', index2, 1, index1, 1, -dx)
				else:
					constraint = Sketcher.Constraint('DistanceX', index1, 1, index2, 1, dx)
				dimension = getDimension(dimensionNode, 'refDimension')
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D horizontal dimension \'%s\' = %s' %(constraint.Name, dimension.getValue()), LOG.LOG_INFO)
		return

	def addSketch2D_Dimension_Vertical_Distance2D(self, dimensionNode, sketchObj):
		'''
		Create a vertical distance constraint
		'''
		point1 = getNode(dimensionNode, 'refPoint1')
		point2 = getNode(dimensionNode, 'refPoint2')
		index1  = self.checkSketchIndex(sketchObj, point1)
		index2  = self.checkSketchIndex(sketchObj, point2)
		if ((index1 is not None) and (index2 is not None)):
			key = 'DistanceX_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				dy = getDistanceY(point1.getSketchEntity(), point2.getSketchEntity())
				if (dy < 0):
					constraint = Sketcher.Constraint('DistanceY', index2, 1, index1, 1, -dy)
				else:
					constraint = Sketcher.Constraint('DistanceY', index1, 1, index2, 1, dy)
				dimension = getDimension(dimensionNode, 'refDimension')
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D vertical distance \'%s\' = %s' %(constraint.Name, dimension.getValue()), LOG.LOG_INFO)
		return

	def addSketch2D_Dimension_Radius2D(self, dimensionNode, sketchObj):
		'''
		Create a radius constraint
		'''
		circle = getNode(dimensionNode, 'refCircle')
		index  = self.checkSketchIndex(sketchObj, circle)
		if (index is not None):
			key = 'Radius_%s' %(index)
			if (not key in self.mapConstraints):
				radius = circle.getSketchEntity().Radius
				constraint = Sketcher.Constraint('Radius',  index, radius)
				dimension = getDimension(dimensionNode, 'refDimension')
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D radius \'%s\' = %s' %(constraint.Name, dimension.getValue()), LOG.LOG_INFO)
		return

	def addSketch2D_Dimension_Diameter2D(self, dimensionNode, sketchObj):
		'''
		Create a diameter (not available in FreeCAD) constraint
		Workaround: Radius and Center constraint.
		'''
		circle = getNode(dimensionNode, 'refCircle')
		index  = self.checkSketchIndex(sketchObj, circle)
		if (index is not None):
			key = 'Diameter_%s' %(index)
			if (not key in self.mapConstraints):
				radius = circle.getSketchEntity().Radius
				constraint = Sketcher.Constraint('Radius',  index, radius)
				dimension = getDimension(dimensionNode, 'refDimension')
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D diameter \'%s\' = %s' %(constraint.Name, dimension.getValue()), LOG.LOG_INFO)
		return

	def addSketch2D_Dimension_Distance2D(self, dimensionNode, sketchObj):
		'''
		Create a distance constraint
		idx1: The index of the sketch object, that will not change by applying the constraint
		idx2: The index of the point, that will change by applying the constraint
		'''
		point1 = getNode(dimensionNode, 'refPoint1')
		point2 = getNode(dimensionNode, 'refPoint2')
		index1  = self.checkSketchIndex(sketchObj, point1)
		index2  = self.checkSketchIndex(sketchObj, point2)
		if ((index1 is not None) and (index2 is not None)):
			key = 'Distance_%s_%s' %(index1, index2)
			if (not key in self.mapConstraints):
				lengthMM = getLengthPoints(point1, point2)
				length = Length(lengthMM, 1.0, 'mm')
				if (point1.getTypeName() == 'Line2D'):
					constraint = Sketcher.Constraint('Distance', index2, 1, index1, lengthMM)
				elif (point2.getTypeName() == 'Line2D'):
					constraint = Sketcher.Constraint('Distance', index1, 1, index2, lengthMM)
				elif (index1 < 0):
					constraint = Sketcher.Constraint('Distance', index1, 1, index2, 1, lengthMM)
				else:
					constraint = Sketcher.Constraint('Distance', index2, 1, index1, 1, lengthMM)
				dimension = getDimension(dimensionNode, 'refDimension')
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D distance \'%s\' = %s' %(constraint.Name, length), LOG.LOG_INFO)
		return

	def addSketch2D_Dimension_Angle(self,  dimensionNode, sketchObj):
		'''
		Create a angle constraint
		'''
		line1 = getNode(dimensionNode, 'refLine1')
		line2 = getNode(dimensionNode, 'refLine2')
		index1 = self.checkSketchIndex(sketchObj, line1)
		index2 = self.checkSketchIndex(sketchObj, line2)

		points1 = line1.getVariable('points')
		points2 = line2.getVariable('points')

		pt11 = points1[0].node
		pt12 = points1[1].node
		pt21 = points2[0].node
		pt22 = points2[1].node

		d1121 = getDistance(pt11, pt21)
		d1122 = getDistance(pt11, pt22)
		d1221 = getDistance(pt12, pt21)
		d1222 = getDistance(pt12, pt22)

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

		if ((index1 is not None) and (index2 is not None)):
			key = 'Angle_%s_%s_%s_%s' %(index1, pos1, index2, pos2)
			if (not key in self.mapConstraints):
				dimension = getDimension(dimensionNode, 'refDimension')
				angle = dimension.getValue()
				constraint = Sketcher.Constraint('Angle', index1, pos1, index2, pos2, angle.getRAD())
				index = self.addDimensionConstraint(sketchObj, dimension, constraint, key)
				dimensionNode.setSketchEntity(index, constraint)
				logMessage('        ... added 2D angle \'%s\' = %s' %(constraint.Name, dimension.getValue()), LOG.LOG_INFO)
		return

	def addSketch2D_Orientation(self, orientationNode, sketchObj): return ignoreBranch(orientationNode)
	def addSketch2D_String(self, stringNode, sketchObj): return ignoreBranch(stringNode)

	def addSketch2D_160915E2(self, node, sketchObj): return
	def addSketch2D_317B7346(self, node, sketchObj): return
	def addSketch2D_3E55D947(self, node, sketchObj): return
	def addSketch2D_3F4FA55F(self, node, sketchObj): return
	def addSketch2D_4E4B14BC(self, node, sketchObj): return
	def addSketch2D_5D8C859D(self, node, sketchObj): return
	def addSketch2D_64DA5250(self, node, sketchObj): return
	def addSketch2D_7C6D149E(self, node, sketchObj): return
	def addSketch2D_8F55A3C0(self, node, sketchObj): return
	def addSketch2D_8FEC335F(self, node, sketchObj): return
	def addSketch2D_A644E76A(self, node, sketchObj): return
	def addSketch2D_BF3B5C84(self, node, sketchObj): return
	def addSketch2D_C681C2E0(self, node, sketchObj):
		# Some kind of parallel / symmetric constraint
		#    *--------|-----*
		# ____________|_________
		#             |
		#    *--------|-----*

		l1 = node.getVariable('refLine1')
		l2 = node.getVariable('refLine2')
		return

	def addSketch2D_DC93DB08(self, node, sketchObj): return
	def addSketch3D_0B86AD43(self, node, sketchObj): return
	def addSketch3D_10B6ADEF(self, node, sketchObj): return
	def addSketch3D_6A3EEA31(self, node, sketchObj): return
	def addSketch3D_E8D30910(self, node, sketchObj): return

	def Create_Sketch2D_Node(self, sketchObj, node):
		if (node.isHandled() == False):
			try:
				addSketchObj = getattr(self, 'addSketch2D_%s' %(node.getTypeName()))
				addSketchObj(node, sketchObj)
			except AttributeError as e:
				logError('ERROR: (%04X): %s - %s' %(node.getIndex(), node.getTypeName(), e))
				#logError("Warning: Don't know how to add %s to 2D sketch - %s"  %(node.getTypeName(), e))
				logError('>E: ' + traceback.format_exc())
			except Exception as e:
				logError('ERROR: (%04X): %s - %s' %(node.getIndex(), node.getTypeName(), e))
				logError('>E: ' + traceback.format_exc())
			node.setHandled(True)
		return

	def Create_Sketch2D(self, sketchNode):
		name = getNodeName(sketchNode)
		sketchObj = self.doc.addObject('Sketcher::SketchObject', name)
		sketchNode.setSketchEntity(-1, sketchObj)
		orientationNode = sketchNode.getVariable('refOrientation')
		directionNode = sketchNode.getVariable('refDirection').node
		placementNode = directionNode.node.next

		# Angle between the sketch direction and (0/0/1):
		dirX = directionNode.get('x')
		dirY = directionNode.get('y')
		dirZ = directionNode.get('z')
		rotAngle = degrees(acos(dirZ))

		# Rotation from (0/0/1) to direction:
		if ((dirY != 0) or (dirX != 0)):
			rotAxis  = createVector(-dirY, dirX, 0.0)
		else:
			rotAxis  = createVector(1.0, 0.0, 0.0)

		origin = getOrigin(placementNode)

		try:
			rotation = createRotation(rotAxis, rotAngle)
			sketchObj.Placement = FreeCAD.Placement(origin, rotation)
		except Exception as e:
			logError('Error in Placement(%s, Rotation(%s, %s): %s' %(origin, rotAxis, rotAngle, e))
		logMessage('        added 2D-Sketch \'%s\' (%g/%g/%g) ...' %(name, getX(origin), getY(origin), getZ(origin)), LOG.LOG_INFO)

		child = sketchNode.first
		while (child):
			if (child.isRef):
				self.Create_Sketch2D_Node(sketchObj, child)
			child = child.next

		if (self.root):
			self.root.addObject(sketchObj)

		return

	def Create_FxPad(self, padNode, sketchNode, name):
		properties = padNode.getVariable('properties')
		direction  = getListNode(properties, 0x02)               # The direction of the extrusion
		reversed   = getListNode(properties, 0x03).get('value')  # If the extrusion direction is inverted
		dimLength1 = getListNode(properties, 0x04)               # The length of the extrusion in direction 1
		dimAngle   = getListNode(properties, 0x05).node          # The taper outward angle  (doesn't work properly in FreeCAD)
		midplane   = getListNode(properties, 0x07).get('value')
		solid      = getListNode(properties, 0x1A) is not None
		dimLength2 = getListNode(properties, 0x1B)               # The length of the extrusion in direction 2
		pad = None
		if (dimLength1):
			dimLength1 = dimLength1.node
			sketchName = getNodeName(sketchNode)
			sketch = sketchNode.getSketchEntity()
			len1 = dimLength1.getValue()
			if (isinstance(len1, Length)):
				len1 = len1.getMM()
			else:
				len1 = len1 * 10.0
			x          = direction.get('x') * len1
			y          = direction.get('y') * len1
			z          = direction.get('z') * len1
			taperAngle = dimAngle.getValue()

			# pad = self.doc.addObject("Part::Extrusion", name)
			# pad.Base = sketch
			# pad.Dir = (x, y, z)
			# pad.Solid = solid
			# pad.TaperAngle = taperAngle.getGRAD()
			# pad.ViewObject.ShapeColor = sketch.ViewObject.ShapeColor
			# pad.ViewObject.LineColor  = sketch.ViewObject.LineColor
			# pad.ViewObject.PointColor = sketch.ViewObject.PointColor

			pad = self.doc.addObject("PartDesign::Pad", name)
			pad.Sketch = sketch
			pad.UpToFace = None
			pad.Reversed = reversed
			pad.Midplane = midplane
			pad.Length = len1
			# Workaround with taperAngle: Add draft on outward face.

			if (dimLength2):
				dimLength2 = dimLength2.node
				len2 = dimLength2.getValue()
				logMessage('        creating pad \'%s\' based on \'%s\' (rev=%s, sym=%s, len=%s, len2=%s) ...' %(name, sketchName, reversed, midplane, len1, len2), LOG.LOG_INFO)
				pad.Type = 4
				pad.Length2 = len2.getMM()
			else:
				logMessage('        creating pad \'%s\' based on \'%s\' (rev=%s, sym=%s, len=%s) ...' %(name, sketchName, reversed, midplane, len1), LOG.LOG_INFO)
				pad.Type = 0
				pad.Length2 = 0.0

			padNode.setSketchEntity(-1, pad)

		return pad

	def Create_FxRevolution(self, revolutionNode, sketchNode, name):
		sketchName = getNodeName(sketchNode)
		properties = revolutionNode.getVariable('properties')
		reversed = 0
		val3 = getPropertyValue(properties, 0x3, 'u16_0')
		x1 = getPropertyValue(properties, 0x2, 'x1')
		y1 = getPropertyValue(properties, 0x2, 'y1')
		z1 = getPropertyValue(properties, 0x2, 'z1')
		x2 = getPropertyValue(properties, 0x2, 'x2')
		y2 = getPropertyValue(properties, 0x2, 'y2')
		z2 = getPropertyValue(properties, 0x2, 'z2')
		dx = x2 - x1
		dy = y2 - y1
		dz = z2 - z1
		lAxis = sqrt(dx*dx + dy*dy + dz*dz)
		val5 = getPropertyValue(properties, 0x5, 'u16_0')
		midplane =  IFF(val5 == 2, 1, 0)
		angle1   = getPropertyValue(properties, 0x4, 'values')

		revolution = None
		if (angle1):
			sketch = sketchNode.getSketchEntity()
			alpha = Angle(angle1[0])

			#revolution = self.doc.addObject("PartDesign::Revolution", name)
			#revolution.Sketch = sketch
			#revolution.Reversed = reversed

			revolution = self.doc.addObject("Part::Revolution", name)
			revolution.Source = sketch
			revolution.Axis = (dx/lAxis, dy/lAxis, dz/lAxis)
			revolution.Base = (x1, y1, z1)

			angle2   = getPropertyValue(properties, 0x12, 'values')
			if (angle2 is None):
				logMessage('        adding revolution \'%s\' (%s)-(%s) based on \'%s\' (rev=%s, sym=%s, alpha=%s) ...' %(name, revolution.Base, revolution.Axis, sketchName, reversed, midplane, alpha), LOG.LOG_INFO)
			else:
				beta = Angle(angle2[0])
				midplane = True
				logMessage('        adding revolution \'%s\' based on \'%s\' (rev=%s, sym=%s, alpha=%s, beta=%s) #BUGGY#...' %(name, sketchName, reversed, midplane, alpha, beta), LOG.LOG_INFO)
				alpha.x += beta.x

			revolution.Angle = alpha.x
			revolution.Solid = getListNode(properties, 0x11) is not None
			revolution.ViewObject.ShapeColor = sketch.ViewObject.ShapeColor
			revolution.ViewObject.LineColor  = sketch.ViewObject.LineColor
			revolution.ViewObject.PointColor = sketch.ViewObject.PointColor
			#revolution.Midplane = midplane

			revolutionNode.setSketchEntity(-1, revolution)
		return revolution

	def Create_FxExtrusion(self, extrusionNode):
		label = extrusionNode.getVariable('label').node
		name = label.name
		refSketch = label.get('lst0')

		logMessage('    adding Create_FxExtrusion \'%s\' ...' %(name), LOG.LOG_INFO)

		if (refSketch):
			refSketch = refSketch[0]
			sketchNode = refSketch.getBranchNode()
			if (sketchNode.getSketchEntity() is None):
				self.CreateObject(sketchNode)

			properties = extrusionNode.getVariable('properties')
			typ = getListNode(properties, 0x02)
			obj3D = None
			if (typ):
				if (typ.typeName == 'Direction'):
					obj3D = self.Create_FxPad(extrusionNode, sketchNode, name)
				elif (typ.typeName == 'Line3D'):
					obj3D = self.Create_FxRevolution(extrusionNode, sketchNode, name)
			if (obj3D):
				if (self.root):
					self.root.addObject(obj3D)
				if (sketchNode):
					sketch = sketchNode.getSketchEntity()
					if (sketch):
						sketch.ViewObject.hide()

	def Create_FxChampher(self, filletNode):
		#source = sourceNode.getSketchEntity()
		#edge =
		#l1 =
		#l2 = l1
		#chamfer = self.doc.addObject("Part::Chamfer", name)
		#chamfer.Base = FreeCAD.ActiveDocument.Fillet
		#edges = []
		#edges.append((edge, l1, l2))
		#chamfer.Edges = edges
		#del edges
		#source.ViewObject.Visibility = False
		#chamfer.ViewObject.LineColor  = source.ViewObject.LineColor
		#chamfer.ViewObject.PointColor = source.ViewObject.PointColor
		return

	def Create_FxFillet(self, filletNode):
		#source = sourceNode.getSketchEntity()
		#fillet = self.doc.addObject("Part::Fillet", name)
		#fillet.Base = source
		#edges = []
		#edges.append((edge, r1, r2))
		#fillet.Edges = edges
		#del edges
		#source.ViewObject.Visibility = False
		#fillet.ViewObject.LineColor  = source.ViewObject.LineColor
		#fillet.ViewObject.PointColor = source.ViewObject.PointColor
		return

	def Create_FxBoolean(self, booleanNode):             return
	def Create_FxBoundaryPatch(self, boundaryPatchNode): return
	def Create_FxDrill(self, drillTypeNode):             return
	def Create_FxLoft(self, loftNode):                   return
	def Create_FxShell(self, shellNode):                 return
	def Create_FxSplit(self, splitNode):                 return
	def Create_FxThicken(self, thickenNode):             return
	def Create_FxThread(self, threadNode):
		# https://www.freecadweb.org/wiki/Thread_for_Screw_Tutorial/de
		return notSupportedNode(threadNode)
	def Create_FxTrim(self, trimNode):                   return
	def Create_SolidBody(self, solidBodyNode):           return
	def Create_Feature(self, solidBodyNode):             return

	def addSketch3D_Point3D(self, pointNode, sketchObj):
		if ((len(pointNode.getVariable('refs')) == 0) and (len(pointNode.getVariable('lst1')) == 0)):
			x = pointNode.getVariable('x') * 10.0
			y = pointNode.getVariable('y') * 10.0
			z = pointNode.getVariable('z') * 10.0
			logMessage('        ... added 3D-Point (%g/%g/%g) ...' %(x, y, z), LOG.LOG_INFO)
			draft = Draft.makePoint(x, y, z)
			if (sketchObj):
				index = sketchObj.addObject(draft)
				pointNode.setSketchEntity(index, draft)
		return

	def addSketch3D_Line3D(self, lineNode, sketchObj):
		x1 = lineNode.getVariable('x1') * 10.0
		y1 = lineNode.getVariable('y1') * 10.0
		z1 = lineNode.getVariable('z1') * 10.0
		x2 = lineNode.getVariable('x2') * 10.0
		y2 = lineNode.getVariable('y2') * 10.0
		z2 = lineNode.getVariable('z2') * 10.0

		points = [createVector(x1, y1, z1), createVector(x2, y2, z2)]

		logMessage('        ... 3D-Line (%g/%g/%g)-(%g/%g/%g) ...' %(x1, y1, z1, x2, y2, z2), LOG.LOG_INFO)
		draft = Draft.makeWire(points, closed = False, face = True, support = None)
		if (sketchObj):
			index = sketchObj.addObject(draft)
			lineNode.setSketchEntity(index, draft)
		return

	def addSketch3D_Radius3D(self, circleNode, sketchObj):
		name = getNodeName(circleNode)
		lst0 = circleNode.getVariable('lst0')
		center = lst0[0].getBranchNode()
		if (center.getTypeName() == 'Circle3D'):
			#TODO: add concentric constraint
			center = getNode(center, 'refCenter')
		type = lst0[1].getBranchNode()
 		xc = center.getVariable('x') * 10.0
 		yc = center.getVariable('y') * 10.0
 		zc = center.getVariable('z') * 10.0
		if (type.getTypeName() == 'Circle3D'):
			circle = type
			# r = circle.getVariable('r') * 10.0
			points = circle.getVariable('points')
			x1 = getPropertyValue(points, 1, 'x')
			y1 = getPropertyValue(points, 1, 'y')
			z1 = getPropertyValue(points, 1, 'z')
			x2 = getPropertyValue(points, 0, 'x')
			y2 = getPropertyValue(points, 0, 'y')
			z2 = getPropertyValue(points, 0, 'z')
			r = sqrt(((xc - x1) * (xc - x1)) + ((yc - y1) * (yc - y1)) + ((zc - z1) * (zc - z1)))
			a = calcAngle3D(xc, yc, zc, x1, y1, z1)
			b = calcAngle3D(xc, yc, zc, x2, y2, z2)
			circle = self.doc.addObject("Part::Circle", name)
			circle.Radius = r
			# Plane : C + r(P1-C) + s (P2-C)
			# N = R x S
			xa = x1 - xc
			ya = y1 - yc
			za = z1 - zc
			xb = x2 - xc
			yb = y2 - yc
			zb = z2 - zc
			xn = ya*zb - za*yb
			yn = za*xb - xa*zb
			zn = xa*yb - ya*xb

			an = calcAngle3D(xc, yc, zc, xn, yn, zn)
			circle.Placement = FreeCAD.Placement(createVector(xc, yc, zc), createRotation(createVector(xn, yn, zn), an))
			if ((a is None) and (b is None)):
				logMessage('        ... added 3D-Circle M=(%g/%g/%g) R=%g ...' %(xc, yc, zc, r), LOG.LOG_INFO)
				circle.Angle0 =   0.0
				circle.Angle1 = 360.0
			else:
				circle.Angle0 = a.x
				circle.Angle1 = b.x
	 			logMessage('        ... added 3D-Arc-Circle M=(%g/%g/%g) R=%g alpha=%s beta=%s ...' %(xc, yc, zc, r, a, b), LOG.LOG_INFO)
			if (sketchObj):
				index = sketchObj.addObject(circle)
				circleNode.setSketchEntity(index, circle)
		elif (type.getTypeName() == 'Ellipse3D'):
			pass
		else:
	 		logWarning('>W1231: ... unknown 3D-Circle \'%s\' M=(%g/%g/%g)!' %(type.getTypeName(), xc, yc, zc))
		return

	def addSketch3D_Spline3D_Curve(self, splineNode, sketchObj):
		points = []
		for ref in splineNode.getVariable('lst0'):
			p = ref.node
			if (p.typeName == 'Point3D'):
				x = p.get('x')
				y = p.get('y')
				z = p.get('z')
				v = createVector(x, y, z)
				points.append(v)
		draft = Draft.makeBSpline(points, closed = False, face = True, support = None)
		if (sketchObj):
			index = sketchObj.addObject(draft)
			splineNode.setSketchEntity(index, draft)
		return

	def addSketch3D_Plane(self, lineNode, sketchObj):             return
	def addSketch3D_SpiralCurve(self, spiralNode, sketchObj):     return
	def addSketch3D_Spline3D_Bezier(self, splineNode, sketchObj): return
	def addSketch3D_Bezier3D(self, branchNode, sketchObj):        return

	def addSketch3D_Circle3D(self, radiusNode, sketchObj):                       return ignoreBranch(radiusNode)

	def addSketch3D_Constraint_Coincident3D(self, constraintNode, sketchObj):    return notSupportedNode(constraintNode)
	def addSketch3D_Constraint_Colinear3D(self, constraintNode, sketchObj):      return notSupportedNode(constraintNode)
	def addSketch3D_Constraint_Horizontal3D(self, constraintNode, sketchObj):    return notSupportedNode(constraintNode)
	def addSketch3D_Constraint_Parallel3D(self, constraintNode, sketchObj):      return notSupportedNode(constraintNode)
	def addSketch3D_Constraint_Perpendicular3D(self, constraintNode, sketchObj): return notSupportedNode(constraintNode)
	def addSketch3D_Constraint_Tangential3D(self, constraintNode, sketchObj):    return notSupportedNode(constraintNode)
	def addSketch3D_Constraint_Vertical3D(self, constraintNode, sketchObj):      return notSupportedNode(constraintNode)

	def Create_Sketch3D(self, sketchNode):
		name = getNodeName(sketchNode)
		logMessage('       adding 3D-Sketch \'%s\'...' %(name), LOG.LOG_INFO)
		sketchObj = createGroup(self.doc, name)
		if (self.root):
			self.root.addObject(sketchObj)

		child = sketchNode.first
		while (child):
			if (child.isRef):
				if (child.isHandled() == False):
					try:
						addSketchObj = getattr(self, 'addSketch3D_%s' %(child.getTypeName()))
						addSketchObj(child, sketchObj)
					except AttributeError as e:
						logError("Warning: Don't know how to add %s to 3D sketch - %s"  %(child.getTypeName(), e))
						# pass
					except:
						logError('>E: ' + traceback.format_exc())
			child.setHandled(True)
			child = child.next
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
		name = getNodeName(planeNode)
		plane = self.doc.addObject("Part::Plane", name)
		l = 10.0
		w = 10.0
		x = 0.0
		y = 0.0
		z = 0.0
		plane.Length = l
		plane.Width = w
		plane.Placement = FreeCAD.Placement(createVector(x, y, z), createRotation(createVector(0, 0, 1), 45))
		if (self.root):
			self.root.addObject(plane)

		return

	def Create_Body(self, bodyNode):                             return ignoreBranch(bodyNode)
	def Create_RDxBody(self, bodyNode):                          return ignoreBranch(bodyNode)
	def Create_Circle3D(self, radiusNode):                       return ignoreBranch(radiusNode)
	def Create_Constraint_Coincident3D(self, constraintNode):    return ignoreBranch(constraintNode)
	def Create_Constraint_Colinear3D(self, constraintNode):      return ignoreBranch(constraintNode)
	def Create_Constraint_Perpendicular3D(self, constraintNode): return ignoreBranch(constraintNode)
	def Create_Stop(self, stopNode):                             return ignoreBranch(stopNode)
	def Create_Group2D(self, groupNode):                         return ignoreBranch(groupNode)
	def Create_Group3D(self, groupNode):                         return ignoreBranch(groupNode)
	def Create_Point3D(self, pointNode):                         return ignoreBranch(pointNode)
	def Create_RDxVar(self, varNode):                            return ignoreBranch(varNode)
	def Create_RevolutionOrientation(self, orientationNode):     return ignoreBranch(orientationNode)
	def Create_Sketch2DSurface(self, surfaceNode):               return ignoreBranch(surfaceNode)
	def Create_Text2D(self, textNode):                           return notSupportedNode(textNode)
	def Create_ValueByte(self, valueNode):                       return ignoreBranch(valueNode)

	def Create_92637D29(self, node):
		# Revolution.Extends1
		return ignoreBranch(node)

	def Create_C7A06AC2(self, node):
		#Revolution.Extends2
		return ignoreBranch(node)

	def Create_Bezier3D(self, node):                  return
	def Create_DeselTable(self, deselTableNode):      return
	def Create_Dimension(self, dimensionNode):        return
	def Create_Direction(self, directionNode):        return
	def Create_MirrorPattern(self, patternNode):      return
	def Create_Label(self, labelNode):                return
	def Create_Orientation(self, orientationNode):    return
	def Create_RectangularPattern(self, patternNode): return
	def Create_SpiralCurve(self, curveNode):          return
	def Create_Spline3D_Bezier(self, bezierNode):     return

	def Create_029DAD70(self, node): return
	def Create_03AA812C(self, node): return
	def Create_04D026D2(self, node): return
	def Create_06977131(self, node): return
	def Create_06DCEFA9(self, node): return
	def Create_07910C0A(self, node): return
	def Create_07910C0B(self, node): return
	def Create_0830C1B0(self, node): return
	def Create_09429287(self, node): return
	def Create_09429289(self, node): return
	def Create_0942928A(self, node): return
	def Create_0B85010C(self, node): return
	def Create_0B86AD43(self, node): return
	def Create_0C12CBF2(self, node): return
	def Create_0C48B860(self, node): return
	def Create_0C48B861(self, node): return
	def Create_0D0F9548(self, node): return
	def Create_0D28D8C0(self, node): return
	def Create_13F4E5A3(self, node): return
	def Create_151280F0(self, node): return
	def Create_173E51F4(self, node): return
	def Create_17B3E814(self, node): return
	def Create_1A1C8265(self, node): return
	def Create_1A26FF54(self, node): return
	def Create_1B48AD11(self, node): return
	def Create_1B48E9DA(self, node): return
	def Create_1DEE2CF3(self, node): return
	def Create_1EF28758(self, node): return
	def Create_1F6D59F6(self, node): return
	def Create_20976662(self, node): return
	def Create_2148C03C(self, node): return
	def Create_255D7ED7(self, node): return
	def Create_27E9A56F(self, node): return
	def Create_2801D6C6(self, node): return
	def Create_2B48CE72(self, node): return
	def Create_2D06CAD3(self, node): return
	def Create_2D86FC26(self, node): return
	def Create_2E692E29(self, node): return
	def Create_3170E5B0(self, node): return
	def Create_31F02EED(self, node): return
	def Create_339807AC(self, node): return
	def Create_34FAB548(self, node): return
	def Create_375C6982(self, node): return
	def Create_38C2654E(self, node): return
	def Create_38C74735(self, node): return
	def Create_39A41830(self, node): return
	def Create_3A083C7B(self, node): return
	def Create_3C6C1C6C(self, node): return
	def Create_3D8924FD(self, node): return
	def Create_3E710428(self, node): return
	def Create_3F36349F(self, node): return
	def Create_3F3634A0(self, node): return
	def Create_402A8F9F(self, node): return
	def Create_4116DA9E(self, node): return
	def Create_424EB7D7(self, node): return
	def Create_46D500AA(self, node): return
	def Create_4949374A(self, node): return
	def Create_4AC78A71(self, node): return
	def Create_4ACA204D(self, node): return
	def Create_4B3150E8(self, node): return
	def Create_4FB10CB8(self, node): return
	def Create_4FD0DC2A(self, node): return
	def Create_509FB5CC(self, node): return
	def Create_528A064A(self, node): return
	def Create_55279EE0(self, node): return
	def Create_578432A6(self, node): return
	def Create_5838B762(self, node): return
	def Create_5838B763(self, node): return
	def Create_5B8EC461(self, node): return
	def Create_5CB011E2(self, node): return
	def Create_5D807360(self, node): return
	def Create_603428AE(self, node): return
	def Create_60406697(self, node): return
	def Create_618C9E00(self, node): return
	def Create_637B1CC1(self, node): return
	def Create_64DE16F3(self, node): return
	def Create_6CA92D02(self, node): return
	def Create_7256922C(self, node): return
	def Create_72C97D63(self, node): return
	def Create_7325290E(self, node): return
	def Create_7325290F(self, node): return
	def Create_73F35CD0(self, node): return
	def Create_748FBD64(self, node): return
	def Create_74E6F48A(self, node): return
	def Create_75A6689B(self, node): return
	def Create_76EC185B(self, node): return
	def Create_778752C6(self, node): return
	def Create_78F28827(self, node): return
	def Create_79D4DD11(self, node): return
	def Create_7C6D7B13(self, node): return
	def Create_7DA7F733(self, node): return
	def Create_7DAA0032(self, node): return
	def Create_7F4A3E30(self, node): return
	def Create_7F936BAA(self, node): return
	def Create_831EBCE9(self, node): return
	def Create_83D31932(self, node): return
	def Create_86173E3F(self, node): return
	def Create_88FA65CA(self, node): return
	def Create_8AFFBE5A(self, node): return
	def Create_8B1E9A97(self, node): return
	def Create_8B2BE62E(self, node): return
	def Create_8D6EF0BE(self, node): return
	def Create_8EB19F04(self, node): return
	def Create_90874D23(self, node): return
	def Create_90874D40(self, node): return
	def Create_90874D51(self, node): return
	def Create_90874D53(self, node): return
	def Create_90874D55(self, node): return
	def Create_90874D56(self, node): return
	def Create_90874D60(self, node): return
	def Create_90874D63(self, node): return
	def Create_90874D74(self, node): return
	def Create_936522B1(self, node): return
	def Create_93C7EE68(self, node): return
	def Create_99684A5A(self, node): return
	def Create_99B938AE(self, node): return
	def Create_99B938B0(self, node): return
	def Create_9C8C1297(self, node): return
	def Create_9DA736B0(self, node): return
	def Create_A244457B(self, node): return
	def Create_A29C84B7(self, node): return
	def Create_A31E29E0(self, node): return
	def Create_A3B0404C(self, node): return
	def Create_A477243B(self, node): return
	def Create_A5977BAA(self, node): return
	def Create_A6118E11(self, node): return
	def Create_A76B22A0(self, node): return
	def Create_AA805A06(self, node): return
	def Create_AAD64116(self, node): return
	def Create_AD0D42B2(self, node): return
	def Create_AD416CEA(self, node): return
	def Create_AE101F92(self, node): return
	def Create_B10D8B80(self, node): return
	def Create_B382A87C(self, node): return
	def Create_B3EAA9EE(self, node): return
	def Create_B58135C4(self, node): return
	def Create_B5D4DEE6(self, node): return
	def Create_B8CB3560(self, node): return
	def Create_B8DBEF70(self, node): return
	def Create_B8E19017(self, node): return
	def Create_BCBBAD85(self, node): return
	def Create_BF8B8868(self, node): return
	def Create_C1887310(self, node): return
	def Create_C6E21E1A(self, node): return
	def Create_CA02411F(self, node): return
	def Create_CA674C90(self, node): return
	def Create_CB6C0A56(self, node): return
	def Create_CCD87CBA(self, node): return
	def Create_CE7F937A(self, node): return
	def Create_CEFD3973(self, node): return
	def Create_D2D440C0(self, node): return
	def Create_D2DA2CF0(self, node): return
	def Create_D524C30A(self, node): return
	def Create_D5DAAA83(self, node): return
	def Create_D61732C1(self, node): return
	def Create_D80CE357(self, node): return
	def Create_D83EF271(self, node): return
	def Create_D8A9C970(self, node): return
	def Create_DA4970B5(self, node): return
	def Create_DFB2586A(self, node): return
	def Create_E0E3E202(self, node): return
	def Create_E0EA12F2(self, node): return
	def Create_E1D3D023(self, node): return
	def Create_E2CCC3B7(self, node): return
	def Create_E524B878(self, node): return
	def Create_E558F428(self, node): return
	def Create_E562B07C(self, node): return
	def Create_E70647C2(self, node): return
	def Create_E70647C3(self, node): return
	def Create_E94FB6D9(self, node): return
	def Create_E9821C66(self, node): return
	def Create_EAC2875A(self, node): return
	def Create_EE767654(self, node): return
	def Create_EE792053(self, node): return
	def Create_EF8279FB(self, node): return
	def Create_EFE47BB4(self, node): return
	def Create_F0677096(self, node): return
	def Create_F94FF0D9(self, node): return
	def Create_F9884C43(self, node): return
	def Create_FB73FDDF(self, node): return
	def Create_FC203F47(self, node): return
	def Create_FEB0D977(self, node): return
	def Create_FF15793D(self, node): return
	def Create_FFD270B8(self, node): return

	def CreateObject(self, node):
		try:
			importObject = getattr(self, 'Create_%s' %(node.getTypeName()))
			importObject(node)
			node.setHandled(True)
		except AttributeError as e:
			logError('Error in creating (%04X): %s - %s'  %(node.getIndex(), node.getTypeName(), e))
			logError('>E: ' + traceback.format_exc())
		except Exception as e:
			logError('Error in creating (%04X): %s - %s'  %(node.getIndex(), node.getTypeName(), e))
			logError('>E: ' + traceback.format_exc())

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

	def importModel(self, model):
		if (model):
			storage = model.RSeStorageData

			grx = FreeCADImporter.findDC(storage)

			if (grx):
				self.mapConstraints = {}
				root = grx.tree.getFirstChild('Part')
				label = root.getVariable('cld_0').node
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
