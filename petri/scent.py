"""scent.py — stigmergy: can a persistent danger-mark pay where
ephemeral calls couldn't?

Call thread closed three ways (i8 eavesdrop, i23 flee-vector,
c4i1 mobbing): the channel dies because the signal is local +
short-lived (~7 ticks). Named successor: scent marks — prey
reflexively deposit fear-musk scaled by sensed pred-gradient;
marks persist ~35 ticks (mark_decay=0.98), cost nothing, and
predators can't smell them. Territory memory, not alarm.

Runs (same genome size, ablation blinds the channel):
  marks: scent_marks=1              — marks deposit + are smelled
  deaf:  scent_marks=1, mark_deaf=1 — marks deposit, senses zeroed

Question: does move-wiring on mark senses go negative (flee
remembered danger) beyond noise, and does survival differ?
"""
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from petri.eco import EcoSim, DEFAULTS

TICKS, EVERY, SEED = 10000, 50, 7
OUT = Path('runs/scent'); OUT.mkdir(parents=True, exist_ok=True)

base = dict(DEFAULTS)
base.update(seed=SEED, scent_marks=1, log_every=EVERY)

runs = {}
for name, kw in (('marks', {}), ('deaf', dict(mark_deaf=1))):
    c = dict(base); c.update(kw)
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
    print(f'{name}: mark {r0.get("prey_mark",0):+.3f}->'
          f'{r1.get("prey_mark",0):+.3f} lvl '
          f'{r1.get("prey_marklvl",0):+.3f} prey {r1["pop_prey"]} '
          f'preds {r1["pop_pred"]}', flush=True)

fig, ax = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
for name, rows in runs.items():
    t = [r['tick'] for r in rows]
    ax[0].plot(t, [r.get('prey_mark', 0) for r in rows], label=name)
    ax[1].plot(t, [r['pop_prey'] for r in rows], label=name)
    ax[2].plot(t, [r['pop_pred'] for r in rows], label=name)
ax[0].axhline(0, c='k', lw=.5)
ax[0].set_ylabel('prey_mark wiring (−=flee)')
ax[1].set_ylabel('prey pop'); ax[2].set_ylabel('pred pop')
for a in ax: a.legend(); a.grid(alpha=.3)
fig.savefig(OUT / 'scent.png', dpi=110)
print('done', flush=True)
