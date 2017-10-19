# -*- coding: utf8 -*-

# Assumes Import_IPT.py is the file that has the code for opening and reading .ipt files
import traceback
from importerUtils import logError

try:
	if (not hasattr(FreeCADGui, 'InventorLoaderPrefs')):
		FreeCADGui.addIconPath(FreeCAD.getHomePath() + 'Mod/InventorLoader/Resources')
		FreeCADGui.addPreferencePage(FreeCAD.getHomePath() + 'Mod/InventorLoader/Resources/ui/PrefsInventorLoader.ui', 'Import-Export')
		FreeCADGui.InventorImporterPrefs = True
except:
	logError(">E: " + traceback.format_exc())
