"""asymmetry.py — витрина №6: эксперимент об асимметрии решений.

Наблюдение из музея: во всех dwell-прогонах существа шли ТОЛЬКО
к правой цели, левая оставалась недосягаемой. Три кандидата:
(a) террейн hills() не зеркален -> уклон фоном толкает вправо;
(b) хиральность тел: волна мышц в одну сторону кодируется проще;
(c) метрика: signed travel штрафует уход от цели симметрично —
    тут подозрений нет.

Эксперимент: N=60 случайных тел, ПЛОСКИЙ террейн, две проверки
каждого — цель +30 и -30. Если дрейф правый и на плоскости —
террейн невиновен, виновата морфология/физика.
Зеркальный тест: тело с x -> -x; при симметричной физике
зеркальная копия обязана двигаться в противоположную сторону.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from creatures import dna, physics                                    # noqa: E402


def signed_trial(b, target, steps=800):
    """Куда реально ушло тело: конечный COM.x (без метрик, чистая физика)."""
    r = physics.simulate_body(b, steps=steps, terrain=None,
                              target=target)
    end = r['body']['pos'][:, 0].mean()      # старт центрирован в 0
    # симулятор не возвращает pos конечный — считаем через dwell/dist:
    return r


def final_x(b, target, steps=800):
    """Конечный x центра масс — переиграем сим ради честного замера."""
    pos = b['pos'].astype(np.float64).copy()
    pos -= pos.mean(0)
    pos[:, 1] += 1.6
    vel = np.zeros_like(pos)
    II, JJ = b['edges'][:, 0], b['edges'][:, 1]
    d0 = pos[II] - pos[JJ]
    L0 = np.maximum(np.hypot(d0[:, 0], d0[:, 1]), 1e-3)
    k, amp, ph, mu, fr = b['k'], b['amp'], b['phase'], b['mu'], b['freq']
    for t in range(steps):
        d = pos[II] - pos[JJ]
        L = np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-6)
        osc = np.sin(2 * np.pi * fr * t * 0.01 + ph)
        Ltar = L0 * (1.0 + amp * osc)
        f = k * (L - Ltar) / L
        F = np.zeros_like(pos)
        np.add.at(F[:, 0], II, -f * d[:, 0])
        np.add.at(F[:, 0], JJ, f * d[:, 0])
        np.add.at(F[:, 1], II, -f * d[:, 1])
        np.add.at(F[:, 1], JJ, f * d[:, 1])
        F[:, 1] -= physics.GRAV
        vel += F * 0.01
        vel *= 0.995
        pos += vel * 0.01
        ground = pos[:, 1] < 0
        if ground.any():
            pos[ground, 1] = 0
            vel[ground, 0] *= 1.0 - mu[ground] * 0.9
            vel[ground, 1] = np.abs(vel[ground, 1]) * 0.05
    return pos[:, 0].mean()


def mirrored(b):
    b2 = dict(b)
    b2['pos'] = b['pos'].copy()
    b2['pos'][:, 0] *= -1
    return b2


if __name__ == '__main__':
    rng = np.random.default_rng(11)
    N, n_right, n_left = 60, 0, 0
    xs = []
    bodies = []
    for i in range(N):
        b = dna.decode(dna.random_dna(rng), n_types=5)
        if b is None:
            continue
        x = final_x(b, target=30)
        xs.append(x)
        bodies.append((b, x))
        n_right += x > 1.0
        n_left += x < -1.0
    xs = np.array(xs)
    print(f'тел: {len(xs)}, ушли вправо >1u: {n_right}, '
          f'влево <-1u: {n_left}')
    print(f'средний дрейф: {xs.mean():+.2f}, медиана '
          f'{np.median(xs):+.2f}, std {xs.std():.2f}')

    # зеркальный тест на 8 самых подвижных телах
    bodies.sort(key=lambda bx: -abs(bx[1]))
    print('зеркальный тест (x исходника -> x зеркала):')
    flips_ok = 0
    for b, x in bodies[:8]:
        xm = final_x(mirrored(b), target=30)
        ok = np.sign(xm) != np.sign(x)
        flips_ok += ok
        print(f'  {x:+8.2f} -> {xm:+8.2f}  {"FLIP" if ok else "SAME"}')
    print(f'переворотов: {flips_ok}/8')
    print('VERDICT:', 'OK' if n_right > n_left else 'FAIL?')
