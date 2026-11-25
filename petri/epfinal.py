"""epfinal.py — final verdict for the ep300 experiment.

Compares runs/ep300-s11 (disease ON, resist cost 0.08) against
runs/deeptime (seed 11, disease OFF). Questions pre-registered
in iteration 12:
  1. does the world lock ecologically despite endemic disease?
  2. does resist plateau (cost/benefit equilibrium) or ratchet
     to ceiling (cost too weak)?
  3. is the lock epidemiologically hot (endemic) or cold?
"""
import csv
import statistics as st
import sys


def load(path):
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        for k in r:
            try:
                r[k] = float(r[k])
            except (ValueError, KeyError):
                pass
    return rows


def blocks(rows, size=10000):
    out = {}
    for r in rows:
        out.setdefault(int(r['tick']) // size, []).append(r)
    return out


def verdict(ep, base):
    rep = []
    lastblk = max(blocks(ep))
    final = blocks(ep)[lastblk]
    t_end = final[-1]['tick']

    # 1. ecological lock: crashes prey<200 in final 30% vs early
    t70 = t_end * 0.7
    late = [r for r in ep if r['tick'] > t70]
    early = [r for r in ep if r['tick'] < t_end * 0.3]
    cr_late = sum(1 for r in late if r['pop_prey'] < 200)
    cr_early = sum(1 for r in early if r['pop_prey'] < 200)
    rep.append(f"crashes prey<200: early {cr_early}, late(after 70%) {cr_late}")
    rep.append(f"final prey mean: {st.mean(r['pop_prey'] for r in late):.0f} "
               f"pred: {st.mean(r['pop_pred'] for r in late):.1f}")

    # 2. resist trajectory: slope in final 30% of run
    rs = [(r['tick'], r['prey_resist']) for r in ep if r['tick'] > t70]
    if len(rs) > 10:
        slope = (rs[-1][1] - rs[0][1]) / (rs[-1][0] - rs[0][0]) * 10000
        rep.append(f"resist: final {rs[-1][1]:.3f}, slope in late run "
                   f"{slope:+.4f}/10k — {'PLATEAU' if abs(slope) < 0.01 else 'STILL RATCHETING' if slope > 0 else 'SAGGING'}")

    # 3. endemicity in lock
    inf_late = st.mean(r['infected'] for r in late)
    rep.append(f"infected mean in late lock: {inf_late:.1f} — {'ENDEMIC lock' if inf_late > 1 else 'cold lock'}")

    # 4. step analysis (pre-registered i21): jump per wave vs sag per lull
    waves = []
    inwave = False
    wstart = None
    for idx, r in enumerate(ep):
        if r['tick'] < 100000:
            continue
        if not inwave and r['infected'] > 30:
            inwave = True; wstart = idx
        elif inwave and r['infected'] < 2:
            inwave = False
            waves.append((wstart, idx))
    jumps = []
    for a, b in waves:
        if b + 10 < len(ep):
            before = ep[max(0, a - 3):a + 1]
            after = ep[b:b + 4]
            if before and after:
                jumps.append(st.mean(x['prey_resist'] for x in after)
                             - st.mean(x['prey_resist'] for x in before))
    lull_sags = []
    # lulls: stretches infected<2, measure resist drift across them
    inzero = False
    zstart = None
    for idx, r in enumerate(ep):
        if r['tick'] < 100000:
            continue
        if not inzero and r['infected'] < 1:
            inzero = True; zstart = idx
        elif inzero and r['infected'] >= 1:
            inzero = False
            if idx - zstart >= 10:
                lull_sags.append(ep[idx - 1]['prey_resist'] - ep[zstart]['prey_resist'])
    if jumps:
        rep.append(f"wave step: mean dResist across wave = {st.mean(jumps):+.4f} (n={len(jumps)})")
    if lull_sags:
        rep.append(f"lull sag: mean dResist across lull = {st.mean(lull_sags):+.4f} (n={len(lull_sags)})")
    if jumps and lull_sags:
        net = st.mean(jumps) * len(jumps) + st.mean(lull_sags) * len(lull_sags)
        rep.append(f"net drift in lock: {net:+.4f} over measured events — "
                   f"{'true PLATEAU' if abs(net) < 0.01 else 'upward RATCHET' if net > 0 else 'downward sag'}")

    # baseline comparison
    bl = blocks(base)
    blast = bl[max(bl)]
    basefinal = [r for r in base if r['tick'] > base[-1]['tick'] * 0.7]
    rep.append(f"baseline deeptime s11: prey {st.mean(r['pop_prey'] for r in basefinal):.0f} "
               f"resist {basefinal[-1].get('prey_resist', float('nan')):.3f} "
               f"infected {st.mean(r['infected'] for r in basefinal):.1f}")
    return '\n'.join(rep)


if __name__ == '__main__':
    ep = load('runs/ep300-s11/dt.csv')
    base = load('runs/deeptime/dt.csv')
    print(f'ep300 rows {len(ep)} t={ep[-1]["tick"]:.0f}; baseline rows {len(base)}')
    print(verdict(ep, base))
