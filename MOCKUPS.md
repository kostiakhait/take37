# MOCKUPS: what in the playable scene 1 stands in for something that is not made yet

Every replacement of the playable scene (src/game, src/play.ts) is listed here with where it is and what replaces it. Sizes and colliders are real in all of them (they come from the art files by node name).

| What | Where | Replacement now | To replace with |
|---|---|---|---|
| Damaged model of the police car | `art`/`assets/borrowed/crown_victoria_cpd87.glb` has no `_damaged` file | the whole model stays when the car is a wreck; parts still come off (hood, trunk, doors, bumpers, wheels) and the sim keeps the damage | `crown_victoria_cpd87_damaged.glb` (same node names), then set `damaged` of `police` in `src/game/config.ts` |
| Damaged model of Vincent's Corvette | `assets/borrowed/corvette_c4_87_conv.glb` has no `_damaged` file | same as above | `corvette_c4_87_conv_damaged.glb`, `damaged` of `corvette` in config.ts |
| Damaged model of the tanker | `art/tanker/` has only whole and lod1 | the whole model; the tanker's fire and blast are drawn by the engine vfx at the tank | `tanker_1987_damaged.glb`, `damaged` of `tanker` in config.ts |
| Matthew jumping out | `Take.jumpOut` in `src/game/take.ts`, drawn in `src/game/view.ts` (`makeDebris`, kind `matthew`) | a blue box of 0.5 m with the mass and the throw of a man (80 kg) | the character model of Matthew with a falling/rolling clip |
| Matthew and Vincent inside their cars | cab and Corvette | not drawn (the first-person view has no body; the Corvette's driver is not modelled) | driver figures in the car models |
| Fragments of a burst tank and cars (fire.ts) | `sim.debris` kinds from `src/game/fire.ts`, view `makeDebris` | dark metal boxes with the size the sim gives them | fragment meshes from the tanker's tank parts |
| Parked and moving traffic far from the camera | `lod1` files of each kind | the lod1 model beyond 110 m, the full model nearer | none (it is the design) |
| Sounds | `src/game/audio.ts` | engine, horn, siren, crashes and blasts are synthesized (WebAudio) | recorded sounds through the engine's audio service |
| Director's reaction | `directorSays` in `src/game/take.ts`, `src/game/hud.ts` | text caption only | voice (planned), the text stays as subtitles |
| Pedestrians | none in the scenario | none | none |
| Dents of the car bodies | `src/game/view.ts` | the damage shows as parts that come off, the vehicle's tilt and the `_damaged` model for traffic cars; the engine's dent lattice (`@ferret/destruction/view-dents`) is not applied to the model meshes | apply `DentCage` to the part meshes of the near cars |

## The station on the street

`art/gas-station/gas_station.glb` (full, with Pump_*, PriceSign, Canopy, CanopyColumn_*, PropaneCage, Fire_* markers) is loaded at `GasStation_Anchor` of the street, turned by +90 degrees about the vertical so that the file's +x (street edge to the shop) runs away from the road (the anchor's own rotation puts it onto the road). The light `gas_station_lite.glb` that `src/scene/set.ts` loads is not loaded in the game (the loader call is answered empty from `src/play.ts`, `set.ts` is not edited). The 36 x 68 m lot covers x 527.75..596.25, z -53.3..-9.3 and overlaps two street buildings (x 522.5..530.5) by 2.5 m at its back corner: it is the art's own size and position; the station art is not edited.

## Assumptions of the game (not art)

- The spawns are read from the street's `SPAWN_Pursuit` and `SPAWN_Player` nodes: the police car at the first, Vincent's Corvette at the second.
- The line fuel of a pump is 600 kg (`PUMP_LINE_KG`), the blast yield of a fuel fire is 2 percent (`BLAST_YIELD`), set in `src/game/fire.ts`.
- The engine's `Vehicle` brakes all wheels together: the handbrake locks all four (no rear-only lock).
- The throttle is limited by a traction factor (speed and yaw rate) in `src/game/sim.ts`, because the engine's vehicle spins at full throttle above 15 m/s.
