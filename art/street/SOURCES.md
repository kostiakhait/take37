# Street kit and level: sources

Everything in `art/street/` is built by the scripts in this folder (Blender 4.2, headless). No photographs and no external models were downloaded or used. Proportions follow public
US practice (MUTCD sign shapes and colours, a federal publication in the public domain; 12 ft lanes of 3.4 m, 1980s kerb and parking-stall sizes); nothing is traced from a picture.
No brand logos or real trademarks anywhere: shop boards carry generic words (HARDWARE, DINER, ...), the road signs carry generic street names, the gas station has no brand.

## Borrowed from the asset library (заимствовано из Феррета)

Library packages `tex-*` (base colour, normal, ORM maps), read from `D:\REPO\ferret\lib\ferret-assets` through `catalog.json`; each is tinted or re-toned in `textures_prep.py`, the maps themselves are not edited:

| Library texture | Used for (texture id in the glb) |
|---|---|
| tex-brick-clay-new-material-sphere-2 | facing brick of the shop fronts and upper floors: brick_red, brick_brown, brick_buff |
| tex-brick-clay-old | side and back walls, chimneys: brick_old |
| tex-stucko-wa1 | plastered fronts: plaster_cream, plaster_white, plaster_sage, plaster_grey, plaster_rose |
| tex-column-plaster-311 | window casings, cornices, trim: trim_white |
| tex-concrete-block | kerbs, plinths, lintels, forecourt: concrete_found |
| tex-concrete | sidewalk slabs (base colour; joints, broom and per-slab turn made for the game) |
| tex-concrete-312 | asphalt: the aggregate grain and the normal map (the colour pass is made for the game) |
| tex-wood-beige | the grain under the painted clapboard siding |
| tex-wood-pine, tex-wood-brown, tex-wood-dark-brown, tex-wood-oak | bench slats, shop-front frames, utility poles, counters, floors |
| tex-bark01, tex-bark02 | tree trunks and branches (maple; elm and oak) |
| tex-ground-grass, tex-grass | verge round the street, planters, lot edge |
| tex-soil | tree pits and planters |
| tex-rock-slate | pitched roofs |
| tex-metal-steel | all painted and bare steel: paint_* variants (tinted; metalness removed for painted parts), steel |
| tex-metal-black | black iron: fire escapes, awning arms, door frames |
| tex-cloth-white-rough | awning canvas in seven colours |

## Made for the game

- Asphalt colour pass with ageing, wheel tracks, oil lines and gutter grime (vertex tone in `street_geo.py`), worn-asphalt and sidewalk slabs with tooled joints, broom texture and a random quarter turn per slab.
- Clapboard siding (lap, shadow line, butt joints, wear), seven paint colours; its normal map.
- Lane paint with worn alpha (white, yellow), crosswalk bars, stall ticks, stop bars.
- Road decal atlas: oil stains, cracks, tar patches with torn edges, utility trench, round manhole cover, storm-drain inlet, skid marks.
- Road-sign atlas after MUTCD shapes and colours: STOP, SPEED LIMIT 25, NO PARKING, ONE WAY, pedestrian crossing, DO NOT ENTER, ROAD CLOSED, FILM SET - NO ENTRY (the film-crew barrier boards), twelve street-name blades, parking meter face.
- Shop boards (32 generic names), the painted window backdrops used by LOD1, leaf-cluster atlases for maple, elm and oak (`leaf_*_c.png`).
- Trees (`trees_kit.py`, wind data in `TREES.md`): branching skeletons with bark, painted leaf-card clusters, six kit items, LOD pair each.
- Real shop interiors for LOD0 (`interiors_kit.py`): rooms with floor, walls, ceiling, fluorescent fixtures, shelving with product fronts, counters, stools, mirrors, display cases, TV racks, washers, barber chairs, sofas ... chosen by shop type; window decals (OPEN, SALE, hours, posters), haze and grime on the glass.
- Upper-floor window rooms (blinds, shades, curtains, lit/dark rooms; window air conditioners), wall art (ghost ads, wheat-paste posters, graffiti tags, rain streaks) on side walls and bulkheads (`textures_detail.py`).
- Street wear (`street_decor.py`): litter, autumn leaves in gutters and on the walk, puddles, sidewalk cracks and utility lids, a second telephone/cable wire pair and service drops.
- All geometry: buildings (36 street designs, 14 side-street designs, each as LOD0 and LOD1), street furniture (LOD pairs), road, kerbs, sidewalks, markings, wires, barriers, gas station.
- Typeface for lettering: DejaVu Sans / Serif (Bitstream Vera derivative, free licence; copy shipped with matplotlib), drawn into the textures.

## Reproduce

    python -I art/street/textures_prep.py
    python -I art/street/textures_detail.py
    blender -b -P art/street/stage_level.py     # street_level.glb + street_colliders.glb
    blender -b -P art/street/stage_kit.py       # street_kit.glb
    blender -b -P art/gas-station/build_gas.py  # gas_station.glb
