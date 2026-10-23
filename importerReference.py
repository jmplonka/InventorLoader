"""Recover only complete, unambiguous historical imported-base boundaries."""
from types import SimpleNamespace
import Part
import Acis
from Acis2Step import export
from importerSolid import checkedShape
from importerSAT import resolveNodes

def recover(model,node):
    brep=model.getBRep()
    attributes=brep.getDcSatAttributes().get(node.get('index'))
    if attributes is None:raise ValueError('No saved boundary for imported base '+node.name)
    component=model.getDC().tree.getFirstChild('Document').get('component')
    hasDownstream=sum(o.typeName=='Feature' for o in component.get('objects'))>1
    acis=brep.AcisList[0].SAT
    active={shell.index for body in resolveNodes(acis) for lump in body.getLumps() for shell in lump.getShells()}
    groups={}
    for face in attributes.getFaces():groups.setdefault(face.getParent().index,[]).append(face)
    shells=[]
    for index,faces in groups.items():
        shell=faces[0].getParent()
        if hasDownstream and index in active:continue
        if {f.index for f in faces}=={f.index for f in shell.getFaces()}:shells.append(shell)
    if not shells:
        raise ValueError('Imported base '+node.name+': no complete recoverable historical shell. Native reconstruction is unavailable for this reference feature.')
    lump=SimpleNamespace(index=0,getShells=lambda:shells,getColor=lambda:None)
    body=SimpleNamespace(index=0,getName=lambda:node.name,getTransform=lambda:None,getLumps=lambda:[lump],getColor=lambda:None)
    path=export('native_base_'+str(node.index),acis.header,[body])
    shape=checkedShape(Part.read(path))
    if shape.getTolerance(1)>1e-4:raise ValueError('Imported base exceeds the geometry tolerance budget')
    shape.fixTolerance(1e-4)
    for solid in shape.Solids:solid.check(True)
    return shape
