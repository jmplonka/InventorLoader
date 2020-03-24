# -*- coding: utf-8 -*-
'''
importerUFRxDoc.py:
Simple approach to read/analyse Autodesk (R) Invetor (R) files.
'''

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

import traceback, io, re
from importerUtils   import *

schema = 0

class UfrxObject(object):
	def __str__(self): return ''
	def __repr__(self): return self.__str__()

class UFRxDocument(object):
	def __init__(self):
		self.schema   = 0                                            # UInt16
		self.arr1     = []                                           # UInt16A[]
		self.arr2     = []*4                                         # UInt16A[4]
		self.dat1     = None                                         # DateTime
		self.arr3     = []*4                                         # UInt16A[4]
		self.dat2     = None                                         # DateTime
		self.comment  = u""                                          # UTF_16_LE
		self.arr4     = []*12                                        # UInt16A[12]
		self.dat3     = None                                         # creation date of 1st version
		self.revision = UUID('00000000-0000-0000-0000-000000000000') # UID
		self.flags    = 0                                            # UInt32
		self.uid2     = UUID('00000000-0000-0000-0000-000000000000') # UID
		self.fName    = u""                                          # UTF_16_LE
		self.n0       = 0                                            # UInt16A
		self.arr5     = []                                           # ???
		self.exports  = []                                           # readExports
		self.n1       = 0                                            # UInt32
		self.txt1     = u""                                          # UTF_16_LE
		self.arr6     = [0]*10                                       # UInt16A[10]
		self.n2       = 0                                            # UInt16
		self.uid3     = UUID('4d29b490-11d0-49b2-077e-c39300000006') # UUID
		self.uid4     = UUID('4d29b490-11d0-49b2-077e-c39300000006') # UUID
		self.n3       = 0                                            # UInt16
		self.iamRefs  = []                                           # readIamRefs
		self.iptRefs  = []                                           # readIptRefs
		self.b1       = False                                        # Boolean
		self.n4       = 0                                            # UInt16
		self.fileRefs = []                                           # readFileRefs
		self.lst1     = []                                           # readL7BHLst1
		self.lst2     = []                                           # readL7BHLst1
		self.n5       = 0                                            # UInt32
		self.settings = []                                           # readSettings
		self.n6       = 0                                            # UInt16
		self.uids     = []                                           # UID[]
		self.envList  = []                                           # readListEnv
		self.n7       = 0                                            # UInt8
		self.arr7     = []                                           # Float64[]
		self.n8       = 0                                            # UInt8
		self.obj1     = None                                         # (UTF_16_LE, UTF_16_LE, UTF_16_LE, Float64, UInt16)?
		self.n9       = 0                                            # UInt16
		self.n10      = 0                                            # UInt16
		self.n11      = 0                                            # UInt16
		self.lst3     = []                                           # readListTxtStrUid
		self.posMin   = (0., 0., 0.)                                 # Float64[3]
		self.posMax   = (0., 0., 0.)                                 # Float64[3]
		self.iMates   = []                                           # (UTF_16_LE, UTF_16_LE, UInt8, UID, UInt16)[]
		self.iMate    = u""                                          # UTF_16_LE

		self.arr8     = []                                           # UInt8
		self.n12      = 0                                            # UInt8

class UfrxBBLTvL(UfrxObject):
	def __init__(self):
		super(UfrxBBLTvL, self).__init__()
		self.b  = False
		self.t  = 0
		self.n1 = 0
		self.v  = None
	def getValueAsStr(self):
		if (self.t in [0x10]):
			return u",({%s},{%s}" %(self.v[0], self.v[1])
		return u"%s" %(self.v)

	def __str__(self):
		s = u"%02X,%s,%04X" %(self.t, self.b, self.n1)
		s += self.getValueAsStr()
		return s

class UfrxBBLTvLNew(UfrxBBLTvL):
	def __init__(self):
		super(UfrxBBLTvLNew, self).__init__()
		self.n2 = 0
	def getValueAsStr(self):
		if (isinstance(self.v, UUID)): return u",{%s}" %(self.v)
		if (type(self.v) == str):      return u",'%s'" %(self.v)
		if (t in [0x19]):            return u",%04X" %(self.v)
		if (t in [0x10]):            return u",%02X" %(self.v)
		return u"%s" %(self.v)
	def __str__(self):
		s = super(UfrxBBLTvLNew, self).__str__()
		return s + u",%04X" %(self.n2)

class UfrxPartRef(UfrxObject):
	def __init__(self):
		super(UfrxPartRef, self).__init__()
		self.n1 = 0
		self.n2 = 0
		self.n3 = 0
		self.a1 = [0,0,0]
		self.u1	= None
		self.u2 = None
		self.a2 = [0, 0, 0, 0]
		self.t1 = u""
		self.t2 = u""
		self.t3 = u""
	def __str__(self):
		return u"%04X,%04X,%03X,%s,{%s},{%s},%s,'%s','%s','%s'" %(self.n1, self.n2, self.n3, IntArr2Str(self.a1, 3), self.u1, self.u2, IntArr2Str(self.a2, 4), self.t1, self.t2, self.t3)

class UfrxExport(UfrxObject):
	def __init__(self):
		super(UfrxExport, self).__init__()
		self.s = u""
		self.u = None
		self.t = u""
	def __str__(self):
		return u"'%s',{%s},\"%s\"" %(self.s, self.u, self.t)

class UfrxFileRef(UfrxObject):
	def __init__(self):
		super(UfrxObject, self).__init__()
		self.n1   = 0
		self.fDat = None
		self.a1   = []
		self.fNam = u""
		self.n2   = -1
		self.wks  = u""
		self.n3   = 0
		self.t3   = u""
		self.a2   = [0,0,0,0]
		self.su   = None
	def __str__(self):
		return u"%04X,#%s#,%s,'%s',%d,'%s',%03X,'%s',%s\n" %(self.n1, self.fDat, IntArr2Str(self.a1, 4), self.fNam, self.n2, self.wks, self.n3, self.t3, IntArr2Str(self.a2, 3))

class UfrxL7HHL(UfrxObject):
	def __init__(self):
		super(UfrxL7HHL, self).__init__()
		self.a1      = []
		self.n1      = 0
		self.n2      = 0
		self.l1      = []
		self.l2      = []
		self.exports = []
		self.a2      = []
		self.a3      = []
		self.a4      = []
		self.su      = None
	def __str__(self):
		s = u"%s,%03X,%02X,%s,%s" %(IntArr2Str(self.a1, 4), self.n1, self.n2, IntArr2Str(self.a2, 2), IntArr2Str(self.a4, 2))
		if (self.su is None):
			s += u",NULL"
		else:
			s += u",('%s',{%s})" %(self.su[0], self.su[1])
		return s

class UfrxEnv(UfrxObject):
	def __init__(self):
		super(UfrxEnv, self).__init__()
		self.u = None
		self.a = []
		self.n = 0
		self.b = False
		self.t = u""

	def __str__(self):
		return u"{%s}, %s, %04X, %s, '%s'\n" %(self.u, IntArr2Str(self.a, 4), self.n, self.b, self.t)

class UfrxTSU(UfrxObject):
	def __init__(self):
		super(UfrxTSU, self).__init__()
		self.s  = u""
		self.t  = u""
		self.u  = None
		self.m  = 0
		self.a1 = []
		self.a2 = []
		self.p  = {}
		self.a2 = []
		self.v1 = None
		self.v2 = None
		self.n = 0

	def __str__(self):
		if (self.u is None):
			u = 'NULL'
		else:
			u = u"{%s}" %(self.u)
		return u"\"%s\",'%s',%s,%s,%s,%02X" %(self.s, self.t, u.upper(), IntArr2Str(self.a1, 3), IntArr2Str(self.a2, 3), self.n)

class UfrxS2I(UfrxObject):
	def __init__(self):
		super(UfrxS2I, self).__init__()
		self.t   = u""
		self.lst = [0]*2
		self.a2  = [0]*5
		self.n   = 0
	def __str__(self):
		return u"'%s',%s,%02X" %(self.t, IntArr2Str(self.a2,4), self.n)

def readBoolean(data, offset, log, txt):
	v, i = getBoolean(data, offset)
	log.write(u"%s:\t%s\n" %(txt, v))
	return v, i

def readDateTime(data, offset, log, txt):
	v, i = getDateTime(data, offset)
	log.write(u"%s:\t#%s#\n" %(txt, v))
	return v, i

def readFloat32_3D(data, offset, log, txt):
	v, i = getFloat32_3D(data, offset)
	log.write(u"%s:\t(%s)\n" %(txt, FloatArr2Str(v)))
	return v, i

def readUInt8(data, offset, log, txt):
	v, i = getUInt8(data, offset)
	log.write(u"%s:\t%02X\n" %(txt, v))
	return v, i

def readUInt8A(data, offset, log, txt, cnt):
	v, i = getUInt8A(data, offset, cnt)
	log.write(u"%s:\t[%s]\n" %(txt, IntArr2Str(v, 2)))
	return v, i

def readUInt16(data, offset, log, txt):
	v, i = getUInt16(data, offset)
	log.write(u"%s:\t%04X\n" %(txt, v))
	return v, i

def readUInt16A(data, offset, log, txt, cnt):
	v, i = getUInt16A(data, offset, cnt)
	log.write(u"%s:\t[%s]\n" %(txt, IntArr2Str(v, 3)))
	return v, i

def readUInt32(data, offset, log, txt):
	v, i = getUInt32(data, offset)
	log.write(u"%s:\t%06X\n" %(txt, v))
	return v, i

def readUInt32A(data, offset, log, txt, cnt):
	v, i = getUInt32A(data, offset, cnt)
	log.write(u"%s:\t[%s]\n" %(txt, IntArr2Str(v, 4)))
	return v, i

def readSInt32(data, offset, log, txt):
	v, i = getSInt32(data, offset)
	log.write(u"%s:\t%d\n" %(txt, v))
	return v, i

def readUID(data, offset, log, txt):
	v, i = getUUID(data, offset)
	log.write(u"%s:\t{%s}\n" %(txt, v))
	return v, i

def readText16(data, offset, log, txt):
	v, i = getLen32Text16(data, offset)
	log.write(u"%s:\t'" %(txt))
	log.write(v)
	log.write(u"'\n")
	return v, i

def readBBLTvL(data, offset):
	# BBLTvL:
	# BB:  UInt16
	# L:  UInt32
	# Tv: UInt8
	#     v = UInt8   <=> T in [10h]
	#     v = UInt32  <=> T in [19h]
	#     v = BSTR_16 <=> T in [05h, 1Eh]
	#     v = UUID    <=> T in [12h, 16h, 17h, 18h, 1Ch, 1Fh, 20h, 22h, 24h, 25h, 2Ah, 2Bh]
	a      = {}
	n, i   = getUInt32(data, offset)
	cnt, i = getUInt32(data, i)
	for j in range(cnt):
		o = UfrxBBLTvL()
		o.b, i  = getBoolean(data, i)
		o.t, i  = getUInt8(data, i)
		o.n1, i = getUInt32(data, i)
		t, i    = getUInt8(data, i)
		assert t == o.t
		if (t in [0x12]):
			u1, i  = getUUID(data, i)
			u2, i  = getUUID(data, i)
			v = (u1, u2)
		else:
			raise ValueError(u"Unknown type %02X for array element in BBLTvL2!" %(t))
		o.n2, i = getUInt32(data, i)
		a[t] = o
	return (n, a), i

def readBBLTvLNew(data, offset):
	# BBLTvL:
	# BB:  UInt16
	# L:  UInt32
	# Tv: UInt8
	#     v = UInt8   <=> T in [10h]
	#     v = UInt32  <=> T in [19h]
	#     v = BSTR_16 <=> T in [05h, 1Eh]
	#     v = UUID    <=> T in [12h, 16h, 17h, 18h, 1Ch, 1Fh, 20h, 22h, 24h, 25h, 2Ah, 2Bh]
	a      = {}
	n, i   = getUInt32(data, offset)
	cnt, i = getUInt32(data, i)
	for j in range(cnt):
		o = UfrxBBLTvLNew()
		o.b, i  = getBoolean(data, i)
		o.t, i  = getUInt8(data, i)
		o.n1, i = getUInt32(data, i)
		t, i    = getUInt8(data, i)
		assert t == o.t
		if (t in [0x11, 0x12, 0x13, 0x16, 0x17, 0x18, 0x1C, 0x1F, 0x20, 0x22, 0x23, 0x24, 0x25, 0x2A, 0x2B]):
			v, i  = getUUID(data, i)
		elif (t in [0x05, 0x1E]):
			v, i  = getLen32Text16(data, i)
		elif (t in [0x19]):
			v, i  = getUInt32(data, i)
		elif (t in [0x10]):
			v, i  = getUInt8(data, i)
		else:
			raise ValueError(u"Unknown type %02X for array element in BBLTvL!" %(t))
		o.n2, i = getUInt32(data, i)
		a[t] = o
	return (n, a), i

def readExports(data, offset, log, txt):
	exports = {}
	cnt, i  = getUInt32(data, offset)
	log.write(u"%s: count=%d\n" %(txt, cnt))
	for j in range(cnt):
		k, i = getLen32Text16(data, i)
		v, i = getLen32Text16(data, i)
		exports[k] = v
		log.write(u"  [%02X]: '%s'='%s'\n" %(j, k, v))
	return exports, i

def readIamRefs(data, offset, log, txt):
	refs   = []
	if (schema >= 0x0C):
		cnt, i = getUInt16(data, offset)
	else:
		cnt, i = getUInt32(data, offset)
	log.write(u"%s: count=%d\n" %(txt, cnt))
	for j in range(cnt):
		n1, i = getUInt8(data, i)
		t1, i = getLen32Text16(data, i)
		a1, i = getUInt16A(data, i, 4)
		refs.append([n1, t1] + list(a1))
		log.write(u"  [%02X]: %02X,'%s',%s\n" %(j, n1, t1, IntArr2Str(a1, 3)))
	return refs, i

def readIptRefs(data, offset, log, txt):
	refs   = []
	cnt, i = getUInt32(data, offset)
	nam, i = getLen32Text16(data, i)
	log.write(u"%s: '%s' count=%d\n" %(txt, nam, cnt))
	for j in range(cnt):
		ref = UfrxPartRef()
		ref.n1, i = getUInt32(data, i)      # index
		ref.t1, i = getLen32Text16(data, i) # filepath
		ref.n2, i = getUInt32(data, i)
		ref.t2, i = getLen32Text16(data, i) # workspace
		ref.n3, i = getUInt16(data, i)
		ref.t3, i = getLen32Text16(data, i) # name
		ref.a1, i = getUInt16A(data, i, 4)
		ref.u1, i = getUUID(data, i)
		ref.u2, i = getUUID(data, i)
		ref.a2, i = getUInt32A(data, i, 3)
		refs.append(ref)
		log.write(u"  [%02X]: %s\n" %(j, ref))

	return (nam, refs), i

def readFileRefs(data, offset, log, txt):
	files  = []
	cnt, i = getUInt32(data, offset)
	log.write(u"%s: count=%d\n" %(txt, cnt))
	for j in range(cnt):
		ref = UfrxFileRef()
		ref.n1, i   = getUInt32(data, i)      # index
		ref.fDat, i = getDateTime(data, i)	  # file's date
		n, k = getUInt32(data, i)
		while (n < 0xFFFF):
			ref.a1.append(n)
			n, k = getUInt32(data, k)
		ref.a1 = ref.a1[:-1]
		ref.fNam, i = getLen32Text16(data, k - 8) # file's path
		ref.n2, i   = getSInt32(data, i)
		ref.wks, i  = getLen32Text16(data, i)     # workspace
		ref.n3, i   = getUInt16(data, i)
		ref.t3, i   = getLen32Text16(data, i)     # ???.fins
		ref.a2, i   = getUInt16A(data, i, 4)
		log.write("  [%02X]: %s\n" %(j, ref))
		files.append(ref)
	return files, i

def readXprtList(data, offset):
	lst = []
	cnt, i = getUInt32(data, offset)
	for j in range(cnt):
		xprt = UfrxExport()
		xprt.s, i = getLen32Text16(data, i) # name
		xprt.u, i = getUUID(data, i)
		xprt.t, i = getLen32Text8(data, i)  # Export
		lst.append(xprt)
	return lst, i

def logWritePresentations(log, txt, v):
	if (v is not None):
		log.write(u"    %s: count=%X\n" %(txt, len(v)))
		for j, o in enumerate(v):
			log.write(u"      [%02X]: '%s',{%s},\"%s\"\n" %(j, o[0], o[1], o[2]))

def logWriteBBLTVLst(log, txt, v):
	if (v is not None):
		log.write(u"    %s: n=%d, count=%X\n" %(txt, v[0], len(v[1])))
		for j, o in enumerate(v[1]):
			log.write(u"      [%02X]: %s\n" %(j, o))

def readL7BHLst1(data, offset, log, txt):
	lst = []
	cntJ, i = getUInt32(data, offset)
	log.write(u"%s: count=%d\n" %(txt, cntJ))
	for j in range(cntJ):
		l7bhls = UfrxL7HHL()
		l7bhls.a1, i = getUInt32A(data, i, 7)
		if (schema >= 0x0C):
			l7bhls.n1, i = getUInt16(data, i)
		else:
			l7bhls.n1, i = getUInt8(data, i)
		tst, k = getUInt8A(data, i + 1, 3)
		if (tst != (0,0,0)):
			l7bhls.n2, i = getUInt8(data, i)
		l7bhls.l1, i      = readBBLTvLNew(data, i)
		l7bhls.l2, i      = readBBLTvLNew(data, i)
		l7bhls.exports, i = readXprtList(data, i)
		if (schema >= 0x0C): l7bhls.a2, i = getUInt8A(data, i, 1)
		cntK, i = getUInt32(data, i)
		for k in range(cntK):
			t, i = getLen32Text16(data, i)
			u, i = getUUID(data, i)
			s, i = getLen32Text8(data, i)
			l7bhls.a3.append((t, u, s))
		l7bhls.a4, i = getUInt8A(data, i, 6)
		if (l7bhls.a1[0] == 1):
			s, i = getLen32Text16(data, i) # name
			u, i = getUUID(data, i)        # UID
			l7bhls.su = (s, u)
		log.write(u"  [%02X]: %s\n" %(j, l7bhls))
		logWritePresentations(log, 'presentations', l7bhls.a3)
		logWriteBBLTVLst(log, 'bbltvl1', l7bhls.l1)
		logWriteBBLTVLst(log, 'bbltvl2', l7bhls.l2)
		log.write(u"  exports: count=%X\n" %(len(l7bhls.exports)))
		for k, o in enumerate(l7bhls.exports):
			log.write(u"      [%02X]: %s\n" %(k, o))
		lst.append(l7bhls)
	return  lst, i

def readTxt2I(data, offset, log, txt):
	lst = []
	cnt, i = getUInt32(data, offset)
	log. write(u"%s: count=%d\n" %(txt, cnt))
	for j in range(cnt):
		o = UfrxS2I()
		o.t, i   = getLen32Text16(data, i)
		o.lst, i = readBBLTvL(data, i)
		o.a2, i  = getUInt32A(data, i, 3)
		if (o.lst[0] > 0): o.n, i   = getUInt8(data, i)
		log.write(u"  [%02X] %s\n" %(j, o))
		logWriteBBLTVLst(log, 'btl', o.lst)
	return lst, i

def readSettings(data, offset, log, txt):
	settings = {}
	cnt, i   = getUInt32(data, offset)
	log.write(u"%s: count=%d\n" %(txt, cnt))
	for j in range(cnt):
		t, i = getUInt8(data, i)
		if (t in [0x04]):
			v, i = getLen32Text16(data, i)
			log.write(u"  %02X = '%s'\n" %(t, v))
		elif (t in [0x0F, 0x10, 0x1D]):
			v, i = getUInt8(data, i)
			log.write(u"  %02X = %02X\n" %(t, v))
		elif (t in [0x12, 0x15, 0x1A, 0x1B, 0x1C, 0x20, 0x23, 0x28, 0x29, 0x2B]):
			v, i = getUUID(data, i)
			log.write(u"  %02X = {%s}\n" %(t, v))
		elif (t in [0x13, 0x16, 0x17, 0x18, 0x1F, 0x24, 0x25, 0x2A]):
			u1, i = getUUID(data, i)
			u2, i = getUUID(data, i)
			v = [u1, u2]
			log.write(u"  %02X = {%s},{%s}\n" %(t, u1, u2))
		elif (t in [0x11]):
			v, i = getUUID(data, i)
			u, j = getUUID(data, i)
			if (v == u):
				i = j
			log.write(u"  %02X = {%s}\n" %(t, v))
		else:
			raise ValueError(u"Unknown UFRxDoc type %02X!" %(t))
		settings[t] = v
	return settings, i

def readListUID(data, offset, log, txt):
	uids   = []
	cnt, i = getUInt32(data, offset)
	log.write(u"%s: count=%d\n" %(txt, cnt))
	for j in range(cnt):
		u, i = getUUID(data, i)
		log.write(u"  [%02X]: {%s}\n" %(j, u))
		uids.append(u)
	return uids, i

def readListEnv(data, offset, log, txt):
	lst = []
	cnt, i = getUInt32(data, offset)
	log.write(u"%s: count=%d\n" %(txt, cnt))
	for j in range(cnt):
		e = UfrxEnv()
		e.u, i = getUUID(data, i)
		e.a, i = getUInt32A(data, i, 2)
		e.n, i = getUInt16(data, i)
		e.b, i = getUInt8(data, i)
		e.t, i = getLen32Text16(data, i)
		lst.append(e)
		log.write(u"  [%02X]: %s\n" %(j, e))
	return lst, i

def readInLengthFactor(data, offset, log, txt):
	b, i = getBoolean(data, offset)
	if (b):
		t1, i = getLen32Text16(data, i)
		t2, i = getLen32Text16(data, i)
		t3, i = getLen32Text16(data, i)
		f1, i = getFloat64(data, i)
		n1, i = getUInt16(data, i)
		log.write(u"%s:\t'%s' '%s' '%s', %g, %04X\n" %(txt, t1, t2, t3, f1, n1))
		return (t1, t2, t3, f1, n1), i
	log.write(u"%s:\tNULL\n" %(txt))
	return None, i

def readListTxtStrUid(data, offset, log, txt):
	lst    = []
	cnt, i = getUInt32(data, offset)
	log.write(u"%s: count=%d\n" %(txt, cnt))
	for j in range(cnt):
		o = UfrxTSU()
		o.s, i  = getLen32Text8(data, i)
		o.t, i  = getLen32Text16(data, i)
		o.u, i  = getUUID(data, i)
		if (schema >= 0x0B):
			o.m, i  = getUInt16(data, i)
		else:
			o.m, i  = getUInt8(data, i)
		o.a1, i = getUInt16A(data, i, 2)
		cntK, i = getUInt32(data, i)
		for k in range(cntK):
			t, i = getUInt8(data, i)
			if (t in [0x27]):
				v, i = getUInt32(data, i)
			elif (t in [0x10]):
				v, i = getUInt8(data, i)
			elif (t in [0x13]):
				v = None
			elif (t in [0x11, 0x22, 0x29]):
				v, i = getUUID(data, i)
			elif (t in [0x16, 0x17, 0x18, 0x1F, 0x24, 0x25, 0x2A]):
				u1, i  = getUUID(data, i)
				u2, i  = getUUID(data, i)
				v = [u1, u2]
			else:
				raise ValueError(u"Unknown type %02X for array element in arr9!" %(t))
			o.p[t] = v
		o.a2, i  = getUInt16A(data, i, 2)
		b, i = getBoolean(data, i)
		if (b):
			o.v1, i = readBBLTvLNew(data, i)
			o.v2, i = readBBLTvLNew(data, i)
		if (schema >= 0x0C):
			o.n, i = getUInt8(data, i)
		log.write(u"  [%02X]: %s\n" %(j, o))
		logWriteBBLTVLst(log, 'bbltvl1', o.v1)
		logWriteBBLTVLst(log, 'bbltvl2', o.v2)
		keys = o.p.keys()
		if (sys.version_info.major < 3):
			keys.sort()
		else:
			keys = sorted(keys)
		for t in keys:
			log.write(u"    [%02X]: " %(t))
			if (t in [0x27]):
				log.write(u"%04X\n" %(o.p[t]))
			elif (t in [0x10]):
				log.write(u"%02X\n" %(o.p[t]))
			elif (t in [0x13]):
				log.write(u"\n")
			elif (t in [0x11, 0x22, 0x29]):
				log.write(u"{%s}\n" %(o.p[t]))
			elif (t in [0x16, 0x17, 0x18, 0x1F, 0x24, 0x25, 0x2A]):
				v = o.p[t]
				log.write(u"{%s},{%s}\n" %(v[0], v[1]))
		lst.append(o)
	return lst, i

def read(data):
	global schema

	dumpFolder = getDumpFolder()
	if (not (dumpFolder is None)):
		ufrx = UFRxDocument()
		with io.open(u"%s/UFRxDoc.log" %(dumpFolder), 'w', encoding='utf8') as log:
			try:
				ufrx.schema, i  = readUInt16(data,   0, log, 'schema')
				schema = ufrx.schema
				cnt, i           = getUInt16(data,    i)
				ufrx.arr1, i     = readUInt16A(data,  i, log, 'arr1', cnt)
				ufrx.arr2, i     = readUInt16A(data,  i, log, 'arr2', 4)
				ufrx.dat1, i     = readDateTime(data, i, log, 'dat1')
				ufrx.arr3, i     = readUInt16A(data,  i, log, 'arr3', 4)
				ufrx.dat2, i     = readDateTime(data, i, log, 'dat2')
				ufrx.comment, i  = readText16(data,   i, log, 'comm')
				ufrx.arr4, i     = readUInt16A(data,  i, log, 'arr4', 12)
				ufrx.dat3, i     = readDateTime(data, i, log, 'dat3') # creation date of version 1
				ufrx.revision, i = readUID(data,      i, log, 'revision')
				ufrx.flags, i    = readUInt32(data,   i, log, 'flags')
				ufrx.uid2, i     = readUID(data,      i, log, 'uid2')
				ufrx.fName, i    = readText16(data,   i, log, 'fName')
				ufrx.n0, i       = readUInt16(data,   i, log, 'n0')
				cnt, i = getUInt32(data, i)
				log.write(u"arr5: count=%d\n" %(cnt))
				for j in range(cnt):
					n1, i = getUInt16(data, i)
					n2, i = getUInt16(data, i)
					t, i = getLen32Text16(data, i)
					n3, i = getUInt8(data, i)
					n4, i = getUInt8(data, i)
					ufrx.arr5.append((n1, n2, t, n3, n4))
					log.write(u"  [%02X]: %03X,%03X,'%s',%02X,%02X\n" %(j, n1, n2, t, n3, n4))
				ufrx.exports, i = readExports(data,  i, log, 'exports')
				ufrx.n1, i      = readUInt32(data,   i, log, 'n1')

				if (ufrx.schema >= 0x0B): ufrx.txt1, i = getLen32Text16(data, i)
				log.write(u"txt1:\t'%s'\n" %(ufrx.txt1))

				ufrx.arr6, i    = readUInt16A(data,  i, log, 'arr6', 10)

				if (ufrx.schema >= 0x0C):
					ufrx.n2, i   = getUInt16(data, i)
					ufrx.uid3, i = getUUID(data, i)
					ufrx.uid4, i = getUUID(data, i)
				log.write(u"n2:\t%04X\n" %(ufrx.n2))
				log.write(u"uid3:\t{%s}\n" %(ufrx.uid3))
				log.write(u"uid4:\t{%s}\n" %(ufrx.uid4))

				ufrx.n3, i = readUInt16(data, i, log, 'n3')

				ufrx.iamRefs, i = readIamRefs(data, i, log, 'iamRefs')
				ufrx.iptRefs, i = readIptRefs(data, i, log, 'iptRefs')
				ufrx.b1,      i = readBoolean(data,  i, log, 'b1')

				if (ufrx.schema >= 0x0C):
					a, i = getUInt16(data, i)
				else:
					a, i = getUInt8(data, i)
				assert a == 0, u"a = %X" %(a)
				ufrx.n4, i       = readUInt16(data,   i, log, 'n4')
				ufrx.fileRefs, i = readFileRefs(data, i, log, 'fRefs')
				if (ufrx.schema >= 0x0C):
					a, i = getUInt8(data, i)
					assert a == 0, u"a = %X" %(a)

				ufrx.lst1, i     = readL7BHLst1(data, i, log, 'lst1')
				ufrx.lst2, i     = readTxt2I(data,    i, log, 'lst2')
				ufrx.n5, i       = readUInt32(data,   i, log, 'n5')
				ufrx.settings, i = readSettings(data, i, log, 'settings')
				ufrx.n6, i       = readUInt16(data,   i, log, 'n6')
				ufrx.uids, i     = readListUID(data,  i, log, 'uids')
				ufrx.envList, i  = readListEnv(data,  i, log, 'environments')

				if (ufrx.schema >= 0x0B):
					ufrx.n7, i = getUInt32(data, i)
					b, i = getUInt16(data, i)
					if (b == 1):
						ufrx.arr7, i = getUInt16A(data, i, 3)
				log.write(u"n7:\t%04X\n" %(ufrx.n7))
				log.write(u"arr7:\t[%s]\n" %(FloatArr2Str(ufrx.arr7)))

				ufrx.n8, i   = readUInt8(data,          i, log, 'n8')
				ufrx.obj1, i = readInLengthFactor(data, i, log, 'obj1')
				ufrx.n9, i   = readUInt16(data,         i, log, 'n9')

				if (ufrx.schema >= 0x0C): ufrx.n10, i = getUInt16(data, i)
				log.write(u"n10:\t%04X\n" %(ufrx.n10))

				if (ufrx.schema >= 0x0B): ufrx.n11, i = getUInt16(data, i)
				log.write(u"n11:\t%03X\n" %(ufrx.n11))

				ufrx.lst3, i   = readListTxtStrUid(data, i, log, 'lst3')
				if (ufrx.n6 == 1):
					ufrx.posMin, i = readFloat32_3D(data,    i, log, 'min')
					ufrx.posMin, i = readFloat32_3D(data,    i, log, 'max')

				n, j = getUInt32(data, i)
				if (n > 2):
					cnt = n
					i = j
					# iMates:
					log.write(u"iMates: count=%d\n" %(cnt))
					for j in range(cnt):
						t, i = getBoolean(data, i)
						if (t):
							t1, i = getLen32Text16(data, i)
							t2, i = getLen32Text16(data, i)
							b, i  = getUInt8(data, i)
							u, i  = getUUID(data, i)
							a, i  = getUInt32A(data, i, 2)
							log.write(u"  [%02X]: %02X,'%s','%s',%02X,%s,[%s]\n" %(j, t, t1, t2, b, u, IntArr2Str(a, 4)))
							ufrx.iMates.append((t, (t1, t2, b, u, a)))
					if (len(ufrx.iMates) > 0):
						ufrx.iMate, i  = readText16(data, i, log, 'sel.') # selected iMate
				elif (n == 0):
					ufrx.arr8, i = readUInt32A(data, i, log, 'arr8', 2)

				ufrx.arr9, i  = readUInt16A(data, i, log, 'arr9', 4)

				if (ufrx.schema >= 0x0C): ufrx.n12, i = getUInt8(data, i)
				log.write(u"n12:\t%02X\n" %(ufrx.n12))
			except Exception as e:
				logError(traceback.format_exc())
				logError(str(e))

			if (i < len(data)):
				if (sys.version_info.major < 3):
					b = " ".join(["%02X" %(ord(c)) for c in data[i:]])
				else:
					b = " ".join(["%02X" %(c) for c in data[i:]])
				aX = re.sub(u"( [2-7][0-9a-fA-F] 00){2,}", u":''", b)
				log.write(u"aX=%02X,%04X: [%s]" %(ufrx.schema, ufrx.n4, aX))
		return ufrx
	return None