"""DNA-analog genome: a symbol sequence that a decoder READS.

Alphabet {0,1,2,3}. A promoter motif (3,1,3,1) opens a gene; codons
are symbol pairs (value = a*4+b, 0..15); codon 15 terminates the gene.
Gene type = first codon:
    0 NODE   -> x, y, mu          (5 codons)
    1 SPRING -> i, j, k, amp, ph  (5 codons; refs node genes seen so far)
    2 FREQ   -> global oscillator freq
    4 REGUL  -> phase-shift / silence the NEXT gene (static modulation)
    5 REFLEX -> [node, edge, shift]: node grounded -> phase offset on
                edge's muscle (sensorimotor reflex arc)
    6 SENSE  -> [signal, edge, shift]: continuous channel modulates
                muscle phase. signals: 0 direction to target,
                1 local slope, 2 com velocity sign,
                3 differential steering: edge field stores a pair
                code (a + b*E); shifts muscle a by +s*smell and
                muscle b by -s*smell, flipping the phase difference
                4 proximity: 1 at target, 0 far - the 'satiation'
                channel, lets a creature tell ARRIVED from zero-smell
    7 INTEG  -> [edge, k]: smell accumulator; s += smell each step,
                muscle phase += k*s. A memory trace in the muscle
                (also an I-controller): keeps direction after the
                stimulus is gone
    other    -> unexpressed (pseudogene substrate)
Variable node/edge counts: body plan can change structurally.
"""
import numpy as np

PROMOTER = (3, 1, 3, 1)
STOP = 15
GENE_LEN = {0: 5, 1: 5, 2: 1, 4: 2, 5: 3, 6: 3, 7: 2}
MAX_NODES = 12


def _codons(seq, i, n):
    """Read up to n codons from seq starting at i; stop at STOP codon.
    Returns (values, next_i)."""
    vals = []
    while len(vals) < n and i + 1 < len(seq):
        c = int(seq[i]) * 4 + int(seq[i + 1])
        i += 2
        if c == STOP:
            break
        vals.append(c)
    return vals, i


def express(seq, n_types=5):
    """Parse sequence -> list of (type, [codons]) genes.
    n_types=4 reproduces the pre-REGUL mapping (old champions)."""
    genes = []
    i = 0
    while i + 4 <= len(seq):
        if tuple(seq[i:i + 4]) == PROMOTER:
            i += 4
            typ, i = _codons(seq, i, 1)
            if not typ:
                continue
            t = typ[0] % n_types   # 3=pseudo, 4=REGUL, 5=REFLEX
            if t == 3:
                _, i = _codons(seq, i, 3)
                genes.append((3, []))
                continue
            vals, i = _codons(seq, i, GENE_LEN.get(t, 3))
            genes.append((t, vals))
        else:
            i += 1
    return genes


def decode(seq, default_freq=1.0, n_types=5):
    """Sequence -> body dict for physics.simulate_body.
    Returns None if the phenotype is unviable (<2 nodes)."""
    genes = express(seq, n_types)
    # REGUL (type 4) modulates the NEXT gene: c1 = phase shift,
    # c2 < 5 silences it entirely (reversible 'deletion').
    mods = {}
    for gi, (t, v) in enumerate(genes):
        if t == 4 and v and gi + 1 < len(genes):
            mods[gi + 1] = (len(v) >= 2 and v[1] < 5,
                            v[0] / 15 * 2 * np.pi)
    pos, mu = [], []
    edges, k, amp, phase = [], [], [], []
    reflex, senses, integ = [], [], []
    freq = default_freq
    for gi, (typ, v) in enumerate(genes):
        silenced, pshift = mods.get(gi, (False, 0.0))
        if silenced:
            continue
        if typ == 0 and len(pos) < MAX_NODES and len(v) >= 3:
            pos.append([v[0] / 15 * 3 - 1.5, v[1] / 15 * 3 - 1.5])
            mu.append(v[2] / 15)
        elif typ == 1 and len(pos) >= 2 and len(v) >= 5:
            i, j = v[0] % len(pos), v[1] % len(pos)
            if i == j:
                continue
            edges.append([i, j])
            k.append(v[2] / 15 * 100)
            amp.append(min(0.45, v[3] / 15 * 0.6))
            phase.append(v[4] / 15 * 2 * np.pi + pshift)
        elif typ == 2 and v:
            freq = 0.5 + v[0] / 15 * 2.5
        elif typ == 5 and len(v) >= 3 and edges:
            reflex.append([v[0] % len(pos), v[1] % len(edges),
                           v[2] / 15 * 2 * np.pi])
        elif typ == 6 and len(v) >= 3 and edges:
            sig = v[0] % 5
            E = len(edges)
            ef = v[1] % (E * E) if sig == 3 else v[1] % E
            senses.append([sig, ef, v[2] / 15 * 2 * np.pi])
        elif typ == 7 and len(v) >= 2 and edges:
            integ.append([v[0] % len(edges), v[1] / 15 * 2 * np.pi])
    if len(pos) < 2:
        return None
    return dict(pos=np.array(pos), edges=np.array(edges or [[0, 1]]),
                k=np.array(k or [10.0]), amp=np.array(amp or [0.0]),
                phase=np.array(phase or [0.0]), mu=np.array(mu),
                freq=freq, n_genes=len(genes),
                reflex=np.array(reflex, float).reshape(-1, 3),
                senses=np.array(senses, float).reshape(-1, 3),
                integ=np.array(integ, float).reshape(-1, 2),
                n_pseudo=sum(1 for t, _ in genes if t == 3),
                n_regul=sum(1 for t, _ in genes if t == 4),
                n_reflex=len(reflex), n_sense=len(senses),
                n_integ=len(integ))


def migrate(seq, n_types, sig_from=4, sig_to=5):
    """Re-encode SENSE signal codons so the decoded signal is
    preserved when the signal-mapping modulus changes (file-format
    migration: same phenotype under new rules)."""
    s = list(int(x) for x in seq)
    i = 0
    while i + 4 <= len(s):
        if tuple(s[i:i + 4]) == PROMOTER:
            i += 4
            typ, i = _codons(s, i, 1)
            if not typ:
                continue
            t = typ[0] % n_types
            n = GENE_LEN.get(t, 3)
            c0 = i                          # first value codon pos
            vals, i = _codons(s, i, n)
            if t == 6 and vals:
                sig = vals[0] % sig_from
                s[c0], s[c0 + 1] = sig // 4, sig % 4
        else:
            i += 1
    return np.array(s, np.int8)


# -- mutations -------------------------------------------------------

def mutate(seq, rng, pt=0.002, indel=0.05, dup=0.08, dele=0.08):
    s = list(seq)
    # point mutations
    m = rng.random(len(s)) < pt
    for i in np.flatnonzero(m):
        s[i] = rng.integers(4)
    # small random insertion
    if rng.random() < indel:
        at = rng.integers(len(s) + 1)
        s[at:at] = list(rng.integers(0, 4, rng.integers(2, 9)))
    # segment duplication -> a chance to copy a whole gene
    if rng.random() < dup and len(s) > 20:
        lo = rng.integers(0, len(s) - 10)
        seg = s[lo:lo + rng.integers(10, 61)]
        at = rng.integers(len(s) + 1)
        s[at:at] = seg
    # segment deletion
    if rng.random() < dele and len(s) > 40:
        lo = rng.integers(0, len(s) - 10)
        del s[lo:lo + rng.integers(5, 31)]
    return np.array(s, np.int8)


def crossover(s1, s2, rng):
    """Single-cut splice of two variable-length sequences."""
    a = rng.integers(0, len(s1) + 1)
    b = rng.integers(0, len(s2) + 1)
    return np.concatenate([s1[:a], s2[b:]]).astype(np.int8)


def random_dna(rng, length=600):
    """Random sequence seeded with promoters so early phenotypes
    are not all empty."""
    s = rng.integers(0, 4, length).astype(np.int8)
    for _ in range(9):
        at = rng.integers(0, length - 4)
        s[at:at + 4] = PROMOTER
    return s
