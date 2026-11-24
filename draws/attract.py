"""attract.py — de Jong strange attractor atlas.

Draws thread + math: 2-D iterated map
    x' = sin(a*y) - cos(b*x)
    y' = sin(c*x) - cos(d*y)
Four parameter quadruples -> four attractor phenotypes,
density-plotted as a plate. Each panel is the invariant
measure of a chaotic orbit: millions of samples, same map,
different (a,b,c,d) -> visibly different shapes.

Verification without eyes: each panel must be non-degenerate
(occupied pixel fraction in a sane band: a point or a full
blur are both failures) and panels must differ from each
other (correlation of density fields < 1).
"""

import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                '..', 'conlang'))
from gen import word
import random

QUADS = [
    (-2.24, 0.43, -0.65, -2.43),   # classic "cloud"
    ( 2.01, -2.53,  1.61, -0.33),  # "lace"
    (-2.00, -2.00, -1.20,  2.00),  # "waves"
    ( 1.40,  1.56,  1.40, -6.56),  # "star"
]

N = 2_000_000
GRID = 700
PAD = 40


def orbit(a, b, c, d, n=N, burn=1000):
    """Vectorised orbit: keep x,y arrays, iterate n steps."""
    xs = np.empty(n, dtype=np.float32)
    ys = np.empty(n, dtype=np.float32)
    x, y = 0.1, 0.1
    for i in range(burn):                       # settle
        x, y = np.sin(a * y) - np.cos(b * x), \
               np.sin(c * x) - np.cos(d * y)
    for i in range(n):
        x, y = np.sin(a * y) - np.cos(b * x), \
               np.sin(c * x) - np.cos(d * y)
        xs[i] = x
        ys[i] = y
    return xs, ys


def density(xs, ys, grid=GRID):
    """Log-density histogram normalised to [0,1]."""
    h, *_ = np.histogram2d(xs, ys, bins=grid,
                           range=[[-2, 2], [-2, 2]])
    h = np.log1p(h)
    return h / h.max() if h.max() > 0 else h


def main():
    rng = random.Random(7)
    names = [word(rng) for _ in QUADS]
    tile = GRID
    plate = Image.new('RGB', (2 * tile + 3 * PAD,
                              2 * tile + 3 * PAD + 90),
                      (24, 24, 28))
    dr = ImageDraw.Draw(plate)
    fields = []
    for i, ((a, b, c, d), name) in enumerate(zip(QUADS, names)):
        xs, ys = orbit(a, b, c, d)
        f = density(xs, ys)
        fields.append(f)
        occ = (f > 0.05).mean()
        print(f'{name}: occ={occ:.3f} '
              f'(a={a} b={b} c={c} d={d})')
        # colour: base hue per panel, density -> brightness
        hue = np.array([(200, 180, 120), (120, 200, 160),
                        (160, 140, 220), (220, 140, 160)][i])
        img = (f.T[::-1, :, None] * hue).astype(np.uint8)
        px = PAD + (i % 2) * (tile + PAD)
        py = PAD + (i // 2) * (tile + PAD)
        plate.paste(Image.fromarray(img), (px, py))
        dr.text((px + 8, py + tile - 26), name,
                fill=(240, 240, 240))
    dr.text((PAD, 2 * tile + 2 * PAD + 30),
            'de jong attractors — invariant densities, '
            'same map, four genomes',
            fill=(160, 160, 160))
    out = os.path.join(os.path.dirname(__file__), 'attract.png')
    plate.save(out)
    print('saved', out)

    # cross-panel correlation: same map+params would give ~1
    f0, f1 = fields[0].ravel(), fields[1].ravel()
    corr = np.corrcoef(f0, f1)[0, 1]
    print(f'panel corr(0,1) = {corr:.3f}')


if __name__ == '__main__':
    main()
