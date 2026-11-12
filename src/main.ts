// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { buildSet } from './scene/set';

/**
 * The set scene: the street, the gas station, the platform and the land round it, in the weather of `src/config/weather.ts`.
 * Address options: `?weather=clear|light-cloud|strong-wind|sunset`, `?hour=15.5`, `?lite=1` (a lighter picture), `?view=cab|cabMid|sunsetFromEnd|street|hill|air|ground`.
 * Fly with W A S D and the mouse (click the picture), E and Q up and down; keys 1 to 6 jump to the views, [ and ] change the hour.
 */
const $ = (id: string) => document.getElementById(id)!;
const q = new URLSearchParams(location.search);
const splash = {
  set(p: number, text: string) { const b = document.getElementById('splashbar'), t = document.getElementById('splashtxt'); if (b) b.style.width = Math.round(p * 100) + '%'; if (t) t.textContent = text; },
  hide() { const e = document.getElementById('splash'); if (e) { e.classList.add('gone'); setTimeout(() => e.remove(), 900); } },
};

async function main() {
  $('splashver').textContent = (globalThis as { __TAKE37_BUILD__?: string }).__TAKE37_BUILD__ ?? '';
  const set = await buildSet($('c') as HTMLCanvasElement, q, (p, t) => splash.set(p, t));
  const names = ['cab', 'cabMid', 'sunsetFromEnd', 'street', 'hill', 'air'] as const;
  const go = (n: string) => set.goto(n);
  addEventListener('keydown', (e) => {
    const i = '123456'.indexOf(e.key); if (i >= 0) void go(names[i]);
    if (e.key === '[') set.setHour(set.look().elevation * 0 + (((set.preset.hour) as number) - 0.5));
  });
  const hud = $('hud'), gpu = set.renderer();
  setInterval(() => {
    const s = set.stats(), w = set.weather.state;
    hud.textContent = `${set.presetName}: ${set.preset.description}\nwind ${w.wind.toFixed(1)} m/s from ${((w.windDir + 180) % 360).toFixed(0)}  gust ${w.gustiness.toFixed(2)}  cloud ${(w.cloudCover * 100).toFixed(0)}%  sun ${(Math.asin(set.look().sunDir[1]) * 180 / Math.PI).toFixed(1)} deg\n`
      + `${gpu.renderer}\n${s.fps} fps  terrain ${s.chunks} chunks ${(+s.triangles / 1000).toFixed(0)}k tris  oaks ${s.oaks} bushes ${s.bushes} stones ${s.stones}`;
  }, 400);
  (window as unknown as Record<string, unknown>).take37 = set;
  const start = q.get('view');
  if (start) await go(start);
  splash.hide();
  (window as unknown as Record<string, unknown>).take37Ready = true;
}

main().catch((e) => { console.error(e); (window as unknown as Record<string, unknown>).take37Error = String(e?.stack ?? e); });
