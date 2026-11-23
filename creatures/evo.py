"""Evolution loop: tournament selection, elites, per-generation best GIF."""
import json
import time
from pathlib import Path

import numpy as np

from . import body, physics, render


def tournament(fits, rng, k=3):
    idx = rng.integers(0, len(fits), k)
    return int(idx[np.argmax(fits[idx])])


def evolve(pop_size=32, gens=30, steps=800, elite=2, mut=0.10,
           seed=None, out='runs/creatures', record_gens=()):
    rng = np.random.default_rng(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    pop = np.stack([body.random_genome(rng) for _ in range(pop_size)])
    log = []
    best_ever, best_fit = None, -1e9
    t0 = time.time()
    for gen in range(gens):
        fits = np.empty(pop_size)
        for i in range(pop_size):
            fits[i] = physics.simulate(pop[i], steps=steps)['fitness']
        order = np.argsort(fits)[::-1]
        b = int(order[0])
        if fits[b] > best_fit:
            best_fit, best_ever = float(fits[b]), pop[b].copy()
        rec = dict(gen=gen, best=float(fits[b]),
                   mean=float(fits.mean()),
                   median=float(np.median(fits)),
                   worst=float(fits[order[-1]]),
                   div=float(pop.std(0).mean()))  # genome diversity
        log.append(rec)
        print(f"gen {gen:>3}  best={rec['best']:7.3f}  "
              f"mean={rec['mean']:7.3f}  div={rec['div']:5.3f}  "
              f"({time.time() - t0:.0f}s)", flush=True)
        if gen in record_gens or gen == gens - 1:
            res = physics.simulate(pop[b], steps=steps, record_every=8)
            render.render_run(res, out / f'gen{gen:03d}')
        next_pop = [pop[i] for i in order[:elite]]
        while len(next_pop) < pop_size:
            p1 = pop[tournament(fits, rng)]
            p2 = pop[tournament(fits, rng)]
            child = body.crossover(p1, p2, rng)
            next_pop.append(body.mutate(child, mut, rng))
        pop = np.stack(next_pop)
    np.save(out / 'champion.npy', best_ever)
    with open(out / 'evo_log.json', 'w') as fh:
        json.dump(dict(log=log, best=best_fit,
                       elapsed=time.time() - t0, seed=seed), fh, indent=2)
    return best_ever, best_fit, log
