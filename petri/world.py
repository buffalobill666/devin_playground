"""Grid world: logistic food regrowth, seasonality, optional geography.

An `island` landmask makes the world bounded (water = impassable);
`shelter` cells soften storm costs — refugia for the remnant."""
import numpy as np


def make_island(size, radius_frac=0.45, rough=0.15, rng=None):
    """Bumpy circular island: 1 = land, 0 = water."""
    rng = rng or np.random.default_rng()
    y, x = np.mgrid[:size, :size]
    c = (size - 1) / 2
    ang = np.arctan2(y - c, x - c)
    dist = np.hypot(y - c, x - c)
    edge = radius_frac * size * (
        1 + rough * np.sin(3 * ang + rng.random() * 6.28)
        + rough * np.sin(7 * ang + rng.random() * 6.28))
    return (dist < edge).astype(np.float32)


def make_shelters(size, n, radius, rng=None):
    """n gaussian refuge pockets; returns 0..1 shelter strength grid."""
    rng = rng or np.random.default_rng()
    s = np.zeros((size, size), np.float32)
    y, x = np.mgrid[:size, :size]
    for _ in range(n):
        cy, cx = rng.uniform(0, size, 2)
        s = np.maximum(s, np.exp(-((y - cy) ** 2 + (x - cx) ** 2)
                                 / (2 * radius ** 2)))
    return np.clip(s, 0, 1)


class World:
    def __init__(self, size=128, food_max=10.0, regrowth=0.02,
                 season_amp=0.0, season_period=4000, food_init=0.3,
                 rng=None, landmask=None, shelter=None):
        self.size = size
        self.food_max = food_max
        self.regrowth = regrowth
        self.season_amp = season_amp
        self.season_period = season_period
        self.rng = rng or np.random.default_rng()
        self.food = self.rng.uniform(
            0, food_max * food_init, (size, size)).astype(np.float32)
        self.land = landmask  # None = open torus
        self.shelter = (shelter if shelter is not None
                        else np.zeros((size, size), np.float32))
        if landmask is not None:
            self.food *= landmask
        self.call = np.zeros((size, size), np.float32)
        self.callx = np.zeros((size, size), np.float32)
        self.cally = np.zeros((size, size), np.float32)
        self.tick = 0

    def grow(self, rate_mult=1.0):
        f = self.food
        season = 1.0 + self.season_amp * np.sin(2 * np.pi * self.tick / self.season_period)
        f += self.regrowth * season * rate_mult * f * (1.0 - f / self.food_max)
        np.clip(f, 0.0, self.food_max, out=f)
        if self.land is not None:
            f *= self.land
        self.tick += 1

    def density(self, ix, iy):
        """Agent count per cell on the torus."""
        d = np.zeros((self.size, self.size), np.float32)
        np.add.at(d, (iy, ix), 1.0)
        return d

    def local_sum(self, arr):
        """3x3 toroidal neighbourhood sum of a grid."""
        s = arr.copy()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    s += np.roll(arr, (dy, dx), (0, 1))
        return s

    def grad(self, arr):
        gx = np.roll(arr, -1, 1) - np.roll(arr, 1, 1)
        gy = np.roll(arr, -1, 0) - np.roll(arr, 1, 0)
        return gx, gy
