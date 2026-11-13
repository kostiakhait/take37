# Police sedan 1987 (Ford LTD Crown Victoria, P72 police package): the cab

Model: `assets/borrowed/crown_victoria_cpd87.glb` (and `_lod1.glb`), заимствовано из библиотек (library package `mdl-crown-victoria-cpd87`, source `D:\REPO\ferret\examples\crown-victoria`).
The exterior, the glass, the roof rack, the wheels and the underbody are the library's. Changed for the game (2026-11-12): the cab (everything inside the glass), the front doors' seal band along the A-pillars (removed, see Nodes) and the outside mirrors (replaced). Sources and build here: `blender/` (a copy of the library's build scripts with `cab.py` and `interior_only.py` added), `gauges.py`.

## The layout: the owner's reference photographs (2026-11-12)

The cab is laid out after the owner's reference photographs of a 1983-87 LTD Crown Victoria's cab (passed by the coordinator, described in words):

| Part | As in the reference |
|---|---|
| Dash top | a soft dark blue pad with a rounded edge over the instruments |
| Dash face | across the whole width a dark walnut-grain strip (red-brown with grain; drawn procedurally by `gauges.py`, not a photograph) with thin bright edging |
| Left of the wheel | a square vent with horizontal ribs |
| Before the driver | a wide horizontal ribbon speedometer (scale 5 to 85 MPH, km/h under it, a needle, the PRNDL indicator under the scale) under glass in a black frame |
| Right of the cluster | vents; in the centre the radio and the climate block in a wooden console; before the passenger a long wooden panel and a vent at the end |
| Below | dark blue plastic panels, dark blue carpet |
| Wheel | large, thin dark blue rim, four spokes (the two lower ones down and out with bright inserts), a big rectangular dark blue pad with an oval emblem; the column with the selector lever (bright, to the right and up, with a ball) and the stalk on the left |
| Seats | dark blue velour bench with lengthwise stitching |
| Doors | blue trim with a horizontal wooden insert, a bright handle |
| A-pillars | thin, about 6-8 cm seen from the seat, covered in dark blue, sloping along the windscreen |
| Inside mirror | a small rounded rectangle about 25 x 6 cm on a stalk to the top of the windscreen at the middle, a dark plastic frame, flat glass |
| Outside mirrors | outside each front door at the foot of the A-pillar, rectangular, a chrome housing on a triangular base on the door, about 15 x 10 cm |
| Hood | the light body's hood seen under the windscreen |

## What the real police car had (and where it is written)

| Fact | Source |
|---|---|
| The police package: speedometer calibrated to 140 mph (a standard car 85 mph), "certified calibration" on the face; heavy-duty interior materials; provisions for extra lights and sirens | Wikipedia, Ford LTD Crown Victoria (https://en.wikipedia.org/wiki/Ford_LTD_Crown_Victoria); Barn Finds, "Real-Deal Police Package: 1987 Ford LTD Crown Victoria" (https://barnfinds.com/real-deal-police-package-1987-ford-ltd-crown-victoria/); Barn Finds, "Police Package: 1985 Ford LTD SSP" (https://barnfinds.com/police-package-1985-ford-ltd-ssp/) |
| Speedometer with mph and km/h scales; no tachometer on the police cars | the two Barn Finds pages above (reader comments) |
| Holes in the dash and in the transmission hump where equipment was bolted; trunk release low on the driver's side of the dash; column shifter | Barn Finds, 1985 LTD SSP (article and comments) |
| A spotlight on the driver's A-pillar of a 1987 patrol car, its handle inside the cab | Barn Finds, 1987 Police Package |
| Front bench, split, folding centre armrest, lap and shoulder belts; a dark blue wheel with a large rectangular pad | Barn Finds photograph of the 1987 police car's cab |
| The horn moved to the wheel's hub in 1985 | Wikipedia |
| Police radio installation of the period: the radio's control head and the siren / lights console on a steel rack over the transmission hump, braced to the dash; a blue pilot light on the siren console; a grey hand microphone with a black grille on a coiled cord; a scanner under the dash to the right (California Highway Patrol, 1977-1988) | WB6NVH, "CHP Radio Systems" (https://wb6nvh.com/CHP/CHP3a.htm) |
| Sizes: wheelbase 114.3 in, length 211.0 in, width 77.5 in, height 55.6 in | the library model's README |

## Where the reference and the police sources differ (open)

- Speedometer scale: the reference shows 5-85 MPH (a civilian car); the police package's certified speedometer read to 140 mph. The cluster follows the reference; `python -I gauges.py --top 140` draws the police scale.
- Walnut trim: on the reference (a civilian car); no source says whether the fleet/police trim had it.
- The spotlight (library model, on the driver's A-pillar outside) stays; the left outside mirror sits low and out on the door so that the lamp does not cover it.

## What is NOT modelled, because no source was found

A shotgun rack, a prisoner partition, a radar unit, a radio make or its lettering (the radio units are plain, without lettering).

## What was chosen without a source

The exact sizes and positions of vents, knobs and radio buttons; the eye position (from the headroom: the eye 17 cm under the headliner, 15 cm ahead of the head restraint's face); the column rake (25 degrees, wheel plane 25 degrees from the vertical), the hub 0.45 m ahead of and 0.32 m below the eye; the aim of the mirrors (each shows the driver the road straight behind, along the car's side for the outside ones).

## Borrowed library materials (D:\REPO\ferret\lib\ferret-assets)

- rug: carpet (dark blue); gray-fabric1: headliner (blue-grey); cloth-grey: seat velour (dark blue).

## Build

`blender -b -t 8 -P blender/build_crownvic.py -- --out ... --lod1 ... --blend base.blend` (the body: slow, exact boolean cuts), then `blender -b base.blend -P blender/interior_only.py -- --out ... --lod1 ... --render dir` for the cab only. `python -I gauges.py` draws the cluster's face and the walnut.

## Nodes

Unchanged names: `CrownVic87`, `Body`, `Glass`, `Trim`, `Door_*` (and `Door_*_shell`, `Glass_*`, `Trim_*`), `Wheel_*`, `Ends`, `Lamps_*`, `Rack`, `Speaker`, `Beacon_*`, `Underbody`, `Interior`.
Changed: `Door_FL_shell`, `Door_FR_shell` lose the seal faces lying in the windscreen's plane along the A-pillar (a by-product of the door split, a 10-16 cm slab seen from the seat); `Trim_FL`, `Trim_FR` lose the library's round-headed outside mirrors.
New under the root: `Dash`, `SteeringWheel` (origin at the hub on the column axis; hub, axis, radius in `src/game/carspec.ts` POLICE_CAB), `Equipment`, `PillarTrim`, `Mirror_Inner`, `Mirror_Inner_Glass`.
New under the front doors: `Mirror_L`, `Mirror_L_Glass` (Door_FL), `Mirror_R`, `Mirror_R_Glass` (Door_FR). The mirror glass nodes are one flat face each, the normal out of the glass, the node's origin at the glass's centre.
New under each door: `DoorCard_FL/FR/RL/RR`.
