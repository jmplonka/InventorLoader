# -*- coding: utf-8 -*-

'''
InventorViewProviders.py
GUI representations for objectec imported from Inventor
'''

import os, re, sys, Part, Draft, FreeCAD, FreeCADGui
from importerUtils   import logInfo, getIconPath, getTableValue, setTableValue, logInfo, logWarning, logError, getCellRef, setTableValue, calcAliasname, isEqual1D
from FreeCAD         import Vector as VEC, Rotation as ROT, Placement as PLC
from importerClasses import ParameterTableModel, VariantTableModel
from math            import degrees, radians, pi, sqrt, cos, sin, atan
from PySide.QtCore   import *
from PySide.QtGui    import *
from importerConstants import DIR_X, DIR_Y, DIR_Z, CENTER

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
	'Diameter' : u'mm',
}

def getProfileFromSelection():
	edges = []
	selections = FreeCADGui.Selection.getSelectionEx(FreeCAD.ActiveDocument.Name)
	for selection in selections:
		for obj in selection.SubObjects:
			edges += obj.Edges
	return edges

def createPartFeature(doctype, name):
	iPart = FreeCAD.ActiveDocument.addObject(doctype, getObjectName(name))
	iPart.Label = name
	return iPart

def getObjectName(name):
	if (sys.version_info.major < 3):
		v = re.sub(r'[^\x00-\x7f]', r'_', name)
	else:
		v = re.sub(b'[^\x00-\x7f]', b'_', name.encode('utf8')).decode('utf8')
	if (INVALID_NAME.match(name)):
		return "_%s" %(v)
	return v

class _ObjectProxy(object):
	def __init__(self, obj):
		obj.Proxy   = self # allows invocation of execute function
		self.Object = obj

	def __getstate__(self):
		state = {}
		return state

	def __setstate__(self, state):
		return

class _ViewProvider(object):
	def __init__(self, vp):
		vp.Proxy = self

	def attach(self, vp):
		self.ViewObject = vp
		self.Object = vp.Object

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

def makeBoundaryPatch(edges, name = "BoundaryPatch"):
	bPatch = createPartFeature("Part::FeaturePython", name)
	bPatch.Shape = Part.Face(Part.Wire(edges))
	if FreeCAD.GuiUp:
		_ViewProviderBoundaryPatch(bPatch.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return bPatch

class _Stich(_ObjectProxy):
	def __init__(self, stich, solid, faces):
		super(_Stich, self).__init__(stich)
		stich.addProperty("App::PropertyBool",     "Solid", "Stitch", "Create a solid if possible")
		stich.addProperty("App::PropertyLinkList", "FaceList", "Stitch", "List of faces to stitch together")
		stich.Solid    = solid
		stich.FaceList = faces

	def execute(self, stich):
		faces = [f.Shape for f in stich.FaceList if not f.Shape is None]
		stich.Shape = Part.Shell(faces)
		if (stich.Solid):
			if (stich.Shape.isClosed()):
				stich.Shape = Part.Solid(stich.Shape)

class _ViewProviderStitch(_ViewProvider):
	def __init__(self, stich):
		super(_ViewProviderStitch, self).__init__(stich)

	def claimChildren(self):
		children = []
		if (hasattr(self.Object,"FaceList")):
			children += self.Object.FaceList
		return children

	def getIcon(self):
		return getIconPath('FxStitch.xpm')

def makeStitch(faces, name = u"FxStitch", solid = False):
	stich = createPartFeature("Part::FeaturePython", name)
	_Stich(stich, solid, faces)
	if FreeCAD.GuiUp:
		_ViewProviderStitch(stich.ViewObject)
	for face in faces:
		face.ViewObject.Visibility = False
	FreeCAD.ActiveDocument.recompute()
	return stich

class _Point(_ObjectProxy):
	def __init__(self, point, pt):
		super(_Point, self).__init__(point)
		point.addProperty("App::PropertyVector", "Point", "Draft", "Location")
		point.Point = pt

	def execute(self, point):
		vec = VEC(point.Point)
		point.Shape = Part.Vertex(vec)

class _ViewProviderPoint(_ViewProvider):
	def __init__(self, point):
		super(_ViewProviderPoint, self).__init__(point)

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

def makePoint(pt, name = u"Point"):
	point = createPartFeature("Part::FeaturePython", name)
	_Point(point, pt)
	if FreeCAD.GuiUp:
		_ViewProviderPoint(point.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return point

class _Line(_ObjectProxy):
	def __init__(self, line, pt1, pt2):
		super(_Line, self).__init__(line)
		line.addProperty("App::PropertyVector", "Start", "Line", "start point").Start = pt1
		line.addProperty("App::PropertyVector", "End", "Line", "end point").End = pt2

	def execute(self, line):
		pt1 = line.Start
		pt2 = line.End
		line.Shape = Part.makeLine(pt1, pt2)

class _ViewProviderLine(_ViewProvider):
	def __init__(self, vp):
		super(_ViewProviderLine, self).__init__(vp)

def makeLine(pt1, pt2, name = u"Line"):
	line = createPartFeature("Part::FeaturePython", name)
	_Line(line, pt1, pt2)
	if FreeCAD.GuiUp:
		_ViewProviderLine(line.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return line

class _Plane(_ObjectProxy):
	def __init__(self, plane, c, n):
		super(_Plane, self).__init__(plane)
		plane.addProperty("App::PropertyVector", "Center", "Plane", "center position").Center = c
		plane.addProperty("App::PropertyVector", "Normal", "Plane", "normal vector of the plane").Normal = n

	def execute(self, plane):
		c = plane.Center
		n = plane.Normal
		plane.Shape = Part.Plane(c, n).toShape()

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

def makePlane(c, n, name = u"Plane"):
	plane = createPartFeature("Part::FeaturePython", name)
	_Plane(plane, c, n)
	if FreeCAD.GuiUp:
		_ViewProviderPlane(plane.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return plane

class _Sketch3D(_ObjectProxy):
	def __init__(self, plane):
		super(_Sketch3D, self).__init__(plane)
		plane.addProperty("App::PropertyPythonObject", "addGeometry").addGeometry = self.addGeometry
		plane.addProperty("App::PropertyPythonObject", "addConstraint").addConstraint = self.addConstraint
		plane.addProperty("App::PropertyPythonObject", "Geometry").Geometry = []
		plane.addProperty("App::PropertyPythonObject", "Constraint").Constraint = []

	def execute(self, plane):
		l = len(plane.Geometry)
		if (l == 0):
			plane.Shape = Part.Shape()
		elif (l == 1):
			plane.Shape = plane.Geometry[0].toShape()
		else:
			plane.Shape = Part.Compound([g.toShape() for g in plane.Geometry])

	def addGeometry(self, geometry, mode = False):
		index = len(self.Object.Geometry)
		self.Object.Geometry.append(geometry)
		return index

	def addConstraint(self, constraint):
		index = len(self.Object.Constraint)
		self.Object.Constraint.append(constraint)
		return index

class _ViewProviderSketch3D(_ViewProvider):
	def __init__(self, sketch):
		super(_ViewProviderSketch3D, self).__init__(sketch)

	def claimChildren(self):
		children = []
		return children

	def getIcon(self):
		return getIconPath("Sketch3D.xpm")

def makeSketch3D(name = u"Sketch3D"):
	sketch = createPartFeature("Part::FeaturePython", name)
	_Sketch3D(sketch)
	if (FreeCAD.GuiUp):
		_ViewProviderSketch3D(sketch.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return sketch

class _PartVariants(_ObjectProxy):
	def __init__(self, fp):
		super(_PartVariants, self).__init__(fp)
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

		try:
			fp.Mapping.clear()
			FreeCAD.ActiveDocument.recompute()
			parameter  = self._getHeadersByRow_(fp.Parameters)
			for col in range(1, len(fp.Values[0])):
				hdr = fp.Values[0][col]
				cell = parameter.get(hdr, None)
				if cell is not None:
					fp.Mapping[col] = cell
				else:
					logWarning(f"PartVariants: UpdateMapping - wrong parameter name '{col}'! Please remove parameter!")
		except Exception as ex:
			FreeCAD.Console.PrintMessage(f"PartVariants: Failed to update mapping - {ex}!\n")
		return True

	def _updateVariant_(self, fp):
		try:
			if (not self._updateMapping_(fp)):
				return False
			r = fp.Rows[fp.Variant]
			FreeCAD.Console.PrintMessage(f"Set parameters according to variant '{fp.Variant}' (row={r}):\n")
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
		except Exception as ex:
			FreeCAD.Console.PrintMessage(f"PartVariants: Failed to update v - {ex}!\n")
			return False

	def _updateValues_(self, fp):
		try:
			colMember = -1
			values = fp.Values
			variants = [str(row[0]) for row in values[1:]]
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
#		self.form.height = self.form.sizeHint().height()

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
			self.form.height += 24
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
				logError(f"Failed to insert column {col}")
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
		hdrLst = [model.headerData(col, Qt.Horizontal, Qt.DisplayRole) for col in range(cols)]

		values.append(hdrLst)
		for row in range(rows):
			rowLst = [model.data(model.index(row, col), Qt.DisplayRole) for col in range(cols)]
			values.append(rowLst)

		self.fp.Values = values
		FreeCADGui.ActiveDocument.resetEdit()
		FreeCAD.ActiveDocument.recompute()
		return True

class _ViewProviderPartVariants(_ViewProvider):
	def __init__(self, iPart):
		super(_ViewProviderPartVariants, self).__init__(iPart)

	def claimChildren(self):
		children = []
		if (hasattr(self.Object,"Parameters")):
			children.append(self.Object.Parameters)
		if (hasattr(self.Object,"Values")):
			children.append(self.Object.Values)
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

def getExpression(obj, prp):
	expressions = obj.ExpressionEngine
	for xpr, value in expressions:
		if (xpr == prp):
			return value
	return None

def searchDocParameters(doc):
	values = []
	for obj in doc.Objects:
		if (not obj.TypeId in SKIPPABLE_OBJECTS):
			if (obj.TypeId == 'Sketcher::SketchObject'):
				for c, constraint in enumerate(obj.Constraints):
					if (constraint.Type in DIM_CONSTRAINTS):
						prp = 'Constraints[%d]' %(c)
						value = getExpression(obj, prp)
						if (value is None):
							value = constraint.Value
							if (constraint.Type == 'Angle'):
								value = degrees(value)
						values.append([False, obj.Name, prp, 'd_%d' %(len(values)), str(value), DIM_CONSTRAINTS[constraint.Type]])
			else:
				for prp in obj.PropertiesList:
					if (obj.getTypeIdOfProperty(prp) in XPR_PROPERTIES):
						value = getExpression(obj, prp)
						if (value is None):
							value = getattr(obj, prp)
							if (hasattr(value, 'Value')):
								value = value.Value
						values.append([False, obj.Name, prp, 'd_%d' %(len(values)), str(value), XPR_PROPERTIES[obj.getTypeIdOfProperty(prp)]])
	return values

def hasValue(table, cell, value):
	result = False
	try:
		result = (table.get(cell) == value)
	except:
		pass
	return result

def getParametersValues(doc):
	table  = None
	for t in doc.getObjectsByLabel('Parameters'):
		if (t.TypeId == 'Spreadsheet::Sheet'):
			table = t
			break
	if (table is None):
		return None, None, True
	if (hasValue(table, 'A1', 'Parameter') and hasValue(table, 'B1', 'Value')):
		logWarning("Spreadsheet 'Parameters' doesn't meet layout constraints to serve as parameters table!")
		logWarning("First row must be 'Parameter', 'Value', 'Unit', 'Source' - creating new one.")
		return None, None, True
	hasUnit     = hasValue(table, 'C1', 'Unit')
	hasSource   = hasValue(table, 'D1', 'Source')
	hasProperty = hasValue(table, 'E1', 'Property')
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
	row = 1
	for i, data in enumerate(values, 2):
		(add, source, property, name, value, unit) = data
		if (add):
			row = row + 1
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

def makePartVariants(name = u"Variations"):
	iPart = createPartFeature("Part::FeaturePython", name)
	_PartVariants(iPart)
	if (FreeCAD.GuiUp):
		_ViewProviderPartVariants(iPart.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return iPart

class _Trim(_ObjectProxy):
	def __init__(self, trim, patches):
		super(_Trim, self).__init__(trim)
		trim.addProperty("App::PropertyPythonObject", "Patches").Patches = patches
	def execute(self, trim):
		face = trim.Patches[0].Shape.Faces[0]
		trim = face.cut([p.Shape.Faces[0] for p in trim.Patches[1:]])
		trim.Shape = trim

class _ViewProviderTrim(_ViewProvider):
	def __init__(self, trim):
		super(_ViewProviderTrim, self).__init__(trim)

	def claimChildren(self):
		children = []
		if (hasattr(self.Object,"Patches")):
			children = self.Object.Patches
		return children

	def getIcon(self):
		return getIconPath('FxBoundaryPatch.xpm')

def makeTrim(name = u"Trim", faces = None):
	if (faces == None):
		selection = FreeCADGui.Selection.getSelectionEx(FreeCAD.ActiveDocument.Name)
		faces = []
		for selObj in selection:
			obj = selObj.Object
			if ((hasattr(obj.ViewObject, "Proxy")) and (obj.ViewObject.Proxy.__class__.__name__ == '_ViewProviderBoundaryPatch')):
				obj.ViewObject.Visibility = False
				faces.append(obj)

	trim = createPartFeature("Part::FeaturePython", name)
	_Trim(trim, faces)
	if FreeCAD.GuiUp:
		_ViewProviderTrim(trim.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return trim

class _Coil(_ObjectProxy):
	def __init__(self, coil, profile = None, base=CENTER, axis=DIR_Z,
			reversed=False, rotation='Clockwise', coil_type='PitchAndRevolution',
			taper_angle=0.0, solid=True, pitch=5.0, revolutions=4.0, height=20.0,
			start_flat=0.0, start_transit=0.0, end_flat=0.0, end_transit=0.0):
		super(_Coil, self).__init__(coil)
		coil.addProperty("App::PropertyLink"       , "Profile"     , "Base", "The profile for the coil")
		coil.addProperty("App::PropertyVector"     , "Axis"        , "Coil", "The direction of the coil's axis").Axis = axis
		coil.addProperty("App::PropertyVector"     , "Base"        , "Coil", "The origin of the coil").Base = base
		coil.addProperty("App::PropertyBool"       , "Reversed"    , "Coil", "Indicator for reversed direction").Reversed = reversed
		coil.addProperty("App::PropertyEnumeration", "Rotation"    , "Coil", "Sens of rotation").Rotation =['Clockwise', 'Counterclockwise']
		coil.addProperty("App::PropertyEnumeration", "CoilType"    , "Coil", "Specifies a pair of parameters").CoilType = ['PitchAndRevolution', 'RevolutionAndHeight', 'PitchAndHeight', 'Spiral']
		coil.addProperty("App::PropertyLength"     , "Pitch"       , "Coil", "The elevation gain for each revolution of the helix").Pitch = pitch
		coil.addProperty("App::PropertyLength"     , "Height"      , "Coil", "The height of the coil from the center of the profile at the start to the center of the profile at the end").Height= height
		coil.addProperty("App::PropertyFloat"      , "Revolutions" , "Coil", "The number of revolutions for the coil").Revolutions = revolutions
		coil.addProperty("App::PropertyAngle"      , "TaperAngle"  , "Coil", "The taper angle, if needed, for all coil types except spiral").TaperAngle = taper_angle # Cylinder!
		coil.addProperty("App::PropertyBool"       , "Solid"       , "Coil", "Create a solid instead of a shell").Solid = solid
		coil.addProperty("App::PropertyAngle"      , "StartTransit", "Ends", "The degrees over which the coil achieves the start transition (normally less than one revolution)").StartTransit = 0.0 #start_transit
		coil.addProperty("App::PropertyAngle"      , "StartFlat"   , "Ends", "The degrees the coil extends before transition with not pitch").StartFlat  = start_flat
		coil.addProperty("App::PropertyAngle"      , "EndTransit"  , "Ends", "The degrees over which the coil achieves the end transition (normally less than one revolution)").EndTransit = 0.0 #end_transit
		coil.addProperty("App::PropertyAngle"      , "EndFlat"     , "Ends", "The degrees the coil extends after transition with no pitch (flat)").EndFlat  = end_flat
		coil.setPropertyStatus('StartTransit', 'Hidden') # not yet implemented
		coil.setPropertyStatus('EndTransit', 'Hidden')   # not yet implemented
		coil.addExtension("Part::AttachExtensionPython")
		coil.Rotation = rotation
		coil.CoilType = coil_type
		if (profile):
			coil.Profile = profile
		return
	def onChanged(self, coil, prop):
		if prop == "CoilType":
			if (coil.CoilType == 'Spiral'):
				return _Coil._hide(coil, 'None') # dummy property to show all.
			if (coil.CoilType == 'PitchAndRevolution'):
				return _Coil._hide(coil, 'Height')
			if (coil.CoilType == 'RevolutionAndHeight'):
				return _Coil._hide(coil, 'Pitch')
			if (coil.CoilType == 'PitchAndHeight'):
				return _Coil._hide(coil, 'Revolutions')
		return
	def _createPathStart(self, coil):
		self.pathWires = []
		m = coil.Profile.Shape.BoundBox.Center # Center of the profile
		r = m.distanceToLine(coil.Base, coil.Base+coil.Axis)
		base = Part.Circle(coil.Base, coil.Axis, r)
		self.a = base.parameter(m)
		if (coil.StartFlat.Value > 0.0): # Angle of the flat part
			if (coil.Rotation == 'Counterclockwise'):
				b = self.a - radians(coil.StartFlat.Value)
				arc = Part.ArcOfCircle(base, b, self.a)
			else:
				b = self.a + radians(coil.StartFlat.Value)
				arc = Part.ArcOfCircle(base, self.a, b)
			self.a = b
			Part.show(arc.toShape(), "start")
			self.pathWires.append(arc.toShape())
#		if (coil.StartTransit.Value > 0.0):
#			if (coil.Rotation == 'Counterclockwise'):
#				b = self.a + radians(coil.StartTransit.Value)
#				transit = Draft.makeBSpline(points)
#			else:
#				b = self.a - radians(coil.StartTransit.Value)
#				transit = Draft.makeBSpline(points)
#			b = self.a + radians(coil.StartTransit.Value)
#			transit = Draft.makeBSpline(points)
#			self.a = b
#			self.pathWires.append(transit)

	def _createPathEnd(self, coil):
		if (coil.EndTransit.Value > 0) or  (coil.EndFlat.Value > 0):
			m = coil.Profile.Shape.BoundBox.Base # Center of the profile
			r = m.distanceToLine(coil.Base, coil.Base+coil.Axis)
			r -= coil.Height.Value * sin(radians(coil.TaperAngle.Value))
			base = Part.Circle(coil.Base, coil.Axis, r)
#			if (coil.EndTransit.Value > 0):
#				if (coil.Rotation == 'Counterclockwise'):
#					b = self.a + radians(coil.EndTransit.Value)
#				else:
#					b = self.a - radians(coil.EndTransit.Value)
#					transit = Draft.makeBSpline(points)
#				self.a = b
#				self.pathWires.append(transit)
			if (coil.EndFlat.Value > 0):
				if (coil.Rotation == 'Counterclockwise'):
					b = self.a - radians(coil.EndFlat.Value)
					arc = Part.ArcOfCircle(base, b, self.a)
				else:
					b = self.a + radians(coil.EndFlat.Value)
					arc = Part.ArcOfCircle(base, self.a, b)
				self.a = b
				Part.show(arc.toShape(), "end")
				self.pathWires.append(arc.toShape())

	def _createSpiral(self, coil):
		m = coil.Profile.Shape.BoundBox.Center # Center of the profile
		myNumRot = coil.Rotations.Value
		myRadius = m.distanceToLine(coil.Base, coil.Base+coil.Axis)
		myGrowth = coil.Growth
		myPitch  = 1.0
		myHeight = myNumRot * myPitch
		myAngle  = atan(myGrowth / myPitch)

		assert myGrowth > 0, u"Growth too small"
		assert myNumRot > 0, u"Number of rotations too small"

		aPnt = VEC(0.0, 0.0, 0.0)
		aDir = VEC(2.0 * pi, myPitch, 0.0)
		surf = Part.Cone(aPnt, DIR_Z, 1.0, 0.0)

		line = Part.LineSegment(aPnt, aDir)
		beg = line.value(0)
		end = line.value(aDir.Length * myNumRot)

		# calculate end point for conical helix
		v = myHeight / cos(myAngle)
		u = myNumRot * 2.0 * pi
		segm = Part.LineSegment(beg , VEC(u, v, 0))

		edgeOnSurf = surf.project(segm)
		wire = edgeOnSurf.toShape()

		aPlane = Part.Plane(aPnt, DIR_Z)
		rng = (myNumRot+1) * myGrowth + 1 + myRadius
		return aPlane.toShape().project(wire)

	def _createHelix(self, coil):
		line = Part.Line(coil.Base, coil.Base + coil.Axis)
		radius = line.projectPoint(coil.Profile.Shape.CenterOfMass, "LowerDistance")
		angle = coil.TaperAngle.Value
		hand = (coil.Rotation == 'Counterclockwise')
		helix = Part.makeHelix(coil.Pitch.Value, coil.Height.Value, radius, angle, hand)
		# rotate helix'axis from (0, 0, 1) to coil's 'axis
		axis =-coil.Axis if (coil.Reversed) else coil.Axis
		angle = degrees(DIR_Z.getAngle(axis))
		if (not isEqual1D(angle, 0)):
			rotation_axis = DIR_Z.cross(axis) if not isEqual1D(angle, 180) else DIR_X
			helix.rotate(CENTER, rotation_axis, angle)
		# move helix from (0,0,0) to base
		helix.translate(coil.Base)
		# rotate helix's start to coil's profile' center
		helix.rotate(coil.Base, axis, degrees(self.a))
		self.pathWires += helix.Edges
		return helix

	@staticmethod
	def _hide_Property(coil, property, name):
		hidden = 'Hidden' if (property == name) else '-Hidden'
		try:
			coil.setPropertyStatus(name, hidden)
		finally:
			return
	@staticmethod
	def _hide(coil, property):
		_Coil._hide_Property(coil, property, 'Pitch')
		_Coil._hide_Property(coil, property, 'Revolutions')
		_Coil._hide_Property(coil, property, 'Height')
		return

	def _createPitchAndRevolution(self, coil):
		assert coil.Pitch.Value > 0, "Pitch must be greater than zero!"
		assert coil.Revolutions > 0, "Revolutions must be greater than zero!"
		coil.Height = coil.Pitch.Value * coil.Revolutions
		return self._createHelix(coil)

	def _createRevolutionAndHeight(self, coil):
		assert coil.Revolutions > 0, "Revolutions must be greater than zero!"
		assert coil.Height.Value > 0, "Height mus be greater than zero!"
		coil.Pitch = coil.Height.Value / coil.Revolutions
		return self._createHelix(coil)

	def _createPitchAndHeight(self, coil):
		assert coil.Pitch > 0, "Pitch must be greater than zero!"
		assert coil.Height > 0, "Height mus be greater than zero!"
		coil.Revolutions = coil.Height.Value / coil.Pitch.Value
		return self._createHelix(coil)

	def _createPathMain(self, coil):
		if (coil.CoilType == 'Spiral'):
			return self._createSpiral(coil)
		if (coil.CoilType == 'PitchAndRevolution'):
			return self._createPitchAndRevolution(coil)
		if (coil.CoilType == 'RevolutionAndHeight'):
			return self._createRevolutionAndHeight(coil)
		if (coil.CoilType == 'PitchAndHeight'):
			return self._createPitchAndHeight(coil)
		raise Exception(u"Unknown Coil-Type '%s'" %(coil.CoilType))

	def _createCoil(self, coil):
		# loft the profile along the path
		try:
			path = Part.Wire(self.pathWires)
			coil.Shape = path.makePipeShell(coil.Profile.Shape.Wires, coil.Solid, True)
		finally:
			return

	def execute(self, coil):
		# Part.ArcOfCircle for Coil's flat ends regardless of the taper angle
		# Part.??? for coil's transition ends
		# Part.makeLongHelix for Coil with with pitch, height, radius, angle, handed

		# Radius of the coil
		self._createPathStart(coil)
		self._createPathMain(coil)
		self._createPathEnd(coil)
		self._createCoil(coil)

class _ViewProviderCoil(_ViewProvider):
	def __init__(self, coil):
		super(_ViewProviderCoil, self).__init__(coil)

	def claimChildren(self):
		children = []
		if (hasattr(self.Object,"Profile")):
			children.append(self.Object.Profile)
		return children

	def getIcon(self):
		return getIconPath('FxCoil.png')

def makeCoil(name = u"Coil", profile=None, base=CENTER, axis=DIR_Z,
			reversed=False, rotation='Clockwise', coil_type='PitchAndRevolution',
			taper_angle=0.0, solid=True, pitch=5.0, turns=4.0, height=20.0,
			start_flat=0.0, start_transit=0.0, end_flat=0.0, end_transit=0.0):
	if (profile is None):
		selection = FreeCADGui.Selection.getSelection()
		if (selection):
			profile = selection[0]

	coil = createPartFeature("Part::FeaturePython", name)
	_Coil(coil, profile, base, axis, reversed, rotation, coil_type, taper_angle, solid, pitch, turns, height, start_flat, start_transit, end_flat, end_transit)
	if FreeCAD.GuiUp:
		_ViewProviderCoil(coil.ViewObject)
	profile.Visibility = False
	return coil
