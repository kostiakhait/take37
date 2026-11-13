# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""R22 Beta II numbers. Sources: Robinson Maintenance Manual ch.16 Fig. 16-2 (MM), EASA TCDS R22 (TCDS), NAC spec sheet (NAC); the rest is read off photographs (PH) and marked."""
XN = -1.60            # x of the nose tip (MM: skid toe is 1.65 m ahead of the mast axis, 259 in fuselage length to the tail rotor disc end)
MAST_X = 0.0
ROTOR_R = 3.835       # MM 151 in
ROTOR_CHORD = 0.18    # PH/brief (7.2 in blade chord)
HUB_Z = 2.68          # MM overall height 2.72 m = top of the hub head
TAIL_ROTOR_D = 1.067  # MM/TCDS 42 in
SKID_TRACK = 1.93     # MM 76 in (outer to outer)
CABIN_W = 1.12        # MM 44 in
CABIN_TOP = 1.75      # MM 69 in
SKID_LEN = 3.00       # PH (toe to heel, from skid vs cabin comparison)
BOOM_END_X = 4.55     # x of the tail rotor hub axis (MM: rotor disc spans x 3.9..5.0 -> overall 8.76 m with the front blade tip at -3.835)
STAB_SPAN = 0.87      # MM 34 in
EMPTY_KG = 399        # NAC
REG = 'F-GT37'        # registration letters (a parameter)
PAINT_MAIN = (0.93, 0.93, 0.90, 1)      # livery colours are material factors: change here or in the game
PAINT_ACCENT = (0.05, 0.12, 0.33, 1)
PAINT_TRIM = (0.74, 0.08, 0.06, 1)      # the red/white end plates and tail guard stripes
