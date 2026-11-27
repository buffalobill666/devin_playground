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
SPOT_REGEN = 0.3
MAX_EXTRACT = 3.0   # saturation cap per channel per tick        # spot regeneration per tick
START_ENERGY = 80.0     # founder endowment — ONE free copy, no more

GENE_TYPES = ("HARVEST", "MOVE", "REPRODUCE")

def make_gene(gtype, param):
    return {"type": gtype, "param": param, "expr": 1.0}

class Cell:
    def __init__(self, genes, energy, x, y):
        self.genes = genes          # list of dicts — the genome
        self.energy = energy
        self.x, self.y = x, y
        self.alive = True
        self.age = 0
        # phenotype is DERIVED, cached per birth — stable in life
        # harvest: rate x affinity per channel; affinity drifts with mutation
        self.harvests = [(g["param"] * g.get("expr", 1.0), g.get("aff", 0.5)) for g in genes if g["type"] == "HARVEST"]
        self.harvest_rate = sum(p for p, a in self.harvests)
        self.move_bias = sum(g["param"] * g.get("expr", 1.0) for g in genes if g["type"] == "MOVE")
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
        if ng["type"] == "HARVEST" and rng.random() < p_point:
            ng["aff"] = min(1.0, max(0.0, ng.get("aff", 0.5) + rng.gauss(0, 0.2)))
        if rng.random() < p_point:
            ng["expr"] = min(1.0, max(0.0, ng.get("expr", 1.0) + rng.gauss(0, 0.25)))
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
        self.spots = [[[SPOT_CAP, SPOT_CAP] for _ in range(size)] for _ in range(size)]
        self.cells = []
        self.tick = 0

    def seed_founders(self, n=6):
        for _ in range(n):
            g = [dict(make_gene("HARVEST", 2.0), aff=0.5), make_gene("MOVE", 1.0),
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
            got = 0.0
            chan_got = [0.0, 0.0]
            for rate, aff in c.harvests:
                for ch, w in ((0, 1.0 - aff), (1, aff)):
                    want = rate * w
                    take = min(want, spot[ch], max(0.0, MAX_EXTRACT - chan_got[ch]))
                    spot[ch] -= take
                    chan_got[ch] += take
                    got += take
            c.energy += got - METABOLISM
            # movement: random walk biased by local gradient (v1: plain random)
            if rng.random() < min(1.0, c.move_bias * 0.3):
                c.energy -= 0.8
                # taxis: sense neighbors, prefer richer spot for own affinity profile
                best, bestv = (c.x, c.y), -1.0
                meanaff = (sum(p * a for p, a in c.harvests) / sum(p for p, a in c.harvests)) if c.harvests else 0.5
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = (c.x + dx) % self.size, (c.y + dy) % self.size
                    sp = self.spots[ny][nx]
                    v = sp[0] * (1.0 - meanaff) + sp[1] * meanaff + rng.random() * 5.0
                    if v > bestv:
                        bestv, best = v, (nx, ny)
                c.x, c.y = best
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
                green_share = 1.0 - x / self.size   # west green-rich, east blue-rich
                self.spots[y][x][0] = min(SPOT_CAP, self.spots[y][x][0] + SPOT_REGEN * green_share)
                self.spots[y][x][1] = min(SPOT_CAP, self.spots[y][x][1] + SPOT_REGEN * (1.0 - green_share))
        self.tick += 1

    def census(self):
        """living diversity — never fossils (museum trap 2)"""
        alive = [c for c in self.cells if c.alive]
        if not alive:
            return {"tick": self.tick, "alive": 0}
        ngenes = [len(c.genes) for c in alive]
        has_harvest = sum(1 for c in alive if c.harvest_rate > 0.5)
        has_repro = sum(1 for c in alive if c.repro_threshold is not None)
        # degenerate signature: REPRODUCE present, HARVEST lost
        degenerate = sum(1 for c in alive
                         if c.repro_threshold is not None and c.harvest_rate <= 0.5)
        return {"tick": self.tick, "alive": len(alive),
                "mean_genes": round(sum(ngenes) / len(ngenes), 2),
                "max_genes": max(ngenes),
                "harvesters": has_harvest, "reproducers": has_repro,
                "degenerate": degenerate}

    def summary(self):
        return self.census()

if __name__ == "__main__":
    import sys, os
    ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    os.makedirs("runs", exist_ok=True)
    out = open(f"runs/p2-s{seed}.csv", "w")
    out.write("tick,alive,mean_genes,max_genes,harvesters,reproducers,degenerate" + chr(10))
    w = World(seed=seed)
    w.seed_founders(6)
    for _ in range(ticks):
        w.step()
        if w.tick % 200 == 0:
            c = w.census()
            row = [c.get(k, "") for k in
                   ("tick", "alive", "mean_genes", "max_genes",
                    "harvesters", "reproducers", "degenerate")]
            out.write(",".join(str(x) for x in row) + chr(10))
            out.flush()
        if not any(c.alive for c in w.cells):
            print(f"EXTINCT at tick {w.tick}")
            break
    out.close()
    print("final:", w.census())
