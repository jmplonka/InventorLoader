# InventorLoader
Loads / Imports Autodesk (R) Inventor (R) files into FreeCAD. Until now only
the structure of IPD, IAM and IDW files can be dumpt, but neither parts (IPT)
nor assemblies (IAM), nor drawings (IDW) can be displayed.

## Prerequisits
- The AddON requires additional python packages in the FreeCAD python installation:
  - https://pypi.python.org/pypi/xlrd: for reading embedded Excel workbooks
  - http://pypi.python.org/pypi/xlutils: for preparing imported Excel workbooks to
    be stored
  - https://pypi.python.org/pypi/xlwt: for writing embedded Excel workbooks
  - http://www.decalage.info/python/olefileio olefile for reading Microsoft OLE(2)
  	files.

## Status:
> Alpha!

Autodesk Inventor files have a OLE2 files.
That allows it to embed Excel workboos e.g.

- The addon is able to read (not analyse) Inventor files from 2003 till 2017 (RSe
  Meta Stream Version Version 3 till 8)
- Read the iProperties (only a few can be set in FreeCAD)
- Display embedded workbooks as a new spreadsheet
- Read BrowserView structure (started V2015 & IPT files only)

| File | Description | IPT | IAM | IDW |
| --- | --- | --- | --- | --- |
| [5]xyz | iProperties | done | done | done |
| RSeDb | Database | done | done | done |
| RSeSegInfo | Content Structure | structure | structure | structure |
| M... | Segment Structre info | started | started | started | started |
| B... | Segment Data | done | started | started |
| Workbook | Spreadsheet | done | done | done |

## History:
- 0.1: first "working" prototype.
	- reading Inventor file Structure
	- reading compressed data for Model-Segments (e.g. Graphics- and Browser-View)
	- displaying Sketches
		- Points-2D
		- Line-2D
		- (Arc-)Circle-2D
		- (Arc-)Ellipse-2D
	- embedded files dumped to export folder

- 0.2: Reading document content now from DC-Segment instead of Graphics-/Browser-
  Segment
	- added reading of object names
	- 2D sketch constraints and dimensions

- 0.3: Started working on sketches.
	- Added placement to sketches. <s>Sometimes Placements have to "Orientation"
	  references, so that a correct placement is not possible</s>
	- Added pad feature. Maybe this will be chagned to Part instead of PartDesign.

- 0.4: Added spreadsheet for parameters.
	- Added handling of expressions for parameters
	- fixed missing placement for 2D-sketches

- 0.4.1: Completed parameter management.
	Parameter table now contains the name, value, formula, tolerance and comment
	of each parameter
	- Added parameter unit handling
	- Added parameter formulas handling
	- Added parameter operations handling (e.g. '+', '-', '*' and '/')
	Even if operations or functions are not supported by FreeCAD (e.g. modulo
	operator, signum or random function), parameters will be replaced by their
	nominal value and unit.

- 0.4.2: Only Code Review
	Most sections found in LT samples are now decoded (structured)

- 0.5: Preparation for supporting Featrues (except iFeature)
	Most sections found in pro samples (2010..2018) are now decoded (structured)

- 0.5.1: continued working on Features
	* added Revolve as Part::Revolution
	* added Extrude as Part::Extrusion
	* added Loft  as Part::Loft
	* added boolean opertations as Part::Cut, Part::MultiFuse, Part::MultiCommon
	* added Polar-Pattern, Rectangular-Pattern with Draft.makeArray()
	* added Mirror-Pattern as 'Part::Mirroring'

- 0.5.2: continued working on Features
	* added Hole as combination of creating Part::Cylinder, Part::Cone(s) and Part::MultiFuse and Part::Cut

- 0.5.3: continued working on Features
	* added Client as a new group of objects.

- 0.5.4: continued working on Features
	* added Sweep  as Part::Sweep
	* added Thicken as Part::Offset
	* Fixed encoding problems regarding filename and Sketch/Feature names

- 0.5.5: code review and bug fixes

- 0.8.1: Added Features
	* FX-Hole

- 0.8.2: Added Features
	* FX-Client

## Next steps in unsorted order:
- Features like Grave, etc.
- Features like Fillet, Champher, Draft, etc.
- Prefferences page