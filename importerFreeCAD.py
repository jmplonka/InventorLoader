#!/usr/bin/env python

'''
importerFreeCAD.py
'''
import FreeCAD
import FreeCADGui
import Spreadsheet
import Part
import Draft
from FreeCAD import Base
from importerUtils   import logMessage, logWarning, LOG
from importerClasses import RSeMetaData, Angle
from math            import sqrt

__author__      = 'Jens M. Plonka'
__copyright__   = 'Copyright 2017, Germany'
__version__     = '0.1.0'
__status__      = 'In-Development'

def ignoreBranch(branch):
	return

def isXYPlane(a0):
	return (a0[0] == 0x8421 and a0[1] == 0x7BDE)

def isXZPlane(a0):
	return (a0[0] == 0x8241 and a0[1] == 0x7DBF)

def isYZPlane(a0):
	return (a0[0] == 0x8214 and a0[1] == 0x7DEB)

def createVector(x, y, z):
	return FreeCAD.Vector(x, y, z)

def createRotation(x, y, z, d):
	return FreeCAD.Rotation(x, y, z, d)

def createGroup(doc, name):
	grp = doc.addObject('App::DocumentObjectGroup', name)
	return grp

def isConstructionMode(node):
	return (len(node.getChildren(0x48EB8607))>0)

class FreeCADImporter:

	def __init__(self, root, doc):
		self.root      = root
		self.doc       = doc
		self.originObj = None

	def import_0DE8E459(self, branch):
		ignoreBranch(branch)
		return

	def importComAttr_022AC1B5(self, branch):
		ignoreBranch(branch)
		return

	def importComAttr_0244393C(self, branch):
		ignoreBranch(branch)
		return

	def importComAttr_189725D1(self, branch):
		ignoreBranch(branch)
		return

	def importComAttrUnknown(self, branch):
		logWarning('>W1002: don\'t know how to import common attribute - %08X!' %(branch.getKey()))
		return

	def importComAttr(self, attr):
		'''
		attr.u32   ???
		attr.u8    key?
		attr.list2 ???
		'''
		element = attr.first
		while (element):
			k = element.getKey()
			if (k == 0x022AC1B5):
				self.importComAttr_022AC1B5(element)
			elif (k == 0x0244393C):
				self.importComAttr_0244393C(element)
			elif (k == 0x189725D1):
				self.importComAttr_189725D1(element)
			else:
				self.importComAttrUnknown(element)
			element = element.next
		return

	def checkOriginObject(self):
		if (self.originObj is None):
			## FIXME: get Name from BrowserSegment...
			name = 'Mein Ursprung'
			self.originObj = createGroup(self.doc, name)
			if (self.root):
				self.root.addObject(self.originObj)
		return

	def addOriginObject(self, child):
		self.checkOriginObject()
		if (self.originObj):
			self.originObj.addObject(child)
		return

	def importWorkPlane(self, wPlane):
		p1 = wPlane.getVariable('a4')
		p2 = wPlane.getVariable('a5')
		a0 = wPlane.getVariable('CodedFloatA.a0')
		obj3d = wPlane.getFirstChild(0xA79EACCF)
		txt = obj3d.getFirstChild(0xA79EACD5)
		txtStr = txt.data.name
		l = (p2[0] - p1[0]) * 10.0
		w = (p2[1] - p1[1]) * 10.0
		x = -l / 2
		y = -w / 2

		## FIXME get the correct name!
		name = txtStr
		planeObj = self.doc.addObject('Part::Plane', name)
		planeObj.ViewObject.Transparency = 90
		planeObj.Length = l
		planeObj.Width  = w

		if (isXYPlane(a0)):
			logMessage('>I1140: importing Workplane XY-plane \'%s\' ...' %(txtStr), LOG.LOG_ALWAYS)
			planeObj.Placement=Base.Placement(Base.Vector(x, y, 0.0), Base.Rotation(0.0, 0.0, 0.0, 1.0))
			textObj = Draft.makeText(txtStr, point=createVector(x, y, 0.0))
			textObj.ViewObject.RotationAxis = 'Z'
			textObj.ViewObject.Rotation = 0
		elif (isYZPlane(a0)):
			logMessage('>I1141: importing Workplane YZ-plane \'%s\' ...' %(txtStr), LOG.LOG_ALWAYS)
 			planeObj.Placement=Base.Placement(Base.Vector(0.0, x, y), Base.Rotation(0.5, 0.5, 0.5, 0.5))
			textObj = Draft.makeText(txtStr, point=createVector(0.0, x, y))
			textObj.ViewObject.RotationAxis = 'Y'
			textObj.ViewObject.Rotation = -90
		else: # XZ Plane! - hopefully ;>
			logMessage('>I1141: importing Workplane XZ-plane \'%s\' ...' %(txtStr), LOG.LOG_ALWAYS)
			planeObj.Placement=Base.Placement(Base.Vector(x, 0.0, y), Base.Rotation(-sqrt(0.5), 0.0, 0.0, -sqrt(0.5)))
			textObj = Draft.makeText(txtStr, point=createVector(x, 0.0, y))
			textObj.ViewObject.RotationAxis = 'X'
			textObj.ViewObject.Rotation = 90

		textObj.ViewObject.FontSize = 0.20

		self.addOriginObject(planeObj)
		self.addOriginObject(textObj)

		return

	def importWorkAxis(self, wAxis):
# 		obj3d = wAxis.getFirstChild(0xA79EACCF)
# 		line = obj3d.getFirstChild(0xA79EACC7)
# 		a0 = wAxis.getVariable('a0')
# 		p1 = line.getVariable('p1')
# 		p2 = line.getVariable('p2')
# 		x1 = 0.0
# 		y1 = 0.0
# 		z1 = 0.0
# 		x2 = 0.0
# 		y2 = 0.0
# 		z2 = 0.0
#
# 		if (a0[4] == 7):
# 			x1 = p1[0] * 10
# 			x2 = p2[0] * 10
# 		elif (a0[4] == 8):
# 			y1 = p1[0] * 10
# 			y2 = p2[0] * 10
# 		else:
# 			z1 = p1[0] * 10
# 			z2 = p2[0] * 10
#
# 		logMessage('>I1170: importing Workaxis (%g/%g/%g)-(%g/%g/%g)...' %(x1, y1, z1, x2, y2, z2), LOG.LOG_ALWAYS)
# 		points = [createVector(x1, y1, z1), createVector(x2, y2, z2)]
# 		lineObj = Draft.makeWire(points,closed=False,face=True,support=None)
# 		self.addOriginObject(lineObj)
		ignoreBranch(wAxis)

		return

	def importWorkPoint(self, wPoint):
		ignoreBranch(wPoint)
		return

	def import_5EDE1890(self, branch):
		ignoreBranch(branch)
		return

	def import2dCircle(self, circle, sketchObj):
		m = circle.getVariable('m')
		x = m[0] * 10.0
		y = m[1] * 10.0
		r = circle.getVariable('r') * 10.0
		a = circle.getVariable('alpha')
		b = circle.getVariable('beta')
		logMessage('>I1130: ... adding 2D-Circle M=(%g/%g) R=%g alpha=%s beta=%s ...' %(x, y, r, a, b), LOG.LOG_ALWAYS)

		circleGeo = Part.Circle(createVector(x, y, 0), createVector(0, 0, 1), r)

		mode = isConstructionMode(circle)
		if ((a.x != 0) or (b.x != 360)):
			circleObj = sketchObj.addGeometry(Part.ArcOfCircle(circleGeo, Angle.grad2rad(a.x), Angle.grad2rad(b.x)), mode)
		else:
			circleObj = sketchObj.addGeometry(circleGeo, mode)

		return

	def import2dEllipse(self, ellipse, sketchObj):
		c = ellipse.getVariable('c')
		c_x = c[0] * 10.0
		c_y = c[1] * 10.0

		x = ellipse.getVariable('a')
		d = ellipse.getVariable('dA')
		a_x = c_x + (x * d[0] * 10.0)
		a_y = c_y + (x * d[1] * 10.0)

		x = ellipse.getVariable('b')
		d = ellipse.getVariable('dB')
		b_x = c_x + (x * d[0] * 10.0)
		b_y = c_y + (x * d[1] * 10.0)

		a = ellipse.getVariable('alpha')
		b = ellipse.getVariable('beta')
		logMessage('>I1130: ... adding 2D-Ellipse  c=(%g/%g) a=(%g/%g) b=(%g/%g) alpha=%s beta=%s ...' %(c_x, c_y, a_x, a_y, b_x, b_y, a, b), LOG.LOG_ALWAYS)

		vecA = createVector(a_x, a_y, 0.0)
		vecB = createVector(b_x, b_y, 0.0)
		vecC = createVector(c_x, c_y, 0.0)
		ellipseGeo = Part.Ellipse(vecA, vecB, vecC)

		mode = isConstructionMode(ellipse)
		if ((a.x != 0.0) or (b.x != 360.0)):
			ellipseObj = sketchObj.addGeometry(Part.ArcOfEllipse(ellipseGeo, Angle.grad2rad(a.x), Angle.grad2rad(b.x)), mode)
		else:
			ellipseObj = sketchObj.addGeometry(ellipseGeo, mode)

		return

	def import2dPoint(self, point, sketchObj):
		lst = point.getFirstChild(0x48EB8607)
		crd = lst.getFirstChild(0xB32BF6A7)
		p = crd.getVariable('vec')
		x = p[0] * 10.0
		y = p[1] * 10.0
		logMessage('>I1110: ... adding 2D-Point(%g/%g) ...' %(x, y), LOG.LOG_ALWAYS)

		mode = isConstructionMode(point)
		pointGeo = Part.Point(createVector(x, y, 0))
		pointObj = sketchObj.addGeometry(pointGeo, mode)

		return

	def import2dLine(self, line, sketchObj):
		p = line.getVariable('p1')
		x1 = p[0] * 10.0
		y1 = p[1] * 10.0

		p = line.getVariable('p2')
		x2 = p[0] * 10.0
		y2 = p[1] * 10.0
		logMessage('>I1160: ... adding 2D-Line (%g|%g)-(%g|%g) ...' %(x1, y1, x2, y2), LOG.LOG_ALWAYS)

		mode = isConstructionMode(line)
		lineGeo = Part.Line(createVector(x1, y1, 0), createVector(x2, y2, 0))
		lineObj = sketchObj.addGeometry(lineGeo, mode)

		return

	def import2dSpline(self, spline, sketchObj):
		## TODO!!!
		logMessage('>I1120: ... adding 2D-Spline ...', LOG.LOG_ALWAYS)
		# points=[createVector(-33.0, -4.0, 0.0), createVector(-18.0, -12.0, 0.0), createVector(-12.0, 14.0, 0.0), createVector(15.0, -13.0, 0.0)]
		# Draft.makeBSpline(points, closed=False, face=True, support=None)
		return

	def import2dSketch(self, sketch):
		## FIXME get the correct name!
		name = 'Sketch1'
		sketchObj = self.doc.addObject('Sketcher::SketchObject', name)
		a0 = sketch.getVariable('CodedFloatA.a0')
		if (isXYPlane(a0)):
			logMessage('>I1100: importing 2d-sketch on XY-plane ...', LOG.LOG_ALWAYS)
			rot = createRotation(0.0, 0.0, 0.0, 1.0)
		elif (isXZPlane(a0)):
			logMessage('>I1101: importing 2d-sketch on XZ-plane ...', LOG.LOG_ALWAYS)
			rot = createRotation(-sqrt(0.5), 0.0, 0.0, -sqrt(0.5))
		else:
			logMessage('>I1102: importing 2d-sketch on YZ-plane ...', LOG.LOG_ALWAYS)
			rot = createRotation(0.5, 0.5, 0.5, 0.5)
		sketchObj.Placement = FreeCAD.Placement(createVector(0.0, 0.0, 0.0), rot)

		elements =  sketch.getVariable('lst1')
		for key in elements:
			ref = key[1]
			element = sketch.getChild(ref.index)
			k = element.getKey()
			if (k == 0x120284EF):
				self.importComAttr(element)
			elif (k == 0x4B57DC55):
				self.import2dCircle(element, sketchObj)
			elif (k == 0x4B57DC56):
				self.import2dEllipse(element, sketchObj)
			elif (k == 0x50E809CD):
				self.import2dPoint(element, sketchObj)
			elif (k == 0xA79EACC7):
				self.import2dLine(element, sketchObj)
			elif (k == 0xA79EACCF):
				ignoreBranch(element)
			elif (k == 0xA79EACD3):
				ignoreBranch(element)
			elif (k == 0xA79EACD3):
				ignoreBranch(element)
			elif (k == 0xC0014C89):
				ignoreBranch(element)
			elif (k == 0xD3A55701):
				self.import2dSpline(element, sketchObj)
			else:
				logWarning('>W1006: don\'t know how to import 2DSketch objcet - %08X!' %(element.getKey()))

		if (self.root):
			self.root.addObject(sketchObj)

		return

	def import_8DA49A23(self, branch):
		ignoreBranch(branch)
		return

	def importNotice(self, notice):
		ignoreBranch(notice)
		return

	def importBody(self, body):
		ignoreBranch(body)
		return

	def import_A529D1E2(self, branch):
		ignoreBranch(branch)
		return

	def import_Extrusion(self, extrusion):
		logMessage('>I1100: importing Extrusion ...', LOG.LOG_ALWAYS)

		## FIXME get the correct name!
		name = 'Extrude'
#		extrusionGeo = Part.Extrusion()
#		extrusionObj = self.doc.addObject(extrusionGeo, name)
#		extrusionObj.Base = base
#		extrusionObj.Dir = (0.1, 0.2, 0.3)
#		extrusionObj.Solid = (True)
#		extrusionObj.TaperAngle = (0)
#		base.Visibility = False
#		if (self.root):
#			self.root.addObject(extrude)

		return

	def import3dSketch(self, sketch):
		##TODO
		ignoreBranch(sketch)
		return

	def import_DBE41D91(self, branch):
		ignoreBranch(branch)
		return

	def importPartModel(self, branch):
		child = branch.first
		while (child):
			k = child.getKey()
			if (k == 0x0DE8E459):
				self.import_0DE8E459(child)
			elif (k == 0x120284EF):
				self.importComAttr(child)
			elif (k == 0x14533D82):
				self.importWorkPlane(child)
			elif (k == 0x2C7020F6):
				self.importWorkAxis(child)
			elif (k == 0x2C7020F8):
				self.importWorkPoint(child)
			elif (k == 0x5EDE1890):
				self.import_5EDE1890(child)
			elif (k == 0x60FD1845):
				self.import2dSketch(child)
			elif (k == 0x8DA49A23):
				self.import_8DA49A23(child)
			elif (k == 0x9215A162):
				self.importNotice(child)
			elif (k == 0x9A676A50):
				self.importBody(child)
			elif (k == 0xA529D1E2):
				self.import_A529D1E2(child)
			elif (k == 0xA94779E0):
				self.import_Extrusion(child)
			elif (k == 0xDA58AA0E):
				self.import3dSketch(child)
			elif (k == 0xDBE41D91):
				self.import_DBE41D91(child)
			else:
				logWarning('>W1001: don\'t know how to import %08X!' %(child.getKey()))
			child = child.next
		return

	@staticmethod
	def findGraphics(storage):
		'''
		storage The map of defined RSeStorageDatas
		REturns the segment that contains the 3D-objects.
		'''
		if (storage):
			for name in storage.keys():
				seg = storage[name]
				if (RSeMetaData.isGraphics(seg)):
					return seg
		return None

	@staticmethod
	def findBrowser(storage):
		'''
		storage The map of defined RSeStorageDatas
		Returns the segment that contains the names of the objects.
		'''
		if (storage):
			for name in storage.keys():
				seg = storage[name]
				if (RSeMetaData.isBrowser(seg)):
					return seg
		return None

	def importModel(self, model):
		if (model):
			storage = model.RSeStorageData

			grx = FreeCADImporter.findGraphics(storage)
			brs = FreeCADImporter.findBrowser(storage)

			if (grx and brs):
				branch = grx.tree.first
				while (branch):
					if (branch.getKey() == 0xA529D1E2):
						child = branch.first
						while (child):
							if (child.getKey() == 0xCA7163A3):
								self.importPartModel(child)
							child = child.next
					branch = branch.next
				if (self.doc):
					self.doc.recompute()
			else:
				logWarning('>>>No content to be displayed<<<')

		return
