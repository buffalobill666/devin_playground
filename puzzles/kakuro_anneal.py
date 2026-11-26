"""kakuro_anneal.py — simulated annealing over run sums.

The c7 failure autopsy: hill-climb descended 12 -> 3 and died in
local minima; naive kicks made it worse. The landscape between
'many solutions' and 'unique' is valleys — exactly what annealing
crosses by design. Changes vs c7, honestly itemized:
  1. best-ever memory (never lose the closest approach)
  2. temperature — worse moves accepted early, rejected late
  3. infeasible (count 0) penalized as worse than any positive,
     not treated as zero-cost (0 solutions is NOT better than 3!)
  4. sums perturbed within valid range for the run length

Objective: capped solution count; cap 20 keeps oracle ~ms.
"""
import random
import time
from kakuro import make_layout
from kakuro_mac import plant_fc, solve_count_mac


def sum_range(n):
    return n * (n + 1) // 2, n * (19 - n) // 2


def cost(runs, sums, cap=20):
    n = solve_count_mac(runs, sums, limit=cap)
    if n == 0:
        return cap + 10  # infeasible — worse than any solvable
    return n


def anneal(rng, runs, sums0, steps=1500, t0=4.0, cool=0.995,
           verbose=False):
    ranges = [sum_range(len(spec)) for (_, _, spec) in runs]
    cur = list(sums0)
    curc = cost(runs, cur)
    best, bestc = list(cur), curc
    t = t0
    for step in range(steps):
        ri = rng.randrange(len(runs))
        lo, hi = ranges[ri]
        delta = rng.choice([-2, -1, -1, 1, 1, 2])
        ns = cur[ri] + delta
        if ns < lo or ns > hi:
            t *= cool
            continue
        trial = list(cur)
        trial[ri] = ns
        tc = cost(runs, trial)
        d = tc - curc
        if d <= 0 or rng.random() < pow(2.718, -d / max(t, 0.01)):
            cur, curc = trial, tc
            if tc < bestc:
                best, bestc = list(trial), tc
                if verbose:
                    print(f'  step{step}: best={bestc} (t={t:.2f})')
            if bestc == 1:
                return best, bestc, step
        t *= cool
    return best, bestc, steps


def trial(seed, W=5, H=5, blackp=0.34, steps=1500):
    rng = random.Random(seed)
    lay = make_layout(rng, W, H, blackp)
    if not lay:
        return None
    white, runs, W2, H2 = lay
    fill = plant_fc(rng, runs)
    if not fill:
        return None
    sums0 = [sum(fill[c] for c in spec) for (_, _, spec) in runs]
    c0 = cost(runs, sums0)
    tstart = time.time()
    best, bestc, used = anneal(rng, runs, sums0, steps=steps)
    dt = time.time() - tstart
    return dict(start=c0, end=bestc, steps_used=used, dt=dt,
                runs=len(runs), sums=best)


if __name__ == '__main__':
    print('annealing trial: 8 attempts on 5x5 blackp .34')
    hits = 0
    for seed in range(8):
        r = trial(seed)
        if r is None:
            print(f'seed{seed}: layout/plant failed')
            continue
        tag = ' UNIQUE!' if r['end'] == 1 else ''
        if r['end'] == 1:
            hits += 1
        print(f'seed{seed}: {r["start"]} -> {r["end"]} '
              f'in {r["steps_used"]} steps, {r["dt"]:.1f}s{tag}')
    print(f'hits: {hits}/8 — baseline rejection is 1/60')
