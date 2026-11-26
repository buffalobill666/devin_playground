"""mine_exp.py — minefield equilibrium measurement (c8/i16)."""
import pickle
from ring import run_ring

CRYSTAL_R = [('CPYR', 0, 8), ('CPYR', 0, 8), ('CPYR', 0, 8),
             ('CPYR', 0, 8), ('REPRO', 8, 0), ('JMPR', 4, 0)]
SIZE, LIFE, CAP, K = 4000, 30, 80000, 6

cells, ctxs, census, deaths = run_ring(
    [(i * (SIZE // K), CRYSTAL_R) for i in range(K)],
    life=LIFE, cap_rounds=CAP, size=SIZE, mu=0.002, seed=0,
    census_every=2000)
out = [(r, a, m) for r, a, _, _, m in census]
pickle.dump(out, open('../runs/mine-exp.pkl', 'wb'))
for r, a, m in out[:14]:
    print(f'{r//1000}k: alive={a} mines={m}')
print('ALL DONE')
