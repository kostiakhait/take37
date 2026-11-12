# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Builds the coupe:  blender -b -P build_coupe.py -- --out coupe87.glb --lod1 coupe87_lod1.glb --damaged coupe87_damaged.glb"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / '_common'))
import cargen  # noqa: E402
import coupe_geom  # noqa: E402

cargen.run(coupe_geom.G)
