"""kakuro_forge.py — puzzle construction by hill-climbing the sums.

The insight that breaks the statistical wall: the planted fill
was always a red herring. The sums ARE the puzzle — they can be
chosen freely within valid ranges, no planting needed. Any sum
assignment with exactly one completion is a valid kakuro.

So: random sums, count completions (cap 6 for gradient), mutate
one sum +-1, keep what lowers the count. The fitness landscape
has a measurable gradient because completion count is integer-
graded, not binary. Construction as optimization, not rejection.
"""
import random
import time
from kakuro import make_layout
from kakuro_mac import solve_count_mac


def sum_range(length):
    lo = sum(range(1, length + 1))
    hi = sum(range(10 - length, 10))
    return lo, hi


def forge(runs, seed=0, max_steps=4000, cap=6, verbose=False):
    rng = random.Random(seed)
    ranges = [sum_range(len(spec)) for (_, _, spec) in runs]
    sums = [rng.randint(lo, hi) for lo, hi in ranges]

    def count(s):
        return solve_count_mac(runs, s, limit=cap)

    def fitness(n):
        return n if n > 0 else cap * 2   # unsolvable worst

    best = fitness(count(sums))
    t0 = time.time()
    stuck = 0
    for step in range(max_steps):
        if best == 1:
            break
        ri = rng.randrange(len(runs))
        lo, hi = ranges[ri]
        delta = rng.choice([-2, -1, 1, 2])
        ns = sums[ri] + delta
        if ns < lo or ns > hi:
            continue
        old = sums[ri]
        sums[ri] = ns
        nn = fitness(count(sums))
        if nn <= best:
            best = nn
            stuck = 0 if nn < best else stuck + 1
        else:
            sums[ri] = old  # reject
            stuck += 1
        # kick: re-randomize a few sums when plateaued
        if stuck > 250:
            for _ in range(3):
                kj = rng.randrange(len(runs))
                lo2, hi2 = ranges[kj]
                sums[kj] = rng.randint(lo2, hi2)
            best = fitness(count(sums))
            stuck = 0
            if verbose:
                print(f'  step{step}: kick, count~{best}')
    dt = time.time() - t0
    final = count(sums)
    return sums, final, step, dt


if __name__ == '__main__':
    rng = random.Random(42)
    lay = None
    while not lay:
        lay = make_layout(rng, 5, 5, 0.30)
    white, runs, W, H = lay
    nc = sum(sum(r) for r in white)
    print(f'layout: {len(runs)} runs, {nc} cells')
    sums, n, steps, dt = forge(runs, seed=1, verbose=True)
    print(f'result: count={n} after {steps} steps, {dt:.1f}s')
    if n == 1:
        print('UNIQUE forged. sums:', sums)
