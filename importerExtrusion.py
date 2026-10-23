"""Editable Inventor extrusion operations and extent controls."""
import math
import re
import FreeCAD as App
import Part
import importerFreeCAD as F

OPERATIONS=['NewBody','Join','Cut','Intersection','Surface']
EXTENTS=['Distance','TwoDistances','ThroughAll','ToFace','ToNext','FromTo']


def state(obj):
    import json
    values=[str(getattr(obj,p)) for p in ('Operation','Extent','LengthFwd','LengthRev','Reversed','Symmetric','TaperAngle','Direction')]
    for name in ('EndFace','StartFace'):
        ref=getattr(obj,name);values.append((ref[0].Name,list(ref[1])) if ref and ref[0] is not None else None)
    return json.dumps(values)


def plane(reference):
    obj,names=reference if reference else (None,[])
    if obj is None:raise ValueError('Select a planar termination face')
    shape=obj.Shape.getElement(names[0]) if names and names[0] else obj.Shape
    if shape.ShapeType!='Face':
        if len(shape.Faces)!=1:raise ValueError('Select one planar face')
        shape=shape.Faces[0]
    if not isinstance(shape.Surface,Part.Plane):raise ValueError('This extent requires a planar face')
    return shape.Surface.Position,shape.normalAt(0,0)


class Settings:
    def execute(self,obj):
        if 'MakeSolid' in obj.PropertiesList:obj.MakeSolid=obj.Operation!='Surface'
        direction=App.Vector(obj.Direction)
        if not all(math.isfinite(v) for v in direction) or direction.Length<1e-9:raise ValueError('Extrusion direction must be finite and nonzero')
        direction.normalize();direction*=(-1 if obj.Reversed else 1)
        profile=obj.Profile.Shape
        if not profile.Vertexes:raise ValueError('Extrusion profile is empty')
        origin=profile.Vertexes[0].Point
        points=[v.Point for v in profile.Vertexes]
        for edge in profile.Edges:
            points.extend(edge.valueAt(edge.FirstParameter+(edge.LastParameter-edge.FirstParameter)*i/4) for i in (1,2,3))
        obj.StartOffset=App.Vector()
        forward,backward=obj.LengthFwd.Value,obj.LengthRev.Value
        if obj.Extent=='Distance':backward=0
        elif obj.Extent=='ThroughAll':
            if obj.Base is None:raise ValueError('Through all requires a preceding body')
            box=obj.Base.Shape.BoundBox
            values=[direction.dot(box.getPoint(i)-origin) for i in range(8)]
            forward=(2*max(max(values),-min(values)) if obj.Symmetric else max(values))+0.001
            backward=0
        elif obj.Extent in ('ToFace','FromTo'):
            point,normal=plane(obj.EndFace)
            denominator=normal.dot(direction)
            if abs(denominator)<1e-9:raise ValueError('Extrusion direction is parallel to the termination face')
            distances=[(point-pointOnProfile).dot(normal)/denominator for pointOnProfile in points]
            if max(distances)-min(distances)>1e-6:raise ValueError('Termination face must be parallel to the profile plane')
            forward=distances[0];backward=0
            if obj.Extent=='FromTo':
                start,startNormal=plane(obj.StartFace)
                den=startNormal.dot(direction)
                if abs(den)<1e-9:raise ValueError('Extrusion direction is parallel to the start face')
                offsets=[(start-pointOnProfile).dot(startNormal)/den for pointOnProfile in points]
                if max(offsets)-min(offsets)>1e-6:raise ValueError('Start face must be parallel to the profile plane')
                obj.StartOffset=direction*offsets[0];forward-=offsets[0]
        elif obj.Extent=='ToNext':
            if obj.Base is None:raise ValueError('To next requires a preceding body')
            face=Part.makeFace(profile.Wires,'Part::FaceMakerBullseye')
            distances=[]
            for boundary in obj.Base.Shape.Faces:
                if not isinstance(boundary.Surface,Part.Plane):continue
                normal=boundary.normalAt(0,0);den=normal.dot(direction)
                if abs(den)<1e-9:continue
                ds=[(boundary.Surface.Position-pointOnProfile).dot(normal)/den for pointOnProfile in points]
                if max(ds)-min(ds)>1e-6 or ds[0]<=1e-7:continue
                moved=face.copy();moved.translate(direction*ds[0])
                if moved.cut(boundary).Area<=max(1e-6,face.Area*1e-8):distances.append(ds[0])
            if not distances:raise ValueError('No next planar face fully intersects the profile')
            forward=min(distances);backward=0
        if not math.isfinite(forward) or not math.isfinite(backward) or forward<=0 or backward<0:
            raise ValueError('Extrusion distances must be positive in the selected direction')
        if obj.Symmetric and obj.Extent not in ('Distance','ThroughAll'):
            raise ValueError('Symmetric direction is available for Distance and Through all')
        obj.CalculatedLength=forward;obj.CalculatedLength2=backward


class Result:
    def execute(self,obj):
        settings=obj.InventorExtrusion
        tool=obj.Tools[0].Shape
        operation=str(settings.Operation)
        if operation in ('Join','Cut','Intersection'):
            if obj.Base is None:raise ValueError(operation+' requires a preceding body')
            base=obj.Base.Shape
            shape={'Join':base.fuse,'Cut':base.cut,'Intersection':base.common}[operation](tool)
            shape=shape.removeSplitter()
        else:
            shape=tool.copy()
            if obj.Base is not None:shape=Part.makeCompound([obj.Base.Shape,shape])
        if shape.isNull() or not shape.isValid() or (operation!='Surface' and not shape.Solids):
            raise ValueError('Extrusion '+operation+' produced empty or invalid geometry')
        obj.Shape=shape
        obj.InventorModified=state(settings)!=settings.ImportedState


def build(importer,node,operation):
    p=node.get('properties');extent=F.getPropertyValue(p,6,'value')
    if extent not in (1,2,4,5,7):raise ValueError('Unsupported stored extrusion extent: '+str(extent))
    profile=importer.createBoundary(F.getProperty(p,1))
    App.ActiveDocument.recompute()
    tool=F.newObject('Part::Extrusion',node.name+'_Tool')
    tool.Base=profile;tool.Dir=F.getProperty(p,2).get('dir');tool.Solid=operation!='Surface'
    base=importer.findBase(F.getProperty(p,26)) if operation!='NewBody' else None
    settings=F.newObject('App::FeaturePython',node.name+'_ExtrusionOptions')
    for prop,values,value in [('Operation',OPERATIONS,operation),('Extent',EXTENTS,{1:'Distance',2:'TwoDistances',4:'ToNext',5:'ThroughAll',7:'ToFace'}[extent])]:
        settings.addProperty('App::PropertyEnumeration',prop,'Extrusion');setattr(settings,prop,values);setattr(settings,prop,value)
    for name,value in [('Base',base),('Profile',profile)]:
        settings.addProperty('App::PropertyLinkGlobal',name,'Extrusion');setattr(settings,name,value);settings.setEditorMode(name,2)
    for name in ('EndFace','StartFace'):settings.addProperty('App::PropertyLinkSubGlobal',name,'Extrusion')
    for name in ('LengthFwd','LengthRev','CalculatedLength','CalculatedLength2'):settings.addProperty('App::PropertyLength',name,'Extrusion')
    settings.addProperty('App::PropertyAngle','TaperAngle','Extrusion')
    for name in ('Reversed','Symmetric'):settings.addProperty('App::PropertyBool',name,'Extrusion')
    for name in ('Direction','StartOffset'):settings.addProperty('App::PropertyVector',name,'Extrusion')
    for name in ('CalculatedLength','CalculatedLength2','StartOffset'):settings.setEditorMode(name,2)
    F.setParameter(settings,'LengthFwd',F.getProperty(p,4),F.getMM)
    F.setParameter(settings,'LengthRev',F.getProperty(p,27),F.getMM)
    F.setParameter(settings,'TaperAngle',F.getProperty(p,5),F.getGRAD)
    settings.Direction=F.getProperty(p,2).get('dir')
    settings.Reversed=bool(F.getPropertyValue(p,3,'value'));settings.Symmetric=bool(F.getPropertyValue(p,7,'value'))
    if extent==2 and settings.Symmetric:settings.Extent='Distance'
    elif extent in (1,2) and settings.LengthRev.Value>0:settings.Extent='TwoDistances'
    if extent==7:
        descriptor=F.getProperty(p,18)
        if descriptor is None or descriptor.typeName!='151280F0':raise ValueError('Unsupported stored termination plane')
        from importerNative import DatumPlane
        target=F.newObject('Part::FeaturePython',node.name+'_TerminationPlane');DatumPlane(target)
        normal=descriptor.get('dir').cross(descriptor.get('point'))
        target.Placement=App.Placement(descriptor.get('pos')*10,App.Rotation(App.Vector(0,0,1),normal))
        target.Proxy.execute(target);settings.EndFace=(target,['Face1']);F.hide(target)
    settings.Proxy=Settings();settings.Proxy.execute(settings)
    settings.addProperty('App::PropertyString','ImportedState','Inventor import').ImportedState=state(settings)
    settings.setEditorMode('ImportedState',2)
    for name,expression in [('LengthFwd','CalculatedLength'),('LengthRev','CalculatedLength2'),('Dir','Direction'),
                            ('Reversed','Reversed'),('Symmetric','Symmetric'),('TaperAngle','TaperAngle')]:
        tool.setExpression(name,settings.Name+'.'+expression)
    tool.setExpression('Placement.Base',settings.Name+'.StartOffset')
    settings.addProperty('App::PropertyBool','MakeSolid','Extrusion');settings.MakeSolid=operation!='Surface';settings.setEditorMode('MakeSolid',2)
    tool.setExpression('Solid',settings.Name+'.MakeSolid')
    result=F.newObject('Part::FeaturePython',node.name)
    result.addProperty('App::PropertyLinkGlobal','Base','Extrusion').Base=base
    result.addProperty('App::PropertyLinkListGlobal','Tools','Extrusion').Tools=[tool]
    result.addProperty('App::PropertyLinkGlobal','InventorExtrusion','Inventor import').InventorExtrusion=settings
    result.addProperty('App::PropertyBool','InventorModified','Inventor import')
    result.setEditorMode('InventorModified',1)
    result.Proxy=Result()
    from importerNative import NativeView
    if App.GuiUp:NativeView(result.ViewObject)
    App.ActiveDocument.recompute();result.Proxy.execute(result)
    F.hide([profile,tool,settings])
    if base is not None:F.hide(base)
    return result


def setDimension(obj,name,value):
    """Preserve a simple source parameter link when its numeric value changes."""
    if abs(getattr(obj,name).Value-value)<1e-9:return
    expression=dict(obj.ExpressionEngine).get(name,'')
    match=re.fullmatch(r'(\w+)\.(\w+)',expression)
    if match:
        sheet=obj.Document.getObject(match[1])
        if sheet is not None and sheet.TypeId=='Spreadsheet::Sheet':
            cell=sheet.getCellFromAlias(match[2]);contents=sheet.getContents(cell)
            if not contents.startswith('='):
                sheet.set(cell,str(value));return
    obj.setExpression(name,None);setattr(obj,name,value)


class Editor:
    def __init__(self,result):
        from PySide import QtGui
        self.result=result;self.settings=result.InventorExtrusion
        self.form=QtGui.QWidget();self.form.setWindowTitle('Inventor extrusion — '+result.InventorFeatureName)
        layout=QtGui.QFormLayout(self.form)
        self.operation=QtGui.QComboBox();self.operation.addItems(['New body','Pad / Join (add material)','Pocket / Cut (remove material)','Intersect','Surface'])
        self.operation.setCurrentIndex(OPERATIONS.index(str(self.settings.Operation)));layout.addRow('Operation',self.operation)
        self.extent=QtGui.QComboBox();self.extent.addItems(['Distance','Two distances','Through all','To face (planar)','To next (planar)','From / to (planar)'])
        self.extent.setCurrentIndex(EXTENTS.index(str(self.settings.Extent)));layout.addRow('Extent',self.extent)
        self.fields={};self.initialValues={}
        for prop,label,suffix in [('LengthFwd','Distance',' mm'),('LengthRev','Second distance',' mm'),('TaperAngle','Taper angle','°')]:
            field=QtGui.QDoubleSpinBox();field.setDecimals(7);field.setRange(-89.9 if prop=='TaperAngle' else 0,89.9 if prop=='TaperAngle' else 1e9)
            field.setValue(getattr(self.settings,prop).Value);field.setSuffix(suffix)
            expr=dict(self.settings.ExpressionEngine).get(prop)
            if expr:field.setToolTip('Source formula: '+expr+'\nA changed numeric value updates a linked constant or overrides a formula.')
            self.fields[prop]=field;layout.addRow(label,field)
            self.initialValues[prop]=field.value()
        self.reverse=QtGui.QCheckBox();self.reverse.setChecked(self.settings.Reversed);layout.addRow('Reversed',self.reverse)
        self.symmetric=QtGui.QCheckBox();self.symmetric.setChecked(self.settings.Symmetric);layout.addRow('Symmetric',self.symmetric)
        self.direction=QtGui.QLineEdit(', '.join('%.12g'%v for v in self.settings.Direction));layout.addRow('Direction (X, Y, Z)',self.direction)
        self.faces=[]
        forbidden={o.Name for o in result.InListRecursive}|{result.Name,self.settings.Name}|{o.Name for o in result.Tools}
        owner=result.getParentGeoFeatureGroup()
        stored={ref[0].Name for prop in ('StartFace','EndFace') if (ref:=getattr(self.settings,prop)) and ref[0] is not None}
        for obj in result.Document.Objects:
            if obj.Name in forbidden or not hasattr(obj,'Shape'):continue
            if obj.Name not in stored:
                if obj.getParentGeoFeatureGroup()!=owner or not obj.ViewObject.ShowInTree:continue
            for i,face in enumerate(obj.Shape.Faces,1):
                if isinstance(face.Surface,Part.Plane):self.faces.append((obj,'Face%d'%i))
        self.faceFields={}
        for prop,label in [('StartFace','From face'),('EndFace','To face')]:
            combo=QtGui.QComboBox();combo.addItem('Select a face…')
            for obj,name in self.faces:combo.addItem(('Stored boundary' if obj.Name in stored and not obj.ViewObject.ShowInTree else obj.Label)+' · '+name)
            current=getattr(self.settings,prop)
            if current and current[0] is not None:
                pair=(current[0],current[1][0] if current[1] else 'Face1')
                if pair in self.faces:combo.setCurrentIndex(self.faces.index(pair)+1)
            self.faceFields[prop]=combo;layout.addRow(label,combo)
        self.error=QtGui.QLabel();self.error.setWordWrap(True);layout.addRow(self.error)
        self.extent.currentIndexChanged.connect(self.updateFields);self.updateFields()
    def updateFields(self,*args):
        extent=EXTENTS[self.extent.currentIndex()]
        self.fields['LengthFwd'].setEnabled(extent in ('Distance','TwoDistances'))
        self.fields['LengthRev'].setEnabled(extent=='TwoDistances')
        self.faceFields['StartFace'].setEnabled(extent=='FromTo')
        self.faceFields['EndFace'].setEnabled(extent in ('ToFace','FromTo'))
        self.symmetric.setEnabled(extent in ('Distance','ThroughAll'))
        if not self.symmetric.isEnabled():self.symmetric.setChecked(False)
    def getStandardButtons(self):
        from PySide.QtGui import QDialogButtonBox
        return QDialogButtonBox.Ok|QDialogButtonBox.Cancel
    def accept(self):
        import FreeCADGui as Gui
        doc=self.result.Document;doc.openTransaction('Edit Inventor extrusion')
        try:
            settings=self.settings
            settings.Operation=OPERATIONS[self.operation.currentIndex()];settings.Extent=EXTENTS[self.extent.currentIndex()]
            for name,field in self.fields.items():
                if field.isEnabled() and field.value()!=self.initialValues[name]:setDimension(settings,name,field.value())
            settings.Reversed=self.reverse.isChecked();settings.Symmetric=self.symmetric.isChecked()
            xyz=[float(v.strip()) for v in self.direction.text().split(',')]
            if len(xyz)!=3:raise ValueError('Enter three direction coordinates')
            settings.Direction=App.Vector(xyz)
            for name,combo in self.faceFields.items():
                if combo.isEnabled():
                    if combo.currentIndex()==0:raise ValueError('Select '+('a start' if name=='StartFace' else 'an end')+' face')
                    obj,face=self.faces[combo.currentIndex()-1];setattr(settings,name,(obj,[face]))
            doc.recompute(None,True,True)
            affected={o.Name for o in self.result.InListRecursive}|{self.result.Name,settings.Name}|{o.Name for o in self.result.Tools}
            invalid=[o.Label for o in doc.Objects if o.Name in affected and 'Invalid' in o.State]
            if invalid:raise ValueError('The edit cannot rebuild: '+', '.join(invalid))
            for solid in self.result.Shape.Solids:solid.check(True)
            doc.commitTransaction();Gui.Control.closeDialog();return True
        except Exception as error:
            doc.abortTransaction();doc.recompute(None,True,True);self.error.setText(str(error));return False
    def reject(self):
        import FreeCADGui as Gui
        Gui.Control.closeDialog();return True


activeEditor=None
def edit(result):
    import FreeCADGui as Gui
    global activeEditor
    activeEditor=Editor(result);Gui.Control.showDialog(activeEditor);return True
