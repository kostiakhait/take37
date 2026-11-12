# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Builds the hatchback:  blender -b -P build_hatchback.py -- --out hatchback87.glb --lod1 hatchback87_lod1.glb --damaged hatchback87_damaged.glb"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / '_common'))
import cargen  # noqa: E402
import hatchback_geom  # noqa: E402

cargen.run(hatchback_geom.G)
