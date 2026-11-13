// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * A viewer for the Robinson R22 glb (art/helicopter/r22): the model is loaded with the same Babylon glTF loader the game uses and shown on the ground, with its rotors turning, its damage states, its detachable pieces falling
 * under the engine's Havok kernel and the whole fuselage dropping as one body on its Collider_* boxes. A check of the model's structure, not the helicopter's flight model.
 * Address: `?lod=0|1`, `?hour=7..20` (sun), `?cam=three|side|front|rear|cockpit|rotor|tail|engine|close|top|walk`, `?dmg=all|Dmg_Group,..`, `?bent=1` (tail boom bent), `?spin=1` (rotors turn), `?pieces=1`, `?fall=1`, `?clean=1`.
 * The page's `window.heli` has `ready`, `info()`, `setCam(name)`, `setDmg(list)`, `spin(on)`, `release(names)`, `fall()`, `step(n)`.
 */
import { havokKernel } from '@ferret/physics-havok';
import type { HavokKernel } from '@ferret/physics';

declare const BABYLON: typeof import('@babylonjs/core');
type Q = [number, number, number, number];
const q = new URLSearchParams(location.search);
const win = window as unknown as Record<string, unknown>;

const rotMul = (a: Q, b: Q): Q => [a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1], a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0], a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3], a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2]];
const rot = (qq: Q, v: [number, number, number]): [number, number, number] => { const [x, y, z, w] = qq, [vx, vy, vz] = v, tx = 2 * (y * vz - z * vy), ty = 2 * (z * vx - x * vz), tz = 2 * (x * vy - y * vx); return [vx + w * tx + y * tz - z * ty, vy + w * ty + z * tx - x * tz, vz + w * tz + x * ty - y * tx]; };

async function main() {
  const canvas = document.getElementById('c') as HTMLCanvasElement;
  const engine = new BABYLON.Engine(canvas, true, { preserveDrawingBuffer: true, stencil: true });
  const gl = engine._gl as WebGL2RenderingContext;
  const dbg = gl.getExtension('WEBGL_debug_renderer_info');
  const renderer = dbg ? String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)) : 'unknown';
  const scene = new BABYLON.Scene(engine);
  const hour = parseFloat(q.get('hour') ?? '12');
  const sunset = hour >= 17.5;
  const k = Math.max(0.05, Math.sin(Math.PI * Math.min(Math.max((hour - 6) / 14, 0.04), 0.96)));
  scene.clearColor = sunset ? new BABYLON.Color4(0.85, 0.52, 0.34, 1) : new BABYLON.Color4(0.55, 0.72, 0.9, 1);
  // sky dome (gradient) and a reflection probe of it as the environment
  const dome = BABYLON.MeshBuilder.CreateSphere('dome', { diameter: 800, sideOrientation: BABYLON.Mesh.BACKSIDE }, scene);
  const dm = new BABYLON.StandardMaterial('dome', scene); dm.disableLighting = true; dm.backFaceCulling = false;
  const dt = new BABYLON.DynamicTexture('domeT', { width: 8, height: 256 }, scene, false); const dc = dt.getContext() as CanvasRenderingContext2D;
  const gr = dc.createLinearGradient(0, 0, 0, 256);
  const stops = sunset ? [[0, '#2b3a66'], [0.45, '#d98a5c'], [0.5, '#f0b070'], [0.52, '#6b5a4e'], [1, '#3e3a34']] : [[0, '#3f78c8'], [0.42, '#a8cdee'], [0.5, '#e6eef5'], [0.52, '#7f8a78'], [1, '#55604a']];
  for (const [o, c] of stops) gr.addColorStop(o as number, c as string);
  dc.fillStyle = gr; dc.fillRect(0, 0, 8, 256); dt.update();
  dm.emissiveTexture = dt; dm.diffuseColor = BABYLON.Color3.Black(); dm.specularColor = BABYLON.Color3.Black(); dome.material = dm; dome.infiniteDistance = true; dome.isPickable = false;
  const probe = new BABYLON.ReflectionProbe('probe', 128, scene); probe.renderList!.push(dome); probe.position.set(0, 2, 0);
  scene.environmentTexture = probe.cubeTexture; scene.environmentIntensity = 0.9 * (0.4 + 0.6 * k);
  const sunDir = sunset ? new BABYLON.Vector3(0.7, -0.22, 0.35) : new BABYLON.Vector3(-0.35, -0.8 * k - 0.2, 0.45);
  const sun = new BABYLON.DirectionalLight('sun', sunDir.normalize(), scene);
  sun.intensity = sunset ? 2.2 : 3.2; sun.diffuse = sunset ? new BABYLON.Color3(1, 0.7, 0.45) : new BABYLON.Color3(1, 0.96, 0.9); sun.position = sunDir.scale(-40);
  const hemi = new BABYLON.HemisphericLight('hemi', new BABYLON.Vector3(0, 1, 0), scene); hemi.intensity = sunset ? 0.35 : 0.5; hemi.groundColor = new BABYLON.Color3(0.25, 0.27, 0.22);
  const sg = new BABYLON.ShadowGenerator(2048, sun); sg.usePercentageCloserFiltering = true; sg.bias = 0.0005; sg.normalBias = 0.01; sun.shadowMinZ = 1; sun.shadowMaxZ = 120; sun.autoUpdateExtends = true;
  // ground: a runway strip on grass, so the model stands on something
  const ground = BABYLON.MeshBuilder.CreateGround('ground', { width: 300, height: 300, subdivisions: 1 }, scene);
  const gm = new BABYLON.PBRMaterial('gm', scene); gm.albedoColor = sunset ? new BABYLON.Color3(0.22, 0.2, 0.12) : new BABYLON.Color3(0.28, 0.36, 0.16); gm.metallic = 0; gm.roughness = 0.95; ground.material = gm; ground.receiveShadows = true;
  const strip = BABYLON.MeshBuilder.CreateGround('strip', { width: 30, height: 300 }, scene); strip.position.y = 0.01;
  const sm = new BABYLON.PBRMaterial('sm', scene); sm.albedoColor = new BABYLON.Color3(0.26, 0.26, 0.27); sm.metallic = 0; sm.roughness = 0.9; strip.material = sm; strip.receiveShadows = true;

  const lod = q.get('lod') === '1' ? '_lod1' : '';
  const res = await BABYLON.SceneLoader.ImportMeshAsync('', '/assets/borrowed/', `r22${lod}.glb`, scene);
  const root = res.meshes[0]!;
  const holder = new BABYLON.TransformNode('holder', scene); root.parent = holder;
  const node = (n: string) => scene.getTransformNodeByName(n) ?? scene.getMeshByName(n);
  const extras = (n: BABYLON.Node) => ((n.metadata as { gltf?: { extras?: Record<string, unknown> } } | null)?.gltf?.extras ?? {});
  const nodes = scene.transformNodes.concat(scene.meshes as unknown as BABYLON.TransformNode[]).filter((n) => n.name !== 'holder' && n !== (root as unknown as BABYLON.TransformNode));
  for (const m of res.meshes) { if ((m as BABYLON.Mesh).getTotalVertices?.() > 0) { sg.addShadowCaster(m); m.receiveShadows = true; } }
  // colliders are for physics only
  for (const m of res.meshes) if (m.name.startsWith('Collider_')) m.setEnabled(false);
  // every damaged-state node is hidden until its group is shown
  const dmgNodes = nodes.filter((n) => extras(n).state === 'damaged');
  const groups = [...new Set(dmgNodes.map((n) => String(extras(n).group)))].filter((g) => g !== 'undefined');
  const groupEmpty = (g: string) => scene.getTransformNodeByName(g);
  const hiddenByDmg = new Set<BABYLON.Node>();
  function setDmg(list: string[]) {
    const all = list.includes('all');
    for (const h of hiddenByDmg) h.setEnabled(true); hiddenByDmg.clear();
    for (const n of dmgNodes) n.setEnabled(false);
    for (const g of groups) {
      if (!(all || list.includes(g))) continue;
      for (const n of dmgNodes) if (extras(n).group === g) n.setEnabled(true);
      const rep = String(extras(groupEmpty(g) ?? n0) .replaces ?? '').split(',').filter(Boolean);
      for (const r of rep) { const t = node(r); if (t) { t.setEnabled(false); hiddenByDmg.add(t); } }
    }
  }
  const n0 = holder;
  setDmg((q.get('dmg') ?? '').split(',').filter(Boolean));
  const pieces = nodes.filter((n) => extras(n).detach !== undefined && extras(n).state !== 'damaged' || n.name === 'TailGroup');
  // bent boom pose
  const tg = scene.getTransformNodeByName('TailGroup');
  const bentEuler = (extras(tg ?? n0).bent_pose_euler_deg as number[] | undefined) ?? [0, -16, 12];
  const tgRot0 = tg?.rotationQuaternion?.clone();
  function bend(on: boolean) { if (!tg || !tgRot0) return; tg.rotationQuaternion = on ? tgRot0.multiply(BABYLON.Quaternion.RotationYawPitchRoll(bentEuler[1]! * Math.PI / 180, bentEuler[2]! * Math.PI / 180, bentEuler[0]! * Math.PI / 180)) : tgRot0.clone(); }
  if (q.get('bent') === '1') bend(true);

  // rotors
  const mainSpin = node('Rotor_Spin'), tailSpin = node('TailRotor_Spin'), teeter = node('Rotor_Teeter');
  let spinning = q.get('spin') === '1', spinA = 0, spinB = 0, rpmScale = 1;
  const mainQ0 = mainSpin?.rotationQuaternion?.clone() ?? BABYLON.Quaternion.Identity(), tailQ0 = tailSpin?.rotationQuaternion?.clone() ?? BABYLON.Quaternion.Identity();
  const bladeNodes = ['Blade_A', 'Blade_B', 'TR_Blade_A', 'TR_Blade_B'].map(node);
  const discNodes = [node('Rotor_Disc'), node('TailRotor_Disc')];
  function showBlur(on: boolean) { for (const d of discNodes) d?.setEnabled(on); }
  showBlur(false);
  win.__blurMode = q.get('blur') === '1';
  scene.onBeforeRenderObservable.add(() => {
    const dt = Math.min(engine.getDeltaTime(), 50) / 1000;
    if (spinning) {
      const blur = !!win.__blurMode;
      spinA += (blur ? 55 : 6) * dt * rpmScale; spinB += (blur ? 330 : 36) * dt * rpmScale;      // rad/s (nominal main rotor 55.5 rad/s = 530 rpm; the demo turns slow without blur so the blades are seen)
      if (mainSpin) mainSpin.rotationQuaternion = mainQ0.multiply(BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Y, spinA));
      if (tailSpin) tailSpin.rotationQuaternion = tailQ0.multiply(BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Z, -spinB));
      // teeter: a flap of a few degrees about the fore-aft axis
      if (teeter) teeter.rotationQuaternion = BABYLON.Quaternion.RotationAxis(BABYLON.Axis.X, Math.sin(spinA * 2) * 0.05);
      showBlur(blur); for (const b of bladeNodes) b?.setEnabled(!blur || (b === bladeNodes[0] && false));
      if (!blur) for (const b of bladeNodes) b?.setEnabled(!hiddenByDmg.has(b!));
    } else { showBlur(false); }
  });

  // camera
  const cam = new BABYLON.ArcRotateCamera('cam', 0, 1, 10, new BABYLON.Vector3(0, 1.3, 0), scene); cam.minZ = 0.05; cam.maxZ = 2000; cam.wheelPrecision = 20; cam.attachControl(canvas, true);
  const presets: Record<string, [number, number, number, number, number, number, number]> = {   // alpha, beta, radius, target x, y, z, fov
    three: [-0.9, 1.25, 11.5, 0.6, 1.3, 0, 0.8], side: [Math.PI / 2 + 0.0, 1.5, 15, 0.8, 1.4, 0, 0.55], front: [0, 1.5, 15, 0, 1.4, 0, 0.55], rear: [Math.PI, 1.45, 15, 0, 1.4, 0, 0.55], top: [Math.PI / 2, 0.02, 18, 0.8, 1, 0, 0.6],
    cockpit: [-1.2, 1.3, 2.4, 0.2, 1.1, 0, 1.0], rotor: [-0.8, 1.2, 3.0, 0, 2.6, 0, 0.9], tail: [-2.2, 1.35, 3.6, -4.4, 1.7, 0, 0.9], engine: [-2.4, 1.3, 3.2, -1.1, 0.85, 0, 0.9], close: [-0.65, 1.38, 5.2, 0.7, 1.2, 0, 0.9], walk: [-0.5, 1.45, 4.2, 0.3, 1.2, 0, 1.0],
    interior: [-1.7, 1.1, 1.7, 0.1, 1.0, 0.1, 1.1], panel: [-3.0, 1.35, 1.3, 0.0, 1.0, 0.0, 0.9],
  };
  function setCam(name: string) { const p = presets[name] ?? presets.three!; cam.alpha = p[0]; cam.beta = p[1]; cam.radius = p[2]; cam.target.set(p[3], p[4], p[5]); cam.fov = p[6]; }
  setCam(q.get('cam') ?? 'three');
  win.__rawcam = cam;

  // ---- physics: detachable pieces and the whole fall under Havok
  let hk: HavokKernel | null = null; const fl: { n: BABYLON.TransformNode; body: ReturnType<HavokKernel['addBody']>; c: BABYLON.Vector3; p0: BABYLON.Vector3; q0: BABYLON.Quaternion }[] = [];
  let fallBody: ReturnType<HavokKernel['addBody']> | null = null, fallStart: BABYLON.Vector3 | null = null;
  async function kernel() { if (hk) return hk; hk = await havokKernel({ gravity: [0, -9.81, 0], substeps: 2 }); hk.addBody({ shape: { type: 'box', half: [150, 0.5, 150] }, kind: 'static', position: [0, -0.5, 0] }); return hk; }
  function bounds(n: BABYLON.TransformNode) { return n.getHierarchyBoundingVectors(true, (m) => m.isEnabled() && m.name.indexOf('Collider_') < 0 && m.isVisible); }
  async function release(names: string[], speed = 0) {
    const k = await kernel();
    for (const nm of names) {
      const n = node(nm) as BABYLON.TransformNode | null; if (!n || fl.some((f) => f.n === n)) continue;
      n.computeWorldMatrix(true); const b = bounds(n); const c = b.min.add(b.max).scale(0.5), half = b.max.subtract(b.min).scale(0.5);
      n.setParent(null); // keep world
      n.rotationQuaternion ??= BABYLON.Quaternion.FromEulerVector(n.rotation);
      const body = k.addBody({ shape: { type: 'box', half: [Math.max(half.x, 0.03), Math.max(half.y, 0.03), Math.max(half.z, 0.03)] }, mass: Math.max(2, half.x * half.y * half.z * 8 * 120), position: [c.x, c.y, c.z], velocity: [speed * (Math.random() - 0.3), 1 + Math.random() * 2, (Math.random() - 0.5) * 2], angularVelocity: [(Math.random() - 0.5) * 6, (Math.random() - 0.5) * 6, (Math.random() - 0.5) * 6], material: undefined });
      fl.push({ n, body, c, p0: n.position.clone(), q0: n.rotationQuaternion.clone() });
    }
  }
  function sync() {
    for (const f of fl) {
      const qb = f.body.orientation as Q, qn = rotMul(qb, [f.q0.x, f.q0.y, f.q0.z, f.q0.w]);
      const d = rot(qb, [f.p0.x - f.c.x, f.p0.y - f.c.y, f.p0.z - f.c.z]);
      f.n.position.set(f.body.position[0] + d[0], f.body.position[1] + d[1], f.body.position[2] + d[2]); f.n.rotationQuaternion = new BABYLON.Quaternion(qn[0], qn[1], qn[2], qn[3]);
    }
    if (fallBody && fallStart) { const qb = fallBody.orientation as Q, r = rot(qb, [fallStart.x, fallStart.y, fallStart.z]); holder.rotationQuaternion = new BABYLON.Quaternion(qb[0], qb[1], qb[2], qb[3]); holder.position.set(fallBody.position[0] - r[0], fallBody.position[1] - r[1], fallBody.position[2] - r[2]); }
  }
  let followOn = false;
  scene.onBeforeRenderObservable.add(() => { if (followOn && fallBody) cam.target.set(fallBody.position[0], fallBody.position[1], fallBody.position[2]); });
  async function fall(h = 25) {
    const k = await kernel();
    const children: { shape: { type: 'box'; half: [number, number, number] }; position: [number, number, number] }[] = [];
    holder.computeWorldMatrix(true);
    let cx = 0, cy = 0, cz = 0; const com = node('CenterOfMass'); if (com) { com.computeWorldMatrix(true); const p = com.getAbsolutePosition(); cx = p.x; cy = p.y; cz = p.z; }
    for (const m of res.meshes) {
      if (!m.name.startsWith('Collider_')) continue;
      m.computeWorldMatrix(true); const bi = m.getBoundingInfo().boundingBox, mn = bi.minimumWorld, mx = bi.maximumWorld;
      children.push({ shape: { type: 'box', half: [(mx.x - mn.x) / 2, (mx.y - mn.y) / 2, (mx.z - mn.z) / 2] }, position: [(mx.x + mn.x) / 2 - cx, (mx.y + mn.y) / 2 - cy, (mx.z + mn.z) / 2 - cz] });
    }
    fallStart = new BABYLON.Vector3(cx, cy, cz);
    fallBody = k.addBody({ shape: { type: 'compound', children }, mass: 399 + 160, position: [cx, cy + h, cz], velocity: [4, 0, 0], angularVelocity: [0.5, 0.3, 1.1] });
  }
  win.heli = {
    follow: (on: boolean) => { followOn = on; }, bodyPos: () => (fallBody ? [...fallBody.position] : null), fl: () => fl.map((f) => [f.n.name, ...f.body.position.map((v) => +v.toFixed(2))]),
    renderer, ready: false, info: () => ({ renderer, nodes: nodes.length, groups, pieces: pieces.map((p) => p.name), colliders: res.meshes.filter((m) => m.name.startsWith('Collider_')).map((m) => m.name), meshes: res.meshes.length, tris: res.meshes.reduce((a, m) => a + ((m as BABYLON.Mesh).getTotalIndices?.() ?? 0) / 3, 0), fps: engine.getFps() }),
    setCam, setDmg, bend, blur: (on: boolean) => { win.__blurMode = on; }, spin: (on: boolean) => { spinning = on; }, spinTo: (a: number, b: number) => { spinA = a; spinB = b; }, release, fall, groups, pieces: pieces.map((p) => p.name),
    step: (n: number) => { if (hk) for (let i = 0; i < n; i++) { hk.step(1 / 60); } sync(); },
    nodePos: (nm: string) => { const n = node(nm); return n ? n.getAbsolutePosition().asArray() : null; },
  };
  scene.onBeforeRenderObservable.add(() => { if (hk) { hk.step(1 / 60); sync(); } });
  if (q.get('pieces') === '1') await release(['Door_L', 'Door_R', 'TailGroup', 'Cowl_Panel_L', 'Cowl_Panel_R', 'Cowl_Belly', 'Blade_A', 'TR_Blade_A', 'Glass_Windshield'], 2);
  if (q.get('fall') === '1') await fall();
  if (q.get('clean') === '1') document.body.classList.add('clean');
  probe.refreshRate = BABYLON.RenderTargetTexture.REFRESHRATE_RENDER_ONCE;
  engine.runRenderLoop(() => scene.render());
  window.addEventListener('resize', () => engine.resize());
  (win.heli as { ready: boolean }).ready = true;
  document.getElementById('hud')!.textContent = `R22 viewer  ${renderer}  ${(globalThis as { __BUILD__?: string }).__BUILD__ ?? ''}`;
}
main().catch((e) => { console.error(e); win.heliError = String(e); });
