# -*- coding: utf-8 -*-
'''
importerF3Z.py

Opens an Autodesk Fusion archive (*.f3z): an assembly saved together with the designs it
references. Every referenced design is an ordinary .f3d; each is imported through importerF3D
(ACIS -> STEP -> sewn solids) and labelled with its Fusion component name.

Limits: the assembly's own placements, joints and repeated instances live in the root design's
undocumented BulkStream and are not read. Parts appear where they sit in their own design file,
which lines up only when they were modelled in place.
'''

import io
import json
import os
import tempfile
import zipfile

import FreeCAD

import importerF3D



def _extract(filename):
	'''Unpack the archive (any Zstandard entries decoded) and return (dir, parts, root).'''
	plain = importerF3D._zip_without_zstd(filename)
	base = os.path.splitext(os.path.basename(filename))[0]
	out = os.path.join(tempfile.gettempdir(), u"InventorLoader", base + u"_f3z")
	os.makedirs(out, exist_ok=True)
	with zipfile.ZipFile(plain) as z:
		z.extractall(out)
	names, root = {}, None
	try:
		with io.open(os.path.join(out, 'Manifest.json'), encoding='utf-8') as fh:   # module-level open() below shadows the builtin
			root = json.load(fh).get('root')
	except Exception:
		pass
	try:
		with io.open(os.path.join(out, 'DesignDescription.json'), encoding='utf-8') as fh:
			desc = json.load(fh)
		for graph in desc['designDescription']['designGraphs']:
			for obj in graph.get('designObjects', []):
				names[obj.get('relativePath')] = obj.get('friendlyName') or obj.get('displayName')
	except Exception:
		pass
	parts = sorted(f for f in os.listdir(out) if f.lower().endswith('.f3d'))
	return out, [(names.get(f) or os.path.splitext(f)[0], os.path.join(out, f), f == root) for f in parts], root


def insert(filename, docname):
	doc = FreeCAD.getDocument(docname)
	folder, parts, root = _extract(filename)
	group = doc.addObject('App::DocumentObjectGroup', 'FusionParts')
	group.Label = os.path.splitext(os.path.basename(filename))[0]
	failed = []
	for label, path, is_root in parts:
		before = set(o.Name for o in doc.Objects)
		try:
			if (not importerF3D.read(path)):
				failed.append(label)
				continue
			importerF3D.convertModel(docname)
		except Exception as e:
			FreeCAD.Console.PrintWarning(u"f3z: %s could not be imported: %s\n" % (label, e))
			failed.append(label)
			continue
		new = [o for o in doc.Objects if o.Name not in before and o.TypeId == 'Part::Feature']
		solids = [o for o in new if (o.Shape.Solids and o.Shape.Volume > 1e-9)]
		if (is_root and not solids):
			for o in new:	# the assembly's own sheets/sketch bodies: not parts
				doc.removeObject(o.Name)
			continue
		for i, o in enumerate(new):
			o.Label = label if (len(new) == 1) else (u"%s_%d" % (label, i + 1) if not o.Name.endswith('open_faces') else label + u"_open_faces")
			group.addObject(o)
	doc.recompute()
	if (failed):
		FreeCAD.Console.PrintWarning(u"f3z: not imported: %s\n" % ', '.join(failed))
	FreeCAD.Console.PrintMessage(u"f3z: %d designs read from %s; assembly placements/joints are not applied\n" % (len(parts), os.path.basename(filename)))
	if (FreeCAD.GuiUp):
		import FreeCADGui
		FreeCADGui.SendMsgToActiveView("ViewFit")


def open(filename):
	name = os.path.splitext(os.path.basename(filename))[0]
	doc = FreeCAD.newDocument(name.replace(' ', '_'))
	doc.Label = name
	insert(filename, doc.Name)
