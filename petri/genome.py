"""Genome layout for petri agents.

A genome is a flat float32 vector:
    [0 : S*O)  policy weights, reshaped to (S, O) — a linear "brain"
    [S*O : S*O + T)  heritable traits

Senses (S=7):  bias, food_here, food_grad_x, food_grad_y, crowd, energy, noise
Outputs (O=4): move_x, move_y, eat_logit, repro_logit
Traits (T=3):  speed, appetite, efficiency  (all squashed to (0, 1))
"""
import numpy as np

S = 7  # senses
O = 4  # outputs
T = 3  # traits
G = S * O + T  # genome length

W_SLICE = slice(0, S * O)
SPEED, APPETITE, EFFICIENCY = range(S * O, S * O + T)


def random_genomes(n, rng, s=S, o=O, t=T):
    g = rng.normal(0.0, 0.5, size=(n, s * o + t)).astype(np.float32)
    g[:, s * o:] = rng.uniform(-1.0, 1.0, (n, t))
    return g


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -8, 8)))


def traits(g, offset=S * O):
    """Heritable traits in (0,1); offset = n_senses * n_outputs."""
    return sigmoid(g[:, offset:])


def mutate(g, rate, rng):
    """Gaussian mutation; returns a new genome array."""
    noise = rng.normal(0.0, rate, size=g.shape).astype(np.float32)
    return g + noise


def crossover(g1, g2, rng):
    """Uniform per-gene crossover of two parent genomes -> child."""
    mask = rng.random(g1.shape) < 0.5
    return np.where(mask, g1, g2).astype(np.float32)
