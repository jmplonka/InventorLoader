# -*- coding: utf8 -*-

'''
Init.py
FreeCAD init script of the InventorLoader module
'''

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

FreeCAD.addImportType("Autodesk INVENTOR part file (*.ipt *.iam)", "importer")
FreeCAD.addImportType("3D ACIS Modeler file (*.sat *.sab)", "importer")
