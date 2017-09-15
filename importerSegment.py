#!/usr/bin/env python

'''
importerSegment.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

import re
import traceback
from importerClasses   import *
from importerSegNode   import BinaryNode, isList, NodeRef
from importerUtils     import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.4.0'
__status__      = 'In-Development'

_listPattern = re.compile('[^\x00]\x00\x00\x30')

_fmt_new = False

ENCODING_FS = 'utf8'

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
	assert (index in seg.sec4), 'Index %X not defined in segment\'s section No.4!' %(index)
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
									val, i = getFloat32A(data, i, 3)
									val = FloatArr2Str(val)
								elif (cls == 0x0131):
									val, i = getFloat32A(data, i, 2)
									val = FloatArr2Str(val)
								elif (cls == 0x0107):
									val, i = getFloat64A(data, i, 2)
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
					file.write('%04X: \'%s\'\n' %(i1, txt))
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
					file.write('%04X: \'%s\'\n' %(i2, txt))
					iOld = i
				else:
					i = i2+4
			except:
				i += 5
			m2 = p2.search(data, i)

	file.write(HexAsciiDump(data[iOld:], iOld, False))
	return

def getBranchNode(data, isRef):
	if (data.typeName == 'Parameter'):               return ParameterNode(data, isRef)
	if (data.typeName == 'ParameterText'):           return ParameterTextNode(data, isRef)
	if (data.typeName == 'ParameterBoolean'):        return ValueNode(data, isRef)
	if (data.typeName == 'Enum'):                    return EnumNode(data, isRef)
	if (data.typeName == 'Feature'):                 return FeatureNode(data, isRef)
	if (data.typeName == 'Point2D'):                 return PointNode(data, isRef)
	if (data.typeName == 'BlockPoint2D'):            return PointNode(data, isRef)
	if (data.typeName == 'Point3D'):                 return PointNode(data, isRef)
	if (data.typeName == 'Line2D'):                  return LineNode(data, isRef)
	if (data.typeName == 'Line3D'):                  return LineNode(data, isRef)
	if (data.typeName == 'Circle2D'):                return CircleNode(data, isRef)
	if (data.typeName == 'Circle3D'):                return CircleNode(data, isRef)
	if (data.typeName == 'Geometric_Radius2D'):      return GeometricRadius2DNode(data, isRef)
	if (data.typeName == 'Geometric_Coincident2D'):  return GeometricCoincident2DNode(data, isRef)
	if (data.typeName == 'Dimension_Distance2D'):    return DimensionDistance2DNode(data, isRef)
	if (data.typeName == 'Dimension_Angle2Line2D'):  return DimensionAngleNode(data, isRef)
	if (data.typeName == 'Dimension_Angle3Point2D'): return DimensionAngleNode(data, isRef)
	if (data.typeName == 'SurfaceBodies'):           return SurfaceBodiesNode(data, isRef)
	if (data.typeName == 'SolidBody'):               return SurfaceBodiesNode(data, isRef)
	return DataNode(data, isRef)

def buildBranchRef(parent, file, nodes, ref, level):
	branch = getBranchNode(ref.data, True)
	parent.append(branch)

	num = ''
	if (ref.number >= 0):
		num = '[%02X] ' %(ref.number)
	reftext = branch.getRefText()
	if (not isinstance(reftext, unicode)):
		print branch.typeName, type(reftext)
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
				logError('>E0010: (%04X): %s - Index out of range (%X>%X)!' %(data.index, data.typeName, ref.index, l))

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

def Read_F645595C_chunk(offset, node):
	key, i = getUInt8(node.data, offset)
	val = None

	if (key == 0x04):
		val, i = getSInt32(node.data, i)
	elif (key == 0x06):
		val, i = getFloat32A(node.data, i, 2)
	elif (key == 0x07):
		val, i = getLen8Text8(node.data, i)
	elif (key == 0x0A):
		val, i = Read_F645595C_chunk(i, node)
	elif (key == 0x0B):
		dummy0, i = Read_F645595C_chunk(i, node)
		dummy1, i = Read_F645595C_chunk(i, node)
		val = [dummy0, dummy1]
	elif (key == 0x0C):
		val, i = getSInt32(node.data, i)
	elif (key == 0x0D):
		val, i = getLen8Text8(node.data, i)
	elif (key == 0x0E):
		val, i = getLen8Text8(node.data, i)
	elif (key == 0x0F):
		val, i = Read_F645595C_chunk(i, node)
	elif (key == 0x10):
		val, i = Read_F645595C_chunk(i, node)
	elif (key == 0x11):
		val = None
	elif (key == 0x13):
		val, i = getFloat64A(node.data, i, 3)
	elif (key == 0x14):
		val, i = getFloat64A(node.data, i, 3)
	elif (key == 0x15):
		val, i = getUInt32(node.data, i)
	else:
		assert (False), '%04X: Don\'t know to %X!' %(node.offset + offset, key)

	chunk = BRepChunk(key, val)
	return chunk, i

class SegmentReader(object):

	def __init__(self, analyseLists = True):
		self.nodeCounter = 0
		self.analyseLists = analyseLists
		self.fmt_old = (getFileVersion() < 2011)
		self.nodeDict = {}

	def createNewNode(self):
		return BinaryNode()

	def ReadUnknown(self, node, block, file, logError = False, analyseLists = True):
		l = len(block)

		if (l > 0):
			i = 0
			if (logError):
				a, dummy = getUInt8A(block, 0, len(block))
				logMessage('%s: %s\t%s\t%s' %(self.__class__.__name__, getInventorFile(), node.typeID, IntArr2Str(a, 2)), LOG.LOG_ERROR)

			if (analyseLists):
				iOld = i
				m3 = _listPattern.search(block, i)
				while (m3):
					i = getStart(m3, block, 0)
					arr, i2 = getUInt16A(block, i, 2)
					if (isList(arr, 0x0002)):
						dumpData(file, block, iOld, i)
						lst, i = node.ReadMetaData_02(block, i2, AbstractNode._TYP_GUESS_)
						iOld = i
					elif (isList(arr, 0x0003)):
						dumpData(file, block, iOld, i)
						lst, i = node.ReadMetaData_03(block, i2, AbstractNode._TYP_NODE_REF_)
						iOld = i
					elif (isList(arr, 0x0004)):
						dumpData(file, block, iOld, i)
						lst, i = node.ReadMetaData_04(block, i2, AbstractNode._TYP_NODE_REF_)
						iOld = i
					elif (isList(arr, 0x0006)):
						dumpData(file, block, iOld, i)
						lst, i = node.ReadMetaData_MAP(block, i2, AbstractNode._TYP_MAP_KEY_REF_)
						iOld = i
					elif (isList(arr, 0x0007)):
						dumpData(file, block, iOld, i)
						lst, i = node.ReadMetaData_MAP(block, i2, AbstractNode._TYP_MAP_KEY_REF_)
						iOld = i
					else:
						i = i2
					m3 = _listPattern.search(block, i)
				dumpData(file, block, i, len(block))
			else:
				l = node.ReadUInt8A(block, 0, l, 'a0')

		return l

	def HandleBlock(self, file, node):
		try:
			readType = getattr(self, 'Read_%s' %(node.typeName))
			i = readType(node)
			if (i < len(node.data)):
				i = node.ReadUInt8A(i, len(node.data) - i, '\taX')
		except Exception as e:
			logError('ERROR> (%04X): %s - %s' %(node.index, node.typeName, e))
			logError('>E: ' + traceback.format_exc())

		return

	def setNodeData(self, node, data):
		offset = node.offset
		nodeTypeID, i = getUInt8(data, offset - 4)
		node.typeID = getNodeType(nodeTypeID, node.seg)
		if (isinstance(node.typeID, UUID)):
			node.typeName = '%08X' % (node.typeID.time_low)
		else:
			node.typeName = '%08X' % (node.typeID)
		node.data = data[offset:offset + node.size]

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

	def skipBlockSize(self, offset):
		i = offset
		if (self.fmt_old):
			i += 4
		return i

	def dumpRawData(self, seg, data):
		filename = '%s\\%sB.bin' %(getInventorFile()[0:-4], seg.name)
		newFileRaw = open (filename, 'wb')
		newFileRaw.write(data)
		newFileRaw.close()
		return

	def dumpNodeDict(self):
		return

	def ReadSegmentData(self, file, buffer, seg):
		vers = getFileVersion()
		showTree = False

		if (not self.skipDumpRawData()):
			self.dumpRawData(seg, buffer)

		self.nodeCounter = 0

		hdrSize = IFF(vers < 2015, 4, 5)

		logMessage('>I0002: reaging %s binary buffer ...' %(seg.name), LOG.LOG_INFO)

		try:
			i = 4

			seg.elementNodes = {}
			seg.indexNodes   = {}
			for sec in seg.sec1:
				if (sec.flags == 1):
					l = sec.length
					start = i - 4
					data = self.ReadBlock(file, buffer, i, l, seg)
					i += data.size
					t = '%08X' % (data.typeID.time_low)
					if (not t in self.nodeDict):
						count = 1
					else:
						count = self.nodeDict[t] + 1
					self.nodeDict[t] = count
					u32_0, i = getUInt32(buffer, i)
					assert (u32_0 == l), '%s: BLOCK[%X] - incorrect block size %X != %X found for offset %X for %s!' %(self.__class__.__name__, data.index, l, u32_0, start, data.typeName)
					i += hdrSize
			showTree = True

		finally:
			if (showTree):
				tree = buildTree(file, seg)
				seg.tree = tree

				self.dumpNodeDict()

		return
