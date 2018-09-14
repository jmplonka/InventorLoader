# -*- coding: utf-8 -*-

'''
importerSegment.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

import re, traceback
from importerClasses   import *
from importerSegNode   import isList, CheckList, BinaryNode, NodeRef
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
				logError(u"ERROR> (%04X): %s - Index out of range (%X>%X)!", data.index, data.typeName, ref.index, l)

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

	def ReadUnknown(self, node, block, file, logError = False, analyseLists = True):
		l = len(block)

		if (l > 0):
			i = 0
			if (logError):
				a, dummy = getUInt8A(block, 0, len(block))
				logError(u"%s: %s\t%s\t%s", self.__class__.__name__, getInventorFile(), node.typeID, IntArr2Str(a, 2))

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
		i = 0

		try:
			readType = getattr(self, 'Read_%s' %(node.typeName))
			i = readType(node)
		except Exception as e:
			if (not isinstance(e, AttributeError)):
				logError(traceback.format_exc())
			elif (self.__class__.__name__ != "SegmentReader"):
				logError(u"ERROR> (%04X) - %s: %s", node.index, node.typeName, e)

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
		node.typeName = 'ASM'
		i = node.Read_Header0()
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
