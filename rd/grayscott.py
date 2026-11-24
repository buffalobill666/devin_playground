"""grayscott.py — реакция-диффузия Грея-Скотта, ~80 строк numpy.

U, V — поля концентраций. Узоры (кораллы, пятна, лабиринты)
возникают из баланса подпитки F и гашения k — одни и те же
уравнения, разные параметры = разные «организмы» поля.

  dU = Du*lap(U) - U*V^2 + F*(1-U)
  dV = Dv*lap(V) + U*V^2 - (F+k)*V
"""

import numpy as np
from PIL import Image

N, DT = 256, 1.0
DU, DV = 0.2097, 0.105  # масштаб Karl Sims: при слабой диффузии фронт стынет


def lap(a):
    # 9-точечный стенсил Пирсона: веса 0.05 диагонали, 0.2 орто, -1 центр
    return (0.2 * (np.roll(a, 1, 0) + np.roll(a, -1, 0)
                   + np.roll(a, 1, 1) + np.roll(a, -1, 1))
            + 0.05 * (np.roll(a, (1, 1), (0, 1)) + np.roll(a, (1, -1), (0, 1))
                      + np.roll(a, (-1, 1), (0, 1))
                      + np.roll(a, (-1, -1), (0, 1))) - a)


def run(f, k, steps=14000, seed=7):
    rng = np.random.default_rng(seed)
    u = np.ones((N, N))
    v = np.zeros((N, N))
    # посев: россыпь мелких пятен U=0.5 / V=0.25 (классика Пирсона)
    for _ in range(6):
        y, x = rng.integers(20, N - 20, 2)
        u[y:y + 8, x:x + 8] = 0.5
        v[y:y + 8, x:x + 8] = 0.25
    v += rng.random((N, N)) * 0.02
    for _ in range(steps):
        uvv = u * v * v
        u += DT * (DU * lap(u) - uvv + f * (1 - u))
        v += DT * (DV * lap(v) + uvv - (f + k) * v)
    return v


def save(v, path):
    # палитра: глубокое море -> бирюза -> кость
    t = np.clip((v - v.min()) / (v.max() - v.min() + 1e-9), 0, 1)
    img = np.zeros((*t.shape, 3), np.uint8)
    img[..., 0] = (26 + t * 200).astype(np.uint8)
    img[..., 1] = (38 + t * 190).astype(np.uint8)
    img[..., 2] = (63 + t * 160).astype(np.uint8)
    Image.fromarray(img).save(path)


if __name__ == '__main__':
    for name, f, k in [('coral', 0.0545, 0.062),
                       ('mitosis', 0.0367, 0.0649)]:
        print('running', name, 'F', f, 'k', k)
        save(run(f, k), f'rd/{name}.png')
        print('  -> rd/%s.png' % name)
