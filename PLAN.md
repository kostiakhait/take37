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
2. **The secret base (evacuation under fire).** Set on a beach, moles, ships and aircraft taken from the Ferret sample set for a beach evacuation (borrowed models: coast, mole(s), vessels, aircraft, soldiers; declared "заимствовано из Феррета"), but the purpose is different. Story: the villain's secret base is on the shore; the whole roadstead is crowded with ships crewed by his henchmen. He keeps Arnold and Emily prisoner in cages on the pier. Task: from the beach, run under fire to the end of the mole, push the cages onto a suitable steamer and sail away on it. A scene full of shootouts: ships sink and explode, the henchmen "die". Score: mostly by the number of ships spectacularly destroyed, to a lesser degree by the number of henchmen "killed". Open: controls on foot and on the ship, cage-pushing mechanic, take-end conditions. Weapons: the stuntman has a submachine gun (henchmen, small boats) and a bazooka (ships, fuel, boilers). The "suitable steamer" is the library paddle steamer Princess Elizabeth (1927, package mdl-princess-elizabeth, 5.2 MB): it must be detailed heavily, exterior only (hull plating, rivets, paddle boxes and wheels, funnel, railings, lifeboats, deck fittings, rigging, windows, paint wear); the detailed version is a modification of a borrowed asset and is logged. Two separate cages (Arnold, Emily): BOTH must be pushed onto the steamer, otherwise the scene is not counted. The paddle steamer never sinks (it is the film's ship, it must survive); only the villain's ships sink and explode. A cage that falls into the water spoils the take.
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
