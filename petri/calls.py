"""Alarm-call experiment: does a costly warning signal need kin?

Two worlds, same seed, alarm calls enabled:
  A clustered - kids spawn near parents (families are neighbours)
  B dispersed - kids teleport anywhere (families scrambled)

If calling is kin-selected, prey_call (pred-grad -> call wiring)
should rise in A and stay ~0 in B.
"""
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from petri.eco import EcoSim, DEFAULTS

TICKS, EVERY, SEED = 15000, 50, 7
OUT = Path('runs/calls'); OUT.mkdir(parents=True, exist_ok=True)

base = dict(DEFAULTS)
base.update(seed=SEED, ticks=TICKS, call_rate=1.0, log_every=EVERY)

runs = {}
for name, disp in (('clustered', 0), ('dispersed', 1)):
    c = dict(base); c['prey_disperse'] = disp
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
    print('%s done: prey_call %.3f -> %.3f, prey %d, fams %d'
          % (name, rows[0]['prey_call'], rows[-1]['prey_call'],
             rows[-1]['pop_prey'], rows[-1]['prey_families']))

fig, ax = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
for name, rows in runs.items():
    t = [r['tick'] for r in rows]
    ax[0].plot(t, [r['prey_call'] for r in rows], label=name)
    ax[1].plot(t, [r['prey_hear'] for r in rows], label=name)
    ax[2].plot(t, [r['pop_prey'] for r in rows], label=name)
ax[0].axhline(0, color='k', lw=.5, alpha=.4)
ax[0].set_ylabel('alarm wiring'); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].set_ylabel('listening (|hear->move|)'); ax[1].grid(alpha=.3)
ax[2].set_ylabel('prey pop'); ax[2].set_xlabel('tick')
ax[2].grid(alpha=.3)
fig.tight_layout()
fig.savefig(OUT / 'calls.png', dpi=140)
print('saved', OUT / 'calls.png')
