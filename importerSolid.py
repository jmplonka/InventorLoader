"""Convert the saved Inventor BRep to checked OpenCascade solids.

The STEP translator preserves trimmed ACIS surfaces that the old SAT builder
cannot reliably rebuild. Closed shells are promoted only after topology checks.
"""
import math
import FreeCAD as App
import Part
from Acis import setReader
from Acis2Step import export
from importerSAT import resolveNodes


def checkedShape(shape):
    if shape.isNull() or not shape.isValid():
        raise ValueError('Inventor BRep translation produced an invalid shape')
    if shape.ShapeType == 'Solid':
        if not shape.isClosed() or not math.isfinite(shape.Volume) or shape.Volume <= 0:
            raise ValueError('Inventor BRep produced an empty or inverted solid')
        return shape
    if shape.ShapeType == 'Shell':
        if not shape.isClosed():
            raise ValueError('Inventor BRep contains an open shell')
        solid = Part.makeSolid(shape)
        if solid.Volume < 0:
            solid.reverse()
        if not solid.isValid() or not solid.isClosed() or solid.Volume <= 0:
            raise ValueError('Cannot turn Inventor shell into a valid solid')
        if len(solid.Faces) != len(shape.Faces) or abs(solid.Area - shape.Area) > max(1e-6, shape.Area * 1e-9):
            raise ValueError('Solid conversion changed Inventor boundary surfaces')
        return solid
    if shape.ShapeType in ('Compound', 'CompSolid'):
        children = [checkedShape(child) for child in shape.childShapes()]
        if not children:
            raise ValueError('Inventor BRep contains no bodies')
        return children[0] if len(children) == 1 else Part.makeCompound(children)
    raise ValueError('Expected an Inventor solid body, got ' + shape.ShapeType)


def savedShapes(model):
    result = []
    for asm in model.getBRep().AcisList:
        acis = asm.SAT
        setReader(acis)
        bodies = resolveNodes(acis)
        if not bodies:
            continue
        path = export(acis.name, acis.header, bodies)
        shape=checkedShape(Part.read(path))
        # STEP transfer can set inconsistent edge/face tolerances even when the
        # geometry agrees within a fraction of a micrometre. Never accept the
        # centimetre-scale tolerances that concealed mirrored helix curves.
        if shape.getTolerance(1)>1e-4:
            raise ValueError('Inventor translation exceeds the 0.0001 mm tolerance budget')
        shape.fixTolerance(1e-4)
        for solid in shape.Solids:
            solid.check(True)
        result.append(shape)
    if not result:
        raise ValueError('No saved Inventor solid geometry was found')
    return result


def compareShapes(a, b, tolerance=1e-6):
    """Compare a native result to the STEP-imported reference in both directions."""
    result=dict(matches=False,reference='Inventor saved BRep -> STEP -> Part.read',
                relative_volume_tolerance=tolerance)
    if a.isNull() or b.isNull() or not a.isValid() or not b.isValid():
        result['reason']='Null or invalid shape';return result
    result.update(native_solids=len(a.Solids),step_solids=len(b.Solids),
                  native_volume_mm3=a.Volume,step_volume_mm3=b.Volume)
    if len(a.Solids) != len(b.Solids):
        result['reason']='Different solid counts';return result
    limit = max(1e-5, b.Volume * tolerance)
    result['allowed_difference_mm3']=limit
    # Mass integration of differently parametrized spline surfaces can differ
    # even when their occupied sets agree. Compare the two actual differences.
    extra,missing=a.cut(b),b.cut(a)
    for difference in (extra,missing):
        if not difference.isNull() and not difference.isValid():
            result['reason']='Invalid Boolean difference';return result
    result.update(extra_material_mm3=abs(extra.Volume),missing_material_mm3=abs(missing.Volume))
    result['matches']=result['extra_material_mm3']+result['missing_material_mm3']<=limit
    if not result['matches']:result['reason']='Occupied material differs'
    return result


def equivalent(a, b, tolerance=1e-6):
    """Compare occupied volume in both directions, also rejecting extra bodies."""
    return compareShapes(a,b,tolerance)['matches']
