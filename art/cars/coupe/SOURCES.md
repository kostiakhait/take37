# Large two-door coupe with a formal roof and opera windows (rear drive), early-80s look

Nodes and files: `coupe84.glb` (full detail), `coupe84_lod1.glb`, `coupe84_damaged.glb` (the same node set posed wrecked: dents, loose bumpers, bent lids, torn-off look, dirt). Root `Coupe84`.

## Shape and sizes

- Outline drawing: Chevrolet Monte Carlo SS 1986 (Outlines, getoutlines.com, https://getoutlines.com/blueprints/12653/1986-chevrolet-monte-carlo-ss-coupe-blueprints, CC BY 4.0). 1888 x 2366 px, the second side view; the drawing's lowered stance and large wheels are not taken over. Copy in `reference/chevrolet-monte-carlo-ss-1986-outlines.png`.
- Sizes: Wikipedia, Chevrolet Monte Carlo (1980-87): wheelbase 108.0 in, length 200.4 in, width 71.8 in, height 54.0 in. Tyre P205/70R14. The drawing gives the shape, every listed size is honoured (`../_common/geomkit.py`).
- Plates are fictional (no state, no marks); no badges, no names anywhere on the car.

## Заимствовано из Феррета (library materials and textures, D:\REPOerret\liberret-assets)

- rug (материал и текстуры basecolor/normal/orm): carpet
- gray-fabric1 (материал и текстуры basecolor/normal/orm): headliner
- cloth-grey (материал и текстуры basecolor/normal/orm): seat cloth
- metal-black (материал и текстуры basecolor/normal/orm): chassis, underbody parts
- metal-steel (материал и текстуры basecolor/normal/orm): exhaust, rear axle
- Method and parts code: carkit.py (tyres with tread and sidewall lettering, brake discs, calipers, lamps, seats, glass, wipers, bevels) from the library's car examples, copied to `../_common/carkit.py`; the lofted-body, boolean-cut and door-split construction follows the library police sedan's build script.

## Made for the game

- Everything else: the body, doors, lids, bumpers, glass, trim, lamps, interior, engine bay, underbody, wheels (`../_common/cargen.py`, `coupe_geom.py`, `build_coupe.py`), the paint colour set (material variants KHR_materials_variants: black, burgundy, silver, dark_blue, gold, white), the dirt vertex colours, the damaged pose.
- Build: `blender -b -t 8 -P build_coupe.py -- --out coupe84.glb --lod1 coupe84_lod1.glb --damaged coupe84_damaged.glb`.
