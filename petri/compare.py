"""Compare metric curves across petri runs.

Usage: python -m petri.compare runs/baseline-* runs/lowmut-* ...
"""
import argparse
import csv
from pathlib import Path


def load(run_dir):
    with open(Path(run_dir) / 'metrics.csv') as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in r:
            r[k] = float(r[k])
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('runs', nargs='+')
    p.add_argument('--out', default=None)
    args = p.parse_args()

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    series = {Path(r).name: load(r) for r in args.runs}
    out = args.out or str(Path(args.runs[0]).parent / 'compare.png')

    fig, ax = plt.subplots(4, 1, figsize=(11, 13), sharex=True)
    for name, rows in series.items():
        t = [r['tick'] for r in rows]
        ax[0].plot(t, [r['pop'] for r in rows], label=name)
        ax[1].plot(t, [r['families'] for r in rows], label=name)
        ax[2].plot(t, [r['food'] for r in rows], label=name)
        for i, k in enumerate(('speed', 'appetite', 'efficiency')):
            ax[3].plot(t, [r[k] for r in rows], label=f'{name}:{k}',
                       alpha=.8)
        ax[3].plot(t, [r['energy'] for r in rows], ls=':', alpha=.3)
    ax[0].set_ylabel('population')
    ax[1].set_ylabel('families')
    ax[2].set_ylabel('total food')
    ax[3].set_ylabel('mean trait')
    ax[3].set_ylim(0, 1.05)
    ax[3].set_xlabel('tick')
    ax[3].legend(fontsize=7, ncol=3)
    for a in ax[:3]:
        a.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(out)


if __name__ == '__main__':
    main()
