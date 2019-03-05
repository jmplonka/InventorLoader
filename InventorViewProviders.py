# -*- coding: utf-8 -*-

'''
InventorViewProviders.py
GUI representations for objectec imported from Inventor
'''

import re, sys, Part, FreeCAD
from importerUtils import logInfo, getIconPath
from FreeCAD       import Vector as VEC

INVALID_NAME = re.compile('^[0-9].*')

def getObjectName(name):
	if (sys.version_info.major < 3):
		v = re.sub(r'[^\x00-\x7f]', r'_', name)
	else:
		v = re.sub(b'[^\x00-\x7f]', b'_', name.encode('utf8')).decode('utf8')
	if (INVALID_NAME.match(name)):
		return "_%s" %(v)
	return v

class _ViewProvider(object):
	def __init__(self, vp):
		vp.Proxy = self

	def attach(self, vp):
		self.ViewObject = vp
		self.fp = vp.Object

	def onChanged(self, vp, prop):   return

	def setEdit(self, vp, mode):     return False

	def unsetEdit(self, vp, mode):   return

	def __getstate__(self):          return None

	def __setstate__(self,state):    return None

	def getDisplayModes(self, vp):   return ["Shaded", "Wireframe", "Flat Lines"]

	def getDefaultDisplayMode(self): return "Shaded"

	def setDisplayMode(self, mode):  return mode


class _ViewProviderBoundaryPatch(_ViewProvider):
	def __init__(self, vp):
		super(_ViewProviderBoundaryPatch, self).__init__(vp)

	def getIcon(self):
		return getIconPath('FxBoundaryPatch.xpm')

def makeBoundaryPatch(edges, name = None):
	if (name is None):
		fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "BoundaryPatch")
	else:
		fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", getObjectName(name))
		fp.Label = name
	fp.Shape = Part.Face(Part.Wire(edges))
	if FreeCAD.GuiUp:
		_ViewProviderBoundaryPatch(fp.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return fp

class _Stich(object):
	def __init__(self, fp, solid, faces):
		fp.addProperty("App::PropertyBool",     "Solid", "Stitch", "Create a solid if possible")
		fp.addProperty("App::PropertyLinkList", "FaceList", "Stitch", "List of faces to stitch together")
		fp.Solid    = solid
		fp.FaceList = faces
		fp.Proxy    = self

	def execute(self, fp):
		faces = [f.Shape for f in fp.FaceList]
		fp.Shape = Part.Shell(faces)
		if (fp.Solid):
			if (fp.Shape.isClosed()):
				fp.Shape = Part.Solid(fp.Shape)

class _ViewProviderStitch(_ViewProvider):
	def __init__(self, vp):
		super(_ViewProviderStitch, self).__init__(vp)

	def claimChildren(self):
		return self.fp.FaceList

	def getIcon(self):
		return getIconPath('FxStitch.xpm')

def makeStitch(faces, name = None, solid = False):
	if (name is None):
		fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "FxStitch")
	else:
		fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", getObjectName(name))
		fp.Label = name
	_Stich(fp, solid, faces)
	if FreeCAD.GuiUp:
		_ViewProviderStitch(fp.ViewObject)
	for face in faces:
		face.ViewObject.Visibility = False
	FreeCAD.ActiveDocument.recompute()
	return fp

class _Point(object):
	def __init__(self, fp, pt):
		fp.addProperty("App::PropertyVector", "Point", "Draft", "Location")
		fp.Point = pt
		fp.Proxy = self

	def execute(self, fp):
		vec = VEC(fp.Point)
		fp.Shape = Part.Vertex(vec)

class _ViewProviderPoint(_ViewProvider):
	def __init__(self, vp):
		super(_ViewProviderPoint, self).__init__(vp)

	def getIcon(self):
		return """
			/* XPM */
			static char * xpm[] = {
			"16 16 9 1",
			" 	c None",
			".	c #92B6B6",
			"+	c #496D92",
			"@	c #246D92",
			"#	c #6D9292",
			"$	c #4992DB",
			"%	c #246DB6",
			"&	c #2492B6",
			"*	c #4992B6",
			"                ",
			"                ",
			"                ",
			"     .+@@+.     ",
			"    #@$$$$@#    ",
			"   .@$$$$$$%.   ",
			"   +$$$$$$&$+   ",
			"   @$*%%%%%%@   ",
			"   @$%%%%%%%@   ",
			"   +$%%%%%%*+   ",
			"   .@%%%%%%%.   ",
			"    #@&%%%%#    ",
			"     .+@@+.     ",
			"                ",
			"                ",
			"                "};
			"""

def makePoint(pt, name):
	fp = FreeCAD.ActiveDocument.addObject("Part::Feature", getObjectName(name))
	fp.Label = name
	_Point(fp, pt)
	if FreeCAD.GuiUp:
		_ViewProviderPoint(fp.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return fp

class _Line(object):
	def __init__(self, fp, pt1, pt2):
		fp.addProperty("App::PropertyVector", "Start", "Line", "start point")
		fp.addProperty("App::PropertyVector", "End", "Line", "end point")
		fp.Start = pt1
		fp.End   = pt2
		fp.Proxy = self

	def execute(self, fp):
		pt1 = fp.Start
		pt2 = fp.End
		fp.Shape = Part.makeLine(pt1, pt2)

class _ViewProviderLine(_ViewProvider):
	def __init__(self, vp):
		super(_ViewProviderLine, self).__init__(vp)

def makeLine(pt1, pt2, name):
	fp = FreeCAD.ActiveDocument.addObject("Part::Feature", getObjectName(name))
	fp.Label = name
	line = _Line(fp, pt1, pt2)
	if FreeCAD.GuiUp:
		_ViewProviderLine(fp.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return fp

class _Plane(object):
	def __init__(self, fp, c, n):
		fp.addProperty("App::PropertyVector", "Center", "Plane", "center position")
		fp.addProperty("App::PropertyVector", "Normal", "Plane", "normal vector of the plane")
		fp.Center = c
		fp.Normal = n
		fp.Proxy = self

	def execute(self, fp):
		c = fp.Center
		n = fp.Normal
		fp.Shape = Part.Plane(c, n).toShape()

class _ViewProviderPlane(_ViewProvider):
	def __init__(self, vp):
		super(_ViewProviderPlane, self).__init__(vp)
	def getIcon(self):
		return """
		    /* XPM */
			static const char * xpm[] = {
			"16 16 25 1",
			" 	c None",
			".	c #E9D5C9",
			"+	c #BC683B",
			"@	c #BA673A",
			"#	c #B96435",
			"$	c #FFAF72",
			"%	c #AD450C",
			"&	c #FFFFFF",
			"*	c #3A4049",
			"=	c #132F59",
			"-	c #D0CBCB",
			";	c #E1BCA7",
			">	c #425575",
			",	c #CBD0D9",
			"'	c #B55D2B",
			")	c #AF5D2E",
			"!	c #C7C7C7",
			"~	c #374E6F",
			"{	c #B45C2B",
			"]	c #C0AB9F",
			"^	c #D1D1D1",
			"/	c #B45D2C",
			"(	c #D2D2D2",
			"_	c #DCDCDC",
			":	c #B35C2B",
			"         .+     ",
			"       @#$%     ",
			"     @$$$$%     ",
			"   @$$$$$$%     ",
			" @$$$$$$$$%     ",
			"%$$$$$$$$$%     ",
			"%$$$$$$$$$%     ",
			"%$$$$&*$$$%     ",
			"%$$$$&*$$$%     ",
			"%$$$$$$==-;     ",
			"%$$$$$$$$>=,    ",
			"%$$$$$$')!!~=,  ",
			"%$$$${]     ^~=,",
			"%$$/]         (_",
			"%:]             ",
			"                "};
			"""

def makePlane(c, n, name):
	fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", getObjectName(name))
	fp.Label = name
	plane = _Plane(fp, c, n)
	if FreeCAD.GuiUp:
		_ViewProviderPlane(fp.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return fp

class _Sketch3D(object):
	def __init__(self, fp):
		fp.addProperty("App::PropertyPythonObject", "addGeometry").addGeometry = self.addGeometry
		fp.addProperty("App::PropertyPythonObject", "addConstraint").addConstraint = self.addConstraint
		fp.addProperty("App::PropertyPythonObject", "Geometry").Geometry = []
		fp.addProperty("App::PropertyPythonObject", "Constraint").Constraint = []
		self.fp = fp
		fp.Proxy = self

	def execute(self, fp):
		l = len(fp.Geometry)
		if (l == 0):
			fp.Shape = Part.Shape()
		elif (l == 1):
			fp.Shape = fp.Geometry[0].toShape()
		else:
			fp.Shape = Part.Compound([g.toShape() for g in fp.Geometry])

	def addGeometry(self, geometry, mode = False):
		index = len(self.fp.Geometry)
		self.fp.Geometry.append(geometry)
		return index

	def addConstraint(self, constraint):
		index = len(self.fp.Constraint)
		self.fp.Constraint.append(constraint)
		return index

class _ViewProviderSketch3D(_ViewProvider):
	def __init__(self, vp):
		super(_ViewProviderSketch3D, self).__init__(vp)

	def claimChildren(self):
		return []

	def getIcon(self):
		return getIconPath("Sketch3D.xpm")

def makeSketch3D(name = None):
	if (name is None):
		fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Sketch3D")
	else:
		fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", getObjectName(name))
		fp.Label = name
	sketch3D = _Sketch3D(fp)
	if (FreeCAD.GuiUp):
		_ViewProviderSketch3D(fp.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return fp
