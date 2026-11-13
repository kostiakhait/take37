# Emily candidate: Fab "Modern Female Character" - evaluation export

Evaluation only. Nothing was dressed, restyled or retextured. Numbers and bone list: facts.md. All renders: Blender 4.2.3 EEVEE on the NVIDIA RTX 3050 (frames/render_device.txt); Ferret viewer frames on ANGLE D3D11 NVIDIA RTX 3050 (frames/ferret_viewer/renderer.txt). Cycles was tried first and abandoned (GPU shared with UE and other sessions: about 2 min per frame, then a CUDA launch failure).

## Contents
- glb/Emily_2k.glb: mesh LOD0 + skeleton (85 joints) + skin weights + 6 materials, textures 2048, 7 clips merged in. glb/Emily_clips.glb (+json): the clips alone. original_4k/: the 4096 exports.
- frames/static (24: front, three_quarter, side, back, restpose (A-pose), head front/3-4/side, each hand front/side, day + dim), frames/anim (64: walk and run from two angles, idle, jump start/loop/end, 8 frames each), frames/ferret_viewer (20).
- sheets/ALL_FRAMES_contact_sheet.png (all 108 frames), walk_contact_sheet.png, run_..., idle_jump_..., bodies_day_and_dim.png, heads_day_and_dim.png, hands.png, viewer_sheet.png.
- scripts/: render.py, viewer_run.mjs, down2k.mjs, glbfacts.mjs, sheet.mjs. Scratch UE project: D:\temp\take37\emily_ue (UE 5.8.4).

## Verdict: what fits
- Exports cleanly: skinned, 85-joint UE5-mannequin-style skeleton, 6 materials, 8,948 triangles, 5,880 vertices (cheap; far under the 100k desktop tier). 2K glb is 6.6 MB.
- Ferret character viewer: loads with no problems (6 meshes, 6 skinned, 7 clips, all 170 tracks move).
- Skeleton shares bone names with the cc-70 group: the library "cc clips" (105 clips, incl. Jog_Fwd, Idle, Jump_Start) bind by name with no retarget map. Viewer: only 2 clip bones unmatched (breast_l, breast_r); frames show natural Jog_Fwd, Idle, Jump_Start. Of the 105 only the additive/pose/aim clips "move nothing", as expected for those. The 7 demo clips (idle, walk, run, jump x4) play on her own skeleton directly; they are UE ThirdPerson template clips shared by every character of that template, so "retargeting" them is the same by-name bind.
- Face: good realistic head, freckles, hazel eyes, lashes, brows; all five fingers per hand, 3 joints each, hands look correct in close-up. Jaw, lip, eye and eyebrow bones exist.
- Daylight and dim interior both read well (frames/static day_* and dim_*).

## Verdict: what does not fit
- Height 1.975 m. Tall for a woman; needs scaling (about 0.85 for 1.68 m) and then the proportions (long legs, in the front frames) stay slender.
- Hair: 626-triangle card shell, stringy lower edge, hard cap-like hairline from the side and 3/4 views (heads_day_and_dim.png); ends are alpha strands, no grooms. Works at game distance, weak in close-ups. Hair moves rigidly with the head (no hair bones).
- 0 morph targets and face only by bones (jaw/lips/eyes/brows). No facial blendshapes, no teeth or tongue meshes: an open mouth will show nothing behind the lips. Expression and lip-sync need the bones, or work on top.
- No LOD1 in the asset (one LOD, 8,948 triangles).
- Skin SSS lost: head and body_skin use a UE Subsurface Profile; glTF exports Default Lit. Skin looks a little waxy in the close-ups and the day lighting makes her skin very pale.
- Clothes are part of the body mesh (the "body" material is top, jeans, belt and boots in one primitive), baked into the skin weights and UV: swapping or restyling her outfit means rework, not a material swap. Does not fit our clothing tailor pipeline without cutting the mesh. The A-pose is rest, not T-pose.
- Skeleton is lean: 3 spine joints (UE5 mannequin has 5), no breast bones, no toes, no metacarpals, no corrective/twist-correction bones: elbow and shoulder deformation is simpler than the MetaHuman Emily the repo has now (1185 joints).
- Licence text not in the vault manifest: check the Fab listing page before use. Fab lists UE 4.26 to 5.4 as compatible (asset built in 5.5.0).
- Textures: 4K body/head are big (116 MB glb with PNGs); the 2K glb is fine for preview. Materials were baked by the UE exporter (roughness/metal/normal kept, specular baked separately).

## Problems seen in the frames (honest list)
1. My first renders had hands out of frame (framing at the hand-bone midpoint): fixed, hands.png is the final.
2. Jump_Start/Jump_Loop frames in frames/anim crop the head at the top of the frame: the camera is fixed (no root follow). That is the camera, not the model.
3. Idle clip (ThirdPersonIdle): the weight is on bent knees with arms slightly in; looks hunched from the side. The run clip has her chin dropped and torso leaning strongly forward (UE template motion, not an export fault).
4. In the Ferret viewer, Emily_with_cc_clips Jump_Start raises arms high and cc Jog has hands in front of the belly: these are the clips' own poses on an A-pose-rest body; no arm/shoulder collapse or twisted joints were seen in the 10 viewer frames I looked at, and the 4K textures show no stretching.
5. The head close-ups (3/4 and side) show the hair as a smooth helmet over the scalp with a visible hard line at the hairline.
6. Face expression is a fixed neutral, slightly stern, mouth closed; in the dim front head frame, one side of the face is nearly black under the single warm lamp.
7. Boots: in the ferret viewer the heels sit on the grid with no foot penetration seen; in Blender the feet at floor height ground at about z=-0.001 m: OK.
8. A stray empty folder C:\frames_static may exist from a relative-path Blender run; I could not delete it (removal blocked by a safety check). Please delete it.

## Not done / not applicable
- LOD1 glb: asset has no LOD1.
- Morph target names: none exist.
- Ferret retarget to "our skeleton group": the cc-70 group already uses the same bone names; bound by name with no map (viewer report above). A dedicated retargetGroup run with rest-pose rebasing was not needed and was not run separately.
- T-pose: the asset's rest pose is an A-pose; only that was rendered.
- ThirdPerson_AnimBP and IdleRun_2D blend space not converted.
- No git commit: output is in D:\temp, not in a repo; nothing pushed.
