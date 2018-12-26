# -*- coding: utf-8 -*-

'''
InventorViewProviders.py
GUI representations for objectec imported from Inventor
'''

import re, sys, Part
from importerUtils import logInfo

INVALID_NAME = re.compile('^[0-9].*')

def getObjectName(name):
	if (sys.version_info.major < 3):
		v = re.sub(r'[^\x00-\x7f]', r'_', name)
	else:
		v = re.sub(b'[^\x00-\x7f]', b'_', name.encode('utf8')).decode('utf8')
	if (INVALID_NAME.match(name)):
		return "_%s" %(v)
	return v

class _ViewProviderBoundaryPatch:
	def __init__(self, vp):
		self.attach(vp)

	def attach(self, vp):
		vp.Proxy = self

	def getDisplayModes(self, vp):
		return ["Shaded", "Wireframe"]

	def getDefaultDisplayMode(self):
		return "Shaded"

	def getIcon(self):
		return """
		    /* XPM */
			static const char * ViewProviderBox_xpm[] = {
			"16 16 5 1",
			"   c None",
			".  c #3333FF",
			"+  c #ffa552",
			"@  c #ffcea5",
			"#  c #ffb573",
			"................",
			".++++++++##@##+.",
			".+++++++##@##++.",
			".++++++##@##+++.",
			".+++++##@##++++.",
			".++++##@##+++++.",
			".+++##@##++++++.",
			".++##@##+++++##.",
			"......++++++##@.",
			"    $.+++++##@#.",
			"     .++++##@##.",
			"     .+++##@##+.",
			"     $.+##@##++.",
			"      $..@##+++.",
			"        $.......",
			"                "};
			"""

	def onChanged(self, vp, prop): return

	def setEdit(self, vp, mode):   return False

	def unsetEdit(self, vp, mode): return

	def __getstate__(self):        return None

	def __setstate__(self, state): return

def makeBoundaryPatch(doc, edges, name):
	fp = doc.addObject("Part::FeaturePython", getObjectName(name))
	fp.Label = name
	fp.Shape = Part.Face(Part.Wire(edges))
	_ViewProviderBoundaryPatch(fp.ViewObject)
	return fp

class _Knit:
	def __init__(self, fp):
		fp.addProperty("App::PropertyLinkList", "Faces", "Knit", "List of faces to knit together")
		fp.addProperty("App::PropertyBool", "Solid", "Knit", "Create a solid if possible")
		fp.Proxy = self

	def execute(self, fp):
		faces = [f.Shape for f in fp.Faces]
		fp.Shape = Part.Shell(faces)
		if (fp.Solid):
			if (fp.Shape.isClosed()):
				fp.Shape = Part.Solid(fp.Shape)

class _ViewProviderKnit:
	def __init__(self, vp):
		self.attach(vp)

	def attach(self, vp):
		vp.Proxy = self
		self.fp   = vp.Object

	def getDisplayModes(self, vp):
		return ["Shaded", "Wireframe", "Flat Lines"]

	def getDefaultDisplayMode(self):
		return "Shaded"

	def onChanged(self, vp, prop): return

	def setEdit(self, vp, mode):   return False

	def unsetEdit(self, vp, mode): return

	def claimChildren(self):
		return self.fp.Faces

	def getIcon(self):
		return """
		    /* XPM */
			static const char * ViewProviderBox_xpm[] = {
			"16 16 9 1",
			"   c None",
			".  c #3333FF",
			"+  c #ffa552",
			"@  c #ffcea5",
			"#  c #ffb573",
			"~  c #ffffff",
			",  c #9999ff",
			";  c #de5200",
			":  c #ffd652",
			"................",
			".~~~~~~~.~~~~~~.",
			".~+++,.....,#@#.",
			".~+++++;.:~#@##.",
			".~+++,.....,##+.",
			".~+++++;.:~##++.",
			".~+++,.....,#++.",
			".~+++++;.:~#+++.",
			".~+++,.....,+++.",
			".~++##@;.:~++++.",
			".~+##,.....,+++.",
			".~##@##;.:~++++.",
			".~#@#,.....,+++.",
			".~@##++;.:~++++.",
			"................",
			"               .",
			};
			"""

	def __getstate__(self): return None

	def __setstate__(self,state): return None

def makeKnit(doc, faces, name, solid):
	fp = doc.addObject("Part::FeaturePython", getObjectName(name))
	fp.Label = name
	knit = _Knit(fp)
	fp.Solid = solid
	fp.Faces = faces
	_ViewProviderKnit(fp.ViewObject)
	for face in faces:
		face.ViewObject.Visibility = False
	return fp