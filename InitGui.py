# -*- coding: utf-8 -*-

'''
InitGui.py
prepare required modules to be installed.
'''
__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

def checkImports():
	def missingDependency(file):
		module = os.path.join(os.path.dirname(EmptyFile.__file__), "libs", file)
		subprocess.call(u"\"%s\" -m pip install \"%s\"" %(sys.executable, module))

	import os, subprocess, traceback, FreeCAD, FreeCADGui, EmptyFile
	try:
		if (not hasattr(FreeCADGui, 'InventorLoaderPrefs')):
			addinpath = os.path.abspath(os.path.dirname(EmptyFile.__file__))
			FreeCADGui.addIconPath(os.path.join(addinpath, 'Resources'))
			FreeCADGui.addPreferencePage(os.path.join(addinpath, 'Resources/ui/PrefsInventorLoader.ui'), 'Import-Export')
			FreeCADGui.InventorImporterPrefs = True
	except:
		FreeCAD.Console.PrintError(">E: %s\n"% traceback.format_exc())

	try:
		import olefile
	except:
		missingDependency("olefile")

	try:
		import xlrd
	except:
		missingDependency("xlrd")

	try:
		import xlwt
	except:
		missingDependency("xlwt")

	try:
		import xlutils
	except:
		missingDependency("xlutils")

	import importerUtils
	try:
		import SheetMetalCmd
		importerUtils.setUseSheetMetal(True)
	except:
		importerUtils.setUseSheetMetal(False)

	from InventorWorkbench import InventorWorkbench
	Gui.addWorkbench(InventorWorkbench)

checkImports()