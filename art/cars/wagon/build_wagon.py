# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Builds the wagon:  blender -b -P build_wagon.py -- --out wagon87.glb --lod1 wagon87_lod1.glb --damaged wagon87_damaged.glb"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / '_common'))
import cargen  # noqa: E402
import wagon_geom  # noqa: E402

cargen.run(wagon_geom.G)
