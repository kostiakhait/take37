# Street trees: structure and wind data

Built by `trees_kit.py` (Blender 4.2, headless), exported into `street_kit.glb` and `street_level.glb`. Six kit items, each with LOD0 and LOD1:

| Kit item | Species | Colouring |
|---|---|---|
| StreetTree1 | sugar maple, one leader | summer green |
| StreetTree2 | American elm, vase crown, drooping tips | summer green |
| StreetTree3 | oak, broad low crown, thick limbs | summer green |
| StreetTree4 | maple | autumn, red-orange |
| StreetTree5 | elm | autumn, golden yellow |
| StreetTree6 | oak | autumn, russet |

Node names are unchanged (`StreetTreeN_LOD0` / `_LOD1` under the placed empties of `Static/`). Trees 1-3 are the old kit names; 4-6 are new. The layout places them in a fixed pseudo-random pattern.

## Geometry

* One mesh per tree and LOD, primitives split by material: `bark` / `bark2` (library texture tex-bark01 / tex-bark02), `leaf_maple` / `leaf_elm` / `leaf_oak` (alpha-cut, `alphaMode MASK`, cutoff 0.5, double sided), plus the tree-pit parts (`soil`, `paint_dark`, `black_metal`).
* The trunk and limbs are a real branching skeleton (trunk, limbs, branches, twigs); every branch is its own ring tube with its own id. Foliage is sprig cards: each card (about 1 m) shows a fan of twigs with about 30 small leaves (4 variants per atlas, `leaf_<species>_c.png` summer, `leaf_<species>_a_c.png` autumn, 2 x 2 cells), anchored on a branch tip and growing along the branch; several thousand cards per tree give tens of thousands of leaves with sky and wood showing through the alpha gaps. Darker inner sprigs fill the middle of the crown. The crown envelope is lumpy (noise), so the silhouettes are irregular. One colour per tree (trees 1-3 summer green, 4 red-orange maple, 5 golden elm, 6 russet oak) with a light tone change by tier (lower crown darker) and by depth.
* Leaf cards carry custom normals pointing out of the crown, so the crown is lit as a volume (a card is not shaded as a flat plane).
* LOD0 about 10-24 k triangles, LOD1 about 3-7 k (fewer, larger cards, thinner skeleton; see the report for the exact numbers).

## Vertex data for the wind

Every value is stored twice in the glb, because Babylon.js's glTF loader (checked: @babylonjs/loaders 9.33.1 in the Ferret repo) drops custom `_ATTRIBUTES` and only delivers the standard channels:

1. Custom glTF attributes `_SWAY`, `_FLUTTER`, `_PHASE`, `_BRANCH`, `_LEVEL`, `_PIVOT` (three.js and engines that keep unknown attributes see these).
2. The same numbers in the extra UV sets, which Babylon loads as `uv2`..`uv5` (glTF `TEXCOORD_1..4`); the value is the raw number as read, no flip:

| Babylon kind (glTF) | u | v |
|---|---|---|
| `uv2` (TEXCOORD_1) | `_SWAY` | `_FLUTTER` |
| `uv3` (TEXCOORD_2) | `_PHASE` | `_BRANCH` |
| `uv4` (TEXCOORD_3) | `_LEVEL` | `_PIVOT.x` |
| `uv5` (TEXCOORD_4) | `_PIVOT.y` | `_PIVOT.z` |

Use `mesh.getVerticesData('uv2')` etc. (stride 2). Positions and pivots are in the node's local glTF space (Y up).

Attribute meanings (the custom `_` names below are also the names of the numbers in the UV table). Positions are in the node's local space (glTF, Y up); the node origin is the foot of the trunk.

| Attribute | Type | Meaning |
|---|---|---|
| `_SWAY` | float 0..1 | Bending weight. 0 at the root (trunk foot), grows with the distance along the skeleton from the root to the vertex, reaches 1 at the tips of the outermost leaf cards. Static parts (tree pit) are 0. Use it as the lever arm: displacement = wind * `_SWAY`^p (p about 1.5-2 looks natural: the trunk stays still, the crown moves). |
| `_FLUTTER` | float 0..1 | Leaf flutter weight. 0 on wood; on leaf cards 0.3 at the centre of the card up to 1.0 at its corners. Drives the fast, small-amplitude vertex motion of individual leaves. |
| `_PHASE` | float 0..1 | Random phase of the branch the vertex belongs to (the same value for all vertices of one branch and for the clusters on its tip). Multiply by 2 pi and add to the time argument so branches do not move in step. |
| `_BRANCH` | float (integer id) | Id of the branch (0 = trunk). Leaf cards carry the id of the branch they hang on; inner filler cards have id 0. |
| `_LEVEL` | float (0..4) | 0 trunk, 1 limb, 2 branch, 3 twig, 4 leaf card. Lets a shader use a different frequency per level (limbs slow, twigs faster). |
| `_PIVOT` | vec3 | Position (glTF local space) of the base of the vertex's branch (for leaf cards: of the twig tip the cluster hangs on). Rotate / bend the vertex about this point: `p' = pivot + R(wind, phase) * (p - pivot)`. |

Also: `COLOR_0` (vertex colour) is a brightness/hue tone for shading depth (darker inside the crown), not wind data. `TEXCOORD_0` is the atlas / bark UV.

### Suggested use (one formula)

```
w   = _SWAY^1.6
t   = time * f(_LEVEL) + 6.2832 * _PHASE          // f: 0.5 Hz limbs, 0.9 Hz branches, 1.4 Hz twigs
bend = windDir * windSpeed * w * (0.5 + 0.5*sin(t))        // whole-branch sway about the pivot, small angle
flut = windSpeed * _FLUTTER * 0.04 * sin(t*7 + dot(position, vec3(3,5,7)))   // leaf flutter, metres
p'  = pivot + rotate(p - pivot, axis = up x windDir, angle = bend) + flutNormal * flut
```

Wind on the trunk (`_LEVEL` 0) should be near zero except at the very top. The data is baked, there is no skin and no animation clip, so any vertex shader or CPU deformation that reads these attributes will work; the Ferret `@ferret/flow` wind field can supply `windDir` / `windSpeed` per tree position.

## Textures and sources

Bark: library packages tex-bark01 / tex-bark02 (borrowed from the Ferret asset library, tinted nowhere, tiled). Leaf cluster atlases are drawn for the game in `textures_prep.py` (`tree_leaves`): leaf outlines (palmate maple, serrated elm, lobed oak), veins, three depth layers, alpha; no photographs.
