# Emily candidate: "Modern Female Character" (Fab) - facts

Evaluation export only. No dressing, restyling or retexturing was done (textures only downscaled 4096 -> 2048 for the preview glb).

## Source
- Fab listing: https://www.fab.com/listings/468f4d31-a500-430d-b832-736cc9896aa2 (vault item FemaleCi231ec60ccc26V1, category "Characters & Creatures", AssetPack)
- Built with UE 5.5.0 (manifest build string 5.5.0-34956854); Fab lists compatibility UE 4.26, 4.27, 5.0-5.4. Exported here with UE 5.8.4 (D:\UE_5.8_b) through the Ferret tool tools/ue-export/ue/characters.py (UE glTF exporter, one mesh per editor run) and characters.mjs clips.
- Licence text: NOT present in the vault manifest (it holds only the listing URL, title, tags and file list). The Fab standard licence applies by default but the listing text was not read. Must be checked on the Fab page before use.
- Content: civilian_girl/ meshes (SKM_army_girl, SK_army_girl_Skeleton, PHYS_army_girl_PhysicsAsset), 6 materials, 12 textures, demo animations ThirdPersonIdle/Walk/Run/Jump_Start/Jump_Loop/Jump_End/Jump, ThirdPerson_AnimBP, ThirdPerson_IdleRun_2D blend space, preview.umap.

## Geometry
- LODs: 1 (LOD0 only). No LOD1 exists in the asset, so no LOD1 glb was produced.
- Total: 8948 triangles, 5880 vertices (UE reports 5880 vertices for LOD0: matches).
- Per material (= per glTF primitive):

| material | triangles | vertices |
|---|---|---|
| M_civilian_girl_body | 2296 | 1740 |
| M_civilian_girl_head | 2338 | 1288 |
| M_civilian_girl_hair | 626 | 533 |
| M_civilian_girl_eyelashes | 106 | 92 |
| M_civilian_girl_body_skin | 3318 | 2081 |
| M_civilian_girl_eyes | 264 | 146 |

- "M_civilian_girl_body" is the clothing (top, jeans, belt, boots, shares the body textures); "M_civilian_girl_body_skin" is the bare skin (arms, hands, neck, parts of the torso).
- Height: 1.975 m (bounding box Z of the skinned meshes in rest pose, hair included; UE bounds extent Z 98.76 cm x 2). This is TALL for a woman.
- Faces +Z in the glTF (imports as facing -Y in Blender); rest pose is an A-pose (arms about 30 degrees down, see frames/static/*_restpose.png). No T-pose is exported.
- Morph targets: **0** (none in the UE asset; "morph_targets" list is empty, glTF has no targets).
- Nanite off. Vertex colours none. UV sets: 3 (TEXCOORD_0..2).

## Skeleton (UE5-mannequin-style, 85 joints in the skin; viewer counts 86 with the glTF root node)
- Face: jaw, lip_up, lip_up_1_l/2_l/1_r/2_r, lip_under, lip_under_l/r, eye_l, eye_r, eyebrow_l/r, eyelashes_01/02_l/r. Jaw: yes. Eyes: yes. Face controls are bones only (no morphs, no facial blendshapes, no tongue/teeth).
- Fingers: all five on both hands, 3 joints each (thumb, index, middle, ring, pinky: _01 _02 _03 on each side, 15 per hand, 30 total); no metacarpal joints, no corrective bones.
- Feet: foot + ball bones, no individual toes. Twist bones: one each on upperarm, lowerarm, thigh, calf. Spine: spine_01..03 (UE5 mannequin has 5). No breast bones (cc-clips want breast_l/r: 2 clip bones unmatched).
- IK helper bones: ik_foot_root, ik_foot_l/r, ik_hand_root, ik_hand_gun, ik_hand_l/r.
- Full list (85):
1. root
2. pelvis
3. spine_01
4. spine_02
5. spine_03
6. clavicle_l
7. upperarm_l
8. lowerarm_l
9. lowerarm_twist_01_l
10. hand_l
11. index_01_l
12. index_02_l
13. index_03_l
14. middle_01_l
15. middle_02_l
16. middle_03_l
17. pinky_01_l
18. pinky_02_l
19. pinky_03_l
20. ring_01_l
21. ring_02_l
22. ring_03_l
23. thumb_01_l
24. thumb_02_l
25. thumb_03_l
26. upperarm_twist_01_l
27. clavicle_r
28. upperarm_r
29. lowerarm_r
30. lowerarm_twist_01_r
31. hand_r
32. thumb_01_r
33. thumb_02_r
34. thumb_03_r
35. index_01_r
36. index_02_r
37. index_03_r
38. middle_01_r
39. middle_02_r
40. middle_03_r
41. ring_01_r
42. ring_02_r
43. ring_03_r
44. pinky_01_r
45. pinky_02_r
46. pinky_03_r
47. upperarm_twist_01_r
48. neck_01
49. head
50. jaw
51. lip_under
52. lip_under_l
53. lip_under_r
54. eye_r
55. eye_l
56. eyelashes_01_l
57. eyelashes_01_r
58. eyelashes_02_r
59. eyelashes_02_l
60. lip_up
61. lip_up_1_l
62. lip_up_2_l
63. lip_up_1_r
64. lip_up_2_r
65. eyebrow_l
66. eyebrow_r
67. thigh_l
68. calf_l
69. calf_twist_01_l
70. foot_l
71. ball_l
72. thigh_twist_01_l
73. thigh_r
74. calf_r
75. calf_twist_01_r
76. foot_r
77. ball_r
78. thigh_twist_01_r
79. ik_foot_root
80. ik_foot_l
81. ik_foot_r
82. ik_hand_root
83. ik_hand_gun
84. ik_hand_l
85. ik_hand_r

## Materials and textures
- 6 materials: body, head, hair (masked, two-sided), eyelashes (translucent, two-sided), body_skin, eyes (uses the head BaseColor texture). Head and body_skin use UE Subsurface Profile (T_civilian_girl_SSS): the glTF exporter bakes them as Default Lit, so skin SSS is lost.
- Original textures (UE import): body BaseColor / Normal / OcclusionRoughnessMetallic / Specular 4096x4096; head BaseColor / Normal / ORM / Specular 4096x4096; hair BaseColor 512x1024, hair Alpha 1024x2048; eyelashes Alpha 512x512; SSS profile asset.
- Exported 4K glb (PNG): original_4k/SKM_army_girl_4k.glb, 116 MB (textures in glb: body/head BaseColor, Normal, ORM at 4096; baked hair 1024x2048, lashes 1024x1024; Specular maps baked to a separate 4096 image per material).
- Preview glb: glb/Emily_2k.glb 6.6 MB, every texture capped to 2048 and re-encoded WebP q92 (textureCompress). Originals kept in original_4k/ and in the vault (read-only).
- Hair type: **cards** (one hair mesh of 626 triangles with an alpha-masked strand texture; no groom/strands asset in the pack).

## What she wears (as delivered, unchanged)
Red tank top, dark grey/black jeans with brown belt, brown lace-up ankle boots; shoulder-length dark-brown bob with a side parting, light freckled skin, hazel/brown eyes.

## Clips (glb/Emily_clips.glb, already merged into Emily_2k.glb; 7, 170 channels each)
ThirdPersonIdle 2.633 s, ThirdPersonWalk 1.0 s, ThirdPersonRun 0.6 s, ThirdPersonJump_Start 0.467 s, ThirdPersonJump_Loop 0.7 s, ThirdPersonJump_End 0.2 s, ThirdPerson_Jump 0.2 s. All move bones. Walk/run are in place (no root translation). ThirdPerson_AnimBP and the IdleRun_2D blend space were not converted (not asked; state graph is the standard UE ThirdPerson template).
