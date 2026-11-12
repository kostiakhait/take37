# Destructible street buildings (step 0 and the pilot)

Owner's order (2026-11-12): use the engine's physics and library materials to the maximum, and make the street buildings destructible gradually, building by building, without breaking the rest of the game.
Owner's decision on what breaks first: shop windows, doors, awnings and signs. The house walls and the upper floors stay whole until the owner says otherwise.

## 1. What the modules offer for buildings

`@ferret/destruction` (read from the sources in packages/destruction/src):

| Need | Module part | Law |
|---|---|---|
| window pane, transom, door glass | `glass.ts` (`glassModel`), substances `glass-annealed` (modulus of rupture 40 MPa), `glass-tempered` (160 MPa, dices at once), `glass-laminated` | Roark plate stress from the hit's energy; stages none, star (the crack star is kept as numbers), shards; the crack surface must be paid for (surface energy); thickness (6 mm, 4 mm) and size are inputs |
| door leaf, sign board | `wood.ts` (`woodModel`), `wood-oak`, `plywood`, `wood-pine` | bending between supports (F = 4 sigma Z / L), knots, splinters, nails that pull out |
| awning (aluminium sheet and arms) | `crush.ts` (ductile: crush zone, 5x3x3 dent lattice) and `assembly.ts` (a part joined to the wall by bolt links that hold `tensile x area x count`; a part with no path to the root comes off) | force-depth curve; link load = residual energy / LINK_GIVE |
| brick wall, plaster | `stone.ts` (`brick`, `concrete`, `plaster`): Voronoi cells by energy, bricks by mortar links, plaster to dust | NOT used in this stage (walls stay whole). The game already has a 3 x 3 m brick bay for blasts (`Sim.blastFacades`) |
| pieces | `debris.ts`: near pieces are bodies, middle ones instances, far ones are not made; cap `maxPieces`; one sound per break | the game's service has `maxPieces: 400`, `maxBodies: 0` (pieces fall by the module's cheap fall), drawn by `ShardView` instances |
| replication | `breakSeed(entity, step, point)`, `BreakRecord`, `replay` | the seed is a hash of the thing, the step and the point, so two machines get the same pieces |
| style | `StyleBook`: the game's `film` level style (physical energy, 1.25x deeper crush, 3x pieces, bounce 0.4) rules these things as it rules the cars and props | |
| blast | `@ferret/physics-explosions` `blastAt(r, tnt)`: overpressure and impulse; `fire.ts` already calls `sim.blastFacades` for blasts of 20 kg TNT and more | |

`@ferret/physics-strength` (`fractured` walls in a level's physics block, `joint` with `maxForce`) is the body-level mechanism of the Havok kernel. The game does not run that kernel (its cars run on the destruction module's own wheeled assembly), so the destruction module is the one that fits; the "pre-fractured wall" of the strength skill is the same idea as the module's Voronoi and brick cells, and is the route for walls later.

Library materials: the building textures are library materials already (tex-brick-clay-*, tex-stucko-wa1, tex-wood-*, tex-cloth-white-rough for the awning canvas; see art/street/SOURCES.md). The parts keep them: the shop file carries no textures, and the page gives each part the street's own material of the same name, so a converted shop front is made of the same brick, wood, glass and canvas as before. The module's substances (glass, oak, plywood, aluminium) are the physical side of the same things.

## 2. What was chosen for the pilot, and why

* One building: `Bld_R_107_18` (x 491.5 to 507.0, the player's side of the street, design 18: a pharmacy front with a long striped awning, 15 m wide, two storeys), the last building before the gas station on the player's route.
* The street glb is NOT rewritten. The building's own meshes are taken out of the street in the page (`hideConverted`, before the street is merged by cell) and the building comes from its own file `art/street/shops/shop_18.glb`: the shell (the same building made by the same `buildings.py` code with the same random numbers, minus the parts) at both levels of detail, and the parts of the full level as meshes of their own: `Part_ShopWindow_<k>_<j>` (one pane between two mullions, 8 panes), `Part_ShopTransom_0`, `Part_ShopDoorLeaf_0`, `Part_ShopDoorGlass_0`, `Part_ShopSign_0`, `Part_ShopAwning_<j>` (5 sections of about 3 m).
  Why not the street glb: it is 81 MB, other agents change it at the same time (terrain, trees, road patch), and rewriting it for one building means a full rebuild and a new package hash for everybody. The pilot is one 1.6 MB file loaded beside it; the original is hidden (an instance is disposed; if the design's source mesh is shared with other buildings it is collapsed to nothing for this building only). `?shops=0` gives the street exactly as it was (for A/B runs). Later converted buildings can be built into the street glb by `stage_level.py`; the split code (`partsplit.py`) is the same.
* `buildings.py` has `with m.part('tag'):` around the shop front's parts. A plain build ignores it, so the other designs and the street glb are unaffected until they are converted.
* Game side, `src/game/shopfronts.ts`: each part is a thing of the module: panes `glass-annealed` 6 mm (transom 4 mm), the door a `wood-oak` leaf with a `glass-tempered` pane joined by a putty link, the sign `plywood` 20 mm held at two fixings, the awning `aluminium-sheet` 2 mm bolted to the wall by four M10 bolts (links that snap at what the bolts hold). A car's contact with the building box (`Sim.collideStatics`) goes to `ShopSim.wallHit`, which gives the closing speed to the parts in front of the car through `DestructionService.contact`; a blast goes through `blastFacades` to `ShopSim.blast` (impulse of the wave times the part's area, over its mass, as the speed it is pushed to). The module decides by the material: no health number, no hand-made break list.
* Picture, `src/game/shopfronts-view.ts`: hides a part that is off, draws the module's crack star on a pane that only cracked, lets an awning section that came off its bolts fall with the sim's debris. The module's pieces (shards, splinters) are drawn by the existing `view.ts`; glass pieces are glass, door and sign pieces are wood.
* Beyond 130 m the plain level of detail of the building is shown, with an intact shop front.

## 3. What it costs and what it needs

* Load: one more 1.6 MB file (loaded after the street) and 17 module things at the start of a take.
* Draw calls: the building's shell was inside the 80 m cell meshes; now it is its own meshes plus 17 parts, about +40 draws while within 130 m, none beyond.
* A break costs the module's `contact` plus the shard instances (cap 400 pieces for the whole world).
* From the street glb: nothing for the pilot. To convert another building: export its design with `art/street/shopfront_parts.py --designs <name>` into `art/street/shops/shop_<name>.glb` and add its `Bld_*` node to `SHOP_BUILDINGS` in `src/game/shopfronts.ts`.

## 4. Results and what is still wrong

Run of 2026-11-12, one pass, RTX 3050 (Playwright chromium, d3d11), A = `?shops=0` (street as it was), B = pilot, in the same run on the same machine; the machine was loaded by other agents, so the frame times are rough:

* Before the crash the two frames are the same (full striped awning, the shelves seen through the glass); frames D:/temp/take37/shopsrun/A4_0_before.png and B4_0_before.png.
* A police car at 17 m/s across the pavement into the front: in B three panes (`ShopWindow_0_3`, `_4`, `_5`) break by the module (`glassBroken` 3), the glass is gone and the shelves are seen through the empty frames, shards fly and lie (B4_4_close.png); in A the front stays whole and the car stops at the wall (A4_4_close.png). Pieces on the street after: A 161 (the car's own), B 128.
* Frame time (ms, mean of 3 to 9 samples at idle and after the crash): idle A 368, B 390; after the crash A 1228, B 1283. On the loaded machine these are 5 percent apart, inside the noise; no collapse.

What is still wrong:
* The wall box of the building still stops the car: it does not drive into the shop. Only the panes in front of the car and next to it go.
* Door, sign and awning reaction (the same code path) was not shown by a car in this run: `awningsHit` 0, `doorsBroken` 0 (the car hit the panes only). Their code is the same module calls, but it has not been seen in a frame.
* Only one building is converted (the pilot); the others stay as they were.
* The street glb is not rewritten (the shop is a second file, 1.6 MB).
