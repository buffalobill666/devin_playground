"""repro_exp.py — reproduction substrate v1 (c8/i10)."""
import pickle
from ring import run_ring

CRYSTAL_R = [('CPYR', 0, 8), ('CPYR', 0, 8), ('CPYR', 0, 8),
             ('CPYR', 0, 8), ('REPRO', 8, 0), ('JMPR', 4, 0)]
SIZE, LIFE, CAP, K = 4000, 30, 80000, 6


def one(seed, mu, tag):
    seeds = [(i * (SIZE // K), CRYSTAL_R) for i in range(K)]
    cells, ctxs, census, deaths = run_ring(
        seeds, life=LIFE, cap_rounds=CAP, size=SIZE, mu=mu,
        seed=seed, census_every=2000)
    peak = max(a for _, a, _, _ in census)
    empty_at = next((r for r, a, _, _ in census if a == 0), None)
    return dict(seed=seed, mu=mu, tag=tag, peak=peak,
                empty_at=empty_at,
                curve=[(r, a) for r, a, _, _ in census])


res = []
for mu in (0.002, 0.004):
    for seed in (0, 1):
        r = one(seed, mu, 'repro')
        res.append(r)
        print(f"repro mu{mu} s{seed}: peak={r['peak']} "
              f"empty_at={r['empty_at']}", flush=True)
with open('../runs/repro-exp-results.pkl', 'wb') as fh:
    pickle.dump(res, fh)
print('ALL DONE')
