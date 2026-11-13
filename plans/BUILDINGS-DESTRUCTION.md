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

## 5. Stage 2 (2026-11-12, evening): six more fronts, the door fixed

Owner's order: go on by the plan, the shop windows, doors and awnings of the other buildings one by one, the walls stay whole, no design changes.

* Converted besides the pilot (the player's side, before the pilot, designs by the name of the building node): `Bld_R_101_19`, `Bld_R_102_21`, `Bld_R_103_28` (no awning in that design), `Bld_R_104_08`, `Bld_R_105_32`, `Bld_R_106_25`. Files `art/street/shops/shop_<design>.glb` made by `shopfront_parts.py --designs 25,32,08,28,21,19` (0.6 to 1.7 MB each; with the pilot 103 parts: panes, transoms, door leaves and glass, signs, awning sections). The page list is `SHOP_BUILDINGS` in `src/game/shopfronts.ts`. Nothing else in the page changed; the street glb is still untouched.
* Two defects found by the run and fixed in `shopfronts.ts`:
  1. The door leaf was made as thick as the mesh bounds (16 cm: the handle and the glass stop are inside the bounds), so it held a car at 16 m/s with all of the energy going to heat. Now it is the 45 mm oak leaf the plan says. Probe on fresh doors, 1600 kg: 16 m/s and 8 m/s break the leaf (fracture 1046 J and 744 J), 5 m/s does not (no fracture).
  2. When the leaf broke, its glass pane stayed whole in the air (state `whole`, drawn). Now a pane whose leaf is gone falls out: the module gets a break of the pane with the energy of its fall (mass x g x height of its centre), and if the module leaves it whole it is released from the leaf anyway. Checked in the run: leaf and pane go together (`ShopDoorGlass:gone`, `ShopDoorLeaf:gone` on 101, 102, 104).
* Run (RTX 3050, Chromium d3d11, the machine loaded by other work, so the frame times are rough; A = `?shops=0`, B = seven fronts): shots D:/temp/take37/bldfronts/shots (`B_*` before the fixes, `D_*` after; `row`, `<building>_0before`, `_1mid`, `_2after`, `_3close`), logs D:/temp/take37/bldfronts/*.log, scripts there too (run.mjs, run2.mjs, idle.mjs, door.mjs).
  * One police car at 16 m/s into each building, aimed at its door where the sidewalk was free (only 104_08), else at a window: panes gone in front of the car and next to it (3 per building), the transom, and the door leaf where the car reached it (101, 102, 104). The pharmacy-like pilot was not hit again.
  * A tanker (3 m high cab) into the awning of 101_19: `awningsHit` 132, one section fell, the sign broke, 21 panes in all by then (the tanker also took fire and blew, frame D:/temp/take37/bldfronts/shots_prev/B_T19_2after.png). A blast of 20 kg TNT in the street in front of 106_25 (the game's facade path): all 27 awning sections of the seven fronts fell, 62 panes, 7 doors, 7 signs broke (shots_prev/B_B25_*); the same blast without the new fronts leaves the fronts whole and white-outs the frame (A_B25 frames).
  * Frame time, idle, the row of seven fronts in view, mean of 8 s after 25 s of settling: A 61.4 and 61.7 ms, B 80 and 98 ms (median 50 against 66 and 83). Active meshes in the frame: A 948 and 1030, B 1458 and 1354, so about 400 to 500 more draws for seven fronts (about 60 per front: every part is its own mesh with several materials). After the 20 kg blast the frames are not comparable (A is a white-out).
* What is still wrong or not done:
  * The wall box still stops the car; only panes next to the car are hit. Street furniture on the sidewalk (mailbox, parking meters, shelters) kept the lane to five of the six doors blocked, so those cars hit windows.
  * Cost: with seven fronts within 130 m the frame is 30 to 60 percent longer on this machine. A shorter distance for the parts (the plain level of detail beyond about 70 m) would cut it but breaks seen from far would not show; not changed, it is a design question for the owner.
  * Left side of the street and the remaining 36 designs on the right side are not converted.
