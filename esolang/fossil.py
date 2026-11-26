"""fossil.py — read ring tape dumps: the fossil record.

A tape dump is a pickled {rnd, cells, ctxs} snapshot written by
run_ring(dump_dir=...). This module answers the questions a
paleontologist asks: who lived where, what were they made of,
and how did the composition of the world shift over time.
"""
import os
import pickle


def load_all(dump_dir):
    files = sorted(f for f in os.listdir(dump_dir)
                   if f.startswith('tape-'))
    out = []
    for f in files:
        with open(os.path.join(dump_dir, f), 'rb') as fh:
            out.append(pickle.load(fh))
    return out


def signatures(dump):
    """count non-NOP cells by (op, a1, a2) signature"""
    sig = {}
    for c in dump['cells']:
        if c[0] != 'NOP' or c[3] > 0:
            key = tuple(c[:3])
            sig[key] = sig.get(key, 0) + 1
    return sig


def zone_profile(dump, zones, size=4000):
    """occupancy + mean hp per zone vs outside — the geography
    of habitability at this snapshot."""
    zmask = [False] * size
    for zs, ze in zones:
        span = (ze - zs) % size
        for k in range(span):
            zmask[(zs + k) % size] = True
    inn = [c for c, z in zip(dump['cells'], zmask)
           if z and (c[0] != 'NOP' or c[3] > 0)]
    out = [c for c, z in zip(dump['cells'], zmask)
           if not z and (c[0] != 'NOP' or c[3] > 0)]
    def stat(cells):
        if not cells:
            return (0, 0.0)
        return (len(cells), sum(c[3] for c in cells) / len(cells))
    return stat(inn), stat(out)


def diversity(dump):
    """number of distinct live signatures — the world's
    heterozygosity at a moment."""
    return len(signatures(dump))


if __name__ == '__main__':
    import sys
    dumps = load_all(sys.argv[1] if len(sys.argv) > 1
                     else 'runs/ring-z1')
    zones = [(1000, 2000)]
    for d in dumps:
        inn, out = zone_profile(d, zones)
        print(f"rnd {d['rnd']:6d}: diversity {diversity(d):4d} | "
              f"zone {inn[0]:4d} cells hp~{inn[1]:4.1f} | "
              f"out {out[0]:4d} cells hp~{out[1]:4.1f}")
