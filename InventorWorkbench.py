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
# Sketch
_SKETCH_2D_         = 'Sketch2D'
_SKETCH_3D_         = 'Sketch3D'
_SKETCH_BLOCK_      = 'SketchBlock'      # FX missing
_SKETCHES_          = 'Sketches'
# Create
_FX_EXTRUDE_        = 'FxExtrude'
_FX_REVOLVE_        = 'FxRevolve'
_FX_LOFT_           = 'FxLoft'
_FX_SWEEP_          = 'FxSweep'
_FX_RIB_            = 'FxRib'            # FX missing
_FX_COIL_           = 'FxCoil'           # FX missing
_FX_EMBOSS_         = 'FxEmboss'         # FX missing
# Modify
_FX_HOLE_           = 'FxHole'
_FX_FILLET_         = 'FxFillet'
_FX_CHAMFER_        = 'FxChamfer'
_FX_SHELL_          = 'FxShell'          # FX Missing
_FX_DRAFT_          = 'FxDraft'          # FX Missing
_FX_THREAD_         = 'FxThread'         # FX Missing
_FX_SPLIT_          = 'FxSplit'          # FX Missing
_FX_COMBINE_        = 'FxCombine'
_FX_MOVE_FACE_      = 'FxMoveFace'       # FX missing
_FX_COPY_OBJECT_    = 'FxCopyObject'     # FX missing
_FX_MOVE_BODY_      = 'FxMoveBody'       # FX missing
# Pattern
_FX_RECTANGULAR_    = 'FxRectangular'
_FX_CIRCULAR_       = 'FxCircular'
_FX_SKETCH_DRIVEN_  = 'FxSketchDriven'
_FX_PATTERNS_       = 'FxPatterns'
_FX_MIRROR_         = 'FxMirror'
# Surface
_FX_THICKEN_        = 'FxThicken'
_FX_STITCH_         = 'FxStitch'
_FX_SCULPT_         = 'FxSculpt'         # FX missing
_FX_PATCH_          = 'FxPatch'
_FX_TRIM_           = 'FxTrim'           # FX missing
_FX_DELETE_FACE_    = 'FxDeleteFace'     # FX missing
# Plastic parts
_FX_GRILL_          = 'FxGrill'          # FX missing
_FX_BOSS_           = 'FxBoss'           # FX missing
_FX_REST_           = 'FxRest'           # FX missing
_FX_SNAP_FIT_       = 'FxSnapFit'        # FX missing
_FX_RULE_FILLET_    = 'FxRuleFillet'     # FX missing
_FX_LIP_            = 'FxLip'            # FX missing
# Freeform
_FREEFORM_BOX_      = 'FreeformBox'      # FX missing
_FREEFORM_PLANE_    = 'FreeformPlane'    # FX missing
_FREEFORM_CYLINDER  = 'FreeformCylinder' # FX missing
_FREEFORM_SPHERE    = 'FreeformSphere'   # FX missing
_FREEFORM_TORUS     = 'FreeformTorus'    # FX missing
_FREEFORM_QUAD_BALL = 'FreeformQuadBall' # FX missing
_FREEFORMS_         = 'Freeforms'
# iPart
_I_PART_            = 'iPart'

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
		return not (FreeCAD.ActiveDocument is None) # as using default buttons
	def Activated(self):
		diag = QMessageBox(QMessageBox.Information, 'FreeCAD: Inventor workbench...', 'Command not ' + self.__class__.__name__ + ' yet implemented!')
		diag.setWindowModality(Qt.ApplicationModal)
		diag.exec_()

# Sketch
class _CmdSketch2D(_CmdAbstract):
	def __init__(self):
		super(_CmdSketch2D, self).__init__(menuText="&2D Sketch", toolTip="Creates an 2D sketch", pixmap=getIconPath("Sketch2D.png"), accel="I, 2")
	def Activated(self):
		if FreeCAD.ActiveDocument:
			import SketcherGui
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
class _CmdFxRevolve(_CmdAbstract):
	def __init__(self):
		super(_CmdFxRevolve, self).__init__(menuText="&Revolve", toolTip="revolve a profile", pixmap=getIconPath("FxRevolve.png"), accel="I, R")
class _CmdFxLoft(_CmdAbstract):
	def __init__(self):
		super(_CmdFxLoft, self).__init__(menuText="&Loft", toolTip="loft profiles", pixmap=getIconPath("FxLoft.png"), accel="I, L")
class _CmdFxSweep(_CmdAbstract):
	def __init__(self):
		super(_CmdFxSweep, self).__init__(menuText="&Sweep", toolTip="sweep profile along path", pixmap=getIconPath("FxSweep.png"), accel="I, W")
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
class _CmdFxChamfer(_CmdAbstract):
	def __init__(self):
		super(_CmdFxChamfer, self).__init__(menuText="&Chamfer", toolTip="Create chamfers", pixmap=getIconPath("FxChamfer.png"))
class _CmdFxShell(_CmdAbstract):
	def __init__(self):
		super(_CmdFxShell, self).__init__(menuText="&Shell", toolTip="Create a shell", pixmap=getIconPath("FxShell.png"))
class _CmdFxDraft(_CmdAbstract):
	def __init__(self):
		super(_CmdFxDraft, self).__init__(menuText="&Draft", toolTip="Create a draft", pixmap=getIconPath("FxDraft.png"))
class _CmdFxThread(_CmdAbstract):
	def __init__(self):
		super(_CmdFxThread, self).__init__(menuText="&Thread", toolTip="Create threads", pixmap=getIconPath("FxThread.png"))
class _CmdFxSplit(_CmdAbstract):
	def __init__(self):
		super(_CmdFxSplit, self).__init__(menuText="S&plit", toolTip="", pixmap=getIconPath("FxSplit.png"))
class _CmdFxCombine(_CmdAbstract):
	def __init__(self):
		super(_CmdFxCombine, self).__init__(menuText="C&ombine", toolTip="", pixmap=getIconPath("FxCombine.png"))
class _CmdFxMoveFace(_CmdAbstract):
	def __init__(self):
		super(_CmdFxMoveFace, self).__init__(menuText="&Move Face", toolTip="", pixmap=getIconPath("FxMoveFace.png"))
class _CmdFxCopyObject(_CmdAbstract):
	def __init__(self):
		super(_CmdFxCopyObject, self).__init__(menuText="Copy O&bject", toolTip="", pixmap=getIconPath("FxCopyObject.png"))
class _CmdFxMoveBody(_CmdAbstract):
	def __init__(self):
		super(_CmdFxMoveBody, self).__init__(menuText="Move Ob&jects", toolTip="", pixmap=getIconPath("FxMoveBody.png"))

# Pattern
class _CmdFxRectangular(_CmdAbstract):
	def __init__(self):
		super(_CmdFxRectangular, self).__init__(menuText="&Rectangular Pattern", toolTip="Arrange objects in rectangular pattern", pixmap=getIconPath("FxRectangular.png"))
class _CmdFxCircular(_CmdAbstract):
	def __init__(self):
		super(_CmdFxCircular, self).__init__(menuText="&Circular Pattern", toolTip="Arrange objects in circular pattern", pixmap=getIconPath("FxCircular.png"))
class _CmdFxSketchDriven(_CmdAbstract):
	def __init__(self):
		super(_CmdFxSketchDriven, self).__init__(menuText="&Sketcht driven", toolTip="Arrange objects according sketch points", pixmap=getIconPath("FxSketchDriven.png"))
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

# Surface
class _CmdFxThicken(_CmdAbstract):
	def __init__(self):
		super(_CmdFxThicken, self).__init__(menuText="T&hicken", toolTip="", pixmap=getIconPath("FxThicken.png"))
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
class _CmdFxStitch(_CmdAbstract):
	def __init__(self):
		super(_CmdFxStitch, self).__init__(menuText="&Stitch faces", toolTip="Stitches selected faces", pixmap=getIconPath("FxStitch.png"), accel="I, S")
	def Activated(self):
		if FreeCAD.ActiveDocument:
			boundaries = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)
			if (len(boundaries) > 1):
				makeStitch(boundaries)
class _CmdFxTrim(_CmdAbstract):
	def __init__(self):
		super(_CmdFxTrim, self).__init__(menuText="&Trim", toolTip="", pixmap=getIconPath("FxTrim.png"))
class _CmdFxDeleteFace(_CmdAbstract):
	def __init__(self):
		super(_CmdFxDeleteFace, self).__init__(menuText="Delete face", toolTip="", pixmap=getIconPath("FxDeleteFace.png"))

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

# iPart
class _CmdiPart(_CmdAbstract):
	def __init__(self):
		super(_CmdiPart, self).__init__(menuText="iPart", toolTip="Create an iPart factory", pixmap=getIconPath("iPart.png"))

class InventorWorkbench(Workbench):
	MenuText = "like Inventor"
	ToolTip  = "Workbench that provides features known by Autodesk Inventor"
	Icon     = getIconPath("Workbench.xpm")

	def Initialize(self):
		toolbar = [
			_SKETCHES_, _SKETCH_BLOCK_, _SEPARATOR_,
			_FX_EXTRUDE_, _FX_REVOLVE_, _FX_LOFT_, _FX_SWEEP_, _FX_RIB_, _FX_COIL_, _FX_EMBOSS_, _SEPARATOR_,
			_FX_HOLE_, _FX_FILLET_, _FX_CHAMFER_, _FX_SHELL_, _FX_DRAFT_, _FX_THREAD_, _FX_SPLIT_, _FX_COMBINE_, _FX_MOVE_FACE_, _FX_COPY_OBJECT_, _FX_MOVE_BODY_, _SEPARATOR_,
			_FX_PATTERNS_, _FX_MIRROR_, _SEPARATOR_,
			_FX_THICKEN_, _FX_STITCH_, _FX_SCULPT_, _FX_PATCH_, _FX_TRIM_, _FX_DELETE_FACE_, _SEPARATOR_,
			_FX_GRILL_, _FX_BOSS_, _FX_REST_, _FX_SNAP_FIT_, _FX_RULE_FILLET_, _FX_LIP_, _SEPARATOR_,
			_FREEFORMS_, _SEPARATOR_,
			_I_PART_
		]
		self.appendToolbar('Inventor', toolbar)
		self.appendMenu(["&Inventor", "create &Sketch"], [_SKETCH_2D_, _SKETCH_3D_, _SKETCH_BLOCK_])
		self.appendMenu(["&Inventor", "&create Model" ], [_FX_EXTRUDE_, _FX_REVOLVE_, _FX_LOFT_, _FX_SWEEP_, _FX_RIB_, _FX_COIL_, _FX_EMBOSS_])
		self.appendMenu(["&Inventor", "&modify Model" ], [_FX_HOLE_, _FX_FILLET_, _FX_CHAMFER_, _FX_SHELL_, _FX_DRAFT_, _FX_THREAD_, _FX_SPLIT_, _FX_COMBINE_, _FX_MOVE_FACE_, _FX_COPY_OBJECT_, _FX_MOVE_BODY_])
		self.appendMenu(["&Inventor", "&Pattern"      ], [_FX_RECTANGULAR_, _FX_CIRCULAR_, _FX_SKETCH_DRIVEN_, _SEPARATOR_, _FX_MIRROR_])
		self.appendMenu(["&Inventor", "Sur&face"      ], [_FX_THICKEN_, _FX_STITCH_, _FX_SCULPT_, _FX_PATCH_, _FX_TRIM_, _FX_DELETE_FACE_])
		self.appendMenu(["&Inventor", "Plas&tic"      ], [_FX_GRILL_, _FX_BOSS_, _FX_REST_, _FX_SNAP_FIT_, _FX_RULE_FILLET_, _FX_LIP_])
		self.appendMenu(["&Inventor", "&Freeform"     ], [_FREEFORM_BOX_, _FREEFORM_PLANE_, _FREEFORM_CYLINDER, _FREEFORM_SPHERE, _FREEFORM_TORUS, _FREEFORM_QUAD_BALL])
		self.appendMenu(["&Inventor", "&iPart"        ], [_I_PART_])

if (FreeCAD.GuiUp):
	addCommand(_SKETCH_2D_         , _CmdSketch2D())
	addCommand(_SKETCH_3D_         , _CmdSketch3D())
	addCommand(_SKETCH_BLOCK_      , _CmdSketchBlock())
	addCommand(_SKETCHES_          , _CmdSketches())
	addCommand(_FX_EXTRUDE_        , _CmdFxExtrude())
	addCommand(_FX_REVOLVE_        , _CmdFxRevolve())
	addCommand(_FX_LOFT_           , _CmdFxLoft())
	addCommand(_FX_SWEEP_          , _CmdFxSweep())
	addCommand(_FX_RIB_            , _CmdFxRib())
	addCommand(_FX_COIL_           , _CmdFxCoil())
	addCommand(_FX_EMBOSS_         , _CmdFxEmboss())
	addCommand(_FX_HOLE_           , _CmdFxHole())
	addCommand(_FX_FILLET_         , _CmdFxFillet())
	addCommand(_FX_CHAMFER_        , _CmdFxChamfer())
	addCommand(_FX_SHELL_          , _CmdFxShell())
	addCommand(_FX_DRAFT_          , _CmdFxDraft())
	addCommand(_FX_THREAD_         , _CmdFxThread())
	addCommand(_FX_SPLIT_          , _CmdFxSplit())
	addCommand(_FX_COMBINE_        , _CmdFxCombine())
	addCommand(_FX_MOVE_FACE_      , _CmdFxMoveFace())
	addCommand(_FX_COPY_OBJECT_    , _CmdFxCopyObject())
	addCommand(_FX_MOVE_BODY_      , _CmdFxMoveBody())
	addCommand(_FX_RECTANGULAR_    , _CmdFxRectangular())
	addCommand(_FX_CIRCULAR_       , _CmdFxCircular())
	addCommand(_FX_SKETCH_DRIVEN_  , _CmdFxSketchDriven())
	addCommand(_FX_PATTERNS_       , _CmdFxPatterns())
	addCommand(_FX_MIRROR_         , _CmdFxMirror())
	addCommand(_FX_THICKEN_        , _CmdFxThicken())
	addCommand(_FX_STITCH_         , _CmdFxStitch())
	addCommand(_FX_SCULPT_         , _CmdFxSculpt())
	addCommand(_FX_PATCH_          , _CmdFxPatch())
	addCommand(_FX_TRIM_           , _CmdFxTrim())
	addCommand(_FX_DELETE_FACE_    , _CmdFxDeleteFace())
	addCommand(_FX_GRILL_          , _CmdFxGrill())
	addCommand(_FX_BOSS_           , _CmdFxBoss())
	addCommand(_FX_REST_           , _CmdFxRest())
	addCommand(_FX_SNAP_FIT_       , _CmdFxSnapFit())
	addCommand(_FX_RULE_FILLET_    , _CmdFxRuleFillet())
	addCommand(_FX_LIP_            , _CmdFxLip())
	addCommand(_FREEFORM_BOX_      , _CmdFreeformBox())
	addCommand(_FREEFORM_PLANE_    , _CmdFreeformPlane())
	addCommand(_FREEFORM_CYLINDER  , _CmdFreeformCylinder())
	addCommand(_FREEFORM_SPHERE    , _CmdFreeformSphere())
	addCommand(_FREEFORM_TORUS     , _CmdFreeformTorus())
	addCommand(_FREEFORM_QUAD_BALL , _CmdFreeformQuadBall())
	addCommand(_FREEFORMS_         , _CmdFreeforms())
	addCommand(_I_PART_            , _CmdiPart())

