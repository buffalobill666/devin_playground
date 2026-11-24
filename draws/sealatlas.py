"""sealatlas.py — atlas of worlds: every family run, one plate.

sealpair asked "how much is written by the seed?" with two
worlds. An atlas asks it properly: lay ALL worlds side by
side and look for what repeats (grammar) vs what differs
(biography).

Discovers runs/family*/families.csv automatically — every
new run joins the atlas without code changes.
"""

import glob
import math
import os
import re

import matplotlib.pyplot as plt

from seal import load, crashes, seal, PAPER
from sealpair import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def discover():
    runs = []
    for csv in sorted(glob.glob(os.path.join(ROOT, 'runs/family*/families.csv'))):
        run = os.path.basename(os.path.dirname(csv))
        m = re.search(r'seed(\d+)', run)
        seed = int(m.group(1)) if m else 7  # runs/family* == seed 7
        label = 'seed %d' % seed if m else f'{run} (seed {seed})'
        runs.append((csv, seed, label))
    return sorted(runs, key=lambda r: (r[1], r[0]))


if __name__ == '__main__':
    runs = discover()
    n = len(runs)
    cols = math.ceil(math.sqrt(n * 1.4))
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4.6 * cols, 5.0 * rows),
                             facecolor=PAPER)
    axes = list(axes.flat) if n > 1 else [axes]
    report = []
    for ax, (path, seed, label) in zip(axes, runs):
        fams, by_tick = load(path)
        seal(ax, fams, by_tick)
        T, spokes, alive, ncr = stats(fams, by_tick)
        ax.set_title(f'{label}\n{T} ticks · {spokes} families · '
                     f'{alive} survived · {ncr} crashes',
                     fontsize=9, family='serif')
        report.append((label, T, spokes, alive, ncr))
    for ax in axes[n:]:
        ax.axis('off')
    fig.suptitle('ATLAS OF WORLDS — one grammar, many biographies',
                 fontsize=13, family='serif')
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = os.path.join(ROOT, 'draws/seal-atlas.png')
    fig.savefig(out, dpi=150, facecolor=PAPER, bbox_inches='tight')
    print('run | ticks | families | survived | crashes')
    for r in report:
        print(' | '.join(map(str, r)))
    print(out)
    print('VERDICT: OK')
