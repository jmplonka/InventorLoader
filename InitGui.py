#import FreeCADGui

# Import_IPT.py is the file that has the code for opening and reading .ipt files
FreeCAD.addImportType('Autodesk INVENTOR part file (*.ipt)', 'Import_IPT')
# Inventor Importer has some user adjustable preferences for troubleshooting
#FreeCADGui.addPreferencePage( ':/ui/IPTprefs.ui', 'Import-Export' )
