# -*- coding: utf-8 -*-

'''
InventorViewProviders.py
GUI representations for objectec imported from Inventor
'''

import os, re, sys, Part, FreeCAD, FreeCADGui
from importerUtils   import logInfo, getIconPath, getTableValue, setTableValue, logInfo, logWarning, logError, getCellRef, setTableValue, calcAliasname
from FreeCAD         import Vector as VEC
from importerClasses import ParameterTableModel, VariantTableModel
from math            import degrees
from PySide.QtCore   import *
from PySide.QtGui    import *

INVALID_NAME   = re.compile('^[0-9].*')
SKIPPABLE_OBJECTS = [
	'Spreadsheet::Sheet'
]
XPR_PROPERTIES = {
	'App::PropertyInteger' : u'',
	'App::PropertyFloat'   : u'',
	'App::PropertyQuantity': u'',
	'App::PropertyAngle'   : u'°',
	'App::PropertyDistance': u'mm',
	'App::PropertyLength'  : u'mm',
	'App::PropertyPercent' : u'%',
}
DIM_CONSTRAINTS = {
	'Angle'    : u'°',
	'Distance' : u'mm',
	'DistanceX': u'mm',
	'DistanceY': u'mm',
	'Radius'   : u'mm',
}

def createPartFeature(doctype, name, default):
	if (name is None):
		fp = FreeCAD.ActiveDocument.addObject(doctype, default)
	else:
		fp = FreeCAD.ActiveDocument.addObject(doctype, getObjectName(name))
		fp.Label = name
	return fp

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
	fp = createPartFeature("Part::FeaturePython", name, "BoundaryPatch")
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
		faces = [f.Shape for f in fp.FaceList if not f.Shape is None]
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
	fp = createPartFeature("Part::FeaturePython", name, "FxStitch")
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
	fp = createPartFeature("Part::FeaturePython", name, "Point")
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
	fp = createPartFeature("Part::FeaturePython", name, "Line")
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
	fp = createPartFeature("Part::FeaturePython", name, "Plane")
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
	fp = createPartFeature("Part::FeaturePython", name, "Sketch3D")
	sketch3D = _Sketch3D(fp)
	if (FreeCAD.GuiUp):
		_ViewProviderSketch3D(fp.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return fp

class _PartVariants(object):
	def __init__(self, fp):
		fp.addProperty("App::PropertyPythonObject", "Values")
		fp.addProperty("App::PropertyPythonObject", "Rows").Rows = {}
		fp.addProperty("App::PropertyPythonObject", "Mapping").Mapping = {}
		fp.addProperty("App::PropertyPythonObject", "Proxy").Proxy = self
		fp.addProperty("App::PropertyLink"        , "Parameters")
		fp.addProperty("App::PropertyEnumeration" , "Variant", "iPart")

	def _getHeadersByRow_(self, table):
		headers = {}
		row = 2 # Skip header row
		header = getTableValue(table, 'A', row)
		while (header):
			headers[header] = row
			row += 1
			header = getTableValue(table, 'A', row)

		return headers

	def _updateMapping_(self, fp):
		if (fp.Values is None): return False
		if (fp.Parameters is None): return False

		fp.Mapping.clear()
		FreeCAD.ActiveDocument.recompute()
		parameter  = self._getHeadersByRow_(fp.Parameters)
		for col in range(1, len(fp.Values[0])):
			hdr = fp.Values[0][col]
			cell = parameter[hdr]
			fp.Mapping[col] = cell

		return True

	def _updateVariant_(self, fp):
		try:
			if (not self._updateMapping_(fp)):
				return False
			r = fp.Rows[fp.Variant]
			FreeCAD.Console.PrintMessage("Set parameters according to variant '%s' (row %d):\n" %(fp.Variant, r))
			for col in fp.Mapping:
				prm = fp.Values[0][col]
				val = fp.Values[r][col]
				if (hasattr(val, 'Value')):
					val = val.Value
				setTableValue(fp.Parameters, 'B', fp.Mapping[col], val)
				FreeCAD.Console.PrintMessage("    '%s' = %s\n" %(prm, val))
			if (FreeCAD.ActiveDocument):
				FreeCAD.ActiveDocument.recompute()
			return True
		except:
			return False

	def _updateValues_(self, fp):
		try:
			colMember = -1
			values = fp.Values
			variants = [row[0] for row in values[1:]]
			fp.Rows.clear()
			for row, variant in enumerate(variants, 1):
				fp.Rows[variant] = row
			fp.Variant = variants
		except:
			pass

	def onChanged(self, fp, prop):
		if (prop == 'Variant'):
			self._updateVariant_(fp)
		elif (prop == 'Values'):
			self._updateValues_(fp)

class DlgIPartVariants(object):
	def __init__(self, fp):
		res = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources")
		ui  = os.path.join(res, "ui", "iPartVariants.ui")
		self.form = FreeCADGui.PySideUic.loadUi(ui)
		table = self.form.tableView
		table.setSelectionMode(QAbstractItemView.SingleSelection)
		self.form.btnPartAdd.setIcon(QIcon(os.path.join(res, "icons", "iPart_Part_add.svg")))
		self.form.btnPartDel.setIcon(QIcon(os.path.join(res, "icons", "iPart_Part_del.svg")))
		self.form.btnParamAdd.setIcon(QIcon(os.path.join(res, "icons", "iPart_Param_add.svg")))
		self.form.btnParamDel.setIcon(QIcon(os.path.join(res, "icons", "iPart_Param_del.svg")))
		QObject.connect(self.form.btnPartAdd, SIGNAL("clicked()"), self.addPart)
		QObject.connect(self.form.btnPartDel, SIGNAL("clicked()"), self.delPart)
		QObject.connect(self.form.btnParamAdd, SIGNAL("clicked()"), self.addParam)
		QObject.connect(self.form.btnParamDel, SIGNAL("clicked()"), self.delParam)
		VariantTableModel(table, fp.Values)
		self.fp = fp
	def getParameters(self):
		parameters = []
		table = self.fp.Parameters
		row = 2
		parameter = getTableValue(table, 'A', row)
		while (parameter):
			parameters.append(parameter)
			row += 1
			parameter = getTableValue(table, 'A', row)
		return parameters
	def addPart(self):
		table = self.form.tableView
		model = table.model()
		rows  = model.rowCount(table)
		index = table.currentIndex()
		if (index.isValid()):
			row = index.row() + 1
		else:
			row = rows
		if (model.insertRow(row)):
			index = model.index(row, 0)
			model.setData(index, 'Part-%02d' %(rows+1), Qt.EditRole)
			FreeCAD.ActiveDocument.recompute()
		else:
			logError("Failed to insert row %d", row)
		return
	def delPart(self):
		table = self.form.tableView
		model = table.model()
		index = table.currentIndex()
		if (index.isValid()):
			row   = index.row()
			ret   =  QMessageBox.question(self.form, "FreeCAD - remove part variant",
				   u"Do you really want to remove '%s'?" %(model.data(model.index(row, 0), Qt.DisplayRole)),
				   QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
			if (ret == QMessageBox.Yes):
				model.removeRow(row)
		FreeCAD.ActiveDocument.recompute()
		return
	def addParam(self):
		parameters = self.getParameters()
		(prmName, ok) = QInputDialog.getItem(None, u"FreeCAD - add iPart parameter", u"Name of the parameter:", parameters)
		if (ok):
			table = self.form.tableView
			model = table.model()
			cols  = model.columnCount(table)
			index = table.currentIndex()
			if (index.isValid()):
				col = index.column() + 1
			else:
				col = cols
			if (model.insertColumn(col)):
				model.setHeaderData(col, Qt.Horizontal, prmName, Qt.DisplayRole)
				FreeCAD.ActiveDocument.recompute()
			else:
				logError("Failed to insert column %d", row)
		return
	def delParam(self):
		table = self.form.tableView
		model = table.model()
		index = table.currentIndex()
		if (index.isValid()):
			col = index.column()
			ret =  QMessageBox.question(self.form, "FreeCAD - remove iPart parameter",
				   u"Do you really want to remove '%s'?" %(model.headerData(col, Qt.Horizontal, Qt.DisplayRole)),
				   QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
			if (ret == QMessageBox.Yes):
				model.removeColumn(col)
		return
	def reject(self):
		FreeCADGui.ActiveDocument.resetEdit()
		return True
	def accept(self):
		table  = self.form.tableView
		model  = table.model()
		values = []
		cols   = model.columnCount(table)
		rows   = model.rowCount(table)
		hdrLst = []
		for col in range(cols):
			hdrLst.append(model.headerData(col, Qt.Horizontal, Qt.DisplayRole))
		values.append(hdrLst)
		for row in range(rows):
			rowLst = []
			for col in range(cols):
				index = model.index(row, col)
				rowLst.append(model.data(index, Qt.DisplayRole))
			values.append(rowLst)
		self.fp.Values = values
		FreeCADGui.ActiveDocument.resetEdit()
		FreeCAD.ActiveDocument.recompute()
		return True

class _ViewProviderPartVariants(_ViewProvider):
	def __init__(self, vp):
		super(_ViewProviderPartVariants, self).__init__(vp)

	def claimChildren(self):
		children = []
		if (not self.fp.Parameters is None):
			children.append(self.fp.Parameters)
		if (not self.fp.Values is None):
			children.append(self.fp.Values)
		return children

	def setEdit(self, vobj=None, mode=0):
		if mode == 0:
			if vobj is None:
				vobj = self.vobj
			fp = vobj.Object
			FreeCADGui.Control.closeDialog()
			FreeCADGui.Control.showDialog(DlgIPartVariants(fp))
			return True
		return False

	def unsetEdit(self, vobj, mode):
		FreeCADGui.Control.closeDialog()
		return False

	def getIcon(self):
		return getIconPath("iPart-VO.png")

def searchDocParameters(doc):
	values = []
	d = 0
	for obj in doc.Objects:
		if (not obj.TypeId in SKIPPABLE_OBJECTS):
			if (obj.TypeId == 'Sketcher::SketchObject'):
				c = 0
				for constraint in obj.Constraints:
					if (constraint.Type in DIM_CONSTRAINTS):
						value = constraint.Value
						if (constraint.Type == 'Angle'):
							value = degrees(value)
						values.append([False, obj.Name, 'Constraints[%d]' %(c), 'd_%d' %(d), str(value), DIM_CONSTRAINTS[constraint.Type]])
						d += 1
					c += 1
			else:
				for prp in obj.PropertiesList:
					if (obj.getTypeIdOfProperty(prp) in XPR_PROPERTIES):
						value = getattr(obj, prp)
						if (hasattr(value, 'Value')):
							value = value.Value
						values.append([False, obj.Name, prp, 'd_%d' %(d), str(value), XPR_PROPERTIES[obj.getTypeIdOfProperty(prp)]])
						d += 1
	return values

def getParametersValues(doc):
	table  = None
	for t in doc.getObjectsByLabel('Parameters'):
		if (t.TypeId == 'Spreadsheet::Sheet'):
			table = t
			break
	if (table is None):
		return None, None, True
	if ((table.get('A1') != 'Parameter') or (table.get('B1') != 'Value')):
		logWarning("Spreadsheet 'Parameters' doesn't meet layout constraints to serve as parameters table!")
		logWarning("First row must be 'Parameter', 'Value', 'Unit', 'Source' - creating new one.")
		return None, None, True
	hasUnit     = (table.get('C1') == 'Unit')
	hasSource   = (table.get('D1') == 'Source')
	hasProperty = (table.get('E1') == 'Property')
	row         = 2
	values      = []
	while (True):
		name     = getTableValue(table, 'A', row)
		if (name is None):
			break
		value    = getTableValue(table, 'B', row)
		unit = None
		if (hasUnit):
			unit = getTableValue(table, 'C', row)
		else:
			unit = table.get(getCellRef('B', row))
			if (hasattr(unit, 'getUserPreferred')):
				unit = unit.getUserPreferred()[2]
			else:
				unit = None
		source = None
		if (hasSource):
			source = getTableValue(table, 'D', row)
		property = None
		if (hasProperty):
			property = getTableValue(table, 'E', row)
		values.append([False, source, property, name, value, unit])
		row += 1
	return table, values, False

def createIPartParameters(doc, values):
	table = doc.addObject('Spreadsheet::Sheet', 'Parameters')
	table.set('A1', 'Parameter')
	table.set('B1', 'Value')
	table.set('C1', 'Unit')
	table.set('D1', 'Source')
	table.set('E1', 'Property')
	for row, data in enumerate(values, 2):
		(add, source, property, name, value, unit) = data
		setTableValue(table, 'A', row, name)
		try:
			setTableValue(table, 'B', row, float(value))
		except:
			setTableValue(table, 'B', row, '=%s' %(value))
		setTableValue(table, 'C', row, unit)
		setTableValue(table, 'D', row, source)
		setTableValue(table, 'E', row, property)
		# replace value by expression
		table.setAlias(u"B%d" %(row), calcAliasname(name))
	doc.recompute()
	return table

def createIPart():
	doc    = FreeCAD.ActiveDocument
	table, values, create = getParametersValues(doc)
	if (values is None):
		values = searchDocParameters(doc)

	form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources", "ui", "iPartParameters.ui"))
	ParameterTableModel(form.tableView, values)
	if (not form.exec_()):
		return None

	if (create):
		table = createIPartParameters(doc, values)

	headers  = ['Member']  # fixed key for part variant name
	variant  = ['Part-01'] # default name of the variant
	variants = [headers, variant]
	for data in values:
		(add, source, property, name, value, unit) = data
		if ((not source is None) and (not property is None)):
			obj = doc.getObject(source)
			obj.setExpression(property, "%s.%s" %(table.Name, calcAliasname(name)))
		if (add):
			variant.append(value)
			headers.append(name)

	fp = makePartVariants()
	fp.Parameters = table
	fp.Values     = variants
	doc.recompute()
	return fp

def makePartVariants(name = None):
	fp = createPartFeature("Part::FeaturePython", name, "Variations")
	iPart = _PartVariants(fp)
	if (FreeCAD.GuiUp):
		_ViewProviderPartVariants(fp.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return fp