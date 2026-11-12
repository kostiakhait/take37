# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Dimensions of the rig, metres, the model's frame (origin on the ground at the middle of the tractor's wheelbase, nose +X, up +Z, left +Y)."""
R_TYRE, R_RIM, W_TYRE = 0.520, 0.2858, 0.285          # 11R22.5
ZC = 0.515                                            # wheel centre height
DUAL = 0.335                                          # dual spacing, centre to centre
STEER_X, D1_X, D2_X = 2.20, -1.515, -2.885            # steer axle, drive tandem (1.37 m spacing)
STEER_Y = 1.02                                        # steer wheel centre
DRIVE_Y = 0.92                                        # centre of the dual pair
KINGPIN_X = -1.95
T1_X, T2_X = -9.315, -10.685                          # trailer tandem (1.37 m spacing, centre at -10.0)
