# -*- coding: utf-8 -*-

'''
InitGui.py
Assumes Import_IPT.py is the file that has the code for opening and reading .ipt files
'''
import os, traceback, importerUtils, FreeCAD, FreeCADGui, importerSAT

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"


# Where is this file located?
# => get it from a module located in the same folder (thanks to DeepSOIC's "ugly hack")
f = importerSAT.__file__ # hope that no other will name a module like this ;>
addinpath = os.path.abspath(os.path.dirname(f)) + os.path.sep
try:
	if (not hasattr(FreeCADGui, 'InventorLoaderPrefs')):
		FreeCADGui.addIconPath(addinpath + 'Resources')
		FreeCADGui.addPreferencePage(addinpath + 'Resources/ui/PrefsInventorLoader.ui', 'Import-Export')
		FreeCADGui.InventorImporterPrefs = True
except:
	FreeCAD.Console.PrintError(">E: %s\n"% traceback.format_exc())

def missingDependency(module, url, folder):
	global addinpath
	import os, subprocess, importerUtils, FreeCAD
	if (not os.path.exists(addinpath + "libs")):
		FreeCAD.Console.PrintWarning("Unpacking required site-packages ... ")
		import zipfile
		zip = zipfile.ZipFile(addinpath + "libs.zip", 'r')
		zip.extractall(addinpath)
		zip.close()
		FreeCAD.Console.PrintWarning("DONE!\n")
	from libs import installLibs
	installLibs.installLib(addinpath + "libs" + os.path.sep, folder, url)
	importerUtils.setCanImport(False)
	FreeCAD.Console.PrintWarning("RESTART REQUIRED!\n")

try:
	import xlrd
except:
	missingDependency("xlrd", "https://pypi.python.org/pypi/xlrd", "xlrd-1.1.0")

try:
	import xlwt
except:
	missingDependency("xlwt", "https://pypi.python.org/pypi/xlwt", "xlwt-1.3.0")

try:
	import xlutils
except:
	missingDependency("xlutils", "http://pypi.python.org/pypi/xlutils", "xlutils-2.0.0")

try:
	import olefile
except:
	missingDependency("olefile", "http://www.decalage.info/python/olefileio", "olefile")

try:
	import SheetMetalCmd
	importerUtils.setUseSheetMetal(True)
except:
	importerUtils.setUseSheetMetal(False)

if (not importerUtils.canImport()):
	from PySide import QtCore, QtGui
	msgBox = QtGui.QMessageBox()
	msgBox.setIcon(QtGui.QMessageBox.Warning)
	msgBox.setText("Dependencies updated!!")
	msgBox.setInformativeText("To use Inventor-AddOn, restart of FreeCAD is required!")
	ret = msgBox.exec_()
else:
	from InventorWorkbench import InventorWorkbench
	Gui.addWorkbench(InventorWorkbench)
