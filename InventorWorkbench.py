# -*- coding: utf-8 -*-

'''
InventorWorkbench.py
'''

import os, FreeCAD, FreeCADGui
from InventorViewProviders import *
from FreeCADGui            import Workbench, addCommand
from importerUtils         import getIconPath

_SEPARATOR_         = 'Separator'
_SKETCH_2D_         = 'Sketch2D'
_SKETCH_3D_         = 'Sketch3D'
_SKETCHES_          = 'Sketches'
_FX_STITCH_         = 'FxStitch'
_FX_BOUNDARY_PATCH_ = 'FxBoundaryPatch_'

class _CmdSketches:
	def GetCommands(self):
		return tuple([_SKETCH_2D_, _SKETCH_3D_])
	def GetDefaultCommand(self):
		return 0 # by default 2D sketches
	def GetResources(self):
		return { 'MenuText': 'Create sketch', 'ToolTip': 'Create sketches'}
	def IsActive(self):
		return not (FreeCAD.ActiveDocument is None) # as using default buttons

class _CmdSketch2D:
	def GetResources(self):
		return {'Pixmap'  : getIconPath("Sketch2D.xpm"),
				'MenuText': "&2D Sketch",
				'Accel': "I, 2",
				'ToolTip': "Creates an 2D sketch"}

	def IsActive(self):
		return not (FreeCAD.ActiveDocument is None)

	def Activated(self):
		if FreeCAD.ActiveDocument:
			import SketcherGui
			FreeCADGui.runCommand("Sketcher_NewSketch")

class _CmdSketch3D:
	def GetResources(self):
		return {'Pixmap'  : getIconPath("Sketch3D.xpm"),
				'MenuText': "&3D Sketch",
				'Accel': "I, 3",
				'ToolTip': "Creates an 3D sketch"}

	def IsActive(self):
		return not (FreeCAD.ActiveDocument is None)

	def Activated(self):
		if FreeCAD.ActiveDocument:
			makeSketch3D()

class _CmdFxBoundaryPatch:
	def GetResources(self):
		return {'Pixmap'  : getIconPath("FxBoundaryPatch.xpm"),
				'MenuText': "&Boundary Patch",
				'Accel': "I, B",
				'ToolTip': "Create a boundary patch for the selected edges"}

	def IsActive(self):
		return not (FreeCAD.ActiveDocument is None)

	def Activated(self):
		if FreeCAD.ActiveDocument:
			edges = []
			selections = FreeCADGui.Selection.getSelectionEx(FreeCAD.ActiveDocument.Name)
			for selection in selections:
				for obj in selection.SubObjects:
					edges += obj.Edges
			if (len(edges) > 0):
				makeBoundaryPatch(edges)

class _CmdFxStitch:
	def GetResources(self):
		return {'Pixmap'  : getIconPath("FxStitch.xpm"),
				'MenuText': "&Stitch faces",
				'Accel': "I, S",
				'ToolTip': "Stitches selected faces"}

	def IsActive(self):
		return not (FreeCAD.ActiveDocument is None)

	def Activated(self):
		if FreeCAD.ActiveDocument:
			boundaries = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)
			if (len(boundaries) > 1):
				makeStitch(boundaries)

class InventorWorkbench(Workbench):
	MenuText = "like Inventor"
	ToolTip  = "Workbench that provides features known by Autodesk Inventor"
	Icon     = getIconPath("Workbench.xpm")

	def Initialize(self):
		toolbar = [_SKETCHES_, _SEPARATOR_, _FX_BOUNDARY_PATCH_, _FX_STITCH_,]
		self.appendToolbar('Inventor', toolbar)
		self.appendMenu(["&Inventor","create &Sketch"], [_SKETCH_2D_, _SKETCH_3D_])
		self.appendMenu(["&Inventor"], [_SEPARATOR_, _FX_BOUNDARY_PATCH_, _FX_STITCH_])

if (FreeCAD.GuiUp):
	addCommand(_SKETCH_2D_        , _CmdSketch2D())
	addCommand(_SKETCH_3D_        , _CmdSketch3D())
	addCommand(_SKETCHES_         , _CmdSketches())
	addCommand(_FX_BOUNDARY_PATCH_, _CmdFxBoundaryPatch())
	addCommand(_FX_STITCH_        , _CmdFxStitch())
