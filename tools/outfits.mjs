// Outfits of the six TAKE 37 characters, sewn on the body by the clothing module (library).
import { C } from 'file:///D:/REPO/ferret/tools/clothing/bundle.mjs'
const F = (name, color) => C.fabricFor(name, color)
function outfit(parts, extra = {}) {
  const fabrics = {}, specs = []
  for (const [block, style, fab, color] of parts) { const f = F(fab, color); fabrics[block] = f.spec; specs.push([block, { ...style, fabric: block }]) }
  fabrics.rib = F('rib knit', 0x303030).spec; fabrics.knit = F('jersey knit', 0x303030).spec
  fabrics.leather = { weave: 'leather', color: [0.02, 0.012, 0.008], roughness: 0.45, depth: 0.00025, wear: 0.4 }
  return { garments: (Cc, body, m) => specs.map(([b, s]) => Cc[b](body, m, s)), fabrics, buttons: 'horn', ...extra }
}
// Emily's shoes: pumps (low cut, 7 cm heel) on the clothing module's last
const PUMPS = { shaft: 0.03, heel: 0.04, sole: 0.012, room: 0.003, eyelets: 1 }
export const OUTFITS = {
  // Matthew: T-shirt, jeans, boots
  matthew: outfit([['trousers', { seatEase: 0.1, waistEase: 0.04, hem: 0.46 }, 'denim', 0x1c3a66], ['tshirt', { neckline: 'crew', length: 'hip' }, 'jersey knit', 0xd8d8d2]], { boots: { shaft: 0.12, eyelets: 6 } }),
  // Arnold: double-breasted suit, white shirt
  arnold: outfit([['trousers', { seatEase: 0.12, waistEase: 0.03, rise: 0.03, hem: 0.5 }, 'flannel', 0x3a3e4c], ['shirt', { collar: 'shirt', closure: 'single', sleeve: 'set-in' }, 'cotton shirting', 0xf0eee8],
    ['jacket', { buttonRows: 2, lapel: 0.09 }, 'wool serge', 0x3c4152]], { boots: { shaft: 0.05, eyelets: 3 } }),
  // Emily: a dress for each scene
  emilyA: outfit([['dress', { cut: 'fitted', sleeves: 'short', length: 'knee', neckline: 'vee' }, 'velvet', 0xa81c24]], { boots: PUMPS }),
  emilyB: outfit([['dress', { cut: 'aline', sleeves: 'none', length: 'midi', neckline: 'square' }, 'silk', 0x30b0b0]], { boots: PUMPS }),
  emilyC: outfit([['dress', { cut: 'shift', sleeves: 'long', length: 'knee', neckline: 'scoop' }, 'wool serge', 0x5a1020]], { boots: PUMPS }),
  // Vincent: hooded robe to the ankle
  vincent: outfit([['hoodie', { length: 'calf', ease: 0.3, sleeve: 'drop', hood: { up: true, deeper: 0.08 } }, 'wool serge', 0x34323f]]),
  // Edward: oversized hoodie and wide trousers
  edward: outfit([['trousers', { seatEase: 0.4, waistEase: 0.06, knee: 0.7, hem: 0.62 }, 'canvas', 0x5a6030], ['tshirt', { length: 'hip', ease: 0.26, sleeve: 'set-in', neckline: 'crew' }, 'jersey knit', 0xc8a020]], { boots: { shaft: 0.1, eyelets: 6 } }),
  // Director: corduroy trousers, shirt, vest
  director: outfit([['trousers', { seatEase: 0.12 }, 'corduroy', 0x5a4a30], ['shirt', { collar: 'shirt', closure: 'single', sleeve: 'set-in' }, 'cotton shirting', 0xb8ae88], ['waistcoat', {}, 'canvas', 0x6a6040]], { boots: { shaft: 0.1, eyelets: 6 } }),
}
// patent leather for the pumps: red with the red dress, black with the others
for (const [k, c] of [['emilyA', [0.4, 0.02, 0.03]], ['emilyB', [0.02, 0.02, 0.025]], ['emilyC', [0.03, 0.01, 0.015]]]) OUTFITS[k].fabrics.leather = { weave: 'leather', color: c, roughness: 0.22, depth: 0.00005, wear: 0 }
