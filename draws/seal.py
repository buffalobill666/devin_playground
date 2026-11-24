"""seal.py — печать прогона: глиф-воск из метрик семейств.

Ex Libris эксперимента: один файл данных -> одна печать,
детерминированная. Читается:
  кольцо           = длительность мира (тики)
  спица            = семейство (угол = рождение, длина = жизнь)
  конец спицы      = точка (дожил до конца) / крест (вымер)
  перламутр точки  = пиковая численность (log)
  внутренняя звезда = финальный вектор 5 черт (среднее по живым)
  насечки кольца   = крахи (провалы суммарной численности >30%)

Вход: runs/family/families.csv -> draws/seal-family.png
"""

import csv
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

TRAITS = ['speed', 'appetite', 'effic', 'vigil', 'resist']
INK, PAPER = '#2a2320', '#faf6ee'


def load(path):
    fams = defaultdict(lambda: defaultdict(list))
    by_tick = defaultdict(int)
    with open(path) as fh:
        for r in csv.DictReader(fh):
            f, t = int(r['fam']), int(r['tick'])
            fams[f]['tick'].append(t)
            fams[f]['n'].append(int(r['n']))
            for tr in TRAITS:
                fams[f][tr].append(float(r[tr]))
            by_tick[t] += int(r['n'])
    for d in fams.values():
        for k in d:
            d[k] = np.array(d[k])
    return fams, by_tick


def crashes(by_tick, min_drop=0.30):
    """Тики, где суммарная численность упала >min_drop к прошлому."""
    ts = sorted(by_tick)
    out = []
    for a, b in zip(ts, ts[1:]):
        if by_tick[a] and by_tick[b] < by_tick[a] * (1 - min_drop):
            out.append(b)
    return out


def seal(ax, fams, by_tick):
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_facecolor(PAPER)

    T = max(by_tick)
    alive_end = {f for f, d in fams.items() if d['tick'].max() == T}

    # внешнее кольцо — длительность
    ring_r = 1.0
    ax.add_patch(plt.Circle((0, 0), ring_r, fill=False, ec=INK,
                            lw=2.2))
    ax.add_patch(plt.Circle((0, 0), ring_r * 0.955, fill=False,
                            ec=INK, lw=0.8))

    # насечки крахов на кольце
    for c in crashes(by_tick):
        a = 2 * np.pi * c / T - np.pi / 2
        ax.plot([0.955 * np.cos(a), np.cos(a)],
                [0.955 * np.sin(a), np.sin(a)], color=INK, lw=3.5)

    # спицы-семейства
    peaks = [d['n'].max() for d in fams.values()]
    pmax = max(peaks) if peaks else 1
    for f, d in fams.items():
        birth, death = d['tick'].min(), d['tick'].max()
        life = (death - birth) / T
        if life < 0.01:
            continue                          # эфемероиды не печатаются
        a = 2 * np.pi * birth / T - np.pi / 2
        L = 0.28 + 0.62 * life                # длина = доля жизни
        pop = np.log1p(d['n'].max()) / np.log1p(pmax)
        ax.plot([0.28 * np.cos(a), L * np.cos(a)],
                [0.28 * np.sin(a), L * np.sin(a)],
                color=INK, lw=0.4 + 2.6 * pop,
                alpha=0.35 + 0.65 * pop)
        r = 0.008 + 0.032 * pop
        if f in alive_end:
            ax.add_patch(plt.Circle((L * np.cos(a), L * np.sin(a)),
                                    r, fc=INK, zorder=5))
        else:
            dx, dy = L * np.cos(a), L * np.sin(a)
            ax.plot([dx - r, dx + r], [dy - r, dy + r],
                    color=INK, lw=1.4, zorder=5)
            ax.plot([dx - r, dx + r], [dy + r, dy - r],
                    color=INK, lw=1.4, zorder=5)

    # звезда финальных черт (среднее по живым на конце)
    last = {tr: np.mean([d[tr][-1] for f, d in fams.items()
                         if f in alive_end]) for tr in TRAITS}
    n = len(TRAITS)
    ang = np.linspace(-np.pi / 2, 3 * np.pi / 2, n, endpoint=False)
    vals = np.array([last[tr] for tr in TRAITS]) * 0.24
    pts = np.c_[vals * np.cos(ang), vals * np.sin(ang)]
    ax.add_patch(plt.Polygon(np.vstack([pts, pts[:1]]),
                             fill=False, ec=INK, lw=1.6))
    ax.add_patch(plt.Polygon(pts, fc=INK, alpha=0.18))
    for p in pts:
        ax.plot([0, p[0]], [0, p[1]], color=INK, lw=0.5, alpha=0.6)
    ax.add_patch(plt.Circle((0, 0), 0.035, fc=INK))


if __name__ == '__main__':
    fams, by_tick = load('runs/family/families.csv')
    fig, ax = plt.subplots(figsize=(7, 7), facecolor=PAPER)
    seal(ax, fams, by_tick)
    fig.savefig('draws/seal-family.png', dpi=170,
                facecolor=PAPER, bbox_inches='tight')
    n_crash = len(crashes(by_tick))
    n_spokes = sum(1 for d in fams.values()
                   if (d['tick'].max() - d['tick'].min())
                   / max(by_tick) >= 0.01)
    print(f'семейств на печати: {n_spokes}, крахов-насечек: {n_crash}')
    print('VERDICT: OK')
