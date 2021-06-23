# -*- coding: utf-8 -*-

'''
importerUtils.py:
Collection of functions necessary to read and analyse Autodesk (R) Invetor (R) files.
'''

import os, sys, datetime, FreeCADGui, json, shutil, re
from PySide.QtCore import *
from PySide.QtGui  import *
from struct        import Struct, unpack_from, pack
from FreeCAD       import Vector as VEC, Console, ParamGet
from olefile       import OleFileIO

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

UUID_NAMES = {
	'3c7f67aa4dd7848a040c58894ab06552': '_BodiesFolder',
	'328fc2ea44d13ec5f05abeb87d4aabca': '_ViewDirectionCollection',
	'8da49a2311d60c3210005aab87ae3483': 'AGxInstanceNode',
	'b91e695f11d52794100011ab87ae3483': 'AGxMultiBodyNode',
	'21e870bb11d0d2d000d8ccbc0663dc09': 'BRxEntry',
	'cb0adcaf11d50e7860009ba6c588fbb0': 'EExCollector',
	'6759d86f11d27838600094b70b02ecb0': 'FWxRenderingStyle',
	'a3ebe1984b705d656174d7969e5ae726': 'MBxBodyNode',
	'a03874b011d41238600018aa9dccefb0': 'MBxContourFlangeFeature',
	'c4c14b9011d328ff60004da99dccefb0': 'MBxFaceFeature',
	'c3dddc0811d397d06000a7a99dccefb0': 'MBxFlangeFeature',
	'10d6c06b46086923c73c0faca268550f': 'MBxSheetMetalRuleStyle',
	'c098d3cf11d5345310003697ab9f0ab5': 'MBRDxPunchToolFeature',
	'6045231311d30d7a6000ecb21d6eefb0': 'MBxUserSettingsAttribute',
	'cadd6468467ce6ee8e1494884110a2da': 'MIxBrepComponent',
	'f645595c11d51333100060a6bba647b5': 'MIxTransactablePartition',
	'd81cde4711d265f760005dbead9287b0': 'NBxEntry',
	'74e3441311d25aeb60005bbead9287b0': 'NBxFolder',
	'd8705bc711d15553000825a5b17adc09': 'NBxGraphicsArea',
	'dbbad87b11d228b0600052bead9287b0': 'NBxItem',
	'4c41596411d12e13000824a5fd7adc09': 'NBxNote',
	'3c95b7ce11d13388000820a5b17adc09': 'NBxNotebook',
	'9215a16211d19776600055bd861c3cb0': 'NBxNoteGlyphGroup',
	'fb96d24a11d18877600046bd861c3cb0': 'NBxNoteGlyphNode',
	'cc253bb711d15553000825a5b17adc09': 'NBxTextArea',
	'ccc5085a11d1aa4c0008c8ba32a3dc09': 'NMxFaceMergeData',
	'cce9204211d171c50008a7ba32a3dc09': 'NMxNameTable',
	'dd4c4d3a4fbbf55e16b785853b52d4dc': 'PMxASMFlatPatternPartRepresentation',
	'9a676a5011d45da66000e3b81269f1b0': 'PMxBodyNode',
	'af48560f11d48dc71000d58dc04a0ab5': 'PMxColorStylePrimAttr',
	'7dfc244811d461a01000c895bba647b5': 'PMxCompositeFeatureOutline',
	'b251bfc011d24761a0001580d694c7c9': 'PMxEntryManager',
	'c0014c894bd6a537fa9444be54ebc63d': 'PMxImage2D',
	'022ac1b511d20d356000f99ac5361ab0': 'PMxPartDrawAttr',
	'ca7163a311d0d3b20008bfbb21eddc09': 'PMxPartNode',
	'5e382456497725cff44fdeafccace65e': 'PMxPartRepresentation',
	'a94779e111d438066000b1b7b035f1b0': 'PMxPatternOutline',
	'a94779e011d438066000b1b7b035f1b0': 'PMxSingleFeatureOutline',
	'f7676ab011d23618a0001280d694c7c9': 'PMxSketchEntry',
	'590d0a1011d1e6ca80006fb1e13554c7': 'RDxAngle2',
	'bf3b5c8411d2e92a60004bb38932edb0': 'RDxAngle3Points2',
	'6d8a4ac711d4490f6000e6ab3a39fbb0': 'RDxAngleInterfaceDef',
	'ce52df3b11d0d2d00008ccbc0663dc09': 'RDxArc2',
	'bee90c4111d43c8280005a9a88fdf9c6': 'RDxAtomicInterfaceDef',
	'de818cc011d452d9c000ba967a14684f': 'RDxBendConstraint',
	'90874d4711d0d1f80008cabc0663dc09': 'RDxBody',
	'90874d4811d0d1f80008cabc0663dc09': 'RDxBodySet',
	'2b24130911d272cc60007bb79b49ebb0': 'RDxBrowserFolder',
	'9e43716a11d20fa5600084b7b035c3b0': 'RDxCircle3',
	'4ef32ef04cf83c27f0b185a66f245b22': 'RDxClientFeature',
	'90874d9411d0d1f80008cabc0663dc09': 'RDxCoincident2',
	'90874d5911d0d1f80008cabc0663dc09': 'RDxComponent',
	'81afc10f11d514051000569772d147b5': 'RDxCompositeInterfaceDef',
	'778752c64a5426253aab58b51014c910': 'RDxCurveToSurfaceProjection',
	'7f936baa4aef3859f4b80e8c548a4a11': 'RDxDecalFeature',
	'27ecb60f11d430c3c0001985e89c6b4f': 'RDxDerivedAssembly',
	'cd7c1c534dd0d3096a46e89e3ba9d923': 'RDxDerivedOccDataCollector',
	'bfb5eb9311d443e8c0001c85e89c6b4f': 'RDxDerivedOccFeature',
	'255d7ed711d3b5f2c0000385e89c6b4f': 'RDxDerivedPart',
	'26287e9611d490bd1000e2962dba09b5': 'RDxDeselTableNode',
	'89b87c6f11d2e0d26000f1b26c74fcb0': 'RDxDiagProfileInvalidLoop',
	'3683ce3311d2fcf16000fab26c74fcb0': 'RDxDiagSketchDimRefGeomFailed',
	'74df96e011d1e069800066b1e13554c7': 'RDxDiameter2',
	'1105855811d295e360000cb38932edb0': 'RDxDistanceDimension2',
	'10b6adef45f57b24911db28d8c498f80': 'RDxDistanceDimension3',
	'90874d5311d0d1f80008cabc0663dc09': 'RDxEdgeId',
	'9e43716b11d20fa5600084b7b035c3b0': 'RDxEllipse3',
	'4507d46011d1e6be80006fb1e13554c7': 'RDxEllipticArc2',
	'748fbd6411d1c41f6000b3b801f31bb0': 'RDxFaceSurfaceId',
	'90874d9111d0d1f80008cabc0663dc09': 'RDxFeature',
	'fd1f3f2111d449d88000679a88fdf9c6': 'RDxFlushInterfaceDef',
	'b71cbec94d8922eaa66f24ad3b81c470': 'RDxHelixConstraint3',
	'00acc00011d1e05f800066b1e13554c7': 'RDxHorizontalDistance2',
	'1b16984a11d28fce6000bdb72508ebb0': 'RDxHospital',
	'6d8a4ac911d4490f6000e6ab3a39fbb0': 'RDxInsertInterfaceDef',
	'dfb2586a11d60a0a10002fbd891e89b5': 'RDxIntersectionCurve',
	'ce52df3a11d0d2d00008ccbc0663dc09': 'RDxLine2',
	'8ef06c8911d1043c60007cb801f31bb0': 'RDxLine3',
	'a327786911d19690000826bd0663dc09': 'RDxLoop',
	'a789eeb011d1e6c080006fb1e13554c7': 'RDxMajorRadius2',
 	'375c698211d16b510008a1ba32a3dc09': 'RDxMatchedEdge',
	'b382a87c45f4ffb9fe4a7486104813a4': 'RDxMatchedLoop',
	'5523121311d4490d6000e6ab3a39fbb0': 'RDxMateInterfaceDef',
	'b4964e9011d1e6c080006fb1e13554c7': 'RDxMinorRadius2',
	'fad9a9b511d2330560002cab01f31bb0': 'RDxMirrorPattern',
	'452121b611d514d6100061a6bba647b5': 'RDxModelerTxnMgr',
	'3e55d947407dffd912db059ae9d0ed1f': 'RDxOffsetCurve2', # OffsetSpline2D
	'90874d1611d0d1f80008cabc0663dc09': 'RDxPart',
	'90874d1111d0d1f80008cabc0663dc09': 'RDxPlanarSketch',
	'ce52df4211d0d2d00008ccbc0663dc09': 'RDxPlane',
	'ce52df3511d0d2d00008ccbc0663dc09': 'RDxPoint2',
	'ce52df3e11d0d2d00008ccbc0663dc09': 'RDxPoint3',
	'0697713111d2323260002cab01f31bb0': 'RDxPolarPattern',
	'f9884c4311d1983d000826bd0663dc09': 'RDxProfile',
	'2d06cad349986fa71ead34b67e52cd7b': 'RDxProjectCutEdges',
	'671bb70011d1e068800066b1e13554c7': 'RDxRadius2',
	'90874d2611d0d1f80008cabc0663dc09': 'RDxReal',
	'2067324411d21dc560002aab01f31bb0': 'RDxRectangularPattern',
	'2d86fc2642dfe34030c08ab05ef9bfc5': 'RDxReferenceEdgeLoopId',
	'317b734611d37a7c60001cb3d1c1fbb0': 'RDxRefSpline',
	'0b86ad43421c4a69e0e0deaab16e7154': 'RDxRefSpline3',
	'3ae9d8da11d42c3ac000ad967a14684f': 'RDxSketch3d',
	'ffd270b811d52d1410000897994909b5': 'RDxSketchFragment',
	'f9372fd411d1d315000847b00524dc09': 'RDxSpline2',
	'7c44abde11d2257a60008cb7b035c3b0': 'RDxSpline3',
	'8f41fd2411d26eac00082aab32a3dc09': 'RDxStopNode',
	'1fbb3c0111d2684da0009e9a3c3aa076': 'RDxString',
	'9a94e34711d36b7fc000d49545df724f': 'RDxToolBodyCacheAttribute',
	'ce52df4011d0d2d00008ccbc0663dc09': 'RDxVector3',
	'3683ff4011d1e05f800066b1e13554c7': 'RDxVerticalDistance2',
	'ea7da98811d447a26000d0b81269f1b0': 'RSeAcisEntityContainer',
	'cc0f752111d18027e38619962259017a': 'RSeAcisEntityWrapper',
	'60fd184511d0d79d0008bfbb21eddc09': 'SCxSketchNode',
	'da58aa0e11d43cb1c000ae967a14684f': 'S3xSketch3dNode',
	'fd1e899d11d635491000568ec04a0ab5': 'SMxAnalysisSetup',
	'a529d1e211d0d0900008bcbb21eddc09': 'SMxGroupNode',
	'022ac1b111d20d356000f99ac5361ab0': 'SMxPersistentScenePath',
	'716b5cd148299bd2474ec788e5ab0c74': 'UCxATEntry',
	'd48240694eb51a34aec9d789df4f97a4': 'UCxClientFeatureNode',
	'dbe41d9111d4414c8000609a88fdf9c6': 'UCxCompInterfaceNode',
	'ca7163a111d0d3b20008bfbb21eddc09': 'UCxComponentNode',
	'd1071d574d61a7c4f2e352bf50116935': 'UCxConstraint3DimensionItem',
	'7dfcc81711d6419710006eab87ae3483': 'UCxConstructionFolderEntry',
	'475e786111d296dba0004a803603c8c9': 'UCxFeatureDimensionStateAttr',
	'2c7020f611d1b3c06000b1b801f31bb0': 'UCxWorkaxisNode',
	'14533d8211d1087100085ba406e5dc09': 'UCxWorkplaneNode',
	'2c7020f811d1b3c06000b1b801f31bb0': 'UCxWorkpointNode',
	'd31891c248bf14c3aa42ea872a846b2a': 'UFRxRef',
}

ENCODING_FS      = 'utf8'

_fileVersion = 0
_fileBeta        = -1
_can_import      = True
_use_sheet_metal = True
_block_size      = 0

__prmPrefOW__ = ParamGet("User parameter:BaseApp/Preferences/OutputWindow")
__prmPrefIL__ = ParamGet("User parameter:BaseApp/Preferences/Mod/InventorLoader")

# The file the be imported
_inventor_file = None
_dump_folder   = None

STRATEGY_SAT    = 0
STRATEGY_NATIVE = 1
STRATEGY_STEP   = 2
__strategy__ = __prmPrefIL__.GetInt("strategy", STRATEGY_SAT)

IS_CELL_REF = re.compile('^[a-z](\d+)?$', re.IGNORECASE)
IS_BETA     = re.compile('^.* Beta(\d+) .*$', re.IGNORECASE)
_author         = ''
_company        = ''
_comment        = ''
_lastModifiedBy = ''
_description    = ''
_colorDefault   = ''

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
	_colorNames[name] = (r, g, b)

def getStrategy():
	global __strategy__
	return __strategy__

def setStrategy(newStrategy):
	global __strategy__, __prmPrefIL__
	__strategy__ = newStrategy
	__prmPrefIL__.SetInt("strategy", newStrategy)

def isStrategySat():
	return getStrategy() == STRATEGY_SAT

def isStrategyStep():
	return getStrategy() == STRATEGY_STEP

def isStrategyNative():
	return getStrategy() == STRATEGY_NATIVE

def setAuthor(author):
	global _author
	if (author):
		_author = author
	else:
		_author = ''
	return

def getAuthor():
	return _author

def setCompany(company):
	global _company
	if (company):
		_company = company
	else:
		_company = ''
	return

def getCompany():
	global _company
	return _company

def setComment(comment):
	global _comment
	if (comment):
		_comment = comment
	else:
		_comment = ''
	return

def getComment():
	global _comment
	return _comment

def setLastModifiedBy(lastModifiedBy):
	global _lastModifiedBy
	if (lastModifiedBy):
		_lastModifiedBy = lastModifiedBy
	else:
		_lastModifiedBy = ''
	return

def getLastModifiedBy():
	global _lastModifiedBy
	return _lastModifiedBy

def setDescription(description):
	global _description
	if (description):
		_description = description
	else:
		_description = ''
	return

def getDescription():
	return _description

def chooseImportStrategyAcis():
	btnCnvrt = QPushButton('&Convert to STEP')
	btnNativ = btnDefault = QPushButton('&nativ')
	thmnl    = getThumbnail()
	msgBox   = QMessageBox()
	msgBox.setIcon(QMessageBox.Question)
	if (thmnl):
		icon = thmnl.getIcon()
		if (icon):
			msgBox.setIconPixmap(icon)
	msgBox.setWindowTitle('FreeCAD - import Autodesk-File. choose strategy')
	msgBox.setText('Import Autodesk-File based:\n* on ACIS data (SAT), or base \n* on feature model (nativ)?')
	msgBox.addButton(btnCnvrt, QMessageBox.ActionRole)
	msgBox.addButton(btnNativ, QMessageBox.NoRole)

	btnDefault = btnCnvrt if (getStrategy() == STRATEGY_STEP) else btnNativ
	msgBox.setDefaultButton(btnDefault)

	QApplication.setOverrideCursor(Qt.ArrowCursor)
	result = msgBox.exec_()
	QApplication.restoreOverrideCursor()

	resultMapping = {0:STRATEGY_STEP, 1: STRATEGY_SAT}
	strategy = resultMapping[result]
	setStrategy(strategy)
	return strategy

def chooseImportStrategy():
	btnCnvrt = QPushButton('&Convert to STEP')
	btnSat   = QPushButton('&SAT')
	btnNativ = QPushButton('&nativ')
	thmnl    = getThumbnail()
	msgBox   = QMessageBox()
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

	btnMapping = {STRATEGY_SAT: btnSat, STRATEGY_NATIVE: btnNativ, STRATEGY_STEP: btnCnvrt}
	msgBox.setDefaultButton(btnMapping[getStrategy()])

	QApplication.setOverrideCursor(Qt.ArrowCursor)
	result = msgBox.exec_()
	QApplication.restoreOverrideCursor()

	resultMapping = {0:STRATEGY_STEP, 1: STRATEGY_SAT, 2:STRATEGY_NATIVE}
	strategy = resultMapping[result]
	setStrategy(strategy)
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
	def __init__(self):
		self._data = None
		self.width = 0
		self.height = 0
		self.icon = None
	def getData(self):
		return self._data
	def setIconData(self, data):
		self._data = data
		self.icon = QPixmap()
		self.icon.loadFromData(QByteArray(data))
		self.width  = self.icon.width()
		self.height = self.icon.height()
	def readData(self, filename):
		with open(filename, 'rb') as f:
			setIconData(f.read())
			self.type = filename[-3:].upper()
	def setData(self, data):
		# skip thumbnail class header (-1, -1, 3, 0, bpp, width, height, 0)
		buffer = data[0x10:]
		self.width, i = getUInt16(data, 0x0A)
		self.height, i = getUInt16(data, i)

		if (buffer[0x1:0x4] == b'PNG'):
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
			buffer = b'BM' + pack('LLL', size + 0x36, 0, 0x36)
			buffer += data[offset:]
		self.setIconData(buffer)
	def length(self):   return len(self._data)
	def __str__(self):  return '%s: %d x %d' % (self.type, self.width, self.height)
	def __repr__(self): return self.__str__()
	def getIcon(self):  return self.icon

_thumbnail = None
def writeThumbnail(data):
	global _thumbnail
	if (data):
		thumbnail = Thumbnail()
		thumbnail.setData(data)
		dumpFolder = getDumpFolder()
		if ((not (dumpFolder is None)) and ParamGet("User parameter:BaseApp/Preferences/Mod/InventorLoader").GetBool('Others.DumpThumbnails', True)):
			with open(u"%s/_.%s" %(dumpFolder, thumbnail.type.lower()), 'wb') as file:
				file.write(thumbnail.getData())
		setThumbnail(thumbnail)
	else:
		_thumbnail = None
	return _thumbnail

def getThumbnail():
	global _thumbnail
	return _thumbnail

def setThumbnail(thumbnail):
	global _thumbnail
	_thumbnail = thumbnail
	return

UINT8      = Struct('<B').unpack_from
SINT8      = Struct('<b').unpack_from
UINT16     = Struct('<H').unpack_from
SINT16     = Struct('<h').unpack_from
UINT32     = Struct('<L').unpack_from
UINT64     = Struct('<Q').unpack_from
SINT32     = Struct('<l').unpack_from
SINT64     = Struct('<q').unpack_from
FLOAT32    = Struct('<f').unpack_from
FLOAT32_2D = Struct('<ff').unpack_from
FLOAT32_3D = Struct('<fff').unpack_from
RGBA       = Struct('<ffff').unpack_from
FLOAT64    = Struct('<d').unpack_from
FLOAT64_2D = Struct('<dd').unpack_from
FLOAT64_3D = Struct('<ddd').unpack_from
DATETIME   = Struct('<Q').unpack_from

def getBoolean(data, offset):
	'''
	Returns a single boolean value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the boolean value.
	Returns:
		True if the byte at the offset is '1', False if it is '0'
		Otherwise an exception will be thrown.
	'''
	val, = UINT8(data, offset)
	if (val == 1): return True, offset + 1
	if (val == 0): return False, offset + 1
	raise ValueError(u"Expected either 0 or 1 but found %02X" %(val))

def getSInt8(data, offset):
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
	val, = SINT8(data, offset)
	return val, offset + 1

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
	end = int(offset + size)
	assert end <= len(data), "Trying to read UInt8 array beyond data end (%d, %X > %X)" %(size, end, len(data))
	val = unpack_from('<' +'B'*int(size), data, offset)
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
	val = unpack_from('<' +'H'*int(size), data, offset)
	return val, int(offset + 2 * size)

def getSInt16(data, offset):
	'''
	Returns a single signed 16-Bit value.
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
	Returns an array of single signed 16-Bit values.
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
	val = unpack_from('<' +'h'*int(size), data, offset)
	return val, int(offset + 2 * size)

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

def getUInt64(data, offset):
	'''
	Returns a single unsingned 64-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the unsigned 64-Bit value.
	Returns:
		The unsigned 64-Bit value at offset.
		The new position in the 'stream'.
	'''
	val, = UINT64(data, offset)
	return val, offset + 8

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
	val = unpack_from('<' +'L'*int(size), data, offset)
	return val, int(offset + 4 * size)

def getUInt64A(data, offset, size):
	'''
	Returns an array of unsingned 64-Bit values.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
		size
			The size of the array.
	Returns:
		The array of unsigned 64-Bit values at offset.
		The new position in the 'stream'.
	'''
	val = unpack_from('<' +'Q'*int(size), data, offset)
	return val, int(offset + 8 * size)

def getSInt32(data, offset):
	'''
	Returns a single signed 32-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the signed 32-Bit value.
	Returns:
		The signed 32-Bit value at offset.
		The new position in the 'stream'.
	'''
	val, = SINT32(data, offset)
	return val, offset + 4

def getSInt64(data, offset):
	'''
	Returns a single signed 64-Bit value.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the signed 32-Bit value.
	Returns:
		The signed 32-Bit value at offset.
		The new position in the 'stream'.
	'''
	val, = SINT64(data, offset)
	return val, offset + 8

def getSInt32A(data, offset, size):
	'''
	Returns an array of signed 32-Bit values.
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
	val = unpack_from('<' + 'l'*int(size), data, offset)
	return val, int(offset + 4 * size)

def getSInt64A(data, offset, size):
	'''
	Returns an array of signed 64-Bit values.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the array.
		size
			The size of the array.
	Returns:
		The array of signed 64-Bit values at offset.
		The new position in the 'stream'.
	'''
	val = unpack_from('<' + 'q'*int(size), data, offset)
	return val, int(offset + 8 * size)

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
	singles = unpack_from('<' + 'f'*int(size), data, offset)
	val = [float(s) for s in singles]
	return val, int(offset + 4 * size)

def getFloat32_2D(data, index):
	val = FLOAT32_2D(data, index)
	return val, int(index + 0x8)

def getFloat32_3D(data, index):
	val = FLOAT32_3D(data, index)
	return val, int(index + 0xC)

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
	val = unpack_from('<' + 'd'*int(size), data, offset)
	return val, int(offset + 8 * size)

def getFloat64_2D(data, index):
	val = FLOAT64_2D(data, index)
	return VEC(val + (0.0,)), int(index + 0x10)

def getFloat64_3D(data, index):
	val = FLOAT64_3D(data, index)
	return VEC(val), int(index + 0x18)

def getColorRGBA(data, offset):
	r, g, b, a = RGBA(data, offset)
	c = Color(r, g, b, a)
	return c, offset + 0x10

class UID(object):
	def __init__(self, str = None, bytes_le = None):
		if (bytes_le):
			self.time_low = (bytes_le[ 3] << 24) | (bytes_le[2] << 16) | (bytes_le[1] << 8) | bytes_le[0]
			self.val1 = (bytes_le[ 5] <<  8) |  bytes_le[4]
			self.val2 = (bytes_le[ 7] <<  8) |  bytes_le[6]
			self.val3 = (bytes_le[ 8] <<  8) |  bytes_le[9]
			self.val4 = (bytes_le[10] << 40) | (bytes_le[11] << 32) | (bytes_le[12] << 24) | (bytes_le[13] << 16) | (bytes_le[12] << 24) | (bytes_le[13] << 16) | (bytes_le[14] << 8) | bytes_le[15]
		elif (str):
			vals = str.split('-')
			self.time_low = int(vals[0], 16)
			self.val1 = int(vals[1], 16)
			self.val2 = int(vals[2], 16)
			self.val3 = int(vals[3], 16)
			self.val4 = int(vals[4], 16)
		else:
			raise AttributeError("wrong argument type")
	@property
	def hex(self): return  "%08x%04x%04x%04x%012x"%(self.time_low, self.val1, self.val2, self.val3, self.val4)
	def __str__(self): return "%08X-%04X-%04X-%04X-%012X"%(self.time_low, self.val1, self.val2, self.val3, self.val4)
	def __repr__(self): return self.__str__()
	def __hash__(self): return hash((type(self),) + tuple(self.__dict__.values()))
	def __eq__(self, other):
		if (type(other) in ['tuple', 'list']) and len(other) == 8:
			if (self.time_low != (other[ 3] << 24) | (other[2] << 16) | (other[1] << 8) | other[0]): return False
			if (self.val1 != (other[ 5] <<  8) |  other[4]): return False
			if (self.val2 != (other[ 7] <<  8) |  other[6]): return False
			if (self.val3 != (other[ 8] <<  8) |  other[9]): return False
			return self.val4 == (other[10] << 40) | (other[11] << 32) | (other[12] << 24) | (other[13] << 16) | (other[12] << 24) | (other[13] << 16) | (other[14] << 8) | other[15]
		if (isinstance(other, UID)):
			if (self.time_low != other.time_low): return False
			if (self.val1 != other.val1): return False
			if (self.val2 != other.val2): return False
			if (self.val3 != other.val3): return False
			return self.val4 == other.val4
		return False
def getUUID(data, offset):
	'''
	Returns a UID.
	Args:
		data
			A binary string.
		offset
			The zero based offset of the UID.
	Returns:
		The UID at offset.
		The new position in the 'stream'.
	'''
	end = offset + 16
	val = UID(bytes_le=data[offset:end])
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
	try:
		txt = data[i: end].decode(ENCODING_FS)
	except:
		txt = data[i: end].decode('ansi')
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
	try:
		txt, i = getText8(data, i, l)
	except UnicodeDecodeError:
		txt = data[i:i+l]
		i += l
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

def decode(filename, utf=False):
	if (isinstance(filename, unicode)):
		# workaround since ifcopenshell currently can't handle unicode filenames
		if (utf):
			encoding = "utf8"
		else:
			import sys
			encoding = sys.getfilesystemencoding()
		filename = filename.encode(encoding).decode("utf-8")
	return filename

def isEmbeddings(names):
	return 'RSeEmbeddings' in names

def isEqual(a, b, e = 0.0001):
	if (a is None): return isEqual(b, CENTER)
	if (b is None): return isEqual(a, CENTER)
	return ((a - b).Length < e)

def isEqual1D(a, b, e = 0.0001):
	if (a is None): return isEqual1D(b, 0.0)
	if (b is None): return isEqual1D(a, 0.0)
	return abs(a - b) < e

def _log(caller, method, msg, args):
	try:
		s = u"%s\n" %(msg)
		if (len(args) > 0):
			method(s %args)
		else:
			method(s)
	except:
		Console.PrintError("FATAL ERROR in %s:\n" %(caller))
		Console.PrintError("msg   = " + msg)
		if (len(args) > 0): Console.PrintError("*args = (%s)" %(",".join(args)))

def setLoggingInfo(val):
	__prmPrefOW__.SetInt("checkLogging", val)
def setLoggingWarn(val):
	__prmPrefOW__.SetInt("checkWarning", val)
def setLoggingError(val):
	__prmPrefOW__.SetInt("checkError", val)

def logInfo(msg, *args):
	if (__prmPrefOW__.GetBool("checkLogging", False)): _log("logInfo",    Console.PrintMessage, msg, args)
def logWarning(msg, *args):
	if (__prmPrefOW__.GetBool("checkWarning", False)): _log("logWarning", Console.PrintWarning, msg, args)
def logError(msg, *args):
	if (__prmPrefOW__.GetBool("checkError", True)):    _log("logError",   Console.PrintError,   msg, args)

def logAlways(msg, *args):
	_log("logAlways", Console.PrintMessage, msg, args)

def getFileVersion():
	global _fileVersion
	return _fileVersion

def getFileBeta():
	global _fileBeta
	return _fileBeta

def getBlockSize():
	global _block_size
	return _block_size

def getProperty(ole, path, key):
	p = ole.getproperties([path], convert_time=True)
	try:
		property = p[key]
		if (isString(property)):
			if (property[-1] == '\x00'):
				return property[0:-1]
		return property
	except:
		return None

def setFileVersion(version):
	global _fileVersion, _block_size
	_fileVersion = version
	_block_size = 0 if (_fileVersion > 2010) else 4

def getInventorFile():
	global _inventor_file
	return _inventor_file

def getDumpFolder():
	global _dump_folder
	return _dump_folder

def cleanDumpFolder():
	folder = getDumpFolder()
	for f in os.listdir(folder):
		p = os.path.join(folder, f)
		if os.path.isfile(p):
			os.unlink(p)
		else:
			shutil.rmtree(p)

def setDumpFolder(anyInputFile):
	global _dump_folder
	fileParts = os.path.splitext(anyInputFile)
	_dump_folder = u"%s_%s" %(fileParts[0], fileParts[1][1:])

	if (os.path.exists(_dump_folder)):
		cleanDumpFolder()
	else:
		try:
			os.mkdir(_dump_folder)
		except:
			_dump_folder = None
			# can't create folder, e.g. insuficien usr right.
			tmp = os.getenv('TEMP')
			if ((tmp is None) or (not os.path.exists(tmp))):
				# strange - maybe it's UNIX
				tmp = os.getenv('TMP')
				if ((tmp is None) or (not os.path.exists(tmp))):
					# even more strange - maybe it's RiscOS
					tmp = os.getenv('TMPDIR')
					if ((tmp is None) or (not os.path.exists(tmp))):
						tmp = os.path.expanduser('~')
						tmp = os.path.join(tmp, "_InventorLoader_Dump")
						if (not os.path.exists(tmp)):
							try:
								os.mkdir(tmp)
								logWarning(u"Can't locate system's TEMP folder! - using '%s'" %(tmp))
							except:
								tmp = None
			if (not tmp is None):
				ifile = os.path.splitext(os.path.basename(anyInputFile))
				_dump_folder = os.path.join(tmp, "%s_%s" %(ifile[0], ifile[1][1:]))
				try:
					if (not os.path.exists(_dump_folder)):
						os.mkdir(_dump_folder)
					else:
						cleanDumpFolder()
				except:
					_dump_folder = None
			if (_dump_folder is None):
				logWarning(u"Can't locate any dump folder! Ignoring dump files!")
			else:
				logWarning(u"Using TEMP folder for dumping files: '%s'" %(_dump_folder))


def setInventorFile(file):
	global _inventor_file

	_inventor_file = os.path.abspath(file)
	setDumpFolder(_inventor_file)
	return OleFileIO(file)

def isString(value):
	if (type(value) is str): return True
	if (sys.version_info.major < 3):
		if (type(value) is unicode): return True
	return False

class Color(object):
	def __init__(self, red, green, blue, alpha):
		self.red   = red
		self.green = green
		self.blue  = blue
		self.alpha = alpha

	def getRGB(self):
		return (self.red, self.green, self.blue)

	def getRGBA(self):
		return (self.red, self.green, self.blue, self.alpha)

	def __str__(self): # return unicode
		r = int(self.red   * 0xFF)
		g = int(self.green * 0xFF)
		b = int(self.blue  * 0xFF)
		a = int(self.alpha * 0xFF)
		return u'#%02X%02X%02X%02X' %(r, g, b, a)

	def __repr__(self):
		return self.__str__()

def getIconPath(fileName):
	return os.path.join(os.path.dirname(__file__), "Resources", "icons", fileName)

def int2col(c):
	if (c < 27):
		return chr(64 + c)
	m = c // 26
	n = c % 26
	if (n == 0):
		n = 26;
		m -=1;
	return int2col(m) + int2col(n)

def getCellRef(col, row):
	if (isString(col)):
		return u"%s%d" %(col, row)
	return u"%s%d" %(int2col(col), row)

def getTableValue(table, col, row):
	try:
		return table.get(getCellRef(col, row))
	except:
		return None

def setTableValue(table, col, row, val):
	if (type(val) == str):
		table.set(getCellRef(col, row), val)
	else:
		if ((sys.version_info.major <= 2) and (type(val) == unicode)):
			table.set(getCellRef(col, row), "%s" %(val.encode("utf8")))
		else:
			table.set(getCellRef(col, row), str(val))

def calcAliasname(name):
	alias = name.replace(':', '_')
	if (IS_CELL_REF.search(name)):
		return '%s_' %(alias)
	# 45, 48..57, 65..90, 97..122
	result = ''
	for c in alias:
		i = ord(c)
		if (i == 45) or (i > 47 and i < 58) or (i > 64 and i < 91) or (i > 96 and i < 123):
			result += c
		else:
			result += '_'
	if (result[0] == '_'):
		return 'd' + result
	return result

def reshape(nums, size):
	if size == 1: return nums
	return [[nums[size * i + j] for j in range(size)] for i in range(len(nums) // size)]
