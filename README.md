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
| M... | Segment MetaInfo | started | started | started | started |
| B... | Segment Data | sarted |  |  |
| Workbook | Spreadsheet | done | done | done |

## Next steps:
- Retrieve browserview structure with names from Browser's Segment Data.
- add sketches for points, lines, circles, elipses etc.
- Extrusions ...
