"""continent.py — edge of a continent, biomes, toponymy in mu.

Island asked "what does a place look like". Continent asks
"what does a LAND look like" — no radial mask: the mass runs
off the north/east edges, ocean takes south/west.

Biomes = elevation x moisture (two independent noise fields).
Toponymy = first SEMANTIC use of mu: place names built by the
language's own morphology, not a label generator:
  kuwa+ka  -> KUWAKA   "the sea"      (definite)
  poka+in  -> POKAJIN  "mountains"    (plural, glide j)
  sumno+an -> SUMNOWAN "the sands"    (collective, glide w)
  komu+an  -> KOMUWAN  "the forests"  (collective)
  rija X   -> river names
All-caps romanization is a cartographic convention.
"""

import sys
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'conlang'))
from island import octave_noise, rivers  # noqa: E402
import island  # noqa: E402
from gen import word  # noqa: E402
import random  # noqa: E402

SEED = 7
island.rng = np.random.default_rng(SEED)  # reproducible artifact
rng = np.random.default_rng(SEED + 1)
mrng = random.Random(3105)
N = 256

# --- mu toponymic lexicon (first semantic layer, fixed here) ---
MU = {'sea': 'kuwa', 'mountain': 'poka', 'sand': 'sumno',
      'forest': 'komu', 'river': 'rija'}


def mu_join(stem, suffix):
    """morph.join inlined (conlang has no package init)."""
    if suffix[0] in 'aeiou' and stem[-1] in 'aeiou':
        g = 'w' if stem[-1] in 'ou' else 'j'
        return stem + g + suffix
    return stem + suffix


TOPO = {
    'sea': mu_join(MU['sea'], 'ka').upper(),          # KUWAKA
    'range': mu_join(MU['mountain'], 'in').upper(),   # POKAJIN
    'desert': mu_join(MU['sand'], 'an').upper(),      # SUMNOWAN
    'forest': mu_join(MU['forest'], 'an').upper(),    # KOMUWAN
}


def continent(n):
    """Heightmap: ocean west+south, landmass off north+east."""
    h = sum(octave_noise(n, c) * w
            for c, w in [(8, 1.0), (16, 0.5), (32, 0.25), (64, 0.12)])
    h /= 1.87
    y, x = np.mgrid[0:n, 0:n] / n
    # edge falloff: only west + south coasts — the land continues
    # off-map to the north and east = a continent's edge
    fall = np.clip((0.30 - x) * 4, 0, 1) + np.clip((y - 0.78) * 4, 0, 1)
    h -= np.clip(fall, 0, 1) * 0.8
    return np.clip(h, 0, 1)


def moisture(n):
    m = sum(octave_noise(n, c) * w
            for c, w in [(6, 1.0), (24, 0.4)])
    m /= 1.4
    y, x = np.mgrid[0:n, 0:n] / n
    return np.clip(m * 0.75 + y * 0.35, 0, 1)  # wetter south (coast)


def render(h, m, flow, path):
    n = h.shape[0]
    img = np.zeros((n, n, 3), np.uint8)
    land = h >= 0.40
    # sea
    img[~land] = (46, 78, 105)
    img[h < 0.34] = (36, 62, 88)
    # biomes on land
    img[land] = (126, 158, 88)  # default: grass — no gaps
    desert = land & (m < 0.38) & (h < 0.62)
    steppe = land & (m >= 0.38) & (m < 0.52) & (h < 0.62)
    forest = land & (m >= 0.70) & (h < 0.70)
    taiga = land & (m >= 0.70) & (h >= 0.70) & (h < 0.80)
    highl = land & (h >= 0.62) & (h < 0.70) & (m < 0.70)
    mount = land & (h >= 0.70) & ~taiga
    snow = h >= 0.86
    img[desert] = (208, 183, 125)
    img[steppe] = (178, 172, 106)
    img[forest] = (74, 118, 66)
    img[taiga] = (56, 92, 74)
    img[highl] = (168, 150, 112)
    img[mount] = (148, 135, 115)
    img[snow] = (235, 232, 224)
    # relief shade — land only; sea/lakes stay flat
    shade = np.roll(h, (1, 1), (0, 1)) - h
    img = np.clip(img + (np.clip(shade, -0.08, 0.08)[:, :, None]
                         * 120 * land[:, :, None]),
                  0, 255).astype(np.uint8)
    # rivers
    img[flow > 0] = (70, 112, 152)
    img[flow > 4] = (96, 140, 182)

    pil = Image.fromarray(img).resize((n * 3, n * 3), Image.NEAREST)
    dr = ImageDraw.Draw(pil)
    f = ImageFont.load_default()

    def label(mask, text, color, k=1):
        pts = np.argwhere(mask)
        if not len(pts):
            return
        y, x = pts[len(pts) // 2]
        dr.text((x * 3 + 3, y * 3 - 4), text, fill=color, font=f)

    label(~land & (np.mgrid[0:n, 0:n][0] > n * 0.80), TOPO['sea'],
          (220, 228, 235))
    label(mount, TOPO['range'], (60, 52, 44))
    label(desert, TOPO['desert'], (110, 88, 50))
    label(forest, TOPO['forest'], (215, 225, 205))
    # rivers: two biggest channels get 'rija X'
    big = np.argwhere(flow > 8)
    for k in rng.permutation(len(big))[:2] if len(big) else []:
        y, x = big[k]
        dr.text((x * 3 + 4, y * 3 - 4),
                f'{MU["river"]} {word(mrng)}', fill=(210, 220, 230), font=f)
    # cities on coast
    beach = land & (h < 0.44)
    for k in rng.permutation(len(np.argwhere(beach)))[:5]:
        y, x = np.argwhere(beach)[k]
        dr.text((x * 3 + 4, y * 3), word(mrng).capitalize(),
                fill=(245, 240, 228), font=f)
        dr.point((x * 3, y * 3), fill=(245, 240, 228))
    pil.save(path)
    return pil


if __name__ == '__main__':
    h = continent(N)
    m = moisture(N)
    f = rivers(h)
    render(h, m, f, 'maps/continent.png')
    print('continent rendered -> maps/continent.png')
    print('toponymy:', TOPO)
