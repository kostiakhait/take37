# Assets

| Asset | Origin | Notes |
|---|---|---|
| Police sedan, 1987 (assets/borrowed/crown_victoria_cpd87*.glb) | заимствовано из Феррета (заимствовано из библиотек) | cab reworked for the first-person view (art/cars/police, SOURCES.md); exterior as is |
| Corvette C4 convertible, 1987 (assets/borrowed/corvette_c4_87_conv*.glb) | заимствовано из Феррета | used as is |
| Materials and textures of the library | заимствовано из Феррета | each use is listed per model in art/*/SOURCES.md |
| Everything else in art/ | made for the game | references and their licences are in art/*/SOURCES.md |
| Scene 2 field: beach, sea with surf and tide, sky, weather ladder, timber mole on piles, dunes' plants (src/scene2, tools/build_scene2.mjs) | заимствовано из Феррета | modified: the mole is 250 m long, the field 600 m, the sea bed steeper (5 m of water at the mole's end), the dunes higher behind the beach |
| Scene 2 fleet: destroyers (mdl-fletcher), yachts (mdl-sundowner), boats (mdl-lucy-lavers), paddle steamer (mdl-princess-elizabeth) | заимствовано из Феррета | modified: instances with their own liveries (repainted materials), scale 0.9-1.15, trim +-2 degrees, laid at anchor in the roadstead; the steamer has her place at the mole's east face |
| Scene 2: prisoners' cages on casters (src/scene2/cage.ts), the villain's post (barrack, watch tower with searchlight, fence with gate; src/scene2/base.ts), the dirt road | made for the game | procedural, no library model; materials are plain colours (khaki/grey), no signs or emblems |
| Scene 2 grove: spruces and bushes (mdl-spruce-tree, bush-1, bush-2) | заимствовано из Феррета | ~200 thin instances behind the dunes, scaled and placed for the game |
| Scene 2 people: henchmen in khaki (tommy-1..3 battledress and helmet), sailors (sailor-1, sailor-4), the three rings of figures (full, lod1, baked impostors), FarCrowd, Decks (the decks read off the models for the walkers), the posture AI | заимствовано из Феррета | src/scene2/near2.ts is the Dunkirk sample's NearCrowd with its pool counts as a parameter (the game's own figure mix); people.ts uses the sample's Decks and FarCrowd as they are; who stands where, the khaki henchmen on decks, at the post and on the road, the sailors on the steamer and in the distant assault, is the game's |
| Arnold and Emily in the cages (art: the game's own characters, MetaHuman base, built by tools/build_character.mjs with SKIN=1; web copies by tools/optchar.mjs) | made for the game | skinned glb, the micro-motion module (breath, weight, head, fidgets, hands on the bars or on the knees) drives the skeleton |
