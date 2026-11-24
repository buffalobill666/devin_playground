"""glide.py — вырезать одиночную орбу и дать ей ползти.

Продолжение i21: адиабатика дала ПОПУЛЯЦИЮ удлинённых орб —
но классический Orbium это одиночный блуждающий организм.
Здесь: выращиваем колонию, вырезаем один blob (flood fill),
пересаживаем в пустое поле, следим за центроидом.

Вердикт: организм жив (масса+структура) И центроид смещается
(gliding) — или жив и стоит (stationary soliton — тоже
результат, у Chan такие есть).
"""

import numpy as np
from collections import deque

from orbium import fft_kernel, speckle, step, N, R

MU, SIGMA = 0.15, 0.015


def grow_colony(rng):
    Fk = fft_kernel()
    A = speckle(rng)
    for _ in range(300):
        A = step(A, Fk, 0.135, 0.03)
    for i in range(600):
        f = i / 600
        A = step(A, Fk, 0.135 + 0.015 * f, 0.03 - 0.015 * f)
    return A


def biggest_blob(A, thr=0.15):
    """Flood-fill по клеткам > thr; возвращает маску и бокс
    самого массивного связного организма."""
    seen = np.zeros_like(A, bool)
    best, bbest = None, 0
    for y0 in range(N):
        for x0 in range(N):
            if A[y0, x0] > thr and not seen[y0, x0]:
                q = deque([(y0, x0)])
                seen[y0, x0] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < N and 0 <= nx < N \
                                and A[ny, nx] > thr and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                if len(cells) > bbest:
                    bbest = len(cells)
                    best = cells
    if not best:
        return None
    mask = np.zeros_like(A, bool)
    for y, x in best:
        mask[y, x] = True
    return mask


def centroid(A):
    s = A.sum()
    y, x = np.indices(A.shape)
    return (y * A).sum() / s, (x * A).sum() / s


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(7)
    colony = grow_colony(rng)
    mask = biggest_blob(colony)
    assert mask is not None, 'no organism found'

    # пересадка: blob -> центр пустого поля с полем-окном 4R
    ys, xs = np.where(mask)
    cy, cx = int(ys.mean()), int(xs.mean())
    h = 2 * R
    donor = colony[max(0, cy - h):cy + h, max(0, cx - h):cx + h]
    A = np.zeros((N, N))
    oy, ox = donor.shape
    A[N // 2 - oy // 2:N // 2 - oy // 2 + oy,
      N // 2 - ox // 2:N // 2 - ox // 2 + ox] = donor

    Fk = fft_kernel()
    path = [centroid(A)]
    snaps = [A.copy()]
    for i in range(900):
        A = step(A, Fk, MU, SIGMA)
        if i % 100 == 99:
            path.append(centroid(A))
            snaps.append(A.copy())

    drift = np.hypot(path[-1][0] - path[0][0],
                     path[-1][1] - path[0][1])
    dists = [np.hypot(path[i + 1][0] - path[i][0],
                      path[i + 1][1] - path[i][1])
             for i in range(len(path) - 1)]
    alive = A.sum() > 50 and A.std() > 0.05
    recolonized = A.sum() > 10 * mask.sum()
    print(f'blob: {mask.sum()} cells; alive={alive} '
          f'mass={A.sum():.0f}; total drift {drift:.1f} cells '
          f'(per-100: {[f"{d:.1f}" for d in dists]})')
    print('VERDICT:', 'GLIDES' if alive and drift > 5 else
          ('RECOLONIZED — colonial regime, not a soliton'
           if recolonized else
           ('STATIONARY but alive' if alive else 'DIED')))

    fig, axes = plt.subplots(1, 4, figsize=(13, 3.4))
    axes[0].imshow(colony, cmap='magma', vmin=0, vmax=1)
    axes[0].set_title('colony (source)')
    for ax, s, t in zip(axes[1:], snaps[::3], ('t=100', 't=400', 't=900')):
        ax.imshow(s, cmap='magma', vmin=0, vmax=1)
        ax.set_title(f'lone organism {t}')
    for ax in axes:
        ax.axis('off')
    fig.tight_layout()
    import os
    fig.savefig(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'glide.png'),
        dpi=140, bbox_inches='tight')
