"""Family archaeology: run EcoSim, log per-lineage census + traits.

Which families survive crashes? Do dynasties rise before waves and
die in them? Do resistant lineages emerge DURING an epidemic?
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from .eco import EcoSim, PREY_S, O, PREY_T
from . import genome as gm


def run_family(ticks=20000, seed=7, preset='epidemic2', storms=True,
               sample=50, out='runs/family', telemetry=None):
    from .run import PRESETS
    cfg = dict(PRESETS[preset])
    if storms:
        cfg.update(storm_period=3500, storm_len=400,
                   storm_regrowth=0.05, storm_cost=3.0)
    sim = EcoSim(cfg=cfg, seed=seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []

    def census(s):
        if s.world.tick % sample or not len(s.prey):
            return
        fam = s.prey.family
        tr = gm.traits(s.prey.genomes, PREY_S * O)
        inf = s.prey.infected.astype(bool)
        for f in np.unique(fam):
            m = fam == f
            row = dict(
                tick=s.world.tick, fam=int(f), n=int(m.sum()),
                speed=float(tr[m, 0].mean()),
                appetite=float(tr[m, 1].mean()),
                effic=float(tr[m, 2].mean()),
                vigil=float(tr[m, 3].mean()),
                resist=float(tr[m, 4].mean()),
                n_inf=int((m & inf).sum()))
            rows.append(row)
            if telemetry is not None:      # живой TORN-стрим на диск
                telemetry.emit(row)

    sim.run(ticks, on_tick=census)
    keys = ['tick', 'fam', 'n', 'speed', 'appetite', 'effic',
            'vigil', 'resist', 'n_inf']
    with open(out / 'families.csv', 'w', newline='') as fh:
        wcsv = csv.DictWriter(fh, keys)
        wcsv.writeheader()
        wcsv.writerows(rows)
    # also save the standard metrics log
    import json
    with open(out / 'eco_log.json', 'w') as fh:
        json.dump(sim.log, fh)
    print(f'{len(rows)} census rows -> {out}/families.csv')
    return out


def chart(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = defaultdict(lambda: defaultdict(list))
    with open(Path(out) / 'families.csv') as fh:
        for r in csv.DictReader(fh):
            f = int(r['fam'])
            for k in ('tick', 'n', 'resist', 'vigil', 'appetite'):
                rows[f][k].append(float(r[k]))
    fig, ax = plt.subplots(figsize=(14, 7))
    # rank families by max population reached; keep top 14 readable
    top = sorted(rows, key=lambda f: -max(rows[f]['n']))[:14]
    for f in top:
        d = rows[f]
        ax.plot(d['tick'], d['n'], lw=1.2, label=f'fam {f}',
                alpha=0.85)
    ax.set_yscale('log')
    ax.set_xlabel('tick'); ax.set_ylabel('prey in family (log)')
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(Path(out) / 'families.png', dpi=110)
    print(f'chart -> {out}/families.png')


if __name__ == '__main__':
    out = run_family(ticks=int(sys.argv[1]) if len(sys.argv) > 1
                     else 20000)
    chart(out)
