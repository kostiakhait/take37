# Minivan (two swing doors, a sliding right door, a liftgate; front drive), 1984-87 look

Nodes and files: `minivan86.glb` (full detail), `minivan86_lod1.glb`, `minivan86_damaged.glb` (the same node set posed wrecked: dents, loose bumpers, bent lids, torn-off look, dirt). Root `Minivan86`.

## Shape and sizes

- Outline drawing: Plymouth Voyager 1984 (Outlines, getoutlines.com, https://getoutlines.com/blueprints/19310/1984-plymouth-voyager-tag-blueprints, CC BY 4.0). 320 x 204 px. Copy in `reference/plymouth-voyager-1984-outlines.png`.
- Sizes: Wikipedia, Dodge Caravan (first generation, short wheelbase): wheelbase 112.1 in, length 175.9 in, width 69.5 in, height 64.4 in. Tyre P185/75R14. The drawing gives the shape, every listed size is honoured (`../_common/geomkit.py`).
- Plates are fictional (no state, no marks); no badges, no names anywhere on the car.

## Заимствовано из Феррета (library materials and textures, D:\REPOerret\liberret-assets)

- rug (материал и текстуры basecolor/normal/orm): carpet
- gray-fabric1 (материал и текстуры basecolor/normal/orm): headliner
- cloth-grey (материал и текстуры basecolor/normal/orm): seat cloth
- metal-black (материал и текстуры basecolor/normal/orm): chassis, underbody parts
- metal-steel (материал и текстуры basecolor/normal/orm): exhaust, rear axle
- Method and parts code: carkit.py (tyres with tread and sidewall lettering, brake discs, calipers, lamps, seats, glass, wipers, bevels) from the library's car examples, copied to `../_common/carkit.py`; the lofted-body, boolean-cut and door-split construction follows the library police sedan's build script.

## Made for the game

- Everything else: the body, doors, lids, bumpers, glass, trim, lamps, interior, engine bay, underbody, wheels (`../_common/cargen.py`, `minivan_geom.py`, `build_minivan.py`), the paint colour set (material variants KHR_materials_variants: beige, burgundy, dark_blue, silver, white, brown), the dirt vertex colours, the damaged pose.
- Build: `blender -b -t 8 -P build_minivan.py -- --out minivan86.glb --lod1 minivan86_lod1.glb --damaged minivan86_damaged.glb`.
