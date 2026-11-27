"""petri2.py — substrate-2 minimal scaffold.

Energy economics first, genomes as gene-lists, mutation at
copy-time only. See analysis/substrate2-design.md and
substrate2-decisions.md for the reasoning. v1: skeleton +
smoke test, not yet the experiment harness.
"""
import random

# physics constants — the anti-degenerate geometry lives here
METABOLISM = 1.0        # energy per tick, flat, non-genomic (2nd law)
COPY_BASE = 60.0        # big fixed cost of reproduction
COPY_PER_GENE = 2.0     # small per-gene surcharge
SPOT_CAP = 200.0        # local energy spot capacity
SPOT_REGEN = 1.5        # spot regeneration per tick
START_ENERGY = 80.0     # founder endowment — ONE free copy, no more

GENE_TYPES = ("HARVEST", "MOVE", "REPRODUCE")

def make_gene(gtype, param):
    return {"type": gtype, "param": param}

class Cell:
    def __init__(self, genes, energy, x, y):
        self.genes = genes          # list of dicts — the genome
        self.energy = energy
        self.x, self.y = x, y
        self.alive = True
        self.age = 0
        # phenotype is DERIVED, cached per birth — stable in life
        self.harvest_rate = sum(g["param"] for g in genes if g["type"] == "HARVEST")
        self.move_bias = sum(g["param"] for g in genes if g["type"] == "MOVE")
        self.repro_threshold = min(
            (g["param"] for g in genes if g["type"] == "REPRODUCE"),
            default=None)  # no REPRODUCE gene = sterile

def mutate(genes, rng, p_point=0.05, p_del=0.02, p_dup=0.02):
    """mutation at copy time — never in life (verdict 1)"""
    out = []
    for g in genes:
        ng = dict(g)
        if rng.random() < p_point:
            ng["param"] = max(0.1, ng["param"] + rng.gauss(0, 0.5))
        out.append(ng)
        if rng.random() < p_dup:
            out.append(dict(ng))     # duplication: innovation engine
    if out and rng.random() < p_del and len(out) > 1:
        out.pop(rng.randrange(len(out)))  # deletion
    return out

class World:
    def __init__(self, size=32, seed=0):
        self.rng = random.Random(seed)
        self.size = size
        self.spots = [[SPOT_CAP for _ in range(size)] for _ in range(size)]
        self.cells = []
        self.tick = 0

    def seed_founders(self, n=6):
        for _ in range(n):
            g = [make_gene("HARVEST", 2.0), make_gene("MOVE", 1.0),
                 make_gene("REPRODUCE", 100.0)]
            self.cells.append(Cell(g, START_ENERGY,
                                   self.rng.randrange(self.size),
                                   self.rng.randrange(self.size)))

    def step(self):
        rng = self.rng
        for c in self.cells:
            if not c.alive:
                continue
            c.age += 1
            # harvest: local spot is depletable — expansion driver
            spot = self.spots[c.y][c.x]
            got = min(c.harvest_rate, spot)
            self.spots[c.y][c.x] = max(0.0, spot - got)
            c.energy += got - METABOLISM
            # movement: random walk biased by local gradient (v1: plain random)
            if rng.random() < c.move_bias * 0.3:
                c.x = (c.x + rng.choice((-1, 0, 1))) % self.size
                c.y = (c.y + rng.choice((-1, 0, 1))) % self.size
            # reproduction: physics triggered by genome signal, price enforced
            if c.repro_threshold is not None and c.energy >= c.repro_threshold + COPY_BASE + COPY_PER_GENE * len(c.genes):
                cost = COPY_BASE + COPY_PER_GENE * len(c.genes)
                c.energy -= cost
                child_genes = mutate(c.genes, rng)
                child = Cell(child_genes, cost * 0.5, c.x, c.y)  # endowment from cost
                self.cells.append(child)
            if c.energy <= 0:
                c.alive = False
        # spots regenerate — but capped; local depletion guaranteed
        for y in range(self.size):
            for x in range(self.size):
                self.spots[y][x] = min(SPOT_CAP, self.spots[y][x] + SPOT_REGEN)
        self.tick += 1

    def summary(self):
        alive = [c for c in self.cells if c.alive]
        ngenes = [len(c.genes) for c in alive]
        return {"tick": self.tick, "alive": len(alive),
                "mean_genes": sum(ngenes) / len(ngenes) if ngenes else 0,
                "max_genes": max(ngenes) if ngenes else 0}

if __name__ == "__main__":
    w = World(seed=8)
    w.seed_founders(6)
    for _ in range(300):
        w.step()
    print(w.summary())
