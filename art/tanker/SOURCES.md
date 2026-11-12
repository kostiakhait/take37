# Fuel tanker (TAKE 37, scene 1) — sources

Model: a 1980s American conventional tractor (6x4, day cab, 3 m hood) with a 9,000 US gallon aluminium tank semitrailer (tandem rear axle). Fictional operator: "Holloway Fuel & Oil Co.", unit 37.
No real maker, brand, logo or licence plate appears anywhere. The truck's lines are generic of the period; the cab and hood are original shapes.

## Why a tractor-trailer and not a straight truck

A tractor with a tank semitrailer was chosen because a 9,000 gallon load is the standard highway delivery rig of the 1980s; its length (about 14.5 m) and its tank at 3.3 m height make it the
biggest obstacle on a small-town main street, and the trailer can be released at the fifth wheel (node `Trailer` pivots at the kingpin) so the game can jack-knife it, break it away and burn it
separately from the cab. A straight-truck tanker (3,000-4,000 gal) would be less spectacular and could not break apart.

## Borrowed from the shared asset library ("заимствовано из Феррета")

Used as tiling textures (the library's `tex-*` packages, base colour, normal, ORM, resized to 1024 px) on the materials named in the right column.

| Library asset | Used for (material in the glb) |
|---|---|
| `tex-metal-steel` (mat-metal-steel) | `M_alu`, `M_stain`: the tank, domes, rails, ladder, tubes (aluminium), stainless heat shields |
| `tex-metal-black` (mat-metal-black) | `M_frame`: the chassis rails, crossmembers, brackets (black painted steel) |
| `tex-metal-rust` (mat-metal-rust) | `M_rust` (small parts) |
| `tex-leather-brown` (mat-leather-brown) | `M_seat`: the vinyl seats, armrests |
| `tex-gray-fabric1` (mat-gray-fabric1) | `M_fabric`: door cards, back wall |
| `tex-cloth-grey` (mat-cloth-grey) | `M_cloth`: floor mat |
| `tex-dust` (mat-dust) | base of the dirt overlay `M_grime` (road dust on the tank flank, doors) |
| `tex-soil` (mat-soil) | base of the mud overlay `M_grime_mud` (mud behind the tandem) |

Code reused: `carkit.py` (tyres with tread and raised lettering, hub nuts, valve stem, lamp builders, seat cushions) is a copy of the vehicle kit from the library's car examples, trimmed to what the tanker uses
(the tread and tyre functions were extended with a sample-count argument). The mesh-builder idea (bmesh lofts, exact booleans, ray-cast placing, Cycles preview on the RTX card) follows the same example scripts.

## Made for the game

Everything else: all geometry; the livery sheet `decals.png` (company name, DOT flammable placards, 1203 panels, signs, plates, data plate, stripes), `tape.png` (red/white conspicuity tape),
the grime alpha overlays `grime.png`, `grime_mud.png` (generated with numpy over the library soil/dust), all colours of paint, glass, rubber, chrome. Scripts: `prep_textures.py` (textures and decals),
`dims.py`, `tkit.py`, `parts.py`, `carkit.py`, `st_wheels.py`, `st_chassis.py`, `st_cab.py`, `st_interior.py`, `st_tank.py`, `st_fittings.py`, `st_lamps.py`, `st_details.py`, `export.py`, `build_tanker.py`, `preview.py`.

## Shape and dimension references

No photograph, drawing or blueprint was copied or traced. The dimensions come from public US federal rules and well-known standard sizes, which are facts and not copyrighted:

- Overall width limit 8.5 ft (2.6 m), height limit 13.5 ft (4.11 m), kingpin and fifth-wheel geometry (SAE J701, 2 in kingpin, 36 in setting), 49 CFR Part 393 (lamps, reflectors, conspicuity tape DOT-C2 red/white 50 mm) —
  public domain, US federal regulation, https://www.ecfr.gov/current/title-49/subtitle-B/chapter-III/subchapter-B/part-393
- Cargo tank form (oval section, dished heads, five compartments, manhole domes with rollover protection, bottom outlets with internal emergency valves, API 4 in adapters), 49 CFR 178.345 (DOT 406) and 178.346/178.348 —
  public domain, https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-C/part-178
- Hazard placard (class 3 flammable liquid, red, white flame, black number; 273 mm diamond) and the orange panel with ID number 1203 (gasoline): 49 CFR 172.519, 172.542, 172.332 —
  public domain, https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-C/part-172
- Tyre 11R22.5 (section 285 mm, rim 22.5 in), a 10-stud hub-piloted wheel on a 285.75 mm bolt circle (ISO 4107 / Tire and Rim Association): public standards data.

These regulations were used from the author's knowledge of them; the pages above were not downloaded during the build.

## Not done / limits

See the build report.
