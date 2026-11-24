"""lenia.py — Lenia: непрерывный клеточный автомат (Chan 2019).

Поле A в [0,1]. На каждом шаге:
  U = A * K        — свёртка с кольцевым ядром (FFT)
  A += dt * G(U)   — гауссова функция роста
G(u) = 2*exp(-((u-mu)/sigma)^2 / 2) - 1  — горб вокруг mu.

Классика: R=13, кольцо с пиком на 0.5R, mu=0.15, sigma=0.015.
Из случайного пятна радиусом ~R собирается «орб» — стабильный
глистящий организм, который ещё и ползёт.

Демо: 300 шагов, 4 кадра + кривая массы -> lenia.png.
Вердикт: масса стабильна и ненулевая к концу (не схлопнулась
и не заполнила поле).
"""

import numpy as np

N, R = 128, 13                  # поле и радиус ядра
MU, SIGMA, DT = 0.135, 0.03, 0.1
RING_MU, RING_SIG = 0.5, 0.15   # форма кольца (доли R)


def kernel():
    ax = np.arange(-R, R + 1)
    X, Y = np.meshgrid(ax, ax)
    D = np.sqrt(X ** 2 + Y ** 2) / R
    K = np.where(D <= 1, np.exp(-((D - RING_MU) / RING_SIG) ** 2 / 2), 0)
    return K / K.sum()


def grow(u):
    return 2 * np.exp(-((u - MU) / SIGMA) ** 2 / 2) - 1


def seed(rng):
    A = np.zeros((N, N))
    ax = np.arange(-R, R + 1)
    X, Y = np.meshgrid(ax, ax)
    blob = (X ** 2 + Y ** 2 <= R ** 2)
    # разреженная крапина ~30%: иначе свёртка >> mu и поле умирает
    c = N // 2
    A[c - R:c + R + 1, c - R:c + R + 1] = \
        (rng.uniform(0, 1, blob.shape) * blob) * \
        (rng.uniform(0, 1, blob.shape) < 0.3)
    return A


def run(A, steps):
    K = kernel()
    Kpad = np.zeros((N, N), dtype=complex)
    Kpad[:2 * R + 1, :2 * R + 1] = K
    Kpad = np.roll(Kpad, (-R, -R), (0, 1))     # центр ядра в (0,0)
    Fk = np.fft.fft2(Kpad)
    mass = [A.sum()]
    for _ in range(steps):
        U = np.fft.ifft2(np.fft.fft2(A) * Fk).real
        A = np.clip(A + DT * grow(U), 0, 1)
        mass.append(A.sum())
    return A, mass


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(7)
    A0 = seed(rng)
    snaps = [A0.copy()]
    A = A0.copy()
    masses = [A.sum()]
    K = kernel()
    Kpad = np.zeros((N, N), dtype=complex)
    Kpad[:2 * R + 1, :2 * R + 1] = K
    Kpad = np.roll(Kpad, (-R, -R), (0, 1))
    Fk = np.fft.fft2(Kpad)
    for i in range(800):
        U = np.fft.ifft2(np.fft.fft2(A) * Fk).real
        A = np.clip(A + DT * grow(U), 0, 1)
        masses.append(A.sum())
        if i in (49, 199, 799):
            snaps.append(A.copy())

    fig, axes = plt.subplots(1, 5, figsize=(15, 3.4))
    for ax, s, t in zip(axes[:4], snaps, (0, 50, 200, 800)):
        ax.imshow(s, cmap='magma', vmin=0, vmax=1)
        ax.set_title(f't={t}')
        ax.axis('off')
    axes[4].plot(masses)
    axes[4].set_title('масса')
    axes[4].set_xlabel('шаг')
    fig.tight_layout()
    fig.savefig('rd/lenia.png', dpi=140, bbox_inches='tight')

    m1 = masses[-1]
    stable = abs(m1 - np.mean(masses[-50:])) < 0.05 * m1
    structured = A.std() > 0.1     # поле не однородно — организмы
    print(f'масса: {masses[0]:.0f} -> {m1:.0f} '
          f'(хвост {np.mean(masses[-50:]):.0f}±{np.std(masses[-50:]):.0f}), '
          f'std поля {A.std():.2f}')
    ok = m1 > 100 and stable and structured
    print('VERDICT:', 'OK — колония кольцевых организмов' if ok
          else 'FAIL')
