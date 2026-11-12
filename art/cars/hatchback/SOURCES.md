# Compact five-door hatchback (front drive), 1981-87 look

Nodes and files: `hatchback85.glb` (full detail), `hatchback85_lod1.glb`, `hatchback85_damaged.glb` (the same node set posed wrecked: dents, loose bumpers, bent lids, torn-off look, dirt). Root `Hatchback85`.

## Shape and sizes

- Outline drawing: Ford Escort Mk III 5-door 1980 (Outlines, getoutlines.com, https://getoutlines.com/blueprints/17467/1980-ford-escort-mk-iii-5-door-sedan-blueprints, CC BY 4.0). 500 x 385 px, side view at the top. Copy in `reference/ford-escort-mk-iii-5-door-1980-outlines.jpg`.
- Sizes: Wikipedia, Ford Escort (North America), first generation: wheelbase 94.2 in, length 169.4 in, width 65.9 in, height 53.7 in (hatchback). Tyre P165/80R13. The drawing gives the shape, every listed size is honoured (`../_common/geomkit.py`).
- Plates are fictional (no state, no marks); no badges, no names anywhere on the car.

## Заимствовано из Феррета (library materials and textures, D:\REPOerret\liberret-assets)

- rug (материал и текстуры basecolor/normal/orm): carpet
- gray-fabric1 (материал и текстуры basecolor/normal/orm): headliner
- cloth-grey (материал и текстуры basecolor/normal/orm): seat cloth
- metal-black (материал и текстуры basecolor/normal/orm): chassis, underbody parts
- metal-steel (материал и текстуры basecolor/normal/orm): exhaust, rear axle
- Method and parts code: carkit.py (tyres with tread and sidewall lettering, brake discs, calipers, lamps, seats, glass, wipers, bevels) from the library's car examples, copied to `../_common/carkit.py`; the lofted-body, boolean-cut and door-split construction follows the library police sedan's build script.

## Made for the game

- Everything else: the body, doors, lids, bumpers, glass, trim, lamps, interior, engine bay, underbody, wheels (`../_common/cargen.py`, `hatchback_geom.py`, `build_hatchback.py`), the paint colour set (material variants KHR_materials_variants: red, white, light_blue, silver, yellow, dark_green), the dirt vertex colours, the damaged pose.
- Build: `blender -b -t 8 -P build_hatchback.py -- --out hatchback85.glb --lod1 hatchback85_lod1.glb --damaged hatchback85_damaged.glb`.
