"""flee.py — is the call useless because it's STALE?

i8 verdict: eavesdropping never evolved even under compulsion
(pred_deaf) — the call marks a spot prey already fled. The
signal is late, not redundant.

Next move on the thread: make calls PREDICTIVE. call_flee=1
makes every scream carry the caller's displacement vector —
the alarm now says where prey is HEADING, and intercepting
predators could finally profit.

Design (same ablation pressure as i8):
  stale:  pred_deaf=1, call_flee=0 — position-only calls
  flee:   pred_deaf=1, call_flee=1 — calls carry flee vector
Both deaf: density channel zeroed, calls are the only cue.
Question: does pred_flee wiring (senses 9-10 -> move) grow
where pred_hear (7-8) stayed noise?
"""
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from petri.eco import EcoSim, DEFAULTS

TICKS, EVERY, SEED = 15000, 50, 7
OUT = Path('runs/flee'); OUT.mkdir(parents=True, exist_ok=True)

base = dict(DEFAULTS)
base.update(seed=SEED, call_rate=1.0, pred_deaf=1, log_every=EVERY)

runs = {}
for name, flee in (('stale', 0), ('flee', 1)):
    c = dict(base); c['call_flee'] = flee
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
    print('%s done: pred_hear %.4f->%.4f pred_flee %.4f->%.4f '
          'preds %d' % (
              name,
              rows[0].get('pred_hear', 0), rows[-1].get('pred_hear', 0),
              rows[0].get('pred_flee', 0), rows[-1].get('pred_flee', 0),
              rows[-1]['pop_pred']), flush=True)

fig, ax = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
for name, rows in runs.items():
    t = [r['tick'] for r in rows]
    ax[0].plot(t, [r.get('pred_hear', 0) for r in rows], label=name)
    ax[1].plot(t, [r.get('pred_flee', 0) for r in rows], label=name)
    ax[2].plot(t, [r['pop_pred'] for r in rows], label=name)
ax[0].set_ylabel('position wiring\n|call-grad -> move|')
ax[1].set_ylabel('flee wiring\n|flee-vec -> move|')
ax[2].set_ylabel('predators')
ax[2].set_xlabel('tick')
for a in ax:
    a.legend(); a.grid(alpha=.3)
fig.tight_layout()
fig.savefig('petri/flee.png', dpi=140, bbox_inches='tight')
print('saved petri/flee.png + runs/flee/*.csv')
