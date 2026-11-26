"""mythos.py — seventh genre: the chronicle map.

Where what happened: events scattered over the continent by
terrain logic (foundings on coasts, battles at river crossings,
miracles on peaks), connected in time order by a dotted journey
— the geography reads as a story. mu-language names.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'conlang'))

import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from continent import continent, moisture
from gen import word

N = 220
rng = random.Random(11)


def mu_name():
    return ''.join(word(rng) for _ in range(1))[:7].capitalize()


def pick_events(h, m, count=9):
    """sites by terrain preference, spread apart."""
    sea = h < 0.18
    peaks = h > 0.7
    coast = np.zeros_like(sea)
    for y in range(1, N - 1):
        for x in range(1, N - 1):
            if not sea[y, x] and (sea[y + 1, x] or sea[y - 1, x]
                                  or sea[y, x + 1] or sea[y, x - 1]):
                coast[y, x] = True
    lowland = (~sea) & (h < 0.45) & (m > 0.35)
    dry = (~sea) & (m < 0.3)
    deep = (~sea) & (h > 0.4) & (h < 0.65) & (m > 0.55)

    kinds = [
        ('founding', lowland, 'o'),
        ('battle', lowland, 'x'),
        ('miracle', peaks, '*'),
        ('temple', deep, '+'),
        ('famine', dry, 'd'),
        ('founding', lowland, 'o'),
        ('battle', lowland, 'x'),
        ('miracle', peaks, '*'),
        ('crossing', coast, 'v'),
    ]
    events = []
    for kind, mask, glyph in kinds[:count]:
        ys, xs = np.where(mask)
        if len(ys) == 0:
            continue
        order = sorted(zip(ys, xs), key=lambda p: rng.random())
        chosen = None
        for y, x in order[:400]:
            if all((y - ey) ** 2 + (x - ex) ** 2 > 26 ** 2
                   for ey, ex, _, _ in events):
                chosen = (y, x)
                break
        if chosen:
            events.append((chosen[0], chosen[1], kind, glyph))
    events.sort(key=lambda e: e[0] + e[1] * 0.3)  # pseudo-time order
    return events


GLYPH_INK = {'founding': (58, 68, 32), 'battle': (128, 30, 20),
             'miracle': (150, 110, 20), 'temple': (70, 40, 90),
             'famine': (110, 70, 20), 'crossing': (30, 60, 110)}


def render(h, m, events, path):
    img = Image.new('RGB', (N * 3, N * 3 + 90), (232, 216, 178))
    dr = ImageDraw.Draw(img)
    # parchment terrain
    for y in range(N):
        for x in range(N):
            if h[y, x] < 0.18:
                c = (176, 188, 172)   # pale sea
            elif h[y, x] > 0.7:
                c = (150, 128, 100)   # peaks
            elif m[y, x] < 0.3:
                c = (222, 198, 150)   # dry
            elif h[y, x] > 0.45:
                c = (196, 172, 128)   # highland
            else:
                c = (206, 186, 138)   # lowland
            dr.rectangle([x * 3, y * 3, x * 3 + 2, y * 3 + 2], fill=c)
    try:
        font = ImageFont.truetype('arial.ttf', 17)
        small = ImageFont.truetype('arial.ttf', 13)
    except OSError:
        font = small = ImageFont.load_default()
    # journey: dotted line in time order
    pts = [(x * 3 + 1, y * 3 + 1) for y, x, _, _ in events]
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        steps = max(2, int(np.hypot(x2 - x1, y2 - y1) / 7))
        for s in range(steps):
            if s % 2 == 0:
                t = s / steps
                dr.ellipse([x1 + (x2 - x1) * t - 1, y1 + (y2 - y1) * t - 1,
                            x1 + (x2 - x1) * t + 1, y1 + (y2 - y1) * t + 1],
                           fill=(90, 50, 30))
    # events: numbered marks
    names = []
    for i, (y, x, kind, glyph) in enumerate(events):
        cx, cy = x * 3 + 1, y * 3 + 1
        ink = GLYPH_INK[kind]
        dr.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=ink, width=2)
        dr.text((cx - 3, cy - 9), str(i + 1), fill=ink, font=small)
        names.append((i + 1, mu_name(), kind))
    # legend
    ly = N * 3 + 8
    dr.text((10, ly), 'chronicle of the continent — where what happened',
            fill=(70, 45, 25), font=font)
    line = '  '.join(f'{n}. {nm} ({k})' for n, nm, k in names[:5])
    dr.text((10, ly + 32), line, fill=(90, 60, 35), font=small)
    line2 = '  '.join(f'{n}. {nm} ({k})' for n, nm, k in names[5:])
    dr.text((10, ly + 52), line2, fill=(90, 60, 35), font=small)
    img.save(path)


if __name__ == '__main__':
    h = continent(N)
    m = moisture(N)
    ev = pick_events(h, m)
    render(h, m, ev, os.path.join(os.path.dirname(__file__),
                                  'mythos.png'))
    print('events:', [(k, (y, x)) for y, x, k, _ in ev])
