# -*- coding: utf8 -*-

'''
Acis.py:
Collection of classes necessary to read and analyse Standard ACIS Text (*.sat) files.
'''

import traceback, FreeCAD, math, Part
from importerUtils import LOG, logMessage, logWarning, logError, isEqual
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
MIN_PI2 = -pi / 2
MIN_INF = float('-inf')

MAX_2PI = 2 * pi
MAX_PI2 = pi / 2
MAX_INF = float('inf')
MAX_LEN = 0.5e+07
scale = 1.0

SUB_TYPE_INDEXES = {}

def addEntity(entity):
	global SUB_TYPE_INDEXES
	name = entity.name
	i = name.rfind('-')
	if (i > 0):
		name = name[0:i]
	try:
		refs = SUB_TYPE_INDEXES[name]
	except KeyError:
		refs = []
		SUB_TYPE_INDEXES[name] = refs
	refs.append(entity)

def getEntity(subtype, index):
	global SUB_TYPE_INDEXES
	refs = SUB_TYPE_INDEXES[name]
	return refs[index]

def clearEntities():
	global SUB_TYPE_INDEXES
	SUB_TYPE_INDEXES.clear()

def enum(*sequential, **named):
	enums   = dict(zip(sequential, range(len(sequential))), **named)
	reverse = dict((value, key) for key, value in enums.iteritems())
	values  = dict((key, value) for key, value in enums.iteritems())
	enums['reverse_mapping'] = reverse
	enums['mapping'] = values
	return type('Enum', (), enums)

RANGE      = enum(I          = 0x0B,  F             = 0x0A)
REFLECTION = enum(no_reflect = 0x0B,  reflect       = 0x0A)
ROTATION   = enum(no_rotate  = 0x0B,  rotate        = 0x0A)
SHEAR      = enum(no_shear   = 0x0B,  shear         = 0x0A)
SENSE      = enum(forward    = 0x0B,  reversed      = 0x0A)
SENSEV     = enum(forward_v  = 0x0B,  reverse_v     = 0x0A)
SIDES      = enum(single     = 0x0B,  double        = 0x0A)
SIDE       = enum(outside    = 'out', inside        = 'in')
SURF_BOOL  = enum(FALSE      = 0x0B,  TRUE          = 0x0A)
SURF_NORM  = enum(ISO        = 0x0B,  UNKNOWN       = 0x0A)
SURF_DIR   = enum(SKIN       = 0x0B,  PERPENDICULAR = 0x0A)
SURF_SWEEP = enum(angled     = 0x0B,  normal        = 0x0A)
FORMAT     = enum(open = 0, closed = 1, periodic = 2)
FULLL      = enum(full = 0, none   = 2)
references = {}
CENTER = VEC(0, 0, 0)
DIR_X  = VEC(1, 0, 0)
DIR_Y  = VEC(0, 1, 0)
DIR_Z  = VEC(0, 0, 1)

def createNode(index, type, entity, version):
	global references
	try:
		node = references[index]
	except:
		try:
			node = TYPES[type]()
		except:
			#try to find the propriate base class
			types = type.split('-')
			i = 1
			node = Entity()
			while (i<len(types)):
				try:
					t = "-".join(types[i:])
					node = TYPES[t]()
					i = len(types)
				except Exception as e:
					i += 1
			logError("TypeError: Can't find class for '%s' - using '%s'!" %(type, t))
			node = Entity()

		if (index >= 0):
			references[index] = node
		if (hasattr(node, 'set')):
			node.set(entity, version)

def getRefNode(entity, index, name):
	chunk = entity.chunks[index]
	try:
		ref = chunk.val.entity
		if (ref is not None) and (name is not None) and (ref.name.endswith(name) == False):
			raise Exception("Excpeced %s but found %s" %(name, ref.name))
		return ref, index + 1
	except Exception as e:
		logError("ERROR: Chunk at index=%d, name='%s' is not a reference (%s)! %s" %(index, name, e, entity))

def getDouble(entity, index):
	return entity.chunks[index].val, index + 1

def getLength(entity, index):
	l, i = getDouble(entity, index)
	return l * getScale(), i

def getInteger(entity, index):
	return entity.chunks[index].val, index + 1

def getText(entity, index):
	return entity.chunks[index].val, index + 1

def getEnumValue(data, index, values):
	chunk = data[index]
	try:
		return values.reverse_mapping[chunk.key], index + 1
	except:
		if (type(chunk.val) is float):
			return values.reverse_mapping[0xB - int(chunk.val)], index + 1
		return values.mapping[chunk.val], index + 1

def getReflection(data, index):
	return getEnumValue(data, index, REFLECTION)

def getRotation(data, index):
	return getEnumValue(data, index, ROTATION)

def getShear(data, index):
	return getEnumValue(data, index, SHEAR)

def getSense(data, index):
	return getEnumValue(data, index, SENSE)

def getSensev(data, index):
	return getEnumValue(data, index, SENSEV)

def getSides(data, index):
	sides, i = getEnumValue(data, index, SIDES)
	if (sides == SIDES.double):
		side, i = getSide(entity, i)
		return sides, side, i
	return sides, None, i

def getSide(entity, index):
	chunk = entity.chunks[index]
	if (chunk.key == 0x0A): return SIDE.inside, index + 1
	if (chunk.key == 0x0B): return SIDE.outside, index + 1
	return SIDE.reverse_mapping[chunk.val], index + 1

def getFormat(data, index):
	chunk = data[index]
	if (chunk.val == 0): return 'open', index + 1
	if (chunk.val == 1): return 'closed', index + 1
	if (chunk.val == 2): return 'periodic', index + 1
	return chunk.val, index + 1

def getSurfBool(data, index):
	chunk = data[index]
	if (chunk.val == 0x0A): return 'TRUE', index + 1
	if (chunk.val == 0x0B): return 'FALSE', index + 1
	return chunk.val, index + 1

def getSurfNorm(data, index):
	chunk = data[index]
	if (chunk.val == 0x0A): return 'UNKNOWN', index + 1
	if (chunk.val == 0x0B): return 'ISO', index + 1
	return chunk.val, index + 1

def getSurfDir(data, index):
	chunk = data[index]
	if (chunk.val == 0x0A): return 'PERPENDICULAR', index + 1
	if (chunk.val == 0x0B): return 'SKIN', index + 1
	return chunk.val, index + 1

def getSurfSweep(data, index):
	chunk = data[index]
	if (chunk.val == 0x0A): return 'normal', index + 1
	if (chunk.val == 0x0B): return 'angled', index + 1
	return chunk.val, index + 1

def getUnknownFT(entity, index, version):
	i = index
	if (version > 7.0):
		if (entity.chunks[i] == 'F'):
			i += 1 # skip ???
		elif (entity.chunks[i] == 'T'):
			i += 7 # skip ???
	return ['I', 0.0], i

def getRange(data, index, default, scale):
	type, i = getEnumValue(data, index, RANGE)
	value = default
	if (type == 'F'):
		value = data[i].val
		i = i + 1
	return Range(type, value, scale), i

def getInterval(data, index, defMin, defMax, scale):
	i = index
	lower, i = getRange(data, i, defMin, scale)
	upper, i = getRange(data, i, defMax, scale)
	return Intervall(lower, upper), i

def getPoint(entity, index):
	chunk = entity.chunks[index]
	if ((chunk.key == 0x13) or (chunk.key == 0x14)):
		return chunk.val, index + 1
	x, i =  getDouble(entity, index)
	y, i =  getDouble(entity, i)
	z, i =  getDouble(entity, i)
	return (x, y, z), i

def getVector(entity, index):
	p, i = getPoint(entity, index)
	return VEC(p[0], p[1], p[2]), i

def getLocation(entity, index):
	v, i = getVector(entity, index)
	return v * getScale(), i

def getBlock(entity, index):
	data = []
	i = index + 1
	chunk = entity.chunks[i]
	while (chunk.key != 0x10):
		data.append(chunk)
		if (chunk.key == 0x0F):
			block, i = getBlock(entity, i)
			data.append(block)
		i += 1
		chunk = entity.chunks[i]
	data.append(chunk)
	return data, i + 1

def createEllipse(center, normal, major, ratio):
	radius = major.Length
	if (ratio == 1):
		ellipse = Part.Circle(center, normal, radius)
	else:
		ellipse = Part.Ellipse(center, radius, radius*ratio)
		ellipse.Axis  = normal
		ellipse.XAxis = major
	return ellipse

def readNumber(entity, index):
	number = int(entity.data[index].val)
	return number, index + 1

def readFloat(entity, index):
	number = float(entity.data[index].val)
	return number, index + 1

def readFull(entity, index):
	val = entity.data[index].val
	if (val == 0): return 'full', index + 1
	if (val == 2): return 'none', index + 1
	if (val == 'full'): return val, index + 1
	if (val == 'none'): return val, index + 1
	return 'full', index

def readDimension1(entity, index):
	# DIMENSION      = (nullbs|nurbs [:NUMBER:]|nubs [:NUMBER:]|summary [:NUMBER:])
	val = entity.data[index].val
	if (val == 'nullbs'):
		return val, 0, index + 1
	if ((val == 'nurbs') or (val == 'nubs') or (val == 'summary')):
		number, i = readNumber(entity, index + 1)
		return val, number, i
	raise Exception("Unknown DIMENSION '%s'" %(val))

def readDimension2(entity, index):
	# DIMENSION      = (nullbs|nurbs [:NUMBER:]|nubs [:NUMBER:]|summary [:NUMBER:])
	val = entity.data[index].val
	if (val == 'nullbs'):
		return val, 0, index + 1
	if ((val == 'nurbs') or (val == 'nubs') or (val == 'summary')):
		number1, i = readNumber(entity, index + 1)
		number2, i = readNumber(entity, index + 1)
		return val, [number1, number2], i
	raise Exception("Unknown DIMENSION '%s'" %(val))

def readFormat1(entity, index):
	# FORMAT = (open=0|closed=1|periodic=2)
	val, i = getFormat(entity.data, index)
	if ((val == 'open') or (val == 'closed') or (val == 'periodic')):
		number, i = readNumber(entity, i)
		return val, number, i
	raise Exception("Unknown FORMAT '%s'!" %(val))

def readFormat2(entity, index):
	# FORMAT = (open=0|closed=1|periodic=2)
	val, i = getFormat(entity.data, index)
	if ((val == 'open') or (val == 'closed') or (val == 'periodic')):
		number, i = readNumber(entity, i)
		return val, number, i
	raise Exception("Unknown FORMAT '%s'!" %(val))

def addPoint(entity, i):
	x, i = readFloat(entity, i)
	y, i = readFloat(entity, i)
	z, i = readFloat(entity, i)
	entity.points.append(VEC(x, y, z) * getScale())
	if (entity.frmName == 'nurbs'):
		d, i = readFloat(entity, i)
	return i

def readPoints1(entity, index):
	j = 0
	i = index
	counts = []
	while (j < entity.frmCount):
		d, i = readFloat(entity, i)
		n, i = readNumber(entity, i)
		counts.append(n)
		j += 1

	if (len(counts) > 0):
		if (counts[0] > 2):
			i = addPoint(entity, i)
		i = addPoint(entity, i)
		for c in counts[1:-1]:
			for j in range(c):
				i = addPoint(entity, i)
		if (counts[-1] > 2):
			i = addPoint(entity, i)
		i = addPoint(entity, i)
	else:
		logWarning("%s" %(entity))

	return i

def readPoints2(entity, index):
	j = 0
	i = index
	countsX = []
	while (j < entity.frmCount[0]):
		d, i = readFloat(entity, i)
		n, i = readNumber(entity, i)
		countsX.append(n)
		j += 1
	countsY = []
	while (j < entity.frmCount[1]):
		d, i = readFloat(entity, i)
		n, i = readNumber(entity, i)
		countsY.append(n)
		j += 1

	if ((len(countsX) > 0) and (len(countsY) > 0)):
		pass
#		if (countsX[0] > 2):
#			i = addPoint(entity, i)
#		i = addPoint(entity, i)
#		for c in counts[1:-1]:
#			for j in range(c):
#				i = addPoint(entity, i)
#		if (counts[-1] > 2):
#			i = addPoint(entity, i)
#		i = addPoint(entity, i)
	else:
		logWarning("%s" %(entity))

	return i

def readVector(entity, index):
	chunk = entity.data[index]
	if ((chunk.key == 0x13) or (chunk.key == 0x14)):
		return chunk.val, index + 1
	x, i =  readFloat(entity, index)
	y, i =  readFloat(entity, i)
	z, i =  readFloat(entity, i)
	return VEC(x, y, z) * getScale(), i

def setScale(value):
	global scale
	scale = value
	return scale

def getScale():
	global scale
	return scale

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

def makeLine(start, end):
	line = Part.makeLine(start, end)
	return line

def makePolygon(points):
	l = len(points)
	if (l < 2):
		return None
	if (l == 2):
		return makeLine(points[0], points[1])
	lines = [makeLine(points[i], points[i+1]) for i in range(l-1)]
	return Part.Wire(lines)

def makeBSplines(points):
	splines = Part.BSplineCurve(points)
	return splines.toShape()

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
			i = 0
			entity.node = self
			self.entity = entity
			try:
				references[entity.index] = self
				self.index = entity.index
				self._attrib, i = getRefNode(entity, i, None)
				if (version > 6):
					i += 1 # skip history!
			except Exception as e:
				logError('>E: ' + traceback.format_exc())

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
	def set(self, entity, version):
		i = super(Transform, self).set(entity, version)
		p, i                         = getPoint(entity, i)
		self.a11, self.a21, self.a31 = p
		self.a41                     = 0.0
		p, i                         = getPoint(entity, i)
		self.a12, self.a22, self.a32 = p
		self.a42                     = 0.0
		p, i                         = getPoint(entity, i)
		self.a13, self.a23, self.a33 = p
		self.a43                     = 0.0
		p, i                         = getPoint(entity, i)
		self.a14, self.a24, self.a34 = p
		self.a44, i                  = getDouble(entity, i)
		self.rotation, i             = getRotation(entity.chunks, i)
		self.reflection, i           = getReflection(entity.chunks, i)
		self.shear, i                = getShear(entity.chunks, i)
		return i
	def getPlacement(self):
		matrix = MAT(self.a11, self.a12, self.a13, self.a14, self.a21, self.a22, self.a23, self.a24, self.a31, self.a32, self.a33, self.a34, self.a41, self.a42, self.a43, self.a44)
		return PLC(matrix)
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
		self.unknown1, i  = getUnknownFT(entity, i, version)
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
		self._next, i     = getRefNode(entity, i, 'lump')
		self._shell, i    = getRefNode(entity, i, 'shell')
		self._owner, i    = getRefNode(entity, i, 'body')
		self.unknown1, i = getUnknownFT(entity, i, version)
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
		self._next       = None  # The next face
		self._loop       = None  # The first loop in the list
		self._parent     = None  # Face's owning shell
		self.unknown     = None  # ???
		self._surface    = None  # Face's underlying surface
		self.sense       = SENSE.forward # Flag defining face is reversed
		self.sides       = SIDES.single # Flag defining face is single or double sided
		self.side        = None # Flag defining face is single or double sided
		self.containment = False # Flag defining face is containment of double-sided faces
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
			self.unknown2, i = getUnknownFT(entity, i, version)
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
		logWarning("    ...Don't know how to build surface '%s' - only edges displayed!" %(s.getType()))
		#self.showEdges(wires)
		return []

class Loop(Topology):
	def __init__(self):
		super(Loop, self).__init__()
		self._next   = None # The next loop
		self._coedge = None # The first coedge in the loop
		self._face   = None # The first coedge in the face
	def set(self, entity, version):
		i = super(Loop, self).set(entity, version)
		self._next, i    = getRefNode(entity, i, 'loop')
		self._coedge, i  = getRefNode(entity, i, 'coedge')
		self._face, i    = getRefNode(entity, i, 'face')
		self.unknown, i = getUnknownFT(entity, i, version)
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
			self.text, i = getText(entity, i)
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
		i = super(Edge, self).set(entity, version)
		self.tolerance, i = getDouble(entity, i)
		return i
class CoEdge(Topology):
	def __init__(self):
		super(CoEdge, self).__init__()
		self._next     = None          # The next coedge
		self._previous = None          # The previous coedge
		self._partner  = None          # The partner coedge
		self._edge     = None          # The coedge's edge
		self.sense     = SENSE.forward # The relative sense
		self._owner    = None          # The coedge's owner
		self._curve    = None
		self.shape     = None          # Will be created in build function
	def set(self, entity, version):
		i = i = super(CoEdge, self).set(entity, version)
		self._next, i     = getRefNode(entity, i, 'coedge')
		self._previous, i = getRefNode(entity, i, 'coedge')
		self._partner, i  = getRefNode(entity, i, 'coedge')
		self._edge, i     = getRefNode(entity, i, 'edge')
		self.sense, i     = getSense(entity.chunks, i)
		self._owner, i    = getRefNode(entity, i, None) # can be either Loop or Wire
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
		self.tStart, i  = getDouble(entity, i)
		self.tEnd, i    = getDouble(entity, i)
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
		self.tolerance, i = getDouble(entity, i)
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
		self._next, i    = getRefNode(entity, i, 'wire')
		self._coedge, i  = getRefNode(entity, i, 'coedge')
		self._owner, i   = getRefNode(entity, i, None)
		self.unknown, i  = getRefNode(entity, i, None)
		self.side, i     = getSide(entity, i)
		self.ft, i       = getUnknownFT(entity, i, version)
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
			self.shape = makeLine(start, end)
		return self.shape
class CurveComp(Curve):    # compound courve "compcurv-curve"
	def __init__(self):
		super(CurveComp, self).__init__()
	def set(self, entity, version):
		i = super(CurveComp, self).set(entity, version)
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
	def set(self, entity, version):
		i = super(CurveEllipse, self).set(entity, version)
		self.center, i = getLocation(entity, i)
		self.normal, i = getVector(entity, i)
		self.major, i  = getLocation(entity, i)
		self.ratio, i  = getDouble(entity, i)
		self.range, i  = getInterval(entity.chunks, i, MIN_0, MAX_2PI, 1.0)
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
		self.sense  = SENSE.forward # The IntCurve's reversal flag
		self.data   = None  #
		self.range  = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
		self.points = []
		self.type   = ''
	def setCurve(self, index):
		self.interval, i = readFull(self, index)
		if (self.interval == 'full'):
			self.dimName, self.dimType, i = readDimension1(self, i)
			self.frmName, self.frmCount, i = readFormat1(self, i)
			i = readPoints1(self, i)
			self.factor, i = readFloat(self, i)
		elif (self.interval == 'none'):
			self.range = getInterval(self.data, i, MIN_INF, MAX_INF, getScale())
		return i
	def setBlend(self, index):
		return self.setCurve(index)
	def setBlendSprng(self, index):
		return self.setCurve(index)
	def setExact(self, index):
		return self.setCurve(index)
	def setLaw(self, index):
		i = index + 1
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
	def setHelix(self, index):
		i = index + 1
		self.range, i      = getInterval(self.data, i, MIN_INF, MAX_INF, getScale())
		self.helixA, i     = readVector(self, i)
		self.helixB, i     = readVector(self, i)
		self.helixC, i     = readVector(self, i)
		self.helixD, i     = readVector(self, i)
		self.helixAlpha, i = readFloat(self, i)
		self.helixDir, i   = readVector(self, i)
		# null_surface
		# null_surface
		# nullbs
		# nullbs

		return i
	def setOffset(self, index):
		return self.setCurve(index)
	def setParameter(self, index):
		return self.setCurve(index)
	def setRef(self, index):
		self.ref, i = readNumber(self, index)
		logWarning("Reference to curve %s is currently not supported !" %(self.ref))
		return i
	def setSurface(self, index):
		return self.setCurve(index)
	def setData(self, version):
		# data syntax
		# DATA = ([:EXACTCUR:]|[:PARCUR:]|[:REF:]|[:PROJ_INT_CUR:]|[:SPRING_INT_CUR:]|[:SURFINTCUR:])
		# EXACTCUR       = exactcur (full)? [:DIMENSION:] [:FORMAT:] [:NUMBER: count] ([:FLOAT:] [:NUMBER:]){count} ([:VECTOR:]){n}
		#                  [:FLOAT:] [:SURFACE:] [:SURFACE:] [:DIMENSION:] [:DIMENSION:] [:RANGE:] .*
		# PARCUR         = ([:DIMENSION:]) [:FLOAT:] [:FORMAT:]

		# PROJ_INT_CUR   = proj_int_cur [:NUMBER:] (full|0)? [:DIMENSION:] [:FORMAT:] [:NUMBER: count] ([:FLOAT:] [:NUMBER:]){count} ([:VECTOR:] [:FLOAT:]?/* dimension == nurbs */){n}
		# REF            = ref [:NUMBER:]
		# SPRING_INT_CUR = spring_int_cur [:NUMBER:] (full|0)? [:DIMENSION:] [:FORMAT:] [:NUMBER: count] ([:FLOAT:] [:NUMBER:]){count} ([:VECTOR:] [:FLOAT:]?/* dimension == nurbs */){n}
		# SURFINTCUR     = surfintcur (full|0)? [:DIMENSION:] [:FORMAT:] [:NUMBER: count] ([:FLOAT:] [:NUMBER:]){count} ([:VECTOR:] [:FLOAT:]?/* dimension == nurbs */){n}

		# VECTOR         = [:FLOAT:] [:FLOAT:] [:FLOAT:]
		i = 0
		chunk = self.data[i]
		self.type = chunk.val
		i += 1
		if (self.type == 'blend_int_cur'):
			self.type = "bldcur"
			i += 1
		elif (self.type == 'defm_int_cur'):
			self.type = "exactcur"
			i += 1
		elif (self.type == 'exact_int_cur'):
			self.type = "exactcur"
			i += 1
		elif (self.type == 'helix_int_cur'):
			self.type = "helixcur"
			i += 1
		elif (self.type == 'int_int_cur'):
			self.type = "surfintcur"
			i += 1
		elif (self.type == 'law_int_cur'):
			self.type = "lawintcur"
			i += 1
		elif (self.type == 'off_int_cur'):
			self.type = "offintcur"
			i += 1
		elif (self.type == 'off_surf_int_cur'):
			self.type = "offsetintcur"
			i += 1
		elif (self.type == 'offset_int_cur'):
			self.type = "offsetintcur"
			i += 1
		elif (self.type == 'exact_int_cur'):
			self.type = "exactcur"
			i += 1
		elif (self.type == 'par_int_cur'):
			self.type = "parcur"
			i += 1
		elif (self.type == 'proj_int_cur'):
			self.type = "parcur"
			i += 1
		elif (self.type == 'spring_int_cur'):
			self.type = "blndsprngcur"
			i += 1
		elif (self.type == 'surf_int_cur'):
			self.type = "surfintcur"
			i += 1

		if (self.type == 'bldcur'):       return self.setBlend(i)
		if (self.type == 'blndsprngcur'): return self.setBlendSprng(i)
		if (self.type == 'exactcur'):     return self.setExact(i)
		if (self.type == 'helixcur'):     return self.setHelix(i)
		if (self.type == 'lawintcur'):    return self.setLaw(i)
#		if (self.type == 'offintcur'):    return self.setOff(i)
		if (self.type == 'offsetintcur'): return self.setOffset(i)
		if (self.type == 'parcur'):       return self.setParameter(i)
		if (self.type == 'ref'):          return self.setRef(i)
		if (self.type == 'surfintcur'):   return self.setSurface(i)
		logError("Curve-Int: unknown subtype %s !" %(self.type))
		return self.setCurve(i)
	def set(self, entity, version):
		i = super(CurveInt, self).set(entity, version)
		self.sense, i = getSense(entity.chunks, i)
		self.data, i  = getBlock(entity, i)
		self.setData(version)
		self.range, i = getInterval(entity.chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def __str__(self): return "-%d Curve-Int: type=%s, points=%s" %(self.getIndex(), self.type, len(self.points))
	def build(self, start, end):
		if (self.shape is None):
			if (self.type == "exactcur"):
				self.shape = makePolygon(self.points)
			elif len(self.points) == 2:
				self.shape = makeLine(self.points[0], self.points[1])
			elif (len(self.points) > 2):
				self.shape = makeBSplines(self.points)
			else:
				print self
			if (self.shape is not None):
				self.shape.Orientation = 'Reversed' if (self.sense == 'reversed') else 'Forward'
		return self.shape
class CurveIntInt(Curve):  # interpolated curve "intcurve-intcurve-curve"
	def __init__(self):
		super(CurveIntInt, self).__init__()
		self.sens = SENSE.forward # The IntCurve's reversal flag
		self.data = None  #
		self.range = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
	def set(self, entity, version):
		i = super(CurveIntInt, self).set(entity, version)
		self.sens, i  = getSense(entity.chunks, i)
		self.data, i  = getBlock(entity, i)
		self.range, i = getInterval(entity.chunks, i, MIN_INF, MAX_INF, getScale())
		return i
class CurvePoly(Curve):    # polygon curve "pcurve"
	def __init__(self):
		super(CurvePoly, self).__init__()
		self.type    = -1    # The PCurve's type
		self.sense  = SENSE.forward
		self._curve   = None  # The PCurve's curve
		self.negated = False # The PCurve's negated flag
		self.space   = None  # Parmeter space vector
	def set(self, entity, version):
		i = super(CurvePoly, self).set(entity, version)
		self.type, i = getInteger(entity, i)
		if (self.type == 0):
			self.sense, i = getSense(entity.chunks, i)
			# data syntax
			# DATA = ([:EXPPC:]|[:REF:])
			# EXPPC = (exppc ([:NUMBER:]?/*version > 22.0*/) [:DIMENSION:] [:NUMBER:dim] [:FORMAT:] [:NUMBER:count]
			# NUMBER         = ([1-9][0-9]*)
			# REF            =  ref [:NUMBER:]
			self.data, i  = getBlock(entity, i)
		else:
			self._curve, i = getRefNode(entity, i, 'curve')
		self.f1, i = getDouble(entity, i)
		self.f2, i = getDouble(entity, i)
		return i
	def build(start, end):
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
	def set(self, entity, version):
		i = super(CurveStraight, self).set(entity, version)
		self.root, i  = getLocation(entity, i)
		self.dir, i   = getLocation(entity, i)
		self.range, i = getInterval(entity.chunks, i, MIN_INF, MAX_INF, getScale())
		return i
	def build(self, start, end):
		if (self.shape is None):
			self.shape = makeLine(start, end)
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
		self.sense  = SENSE.forward
		self.urange = Intervall(Range('I', MIN_0), Range('I', MAX_2PI))
		self.vrange = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
	def __str__(self): return "Surface-Cone: center=%s, axis=%s, radius=%g, ratio=%g, semiAngle=%g" %(self.center, self.axis, self.major.Length, self.ratio, math.degrees(math.asin(self.sine)))
	def set(self, entity, version):
		i = super(SurfaceCone, self).set(entity, version)
		self.center, i = getLocation(entity, i)
		self.axis, i   = getVector(entity, i)
		self.major, i  = getLocation(entity, i)
		self.ratio, i  = getDouble(entity, i)
		self.range, i  = getInterval(entity.chunks, i, MIN_INF, MIN_INF, getScale())
		self.sine, i   = getDouble(entity, i)
		self.cosine, i = getDouble(entity, i)
		if (version >= ENTIY_VERSIONS.get('CONE_SCALING_VERSION')):
			self.scale, i = getLength(entity, i)
		else:
			self.scale = getScale()
		self.sense, i  = getSense(entity.chunks, i)
		self.urange, i = getInterval(entity.chunks, i, MIN_0, MAX_2PI, 1.0)
		self.vrange, i = getInterval(entity.chunks, i, MIN_INF, MAX_INF, getScale())
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
					logError("Can't set con.SemiAngle=%s - %s" %(math.degrees(semiAngle), e))
#				cone.Radius = self.major.Length
				# = self.ratio
				# = self.major
				self.shape = cone.toShape()
		return self.shape
class SurfaceMesh(Surface):
	def __init__(self):
		super(SurfaceMesh, self).__init__()
	def set(self, entity, version):
		i = super(SurfaceMesh, self).set(entity, version)
		return i
class SurfacePlane(Surface):
	def __init__(self):
		super(SurfacePlane, self).__init__()
		self.root     = CENTER
		self.normal   = DIR_Z
		self.uvorigin = CENTER
		self.sensev   = SENSEV.forward_v
		self.urange   = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
		self.vrange   = Intervall(Range('I', MIN_INF), Range('I', MAX_INF))
	def __str__(self): return "Surface-Plane: root=%s, normal=%s, uvorigin=%s" %(self.root, self.normal, self.uvorigin)
	def set(self, entity, version):
		i = super(SurfacePlane, self).set(entity, version)
		self.root, i     = getLocation(entity, i)
		self.normal, i   = getVector(entity, i)
		self.uvorigin, i = getLocation(entity, i)
		self.sensev, i   = getSensev(entity.chunks, i)
		self.urange, i   = getInterval(entity.chunks, i, MIN_INF, MAX_INF, getScale())
		self.vrange, i   = getInterval(entity.chunks, i, MIN_INF, MAX_INF, getScale())
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
		self.sensev   = SENSEV.forward_v
		self.urange   = Intervall(Range('I', MIN_0), Range('I', MAX_2PI))
		self.vrange   = Intervall(Range('I', MIN_PI2), Range('I', MAX_PI2))
	def __str__(self): return "Surface-Sphere: center=%s, radius=%g, uvorigin=%s, pole=%s" %(self.center, self.radius, self.uvorigin, self.pole)
	def set(self, entity, version):
		i = super(SurfaceSphere, self).set(entity, version)
		self.center, i   = getLocation(entity, i)
		self.radius, i   = getLength(entity, i)
		self.uvorigin, i = getVector(entity, i)
		self.pole, i     = getVector(entity, i)
		self.sensev, i   = getSensev(entity.chunks, i)
		self.urange, i   = getInterval(entity.chunks, i, MIN_0, MAX_2PI, 1.0)
		self.vrange, i   = getInterval(entity.chunks, i, MIN_PI2, MAX_PI2, 1.0)
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
	def setSurface(self, i):
		self.interval, i = readFull(self, index)
		if (self.interval == 'full'):
			self.dimName, self.dimType, i = readDimension2(self, i)
			self.frmName, self.frmCount, i = readFormat2(self, i)
			#  both periodic open none none 5 2
			i = readPoints2(self, i)
			self.factor, i = readFloat(self, i)
		elif (self.interval == 'none'):
			self.range = getInterval(self.data, i, MIN_INF, MAX_INF, getScale())
	def setSubCurve(self, type, i, version):
		chunk = self.data[i]
		subtype = chunk.val
		if (subtype == 'ellipse'):
			curve = CurveEllipse()
			curve.normal, i = getVector(entity, i + 1)
			curve.major, i  = getLocation(entity, i)
			curve.ratio, i  = getDouble(entity, i)
			curve.range, i  = getInterval(entity.data, i, MIN_0, MAX_2PI, 1.0)
			curve.u, i      = getLocation(entity, i)
			curve.v, i      = getLocation(entity, i)
			return curve, i
		if (subtype == 'intcurve'):
			curve = CurveInt()
			curve.sense, i = getSense(entity.data, i)
			curve.data, i  = getBlock(entity, i)
			curve.setData(version)
			curve.range, i = getInteger(entity.data, i, MIN_INF, MAX_INF, getScale())
			return curve, i
		raise Exception("Unknown curve-type '%s' in spline-surface type '%s'!" % (subtype, type))
	def setSubSurface(self, type, i, version):
		chunk = self.data[i]
		subtype = chunk.val
		if (subtype == 'cone'):
			surface = SurfaceCone()
			surface.center, i = getLocation(entity, i)
			surface.axis, i   = getVector(entity, i)
			surface.major, i  = getLocation(entity, i)
			surface.ratio, i  = getDouble(entity, i)
			surface.range, i  = getInterval(entity.data, i, MIN_INF, MIN_INF, getScale())
			surface.sine, i   = getDouble(entity, i)
			surface.cosine, i = getDouble(entity, i)
			if (version >= ENTIY_VERSIONS.get('CONE_SCALING_VERSION')):
				surface.scale, i = getLength(entity, i)
			surface.sense, i  = getSense(entity.data, i)
			surface.urange, i = getInterval(entity.data, i, MIN_0, MAX_2PI, 1.0)
			surface.vrange, i = getInterval(entity.data, i, MIN_INF, MAX_INF, getScale())
			vec1, i = getVector(entity, i)
			vec2, i = getVector(entity, i)
			vec3, i = getVector(entity, i)
			vec4, i = getVector(entity, i)
			vec5, i = getVector(entity, i)
			self.setSurface(i)
			return surface, i
		if (subtype == 'plane'):
			surface = SurfacePlane()
			surface.root, i     = getLocation(entity, i)
			surface.normal, i   = getVector(entity, i)
			surface.uvorigin, i = getLocation(entity, i)
			surface.sensev, i   = getSensev(entity.data, i)
			surface.urange, i   = getInterval(entity.data, i, MIN_INF, MAX_INF, getScale())
			surface.vrange, i   = getInterval(entity.data, i, MIN_INF, MAX_INF, getScale())
			return surface, i
		if (subtype == 'spline'):
			surface = SurfaceSpline()
			curve.sense, i = getSense(entity.data, i)
			curve.data, i  = getBlock(entity, i)
			# break potential endless loops ?!?
			return surface, i
		raise Exception("Unknown surface-type '%s' in spline-surface type '%s'!" % (subtype, type))
	def setCylinder(self, i, version):
		chunk = self.data[i]
		curveType = chunk.val
		if (curveType == 'intcurve'):
			curve = CurveInt()
			curve.sense, i = getSense(entity.data, i)
			curve.data, i  = getBlock(entity, i)
			curve.setData(version)
			curve.range, i = getInterval(entity.data, i, MIN_INF, MAX_INF, getScale())
			vec1, i = readVector(entity, i)
			d, i = readFloat(entity, i)
			vec2, i = readVector(entity, i)
			self.setSurface(i)
		else:
			raise Exception("Unknown curve-type '%s' in spline-surface type cylinder!" % (curveType))
	def setClLoft(self, i, version):
		self.setSurface(i)
		pass
	def setDefm(self, i, version):
		self.setSubSurface('DEFM', i, version)
	def setExact(self, i, version):
		self.setSurface(i)
	def setG2Blend(self, i, version):
		chunk = self.data[i]
		name = chunk.val
		self.setSubSurface('G2Blend', i + 1, version)
	def setLoft(self, i, version):
		a, i = readNumber(entity, i)
		b, i = readNumber(entity, i)
		c, i = readNumber(entity, i)
		d, i = readNumber(entity, i)
		self.setSubCurve('Loft', i, version)
	def setOffset(self, i, version):
		self.setSubSurface('Offset', i, version)
	def setRbBlend(self, i, version):
		self.setSubSurface('RB-Blend', i, version)
	def setRotation(self, i, version):
		self.setSubCurve('Rotation', i, version)
		self.setSurface(i)
	def setSkin(self, i, version, asm):
		# 0x0B 0x0B 0x0B 3 -1 -1 -1 -1 0 1 1
		bool, i = getSurfBool(entity.data, i)
		norm, i = getSurfNorm(entity.data, i)
		dir, i  = getSurfDir(entity.data, i)
		num, i  = readNumber(entity, i)
		a1, i  = readNumber(entity, i)
		a2, i  = readNumber(entity, i)
		a3, i  = readNumber(entity, i)
		a4, i  = readNumber(entity, i)
		a5, i  = readNumber(entity, i)
		if (asm): i += 2
		self.setSubCurve('Skin', i, version)
	def setBlendSupport(self, i, version):
		chunk = self.data[i]
		name = chunk.val
		self.setSubSurface(name, i + 1, version)
	def setSweep(self, i, version):
		type, i = getSurfSweep(entity.data)
		self.setSubCurve('Sweep', i, version)
	def setData(self, version):
		i = 0
		chunk = self.data[i]
		self.type = chunk.val
		i += 1
		if (self.type == 'cl_loft_spl_sur'):
			self.type = 'clloftsur'
			i += 1
		elif (self.type == 'cyl_spl_sur'):
			self.type = 'cylsur'
			i += 1
		elif (self.type == 'defm_spl_sur'):
			self.type = 'defmsur'
			i += 1
		elif (self.type == 'loft_spl_sur'):
			self.type = 'loftsur'
			i += 1
		elif (self.type == 'exact_spl_sur'):
			self.type = 'exactsur'
			i += 1
		elif (self.type == 'g2_blend_spl_sur'):
			self.type = 'g2blnsur'
			i += 1
		elif (self.type == 'off_spl_sur'):
			self.type = 'offsur'
			i += 1
		elif (self.type == 'rb_blend_spl_sur'):
			self.type = 'rbblnsur'
			i += 1
		elif (self.type == 'rot_spl_sur'):
			self.type = 'rotsur'
			i += 1
		elif (self.type == 'scaled_cloft_spl_sur'):
			self.type = 'sclclftsur'
			i += 1
		elif (self.type == 'skin_spl_sur'):
			i += 1
		elif (self.type == 'srf_srf_v_bl_spl_sur'):
			self.type = 'srfsrfblndsur'
			i += 1
		elif (self.type == 'sss_blend_spl_sur'):
			self.type = 'sssblndsur'
			i += 1
		elif (self.type == 'sweep_spl_sur'):
			self.type = 'sweepsur'
			i += 1
		if (self.type == 'cylsur'):        return self.setCylinder(i, version)
		if (self.type == 'defmsur'):       return self.setDefm(i, version)
		if (self.type == 'exactsur'):      return self.setExact(i, version)
		if (self.type == 'g2blnsur'):      return self.setG2Blend(i, version)
		if (self.type == 'loftsur'):       return self.setLoft(i, version)
		if (self.type == 'clloftsur'):     return self.setClLoft(i, version)
		if (self.type == 'offsur'):        return self.setOffset(i, version)
		if (self.type == 'rbblnsur'):      return self.setRbBlend(i, version)
		if (self.type == 'rotsur'):        return self.setRotation(i, version)
		if (self.type == 'skinsur'):       return self.setSkin(i, version, False)
		if (self.type == 'skin_spl_sur'):  return self.setSkin(i, version, True)
		if (self.type == 'srfsrfblndsur'): return self.setBlendSupport(i, version)
		if (self.type == 'sssblndsur'):    return self.setBlendSupport(i, version)
		if (self.type == 'sweepsur'):      return self.setSweep(i, version)
		raise Exception("Unknown SplineSurface '%s'!"%(self.type))
	def set(self, entity, version):
		i = super(SurfaceSpline, self).set(entity, version)
		self.sense, i = getSense(entity.chunks, i)
		self.data, i  = getBlock(entity, i)
		self.setData(version)
		self.range1, i = getInterval(entity.chunks, i, MIN_INF, MAX_INF, getScale())
		self.range2, i = getInterval(entity.chunks, i, MIN_INF, MAX_INF, getScale())
		return i
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
		self.sensev   = SENSEV.forward_v
		self.urange   = Intervall(Range('I', MIN_0), Range('I', MAX_2PI))
		self.vrange   = Intervall(Range('I', MIN_0), Range('I', MAX_2PI))
	def __str__(self): return "Surface-Torus: center=%s, normal=%s, R=%g, r=%g, uvorigin=%s" %(self.center, self.axis, self.major, self.minor, self.uvorigin)
	def set(self, entity, version):
		i = super(SurfaceTorus, self).set(entity, version)
		self.center, i   = getLocation(entity, i)
		self.axis, i     = getVector(entity, i)
		self.major, i    = getLength(entity, i)
		self.minor, i    = getLength(entity, i)
		self.uvorigin, i = getLocation(entity, i)
		self.sensev, i   = getSensev(entity.chunks, i)
		self.urange, i   = getInterval(entity.chunks, i, MIN_0, MAX_2PI, 1.0)
		self.vrange, i   = getInterval(entity.chunks, i, MIN_0, MAX_2PI, 1.0)
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
				logError("ERROR> Creation of torus failed for major=%g, minor=%g, center=%s, axis=%s:\n\t%s" %(major, minor, self.center, self.axis, e))
		return self.shape
class Point(Geometry):
	def __init__(self):
		super(Point, self).__init__()
		self.position = CENTER
		self.count    = -1 # Number of references
	def set(self, entity, version):
		i = super(Point, self).set(entity, version)
		self.position, i = getLocation(entity, i)
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
			i += 18 # skip ???
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
		if (i < 16.0):
			i += 5 # [(keep|copy) , (keep_keep), (ignore), (copy) Number]
		self.text, i = getText(entity, i)
		return i
class AttribGenNameInteger(AttribGenName):
	def __init__(self):
		super(AttribGenNameInteger, self).__init__()
		self.value = 0
	def set(self, entity, version):
		i = super(AttribGenNameInteger, self).set(entity, version)
		self.value, i = getInteger(entity, i)
		return i
class AttribGenNameString(AttribGenName):
	def __init__(self):
		super(AttribGenNameString, self).__init__()
		self.value = ''
	def set(self, entity, version):
		i = super(AttribGenNameString, self).set(entity, version)
		self.value, i = getText(entity, i)
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
		self.color, i = getPoint(entity, i)
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
class AttribAtUfldFfldPosTransf(AttribAtUfld):
	def __init__(self): super(AttribAtUfldFfldPosTransf, self).__init__()
class AttribAtUfldFfldPosTransfMixUfContourRollTrack(AttribAtUfldFfldPosTransf):
	def __init__(self): super(AttribAtUfldFfldPosTransfMixUfContourRollTrack, self).__init__()
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
	"ufld_pos_transf_attrib-at_ufld-attrib":                                                       AttribAtUfldFfldPosTransf,
	"mix_UF_ContourRoll_Track-ufld_pos_transf_attrib-at_ufld-attrib":                              AttribAtUfldFfldPosTransfMixUfContourRollTrack,
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
	"intcurve-curve":                                                                              CurveInt,
	"intcurve-intcurve-curve":                                                                     CurveIntInt,
	"pcurve":                                                                                      CurvePoly,
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
