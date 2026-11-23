"""Evolution over DNA sequences: variable-length genomes, tournament."""
import json
import time
from pathlib import Path

import numpy as np

from . import dna, physics, render


def _fit(seq, steps, terrain=None, n_types=5, seek=None, dwell=False,
         fade_at=None, flip_at=None):
    b = dna.decode(seq, n_types=n_types)
    if b is None:
        return 0.0, None
    key = 'dwell' if dwell else 'fitness'
    if seek is not None:
        r1 = physics.simulate_body(b, steps=steps, terrain=terrain,
                                   target=seek, fade_at=fade_at,
                                   flip_at=flip_at)
        r2 = physics.simulate_body(b, steps=steps, terrain=terrain,
                                   target=-seek, fade_at=fade_at,
                                   flip_at=flip_at)
        # dwell scores the WORSE trial: a blind 'parking' gait that
        # camps near one of the two possible foods must score 0 -
        # solving only one side is not arrival, it's an exploit
        if dwell == 'min':
            return min(r1[key], r2[key]), r1
        if dwell == 'combo':
            # composite: signed travel progress + dwell (sharp
            # basin). Approaching pays first, arriving-and-staying
            # pays much more - a real curriculum gradient
            return (r1['fitness'] + r2['fitness']
                    + r1['dwell'] + r2['dwell']), r1
        return r1[key] + r2[key], r1
    r = physics.simulate_body(b, steps=steps, terrain=terrain)
    return r[key], r


def tournament(fits, rng, k=3):
    idx = rng.integers(0, len(fits), k)
    return int(idx[np.argmax(fits[idx])])


def devolve(pop_size=32, gens=30, steps=800, elite=2,
            seed=None, out='runs/devo', record_gens=(), terrain=None,
            n_types=5, seek=None, dwell=False, seed_seq=None,
            fade_at=None, flip_at=None):
    rng = np.random.default_rng(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    pop = [dna.random_dna(rng) for _ in range(pop_size)]
    if seed_seq is not None:
        # radiation from a proven champion: verbatim + mutants
        seed_seq = np.asarray(seed_seq, np.int8)
        pop[0] = seed_seq.copy()
        for i in range(1, pop_size // 2):
            pop[i] = dna.mutate(seed_seq, rng)
    log = []
    best_ever, best_fit = None, -1e9
    t0 = time.time()
    for gen in range(gens):
        fits = np.empty(pop_size)
        ng, nps, nrg = (np.empty(pop_size) for _ in range(3))
        for i in range(pop_size):
            fits[i], _ = _fit(pop[i], steps, terrain, n_types, seek,
                              dwell, fade_at, flip_at)
            g = dna.express(pop[i], n_types)
            ng[i] = len(g)
            nps[i] = sum(1 for t, _ in g if t == 3)
            nrg[i] = sum(1 for t, _ in g if t == 4) + \
                sum(1 for t, _ in g if t == 5)
        order = np.argsort(fits)[::-1]
        b = int(order[0])
        if fits[b] > best_fit:
            best_fit, best_ever = float(fits[b]), pop[b].copy()
        rec = dict(gen=gen, best=float(fits[b]),
                   mean=float(fits.mean()),
                   g_len=float(np.mean([len(s) for s in pop])),
                   n_genes=float(ng.mean()),
                   n_pseudo=float(nps.mean()),
                   n_regul=float(nrg.mean()))
        log.append(rec)
        print(f"gen {gen:>3}  best={rec['best']:7.3f}  "
              f"mean={rec['mean']:7.3f}  len={rec['g_len']:5.0f}  "
              f"genes={rec['n_genes']:4.1f}  reg={rec['n_regul']:3.1f}  "
              f"({time.time() - t0:.0f}s)", flush=True)
        if gen in record_gens or gen == gens - 1:
            _, res = _fit(pop[b], steps, terrain)
            if res is not None:
                res['frames'] = []
                res = physics.simulate_body(
                    dna.decode(pop[b], n_types=n_types),
                    steps=steps, record_every=8, terrain=terrain,
                    target=seek, fade_at=fade_at, flip_at=flip_at)
                res['body']['target'] = seek
                render.render_run(res, out / f'gen{gen:03d}',
                                  terrain=terrain)
        next_pop = [pop[i] for i in order[:elite]]
        while len(next_pop) < pop_size:
            p1 = pop[tournament(fits, rng)]
            p2 = pop[tournament(fits, rng)]
            child = dna.crossover(p1, p2, rng)
            next_pop.append(dna.mutate(child, rng))
        pop = next_pop
        # genomic extinction rescue: if nothing is viable, inject
        # fresh 'panspermia' sequences (same trick as petri)
        if fits.max() <= 0:
            for i in range(pop_size // 4):
                pop[rng.integers(pop_size)] = dna.random_dna(rng)
    np.save(out / 'champion_dna.npy', best_ever)
    with open(out / 'evo_log.json', 'w') as fh:
        json.dump(dict(log=log, best=best_fit,
                       elapsed=time.time() - t0, seed=seed), fh, indent=2)
    return best_ever, best_fit, log
