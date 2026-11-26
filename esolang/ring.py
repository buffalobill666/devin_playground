"""ring.py — ring world: migration unbounded, selection continuous.

Linear tape ends; a ring does not. Positions are modulo SIZE:
migrants lap the world, fast fronts overtake slow bodies, and
there is no edge to die at — only each other. Mutation corrupts
copies with probability mu (perturb an arg or swap the op);
the copy a context migrates INTO is the body it becomes.

The parasite question, sharpened honestly before running:
Tierra parasites use a neighbor's copy machinery because memory
is shared in place. Here copying is self-directed migration —
survival IS copying. Can parasitism exist in migration geometry?
Candidates: cargo-riding (junk genes copied for free inside a
copier), collision-harvesting (body refreshed by overwrite that
happens to match). Prediction register:
  P1: genomes compress toward minimal replicators (speed)
  P2: cargo/payload cells die first — they cost copies, give nothing
  P3: collision survival selects speed OR overwrite-robustness
  P4: true parasitism does NOT appear — geometry forbids it.
      If it does, the geometry model is wrong (falsifiable!)

Census: per-context generation progress + periodic tape digests.
"""
import os
import pickle
import random
import sys
sys.path.insert(0, 'esolang')

CRYSTAL = [('CPYR', 0, 8), ('CPYR', 0, 8), ('CPYR', 0, 8),
           ('CPYR', 0, 8), ('JMPR', 4, 0)]
OPL = ['PUSH', 'ADD', 'SUB', 'PRINT', 'JMPR', 'JNZR', 'JZR',
       'CPYR', 'DUP', 'DROP', 'HALT', 'NOP']


OPL_NOHALT = [o for o in OPL if o != 'HALT']


def mutate_cell(cell, rng, mu, alphabet=None):
    op, a1, a2, hp = cell
    if rng.random() >= mu:
        return [op, a1, a2, hp]
    alphabet = alphabet or OPL
    r = rng.random()
    if r < 0.5:
        return [op, a1 + rng.choice([-1, 1]), a2, hp]
    elif r < 0.8:
        return [op, a1, a2 + rng.choice([-1, 1]), hp]
    return [rng.choice(alphabet), a1, a2, hp]


def run_ring(seeds, life, cap_rounds, size=4000, mu=0.002, seed=0,
             census_every=4000, snap_every=0, alphabet=None,
             zones=None, zone_decay=1, dump_dir=None, dump_every=0,
             zone_mu=None, dens_alpha=None, dens_win=20):
    """zones: list of (start, end) hot bands — cells there lose
    zone_decay hp passively every round, executed or not. Wraps
    around. dump_dir/dump_every: pickle tape+ctxs to disk —
    the fossil record."""
    rng = random.Random(seed)
    snaps = []
    deaths = []
    cells = [['NOP', 0, 0, 0] for _ in range(size)]
    ctxs = []
    for pos, genome in seeds:
        for i, (op, a1, a2) in enumerate(genome):
            cells[(pos + i) % size] = [op, a1, a2, life]
        ctxs.append({'ip': pos, 'stack': [], 'alive': True,
                     'start': pos, 'travel': 0, 'mutcells': 0})
    census = []
    for rnd in range(cap_rounds):
        for ctx in ctxs:
            if not ctx['alive']:
                continue
            ip = ctx['ip'] % size
            op, a1, a2, hp = cells[ip]
            if hp <= 0:
                ctx['ip'] += 1
                continue
            cells[ip][3] -= 1
            cur = ip
            ctx['ip'] += 1
            ctx['travel'] += 1
            st = ctx['stack']
            if op == 'PUSH': st.append(a1)
            elif op == 'ADD':
                if len(st) >= 2: st.append(st.pop() + st.pop())
            elif op == 'SUB':
                if len(st) >= 2:
                    a, b = st.pop(), st.pop(); st.append(b - a)
            elif op == 'PRINT': pass
            elif op == 'JMPR': ctx['ip'] = cur + a1
            elif op == 'JNZR':
                if st: ctx['ip'] = cur + a1 if st.pop() != 0 else ctx['ip']
            elif op == 'JZR':
                if st: ctx['ip'] = cur + a1 if st.pop() == 0 else ctx['ip']
            elif op == 'CPYR':
                ctx['copies'] = ctx.get('copies', 0) + 1
                src = (cur + a1) % size
                dst = (cur + a2) % size
                mu_eff = mu
                if dens_alpha is not None:
                    lo = max(0, src - dens_win)
                    hi = min(size, src + dens_win + 1)
                    win = cells[lo:hi]
                    dens = sum(1 for c in win if c[0] != 'NOP') / len(win)
                    mu_eff = mu * (1 + dens_alpha * dens)
                if zone_mu is not None and zones:
                    for zs, ze in zones:
                        if (dst - zs) % size < (ze - zs) % size:
                            mu_eff = zone_mu
                            break
                nc = mutate_cell(cells[src], rng, mu_eff, alphabet)
                if nc[:3] != cells[src][:3]:
                    ctx['mutcells'] += 1
                nc[3] = life
                cells[dst] = nc
            elif op == 'DUP':
                if st: st.append(st[-1])
            elif op == 'DROP':
                if st: st.pop()
            elif op == 'HALT':
                ctx['alive'] = False
                deathsite = [(cells[(ip + k) % size][0],
                              cells[(ip + k) % size][1],
                              cells[(ip + k) % size][2])
                             for k in range(-2, 4)]
                deaths.append(dict(ctx=ctxs.index(ctx), rnd=rnd,
                                   ip=ip, op=op, a1=a1, a2=a2,
                                   site=deathsite,
                                   travel=ctx['travel']))
            if len(st) > 64:
                del st[:-64]
        if zones:
            for zs, ze in zones:
                span = (ze - zs) % size
                for k in range(span):
                    c = cells[(zs + k) % size]
                    if c[3] > 0:
                        c[3] -= zone_decay
        if dump_dir and dump_every and rnd % dump_every == 0:
            os.makedirs(dump_dir, exist_ok=True)
            with open(os.path.join(dump_dir,
                                   f'tape-{rnd:07d}.pkl'), 'wb') as fh:
                pickle.dump({'rnd': rnd, 'cells': cells,
                             'ctxs': [{k: v for k, v in c.items()
                                       if k != 'stack'} for c in ctxs]},
                            fh)
        if snap_every and rnd % snap_every == 0:
            snaps.append(([c[:3] for c in cells],
                          [c['ip'] % size if c['alive'] else -1
                           for c in ctxs]))
        if rnd % census_every == 0:
            alive = sum(1 for c in ctxs if c['alive'])
            trav = [c['travel'] for c in ctxs]
            census.append((rnd, alive, list(trav),
                           sum(c.get('copies', 0) for c in ctxs)))
    if snap_every:
        return cells, ctxs, census, snaps
    return cells, ctxs, census, deaths


if __name__ == '__main__':
    # pilot: 6 identical crystals evenly spaced on a 4000-ring
    K = 6
    seeds = [(i * (4000 // K), CRYSTAL) for i in range(K)]
    cells, ctxs, census = run_ring(seeds, life=30, cap_rounds=60000,
                                   size=4000, mu=0.002)
    for rnd, alive, trav, muts in census:
        print(f'round {rnd:6d}: alive {alive} travel {trav} muts {muts}')
    print('final alive:', sum(1 for c in ctxs if c['alive']))
