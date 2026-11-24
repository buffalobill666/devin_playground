"""eavesdrop.py — forced-choice test on the predator hear channel.

Open thread #4: predators never evolved eavesdropping on
alarm calls (+0.04, noise) despite the channel existing in
the genome (call_gx/call_gy -> move wiring).

Two hypotheses:
  redundant  — the prey-density field is a stronger, always-on
               signal; selection had no reason to use calls
  useless    — the call field is too sparse/local to hunt by

Ablation: pred_deaf=1 zeroes the prey-density senses (1-3).
Calls become the ONLY prey cue. If eavesdropping now evolves
(wiring grows) -> machinery was fine, signal was redundant.
If predators collapse -> calls cannot sustain predation at
all (signal sparse/late) — silence is ecological, not genetic.
"""
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from petri.eco import EcoSim, DEFAULTS

TICKS, EVERY, SEED = 15000, 50, 7
OUT = Path('runs/eavesdrop'); OUT.mkdir(parents=True, exist_ok=True)

base = dict(DEFAULTS)
base.update(seed=SEED, call_rate=1.0, log_every=EVERY)

runs = {}
for name, deaf in (('control', 0), ('deaf', 1)):
    c = dict(base); c['pred_deaf'] = deaf
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
    print('%s done: pred_hear %.4f -> %.4f, pred_density %.4f -> %.4f, '
          'preds %d' % (name, rows[0].get('pred_hear', 0),
                        rows[-1].get('pred_hear', 0),
                        rows[0].get('pred_density', 0),
                        rows[-1].get('pred_density', 0),
                        rows[-1]['pop_pred']), flush=True)

fig, ax = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
for name, rows in runs.items():
    t = [r['tick'] for r in rows]
    ax[0].plot(t, [r.get('pred_hear', 0) for r in rows], label=name)
    ax[1].plot(t, [r.get('pred_density', 0) for r in rows], label=name)
    ax[2].plot(t, [r['pop_pred'] for r in rows], label=name)
ax[0].set_ylabel('eavesdrop wiring\n|call -> move|')
ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].set_ylabel('density wiring\n|prey-grad -> move|')
ax[1].grid(alpha=.3)
ax[2].set_ylabel('predator pop'); ax[2].set_xlabel('tick')
ax[2].grid(alpha=.3)
fig.suptitle('Eavesdropping under forced deafness')
fig.tight_layout()
fig.savefig(OUT / 'eavesdrop.png', dpi=140)
print('saved', OUT / 'eavesdrop.png')
