"""Chain-quality metric for skeleton puzzles.

A puzzle is a program for a human computer. Aesthetics = shape of execution:
- branching: moments where multiple cells become derivable at once (width)
- plateau: long stretches of forced single-file deduction (monotony risk)
- the finish: whether the last deductions are trivial mop-up or a real crest

Metrics (all computed from the propagation trace):
  width_profile  — how many cells were simultaneously derivable at each step
  n_branchpoints — count of steps where width jumped to >= 3
  max_plateau    — longest run of width-1 steps (single-file forced chain)
  finish_weight  — fraction of cells deduced in final quarter vs their difficulty
  hardness       — mean over steps of (candidates eliminated) — proxy for work
"""
import sys, json
sys.path.insert(0, 'puzzles')
from deduce import combos

def trace_widths(puz):
    """Re-simulate propagation, recording at each step how many cells were derivable."""
    runs = puz['runs']
    cells = sorted({c for r in runs for c in map(tuple, r['cells'])})
    cell_runs = {c: [] for c in cells}
    for r in runs:
        rcells = [tuple(x) for x in r['cells']]
        for c in rcells:
            cell_runs[c].append((rcells, r['sum']))
    solved = {}
    widths = []
    while len(solved) < len(cells):
        derivable = []
        for c in cells:
            if c in solved:
                continue
            cand = None
            for rcells, s in cell_runs[c]:
                k = len(rcells)
                idx = rcells.index(c)
                vals = set()
                for combo in combos(s, k):
                    ok = True
                    for cc, v in zip(rcells, combo):
                        if cc in solved and solved[cc] != v:
                            ok = False
                            break
                    if ok:
                        vals.add(combo[idx])
                cand = vals if cand is None else cand & vals
            if cand is not None and len(cand) == 1:
                derivable.append((c, next(iter(cand))))
        if not derivable:
            return widths, False
        widths.append(len(derivable))
        c, v = derivable[0]
        solved[c] = v
    return widths, True

def quality(puz):
    widths, full = trace_widths(puz)
    if not full:
        return {'full': False}
    n_branch = sum(1 for w in widths if w >= 3)
    max_plateau = 0
    cur = 0
    for w in widths:
        if w == 1:
            cur += 1
            max_plateau = max(max_plateau, cur)
        else:
            cur = 0
    mean_w = sum(widths) / len(widths)
    # finish: mean width in last quarter — low = clean single-file crest
    q = max(1, len(widths) // 4)
    finish = sum(widths[-q:]) / q
    return {
        'full': True,
        'steps': len(widths),
        'widths': widths,
        'mean_width': round(mean_w, 2),
        'branchpoints': n_branch,
        'max_plateau': max_plateau,
        'finish_width': round(finish, 2),
    }

if __name__ == '__main__':
    puz = json.load(open('puzzles/k1-first-skeleton.json', encoding='utf-8'))
    rep = quality(puz)
    print('k1 quality:', {k: v for k, v in rep.items() if k != 'widths'})
    print('width profile:', rep['widths'])
