"""breath.py — does the world's trait space saturate?

Open thread #2: worlds "run out of breath". Hypothesis:
fixed perception channels = fixed phenotype box -> novelty
exhausts, selection rotates families inside a bounded room.

Test on existing censuses (no new sims). Per tick:
  vol   = sqrt(det(cov + eps*I)) — generalized trait volume
  cells = fraction of a 0.1-grid over [0,1]^5 that is occupied
  fams  = family count; born = new family ids per 1000 ticks

Verdict reads the CURVES, not the tail: does vol plateau?
do births decay to zero? If both -> breath ends because
space ends. If births decay but vol holds -> rotation, not
exhaustion.
"""

import csv
import glob
import os
import re

import numpy as np
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAITS = ('speed', 'appetite', 'effic', 'vigil', 'resist')
GRID = 0.1


def load_series(path):
    rows = list(csv.DictReader(open(path)))
    ticks = np.array(sorted({int(r['tick']) for r in rows}))
    tr = np.array([[float(r[k]) for k in TRAITS] for r in rows])
    tt = np.array([int(r['tick']) for r in rows])
    fam = np.array([int(r['fam']) for r in rows])
    vol, cells, nf = [], [], []
    for t in ticks:
        m = tt == t
        X = tr[m]
        if len(X) < 6:
            vol.append(np.nan); cells.append(np.nan); nf.append(m.sum()); continue
        c = np.cov(X.T) + 1e-8 * np.eye(5)
        vol.append(float(np.sqrt(np.linalg.det(c))))
        occ = {tuple(int(v / GRID) for v in x) for x in X}
        cells.append(len(occ) / 10 ** 5)
        nf.append(m.sum())
    first = {}
    for f, t in zip(fam, tt):
        first.setdefault(f, t)
    born = np.array([sum(1 for v in first.values() if t <= v < t + 1000)
                     for t in range(0, int(ticks.max()), 1000)])
    return ticks, np.array(vol), np.array(cells), np.array(nf), born


if __name__ == '__main__':
    runs = sorted(glob.glob(os.path.join(ROOT, 'runs/family-seed*/families.csv')))
    fig, axes = plt.subplots(3, 1, figsize=(11, 11), sharex=True)
    print(f'{"run":<16} {"vol(0-5k)":>10} {"vol(15k+)":>10} '
          f'{"born(0-5k)":>11} {"born(15k+)":>11} {"fams(last)":>10}')
    for path in runs:
        name = re.search(r'family(-seed\d+)', path).group(1)
        ticks, vol, cells, nf, born = load_series(path)
        axes[0].plot(ticks, vol, lw=0.8, label=name)
        axes[1].plot(ticks, cells * 1e5, lw=0.8)
        axes[2].plot(ticks, nf, lw=0.8)
        early = vol[(ticks > 0) & (ticks < 5000)]
        late = vol[ticks > 15000]
        print(f'{name:<16} {np.nanmedian(early):>10.5f} '
              f'{np.nanmedian(late):>10.5f} '
              f'{born[:5].sum():>11} {born[15:].sum():>11} '
              f'{int(nf[~np.isnan(nf)][-1]):>10}')
    axes[0].set_ylabel('trait volume\nsqrt(det cov)')
    axes[1].set_ylabel('occupied cells\n(of 1e5 grid)')
    axes[2].set_ylabel('families alive')
    axes[2].set_xlabel('tick')
    axes[0].legend(fontsize=8)
    fig.suptitle('Does the phenotype room exhaust? 5 worlds, same rules')
    fig.tight_layout()
    out = os.path.join(ROOT, 'petri/breath.png')
    fig.savefig(out, dpi=140)
    print(out)
