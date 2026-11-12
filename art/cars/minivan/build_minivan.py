# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Builds the minivan:  blender -b -P build_minivan.py -- --out minivan87.glb --lod1 minivan87_lod1.glb --damaged minivan87_damaged.glb"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / '_common'))
import cargen  # noqa: E402
import minivan_geom  # noqa: E402

cargen.run(minivan_geom.G)
