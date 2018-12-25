# -*- coding: utf-8 -*-

'''
InventorViewProviders.py
GUI representations for objectec imported from Inventor
'''

import re, sys, Part
from importerUtils import logInfo

INVALID_NAME = re.compile('^[0-9].*')

class BoundaryPatch:
	def __init__(self, obj, edges):
		obj.addProperty("Part::PropertyPartShape", "Shape", "BoundaryPatch", "Shape of the boundary patch")
		obj.Proxy = self
		obj.Shape = self.__createFace__(edges)

	def __createFace__(self, edges):
		wire = Part.Wire(edges)
		return Part.Face(wire)

	def execute(self, fp):
		fp.Shape = self.__createFace__(fp.Shape.Edges)

class ViewProviderBoundaryPatch:
	def __init__(self, obj):
		''' Set this object to the proxy object of the actual view provider '''
		obj.Proxy = self

	def attach(self, obj):
		''' Setup the scene sub-graph of the view provider.'''
		return

	def getDisplayModes(self,obj):
		'''Return a list of display modes.'''
		return ["Shaded", "Wireframe"]

	def getDefaultDisplayMode(self):
		'''Return the name of the default display mode. It must be defined in getDisplayModes.'''
		return "Shaded"

	def onChanged(self, vp, prop):
		'''Here we can do something when a single property got changed'''
		logInfo("Change property: %s" %(prop))

	def getIcon(self):
		'''Return the icon in XPM format which will appear in the tree view.'''
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

	def __getstate__(self):
		'''When saving the document this object gets stored using Python's cPickle module.
		Since we have some un-pickable here -- the Coin stuff -- we must define this method
		to return a tuple of all pickable objects or None.'''
		return None

	def __setstate__(self,state):
		'''When restoring the pickled object from document we have the chance to set some
		internals here. Since no data were pickled nothing needs to be done here.'''
		return None

def getObjectName(name):
	v = name
	if (sys.version_info.major < 3):
		v = v.encode('utf8')
		v = v.strip()
	if (INVALID_NAME.match(name)):
		return u"_%s" %(v)
	return v

def makeBoundaryPath(doc, edges, name):
	a = doc.addObject("Part::FeaturePython", getObjectName(name))
	a.Label = name
	boundaryPatch = BoundaryPatch(a, edges)
	ViewProviderBoundaryPatch(a.ViewObject)
	return a