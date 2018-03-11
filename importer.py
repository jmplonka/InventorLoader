# -*- coding: utf8 -*-

'''
importer.py:
Collection of 3D Mesh importers
'''

import os, FreeCAD, importerSAT

__author__     = "Jens M. Plonka"
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

def decode(name):
	"decodes encoded strings"
	try:
		decodedName = (name.decode("utf8"))
	except UnicodeDecodeError:
		try:
			decodedName = (name.decode("latin1"))
		except UnicodeDecodeError:
			FreeCAD.Console.PrintError("Error: Couldn't determine character encoding")
			decodedName = name
	return decodedName

def read(doc, filename):
	name, ext = os.path.splitext(filename)
	ext = ext.lower()
	FreeCAD.ActiveDocument = doc
	if (ext == '.sat'):
		importerSAT.read(doc, filename)
	else:
		FreeCAD.Console.PrintError("No suitable reader found for ext=%s\n" %(ext))
	return

def insert(filename, docname):
	'''
	Called when freecad wants to import a file into an existing project.
	'''
	try:
		doc = FreeCAD.getDocument(docname)
		read(doc, filename)
		return doc
	except:
		return open(filename)

def open(filename):
	'''
	Called when freecad wants to open a file as a new project.
	'''
	docname = (os.path.splitext(os.path.basename(filename))[0]).encode("utf8")
	doc = FreeCAD.newDocument(docname)
	doc.Label = decode(docname)
	read(doc, filename)
	return doc
