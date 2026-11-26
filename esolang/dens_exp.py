"""dens_exp.py — state-dependent mutation experiment (c8/i9).

mu_local = mu * (1 + alpha * density), density = fraction of
non-NOP cells in +-dens_win around the copy source. P-dens-1:
sustained strain diversity (niches from feedback). P-dens-2:
shorter lifespan only — the mu-pump dressed in spatiality.
"""
import pickle, os, sys
from ring import run_ring, CRYSTAL

MU, CAP, LIFE, SIZE, ALPHA = 0.003, 60000, 30, 4000, 3
K = 6


def one(seed, alpha, tag):
    seeds = [(i * (SIZE // K), CRYSTAL) for i in range(K)]
    out = run_ring(seeds, life=LIFE, cap_rounds=CAP, size=SIZE,
                   mu=MU, seed=seed, dens_alpha=alpha,
                   dump_dir=f'../runs/dens-{tag}-s{seed}',
                   dump_every=10000, census_every=2000)
    cells, ctxs, census, deaths = out
    empty_at = CAP
    for rnd, alive, trav, muts in census:
        if alive == 0:
            empty_at = rnd
            break
    return dict(seed=seed, alpha=alpha, empty_at=empty_at,
                census=[(r, a) for r, a, _, _ in census],
                final_alive=sum(1 for c in ctxs if c['alive']))


results = []
for seed in (0, 1, 2):
    results.append(one(seed, ALPHA, 'dens'))
    print(f'dens s{seed} done: empty_at={results[-1]["empty_at"]}',
          flush=True)
    results.append(one(seed, None, 'ctrl'))
    print(f'ctrl s{seed} done: empty_at={results[-1]["empty_at"]}',
          flush=True)

with open('../runs/dens-exp-results.pkl', 'wb') as fh:
    pickle.dump(results, fh)
print('ALL DONE')
