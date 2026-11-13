// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { AssetLibrary } from '@ferret/levels';

/**
 * The materials of the airfield: library materials (by catalog id) with the metre size of one texture repeat they are drawn at, made once and shared. Geometry gives its UVs in tiles of `TILE[id]` metres.
 * Where the library has nothing (asphalt, paint, corrugation, sandbags, chain-link) the textures come from `textures3.ts`; see ASSETS.md.
 */
export const TILE: Record<string, number> = {
  concrete: 5, 'concrete-312': 4, 'concrete-block': 2, 'brick-clay-old': 3, 'bricks01-wa': 3, 'roof-tiles': 3, 'metal-steel': 3, 'metal-rust': 3, 'metal-black': 3, 'wood-pine': 2, 'wood-brown': 2, 'wood-dark-brown': 2,
  'crate-wood-270': 1.2, 'crate-wood-271': 1.2, 'crate-wood-274': 1.2, 'stucko-wa1': 4, 'panel-plaster-285': 4, soil: 3, 'cobble-stone-pebble-floor-12': 3, 'rock-slate': 3, bark01: 2, 'wood-oak': 2, 'wood-beige': 2, 'wood-blue': 2,
};

export class Mats {
  private cache = new Map<string, Promise<BABYLON.PBRMaterial>>();
  constructor(private lib: AssetLibrary, private scene: BABYLON.Scene) {}
  /** a library material as it comes, backface culling off and a hint of shine control; `tint` multiplies the base colour, `rough` overrides roughness */
  get(id: string, o: { tint?: [number, number, number]; rough?: number; key?: string; zOffset?: number } = {}): Promise<BABYLON.PBRMaterial> {
    const key = o.key ?? id + JSON.stringify([o.tint, o.rough, o.zOffset]);
    let p = this.cache.get(key);
    if (!p) {
      p = this.lib.material(id, { name: key, scene: this.scene }).then(m => {
        m.backFaceCulling = false; m.twoSidedLighting = true; m.environmentIntensity = 0.35; m.specularIntensity = 0.5;
        if (o.tint) m.albedoColor = new BABYLON.Color3(...o.tint);
        if (o.rough !== undefined) m.roughness = o.rough;
        m.metallic = Math.min(m.metallic, 0.35);
        if (o.zOffset !== undefined) { m.zOffset = o.zOffset; m.zOffsetUnits = o.zOffset; }
        for (const t of [m.albedoTexture, m.bumpTexture, m.metallicTexture]) if (t) (t as BABYLON.Texture).anisotropicFilteringLevel = 8;
        return m;
      });
      this.cache.set(key, p);
    }
    return p;
  }
}

/** a lit flat-colour or textured decal material (alpha from the texture) that lies on pavement: no specular, depth-biased toward the camera */
export function decalMaterial(scene: BABYLON.Scene, name: string, o: { tex?: BABYLON.Texture; colour?: [number, number, number]; alpha?: number; z?: number; spec?: number }): BABYLON.StandardMaterial {
  const m = new BABYLON.StandardMaterial(name, scene);
  m.diffuseColor = o.colour ? new BABYLON.Color3(...o.colour) : BABYLON.Color3.White(); m.specularColor = new BABYLON.Color3(o.spec ?? 0.02, o.spec ?? 0.02, o.spec ?? 0.02);
  if (o.tex) { m.diffuseTexture = o.tex; m.useAlphaFromDiffuseTexture = true; m.transparencyMode = BABYLON.Material.MATERIAL_ALPHABLEND; }
  if (o.alpha !== undefined) { m.alpha = o.alpha; m.transparencyMode = BABYLON.Material.MATERIAL_ALPHABLEND; }
  m.backFaceCulling = false; m.zOffset = o.z ?? -2; m.zOffsetUnits = o.z ?? -2; m.disableDepthWrite = true;
  return m;
}
