// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Loading of the car models for the page without touching the game's loader (GameView.loadModels loads three glbs per kind one after another):
//  - every car glb (full and reduced) starts loading at once, so that the downloads and the texture decoding overlap; GameView's own calls then take the running load by its URL;
//  - the damaged variants are only needed at the first wreck, so GameView is told they are absent while the page loads, and they are loaded behind it and put into its packs afterwards.
import { CAR_KINDS, type KindId } from './game/config';
import './perf';   // the ?perf=1 overlay and the render-scale governor install themselves when the page is ready

type Loader = typeof BABYLON.SceneLoader.LoadAssetContainerAsync;
interface Packs { packs: Map<string, { damaged?: BABYLON.AssetContainer }> }

const FILL: [RegExp, number, number, number][] = [[/headliner/i, 0.30, 0.32, 0.36], [/^M_interior/i, 0.15, 0.15, 0.19], [/carpet/i, 0.09, 0.09, 0.11], [/dash/i, 0.12, 0.12, 0.14], [/seat/i, 0.14, 0.13, 0.12], [/^M_seal|^M_gap|^M_black|^M_well|^M_under/i, 0.07, 0.07, 0.08]];

/** call before `GameView.loadModels`; returns `loadDamaged(view)` to call when the page is ready */
export function planCarLoading(scene: BABYLON.Scene, kinds: KindId[]) {
  const orig: Loader = BABYLON.SceneLoader.LoadAssetContainerAsync.bind(BABYLON.SceneLoader);
  const running = new Map<string, Promise<BABYLON.AssetContainer | undefined>>();
  const damaged = new Map<string, KindId>();
  const key = (root: string, file: unknown) => root + String(file);
  for (const k of kinds) if (CAR_KINDS[k].damaged) damaged.set(CAR_KINDS[k].damaged!, k);
  for (const k of kinds) for (const url of [CAR_KINDS[k].glb, CAR_KINDS[k].lod1]) {
    if (!url) continue;
    const i = url.lastIndexOf('/');
    running.set(key(url.slice(0, i + 1), url.slice(i + 1)), (orig(url.slice(0, i + 1), url.slice(i + 1), scene) as Promise<BABYLON.AssetContainer>).catch((e: unknown) => { console.warn('model not loaded', url, e); return undefined; }));
  }
  const patched = ((root: string, file: unknown, ...rest: unknown[]) => {
    const kk = key(root, file);
    const p = running.get(kk);
    if (p) { running.delete(kk); return p; }
    if ([...damaged.keys()].some((u) => u === root + String(file))) return Promise.resolve(undefined);
    return (orig as unknown as (...a: unknown[]) => Promise<BABYLON.AssetContainer>)(root, file, ...rest);
  }) as unknown as Loader;
  BABYLON.SceneLoader.LoadAssetContainerAsync = patched;
  return {
    /** the loader of the engine is the engine's again; the damaged variants are loaded and handed to the view */
    async loadDamaged(view: unknown) {
      BABYLON.SceneLoader.LoadAssetContainerAsync = orig;
      const packs = (view as Packs).packs;
      await Promise.all([...damaged].map(async ([url, k]) => {
        const i = url.lastIndexOf('/'), c = await orig(url.slice(0, i + 1), url.slice(i + 1), scene).catch((e: unknown) => { console.warn('model not loaded', url, e); return undefined; });
        for (const m of c?.materials ?? []) {
          if (m instanceof BABYLON.PBRMaterial && (k === 'police' || k === 'corvette')) { const f = FILL.find((x) => x[0].test(m.name)); if (f) { m.emissiveColor = new BABYLON.Color3(f[1], f[2], f[3]); m.emissiveIntensity = 1; } }
          if (/glass/i.test(m.name) && m instanceof BABYLON.PBRMaterial) { m.alpha = 0.22; m.transparencyMode = BABYLON.Material.MATERIAL_ALPHABLEND; m.backFaceCulling = false; m.needDepthPrePass = false; }
        }
        const pack = packs.get(k); if (pack && c) pack.damaged = c;
      }));
    },
  };
}
