# -*- coding: utf-8 -*-

'''
importerUtils.py:
Collection of functions necessary to read and analyse Autodesk (R) Invetor (R) files.
'''

import os, sys, datetime, FreeCAD, FreeCADGui, numpy, json
from PySide.QtCore import *
from PySide.QtGui  import *
from uuid          import UUID
from struct        import Struct, unpack_from, pack
from FreeCAD       import Vector as VEC, Console, GuiUp, ParamGet

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

UUID_NAMES = {
	'21e870bb11d0d2d000d8ccbc0663dc09': 'BRxEntry',
	'6759d86f11d27838600094b70b02ecb0': 'FWxRenderingStyle',
	'f645595c11d51333100060a6bba647b5': 'MIxTransactablePartition',
	'd81cde4711d265f760005dbead9287b0': 'NBxEntry',
	'dbbad87b11d228b0600052bead9287b0': 'NBxItem',
	'3c95b7ce11d13388000820a5b17adc09': 'NBxNotebook',
	'9a676a5011d45da66000e3b81269f1b0': 'PMxBodyNode',
	'af48560f11d48dc71000d58dc04a0ab5': 'PMxColorStylePrimAttr',
	'b251bfc011d24761a0001580d694c7c9': 'PMxEntryManager',
	'022ac1b511d20d356000f99ac5361ab0': 'PMxPartDrawAttr',
	'a94779e111d438066000b1b7b035f1b0': 'PMxPatternOutline',
	'a94779e011d438066000b1b7b035f1b0': 'PMxSingleFeatureOutline',
	'590d0a1011d1e6ca80006fb1e13554c7': 'RDxAngle2',
	'ce52df3b11d0d2d00008ccbc0663dc09': 'RDxArc2',
	'90874d4711d0d1f80008cabc0663dc09': 'RDxBody',
	'2b24130911d272cc60007bb79b49ebb0': 'RDxBrowserFolder',
	'26287e9611d490bd1000e2962dba09b5': 'RDxDeselTableNode',
	'74df96e011d1e069800066b1e13554c7': 'RDxDiameter2',
	'1105855811d295e360000cb38932edb0': 'RDxDistanceDimension2',
	'90874d9111d0d1f80008cabc0663dc09': 'RDxFeature',
	'00acc00011d1e05f800066b1e13554c7': 'RDxHorizontalDistance2',
	'ce52df3a11d0d2d00008ccbc0663dc09': 'RDxLine2',
	'8ef06c8911d1043c60007cb801f31bb0': 'RDxLine3',
	'fad9a9b511d2330560002cab01f31bb0': 'RDxMirrorPattern',
	'452121b611d514d6100061a6bba647b5': 'RDxModelerTxnMgr',
	'90874d1611d0d1f80008cabc0663dc09': 'RDxPart',
	'90874d1111d0d1f80008cabc0663dc09': 'RDxPlanarSketch',
	'ce52df4211d0d2d00008ccbc0663dc09': 'RDxPlane',
	'ce52df3511d0d2d00008ccbc0663dc09': 'RDxPoint2',
	'ce52df3e11d0d2d00008ccbc0663dc09': 'RDxPoint3',
	'671bb70011d1e068800066b1e13554c7': 'RDxRadius2',
	'2067324411d21dc560002aab01f31bb0': 'RDxRectangularPattern',
	'2d86fc2642dfe34030c08ab05ef9bfc5': 'RDxReferenceEdgeLoopId',
	'8f41fd2411d26eac00082aab32a3dc09': 'RDxStopNode',
	'1fbb3c0111d2684da0009e9a3c3aa076': 'RDxString',
	'3683ff4011d1e05f800066b1e13554c7': 'RDxVerticalDistance2',
	'cc0f752111d18027e38619962259017a': 'RSeAcisEntityWrapper',
	'60fd184511d0d79d0008bfbb21eddc09': 'SCx2dSketchNode',
	'da58aa0e11d43cb1c000ae967a14684f': 'SCx3dSketchNode',
	'ca7163a111d0d3b20008bfbb21eddc09': 'UCxComponentNode',
	'2c7020f611d1b3c06000b1b801f31bb0': 'UCxWorkaxisNode',
	'14533d8211d1087100085ba406e5dc09': 'UCxWorkplaneNode',
	'2c7020f811d1b3c06000b1b801f31bb0': 'UCxWorkpointNode',
}
ENCODING_FS      = 'utf8'

_dumpLineLength  = 0x20
_fileVersion     = None
_can_import      = True
_use_sheet_metal = True

# The file the be imported
_inventor_file = None

# The dictionary of all found UUIDs and their origin
foundUids = {}

STRATEGY_SAT    = 0
STRATEGY_NATIVE = 1
STRATEGY_STEP   = 2

_author = ''
_description = None
_colorDefault = None

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"colors.json")) as colorPalette:
	_colorNames = json.load(colorPalette)
	for n in _colorNames:
		if (not n.startswith('_')):
			rgb =  _colorNames[n]
			r   = int(rgb[1:3], 0x10) / 255.0
			g   = int(rgb[3:5], 0x10) / 255.0
			b   = int(rgb[5:7], 0x10) / 255.0
			_colorNames[n] = (r, g, b)

def setColorDefault(r, g, b):
	global _colorDefault
	_colorDefault = (r, g, b)

def getColorDefault():
	global _colorDefault
	return _colorDefault

def getColor(name):
	global _colorNames, _colorDefault

	return _colorNames.get(name, _colorDefault)

def setColor(name, r, g, b):
	global _colorNames
	oldColorDef = _colorNames.get(name, None)
	sNew = "#%02X%02X%02X" % (r*255.0, g*255.0, b*255.0)
	if (oldColorDef is None):
		logWarning(u"Found new color '%s': %s - please add to colors.json!" %(name, sNew))
	else:
		sOld = "#%02X%02X%02X" % (oldColorDef[0]*255.0, oldColorDef[1]*255.0, oldColorDef[2]*255.0)
		if (sOld == sNew):
			return
		logWarning(u"Overwriting color '%s': %s with new definition %s!" %(name, sOld, sNew))
	_colorNames[name] = (r, g, b)

def getStrategy():
	if getFileVersion() < 2010: return STRATEGY_SAT
	return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/InventorLoader").GetInt("strategy", STRATEGY_SAT)

def isStrategySat():
	return getStrategy() == STRATEGY_SAT

def isStrategyStep():
	return getStrategy() == STRATEGY_STEP

def isStrategyNative():
	return getStrategy() == STRATEGY_NATIVE

def setAuthor(author):
	global _author
	_author = author
	return

def getAuthor():
	return _author

def setDescription(description):
	global _description
	_description = description
	return

def getDescription():
	return _description

def chooseImportStrategyAcis():
	btnCnvrt = QPushButton('&Convert to STEP')
	btnNativ = btnDefault = QPushButton('&nativ')
	msgBox   = QMessageBox()
	msgBox.setIcon(QMessageBox.Question)
	msgBox.setWindowTitle('FreeCAD - import Autodesk-File. choose strategy')
	msgBox.setText('Import Autodesk-File based:\n* on ACIS data (SAT), or base \n* on feature model (nativ)?')
	msgBox.addButton(btnCnvrt, QMessageBox.ActionRole)
	msgBox.addButton(btnNativ, QMessageBox.NoRole)
	param = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/InventorLoader")

	btnDefault = btnCnvrt if (param.GetInt("strategy") == STRATEGY_STEP) else btnNativ
	msgBox.setDefaultButton(btnDefault)

	result = msgBox.exec_()

	resultMapping = {0:STRATEGY_STEP, 1: STRATEGY_SAT}
	strategy = resultMapping[result]
	param.SetInt("strategy", strategy)
	return strategy

def chooseImportStrategy():
	btnCnvrt = QPushButton('&Convert to STEP')
	btnSat   = QPushButton('&SAT')
	btnNativ = QPushButton('&nativ')
	msgBox   = QMessageBox()
	thmnl    = getThumbnailImage()
	msgBox.setIcon(QMessageBox.Question)
	if (thmnl is not None):
		icon = thmnl.getIcon()
		if (icon):
			msgBox.setIconPixmap(icon)
	msgBox.setWindowTitle('FreeCAD - import Autodesk-File. choose strategy')
	msgBox.setText('Import Autodesk-File based:\n* on ACIS data (SAT), or base \n* on feature model (nativ)?')
	msgBox.addButton(btnCnvrt, QMessageBox.ActionRole)
	msgBox.addButton(btnSat, QMessageBox.YesRole)
	msgBox.addButton(btnNativ, QMessageBox.NoRole)
	param = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/InventorLoader")

	btnMapping = {STRATEGY_SAT: btnSat, STRATEGY_NATIVE: btnNativ, STRATEGY_STEP: btnCnvrt}
	msgBox.setDefaultButton(btnMapping[param.GetInt("strategy")])

	result = msgBox.exec_()

	resultMapping = {0:STRATEGY_STEP, 1: STRATEGY_SAT, 2:STRATEGY_NATIVE}
	strategy = resultMapping[result]
	param.SetInt("strategy", strategy)
	return strategy

def setCanImport(canImport):
	global _can_import
	_can_import = canImport
	return

def canImport():
	global _can_import
	return _can_import

def setUseSheetMetal(sheetMetal):
	global _use_sheet_metal
	_use_sheet_metal = sheetMetal
	return

def useSheetMetal():
	global _use_sheet_metal
	return _use_sheet_metal

class Thumbnail(object):
	def __init__(self, data):
		self.setData(data)
	def getData(self):
		return self._data
	def setData(self, data):
		# skip thumbnail class header (-1, -1, 3, 0, bpp, width, height, 0)
		buffer = data[0x10:]
		self.width, i = getUInt16(data, 0x0A)
		self.height, i = getUInt16(data, i)

		if (buffer[0x1:0x4] == 'PNG'):
			self.type = 'PNG'
			self.data_ = buffer
		else: # it's old BMP => rebuild header
			self.type = 'BMP'
			fmt, dummy = getUInt32(buffer, 0x12)
			if (fmt == 3):
				offset = 0x50
			elif (fmt == 5):
				offset = 0x4C
			else:
				raise AssertionError("Unknown thumbnail format %d" %(fmt))
			size, dummy = getUInt32(data, offset + 20)
			buffer = 'BM' + pack('LLL', size + 0x36, 0, 0x36)
			buffer += data[offset:]
		self._data = buffer
	def length(self):
		return len(self.data)
	def __str__(self):
		return '%s: %d x %d' % (self.type, self.width, self.height)
	def getIcon(self):
		icon = QPixmap()
		icon.loadFromData(QByteArray(self.getData()))
		return icon

_thumbnail = None
def writeThumbnail(data):
	global _thumbnail
	_thumbnail = Thumbnail(data)

	if (ParamGet("User parameter:BaseApp/Preferences/Mod/InventorLoader").GetBool('Others.DumpThumbnails', False)):
		filename = "%s/_.%s" %(getInventorFile()[0:-4], _thumbnail.type.lower())
		with open(filename, 'wb') as thumbnail:
			thumbnail.write(_thumbnail.getData())

	return _thumbnail

def getThumbnailImage():
	global _thumbnail
	return _thumbnail

def setThumbnail(ole):
	t = getProperty(ole, '\x05Zrxrt4arFafyu34gYa3l3ohgHg', 0x11)
	if (t is not None):
		writeThumbnail(t)

UINT8    = Struct('<B').unpack_from
UINT16   = Struct('<H').unpack_from
SINT16   = Struct('<h').unpack_from
UINT32   = Struct('<L').unpack_from
SINT32   = Struct('<l').unpack_from
FLOAT32  = Struct('<f').unpack_from
FLOAT64  = Struct('<d').unpack_from
RGBA     = Struct('<ffff').unpack_from
DATETIME = Struct('<Q').unpack_from

def getUInt8(data, offset):
	'''
	Returns a single unsingned 8-Bit value (byte).
	Args:
		data
			A binary string.
		offset
			The zero based offset of the byte.
	Returns:
		The unsigned 8-Bit value at offset.
		The new position in the 'stream'.
	'''
	val, = UINT8(data, offset)
	return val, offset + 1

def getUInt8A(data, offset, size):
	'''
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
	'''
	end = offset + size
	assert end <= len(data), "Trying to read UInt8 array beyond data end (%d, %X > %X)" %(size, end, len(data))
	val = unpack_from('<' +'B'*size, data, offset)
	val = list(val)
	return val, end

def getUInt16(data, offset):
	'''
	Returns a single unsingned 16-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the unsigned 16-Bit value.
	Returns:
		The unsigned 16-Bit value at offset.
		The new position in the 'stream'.
	'''
	val, = UINT16(data, offset)
	return val, offset + 2

def getUInt16A(data, offset, size):
	'''
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
	'''
	val = unpack_from('<' +'H'*size, data, offset)
	val = list(val)
	return val, offset + 2*size

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
	val, = SINT16(data, offset)
	return val, offset + 2

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
	val = unpack_from('<' +'h'*size, data, offset)
	val = list(val)
	return val, offset + 2 * size

def getUInt32(data, offset):
	'''
	Returns a single unsingned 32-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the unsigned 32-Bit value.
	Returns:
		The unsigned 32-Bit value at offset.
		The new position in the 'stream'.
	'''
	val, = UINT32(data, offset)
	return val, offset + 4

def getUInt32A(data, offset, size):
	'''
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
	'''
	val = unpack_from('<' +'L'*size, data, offset)
	val = list(val)
	return val, offset + 4 * size

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
	val, = SINT32(data, offset)
	return val, offset + 4

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
	val = unpack_from('<' + 'l'*size, data, offset)
	val = list(val)
	return val, offset + 4 * size

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
	val, = FLOAT32(data, offset)
	val = float(val)
	return val, offset + 4

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
	singles = unpack_from('<' + 'f'*size, data, offset)
	val = [float(s) for s in singles]
	return val, offset + 4 * size

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
	val, = FLOAT64(data, offset)
	return val, offset + 8

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
	val = unpack_from('<' + 'd'*size, data, offset)
	val = list(val)
	return val, offset + 8 * size

def getColorRGBA(data, offset):
	r, g, b, a = RGBA(data, offset)
	c = Color(r, g, b, a)
	return c, offset + 0x10

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
	val, = DATETIME(data, offset)
	if val != 0:
		return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=val/10.), offset + 8
	return None, offset + 8

def getText8(data, offset, l):
	i = offset
	end = i + l
	txt = data[i: end].decode(ENCODING_FS)

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

def getUidText(uid):
	b = uid.hex
	try:
		return UUID_NAMES[b]
	except:
		#logError(u"    Can't find name for type %s!", b)
		return uid

def FloatArr2Str(arr):
	return (', '.join(['%g' %(f) for f in arr]))

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
		asciiDump += b if (ord(b) >= 32 and ord(b)) else '.'
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
	return 'RSeEmbeddings' in names

def isEqual(a, b):
	if (a is None): return isEqual(b, VEC())
	if (b is None): return isEqual(a, VEC())
	return ((a - b).Length < 0.0001)

def isEqual1D(a, b):
	if (a is None): return isEqual1D(b, 0.0)
	if (b is None): return isEqual1D(a, 0.0)
	return abs(a - b) < 0.0001

def _log(caller, method, msg, args):
	try:
		if (len(args) > 0):
			method(msg %args + '\n')
		else:
			method(msg + '\n')
	except:
		Console.PrintError("FATAL ERROR in %s:\n" %(caller))
		Console.PrintError("msg   = " + msg)
		if (len(args) > 0): Console.PrintError("*args = (%s)" %(",".join(args)))

def logInfo(msg, *args):
	_log("logInfo", Console.PrintLog, msg, args)

def logWarning(msg, *args):
	_log("logWarning", Console.PrintWarning, msg, args)

def logError(msg, *args):
	_log("logError", Console.PrintError, msg, args)

def logAlways(msg, *args):
	_log("logAlways", Console.PrintMessage, msg, args)

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
	try:
		return p[key]
	except:
		return None

def setFileVersion(ole):
	global _fileVersion

	v = None
	b = getProperty(ole, '\x05Qz4dgm1gRjudbpksAayal4qdGf', 0x16)

	if (b is not None):
		if ((b // 10000000) == 14):
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
		if (_fileVersion == 134): # early version of 2010
			_fileVersion = 2010
	logInfo(u"Autodesk Inventor %s (Build %d) file" %(_fileVersion, b))

def getInventorFile():
	global _inventor_file
	return _inventor_file

def setInventorFile(file):
	global _inventor_file
	_inventor_file = file
	folder   = _inventor_file[0:-4]
	if (not os.path.exists(os.path.abspath(folder))):
		os.mkdir(folder)

def translate(str):
	res = str.replace(u'Ä', 'Ae')
	res = res.replace(u'ä', 'ae')
	res = res.replace(u'Ö', 'Oe')
	res = res.replace(u'ö', 'oe')
	res = res.replace(u'Ü', 'Ue')
	res = res.replace(u'ü', 'ue')
	res = res.replace(u'ß', 'ss')
	return res

def viewAxonometric():
	if (GuiUp):
		FreeCADGui.activeView().viewAxonometric()
		FreeCADGui.SendMsgToActiveView("ViewFit")
	logAlways(u"DONE!")

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
		return u'#%02X%02X%02X%02X' %(r, g, b, a)

	def __repr__(self):
		return self.__str__()
