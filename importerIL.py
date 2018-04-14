# -*- coding: utf-8 -*-

'''
importer.py:
Collection of 3D Mesh importers
'''

import os, sys, FreeCAD, importerSAT, Import_IPT
from importerUtils import canImport, logMessage, logError, LOG

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

def decode(name):
	"decodes encoded strings"
	try:
		decodedName = name.encode("utf8")
	except UnicodeEncodeError:
		try:
			decodedName = name.encode(sys.getfilesystemencoding())
		except UnicodeEncodeError:
			FreeCAD.Console.PrintError("Error: Couldn't determine character encoding!\n")
			decodedName = name
	return decodedName

def insertGroup(doc, filename):
	grpName = os.path.splitext(os.path.basename(filename))[0]
	#There's a problem with adding groups starting with numbers!
	root = createGroup(doc, '_%s' %(grpName))
	root.Label = grpName

	return root

def read(doc, filename, readProperties):
	name, ext = os.path.splitext(filename)
	ext = ext.lower()
	if (ext == '.ipt'):
		if (Import_IPT.read(doc, filename, readProperties)):
			return Import_IPT
	elif (ext == '.sat'):
		if (importerSAT.readText(doc, filename)):
			return importerSAT
	elif (ext == '.iam'):
		logError("Sorry, AUTODESK assembly files not yet supported!")
	elif (ext == '.sab'):
		if (importerSAT.readBinary(doc, filename)):
			return importerSAT
	return None

def checkfile(filename):
	if (not os.path.exists(filename)):
		logError("File doesn't exists!")
		return False
	if (not os.path.isfile(filename)):
		logError("Can't import folders!")
		return False
	return canImport()

def insert(filename, docname, skip = [], only = [], root = None):
	'''
	opens an Autodesk Inventor file in the current document
	'''
	if (checkfile(filename)):
		try:
			doc = FreeCAD.getDocument(docname)
			logMessage("Importing: %s" %(filename), LOG.LOG_ALWAYS)
			reader = read(doc, filename, False)
			if (reader is not None):
				name = os.path.splitext(os.path.basename(filename))[0]
				name = decode(name)
				group = insertGroup(doc, name)
				reader.create3dModel(group, doc)
		except:
			open(filename, skip, only, root)
	return

def open(filename, skip = [], only = [], root = None):
	'''
	opens an Autodesk Inventor file in a new document
	In addition to insert (import), the iProperties are as well added to the document.
	'''
	if (checkfile(filename)):
		logMessage("Reading: %s" %(filename), LOG.LOG_ALWAYS)
		name = os.path.splitext(os.path.basename(filename))[0]
		name = decode(name)
		doc = FreeCAD.newDocument(name)
		doc.Label = name
		reader = read(doc, filename, True)
		if (reader is not None):
			# Create 3D-Model in root (None) of document
			reader.create3dModel(None , doc)
	return
