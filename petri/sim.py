"""Agent population + one tick of the petri world.

All state lives in flat numpy arrays so a tick is fully vectorized.
Nothing here tells agents WHAT to do — the genome's linear policy maps
senses to outputs, and selection does the rest.
"""
import numpy as np

from . import genome as gm
from .world import World

DEFAULTS = dict(
    size=128,
    start_pop=300,
    pop_cap=5000,
    food_max=10.0,
    regrowth=0.06,
    food_init=0.3,
    food_floor=1.0,      # uneatable reserve — resource can never hit zero
    reseed_below=20,     # panspermia: new founder genomes drift in
    reseed_prob=0.5,
    reseed_n=2,
    season_amp=0.0,
    season_period=4000,
    mutation=0.05,
    step_max=2.0,
    bite_max=2.0,
    food_energy=1.5,
    base_cost=0.4,
    speed_cost=0.8,
    move_cost=0.4,
    repro_urge=0.6,      # sigmoid threshold to want children
    repro_energy=80.0,   # energy needed to reproduce
    child_energy=30.0,
    birth_cost=5.0,
    mature_age=40,       # can't reproduce before this age
    repro_cooldown=40,   # ticks between births for one parent
    start_energy=20.0,
    energy_full=100.0,
    age_max=5000,
    crowd_norm=9.0,
    log_every=50,
)


class Sim:
    def __init__(self, cfg=None, seed=None):
        self.cfg = {**DEFAULTS, **(cfg or {})}
        c = self.cfg
        self.rng = np.random.default_rng(seed)
        self.world = World(c['size'], c['food_max'], c['regrowth'],
                           c['season_amp'], c['season_period'],
                           c['food_init'], self.rng)
        n = c['start_pop']
        self.pos = self.rng.uniform(0, c['size'], (n, 2)).astype(np.float32)
        self.energy = np.full(n, c['start_energy'], np.float32)
        self.age = np.zeros(n, np.int32)
        self.cooldown = np.zeros(n, np.int32)
        self.genomes = gm.random_genomes(n, self.rng)
        self.family = np.arange(n, dtype=np.int64)
        self.next_family = n
        self.log = []
        self.births = 0
        self.deaths = 0
        self.empty_ticks = 0

    @property
    def n(self):
        return len(self.energy)

    def step(self):
        c = self.cfg
        w = self.world
        w.grow()
        births_this = deaths_this = 0

        if self.n:
            ix = self.pos[:, 0].astype(np.int32) % w.size
            iy = self.pos[:, 1].astype(np.int32) % w.size

            dens = w.density(ix, iy)
            crowd = w.local_sum(dens)[iy, ix] / c['crowd_norm']
            fgx, fgy = w.grad(w.food)
            senses = np.stack([
                np.ones(self.n, np.float32),
                w.food[iy, ix] / c['food_max'],
                fgx[iy, ix] / c['food_max'],
                fgy[iy, ix] / c['food_max'],
                np.clip(crowd, 0, 2) / 2,
                np.clip(self.energy / c['energy_full'], 0, 1),
                self.rng.normal(0, 0.5, self.n).astype(np.float32),
            ], axis=1)

            W = self.genomes[:, :gm.S * gm.O].reshape(self.n, gm.S, gm.O)
            out = np.einsum('ns,nso->no', senses, W)
            move = np.tanh(out[:, :2])
            want_eat = gm.sigmoid(out[:, 2]) > 0.5
            repro = gm.sigmoid(out[:, 3])

            tr = gm.traits(self.genomes)
            speed, appetite, eff = tr[:, 0], tr[:, 1], tr[:, 2]

            disp = move * (speed * c['step_max'])[:, None]
            self.pos = (self.pos + disp) % w.size
            moved = np.hypot(disp[:, 0], disp[:, 1]) / c['step_max']

            cost = (c['base_cost'] + c['speed_cost'] * speed ** 2
                    + c['move_cost'] * moved) * (1.5 - eff)
            self.energy -= cost.astype(np.float32)

            # eating with per-cell competition (proportional share),
            # cells can't be stripped below food_floor
            flat = iy * w.size + ix
            want = np.where(want_eat, c['bite_max'] * appetite, 0).astype(np.float32)
            demand = np.bincount(flat, weights=want,
                                 minlength=w.size * w.size)
            available = np.maximum(0.0, w.food.ravel() - c['food_floor'])
            ratio = np.where(demand > 0,
                             np.minimum(1.0, available
                                        / np.maximum(demand, 1e-9)), 0)
            taken = want * ratio[flat]
            np.subtract.at(w.food.ravel(), flat, taken)
            self.energy += taken * c['food_energy']

            self.age += 1
            self.cooldown -= 1
            dead = (self.energy <= 0) | (self.age > c['age_max'])
            deaths_this = int(dead.sum())
            self.deaths += deaths_this
            keep = ~dead
            self.pos, self.energy, self.age = (self.pos[keep],
                                               self.energy[keep],
                                               self.age[keep])
            self.cooldown = self.cooldown[keep]
            self.genomes, self.family = self.genomes[keep], self.family[keep]
            repro, tr = repro[keep], tr[keep]

            fertile = ((repro > c['repro_urge'])
                       & (self.energy > c['repro_energy'])
                       & (self.age > c['mature_age'])
                       & (self.cooldown <= 0))
            room = max(0, c['pop_cap'] - self.n)
            idx = np.flatnonzero(fertile)
            if len(idx) > room:
                idx = self.rng.choice(idx, room, replace=False)
            if len(idx):
                children = gm.mutate(self.genomes[idx], c['mutation'], self.rng)
                off = self.rng.uniform(-1.5, 1.5, (len(idx), 2))
                self.pos = np.vstack([self.pos,
                                      (self.pos[idx] + off) % w.size])
                self.energy = np.concatenate([
                    self.energy,
                    np.full(len(idx), c['child_energy'], np.float32)])
                self.energy[idx] -= c['child_energy'] + c['birth_cost']
                self.age = np.concatenate([self.age,
                                           np.zeros(len(idx), np.int32)])
                self.cooldown = np.concatenate([
                    self.cooldown, np.zeros(len(idx), np.int32)])
                self.cooldown[idx] = c['repro_cooldown']
                self.genomes = np.vstack([self.genomes, children])
                self.family = np.concatenate([self.family, self.family[idx]])
                births_this = len(idx)
                self.births += births_this

        # panspermia — rare immigration of fresh genomes keeps life going
        if self.n < c['reseed_below'] and self.rng.random() < c['reseed_prob']:
            k = min(c['reseed_n'], c['pop_cap'] - self.n)
            if k > 0:
                self.pos = np.vstack([self.pos, self.rng.uniform(
                    0, c['size'], (k, 2)).astype(np.float32)])
                self.energy = np.concatenate([
                    self.energy, np.full(k, c['start_energy'], np.float32)])
                self.age = np.concatenate([self.age, np.zeros(k, np.int32)])
                self.cooldown = np.concatenate(
                    [self.cooldown, np.zeros(k, np.int32)])
                self.genomes = np.vstack(
                    [self.genomes, gm.random_genomes(k, self.rng)])
                self.family = np.concatenate([
                    self.family,
                    np.arange(self.next_family, self.next_family + k)])
                self.next_family += k

        self.empty_ticks = self.empty_ticks + 1 if self.n == 0 else 0
        if w.tick % c['log_every'] == 0:
            self.log.append(self.metrics(births_this, deaths_this))

    def metrics(self, births, deaths):
        c = self.cfg
        m = dict(tick=self.world.tick, pop=self.n,
                 births=births, deaths=deaths,
                 food=float(self.world.food.sum()))
        if self.n:
            tr = gm.traits(self.genomes)
            m.update(energy=float(self.energy.mean()),
                     speed=float(tr[:, 0].mean()),
                     appetite=float(tr[:, 1].mean()),
                     efficiency=float(tr[:, 2].mean()),
                     age=float(self.age.mean()),
                     families=int(len(np.unique(self.family))))
        else:
            m.update(energy=0, speed=0, appetite=0, efficiency=0,
                     age=0, families=0)
        return m

    def run(self, ticks, on_tick=None, max_empty=500):
        for _ in range(ticks):
            self.step()
            if on_tick:
                on_tick(self)
            if self.empty_ticks > max_empty:
                break
