# InventorLoader
Loads / Imports Autodesk (R) Inventor (R) files into FreeCAD. Until now only the structure of IPD, IAM and IDW files can be dumpt, but neither parts (IPT) nor assemblies (IAM), nor drawings (IDW) can be displayed.

## Prerequisits
- The AddON requires additional python packages in the FreeCAD python installation:
  - https://pypi.python.org/pypi/xlrd: for reading embedded Excel workbooks
  - http://pypi.python.org/pypi/xlutils: for preparing imported Excel workbooks to be stored
  - https://pypi.python.org/pypi/xlwt: for writing embedded Excel workbooks

## Status:
> Alpha!

Autodesk Inventor files have a OLE2 files.
That allows it to embed Excel workboos e.g.

- The addon is able to read (not analyse) Inventor files from 2003 till 2017 (RSe Meta Stream Version Version 3 till 8)
- Read the iProperties (only a few can be set in FreeCAD)
- Display embedded workbooks as a new spreadsheet
- Read BrowserView structure (started V2015 & IPT files only)

| File | Description | IPT | IAM | IDW |
| --- | --- | --- | --- | --- |
| [5]xyz | iProperties | done | done | done |
| RSeDb | Database | done | done | done |
| RSeSegInfo | Content Structure | structure | structure | structure |
| M... | Segment Structre info | started | started | started | started |
| B... | Segment Data | sarted |  |  |
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

- 0.2: Reading document content now from DC-Segment instead of Graphics-/Browser-Segment
	- added reading of object names
	- 2D sketch constraints and dimensions

## Next steps:
- Features like Pads, Pockets, Revolutions, etc.
- Features like Fillet, Champher, Draft, etc.
- Features like boolean operations, mirrors, etc.
=======
## Next steps:
- Retrieve browserview structure with names from Browser's Segment Data.- add Sketch's Constraints
- retrieve graphic's object names from Broweser-Segment
- Extrusions ...
>>>>>>> f26ca18... Version 0.1: import 2D-Sketch + Point, Line, (Arc-)Circle, (Arc-)Ellipse
