# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Builds the mid-size sedan:  blender -b -P build_sedan.py -- --out sedan87.glb --lod1 sedan87_lod1.glb --damaged sedan87_damaged.glb"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / '_common'))
import cargen  # noqa: E402
import sedan_geom  # noqa: E402

cargen.run(sedan_geom.G)
