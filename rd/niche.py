"""niche.py — скан (mu, sigma) на нишу solitary-orbium.

i25 показал: адиабатические орбы ре-колонизируют поле —
режим самораспространения. Настоящий блуждающий Orbium
нуждается в маргинальной стабильности: параметры, где
одиночный blob ЖИВЁТ, но не почкуется.

Тест на клетке сетки: пересадить один и тот же blob,
800 шагов, метрики:
  alive     — масса > 30 и структура (std > .05)
  spread    — масса > 3x исходной (колонизация)
  drift     — сдвиг центроида (gliding)

Предсказание: под mu — смерть; над mu — колонизация;
ниша — тонкая полоса между ними, если она вообще есть.
"""

import numpy as np

from orbium import fft_kernel, speckle, step, N, R
from glide import grow_colony, biggest_blob, centroid


def trial(A0, Fk, mu, sig, steps=800):
    A = A0.copy()
    c0 = centroid(A)
    m0 = A.sum()
    for _ in range(steps):
        A = step(A, Fk, mu, sig)
        if A.sum() < 1:
            break
    cy = centroid(A) if A.sum() > 1 else c0
    drift = np.hypot(cy[0] - c0[0], cy[1] - c0[1])
    return dict(mass=A.sum(), spread=A.sum() > 3 * m0,
                drift=drift,
                alive=A.sum() > 30 and A.std() > 0.05)


if __name__ == '__main__':
    rng = np.random.default_rng(7)
    colony = grow_colony(rng)
    mask = biggest_blob(colony)
    ys, xs = np.where(mask)
    cy, cx = int(ys.mean()), int(xs.mean())
    h = 2 * R
    donor = colony[cy - h:cy + h, cx - h:cx + h]
    A0 = np.zeros((N, N))
    A0[N // 2 - h:N // 2 + h, N // 2 - h:N // 2 + h] = donor
    print(f'blob: {mask.sum()} cells, mass {A0.sum():.0f}')

    Fk = fft_kernel()
    print(f'{"mu":>6} {"sigma":>6} | {"mass":>6} {"drift":>6}  verdict')
    grid = []
    for mu in (0.12, 0.135, 0.15, 0.165, 0.18):
        for sig in (0.012, 0.015, 0.02, 0.03):
            r = trial(A0, Fk, mu, sig)
            if not r['alive']:
                v = 'dead'
            elif r['spread']:
                v = 'COLONIZES'
            elif r['drift'] > 5:
                v = 'GLIDES'
            else:
                v = 'soliton*'
            grid.append((mu, sig, v, r['mass'], r['drift']))
            print(f'{mu:6.3f} {sig:6.3f} | {r["mass"]:6.0f} '
                  f'{r["drift"]:6.1f}  {v}', flush=True)
    niches = [g for g in grid if g[2] in ('GLIDES', 'soliton*')]
    print('VERDICT:', f'{len(niches)} niche cells: '
          + ', '.join(f'({m},{s})={v}' for m, s, v, _, _ in niches)
          if niches else 'no solitary niche found')
