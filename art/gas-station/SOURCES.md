# Gas station: sources

Built by `build_gas.py` (Blender 4.2, headless) with the helpers in `art/street/` (`kitlib.py`); textures drawn by `gas_tex.py`. No photographs, no external models, no real brand:
the station is the fictional brand VALDOR (a "V" in a ring, red, white and yellow house colours); every sign, price and label is original.

## Borrowed from the asset library (заимствовано из Феррета)

Tinted in `art/street/textures_prep.py`, maps themselves unedited:

| Library texture | Used for |
|---|---|
| tex-concrete-block, tex-concrete-312 | forecourt slab, island kerbs, perimeter kerb, column plinths, stele foot |
| tex-brick-clay-new-material-sphere-2 (buff firing), tex-brick-clay-old | shop and car-wash walls |
| tex-metal-steel | painted pump cabinets, canopy fascia, columns, price pole, bare steel parts (tinted, non-metal where painted) |
| tex-metal-black | pump bases, door frames, hose holsters, grates |
| tex-stucko-wa1, tex-column-plaster-311 | canopy soffit, trim |
| tex-wood-dark-brown, tex-wood-pine | counter, bench |
| tex-ground-grass | strip behind the lot |

## Made for the game

- `gas_tex.py` draws: the pump face (seven-segment SALE / GALLONS / PRICE PER GALLON display, grade buttons, stickers), the lit pump header with the VALDOR logo, the price stele
  (REGULAR .849 / UNLEADED .899 / SUPER .999 style rows at 1987 prices), the shop fascia, a 4x4 sticker atlas (no smoking, pay first, cold drinks, packaged ice, open, 24 hours, self serve,
  rest rooms, air, water, hot coffee, logo, drive slow, enter, no loitering, lotto), the oil-can label. Typeface in the textures: DejaVu (free licence).
- All geometry: canopy with deep fascia, soffit grid, fluorescent troughs, downspouts; guarded columns; six pumps with hoses and nozzles; islands with bollards; stele; shop with
  stocked gondolas, wall coolers, counter; ice chest, propane cage, oil rack, tyres, bins, news boxes, lamps, vents, signs; drains, hatches, markings; forecourt decals (stains, cracks,
  manholes, from the street decal atlas) and the vertex-tone weathering.
