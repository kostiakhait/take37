# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Export the tanker to glb (Y up, nose +X): the full model and a reduced LOD1. Called from build_tanker.py --stage export.

LOD1 keeps every node and every pivot; meshes above 600 faces are decimated (collapse, 0.30) with the UV seams kept, rivets, welds and bolt heads thus disappear first.
"""
import pathlib

import bpy

import tkit as T


def stats():
    out = {}
    tot = 0
    for ob in bpy.data.objects:
        if ob.type == 'MESH':
            d = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            me = d.to_mesh()
            tris = sum(len(p.vertices) - 2 for p in me.polygons)
            d.to_mesh_clear()
            out[ob.name] = tris
            tot += tris
    return out, tot


def write(path, lod=None):
    bpy.ops.object.select_all(action='DESELECT')
    obs = [o for o in bpy.data.objects if o.name == 'Tanker' or (o.parent is not None)]
    mods = []
    if lod:
        for ob in obs:
            if ob.type == 'MESH' and len(ob.data.polygons) > 600:
                md = ob.modifiers.new('lod', 'DECIMATE')
                md.ratio = lod
                md.use_collapse_triangulate = False
                mods.append((ob, md))
    for ob in obs:
        ob.select_set(True)
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True, export_apply=True, export_image_format='WEBP',
                              export_materials='EXPORT', export_extras=True, export_cameras=False, export_lights=False, export_texcoords=True, export_normals=True)
    st, tot = stats()
    for ob, md in mods:
        ob.modifiers.remove(md)
    T.log('wrote', path, 'triangles', tot, 'bytes', pathlib.Path(path).stat().st_size)
    return tot


def run(out, lod1):
    write(out)
    write(lod1, lod=0.30)
