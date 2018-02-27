# -*- coding: utf8 -*-

'''
importerUtils.py:

Collection of functions necessary to read and analyse Autodesk (R) Invetor (R) files.
'''

import sys
import datetime
import FreeCAD
from uuid    import UUID
from struct  import pack, unpack
from math    import fabs

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.6.0'
__status__      = 'In-Development'

_dumpLineLength = 0x20
_fileVersion    = None
_can_import     = True

# The file the be imported
_inventor_file = None

# The dictionary of all found UUIDs and their origin
foundUids = {}

def setCanImport(canImport):
	global _can_import
	_can_import = canImport
	return

def canImport():
	global _can_import
	return _can_import

class LOG():
	LOG_DEBUG   = 1
	LOG_INFO    = 2
	LOG_WARNING = 4
	LOG_ERROR   = 8
	LOG_ALWAYS  = 16
	LOG_FILTER  = LOG_INFO | LOG_WARNING | LOG_ERROR

def getUInt8(data, offset):
	'''
	Returns a single unsigned 8-Bit value (byte).
	Args:
		data
			A binary string.
		offset
			The zero based offset of the byte.
	Returns:
		The unsigned 8-Bit value at offset.
		The new position in the 'stream'.
	'''
	end = offset + 1
	assert end <= len(data), "Trying to read UInt8 beyond data end (%X > %X)" %(end, len(data))
	val = unpack('<B', data[offset:end])[0]
	return val, end

def getUInt8A(data, offset, size):
	'''
	Returns an array of unsigned 8-Bit values (bytes).
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
		size
			The size of the array.
	Returns:
		The array of unsigned 8-Bit values at offset.
		The new position in the 'stream'.
	'''
	end = offset + size
	assert end <= len(data), "Trying to read UInt8 array beyond data end (%d, %X > %X)" %(size, end, len(data))
	val = unpack('<' +'B'*size, data[offset:end])
	val = list(val)
	return val, end

def getUInt16(data, offset):
	'''
	Returns a single unsigned 16-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the unsigned 16-Bit value.
	Returns:
		The unsigned 16-Bit value at offset.
		The new position in the 'stream'.
	'''
	end = offset + 2
	assert end <= len(data), "Trying to read UInt16 beyond data end (%X > %X)" %(end, len(data))
	val = unpack('<H', data[offset:end])[0]
	return val, end

def getUInt16A(data, offset, size):
	'''
	Returns an array of unsigned 16-Bit values.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
		size
			The size of the array.
	Returns:
		The array of unsigned 16-Bit values at offset.
		The new position in the 'stream'.
	'''
	end = offset + 2*size
	assert end <= len(data), "Trying to read UInt16 array beyond data end (%d, %X > %X)" %(size, end, len(data))
	val = unpack('<' +'H'*size, data[offset:end])

	val = list(val)
	return val, end

def getSInt16(data, offset):
	'''
	Returns a single singned 16-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the signed 16-Bit value.
	Returns:
		The signed 16-Bit value at offset.
		The new position in the 'stream'.
	'''
	end = offset + 2
	assert end <= len(data), "Trying to read SInt16 beyond data end (%X > %X)" %(end, len(data))
	val = unpack('<h', data[offset:end])[0]
	return val, end

def getSInt16A(data, offset, size):
	'''
	Returns an array of single singned 16-Bit values.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the signed 16-Bit value.
		size
			The size of the array.
	Returns:
		The array of unsigned 32-Bit values at offset.
		The new position in the 'stream'.
	'''
	end = offset + 2 * size
	assert end <= len(data), "Trying to read SInt16 array beyond data end (%d, %X > %X)" %(size, end, len(data))
	val = unpack('<' +'h'*size, data[offset:end])
	val = list(val)
	return val, end

def getUInt32(data, offset):
	'''
	Returns a single unsigned 32-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the unsigned 32-Bit value.
	Returns:
		The unsigned 32-Bit value at offset.
		The new position in the 'stream'.
	'''
	end = offset + 4
	assert end <= len(data), "Trying to read UInt32 beyond data end (%X > %X)" %(end, len(data))
	val = unpack('<L', data[offset:end])[0]
	return val, end

def getUInt32A(data, offset, size):
	'''
	Returns an array of unsigned 32-Bit values.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
		size
			The size of the array.
	Returns:
		The array of unsigned 32-Bit values at offset.
		The new position in the 'stream'.
	'''
	end = offset + 4 * size
	assert end <= len(data), "Trying to read UInt32 array beyond data end (%d, %X > %X)" %(size, end, len(data))
	val = unpack('<' +'L'*size, data[offset:end])
	val = list(val)
	return val, end

def getSInt32(data, offset):
	'''
	Returns a single singned 32-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the singned 32-Bit value.
	Returns:
		The singned 32-Bit value at offset.
		The new position in the 'stream'.
	'''
	end = offset + 4
	assert end <= len(data), "Trying to read SInt32 beyond data end (%X > %X)" %(end, len(data))
	val = unpack('<l', data[offset:end])[0]
	return val, end

def getSInt32A(data, offset, size):
	'''
	Returns an array of singned 32-Bit values.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
		size
			The size of the array.
	Returns:
		The array of signed 32-Bit values at offset.
		The new position in the 'stream'.
	'''
	end = offset + 4 * size
	assert end <= len(data), "Trying to read SInt32 array beyond data end (%d, %X > %X)" %(size, end, len(data))
	val = unpack('<' +'l'*size, data[offset:end])
	val = list(val)
	return val, end

def getFloat32(data, offset):
	'''
	Returns a double precision float value from a single one.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
	Returns:
		The double precision float value at offset from a single one.
		The new position in the 'stream'.
	'''
	end = offset + 4
	assert end <= len(data), "Trying to read Float32 beyond data end (%X > %X)" %(end, len(data))
	val = unpack('<f', data[offset:end])[0]
	val = unpack('d', pack('d',  val))[0]
	return val, end

def getFloat32A(data, offset, size):
	'''
	Returns an array of double precision float values from a list of single ones.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
		size
			The size of the array.
	Returns:
		The array of double precision float values from a list of single ones at offset.
		The new position in the 'stream'.
	'''
	end = offset + 4 * size
	assert end <= len(data), "Trying to read Float32 array beyond data end (%d, %X > %X)" %(size, end, len(data))
	singles = unpack('<' + 'f'*size, data[offset:end])
	val = []
	for s in singles:
		val += unpack('d', pack('d',  s))
	return val, end

def getFloat64(data, offset):
	'''
	Returns a double precision float value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
	Returns:
		The double precision float value at offset.
		The new position in the 'stream'.
	'''
	end = offset + 8
	assert end <= len(data), "Trying to read Float64 beyond data end (%X > %X)" %(end, len(data))
	val = unpack('<d', data[offset:end])[0]
	return val, end

def getFloat64A(data, offset, size):
	'''
	Returns an array of double precision float values.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
		size
			The size of the array.
	Returns:
		The array of double precision float values at offset.
		The new position in the 'stream'.
	'''
	end = offset + 8 * size
	assert end <= len(data), "Trying to read Float64 array beyond data end (%d, %X > %X)" %(size, end, len(data))
	val = unpack('<' + 'd'*size, data[offset:end])
	val = list(val)
	return val, end

def getColorRGBA(data, offset):
	i = offset
	r, i = getFloat32(data, i)
	g, i = getFloat32(data, i)
	b, i = getFloat32(data, i)
	a, i = getFloat32(data, i)
	c = Color(r, g, b, a)
	return c, i

def getUUID(data, offset, source):
	'''
	Returns a UUID.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the UUID.
	Returns:
		The UUID at offset.
		The new position in the 'stream'.
	'''
	global foundUids

	end = offset + 16
	val = UUID(bytes_le=data[offset:end])

	if (val not in foundUids):
		list = []
		foundUids[val] = list
	else:
		list = foundUids[val]

	if (source not in list):
		list.append(source)

	return val, end

def getDateTime(data, offset):
	'''
	Returns a timestamp (datetime).
	Args:
		data
			A binary string.
		offset
			The zero based offset of the timestamp.
	Returns:
		The timestamp at offset.
		The new position in the 'stream'.
	'''
	end = offset + 8
	assert end <= len(data), "Trying to read DateTime beyond data end (%X > %X)" %(end, len(data))
	val = unpack('<Q', data[offset:end])[0]
	if val != 0:
		return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=val/10.), end
	return None, end

def getText8(data, offset, l):
	i = offset
	end = i + l
	txt = data[i: end].decode('UTF-8')

	if (txt[-1:] == '\0'):
		txt = txt[:-1]

	if (txt[-1:] == '\n'):
		txt = txt[:-1]

	return txt, end

def getLen8Text8(data, offset):
	l, i = getUInt8(data, offset)
	txt, i = getText8(data, i, l)
	return txt, i

def getLen32Text8(data, offset):
	l, i = getUInt32(data, offset)
	txt, i = getText8(data, i, l)
	return txt, i

def getLen32Text16(data, offset):
	l, i = getUInt32(data, offset)
	end = i + 2 * l
	txt = data[i: end].decode('UTF-16LE')
	if (txt[-1:] == '\0'):
		txt = txt[:-1]

	if (txt[-1:] == '\n'):
		txt = txt[:-1]
	return txt, end

def getText1(uid):
	b = uid.hex

	if (b == '90874d1611d0d1f80008cabc0663dc09'): return 'RDxPart'
	if (b == 'ce52df4211d0d2d00008ccbc0663dc09'): return 'RDxPlane'
	if (b == '8ef06c8911d1043c60007cb801f31bb0'): return 'RDxLine3'
	if (b == 'ce52df3e11d0d2d00008ccbc0663dc09'): return 'RDxPoint3'
	if (b == '90874d4711d0d1f80008cabc0663dc09'): return 'RDxBody'
	if (b == '90874d1111d0d1f80008cabc0663dc09'): return 'RDxPlanarSketch'
	if (b == 'ce52df3b11d0d2d00008ccbc0663dc09'): return 'RDxArc2'
	if (b == '74df96e011d1e069800066b1e13554c7'): return 'RDxDiameter2'

	if (b == 'ce52df3511d0d2d00008ccbc0663dc09'): return 'RDxPoint2'
	if (b == 'ce52df3a11d0d2d00008ccbc0663dc09'): return 'RDxLine2'

	if (b == '1105855811d295e360000cb38932edb0'): return 'RDxDistanceDimension2'
	if (b == '00acc00011d1e05f800066b1e13554c7'): return 'RDxHorizontalDistance2'
	if (b == '3683ff4011d1e05f800066b1e13554c7'): return 'RDxVerticalDistance2'
	if (b == '90874d9111d0d1f80008cabc0663dc09'): return 'RDxFeature'
	if (b == '2067324411d21dc560002aab01f31bb0'): return 'RDxRectangularPattern'
	if (b == 'fad9a9b511d2330560002cab01f31bb0'): return 'RDxMirrorPattern'
	if (b == '6759d86f11d27838600094b70b02ecb0'): return 'FWxRenderingStyle'
	if (b == 'f645595c11d51333100060a6bba647b5'): return 'MIxTransactablePartition'
	if (b == 'cc0f752111d18027e38619962259017a'): return 'RSeAcisEntityWrapper'
	if (b == '26287e9611d490bd1000e2962dba09b5'): return 'RDxDeselTableNode'
	if (b == '2d86fc2642dfe34030c08ab05ef9bfc5'): return 'RDxReferenceEdgeLoopId'
	if (b == '8f41fd2411d26eac00082aab32a3dc09'): return 'RDxStopNode'
	if (b == '2b24130911d272cc60007bb79b49ebb0'): return 'RDxBrowserFolder'
	if (b == '3c95b7ce11d13388000820a5b17adc09'): return 'NBxNotebook'
	if (b == 'd81cde4711d265f760005dbead9287b0'): return 'NBxEntry'

	if (b == '671bb70011d1e068800066b1e13554c7'): return 'RDxRadius2'
	if (b == '590d0a1011d1e6ca80006fb1e13554c7'): return 'RDxAngle2'

	if (b == '1fbb3c0111d2684da0009e9a3c3aa076'): return 'RDxString'

	# logError("\tWARNING - can't find name for type %s" %(b))

	return uid

def getText2(uid):
	b = uid.hex

	if (b == 'ca7163a111d0d3b20008bfbb21eddc09'): return 'UCxComponentNode'
	if (b == '14533d8211d1087100085ba406e5dc09'): return 'UCxWorkplaneNode'
	if (b == '2c7020f611d1b3c06000b1b801f31bb0'): return 'UCxWorkaxisNode'
	if (b == '2c7020f811d1b3c06000b1b801f31bb0'): return 'UCxWorkpointNode'
	if (b == '9a676a5011d45da66000e3b81269f1b0'): return 'PMxBodyNode'
	if (b == 'da58aa0e11d43cb1c000ae967a14684f'): return 'SCx3dSketchNode'
	if (b == '60fd184511d0d79d0008bfbb21eddc09'): return 'SCx2dSketchNode'
	if (b == 'a94779e011d438066000b1b7b035f1b0'): return 'PMxSingleFeatureOutline'
	if (b == 'a94779e111d438066000b1b7b035f1b0'): return 'PMxPatternOutline'
	if (b == '022ac1b511d20d356000f99ac5361ab0'): return 'PMxPartDrawAttr'
	if (b == 'af48560f11d48dc71000d58dc04a0ab5'): return 'PMxColorStylePrimAttr'
	if (b == '452121b611d514d6100061a6bba647b5'): return 'RDxModelerTxnMgr'
	if (b == '90874d4711d0d1f80008cabc0663dc09'): return 'RDxBody'
	if (b == 'b251bfc011d24761a0001580d694c7c9'): return 'PMxEntryManager'
	if (b == '21e870bb11d0d2d000d8ccbc0663dc09'): return 'BRxEntry'
	if (b == 'dbbad87b11d228b0600052bead9287b0'): return 'NBxItem'

	# logError("\tWARNING - can't find name for node %s" %(b))

	return uid

# IFF: IF Function
def IFF(expression, valueTrue, valueFalse):
	if expression:
		return valueTrue
	else:
		return valueFalse

def FloatArr2Str(arr):
	return (', '.join('%g' %(f) for f in arr))

def IntArr2Str(arr, width):
	fmt = '%0{0}X'.format(width)
	return (','.join([fmt %(h) for h in arr]))

def Int2DArr2Str(arr, width):
	fmt = '%0{0}X'.format(width)
	return ','.join(['['+ ','.join([fmt %(h) for h in a])+']' for a in arr])

def PrintableName(fname):
	return repr('/'.join(fname))

def CombineHexAscii(hexDump, asciiDump):
	if hexDump == '':
		return ''
	return hexDump + '  ' + (' ' * (3 * (getDumpLineLength() - len(asciiDump)))) + asciiDump

def HexAsciiDump(data, offset = 0, doAscii = True):
	oDumpStream = CDumpStream()
	hexDump = ''
	asciiDump = ''
	dumplinelength = getDumpLineLength()

	for i, b in enumerate(data):
		if i % dumplinelength == 0:
			if hexDump != '':
				if (doAscii == True):
					oDumpStream.Addline(CombineHexAscii(hexDump, asciiDump))
				else:
					oDumpStream.Addline(hexDump)
			hexDump = '%04X:' % (i+offset)
			asciiDump = ''
		hexDump+= ' %02X' % ord(b)
		asciiDump += IFF(ord(b) >= 32 and ord(b), b, '.')
	if (doAscii == True):
		oDumpStream.Addline(CombineHexAscii(hexDump, asciiDump))
	else:
		oDumpStream.Addline(hexDump)
	return oDumpStream.Content()

def decode(filename, utf=False):
	if (isinstance(filename, unicode)):
		# workaround since ifcopenshell currently can't handle unicode filenames
		if (utf):
			encoding = "utf8"
		else:
			import sys
			encoding = sys.getfilesystemencoding()
		filename = filename.encode(encoding)
	return filename

def isEmbeddings(names):
	embedding = False
	for name in names:
		if (name == 'RSeEmbeddings'):
			embedding = True

	return embedding

def isEqual(a, b):
	if (a is None): return isEqual(b, 0)
	if (b is None): return isEqual(a, 0)
	return (fabs(a - b) < 0.0001)

def logWarning(msg):
	logMessage(msg, LOG.LOG_WARNING)
	return

def logError(msg):
	logMessage(msg, LOG.LOG_ERROR)
	return

def logMessage(msg, level=LOG.LOG_DEBUG):
	if (level != LOG.LOG_ALWAYS):
		if ((level & LOG.LOG_FILTER) == 0):
			return
	if (level == LOG.LOG_WARNING):
		FreeCAD.Console.PrintWarning(msg + '\n')
	elif (level == LOG.LOG_ERROR):
		FreeCAD.Console.PrintError(msg + '\n')
	else:
		FreeCAD.Console.PrintMessage(msg + '\n')

def getDumpLineLength():
	global _dumpLineLength
	return _dumpLineLength

def setDumpLineLength(length):
	global _dumpLineLength
	_dumpLineLength = length

def getFileVersion():
	global _fileVersion
	return _fileVersion

def getProperty(ole, path, key):
	p = ole.getproperties([path], convert_time=True)
	if (p is not None):
		if (key in p):
			v = p[key]
			return v
	return None

def setFileVersion(ole):
	global _fileVersion

	v = None
	b = getProperty(ole, '\x05Qz4dgm1gRjudbpksAayal4qdGf', 0x16)

	if (b is not None):
		if ((b // 100000) == 1402):
			_fileVersion = 2010
		else:
			_fileVersion = 2009
	else:
		b = 0
		_fileVersion = 2008

	v = getProperty(ole, '\x05PypkizqiUjudbposAayal4qdGf', 0x43)
	if (v is not None):
		v = v[0:v.index(' ')]
		_fileVersion = int(float(v))

	logMessage('Autodesk Inventor %s (Build %d) file' %(_fileVersion, b), LOG.LOG_ALWAYS)

def getInventorFile():
	global _inventor_file
	return _inventor_file

def setInventorFile(file):
	global _inventor_file
	_inventor_file = file

def translate(str):
	res = str.replace(u'Ä', 'Ae')
	res = res.replace(u'ä', 'ae')
	res = res.replace(u'Ö', 'Oe')
	res = res.replace(u'ö', 'oe')
	res = res.replace(u'Ü', 'Ue')
	res = res.replace(u'ü', 'ue')
	res = res.replace(u'ß', 'ss')
	return res

class CDumpStream():
	def __init__(self):
		self.text = ''

	def Addline(self, line):
		if line != '':
			self.text += line + '\n'

	def Content(self):
		return self.text

class Color():
	def __init__(self, red, green, blue, alpha):
		self.red   = red
		self.green = green
		self.blue  = blue
		self.alpha = alpha

	def __str__(self): # return unicode
		r = int(self.red   * 0xFF)
		g = int(self.green * 0xFF)
		b = int(self.blue  * 0xFF)
		a = int(self.alpha * 0xFF)
		return u'#%02X%02X%02X%02X' %(a, r, g, b)
