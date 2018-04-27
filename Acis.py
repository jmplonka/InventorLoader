# -*- coding: utf-8 -*-

'''
Acis.py:
Collection of classes necessary to read and analyse Standard ACIS Text (*.sat) files.
'''

import traceback, FreeCAD, math, Part, Draft
from importerUtils import LOG, logMessage, logWarning, logError, isEqual, getUInt8, getUInt16, getSInt32, getFloat64, getFloat64A, getUInt32, ENCODING_FS
from FreeCAD       import Vector as VEC, Rotation as ROT, Placement as PLC, Matrix as MAT, Base
from math          import pi, fabs

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

V2D = Base.Vector2d

ENTIY_VERSIONS = {
	'ADV_BL_VERSION': 1.8,
	'ADV_VAR_BLEND_TWO_RADII_VERSION': 2.2,
	'ANG_XCUR_VERSION': 1.7,
	'ANNO_HOOKED_VERSION': 7.0,
	'APPROX_SUMMARY_VERSION': 5.0,
	'ARCWISE_SKIN_VERSION': 2.2,
	'AT_VERSION': 7.0,
	'BLEND_VERSION': 1.5,
	'BL_ENV_SF_VERSION': 4.0,
	'BNDCUR_VERSION': 1.6,
	'BNDSUR_VERSION': 1.6,
	'COEDGE_SENSE_VERSION': 2.2,
	'CONE_SCALING_VERSION': 4.0,
	'CONSISTENT_VERSION': 2.0,
	'CURVE_VERSION': 1.3,
	'DISCONTINUITY_VERSION': 3.0,
	'DM_60_VERSION': 6.0,
	'DM_MULTI_SURF_COLOR_VERSION': 6.0,
	'DM_MULTI_SURF_VERSION': 5.0,
	'DOLLAR_VERSION': 1.3,
	'EELIST_OWNER_VERSION': 6.0,
	'ELLIPSE_OFFSET_VERSION': 5.0,
	'ENTITY_TAGS_VERSION': 7.0,
	'EXT_CU_SF_VERSION': 2.1,
	'FILEINFO_VERSION': 2.0,
	'FILEINTERFACE_VERSION': 1.6,
	'GA_COPY_ACTION_VERSION': 6.0,
	'HISTORY_VERSION': 1.7,
	'INFINT_VERSION': 1.6,
	'INTCURVE_VERSION': 1.3,
	'LAW_VERSION': 2.2,
	'LAW_SPL_VERSION': 4.0,
	'LAZY_B_SPLINE_VERSION': 5.0,
	'LOFT_LAW_VERSION': 4.0,
	'LOFT_PCURVE_VERSION': 6.0,
	'LOGIO_VERSION': 1.5,
	'LUMP_VERSION': 1.1,
	'MESH_VERSION': 2.0,
	'MULTSAV_VERSION': 1.5,
	'NET_LAW_VERSION': 7.0,
	'NET_SPL_VERSION': 3.0,
	'OFFSET_REV_VERSION': 2.2,
	'PARAM_VERSION': 1.1,
	'PARCUR_VERSION': 1.5,
	'PATTERN_VERSION': 7.0,
	'PCURVE_VERSION': 1.5,
	'RECAL_SKIN_ERROR_VERSION': 5.2,
	'REF_MIN_UV_GRID_VERSION': 4.0,
	'SAFERANGE_VERSION': 1.7,
	'SHARABLE_VERSION': 1.4,
	'SORTCOED_VERSION': 1.5,
	'SPLINE_VERSION': 1.3,
	'STRINGLESS_HISTORY_VERSION': 7.0,
	'SURFACE_VERSION': 1.3,
	'TAPER_EXISTENCE_VERSION': 2.1,
	'TAPER_VERSION': 3.0,
	'TAPER_SCALING_VERSION': 5.0,
	'TAPER_U_RULED_VERSION': 6.0,
	'THREEDEYE_REF_VERSION': 1.7,
	'TOL_MODELING_VERSION': 5.0,
	'TWOSIDE_VERSION': 1.5,
	'VBLEND_AUTO_VERSION': 4.0,
	'WIREBOOL_VERSION': 1.7,
}

MIN_0   = 0.0
MIN_PI  = -pi
MIN_PI2 = -pi / 2
MIN_INF = float('-inf')

MAX_2PI = 2 * pi
MAX_PI  = pi
MAX_PI2 = pi / 2
MAX_INF = float('inf')
MAX_LEN = 0.5e+07

CENTER = VEC(0, 0, 0)
DIR_X  = VEC(1, 0, 0)
DIR_Y  = VEC(0, 1, 0)
DIR_Z  = VEC(0, 0, 1)

RANGE      = {0x0B: 'I',          0x0A: 'F'}
REFLECTION = {0x0B: 'no_reflect', 0x0A: 'reflect'}
ROTATION   = {0x0B: 'no_rotate',  0x0A: 'rotate'}
SHEAR      = {0x0B: 'no_shear',   0x0A: 'shear'}
SENSE      = {0x0B: 'forward',    0x0A: 'reversed'}
SENSEV     = {0x0B: 'forward_v',  0x0A: 'reverse_v'}
SIDES      = {0x0B: 'single',     0x0A: 'double'}
SIDE       = {0x0B: 'out',        0x0A: 'in'}

SURF_BOOL  = {0x0B: 'FALSE',      0x0A: 'TRUE'}
SURF_NORM  = {0x0B: 'ISO',        0x0A: 'UNKNOWN'}
SURF_DIR   = {0x0B: 'SKIN',       0x0A: 'PERPENDICULAR'}
SURF_SWEEP = {0x0B: 'angled',     0x0A: 'normal'}

CIRC_TYP  = {0x0B: 'non_cross',   0x0A: 'cross'}
CIRC_SMTH = {0x0B: 'normal',      0x0A: 'smooth'}

CLOSURE     = {0: 'open', 1: 'closed', 2: 'periodic', '0x0B': 'open', '0x0A': 'periodic'}
SINGULARITY = {0: 'full', 1: 'v',      2: 'none',     '0x0B': 'none', '0x0A': 'full'}
VBL_CIRLE   = {0: 'circle', 1: 'ellipse', 3: 'unknown', 'cylinder': 'circle'}

scale   = 1.0

version = 7.0

subtypeTable = {}

references = {}

def addNode(node):
	if (node.entity is not None):
		subtype = node.getType()
		i = subtype.rfind('-')
		if (i > 0):
			subtype = subtype[0:i]

def addSubtypeNode(subtype, node):
	global subtypeTable
	try:
		refs = subtypeTable[subtype]
	except KeyError:
		refs = []
		subtypeTable[subtype] = refs
	refs.append(node)

def getSubtypeNode(subtype, index):
	global subtypeTable
	try:
		refs = subtypeTable[subtype]
		return refs[index]
	except:
		return None

def clearEntities():
	global subtypeTable, references
	subtypeTable.clear()
	references.clear()

def setScale(value):
	global scale
	scale = value
	return scale

def getScale():
	global scale
	return scale

def setVersion(vers):
	global version
	version = vers

def getVersion():
	global version
	return version

def createNode(entity):
	global references

	try:
		if (entity.index < 0):
			return
		node = references[entity.index]
		# this entity is overwriting a previus entity with the same index -> ignore it
		logWarning("    Found 2nd '-%d %s' - IGNORED!" %(entity.index, entity.name))
		entity.node = node
	except:
		try:
			node = ENTITY_TYPES[entity.name]()
		except:
			#try to find the propriate base class
			types = entity.name.split('-')
			i = 1
			node = Entity()
			t = 'Entity'
			while (i<len(types)):
				try:
					t = "-".join(types[i:])
					node = ENTITY_TYPES[t]()
					i = len(types)
				except Exception as e:
					i += 1
			logError("TypeError: Can't find class for '%s' - using '%s'!" %(entity.name, t))

		if (entity.index >= 0):
			references[entity.index] = node
		if (hasattr(node, 'set')):
			node.set(entity)

def getValue(chunks, index):
	val = chunks[index].val
	return val, index + 1

def getRefNode(entity, index, name):
	val, i = getValue(entity.chunks, index)
	if (isinstance(val, AcisRef)):
		ref = val.entity
		if (name is not None) and (ref is not None) and (ref.name.endswith(name) == False):
			raise Exception("Excpeced %s but found %s" %(name, ref.name))
	else:
		raise Exception("Chunk at index=%d, is not a reference" %(index))
	return ref, i

def getEnum(chunks, index):
	tag = chunks[index].tag
	assert (tag == 0x0A) or (tag == 0x0B)
	return tag, index + 1

def getInteger(chunks, index):
	val, i = getValue(chunks, index)
	return int(val), i

def getIntegers(chunks, index, count):
	i = index
	arr = []
	for n in range(0, count):
		n, i = getInteger(chunks, i)
		arr.append(n)
	return arr, i

def getLong(chunks, index):
	val, i = getValue(chunks, index)
	return long(val), i

def getFloat(chunks, index):
	val, i = getValue(chunks, index)
	return float(val), i

def getFloats(chunks, index, count):
	i = index
	arr = []
	for n in range(0, count):
		f, i = getFloat(chunks, i)
		arr.append(f)
	return arr, i

def getFloatArray(chunks, index):
	n, i = getInteger(chunks, index)
	arr, i = getFloats(chunks, i, n)
	return arr, i

def getLength(chunks, index):
	l, i = getFloat(chunks, index)
	return l * getScale(), i

def getText(chunks, index):
	return getValue(chunks, index)

def getEnumByTag(chunks, index, values):
	chunk = chunks[index]
	try:
		return values[chunk.tag], index + 1
	except:
		return chunk.val, index + 1

def getEnumByValue(chunks, index, values):
	val, i = getValue(chunks, index)
	try:
		return values[val], index + 1
	except:
		return val, index + 1

def getReflection(chunks, index):
	return getEnumByTag(chunks, index, REFLECTION)

def getRotation(chunks, index):
	return getEnumByTag(chunks, index, ROTATION)

def getShear(chunks, index):
	return getEnumByTag(chunks, index, SHEAR)

def getSense(chunks, index):
	return getEnumByTag(chunks, index, SENSE)

def getSensev(chunks, index):
	return getEnumByTag(chunks, index, SENSEV)

def getSides(chunks, index):
	sides, i = getEnumByTag(chunks, index, SIDES)
	if (sides == 'double'):
		side, i = getSide(chunks, i)
		return sides, side, i
	return sides, None, i

def getSide(chunks, index):
	return getEnumByTag(chunks, index, SIDE)

def getClosure(chunks, index):
	closure, i = getEnumByValue(chunks, index, CLOSURE)
	closure = closure.lower()
	return closure, i

def getSingularity(chunks, index):
	if (getVersion() > 4):
		return getEnumByValue(chunks, index, SINGULARITY)
	return 'full', index

def getVblCirleType(chunks, index):
	return getEnumByValue(chunks, index, VBL_CIRLE)

def getSurfBool(chunks, index):
	return getEnumByTag(chunks, index, SURF_BOOL)

def getSurfNorm(chunks, index):
	return getEnumByTag(chunks, index, SURF_NORM)

def getSurfDir(chunks, index):
	return getEnumByTag(chunks, index, SURF_DIR)

def getSurfSweep(chunks, index):
	return getEnumByTag(chunks, index, SURF_SWEEP)

def getCircleType(chunks, index):
	return getEnumByTag(chunks, index, CIRC_TYP)

def getCircleSmoothing(chunks, index):
	return getEnumByTag(chunks, index, CIRC_SMTH)

def getUnknownFT(chunks, index):
	i = index
	val = 'F'
	if (getVersion() > 7.0):
		val, i = getValue(chunks, i)
		if (val == 'T'):
			arr, i = getFloats(chunks, i, 6)
			val2, i = getValue(chunks, i)
			return (val, arr, val2), i
	return (val, [], 'F'), i

def getRange(chunks, index, default, scale):
	type, i = getEnumByTag(chunks, index, RANGE)
	val = default
	if (type == 'F'):
		val, i = getFloat(chunks, i)
	elif (type == 'T'):
		arr, i = getFloats(chunks, i, 7)
		val = arr[0]
	return Range(type, val, scale), i

def getInterval(chunks, index, defMin, defMax, scale):
	lower, i = getRange(chunks, index, defMin, scale)
	upper, i = getRange(chunks, i, defMax, scale)
	return Intervall(lower, upper), i

def getPoint(chunks, index):
	chunk = chunks[index]
	if ((chunk.tag == 0x13) or (chunk.tag == 0x14)):
		return chunk.val, index + 1
	x, i =  getFloat(chunks, index)
	y, i =  getFloat(chunks, i)
	z, i =  getFloat(chunks, i)
	return (x, y, z), i

def getVector(chunks, index):
	p, i = getPoint(chunks, index)
	return VEC(p[0], p[1], p[2]), i

def getLocation(chunks, index):
	v, i = getVector(chunks, index)
	return v * getScale(), i

def getBlock(chunks, index):
	data = []
	i = index + 1
	chunk = chunks[i]
	while (chunk.tag != 0x10):
		data.append(chunk)
		if (chunk.tag == 0x0F):
			block, i = getBlock(chunks, i)
			data += block
		else:
			i += 1
		chunk = chunks[i]
	data.append(chunk)
	return data, i + 1

def getDimensionCurve(chunks, index):
	# DIMENSION = (nullbs|nurbs [:NUMBER:]|nubs [:NUMBER:])
	val, i  = getValue(chunks, index)
	if (val == 'nullbs'):
		return val, 0, i
	if (val in ('nurbs', 'nubs')):
		degrees, i = getInteger(chunks, i)
		return val, degrees, i
	raise Exception("Unknown DIMENSION '%s'" %(val))

def getDimensionSurface(chunks, index):
	# DIMENSION = (nullbs|nurbs [:NUMBER:]|nubs [:NUMBER:]|summary [:NUMBER: Version > 17])
	val, i = getValue(chunks, index)
	if (val == 'nullbs'):
		return val, None, None, i
	if (val in ('nurbs', 'nubs', 'summary')):
		degreesU, i = getInteger(chunks, i)
		degreesV, i = getInteger(chunks, i)
		return val, degreesU, degreesV, i
	raise Exception("Unknown DIMENSION '%s'" %(val))

def getClosureCurve(chunks, index):
	# CLOSURE = (open=0|closed=1|periodic=2)
	closure, i = getClosure(chunks, index)
	if (closure in ('open', 'closed', 'periodic')):
		knots, i = getInteger(chunks, i)
		return closure, knots, i
	raise Exception("Unknown closure '%s'!" %(closure))

def getClosureSurface(chunks, index):
	# Syntax: [:CLOSURE:] [:CLOSURE:] [:FULL:] [:FULL:] [:NUMBER:] [:NUMBER:]
	# CLOSURE = (open=0|closed=1|periodic=2)
	# FULL    = (full=0|none=1)

	closureU, i = getClosure(chunks, index)
	if (closureU in ('both', 'u', 'v')):
		closureU, i = getClosure(chunks, i)
	if (closureU in ('open', 'closed', 'periodic')):
		# open none none 2 2
		closureV, i = getClosure(chunks, i)
		singularityU, i = getEnumByValue(chunks, i, SINGULARITY)
		singularityV, i = getEnumByValue(chunks, i, SINGULARITY)
		knotsU, i = getInteger(chunks, i)
		knotsV, i = getInteger(chunks, i)
		return closureU, closureV, singularityU, singularityV, knotsU, knotsV, i

	raise Exception("Unknown closure '%s'!" %(closureU))

def readKnotsMults(count, chunks, index):
	knots = []
	mults = []
	i     = index
	j     = 0

	while (j < count):
		knot, i = getFloat(chunks, i)
		mult, i = getInteger(chunks, i)
		knots.append(knot)
		mults.append(mult)
		j += 1
	return knots, mults, i

def adjustMultsKnots(knots, mults, periodic, degree):
	mults[0] = degree + 1
	mults[-1] = degree + 1
	return knots, mults, False # Force periodic to False!!!

def readPoints2DList(nubs, count, chunks, index):
	nubs.uKnots, nubs.uMults, i = readKnotsMults(count, chunks, index)
	us = sum(nubs.uMults) - (nubs.uDegree - 1)
	nubs.poles   = [None for r in range(0, us)]
	nubs.weights = [1 for r in range(0, us)] if (nubs.rational) else None

	for k in range(0, us):
		u, i  = getLength(chunks, i)
		v, i  = getLength(chunks, i)
		nubs.poles[k] = V2D(u, v)
		if (nubs.rational): nubs.weights[k], i = getFloat(chunks, i)

	nubs.uKnots, nubs.uMults, nubs.uPeriodic = adjustMultsKnots(nubs.uKnots, nubs.uMults, nubs.uPeriodic, nubs.uDegree)

	return i

def readPoints3DList(nubs, count, chunks, index):
	nubs.uKnots, nubs.uMults, i = readKnotsMults(count, chunks, index)
	us = sum(nubs.uMults) - (nubs.uDegree - 1)
	nubs.poles   = [None for r in range(0, us)]
	nubs.weights = [1 for r in range(0, us)] if (nubs.rational) else None

	for u in range(0, us):
		nubs.poles[u], i = getLocation(chunks, i)
		if (nubs.rational): nubs.weights[u], i = getFloat(chunks, i)

	nubs.uKnots, nubs.uMults, nubs.uPeriodic = adjustMultsKnots(nubs.uKnots, nubs.uMults, nubs.uPeriodic, nubs.uDegree)
	return i

def readPoints3DMap(nubs, knotsU, knotsV, chunks, index):
	# row definitions
	nubs.uKnots, nubs.uMults, i = readKnotsMults(knotsU, chunks, index)
	# column definitions
	nubs.vKnots, nubs.vMults, i = readKnotsMults(knotsV, chunks, i)

	us = sum(nubs.uMults) - (nubs.uDegree - 1)
	vs = sum(nubs.vMults) - (nubs.vDegree - 1)

	nubs.poles   = [[None for c in range(0, vs)] for r in range(0, us)]
	nubs.weights = [[1 for c in range(0, vs)] for r in range(0, us)] if (nubs.rational) else None
	for v in range(0, vs):
		for u in range(0, us):
			nubs.poles[u][v], i  = getLocation(chunks, i)
			if (nubs.rational): nubs.weights[u][v], i = getFloat(chunks, i)

	nubs.uKnots, nubs.uMults, nubs.uPeriodic = adjustMultsKnots(nubs.uKnots, nubs.uMults, nubs.uPeriodic, nubs.uDegree)
	nubs.vKnots, nubs.vMults, nubs.vPeriodic = adjustMultsKnots(nubs.vKnots, nubs.vMults, nubs.vPeriodic, nubs.vDegree)

	return i

def readBlend(chunks, index):
	nubs, i = readBS2Curve(chunks, index)
	if (nubs is not None):
		nubs.sense, i = getSense(chunks, i)
		nubs.factor, i = getFloat(chunks, i)
		return nubs, i
	return None, index

def readLaw(chunks, index):
	# Laws:
	#	trigonometric:
	#		cos(x), cosh(x), cot(x) = cos(x)/sin(x), coth(x)
	#		csc(x) = 1/sin(x), csch(x), sec(x) = 1/cos(x), sech(x)
	#		sin(x), sinh(x), tan(x), tanh(x)
	#		arccos(x), arccosh(x), arcot(x), arcoth(x)
	#		arccsc(x), arccsch(x), arcsec(x), arcsech(x)
	#		arcsin(x), arcsinh(x), arctan(x), arctanh(x)
	#	functions:
	#		vec(x,y,z)
	#		abs(x), exp(x), ln(x), log(x), norm(X), sqrt(x)
	#		rotate(x,y), set(x) = sign(x), size(x), step(...)
	#		term(X,n), trans(X,y)
	#		min(x), max(x), not(x)
	#	operators:
	#		+,-,*,/,x,^,<,>,<=,>=
	#	constants
	#		e = 2.718
	#		pi= 3.141
	n, i = getText(chunks, index)
	if (n == 'TRANS'):
		v = Transform()
		i = v.setBulk(chunks, i)
	elif (n == 'EDGE'):
		c, i = readCurve(chunks, i)
		f, i = getFloats(chunks, i, 2)
		v = (c, f)
	elif (n == 'SPLINE_LAW'):
		a, i = getInteger(chunks, i)
		b, i = getFloatArray(chunks, i)
		c, i = getFloatArray(chunks, i)
		d, i = getPoint(chunks, i)
		v = (a, b, c, d)
	else:
		v = None

	return (n, v), i

def newInstance(CLASSES, key):
	cls = CLASSES[key]
	if (cls is None):
		return None
	return cls()

def readCurve(chunks, index):
	val, i = getValue(chunks, index)
	curve = None
	try:
		curve = newInstance(CURVES, val)
	except:
		raise Exception("Unknown curve-type '%s'!" % (val))
	if (curve):
		i = curve.setSubtype(chunks, i)
	return curve, i

def readSurface(chunks, index):
	chunk = chunks[index]
	i = index + 1
	subtype = chunk.val
	tag = chunk.tag
	if ((tag == 0x07) or (tag == 0x0D)):
		surface = None
		try:
			surface = newInstance(SURFACES, subtype)
		except:
			raise Exception("Unknown surface-type '%s'!" % (subtype))
		if (surface):
			i = surface.setSubtype(chunks, i)
		return surface, i
#FIXME: this is a dirty hack :(
	elif (tag == 0x06):
		a, i = getFloats(chunks, index, 5)
		return None, i
	elif ((tag == 0x13) or (tag == 0x14)):
		a, i = getFloats(chunks, i, 2)
		return None, i

def readArrayFloats(chunks, index, inventor):
	a1, i = getFloatArray(chunks, index)
	a2, i = getFloatArray(chunks, i)
	a3, i = getFloatArray(chunks, i)
	a4, i = getFloatArray(chunks, i)
	a5, i = getFloatArray(chunks, i)
	a6, i = getFloatArray(chunks, i)
	if (inventor and chunks[i].tag in (0x0A, 0x0B)):
		e, i = getEnum(chunks, i)
	else:
		e = 0x0B
	return (a1, a2, a3, a4, a5, a6, e), i

def rotateShape(shape, dir):
	# Setting the axis directly doesn't work for directions other than x-axis!
	angle = math.degrees(DIR_Z.getAngle(dir))
	if (angle != 0):
		axis = DIR_Z.cross(dir) if angle != 180 else DIR_Z
		shape.rotate(PLC(CENTER, axis, angle))
	return

def getEdges(wires):
	edges = []
	for wire in wires:
		edges += wire.Edges
	return edges

def isBetween(a, c, b):
	ac = a.distanceToPoint(c)
	cb = c.distanceToPoint(b)
	ab = a.distanceToPoint(b)
	return ac + cb == ab

def isOnLine(fEdge, sEdge):
	sv = sEdge.Vertexes
	fv = fEdge.Vertexes
	s0 = sv[0].Point
	s1 = sv[1].Point
	result = (isBetween(s0, fv[0].Point, s1) and isBetween(s0, fv[1].Point, s1))
	return result
def isOnCircle(fEdge, sEdge):
	fc = fEdge.Curve
	sc = sEdge.Curve
	if (isEqual(fc.Location, sc.Location)):
		if (isEqual(fc.Axis, sc.Axis) or isEqual(-1 * fc.Axis, sc.Axis)):
			return (fc.Radius == sc.Radius)
	return False
def isOnEllipse(fEdge, sEdge):
	fc = fEdge.Curve
	sc = sEdge.Curve
	if (isEqual(fc.Location, sc.Location)):
		if (isEqual(fc.Axis, sc.Axis)):
			if (isEqual(fc.Focus1, sc.Focus1)):
				if (fc.MajorRadius == sc.MajorRadius):
					return (fc.MinorRadius == sc.MinorRadius)
	return False
def isOnBSplineCurve(fEdge, sEdge):
	sp = [v.Point for v in sEdge.Vertexes]
	fp = [v.Point for v in fEdge.Vertexes]
	if (len(sp) != len(fp)):
		return False
	for i, p in enumerate(sp):
		if (not isEqual(p, fp[i])):
			return False
	return True
def isSeam(edge, edges):
	seam = False
	for sEdge in edges:
		try:
			if (isinstance(edge.Curve, sEdge.Curve.__class__)):
				if (isinstance(edge.Curve, Part.Line) or isinstance(edge.Curve, Part.LineSegment)):
					seam |= isOnLine(edge, sEdge)
				elif (isinstance(edge.Curve, Part.Circle)):
					seam |= isOnCircle(edge, sEdge)
				elif (isinstance(edge.Curve, Part.Ellipse)):
					seam |= isOnEllipse(edge, sEdge)
				elif (isinstance(edge.Curve, Part.BSplineCurve)):
					seam |= isOnBSplineCurve(edge, sEdge)
		except:
			pass
	return seam

def isValid(face):
	for edge in face.Edges:
		for v in edge.Vertexes:
			if (v.Point.Length >= 0.4e+07):
				return False
	return True

def eliminateOuterFaces(faces, wires):
	edges = getEdges(wires)
	result = []
	for i, face in enumerate(faces):
		if (isValid(face)):
			matches = 0
			for fEdge in face.Edges:
				if (isSeam(fEdge, edges)):
					matches += 1
			if ((matches == len(edges)) and (matches == len(face.Edges))):
				return [face] #Teminator: "There Can Be Only One!"
			if (matches > 1):
				result.append(face)
	return result

def createEllipse(center, normal, major, ratio):
	radius = major.Length
	if (ratio == 1):
		ellipse = Part.Circle(center, normal, radius)
	else:
		ellipse = Part.Ellipse(center, radius, radius*ratio)
		ellipse.Axis  = normal
		ellipse.XAxis = major
	return ellipse

def createLine(start, end):
	line = Part.makeLine(start, end)
	return line

def createPolygon(points):
	l = len(points)
	if (l < 2):
		return None
	if (l == 2):
		return createLine(points[0], points[1])
	lines = [createLine(points[i], points[i+1]) for i in range(l-1)]
	return Part.Wire(lines)

def createBSplinesPCurve(pcurve, surface, sense):
	if (pcurve is None):
		return None
	if (surface is None):
		return None
	surf = surface.build()
	if (surf is None):
		return None
	number_of_poles = len(pcurve.poles)
	if (number_of_poles == 2): # if there are only two poles we can simply draw a line
		g2d = Part.Geom2d.Line2dSegment(pcurve.poles[0], pcurve.poles[1])
	else:
		g2d = Part.Geom2d.BSplineCurve2d()
		g2d.buildFromPolesMultsKnots(pcurve.poles, pcurve.uMults, pcurve.uKnots, pcurve.uPeriodic, pcurve.uDegree, pcurve.weights)
	shape = g2d.toShape(surf, g2d.FirstParameter, g2d.LastParameter)
	if (shape is not None):
		shape.Orientation = 'Reversed' if (sense == 'reversed') else 'Forward'
	return shape

def createBSplinesCurve(nubs, sense):
	if (nubs is None):
		return None
	number_of_poles = len(nubs.poles)
	if (number_of_poles == 2): # if there are only two poles we can simply draw a line
		shape = createLine(nubs.poles[0], nubs.poles[1])
	else:
		try:
			bsc = Part.BSplineCurve()
			if (nubs.rational):
				bsc.buildFromPolesMultsKnots(       \
					poles         = nubs.poles,     \
					mults         = nubs.uMults,    \
					knots         = nubs.uKnots,    \
					periodic      = nubs.uPeriodic, \
					degree        = nubs.uDegree,   \
					weights       = nubs.weights,   \
					CheckRational = nubs.rational
				)
			else:
				bsc.buildFromPolesMultsKnots(       \
					poles         = nubs.poles,     \
					mults         = nubs.uMults,    \
					knots         = nubs.uKnots,    \
					periodic      = nubs.uPeriodic, \
					degree        = nubs.uDegree,   \
					CheckRational = nubs.rational
			)
			shape = bsc.toShape()
		except Exception as e:
			logError('>E: ' + traceback.format_exc())
	if (shape is not None):
		shape.Orientation = 'Reversed' if (sense == 'reversed') else 'Forward'
	return shape

def createBSplinesSurface(nubs):
	if (nubs is None):
		return None
	try:
		bss = Part.BSplineSurface()
		if (nubs.rational):
			bss.buildFromPolesMultsKnots(       \
				poles     = nubs.poles,     \
				umults    = nubs.uMults,    \
				vmults    = nubs.vMults,    \
				uknots    = nubs.uKnots,    \
				vknots    = nubs.vKnots,    \
				uperiodic = nubs.uPeriodic, \
				vperiodic = nubs.vPeriodic, \
				udegree   = nubs.uDegree,   \
				vdegree   = nubs.vDegree,   \
				weights   = nubs.weights    \
			)
		else:
			bss.buildFromPolesMultsKnots(       \
				poles     = nubs.poles,     \
				umults    = nubs.uMults,    \
				vmults    = nubs.vMults,    \
				uknots    = nubs.uKnots,    \
				vknots    = nubs.vKnots,    \
				uperiodic = nubs.uPeriodic, \
				vperiodic = nubs.vPeriodic, \
				udegree   = nubs.uDegree,   \
				vdegree   = nubs.vDegree,   \
			)
		return bss.toShape()
	except Exception as e:
		logWarning('>E: %s' %(e))
	return None

def createHelix(data):
	axis = Draft.makeWire([data.axisStart, data.axisEnd], closed=False, face=False, support=None)
	axis.ViewObject.LineColor  = (0.0, 1.0, 0.0)
	axis.ViewObject.DrawStyle  = "Dashdot"
	axis.ViewObject.PointSize  = 1
	axis.Label = "Helix_Axis (%s)" %(axis.Length.Value)

	#helix = Part.makeHelix(pitch, height, radius, angle)
	#helix.LocalCoord=0
	#helix.Style = 1

	return None

def readBS2Curve(chunks, index):
	nbs, dgr, i = getDimensionCurve(chunks, index)
	if (nbs == 'nullbs'):
		return None, i
	if (nbs in ('nubs', 'nurbs')):
		closure, knots, i = getClosureCurve(chunks, i)
		nubs = BS3_Curve(nbs == 'nurbs', closure == 'periodic', dgr)
		i = readPoints2DList(nubs, knots, chunks, i)
		return nubs, i
	return None, index

def readBS3Curve(chunks, index):
	nbs, dgr, i = getDimensionCurve(chunks, index)
	if (nbs == 'nullbs'):
		return None, i
	if (nbs in ('nubs', 'nurbs')):
		closure, knots, i = getClosureCurve(chunks, i)
		nubs = BS3_Curve(nbs == 'nurbs', closure == 'periodic', dgr)
		i = readPoints3DList(nubs, knots, chunks, i)
		return nubs, i
	return None, index

def readBS3Surface(chunks, index):
	nbs, degreeU, degreeV, i = getDimensionSurface(chunks, index)
	if (nbs == 'nullbs'):
		return None, i
	if (nbs in ('nubs', 'nurbs')):
		closureU, closureV, singularityU, singularityV, knotsU, knotsV, i = getClosureSurface(chunks, i)
		nubs = BS3_Surface(nbs == 'nurbs', closureU == 'periodic', closureV == 'periodic', degreeU, degreeV)
		i = readPoints3DMap(nubs, knotsU, knotsV, chunks, i)
	return nubs, i

def readSplineSurface(chunks, index, tolerance):
	singularity, i = getSingularity(chunks, index)
	if (singularity == 'full'):
		spline, i = readBS3Surface(chunks, i)
		if ((spline is not None) and tolerance):
			tol, i = getFloat(chunks, i)
			return spline, tol * getScale(), i
		return spline, None, i
	if (singularity == 'none'):
		rU, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		rV, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		closureU, i = getClosure(chunks, i)
		closureV, i = getClosure(chunks, i)
		singularityU, i = getSingularity(chunks, i)
		singularityV, i = getSingularity(chunks, i)
		return None, (rU, rV, closureU, closureV, singularityU, singularityV), i
	elif (singularity == 'v'):
		a11, i = getFloatArray(chunks, i)
		a12, i = getFloatArray(chunks, i)
		f, i = getFloat(chunks, i)
		closureU, i = getClosure(chunks, i)
		closureV, i = getClosure(chunks, i)
		singularityU, i = getSingularity(chunks, i)
		singularityV, i = getSingularity(chunks, i)
		return None, (a11, a12, f, closureU, closureV, singularityU, singularityV), i
	elif (singularity == 4): # TODO what the heck is this???
		rU, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		rV, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		closureU, i = getClosure(chunks, i)
		closureV, i = getClosure(chunks, i)
		singularityU, i = getSingularity(chunks, i)
		singularityV, i = getSingularity(chunks, i)
		return None, (rU, rV, closureU, closureV, singularityU, singularityV), i

	raise Exception("Unknown spline singularity '%s'" %(singularity))

def readLofSubdata(chunks, i):
	type, i    = getInteger(chunks, i)
	n, i       = getInteger(chunks, i)
	m, i       = getInteger(chunks, i)
	# 0x0B 213 1 0 (0.0, 1.0 0.0, 1.0                                                  0x0B
	# 0x0B 212 1 0 (0.0, 1.0 0.0, 2.34107                                              0x0B
	# 0x0B 213 1 1 (0.0, 0.5 0.5, 0.75     0.5      0.5                                0x0B
	# 0x0B 213 1 2 (0.0, 1.0 0.0, 0.364571 0.364571 0.364571 0.0 0.0                   0x0B
	# 0x0B 212 1 2 (0.0, 1.0 0.0, 1.0      1.0      1.0      0.0 0.0                   0x0B
	# 0x0B 213 2 1 (0.0, 0.5 0.0, 0.5      1.0 1.0  0.5      1.0  0.5      1.0 1.0 1.0 0x0B
	# 0x0B 211 0 0 ()                                             2*PI, 0, 0, 1, 0x0B
	v = []
	if (type == 211):
		a, i = getFloats(chunks, i, 2)
		b, i = getFloats(chunks, i, 2)
		v.append((a, b, None))
	else:
		for k in range(0, n):
			a, i =  getFloats(chunks, i , 2)
			b, i =  getFloats(chunks, i , 2)
			p = []
			for l in range(0, m):
				c, i = getFloats(chunks, i, 2)
				p.append(c)
			v.append((a, b, p))
	return (type, n, m, v), i

def readLoftData(chunks, index):
	ld = LoftData()
	ld.surface, i = readSurface(chunks, index)
	ld.bs2cur, i  = readBS2Curve(chunks, i)
	ld.e1, i      = getEnum(chunks, i)
	subdata, i    = readLofSubdata(chunks, i)
	(ld.type, n, m, v) = subdata
	ld.e2, i      = getEnum(chunks, i)
	if (ld.e2 == 0x0A):
		ld.dir, i = getVector(chunks, i)
	return ld, i

def readLoftProfile(chunks, index):
	m, i = getInteger(chunks, index)
	section = []
	for l in range(0, m):
		t, i = getInteger(chunks, i)
		ck, i = readCurve(chunks, i)
		lk, i = readLoftData(chunks, i)
		section.append((t, ck, lk))
	return section, i

def readLoftPath(chunks, index):
	cur, i = readCurve(chunks, index)
	n, i = getInteger(chunks, i)
	paths = []
	for k in range(0, n):
		bs3, i = readBS3Curve(chunks, i)
		paths.append(bs3)
	f, i = getInteger(chunks, i)
	return (cur, paths, f), i

def readLofSection(chunks, index):
	n, i = getInteger(chunks, index)
	loft = []
	for k in range(0, n):
		fk, i = getFloat(chunks, i)
		profile, i = readLoftProfile(chunks, i)
		path, i = readLoftPath(chunks, i)
		loft.append((fk, profile, path))
	return loft, i

def readScaleClLoft(chunks, index):
	if (chunks[index].tag in (0x0A, 0x0B)):
		## fixme!
		return None, index
	n, i = getInteger(chunks, index)
	lofts = []
	for k in range(0, n):
		nk, i = getInteger(chunks, i)
		ck, i = readCurve(chunks, i)
		lk, i = readLoftData(chunks, i)
		lofts.append([nk, ck, lk])
	if (not chunks[i].tag in (0x07, 0x0D, 0x0E)):
		## fixme!
		return None, index
	cur, i = readCurve(chunks, i)
	n, i = getInteger(chunks, i) # 1
	bs3 = []
	for k in range(0, n):
		bs3c, i = readBS3Curve(chunks, i)
		bs3.append(bs3c)
	arr, i = getIntegers(chunks, i, 2) # BS3_CURVE,
	return (lofts, cur, bs3, arr), i

def readSkin(chunks, index, inventor):
	skin = Skin()
	skin.a1, i   = getIntegers(chunks, index, 4)
	skin.f1, i   = getFloat(chunks, i)
	if (inventor):
		n, i = getInteger(chunks, i)
		if (not chunks[i].tag in (0x07, 0x0D, 0x0E)):
			for k in range(0, n):
				i += 1
				skin.cur, i = readCurve(chunks, i)
				skin.loft, i = readLoftData(chunks, i)
			skin.cur2, i  = readCurve(chunks, i)
			i += 2 # 0, -1
		else:
			skin.cur, i = readCurve(chunks, i)
			skin.loft, i = readLofSubdata(chunks, i)
			i += 1
			skin.cur2, i  = readCurve(chunks, i)
			i += 1
		skin.vec, i  = getVector(chunks, i)
	else:
		skin.cur, i  = readCurve(chunks, i)
		skin.vec, i  = getVector(chunks, i)
		skin.surf, i = readSurface(chunks, i)
	skin.f2, i    = getFloat(chunks, i)
	skin.law, i  = readFormula(chunks, i)
	skin.pcur, i = readCurve(chunks, i)
	return skin, i

def readFormula(chunks, index):
	frml, i = getValue(chunks, index)
	if (frml == 'null_law'):
		return (None, []), i
	vars = []
	n, i = getInteger(chunks, i)
	for k in range(0, n):
		var, i = readLaw(chunks, i)
		vars.append(var)
	return (frml, vars), i

def readRbBlend(chunks, index, inventor):
	txt, i = getText(chunks, index)
	srf, i = readSurface(chunks, i)
	cur, i = readCurve(chunks, i)
	bs2, i = readBS2Curve(chunks, i)
	vec, i = getVector(chunks, i)
	if (inventor):
		dummy, i = readBS2Curve(chunks, i)
		spline, tol, i = readSplineSurface(chunks, i, False)
		return (txt, srf, cur, bs2, vec, (dummy, spline, tol)), i
	return (txt, srf, cur, bs2, vec, None), i

class VBL():
	def __init__(self):
		self.t  = ''
		self.n  = 'cross'
	def read(self, chunks, index, inventor):
		self.t, i = getText(chunks, index)
		self.n, i = getCircleType(chunks, i)
		self.p, i = getLocation(chunks, i)
		self.u, i = getCircleSmoothing(chunks, i)
		self.v, i = getCircleSmoothing(chunks, i)
		self.a, i = getFloat(chunks, i)
		if (self.t == 'circle'):
			self.o, i = readCurve(chunks, i)
			self.type, i = getVblCirleType(chunks, i)
			if (self.type == 'circle'):
				v1 = v2 = None
			elif (self.type == 'ellipse'):
				v1, i = getLocation(chunks, i)
				v2 = None
			elif (self.type == 'unknown'):
				v1, i = getLocation(chunks, i)
				v2, i = getLocation(chunks, i)
			else:
				raise Exception("Unknown VBL-Circle:form '%s'" %(self.type))
			self.v = (v1, v2)
			self.angles, i = getFloats(chunks, i, 2)
			self.sense, i  = getSense(chunks, i)
		elif (self.t == 'plane'):
			self.v, i = getLocation(chunks, i)
			self.a, i = getFloats(chunks, i, 2)
			self.o, i = readCurve(chunks, i)
		elif (self.t == 'pcurve'):
			self.o, i  = readSurface(chunks, i)
			self.c, i  = readBS2Curve(chunks, i)
			self.e6, i = getSense(chunks, i)
			self.f, i  = getFloat(chunks, i)
		else:
			raise Exception("Unknown VBL-type '%s'" %(self.t))
		return i
class LoftData():
	def __init__(self):
		self.surface = None
		self.bs2cur  = None
		self.e1      = 0x0B
		self.type    = 213
		self.n       = 1
		self.m       = 1
		self.v       = []
		self.e2      = 0x0B
class Skin():
	def __init__(self):
		self.a1   = [-1, -1, -1, -1]
		self.f    = MIN_0
		self.cur  = None
		self.a2   = [0.0, 0.0, 0.0]
		self.surf = None
		self.n    = 0
		self.law  = 'null_law'
		self.pcur = None
class BS3_Curve(object):
	def __init__(self, rational, periodic, degree):
		self.poles     = []       # sequence of VEC
		self.uMults    = ()       # tuple of int, e.g.  (3, 1,  3)
		self.uKnots    = ()       # tuple of float, eg. (0, 0.5, 1)
		self.uPeriodic = periodic # boolean
		self.uDegree   = degree   # int
		self.weights   = []       # sequence of float, e.g. (1, 0.8, 0.2), must have the same length as poles
		self.rational  = rational # boolean: False for nubs, True for nurbs
class BS3_Surface(BS3_Curve):
	def __init__(self, rational, uPeriodic, vPeriodic, uDegree, vDegree):
		super(BS3_Surface, self).__init__(rational, uPeriodic, uDegree)
		self.poles     = [[]]      # sequence of sequence ofVEC
		self.weights   = [[]]      # sequence of sequence float
		self.vMults    = ()        # tuple of int, ref. umults
		self.vKnots    = ()        # tuple of float
		self.vPeriodic = vPeriodic # boolean
		self.vDegree   = vDegree          # int
class Helix():
	def __init(self):
		self.angleStart = Range('I', 1.0) # start angle
		self.angleEnd   = Range('I', 1.0) # end engle
		self.center     = CENTER
		self.rMajor     = CENTER
		self.rMinor     = CENTER
		self.axisStart  = CENTER
		self.alpha      = MIN_0
		self.axisEnd    = DIR_Z
class Range():
	def __init__(self, type, limit, scale = 1.0):
		self.type  = type
		self.limit = limit
		self.scale = scale
	def __str__(self): return 'I' if (self.type == 'I') else "F %g" %(self.getLimit())
	def __repr__(self): return 'I' if (self.type == 'I') else "%g" %(self.getLimit())
	def getLimit(self): return self.limit if (self.type == 'I') else self.limit * self.scale
class Intervall():
	def __init__(self, upper, lower):
		self.lower = upper
		self.upper = lower
	def __str__(self): return "%s %s" %(self.lower, self.upper)
	def __repr__(self): return "[%r-%r]" %(self.lower, self.upper)
	def getLowerType(self):  return self.lower.type
	def getLowerLimit(self): return self.lower.getLimit()
	def getUpperType(self):  return self.upper.type
	def getUpperLimit(self): return self.upper.getLimit()
class BeginOfAcisHistoryData(): pass
class EndOfAcisHistorySection(): pass
class EndOfAcisData(): pass
class DeltaState(): pass
class AsmHeader(): pass

# abstract super class
class Entity(object):
	def __init__(self):
		self._attrib = None
		self.entity  = None
	def set(self, entity):
		entity.node = self
		self.entity = entity
		addNode(self)

		try:
			references[entity.index] = self
			self._attrib, i = getRefNode(entity, 0, None)
			if (getVersion() > 6):
				i += 1 # skip history!
		except Exception as e:
			logError('>E: ' + traceback.format_exc())
		return i
	def getIndex(self):  return -1   if (self.entity is None)  else self.entity.index
	def getType(self):   return -1   if (self.entity is None)  else self.entity.name
	def getAttrib(self): return None if (self._attrib is None) else self._attrib.node
	def __str__(self):   return "%s" % (self.entity)
	def __repr__(self): return self.__str__()

class EyeRefinement(Entity):
	def __init__(self): super(EyeRefinement, self).__init__()
class VertexTemplate(Entity):
	def __init__(self): super(VertexTemplate, self).__init__()
class Wcs(Entity):
	def __init__(self): super(Wcs, self).__init__()
class Transform(Entity):
	def __init__(self):
		super(Transform, self).__init__()
		self.affine = []
		self.affine.append((1, 0, 0))
		self.affine.append((0, 1, 0))
		self.affine.append((0, 0, 1))
		self.transl     = (0, 0, 0)
		self.scale      = 1.0
		self.rotation   = False
		self.reflection = False
		self.shear      = False
	def setBulk(self, chunks, index):
		p, i          = getPoint(chunks, index)
		a11, a21, a31 = p
		p, i          = getPoint(chunks, i)
		a12, a22, a32 = p
		p, i          = getPoint(chunks, i)
		a13, a23, a33 = p
		p, i          = getLocation(chunks, i)
		a14 = p.x
		a24 = p.y
		a34 = p.z
		a44, i        = getFloat(chunks, i)
		self.rotation, i             = getRotation(chunks, i)
		self.reflection, i           = getReflection(chunks, i)
		self.shear, i                = getShear(chunks, i)
		self.matrix = MAT(a11, a12, a13, a14, a21, a22, a23, a24, a31, a32, a33, a34, 0.0, 0.0, 0.0, a44)
		return i
	def set(self, entity):
		i = super(Transform, self).set(entity)
		i = self.setBulk(entity.chunks, i)
		return i
	def getPlacement(self):
		return PLC(self.matrix)
class Topology(Entity):
	'''Abstract super class for all topology entities.'''
	def __init__(self): super(Topology, self).__init__()
	def set(self, entity):
		i = super(Topology, self).set(entity)
		if (getVersion() > 10.0):
			i += 1 # skip ???
		if (getVersion() > 6.0):
			i += 1 # skip ???
		return i
class Body(Topology):
	def __init__(self):
		super(Body, self).__init__()
		self._lump      = None # Pointer to LUMP object
		self._wire      = None # Pointer to Wire object
		self._transform = None # Pointer to Transform object
	def set(self, entity):
		i = super(Body, self).set(entity)
		self._lump, i      = getRefNode(entity, i, 'lump')
		self._wire, i      = getRefNode(entity, i, 'wire')
		self._transform, i = getRefNode(entity, i, 'transform')
		self.unknown1, i   = getUnknownFT(entity.chunks, i)
		return i
	def getLumps(self):
		lumps = []
		l = self.getLump()
		while (l is not None):
			lumps.append(l)
			l = l.getNext()
		return lumps
	def getWires(self):
		wires = []
		w = self.getWire()
		while (w is not None):
			wires.append(w)
			w = w.getNext()
		return wires
	def getLump(self):      return None if (self._lump is None)      else self._lump.node
	def getWire(self):      return None if (self._wire is None)      else self._wire.node
	def getTransform(self): return None if (self._transform is None) else self._transform.node
class Lump(Topology):
	def __init__(self):
		super(Lump, self).__init__()
		self._next  = None # The next LUMP
		self._shell = None # The first of shells of the LUMP
		self._owner = None # The lump's body
	def set(self, entity):
		i = super(Lump, self).set(entity)
		self._next, i    = getRefNode(entity, i, 'lump')
		self._shell, i   = getRefNode(entity, i, 'shell')
		self._owner, i   = getRefNode(entity, i, 'body')
		self.unknown1, i = getUnknownFT(entity.chunks, i)
		return i
	def getShells(self):
		shells = []
		s = self.getShell()
		while (s is not None):
			shells.append(s)
			s = s.getNext()
		return shells
	def getNext(self):  return None if (self._next is None)  else self._next.node
	def getShell(self): return None if (self._shell is None) else self._shell.node
	def getOwner(self): return None if (self._owner is None) else self._owner.node
class Shell(Topology):
	def __init__(self):
		super(Shell, self).__init__()
		self._next  = None # The next shell
		self._shell = None # The subshell of the shell
		self._face  = None # The first of faces of the shell
		self._wire  = None # The shell's wire
		self._lump  = None # The shell's lump
	def set(self, entity):
		i = super(Shell, self).set(entity)
		self._next, i  = getRefNode(entity, i, 'shell')
		self._shell, i = getRefNode(entity, i, None)
		self._face, i  = getRefNode(entity, i, 'face')
		if (getVersion() > 1.07):
			self._wire, i  = getRefNode(entity, i, 'wire')
		self._lump, i  = getRefNode(entity, i, 'lump')
		return i
	def getFaces(self):
		faces = []
		f = self.getFace()
		while (f is not None):
			faces.append(f)
			f = f.getNext()
		return faces
	def getWires(self):
		wires = []
		w = self.getWire()
		while (w is not None):
			wires.append(w)
			w = w.getNext()
		return wires
	def getSubShells(self):
		shells = []
		s = self.shell
		while (s is not None):
			shells.append(s)
			s = s.next
		return shells
	def getNext(self):  return None if (self._next is None)  else self._next.node
	def getShell(self): return None if (self._shell is None) else self._shell.node
	def getFace(self):  return None if (self._face is None)  else self._face.node
	def getWire(self):  return None if (self._wire is None)  else self._wire.node
	def getLump(self):  return None if (self._lump is None)  else self._lump.node
class SubShell(Topology):
	def __init__(self):
		super(SubShell, self).__init__()
		self._owner = None # The subshell's owner
		self._next  = None # The next subshell
		self._child = None # The child subshell
		self._face  = None # The first face of the subshell
		self._wire  = None # The subshell's wire
	def set(self, entity):
		i = super(SubShell, self).set(entity)
		self._owner = getRefNode(entity, i, 'shell')
		self._next  = getRefNode(entity, i, None)
		self._child = getRefNode(entity, i, None)
		self._face  = getRefNode(entity, i, 'face')
		self._wire  = getRefNode(entity, i, 'wire')
		return i
	def getOwner(self): return None if (self._owner is None) else self._owner.node
	def getNext(self):  return None if (self._next is None)  else self._next.node
	def getChild(self): return None if (self._child is None) else self._child.node
	def getFace(self):  return None if (self._face is None)  else self._face.node
	def getWire(self):  return None if (self._wire is None)  else self._wire.node
class Face(Topology):
	def __init__(self):
		super(Face, self).__init__()
		self._next       = None      # The next face
		self._loop       = None      # The first loop in the list
		self._parent     = None      # Face's owning shell
		self.unknown     = None      # ???
		self._surface    = None      # Face's underlying surface
		self.sense       = 'forward' # Flag defining face is reversed
		self.sides       = 'single'  # Flag defining face is single or double sided
		self.side        = None      # Flag defining face is single or double sided
		self.containment = False     # Flag defining face is containment of double-sided faces
	def set(self, entity):
		i = super(Face, self).set(entity)
		self._next, i                   = getRefNode(entity, i, 'face')
		self._loop, i                   = getRefNode(entity, i, 'loop')
		self._parent, i                 = getRefNode(entity, i, None)
		self.unknown, i                 = getRefNode(entity, i, None)
		self._surface, i                = getRefNode(entity, i, 'surface')
		self.sense, i                   = getSense(entity.chunks, i)
		self.sides, self.containment, i = getSides(entity.chunks, i)
		if (getVersion() > 9.0):
			self.unknown2, i = getUnknownFT(entity.chunks, i)
		return i
	def getLoops(self):
		loops = []
		l = self.getLoop()
		while (l is not None):
			loops.append(l)
			l = l.getNext()
		return loops
	def getNext(self):    return None if (self._next is None)    else self._next.node
	def getLoop(self):    return None if (self._loop is None)    else self._loop.node
	def getParent(self):  return None if (self._parent is None)  else self._parent.node
	def getSurface(self): return None if (self._surface is None) else self._surface.node
	def buildCoEdges(self, doc):
		edges = []
		loop = self.getLoop()
		while (loop is not None):
			for coedge in loop.getCoEdges():
				edge = coedge.build(doc)
				if (edge is not None):
					edges += edge.Edges
			loop = loop.getNext()
		return edges
	def showEdges(self, wires):
		for wire in wires:
			Part.show(wire)
		return None
	def buildWires(self, doc):
		wires    = []
		edges    = self.buildCoEdges(doc)
		for cluster in Part.getSortedClusters(edges):
			for edge in cluster:
				for vertex in edge.Vertexes:
					vertex.Tolerance = 0.025
				edge.Tolerance = 0.025
			try:
				wires.append(Part.Wire(cluster))
			except:
				wires += [Part.Wire(edge) for edge in cluster]

		return wires
	def build(self, doc):
		wires = self.buildWires(doc)
		s     = self.getSurface()
		face = None
		surface = s.build() if (s is not None) else None
		if (surface is not None):
			if (len(wires) > 0):
				# got from Part.BOPTools.SplitAPI.slice()
				compound, map = surface.generalFuse(wires, 0.05)
				# eliminate faces with vertexes outside wires
				return eliminateOuterFaces(map[0], wires)
			# edges can be empty because not all edges can be created right now :(
			return [surface]
		if (hasattr(s, 'type')):
			if (s.type != 'ref'):
				logWarning("    ... Don't know how to build surface '%s::%s' - only edges displayed!" %(s.__class__.__name__, s.type))
		else:
			logWarning("    ... Don't know how to build surface '%s' - only edges displayed!" %(s.__class__.__name__))
		self.showEdges(wires)
		return []
class Loop(Topology):
	def __init__(self):
		super(Loop, self).__init__()
		self._next   = None # The next loop
		self._coedge = None # The first coedge in the loop
		self._face   = None # The first coedge in the face
	def set(self, entity):
		i = super(Loop, self).set(entity)
		self._next, i   = getRefNode(entity, i, 'loop')
		self._coedge, i = getRefNode(entity, i, 'coedge')
		self._face, i   = getRefNode(entity, i, 'face')
		self.unknown, i = getUnknownFT(entity.chunks, i)
		if (getVersion() > 9.0):
			i += 1
		return i
	def getNext(self):   return None if (self._next is None)   else self._next.node
	def getCoEdge(self): return None if (self._coedge is None) else self._coedge.node
	def getFace(self):   return None if (self._face is None)   else self._face.node
	def getCoEdges(self):
		coedges = []
		ce = self.getCoEdge()
		index =  -1 if (ce is None) else ce.getIndex()
		while (ce is not None):
			coedges.append(ce)
			ce = ce.getNext()
			if ((ce is not None) and (ce.getIndex() == index)):
				ce = None
		return coedges
class Edge(Topology):
	def __init__(self):
		super(Edge, self).__init__()
		self._start  = None # The start vertex
		self._end    = None # The end vertex
		self._parent = None # The edge's coedge
		self._curve  = None # Lying on one the Adjacent faces
		self.text   = ''
	def set(self, entity):
		i = super(Edge, self).set(entity)
		self._start, i  = getRefNode(entity, i, 'vertex')
		if (getVersion() > 4.0):
			i += 1 # skip double
		self._end, i    = getRefNode(entity, i, 'vertex')
		if (getVersion() > 4.0):
			i += 1 # skip double
		self._parent, i = getRefNode(entity, i, 'coedge')
		self._curve, i  = getRefNode(entity, i, 'curve')
		self.sense, i  = getSense(entity.chunks, i)
		if (getVersion() > 5.0):
			self.text, i = getText(entity.chunks, i)
		self.unknown, i = getUnknownFT(entity.chunks, i)
		return i
	def getStart(self):
		try:
			return (0, 0, 0) if (self._start is None) else self._start.node.getPosition()
		except Exception as e:
			raise Exception("%s,%s - %s" %(self, self._start, e))
	def getEnd(self):    return (0, 0, 0) if (self._end is None)   else self._end.node.getPosition()
	def getParent(self): return None if (self._parent is None)     else self._parent.node
	def getCurve(self):  return None if (self._curve is None)      else self._curve.node
class EdgeTolerance(Edge):
	def __init__(self):
		super(EdgeTolerance, self).__init__()
		self.tolerance = 0.0
	def set(self, entity):
		i = super(EdgeTolerance, self).set(entity)
		return i
class CoEdge(Topology):
	def __init__(self):
		super(CoEdge, self).__init__()
		self._next     = None      # The next coedge
		self._previous = None      # The previous coedge
		self._partner  = None      # The partner coedge
		self._edge     = None      # The coedge's edge
		self.sense     = 'forward' # The relative sense
		self._owner    = None      # The coedge's owner
		self._curve    = None
		self.shape     = None      # Will be created in build function
	def set(self, entity):
		i = i = super(CoEdge, self).set(entity)
		self._next, i     = getRefNode(entity, i, 'coedge')
		self._previous, i = getRefNode(entity, i, 'coedge')
		self._partner, i  = getRefNode(entity, i, 'coedge')
		self._edge, i     = getRefNode(entity, i, 'edge')
		self.sense, i     = getSense(entity.chunks, i)
		self._owner, i    = getRefNode(entity, i, None) # can be either Loop or Wire
		if (entity.chunks[i].tag != 0x0C):
			i += 1
		self._curve, i    = getRefNode(entity, i, 'curve')
		return i
	def getNext(self):     return None if (self._next is None)     else self._next.node
	def getPrevious(self): return None if (self._previous is None) else self._previous.node
	def getPartner(self):  return None if (self._partner is None)  else self._partner.node
	def getEdge(self):     return None if (self._edge is None)     else self._edge.node
	def getOwner(self):    return None if (self._owner is None)    else self._owner.node
	def getCurve(self):    return None if (self._curve is None)    else self._curve.node
	def build(self, doc):
		if (self.shape is None):
			e = self.getEdge()
			c = e.getCurve()
			if (c is not None):
				if (c.shape is None):
					p1 = e.getStart() if (e.sense == 'forward') else e.getEnd()
					p2 = e.getEnd() if (e.sense == 'forward') else e.getStart()
					c.build(p1, p2)
				if (c.shape is not None):
					self.shape = c.shape.copy()
		return self.shape
class CoEdgeTolerance(CoEdge):
	def __init__(self):
		super(CoEdgeTolerance, self).__init__()
		self.tStart = 0.0
		self.tEnd = 0.0
	def set(self, entity):
		i = super(CoEdgeTolerance, self).set(entity)
		self.tStart, i  = getFloat(entity.chunks, i)
		self.tEnd, i    = getFloat(entity.chunks, i)
		return i
class Vertex(Topology):
	def __init__(self):
		super(Vertex, self).__init__()
		self._parent = None # One of the vertex' owners
		self._point = None  # The vertex' location
		self.count = -1    # Number of edges using this vertex
	def set(self, entity):
		i = super(Vertex, self).set(entity)
		self._parent, i = getRefNode(entity, i, 'edge')
		# inventor-version: 2010 -> workaround
		if (entity.chunks[i].tag != 0xC):
			i += 1
		self._point, i  = getRefNode(entity, i, 'point')
		return i
	def getParent(self):   return None if (self._parent is None) else self._parent.node
	def getPoint(self):    return None if (self._point is None)  else self._point.node
	def getPosition(self):
		p = self.getPoint()
		return CENTER if (p is None) else p.position
class VertexTolerance(Vertex):
	def __init__(self):
		super(VertexTolerance, self).__init__()
		self.tolerance = 0.0
	def set(self, entity):
		i = super(VertexTolerance, self).set(entity)
		self.tolerance, i = getFloat(entity.chunks, i)
		return i
class Wire(Topology):
	def __init__(self):
		super(Wire, self).__init__()
		self._next = None
		self._coedge = None
		self._shell = None
		self.side = False
	def set(self, entity):
		i = super(Wire, self).set(entity)
		self._next, i   = getRefNode(entity, i, 'wire')
		self._coedge, i = getRefNode(entity, i, 'coedge')
		self._owner, i  = getRefNode(entity, i, None)
		self.unknown, i = getRefNode(entity, i, None)
		self.side, i    = getSide(entity.chunks, i)
		self.ft, i      = getUnknownFT(entity.chunks, i)
		return i
	def getNext(self):   return None if (self._next is None)   else self._next.node
	def getCoEdge(self): return None if (self._coedge is None) else self._coedge.node
	def getShell(self):  return None if (self._shell is None)  else self._shell.node
	def getOwner(self):  return None if (self._owner is None)  else self._owner.node
	def getCoEdges(self):
		coedges = []
		ce = self.getCoEdge()
		index = -1 if (ce is None) else ce.getIndex()
		idxLst = []
		while (ce is not None):
			coedges.append(ce)
			idxLst.append(ce.getIndex())
			ce = ce.getNext()
			if (ce.getIndex() in idxLst):
				ce = None
		return coedges
	def getShells(self):
		shells = []
		shell = self.getShell()
		index = -1 if (shell is None) else shell.getIndex()
		while (shell is not None):
			shells.append(shell)
			shell = shell.getNext()
		return shells

# abstract super class for all geometries
class Geometry(Entity):
	def __init__(self): super(Geometry, self).__init__()
	def set(self, entity):
		i = super(Geometry, self).set(entity)
		if (getVersion() > 10.0):
			i += 1 # skip ???
		if (getVersion() > 6.0):
			i += 1 # skip ???
		return i
class Curve(Geometry):
	def __init__(self):
		super(Curve, self).__init__()
		self.shape = None
	def setSubtype(self, chunks, index):
		return index
	def set(self, entity):
		i = super(Curve, self).set(entity)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self, start, end): # by default: return a line-segment!
		logWarning("    ... '%s' not yet supported - forced to straight-curve!" %(self.__class__.__name__))
		if (self.shape is None):
			# force everything else to straight line!
			self.shape = createLine(start, end)
		return self.shape
class CurveComp(Curve):    # compound courve "compcurv-curve"
	def setSubtype(self, chunks, index):
		return index
class CurveDegenerate(Curve):    # degenerate courve "degenerate_curve"
	def setSubtype(self, chunks, index):
		v1, i = getLocation(chunks, index)
		r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		return i
class CurveEllipse(Curve): # ellyptical curve "ellipse-curve"
	def __init__(self):
		super(CurveEllipse, self).__init__()
		self.center = CENTER
		self.normal = DIR_Z
		self.major  = DIR_X
		self.ratio  = MIN_0
		self.range  = Intervall(Range('I', MIN_0), Range('I', MAX_2PI))
	def __str__(self): return "Curve-Ellipse: center=%s, dir=%s, major=%s, ratio=%g, range=%s" %(self.center, self.normal, self.major, self.ratio, self.range)
	def __repr__(self): return self.__str__()
	def setSubtype(self, chunks, index):
		self.center, i = getLocation(chunks, index)
		self.normal, i = getVector(chunks, i)
		self.major, i  = getLocation(chunks, i)
		self.ratio, i  = getFloat(chunks, i)
		self.range, i  = getInterval(chunks, i, MIN_0, MAX_2PI, 1.0)
		return i
	def build(self, start, end):
		if (self.shape is None):
			ellipse = createEllipse(self.center, self.normal, self.major, self.ratio)
			if (start != end):
				a = ellipse.parameter(start)
				b = ellipse.parameter(end)
				self.range = Intervall(Range('F', a), Range('F', b))
				ellipse = Part.ArcOfCircle(ellipse, a, b) if (self.ratio == 1) else Part.ArcOfEllipse(ellipse, a, b)
			self.shape = ellipse.toShape()
		return self.shape
class CurveInt(Curve):     # interpolated ('Bezier') curve "intcurve-curve"
	def __init__(self):
		super(CurveInt, self).__init__()
		self.sense  = 'forward' # The IntCurve's reversal flag
		self.range  = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
		self.type   = ''
		self.curve  = None
	def __str__(self): return "-%d Curve-Int: type=%s" %(self.getIndex(), self.type)
	def __repr__(self): return self.__str__()
	def setCurve(self, chunks, index):
		self.singularity, i = getSingularity(chunks, index)
		if (self.singularity == 'full'):
			nubs, i = readBS3Curve(chunks, i)
			self.tolerance, i = getLength(chunks, i)
			self.shape = createBSplinesCurve(nubs, self.sense)
		elif (self.singularity == 'none'):
			self.range, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			val, i= getValue(chunks, i)
			if (type(val) == float):
				self.tolerance = val
		elif (self.singularity == 'summary'):
			if (getVersion() > 17.0):
				i += 1
			arr, i  = getFloatArray(chunks, i)
			fac, i  = getFloat(chunks, i)
			clsr, i = getClosure(chunks, i)
		elif (self.singularity == 'v'):
			nubs = BS3_Curve(False, False, 3)
			nubs.uKnots, i = getFloatArray(chunks, i) # nubs 3 0 n
			nubs.uMults = [3] * len(nubs.uKnots)
			self.tolerance, i = getLength(chunks, i)
			f2, i = getFloat(chunks, i)
		else:
			raise Exception("Unknwon Surface-singularity '%s'" %(self.singularity))
		return i
	def setSurfaceCurve(self, chunks, index):
		i = self.setCurve(chunks, index)
		surface1, i = readSurface(chunks, i)
		surface2, i = readSurface(chunks, i)
		curve1, i   = readBS2Curve(chunks, i)
		curve2, i   = readBS2Curve(chunks, i)
		if (getVersion() > 15.0):
			i += 2
		range2, i   = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		if (getVersion() >= 2.0):
			a1, i       = getFloatArray(chunks, i)
			a2, i       = getFloatArray(chunks, i)
			a3, i       = getFloatArray(chunks, i)
		return i
	def setBlend(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		txt, i      = getText(chunks, i)
		return i
	def setBlendSprng(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		txt, i      = getText(chunks, i)
		return i
	def setComp(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		a4, i       = getFloatArray(chunks, i)
		a5, i       = getFloatArray(chunks, i)
		if (inventor):
			i += 1 # 0x0A
		self.curves = []
		for k in range(0, len(a5)):
			c, i = readCurve(chunks, i)
			self.curves.append(c)
		return i
	def setDefm(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (inventor):
			x3, i = getFloat(chunks, i)
		bend, i = readCurve(chunks, i)
		return i
	def setExact(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (getVersion() >= 2.0):
			if (inventor):
				x3, i = getFloat(chunks, i)
			if (getVersion() > 15.0):
				i += 2
			unknown, i = getUnknownFT(chunks, i)
			range2, i  = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def setHelix(self, chunks, index, inventor):
		helix = Helix()
		helix.angleStart, i = getRange(chunks, index, MIN_0, 1.0)
		helix.angleEnd, i   = getRange(chunks, i, MAX_2PI, 1.0)
		helix.axisStart, i  = getLocation(chunks, i)        # axis start
		helix.rMajor, i     = getLocation(chunks, i)        # profile's ellipse major radius
		helix.rMinor, i     = getLocation(chunks, i)        # profile's ellipse minor radius
		helix.center, i     = getLocation(chunks, i)        # profile's ellipse center
		helix.alpha, i      = getFloat(chunks, i)           # pitch ???
		helix.axisEnd, i    = getLocation(chunks, i)        # axis end
		self.shape = createHelix(helix)
		surface1, i = readSurface(chunks, i)  # None
		surface2, i = readSurface(chunks, i)  # None
		curve1, i   = readBS2Curve(chunks, i) # None
		curve2, i   = readBS2Curve(chunks, i) # None
		return i
	def setInt(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		x, i = getFloat(chunks, i)
		return i
	def setLaw(self, chunks, index, inventor):
		i = index
		i = self.setSurfaceCurve(chunks, index)
		laws = []
		if (inventor):
			n, i   = getInteger(chunks, i) # 0
		l, i  = readLaw(chunks, i)
		laws.append(l)
		subLaws = []
		laws.append(subLaws)
		n, i   = getInteger(chunks, i) # 0..n
		for cnt in range(0, n):
			l, i  = readLaw(chunks, i)
			subLaws .append(l)
		n, i   = getInteger(chunks, i) #4
		if (n == 0):
			return i
		subLaws = []
		laws.append(subLaws)
		while (True):
			l, i  = readLaw(chunks, i) # null_law
			subLaws.append(l)
			if (l[0] != 'null_law'):
				break
		subLaws = []
		laws.append(subLaws)
		while (i < len(chunks)):
			n, i   = getInteger(chunks, i) #0
			if (n == 0):
				l, i  = readLaw(chunks, i)
				subLaws.append(l)
			elif (n == 1):
				l, i  = readLaw(chunks, i)
				subLaws.append(l)
				break
			elif (n == 2):
				l, i  = readLaw(chunks, i)
				subLaws.append(l)
				l, i  = readLaw(chunks, i)
				subLaws.append(l)
				while (True):
					l, i  = readLaw(chunks, i)
					subLaws.append(l)
					if (l[0] != 'null_law'):
						break
		return i
	def setOff(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (inventor):
				i += 1
		offsets, i = getFloats(chunks, i, 2)
		return i
	def setOffset(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (inventor):
			i += 1
		curve, i = readCurve(chunks, i)
		return i
	def setOffsetSurface(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (inventor):
			i += 1
		rngU, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		rngV, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		curve, i = readCurve(chunks, i)
		rng, i  = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		# x, y, z ???
		return i
	def setParameter(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (getVersion() > 15.0):
			i += 1
		if (not inventor):
			if (getVersion() > 17.0):
				i += 2 # 'none', F ???
			txt, i = getText(chunks, i)
		return i
	def setParameterSilhouette(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		i1, i = getInteger(chunks, i)
		v1, i = getVector(chunks, i) # direction
		f1, i = getFloat(chunks, i)
		return i
	def setProject(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (inventor):
			i += 1
		curve, i = readCurve(chunks, i)
		if (inventor):
			i += 1
		return i
	def setRef(self, chunks, index):
		self.curve, i = getInteger(chunks, index)
		return i
	def setSpring(self, chunks, index, inventor):
		i = self.setCurve(chunks, index)
		surface1, i = readSurface(chunks, i)
		if (surface1 is None):
			rangeU, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
			rangeV, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		surface2, i = readSurface(chunks, i)
		curve1, i   = readBS2Curve(chunks, i)
		if (getVersion() == 18.0):
			i += 2
		curve2, i   = readBS2Curve(chunks, i)
		if (getVersion() > 15.0):
			i += 2
		range2, i   = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		a1, i       = getFloatArray(chunks, i)
		a2, i       = getFloatArray(chunks, i)
		a3, i       = getFloatArray(chunks, i)
		# n, m ???
		return i
	def setSurface(self, chunks, index):
		i = self.setSurfaceCurve(chunks, index)
		return i
	def setBulk(self, chunks, index):
		self.type, i = getValue(chunks, index)

		if (self.type == 'ref'):               return self.setRef(chunks, i)

		addSubtypeNode('intcurve', self)

		try:
			prm = CURVE_TYPES[self.type]
			fkt = getattr(self, prm[0])
			return fkt(chunks, i + prm[1], prm[2])
		except KeyError as ke:
			raise Exception("Curve-Int: unknown subtype '%s'!" %(self.type))
	def setSubtype(self, chunks, index):
		self.sense, i  = getSense(chunks, index)
		block, i      = getBlock(chunks, i)
		self.setBulk(block, 0)
		self.range, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def build(self, start, end):
		if (self.shape is None):
			if (hasattr(self, 'curves')):
				curve = self.curves[0].build(None, None)
				others = []
				for c in self.curves[1:]:
					shp = c.build(None, None)
					if (shp): others.append(shp)
				self.shape = curve.multifuse(others)
			else:
				if (not self.curve is None):
					if (type(self.curve) == int):
						self.curve = getSubtypeNode('intcurve', self.curve)
				if (not self.curve is None):
					self.shape = self.curve.build(start, end)
		return self.shape
class CurveIntInt(CurveInt):  # interpolated int-curve "intcurve-intcurve-curve"
	def __init__(self):
		super(CurveIntInt, self).__init__()
		self.sense = 'forward' # The IntCurve's reversal flag
		self.range = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
		self.type  = ''
		self.curve = None
	def setLaw(self, chunks, index, inventor):
		i = self.setCurve(chunks, index)
		return i
	def setBulk(self, chunks, index):
		self.type, i = getValue(chunks, index)
		if (self.type == 'lawintcur'):        return self.setLaw(chunks, i, False)
		if (self.type == 'law_int_cur'):      return self.setLaw(chunks, i + 1, True)
		logError("    Curve-Int-Int: unknown subtype %s !" %(self.type))
		return self.setCurve(chunks, i)
	def setSubtype(self, chunks, index):
		self.sense, i  = getSense(chunks, index)
		block, i      = getBlock(chunks, i)
		self.setBulk(block, 0)
		self.range, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
class CurveP(Curve):       # projected curve "pcurve" for each point in CurveP: point3D = surface.value(u, v)
	'''An approximation to a curve lying on a surface, defined in terms of the surface’s u-v parameters.'''
	def __init__(self):
		super(CurveP, self).__init__()
		self.type   = -1    # The PCurve's type
		self.sense  = 'forward'
		self._curve = None  # The PCurve's curve
	def setExpPar(self, chunks, index):
		i = index if (getVersion() <= 22.0) else index + 1
		self.pcurve, i = readBS2Curve(chunks, i)
		factor, i = getFloat(chunks, i)
		if (getVersion() > 15.0):
			i += 1
		self.surface, i = readSurface(chunks, i)
		self.type = 'exppc'
		return i
	def setRef(self, chunks, index):
		self.ref, i = getInteger(chunks, index)
		return i
	def setBulk(self, chunks, index):
		self.type, i = getValue(chunks, index)
		if (self.type == 'ref'):         return self.setRef(chunks, i)

		addSubtypeNode('pcurve', self)

		if (self.type == 'exp_par_cur'): return self.setExpPar(chunks, i)
		if (self.type == 'exppc'):       return self.setExpPar(chunks, i)
		raise Exception("PCurve: unknown subtype '%s'!" %(self.type))
	def setSubtype(self, chunks, index):
		self.sense, i = getSense(chunks, index)
		block, i = getBlock(chunks, i)
		self.setBulk(block, 0)
		self.u, i = getFloat(chunks, i)
		self.v, i = getFloat(chunks, i)
		return i
	def set(self, entity):
		i = super(Curve, self).set(entity)
		self.type, i = getInteger(entity.chunks, i)
		if (self.type == 0):
			i = self.setSubtype(entity.chunks, i)
		else:
			self._curve, i = getRefNode(entity, i, 'curve')
			self.u, i = getFloat(entity.chunks, i)
			self.v, i = getFloat(entity.chunks, i)
		return i
	def build(self, start, end):
		if (self.shape is None):
			if (self.type == 'ref'):
				curve = getSubtypeNode('pcurve', self.ref)
				if (curve is not None):
					self.shape = curve.build(start, end)
			elif (self.type == 'exppc'):
				shelf.shape = createBSplinesPCurve(self.pcurve, self.surface, self.sense)
			elif (self._curve is not None):
				self.shape = self._curve.build(start, end)
		return self.shape
class CurveStraight(Curve):# straight curve "straight-curve"
	def __init__(self):
		super(CurveStraight, self).__init__()
		self.root  = CENTER
		self.dir   = CENTER
		self.range = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
	def __str__(self): return "Curve-Straight: root=%s, dir=%s, range=%s" %(self.root, self.dir, self.range)
	def __repr__(self): return self.__str__()
	def setSubtype(self, chunks, index):
		self.root, i  = getLocation(chunks, index)
		self.dir, i   = getVector(chunks, i)
		self.range, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def build(self, start, end):
		if (self.shape is None):
			self.shape = createLine(start, end)
		return self.shape
class Surface(Geometry):
	def __init__(self):
		super(Surface, self).__init__()
		self.shape = None
	def set(self, entity):
		i = super(Surface, self).set(entity)
		return i
	def build(self): return None
class SurfaceCone(Surface):
	def __init__(self):
		super(SurfaceCone, self).__init__()
		self.center = CENTER
		self.axis   = DIR_Z
		self.major  = DIR_X
		self.ratio  = 1.0
		self.range  = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
		self.sine   = 0.0
		self.cosine = 0.0
		self.scale  = 1.0
		self.sense  = 'forward'
		self.urange = Intervall(Range('I', MIN_0), Range('I', MAX_2PI))
		self.vrange = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
	def __str__(self): return "Surface-Cone: center=%s, axis=%s, radius=%g, ratio=%g, semiAngle=%g" %(self.center, self.axis, self.major.Length, self.ratio, math.degrees(math.asin(self.sine)))
	def __repr__(self): return self.__str__()
	def setSubtype(self, chunks, index):
		self.center, i = getLocation(chunks, index)
		self.axis, i   = getVector(chunks, i)
		self.major, i  = getLocation(chunks, i)
		self.ratio, i  = getFloat(chunks, i)
		self.range, i  = getInterval(chunks, i, MIN_INF, MIN_INF, getScale())
		self.sine, i   = getFloat(chunks, i)
		self.cosine, i = getFloat(chunks, i)
		if (getVersion() >= ENTIY_VERSIONS.get('CONE_SCALING_VERSION')):
			self.scale, i = getLength(chunks, i)
		else:
			self.scale = getScale()
		self.sense, i  = getSense(chunks, i)
		self.urange, i = getInterval(chunks, i, MIN_0, MAX_2PI, 1.0)
		self.vrange, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def set(self, entity):
		i = super(SurfaceCone, self).set(entity)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self):
		if (self.shape is None):
			if (self.sine == 0): # 90°
				# Workaround: create ellipse and extrude in both directions
				ellipse = createEllipse(self.center, self.axis, self.major, self.ratio)
				# make a gigantic extrusion as it will be beautyfied later
				cyl = ellipse.toShape().extrude((2*MAX_LEN) * self.axis)
				cyl.translate((-MAX_LEN) * self.axis)
				self.shape = cyl.Faces[0]
			elif (self.ratio == 1):
				# TODO: elliptical cones not yet supported!
				cone = Part.Cone()
				rotateShape(cone, self.axis)
				cone.Center = self.center
				semiAngle = math.asin(self.sine)
				try:
					cone.SemiAngle = semiAngle
				except Exception as e:
					logError("    Can't set cone.SemiAngle=%s - %s" %(math.degrees(semiAngle), e))
#				cone.Radius = self.major.Length
				# = self.ratio
				# = self.major
				self.shape = cone.toShape()
		return self.shape
class SurfaceMesh(Surface):
	def __init__(self):
		super(SurfaceMesh, self).__init__()
	def setSubtype(self, chunks, index):
		return index
	def set(self, entity):
		i = super(SurfaceMesh, self).set(entity)
		i = self.setSubtype(entity.chunks, i)
		return i
class SurfacePlane(Surface):
	def __init__(self):
		super(SurfacePlane, self).__init__()
		self.root     = CENTER
		self.normal   = DIR_Z
		self.uvorigin = CENTER
		self.sensev   = 'forward_v'
		self.urange   = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
		self.vrange   = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
	def __str__(self): return "Surface-Plane: root=%s, normal=%s, uvorigin=%s" %(self.root, self.normal, self.uvorigin)
	def __repr__(self): return self.__str__()
	def setSubtype(self, chunks, index):
		self.root, i     = getLocation(chunks, index)
		self.normal, i   = getVector(chunks, i)
		self.uvorigin, i = getLocation(chunks, i)
		self.sensev, i   = getSensev(chunks, i)
		self.urange, i   = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		self.vrange, i   = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def set(self, entity):
		i = super(SurfacePlane, self).set(entity)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self):
		if (self.shape is None):
			plane = Part.Plane()
			plane.Axis = self.normal
			plane.Position = self.root
			self.shape = plane.toShape()
		return self.shape
class SurfaceSphere(Surface):
	def __init__(self):
		super(SurfaceSphere, self).__init__()
		self.center   = CENTER
		self.radius   = 0.0
		self.uvorigin = CENTER
		self.pole     = DIR_Z
		self.sensev   = 'forward_v'
		self.urange   = Intervall(Range('I', MIN_0), Range('I', MAX_2PI))
		self.vrange   = Intervall(Range('I', MIN_PI2), Range('I', MAX_PI2))
	def __str__(self): return "Surface-Sphere: center=%s, radius=%g, uvorigin=%s, pole=%s" %(self.center, self.radius, self.uvorigin, self.pole)
	def __repr__(self): return self.__str__()
	def setSubtype(self, chunks, index):
		self.center, i   = getLocation(chunks, index)
		self.radius, i   = getLength(chunks, i)
		self.uvorigin, i = getVector(chunks, i)
		self.pole, i     = getVector(chunks, i)
		self.sensev, i   = getSensev(chunks, i)
		self.urange, i   = getInterval(chunks, i, MIN_0, MAX_2PI, 1.0)
		self.vrange, i   = getInterval(chunks, i, MIN_PI2, MAX_PI2, 1.0)
		return i
	def set(self, entity):
		i = super(SurfaceSphere, self).set(entity)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self):
		if (self.shape is None):
			sphere = Part.Sphere()
			rotateShape(sphere, self.pole)
			sphere.Center = self.center
			sphere.Radius = fabs(self.radius)
			self.shape = sphere.toShape()
		return self.shape
class SurfaceSpline(Surface):
	def __init__(self):
		super(SurfaceSpline, self).__init__()
		self.surface = None
	def setSurfaceShape(self, chunks, index, inventor):
		spline, tol, i = readSplineSurface(chunks, index, True)
		self.shape = createBSplinesSurface(spline)
		if (getVersion() >= 2.0):
			arr, i  = readArrayFloats(chunks, i, inventor)
		return i
	def setBlendSupply(self, chunks, index, inventor):
		name, i = getValue(chunks, index)
		self.surface, i = readSurface(chunks, i)
		return i
	def setClLoft(self, chunks, index, inventor):
		i = self.setSurfaceShape(chunks, index, inventor)
		scl1, i = readScaleClLoft(chunks, i)
		scl2, i = readScaleClLoft(chunks, i)
		scl3, i = readScaleClLoft(chunks, i)
		scl3, i = readScaleClLoft(chunks, i)
		e1, i = getEnum(chunks, i)
		e2, i = getEnum(chunks, i)
		n1, i = getInteger(chunks, i) # 7
		e2, i = getEnum(chunks, i)
		scl3, i = readScaleClLoft(chunks, i)
		e2, i = getEnum(chunks, i)
		scl3, i = readScaleClLoft(chunks, i)
		n1, i = getInteger(chunks, i) # 0
		v1, i = getVector(chunks, i)
		e1, i = getEnum(chunks, i)
		e2, i = getEnum(chunks, i)
		return i
	def setCompound(self, chunks, index, inventor):
		i = self.setSurfaceShape(chunks, index, inventor)
		d, i  = getFloatArray(chunks, i)
		e = []
		for k in range(0, len(d)):
			f, i = readSurface(chunks, i)
			e.append(f)
		return i
	def setCylinder(self, chunks, index, inventor):
		c1, i = readCurve(chunks, index)
		v1, i = getVector(chunks, i)
		v2, i = getVector(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setDefm(self, chunks, index, inventor):
		self.surface, i = readSurface(chunks, index)
		a1, i = getInteger(chunks, i) # 3, 8
		v11, i = getVector(chunks, i)
		v12, i = getVector(chunks, i)
		v13, i = getVector(chunks, i)
		v14, i = getVector(chunks, i)
		t1, i = getInteger(chunks, i) # 0, 1
		if (t1 == 1):
			#0x0A 0x0B 0x0B VEC VEC VEC 1 0x0B 0x0B 0 1 2.02849 0x0B 0x0B 0x0B 0x0B 0x0B 1 0
			e21, i = getEnum(chunks, i)
			e22, i = getEnum(chunks, i)
			e23, i = getEnum(chunks, i)
			v21, i = getVector(chunks, i)
			v22, i = getVector(chunks, i)
			v23, i = getVector(chunks, i)
			f21, i = getFloat(chunks, i)
			e24, i = getEnum(chunks, i)
			e25, i = getEnum(chunks, i)
			v24, i = getPoint(chunks, i)
			e26, i = getEnum(chunks, i)
			e27, i = getEnum(chunks, i)
			e28, i = getEnum(chunks, i)
			e29, i = getEnum(chunks, i)
			e2A, i = getEnum(chunks, i)
			a21, i = getIntegers(chunks, i, 2)
		elif (t1 != 0):
			raise Exception()
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setExact(self, chunks, index, inventor):
		i = self.setSurfaceShape(chunks, index, inventor)
		if (getVersion() > 2.0):
			rU, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			rV, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			if (inventor):
				ft, i = getInteger(chunks, i)
		return i
	def setG2Blend(self, chunks, index, inventor):
		t11, i = getValue(chunks, index)
		while (type(t11) != str):
			t11, i = getValue(chunks, i)
		s11, i = readSurface(chunks, i)
		c11, i = readCurve(chunks, i)
		p11, i = readBS2Curve(chunks, i)
		v11, i = getVector(chunks, i)
		p12, i = readBS2Curve(chunks, i)
		singularity, i = getSingularity(chunks, i)
		if (singularity == 'full'):
			s12, i = readBS3Surface(chunks, i)
			if (s12):
				tol11, i = getLength(chunks, i)
		elif (singularity == 'none'):
			s12, i = getFloats(chunks, i, 9)
			tol11, i = getLength(chunks, i)
			if (not chunks[i].tag in (0x07, 0x0D, 0x0E)):
				i += 1 # newer Inventor versions (>2017
			p13, i = readBS2Curve(chunks, i)
		else:
			raise AssertionError("wrong singularity %s" %(singularity))

		t21, i = getValue(chunks, i)
		s21, i = readSurface(chunks, i)
		c21, i = readCurve(chunks, i)
		p21, i = readBS2Curve(chunks, i)
		v21, i = getVector(chunks, i)
		p22, i = readBS2Curve(chunks, i)
		s22, tol21, i = readSplineSurface(chunks, i, True)

		c1, i = readCurve(chunks, i)
		a1, i = getFloats(chunks, i, 2)
		l1, i = getLong(chunks, i) # non_
		rU, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		rV, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		a1, i = getFloats(chunks, i, 4)# 1, 0.05, 1e-4, 1
		i = self.setSurfaceShape(chunks, i, inventor)
		if (inventor):
			a31, i = getFloatArray(chunks, i)
			a31, i = getFloatArray(chunks, i)
			a31, i = getFloatArray(chunks, i)
		return i
	def setHelixCircle(self, chunks, index, inventor):
		angle, i  = getInterval(chunks, index, MIN_PI, MAX_PI, 1.0)
		dime1, i  = getInterval(chunks, i, -MAX_LEN, MAX_LEN, getScale())
		length, i = getLength(chunks, i)
		dime2, i  = getInterval(chunks, i, -MAX_LEN, MAX_LEN, getScale())
		x1, i     = getLocation(chunks, i)
		x2, i     = getLocation(chunks, i)
		x3, i     = getLocation(chunks, i)
		x4, i     = getLocation(chunks, i)
		fac1, i   = getFloat(chunks, i)
		x5, i     = getVector(chunks, i)
		s1, i     = readSurface(chunks, i)
		s2, i     = readSurface(chunks, i)
		c1, i     = readBS2Curve(chunks, i)
		c2, i     = readBS2Curve(chunks, i)
		fac2, i   = getFloat(chunks, i)
		return i
	def setHelixLine(self, chunks, index, inventor):
		angle, i  = getInterval(chunks, index, MIN_PI, MAX_PI, 1.0)
		dime1, i  = getInterval(chunks, i, -MAX_LEN, MAX_LEN, getScale())
		dime2, i  = getInterval(chunks, i, -MAX_LEN, MAX_LEN, getScale())
		x1, i     = getLocation(chunks, i)
		x2, i     = getLocation(chunks, i)
		x3, i     = getLocation(chunks, i)
		x4, i     = getLocation(chunks, i)
		fac1, i   = getFloat(chunks, i)
		x5, i     = getVector(chunks, i)
		s1, i     = readSurface(chunks, i)
		s2, i     = readSurface(chunks, i)
		c1, i     = readBS2Curve(chunks, i)
		c2, i     = readBS2Curve(chunks, i)
		x6, i     = getVector(chunks, i)
		return i
	def setLoft(self, chunks, index, inventor):
		ls1, i = readLofSection(chunks, index)
		ls2, i = readLofSection(chunks, i)

		r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		r2, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		clsr1, i = getClosure(chunks, i)
		clsr2, i = getClosure(chunks, i)
		sng1, i = getSingularity(chunks, i)
		sng2, i = getSingularity(chunks, i)
		# 1|2, 0?, 0, nubs
		b, i = getInteger(chunks, i)
		while (not chunks[i+1].tag in (0x07, 0x0D, 0x0E)):
			i += 1 ## FIXME
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setNet(self, chunks, index, inventor):
		ls1, i = readLofSection(chunks, index)
		ls2, i = readLofSection(chunks, i)
		a1, i = getFloats(chunks, i, 12)
		a2, i = getInteger(chunks, i)
		v1, i = getVector(chunks, i)
		v2, i = getVector(chunks, i)
		v3, i = getVector(chunks, i)
		v4, i = getVector(chunks, i)
		frml1, i = readFormula(chunks, i)
		frml2, i = readFormula(chunks, i)
		frml3, i = readFormula(chunks, i)
		frml4, i = readFormula(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setOffset(self, chunks, index, inventor):
		self.surface, i = readSurface(chunks, index)
		f1, i = getFloat(chunks, i)
		senseU, i = getSense(chunks, i)
		senseV, i = getSense(chunks, i)
		if (inventor):
			e3, i = getEnum(chunks, i) # 0x0B
			if ((chunks[i].tag == 0x0A) or (chunks[i].tag == 0x0B)): # 0x0B
				i += 1
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setOrtho(self, chunks, index, inventor):
		self.surface, i = readSurface(chunks, index)
		curve, i = readCurve(chunks, i)
		p1, i = readBS2Curve(chunks, i)
		i += 1 # float=1.0
		singularity, i = getSingularity(chunks, i)
		if (singularity == 'full'):
			nubs, i = readBS3Surface(chunks, i)
			self.shape = createBSplinesSurface(nubs)
			v1, i = getPoint(chunks, i)
			a1, i = getFloatArray(chunks, i)
			v2, i = getPoint(chunks, i)
		else:
			a1, i = getFloatArray(chunks, i)
			a2, i = getFloatArray(chunks, i)
			a3, i = getFloats(chunks, i, 7)
			a4, i = getFloatArray(chunks, i)
			a5, i = getFloats(chunks, i, 2)
			# int
		if (inventor):
			i += 2
		return i
	def setRbBlend(self, chunks, index, inventor):
		i = index
		rb1, i = readRbBlend(chunks, i, inventor)
		rb2, i = readRbBlend(chunks, i, inventor)

		# read remaining data
		c3, i = readCurve(chunks, i)
		a1, i = getFloats(chunks, i, 2)
		i += 1 # no_radius,  -1
		r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		a2, i = getFloats(chunks, i, 3)
		i += 1 # 1
		i = self.setSurfaceShape(chunks, i, inventor)
		if (inventor):
			a7, i = getFloatArray(chunks, i)
			a8, i = getFloatArray(chunks, i)
			a9, i = getFloatArray(chunks, i)
		return i
	def setRotation(self, chunks, index, inventor):
		profile, i = readCurve(chunks, index)
		loc, i     = getLocation(chunks, i)
		dir, i     = getVector(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setSkin(self, chunks, index, inventor):
		skins = []
		bool, i = getSurfBool(chunks, index)
		norm, i = getSurfNorm(chunks, i)
		dir, i  = getSurfDir(chunks, i)
		n, i  = getInteger(chunks, i)
		for k in range(0, n):
			skin, i = readSkin(chunks, i, inventor)
			skins.append(skin)
		n, i  = getInteger(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setSweep(self, chunks, index, inventor):
		# Syntax:
		# STR?v>16 SWEEP CURVE CURVE SWEEP VEC RIGID?v>16 VEC{4} f f i i FORMULA n FRML_VAR{n} STR n STR n SINGULARITY (BS3SURFACE|NONE) [float]{6}
		# NONE = RANGE{2} CLOSURE_E{2} SINGULARITY_E{2}
		# CLOSURE_E = {CLOSURE_UNSET, }
		# SINGULARITY_E = {'SINGULARITY_UNKNOWN', }
		i = index
		if (getVersion() > 16.0): # ??? correct ???
			txt, i = getText(chunks, i)
		sw1, i = getSurfSweep(chunks, i)
		c1, i = readCurve(chunks, i) # prfile[0]
		c2, i = readCurve(chunks, i) # sweep-path
		sw2, i = getSurfSweep(chunks, i)
		v1, i = getVector(chunks, i)
		if (getVersion() > 16.0):
			i += 1 # skip rigid/non-rigid
		v2, i = getVector(chunks, i)
		v3, i = getVector(chunks, i)
		v4, i = getVector(chunks, i)
		v5, i = getVector(chunks, i)
		v6, i = getVector(chunks, i)
		if (inventor):
			a1, i = getFloats(chunks, i, 4) # -8.0, 0.0, 0.0, -0.559
		else:
			a1, i = getFloats(chunks, i, 1) # 0.0
		frm1l, i = readFormula(chunks, i)
		frm12, i = readFormula(chunks, i)
		frm13, i = readFormula(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setSweepSpline(self, chunks, index, inventor):
		sw1, i = getSurfSweep(chunks, index)
		n1, i  = getInteger(chunks, i)
		c1, i  = readCurve(chunks, i)
		r1, i  = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		e0, i  = getEnum(chunks, i)
		v1, i  = getVector(chunks, i)
		v2, i  = getVector(chunks, i)
		v3, i  = getVector(chunks, i)
		v4, i  = getVector(chunks, i)
		try:
			v5, i  = getVector(chunks, i)
			v6, i  = getVector(chunks, i)
		except:
			pass
		if (n1 == -2):
			frml1, i = readFormula(chunks, i)
			r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			v1, i = getVector(chunks, i)
			n2, i = getInteger(chunks, i)
			e1, i = getEnum(chunks, i)
			c2, i = readCurve(chunks, i)
			r2, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			n3, i = getInteger(chunks, i)
			e2, i = getEnum(chunks, i)
			frml2, i = readFormula(chunks, i)
			frml3, i = readFormula(chunks, i)
			e7, i = getEnum(chunks, i)
		elif (n1 == -1):
			n2, i = getInteger(chunks, i)	  # 2, 3
			e1, i = getEnum(chunks, i)	      # 0x0B
			c2, i = readCurve(chunks, i)
			r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			n3, i = getFloat(chunks, i)     # 0
			e2, i = getEnum(chunks, i)	      # 0x0B
			if (chunks[i].tag == 0x0A):
				i += 1
				c2, i = readCurve(chunks, i)
				r2, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			else:
				try:
					c2, i = readSurface(chunks, i) # 3, hB, 0, hB
					try:
						r2, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
					except:
						# 0A PCurve 0B
						e4, i = getEnum(chunks, i)
						pc2, i = readCurve(chunks, i)
						e5, i = getEnum(chunks, i)
				except: # dirty hack!!!
					frml1, i = readFormula(chunks, i)
					e3, i = getEnum(chunks, i)

		elif (n1 == 1):
			n2, i  = getInteger(chunks, i)
			e1, i  = getEnum(chunks, i)
			c2, i  = readCurve(chunks, i)
			r2, i  = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
			f3, i  = getFloat(chunks, i)
			e2, i  = getEnum(chunks, i)
			if (n2 == 2):
				e3, i = getEnum(chunks, i)
				c3, i = readCurve(chunks, i)
				r3, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
				a1, i = getIntegers(chunks, i, 2)
				a2, i = getFloats(chunks, i, 6)
			elif (n2 == 3):
				s1, i = readSurface(chunks, i)
			else:
				raise Exception()
			e4, i = getEnum(chunks, i)
			if (e4 == 0x0A):
				c4, i = readCurve(chunks, i)
			else:
				e5, i = getEnum(chunks, i)
			e6, i = getEnum(chunks, i)
		else:
			raise Exception()
		if (chunks[i].val == 2):
			a1, i = getIntegers(chunks, i, 4)
			a2, i = getFloats(chunks, i, 4)
			e1, i = getEnum(chunks, i)
			e2, i = getEnum(chunks, i)
			e3, i = getEnum(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setScaleClft(self, chunks, index, inventor):
		singularity, i = getSingularity(chunks, index)
		if (singularity == 'full'):
			spline, i = readBS3Surface(chunks, i)
			self.shape = createBSplinesSurface(spline)
			tol, i = getLength(chunks, i)
		elif (singularity == 'none'):
			r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			r2, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			a11, i = getFloatArray(chunks, i)
			a12, i = getFloatArray(chunks, i)
		arr, i  = readArrayFloats(chunks, i, inventor)

		l1, i = readScaleClLoft(chunks, i) # ([1], None, [0], (-1, 2))
		l2, i = readScaleClLoft(chunks, i) # ([1], None, [0], ( 1, 0))
		l3, i = readScaleClLoft(chunks, i) # ([4], None, [0], ( 1, 1))

		e1, i = getEnum(chunks, i)    # 0x0B
		e2, i = getEnum(chunks, i)    # 0x0B
		i1, i = getInteger(chunks, i) # 0

		e4, i = getEnum(chunks, i)
		if (e4 == 0x0A):
			l4, i = readScaleClLoft(chunks, i)
			e5, i = getEnum(chunks, i)
			if (e5 == 0x0A):
				l5, i = readScaleClLoft(chunks, i)
				i2, i = getInteger(chunks, i) # 0
				p1, i = getVector(chunks, i)
			else:
				e4, i = getEnum(chunks, i)
				i1, i = getInteger(chunks, i)
				l5, i = readBS3Curve(chunks, i)
		else:
			e4, i = getEnum(chunks, i) # 0x0B
			i1, i = getInteger(chunks, i)
			if (i1 == 0):
				l5, i = getVector(chunks, i)
			else:
				l5, i = readBS3Curve(chunks, i)

		e5, i = getEnum(chunks, i)    # 0x0B
		e6, i = getEnum(chunks, i)    # 0x0B
		i3, i = getInteger(chunks, i) # 2
		v1, i = getVector(chunks, i)
		v2, i = getVector(chunks, i)
		i4, i = getInteger(chunks, i) # 11
		p3, i = readBS3Curve(chunks, i)
		return i
	def setSum(self, chunks, index, inventor):
		c1, i = readCurve(chunks, index)
		c2, i = readCurve(chunks, i)
		vec, i = getVector(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setShadowTpr(self, chunks, index, inventor):
		self.surface, i = readSurface(chunks, index)
		c1, i     = readCurve(chunks, i)
		c2, i     = readBS2Curve(chunks, i)
		f1, i     = getFloat(chunks, i)
		s1, t1, i = readSplineSurface(chunks, i, True)
		arr, i    = readArrayFloats(chunks, i, inventor)
		v1, i     = getVector(chunks, i)
		u, i      = getFloat(chunks, i)
		v, i      = getFloat(chunks, i)
		return i
	def setTSpline(self, chunks, index, inventor):
		i = self.setSurfaceShape(chunks, index, inventor)
		rU, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		rV, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		type, i = getInteger(chunks, i)
		block, i = getBlock(chunks, i)
		# block: (t_spl_subtrans_object, def (str), values (str)|ref number)
		num, i  = getInteger(chunks, i)
		# int
		return i
	def setVertexBlend(self, chunks, index, inventor):
		n, i = getInteger(chunks, index)
		arr  = []
		for j in range(0, n):
			vbl = VBL()
			i = vbl.read(chunks, i, inventor)
			arr.append(vbl)
		a1, i = getFloats(chunks, i, 2) # int, float
		return i
	def setRuledTpr(self, chunks, index, inventor):
		surf, i = readSurface(chunks, index)
		curv, i = readCurve(chunks, i)
		bs2curf, i = readBS2Curve(chunks, i)
		f1, i = getFloat(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		vec, i = getVector(chunks, i)
		f2, i = getFloat(chunks, i)
		f3, i = getFloat(chunks, i)
		f4, i = getFloat(chunks, i)
		return i
	def setSweptTpr(self, chunks, index, inventor):
		surf, i = readSurface(chunks, index)
		curv, i = readCurve(chunks, i)
		bs2curf, i = readBS2Curve(chunks, i)
		f1, i = getFloat(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		vec, i = getVector(chunks, i)
		f2, i = getFloat(chunks, i)
		f3, i = getFloat(chunks, i)
		return i
	def setRef(self, chunks, index):
		self.ref, i = getInteger(chunks, index)
		return i
	def setBulk(self, chunks, index):
		self.type, i = getValue(chunks, index)
		if (self.type == 'ref'):                   return self.setRef(chunks, i)

		addSubtypeNode('spline', self)

		try:
			prm = SURFACE_TYPES[self.type]
			fkt = getattr(self, prm[0])
			return fkt(chunks, i + prm[1], prm[2])
		except KeyError as ke:
			raise Exception("Spline-Surface: Unknown subtype '%s'!" %(self.type))
	def setSubtype(self, chunks, index):
		self.sense, i  = getSense(chunks, index)
		block, i       = getBlock(chunks, i)
		self.setBulk(block, 0)
		self.rangeU, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		self.rangeV, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def set(self, entity):
		i = super(SurfaceSpline, self).set(entity)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self):
		if (self.shape is None):
			if (self.type == 'ref'):
				surface = getSubtypeNode('spline', self.ref)
				if (surface is not None):
					self.shape = surface.build()
					if (self.shape is None):
						if (hasattr(surface, 'type')):
							logWarning("    ... Don't know how to build surface '%s::%s' - only edges displayed!" %(surface.__class__.__name__, surface.type))
						else:
							logWarning("    ... Don't know how to build surface '%s' - only edges displayed!" %(surface.__class__.__name__))
			if (self.surface is not None):
				self.shape = self.surface.build()
		return self.shape
class SurfaceTorus(Surface):
	'''
	The torus surface is defined by the center point, normal vector, the major
	and min radius, the u-v-origin point the range for u and v and the sense.
	'''
	def __init__(self):
		super(SurfaceTorus, self).__init__()
		self.center   = CENTER
		self.axis     = DIR_Z
		self.major    = 1.0
		self.minor    = 0.1
		self.uvorigin = CENTER
		self.sensev   = 'forward_v'
		self.urange   = Intervall(Range('I', MIN_0), Range('I', MAX_2PI))
		self.vrange   = Intervall(Range('I', MIN_0), Range('I', MAX_2PI))
	def __str__(self): return "Surface-Torus: center=%s, normal=%s, R=%g, r=%g, uvorigin=%s" %(self.center, self.axis, self.major, self.minor, self.uvorigin)
	def __repr__(self): return self.__str__()
	def setSubtype(self, chunks, index):
		self.center, i   = getLocation(chunks, index)
		self.axis, i     = getVector(chunks, i)
		self.major, i    = getLength(chunks, i)
		self.minor, i    = getLength(chunks, i)
		self.uvorigin, i = getLocation(chunks, i)
		self.sensev, i   = getSensev(chunks, i)
		self.urange, i   = getInterval(chunks, i, MIN_0, MAX_2PI, 1.0)
		self.vrange, i   = getInterval(chunks, i, MIN_0, MAX_2PI, 1.0)
		return i
	def set(self, entity):
		i = super(SurfaceTorus, self).set(entity)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self):
		if (self.shape is None):
			major = math.fabs(self.major)
			minor = math.fabs(self.minor)
			try:
				torus = Part.Toroid()
				rotateShape(torus, self.axis)
				torus.Center = self.center
				torus.MajorRadius = math.fabs(self.major)
				torus.MinorRadius = math.fabs(self.minor)
				self.shape = torus.toShape()
			except Exception as e:
				logError("    Creation of torus failed for major=%g, minor=%g, center=%s, axis=%s:\n\t%s" %(major, minor, self.center, self.axis, e))
		return self.shape
class Point(Geometry):
	def __init__(self):
		super(Point, self).__init__()
		self.position = CENTER
		self.count    = -1 # Number of references
	def set(self, entity):
		i = super(Point, self).set(entity)
		self.position, i = getLocation(entity.chunks, i)
		return i
class Refinement(Entity):
	def __init__(self): return super(Refinement, self).__init__()
# abstract super class for all attributes
class Attributes(Entity):
	def __init__(self):
		super(Attributes, self).__init__()
		self._next     = None
		self._previous = None
		self._owner    = None
	def set(self, entity):
		i = super(Attributes, self).set(entity)
		self._next, i     = getRefNode(entity, i, 'attrib')
		self._previous, i = getRefNode(entity, i, 'attrib')
		self._owner, i    = getRefNode(entity, i, None)
		if (getVersion() > 15.0):
			i += 17 # skip ???
		return i
	def getNext(self):     return None if (self._next is None)     else self._next.node
	def getPrevious(self): return None if (self._previous is None) else self._previous.node
	def getOwner(self):    return None if (self._owner is None)    else self._owner.node
class Attrib(Attributes):
	def __init__(self): super(Attrib, self).__init__()
	def set(self, entity): return super(Attrib, self).set(entity)
class AttribADesk(Attrib):
	def __init__(self): super(AttribADesk, self).__init__()
class AttribADeskColor(AttribADesk):
	def __init__(self): super(AttribADeskColor, self).__init__()
class AttribAnsoft(Attrib):
	def __init__(self): super(AttribAnsoft, self).__init__()
class AttribAnsoftId(AttribAnsoft):
	def __init__(self): super(AttribAnsoftId, self).__init__()
class AttribAnsoftProperties(AttribAnsoft):
	def __init__(self): super(AttribAnsoftProperties, self).__init__()
class AttribDxid(Attrib):
	def __init__(self): super(AttribDxid, self).__init__()
class AttribCustom(Attrib):
	def __init__(self): super(AttribCustom, self).__init__()
class AttribEye(Attrib):
	def __init__(self): super(AttribEye, self).__init__()
class AttribEyeFMesh(AttribEye):
	def __init__(self): super(AttribEyeFMesh, self).__init__()
class AttribEyePtList(AttribEye):
	def __init__(self): super(AttribEyePtList, self).__init__()
class AttribEyeRefVt(AttribEye):
	def __init__(self): super(AttribEyeRefVt, self).__init__()
class AttribFdi(Attrib):
	def __init__(self): super(AttribFdi, self).__init__()
class AttribFdiLabel(AttribFdi):
	def __init__(self): super(AttribFdiLabel, self).__init__()
class AttribGen(Attrib):
	def __init__(self): super(AttribGen, self).__init__()
class AttribGenName(AttribGen):
	def __init__(self):
		super(AttribGenName, self).__init__()
		self.text = ''
	def set(self, entity):
		i = super(AttribGenName, self).set(entity)
		if (getVersion() < 16.0):
			i += 4 # [(keep|copy) , (keep_keep), (ignore), (copy)]
		self.text, i = getText(entity.chunks, i)
		return i
class AttribGenNameInteger(AttribGenName):
	def __init__(self):
		super(AttribGenNameInteger, self).__init__()
		self.value = 0
	def set(self, entity):
		i = super(AttribGenNameInteger, self).set(entity)
		if (getVersion() > 10):
			self.name, i  = getText(entity.chunks, i)
		self.value, i = getInteger(entity.chunks, i)
		return i
class AttribGenNameString(AttribGenName):
	def __init__(self):
		super(AttribGenNameString, self).__init__()
		self.value = ''
	def set(self, entity):
		i = super(AttribGenNameString, self).set(entity)
		self.value, i = getText(entity.chunks, i)
		return i
class AttribLwd(Attrib):
	def __init__(self): super(AttribLwd, self).__init__()
class AttribLwdFMesh(Attrib): # color face mapping
	def __init__(self): super(AttribLwdFMesh, self).__init__()
class AttribLwdPtList(Attrib): # Refinement-VertexTemplate mapping for body
	def __init__(self): super(AttribLwdPtList, self).__init__()
class AttribLwdRefVT(Attrib): # Refinement-VertexTemplate mapping for body
	def __init__(self): super(AttribLwdRefVT, self).__init__()
class AttribRfBase(Attrib):
	def __init__(self): super(AttribRfBase, self).__init__()
class AttribRfBaseFaceTracker(AttribRfBase):
	def __init__(self): super(AttribRfBaseFaceTracker, self).__init__()
class AttribSg(Attrib):
	def __init__(self): super(AttribSg, self).__init__()
class AttribSgPidName(AttribSg):
	def __init__(self): super(AttribSgPidName, self).__init__()
class AttribSnl(Attrib):
	def __init__(self): super(AttribSnl, self).__init__()
class AttribSnlCubitOwner(AttribSnl):
	def __init__(self):super(AttribSnlCubitOwner, self).__init__()
class AttribSt(Attrib):
	def __init__(self): super(AttribSt, self).__init__()
class AttribStNoMerge(AttribSt):
	def __init__(self): super(AttribStNoMerge, self).__init__()
class AttribStNoCombine(AttribSt):
	def __init__(self): super(AttribStNoCombine, self).__init__()
class AttribStRgbColor(AttribSt):
	def __init__(self):
		super(AttribStRgbColor, self).__init__()
		self.color = (0.5, 0.5, 0.5)
	def set(self, entity):
		i = super(AttribStRgbColor, self).set(entity)
		self.color, i = getPoint(entity.chunks, i)
		return i
class AttribStDisplay(AttribSt):
	def __init__(self): super(AttribStDisplay, self).__init__()
class AttribStId(AttribSt):
	def __init__(self): super(AttribStId, self).__init__()
class AttribSys(Attrib):
	def __init__(self): super(AttribSys, self).__init__()
class AttribSysAnnotationAttrib(AttribSys):
	def __init__(self): super(AttribSysAnnotationAttrib, self).__init__()
class AttribSysConvexity(AttribSt):
	def __init__(self): super(AttribSysConvexity, self).__init__()
class AttribSysStichHint(AttribSys):
	def __init__(self): super(AttribSysStichHint, self).__init__()
class AttribSysTag(AttribSys):
	def __init__(self): super(AttribSysTag, self).__init__()
class AttribSysVertedge(AttribSys):
	def __init__(self): super(AttribSysVertedge, self).__init__()
class AttribTsl(Attrib):
	def __init__(self): super(AttribTsl, self).__init__()
class AttribTslId(AttribTsl):
	def __init__(self): super(AttribTslId, self).__init__()
class AttribMixOrganization(Attrib):
	def __init__(self): super(AttribMixOrganization, self).__init__()
class AttribMixOrganizationDecalEntity(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationDecalEntity, self).__init__()
class AttribMixOrganizationDetailEdgeInfo(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationDetailEdgeInfo, self).__init__()
class AttribMixOrganizationEntityQuality(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationEntityQuality, self).__init__()
class AttribMixOrganizationCreEntityQuality(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationCreEntityQuality, self).__init__()
class AttribMixOrganizationBendExtendPlane(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationBendExtendPlane, self).__init__()
class AttribMixOrganizationCornerEdge(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationCornerEdge, self).__init__()
class AttribMixOrganizationFlangeTrimEdge(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationFlangeTrimEdge, self).__init__()
class AttribMixOrganizationJacobiCornerEdge(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationJacobiCornerEdge, self).__init__()
class AttribMixOrganizationLimitTrackingFraceFrom(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationLimitTrackingFraceFrom, self).__init__()
class AttribMixOrganizationNoBendRelief(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationNoBendRelief, self).__init__()
class AttribMixOrganizationNoCenterline(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationNoCenterline, self).__init__()
class AttribMixOrganizationSmoothBendEdge(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationSmoothBendEdge, self).__init__()
class AttribMixOrganizationTraceFace(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationTraceFace, self).__init__()
class AttribMixOrganizationUfContourRollExtentTrack(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationUfContourRollExtentTrack, self).__init__()
class AttribMixOrganizationUfFaceType(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationUfFaceType, self).__init__()
class AttribMixOrganizationUnfoldInfo(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationUnfoldInfo, self).__init__()
class AttribNamingMatching(Attrib):
	def __init__(self): super(AttribNamingMatching, self).__init__()
class AttribNamingMatchingNMxMatchedEntity(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxMatchedEntity, self).__init__()
class AttribNamingMatchingNMxEdgeCurve(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxEdgeCurve, self).__init__()
class AttribNamingMatchingNMxDup(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxDup, self).__init__()
class AttribNamingMatchingNMxPuchtoolBRep(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxPuchtoolBRep, self).__init__()
class AttribNamingMatchingNMxFFColorEntity(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxFFColorEntity, self).__init__()
class AttribNamingMatchingNMxThreadEntity(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxThreadEntity, self).__init__()
class AttribNamingMatchingNMxFeatureOrientation(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxFeatureOrientation, self).__init__()
class AttribNamingMatchingNMxGenTagDisambiguation(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxGenTagDisambiguation, self).__init__()
class AttribNamingMatchingNMxFeatureDependency(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxFeatureDependency, self).__init__()
class AttribNamingMatchingNMxBrepTag(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxBrepTag, self).__init__()
class AttribNamingMatchingNMxBrepTagFeature(AttribNamingMatchingNMxBrepTag):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagFeature, self).__init__()
class AttribNamingMatchingNMxBrepTagSwitch(AttribNamingMatchingNMxBrepTag):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagSwitch, self).__init__()
class AttribNamingMatchingNMxBrepTagName(AttribNamingMatchingNMxBrepTag):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagName, self).__init__()
class AttribNamingMatchingNMxBrepTagNameBPatch(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameBPatch, self).__init__()
class AttribNamingMatchingNMxBrepTagNameBlend(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameBlend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameBodySplit(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameBodySplit, self).__init__()
class AttribNamingMatchingNMxBrepTagNameCompositeFeature(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameCompositeFeature, self).__init__()
class AttribNamingMatchingNMxBrepTagNameCornerSculpt(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameCornerSculpt, self).__init__()
class AttribNamingMatchingNMxBrepTagNameMold(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameMold, self).__init__()
class AttribNamingMatchingNMxBrepTagNameMoveFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameMoveFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameHole(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameHole, self).__init__()
class AttribNamingMatchingNMxBrepTagNameImportAlias(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameImportAlias, self).__init__()
class AttribNamingMatchingNMxBrepTagNameLocalFaceModifier(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameLocalFaceModifier, self).__init__()
class AttribNamingMatchingNMxBrepTagNameLocalFaceModifierForCorner(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameLocalFaceModifierForCorner, self).__init__()
class AttribNamingMatchingNMxBrepTagNameThickenFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameThickenFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameTrim(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameTrim, self).__init__()
class AttribNamingMatchingNMxBrepTagNameTweakFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameTweakFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameTweakReblend(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameTweakReblend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameVertexBlend(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameVertexBlend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameLoftSurface(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameLoftSurface, self).__init__()
class AttribNamingMatchingNMxBrepTagNameLoftedFlange(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameLoftedFlange, self).__init__()
class AttribNamingMatchingNMxBrepTagNameReversedFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameReversedFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameShadowTaperFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameShadowTaperFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameModFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameModFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameBend(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameBend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameBendPart(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameBendPart, self).__init__()
class AttribNamingMatchingNMxBrepTagNameCutXBendRimFaceTag(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameCutXBendRimFaceTag, self).__init__()
class AttribNamingMatchingNMxBrepTagNameDeleteFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameDeleteFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameEdgeBlend(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameEdgeBlend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameEmbossBottomFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameEmbossBottomFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameEmbossRimFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameEmbossRimFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameEntityEntityBlend(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameEntityEntityBlend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameExtBool(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameExtBool, self).__init__()
class AttribNamingMatchingNMxBrepTagNameExtendSurf(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameExtendSurf, self).__init__()
class AttribNamingMatchingNMxBrepTagNameFlange(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameFlange, self).__init__()
class AttribNamingMatchingNMxBrepTagNameFoldFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameFoldFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameGenerated(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameGenerated, self).__init__()
class AttribNamingMatchingNMxBrepTagNameGrillOffsetBrep(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameGrillOffsetBrep, self).__init__()
class AttribNamingMatchingNMxBrepTagNameSweepGenerated(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameSweepGenerated, self).__init__()
class AttribNamingMatchingNMxBrepTagNameShellFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameShellFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameSplitFace(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameSplitFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameSplitVertex(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameSplitVertex, self).__init__()
class AttribNamingMatchingNMxBrepTagNameSplitEdge(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameSplitEdge, self).__init__()
class AttribAtUfld(Attrib):
	def __init__(self): super(AttribAtUfld, self).__init__()
class AttribAtUfldDefmData(AttribAtUfld):
	def __init__(self): super(AttribAtUfldDefmData, self).__init__()
class AttribAtUfldDevPair(AttribAtUfld):
	def __init__(self): super(AttribAtUfldDevPair, self).__init__()
class AttribAtUfldFfldPosTransf(AttribAtUfld):
	def __init__(self): super(AttribAtUfldFfldPosTransf, self).__init__()
class AttribAtUfldFfldPosTransfMixUfContourRollTrack(AttribAtUfldFfldPosTransf):
	def __init__(self): super(AttribAtUfldFfldPosTransfMixUfContourRollTrack, self).__init__()
class AttribAtUfldNonMergeBend(AttribAtUfld):
	def __init__(self): super(AttribAtUfldNonMergeBend, self).__init__()
class AttribAtUfldPosTrack(AttribAtUfld):
	def __init__(self): super(AttribAtUfldPosTrack, self).__init__()
class AttribAtUfldPosTrackMixUfRobustPositionTrack(AttribAtUfldPosTrack):
	def __init__(self): super(AttribAtUfldPosTrackMixUfRobustPositionTrack, self).__init__()
class AttribAtUfldPosTrackSurfSimp(AttribAtUfldPosTrackMixUfRobustPositionTrack):
	def __init__(self): super(AttribAtUfldPosTrackSurfSimp, self).__init__()

# abstract super class for all annotations
class Annotation(Entity):
	def __init__(self): super(Annotation, self).__init__()
class AnnotationPrimitive(Annotation):
	def __init__(self): super(AnnotationPrimitive, self).__init__()
class AnnotationSplit(Annotation):
	def __init__(self): super(AnnotationSplit, self).__init__()
class AnnotationTol(Annotation):
	def __init__(self): super(AnnotationTol, self).__init__()
class AnnotationTolCreate(AnnotationTol):
	def __init__(self): super(AnnotationTolCreate, self).__init__()
class AnnotationTolRevert(AnnotationTol):
	def __init__(self): super(AnnotationTolRevert, self).__init__()

class AcisChunk():
	def __init__(self, key, val):
		self.tag = key
		self.val = val
	def __str__(self):
		if (self.tag == 0x04): return "%d "     %(self.val)
		if (self.tag == 0x06): return "%g "     %(self.val)
		if (self.tag == 0x07): return "@%d %s " %(len(self.val), self.val)                 # STRING
		if (self.tag == 0x08): return "%s"      %(self.val)                                # STRING
		if (self.tag == 0x0A): return "%s "     %(self.val)
		if (self.tag == 0x0B): return "%s "     %(self.val)
		if (self.tag == 0x0C): return "%s "     %(self.val)                                # ENTITY_POINTER
		if (self.tag == 0x0D): return "%s "     %(self.val)                                # CLASS_IDENTIFYER
		if (self.tag == 0x0E): return "%s-"     %(self.val)                                # SUBCLASS_IDENTIFYER
		if (self.tag == 0x0F): return "%s "     %(self.val)                                # SUBTYP_START
		if (self.tag == 0x10): return "%s "     %(self.val)                                # SUBTYP_END
		if (self.tag == 0x11): return "%s\n"    %(self.val)                                # TERMINATOR
		if (self.tag == 0x12): return "@%d %s " %(len(self.val), self.val)                 # STRING
		if (self.tag == 0x13): return "(%s) "   %(" ".join(["%g" %(f) for f in self.val]))
		if (self.tag == 0x14): return "(%s) "   %(" ".join(["%g" %(f) for f in self.val])) # something to do with scale
		if (self.tag == 0x15): return "%d "     %(self.val)
		if (self.tag == 0x16): return "(%s) "   %(" ".join(["%g" %(f) for f in self.val]))
		return ''
	def __repr__(self):
		if (self.tag == 0x04): return "%d "   %(self.val)
		if (self.tag == 0x06): return "%g "   %(self.val)
		if (self.tag == 0x07): return "'%s' " %(self.val)                                # STRING
		if (self.tag == 0x08): return "'%s' " %(self.val)                                # STRING
		if (self.tag == 0x0A): return '0x0A '
		if (self.tag == 0x0B): return '0x0B '
		if (self.tag == 0x0E): return "%s-"   %(self.val)                                # SUBCLASS_IDENTIFYER
		if (self.tag == 0x0F): return '{ '
		if (self.tag == 0x10): return '} '
		if (self.tag == 0x11): return '#'
		if (self.tag == 0x12): return "'%s' " %(self.val)                                # STRING
		if (self.tag == 0x11): return "%s "   %(self.val)                                # TERMINATOR
		if (self.tag == 0x13): return "(%s) " %(" ".join(["%g" %(f) for f in self.val]))
		if (self.tag == 0x14): return "(%s) " %(" ".join(["%g" %(f) for f in self.val])) # something to do with scale
		if (self.tag == 0x15): return "%d "   %(self.val)
		if (self.tag == 0x16): return "(%s) " %(" ".join(["%g" %(f) for f in self.val]))
		return "%s " %(self.val)

class AcisEntity():
	def __init__(self, name):
		self.chunks = []
		self.name   = name
		self.index  = -1
		self.node   = None

	def add(self, key, val):
		self.chunks.append(AcisChunk(key, val))
	def getStr(self): return "-%d %s %s" %(self.index, self.name, ''.join('%s' %c for c in self.chunks))
	def __repr__(self): return "%s %s" %(self.name, ''.join('%r' %c for c in self.chunks))
	def __str__(self):
		if (self.index < 0):
			if (self.index == -2):
				return "%s %s" %(self.name,''.join('%s' %c for c in self.chunks))
			return ""
		return self.getStr()

class AcisRef():
	def __init__(self, index):
		self.index = index
		self.entity = None

	def __str__(self):
		if (self.entity is None or self.entity.index < 0):
			return "$%d" % self.index
		return "$%d" %(self.entity.index)
	def __repr__(self):
		return self.__str__()

def readStr1(data, offset):
	l, i = getUInt8(data, offset)
	end = i + l
	txt = data[i: end].decode('cp1252').encode(ENCODING_FS)
	return txt, end

def readStr2(data, offset):
	l, i = getUInt16(data, offset)
	end = i + l
	txt = data[i: end].decode('cp1252').encode(ENCODING_FS)
	return txt, end

def readStr4(data, offset):
	l, i = getUInt32(data, offset)
	end = i + l
	txt = data[i: end].decode('cp1252').encode(ENCODING_FS)
	return txt, end

def readEntityRef(data, offset):
	index, i = getSInt32(data, offset)
	return AcisRef(index), i

def readTagA(data, index):         return '0x0A', index
def readTagB(data, index):         return '0x0B', index
def readTagOpen(data, index):      return '{', index
def readTagClose(data, index):     return '}', index
def readTagTerminate(data, index): return '#', index
def readTagFloats3D(data, index):  return getFloat64A(data, index, 3)
def readTagFloats2D(data, index):  return getFloat64A(data, index, 2)

TAG_READER = {
	0x04: getSInt32,
	0x06: getFloat64,
	0x07: readStr1,
	0x08: readStr2,
	0x0A: readTagA,
	0x0B: readTagB,
	0x0C: readEntityRef,
	0x0D: readStr1,
	0x0E: readStr1,
	0x0F: readTagOpen,
	0x10: readTagClose,
	0x11: readTagTerminate,
	0x12: readStr4,
	0x13: readTagFloats3D,
	0x14: readTagFloats3D,
	0x15: getUInt32,
	0x16: readTagFloats2D,
}

def readNextSabChunk(data, index):
	tag, i = getUInt8(data, index)
	try:
		reader = TAG_READER[tag]
		return (tag, ) + reader(data, i)
	except KeyError as ke:
		raise Exception("Don't know to read TAG %X" %(tag))

CURVES = {
	'compcurv':          CurveComp,
	'degenerate_curve':  CurveDegenerate,
	'ellipse':           CurveEllipse,
	'intcurve':          CurveInt,
	'intcurve-intcurve': CurveIntInt,
	'pcurve':            CurveP,
	'straight':          CurveStraight,
	'null_curve':        None,
	'null_pcurve':       None,
}

SURFACES = {
	'cone':         SurfaceCone,
	'mesh':         SurfaceMesh,
	'plane':        SurfacePlane,
	'sphere':       SurfaceSphere,
	'spline':       SurfaceSpline,
	'torus':        SurfaceTorus,
	'null_surface': None,
}

CURVE_TYPES = {
	'bldcur':            ('setBlend', 0, False),
	'blend_int_cur':     ('setBlend', 1, True),
	'blndsprngcur':      ('setBlendSprng', 0, False),
	'comp_int_cur':      ('setComp', 1, True),
	'defm_int_cur':      ('setDefm', 1, True),
	'exactcur':          ('setExact', 0, False),
	'exact_int_cur':     ('setExact', 1, True),
	'helix_int_cur':     ('setHelix', 1, True),
	'int_int_cur':       ('setInt', 1, True),
	'lawintcur':         ('setLaw', 0, False),
	'law_int_cur':       ('setLaw', 1, True),
	'offintcur':         ('setOff', 0, False),
	'off_int_cur':       ('setOff', 1, True),
	'offsetintcur':      ('setOffset', 0, False),
	'offset_int_cur':    ('setOffset', 1, True),
	'offsurfintcur':     ('setOffsetSurface', 0, False),
	'off_surf_int_cur':  ('setOffsetSurface', 1, True),
	'parcur':            ('setParameter', 0, False),
	'par_int_cur':       ('setParameter', 1, True),
	'para_silh_int_cur': ('setParameterSilhouette', 1, True),
	'proj_int_cur':      ('setProject', 1, True),
	'spring_int_cur':    ('setSpring', 1, True),
	'surfintcur':        ('setSurface', 0, False),
	'surf_int_cur':      ('setSurface', 1, True),
}

SURFACE_TYPES = {
	'cl_loft_spl_sur':      ('setClLoft', 1, True),
	'comp_spl_sur':         ('setCompound', 1, True),
	'cylsur':               ('setCylinder', 0, False),
	'cyl_spl_sur':          ('setCylinder', 1, True),
	'defmsur':              ('setDefm', 0, False),
	'defm_spl_sur':         ('setDefm', 1, True),
	'exactsur':             ('setExact', 0, False),
	'exact_spl_sur':        ('setExact', 1, True),
	'g2blnsur':             ('setG2Blend', 0, False),
	'g2_blend_spl_sur':     ('setG2Blend', 1, True),
	'helix_spl_circ':       ('setHelixCircle', 1, True),
	'helix_spl_line':       ('setHelixLine', 1, True),
	'loftsur':              ('setLoft', 0, False),
	'loft_spl_sur':         ('setLoft', 1, True),
	'net_spl_sur':          ('setNet', 1, True),
	'offsur':               ('setOffset', 0, False),
	'off_spl_sur':          ('setOffset', 1, True),
	'orthosur':             ('setOrtho', 0, False),
	'ortho_spl_sur':        ('setOrtho', 1, True),
	'rbblnsur':             ('setRbBlend', 0, False),
	'rb_blend_spl_sur':     ('setRbBlend', 1, True),
	'rotsur':               ('setRotation', 0, False),
	'rot_spl_sur':          ('setRotation', 1,  True),
	'sclclftsur':           ('setScaleClft', 0, False),
	'scaled_cloft_spl_sur': ('setScaleClft', 1, True),
	'shadow_tpr_spl_sur':   ('setShadowTpr', 1, True),
	'skinsur':              ('setSkin', 0, False),
	'skin_spl_sur':         ('setSkin', 1, True),
	'sweepsur':             ('setSweep', 0, False),
	'sweep_spl_sur':        ('setSweep', 1, True),
	'sweep_sur':            ('setSweepSpline', 1, True),
	't_spl_sur':            ('setTSpline', 1, True),
	'vertexblendsur':       ('setVertexBlend', 0, False),
	'VBL_SURF':             ('setVertexBlend', 1, True),
	'srfsrfblndsur':        ('setBlendSupply', 0, False),
	'srf_srf_v_bl_spl_sur': ('setBlendSupply', 1, True),
	'sssblndsur':           ('setBlendSupply', 0, False),
	'sss_blend_spl_sur':    ('setBlendSupply', 1, True),
	'sumsur':               ('setSum', 0, False),
	'sum_spl_sur':          ('setSum', 1, True),
	'ruled_tpr_spl_sur':    ('setRuledTpr', 1, True),
	'swept_tpr_spl_sur':    ('setSweptTpr', 1, True),
}

ENTITY_TYPES = {
	"annotation":                                                                                  Annotation,
	"primitive_annotation-annotation":                                                             AnnotationPrimitive,
	"split_annotation-annotation":                                                                 AnnotationSplit,
	"tol_annotation-annotation":                                                                   AnnotationTol,
	"create_tol_anno-tol_annotation-annotation":                                                   AnnotationTolCreate,
	"revert_tol_anno-tol_annotation-annotation":                                                   AnnotationTolRevert,
	"asmheader":                                                                                   AsmHeader,
	"attrib":                                                                                      Attrib,
	"adesk-attrib":                                                                                AttribADesk,
	"color-adesk-attrib":                                                                          AttribADeskColor,
	"ansoft-attrib":                                                                               AttribAnsoft,
	"id-ansoft-attrib":                                                                            AttribAnsoftId,
	"properties-ansoft-attrib":                                                                    AttribAnsoftProperties,
	"at_ufld-attrib":                                                                              AttribAtUfld,
	"ufld_defm_data_attrib-at_ufld-attrib":                                                        AttribAtUfldDefmData,
	"ufld_dev_pair_attrib-at_ufld-attrib":                                                         AttribAtUfldDevPair,
	"ufld_pos_transf_attrib-at_ufld-attrib":                                                       AttribAtUfldFfldPosTransf,
	"mix_UF_ContourRoll_Track-ufld_pos_transf_attrib-at_ufld-attrib":                              AttribAtUfldFfldPosTransfMixUfContourRollTrack,
	"ufld_non_merge_bend_attrib-at_ufld-attrib":                                                   AttribAtUfldNonMergeBend,
	"ufld_pos_track_attrib-at_ufld-attrib":                                                        AttribAtUfldPosTrack,
	"mix_UF_RobustPositionTrack-ufld_pos_track_attrib-at_ufld-attrib":                             AttribAtUfldPosTrackMixUfRobustPositionTrack,
	"ufld_surf_simp_attrib-ufld_pos_track_attrib-at_ufld-attrib":                                  AttribAtUfldPosTrackSurfSimp,
	"DXID-attrib":                                                                                 AttribDxid,
	"ATTRIB_CUSTOM-attrib":                                                                        AttribCustom,
	"eye-attrib":                                                                                  AttribEye,
	"fmesh-eye-attrib":                                                                            AttribEyeFMesh,
	"ptlist-eye-attrib":                                                                           AttribEyePtList,
	"ref_vt-eye-attrib":                                                                           AttribEyeRefVt,
	"fdi-attrib":                                                                                  AttribFdi,
	"label-fdi-attrib":                                                                            AttribFdiLabel,
	"gen-attrib":                                                                                  AttribGen,
	"name_attrib-gen-attrib":                                                                      AttribGenName,
	"integer_attrib-name_attrib-gen-attrib":                                                       AttribGenNameInteger,
	"string_attrib-name_attrib-gen-attrib":                                                        AttribGenNameString,
	"lwd-attrib":                                                                                  AttribLwd,
	"fmesh-lwd-attrib":                                                                            AttribLwdFMesh,
	"ptlist-lwd-attrib":                                                                           AttribLwdPtList,
	"ref_vt-lwd-attrib":                                                                           AttribLwdRefVT,
	"mix_Organizaion-attrib":                                                                      AttribMixOrganization,
	"mix_BendExtendPlane-mix_Organizaion-attrib":                                                  AttribMixOrganizationBendExtendPlane,
	"mix_CornerEdge-mix_Organizaion-attrib":                                                       AttribMixOrganizationCornerEdge,
	"mix_CREEntityQuality-mix_Organizaion-attrib":                                                 AttribMixOrganizationCreEntityQuality,
	"MIx_Decal_Entity-mix_Organizaion-attrib":                                                     AttribMixOrganizationDecalEntity,
	"mix_DetailEdgeInfo-mix_Organizaion-attrib":                                                   AttribMixOrganizationDetailEdgeInfo,
	"mix_EntityQuality-mix_Organizaion-attrib":                                                    AttribMixOrganizationEntityQuality,
	"mix_FlangeTrimEdge-mix_Organizaion-attrib":                                                   AttribMixOrganizationFlangeTrimEdge,
	"mix_JacobiCornerEdge-mix_Organizaion-attrib":                                                 AttribMixOrganizationJacobiCornerEdge,
	"mix_LimitTrackingFaceFrom-mix_Organizaion-attrib":                                            AttribMixOrganizationLimitTrackingFraceFrom,
	"mix_NoBendRelief-mix_Organizaion-attrib":                                                     AttribMixOrganizationNoBendRelief,
	"mix_NoCenterline-mix_Organizaion-attrib":                                                     AttribMixOrganizationNoCenterline,
	"mix_SmoothBendEdge-mix_Organizaion-attrib":                                                   AttribMixOrganizationSmoothBendEdge,
	"mix_TrackFace-mix_Organizaion-attrib":                                                        AttribMixOrganizationTraceFace,
	"mix_UF_ContourRoll_Extent_Track-mix_Organizaion-attrib":                                      AttribMixOrganizationUfContourRollExtentTrack,
	"mix_UF_Face_Type-mix_Organizaion-attrib":                                                     AttribMixOrganizationUfFaceType,
	"mix_UnfoldInfo-mix_Organizaion-attrib":                                                       AttribMixOrganizationUnfoldInfo,
	"NamingMatching-attrib":                                                                       AttribNamingMatching,
	"NMx_Brep_tag-NamingMatching-attrib":                                                          AttribNamingMatchingNMxBrepTag,
	"NMx_Brep_Feature_tag-NMx_Brep_tag-NamingMatching-attrib":                                     AttribNamingMatchingNMxBrepTagFeature,
	"NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                                        AttribNamingMatchingNMxBrepTagName,
	"NMx_BPatch_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                         AttribNamingMatchingNMxBrepTagNameBPatch,
	"NMx_bend_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                           AttribNamingMatchingNMxBrepTagNameBend,
	"NMx_bend_part_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                      AttribNamingMatchingNMxBrepTagNameBendPart,
	"NMx_blend_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                          AttribNamingMatchingNMxBrepTagNameBlend,
	"NMx_body_split_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameBodySplit,
	"NMx_Composite_feature_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":              AttribNamingMatchingNMxBrepTagNameCompositeFeature,
	"NMx_Corner_Sculpt_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                  AttribNamingMatchingNMxBrepTagNameCornerSculpt,
	"NMx_CutXBendRimFaceTag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                 AttribNamingMatchingNMxBrepTagNameCutXBendRimFaceTag,
	"NMx_delete_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                    AttribNamingMatchingNMxBrepTagNameDeleteFace,
	"NMx_edge_blend_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameEdgeBlend,
	"NMx_EmbossBottomFaceTag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                AttribNamingMatchingNMxBrepTagNameEmbossBottomFace,
	"NMx_EmbossRimFaceTag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                   AttribNamingMatchingNMxBrepTagNameEmbossRimFace,
	"NMx_entity_entity_blend_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":            AttribNamingMatchingNMxBrepTagNameEntityEntityBlend,
	"NMx_Ext_Bool_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                       AttribNamingMatchingNMxBrepTagNameExtBool,
	"NMx_extend_surf_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                    AttribNamingMatchingNMxBrepTagNameExtendSurf,
	"NMx_flange_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                         AttribNamingMatchingNMxBrepTagNameFlange,
	"NMx_fold_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                      AttribNamingMatchingNMxBrepTagNameFoldFace,
	"NMx_Generated_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                 AttribNamingMatchingNMxBrepTagNameGenerated,
	"NMx_GrillOffset_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":               AttribNamingMatchingNMxBrepTagNameGrillOffsetBrep,
	"NMx_Hole_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                      AttribNamingMatchingNMxBrepTagNameHole,
	"NMx_import_alias_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                   AttribNamingMatchingNMxBrepTagNameImportAlias,
	"NMx_local_face_modifier_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":            AttribNamingMatchingNMxBrepTagNameLocalFaceModifier,
	"NMx_local_face_modifier_for_corner_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib": AttribNamingMatchingNMxBrepTagNameLocalFaceModifierForCorner,
	"NMx_Loft_Surface_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":              AttribNamingMatchingNMxBrepTagNameLoftSurface,
	"NMx_LoftedFlange_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":              AttribNamingMatchingNMxBrepTagNameLoftedFlange,
	"NMx_mod_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                       AttribNamingMatchingNMxBrepTagNameModFace,
	"NMx_mold_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                           AttribNamingMatchingNMxBrepTagNameMold,
	"NMx_move_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                      AttribNamingMatchingNMxBrepTagNameMoveFace,
	"NMx_reversed_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                  AttribNamingMatchingNMxBrepTagNameReversedFace,
	"NMx_shadow_taper_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":              AttribNamingMatchingNMxBrepTagNameShadowTaperFace,
	"NMx_shell_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameShellFace,
	"NMx_Split_Egde_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameSplitEdge,
	"NMx_split_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameSplitFace,
	"NMx_Split_Vertex_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                   AttribNamingMatchingNMxBrepTagNameSplitVertex,
	"NMx_Sweep_Generated_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":           AttribNamingMatchingNMxBrepTagNameSweepGenerated,
	"NMx_Thicken_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                   AttribNamingMatchingNMxBrepTagNameThickenFace,
	"NMx_Trim_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                           AttribNamingMatchingNMxBrepTagNameTrim,
	"NMx_tweak_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameTweakFace,
	"NMx_tweak_reblend_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                  AttribNamingMatchingNMxBrepTagNameTweakReblend,
	"NMx_vertex_blend_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                   AttribNamingMatchingNMxBrepTagNameVertexBlend,
	"NMx_stitch_tag-NMx_Brep_tag-NamingMatching-attrib":                                           AttribNamingMatchingNMxBrepTagSwitch,
	"NMx_Dup_Attrib-NamingMatching-attrib":                                                        AttribNamingMatchingNMxDup,
	"NMxEdgeCurveAttrib-NamingMatching-attrib":                                                    AttribNamingMatchingNMxEdgeCurve,
	"NMx_FFColor_Entity-NamingMatching-attrib":                                                    AttribNamingMatchingNMxFFColorEntity,
	"NMx_feature_dependency_attrib-NamingMatching-attrib":                                         AttribNamingMatchingNMxFeatureDependency,
	"NMx_Feature_Orientation-NamingMatching-attrib":                                               AttribNamingMatchingNMxFeatureOrientation,
	"NMx_GenTag_Disambiguation_Attrib-NamingMatching-attrib":                                      AttribNamingMatchingNMxGenTagDisambiguation,
	"NMx_Matched_Entity-NamingMatching-attrib":                                                    AttribNamingMatchingNMxMatchedEntity,
	"NMx_Punchtool_Brep_tag-NamingMatching-attrib":                                                AttribNamingMatchingNMxPuchtoolBRep,
	"NMx_Thread_Entity-NamingMatching-attrib":                                                     AttribNamingMatchingNMxThreadEntity,
	"RFbase-attrib":                                                                               AttribRfBase,
	"RFFaceTracker-RFbase-attrib":                                                                 AttribRfBaseFaceTracker,
	"sg-attrib":                                                                                   AttribSg,
	"pid_name-sg-attrib":                                                                          AttribSgPidName,
	"snl-attrib":                                                                                  AttribSnl,
	"cubit_owner-snl-attrib":                                                                      AttribSnlCubitOwner,
	"st-attrib":                                                                                   AttribSt,
	"no_merge_attribute-st-attrib":                                                                AttribStNoMerge,
	"no_combine_attribute-st-attrib":                                                              AttribStNoCombine,
	"rgb_color-st-attrib":                                                                         AttribStRgbColor,
	"display_attribute-st-attrib":                                                                 AttribStDisplay,
	"id_attribute-st-attrib":                                                                      AttribStId,
	"sys-attrib":                                                                                  AttribSys,
	"convexity-sys-attrib":                                                                        AttribSysConvexity,
	"attrib_annotation-sys-attrib":                                                                AttribSysAnnotationAttrib,
	"stitch_hint-sys-attrib":                                                                      AttribSysStichHint,
	"tag-sys-attrib":                                                                              AttribSysTag,
	"vertedge-sys-attrib":                                                                         AttribSysVertedge,
	"tsl-attrib":                                                                                  AttribTsl,
	"id-tsl-attrib":                                                                               AttribTslId,
	"Begin-of-ACIS-History-Data":                                                                  BeginOfAcisHistoryData,
	"body":                                                                                        Body,
	"coedge":                                                                                      CoEdge,
	"tcoedge-coedge":                                                                              CoEdgeTolerance,
	"curve":                                                                                       Curve,
	"compcurv-curve":                                                                              CurveComp,
	"ellipse-curve":                                                                               CurveEllipse,
	"degenerate_curve-curve":                                                                      CurveDegenerate,
	"intcurve-curve":                                                                              CurveInt,
	"intcurve-intcurve-curve":                                                                     CurveIntInt,
	"pcurve":                                                                                      CurveP,
	"straight-curve":                                                                              CurveStraight,
	"delta_state":                                                                                 DeltaState,
	"edge":                                                                                        Edge,
	"tedge-edge":                                                                                  EdgeTolerance,
	"End-of-ACIS-data":                                                                            EndOfAcisData,
	"End-of-ACIS-History-Section":                                                                 EndOfAcisHistorySection,
	"eye_refinement":                                                                              EyeRefinement,
	"face":                                                                                        Face,
	"loop":                                                                                        Loop,
	"lump":                                                                                        Lump,
	"point":                                                                                       Point,
	"refinement":                                                                                  Refinement,
	"shell":                                                                                       Shell,
	"subshell":                                                                                    SubShell,
	"surface":                                                                                     Surface,
	"cone-surface":                                                                                SurfaceCone,
	"meshsurf-surface":                                                                            SurfaceMesh,
	"plane-surface":                                                                               SurfacePlane,
	"sphere-surface":                                                                              SurfaceSphere,
	"spline-surface":                                                                              SurfaceSpline,
	"torus-surface":                                                                               SurfaceTorus,
	"transform":                                                                                   Transform,
	"vertex":                                                                                      Vertex,
	"vertex_template":                                                                             VertexTemplate,
	"tvertex-vertex":                                                                              VertexTolerance,
	"wcs":                                                                                         Wcs,
	"wire":                                                                                        Wire,
}
