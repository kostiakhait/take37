// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The sounds of the cab: engine, horn, siren, crashes and blasts, synthesized (WebAudio). The recorded sounds come later; the calls here stay.
import type { SimEvent } from './sim';

export class CabAudio {
  private ctx: AudioContext | null = null;
  private engine!: OscillatorNode; private engineGain!: GainNode; private hornGain!: GainNode; private sirenOsc!: OscillatorNode; private sirenGain!: GainNode; private master!: GainNode; private noise!: AudioBuffer;
  private started = false;

  /** browsers want a gesture first: call from a key or a click */
  start() {
    if (this.started) { void this.ctx?.resume(); return; }
    try {
      const ctx = this.ctx = new AudioContext(); this.started = true;
      this.master = ctx.createGain(); this.master.gain.value = 0.5; this.master.connect(ctx.destination);
      this.engine = ctx.createOscillator(); this.engine.type = 'sawtooth'; this.engine.frequency.value = 40; this.engineGain = ctx.createGain(); this.engineGain.gain.value = 0;
      const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 420; this.engine.connect(lp); lp.connect(this.engineGain); this.engineGain.connect(this.master); this.engine.start();
      this.hornGain = ctx.createGain(); this.hornGain.gain.value = 0; this.hornGain.connect(this.master);
      for (const f of [392, 494]) { const o = ctx.createOscillator(); o.type = 'square'; o.frequency.value = f; o.connect(this.hornGain); o.start(); }
      this.sirenOsc = ctx.createOscillator(); this.sirenOsc.type = 'triangle'; this.sirenOsc.frequency.value = 700; this.sirenGain = ctx.createGain(); this.sirenGain.gain.value = 0; this.sirenOsc.connect(this.sirenGain); this.sirenGain.connect(this.master); this.sirenOsc.start();
      this.noise = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate); const d = this.noise.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    } catch { this.ctx = null; }
  }
  /** each frame: the speed of the player's car (m/s), the throttle, the horn and the siren */
  update(speed: number, throttle: number, horn: boolean, siren: boolean, t: number) {
    const c = this.ctx; if (!c) return;
    const now = c.currentTime;
    this.engine.frequency.setTargetAtTime(38 + Math.abs(speed) * 3.2 + throttle * 14, now, 0.08);
    this.engineGain.gain.setTargetAtTime(0.06 + 0.05 * throttle, now, 0.1);
    this.hornGain.gain.setTargetAtTime(horn ? 0.12 : 0, now, 0.02);
    this.sirenGain.gain.setTargetAtTime(siren ? 0.1 : 0, now, 0.05);
    if (siren) this.sirenOsc.frequency.setTargetAtTime(900 + 450 * Math.sin(t * 5.2), now, 0.03);
  }
  private burst(gain: number, dur: number, cutoff: number, at = 0) {
    const c = this.ctx; if (!c) return;
    const s = c.createBufferSource(); s.buffer = this.noise; const f = c.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = cutoff; const g = c.createGain();
    g.gain.setValueAtTime(gain, c.currentTime + at); g.gain.exponentialRampToValueAtTime(0.001, c.currentTime + at + dur);
    s.connect(f); f.connect(g); g.connect(this.master); s.start(c.currentTime + at, Math.random()); s.stop(c.currentTime + at + dur + 0.05);
  }
  /** a sim event heard from the player's car at distance `d` */
  hear(e: SimEvent, d: number) {
    if (!this.ctx) return;
    const near = 1 / (1 + d / 25);
    if (e.type === 'impact' && e.speed > 2) this.burst(Math.min(1, e.speed / 14) * near, 0.35, 1800 + e.speed * 80);
    else if (e.type === 'detach') this.burst(0.5 * near, 0.5, 3500);
    else if (e.type === 'wreck') this.burst(0.8 * near, 0.9, 1200);
    else if (e.type === 'blast') this.burst(Math.min(1.5, 0.4 + Math.log10(1 + e.tnt) * 0.5) * (0.3 + near), 2.4, 260, d / 340);
    else if (e.type === 'ignite') this.burst(0.3 * near, 0.6, 700);
  }
}
