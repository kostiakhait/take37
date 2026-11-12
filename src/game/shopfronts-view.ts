// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The picture of the converted shop fronts (plans/BUILDINGS-DESTRUCTION.md): the shell and the parts of a building are loaded from its shop file and put where the street's own building stood (whose
// meshes are taken out before the street is merged); a part that the sim says is off is hidden, a pane that is only cracked gets the module's crack star, an awning that came off its bolts falls.
// The pieces of a break (shards, splinters) are drawn by view.ts from the module's `destruction:hit` like every other thing's.
import { starOf, starSegments } from '@ferret/destruction/view-shards';
import { SHOP_BUILDINGS, type ShopState } from './shopfronts';
import type { Sim } from './sim';

type Node = BABYLON.TransformNode;
const NOT_CAST = /^(int_|shelfgoods|wincontent|fluor_int|interiors|windecals|wallart|shopsigns|glass|paint_dark$)/;

/** called by the page before the street's parts are merged: the converted buildings' own meshes leave the street (their shell and parts come from the shop files) */
export function hideConverted(street: BABYLON.ISceneLoaderAsyncResult): void {
  const names = new Set(SHOP_BUILDINGS.flatMap((b) => [b.bld + '_LOD0', b.bld + '_LOD1']));
  for (const n of [...street.transformNodes, ...street.meshes]) {
    if (!names.has(n.name) || n.isDisposed()) continue;
    // an instance goes; the mesh that other buildings of the same design are instances of stays (disposing it would take them along) and is collapsed to nothing instead
    if (n instanceof BABYLON.Mesh && n.instances.length > 0) { n.scaling.setAll(0); n.computeWorldMatrix(true); } else n.dispose(false, false);
  }
}

export class ShopView {
  /** the nodes of the parts, by the sim's part id */
  private nodes = new Map<string, Node>();
  private lods: { hi: Node; lo: Node; at: BABYLON.Vector3 }[] = [];
  private shownOff = new Set<string>();
  private w0 = new Map<string, BABYLON.Matrix>();
  private stars = new Map<string, BABYLON.Mesh>();
  private unlisten: (() => void) | null = null;
  private sim: Sim | null = null;
  stats = { loaded: 0, meshes: 0 };

  constructor(private readonly scene: BABYLON.Scene, private readonly shadow: BABYLON.ShadowGenerator | null, private readonly propNodes: Map<string, Node>) {}

  /** load the shop files and put them under the street's building nodes; the street's materials (same names) are used so that the shop front looks as it did */
  async load(street: BABYLON.ISceneLoaderAsyncResult): Promise<void> {
    const scene = this.scene, mats = new Map<string, BABYLON.Material>();
    for (const m of scene.materials) if (!mats.has(m.name)) mats.set(m.name, m);
    for (const b of SHOP_BUILDINGS) {
      const bld = street.transformNodes.find((n) => n.name === b.bld); if (!bld) { console.warn('shop front: no building node', b.bld); continue; }
      const i = b.url.lastIndexOf('/'), res = await BABYLON.SceneLoader.ImportMeshAsync('', b.url.slice(0, i + 1), b.url.slice(i + 1), scene);
      const root = res.transformNodes.find((n) => /^ShopBld_/.test(n.name)); if (!root) { console.warn('shop front: no root in', b.url); continue; }
      root.parent = bld; root.position.setAll(0); root.rotationQuaternion = BABYLON.Quaternion.Identity(); root.scaling.setAll(1);
      const spent = new Set<BABYLON.Material>(); // the file's own materials are shared by its meshes: dispose only after all are swapped (disposing one early nulls the material of the others)
      for (const m of res.meshes) {
        if (m.getTotalVertices() === 0) continue;
        const own = m.material, use = own ? mats.get(own.name) : undefined;
        if (use && use !== own) { m.material = use; spent.add(own!); }
        m.isPickable = false; m.receiveShadows = true; m.alwaysSelectAsActiveMesh = false;
        if (this.shadow && !NOT_CAST.test(m.material?.name ?? '')) this.shadow.addShadowCaster(m, false);
        this.stats.meshes++;
      }
      for (const s of spent) s.dispose();
      for (const n of [...res.transformNodes, ...res.meshes]) { const mm = n.name.match(/^Part_(Shop[A-Za-z]+_.+?)(?:_primitive\d+)?$/); if (mm && !this.nodes.has(`${b.bld}:${mm[1]}`)) this.nodes.set(`${b.bld}:${mm[1]}`, n as Node); }
      const hi = res.transformNodes.find((n) => n.name === 'Shell_LOD0') ?? res.meshes.find((m) => m.name === 'Shell_LOD0'), lo = res.transformNodes.find((n) => n.name === 'Shell_LOD1') ?? res.meshes.find((m) => m.name === 'Shell_LOD1');
      if (hi && lo) { root.computeWorldMatrix(true); this.lods.push({ hi: hi as Node, lo: lo as Node, at: root.getAbsolutePosition().clone() }); }
      for (const [id, n] of this.nodes) if (/ShopAwning/.test(id)) this.propNodes.set(id, n);
      for (const n of res.meshes.filter((m) => !m.parent || m.parent.name === '__root__')) if (n.name === '__root__') n.dispose();
      this.stats.loaded++;
    }
    this.lod(new BABYLON.Vector3(0, 0, 0), true);
  }

  /** near: the shell with its parts; far (past 130 m): the plain level of detail (the parts are inside it) */
  private lod(cam: BABYLON.Vector3, force = false) {
    for (const l of this.lods) {
      const near = Math.hypot(l.at.x - cam.x, l.at.z - cam.z) < 130;
      if (force || l.hi.isEnabled() !== near) { l.hi.setEnabled(near); l.lo.setEnabled(!near); if (!near) for (const [id, n] of this.nodes) n.setEnabled(false); else for (const [id, n] of this.nodes) n.setEnabled(!this.shownOff.has(id)); }
    }
  }

  /** a new take: every part back, the stars gone, the module's new events listened to */
  startTake(sim: Sim, ds: { listen(fn: (name: string, p: any) => void): () => void }) {
    this.sim = sim; this.unlisten?.(); this.shownOff.clear();
    for (const [id, n] of this.nodes) { n.unfreezeWorldMatrix(); n.setEnabled(true); this.w0.delete(id); }
    for (const s of this.stars.values()) s.dispose(); this.stars.clear();
    if (!sim.shops) return;
    this.unlisten = ds.listen((name, p) => { if (name === 'destruction:crack') this.star(p.id, p.part); });
  }

  private star(thing: string, part: string) {
    const sim = this.sim; if (!sim?.shops) return;
    const st = [...sim.shops.parts.values()].find((s) => s.thing === thing && s.part === part); if (!st) return;
    const p = sim.ds.thing(thing).assembly.get(part).part, key = thing + '/' + part;
    this.stars.get(key)?.dispose(); this.stars.delete(key);
    if (!starOf(p.damage)) return;
    const seg = starSegments(p.damage, p.size[0], p.size[1]), f = st.frame, t = p.size[2] / 2 + 0.003, lines: BABYLON.Vector3[][] = [];
    const w = (x: number, y: number) => new BABYLON.Vector3(f.at[0] + f.u[0] * x + f.up[0] * y + f.out[0] * t, f.at[1] + f.u[1] * x + f.up[1] * y + f.out[1] * t, f.at[2] + f.u[2] * x + f.up[2] * y + f.out[2] * t);
    for (let i = 0; i + 3 < seg.length; i += 4) lines.push([w(seg[i]!, seg[i + 1]!), w(seg[i + 2]!, seg[i + 3]!)]);
    const m = BABYLON.MeshBuilder.CreateLineSystem('star-' + key, { lines }, this.scene); m.color = new BABYLON.Color3(0.92, 0.96, 1); m.isPickable = false;
    this.stars.set(key, m);
  }

  frame(cam: BABYLON.Vector3) {
    this.lod(cam);
    const sim = this.sim; if (!sim?.shops) return;
    for (const s of sim.shops.parts.values()) this.part(s, sim);
  }
  private part(s: ShopState, sim: Sim) {
    const n = this.nodes.get(s.def.id); if (!n) return;
    if (s.state === 'whole') return;
    if (s.state === 'gone') {
      if (!this.shownOff.has(s.def.id)) { this.shownOff.add(s.def.id); n.setEnabled(false); const st = this.stars.get(s.thing + '/' + s.part); if (st) { st.dispose(); this.stars.delete(s.thing + '/' + s.part); } }
      return;
    }
    // fell: the awning section is carried with the sim's falling body
    const d = sim.debris.find((x) => x.ref === s.def.id); if (!d) return;
    this.shownOff.add(s.def.id);
    let w0 = this.w0.get(s.def.id);
    if (!w0) { n.computeWorldMatrix(true); w0 = n.getWorldMatrix().clone(); this.w0.set(s.def.id, w0); }
    const b = s.def.box, base = [(b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2];
    const R = new BABYLON.Matrix(); new BABYLON.Quaternion(d.rot[0], d.rot[1], d.rot[2], d.rot[3]).toRotationMatrix(R);
    n.freezeWorldMatrix(w0.multiply(BABYLON.Matrix.Translation(-base[0]!, -base[1]!, -base[2]!).multiply(R).multiply(BABYLON.Matrix.Translation(d.pos[0], d.pos[1], d.pos[2]))));
  }
}
