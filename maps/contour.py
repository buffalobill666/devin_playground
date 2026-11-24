"""contour.py — topographic survey of the continent.

Third cartographic genre on the same world (after the
political map and the transit schematic): isolines. Same
heightfield recipe as continent.py (unseeded rng like the
original — the survey is of *a* continent of this family,
not of the same tile). Hypsometric fill + contour lines at
100 m + labels on major levels. The coastline (h==sea) is
the zero contour — it should trace the same west/south
edge the political map drew.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'conlang'))
from continent import continent  # noqa: E402
from gen import word  # noqa: E402
import random  # noqa: E402

N = 400
SEA = 0.30
rng = np.random.default_rng(7)


def main():
    h = continent(N)
    # normalise: sea at 0, land to ~2500m
    elev = np.clip((h - SEA) / (1 - SEA), 0, 1) * 2500
    fig, ax = plt.subplots(figsize=(10, 9))
    ax.set_facecolor('#8fb3c9')
    land = np.ma.masked_where(elev <= 0, elev)
    ax.contourf(elev, levels=np.linspace(0, 2500, 26),
                cmap='gist_earth', alpha=.85)
    cs = ax.contour(land, levels=np.arange(0, 2501, 100),
                    colors='#4a3c28', linewidths=.35)
    ax.clabel(cs, levels=cs.levels[::5], fmt='%d m',
              fontsize=7, inline=True)
    # coastline emphasised
    ax.contour(elev, levels=[1], colors='#1a3a4a',
               linewidths=1.6)
    rr = random.Random(11)
    name = word(rr).upper()
    ax.set_title(f'KUWAKA SURVEY — {name} sheet, 1:250 000',
                 fontsize=11, family='serif')
    ax.set_xticks([]); ax.set_yticks([])
    fig.savefig(os.path.join(os.path.dirname(__file__),
                             'contour.png'), dpi=150,
                bbox_inches='tight', facecolor='#e8e0cc')
    print('saved maps/contour.png')


if __name__ == '__main__':
    main()
