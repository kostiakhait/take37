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
export const OUTFITS = {
  // Matthew: T-shirt, jeans, boots
  matthew: outfit([['trousers', { seatEase: 0.1, waistEase: 0.04, hem: 0.46 }, 'denim', 0x1c3a66], ['tshirt', { neckline: 'crew', length: 'hip' }, 'jersey knit', 0xd8d8d2]], { boots: { shaft: 0.12, eyelets: 6 } }),
  // Arnold: double-breasted suit, white shirt
  arnold: outfit([['trousers', { seatEase: 0.12, waistEase: 0.03, rise: 0.03, hem: 0.5 }, 'flannel', 0x3a3e4c], ['shirt', { collar: 'shirt', closure: 'single', sleeve: 'set-in' }, 'cotton shirting', 0xf0eee8],
    ['jacket', { buttonRows: 2, lapel: 0.09 }, 'wool serge', 0x3c4152]], { boots: { shaft: 0.07, eyelets: 0 } }),
  // Emily: a dress for each scene
  emilyA: outfit([['dress', { cut: 'fitted', sleeves: 'short', length: 'knee', neckline: 'vee' }, 'velvet', 0xa81c24]]),
  emilyB: outfit([['dress', { cut: 'aline', sleeves: 'none', length: 'midi', neckline: 'square' }, 'silk', 0x30b0b0]]),
  emilyC: outfit([['dress', { cut: 'shift', sleeves: 'long', length: 'knee', neckline: 'scoop' }, 'wool serge', 0x5a1020]]),
  // Vincent: hooded robe to the ankle
  vincent: outfit([['hoodie', { length: 'calf', ease: 0.3, sleeve: 'drop', hood: { up: true, deeper: 0.08 } }, 'wool serge', 0x34323f]]),
  // Edward: oversized hoodie and wide trousers
  edward: outfit([['trousers', { seatEase: 0.4, waistEase: 0.06, knee: 0.7, hem: 0.62 }, 'canvas', 0x5a6030], ['tshirt', { length: 'hip', ease: 0.34, sleeve: 'drop', neckline: 'crew' }, 'jersey knit', 0xc8a020]], { boots: { shaft: 0.1, eyelets: 6 } }),
  // Director: corduroy trousers, shirt, vest
  director: outfit([['trousers', { seatEase: 0.12 }, 'corduroy', 0x5a4a30], ['shirt', { collar: 'shirt', closure: 'single', sleeve: 'set-in' }, 'cotton shirting', 0xb8ae88], ['waistcoat', {}, 'canvas', 0x6a6040]], { boots: { shaft: 0.1, eyelets: 6 } }),
}
