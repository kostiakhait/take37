# Full-size pickup truck, regular cab, short bed, rear drive, 1987 look

Nodes and files: `pickup87.glb` (full detail), `pickup87_lod1.glb`, `pickup87_damaged.glb` (the same node set posed wrecked: dents, loose bumpers, bent lids, torn-off look, dirt). Root `Pickup87`.

## Shape and sizes

- Outline drawing: Ford F-150 1987 (Outlines, getoutlines.com, https://getoutlines.com/blueprints/18524/1987-ford-f-150-pickup-truck-blueprints, CC BY 4.0). 327 x 428 px, the upper side view. Copy in `reference/ford-f-150-1987-outlines.png`.
- Sizes: Wikipedia, Ford F-Series (eighth generation): wheelbase 117 in, length 194.1 in, width 79 in; height 1.78 m (the page lists none for this body; taken from the drawing proportions). Tyre P235/75R15. The drawing gives the shape, every listed size is honoured (`../_common/geomkit.py`).
- Plates are fictional (no state, no marks); no badges, no names anywhere on the car.

## Заимствовано из Феррета (library materials and textures, D:\REPOerret\liberret-assets)

- rug (материал и текстуры basecolor/normal/orm): carpet
- gray-fabric1 (материал и текстуры basecolor/normal/orm): headliner
- cloth-grey (материал и текстуры basecolor/normal/orm): seat cloth
- metal-black (материал и текстуры basecolor/normal/orm): chassis, underbody parts
- metal-steel (материал и текстуры basecolor/normal/orm): exhaust, rear axle
- Method and parts code: carkit.py (tyres with tread and sidewall lettering, brake discs, calipers, lamps, seats, glass, wipers, bevels) from the library's car examples, copied to `../_common/carkit.py`; the lofted-body, boolean-cut and door-split construction follows the library police sedan's build script.

## Made for the game

- Everything else: the body, doors, lids, bumpers, glass, trim, lamps, interior, engine bay, underbody, wheels (`../_common/cargen.py`, `pickup_geom.py`, `build_pickup.py`), the paint colour set (material variants KHR_materials_variants: two_tone_blue, red, white, brown_metallic, light_blue, forest_green), the dirt vertex colours, the damaged pose.
- Build: `blender -b -t 8 -P build_pickup.py -- --out pickup87.glb --lod1 pickup87_lod1.glb --damaged pickup87_damaged.glb`.
