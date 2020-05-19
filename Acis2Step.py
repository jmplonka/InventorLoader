# -*- coding: utf-8 -*-

'''
Acis2Step.py:
'''

from datetime      import datetime
from importerUtils import isEqual, getDumpFolder
from FreeCAD       import Vector as VEC
from importerUtils import logInfo, logWarning, logError, logAlways, isEqual1D, getAuthor, getDescription, ENCODING_FS, getColorDefault
import traceback, inspect, os, sys, Acis, math, re, Part, io

#############################################################
# private variables
#############################################################

_pointsVertex    = {}
_pointsCartesian = {}
_directions      = {}
_edgeCurves      = {}
_lines           = {}
_ellipses        = {}
_vectors         = {}
_cones           = {}
_cylinders       = {}
_planes          = {}
_spheres         = {}
_curveBSplines   = {}
_assignments     = {}
_entities        = []
_colorPalette    = {}

#############################################################
# private functions
#############################################################

def _getE(o):
	if (isinstance(o, E)): return o
	if (o is None): return None
	return E(o)

def _dbl2str(d):
	if (d == 0.0):
		return u"0."
	if (math.fabs(d) > 5e5):
		s = ('%E' % d).split('E')
		return s[0].rstrip('0') + 'E+' + s[1][1:].lstrip('0')
	if (math.fabs(d) < 5e-5):
		s = ('%E' % d).split('E')
		return s[0].rstrip('0') + 'E-' + s[1][1:].lstrip('0')
	s = u"%r" %(d)
	return s.rstrip('0')

def _bool2str(v):
	return u".T." if v else u".F."

def _str2str(s):
	if (s is None):
		return '$'
	return u"'%s'" %(s)

def _entity2str(e):
	if (isinstance(e, AnonymEntity)):
		return u"%s" %(e.__str__())
	return '*'

def _lst2str(l):
	return u"(%s)" %(",".join([_obj2str(i) for i in l]))

def _obj2str(o):
	if (o is None):                   return _str2str(o)
	if (type(o) == int):              return u"%d" %(o)
	if (sys.version_info.major < 3):
		if (type(o) == long):         return u"%d" %(o)
		if (type(o) == unicode):      return _str2str(o)
	if (type(o) == float):            return _dbl2str(o)
	if (type(o) == bool):             return _bool2str(o)
	if (type(o) == str):              return _str2str(o)
	if (isinstance(o, AnyEntity)):    return "*"
	if (isinstance(o, E)):            return u"%r" %(o)
	if (isinstance(o, AnonymEntity)): return _entity2str(o)
	if (type(o) == list):             return _lst2str(o)
	if (type(o) == tuple):            return _lst2str(o)
	raise Exception("Don't know how to convert '%s' into a string!" %(o.__class__.__name__))

def _values3D(v):
	return [v.x, v.y, v.z]

def getColor(entity):
	global _colorPalette

	r = g = b = None

	color = entity.getColor()
	if (color is not None):
		r, g, b = color.red, color.green, color.blue
	else:
		color = getColorDefault()
		if (color is not None):
			r, g, b = color
		else:
			return None
	key = "#%02X%02X%02X" %(int(r*255.0), int(g*255.0), int(b*255.0))
	try:
		rgb = _colorPalette[key]
	except:
		rgb = COLOUR_RGB('', r, g, b)
		_colorPalette[key] = rgb
	return rgb

def assignColor(color, item, context):
	global _assignments

	if (color is not None):
		keyRGB = "%g,%g,%g" %(color.red, color.green, color.blue)
		representation = MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('', [], context)
		style = STYLED_ITEM('color', [], item)
		representation.items.append(style)
		try:
			assignment = _assignments[keyRGB]
		except:
			assignment = PRESENTATION_STYLE_ASSIGNMENT(color);
			_assignments[keyRGB] = assignment
		style.styles = [assignment]

def _createUnit(tolerance):
	unit = UNIT()
	uncr = GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT()
	glob = GLOBAL_UNIT_ASSIGNED_CONTEXT()
	repr = REPRESENTATION_CONTEXT()

	length = ListEntity(LENGTH_UNIT(None), NAMED_UNIT(AnyEntity()), SI_UNIT('MILLI', 'METRE'))
	angle1 = ListEntity(NAMED_UNIT(AnyEntity()), PLANE_ANGLE_UNIT(None), SI_UNIT(None, 'RADIAN'))
	angle2 = ListEntity(NAMED_UNIT(AnyEntity()), SI_UNIT(None, 'STERADIAN'), SOLID_ANGLE_UNIT(None))
	uncertainty = UNCERTAINTY_MEASURE_WITH_UNIT(tolerance, length)

	uncr.units = (uncertainty,)

	glob.assignments = (length, angle1, angle2)

	unit.entities =  _createGeometricRepresentationList(uncr, glob, repr)
	return unit

def _createCartesianPoint(fcVec, name = ''):
	global _pointsCartesian
	key = "%s,'%s'" %(fcVec, name)
	try:
		cp = _pointsCartesian[key]
	except:
		cp = CARTESIAN_POINT(name, _values3D(fcVec))
		_pointsCartesian[key] = cp
	return cp

def _createVertexPoint(fcVec, name = ''):
	global _pointsVertex
	key = "%s,'%s'" %(fcVec, name)
	try:
		vp = _pointsVertex[key]
	except:
		vp = VERTEX_POINT('', None)
		vp.point = _createCartesianPoint(fcVec)
		_pointsVertex[key] = vp
	return vp

def _createDirection(fcVec, name = ''):
	global _directions
	v = VEC(fcVec).normalize()
	key = "%s,'%s'" %(v, name)
	try:
		dir =  _directions[key]
	except:
		dir = DIRECTION(name, _values3D(v))
		_directions[key] = dir
	return dir

def _createVector(fcVec, name = ''):
	global _vectors
	global _scale
	key = "%s,'%s'" %(fcVec, name)
	try:
		vec = _vectors[key]
	except:
		vec = VECTOR('', None, _scale)
		vec.orientation = _createDirection(fcVec)
		_vectors[key] = vec
	return vec

def _createAxis1Placement(name, aPt, aName, bPt, bName):
	plc = AXIS1_PLACEMENT(name, None, None)
	plc.location  = _createCartesianPoint(aPt, aName)
	plc.axis      = _createDirection(bPt, bName)
	return plc

def _createAxis2Placement3D(name, aPt, aName, bPt, bName, cPt, cName):
	plc = AXIS2_PLACEMENT_3D(name, None, None, None)
	plc.location  = _createCartesianPoint(aPt, aName)
	plc.axis      = _createDirection(bPt, bName)
	plc.direction = _createDirection(cPt, cName)
	return plc

def _createEdgeCurve(p1, p2, curve, sense):
	global _edgeCurves
	key = "#%d,#%d,#%d,%s" %(p1.id, p2.id, curve.id, _bool2str(sense))
	try:
		ec = _edgeCurves[key]
	except:
		ec = EDGE_CURVE('', p1, p2, curve, sense)
		_edgeCurves[key] = ec
	return ec

def _exportList_(a):
	step = ''
	for i in a:
		if (isinstance(i, ExportEntity)):
			step += i.exportSTEP()
		elif (type(i) == list):
			step += _exportList_(i)
		elif (type(i) == tuple):
			step += _exportList_(i)
	return step

def _createCurveComp(acisCurve):
    # TODO
	return acisCurve

def _createCurveDegenerate(acisCurve):
    # TODO
	return acisCurve

def _createCurveEllipse(acisCurve):
	global _ellipses
	key = '%s,%s,%s,%s' %(acisCurve.center, acisCurve.axis, acisCurve.major, acisCurve.ratio)
	try:
		circle = _ellipses[key]
	except:
		if (isEqual1D(acisCurve.ratio, 1.0)):
			circle = CIRCLE('', None, acisCurve.major.Length)
		else:
			axis1 = acisCurve.major.Length
			circle = ELLIPSE('', None, axis1, axis1 * acisCurve.ratio)
		circle.placement = _createAxis2Placement3D('', acisCurve.center, 'Origin', acisCurve.axis, 'center_axis', acisCurve.major, 'ref_axis')
		_ellipses[key] = circle
	return circle

def _createCurveInt(acisCurve):
	global _curveBSplines
	shape = acisCurve.build()
	if (isinstance(shape, Part.Edge)):
		bsc = shape.Curve
		if (isinstance(bsc, Part.BSplineCurve)):
			points = [_createCartesianPoint(v, 'Ctrl Pts') for v in bsc.getPoles()]
			k1 = ",".join(["#%d"%(p.id) for p in points])
			k2 = ""
			mults = bsc.getMultiplicities()
			if (mults is not None):
				k2 = ",".join(["%d" %(d) for d in mults])
			k3 = ""
			knots = bsc.getKnots()
			if (knots is not None): k3 = ",".join(["%r" %(r) for r in knots])
			key = "(%s),(%s),(%s)" %(k1, k2, k3)
			try:
				curve = _curveBSplines[key]
			except:
				if (bsc.isRational()):
					p0 = BOUNDED_CURVE()
					p1 = B_SPLINE_CURVE(name=None, degree=bsc.Degree, points=points, form='UNSPECIFIED', closed=bsc.isClosed(), selfIntersecting=False)
					p2 = B_SPLINE_CURVE_WITH_KNOTS(mults=bsc.getMultiplicities(), knots=bsc.getKnots(), form2='UNSPECIFIED')
					p3 = CURVE()
					p4 = GEOMETRIC_REPRESENTATION_ITEM()
					p5 = RATIONAL_B_SPLINE_CURVE(bsc.getWeights())
					p6 = REPRESENTATION_ITEM('')
					curve = ListEntity(p0, p1, p2, p3, p4, p5, p6)
				else:
					curve = B_SPLINE_CURVE_WITH_KNOTS(name='', degree=bsc.Degree, points=points, form='UNSPECIFIED', closed=bsc.isClosed(), selfIntersecting=False, mults=bsc.getMultiplicities(), knots=bsc.getKnots(), form2='UNSPECIFIED')
				_curveBSplines[key] = curve
			return curve
		if (isinstance(bsc, Part.Line)):
			key = "%s,%s" %(bsc.Location, bsc.Direction)
			try:
				line = _lines[key]
			except:
				line = LINE('', None, None)
				line.pnt = _createCartesianPoint(bsc.Location)
				line.dir = _createVector(bsc.Direction)
				_lines[key] = line
			return line
	return None

def _createCurveIntInt(acisCurve):
    # TODO
	return acisCurve

def _createCurveP(acisCurve):
    # TODO
	return acisCurve

def _createCurveStraight(acisCurve):
	global _lines

	key = "%s,%s" %(acisCurve.root, acisCurve.dir)
	try:
		line = _lines[key]
	except:
		line = LINE('', None, None)
		line.pnt = _createCartesianPoint(acisCurve.root)
		line.dir = _createVector(acisCurve.dir)
		_lines[key] = line
	return line

def _createCurve(acisCurve):
	if (acisCurve is None):
		return None
	if (isinstance(acisCurve, Acis.CurveComp)):
		return _createCurveComp(acisCurve)
	if (isinstance(acisCurve, Acis.CurveDegenerate)):
		return _createCurveDegenerate(acisCurve)
	if (isinstance(acisCurve, Acis.CurveEllipse)):
		return _createCurveEllipse(acisCurve)
	if (isinstance(acisCurve, Acis.CurveInt)):
		return _createCurveInt(acisCurve)
	if (isinstance(acisCurve, Acis.CurveIntInt)):
		return _createCurveIntInt(acisCurve)
	if (isinstance(acisCurve, Acis.CurveP)):
		return _createCurveP(acisCurve)
	if (isinstance(acisCurve, Acis.CurveStraight)):
		return _createCurveStraight(acisCurve)
	raise AttributeError("Don't know how to create curve %s" %(acisCurve.__class__.__name__))

def _createCoEdge(acisCoEdge):
	acisEdge = acisCoEdge.getEdge()
	curve    = _createCurve(acisEdge.getCurve())
	if (curve is not None):
		oe = ORIENTED_EDGE((acisCoEdge.sense == 'forward'))
		p1      = _createVertexPoint(acisEdge.getStart())
		p2      = _createVertexPoint(acisEdge.getEnd())
		e       = _createEdgeCurve(p1, p2, curve, (acisEdge.sense == 'forward'))
		oe.edge = e
		return oe
	return None

def _createBoundaries(acisLoops):
	boundaries = []
	isouter = True
	for acisLoop in acisLoops:
		coedges = acisLoop.getCoEdges()
		edges = []
		for index in coedges:
			acisCoEdge = coedges[index]
			edge = _createCoEdge(acisCoEdge)
			if (edge is not None):
				edges.append(edge)
		if (len(edges) > 0):
			face = FACE_BOUND('', True)
			loop = EDGE_LOOP('', edges)
			face.wire = loop
			boundaries.append(face)
	return boundaries

def _calculateRef(axis):
	if (isEqual1D(axis.x, 1.0)):  return Acis.DIR_Y
	if (isEqual1D(axis.x, -1.0)): return -Acis.DIR_Y
	return Acis.DIR_X.cross(axis) # any perpendicular vector to normal?!?

def _createSurfaceBSpline(bss, acisSurface, sense):
	points = []
	for u in bss.getPoles():
		p = [_createCartesianPoint(v, 'Ctrl Pts') for v in u]
		points.append(p)
	if (bss.isURational()):
		p0 = BOUNDED_SURFACE()
		p1 = B_SPLINE_SURFACE(bss.UDegree, bss.VDegree, points, 'UNSPECIFIED', bss.isUClosed(), bss.isVClosed(), False)
		p2 = B_SPLINE_SURFACE_WITH_KNOTS(uMults=bss.getUMultiplicities(), vMults=bss.getVMultiplicities(), uKnots=bss.getUKnots(), vKnots=bss.getVKnots(), form2='UNSPECIFIED')
		p3 = GEOMETRIC_REPRESENTATION_ITEM()
		p4 = RATIONAL_B_SPLINE_SURFACE(bss.getWeights())
		p5 = REPRESENTATION_ITEM('')
		p6 = SURFACE()
		spline = ListEntity(p0, p1, p2, p3, p4, p5, p6)
	else:
		spline = B_SPLINE_SURFACE_WITH_KNOTS(name='', uDegree=bss.UDegree, vDegree=bss.VDegree, points=points, form='UNSPECIFIED', uClosed=bss.isUClosed(), vClosed=bss.isVClosed(), selfIntersecting=False, uMults=bss.getUMultiplicities(), vMults=bss.getVMultiplicities(), uKnots=bss.getUKnots(), vKnots=bss.getVKnots(), form2='UNSPECIFIED')
	spline.__acis__ = acisSurface
	return spline, sense == 'forward'

def _createSurfaceCone(center, axis, cosine, sine, major, sense):
	global _cones
	key = "%s,%s,%s,%s,%s,%s" %(center, axis, major, cosine, sine, major)
	try:
		cone = _cones[key]
	except:
		if (cosine * sine < 0):
			plc = _createAxis2Placement3D('', center, 'Origin', axis.negative(), 'center_axis',  major, 'ref_axis')
		else:
			plc = _createAxis2Placement3D('', center, 'Origin', axis, 'center_axis',  major, 'ref_axis')
		radius = major.Length
		if (isEqual1D(sine, 0.0)):
			cone = CYLINDRICAL_SURFACE('', plc, radius)
		else:
			angle = math.fabs(math.asin(sine))
			cone  = CONICAL_SURFACE('', plc, radius, angle)
		_cones[key] = cone
	if( cosine < 0.0):
		return cone, (sense != 'forward')
	return cone, (sense == 'forward')

def _createSurfaceCylinder(center, axis, radius, sense):
	global _cylinders
	key = "%s,%s,%s" %(center, axis, radius)
	try:
		cylinder = _cylinders[key]
	except:
		ref = _calculateRef(axis)
		plc = _createAxis2Placement3D('', center, 'Origin', axis, 'center_axis',  ref, 'ref_axis')
		cylinder = CYLINDRICAL_SURFACE('', plc, radius)
		_cylinders[key] = cylinder
	return cylinder, (sense == 'forward')

def _createSurfacePlane(center, axis, sense):
	global _planes

	key = "%s,%s" %(center, axis)
	try:
		plane = _planes[key]
	except:
		ref = _calculateRef(axis)
		plane = PLANE('', None)
		plane.placement = _createAxis2Placement3D('', center, 'Origin', axis, 'center_axis', ref, 'ref_axis')
		_planes[key] = plane
	return plane, sense == 'forward'

def _createSurfaceRevolution(curve, center, axis, sense):
	ref = _calculateRef(axis)
	revolution = SURFACE_OF_REVOLUTION('', None, None)
	revolution.curve = _createCurve(curve)
	revolution.placement =  _createAxis2Placement3D('', center, 'Origin', axis, 'center_axis', ref, 'ref_axis')
	return revolution, (sense == 'forward')

def _createSurfaceSphere(origin, radius, center, sense):
	global _spheres
	key = "%s,%r" %(origin, radius)
	try:
		sphere = _spheres[key]
	except:
		sphere = SPHERICAL_SURFACE('', None, radius)
		ref = _calculateRef(axis)
		sphere.placement = _createAxis2Placement3D('', origin, 'Origin', center, 'center_axis', ref, 'ref_axis')
		_spheres[key] = sphere
	return sphere, (sense == 'forward')

def _createSurfaceToroid(major, minor, center, axis, sense):
	torus = TOROIDAL_SURFACE('', None, major, math.fabs(minor))
	ref = _calculateRef(axis)
	torus.placement = _createAxis2Placement3D('', center, 'Origin', axis, 'center_axis', ref, 'ref_axis')
	if (minor < 0.0): return torus, (sense != 'forward')
	return torus, (sense == 'forward')

def _createSurfaceFaceShape(acisFace, shape):
	surface = acisFace._surface.getSurface()
	if (isinstance(surface, Acis.SurfaceCone)):
		return _createSurfaceCone(surface.center, surface.axis, surface.cosine, surface.sine, surface.major, acisFace.sense)
	if (isinstance(surface, Acis.SurfacePlane)):
		return _createSurfacePlane(surface.root, surface.normal, acisFace.sense)
	if (isinstance(surface, Acis.SurfaceSphere)):
		return _createSurfaceSphere(surface.center, surface.radius, surface.pole, acisFace.sense)
	if (isinstance(surface, Acis.SurfaceTorus)):
		return _createSurfaceToroid(surface.major, surface.minor, surface.center, surface.axis, acisFace.sense)
	if (isinstance(shape, Part.BSplineSurface)):
		return _createSurfaceBSpline(shape, surface, acisFace.sense)
#	if (isinstance(shape, Part.Mesh)):
#		return _createSurfaceMesh(shape, acisFace.sense)
	if (isinstance(shape, Part.Cone)):
		return _createSurfaceCone(surface.center, surface.axis, surface.cosine, surface.sine, surface.major, acisFace.sense)
	if (isinstance(shape, Part.Cylinder)):
		return _createSurfaceCylinder(shape.Center, shape.Axis, shape.Radius, acisFace.sense)
	if (isinstance(shape, Part.Plane)):
		return _createSurfacePlane(shape.Position, shape.Axis, acisFace.sense)
	if (isinstance(shape, Part.Sphere)):
		return _createSurfaceSphere(surface.center, surface.radius, surface.pole, acisFace.sense)
	if (isinstance(shape, Part.SurfaceOfRevolution)):
		return _createSurfaceRevolution(surface.profile, surface.center, surface.axis, acisFace.sense)
	if (isinstance(shape, Part.Toroid)):
		return _createSurfaceToroid(surface.major, surface.minor, surface.center, surface.axis, acisFace.sense)
	logWarning("Can't export surface '%s.%s'!" %(shape.__class__.__module__, shape.__class__.__name__))
	return None

def _createSurface(acisFace):
	faces = []
	shape = acisFace.build() # will Return Face!
	if (shape):
		for face in shape.Faces:
			f = _createSurfaceFaceShape(acisFace, face.Surface)
			if (f):
				faces.append(f)
	return faces

def _convertFace(acisFace, representation, parentColor, context):
	color = getColor(acisFace)
	if (color is None):
		color = parentColor
	shells = []
	faces = _createSurface(acisFace)
	for surface, sense in faces:
		face = ADVANCED_FACE('', surface, sense)
		face.bounds = _createBoundaries(acisFace.getLoops())
		assignColor(color, face, context)
		shells.append(face)

	return shells

def _convertShell(acisShell, representation, shape, parentColor):
	# FIXME how to distinguish between open or closed shell?
	faces = acisShell.getFaces()
	if (len(faces) > 0):
		color = getColor(acisShell)
		defColor = parentColor if (color is None) else color
		shell = OPEN_SHELL('',[])

		for acisFace in faces:
			faces = _convertFace(acisFace, representation, defColor, representation.context)
			shell.faces += faces

			assignColor(defColor, shell, representation.context)
		return shell

	return None

def _convertLump(acisLump, name, appContext, parentColor):

	name = "%s_L_%02d" %(name, acisLump.index)
	shape = SHAPE_DEFINITION_REPRESENTATION(name, appContext)

	shapeRepresentation = SHAPE_REPRESENTATION()
	lump = SHELL_BASED_SURFACE_MODEL()
	shapeRepresentation.items.append(lump)
	unit = _createUnit(1e-7)
	shapeRepresentation.context = unit

	shape.representation = shapeRepresentation
	color = getColor(acisLump)
	defColor = parentColor if (color is None) else color
	for acisShell in acisLump.getShells():
		shell = _convertShell(acisShell, shapeRepresentation, shape, defColor)
		if (shell is not None):
			lump.items.append(shell)

	assignColor(defColor, lump, unit)

	return shape

def _convertBody(acisBody, appPrtDef):
	bodies = []

	name = acisBody.getName()
	if ((name is None) or (len(name) == 0)):
		name = "Body_%02d" %(acisBody.index)

	for acisLump in acisBody.getLumps():
		shape = _convertLump(acisLump, name, appPrtDef.application, getColor(acisBody))
		if (shape is not None):
			bodies.append(shape.getProduct())

	return bodies

def _initExport():
	global _pointsVertex, _pointsCartesian, _directions, _vectors
	global _edgeCurves, _lines, _ellipses, _curveBSplines
	global _cones, _cylinders, _planes, _spheres
	global _assignments
	global _colorPalette
	global _entities

	_pointsVertex.clear()
	_pointsCartesian.clear()
	_directions.clear()
	_edgeCurves.clear()
	_lines.clear()
	_ellipses.clear()
	_vectors.clear()
	_cones.clear()
	_cylinders.clear()
	_planes.clear()
	_spheres.clear()
	_curveBSplines.clear()
	_assignments.clear()
	_colorPalette.clear()
	_entities[:]= []
	return

def _finalizeExport():
	global _pointsVertex, _pointsCartesian, _directions, _vectors
	global _edgeCurves, _lines, _ellipses, _curveBSplines
	global _cones, _cylinders, _planes, _spheres
	global _assignments
	global _colorPalette
	global _entities

	_pointsVertex.clear()
	_pointsCartesian.clear()
	_directions.clear()
	_edgeCurves.clear()
	_lines.clear()
	_ellipses.clear()
	_vectors.clear()
	_cones.clear()
	_cylinders.clear()
	_planes.clear()
	_spheres.clear()
	_curveBSplines.clear()
	_assignments.clear()
	_entities[:] = []

def _setExported(l, b):
	if ((type(l) == dict) or (type(l) == list)):
		for p in l:
			if (isinstance(p, ExportEntity)):
				p.isexported = b
			else:
				l[p].isexported = b
	if (isinstance(l, ExportEntity)):
		l.isexported = b

def _exportList(l):
	step = u''
	if (type(l) == list):
		d = l
	else:
		d = l.values()
	for p in d:
		step += p.exportSTEP()
	return step

def _createGeometricRepresentationList(*entities):
	return (GEOMETRIC_REPRESENTATION_CONTEXT(len(entities)),) + entities

#############################################################
# global classes
#############################################################

class E(object):
	def __init__(self, value):
		self.value = str(value).upper()
	def __str__(self):
		return self.value
	def __repr__(self):
		return u".%s." %(self.value)

class AnyEntity(object):
	def __init__(self):
		super(AnyEntity, self).__init__()
	def __repr__(self):
		return '*'

class AnonymEntity(object):
	def __init__(self):
		global _entities
		self.id = len(_entities) + 1
		_entities.append(self)
	def _getParameters(self):
		return []
	def _getClassName(self):
		return ""
	def getAttribute(self):
		l = [_obj2str(p) for p in self._getParameters()]
		return "%s(%s)" %(self._getClassName(), ",".join(l))
	def toString(self):
		l = [_obj2str(p) for p in self._getParameters()]
		return "%s(%s)" %(self._getClassName(), ",".join(l))
	def __str__(self):
		return self.toString()
	def __repr__(self):
		l = [_obj2str(p) for p in self._getParameters()]
		return u"#%d\t= %s(%s)" %(self.id, self._getClassName(), ",".join(l))

class ExportEntity(AnonymEntity):
	def __init__(self):
		super(ExportEntity, self).__init__()
		self.isexported = False
	def _getClassName(self):
		return self.__class__.__name__
	def exportProperties(self):
		step = u""
		variables = self._getParameters()
		for k in variables:
			try:
				a = k
				if (isinstance(a, ReferencedEntity)):
					step += a.exportSTEP()
				elif (type(a) == list):
					step += _exportList_(a)
				elif (type(a) == tuple):
					step += _exportList_(a)
			except:
				logError(traceback.format_exc())
		return step
	def exportSTEP(self):
		if (self.isexported):
			return ''
		step = u""
		if (hasattr(self, '__acis__')):
			if (self.__acis__.subclass == 'ref'):
				step += u"/*\n * ref = %d\n */\n" %(self.__acis__.ref)
			else:
				step += u"/*\n * $%d\n */\n" %(self.__acis__.index)
		step += u"%s;\n" %(self.__repr__())
		step += self.exportProperties()
		self.isexported = True
		return step

class ReferencedEntity(ExportEntity):
	def __init__(self):
		super(ReferencedEntity, self).__init__()
	def __str__(self):
		return '#%d' %(self.id)
	def _getClassName(self):
		return self.__class__.__name__

class NamedEntity(ReferencedEntity):
	def __init__(self, name = ''):
		super(NamedEntity, self).__init__()
		self.name = name
	def _getParameters(self):
		return super(NamedEntity, self)._getParameters() + [self.name]

class COLOUR_RGB(NamedEntity):
	def __init__(self, name = '', red = 0.749019607843137, green = 0.749019607843137, blue = 0.749019607843137):
		super(COLOUR_RGB, self).__init__(name)
		self.red   = red
		self.green = green
		self.blue  = blue
	def _getParameters(self):
		return super(COLOUR_RGB, self)._getParameters() + [self.red, self.green, self.blue]

class FILL_AREA_STYLE_COLOUR(NamedEntity):
	def __init__(self, color):
		super(FILL_AREA_STYLE_COLOUR, self).__init__()
		self.colour = color
	def _getParameters(self):
		return super(FILL_AREA_STYLE_COLOUR, self)._getParameters() + [self.colour]

class FILL_AREA_STYLE(NamedEntity):
	def __init__(self, color):
		super(FILL_AREA_STYLE, self).__init__()
		self.styles = [FILL_AREA_STYLE_COLOUR(color)]
	def _getParameters(self):
		return super(FILL_AREA_STYLE, self)._getParameters() + [self.styles]

class SURFACE_STYLE_FILL_AREA(ReferencedEntity):
	def __init__(self, color):
		super(SURFACE_STYLE_FILL_AREA, self).__init__()
		self.style = FILL_AREA_STYLE(color)
	def _getParameters(self):
		return super(SURFACE_STYLE_FILL_AREA, self)._getParameters() + [self.style]

class SURFACE_SIDE_STYLE(NamedEntity):
	def __init__(self, color):
		super(SURFACE_SIDE_STYLE, self).__init__()
		self.styles = [SURFACE_STYLE_FILL_AREA(color)]
	def _getParameters(self):
		return super(SURFACE_SIDE_STYLE, self)._getParameters() + [self.styles]

class SURFACE_STYLE_USAGE(ReferencedEntity):
	def __init__(self, color):
		super(SURFACE_STYLE_USAGE, self).__init__()
		self.sides = _getE('BOTH')
		self.style = SURFACE_SIDE_STYLE(color)
	def _getParameters(self):
		return super(SURFACE_STYLE_USAGE, self)._getParameters() + [self.sides, self.style]

class PRESENTATION_STYLE_ASSIGNMENT(ReferencedEntity):
	def __init__(self, color):
		super(PRESENTATION_STYLE_ASSIGNMENT, self).__init__()
		self.styles = [SURFACE_STYLE_USAGE(color)]
	def _getParameters(self):
		return super(PRESENTATION_STYLE_ASSIGNMENT, self)._getParameters() + [self.styles]

class APPLICATION_CONTEXT(NamedEntity):
	def __init__(self, name = 'Core Data for Automotive Mechanical Design Process'):
		super(APPLICATION_CONTEXT, self).__init__(name)

class APPLICATION_PROTOCOL_DEFINITION(NamedEntity):
	def __init__(self, name = 'international standard'):
		super(APPLICATION_PROTOCOL_DEFINITION, self).__init__(name)
		self.schema      = 'automotive_design'
		self.year        = 2009
		self.application = APPLICATION_CONTEXT()
	def _getParameters(self):
		return super(APPLICATION_PROTOCOL_DEFINITION, self)._getParameters() + [self.schema, self.year, self.application]

class PRODUCT_RELATED_PRODUCT_CATEGORY(NamedEntity):
	def __init__(self, name, products):
		super(PRODUCT_RELATED_PRODUCT_CATEGORY, self).__init__(name)
		self.description = None
		self.products = products
	def _getParameters(self):
		return super(PRODUCT_RELATED_PRODUCT_CATEGORY, self)._getParameters() + [self.description, self.products]

class PRODUCT(ReferencedEntity):
	def __init__(self, name, context = APPLICATION_CONTEXT()):
		super(PRODUCT, self).__init__()
		self.identifyer = name
		self.name = name
		self.description = ''
		self.frames = [PRODUCT_CONTEXT('', context, 'mechanical')]
	def _getParameters(self):
		return super(PRODUCT, self)._getParameters() + [self.identifyer, self.name, self.description, self.frames]

class PRODUCT_CONTEXT(NamedEntity):
	def __init__(self, name = 'part definition', frame = None, discipline = 'mechanical'):
		super(PRODUCT_CONTEXT, self).__init__(name)
		self.frame      = frame
		self.discipline = discipline
	def _getParameters(self):
		return super(PRODUCT_CONTEXT, self)._getParameters() + [self.frame, self.discipline]

class DIRECTION(NamedEntity):
	def __init__(self, name = '', direction = [0.0, 0.0, 0.0]):
		super(DIRECTION, self).__init__(name)
		self.direction = direction
	def _getParameters(self):
		return super(DIRECTION, self)._getParameters() + [self.direction]

class VECTOR(NamedEntity):
	def __init__(self, name, orientation, magnitude):
		super(VECTOR, self).__init__(name)
		self.orientation = orientation
		self.magnitude   = magnitude
	def _getParameters(self):
		return super(VECTOR, self)._getParameters() + [self.orientation, self.magnitude]

class CARTESIAN_POINT(NamedEntity):
	def __init__(self, name = '', coordinates = [0.0, 0.0, 0.0]):
		super(CARTESIAN_POINT, self).__init__(name)
		self.coordinates = coordinates
	def _getParameters(self):
		return super(CARTESIAN_POINT, self)._getParameters() + [self.coordinates]

class VERTEX_POINT(NamedEntity):
	def __init__(self, name, point):
		super(VERTEX_POINT, self).__init__(name)
		self.point = point
	def _getParameters(self):
		return super(VERTEX_POINT, self)._getParameters() + [self.point]

class LINE(NamedEntity):
	def __init__(self, name, pnt, dir):
		super(LINE, self).__init__(name)
		self.pnt = pnt
		self.dir = dir
	def _getParameters(self):
		return super(LINE, self)._getParameters() + [self.pnt, self.dir]

class CIRCLE(NamedEntity):
	def __init__(self, name, placement, radius):
		super(CIRCLE, self).__init__(name)
		self.placement = placement
		self.radius    = radius
	def _getParameters(self):
		return super(CIRCLE, self)._getParameters() + [self.placement, self.radius]

class ELLIPSE(NamedEntity):
	def __init__(self, name, placement, axis1, axis2):
		super(ELLIPSE, self).__init__(name)
		self.placement = placement
		self.axis1     = axis1
		self.axis2     = axis2
	def _getParameters(self):
		return super(ELLIPSE, self)._getParameters() + [self.placement, self.axis1, self.axis2]

class AXIS1_PLACEMENT(NamedEntity):
	def __init__(self, name='', location=None, axis=None):
		super(AXIS1_PLACEMENT, self).__init__(name)
		self.location  = location
		self.axis      = axis
	def _getParameters(self):
		return super(AXIS1_PLACEMENT, self)._getParameters() + [self.location, self.axis]

class AXIS2_PLACEMENT_3D(AXIS1_PLACEMENT):
	def __init__(self, name='', location=None, axis=None, direction=None):
		super(AXIS2_PLACEMENT_3D, self).__init__(name, location, axis)
		self.direction = direction
	def _getParameters(self):
		return super(AXIS2_PLACEMENT_3D, self)._getParameters() + [self.direction]

class ListEntity(ReferencedEntity):
	def __init__(self, *entities):
		super(ListEntity, self).__init__()
		self.entities = entities
	def _getClassName(self):
		return ""
	def _getParameters(self):
		params = super(ListEntity, self)._getParameters() + [self.entities]
		params = sorted(params)
		return params
	def exportSTEP(self):
		if (self.isexported):
			return ''
		step = u""
		if (hasattr(self, '__acis__')):
			if (self.__acis__.subclass == 'ref'):
				step += u"/*\n * ref = %d\n */\n" %(self.__acis__.ref)
			else:
				step += u"/*\n * $%d\n */\n" %(self.__acis__.index)
		step += u"%r;\n" %(self)
		for e in self.entities:
			try:
				if (isinstance(e, ExportEntity)):
					step += e.exportProperties()
				elif (type(e) == list):
					step += _exportList_(e)
				elif (type(e) == tuple):
					step += _exportList_(e)
			except:
				logError(traceback.format_exc())
		self.isexported = True
		return step
	def __repr__(self):
		return u"#%d\t= (%s)" %(self.id, " ".join(["%s" % (e.toString()) for e in self.entities]))

class NamedListEntity(ListEntity):
	def __init__(self, entities):
		super(NamedListEntity, self).__init__(entities)

class NAMED_UNIT(ExportEntity):
	def __init__(self, dimensions):
		super(NAMED_UNIT, self).__init__()
		self.dimensions = dimensions
		self.isexported = True
	def _getParameters(self):
		l = super(NAMED_UNIT, self)._getParameters()
		if (self.dimensions is not None):
			l += [self.dimensions]
		return l

class LENGTH_UNIT(NAMED_UNIT):
	def __init__(self, dimensions):
		super(LENGTH_UNIT, self).__init__(dimensions)

class SOLID_ANGLE_UNIT(NAMED_UNIT):
	def __init__(self, dimensions):
		super(SOLID_ANGLE_UNIT, self).__init__(dimensions)

class SI_UNIT(NAMED_UNIT):
	def __init__(self, name, prefix):
		super(SI_UNIT, self).__init__(None)
		self.name   = _getE(name)
		self.prefix = _getE(prefix)
	def _getParameters(self):
		return [self.name, self.prefix]

class PLANE_ANGLE_UNIT(NAMED_UNIT):
	def __init__(self, dimensions):
		super(PLANE_ANGLE_UNIT, self).__init__(dimensions)

class CONVERSION_BASED_UNIT(NAMED_UNIT):
	def __init__(self, name, factor):
		super(CONVERSION_BASED_UNIT, self).__init__(factor)
		self.name   = name
	def _getParameters(self):
		return [self.name] + super(CONVERSION_BASED_UNIT, self)._getParameters()

class ValueObject(ExportEntity):
	def __init__(self, value):
		super(ValueObject, self).__init__()
		self.value = value
	def _getParameters(self):
		return super(ValueObject, self)._getParameters() + [self.value]

class PLANE_ANGLE_MEASURE(ValueObject):
	def __init__(self, value):
		super(PLANE_ANGLE_MEASURE, self).__init__(value)

class GEOMETRIC_REPRESENTATION_CONTEXT(ValueObject):
	def __init__(self, value):
		super(GEOMETRIC_REPRESENTATION_CONTEXT, self).__init__(value)
		self.isexported = True

class LENGTH_MEASURE(ValueObject):
	def __init__(self, value):
		super(LENGTH_MEASURE, self).__init__(value)
		self.isexported = True

class UNCERTAINTY_MEASURE_WITH_UNIT(ReferencedEntity):
	def __init__(self, value, length):
		super(UNCERTAINTY_MEASURE_WITH_UNIT, self).__init__()
		self.value = LENGTH_MEASURE(value)
		self.length = length
		self.name = 'DISTANCE_ACCURACY_VALUE'
		self.description = 'Maximum model space distance between geometric entities at asserted connectivities'
	def _getParameters(self):
		return super(UNCERTAINTY_MEASURE_WITH_UNIT, self)._getParameters() + [self.value, self.length, self.name, self.description]

class GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT(ExportEntity):
	def __init__(self):
		super(GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT, self).__init__()
		self.units = []
		self.isexported = True
	def _getParameters(self):
		return super(GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT, self)._getParameters() + [self.units]

class GLOBAL_UNIT_ASSIGNED_CONTEXT(ExportEntity):
	def __init__(self):
		super(GLOBAL_UNIT_ASSIGNED_CONTEXT, self).__init__()
		self.assignments = []
		self.isexported = True
	def _getParameters(self):
		return super(GLOBAL_UNIT_ASSIGNED_CONTEXT, self)._getParameters() + [self.assignments]

class REPRESENTATION_CONTEXT(ExportEntity):
	def __init__(self, identifyer = '', t = '3D'):
		super(REPRESENTATION_CONTEXT, self).__init__()
		self.identifyer = identifyer
		self.type = t
		self.isexported = True
	def _getParameters(self):
		return super(REPRESENTATION_CONTEXT, self)._getParameters() + [self.identifyer, self.type]

class PLANE_ANGLE_MEASURE_WITH_UNIT(ReferencedEntity):
	def __init__(self, value):
		super(PLANE_ANGLE_MEASURE_WITH_UNIT, self).__init__()
		self.value = PLANE_ANGLE_MEASURE(value)
		self.unit  = UNIT((NAMED_UNIT(AnyEntity()), PLANE_ANGLE_UNIT(None), SI_UNIT(None, 'RADIAN')))
	def _getParameters(self):
		return super(PLANE_ANGLE_MEASURE_WITH_UNIT, self)._getParameters() + [self.value, self.unit]

class DIMENSIONAL_EXPONENTS(ReferencedEntity):
	def __init__(self, length = 0.0, mass = 0.0, time = 0.0, current = 0.0, temperature = 0.0, amount = 0.0, luminosity = 0.0):
		super(DIMENSIONAL_EXPONENTS, self).__init__()
		self.length      = length
		self.mass        = mass
		self.time        = time
		self.current     = current
		self.temperature = temperature
		self.amount      = amount
		self.luminosity = luminosity
	def _getParameters(self):
		return super(DIMENSIONAL_EXPONENTS, self)._getParameters() +[self.length, self.mass, self.time, self.current, self.temperature, self.amount, self.luminosity]

class UNIT(ListEntity):
	def __init__(self, units=()):
		super(UNIT, self).__init__(units)

class DATE_TIME_ROLE(NamedEntity):
	def __init__(self, name = 'creation_date'):
		super(DATE_TIME_ROLE, self).__init__(name)

class COORDINATED_UNIVERSAL_TIME_OFFSET(ReferencedEntity):
	def __init__(self, hour = 0, minute = 0, sense = 'BEHIND'):
		super(COORDINATED_UNIVERSAL_TIME_OFFSET, self).__init__()
		self.hour   = hour
		self.minute = minute
		self.sense  = _getE(sense)
	def _getParameters(self):
		return super(COORDINATED_UNIVERSAL_TIME_OFFSET, self)._getParameters() + [self.hour, self.minute, self.sense]

class LOCAL_TIME(ReferencedEntity):
	def __init__(self, hour, minute, seconds, zone):
		super(LOCAL_TIME, self).__init__()
		self.hour    = hour
		self.minute  = minute
		self.seconds = seconds
		self.zone    = zone
	def _getParameters(self):
		return super(LOCAL_TIME, self)._getParameters() + [self.hour, self.minute, self.seconds, self.zone]

class CALENDAR_DATE(ReferencedEntity):
	def __init__(self, year, month, day):
		super(CALENDAR_DATE, self).__init__()
		self.year  = year
		self.month = month
		self.day   = day
	def _getParameters(self):
		return super(CALENDAR_DATE, self)._getParameters() + [self.year, self.month, self.day]

class DATE_AND_TIME(ReferencedEntity):
	def __init__(self, dt):
		super(DATE_AND_TIME, self).__init__()
		self.date = CALENDAR_DATE(dt.year, dt.month, dt.day)
		zone = COORDINATED_UNIVERSAL_TIME_OFFSET()
		self.time  = LOCAL_TIME(dt.hour, dt.minute, dt.second + dt.microsecond/1e+6, zone)
	def _getParameters(self):
		return super(DATE_AND_TIME, self)._getParameters() + [self.date, self.time]

class APPLIED_DATE_AND_TIME_ASSIGNMENT(ReferencedEntity):
	def __init__(self, dt):
		super(APPLIED_DATE_AND_TIME_ASSIGNMENT, self).__init__()
		self.datetime = DATE_AND_TIME(dt)
		self.role = DATE_TIME_ROLE()
		self.products = []
	def _getParameters(self):
		return super(APPLIED_DATE_AND_TIME_ASSIGNMENT, self)._getParameters() + [self.datetime, self.role, self.products]

class PRODUCT_DEFINITION_SHAPE(NamedEntity):
	def __init__(self, name, context):
		super(PRODUCT_DEFINITION_SHAPE, self).__init__()
		self.description = ''
		self.definition  = PRODUCT_DEFINITION(name, context)
	def _getParameters(self):
		return super(PRODUCT_DEFINITION_SHAPE, self)._getParameters() + [self.description, self.definition]

class SHAPE_REPRESENTATION(NamedEntity):
	def __init__(self):
		super(SHAPE_REPRESENTATION, self).__init__('')
		self.items = []
		self.context = None
	def _getParameters(self):
		return super(SHAPE_REPRESENTATION, self)._getParameters() + [self.items, self.context]

class MANIFOLD_SURFACE_SHAPE_REPRESENTATION(SHAPE_REPRESENTATION):
	def __init__(self):
		super(MANIFOLD_SURFACE_SHAPE_REPRESENTATION, self).__init__()

class SHAPE_DEFINITION_REPRESENTATION(ReferencedEntity):
	def __init__(self, name, context):
		super(SHAPE_DEFINITION_REPRESENTATION, self).__init__()
		self.definition = PRODUCT_DEFINITION_SHAPE(name, context)
		self.representation = None
	def _getParameters(self):
		return super(SHAPE_DEFINITION_REPRESENTATION, self)._getParameters() + [self.definition, self.representation]
	def getProduct(self):
		return self.definition.definition.formation.product
	def getAppContext(self):
		return self.definition.definition.frame.context

class PRODUCT_DEFINITION_FORMATION(NamedEntity):
	def __init__(self, name, context):
		super(PRODUCT_DEFINITION_FORMATION, self).__init__('')
		self.description = ''
		self.product     = PRODUCT(name, context)
	def _getParameters(self):
		return super(PRODUCT_DEFINITION_FORMATION, self)._getParameters() + [self.description, self.product]

class PRODUCT_DEFINITION_CONTEXT(NamedEntity):
	def __init__(self, name = 'part definition', context = None, stage = 'design'):
		super(PRODUCT_DEFINITION_CONTEXT, self).__init__(name)
		self.context = context
		self.stage = stage
	def _getParameters(self):
		return super(PRODUCT_DEFINITION_CONTEXT, self)._getParameters() + [self.context, self.stage]

class PRODUCT_DEFINITION(NamedEntity):
	def __init__(self, name, context):
		super(PRODUCT_DEFINITION, self).__init__('design')
		self.description = ''
		self.formation   = PRODUCT_DEFINITION_FORMATION(name, context)
		self.frame       = PRODUCT_DEFINITION_CONTEXT('part definition', context, 'design')
	def _getParameters(self):
		return super(PRODUCT_DEFINITION, self)._getParameters() + [self.description, self.formation, self.frame]

class ItemsRepresentationEntity(NamedEntity):
	def __init__(self, name, items, context):
		super(ItemsRepresentationEntity, self).__init__(name)
		self.items   = items
		self.context = context
	def _getParameters(self):
		return super(ItemsRepresentationEntity, self)._getParameters() + [self.items, self.context]

class MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION(ItemsRepresentationEntity):
	def __init__(self, name, items, context):
		super(MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION, self).__init__(name, items, context)

class ADVANCED_BREP_SHAPE_REPRESENTATION(ItemsRepresentationEntity):
	def __init__(self, name, items, context):
		super(ADVANCED_BREP_SHAPE_REPRESENTATION, self).__init__(name, items, context)

class SHAPE_REPRESENTATION_RELATIONSHIP(NamedEntity):
	def __init__(self, name, description, rep1, rep2):
		super(SHAPE_REPRESENTATION_RELATIONSHIP, self).__init__(name)
		self.description = description
		self.rep1        = rep1
		self.rep2        = rep2
	def _getParameters(self):
		return super(SHAPE_REPRESENTATION_RELATIONSHIP, self)._getParameters() + [self.description, self.rep1, self.rep2]

class CLOSED_SHELL(NamedEntity):
	def __init__(self, name, faces):
		super(CLOSED_SHELL, self).__init__(name)
		self.faces = faces
	def _getParameters(self):
		return super(CLOSED_SHELL, self)._getParameters() + [self.faces]

class OPEN_SHELL(NamedEntity):
	def __init__(self, name, faces):
		super(OPEN_SHELL, self).__init__(name)
		self.faces = faces
	def _getParameters(self):
		return super(OPEN_SHELL, self)._getParameters() + [self.faces]

class SHELL_BASED_SURFACE_MODEL(NamedEntity):
	def __init__(self, ):
		super(SHELL_BASED_SURFACE_MODEL, self).__init__('')
		self.items = []
	def _getParameters(self):
		return super(SHELL_BASED_SURFACE_MODEL, self)._getParameters() + [self.items]

class MANIFOLD_SOLID_BREP(NamedEntity):
	def __init__(self, name, outer):
		super(MANIFOLD_SOLID_BREP, self).__init__(name)
		self.outer = outer
	def _getParameters(self):
		return super(MANIFOLD_SOLID_BREP, self)._getParameters() + [self.outer]

class STYLED_ITEM(NamedEntity):
	def __init__(self, name, styles, item):
		super(STYLED_ITEM, self).__init__(name)
		self.styles = styles
		self.item = item
	def _getParameters(self):
		return super(STYLED_ITEM, self)._getParameters() + [self.styles, self.item]

class EDGE_LOOP(NamedEntity):
	def __init__(self, name, edges):
		super(EDGE_LOOP, self).__init__(name)
		self.edges = edges
	def _getParameters(self):
		return super(EDGE_LOOP, self)._getParameters() + [self.edges]

class FACE_BOUND(NamedEntity):
	def __init__(self, name, bound):
		super(FACE_BOUND, self).__init__(name)
		self.wire = []
		self.bound = bound
	def _getParameters(self):
		return super(FACE_BOUND, self)._getParameters() + [self.wire, self.bound]

class FACE_OUTER_BOUND(NamedEntity):
	def __init__(self, name, wire, bound):
		super(FACE_OUTER_BOUND, self).__init__(name)
		self.wire = wire
		self.bound = bound
	def _getParameters(self):
		return super(FACE_OUTER_BOUND, self)._getParameters() + [self.wire, self.bound]

class ADVANCED_FACE(NamedEntity):
	def __init__(self, name, surface, bound):
		super(ADVANCED_FACE, self).__init__(name)
		self.bounds  = []
		self.surface = surface
		self.bound   = bound
	def _getParameters(self):
		return super(ADVANCED_FACE, self)._getParameters() + [self.bounds, self.surface, self.bound]

class PLANE(NamedEntity):
	def __init__(self, name, placement):
		super(PLANE, self).__init__(name)
		self.placement = placement
	def _getParameters(self):
		return super(PLANE, self)._getParameters() + [self.placement]

class CYLINDRICAL_SURFACE(NamedEntity):
	def __init__(self, name="", placement=None, radius=None):
		super(CYLINDRICAL_SURFACE, self).__init__(name)
		self.placement = placement
		self.radius    = radius
	def _getParameters(self):
		return super(CYLINDRICAL_SURFACE, self)._getParameters() + [self.placement, self.radius]

class CONICAL_SURFACE(NamedEntity):
	def __init__(self, name, placement, radius, angle):
		super(CONICAL_SURFACE, self).__init__(name)
		self.placement = placement
		self.axis1     = radius
		self.axis2     = angle
	def _getParameters(self):
		return super(CONICAL_SURFACE, self)._getParameters() + [self.placement, self.axis1, self.axis2]

class SPHERICAL_SURFACE(NamedEntity):
	def __init__(self, name, placement, radius):
		super(SPHERICAL_SURFACE, self).__init__(name)
		self.placement = placement
		self.radius    = radius
	def _getParameters(self):
		return super(SPHERICAL_SURFACE, self)._getParameters() + [self.placement, self.radius]

class TOROIDAL_SURFACE(NamedEntity):
	def __init__(self, name, placement, major, minor):
		super(TOROIDAL_SURFACE, self).__init__(name)
		self.placement = placement
		self.major     = major
		self.minor     = minor
	def _getParameters(self):
		return super(TOROIDAL_SURFACE, self)._getParameters() + [self.placement, self.major, self.minor]

class ORIENTED_EDGE(NamedEntity):
	def __init__(self, orientation):
		super(ORIENTED_EDGE, self).__init__('')
		self.start       = AnyEntity()
		self.end         = AnyEntity()
		self.edge        = None
		self.orientation = orientation
	def _getParameters(self):
		return super(ORIENTED_EDGE, self)._getParameters() + [self.start, self.end, self.edge, self.orientation]

class EDGE_CURVE(NamedEntity):
	def __init__(self, name, start, end, curve, sense):
		super(EDGE_CURVE, self).__init__(name)
		self.start = start
		self.end   = end
		self.curve = curve
		self.sense = sense
	def _getParameters(self):
		return super(EDGE_CURVE, self)._getParameters() + [self.start, self.end, self.curve, self.sense]

class CURVE(ReferencedEntity):
	def __init__(self, name=None):
		super(CURVE, self).__init__()
		self.name             = name

class BOUNDED_CURVE(CURVE):
	def __init__(self, name=None):
		super(BOUNDED_CURVE, self).__init__(name)

class RATIONAL_B_SPLINE_CURVE(ReferencedEntity):
	def __init__(self, weights):
		super(RATIONAL_B_SPLINE_CURVE, self).__init__()
		self.weights = weights
	def _getParameters(self):
		return super(RATIONAL_B_SPLINE_CURVE, self)._getParameters() + [self.weights]

class B_SPLINE_CURVE(ReferencedEntity):
	def __init__(self, name=None, degree=None, points=None, form=None, closed=None, selfIntersecting=None):
		super(B_SPLINE_CURVE, self).__init__()
		self.name             = name
		self.degree           = degree
		self.points           = points
		self.form             = _getE(form)
		self.closed           = closed
		self.selfIntersecting = selfIntersecting
	def _getParameters(self):
		l = super(B_SPLINE_CURVE, self)._getParameters()
		if (self.name             is not None): l.append(self.name)
		if (self.degree           is not None): l.append(self.degree)
		if (self.points           is not None): l.append(self.points)
		if (self.form             is not None): l.append(self.form)
		if (self.closed           is not None): l.append(self.closed)
		if (self.selfIntersecting is not None): l.append(self.selfIntersecting)
		return l

class B_SPLINE_CURVE_WITH_KNOTS(B_SPLINE_CURVE):
	def __init__(self, name=None, degree=None, points=None, form=None, closed=None, selfIntersecting=None, mults=None, knots=None, form2=None):
		super(B_SPLINE_CURVE_WITH_KNOTS, self).__init__(name, degree, points, form, closed, selfIntersecting)
		self.mults            = mults
		self.knots            = knots
		self.form2            = _getE(form2)
	def _getParameters(self):
		l = super(B_SPLINE_CURVE_WITH_KNOTS, self)._getParameters()
		if (self.mults            is not None): l.append(self.mults)
		if (self.knots            is not None): l.append(self.knots)
		if (self.form2            is not None): l.append(self.form2)
		return l

class SURFACE_OF_REVOLUTION(NamedEntity):
	def __init__(self, name=None, curve=None, position=None):
		super(SURFACE_OF_REVOLUTION, self).__init__('')
		self.curve     = curve
		self.placement = position
	def _getParameters(self):
		l = super(SURFACE_OF_REVOLUTION, self)._getParameters()
		if (self.curve     is not None): l.append(self.curve)
		if (self.placement is not None): l.append(self.placement)
		return l

class BOUNDED_SURFACE(ReferencedEntity):
	def __init__(self):
		super(BOUNDED_SURFACE, self).__init__()

class B_SPLINE_SURFACE(ReferencedEntity):
	def __init__(self, uDegree, vDegree, points, form, uClosed, vClosed, selfIntersecting):
		super(B_SPLINE_SURFACE, self).__init__()
		self.uDegree          = uDegree
		self.vDegree          = vDegree
		self.points           = points
		self.form             = _getE(form)
		self.vClosed          = vClosed
		self.uClosed          = uClosed
		self.selfIntersecting = selfIntersecting
	def _getParameters(self):
		return super(B_SPLINE_SURFACE, self)._getParameters() + [self.uDegree, self.vDegree, self.points, self.form, self.uClosed, self.vClosed, self.selfIntersecting]

class B_SPLINE_SURFACE_WITH_KNOTS(ReferencedEntity):
	def __init__(self, name=None, uDegree=None, vDegree=None, points=None, form=None, uClosed=None, vClosed=None, selfIntersecting=None, uMults=None, vMults=None, uKnots=None, vKnots=None, form2=None):
		super(B_SPLINE_SURFACE_WITH_KNOTS, self).__init__()
		self.name			  = name
		self.uDegree		  = uDegree
		self.vDegree		  = vDegree
		self.points			  = points
		self.form			  = _getE(form)
		self.uClosed		  = uClosed
		self.vClosed		  = vClosed
		self.selfIntersecting = selfIntersecting
		self.uMults           = uMults
		self.vMults           = vMults
		self.uKnots           = uKnots
		self.vKnots           = vKnots
		self.form2            = _getE(form2)
	def _getParameters(self):
		l = super(B_SPLINE_SURFACE_WITH_KNOTS, self)._getParameters()
		if (self.name             is not None): l.append(self.name)
		if (self.uDegree		  is not None): l.append(self.uDegree)
		if (self.vDegree		  is not None): l.append(self.vDegree)
		if (self.points			  is not None): l.append(self.points)
		if (self.form			  is not None): l.append(self.form)
		if (self.uClosed		  is not None): l.append(self.uClosed)
		if (self.vClosed		  is not None): l.append(self.vClosed)
		if (self.selfIntersecting is not None): l.append(self.selfIntersecting)
		if (self.uMults           is not None): l.append(self.uMults)
		if (self.vMults           is not None): l.append(self.vMults)
		if (self.uKnots           is not None): l.append(self.uKnots)
		if (self.vKnots           is not None): l.append(self.vKnots)
		if (self.form2            is not None): l.append(self.form2)
		return l

class GEOMETRIC_REPRESENTATION_ITEM(ReferencedEntity):
	def __init__(self):
		super(GEOMETRIC_REPRESENTATION_ITEM, self).__init__()

class SURFACE(ReferencedEntity):
	def __init__(self):
		super(SURFACE, self).__init__()

class RATIONAL_B_SPLINE_SURFACE(ReferencedEntity):
	def __init__(self, weights):
		super(RATIONAL_B_SPLINE_SURFACE, self).__init__()
		self.weights = weights
	def _getParameters(self):
		return super(RATIONAL_B_SPLINE_SURFACE, self)._getParameters() + [self.weights]

class REPRESENTATION_ITEM(NamedEntity):
	def __init__(self, name):
		super(REPRESENTATION_ITEM, self).__init__()

class GROUP(NamedEntity):
	def __init__(self, name = '', desc=None):
		super(GROUP, self).__init__(name)
		self.desc = desc
	def _getParameters(self):
		return super(GROUP, self)._getParameters() + [self.desc]

#############################################################
# Global functions
#############################################################

def export(filename, satHeader, satBodies):
	dt     = datetime.now() # 2018-05-13T08:03:27-07:00
	user   = getAuthor()
	desc   = getDescription()
	orga   = ''
	proc   = 'InventorImporter 0.9'
	auth   = ''

	_initExport()

	global _scale
	_scale = satHeader.scale

	appPrtDef = APPLICATION_PROTOCOL_DEFINITION()
	bodies = []
	for body in satBodies:
		bodies += _convertBody(body, appPrtDef)
	PRODUCT_RELATED_PRODUCT_CATEGORY('part', bodies)

	path, f = os.path.split(filename)
	name, x = os.path.splitext(f)
	path = getDumpFolder().replace('\\', '/')
	stepfile = "%s/%s.step" %(path, name)

	step = u"ISO-10303-21;\n"
	step += u"HEADER;\n"
	step += u"FILE_DESCRIPTION(('FreeCAD Model'),'2;1');\n"
	step += u"FILE_NAME('%s'," %(stepfile)
	step += u"'%s'," %(dt.strftime("%Y-%m-%dT%H:%M:%S"))
	if (sys.version_info.major < 3):
		step += u"('%s')," %(user.decode('utf8'))
	else:
		step += u"('%s')," %(user)
	step += u"('%s')," %(orga)
	step += u"'%s'," %(proc)
	step += u"'FreeCAD','%s');\n" %(auth)
	step += u"FILE_SCHEMA (('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1}'));\n"
	step += u"ENDSEC;\n"
	step += u"\n"
	step += u"DATA;\n"

	step += _exportList(_entities)

	step += u"ENDSEC;\n"
	step += u"END-ISO-10303-21;"

	with io.open(stepfile, 'wt', encoding="UTF-8") as stepFile:
		stepFile.write(step)
#		logAlways(u"STEP file written to '%s'.", stepfile)
		logInfo(u"STEP file written to '%s'.", stepfile)

	_finalizeExport()

	return stepfile
