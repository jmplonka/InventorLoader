# -*- coding: utf8 -*-

'''
InitGui.py
Assumes Import_IPT.py is the file that has the code for opening and reading .ipt files
'''
import traceback, importerUtils

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

#try:
#	addinpath = os.path.dirname(os.path.abspath(__file__))
#	if (not hasattr(FreeCADGui, 'InventorLoaderPrefs')):
#		FreeCADGui.addIconPath(addinpath + '/Resources')
#		FreeCADGui.addPreferencePage(addinpath + '/Resources/ui/PrefsInventorLoader.ui', 'Import-Export')
#		FreeCADGui.InventorImporterPrefs = True
#except:
#	FreeCAD.Console.PrintError(">E: %s\n"% traceback.format_exc())

def missingDependency(module, url, folder):
	import os, subprocess, importerUtils

	# Where is this file located???
	addinpath = FreeCAD.getHomePath() + "Mod/InventorLoader/"
	#addinpath = FreeCAD.getUserAppDataDir() + "Mod/InventorLoader/"
	if (not os.path.exists(addinpath + "libs")):
		print "Libs does not exists will try to unpack them ... "
		import zipfile
		zip = zipfile.ZipFile(addinpath + "libs.zip", 'r')
		zip.extractall(addinpath)
		zip.close()
		FreeCAD.Console.PrintWarning("DONE!\n")
	FreeCAD.Console.PrintWarning("Trying to install missing site-package '%s' ... " %(module))
	os.chdir(addinpath + "libs")
	subprocess.call(['python', 'installLibs.py', FreeCAD.getHomePath(), url, folder])
	FreeCAD.Console.PrintWarning("DONE!\n")
	importerUtils.setCanImport(False)

try:
	import xlwt
except:
	missingDependency("xlrd", "https://pypi.python.org/pypi/xlwt", "xlwt-1.3.0")

try:
	import xlrd
except:
	missingDependency("xlrd", "https://pypi.python.org/pypi/xlrd", "xlrd-1.1.0")

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
	msgBox.setIcon(QtGui.QMessageBox.Question)
	msgBox.setText("Dependencies updated!!")
	msgBox.setInformativeText("To use Inventor-AddOn, restart of FreeCAD required.\nQuit FreeCAD now?")
	msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
	msgBox.setDefaultButton(QtGui.QMessageBox.Yes)
	ret = msgBox.exec_()
	if (ret == QtGui.QMessageBox.Yes):
		FreeCADGui.getMainWindow().close()