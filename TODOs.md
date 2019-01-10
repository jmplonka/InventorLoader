# IPT file
## Incomplete Features
	* Sketch2D, Sketch3D
		* SketchBlock
		* SketchDrivenPattern

## Missing Features
	* SheetMetal
		* add (Cosmetic-)Bend, (Re-)Fold, Hem, Face (Delete, Draft, Move, Replace), Corner (Chamfer, Round), (Contour-, Lofted-)Flange
		* add CounterRoll, Rip

	* Solids modeling
		* add Shell, Split, (Presentation-)Mesh

	* Surfaces
		* add Trim, Sculpt, Extend
		* add RuledSurface
		* add Decal, Emboss

	* Edge modeling
		* add Chamfer (Variable, Constant),
		* add (Rule-)Fillet

	* combined
		* add Boss, Rib, Grill, Lip, Rest, SnapFit

	* Access to feature properties

## Unsupported
	* NonParametricBase, CoreCavity, (Alias-)Freeform, Reference, DirectEdit, PunchTool, iFeature

# SAT files
## Incomplete Features
	* spline-surface - missing creation of helical lines, vertex-blends and summary surfaces
	* references - sometime references can't be resolved :(

## missing Features
	* compu-, int-int-curves

## unsupported
	* attributes (except colors)
	* annotations
	* splines other than nurbs or nubs (e.g. "summary" or "none")
