"""sealpair.py — две печати рядом: сравнительная экслибриология.

Печать — глиф мира (seal.py). Две печати рядом — уже сравнение
миров: одинаковые правила, разные seed -> разная география
династий. Вопрос артефакта: насколько история мира написана
seed'ом, а насколько — правилами?

Вход: runs/family + runs/family-seed8 -> draws/seal-pair.png
"""

import os

import matplotlib.pyplot as plt

from seal import load, crashes, seal, PAPER

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = [(os.path.join(ROOT, 'runs/family/families.csv'), 'seed 7'),
        (os.path.join(ROOT, 'runs/family-seed8/families.csv'), 'seed 8')]


def stats(fams, by_tick):
    T = max(by_tick)
    spokes = sum(1 for d in fams.values()
                 if (d['tick'].max() - d['tick'].min()) / T >= 0.01)
    alive = sum(1 for d in fams.values() if d['tick'].max() == T)
    return T, spokes, alive, len(crashes(by_tick))


if __name__ == '__main__':
    fig, axes = plt.subplots(1, 2, figsize=(13, 7.4),
                             facecolor=PAPER)
    report = []
    for ax, (path, label) in zip(axes, RUNS):
        fams, by_tick = load(path)
        seal(ax, fams, by_tick)
        T, spokes, alive, ncr = stats(fams, by_tick)
        ax.set_title(f'{label}: {T} тиков, {spokes} семейств, '
                     f'{alive} дожило, {ncr} крах.',
                     fontsize=10, family='serif')
        report.append((label, T, spokes, alive, ncr))
    fig.savefig(os.path.join(ROOT, 'draws/seal-pair.png'), dpi=160,
                facecolor=PAPER, bbox_inches='tight')
    for r in report:
        print(' | '.join(map(str, r)))
    print('draws/seal-pair.png')
    print('VERDICT: OK')
