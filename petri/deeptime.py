"""deeptime.py — 100k-tick ecology run via the sim-runner daemon.

Longest run ever attempted on this substrate. Question: what
does the world do PAST every horizon we've watched? Options:
(a) same oscillating regime forever (stationarity), (b) slow
regime drift (trait equilibria shift), (c) a late-emergent
collapse/speciation event no short run has shown.

Protocol (sim-runner skill): progress print every 5000 ticks,
checkpoint CSV appended every 2000 — a killed run loses at
most the last chunk. Final: deeptime.png + summary line.
"""
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from petri.eco import EcoSim, DEFAULTS
import argparse

P = argparse.ArgumentParser()
P.add_argument('--seed', type=int, default=11)
P.add_argument('--ticks', type=int, default=100_000)
P.add_argument('--out', default='runs/deeptime')
P.add_argument('--disease', type=float, default=0.0)
P.add_argument('--disease-intro', type=float, default=0.0)
P.add_argument('--disease-mort', type=float, default=0.02)
P.add_argument('--disease-mort-exp', type=float, default=1.0)
P.add_argument('--disease-start', type=float, default=0.0)
P.add_argument('--resist-cost', type=float, default=0.0)
P.add_argument('--mutation', type=float, default=0.05)
A = P.parse_args()

TICKS, EVERY, SEED = A.ticks, 50, A.seed
OUT = Path(A.out); OUT.mkdir(parents=True, exist_ok=True)
CSV = OUT / 'dt.csv'


def main():
    c = dict(DEFAULTS)
    c.update(seed=SEED, log_every=EVERY,
             disease=A.disease, disease_intro=A.disease_intro,
             disease_start=A.disease_start,
             disease_mort=A.disease_mort,
             disease_mort_exp=A.disease_mort_exp,
             disease_resist_cost=A.resist_cost,
             mutation=A.mutation)
    sim = EcoSim(c)
    first = not CSV.exists()
    f = open(CSV, 'a', newline='')
    w = None
    rows_new = []
    while sim.world.tick < TICKS:
        sim.step()
        t = sim.world.tick
        if t % EVERY == 0:
            m = sim.metrics(0, 0, 0, 0)
            if w is None:
                w = csv.DictWriter(f, fieldnames=m.keys())
                if first:
                    w.writeheader()
            w.writerow(m)
            rows_new.append(m)
        if t % 5000 == 0:
            f.flush()
            print(f't={t} prey={len(sim.prey)} '
                  f'pred={len(sim.pred)}', flush=True)
    f.close()
    # plot the whole file (cheap enough at 2000 rows)
    f2 = csv.DictReader(open(CSV))
    rows = list(f2)
    t = [int(r['tick']) for r in rows]
    fig, ax = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    ax[0].plot(t, [float(r['pop_prey']) for r in rows],
               lw=.6, label='prey')
    ax[0].plot(t, [float(r['pop_pred']) for r in rows],
               lw=.6, label='pred')
    for i, k in enumerate(('prey_speed', 'prey_efficiency',
                           'infected'), 1):
        ax[i].plot(t, [float(r[k]) for r in rows], lw=.6)
        ax[i].set_ylabel(k)
    ax[0].legend()
    for a in ax:
        a.grid(alpha=.3)
    fig.savefig(OUT / 'deeptime.png', dpi=110)
    tail = rows[-1]
    print(f'DONE t={tail["tick"]} prey={tail["pop_prey"]} '
          f'pred={tail["pop_pred"]} rows={len(rows)}',
          flush=True)


if __name__ == '__main__':
    main()
