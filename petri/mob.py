"""mob.py — can alarm calls pay their cost via the selfish herd?

i8 + i23 closed predator-side eavesdropping (signal doomed).
Last open direction: PREY-side use. Mobbing/aggregation:
calls attract prey -> local density -> predator confusion.

New mechanic: herd_dilution>0 divides catch chance by
(1 + k * prey-neighbors of the target) — Hamilton's selfish
herd, a real ecological force, not a fiat for calls.

Runs (calls on, predators sighted):
  noherd: herd_dilution=0   — calls still only betray
  herd:   herd_dilution=0.5 — grouping dilutes catch chance

Questions:
  prey_mob (signed wiring call-grad -> move): + = approach,
       - = avoid. Does the herd world flip it positive?
  prey_call: does calling itself evolve (kin/group benefit)?
  pred_hear: do predators eavesdrop NOW that calls predict
       prey DENSITY (not stale positions)?
"""
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from petri.eco import EcoSim, DEFAULTS

TICKS, EVERY, SEED = 15000, 50, 7
OUT = Path('runs/mob'); OUT.mkdir(parents=True, exist_ok=True)

base = dict(DEFAULTS)
base.update(seed=SEED, call_rate=1.0, log_every=EVERY)

runs = {}
for name, herd in (('noherd', 0.0), ('herd', 0.5)):
    c = dict(base); c['herd_dilution'] = herd
    sim = EcoSim(c)
    rows = []
    while sim.world.tick < TICKS:
        sim.step()
        if sim.world.tick % EVERY == 0:
            rows.append(sim.metrics(0, 0, 0, 0))
    with open(OUT / f'{name}.csv', 'w', newline='') as f:
        wcsv = csv.DictWriter(f, fieldnames=rows[0].keys())
        wcsv.writeheader(); wcsv.writerows(rows)
    runs[name] = rows
    r0, r1 = rows[0], rows[-1]
    print(f'{name}: mob {r0.get("prey_mob",0):+.3f}->'
          f'{r1.get("prey_mob",0):+.3f} call {r0.get("prey_call",0):.3f}->'
          f'{r1.get("prey_call",0):.3f} prey {r1["pop_prey"]} '
          f'preds {r1["pop_pred"]}', flush=True)

fig, ax = plt.subplots(4, 1, figsize=(10, 12), sharex=True)
for name, rows in runs.items():
    t = [r['tick'] for r in rows]
    ax[0].plot(t, [r.get('prey_mob', 0) for r in rows], label=name)
    ax[1].plot(t, [r.get('prey_call', 0) for r in rows], label=name)
    ax[2].plot(t, [r.get('pred_hear', 0) for r in rows], label=name)
    ax[3].plot(t, [r['pop_prey'] for r in rows], label=name)
ax[0].axhline(0, c='k', lw=.5)
ax[0].set_ylabel('mob wiring\n(+approach / -avoid)')
ax[1].set_ylabel('call output wiring')
ax[2].set_ylabel('pred eavesdrop wiring')
ax[3].set_ylabel('prey pop')
ax[3].set_xlabel('tick')
for a in ax:
    a.legend(); a.grid(alpha=.3)
fig.tight_layout()
fig.savefig('petri/mob.png', dpi=140, bbox_inches='tight')
print('saved petri/mob.png + runs/mob/*.csv')
