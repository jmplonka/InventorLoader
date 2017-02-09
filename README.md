# InventorLoader
Loads / Imports Autodesk (R) Inventor (R) files into FreeCAD. Until now only the structure of IPD, IAM and IDW files can be dumpt, but neither parts (IPT) nor assemblies (IAM), nor drawings (IDW) can be displayed.
## Status:
> Alpha!

Autodesk Inventor files have a OLE2 files.
That allows it to embed Excel workboos e.g.

- The addon is able to read (not analyse) Inventor files from 2003 till 2017 (RSe Meta Stream Version Version 3 till 8)
- Read the iProperties (only a few can be set in FreeCAD)
- Display embedded workbooks as a new spreadsheet

## Next steps:
- add sketches for points, lines, circles, elipses etc. (help needed to read the coordinates).
- retrieve object names from the file.
