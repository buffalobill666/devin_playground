"""climate.py — fourth cartographic genre: the climate sheet.

continent.py drew politics, contour.py drew the land itself;
this sheet draws the sky above it. Two derived fields:

  T(y, elev) = T_equator + lat_lapse*(1-y) - lapse*elev_km
      — warm south coast, cold north highlands
  R = moisture field + orographic bonus on south-facing
      rises (rain shadow on their north sides)

Zones are Whittaker-lite bins on (T, R): tundra, boreal
forest, cold steppe, temperate forest, steppe, warm
forest, savanna, desert, sea. Same seed-7 terrain recipe
as the political map — a third reading of the same
continent-family (see history c5/и9: 'seed 7' is a figure
of speech, the rng is unseeded — family, not tile).
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from continent import continent, moisture        # noqa: E402

N, SEA = 420, 0.30

ZONES = [
    ('sea', '#5b84a8'),
    ('tundra', '#c8d4dc'),
    ('boreal forest', '#4d7a5c'),
    ('cold steppe', '#9aa87a'),
    ('temperate forest', '#3e8a5a'),
    ('steppe', '#c9b877'),
    ('warm forest', '#2f7a52'),
    ('savanna', '#d9c26a'),
    ('desert', '#e0b070'),
]
ZID = {name: i for i, (name, _) in enumerate(ZONES)}


def climate_fields(n):
    h = continent(n)
    elev = np.clip((h - SEA) / (1 - SEA), 0, 1) * 2500   # meters
    y = np.mgrid[0:n, 0:n][0] / n
    T = 27.0 - 30.0 * (1 - y) - 0.0065 * elev            # °C
    # orographic: south-facing rise gets wetter, north lee drier
    dh_dy = np.gradient(elev, axis=0)
    oro = np.clip(dh_dy / 40.0, -0.25, 0.35)
    R = np.clip(moisture(n) + oro, 0, 1)
    return elev, T, R


def zone_of(T, R, sea):
    z = np.select(
        [sea, T < 0, T < 6, T < 16, True],
        [ZID['sea'],
         ZID['tundra'],
         np.where(R < 0.35, ZID['cold steppe'],
                  ZID['boreal forest']),
         np.where(R < 0.35, ZID['steppe'],
                  ZID['temperate forest']),
         np.select([R < 0.22, R < 0.45],
                   [ZID['desert'], ZID['savanna']],
                   ZID['warm forest'])])
    return z


def main():
    elev, T, R = climate_fields(N)
    sea = elev <= 0
    z = zone_of(T, R, sea)
    fig, ax = plt.subplots(figsize=(10, 9))
    cmap = ListedColormap([c for _, c in ZONES])
    norm = BoundaryNorm(np.arange(len(ZONES) + 1) - 0.5, cmap.N)
    ax.imshow(z, cmap=cmap, norm=norm, interpolation='nearest')
    ax.contour(elev, levels=[1500, 2200], colors='#00000066',
               linewidths=0.5)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title('NOTU — climate sheet: Whittaker bins on '
                 '(T, R), orographic shadows kept',
                 fontfamily='monospace', fontsize=11)
    handles = [Patch(color=c, label=n) for n, c in ZONES[1:]]
    ax.legend(handles=handles, loc='lower left', fontsize=8,
              framealpha=0.9)
    # report the zone census — a climate claim must carry numbers
    land = ~sea
    counts = {name: int(((z == ZID[name]) & land).sum())
              for name, _ in ZONES[1:]}
    total = land.sum()
    print('zone census (% of land):')
    for name, k in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f'  {name:>18}: {100 * k / total:5.1f}%')
    out = os.path.join(os.path.dirname(__file__), 'climate.png')
    fig.savefig(out, dpi=110, bbox_inches='tight')
    print('saved', out)


if __name__ == '__main__':
    main()
