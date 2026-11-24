"""bestiary.py — бестиарий мира: портреты семейств по генам.

Морфология кодирует вектор черт (последняя запись семейства
в runs/family/families.csv):
  speed    -> длина ног и вытянутость тела
  appetite -> размер рта и брюха
  effic    -> обтекаемость (узость тела)
  vigil    -> число и размер глаз
  resist   -> панцирные щитки

Девять крупнейших семейств -> draws/bestiary.png.
"""

import csv
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Circle, Ellipse, Polygon

TRAITS = ['speed', 'appetite', 'effic', 'vigil', 'resist']


def last_traits(path):
    fams = defaultdict(lambda: {'n': 0})
    with open(path) as fh:
        for r in csv.DictReader(fh):
            f = int(r['fam'])
            fams[f]['n'] = max(fams[f]['n'], int(r['n']))
            for tr in TRAITS:                    # последняя запись
                fams[f][tr] = float(r[tr])
    return fams


def normalize(fams, fam_ids):
    """Черты -> 0..1 по разбросу выбранных семейств."""
    out = {}
    for tr in TRAITS:
        vals = [fams[f][tr] for f in fam_ids]
        lo, hi = min(vals), max(vals)
        rng = hi - lo or 1
        for f in fam_ids:
            out.setdefault(f, {})[tr] = (fams[f][tr] - lo) / rng
    return out


def creature(ax, t, name):
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.5, 1.7)
    ax.set_aspect('equal')
    ax.axis('off')
    ink = '#2a2320'

    bw = 0.65 + 0.9 * t['speed']
    bh = 0.45 + 0.65 * t['appetite']
    ax.add_patch(Ellipse((0, 0.1), bw, bh, fc='#f4ead8', ec=ink,
                         lw=1.6, zorder=3))

    # ноги: 3-5, длина по speed
    n_legs = 3 + int(2 * t['speed'])
    for i in range(n_legs):
        x = -bw / 2.6 + i * (bw / 1.3) / max(n_legs - 1, 1)
        ln = 0.15 + 0.8 * t['speed']
        ax.plot([x, x], [-bh / 2 + 0.12, -bh / 2 + 0.12 - ln],
                color=ink, lw=1.6, zorder=2)

    # панцирь: щитки-дуги; при высоком resist — шипы
    n_sc = int(1 + 5 * t['resist'])
    for i in range(n_sc):
        x0 = -bw / 2 + 0.08 + i * (bw - 0.16) / max(n_sc, 1)
        cw = (bw - 0.16) / n_sc
        if t['resist'] > 0.66:
            ax.add_patch(Polygon([(x0, 0.1 + bh / 2 - 0.1),
                                  (x0 + cw / 2, 0.1 + bh / 2 + 0.28),
                                  (x0 + cw, 0.1 + bh / 2 - 0.1)],
                                 fc='#f4ead8', ec=ink, lw=1.2,
                                 zorder=4))
        else:
            ax.add_patch(Arc((x0 + cw / 2, 0.1 + bh / 2 - 0.12),
                             cw, 0.4, theta1=10, theta2=170,
                             ec=ink, lw=1.4, zorder=4))

    # глаза: 1-4, радиус по vigil
    n_eyes = 1 + int(3 * t['vigil'])
    for i in range(n_eyes):
        ex = bw / 4 + i * 0.2 - (n_eyes - 1) * 0.09
        er = 0.05 + 0.12 * t['vigil']
        ax.add_patch(Circle((ex, 0.18), er, fc='white', ec=ink,
                            lw=1.2, zorder=5))
        ax.add_patch(Circle((ex, 0.18), er * 0.4, fc=ink, zorder=6))

    # рот: дуга, раскрыв по appetite
    m = 0.1 + 0.35 * t['appetite']
    ax.add_patch(Arc((bw / 4, -0.1), m * 2, m * 1.7,
                     theta1=200, theta2=340, ec=ink, lw=1.6,
                     zorder=5))

    ax.set_title(f'fam {name}', fontsize=9)
    for i, tr in enumerate(TRAITS):
        ax.text(-1.5, -0.85 - i * 0.14, tr[:5], fontsize=5,
                family='monospace', va='center')
        ax.add_patch(plt.Rectangle((-0.9, -0.9 - i * 0.14),
                                   t[tr] * 1.8, 0.08, fc='#8a7a5c'))


if __name__ == '__main__':
    fams = last_traits('runs/family/families.csv')
    top = sorted(fams, key=lambda f: -fams[f]['n'])[:9]
    norm = normalize(fams, top)
    fig, axes = plt.subplots(3, 3, figsize=(10, 10))
    for ax, f in zip(axes.flat, top):
        creature(ax, norm[f], f)
    fig.suptitle('Бестиарий: девять крупнейших семейств '
                 '(черты — относительные, внутри девятки)',
                 fontsize=13)
    fig.tight_layout()
    fig.savefig('draws/bestiary.png', dpi=150,
                facecolor='#faf6ee', bbox_inches='tight')
    print('семейств нарисовано:', len(top), 'из', len(fams))
    print('VERDICT: OK' if len(top) == 9 else 'FAIL')
