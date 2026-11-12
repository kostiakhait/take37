// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { WeatherState } from '@ferret/weather';
import type { WeatherPreset } from '../config/weather';

export type V3 = [number, number, number];
const mix = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
const mul = (a: V3, k: number): V3 => [a[0] * k, a[1] * k, a[2] * k];
const cl = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const sstep = (a: number, b: number, x: number) => { const t = cl((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const rad = Math.PI / 180;

/** the set's place: a Californian valley at about 35 degrees north, +x east and +z north, in summer; the sun's declination is that of late June to July */
export const PLACE = { latitude: 35, declination: 21 };

/** the direction to the sun for an hour (local solar time), turned about the vertical by `roll` degrees (the street is not necessarily east-west) */
export function sunDirection(hour: number, roll = 0): V3 {
  const H = (hour - 12) * 15 * rad, lat = PLACE.latitude * rad, dec = PLACE.declination * rad;
  const east = -Math.cos(dec) * Math.sin(H);
  const north = Math.sin(dec) * Math.cos(lat) - Math.cos(dec) * Math.cos(H) * Math.sin(lat);
  const up = Math.sin(dec) * Math.sin(lat) + Math.cos(dec) * Math.cos(H) * Math.cos(lat);
  const r = roll * rad, c = Math.cos(r), s = Math.sin(r), x = east * c - north * s, z = east * s + north * c, l = Math.hypot(x, up, z);
  return [x / l, up / l, z / l];
}

export interface Look {
  sunDir: V3; sunColor: V3; sunIntensity: number;
  skyTop: V3; skyHorizon: V3; skySun: V3; hazeColor: V3; hazeDensity: number; fogDensity: number;
  hemiSky: V3; hemiGround: V3; hemiIntensity: number;
  elevation: number; day: number; cover: number;
}

/**
 * The look of the sky from the weather and the hour: the colour of the zenith, the horizon and the haze, the sun's colour and strength, the ambient light. The sun reddens and weakens as
 * it nears the horizon (a longer path through the air), cloud takes light from the direct sun and greys the sky, the visibility (km) sets how fast distance turns to haze.
 */
export function lookOf(s: WeatherState, p: WeatherPreset): Look {
  const sunDir = sunDirection(p.hour, p.sunRoll), elev = sunDir[1];
  const day = sstep(-0.14, 0.22, elev), cover = Math.pow(cl(s.cloudCover), 0.85);
  // a clear Rayleigh sky: deep blue at the top, pale and a little warm near the horizon; the sun's glow reddens both when it is low
  let top: V3 = mix([0.1, 0.24, 0.58], [0.2, 0.34, 0.66], 1 - sstep(0.1, 0.9, elev));
  let hor: V3 = [0.62, 0.74, 0.9];
  const warm = sstep(0.42, 0.0, elev) * sstep(-0.16, 0.03, elev);
  hor = mix(hor, [0.98, 0.58, 0.32], warm * 0.78); top = mix(top, [0.2, 0.2, 0.42], warm * 0.45);
  const dust = cl(s.dustiness);
  hor = mix(hor, [0.78, 0.68, 0.52], dust * 0.5); top = mix(top, [0.5, 0.5, 0.52], dust * 0.4);
  const grey = mix([0.66, 0.68, 0.72], [0.42, 0.43, 0.47], cover);
  top = mix(top, mul(grey, 0.85), cover * 0.55); hor = mix(hor, mul(grey, 1.0), cover * 0.45);
  const dim = 0.03 + 0.97 * day;
  top = mul(top, dim); hor = mul(hor, 0.04 + 0.96 * Math.max(day, warm * 0.9));
  // the sky round the sun: bright and warm
  const sunCol = mix([1.0, 0.96, 0.88], [1.0, 0.52, 0.2], sstep(0.4, 0.02, elev));
  const skySun = mix(hor, mix(sunCol, [1, 1, 1], 0.2), 0.55);
  const sunIntensity = 4.2 * Math.pow(cl(elev, 0, 1), 0.45) * (1 - 0.8 * cover) * (1 - 0.5 * dust) * day;
  // haze: the Koschmieder law, extinction 3.9 / visibility; the haze takes the colour of the horizon air
  const vis = Math.max(2000, p.visibilityKm * 1000), hazeDensity = 3.9 / vis * 0.17;
  const haze = mix(mix(mul(hor, 0.9), [0.5, 0.62, 0.82], 0.3 * day), [0.72, 0.66, 0.56], dust * 0.35);
  const hemiSky = mix(hor, top, 0.55), hemiGround = mul(mix([0.5, 0.42, 0.3], [0.4, 0.36, 0.3], cover), 0.25 + 0.75 * day);
  return {
    sunDir, sunColor: sunCol, sunIntensity, skyTop: top, skyHorizon: hor, skySun, hazeColor: haze, hazeDensity, fogDensity: hazeDensity * 0.8,
    hemiSky, hemiGround, hemiIntensity: (0.35 + 0.55 * day) * (1 - 0.15 * cover), elevation: elev, day, cover,
  };
}

const VS = `
precision highp float;
attribute vec3 position; uniform mat4 worldViewProjection; varying vec3 vD;
void main() { vD = position; vec4 p = worldViewProjection * vec4(position, 1.0); gl_Position = p.xyww; }`;
const FS = `
precision highp float;
varying vec3 vD; uniform vec3 top; uniform vec3 horizon; uniform vec3 haze; uniform vec3 sunDir; uniform vec3 sunCol; uniform vec3 skySun; uniform vec4 misc;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
void main() {
  vec3 d = normalize(vD);
  float up = d.y;
  float t = clamp(up, 0.0, 1.0);
  // the gradient: a thin bright band at the horizon, the blue deepening with the square root of the altitude
  vec3 col = mix(horizon, top, pow(t, 0.42));
  float s = max(dot(d, normalize(sunDir)), 0.0);
  // Mie forward scattering about the sun, widening and warming near the horizon
  float lowSun = 1.0 - clamp(sunDir.y * 2.5, 0.0, 1.0);
  col = mix(col, skySun, (pow(s, 7.0) * 0.5 + pow(s, 40.0) * 0.45) * (1.0 - misc.x * 0.7) * (0.55 + 0.45 * lowSun));
  // the sun itself, with a soft limb; clouds in front are drawn over it and take its light
  float disc = smoothstep(0.99955, 0.99985, s);
  col += sunCol * (disc * 14.0 + pow(s, 900.0) * 1.2) * (1.0 - misc.x * 0.85) * misc.y;
  // the dust of the lower air: the horizon goes to the haze of the land; below the horizon the haze itself
  float band = exp(-max(up, 0.0) * 9.0);
  col = mix(col, haze, band * 0.6);
  if (up < 0.0) col = mix(haze, haze * 0.82, clamp(-up * 4.0, 0.0, 1.0));
  // a little dither against banding
  col += (hash(gl_FragCoord.xy) - 0.5) / 255.0;
  gl_FragColor = vec4(col, 1.0);
}`;

/** the sky dome: follows the camera; the gradient, the sun and the haze from `Look` */
export class SkyDome {
  readonly mesh: BABYLON.Mesh;
  private mat: BABYLON.ShaderMaterial;
  constructor(scene: BABYLON.Scene) {
    BABYLON.Effect.ShadersStore['take37SkyVertexShader'] = VS; BABYLON.Effect.ShadersStore['take37SkyFragmentShader'] = FS;
    this.mat = new BABYLON.ShaderMaterial('sky', scene, { vertex: 'take37Sky', fragment: 'take37Sky' }, { attributes: ['position'], uniforms: ['worldViewProjection', 'top', 'horizon', 'haze', 'sunDir', 'sunCol', 'skySun', 'misc'] });
    this.mat.backFaceCulling = false; this.mat.disableDepthWrite = true; this.mat.fogEnabled = false;
    this.mesh = BABYLON.MeshBuilder.CreateSphere('skydome', { diameter: 2, segments: 32 }, scene);
    this.mesh.material = this.mat; this.mesh.infiniteDistance = true; this.mesh.renderingGroupId = 0; this.mesh.isPickable = false; this.mesh.applyFog = false; this.mesh.alwaysSelectAsActiveMesh = true;
  }
  set(l: Look) {
    const v = (a: number[]) => new BABYLON.Vector3(a[0], a[1], a[2]);
    this.mat.setVector3('top', v(l.skyTop)); this.mat.setVector3('horizon', v(l.skyHorizon)); this.mat.setVector3('haze', v(l.hazeColor));
    this.mat.setVector3('sunDir', v(l.sunDir)); this.mat.setVector3('sunCol', v(l.sunColor)); this.mat.setVector3('skySun', v(l.skySun));
    this.mat.setVector4('misc', new BABYLON.Vector4(l.cover, 1, 0, 0));
  }
}
