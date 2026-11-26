"""kakuro_rect.py — deadly-rectangle analysis.

The i5 forensic finding: sum-preserving +-e shift rectangles make
non-uniqueness structural — sums are blind to them by construction.
This module measures whether rectangle count in a planted fill
predicts its solution count. If yes: construction should plant
rectangle-free fills, not search sums.

A rectangle: two horizontal runs h1,h2 sharing two vertical runs
v1,v2 — four white corner cells. Shiftable with shift e != 0 if
a+e, b-e, c-e, d+e all in 1..9 and pairwise collision-free inside
the rectangle (approximation of run-validity).
"""
from kakuro import make_layout
from kakuro_mac import plant_fc, solve_count_mac
import random


def build_grid(runs, fill):
    """cell -> value map is fill already; need row/col structure"""
    cells = sorted(fill)
    grid = {}
    for c in cells:
        grid[c] = fill[c]
    return grid


def find_rectangles(runs, fill):
    """count shiftable rectangles. runs are tuples (dir, start, cellspec)
    with cellspec = list of (x,y) cells."""
    # classify runs by orientation: horizontal if all cells share y
    hor, ver = [], []
    for ri, (d, s, spec) in enumerate(runs):
        ys = {c[1] for c in spec}
        if len(ys) == 1:
            hor.append((ri, set(spec)))
        else:
            ver.append((ri, set(spec)))
    count = 0
    shiftsum = 0
    for i1 in range(len(hor)):
        for i2 in range(i1 + 1, len(hor)):
            _, cellsA = hor[i1]
            _, cellsB = hor[i2]
            for j1 in range(len(ver)):
                for j2 in range(j1 + 1, len(ver)):
                    _, cellsV1 = ver[j1]
                    _, cellsV2 = ver[j2]
                    corners = []
                    ok = True
                    for hc in (cellsA, cellsB):
                        for vc in (cellsV1, cellsV2):
                            inter = hc & vc
                            if len(inter) == 1:
                                corners.append(inter.pop())
                            elif len(inter) > 1:
                                ok = False
                    if len(corners) != 4:
                        continue
                    # order: a=h1v1 b=h1v2 c=h2v1 d=h2v2 — but corners
                    # collected in order A-V1, A-V2, B-V1, B-V2 — correct
                    a, b, c, d = [fill[x] for x in corners]
                    for e in range(1, 9):
                        vals = [a + e, b - e, c - e, d + e]
                        if all(1 <= v <= 9 for v in vals):
                            # collision check inside rectangle rows/cols
                            if vals[0] != b and vals[1] != a and \
                               vals[2] != d and vals[3] != c and \
                               vals[0] != c and vals[2] != a and \
                               vals[1] != d and vals[3] != b and \
                               len(set(vals)) == 4:
                                count += 1
                                shiftsum += abs(e)
                                break
    return count


if __name__ == '__main__':
    print('rectangle count vs solution count, 5x5 blackp .34, 40 fills:')
    data = []
    rngseq = 0
    while len(data) < 40:
        rng = random.Random(1000 + rngseq)
        rngseq += 1
        lay = make_layout(rng, 5, 5, 0.34)
        if not lay:
            continue
        white, runs, W, H = lay
        fill = plant_fc(rng, runs)
        if not fill:
            continue
        nrect = find_rectangles(runs, fill)
        nsol = solve_count_mac(runs, [sum(fill[c] for c in spec)
                                      for (_, _, spec) in runs], limit=20)
        data.append((nrect, nsol))
    zero_rect = [s for r, s in data if r == 0]
    some_rect = [s for r, s in data if r > 0]
    print(f'fills with 0 rectangles: {len(zero_rect)}, '
          f'mean sols {sum(zero_rect)/max(1,len(zero_rect)):.1f}, '
          f'unique: {sum(1 for s in zero_rect if s == 1)}')
    print(f'fills with 1+ rectangles: {len(some_rect)}, '
          f'mean sols {sum(some_rect)/max(1,len(some_rect)):.1f}, '
          f'unique: {sum(1 for s in some_rect if s == 1)}')
    hist = {}
    for r, s in data:
        hist.setdefault(r, []).append(s)
    for r in sorted(hist):
        print(f'  rect={r}: n={len(hist[r])} mean_sols={sum(hist[r])/len(hist[r]):.1f}')
