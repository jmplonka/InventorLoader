"""Portable text regressions, using an installed font and synthetic contours."""
import json,math,os,sys,unittest
from pathlib import Path
from types import SimpleNamespace as S
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,FreeCADGui as Gui,Part
Gui.setupWithoutGUI()
from PySide.QtGui import QApplication
qtapp=QApplication.instance() or QApplication([])
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import importerText as T
from importerNative import Profile


class TextTests(unittest.TestCase):
    def test_font_runs(self):
        self.assertEqual(T.plainText(r'\F11;ABC\F12;'),'ABC')
        def node(**values):return S(get=lambda key:values.get(key))
        row=(11,4,700,0.305,1.1,'Tahoma',0,1,0,0)
        fonts=node(lst0=[row]);fonts.typeName='37186901'
        model=S(RSeMetaData={'app':S(name='PmAppSegment',elementNodes={1:fonts})})
        style=T.fontStyle(model,r'\F11;ABC\F12;')
        self.assertEqual(style['weight'],700)
        self.assertAlmostEqual(style['size'],3.05)
        with self.assertRaises(ValueError):T.fontStyle(model,r'\F11;P\F12;PE')
        with self.assertRaises(ValueError):T.plainText(r'\F11;P\X;PE')

    def test_dynamic_glyph_and_hole_counts_drive_cut(self):
        font=T.findFont('Tahoma',700) or T.findFont('DejaVu Sans',700)
        if not font:self.skipTest('No matching test font installed')
        doc=App.newDocument('SyntheticEditableText')
        try:
            sketch=doc.addObject('Sketcher::SketchObject','Support')
            path=sketch.addGeometry(Part.Circle(App.Vector(),App.Vector(0,0,1),17.5),True)
            text=doc.addObject('Part::Part2DObjectPython','Text')
            props=[('String','App::PropertyString','XXP'),('FontFile','App::PropertyFile',font),
                ('Size','App::PropertyLength',3.05),('WidthFactor','App::PropertyFloat',1.1),
                ('Tracking','App::PropertyDistance',0),('Sketch','App::PropertyLink',sketch),
                ('Layout','App::PropertyString','Circular'),('PathGeometry','App::PropertyInteger',path),
                ('Angle','App::PropertyAngle',180),('PathOffset','App::PropertyDistance',-1),
                ('SpacingScale','App::PropertyFloat',1),('RenderStatus','App::PropertyString',''),
                ('SourceSettings','App::PropertyString','{}'),('SourceLayout','App::PropertyString','{}')]
            for name,typ,value in props:setattr(text.addProperty(typ,name,'Text'),name,value)
            text.addProperty('Part::PropertyPartShape','SourceOutlines','Source')
            T.SketchText(text)
            profile=doc.addObject('Part::FeaturePython','Profile');Profile(profile,[],[],[],[text])
            extrusion=doc.addObject('Part::Extrusion','TextTool')
            extrusion.Base=profile;extrusion.Dir=App.Vector(0,0,-1);extrusion.LengthFwd=1;extrusion.Solid=True
            base=doc.addObject('Part::Feature','Base');base.Shape=Part.makeBox(50,50,3,App.Vector(-25,-25,-2))
            cut=doc.addObject('Part::Cut','Engraving');cut.Base=base;cut.Tool=extrusion
            doc.recompute(None,True,True)
            self.assertEqual(len(profile.Shape.Wires),4)
            cut.Shape.check(True);volume=cut.Shape.Volume
            text.String='XXPP';doc.recompute(None,True,True)
            self.assertEqual(len(profile.Shape.Wires),6)
            cut.Shape.check(True)
            self.assertLess(cut.Shape.Volume,volume)
            text.String='XXP';text.Size=3.2;doc.recompute(None,True,True)
            cut.Shape.check(True)
            self.assertGreater(abs(volume-cut.Shape.Volume),0.1)
            # Invalid font edits must clear the old text rather than reuse stale glyphs.
            text.FontFile=font+'.missing'
            with self.assertRaises(ValueError):text.Proxy.execute(text)
            self.assertTrue(text.Shape.isNull())
        finally:App.closeDocument(doc.Name)


if __name__=='__main__':unittest.main(verbosity=2)
