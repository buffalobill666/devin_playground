"""kakuro_mac.py — MAC solver: arc consistency maintained INSIDE
the search, not just once before it. The scaling missing piece.

kakuro.py propagates once, then backtracks blind: a wrong tuple
choice deep in the tree is only discovered when the contradiction
reaches the surface. MAC re-propagates after every assignment —
the domains of all touching runs shrink with each decision, and
most wrong branches die in one step instead of a thousand.

Measured honestly: time-to-proof on boards of growing size.
"""
import random
import time
from itertools import permutations
from kakuro import (make_layout, plant, run_combos_fast,
                    extract_runs, solve_count)


def ac_prune(doms, celluse):
    """one full arc-consistency sweep to fixpoint.
    doms: list of tuple-lists (copies — caller owns mutation).
    returns False if any domain empties."""
    changed = True
    while changed:
        changed = False
        for c, uses in celluse.items():
            per_run = []
            for ri, pos in uses:
                per_run.append({t[pos] for t in doms[ri]})
            if not per_run:
                continue
            inter = set.intersection(*per_run) if len(per_run) > 1 else per_run[0]
            for ri, pos in uses:
                before = len(doms[ri])
                doms[ri] = [t for t in doms[ri] if t[pos] in inter]
                if len(doms[ri]) != before:
                    changed = True
                    if not doms[ri]:
                        return False
    return all(doms)


def solve_count_mac(runs, sums, limit=2):
    """count completions with MAC. Returns count up to limit."""
    doms0 = []
    for i, (_, _, cellspec) in enumerate(runs):
        d = run_combos_fast(sums[i], len(cellspec))
        if not d:
            return 0
        doms0.append(list(d))
    celluse = {}
    for i, (_, _, cellspec) in enumerate(runs):
        for pos, c in enumerate(cellspec):
            celluse.setdefault(c, []).append((i, pos))
    count = 0

    def bt(doms):
        nonlocal count
        if count >= limit:
            return
        doms = [list(d) for d in doms]
        if not ac_prune(doms, celluse):
            return
        if all(len(d) == 1 for d in doms):
            count += 1
            return
        # branch on smallest domain > 1
        ri = min((i for i in range(len(doms)) if len(doms[i]) > 1),
                 key=lambda i: len(doms[i]))
        for tup in doms[ri]:
            ndoms = [list(d) for d in doms]
            ndoms[ri] = [tup]
            bt(ndoms)
            if count >= limit:
                return

    bt(doms0)
    return count


def generate_big(seed, W, H, blackp=0.34, tries=40, verbose=False):
    rng = random.Random(seed)
    t0 = time.time()
    for attempt in range(tries):
        lay = make_layout(rng, W, H, blackp)
        if not lay:
            continue
        white, runs, W2, H2 = lay
        fill, assign = plant(rng, runs)
        if not fill:
            continue
        sums = [sum(assign[i]) for i in range(len(runs))]
        n = solve_count_mac(runs, sums, limit=2)
        if verbose:
            print(f'  att{attempt}: {len(runs)} runs, sols={n}')
        if n == 1:
            return dict(white=white, runs=runs, sums=sums, W=W2, H=H2,
                        fill=fill, attempt=attempt, elapsed=time.time() - t0)
    return None


if __name__ == '__main__':
    # benchmark: 5x5 reference (existing genre), then 6x6, 7x7
    for W, H in [(5, 5), (6, 6), (7, 7)]:
        t0 = time.time()
        res = generate_big(seed=W * 100 + 3, W=W, H=H, tries=25)
        dt = time.time() - t0
        if res:
            nc = sum(sum(r) for r in res['white'])
            print(f'{W}x{H}: UNIQUE in {dt:.1f}s — '
                  f'{len(res["runs"])} runs, {nc} cells, att{res["attempt"]}')
        else:
            print(f'{W}x{H}: no unique in 25 tries ({dt:.1f}s)')
