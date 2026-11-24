"""terr.py — do marks pay for STATIC information?

i6 closed marks of mobile threats (stale at any half-life).
Named residual: deposited info should pay when the feature
is static. Territory marks: prey drip a constant trickle
(mark_mode='home'); others smell marks and may space out —
the classic territorial function. Caveat wired in honestly:
own scent is indistinguishable from rivals' — self-repulsion
is part of the physics, same as real pheromones.

Runs:
  home: marks deposit + are smelled
  deaf: same deposits, senses zeroed (ablation)

Metrics: spacing (mean nearest-neighbor distance),
mean energy, prey_mark wiring (negative = evolved to avoid
marked territory).
"""
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from petri.eco import EcoSim, DEFAULTS

TICKS, EVERY = 10000, 50
OUT = Path('runs/terr'); OUT.mkdir(parents=True, exist_ok=True)


def spacing(pos, rng):
    if len(pos) < 2:
        return 0.0
    idx = rng.choice(len(pos), min(150, len(pos)), replace=False)
    s = pos[idx]
    d = np.sqrt(((s[:, None, :] - s[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, 1e9)
    return float(d.min(1).mean())


base = dict(DEFAULTS)
base.update(scent_marks=1, mark_mode='home', mark_rate=0.02,
            log_every=EVERY)

for seed in (7, 8):
    rows = {}
    for name, kw in (('home', {}), ('deaf', dict(mark_deaf=1))):
        c = dict(base); c.update(seed=seed); c.update(kw)
        sim = EcoSim(c)
        rng = np.random.default_rng(seed)
        rr = []
        while sim.world.tick < TICKS:
            sim.step()
            if sim.world.tick % EVERY == 0:
                m = sim.metrics(0, 0, 0, 0)
                m['spacing'] = spacing(sim.prey.pos, rng)
                m['energy'] = float(sim.prey.energy.mean()) \
                    if len(sim.prey) else 0.0
                rr.append(m)
        rows[name] = rr
        with open(OUT / f's{seed}_{name}.csv', 'w',
                  newline='') as f:
            wcsv = csv.DictWriter(f, fieldnames=rr[0].keys())
            wcsv.writeheader(); wcsv.writerows(rr)
        r = rr[-1]
        print(f's{seed} {name}: space {r["spacing"]:.2f} '
              f'energy {r["energy"]:.3f} mark '
              f'{r.get("prey_mark", 0):+.3f} prey {r["pop_prey"]}',
              flush=True)
    fig, ax = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    for name, rr in rows.items():
        t = [r['tick'] for r in rr]
        ax[0].plot(t, [r['spacing'] for r in rr], label=name)
        ax[1].plot(t, [r.get('prey_mark', 0) for r in rr],
                   label=name)
        ax[2].plot(t, [r['energy'] for r in rr], label=name)
    ax[0].set_ylabel('spacing'); ax[1].set_ylabel('mark wiring')
    ax[2].set_ylabel('mean energy')
    ax[1].axhline(0, c='k', lw=.5)
    for a in ax: a.legend(); a.grid(alpha=.3)
    fig.savefig(OUT / f'terr_s{seed}.png', dpi=110)
print('done', flush=True)
