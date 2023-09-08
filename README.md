# InventorLoader
Loads/Imports: Autodesk (R) Inventor (R) files into FreeCAD (v0.18 or greater). 
Until now only Parts (IPT) but not assemblies (IAM) or drawings (IDW) or presentations (IPN) can be displayed.

As Inventor files contains a complete ACIS model representation, SAT and SAB files can also be 
imported into FreeCAD.

As Fusion360 files contains a complete ACIS model representation these files can also be opened in FreeCAD.
## Status:
**Released 1.3**

## Screenshots
[Demo-Status](https://github.com/jmplonka/InventorLoader/tree/master/Demo-Status/) subdirectory shows examples of this Addon.

## Prerequisites
[FreeCAD](https://freecadweb.org/downloads.php) v0.17 or greater required!

This Addon also requires additional python packages:
* https://pypi.python.org/pypi/xlrd - for reading embedded Excel workbooks
* https://pypi.python.org/pypi/xlwt - for writing embedded Excel workbooks
* http://www.decalage.info/python/olefileio - olefile for reading Microsoft OLE(2)
    files.

## Installation
### Automatic Install (recommended)
Installable via the FreeCAD [Addon Manager](https://www.freecadweb.org/wiki/Std_AddonMgr).  
Requires a restart after downloading this addon.  

### Manual Install
1. Create a directory in either two locations where FreeCAD searches for
addons:  
  a. FreeCAD's `bin` folder, or  
  b. in the user's application data (`%APPDATA%` on Windows) or home (`~/`) folder (on Linux/MacOS).  
2. Create a `Mod` subdirectory if one doesn't exist and/or move in to it. 
3. Download the InventorLoader repository as either:  
  a. [ZIP archive](https://github.com/jmplonka/InventorLoader/archive/master.zip), or via  
  b.`git clone https://github.com/jmplonka/InventorLoader.git`  
and expand its content directly into the
FreeCAD subdirectory named `Mod`.  
3. Start (or restart) FreeCAD  

The next time FreeCAD starts new import formats for ACIS' SAT (\*.sat) files and Autodesk 
Inventor's IPT (\*.ipt) files as will be available and supported import formats.

**Note:** Please pre-install the [Prerequisite](https://github.com/jmplonka/InventorLoader#prerequisites) python libraries 
so that the new packages become available.

### Solving installation problems
Sometimes it can happen that the packages can't be installed.
1. Navigate to the InventorLoader plugin (ILP) folder with your file-browser (e.g.
   Windows-Explorer)
2. Extract the libs.zip into the ILP's folder (a new subfolder `libs` should be created).
3. Open a command shell (e.g. `cmd` on windows or `sh` on linux)
   1. Adapt the `PATH` variable to point to FreeCAD's python: `set PATH="<PATH-TO-FREECAD>\bin";%PATH%`
      (on linux you have to export the `PATH` variable). **Note**: Linux and MAC users
      should use '/' instead of '\'!
   2. Change the working folder to ILP's `libs` folder (e.g. `cd <PATH-TO-FREECAD>\Mod\InventorLoader-master\libs`)
   3. Run the installation script: `python ./installLibs.py`
      This should install the required packages.
4. Restart FreeCAD

#### Constraints in Native-IPT Import:
Please disable Dimension constraints in user.cfg:
```xml
<FCBool Name="Sketch.Constraint.Dimension.Angle2Line" Value="0"/>
<FCBool Name="Sketch.Constraint.Dimension.Angle3Point" Value="0"/>
```

## Limitations
Export will not be supported - neither IPT nor SAT/SAB or DXF.
Only files from INVENTOR V2010 or newer are supported.

### Feature Based Import

### ACIS (`sat`) Native Import
- Blending surfaces are not yet supported.
- Helix surfaces are not yet supported for lines.
- Interpolated curves and surfaces defined by laws are omitted if they don't have spline data.

### STEP Conversion Import
STEP converts the ACIS data from SAT or IPT files. Therefore any limitation is inherited.

Autodesk Inventor files have OLE2 files.  
This allows embedding Excel workbooks e.g.:  
* The addon is able to read Inventor files from 2010 or newer.
* Read the iProperties (Note: only a few can be applied in FreeCAD).
* Display embedded workbooks as a new spreadsheet when importing as features.
* Three strategies are provided:  
  * **feature base**: the addon tries to rebuild all the features.
  * **SAT based**: like STEP file, model will be imported based on FACE, EDGES and VERTICES.
  * **STEP based**: The ACIS model will be converted into STEP and imported afterwards.

### DXF import
DXF files contains sometimes 3D-Solids. These are represented as SAT/SAB content.
The solids can be imported either using native of STEP conversion.

## History
**1.3**    (2021-03-09): Added support for Fusion360 files.  
**1.2**    (2021-02-28): Added support for Inventor 2021 files.  
**1.1**    (2020-05-04): Added importing of 3D-Solids from DXF files.  
**1.0.1**  (2020-04-10): Fixed finding of SAB import.  
**1.0.0**  (2019-08-26): Reorganized section readers (1.0).  
**0.18.0** (2019-08-07): Added coloring of single faces and changed to default Inventor campera position (RC2).  
**0.17.0** (2019-07-04): Missing features added as ACIS models (RC1).  
**0.16.0** (2019-03-19): Added creation of Shells  
**0.15.0** (2019-03-07): Added part variant handling (ak iPart)  
**0.14.0** (2019-03-05): InventorLoader is now a workbench.  
**0.13.0** (2019-03-01): Added support for Fillets and Chamfers. Segmented variable radius
            chamfers are not supported by FreeCAD. In such cases please import as STEP instead.  

**0.12.0** (2019-01-08): Added support for Surface Features "BoundaryPatch" and "Knit". Both
            features will be displayed with their own icon in the model browser.  

**0.11.0** (2018-11-06): Added support for Meshes  
**0.10.0** Added table for iParts.  
**0.9.5** Added chamfer feature for nativ strategy.  
**0.9.4** InventorLoader is now compatible with python 2 and 3  
**0.9.3** Added support of offset surfaces and spring surfaces (circle that is seepted along a helix)  

**0.9.2** Added named colors to STEP.  
**0.9.1** Added colors to STEP.  
**0.9.0** Added conversion to STEP. IPT files can now either be imported:  
  * Based on features (nearest to FreeCAD so changing the model is easy)
  * Based on SAT (model is imported based on stored Surfaces and Edges)
  * Based on STEP (SAT model is converted to STEP and imported into FreeCAD using built-in reader)  

**0.8.1** Fixed support of cone surfaces.  
**0.8.0** Added handling of Inventor 2019 file format.  
**0.7.2** Added interpolated surfaces for SAT files.  
**0.7.1** Added interpolated curves for SAT files.  
**0.7.0** Added ACIS file format reading for IPT and SAT files.  
  * IPT: during import user selectable strategy with thumbnail.  

**0.6.0** continued working on Features  
  * Added Coil as Part::Helix and Part::Spiral with Sweep
  * Automated installation of required site-packages

**0.5.5** Maintenance version  
  * Fixed wrong creation of boundary wires/faces from sketches
  * Fixed wrong handling of constraints in sketches
  * Code reviewed

**0.5.4** continued working on Features  
  * Added Sweep as Part::Sweep
  * Added Thicken as Part::Offset
  * Fixed encoding problems regarding filename and Sketch/Feature names
  
**0.5.3** Continued working on Features  
  * Added Client as a new group of objects.

**0.5.2** Continued working on Features  
  * Added Hole as combination of creating Part::Cylinder, Part::Cone(s) and Part::MultiFuse and Part::Cut  

**0.5.1** Continued working on Features  
  * Added Revolve as Part::Revolution
  * Added Extrude as Part::Extrusion
  * Added Loft  as Part::Loft
  * Added boolean operations as Part::Cut, Part::MultiFuse, Part::MultiCommon
  * Added Polar-Pattern, Rectangular-Pattern with Draft.makeArray()
  * Added Mirror-Pattern as 'Part::Mirroring'

**0.5.0** Preparation for supporting Features (except iFeature)
  * Most sections found in pro samples (2010..2018) are now decoded (structured)

**0.4.2** Only Code Review  
  * Most sections found in LT samples are now decoded (structured)

**0.4.1** Completed parameter management.
  * Parameter table now contains the name, value, formula, tolerance and comment
  of each parameter  
    * Added parameter unit handling
    * Added parameter formulas handling
    * Added parameter operations handling (e.g. '+', '-', '*' and '/')  

    Even if operations or functions are not supported by FreeCAD (e.g. modulo
    operator, signum or random function), parameters will be replaced by their
    nominal value and unit.

**0.4** Added spreadsheet for parameters.  
  * Added handling of expressions for parameters
  * Fixed missing placement for 2D-sketches

**0.3** Started working on sketches.
  * Added placement to sketches. ~Sometimes Placements have to "Orientation"
  references, so that a correct placement is not possible~
  * Added pad feature. Maybe this will be changed to Part instead of PartDesign.

**0.2** Reading document content now from DC-Segment instead of Graphics-/Browser-
Segment
  * Added reading of object names
  * 2D sketch constraints and dimensions

**0.1** First "working" prototype.
  * Reading Inventor file Structure
  * Reading compressed data for Model-Segments (e.g. Graphics- and Browser-View)
  * Displaying Sketches
    * Points-2D
    * Line-2D
    * (Arc-)Circle-2D
    * (Arc-)Ellipse-2D
  * Embedded files dumped to export folder

## Roadmap (in no particular order)
* Features like Grave, etc.
* Features like Draft, etc.
* Preferences page
