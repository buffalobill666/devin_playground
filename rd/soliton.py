"""soliton.py — поиск ниши одиночного организма по ЧИСЛУ блобов.

i27 скан мерил массу — но солитон это не масса, а СЧЁТ:
один организм, который живёт и не почкуется. Здесь —
тот же трансплантат, но метрика = количество связных
организмов через 1200 шагов + стабильность счёта.

Кандидатная зона: граница colonize/dead из niche.py —
mu вокруг 0.14-0.16, sigma вокруг 0.010-0.016.
Также бонусом: нативный посев прямо в точке (не
трансплантат) — спекла в центре, тот же подсчёт.
"""

import numpy as np
from collections import deque

from orbium import fft_kernel, speckle, step, N, R
from glide import grow_colony, biggest_blob, centroid


def count_blobs(A, thr=0.15):
    seen = np.zeros_like(A, bool)
    n = 0
    for y0 in range(N):
        for x0 in range(N):
            if A[y0, x0] > thr and not seen[y0, x0]:
                n += 1
                q = deque([(y0, x0)])
                seen[y0, x0] = True
                while q:
                    y, x = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < N and 0 <= nx < N \
                                and A[ny, nx] > thr \
                                and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
    return n


def trial(A0, Fk, mu, sig, steps=1200):
    A = A0.copy()
    counts = [count_blobs(A)]
    for i in range(steps):
        A = step(A, Fk, mu, sig)
        if i % 200 == 199:
            counts.append(count_blobs(A))
    counts.append(count_blobs(A))
    return A, counts


if __name__ == '__main__':
    rng = np.random.default_rng(7)
    colony = grow_colony(rng)
    mask = biggest_blob(colony)
    ys, xs = np.where(mask)
    cy, cx = int(ys.mean()), int(xs.mean())
    h = 2 * R
    donor = colony[cy - h:cy + h, cx - h:cx + h]
    T0 = np.zeros((N, N))
    T0[N // 2 - h:N // 2 + h, N // 2 - h:N // 2 + h] = donor
    Fk = fft_kernel()

    print('== transplant to boundary zone ==')
    print(f'{"mu":>6} {"sig":>6} | {"counts(t)":>30}  verdict')
    for mu in (0.14, 0.145, 0.15, 0.155, 0.16):
        for sig in (0.010, 0.013, 0.016):
            A, counts = trial(T0, Fk, mu, sig)
            fin = counts[-1]
            if fin == 0:
                v = 'dead'
            elif fin == 1:
                v = 'SOLITON?'
            elif fin > 3:
                v = 'colonial'
            else:
                v = f'{fin} organisms'
            print(f'{mu:6.3f} {sig:6.3f} | '
                  f'{str(counts):>30}  {v}', flush=True)

    print('== native seed (speckle at point) ==')
    for mu, sig in [(0.145, 0.013), (0.15, 0.013)]:
        A, counts = trial(speckle(np.random.default_rng(11)),
                          Fk, mu, sig)
        print(f'{mu:6.3f} {sig:6.3f} | '
              f'{str(counts):>30}  counts', flush=True)
