"""runseal.py — печать конкретного прогона (Ex Libris эксперимента).

Named step from INTERESTS: each significant run gets a seal —
a procedural glyph built from its own metrics.

Design: a circular wreath. Each census tick maps to an angle;
prey population -> petal length (radial), predator count ->
petal warmth (red), food -> base ring thickness. Same layout,
same data -> same seal: the run is reproducible, so is its
stamp. Paired runs (terr home vs deaf — differ only in the
mark mechanic) produce paired seals where the visible
difference IS the experiment.

Output: runseal.png — paired seals for terr s7/s8 pairs.
"""

import csv
import math
import os
from PIL import Image, ImageDraw

R_IN, R_OUT = 90, 300
TILE = 2 * (R_OUT + 40)


def load(path):
    rows = list(csv.DictReader(open(path)))
    return rows


def seal(rows, label):
    """Rows -> tile image with the wreath + caption."""
    img = Image.new('RGB', (TILE, TILE), (18, 18, 22))
    dr = ImageDraw.Draw(img)
    cx = cy = TILE // 2
    n = len(rows)
    prey = [float(r['pop_prey']) for r in rows]
    pred = [float(r['pop_pred']) for r in rows]
    food = [float(r['food']) for r in rows]
    pmax = max(prey) or 1
    fmax = max(food) or 1
    prmax = max(pred) or 1

    # base ring — food level modulates thickness
    for i, f in enumerate(food):
        a0 = 2 * math.pi * i / n
        a1 = 2 * math.pi * (i + 1) / n
        r = R_IN + 8 + 26 * (f / fmax)
        dr.arc([cx - r, cy - r, cx + r, cy + r],
               math.degrees(a0), math.degrees(a1),
               fill=(60, 90, 60), width=3)

    # petals — prey population outward, predators tint
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        r0 = R_IN + 12
        r1 = R_IN + 12 + (R_OUT - R_IN - 30) * (prey[i] / pmax)
        warm = int(200 * pred[i] / prmax)
        col = (min(255, 120 + warm), 170 - warm // 2,
               140 - warm // 3)
        x0, y0 = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
        x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
        dr.line([x0, y0, x1, y1], fill=col, width=2)
        dr.ellipse([x1 - 1.5, y1 - 1.5, x1 + 1.5, y1 + 1.5],
                   fill=col)

    # hanko core: run label + tick span
    dr.ellipse([cx - R_IN, cy - R_IN, cx + R_IN, cy + R_IN],
               outline=(200, 180, 140), width=2)
    dr.text((cx, cy - 18), label, anchor='mm',
            fill=(235, 220, 180))
    dr.text((cx, cy + 6), f"{int(rows[-1]['tick'])} ticks",
            anchor='mm', fill=(150, 140, 120))
    dr.text((cx, cy + 26),
            f"peak prey {int(pmax)}",
            anchor='mm', fill=(120, 115, 100))
    return img


def main():
    base = os.path.join(os.path.dirname(__file__), '..', 'runs')
    pairs = [
        ('terr/s7_home.csv', 'terr/s7_deaf.csv', 's7'),
        ('terr/s8_home.csv', 'terr/s8_deaf.csv', 's8'),
    ]
    plate = Image.new('RGB', (2 * TILE + 60,
                              len(pairs) * TILE + 40 *
                              (len(pairs) + 1)), (24, 24, 28))
    dr = ImageDraw.Draw(plate)
    for row, (ha, da, tag) in enumerate(pairs):
        y = 40 + row * (TILE + 40)
        for col, (path, name) in enumerate(
                ((ha, 'home'), (da, 'deaf'))):
            img = seal(load(os.path.join(base, path)),
                       f'{tag} · {name}')
            plate.paste(img, (40 + col * (TILE + 40), y))
        dr.text((40, y - 22),
                f'terr {tag}: identical sims, one difference '
                f'— territorial marks', fill=(140, 140, 140))
    out = os.path.join(os.path.dirname(__file__), 'runseal.png')
    plate.save(out)
    print('saved', out)


if __name__ == '__main__':
    main()
