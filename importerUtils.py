#!/usr/bin/env python

"""
importerUtils.py:

Collection of functions necessary to read and analyse Autodesk (R) Invetor (R) files.
"""

from struct import unpack
from uuid import UUID
import sys
import datetime

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

# The dictionary of all found UUIDs and their origin
foundUids = {}

class LOG():
	LOG_DEBUG   = 1
	LOG_INFO    = 2
	LOG_WARNING = 4
	LOG_ERROR   = 8
	LOG_ALWAYS  = 16
	LOG_FILTER  = LOG_INFO | LOG_WARNING | LOG_ERROR

def getUInt8(data, offset):
	"""
	Returns a single unsingned 8-Bit value (byte).
	Args:
		data
			A binary string.
		offset
			The zero based offset of the byte.
	Returns:
		The unsigned 8-Bit value at offset.
		The new position in the 'stream'.
	"""
	end = offset + 1
	val = unpack('<B', data[offset:end])[0]
	return val, end

def getUInt8A(data, offset, size):
	"""
	Returns an array of unsingned 8-Bit values (bytes).
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
	"""
	end = offset + size
	val = unpack('<' +'B'*size, data[offset:end])
	return val, end

def getUInt16(data, offset):
	"""
	Returns a single unsingned 16-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the unsigned 16-Bit value.
	Returns:
		The unsigned 16-Bit value at offset.
		The new position in the 'stream'.
	"""
	end = offset + 2
	val = unpack('<H', data[offset:end])[0]
	return val, end

def getUInt16A(data, offset, size):
	"""
	Returns an array of unsingned 16-Bit values.
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
	"""
	end = offset + 2*size
	val = unpack('<' +'H'*size, data[offset:end])
	return val, end

def getSInt16(data, offset):
	"""
	Returns a single singned 16-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the signed 16-Bit value.
	Returns:
		The signed 16-Bit value at offset.
		The new position in the 'stream'.
	"""
	end = offset + 2
	val = unpack('<h', data[offset:end])[0]
	return val, end

def getUInt32(data, offset):
	"""
	Returns a single unsingned 32-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the unsigned 32-Bit value.
	Returns:
		The unsigned 32-Bit value at offset.
		The new position in the 'stream'.
	"""
	end = offset + 4
	val = unpack('<L', data[offset:end])[0]
	return val, end

def getUInt32A(data, offset, size):
	"""
	Returns an array of unsingned 32-Bit values.
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
	"""
	end = offset + 4 * size
	val = unpack('<' +'L'*size, data[offset:end])
	return val, end

def getSInt32(data, offset):
	"""
	Returns a single singned 32-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the singned 32-Bit value.
	Returns:
		The singned 32-Bit value at offset.
		The new position in the 'stream'.
	"""
	end = offset + 4
	val = unpack('<l', data[offset:end])[0]
	return val, end

def getFloat32(data, offset):
	"""
	Returns a single precision floating value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
	Returns:
		The single precision floating value at offset.
		The new position in the 'stream'.
	"""
	end = offset + 4
	val = unpack('<f', data[offset:end])[0]
	return val, end

def getFloat32A(data, offset, size):
	"""
	Returns an array of single precision floating values.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
		size
			The size of the array.
	Returns:
		The array of single precision floating values at offset.
		The new position in the 'stream'.
	"""
	end = offset + 4 * size
	val = unpack('<' + 'f'*size, data[offset:end])
	return val, end

# | ID                                   | Type | Name
# +--------------------------------------+------+----------------------------------------------------
# | B6B5DC40-96E3-11d2-B774-0060B0F159EF | CLS  | Inventor Application
# | C343ED84-A129-11d3-B799-0060B0F159EF | CLS  | Inventor Apprentice Server
# | 4D29B490-49B2-11D0-93C3-7E0706000000 | CLS  | Inventor Part
# | E60F81E1-49B3-11D0-93C3-7E0706000000 | CLS  | Inventor Assembly
# | BBF9FDF1-52DC-11D0-8C04-0800090BE8EC | CLS  | Inventor Drawing
# | 76283A80-50DD-11D3-A7E3-00C04F79D7BC | CLS  | Inventor Presentation
# | 28EC8354-9024-440F-A8A2-0E0E55D635B0 | CLS  | Inventor Weldment
# | 9C464203-9BAE-11D3-8BAD-0060B0CE6BB4 | CLS  | Inventor Sheet Metal Part
# | 92055419-B3FA-11D3-A479-00C04F6B9531 | CLS  | Inventor Generic Proxy Part
# | 9C464204-9BAE-11D3-8BAD-0060B0CE6BB4 | CLS  | Inventor Compatibility Proxy Part
# | 9C88D3AF-C3EB-11D3-B79E-0060B0F159EF | CLS  | Inventor Catalog Proxy Part
# | 4D8D80D4-F5B0-4460-8CEA-4CD222684469 | CLS  | Inventor Molded Part Document
# | 62FBB030-24C7-11D3-B78D-0060B0F159EF | CLS  | Inventor iFeature
# | 81B95C5D-8E31-4F65-9790-CCF6ECABD141 | CLS  | Inventor Design View
# | 1BACED46-C2CB-11d3-B79D-0060B0F159EF | I    | Inventor IRxPropVariantProperty
# | 9C88D3AE-C3EB-11d3-B79E-0060B0F159EF | I    | Inventor IRxPropVariantPropertySet
# | F29F85E0-4FF9-1068-AB91-08002B27B3D9 | FMT  | Microsoft Summary Information
# | D5CDD502-2E9C-101B-9397-08002B2CF9AE | FMT  | Microsoft Document Summary Information
# | D5CDD505-2E9C-101B-9397-08002B2CF9AE | FMT  | Microsoft User Defined Properties
# | 32853F0F-3444-11d1-9E93-0060B03C1CA6 | FMT  | Inventor Design Tracking Properties
# | B9600981-DEE8-4547-8D7C-E525B3A1727A | FMT  | Inventor Content Library Component Properties
# | F73AD5E7-C24C-44F0-B277-0F9A5AA3C35B | FMT  | Inventor Content Part Component Properties
# | E357129A-DB40-11d2-B783-0060B0F159EF | CAT  | Inventor Application AddIn Server protocol
# | 39AD2B5C-7A29-11D6-8E0A-0010B541CAA8 | CAT  | Inventor Versioned Application AddIn Server protocol
# | E357129B-DB40-11d2-B783-0060B0F159EF | CAT  | Inventor Application AddIn Site protocol
# | E7010077-425E-4ed3-8B28-A0CCED30927D | CAT  | Inventor Application AddIn Registration protocol
# | E956B1CC-1AA4-41c6-A40C-687B4A4AE0E9 | CAT  | Inventor Application AddIn Re-Registration protocol

def getUUID(data, offset, source):
	"""
	Returns a UUID.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the UUID.
	Returns:
		The UUID at offset.
		The new position in the 'stream'.
	"""
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
	"""
	Returns a timestamp (datetime).
	Args:
		data
			A binary string.
		offset
			The zero based offset of the timestamp.
	Returns:
		The timestamp at offset.
		The new position in the 'stream'.
	"""
	end = offset + 8
	val = unpack('<Q', data[offset:end])[0]
	if val != 0:
		return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=val/10.), end
	return None, end

def getLen32Text8(data, offset):
	len, i = getUInt32(data, offset)
	end = i + len
	txt = data[i: end].decode('UTF-8').encode('cp1252')
	if (txt[-1:] == '\0'):
		txt = txt[:-1]
	return txt, end

def getLen32Text16(data, offset):
	len, i = getUInt32(data, offset)
	end = i + 2 * len
	txt = data[i: end].decode('UTF-16LE').encode('cp1252')
	if (txt[-1:] == '\0'):
		txt = txt[:-1]
	return txt, end

# IFF: IF Function
def IFF(expression, valueTrue, valueFalse):
	if expression:
		return valueTrue
	else:
		return valueFalse

def IntArr2Str(arr, width):
	fmt = '%0{0}X'.format(width)
	return (','.join([fmt % (h) for h in arr]))

def PrintableName(fname):
	return repr('/'.join(fname))

def StdoutWriteChunked(data):
	while (len(data)>0):
		logMessage(data[0:10000])
		data = data[10000:]
	return

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

def logError(msg):
	print >> sys.stderr, msg
	sys.stderr.flush()

def logMessage(msg, level=LOG.LOG_DEBUG):
	if (level == LOG.LOG_ERROR):
		logError(msg)
	if (level != LOG.LOG_ALWAYS):
		if ((level & LOG.LOG_FILTER) == 0):
			return
	if ((level == LOG.LOG_WARNING) or (level == LOG.LOG_ERROR)):
		print >> sys.stderr, msg
		sys.stderr.flush()
	else:
		print >> sys.stdout, msg
		sys.stdout.flush()
