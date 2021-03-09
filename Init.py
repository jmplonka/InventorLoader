# -*- coding: utf-8 -*-

'''
Init.py
FreeCAD init script of the InventorLoader module
'''

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

FreeCAD.addImportType("Autodesk INVENTOR part file (*.ipt)", "importerIL")
#FreeCAD.addImportType("Autodesk INVENTOR assembly file (*.iam)", "importerIL")
#FreeCAD.addImportType("Autodesk INVENTOR presentation file (*.ipn)", "importerIL")
#FreeCAD.addImportType("Autodesk INVENTOR drawing file (*.idw)", "importerIL")
FreeCAD.addImportType("3D ACIS Modeler file (*.sat *.sab *.smb *.smbh)", "importerIL")
FreeCAD.addImportType("AutoCAD 3D-Drawing file (*.dxf)", "importerIL")
FreeCAD.addImportType("AutoCAD Fusion360 file (*.f3d)", "importerIL")
