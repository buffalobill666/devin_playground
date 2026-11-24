"""transit.py — schematic transit map of the continent.

Same world, different cartographic genre: continent.py gives
real geography (seed 7); this draws the metro map over it —
coastal cities connected by MST, chains decomposed into
named lines, drawn schematically over a faint landmass
silhouette. Stations get mu names (conlang/gen).

Lines: maximal chains between terminals/branch nodes.
Interchanges: degree >= 3 or shared by two lines.
"""

import os
import sys
import random
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'conlang'))
import continent as cm                       # noqa: E402
from gen import word                          # noqa: E402

N, K = 256, 9
SEED = 7


def pick_cities(h, rng):
    beach = (h >= 0.40) & (h < 0.46)
    pts = np.argwhere(beach)
    sel = [tuple(pts[rng.integers(len(pts))])]
    while len(sel) < K:
        c = pts[rng.integers(len(pts))]
        d = min((c[0] - s[0]) ** 2 + (c[1] - s[1]) ** 2
                for s in sel)
        if d > 24 ** 2:
            sel.append(tuple(c))
    return sel


def mst(pts):
    n = len(pts)
    inT = {0}
    edges = []
    while len(inT) < n:
        best = None
        for i in inT:
            for j in range(n):
                if j in inT:
                    continue
                d = (pts[i][0] - pts[j][0]) ** 2 + \
                    (pts[i][1] - pts[j][1]) ** 2
                if best is None or d < best[0]:
                    best = (d, i, j)
        edges.append((best[1], best[2]))
        inT.add(best[2])
    return edges


def lines_from_edges(edges, n):
    """Decompose tree into maximal chains between terminals
    (deg==1) and branch nodes (deg>=3)."""
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    deg = {i: len(adj[i]) for i in range(n)}
    lines = []
    seen = set()
    for start in range(n):
        if deg[start] == 2:
            continue
        for nxt in adj[start]:
            if (start, nxt) in seen:
                continue
            chain = [start]
            prev, cur = start, nxt
            while True:
                seen.add((prev, cur))
                seen.add((cur, prev))
                chain.append(cur)
                if deg[cur] != 2:
                    break
                a, b = adj[cur]
                prev, cur = cur, b if a == prev else a
            lines.append(chain)
    return lines, deg


COLORS = [(192, 57, 43), (41, 84, 144), (46, 125, 50),
          (170, 110, 40), (120, 60, 140), (60, 130, 130)]


def render(h, cities, lines, names, lnames, path):
    S = 3
    land = h >= 0.40
    img = np.full((N, N, 3), 252, np.uint8)
    img[land] = (232, 228, 218)                    # faint land
    img[~land] = (222, 234, 244)                   # pale sea
    pil = Image.fromarray(img).resize(
        (N * S, N * S), Image.NEAREST)
    d = ImageDraw.Draw(pil)
    P = [(c[1] * S, c[0] * S) for c in cities]     # x,y px
    line_of = {}
    for li, chain in enumerate(lines):
        col = COLORS[li % len(COLORS)]
        xy = [P[i] for i in chain]
        d.line(xy, fill=col, width=7)
        for i in chain:
            line_of.setdefault(i, set()).add(li)
        # line tag at first station
        x, y = xy[0]
        d.text((x + 8, y - 14), lnames[li], fill=col)
    for i, (x, y) in enumerate(P):
        inter = len(line_of.get(i, ())) > 1
        if inter:
            d.ellipse([x - 8, y - 8, x + 8, y + 8],
                      outline=(30, 30, 30), width=3)
        d.ellipse([x - 5, y - 5, x + 5, y + 5],
                  fill=(255, 255, 255),
                  outline=(30, 30, 30), width=2)
        d.text((x + 8, y - 4), names[i], fill=(40, 40, 40))
    pil.save(path)


if __name__ == '__main__':
    rng = np.random.default_rng(SEED + 40)
    mrng = random.Random(41)
    h = cm.continent(N)
    cities = pick_cities(h, rng)
    edges = mst(cities)
    lines, deg = lines_from_edges(edges, len(cities))
    names = [word(mrng) for _ in cities]
    lnames = [word(mrng) for _ in lines]
    out = os.path.join(HERE, 'transit.png')
    render(h, cities, lines, names, lnames, out)
    inter = sum(1 for i in range(len(cities))
                if deg[i] >= 3)
    print(f'cities: {len(cities)}, lines: {len(lines)}, '
          f'edges: {len(edges)}, branch nodes: {inter}')
    for li, ch in enumerate(lines):
        print(f'  {lnames[li]}: ' +
              ' - '.join(names[i] for i in ch))
    print('VERDICT: OK' if len(lines) >= 2 else
          'VERDICT: degenerate (single line)')
