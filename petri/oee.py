"""OEE diagnostics: was the eco world open-ended?

Bedau-style evolutionary-activity analysis over the family census
(runs/family/families.csv). Structural note: `fam` is a lineage id
fixed at birth; new ids enter ONLY via reseeding, so at family
granularity the world is an immigration-extinction system (island
biogeography) rather than a branching novelty process. The
open-ended question therefore splits in two:
  (a) lineage level - immigration equilibrium vs founder lock-in;
  (b) trait level - does adaptive change inside lineages continue,
      or does the population-weighted trait vector stall?

Outputs: runs/oee/oee.png (9 panels), runs/oee/oee_summary.txt.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

TRAITS = ['speed', 'appetite', 'effic', 'vigil', 'resist']
YOUNG = 1500          # age threshold for "young family" cohort
WIN = 1000            # window for rates
BINS = [(0, 5000), (5000, 15000), (15000, 20000)]


def load(path):
    fams = defaultdict(lambda: defaultdict(list))
    ticks = set()
    with open(path) as fh:
        for r in csv.DictReader(fh):
            f, t = int(r['fam']), int(r['tick'])
            d = fams[f]
            d['tick'].append(t)
            d['n'].append(int(r['n']))
            d['n_inf'].append(int(r['n_inf']))
            for tr in TRAITS:
                d[tr].append(float(r[tr]))
            ticks.add(t)
    for d in fams.values():
        for k in d:
            d[k] = np.array(d[k])
    return fams, sorted(ticks)


def analyse(path):
    fams, ticks = load(path)
    sample = ticks[1] - ticks[0] if len(ticks) > 1 else 50
    birth = {f: d['tick'].min() for f, d in fams.items()}
    death = {f: d['tick'].max() for f, d in fams.items()}
    T = ticks[-1]
    alive_end = {f for f in fams if death[f] == T}
    activity = {f: d['n'].sum() * sample for f, d in fams.items()}

    # per-tick aggregates
    by_tick = defaultdict(dict)                      # tick -> fam -> n
    tr_by_tick = defaultdict(lambda: defaultdict(dict))  # tick -> trait -> fam -> mean
    for f, d in fams.items():
        for i, t in enumerate(d['tick']):
            by_tick[t][f] = d['n'][i]
            for tr in TRAITS:
                tr_by_tick[t][tr][f] = d[tr][i]

    N, D, act_age, young_share = [], [], [], []
    wmean = {tr: [] for tr in TRAITS}     # population-weighted mean
    wstd = {tr: [] for tr in TRAITS}      # between-family spread
    for t in ticks:
        col = by_tick[t]
        ns = np.array(list(col.values()), float)
        fs = list(col.keys())
        N.append(ns.sum()); D.append(len(col))
        ages = np.array([t - birth[f] for f in fs], float)
        act_age.append((ns * ages).sum() / ns.sum())
        young = np.array([ages[i] < YOUNG for i in range(len(fs))])
        young_share.append(ns[young].sum() / ns.sum())
        for tr in TRAITS:
            v = np.array([tr_by_tick[t][tr][f] for f in fs])
            m = (ns * v).sum() / ns.sum()
            wmean[tr].append(m)
            wstd[tr].append(np.sqrt((ns * (v - m) ** 2).sum() / ns.sum()))
    N, D, act_age, young_share = map(np.array, (N, D, act_age, young_share))

    # discovery curve + immigration rate
    seen, cum_fams, new_per_win = set(), [], defaultdict(int)
    for t in ticks:
        new = [f for f in by_tick[t] if f not in seen]
        seen.update(new)
        cum_fams.append(len(seen))
        for _ in new:
            new_per_win[t // WIN] += 1
    cum_fams = np.array(cum_fams)

    # trait velocity: |d(weighted mean)| per 1000 ticks
    tt = np.array(ticks)
    vel = np.zeros(len(tt))
    for tr in TRAITS:
        m = np.array(wmean[tr])
        vel += np.abs(np.gradient(m, tt)) * 1000
    vel /= len(TRAITS)

    # activity concentration
    act_sorted = np.array(sorted(activity.values(), reverse=True), float)
    total_act = act_sorted.sum()
    top1 = act_sorted[0] / total_act
    top5 = act_sorted[:5].sum() / total_act
    hhi = ((act_sorted / total_act) ** 2).sum()

    lifespans = np.array([death[f] - birth[f] for f in fams])
    n_dead = len(fams) - len(alive_end)

    def wstat(arr, lo, hi):
        m = (tt >= lo) & (tt < hi)
        return float(arr[m].mean()) if m.any() else float('nan')

    s = dict(
        T=T, n_fams=len(fams), n_dead=n_dead,
        alive_end=len(alive_end), sample=sample,
        lifespan_med=float(np.median(lifespans)),
        lifespan_max=int(lifespans.max()),
        top1=top1, top5=top5, hhi=hhi,
        actage_end=float(act_age[-1]), actage_ratio=float(act_age[-1] / T),
        young_end=float(young_share[-1]),
        young_early=wstat(young_share, *BINS[0]),
        young_late=wstat(young_share, *BINS[2]),
        immi_early=sum(v for k, v in new_per_win.items() if k * WIN < 5000) / 5,
        immi_late=sum(v for k, v in new_per_win.items() if k * WIN >= 15000) / 5,
        vel_early=wstat(vel, *BINS[0]), vel_mid=wstat(vel, *BINS[1]),
        vel_late=wstat(vel, *BINS[2]),
        D_late=wstat(D, *BINS[2]),
        D_late_cv=float(D[(tt >= 15000)].std() / D[(tt >= 15000)].mean()),
    )
    return dict(ticks=tt, N=N, D=D, act_age=act_age,
                young_share=young_share, cum_fams=cum_fams,
                new_per_win=new_per_win, wmean=wmean, wstd=wstd,
                vel=vel, act_sorted=act_sorted, lifespans=lifespans,
                birth=birth, stats=s)


def chart(r, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    t = r['ticks']
    fig, ax = plt.subplots(3, 3, figsize=(16, 11))

    a = ax[0, 0]
    a.plot(t, r['N'], lw=1.2, label='N prey')
    a.set_yscale('log'); a.set_ylabel('N (log)')
    a2 = a.twinx(); a2.plot(t, r['D'], color='tab:red', lw=1)
    a2.set_ylabel('families D', color='tab:red')
    a.set_title('population & family diversity')

    a = ax[0, 1]
    a.plot(t, r['act_age'], lw=1.2, label='activity-wtd lineage age')
    a.plot(t, t, ls='--', color='gray', label='age = t (founder lock-in)')
    a.set_title('clock test'); a.legend(fontsize=8)

    a = ax[0, 2]
    a.plot(t, r['young_share'], lw=1.2)
    a.set_ylim(0, 1.05)
    a.set_title(f'share of activity from families <{YOUNG}t old')

    a = ax[1, 0]
    a.plot(t, r['cum_fams'], lw=1.2, label='distinct fams seen')
    wins = sorted(r['new_per_win'])
    a2 = a.twinx()
    a2.bar([w * WIN + WIN / 2 for w in wins],
           [r['new_per_win'][w] for w in wins],
           width=WIN * .8, alpha=.35, color='tab:orange')
    a2.set_ylabel('new fams / 1000t', color='tab:orange')
    a.set_title('discovery curve (immigration only!)'); a.legend(fontsize=8)

    a = ax[1, 1]
    for tr in TRAITS:
        a.plot(t, r['wmean'][tr], lw=1, label=tr)
    a.set_title('population-weighted mean traits'); a.legend(fontsize=7)

    a = ax[1, 2]
    a.plot(t, r['vel'], lw=1.2)
    a.set_title('trait velocity |d mean| per 1000t')

    a = ax[2, 0]
    for tr in TRAITS:
        a.plot(t, r['wstd'][tr], lw=1, label=tr)
    a.set_title('between-family trait spread'); a.legend(fontsize=7)

    a = ax[2, 1]
    cs = np.cumsum(r['act_sorted'] / r['act_sorted'].sum())
    a.plot(range(1, len(cs) + 1), cs, lw=1.4)
    a.axhline(.9, ls='--', color='gray', lw=.8)
    a.set_xscale('log'); a.set_ylim(0, 1.02)
    a.set_xlabel('top-k families'); a.set_title('activity concentration (cumulative share)')

    a = ax[2, 2]
    a.hist(r['lifespans'], bins=40)
    a.set_yscale('log')
    a.set_xlabel('lifespan (ticks)'); a.set_title('family lifespan distribution')

    for c in ax.flat:
        c.tick_params(labelsize=8)
    fig.tight_layout()
    fig.savefig(Path(out) / 'oee.png', dpi=110)
    print(f"chart -> {out}/oee.png")


def verdict(r):
    s = r['stats']
    L = []
    L.append(f"T={s['T']}, families total={s['n_fams']}, "
             f"dead={s['n_dead']}, alive at end={s['alive_end']}")
    L.append(f"lifespan: median={s['lifespan_med']:.0f}t, max={s['lifespan_max']}t")
    L.append(f"activity concentration: top1={s['top1']:.1%}, "
             f"top5={s['top5']:.1%}, HHI={s['hhi']:.3f}")
    L.append(f"clock test: act-age at end={s['actage_end']:.0f}t "
             f"(ratio to T: {s['actage_ratio']:.2f}; 1.0 = founder lock-in)")
    L.append(f"young-cohort activity share: early={s['young_early']:.1%} "
             f"-> late={s['young_end']:.1%} (window mean {s['young_late']:.1%})")
    L.append(f"immigration: {s['immi_early']:.1f} vs {s['immi_late']:.1f} "
             f"new fams/1000t (early vs late)")
    L.append(f"trait velocity per 1000t: early={s['vel_early']:.3f}, "
             f"mid={s['vel_mid']:.3f}, late={s['vel_late']:.3f}")
    L.append(f"late diversity D={s['D_late']:.0f} (CV={s['D_late_cv']:.2f})")
    return '\n'.join(L)


def main(path='runs/family/families.csv', out='runs/oee'):
    Path(out).mkdir(parents=True, exist_ok=True)
    r = analyse(path)
    chart(r, out)
    v = verdict(r)
    print(v)
    with open(Path(out) / 'oee_summary.txt', 'w') as fh:
        fh.write(v + '\n')


if __name__ == '__main__':
    main(*sys.argv[1:])
