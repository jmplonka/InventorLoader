# -*- coding: utf8 -*-

# Assumes Import_IPT.py is the file that has the code for opening and reading .ipt files
import traceback

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.6.0'
__status__      = 'In-Development'

try:
	if (not hasattr(FreeCADGui, 'InventorLoaderPrefs')):
		FreeCADGui.addIconPath(FreeCAD.getHomePath() + 'Mod/InventorLoader/Resources')
		FreeCADGui.addPreferencePage(FreeCAD.getHomePath() + 'Mod/InventorLoader/Resources/ui/PrefsInventorLoader.ui', 'Import-Export')
		FreeCADGui.InventorImporterPrefs = True
except:
	FreeCAD.Console.PrintError(">E: %s\n"% traceback.format_exc())

_can_import = True

def missingDependency(module, url, folder):
	import os
	import subprocess
	global _can_import
	
	addinpath = FreeCAD.getHomePath() + "Mod/InventorLoader/"
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
	_can_import = False

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

if (not _can_import):
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