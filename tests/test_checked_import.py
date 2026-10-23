"""Synthetic regression tests; run with FreeCAD's Python and addon dependencies."""
import math
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
Gui.setupWithoutGUI()
from PySide.QtGui import QApplication
qtapp = QApplication.instance() or QApplication([])
# FreeCAD initialization prepends installed addon paths; test this checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import Acis
import importerInventor as I
import importerUtils as U
from importerReader import decompressInventorData
from importerSolid import checkedShape, compareShapes
import importerExtrusion as E
from importerNative import Importer


class CheckedImportTests(unittest.TestCase):
    def test_extrusion_operations_change_material(self):
        doc = App.newDocument('ExtrusionOperations')
        try:
            base = doc.addObject('Part::Feature', 'Base')
            base.Shape = Part.makeBox(10, 10, 10)
            tool = doc.addObject('Part::Feature', 'Tool')
            tool.Shape = Part.makeBox(10, 10, 10, App.Vector(5, 0, 0))
            settings = SimpleNamespace(Operation='Join', ImportedState='initial',
                Extent='Distance', LengthFwd=10, LengthRev=0, Reversed=False,
                Symmetric=False, TaperAngle=0, Direction=App.Vector(0, 0, 1),
                EndFace=None, StartFace=None)
            # Exercise the real Boolean implementation with controlled geometry.
            obj = SimpleNamespace(InventorExtrusion=settings, Tools=[tool], Base=base)
            for operation, volume in [('Join', 1500), ('Cut', 500),
                                      ('Intersection', 500), ('NewBody', 2000)]:
                with self.subTest(operation=operation):
                    settings.Operation = operation
                    E.Result().execute(obj)
                    self.assertAlmostEqual(obj.Shape.Volume, volume)
                    self.assertTrue(obj.InventorModified)
                    for solid in obj.Shape.Solids:
                        solid.check(True)
            settings.Operation = 'Cut'
            settings.ImportedState = E.state(settings)
            E.Result().execute(obj)
            self.assertFalse(obj.InventorModified)
        finally:
            App.closeDocument(doc.Name)

    def test_planar_extrusion_extents_and_inclined_face_rejection(self):
        base = SimpleNamespace(Shape=Part.makeBox(10, 10, 10))
        profile = SimpleNamespace(Shape=Part.Wire(Part.makeCircle(2, App.Vector(5, 5, 0))))
        end = SimpleNamespace(Shape=Part.makePlane(20, 20, App.Vector(0, 0, 8)))
        start = SimpleNamespace(Shape=Part.makePlane(20, 20, App.Vector(0, 0, 2)))
        obj = SimpleNamespace(PropertiesList=[], Direction=App.Vector(0, 0, 1),
            Reversed=False, Symmetric=False, Profile=profile, Base=base,
            LengthFwd=SimpleNamespace(Value=3), LengthRev=SimpleNamespace(Value=2),
            EndFace=(end, ['Face1']), StartFace=(start, ['Face1']))
        for extent, forward, backward in [('Distance', 3, 0), ('TwoDistances', 3, 2),
                                         ('ToFace', 8, 0), ('ToNext', 10, 0), ('FromTo', 6, 0)]:
            with self.subTest(extent=extent):
                obj.Extent = extent
                E.Settings().execute(obj)
                self.assertAlmostEqual(obj.CalculatedLength, forward)
                self.assertAlmostEqual(obj.CalculatedLength2, backward)
        self.assertAlmostEqual(obj.StartOffset.z, 2)
        obj.Extent = 'ThroughAll'
        E.Settings().execute(obj)
        self.assertGreater(obj.CalculatedLength, 10)
        obj.Symmetric = True
        E.Settings().execute(obj)
        self.assertGreater(obj.CalculatedLength, 20)
        obj.Symmetric = False
        obj.Extent = 'ToFace'
        end.Shape.rotate(App.Vector(), App.Vector(1, 0, 0), 20)
        with self.assertRaisesRegex(ValueError, 'parallel to the profile'):
            E.Settings().execute(obj)
        obj.Direction = App.Vector()
        with self.assertRaisesRegex(ValueError, 'nonzero'):
            E.Settings().execute(obj)

    def test_constraint_guard_restores_displaced_source_curves(self):
        doc = App.newDocument('ConstraintGuard')
        try:
            sketch = doc.addObject('Sketcher::SketchObject', 'Sketch')
            sketch.addGeometry(Part.LineSegment(App.Vector(), App.Vector(10, 0, 0)), False)
            importer = Importer()
            importer.mapConstraints = {}  # Normally initialized by createSketch.
            before = [g.copy() for g in sketch.Geometry]
            sketch.addConstraint(Sketcher.Constraint('Distance', 0, 5.0))
            self.assertFalse(importer.checkedConstraint(sketch, before, 0, 'partial-line'))
            self.assertEqual(sketch.ConstraintCount, 0)
            self.assertAlmostEqual(sketch.Geometry[0].length(), 10)
            self.assertIn('source constraint not bound', sketch.InventorConstraintNotes[0])
            sketch.addConstraint(Sketcher.Constraint('Horizontal', 0))
            self.assertTrue(importer.checkedConstraint(sketch, before, 0, 'horizontal'))
            self.assertEqual(sketch.ConstraintCount, 1)
        finally:
            App.closeDocument(doc.Name)

    def test_zlib_stream(self):
        payload = b'Inventor stream\0' * 1000
        self.assertEqual(decompressInventorData(zlib.compress(payload)), payload)

    def test_zstandard_unknown_content_size(self):
        import zstandard
        payload = b'Inventor stream\0' * 1000
        compressed = zstandard.ZstdCompressor(write_content_size=False).compress(payload)
        self.assertEqual(decompressInventorData(compressed), payload)

    def test_signed_helix_endpoints(self):
        h = Acis.Helix()
        h.posCenter = App.Vector(1, 2, 3)
        h.dirMajor = App.Vector(0, 5, 0)
        h.dirMinor = App.Vector(5, 0, 0)
        h.dirPitch = App.Vector(0, 0, -20)
        h.radAngles = Acis.Interval(Acis.Range('F', 0), Acis.Range('F', math.pi / 2))
        edge = h.build()
        self.assertLess((edge.firstVertex().Point - App.Vector(1, 7, 3)).Length, 1e-7)
        self.assertLess((edge.lastVertex().Point - App.Vector(6, 2, -2)).Length, 1e-7)

    def test_circular_screw_cylinder_intersections(self):
        from importerIntersection import screwCylinderIntersection, splineData
        for sign in (-1, 1):
            with self.subTest(branch=sign):
                h = Acis.Helix()
                h.posCenter = App.Vector(1, 2, 3)
                h.dirMajor = App.Vector(10, 0, 0)
                h.dirMinor = App.Vector(0, 10, 0)
                h.dirPitch = App.Vector(0, 0, -8)
                h.radAngles = Acis.Interval(Acis.Range('F', 0), Acis.Range('F', 2*math.pi))
                cylinder = Acis.SurfaceCone()
                cylinder.sine, cylinder.ratio = 0, 1
                cylinder.center, cylinder.axis = h.posCenter, App.Vector(0, 0, 1)
                cylinder.major = App.Vector(10, 0, 0)
                profile = Acis.CurveEllipse()
                profile.ratio, profile.axis = 1, App.Vector(0, 0, 1)
                profile.center, profile.major = h.posCenter+h.dirMajor, App.Vector(2, 0, 0)
                sweep = Acis.SurfaceSpline()
                sweep.subtype = 'sweep_spl_sur'
                sweep.path, sweep.profile = SimpleNamespace(helix=h), profile
                sweep.getSurface = lambda: sweep
                delta = sign * math.acos(0.98)
                def point(u):
                    return h.posCenter + App.Vector(10*math.cos(u+delta), 10*math.sin(u+delta), -8*u/(2*math.pi))
                guide = Part.BSplineCurve()
                params = [0.1 + 2*i/128 for i in range(129)]
                guide.interpolate(Points=[point(u) for u in params], Parameters=params, Tolerance=1e-10)
                curve = SimpleNamespace(spline=splineData(guide), subtype='int_int_cur', tolerance=1e-5, sense='forward')
                result = screwCylinderIntersection(curve, [cylinder, sweep])
                self.assertIsNotNone(result)
                exact = Acis.createBSplinesCurve(result, 'forward', 'int_int_cur').Curve
                for i in range(31):
                    u = exact.FirstParameter+(exact.LastParameter-exact.FirstParameter)*i/30
                    p = exact.value(u)
                    self.assertLess((p-point(u)).Length, 1e-7)

    def test_geometry_comparison_rejects_removal_errors(self):
        base = Part.makeBox(30, 30, 10)
        reference = base.cut(Part.makeCylinder(2, 10, App.Vector(5, 5, 0)))
        wrong_hole = base.cut(Part.makeCylinder(2, 10, App.Vector(8, 5, 0)))
        self.assertLess(abs(wrong_hole.Volume-reference.Volume), 1e-8)
        cases = {
            'identical': (reference.copy(), True),
            'filled_hole': (base, False),
            'extra_hole': (reference.cut(Part.makeCylinder(2, 10, App.Vector(20, 20, 0))), False),
            'relocated_equal_volume_hole': (wrong_hole, False),
            'extra_solid': (Part.makeCompound([reference, Part.makeBox(1, 1, 1, App.Vector(40, 0, 0))]), False),
        }
        for name, (shape, expected) in cases.items():
            with self.subTest(case=name):
                self.assertEqual(compareShapes(shape, reference)['matches'], expected)
        moved = compareShapes(wrong_hole, reference)
        self.assertGreater(moved['extra_material_mm3'], 1)
        self.assertGreater(moved['missing_material_mm3'], 1)

    def test_closed_shell_conversion_and_open_surface_rejection(self):
        box = Part.makeBox(3, 4, 5)
        result = checkedShape(box.Shells[0])
        result.check(True)
        self.assertAlmostEqual(result.Volume, 60)
        with self.assertRaises(ValueError):
            checkedShape(Part.makePlane(3, 4))

    def test_failed_import_preserves_existing_document(self):
        doc = App.newDocument('CheckedImportRollback')
        try:
            box = doc.addObject('Part::Box', 'Keep')
            doc.recompute()
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'broken.iam'
                path.write_bytes(b'not an Inventor document')
                with self.assertRaises(Exception):
                    I.importFile(path, doc)
            self.assertEqual([o.Name for o in doc.Objects], [box.Name])
            self.assertAlmostEqual(box.Shape.Volume, 1000)
        finally:
            App.closeDocument(doc.Name)

    def test_dialog_uses_clicked_button_instead_of_numeric_return(self):
        class MessageBox:
            Question, ActionRole, RejectRole = 1, 2, 3
            selected = None
            def __init__(self): self.buttons = []
            def addButton(self, button, role): self.buttons.append(button)
            def exec_(self): return 4  # The reported Qt regression.
            def clickedButton(self):
                return None if self.selected is None else self.buttons[self.selected]
            def __getattr__(self, name): return lambda *args: None
        with patch.object(U, 'QMessageBox', MessageBox), patch.object(U, 'getThumbnail', return_value=None), \
             patch.object(U, 'getStrategy', return_value=U.STRATEGY_STEP), patch.object(U, 'setStrategy'):
            for func, choices in (
                (U.chooseImportStrategy, [U.STRATEGY_STEP, U.STRATEGY_SAT, U.STRATEGY_NATIVE, U.STRATEGY_CANCEL]),
                (U.chooseImportStrategyAcis, [U.STRATEGY_STEP, U.STRATEGY_SAT, U.STRATEGY_CANCEL]),
            ):
                for index, expected in enumerate(choices):
                    MessageBox.selected = index
                    self.assertEqual(func(), expected)
                MessageBox.selected = None
                self.assertEqual(func(), U.STRATEGY_CANCEL)


if __name__ == '__main__':
    unittest.main()
