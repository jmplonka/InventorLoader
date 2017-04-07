#!/usr/bin/env python

'''
importerSegment.py:

Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

import re
from importerUtils     import *
from importerClasses   import BinaryNode, ResultItem4, GraphicsFont, DataNode, Header0, Angle, NodeRef

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

_listPattern = re.compile('[^\x00]\x00\x00\x30')

_fmt_old = False
_fmt_new = False

def checkReadAll(node, i, l):
	if (i < l):
		assert (i == l), '%s: Have not read all data (%d <> %d)' %(node.typeID, i, l)
	elif (i > l):
		assert (i == l), '%s: Have read beyond data (%d <> %d)' %(node.typeID, i, l)

	return

def dumpData(file, data, offset, end):
	if (offset < end):
		arr8, dummy = getUInt8A(data, offset, end - offset)
		if (not file is None):
			file.write('\t[%s]\n' %(IntArr2Str(arr8, 2)))
	return

def isList(data, code):
	return ((data[-1] == 0x3000) and (data[-2] == code))

def CheckList(data, offset, type):
	lst, i = getUInt16A(data, offset, 2)
	if (getFileVersion() < 2015):
		if (lst[0] == 0 and (lst[1] == 0)):
			return i - 4 # keep fingers crossed that this is really the number of bytes!
	assert (isList(lst, type)), 'Expected list %d - not [%s]' %(type, IntArr2Str(lst, 4))
	return i

def getNodeType(index, seg):
	if (index in seg.sec4):
		blockType = seg.sec4[index]
		return blockType.typeID
	return index

def getStart(m, data, offset):
	if (m):
		return m.start() - offset
	return len(data)

def skipBlockSize(block, offset):
	i = offset
	if (_fmt_old):
		blockSize, i = getUInt32(block, i)
	return i

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

def ReadChildRef(block, offset, node):
	u16_0, i = getUInt16(block, offset)
	u16_1, i = getUInt16(block, i)
	ref = NodeRef(u16_0, u16_1, NodeRef.TYPE_CHILD)

	node.set('ref', None)

	if (ref.index > 0):
		if (not ref.index in node.childIndexes):
			node.childIndexes.append(ref)
		node.set('ref', ref)

	return i

def ReadCrossRef(block, offset, node):
	u16_0, i = getUInt16(block, offset)
	u16_1, i = getUInt16(block, i)
	ref = NodeRef(u16_0, u16_1, NodeRef.TYPE_CROSS)

	node.set('ref', None)

	if (ref.index > 0):
		if (not ref.index in node.childIndexes):
			node.childIndexes.append(ref)
			node.set('ref', ref)

	return i

def ReadParentRef(block, offset, node):
	u16_0, i = getUInt16(block, offset)
	u16_1, i = getUInt16(block, i)
	ref = NodeRef(u16_0, u16_1, NodeRef.TYPE_PARENT)

	node.set('parent', None)
	if (ref.index > 0):
		node.parentIndex = ref
		node.set('parent', ref)

	return i

def buildBranchRef(file, nodes, node, level = 0):
	branch = None
	if (node.printable):
		branch = DataNode(node)
		file.write('%s-> %s\n' %(level * '\t', branch))

	return branch

def buildBranch(file, nodes, node, level = 0):
	branch = None
	if (node.printable):
		branch = DataNode(node)
		file.write('%s%s\n' %(level * '\t', branch))

		for ref in node.childIndexes:
			if (ref.index in nodes):
				child = nodes[ref.index]
				if (ref.type == NodeRef.TYPE_CHILD):
					subBranch = buildBranch(file, nodes, child, level + 1)
					if (subBranch):
						branch.append(subBranch)
				elif (ref.type == NodeRef.TYPE_CROSS):
					xRefLeaf = buildBranchRef(file, nodes, child, level + 1)
					if (xRefLeaf):
						branch.append(xRefLeaf)

	return branch

def buildTree(file, nodes):
	l = len(nodes)
	tree = DataNode(None)

	for idx1 in nodes:
		node = nodes[idx1]
		for ref in node.childIndexes:
			if (ref.index in nodes):
				nodes[ref.index].hasParent = True
			else:
				logError('>E0010: Index out of range (%d>%d) for %s' %(idx, l, node.typeID))

		ref = node.parentIndex
		node.parent = None
		if (ref):
			if (ref.index in nodes):
				node.parent = nodes[ref.index]

	for idx1 in nodes:
		node = nodes[idx1]
		if (node.hasParent == False):
			ref = node.parent
			if (ref):
				parent = nodes[ref.index]
#				logError('>E0011: Parent %s.%08X(%04X) set but not referenced: %s.%08X(%04X)' %(parent.__class__.__name__, parent.typeID.time_low, parent.index, node.__class__.__name__, node.typeID.time_low, node.index))
			branch = buildBranch(file, nodes, node)
			if (branch):
				tree.append(branch)
	return tree

class SegmentReader(object):
	_TYP_GUESS_             = 0x0000
	_TYP_2D_UINT16_         = 0x0001
	_TYP_2D_SINT16_         = 0x0002
	_TYP_2D_UINT32_         = 0x0003
	_TYP_2D_SINT32_         = 0x0004
	_TYP_2D_FLOAT32_        = 0x0005
	_TYP_2D_FLOAT64_        = 0x0006
	_TYP_3D_UINT16_         = 0x0007
	_TYP_3D_SINT16_         = 0x0008
	_TYP_3D_UINT32_         = 0x0009
	_TYP_3D_SINT32_         = 0x000A
	_TYP_3D_FLOAT32_        = 0x000B
	_TYP_3D_FLOAT64_        = 0x000C
	_TYP_1D_UINT32_         = 0x000D
	_TYP_1D_CHAR_           = 0x000E

	_TYP_FONT_              = 0x0011
	_TYP_2D_F64_U32_4D_U8_  = 0x0012
	_TYP_NODE_REF_          = 0x0013
	_TYP_STRING16_          = 0x0014
	_TYP_RESULT_ITEM4_      = 0x0015
	_TYP_NODE_X_REF_        = 0x0016

	_TYP_LIST_GUESS_        = 0x8000
	_TYP_LIST_2D_UINT16_    = 0x8001
	_TYP_LIST_2D_SINT16_    = 0x8002
	_TYP_LIST_2D_UINT32_    = 0x8003
	_TYP_LIST_2D_SINT32_    = 0x8004
	_TYP_LIST_2D_FLOAT32_   = 0x8005
	_TYP_LIST_2D_FLOAT64_   = 0x8006
	_TYP_LIST_3D_UINT16_    = 0x8007
	_TYP_LIST_3D_SINT16_    = 0x8008
	_TYP_LIST_3D_UINT32_    = 0x8009
	_TYP_LIST_3D_SINT32_    = 0x800A
	_TYP_LIST_3D_FLOAT32_   = 0x800B
	_TYP_LIST_3D_FLOAT64_   = 0x800C
	_TYP_LIST_FONT_         = 0x8011

	def __init__(self, analyseLists = True):
		global _fmt_old
		self.nodeCounter = 0
		self.hdrSize    =  0
		self.analyseLists = analyseLists
		_fmt_old = (getFileVersion() < 2011)

	def ReadUInt8(self, block, offset, node, name):
		x, i = getUInt8(block, offset)
		node.set(name, x)
		node.content += ' %s=%02X' %(name, x)
		return i

	def ReadUInt8A(self, block, offset, n, node, name):
		x, i = getUInt8A(block, offset, n)
		node.set(name, x)
		node.content += ' %s=[%s]' %(name, IntArr2Str(x, 2))
		return i

	def ReadUInt16(self, block, offset, node, name):
		x, i = getUInt16(block, offset)
		node.set(name, x)
		node.content += ' %s=%04X' %(name, x)
		return i

	def ReadUInt16A(self, block, offset, n, node, name):
		x, i = getUInt16A(block, offset, n)
		node.set(name, x)
		node.content += ' %s=[%s]' %(name, IntArr2Str(x, 4))
		return i

	def ReadUInt32(self, block, offset, node, name):
		x, i = getUInt32(block, offset)
		node.set(name, x)
		node.content += ' %s=%06X' %(name, x)
		return i

	def ReadUInt32A(self, block, offset, n, node, name):
		x, i = getUInt32A(block, offset, n)
		node.set(name, x)
		node.content += ' %s=[%s]' %(name, IntArr2Str(x, 4))
		return i

	def ReadSInt32(self, block, offset, node, name):
		x, i = getSInt32(block, offset)
		node.set(name, x)
		node.content += ' %s=%X' %(name, x)
		return i

	def ReadSInt32A(self, block, offset, n, node, name):
		x, i = getSInt32A(block, offset, n)
		node.set(name, x)
		node.content += ' %s=[%s]' %(name, IntArr2Str(x, 4))
		return i

	def ReadFloat32(self, block, offset, node, name):
		x, i = getFloat32(block, offset)
		node.set(name, x)
		node.content += ' %s=%g' %(name, x)
		return i

	def ReadFloat32A(self, block, offset, n, node, name):
		x, i = getFloat32A(block, offset, n)
		node.set(name, x)
		node.content += ' %s=(%s)' %(name, FloatArr2Str(x))
		return i

	def ReadFloat64(self, block, offset, node, name):
		x, i = getFloat64(block, offset)
		node.set(name, x)
		node.content += ' %s=%g' %(name, x)
		return i

	def ReadFloat64A(self, block, offset, n, node, name):
		x, i = getFloat64A(block, offset, n)
		node.set(name, x)
		node.content += ' %s=(%s)' %(name, FloatArr2Str(x))
		return i

	def ReadUUID(self, block, offset, node, name):
		x, i = getUUID(block, offset, '%08X[%d]' %(node.typeID.time_low, node.index))
		node.set(name, x)
		node.content += ' %s=%r' %(name, x)
		return i

	def ReadColorRGBA(self, block, offset, node, name):
		x, i = getColorRGBA(block, offset)
		node.set(name, x)
		node.content += ' %s=%s' %(name, x)
		return i

	def ReadAngle(self, block, offset, node, name):
		x, i = getFloat64(block, offset)
		x = Angle(x)
		node.set(name, x)
		node.content += ' %s=%s' %(name, x)
		return i

	def ReadLen32Text16(self, block, offset, node, name = None):
		x, i = getLen32Text16(block, offset)
		if (name):
			node.set(name, x)
			node.content += ' %s=\'%s\'' %(name, x)
		else:
			node.name = x
		return i

	def Read_Header0(self, block, node):
		u32_0, i = getUInt32(block, 0)
		u16_0, i = getUInt16(block, i)
		i = skipBlockSize(block, i)

		hdr = Header0(u32_0, u16_0)
		node.set('Header0', hdr)
		node.content += ' hdr={%s}' %(hdr)

		return i

	def Read_Header1(self, block, node):
		i = skipBlockSize(block, 0)
		i = ReadParentRef(block, i, node)
		return i

	def ReadMetaData_02(self, data, offset, node, typ):
		sep = ''
		hasFlag = (getFileVersion() < 2011)
		cnt, i = getUInt32(data, offset)
		lst = []

		if (cnt > 0):
			arr32, i = getUInt32A(data, i, 2)

			if (typ == SegmentReader._TYP_GUESS_):
				t = arr32[1]
				if (t == 0x0107):
					t = SegmentReader._TYP_2D_F64_U32_4D_U8_
				elif (t >= 0x0114 and t <= 0x0126):
					t = SegmentReader._TYP_3D_FLOAT32_
				elif (t >= 0x0129 and t <= 0x013F) or (t == 0x0146):
					t = SegmentReader._TYP_2D_FLOAT32_
				elif (t == 0x0142):
					t = SegmentReader._TYP_FONT_
				else:
					t = SegmentReader._TYP_NODE_REF_
			else:
				t = typ

			if (t == SegmentReader._TYP_1D_CHAR_):
				val, i = getText8(data, i, cnt)
				lst.append(val)
				node.content += val
			else:
				#if (t != SegmentReader._TYP_NODE_REF_):
				#	node.content += '[0002,3000] - [%s]: {' %(IntArr2Str(arr32, 4))
				j = 0
				while (j < cnt):
					str = ''
					if (t == SegmentReader._TYP_NODE_REF_):
						i = ReadChildRef(data, i, node)
						val = node.get('ref')
						str = ''
					elif (t == SegmentReader._TYP_1D_UINT32_):
						val, i = getUInt32(data, i)
						str = '%04X' %(val)
					elif (t == SegmentReader._TYP_2D_UINT16_):
						val, i = getUInt16A(data, i, 2)
						str = '(%s)' %(IntArr2Str(val, 4))
					elif (t == SegmentReader._TYP_2D_SINT16_):
						val, i = getSInt16A(data, i, 2)
						if (hasFlag):
							flg, i = getUInt32(data, i)
						str = '(%s)' %(IntArr2Str(val, 4))
					elif (t == SegmentReader._TYP_2D_UINT32_):
						val, i = getUInt32A(data, i, 2)
						str = '(%s)' %(IntArr2Str(val, 8))
					elif (t == SegmentReader._TYP_2D_SINT32_):
						val, i = getSInt32A(data, i, 2)
						str = '(%s)' %(IntArr2Str(val, 8))
					elif (t == SegmentReader._TYP_2D_FLOAT32_):
						val, i = getFloat32A(data, i, 2)
						if (hasFlag):
							flg, i = getUInt32(data, i)
						str = '(%s)' %(FloatArr2Str(val))
					elif (t == SegmentReader._TYP_2D_FLOAT64_):
						val, i = getFloat64A(data, i, 2)
						if (hasFlag):
							flg, i = getUInt32(data, i)
						str = '(%s)' %(FloatArr2Str(val))
					elif (t == SegmentReader._TYP_3D_UINT16_):
						val, i = getUInt16A(data, i, 3)
						if (hasFlag):
							flg, i = getUInt32(data, i)
						str = '(%s)' %(IntArr2Str(val, 4))
					elif (t == SegmentReader._TYP_3D_SINT16_):
						val, i = getSInt16A(data, i, 3)
						if (hasFlag):
							flg, i = getUInt32(data, i)
						str = '(%s)' %(IntArr2Str(val, 4))
					elif (t == SegmentReader._TYP_3D_UINT32_):
						val, i = getUInt32A(data, i, 3)
						if (hasFlag):
							flg, i = getUInt32(data, i)
						str = '(%s)' %(IntArr2Str(val, 8))
					elif (t == SegmentReader._TYP_3D_SINT32_):
						val, i = getSInt32A(data, i, 3)
						if (hasFlag):
							flg, i = getUInt32(data, i)
						str = '(%s)' %(IntArr2Str(val, 8))
					elif (t == SegmentReader._TYP_3D_FLOAT32_): # 3D-Float32
						val, i = getFloat32A(data, i, 3)
						if (hasFlag):
							flg, i = getUInt32(data, i)
						str = '(%s)' %(FloatArr2Str(val))
					elif (t == SegmentReader._TYP_3D_FLOAT64_):
						val, i = getFloat64A(data, i, 3)
						str = '(%s)' %(FloatArr2Str(val))
					elif (t == SegmentReader._TYP_FONT_): # Font settings
						val = GraphicsFont()
						val.number, i = getUInt32(data, i)
						val.ukn1, i = getUInt16A(data, i, 4)
						val.ukn2, i = getUInt8A(data, i, 2)
						val.ukn3, i = getUInt16A(data, i, 2)
						val.name, i = getLen32Text16(data, i)
						val.f, i = getFloat32A(data, i, 2)
						val.ukn4, i = getUInt8A(data, i, 3)
						str = '%s' %(val)
					elif (t == SegmentReader._TYP_2D_F64_U32_4D_U8_):
						val = []
						f, i = getFloat64A(data, i, 2)
						val.append(f)
						u, i = getUInt32(data, i)
						val.append(u)
						if (hasFlag):
							flg, i = getUInt32(data, i)
						a, i = getUInt8A(data, i, 4)
						val.append(a)
						if (hasFlag):
							flg, i = getUInt32(data, i)
						str = '(%s) %X [%s]' %(FloatArr2Str(f), u, IntArr2Str(a, 1))
					elif (t == SegmentReader._TYP_LIST_GUESS_):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_GUESS_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_2D_UINT16_ ):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_NODE_REF_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_2D_SINT16_ ):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_2D_SINT16_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_2D_UINT32_ ):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_2D_UINT32_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_2D_SINT32_ ):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_2D_SINT32_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_2D_FLOAT32_):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_2D_FLOAT32_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_2D_FLOAT64_):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_2D_FLOAT64_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_3D_UINT16_ ):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_3D_UINT16_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_3D_SINT16_ ):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_3D_SINT16_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_3D_UINT32_ ):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_3D_UINT32_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_3D_SINT32_ ):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_3D_SINT32_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_3D_FLOAT32_):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_3D_FLOAT32_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_3D_FLOAT64_):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_3D_FLOAT64_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					elif (t == SegmentReader._TYP_LIST_FONT_):
						i = self.ReadList2(data, i, node, SegmentReader._TYP_FONT_, 'tmp')
						val = node.get('tmp')
						node.delete('tmp')
					else:
						val, i = getUInt16A(data, i, 2)
						str = '[%s]' %(IntArr2Str(val[0], 1))
					lst.append(val)

					if (len(str) > 0):
						node.content += '%s%s' %(sep, str)
					sep = ','
					j += 1
				#if (t != SegmentReader._TYP_NODE_REF_):
				#	node.content += '}'
		return lst, i

	def ReadMetaData_03(self, data, offset, node, typ):
		lst = []

		cnt, i = getUInt32(data, offset)
		if (cnt > 0):
			u32_0, i = getUInt32A(data, i, 1)
			j = 0
			#sep = ''
			while (j < cnt):
				j += 1
				if (typ == SegmentReader._TYP_NODE_X_REF_):
					i = ReadCrossRef(data, i, node)
				else:
					i = ReadChildRef(data, i, node)
				#val = node.get('ref')
				#node.content += '%s%s' %(sep, val)
				#sep = ','

		return lst, i

	def ReadMetaData_04(self, data, offset, node, typ):
		lst = []
		sep = ''
		hasFlag = (getFileVersion() < 2011)

		cnt, i = getUInt32(data, offset)
		if (cnt > 0):
			arr16, i = getUInt16A(data, i, 2)
			t = typ
			if (t == SegmentReader._TYP_GUESS_):
				if ((arr16[0] == 0x0101) and (arr16[0]==0x0000)):
					t = SegmentReader._TYP_RESULT_ITEM4_
				else:
					t = SegmentReader._TYP_NODE_REF_
			#node.content += '[0004,3000] - [%s]: {' %(IntArr2Str(arr16, 4))
			j = 0
			while (j < cnt):
				j += 1

				if (t == SegmentReader._TYP_NODE_REF_):
					val, i = getUInt16A(data, i, 2)
					str = '%s' %(IntArr2Str(val, 4))
				elif (t == SegmentReader._TYP_STRING16_):
					val, i = getLen32Text8(data, i)
					str = '\"%s\"' %(val)
				elif (t == SegmentReader._TYP_2D_SINT32_):
					val, i = getSInt32A(data, i, 2)
					str = '[%s]' %(IntArr2Str(val, 8))
				elif (t == SegmentReader._TYP_2D_UINT32_):
					val, i = getUInt32A(data, i, 2)
					if (hasFlag):
						dummy, i = getUInt32(data, i)
					str = '[%s]' %(IntArr2Str(val, 8))
				elif (t == SegmentReader._TYP_RESULT_ITEM4_):
					val = ResultItem4()
					val.a0, i = getUInt16A(data, i, 4)
					val.a1, i = getFloat64A(data, i, 3)
					val.a2, i = getFloat64A(data, i, 3)
					if (hasFlag):
						dummy, i = getUInt32(data, i)
					str = '%s' %(val)
				lst.append(val)
				node.content += '%s%s' %(sep, str)
				sep = ','
			#node.content += '}'

		return lst, i

	def ReadMetaData_06(self, data, offset, node):
		lst = []
		sep = ''

		cnt, i = getUInt32(data, offset)
		if (cnt > 0):
			arr32, i = getUInt32A(data, i, 2)
			#node.content += '[0006,3000] - [%s]: {' %(IntArr2Str(arr32, 4))
			j = 0
			while (j < cnt):
				j += 1
				key, i = getUInt32(data, i)
				i = ReadChildRef(data, i, node)
				ref = node.get('ref')
				lst.append([key, ref])
				node.content += '%s[%04X: (%s)]' %(sep, key, ref)
				sep = ','
			#node.content += '}'

		return lst, i

	def ReadMetaData_07(self, data, offset, node):
		lst = []
		sep = ''

		cnt, i = getUInt32(data, offset)
		if (cnt > 0):
			arr32, i = getUInt32A(data, i, 2)
			#node.content += '[0007,3000] - [%s]: {' %(IntArr2Str(arr32, 4))
			j = 0
			while (j < cnt):
				j += 1
				key, i = getUInt32(data, i)
				idx, i = getUInt32(data, i)
				idx &= 0x7FFFFFF
				lst.append([key, idx])
				node.content += '%s[%04X: (%04X)]' %(sep, key, idx)
				sep = ','
			#node.content += '}'

		return lst, i

	def ReadList2(self, data, offset, node, typ, name):
		i = CheckList(data, offset, 0x0002)
		node.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_02(data, i, node, typ)
		node.content += '}'
		node.set(name, lst)
		return i

	def ReadList3(self, data, offset, node, typ, name):
		i = CheckList(data, offset, 0x0003)
		node.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_03(data, i, node, SegmentReader._TYP_NODE_REF_)
		node.content += '}'
		node.set(name, lst)
		return i

	def ReadList4(self, data, offset, node, typ, name = 'lst4'):
		i = CheckList(data, offset, 0x0004)
		node.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_04(data, i, node, typ)
		node.content += '}'
		node.set(name, lst)
		return i

	def ReadList6(self, data, offset, node, name = 'lst6'):
		i = CheckList(data, offset, 0x0006)
		node.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_06(data, i, node)
		node.content += '}'
		node.set(name, lst)
		return i

	def ReadList7(self, data, offset, node, name = 'lst7'):
		i = CheckList(data, offset, 0x0007)
		node.content += ' %s={' %(name)
		lst, i = self.ReadMetaData_07(data, i, node)
		node.content += '}'
		node.set(name, lst)
		return i

	def createNewNode(self):
		return BinaryNode()

	def ReadUnknown(self, node, block, file, logError = False, analyseLists = True):
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
					lst, i = self.ReadMetaData_02(block, i2, node, SegmentReader._TYP_GUESS_)
					iOld = i
				elif (isList(arr, 0x0003)):
					dumpData(file, block, iOld, i)
					lst, i = self.ReadMetaData_03(block, i2, node, SegmentReader._TYP_NODE_REF_)
					iOld = i
				elif (isList(arr, 0x0004)):
					dumpData(file, block, iOld, i)
					lst, i = self.ReadMetaData_04(block, i2, node, SegmentReader._TYP_NODE_REF_)
					iOld = i
				elif (isList(arr, 0x0006)):
					dumpData(file, block, iOld, i)
					lst, i = self.ReadMetaData_06(block, i2, node)
					iOld = i
				elif (isList(arr, 0x0007)):
					dumpData(file, block, iOld, i)
					lst, i = self.ReadMetaData_07(block, i2, node)
					iOld = i
				else:
					i = i2
				m3 = _listPattern.search(block, i)

		dumpData(file, block, i, len(block))

		return len(block)

	def ReadUnknownBlock(self, file, node, block, logError = False):
		l = len(block)
		vers = getFileVersion()
		i = 0

		i += self.ReadUnknown(node, block[i:], file, logError, self.analyseLists)

		checkReadAll(node, i, l)

		return

	def HandleBlock(self, file, block, node, seg, logError = False):

		self.ReadUnknownBlock(file, node, block, logError)

		return

	def ReadBlock(self, file, data, offset, size, seg):
		self.nodeCounter += 1
		i = offset - 4
		node = self.createNewNode()
		node.index = self.nodeCounter

		nodeTypeID, i = getUInt8(data, i)
		node.typeID = getNodeType(nodeTypeID, seg)
		if (isinstance(node.typeID, UUID)):
			node.typeName = '%08X' % (node.typeID.time_low)
		else:
			node.typeName = '%08X' % (node.typeID)

		block = data[offset:offset + size]

		self.HandleBlock(file, block, node, seg)

		return node

	def skipDumpRawData(self):
		return False

	def dumpRawData(self, seg, data):
		folder = getInventorFile()[0:-4]

		filename = '%s\\%sB.bin' %(folder, seg.name)
		newFileRaw = open (filename, 'wb')
		newFileRaw.write(data)
		newFileRaw.close()

		return

	def ReadSegmentData(self, file, data, seg):
		vers = getFileVersion()
		nodes = {}
		showTree = False

		if (not self.skipDumpRawData()):
			self.dumpRawData(seg, data)

		self.nodeCounter = 0

		if (vers < 2015):
			self.hdrSize = 4
		else:
			self.hdrSize = 5

		logMessage('>I0002: reaging %s binary data ...' %(seg.name), LOG.LOG_INFO)

		try:
			i = 4

			for sec in seg.sec1:
				if (sec.flags == 1):
					l = sec.length
					node = self.ReadBlock(file, data, i, l, seg)
					nodes[node.index] = node
					i += self.hdrSize + l + 4
			showTree = True

		finally:
			if (i < len(data)):
				file.write('\n>>> FOOTER <<<\n')
				dumpRemainingDataB(file, data, i)

			if (showTree):
				tree = buildTree(file, nodes)
				seg.tree = tree

		return
