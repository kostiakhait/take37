# Wood-panel station wagon (four doors and a tailgate, rear drive), 1981-83 look

Nodes and files: `wagon82.glb` (full detail), `wagon82_lod1.glb`, `wagon82_damaged.glb` (the same node set posed wrecked: dents, loose bumpers, bent lids, torn-off look, dirt). Root `Wagon82`.

## Shape and sizes

- Outline drawing: Chevrolet Malibu Station Wagon 1981 (Outlines, getoutlines.com, https://getoutlines.com/blueprints/18957/1981-chevrolet-malibu-station-wagon-wagon-blueprints, CC BY 4.0). 2503 x 780 px. Copy in `reference/chevrolet-malibu-station-wagon-1981-outlines.png`.
- Sizes: Wikipedia, Chevrolet Malibu (1978-83): wagon wheelbase 108 in, length 193.4 in, width 71.2 in, height 54.5 in. Tyre P195/75R14. The drawing gives the shape, every listed size is honoured (`../_common/geomkit.py`).
- Plates are fictional (no state, no marks); no badges, no names anywhere on the car.

## Заимствовано из Феррета (library materials and textures, D:\REPOerret\liberret-assets)

- rug (материал и текстуры basecolor/normal/orm): carpet
- gray-fabric1 (материал и текстуры basecolor/normal/orm): headliner
- cloth-grey (материал и текстуры basecolor/normal/orm): seat cloth
- metal-black (материал и текстуры basecolor/normal/orm): chassis, underbody parts
- metal-steel (материал и текстуры basecolor/normal/orm): exhaust, rear axle
- wood-walnut (материал и текстуры basecolor/normal/orm): simulated wood side panels
- Method and parts code: carkit.py (tyres with tread and sidewall lettering, brake discs, calipers, lamps, seats, glass, wipers, bevels) from the library's car examples, copied to `../_common/carkit.py`; the lofted-body, boolean-cut and door-split construction follows the library police sedan's build script.

## Made for the game

- Everything else: the body, doors, lids, bumpers, glass, trim, lamps, interior, engine bay, underbody, wheels (`../_common/cargen.py`, `wagon_geom.py`, `build_wagon.py`), the paint colour set (material variants KHR_materials_variants: beige, forest_green, brown, light_blue, burgundy, white), the dirt vertex colours, the damaged pose.
- Build: `blender -b -t 8 -P build_wagon.py -- --out wagon82.glb --lod1 wagon82_lod1.glb --damaged wagon82_damaged.glb`.
