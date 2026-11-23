"""Soft-body creature: genome -> morphology + muscle controller.

N point masses, complete graph of springs. A spring's stiffness gene
can decay to ~0, effectively removing the edge -> topology evolves too.
Muscles oscillate spring rest-length (amp, phase per edge; one global
frequency). Per-node friction gene = evolving 'feet'.
"""
import numpy as np

N = 6                       # point masses
E = N * (N - 1) // 2        # 15 springs
G = 2 * N + 3 * E + N + 1   # pos + stiff + amp + phase + friction + freq

EDGES = np.array([(i, j) for i in range(N) for j in range(i + 1, N)])
II, JJ = EDGES[:, 0], EDGES[:, 1]


def decode(g):
    g = np.asarray(g, np.float64)
    pos = g[:2 * N].reshape(N, 2) * 1.5
    k = np.clip(g[2 * N:2 * N + E], 0, 2.5) * 40.0  # cap: no railguns
    amp = np.clip(np.abs(g[2 * N + E:2 * N + 2 * E]) * 0.5, 0, 0.45)
    phase = g[2 * N + 2 * E:2 * N + 3 * E] * np.pi
    o = 2 * N + 3 * E
    mu = 1 / (1 + np.exp(-np.clip(g[o:o + N], -6, 6)))
    freq = 0.5 + 2.5 / (1 + np.exp(-np.clip(g[-1], -6, 6)))
    return dict(pos=pos, k=k, amp=amp, phase=phase, mu=mu, freq=freq)


def random_genome(rng):
    return rng.normal(0, 0.7, G)


def mutate(g, rate, rng):
    return g + rng.normal(0, rate, g.shape)


def crossover(g1, g2, rng):
    return np.where(rng.random(g1.shape) < 0.5, g1, g2)
