// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026

/**
 * The material of the land: `TerrainView` bakes the colour of each ground layer into the vertices (that colour carries the golden grass, the pale soil, the road dirt and the rock over a
 * whole hillside), and this shader adds the near detail from the asset library's ground textures: it multiplies the baked colour by the relative brightness of the grass, soil and rock
 * textures (their own hue is not used: the land is dry and gold, the textures are green), at two scales so no repeat shows, fading out with distance. Steep ground takes the rock texture
 * in the plane of the slope. Lighting, haze and the cast shadows baked into the vertices are as the module's own.
 */
const VERT = `
precision highp float;
attribute vec3 position; attribute vec3 normal; attribute vec4 color; attribute float morph; attribute float shadow;
uniform mat4 world; uniform mat4 worldViewProjection; uniform vec3 cameraPosition; uniform vec2 morphRange;
varying vec3 vN; varying vec4 vC; varying float vDist; varying vec3 vW; varying float vS;
void main() {
  vec4 w = world * vec4(position, 1.0);
  float d = distance(cameraPosition.xz, w.xz);
  float k = smoothstep(morphRange.x, morphRange.y, d);
  vec3 p = position; p.y += morph * k;
  w = world * vec4(p, 1.0);
  vS = shadow; vN = normal; vC = color; vDist = distance(cameraPosition, w.xyz); vW = w.xyz;
  gl_Position = worldViewProjection * vec4(p, 1.0);
}`;

const FRAG = `
precision highp float;
varying vec3 vN; varying vec4 vC; varying float vDist; varying vec3 vW; varying float vS;
uniform vec3 sunDir; uniform vec3 sunColor; uniform vec3 ambient; uniform vec3 hazeColor; uniform float hazeDensity; uniform vec3 groundColor; uniform float exposure;
uniform sampler2D grassTex; uniform sampler2D soilTex; uniform sampler2D rockTex;
float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }
float lum(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
float rel(sampler2D t, vec2 uv) { return lum(texture2D(t, uv).rgb) / max(lum(texture2D(t, uv, 9.0).rgb), 0.02); }
vec3 aces(vec3 x) { return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }
void main() {
  vec3 n = normalize(vN);
  float grain = vC.a, near = 1.0 - smoothstep(25.0, 420.0, vDist), mid = 1.0 - smoothstep(120.0, 1500.0, vDist);
  vec2 p = vW.xz;
  float g1 = rel(grassTex, p * 0.41), g2 = rel(grassTex, p * 0.047 + 3.1);
  float s1 = rel(soilTex, p * 0.55 + 7.7), s2 = rel(soilTex, p * 0.061);
  float r1 = 0.5 * (rel(rockTex, vW.xy * 0.33) + rel(rockTex, vW.zy * 0.33)), r2 = 0.5 * (rel(rockTex, vW.xy * 0.05) + rel(rockTex, vW.zy * 0.05));
  float soilK = smoothstep(0.52, 0.32, vC.g / max(vC.r, 0.05) * 0.62);
  float slopeK = smoothstep(0.86, 0.6, n.y);
  float d1 = mix(g1, s1, soilK), d2 = mix(g2, s2, soilK);
  float detail = mix(d1 * 0.65 + d2 * 0.35, r1 * 0.6 + r2 * 0.4, slopeK);
  float g = (vn(vW.xz * 1.7) * 0.5 + vn(vW.xz * 6.1) * 0.35 + vn(vW.xz * 23.0) * 0.15) - 0.5;
  float big = vn(vW.xz * 0.006) - 0.5;
  vec3 base = pow(vC.rgb, vec3(2.2));
  float hue = vn(vW.xz * 0.0021 + 11.0), hue2 = vn(vW.xz * 0.009 + 5.0);
  base *= mix(vec3(1.12, 1.0, 0.8), vec3(0.86, 0.98, 0.84), smoothstep(0.35, 0.7, hue)) * (0.82 + 0.36 * hue2);
  base *= mix(1.0, detail, 0.82 * near) * (1.0 + g * grain * 0.55 * near) * (1.0 + big * 0.5 * mid);
  float lit = max(dot(n, normalize(sunDir)), 0.0) * (1.0 - vS);
  vec3 col = base * (ambient * (0.55 + 0.45 * n.y) + sunColor * lit);
  float f = 1.0 - exp(-hazeDensity * vDist);
  col = mix(col, hazeColor, clamp(f, 0.0, 1.0));
  gl_FragColor = vec4(pow(aces(col * exposure), vec3(1.0 / 2.2)), 1.0);
}`;

export interface TerrainTextures { grass: BABYLON.BaseTexture; soil: BABYLON.BaseTexture; rock: BABYLON.BaseTexture }

/** the material handed to `TerrainView.material`; keeps the lighting in step with the sky through `light()` */
export function terrainMaterial(scene: BABYLON.Scene, tex: TerrainTextures) {
  BABYLON.Effect.ShadersStore['take37TerrainVertexShader'] = VERT; BABYLON.Effect.ShadersStore['take37TerrainFragmentShader'] = FRAG;
  const m = new BABYLON.ShaderMaterial('terrain-mat', scene, { vertex: 'take37Terrain', fragment: 'take37Terrain' }, {
    attributes: ['position', 'normal', 'color', 'morph', 'shadow'],
    uniforms: ['world', 'worldViewProjection', 'cameraPosition', 'morphRange', 'sunDir', 'sunColor', 'ambient', 'hazeColor', 'hazeDensity', 'groundColor', 'exposure'],
    samplers: ['grassTex', 'soilTex', 'rockTex'],
  });
  m.setTexture('grassTex', tex.grass); m.setTexture('soilTex', tex.soil); m.setTexture('rockTex', tex.rock);
  m.setVector3('groundColor', new BABYLON.Vector3(0.5, 0.4, 0.3)); m.setFloat('exposure', 1);
  m.backFaceCulling = false;
  // the terrain lies a little behind the road where the two share a plane (the platform), whatever the depth precision
  m.zOffset = 3; m.zOffsetUnits = 3;
  m.onBindObservable.add((mesh) => { const r = (mesh.metadata as { morphRange?: [number, number] } | null)?.morphRange; if (r) m.getEffect()?.setFloat2('morphRange', r[0], r[1]); });
  return m;
}
