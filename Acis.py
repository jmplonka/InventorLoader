# -*- coding: utf-8 -*-
from __future__                 import unicode_literals

'''
Acis.py:
Collection of classes necessary to read and analyse Standard ACIS Text (*.sat) files.
'''

import traceback, FreeCAD, Part, Draft, os
from importerUtils              import *
from FreeCAD                    import Vector as VEC, Rotation as ROT, Placement as PLC, Matrix as MAT, Base
from math                       import pi, fabs, degrees, asin, sin, cos, tan, atan2, ceil, e, cosh, sinh, tanh, acos, acosh, asin, asinh, atan, atanh, log, sqrt, exp, log10
from BOPTools.GeneralFuseResult import GeneralFuseResult

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

# Primitives for Binary File Format (.sab)
TAG_CHAR          =  2	 # character (unsigned 8 bit)
TAG_SHORT         =  3	 # 16Bit signed value
TAG_LONG          =  4	 # 32Bit signed value
TAG_FLOAT         =  5	 # 32Bit IEEE Float value
TAG_DOUBLE        =  6	 # 64Bit IEEE Float value
TAG_UTF8_U8       =  7	 #  8Bit length + UTF8-Char
TAG_UTF8_U16      =  8	 # 16Bit length + UTF8-Char
TAG_UTF8_U32_A    =  9	 # 32Bit length + UTF8-Char
TAG_TRUE          = 10	 # Logical true value
TAG_FALSE         = 11	 # Logical false value
TAG_ENTITY_REF    = 12	 # Entity reference
TAG_IDENT         = 13	 # Sub-Class-Name
TAG_SUBIDENT      = 14	 # Base-Class-Namme
TAG_SUBTYPE_OPEN  = 15	 # Opening block tag
TAG_SUBTYPE_CLOSE = 16	 # Closing block tag
TAG_TERMINATOR    = 17	 # '#' sign
TAG_UTF8_U32_B    = 18	 # 32Bit length + UTF8-Char
TAG_POSITION      = 19	 # 3D-Vector scaled (scaling will be done later because of text file handling!)
TAG_VECTOR_3D     = 20	 # 3D-Vector normalized
TAG_ENUM_VALUE    = 21	 # value of an enumeration
TAG_VECTOR_2D     = 22	 # U-V-Vector

# TAG_FALSE, TAG_TRUE value mappings
RANGE        = {TAG_FALSE: 'I',            TAG_TRUE: 'F'}
REFLECTION   = {TAG_FALSE: 'no_reflect',   TAG_TRUE: 'reflect'}
ROTATION     = {TAG_FALSE: 'no_rotate',    TAG_TRUE: 'rotate'}
SHEAR        = {TAG_FALSE: 'no_shear',     TAG_TRUE: 'shear'}
SENSE        = {TAG_FALSE: 'forward',      TAG_TRUE: 'reversed'}
SENSEV       = {TAG_FALSE: 'forward_v',    TAG_TRUE: 'reverse_v'}
SIDES        = {TAG_FALSE: 'single',       TAG_TRUE: 'double'}
SIDE         = {TAG_FALSE: 'out',          TAG_TRUE: 'in'}
SURF_BOOL    = {TAG_FALSE: 'FALSE',        TAG_TRUE: 'TRUE'}
SURF_NORM    = {TAG_FALSE: 'ISO',          TAG_TRUE: 'UNKNOWN'}
SURF_DIR     = {TAG_FALSE: 'SKIN',         TAG_TRUE: 'PERPENDICULAR'}
SURF_SWEEP   = {TAG_FALSE: 'angled',       TAG_TRUE: 'normal'}
CIRC_TYP     = {TAG_FALSE: 'non_cross',    TAG_TRUE: 'cross'}
CIRC_SMTH    = {TAG_FALSE: 'normal',       TAG_TRUE: 'smooth'}
CALIBRATED   = {TAG_FALSE: 'uncalibrated', TAG_TRUE: 'calibrated'}
CHAMFER_TYPE = {TAG_FALSE: 'const',        TAG_TRUE: 'radius'}
CONVEXITY    = {TAG_FALSE: 'concave',      TAG_TRUE: 'convex'}
RENDER_BLEND = {TAG_FALSE: 'rb_snapshot',  TAG_TRUE: 'rb_envelope'}

# TAG_ENUM value mappings
VAR_RADIUS  = {0: 'single_radius',  1: 'two_radii'}
VAR_CHAMFER = {3: 'rounded_chamfer'}
CLOSURE     = {0: 'open',   1: 'closed',  2: 'periodic', '0x0B': 'open', '0x0A': 'periodic'}
SINGULARITY = {0: 'full',   1: 'v',       2: 'none',     '0x0B': 'none', '0x0A': 'full'}
VBL_CIRLE   = {0: 'circle', 1: 'ellipse', 3: 'unknown', 'cylinder': 'circle'}
CURV_DIR    = {0: 'left',   2: 'right'}
scale   = 1.0

version = 7.0

subtypeTableCurves   = []
subtypeTablePCurves  = []
subtypeTableSurfaces = {}
references           = {} # dict of AcisEntities
_invSubTypTblSurfLst = {}
_nameMtchAttr        = {}
_refs                = {} # dict of AcisRefs
_dcIdxAttributes     = {} # dict of an attribute list
_header              = None

def getSatRefs():
	global _refs
	return _refs

def initSatRefs():
	global _refs
	_refs.clear()

def getDcAttributes():
	global _dcIdxAttributes
	return _dcIdxAttributes

def _getStr_(data, offset, end):
	txt = data[offset: end].decode('cp1252')
	if (sys.version_info.major < 3):
		txt = txt.encode(ENCODING_FS).decode("utf8")
	return txt, end

def COS(x):        return (cos(x))
def COSH(x):       return (cosh(x))
def COT(x):        return (cos(x)/sin(x))
def COTH(x):       return (cosh(x)/sinh(x))
def CSC(x):        return (1/sin(x))
def CSCH(x):       return (1/sinh(x))
def SEC(x):        return (1/cos(x))
def SECH(x):       return (1/cosh(x))
def SIN(x):        return (sin(x))
def SINH(x):       return (sinh(x))
def TAN(x):        return (tan(x))
def TANH(x):       return (tanh(x))
def ARCCOS(x):     return (acos(x))
def ARCCOSH(x):    return (acosh(x))
def ARCOT(x):      return (pi/2 - atan(x))
def ARCOTH(x):     return (0.5*log((x+1)/(x-1)))
def ARCCSC(x):     return (asin(1/x))
def ARCCSCH(x):    return (log((1+sqrt(1+x**2))/x))
def ARCSEC(x):     return (acos(1/x))
def ARCSECH(x):    return (log((1+sqrt(1-x**2))/x))
def ARCSIN(x):     return (asin(x))
def ARCSINH(x):    return (asinh(x))
def ARCTAN(x):     return (atan(x))
def ARCTANH(x):    return (atanh(x))
def ABS(x):        return (abs(x))
def EXP(x):        return (exp(x))
def LN(x):         return (log(x))
def LOG(x):        return (log10(x))
def NORM(value):   return VEC(value.x, value.y, value.z).normalize()
def ROTATE(v, t):  return t.rotate(v)
def CROSS(v1, v2): return v1.cross(v2)
def DOT(v1, v2):   return v1.dot(v2)
def SET(x):
	if (x > 0.0): return 1
	return -1 if (x < 0.0) else 0
def SIGN(x):       return SET(x)
def SIZE(v):       return v.Length()
#def STEP(l1, n1, l2, n2, ...) ... will throw an error if found in evaluation
def TERM(v, n):    return v.__getitem__(n)
def TRANS(v, t):
	return t.transpose(v)
def MIN(*x):       return min(x)
def MAX(*x):       return max(x)
#def NOT(x) ... will throw an error if found in evaluation
def DCUR(c, x):     return c.parameter(x)
def DSURF(c, u, v): return c.parameter(u, v)

def getHeader():
	global _header
	return _header
def setHeader(header):
	global _header
	_header = header

class Law(object):
	# Laws:
	#	trigonometric:
	#		cos(x), cosh(x), cot(x) = cos(x)/sin(x), coth(x)
	#		csc(x) = 1/sin(x), csch(x), sec(x) = 1/cos(x), sech(x)
	#		sin(x), sinh(x), tan(x), tanh(x)
	#		arccos(x), arccosh(x), arcot(x), arcoth(x)
	#		arccsc(x), arccsch(x), arcsec(x), arcsech(x)
	#		arcsin(x), arcsinh(x), arctan(x), arctanh(x)
	#	functions:
	#		vec(x,y,z), norm(X)
	#		abs(x), exp(x), ln(x), log(x), sqrt(x)
	#		rotate(x,y), set(x) = sign(x), size(x), step(...)
	#		term(X,n), trans(X,y)
	#		min(x), max(x), not(x)
	#	operators:
	#		+,-,*,/,x,^,<,>,<=,>=
	#	constants
	#		e = 2.718
	#		pi= 3.141
	def __init__(self, eq):
		#FIXME: how to handle cross operator???
		self.eq = eq
		# convert ^ into **
		self.eq = self.eq.replace('^', ' ** ')
	def evaluate(self, X):
		try:
			return eval(self.eq)
		except Exception as e:
			logError(u"Can't evaluate '%s': %s", self.eq, e)
		return None

def init():
	global references, subtypeTableCurves, subtypeTablePCurves, subtypeTableSurfaces, _invSubTypTblSurfLst, _nameMtchAttr, _dcIdxAttributes

	subtypeTableCurves   = []
	subtypeTablePCurves  = []
	subtypeTableSurfaces = {}
	_invSubTypTblSurfLst = {}
	_nameMtchAttr        = {}
	references           = {}
	_dcIdxAttributes     = {}
	initSatRefs()

def addSubtypeNodeCurve(curve):
	global subtypeTableCurves
	subtypeTableCurves.append(curve)

def addSubtypeNodePCurve(pcurve):
	global subtypeTablePCurves
	subtypeTablePCurves.append(pcurve)

def addSubtypeNodeSurface(surface, index):
	global subtypeTableSurfaces
	global _invSubTypTblSurfLst

	entityID = surface.index
	subtypeTableSurfaces[index] = surface
	_invSubTypTblSurfLst[entityID] = index

def getSubtypeNodeCurve(index):
	global subtypeTableCurves
	try:
		return subtypeTableCurves[index]
	except:
		return None

def getSubtypeNodePCurve(index):
	global subtypeTablePCurves
	try:
		return subtypeTablePCurves[index]
	except:
		return None

def getSubtypeNodeSurfaces(index):
	global subtypeTableSurfaces
	return subtypeTableSurfaces.get(index, None)

def clearEntities():
	global subtypeTableCurves, subtypeTablePCurves, subtypeTableSurfaces, _invSubTypTblSurfLst, _nameMtchAttr, references

	subtypeTableCurves[:] = []
	subtypeTablePCurves[:] = []
	subtypeTableSurfaces.clear()
	_invSubTypTblSurfLst.clear()
	_nameMtchAttr.clear()
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
		if (entity.index < 0): return None
		if (entity.name == 'delta_state'): return None
		node = references[entity.index]
		# this entity is overwriting a previous entity with the same index -> ignore it
		logWarning(u"    Found 2nd '-%d %s' - IGNORED!", entity.index, entity.name)
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
					break
				except:
					i += 1
			logError(u"TypeError: Can't find class for '%s' - using '%s'!", entity.name, t)

		if (entity.index >= 0):
			references[entity.index] = node
		if (hasattr(node, 'set')):
			entity.node = node
			node.entity = entity
			node.set(entity)
	return node

def getValue(chunks, index):
	val = chunks[index].val
	return val, index + 1

def getRefNode(entity, index, name):
	val, i = getValue(entity.chunks, index)
	if (isinstance(val, AcisRef)):
		ref = val.entity
		if (name is not None) and (ref is not None) and (ref.name.endswith(name) == False):
			raise Exception("Excpeced %s but found %s" %(name, ref.name))
		return ref, i
	raise Exception("Chunk at index=%d, is not a reference" %(index))

def getEnum(chunks, index):
	chunk = chunks[index]
	tag = chunk.tag
	assert (tag in [TAG_TRUE, TAG_FALSE]), u"Expected either TRUE or FALSE but found '%s'" %(chunk)
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

def getDcIndexMappings(chunks, index, attr):
	global _dcIdxAttributes
	m = []
	count, i = getInteger(chunks, index)
	for n in range(count):
		dcIdx, i = getInteger(chunks, i)
		value, i = getInteger(chunks, i)
		m.append((dcIdx, value))
		try:
			indexMappings = _dcIdxAttributes[dcIdx]
		except:
			indexMappings = IndexMappings()
			_dcIdxAttributes[dcIdx] = indexMappings
		indexMappings.append(attr)
	return m, i

def getLong(chunks, index):
	val, i = getValue(chunks, index)
	if (sys.version_info.major > 2):
		return int(val), i
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

def getFloatsScaled(chunks, index, count):
	s = getScale()
	i = index
	arr = []
	for n in range(0, count):
		f, i = getFloat(chunks, i)
		arr.append(f * f)
	return arr, i

def getFloatArray(chunks, index):
	n, i = getInteger(chunks, index)
	arr, i = getFloats(chunks, i, n)
	return arr, i

def getLength(chunks, index):
	l, i = getFloat(chunks, index)
	return l * getScale(), i

def getText(chunks, index):
	chunk = chunks[index]
	if (chunk.tag == TAG_DOUBLE):
		return getValue(chunks, index+1)
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
		return values[val], i
	except:
		return val, i

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

def getCurvDir(chunks, index):
	return getEnumByValue(chunks, index, CURV_DIR)

def getSurfSweep(chunks, index):
	return getEnumByTag(chunks, index, SURF_SWEEP)

def getVblType(chunks, index):
	return getEnumByTag(chunks, index, CIRC_TYP)

def getCircleSmoothing(chunks, index):
	return getEnumByTag(chunks, index, CIRC_SMTH)

def getVarRadius(chunks, index):
	radius, i = getEnumByValue(chunks, index, VAR_RADIUS)
	if (isString(radius)):
		return radius.lower(), i
	return radius, i

def getVarChamfer(chunks, index):
	chamfer, i = getEnumByValue(chunks, index, VAR_CHAMFER)
	return chamfer.lower(), i

def getCalibrated(chunks, index):
	return getEnumByTag(chunks, index, CALIBRATED)

def getChamferType(chunks, index):
	return getEnumByTag(chunks, index, CHAMFER_TYPE)

def getConvexity(chunks, index):
	return getEnumByTag(chunks, index, CONVEXITY)

def getRenderBlend(chunks, index):
	return getEnumByTag(chunks, index, RENDER_BLEND)

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
	return Interval(lower, upper), i

def getPoint(chunks, index):
	chunk = chunks[index]
	if ((chunk.tag == TAG_POSITION) or (chunk.tag == TAG_VECTOR_3D)):
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
	i = index
	chunk = chunks[i]
	data.append(chunk)
	i += 1
	chunk = chunks[i]
	while (chunk.tag != TAG_SUBTYPE_CLOSE):
		if (chunk.tag == TAG_SUBTYPE_OPEN):
			block, i = getBlock(chunks, i)
			data += block
		else:
			data.append(chunk)
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
		countU, i = getInteger(chunks, i)
		countV, i = getInteger(chunks, i)
		return closureU, closureV, singularityU, singularityV, countU, countV, i

	raise Exception("Unknown closure '%s'!" %(closureU))

def readKnotsMults(count, chunks, index):
	knots = []
	mults = []
	i     = index
	for j in range(count):
		knot, i = getFloat(chunks, i)
		mult, i = getInteger(chunks, i)
		knots.append(knot)
		mults.append(mult)
	return knots, mults, i

def adjustMultsKnots(knots, mults, periodic, degree):
	mults[0] = degree + 1
	mults[-1] = degree + 1
#	return knots, mults, False # Force periodic to False!!!
	return knots, mults, periodic

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

def readBlend(chunks, index):
	nubs, i = readBS2Curve(chunks, index)
	if (nubs is not None):
		nubs.sense, i = getSense(chunks, i)
		nubs.factor, i = getFloat(chunks, i)
		return nubs, i
	return None, index

def readLaw(chunks, index):
	n, i = getText(chunks, index)
	if (n == 'TRANS'):
		v = Transform()
		i = v.setBulk(chunks, i)
		return (n, v), i
	if (n == 'EDGE'):
		c, i = readCurve(chunks, i)
		f, i = getFloats(chunks, i, 2)
		return (n, c, f), i
	if (n == 'SPLINE_LAW'):
		a, i = getInteger(chunks, i)
		b, i = getFloatArray(chunks, i)
		c, i = getFloatArray(chunks, i)
		d, i = getPoint(chunks, i)
		return (n, a, b, c, d), i
	if (n == 'null_law'):
		return (n, None), i
	l = Law(n)
	return (n, l), i

def newInstance(CLASSES, key):
	cls = CLASSES[key]
	if cls is None: return None
	return cls()

def readCurve(chunks, index):
	val, i = getValue(chunks, index)
	try:
		curve = newInstance(CURVES, val)
		if (curve is not None):
			i = curve.setSubtype(chunks, i)
		return curve, i
	except:
		raise Exception("Unknown curve-type '%s'!" % (val))

def readSurface(spline, chunks, index):
	chunk = chunks[index]
	i = index + 1
	subtype = chunk.val
	if (chunk.tag in [TAG_UTF8_U8, TAG_IDENT]):
		try:
			surface = newInstance(SURFACES, subtype)
			if (surface is not None):
				i = surface.setSubtype(chunks, i)
				if (isinstance(surface, SurfaceSpline)):
					spline.surfaces.append(surface)
		except:
			raise Exception("Unknown surface-type '%s'!" % (subtype))

		return surface, i
#FIXME: this is a dirty hack :(
	if (chunk.tag == TAG_DOUBLE):
		a, i = getFloats(chunks, index, 5)
		return None, i
	if (chunk.tag in [TAG_POSITION, TAG_VECTOR_3D]):
		a, i = getFloats(chunks, i, 2)
		return None, i

def readArrayFloats(chunks, index, inventor):
	a1, i = getFloatArray(chunks, index)
	a2, i = getFloatArray(chunks, i)
	a3, i = getFloatArray(chunks, i)
	a4, i = getFloatArray(chunks, i)
	a5, i = getFloatArray(chunks, i)
	a6, i = getFloatArray(chunks, i)
	if (inventor and chunks[i].tag in (TAG_TRUE, TAG_FALSE)):
		e, i = getEnum(chunks, i)
	else:
		e = TAG_FALSE
	return (a1, a2, a3, a4, a5, a6, e), i

def rotateShape(shape, dir):
	# Setting the axis directly doesn't work for directions other than x-axis!
	angle = degrees(DIR_Z.getAngle(dir))
	if (isEqual1D(angle, 0)):
		axis = DIR_Z.cross(dir) if angle != 180 else DIR_X
		shape.rotate(PLC(CENTER, axis, angle))
	return

def isBetween(a, c, b):
	ac = a.distanceToPoint(c)
	cb = c.distanceToPoint(b)
	ab = a.distanceToPoint(b)
	return ac + cb == ab

def isOnLine(sEdge, fEdge):
	# either start- or endpoint mus be same!
	sp = [v.Point for v in sEdge.Vertexes]
	fp = [v.Point for v in fEdge.Vertexes]
#	if (isEqual(sp[0], fp[0]) or isEqual(sp[1], fp[0])): return isBetween(sp[0], fp[1], sp[1])
#	if (isEqual(sp[0], fp[1]) or isEqual(sp[1], fp[1])): return isBetween(sp[0], fp[0], sp[1])
	if (isEqual(sp[0], fp[0])): return isBetween(sp[0], fp[1], sp[1])
	if (isEqual(sp[1], fp[1])): return isBetween(sp[0], fp[0], sp[1])
	return False

def isOnCircle(sEdge, fEdge):
	sp = [v.Point for v in sEdge.Vertexes]
	fp = [v.Point for v in fEdge.Vertexes]
	sc = sEdge.Curve
	fc = fEdge.Curve
	if (isEqual(sp[0], fp[0])):
#		if (isEqual(fc.Axis, sc.Axis) or isEqual(-1 * fc.Axis, sc.Axis)):
		if (isEqual(fc.Axis, sc.Axis)):
			return isEqual1D(fc.Radius, sc.Radius)
	return False

def isOnEllipse(se, fe):
	sc = se.Curve
	fc = fe.Curve
	if (isEqual(fc.Location, sc.Location)):
		if (isEqual(fc.Axis, sc.Axis)):
			if (isEqual(fc.Focus1, sc.Focus1)):
				if (isEqual1D(fc.MajorRadius, sc.MajorRadius)):
					return isEqual1D(fc.MinorRadius, sc.MinorRadius)
	return False

def isOnBSplineCurve(sEdge, fEdge):
	sp = [v.Point for v in sEdge.Vertexes]
	fp = [v.Point for v in fEdge.Vertexes]
	if (len(sp) != len(fp)):
		return False
	for i, p in enumerate(sp):
		if (not isEqual(p, fp[i])):
			return False
	return True

def isSeam(edge, face):
	c = edge.Curve
	for fEdge in face.Edges:
		try:
			if (isinstance(c, fEdge.Curve.__class__)):
				if (isinstance(c, Part.Line)):
					if isOnLine(edge, fEdge): return True
				elif (isinstance(c, Part.LineSegment)):
					if isOnLine(edge, fEdge): return True
				elif (isinstance(c, Part.Circle)):
					if isOnCircle(edge, fEdge): return True
				elif (isinstance(c, Part.Ellipse)):
					if isOnEllipse(edge, fEdge): return True
				elif (isinstance(c, Part.BSplineCurve)):
					if isOnBSplineCurve(edge, fEdge): return True
				elif (isinstance(c, Part.ArcOfCircle)):
					if isOnCircle(c.Circle, fEdge.Curve.Circle): return True
				elif (isinstance(c, Part.ArcOfEllipse)):
					if isOnEllipse(c.Ellipse, fEdge.Curve.Ellipse): return True
				else:
					logError(u"Unknown edge type '%s'!", c.__class__.__name)
		except Exception as e:
			pass
	return False

def isValid(face):
	if (not face.isValid()):
		return False
	for edge in face.Edges:
		for v in edge.Vertexes:
			if (v.Point.Length >= 0.4e+7):
				return False
	return True

def findMostMatches(faces):
	if (len(faces) > 0):
		matches = faces.keys()
		matches = sorted(matches)
		return faces[matches[-1]]
	return []

def eliminateOuterFaces(faces, edges):
	_faces = [f for f in faces if isValid(f)]

	if (len(_faces) == 0):
		return None

	if (len(_faces) == 1):
		return _faces[0]

	result = {}
	for face in _faces:
		matches = 0
		for e in edges:
			if (isSeam(e, face)):
				matches += 1
		try:
			lst = result[matches]
		except:
			lst = []
			result[matches] = lst
		lst.append(face)
	faces = findMostMatches(result)
	if (len(faces) == 1):
		return faces[0]
	return faces[0].multiFuse(faces[1:])

def createCircle(center, normal, radius):
	circle = Part.Circle(center, normal, radius.Length)
	circle.XAxis = radius
	return circle

def createEllipse(center, normal, major, ratio):
	if (ratio == 1):
		return createCircle(center, normal, major)
	if (ratio <= 1):
		s1 = center + major
		s2 = center + major.cross(normal).normalize() * major.Length * ratio
	else:
		s2 = center + major
		s1 = center + major.cross(normal).normalize() * major.Length / ratio
	try:
		return Part.Ellipse(s1, s2, center)
	except:
		try:
			return Part.Ellipse(s2, s1, center)
		except:
			logError("ERROR> Can't create ellipse for center=(%s), normal=(%s), major=(%s), ratio=%g", center, normal, major, ratio)

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
	bsc = Part.Geom2d.BSplineCurve2d()
	if (pcurve.rational):
		bsc.buildFromPolesMultsKnots(      \
			poles    = pcurve.poles,   \
			mults    = pcurve.uMults,  \
			knots    = pcurve.uKnots,  \
			periodic = False,          \
			degree   = pcurve.uDegree, \
			weights  = pcurve.weights  \
		)
	else:
		bsc.buildFromPolesMultsKnots(      \
			poles    = pcurve.poles,   \
			mults    = pcurve.uMults,  \
			knots    = pcurve.uKnots,  \
			periodic = False,          \
			degree   = pcurve.uDegree  \
		)
	shape = bsc.toShape(surf, bsc.FirstParameter, bsc.LastParameter)
	if (shape is not None):
		shape.Orientation = str('Reversed') if (sense == 'reversed') else str('Forward')
	return shape

def createBSplinesCurve(nubs, sense):
	if (nubs is None):
		return None
	number_of_poles = len(nubs.poles)
	if (number_of_poles == 2): # if there are only two poles we can simply draw a line
		shape = createLine(nubs.poles[0], nubs.poles[1])
	else:
		shape = None
		try:
			bsc = Part.BSplineCurve()
			if (nubs.rational):
				bsc.buildFromPolesMultsKnots(       \
					poles         = nubs.poles,     \
					mults         = nubs.uMults,    \
					knots         = nubs.uKnots,    \
					periodic      = False,          \
					degree        = nubs.uDegree,   \
					weights       = nubs.weights
				)
			else:
				bsc.buildFromPolesMultsKnots(       \
					poles         = nubs.poles,     \
					mults         = nubs.uMults,    \
					knots         = nubs.uKnots,    \
					periodic      = False,          \
					degree        = nubs.uDegree
				)
			# periodic = nubs.uPeriodic
			shape = bsc.toShape()
		except Exception as e:
			logError(u"ERROR> %s", e)
			logError(traceback.format_exc())
	if (shape is not None):
		shape.Orientation = str('Reversed') if (sense == 'reversed') else str('Forward')
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
				uperiodic = False,          \
				vperiodic = False,          \
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
				uperiodic = False,          \
				vperiodic = False,          \
				udegree   = nubs.uDegree,   \
				vdegree   = nubs.vDegree    \
			)
		# uperiodic = nubs.uPeriodic
		# vperiodic = nubs.vPeriodic
		return bss.toShape()
	except Exception as e:
		logError(u"ERROR> %s", e)
		logError(traceback.format_exc())
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
		spline = BS3_Curve(nbs == 'nurbs', closure == 'periodic', dgr)
		i = spline.readPoints3DList(knots, chunks, i)
		return spline, i
	return None, index

def readBS3Surface(chunks, index):
	nbs, degreeU, degreeV, i = getDimensionSurface(chunks, index)
	if (nbs == 'nullbs'):
		return None, i
	if (nbs in ('nubs', 'nurbs')):
		closureU, closureV, singularityU, singularityV, countU, countV, i = getClosureSurface(chunks, i)
		spline = BS3_Surface(nbs == 'nurbs', closureU == 'periodic', closureV == 'periodic', degreeU, degreeV)
		i = spline.readPoints3DMap(countU, countV, chunks, i)
		return spline, i
	if (nbs == 'summary'):
		x, i            = getFloat(chunks, i)
		arr, i          = getFloatArray(chunks, i)
		tol, i          = getLength(chunks, i)
		closureU, i     = getClosure(chunks, i)
		closureV, i     = getClosure(chunks, i)
		singularityU, i = getSingularity(chunks, i)
		singularityV, i = getSingularity(chunks, i)
		# FIXME: create a surface from these values! -> ../tutorials/2012/Tube and Pipe/Example_iparts/45Elbow.ipt
	return None, i

def readSplineSurface(chunks, index, tolerance):
	singularity, i = getSingularity(chunks, index)
	if (singularity == 'full'):
		spline, i = readBS3Surface(chunks, i)
		if ((spline is not None) and tolerance):
			tol, i = getLength(chunks, i)
			return spline, tol, i
		return spline, None, i
	arr1 = None
	arr2 = None
	rngU = None
	rngV = None
	tol  = None
	if ((singularity == 'none') or (singularity == 4)):
		rngU, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		rngV, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		clsU, i = getClosure(chunks, i)
		clsV, i = getClosure(chunks, i)
		sngU, i = getSingularity(chunks, i)
		sngV, i = getSingularity(chunks, i)
		return None, (arr1, arr2, rngU, rngV, tol, clsU, clsV, sngU, sngV), i
	if ((singularity == 'v') or (singularity == 'summary')):
		arr1, i = getFloatArray(chunks, i)
		arr2, i = getFloatArray(chunks, i)
		tol, i  = getLength(chunks, i)
		clsU, i = getClosure(chunks, i)
		clsV, i = getClosure(chunks, i)
		sngU, i = getSingularity(chunks, i)
		sngV, i = getSingularity(chunks, i)
		# FIXME: create a surface from these values! -> ../tutorials/2012/Tube and Pipe/Example_iparts/45Elbow.ipt
		return None, (arr1, arr2, rngU, rngV, tol, clsU, clsV, sngU, sngV), i
	raise Exception("Unknown spline singularity '%s'" %(singularity))

def readLofSubdata(chunks, i):
	type, i    = getInteger(chunks, i)
	n, i       = getInteger(chunks, i)
	m, i       = getInteger(chunks, i)
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

def getBlendValues(chunks, index):
	a   = None
	s   = None
	r   = None
	bsc = None
	name, i     = getValue(chunks, index)
	if (chunks[i].tag in [TAG_UTF8_U8, TAG_TRUE, TAG_FALSE]):
		t = 1
	else:
		t, i = getInteger(chunks, i) # Enum value
	c, i = getCalibrated(chunks, i)
	if (name == 'two_ends'):
		a, i = getFloats(chunks, i, 2)
		s, i = getFloatsScaled(chunks, i, 2)
		return (name, c, t, a, s, bsc, r, None), i
	if (name == 'edge_offset'):
		if (t == 0):
			a, i = getFloats(chunks, i, 2) # start and end angle in RAD
			r, i = getLength(chunks, i)
		elif (t == 1):
			r, i = getFloat(chunks, i)
			s, i = getFloatsScaled(chunks, i, 2)
		return (name, c, t, a, s, bsc, r, None), i
	if (name == 'functional'):
		a, i   = getFloats(chunks, i, 1)
		s, i   = getLength(chunks, i)
		bsc, i = readBS2Curve(chunks, i)
		if (type(chunks[i].val) == float):
			r, i   = getFloat(chunks, i)
		else:
			r, i   = getValue(chunks, i)
		return (name, c, t, a, [s], bsc, r, None), i
	if (name == 'const'):
		a, i   = getFloats(chunks, i, 2)
		s, i   = getLength(chunks, i)
		vc, i  = getVarChamfer(chunks, i)   # 3 = rounded_chamfer
		ct, i  = getChamferType(chunks, i)  # 0x0A = radius, 0x0B = const
		bv, i  = getBlendValues(chunks, i)  # two_ends ...
		return (name, c, t, a, [s], bsc, r, (vc, ct, bv)), i
	if (name == 'interp'): # Fillets variant radii
		a, i   = getFloats(chunks, i, 1)
		s, i   = getLength(chunks, i)
		bsc, i = readBS2Curve(chunks, i)
		n, i   = getInteger(chunks, i)   # Enum
		k, i   = getInteger(chunks, i)   # number of points
		lst = []
		for j in range(k):
			u_j, i = getFloat(chunks, i)     # u-value of the radius
			r_j, i = getLength(chunks, i)    # Radius
			t_j, i = getFloats(chunks, i, 2) # Doubles???
			p_j, i = getLocation(chunks, i)  # Position
			n_j, i = getVector(chunks, i)    # Axis
			lst.append((u_j, r_j, t_j, p_j, n_j))
		b, i  = getInteger(chunks, i)   # Enum
		if (b):
			a3, i = getFloats(chunks, i, 2)
		else:
			a3 = None
		return (name, c, t, a, [s], bsc, r, lst, a3), i
	raise Exception("Unknown BlendValue %s!" %(name))

def addSurfaceDefs(surface, defs):
	global _invSubTypTblSurfLst

	if (isinstance(surface, SurfaceSpline)):
		if (not hasattr(surface, 'ref')):
			if (surface.index not in _invSubTypTblSurfLst):
				defs.append(surface)
		for srf in surface.surfaces:
			addSurfaceDefs(srf, defs)

def addCurveSurfaceDefs(curve, defs):
	srf = getattr(curve, 'surface', None)
	addSurfaceDefs(srf, defs)
	lst = getattr(curve, 'surfaces', [])
	for srf in lst:
		addSurfaceDefs(srf, defs)

def getNameMatchAttributes():
	global _nameMtchAttr
	return _nameMtchAttr

def releaseMemory():
	global _dcIdxAttributes, _header

	clearEntities()
	initSatRefs()

	_dcIdxAttributes.clear()
	_header  = None

class BDY_GEOM(object):
	def __init__(self, svId):
		self.svId  = svId
		self.shape = None
	def build(self):
		if (self.shape is None):
			self.buildCurve()
		return self.shape
class BDY_GEOM_CIRCLE(BDY_GEOM):
	def __init__(self):
		super(BDY_GEOM_CIRCLE, self).__init__('circle')
		self.curve      = None
		self.twist      = (None, None)
		self.parameters = (MIN_0, MAX_2PI)
		self.sense      = 'forward'
	def buildCurve(self):
		if (not self.curve is None):
			u = self.parameters[0]
			v = self.parameters[1]
			self.shape = self.curve.build(u, v)
class BDY_GEOM_DEG(BDY_GEOM):
	def __init__(self):
		super(BDY_GEOM_DEG, self).__init__('deg')
		self.location = VEC(0.0, 0.0, 0.0)
		self.normal1  = VEC(1.0, 0.0, 0.0)
		self.normal2  = VEC(0.0, 1.0, 0.0)
	def buildCurve(self):
		self.shape = Part.Point(self.location).toShape()
class BDY_GEOM_PCURVE(BDY_GEOM):
	def __init__(self):
		super(BDY_GEOM_PCURVE, self).__init__('pcurve')
		self.surface      = None
		self.pcurve       = None
		self.sense        = 'forward'
		self.fittolerance = 0.0
	def buildCurve(self):
		self.shape = createBSplinesPCurve(self.pcurve, self.surface, self.sense)
class BDY_GEOM_PLANE(BDY_GEOM):
	def __init__(self):
		super(BDY_GEOM_PLANE, self).__init__('plane')
		self.normal     = VEC(0.0, 0.0, 1.0)
		self.parameters = (MIN_0, 1.0)
		self.curve      = None
	def buildCurve(self):
		if (not self.curve is None):
			u = self.parameters[0]
			v = self.parameters[1]
			self.shape = self.curve.build(u, v)
class LoftData(object):
	def __init__(self):
		self.surface = None
		self.bs2cur  = None
		self.e1      = TAG_FALSE
		self.type    = 213
		self.n       = 1
		self.m       = 1
		self.v       = []
		self.e2      = TAG_FALSE
class Skin(object):
	def __init__(self):
		self.a1   = [-1, -1, -1, -1]
		self.f    = MIN_0
		self.loft = []
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
	def readPoints3DList(self, count, chunks, index):
		self.uKnots, self.uMults, i = readKnotsMults(count, chunks, index)
		us = sum(self.uMults) - (self.uDegree - 1)
		self.poles   = [None for r in range(0, us)]
		self.weights = [1 for r in range(0, us)] if (self.rational) else None

		for u in range(0, us):
			self.poles[u], i = getLocation(chunks, i)
			if (self.rational): self.weights[u], i = getFloat(chunks, i)

		self.uKnots, self.uMults, self.uPeriodic = adjustMultsKnots(self.uKnots, self.uMults, self.uPeriodic, self.uDegree)
		return i
class BS3_Surface(BS3_Curve):
	def __init__(self, rational, uPeriodic, vPeriodic, uDegree, vDegree):
		super(BS3_Surface, self).__init__(rational, uPeriodic, uDegree)
		self.poles     = [[]]      # sequence of sequence ofVEC
		self.weights   = [[]]      # sequence of sequence float
		self.vMults    = ()        # tuple of int, ref. umults
		self.vKnots    = ()        # tuple of float
		self.vPeriodic = vPeriodic # boolean
		self.vDegree   = vDegree          # int
	def readPoints3DMap(self, countU, countV, chunks, index):
		# row definitions
		self.uKnots, self.uMults, i = readKnotsMults(countU, chunks, index)
		# column definitions
		self.vKnots, self.vMults, i = readKnotsMults(countV, chunks, i)

		us = sum(self.uMults) - (self.uDegree - 1)
		vs = sum(self.vMults) - (self.vDegree - 1)

		self.poles   = [[None for c in range(0, vs)] for r in range(0, us)]
		self.weights = [[1 for c in range(0, vs)] for r in range(0, us)] if (self.rational) else None
		for v in range(0, vs):
			for u in range(0, us):
				self.poles[u][v], i  = getLocation(chunks, i)
				if (self.rational): self.weights[u][v], i = getFloat(chunks, i)

		self.uKnots, self.uMults, self.uPeriodic = adjustMultsKnots(self.uKnots, self.uMults, self.uPeriodic, self.uDegree)
		self.vKnots, self.vMults, self.vPeriodic = adjustMultsKnots(self.vKnots, self.vMults, self.vPeriodic, self.vDegree)

		return i
class Helix(object):
	def __init__(self):
		self.radAngles = Interval(Range('I', 1.0), Range('I', 1.0))
		self.posCenter = CENTER
		self.dirMajor  = DIR_X
		self.dirMinor  = DIR_Y
		self.dirPitch  = DIR_Z
		self.facApex   = MIN_0
		self.vecAxis   = DIR_Z
	def __str__(self):
		return "%s %s %s %s %s %g %s" %(self.radAngles, self.posCenter, self.dirMajor, self.dirMinor, self.dirPitch
			, self.facApex, self.vecAxis)
	def	getPitch(self):
		return self.dirPitch.Length
	def	getHeight(self):
		angle = self.radAngles.getLimit()
		pitch = self.getPitch()
		return pitch * angle / 2.0 / pi
	def	getRadius(self):
		assert (isEqual1D(self.dirMajor.Length, self.dirMinor.Length)), 'Helix: elliptical helix not supported!'
		return self.dirMajor.Length
	def	getApexAngle(self):
		radApexAngle = atan2(self.facApex * self.getRadius(), self.getPitch())
		return degrees(radApexAngle)
	def isLeftHanded(self):
		return (self.vecAxis.cross(self.dirMajor).getAngle(self.dirMinor) < 0.1)
	def rotateShape(self, shape, vec_1, vec_2, vec_3):
		angle = degrees(vec_1.getAngle(vec_2))
		if (angle > 1e-5):
			axis = vec_1.cross(vec_2) if (angle != 180.0) else vec_3
			shape.rotate(PLC(CENTER, axis, angle))
	@staticmethod
	def calcSteps(a, b, numSegments = 6):
		startSegment = 0.05 # ~1 degree to smooth start
		steps = [a, a + startSegment]

		d = (b - a)
		step = d / int(ceil(numSegments * d / 2 / pi)) # number of segments per turn
		c = a
		while c < (b - startSegment):
			c += step
			steps.append(c)

		steps.insert(len(steps)-1, b - startSegment)

		return steps
	@staticmethod
	def calcPoint(u, min_U, a, r_maj, r_min, handed, pitch):
		delta_U = (u - min_U) / 2 / pi
		fac     = 1 + a * delta_U
		x       = r_maj * fac * cos(u)
		y       = r_min * fac * sin(u) * handed
		z       = pitch * delta_U
		return VEC(x, y, z)

	def build(self):
		min_U   = self.radAngles.getLowerLimit()
		max_U   = self.radAngles.getUpperLimit()
		r_maj   = self.dirMajor.Length
		r_min   = self.dirMinor.Length
		pitch   = self.dirPitch.Length
		steps_U = Helix.calcSteps(min_U, max_U)
		handed  = 1 if (self.isLeftHanded()) else -1
		points  = []

		for u in steps_U:
			c = Helix.calcPoint(u, min_U, self.facApex, r_maj, r_min, handed, pitch)
			points.append(c)

		# bring the helix into the correct position:
		helix = Part.BSplineCurve()
		helix.interpolate(points)
		self.rotateShape(helix, DIR_X, VEC(self.dirMajor.x, self.dirMajor.y, 0), DIR_Z)
		self.rotateShape(helix, DIR_Z, self.vecAxis, DIR_X)
		helix.translate(self.posCenter)
		return helix.toShape()

	def buildSurfaceCircle(self, r, min_V, max_V):
		min_U   = self.radAngles.getLowerLimit()
		max_U   = self.radAngles.getUpperLimit()
		r_maj   = self.dirMajor.Length
		r_min   = self.dirMinor.Length
		pitch   = self.dirPitch.Length
		steps_U = Helix.calcSteps(min_U, max_U, 8)
		steps_V = Helix.calcSteps(min_V, max_V, 6)
		handed  = 1 if (self.isLeftHanded()) else -1
		points  = []

		for u  in steps_U:
			c = Helix.calcPoint(u, min_U, self.facApex, r_maj, r_min, handed, pitch)
			circle = []
			m = MAT(cos(u), sin(u), 0, 0, -sin(u), cos(u), 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
			for v in steps_V:
				p = m.multiply(VEC(r * cos(v), 0, r * sin(v)))
				circle.append(p + c)
			points.append(circle)

		# bring the helix into the correct position:
		helix = Part.BSplineSurface()
		helix.interpolate(points)
		self.rotateShape(helix, DIR_X, VEC(self.dirMajor.x, self.dirMajor.y, 0), DIR_Z)
		self.rotateShape(helix, DIR_Z, self.vecAxis, DIR_X)
		helix.translate(self.posCenter)
		return helix.toShape()

class Range(object):
	def __init__(self, type, limit, scale = 1.0):
		self.type  = type
		self.limit = limit
		self.scale = scale
	def __str__(self): return 'I' if (self.type == 'I') else "F %g" %(self.getLimit())
	def __repr__(self): return 'I' if (self.type == 'I') else "%g" %(self.getLimit())
	def getLimit(self): return self.limit if (self.type == 'I') else self.limit * self.scale
class Interval(object):
	def __init__(self, upper, lower):
		self.lower = upper
		self.upper = lower
	def __str__(self): return "%s %s" %(self.lower, self.upper)
	def __repr__(self): return "[%r-%r]" %(self.lower, self.upper)
	def getLowerType(self):  return self.lower.type
	def getLowerLimit(self): return self.lower.getLimit()
	def getUpperType(self):  return self.upper.type
	def getUpperLimit(self): return self.upper.getLimit()
	def getLimit(self):      return self.getUpperLimit() - self.getLowerLimit()
class IndexMappings(object):
	def __init__(self):
		self.attributes = []
	def append(self, attr):
		self.attributes.append(attr)
	def __getTypedOwners__(self, ownerType):
		result = {}
		for a in self.attributes:
			owner = a.getOwner()
			if (owner.getType() == ownerType):
				if (owner.index not in result):
					result[owner.index] = owner
		return result.values()
	def getEdges(self):
		return self.__getTypedOwners__('edge')
	def getFaces(self):
		return self.__getTypedOwners__('face')
class AsmHeader(object): pass
class BeginOfAcisHistoryData(object): pass
class DeltaState(object): pass
class EndOfAcisHistorySection(object): pass
class EndOfAcisData(object): pass

# abstract super class
class Entity(object):
	def __init__(self):
		self._attrib = None
		self.entity  = None
		self.history = None

	def set(self, entity):
		try:
			references[entity.index] = self
			self._attrib, i = getRefNode(entity, 0, None)
			if (getVersion() > 6):
				self.history, i = getInteger(entity.chunks, i)
		except Exception as e:
			logError(traceback.format_exc())
		return i
	@property
	def index(self):  return -1   if (self.entity is None)  else self.entity.index
	def getType(self):   return -1   if (self.entity is None)  else self.entity.name
	@property
	def attrib(self): return None if (self._attrib is None) else self._attrib.node
	def __str__(self):   return "%s" % (self.entity)
	def __repr__(self): return self.__str__()
	def __lt__(self, other):
		return self.index < other.index
	def getAttribute(self, clsNames):
		a = self.attrib
		if (isString(clsNames)):
			names = [clsNames]
		else:
			names = clsNames

		while (a is not None) and (a.index >= 0):
			if (a.__class__.__name__ in names):
				return a
			a = a.getNext()
		return None

	def getName(self):
		a = self.getAttribute('AttribGenName')
		if (a is not None):
			return a.text
		return None

	def getColor(self):
		color = self.getAttribute(['AttribStRgbColor', 'AttribNamingMatchingNMxFFColorEntity', 'AttribADeskTrueColor'])
		return color
class EyeRefinement(Entity):
	def __init__(self): super(EyeRefinement, self).__init__()
class VertexTemplate(Entity):
	def __init__(self): super(VertexTemplate, self).__init__()
class Wcs(Entity):
	def __init__(self): super(Wcs, self).__init__()
class Transform(Entity):
	def __init__(self):
		super(Transform, self).__init__()
		self.affine = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
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
		self._next, i   = getRefNode(entity, i, 'lump')
		self._shell, i  = getRefNode(entity, i, 'shell')
		self._owner, i  = getRefNode(entity, i, 'body')
		self.unknown, i = getUnknownFT(entity.chunks, i)
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
		self._owner = None # The shell's lump
	def set(self, entity):
		i = super(Shell, self).set(entity)
		self._next, i  = getRefNode(entity, i, 'shell')
		self._shell, i = getRefNode(entity, i, None)
		self._face, i  = getRefNode(entity, i, 'face')
		if (getVersion() > 1.7):
			self._wire, i  = getRefNode(entity, i, 'wire')
		self._owner, i = getRefNode(entity, i, 'lump')
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
	def getLump(self):  return None if (self._owner is None) else self._owner.node
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
	def buildCoEdges(self):
		edges = []
		loop = self.getLoop()
		while (loop is not None):
			coedges = loop.getCoEdges()
			for index in coedges:
				coEdge = coedges[index]
				edge = coEdge.build()
				if (edge is not None):
					edges.append(edge)
			loop = loop.getNext()
		return edges
	def showEdges(self, edges):
		for edge in edges:
			Part.show(edge)
		return None
	def build(self):
		edges = self.buildCoEdges()
		s     = self.getSurface()
		if (s is not None):
			face = None
			surface = s.build() if (s is not None) else None
			if (surface is not None):
				if (len(edges) > 0):
					compound, elements = surface.generalFuse(edges)
					surface = eliminateOuterFaces(elements[0], edges)
				# edges can be empty because not all edges can be created right now :(
				return surface
			if (hasattr(s, 'type')):
				if (s.type != 'ref'):
					logWarning(u"    ... Don't know how to build surface '-%d %s::%s' - only edges displayed!", s.index, s.__class__.__name__, s.type)
			else:
				logWarning(u"    ... Don't know how to build surface '-%d %s' - only edges displayed!", s.index, s.__class__.__name__)
		return self.showEdges(edges)
	def getSurfaceRef(self):
		return getattr(self.getSurface(), 'ref', None)
	def getCoEdgeRefs(self):
		refs = []
		loop = self.getLoop()
		while (loop is not None):
			refs += loop.getCoEdgeRefs()
			loop = loop.getNext()
		return refs
	def getSurfaceRefs(self):
		refs = self.getCoEdgeRefs()
		ref  = self.getSurfaceRef()
		if (ref is not None):
			refs.append(ref)
		refs = list(set(refs))
		refs = sorted(refs)
		return refs
	def getSurfaceDefinitions(self):
		defs = []
		addSurfaceDefs(self.getSurface(), defs)
		loop = self.getLoop()
		while (loop is not None):
			defs += loop.getSurfaceDefinitions()
			loop = loop.getNext()
		attr = self.getAttribute('AttribNamingMatchingNMxFeatureOrientation')
		entity = getattr(attr, 'ref1', None)
		if (entity is not None):
			addCurveSurfaceDefs(entity.node, defs)
		entity = getattr(attr, 'ref2', None)
		if (entity is not None):
			addCurveSurfaceDefs(entity.node, defs)
		defs = sorted(defs)
		return defs
	def isCone(self):   return isinstance(self.getSurface(), SurfaceCone)
	def isMesh(self):   return isinstance(self.getSurface(), SurfaceMesh)
	def isPlane(self):  return isinstance(self.getSurface(), SurfacePlane)
	def isSphere(self): return isinstance(self.getSurface(), SurfaceSphere)
	def isSpline(self): return isinstance(self.getSurface(), SurfaceSpline)
	def isTorus(self):  return isinstance(self.getSurface(), SurfaceTorus)
	def getEdges(self):
		edges = []
		for loop in self.getLoops():
			edges += loop.getEdges()
		return edges
class Loop(Topology):
	def __init__(self):
		super(Loop, self).__init__()
		self._next   = None # The next loop
		self._coedge = None # The first coedge in the loop
		self._owner  = None # The first coedge in the face
	def set(self, entity):
		i = super(Loop, self).set(entity)
		self._next, i   = getRefNode(entity, i, 'loop')
		self._coedge, i = getRefNode(entity, i, 'coedge')
		self._owner, i  = getRefNode(entity, i, 'face')
		self.unknown, i = getUnknownFT(entity.chunks, i)
		if (getVersion() > 10.0):
			i += 1
		return i
	def getNext(self):   return None if (self._next is None)   else self._next.node
	def getCoEdge(self): return None if (self._coedge is None) else self._coedge.node
	def getFace(self):   return None if (self._owner is None)  else self._owner.node
	def getCoEdges(self):
		coedges = {}
		ce = self.getCoEdge()
		while (ce is not None):
			if (ce.index in coedges): break
			coedges[ce.index] = ce
			ce = ce.getNext()
		return coedges
	def getCoEdgeRefs(self):
		refs = []
		coedges = self.getCoEdges()
		for index in coedges:
			ce = coedges[index]
			srf = getattr(ce.getCurve(), 'surface', None)
			ref = getattr(srf, 'ref', None)
			if (ref is not None):
				refs.append(ref)
			e = ce.getEdge()
			if (e is not None):
				srf = getattr(e.getCurve(), 'surface', None)
				ref = getattr(srf, 'ref', None)
				if (ref is not None):
					refs.append(ref)
		return refs
	def getSurfaceDefinitions(self):
		defs = []
		coEdges = self.getCoEdges()
		for index in coEdges:
			ce = coEdges[index]
			addCurveSurfaceDefs(ce.getCurve(), defs)
			e = ce.getEdge()
			if (e is not None):
				addCurveSurfaceDefs(e.getCurve(), defs)
		return defs
	def getEdges(self):
		return [coEdge.getEdge() for coEdge in self.getCoEdges().values()]
class Wire(Topology):
	def __init__(self):
		super(Wire, self).__init__()
		self._next = None
		self._coedge = None
		self._owner = None
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
	def getOwner(self):  return None if (self._owner is None)  else self._owner.node
	def getCoEdges(self):
		coedges = {}
		ce = self.getCoEdge()
		index = -1 if (ce is None) else ce.index
		while (ce is not None):
			if (ce.index in coedges):
				break
			coedges[ce.index] = ce
			ce = ce.getNext()
		return coedges
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
	def set(self, entity):
		i = i = super(CoEdge, self).set(entity)
		self._next, i     = getRefNode(entity, i, 'coedge')
		self._previous, i = getRefNode(entity, i, 'coedge')
		self._partner, i  = getRefNode(entity, i, 'coedge')
		self._edge, i     = getRefNode(entity, i, 'edge')
		self.sense, i     = getSense(entity.chunks, i)
		self._owner, i    = getRefNode(entity, i, None) # can be either Loop or Wire
		if (entity.chunks[i].tag != TAG_ENTITY_REF):
			i += 1
		self._curve, i    = getRefNode(entity, i, 'pcurve')
		return i
	def getNext(self):     return None if (self._next is None)     else self._next.node
	def getPrevious(self): return None if (self._previous is None) else self._previous.node
	def getPartner(self):  return None if (self._partner is None)  else self._partner.node
	def getEdge(self):     return None if (self._edge is None)     else self._edge.node
	def getOwner(self):    return None if (self._owner is None)    else self._owner.node
	def getCurve(self):    return None if (self._curve is None)    else self._curve.node
	def build(self, ):
		e = self.getEdge()
		c = e.getCurve()
		if (c is not None):
			p1 = e.getStart() if (e.sense == 'forward') else e.getEnd()
			p2 = e.getEnd() if (e.sense == 'forward') else e.getStart()
			return c.build(p1, p2)
		return None
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
class Edge(Topology):
	def __init__(self):
		super(Edge, self).__init__()
		self._start = None # The start vertex
		self._end   = None # The end vertex
		self._owner = None # The edge's coedge
		self._curve = None # Lying on one the Adjacent faces
		self.sense  = 'forwared'
		self.text   = ''
	def set(self, entity):
		i = super(Edge, self).set(entity)
		self._start, i = getRefNode(entity, i, 'vertex')
		if (getVersion() > 4.0):
			self.parameter1, i = getFloat(entity.chunks, i)
		else:
			self.parameter1 = 0.0
		self._end, i   = getRefNode(entity, i, 'vertex')
		if (getVersion() > 4.0):
			self.parameter2, i = getFloat(entity.chunks, i)
		else:
			self.parameter2 = 1.0
		self._owner, i = getRefNode(entity, i, 'coedge')
		self._curve, i = getRefNode(entity, i, 'curve')
		self.sense, i  = getSense(entity.chunks, i)
		if (getVersion() > 5.0):
			self.text, i = getText(entity.chunks, i)
		self.unknown, i = getUnknownFT(entity.chunks, i)
		return i
	def getStart(self):  return None if (self._start is None) else self._start.node.getPosition()
	def getEnd(self):    return None if (self._end   is None) else self._end.node.getPosition()
	def getParent(self): return None if (self._owner is None) else self._owner.node
	def getCurve(self):  return None if (self._curve is None) else self._curve.node
	def getPoints(self):
		points = []
		ptStart = None if (self._start is None) else self._start.node
		if (ptStart is not None): points.append(ptStart.getPosition())
		ptEnd = None if (self._end   is None) else self._end.node
		if ((ptEnd is not None) and (ptEnd.index != ptStart.index)): points.append(ptEnd.getPosition())
		return points
class EdgeTolerance(Edge):
	def __init__(self):
		super(EdgeTolerance, self).__init__()
		self.tolerance = 0.0
	def set(self, entity):
		i = super(EdgeTolerance, self).set(entity)
		return i
class Vertex(Topology):
	def __init__(self):
		super(Vertex, self).__init__()
		self._owner = None # One of the vertex' owners
		self._point = None # The vertex' location
		self.count  = -1   # Number of edges using this vertex
	def set(self, entity):
		i = super(Vertex, self).set(entity)
		self._owner, i = getRefNode(entity, i, 'edge')
		# inventor-version: 2010 -> workaround
		if (entity.chunks[i].tag != 0xC):
			i += 1
		self._point, i  = getRefNode(entity, i, 'point')
		return i
	def getParent(self):   return None if (self._owner is None) else self._owner.node
	def getPoint(self):    return None if (self._point is None) else self._point.node
	def getPosition(self):
		p = self.getPoint()
		return None if (p is None) else p.position
class VertexTolerance(Vertex):
	def __init__(self):
		super(VertexTolerance, self).__init__()
		self.tolerance = 0.0
	def set(self, entity):
		i = super(VertexTolerance, self).set(entity)
		self.tolerance, i = getFloat(entity.chunks, i)
		return i

# abstract super class for all geometries
class Geometry(Entity):
	def __init__(self, name):
		super(Geometry, self).__init__()
		self.__name__ = name
	def set(self, entity):
		i = super(Geometry, self).set(entity)
		if (getVersion() > 10.0):
			i += 1 # skip ???
		if (getVersion() > 6.0):
			i += 1 # skip ???
		return i
	def __repr__(self):
		if (self.entity is None):
			if (hasattr(self, 'ref')):
				return "%s { ref %d }" %(self.__name__, self.ref)
			if (hasattr(self, 'type')):
				return "%s { %s ... }" %(self.__name__, self.type)
			return "%s { ... }" %(self.__name__)
		return super(Geometry, self).__repr__()
class Curve(Geometry):
	def __init__(self, name):
		super(Curve, self).__init__(name)
		self.shape = None
	def setSubtype(self, chunks, index):
		return index
	def set(self, entity):
		i = super(Curve, self).set(entity)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self, start, end): # by default: return a line-segment!
		logWarning(u"    ... '%s' not yet supported - forced to straight-curve!", self.__class__.__name__)
		if (self.shape is None):
			# force everything else to straight line!
			if (isinstance(start, VEC)):
				self.shape = createLine(start, end)
		return self.shape
	def __str__(self):  return self.__class__.__name__

class CurveComp(Curve):    # compound curve "compcurv-curve"
	def __init__(self):
		super(CurveComp, self).__init__('compcurv')
	def setSubtype(self, chunks, index):
		return index
class CurveDegenerate(Curve):    # degenerate curve "degenerate-curve"
	def __init__(self):
		super(CurveDegenerate, self).__init__('degenerate')
	def setSubtype(self, chunks, index):
		self._start, i = getLocation(chunks, index)
		r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		return i
class CurveEllipse(Curve): # ellyptical curve "ellipse-curve"
	def __init__(self):
		super(CurveEllipse, self).__init__('ellipse')
		self.center = CENTER
		self.axis   = DIR_Z
		self.major  = DIR_X
		self.ratio  = MIN_0
		self.range  = Interval(Range('I', MIN_0), Range('I', MAX_2PI))
	def __str__(self): return "Curve-Ellipse: center=%s, dir=%s, major=%s, ratio=%g, range=%s" %(self.center, self.axis, self.major, self.ratio, self.range)
	def setSubtype(self, chunks, index):
		self.center, i = getLocation(chunks, index)
		self.axis, i   = getVector(chunks, i)
		self.major, i  = getLocation(chunks, i)
		self.ratio, i  = getFloat(chunks, i)
		self.range, i  = getInterval(chunks, i, MIN_0, MAX_2PI, 1.0)
		return i
	def build(self, start, end):
		if (self.ratio == 1):
			ellipse = createCircle(self.center, self.axis, self.major)
		else:
			ellipse = createEllipse(self.center, self.axis, self.major, self.ratio)
		if (start != end):
			if (isinstance(start, VEC)):
				a = ellipse.parameter(start)
			else:
				a = start
			if (isinstance(end, VEC)):
				b = ellipse.parameter(end)
			else:
				b = end
			self.range = Interval(Range('F', a), Range('F', b))
			if (self.ratio == 1):
				ellipse = Part.ArcOfCircle(ellipse, a, b)
			else:
				if (self.ratio < 0):
					ellipse = Part.ArcOfEllipse(ellipse, a, b)
				else:
					ellipse = Part.ArcOfEllipse(ellipse, (a + pi/2) % (2*pi), (b + pi/2) % (2*pi))
		return ellipse.toShape()
class CurveInt(Curve):     # interpolated ('Bezier') curve "intcurve-curve"
	def __init__(self, name = ''):
		super(CurveInt, self).__init__(name + 'intcurve')
		self.sense    = 'forward' # The IntCurve's reversal flag
		self.range    = Interval(Range('I', MIN_INF), Range('I', MAX_INF))
		self.type     = ''
		self.surfaces = []
		self.curve    = None
		self.ignore   = False
	def getShape(self):
		if (self.shape is None):
			if (hasattr(self, 'curves')):
				curve = self.curves[0].getShape()
				others = []
				for c in self.curves[1:]:
					shp = c.getShape()
					if (shp is not None):
						others.append(shp)
				self.shape = curve.multifuse(others)
			elif (hasattr(self, 'surfaceProjection')):
				(surface, pcurve) = self.surfaceProjection
				if (self.singularity == 'summary'):
					# try to create a curve from a surface projection
					self.shape = createBSplinesPCurve(pcurve, surface, self.sense)
			else:
				if (type(self.curve) == int):
					self.curve = getSubtypeNodeCurve(self.curve)
				if (isinstance(self.curve, Curve)):
					self.shape = self.curve.build(None, None)
		return self.shape
	def setProjectionSurface(self, surface, curve):
		if (surface is not None):
			if (curve is not None):
				self.surfaceProjection = (surface, curve)
				return True
		return False
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
			if (getVersion() >= 17.0):
				i += 1 # 3
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
			raise Exception("Unknown Surface-singularity '%s'" %(self.singularity))
		return i
	def setSurfaceCurve(self, chunks, index, inventor):
		i = self.setCurve(chunks, index)
		surface1, i = readSurface(self, chunks, i)
		surface2, i = readSurface(self, chunks, i)
		curve1, i   = readBS2Curve(chunks, i)
		curve2, i   = readBS2Curve(chunks, i)
		if (getVersion() > 15.0):
			i += 2
		range2, i   = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		if (getVersion() >= 2.0):
			a1, i       = getFloatArray(chunks, i)
			a2, i       = getFloatArray(chunks, i)
			a3, i       = getFloatArray(chunks, i)

		if (not self.setProjectionSurface(surface1, curve1)):
			self.setProjectionSurface(surface2, curve2)

		return i
	def setBlend(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		txt, i      = getText(chunks, i)
		return i
	def setBlendSprng(self, chunks, index, inventor):
		i = self.setCurve(chunks, index)
		surface1, i = readSurface(self, chunks, i)
		if (surface1 is None):
			ruS1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
			rvS1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		surface2, i = readSurface(self, chunks, i)
		if (surface2 is None):
			ruS2, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
			rvS2, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		curve1, i   = readBS2Curve(chunks, i)
		if (curve1 is None):
			ruC1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		curve2, i   = readBS2Curve(chunks, i)
		ruC2, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		if (getVersion() >= 2.0):
			a1, i       = getFloatArray(chunks, i)
			a2, i       = getFloatArray(chunks, i)
			a3, i       = getFloatArray(chunks, i)

		if (inventor):
			i += 1
			direction, i = getCurvDir(chunks, i)
		else:
			direction, i = getText(chunks, i)

		if (not self.setProjectionSurface(surface1, curve1)):
			self.setProjectionSurface(surface2, curve2)
		return i
	def setComp(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		a4, i       = getFloatArray(chunks, i)
		count, i    = getInteger(chunks, i)
		a5, i       = getFloats(chunks, i, count)
		if (inventor):
			i += 1 # 0x0A
		self.curves = []
		for k in range(0, count):
			c, i = readCurve(chunks, i)
			self.curves.append(c)
		return i
	def setDefm(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		if (inventor):
			x3, i = getFloat(chunks, i)
		bend, i = readCurve(chunks, i)
		return i
	def setExact(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		if (getVersion() >= 2.0):
			if (inventor):
				x3, i = getFloat(chunks, i)
			if (getVersion() > 15.0):
				i += 2
			unknown, i = getUnknownFT(chunks, i)
			range2, i  = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def setHelix(self, chunks, index, inventor):
		self.helix = Helix()
		self.helix.radAngles, i = getInterval(chunks, index, MIN_0, MAX_2PI, 1.0)
		self.helix.posCenter, i = getLocation(chunks, i)        # axis start
		self.helix.dirMajor, i  = getLocation(chunks, i)        # profile's ellipse major radius
		self.helix.dirMinor, i  = getLocation(chunks, i)        # profile's ellipse minor radius
		self.helix.dirPitch, i  = getLocation(chunks, i)        # profile's ellipse center
		self.helix.facApex, i   = getFloat(chunks, i)           # pitch ???
		self.helix.vecAxis, i   = getVector(chunks, i)        # axis end
		surface1, i = readSurface(self, chunks, i)  # None
		surface2, i = readSurface(self, chunks, i)  # None
		curve1, i   = readBS2Curve(chunks, i) # None
		curve2, i   = readBS2Curve(chunks, i) # None
		self.shape = self.helix.build()
		if (not self.setProjectionSurface(surface1, curve1)):
			self.setProjectionSurface(surface2, curve2)
		return i
	def setInt(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		x, i = getFloat(chunks, i)
		return i
	def setLaw(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
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
		while (isString(chunks[i].val)):
			l, i  = readLaw(chunks, i) # null_law
			subLaws.append(l)
		subLaws = []
		laws.append(subLaws)
		while (i < len(chunks)):
			n, i = getInteger(chunks, i)
			l, i = readLaw(chunks, i)
			subLaws.append(l)
			for j in range(n-1):
				l, i = readLaw(chunks, i)
				subLaws.append(l)
			i = len(chunks)
		return i
	def setOff(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		if (inventor):
				i += 1
		if (getVersion() > 22.0):
			i += 3 # -1 none F
		offsets, i = getFloats(chunks, i, 2)
		return i
	def setOffset(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		if (inventor):
			i += 1
		curve, i = readCurve(chunks, i)
		return i
	def setOffsetSurface(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		if (inventor):
			i += 1
		rngU, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		rngV, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		curve, i = readCurve(chunks, i)
		rng, i  = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		# x, y, z ???
		return i
	def setParameter(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		if (getVersion() > 15.0):
			i += 1
		if (not inventor):
			if (getVersion() > 17.0):
				i += 2 # 'none', F ???
			txt, i = getText(chunks, i)
		return i
	def setParameterSilhouette(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		if (inventor):
			i1, i = getInteger(chunks, i)
		v1, i = getVector(chunks, i) # direction
		f1, i = getFloat(chunks, i)
		return i
	def setProject(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		if (inventor):
			i += 1
		curve, i = readCurve(chunks, i)
		if (inventor):
			i += 1
		return i
	def setSSS(self, chunks, index, inventor):
		i = index
		i = self.setSurfaceCurve(chunks, i, inventor)
		n, i = getInteger(chunks, i)
		s, i = readSurface(self, chunks, i)
		p, i = readBS2Curve(chunks, i)
		return i

	def setRef(self, chunks, index):
		self.curve, i = getInteger(chunks, index)
		self.ref = self.curve
		return i
	def setSurface(self, chunks, index, inventor):
		i = self.setSurfaceCurve(chunks, index, inventor)
		return i
	def setBulk(self, chunks, index):
		self.type, i = getValue(chunks, index)

		if (self.type == 'ref'):               return self.setRef(chunks, i)

		try:
			prm = CURVE_SET_DATA[self.type]
			setCurveData = getattr(self, prm[0])
			return setCurveData(chunks, i + prm[1], prm[2])
		except KeyError as ke:
			raise Exception("Curve-Int: unknown subtype '%s'!" %(self.type))
	def setSubtype(self, chunks, index):
		self.sense, i  = getSense(chunks, index)
		block, i      = getBlock(chunks, i)
		addSubtypeNodeCurve(self)
		self.setBulk(block, 1)
		self.range, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def build(self, start, end):
		if (self.shape is None) and not self.ignore:
			self.ignore = True # Don't try to create me more than once
			if (hasattr(self, 'curves')):
				curve = self.curves[0].build(None, None)
				others = []
				for c in self.curves[1:]:
					shp = c.build(None, None)
					if (shp): others.append(shp)
				self.shape = curve.multifuse(others)
			else:
				while (type(self.curve) == int):
					self.curve = getSubtypeNodeCurve(self.curve)
				if (isinstance(self.curve, Curve)):
					self.shape = self.curve.build(start, end)
		return self.shape
class CurveIntInt(CurveInt):  # interpolated int-curve "intcurve-intcurve-curve"
	def __init__(self):
		super(CurveIntInt, self).__init__('intcurve-')
		self.sense = 'forward' # The IntCurve's reversal flag
		self.range = Interval(Range('I', MIN_INF), Range('I', MAX_INF))
		self.type  = ''
		self.curve = None
	def setLaw(self, chunks, index, inventor):
		i = self.setCurve(chunks, index)
		return i
	def setBulk(self, chunks, index):
		self.type, i = getValue(chunks, index)
		if (self.type == 'lawintcur'):        return self.setLaw(chunks, i, False)
		if (self.type == 'law_int_cur'):      return self.setLaw(chunks, i + 1, True)
		logError(u"    Curve-Int-Int: unknown subtype %s !", self.type)
		return self.setCurve(chunks, i)
class CurveP(Curve):       # projected curve "pcurve" for each point in CurveP: point3D = surface.value(u, v)
	'''An approximation to a curve lying on a surface, defined in terms of the surface's u-v parameters.'''
	def __init__(self):
		super(CurveP, self).__init__('pcurve')
		self.type     = -1    # The PCurve's type
		self.sense    = 'forward'
		self.pcurve   = None
		self.surfaces = []
	def setExpPar(self, chunks, index):
		i = index if (getVersion() < 25.0) else index + 1
		self.pcurve, i = readBS2Curve(chunks, i)
		tolerance, i = getFloat(chunks, i)
		if (getVersion() > 15.0): i += 1
		self.surface, i = readSurface(self, chunks, i)
		self.type = 'exppc'
		return i
	def setImpPar(self, chunks, index):
		self.sense, i  = getSense(chunks, index)
		block, i      = getBlock(chunks, i)
		self.curve = CurveInt()
		self.curve.setBulk(block, 1)
		self.type = 'imppc'
		return i
	def setRef(self, chunks, index):
		self.pcurve, i = getInteger(chunks, index)
		self.ref = self.pcurve
		self.type = 'ref'
		return i
	def setBulk(self, chunks, index):
		self.type, i = getValue(chunks, index)
		try:
			prm = PCURVE_SET_DATA[self.type]
			fkt = getattr(self, prm)
			return fkt(chunks, i)
		except KeyError as ke:
			raise Exception("PCurve: unknown subtype '%s'!" %(self.type))
	def setSubtype(self, chunks, index):
		self.sense, i = getSense(chunks, index)
		block, i = getBlock(chunks, i)
		addSubtypeNodePCurve(self)
		self.setBulk(block, 1)
		self.u, i = getFloat(chunks, i)
		self.v, i = getFloat(chunks, i)
		return i
	def set(self, entity):
		i = super(Curve, self).set(entity)
		self.type, i = getInteger(entity.chunks, i)
		if (self.type == 0):
			i = self.setSubtype(entity.chunks, i)
		else:
			self.pcurve, i = getRefNode(entity, i, 'curve')
			self.u, i = getFloat(entity.chunks, i)
			self.v, i = getFloat(entity.chunks, i)
			self.type = 'ref'
		return i
	def build(self, start, end):
		if (self.shape is None):
			if (self.type == 'ref'):
				if (type(self.pcurve) == int):
					self.pcurve = getSubtypeNodePCurves(self.pcurve)
				if (isinstance(self.pcurve, CurveP)):
					self.shape = self.pcurve.build(start, end)
			elif (self.type == 'exppc'):
				self.shape = createBSplinesPCurve(self.pcurve, self.surface, self.sense)
		return self.shape
class CurveStraight(Curve):# straight curve "straight-curve"
	def __init__(self):
		super(CurveStraight, self).__init__('straight')
		self.root  = CENTER
		self.dir   = CENTER
		self.range = Interval(Range('I', MIN_INF), Range('I', MAX_INF))
	def __str__(self): return "Line: root=%s, dir=%s, range=%s" %(self.root, self.dir, self.range)
	def setSubtype(self, chunks, index):
		self.root, i  = getLocation(chunks, index)
		self.dir, i   = getVector(chunks, i)
		self.range, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def build(self, start, end):
		if (type(start) == float) and (type(end) == float):
			line = Part.Line(self.root, self.root + self.dir)
			start = line.value(start)
			end = line.value(end)
		return createLine(start, end)
class Surface(Geometry):
	def __init__(self, name):
		super(Surface, self).__init__(name)
		self.shape = None
		self.type  = name
	def setSubtype(self, chunks, index):
		return index
	def set(self, entity):
		i = super(Surface, self).set(entity)
		i = self.setSubtype(entity.chunks, i)
		return i
	def build(self): return None
class SurfaceCone(Surface):
	def __init__(self):
		super(SurfaceCone, self).__init__('cone')
		self.center = CENTER
		self.axis   = DIR_Z
		self.major  = DIR_X
		self.ratio  = 1.0
		self.range  = Interval(Range('I', MIN_INF), Range('I', MAX_INF))
		self.sine   = 0.0
		self.cosine = 0.0
		self.scale  = 1.0
		self.sense  = 'forward'
		self.urange = Interval(Range('I', MIN_0), Range('I', MAX_2PI))
		self.vrange = Interval(Range('I', MIN_INF), Range('I', MAX_INF))
	def __str__(self): return "Surface-Cone: center=%s, axis=%s, radius=%g, ratio=%g, semiAngle=%g" %(self.center, self.axis, self.major.Length, self.ratio, degrees(asin(self.sine)))
	def setSubtype(self, chunks, index):
		self.center, i = getLocation(chunks, index) # Cartesian Point 'Origin'
		self.axis, i   = getVector(chunks, i)       # Direction 'Center Axis'
		self.major, i  = getLocation(chunks, i)     # Direction 'Ref Axis'
		self.ratio, i  = getFloat(chunks, i)
		self.range, i  = getInterval(chunks, i, MIN_INF, MIN_INF, getScale())
		self.sine, i   = getFloat(chunks, i)
		self.cosine, i = getFloat(chunks, i)
		if (getVersion() >= ENTIY_VERSIONS.get('CONE_SCALING_VERSION')):
			self.r1, i = getLength(chunks, i)
		else:
			self.r1 = self.major.Length
		self.sense, i  = getSense(chunks, i)
		self.urange, i = getInterval(chunks, i, MIN_0, MAX_2PI, 1.0)
		self.vrange, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		if (self.sine == 0.):
			self.apex = None
		else:
			h = self.major.Length / tan(asin(self.sine))
			self.apex = self.center - self.axis * h
		return i
	def build(self):
		if (self.shape is None):
			if (isEqual1D(self.sine, 0.)): # 90 Deg
				# Workaround: create ellipse and extrude in both directions
				ellipse = createEllipse(self.center, self.axis, self.major, self.ratio)
				# make a gigantic extrusion as it will be beautyfied later
				if (ellipse):
					cyl = ellipse.toShape().extrude((2*MAX_LEN) * self.axis)
					cyl.translate((-MAX_LEN) * self.axis)
					self.shape = cyl.Faces[0]
			else:
				# Workaround: can't generate Part.Cone!
				l = Part.Line(self.apex, self.center + self.major)
				e = Part.LineSegment(self.apex, l.value(MAX_LEN)).toShape()
				if (self.ratio != 1):
					# TODO: apply scaling for ratios != 1.0!
					logWarning(u"    ... Can't create cone surface with elliptical base - skipped!")
				else:
					self.shape = e.revolve(self.center, self.axis, 360.0)
		return self.shape
class SurfaceMesh(Surface):
	def __init__(self):
		super(SurfaceMesh, self).__init__('mesh')
	def setSubtype(self, chunks, index):
		# TODO: missing example for mesh-surface
		return index
class SurfacePlane(Surface):
	def __init__(self):
		super(SurfacePlane, self).__init__('plane')
		self.root     = CENTER
		self.normal   = DIR_Z
		self.uvorigin = CENTER
		self.sensev   = 'forward_v'
		self.urange   = Interval(Range('I', MIN_INF), Range('I', MAX_INF))
		self.vrange   = Interval(Range('I', MIN_INF), Range('I', MAX_INF))
	def __str__(self): return "Surface-Plane: root=%s, normal=%s, uvorigin=%s" %(self.root, self.normal, self.uvorigin)
	def setSubtype(self, chunks, index):
		self.root, i     = getLocation(chunks, index)
		self.normal, i   = getVector(chunks, i)
		self.uvorigin, i = getLocation(chunks, i)
		self.sensev, i   = getSensev(chunks, i)
		self.urange, i   = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		self.vrange, i   = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def build(self):
		if (self.shape is None):
			plane = Part.Plane(self.root, self.normal)
			self.shape = plane.toShape()
		return self.shape
class SurfaceSphere(Surface):
	def __init__(self):
		super(SurfaceSphere, self).__init__('sphere')
		self.center   = CENTER
		self.radius   = 0.0
		self.uvorigin = CENTER
		self.pole     = DIR_Z
		self.sensev   = 'forward_v'
		self.urange   = Interval(Range('I', MIN_0), Range('I', MAX_2PI))
		self.vrange   = Interval(Range('I', MIN_PI2), Range('I', MAX_PI2))
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
		super(SurfaceSpline, self).__init__('spline')
		self.surface = None
		self.surfaces = []
	def _readBlendSurface(self, chunks, index, inventor):
		name, i    = getValue(chunks, index)
		surface, i = readSurface(self, chunks, i)
		curve, i   = readCurve(chunks,i)
		bs, i      = readBS2Curve(chunks, i) # nullbs
		v, i       = getLocation(chunks, i)
		if (inventor):
			bs, i = readBS2Curve(chunks, i) # nullbs
			f, i  = getFloat(chunks, i)
			bs, i = readBS2Curve(chunks, i) # nullbs
		return (name, surface, curve, bs, v), i
	def _readLoftData(self, chunks, index):
		ld = LoftData()
		ld.surface, i = readSurface(self, chunks, index)
		ld.bs2cur, i  = readBS2Curve(chunks, i)
		ld.e1, i      = getEnum(chunks, i)
		subdata, i    = readLofSubdata(chunks, i)
		(ld.type, n, m, v) = subdata
		ld.e2, i      = getEnum(chunks, i)
		if (ld.e2 == TAG_TRUE):
			ld.dir, i = getVector(chunks, i)
		return ld, i
	def _readLoftProfile(self, chunks, index, inventor):
		i = index
		if (inventor):
			m, i = getInteger(chunks, i)
		else:
			m = 1
		section = []
		for l in range(0, m):
			if (inventor):
				t, i = getInteger(chunks, i)
			else:
				t = 0
			ck, i = readCurve(chunks, i)
			if (inventor):
				lk, i = self._readLoftData(chunks, i)
			else:
				lk = None
			section.append((t, ck, lk))
		return section, i
	def _readLoftPath(self, chunks, index):
		cur, i = readCurve(chunks, index)
		n, i = getInteger(chunks, i)
		paths = []
		for k in range(0, n):
			bs3, i = readBS3Curve(chunks, i)
			paths.append(bs3)
		f, i = getInteger(chunks, i)
		return (cur, paths, f), i
	def _readLofSection(self, chunks, index, inventor):
		n, i = getInteger(chunks, index)
		loft = []
		for k in range(0, n):
			fk, i = getFloat(chunks, i)
			profile, i = self._readLoftProfile(chunks, i, inventor)
			if (inventor):
				path, i = self._readLoftPath(chunks, i)
			else:
				path = None
			loft.append((fk, profile, path))
		return loft, i
	def _readRbBlend(self, chunks, index, inventor):
		txt, i = getText(chunks, index)
		srf, i = readSurface(self, chunks, i)
		cur, i = readCurve(chunks, i)
		bs2, i = readBS2Curve(chunks, i)
		vec, i = getVector(chunks, i)
		if (inventor):
			dummy, i = readBS2Curve(chunks, i)
			spline, tol, i = readSplineSurface(chunks, i, False)
			return (txt, srf, cur, bs2, vec, (dummy, spline, tol)), i
		return (txt, srf, cur, bs2, vec, None), i
	def _readScaleClLoft(self, chunks, index):
		if (chunks[index].tag in [TAG_TRUE, TAG_FALSE]):
			## FIXME!
			return None, index
		n, i = getInteger(chunks, index)
		lofts = []
		for k in range(0, n):
			nk, i = getInteger(chunks, i)
			ck, i = readCurve(chunks, i)
			lk, i = self._readLoftData(chunks, i)
			lofts.append([nk, ck, lk])
		if (not chunks[i].tag in [TAG_UTF8_U8, TAG_IDENT, TAG_SUBIDENT]):
			## FIXME!
			return None, index
		cur, i = readCurve(chunks, i)
		n, i = getInteger(chunks, i) # 1
		bs3 = []
		for k in range(0, n):
			bs3c, i = readBS3Curve(chunks, i)
			bs3.append(bs3c)
		arr, i = getIntegers(chunks, i, 2) # BS3_CURVE,
		return (lofts, cur, bs3, arr), i
	def _readSkin(self, chunks, index, inventor):
		skin = Skin()
		skin.a1, i   = getIntegers(chunks, index, 4)
		skin.f1, i   = getFloat(chunks, i)
		if (inventor):
			n, i = getInteger(chunks, i)
			if (not chunks[i].tag in [TAG_UTF8_U8, TAG_IDENT, TAG_SUBIDENT]):
				for k in range(0, n):
					i += 1
					curve, i = readCurve(chunks, i)
					loftdata, i = self._readLoftData(chunks, i)
					skin.loft.append((curve, loftdata))
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
			skin.surf, i = readSurface(self, chunks, i)
		skin.f2, i    = getFloat(chunks, i)
		skin.law, i  = readFormula(chunks, i)
		skin.pcur, i = readCurve(chunks, i)
		return skin, i
	def _readBoundaryGeometry(self, chunks, index, inventor):
		svId,           i = getText(chunks, index)        # boundary sv id
		vbl = VBL_CLASSES[svId]()
		vbl.type,       i = getVblType(chunks, i)         #
		vbl.magic,      i = getLocation(chunks, i)        # magic
		vbl.uSmoothing, i = getCircleSmoothing(chunks, i) # u smoothing
		vbl.vSmoothing, i = getCircleSmoothing(chunks, i) # v smoothing
		vbl.fullness,   i = getFloat(chunks, i)           # fullness
		if (svId == 'circle'):
			vbl.curve, i = readCurve(chunks, i)
			subType, i = getVblCirleType(chunks, i)
			if (subType== 'circle'):
				vbl.twist = (None, None)
			elif (subType == 'ellipse'):
				v1, i = getLocation(chunks, i)
				vbl.twist = (v1, None)
			elif (subType == 'unknown'):
				v1, i = getLocation(chunks, i)
				v2, i = getLocation(chunks, i)
				vbl.twist = (v1, v2)
			else:
				raise Exception("Unknown VBL-Circle:form '%s'" %(subType))
			vbl.parameters, i = getFloats(chunks, i, 2)
			vbl.sense, i  = getSense(chunks, i)
		elif (svId == 'deg'): # degenerated curve (e.g. cone's Apex)
			vbl.location, i = getLocation(chunks, i)
			vbl.normal1, i = getVector(chunks, i)
			vbl.normal2, i = getVector(chunks, i)
		elif (svId == 'pcurve'):
			vbl.surface, i       = readSurface(self, chunks, i)
			vbl.pcurve, i        = readBS2Curve(chunks, i)
			vbl.sense, i         = getSense(chunks, i)
			vbl.fittolerance, i  = getFloats(chunks, i, 1)
		elif (svId == 'plane'):
			vbl.normal, i     = getVector(chunks, i)
			vbl.parameters, i = getFloats(chunks, i, 2)
			vbl.curve, i      = readCurve(chunks, i)
		else:
			raise Exception("Unknown VBL-type '%s'" %(self.t))
		return vbl, i
	def setSurfaceShape(self, chunks, index, inventor):
		spline, self.tolerance, i = readSplineSurface(chunks, index, True)
		self.shape = createBSplinesSurface(spline)
		if (getVersion() >= 2.0):
			arr, i  = readArrayFloats(chunks, i, inventor)
		return i
	def setBlendSupply(self, chunks, index, inventor):
		bs1, i  = self._readBlendSurface(chunks, index, inventor)
		bs2, i  = self._readBlendSurface(chunks, i, inventor)
		if (getVersion() > 22.0):
			i += 2 # 122, -1
		cur1, i = readCurve(chunks, i)
		if (getVersion() > 22.0):
			curT1, i = readCurve(chunks, i)
			curT2, i = readCurve(chunks, i)
			curT3, i = readCurve(chunks, i)
			curT4, i = readCurve(chunks, i)

		tol1, i = getFloats(chunks, i, 2)   # 0, 0
		r1  , i = getVarRadius(chunks, i)   # 0 = single_radius, 1 = two_radii
		bv1 , i = getBlendValues(chunks, i)
		if (r1 == 'two_radii'):
			bv2 , i  = getBlendValues(chunks, i)
			if (chunks[i].val in [3, 'rounded_chamfer']):
				vc  , i  = getVarChamfer(chunks, i)
				ct  , i  = getChamferType(chunks, i)
				bv3 , i  = getBlendValues(chunks, i)
			else:
				vc  = None
				ct  = False
				bv3 = None
		elif (r1 == 'single_radius'):
			if (chunks[i].val == 7): # ???
				ut1, i = getValue(chunks, i)
				uv1, i = getFloats(chunks, i, 2)
		rU, i   = getInterval(chunks, i, 0, 1, 1.0)
		rV, i   = getInterval(chunks, i, 0, 1, 1.0)
		j, i    = getInteger(chunks, i)      # 1
		f, i    = getFloat(chunks, i)        #
		s, i    = getLength(chunks, i)       #

		if (getVersion() > 22.0):
			i += 1 # T

		k, i    = getInteger(chunks, i)      # 1
		i = self.setSurfaceShape(chunks, i, inventor)
		if (inventor): a, i = getIntegers(chunks, i, 3) # 0 0 0
		cur2, i = readCurve(chunks, i)
		c   , i = getConvexity(chunks, i)   # 0x0A = convex
		rb  , i = getRenderBlend(chunks, i) # 0x0A = rb_envelope, 0x0B = rb_snapshop
		if (inventor):
			r, i  = getInterval(chunks, i, 0.0, 1.0, 1.0)
			bc1, i = readBS3Curve(chunks, i)
			bc2, i = readBS2Curve(chunks, i)  # nullbs
		return i
	def setClLoft(self, chunks, index, inventor):
		i = self.setSurfaceShape(chunks, index, inventor)
		scl1, i = self._readScaleClLoft(chunks, i)
		scl2, i = self._readScaleClLoft(chunks, i)
		scl3, i = self._readScaleClLoft(chunks, i)
		scl4, i = self._readScaleClLoft(chunks, i)
		chunk = chunks[i]
		if (isinstance(chunk, AcisLongChunk)):
			scl5, i = self._readScaleClLoft(chunks, i)
		e1, i = getEnum(chunks, i)    # 0x0B
		e2, i = getEnum(chunks, i)    # 0x0B
		n1, i = getInteger(chunks, i) # 0, 6, 7
		if (n1 == 6):
			e3  , i = getEnum(chunks, i)    # 0x0B
			e4  , i = getEnum(chunks, i)   # 0x0A
			scl5, i = self._readScaleClLoft(chunks, i)
			n2  , i = getInteger(chunks, i) # 0
			v1  , i = getVector(chunks, i)
		elif (n1 == 7):
			e3  , i = getEnum(chunks, i)    # 0x0B
			scl5, i = self._readScaleClLoft(chunks, i)
			e4  , i = getEnum(chunks, i)
			scl6, i = self._readScaleClLoft(chunks, i)
			n2  , i = getInteger(chunks, i) # 0
			v1  , i = getVector(chunks, i)
			e5, i = getEnum(chunks, i)
			e6, i = getEnum(chunks, i)
		else:
			e3  , i = getEnum(chunks, i)    # 0x0B
			e4  , i = getEnum(chunks, i)    # 0x0B
			n2  , i = getInteger(chunks, i)
			if (n2 == 0):
				c3, i = getVector(chunks, i)
			else:
				c3, i = readBS3Curve(chunks, i)
			e5, i = getEnum(chunks, i)
			e6, i = getEnum(chunks, i)
		return i
	def setCompound(self, chunks, index, inventor):
		i = self.setSurfaceShape(chunks, index, inventor)
		d, i  = getFloatArray(chunks, i)
		for k in range(0, len(d)):
			f, i = readSurface(self, chunks, i)
		return i
	def setCylinder(self, chunks, index, inventor):
		self.profile, i = readCurve(chunks, index) # the curve on the cylinder's surface
		self.axis,    i = getVector(chunks, i)     # the cylinder's axis
		self.center,  i = getLocation(chunks, i)   # the cylinder's center
		i = self.setSurfaceShape(chunks, i, inventor)
		self.type = 'cyl_spl_sur'
		return i
	def setDefm(self, chunks, index, inventor):
		self.surface, i = readSurface(self, chunks, index)
		t1, i = getInteger(chunks, i) # 1, 3, 5, 8
		if (t1 == 1):
			v11, i = getVector(chunks, i)
			v12, i = getVector(chunks, i)
			v13, i = getVector(chunks, i)
			v14, i = getVector(chunks, i)
			f15, i = getFloat(chunks, i)
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
			t3, i  = getInteger(chunks, i) # 1
			v31, i = getPoint(chunks, i)
		elif (t1 == 3):
			v11, i = getVector(chunks, i)
			v12, i = getVector(chunks, i)
			v13, i = getVector(chunks, i)
			v14, i = getVector(chunks, i)
			f15, i = getFloat(chunks, i)
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
			t3, i  = getInteger(chunks, i) # 1
			v31, i = getFloat(chunks, i)
		elif (t1 == 5):
			self.surface, i = readSurface(self, chunks, i)
			e31, i = getEnum(chunks, i)
			f32, i = getFloat(chunks, i)
			i33, i = getInteger(chunks, i)
			f34, i = getFloat(chunks, i)
			self.curve = CurveInt()
			i = self.curve.setSubtype(chunks, i)
			v11, i = getVector(chunks, i)
			v12, i = getVector(chunks, i)
			v13, i = getVector(chunks, i)
			v14, i = getVector(chunks, i)
			f15, i = getFloat(chunks, i)
			e21, i = getEnum(chunks, i)
			e22, i = getEnum(chunks, i)
			e23, i = getEnum(chunks, i)
		elif (t1 == 8):
			v11, i = getVector(chunks, i)
			v12, i = getVector(chunks, i)
			v13, i = getVector(chunks, i)
			v14, i = getVector(chunks, i)
			t2, i  = getInteger(chunks, i) # 0
		else:
			raise TypeError("Unknown defm_sur_spl type %d" %(t1))
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
		while (not isString(t11)):
			t11, i = getValue(chunks, i)
		s11, i = readSurface(self, chunks, i)
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
			if (not chunks[i].tag in [TAG_UTF8_U8, TAG_IDENT, TAG_SUBIDENT]):
				i += 1 # newer Inventor versions (>2017
			p13, i = readBS2Curve(chunks, i)
		else:
			raise AssertionError("wrong singularity %s" %(singularity))

		t21, i = getValue(chunks, i)
		s21, i = readSurface(self, chunks, i)
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
		length, i = getLength(chunks, i) # pi / 2
		curve = CurveInt()
		curve.type = "helix_int_cur"
		i = curve.setHelix(chunks, i, inventor)
		radius, i   = getLength(chunks, i) # radius of the circle
		helix = curve.helix
		self.shape = helix.buildSurfaceCircle(radius, angle.getLowerLimit(), angle.getUpperLimit())
		return i
	def setHelixLine(self, chunks, index, inventor):
		angle, i  = getInterval(chunks, index, MIN_PI, MAX_PI, 1.0)
		values, i  = getInterval(chunks, i, -MAX_LEN, MAX_LEN, 1.0)
		curve = CurveInt()
		curve.type = "helix_int_cur"
		i = curve.setHelix(chunks, i, inventor)
		helix = curve.helix
		posCenter, i     = getLocation(chunks, i)
		return i
	def setLoft(self, chunks, index, inventor):
		ls1, i = self._readLofSection(chunks, index, inventor)
		ls2, i = self._readLofSection(chunks, i, inventor)

		r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		r2, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		clsr1, i = getClosure(chunks, i)
		clsr2, i = getClosure(chunks, i)
		sng1, i = getSingularity(chunks, i)
		sng2, i = getSingularity(chunks, i)
		# 1|2, 0?, 0, nubs
		b, i = getInteger(chunks, i)
		while (not chunks[i+1].tag in [TAG_UTF8_U8, TAG_IDENT, TAG_SUBIDENT]):
			i += 1 ## FIXME
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setNet(self, chunks, index, inventor):
		ls1, i = self._readLofSection(chunks, index, inventor)
		ls2, i = self._readLofSection(chunks, i, inventor)
		if (inventor):
			a1, i = getFloats(chunks, i, 12)
			a2, i = getInteger(chunks, i)
			v1, i = getVector(chunks, i)
			v2, i = getVector(chunks, i)
			v3, i = getVector(chunks, i)
			v4, i = getVector(chunks, i)
		else:
			a1 = []
			for j in range(0, len(ls2)):
				a2 = []
				for k in range(0, len(ls1)):
					a3, i = getFloats(chunks, i, 2)
					a2.append(a3)
				a1.append(a2)
		frml1, i = readFormula(chunks, i)
		frml2, i = readFormula(chunks, i)
		frml3, i = readFormula(chunks, i)
		frml4, i = readFormula(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		return i
	def setOffset(self, chunks, index, inventor):
		self.surface, i = readSurface(self, chunks, index)
		self.offset, i = getFloat(chunks, i)
		self.senseU, i = getSense(chunks, i)
		self.senseV, i = getSense(chunks, i)
		if (inventor):
			e3, i = getEnum(chunks, i) # 0x0B
			if (chunks[i].tag in [TAG_TRUE, TAG_FALSE]):
				i += 1
		i = self.setSurfaceShape(chunks, i, inventor)
		self.type = 'off_spl_sur'
		return i
	def setOrtho(self, chunks, index, inventor):
		self.surface, i = readSurface(self, chunks, index)
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
		rb1, i = self._readRbBlend(chunks, i, inventor)
		rb2, i = self._readRbBlend(chunks, i, inventor)

		if (getVersion() > 22.0):
			i += 2 # 43, 1e-10
		# read remaining data
		c3, i = readCurve(chunks, i)
		if (getVersion() > 22.0):
			cT, i = readCurve(chunks, i)
			cT, i = readCurve(chunks, i)
			cT, i = readCurve(chunks, i)
			cT, i = readCurve(chunks, i)
		a1, i = getFloats(chunks, i, 2)
		f1, i = getValue(chunks, i); # -1 = no_radius, float
		r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		a2, i = getFloats(chunks, i, 3)
		if (getVersion() > 22.0):
			i += 1 # T
		i += 1 # 1
		i = self.setSurfaceShape(chunks, i, inventor)
		if (inventor):
			a7, i = getFloatArray(chunks, i)
			a8, i = getFloatArray(chunks, i)
			a9, i = getFloatArray(chunks, i)
		return i
	def setRotation(self, chunks, index, inventor):
		self.profile, i = readCurve(chunks, index)
		self.loc, i     = getLocation(chunks, i)
		self.dir, i     = getVector(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		self.type = 'rot_spl_sur'
		return i
	def setSkin(self, chunks, index, inventor):
		skins = []
		bool, i = getSurfBool(chunks, index)
		norm, i = getSurfNorm(chunks, i)
		dir, i  = getSurfDir(chunks, i)
		n, i  = getInteger(chunks, i)
		for k in range(0, n):
			skin, i = self._readSkin(chunks, i, inventor)
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
			if (chunks[i].tag == TAG_TRUE):
				i += 1
				c2, i = readCurve(chunks, i)
				r2, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			else:
				try:
					c2, i = readSurface(self, chunks, i) # 3, hB, 0, hB
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
				s1, i = readSurface(self, chunks, i)
			else:
				raise Exception()
			e4, i = getEnum(chunks, i)
			if (e4 == TAG_TRUE):
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
			r1, i  = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			r2, i  = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
			a11, i = getFloatArray(chunks, i)
			a12, i = getFloatArray(chunks, i)
		arr, i  = readArrayFloats(chunks, i, inventor)

		l1, i = self._readScaleClLoft(chunks, i) # ([1], None, [0], (-1, 2))
		l2, i = self._readScaleClLoft(chunks, i) # ([1], None, [0], ( 1, 0))
		l3, i = self._readScaleClLoft(chunks, i) # ([4], None, [0], ( 1, 1))

		e1, i = getEnum(chunks, i)    # 0x0B
		e2, i = getEnum(chunks, i)    # 0x0B
		i1, i = getInteger(chunks, i) # 0

		e4, i = getEnum(chunks, i)
		if (e4 == TAG_TRUE):
			l5, i = self._readScaleClLoft(chunks, i)
			e5, i = getEnum(chunks, i)
			if (e5 == TAG_TRUE):
				l6, i = self._readScaleClLoft(chunks, i)
				i6, i = getInteger(chunks, i) # 0
				p6, i = getVector(chunks, i)
			else:
				e6, i = getEnum(chunks, i)
				i6, i = getInteger(chunks, i)
				c6, i = readBS3Curve(chunks, i)
		else:
			e5, i = getEnum(chunks, i) # 0x0B
			i5, i = getInteger(chunks, i)
			if (i5 == 0):
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
		'''A linear sum of two curves.'''
		self.profile1, i = readCurve(chunks, index)
		self.profile2, i = readCurve(chunks, i)
		self.loc, i = getLocation(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		self.type = 'sum_spl_sur'
		return i
	def setShadowTaper(self, chunks, index, inventor):
		self.surface, i = readSurface(self, chunks, index)
		c1, i = readCurve(chunks, i)
		c2, i = readBS2Curve(chunks, i)
		f1, i = getFloat(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		dir, i    = getVector(chunks, i)
		valueU, i = getFloat(chunks, i)
		valueV, i = getFloat(chunks, i)
		return i
	def setSSSBend(self, chunks, index, inventor):
		i = index
		rb1, i = self._readRbBlend(chunks, i, inventor)
		rb2, i = self._readRbBlend(chunks, i, inventor)
		if (getVersion() > 22.0):
			i += 2 # 43, 1e-10
		# read remaining data
		c3, i = readCurve(chunks, i)
		if (getVersion() > 22.0):
			cT, i = readCurve(chunks, i)
			cT, i = readCurve(chunks, i)
			cT, i = readCurve(chunks, i)
			cT, i = readCurve(chunks, i)
		a1, i = getFloats(chunks, i, 2)
		f1, i = getValue(chunks, i); # -1 = no_radius, float
		r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		r1, i = getInterval(chunks, i, MIN_INF, MAX_INF, 1.0)
		a2, i = getFloats(chunks, i, 3)
		if (getVersion() > 22.0):
			i += 1 # T
		i += 1 # 1
		i = self.setSurfaceShape(chunks, i, inventor)
		if (inventor):
			a7, i = getFloatArray(chunks, i)
			a8, i = getFloatArray(chunks, i)
			a9, i = getFloatArray(chunks, i)
		return i
	def setTSpline(self, chunks, index, inventor):
		i = self.setSurfaceShape(chunks, index, inventor)
		rU, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		rV, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		typ, i = getInteger(chunks, i)
		block, i = getBlock(chunks, i)
		# block: (t_spl_subtrans_object, def (str), values (str)|ref number)
		num, i  = getInteger(chunks, i)
		# int
		return i
	def setVertexBlend(self, chunks, index, inventor):
		n, i = getInteger(chunks, index)      # vertexblendsur
		self.boundaries = []
		for j in range(0, n):
			vbl, i = self._readBoundaryGeometry(chunks, i, inventor)
			self.boundaries.append(vbl)
		grid,      i = getInteger(chunks, i)  # Grid-Size
		tolerance, i = getFloat(chunks, i)    # fit tolerance
		self.type = 'VBL_SURF'
		return i
	def setRuledTaper(self, chunks, index, inventor):
		surf, i = readSurface(self, chunks, index)
		curv, i = readCurve(chunks, i)
		bs2curf, i = readBS2Curve(chunks, i)
		f1, i = getFloat(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		vec, i = getVector(chunks, i)
		f2, i = getFloat(chunks, i)
		f3, i = getFloat(chunks, i)
		f4, i = getFloat(chunks, i)
		return i
	def setSweptTaper(self, chunks, index, inventor):
		surf, i = readSurface(self, chunks, index)
		curv, i = readCurve(chunks, i)
		bs2curf, i = readBS2Curve(chunks, i)
		f1, i = getFloat(chunks, i)
		i = self.setSurfaceShape(chunks, i, inventor)
		vec, i = getVector(chunks, i)
		f2, i = getFloat(chunks, i)
		f3, i = getFloat(chunks, i)
		return i
	def setRef(self, chunks, index):
		self.surface, i = getInteger(chunks, index)
		self.ref = self.surface
		return i
	def setBulk(self, chunks, index):
		self.type, i = getValue(chunks, index)

		if (self.type == 'ref'):                   return self.setRef(chunks, i)

		try:
			prm = SURFACE_TYPES[self.type]
			fkt = getattr(self, prm[0])
			return fkt(chunks, i + prm[1], prm[2])
		except KeyError as ke:
			raise Exception("Spline-Surface: Unknown subtype '%s'!" %(self.type))
	def setSubtype(self, chunks, index):
		self.sense, i  = getSense(chunks, index)
		block, i       = getBlock(chunks, i)
		if (self.entity is None):
			self.entity = AcisEntity('spline')
			self.entity.index = self.index
			if (self.sense == 'forward'):
				self.entity.chunks = [ACIS_CONST_CHUNKS[TAG_FALSE]] + block
			else:
				self.entity.chunks = [ACIS_CONST_CHUNKS[TAG_TRUE]] + block

		self.setBulk(block, 1)
		self.rangeU, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		self.rangeV, i = getInterval(chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def build(self):
		if (self.shape is None):
			if (hasattr(self, 'failed')):
				return None
			self.failed = True # assume we can't build the surface!
			if (self.type == 'ref'):
				if (type(self.surface) == int):
					ref = getSubtypeNodeSurfaces(self.surface)
					if (ref is not None) and (ref.type == 'rot_spl_sur'):
						self.profile = ref.profile
					self.surface = ref
			elif (self.type == 'cyl_spl_sur'):
				if (self.surface is None):
					# create a cylinder surface from the profile
					self.surface = Part.Cylinder()
					rotateShape(self.surface, self.axis)
					self.surface.Center = self.center
					curve = self.profile.build(self.profile.range.getLowerLimit(), self.profile.range.getUpperLimit())
					if (curve is not None):
						point = curve.Curve.StartPoint
						u, v = self.surface.parameter(point)
						radius = point - self.surface.value(u, v)
						self.surface.Radius = radius.Length + 1.0
						self.shape = self.surface.toShape()
					else:
						logError("Can't create cylinder from profile (%r)" %(self.profile))
			elif (self.type == 'VBL_SURF'):
				if (self.surface is None):
					edges = []
					for vbl in self.boundaries:
						edge = vbl.build()
						if (not edge is None):
							edges.append(edge)
					try:
						self.shape = Part.makeFilledFace(edges)
					except:
						for edge in edges:
							Part.show(edge)
			elif (self.type == 'off_spl_sur'):
				if (self.surface is not None):
					source = self.surface.build()
					if (source is not None):
						distance  = self.offset
						tolerance = 1e-6
						mode = 0 # 0=skin, 1=pipe, 2=rect-verso
						join = 0 # 0=arc, 1=tangent, 2=intersection
						fill = False

						s = source.Surface
						if (s.Continuity == 'C0') and (isinstance(s, Part.BSplineCurve)):
							"""Try to approximate 'in_surf' to C1 continuity, with given tolerance 'tol' """
							tol = 1e-2
							tmp = s.copy()
							for iU in range(2, tmp.NbUKnots):
								if (tmp.getUMultiplicity(iU) >= tmp.UDegree):
									tmp.removeUKnot(iU, tmp.UDegree-1, tol)
							for kV in range(2, tmp.NbVKnots):
								if (tmp.getVMultiplicity(kV) >= tmp.VDegree):
									tmp.removeVKnot(kV, tmp.VDegree-1, tol)
							source  = tmp.toShape()

						self.shape = source.makeOffsetShape(distance, tolerance, False, False, mode, join, fill)
			elif (self.type == 'rot_spl_sur'):
				if (self.surface is None):
					# create a rotation shape from the profile
					curve = self.profile.build(None, None)
					if (curve is not None):
						self.shape = Part.SurfaceOfRevolution(curve.Curve, self.loc, self.dir).toShape()
					else:
						logError("Can't create curve for revolution of (%r)" %(self.profile))
			elif (self.type == 'sum_spl_sur'):
				rngU = self.tolerance[2]
				curve1 = self.profile1.build(rngU.getLowerLimit(), rngU.getUpperLimit())
				if (curve1 is not None):
					rngV = self.tolerance[3]
					curve2 = self.profile2.build(rngV.getLowerLimit(), rngV.getUpperLimit())
					if (curve2 is not None):
						self.shape = Part.makeRuledSurface(curve1, curve2)
						self.shape.translate(self.loc)
					else:
						logError("Can't create ruled surface of 2nd curve - (%r)" %(self.profile2))
				else:
					logError("Can't create ruled surface of 1st curve - (%r)" %(self.profile1))

			if (isinstance(self.surface, Surface)):
				self.shape = self.surface.build()
				if (self.shape is None):
					if (hasattr(self.surface, 'type')):
						if (self.surface.type == 'ref'):
							logWarning(u"    ... Don't know how to build surface '-%d %s::ref %d' - only edges displayed!", self.surface.index, self.surface.__class__.__name__, self.surface.ref)
						else:
							logWarning(u"    ... Don't know how to build surface '-%d %s::%s' - only edges displayed!", self.surface.index, self.surface.__class__.__name__, self.surface.type)
					else:
						logWarning(u"    ... Don't know how to build surface '-%d %s' - only edges displayed!", self.surface.index, self.surface.__class__.__name__)
#				elif (not (isinstance(self.shape.Surface, Part.BSplineSurface) or isinstance(self.shape.Surface, Part.SurfaceOfRevolution))):
#					logWarning(u"    ... referenced spline surface is of incompatible type '%s' - only edges displayed!", self.shape.Surface.__class__.__name__)
#					self.shape = None
		return self.shape
class SurfaceTorus(Surface):
	'''
	The torus surface is defined by the center point, normal vector, the major
	and min radius, the u-v-origin point the range for u and v and the sense.
	'''
	def __init__(self):
		super(SurfaceTorus, self).__init__('torus')
		self.center   = CENTER
		self.axis     = DIR_Z
		self.major    = 1.0
		self.minor    = 0.1
		self.uvorigin = CENTER
		self.sensev   = 'forward_v'
		self.urange   = Interval(Range('I', MIN_0), Range('I', MAX_2PI))
		self.vrange   = Interval(Range('I', MIN_0), Range('I', MAX_2PI))
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
	def build(self):
		if (self.shape is None):
			circleAxis   = self.axis.cross(self.uvorigin).normalize()
			circleCenter = self.center + self.uvorigin.normalize() * fabs(self.major)
			circle       = Part.makeCircle(fabs(self.minor), circleCenter, circleAxis)
			torus = circle.revolve(self.center, self.axis, 360)
			self.shape = torus
		return self.shape
class Point(Geometry):
	def __init__(self):
		super(Point, self).__init__('point')
		self.position = CENTER
		self.count    = -1 # Number of references
	def set(self, entity):
		i = super(Point, self).set(entity)
		self.position, i = getLocation(entity.chunks, i)
		return i
class Refinement(Entity):
	def __init__(self):
		super(Refinement, self).__init__()
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
			i += 18 # skip ???
		return i
	def getNext(self):     return None if (self._next is None)     else self._next.node
	def getPrevious(self): return None if (self._previous is None) else self._previous.node
	def getOwner(self):    return None if (self._owner is None)    else self._owner.node
class Attrib(Attributes):
	def __init__(self): super(Attrib, self).__init__()
class AttribBt(Attrib):
	def __init__(self): super(AttribBt, self).__init__()
class AttribBtEntityColor(AttribBt):
	# string with numbers
	def __init__(self): super(AttribBtEntityColor, self).__init__()
class AttribADesk(Attrib):
	def __init__(self): super(AttribADesk, self).__init__()
class AttribADeskColor(AttribADesk):
	def __init__(self):
		super(AttribADeskColor, self).__init__()
	def set(self, entity):
		i = super(AttribADeskColor, self).set(entity)
		coloridx, i = getInteger(entity.chunks, i)
		return i
class AttribADeskTrueColor(AttribADesk):
	def __init__(self):
		super(AttribADeskTrueColor, self).__init__()
		self.alhpa = 0.0
		self.red   = .749
		self.green = .749
		self.blue  = .749
	def set(self, entity):
		i = super(AttribADeskTrueColor, self).set(entity)
		rgba, i = getText(entity.chunks, i)
		self.alhpa = ((int(rgba) >> 24) & 0xFF) / 255.0
		self.red   = ((int(rgba) >> 16) & 0xFF) / 255.0
		self.green = ((int(rgba) >>  8) & 0xFF) / 255.0
		self.blue  = ((int(rgba) >>  0) & 0xFF) / 255.0
		return i
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
		vers = getVersion()
		if (vers > 1.7):
			if (vers < 16.0):
				i += 4 # [(keep|copy) , (keep_keep), (ignore), (copy)]
			self.text, i = getText(entity.chunks, i)
		return i
class AttribGenNameInteger(AttribGenName):
	def __init__(self):
		super(AttribGenNameInteger, self).__init__()
		self.value = 0
	def set(self, entity):
		i = super(AttribGenNameInteger, self).set(entity)
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
class AttribGenNameReal(AttribGenName):
	def __init__(self):
		super(AttribGenNameReal, self).__init__()
		self.value = ''
	def set(self, entity):
		i = super(AttribGenNameReal, self).set(entity)
		self.value, i = getFloat(entity.chunks, i)
		return i
class AttribKcId(Attrib):
	# string with numbers
	def __init__(self): super(AttribKcId, self).__init__()
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
		self.red   = 0.749
		self.green = 0.749
		self.blue  = 0.749
	def set(self, entity):
		i = super(AttribStRgbColor, self).set(entity)
		self.red,   i = getFloat(entity.chunks, i)
		self.green, i = getFloat(entity.chunks, i)
		self.blue,  i = getFloat(entity.chunks, i)
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
class AttribTslColour(AttribTsl):
	def __init__(self):
		super(AttribTslColour, self).__init__()
	def set(self, entity):
		i = super(AttribTslColour, self).set(entity)
		return i
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
class AttribMixOrganizationBendCenterEdge(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationBendCenterEdge, self).__init__()
class AttribMixOrganizationBendExtendedEdge(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationBendExtendedEdge, self).__init__()
class AttribMixOrganizationBendExtendedEdgeProgenitorTagIds(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationBendExtendedEdgeProgenitorTagIds, self).__init__()
class AttribMixOrganizationCornerEdge(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationCornerEdge, self).__init__()
class AttribMixOrganizationFlangeTrimEdge(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationFlangeTrimEdge, self).__init__()
class AttribMixOrganizationFlatPatternVis(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationFlatPatternVis, self).__init__()
class AttribMixOrganizationJacobiCornerEdge(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationJacobiCornerEdge, self).__init__()
class AttribMixOrganizationLimitTrackingFraceFrom(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationLimitTrackingFraceFrom, self).__init__()
class AttribMixOrganizationNoBendRelief(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationNoBendRelief, self).__init__()
class AttribMixOrganizationNoCenterline(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationNoCenterline, self).__init__()
class AttribMixOrganizationRefoldInfo(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationRefoldInfo, self).__init__()
class AttribMixOrganizationRolExtents(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationRolExtents, self).__init__()
class AttribMixOrganizationSmoothBendEdge(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationSmoothBendEdge, self).__init__()
class AttribMixOrganizationTraceFace(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationTraceFace, self).__init__()
class AttribMixOrganizationUfContourRollExtentTrack(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationUfContourRollExtentTrack, self).__init__()
class AttribMixOrganizationUfFaceType(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationUfFaceType, self).__init__()
class AttribMixOrganizationUfUnrollTrack(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationUfUnrollTrack, self).__init__()
class AttribMixOrganizationUnfoldInfo(AttribMixOrganization):
	def __init__(self): super(AttribMixOrganizationUnfoldInfo, self).__init__()
class AttribNamingMatching(Attrib):
	def __init__(self): super(AttribNamingMatching, self).__init__()
	def set(self, entity):
		i = super(AttribNamingMatching, self).set(entity)
		if (getHeader().version >= 21600):
			return i + 1 # since ASM 216 (Inventor 2011) there is an identifyer added!
		return i
class AttribNamingMatchingNMxMatchedEntity(AttribNamingMatching):
	# [dxIdx, msk] n1, n2
	def __init__(self): super(AttribNamingMatchingNMxMatchedEntity, self).__init__()
	def set(self, entity):
		i = super(AttribNamingMatchingNMxMatchedEntity, self).set(entity)
		self.mapping, i = getDcIndexMappings(entity.chunks, i, self)
		self.a      , i = getIntegers(entity.chunks, i, 2)
		return i
class AttribNamingMatchingNMxEdgeCurve(AttribNamingMatching):
	def __init__(self): super(AttribNamingMatchingNMxEdgeCurve, self).__init__()
class AttribNamingMatchingNMxDup(AttribNamingMatching):
	# n1, n2, n3, n4, n5
	def __init__(self): super(AttribNamingMatchingNMxDup, self).__init__()
class AttribNamingMatchingNMxOrderCount(AttribNamingMatching):
	# n1, n2
	def __init__(self): super(AttribNamingMatchingNMxOrderCount, self).__init__()
class AttribNamingMatchingNMxPuchtoolBRep(AttribNamingMatching):
	# n1, n2
	def __init__(self): super(AttribNamingMatchingNMxPuchtoolBRep, self).__init__()
class AttribNamingMatchingNMxFFColorEntity(AttribNamingMatching):
	def __init__(self):
		super(AttribNamingMatchingNMxFFColorEntity, self).__init__()
		self.a1         = []
		self.name       = u"Default"
		self.idxCreator = -1
		self.mapping    = []
		self.red = self.green = self.blue = 0xBE / 255.0 # light gray
	def set(self, entity):
		i = super(AttribNamingMatchingNMxFFColorEntity, self).set(entity)
		self.a1     , i = getIntegers(entity.chunks, i, 2)
		self.name   , i = getText(entity.chunks, i)
		self.mapping, i = getDcIndexMappings(entity.chunks, i, self)
		return i
class AttribNamingMatchingNMxThreadEntity(AttribNamingMatching):
	# x1, x2, V1, V2, n1, V2, [????]
	def __init__(self): super(AttribNamingMatchingNMxThreadEntity, self).__init__()
	def set(self, entity):
		i = super(AttribNamingMatchingNMxThreadEntity, self).set(entity)
		self.x      , i = getFloat(entity.chunks, i)
		self.y      , i = getFloat(entity.chunks, i)
		self.n1     , i = getInteger(entity.chunks, i)
		self.p1     , i = getPoint(entity.chunks, i)
		self.p2     , i = getPoint(entity.chunks, i)
		self.n2     , i = getInteger(entity.chunks, i)
		self.p3     , i = getPoint(entity.chunks, i)
		self.n2     , i = getInteger(entity.chunks, i)
		self.t1     , i = getText(entity.chunks, i)
		self.t2     , i = getText(entity.chunks, i)
		self.n3     , i = getInteger(entity.chunks, i)
		self.t3     , i = getText(entity.chunks, i)
		self.t4     , i = getText(entity.chunks, i)
		self.t5     , i = getText(entity.chunks, i)
		self.n4     , i = getInteger(entity.chunks, i)
		self.t3     , i = getText(entity.chunks, i)
		self.lst = []
		for n in range(self.n2):
			t1, i = getText(entity.chunks, i)
			t2, i = getText(entity.chunks, i)
			t3, i = getText(entity.chunks, i)
			t4, i = getText(entity.chunks, i)
			t5, i = getText(entity.chunks, i)
			t6, i = getText(entity.chunks, i)
			t7, i = getText(entity.chunks, i)
			t8, i = getText(entity.chunks, i)
			self.lst.append((t1, t2, t3, t4, t5, t6, t7, t8))
		self.mapping, i = getDcIndexMappings(entity.chunks, i, self)
		self.p4     , i = getPoint(entity.chunks, i)
		self.p5     , i = getPoint(entity.chunks, i)
		self.n5     , i = getInteger(entity.chunks, i)

		return i
class AttribNamingMatchingNMxTagWeldLateralFaceName(AttribNamingMatching):
	# no more values
	def __init__(self): super(AttribNamingMatchingNMxTagWeldLateralFaceName, self).__init__()
class AttribNamingMatchingNMxTagWeldLumpFaceName(AttribNamingMatching):
	# no more values
	def __init__(self): super(AttribNamingMatchingNMxTagWeldLumpFaceName, self).__init__()
class AttribNamingMatchingNMxWeld(AttribNamingMatching):
	# n
	def __init__(self): super(AttribNamingMatchingNMxWeld, self).__init__()
class AttribNamingMatchingNMxFeatureOrientation(AttribNamingMatching):
	def __init__(self):
		super(AttribNamingMatchingNMxFeatureOrientation, self).__init__()
	def set(self, entity):
		i = super(AttribNamingMatchingNMxFeatureOrientation, self).set(entity)
		if (entity.chunks[i].tag != TAG_ENTITY_REF): i += 1
		self.ref1, i = getRefNode(entity, i, 'curve')
		self.ref2, i = getRefNode(entity, i, 'curve')
		return i
class AttribNamingMatchingNMxGenTagDisambiguation(AttribNamingMatching):
	# n1
	def __init__(self): super(AttribNamingMatchingNMxGenTagDisambiguation, self).__init__()
class AttribNamingMatchingNMxFeatureDependency(AttribNamingMatching):
	# [a]
	def __init__(self): super(AttribNamingMatchingNMxFeatureDependency, self).__init__()
class AttribNamingMatchingNMxBrepTag(AttribNamingMatching):
	def __init__(self):
		super(AttribNamingMatchingNMxBrepTag, self).__init__()
	def set(self, entity):
		i = super(AttribNamingMatchingNMxBrepTag, self).set(entity)
		self.mapping, i = getDcIndexMappings(entity.chunks, i, self) # (DC-index, mask){n}
		return i
class AttribNamingMatchingNMxBrepTagFeature(AttribNamingMatchingNMxBrepTag):
	# no more values
	def __init__(self): super(AttribNamingMatchingNMxBrepTagFeature, self).__init__()
class AttribNamingMatchingNMxBrepTagSwitch(AttribNamingMatchingNMxBrepTag):
	# no more values
	def __init__(self): super(AttribNamingMatchingNMxBrepTagSwitch, self).__init__()
class AttribNamingMatchingNMxBrepTagFilletWeld(AttribNamingMatchingNMxBrepTag):
	# [n] n1, n2, n3
	def __init__(self): super(AttribNamingMatchingNMxBrepTagFilletWeld, self).__init__()
class AttribNamingMatchingNMxBrepTagGapWeldFace(AttribNamingMatchingNMxBrepTag):
	# no more values
	def __init__(self): super(AttribNamingMatchingNMxBrepTagGapWeldFace, self).__init__()
class AttribNamingMatchingNMxBrepTagWeldEnt(AttribNamingMatchingNMxBrepTag):
	# 1 n1 n2 dir *[01]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagWeldEnt, self).__init__()
class AttribNamingMatchingNMxBrepTagName(AttribNamingMatchingNMxBrepTag):
	# no more values
	def __init__(self): super(AttribNamingMatchingNMxBrepTagName, self).__init__()
class AttribNamingMatchingNMxBrepTagNameBPatch(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, n3, n4, n5, n6
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameBPatch, self).__init__()
class AttribNamingMatchingNMxBrepTagNameBlend(AttribNamingMatchingNMxBrepTagName):
	# n1, [a1], [a2], [a3]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameBlend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameBodySplit(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameBodySplit, self).__init__()
class AttribNamingMatchingNMxBrepTagNameCompositeFeature(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameCompositeFeature, self).__init__()
class AttribNamingMatchingNMxBrepTagNameCornerSculpt(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameCornerSculpt, self).__init__()
class AttribNamingMatchingNMxBrepTagNameMold(AttribNamingMatchingNMxBrepTagName):
	# n1, 0, 0
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameMold, self).__init__()
class AttribNamingMatchingNMxBrepTagNameMoveFace(AttribNamingMatchingNMxBrepTagName):
	# no more values!
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameMoveFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameHole(AttribNamingMatchingNMxBrepTagName):
	# n1, n2
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameHole, self).__init__()
class AttribNamingMatchingNMxBrepTagNameImportAlias(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameImportAlias, self).__init__()
class AttribNamingMatchingNMxBrepTagNameImportBrep(AttribNamingMatchingNMxBrepTagName):
	# 1, [i], 0
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameImportBrep, self).__init__()
class AttribNamingMatchingNMxBrepTagNameLocalFaceModifier(AttribNamingMatchingNMxBrepTagName):
	# no more values!
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameLocalFaceModifier, self).__init__()
class AttribNamingMatchingNMxBrepTagNameLocalFaceModifierForCorner(AttribNamingMatchingNMxBrepTagName):
	# n1
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameLocalFaceModifierForCorner, self).__init__()
class AttribNamingMatchingNMxBrepTagNameThickenFace(AttribNamingMatchingNMxBrepTagName):
	# n1, [a], x, n2, n3, n4
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameThickenFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameTrim(AttribNamingMatchingNMxBrepTagName):
	# n1, 1, n3, n4, n5, n6, n7, 0, 0, 0, 0, x, y
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameTrim, self).__init__()
class AttribNamingMatchingNMxBrepTagNameTweakFace(AttribNamingMatchingNMxBrepTagName):
	# n1, 1, n3, 1, 0, 0, 0
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameTweakFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameTweakReblend(AttribNamingMatchingNMxBrepTagName):
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameTweakReblend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameUnfoldBendLine(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, [a], n3, 0, 0
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameUnfoldBendLine, self).__init__()
class AttribNamingMatchingNMxBrepTagNameUnfoldGeomRepl(AttribNamingMatchingNMxBrepTagName):
	# n1, [a]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameUnfoldGeomRepl, self).__init__()
class AttribNamingMatchingNMxBrepTagNameVertexBlend(AttribNamingMatchingNMxBrepTagName):
	# n1
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameVertexBlend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameVentFace(AttribNamingMatchingNMxBrepTagName):
	# n1
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameVentFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameLoftSurface(AttribNamingMatchingNMxBrepTagName):
	# [a, b, c, d, e]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameLoftSurface, self).__init__()
class AttribNamingMatchingNMxBrepTagNameLoftedFlange(AttribNamingMatchingNMxBrepTagName):
	# [a, b, c, d, e, f, g]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameLoftedFlange, self).__init__()
class AttribNamingMatchingNMxBrepTagNameMidSurfaceFace(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, n3, n4, x, n6, n7, n8
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameMidSurfaceFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameReversedFace(AttribNamingMatchingNMxBrepTagName):
	# n1
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameReversedFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameRuledSurface(AttribNamingMatchingNMxBrepTagName):
	# [a], n2
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameRuledSurface, self).__init__()
class AttribNamingMatchingNMxBrepTagNameShadowTaperFace(AttribNamingMatchingNMxBrepTagName):
	# n1, 0
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameShadowTaperFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameModFace(AttribNamingMatchingNMxBrepTagName):
	# no more values!
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameModFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameBend(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, n3, n4, n5, n6, n7, n8
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameBend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameBendPart(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, n3
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameBendPart, self).__init__()
class AttribNamingMatchingNMxBrepTagBendLineFeature(AttribNamingMatchingNMxBrepTagName):
	# [[a b]]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagBendLineFeature, self).__init__()
class AttribNamingMatchingNMxBrepTagNameCutXBendBottomFaceTag(AttribNamingMatchingNMxBrepTagName):
	# n1, n2
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameCutXBendBottomFaceTag, self).__init__()
class AttribNamingMatchingNMxBrepTagNameCutXBendRimFaceTag(AttribNamingMatchingNMxBrepTagName):
	# n1, 0 20, 0, n5, 0
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameCutXBendRimFaceTag, self).__init__()
class AttribNamingMatchingNMxBrepTagNameDeleteFace(AttribNamingMatchingNMxBrepTagName):
	# n1
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameDeleteFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameEdgeBlend(AttribNamingMatchingNMxBrepTagName):
	# n1
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameEdgeBlend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameEmbossBottomFace(AttribNamingMatchingNMxBrepTagName):
	# 0, n2
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameEmbossBottomFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameEmbossRimFace(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, n3, n4, n5, n6
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameEmbossRimFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameEntityEntityBlend(AttribNamingMatchingNMxBrepTagName):
	# [a]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameEntityEntityBlend, self).__init__()
class AttribNamingMatchingNMxBrepTagNameExtBool(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, n3, n4, n5, n6
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameExtBool, self).__init__()
class AttribNamingMatchingNMxBrepTagNameExtendSurf(AttribNamingMatchingNMxBrepTagName):
	# [a], [b], 0
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameExtendSurf, self).__init__()
class AttribNamingMatchingNMxBrepTagNameFlange(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, n3, n4, n5, 0, n7
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameFlange, self).__init__()
class AttribNamingMatchingNMxBrepTagNameFoldFace(AttribNamingMatchingNMxBrepTagName):
	# n1, [a]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameFoldFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameGenerated(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, n3
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameGenerated, self).__init__()
	def set(self, entity):
		global _nameMtchAttr
		i = super(AttribNamingMatchingNMxBrepTagNameGenerated, self).set(entity)
		self.key, i = getInteger(entity.chunks, i)
		self.n2,  i = getInteger(entity.chunks, i)
		self.n3,  i = getInteger(entity.chunks, i)
		lst = _nameMtchAttr.get(self.key, None)
		if (lst is None):
			lst = []
			_nameMtchAttr[self.key] = lst
		lst.append(self)
		return i
class AttribNamingMatchingNMxBrepTagNameGrillSplitFace(AttribNamingMatchingNMxBrepTagName):
	# n1, n2
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameGrillSplitFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameGrillOffsetBrep(AttribNamingMatchingNMxBrepTagName):
	# n1, n2
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameGrillOffsetBrep, self).__init__()
class AttribNamingMatchingNMxBrepTagNameSweepGenerated(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, n3, 0, [a], [b], [c], n8, n9, n10
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameSweepGenerated, self).__init__()
class AttribNamingMatchingNMxBrepTagNameShellFace(AttribNamingMatchingNMxBrepTagName):
	# n1, x, 0, n3
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameShellFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameSolidSweep(AttribNamingMatchingNMxBrepTagName):
	# [0, i, x, 1, b, 0, 0]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameSolidSweep, self).__init__()
class AttribNamingMatchingNMxBrepTagNameSplitFace(AttribNamingMatchingNMxBrepTagName):
	# n1, [a, 2, c, 0, x, f, g, h, 1, y, k, l]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameSplitFace, self).__init__()
class AttribNamingMatchingNMxBrepTagNameSplitVertex(AttribNamingMatchingNMxBrepTagName):
	# n1, n2, 0, n4, 0, n6, [a, x, 1, 1]
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameSplitVertex, self).__init__()
class AttribNamingMatchingNMxBrepTagNameSplitEdge(AttribNamingMatchingNMxBrepTagName):
	# n1, 3, 0, n4, 0, n6
	def __init__(self): super(AttribNamingMatchingNMxBrepTagNameSplitEdge, self).__init__()
class AttribAtUfld(Attrib):
	def __init__(self): super(AttribAtUfld, self).__init__()
class AttribAtUfldDefmData(AttribAtUfld):
	def __init__(self): super(AttribAtUfldDefmData, self).__init__()
class AttribAtUfldDevPair(AttribAtUfld):
	def __init__(self): super(AttribAtUfldDevPair, self).__init__()
class AttribAtUfldFlatBend(AttribAtUfld):
	def __init__(self): super(AttribAtUfldFlatBend, self).__init__()
class AttribAtUfldFfldPosTransf(AttribAtUfld):
	def __init__(self): super(AttribAtUfldFfldPosTransf, self).__init__()
class AttribAtUfldFfldPosTransfMixUfContourRollTrack(AttribAtUfldFfldPosTransf):
	def __init__(self): super(AttribAtUfldFfldPosTransfMixUfContourRollTrack, self).__init__()
class AttribAtUfldFfldPosTransfMixUfTransformTrack(AttribAtUfldFfldPosTransf):
	def __init__(self): super(AttribAtUfldFfldPosTransfMixUfTransformTrack, self).__init__()
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

class AttribCt(Attrib):
	def __init__(self): super(AttribCt, self).__init__()
class AttribCtCellPtr(AttribCt):
	def __init__(self): super(AttribCtCellPtr, self).__init__()
class AttribCtCFace(AttribCt):
	def __init__(self): super(AttribCtCFace, self).__init__()
class Cell(Entity):
	def __init__(self): super(Cell, self).__init__()
class Cell3d(Cell):
	def __init__(self): super(Cell3d, self).__init__()
class CFace(Entity):
	def __init__(self): super(CFace, self).__init__()
class CShell(Entity):
	def __init__(self): super(CShell, self).__init__()

class _AcisChunk_(object):
	def __init__(self, key, val = None):
		self.tag = key
		self.val = val
	def __str__(self):  return self.__repr__()
	def __repr__(self): return "%s " %(self.val)
	def read(self, data, offset): return offset
class AcisCharChunk(_AcisChunk_):
	'''Single character (unsigned 8 bit)'''
	def __init__(self, value = None):
		super(AcisCharChunk, self).__init__(TAG_CHAR, value)
	def __repr__(self): return u"%s " %(self.val)
	def read(self, data, offset):
		self.val = data[offset]
		return offset + 1
class AcisNumberChunk(_AcisChunk_):
	def __init__(self, tag, value = None):
		super(AcisNumberChunk, self).__init__(tag, value)
	def __repr__(self): return u"%g " %(self.val)
class AcisShortChunk(AcisNumberChunk):
	'''16Bit signed value'''
	def __init__(self, value = None):
		super(AcisShortChunk, self).__init__(TAG_SHORT, value)
	def read(self, data, offset):
		self.val, i = getSInt16(data, offset)
		return i
class AcisLongChunk(AcisNumberChunk):
	'''32Bit signed value'''
	def __init__(self, value = None):
		super(AcisLongChunk, self).__init__(TAG_LONG, value)
	def read(self, data, offset):
		self.val, i = getSInt32(data, offset)
		return i
class AcisFloatChunk(AcisNumberChunk):
	'''32Bit IEEE float value'''
	def __init__(self, value = None):
		super(AcisFloatChunk, self).__init__(TAG_FLOAT, value)
	def read(self, data, offset):
		self.val, i = getFloat32(data, offset)
		return i
class AcisDoubleChunk(AcisNumberChunk):
	'''64Bit IEEE float value'''
	def __init__(self, value = None):
		super(AcisDoubleChunk, self).__init__(TAG_DOUBLE, value)
	def read(self, data, offset):
		self.val, i = getFloat64(data, offset)
		return i
class AcisUtf8U8Chunk(_AcisChunk_):
	'''8Bit length + UTF8-Chars'''
	def __init__(self, value = None):
		super(AcisUtf8U8Chunk, self).__init__(TAG_UTF8_U8, value)
	def __str__(self):  return u"@%d %s " %(len(self.val), self.val)
	def __repr__(self): return u"'%s' " %(self.val)
	def read(self, data, offset):
		l, i = getUInt8(data, offset)
		self.val, i = _getStr_(data, i, l + i)
		return i
class _AcisUtf8StringChunk_(_AcisChunk_):
	def __init__(self, key, val = None):
		super(_AcisUtf8StringChunk_, self).__init__(key, val)
	def __str__(self):  return u"@%d %s " %(len(self.val), self.val)
	def __repr__(self): return u"'%s' " %(self.val)
class AcisUtf8U16Chunk(_AcisUtf8StringChunk_):
	'''16Bit length + UTF8-Chars'''
	def __init__(self, value = None):
		super(AcisUtf8U16Chunk, self).__init__(TAG_UTF8_U16, value)
	def read(self, data, offset):
		l, i = getUInt16(data, offset)
		self.val, i = _getStr_(data, i, l + i)
		return i
class AcisUtf8U32AChunk(_AcisUtf8StringChunk_):
	'''32Bit length + UTF8-Chars'''
	def __init__(self, value = None):
		super(AcisUtf8U32AChunk, self).__init__(TAG_UTF8_U32_A, value)
	def read(self, data, offset):
		l, i = getUInt32(data, offset)
		self.val, i = _getStr_(data, i, l + i)
		return i
class AcisUtf8U32BChunk(_AcisUtf8StringChunk_):
	'''32Bit length + UTF8-Chars'''
	def __init__(self, value = None):
		super(AcisUtf8U32BChunk, self).__init__(TAG_UTF8_U32_B, value)
	def read(self, data, offset):
		l, i = getUInt32(data, offset)
		self.val, i = _getStr_(data, i, l + i)
		return i
class _AcisBooleanChunk_(_AcisChunk_):
	'''Boolean value 0x0A=True, 0x0B=False'''
	def __init__(self, tag, value = None):
		super(_AcisBooleanChunk_, self).__init__(tag, value)
class AcisTrueChunk(_AcisBooleanChunk_):
	'''Boolean value 0x0A=True, 0x0B=False'''
	def __init__(self):
		super(AcisTrueChunk, self).__init__(TAG_TRUE, u"0x0A")
class AcisFalseChunk(_AcisBooleanChunk_):
	'''Boolean value 0x0A=True, 0x0B=False'''
	def __init__(self):
		super(AcisFalseChunk, self).__init__(TAG_FALSE, u"0x0B")
class AcisEntityRefChunk(_AcisChunk_):
	'''Entity reference'''
	def __init__(self, value = None):
		super(AcisEntityRefChunk, self).__init__(TAG_ENTITY_REF, value)
	def __repr__(self): return u"%s " %(self.val)
	def read(self, data, offset):
		index, i = getSInt32(data, offset)
		if (index >= 0):
			refs = getSatRefs()
			try:
				self.val = refs[index]
			except:
				self.val = AcisRef(index)
				refs[index] = self.val
		else:
			self.val = ACIS_REF_NONE
		return i
class AcisIdentChunk(_AcisChunk_):
	'''name of the base class'''
	def __init__(self, value = None):
		super(AcisIdentChunk, self).__init__(TAG_IDENT, value)
	def __repr__(self): return u"%s " %(self.val)
	def read(self, data, offset):
		l, i = getUInt8(data, offset)
		self.val, i = _getStr_(data, i, l + i)
		return i
class AcisSubidentChunk(_AcisChunk_):
	'''name of the sub class'''
	def __init__(self, value = None):
		super(AcisSubidentChunk, self).__init__(TAG_SUBIDENT, value)
	def __repr__(self): return u"%s-" %(self.val)
	def read(self, data, offset):
		l, i = getUInt8(data, offset)
		self.val, i = _getStr_(data, i, l + i)
		return i
class AcisSubtypeOpenChunk(_AcisChunk_):
	'''Opening block tag'''
	def __init__(self):
		super(AcisSubtypeOpenChunk, self).__init__(TAG_SUBTYPE_OPEN, u"{")
class AcisSubtypeCloseChunk(_AcisChunk_):
	'''Closing block tag'''
	def __init__(self):
		super(AcisSubtypeCloseChunk, self).__init__(TAG_SUBTYPE_CLOSE, u"}")
class AcisTerminatorChunk(_AcisChunk_):
	'''terminator char ('#') for the entity'''
	def __init__(self):
		super(AcisTerminatorChunk, self).__init__(TAG_TERMINATOR, u"#")
	def __repr__(self): return u"#"
class AcisEnumValueChunk(_AcisChunk_):
	'''value of an enumeration'''
	def __init__(self, value = None):
		super(AcisEnumValueChunk, self).__init__(TAG_ENUM_VALUE, value)
	def __repr__(self): return u"%d " %(self.val)
	def read(self, data, offset):
		self.val, i = getUInt32(data, offset)
		return i
class _AcisArrayChunk_(_AcisChunk_):
	def __init__(self, tag, array_size, value = None):
		super(_AcisArrayChunk_, self).__init__(tag, value)
		self.array_size = array_size
	def __repr__(self): return u"(%s) " %(" ".join(["%g" %(f) for f in self.val]))
	def read(self, data, offset):
		self.val, i = getFloat64A(data, offset, self.array_size)
		return i
class AcisPositionChunk(_AcisArrayChunk_):
	def __init__(self, value = None):
		super(AcisPositionChunk, self).__init__(TAG_POSITION, 3, value)
class AcisVector2dChunk(_AcisArrayChunk_):
	def __init__(self, value = None):
		super(AcisVector2dChunk, self).__init__(TAG_VECTOR_2D, 2, value)
class AcisVector3dChunk(_AcisArrayChunk_):
	def __init__(self, value = None):
		super(AcisVector3dChunk, self).__init__(TAG_VECTOR_3D, 3, value)

ACIS_CONST_CHUNKS = {
	TAG_TRUE:          AcisTrueChunk(),
	TAG_FALSE:         AcisFalseChunk(),
	TAG_SUBTYPE_OPEN:  AcisSubtypeOpenChunk(),
	TAG_SUBTYPE_CLOSE: AcisSubtypeCloseChunk(),
	TAG_TERMINATOR:    AcisTerminatorChunk(),
}
ACIS_VALUE_CHUNKS = {
	TAG_CHAR         : AcisCharChunk,
	TAG_SHORT        : AcisShortChunk,
	TAG_LONG         : AcisLongChunk,
	TAG_FLOAT        : AcisFloatChunk,
	TAG_DOUBLE       : AcisDoubleChunk,
	TAG_UTF8_U8      : AcisUtf8U8Chunk,
	TAG_UTF8_U16     : AcisUtf8U16Chunk,
	TAG_UTF8_U32_A   : AcisUtf8U32AChunk,
	TAG_UTF8_U32_B   : AcisUtf8U32BChunk,
	TAG_ENTITY_REF   : AcisEntityRefChunk,
	TAG_IDENT        : AcisIdentChunk,
	TAG_SUBIDENT     : AcisSubidentChunk,
	TAG_ENUM_VALUE   : AcisEnumValueChunk,
	TAG_POSITION     : AcisPositionChunk,
	TAG_VECTOR_2D    : AcisVector2dChunk,
	TAG_VECTOR_3D    : AcisVector3dChunk,
}
class AcisEntity(object):
	def __init__(self, name):
		self.chunks = []
		self.name   = name
		self.index  = -1
		self.node   = None

	def add(self, key, val):
		try:
			chunk = ACIS_CONST_CHUNKS[key]
		except:
			chunk = ACIS_VALUE_CHUNKS[key](val)
		self.chunks.append(chunk)

	def __repr__(self):
		return "%s %s" %(self.name, ''.join(c.__repr__() for c in self.chunks))

	def __str__(self):
		if (self.index < 0):
			if (self.index == -2):
				return "%s %s" %(self.name,''.join(c.__str__() for c in self.chunks))
			return ""
		return "-%d %s %s" %(self.index, self.name, ''.join(u"%s" %(c) for c in self.chunks))

class AcisRef(object):
	def __init__(self, index, entity = None):
		self.index = index
		self.entity = entity

	def __str__(self):
		if (self.entity is None or self.entity.index < 0):
			return "$%d" % self.index
		return "$%d" %(self.entity.index)
	def __repr__(self):
		return self.__str__()

ACIS_REF_NONE = AcisRef(-1)

def readNextSabChunk(data, index):
	tag, i = getUInt8(data, index)
	try:
		chunk = ACIS_CONST_CHUNKS.get(tag, None)
		if (chunk is None):
			chunk = ACIS_VALUE_CHUNKS[tag]()
			i = chunk.read(data, i)
		return chunk, i
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

PCURVE_SET_DATA = {
	'ref':         'setRef',
	'exp_par_cur': 'setExpPar',
	'exppc':       'setExpPar',
	'imp_par_cur': 'setImpPar',
	'imppc':       'setImpPar',
}

CURVE_SET_DATA = {
	'bldcur':            ('setBlend', 0, False),
	'blend_int_cur':     ('setBlend', 1, True),
	'blndsprngcur':      ('setBlendSprng', 0, False),
	'spring_int_cur':    ('setBlendSprng', 1, True),
#	'':                  ('setComp', 0, False),
	'comp_int_cur':      ('setComp', 1, True),
#	'':                  ('setDefm', 0, False),
	'defm_int_cur':      ('setDefm', 1, True),
	'exactcur':          ('setExact', 0, False),
	'exact_int_cur':     ('setExact', 1, True),
#	'':                  ('setHelix', 0, False),
	'helix_int_cur':     ('setHelix', 1, True),
#	'':                  ('setInt', 0, False),
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
	'parasil':           ('setParameterSilhouette', 0, False),
	'para_silh_int_cur': ('setParameterSilhouette', 1, True),
#	'':                  ('setProject', 0, False),
	'proj_int_cur':      ('setProject', 1, True),
	'surfintcur':        ('setSurface', 0, False),
	'surf_int_cur':      ('setSurface', 1, True),
#	'':                  ('setSSS', 0, False),
	'sss_int_cur':       ('setSSS', 1, True),
}

SURFACE_TYPES = {
#	'':                     ('setClLoft', 0, False),
	'cl_loft_spl_sur':      ('setClLoft', 1, True),
#	'':                     ('setCompound', 0, False),
	'comp_spl_sur':         ('setCompound', 1, True), # Inventor 2019
	'cylsur':               ('setCylinder', 0, False),
	'cyl_spl_sur':          ('setCylinder', 1, True),
	'defmsur':              ('setDefm', 0, False),
	'defm_spl_sur':         ('setDefm', 1, True),
	'exactsur':             ('setExact', 0, False),
	'exact_spl_sur':        ('setExact', 1, True),
	'g2blnsur':             ('setG2Blend', 0, False),
	'g2_blend_spl_sur':     ('setG2Blend', 1, True),
#	'':                     ('setHelixCircle', 0, False),
	'helix_spl_circ':       ('setHelixCircle', 1, True),
#	'':                     ('setHelixLine', 0, False),
	'helix_spl_line':       ('setHelixLine', 1, True),
	'loftsur':              ('setLoft', 0, False),
	'loft_spl_sur':         ('setLoft', 1, True),
	'netsur':               ('setNet', 0, False),
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
	'shadowtapersur':       ('setShadowTaper', 0, False),
	'shadow_tpr_spl_sur':   ('setShadowTaper', 1, True),
	'skinsur':              ('setSkin', 0, False),
	'skin_spl_sur':         ('setSkin', 1, True),
	'sweepsur':             ('setSweep', 0, False),
	'sweep_spl_sur':        ('setSweep', 1, True),
#	'':                     ('setSweepSpline', 0, False),
	'sweep_sur':            ('setSweepSpline', 1, True),
	'sssblndsur':           ('setSSSBend', 0, False),
	'sss_blend_spl_sur':    ('setSSSBend', 1, True),
#	'':                     ('setTSpline', 0, False),
	't_spl_sur':            ('setTSpline', 1, True),
	'vertexblendsur':       ('setVertexBlend', 0, False),
	'VBL_SURF':             ('setVertexBlend', 1, True),
	'srfsrfblndsur':        ('setBlendSupply', 0, False),
	'srf_srf_v_bl_spl_sur': ('setBlendSupply', 1, True),
	'sumsur':               ('setSum', 0, False),
	'sum_spl_sur':          ('setSum', 1, True),
	'ruledtapersur':        ('setRuledTaper', 0, False),
	'ruled_tpr_spl_sur':    ('setRuledTaper', 1, True),
	'swepttapersur':		('setSweptTaper', 0, False),
	'swept_tpr_spl_sur':    ('setSweptTaper', 1, True),
}

VBL_CLASSES = {
	"circle": BDY_GEOM_CIRCLE,
	"deg":    BDY_GEOM_DEG,
	"pcurve": BDY_GEOM_PCURVE,
	"plane":  BDY_GEOM_PLANE
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
	"truecolor-adesk-attrib":                                                                      AttribADeskTrueColor,
	"ansoft-attrib":                                                                               AttribAnsoft,
	"id-ansoft-attrib":                                                                            AttribAnsoftId,
	"properties-ansoft-attrib":                                                                    AttribAnsoftProperties,
	"at_ufld-attrib":                                                                              AttribAtUfld,
	"ufld_defm_data_attrib-at_ufld-attrib":                                                        AttribAtUfldDefmData,
	"ufld_dev_pair_attrib-at_ufld-attrib":                                                         AttribAtUfldDevPair,
	"ufld_flat_bend_attrib-at_ufld-attrib":                                                        AttribAtUfldFlatBend,
	"ufld_pos_transf_attrib-at_ufld-attrib":                                                       AttribAtUfldFfldPosTransf,
	"mix_UF_ContourRoll_Track-ufld_pos_transf_attrib-at_ufld-attrib":                              AttribAtUfldFfldPosTransfMixUfContourRollTrack,
	"mix_UF_Transform_Track-ufld_pos_transf_attrib-at_ufld-attrib":                                AttribAtUfldFfldPosTransfMixUfTransformTrack,
	"ufld_non_merge_bend_attrib-at_ufld-attrib":                                                   AttribAtUfldNonMergeBend,
	"ufld_pos_track_attrib-at_ufld-attrib":                                                        AttribAtUfldPosTrack,
	"mix_UF_RobustPositionTrack-ufld_pos_track_attrib-at_ufld-attrib":                             AttribAtUfldPosTrackMixUfRobustPositionTrack,
	"ufld_surf_simp_attrib-ufld_pos_track_attrib-at_ufld-attrib":                                  AttribAtUfldPosTrackSurfSimp,
	"bt-attrib":                                                                                   AttribBt,
	"entatt_color-bt-attrib":                                                                      AttribBtEntityColor,
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
	"real_attrib-name_attrib-gen-attrib":                                                          AttribGenNameReal,
	"kc_id-attrib":                                                                                AttribKcId,
	"lwd-attrib":                                                                                  AttribLwd,
	"fmesh-lwd-attrib":                                                                            AttribLwdFMesh,
	"ptlist-lwd-attrib":                                                                           AttribLwdPtList,
	"ref_vt-lwd-attrib":                                                                           AttribLwdRefVT,
	"mix_Organizaion-attrib":                                                                      AttribMixOrganization,
	"mix_BendCenterEdge-mix_Organizaion-attrib":                                                   AttribMixOrganizationBendCenterEdge,
	"mix_BendExtentEdge-mix_Organizaion-attrib":                                                   AttribMixOrganizationBendExtendedEdge,
	"mix_BendExtentEdge_Progenitor_TagIds-mix_Organizaion-attrib":                                 AttribMixOrganizationBendExtendedEdgeProgenitorTagIds,
	"mix_BendExtendPlane-mix_Organizaion-attrib":                                                  AttribMixOrganizationBendExtendPlane,
	"mix_CornerEdge-mix_Organizaion-attrib":                                                       AttribMixOrganizationCornerEdge,
	"mix_CREEntityQuality-mix_Organizaion-attrib":                                                 AttribMixOrganizationCreEntityQuality,
	"MIx_Decal_Entity-mix_Organizaion-attrib":                                                     AttribMixOrganizationDecalEntity,
	"mix_DetailEdgeInfo-mix_Organizaion-attrib":                                                   AttribMixOrganizationDetailEdgeInfo,
	"mix_EntityQuality-mix_Organizaion-attrib":                                                    AttribMixOrganizationEntityQuality,
	"mix_FlangeTrimEdge-mix_Organizaion-attrib":                                                   AttribMixOrganizationFlangeTrimEdge,
	"mix_FlatPatternVis-mix_Organizaion-attrib":                                                   AttribMixOrganizationFlatPatternVis,
	"mix_JacobiCornerEdge-mix_Organizaion-attrib":                                                 AttribMixOrganizationJacobiCornerEdge,
	"mix_LimitTrackingFaceFrom-mix_Organizaion-attrib":                                            AttribMixOrganizationLimitTrackingFraceFrom,
	"mix_NoBendRelief-mix_Organizaion-attrib":                                                     AttribMixOrganizationNoBendRelief,
	"mix_NoCenterline-mix_Organizaion-attrib":                                                     AttribMixOrganizationNoCenterline,
	"mix_RefoldInfo-mix_Organizaion-attrib":                                                       AttribMixOrganizationRefoldInfo,
	"mix_RollExtents-mix_Organizaion-attrib":                                                      AttribMixOrganizationRolExtents,
	"mix_SmoothBendEdge-mix_Organizaion-attrib":                                                   AttribMixOrganizationSmoothBendEdge,
	"mix_TrackFace-mix_Organizaion-attrib":                                                        AttribMixOrganizationTraceFace,
	"mix_UF_ContourRoll_Extent_Track-mix_Organizaion-attrib":                                      AttribMixOrganizationUfContourRollExtentTrack,
	"mix_UF_Face_Type-mix_Organizaion-attrib":                                                     AttribMixOrganizationUfFaceType,
	"mix_UF_Unroll_Track-mix_Organizaion-attrib":                                                  AttribMixOrganizationUfUnrollTrack,
	"mix_UnfoldInfo-mix_Organizaion-attrib":                                                       AttribMixOrganizationUnfoldInfo,
	"NamingMatching-attrib":                                                                       AttribNamingMatching,
	"NMx_Brep_tag-NamingMatching-attrib":                                                          AttribNamingMatchingNMxBrepTag,
	"NMx_Brep_Feature_tag-NMx_Brep_tag-NamingMatching-attrib":                                     AttribNamingMatchingNMxBrepTagFeature, # (n > 2010) 1 m -1
	"NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                                        AttribNamingMatchingNMxBrepTagName,
	"NMx_BPatch_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                         AttribNamingMatchingNMxBrepTagNameBPatch,
	"NMx_bend_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                           AttribNamingMatchingNMxBrepTagNameBend,
	"NMx_bend_part_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                      AttribNamingMatchingNMxBrepTagNameBendPart,
	"NMx_Bend_Line_Feature_Tag_Attrib-NamingMatching-attrib":                                      AttribNamingMatchingNMxBrepTagBendLineFeature,
	"NMx_blend_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                          AttribNamingMatchingNMxBrepTagNameBlend,
	"NMx_body_split_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameBodySplit,
	"NMx_Composite_feature_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":              AttribNamingMatchingNMxBrepTagNameCompositeFeature,
	"NMx_Corner_Sculpt_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                  AttribNamingMatchingNMxBrepTagNameCornerSculpt,
	"NMx_CutXBendBottomFaceTag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":              AttribNamingMatchingNMxBrepTagNameCutXBendBottomFaceTag,
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
	"NMx_grill_split_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":               AttribNamingMatchingNMxBrepTagNameGrillSplitFace,
	"NMx_GrillOffset_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":               AttribNamingMatchingNMxBrepTagNameGrillOffsetBrep,
	"NMx_Hole_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                      AttribNamingMatchingNMxBrepTagNameHole,
	"NMx_import_alias_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                   AttribNamingMatchingNMxBrepTagNameImportAlias,
	"NMx_Import_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                    AttribNamingMatchingNMxBrepTagNameImportBrep,
	"NMx_local_face_modifier_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":            AttribNamingMatchingNMxBrepTagNameLocalFaceModifier,
	"NMx_local_face_modifier_for_corner_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib": AttribNamingMatchingNMxBrepTagNameLocalFaceModifierForCorner,
	"NMx_Loft_Surface_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":              AttribNamingMatchingNMxBrepTagNameLoftSurface,
	"NMx_LoftedFlange_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":              AttribNamingMatchingNMxBrepTagNameLoftedFlange,
	"NMx_MidSurface_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                AttribNamingMatchingNMxBrepTagNameMidSurfaceFace,
	"NMx_mod_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                       AttribNamingMatchingNMxBrepTagNameModFace,
	"NMx_mold_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                           AttribNamingMatchingNMxBrepTagNameMold,
	"NMx_move_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                      AttribNamingMatchingNMxBrepTagNameMoveFace,
	"NMx_reversed_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                  AttribNamingMatchingNMxBrepTagNameReversedFace,
	"NMx_Ruled_Surface_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                  AttribNamingMatchingNMxBrepTagNameRuledSurface,
	"NMx_shadow_taper_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":              AttribNamingMatchingNMxBrepTagNameShadowTaperFace,
	"NMx_shell_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameShellFace,
	"NMx_SolidSweep_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameSolidSweep,
	"NMx_Split_Egde_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameSplitEdge,
	"NMx_split_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameSplitFace,
	"NMx_Split_Vertex_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                   AttribNamingMatchingNMxBrepTagNameSplitVertex,
	"NMx_Sweep_Generated_Brep_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":           AttribNamingMatchingNMxBrepTagNameSweepGenerated,
	"NMx_Thicken_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                   AttribNamingMatchingNMxBrepTagNameThickenFace,
	"NMx_Trim_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                           AttribNamingMatchingNMxBrepTagNameTrim,
	"NMx_tweak_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagNameTweakFace,
	"NMx_tweak_reblend_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                  AttribNamingMatchingNMxBrepTagNameTweakReblend,
	"NMx_unfold_bend_line_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":               AttribNamingMatchingNMxBrepTagNameUnfoldBendLine,
	"NMx_unfold_geom_repl_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":               AttribNamingMatchingNMxBrepTagNameUnfoldGeomRepl,
	"NMx_vertex_blend_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                   AttribNamingMatchingNMxBrepTagNameVertexBlend,
	"NMx_vent_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                      AttribNamingMatchingNMxBrepTagNameVentFace,
	"NMx_stitch_tag-NMx_Brep_tag-NamingMatching-attrib":                                           AttribNamingMatchingNMxBrepTagSwitch,
	"NMx_FilletWeld_Tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                     AttribNamingMatchingNMxBrepTagFilletWeld,
	"NMx_GapWeld_face_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                   AttribNamingMatchingNMxBrepTagGapWeldFace,
	"NMx_weld_ent_tag-NMx_Brep_Name_tag-NMx_Brep_tag-NamingMatching-attrib":                       AttribNamingMatchingNMxBrepTagWeldEnt,
	"NMx_Dup_Attrib-NamingMatching-attrib":                                                        AttribNamingMatchingNMxDup,
	"NMxEdgeCurveAttrib-NamingMatching-attrib":                                                    AttribNamingMatchingNMxEdgeCurve,
	"NMx_FFColor_Entity-NamingMatching-attrib":                                                    AttribNamingMatchingNMxFFColorEntity,
	"NMx_feature_dependency_attrib-NamingMatching-attrib":                                         AttribNamingMatchingNMxFeatureDependency,
	"NMx_Feature_Orientation-NamingMatching-attrib":                                               AttribNamingMatchingNMxFeatureOrientation,
	"NMx_GenTag_Disambiguation_Attrib-NamingMatching-attrib":                                      AttribNamingMatchingNMxGenTagDisambiguation,
	"NMx_Matched_Entity-NamingMatching-attrib":                                                    AttribNamingMatchingNMxMatchedEntity,
	"NMx_Order_Count_Attrib-NamingMatching-attrib":                                                AttribNamingMatchingNMxOrderCount,
	"NMx_Punchtool_Brep_tag-NamingMatching-attrib":                                                AttribNamingMatchingNMxPuchtoolBRep,
	"NMx_Thread_Entity-NamingMatching-attrib":                                                     AttribNamingMatchingNMxThreadEntity,
	"NMxAttribTagWeldLateralFaceName-NamingMatching-attrib":                                       AttribNamingMatchingNMxTagWeldLateralFaceName,
	"NMxAttribTagWeldLumpFaceName-NamingMatching-attrib":                                          AttribNamingMatchingNMxTagWeldLumpFaceName,
	"NMx_Weld_Attrib-NamingMatching-attrib":                                                       AttribNamingMatchingNMxWeld,
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
	"colour-tsl-attrib":                                                                           AttribTslColour,
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
	"ct-attrib":                                                                                   AttribCt,
	"cell_ptr-ct-attrib":                                                                          AttribCtCellPtr,
	"cface_ptr-ct-attrib":                                                                         AttribCtCFace,
	"cell":                                                                                        Cell,
	"cell3d-cell":                                                                                 Cell3d,
	"cface":                                                                                       CFace,
	"cshell":                                                                                      CShell,
}
