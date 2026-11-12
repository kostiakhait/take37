# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Builds the mid-size pickup:  blender -b -P build_pickup.py -- --out pickup87.glb --lod1 pickup87_lod1.glb --damaged pickup87_damaged.glb"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / '_common'))
import cargen  # noqa: E402
import pickup_geom  # noqa: E402

cargen.run(pickup_geom.G)
