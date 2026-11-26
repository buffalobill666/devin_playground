"""k48_exp.py — K=48 fixed-population control (c8/i18)."""
import pickle
from ring import run_ring, CRYSTAL

SIZE, LIFE, CAP, K = 4000, 30, 80000, 48
res = []
for mu in (0.002, 0.004):
    for seed in (0, 1):
        seeds = [(i * (SIZE // K), CRYSTAL) for i in range(K)]
        cells, ctxs, census, deaths = run_ring(
            seeds, life=LIFE, cap_rounds=CAP, size=SIZE, mu=mu,
            seed=seed, census_every=2000)
        empty_at = next((r for r, a, _, _, _ in census if a == 0), None)
        res.append(dict(mu=mu, seed=seed, empty_at=empty_at,
                        curve=[(r, a) for r, a, _, _, _ in census]))
        print(f'k48 mu{mu} s{seed}: empty_at={empty_at}', flush=True)
pickle.dump(res, open('../runs/k48-results.pkl', 'wb'))
print('ALL DONE')
