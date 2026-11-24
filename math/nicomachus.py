"""nicomachus.py — proof without words: sum k^3 = (sum k)^2.

Nicomachus' identity. The square of side T(n)=n(n+1)/2
partitions into nested L-gnomons; gnomon k has area
T(k)^2 - T(k-1)^2 = k * (T(k)+T(k-1)) = k * k^2 = k^3.

The drawing shows each gnomon actually TILED by k blocks
of side k: for odd k they fit whole; for even k one block
splits into two halves that live at opposite gnomon ends.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

N = 7


def T(k):
    return k * (k + 1) // 2


def gnomon_tiles(k):
    """Rectangles (x, y, w, h, half?) tiling gnomon k with k
    blocks of area k*k each (half blocks pair up)."""
    tiles = []
    tk, tm = T(k), T(k - 1)
    # top strip: y in [tm, tk), height k, width tk
    x = 0
    while x + k <= tk:
        tiles.append((x, tm, k, k, False))
        x += k
    if x < tk:                               # even k: half corner
        tiles.append((x, tm, tk - x, k, True))
    # left strip: x in [tm, tk), width k, height tm
    y = 0
    while y + k <= tm:
        tiles.append((tm, y, k, k, False))
        y += k
    if y < tm:                               # even k: half
        tiles.append((tm, y, k, tm - y, True))
    return tiles


if __name__ == '__main__':
    # numeric check
    lhs = sum(k ** 3 for k in range(1, N + 1))
    rhs = T(N) ** 2
    print(f'sum k^3 (k=1..{N}) = {lhs} == T({N})^2 = {rhs}:',
          lhs == rhs)

    # area check of the tiling: every gnomon == k^3
    for k in range(1, N + 1):
        area = sum(w * h for _, _, w, h, _ in gnomon_tiles(k))
        assert area == k ** 3, (k, area)
    print('tiling: every gnomon tiles to exactly k^3: OK')

    fig, ax = plt.subplots(figsize=(8, 8))
    cmap = plt.cm.viridis(np.linspace(0.15, 0.9, N))
    for k in range(1, N + 1):
        for x, y, w, h, half in gnomon_tiles(k):
            ax.add_patch(Rectangle((x, y), w, h,
                                   facecolor=cmap[k - 1],
                                   edgecolor='k', lw=0.8,
                                   alpha=0.55 if half else 0.9))
        # label gnomon inside its corner region
        ax.text(T(k - 1) + k / 2, T(k) - k / 2, f'{k}³',
                ha='center', va='center', fontsize=11,
                fontweight='bold')
    S = T(N)
    ax.set_xlim(-0.5, S + 0.5)
    ax.set_ylim(-0.5, S + 0.5)
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f'1³+2³+…+{N}³  =  (1+2+…+{N})²  =  {S}²\n'
                 f'each gnomon k is {k}³ — tiled by k blocks of k×k',
                 fontsize=12)
    fig.tight_layout()
    fig.savefig('math/nicomachus.png', dpi=140)
    print('-> math/nicomachus.png')
