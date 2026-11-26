"""sterility_exp.py — REPRO-carrier fraction among the living (c8/i17).

Erosion hypothesis: sterile genomes (REPRO mutated away) travel
but cannot birth — demographic takeover. Measure: for each alive
ctx, the 6 cells ahead of its ip ARE the genome it executes —
does it contain REPRO? Dumps every 2000 rounds.
"""
import pickle
from ring import run_ring

CRYSTAL_R = [('CPYR', 0, 8), ('CPYR', 0, 8), ('CPYR', 0, 8),
             ('CPYR', 0, 8), ('REPRO', 8, 0), ('JMPR', 4, 0)]
SIZE, LIFE, CAP, K = 4000, 30, 80000, 6

cells, ctxs, census, deaths = run_ring(
    [(i * (SIZE // K), CRYSTAL_R) for i in range(K)],
    life=LIFE, cap_rounds=CAP, size=SIZE, mu=0.002, seed=0,
    census_every=2000, dump_dir='../runs/sterility-s0',
    dump_every=2000)
print('ALL DONE', sum(1 for c in ctxs if c['alive']), 'alive end')
