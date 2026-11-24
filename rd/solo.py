"""solo.py — одиночный triple-кольцевой организм: солитон?

i3 показал: triple-ядро [.25,.5,.75] даёт крупные кольца —
морфологически ближайшее к Chan-орбуму. Тест: вырезать один,
посадить в пустое поле, то же ядро, 900 шагов.
Метрики: жив/мертв, счёт блобов (почкуется ли),
сдвиг центроида (gliding).
"""

import numpy as np

from orbium import fft_kernel, step, N, R
from glide import biggest_blob, centroid
from multik import grow
from soliton import count_blobs

TRIPLE = ([0.25, 0.5, 0.75], [1.0, 0.5, 1.0])

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import os
    rng = np.random.default_rng(7)
    Fk = fft_kernel(*TRIPLE)
    colony = grow(Fk, rng)
    mask = biggest_blob(colony)
    ys, xs = np.where(mask)
    cy, cx = int(ys.mean()), int(xs.mean())
    h = 2 * R
    donor = colony[cy - h:cy + h, cx - h:cx + h]
    A = np.zeros((N, N))
    A[N // 2 - h:N // 2 + h, N // 2 - h:N // 2 + h] = donor

    path = [centroid(A)]
    counts = [count_blobs(A)]
    snaps = [A.copy()]
    for i in range(900):
        A = step(A, Fk, 0.15, 0.015)
        if i % 150 == 149:
            path.append(centroid(A))
            counts.append(count_blobs(A))
            snaps.append(A.copy())

    drift = np.hypot(path[-1][0] - path[0][0],
                     path[-1][1] - path[0][1])
    print(f'blob {mask.sum()} cells -> counts {counts} '
          f'mass {A.sum():.0f} drift {drift:.1f}')
    print('VERDICT:', 'GLIDES' if A.sum() > 30 and drift > 5 and
          counts[-1] == 1 else
          ('SOLITON (stable, stationary)' if counts[-1] == 1
           and A.sum() > 30 else
           'colonial/dead' if A.sum() > 30 else 'DIED'))

    fig, axes = plt.subplots(1, 4, figsize=(13, 3.4))
    axes[0].imshow(colony, cmap='magma', vmin=0, vmax=1)
    axes[0].set_title('triple colony')
    for ax, s, t in zip(axes[1:], snaps[1::2], ('t=300', 't=750', 't=900')):
        ax.imshow(s, cmap='magma', vmin=0, vmax=1)
        ax.set_title(f'lone ring {t}')
    for ax in axes:
        ax.axis('off')
    fig.tight_layout()
    fig.savefig(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'solo.png'),
        dpi=140, bbox_inches='tight')
