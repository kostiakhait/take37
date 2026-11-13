# TAKE 37 — plan

Contest game, theme "Director's Cut". Built on Ferret, delivered as an Unreal Engine 5 build for Windows.

## 1. Deadline

- Submission: Sunday 2026-11-15, 21:00.
- Game complete: Saturday 2026-11-14, evening.
- Sunday: UE5 port. The port starts as soon as scene 1 is ready, not on Sunday.

## 2. Story

1987. A studio shoots an action film that is doomed to fail, on a fixed budget. The whole crew are freaks: a petty-tyrant director, a narcissistic lead, a beautiful flighty heroine. The only sane person is the stuntman. Only spectacular effects can save the film, and all hope is on him.

## 3. Game

- First person, as the stuntman **Matthew**.
- One mission is one scene to be shot spectacularly.
- Unlimited takes; each take costs budget. Budget gone: game lost.
- Budget: $15,000,000 at the start. Version 1: a take costs a fixed $1,000,000 (sized for 3 scenes × 5 takes). If time allows: cost by destroyed props, averaging about $1,000,000 per take.
- A take is scored by the spectacle of its effects. Game score is the sum of the best take of each scene.
- The player sees the budget. The player does not see take points; only the director's reaction.
- Finale: a trailer is assembled automatically from the best takes, with a voice-over commentary; then the score is shown. There is no editing module for the player.
- Language: English (interface, lines, voice). Voice: SquirrelWisdom TTS, pre-recorded into audio files.
- Music: source to be decided along the way.

## 4. Characters

| Character | Look | Role |
|---|---|---|
| Director | dishevelled, bearded, never without a megaphone | mostly sits on a chair; reacts to takes |
| Arnold (lead) | polished man, fashionable suit, styled haircut, clean-shaven | stands beside the director; Matthew works for him |
| Emily (heroine) | Hollywood blonde, bright make-up, a new dress in every scene | takes an active part in scenes |
| Vincent (villain) | sinister old man in a hooded robe | takes an active part in scenes |
| Edward (cameraman) | Black, middle-aged, dreadlocks, oversized clothes; inseparable from his camera | films the scenes |
| Matthew (player) | young man, T-shirt and jeans, shoulder-length red hair | stuntman |

Graphics: maximally realistic, AAA-class; models worked to excellent quality. Idle characters are never still: they gesture, look about and move about (a Ferret module, connected to the game when ready).

## 5. Scenes

1. **Police chase.** Matthew in a police car chases Vincent in a Corvette along a busy street of a small American town. Each take starts with both getting into their cars. A fuel tanker and a gas station are on the street. The task is to wreck a car beautifully with spectacular explosions. Reaching the end of the street is a failed take; the director is unhappy. Score grows with the number of cars wrecked (moving and parked); best of all is setting the tanker and the gas station on fire.
2. **The secret base (evacuation under fire).** Set on a beach, moles, ships and aircraft taken from the Ferret sample set for a beach evacuation (borrowed models: coast, mole(s), vessels, aircraft, soldiers; declared "заимствовано из Феррета"), but the purpose is different. Story: the villain's secret base is on the shore; the whole roadstead is crowded with ships crewed by his henchmen. He keeps Arnold and Emily prisoner in cages on the pier. Task: from the beach, run under fire to the end of the mole, push the cages onto a suitable steamer and sail away on it. A scene full of shootouts: ships sink and explode, the henchmen "die". Score: mostly by the number of ships spectacularly destroyed, to a lesser degree by the number of henchmen "killed". Open: controls on foot and on the ship, cage-pushing mechanic, take-end conditions. Weapons (unlimited ammunition for now, little time): the stuntman has a submachine gun (henchmen, small boats) and a bazooka (ships, fuel, boilers). The "suitable steamer" is the library paddle steamer Princess Elizabeth (1927, package mdl-princess-elizabeth, 5.2 MB): it must be detailed heavily, exterior only (hull plating, rivets, paddle boxes and wheels, funnel, railings, lifeboats, deck fittings, rigging, windows, paint wear); the detailed version is a modification of a borrowed asset and is logged. Two separate cages (Arnold, Emily), pushed PHYSICALLY by Matthew's shoulder on engine rigid-body physics (no button-press shortcut; showing off the engine physics is a goal of the game): BOTH must be pushed onto the steamer, otherwise the scene is not counted. The paddle steamer never sinks (it is the film's ship, it must survive); only the villain's ships sink and explode. A cage that falls into the water spoils the take. The steamer comes to the pier by itself (AI) a fixed time after the take starts, steered by a sailor taken from the library (package chr-human-mh-sailor, "Merchant seaman, 1912", MetaHuman, заимствовано из Феррета; to be confirmed by the owner); pushing a cage before the steamer is alongside drops it into the water: the cage sinks and the take is failed. Take end: once both cages are on the steamer, the AI moves the steamer away from the pier, then the director shouts and the scene is shot (success). Cut conditions (spoiled take): Matthew cannot be killed (he is a stuntman) but he may fall off the mole (the take ends at once, no climbing back; his mission is to run along the mole, shoot and rescue the heroes); a cage falls into the water; the time limit per take runs out (stops aimless running up and down the mole). Time limit value: to be tuned in play.
3. **Plane race.** The villain kidnaps the heroine; the stuntman must catch him and rescue her. Mechanics to be designed while other work is built.

### Scene 1 take flow

1. The director briefs the take through the megaphone.
2. Clapperboard: "Scene 1, take N". Matthew runs to his car, gets in, starts the engine; Vincent does the same.
3. Chase in first person; the director shouts along the way.
4. The take ends: "Cut!" for a spoiled take (left the set, hit the crew, reached the end of the street without a wreck), or "That's a wrap" after a spectacular wreck.
5. Replay from the set cameras with the director's reaction, no numbers.
6. Another take or move on. The best take counts.

Cameras: the set cameras (Edward's among them) score a stunt only when it is in frame; every stunt in frame is stored as a clip for the trailer.

### Controls (proposal, to be confirmed in play)

| Action | Keyboard and mouse | Gamepad |
|---|---|---|
| Gas / brake and reverse | W / S | RT / LT |
| Steer | A / D | left stick |
| Handbrake | Space | A |
| Jump out of the car | E | X |
| Free look | mouse | right stick |
| Horn | H | left stick press |
| Lights and siren | Q | LB |
| Call "Cut" yourself | R | Back |
| Pause | Esc | Start |

On foot (start of a take): WASD, Shift to run, Space to jump or vault the hood, E to open the door and get in.

## 6. Scoring (spectacle only)

Each wrecked car scores; chain reactions score more; the burning tanker and gas station score most, sized by the physics of the fire and blast. Everything is multiplied by being in frame. Scoring is hidden from the player.

## 7. Work stages

| Stage | Content | Check |
|---|---|---|
| G0 | Repository, logbook, plan | pushed, logbook has entries |
| G1 | Characters: director, Arnold, Emily, Vincent, Edward, Matthew | one picture sheet of all six |
| G2 | Scene 1: street, cars, tanker, gas station, Corvette, police car | a drivable street |
| G3 | Scene 1 mechanics: boarding, chase, wreck scoring, cameras, take flow, budget | a full take played |
| G4 | **Start of UE5 port** with scene 1 | scene 1 runs in the UE build |
| G5 | Voice lines recorded to audio files | all lines present |
| G6 | Scene 2 design, then build | a full take played |
| G7 | Scene 3 design, then build | a full take played |
| G8 | Automatic trailer and the score screen | trailer plays with commentary |
| G9 | Balance, polish, final UE5 Windows build | build runs from start to the score screen |

Up to three agents work in parallel. Heavy processes run at lowered priority and in short, resumable stages.

## 8. Assets

Every asset is listed in the logbook with its origin: "заимствовано из Феррета", "ЗАИМСТВОВАНЫ ИЗ БИБЛИОТЕК", or made for this game. Modified assets are logged.

## 9. Open

- Music source.
- Scene 2 and scene 3 mechanics and controls.
- Cost by destroyed props (only if time allows).

### Scene 2 roadstead fleet (owner's decision 2026-11-12)

All vessels from the library (заимствовано из Феррета). Library has one model of each kind: Fletcher-class destroyer (mdl-fletcher), motor yacht Sundowner (mdl-sundowner), RNLI lifeboat Lucy Lavers (mdl-lucy-lavers), PT-boat parts, U-boat; the fleet is instances of these with different liveries, scale and trim, plus any further boats found in the Dunkirk sample.

| Kind | Count | Behaviour |
|---|---|---|
| Destroyer | 2 | indestructible; fires and explosions can break out on them |
| Yacht | 4 | sink slowly from bullets; set on fire and explode from the bazooka |
| Boat | 6 | sink from bullets; blown to pieces by the bazooka |

Score: mostly ships destroyed (yachts and boats count; destroyers count for fires and explosions staged on them), less for "killed" henchmen.

Henchmen "die" both ways: shot ones fall (onto the deck or overboard); blasts throw them as ragdolls. They stand on decks on engine Walkers physics (ferret-physics-walkers), so decks that tilt or sink carry or drop them correctly.

Henchmen shoot at Matthew without doing damage (they knock him back at most). Destroyers fire their guns, anti-aircraft guns fire at aircraft, aircraft raid the roadstead: the whole entourage of the Dunkirk sample is reproduced as the set of scene 2 (2 km beach with the crowd, the mole on piles, wrecked lorries and guns, AA sites, litter, dunes, tide and surf, wakes, weather ladder, air war with Hurricane, Spitfire, Ju 87, He 111, Do 17, Bf 109). All of it is borrowed from the sample and the library ("заимствовано из Феррета"); what is changed (the villain's base on the shore, cages on the pier, fleet, shooting scenario) is logged as modification.

Scale and people of scene 2 (owner's decision): fewer soldiers and a smaller playing field than the Dunkirk sample; no evacuation queue. Two kinds of people: (1) the villain's henchmen, library soldiers in khaki; (2) "sailors", who storm the villain's lair (the crew of the paddle steamer is of this kind). For atmosphere a further assault scene may be staged far away, with no camera approach (distant crowd only, through the engine's far-crowd impostors).

Mole length: 250 m (the sample's is 1.1 km); about 40-50 s of running from the beach to the cages at the end.

Cages: one in the middle of the mole, one at its end. The steamer comes alongside at both places in turn (there and here); Matthew must be at the cage when the steamer arrives. Waiting counts against the take (score penalty that grows with the time spent waiting), so he has to hurry and use the steamer's arrival windows. Exact order and timing of the arrivals: to be tuned in play.

Steamer route (owner's correction): as the destroyer in the Dunkirk sample, the steamer comes in from the end of the mole, so it reaches the END cage first, then the MIDDLE one. If a cage was not pushed aboard, the steamer goes back to the end and returns once more: each extra pass is a score penalty for the scene. (Replaces the earlier "middle then end" reading.)

Penalties (waiting, extra steamer passes) are shown to the player only through the director's reaction; they are subtracted from the scene's points, which stay hidden. No counter.

Director during takes (all scenes): he shouts and gestures along the way, reacting to what happens (hurry, praise, despair). LOWER PRIORITY by the owner's explicit order (2026-11-12): built after everything else; the director's reaction after the take stays as planned.

Order of work (owner's order 2026-11-12): NO work on scene 2 until scene 1 is finished. The scene 2 description above is design only.

## Structure of every scene (owner's decision 2026-11-12)

Each scene consists of a prologue, the playable part and an epilogue. The prologue and epilogue are shot from the third person and driven by the AI; the playable part is from Matthew's eyes and driven by the player.

Scene 1: prologue: Matthew gets up from his chair (the prop is already in place), Vincent gets up from his chair, both walk to their cars and get in; each take they walk a little differently (variation per take). Epilogue: Matthew comes out of the ruins of the street and walks back to his chair. The playable part is built first; prologue and epilogue after it.

## Scene assembly (owner's task to the lead, 2026-11-12)

When the prerequisites are met, the lead assembles the scene 1 play build from the assets as they are, then changes it incrementally as assets and mechanics improve, and shows the renders of each assembly to the owner. Tool: `node tools/assemble_scene.mjs [label]`: own build and port, fixed views (cab, street, the station and the tanker, high views, the chase on the autopilot), renders and `manifest.json` (asset versions, renderer string, console messages) in `D:/temp/take37/assembly/<stamp>/`.

Prerequisites (owner: the cars need not be perfect, they are taken as they are): (1) every asset file of the manifest exists; (2) the page loads without errors on the RTX 3050 and the cab frame is readable (the cab interior is lit, the left pillar is not black); (3) the page runs fast enough for the stills to be taken in a few minutes (the terrain and weather agent's frame-rate work); (4) the verdict camera is not blocked.

## Drawing the player's car from inside (owner's decision 2026-11-12)

The view is first person and the player's head does not turn back, so of the police car only the parts seen from the driver's seat are drawn: the cab (dashboard, wheel, pillars, mirrors, headliner, seats as seen), the inner faces of the doors and the glass, and the outside only where it shows through the windscreen and the side windows (the hood, the front wings, the mirrors). Everything else of the car (the body sides and rear, the wheels, the underside, the boot) is not drawn while the camera is in the cab; it is drawn again in the third-person and set cameras and after the player jumps out.
This is to be a general mechanism of the engine, not a game trick: for any object seen from inside (a cab, a cockpit, a room), the parts that cannot be seen from the inside viewpoint and its allowed head movement are not drawn (computed once per object and viewpoint, kept as a visibility set).

## Trees: leaves and bark (owner's task 2026-11-12)

The foliage of the street's trees is to be improved, most likely through its textures (the leaf cards' colour, alpha and normal maps); the rest of the trees (shape, placement, sway) is fine as it is. The bark is to be improved the same way, by its texture.

## Walls of houses and the station (owner's decision 2026-11-12)

No collapse of walls: house walls stay whole after blasts and impacts. Shop windows, doors, signs and awnings break (buildings destructible gradually); the gas station is brought down through its canopy and roof, not through its walls.

### Sinking of ships (owner's decision 2026-11-12)

Hybrid: a hit makes a breach, the engine's vessel physics (compartments, breaches, flooding, heel, capsize) counts the flooding, but accelerated so that a ship goes down in 20-40 s; heel, trim and capsizing follow from where it was hit. People on a tilting or sinking deck slide and fall overboard through Walkers. Destroyers do not sink: only fires and explosions break out on them. Not built yet: the mechanics of scene 2 are designed after its field and assets.

### Falls of people (owner's decision 2026-11-12)

People fall through the engine's character and animation modules: fall clips (the combat module's death clips by the side of the hit, retargeted), the position carried by Walkers (so a tilting or sinking deck slides them and drops them overboard), a ballistic body under the figure when a blast throws him with the falling pose blended in, and IK so the feet meet deck, mole and sand. A trial scene of falls (bullets from front, side, behind; overboard from a heeling deck; blast throw) is made first and shown to the owner; a physical ragdoll (joints on the Havok kernel) is made only if the clips do not convince. Mechanics of scene 2 are built after its field and assets.

## Scene 3: plane race (owner's description 2026-11-12)

Only what the owner has said is fixed here; everything else is listed under "Open" and is asked, not invented.

### Place

A small provincial airfield: a runway, a taxiway, hangars. A Robinson R22 helicopter stands on the runway ready for take-off. Different aeroplanes of our collection stand on the taxiway, among them a P-51 Mustang. Whether the library has the R22 and the Mustang is to be checked before building.

### Prologue

Vincent kidnaps Emily and takes her away in the R22. As the helicopter lifts off, a police car drives onto the airfield; Matthew gets out of it and climbs into the Mustang.

### Mission

Take off in the Mustang, catch the helicopter, shoot it down, and while it is falling bring the Mustang level with it so that Emily can get onto the wing.

- Weapons: the Mustang's own machine guns. The ammunition is limited.
- The helicopter must be shot down so that it falls as a whole: the fall is physical (loss of lift or tail rotor, spin), not a prepared clip.
- Emily moves to the wing by herself: she jumps. The jump succeeds when the player holds the Mustang beside the falling helicopter within a narrow window of distance, speed and bank. Outside the window the jump fails.

### Epilogue

The Mustang flies into the sunset sea with Emily standing on the wing.

### The take is spoiled (cut) when

- the helicopter is not shot down;
- the helicopter falls with Emily aboard (she is not on the wing);
- the helicopter blows up in the air;
- the jump fails and Emily does not land on the wing.

### The take is a wrap when

The helicopter is shot down and falls as a whole, the Mustang is level with it inside the window, Emily jumps and stands on the wing; then the epilogue.

### Open (to be asked, one question at a time)

- Number of rounds, and how many hits the R22 takes before it loses control (to be tuned in play).
- Controls of the flight (keyboard, gamepad) and the camera (cockpit or outside).
- How Matthew gets from the police car to the Mustang (on foot, how far, whether the player controls it).
- Whether the score of the scene depends on anything besides success (spectacle of the fall, time).
- Voice lines and the director's reaction for this scene.
- Weather and time of day of the airfield (the epilogue is a sunset).

### Scene 3: what is borrowed and what is made (owner's decisions 2026-11-12)

Borrowed from Ferret ("заимствовано из Феррета"; the owner: much comes from the air war samples, air traffic included):
- the Mustang: library model `mdl-mustang` and the playable P-51D of `examples/airwar` (flight model `Aeroplane`, `Pilot`, guns and ballistics, zone damage, gunsight with lead marker, cockpit and chase cameras, HUD, input);
- the air war of `examples/dunkirk/src/airwar.ts` (the same flight core, autopilot-flown aircraft, raids, ground guns) for the air traffic around the airfield, as far as the scene needs it;
- the aeroplanes of the collection standing on the taxiway.

Made for this game:
- the Robinson R22 helicopter, not in the library (owner: "make it ourselves"): a model built in Blender from drawings and photos, and a helicopter flight and damage model on the engine's rotor blocks (`@ferret/physics-rotor`; no helicopter exists in `physics-vehicles` yet): main rotor, tail rotor, collective and cyclic, hits by zone (engine, tail boom, main rotor, cabin), a physical fall after loss of lift or of the tail rotor;
- the airfield (runway, taxiway, hangars), the police car arrival, the jump of Emily to the wing, the fail and wrap conditions above.

### Scene 3: state of the airfield and what is still to do (agent's report 2026-11-13, the agent stopped by the owner)

Built (commit 0383fd2, branch `scene3`, worktree D:/temp/take37/s3_wt; viewer `node tools/build_scene3.mjs` + `tools/serve_scene3.mjs`, page API `window.__scene3`; frames D:/temp/take37/s3/shots/, README.md there):
- the land is the R22 agent's `heli_land_height.ts` (Zeppelin 100 x 100 km zone, coast opened to the east), one height source; ground grid 102 x 60 km, terrain view radius 80 km, far map 120 x 110 km; renderer is @ferret/terrain Landscape + TerrainView (not the Zeppelin sample's quadtree); Zeppelin forest, farmland patchwork, lakes; airwar Sea;
- airfield: runway 1100 x 36 m, taxiway, links, dispersal and hangar apron; 3 hangars, tower, Nissen huts, fuel store, windsock, R22 pad; fence, gate, access road; Bedford lorries, twin Bofors in sandbag rings, 25-pounder, crates; 7 crew on Walkers with micro-motion; the police car drives the game's own car sim to a stop point beside the Mustang;
- all junctions rounded (owner's order 2026-11-13): fillets r 14 m (link-runway, link-taxiway), r 12 m apron entries, 9 m free corners and taxiway ends; yellow centre lines curve on arcs r 28 m; edge lights, taxi lamps and the edge skirt follow the curves;
- Mustang take-off proof (airwar P-51D spec, real field ground): roll 513.6 m, lift-off 52.2 m/s at 18.7 s, lateral deviation ~0, no crash.

To do (nothing is deferred; each item is made, or asked of the owner, one question at a time):
1. Frame time: measured 60-470 ms (disturbed by other processes), budget 16 ms. Profile on a quiet machine; suspects: terrain.update ~22 ms, forest.update ~5 ms (max 51 ms), 470 chunks / 1.08 M triangles at 2 km; per-frame draw calls are not yet measured (the probe counter is cumulative).
2. Spruce forest shader (FadePlugin): error "field selection requires structure" (instanceColor) and 256 "Vertex buffer is not big enough" warnings; the forest renders as dark uniform stipple with a jagged polygon edge.
3. Altitude views: at 2 km the fields are Voronoi cells with seams and the lakes perfect ellipses; at 10 km the land and sea are almost white; the coast is a blur (far map only) with a dark outline strip and a flat white wedge (mountain); the shore is a flat khaki plain, the wave texture is faint, hard black seam lines at the sea edge at sunset.
4. Light: the Mustang, lorries, Bofors and crew are almost black in the day set; sunset frames are too dark (markings invisible, the Mustang a silhouette); the apron asphalt is dark and splotchy; the access road is a black ribbon.
5. Airfield detail: grass tufts stand on the runway concrete; marking and numeral paint is pixelated at the edges; hangars 1 and 2 are flat brown planks with a single brick roof texture, hangar 3 a pink-red mottled texture; the crate stack is a cube with a leaf texture; the tanks are plain cylinders; uniform grass; the apron edge is a jagged brown wear band; the R22 pad texture is not recognisable; a floating thin grey post at the centre of 23_boundary_countryside; Nissen roof blurred; the sailor in 15_fuel_close is bent forward (micro-motion gesture over the idle clip); only two of the seven crew show in 18_crew.
6. Cockpit during take-off: three dark-green boxes, flat black propeller, no instruments (sunset cockpit frames almost black).
7. Re-shoot `final_day` after the fillets (frames 01, 04, 27 show the old square corners).
8. Not built: ambient autopilot air traffic (parked fighters are static), landing test (take-off only), the perspective ladder for ambient traffic untested.
9. Open owner questions: distance of the coast (42 km measured, agent recommends 20-25 km for a chase); take-off direction (runway runs north-south, sea east: turn at once or later); default weather/time (day 13:24 or sunset 18:54); number of rounds; controls and camera of the flight; how Matthew gets from the car to the Mustang (path, cut-scene, controlled); score; voice lines; whether to attack frame time next.

## Status 2026-11-13 (evening; owner's decisions and what is pushed)

Pushed (origin github.com/kostiakhait/take37): main, buildings, mirrors, scene2, scene3; ferret branch `morph` (cedae32c). Uncommitted in worktrees: the mirrors work (D:/temp/take37/mirror_wt, inner mirror removed, see below), the damage agents' files for the other five cars.

Accepted by the owner:
- police cab (0776455) "acceptable, not ideal";
- coupe damage sample (27 variants, 24fce52): the owner accepted the agent's work; the batch for hatchback, minivan, pickup, sedan, wagon (27 variants each) was launched 2026-11-13; the police car is not in this batch; game side still lacks corner hit types (`HitSide` in view.ts: front_corner and rear_corner variants need it);
- gas station: canopy break into 9 panels (seq5 blast-with-collapse frames accepted); the fire look pass (2030b09: orange tongues, stronger at the pumps, thick tall smoke, soot) is accepted as is; known and accepted: soot too heavy on the forecourt, blast frame ~807 ms, yellow-white root at the pumps, white shock cloud over the minimart, stray pole lying in the blast frames;
- R22 helicopter (0c25eed, 89322d2): delivered; the owner calls it "a toy helicopter", no re-run for now; defects: bulbous cowl, grey side glass from outside, overlapping gauge labels.

Mirrors (owner's order: simplest picture, just see what is behind the car, close the task fast):
- the inside mirror is removed (nodes Mirror_Inner / Mirror_Inner_Glass out of both cab glb files, cab.py, carspec.ts; two door mirrors remain); not yet committed;
- open: the mirror pass costs ~+300-400 ms a frame (595 ms on, ~200-277 off); the refraction/transmission hypothesis did not hold in the last measurement (refraction off: 1110 ms, noisy: other agents on the GPU); the minimal variant proposed: mirror target 128 px, range 50 m, 5 Hz; waits for the owner's go.

Emily (character look under owner's revision, nothing is done to looks): evaluation export of Fab "Modern Female Character" in D:/temp/take37/emily (README.md, facts.md, sheets): 8,948 tris, 1 LOD, 85 bones, 0 morph targets, 1.975 m, hair cards, clothes in the body mesh, 7 clips work in the Ferret viewer; no licence text found; the owner decides if it is used.

Scene 3: see the section above (airfield built, to-do list and open questions); the field agent is stopped.

Still open for the owner: damage rework of the coupe defects (glass patches, soft metal, rear of front-hit cars) if wanted; mirrors go; scene 2 (claw fingers, jacket slivers, beach uniformity, lorry in surf, wire; real man-overboard event); scene 3 questions; helicopter flight and damage model (physics-rotor) not yet commissioned; delete the stray empty folder C:\frames_static.

## Status 2026-11-13 (afternoon): all agent work accepted as is
Owner's order: accept every agent's result as it stands, document everything, log, push, wait for instructions.
- Damaged cars: see art/cars/DAMAGE_STATUS.md (coupe 27/27, hatchback 18, minivan 19, pickup 25, sedan 19, wagon 16 of 27). Remaining variants wait for the owner's word to resume the agents.
- R22 helicopter: delivered (commits 3d2a3f9, 0c25eed, 89322d2); a toy-level model by the owner's judgement, not to be re-run for now; no flight/damage model commissioned.
- Gas station: fire pass (2030b09) and canopy panels (1444aa9) accepted. Owner's fire notes (orange flames of different heights, stronger fire at the pumps, denser/taller smoke, dimmer base under smoke, soot on surfaces) were applied in the pass.
- Scene 3 (airfield, branch scene3 0383fd2) and scene 2 (branch scene2 dd3a6c3): accepted in current form; open questions listed in the earlier scene-3 section.
- Emily: assets/borrowed/emily_fab (Fab "Modern Female Character"); licence text not found, repo is public: owner to decide.
- Cab mirrors (branch mirrors, e0fa130): inside mirror removed; side mirrors minimal (128 px, 5 Hz, 70 m, 150-mesh budget), aimed by the picture centre so the road, not the sky, is shown (frames D:/temp/take37/cab/mir8). Frame-time cost on a quiet machine still unmeasured; owner's wish to reuse an already rendered fragment not yet clarified.
- Character appearance: under full revision by the owner; not touched.
