# -*- coding: utf-8 -*-

'''
Acis2Step.py:
'''

from datetime      import datetime
from importerUtils import isEqual
from FreeCAD       import Vector as VEC
from importerUtils import logWarning, logError, logAlways, isEqual1D, getAuthor, getDescription
import traceback, inspect, os, Acis, math, re, Part

#############################################################
# private variables
#############################################################

_entityId        = 10
_pointsVertex    = {}
_pointsCartesian = {}
_directions      = {}
_edgeCurves      = {}
_lines           = {}
_ellipses        = {}
_vectors         = {}
_cones           = {}
_planes          = {}
_spheres         = {}
_toroids         = {}
_curveBSplines   = {}
_surfaceBSplines = []
_axisPlacements  = []
_orientedEdges   = []
_edgeLoops       = []
_faceBounds      = []
_faceOuterBounds = []
_advancedFaces   = {}
_representations = []
_assignments     = {}
_lumpCounter     = 0

#############################################################
# private functions
#############################################################

def _getE(o):
	if (isinstance(o, E)): return o
	if (o is None): return None
	return E(o)

def _dbl2str(d):
	if (d == 0.0):
		return "0."
	if (math.fabs(d) > 1e5):
		s = ('%E' % d).split('E')
		return s[0].rstrip('0') + 'E+' + s[1][1:].lstrip('0')
	if (math.fabs(d) < 1e-5):
		s = ('%E' % d).split('E')
		return s[0].rstrip('0') + 'E-' + s[1][1:].lstrip('0')
	s = "%r" %(d)
	return s.rstrip('0')

def _bool2str(v):
	return '.T.' if v else '.F.'

def _int2str(i):
	return '%d' %(i)

def _str2str(s):
	if (s is None):
		return '$'
	return "'%s'" %(s)

def _enum2str(e):
	return "%r" %(e)

def _entity2str(e):
	if (isinstance(e, AnonymEntity)):
		return '%s' %(e)
	return '*'

def _lst2str(l):
	return "(%s)" %(",".join([_obj2str(i) for i in l]))

def _obj2str(o):
	if (o is None):                   return _str2str(o)
	if (type(o) == int):              return _int2str(o)
	if (type(o) == long):             return _int2str(o)
	if (type(o) == float):            return _dbl2str(o)
	if (type(o) == bool):             return _bool2str(o)
	if (type(o) == str):              return _str2str(o)
	if (type(o) == unicode):          return _str2str(o)
	if (isinstance(o, AnyEntity)):    return "*"
	if (isinstance(o, E)):            return _enum2str(o)
	if (isinstance(o, AnonymEntity)): return _entity2str(o)
	if (type(o) == list):             return _lst2str(o)
	if (type(o) == tuple):            return _lst2str(o)
	raise Exception("Don't know how to convert '%s' into a string!" %(o.__class__.__name__))
def _values3D(v):
	return [v.x, v.y, v.z]

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
	global _axisPlacements
	plc = AXIS1_PLACEMENT(name, None, None)
	plc.location  = _createCartesianPoint(aPt, aName)
	plc.axis      = _createDirection(bPt, bName)
	_axisPlacements.append(plc)
	return plc

def _createAxis2Placement3D(name, aPt, aName, bPt, bName, cPt, cName):
	global _axisPlacements
	plc = AXIS2_PLACEMENT_3D(name, None, None, None)
	plc.location  = _createCartesianPoint(aPt, aName)
	plc.axis      = _createDirection(bPt, bName)
	plc.direction = _createDirection(cPt, cName)
	_axisPlacements.append(plc)
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
	return curve
def _createCurveDegenerate(acisCurve):
	return curve
def _createCurveEllipse(acisCurve):
	global _ellipses
	key = '%s,%s,%s,%s' %(acisCurve.center, acisCurve.normal, acisCurve.major, acisCurve.ratio)
	try:
		circle = _ellipses[key]
	except:
		if (isEqual1D(acisCurve.ratio, 1.0)):
			circle = CIRCLE('', None, acisCurve.major.Length)
		else:
			axis1 = acisCurve.major.Length
			circle = ELLIPSE('', None, axis1, axis1 * acisCurve.ratio)
		circle.placement = _createAxis2Placement3D('', acisCurve.center, 'Origin', acisCurve.normal, 'center_axis', acisCurve.major, 'ref_axis')
		_ellipses[key] = circle
	return circle
def _createCurveInt(acisCurve):
	global _curveBSplines
	shape = acisCurve.getShape()
	if (shape is not None):
		bsc = shape.Curve
		if (isinstance(bsc, Part.BSplineCurve)):
			points = [_createCartesianPoint(v, 'Ctrl Pts') for v in bsc.getPoles()]
			key = "(%s),(%s),(%s)" %(",".join(["#%d"%(p.id) for p in points]), ",".join(["%d" %(d) for d in bsc.getMultiplicities()]), ",".join(["%r" %(r) for r in bsc.getKnots()]))
			try:
				curve = _curveBSplines[key]
			except:
				if (bsc.isRational()):
					params = (
						BOUNDED_CURVE(),
						B_SPLINE_CURVE(name=None, degree=bsc.Degree, points=points, form='UNSPECIFIED', closed=bsc.isClosed(), selfIntersecting=False),
						B_SPLINE_CURVE_WITH_KNOTS(mults=bsc.getMultiplicities(), knots=bsc.getKnots(), form2='UNSPECIFIED'),
						CURVE(),
						GEOMETRIC_REPRESENTATION_ITEM(),
						RATIONAL_B_SPLINE_CURVE(bsc.getWeights()),
						REPRESENTATION_ITEM(''))
					curve = ListEntity(params)
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
	logError(u"Int-Curve not created for (%s)", acisCurve.__str__()[:-1])
	return None
def _createCurveIntInt(acisCurve):
	return curve
def _createCurveP(acisCurve):
	return curve
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
		p1       = _createVertexPoint(acisEdge.getStart())
		p2       = _createVertexPoint(acisEdge.getEnd())
		e        = _createEdgeCurve(p1, p2, curve, (acisEdge.sense == 'forward'))
		oe = ORIENTED_EDGE('', AnyEntity(), AnyEntity(), e, (acisCoEdge.sense == 'forward'))
		_orientedEdges.append(oe)
		return oe
	return None

def _createBoundaries(acisLoops):
	boundaries = []
	isouter = True
	for acisLoop in acisLoops:
		loop = EDGE_LOOP('', [])
		coedges = acisLoop.getCoEdges()
		if (len(coedges) > 0):
			for acisCoEdge in coedges:
				edge = _createCoEdge(acisCoEdge)
				if (edge is not None):
					loop.edges.append(edge)
		if (len(loop.edges) > 0):
			_edgeLoops.append(loop)
			face = FACE_BOUND('', loop, True)
			boundaries.append(face)
			_faceBounds.append(face)
	return boundaries

def _createSurfaceCone(acisSurface):
	global _cones
	key = "%s,%s,%s,%s,%s" %(acisSurface.center, acisSurface.axis, acisSurface.major, acisSurface.ratio, acisSurface.sine)
	try:
		cone = _cones[key]
	except:
		if (acisSurface.cosine * acisSurface.sine < 0):
			plc    = _createAxis2Placement3D('', acisSurface.center, 'Origin', acisSurface.axis.negative(), 'center_axis',  acisSurface.major, 'ref_axis')
		else:
			plc    = _createAxis2Placement3D('', acisSurface.center, 'Origin', acisSurface.axis, 'center_axis',  acisSurface.major, 'ref_axis')
		radius = acisSurface.major.Length
		if (isEqual1D(acisSurface.sine, 0.0)):
			cone = CYLINDRICAL_SURFACE('', plc, radius)
		else:
			angle  = math.degrees(math.asin(acisSurface.sine))
			cone = CONICAL_SURFACE('', plc, radius, math.fabs(angle))
		_cones[key] = cone
	return cone
def _createSurfaceMesh(acisSurface):
	return surface
def _createSurfacePlane(acisSurface):
	global _planes

	key = "%s,%s" %(acisSurface.root, acisSurface.normal)
	try:
		plane = _planes[key]
	except:
		if (isEqual1D(acisSurface.normal.x, 1.0)):
			ref = VEC(0.0, 1.0, 0.0)
		elif (isEqual1D(acisSurface.normal.x, -1.0)):
			ref = VEC(0.0, -1.0, 0.0)
		else:
			ref = acisSurface.normal.cross(VEC(-1, 0, 0)) # any perpendicular vector to normal?!?
		plane = PLANE('', None)
		plane.placement = _createAxis2Placement3D('', acisSurface.root, 'Origin', acisSurface.normal, 'center_axis', ref, 'ref_axis')
		_planes[key] = plane
	return plane
def _createSurfaceSphere(acisSurface):
	global _spheres
	key = "%s,%r" %(acisSurface.center, acisSurface.radius)
	try:
		sphere = _spheres[key]
	except:
		sphere = SPHERICAL_SURFACE('', None, acisSurface.radius)
		sphere.placement = _createAxis2Placement3D('', acisSurface.center, 'Origin', acisSurface.pole, 'center_axis', acisSurface.uvorigin, 'ref_axis')
		_spheres[key] = sphere
	return sphere
def _createSurfaceSpline(acisSurface):
	global _surfaceBSplines
	shape = acisSurface.build()
	if (hasattr(shape, 'Surface')):
		if (isinstance(shape.Surface, Part.BSplineSurface)):
			bss = shape.Surface
			points = []
			for u in bss.getPoles():
				p = [_createCartesianPoint(v, 'Ctrl Pts') for v in u]
				points.append(p)
			if (bss.isURational()):
				params = (
					BOUNDED_SURFACE(),
					B_SPLINE_SURFACE(bss.UDegree, bss.VDegree, points, 'UNSPECIFIED', bss.isUClosed(), bss.isVClosed(), False),
					B_SPLINE_SURFACE_WITH_KNOTS(uMults=bss.getUMultiplicities(), vMults=bss.getVMultiplicities(), uKnots=bss.getUKnots(), vKnots=bss.getVKnots(), form2='UNSPECIFIED'),
					GEOMETRIC_REPRESENTATION_ITEM(),
					RATIONAL_B_SPLINE_SURFACE(bss.getWeights()),
					REPRESENTATION_ITEM(''),
					SURFACE())
				spline = ListEntity(params)
			else:
				spline = B_SPLINE_SURFACE_WITH_KNOTS(name='', uDegree=bss.UDegree, vDegree=bss.VDegree, points=points, form='UNSPECIFIED', uClosed=bss.isUClosed(), vClosed=bss.isVClosed(), selfIntersecting=False, uMults=bss.getUMultiplicities(), vMults=bss.getVMultiplicities(), uKnots=bss.getUKnots(), vKnots=bss.getVKnots(), form2='UNSPECIFIED')
			_surfaceBSplines.append(spline)
			spline.__acis__ = acisSurface
			return spline
		if (isinstance(shape.Surface, Part.SurfaceOfRevolution)):
			node = acisSurface
			while (node.type == 'ref'):
				node = node.surface
			profile   = _createCurve(node.profile)
			placement = _createAxis1Placement('', node.loc, '', node.dir, '')
			spline    = SURFACE_OF_REVOLUTION('', profile, placement)
			_surfaceBSplines.append(spline)
			return spline
	logError(u"Spline-Surface not created for (%s)", acisSurface.__str__()[:-1])
	return None
def _createSurfaceTorus(acisSurface):
	global _toroids
	key = "%s,%s,%s,%r,%r" %(acisSurface.center, acisSurface.axis, acisSurface.uvorigin, acisSurface.major, acisSurface.minor)
	try:
		torus = _toroids[key]
	except:
		torus = TOROIDAL_SURFACE('', None, acisSurface.major, math.fabs(acisSurface.minor))
		torus.placement = _createAxis2Placement3D('', acisSurface.center, 'Origin', acisSurface.axis, 'center_axis', acisSurface.uvorigin, 'ref_axis')
		_toroids[key] = torus
	return torus

def _createSurface(acisFace):
	acisSurface = acisFace.getSurface()
	if (isinstance(acisSurface, Acis.SurfaceMesh)):   return (_createSurfaceMesh(acisSurface),   (acisFace.sense == 'forward'))
	if (isinstance(acisSurface, Acis.SurfacePlane)):  return (_createSurfacePlane(acisSurface),  (acisFace.sense == 'forward'))
	if (isinstance(acisSurface, Acis.SurfaceSphere)): return (_createSurfaceSphere(acisSurface), (acisFace.sense == 'forward'))
	if (isinstance(acisSurface, Acis.SurfaceSpline)): return (_createSurfaceSpline(acisSurface), (acisFace.sense == 'forward'))
	if (isinstance(acisSurface, Acis.SurfaceCone)):
		surface = _createSurfaceCone(acisSurface)
		if( acisSurface.cosine < 0):
			return surface, (acisFace.sense != 'forward')
		return surface, (acisFace.sense == 'forward')
	if (isinstance(acisSurface, Acis.SurfaceTorus)):
		surface = _createSurfaceTorus(acisSurface)
		if (acisSurface.minor < 0.0):
			return surface, (acisFace.sense != 'forward')
		return surface, (acisFace.sense == 'forward')
	return None, False
def _convertFace(acisFace, shell):
	global _advancedFaces
	global _currentColor
	global _representations
	global _assignments

	boundaries     = _createBoundaries(acisFace.getLoops())
	surface, sense = _createSurface(acisFace)
	id = "None" if surface is None else surface.id
	key = '(%s),%s,%s' %(_lst2str(boundaries), id, _bool2str(sense))
	try:
		face = _advancedFaces[key]
	except:
		face = ADVANCED_FACE('', boundaries, surface, sense)
		_advancedFaces[key] = face
		keyRGB = "%g,%g,%g" %(_currentColor.red, _currentColor.green, _currentColor.blue)
		try:
			assignment = _assignments[keyRGB]
		except:
			assignment = PRESENTATION_STYLE_ASSIGNMENT(_currentColor);
			_assignments[keyRGB] = assignment
		items = [STYLED_ITEM('color', [assignment], face)]
		_representations.append(MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('', items, _representations[0].context))

	return face

def _convertShell(acisShell):
	# FIXME how to distinguish between open or closed shell?
	shell = OPEN_SHELL('',[])
	for acisFace in acisShell.getFaces():
		face = _convertFace(acisFace, shell)
		shell.faces.append(face)
	return shell

def getColor(acisLump):
	color = acisLump.getColor()
	if (color is not None):
		global _currentColor

		key = "%g,%g,%g" %(color.red, color.green, color.blue)
		try:
			rgb = _colorPalette[key]
		except:
			rgb = COLOUR_RGB(color.red, color.green, color.blue)
			_colorPalette[key] = rgb
			logAlways("Found new used color (%s)" %(key))
		return rgb
	return None

def _convertLump(acisLump, bodies, representation):
	global _lumpCounter
	global _colorPalette
	global _currentColor

	color = getColor(acisLump)
	if (color is not None):
		_currentColor = color

	for acisShell in acisLump.getShells():
		for acisFace in acisShell.getFaces():
			_lumpCounter += 1
			lump = SHELL_BASED_SURFACE_MODEL("Lump_%d" % (_lumpCounter), [])
			shell = OPEN_SHELL('',[])
			lump.items.append(shell)
			face = _convertFace(acisFace, shell)
			shell.faces.append(face)
			representation.items.append(lump)

#		shell = _convertShell(acisShell)
#		_lumpCounter += 1
#		lump = SHELL_BASED_SURFACE_MODEL("Lump_%d" % (_lumpCounter), [])
#		lump.items.append(shell)
#		representation.items.append(lump)
		bodies.append(lump)

def _convertBody(acisBody, bodies, representation):
	for acisLump in acisBody.getLumps():
		_convertLump(acisLump, bodies, representation)

def _initExport():
	global _entityId
	global _pointsVertex
	global _pointsCartesian
	global _directions
	global _edgeCurves
	global _lines
	global _ellipses
	global _vectors
	global _cones
	global _planes
	global _spheres
	global _toroids
	global _curveBSplines
	global _surfaceBSplines
	global _axisPlacements
	global _orientedEdges
	global _edgeLoops
	global _faceBounds
	global _faceOuterBounds
	global _advancedFaces
	global _representations
	global _assignments
	global _colorPalette

	_entityId        = 10
	_pointsVertex    = {}
	_pointsCartesian = {}
	_directions      = {}
	_edgeCurves      = {}
	_lines           = {}
	_ellipses        = {}
	_vectors         = {}
	_cones           = {}
	_planes          = {}
	_spheres         = {}
	_toroids         = {}
	_curveBSplines   = {}
	_surfaceBSplines = []
	_axisPlacements  = []
	_orientedEdges   = []
	_edgeLoops       = []
	_faceBounds      = []
	_advancedFaces   = {}
	_representations = []
	_assignments     = {}
	_colorPalette    = {}

	return

def _setExported(l, b):
	if ((type(l) == dict) or (type(l) == list)):
		for p in l:
			if (isinstance(p, ExportEntity)):
				p.isexported = b
			else:
				l[p].isexported = b
	if (isinstance(l, ExportEntity)):
		l.isexported = b

def _exportList(step, l):
	if (type(l) == list):
		d = l
	else:
		d = l.values()
	d.sort()
	for p in d:
		step.write(p.exportSTEP())

#############################################################
# global classes
#############################################################

class E(object):
	def __init__(self, value):
		self.value = str(value).upper()
	def __str__(self):
		return self.value
	def __repr__(self):
		return '.%s.' %(self.value)

class AnyEntity(object):
	def __init__(self):
		return super(AnyEntity, self).__init__()
	def __repr__(self):
		return '*'

class AnonymEntity(object):
	def __init__(self):
		global _entityId
		self.id = _entityId
		_entityId += 1
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
		return "#%d\t= %s(%s)" %(self.id, self._getClassName(), ",".join(l))

class ExportEntity(AnonymEntity):
	def __init__(self):
		super(ExportEntity, self).__init__()
		self.isexported = False
	def _getClassName(self):
		return self.__class__.__name__
	def exportProperties(self):
		step = ''
		variables = [i for i in dir(self) if not (inspect.ismethod(getattr(self, i)) or i.startswith('__'))]
		for k in variables:
			try:
				a = getattr(self, k)
				if (isinstance(a, ReferencedEntity)):
					try:
						step += a.exportSTEP()
					except:
						print traceback.format_exc()
				elif (type(a) == list):
					step += _exportList_(a)
				elif (type(a) == tuple):
					step += _exportList_(a)
			except:
				print traceback.format_exc()
		return step
	def exportSTEP(self):
		if (self.isexported):
			return ''
		step = ""
		if (hasattr(self, '__acis__')):
			if (self.__acis__.type == 'ref'):
				step += "/*\n * ref = %d\n */\n" %(self.__acis__.ref)
			else:
				step += "/*\n * $%d\n */\n" %(self.__acis__.getIndex())
		step += "%r;\n" %(self)
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
	def __init__(self, red = 0.749019607843137, green = 0.749019607843137, blue = 0.749019607843137):
		super(COLOUR_RGB, self).__init__()
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
	def __init__(self, name, description = None, products = []):
		super(PRODUCT_RELATED_PRODUCT_CATEGORY, self).__init__(name)
		self.description = description if not description is None else name
		self.products = products
	def _getParameters(self):
		return super(PRODUCT_RELATED_PRODUCT_CATEGORY, self)._getParameters() + [self.description, self.products]

class PRODUCT(ReferencedEntity):
	def __init__(self, id, name, description=None, context = APPLICATION_CONTEXT()):
		super(PRODUCT, self).__init__()
		prdCtx = PRODUCT_CONTEXT(frame=context)
		self.identifyer = id
		self.name = name
		self.description = description
		self.frames = [prdCtx]
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
	def __init__(self, name, location, axis):
		super(AXIS1_PLACEMENT, self).__init__(name)
		self.location  = location
		self.axis      = axis
	def _getParameters(self):
		return super(AXIS1_PLACEMENT, self)._getParameters() + [self.location, self.axis]

class AXIS2_PLACEMENT_3D(AXIS1_PLACEMENT):
	def __init__(self, name, location, axis, direction):
		super(AXIS2_PLACEMENT_3D, self).__init__(name, location, axis)
		self.direction = direction
	def _getParameters(self):
		return super(AXIS2_PLACEMENT_3D, self)._getParameters() + [self.direction]

class ListEntity(ReferencedEntity):
	def __init__(self, entities):
		super(ListEntity, self).__init__()
		self.entities = entities
	def _getClassName(self):
		return ""
	def _getParameters(self):
		return super(ListEntity, self)._getParameters() + [self.entities]
	def exportSTEP(self):
		if (self.isexported):
			return ''
		step = ""
		if (hasattr(self, '__acis__')):
			if (self.__acis__.type == 'ref'):
				step += "/*\n * ref = %d\n */\n" %(self.__acis__.ref)
			else:
				step += "/*\n * $%d\n */\n" %(self.__acis__.getIndex())
		step += "%r;\n" %(self)
		for e in self.entities:
			try:
				if (isinstance(e, ExportEntity)):
					step += e.exportProperties()
				elif (type(e) == list):
					step += _exportList_(e)
				elif (type(e) == tuple):
					step += _exportList_(e)
			except:
				print traceback.format_exc()
		self.isexported = True
		return step
	def __repr__(self):
		return "#%d\t= (%s)" %(self.id, " ".join(["%s" % (e.toString()) for e in self.entities]))

class NamedListEntity(ListEntity):
	def __init__(self, entities):
		return super(NamedListEntity, self).__init__(entities)
	def _getClassName(self):
		return super(ListEntity, self)._getClassName()

class NAMED_UNIT(ExportEntity):
	def __init__(self, dimensions):
		super(NAMED_UNIT, self).__init__()
		self.dimensions = dimensions
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

class LENGTH_MEASURE(ValueObject):
	def __init__(self, value):
		super(LENGTH_MEASURE, self).__init__(value)

class UNCERTAINTY_MEASURE_WITH_UNIT(ReferencedEntity):
	def __init__(self, value, globalLength):
		super(UNCERTAINTY_MEASURE_WITH_UNIT, self).__init__()
		self.value = LENGTH_MEASURE(value)
		self.length = globalLength
		self.name = 'DISTANCE_ACCURACY_VALUE'
		self.description = 'Maximum model space distance between geometric entities at asserted connectivities'
	def _getParameters(self):
		return super(UNCERTAINTY_MEASURE_WITH_UNIT, self)._getParameters() + [self.value, self.length, self.name, self.description]

class GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT(ExportEntity):
	def __init__(self, units):
		super(GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT, self).__init__()
		if (type(units) == tuple) or (type(units) == list):
			self.units = units
		else:
			self.units = (units,)
	def _getParameters(self):
		return super(GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT, self)._getParameters() + [self.units]

class GLOBAL_UNIT_ASSIGNED_CONTEXT(ExportEntity):
	def __init__(self, assignements):
		super(GLOBAL_UNIT_ASSIGNED_CONTEXT, self).__init__()
		self.assignements = assignements
	def _getParameters(self):
		return super(GLOBAL_UNIT_ASSIGNED_CONTEXT, self)._getParameters() + [self.assignements]

class REPRESENTATION_CONTEXT(ExportEntity):
	def __init__(self, identifyer = '', t = '3D'):
		super(REPRESENTATION_CONTEXT, self).__init__()
		self.identifyer = identifyer
		self.type = t
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
	def __init__(self, length = 0.0, mass = 0.0, time = 0.0, current = 0.0, temperature = 0.0, amount = 0.0, luminousity = 0.0):
		super(DIMENSIONAL_EXPONENTS, self).__init__()
		self.length      = length
		self.mass        = mass
		self.time        = time
		self.current     = current
		self.temperature = temperature
		self.amount      = amount
		self.luminousity = luminousity
	def _getParameters(self):
		return super(DIMENSIONAL_EXPONENTS, self)._getParameters() +[self.length, self.mass, self.time, self.current, self.temperature, self.amount, self.luminousity]

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
	def __init__(self, name = '', description=None, definition=None):
		super(PRODUCT_DEFINITION_SHAPE, self).__init__(name)
		self.description = description
		self.definition  = definition
	def _getParameters(self):
		return super(PRODUCT_DEFINITION_SHAPE, self)._getParameters() + [self.description, self.definition]

class SHAPE_REPRESENTATION(NamedEntity):
	def __init__(self, name = '', item=None, value=0.01, globalLength=None, globalSolidAngle=None, globalPlaneAngle=None):
		super(SHAPE_REPRESENTATION, self).__init__(name)
		self.items = [item]
		uncertainty = UNCERTAINTY_MEASURE_WITH_UNIT(value, globalLength)
		geom = GEOMETRIC_REPRESENTATION_CONTEXT(3)
		uncr = GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT(uncertainty)
		glob = GLOBAL_UNIT_ASSIGNED_CONTEXT((globalLength, globalPlaneAngle, globalSolidAngle))
		repr = REPRESENTATION_CONTEXT()
		self.context = UNIT((geom, uncr, glob, repr));
	def _getParameters(self):
		return super(SHAPE_REPRESENTATION, self)._getParameters() + [self.items, self.context]

class SHAPE_DEFINITION_REPRESENTATION(ReferencedEntity):
	def __init__(self, product, representation):
		super(SHAPE_DEFINITION_REPRESENTATION, self).__init__()
		self.definition = PRODUCT_DEFINITION_SHAPE('', None, product)
		self.representation = representation
	def _getParameters(self):
		return super(SHAPE_DEFINITION_REPRESENTATION, self)._getParameters() + [self.definition, self.representation]

class PRODUCT_DEFINITION_FORMATION(NamedEntity):
	def __init__(self, name = '', description = None, product = None):
		super(PRODUCT_DEFINITION_FORMATION, self).__init__(name)
		self.description = description
		self.product     = product
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
	def __init__(self, name, description, product, context):
		super(PRODUCT_DEFINITION, self).__init__(name)
		self.description = description
		self.formation   = PRODUCT_DEFINITION_FORMATION(product = product)
		self.frame       = PRODUCT_DEFINITION_CONTEXT(context = context)
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
	def __init__(self, name, items):
		super(SHELL_BASED_SURFACE_MODEL, self).__init__(name)
		self.items = items
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
	def __init__(self, name, wire, bound):
		super(FACE_BOUND, self).__init__(name)
		self.wire = wire
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
	def __init__(self, name, bounds, surface, bound):
		super(ADVANCED_FACE, self).__init__(name)
		self.bounds    = bounds
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
	def __init__(self, name, placement, radius):
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
	def __init__(self, name, start, end, edge, orientation):
		super(ORIENTED_EDGE, self).__init__(name)
		self.start       = start
		self.end         = end
		self.edge        = edge
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

class SURFACE_OF_REVOLUTION(ReferencedEntity):
	def __init__(self, name=None, curve=None, position=None):
		super(SURFACE_OF_REVOLUTION, self).__init__()
		self.name      = name
		self.curve     = curve
		self.positions = position
	def _getParameters(self):
		l = super(SURFACE_OF_REVOLUTION, self)._getParameters()
		if (self.name      is not None): l.append(self.name)
		if (self.curve     is not None): l.append(self.curve)
		if (self.positions is not None): l.append(self.positions)
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
		return super(GEOMETRIC_REPRESENTATION_ITEM, self).__init__()

class SURFACE(ReferencedEntity):
	def __init__(self):
		return super(SURFACE, self).__init__()

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

class APPLIED_GROUP_ASSIGNMENT(ReferencedEntity):
	def __init__(self, items):
		super(APPLIED_GROUP_ASSIGNMENT, self).__init__()
		self.group = GROUP('Sweeping-Fl\X\E4che1', None)
		self.items = items
	def _getParameters(self):
		return super(APPLIED_GROUP_ASSIGNMENT, self)._getParameters() + [self.group, self.items]

#############################################################
# Global functions
#############################################################

def export(filename, satHeader, satBodies):
	dt     = datetime.now() # 2018-05-13T08:03:27-07:00
	user   = getAuthor()
	desc   = getDescription()
	orga   = ''
	proc   = 'ST-DEVELOPER v16.5'
	auth   = ''
	bodies = []

	_initExport()

	global _scale
	_scale = satHeader.scale

	path, f = os.path.split(filename)
	name, x = os.path.splitext(f)
	path = path.replace('\\', '/')

	subpath = "%s/%s" %(path,name)
	if (not os.path.exists(subpath)):
		os.makedirs(subpath)
	with open("%s/subtypes.txt" %(subpath), 'w') as fp:
		surfaces = Acis.subtypeTable.get('surface', [])
		for i, n in enumerate(surfaces):
			s = repr(n)
			if (len(s) > 0) and (s[-1] == '\n'):
				s = s[0:-1]
			fp.write("%d\t%r\n" %(i, s))

	glbLength     = UNIT((LENGTH_UNIT(None), NAMED_UNIT(AnyEntity()), SI_UNIT('MILLI','METRE')))
	glbAngleSolid = UNIT((NAMED_UNIT(AnyEntity()), SI_UNIT(None,'STERADIAN'), SOLID_ANGLE_UNIT(None)))
	dimExp        = DIMENSIONAL_EXPONENTS()
	pamwu         = PLANE_ANGLE_MEASURE_WITH_UNIT(0.01745329252)
	glbAnglePlane = UNIT((CONVERSION_BASED_UNIT('degree', pamwu), NAMED_UNIT(dimExp), PLANE_ANGLE_UNIT(None)))

	l =	UNCERTAINTY_MEASURE_WITH_UNIT(satHeader.resabs, glbLength)
	u = UNIT((GEOMETRIC_REPRESENTATION_CONTEXT(3), GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT(l), GLOBAL_UNIT_ASSIGNED_CONTEXT((glbLength, glbAngleSolid, glbAnglePlane)), REPRESENTATION_CONTEXT()))
	if (len(bodies) > 0):
		aga = APPLIED_GROUP_ASSIGNMENT(bodies)
	else:
		aga = l

	mdgpr = MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('', [], u)
	_representations.append(mdgpr)

	appDatTimAss = APPLIED_DATE_AND_TIME_ASSIGNMENT(dt)
	appPrtDef    = APPLICATION_PROTOCOL_DEFINITION()
	prd          = PRODUCT(name, name, desc, appPrtDef.application)
	prdDef       = PRODUCT_DEFINITION(name, name, prd, appPrtDef.application)

	placement    = _createAxis2Placement3D('placement', VEC(0,0,0), '', VEC(0,0,1), 'axis', VEC(1,0,0), 'refdir')
	shpRpr       = SHAPE_REPRESENTATION('', placement, 0.01, glbLength, glbAngleSolid, glbAnglePlane)
	appDatTimAss.products.append(prdDef)
	advShpRpr    = ADVANCED_BREP_SHAPE_REPRESENTATION('', [], shpRpr.context)
	shpRepRel    = SHAPE_REPRESENTATION_RELATIONSHIP('SRR', 'None', shpRpr, advShpRpr)

	shpDefRep    = SHAPE_DEFINITION_REPRESENTATION(prdDef, shpRpr)

	prdRelPRdCat = PRODUCT_RELATED_PRODUCT_CATEGORY(name, name, [prd])

	global _currentColor
	_currentColor = COLOUR_RGB(0.749019607843137,0.749019607843137,0.749019607843137)
	keyRGB = "%g,%g,%g" %(_currentColor.red, _currentColor.green, _currentColor.blue)
	_assignments[keyRGB] = PRESENTATION_STYLE_ASSIGNMENT(_currentColor)
	for body in satBodies:
		_convertBody(body.node, bodies, advShpRpr)

#	_setExported(glbLength, True)
#	_setExported(glbAngleSolid, True)
#	_setExported(glbAnglePlane, True)
#	_setExported(shpRepRel, True)
#	_setExported(prdRelPRdCat, True)
#	_setExported(appPrtDef, True)
#	_setExported(shpDefRep, True)
#	_setExported(appDatTimAss, True)
#	_setExported(prsStyAss[0], True)
#	_setExported(pamwu, True)
#	_setExported(prdDef, True)
#
#	_setExported(_pointsCartesian, True)
#	_setExported(_directions, True)
#	_setExported(_axisPlacements, True)
#	_setExported(_orientedEdges, True)
#	_setExported(_edgeCurves, True)
#	_setExported(_pointsVertex, True)
#	_setExported(_lines, True)
#	_setExported(_ellipses, True)
#	_setExported(_edgeLoops, True)
#	_setExported(_faceBounds, True)
#	_setExported(_vectors, True)
#	_setExported(_cones, True)
#	_setExported(_planes, True)
#	_setExported(_spheres, True)
#	_setExported(_toroids, True)
#	_setExported(_curveBSplines, True)
#	_setExported(_surfaceBSplines, False)
#	_setExported(_faceOuterBounds, True)
#	_setExported(_advancedFaces, True)

	stepfile = "%s/%s.step" %(path, name)
	with open(stepfile, 'w') as step:
		step.write("ISO-10303-21;\n")
		step.write("HEADER;\n")
		step.write("/* Generated by software containing ST-Developer\n")
		step.write(" * from STEP Tools, Inc. (www.steptools.com) \n")
		step.write(" */\n")
		step.write("\n");
		step.write("FILE_DESCRIPTION(\n")
		step.write("/* description */ (''),\n")
		step.write("/* implementation_level */ '2;1');\n")
		step.write("\n");
		step.write("FILE_NAME(\n")
		step.write("/* name */ '%s',\n" %(stepfile))
		step.write("/* time_stamp */ '%s',\n" %(dt.strftime("%Y-%m-%dT%H:%M:%S")))
		step.write("/* author */ ('%s'),\n" %(user))
		step.write("/* organization */ ('%s'),\n" %(orga))
		step.write("/* preprocessor_version */ '%s',\n" %(proc))
		step.write("/* originating_system */ 'Autodesk Inventor 2017',\n")
		step.write("/* authorisation */ '%s');\n" %(auth))
		step.write("\n");
		step.write("FILE_SCHEMA (('AUTOMOTIVE_DESIGN { 1 0 10303 214 3 1 1 }'));\n")
		step.write("ENDSEC;\n")
		step.write("\n");
		step.write("DATA;\n")
		step.write(mdgpr.exportSTEP())
		step.write(aga.exportSTEP())

#		_exportList(step, _faceOuterBounds)
#		_exportList(step, _toroids)
#		_exportList(step, _planes)
#		_exportList(step, _ellipses)
#		_exportList(step, _spheres)
#		_exportList(step, _faceBounds)
#		_exportList(step, _edgeLoops)
#		_exportList(step, _lines)
#		_exportList(step, _vectors)
#		_exportList(step, _curveBSplines)
#		_exportList(step, _pointsVertex)
#		_exportList(step, _edgeCurves)
#		_exportList(step, _orientedEdges)
#		_exportList(step, _cones)
#		_exportList(step, _surfaceBSplines)
#		_exportList(step, _advancedFaces)
#		appDatTimAss.isexported = False
		step.write(appDatTimAss.exportSTEP())
#		_exportList(step, _axisPlacements)
#		_exportList(step, _directions)
#		_exportList(step, _pointsCartesian)

#		glbLength.isexported = False
		step.write(glbLength.exportSTEP())
#		glbAngleSolid.isexported = False
		step.write(glbAngleSolid.exportSTEP())
		step.write(dimExp.exportSTEP())
#		glbAnglePlane.isexported = False
		step.write(glbAnglePlane.exportSTEP())
#		pamwu.isexported = False
		step.write(pamwu.exportSTEP())
#		shpDefRep.isexported = False
		step.write(shpDefRep.exportSTEP())
#		shpRepRel.isexported = False
		step.write(shpRepRel.exportSTEP())
#		prdRelPRdCat.isexported = False
		step.write(prdRelPRdCat.exportSTEP())
#		appPrtDef.isexported = False
		step.write(appPrtDef.exportSTEP())
#		prdDef.isexported = False
		step.write(prdDef.exportSTEP())
		_exportList(step, _representations)
		_exportList(step, _assignments)
		step.write("ENDSEC;\n")
		step.write("END-ISO-10303-21;")
	logAlways(u"File written to '%s'.", stepfile)
	return stepfile
