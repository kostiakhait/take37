// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { WindField } from '../weather/wind-sway';

/**
 * The material of the plants of the landscape (thin instances of unit-height meshes with vertex colours): lit by the sun and the sky like the land, hazed like the land, and moved by the
 * wind field in the vertex shader, by the height in the plant (the crown bends, the foot stays), so a gust that leans the grass reaches the oaks a moment later.
 */
const VERT = `
precision highp float;
attribute vec3 position; attribute vec3 normal; attribute vec4 color; attribute vec4 world0; attribute vec4 world1; attribute vec4 world2; attribute vec4 world3; attribute vec4 instanceColor;
uniform mat4 viewProjection; uniform vec3 cameraPosition; uniform sampler2D windTex; uniform vec4 windA; uniform vec4 windB; uniform float unitHeight; uniform float windGain;
varying vec3 vN; varying vec3 vCol; varying float vDist; varying float vShade;
float hash(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
void main() {
  mat4 w = mat4(world0, world1, world2, world3);
  vec4 wp = w * vec4(position, 1.0);
  float H = length(world1.xyz) * unitHeight;
  vec2 uvw = (wp.xz - windB.xy) / windB.z + 0.5;
  float g = texture2D(windTex, clamp(uvw, 0.001, 0.999)).r * 3.0;
  float u = windA.z * g * windGain;
  float ph = hash(floor(world3.xyz * 0.37)) * 6.2831;
  float h = clamp(position.y / unitHeight, 0.0, 1.6);
  float wgt = pow(h, 1.7);
  float lean = clamp(u * 0.016, 0.0, 0.42);
  float osc = sin(windA.w * 1.3 + ph) * 0.3 + sin(windA.w * 2.9 + ph * 1.7) * 0.12;
  float a = lean * (1.0 + osc * clamp(u / 5.0, 0.15, 1.6));
  vec3 off = vec3(windA.x, 0.0, windA.y) * a * wgt * H;
  off.y -= 0.5 * a * a * wgt * H;
  off += vec3(sin(windA.w * 8.0 + dot(wp.xyz, vec3(2.3, 3.1, 2.9))), sin(windA.w * 9.3 + dot(wp.xyz, vec3(3.7, 2.1, 3.3))), 0.0) * 0.012 * clamp(u / 8.0, 0.0, 1.5) * wgt * length(world1.xyz) * step(0.5, h);
  wp.xyz += off;
  vN = normalize((w * vec4(normal, 0.0)).xyz);
  vCol = color.rgb * instanceColor.rgb; vShade = 0.55 + 0.45 * clamp(position.y / unitHeight, 0.0, 1.0);
  vDist = distance(cameraPosition, wp.xyz);
  gl_Position = viewProjection * wp;
}`;
const FRAG = `
precision highp float;
varying vec3 vN; varying vec3 vCol; varying float vDist; varying float vShade;
uniform vec3 sunDir; uniform vec3 sunColor; uniform vec3 ambient; uniform vec3 hazeColor; uniform float hazeDensity;
vec3 aces(vec3 x) { return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }
void main() {
  vec3 n = normalize(vN);
  float lit = abs(dot(n, normalize(sunDir))) * 0.8 + max(dot(n, normalize(sunDir)), 0.0) * 0.2;
  vec3 base = pow(vCol, vec3(2.2));
  vec3 col = base * vShade * (ambient * (0.6 + 0.4 * n.y) + sunColor * lit);
  col = mix(col, hazeColor, clamp(1.0 - exp(-hazeDensity * vDist), 0.0, 1.0));
  gl_FragColor = vec4(pow(aces(col), vec3(1.0 / 2.2)), 1.0);
}`;

export function plantMaterial(scene: BABYLON.Scene, field: WindField, windGain = 1) {
  BABYLON.Effect.ShadersStore['take37PlantVertexShader'] = VERT; BABYLON.Effect.ShadersStore['take37PlantFragmentShader'] = FRAG;
  const m = new BABYLON.ShaderMaterial('plants', scene, { vertex: 'take37Plant', fragment: 'take37Plant' }, {
    attributes: ['position', 'normal', 'color', 'world0', 'world1', 'world2', 'world3', 'instanceColor'],
    uniforms: ['viewProjection', 'cameraPosition', 'windA', 'windB', 'unitHeight', 'windGain', 'sunDir', 'sunColor', 'ambient', 'hazeColor', 'hazeDensity'], samplers: ['windTex'],
  });
  m.backFaceCulling = false; m.setTexture('windTex', field.tex); m.setFloat('unitHeight', 1); m.setFloat('windGain', windGain);
  m.setVector3('sunDir', new BABYLON.Vector3(0.3, 0.8, 0.4)); m.setVector3('sunColor', new BABYLON.Vector3(1, 1, 1)); m.setVector3('ambient', new BABYLON.Vector3(0.3, 0.3, 0.3)); m.setVector3('hazeColor', new BABYLON.Vector3(0.6, 0.7, 0.8)); m.setFloat('hazeDensity', 1e-4);
  scene.onBeforeRenderObservable.add(() => {
    const u = field.u, c = scene.activeCamera?.globalPosition;
    m.setVector4('windA', new BABYLON.Vector4(u.dirX, u.dirZ, u.speed, u.time)); m.setVector4('windB', new BABYLON.Vector4(u.ox, u.oz, u.span, 0));
    if (c) m.setVector3('cameraPosition', c);
  });
  return Object.assign(m, {
    light(sun: number[], sunColor: number[], ambient: number[], haze: number[], density: number) {
      m.setVector3('sunDir', new BABYLON.Vector3(sun[0], sun[1], sun[2])); m.setVector3('sunColor', new BABYLON.Vector3(sunColor[0], sunColor[1], sunColor[2]));
      m.setVector3('ambient', new BABYLON.Vector3(ambient[0], ambient[1], ambient[2])); m.setVector3('hazeColor', new BABYLON.Vector3(haze[0], haze[1], haze[2])); m.setFloat('hazeDensity', density);
    },
  });
}
