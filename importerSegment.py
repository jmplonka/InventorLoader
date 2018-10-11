# -*- coding: utf-8 -*-

'''
importerSegment.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

import re, traceback
from importerClasses   import *
from importerSegNode   import isList, CheckList, BinaryNode, NodeRef, _TYP_NODE_REF_
from importerUtils     import *
from Acis              import clearEntities
from importerSAT       import readEntityBinary, Header

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

_listPattern = re.compile('[^\x00]\x00\x00\x30')

_fmt_new = False

def resolveEntityReferences(entities, lst):
	skip = False
	for entity in lst:
		name = entity.name
		entity.valid = True
		if (name == "Begin-of-ACIS-History-Data"):
			entity.index = -1
			skip = True
		elif (name == 'asmheader'):
			# skip ASM specific stuff
			entity.index = -1 # mark as deleted

		try:
			# clear history reference!
			entity.chunks[1].val = -1
		except:
			pass

		if (not skip):
			for chunk in entity.chunks:
				if (chunk.tag == 0x0C):
					ref = chunk.val
					if (ref.index >= 0):
						entity = entities[ref.index]
						if (entity.index == -1):
							ref.index = -1 # entity was removed
							ref.entity = None
						else:
							ref.entity = entity
		else:
			# skip everything beyond history
			entity.index = -1
			entity.valid = False

	idx = 0
	for entity in lst:
		if (entity.index != -1):
			entity.index = idx
		idx += 1

def dumpSat(node):
	folder = getInventorFile()[0:-4]
	filename = "%s\%04X.sat" %(folder, node.index)
	header, entities = node.get('SAT')
	content = '%s' %(header)
	content += ''.join(['%s' %(ntt.getStr()) for ntt in entities if ntt.index >= 0])
	with open(filename, 'w') as sat:
		sat.write(content)
		sat.write("End-of-ACIS-data\n")

def checkReadAll(node, i, l):
	assert (i == l), '%s: Have not read all data (%d <> %d)' %(node.typeID, i, l)

	return

def dumpData(file, data, offset, end):
	if (offset < end):
		arr8, dummy = getUInt8A(data, offset, end - offset)
		if (not file is None):
			file.write('\t[%s]\n' %(IntArr2Str(arr8, 2)))
	return

def getNodeType(index, seg):
	assert (index in seg.sec4), "Index %X not defined in segment's section No.4!" %(index)
	blockType = seg.sec4[index]
	return blockType.typeID

def getStart(m, data, offset):
	if (m):
		return m.start() - offset
	return len(data)

def dumpRemainingDataB(file, data, offset):
	p1 = re.compile('\x00\x00[ 0-z]\x00[ 0-z]\x00')
	p2 = re.compile('\x00\x00\x00[ 0-z][ 0-z]')
	p3 = re.compile('[^\x00]\x00\x00\x30')

	i = offset

	m1 = p1.search(data, i)
	m2 = p2.search(data, i)
	m3 = p3.search(data, i)

	iOld = offset

	while (m1 or m2 or m3):
		i1 = getStart(m1, data, 2)
		i2 = getStart(m2, data, 1)
		i3 = getStart(m3, data, 0)

		if ((i3 < i1) and (i3 < i2)):
			typ, i = getUInt16(data, i3)
			cod, i = getUInt16(data, i)
			cnt, i = getUInt32(data, i)
			if (cnt > 0):
				file.write(HexAsciiDump(data[iOld:i3], iOld, False))
				if (typ == 0x02):
					if (cnt < 0x100):
						arr, i = getUInt32A(data, i, 2)
						cls = arr[1]
						file.write('\t[%04X,%04X] %X - [%s]\n' %(typ, cod, cnt, IntArr2Str(arr, 4)))
						j = 0;
						try:
							while (j < cnt):
								if (cls == 0x1000):
									val, i = getUInt32(data, i)
								elif (cls == 0x0000):
									val, i = getUInt16A(data, i, 2)
									val = IntArr2Str(val, 4)
								elif ((cls >= 0x0114) and (cls <=0x011B)):
									val, i = getFloat32_3D(data, i)
									val = FloatArr2Str(val)
								elif (cls == 0x0131):
									val, i = getFloat32_2D(data, i)
									val = FloatArr2Str(val)
								elif (cls == 0x0107):
									val, i = getFloat64_2D(data, i)
									a8, i = getUInt8A(data, i, 8)
									val = '%s,%s' %(FloatArr2Str(val), IntArr2Str(a8, 2))
								else:
									val = ''
								file.write('\t\t%d: %s\n' %(j, val))
								j += 1
						except:
							i = i3 + 1
					else:
						file.write('\t[%04X,%04X] %X\n' %(typ, cod, cnt))
				elif (typ == 0x06):
					arr, i = getUInt32A(data, i, 2)
					file.write('\t[%04X,%04X] %X - [%s]\n' %(typ, cod, cnt, IntArr2Str(arr, 4)))
					j = 0
					if (cnt * 8 + i < len(data)):
						while (j < cnt):
							val, i = getUInt32(data, i)
							arr, i = getUInt16A(data, i, 2)
							file.write('\t\t%d: %4X - [%s]\n' %(j, val, IntArr2Str(arr, 4)))
							j += 1
				elif (typ == 0x07):
					arr, i = getUInt32A(data, i, 2)
					file.write('\t[%04X,%04X] %X - [%s]\n' %(typ, cod, cnt, IntArr2Str(arr, 4)))
				else:
					file.write('\t[%04X,%04X] %X\n' %(typ, cod, cnt))
				iOld = i
			else:
				i += 4
			m3 = p3.search(data, i)
		elif ((i1 < i2) and (i1 < i3)):
			try:
				txt, i = getLen32Text16(data, i1)
				if (len(txt) > 0):
					file.write(HexAsciiDump(data[iOld:i1], iOld, False))
					file.write("%04X: '%s'\n" %(i1, txt))
					iOld = i
				else:
					i = i1+4
			except:
				i += 10
			m1 = p1.search(data, i)
		else:
			try:
				txt, i = getLen32Text8(data, i2)
				if (len(txt) > 0):
					file.write(HexAsciiDump(data[iOld:i2], iOld, False))
					file.write("%04X: '%s'\n" %(i2, txt))
					iOld = i
				else:
					i = i2+4
			except:
				i += 5
			m2 = p2.search(data, i)

	file.write(HexAsciiDump(data[iOld:], iOld, False))
	return

def getBranchNode(data, isRef):
	if (data.typeName == 'Parameter'):                       return ParameterNode(data, isRef)
	if (data.typeName == 'ParameterText'):                   return ParameterTextNode(data, isRef)
	if (data.typeName == 'ParameterBoolean'):                return ValueNode(data, isRef)
	if (data.typeName == 'Enum'):                            return EnumNode(data, isRef)
	if (data.typeName == 'Feature'):                         return FeatureNode(data, isRef)
	if (data.typeName == 'Point2D'):                         return PointNode(data, isRef)
	if (data.typeName == 'BlockPoint2D'):                    return PointNode(data, isRef)
	if (data.typeName == 'Point3D'):                         return PointNode(data, isRef)
	if (data.typeName == 'Line2D'):                          return LineNode(data, isRef)
	if (data.typeName == 'Line3D'):                          return LineNode(data, isRef)
	if (data.typeName == 'Arc2D'):                           return CircleNode(data, isRef)
	if (data.typeName == 'Circle2D'):                        return CircleNode(data, isRef)
	if (data.typeName == 'Circle3D'):                        return CircleNode(data, isRef)
	if (data.typeName == 'Geometric_Radius2D'):              return GeometricRadius2DNode(data, isRef)
	if (data.typeName == 'Geometric_Coincident2D'):          return GeometricCoincident2DNode(data, isRef)
	if (data.typeName == 'Dimension_Distance2D'):            return DimensionDistance2DNode(data, isRef)
	if (data.typeName == 'Dimension_Distance_Horizontal2D'): return DimensionDistance2DNode(data, isRef)
	if (data.typeName == 'Dimension_Distance_Vertical2D'):   return DimensionDistance2DNode(data, isRef)
	if (data.typeName == 'Dimension_Angle2Line2D'):          return DimensionAngleNode(data, isRef)
	if (data.typeName == 'Dimension_Angle3Point2D'):         return DimensionAngleNode(data, isRef)
	if (data.typeName == 'SurfaceBodies'):                   return SurfaceBodiesNode(data, isRef)
	if (data.typeName == 'SolidBody'):                       return SurfaceBodiesNode(data, isRef)
	if (data.typeName == 'Direction'):                       return DirectionNode(data, isRef)
	if (data.typeName == 'A244457B'):                        return DirectionNode(data, isRef)
	return DataNode(data, isRef)

def buildBranchRef(parent, file, nodes, ref, level):
	branch = getBranchNode(ref.data, True)
	parent.append(branch)

	num = ''
	if (ref.number >= 0):
		num = '[%02X] ' %(ref.number)
	reftext = branch.getRefText()
	file.write('%s-> %s%s\n' %(level * '\t', num, reftext))

	return

def buildBranch(parent, file, nodes, data, level, ref):
	branch = getBranchNode(data, False)
	parent.append(branch)

	num = ''
	if ((ref is not None) and (ref.number >= 0)):
		num = '[%02X] ' %(ref.number)
	s = branch.__str__()
	file.write('%s%s%s\n' %(level * '\t', num, s))

	for childRef in data.childIndexes:
		if (childRef.index in nodes):
			childRef.data = nodes[childRef.index]
		if (childRef.data is not None):
			child = childRef.data
			if (childRef.type == NodeRef.TYPE_CHILD):
				buildBranch(branch, file, nodes, childRef.data, level + 1, childRef)
			elif (childRef.type == NodeRef.TYPE_CROSS):
				buildBranchRef(branch, file, nodes, childRef, level + 1)

	return

def buildTree(file, seg):
	nodes = seg.elementNodes
	l = len(nodes)
	tree = DataNode(None, False)

	for idx1 in nodes:
		data = nodes[idx1]
		data.handled = False
		data.sketchIndex = None
		isRadius2D = (data.typeName == 'Dimension_Radius2D')
		for ref in data.childIndexes:
			if (ref.index in nodes):
				child = nodes[ref.index]
				ref._data = child
				if (ref.type == NodeRef.TYPE_CHILD):
					ref.data.hasParent = True
				elif (ref.type == NodeRef.TYPE_CROSS):
					if (isRadius2D and ((ref.typeName == 'Circle2D') or (ref.typeName == 'Ellipse2D') or (ref.typeName == '160915E2'))):
						radius = NodeRef(idx1, 0x8000, NodeRef.TYPE_CROSS)
						radius._data = data
						ref.data.set('refRadius', radius)
			elif (ref.index > -1):
				logError(u"ERROR> %s(%04X): %s - Index out of range (%X>%X)!", seg.name, data.index, data.typeName, ref.index, l)
		if (data.typeName in ['424EB7D7', '603428AE', 'F9884C43']):
			refFx = data.get('refFX')
			refFx.set('refProfile', data)
		elif (data.typeName in ['D61732C1']):
			refFx = data.get('refPatch1')
			refFx.set('refProfile', data)
			refFx = data.get('refPatch2')
			refFx.set('refProfile', data)

		ref = data.parentIndex
		data.parent = None
		if (ref):
			if (ref.index in nodes):
				data.parent = nodes[ref.index]

	for idx1 in nodes:
		data = nodes[idx1]
		if (data.hasParent == False):
			buildBranch(tree, file, nodes, data, 0, None)
	return tree

def convert2Version7(entity):
	if ((getFileVersion() > 2012) and (entity.name == 'coedge')):
		del entity.chunks[len(entity.chunks) - 3]
	elif (entity.name == 'vertex'):
		del entity.chunks[len(entity.chunks) - 3]
	elif (entity.name == 'tvertex-vertex'):
		del entity.chunks[7]
		del entity.chunks[6]
		del entity.chunks[4]
	elif ((getFileVersion() > 2012) and (entity.name == 'tcoedge-coedge')):
		del entity.chunks[9]
	return

class SegmentReader(object):

	def __init__(self, analyseLists = True):
		self.nodeCounter = 0
		self.analyseLists = analyseLists
		self.fmt_old = (getFileVersion() < 2011)

	def postRead(self, seg):
		return

	def createNewNode(self):
		return BinaryNode()

	def ReadNodeRef(self, node, offset, number, type):
		n, i = getUInt16(node.data, offset)
		m, i = getUInt16(node.data, i)
		ref = NodeRef(n, m, type)
		if (ref.index > 0):
			ref.number = number
			node.childIndexes.append(ref)
		else:
			ref = None
		return ref, i

	def ReadHeaderSU32S(self, node, typeName=None):
		if (typeName is not None): node.typeName = typeName
		i = self.skipBlockSize(0)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_5F9D0021(self, node):
		i = node.Read_Header0('SystemOfUnitsCollection')
		i = node.ReadCrossRef(i, 'refSelected')
		i = node.ReadList3(i, _TYP_NODE_REF_, 'customUnitSystems')
		i = node.ReadList3(i, _TYP_NODE_REF_, 'predefinedUnitSystems')
		return i

	def ReadHeaderSysOfUnits(self, node, typeName):
		i = node.Read_Header0(typeName)
		i = node.ReadList3(i, _TYP_NODE_REF_, 'units')
		i = node.ReadLen32Text16(i)
		i = self.skipBlockSize(i)
		return i

	def Read_Unit(self, node, abbreviation, unitName, offset, factor, supported = False):
		'''
		Reads the parameter's unit information
		ToDo: Handle units not supported by FreeCAD
		List of SI units
		LENGTH:                    [1,0,0,0,0,0,0] 'm'
		MASS:                      [0,1,0,0,0,0,0] 'g'
		TIME:                      [0,0,1,0,0,0,0] 's'
		ELECTRIC CURRENT:          [0,0,0,1,0,0,0] 'A'
		THERMODYNAMIC TEMPERATURE: [0,0,0,0,1,0,0] 'K'
		AMOUNT OF SUBSTANCE:       [0,0,0,0,0,1,0] 'mol'
		LUMINOUS INTENSITY:        [0,0,0,0,0,0,1] 'cd'
		'''
		i = self.Read_5F9D0022(node)
		i = self.skipBlockSize(i)
		node.typeName = u'Unit' + unitName
		node.set('Unit', abbreviation)
		if (sys.version_info.major < 3) and (not isinstance(abbreviation, unicode)):
			node.set('Unit', unicode(abbreviation))
		node.set('UnitOffset', offset)
		node.set('UnitFactor', factor)
		node.set('UnitSupportet', supported)
		return i

	def Read_5C30CE1D(self, node): # SystemOfMeasureEnum {50131E62-D297-11D3-B7A0-0060B0F159EF}:
		i = self.ReadHeaderSysOfUnits(node, 'SystemOfUnitsMGS')
		return i

	def Read_EBEE69CA(self, node): # SystemOfMeasureEnum {50131E62-D297-11D3-B7A0-0060B0F159EF}:
		i = self.ReadHeaderSysOfUnits(node, 'SystemOfUnitsCGS')
		return i

	def Read_EBEE69CB(self, node): # SystemOfMeasureEnum {50131E62-D297-11D3-B7A0-0060B0F159EF}:
		i = self.ReadHeaderSysOfUnits(node, 'SystemOfUnitsEnglish')
		return i

	def Read_EBEE69D0(self, node): # SystemOfMeasureEnum {50131E62-D297-11D3-B7A0-0060B0F159EF}:
		i = self.ReadHeaderSysOfUnits(node, 'SystemOfUnitsCGS')
		return i

	def Read_5F9D0022(self, node): # UnitRef
		i = node.Read_Header0('UnitRef')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'magnitude')
		i = node.ReadFloat64(i, 'factor')
		i = self.skipBlockSize(i)
		node.set('Unit', '')
		node.set('UnitOffset', 0.0)
		node.set('UnitFactor', 1.0)
		node.set('UnitSupportet', True)
		return i

	def Read_Unit(self, node, abbreviation, unitName, offset, factor, supported = False):
		'''
		Reads the parameter's unit information
		ToDo: Handle units not supported by FreeCAD
		List of SI units
		LENGTH:                    [1,0,0,0,0,0,0] 'm'
		MASS:                      [0,1,0,0,0,0,0] 'g'
		TIME:                      [0,0,1,0,0,0,0] 's'
		ELECTRIC CURRENT:          [0,0,0,1,0,0,0] 'A'
		THERMODYNAMIC TEMPERATURE: [0,0,0,0,1,0,0] 'K'
		AMOUNT OF SUBSTANCE:       [0,0,0,0,0,1,0] 'mol'
		LUMINOUS INTENSITY:        [0,0,0,0,0,0,1] 'cd'
		'''
		i = self.Read_5F9D0022(node)
		i = self.skipBlockSize(i)
		node.typeName = u'Unit' + unitName
		node.set('Unit', abbreviation)
		if (sys.version_info.major < 3) and (not isinstance(abbreviation, unicode)):
			node.set('Unit', unicode(abbreviation))
		node.set('UnitOffset', offset)
		node.set('UnitFactor', factor)
		node.set('UnitSupportet', supported)
		return i

	###
	# The unit's symbol must match with the known unit symbols of FreeCAD!
	# Length (default 'cm'):
	def Read_624120BC(self, node): return self.Read_Unit(node, 'mm'       , 'MilliMeter'                , 0.0,      0.1    , True)
	def Read_F8A779F5(self, node): return self.Read_Unit(node, 'm'        , 'Meter'                     , 0.0,    100.0    , True)
	def Read_F8A779F6(self, node): return self.Read_Unit(node, 'in'       , 'Inch'                      , 0.0,      2.54   , True)
	def Read_F8A779F7(self, node): return self.Read_Unit(node, 'ft'       , 'Foot'                      , 0.0,     30.48   , True)
	def Read_5DFE5E70(self, node): return self.Read_Unit(node, 'mil'      , 'Mile'                      , 0.0,      0.00254, True)
	def Read_5C30CE17(self, node): return self.Read_Unit(node, 'sm'       , 'SeaMile'                   , 0.0, 185324.5218 , True)
	# Mass (default 'kg'):
	def Read_F8A779F1(self, node): return self.Read_Unit(node, 'g'        , 'Gram'                      , 0.0,  0.001      , True)
	def Read_F8A779F2(self, node): return self.Read_Unit(node, 'slug'     , 'Slug'                      , 0.0, 14.5939     , True)
	def Read_F8A779F3(self, node): return self.Read_Unit(node, 'lb'       , 'Pound'                     , 0.0,  0.428334865, True)
	def Read_5C30CE22(self, node): return self.Read_Unit(node, 'oz'       , 'Ounze'                     , 0.0,  0.028349525, True)
	# Time (default 's'):
	def Read_5F9D0025(self, node): return self.Read_Unit(node, 's'        , 'Second'                    , 0.0,    1.0      , True)
	def Read_5F9D0026(self, node): return self.Read_Unit(node, 'min'      , 'Minute'                    , 0.0,   60.0      , True)
	def Read_5F9D0027(self, node): return self.Read_Unit(node, 'h'        , 'Hour'                      , 0.0, 3600.0      , True)
	# Temperatur (default 'K'):
	def Read_5F9D0029(self, node): return self.Read_Unit(node, 'K'        , 'Kelvin'                    ,   0.0 , 1.0      , True)
	def Read_5F9D002A(self, node): return self.Read_Unit(node, u'\xB0C'   , 'Celsius'                   , 273.15, 1.0      , True)
	def Read_5F9D002B(self, node): return self.Read_Unit(node, u'\xB0F'   , 'Fahrenheit'                , 459.67, 5.0/9    , True)
	# Angularity (default ''):
	def Read_5C30CDF2(self, node): return self.Read_Unit(node, 'rad'      , 'Radian'                    , 0.0, 1.0         , True)
	def Read_5C30CDF0(self, node): return self.Read_Unit(node, u'\xb0'    , 'Degree'                    , 0.0, pi/180.0    , True)
	def Read_3D0B9C8D(self, node): return self.Read_Unit(node, 'gon'      , 'Gradiant'                  , 0.0, pi/200.0    , True)
	def Read_5C30CDF6(self, node): return self.Read_Unit(node, u'\xb0'    , 'Grad'                      , 0.0, pi/180.0    , True)
	def Read_D7155C2A(self, node): return self.Read_Unit(node, 'sr'       , 'Steradian'                 , 0.0, 1.0)
	# Velocity (default 'cm/s'):
	def Read_4D4F962F(self, node): return self.Read_Unit(node, 'm/s'      , 'Meter/Second'              , 0.0, 100.0       , True)
	def Read_A116EF37(self, node): return self.Read_Unit(node, 'f/s'      , 'Feet/Second'               , 0.0,  30.48      , True)
	def Read_4D4F9631(self, node): return self.Read_Unit(node, 'mil/h'    , 'Miles/Hour'                , 0.0,  44.72399926, True)
	def Read_E18489FC(self, node): return self.Read_Unit(node, '1/min'    , 'Revolution/Minute'         , 0.0,  pi/30.0    , True)
	#Area:
	def Read_F0F5A577(self, node): return self.Read_Unit(node, 'circ.mil' , 'CircularMile'              , 0.0, 1/1973525004.0)     # not supported
	# Volume (default 'l'):
	def Read_40AFEBA9(self, node): return self.Read_Unit(node, 'gal'      , 'Galon'                     , 0.0, 1.0/264.1706)	   # not supported
	def Read_40AFEBAA(self, node): return self.Read_Unit(node, 'dm^3'     , 'Liter'                     , 0.0, 1.0         , True) # Workaround
	# Force (default 'N'):
	def Read_40AFEBA3(self, node): return self.Read_Unit(node, 'N'        , 'Newton'                    , 0.0, 1.0         , True)
	def Read_40AFEBA2(self, node): return self.Read_Unit(node, 'dyn'      , 'Dyn'                       , 0.0, 1.0)	               # not supported
	def Read_40AFEBA1(self, node): return self.Read_Unit(node, 'lbf'      , 'PoundForce'                , 0.0, 4.44822301540537, True)
	def Read_40AFEBA0(self, node): return self.Read_Unit(node, 'ozf'      , 'OunzeForce'                , 0.0, 0.278013851)	       # not supported
	# Pressure (default 'Pa'):
	def Read_23663C43(self, node): return self.Read_Unit(node, 'Pa'       , 'Pascal'                    , 0.0,       1.0   , True)
	def Read_40AFEBA5(self, node): return self.Read_Unit(node, 'psi'      , 'PoundForce/SquareInch'     , 0.0,    6890.0   , True)
	def Read_40AFEBA4(self, node): return self.Read_Unit(node, 'ksi'      , 'KiloPoundFource/SquareInch', 0.0, 6890000.0   , True)
	# Power (default 'W'):
	def Read_40AFEB9F(self, node): return self.Read_Unit(node, 'W'        , 'Watt'                      , 0.0,   1.0       , True)
	def Read_40AFEB9E(self, node): return self.Read_Unit(node, 'hp'       , 'HorsePower'                , 0.0, 745.7)	           # not supported
	# Work (default 'J'):
	def Read_40AFEB9D(self, node): return self.Read_Unit(node, 'J'        , 'Joule'                     , 0.0,    1.0      , True)
	def Read_40AFEB9C(self, node): return self.Read_Unit(node, 'erg'      , 'Erg'                       , 0.0,    1.0)	           # not supported
	def Read_40AFEB9B(self, node): return self.Read_Unit(node, 'Cal'      , 'Calories'                  , 0.0,    4.184)	       # not supported
	def Read_40AFEB9A(self, node): return self.Read_Unit(node, 'BTU'      , 'BritishThermalUnit'        , 0.0, 1054.6)	           # not supported
	# Electrical (default depends):
	def Read_CEA6CA2D(self, node): return self.Read_Unit(node, 'A'        , 'Ampere'                    , 0.0, 1.0         , True)
	def Read_9E5A8E15(self, node): return self.Read_Unit(node, 'V'        , 'Volt'                      , 0.0, 1.0)                # not supported
	def Read_BD378B6A(self, node): return self.Read_Unit(node, 'ohm'      , 'Ohm'                       , 0.0, 1.0)                # not supported
	def Read_E7A9656E(self, node): return self.Read_Unit(node, 'C'        , 'Coulomb'                   , 0.0, 1.0)                # not supported
	def Read_28FEBA33(self, node): return self.Read_Unit(node, 'F'        , 'Farad'                     , 0.0, 1.0)                # not supported
	def Read_45BD8053(self, node): return self.Read_Unit(node, 'y'        , 'Gamma'                     , 0.0, 1.0e-9)             # not supported
	def Read_5F9F2379(self, node): return self.Read_Unit(node, 'Gs'       , 'Gauss'                     , 0.0, 0.0001)             # not supported
	def Read_DA430213(self, node): return self.Read_Unit(node, 'H'        , 'Henry'                     , 0.0, 1.0)                # not supported
	def Read_11EB21E7(self, node): return self.Read_Unit(node, 'Hz'       , 'Hertz'                     , 0.0, 1.0)                # not supported
	def Read_26072ECF(self, node): return self.Read_Unit(node, 'maxwell'  , 'Maxwell'                   , 0.0, 1.0e-8)             # not supported
	def Read_7D8BC1F7(self, node): return self.Read_Unit(node, 'mho'      , 'Mho'                       , 0.0, 1.0)                # not supported
	def Read_9E064B0C(self, node): return self.Read_Unit(node, 'Oe'       , 'Oersted'                   , 0.0, 79.577472)          # not supported
	def Read_3D793814(self, node): return self.Read_Unit(node, 'S'        , 'Siemens'                   , 0.0, 1.0)                # not supported
	def Read_FB4E31FB(self, node): return self.Read_Unit(node, 'T'        , 'Tesla'                     , 0.0, 1.0)                # not supported
	def Read_660F65B6(self, node): return self.Read_Unit(node, 'Wb'       , 'Weber'                     , 0.0, 1.0)                # not supported
	# Luminosity (default 'cd'):
	def Read_B7A5131F(self, node): return self.Read_Unit(node, 'lx'       , 'Lux'                       , 0.0, 1.0)                # not supported
	def Read_E9D0671D(self, node): return self.Read_Unit(node, 'lm'       , 'Lumen'                     , 0.0, 1.0)                # not supported
	def Read_F94FEEE2(self, node): return self.Read_Unit(node, 'cd'       , 'Candela'                   , 0.0, 1.0         , True)
	# Substance (default 'mol'):
	def Read_2F6A0C3F(self, node): return self.Read_Unit(node, 'mol'      , 'Mol'                       , 0.0, 1.0         , True)
	# without Unit:
	def Read_5F9D0023(self, node): return self.Read_Unit(node, ''         , 'Empty'                     , 0.0, 1.0         , True)

	def HandleBlock(self, file, node):
		i = 0

		try:
			readType = getattr(self, 'Read_%s' %(node.typeName))
			i = readType(node)
		except AttributeError:
			logError(u"ERROR> %s.Read_%s not defined!", self.__class__.__name__, node.typeName)
		except:
			logError(traceback.format_exc())

		try:
			if (i < len(node.data)): i = node.ReadUInt8A(i, len(node.data) - i, '\taX')
		except:
			logError(u"ERROR in %s.Read_%s: %s", self.__class__.__name__, node.typeName, traceback.format_exc())

		return

	def setNodeData(self, node, data):
		nodeTypeID, i = getUInt8(data, node.offset)
		node.typeID = getNodeType(nodeTypeID, node.segment)
		if (isinstance(node.typeID, UUID)):
			node.typeName = '%08X' % (node.typeID.time_low)
		else:
			node.typeName = '%08X' % (node.typeID)
		node.data = data[i + 3:i + 3 + node.size]

	def newNode(self, size, offset, data, seg):
		self.nodeCounter += 1
		node = self.createNewNode()
		node.index = self.nodeCounter
		node.size  = size
		node.offset = offset
		node.reader = self
		seg.elementNodes[node.index] = node
		node.segment = seg
		self.setNodeData(node, data)

		return node

	def ReadBlock(self, file, data, offset, size, seg):
		node = self.newNode(size, offset, data, seg)
		self.HandleBlock(file, node)
		return node

	def skipDumpRawData(self):
		return False

	def skipBlockSize(self, offset, l = 4):
		if (self.fmt_old):
			return offset + l
		return offset

	def dumpRawData(self, seg, data):
#		filename = '%s\\%sB.bin' %(getInventorFile()[0:-4], seg.name)
#		newFileRaw = open (filename, 'wb')
#		newFileRaw.write(data)
#		newFileRaw.close()
		return

	def ReadRefU32AList(self, node, offset, name, size, type):
		cnt, i = getUInt32(node.data, offset)
		j = 0
		lst = []
		while (j < cnt):
			ref, i = self.ReadNodeRef(node, i, j, type)
			a, i = getUInt32A(node.data, i, size)
			j += 1
			lst.append([ref, a])
		node.content += ' %s=[%s]' %(name, ','.join(['(%s,%s)' %(r[0], IntArr2Str(r[1], 4)) for r in lst]))
		node.set(name, lst)
		return i

	def ReadRefU32ARefU32List(self, node, offset, name, size):
		cnt, i = getUInt32(node.data, offset)
		j = 0
		lst = []
		while (j < cnt):
			ref1, i = self.ReadNodeRef(node, i, j, NodeRef.TYPE_CROSS)
			u32, i = getUInt32(node.data, i)
			ref2, i = self.ReadNodeRef(node, i, j, NodeRef.TYPE_CROSS)
			a, i = getUInt32A(node.data, i, size)
			j += 1
			lst.append([ref1, a, ref2, u32])
		node.content += ' %s=[%s]' %(name, ','.join(['(%s,[%s],%s,%s)' %(r[0], IntArr2Str(r[1],4), r[2], r[3]) for r in lst]))
		node.set(name, lst)
		return i

	def Read_F645595C(self, node):
		# Spatial's (A)CIS (S)olid (M)odeling
		# 3 Line Header:
		# [1]	[VERSION_NUMBER] [ENTIY_RECORDS] 4 [FLAGS]
		# [2]	[STR_LEN] [STRING:PRODUCT] [STR_LEN] [STRING:PRODUCER] [STR_LEN] [STRING:DATE]
		# [3]	[UNIT_LENGTH] [FAC_RES_ABS] [FAC_RES_NOR]
		i = node.Read_Header0('ASM')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'lenFooter')
		txt, i = getText8(node.data, i, 15)
		node.content += " fmt='%s'" %(txt)
		node.set('fmt', txt)
		vrs, i = getUInt32(node.data, i)
		data = b'\x04\xBC\x02\x00\x00'       # ACIS-Version
		data += b'\x04' + node.data[i:i+4]   # Number of records
		data += b'\x04' + node.data[i+4:i+8] # Number of bodies
		data += b'\x04' + node.data[i+8:]    # Flags + entities
		lst = []
		header = Header()
		i = header.readBinary(data)
		index = 0
		clearEntities()
		entities = {}
		l = len(data)
		e = (l - 17) if (getFileVersion() > 2010) else (l - 25)
		while (i < e):
			entity, i = readEntityBinary(data, i, e)
			entity.index = index
			entities[index] = entity
			lst.append(entity)
			convert2Version7(entity)
			index += 1
			if (entity.name == "End-of-ACIS-data"):
				entity.index = -2
				break
		i = len(node.data) - node.get('lenFooter') + 0x18
		i = self.skipBlockSize(i)
		resolveEntityReferences(entities, lst)
		node.set('SAT', [header, lst])
		node.segment.AcisList.append(node)
		dumpSat(node)
		return i

	def ReadTrailer(self, buffer, offset):
		i = offset
		if (getFileVersion() > 2014):
			u8_0, i = getUInt8(buffer, i)
			if (u8_0  == 1):
				n, i = getUInt32(buffer, i)
				txt = []
				if ((n & 0x80000000) > 0):
					pass # check  X-Ref???
				else:
					while (n > 0):
						n -= 1
						k, i = getLen32Text8(buffer, i)
						u32_1, i = getUInt32(buffer, i)
						if (u32_1   == 0b0001):
							v, i = getUInt8A(buffer, i, 3)
						elif (u32_1 == 0b0011):
							v, i = getUInt16A(buffer, i, 2)
						elif (u32_1 == 0b0111):
							v, i = getUInt16A(buffer, i, 2)
						elif (u32_1 == 0b1000):
							v, i = getUInt16A(buffer, i, 3)
						elif (u32_1 == 0b1010):
							v, i = getUInt16A(buffer, i, 3)
						elif (u32_1 == 0b1011):
							v, i = getUInt16A(buffer, i, 5)
						else:
							raise ValueError(u"Unknown property value type 0x%02X!" %(u32_1))
						txt.append((k,v))
					i = CheckList(buffer, i, 0x0006)
					cnt, i = getUInt32(buffer, i)
					if (cnt > 0):
						arr32, i = getUInt32A(buffer, i, 2)
						values = []
						while (cnt > 0):
							cnt -= 1
							txt, i = getLen32Text8(buffer, i)
							a, i = getUInt16A(buffer, i, 2)
							ref = NodeRef(a[0], a[1], NodeRef.TYPE_CROSS)
							values.append([txt, ref])
		return i

	def ReadSegmentData(self, file, buffer, seg):
		showTree = False

		if (not self.skipDumpRawData()):
			self.dumpRawData(seg, buffer)

		self.nodeCounter = 0

		try:
			i = 0

			seg.elementNodes = {}
			seg.indexNodes   = {}
			#SECTION = [UUID_IDX_U8][RES_U24 = 0x000001][DATA][DATA_LENGTH_U32][TRAILER]
			for sec in seg.sec1:
				if (sec.flags == 1):
					start = i
					data = self.ReadBlock(file, buffer, i, sec.length, seg)
					i += data.size + 4
					l, i = getUInt32(buffer, i)
					i = self.ReadTrailer(buffer, i)
					if ((l != 0) and (sec.length != l)):
						logError('%s: BLOCK[%04X] - incorrect block size %X != 	%X found for offset %X for %s!' %(self.__class__.__name__, data.index, l, u32_0, start, data.typeName))
			showTree = True

		finally:
			if (showTree):
				tree = buildTree(file, seg)
				seg.tree = tree
				self.postRead(seg)
		return
