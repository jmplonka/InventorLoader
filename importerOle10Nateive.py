# -*- coding: utf-8 -*-

from importerUtils import getUInt16, getUInt32, getLen32Text8, getLen32Text16

def getText(data, offset):
	e = data.index('\x00', offset)
	return data[offset:e], e + 1

class olenative():
	def __init__(self):
		self.size        = 0
		self.header      = None
		self.label       = u''
		self.orgPath     = u''
		self.fmtId     = None
		self.dataPath    = u''
		self.dataLen     = 0
		self.data        = []
		self.orgPathW    = u''
		self.labelW      = u''
		self.defPathW    = u''

	def __repr__(self): return str(self.getDict())

	def getDict(self):
		"""populate temp dict that stores configurations"""
		return {
			"size":             self.size,
			"header":           self.header,
			"label":            self.label,
			"orgPath":          self.orgPath,
			"fmtId":            self.fmtId,
			"dataPath":         self.dataPath,
			"dataLen":          self.dataLen,
			"orgPathW":         self.orgPathW,
			"labelW":           self.labelW,
			"defPathW":         self.defPathW,
		}

	def read(self, data):
		""" parses olenative structure"""
		self.size, i        = getUInt32(data, 0)
		self.header, i      = getUInt16(data, i)# get flag1, typically a hardcoded value of 02 00
		self.label, i       = getText(data, i)
		self.orgPath, i     = getText(data, i)
		self.fmtId, i       = getUInt32(data, i) # 0x0300 => empedded, 0x0100 => linked
		self.dataPath, i    = getLen32Text8(data, i)
		self.dataLen, i     = getUInt32(data, i)
		self.data           = data[i:i+self.dataLen]
		i += self.dataLen
		if (len(data) - i > 12):
			self.orgPathW, i    = getLen32Text16(data, i) # command16
			self.labelW, i      = getLen32Text16(data, i) # label16
			self.defPathW, i    = getLen32Text16(data, i) # filePath16
