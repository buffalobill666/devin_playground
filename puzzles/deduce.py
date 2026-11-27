"""deduce.py — human-style propagation solver for kakuro.

The core question of the causality thread: does a puzzle have
a propagation skeleton — a solution path of forced moves with
no backtracking? This simulates the human deduction loop:
cell candidates = intersection of both crossing runs' combo
possibilities; singletons get filled; combos filtered.
Measures: coverage (fraction solved by propagation alone)
and max step cost (worst candidate count at a forced step).
"""
from itertools import permutations


def combos(total, length):
    """all ordered tuples of distinct 1-9 digits summing to total"""
    if length == 1:
        return [(total,)] if 1 <= total <= 9 else []
    out = []
    for first in range(1, 10):
        if first >= total:
            break
        for rest in combos(total - first, length - 1):
            if first not in rest:
                out.append((first,) + rest)
    return out


def solve_propagation(puzzle):
    """puzzle: dict with 'cells' {(r,c): None}, 'runs' list of
    {'cells': [(r,c)...], 'sum': int}. Returns report dict."""
    runs = []
    for run in puzzle['runs']:
        runs.append({'cells': run['cells'], 'sum': run['sum'],
                     'combos': combos(run['sum'], len(run['cells']))})
    cellruns = {}
    for i, run in enumerate(runs):
        for pos, cell in enumerate(run['cells']):
            cellruns.setdefault(cell, []).append((i, pos))

    solved = {}
    order = []
    maxcost = 0
    while True:
        progress = False
        for cell, appearances in cellruns.items():
            if cell in solved:
                continue
            # candidate values = intersection across appearances
            poss = None
            for ri, pos in appearances:
                vals = {c[pos] for c in runs[ri]['combos']}
                poss = vals if poss is None else poss & vals
            if len(poss) == 1:
                v = poss.pop()
                solved[cell] = v
                order.append((cell, v))
                maxcost = max(maxcost, 1)
                # filter combos containing v at this pos, and
                # enforce digit-uniqueness within runs
                for ri, pos in appearances:
                    run = runs[ri]
                    run['combos'] = [c for c in run['combos']
                                     if c[pos] == v and len(set(c)) == len(c)]
                progress = True
        if not progress:
            break
    ncells = len(cellruns)
    return {'solved': len(solved), 'total': ncells,
            'coverage': len(solved) / ncells if ncells else 0,
            'order': order, 'full': len(solved) == ncells,
            'skeleton': len(solved) == ncells}


if __name__ == '__main__':
    # micro-test: 2x2 crossing — the atom of propagation.
    # r1: cells (0,0)+(0,1) sum 4 -> must be 1+3 or 3+1
    # r2: (1,0)+(1,1) sum 9
    # c1: (0,0)+(1,0) sum 8
    # c2: (0,1)+(1,1) sum 5
    # solution: 1 3 / 7 2  (check: 4, 9, 8, 5 — yes)
    puz = {'runs': [
        {'cells': [(0, 0), (0, 1)], 'sum': 4},
        {'cells': [(1, 0), (1, 1)], 'sum': 9},
        {'cells': [(0, 0), (1, 0)], 'sum': 8},
        {'cells': [(0, 1), (1, 1)], 'sum': 5},
    ]}
    rep = solve_propagation(puz)
    print('coverage:', rep['coverage'], 'full:', rep['full'])
    print('order:', rep['order'])
