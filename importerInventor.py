"""Checked IPT/IAM import with isolated parsing and validated parametric reconstruction."""
import contextlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import FreeCAD as App
import FreeCADGui as Gui
import Part
from olefile import OleFileIO
import Import_IPT
import importerClasses as C
import importerUtils as U
from importerSolid import savedShapes, equivalent, compareShapes


@contextlib.contextmanager
def parsed(source, strategy=None, geometryOnly=False):
    """All parser dumps live in a private temporary directory, never by input."""
    previous = (U.__strategy__, U.getDumpFolder(), U.getInventorFile())
    with tempfile.TemporaryDirectory(prefix='InventorLoader_') as folder:
        path = Path(folder) / Path(source).name
        shutil.copyfile(str(source), str(path))
        ole = None
        try:
            ole = Import_IPT.checkVersion(str(path))
            if ole is None:
                raise ValueError('Unsupported Inventor file version')
            if not Import_IPT.read(ole, strategy=strategy, geometryOnly=geometryOnly, featureOnly=True):
                yield None
            else:
                yield C.getModel()
        finally:
            if ole is not None:
                ole.close()
            C.releaseModel()
            import Acis
            Acis.releaseMemory()
            U.setThumbnail(None)
            if strategy is not None:
                U.__strategy__ = previous[0]
            U._dump_folder, U._inventor_file = previous[1:]


def annotate(obj, source, mode):
    obj.addProperty('App::PropertyFile', 'InventorSource', 'Inventor import').InventorSource = str(source)
    obj.addProperty('App::PropertyString', 'InventorImportMethod', 'Inventor import').InventorImportMethod = mode
    obj.addProperty('App::PropertyBool', 'InventorGeometryValid', 'Inventor import').InventorGeometryValid = True


def makeBodies(doc, parent, shapes, source, mode):
    bodies = []
    for i, shape in enumerate(shapes,1):
        obj = doc.addObject('Part::Feature', 'InventorBody')
        obj.Label = Path(source).stem + (f' ({i})' if len(shapes)>1 else '')
        # Keep native feature builders and viewport tessellations from sharing
        # mutable OpenCascade geometry with the reference used for validation.
        obj.Shape = shape.copy(True, False)
        annotate(obj,source,mode)
        if parent:
            parent.addObject(obj)
        bodies.append(obj)
    return bodies


def nativeBodies(doc, parent, model, reference, source):
    from importerNative import Importer
    from importerStructure import organize
    before={o.Name for o in doc.Objects}
    importer=Importer(source=source)
    candidates=importer.build(parent)
    doc.recompute(None,True,True)
    if not candidates:
        raise ValueError('Native reconstruction produced no final solid')
    # Presenting the source hierarchy touches dependencies. Validate the final
    # recomputed document, including those changes, before recording a match.
    organize(model,importer,candidates,before,parent)
    doc.recompute(None,True,True)
    shape=Part.makeCompound([o.Shape for o in candidates])
    for solid in shape.Solids:
        solid.check(True)
    comparison=compareShapes(shape,Part.makeCompound(reference))
    if not comparison['matches']:
        raise ValueError('Native reconstruction differs from the saved Inventor BRep (STEP import): '+str(source)+'; '+json.dumps(comparison))
    for obj in candidates:
        annotate(obj,source,'Native features; checked against saved BRep')
        obj.addProperty('App::PropertyString','InventorStepComparison','Inventor import').InventorStepComparison=json.dumps(comparison,sort_keys=True)
    return candidates


def part(source, doc, parent=None, strategy=None):
    with parsed(source,strategy=strategy) as model:
        if model is None:
            return []
        reference=savedShapes(model)
        if U.getStrategy()==U.STRATEGY_NATIVE:
            return nativeBodies(doc,parent,model,reference,source)
        return makeBodies(doc,parent,reference,source,'Saved Inventor BRep; checked solid')


def assembly(source, doc, parent=None, ancestors=(), strategy=None):
    import importerAssembly as A
    import importerStructure as S
    key=os.path.normcase(os.path.realpath(str(source)))
    if key in ancestors:
        raise ValueError('Cyclic Inventor assembly reference: ' + str(source))
    with OleFileIO(str(source)) as ole:
        refs=A.references(ole.openstream('UFRxDoc').read())
    with parsed(source,strategy=U.STRATEGY_STEP,geometryOnly=True) as model:
        entries=A.occurrences(model,refs)
        specification=S.assemblySpecification(model)
    resolver=A.Resolver(Path(source).parent)
    # Resolve all files before creating any objects, so missing parts are explicit.
    for entry in entries:
        entry['path'],entry['identity']=resolver.resolve(entry['reference'])
    group=S.component(doc,'InventorAssembly',Path(source).stem,nested=parent is not None)
    annotate(group,source,'IAM saved occurrences and placements (constraints not reconstructed)')
    if parent:
        parent.addObject(group)
    sourceFolders=S.assemblyFolders(doc,group,specification)
    links=[]
    cache={}
    for entry in entries:
        path=entry['path']
        cachekey=os.path.normcase(str(path.resolve()))
        if cachekey not in cache:
            if path.suffix.lower()=='.iam':
                definition=assembly(path,doc,group,ancestors+(key,),strategy=strategy)
            else:
                definition=S.component(doc,'InventorComponent',path.stem)
                group.addObject(definition)
                bodies=part(path,doc,definition,strategy=strategy)
                if not definition.InventorResults:
                    definition.InventorResults=bodies;definition.Proxy.execute(definition)
            definition.Visibility=False
            cache[cachekey]=definition
        link=doc.addObject('App::Link','InventorOccurrence')
        link.setLink(cache[cachekey])
        link.LinkClaimChild=False
        group.addObject(link)
        link.Label=entry['label']
        link.Placement=entry['placement']
        annotate(link,path,'IAM occurrence')
        link.addProperty('App::PropertyInteger','InventorOccurrenceId','Inventor import').InventorOccurrenceId=entry['occurrence']
        link.addProperty('App::PropertyString','InventorSavedReference','Inventor import').InventorSavedReference=entry['reference']['path']
        changed=entry['identity']['revision'] != entry['reference']['revision']
        link.addProperty('App::PropertyBool','InventorRevisionChanged','Inventor import').InventorRevisionChanged=changed
        if changed:
            U.logWarning('IAM: %s uses a newer/different component revision: %s\n',entry['label'],str(path))
        link.Visibility=True
        links.append(link)
    group.InventorResults=links
    group.InventorChildren=sourceFolders+links if parent else []
    group.Proxy.execute(group)
    if parent is None:
        # The FreeCAD document already represents the root assembly. Do not
        # make its occurrences children of a second, hidden assembly wrapper.
        group.Group=[]
        for link in links:link.Visibility=True
    group.addProperty('App::PropertyString','InventorStructure','Inventor import').InventorStructure=json.dumps(dict(source_order=[o.Label for o in sourceFolders]+[o.Label for o in links],extra_import_groups=False))
    doc.recompute()
    return group


def importFile(source, doc=None, root=None, strategy=None):
    source=Path(source).resolve()
    created=doc is None
    doc=doc or App.newDocument(source.stem)
    App.setActiveDocument(doc.Name)
    doc.openTransaction('Import Inventor file')
    labels=App.ParamGet('User parameter:BaseApp/Preferences/Document')
    duplicateLabels=labels.GetBool('DuplicateLabels',False)
    # Origin/Sketch1/etc. legitimately recur in different Inventor components.
    # Preserve their stored labels without changing the user's saved preference.
    labels.SetBool('DuplicateLabels',True)
    try:
        if source.suffix.lower()=='.iam':
            if strategy is None:
                with OleFileIO(str(source)) as ole:
                    if not ole.exists('UFRxDoc'):raise ValueError('IAM has no component reference stream')
                strategy=Import_IPT.chooseImportStrategy()
            if strategy==U.STRATEGY_CANCEL:
                result=[]
            else:
                result=assembly(source,doc,root,strategy=strategy)
        else:
            result=part(source,doc,root,strategy)
        if result==[]:
            doc.abortTransaction()
            if created:
                App.closeDocument(doc.Name)
            return None
        doc.recompute()
        doc.commitTransaction()
        if App.GuiUp:
            Gui.activeDocument().activeView().viewAxonometric()
            Gui.activeDocument().activeView().fitAll()
        return doc
    except Exception:
        doc.abortTransaction()
        if created:
            App.closeDocument(doc.Name)
        raise
    finally:
        labels.SetBool('DuplicateLabels',duplicateLabels)
