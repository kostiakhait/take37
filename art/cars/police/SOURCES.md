# Police sedan 1987 (Ford LTD Crown Victoria, P72 police package): the cab

Model: `assets/borrowed/crown_victoria_cpd87.glb` (and `_lod1.glb`), заимствовано из библиотек (Ferret library package `mdl-crown-victoria-cpd87`, source `D:\REPO\ferret\examples\crown-victoria`).
The exterior, the glass, the doors, the roof rack, the wheels and the underbody are the library's, unchanged. The cab (everything inside the glass) was reworked for the game (2026-11-12): the sources and build here (`blender/`, a copy of the library's build scripts with `cab.py` and `interior_only.py` added).

## What the real car's cab had (and where it is written)

| Fact | Source |
|---|---|
| The police package: speedometer calibrated to 140 mph (a standard car 85 mph), "certified calibration" on the face; heavy-duty interior materials; provisions for extra lights and sirens | Wikipedia, Ford LTD Crown Victoria (https://en.wikipedia.org/wiki/Ford_LTD_Crown_Victoria); Barn Finds, "Real-Deal Police Package: 1987 Ford LTD Crown Victoria" (https://barnfinds.com/real-deal-police-package-1987-ford-ltd-crown-victoria/); Barn Finds, "Police Package: 1985 Ford LTD SSP" (https://barnfinds.com/police-package-1985-ford-ltd-ssp/) |
| Speedometer with both mph and km/h scales (reader comment on the 1987 car's listing photos); no tachometer on the police cars (reader comment, 1985 SSP) | the two Barn Finds pages above |
| Holes in the dash and in the transmission hump where equipment was bolted; trunk release low on the driver's side of the dash; column shifter | Barn Finds, 1985 LTD SSP (article and comments) |
| A non-working spotlight left in a 1987 Sierra Vista (AZ) patrol car: the A-pillar spotlight with its handle inside the cab | Barn Finds, 1987 Police Package |
| Front bench in ribbed blue-grey cloth, split with a folding centre armrest (down), lap and shoulder belt with a buckle on the cushion's inner side, dark blue steering wheel with a large rectangular horn pad and two spokes | Barn Finds photograph "1987 Crown Vic Interior" (the 1987 police car above, https://barnfinds.com/wp-content/uploads/2026/09/1987-Crown-Vic-Interior-e1788347152118-630x390.png) |
| Dash layout of the 1983-87 cars: a rectangular cluster with a hood on the driver's side, a bank of vents beside it, AM/FM radio and the heater controls in the centre stack, glove box on the right; door panel with a long pull strap, an armrest with a chrome switch plate, a chrome latch; column stalks; two-spoke wheel; the horn in the wheel's hub from 1985 | Curbside Classic, "1987 Ford LTD Crown Victoria" photographs (https://www.curbsideclassic.com/curbside-classics-american/curbside-classic-1987-ford-ltd-crown-victoria-helloooooooo-kitty, the photo `1987-Ford-LTD-Crown-Victoria-g.jpg`); Wikipedia (horn on the hub in 1985) |
| Fleet trim "S" of 1987: vinyl bench, manual windows, AM radio; AC and electronic clock standard except on fleet cars; the LX police cars had cloth seats and carpet | Wikipedia; Barn Finds (the 1987 Sierra Vista car: power windows, AM/FM, no tint, no AC compressor) |
| Police radio installation of the period: the radio's control head and the siren / lights console on a welded steel rack over the transmission hump, braced to the dash; the siren console with a slide VOL control, a NOR-DIM switch lighting the switches through a blue lens, a blue pilot light on its upper edge; a hand microphone grey with a black grille (or all black) with a coiled cord; a scanner under the dash to the right of the control head (California Highway Patrol, 1977-1988) | WB6NVH, "CHP Radio Systems" (https://wb6nvh.com/CHP/CHP3a.htm) |
| Sizes: the model's own (wheelbase 114.3 in, length 211.0 in, width 77.5 in, height 55.6 in) | the library model's README |

## What is NOT modelled, because no source for this car was found

A shotgun rack, a prisoner partition, a radar unit, a mobile data terminal (not in 1987), a particular radio make or its lettering. The radio control head, the siren console, the
microphone and the scanner are plain units without lettering, laid out as the CHP page describes (a rack on the hump, the scanner under the dash to the right); the car's own department
(the livery is Chicago's) may have laid it out differently: no source for that was found.

## What was chosen without a source

The colour of the vinyl (blue, following the 1987 patrol car's photo), the cluster's layout (a ribbon speedometer between a fuel and a temperature gauge: the library's drawing), the exact
positions of the vents and knobs (from the Curbside Classic photograph, approximately), the controller's switch count, the eye position, the column rake.

## Borrowed library materials (D:\REPO\ferret\lib\ferret-assets)

- rug: carpet; gray-fabric1: headliner; cloth-grey: seat cloth (tinted blue-grey).

## Build

`blender -b -t 8 -P blender/build_crownvic.py -- --out ... --lod1 ... --blend base.blend` (the body: slow, exact boolean cuts), then `blender -b base.blend -P blender/interior_only.py -- --out ... --render dir` for the cab only. `gauges.py` draws the cluster's face.

## Nodes

Unchanged: `CrownVic87`, `Body`, `Glass`, `Trim`, `Door_*`, `Wheel_*`, `Ends`, `Lamps_*`, `Rack`, `Speaker`, `Beacon_*`, `Underbody`, `Interior`. New under the root: `Dash`, `SteeringWheel` (origin at the hub on the column axis, axis in `src/game/carspec.ts` POLICE_CAB), `Equipment` (radio rack, siren console, microphone, scanner), `PillarTrim` (A, B, C pillar covers, built between the glass edges). New under each door node: `DoorCard_FL/FR/RL/RR` (pull strap, switch plate, bolster, carpet band), so they open and fall off with the door.
