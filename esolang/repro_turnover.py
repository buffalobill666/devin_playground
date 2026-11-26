"""repro_turnover.py — who lives who dies: born/death census (c8/i12)."""
import pickle
from ring import run_ring

CRYSTAL_R = [('CPYR', 0, 8), ('CPYR', 0, 8), ('CPYR', 0, 8),
             ('CPYR', 0, 8), ('REPRO', 8, 0), ('JMPR', 4, 0)]
SIZE, LIFE, CAP, K = 4000, 30, 80000, 6

cells, ctxs, census, deaths = run_ring(
    [(i * (SIZE // K), CRYSTAL_R) for i in range(K)],
    life=LIFE, cap_rounds=CAP, size=SIZE, mu=0.002, seed=0,
    census_every=2000)
out = dict(
    deaths=[dict(born=c.get('born', 0), rnd=d['rnd']) for c, d in
            zip(ctxs, deaths)] if False else deaths,
    final=[dict(born=c.get('born', 0), alive=c['alive'],
                start=c['start'], travel=c['travel'])
           for c in ctxs],
    curve=[(r, a) for r, a, _, _ in census])
pickle.dump(out, open('../runs/repro-turnover.pkl', 'wb'))
nborn = sum(1 for c in ctxs if c.get('born'))
print(f'total ctxs {len(ctxs)}, born during run {nborn}')
print(f'deaths recorded {len(deaths)}')
alive_end = [c for c in ctxs if c['alive']]
print(f'alive at end {len(alive_end)}, of them original-6: '
      f'{sum(1 for c in alive_end if not c.get("born"))}')
print('ALL DONE')
