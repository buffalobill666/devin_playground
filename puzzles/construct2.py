"""Constructor v4 — mixed-length layout, shifted seams, connectivity-checked.

Kakuro rule: each cell in exactly one across + one down run, run lengths >= 2.
4x4 rows partition as either [4] or [2,2]; seams shifted between rows so
the deduction graph stays connected. Entry: one 2-cell tail-sum crossing.
"""
import sys, random
sys.path.insert(0, 'puzzles')
from deduce import solve_propagation

def partition_row(rng):
    return [2, 2] if rng.random() < 0.5 else [4]

def build_layout(n, rng):
    across = []
    for r in range(n):
        part = partition_row(rng)
        c = 0
        for L in part:
            across.append([(r, c + i) for i in range(L)])
            c += L
    down = []
    for c in range(n):
        part = partition_row(rng)
        r = 0
        for L in part:
            down.append([(r + i, c) for i in range(L)])
            r += L
    return across + down

def connected(runs, n):
    cells = [(r, c) for r in range(n) for c in range(n)]
    adj = {cell: set() for cell in cells}
    for run in runs:
        for a in run:
            for b in run:
                if a != b: adj[a].add(b)
    seen = {cells[0]}
    stack = [cells[0]]
    while stack:
        for nb in adj[stack.pop()]:
            if nb not in seen:
                seen.add(nb); stack.append(nb)
    return len(seen) == len(cells)

def try_build(n, seed):
    rng = random.Random(seed)
    runs = build_layout(n, rng)
    if not connected(runs, n):
        return None
    # random fill respecting distinctness per run (simple rejection inside)
    fill = {}
    cells = [(r, c) for r in range(n) for c in range(n)]
    rng.shuffle(cells)
    for cell in cells:
        used = set()
        for run in runs:
            if cell in run:
                for cc in run:
                    if cc != cell and cc in fill:
                        used.add(fill[cc])
        choices = [d for d in range(1, 10) if d not in used]
        if not choices:
            return None
        fill[cell] = rng.choice(choices)
    puz = {'runs': [{'cells': run, 'sum': sum(fill[c] for c in run)} for run in runs]}
    rep = solve_propagation(puz)
    return {'puz': puz, 'fill': fill, 'rep': rep, 'runs': runs}

if __name__ == '__main__':
    best = None
    stats = {'conn': 0, 'full': 0, 'att': 0}
    covs = []
    for seed in range(120):
        res = try_build(4, seed)
        if not res: continue
        stats['att'] += 1
        covs.append(res['rep']['coverage'])
        if res['rep']['full']:
            stats['full'] += 1
            if not best: best = (seed, res)
    mc = sum(covs)/len(covs) if covs else 0
    print(f'4x4 mixed: valid {stats["att"]}/120, full skeleton {stats["full"]}, mean cov {mc:.2f}')
    if best:
        print('first full seed', best[0])
        for row in range(4):
            print([best[1]['fill'][(row, c)] for c in range(4)])
