#!/usr/bin/env python

'''
importerDC.py:
Importer for the Document's components
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''
from importerSegment import SegmentReader, getNodeType
from importerSegNode import AbstractNode, DCNode
from importerUtils   import *

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.2'
__status__      = 'In-Development'

class DCReader(SegmentReader):
	def __init__(self):
		super(DCReader, self).__init__(False)

	def createNewNode(self):
		return DCNode()

	def skipDumpRawData(self):
		return True

	def ReadContentHeader(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'label')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'index')

		flags = node.get('flags')
		node.visible             = (flags & 0x00000400) > 0
		node.dimensioningVisible = (flags & 0x00800000) > 0
		node.set('ContentHeader', True)

		return i

	def ReadConstraintHeader2D(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
			node.content += ' lst0={} lst1={}'
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def ReadConstraintHeader3D(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_1')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst2')
		else:
			i = self.skipBlockSize(i)
			node.content += ' lst1={} lst2={}'
		return i

	def ReadCodedFloat(self, node, offset):
		a0, i = getUInt16A(node.data, offset, 2)
		node.set('CodedFloat.a0', a0)
		if (a0[0] == 0x8000 and a0[1] == 0x7000):   n = 0x0C
		elif (a0[0] == 0x8000 and a0[1] == 0x7010): n = 0x0B
		elif (a0[0] == 0x8000 and a0[1] == 0x7090): n = 0x0A
		elif (a0[0] == 0x8000 and a0[1] == 0x7100): n = 0x0B
		elif (a0[0] == 0x8000 and a0[1] == 0x7180): n = 0x0A
		elif (a0[0] == 0x8000 and a0[1] == 0x76DB): n = 0x04
		elif (a0[0] == 0x8000 and a0[1] == 0x7B44): n = 0x07
		elif (a0[0] == 0x8000 and a0[1] == 0x7BCC): n = 0x05
		elif (a0[0] == 0x8001 and a0[1] == 0x7002): n = 0x0A
		elif (a0[0] == 0x8001 and a0[1] == 0x7004): n = 0x0A
		elif (a0[0] == 0x8001 and a0[1] == 0x7011): n = 0x0A
		elif (a0[0] == 0x8001 and a0[1] == 0x7100): n = 0x0A
		elif (a0[0] == 0x8001 and a0[1] == 0x7101): n = 0x0A
		elif (a0[0] == 0x8001 and a0[1] == 0x7116): n = 0x07
		elif (a0[0] == 0x8001 and a0[1] == 0x7117): n = 0x07
		elif (a0[0] == 0x8001 and a0[1] == 0x711E): n = 0x06
		elif (a0[0] == 0x8001 and a0[1] == 0x711F): n = 0x06
		elif (a0[0] == 0x8001 and a0[1] == 0x7181): n = 0x09
		elif (a0[0] == 0x8001 and a0[1] == 0x7196): n = 0x06
		elif (a0[0] == 0x8004 and a0[1] == 0x7006): n = 0x0A
		elif (a0[0] == 0x8010 and a0[1] == 0x7100): n = 0x0A
		elif (a0[0] == 0x8010 and a0[1] == 0x7110): n = 0x0A
		elif (a0[0] == 0x8010 and a0[1] == 0x7161): n = 0x07
		elif (a0[0] == 0x8010 and a0[1] == 0x7171): n = 0x07
		elif (a0[0] == 0x8010 and a0[1] == 0x71E1): n = 0x06
		elif (a0[0] == 0x8010 and a0[1] == 0x71F1): n = 0x06
		elif (a0[0] == 0x8010 and a0[1] == 0x7910): n = 0x09
		elif (a0[0] == 0x8010 and a0[1] == 0x7961): n = 0x06
		elif (a0[0] == 0x8010 and a0[1] == 0x7971): n = 0x06
		elif (a0[0] == 0x8020 and a0[1] == 0x7010): n = 0x0A
		elif (a0[0] == 0x8020 and a0[1] == 0x7200): n = 0x0A
		elif (a0[0] == 0x8100 and a0[1] == 0x7000): n = 0x0B
		elif (a0[0] == 0x8100 and a0[1] == 0x7190): n = 0x09
		elif (a0[0] == 0x8100 and a0[1] == 0x7611): n = 0x07
		elif (a0[0] == 0x8100 and a0[1] == 0x7711): n = 0x07
		elif (a0[0] == 0x8100 and a0[1] == 0x7799): n = 0x05
		elif (a0[0] == 0x8100 and a0[1] == 0x7C08): n = 0x08
		elif (a0[0] == 0x8100 and a0[1] == 0x7E99): n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7004): n = 0x09
		elif (a0[0] == 0x8124 and a0[1] == 0x7014): n = 0x08
		elif (a0[0] == 0x8124 and a0[1] == 0x7100): n = 0x09
		elif (a0[0] == 0x8124 and a0[1] == 0x7110): n = 0x08
		elif (a0[0] == 0x8124 and a0[1] == 0x7140): n = 0x08
		elif (a0[0] == 0x8124 and a0[1] == 0x7204): n = 0x08
		elif (a0[0] == 0x8124 and a0[1] == 0x7256): n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x7352): n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x7543): n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x7615): n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x7657): n = 0x03
		elif (a0[0] == 0x8124 and a0[1] == 0x7711): n = 0x05
		elif (a0[0] == 0x8124 and a0[1] == 0x7753): n = 0x03
		elif (a0[0] == 0x8124 and a0[1] == 0x7E15): n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7E57): n = 0x02
		elif (a0[0] == 0x8124 and a0[1] == 0x7ED7): n = 0x01
		elif (a0[0] == 0x8124 and a0[1] == 0x7EDF): n = 0x00
		elif (a0[0] == 0x8124 and a0[1] == 0x7F11): n = 0x04
		elif (a0[0] == 0x8124 and a0[1] == 0x7F53): n = 0x02
		elif (a0[0] == 0x8124 and a0[1] == 0x7FD3): n = 0x01
		elif (a0[0] == 0x8124 and a0[1] == 0x7FDB): n = 0x00
		elif (a0[0] == 0x8142 and a0[1] == 0x7001): n = 0x08
		elif (a0[0] == 0x8142 and a0[1] == 0x7327): n = 0x05
		elif (a0[0] == 0x8142 and a0[1] == 0x7635): n = 0x03
		elif (a0[0] == 0x8142 and a0[1] == 0x7737): n = 0x03
		elif (a0[0] == 0x8142 and a0[1] == 0x7D7C): n = 0x03
		elif (a0[0] == 0x8142 and a0[1] == 0x7EBD): n = 0x00
		elif (a0[0] == 0x8200 and a0[1] == 0x7100): n = 0x0A
		elif (a0[0] == 0x8200 and a0[1] == 0x7188): n = 0x08
		elif (a0[0] == 0x8200 and a0[1] == 0x7200): n = 0x0B
		elif (a0[0] == 0x8200 and a0[1] == 0x7280): n = 0x0A
		elif (a0[0] == 0x8200 and a0[1] == 0x7300): n = 0x0A
		elif (a0[0] == 0x8200 and a0[1] == 0x7522): n = 0x07
		elif (a0[0] == 0x8200 and a0[1] == 0x75A2): n = 0x06
		elif (a0[0] == 0x8200 and a0[1] == 0x7600): n = 0x0A
		elif (a0[0] == 0x8200 and a0[1] == 0x7D22): n = 0x06
		elif (a0[0] == 0x8200 and a0[1] == 0x7D2A): n = 0x05
		elif (a0[0] == 0x8214 and a0[1] == 0x7100): n = 0x08
		elif (a0[0] == 0x8214 and a0[1] == 0x7114): n = 0x08
		elif (a0[0] == 0x8214 and a0[1] == 0x7161): n = 0x05
		elif (a0[0] == 0x8214 and a0[1] == 0x7175): n = 0x05
		elif (a0[0] == 0x8214 and a0[1] == 0x71E1): n = 0x04
		elif (a0[0] == 0x8214 and a0[1] == 0x7522): n = 0x05
		elif (a0[0] == 0x8214 and a0[1] == 0x7536): n = 0x05
		elif (a0[0] == 0x8214 and a0[1] == 0x7563): n = 0x03
		elif (a0[0] == 0x8214 and a0[1] == 0x756B): n = 0x02
		elif (a0[0] == 0x8214 and a0[1] == 0x7577): n = 0x03
		elif (a0[0] == 0x8214 and a0[1] == 0x75E3): n = 0x02
		elif (a0[0] == 0x8214 and a0[1] == 0x75F7): n = 0x02
		elif (a0[0] == 0x8214 and a0[1] == 0x79E1): n = 0x03
		elif (a0[0] == 0x8214 and a0[1] == 0x79FD): n = 0x02
		elif (a0[0] == 0x8214 and a0[1] == 0x7D22): n = 0x04
		elif (a0[0] == 0x8214 and a0[1] == 0x7D36): n = 0x04
		elif (a0[0] == 0x8214 and a0[1] == 0x7D63): n = 0x02
		elif (a0[0] == 0x8214 and a0[1] == 0x7D77): n = 0x02
		elif (a0[0] == 0x8214 and a0[1] == 0x7DA2): n = 0x03
		elif (a0[0] == 0x8214 and a0[1] == 0x7DBE): n = 0x02
		elif (a0[0] == 0x8214 and a0[1] == 0x7DE3): n = 0x01
		elif (a0[0] == 0x8214 and a0[1] == 0x7DEB): n = 0x00
		elif (a0[0] == 0x8214 and a0[1] == 0x7DF7): n = 0x01
		elif (a0[0] == 0x8214 and a0[1] == 0x7DFF): n = 0x00
		elif (a0[0] == 0x821C and a0[1] == 0x7577): n = 0x02
		elif (a0[0] == 0x821C and a0[1] == 0x7DEB): n = 0x00
		elif (a0[0] == 0x8241 and a0[1] == 0x7040): n = 0x09
		elif (a0[0] == 0x8241 and a0[1] == 0x7042): n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7101): n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7117): n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x711F): n = 0x04
		elif (a0[0] == 0x8241 and a0[1] == 0x7140): n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7156): n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x715E): n = 0x04
		elif (a0[0] == 0x8241 and a0[1] == 0x71D6): n = 0x04
		elif (a0[0] == 0x8241 and a0[1] == 0x7200): n = 0x09
		elif (a0[0] == 0x8241 and a0[1] == 0x7202): n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7300): n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7316): n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7440): n = 0x08
		elif (a0[0] == 0x8241 and a0[1] == 0x7474): n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7523): n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7537): n = 0x03
		elif (a0[0] == 0x8241 and a0[1] == 0x753F): n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x7562): n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7576): n = 0x03
		elif (a0[0] == 0x8241 and a0[1] == 0x757E): n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x75A3): n = 0x04
		elif (a0[0] == 0x8241 and a0[1] == 0x75B7): n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x75F6): n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x7634): n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7722): n = 0x05
		elif (a0[0] == 0x8241 and a0[1] == 0x7736): n = 0x03
		elif (a0[0] == 0x8241 and a0[1] == 0x7C40): n = 0x07
		elif (a0[0] == 0x8241 and a0[1] == 0x7D23): n = 0x04
		elif (a0[0] == 0x8241 and a0[1] == 0x7D37): n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x7D3F): n = 0x01
		elif (a0[0] == 0x8241 and a0[1] == 0x7D62): n = 0x04
		elif (a0[0] == 0x8241 and a0[1] == 0x7D76): n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x7D7E): n = 0x01
		elif (a0[0] == 0x8241 and a0[1] == 0x7DB7): n = 0x01
		elif (a0[0] == 0x8241 and a0[1] == 0x7DBF): n = 0x00
		elif (a0[0] == 0x8241 and a0[1] == 0x7DEA): n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x7DF6): n = 0x01
		elif (a0[0] == 0x8241 and a0[1] == 0x7DFE): n = 0x00
		elif (a0[0] == 0x8241 and a0[1] == 0x7E34): n = 0x04
		elif (a0[0] == 0x8241 and a0[1] == 0x7F22): n = 0x04
		elif (a0[0] == 0x8241 and a0[1] == 0x7F36): n = 0x02
		elif (a0[0] == 0x8241 and a0[1] == 0x7F3E): n = 0x01
		elif (a0[0] == 0x8241 and a0[1] == 0x7FBE): n = 0x00
		elif (a0[0] == 0x8249 and a0[1] == 0x75BF): n = 0x01
		elif (a0[0] == 0x8249 and a0[1] == 0x7DFE): n = 0x00
		elif (a0[0] == 0x82C1 and a0[1] == 0x7DBF): n = 0x00
		elif (a0[0] == 0x8400 and a0[1] == 0x7400): n = 0x0B
		elif (a0[0] == 0x8412 and a0[1] == 0x7171): n = 0x05
		elif (a0[0] == 0x8412 and a0[1] == 0x7765): n = 0x03
		elif (a0[0] == 0x8412 and a0[1] == 0x7D61): n = 0x04
		elif (a0[0] == 0x8421 and a0[1] == 0x7000): n = 0x09
		elif (a0[0] == 0x8421 and a0[1] == 0x7002): n = 0x08
		elif (a0[0] == 0x8421 and a0[1] == 0x7010): n = 0x08
		elif (a0[0] == 0x8421 and a0[1] == 0x7023): n = 0x08
		elif (a0[0] == 0x8421 and a0[1] == 0x7104): n = 0x07
		elif (a0[0] == 0x8421 and a0[1] == 0x7116): n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x711E): n = 0x04
		elif (a0[0] == 0x8421 and a0[1] == 0x7252): n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x72D2): n = 0x04
		elif (a0[0] == 0x8421 and a0[1] == 0x7344): n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x7356): n = 0x03
		elif (a0[0] == 0x8421 and a0[1] == 0x735E): n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x7365): n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x73D6): n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x73DE): n = 0x01
		elif (a0[0] == 0x8421 and a0[1] == 0x7401): n = 0x09
		elif (a0[0] == 0x8421 and a0[1] == 0x7403): n = 0x08
		elif (a0[0] == 0x8421 and a0[1] == 0x7411): n = 0x08
		elif (a0[0] == 0x8421 and a0[1] == 0x7517): n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x751F): n = 0x04
		elif (a0[0] == 0x8421 and a0[1] == 0x7653): n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x76D3): n = 0x04
		elif (a0[0] == 0x8421 and a0[1] == 0x7745): n = 0x05
		elif (a0[0] == 0x8421 and a0[1] == 0x7757): n = 0x03
		elif (a0[0] == 0x8421 and a0[1] == 0x775F): n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x77D7): n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x77DF): n = 0x01
		elif (a0[0] == 0x8421 and a0[1] == 0x7810): n = 0x07
		elif (a0[0] == 0x8421 and a0[1] == 0x7B56): n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x7B5E): n = 0x01
		elif (a0[0] == 0x8421 and a0[1] == 0x7B65): n = 0x04
		elif (a0[0] == 0x8421 and a0[1] == 0x7BD6): n = 0x01
		elif (a0[0] == 0x8421 and a0[1] == 0x7BDE): n = 0x00
		elif (a0[0] == 0x8421 and a0[1] == 0x7F45): n = 0x04
		elif (a0[0] == 0x8421 and a0[1] == 0x7F57): n = 0x02
		elif (a0[0] == 0x8421 and a0[1] == 0x7FDE): n = 0x00
		elif (a0[0] == 0x8421 and a0[1] == 0x7FDF): n = 0x00
		elif (a0[0] == 0x84A1 and a0[1] == 0x73D6): n = 0x02
		elif (a0[0] == 0x8A14 and a0[1] == 0x75F7): n = 0x01
		elif (a0[0] == 0x8A14 and a0[1] == 0x7900): n = 0x07
		elif (a0[0] == 0x8A1C and a0[1] == 0x7577): n = 0x01
		elif (a0[0] == 0x8A1C and a0[1] == 0x75FF): n = 0x00
		elif (a0[0] == 0x8A41 and a0[1] == 0x75B7): n = 0x01
		elif (a0[0] == 0x8A49 and a0[1] == 0x75BF): n = 0x00
		elif (a0[0] == 0x8C21 and a0[1] == 0x73DE): n = 0x00
		elif (a0[0] == 0x8C21 and a0[1] == 0x7B56): n = 0x02
		else:
			assert (False), 'Don\'t know how to read float array for [%s]!' %(IntArr2Str(a0, 4))
		a1, i = getFloat64A(node.data, i, n)
		node.content += ' CodedFloat={a0=[%s] a1=[%s]}' %(IntArr2Str(a0, 4), FloatArr2Str(a1))
		node.set('CodedFloat.a1', a1)
		return i

	def Read_009A1CC4(self, node):
		i = node.Read_Header0()
		return i

	def Read_00ACC000(self, node):
		node.typeName = 'Dimension_Horizonzal_Distance2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			node.content += ' lst0={} lst1={}'
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refDimension')
		return i

	def Read_00E41C0E(self, node):
		i = node.Read_Header0()
		return i

	def Read_01E0570C(self, node):
		i = node.Read_Header0()
		return i

	def Read_01E7910C(self, node):
		i = node.Read_Header0()
		return i

	def Read_0229768D(self, node):
		i = node.Read_Header0()
		return i

	def Read_025C7CD8(self, node):
		i = node.Read_Header0()
		return i

	def Read_029DAD70(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_033E027B(self, node):
		i = node.Read_Header0()
		return i

	def Read_03AA812C(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_03D6552D(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)

		node.printable = False

		return i

	def Read_040D7FB2(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_04D026D2(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_053C4810(self, node):
		i = node.Read_Header0()
		return i

	def Read_05520360(self, node):
		i = node.Read_Header0()
		return i

	def Read_05C619B6(self, node):
		i = node.Read_Header0()
		return i

	def Read_0645C2A5(self, node):
		i = node.Read_Header0()
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		return i

	def Read_06977131(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_06DCEFA9(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_077D9583(self, node):
		i = node.Read_Header0()
		return i

	def Read_07910C0A(self, node):
		i = node.Read_Header0()
		return i

	def Read_07910C0B(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_07AB2269(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'refRDxBody')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUUID(i, 'uid')
		return i

	def Read_0811C56E(self, node):
		i = node.Read_Header0()
		return i

	def Read_0830C1B0(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_09429287(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_09429289(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_0942928A(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_1')
		i = node.ReadCrossRef(i, 'xrf_2')
		i = node.ReadCrossRef(i, 'xrf_3')
		return i

	def Read_0B85010C(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_0A576361(self, node):
		i = node.Read_Header0()
		return i

	def Read_0B86AD43(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		return i

	def Read_0BDC96E0(self, node):
		i = node.Read_Header0()
		return i

	def Read_0C12CBF2(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_0C48B860(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_0C48B861(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_0D28D8C0(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		return i

	def Read_0D0F9548(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_0DDD7C10(self, node):
		node.typeName = 'Constraint_SymmetryLine2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadCrossRef(i, 'refLineSym')
		return i

	def Read_0E64A759(self, node):
		i = node.Read_Header0()
		return i

	def Read_0E6870AE(self, node):
		node.typeName = 'SolidBody'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_0F177BB0(self, node):
		node.typeName = 'Constraint_Fix2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refPoint')
		return i

	def Read_10587822(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'xrf_1')
		i = self.skipBlockSize(i)
		return i

	def Read_10B6ADEF(self, node):
		i = node.Read_Header0()
		return i

	def Read_11058558(self, node):
		node.typeName = 'Dimension_Distance2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
			node.content += ' lst0={} lst1={}'
		i = node.ReadCrossRef(i, 'refDimension')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')
		i = node.ReadUInt32A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 4, 'a1')
		i = node.ReadUInt32A(i, 4, 'a1')
		return i

	def Read_117806EE(self, node):
		i = node.Read_Header0()
		return i

	def Read_151280F0(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_15A5FF92(self, node):
		i = node.Read_Header0()
		return i

	def Read_167018B8(self, node):
		i = node.Read_Header0()
		return i

	def Read_16DE1A75(self, node):
		i = node.Read_Header0()
		return i

	def Read_17B3E814(self, node):
		i = node.Read_Header0()
		return i

	def Read_18951917(self, node):
		node.typeName = 'RevolutionOrientation'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_1A26FF54(self, node):
		i = node.Read_Header0()
		return i

	def Read_1B48E9DA(self, node):
		node.typeName = 'FxFillet'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_1E3A132C(self, node):
		i = node.Read_Header0()
		return i

	def Read_1F6D59F6(self, node):
		i = node.Read_Header0()
		return i

	def Read_1FBB3C01(self, node):
		node.typeName = 'String'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'x1')
		i = node.ReadFloat64(i, 'y1')
		i = node.ReadFloat64(i, 'z1')
		i = node.ReadUInt16A(i, 18, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2015):
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadFloat64(i, 'f64_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadUInt32A(i, 4, 'a2')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadFloat64(i, 'x2')
		i = node.ReadFloat64(i, 'y2')
		i = node.ReadFloat64(i, 'z2')
		i = node.ReadFloat64(i, 'x3')
		i = node.ReadFloat64(i, 'y3')
		i = node.ReadFloat64(i, 'z3')
		i = node.ReadUInt16A(i, 3, 'a3')
		i = node.ReadUInt8(i, 'u8_1')
		i = node.ReadParentRef(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst2')
		i = node.ReadLen32Text16(i, 'txt_0')
		i = self.skipBlockSize(i)
		return i

	def Read_20673244(self, node):
		node.typeName = 'RectangularPattern'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst1')
		return i

	def Read_21E870BF(self, node):
		node.typeName = 'Constraint_SymmetryPoint2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refObject')
		i = node.ReadCrossRef(i, 'refPoint')
		if (getFileVersion() > 2015):
			i += 4
		return i

	def Read_223360AD(self, node):
		i = node.Read_Header0()
		return i

	def Read_22947391(self, node):
		node.typeName = 'FxBoundaryPatch'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_23BA0568(self, node):
		i = node.Read_Header0()
		return i

	def Read_24BCB2F1(self, node):
		node.typeName = 'FxThread' # Gewinde
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_2510347F(self, node):
		node.typeName = 'Text2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'refText')
		return i

	def Read_2574C505(self, node):
		node.typeName = 'Radius3D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst1')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst2')
		else:
			node.content += ' lst0={} lst1={}'
		return i

	def Read_26F369B7(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'cld_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = node.ReadFloat64A(i, 2, 'a2')
		i = self.skipBlockSize(i)
		#i = node.ReadFloat64A(i, 8, 'a2')
		return i

	def Read_27E9A56F(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_28BE2D59(self, node):
		i = node.Read_Header0()
		return i

	def Read_28BE2D5B(self, node):
		i = node.Read_Header0()
		return i

	def Read_2AF9B62B(self, node):
		i = node.Read_Header0()
		return i

	def Read_2B241309(self, node):
		node.typeName = 'BrowserFolder'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		return i

	def Read_2B60D993(self, node):
		i = node.Read_Header0()
		return i

	def Read_2B48A42B(self, node):
		node.typeName = 'Label'
		i = node.Read_Header0()

		if (node.get('hdr').m == 0x12):
			i = 0
			node.delete('hdr')
			node.content = ""
			i = node.ReadLen32Text8(i)
			i = node.ReadUInt32A(i, 2, 'a0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_TEXT8_X_REF_, 'lst1')
			# 0F 01
			i = node.ReadUInt16(i, 'u16_0')
			# 00 00 00 00 00 00 33 C7
			i = node.ReadFloat64(i, 'x')
			# 30 05 00 80
			i = node.ReadCrossRef(i, 'ref_1')
			# 00 62 00 00
			i = node.ReadUInt32(i, 'flags')
			# 03 00 00 80
			i = node.ReadParentRef(i)
			# D7 0A 00 00
			i = node.ReadUInt32(i, 'index')
			# 16 00 00 00
			i = node.ReadUInt32(i, 'u32_0')
			# 00 00 00 00
			i = node.ReadUInt32(i, 'u32_1')
			# 02 00 00 30 14 00 00 00 1C 00 00 00 00 00 00 00
			#	63 03 00 80,5D 03 00 80,61 03 00 80,64 03 00 80
			#	60 03 00 80,70 04 00 80,00 00 00 00,65 03 00 80
			#	00 00 00 00,66 03 00 80,67 03 00 80,5D 03 00 80
			#	68 03 00 80,00 00 00 00,00 00 00 00,00 00 00 00
			#	71 04 00 80,34 04 00 80,00 00 00 00,00 00 00 00
			i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
			# 00 00 00 00
			i = node.ReadUInt32(i, 'u32_2')
		else:
			i = node.ReadCrossRef(i, 'ref_1')
			i = node.ReadUInt32(i, 'flags')
			i = self.skipBlockSize(i)
			i = node.ReadParentRef(i)
			i = node.ReadCrossRef(i, 'refRoot')
			i = node.ReadChildRef(i, 'ref_2')
			i = self.skipBlockSize(i)
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
			i = node.ReadLen32Text16(i)
			i = node.ReadUUID(i, 'uid')
		return i

	def Read_2CE86835(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_2D06CAD3(self, node):
		i = node.Read_Header0()
		return i

	def Read_2E04A208(self, node):
		i = node.Read_Header0()
		return i

	def Read_2D86FC26(self, node):
		node.typeName = 'ReferenceEdgeLoopId'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_X_REF_, 'lst0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_X_REF_, 'lst1')
		return i

	def Read_312F9E50(self, node):
		node.typeName = 'FxLoft'
		i = self.ReadContentHeader(node)
		return i

	def Read_317B7346(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'points')
		if(getFileVersion() > 2012):
			i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadSInt32(i, 's')
		else:
			node.content += ' lst0={}'
			i = self.skipBlockSize(i)
			i = node.ReadUInt32(i, 'u32_0')
			i = node.ReadUInt8(i, 's')
		i = node.ReadChildRef(i, 'ref_1')
		return i

	def Read_31C98504(self, node):
		i = node.Read_Header0()
		return i

	def Read_31D7A200(self, node):
		i = node.Read_Header0()
		return i

	def Read_33EC1003(self, node):
		node.typeName = 'Constraint_Parallel3D'
		i = self.ReadConstraintHeader3D(node)
		return i

	def Read_346F5947(self, node):
		i = node.Read_Header0()
		return i

	def Read_357D669C(self, node):
		i = node.Read_Header0()
		return i

	def Read_3683FF40(self, node):
		node.typeName = 'Dimension_Vertical_Distance2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			node.content += ' lst0={} lst1={}'
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refDimension')
		return i

	def Read_3689CC91(self, node):
		i = node.Read_Header0()
		return i

	def Read_375C6982(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_1D_UINT32_, 'lst0')
		if (len(node.get('lst0')) > 0):
			i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_37889260(self, node):
		i = node.Read_Header0()
		return i

	def Read_381AF8C4(self, node):
		i = node.Read_Header0()
		return i

	def Read_39A41830(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_39AD9666(self, node):
		i = node.Read_Header0()
		return i

	def Read_3A98DCE3(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = node.ReadCrossRef(i, 'xrf_1')
		i = node.ReadCrossRef(i, 'xrf_2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_4')
		return i

	def Read_3AE9D8DA(self, node):
		node.typeName = 'Sketch3D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_1')
		i = node.ReadList8(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat32A(i, 2, 'a0')
		if (getFileVersion() > 2014):
			i = node.ReadFloat64A(i, 6, 'a1')
		return i

	def Read_3B13313C(self, node):
		i = node.Read_Header0()
		return i

	def Read_3C6C1C6C(self, node):
		i = node.Read_Header0()
		return i

	def Read_3C7F67AA(self, node):
		node.typeName = 'Body'
		i = self.ReadContentHeader(node)
		return i

	def Read_3D64CCF0(self, node):
		node.typeName = 'Sketch2DPlacementPlane'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refOrientation')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 7, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPlane')
		return i

	def Read_3D8924FD(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_3E710428(self, node):
		i = node.Read_Header0()
		return i

	def Read_3E863C3E(self, node):
		i = node.Read_Header0()
		return i

	def Read_402A8F9F(self, node):
		i = node.Read_Header0()
		return i

	def Read_405AB2C6(self, node):
		i = node.Read_Header0()
		return i

	def Read_4116DA9E(self, node):
		i = node.Read_Header0()
		return i

	def Read_43CAB9D6(self, node):
		i = node.Read_Header0()
		return i

	def Read_43CD7C11(self, node):
		node.typeName = 'FxDrill'
		i = self.ReadContentHeader(node)
		return i

	def Read_442C7DD0(self, node):
		node.typeName = 'Coincident_Circle2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
			node.content += ' lst0={} lst1={}'
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refCircle1')
		i = node.ReadCrossRef(i, 'refCircle2')

		return i

	def Read_4507D460(self, node):
		node.typeName = 'Ellipse2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst1')
		else:
			node.content += ' lst1={}'
		i = node.ReadCrossRef(i, 'refCenter')
		i = node.ReadFloat64A(i, 2, 'dA')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadFloat64(i, 'b')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_452121B6(self, node):
		node.typeName = 'ModelerTxnMgr'
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'ref_2')
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2011):
			i += 4
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_MDL_TXN_MGR_)
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_454C24A9(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		return i

	def Read_4580CAF0(self, node):
		i = node.Read_Header0()
		return i

	def Read_464ECA8A(self, node):
		i = node.Read_Header0()
		return i

	def Read_46D500AA(self, node):
		i = node.Read_Header0()
		return i

	def Read_475E7861(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFeature')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'cld_1')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'cld_2')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadCrossRef(i, 'xrf_0')
		return i

	def Read_488C5309(self, node):
		i = node.Read_Header0()
		return i

	def Read_48C52258(self, node):
		node.typeName = 'Spline3D_Bezier'
		i = node.Read_Header0()
		return i

	def Read_48C5F41A(self, node):
		i = node.Read_Header0()
		return i

	def Read_48CF47FA(self, node):
		i = node.Read_Header0()
		return i

	def Read_48CF71CA(self, node):
		i = node.Read_Header0()
		return i

	def Read_4949374A(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_4AC78A71(self, node):
		i = node.Read_Header0()
		return i

	def Read_4B3150E8(self, node):
		i = node.Read_Header0()
		return i

	def Read_4ACA204D(self, node):
		i = node.Read_Header0()
		return i

	def Read_4E4B14BC(self, node):
		i = node.Read_Header0()
		return i

	def Read_4E8F7EE5(self, node):
		i = node.Read_Header0()
		return i

	def Read_4FB10CB8(self, node):
		i = node.Read_Header0()
		return i

	def Read_4FD0DC2A(self, node):
		i = node.Read_Header0()
		return i

	def Read_502678E7(self, node):
		i = node.Read_Header0()
		return i

	def Read_509FB5CC(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_1D_UINT32_, 'lst0')
		if (len(node.get('lst0')) > 0):
			i = node.ReadSInt32(i, 's32_0')
		return i

	def Read_52534838(self, node):
		node.typeName = 'Constraint_PolygonCenter2D'
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_528A064A(self, node):
		i = node.Read_Header0()
		return i

	def Read_52D04C41(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refRoot')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_2')
		i = self.skipBlockSize(i)
		#08,00,00,30,01,00,00,00,00,00,00,00,23,00,00,80
		i = node.ReadList8(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_534DD87E(self, node):
		i = node.Read_Header0()
		return i

	def Read_54829655(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_4')
		return i

	def Read_55180D7F(self, node):
		i = node.Read_Header0()
		return i

	def Read_553DA303(self, node):
		i = node.Read_Header0()
		return i

	def Read_56970DFA(self, node):
		i = node.Read_Header0()
		return i

	def Read_56A95F20(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		return i

	def Read_578432A6(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		return i

	def Read_5838B763(self, node):
		i = node.Read_Header0()
		return i

	def Read_590D0A10(self, node):
		node.typeName = 'Dimension_Angle'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_X_REF_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_X_REF_, 'lst1')
		else:
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
			node.content += ' lst0={} lst1={}'
		i = node.ReadCrossRef(i, 'refDimension')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_598AACFE(self, node):
		i = node.Read_Header0()
		return i

	def Read_5A6B6124(self, node):
		i = node.Read_Header0()
		return i

	def Read_5A9A7BE0(self, node):
		node.typeName = 'Constraint_Colinear2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		return i

	def Read_5B708411(self, node):
		i = node.Read_Header0()
		return i

	def Read_5B8EC461(self, node):
		i = node.Read_Header0()
		return i

	def Read_5C30CDF0(self, node):
		node.typeName = 'DimensionTypeAngle'
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_5C30CDF6(self, node):
		node.typeName = 'DimensionUnitRAD'
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'factors')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		node.set('UNIT', True)
		return i

	def Read_5D807360(self, node):
		i = node.Read_Header0()
		return i

	def Read_5D8C859D(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			node.content += ' lst0={} lst1={}'
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_5DD3A2D3(self, node):
		i = node.Read_Header0()
		return i

	def Read_5E464B13(self, node):
		i = node.Read_Header0()
		return i

	def Read_5F9D0022(self, node):
		node.typeName = 'DimensionTypeRef'
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat32A(i, 3, 'a0')
		i = self.skipBlockSize(i)
		return i

	def Read_5F9D0023(self, node):
		node.typeName = 'DimensionTypeFactor3D'
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat32A(i, 3, 'a0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_60406697(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = node.ReadCrossRef(i, 'xrf_1')
		i = node.ReadCrossRef(i, 'xrf_2')
		return i

	def Read_614A01F1(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadUInt32A(i, 5, 'a1')
		i = node.ReadLen32Text8(i, 'txt_0')
		return i

	def Read_617931B4(self, node):
		i = node.Read_Header0()
		return i

	def Read_618C9E00(self, node):
		i = node.Read_Header0()
		return i

	def Read_61B56690(self, node):
		i = node.Read_Header0()
		return i

	def Read_624120BC(self, node):
		node.typeName = 'DimensionTypeLength'
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'vec2d_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_6250D222(self, node):
		i = node.Read_Header0()
		return i

	def Read_63266191(self, node):
		node.typeName = 'Constraint_Perpendicular3D'
		i = self.ReadConstraintHeader3D(node)
		return i

	def Read_637B1CC1(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_63D9BDC4(self, node):
		i = node.Read_Header0()
		return i

	def Read_64DA5250(self, node):
		i = node.Read_Header0()
		return i

	def Read_64DE16F3(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = node.ReadCrossRef(i, 'xrf_1')
		i = node.ReadCrossRef(i, 'xrf_2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_6566C3E1(self, node):
		i = node.Read_Header0()
		return i

	def Read_65897E4A(self, node):
		i = node.Read_Header0()
		return i

	def Read_671BB700(self, node):
		node.typeName = 'Dimension_Radius2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
			node.content += ' lst0={} lst1={}'
		i = node.ReadCrossRef(i, 'refDimension')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'refCircle')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadUInt32(i, 'u32_3')
		return i

	def Read_6CA92D02(self, node):
		i = node.Read_Header0()
		return i

	def Read_6FB0D4A7(self, node):
		i = node.Read_Header0()
		return i

	def Read_6FD9928E(self, node):
		i = node.Read_Header0()
		return i

	def Read_729ABE28(self, node):
		node.typeName = 'FxExtrusion'
		# extrusoins like pad, pocket, revolution, groove
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_7312DB35(self, node):
		i = node.Read_Header0()
		return i

	def Read_7325290E(self, node):
		i = node.Read_Header0()
		return i

	def Read_7325290F(self, node):
		i = node.Read_Header0()
		return i

	def Read_73F35CD0(self, node):
		i = node.Read_Header0()
		return i

	def Read_7457BB19(self, node):
		node.typeName = 'Constraint_Tangential3D'
		i = self.ReadConstraintHeader3D(node)
		return i

	def Read_748FBD64(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'xrf_0')
		i = self.skipBlockSize(i)
		return i

	def Read_74DF96E0(self, node):
		node.typeName = 'Dimension_Diameter2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
			node.content += ' lst0={} lst1={}'
		i = node.ReadCrossRef(i, 'refDimension')
		i = node.ReadCrossRef(i, 'xrf_2')
		i = node.ReadCrossRef(i, 'refCircle')
		return i

	def Read_74E6F48A(self, node):
		i = node.Read_Header0()
		return i

	def Read_75F64419(self, node):
		i = node.Read_Header0()
		return i

	def Read_774572D4(self, node):
		i = node.Read_Header0()
		return i

	def Read_78F28827(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_76EC185B(self, node):
		i = node.Read_Header0()
		return i

	def Read_797737B1(self, node):
		i = node.Read_Header0()
		i = node.ReadList2(i, AbstractNode._TYP_3D_FLOAT64_, 'lst0')
		try:
			i = self.ReadCodedFloat(node, i)
		except AssertionError as e:
			a1, i = getUInt8A(node.data, i + 4, len(node.data) - i - 4 - 5)
			a0 = node.get('CodedFloat.a0')
			logError("elif (a0[0] == 0x%X and a0[1] == 0x%X): n = 0x%02X"  %(a0[0], a0[1], len(a1) / 8))
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refDimension')
		return i

	def Read_79D4DD11(self, node):
		i = node.Read_Header0()
		return i

	def Read_7A98AD0E(self, node):
		node.typeName = 'Frame2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		#if (getFileVersion() > 2012):
		#	i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
		#	i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		#else:
		#	node.content += ' lst0={} lst1={}'
		#i = node.ReadUInt32(i, 'u32_0')
		#i = node.ReadUInt32(i, 'u32_0')
		#i = node.ReadCrossRef(i, 'refLine')
		#i = node.ReadCrossRef(i, 'refLineLeft')
		#i = node.ReadCrossRef(i, 'refLineTop')
		#i = node.ReadCrossRef(i, 'refLineRight')
		#i = node.ReadCrossRef(i, 'refLineLeft')
		#i = node.ReadCrossRef(i, 'refPointBL') # bottom left 2D-Point
		#i = node.ReadCrossRef(i, 'refPointTL') # top left 2D-Point
		#i = node.ReadCrossRef(i, 'refPointTR') # top right 2D-Point
		#i = node.ReadCrossRef(i, 'refPointBR') # bottom right 2D-Point
		#i = node.ReadUInt8(i, 'u8_0')
		#i = node.ReadFloat64(i, 'x')
		return i

	def Read_7C321197(self, node):
		i = node.Read_Header0()
		return i

	def Read_7C39DC59(self, node):
		i = node.Read_Header0()
		return i

	def Read_7C44ABDE(self, node):
		node.typeName = 'Bezier3D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		return i

	def Read_7C6D149E(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			node.content += ' lst0={} lst1={}'
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refSpline')
		i = node.ReadCrossRef(i, 'refPoint')
		return i

	def Read_7DA7F733(self, node):
		i = node.Read_Header0()
		return i

	def Read_7DAA0032(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_7DF60748(self, node):
		i = node.Read_Header0()
		return i

	def Read_7F4A3E30(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'a0')
		i = node.ReadUInt16A(i, 3, 'a2')
		i = self.skipBlockSize(i)
		return i

	def Read_7F7F05AC(self, node):
		i = node.Read_Header0()
		return i

	def Read_81E94AB7(self, node):
		i = node.Read_Header0()
		return i

	def Read_828E73A6(self, node):
		i = node.Read_Header0()
		return i

	def Read_845212C7(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_86173E3F(self, node):
		i = node.Read_Header0()
		return i

	def Read_871D6F71(self, node):
		i = node.Read_Header0()
		return i

	def Read_896A9790(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		return i

	def Read_8B1E9A97(self, node):
		i = node.Read_Header0()
		return i

	def Read_8B2BE62E(self, node):
		i = node.Read_Header0()
		return i

	def Read_8B3E95F7(self, node):
		i = node.Read_Header0()
		return i

	def Read_8BE7021F(self, node):
		i = node.Read_Header0()
		return i

	def Read_8C702CD5(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_8D6EF0BE(self, node):
		i = node.Read_Header0()
		return i

	def Read_8DFFE0CD(self, node):
		i = node.Read_Header0()
		return i

	def Read_8EE901B9(self, node):
		i = node.Read_Header0()
		return i

	def Read_8EF06C89(self, node):
		node.typeName = 'Line3D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		if (len(node.data) - i == 6*8 + 1 + 4):
			i += 4
		i = node.ReadFloat64(i, 'x1')
		i = node.ReadFloat64(i, 'y1')
		i = node.ReadFloat64(i, 'z1')
		i = node.ReadFloat64(i, 'x2')
		i = node.ReadFloat64(i, 'y2')
		i = node.ReadFloat64(i, 'z2')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_8EB19F04(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_8F41FD24(self, node):
		node.typeName = 'Stop'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_8F55A3C0(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_X_REF_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_KEY_X_REF_, 'lst1')
		else:
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
			node.content += ' lst0={} lst1={}'
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')

		return i

	def Read_90874D56(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_903F453F(self, node):
		node.typeName = 'ExtrusionSurface'
		i = self.ReadContentHeader(node)
		i = node.ReadChildRef(i, 'cld_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		return i

	def Read_90874D11(self, node):
		node.typeName = 'Sketch2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 'numElements')
		i = node.ReadList8(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refOrientation')
		i = node.ReadCrossRef(i, 'refDirection')
		return i

	def Read_90874D13(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 9, 'a1')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		return i

	def Read_90874D15(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt32A(i, 3, 'a1')

		node.printable = False

		return i

	def Read_90874D16(self, node):
		node.typeName = 'Part'
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUUID(i, 'uid_0')
		i = node.ReadLen32Text16(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt16A(i, 6, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refElements')
		i = node.ReadChildRef(i, 'ref_2')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16A(i, 4, 'a1')
		i = node.ReadChildRef(i, 'cld_1')
		i = node.ReadChildRef(i, 'cld_2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadChildRef(i, 'cld_3')
		i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadChildRef(i, 'cld_4')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_2')
		i = node.ReadLen32Text16(i, 'refSegName')
		i = node.ReadFloat64(i, 'f64_0')
		return i

	def Read_90874D18(self, node):
		node.typeName = 'Orientation'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		try:
			i = self.ReadCodedFloat(node, i)
			a0 = node.get('CodedFloat.a0')
			orientation = a0[1] < 16 | a0[1]
			node.set('orientation', orientation)
		except AssertionError as e:
			a1, i = getUInt8A(node.data, i + 4, len(node.data) - i - 4)
			a0 = node.get('CodedFloat.a0')
			logError("elif (a0[0] == 0x%X and a0[1] == 0x%X): n = 0x%02X"  %(a0[0], a0[1], len(a1) / 8))
		return i

	def Read_90874D23(self, node):
		node.typeName = 'Sketch2DPlacement'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refOrientation1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refDirection')
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'refOrientation2')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = self.skipBlockSize(i)

		return i

	def Read_90874D26(self, node):
		node.typeName = 'Dimension'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i += 4
		i = node.ReadChildRef(i, 'refType')
		i = node.ReadChildRef(i, 'refValue')
		i = node.ReadFloat64A(i, 2, 'values')
		i = node.ReadSInt16A(i, 2, 'a3')
		return i

	def Read_90874D28(self, node):
		node.typeName = 'ValueByte'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2012):
			i += 8
		i = node.ReadUInt8(i, 'value')
		return i

	def Read_90874D40(self, node):
		i = node.Read_Header0()
		return i

	def Read_90874D47(self, node):
		node.typeName = 'RDxBody'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		return i

	def Read_90874D51(self, node):
		node.typeName = 'FxChampher'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_90874D53(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)

		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, AbstractNode._TYP_1D_UINT32_, 'lst0')
		i = node.ReadList8(i, AbstractNode._TYP_1D_UINT32_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_90874D55(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		return i

	def Read_90874D62(self, node):
		node.typeName = 'Group2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_1')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		i = node.ReadUInt32(i, 'u32_0')
		node.printable = False
		return i

	def Read_90874D63(self, node):
		i = node.Read_Header0()
		if ((getFileVersion() > 2014) and (node.get('hdr').m != 0)):
			node.delete('hdr')
			node.content = ""
			i = node.ReadLen32Text8(0)
			i = node.ReadUInt16A(i, 7, 'a0')
			i = node.ReadLen32Text8(i, 'txt_0')
		else:
			i = node.ReadChildRef(i, 'cld_0')
			i = node.ReadUInt16A(i, 2, 'a0')
			i = self.skipBlockSize(i)
			i = node.ReadParentRef(i)
			i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_TEXT16_X_REF_, 'dimensions')

		return i

	def Read_90874D74(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadCrossRef(i, 'xrf_0')
		#i = node.ReadUInt16(i, 'u16_0')
		#i = self.skipBlockSize(i)
		return i

	def Read_90874D91(self, node):
		node.typeName = 'Feature'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'properties')
		i = self.skipBlockSize(i)
		return i

	def Read_90874D94(self, node):
		node.typeName = 'Constraint_Coincident2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refObject')
		i = node.ReadCrossRef(i, 'refPoint')

		return i

	def Read_90874D95(self, node):
		node.typeName = 'Constraint_Parallel2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_90874D96(self, node):
		node.typeName = 'Constraint_Perpendicular2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_90874D97(self, node):
		node.typeName = 'Constraint_Tangential2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		if (getFileVersion() > 2014):
			i += 4
		return i

	def Read_90874D98(self, node):
		node.typeName = 'Constraint_Horizontal2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refLine')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_90874D99(self, node):
		node.typeName = 'Constraint_Vertical2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refLine')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_90F4820A(self, node):
		i = node.Read_Header0()
		return i

	def Read_91637937(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'root')
		i = node.ReadCrossRef(i, 'xrf_0')
		i = node.ReadCrossRef(i, 'xrf_1')
		i = self.skipBlockSize(i)
		return i

	def Read_92637D29(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt16(i, 's16_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		return i

	def Read_936522B1(self, node):
		i = node.Read_Header0()
		return i

	def Read_938BED94(self, node):
		i = node.Read_Header0()
		return i

	def Read_93C7EE68(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'xrf_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_9574000C(self, node):
		i = node.Read_Header0()
		return i

	def Read_99684A5A(self, node):
		i = node.Read_Header0()
		return i

	def Read_99B938AE(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'a1')
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2014):
			dummy, i = getUInt32(node.data, i)
#		node.printable = False
		return i

	def Read_99B938B0(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_9A94E347(self, node):
		i = node.Read_Header0()
		return i

	def Read_9BB4281C(self, node):
		i = node.Read_Header0()
		return i

	def Read_9C8C1297(self, node):
		i = node.Read_Header0()
		return i

	def Read_9E43716A(self, node):
		node.typeName = 'Circle3D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 3, 'center')
		i = node.ReadFloat64A(i, 3, 'm1')
		i = node.ReadFloat64A(i, 3, 'm2')
		i = node.ReadFloat64A(i, 3, 'm3')
		i = node.ReadCrossRef(i, 'refCenter')
		return i

	def Read_9E43716B(self, node):
		i = node.Read_Header0()
		return i

	def Read_9ED6024F(self, node):
		i = node.Read_Header0()
		return i

	def Read_A244457B(self, node):
		i = node.Read_Header0()
		return i

	def Read_A31E29E0(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadParentRef(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = self.skipBlockSize(i)
		return i

	def Read_A3277869(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		return i

	def Read_A3B0404C(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_A4087E1F(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadChildRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		i = node.ReadLen32Text16(i, 'txt_0')
		i = node.ReadLen32Text16(i, 'txt_1')
		i = node.ReadLen32Text16(i, 'txt_2')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64(i, 'x')
		i = node.ReadLen32Text16(i, 'txt_3')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i, 'txt_4')
		i = node.ReadLen32Text16(i, 'txt_5')
		i = node.ReadLen32Text16(i, 'txt_6')
		i = node.ReadLen32Text16(i, 'txt_7')
		i = node.ReadLen32Text16(i, 'txt_8')
		i = node.ReadLen32Text16(i, 'txt_9')
		i = node.ReadLen32Text16(i, 'txt_A')
		i = node.ReadLen32Text16(i, 'txt_B')
		i = node.ReadLen32Text16(i, 'txt_C')
		return i

	def Read_A477243B(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i

	def Read_A5428F7A(self, node):
		i = node.Read_Header0()
		return i

	def Read_A78639EE(self, node):
		i = node.Read_Header0()
		return i

	def Read_A917F560(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadUInt16A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'cld_1')
		return i

	def Read_A98906A7(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt16A(i, 4, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		cnt, i = getUInt32(node.data, i)
		i = node.ReadUInt32A(i, cnt, 'arr')
		return i

	def Read_A99F1B26(self, node):
		i = node.Read_Header0()
		return i

	def Read_A9F6B271(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadParentRef(i)
		i = node.ReadChildRef(i, 'cld_1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refFeature')
		node.printable = False
		return i

	def Read_AAD64116(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'refDimension')
		i = node.ReadCrossRef(i, 'ref_3')
		i = node.ReadCrossRef(i, 'refValue')
		return i

	def Read_AE0E267A(self, node):
		i = node.Read_Header0()
		return i

	def Read_AE101F92(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32A(i, 3, 'a1')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadFloat64(i, 'a')
		i = node.ReadUInt16A(i, 3, 'a2')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 3, 'a3')
		i = node.ReadFloat64A(i, 3, 'a4')
		i = node.ReadFloat64A(i, 3, 'a5')
		i = node.ReadFloat64A(i, 3, 'a6')
		i = node.ReadFloat64A(i, 3, 'a7')
		i = node.ReadFloat64A(i, 3, 'a8')
		i = node.ReadFloat64A(i, 3, 'a9')
		return i

	def Read_AD416CEA(self, node):
		i = node.Read_Header0()
		return i

	def Read_AE5E4082(self, node):
		i = node.Read_Header0()
		return i

	def Read_B10D8B80(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		return i

	def Read_B1CF069E(self, node):
		i = node.Read_Header0()
		return i

	def Read_B382A87C(self, node):
		i = node.Read_Header0()
		return i

	def Read_B3A169E4(self, node):
		node.typeName = 'FxShell'
		i = node.Read_Header0()
		return i

	def Read_B4124F0C(self, node):
		i = node.Read_Header0()
		return i

	def Read_B58135C4(self, node):
		i = node.Read_Header0()
		return i

	def Read_B6482AF8(self, node):
		i = node.Read_Header0()
		return i

	def Read_B6A36C30(self, node):
		i = node.Read_Header0()
		return i

	def Read_B71CBEC9(self, node):
		node.typeName = 'SpiralCurve'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refSketch')
		i = self.skipBlockSize(i)
		return i

	def Read_B835A483(self, node):
		i = node.Read_Header0()
		return i

	def Read_B8CB3560(self, node):
		i = node.Read_Header0()
		return i

	def Read_B8DBEF70(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'xrf_0')
		i = self.skipBlockSize(i)
		return i

	def Read_B8E19017(self, node):
		i = node.Read_Header0()
		return i

	def Read_B8E19019(self, node):
		node.typeName = 'FxSplit'
		i = self.ReadContentHeader(node)
		return i

	def Read_BB1DD5DF(self, node):
		node.typeName = 'RDxVar'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadLen32Text16(i)
		return i

	def Read_BCBBAD85(self, node):
		i = node.Read_Header0()
		return i

	def Read_BDE13180(self, node):
		i = node.Read_Header0()
		return i

	def Read_BE8CEB3C(self, node):
		i = node.Read_Header0()
		return i

	def Read_BEE5961F(self, node):
		i = node.Read_Header0()
		return i

	def Read_BF32E0A6(self, node):
		i = node.Read_Header0()
		return i

	def Read_BFD09C43(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'label')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadParentRef(i)
		return i

	def Read_C1887310(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_1D_UINT32_, 'lst0')
		if (len(node.get('lst0')) > 0):
			i = node.ReadSInt32(i, 's32_0')
		return i

	def Read_C5538931(self, node):
		node.typeName = 'Constraint_Coincident3D'
		i = self.ReadConstraintHeader3D(node)
		return i

	def Read_C681C2E0(self, node):
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		return i

	def Read_C7A06AC2(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt16(i, 's16_0')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		return i

	def Read_C89EF3C0(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt16A(i, 2, 'a0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadParentRef(i)
#		node.printable = False
		return i

	def Read_CA02411F(self, node):
		i = node.Read_Header0()
		return i

	def Read_CA674C90(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		return i

	def Read_CAB7E237(self, node):
		i = node.Read_Header0()
		return i

	def Read_CB370222(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_CB6C0A56(self, node):
		i = node.Read_Header0()
		return i

	def Read_CC0F7521(self, node):
		node.typeName = 'AcisEntityWrapper'
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'xrf_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_CCC5085A(self, node):
		i = node.Read_Header0()
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'cld_0')
		return i

	def Read_CCE264C4(self, node):
		i = node.Read_Header0()
		return i

	def Read_CCE92042(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'cnt1')
		i = node.ReadUInt32(i, 'cnt2')
		cnt = node.get('cnt2')
		sep = ''
		lst = {}
		node.content += ' lst0={'
		j = 0
		while (j<cnt):
			key, i = getUInt32(node.data, i)
			node.content += '%s' %(sep)
			i = node.ReadChildRef(i, 'tmp')
			val = node.get('tmp')
			node.content += ':%02X' %(key)
			j += 1
			lst[key] = val
			sep = ','
			node.delete('tmp')

		node.content += '}'
		node.set('lst0', lst)

		return i

	def Read_CE52DF35(self, node):
		node.typeName = 'Point2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'refCoincidences')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst1')
		#i = node.ReadUInt32(i, 'u32_0')
		#i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst2')
		return i

	def Read_CE52DF3B(self, node):
		node.typeName = 'Circle2D'
#		node.typeName = 'Radius2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst1')
		i = node.ReadCrossRef(i, 'refCenter')
		i = node.ReadFloat64(i, 'r')
		i = node.ReadUInt8(i, 'u8_0')
		return i

	def Read_CE52DF3E(self, node):
		node.typeName = 'Point3D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		i = node.ReadFloat64(i, 'z')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'refs')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst1')
		return i

	def Read_CE52DF40(self, node):
		node.typeName = 'Direction'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'a')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		if (getFileVersion() > 2017):
			i += 4
		i = node.ReadFloat64(i, 'z')
		return i

	def Read_CE52DF3A(self, node):
		node.typeName = 'Line2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst1')
		else:
			node.content += ' lst1={}'
		i = node.ReadFloat64(i, 'x1')
		i = node.ReadFloat64(i, 'y1')
		i = node.ReadFloat64(i, 'x2')
		i = node.ReadFloat64(i, 'y2')

		return i

	def Read_CE52DF42(self, node):
		node.typeName = 'Plane'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2017):
			i += 4
		i = node.ReadUInt32(i, 'u32_1')
		if (node.get('u32_1') > 1):
			i = node.ReadUInt32(i, 'u32_2')
		i = node.ReadFloat64A(i, 3, 'origin')
		i = node.ReadFloat64A(i, 3, 'a1')
		i = node.ReadFloat64A(i, 3, 'axis')
		#a, i = getUInt8A(node.data, i, len(node.data) - i)
		#logError('%s %s' %(getFileVersion(), ' '.join(['%02X' %(h) for h in a])))

		return i

	def Read_CE7F937A(self, node):
		i = node.Read_Header0()
		return i

	def Read_CEFD3973(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		return i

	def Read_D13107FE(self, node):
		node.typeName = 'Constraint_Colinear3D'
		i = self.ReadConstraintHeader3D(node)
		return i

	def Read_D3F71C7A(self, node):
		i = node.Read_Header0()
		return i

	def Read_D5DAAA83(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		return i

	def Read_D5F19E40(self, node):
		i = node.Read_Header0()
		return i

	def Read_D5F19E41(self, node):
		i = node.Read_Header0()
		return i

	def Read_D77CC069(self, node):
		i = node.Read_Header0()
		return i

	def Read_D77CC06A(self, node):
		i = node.Read_Header0()
		return i

	def Read_D77CC06B(self, node):
		i = node.Read_Header0()
		return i

	def Read_D80CE357(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_0')
		i = node.ReadCrossRef(i, 'ref_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		if (getFileVersion() > 2017):
			i += 4
		else:
			i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList8(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadList8(i, AbstractNode._TYP_NODE_X_REF_, 'lst1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt16(i, 'u16_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_D83EF271(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		node.printable = False
		return i

	def Read_D8A9C970(self, node):
		i = node.Read_Header0()
		return i

	def Read_D94F1914(self, node):
		i = node.Read_Header0()
		return i

	def Read_D95B951A(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadUInt16(i, 'decimalsLength')
		i = node.ReadUInt16(i, 'decimalsAngle')
		i = node.ReadUInt16(i, 'u16_0')
		return i

	def Read_DB04EB11(self, node):
		node.typeName = 'Group3D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		if (getFileVersion() > 2016):
			i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst1')
		else:
			node.content += ' lst1={}'
		i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst2')
		i = node.ReadUInt32(i, 'u32_1')
		return i

	def Read_DBD67510(self, node):
		i = node.Read_Header0()
		return i

	def Read_DBDD00E3(self, node):
		i = node.Read_Header0()
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_1')
		i = node.ReadCrossRef(i, 'refSketch')
		i = node.ReadUInt32(i, 'u32_2')
		return i

	def Read_DD64FF02(self, node):
		i = node.Read_Header0()
		return i

	def Read_DDCF0E1C(self, node):
		i = node.Read_Header0()
		return i

	def Read_DE172BCF(self, node):
		i = node.Read_Header0()
		return i

	def Read_DF3B2C5B(self, node):
		i = node.Read_Header0()
		return i

	def Read_E0E3E202(self, node):
		i = node.Read_Header0()
		return i

	def Read_E1108C00(self, node):
		node.typeName = 'Radius2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			i = self.skipBlockSize(i)
			i = self.skipBlockSize(i)
			node.content += ' lst0={} lst1={}'
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadCrossRef(i, 'refObject')
		i = node.ReadCrossRef(i, 'refCenter')
		return i

	def Read_E192FA73(self, node):
		i = node.Read_Header0()
		return i

	def Read_E1D3D023(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadFloat32A(i, 3, 'a1')
		i = node.ReadUInt16A(i, 3, 'a2')
		if (getFileVersion() > 2016):
			i += 1
		else:
			i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 3, 'a3')
		i = node.ReadFloat64A(i, 3, 'a4')
		i = node.ReadSInt32A(i, 2, 'a5')
		i = node.ReadFloat64A(i, 31, 'a6')
		i = node.ReadUInt8A(i, 18, 'a7')
		i = node.ReadFloat64A(i, 6, 'a8')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadChildRef(i, 'ref_1')
		i = node.ReadCrossRef(i, 'ref_2')
		return i

	def Read_E2CCC3B7(self, node):
		i = node.Read_Header0()
		return i

	def Read_E558F428(self, node):
		i = node.Read_Header0()
		return i

	def Read_E562B07C(self, node):
		i = node.Read_Header0()
		return i

	def Read_E70647C3(self, node):
		i = node.Read_Header0()
		return i

	def Read_E8D30910(self, node):
		i = node.Read_Header0()
		return i

	def Read_E94FB6D9(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_E9821C66(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_1')
		return i

	def Read_EAC2875A(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadCrossRef(i, 'ref_1')
		return i

	def Read_EC7B8A2B(self, node):
		i = node.Read_Header0()
		return i

	def Read_EE792053(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_EF8279FB(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_EEE03AF5(self, node):
		i = self.ReadContentHeader(node)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'cld_1')
		i = node.ReadUInt16(i, 'u16_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPoint1')
		i = node.ReadCrossRef(i, 'refPoint2')
		i = node.ReadFloat64A(i, 2, 'a2')
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2010):
			i = node.ReadFloat64A(i, 8, 'a3')
		return i

	def Read_EEF10748(self, node):
		i = node.Read_Header0()
		return i

	def Read_EFF2257A(self, node):
		node.typeName = 'FxThicken'
		i = self.ReadContentHeader(node)
		return i

	def Read_F10C26A4(self, node):
		i = node.Read_Header0()
		return i

	def Read_F3F435A1(self, node):
		i = node.Read_Header0()
		return i

	def Read_F3FC69C6(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = node.ReadUInt32(i, 'flags')
		i = self.skipBlockSize(i)
		i = node.ReadParentRef(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = node.ReadUInt32(i, 'u32_1')
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'xrf_0')
		i = node.ReadUInt32(i, 'xrf_1')
		return i

	def Read_F4360D18(self, node):
		i = node.Read_Header0()
		return i

	def Read_F645595C(self, node):
		node.typeName = 'TransactablePartition'
		node.printable = False

		return len(node.data)

	def Read_F8A779F5(self, node):
		node.typeName = 'DimensionUnitCM'
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'factors')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		node.set('UNIT', True)
		return i

	def Read_F8A779F6(self, node):
		node.typeName = 'DimensionUnitINCH'
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadFloat64A(i, 2, 'factors')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		node.set('UNIT', True)
		return i

	def Read_F8A779FD(self, node):
		node.typeName = 'DimensionType'
		i = node.Read_Header0()
		i = self.skipBlockSize(i)
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList3(i, AbstractNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadChildRef(i, 'ref_1')
#		node.printable = False
		return i

	def Read_F8A77A03(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'refType')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lstValues')
		i = node.ReadUInt32(i, 'u32_0')
		ref = node.get('lstValues')[0]
		node.set('refValue', ref)
		return i

	def Read_F8A77A04(self, node):
		node.typeName = 'DimensionValue'
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'refType')
		i = self.skipBlockSize(i)
		i = node.ReadFloat64(i, 'x')
		i = node.ReadUInt16(i, 'type')
#		node.printable = False
		return i

	def Read_F8A77A05(self, node):
		node.typeName = 'DimensionValueDimensionRef'
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'cld_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refDimension')
		return i

	def Read_F8A77A06(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'refType')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refDimension')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refValue')
		i = self.skipBlockSize(i)
		return i

	def Read_F8A77A07(self, node):
		#node.typeName = 'DimensionValueUnknown'
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'refType')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refValue')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refValue1')
		i = self.skipBlockSize(i)
		return i

	def Read_F8A77A08(self, node):
		node.typeName = 'DimensionValueDimensionRef1'
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'refType')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refValue')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refFactor')
		i = self.skipBlockSize(i)
		return i

	def Read_F8A77A09(self, node):
		node.typeName = 'DimensionValueDimensionRef2'
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'refType')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refValue')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refFactor')
		i = self.skipBlockSize(i)
		return i

	def Read_F8A77A0C(self, node):
		node.typeName = 'DimensionValueRef'
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'refType')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refValue')
		i = self.skipBlockSize(i)
		return i

	def Read_F8A77A0D(self, node):
		i = node.Read_Header0()
		i = node.ReadChildRef(i, 'refType')
		i = self.skipBlockSize(i)
		i = node.ReadChildRef(i, 'refValue')
		i = self.skipBlockSize(i)
		return i

	def Read_F9372FD4(self, node):
		node.typeName = 'Spline2D'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'points')
		i = self.skipBlockSize(i)
		if (getFileVersion() > 2012):
			node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst1')
			i += 8
		else:
			node.content += ' lst1={}'
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadUInt16A(i, 5, 'a0')
		i = node.ReadCrossRef(i, 'ref_2')
		i = node.ReadUInt16A(i, 5, 'a1')
		i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst1')
		#i = node.ReadUInt32A(i, 6, 'a2')
		#if (getFileVersion() > 2012):
		#	i += 4
		#i = node.ReadList2(i, AbstractNode._TYP_2D_UINT16_, 'lst2')
		return i

	def Read_F94FF0D9(self, node):
		node.typeName = 'Spline3D_Curve'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refGroup')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'u8_0')
		i = node.ReadCrossRef(i, 'refSketch')
		if (getFileVersion() > 2012):
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_FLOAT64_, 'lst0')
			i = node.ReadList6(i, AbstractNode._TYP_MAP_X_REF_KEY_, 'lst1')
		else:
			node.content += ' lst0={} lst1={}'
		return i

	def Read_F9884C43(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst0')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst1')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_REF_, 'lst2')
		i = node.ReadUInt32A(i, 2, 'a1')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'xrf_0')
		if (getFileVersion() > 2011):
			i = node.ReadCrossRef(i, 'xrf_1')
		return i

	def Read_F9DB9290(self, node):
		i = node.Read_Header0()
		return i

	def Read_FAD9A9B5(self, node):
		node.typeName = 'MirrorPattern'
		i = self.ReadContentHeader(node)
		return i

	def Read_FBDB891F(self, node):
		'''
		Behaves like an equal constraint
		'''
		node.typeName = 'Constraint_PolygonEdge2D'
		i = self.ReadConstraintHeader2D(node)
		i = node.ReadCrossRef(i, 'refLine1')
		i = node.ReadCrossRef(i, 'refLine2')
		i = node.ReadCrossRef(i, 'refPoint')
		i = node.ReadCrossRef(i, 'xrf_4')
		i = node.ReadCrossRef(i, 'xrf_5')
		i = node.ReadUInt32A(i, 2, 'a1')
		return i

	def Read_FEB0D977(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadSInt32(i, 's32_0')
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refPoint2D')
		i = node.ReadCrossRef(i, 'refOrientation')
		i = node.ReadCrossRef(i, 'refPoint3D')
		return i

	def Read_FC203F47(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_FF15793D(self, node):
		i = self.ReadContentHeader(node)
		return i

	def Read_FF46726C(self, node):
		i = node.Read_Header0()
		return i

	def Read_FFD270B8(self, node):
		i = self.ReadContentHeader(node)
		return i
	def Read_10DC334C(self, node):
		i = node.Read_Header0()
		return i
	def Read_13F4E5A3(self, node):
		i = node.Read_Header0()
		return i
	def Read_1488B839(self, node):
		i = node.Read_Header0()
		return i
	def Read_160915E2(self, node):
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = self.skipBlockSize(i)
		i = node.ReadUInt32(i, 'u32_0')
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refSketch')
		i = self.skipBlockSize(i)
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		if (getFileVersion() > 2012):
			i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		else:
			i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'refCenter')
		i = node.ReadFloat64(i, 'r')
		i = node.ReadUInt8(i, 'u8_0')
		i = self.skipBlockSize(i)
		return i
	def Read_173E51F4(self, node):
		i = node.Read_Header0()
		return i
	def Read_182D1C40(self, node):
		i = node.Read_Header0()
		return i
	def Read_182D1C8A(self, node):
		i = node.Read_Header0()
		return i
	def Read_197F7DBE(self, node):
		i = node.Read_Header0()
		return i
	def Read_19F763CB(self, node):
		i = node.Read_Header0()
		return i
	def Read_1A1C8265(self, node):
		i = node.Read_Header0()
		return i
	def Read_1B48AD11(self, node):
		i = node.Read_Header0()
		return i
	def Read_1DCBFBA7(self, node):
		i = node.Read_Header0()
		return i
	def Read_1DEE2CF3(self, node):
		i = node.Read_Header0()
		return i
	def Read_1EF28758(self, node):
		i = node.Read_Header0()
		return i
	def Read_20976662(self, node):
		i = node.Read_Header0()
		return i
	def Read_2148C03C(self, node):
		i = node.Read_Header0()
		return i
	def Read_22178C64(self, node):
		i = node.Read_Header0()
		return i
	def Read_255D7ED7(self, node):
		i = node.Read_Header0()
		return i
	def Read_26287E96(self, node):
		node.typeName = 'DeselTable'
		i = self.ReadContentHeader(node)
		i = self.skipBlockSize(i)
		i = node.ReadCrossRef(i, 'ref_1')
		i = node.ReadSInt32(i, 's32_0')
		i = node.ReadUUID(i, 'uid')
		i = node.ReadLen32Text16(i)
		i = node.ReadCrossRef(i, 'refParent')
		i = node.ReadList2(i, AbstractNode._TYP_NODE_X_REF_, 'lst0')
		i = node.ReadUInt8(i, 'selected')
		return i
	def Read_2801D6C6(self, node):
		i = node.Read_Header0()
		return i
	def Read_2A636E60(self, node):
		i = node.Read_Header0()
		return i
	def Read_2B48CE72(self, node):
		i = node.Read_Header0()
		return i
	def Read_2E692E29(self, node):
		i = node.Read_Header0()
		return i
	def Read_2F39A056(self, node):
		i = node.Read_Header0()
		return i
	def Read_3170E5B0(self, node):
		i = node.Read_Header0()
		return i
	def Read_31F02EED(self, node):
		i = node.Read_Header0()
		return i
	def Read_339807AC(self, node):
		i = node.Read_Header0()
		return i
	def Read_34FAB548(self, node):
		i = node.Read_Header0()
		return i
	def Read_38C2654E(self, node):
		i = node.Read_Header0()
		return i
	def Read_38C74735(self, node):
		i = node.Read_Header0()
		return i
	def Read_3A083C7B(self, node):
		i = self.ReadContentHeader(node)
		return i
	def Read_3E55D947(self, node):
		i = self.ReadContentHeader(node)
		return i
	def Read_3F36349F(self, node):
		i = node.Read_Header0()
		return i
	def Read_3F3634A0(self, node):
		i = node.Read_Header0()
		return i
	def Read_3F4FA55F(self, node):
		i = node.Read_Header0()
		return i
	def Read_40236C89(self, node):
		i = node.Read_Header0()
		return i
	def Read_40AFEBA1(self, node):
		node.typeName = 'DimensionValue_40AFEBA1'
		i = node.Read_Header0()
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		return i
	def Read_424EB7D7(self, node):
		i = node.Read_Header0()
		return i
	def Read_436D821A(self, node):
		i = node.Read_Header0()
		return i
	def Read_45741FAF(self, node):
		i = node.Read_Header0()
		return i
	def Read_46407F70(self, node):
		i = node.Read_Header0()
		return i
	def Read_4F8A6797(self, node):
		i = node.Read_Header0()
		return i
	def Read_537799E0(self, node):
		i = node.Read_Header0()
		return i
	def Read_55279EE0(self, node):
		i = node.Read_Header0()
		return i
	def Read_5838B762(self, node):
		i = node.Read_Header0()
		return i
	def Read_5CB011E2(self, node):
		i = node.Read_Header0()
		return i
	def Read_5F425538(self, node):
		i = node.Read_Header0()
		return i
	def Read_5F9D0025(self, node):
		node.typeName = 'DimensionValue_5F9D0025'
		i = node.Read_Header0()
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		return i
	def Read_5FB25A7E(self, node):
		node.typeName = 'FxBoolean'
		i = self.ReadContentHeader(node)
		return i
	def Read_603428AE(self, node):
		i = node.Read_Header0()
		return i
	def Read_606D9AB1(self, node):
		i = node.Read_Header0()
		return i
	def Read_63E209F9(self, node):
		i = node.Read_Header0()
		return i
	def Read_66398149(self, node):
		i = node.Read_Header0()
		return i
	def Read_6A3EEA31(self, node):
		i = node.Read_Header0()
		return i
	def Read_6C7D97A9(self, node):
		i = node.Read_Header0()
		return i
	def Read_6E2BCB60(self, node):
		i = node.Read_Header0()
		return i
	def Read_7256922C(self, node):
		i = self.ReadContentHeader(node)
		return i
	def Read_72C97D63(self, node):
		i = node.Read_Header0()
		return i
	def Read_75A6689B(self, node):
		i = node.Read_Header0()
		return i
	def Read_778752C6(self, node):
		i = node.Read_Header0()
		return i
	def Read_7C6D7B13(self, node):
		i = node.Read_Header0()
		return i
	def Read_7E36DE81(self, node):
		i = node.Read_Header0()
		return i
	def Read_7F936BAA(self, node):
		i = node.Read_Header0()
		return i
	def Read_80102AC1(self, node):
		i = node.Read_Header0()
		return i
	def Read_831EBCE9(self, node):
		i = node.Read_Header0()
		return i
	def Read_83D31932(self, node):
		i = node.Read_Header0()
		return i
	def Read_86197AE1(self, node):
		i = node.Read_Header0()
		return i
	def Read_88FA65CA(self, node):
		i = node.Read_Header0()
		return i
	def Read_8AFFBE5A(self, node):
		i = node.Read_Header0()
		return i
	def Read_8E5D4198(self, node):
		i = node.Read_Header0()
		return i
	def Read_8FEC335F(self, node):
		i = node.Read_Header0()
		return i
	def Read_90874D60(self, node):
		i = node.Read_Header0()
		return i
	def Read_9271AB29(self, node):
		i = node.Read_Header0()
		return i
	def Read_951388CF(self, node):
		i = node.Read_Header0()
		return i
	def Read_9C3D6A2F(self, node):
		i = node.Read_Header0()
		return i
	def Read_9DA736B0(self, node):
		i = node.Read_Header0()
		return i
	def Read_A040D1B1(self, node):
		i = node.Read_Header0()
		return i
	def Read_A29C84B7(self, node):
		i = node.Read_Header0()
		return i
	def Read_A5977BAA(self, node):
		i = node.Read_Header0()
		return i
	def Read_A6118E11(self, node):
		i = node.Read_Header0()
		return i
	def Read_A644E76A(self, node):
		i = node.Read_Header0()
		return i
	def Read_A76B22A0(self, node):
		i = node.Read_Header0()
		return i
	def Read_AA805A06(self, node):
		i = node.Read_Header0()
		return i
	def Read_AD0D42B2(self, node):
		i = node.Read_Header0()
		return i
	def Read_B269ACEF(self, node):
		i = node.Read_Header0()
		return i
	def Read_B292F94A(self, node):
		i = node.Read_Header0()
		return i
	def Read_B3EAA9EE(self, node):
		i = node.Read_Header0()
		return i
	def Read_B447E0DC(self, node):
		i = node.Read_Header0()
		return i
	def Read_B59F6734(self, node):
		i = node.Read_Header0()
		return i
	def Read_B5D4DEE6(self, node):
		i = node.Read_Header0()
		return i
	def Read_B6C5116B(self, node):
		i = node.Read_Header0()
		return i
	def Read_BF3B5C84(self, node):
		i = node.Read_Header0()
		return i
	def Read_BF8B8868(self, node):
		i = node.Read_Header0()
		return i
	def Read_C6E21E1A(self, node):
		i = node.Read_Header0()
		return i
	def Read_CB072B3B(self, node):
		i = node.Read_Header0()
		return i
	def Read_CCD87CBA(self, node):
		i = node.Read_Header0()
		return i
	def Read_CE4A0723(self, node):
		i = node.Read_Header0()
		return i
	def Read_D2D440C0(self, node):
		i = node.Read_Header0()
		return i
	def Read_D2DA2CF0(self, node):
		i = node.Read_Header0()
		return i
	def Read_D524C30A(self, node):
		i = node.Read_Header0()
		return i
	def Read_D589D818(self, node):
		i = node.Read_Header0()
		return i
	def Read_D5F19E42(self, node):
		i = node.Read_Header0()
		return i
	def Read_D61732C1(self, node):
		i = node.Read_Header0()
		return i
	def Read_D7BE5663(self, node):
		i = node.Read_Header0()
		return i
	def Read_D7F4C16F(self, node):
		i = node.Read_Header0()
		return i
	def Read_DA2C89C5(self, node):
		i = node.Read_Header0()
		return i
	def Read_DA4970B5(self, node):
		i = node.Read_Header0()
		return i
	def Read_DC93DB08(self, node):
		i = node.Read_Header0()
		return i
	def Read_DFB2586A(self, node):
		i = node.Read_Header0()
		return i
	def Read_E0EA12F2(self, node):
		i = node.Read_Header0()
		return i
	def Read_E28D3B3F(self, node):
		i = node.Read_Header0()
		return i
	def Read_E524B878(self, node):
		i = node.Read_Header0()
		return i
	def Read_E70647C2(self, node):
		i = node.Read_Header0()
		return i
	def Read_EA680672(self, node):
		node.typeName = 'FxTrim'
		i = self.ReadContentHeader(node)
		return i
	def Read_EE767654(self, node):
		i = self.ReadContentHeader(node)
		return i
	def Read_EFE47BB4(self, node):
		i = self.ReadContentHeader(node)
		return i
	def Read_F0677096(self, node):
		i = self.ReadContentHeader(node)
		return i
	def Read_F5E51520(self, node):
		i = node.Read_Header0()
		return i
	def Read_F7693D55(self, node):
		i = node.Read_Header0()
		return i
	def Read_F8A779F1(self, node):
		node.typeName = 'DimensionValue_F8A779F1'
		i = node.Read_Header0()
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		return i
	def Read_F8A779F7(self, node):
		node.typeName = 'DimensionValue_F8A779F7'
		i = node.Read_Header0()
		i = node.ReadFloat64(i, 'x')
		i = node.ReadFloat64(i, 'y')
		return i
	def Read_FA6E9782(self, node):
		i = node.Read_Header0()
		return i
	def Read_FB73FDDF(self, node):
		i = self.ReadContentHeader(node)
		return i
	def Read_FD590AA5(self, node):
		i = node.Read_Header0()
		return i
	def Read_FD7702B0(self, node):
		i = node.Read_Header0()
		return i

	# override importerSegment.setNodeData
	def setNodeData(self, node, data, seg):
		offset = node.offset
		nodeTypeID, i = getUInt8(data, offset - 4)
		node.typeID = getNodeType(nodeTypeID, seg)
		if (isinstance(node.typeID, UUID)):
			node.typeName = '%08X' % (node.typeID.time_low)
			i = offset + node.size
			s, dummy = getUInt32(data, i)
			id = node.typeID.time_low
			if ((s != node.size) and ((id == 0x2B48A42B) or (id == 0x90874D63))):
				s, dummy = getUInt32(data, i)
				while ((s != node.size) and (i < len(data))):
					i += 1
					s, dummy = getUInt32(data, i)
				node.size = i - offset
		else:
			node.typeName = '%08X' % (node.typeID)

		node.data = data[offset:offset + node.size]
