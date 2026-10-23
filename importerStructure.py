"""Present the stored Inventor browser instead of the Boolean dependency graph.

Native Part operations remain the calculation objects. Their source feature
nodes expose the same editable dimensions and only claim the source sketches,
never previous solids, profile decoders or cutting tools.
"""
import json
import re
from pathlib import Path
import FreeCAD as App
import Part
from importerUtils import getIconPath


def linkProperty(obj, name, values, multiple=True):
    kind = 'App::PropertyLinkListGlobal' if multiple else 'App::PropertyLinkGlobal'
    if name not in obj.PropertiesList: obj.addProperty(kind, name, 'Inventor structure')
    setattr(obj, name, values)
    obj.setEditorMode(name, 2)


class SourceView:
    def __init__(self, view): self.Object = view.Object; view.Proxy = self
    def attach(self, view): self.Object = view.Object
    def __getstate__(self): return None
    def __setstate__(self, state): pass
    def claimChildren(self): return list(getattr(self.Object, 'InventorChildren', []))
    def getIcon(self):
        native=getattr(self.Object,'InventorNativeFeature',None)
        settings=getattr(native,'InventorExtrusion',None) if native is not None else None
        if settings is not None:
            from PySide.QtCore import QFile
            operation=str(settings.Operation)
            icon=':/icons/PartDesign_'+('Pocket' if operation=='Cut' else 'Pad')+'.svg'
            if operation in ('Cut','Join','NewBody') and QFile.exists(icon):return icon
            return getIconPath({'Cut':'SheetMetalCut.png','Intersection':'FxCombine.png','Surface':'FxBoundaryPatch.xpm'}.get(operation,'FxExtrude.png'))
        kind = getattr(self.Object, 'InventorFeatureType', '')
        return getIconPath({'Coil':'FxCoil.svg','Fillet':'FxFillet.png',
                            'Chamfer':'FxChamfer.png','Extrude':'FxExtrude.png',
                            'Sketch2D':'Sketch2D.png','Sketch3D':'Sketch3D.png'}.get(kind,'FxCombine.png'))
    def doubleClicked(self, view):
        obj = view.Object
        native=getattr(obj,'InventorNativeFeature',None)
        if native is not None and hasattr(native,'InventorExtrusion'):
            from importerExtrusion import edit
            return edit(native)
        target = getattr(obj, 'InventorParameterTarget', None)
        if target is None: return False
        import FreeCADGui as Gui
        if not Gui.activeDocument().setEdit(target.Name, 0):
            Gui.Selection.clearSelection(); Gui.Selection.addSelection(target)
        return True


class SourceFeature:
    def __init__(self, obj): self.busy = False; obj.Proxy = self
    def __getstate__(self): return None
    def __setstate__(self, state): self.busy = False
    def execute(self, obj):
        self.busy = True
        try:
            obj.Shape = obj.InventorNativeFeature.Shape.copy()
            target = obj.InventorParameterTarget
            if target is None:return
            for name in json.loads(obj.InventorDimensionNames):
                if name not in dict(obj.ExpressionEngine): setattr(obj, name, getattr(target, name))
        finally: self.busy = False
    def onChanged(self, obj, prop):
        if obj.Document.Restoring or 'Restore' in obj.State:return
        if getattr(self, 'busy', True) or 'InventorDimensionNames' not in obj.PropertiesList: return
        names = json.loads(obj.InventorDimensionNames or '[]')
        if prop not in names and prop != 'ExpressionEngine': return
        self.busy = True
        try:
            target = obj.InventorParameterTarget
            if target is None:return
            expressions = dict(obj.ExpressionEngine)
            native = dict(target.ExpressionEngine)
            for name in names if prop == 'ExpressionEngine' else [prop]:
                expr = expressions.get(name)
                if expr != native.get(name): target.setExpression(name, expr)
                if not expr: setattr(target, name, getattr(obj, name))
        finally: self.busy = False


class Component:
    def getSubObjects(self,obj,reason):
        # STEP export traverses subobjects even for Part::FeaturePython. Only
        # final results are geometric children; the browser is supplied by the
        # view provider. Exporting Group would include hidden tools and planes.
        return [o.Name+'.' for o in obj.InventorResults]
    def execute(self, obj):
        shapes = [o.Shape for o in obj.InventorResults if hasattr(o, 'Shape') and not o.Shape.isNull()]
        obj.Shape = Part.makeCompound(shapes) if len(shapes)>1 else shapes[0].copy() if shapes else Part.Shape()


def appearance(source, target):
    if not App.GuiUp:return
    for prop in ('ShapeAppearance','LineColor','PointColor','Transparency'):
        if prop in source.ViewObject.PropertiesList and prop in target.ViewObject.PropertiesList:
            setattr(target.ViewObject,prop,getattr(source.ViewObject,prop))


def component(doc, name, label, nested=True):
    obj = doc.addObject('Part::FeaturePython', name)
    # Own Shape contains final bodies only. App::Part would collect hidden
    # intermediate solids and work-plane faces when read through an App::Link.
    obj.addExtension('App::GeoFeatureGroupExtensionPython' if nested else 'App::GroupExtensionPython')
    obj.Label = label
    linkProperty(obj, 'InventorResults', [])
    linkProperty(obj, 'InventorChildren', [])
    obj.Proxy = Component()
    if App.GuiUp:
        SourceView(obj.ViewObject)
        obj.ViewObject.ShowInTree = False
    obj.Visibility = False
    return obj


def primary(feature):
    if 'InventorExtrusion' in feature.PropertiesList:return feature.InventorExtrusion
    if feature.isDerivedFrom('Part::Cut'): return feature.Tool
    tools = list(getattr(feature, 'Tools', []))
    return tools[0] if len(tools)==1 else feature


def dimensionExpression(target, expression):
    # Extents to a face can reference computed native properties such as
    # .TargetPoint. Those properties do not belong to the browser mirror.
    # Qualify the source object rather than accidentally rebinding to it.
    return re.sub(r'(?<![\w.>])\.([A-Za-z_]\w*)',
                  lambda match: target.Name+'.'+match[1] if match[1] in target.PropertiesList else match[0],
                  expression)


def featureNode(doc, node, parameters, owner):
    native = node.geometry
    obj = doc.addObject('Part::FeaturePython', 'InventorFeature')
    if owner: owner.addObject(obj)
    obj.Label = node.name or native.Label
    obj.addProperty('App::PropertyString','InventorFeatureType','Inventor import').InventorFeatureType = node.typeName if node.typeName.startswith('Sketch') else node.node.getSubTypeName() if hasattr(node,'node') else node.getSubTypeName()
    obj.addProperty('App::PropertyInteger','InventorSourceIndex','Inventor import').InventorSourceIndex = node.index
    if 'InventorConstraintNotes' in native.PropertiesList:
        obj.addProperty('App::PropertyStringList','InventorConstraintNotes','Inventor import').InventorConstraintNotes=list(native.InventorConstraintNotes)
        obj.setEditorMode('InventorConstraintNotes',1)
    linkProperty(obj, 'InventorNativeFeature', native, False)
    target = native if node.typeName.startswith('Sketch') else primary(native)
    linkProperty(obj, 'InventorParameterTarget', target, False)
    linkProperty(obj, 'InventorChildren', [])
    obj.addProperty('App::PropertyLinkGlobal','DimensionTable','Inventor dimensions').DimensionTable = parameters
    names = []
    for name in target.PropertiesList:
        controls=('Operation','Extent','Direction','EndFace','StartFace') if 'CalculatedLength' in target.PropertiesList else ()
        if name not in ('LengthFwd','LengthRev','Reversed','Symmetric','TaperAngle','Height','Revolutions',
                        'Pitch','Clockwise','Distance1','Distance2','Angle','Flip')+controls and not name.startswith('Radius'): continue
        typ = target.getTypeIdOfProperty(name)
        if typ not in ('App::PropertyLength','App::PropertyDistance','App::PropertyAngle','App::PropertyBool','App::PropertyFloat',
                       'App::PropertyEnumeration','App::PropertyVector','App::PropertyLinkSub','App::PropertyLinkSubList',
                       'App::PropertyLinkSubGlobal','App::PropertyLinkSubListGlobal'): continue
        obj.addProperty({'App::PropertyLinkSub':'App::PropertyLinkSubGlobal','App::PropertyLinkSubList':'App::PropertyLinkSubListGlobal'}.get(typ,typ), name, 'Inventor dimensions')
        if typ=='App::PropertyEnumeration':setattr(obj,name,target.getEnumerationsOfProperty(name))
        setattr(obj, name, getattr(target,name)); names.append(name)
    obj.addProperty('App::PropertyString','InventorDimensionNames','Inventor structure').InventorDimensionNames = json.dumps(names)
    obj.setEditorMode('InventorDimensionNames',2)
    for name, expression in target.ExpressionEngine:
        if name in names: obj.setExpression(name, dimensionExpression(target, expression))
    SourceFeature(obj)
    obj.setEditorMode('Placement',1)
    if App.GuiUp: SourceView(obj.ViewObject)
    obj.Proxy.execute(obj)
    appearance(native,obj)
    obj.Visibility = False
    return obj


def sourceMark(obj, kind, index=0):
    if 'InventorSourceKind' not in obj.PropertiesList:
        obj.addProperty('App::PropertyString','InventorSourceKind','Inventor import')
        obj.addProperty('App::PropertyInteger','InventorBrowserIndex','Inventor import')
    obj.InventorSourceKind = kind; obj.InventorBrowserIndex = index


def owned(doc, owner, typ, name, label):
    obj = doc.addObject(typ, name); obj.Label = label
    if owner: owner.addObject(obj)
    return obj


def rootEntries(model):
    browser = model.getBrowser()
    nodes = list(browser.elementNodes.values())
    roots = [n for n in nodes if n.typeName=='F7676AB1' and n.get('items')]
    if len(roots)==1: return roots[0].get('items')
    roots = [n for n in nodes if n.typeName=='2524F6EB']
    return roots[0].get('lst0') or [] if len(roots)==1 else []


def inputSketches(native):
    target = primary(native)
    if 'InventorProfile' in target.PropertiesList:
        profile=target.InventorProfile
        return list(getattr(profile,'Sketches',[]))+[t.Sketch for t in getattr(profile,'Texts',[])]
    profile = getattr(target, 'Profile', None) or getattr(target, 'Base', None)
    if profile is None: return []
    return list(getattr(profile, 'Sketches', []))+[t.Sketch for t in getattr(profile, 'Texts', [])]


def organize(model, importer, finals, before, owner=None):
    doc = App.ActiveDocument
    dc = model.getDC(); src = dc.tree.getFirstChild('Document').get('component')
    objects = list(src.get('objects'))
    created = [o for o in doc.Objects if o.Name not in before]
    for obj in created:
        if App.GuiUp: obj.ViewObject.ShowInTree = False
        # FreeCAD may enforce unique labels. Reserve the original names for
        # source browser nodes instead of silently turning Coil1 into Coil002.
        obj.addProperty('App::PropertyString','InventorOriginalLabel','Inventor structure').InventorOriginalLabel=obj.Label
        obj.setEditorMode('InventorOriginalLabel',2)
        obj.Label='[internal] '+obj.Name
    mapped = {}; used = set(); exposed = []; notes = []
    features = [n for n in objects if n.typeName=='Feature' and n.geometry is not None]
    def geometry(ref, parent=None):
        candidates = [n for n in objects if n.name and n.name == ref.name and
                      (n.typeName == ref.typeName or ref.typeName=='3dObject' and n.typeName in ('Plane','Line3D','Point3D'))]
        if len(candidates)==1: return candidates[0]
        if ref.typeName=='Sketch2D' and parent is not None:
            sketches = inputSketches(parent.geometry)
            candidates = [n for n in objects if n.typeName=='Sketch2D' and n.geometry in sketches]
            if len(candidates)==1: return candidates[0]
        return None
    def present(obj, ref=None):
        if App.GuiUp: obj.ViewObject.ShowInTree = True
        if obj not in exposed: exposed.append(obj)
        if ref: sourceMark(obj,ref.typeName,ref.index)
        return obj
    def metadata(ref):
        obj = owned(doc,owner,'App::FeaturePython','InventorEntry',ref.name or ('End of Part' if ref.typeName=='EndOfPart' else ref.typeName))
        sourceMark(obj,ref.typeName,ref.index)
        obj.addProperty('App::PropertyString','InventorStatus','Inventor import').InventorStatus = 'Stored browser entry; no additional geometry reconstructed'
        return present(obj)
    def materialize(ref, parent=None, seen=()):
        if ref.index in seen: raise ValueError('Cyclic Inventor browser entry')
        if ref.index in mapped: return mapped[ref.index]
        kind = ref.typeName
        if kind in ('FolderBrowser','FolderBodies','FolderAnnotations'):
            items = list(ref.get('items') or [])
            if kind=='FolderBodies' and not items: return None
            label = ref.name
            if not label and kind=='FolderBodies':
                names = [n.name for n in objects if n.typeName=='BodiesFolder' and n.name]
                label = next((n for n in names if ('Solid' in n)==(ref.get('u16_0')==2)), 'Solid Bodies' if ref.get('u16_0')==2 else 'Surface Bodies')
            obj = owned(doc,owner,'App::DocumentObjectGroup','InventorFolder',label or kind)
            mapped[ref.index] = present(obj,ref)
            obj.Group = [child for item in items if (child:=materialize(item,parent,seen+(ref.index,))) is not None]
            return obj
        if kind=='Feature':
            node = geometry(ref)
            if node is None: notes.append('Unresolved browser feature: '+str(ref.name)); return None
            obj = featureNode(doc,node,importer.parameters,owner); used.add(node.index)
            obj.Label=ref.name or node.name
            mapped[ref.index] = present(obj,ref)
            obj.InventorChildren = [child for r in ref.get('items') or [] if (child:=materialize(r,node,seen+(ref.index,))) is not None]
            return obj
        if kind in ('Sketch2D','3dObject'):
            node = geometry(ref,parent)
            if node is None: return None
            native = importer.getGeometry(node)
            if native is None: native = node.geometry
            if native is None: return None
            obj=featureNode(doc,node,importer.parameters,owner) if kind=='Sketch2D' else native
            used.add(node.index); mapped[ref.index] = present(obj,ref)
            obj.Label = ref.name or node.name or obj.Label
            if kind=='Sketch2D':
                children = [child for r in ref.get('items') or [] if (child:=materialize(r,node,seen+(ref.index,))) is not None]
                texts = [o for o in doc.Objects if getattr(o,'Sketch',None) is native and 'String' in o.PropertiesList]
                children += [present(o) for o in texts]
                obj.InventorChildren=children
            return obj
        if kind=='ProjectedLoop' and parent is not None:
            projection = getattr(parent.geometry,'ProjectionObject',None)
            if projection is not None:
                obj=owned(doc,owner,'Part::FeaturePython','InventorProjectedLoop',ref.name)
                linkProperty(obj,'InventorResults',[projection]);linkProperty(obj,'InventorChildren',[])
                obj.Proxy=Component()
                if App.GuiUp:SourceView(obj.ViewObject)
                obj.Proxy.execute(obj);obj.Visibility=False
                mapped[ref.index] = present(obj,ref); return obj
        if kind=='Body':
            body = importer.bodyNodes.get(ref.name)
            if body is not None and body.geometry is not None:
                obj=owned(doc,owner,'Part::FeaturePython','InventorBodyEntry',ref.name)
                linkProperty(obj,'InventorResults',[body.geometry]);linkProperty(obj,'InventorChildren',[])
                obj.Proxy=Component()
                if App.GuiUp:SourceView(obj.ViewObject)
                obj.Proxy.execute(obj);obj.Visibility=False
                mapped[ref.index]=present(obj,ref);return obj
        if kind in ('Body','EndOfPart','AnnotationText','E149D710','ProjectedLoop'):
            obj = metadata(ref); mapped[ref.index] = obj; return obj
        return None
    roots = [obj for ref in rootEntries(model) if (obj:=materialize(ref)) is not None]
    # A changed component revision can contain a newer feature than its saved
    # browser cache. Retain that source feature; do not hide an unmapped result.
    for node in features:
        if node.index not in used:
            obj = featureNode(doc,node,importer.parameters,owner); sourceMark(obj,'Feature')
            obj.InventorChildren = inputSketches(node.geometry)
            for sketch in obj.InventorChildren: present(sketch)
            roots.append(present(obj)); notes.append('Feature absent from cached browser: '+str(node.name))
    # Also retain explicit named work planes/axes not consumed by any feature.
    for node in objects:
        if node.typeName not in ('Plane','Line3D','Point3D','Sketch2D','Sketch3D') or not node.name or node.index in used: continue
        obj = importer.getGeometry(node) or node.geometry
        if obj is not None and obj not in exposed:
            obj.Label=node.name; sourceMark(obj,node.typeName); roots.append(present(obj))
    mirrors = [o for o in exposed if hasattr(o,'InventorNativeFeature') and getattr(o,'InventorSourceKind','')=='Feature']
    for obj in created:
        if hasattr(obj,'Shape'): obj.Visibility=False
    # Work features created while organizing were not in the initial list.
    for obj in exposed:
        if hasattr(obj,'Shape'): obj.Visibility=False
    for mirror in mirrors:
        if mirror.InventorNativeFeature in finals: mirror.Visibility = owner is None
    if owner:
        owner.InventorResults = finals; owner.InventorChildren = roots
        owner.Proxy.execute(owner)
    record = dict(roots=[o.Name for o in roots],source_order=[o.Label for o in roots],
                  feature_labels=[o.Label for o in mirrors],notes=notes)
    target = owner or finals[-1]
    target.addProperty('App::PropertyString','InventorStructure','Inventor import').InventorStructure = json.dumps(record)
    return roots


def assemblySpecification(model):
    document = model.getDC().tree.getFirstChild('Document')
    source = document.get('component')
    datums = []
    for node in source.get('objects'):
        if not node.name or node.typeName not in ('Plane','Line3D','Point3D'): continue
        datum = dict(kind=node.typeName,label=node.name,index=node.index)
        if node.typeName=='Plane': datum.update(center=list(node.get('center')*10),x=list(node.get('a1')),y=list(node.get('normal')))
        elif node.typeName=='Line3D': datum.update(start=list(node.get('pos')*10),end=list((node.get('pos')+node.get('dir'))*10))
        else: datum['point'] = list(node.get('pos')*10)
        datums.append(datum)
    def browserEntry(node):
        if node.typeName=='767A2031':return dict(kind='Occurrence',label=node.name)
        if node.typeName=='9180FF9E':return dict(kind='Origin',label=node.name or 'Origin')
        if node.typeName=='EA6894C1':return dict(kind='Constraints',label=node.name,children=[dict(label=n.name,kind=n.typeName) for n in node.get('lst0') or []])
        return None
    tree=[entry for n in rootEntries(model) if (entry:=browserEntry(n)) is not None]
    return dict(datums=datums,order=[n.name for n in model.getDC().elementNodes.values() if n.typeName=='90874D61'],tree=tree)


class Datum:
    def execute(self,obj):
        if obj.InventorSourceKind=='Line3D': obj.Shape = Part.makeLine(obj.Start,obj.End)
        else: obj.Shape = Part.Vertex(obj.Point)


def assemblyOrigin(doc, owner, spec):
    from importerNative import DatumPlane
    group = owned(doc,owner,'App::DocumentObjectGroup','InventorOrigin','Origin')
    sourceMark(group,'Origin')
    for datum in spec['datums']:
        obj = owned(doc,owner,'Part::FeaturePython','InventorDatum',datum['label'])
        sourceMark(obj,datum['kind'],datum['index'])
        if datum['kind']=='Plane':
            DatumPlane(obj)
            x,y=App.Vector(datum['x']),App.Vector(datum['y'])
            obj.Placement=App.Placement(App.Vector(datum['center']),App.Rotation(x,y,x.cross(y),'ZXY'))
        else:
            for name,key in (('Start','start'),('End','end')) if datum['kind']=='Line3D' else (('Point','point'),):
                obj.addProperty('App::PropertyVector',name,'Datum');setattr(obj,name,App.Vector(datum[key]))
            obj.Proxy=Datum()
        if App.GuiUp: SourceView(obj.ViewObject)
        obj.Proxy.execute(obj);obj.Visibility=False
        group.addObject(obj)
    return group


def assemblyFolders(doc,owner,spec):
    roots=[]
    for entry in spec['tree']:
        if entry['kind']=='Occurrence':continue
        if entry['kind']=='Origin':
            obj=assemblyOrigin(doc,owner,spec);obj.Label=entry['label'];roots.append(obj)
        elif entry['kind']=='Constraints':
            obj=owned(doc,owner,'App::DocumentObjectGroup','InventorConstraints',entry['label'])
            sourceMark(obj,'Constraints');roots.append(obj)
            for record in entry['children']:
                child=owned(doc,owner,'App::FeaturePython','InventorConstraint',record['label'] or record['kind'])
                sourceMark(child,record['kind'])
                child.addProperty('App::PropertyString','InventorStatus','Inventor import').InventorStatus='Stored source constraint entry; assembly retains saved rigid placement'
                obj.addObject(child)
    if not any(getattr(o,'InventorSourceKind','')=='Origin' for o in roots):roots.append(assemblyOrigin(doc,owner,spec))
    return roots
