# -*- coding: utf-8 -*-

'''
Acis.py:
Collection of classes necessary to read and analyse Standard ACIS Text (*.sat) files.
'''

import traceback, FreeCAD, math, Part
from importerUtils import LOG, logMessage, logWarning, logError, isEqual, getUInt8, getUInt16, getSInt32, getFloat64, getFloat64A, getUInt32, ENCODING_FS
from FreeCAD       import Vector as VEC, Rotation as ROT, Placement as PLC, Matrix as MAT
from math          import pi

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

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

CLOSURE     = {0: 'open', 1: 'closed', 2: 'periodic'}
SINGULARITY = {0: 'full', 1: 'v',      2: 'none'}

scale = 1.0

subtypeTable = {}

references = {}

def addSubtypeNode(subtype, node):
	global subtypeTable
	try:
		refs = subtypeTable[subtype]
	except KeyError:
		refs = []
		subtypeTable[subtype] = refs
	refs.append(node)

def addNode(node):
	if (node.entity is not None):
		subtype = node.getType()
		i = subtype.rfind('-')
		if (i > 0):
			subtype = subtype[0:i]
		addSubtypeNode(subtype, node)

def getSubtypeNode(subtype, index):
	global subtypeTable
	try:
		refs = subtypeTable[subtype]
		return refs[index]
	except:
		return None

def clearEntities():
	global subtypeTable
	subtypeTable.clear()

def setScale(value):
	global scale
	scale = value
	return scale

def getScale():
	global scale
	return scale

def createNode(entity, version):
	global references

	try:
		if (entity.index < 0):
			return
		node = references[entity.index]
		# this entity is overwriting a previus entity with the same index->
		logWarning("    Found 2nd '-%d %s' - IGNORED!" %(entity.index, entity.name))
		entity.node = node
	except:
		try:
			node = TYPES[entity.name]()
		except:
			#try to find the propriate base class
			types = entity.name.split('-')
			i = 1
			node = Entity()
			t = 'Entity'
			while (i<len(types)):
				try:
					t = "-".join(types[i:])
					node = TYPES[t]()
					i = len(types)
				except Exception as e:
					i += 1
			logError("TypeError: Can't find class for '%s' - using '%s'!" %(entity.name, t))

		if (entity.index >= 0):
			references[entity.index] = node
		if (hasattr(node, 'set')):
			node.set(entity, version)

def getRefNode(entity, index, name):
	chunk = entity.chunks[index]
	try:
		ref = chunk.val.entity
	except Exception as e:
		logError("ERROR: Chunk at index=%d, name='%s' is not a reference (%s)! %s" %(index, name, e, entity))
		return None, index + 1
	if (ref is not None) and (name is not None) and (ref.name.endswith(name) == False):
		raise Exception("Excpeced %s but found %s" %(name, ref.name))
	return ref, index + 1

def getValue(chunks, index):
	val = chunks[index].val
	return val, index + 1

def getInteger(chunks, index):
	val, i = getValue(chunks, index)
	return int(val), i

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

def checkClosure(chunks, index):
	closure, i = getEnumByValue(chunks, index, CLOSURE)
	closure = closure.lower()
	return closure, i

def getSingularity(chunks, index, version):
	if (version > 4):
		return getEnumByValue(chunks, index, SINGULARITY)
	return 'full', index

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

def getUnknownFT(chunks, index, version):
	i = index
	val = 'F'
	if (version > 7.0):
		val, i = getValue(chunks, i)
		if (val == 'T'):
			i += 7 # skip ???
	return val, i

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
	# DIMENSION      = (nullbs|nurbs [:NUMBER:]|nubs [:NUMBER:]|summary [:NUMBER: Version > 17]|cylinder)
	val, i  = getValue(chunks, index)
	if (val == 'nullbs'):
		return val, 0, i
	if ((val == 'nurbs') or (val == 'nubs')):
		number, i = getInteger(chunks, i)
		return val, number, i
	raise Exception("Unknown DIMENSION '%s'" %(val))

def getDimensionSurface(chunks, index):
	# DIMENSION      = (nullbs|nurbs [:NUMBER:]|nubs [:NUMBER:]|summary [:NUMBER:])
	val, i = getValue(chunks, index)
	if (val == 'nullbs'):
		return val, None, i
	if ((val == 'nurbs') or (val == 'nubs') or (val == 'summary')):
		knotsU, i = getInteger(chunks, i)
		knotsV, i = getInteger(chunks, i)
		return val, knotsU, knotsV, i
	raise Exception("Unknown DIMENSION '%s'" %(val))

def getClosureCurve(chunks, index):
	# CLOSURE = (open=0|closed=1|periodic=2)
	closure, i = checkClosure(chunks, index)
	if ((closure == 'open') or (closure == 'closed') or (closure == 'periodic')):
		knots, i = getInteger(chunks, i)
		return closure, knots, i
	raise Exception("Unknown closure '%s'!" %(closure))

def getClosureSurface(chunks, index):
	# Syntax: [:CLOSURE:] [:CLOSURE:] [:FULL:] [:FULL:] [:NUMBER:] [:NUMBER:]
	# CLOSURE = (open=0|closed=1|periodic=2)
	# FULL   = (full=0|none=1)

	closureU, i = checkClosure(chunks, index)
	if ((closureU == 'both') or (closureU == 'u') or (closureU == 'v')):
		closureU, i = checkClosure(chunks, i)
	if ((closureU == 'open') or (closureU == 'closed') or (closureU == 'periodic')):
		# open none none 2 2
		closureV, i = checkClosure(chunks, i)
		singularityU, i = getSingularity(chunks, i, 7.0)
		singularityV, i = getSingularity(chunks, i, 7.0)
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

def readPoints2DList(nubs, count, chunks, index, version):
	nubs.uKnots, nubs.uMults, i = readKnotsMults(count, chunks, index)
	us = sum(nubs.uMults) - (nubs.uDegree - 1)
	nubs.poles   = [None for r in range(0, us)]
	nubs.weights = [1 for r in range(0, us)] if (nubs.rational) else None

	for u in range(0, us):
		p, i  = getFloats(chunks, i, 2)
		nubs.poles[u] = VEC(p[0], p[1], 0) * getScale()
		if (nubs.rational): nubs.weights[u], i = getFloat(chunks, i)

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

def readBlend(chunks, index, version):
	nubs, i = readBS2Curve(chunks, index, version)
	if (nubs is not None):
		nubs.sense, i = getSense(chunks, i)
		nubs.factor, i = getFloat(chunks, i)
		return nubs, i
	return None, index

def readUnknown(chunks, index, version):
	val, i = getValue(chunks, index)
	if (val == 'compcurv'):
		obj = CurveComp()
	elif (val == 'cylinder'):
		return None, i
	elif (val == 'ellipse'):
		obj = CurveEllipse()
	elif (val == 'intcurve'):
		obj = CurveInt()
	elif (val == 'intcurve-intcurve'):
		obj = CurveIntInt()
	elif (val == 'pcurve'):
		obj = CurveP()
	elif (val == 'straight'):
		obj = CurveStraight()
	if (val == 'cone'):
		obj = SurfaceCone()
	elif (val == 'mesh'):
		obj = SurfaceMesh()
	elif (val == 'plane'):
		obj = SurfacePlane()
	elif (val == 'sphere'):
		obj = SurfaceSphere()
	elif (val == 'spline'):
		obj = SurfaceSpline()
	elif (val == 'torus'):
		obj = SurfaceTorus()
	elif ((val == 'nubs') or (val =='nurbs')):
		curve, i = readBS2Curve(chunks, index, version)
		curve.sense, i = getSense(chunks, i)
		curve.tolerance, i = getFloat(chunks, i)
		return curve, i
	elif (val == 'nullbs'):
		return None, i
	elif (val == 'null_surface'):
		return None, i
	obj.version = version
	addSubtypeNode(val, obj)
	i = obj.setSubtype(chunks, i)
	return obj, i

def readLaw(chunks, index, version):
	n, i = getText(chunks, index)
	if (n == 'TRANS'):
		v = Transform()
		i = v.setBulk(chunks, i)
	elif (n == 'EDGE'):
		c, i = readCurve(chunks, i, version)
		f, i = getFloats(chunks, i, 2)
		v = (c, f)
	elif (n == 'null_law'):
		v = None
	else:
		v = None

	return (n, v), i
def readCurve(chunks, index, version):
	val, i = getValue(chunks, index)
	if (val == 'compcurv'):
		curve = CurveComp()
	elif (val == 'ellipse'):
		curve = CurveEllipse()
	elif (val == 'degenerate_curve'):
		curve = CurveDegenerate()
	elif (val == 'intcurve'):
		curve = CurveInt()
	elif (val == 'intcurve-intcurve'):
		curve = CurveIntInt()
	elif (val == 'pcurve'):
		curve = CurveP()
	elif (val == 'straight'):
		curve = CurveStraight()
	elif (val == 'null_curve'):
		return None, i
	else:
		raise Exception("Unknown curve-type '%s'!" % (val))
	curve.version = version
	addSubtypeNode(val, curve)
	i = curve.setSubtype(chunks, i)
	return curve, i

def readSurface(chunks, index, version):
	chunk = chunks[index]
	i = index + 1
	subtype = chunk.val
	tag = chunk.tag
	if ((tag == 0x07) or (tag == 0x0D)):
		if (subtype == 'cone'):
			surface = SurfaceCone()
		elif (subtype == 'mesh'):
			surface = SurfaceMesh()
		elif (subtype == 'plane'):
			surface = SurfacePlane()
		elif (subtype == 'sphere'):
			surface = SurfaceSphere()
		elif (subtype == 'spline'):
			surface = SurfaceSpline()
		elif (subtype == 'torus'):
			surface = SurfaceTorus()
		elif (subtype == 'null_surface'):
			return None, i
		else:
			raise Exception("Unknown surface-type '%s'!" % (subtype))
		surface.version = version
		addSubtypeNode(subtype, surface)
		i = surface.setSubtype(chunks, i)
		return surface, i
	elif (tag == 0x06):
		a, i = getFloats(chunks, index, 5)
		return None, i
	elif ((tag == 0x13) or (tag == 0x14)):
		a, i = getFloats(chunks, i, 2)
		return None, i
	else:
		pass

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

def createBSplinesCurve(nubs):
	number_of_poles = len(nubs.poles)
	if (number_of_poles == 2): # if there are only two poles we can simply draw a line
		return createLine(nubs.poles[0], nubs.poles[1])

	sum_of_mults    = sum(nubs.uMults)
	degree          = nubs.uDegree
	periodic        = nubs.uPeriodic
#	if (periodic):
#		# For a periodic curve the relation is:
#		# number_of_knot_values = number_of_poles - multiplicity[1] + 2 * (degree + 1)
#		assert (sum_of_mults == number_of_poles), "number of poles (%d) <> sum(mults) (%d)" %(number_of_poles, sum_of_mults)
#	else:
#		# For a non-periodic curve the relation is:
#		# number_of_knot_values = number_of_poles + degree + 1
#		assert (sum_of_mults == (number_of_poles + degree + 1)), "number of poles<>sum(mults)-degree-1: %d != %d - %d + 1" %(number_of_poles, sum_of_mults, degree)

	bsc = Part.BSplineCurve()
	if (nubs.rational):
		bsc.buildFromPolesMultsKnots(     \
			poles         = nubs.poles,   \
			mults         = nubs.uMults,  \
			knots         = nubs.uKnots,  \
			periodic      = periodic,     \
			degree        = degree,       \
			weights       = nubs.weights, \
			CheckRational = nubs.rational
		)
	else:
		bsc.buildFromPolesMultsKnots(     \
			poles         = nubs.poles,   \
			mults         = nubs.uMults,  \
			knots         = nubs.uKnots,  \
			periodic      = periodic,     \
			degree        = degree,       \
			CheckRational = nubs.rational
		)
	return bsc.toShape()

def createBSplinesSurface(nubs):
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

def createHelix(helix):
	return None

def readBS2Curve(chunks, index, version):
	nbs, dgr, i = getDimensionCurve(chunks, index)
	if (nbs == 'nullbs'):
		return None, i
	if ((nbs == 'nubs') or (nbs == 'nurbs')):
		closure, knots, i = getClosureCurve(chunks, i)
		nubs = BS3_Curve(nbs == 'nurbs', closure == 'periodic', dgr)
		i = readPoints2DList(nubs, knots, chunks, i, version)
		return nubs, i
	return None, index

def readBS3Curve(chunks, index):
	nbs, dgr, i = getDimensionCurve(chunks, index)
	if (nbs == 'nullbs'):
		return None, i
	if ((nbs == 'nubs') or (nbs == 'nurbs')):
		closure, knots, i = getClosureCurve(chunks, i)
		nubs = BS3_Curve(nbs == 'nurbs', closure == 'periodic', dgr)
		i = readPoints3DList(nubs, knots, chunks, i)
		return nubs, i
	return None, index

def readBS3Surface(chunks, index):
	nbs, degreeU, degreeV, i = getDimensionSurface(chunks, index)
	if (nbs == 'nullbs'):
		return None, i
	if ((nbs == 'nurbs') or (nbs == 'nubs')):
		closureU, closureV, singularityU, singularityV, knotsU, knotsV, i = getClosureSurface(chunks, i)
		nubs = BS3_Surface(nbs == 'nurbs', closureU == 'periodic', closureV == 'periodic', degreeU, degreeV)
		i = readPoints3DMap(nubs, knotsU, knotsV, chunks, i)
	return nubs, i

class VBL():
	def __init__(self):
		self.n  = ''
		self.r  = None
		self.v  = CENTER
		self.a  = 0x0B
		self.b  = 0x0B
		self.c  = 0.0
		self.s  = None
		self.p  = None
		self.d  = None
		self.e  = 0.0
		self.c1 = None
		self.c2 = None
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
		self.a          = CENTER
		self.alpha      = 0.0
		self.b          = DIR_Z
class Range():
	def __init__(self, type, limit, scale = 1.0):
		self.type  = type
		self.limit = limit
		self.scale = scale
	def __str__(self): return 'I' if (self.type == 'I') else "F %g" %(self.getLimit())
	def getLimit(self): return self.limit if (self.type == 'I') else self.limit * self.scale
class Intervall():
	def __init__(self, upper, lower):
		self.lower = upper
		self.upper = lower
	def __str__(self): return "%s %s" %(self.lower, self.upper)
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
		self.index   = -1
		self._attrib = None # Attrib
		self.history = -1  # from Version 6.0 on
		self.entity  = None
		self.done = False
		self.version = 1.0
	def set(self, entity, version):
		self.version = version
		if (not self.done):
			# prevent endless loops
			self.done = True
			entity.node = self
			self.entity = entity
			addNode(self)

			try:
				references[entity.index] = self
				self._attrib, i = getRefNode(entity, 0, None)
				if (version > 6):
					i += 1 # skip history!
			except Exception as e:
				logError('>E: ' + traceback.format_exc())
		else:
			i = 2 if (version > 6) else 1 # skip history!
		return i
	def getIndex(self):  return -1   if (self.entity is None)  else self.entity.index
	def getType(self):   return -1   if (self.entity is None)  else self.entity.name
	def getAttrib(self): return None if (self._attrib is None) else self._attrib.node
	def __str__(self):   return "%s" % (self.entity)

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
	def set(self, entity, version):
		i = super(Transform, self).set(entity, version)
		i = self.setBulk(entity.chunks, i)
		return i
	def getPlacement(self):
		return PLC(self.matrix)
# abstract super class for all topologies
class Topology(Entity):
	def __init__(self): super(Topology, self).__init__()
	def set(self, entity, version):
		i = super(Topology, self).set(entity, version)
		if (version > 10.0):
			i += 1 # skip ???
		if (version > 6.0):
			i += 1 # skip ???
		return i
class Body(Topology):
	def __init__(self):
		super(Body, self).__init__()
		self._lump      = None # Pointer to LUMP object
		self._wire      = None # Pointer to Wire object
		self._transform = None # Pointer to Transform object
	def set(self, entity, version):
		i = super(Body, self).set(entity, version)
		self._lump, i      = getRefNode(entity, i, 'lump')
		self._wire, i      = getRefNode(entity, i, 'wire')
		self._transform, i = getRefNode(entity, i, 'transform')
		self.unknown1, i   = getUnknownFT(entity.chunks, i, version)
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
	def set(self, entity, version):
		i = super(Lump, self).set(entity, version)
		self._next, i    = getRefNode(entity, i, 'lump')
		self._shell, i   = getRefNode(entity, i, 'shell')
		self._owner, i   = getRefNode(entity, i, 'body')
		self.unknown1, i = getUnknownFT(entity.chunks, i, version)
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
	def set(self, entity, version):
		i = super(Shell, self).set(entity, version)
		self._next, i  = getRefNode(entity, i, 'shell')
		self._shell, i = getRefNode(entity, i, None)
		self._face, i  = getRefNode(entity, i, 'face')
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
	def set(self, entity, version):
		i = super(SubShell, self).set(entity, version)
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
	def set(self, entity, version):
		i = super(Face, self).set(entity, version)
		self._next, i                   = getRefNode(entity, i, 'face')
		self._loop, i                   = getRefNode(entity, i, 'loop')
		self._parent, i                 = getRefNode(entity, i, None)
		self.unknown, i                 = getRefNode(entity, i, None)
		self._surface, i                = getRefNode(entity, i, 'surface')
		self.sense, i                   = getSense(entity.chunks, i)
		self.sides, self.containment, i = getSides(entity.chunks, i)
		if (version > 9.0):
			self.unknown2, i = getUnknownFT(entity.chunks, i, version)
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
		if (hasattr(s, "type")):
			logWarning("    ... Don't know how to build surface '%s::%s' - only edges displayed!" %(s.getType(), s.type))
		else:
			logWarning("    ... Don't know how to build surface '%s' - only edges displayed!" %(s.getType()))
		self.showEdges(wires)
		return []

class Loop(Topology):
	def __init__(self):
		super(Loop, self).__init__()
		self._next   = None # The next loop
		self._coedge = None # The first coedge in the loop
		self._face   = None # The first coedge in the face
	def set(self, entity, version):
		i = super(Loop, self).set(entity, version)
		self._next, i   = getRefNode(entity, i, 'loop')
		self._coedge, i = getRefNode(entity, i, 'coedge')
		self._face, i   = getRefNode(entity, i, 'face')
		self.unknown, i = getUnknownFT(entity.chunks, i, version)
		if (version > 9.0):
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
	def set(self, entity, version):
		i = super(Edge, self).set(entity, version)
		self._start, i  = getRefNode(entity, i, 'vertex')
		if (version > 4.0):
			i += 1 # skip double
		self._end, i    = getRefNode(entity, i, 'vertex')
		if (version > 4.0):
			i += 1 # skip double
		self._parent, i = getRefNode(entity, i, 'coedge')
		self._curve, i  = getRefNode(entity, i, 'curve')
		self.sense, i  = getSense(entity.chunks, i)
		if (version > 5.0):
			self.text, i = getText(entity.chunks, i)
		self.unknown, i = getUnknownFT(entity.chunks, i, version)
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
	def set(self, entity, version):
		i = super(EdgeTolerance, self).set(entity, version)
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
	def set(self, entity, version):
		i = i = super(CoEdge, self).set(entity, version)
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
					c.build(e.getStart(), e.getEnd())
				if (c.shape is not None):
					self.shape = c.shape.copy()
					self.shape.Orientation = 'Reversed' if (self.sense == 'reversed') else 'Forward'
		return self.shape
class CoEdgeTolerance(CoEdge):
	def __init__(self):
		super(CoEdgeTolerance, self).__init__()
		self.tStart = 0.0
		self.tEnd = 0.0
	def set(self, entity, version):
		i = super(CoEdgeTolerance, self).set(entity, version)
		self.tStart, i  = getFloat(entity.chunks, i)
		self.tEnd, i    = getFloat(entity.chunks, i)
		return i
class Vertex(Topology):
	def __init__(self):
		super(Vertex, self).__init__()
		self._parent = None # One of the vertex' owners
		self._point = None  # The vertex' location
		self.count = -1    # Number of edges using this vertex
	def set(self, entity, version):
		i = super(Vertex, self).set(entity, version)
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
	def set(self, entity, version):
		i = super(VertexTolerance, self).set(entity, version)
		self.tolerance, i = getFloat(entity.chunks, i)
		return i
class Wire(Topology):
	def __init__(self):
		super(Wire, self).__init__()
		self._next = None
		self._coedge = None
		self._shell = None
		self.side = False
	def set(self, entity, version):
		i = super(Wire, self).set(entity, version)
		self._next, i   = getRefNode(entity, i, 'wire')
		self._coedge, i = getRefNode(entity, i, 'coedge')
		self._owner, i  = getRefNode(entity, i, None)
		self.unknown, i = getRefNode(entity, i, None)
		self.side, i    = getSide(entity.chunks, i)
		self.ft, i      = getUnknownFT(entity.chunks, i, version)
		return i
	def getNext(self):   return None if (self._next is None)   else self._next.node
	def getCoEdge(self): return None if (self._coedge is None) else self._coedge.node
	def getShell(self):  return None if (self._shell is None)  else self._shell.node
	def getOwner(self):  return None if (self._owner is None)  else self._owner.node
	def getCoEdges(self):
		coedges = []
		ce = self.getCoEdge()
		index = -1 if (ce is None) else ce.getIndex()
		while (ce is not None):
			coedges.append(ce)
			ce = ce.getNext()
			if ((ce is not None) and (ce.getIndex() == index)):
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
	def set(self, entity, version):
		i = super(Geometry, self).set(entity, version)
		if (version > 10.0):
			i += 1 # skip ???
		if (version > 6.0):
			i += 1 # skip ???
		return i
class Curve(Geometry):
	def __init__(self):
		super(Curve, self).__init__()
		self.shape = None
	def set(self, entity, version):
		i = super(Curve, self).set(entity, version)
		return i
	def build(self, start, end): # by default: return a line-segment!
		logWarning("    ... '%s' not yet supported - forced to straight-curve!" %(self.getType()))
		if (self.shape is None):
			# force everything else to straight line!
			self.shape = createLine(start, end)
		return self.shape
class CurveComp(Curve):    # compound courve "compcurv-curve"
	def __init__(self):
		super(CurveComp, self).__init__()
	def set(self, entity, version):
		i = super(CurveComp, self).set(entity, version)
		return i
class CurveDegenerate(Curve):    # degenerate courve "degenerate_curve"
	def __init__(self):
		super(CurveDegenerate, self).__init__()
	def setSubtype(self, chunks, index):
		self.center, i  = getLocation(chunks, index)
		self.range, i   = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		self.surface, i = readSurface(chunks, i, self.version)
		self.bs2, i   = readBS2Curve(chunks, i, self.version)
		self.a1, i = getValue(chunks, i)   # 0x0B
		self.a2, i = getInteger(chunks, i) # 213
		self.a3, i = getInteger(chunks, i) # 1
		self.a4, i = getInteger(chunks, i) # 1
		self.a5, i = getFloat(chunks, i)   # 0.0
		self.a6, i = getFloat(chunks, i)   # 1.0
		self.a7, i = getFloat(chunks, i)   # 0.0
		self.a8, i = getFloat(chunks, i)   # 0.0
		self.a9, i = getFloat(chunks, i)   # 0.0
		self.b1, i = getFloat(chunks, i)   # 0.0
		self.b2, i = getValue(chunks, i)   # 0x0B
		self.curve, i = readCurve(chunks, i, self.version)  # 'null_curve'
		self.b3, i = getInteger(chunks, i) # 0
		self.b4, i = getInteger(chunks, i) # -1
		self.b5, i = getFloat(chunks, i)   # 1.0
		self.b6, i = getInteger(chunks, i) # 1
		self.b7, i = getInteger(chunks, i) # 1
		return i
	def set(self, entity, version):
		i = super(CurveDegenerate, self).set(entity, version)
		return i
class CurveEllipse(Curve): # ellyptical curve "ellipse-curve"
	def __init__(self):
		super(CurveEllipse, self).__init__()
		self.center = CENTER
		self.normal = DIR_Z
		self.major  = DIR_X
		self.ratio  = 0.0
		self.range  = Intervall(Range('I', MIN_0), Range('I', MAX_2PI))
	def __str__(self):
		return "Curve-Ellipse: center=%s, dir=%s, major=%s, ratio=%g, range=%s" %(self.center, self.normal, self.major, self.ratio, self.range)
	def setSubtype(self, chunks, index):
		self.center, i = getLocation(chunks, index)
		self.normal, i = getVector(chunks, i)
		self.major, i  = getLocation(chunks, i)
		self.ratio, i  = getFloat(chunks, i)
		self.range, i  = getInterval(chunks, i, MIN_0, MAX_2PI, 1.0)
		return i
	def set(self, entity, version):
		i = super(CurveEllipse, self).set(entity, version)
		i = self.setSubtype(entity.chunks, i)
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
		self.data   = None  #
		self.range  = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
		self.points = []
		self.type   = ''
		self.curve  = None
	def __str__(self): return "-%d Curve-Int: type=%s, points=%s" %(self.getIndex(), self.type, len(self.points))
	def setCurve(self, chunks, index):
		self.singularity, i = getSingularity(chunks, index, self.version)
		if (self.singularity == 'full'):
			nubs, i = readBS3Curve(chunks, i)
			nubs.tolerance, i = getFloat(chunks, i)
			nubs.tolerance *= getScale()
			try:
				self.shape = createBSplinesCurve(nubs)
			except Exception as e:
				logError('>E: ' + traceback.format_exc())
		elif (self.singularity == 'none'):
			self.range, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			val, i= getValue(chunks, i)
			if (type(val) == float):
				self.tolerance = val
		elif (self.singularity == 'summary'):
			if (self.version > 17.0):
				i += 1
			arr, i  = getFloatArray(chunks, i)
			fac, i  = getFloat(chunks, i)
			clsr, i = checkClosure(chunks, i)
		elif (self.singularity == 'v'):
			arr, i = getFloatArray(chunks, i)
			f1, i = getFloat(chunks, i)
			f2, i = getFloat(chunks, i)
		else:
			raise Exception("Unknwon Surface-singularity '%s'" %(self.singularity))
		return i
	def setSurfaceCurve(self, chunks, index):
		i = self.setCurve(chunks, index)
		surface1, i = readSurface(chunks, i, self.version)
		surface2, i = readSurface(chunks, i, self.version)
		curve1, i   = readBS2Curve(chunks, i, self.version)
		if (self.version == 18.0):
			i += 2
		curve2, i   = readBS2Curve(chunks, i, self.version)
		if (self.version > 15.0):
			i += 2
		range2, i   = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		a1, i       = getFloatArray(chunks, i)
		a2, i       = getFloatArray(chunks, i)
		a3, i       = getFloatArray(chunks, i)
		return i
	def setBlend(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		txt, i      = getText(chunks, i)
		return i
	def setBlendSprng(self, chunks, index):
		i = self.setSurfaceCurve(chunks, index)
		txt, i      = getText(chunks, i)
		return i
	def setComp(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		a4, i       = getFloatArray(chunks, i)
		a5, i       = getFloatArray(chunks, i)
		if (inventor):
			i += 1
		c1, i = readCurve(chunks, i, self.version)
		c2, i = readCurve(chunks, i, self.version)
		c3, i = readCurve(chunks, i, self.version)
		return i
	def setDefm(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (inventor):
			x3, i = getFloat(chunks, i)
		bend, i = readCurve(chunks, i, self.version)
		return i
	def setExact(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (inventor):
			x3, i = getFloat(chunks, i)
		if (self.version > 15.0):
			i += 2
		unknown, i = getUnknownFT(chunks, i, self.version)
		range2, i  = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def setHelix(self, chunks, index):
		helix = Helix()
		helix.angleStart, i = getRange(chunks, index, MIN_0, 1.0)
		helix.angleEnd, i   = getRange(chunks, i, MAX_2PI, 1.0)
		helix.center, i     = getLocation(chunks, i)
		helix.rMajor, i     = getLocation(chunks, i)
		helix.rMinor, i     = getLocation(chunks, i)
		helix.a, i          = getLocation(chunks, i)
		helix.alpha, i      = getFloat(chunks, i)
		helix.b, i          = getLocation(chunks, i)
		surface1, i = readSurface(chunks, i, self.version)
		surface2, i = readSurface(chunks, i, self.version)
		curve1, i   = readBS2Curve(chunks, i, self.version)
		curve2, i   = readBS2Curve(chunks, i, self.version)
		self.helix = helix
		return i
	def setInt(self, chunks, index):
		i = self.setSurfaceCurve(chunks, index)
		x, i = getFloat(chunks, i)
		return i
	def setLaw(self, chunks, index, inventor):
		i = index
		i = self.setSurfaceCurve(chunks, index)
		laws = []
		if (inventor):
			n, i   = getInteger(chunks, i) # 0
		l, i  = readLaw(chunks, i, self.version)
		laws.append(l)
		subLaws = []
		laws.append(subLaws)
		n, i   = getInteger(chunks, i) # 0..n
		for cnt in range(0, n):
			l, i  = readLaw(chunks, i, self.version)
			subLaws .append(l)
		n, i   = getInteger(chunks, i) #4
		if (n == 0):
			return i
		subLaws = []
		laws.append(subLaws)
		while (True):
			l, i  = readLaw(chunks, i, self.version) # null_law
			subLaws.append(l)
			if (l[0] != 'null_law'):
				break
		subLaws = []
		laws.append(subLaws)
		while (i < len(chunks)):
			n, i   = getInteger(chunks, i) #0
			if (n == 0):
				l, i  = readLaw(chunks, i, self.version)
				subLaws.append(l)
			elif (n == 1):
				l, i  = readLaw(chunks, i, self.version)
				subLaws.append(l)
				break
			elif (n == 2):
				l, i  = readLaw(chunks, i, self.version)
				subLaws.append(l)
				l, i  = readLaw(chunks, i, self.version)
				subLaws.append(l)
				while (True):
					l, i  = readLaw(chunks, i, self.version)
					subLaws.append(l)
					if (l[0] != 'null_law'):
						break
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
		curve, i = readCurve(chunks, i, self.version)
		return i
	def setOffsetSurface(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (inventor):
			i += 1
		rngU, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		rngV, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		curve, i = readCurve(chunks, i, self.version)
		rng, i  = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		# x, y, z ???
		return i
	def setParameter(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index)
		if (self.version > 15.0):
			i += 1
		if (not inventor):
			if (self.version > 17.0):
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
		curve, i = readCurve(chunks, i, self.version)
		# 0x0A|0x0B ???
		return i
	def setRef(self, chunks, index):
		ref, i = getInteger(chunks, index)
		self.curve = getSubtypeNode('intcurve', ref)
		return i
	def setSpring(self, chunks, index, inventor):
		i = self.setCurve(chunks, index)
		surface1, i = readSurface(chunks, i, self.version)
		if (surface1 is None):
			rangeU, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
			rangeV, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		surface2, i = readSurface(chunks, i, self.version)
		curve1, i   = readBS2Curve(chunks, i, self.version)
		if (self.version == 18.0):
			i += 2
		curve2, i   = readBS2Curve(chunks, i, self.version)
		if (self.version > 15.0):
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
		# data syntax
		# DATA = ([:EXACTCUR:]|[:PARCUR:]|[:REF:]|[:PROJ_INT_CUR:]|[:SPRING_INT_CUR:]|[:SURFINTCUR:])
		# EXACTCUR       = exactcur (full)? [:DIMENSION:] [:CLOSURE:] [:NUMBER: count] ([:FLOAT:] [:NUMBER:]){count} ([:VECTOR:]){n}
		#                  [:FLOAT:] [:SURFACE:] [:SURFACE:] [:DIMENSION:] [:DIMENSION:] [:RANGE:] .*
		# PARCUR         = ([:DIMENSION:]) [:FLOAT:] [:CLOSURE:]

		# PROJ_INT_CUR   = proj_int_cur [:NUMBER:] (full|0)? [:DIMENSION:] [:CLOSURE:] [:NUMBER: count] ([:FLOAT:] [:NUMBER:]){count} ([:VECTOR:] [:FLOAT:]?/* dimension == nurbs */){n}
		# REF            = ref [:NUMBER:]
		# SPRING_INT_CUR = spring_int_cur [:NUMBER:] (full|0)? [:DIMENSION:] [:CLOSURE:] [:NUMBER: count] ([:FLOAT:] [:NUMBER:]){count} ([:VECTOR:] [:FLOAT:]?/* dimension == nurbs */){n}
		# SURFINTCUR     = surfintcur (full|0)? [:DIMENSION:] [:CLOSURE:] [:NUMBER: count] ([:FLOAT:] [:NUMBER:]){count} ([:VECTOR:] [:FLOAT:]?/* dimension == nurbs */){n}

		# VECTOR         = [:FLOAT:] [:FLOAT:] [:FLOAT:]
		self.type, i = getValue(chunks, index)

		if (self.type == 'bldcur'):           return self.setBlend(chunks, i, False)
		if (self.type == 'blend_int_cur'):    return self.setBlend(chunks, i + 1, True)
		if (self.type == 'blndsprngcur'):     return self.setBlendSprng(chunks, i)
		if (self.type == 'comp_int_cur'):     return self.setComp(chunks, i + 1, True)
		if (self.type == 'defm_int_cur'):     return self.setDefm(chunks, i + 1, True)
		if (self.type == 'exactcur'):         return self.setExact(chunks, i, False)
		if (self.type == 'exact_int_cur'):    return self.setExact(chunks, i + 1, True)
		if (self.type == 'helix_int_cur'):    return self.setHelix(chunks, i + 1)
		if (self.type == 'int_int_cur'):      return self.setInt(chunks, i + 1)
		if (self.type == 'lawintcur'):        return self.setLaw(chunks, i, False)
		if (self.type == 'law_int_cur'):      return self.setLaw(chunks, i + 1, True)
		if (self.type == 'offintcur'):        return self.setOff(chunks, i, False)
		if (self.type == 'off_int_cur'):      return self.setOff(chunks, i + 1, True)
		if (self.type == 'offsetintcur'):     return self.setOffset(chunks, i, False)
		if (self.type == 'offset_int_cur'):   return self.setOffset(chunks, i + 1, True)
		if (self.type == 'off_surf_int_cur'): return self.setOffsetSurface(chunks, i + 1, True)
		if (self.type == 'parcur'):           return self.setParameter(chunks, i, False)
		if (self.type == 'par_int_cur'):      return self.setParameter(chunks, i + 1, True)
		if (self.type == 'para_silh_int_cur'): return self.setParameterSilhouette(chunks, i + 1, True)
		if (self.type == 'proj_int_cur'):      return self.setProject(chunks, i + 1, True)
		if (self.type == 'ref'):               return self.setRef(chunks, i)
		if (self.type == 'spring_int_cur'):    return self.setSpring(chunks, i + 1, True)
		if (self.type == 'surfintcur'):        return self.setSurface(chunks, i)
		if (self.type == 'surf_int_cur'):      return self.setSurface(chunks, i + 1)
		logError("    Curve-Int: unknown subtype %s !" %(self.type))
		return self.setCurve(chunks, i)
	def setSubtype(self, chunks, index):
		self.sens, i  = getSense(chunks, index)
		block, i      = getBlock(chunks, i)
		self.setBulk(block, 0)
		self.range, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		if (self.shape is None):
			if (self.curve is not None):
				start = None
				end   = None
				self.shape = self.curve.build(start, end)
		return i
	def set(self, entity, version):
		i = super(CurveInt, self).set(entity, version)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self, start, end):
		if (self.shape is None):
			if (self.type == "exactcur"):
				self.shape = createPolygon(self.points)
			elif (self.type == "helix_int_cur"):
				self.shape = createHelix(self.helix)
			elif len(self.points) == 2:
				self.shape = createLine(self.points[0], self.points[1])
			elif (len(self.points) > 2):
				bsc = Part.BSplineCurve(self.points)
				self.shape = bsc.toShape()
#			else:
#				print self
			if (self.shape is not None):
				self.shape.Orientation = 'Reversed' if (self.sense == 'reversed') else 'Forward'
		return self.shape
class CurveIntInt(CurveInt):  # interpolated int-curve "intcurve-intcurve-curve"
	def __init__(self):
		super(CurveIntInt, self).__init__()
		self.sens = 'forward' # The IntCurve's reversal flag
		self.data = None  #
		self.range = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
		self.points = []
		self.type   = ''
		self.curve  = None
	def setLaw(self, chunks, index, inventor):
		i = self.setCurve(chunks, index)
		return i
	def setBulk(self, chunks, index):
		self.type, i = getValue(chunks, index)
		if (self.type == 'law_int_cur'):      return self.setLaw(chunks, i + 1, True)
		logError("    Curve-Int-Int: unknown subtype %s !" %(self.type))
		return self.setCurve(chunks, i)
class CurveP(Curve):       # projected curve "pcurve" for each point in CurveP: point3D = surface.value(u, v)
	'''An approximation to a curve lying on a surface, defined in terms of the surface’s u-v parameters.'''
	def __init__(self):
		super(CurveP, self).__init__()
		self.type    = -1    # The PCurve's type
		self.sense   = 'forward'
		self._curve  = None  # The PCurve's curve
		self.negated = False # The PCurve's negated flag
		self.space   = None  # Parmeter space vector
		self.points = []
	def setExpPar(self, chunks, index):
		# EXPPC = exppc ([:NUMBER:]?/*version > 22.0*/) [:DIMENSION:] [:NUMBER:dim] [:CLOSURE:] [:NUMBER: count] ([:FLOAT:] [:NUMBER:]){count} ([:VECTOR:]){n}
		#                  [:FLOAT:] ([:FLOAT:] [:SURFACE:]
		i = index if (self.version <= 22.0) else index + 1
		nubs, i = readBS2Curve(chunks, i, self.version)
		factor, i = getFloat(chunks, i)
		if (self.version > 15.0):
			i += 1
		surface, i = readSurface(chunks, i, self.version)
		if (surface is not None):
			s = surface.build()
		return i
	def setRef(self, chunks, index):
		ref, i = getInteger(chunks, index)
		curve = getSubtypeNode('pcurve', ref)
		if (curve is not None):
			self.shape = curve.build(None, None)
		return i
	def setBulk(self, chunks, index):
		# data syntax
		# DATA = ([:EXPPC:]|[:REF:])
		# REF            = ref [:NUMBER:]
		# VECTOR         = [:FLOAT:] [:FLOAT:]
		self.type, i = getValue(chunks, index)
		if (self.type == 'exp_par_cur'):
			return self.setExpPar(chunks, i)
		if (self.type == 'exppc'):
			return self.setExpPar(chunks, i)
		if (self.type == 'ref'):
			return self.setRef(chunks, i)
		logError("    PCurve: unknown subtype %s !" %(self.type))
		return self.setCurve(i)
	def set(self, entity, version):
		i = super(CurveP, self).set(entity, version)
		self.type, i = getInteger(entity.chunks, i)
		if (self.type == 0):
			self.sense, i = getSense(entity.chunks, i)
			block, i = getBlock(entity.chunks, i)
			self.setBulk(block, 0)
		else:
			self._curve, i = getRefNode(entity, i, 'curve')
		self.u, i = getFloat(entity.chunks, i)
		self.v, i = getFloat(entity.chunks, i)
		return i
	def build(self, start, end):
		if (self.shape is None):
			points = []
			bspline = Part.BSplineCurve()
			#bspline.interpolate(points)
			#self.shape = bspline.toShape()
		return self.shape
class CurveStraight(Curve):# straight curve "straight-curve"
	def __init__(self):
		super(CurveStraight, self).__init__()
		self.root  = CENTER
		self.dir   = CENTER
		self.range = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
	def __str__(self): return "Curve-Straight: root=%s, dir=%s, range=%s" %(self.root, self.dir, self.range)
	def setSubtype(self, chunks, index):
		self.root, i  = getLocation(chunks, index)
		self.dir, i   = getLocation(chunks, i)
		self.range, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def set(self, entity, version):
		i = super(CurveStraight, self).set(entity, version)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self, start, end):
		if (self.shape is None):
			self.shape = createLine(start, end)
		return self.shape
class Surface(Geometry):
	def __init__(self):
		super(Surface, self).__init__()
		self.shape = None
	def set(self, entity, version):
		i = super(Surface, self).set(entity, version)
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
	def setSubtype(self, chunks, index):
		self.center, i = getLocation(chunks, index)
		self.axis, i   = getVector(chunks, i)
		self.major, i  = getLocation(chunks, i)
		self.ratio, i  = getFloat(chunks, i)
		self.range, i  = getInterval(chunks, i, MIN_INF, MIN_INF, getScale())
		self.sine, i   = getFloat(chunks, i)
		self.cosine, i = getFloat(chunks, i)
		if (self.version >= ENTIY_VERSIONS.get('CONE_SCALING_VERSION')):
			self.scale, i = getLength(chunks, i)
		else:
			self.scale = getScale()
		self.sense, i  = getSense(chunks, i)
		self.urange, i = getInterval(chunks, i, MIN_0, MAX_2PI, 1.0)
		self.vrange, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def set(self, entity, version):
		i = super(SurfaceCone, self).set(entity, version)
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
	def set(self, entity, version):
		i = super(SurfaceMesh, self).set(entity, version)
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
	def setSubtype(self, chunks, index):
		self.root, i     = getLocation(chunks, index)
		self.normal, i   = getVector(chunks, i)
		self.uvorigin, i = getLocation(chunks, i)
		self.sensev, i   = getSensev(chunks, i)
		self.urange, i   = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		self.vrange, i   = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def set(self, entity, version):
		i = super(SurfacePlane, self).set(entity, version)
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
	def setSubtype(self, chunks, index):
		self.center, i   = getLocation(chunks, index)
		self.radius, i   = getLength(chunks, i)
		self.uvorigin, i = getVector(chunks, i)
		self.pole, i     = getVector(chunks, i)
		self.sensev, i   = getSensev(chunks, i)
		self.urange, i   = getInterval(chunks, i, MIN_0, MAX_2PI, 1.0)
		self.vrange, i   = getInterval(chunks, i, MIN_PI2, MAX_PI2, 1.0)
		return i
	def set(self, entity, version):
		i = super(SurfaceSphere, self).set(entity, version)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self):
		if (self.shape is None):
			sphere = Part.Sphere()
			rotateShape(sphere, self.pole)
			sphere.Center = self.center
			sphere.Radius = self.radius
			self.shape = sphere.toShape()
		return self.shape
class SurfaceSpline(Surface):
	def __init__(self):
		super(SurfaceSpline, self).__init__()
		self.data = None # The spline's data
		self.points = []
	def setSurface(self, chunks, index, inventor, withUV = True):
		self.singularity, i = getSingularity(chunks, index, self.version)
		if (self.singularity == 'full'):
			nubs, i = readBS3Surface(chunks, i)
			nubs.toleranceU, i = getFloat(chunks, i)
			nubs.toleranceV, i = getFloat(chunks, i)
			a1, i = getFloatArray(chunks, i)
			a2, i = getFloatArray(chunks, i)
			a3, i = getFloatArray(chunks, i)
			a4, i = getFloatArray(chunks, i)
			a5, i = getFloatArray(chunks, i)
			if (inventor):
				i += 1
			if (withUV):
				nubs.rangeU, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
				nubs.rangeV, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			try:
				self.shape = createBSplinesSurface(nubs)
			except Exception as e:
				logWarning('>E: %s' %(e))
		elif (self.singularity == 'none'):
			self.rangeU = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			self.rangeV = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			# OPEN OPEN SINGULAR_BOTH NON_SINGULAR
		return i
	def setSubSurface(self, chunks, index):
		surface, i = readSurface(chunks, index, self.version)
		if (surface is not None):
			self.shape = surface.build()
		return i
	def setBlendSupply(self, chunks, index):
		name, i = getValue(chunks, index)
		i = self.setSubSurface(chunks, i)
		return i
	def setBlendSupport(self, chunks, index):
		name, i = getValue(chunks, index)
		i = self.setSubSurface(chunks, i)
		return i
	def setClLoft(self, chunks, index, inventor):
		i = self.setSurface(chunks, index, inventor, False)
		return i
	def setCylinder(self, chunks, index):
		curve, i = readCurve(chunks, index, self.version)
		return i
	def setDefm(self, chunks, index):
		i = self.setSubSurface(chunks, index)
		return i
	def setExact(self, chunks, index, inventor):
		i = self.setSurface(chunks, index, inventor)
		# number (int)
		return i
	def setG2Blend(self, chunks, index):
		t1, i = getValue(chunks, index)
		while (type(t1) != str):
			t1, i = getValue(chunks, i)
		i = self.setSubSurface(chunks, i)
		c1, i = readCurve(chunks, i, self.version)
		c2, i = readBS2Curve(chunks, i, self.version)
		v1, i = getVector(chunks, i)
		c3, i = readBS2Curve(chunks, i, self.version)
		n1, i = getInteger(chunks, i)
		if (n1 == 0):
			if (type(chunks[i].val) != str):
				a0, i = getFloats(chunks, i, 0)
		elif (n1 == 2):
			j = 0
			while (type(chunks[i + j].val) == float):
				j += 1
			a0, i = getFloats(chunks, i, j)
		else:
			pass
		c4, i = readBS2Curve(chunks, i, self.version)
		t2, i = getValue(chunks, i)
		s1, i = readSurface(chunks, i, self.version)
		c5, i = readCurve(chunks, i, self.version)
		c6, i = readBS2Curve(chunks, i, self.version)
		v2, i = getVector(chunks, i)
		c7, i = readBS2Curve(chunks, i, self.version)
		f2, i = getInteger(chunks, i)
		c4, i = readBS2Curve(chunks, i, self.version)
		c5, i = readCurve(chunks, i, self.version)
		a1, i = getFloats(chunks, i, 3)
		rangeU, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		rangeV, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		a2, i = getFloats(chunks, i, 5)
		s1, i = readBS3Surface(chunks, i)
		f2, i = getFloat(chunks, i)
		a1, i	= getFloatArray(chunks, i)
		a2, i	= getFloatArray(chunks, i)
		a3, i	= getFloatArray(chunks, i)
		a4, i	= getFloatArray(chunks, i)
		a5, i	= getFloatArray(chunks, i)
		a6, i	= getFloatArray(chunks, i)
		return i
	def setHelixCircle(self, chunks, index):
		angle, i  = getInterval(chunks, index, MIN_PI, MAX_PI, 1.0)
		dime1, i  = getInterval(chunks, i, -MAX_LEN, MAX_LEN, getScale())
		length, i = getLength(chunks, i)
		dime1, i  = getInterval(chunks, i, -MAX_LEN, MAX_LEN, getScale())
		x1, i     = getLocation(chunks, i)
		x2, i     = getLocation(chunks, i)
		x3, i     = getLocation(chunks, i)
		x4, i     = getLocation(chunks, i)
		fac1, i   = getFloat(chunks, i)
		x5, i     = getVector(chunks, i)
		s1, i     = readSurface(chunks, i, self.version)
		s2, i     = readSurface(chunks, i, self.version)
		c1, i     = readBS2Curve(chunks, i, self.version)
		c2, i     = readBS2Curve(chunks, i, self.version)
		fac2, i   = getFloat(chunks, i)
		return i
	def setHelixLine(self, chunks, index):
		angle, i  = getInterval(chunks, index, MIN_PI, MAX_PI, 1.0)
		dime1, i  = getInterval(chunks, i, -MAX_LEN, MAX_LEN, getScale())
		dime2, i  = getInterval(chunks, i, -MAX_LEN, MAX_LEN, getScale())
		x1, i     = getLocation(chunks, i)
		x2, i     = getLocation(chunks, i)
		x3, i     = getLocation(chunks, i)
		x4, i     = getLocation(chunks, i)
		fac1, i   = getFloat(chunks, i)
		x5, i     = getVector(chunks, i)
		s1, i     = readSurface(chunks, i, self.version)
		s2, i     = readSurface(chunks, i, self.version)
		c1, i     = readBS2Curve(chunks, i, self.version)
		c2, i     = readBS2Curve(chunks, i, self.version)
		x6, i     = getVector(chunks, i)
		return i
	def setLoft(self, chunks, index):
		a, i = getInteger(chunks, index)
		b, i = getFloat(chunks, i)
		c, i = getInteger(chunks, i)
		d, i = getInteger(chunks, i)
		curve, i = readCurve(chunks, i, self.version)
		if (isinstance(curve, CurveDegenerate)):
			return i
		s1, i = readSurface(chunks, i, self.version)
		c1, i = readBS2Curve(chunks, i, self.version)
		return i
	def setNet(self, chunks, index):
		a, i = getInteger(chunks, index)
		b, i = getFloat(chunks, i)
		c, i = getInteger(chunks, i)
		d, i = getInteger(chunks, i)
		curve, i = readCurve(chunks, i, self.version)
		s1, i = readSurface(chunks, i, self.version)
		c1, i = readBS2Curve(chunks, i, self.version)
		return i
	def setOffset(self, chunks, index, inventor):
		surface, i = readSurface(chunks, index, self.version)
		f1, i = getFloat(chunks, i)
		senseU, i = getSense(chunks, i)
		senseV, i = getSense(chunks, i)
		if (inventor):
			e3, i = getValue(chunks, i) # 0x0B
			if ((chunks[i].tag == 0x0A) or (chunks[i].tag == 0x0B)): # 0x0B
				i += 1
		singularity, i = getSingularity(chunks, i, self.version)
		if (singularity == 'full'):
			c1, i = readBS3Surface(chunks, i)
			f3, i = getFloat(chunks, i)
		elif (singularity == 'none'):
			rngU, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
			rngV, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
			closureU, i = checkClosure(chunks, i)
			closureV, i = checkClosure(chunks, i)
			singularityU, i = getSingularity(chunks, i, self.version)
			singularityV, i = getSingularity(chunks, i, self.version)
		elif (singularity == 'v'):
			a11, i = getFloatArray(chunks, i)
			a12, i = getFloatArray(chunks, i)
			f, i = getFloat(chunks, i)
			closureU, i = checkClosure(chunks, i)
			closureV, i = checkClosure(chunks, i)
			singularityU, i = getSingularity(chunks, i, self.version)
			singularityV, i = getSingularity(chunks, i, self.version)
		else:
			return i
		a1, i  = getFloatArray(chunks, i)
		a2, i  = getFloatArray(chunks, i)
		a3, i  = getFloatArray(chunks, i)
		a4, i  = getFloatArray(chunks, i)
		a5, i  = getFloatArray(chunks, i)
		a6, i  = getFloatArray(chunks, i)
		if (inventor):
			i += 1
		return i
	def setOrtho(self, chunks, index, inventor):
		surface, i = readSurface(chunks, index, self.version)
		curve, i = readCurve(chunks, i, self.version)
		p1, i = readBS2Curve(chunks, i, self.version)
		i += 1 # float=1.0
		singularity, i = getSingularity(chunks, i, self.version)
		if (singularity == 'full'):
			p2, i = readBS3Surface(chunks, i)
			v, i = getPoint(chunks, i)
			a, i = getFloatArray(chunks, i)
			# float, float, float, 'F'
		else:
			a1, i = getFloatArray(chunks, i)
			a2, i = getFloatArray(chunks, i)
			a3, i = getFloats(chunks, i, 7)
			a4, i = getFloatArray(chunks, i)
			a5, i = getFloats(chunks, i, 2)
			# int, 0x0B, 0x0B
		return i
	def setRbBlend(self, chunks, index):
		name, i = getText(chunks, index)
		i = self.setSubSurface(chunks, i)
		return i
	def setRotation(self, chunks, index, inventor):
		curve, i = readCurve(chunks, index, self.version)
		loc, i   = getLocation(chunks, i)
		dir, i   = getVector(chunks, i)
		if (inventor):
			n, i = getInteger(chunks, i)
			if (n > 0):
				chunks[i].val = 'none'
		singularity, dummy = getValue(chunks, i)
		if (singularity == 'none'):
			rangeU, i    = getInterval(chunks, dummy, MIN_0, MIN_PI2, 1.0)
			rangeV, i    = getInterval(chunks, i, MIN_0, MIN_PI, 1.0)
			closure1, i  = checkClosure(chunks, i)
			closure2, i  = checkClosure(chunks, i)
			singular1, i = getValue(chunks, i)
			singular2, i = getValue(chunks, i)
		else:
			if (singularity == 'full'):
				i = dummy
			c1, i  = readBS3Surface(chunks, i)
			fac, i = getFloat(chunks, i)
		a1, i  = getFloatArray(chunks, i)
		a2, i  = getFloatArray(chunks, i)
		a3, i  = getFloatArray(chunks, i)
		a4, i  = getFloatArray(chunks, i)
		a5, i  = getFloatArray(chunks, i)
		a6, i  = getFloatArray(chunks, i)
		return i
	def setSkin(self, chunks, index, asm):
		bool, i = getSurfBool(chunks, index)
		norm, i = getSurfNorm(chunks, i)
		dir, i  = getSurfDir(chunks, i)
		num, i  = getInteger(chunks, i)
		a1, i  = getInteger(chunks, i)
		a2, i  = getInteger(chunks, i)
		a3, i  = getInteger(chunks, i)
		a4, i  = getInteger(chunks, i)
		a5, i  = getInteger(chunks, i)
		if (asm):
			 i += 2
		curve, i = readCurve(chunks, i, self.version)
		return i
	def setSum(self, chunks, index):
		curve, i = readCurve(chunks, index, self.version)
		return i
	def setSweep(self, chunks, index, inventor):
		i = index
		if (self.version > 16.0): # ??? correct ???
			txt, i = getText(chunks, i)
		tU, i = getSurfSweep(chunks, i)
		if (inventor):
			a, i = getFloat(chunks, i)
		c1, i = readCurve(chunks, i, self.version)
		if (inventor):
			rangeU, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
			a, i = getValue(chunks, i)
			v1, i = getVector(chunks, i)
			v2, i = getVector(chunks, i)
			v3, i = getVector(chunks, i)
			v4, i = getVector(chunks, i)
			if (a == '0x0A'):
				v5, i = getVector(chunks, i)
				v6, i = getVector(chunks, i)
			b, i = getValue(chunks, i)
			c, i = getValue(chunks, i)
		else:
			c2, i = readCurve(chunks, i, self.version)
		return i
	def setSweepSpline(self, chunks, index):
		type, i = getSurfSweep(chunks, index)
		prof, i = readCurve(chunks, i, self.version)
		path, i = readCurve(chunks, i, self.version)
#		if (profile is not None):
#			eProf = prof.build(None, None)
#			if (eProf is not None):
#				if (path is not None):
#					ePath = path.build(None, None)
#					if (ePath is not None):
#						surface = sweep = Part.Wire(ePath).makePipeShell([Part.Wire(eProf)], False, False)
#						self.shape = surface
		return i
	def setScaleClft(self, chunks, index, inventor):
		i = self.setSurface(chunks, index, inventor, False)
		return i
	def setShadowTpr(self, chunks, index, inventor):
		s1, i = readSurface(chunks, index, self.version)
		c1, i = readCurve(chunks, i, self.version)
		c2, i = readBS2Curve(chunks, i, self.version)
		f1, i = getFloat(chunks, i)
		i1, i = getInteger(chunks, i) #0
		if (i1 == 0):
			s2, i = readBS3Surface(chunks, i)
			f2, i = getFloat(chunks, i)
		if (i1 == 1):
			a00, i = getFloatArray(chunks, i)
			a01, i = getFloatArray(chunks, i)
			f2, i = getFloat(chunks, i)
			i2, i = getInteger(chunks, i) #0
			i3, i = getInteger(chunks, i) #0
			i4, i = getInteger(chunks, i) #0
			i5, i = getInteger(chunks, i) #0
		a1, i = getFloatArray(chunks, i)
		a2, i = getFloatArray(chunks, i)
		a3, i = getFloatArray(chunks, i)
		a4, i = getFloatArray(chunks, i)
		a5, i = getFloatArray(chunks, i)
		a6, i = getFloatArray(chunks, i)
		a1, i = getValue(chunks, i) # 0x0A/B
		v1, i = getVector(chunks, i)
		u, i = getFloat(chunks, i)
		v, i = getFloat(chunks, i)
		return i
	def setTSpline(self, chunks, index, inventor):
		i = self.setSurface(chunks, index, inventor)
		# int
		# block: type (str), def (str), values (str)
		# int
		return i
	def setVertexBlend(self, chunks, index):
		n, i = getInteger(chunks, index)
		arr  = []
		for j in range(0, n):
			vbl = VBL()
			vbl.t, i  = getText(chunks, i)
			vbl.n, i  = getCircleType(chunks, i)
			vbl.p, i  = getLocation(chunks, i)
			vbl.u, i  = getCircleSmoothing(chunks, i)
			vbl.v, i  = getCircleSmoothing(chunks, i)
			vbl.a, i  = getFloat(chunks, i)
			if (vbl.n == 'non_cross'):
				if (self.version > 3.0):
					vbl.s, i  = readSurface(chunks, i, self.version)
					vbl.c, i  = readUnknown(chunks, i, self.version)
				else:
					i += 5
					vbl.c, i = readCurve(chunks, i, self.version)
			elif (vbl.n == 'cross'):
				vbl.c, i = readUnknown(chunks, i, self.version)
				dummy = getValue(chunks, i)
				if (type(dummy[0]) == str):
					vbl.s, i = readUnknown(chunks, i, self.version)
				else:
					a, i = getInteger(chunks, i)
					b = []
					if (a == 1):
						dummy, i = getVector(chunks, i)
						b.append(dummy)
					elif (a == 3):
						dummy, i = getVector(chunks, i)
						b.append(dummy)
						dummy, i = getVector(chunks, i)
						b.append(dummy)
					if (self.version < 7.0):
						c, i = getVector(chunks, i)
				if (vbl.s is None):
					d, i = getFloat(chunks, i)
					e, i = getFloat(chunks, i)
					f, i = getSense(chunks, i)
			arr.append(vbl)
		return index
	def setRuledTpr(self, chunks, index, inventor):
		s1, i = readSurface(chunks, index, self.version)
		return i
	def setSweptTpr(self, chunks, index):
		s1, i = readSurface(chunks, index, self.version)
		return i
	def setRef(self, chunks, index):
		ref, i = getInteger(chunks, index)
		return i
	def setBulk(self, chunks, index):
		self.type, i = getValue(chunks, index)
		if (self.type == 'blend_support_surface'): return self.setBlendSupport(chunks, i + 1)
		if (self.type == 'clloftsur'):             return self.setClLoft(chunks, i, False)
		if (self.type == 'cl_loft_spl_sur'):       return self.setClLoft(chunks, i + 1, True)
		if (self.type == 'cylsur'):                return self.setCylinder(chunks, i)
		if (self.type == 'cyl_spl_sur'):           return self.setCylinder(chunks, i + 1)
		if (self.type == 'defmsur'):               return self.setDefm(chunks, i)
		if (self.type == 'defm_spl_sur'):          return self.setDefm(chunks, i + 1)
		if (self.type == 'exactsur'):              return self.setExact(chunks, i, False)
		if (self.type == 'exact_spl_sur'):         return self.setExact(chunks, i + 1, True)
		if (self.type == 'g2blnsur'):              return self.setG2Blend(chunks, i)
		if (self.type == 'g2_blend_spl_sur'):      return self.setG2Blend(chunks, i + 1)
		if (self.type == 'helix_spl_circ'):        return self.setHelixCircle(chunks, i + 1)
		if (self.type == 'helix_spl_line'):        return self.setHelixLine(chunks, i + 1)
		if (self.type == 'loftsur'):               return self.setLoft(chunks, i)
		if (self.type == 'loft_spl_sur'):          return self.setLoft(chunks, i + 1)
		if (self.type == 'net_spl_sur'):           return self.setNet(chunks, i + 1)
		if (self.type == 'offsur'):                return self.setOffset(chunks, i, False)
		if (self.type == 'off_spl_sur'):           return self.setOffset(chunks, i + 1, True)
		if (self.type == 'orthosur'):              return self.setOrtho(chunks, i, False)
		if (self.type == 'ortho_spl_sur'):         return self.setOrtho(chunks, i + 1, True)
		if (self.type == 'rbblnsur'):              return self.setRbBlend(chunks, i)
		if (self.type == 'rb_blend_spl_sur'):      return self.setRbBlend(chunks, i + 1)
		if (self.type == 'rotsur'):                return self.setRotation(chunks, i, False)
		if (self.type == 'rot_spl_sur'):           return self.setRotation(chunks, i + 1,  True)
		if (self.type == 'sclclftsur'):            return self.setScaleClft(chunks, i, False)
		if (self.type == 'scaled_cloft_spl_sur'):  return self.setScaleClft(chunks, i + 1, True)
		if (self.type == 'shadow_tpr_spl_sur'):    return self.setShadowTpr(chunks, i + 1, True)
		if (self.type == 'skinsur'):               return self.setSkin(chunks, i, False)
		if (self.type == 'skin_spl_sur'):          return self.setSkin(chunks, i + 1, True)
		if (self.type == 'srfsrfblndsur'):         return self.setBlendSupply(chunks, i)
		if (self.type == 'srf_srf_v_bl_spl_sur'):  return self.setBlendSupply(chunks, i + 1)
		if (self.type == 'sssblndsur'):            return self.setBlendSupply(chunks, i)
		if (self.type == 'sss_blend_spl_sur'):     return self.setBlendSupply(chunks, i + 1)
		if (self.type == 'sumsur'):                return self.setSum(chunks, i)
		if (self.type == 'sum_spl_sur'):           return self.setSum(chunks, i + 1)
		if (self.type == 'sweepsur'):              return self.setSweep(chunks, i, False)
		if (self.type == 'sweep_sur'):             return self.setSweep(chunks, i + 1, True)
		if (self.type == 'sweep_spl_sur'):         return self.setSweepSpline(chunks, i + 1)
		if (self.type == 't_spl_sur'):             return self.setTSpline(chunks, i + 1, True)
		if (self.type == 'ref'):                   return self.setRef(chunks, i)
		if (self.type == 'vertexblendsur'):        return self.setVertexBlend(chunks, i)
		if (self.type == 'VBL_SURF'):              return self.setVertexBlend(chunks, i + 1)
		if (self.type == 'ruled_tpr_spl_sur'):     return self.setRuledTpr(chunks, i + 1, True)
		if (self.type == 'swept_tpr_spl_sur'):     return self.setSweptTpr(chunks, i + 1)
		raise Exception("Unknown SplineSurface '%s'!"%(self.type))
	def setSubtype(self, chunks, index):
		self.sense, i  = getSense(chunks, index)
		block, i       = getBlock(chunks, i)
		self.setBulk(block, 0)
		self.rangeU, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		self.rangeV, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def set(self, entity, version):
		i = super(SurfaceSpline, self).set(entity, version)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self):
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
	def set(self, entity, version):
		i = super(SurfaceTorus, self).set(entity, version)
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
	def set(self, entity, version):
		i = super(Point, self).set(entity, version)
		self.position, i = getLocation(entity.chunks, i)
		return i

# abstract super class for all attributes
class Attributes(Entity):
	def __init__(self):
		super(Attributes, self).__init__()
		self._next     = None
		self._previous = None
		self._owner    = None
	def set(self, entity, version):
		i = super(Attributes, self).set(entity, version)
		self._next, i     = getRefNode(entity, i, 'attrib')
		self._previous, i = getRefNode(entity, i, 'attrib')
		self._owner, i    = getRefNode(entity, i, None)
		if (version > 15.0):
			i += 17 # skip ???
		return i
	def getNext(self):     return None if (self._next is None)     else self._next.node
	def getPrevious(self): return None if (self._previous is None) else self._previous.node
	def getOwner(self):    return None if (self._owner is None)    else self._owner.node
class Attrib(Attributes):
	def __init__(self): super(Attrib, self).__init__()
	def set(self, entity, version): return super(Attrib, self).set(entity, version)
class AttribADesk(Attrib):
	def __init__(self): super(AttribADesk, self).__init__()
class AttribADeskColor(AttribADesk):
	def __init__(self): super(AttribADeskColor, self).__init__()
	def set(self, entity, version):
		i = super(Attrib, self).set(entity, version)
		self.color, i = getText(entity.chunks, i)
		return i
class AttribAnsoft(Attrib):
	def __init__(self): super(AttribAnsoft, self).__init__()
class AttribAnsoftId(AttribAnsoft):
	def __init__(self): super(AttribAnsoftId, self).__init__()
class AttribAnsoftProperties(AttribAnsoft):
	def __init__(self): super(AttribAnsoftProperties, self).__init__()
class AttribDxid(Attrib):
	def __init__(self): super(AttribDxid, self).__init__()
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
	def set(self, entity, version):
		i = super(AttribGenName, self).set(entity, version)
		if (self.version < 16.0):
			i	 += 4 # [(keep|copy) , (keep_keep), (ignore), (copy)]
		self.text, i = getText(entity.chunks, i)
		return i
class AttribGenNameInteger(AttribGenName):
	def __init__(self):
		super(AttribGenNameInteger, self).__init__()
		self.value = 0
	def set(self, entity, version):
		i = super(AttribGenNameInteger, self).set(entity, version)
		if (version > 10):
			self.name, i  = getText(entity.chunks, i)
		self.value, i = getInteger(entity.chunks, i)
		return i
class AttribGenNameString(AttribGenName):
	def __init__(self):
		super(AttribGenNameString, self).__init__()
		self.value = ''
	def set(self, entity, version):
		i = super(AttribGenNameString, self).set(entity, version)
		self.value, i = getText(entity.chunks, i)
		return i
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
class AttribSysConvexity(AttribSt):
	def __init__(self): super(AttribSysConvexity, self).__init__()
class AttribStNoMerge(AttribSt):
	def __init__(self): super(AttribStNoMerge, self).__init__()
class AttribStNoCombine(AttribSt):
	def __init__(self): super(AttribStNoCombine, self).__init__()
class AttribStRgbColor(AttribSt):
	def __init__(self):
		super(AttribStRgbColor, self).__init__()
		self.color = (0.5, 0.5, 0.5)
	def set(self, entity, version):
		i = super(AttribStRgbColor, self).set(entity, version)
		self.color, i = getPoint(entity.chunks, i)
		return i
class AttribStDisplay(AttribSt):
	def __init__(self):
		super(AttribStRgbColor, self).__init__()
		self.revision = 0
	def set(self, entity, version):
		i = super(AttribStRgbColor, self).set(entity, version)
		self.revision, i = getInteger(entity.chunks, i)
		return i
class AttribSys(Attrib):
	def __init__(self): super(AttribSys, self).__init__()
class AttribSysAnnotationAttrib(AttribSys):
	def __init__(self): super(AttribSysAnnotationAttrib, self).__init__()
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
		self.typ = '@'

	def __str__(self):
		if (self.tag == 0x04): return "%d "      %(self.val)
		if (self.tag == 0x06): return "%g "      %(self.val)
		if (self.tag == 0x07): return "%s%d %s " %(self.typ, len(self.val), self.val)# STRING
		if (self.tag == 0x08): return "%s"       %(self.val)                         # STRING
		if (self.tag == 0x0A): return "%s "      %(self.val)
		if (self.tag == 0x0B): return "%s "      %(self.val)
		if (self.tag == 0x0C): return "%s "      %(self.val)                         # ENTITY_POINTER
		if (self.tag == 0x0D): return "%s "      %(self.val)                         # CLASS_IDENTIFYER
		if (self.tag == 0x0E): return "%s-"      %(self.val)                         # SUBCLASS_IDENTIFYER
		if (self.tag == 0x0F): return "%s "      %(self.val)                         # SUBTYP_START
		if (self.tag == 0x10): return "%s "      %(self.val)                         # SUBTYP_END
		if (self.tag == 0x11): return "%s\n"     %(self.val)                         # TERMINATOR
		if (self.tag == 0x12): return "%s%d %s " %(self.typ, len(self.val), self.val)# STRING
		if (self.tag == 0x13): return "(%s) "      %(" ".join(["%g" %(f) for f in self.val]))
		if (self.tag == 0x14): return "(%s) "      %(" ".join(["%g" %(f) for f in self.val])) # something to do with scale
		if (self.tag == 0x15): return "%d "      %(self.val)
		if (self.tag == 0x16): return "(%s) "      %(" ".join(["%g" %(f) for f in self.val]))
		return ''

class AcisEntity():
	def __init__(self, name):
		self.chunks = []
		self.name   = name
		self.index  = -1
		self.node   = None

	def add(self, key, val):
		self.chunks.append(AcisChunk(key, val))
	def getStr(self):
		return "-%d %s %s" %(self.index, self.name,''.join('%s' %c for c in self.chunks))
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

def readNextSabChunk(data, index):
	tag, i = getUInt8(data, index)

	if (tag == 0x04):   val, i = getSInt32(data, i)
	elif (tag == 0x06): val, i = getFloat64(data, i)
	elif (tag == 0x07): val, i = readStr1(data, i)
	elif (tag == 0x08): val, i = readStr2(data, i)
	elif (tag == 0x0A): val    = '0x0A'
	elif (tag == 0x0B): val    = '0x0B'
	elif (tag == 0x0C): val, i = readEntityRef(data, i) # ENTITY_POINTER
	elif (tag == 0x0D): val, i = readStr1(data, i)
	elif (tag == 0x0E): val, i = readStr1(data, i)
	elif (tag == 0x0F): val    = '{'
	elif (tag == 0x10): val    = '}'
	elif (tag == 0x11): val    = '#'
	elif (tag == 0x12): val, i = readStr4(data, i)
	elif (tag == 0x13): val, i = getFloat64A(data, i, 3) # normalized direction
	elif (tag == 0x14): val, i = getFloat64A(data, i, 3) # position that needs to be scaled
	elif (tag == 0x15): val, i = getUInt32(data, i)
	elif (tag == 0x16): val, i = getFloat64A(data, i, 2)
	else:
		raise Exception("Don't know to read TAG %X" %(tag))
	return tag, val, i

TYPES = {
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
	"ufld_dev_pair_attrib-at_ufld-attrib":                                                         AttribAtUfldDevPair,
	"ufld_pos_transf_attrib-at_ufld-attrib":                                                       AttribAtUfldFfldPosTransf,
	"mix_UF_ContourRoll_Track-ufld_pos_transf_attrib-at_ufld-attrib":                              AttribAtUfldFfldPosTransfMixUfContourRollTrack,
	"ufld_non_merge_bend_attrib-at_ufld-attrib":                                                   AttribAtUfldNonMergeBend,
	"ufld_pos_track_attrib-at_ufld-attrib":                                                        AttribAtUfldPosTrack,
	"mix_UF_RobustPositionTrack-ufld_pos_track_attrib-at_ufld-attrib":                             AttribAtUfldPosTrackMixUfRobustPositionTrack,
	"ufld_surf_simp_attrib-ufld_pos_track_attrib-at_ufld-attrib":                                  AttribAtUfldPosTrackSurfSimp,
	"DXID-attrib":                                                                                 AttribDxid,
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
