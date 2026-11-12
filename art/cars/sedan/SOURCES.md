# Mid-size sedan (four doors, notchback, front drive), 1982-87 look

Nodes and files: `sedan87.glb` (full detail), `sedan87_lod1.glb`, `sedan87_damaged.glb` (the same node set posed wrecked: dents, loose bumpers, bent lids, torn-off look, dirt). Root `Sedan87`.

## Shape and sizes

- Outline drawing: Oldsmobile Cutlass Ciera 1989 (Outlines, getoutlines.com, "1989 Oldsmobile Cutlass Ciera Sedan", https://getoutlines.com/blueprints/10965/1989-oldsmobile-cutlass-ciera-sedan-blueprints, CC BY 4.0). 318 x 201 px: a low-resolution drawing, the shape between the listed sizes is therefore smoothed. Copy in `reference/oldsmobile-cutlass-ciera-1989-outlines.png`.
- Sizes: Wikipedia, Oldsmobile Cutlass Ciera (https://en.wikipedia.org/wiki/Oldsmobile_Cutlass_Ciera): wheelbase 104.9 in, length 190.3 in, width 69.5 in, height 54.1 in. Tyre P185/75R14 (radius 0.317 m). The drawing gives the shape, every listed size is honoured (`../_common/geomkit.py`).
- Plates are fictional (no state, no marks); no badges, no names anywhere on the car.

## Заимствовано из Феррета (library materials and textures, D:\REPOerret\liberret-assets)

- rug (материал и текстуры basecolor/normal/orm): carpet
- gray-fabric1 (материал и текстуры basecolor/normal/orm): headliner
- cloth-grey (материал и текстуры basecolor/normal/orm): seat cloth
- metal-black (материал и текстуры basecolor/normal/orm): chassis, underbody parts
- metal-steel (материал и текстуры basecolor/normal/orm): exhaust, rear axle
- Method and parts code: carkit.py (tyres with tread and sidewall lettering, brake discs, calipers, lamps, seats, glass, wipers, bevels) from the library's car examples, copied to `../_common/carkit.py`; the lofted-body, boolean-cut and door-split construction follows the library police sedan's build script.

## Made for the game

- Everything else: the body, doors, lids, bumpers, glass, trim, lamps, interior, engine bay, underbody, wheels (`../_common/cargen.py`, `sedan_geom.py`, `build_sedan.py`), the paint colour set (material variants KHR_materials_variants: silver, midnight_blue, maroon, desert_tan, white, forest_green), the dirt vertex colours, the damaged pose.
- Build: `blender -b -t 8 -P build_sedan.py -- --out sedan87.glb --lod1 sedan87_lod1.glb --damaged sedan87_damaged.glb`.
