"""Two-trophic ecosystem: evolving prey (grazers) + evolving predators,
sexual reproduction with local mate search. "Mini Isle Royale".

Sensing is vectorized via 'scent fields': each species smells the
(blurred) density gradient of the other — predators run uphill toward
prey, prey downhill away from predators.

Prey genome  (S=11, O=4, T=5): bias, food, fgx, fgy, crowd, energy,
    noise, pred_gx, pred_gy, own_gx, own_gy -> move, eat, repro |
    speed, appetite, efficiency, vigilance, resist
Pred genome  (S=7, O=4, T=4): bias, prey_dens, prey_gx, prey_gy, crowd,
    energy, noise -> move, hunt, repro | speed, ferocity, efficiency, sense

Disease: a third actor living inside prey. Each carrier holds a
`vir`ulence float (the pathogen's 'genome') — transmitted to neighbours
with mutation, vertically to offspring; hosts evolve `resist`.
"""
import numpy as np

from . import genome as gm
from .world import World

PREY_S, PRED_S, O, PREY_T, PRED_T = 16, 11, 5, 5, 4
PREY_G = PREY_S * O + PREY_T
PRED_G = PRED_S * O + PRED_T

DEFAULTS = dict(
    size=128,
    food_max=10.0,
    regrowth=0.06,
    food_init=0.3,
    food_floor=1.0,
    season_amp=0.0,
    season_period=4000,
    mutation=0.05,
    step_max=2.0,
    bite_max=2.0,
    food_energy=1.5,
    log_every=50,
    crowd_norm=9.0,

    prey_start=400,
    prey_start_cluster=0,   # >0: founders released as one herd (radius)
    prey_cap=3500,
    prey_start_energy=30.0,
    prey_energy_full=100.0,
    prey_base_cost=0.4,
    prey_speed_cost=0.8,
    prey_move_cost=0.4,
    prey_repro_urge=0.6,
    prey_repro_energy=90.0,
    prey_child_energy=20.0,
    prey_birth_cost=5.0,
    prey_mature_age=40,
    prey_cooldown=40,
    prey_age_max=5000,
    prey_mate_block=2,      # mates must share a 2x2 block
    prey_reseed_below=20,

    pred_start=50,
    pred_start_cluster=0,
    pred_cap=800,
    pred_start_energy=60.0,
    pred_energy_full=150.0,
    pred_base_cost=0.6,     # bigger body, higher basal (Kleiber-ish)
    pred_speed_cost=1.0,
    pred_move_cost=0.5,
    pred_hunt_cost=0.8,
    pred_repro_urge=0.6,
    pred_repro_energy=100.0,
    pred_child_energy=40.0,
    pred_birth_cost=10.0,
    pred_mature_age=60,
    pred_cooldown=80,
    pred_age_max=8000,
    pred_mate_block=8,
    pred_reseed_below=15,

    catch_base=0.15,        # p = base + k*(ferocity - prey vigilance)
    catch_scale=0.5,
    meat_base=15.0,         # energy per kill = base + frac*prey energy
    meat_frac=0.3,
    reseed_prob=0.5,
    reseed_n=3,

    # stochastic severe winters (0 = disabled)
    storm_period=0,         # mean ticks between storms
    storm_len=300,          # storm duration in ticks
    storm_regrowth=0.1,     # food regrowth multiplier during storm
    storm_cost=3.0,         # base-cost multiplier during storm

    # second forage layer — "grass/sedges": fast, lean fallback food.
    # 0 regrowth = layer absent (default worlds unchanged).
    grass_max=4.0,
    grass_regrowth=0.0,
    grass_init=0.5,
    grass_floor=0.2,
    grass_energy=0.8,

    # geography: 0 = open torus; island + refugia for real-island cases
    island_radius=0.0,      # fraction of size; >0 = bounded island
    island_rough=0.15,
    shelter_n=0,            # refuge pockets (soften storm costs)
    shelter_radius=8.0,

    # founder animals arrive with working brains (like real released
    # wildlife), not random genomes: blend a plausible policy template
    prey_founder_bias=0.0,  # 0 = random founders (evolution from scratch)
    pred_founder_bias=0.0,

    # disease — the third actor (0 = disabled). SIR-flavoured:
    # density-dependent transmission inside prey, virulence mutates on
    # transmission, hosts can recover and evolve 'resist' (trait #5).
    disease=0.0,            # transmission scale (beta)
    disease_start=0.0,      # fraction of founders infected at t0
    disease_intro=0.0,      # per-tick prob of spontaneous new case
    disease_cost=0.6,       # extra energy drain, x virulence
    disease_mort=0.02,      # per-tick death prob at virulence=1
    disease_mort_exp=1.0,   # lethality ~ vir**exp; >1 makes hot
                            # strains pay disproportionately (the
                            # classic transmission-virulence tradeoff)
    disease_recover=0.03,   # base per-tick recovery prob
    disease_mut=0.08,       # virulence mutation sd on transmission
    disease_vert=0.4,       # vertical transmission prob to kids

    # alarm calls — communication as costly signal (0 = disabled).
    # prey get a 5th output 'call' and 2 senses for the call-field
    # gradient; predators hear calls too (they betray the caller).
    call_rate=0.0,          # max emission strength
    call_decay=0.90,        # field decay per tick
    call_cost=0.3,          # energy cost per tick while calling
    prey_disperse=0,        # 1: kids spawn at random cells
                            # (breaks family clustering -> kin control)
    pred_deaf=0,            # 1: blind predators to the prey-density
                            # field — calls become their only prey cue
    call_flee=False,        # calls carry the caller's flee vector:
                            # scream points where prey is HEADING
    herd_dilution=0.0,      # selfish herd: catch chance divided by
                            # (1 + k * prey-neighbors of the target)
    scent_marks=0,          # fear-musk: prey reflexively deposit a
                            # persistent danger-mark scaled by the
                            # pred-gradient they smell. Unlike calls:
                            # zero cost, long-lived, unhearable by
                            # predators — territory memory, not alarm
    mark_decay=0.98,        # ~35-tick half-life (calls die in ~7)
    mark_rate=1.0,          # deposit strength
    mark_deaf=0,            # ablation: prey can't smell marks
)


def _prey_template(n, rng):
    """A plausible grazer policy: seek food, graze, breed, flee preds."""
    w = np.zeros((PREY_S, O), np.float32)
    w[0, 2] = 0.8                    # bias -> graze
    w[1, 2] = 1.0                    # food here -> eat
    w[2, 0] = 1.2                    # food grad x -> move x
    w[3, 1] = 1.2                    # food grad y -> move y
    w[4, 0] = w[4, 1] = -0.4         # crowded -> spread
    w[5, 3] = 1.5                    # energy -> want kids
    w[6, 0] = w[6, 1] = 0.3          # jitter
    w[7, 0] = -1.0                   # flee predator gradient
    w[8, 1] = -1.0
    return np.repeat(w[None], n, 0) + rng.normal(0, .3, (n, PREY_S, O))


class Pop:
    """Flat-array state of one species."""
    def __init__(self, n, size, g_len, start_energy, rng):
        self.pos = rng.uniform(0, size, (n, 2)).astype(np.float32)
        self.energy = np.full(n, start_energy, np.float32)
        self.age = np.zeros(n, np.int32)
        self.cooldown = np.zeros(n, np.int32)
        self.genomes = np.zeros((n, g_len), np.float32)
        self.family = np.arange(n, dtype=np.int64)

    def __len__(self):
        return len(self.energy)

    def cells(self, size):
        ix = self.pos[:, 0].astype(np.int32) % size
        iy = self.pos[:, 1].astype(np.int32) % size
        return ix, iy

    def keep(self, mask):
        for a in ('pos', 'energy', 'age', 'cooldown', 'genomes',
                  'family', 'infected', 'vir'):
            v = getattr(self, a, None)
            if v is not None:
                setattr(self, a, v[mask])


def _density_grid(size, flat):
    return np.bincount(flat, minlength=size * size).reshape(size, size)


def _mate_pairs(pop, fertile_idx, block, size, rng):
    """Pair fertile individuals sharing a `block`x`block` coarse cell.
    Returns (parent1_idx, parent2_idx) arrays."""
    if len(fertile_idx) < 2:
        return None, None
    bx = (pop.pos[fertile_idx, 0].astype(np.int32) // block) % (size // block)
    by = (pop.pos[fertile_idx, 1].astype(np.int32) // block) % (size // block)
    bid = by * (size // block) + bx
    order = np.argsort(bid, kind='stable')
    fertile_sorted, bid_sorted = fertile_idx[order], bid[order]
    uniq = np.unique(bid_sorted)
    starts = np.searchsorted(bid_sorted, uniq)
    p1, p2 = [], []
    for i, b in enumerate(uniq):
        lo = starts[i]
        hi = np.searchsorted(bid_sorted, b, side='right')
        grp = fertile_sorted[lo:hi].copy()
        rng.shuffle(grp)
        for i in range(0, len(grp) - 1, 2):
            p1.append(grp[i])
            p2.append(grp[i + 1])
    return np.array(p1), np.array(p2)


def _move(pos, disp, w):
    """Move on torus, or on a bounded island where water is a wall."""
    new = pos + disp
    if w.land is None:
        return new % w.size
    new = np.clip(new, 0, w.size - 1e-4)
    ix = new[:, 0].astype(np.int32)
    iy = new[:, 1].astype(np.int32)
    ok = w.land[iy, ix] > 0
    return np.where(ok[:, None], new, pos)


def _reproduce(pop, p1, p2, c, rng, mutation, land=None):
    n = len(p1)
    kids = gm.crossover(pop.genomes[p1], pop.genomes[p2], rng)
    kids = gm.mutate(kids, mutation, rng)
    child_e = c['child_energy']
    if c.get('prey_disperse'):
        cpos = rng.uniform(0, c['size'], (n, 2))
    else:
        cpos = (pop.pos[p1] + pop.pos[p2]) / 2 \
            + rng.uniform(-1.5, 1.5, (n, 2))
    if land is None:
        cpos %= c['size']
    else:
        cpos = np.clip(cpos, 0, c['size'] - 1e-4)
        ix = cpos[:, 0].astype(np.int32)
        iy = cpos[:, 1].astype(np.int32)
        cpos = np.where((land[iy, ix] > 0)[:, None], cpos, pop.pos[p1])
    pop.pos = np.vstack([pop.pos, cpos])
    pop.energy = np.concatenate(
        [pop.energy, np.full(n, child_e, np.float32)])
    pop.energy[p1] -= child_e / 2 + c['birth_cost']
    pop.energy[p2] -= child_e / 2 + c['birth_cost']
    pop.age = np.concatenate([pop.age, np.zeros(n, np.int32)])
    pop.cooldown = np.concatenate(
        [pop.cooldown, np.zeros(n, np.int32)])
    pop.cooldown[p1] = pop.cooldown[p2] = c['cooldown']
    pop.genomes = np.vstack([pop.genomes, kids])
    pop.family = np.concatenate([pop.family, pop.family[p1]])
    if hasattr(pop, 'infected'):
        pop.infected = np.concatenate(
            [pop.infected, np.zeros(n, np.int8)])
        pop.vir = np.concatenate(
            [pop.vir, np.zeros(n, np.float32)])
    return n


class EcoSim:
    def __init__(self, cfg=None, seed=None):
        self.cfg = {**DEFAULTS, **(cfg or {})}
        c = self.cfg
        self.rng = np.random.default_rng(seed)
        land = shelter = None
        if c['island_radius'] > 0:
            from .world import make_island, make_shelters
            land = make_island(c['size'], c['island_radius'],
                               c['island_rough'], self.rng)
            if c['shelter_n']:
                shelter = make_shelters(c['size'], c['shelter_n'],
                                        c['shelter_radius'], self.rng)
                shelter *= land  # refuges only on land
        self.world = World(c['size'], c['food_max'], c['regrowth'],
                           c['season_amp'], c['season_period'],
                           c['food_init'], self.rng, land, shelter)
        self.prey = Pop(c['prey_start'], c['size'], PREY_G,
                        c['prey_start_energy'], self.rng)
        self.prey.genomes = gm.random_genomes(len(self.prey), self.rng,
                                              PREY_S, O, PREY_T)
        if c['prey_founder_bias'] > 0 and len(self.prey):
            n = len(self.prey)
            self.prey.genomes[:, :PREY_S * O] = (
                _prey_template(n, self.rng)
                * c['prey_founder_bias']).reshape(n, -1)
        self.prey.infected = np.zeros(len(self.prey), np.int8)
        self.prey.vir = np.zeros(len(self.prey), np.float32)
        if c['disease'] > 0 and c['disease_start'] > 0 and len(self.prey):
            m = self.rng.random(len(self.prey)) < c['disease_start']
            self.prey.infected[m] = 1
            self.prey.vir[m] = self.rng.uniform(0.2, 0.6, int(m.sum()))
        self.pred = Pop(c['pred_start'], c['size'], PRED_G,
                        c['pred_start_energy'], self.rng)
        self.pred.genomes = gm.random_genomes(len(self.pred), self.rng,
                                              PRED_S, O, PRED_T)
        for pop, key in ((self.prey, 'prey'), (self.pred, 'pred')):
            r = c[f'{key}_start_cluster']
            if r > 0 and len(pop):
                if land is not None:
                    lcells = np.argwhere(land > 0)
                    cy, cx = lcells[self.rng.integers(len(lcells))]
                    ctr = np.array([cx, cy], float)
                    pop.pos = ctr + self.rng.uniform(
                        -r, r, (len(pop), 2))
                    ix = np.clip(pop.pos[:, 0].astype(np.int32),
                                 0, c['size'] - 1)
                    iy = np.clip(pop.pos[:, 1].astype(np.int32),
                                 0, c['size'] - 1)
                    wet = land[iy, ix] == 0
                    pop.pos[wet] = ctr
                else:
                    ctr = self.rng.uniform(r, c['size'] - r, 2)
                    pop.pos = (ctr + self.rng.uniform(
                        -r, r, (len(pop), 2))) % c['size']
        self.grass = (self.rng.uniform(
            0, c['grass_max'] * c['grass_init'],
            (c['size'], c['size'])).astype(np.float32)
            if c['grass_regrowth'] > 0 else np.zeros(
                (c['size'], c['size']), np.float32))
        self.log = []
        self.b_prey = self.d_prey = self.b_pred = self.d_pred = 0
        self.empty_ticks = 0
        self.storm_left = 0

    # -- scent fields -------------------------------------------------
    def _fields(self):
        w = self.world
        prey_flat = self.prey.cells(w.size)[1] * w.size \
            + self.prey.cells(w.size)[0] if len(self.prey) else None
        pred_flat = self.pred.cells(w.size)[1] * w.size \
            + self.pred.cells(w.size)[0] if len(self.pred) else None
        prey_field = np.zeros((w.size, w.size), np.float32)
        pred_field = np.zeros((w.size, w.size), np.float32)
        if prey_flat is not None:
            d = _density_grid(w.size, prey_flat)
            prey_field = w.local_sum(w.local_sum(d))  # ~5x5 blur
        if pred_flat is not None:
            d = _density_grid(w.size, pred_flat)
            pred_field = w.local_sum(d)  # ~3x3 blur
        return prey_field, pred_field

    # -- one tick -----------------------------------------------------
    def step(self):
        c, w, rng = self.cfg, self.world, self.rng
        # severe-winter events: rare, sudden, suppress regrowth, raise costs
        if c['storm_period'] > 0:
            if self.storm_left > 0:
                self.storm_left -= 1
            elif rng.random() < 1.0 / c['storm_period']:
                self.storm_left = c['storm_len']
        w.grow(c['storm_regrowth'] if self.storm_left else 1.0)
        if c['grass_regrowth'] > 0:
            g = self.grass
            rm = c['storm_regrowth'] if self.storm_left else 1.0
            g += c['grass_regrowth'] * rm * g * (1 - g / c['grass_max'])
            np.clip(g, 0, c['grass_max'], out=g)
        storm_cost = c['storm_cost'] if self.storm_left else 1.0
        prey_field, pred_field = self._fields()
        pgx, pgy = w.grad(pred_field)      # prey smells danger
        qgx, qgy = w.grad(prey_field)      # predator smells food
        cgx, cgy = w.grad(w.call)          # everyone hears the calls
        mgx, mgy = w.grad(w.mark)          # scent-mark trails
        bp = dp = bc = dc = dd = 0
        repro_prey = np.zeros(0)
        repro_pred = np.zeros(0)
        ddead = np.zeros(len(self.prey), bool)

        # --- prey ---------------------------------------------------
        if len(self.prey):
            p = self.prey
            ix, iy = p.cells(w.size)
            dens = w.density(ix, iy)
            crowd = w.local_sum(dens)[iy, iy] / c['crowd_norm']
            fgx, fgy = w.grad(w.food)
            senses = np.stack([
                np.ones(len(p), np.float32),
                w.food[iy, ix] / c['food_max'],
                fgx[iy, ix] / c['food_max'],
                fgy[iy, ix] / c['food_max'],
                np.clip(crowd, 0, 2) / 2,
                np.clip(p.energy / c['prey_energy_full'], 0, 1),
                rng.normal(0, .5, len(p)).astype(np.float32),
                pgx[iy, ix] / 4,
                pgy[iy, ix] / 4,
                qgx[iy, ix] / 9,      # conspecific gradient — can
                qgy[iy, ix] / 9,      # herding evolve at all?
                cgx[iy, ix],
                cgy[iy, ix],
                w.mark[iy, ix],       # mark level underfoot
                mgx[iy, ix],          # mark gradient: toward the
                mgy[iy, ix],          # remembered danger spot
            ], axis=1)
            if c['mark_deaf']:
                senses[:, 13:16] = 0.0
            out = np.einsum('ns,nso->no', senses,
                            p.genomes[:, :PREY_S * O].reshape(-1, PREY_S, O))
            move = np.tanh(out[:, :2])
            want_eat = gm.sigmoid(out[:, 2]) > 0.5
            repro = gm.sigmoid(out[:, 3])
            tr = gm.traits(p.genomes, PREY_S * O)
            speed, appetite, eff = tr[:, 0], tr[:, 1], tr[:, 2]

            disp = move * (speed * c['step_max'])[:, None]
            p.pos = _move(p.pos, disp, w)
            moved = np.hypot(disp[:, 0], disp[:, 1]) / c['step_max']
            smult = 1 + (storm_cost - 1) * (1 - w.shelter[iy, ix])
            p.energy -= ((c['prey_base_cost'] * smult
                          + c['prey_speed_cost'] * speed ** 2
                          + c['prey_move_cost'] * moved)
                         * (1.5 - eff)).astype(np.float32)

            flat = iy * w.size + ix
            want = np.where(want_eat, c['bite_max'] * appetite, 0) \
                .astype(np.float32)
            demand = np.bincount(flat, weights=want,
                                 minlength=w.size * w.size)
            avail = np.maximum(0.0, w.food.ravel() - c['food_floor'])
            ratio = np.where(demand > 0, np.minimum(
                1.0, avail / np.maximum(demand, 1e-9)), 0)
            taken = want * ratio[flat]
            np.subtract.at(w.food.ravel(), flat, taken)
            p.energy += taken * c['food_energy']
            # unspent bite goes to the lean fallback layer (grass)
            if c['grass_regrowth'] > 0:
                rest = want - taken
                if rest.any():
                    d2 = np.bincount(flat, weights=rest,
                                     minlength=w.size * w.size)
                    av2 = np.maximum(0.0, self.grass.ravel()
                                     - c['grass_floor'])
                    t2 = rest * np.where(d2 > 0, np.minimum(
                        1.0, av2 / np.maximum(d2, 1e-9)), 0)[flat]
                    np.subtract.at(self.grass.ravel(), flat, t2)
                    p.energy += t2 * c['grass_energy']
            np.clip(p.energy, 0, 2 * c['prey_energy_full'], out=p.energy)
            p.age += 1
            p.cooldown -= 1
            repro_prey = repro
            # alarm calls: emit into w.call, pay the cost - the
            # caller betrays itself to any predator that listens
            if c['call_rate'] > 0:
                call_sig = gm.sigmoid(out[:, 4]) * c['call_rate']
                np.add.at(w.call.ravel(), flat, call_sig)
                if c['call_flee']:
                    np.add.at(w.callx.ravel(), flat,
                              call_sig * disp[:, 0])
                    np.add.at(w.cally.ravel(), flat,
                              call_sig * disp[:, 1])
                p.energy -= call_sig * c['call_cost']

            # fear-musk: reflexive deposit proportional to how much
            # danger this prey smells right now — no output channel,
            # no cost; the environment remembers where fear happened
            if c['scent_marks']:
                fear = np.clip(np.hypot(pgx[iy, ix],
                                        pgy[iy, ix]) / 4, 0, 1)
                np.add.at(w.mark.ravel(), flat,
                          fear * c['mark_rate'])

            # --- disease: density-dependent transmission ------------
            if c['disease'] > 0:
                inf = p.infected.astype(bool)
                if inf.any():
                    cnt = np.bincount(flat[inf],
                                      minlength=w.size * w.size) \
                        .reshape(w.size, w.size)
                    vs = np.bincount(flat[inf], weights=p.vir[inf],
                                     minlength=w.size * w.size) \
                        .reshape(w.size, w.size)
                    lcnt = w.local_sum(cnt)
                    lvir = w.local_sum(vs) / np.maximum(lcnt, 1e-9)
                    resist = tr[:, 4]
                    pinf = 1.0 - np.exp(
                        -c['disease'] * lcnt[iy, ix]
                        * np.clip(lvir[iy, ix], 0.05, None)
                        * (1.0 - resist))
                    new = (~inf) & (rng.random(len(p)) < pinf)
                    if new.any():
                        p.infected[new] = 1
                        p.vir[new] = np.clip(
                            lvir[iy[new], ix[new]]
                            + rng.normal(0, c['disease_mut'],
                                         int(new.sum())),
                            0.05, 1.0).astype(np.float32)
                    p.energy -= inf * p.vir * c['disease_cost']
                    ddead = inf & (
                        rng.random(len(p))
                        < c['disease_mort']
                        * p.vir ** c['disease_mort_exp'])
                    rec = inf & (rng.random(len(p))
                                 < c['disease_recover']
                                 * (0.3 + 0.7 * resist))
                    p.infected[rec] = 0
                    p.vir[rec] = 0
                elif c['disease_intro'] > 0 \
                        and rng.random() < c['disease_intro']:
                    j = int(rng.integers(len(p)))
                    p.infected[j] = 1
                    p.vir[j] = self.rng.uniform(0.2, 0.6)

        # --- predators ----------------------------------------------
        eaten = np.zeros(len(self.prey), bool)
        if len(self.pred):
            h = self.pred
            ix, iy = h.cells(w.size)
            dens = w.density(ix, iy)
            crowd = w.local_sum(dens)[iy, iy] / c['crowd_norm']
            senses = np.stack([
                np.ones(len(h), np.float32),
                np.clip(prey_field[iy, ix] / 9, 0, 1),
                qgx[iy, ix] / 9,
                qgy[iy, ix] / 9,
                np.clip(crowd, 0, 2) / 2,
                np.clip(h.energy / c['pred_energy_full'], 0, 1),
                rng.normal(0, .5, len(h)).astype(np.float32),
                cgx[iy, ix],          # predators hear the alarms
                cgy[iy, ix],          # too - calls betray the caller
                w.callx[iy, ix],      # flee-vector: where prey heads
                w.cally[iy, ix],
            ], axis=1)
            if c['pred_deaf']:
                senses[:, 1:4] = 0.0  # ablation: no prey-density field
            out = np.einsum('ns,nso->no', senses,
                            h.genomes[:, :PRED_S * O].reshape(-1, PRED_S, O))
            move = np.tanh(out[:, :2])
            want_hunt = gm.sigmoid(out[:, 2]) > 0.5
            repro = gm.sigmoid(out[:, 3])
            tr = gm.traits(h.genomes, PRED_S * O)
            speed, ferocity, eff, sense = tr[:, 0], tr[:, 1], tr[:, 2], tr[:, 3]

            disp = move * (speed * c['step_max'])[:, None]
            h.pos = _move(h.pos, disp, w)
            moved = np.hypot(disp[:, 0], disp[:, 1]) / c['step_max']
            smult = 1 + (storm_cost - 1) * (1 - w.shelter[iy, ix])
            h.energy -= ((c['pred_base_cost'] * smult
                          + c['pred_speed_cost'] * speed ** 2
                          + c['pred_move_cost'] * moved)
                         * (1.5 - eff)).astype(np.float32)
            h.age += 1
            h.cooldown -= 1

            # hunt: each hunter picks a random prey within its 3x3
            if len(self.prey) and want_hunt.any():
                ix, iy = h.cells(w.size)
                pflat = (self.prey.pos[:, 1].astype(np.int32) % w.size) \
                    * w.size + (self.prey.pos[:, 0].astype(np.int32) % w.size)
                order = np.argsort(pflat, kind='stable')
                qflat_sorted = pflat[order]
                cells = np.flatnonzero(want_hunt)
                hy, hx = iy[cells], ix[cells]
                S = w.size
                nbr = np.stack([
                    ((hy + dy) % S) * S + (hx + dx) % S
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)], 1)
                starts = np.searchsorted(
                    qflat_sorted, nbr.ravel()).reshape(-1, 9)
                ends = np.searchsorted(
                    qflat_sorted, nbr.ravel(), side='right').reshape(-1, 9)
                cnts = ends - starts
                total = cnts.sum(1)
                ok = total > 0
                cells, starts, cnts, total = (cells[ok], starts[ok],
                                              cnts[ok], total[ok])
                if len(cells):
                    r = rng.integers(0, total)
                    cum = np.cumsum(cnts, 1) - cnts
                    kk = np.clip((cum <= r[:, None]).sum(1) - 1, 0, 8)
                    row = np.arange(len(r))
                    pick = starts[row, kk] + r - cum[row, kk]
                    target = order[pick]
                    vigil = gm.traits(self.prey.genomes, PREY_S * O)[:, 3]
                    p_catch = np.clip(
                        c['catch_base'] + c['catch_scale']
                        * (ferocity[cells] - vigil[target]), 0.02, 0.95)
                    if c['herd_dilution'] > 0:
                        # selfish herd: prey count in target's 3x3
                        pcnt = np.bincount(
                            pflat, minlength=w.size * w.size
                            ).reshape(w.size, w.size)
                        lprey = w.local_sum(pcnt)
                        n_t = np.clip(
                            lprey.ravel()[pflat[target]] - 1, 0, None)
                        p_catch = np.clip(
                            p_catch / (1 + c['herd_dilution'] * n_t),
                            0.02, 0.95)
                    h.energy[cells] -= c['pred_hunt_cost']
                    success = rng.random(len(cells)) < p_catch
                    ok_cells, ok_target = cells[success], target[success]
                    # dedupe: one prey feeds only its first killer
                    _, first = np.unique(ok_target, return_index=True)
                    ok_cells, ok_target = ok_cells[first], ok_target[first]
                    eaten[ok_target] = True
                    h.energy[ok_cells] += (c['meat_base'] + c['meat_frac']
                                           * self.prey.energy[ok_target])
            np.clip(h.energy, 0, 2 * c['pred_energy_full'], out=h.energy)
            repro_pred = repro

        # --- deaths ---------------------------------------------------
        if len(self.prey):
            dd = int(ddead.sum())
            dead = (self.prey.energy <= 0) | eaten | ddead \
                | (self.prey.age > c['prey_age_max'])
            dp = int(dead.sum())
            self.d_prey += dp
            keep = ~dead
            self.prey.keep(keep)
            repro_prey = repro_prey[keep]
        if len(self.pred):
            dead = (self.pred.energy <= 0) \
                | (self.pred.age > c['pred_age_max'])
            dc = int(dead.sum())
            self.d_pred += dc
            keep = ~dead
            self.pred.keep(keep)
            repro_pred = repro_pred[keep]

        # --- sexual reproduction --------------------------------------
        for pop, s, urges in ((self.prey, 'prey', repro_prey),
                              (self.pred, 'pred', repro_pred)):
            if len(pop) < 2 or not len(urges):
                continue
            fertile = ((urges > c[f'{s}_repro_urge'])
                       & (pop.energy > c[f'{s}_repro_energy'])
                       & (pop.age > c[f'{s}_mature_age'])
                       & (pop.cooldown <= 0))
            idx = np.flatnonzero(fertile)
            room = c[f'{s}_cap'] - len(pop)
            if len(idx) > room:
                idx = rng.choice(idx, room, replace=False)
            p1, p2 = _mate_pairs(pop, idx, c[f'{s}_mate_block'],
                                 w.size, rng)
            if p1 is not None and len(p1):
                sub = {k: c[f'{s}_{k}'] for k in
                       ('child_energy', 'birth_cost', 'cooldown')}
                sub['size'] = c['size']
                sub['prey_disperse'] = c['prey_disperse'] \
                    if s == 'prey' else 0
                nb = _reproduce(pop, p1, p2, sub, rng, c['mutation'],
                                w.land)
                if s == 'prey':
                    if c['disease'] > 0 and nb:
                        pinf = pop.infected[p1] | pop.infected[p2]
                        kinf = pinf.astype(bool) & (
                            rng.random(nb) < c['disease_vert'])
                        tail = np.arange(len(pop) - nb, len(pop))
                        pop.infected[tail[kinf]] = 1
                        pop.vir[tail[kinf]] = pop.vir[p1[kinf]]
                    self.b_prey += nb
                    bp = nb
                else:
                    self.b_pred += nb
                    bc = nb

        # call field decays every tick (acoustic signal is short-lived)
        w.call *= c['call_decay']
        w.mark *= c['mark_decay']
        w.callx *= c['call_decay']
        w.cally *= c['call_decay']

        # --- panspermia ------------------------------------------------
        for pop, s, g_len in ((self.prey, 'prey', PREY_G),
                              (self.pred, 'pred', PRED_G)):
            if len(pop) < c[f'{s}_reseed_below'] \
                    and rng.random() < c['reseed_prob']:
                k = min(c['reseed_n'], c[f'{s}_cap'] - len(pop))
                if k > 0:
                    fresh = gm.random_genomes(
                        k, rng, PREY_S if s == 'prey' else PRED_S, O,
                        PREY_T if s == 'prey' else PRED_T)
                    if w.land is not None:
                        lidx = np.flatnonzero(w.land.ravel())
                        pk = lidx[rng.integers(0, len(lidx), k)]
                        newpos = np.stack([pk % w.size, pk // w.size],
                                          1).astype(np.float32) + .5
                    else:
                        newpos = rng.uniform(
                            0, c['size'], (k, 2)).astype(np.float32)
                    pop.pos = np.vstack([pop.pos, newpos])
                    pop.energy = np.concatenate([pop.energy, np.full(
                        k, c[f'{s}_start_energy'], np.float32)])
                    pop.age = np.concatenate(
                        [pop.age, np.zeros(k, np.int32)])
                    pop.cooldown = np.concatenate(
                        [pop.cooldown, np.zeros(k, np.int32)])
                    pop.genomes = np.vstack([pop.genomes, fresh])
                    if hasattr(pop, 'infected'):
                        pop.infected = np.concatenate(
                            [pop.infected, np.zeros(k, np.int8)])
                        pop.vir = np.concatenate(
                            [pop.vir, np.zeros(k, np.float32)])
                    fam = pop.family
                    pop.family = np.concatenate([
                        fam, np.arange(fam.max() + 1 if len(fam) else 0,
                                       (fam.max() + 1 if len(fam) else 0) + k)])

        self.empty_ticks = self.empty_ticks + 1 \
            if len(self.prey) == 0 and len(self.pred) == 0 else 0
        if w.tick % c['log_every'] == 0:
            self.log.append(self.metrics(bp, dp, bc, dc, dd))

    def metrics(self, bp, dp, bc, dc, dd=0):
        c = self.cfg
        m = dict(tick=self.world.tick, pop_prey=len(self.prey),
                 pop_pred=len(self.pred), b_prey=bp, d_prey=dp,
                 b_pred=bc, d_pred=dc, food=float(self.world.food.sum()),
                 grass=float(self.grass.sum()),
                 storm=1 if self.storm_left else 0, d_disease=dd)
        for pop, s in ((self.prey, 'prey'), (self.pred, 'pred')):
            n = len(pop)
            if n:
                tr = gm.traits(pop.genomes,
                               PREY_S * O if s == 'prey' else PRED_S * O)
                if s == 'prey':
                    keys = ('speed', 'appetite', 'efficiency',
                            'vigilance', 'resist')
                else:
                    keys = ('speed', 'ferocity', 'efficiency', 'sense')
                for i, k in enumerate(keys):
                    m[f'{s}_{k}'] = float(tr[:, i].mean())
                if s == 'prey':
                    ib = pop.infected.astype(bool)
                    m['infected'] = int(ib.sum())
                    m['virulence'] = float(pop.vir[ib].mean()) \
                        if ib.any() else 0.0
                    W = pop.genomes[:, :PREY_S * O] \
                        .reshape(-1, PREY_S, O)
                    # alarm wiring: pred-grad senses -> call output
                    m['prey_call'] = float(
                        (W[:, 7:9, 4]).mean())
                    m['prey_hear'] = float(
                        np.abs(W[:, 11:13, :2]).mean())
                    if c['call_rate'] > 0:
                        # mobbing: signed wiring — approach calls
                        # (+) vs avoid them (-), per move axis
                        m['prey_mob'] = float(
                            W[:, 11:13, :2].mean())
                    # scent-mark wiring: signed mark-grad -> move.
                    # negative = flee remembered danger (adaptive)
                    m['prey_mark'] = float(W[:, 14:16, :2].mean())
                    m['prey_marklvl'] = float(W[:, 13, :2].mean())
                if s == 'pred' and c['call_rate'] > 0:
                    W = pop.genomes[:, :PRED_S * O] \
                        .reshape(-1, PRED_S, O)
                    # eavesdropping: call-grad senses (7-8) -> move
                    m['pred_hear'] = float(
                        np.abs(W[:, 7:9, :2]).mean())
                    if c['call_flee']:
                        # flee-vector wiring: senses 9-10 -> move
                        m['pred_flee'] = float(
                            np.abs(W[:, 9:11, :2]).mean())
                    # control: prey-density senses -> move
                    m['pred_density'] = float(
                        np.abs(W[:, 1:4, :2]).mean())
                m[f'{s}_energy'] = float(pop.energy.mean())
                m[f'{s}_age'] = float(pop.age.mean())
                m[f'{s}_families'] = int(len(np.unique(pop.family)))
                size = self.world.size
                flat = (pop.pos[:, 1].astype(np.int32) % size) * size \
                    + pop.pos[:, 0].astype(np.int32) % size
                m[f'{s}_disp'] = float(len(np.unique(flat)) / n)
            else:
                for k in (('speed', 'appetite', 'efficiency',
                           'vigilance', 'resist')
                          if s == 'prey' else
                          ('speed', 'ferocity', 'efficiency', 'sense')):
                    m[f'{s}_{k}'] = 0.0
                if s == 'prey':
                    m['infected'] = 0
                    m['virulence'] = 0.0
                m[f'{s}_energy'] = m[f'{s}_age'] = 0.0
                m[f'{s}_families'] = 0
                m[f'{s}_disp'] = 0.0
        return m

    def run(self, ticks, on_tick=None, max_empty=500):
        for _ in range(ticks):
            self.step()
            if on_tick:
                on_tick(self)
            if self.empty_ticks > max_empty:
                break
