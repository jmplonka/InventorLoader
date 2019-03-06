# -*- coding: utf-8 -*-

'''
InventorWorkbench.py
'''

import os, FreeCAD, FreeCADGui
from InventorViewProviders import *
from FreeCADGui            import Workbench, addCommand
from importerUtils         import getIconPath
from PySide.QtGui          import QMessageBox
from PySide.QtCore         import Qt

_SEPARATOR_  = 'Separator'
PREFIX = 'InventorLoader_'
# Sketch
_SKETCH_2D_           = PREFIX + 'Sketch2D'
_SKETCH_3D_           = PREFIX + 'Sketch3D'
_SKETCH_BLOCK_        = PREFIX + 'SketchBlock'      # FX missing
_SKETCHES_            = PREFIX + 'Sketches'
# Create
_FX_EXTRUDE_          = PREFIX + 'FxExtrude'
_FX_REVOLVE_          = PREFIX + 'FxRevolve'
_FX_LOFT_             = PREFIX + 'FxLoft'
_FX_SWEEP_            = PREFIX + 'FxSweep'
_FX_RIB_              = PREFIX + 'FxRib'             # FX missing
_FX_COIL_             = PREFIX + 'FxCoil'            # FX missing
_FX_EMBOSS_           = PREFIX + 'FxEmboss'          # FX missing
_PRIMITIVE_BOX_       = PREFIX + 'PrimitiveBox'
_PRIMITIVE_CYLINDER_  = PREFIX + 'PrimitiveCylinder'
_PRIMITIVE_SPHERE_    = PREFIX + 'PrimitiveShpere'
_PRIMITIVE_CONE_      = PREFIX + 'PrimitiveCone'
_PRIMITIVE_ELLIPSOID_ = PREFIX + 'PrimitiveEllipsoid'
_PRIMITIVE_TORUS_     = PREFIX + 'PrimitiveTorus'
_PRIMITIVE_PRISM_     = PREFIX + 'PrimitivePrism'
_PRIMITIVE_WEDGE_     = PREFIX + 'PrimitiveWedge'
_PRIMITIVES_          = PREFIX + 'Primitives'
# Modify
_FX_HOLE_             = PREFIX + 'FxHole'
_FX_FILLET_           = PREFIX + 'FxFillet'
_FX_CHAMFER_          = PREFIX + 'FxChamfer'
_FX_SHELL_            = PREFIX + 'FxShell'           # FX Missing
_FX_DRAFT_            = PREFIX + 'FxDraft'           # FX Missing
_FX_THREAD_           = PREFIX + 'FxThread'          # FX Missing
_FX_SPLIT_            = PREFIX + 'FxSplit'           # FX Missing
_FX_COMBINE_          = PREFIX + 'FxCombine'
_FX_MOVE_FACE_        = PREFIX + 'FxFaceMove'        # FX missing
_FX_COPY_OBJECT_      = PREFIX + 'FxCopyObject'      # FX missing
_FX_MOVE_BODY_        = PREFIX + 'FxMove'            # FX missing
# Pattern
_FX_RECTANGULAR_      = PREFIX + 'FxPatternRectangular'
_FX_CIRCULAR_         = PREFIX + 'FxPatternPolar'
_FX_SKETCH_DRIVEN_    = PREFIX + 'FxPatternSketchDriven'
_FX_MIRROR_           = PREFIX + 'FxMirror'
# Surface
_FX_THICKEN_          = PREFIX + 'FxThicken'
_FX_STITCH_           = PREFIX + 'FxStitch'
_FX_SCULPT_           = PREFIX + 'FxSculpt'          # FX missing
_FX_PATCH_            = PREFIX + 'FxBoundaryPatch'
_FX_TRIM_             = PREFIX + 'FxTrim'            # FX missing
_FX_DELETE_FACE_      = PREFIX + 'FxFaceDelete'      # FX missing
_FX_REPLACE_FACE_     = PREFIX + 'FxFaceReplace'     # FX missing
_FX_EXTEND_FACE_      = PREFIX + 'FxFaceExtend'      # FX missing
_FX_RULED_SURFACE_    = PREFIX + 'FxRuledSurface'    # FX missing
# Plastic parts
_FX_GRILL_            = PREFIX + 'FxGrill'           # FX missing
_FX_BOSS_             = PREFIX + 'FxBoss'            # FX missing
_FX_REST_             = PREFIX + 'FxRest'            # FX missing
_FX_SNAP_FIT_         = PREFIX + 'FxSnapFit'         # FX missing
_FX_RULE_FILLET_      = PREFIX + 'FxFilletRule'      # FX missing
_FX_LIP_              = PREFIX + 'FxLip'             # FX missing
# Freeform
_FREEFORM_BOX_        = PREFIX + 'FreeformBox'       # FX missing
_FREEFORM_PLANE_      = PREFIX + 'FreeformPlane'     # FX missing
_FREEFORM_CYLINDER    = PREFIX + 'FreeformCylinder'  # FX missing
_FREEFORM_SPHERE      = PREFIX + 'FreeformSphere'    # FX missing
_FREEFORM_TORUS       = PREFIX + 'FreeformTorus'     # FX missing
_FREEFORM_QUAD_BALL   = PREFIX + 'FreeformQuadBall'  # FX missing
_FREEFORMS_           = PREFIX + 'Freeforms'
# Sheet-Metal
_SHEET_METAL_FACE_    = PREFIX + 'FxFace'          # FX missing
_SHEET_METAL_FLANGE_  = PREFIX + 'FxFlange'        # FX missing
_SHEET_METAL_CONTOUR_ = PREFIX + 'FxFlangeContour' # FX missing
_SHEET_METAL_LOFTED_  = PREFIX + 'FxLoftedFlange'  # FX missing
_SHEET_METAL_FLANGES_ = PREFIX + 'FxFlanges'
_SHEET_METAL_ROLL_    = PREFIX + 'FxContourRoll'   # FX missing
_SHEET_METAL_HEM_     = PREFIX + 'FxHem'           # FX missing
_SHEET_METAL_BEND_    = PREFIX + 'FxBend'          # FX missing
_SHEET_METAL_FOLD_    = PREFIX + 'FxFold'          # FX missing
_SHEET_METAL_CUT_     = PREFIX + 'FxCut'           # FX missing
_SHEET_METAL_CORNER_  = PREFIX + 'FxCorner'        # FX missing
_SHEET_METAL_RIP_     = PREFIX + 'FxRip'           # FX missing
_SHEET_METAL_UNFOLD_  = PREFIX + 'FxUnfold'        # FX missing
_SHEET_METAL_REFOLD_  = PREFIX + 'FxRefold'        # FX missing

# others
_I_PART_              = PREFIX + 'iPart'
_FX_DIRECT_EDIT_      = PREFIX + 'FxDirectEdit'      # FX missing

def runPartDesignCommand(cmd):
	import PartDesign
	doc  = FreeCAD.ActiveDocument
	if (doc):
		view = FreeCADGui.ActiveDocument
		if (len(doc.findObjects('PartDesign::Body')) < 1):
			body = doc.addObject('PartDesign::Body','Body')
			view .setActiveObject('pdbody', body)
			FreeCADGui.Selection.clearSelection()
			Gui.Selection.addSelection(body)
			doc.recompute()
			FreeCADGui.runCommand(cmd)
	return

def createPrimitive(name):
	import PartDesign
	doc = FreeCAD.ActiveDocument
	if (doc):
		view = FreeCADGui.ActiveDocument
		body = doc.addObject('PartDesign::Body', 'Body')
		view.setActiveObject('pdbody', body)
		box = doc.addObject('PartDesign::Additive' + name, name)
		doc.Body.addObject(box)
		doc.recompute()
		box.ViewObject.ShapeColor  =body.ViewObject.ShapeColor
		box.ViewObject.LineColor   =body.ViewObject.LineColor
		box.ViewObject.PointColor  =body.ViewObject.PointColor
		box.ViewObject.Transparency=body.ViewObject.Transparency
		box.ViewObject.DisplayMode =body.ViewObject.DisplayMode
		view.setEdit(box.Name)

class _CmdAbstract(object):
	def __init__(self, menuText = None, toolTip = None, pixmap = None, accel=None):
		super(_CmdAbstract, self).__init__()
		self.resources = {}
		self.addResource('MenuText', menuText)
		self.addResource('ToolTip',  toolTip)
		self.addResource('Pixmap',   pixmap)
		self.addResource('Accel',    accel)
	def addResource(self, resource, value):
		if (not value is None):
			self.resources[resource] = value
	def GetResources(self):
		return self.resources
	def IsActive(self):
		return not (FreeCAD.ActiveDocument is None)
	def Activated(self):
		dlg = QMessageBox(QMessageBox.Information, 'FreeCAD: Inventor workbench...', 'Command not ' + self.__class__.__name__ + ' yet implemented!')
		dlg.setWindowModality(Qt.ApplicationModal)
		dlg.exec_()

# Sketch
class _CmdSketch2D(_CmdAbstract):
	def __init__(self):
		super(_CmdSketch2D, self).__init__(menuText="&2D Sketch", toolTip="Creates an 2D sketch", pixmap=getIconPath("Sketch2D.png"), accel="I, 2")
	def Activated(self):
		if FreeCAD.ActiveDocument:
			import Sketcher
			FreeCADGui.runCommand("Sketcher_NewSketch")
class _CmdSketch3D(_CmdAbstract):
	def __init__(self):
		super(_CmdSketch3D, self).__init__(menuText="&3D Sketch", toolTip="Creates an 3D sketch", pixmap=getIconPath("Sketch3D.png"), accel="I, 3")
	def Activated(self):
		if FreeCAD.ActiveDocument:
			makeSketch3D()
class _CmdSketchBlock(_CmdAbstract):
	def __init__(self):
		super(_CmdSketchBlock, self).__init__(menuText="Sketch-&Block", toolTip="Creates an sketch block", pixmap=getIconPath("SketchBlock.png"), accel="I, B")
class _CmdSketches(_CmdAbstract):
	def __init__(self):
		super(_CmdSketches, self).__init__(menuText='Create sketch', toolTip='Create sketches')
	def GetCommands(self):
		return tuple([_SKETCH_2D_, _SKETCH_3D_])
	def GetDefaultCommand(self):
		return 0 # by default 2D sketches

# Create
class _CmdFxExtrude(_CmdAbstract):
	def __init__(self):
		super(_CmdFxExtrude, self).__init__(menuText="&Extrude", toolTip="extrude a profile", pixmap=getIconPath("FxExtrude.png"), accel="I, E")
	def Activated(self):
		runPartDesignCommand("PartDesign_Pad")
class _CmdFxRevolve(_CmdAbstract):
	def __init__(self):
		super(_CmdFxRevolve, self).__init__(menuText="&Revolve", toolTip="revolve a profile", pixmap=getIconPath("FxRevolve.png"), accel="I, R")
	def Activated(self):
		runPartDesignCommand("PartDesign_Revolution")
class _CmdFxLoft(_CmdAbstract):
	def __init__(self):
		super(_CmdFxLoft, self).__init__(menuText="&Loft", toolTip="loft profiles", pixmap=getIconPath("FxLoft.png"), accel="I, L")
	def Activated(self):
		runPartDesignCommand("PartDesign_AdditiveLoft")
class _CmdFxSweep(_CmdAbstract):
	def __init__(self):
		super(_CmdFxSweep, self).__init__(menuText="&Sweep", toolTip="sweep profile along path", pixmap=getIconPath("FxSweep.png"), accel="I, W")
	def Activated(self):
		runPartDesignCommand("PartDesign_AdditivePipe")
class _CmdFxRib(_CmdAbstract):
	def __init__(self):
		super(_CmdFxRib, self).__init__(menuText="Ri&b", toolTip="Create ribs", pixmap=getIconPath("FxRib.png"))
class _CmdFxCoil(_CmdAbstract):
	def __init__(self):
		super(_CmdFxCoil, self).__init__(menuText="&Coil", toolTip="Create coils", pixmap=getIconPath("FxCoil.png"))
class _CmdFxEmboss(_CmdAbstract):
	def __init__(self):
		super(_CmdFxEmboss, self).__init__(menuText="Embos&s", toolTip="Creates a raised (emboss) or recessed (engrave) feature from a profile", pixmap=getIconPath("FxEmboss.png"))

# Modify
class _CmdFxHole(_CmdAbstract):
	def __init__(self):
		super(_CmdFxHole, self).__init__(menuText="&Hole", toolTip="Create holes", pixmap=getIconPath("FxHole.png"))
class _CmdFxFillet(_CmdAbstract):
	def __init__(self):
		super(_CmdFxFillet, self).__init__(menuText="&Fillet", toolTip="Create fillets", pixmap=getIconPath("FxFillet.png"))
	def Activated(self):
		runPartDesignCommand("PartDesign_Fillet")
class _CmdFxChamfer(_CmdAbstract):
	def __init__(self):
		super(_CmdFxChamfer, self).__init__(menuText="&Chamfer", toolTip="Create chamfers", pixmap=getIconPath("FxChamfer.png"))
	def Activated(self):
		runPartDesignCommand("PartDesign_Chamfer")
class _CmdFxShell(_CmdAbstract):
	def __init__(self):
		super(_CmdFxShell, self).__init__(menuText="&Shell", toolTip="Create a shell", pixmap=getIconPath("FxShell.png"))
	def Activated(self):
		runPartDesignCommand("PartDesign_Thickness")
class _CmdFxDraft(_CmdAbstract):
	def __init__(self):
		super(_CmdFxDraft, self).__init__(menuText="&Draft", toolTip="Create a draft", pixmap=getIconPath("FxDraft.png"))
	def Activated(self):
		runPartDesignCommand("PartDesign_Draft")
class _CmdFxThread(_CmdAbstract):
	def __init__(self):
		super(_CmdFxThread, self).__init__(menuText="&Thread", toolTip="Create threads", pixmap=getIconPath("FxThread.png"))
class _CmdFxSplit(_CmdAbstract):
	def __init__(self):
		super(_CmdFxSplit, self).__init__(menuText="S&plit", toolTip="", pixmap=getIconPath("FxSplit.png"))
class _CmdFxCombine(_CmdAbstract):
	def __init__(self):
		super(_CmdFxCombine, self).__init__(menuText="C&ombine", toolTip="", pixmap=getIconPath("FxCombine.png"))
	def Activated(self):
		runPartDesignCommand("PartDesign_Boolean")
class _CmdFxMoveFace(_CmdAbstract):
	def __init__(self):
		super(_CmdFxMoveFace, self).__init__(menuText="&Move Face", toolTip="", pixmap=getIconPath("FxMoveFace.png"))
class _CmdFxCopyObject(_CmdAbstract):
	def __init__(self):
		super(_CmdFxCopyObject, self).__init__(menuText="Copy O&bject", toolTip="", pixmap=getIconPath("FxCopyObject.png"))
	def Activated(self):
		if FreeCAD.ActiveDocument:
			import Part
			FreeCADGui.runCommand("Part_SimpleCopy")
class _CmdFxMoveBody(_CmdAbstract):
	def __init__(self):
		super(_CmdFxMoveBody, self).__init__(menuText="Move Ob&jects", toolTip="", pixmap=getIconPath("FxMoveBody.png"))

# Pattern
class _CmdFxRectangular(_CmdAbstract):
	def __init__(self):
		super(_CmdFxRectangular, self).__init__(menuText="&Rectangular Pattern", toolTip="Arrange objects in rectangular pattern", pixmap=getIconPath("FxRectangular.png"))
	def Activated(self):
		runPartDesignCommand("PartDesign_LinearPattern")
class _CmdFxCircular(_CmdAbstract):
	def __init__(self):
		super(_CmdFxCircular, self).__init__(menuText="&Circular Pattern", toolTip="Arrange objects in circular pattern", pixmap=getIconPath("FxCircular.png"))
	def Activated(self):
		runPartDesignCommand("PartDesign_PolarPattern")
class _CmdFxSketchDriven(_CmdAbstract):
	def __init__(self):
		super(_CmdFxSketchDriven, self).__init__(menuText="&Sketcht driven", toolTip="Arrange objects according sketch points", pixmap=getIconPath("FxSketchDriven.png"))
	def Activated(self):
		if FreeCAD.ActiveDocument:
			import Draft
			FreeCADGui.runCommand("Draft_PointArray")
class _CmdFxPatterns(_CmdAbstract):
	def __init__(self):
		super(_CmdFxPatterns, self).__init__(menuText='Create Patterns', toolTip='Arrange part in patterns')
	def GetCommands(self):
		return tuple([_FX_RECTANGULAR_, _FX_CIRCULAR_, _FX_SKETCH_DRIVEN_])
	def GetDefaultCommand(self):
		return 0 # by default 'Box'
class _CmdFxMirror(_CmdAbstract):
	def __init__(self):
		super(_CmdFxMirror, self).__init__(menuText="&Mirror Pattern", toolTip="Arrange objects in a mirror pattern", pixmap=getIconPath("FxMirror.png"))
	def Activated(self):
		if FreeCAD.ActiveDocument:
			import Part
			FreeCADGui.runCommand("Part_Mirror")

# Surface
class _CmdFxThicken(_CmdAbstract):
	def __init__(self):
		super(_CmdFxThicken, self).__init__(menuText="T&hicken", toolTip="", pixmap=getIconPath("FxThicken.png"))
	def Activated(self):
		if FreeCAD.ActiveDocument:
			import Part
			FreeCADGui.runCommand("Part_Offset")
class _CmdFxStitch(_CmdAbstract):
	def __init__(self):
		super(_CmdFxStitch, self).__init__(menuText="&Stitch faces", toolTip="Stitches selected faces", pixmap=getIconPath("FxStitch.png"), accel="I, S")
	def Activated(self):
		if FreeCAD.ActiveDocument:
			boundaries = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)
			if (len(boundaries) > 1):
				makeStitch(boundaries)
class _CmdFxSculpt(_CmdAbstract):
	def __init__(self):
		super(_CmdFxSculpt, self).__init__(menuText="S&culpt", toolTip="", pixmap=getIconPath("FxSculpt.png"))
class _CmdFxPatch(_CmdAbstract):
	def __init__(self):
		super(_CmdFxPatch, self).__init__(menuText="&Boundary Patch", toolTip="Create a boundary patch for the selected edges", pixmap=getIconPath("FxBoundaryPatch.png"), accel="I, P")
	def Activated(self):
		if FreeCAD.ActiveDocument:
			edges = []
			selections = FreeCADGui.Selection.getSelectionEx(FreeCAD.ActiveDocument.Name)
			for selection in selections:
				for obj in selection.SubObjects:
					edges += obj.Edges
			if (len(edges) > 0):
				makeBoundaryPatch(edges)
class _CmdFxTrim(_CmdAbstract):
	def __init__(self):
		super(_CmdFxTrim, self).__init__(menuText="&Trim face", toolTip="", pixmap=getIconPath("FxTrim.png"))
class _CmdFxFaceDelete(_CmdAbstract):
	def __init__(self):
		super(_CmdFxFaceDelete, self).__init__(menuText="&Delete face", toolTip="", pixmap=getIconPath("FxFaceDelete.png"))
class _CmdFxFaceReplace(_CmdAbstract):
	def __init__(self):
		super(_CmdFxFaceReplace, self).__init__(menuText="&Replace face", toolTip="", pixmap=getIconPath("FxFaceReplace.png"))
class _CmdFxFaceExtend(_CmdAbstract):
	def __init__(self):
		super(_CmdFxFaceExtend, self).__init__(menuText="&Extend face", toolTip="", pixmap=getIconPath("FxFaceExtend.png"))
class _CmdFxRuledSurface(_CmdAbstract):
	def __init__(self):
		super(_CmdFxRuledSurface, self).__init__(menuText="Ruled sur&face", toolTip="", pixmap=getIconPath("FxRuledSurface.png"))

# Plastic parts
class _CmdFxGrill(_CmdAbstract):
	def __init__(self):
		super(_CmdFxGrill, self).__init__(menuText="&Grill", toolTip="The Grill feature is used to create vents or openings on the thin walls of a part to provide air flow for internal components. ", pixmap=getIconPath("FxGrill.png"))
class _CmdFxBoss(_CmdAbstract):
	def __init__(self):
		super(_CmdFxBoss, self).__init__(menuText="&Boss", toolTip="Build a boss feature on a part using points of a 2D sketch or using On Point placement.", pixmap=getIconPath("FxBoss.png"))
class _CmdFxRest(_CmdAbstract):
	def __init__(self):
		super(_CmdFxRest, self).__init__(menuText="&Rest", toolTip="Create a Rest", pixmap=getIconPath("FxRest.png"))
class _CmdFxSnapFit(_CmdAbstract):
	def __init__(self):
		super(_CmdFxSnapFit, self).__init__(menuText="&Snap-Fit", toolTip="Create a Snap Fit", pixmap=getIconPath("FxSnapFit.png"))
class _CmdFxRuleFillet(_CmdAbstract):
	def __init__(self):
		super(_CmdFxRuleFillet, self).__init__(menuText="Ruled &Fillet", toolTip="Rule-based fillets are useful for creating grills or adding to machined parts", pixmap=getIconPath("FxRuleFillet.png"))
class _CmdFxLip(_CmdAbstract):
	def __init__(self):
		super(_CmdFxLip, self).__init__(menuText="&Lip", toolTip="Limit the lip extension on one of the paths to two trimming planes", pixmap=getIconPath("FxLip.png"))

# Freeform
class _CmdFreeformBox(_CmdAbstract):
	def __init__(self):
		super(_CmdFreeformBox, self).__init__(menuText="&Box", toolTip="Create a rectangular boxed freeform", pixmap=getIconPath("FreeformBox.png"))
class _CmdFreeformPlane(_CmdAbstract):
	def __init__(self):
		super(_CmdFreeformPlane, self).__init__(menuText="&Plane", toolTip="Create a rectangular planar freeform", pixmap=getIconPath("FreeformPlane.png"))
class _CmdFreeformCylinder(_CmdAbstract):
	def __init__(self):
		super(_CmdFreeformCylinder, self).__init__(menuText="&Cylinder", toolTip="Create a cylindrical freeform", pixmap=getIconPath("FreeformCylinder.png"))
class _CmdFreeformSphere(_CmdAbstract):
	def __init__(self):
		super(_CmdFreeformSphere, self).__init__(menuText="&Sphere", toolTip="Create a sphercical freeform", pixmap=getIconPath("FreeformSphere.png"))
class _CmdFreeformTorus(_CmdAbstract):
	def __init__(self):
		super(_CmdFreeformTorus, self).__init__(menuText="&Torus", toolTip="Create a toroidal freeform", pixmap=getIconPath("FreeformTorus.png"))
class _CmdFreeformQuadBall(_CmdAbstract):
	def __init__(self):
		super(_CmdFreeformQuadBall, self).__init__(menuText="&Quad Ball", toolTip="Create a 'quad ball' freeform", pixmap=getIconPath("FreeformQuadBall.png"))
class _CmdFreeforms(_CmdAbstract):
	def __init__(self):
		super(_CmdFreeforms, self).__init__(menuText='Create Freeform', toolTip='Create a freeform')
	def GetCommands(self):
		return tuple([_FREEFORM_BOX_, _FREEFORM_PLANE_, _FREEFORM_CYLINDER, _FREEFORM_SPHERE, _FREEFORM_TORUS, _FREEFORM_QUAD_BALL])
	def GetDefaultCommand(self):
		return 0 # by default 'Box'
class  _CmdPrimitiveBox(_CmdAbstract):
	def __init__(self):
		super(_CmdPrimitiveBox, self).__init__(menuText="&Box", toolTip="Create a primitive box", pixmap=getIconPath("Primitive_Box.svg"))
	def Activated(self):
		createPrimitive('Box')
class  _CmdPrimitiveCylinder(_CmdAbstract):
	def __init__(self):
		super(_CmdPrimitiveCylinder, self).__init__(menuText="&Cylinder", toolTip="Create a primitive cylinder", pixmap=getIconPath("Primitive_Cylinder.svg"))
	def Activated(self):
		createPrimitive('Cylinder')
class  _CmdPrimitiveShpere(_CmdAbstract):
	def __init__(self):
		super(_CmdPrimitiveShpere, self).__init__(menuText="&Shpere", toolTip="Create a primitive hpere", pixmap=getIconPath("Primitive_Sphere.svg"))
	def Activated(self):
		createPrimitive('Sphere')
class  _CmdPrimitiveCone(_CmdAbstract):
	def __init__(self):
		super(_CmdPrimitiveCone, self).__init__(menuText="C&one", toolTip="Create a primitive cone", pixmap=getIconPath("Primitive_Cone.svg"))
	def Activated(self):
		createPrimitive('Cone')
class  _CmdPrimitiveEllipsoid(_CmdAbstract):
	def __init__(self):
		super(_CmdPrimitiveEllipsoid, self).__init__(menuText="&Ellipsoid", toolTip="Create a primitive ellipsoid", pixmap=getIconPath("Primitive_Ellipsoid.svg"))
	def Activated(self):
		createPrimitive('Ellipsoid')
class  _CmdPrimitiveTorus(_CmdAbstract):
	def __init__(self):
		super(_CmdPrimitiveTorus, self).__init__(menuText="&Torus", toolTip="Create a primitive torus", pixmap=getIconPath("Primitive_Torus.svg"))
	def Activated(self):
		createPrimitive('Torus')
class  _CmdPrimitivePrism(_CmdAbstract):
	def __init__(self):
		super(_CmdPrimitivePrism, self).__init__(menuText="&Prism", toolTip="Create a primitive prism", pixmap=getIconPath("Primitive_Prism.svg"))
	def Activated(self):
		createPrimitive('Prism')
class  _CmdPrimitiveWedge(_CmdAbstract):
	def __init__(self):
		super(_CmdPrimitiveWedge, self).__init__(menuText="&Wedge", toolTip="Create a primitive wedge", pixmap=getIconPath("Primitive_Wedge.svg"))
	def Activated(self):
		createPrimitive('Wedge')
class  _CmdPrimitives(_CmdAbstract):
	def __init__(self):
		super(_CmdPrimitives, self).__init__(menuText='Create Freeform', toolTip='Create a freeform')
	def GetCommands(self):
		return tuple([_PRIMITIVE_BOX_, _PRIMITIVE_CYLINDER_, _PRIMITIVE_SPHERE_, _PRIMITIVE_CONE_, _PRIMITIVE_ELLIPSOID_, _PRIMITIVE_TORUS_, _PRIMITIVE_PRISM_, _PRIMITIVE_WEDGE_])
	def GetDefaultCommand(self):
		return 0 # by default 'Box'

# Sheet-Metal
class _CmdSheetMetalFace(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalFace, self).__init__(menuText="Plate", toolTip="Face for sheet metal", pixmap=getIconPath("SheetMetalFace.png"))
class _CmdSheetMetalFlange(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalFlange, self).__init__(menuText="Flange", toolTip="Flange sheet metal", pixmap=getIconPath("SheetMetalFlange.png"))
class _CmdSheetMetalFlangeContour(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalFlangeContour, self).__init__(menuText="Contour Flange", toolTip="Contour flange sheet metal", pixmap=getIconPath("SheetMetalFlangeContour.png"))
class _CmdSheetMetalFlangeLofted(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalFlangeLofted, self).__init__(menuText="Lofted Flange", toolTip="Lofted flange sheet metal", pixmap=getIconPath("SheetMetalFlangeLofted.png"))
class _CmdSheetMetalFlanges(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalFlanges, self).__init__(menuText='Create Flange', toolTip='Create flanges for sheet metal')
	def GetCommands(self):
		return tuple([_SHEET_METAL_FLANGE_, _SHEET_METAL_CONTOUR_, _SHEET_METAL_LOFTED_])
	def GetDefaultCommand(self):
		return 0 # by default normal Flange
class _CmdSheetMetalContourRoll(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalContourRoll, self).__init__(menuText="Contour Roll", toolTip="Contour Rolll sheet metal", pixmap=getIconPath("SheetMetalContourRoll.png"))
class _CmdSheetMetalHem(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalHem, self).__init__(menuText="Hem", toolTip="Hem sheet metal", pixmap=getIconPath("SheetMetalHem.png"))
class _CmdSheetMetalBend(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalBend, self).__init__(menuText="Bend", toolTip="Bend sheet metal", pixmap=getIconPath("SheetMetalBend.png"))
class _CmdSheetMetalFold(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalFold, self).__init__(menuText="Fold", toolTip="Fold sheet metal", pixmap=getIconPath("SheetMetalFold.png"))
class _CmdSheetMetalUnfold(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalUnfold, self).__init__(menuText="Unfold", toolTip="Unfold sheet metal", pixmap=getIconPath("SheetMetalUnfold.png"))
class _CmdSheetMetalRefold(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalRefold, self).__init__(menuText="Refold", toolTip="Refold sheet metal", pixmap=getIconPath("SheetMetalRefold.png"))
class _CmdSheetMetalCut(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalCut, self).__init__(menuText="Cut", toolTip="Cut sheet metal", pixmap=getIconPath("SheetMetalCut.png"))
class _CmdSheetMetalCorner(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalCorner, self).__init__(menuText="Corner", toolTip="Corner sheet metal", pixmap=getIconPath("SheetMetalCorner.png"))
class _CmdSheetMetalRip(_CmdAbstract):
	def __init__(self):
		super(_CmdSheetMetalRip, self).__init__(menuText="Rip", toolTip="Rip sheet metal", pixmap=getIconPath("SheetMetalRip.png"))
# others
class _CmdiPart(_CmdAbstract):
	def __init__(self):
		super(_CmdiPart, self).__init__(menuText="iPart", toolTip="Create an iPart factory", pixmap=getIconPath("iPart.png"))
class _CmdFxDirectEdit(_CmdAbstract):
	def __init__(self):
		super(_CmdFxDirectEdit, self).__init__(menuText="Direct edit", toolTip="Applies direct edits to bodies", pixmap=getIconPath("FxDirectEdit.png"))

class InventorWorkbench(Workbench):
	MenuText = "like Inventor"
	ToolTip  = "Workbench that provides features known by Autodesk Inventor"
	Icon     = getIconPath("Workbench.xpm")

	def Initialize(self):
		self.appendToolbar('Inventor-Create'     , [_SKETCHES_, _SKETCH_BLOCK_, _SEPARATOR_,_FX_EXTRUDE_, _FX_REVOLVE_, _FX_LOFT_, _FX_SWEEP_, _FX_RIB_, _FX_COIL_, _FX_EMBOSS_, _SEPARATOR_, _FREEFORMS_ , _PRIMITIVES_, _SEPARATOR_, _I_PART_])
		self.appendToolbar('Inventor-Modify'     , [_FX_HOLE_, _FX_FILLET_, _FX_CHAMFER_, _FX_SHELL_, _FX_DRAFT_, _FX_THREAD_, _FX_SPLIT_, _FX_COMBINE_, _FX_MOVE_FACE_, _FX_COPY_OBJECT_, _FX_MOVE_BODY_, _FX_DIRECT_EDIT_])
		self.appendToolbar('Inventor-Patterns'   , [_FX_RECTANGULAR_, _FX_CIRCULAR_, _FX_SKETCH_DRIVEN_, _FX_MIRROR_])
		self.appendToolbar('Inventor-Surfaces'   , [_FX_THICKEN_, _FX_STITCH_, _FX_SCULPT_, _FX_PATCH_, _FX_TRIM_, _FX_DELETE_FACE_, _FX_REPLACE_FACE_, _FX_RULED_SURFACE_])
		self.appendToolbar('Inventor-Plastic'    , [_FX_GRILL_, _FX_BOSS_, _FX_REST_, _FX_SNAP_FIT_, _FX_RULE_FILLET_, _FX_LIP_])
		self.appendToolbar('Inventor-Sheet-Metal', [_SHEET_METAL_FACE_, _SHEET_METAL_FLANGES_, _SHEET_METAL_ROLL_, _SHEET_METAL_HEM_, _SHEET_METAL_BEND_, _SHEET_METAL_FOLD_, _SHEET_METAL_UNFOLD_, _SHEET_METAL_REFOLD_, _SHEET_METAL_CUT_, _SHEET_METAL_CORNER_, _SHEET_METAL_RIP_])

		self.appendMenu(["&Inventor", "create &Sketch"    ], [_SKETCH_2D_, _SKETCH_3D_, _SKETCH_BLOCK_])
		self.appendMenu(["&Inventor", "create &Primitives"], [_PRIMITIVE_BOX_, _PRIMITIVE_CYLINDER_, _PRIMITIVE_SPHERE_, _PRIMITIVE_CONE_, _PRIMITIVE_ELLIPSOID_, _PRIMITIVE_TORUS_, _PRIMITIVE_PRISM_, _PRIMITIVE_WEDGE_])
		self.appendMenu(["&Inventor", "&create Model"     ], [_FX_EXTRUDE_, _FX_REVOLVE_, _FX_LOFT_, _FX_SWEEP_, _FX_RIB_, _FX_COIL_, _FX_EMBOSS_])
		self.appendMenu(["&Inventor", "&modify Model"     ], [_FX_HOLE_, _FX_FILLET_, _FX_CHAMFER_, _FX_SHELL_, _FX_DRAFT_, _FX_THREAD_, _FX_SPLIT_, _FX_COMBINE_, _FX_MOVE_FACE_, _FX_COPY_OBJECT_, _FX_MOVE_BODY_, _FX_DIRECT_EDIT_])
		self.appendMenu(["&Inventor", "&Pattern"          ], [_FX_RECTANGULAR_, _FX_CIRCULAR_, _FX_SKETCH_DRIVEN_, _SEPARATOR_, _FX_MIRROR_])
		self.appendMenu(["&Inventor", "Sur&face"          ], [_FX_THICKEN_, _FX_STITCH_, _FX_SCULPT_, _FX_PATCH_, _FX_TRIM_, _FX_DELETE_FACE_, _FX_REPLACE_FACE_, _FX_RULED_SURFACE_])
		self.appendMenu(["&Inventor", "Plas&tic"          ], [_FX_GRILL_, _FX_BOSS_, _FX_REST_, _FX_SNAP_FIT_, _FX_RULE_FILLET_, _FX_LIP_])
		self.appendMenu(["&Inventor", "&Freeform"         ], [_FREEFORM_BOX_, _FREEFORM_PLANE_, _FREEFORM_CYLINDER, _FREEFORM_SPHERE, _FREEFORM_TORUS, _FREEFORM_QUAD_BALL])
		self.appendMenu(["&Inventor", "Sheet-M&etal"      ], [_SHEET_METAL_FACE_, _SHEET_METAL_FLANGE_, _SHEET_METAL_CONTOUR_, _SHEET_METAL_LOFTED_, _SHEET_METAL_ROLL_, _SHEET_METAL_HEM_, _SHEET_METAL_BEND_, _SHEET_METAL_FOLD_, _SHEET_METAL_UNFOLD_, _SHEET_METAL_REFOLD_, _SEPARATOR_, _SHEET_METAL_CUT_, _SHEET_METAL_CORNER_, _SHEET_METAL_RIP_])
		self.appendMenu(["&Inventor"], [_I_PART_])

if (FreeCAD.GuiUp):
	addCommand(_SKETCH_2D_          , _CmdSketch2D())
	addCommand(_SKETCH_3D_          , _CmdSketch3D())
	addCommand(_SKETCH_BLOCK_       , _CmdSketchBlock())
	addCommand(_SKETCHES_           , _CmdSketches())
	addCommand(_FX_EXTRUDE_         , _CmdFxExtrude())
	addCommand(_FX_REVOLVE_         , _CmdFxRevolve())
	addCommand(_FX_LOFT_            , _CmdFxLoft())
	addCommand(_FX_SWEEP_           , _CmdFxSweep())
	addCommand(_FX_RIB_             , _CmdFxRib())
	addCommand(_FX_COIL_            , _CmdFxCoil())
	addCommand(_FX_EMBOSS_          , _CmdFxEmboss())
	addCommand(_PRIMITIVE_BOX_      , _CmdPrimitiveBox())
	addCommand(_PRIMITIVE_CYLINDER_ , _CmdPrimitiveCylinder())
	addCommand(_PRIMITIVE_SPHERE_   , _CmdPrimitiveShpere())
	addCommand(_PRIMITIVE_CONE_     , _CmdPrimitiveCone())
	addCommand(_PRIMITIVE_ELLIPSOID_, _CmdPrimitiveEllipsoid())
	addCommand(_PRIMITIVE_TORUS_    , _CmdPrimitiveTorus())
	addCommand(_PRIMITIVE_PRISM_    , _CmdPrimitivePrism())
	addCommand(_PRIMITIVE_WEDGE_    , _CmdPrimitiveWedge())
	addCommand(_PRIMITIVES_         , _CmdPrimitives())
	addCommand(_FX_HOLE_            , _CmdFxHole())
	addCommand(_FX_FILLET_          , _CmdFxFillet())
	addCommand(_FX_CHAMFER_         , _CmdFxChamfer())
	addCommand(_FX_SHELL_           , _CmdFxShell())
	addCommand(_FX_DRAFT_           , _CmdFxDraft())
	addCommand(_FX_THREAD_          , _CmdFxThread())
	addCommand(_FX_SPLIT_           , _CmdFxSplit())
	addCommand(_FX_COMBINE_         , _CmdFxCombine())
	addCommand(_FX_MOVE_FACE_       , _CmdFxMoveFace())
	addCommand(_FX_COPY_OBJECT_     , _CmdFxCopyObject())
	addCommand(_FX_MOVE_BODY_       , _CmdFxMoveBody())
	addCommand(_FX_RECTANGULAR_     , _CmdFxRectangular())
	addCommand(_FX_CIRCULAR_        , _CmdFxCircular())
	addCommand(_FX_SKETCH_DRIVEN_   , _CmdFxSketchDriven())
	addCommand(_FX_MIRROR_          , _CmdFxMirror())
	addCommand(_FX_THICKEN_         , _CmdFxThicken())
	addCommand(_FX_STITCH_          , _CmdFxStitch())
	addCommand(_FX_SCULPT_          , _CmdFxSculpt())
	addCommand(_FX_PATCH_           , _CmdFxPatch())
	addCommand(_FX_TRIM_            , _CmdFxTrim())
	addCommand(_FX_DELETE_FACE_     , _CmdFxFaceDelete())
	addCommand(_FX_REPLACE_FACE_    , _CmdFxFaceReplace())
	addCommand(_FX_EXTEND_FACE_     , _CmdFxFaceExtend())
	addCommand(_FX_RULED_SURFACE_   , _CmdFxRuledSurface())
	addCommand(_FX_GRILL_           , _CmdFxGrill())
	addCommand(_FX_BOSS_            , _CmdFxBoss())
	addCommand(_FX_REST_            , _CmdFxRest())
	addCommand(_FX_SNAP_FIT_        , _CmdFxSnapFit())
	addCommand(_FX_RULE_FILLET_     , _CmdFxRuleFillet())
	addCommand(_FX_LIP_             , _CmdFxLip())
	addCommand(_FREEFORM_BOX_       , _CmdFreeformBox())
	addCommand(_FREEFORM_PLANE_     , _CmdFreeformPlane())
	addCommand(_FREEFORM_CYLINDER   , _CmdFreeformCylinder())
	addCommand(_FREEFORM_SPHERE     , _CmdFreeformSphere())
	addCommand(_FREEFORM_TORUS      , _CmdFreeformTorus())
	addCommand(_FREEFORM_QUAD_BALL  , _CmdFreeformQuadBall())
	addCommand(_FREEFORMS_          , _CmdFreeforms())
	addCommand(_I_PART_             , _CmdiPart())
	addCommand(_FX_DIRECT_EDIT_     , _CmdFxDirectEdit())
	addCommand(_SHEET_METAL_FACE_   , _CmdSheetMetalFace())
	addCommand(_SHEET_METAL_FLANGE_ , _CmdSheetMetalFlange())
	addCommand(_SHEET_METAL_CONTOUR_, _CmdSheetMetalFlangeContour())
	addCommand(_SHEET_METAL_LOFTED_ , _CmdSheetMetalFlangeLofted())
	addCommand(_SHEET_METAL_FLANGES_, _CmdSheetMetalFlanges())
	addCommand(_SHEET_METAL_ROLL_   , _CmdSheetMetalContourRoll())
	addCommand(_SHEET_METAL_HEM_    , _CmdSheetMetalHem())
	addCommand(_SHEET_METAL_BEND_   , _CmdSheetMetalBend())
	addCommand(_SHEET_METAL_FOLD_   , _CmdSheetMetalFold())
	addCommand(_SHEET_METAL_UNFOLD_ , _CmdSheetMetalUnfold())
	addCommand(_SHEET_METAL_REFOLD_ , _CmdSheetMetalRefold())
	addCommand(_SHEET_METAL_CUT_    , _CmdSheetMetalCut())
	addCommand(_SHEET_METAL_CORNER_ , _CmdSheetMetalCorner())
	addCommand(_SHEET_METAL_RIP_    , _CmdSheetMetalRip())
