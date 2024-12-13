# -*- coding: utf-8 -*-

'''
importer.py:
Collection of 3D Mesh importers
'''

import os, sys, FreeCAD, FreeCADGui, importerSAT, importerDXF, Import_IPT, importerF3D
import Acis, importerClasses
from importerUtils   import canImport, logInfo, logWarning, logError, logAlways, getAuthor, getComment, getLastModifiedBy, setThumbnail
from olefile         import isOleFile
from importerFreeCAD import createGroup
from pivy            import coin

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

def decode(name):
	"decodes encoded strings"
	decodedName = name
	try:
		decodedName = name.encode(sys.getfilesystemencoding()).decode("utf8")
	except:
		logWarning("    Couldn't determine character encoding for filename - using unencoded!\n")
	return decodedName

def insertGroup(filename):
	grpName = os.path.splitext(os.path.basename(filename))[0]
	#There's a problem with adding groups starting with numbers!
	root = createGroup('_%s' %(grpName))
	root.Label = grpName

	return root

def read(filename):
	setThumbnail(None)
	name, ext = os.path.splitext(filename)
	ext = ext.lower()
	if (ext == '.ipt'):
		ole = Import_IPT.checkVersion(filename)
		if (ole):
			if (Import_IPT.read(ole)):
				return Import_IPT
	elif (ext == '.sat'):
		if (importerSAT.readText(filename)):
			return importerSAT
	elif (ext in ['.sab', '.smb', '.smbh']):
		if (importerSAT.readBinary(filename)):
			return importerSAT
	elif (ext == '.dxf'):
		if (importerDXF.read(filename)):
			return importerDXF
	elif (ext == '.iam'):
		ole = Import_IPT.checkVersion(filename)
		if (ole):
			if (Import_IPT.read(ole)):
				return Import_IPT
	elif (ext == '.ipn'):
		ole = Import_IPT.checkVersion(filename)
		if (ole):
			if (Import_IPT.read(ole)):
				return Import_IPT
	elif (ext == '.idw'):
		ole = Import_IPT.checkVersion(filename)
		if (ole):
			if (Import_IPT.read(ole)):
				return Import_IPT
	elif (ext == '.f3d'):
		if (importerF3D.read(filename)):
			return importerF3D
	return None

def isFileValid(filename):
	if (not os.path.exists(os.path.abspath(filename))):
		logError(u"File doesn't exists (%s)!", os.path.abspath(filename))
		return False
	if (not os.path.isfile(filename)):
		logError(u"Can't import folders!")
		return False
	if (filename.split(".")[-1].lower() in ("ipt", "iam", "ipn", "idw")):
		if (not isOleFile(filename)):
			logError(u"ERROR> '%s' is not a valid Autodesk Inventor file!", filename)
			return False
	return canImport()

def releaseMemory():
	setThumbnail(None)
	Acis.releaseMemory()
	importerClasses.releaseModel()

def adjustView(doc):
	if (FreeCAD.GuiUp):
		# adjust camara position and orientation
		g = FreeCADGui.getDocument(doc.Name)
		v = g.ActiveView
		c = v.getCameraNode()
		p = coin.SbVec3f(1, 1, 1)
		o = coin.SbVec3f(0, 0, 0)
		u = coin.SbVec3f(0, 1, 0)
		c.position.setValue(p)
		c.pointAt( o, u )
		FreeCADGui.SendMsgToActiveView("ViewFit")

def insert(filename, docname, skip = [], only = [], root = None):
	'''
	opens an Autodesk Inventor file in the current document
	'''
	doc = FreeCAD.listDocuments().get(docname)
	if (doc):
		if (isFileValid(filename)):
			logAlways(u"Importing: %s", filename)
			reader = read(filename)
			if (reader is not None):
				name = os.path.splitext(os.path.basename(filename))[0]
				name = decode(name)
				group = insertGroup(name)
				reader.create3dModel(group, doc)
			releaseMemory()
			FreeCADGui.SendMsgToActiveView("ViewFit")
	else:
		_open(filename, skip, only, root)
	logInfo(u"DONE!")
	return

def _open(filename, skip = [], only = [], root = None):
	reader = read(filename)
	if (reader is not None):
		name = os.path.splitext(os.path.basename(filename))[0]
		doc = FreeCAD.newDocument(decode(name))
		doc.Label = name
		doc.CreatedBy = getAuthor()
		doc.LastModifiedBy = getLastModifiedBy()
		doc.Comment = getComment()
		reader.create3dModel(root , doc)
		adjustView(doc)
	releaseMemory()
	return

def open(filename, skip = [], only = [], root = None):
	'''
	opens an Autodesk Inventor file in a new document
	In addition to insert (import), the iProperties are as well added to the document.
	'''
	if (isFileValid(filename)):
		abs_file_name = os.path.abspath(filename)
		logAlways(f"Reading: {abs_file_name}")
		_open(abs_file_name, skip, only, root)
		logInfo('DONE!')
	return
