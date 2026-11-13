# Assets

| Asset | Origin | Notes |
|---|---|---|
| Police sedan, 1987 (assets/borrowed/crown_victoria_cpd87*.glb) | заимствовано из Феррета (заимствовано из библиотек) | cab reworked for the first-person view (art/cars/police, SOURCES.md); exterior as is |
| Corvette C4 convertible, 1987 (assets/borrowed/corvette_c4_87_conv*.glb) | заимствовано из Феррета | used as is |
| Materials and textures of the library | заимствовано из Феррета | each use is listed per model in art/*/SOURCES.md |
| Everything else in art/ | made for the game | references and their licences are in art/*/SOURCES.md |
| Scene 3 (airfield): terrain, farmland, forest, lakes (src/scene3) | заимствовано из Феррета (Zeppelin sample's landscape: height, farmland and forest rules, its spruce; @ferret/terrain; the engine's water) | the field sits in the 100 x 100 km Zeppelin zone; fields, hedges and the airfield's wear map are made for the game in code |
| Scene 3: runway concrete, apron, brick, roof tiles, steel, rust, crates, timber, plaster, concrete block | заимствовано из Феррета (library materials by catalog id) | listed in src/scene3/mats3.ts and buildings3.ts |
| Scene 3: aircraft (mustang, spitfire-mk1, hurricane-mk1, avenger, b17g), lorry (bedford-qld), guns (bofors-twin-mk1, qf-25pdr), people (tommy-*, officer-1, sailor-2) | заимствовано из Феррета (library models and characters) | aircraft far away by @ferret/perspective, people on @ferret/physics Walkers with @ferret/micromotion |
| Scene 3: asphalt (tarmac), slab and tarmac wear, tyre rubber, paint and the numerals 36/18, corrugated-sheet normal map, sandbags, chain-link, the R22 pad's H, lane marking of the road | made for the game, drawn in code (src/scene3/textures3.ts) | the library has no asphalt, no paint, no corrugation, no sandbag or wire-mesh texture |
| Scene 3: hangars, tower, Nissen huts, fuel store (tanks, drums, bowser), sheds, windsock, fence, gate, edge lights; meadow tufts, long grass, docks, parsley, bramble, hawthorn, oak, ash, elm, poplar | made for the game, built in code (buildings3.ts, plants3.ts) | shapes only; their materials are the library's where one fits |
