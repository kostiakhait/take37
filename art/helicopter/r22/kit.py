# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Geometry and material kit for the Robinson R22 build (Blender 4.2, headless).

Build frame: metres, the NOSE POINTS TO -X, +Y is the aircraft's RIGHT, +Z up, origin on the ground under the main rotor axis; zones.finish() turns the content 180 deg about Z so the glTF export
(Y up) has the nose on +X and the left on -Z, like the cars and the airwar aircraft.
`DET` (1.0 for lod0, 0.5 for lod1) scales every ring/segment count so lod1 is a lighter *build* of the same model (same nodes, same names), not a decimation of lod0.
"""
import math
import os
import struct
import zlib
import bpy
import bmesh
from mathutils import Vector, Matrix
import numpy as np

DET = 1.0
SEED = 37
TEXDIR = 'D:/temp/take37/heli/tex'


def seg(n, lo=3):
    """a segment count scaled by the detail level"""
    return max(lo, int(round(n * DET)))


# ------------------------------------------------------------------ splines

def crom(pts, t):
    """Catmull-Rom through pts [(s, v)...] at s=t (v scalar or tuple); clamps outside"""
    xs = [p[0] for p in pts]
    if t <= xs[0]:
        return pts[0][1]
    if t >= xs[-1]:
        return pts[-1][1]
    i = max(k for k in range(len(xs) - 1) if xs[k] <= t)

    def val(k):
        k = min(max(k, 0), len(pts) - 1)
        return np.array(pts[k][1], dtype=float)
    p0, p1, p2, p3 = val(i - 1), val(i), val(i + 1), val(i + 2)
    u = (t - xs[i]) / (xs[i + 1] - xs[i])
    h = xs[i + 1] - xs[i]
    l0 = xs[i] - xs[max(i - 1, 0)] if i > 0 else h
    l1 = xs[min(i + 2, len(xs) - 1)] - xs[i + 1] if i + 2 < len(xs) else h
    m1 = (p2 - p0) / (h + l0) * h if i > 0 else (p2 - p1)
    m2 = (p3 - p1) / (h + l1) * h if i + 2 < len(xs) else (p2 - p1)
    u2, u3 = u * u, u * u * u
    r = (2 * u3 - 3 * u2 + 1) * p1 + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * p2 + (u3 - u2) * m2
    return float(r) if r.ndim == 0 else r


def sgnpow(x, p):
    return math.copysign(abs(x) ** p, x)


# ------------------------------------------------------------------ materials

MATS = {}


def mat(name, base=(0.8, 0.8, 0.8, 1), metal=0.0, rough=0.5, emit=None, emit_strength=1.0, alpha=None, tex=None, normal=None, spec=None, coat=0.0):
    """Principled PBR material; `base` is the colour factor (livery colours live here), `tex` an image multiplied into it."""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True       # single-sided: the 3 mm shell's inner faces must not show through the paint (z-fighting at a long far plane)
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    bsdf.inputs['Base Color'].default_value = base
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    if spec is not None:
        bsdf.inputs['Specular IOR Level'].default_value = spec
    if coat:
        bsdf.inputs['Coat Weight'].default_value = coat
        bsdf.inputs['Coat Roughness'].default_value = 0.05
    if emit is not None:
        bsdf.inputs['Emission Color'].default_value = (*emit, 1)
        bsdf.inputs['Emission Strength'].default_value = emit_strength
    if alpha is not None:
        bsdf.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
        m.use_backface_culling = False
    if tex is not None:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = tex
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1.0
        mix.inputs[6].default_value = base
        nt.links.new(t.outputs['Color'], mix.inputs[7])
        nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
        if alpha is not None and alpha >= 1.0:
            nt.links.new(t.outputs['Alpha'], bsdf.inputs['Alpha'])
    if normal is not None:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = normal
        t.image.colorspace_settings.name = 'Non-Color'
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = 1.0
        nt.links.new(t.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    MATS[name] = m
    return m


def vcol_mult(m):
    """multiply the Color attribute (soot/dirt) into the base colour so renders show it; glTF carries COLOR_0 and the game multiplies it as the cars' do"""
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    src = bsdf.inputs['Base Color']
    attr = nt.nodes.new('ShaderNodeVertexColor')
    attr.layer_name = 'Color'
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1.0
    if src.links:
        l = src.links[0]
        fr = l.from_socket
        nt.links.remove(l)
        nt.links.new(fr, mix.inputs[6])
    else:
        mix.inputs[6].default_value = src.default_value
    nt.links.new(attr.outputs['Color'], mix.inputs[7])
    nt.links.new(mix.outputs[2], src)


def write_png(path, a):
    """RGBA uint8 [h, w, 4] -> PNG without PIL (Blender's Python has none); rows are written top first"""
    h, w = a.shape[:2]
    raw = b''.join(b'\x00' + a[y].tobytes() for y in range(h))

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def image_from_array(name, arr, srgb=True):
    """arr float32 [h, w, 4] 0..1 (row 0 = top of the picture) -> PNG under TEXDIR -> Blender image (packed, so the .blend and the glb keep it)"""
    os.makedirs(TEXDIR, exist_ok=True)
    path = '%s/%s_%d.png' % (TEXDIR, name, int(DET * 10))
    write_png(path, (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8))
    im = bpy.data.images.load(path)
    im.name = name
    im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
    im.alpha_mode = 'STRAIGHT'
    im.pack()
    return im


def height_to_normal(hgt, strength=2.0):
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * strength
    gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * strength
    nz = np.ones_like(hgt)
    ln = np.sqrt(gx * gx + gy * gy + nz * nz)
    return np.stack([-gx / ln * 0.5 + 0.5, gy / ln * 0.5 + 0.5, nz / ln * 0.5 + 0.5, np.ones_like(hgt)], -1)


def noise(w, h, scale, seed):
    r = np.random.RandomState(seed)
    g = r.rand(h // scale + 2, w // scale + 2)
    yy, xx = np.mgrid[0:h, 0:w]
    fy, fx = yy / scale, xx / scale
    iy, ix = fy.astype(int), fx.astype(int)
    ty, tx = fy - iy, fx - ix
    ty, tx = ty * ty * (3 - 2 * ty), tx * tx * (3 - 2 * tx)
    a = g[iy, ix] * (1 - tx) + g[iy, ix + 1] * tx
    b = g[iy + 1, ix] * (1 - tx) + g[iy + 1, ix + 1] * tx
    return a * (1 - ty) + b * ty


# ------------------------------------------------------------------ objects

def link(ob, parent=None, col=None):
    (col or bpy.context.scene.collection).objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def from_bm(name, bm, mats=(), parent=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    link(ob, parent)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def empty(name, loc=(0, 0, 0), parent=None, kind='PLAIN_AXES', size=0.05, **props):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind
    e.empty_display_size = size
    e.location = loc
    link(e, parent)
    for k, v in props.items():
        e[k] = v
    return e


def place(ob, pivot):
    """the geometry was built relative to the pivot: just put the object origin there"""
    ob.location = Vector(pivot)


def reparent(ob, parent):
    """keep the world transform"""
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = parent
    bpy.context.view_layer.update()
    ob.matrix_parent_inverse = parent.matrix_world.inverted()
    ob.matrix_world = mw


def bm_box(bm, c, size, mat_idx=0):
    sx, sy, sz = size
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = Vector((v.co.x * sx + c[0], v.co.y * sy + c[1], v.co.z * sz + c[2]))
    for f in set(f for v in r['verts'] for f in v.link_faces):
        f.material_index = mat_idx
    return r['verts']


def bm_cyl(bm, p0, p1, r0, r1=None, n=16, caps=True, mat_idx=0):
    """cylinder/cone between two points"""
    p0, p1 = Vector(p0), Vector(p1)
    r1 = r0 if r1 is None else r1
    n = seg(n, 6)
    q = (p1 - p0).to_track_quat('Z', 'Y')
    ring0, ring1 = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = q @ Vector((math.cos(a), math.sin(a), 0))
        ring0.append(bm.verts.new(p0 + d * r0))
        ring1.append(bm.verts.new(p1 + d * r1))
    fs = []
    for i in range(n):
        j = (i + 1) % n
        fs.append(bm.faces.new((ring0[i], ring0[j], ring1[j], ring1[i])))
    if caps:
        fs.append(bm.faces.new(ring0[::-1]))
        fs.append(bm.faces.new(ring1))
    for f in fs:
        f.material_index = mat_idx
        f.smooth = True
    return fs


def bm_tube(bm, pts, r, n=10, mat_idx=0, r_end=None):
    """a bent tube along a polyline pts (sweeps circles, mitre by averaging directions)"""
    n = seg(n, 6)
    pts = [Vector(p) for p in pts]
    rings = []
    for k, p in enumerate(pts):
        if k == 0:
            d = pts[1] - p
        elif k == len(pts) - 1:
            d = p - pts[k - 1]
        else:
            d = (pts[k + 1] - p).normalized() + (p - pts[k - 1]).normalized()
        d.normalize()
        q = d.to_track_quat('Z', 'Y')
        rr = r if r_end is None else r + (r_end - r) * k / (len(pts) - 1)
        rings.append([bm.verts.new(p + q @ Vector((math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n), 0)) * rr) for i in range(n)])
    fs = []
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            fs.append(bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i])))
    fs.append(bm.faces.new(rings[0][::-1]))
    fs.append(bm.faces.new(rings[-1]))
    for f in fs:
        f.material_index = mat_idx
        f.smooth = True
    return fs


def bm_loft(bm, rings, cap_end=False, mat_idx=0):
    """rings: list of lists of Vectors with the same count; returns the face grid and the vertex grid"""
    vr = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    grid = []
    for k in range(len(vr) - 1):
        row = []
        for j in range(n):
            jj = (j + 1) % n
            f = bm.faces.new((vr[k][j], vr[k + 1][j], vr[k + 1][jj], vr[k][jj]))
            f.material_index = mat_idx
            row.append(f)
        grid.append(row)
    if cap_end:
        f = bm.faces.new(vr[-1][::-1])
        f.material_index = mat_idx
    return grid, vr


def recalc(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


def planar_uv(ob, axes=(0, 1), scale=1.0, off=(0, 0), layer='UVMap'):
    me = ob.data
    uv = me.uv_layers.get(layer) or me.uv_layers.new(name=layer)
    for p in me.polygons:
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co[axes[0]] + off[0]) * scale, (co[axes[1]] + off[1]) * scale)


def box_uv(ob, scale=1.0):
    """box projection per face by the dominant normal axis"""
    me = ob.data
    uv = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda a: abs(n[a]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co[a] * scale, co[b] * scale)


def ensure_attr(ob):
    me = ob.data
    if me.color_attributes.get('Color') is None:
        ca = me.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
        for d in ca.data:
            d.color = (1, 1, 1, 1)


def tris(obs):
    n = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for o in obs:
        if o.type == 'MESH':
            e = o.evaluated_get(dg)
            me = e.to_mesh()
            me.calc_loop_triangles()
            n += len(me.loop_triangles)
            e.to_mesh_clear()
    return n


# ------------------------------------------------------------------ lofts, shells, tags

def bm_solidify(bm, t, inner_mat=None):
    """shell thickness without operators: a copy of every vertex moved `t` against its normal, reversed inner faces, rim faces on the open boundary"""
    bm.normal_update()
    faces = list(bm.faces)
    boundary = [e for e in bm.edges if len(e.link_faces) == 1]
    vmap = {v: bm.verts.new(v.co - v.normal * t) for v in list(bm.verts)}
    uvl = bm.loops.layers.uv.active
    for f in faces:
        nf = bm.faces.new([vmap[v] for v in reversed(f.verts)])
        nf.material_index = f.material_index if inner_mat is None else inner_mat
        nf.smooth = True
        if uvl is not None:
            for lnew, lold in zip(nf.loops, reversed(list(f.loops))):
                lnew[uvl].uv = lold[uvl].uv
    for e in boundary:
        f = e.link_faces[0]
        a = b = None
        for l in f.loops:
            if l.edge == e:
                a, b = l.vert, l.link_loop_next.vert
                break
        rf = bm.faces.new((b, a, vmap[a], vmap[b]))
        rf.material_index = f.material_index if inner_mat is None else inner_mat
        rf.smooth = False


def loft_grid(P, UV, cls_fn, closed=True):
    """P[K,N,3] ring points, UV[K,N+1,2]; cls_fn(k, j) -> (class_name, material_index) | None for the cell between stations k,k+1 and ring points j,j+1; returns ({class: bmesh}, {class: vertex map})"""
    K, N = P.shape[0], P.shape[1]
    bms, vmaps = {}, {}
    for k in range(K - 1):
        for j in range(N if closed else N - 1):
            c = cls_fn(k, j)
            if c is None:
                continue
            name, mi = c
            if name not in bms:
                bms[name] = bmesh.new()
                bms[name].loops.layers.uv.new('UVMap')
                vmaps[name] = {}
            bm, vm = bms[name], vmaps[name]
            jj = (j + 1) % N

            def vtx(kk, jx, bm=bm, vm=vm):
                key = (kk, jx)
                if key not in vm:
                    vm[key] = bm.verts.new(Vector(P[kk, jx]))
                return vm[key]
            vs = [vtx(k, j), vtx(k + 1, j), vtx(k + 1, jj), vtx(k, jj)]
            uvs = [UV[k, j], UV[k + 1, j], UV[k + 1, j + 1], UV[k, j + 1]]
            f = bm.faces.new(vs)
            f.material_index = mi
            f.smooth = True
            uvl = bm.loops.layers.uv.active
            for lp, uv in zip(f.loops, uvs):
                lp[uvl].uv = (float(uv[0]), float(uv[1]))
    return bms, vmaps


def arc_uv(P, uscale=1.0, vscale=1.0):
    """UVs in metres for a ring grid: u by the x coordinate of the ring, v by the arc length around the ring (N+1 columns)"""
    K, N = P.shape[0], P.shape[1]
    UV = np.zeros((K, N + 1, 2))
    for k in range(K):
        q = np.vstack([P[k], P[k][:1]])
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
        UV[k, :, 0] = P[k, :, 0].mean() * uscale
        UV[k, :, 1] = d * vscale
    return UV


def tag(ob, zone=None, state='intact', detach=None, **kw):
    """custom properties the game reads (glTF extras): zone group, intact/damaged state, detachable piece with its break mode"""
    if zone:
        ob['zone'] = zone
    ob['state'] = state
    if detach:
        ob['detach'] = detach
    for k, v in kw.items():
        ob[k] = v
    return ob


def smooth_poly(pts, n=8):
    """Catmull-Rom resample of a 3D polyline through its points (n samples per segment)"""
    arr = [(i, tuple(p)) for i, p in enumerate(pts)]
    out = []
    for i in range(len(pts) - 1):
        for k in range(n):
            out.append(Vector(crom(arr, i + k / n)))
    out.append(Vector(pts[-1]))
    return out


def bm_plate(bm, poly_xz, y0, y1, bevel=0.0, mat_idx=0):
    """a plate: the polygon (x, z) pairs extruded between y0 and y1 (a vertical fin or end plate), edges bevelled"""
    vs0 = [bm.verts.new((x, y0, z)) for x, z in poly_xz]
    f = bm.faces.new(vs0)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=nv, vec=(0, y1 - y0, 0))
    faces = {ff for v in vs0 + nv for ff in v.link_faces}
    bmesh.ops.recalc_face_normals(bm, faces=list(faces))
    if bevel > 0:
        edges = list({e for v in vs0 + nv for e in v.link_edges})
        res = bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=2 if DET >= 1 else 1, affect='EDGES', profile=0.5)
        faces = {f for f in faces if f.is_valid} | set(res['faces'])
    for ff in faces:
        ff.material_index = mat_idx
        ff.smooth = True
    return faces


def naca4(t, n):
    """symmetric NACA 00tt section, chord 1, x 0..1; points from the trailing edge over the top to the leading edge and back along the bottom"""
    xs = [(1 - math.cos(math.pi * i / n)) / 2 for i in range(n + 1)]

    def yt(x):
        return 5 * t * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    up = [(x, yt(x)) for x in reversed(xs)]
    lo = [(x, -yt(x)) for x in xs[1:-1]]
    return up + lo
