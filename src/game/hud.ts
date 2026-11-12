// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// What the player reads: the budget and the take number, the clapperboard, the speed, the director's captions, the pause. Points are never shown. VIEW FILE (DOM).
import type { Take } from './take';

const money = (n: number) => '$' + Math.round(n).toLocaleString('en-US');

export class Hud {
  private el: Record<string, HTMLElement> = {};
  constructor(private root: HTMLElement) {
    root.innerHTML = `
      <div id="h-top"><span id="h-budget"></span><span id="h-take"></span></div>
      <div id="h-speed"></div>
      <div id="h-hint"></div>
      <div id="h-board"><div class="b-title">TAKE 37</div><div class="b-row"><span>SCENE</span><b id="b-scene">1</b><span>TAKE</span><b id="b-take"></b></div><div class="b-sticks"></div></div>
      <div id="h-call"></div>
      <div id="h-caption"></div>
      <div id="h-menu"></div>
      <div id="h-pause">PAUSED<br><small>Esc to continue</small></div>`;
    for (const id of ['h-top', 'h-budget', 'h-take', 'h-speed', 'h-hint', 'h-board', 'b-take', 'h-call', 'h-caption', 'h-menu', 'h-pause']) this.el[id] = root.querySelector('#' + id) as HTMLElement;
  }
  private set(id: string, text: string) { const e = this.el[id]!; if (e.textContent !== text) e.textContent = text; }
  private show(id: string, on: boolean) { this.el[id]!.style.display = on ? '' : 'none'; }
  update(take: Take, speedMps: number, paused: boolean, prompt: (a: string) => string) {
    this.set('h-budget', 'Budget ' + money(take.budget)); this.set('h-take', take.takeNo ? 'Scene 1, take ' + take.takeNo : '');
    this.set('h-speed', Math.round(Math.abs(speedMps) * 2.237) + ' mph');
    this.el['h-pause']!.style.display = paused ? 'flex' : 'none';
    const ph = take.phase;
    this.show('h-board', ph === 'clapper'); this.set('b-take', String(take.takeNo));
    this.el['h-board']!.classList.toggle('snap', ph === 'clapper' && take.phaseT > 1.7);
    const call = this.el['h-call']!;
    const brief = ph === 'brief';
    this.show('h-hint', brief || (ph === 'play' && take.t < 14));
    this.set('h-hint', brief ? `Scene 1. Edward has his camera on the street. Vincent's Corvette is ahead. Stay on him and give the director a spectacle.\nGas ${prompt('gas')}   Brake ${prompt('brake')}   Steer ${prompt('steer')}   Handbrake ${prompt('handbrake')}   Siren ${prompt('siren')}   Horn ${prompt('horn')}   Look back ${prompt('lookback')}   Jump out ${prompt('jump')}   Call "Cut" ${prompt('cut')}` : `Gas ${prompt('gas')}  Brake ${prompt('brake')}  Handbrake ${prompt('handbrake')}  Siren ${prompt('siren')}  Look back ${prompt('lookback')}  Jump out ${prompt('jump')}  Cut ${prompt('cut')}`);
    let text = '', cls = '';
    if (ph === 'clapper') { text = take.phaseT < 1.5 ? 'Scene 1, take ' + take.takeNo : 'Action!'; cls = 'slate'; }
    else if (ph === 'verdict' && take.outcome) { text = take.outcome.verdict === 'wrap' ? "That's a wrap!" : 'Cut!'; cls = take.outcome.verdict; }
    else if (ph === 'over') { text = 'The money is gone. The studio pulls the plug.'; cls = 'cut'; }
    call.className = cls; this.set('h-call', text); this.show('h-call', !!text);
    const cap = ph === 'verdict' || ph === 'choice' ? take.outcome?.text ?? '' : '';
    this.set('h-caption', cap); this.show('h-caption', !!cap && take.phaseT > 1.2 || ph === 'choice');
    const menu = this.el['h-menu']!;
    if (ph === 'choice') { const b = take.best; menu.innerHTML = `<div>Budget ${money(take.budget)}. Another take costs ${money(1_000_000)}.</div>${b ? `<div class="best">Best take so far: take ${b.take}</div>` : ''}<div class="go">${prompt('accept')}: another take</div>`; menu.style.display = ''; }
    else if (ph === 'over') { menu.innerHTML = `<div class="go">${prompt('accept')}: start over with a new budget</div>`; menu.style.display = ''; }
    else menu.style.display = 'none';
  }
}

export const HUD_CSS = `
#hud2 { position: fixed; inset: 0; pointer-events: none; font-family: Georgia, 'Times New Roman', serif; color: #f2ecdd; text-shadow: 0 1px 3px #000; }
#hud2 #h-top { position: absolute; left: 18px; top: 14px; display: flex; gap: 28px; font: 600 20px ui-monospace, Consolas, monospace; letter-spacing: .04em; }
#hud2 #h-speed { position: absolute; right: 24px; bottom: 18px; font: 700 34px ui-monospace, Consolas, monospace; }
#hud2 #h-hint { position: absolute; left: 50%; bottom: 6%; transform: translateX(-50%); width: min(900px, 92vw); text-align: center; font: 15px/1.45 system-ui, sans-serif; white-space: pre-wrap; background: rgba(8,8,10,.55); padding: 10px 14px; border-radius: 6px; }
#hud2 #h-board { position: absolute; left: 50%; top: 50%; transform: translate(-50%,-50%) rotate(-2deg); width: min(520px, 80vw); background: #17171a; border: 6px solid #f2ecdd; padding: 14px 18px; text-shadow: none; }
#hud2 #h-board.snap { transform: translate(-50%,-50%) rotate(-2deg) scaleY(.92); }
#hud2 .b-title { font: 700 36px Georgia, serif; letter-spacing: .3em; text-align: center; }
#hud2 .b-row { display: flex; gap: 14px; align-items: baseline; justify-content: center; font: 22px ui-monospace, Consolas, monospace; } #hud2 .b-row b { font-size: 46px; color: #ffd45a; }
#hud2 #h-call { position: absolute; left: 50%; top: 34%; transform: translateX(-50%); font: 700 clamp(40px, 9vw, 120px)/1 Georgia, serif; letter-spacing: .06em; text-align: center; width: 96vw; }
#hud2 #h-call.cut { color: #ff5a4a; } #hud2 #h-call.wrap { color: #ffd45a; } #hud2 #h-call.slate { font-size: clamp(30px, 6vw, 70px); }
#hud2 #h-caption { position: absolute; left: 50%; bottom: 12%; transform: translateX(-50%); width: min(980px, 92vw); text-align: center; font: italic 24px/1.4 Georgia, serif; background: rgba(8,8,10,.62); padding: 12px 18px; border-radius: 6px; }
#hud2 #h-menu { position: absolute; left: 50%; top: 56%; transform: translateX(-50%); text-align: center; font: 22px/1.6 system-ui, sans-serif; background: rgba(8,8,10,.6); padding: 12px 22px; border-radius: 6px; } #hud2 #h-menu .go { color: #ffd45a; font-weight: 700; }
#hud2 #h-pause { position: absolute; inset: 0; background: rgba(0,0,0,.55); display: none; flex-direction: column; align-items: center; justify-content: center; text-align: center; font: 700 64px Georgia, serif; padding-top: 30vh; } #hud2 #h-pause small { font-size: 28px; font-weight: 400; }
`;
