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
| Look back | C (hold) | Y |
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

Prerequisites (all must hold): (1) every asset file of the manifest exists and the cars were accepted after the agent's report; (2) the page loads without errors on the RTX 3050 and the cab frame is readable (the cab interior is lit, the left pillar is not black); (3) the page runs fast enough for the stills to be taken in a few minutes (the terrain and weather agent's frame-rate work); (4) the verdict camera is not blocked.
