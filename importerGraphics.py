#!/usr/bin/env python

'''
importerGraphics.py:

	Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) graphics data.
	The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
	TODO:
'''

from importerSegment import SegmentReader, ReadChildRef, ReadCrossRef, ReadParentRef, checkReadAll, skipBlockSize
from importerClasses import GraphicsNode, GraphicsFont, B32BF6AC, _32RRR2, _32RA
from importerUtils   import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

class GraphicsReader(SegmentReader):

	def __init__(self):
		super(GraphicsReader, self).__init__(True)

	def createNewNode(self):
		return GraphicsNode()

	def skipDumpRawData(self):
		return True

	def Read_32RA(self, block, node):
		i = self.Read_Header0(block, node)
		u16_0, i = getUInt16(block, i)
		u16_1, i = getUInt16(block, i)
		i = ReadChildRef(block, i, node)
		u8_0, i = getUInt8(block, i)
		i = skipBlockSize(block, i)

		val = _32RA(u16_0, u16_1, u8_0)
		node.set('32RRR2', val)
		node.content += ' 32RR2={%s}' %(val)

		return i

	def Read_32RRR2(self, block, node):
		i = self.Read_Header0(block, node)
		u16_0, i = getUInt16(block, i)
		u16_1, i = getUInt16(block, i)
		i = ReadChildRef(block, i, node)
		i = ReadChildRef(block, i, node)
		i = ReadParentRef(block, i, node)
		u32_0, i = getUInt32(block, i)
		i = skipBlockSize(block, i)

		val = _32RRR2(u16_0, u16_1, u32_0)
		node.set('32RA', val)
		node.content += ' 32RA={%s}' %(val)

		return i

	def Read_ColorAttr(self, block, offset, node):
		i = skipBlockSize(block, offset)
		i = self.ReadUInt8A(block, i, 2, node, 'ColorAttr.a0')
		i = self.ReadColorRGBA(block, i, node, 'ColorAttr.c0')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'ColorAttr.c1')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'ColorAttr.c2')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'ColorAttr.c3')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 2, node, 'ColorAttr.a5')

		return i

	def Read_HeaderParent(self, block, node):
		i = skipBlockSize(block, 0)
		i = skipBlockSize(block, i)
		i = ReadParentRef(block, i, node)
		i = skipBlockSize(block, i)
		return i

	def Read_TypedFloat(self, block, offset, node):
		cnt, i = getUInt32(block, offset)
		lst0 = []
		j = 0
		node.content += '{'
		while (j < cnt):
			j += 1
			t, i = getUInt32(block, i)
			if (t == 0x0B):
				a0, i = getFloat64A(block, i, 0x0C)
				lst0.append(a0)
				node.content += ' %d: (%s)' %(j, FloatArr2Str(a0))
			elif (t == 0x11):
				a0, i = getFloat64A(block, i, 0x0D)
				lst0.append(a0)
				node.content += ' %d: (%s)' %(j, FloatArr2Str(a0))
			elif (t == 0x17):
				a0, i = getFloat64A(block, i, 0x06)
				lst0.append(a0)
				node.content += ' %d: (%s)' %(j, FloatArr2Str(a0))
			else:
				logError('>E0001: Don\'t know how to handle %X in {%s}!' %(t, node.typeID))
		node.content += '}'
		node.set('TypedFloat.lst0', lst0)
		return i

	def Read_CodedFloatA(self, block, offset, node):
		i = self.ReadUInt16A(block, offset, 2, node, 'CodedFloatA.a0')
		a0 = node.get('CodedFloatA.a0')
		if (a0[0] == 0x8000 and a0[1] == 0x7000):
			n = 0x0C
		elif (a0[0] == 0x8000 and a0[1] == 0x7010):
			n = 0x0B
		elif (a0[0] == 0x8000 and a0[1] == 0x7100):
			n = 0x0B
		elif (a0[0] == 0x8001 and a0[1] == 0x7002):
			n = 0x0A
		elif (a0[0] == 0x8001 and a0[1] == 0x7004):
			n = 0x0A
		elif (a0[0] == 0x8001 and a0[1] == 0x7116):
			n = 0x07
		elif (a0[0] == 0x8010 and a0[1] == 0x7100):
			n = 0x0A
		elif (a0[0] == 0x8010 and a0[1] == 0x7110):
			n = 0x0A
		elif (a0[0] == 0x8010 and a0[1] == 0x7171):
			n = 0x07
		elif (a0[0] == 0x8010 and a0[1] == 0x7961):
			n = 0x06
		elif (a0[0] == 0x8010 and a0[1] == 0x7971):
			n = 0x06
		elif (a0[0] == 0x8020 and a0[1] == 0x7010):
			n = 0x0A
		elif (a0[0] == 0x8020 and a0[1] == 0x7200):
			n = 0x0A
		elif (a0[0] == 0x8040 and a0[1] == 0x7000):
			n = 0x0B
		elif (a0[0] == 0x8100 and a0[1] == 0x7000):
			n = 0x0B
		elif (a0[0] == 0x8100 and a0[1] == 0x7190):
			n = 0x09
		elif (a0[0] == 0x8100 and a0[1] == 0x7711):
			n = 0x07
		elif (a0[0] == 0x8100 and a0[1] == 0x7C08):
			n = 0x08
		elif (a0[0] == 0x8100 and a0[1] == 0x7E99):
			n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7004):
			n = 0x09
		elif (a0[0] == 0x8124 and a0[1] == 0x7014):
			n = 0x08
		elif (a0[0] == 0x8124 and a0[1] == 0x7100):
			n = 0x09
		elif (a0[0] == 0x8124 and a0[1] == 0x7110):
			n = 0x08
		elif (a0[0] == 0x8124 and a0[1] == 0x7140):
			n = 0x08
		elif (a0[0] == 0x8124 and a0[1] == 0x7204):
			n = 0x08
		elif (a0[0] == 0x8124 and a0[1] == 0x7256):
			n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x7352):
			n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x7615):
			n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x7657):
			n = 0x03
		elif (a0[0] == 0x8124 and a0[1] == 0x7711):
			n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x7753):
			n = 0x03
		elif (a0[0] == 0x8124 and a0[1] == 0x7E15):
			n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7E57):
			n = 0x02
		elif (a0[0] == 0x8124 and a0[1] == 0x7ED7):
			n = 0x01
		elif (a0[0] == 0x8124 and a0[1] == 0x7EDF):
			n = 0
		elif (a0[0] == 0x8124 and a0[1] == 0x7F11):
			n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7F53):
			n = 0x02
		elif (a0[0] == 0x8124 and a0[1] == 0x7FD3):
			n = 0x01
		elif (a0[0] == 0x8142 and a0[1] == 0x7737):
			n = 0x03
		elif (a0[0] == 0x8142 and a0[1] == 0x7E35):
			n = 0x02
		elif (a0[0] == 0x8200 and a0[1] == 0x7188):
			n = 0x08
		elif (a0[0] == 0x8200 and a0[1] == 0x7200):
			n = 0x0B
		elif (a0[0] == 0x8200 and a0[1] == 0x7280):
			n = 0x0A
		elif (a0[0] == 0x8200 and a0[1] == 0x7300):
			n = 0x0A
		elif (a0[0] == 0x8200 and a0[1] == 0x7522):
			n = 0x07
		elif (a0[0] == 0x8200 and a0[1] == 0x7600):
			n = 0x0A
		elif (a0[0] == 0x8200 and a0[1] == 0x7D22):
			n = 0x06
		elif (a0[0] == 0x8200 and a0[1] == 0x7D2A):
			n = 0x05
		elif (a0[0] == 0x8214 and a0[1] == 0x7522):
			n = 0x05
		elif (a0[0] == 0x8214 and a0[1] == 0x7563):
			n = 0x03
		elif (a0[0] == 0x8214 and a0[1] == 0x7577):
			n = 0x03
		elif (a0[0] == 0x8214 and a0[1] == 0x75B6):
			n = 0x04
		elif (a0[0] == 0x8214 and a0[1] == 0x7961):
			n = 0x04
		elif (a0[0] == 0x8214 and a0[1] == 0x7D22):
			n = 0x04
		elif (a0[0] == 0x8214 and a0[1] == 0x7D36):
			n = 0x04
		elif (a0[0] == 0x8214 and a0[1] == 0x7D63):
			n = 0x02
		elif (a0[0] == 0x8214 and a0[1] == 0x7D77):
			n = 0x02
		elif (a0[0] == 0x8214 and a0[1] == 0x7DBE):
			n = 0x02
		elif (a0[0] == 0x8214 and a0[1] == 0x7DE3):
			n = 0x01
		elif (a0[0] == 0x8214 and a0[1] == 0x7DEB):
			n = 0
		elif (a0[0] == 0x8214 and a0[1] == 0x7DF7):
			n = 0x01
		elif (a0[0] == 0x8214 and a0[1] == 0x7DFF):
			n = 0
		elif (a0[0] == 0x8241 and a0[1] == 0x7040):
			n = 0x09
		elif (a0[0] == 0x8241 and a0[1] == 0x7042):
			n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7140):
			n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7200):
			n = 0x09
		elif (a0[0] == 0x8241 and a0[1] == 0x7202):
			n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7300):
			n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7316):
			n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7440):
			n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7474):
			n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7562):
			n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7576):
			n = 0x03
		elif (a0[0] == 0x8241 and a0[1] == 0x7634):
			n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7722):
			n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7736):
			n = 0x03
		elif (a0[0] == 0x8241 and a0[1] == 0x7C40):
			n = 0x07
		elif (a0[0] == 0x8241 and a0[1] == 0x7D37):
			n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x7D3F):
			n = 0x01
		elif (a0[0] == 0x8241 and a0[1] == 0x7D76):
			n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x7D7E):
			n = 0x01
		elif (a0[0] == 0x8241 and a0[1] == 0x7DBF):
			n = 0
		elif (a0[0] == 0x8241 and a0[1] == 0x7DEA):
			n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x7DFE):
			n = 0
		elif (a0[0] == 0x8241 and a0[1] == 0x7E34):
			n = 0x04
		elif (a0[0] == 0x8241 and a0[1] == 0x7F22):
			n = 0x04
		elif (a0[0] == 0x8241 and a0[1] == 0x7F36):
			n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x7F3E):
			n = 0x01
		elif (a0[0] == 0x8241 and a0[1] == 0x7FBE):
			n = 0
		elif (a0[0] == 0x8400 and a0[1] == 0x7400):
			n = 0x0B
		elif (a0[0] == 0x8412 and a0[1] == 0x7367):
			n = 0x03
		elif (a0[0] == 0x8412 and a0[1] == 0x7B67):
			n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x7000):
			n = 0x09
		elif (a0[0] == 0x8421 and a0[1] == 0x7002):
			n = 0x08
		elif (a0[0] == 0x8421 and a0[1] == 0x7010):
			n = 0x08
		elif (a0[0] == 0x8421 and a0[1] == 0x7116):
			n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x7252):
			n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x7344):
			n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x7356):
			n = 0x03
		elif (a0[0] == 0x8421 and a0[1] == 0x7365):
			n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x73D6):
			n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x73DE):
			n = 0x01
		elif (a0[0] == 0x8421 and a0[1] == 0x7401):
			n = 0x09
		elif (a0[0] == 0x8421 and a0[1] == 0x7403):
			n = 0x08
		elif (a0[0] == 0x8421 and a0[1] == 0x7517):
			n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x7653):
			n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x7757):
			n = 0x03
		elif (a0[0] == 0x8421 and a0[1] == 0x77DF):
			n = 0x01
		elif (a0[0] == 0x8421 and a0[1] == 0x7810):
			n = 0x07
		elif (a0[0] == 0x8421 and a0[1] == 0x7916):
			n = 0x04
		elif (a0[0] == 0x8421 and a0[1] == 0x7B56):
			n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x7BD6):
			n = 0x01
		elif (a0[0] == 0x8421 and a0[1] == 0x7BDE):
			n = 0
		elif (a0[0] == 0x8421 and a0[1] == 0x7F45):
			n = 0x04
		elif (a0[0] == 0x8421 and a0[1] == 0x7F57):
			n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x7FDF):
			n = 0
		elif (a0[0] == 0x8C21 and a0[1] == 0x73DE):
			n = 0
		else:
			assert (False), 'Don\'t know how to read float array for [%s]!' %(IntArr2Str(a0, 4))
		i = self.ReadFloat64A(block, i, n, node, 'CodedFloatA.a1')
		return i

	def Read_CodedFloatB(self, block, offset):
		a0, i    = getUInt16A(block, offset, 2)
		if (a0[0] == 0x8000 and a0[1] == 0x7000):
			n = 0x0C
		elif (a0[0] == 0x8000 and a0[1] == 0x7001):
			n = 0x0B
		elif (a0[0] == 0x8020 and a0[1] == 0x7252):
			n = 0x07
		elif (a0[0] == 0x8020 and a0[1] == 0x725A):
			n = 0x06
		elif (a0[0] == 0x8020 and a0[1] == 0x72D2):
			n = 0x06
		elif (a0[0] == 0x8020 and a0[1] == 0x72DA):
			n = 0x05
		elif (a0[0] == 0x8020 and a0[1] == 0x7A12):
			n = 0x06
		elif (a0[0] == 0x8020 and a0[1] == 0x7A52):
			n = 0x06
		elif (a0[0] == 0x8020 and a0[1] == 0x7ADA):
			n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7256):
			n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x72D6):
			n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7352):
			n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x735A):
			n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x73D2):
			n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x73DA):
			n = 0x03
		elif (a0[0] == 0x8124 and a0[1] == 0x7A16):
			n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7A56):
			n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7ADE):
			n = 0x02
		elif (a0[0] == 0x8124 and a0[1] == 0x7B52):
			n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7BDA):
			n = 0x02
		elif (a0[0] == 0x8400 and a0[1] == 0x7000):
			n = 0x0B
		elif (a0[0] == 0x8400 and a0[1] == 0x7344):
			n = 0x07
		elif (a0[0] == 0x8400 and a0[1] == 0x7B44):
			n = 0x06
		elif (a0[0] == 0x8412 and a0[1] == 0x7002):
			n = 0x09
		elif (a0[0] == 0x8412 and a0[1] == 0x7346):
			n = 0x05
		elif (a0[0] == 0x8412 and a0[1] == 0x7354):
			n = 0x05
		elif (a0[0] == 0x8412 and a0[1] == 0x73DC):
			n = 0x03
		elif (a0[0] == 0x8412 and a0[1] == 0x7B46):
			n = 0x04
		elif (a0[0] == 0x8412 and a0[1] == 0x7B54):
			n = 0x04
		elif (a0[0] == 0x8421 and a0[1] == 0x7356):
			n = 0x03
		elif (a0[0] == 0x8421 and a0[1] == 0x7653):
			n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x7B56):
			n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x7ED3):
			n = 0x03
		elif (a0[0] == 0x8429 and a0[1] == 0x7BDE):
			n = 0
		elif (a0[0] == 0x8480 and a0[1] == 0x7BCC):
			n = 0x04
		elif (a0[0] == 0x8492 and a0[1] == 0x7BCE):
			n = 0x02
		elif (a0[0] == 0x8820 and a0[1] == 0x7ADA):
			n = 0x04
		elif (a0[0] == 0x8924 and a0[1] == 0x7ADE):
			n = 0x02
		else:
			assert (False), 'Don\'t know how to read float array for [%s]!' %(IntArr2Str(a0, 4))
		a1, i = getFloat64A(block, i, n)
		return a0, a1, i

	def Read_Float32Arr(self, block, offset, node, name):
		cnt0, i = getUInt32(block, offset)
		i = self.ReadUInt32A(block, i, 2, node, 'Float32Arr_' + name)

		lst = []
		l2 = []
		j = 0
		while (j < cnt0):
			j += 1
			a1, i = getFloat32A(block, i, 2)
			lst.append(a1)
			vec = FloatArr2Str(a1)
			l2.append('(%s)' %(vec))

		if (len(l2) > 0):
			node.content += ' {%s}' %(','.join(l2))
		node.set(name, lst)

		return i

	def Read_Float64Arr(self, block, offset, node, l, name):
		cnt0, i = getUInt32(block, offset)
		i = self.ReadUInt32A(block, i, 2, node, 'Float64Arr_' + name)

		lst = []
		l2 = []
		j = 0
		while (j < cnt0):
			j += 1
			a1, i = getFloat64A(block, i, l)
			lst.append(a1)
			vec = FloatArr2Str(a1)
			l2.append('(%s)' %(vec))

		if (len(l2) > 0):
			node.content += ' {%s}' %(','.join(l2))
		node.set(name, lst)

		return i

	def Read_022ac1b1(self, node, block):
		i = self.ReadUInt8(block, 0, node, 'u8')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')

		checkReadAll(node, i, len(block))
		return

	def Read_022ac1b5(self, node, block):
		'''
		Part drawing Attribute
		'''
		node.typeName = 'PDrwAttr'
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')

		if (getFileVersion() >= 2015):
			i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		else:
			i = self.ReadUInt16A(block, i, 2, node, 'a1')

		i = self.ReadUInt16A(block, i, 3, node, 'a2')
		i = self.Read_ColorAttr(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 2, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_0244393c(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'keyRef')

		checkReadAll(node, i, len(block))
		return

	def Read_0270ffc7(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_2')

		checkReadAll(node, i, len(block))
		return

	def Read_03e3d90b(self, node, block):
		i = self.Read_HeaderParent(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_2D_UINT32_, 'lst0')
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadFloat64A(block, i, 3, node, 'a2')
		i = self.ReadFloat64A(block, i, 3, node, 'a3')

		checkReadAll(node, i, len(block))
		return

	def Read_0ae12f04(self, node, block):
		i = self.ReadUInt32(block, 0, node, 'u32_0')
		i = self.ReadFloat64A(block, i, 3, node, 'a0')
		i = self.ReadFloat64A(block, i, 3, node, 'a1')
		i = self.ReadLen32Text16(block, i, node)

		checkReadAll(node, i, len(block))
		return

	def Read_0bc8ea6d(self, node, block):
		'''
		ParentKeyRef
		'''
		node.typeName = 'KeyRef'
		i = self.Read_HeaderParent(block, node)
		i = self.ReadUInt32(block, i, node, 'key')

		node.printable = False

		checkReadAll(node, i, len(block))
		return

	def Read_0de8e459(self, node, block):
		i = self.Read_32RA(block, node)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = self.ReadFloat64A(block, i, 3, node, 'a3')
		i = self.ReadUInt32(block, i, node, 'u32_1')

		checkReadAll(node, i, len(block))
		return

	def Read_120284ef(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)

		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')

		checkReadAll(node, i, len(block))
		return

	def Read_12a31e33(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 5, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = self.ReadUInt16A(block, i, 8, node, 'a1')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_13fc8170(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_14533d82(self, node, block):
		'''
		Workplane
		'''
		node.typeName = 'WrkPlane'
		i = self.Read_32RA(block, node)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 6, node, 'a3')
		i = self.ReadFloat64A(block, i, 3, node, 'a4')
		i = self.ReadFloat64A(block, i, 3, node, 'a5')

		# TODO: Hugh - Does this really fit????
		if (node.get('Header0').x == 0x09):
			i = self.ReadUInt32(block, i, node, 'u32_0')
		else:
			node.set('u32_0', 0)
		i = self.Read_CodedFloatA(block, i, node)
		i = self.ReadUInt8A(block, i, 3, node, 'a6')

		checkReadAll(node, i, len(block))
		return

	def Read_189725d1(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadSInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i  = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16(block, i, node, 'u16_0')

		checkReadAll(node, i, len(block))
		return

	def Read_2c7020f6(self, node, block):
		'''
		Workaxis
		'''
		node.typeName = 'WrkAxis'
		i = self.Read_32RA(block, node)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 6, node, 'a0')
		a1, a2, i = self.Read_CodedFloatB(block, i)
		node.set('a1', a1)
		node.set('a2', a2)
		i = self.ReadUInt8A(block, i, 3, node, 'a3')

		checkReadAll(node, i, len(block))
		return

	def Read_2c7020f8(self, node, block):
		'''
		Workpoint
		'''
		node.typeName = 'WrkPoint'
		i = self.Read_32RA(block, node)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 6, node, 'a3')
		i = self.Read_CodedFloatA(block, i, node)
		i = self.ReadUInt16(block, i, node, 'u16_0')

		checkReadAll(node, i, len(block))
		return

	def Read_37db9d1e(self, node, block):
		i = self.Read_HeaderParent(block, node)
		i  = self.ReadList2(block, i, node, SegmentReader._TYP_2D_SINT32_, 'lst0')
		i = self.ReadSInt32(block, i, node, 'u32_0')
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_3d953eb2(self, node, block):
		i = self.Read_HeaderParent(block, node)
		i = self.ReadUInt32A(block, i, 2, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_3da2c291(self, node, block):
		i = self.Read_32RA(block, node)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = skipBlockSize(block, i)
		i = ReadParentRef(block, i, node)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = self.ReadUInt8A(block, i, 4, node, 'a2')

		checkReadAll(node, i, len(block))
		return

	def Read_3ea856ac(self, node, block):
		i = self.Read_HeaderParent(block, node)
		i = self.ReadUInt32A(block, i, 2, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_41305114(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = self.ReadFloat32(block, i, node, 'f32_0')
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadFloat32A(block, i, 5, node, 'a0')
		i = self.ReadUInt16(block, i, node, 'u16_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_2')

		checkReadAll(node, i, len(block))
		return

	def Read_438452f0(self, node, block):
		i = self.ReadUInt16A(block, 0, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = self.Read_ColorAttr(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 5, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = self.ReadUInt16A(block, i, 8, node, 'a1')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_440d2b29(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')

		checkReadAll(node, i, len(block))
		return

	def Read_48eb8607(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')

		node.printable = (len(node.get('lst0')) > 0)

		checkReadAll(node, i, len(block))
		return

	def Read_48eb8608(self, node, block):
		node.typeName = '2dLineColor'
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c0')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c1')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c2')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c3')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c4')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_4ad05620(self, node, block):
		'''
		ParentKeyRef
		'''
		node.typeName = 'KeyRef'
		i = self.Read_HeaderParent(block, node)
		i = self.ReadUInt32(block, i, node, 'key')

		node.printable = False

		checkReadAll(node, i, len(block))
		return

	def Read_4b57dc55(self, node, block):
		node.typeName = '2dCircle'
		i = self.Read_32RRR2(block, node)
		i = self.ReadFloat64A(block, i, 3, node, 'm')
		i = self.ReadFloat64(block, i, node, 'f64_0')
		i = self.ReadFloat64(block, i, node, 'r')
		# start angle
		i = self.ReadAngle(block, i, node, 'alpha')
		# stop angle
		i = self.ReadAngle(block, i, node, 'beta')

		checkReadAll(node, i, len(block))
		return

	def Read_4b57dc56(self, node, block):
		node.typeName = '2dEllipse'

		i = self.Read_32RRR2(block, node)
		i = self.ReadFloat64A(block, i, 2, node, 'c')
		i = self.ReadFloat64(block, i, node, 'b')      # length for point B
		i = self.ReadFloat64(block, i, node, 'a')      # length for point A
		i = self.ReadFloat64A(block, i, 2, node, 'dB') # direction vector-2D for point B
		i = self.ReadFloat64A(block, i, 2, node, 'dA') # direction vector-2D for point A
		# start angle
		i = self.ReadAngle(block, i, node, 'alpha')
		# stop angle
		i = self.ReadAngle(block, i, node, 'beta')

		checkReadAll(node, i, len(block))
		return

	def Read_4e951290(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')

		checkReadAll(node, i, len(block))
		return

	def Read_4e951291(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_50e809cd(self, node, block):
		'''
		2D-Point
			GUID = {50e809cd-11d2-7827-6000-75b72c39cdb0}
		'''
		node.typeName = '2dPoint'
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_3D_FLOAT32_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_2D_UINT16_, 'lst1')

		checkReadAll(node, i, len(block))
		return

	def Read_5194e9a2(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadFloat64A(block, i, 3, node, 'a0')
		i = self.ReadFloat64A(block, i, 3, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_5194e9a3(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadFloat64A(block, i, 3, node, 'a2')
		i = self.ReadFloat64A(block, i, 3, node, 'a3')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32A(block, i, 3, node, 'a4')

		checkReadAll(node, i, len(block))
		return

	def Read_591e9565(self, node, block):
		i = self.Read_HeaderParent(block, node)
		i = self.ReadUInt32A(block, i, 2, node, 'a0')

		return

	def Read_5d916ce9(self, node, block):
		'''
		ParentKeyRef
		'''
		node.typeName = 'KeyRef'
		i = self.Read_HeaderParent(block, node)
		i = self.ReadUInt32(block, i, node, 'key')

		node.printable = False

		checkReadAll(node, i, len(block))
		return

	def Read_5ede1890(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 6, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_60fd1845(self, node, block):
		'''
		2D-Sketch
			GUID = {60fd1845-11d0-d79d-0008-bfbb21eddc09}
			lst1 map with elements
			lst3 map with spezial elements (e.g. Text)
		'''
		node.typeName = '2dSketch'
		i = self.Read_Header0(block, node)
		i = ReadParentRef(block, i, node)
		i = ReadChildRef(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')

		lst0 = node.get('lst0')
		assert (len(lst0) == 0 or len(lst0) == l), '%s: unknown format for list length = %d!' %(node.typeID, len(lst0))

		i = skipBlockSize(block, i)

		if (len(lst0) == 0):
			i = ReadChildRef(block, i, node)
		elif (len(lst0) == 1):
			i = ReadChildRef(block, i, node)
			i = ReadChildRef(block, i, node)

		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.Read_CodedFloatA(block, i, node)
		i = self.ReadList6(block, i, node, 'lst1')
		i = self.ReadList6(block, i, node, 'lst2')
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = self.ReadList6(block, i, node, 'lst3')
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_6266d8cd(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_3D_FLOAT32_, 'lst0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 6, node, 'a2')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadFloat32A(block, i, 3, node, 'a3')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_6a6931dc(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = self.Read_TypedFloat(block, i, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_LIST_3D_FLOAT64_, 'lst0')
		i = self.ReadFloat64A(block, i, 6, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_6c6322eb(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i  = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_6c8a5c53(self, node, block):
		i = self.Read_32RA(block, node)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = skipBlockSize(block, i)
		i = ReadParentRef(block, i, node)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = self.ReadFloat64A(block, i, 6, node, 'a4')
		i = self.ReadUInt8A(block, i, 4, node, 'a5')

		checkReadAll(node, i, len(block))
		return

	def Read_6e176bb6(self, node, block):
		i = self.ReadUInt32(block, 0, node, 'u32_0')
		i = self.ReadFloat64A(block, i, 3, node, 'a0')
		i = self.ReadFloat64A(block, i, 2, node, 'a1')
		i = self.ReadUInt32(block, i, node, 'u32_1')

		checkReadAll(node, i, len(block))
		return

	def Read_7333f86d(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = self.ReadFloat64A(block, i, 2, node, 'a1')
		i = self.ReadUInt32(block, i, node, 'u32_2')

		checkReadAll(node, i, len(block))
		return

	def Read_7ae0e1a3(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32')
		i = skipBlockSize(block, i)
		i = self.ReadFloat64A(block, i, 2, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_7dfc2448(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt32(block, i, node, 'key')

		checkReadAll(node, i, len(block))
		return

	def Read_824d8fd9(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i  = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt32(block, i, node, 'u32_1')

		checkReadAll(node, i, len(block))
		return

	def Read_8da49a23(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 5, node, 'a1')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 4, node, 'a2')

		checkReadAll(node, i, len(block))
		return

	def Read_8f0b160b(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c0')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c1')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c2')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c3')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c4')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 2, node, 'a10')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 10, node, 'a11')

		checkReadAll(node, i, len(block))
		return

	def Read_8f0b160c(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 10, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadUInt16A(block, i, 3, node, 'a1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 4, node, 'a2')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')

		checkReadAll(node, i, len(block))
		return

	def Read_9215a162(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 2, node, 'a2')

		checkReadAll(node, i, len(block))
		return

	def Read_9360cf4d(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadFloat64(block, i, node, 'f64_0')

		if (getFileVersion() > 2013):
			i = self.ReadList6(block, i, node, 'lst1')
		else:
			node.set('lst1', [])

		checkReadAll(node, i, len(block))
		return

	def Read_9516e3a1(self, node, block):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_9795e56a(self, node, block):
		i = self.ReadUInt32(block, 0, node, 'u32')
		i = self.ReadFloat64A(block, i, 3, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_9a676a50(self, node, block):
		'''
		Body
		'''
		node.typeName = 'Body'
		i = self.Read_32RA(block, node)
		i = ReadParentRef(block, i, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = ReadChildRef(block, i, node)
		i = self.ReadUInt16A(block, i, 7, node, 'a1')
		i = ReadCrossRef(block, i, node)
		i = ReadCrossRef(block, i, node)
		i = ReadChildRef(block, i, node)
		i = ReadChildRef(block, i, node)
		i = ReadChildRef(block, i, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_2D_F64_U32_4D_U8_, 'lst0')
		i = skipBlockSize(block, i)
		i = self.ReadFloat64A(block, i, 2, node, 'a2')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadList7(block, i, node, 'lst1')
		i = self.ReadUInt16A(block, i, 4, node, 'a3')

		a4, dummy = getUInt16A(block, i, 2)
		if (a4[0] == 0x02 and a4[1] == 0x3000):
			i = self.ReadList2(block, i, node, SegmentReader._TYP_1D_UINT32_, 'lst0')
			i = self.ReadList2(block, i, node, SegmentReader._TYP_1D_UINT32_, 'lst0')
			i = self.ReadUInt16A(block, i, 2, node, 'a4')
		else:
			node.set('lst2', [])
			node.set('lst3', [])
			i = dummy

		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_a529d1e2(self, node, block):
		i = self.Read_32RA(block, node)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')

		checkReadAll(node, i, len(block))
		return

	def Read_a79eacc7(self, node, block):
		'''
		2D-Line
		'''
		node.typeName = '2dLine'
		i = self.Read_32RRR2(block, node)
		i = self.ReadFloat64A(block, i, 3, node, 'p1')
		i = self.ReadFloat64A(block, i, 3, node, 'p2')

		checkReadAll(node, i, len(block))
		return

	def Read_a79eaccb(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_3D_FLOAT32_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8')

		checkReadAll(node, i, len(block))
		return

	def Read_a79eaccc(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadFloat64A(block, i, 12, node, 'a2')
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_a79eaccf(self, node, block):
		'''
		3D-Object
		'''
		node.typeName = '3dObject'
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		if (node.get('u8_0') == 1):
			i = self.ReadUInt8A(block, i, 4, node, 'a0')
			i = self.ReadFloat64A(block, i, 3, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_a79eacd2(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_3D_FLOAT32_, 'lst0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_2D_UINT16_, 'lst1')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_3D_FLOAT32_, 'lst2')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_2D_FLOAT32_, 'lst3')
		i = self.ReadUInt16A(block, i, 2, node, 'a0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst4')
		i = self.ReadFloat32A(block, i, 2, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_a79eacd3(self, node, block):
		'''
		LinePoint
		'''
		node.typeName = 'LinePoint'
		i = self.Read_32RRR2(block, node)
		i = self.ReadFloat64A(block, i, 3, node, 'vec')
		i = self.ReadFloat32(block, i, node, 'f32_0')
		i = self.ReadSInt32(block, i, node, 's32_0')
		i = self.ReadUInt16(block, i, node, 'u16_0')

		checkReadAll(node, i, len(block))
		return

	def Read_a79eacd5(self, node, block):
		'''
		2D-Text
		'''
		node.typeName = '2dText'
		i = self.Read_32RRR2(block, node)
		i = self.ReadLen32Text16(block, i , node)
		i = self.ReadFloat64A(block, i , 3, node, 'vec')
		i = self.ReadFloat64A(block, i , 3, node, 'a0')
		i = self.ReadUInt16A(block, i, 3, node, 'a1')
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_a94779e0(self, node, block):
		'''
		Extrusion
		'''
		node.typeName = 'Extrusion'
		i = skipBlockSize(block, 0)

		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadFloat64A(block, i, 3, node, 'a1')
		i = self.ReadFloat64A(block, i, 3, node, 'a2')
		i = self.Read_TypedFloat(block, i, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_LIST_3D_FLOAT64_, 'lst0')

		checkReadAll(node, i, len(block))
		return

	def Read_a94779e2(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt32A(block, i, 3, node, 'a1')
		i = self.ReadUInt16A(block, i, 4, node, 'a2')
		i = self.ReadFloat64A(block, i, 3, node, 'a3')
		i = self.ReadFloat64A(block, i, 3, node, 'a4')

		if (node.get('a1')[2] == 1):
			i = self.ReadFloat64A(block, i, 3, node, 'a5_0')
			i = self.ReadFloat64A(block, i, 3, node, 'a5_1')
			i = self.ReadFloat64A(block, i, 3, node, 'a5_2')
			i = self.ReadFloat64A(block, i, 3, node, 'a5_3')

		if (node.get('a2')[2] == 1):
			i = self.ReadFloat64A(block, i, 3, node, 'a6_0')

		i = self.ReadUInt8A(block, i, 2, node, 'a7')
		i = self.Read_TypedFloat(block, i, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_LIST_3D_FLOAT64_, 'lst1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadUInt32(block, i, node, 'cnt3')
		i = self.ReadFloat64A(block, i, 4, node, 'a8')
		i = self.ReadUInt8A(block, i, 6, node, 'a9')
		i = self.ReadUInt32(block, i, node, 'cnt4')
		i = self.ReadFloat64A(block, i, 4, node, 'a10')
		i = self.ReadUInt8A(block, i, 5, node, 'a11')
		cnt1, i = getUInt32(block, i)
		j = 0
		lst2 = []
		while (j < cnt1):
			j += 1
			a0, a1, i = self.Read_CodedFloatB(block, i)
			lst2.append(a1)
		node.set('lst2', lst2)
		checkReadAll(node, i, len(block))
		return

	def Read_a94779e3(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt32A(block, i, 5, node, 'a1')
		i = self.ReadFloat64A(block, i, 3, node, 'a2')
		i = self.ReadFloat64A(block, i, 3, node, 'a3')
		i = self.ReadUInt8A(block, i, 2, node, 'a4')
		i = self.Read_TypedFloat(block, i, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_LIST_3D_FLOAT64_, 'lst1')
		i = skipBlockSize(block, i)
		i = self.ReadFloat64A(block, i, 7, node, 'a6')
		if (getFileVersion() > 2016):
			i = self.ReadUInt16A(block, i, 13, node, 'a7')
		else:
			i = self.ReadUInt8A(block, i, 1, node, 'a7')

		checkReadAll(node, i, len(block))
		return

	def Read_a94779e4(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt32A(block, i, 2, node, 'a1')
		i = self.ReadUInt32(block, i, node, 'u32_0')

		if (node.get('u32_0') != 0):
			i = self.ReadFloat64A(block, i, 12, node, 'a2')
		else:
			node.set('a2', [])
			node.content += ' ()'

		i = self.ReadUInt32(block, i, node, 'u32_1')
		if (node.get('u32_1') != 0):
			i = self.ReadFloat64A(block, i, 12, node, 'a3')
		else:
			node.set('a3', [])
			node.content += ' ()'

		i = self.ReadUInt32(block, i, node, 'u32_2')
		i = self.ReadFloat64A(block, i, 6, node, 'a4')
		i = self.ReadUInt16A(block, i, 3, node, 'a5')
		i   = self.ReadList2(block, i, node, SegmentReader._TYP_GUESS_, 'lst1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32A(block, i, 7, node, 'a6')
		i = self.ReadFloat64A(block, i, 3, node, 'a7')
		i = self.ReadFloat64A(block, i, 3, node, 'a8')

		checkReadAll(node, i, len(block))
		return

	def Read_a98235c4(self, node, block):
		i = self.Read_32RA(block, node)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 2, node, 'a2')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8A(block, i, 4, node, 'a3')
		i = self.ReadUInt32(block, i, node, 'u32_0')

		if (getFileVersion() < 2012):
			i = self.ReadUInt16A(block, i, 5, node, 'a4')
		else:
			i = self.ReadUInt16A(block, i, 7, node, 'a4')

		if (node.get('u32_0') == 1):
			i = self.ReadUInt16A(block, i, 3, node, 'a5')
			i = self.ReadFloat64(block, i, node, 'f64_0')
		else:
			node.set('a5', [])
			node.set('f64_0', 0.0)
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_af48560f(self, node, block):
		'''
		ColorStyle primary Attribute
		'''
		node.typeName = 'PrmColorAttr'
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 7, node, 'a0')
		i = self.Read_ColorAttr(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadUInt16A(block, i, 2, node, 'a1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_b01025bf(self, node, block):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_b069bc6a(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadUInt16A(block, i, 8, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_b1057be1(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 13, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_b1057be2(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 13, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_b1057be3(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 13, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_b255d907(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadFloat64A(block, i, 3, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_b32bf6a2(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt16(block, i, node, 'u16_0')
		i = self.Read_ColorAttr(block, i, node)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_b32bf6a3(self, node, block):
		node.typeName = 'Visibility'
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_b32bf6a5(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16(block, i, node, 'u16_0')

		checkReadAll(node, i, len(block))
		return

	def Read_b32bf6a6(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_b32bf6a7(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadFloat64(block, i, node, 'f64_0')
		i = self.ReadFloat64A(block, i, 3, node, 'vec')
		i = self.ReadFloat64(block, i, node, 'f64_1')
		i = self.ReadUInt32(block, i, node, 'u32_1')

		checkReadAll(node, i, len(block))
		return

	def Read_b32bf6a8(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')

		checkReadAll(node, i, len(block))
		return

	def Read_b32bf6a9(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16(block, i, node, 'u16_0')

		checkReadAll(node, i, len(block))
		return

	def Read_b32bf6ab(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')

		checkReadAll(node, i, len(block))
		return

	def Read_b32bf6ac(self, node, block):
		node.typeName = 'LineStyle'
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16(block, i, node, 'u16_0')
		i = self.ReadFloat32(block, i, node, 'width')
		i = self.ReadUInt16A(block, i, 2, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadUInt16(block, i, node, 'u16_1')
		cnt, i = getUInt16(block, i)
		j = 0
		a1 = []
		while (j < cnt):
			j += 1
			u32_0, i = getUInt32(block, i)
			f32_0, i = getFloat32(block, i)
			x = B32BF6AC(u32_0, f32_0)
			a1.append(x)
		node.set('a1', a1)
		i = self.ReadFloat32A(block, i, 3, node, 'a2')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 4, node, 'a3')

		checkReadAll(node, i, len(block))
		return

	def Read_b32bf6ae(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadFloat64A(block, i , 3, node, 'a0')
		i = self.ReadFloat64A(block, i , 3, node, 'a1')
		i = self.ReadFloat64A(block, i , 3, node, 'a2')

		checkReadAll(node, i, len(block))
		return

	def Read_b3895bc2(self, node, block):
		i = self.ReadUInt32A(block, 0, 2, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.Read_ColorAttr(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 5, node, 'a1')
		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = self.ReadUInt16A(block, i, 8, node, 'a2')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_b9274ce3(self, node, block):
		i = self.Read_HeaderParent(block, node)
		i = self.ReadUInt32(block, i, node, 'key')

		node.printable = False

		checkReadAll(node, i, len(block))
		return

	def Read_bbc99377(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt16A(block, i, 2, node, 'a0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 4, node, 'a1')
		i = self.ReadUInt8A(block, i, 5, node, 'a2')
		i = self.ReadFloat64A(block, i, 3, node, 'a3')
		i = self.ReadFloat64A(block, i, 3, node, 'a4')
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8A(block, i, 3, node, 'a5')
		if (node.get('u32_0') == 0):
			i = self.ReadFloat64A(block, i, 3, node, 'a6')
			node.get('a6').insert(0, 0.0)
		else:
			i = self.ReadFloat64A(block, i, 4, node, 'a6')

		i = self.ReadUInt8(block, i, node, 'u8_0')
		u8_0 = node.get('u8_0')
		if (u8_0 == 0x74):
			i = self.ReadFloat64A(block, i, 0x0B, node, 'a7')
		elif (u8_0 == 0x72):
			i = self.ReadFloat64A(block, i, 0x10, node, 'a7')
		elif (u8_0 == 0x7D):
			i = self.ReadFloat64A(block, i, 0x07, node, 'a7')

		i = self.ReadUInt8(block, i, node, 'u8_1')
		i = self.ReadUInt16A(block, i , 2, node, 'a8')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst1')
		i = self.ReadUInt8(block, i, node, 'u8_2')

		checkReadAll(node, i, len(block))
		return

	def Read_bcc1e889(self, node, block):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_bd5bb62b(self, node, block):
		i = self.Read_HeaderParent(block, node)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadUInt8(block, i, node, 'u8_0')

		node.printable = False

		checkReadAll(node, i, len(block))
		return

	def Read_c0014c89(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadFloat64A(block, i, 2, node, 'a1')
		i = self.ReadUInt8A(block, i, 4, node, 'a2')
		a3, a4, i = self.Read_CodedFloatB(block, i)
		node.set('a3', a3)
		node.set('a4', a4)
		i = skipBlockSize(block, i)
		i = self.ReadUInt16A(block, i, 7, node, 'a5')

		checkReadAll(node, i, len(block))
		return

	def Read_c29d5c11(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadFloat64A(block, i, 3, node, 'a0')

		checkReadAll(node, i, len(block))
		return

	def Read_c2f1f8ed(self, node, block):
		'''
		dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_c46b45c9(self, node, block):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_c9da5109(self, node, block):
		i = skipBlockSize(block, 0)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_GUESS_, 'lst0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_2')

		checkReadAll(node, i, len(block))
		return

	def Read_ca7163a3(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16A(block, i, 2, node, 'a0')
		i = ReadChildRef(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadList6(block, i, node, 'lst1')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c0')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c1')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c2')
		i = skipBlockSize(block, i)
		i = self.ReadColorRGBA(block, i, node, 'c3')
		i = skipBlockSize(block, i)
		i = self.ReadFloat32(block, i, node, 'f32_0')
		i = skipBlockSize(block, i)

		checkReadAll(node, i, len(block))
		return

	def Read_d1071d57(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		a3,    i = getUInt16A(block, i, 2)
		# like Read_CodedFloatA
		if (a3[0] == 0x8000 and a3[1] == 0x7000):
			n = 0x0C
		elif (a3[0] == 0x8000 and a3[1] == 0x7090):
			n = 0x0A
		elif (a3[0] == 0x8000 and a3[1] == 0x76DB):
			n = 0x04
		elif (a3[0] == 0x8100 and a3[1] == 0x7799):
			n = 0x05
		elif (a3[0] == 0x8214 and a3[1] == 0x7577):
			n = 0x03
		elif (a3[0] == 0x8214 and a3[1] == 0x79FD):
			n = 0x02
		elif (a3[0] == 0x8421 and a3[1] == 0x7F57):
			n = 0x02
		else:
			i += self.ReadUnknown(node, block[i:], None, True, False)
			assert (False), 'Don\'t know how to read float array for [%s]!' %(IntArr2Str(a3, 4))
		i = self.ReadFloat64A(block, i, n, node, 'a4')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_d3a55701(self, node, block):
		'''
		2D-Spline
		'''
		node.typeName = '2dSpline'
		i = self.Read_32RRR2(block, node)
		i = self.ReadUInt32A(block, i, 3, node, 'a0')
		i = self.ReadUInt8A(block, i, 8, node, 'a1')
		i = self.Read_Float32Arr(block, i, node, 'lst0')
		i = self.Read_Float32Arr(block, i, node, 'lst1')
		i = self.Read_Float64Arr(block, i, node, 2, 'lst2')
		i = self.ReadUInt8A(block, i, 8, node, 'a2')
		i = self.ReadUInt32A(block, i, 2, node, 'a3')
		i = self.ReadFloat64A(block, i, 2, node, 'a4')
		i = self.Read_Float64Arr(block, i, node, 2, 'lst3')

		checkReadAll(node, i, len(block))
		return

	def Read_d3a55702(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadUInt32A(block, i, 3, node, 'a0')
		i = self.ReadUInt8A(block, i, 8, node, 'a1')
		i = self.Read_Float32Arr(block, i, node, 'lst0')
		i = self.Read_Float32Arr(block, i, node, 'lst1')
		i = self.Read_Float64Arr(block, i, node, 3, 'lst2')
		i = self.ReadUInt8A(block, i, 8, node, 'a2')
		i = self.ReadUInt32A(block, i, 2, node, 'a3')
		i = self.ReadFloat64A(block, i, 2, node, 'a4')

		checkReadAll(node, i, len(block))
		return

	def Read_d79ad3f3(self, node, block):
		'''
		Mesh???
		'''
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_3D_FLOAT32_, 'lst0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_2D_UINT16_, 'lst1')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_3D_FLOAT32_, 'lst2')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_2D_FLOAT32_, 'lst3')
		i = self.ReadUInt16A(block, i, 2, node, 'a0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst4')
		i = self.ReadFloat32A(block, i, 2, node, 'a1')
		i = skipBlockSize(block, i)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_2D_UINT16_, 'lst5')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_2D_UINT16_, 'lst6')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_2D_UINT16_, 'lst7')

		checkReadAll(node, i, len(block))
		return

	def Read_da58aa0e(self, node, block):
		'''
		3D-Sketch
		'''
		node.typeName = '3dSketch'
		i = self.Read_Header0(block, node)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = ReadChildRef(block, i, node)
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadList3(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = skipBlockSize(block, i)
		i = ReadChildRef(block, i, node)
		i = skipBlockSize(block, i)
		i = self.ReadUInt8(block, i, node, 'u8_2')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_1')
		i = self.ReadList6(block, i, node, 'lst1')
		i = self.ReadUInt8(block, i, node, 'u8_3')
		i = self.ReadList6(block, i, node, 'lst2')
		i = self.ReadUInt8(block, i, node, 'u8_4')

		checkReadAll(node, i, len(block))
		return

	def Read_dbe41d91(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadFloat64A(block, i, 3, node, 'a1')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32A(block, i, 14, node, 'a2')

		checkReadAll(node, i, len(block))
		return

	def Read_def9ad02(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_3D_FLOAT32_, 'lst0')
		i = self.ReadUInt32(block, i, node, 'u32_1')

		if (getFileVersion() > 2013):
			i = self.ReadList6(block, i, node, 'lst1')
		else:
			node.set('lst1', [])

		checkReadAll(node, i, len(block))
		return

	def Read_def9ad03(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt32(block, i, node, 'u32_1')

		if (getFileVersion() > 2013):
			i = self.ReadList6(block, i, node, 'lst1')
		else:
			node.set('lst1', [])

		checkReadAll(node, i, len(block))
		return

	def Read_e1eb685c(self, node, block):
		i = self.Read_32RRR2(block, node)
		i = self.ReadUInt32A(block, i, 9, node, 'a0')
		i = self.ReadList2(block, i, node, SegmentReader._TYP_GUESS_, 'lst0')
		i = self.ReadUInt32A(block, i, 2, node, 'a1')

		checkReadAll(node, i, len(block))
		return

	def Read_ef1e3be5(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_FONT_, 'lst0')

		checkReadAll(node, i, len(block))
		return

	def Read_f6adcc68(self, node, block):
		i = self.Read_HeaderParent(block, node)
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_f6adcc69(self, node, block):
		i = self.Read_HeaderParent(block, node)
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_fb96d24a(self, node, block):
		i = self.Read_Header0(block, node)
		i = self.ReadUInt16A(block, i, 4, node, 'a0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = self.ReadFloat64A(block, i, 3, node, 'f64_0')
		i = self.ReadUInt32(block, i, node, 'u32_0')

		checkReadAll(node, i, len(block))
		return

	def Read_ff084971(self, node, block):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def Read_ffb5643c(self, node, block):
		'''
		Dimensioning
		'''
		node.typeName = 'Dimensioning'
		i = self.Read_32RRR2(block, node)
		i = self.ReadList2(block, i, node, SegmentReader._TYP_NODE_REF_, 'lst0')
		i = self.ReadUInt8(block, i, node, 'u8_0')
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'u32_0')
		i = skipBlockSize(block, i)
		i = skipBlockSize(block, i)
		i = self.ReadUInt32(block, i, node, 'key')
		i = self.ReadUInt8(block, i, node, 'u8_1')

		checkReadAll(node, i, len(block))
		return

	def HandleBlock(self, file, block, node, seg):
		ntid = node.typeID.time_low
		if (ntid == 0x022ac1b1):
			self.Read_022ac1b1(node, block)
		elif (ntid == 0x022ac1b5):
			self.Read_022ac1b5(node, block)
		elif (ntid == 0x0244393c):
			self.Read_0244393c(node, block)
		elif (ntid == 0x0270ffc7):
			self.Read_0270ffc7(node, block)
		elif (ntid == 0x03e3d90b):
			self.Read_03e3d90b(node, block)
		elif (ntid == 0x0ae12f04):
			self.Read_0ae12f04(node, block)
		elif (ntid == 0x0bc8ea6d):
			self.Read_0bc8ea6d(node, block)
		elif (ntid == 0x0de8e459):
			self.Read_0de8e459(node, block)
		elif (ntid == 0x120284ef):
			self.Read_120284ef(node, block)
		elif (ntid == 0x12a31e33):
			self.Read_12a31e33(node, block)
		elif (ntid == 0x13fc8170):
			self.Read_13fc8170(node, block)
		elif (ntid == 0x14533d82):
			self.Read_14533d82(node, block)
		elif (ntid == 0x189725d1):
			self.Read_189725d1(node, block)
		elif (ntid == 0x2c7020f6):
			self.Read_2c7020f6(node, block)
		elif (ntid == 0x2c7020f8):
			self.Read_2c7020f8(node, block)
		elif (ntid == 0x37db9d1e):
			self.Read_37db9d1e(node, block)
		elif (ntid == 0x3d953eb2):
			self.Read_3d953eb2(node, block)
		elif (ntid == 0x3da2c291):
			self.Read_3da2c291(node, block)
		elif (ntid == 0x3ea856ac):
			self.Read_3ea856ac(node, block)
		elif (ntid == 0x41305114):
			self.Read_41305114(node, block)
		elif (ntid == 0x438452f0):
			self.Read_438452f0(node, block)
		elif (ntid == 0x440d2b29):
			self.Read_440d2b29(node, block)
		elif (ntid == 0x48eb8607):
			self.Read_48eb8607(node, block)
		elif (ntid == 0x48eb8608):
			self.Read_48eb8608(node, block)
		elif (ntid == 0x4ad05620):
			self.Read_4ad05620(node, block)
		elif (ntid == 0x4b57dc55):
			self.Read_4b57dc55(node, block)
		elif (ntid == 0x4b57dc56):
			self.Read_4b57dc56(node, block)
		elif (ntid == 0x4e951290):
			self.Read_4e951290(node, block)
		elif (ntid == 0x4e951291):
			self.Read_4e951291(node, block)
		elif (ntid == 0x50e809cd):
			self.Read_50e809cd(node, block)
		elif (ntid == 0x5194e9a2):
			self.Read_5194e9a2(node, block)
		elif (ntid == 0x5194e9a3):
			self.Read_5194e9a3(node, block)
		elif (ntid == 0x591e9565):
			self.Read_591e9565(node, block)
		elif (ntid == 0x5d916ce9):
			self.Read_5d916ce9(node, block)
		elif (ntid == 0x5ede1890):
			self.Read_5ede1890(node, block)
		elif (ntid == 0x60fd1845):
			self.Read_60fd1845(node, block)
		elif (ntid == 0x6266d8cd):
			self.Read_6266d8cd(node, block)
		elif (ntid == 0x6a6931dc):
			self.Read_6a6931dc(node, block)
		elif (ntid == 0x6c6322eb):
			self.Read_6c6322eb(node, block)
		elif (ntid == 0x6c8a5c53):
			self.Read_6c8a5c53(node, block)
		elif (ntid == 0x6e176bb6):
			self.Read_6e176bb6(node, block)
		elif (ntid == 0x7333f86d):
			self.Read_7333f86d(node, block)
		elif (ntid == 0x7ae0e1a3):
			self.Read_7ae0e1a3(node, block)
		elif (ntid == 0x7dfc2448):
			self.Read_7dfc2448(node, block)
		elif (ntid == 0x824d8fd9):
			self.Read_824d8fd9(node, block)
		elif (ntid == 0x8da49a23):
			self.Read_8da49a23(node, block)
		elif (ntid == 0x8f0b160b):
			self.Read_8f0b160b(node, block)
		elif (ntid == 0x8f0b160c):
			self.Read_8f0b160c(node, block)
		elif (ntid == 0x9215a162):
			self.Read_9215a162(node, block)
		elif (ntid == 0x9360cf4d):
			self.Read_9360cf4d(node, block)
		elif (ntid == 0x9516e3a1):
			self.Read_9516e3a1(node, block)
		elif (ntid == 0x9795e56a):
			self.Read_9795e56a(node, block)
		elif (ntid == 0x9a676a50):
			self.Read_9a676a50(node, block)
		elif (ntid == 0xa529d1e2):
			self.Read_a529d1e2(node, block)
		elif (ntid == 0xa79eacc7):
			self.Read_a79eacc7(node, block)
		elif (ntid == 0xa79eaccb):
			self.Read_a79eaccb(node, block)
		elif (ntid == 0xa79eaccc):
			self.Read_a79eaccc(node, block)
		elif (ntid == 0xa79eaccf):
			self.Read_a79eaccf(node, block)
		elif (ntid == 0xa79eacd2):
			self.Read_a79eacd2(node, block)
		elif (ntid == 0xa79eacd3):
			self.Read_a79eacd3(node, block)
		elif (ntid == 0xa79eacd5):
			self.Read_a79eacd5(node, block)
		elif (ntid == 0xa94779e0):
			self.Read_a94779e0(node, block)
		elif (ntid == 0xa94779e2):
			self.Read_a94779e2(node, block)
		elif (ntid == 0xa94779e3):
			self.Read_a94779e3(node, block)
		elif (ntid == 0xa94779e4):
			self.Read_a94779e4(node, block)
		elif (ntid == 0xa98235c4):
			self.Read_a98235c4(node, block)
		elif (ntid == 0xaf48560f):
			self.Read_af48560f(node, block)
		elif (ntid == 0xb01025bf):
			self.Read_b01025bf(node, block)
		elif (ntid == 0xb069bc6a):
			self.Read_b069bc6a(node, block)
		elif (ntid == 0xb1057be1):
			self.Read_b1057be1(node, block)
		elif (ntid == 0xb1057be2):
			self.Read_b1057be2(node, block)
		elif (ntid == 0xb1057be3):
			self.Read_b1057be3(node, block)
		elif (ntid == 0xb255d907):
			self.Read_b255d907(node, block)
		elif (ntid == 0xb32bf6a2):
			self.Read_b32bf6a2(node, block)
		elif (ntid == 0xb32bf6a3):
			self.Read_b32bf6a3(node, block)
		elif (ntid == 0xb32bf6a5):
			self.Read_b32bf6a5(node, block)
		elif (ntid == 0xb32bf6a6):
			self.Read_b32bf6a6(node, block)
		elif (ntid == 0xb32bf6a7):
			self.Read_b32bf6a7(node, block)
		elif (ntid == 0xb32bf6a8):
			self.Read_b32bf6a8(node, block)
		elif (ntid == 0xb32bf6a9):
			self.Read_b32bf6a9(node, block)
		elif (ntid == 0xb32bf6ab):
			self.Read_b32bf6ab(node, block)
		elif (ntid == 0xb32bf6ac):
			self.Read_b32bf6ac(node, block)
		elif (ntid == 0xb32bf6ae):
			self.Read_b32bf6ae(node, block)
		elif (ntid == 0xb3895bc2):
			self.Read_b3895bc2(node, block)
		elif (ntid == 0xb9274ce3):
			self.Read_b9274ce3(node, block)
		elif (ntid == 0xbbc99377):
			self.Read_bbc99377(node, block)
		elif (ntid == 0xbcc1e889):
			self.Read_bcc1e889(node, block)
		elif (ntid == 0xbd5bb62b):
			self.Read_bd5bb62b(node, block)
		elif (ntid == 0xc0014c89):
			self.Read_c0014c89(node, block)
		elif (ntid == 0xc29d5c11):
			self.Read_c29d5c11(node, block)
		elif (ntid == 0xc2f1f8ed):
			self.Read_c2f1f8ed(node, block)
		elif (ntid == 0xc46b45c9):
			self.Read_c46b45c9(node, block)
		elif (ntid == 0xc9da5109):
			self.Read_c9da5109(node, block)
		elif (ntid == 0xca7163a3):
			self.Read_ca7163a3(node, block)
		elif (ntid == 0xd1071d57):
			self.Read_d1071d57(node, block)
		elif (ntid == 0xd3a55701):
			self.Read_d3a55701(node, block)
		elif (ntid == 0xd3a55702):
			self.Read_d3a55702(node, block)
		elif (ntid == 0xd79ad3f3):
			self.Read_d79ad3f3(node, block)
		elif (ntid == 0xda58aa0e):
			self.Read_da58aa0e(node, block)
		elif (ntid == 0xdbe41d91):
			self.Read_dbe41d91(node, block)
		elif (ntid == 0xdef9ad02):
			self.Read_def9ad02(node, block)
		elif (ntid == 0xdef9ad03):
			self.Read_def9ad03(node, block)
		elif (ntid == 0xe1eb685c):
			self.Read_e1eb685c(node, block)
		elif (ntid == 0xef1e3be5):
			self.Read_ef1e3be5(node, block)
		elif (ntid == 0xf6adcc68):
			self.Read_f6adcc68(node, block)
		elif (ntid == 0xf6adcc69):
			self.Read_f6adcc69(node, block)
		elif (ntid == 0xfb96d24a):
			self.Read_fb96d24a(node, block)
		elif (ntid == 0xff084971):
			self.Read_ff084971(node, block)
		elif (ntid == 0xffb5643c):
			self.Read_ffb5643c(node, block)
		else:
			self.ReadUnknownBlock(file, node, block, True)

		return
