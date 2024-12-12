# -*- coding: utf-8 -*-

'''
Acis2Step.py:
MC:
 Le classi maiuscolo sono 1-1 con le entity STEP. E' buono cosi si rimodella agevolmente l'object model di STEP.
 Con la reflection viene dumpato il nome della classe.
'''

import traceback, os, sys, math, io
import Part
import Acis

from datetime          import datetime
from FreeCAD           import Vector as VEC, Placement as PLC, Matrix as MAT
from importerUtils     import logInfo, logWarning, logError, isEqual1D, getColorDefault, getDumpFolder, getAuthor, getDescription
from importerConstants import CENTER, DIR_X, DIR_Y, DIR_Z, EPS

if (sys.version_info.major > 2):
	long    = int
	unicode = str

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

TRANSFORM_NONE   = PLC()

#############################################################
# private functions
#############################################################

def _isIdentity(transf):
	return transf.Base.distanceToPoint(CENTER) < EPS and transf.Rotation.Axis.getAngle(DIR_Z) < EPS

def _getE(o):
	if (o is None): return None
	if (isinstance(o, E)): return o
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

# $ significa null (come $-1 in ACIS SAT)
def _str2str(s):
	if (s is None): return '$'
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

def rotation_matrix(axis, angle):
	axis.normalize()
	a = math.cos(angle / 2.0)
	aa = a * a
	v = axis * math.sin(angle / -2.0)
	b = v.x
	c = v.y
	d = v.z
	aa, bb, cc, dd = a * a, b * b, c * c, d * d
	bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
	m11 = aa + bb - cc - dd
	m12 = 2 * (bc + ad)
	m13 = 2 * (bd - ac)
	m21 = 2 * (bc - ad)
	m22 = aa + cc - bb - dd
	m23 = 2 * (cd + ab)
	m31 = 2 * (bd + ac)
	m32 = 2 * (cd - ab)
	m33 = aa + dd - bb - cc
	return MAT(m11, m12, m13, 0.0, m21, m22, m23, 0.0, m31, m32, m33, 0.0, 0.0, 0.0, 0.0, 0.0)

def _rotate(vec, rotation):
	if rotation.Axis.Length < EPS: return vec
	return rotation_matrix(rotation.Axis, rotation.Angle) * vec

def getColor(entity):
	global _colorPalette

	r = g = b = None

	color = entity.getColor()
	if (color):
		r, g, b = color.red, color.green, color.blue
	else:
		color = getColorDefault()
		if (color):
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

	if (color):
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

def _createTransformation(ref1, ref2, idt):
	return ListEntity(REPRESENTATION_RELATIONSHIP(None, ref1, ref2), REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION(idt), SHAPE_REPRESENTATION_RELATIONSHIP())

def _createUnit(tolerance):
	unit     = UNIT()
	uncr_ctx = GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT()
	glob_ctx = GLOBAL_UNIT_ASSIGNED_CONTEXT()
	repr_ctx = REPRESENTATION_CONTEXT()

	length = ListEntity(LENGTH_UNIT(None), NAMED_UNIT(AnyEntity()), SI_UNIT('MILLI', 'METRE'))
	angle1 = ListEntity(NAMED_UNIT(AnyEntity()), PLANE_ANGLE_UNIT(None), SI_UNIT(None, 'RADIAN'))
	angle2 = ListEntity(NAMED_UNIT(AnyEntity()), SI_UNIT(None, 'STERADIAN'), SOLID_ANGLE_UNIT(None))
	uncertainty = UNCERTAINTY_MEASURE_WITH_UNIT(tolerance, length)

	uncr_ctx.units = (uncertainty,)

	glob_ctx.assignments = (length, angle1, angle2)

	unit.entities = _createGeometricRepresentationList(uncr_ctx, glob_ctx, repr_ctx)
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

def _exportInternalList_(a):
	step = ''
	for i in a:
		if (isinstance(i, ExportEntity)):
			step += i.exportSTEP()
		elif (type(i) == list):
			step += _exportInternalList_(i)
		elif (type(i) == tuple):
			step += _exportInternalList_(i)
	return step

def _createCurveComp(acisCurve):
	# TODO
	return None

def _createCurveDegenerate(acisCurve):
	# TODO
	return None

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

def __create_b_spline_curve(spline):
	if (spline):
		points = [_createCartesianPoint(pole, 'Ctrl Pts') for pole in spline.poles]
		k1 = ",".join(["#%d"%(point.id) for point in points])
		k2 = ""
		mults = spline.uMults
		if (mults):
			k2 = ",".join(["%d" %(mult) for mult in mults])
		k3 = ""
		knots = spline.uKnots
		if (knots):
			k3 = ",".join(["%r" %(knot) for knot in knots])
		key = "(%s),(%s),(%s)" %(k1, k2, k3)
		try:
			curve = _curveBSplines[key]
		except:
			degree = spline.uDegree
			closed = (spline.poles[0] == spline.poles[-1])
			if (spline.rational):
				p0 = BOUNDED_CURVE()
				p1 = B_SPLINE_CURVE(name=None, degree=degree, points=points, form='UNSPECIFIED', closed=closed, selfIntersecting=False)
				p2 = B_SPLINE_CURVE_WITH_KNOTS(name='', mults=mults, knots=knots, form2='UNSPECIFIED', closed=closed)
				p3 = CURVE()
				p4 = GEOMETRIC_REPRESENTATION_ITEM()
				p5 = RATIONAL_B_SPLINE_CURVE(spline.weights)
				p6 = REPRESENTATION_ITEM('')
				curve = ListEntity(p0, p1, p2, p3, p4, p5, p6)
			else:
				curve = B_SPLINE_CURVE_WITH_KNOTS(name='', degree=degree, points=points, form='UNSPECIFIED', closed=closed, selfIntersecting=False, mults=spline.uMults, knots=spline.uKnots, form2='UNSPECIFIED')
			_curveBSplines[key] = curve
		return curve
	return None

def _createCurveIntExact(acisCurve):
#	acisCurve.spline
#	acisCurve.singularity
#	acisCurve.surface1# readSurface(chunks, i)
#	acisCurve.surface2# readSurface(chunks, i)
#	acisCurve.pcurve1 # readBS2Curve(chunks, i)
#	acisCurve.pcurve2 # readBS2Curve(chunks, i)
#
	curve = __create_b_spline_curve(acisCurve.spline)
	return curve

def _createCurveIntBlend(acisCurve):
	# TODO
	return None

def _createCurveIntBlendSpring(acisCurve):
	# TODO
	return None

def _createCurveIntLaw(acisCurve):
	# TODO
	return None

def _createCurveIntOff(acisCurve):
	# TODO
	return None

def _createCurveIntOffset(acisCurve):
	# TODO
	return None

def _createCurveIntOffsetSurface(acisCurve):
	# TODO
	return None

def _createCurveIntSilhouetteParameter(acisCurve):
	# TODO
	return None

def _createCurveIntParameter(acisCurve):
	# TODO
	return None

def _createCurveIntProject(acisCurve):
	# TODO
	return None

def _createCurveIntSurface(acisCurve):
	# TODO
	return None

def _createCurveIntSilhouetteTaper(acisCurve):
	# TODO
	return None

def _createCurveIntComp(acisCurve):
	# TODO
	return None

def _createCurveIntDefm(acisCurve):
	# TODO
	return None

def _createCurveIntHelix(acisCurve):
	# TODO
	return None

def _createCurveIntSSS(acisCurve):
	# TODO
	return None

def _createCurveIntInt(acisCurve):
	# TODO
	return None

CREATE_CURVE_INT ={
	'bldcur':              _createCurveIntBlend,
	'blend_int_cur':       _createCurveIntBlend,
	'blndsprngcur':        _createCurveIntBlendSpring,
	'spring_int_cur':      _createCurveIntBlendSpring,
	'exactcur':            _createCurveIntExact,
	'exact_int_cur':       _createCurveIntExact,
	'lawintcur':           _createCurveIntLaw,
	'law_int_cur':         _createCurveIntLaw,
	'offintcur':           _createCurveIntOff,
	'off_int_cur':         _createCurveIntOff,
	'offsetintcur':        _createCurveIntOffset,
	'offset_int_cur':      _createCurveIntOffset,
	'offsurfintcur':       _createCurveIntOffsetSurface,
	'off_surf_int_cur':    _createCurveIntOffsetSurface,
	'parasil':             _createCurveIntSilhouetteParameter,
	'para_silh_int_cur':   _createCurveIntSilhouetteParameter,
	'parcur':              _createCurveIntParameter,
	'par_int_cur':         _createCurveIntParameter,
	'projcur':             _createCurveIntProject,
	'proj_int_cur':        _createCurveIntProject,
#	'd5c2_cur':            _createCurveIntSkin,       # !!!No examples available!!!
#	'skin_int_cur':        _createCurveIntSkin,       # !!!No examples available!!!
#	'subsetintcur':        _createCurveIntSubset,     # !!!No examples available!!!
#	'subset_int_cur':      _createCurveIntSubset,     # !!!No examples available!!!
	'surfcur':             _createCurveIntSurface,
	'surf_int_cur':        _createCurveIntSurface,
	'surfintcur':          _createCurveIntInt,
	'int_int_cur':         _createCurveIntInt,
#	'tapersil':            _createCurveIntSilhouetteTaper,  # !!!No examples available!!!
#	'taper_silh_int_cur':  _createCurveIntSilhouetteTaper,  # !!!No examples available!!!
## ASM Extensions ##
	'comp_int_cur':        _createCurveIntComp,
	'defm_int_cur':        _createCurveIntDefm,
	'helix_int_cur':       _createCurveIntHelix,
	'sss_int_cur':         _createCurveIntSSS,
}

#MC vecchio/nuovo mergiato
def _createCurveInt(acisCurve):
	global _curveBSplines
	shape = acisCurve.build() # fa il build con Part, va benissimo
	spline = acisCurve.spline
	if (spline):
		curve = __create_b_spline_curve(spline)
		return curve
	elif (isinstance(shape, Part.Edge)):
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
	else:
		try:
			create = CREATE_CURVE_INT[acisCurve.subtype]
			return create(acisCurve)
		except Exception as ex:
			logError("Don't know how how to create INT_CURVE %s - %s" %(acisCurve.subtype, ex))
	return None

def _createCurveP(acisCurve):
	# TODO
	return None

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
	return None

def _createCoEdge(acisCoEdge):
	acisEdge  = acisCoEdge.getEdge()
	acisCurve = acisEdge.getCurve()
	curve     = _createCurve(acisCurve)
	if (curve):
		oe = ORIENTED_EDGE((acisCoEdge.sense == 'forward'))
		p1 = _createVertexPoint(acisEdge.getStart())
		p2 = _createVertexPoint(acisEdge.getEnd())
		e  = _createEdgeCurve(p1, p2, curve, (acisEdge.sense == 'forward'))
		oe.edge = e
		return oe
	return None

def _createBoundaries(acisLoops):
	boundaries = []
	isouter = True
	for acisLoop in acisLoops:
		coedges = acisLoop.getCoEdges()
		edges = []
		for acisCoEdge in coedges:
			edge = _createCoEdge(acisCoEdge)
			if (edge):
				edges.append(edge)
		if (len(edges) > 0):
			face = FACE_BOUND('', True)
			loop = EDGE_LOOP('', edges)
			face.wire = loop
			boundaries.append(face)
	return boundaries

def _calculateRef(axis):
	if (isEqual1D(axis.x, 1.0)):  return DIR_Y
	if (isEqual1D(axis.x, -1.0)): return -DIR_Y
	return DIR_X.cross(axis) # any perpendicular vector to normal?!?

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
			plc = _createAxis2Placement3D('', center, 'Origin', axis.negative(), 'center_axis', major, 'ref_axis')
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
	revolution.placement = _createAxis2Placement3D('', center, 'Origin', axis, 'center_axis', ref, 'ref_axis')
	return revolution, (sense == 'forward')

def _createSurfaceSphere(center, radius, pole, sense):
	global _spheres
	key = "%s,%r" %(center, radius)
	try:
		sphere = _spheres[key]
	except:
		sphere = SPHERICAL_SURFACE('', None, radius)
		ref = _calculateRef(pole)
		sphere.placement = _createAxis2Placement3D('', center, 'Origin', pole, 'center_axis', ref, 'ref_axis')
		_spheres[key] = sphere
	return sphere, (sense == 'forward')

def _createSurfaceBS(acisSurface, sense):
	spline = acisSurface.spline
	points = []
	for u in spline.poles:
		p = [_createCartesianPoint(v, 'Ctrl Pts') for v in u]
		points.append(p)
	if (spline.rational):
		p0 = BOUNDED_SURFACE()
		p1 = B_SPLINE_SURFACE(spline.uDegree, spline.vDegree, points, 'UNSPECIFIED', spline.uPeriodic, spline.vPeriodic, False)
		p2 = B_SPLINE_SURFACE_WITH_KNOTS(uMults=spline.uMults, vMults=spline.vMults, uKnots=spline.uKnots, vKnots=spline.vKnots, form2='UNSPECIFIED')
		p3 = GEOMETRIC_REPRESENTATION_ITEM()
		p4 = RATIONAL_B_SPLINE_SURFACE(spline.weights)
		p5 = REPRESENTATION_ITEM('')
		p6 = SURFACE()
		spline = ListEntity(p0, p1, p2, p3, p4, p5, p6)
	else:
		spline = B_SPLINE_SURFACE_WITH_KNOTS(name='', uDegree=spline.uDegree, vDegree=spline.vDegree, points=points, form='UNSPECIFIED', uClosed=spline.uPeriodic, vClosed=spline.vPeriodic, selfIntersecting=False, uMults=spline.uMults, vMults=spline.vMults, uKnots=spline.uKnots, vKnots=spline.vKnots, form2='UNSPECIFIED')
	spline.__acis__ = acisSurface
	return spline, sense == 'forward'

def _createSurfaceSpline(acisFace):
	surface = acisFace.getSurface()
	if (surface.subtype == 'ref'):
		surface = surface.getSurface()

	if (surface.spline):
		return _createSurfaceBS(surface, acisFace.sense)
	shape = acisFace.build()
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
		return _createSurfaceToroid(shape.MajorRadius, shape.MinorRadius, shape.Center, shape.Axis, acisFace.sense)

	return None, acisFace.sense == 'forward'

def _createSurfaceToroid(major, minor, center, axis, sense):
	torus = TOROIDAL_SURFACE('', None, major, math.fabs(minor))
	ref = _calculateRef(axis)
	torus.placement = _createAxis2Placement3D('', center, 'Origin', axis, 'center_axis', ref, 'ref_axis')
	if (minor < 0.0): return torus, (sense != 'forward')
	return torus, (sense == 'forward')

def _createSurfaceFaceShape(acisFace):
	surface = acisFace.getSurface()
	if (isinstance(surface, Acis.SurfaceCone)):
		return _createSurfaceCone(surface.center, surface.axis, surface.cosine, surface.sine, surface.major, acisFace.sense)
#	if (isinstance(surface, Acis.SurfaceMesh)):
#		return _createSurfaceMesh(surface, acisFace.sense)
	if (isinstance(surface, Acis.SurfacePlane)):
		return _createSurfacePlane(surface.root, surface.normal, acisFace.sense)
	if (isinstance(surface, Acis.SurfaceSphere)):
		return _createSurfaceSphere(surface.center, surface.radius, surface.pole, acisFace.sense)
	if (isinstance(surface, Acis.SurfaceTorus)):
		return _createSurfaceToroid(surface.major, surface.minor, surface.center, surface.axis, acisFace.sense)
	if (isinstance(surface, Acis.SurfaceSpline)):
		return _createSurfaceSpline(acisFace)
	logWarning("Can't export surface '%s.%s'!" %(surface.__class__.__module__, surface.__class__.__name__))
	return None, (acisFace.sense == 'forward')

# MC vecchio
def _createSurfaceFaceShapeOld(acisFace, shape):
	surface = acisFace.getSurface()
	if (isinstance(shape, Part.BSplineSurface)):
		return _createSurfaceBSpline(shape, surface, acisFace.sense)
	elif (isinstance(shape, Part.Cone)):
		return _createSurfaceCone(surface.center, surface.axis, surface.cosine, surface.sine, surface.major, acisFace.sense)
	elif (isinstance(shape, Part.Cylinder)):
		return _createSurfaceCylinder(shape.Center, shape.Axis, shape.Radius, acisFace.sense)
	elif (isinstance(shape, Part.Plane)):
		return _createSurfacePlane(shape.Position, shape.Axis, acisFace.sense)
	elif (isinstance(shape, Part.Sphere)):
		return _createSurfaceSphere(surface.center, surface.radius, surface.pole, acisFace.sense)
	elif (isinstance(shape, Part.SurfaceOfRevolution)):
		return _createSurfaceRevolution(surface.profile, surface.profile.center, surface.profile.axis, acisFace.sense)
	elif (isinstance(shape, Part.Toroid)):
		return _createSurfaceToroid(surface.major, surface.minor, surface.center, surface.axis, acisFace.sense)

# MC vecchio
def _createSurfaceOld(acisFace):
	faces = []
	shape = acisFace.build() # will Return one single Face!
	if (shape):
		for face in shape.Faces:
			f = _createSurfaceFaceShapeOld(acisFace, face.Surface)
			if (f):
				faces.append(f)
	return faces

def _convertFace(acisFace, parentColor, context):
	color = getColor(acisFace)
	if (color is None): color = parentColor

	try:
		surface, sense = _createSurfaceFaceShape(acisFace)
		if (surface):
			face = ADVANCED_FACE('', surface, sense)
			face.bounds = _createBoundaries(acisFace.getLoops())
			assignColor(color, face, context)
			return [face]
		else:
			shells = []
			faces = _createSurfaceOld(acisFace)
			for surface, sense in faces:
				face = ADVANCED_FACE('', surface, sense)
				face.bounds = _createBoundaries(acisFace.getLoops())
				assignColor(color, face, context)
				shells.append(face)
			return shells
	except:
		logError('Fatal for acisFace= %s', acisFace.getSurface().getSurface())
	return None

def _convertShell(acisShell, representation, parentColor):
	# FIXME how to distinguish between open or closed shell?
	# MC: vedi OPEN_SHELL e CLOSED_SHELL, ma alla fine non le usa
	faces = acisShell.getFaces()
	if (len(faces) > 0):
		color = getColor(acisShell)
		if (color is None): color = parentColor
		shell = OPEN_SHELL('',[])

		for acisFace in faces:
			#>MC vecchio
			faces = _convertFace(acisFace, color, representation.context)
			shell.faces += faces

			#face = _convertFace(acisFace, color, representation.context)
			#shell.addFace(face)
		assignColor(color, shell, representation.context)
		return shell

	return None

def _convertLump(acisLump, name, appContext, parentColor, transformation):
	#MC:
	#NOTA quando si volesse usare Part nativo, siccome li le trasformate le ho gia applicate, bastera esportare in STEP

	# Da OCCT
	#product_definition
	#	A shape corresponding to the component type of for components. Each assembly or component has its own product_definition. It is used as a starting point for translation when read.step.product.mode is ON.
	#product_definition_shape
	#	This entity provides a link between product_definition and corresponding shape_definition_representation, or between next_assembly_usage_occurence and corresponding context_dependent_shape_representation.
	#shape_definition_representation
	#	A TopoDS_Compound for assemblies, a CASCADE shape corresponding to the component type for components.	Each assembly or component has its own shape_definition_representation. The graph of dependencies is modified in such a way that shape_definition_representations of all components of the assembly are referred by the shape_definition_representation of the assembly.
	#next_assembly_usage_occurence
	#	This entity defines a relationship between the assembly and its component. It is used to introduce (in the dependencies graph) the links between shape_definition_representation of the assembly and shape_definition_representations and context_dependent_shape_representations of all its components.
	#context_dependent_shape_representation
	#	This entity is associated with the next_assembly_usage_occurence entity and defines a placement of the component in the assembly. The graph of dependencies is modified so that each context_dependent_shape_representation is referred by shape_definition_representation of the corresponding assembly.
	#shape_representation_relationship_with_transformation
	#	This entity is associated with context_dependent_shape_representation and defines a transformation necessary to apply to the component in order to locate it in its place in the assembly.
	#item_defined_transformation
	#	This entity defines a transformation operator used by shape_representation_relationship_with_transformation or mapped_item entity

	name = "%s_L_%02d" %(name, acisLump.index)
	frames          = [PRODUCT_CONTEXT('', appContext, 'mechanical')]
	prod            = PRODUCT(name, frames)
	prod_def_fmt    = PRODUCT_DEFINITION_FORMATION(name + '_def_fmt', prod)
	prod_def_ctx    = PRODUCT_DEFINITION_CONTEXT(name + '_def_ctx', appContext, 'design')
	prod_transf_def = PRODUCT_DEFINITION(name, prod_def_fmt, prod_def_ctx)
	prod_def_shape  = PRODUCT_DEFINITION_SHAPE(name + '_def_shape', '', prod_transf_def)
	unit  = _createUnit(1e-7)
	lump  = SHELL_BASED_SURFACE_MODEL()
	color = getColor(acisLump)

	if (color is None): color = parentColor
	assignColor(color, lump, unit)
	if ((not transformation is None) and (_isIdentity(transformation)==False)):
		placement    = TRANSFORM_NONE.Base
		zDir         = DIR_Z
		xDir         = DIR_X
		ident_transf = _createAxis2Placement3D('', placement, '', zDir, '', xDir, '')

		advShapeRepresentation = ADVANCED_BREP_SHAPE_REPRESENTATION('', [], unit)
		advShapeRepresentation.items.append(lump)
		advShapeRepresentation.items.append(ident_transf) # a rhino basta questo con la trasformata effettiva, senza relazioni niente

		placement = transformation.Base
		zDir      = _rotate(DIR_Z, transformation.Rotation)
		xDir      = _rotate(DIR_X, transformation.Rotation)
		transf    = _createAxis2Placement3D('', placement, '', zDir, '', xDir, '')

		# rappresentazione contenente tutte le trasformate utilizzate nelle istanze
		shapeRepresentation_trsfs = SHAPE_REPRESENTATION(unit)
		shapeRepresentation_trsfs.items.append(ident_transf)
		shapeRepresentation_trsfs.items.append(transf)

		shapeOriginalWithProductInfo = SHAPE_DEFINITION_REPRESENTATION(prod_def_shape, shapeRepresentation_trsfs)

		idt = ITEM_DEFINED_TRANSFORMATION('', None, ident_transf, transf)
		rr_transf = _createTransformation(advShapeRepresentation, shapeRepresentation_trsfs, idt)
		prod_transf = PRODUCT('', frames)
		prod_transf_def_form = PRODUCT_DEFINITION_FORMATION(prod_transf.name + '_trans_def_form', prod_transf)
		prod_transf_def = PRODUCT_DEFINITION(prod.name + '_trans_def', prod_transf_def_form, prod_def_ctx)
		prod_transf_def_shape = PRODUCT_DEFINITION_SHAPE(name + '_transdef_shape', '', prod_transf_def)
		nass = NEXT_ASSEMBLY_USAGE_OCCURRENCE(name + '_inst', name + '_inst', '', shapeOriginalWithProductInfo.definition.definition, prod_transf_def)
		prod_def_shape_nass = PRODUCT_DEFINITION_SHAPE('', None, nass)
		CONTEXT_DEPENDENT_SHAPE_REPRESENTATION(rr_transf, prod_def_shape_nass)
		shapeToBeTransformed = SHAPE_DEFINITION_REPRESENTATION(prod_transf_def_shape, advShapeRepresentation)
		shapeToBeTransformed.representation = advShapeRepresentation
		shapeRet = shapeToBeTransformed
	else:
		shapeRepresentation = SHAPE_REPRESENTATION(unit)
		shapeRepresentation.items.append(lump)
		shapeOriginalWithProductInfo = SHAPE_DEFINITION_REPRESENTATION(prod_def_shape, shapeRepresentation)
		shapeOriginalWithProductInfo.representation = shapeRepresentation
		shapeRet = shapeOriginalWithProductInfo

	for acisShell in acisLump.getShells():
		shell = _convertShell(acisShell, shapeRet.representation, color)
		if (not lump.add(shell)):
			logError("Failed to create shell %s", acisShell)

	return shapeRet

def _convertBody(acisBody, appPrtDef):
	bodies = []

	name = acisBody.getName()
	if ((name is None) or (len(name) == 0)):
		name = "Body_%02d" %(acisBody.index)

	transform = acisBody.getTransform()
	if (transform):
		transformation = transform.getPlacement()
	else:
		transformation = TRANSFORM_NONE
	for acisLump in acisBody.getLumps():
		lump = _convertLump(acisLump, name, appPrtDef.application, getColor(acisBody), transformation)
		if (lump):
			bodies.append(lump.getProduct())

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
				p.has_been_exported = b
			else:
				l[p].has_been_exported = b
	if (isinstance(l, ExportEntity)):
		l.has_been_exported = b

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
		self.has_been_exported = False
	def _getClassName(self):
		return self.__class__.__name__
	def exportProperties(self):
		step = u""
		variables = self._getParameters()
		for a in variables:
			try:
				if (isinstance(a, ReferencedEntity)):
					step += a.exportSTEP()
				elif (type(a) in (list, tuple)):
					step += _exportInternalList_(a)
			except:
				logError(traceback.format_exc())
		return step
	def exportSTEP(self):
		if (self.has_been_exported):
			return ''
		step = u""
		if (hasattr(self, '__acis__')):
			if (self.__acis__.subtype == 'ref'):
				step += u"/*\n * ref = %d\n */\n" %(self.__acis__.ref)
			else:
				step += u"/*\n * $%d\n */\n" %(self.__acis__.index)
		step += u"%s;\n" %(self.__repr__())
		step += self.exportProperties()
		self.has_been_exported = True
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

class PRODUCT_DEFINITION_RELATIONSHIP(NamedEntity):
	def __init__(self, identifier = None, name = None, description = None, relating_product_definition = None, related_product_definition = None):
		super(PRODUCT_DEFINITION_RELATIONSHIP, self).__init__(name)
		self.identifier = identifier
		self.description = description
		self.relating_product_definition = relating_product_definition
		self.related_product_definition	= related_product_definition
	def _getParameters(self):
		return super(PRODUCT_DEFINITION_RELATIONSHIP, self)._getParameters() + [self.identifier, self.description, self.relating_product_definition, self.related_product_definition]

class PRODUCT_DEFINITION_USAGE(PRODUCT_DEFINITION_RELATIONSHIP):
	def __init__(self, identifier = None, name = None, description = None, relating_product_definition = None, related_product_definition = None):
		super(PRODUCT_DEFINITION_USAGE, self).__init__(identifier, name, description, relating_product_definition, related_product_definition)
	def _getParameters(self):
		return super(PRODUCT_DEFINITION_USAGE, self)._getParameters()

class ASSEMBLY_COMPONENT_USAGE(PRODUCT_DEFINITION_USAGE):
	def __init__(self, identifier = None, name = None, description = None, relating_product_definition = None, related_product_definition = None, reference_designator = None):
		super(ASSEMBLY_COMPONENT_USAGE, self).__init__(identifier, name, description, relating_product_definition, related_product_definition)
		self.reference_designator = reference_designator
	def _getParameters(self):
		return super(ASSEMBLY_COMPONENT_USAGE, self)._getParameters() + [self.reference_designator]

class NEXT_ASSEMBLY_USAGE_OCCURRENCE(ASSEMBLY_COMPONENT_USAGE):
	def __init__(self, identifier = None, name = None, description = None, relating_product_definition = None, related_product_definition = None, reference_designator = None):
		super(NEXT_ASSEMBLY_USAGE_OCCURRENCE, self).__init__(identifier, name, description, relating_product_definition, related_product_definition, reference_designator)
	def _getParameters(self):
		return super(NEXT_ASSEMBLY_USAGE_OCCURRENCE, self)._getParameters()

class PRODUCT(ReferencedEntity):
	def __init__(self, name, frames):
		super(PRODUCT, self).__init__()
		self.identifier = name
		self.name = name
		self.description = ''
		self.frames = frames
	def _getParameters(self):
		return super(PRODUCT, self)._getParameters() + [self.identifier, self.name, self.description, self.frames]

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
		self.location = location
		self.axis     = axis
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
		if (self.has_been_exported):
			return ''
		step = u""
		if (hasattr(self, '__acis__')):
			if (self.__acis__.subtype == 'ref'):
				step += u"/*\n * ref = %d\n */\n" %(self.__acis__.ref)
			else:
				step += u"/*\n * $%d\n */\n" %(self.__acis__.index)
		step += u"%r;\n" %(self)
		for e in self.entities:
			try:
				if (isinstance(e, ExportEntity)):
					step += e.exportProperties()
				elif (type(e) == list):
					step += _exportInternalList_(e)
				elif (type(e) == tuple):
					step += _exportInternalList_(e)
			except:
				logError(traceback.format_exc())
		self.has_been_exported = True
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
		self.has_been_exported = True
	def _getParameters(self):
		l = super(NAMED_UNIT, self)._getParameters()
		if (self.dimensions):
			l += [self.dimensions]
		return l

class LENGTH_UNIT(NAMED_UNIT):
	def __init__(self, dimensions):
		super(LENGTH_UNIT, self).__init__(dimensions)

class REPRESENTATION_RELATIONSHIP(NamedEntity):
	def __init__(self, descr = None, repr1 = None, repr2 = None):
		super(REPRESENTATION_RELATIONSHIP, self).__init__()
		self.description = descr
		self.repr1		 = repr1
		self.repr2		 = repr2
		self.has_been_exported = True # fa parte di una listEntity
	def _getParameters(self):
		return super(REPRESENTATION_RELATIONSHIP, self)._getParameters() + [self.description, self.repr1, self.repr2]

#The entity shape_representation_relationship_is a subtype of representation_relationship. The subtype adds
#specific local constraints that ensures that it defines a relationship between two shape_representations. To
#define a relationship between two shape_representations that is established via a transformation, a complex
#instantiation of shape_representation_relationship AND representation_relationship_with_transformation is
#used.
class SHAPE_REPRESENTATION_RELATIONSHIP(REPRESENTATION_RELATIONSHIP):
	def __init__(self, repr1 = None, repr2 = None):
		super(SHAPE_REPRESENTATION_RELATIONSHIP, self).__init__(repr1, repr2)
		self.has_been_exported = True # fa parte di una listEntity
	def _getParameters(self):
		return [] # nella pratica shape_representation_relationship e sempre senza argomenti

#The entity representation_relationship_with_transformation_is a subtype of representation_relationship.
#The subtype adds the attribute transformation_operator as a reference to a transformation. To define a
#relationship between two shape_representations that is established via a transformation, a complex
#instantiation of shape_representation_relationship AND representation_relationship_with_transformation is
#used.
#NOTA peccato che nella pratica shape_representation_relationship sia sempre senza argomenti
class REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION(REPRESENTATION_RELATIONSHIP):
	def __init__(self, transform):
		super(REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION, self).__init__()
		self.transform = transform
		self.has_been_exported = True # fa parte di una listEntity
	def _getParameters(self):
		return [self.transform] # MC non mi interessa del resto

#An item_defined_transformation models a transformation performed by defining two representation_items
#before and after applying the transformation function The transformation function is not explicitly
#provided, but it is derived through its relationship to the representation_items.
class ITEM_DEFINED_TRANSFORMATION(NamedEntity):
	def __init__(self, name = '', description = None, trans_before = None, trans_after = None):
		self.description = description
		self.trans_before = trans_before
		self.trans_after = trans_after
		super(ITEM_DEFINED_TRANSFORMATION, self).__init__(name)
	def _getParameters(self):
		return super(ITEM_DEFINED_TRANSFORMATION, self)._getParameters() + [self.description, self.trans_before, self.trans_after]

#The relationships between the assembly and the component on the product_definition level and the shape_-
#representation level has to be linked through a context_dependent_shape_representation. This is necessary
#to distinguish between several occurrences of the same component within an assembly
#A context_dependent_shape_representation associates a shape_representation_relationship with a product_-
#definition_shape. In the given context this allows the explicit specification of a shape of the assembly 'as
#assembled'. Since elements when assembled might change their shape - e.g., under pressure - this
#representation may differ from the geometric assembly of the individual shapes.
class CONTEXT_DEPENDENT_SHAPE_REPRESENTATION(ExportEntity):
	def __init__(self, shape_unassembled = None, shape_assembled = None):
		super(CONTEXT_DEPENDENT_SHAPE_REPRESENTATION, self).__init__()
		self.shape_unassembled = shape_unassembled
		self.shape_assembled = shape_assembled
	def _getParameters(self):
		return [self.shape_unassembled, self.shape_assembled] # MC non mi interessa di scrivere il nome

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
		self.name = name
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
		self.has_been_exported = True

class LENGTH_MEASURE(ValueObject):
	def __init__(self, value):
		super(LENGTH_MEASURE, self).__init__(value)
		self.has_been_exported = True

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
		self.has_been_exported = True
	def _getParameters(self):
		return super(GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT, self)._getParameters() + [self.units]

class GLOBAL_UNIT_ASSIGNED_CONTEXT(ExportEntity):
	def __init__(self):
		super(GLOBAL_UNIT_ASSIGNED_CONTEXT, self).__init__()
		self.assignments = []
		self.has_been_exported = True
	def _getParameters(self):
		return super(GLOBAL_UNIT_ASSIGNED_CONTEXT, self)._getParameters() + [self.assignments]

class REPRESENTATION_CONTEXT(ExportEntity):
	def __init__(self, identifier = '', t = '3D'):
		super(REPRESENTATION_CONTEXT, self).__init__()
		self.identifier = identifier
		self.type = t
		self.has_been_exported = True
	def _getParameters(self):
		return super(REPRESENTATION_CONTEXT, self)._getParameters() + [self.identifier, self.type]

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
		self.luminosity  = luminosity
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
	def __init__(self, name = None, description = None, definition = None):
		super(PRODUCT_DEFINITION_SHAPE, self).__init__(name)
		self.description = description
		self.definition  = definition
	def _getParameters(self):
		return super(PRODUCT_DEFINITION_SHAPE, self)._getParameters() + [self.description, self.definition]

class REPRESENTATION(NamedEntity):
	def __init__(self, context):
		super(REPRESENTATION, self).__init__('')
		#The items attribute collects the items of the shape_representation.
		self.items = []
		# The context_of_items attribute references a geometric_representation_context that establishes
		# the coordinate space for the shape_representation
		self.context = context
	def _getParameters(self):
		return super(REPRESENTATION, self)._getParameters() + [self.items, self.context]

class SHAPE_REPRESENTATION(REPRESENTATION):
	def __init__(self, context):
		super(SHAPE_REPRESENTATION, self).__init__(context)
	def _getParameters(self):
		return super(SHAPE_REPRESENTATION, self)._getParameters()

class MANIFOLD_SURFACE_SHAPE_REPRESENTATION(SHAPE_REPRESENTATION):
	def __init__(self):
		super(MANIFOLD_SURFACE_SHAPE_REPRESENTATION, self).__init__()

class SHAPE_DEFINITION_REPRESENTATION(ReferencedEntity):
	def __init__(self, definition = None, representation = None):
		super(SHAPE_DEFINITION_REPRESENTATION, self).__init__()
		self.definition = definition
		self.representation = representation
	def _getParameters(self):
		return super(SHAPE_DEFINITION_REPRESENTATION, self)._getParameters() + [self.definition, self.representation]
	def getProduct(self):
		return self.definition.definition.formation.product
	def getAppContext(self):
		return self.definition.definition.frame.context

class PRODUCT_DEFINITION_FORMATION(NamedEntity):
	def __init__(self, name, product):
		super(PRODUCT_DEFINITION_FORMATION, self).__init__(name)
		self.description = ''
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
	def __init__(self, name, formation, context):
		super(PRODUCT_DEFINITION, self).__init__(name)
		self.description = ''
		self.formation   = formation
		self.frame       = context
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
	def addFace(self, face):
		if (face): self.faces.append(face)
		return not face is None

class SHELL_BASED_SURFACE_MODEL(NamedEntity):
	def __init__(self, ):
		super(SHELL_BASED_SURFACE_MODEL, self).__init__('')
		self.items = []
	def _getParameters(self):
		return super(SHELL_BASED_SURFACE_MODEL, self)._getParameters() + [self.items]
	def add(self, child):
		if (child): self.items.append(child)
		return not child is None

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
		self.name = name

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
	def __init__(self, name='', degree=None, points=None, form=None, closed=None, selfIntersecting=None):
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
		self.mults = mults
		self.knots = knots
		self.form2 = _getE(form2)
	def _getParameters(self):
		l = super(B_SPLINE_CURVE_WITH_KNOTS, self)._getParameters()
		if (self.mults is not None): l.append(self.mults)
		if (self.knots is not None): l.append(self.knots)
		if (self.form2 is not None): l.append(self.form2)
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
		self.name             = name
		self.uDegree          = uDegree
		self.vDegree          = vDegree
		self.points           = points
		self.form             = _getE(form)
		self.uClosed          = uClosed
		self.vClosed          = vClosed
		self.selfIntersecting = selfIntersecting
		self.uMults           = uMults
		self.vMults           = vMults
		self.uKnots           = uKnots
		self.vKnots           = vKnots
		self.form2            = _getE(form2)
	def _getParameters(self):
		l = super(B_SPLINE_SURFACE_WITH_KNOTS, self)._getParameters()
		if (self.name             is not None): l.append(self.name)
		if (self.uDegree          is not None): l.append(self.uDegree)
		if (self.vDegree          is not None): l.append(self.vDegree)
		if (self.points           is not None): l.append(self.points)
		if (self.form             is not None): l.append(self.form)
		if (self.uClosed          is not None): l.append(self.uClosed)
		if (self.vClosed          is not None): l.append(self.vClosed)
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
	global _scale, _entities

	dt     = datetime.now() # 2018-05-13T08:03:27-07:00
	user   = getAuthor()
	desc   = getDescription()
	orga   = ''
	proc   = 'InventorImporter'
	auth   = ''

	_initExport()

	_scale = satHeader.scale

	appPrtDef = APPLICATION_PROTOCOL_DEFINITION()

	for body in satBodies:
		body.name = filename
		part = _convertBody(body, appPrtDef)
		# MC: fanno tutti 1 body -> 1 parte
		PRODUCT_RELATED_PRODUCT_CATEGORY('part', part)

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

	for entity in _entities:
		step += entity.exportSTEP()

	step += u"ENDSEC;\n"
	step += u"END-ISO-10303-21;"

	with io.open(stepfile, 'wt', encoding="UTF-8") as stepFile:
		stepFile.write(step)

	_finalizeExport()

	logInfo(u"STEP file written to '%s'.", stepfile)

	return stepfile #MC: non lo usa nessuno
