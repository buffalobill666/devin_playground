"""orbium.py — охота за Orbium: адиабатическая нуклеация.

Мёртвые гипотезы (честный след):
- крапина 30% -> Orbium умирает (дисперсия U >> sigma)
- плотный шум [0,1] -> U~0.5 >> mu, мгновенная смерть
- плотный тихий шум [0,2*mu] -> все клетки в колоколе,
  растут до 1 -> U~0.5 -> смерть. Положительная обратная
  связь без самоограничения: узкий sigma не тормозит.

Рабочая идея: АДИАБАТА. Знаем точку, где жизнь есть:
mu=0.135, s=0.03 (колония колец в lenia.py). Варим её,
потом МЕДЛЕННО дрейфуем mu 0.135->0.15, s 0.03->0.015 —
структура адаптируется по мере затягивания колокола,
как выращивание кристалла при охлаждении.
"""

import numpy as np

N, R = 128, 13
RING_MU, RING_SIG, DT = 0.5, 0.15, 0.1


def kernel():
    ax = np.arange(-R, R + 1)
    X, Y = np.meshgrid(ax, ax)
    D = np.sqrt(X ** 2 + Y ** 2) / R
    K = np.where(D <= 1,
                 np.exp(-((D - RING_MU) / RING_SIG) ** 2 / 2), 0)
    return K / K.sum()


def fft_kernel():
    K = kernel()
    Kp = np.zeros((N, N), dtype=complex)
    Kp[:2 * R + 1, :2 * R + 1] = K
    return np.fft.fft2(np.roll(Kp, (-R, -R), (0, 1)))


def speckle(rng, side=2 * R, fill=0.3):
    A = np.zeros((N, N))
    c = N // 2
    h = side // 2
    A[c - h:c - h + side, c - h:c - h + side] = \
        (rng.uniform(0, 1, (side, side)) *
         (rng.uniform(0, 1, (side, side)) < fill))
    return A


def step(A, Fk, mu, sig):
    U = np.fft.ifft2(np.fft.fft2(A) * Fk).real
    g = 2 * np.exp(-((U - mu) / sig) ** 2 / 2) - 1
    return np.clip(A + DT * g, 0, 1)


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(7)
    Fk = fft_kernel()

    A = speckle(rng)
    snaps = [(A.copy(), 'seed')]
    mass = [A.sum()]

    # фаза 1: варка в рабочих параметрах (колония колец)
    for _ in range(300):
        A = step(A, Fk, 0.135, 0.03)
        mass.append(A.sum())
    snaps.append((A.copy(), 'mu=.135 s=.03 t=300'))

    # фаза 2: адиабатический дрейф к канону
    mu0, mu1, s0, s1 = 0.135, 0.15, 0.03, 0.015
    T = 600
    for i in range(T):
        f = i / T
        A = step(A, Fk, mu0 + (mu1 - mu0) * f, s0 + (s1 - s0) * f)
        mass.append(A.sum())
    snaps.append((A.copy(), 'annealed t=900'))

    # фаза 3: жизнь в каноническом режиме
    for _ in range(800):
        A = step(A, Fk, mu1, s1)
        mass.append(A.sum())
    snaps.append((A.copy(), 'orbium? t=1700'))

    fig, axes = plt.subplots(1, 5, figsize=(15, 3.6))
    for ax, (s, t) in zip(axes[:4], snaps):
        ax.imshow(s, cmap='magma', vmin=0, vmax=1)
        ax.set_title(t, fontsize=9)
        ax.axis('off')
    axes[4].plot(mass)
    axes[4].axvline(300, ls='--', c='gray', lw=0.8)
    axes[4].axvline(900, ls='--', c='gray', lw=0.8)
    axes[4].set_title('mass')
    fig.tight_layout()
    fig.savefig('rd/orbium.png', dpi=140, bbox_inches='tight')

    tail = np.mean(mass[-100:])
    alive = tail > 50 and A.std() > 0.05
    print(f'mass: {mass[0]:.0f} -> {mass[-1]:.0f} '
          f'(tail {tail:.0f}), std {A.std():.2f}')
    print('VERDICT:', 'OK — Orbium жив' if alive else 'FAIL')
