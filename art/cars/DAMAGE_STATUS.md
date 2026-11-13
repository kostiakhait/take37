# Damaged cars: status 2026-11-13 (all agent results accepted as is by the owner)

Kit: art/cars/_common (crash_run.py, crash_table.py, crashkit.py, crashfragile.py, crashglass.py, crash_profiles.py). Blender 4.2.3.
9 kinds x 3 degrees: front, front_corner_L/R, rear, rear_corner_L/R, side_L/R, roll (d1..d3). Each variant: full glb + _lod1.glb.
Per-car folders: art/cars/<car>/damaged/<name>_<kind>_d<N>.glb. Catalogue sheets (outside repo): D:/temp/take37/cars2/katalog_povrezhdeniya/<car>/.

| Car | Full variants | Of 27 | State |
|---|---|---|---|
| coupe | 27 | 27 | complete (pushed earlier) |
| hatchback | 18 | 27 | agent stopped at API limit; 9 missing |
| minivan | 19 | 27 | agent stopped at API limit; 8 missing; scripts minivan_crash_run.py, minivan_profile.py |
| pickup | 25 | 27 | agent stopped at API limit; 2 missing (some sheets partial) |
| sedan | 19 | 27 | agent stopped at API limit; 8 missing; crash_run_sedan.py |
| wagon | 16 | 27 | agent stopped at API limit; 11 missing; crash_wagon.py |

The missing variants are not built; the five agents can be resumed on the owner's word (limit reset 17:20 America/New_York).
Known open item: corner hit types (HitSide) in src/game/view.ts.
