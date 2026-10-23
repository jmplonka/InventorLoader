"""Parametric reconstruction of the feature definitions stored in an IPT."""
import json
import math
import FreeCAD as App
import Part
import Sketcher
import importerFreeCAD as F
from importerClasses import getModel
from importerUtils import getIconPath


class NativeView:
    """Expose actual profile/Boolean dependencies in the feature tree."""
    def __init__(self,view):self.Object=view.Object;view.Proxy=self
    def attach(self,view):self.Object=view.Object
    def __getstate__(self):return None
    def __setstate__(self,state):return None
    def claimChildren(self):
        obj=self.Object
        if isinstance(obj.Proxy,Boolean):return [obj.Base]+list(obj.Tools)
        if isinstance(obj.Proxy,Coil):return [obj.Profile]
        if isinstance(obj.Proxy,Profile):return list(obj.Sketches)+list(obj.Sources)+list(getattr(obj,'Texts',[]))
        if isinstance(obj.Proxy,Projection):return [obj.Plane]
        return []
    def getIcon(self):
        proxy=self.Object.Proxy
        return getIconPath('FxCoil.svg' if isinstance(proxy,Coil) else
                             'FxBoundaryPatch.xpm' if isinstance(proxy,Profile) else 'FxCombine.png')


class DatumPlane:
    def __init__(self,obj):
        obj.Proxy=self
        if App.GuiUp:NativeView(obj.ViewObject)
    def execute(self,obj):
        placement=obj.Placement
        obj.Shape=Part.makePlane(20000,20000,App.Vector(-10000,-10000,0))
        obj.Placement=placement


class Projection:
    def __init__(self,obj,base,plane):
        obj.addProperty('App::PropertyLinkGlobal','Base','Projection').Base=base
        obj.addProperty('App::PropertyLinkGlobal','Plane','Projection').Plane=plane
        obj.Proxy=self
        if App.GuiUp:NativeView(obj.ViewObject)
    def execute(self,obj):
        axis=obj.Plane.Placement.Rotation.multVec(App.Vector(0,0,1))
        edges=[]
        for edge in obj.Base.Shape.Edges:
            curve=edge.Curve
            shape=curve.toShape() if curve.isClosed() else edge
            projected=obj.Plane.Shape.makeParallelProjection(shape,axis)
            for candidate in projected.Edges:
                if not any(abs(candidate.Length-e.Length)<1e-6 and
                           max((e.distToShape(Part.Vertex(candidate.valueAt(candidate.FirstParameter+(candidate.LastParameter-candidate.FirstParameter)*i/8)))[0] for i in range(9)))<1e-6 for e in edges):
                    edges.append(candidate)
        # Kernel recomputation may enumerate unchanged projected contours in a
        # different order. Keep their existing element numbers for live profiles.
        def key(edge):
            box=edge.BoundBox
            return (type(edge.Curve).__name__,)+tuple(round(v,6) for v in
                    (box.XMin,box.YMin,box.ZMin,box.XMax,box.YMax,box.ZMax,edge.Length))
        previous=[key(edge) for edge in obj.Shape.Edges]
        current={key(edge):edge for edge in edges}
        if len(current)==len(edges) and len(previous)==len(edges) and set(previous)==set(current):
            edges=[current[value] for value in previous]
        else:edges.sort(key=key)
        obj.Shape=Part.makeCompound(edges)


class Profile:
    """A selected, possibly trimmed sketch region that updates with its sketches."""
    def __init__(self, obj, sketches, records, sources, texts=()):
        obj.addProperty('App::PropertyLinkList','Sketches','Profile').Sketches=sketches
        obj.addProperty('App::PropertyLinkList','Sources','Profile').Sources=sources
        obj.addProperty('App::PropertyLinkList','Texts','Profile').Texts=list(texts)
        obj.addProperty('App::PropertyString','Selection','Profile').Selection=json.dumps(records)
        obj.Proxy=self
        if App.GuiUp:NativeView(obj.ViewObject)

    def execute(self, obj):
        edges=[]
        for text in getattr(obj,'Texts',[]):
            if text.Shape.isNull() or not text.Shape.isValid():
                obj.Shape=Part.Shape()
                raise ValueError('The linked sketch text has no valid contours')
            # Text edits can change the number of glyphs and holes. Consume its
            # current complete outline rather than saved EdgeN references.
            edges.extend(text.Shape.Edges)
        for record in json.loads(obj.Selection):
            sketch=obj.Sketches[record['sketch']]
            if 'source' in record:
                edge=obj.Sources[record['source']].Shape.getElement(record['element']).copy()
                if not record['full']:
                    first,last=edge.FirstParameter,edge.LastParameter
                    a,b=[first+(last-first)*u for u in record['interval']]
                    edge=edge.Curve.toShape(a,b)
                edges.append(edge)
                continue
            geometry=sketch.Geometry[record['geometry']]
            if record['full']:
                edge=geometry.toShape()
            else:
                first,last=geometry.FirstParameter,geometry.LastParameter
                a,b=[first+(last-first)*u for u in record['interval']]
                edge=geometry.toShape(a,b)
            edge.Placement=sketch.Placement.multiply(edge.Placement)
            edges.append(edge)
        wires=[Part.Wire(group) for group in Part.sortEdges(edges)]
        if not wires or any(not wire.isClosed() for wire in wires):
            raise ValueError('The selected sketch profile is not closed')
        obj.Shape=wires[0] if len(wires)==1 else Part.makeCompound(wires)


class Coil:
    """Recomputable circular screw sweeps, with one sweep per profile loop."""
    def __init__(self,obj,profile,base,axis,height,turns,clockwise,reverse):
        obj.addProperty('App::PropertyLink','Profile','Coil').Profile=profile
        obj.addProperty('App::PropertyVector','AxisBase','Coil').AxisBase=base
        obj.addProperty('App::PropertyVector','Axis','Coil').Axis=axis
        obj.addProperty('App::PropertyLength','Height','Coil').Height=height
        obj.addProperty('App::PropertyFloat','Revolutions','Coil').Revolutions=turns
        obj.addProperty('App::PropertyBool','Clockwise','Coil').Clockwise=clockwise
        obj.addProperty('App::PropertyBool','Reversed','Coil').Reversed=reverse
        obj.Proxy=self
        if App.GuiUp:NativeView(obj.ViewObject)

    def execute(self,obj):
        import Acis
        if obj.Height.Value<=0 or obj.Revolutions<=0:raise ValueError('Coil height and revolutions must be positive')
        axis=App.Vector(obj.Axis).normalize()*(-1 if obj.Reversed else 1)
        angle=2*math.pi*obj.Revolutions
        solids=[]
        for wire in obj.Profile.Shape.Wires:
            if len(wire.Edges)!=1 or not isinstance(wire.Edges[0].Curve,Part.Circle):
                raise ValueError('Parametric coil currently requires circular profile loops')
            circle=wire.Edges[0].Curve
            center=obj.AxisBase+axis*((circle.Center-obj.AxisBase).dot(axis))
            helix=Acis.Helix()
            helix.posCenter=center
            helix.dirMajor=circle.Center-center
            helix.dirMinor=axis.cross(helix.dirMajor)*(-1 if obj.Clockwise else 1)
            helix.dirPitch=axis*(obj.Height.Value/obj.Revolutions)
            helix.radAngles=Acis.Interval(Acis.Range('F',0),Acis.Range('F',angle))
            if abs(abs(circle.Axis.dot(axis))-1)>1e-9:
                raise ValueError('Coil profile must be perpendicular to its axis')
            # A fixed trihedron keeps circular sections parallel to the sketch.
            # OpenCascade builds the pipe and caps consistently, avoiding the
            # fragile intersections of independently sewn sweep surfaces.
            pipe=Part.BRepOffsetAPI.MakePipeShell(Part.Wire(helix.build()))
            pipe.setTrihedronMode(circle.Center,circle.Axis)
            pipe.setTolerance(1e-7,1e-7,1e-7)
            pipe.add(wire,False,False);pipe.build();pipe.makeSolid()
            solid=pipe.shape()
            if solid.Volume<0:solid.reverse()
            if not solid.isValid() or not solid.isClosed():raise ValueError('Coil sweep did not produce a valid solid')
            if solid.getTolerance(1)>1e-4:raise ValueError('Coil sweep exceeds the geometry tolerance budget')
            solid.check(True)
            solids.append(solid)
        obj.Shape=solids[0] if len(solids)==1 else Part.makeCompound(solids)


class ThroughAll:
    def __init__(self,obj,base,profile,direction,reverse,symmetric):
        obj.addProperty('App::PropertyLink','Base','Extent').Base=base
        obj.addProperty('App::PropertyLink','Profile','Extent').Profile=profile
        obj.addProperty('App::PropertyVector','Direction','Extent').Direction=direction
        obj.addProperty('App::PropertyBool','Reversed','Extent').Reversed=reverse
        obj.addProperty('App::PropertyBool','Symmetric','Extent').Symmetric=symmetric
        obj.addProperty('App::PropertyLength','Length','Extent')
        obj.Proxy=self
    def execute(self,obj):
        direction=App.Vector(obj.Direction).normalize()*(-1 if obj.Reversed else 1)
        def bounds(shape):
            box=shape.BoundBox
            values=[direction.dot(box.getPoint(i)) for i in range(8)]
            return min(values),max(values)
        low,high=bounds(obj.Base.Shape)
        start,end=bounds(obj.Profile.Shape)
        margin=0.001
        obj.Length=(2*max(high-start,end-low)+margin if obj.Symmetric else max(high-start,0)+margin)


class Boolean:
    def __init__(self,obj,base,tools,operation):
        obj.addProperty('App::PropertyLinkGlobal','Base','Boolean').Base=base
        obj.addProperty('App::PropertyLinkListGlobal','Tools','Boolean').Tools=tools
        obj.addProperty('App::PropertyEnumeration','Operation','Boolean').Operation=['Join','Cut','Intersection']
        obj.Operation=operation
        obj.Proxy=self
        if App.GuiUp:NativeView(obj.ViewObject)

    def execute(self,obj):
        shape=obj.Base.Shape.copy()
        for tool in obj.Tools:
            shape={'Join':shape.fuse,'Cut':shape.cut,'Intersection':shape.common}[obj.Operation](tool.Shape)
        if shape.isNull() or not shape.isValid():raise ValueError('Parametric Boolean operation produced invalid geometry')
        obj.Shape=shape.removeSplitter()


class Importer(F.FreeCADImporter):
    def __init__(self,source=None):
        super().__init__()
        self.source=source
        self.profiles={}
        self.failures=[]
        self.externalIndices={}

    def getGeometry(self,node):
        if self.failures:raise ValueError(self.failures[0])
        result=super().getGeometry(node)
        if self.failures:raise ValueError(self.failures[0])
        return result

    @staticmethod
    def constraintGeometry(geometry):
        shape=geometry.toShape()
        if shape.ShapeType=='Vertex':return [shape.Point]
        return [shape.valueAt(shape.FirstParameter+(shape.LastParameter-shape.FirstParameter)*u) for u in (0,.25,.5,.75,1)]

    def checkedConstraint(self,sketch,before,count,key):
        status=sketch.solve()
        drift=max(((a-b).Length for old,new in zip(before,sketch.Geometry)
                   for a,b in zip(self.constraintGeometry(old),self.constraintGeometry(new))),default=0)
        if status==0 and drift<=1e-6:return True
        for index in range(sketch.ConstraintCount-1,count-1,-1):sketch.delConstraint(index)
        # Restoring the exact source geometry keeps profile intervals valid;
        # removing a bad constraint alone leaves the solver's displaced curves.
        sketch.Geometry=before+list(sketch.Geometry[len(before):]);sketch.solve()
        self.mapConstraints.pop(key,None)
        if 'InventorConstraintNotes' not in sketch.PropertiesList:
            sketch.addProperty('App::PropertyStringList','InventorConstraintNotes','Inventor import');sketch.setEditorMode('InventorConstraintNotes',1)
        sketch.InventorConstraintNotes=list(sketch.InventorConstraintNotes)+[
            '%s: source constraint not bound (solver %s; displacement %.9g mm)'%(key,status,drift)]
        return False

    def addConstraint(self,sketch,constraint,key):
        if getattr(self,'checkingDimension',False):return super().addConstraint(sketch,constraint,key)
        before=[g.copy() for g in sketch.Geometry];count=sketch.ConstraintCount
        index=super().addConstraint(sketch,constraint,key)
        return index if self.checkedConstraint(sketch,before,count,key) else None

    def addDimensionConstraint(self,sketch,dimension,constraint,key,useExpression=True):
        before=[g.copy() for g in sketch.Geometry];count=sketch.ConstraintCount
        self.checkingDimension=True
        try:index=super().addDimensionConstraint(sketch,dimension,constraint,key,useExpression)
        finally:self.checkingDimension=False
        return index if self.checkedConstraint(sketch,before,count,key) else None

    def addDistanceConstraint(self,sketch,node,name,prefix):
        if name not in ('DistanceX','DistanceY'):return super().addDistanceConstraint(sketch,node,name,prefix)
        if F.skipConstraint(F.BIT_DIM_DISTANCE):return
        first,second=node.get('entity1'),node.get('entity2')
        i,p,j,q=self.getIndexPos(sketch,first,second)
        if i is None or j is None or i==j or (p is not None and q is not None):
            return super().addDistanceConstraint(sketch,node,name,prefix)
        # FreeCAD accepts projected point-to-point distances, but its five-
        # argument point-to-line form exists only for perpendicular Distance.
        lineIndex=j if q is None else i
        line=sketch.Geometry[lineIndex]
        if not isinstance(line,Part.LineSegment):return
        delta=line.EndPoint-line.StartPoint
        axis=0 if name=='DistanceX' else 1
        if abs(delta[axis])>1e-7:
            F.logWarning('Projected point-to-inclined-line dimension retained in source parameters\n');return
        p=1 if p is None else p;q=1 if q is None else q
        a,b=sketch.getPoint(i,p),sketch.getPoint(j,q)
        dimension=F.getDimension(node,'parameter');value=F.getMM(dimension)
        signed=math.copysign(abs(value),b[axis]-a[axis])
        key='Projected%s_%s_%s'%(name,i,j)
        before=[g.copy() for g in sketch.Geometry];count=sketch.ConstraintCount
        self.checkingDimension=True
        try:
            constraint=Sketcher.Constraint(name,i,p,j,q,signed)
            index=super().addDimensionConstraint(sketch,dimension,constraint,key,False)
            alias=dimension.get('alias')
            if alias:sketch.setExpression('Constraints[%d]'%index,('-' if signed*value<0 else '')+alias)
        finally:self.checkingDimension=False
        if self.checkedConstraint(sketch,before,count,key):node.setGeometry(constraint,index)

    def getPointIndexPos(self,sketch,point,entity):
        if entity.typeName=='Point2D':
            # Two points can lie on only part of a longer sketch line. Their
            # dimension must not become the length of that complete line.
            return self.findEntityPos(sketch,point)+self.findEntityPos(sketch,entity)
        return super().getPointIndexPos(sketch,point,entity)

    def addSketch_Text2D(self,node,sketch):
        record=node.get('text')
        if record is not None and not record.get('lst1'):
            from importerText import createAnnotation
            annotation=createAnnotation(App.ActiveDocument,sketch,record)
            if annotation is not None and self.root:self.root.addObject(annotation)
        node.setGeometry(None)

    def createParameterTable(self, component):
        before={o.Name for o in App.ActiveDocument.Objects}
        super().createParameterTable(component)
        self.parameters=next(o for o in App.ActiveDocument.Objects if o.Name not in before and o.TypeId=='Spreadsheet::Sheet')
        if self.root:self.root.addObject(self.parameters)
        # Every component has an independent namespace, even when its parameters
        # use the same Inventor names (d0, d1, ...).
        for node in component.segment.elementNodes.values():
            alias=node.get('alias')
            if alias and alias.startswith('Parameters.'):
                node.set('alias',self.parameters.Name+alias[len('Parameters'):],None)

    def createSketch(self, node, kind):
        old=self.mapConstraints
        self.mapConstraints={}
        try:
            sketch=super().createSketch(node,kind)
            if sketch.solve()==-2:
                sketch.autoRemoveRedundants()
                sketch.solve()
            return sketch
        finally:self.mapConstraints=old

    def addSketch_Dimension_Diameter2D(self, node, sketch):
        circle=node.get('circle')
        if circle.sketchIndex is None:return
        parameter=F.getDimension(node,'parameter')
        constraint=Sketcher.Constraint('Diameter',circle.sketchIndex,circle.geometry.Radius*2)
        index=self.addDimensionConstraint(sketch,parameter,constraint,'Diameter_%s'%circle.sketchIndex,True)
        node.setGeometry(constraint,index)

    def Create_Plane(self,node):
        # The stored a1/normal vectors are the in-plane X/Y basis, not a
        # plane normal (the legacy view-only decoder treated Y as Z).
        x=node.get('a1');y=node.get('normal');z=x.cross(y)
        if z.Length<1e-9:raise ValueError('Invalid work-plane coordinate frame')
        obj=F.newObject('Part::FeaturePython',node.name or 'WorkPlane')
        DatumPlane(obj)
        obj.Placement=App.Placement(F.p2v(node.get('center')),App.Rotation(x,y,z,'ZXY'))
        obj.Proxy.execute(obj);node.setGeometry(obj);F.hide(obj)
        if self.root:self.root.addObject(obj)

    def Create_Line3D(self,node):
        import InventorViewProviders as V
        obj=V.makeLine(F.p2v(node.get('pos')),F.p2v(node.get('pos')+node.get('dir')),node.name or 'WorkAxis')
        node.setGeometry(obj);F.hide(obj)
        if self.root:self.root.addObject(obj)

    def Create_Point3D(self,node):
        super().Create_Point3D(node)
        node.geometry.Label=node.name or 'WorkPoint'
        F.hide(node.geometry)
        if self.root:self.root.addObject(node.geometry)

    @staticmethod
    def attach(obj,base,element,mode,placement):
        if 'MapMode' not in obj.PropertiesList:obj.addExtension('Part::AttachExtensionPython')
        support='AttachmentSupport' if 'AttachmentSupport' in obj.PropertiesList else 'Support'
        setattr(obj,support,(base,[element] if element else []))
        obj.MapMode=mode
        obj.Document.recompute()
        frame=obj.Placement
        obj.AttachmentOffset=frame.inverse().multiply(placement)
        obj.Document.recompute()
        error=max(abs(a-b) for a,b in zip(obj.Placement.toMatrix().A,placement.toMatrix().A))
        if error>1e-6:raise ValueError('Sketch attachment changed its stored coordinate frame')

    def planarSupport(self,item):
        """Resolve the named source face on its creating feature, never a neighbour."""
        matches=[]
        attributes=getModel().getBRep().getDcSatAttributes()
        for ref in item.get('indexRefs') or []:
            face=item.segment.indexNodes[ref];creator=face.get('creator')
            if creator is None:continue
            base=self.getGeometry(item.segment.indexNodes[creator.get('idxCreator')])
            source=attributes.get(ref)
            if base is None or source is None:continue
            # Later cuts can change a face's boundary. A unique plane on the
            # explicitly named creator still identifies the original support.
            for i,candidate in enumerate(base.Shape.Faces,1):
                surface=candidate.Surface
                if not isinstance(surface,Part.Plane):continue
                for saved in source.getFaces():
                    if not saved.isPlane():continue
                    plane=saved.getSurface()
                    if (abs(abs(surface.Axis.dot(plane.normal))-1)<1e-8 and
                        abs(plane.root.distanceToPlane(surface.Position,surface.Axis))<1e-6):
                        match=(base,'Face%d'%i)
                        if match not in matches:matches.append(match)
        return matches[0] if len(matches)==1 else None

    def Create_Sketch2D(self,node):
        super().Create_Sketch2D(node)
        sketch=node.geometry;matrix=node.get('transformation');supports=[]
        for record in node.segment.elementNodes.values():
            if record.typeName not in ('Sketch2DPlacement','Sketch2DPlacementPlane'):continue
            transform=record.get('transformation2')
            if transform is None or transform.index!=matrix.index:continue
            if record.typeName=='Sketch2DPlacementPlane':
                plane=record.get('plane')
                if plane:supports.append((self.getGeometry(plane),'','ObjectXY'))
            else:
                item=record.get('ref_3')
                if item and item.typeName=='FaceItem':
                    support=self.planarSupport(item)
                    if support:supports.append((*support,'FlatFace'))
        supports=list(dict.fromkeys(supports))
        if len(supports)==1:
            base,element,mode=supports[0];placement=sketch.Placement
            self.attach(sketch,base,element,mode,placement)
            plane=getattr(sketch,'ProjectionPlane',None)
            if plane:self.attach(plane,base,element,mode,placement)
            sketch.addProperty('App::PropertyString','InventorAttachment','Inventor import').InventorAttachment='Linked to stored support'
        else:
            sketch.addProperty('App::PropertyString','InventorAttachment','Inventor import').InventorAttachment='Stored placement; support not uniquely reconstructed'
        # Mapping the completed sketch onto its support can introduce solver
        # redundancies that did not exist before the attachment was evaluated.
        if sketch.solve()==-2:
            sketch.autoRemoveRedundants();sketch.solve();sketch.Document.recompute()

    def createBoundary(self, patch):
        if patch.index in self.profiles:return self.profiles[patch.index]
        profile=patch.get('profile')
        if profile is None:raise ValueError('No parametric sketch profile in boundary')
        sketches=[];records=[];sources=[];texts=[]
        # Text outlines are saved as exact profile curves, separately from the
        # sketch's ordinary entity references. Keep them in an editable sketch.
        outlines=profile.get('lst1') or []
        if not profile.get('parts') and outlines:
            sourceSketch=profile.get('sketch')
            self.getGeometry(sourceSketch)
            from importerText import createText
            strings=profile.get('lst2') or []
            covered=set()
            for string in strings:
                selected=[o for o in string.get('lst1') or [] if o.index in {n.index for n in outlines}]
                if not selected:continue
                try:
                    text=createText(App.ActiveDocument,sourceSketch.geometry,string,selected,getModel())
                except ValueError as exc:
                    F.logWarning('Sketch text retains saved curves: %s\n',exc)
                    continue
                if self.root:self.root.addObject(text)
                self.attach(text,sourceSketch.geometry,'','ObjectXY',text.Placement)
                texts.append(text);covered.update(o.index for o in selected)
            remaining=[o for o in outlines if o.index not in covered]
            if remaining:
                textSketch=F.newObject('Sketcher::SketchObject',sourceSketch.name+'_TextContours')
                textSketch.Placement=sourceSketch.geometry.Placement
                for outline in remaining:
                    if outline.typeName!='19F763CB':raise ValueError('Unknown stored text outline format')
                    for curve in outline.get('edges'):
                        geometry=curve.getGeometry()
                        geometry.transform(textSketch.Placement.inverse().toMatrix())
                        index=textSketch.addGeometry(geometry)
                        records.append(dict(sketch=0,geometry=index,full=True,interval=[0,1]))
                self.attach(textSketch,sourceSketch.geometry,'','ObjectXY',textSketch.Placement)
                sketches.append(textSketch)
                if self.root:self.root.addObject(textSketch)

        for loop in profile.get('parts') or []:
            # Inner loops have operation==0 and must be retained as holes.
            for edge in loop.get('edges') or []:
                sketch=edge.get('sketch')
                if sketch is None:raise ValueError('Profile edge has no source sketch')
                self.getGeometry(sketch)
                entity=edge.get('curve') or F.getAssociatedSketchEntity(sketch,edge.get('entityAI'),edge.get('typEntity'))
                if entity is None or entity.sketchIndex is None:
                    raise ValueError('Profile curve cannot be mapped: sketch %s, edge %s, entity %s/%s, AI %s' %
                        (sketch.name,edge.index,getattr(entity,'typeName',None),getattr(entity,'index',None),edge.get('entityAI')))
                if sketch.geometry not in sketches:sketches.append(sketch.geometry)
                # Reuse the legacy trimming decoder, but retain the sketch link.
                temporary=F.newObject('Sketcher::SketchObject','ProfileDecoder')
                if isinstance(entity.geometry,Part.BSplineCurve) and entity.geometry.isClosed() and edge.get('point1AI')==edge.get('point2AI'):
                    temporary.addGeometry(entity.geometry.copy())
                else:
                    super().addGeometryFromNode(temporary,edge)
                if temporary.GeometryCount!=1:
                    p1=edge.get('point1') or F.getAssociatedSketchEntity(sketch,edge.get('point1AI'),edge.get('typPt1'))
                    p2=edge.get('point2') or F.getAssociatedSketchEntity(sketch,edge.get('point2AI'),edge.get('typPt2'))
                    if (temporary.GeometryCount==0 and isinstance(entity.geometry,(Part.Line,Part.LineSegment)) and
                        p1 is not None and p2 is not None and (F.p2v(p1)-F.p2v(p2)).Length<=1e-7):
                        # A zero-length selection between coincident source
                        # vertices contributes no profile edge.
                        App.ActiveDocument.removeObject(temporary.Name);continue
                    raise ValueError('Profile trimming failed')
                trimmed=temporary.Geometry[0].toShape()
                raw=entity.geometry.toShape()
                full=abs(trimmed.Length-raw.Length)<1e-7 and trimmed.distToShape(raw)[0]<1e-7
                interval=[0,1]
                if not full:
                    a=raw.Curve.parameter(trimmed.valueAt(trimmed.FirstParameter))
                    b=raw.Curve.parameter(trimmed.valueAt(trimmed.LastParameter))
                    if b<a and raw.Curve.isPeriodic():b+=raw.Curve.period()
                    interval=[(u-raw.FirstParameter)/(raw.LastParameter-raw.FirstParameter) for u in (a,b)]
                App.ActiveDocument.removeObject(temporary.Name)
                record=dict(sketch=sketches.index(sketch.geometry),geometry=entity.sketchIndex,full=full,interval=interval)
                external=entity.get('_nativeSource')
                if external:
                    source,element=external
                    if source not in sources:sources.append(source)
                    record.update(source=sources.index(source),element=element)
                records.append(record)
        obj=F.newObject('Part::FeaturePython',profile.get('sketch').name+'_Profile')
        Profile(obj,sketches,records,sources,texts)
        obj.Proxy.execute(obj)
        self.profiles[patch.index]=obj
        if self.root:self.root.addObject(obj)
        for sketch in sketches:F.hide(sketch)
        for text in texts:F.hide(text)
        return obj

    def addSketch_Spline2D(self,node,sketch):
        points=[F.p2v(p) for p in node.get('points')]
        if len(points)>=2 and (points[0]-points[1]).Length<1e-7:
            base=getattr(self,'lastActiveBody',None)
            if base is None or base.geometry is None:raise ValueError('Projected spline has no preceding feature')
            source=node.get('sketch')
            placement=F.getPlacement(source.get('transformation'))
            plane=getattr(sketch,'ProjectionPlane',None)
            if plane is None:
                plane=F.newObject('Part::FeaturePython',sketch.Name+'_Plane')
                DatumPlane(plane);plane.Placement=placement;plane.Proxy.execute(plane)
                sketch.addProperty('App::PropertyLink','ProjectionPlane','Inventor import').ProjectionPlane=plane
            section=getattr(sketch,'ProjectionObject',None)
            if section is None:
                section=F.newObject('Part::FeaturePython',sketch.Name+'_Projection')
                Projection(section,base.geometry,plane)
                sketch.addProperty('App::PropertyLink','ProjectionObject','Inventor import').ProjectionObject=section
            App.ActiveDocument.recompute()
            point=placement.multVec(points[0])
            matches=[(i,e) for i,e in enumerate(section.Shape.Edges,1) if e.isClosed() and e.distToShape(Part.Vertex(point))[0]<1e-5]
            if len(matches)!=1:return
            index,edge=matches[0]
            curve=edge.Curve.copy();curve.transform(placement.inverse().toMatrix())
            external=(section.Name,'Edge%d'%index)
            key=(sketch.Name,external)
            if key not in self.externalIndices:self.externalIndices[key]=sketch.addExternal(*external,True)
            number=self.externalIndices[key]
            node.setGeometry(curve,-3-(number or 0))
            node.set('_nativeSource',(section,'Edge%d'%index),None)
            F.hide([plane,section])
            if self.root:self.root.addObject(plane);self.root.addObject(section)
            return
        return super().addSketch_Spline2D(node,sketch)

    def createFxExtrude_Operation(self,node,section,name,suffix,kind):
        reference=F.getProperty(node.get('properties'),26)
        if reference is None:raise ValueError('Extrusion has no base-body reference')
        base=self.findBase(reference)
        if base is None:raise ValueError('Extrusion base could not be reconstructed')
        tool=self.Create_FxExtrude_New(node,section,name+suffix)
        if tool is None:raise ValueError('Extrusion tool could not be reconstructed')
        return self.createBoolean(kind,name,base,[tool])

    def Create_FxExtrude(self, node):
        properties=node.get('properties')
        operation=F.getPropertyValue(properties,0,'value')
        participants=node.getParticipants()
        if not participants:raise ValueError('Extrusion has no sketch')
        section=participants[0].node
        if operation in (self.FX_EXTRUDE_JOIN,self.FX_EXTRUDE_CUT,self.FX_EXTRUDE_NEW,self.FX_EXTRUDE_INTERSECTION,self.FX_EXTRUDE_SURFACE):
            from importerExtrusion import build
            result=build(self,node,{1:'NewBody',2:'Cut',3:'Join',4:'Intersection',5:'Surface'}[operation])
        else:raise ValueError('Unsupported extrusion operation: '+str(operation))
        if result is None:raise ValueError('Extrusion produced no feature')
        self.featureOperation(result,node,{1:'NewBody',2:'Cut',3:'Join',4:'Intersection',5:'Surface'}[operation])
        self.addBody(node,result,0x1A,0x10)
        if self.root:self.root.addObject(result)

    @staticmethod
    def featureOperation(obj,node,operation):
        obj.addProperty('App::PropertyString','InventorFeatureName','Inventor import').InventorFeatureName=node.name
        obj.addProperty('App::PropertyString','InventorFeatureType','Inventor import').InventorFeatureType=node.getSubTypeName()
        obj.addProperty('App::PropertyString','InventorOperation','Inventor import').InventorOperation=operation
        obj.Label=node.name+' ['+operation+']'
        if operation=='Cut':
            tools=[obj.Tool] if obj.isDerivedFrom('Part::Cut') else list(obj.Tools)
            for tool in tools:
                tool.Label=node.name+' [Cutting tool]';F.hide(tool)

    def Create_FxExtrude_New(self,node,section,name):
        p=node.get('properties')
        if F.getPropertyValue(p,6,'value')==7:
            descriptor=F.getProperty(p,18)
            if descriptor is None or descriptor.typeName!='151280F0':
                raise ValueError('Extrusion target plane is not supported')
            profile=self.createBoundary(F.getProperty(p,1))
            sketch=profile.Sketches[0] if profile.Sketches else profile.Texts[0].Sketch
            direction=F.getProperty(p,2).get('dir')
            reverse=F.getPropertyValue(p,3,'value')
            normal=descriptor.get('dir').cross(descriptor.get('point')).normalize()
            denominator=direction.dot(normal)*(-1 if reverse else 1)
            if abs(denominator)<1e-9:raise ValueError('Extrusion is parallel to its target plane')
            target=descriptor.get('pos')*10
            distance=(target-sketch.Placement.Base).dot(normal)/denominator
            if distance<=0:raise ValueError('Extrusion target is behind its direction')
            obj=F.newObject('Part::Extrusion',name)
            obj.Base=profile;obj.Solid=F.getProperty(p,26) is not None
            obj.Dir=direction;obj.Reversed=reverse
            obj.addProperty('App::PropertyVector','TargetPoint','Extent').TargetPoint=target
            obj.LengthFwd=distance
            terms=['(TargetPoint.%s*1 mm-%s.Placement.Base.%s)*%.17g'%(c,sketch.Name,c,v) for c,v in zip('xyz',normal) if abs(v)>1e-12]
            obj.setExpression('LengthFwd','(%s)/%.17g'%('+'.join(terms),denominator))
            F.setParameter(obj,'TaperAngle',F.getProperty(p,5),F.getGRAD)
            F.hide(profile)
            return obj
        # Building/attaching a profile can recompute the document. Complete it
        # before the legacy builder creates a Part::Extrusion with an empty Base.
        # Its subsequent createBoundary call reuses this cached live profile.
        self.createBoundary(F.getProperty(p,1))
        obj=super().Create_FxExtrude_New(node,section,name)
        if obj is not None:
            p=node.get('properties')
            # LengthRev/Symmetric already account for the negative extent in
            # FreeCAD. The legacy builder additionally translated it a second time.
            offset=obj.LengthRev.Value
            obj.Placement.Base += F.getProperty(p,2).get('dir')*offset
            if F.getPropertyValue(p,6,'value')==5:
                base=self.findBase(F.getProperty(p,26))
                extent=F.newObject('App::FeaturePython',name+'_ThroughAll')
                ThroughAll(extent,base,obj.Base,obj.Dir,obj.Reversed,obj.Symmetric)
                extent.Proxy.execute(extent)
                obj.LengthRev=0
                obj.setExpression('LengthFwd',extent.Name+'.Length')
                if self.root:self.root.addObject(extent)
        return obj

    def createBoolean(self,kind,name,base,tools):
        if base is None or not tools:raise ValueError('Boolean operation is missing its base or tool')
        App.ActiveDocument.recompute()
        if kind=='Cut':
            result=base
            for index,tool in enumerate(tools):
                obj=F.newObject('Part::Cut',name if index==len(tools)-1 else name+'_Removal%d'%(index+1))
                obj.Base=result;obj.Tool=tool;obj.Refine=True
                App.ActiveDocument.recompute()
                if obj.Shape.isNull() or not obj.Shape.isValid():raise ValueError('Native Cut produced invalid geometry')
                F.hide([result,tool]);result=obj
            return result
        obj=F.newObject('Part::FeaturePython',name)
        Boolean(obj,base,tools,{'MultiFuse':'Join','Cut':'Cut','MultiCommon':'Intersection'}[kind])
        obj.Proxy.execute(obj)
        F.hide([base]+list(tools))
        return obj

    def Create_FxChamfer(self,node):
        p=node.get('properties')
        kind=F.getProperty(p,4).node.getValueText().strip("'")
        if kind not in ('Distance','DistanceAndAngle','TwoDistances'):
            raise ValueError('Unsupported chamfer definition: '+kind)
        objects=[]
        for creator,indices in self.getEdgesFromSet(F.getProperty(p,0)).items():
            obj=F.newObject('Part::Chamfer',node.name)
            obj.Base=node.segment.indexNodes[creator].geometry
            self.dimension(obj,'Distance1',F.getProperty(p,2))
            if kind=='Distance':
                obj.addProperty('App::PropertyLength','Distance2','Chamfer')
                obj.setExpression('Distance2','Distance1')
            elif kind=='TwoDistances':
                self.dimension(obj,'Distance2',F.getProperty(p,3))
            else:
                obj.addProperty('App::PropertyAngle','Angle','Chamfer')
                F.setParameter(obj,'Angle',F.getProperty(p,10),F.getGRAD)
                obj.addProperty('App::PropertyLength','Distance2','Chamfer')
                obj.setExpression('Distance2','Distance1 * tan(Angle)')
            obj.addProperty('App::PropertyBool','Flip','Chamfer').Flip=F.getBOOL(F.getProperty(p,5))
            first='(Flip ? Distance2 : Distance1)'
            second='(Flip ? Distance1 : Distance2)'
            self.edgeExpression(obj,[(i+1,first,second) for i in indices])
            objects.append(obj);F.hide(obj.Base)
            if self.root:self.root.addObject(obj)
        if not objects:raise ValueError('Chamfer edges could not be resolved')
        self.addSolidBody(node,self.combineGeometries(objects,node),F.getProperty(p,11))

    @staticmethod
    def dimension(obj,name,parameter):
        obj.addProperty('App::PropertyLength',name,'Inventor dimensions')
        F.setParameter(obj,name,parameter,F.getMM)

    @staticmethod
    def edgeExpression(obj,entries):
        # PropertyFilletEdges stores immutable tuples. Bind the whole property;
        # expressions on Edges[n][1] fail during recomputation in FreeCAD 1.1.
        expression='list('+ '; '.join('tuple(%d; %s / 1 mm; %s / 1 mm)'%entry for entry in entries)+')'
        obj.setExpression('Edges',expression)

    def Create_FxFillet(self,node):
        p=node.get('properties');groups=[]
        constant=F.getProperty(p,0)
        if constant:
            groups.extend((g,g.get('radius'),g.get('radius')) for g in constant.get('sets'))
        variable=F.getProperty(p,1)
        if variable:
            for group in variable.get('sets'):
                radii=group.get('radii')
                if radii.get('additional'):
                    raise ValueError('Variable fillets with intermediate radii are not supported')
                extrema=radii.get('extrema')
                if len(extrema)!=2:raise ValueError('Variable fillet requires two endpoint radii')
                groups.append((group,extrema[0].get('radius'),extrema[1].get('radius')))
        definitions={}
        for index,(group,start,end) in enumerate(groups,1):
            edges=self.getEdgesFromSet(group.get('edges') or group.get('items'))
            if not edges:raise ValueError('Fillet edges could not be resolved')
            for creator,indices in edges.items():
                definitions.setdefault(creator,[]).append((index,indices,start,end))
        if not definitions:raise ValueError('Unsupported or empty fillet definition')
        objects=[]
        for creator,sets in definitions.items():
            obj=F.newObject('Part::Fillet',node.name)
            obj.Base=node.segment.indexNodes[creator].geometry
            entries=[]
            for index,indices,start,end in sets:
                first='Radius' if len(groups)==1 else 'Radius%d'%index
                self.dimension(obj,first,start)
                last=first
                if end is not start:
                    last=first+'End';self.dimension(obj,last,end)
                entries.extend((i+1,first,last) for i in indices)
            self.edgeExpression(obj,entries)
            objects.append(obj);F.hide(obj.Base)
        body=F.getProperty(p,15) or F.getProperty(p,16)
        self.addSolidBody(node,self.combineGeometries(objects,node),body)

    def createFromAcisData(self,node,body):
        from importerReference import recover
        shape=recover(getModel(),node)
        obj=F.newObject('Part::Feature',node.name)
        obj.Shape=shape
        obj.addProperty('App::PropertyString','InventorHistory','Inventor import').InventorHistory='Imported base in source; earlier construction features are not present'
        self.addSurfaceBody(node,obj,body)
        if self.root:self.root.addObject(obj)
        return obj

    def notYetImplemented(self,node,body=None):
        raise ValueError('Native reconstruction is not implemented for '+node.getSubTypeName())

    def Create_Feature(self, node):
        try:super().Create_Feature(node)
        except Exception as exc:
            self.failures.append('%s (%s): %s'%(node.name,node.getSubTypeName(),exc))
            raise

    def Create_FxCoil(self,node):
        p=node.get('properties')
        prop=lambda i:F.getProperty(p,i)
        if abs(F.getGRAD(prop(9)))>1e-12:raise ValueError('Tapered parametric coils are not yet supported')
        if F.getBOOL(prop(10)) or F.getBOOL(prop(13)):raise ValueError('Coil end transitions are not yet supported')
        kind=prop(5).node.getValueText()
        turns=prop(8).getValue().getNominalValue()
        height=F.getMM(prop(7))
        pitch=F.getMM(prop(6))
        if kind=='PitchAndRevolution':height=pitch*turns
        elif kind=='PitchAndHeight':turns=height/pitch
        elif kind!='RevolutionAndHeight':raise ValueError('Unsupported coil definition: '+kind)
        base=self.findBase(prop(19))
        profile=self.createBoundary(prop(1))
        obj=F.newObject('Part::FeaturePython',node.name+'_Sweep')
        Coil(obj,profile,F.p2v(prop(2)),prop(2).get('dir'),height,turns,F.getBOOL(prop(4)),F.getBOOL(prop(3)))
        if kind=='RevolutionAndHeight':
            F.setParameter(obj,'Height',prop(7),F.getMM)
            F.setParameter(obj,'Revolutions',prop(8))
        elif kind=='PitchAndRevolution':
            obj.addProperty('App::PropertyLength','Pitch','Coil')
            F.setParameter(obj,'Pitch',prop(6),F.getMM)
            F.setParameter(obj,'Revolutions',prop(8))
            obj.setExpression('Height','Pitch * Revolutions')
        elif kind=='PitchAndHeight':
            obj.addProperty('App::PropertyLength','Pitch','Coil')
            F.setParameter(obj,'Pitch',prop(6),F.getMM)
            F.setParameter(obj,'Height',prop(7),F.getMM)
            obj.setExpression('Revolutions','Height / Pitch')
        obj.Proxy.execute(obj)
        App.ActiveDocument.recompute()
        operation=F.getPropertyValue(p,0,'value')
        result=obj if operation==self.FX_EXTRUDE_NEW else self.createBoolean(
            {self.FX_EXTRUDE_JOIN:'MultiFuse',self.FX_EXTRUDE_CUT:'Cut',self.FX_EXTRUDE_INTERSECTION:'MultiCommon'}[operation],node.name,base,[obj])
        if result is None:raise ValueError('Coil base body is missing')
        self.featureOperation(result,node,{self.FX_EXTRUDE_NEW:'NewBody',self.FX_EXTRUDE_JOIN:'Join',self.FX_EXTRUDE_CUT:'Cut',self.FX_EXTRUDE_INTERSECTION:'Intersection'}[operation])
        self.addBody(node,result,19,17)
        if self.root:
            self.root.addObject(obj);self.root.addObject(result)
        F.hide(profile)
        if result is not obj:F.hide([base,obj])

    def build(self, root):
        original=F.newObject
        def owned(*args,**kwargs):
            obj=original(*args,**kwargs)
            if root:root.addObject(obj)
            return obj
        F.newObject=owned
        try:self.importModel(root)
        finally:F.newObject=original
        if self.failures:raise ValueError('; '.join(self.failures))
        component=getModel().getDC().tree.getFirstChild('Document').get('component')
        missing=[o.name for o in component.get('objects') if o.typeName=='Feature' and o.geometry is None]
        if missing:raise ValueError('Features not reconstructed: '+', '.join(missing))
        return list(dict.fromkeys(n.geometry for n in self.bodyNodes.values() if n.geometry is not None))
