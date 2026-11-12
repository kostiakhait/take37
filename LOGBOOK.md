# Logbook — TAKE 37

Every operation made to create the game: local time and description.

## Asset origin declarations

- Assets of Ferret and of its examples are declared as **«заимствовано из Феррета»**.
- Assets taken from outside libraries are declared as **«ЗАИМСТВОВАНЫ ИЗ БИБЛИОТЕК»**.
- Any modification of an asset is logged as its own entry.

## Entries

| Time (local) | Operation |
|---|---|
| 2026-11-12 00:00 | Development opened. |
| 2026-11-12 00:00 | Created the public GitHub repository `take37` under the account kostiakhait. |
| 2026-11-12 00:01 | Wrote the plan of the game (PLAN.md) and started the logbook (LOGBOOK.md). |
| 2026-11-12 00:02 | Took the 1987 Corvette C4 convertible (Vincent's car) and the 1987 police sedan (Matthew's car) from the library into assets/borrowed (4 files: full and reduced detail of each). Origin: заимствовано из Феррета. |
| 2026-11-12 00:02 | Decided to take every usable material and texture from the library; the rest of the scene-1 models are drawn for the game. |
| 2026-11-12 00:02 | Launched three modelling tasks for scene 1: the street kit with the gas station, the fuel tanker, and the civilian traffic cars. |
| 2026-11-12 00:08 | Started the characters. Chose to build all six on the library's character modules: a preset face and body for each, strand hair, and clothes sewn to the body. Started the first three face-and-body exports (Edward, Matthew, Emily) at lowered priority. |
| 2026-11-12 06:36 | The work stood still from about 01:50 to 06:30 because of the account's request limit; the modelling tasks stopped and were resumed at 06:34. |
| 2026-11-12 06:36 | Face-and-body exports of Edward, Emily and Arnold finished. Matthew's export wrote nothing twice because the script closed before the writing ended; fixed the script to wait for it, restarted Matthew and started the director's export. |
| 2026-11-12 06:36 | Wrote the character build script (tools/build_character.mjs) and the outfits (tools/outfits.mjs): strand hair and beard, clothes sewn and draped on the body. First builds of Edward and Vincent (Vincent on the library's old-man face). Reviewed the renders: Edward's hair is not dreadlocks and Vincent's robe hem is crumpled; both rebuilt. |
| 2026-11-12 00:02-01:09 | Street and gas station task (modelling agent): inspected the tools and library; unpacked 23 library textures and made tinted variants plus asphalt, sidewalk, clapboard, decals, road signs, shop boards, interiors and leaves (library textures: заимствовано из Феррета; the rest drawn for the game); wrote the mesh builder with vertex-tone weathering; built 31 prop kinds as full and reduced pairs, 12 building designs and the road modules; assembled the 680 m main street with 9 cross streets closed by crew barriers; built the gas station; retuned materials. |
| 2026-11-12 06:34-07:10 | Resumed after the request-limit pause; exported gas_station.glb (06:34), street_kit.glb (06:43), street_level.glb and street_colliders.glb (07:10). |
| 2026-11-12 07:12 | Reviewed the street and gas station renders: the street reads well from the car's eye height; the gas station is weak (plain white canopy, small boxy pumps, no readable prices) and needs a polish pass. Street and station accepted as the working version. |
