"""multik.py — другие фенотипы через мульти-кольцевые ядра.

Вердикт дуги Orbium: солитон живёт в другом ядре. Multi-ring
(beta>1) — именно тот рычаг, из которого Chan вытащил тысячи
видов. Три ядра, одна процедура (адиабатика -> канон):
  single  — контроль (классика)
  double  — кольца 0.3 + 0.6, веса 1 : 0.5
  triple  — кольца 0.25 + 0.5 + 0.75, веса 1 : 0.5 : 1
Метрика: число и форма организмов в конце + спектр размеров.
"""

import numpy as np

from orbium import fft_kernel, speckle, step, N, R
from soliton import count_blobs

KERNELS = {
    'single': ([0.5], [1.0]),
    'double': ([0.3, 0.6], [1.0, 0.5]),
    'triple': ([0.25, 0.5, 0.75], [1.0, 0.5, 1.0]),
}


def grow(Fk, rng, steps=900):
    A = speckle(rng)
    for _ in range(300):
        A = step(A, Fk, 0.135, 0.03)
    for i in range(600):
        f = i / 600
        A = step(A, Fk, 0.135 + 0.015 * f, 0.03 - 0.015 * f)
    for _ in range(steps - 900):
        A = step(A, Fk, 0.15, 0.015)
    return A


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(7)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, (name, (pk, wt)) in zip(axes, KERNELS.items()):
        Fk = fft_kernel(pk, wt)
        A = grow(Fk, rng)
        n = count_blobs(A)
        ax.imshow(A, cmap='magma', vmin=0, vmax=1)
        ax.set_title(f'{name} {pk}\nblobs={n} mass={A.sum():.0f}')
        ax.axis('off')
        print(f'{name}: blobs={n} mass={A.sum():.0f} '
              f'std={A.std():.2f}', flush=True)
    fig.tight_layout()
    import os
    fig.savefig(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'multik.png'),
        dpi=140, bbox_inches='tight')
    print('saved rd/multik.png')
