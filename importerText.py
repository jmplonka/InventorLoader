"""Editable sketch text, including circular text, driving native profiles.

Inventor's saved glyphs preserve the imported typography exactly. Edits render
new glyphs with the declared installed font; differences between font versions
do not alter the original import or bypass its STEP comparison.
"""
import json
import math
import os
from pathlib import Path
import re
import statistics

import FreeCAD as App
import Part


def plainText(formatted):
    """Decode the supported Inventor inline font runs, without guessing fields."""
    text = re.sub(r'\\[Ff]\d+;', '', formatted)
    if '\\' in text or '\n' in text or '\r' in text:
        raise ValueError('Unsupported Inventor sketch text formatting')
    return text


def fontStyle(model, formatted):
    match = re.search(r'\\[Ff](\d+);', formatted)
    if not match:
        raise ValueError('Sketch text has no decoded font selection')
    number = int(match.group(1))
    active = None
    used = set()
    for run in re.split(r'(\\[Ff]\d+;)', formatted):
        if re.fullmatch(r'\\[Ff]\d+;', run):
            active = int(run[2:-1])
        elif run:
            used.add(active)
    if used != {number}:
        raise ValueError('Mixed-font sketch text is not implemented')
    found = []
    for segment in model.RSeMetaData.values():
        if 'appsegment' not in segment.name.lower():
            continue
        for node in segment.elementNodes.values():
            if node.typeName == '37186901':
                found.extend(row for row in node.get('lst0') or [] if row[0] == number)
    if len(found) != 1:
        raise ValueError('Sketch text font definition is not unique')
    row = found[0]
    return dict(family=row[5], weight=row[2], size=row[3]*10, width=row[4])


def findFont(family, weight):
    """Find the declared family; never silently substitute another family."""
    key = re.sub('[^a-z0-9]', '', family.lower())
    suffixes = ('bd', 'bold', '-bold', 'b') if weight >= 600 else ('', '-regular', 'regular')
    dirs = []
    if os.name == 'nt':
        dirs = [Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts',
                Path(os.environ.get('LOCALAPPDATA', ''))/'Microsoft/Windows/Fonts']
    else:
        dirs = [Path('/usr/share/fonts'), Path('/usr/local/share/fonts'),
                Path('/Library/Fonts'), Path.home()/'Library/Fonts', Path.home()/'.fonts']
    for directory in dirs:
        if not directory.is_dir():
            continue
        for suffix in suffixes:
            target = re.sub('[^a-z0-9]', '', key+suffix)
            candidates = [p for p in directory.rglob('*')
                          if p.suffix.lower() in ('.ttf', '.otf', '.ttc') and
                          re.sub('[^a-z0-9]', '', p.stem.lower()) == target]
            if candidates:
                return str(sorted(candidates)[0])
    return ''


def characters(text, font, size, width, tracking=0):
    if not font or not Path(font).is_file():
        raise ValueError('Select the installed text font in FontFile before editing')
    if size <= 0 or width <= 0:
        raise ValueError('Text Size and WidthFactor must be positive')
    # FreeType's em size is not the cap height used by Inventor sketch text.
    cap = Part.makeCompound(Part.makeWireString('M', font, 1, 0)[0]).BoundBox.YMax
    if cap <= 0:
        raise ValueError('The selected font has no usable cap height')
    matrix = App.Matrix()
    matrix.A11, matrix.A22 = width/cap, 1/cap
    groups = Part.makeWireString(text, font, size, tracking*cap/width)
    return [Part.makeCompound(wires).transformGeometry(matrix) if wires else None
            for wires in groups]


def pathSignature(sketch, geometry):
    circle = sketch.Geometry[geometry]
    if not isinstance(circle, Part.Circle):
        raise ValueError('Editable curved sketch text requires a circular path')
    return [circle.Center.x, circle.Center.y, circle.Center.z, circle.Radius]


def calibrate(groups, glyphs, center, circular):
    """Recover glyph frames from saved outlines and the declared cap height.

    Only an unambiguous cap-height straight edge is accepted. Unsupported layouts
    keep their original curves rather than acquiring an invented text placement.
    """
    frames = []
    for shape, glyph in zip(groups, glyphs):
        if glyph is None:
            continue
        height = glyph.BoundBox.YLength
        choices = []
        for edge in shape.Edges:
            if isinstance(edge.Curve, Part.Line) and abs(edge.Length-height) < max(1e-5, height*1e-5):
                y = (edge.Vertexes[-1].Point-edge.Vertexes[0].Point).normalize()
                if circular and y.dot(center-shape.BoundBox.Center) < 0:
                    y = -y
                if not circular and y.y < 0:
                    y = -y
                if not any(abs(y.dot(old)-1) < 1e-8 for old in choices):
                    choices.append(y)
        if len(choices) != 1:
            raise ValueError('Saved text glyph has no unambiguous cap-height frame')
        y = choices[0]
        x = y.cross(App.Vector(0, 0, 1))
        rotation = App.Rotation(x, y, App.Vector(0, 0, 1), 'ZXY')
        local = shape.copy()
        local.Placement = App.Placement(App.Vector(), rotation.inverted()).multiply(local.Placement)
        box, generated = local.optimalBoundingBox(), glyph.optimalBoundingBox()
        # The baseline is independent of glyph width or cap bearings.
        origin = rotation.multVec(App.Vector(box.XMin-generated.XMin, box.YMin-generated.YMin, 0))
        if circular:
            radius = -(origin-center).dot(y)
            angle = math.atan2(-y.y, -y.x)
            while frames and angle-frames[-1]['angle'] > math.pi: angle -= 2*math.pi
            while frames and angle-frames[-1]['angle'] < -math.pi: angle += 2*math.pi
            frames.append(dict(angle=angle, radius=radius, x=(generated.XMin+generated.XMax)/2))
        else:
            frames.append(dict(origin=list(origin), rotation=list(rotation.Q)))
    if not frames:
        raise ValueError('Text has no usable saved glyphs')
    if not circular:
        if any((App.Vector(f['origin'])-App.Vector(frames[0]['origin'])).Length > 0.05 for f in frames):
            raise ValueError('Linear text glyph frames disagree')
        return frames[0]
    radii = [f['radius'] for f in frames]
    if max(radii)-min(radii) > 0.05:
        raise ValueError('Circular text glyph baseline radii disagree')
    if len(frames) < 2:
        raise ValueError('Circular text needs at least two saved glyph frames')
    meanx = statistics.mean(f['x'] for f in frames)
    meana = statistics.mean(f['angle'] for f in frames)
    variance = sum((f['x']-meanx)**2 for f in frames)
    slope = sum((f['x']-meanx)*(f['angle']-meana) for f in frames)/variance
    if abs(slope) < 1e-8:
        raise ValueError('Circular text direction could not be recovered')
    if max(abs(f['angle']-(meana+slope*(f['x']-meanx))) for f in frames) > 0.01:
        raise ValueError('Circular text glyph spacing is not uniform')
    return dict(angle=meana, slope=slope, centerX=meanx, radius=statistics.mean(radii))


class TextView:
    def __init__(self, view): view.Proxy = self
    def attach(self, view): pass
    def __getstate__(self): return None
    def __setstate__(self, state): pass
    def getIcon(self): return ':/icons/Draft_ShapeString.svg'
    def doubleClicked(self, view):
        from PySide import QtGui
        dialog = getattr(QtGui, 'QInputDialog', None)
        if dialog is None:
            from PySide import QtWidgets
            dialog = QtWidgets.QInputDialog
        text, accepted = dialog.getText(None, 'Inventor sketch text', 'Text', text=view.Object.String)
        if accepted:
            doc = view.Object.Document
            doc.openTransaction('Edit imported sketch text')
            view.Object.String = text
            doc.recompute()
            doc.commitTransaction()
        return True


class Annotation:
    def execute(self,obj):
        obj.Label=getattr(obj.Sketch,'InventorOriginalLabel',obj.Sketch.Label)+' Text: '+obj.String


def createAnnotation(doc,sketch,record):
    """Retain text without saved glyphs as editable, explicitly unrendered metadata."""
    formatted=record.get('txt0') or ''
    if not formatted:return None
    try:string=plainText(formatted)
    except ValueError:string=formatted
    obj=doc.addObject('App::FeaturePython',sketch.Name+'_Annotation')
    obj.addProperty('App::PropertyString','String','Text').String=string
    obj.addProperty('App::PropertyLinkGlobal','Sketch','Text support').Sketch=sketch
    obj.setEditorMode('Sketch',2)
    obj.addProperty('App::PropertyString','RenderStatus','Inventor import').RenderStatus='Source annotation text retained; display layout not reconstructed'
    obj.setEditorMode('RenderStatus',1)
    obj.addProperty('App::PropertyString','SourceFormattedText','Inventor source').SourceFormattedText=formatted
    obj.setEditorMode('SourceFormattedText',2)
    obj.Proxy=Annotation();obj.Proxy.execute(obj)
    if App.GuiUp:TextView(obj.ViewObject)
    return obj


class SketchText:
    def __init__(self, obj):
        obj.Proxy = self
        if App.GuiUp: TextView(obj.ViewObject)

    def execute(self, obj):
        placement = obj.Placement
        try:
            signature = pathSignature(obj.Sketch, obj.PathGeometry) if obj.Layout == 'Circular' else []
            original = json.loads(obj.SourceSettings)
            current = dict(string=obj.String, font=obj.FontFile, size=obj.Size.Value,
                           width=obj.WidthFactor, tracking=obj.Tracking.Value,
                           angle=obj.Angle.Value, offset=obj.PathOffset.Value,
                           spacing=obj.SpacingScale, path=signature)
            if current == original:
                obj.Shape = obj.SourceOutlines.copy()
                obj.RenderStatus = 'Original Inventor glyph outlines'
            else:
                glyphs = characters(obj.String, obj.FontFile, obj.Size.Value, obj.WidthFactor, obj.Tracking.Value)
                present = [g for g in glyphs if g is not None]
                if not present:
                    raise ValueError('Text must contain at least one visible glyph')
                bounds = Part.makeCompound(present).BoundBox
                midpoint = (bounds.XMin+bounds.XMax)/2
                shapes = []
                for glyph in present:
                    if obj.Layout == 'Circular':
                        center = App.Vector(*signature[:3])
                        radius = signature[3]+obj.PathOffset.Value
                        if radius <= 0:
                            raise ValueError('Text baseline radius must be positive')
                        xmid = (glyph.BoundBox.XMin+glyph.BoundBox.XMax)/2
                        angle = math.radians(obj.Angle.Value)+(xmid-midpoint)*obj.SpacingScale/signature[3]
                        y = App.Vector(-math.cos(angle), -math.sin(angle), 0)
                        x = y.cross(App.Vector(0, 0, 1))
                        rotation = App.Rotation(x, y, App.Vector(0, 0, 1), 'ZXY')
                        base = center-y*radius-x*xmid
                        glyph.Placement = App.Placement(base, rotation).multiply(glyph.Placement)
                    else:
                        layout = json.loads(obj.SourceLayout)
                        glyph.Placement = App.Placement(App.Vector(layout['origin']), App.Rotation(*layout['rotation'])).multiply(glyph.Placement)
                    shapes.append(glyph)
                obj.Shape = Part.makeCompound(shapes)
                obj.RenderStatus = 'Rebuilt from editable text and FontFile'
            obj.Placement = placement
            obj.positionBySupport()
            obj.Label = getattr(obj.Sketch,'InventorOriginalLabel',obj.Sketch.Label)+' Text: '+obj.String
        except Exception:
            obj.Shape = Part.Shape()
            obj.Placement = placement
            obj.RenderStatus = 'Text rebuild failed; check font and layout properties'
            raise


def createText(doc, sketch, record, outlines, model):
    formatted = record.get('txt0')
    string = plainText(formatted)
    style = fontStyle(model, formatted)
    font = findFont(style['family'], style['weight'])
    if not font:
        raise ValueError('Font not installed: '+style['family'])
    glyphs = characters(string, font, style['size'], style['width'])
    groups, anchors = [], []
    inverse = sketch.Placement.inverse()
    for outline in outlines:
        if outline.typeName != '19F763CB':
            raise ValueError('Unsupported text outline record')
        edges = [curve.getGeometry().toShape() for curve in outline.get('edges')]
        shape = Part.makeCompound(edges)
        shape.Placement = inverse.multiply(shape.Placement)
        anchor = outline.get('a1')
        match = next((i for i,p in enumerate(anchors) if (anchor-p).Length < 1e-7), None)
        if match is None:
            anchors.append(anchor); groups.append([]); match = len(groups)-1
        groups[match].append(shape)
    groups = [Part.makeCompound(g) for g in groups]
    if len(groups) != sum(g is not None for g in glyphs):
        raise ValueError('Saved text glyph count does not match the text')
    visible = [g for g in glyphs if g is not None]
    links = [n for n in record.segment.elementNodes.values()
             if n.typeName == 'DD80AC37' and n.get('refString') and n.get('refString').index == record.index]
    path = links[0].get('refEdge') if len(links) == 1 else None
    circular = path is not None and path.typeName == 'Circle2D'
    if path is not None and not circular:
        raise ValueError('Text on non-circular paths is not implemented')
    center = sketch.Geometry[path.sketchIndex].Center if circular else App.Vector()
    layout = calibrate(groups, visible, center, circular)
    obj = doc.addObject('Part::Part2DObjectPython', sketch.Name+'_Text')
    obj.addProperty('App::PropertyString', 'String', 'Text', 'Editable text; changing it rebuilds the linked extrusion').String = string
    obj.addProperty('App::PropertyFile', 'FontFile', 'Text').FontFile = font
    obj.addProperty('App::PropertyString', 'FontFamily', 'Text').FontFamily = style['family']
    obj.addProperty('App::PropertyLength', 'Size', 'Text').Size = style['size']
    obj.addProperty('App::PropertyFloat', 'WidthFactor', 'Text').WidthFactor = style['width']
    obj.addProperty('App::PropertyDistance', 'Tracking', 'Text').Tracking = 0
    obj.addProperty('App::PropertyLink', 'Sketch', 'Text support').Sketch = sketch
    obj.addProperty('App::PropertyString', 'Layout', 'Text support').Layout = 'Circular' if circular else 'Linear'
    obj.addProperty('App::PropertyInteger', 'PathGeometry', 'Text support').PathGeometry = path.sketchIndex if circular else -1
    obj.addProperty('App::PropertyAngle', 'Angle', 'Text support').Angle = math.degrees(layout['angle']) if circular else 0
    signature = pathSignature(sketch, obj.PathGeometry) if circular else []
    obj.addProperty('App::PropertyDistance', 'PathOffset', 'Text support').PathOffset = layout['radius']-signature[3] if circular else 0
    obj.addProperty('App::PropertyFloat', 'SpacingScale', 'Text support').SpacingScale = layout['slope']*signature[3] if circular else 1
    obj.addProperty('App::PropertyString', 'RenderStatus', 'Inventor import')
    obj.addProperty('Part::PropertyPartShape', 'SourceOutlines', 'Inventor source').SourceOutlines = Part.makeCompound(groups)
    obj.addProperty('App::PropertyString', 'SourceLayout', 'Inventor source').SourceLayout = json.dumps(layout)
    obj.addProperty('App::PropertyString', 'SourceSettings', 'Inventor source').SourceSettings = json.dumps(dict(
        string=string, font=font, size=obj.Size.Value, width=obj.WidthFactor, tracking=0,
        angle=obj.Angle.Value, offset=obj.PathOffset.Value, spacing=obj.SpacingScale, path=signature))
    for prop in ('SourceOutlines', 'SourceLayout', 'SourceSettings'): obj.setEditorMode(prop, 2)
    for prop in ('FontFamily', 'Layout', 'PathGeometry', 'RenderStatus'): obj.setEditorMode(prop, 1)
    obj.Placement = sketch.Placement
    SketchText(obj)
    obj.Proxy.execute(obj)
    return obj
