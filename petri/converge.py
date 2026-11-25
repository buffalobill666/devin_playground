"""converge.py — the three-witness convergence verdict.

deeptime (s11), s7, s8: three seeds of the same world, 100k
ticks each. Cycle-5 showed s11/s7 converge: violent distinct
youths, same calm old age at capacity ~3400, families 43->2
vs 73->2. s8 is the churn-world: early crash prey 22, then
recovery to 3136, predator overshoot 203. Question: does the
churn world lock in too — is convergence a law of the
substrate, or a property of the calm seeds?

Method: window statistics over late-run (last 20k ticks) vs
youth (first 20k): mean/std of prey pop, pred pop, families,
key genes. If late windows agree across seeds while youth
windows don't — convergence confirmed for all three.
"""
import csv
import statistics as st
from pathlib import Path

RUNS = {'s11': 'runs/deeptime/dt.csv', 's7': 'runs/deeptime-s7/dt.csv',
        's8': 'runs/deeptime-s8/dt.csv'}


def load(p):
    rows = list(csv.DictReader(open(p)))
    for r in rows:
        for k in r:
            r[k] = float(r[k])
    return rows


def window(rows, t0, t1):
    return [r for r in rows if t0 <= r['tick'] < t1]


def stats(win, key):
    v = [r[key] for r in win]
    return st.mean(v), st.stdev(v), min(v), max(v)


def report(rows, tag):
    print(f'== {tag} ==')
    for label, t0, t1 in (('youth  0-20k', 0, 20000),
                          ('mid   40-60k', 40000, 60000),
                          ('late 80-100k', 80000, 100001)):
        w = window(rows, t0, t1)
        pm, ps, plo, phi = stats(w, 'pop_prey')
        qm, qs, qlo, qhi = stats(w, 'pop_pred')
        fm = st.mean([r['prey_families'] for r in w])
        print(f'  {label}: prey {pm:7.0f}±{ps:5.0f} [{plo:.0f},{phi:.0f}]'
              f'  pred {qm:5.1f}±{qs:4.1f} [{qlo:.0f},{qhi:.0f}]'
              f'  fam {fm:.1f}')
    last = rows[-1]
    print(f'  final: prey {last["pop_prey"]:.0f} pred {last["pop_pred"]:.0f}'
          f' fam {last["prey_families"]:.0f}'
          f' | genes spd {last["prey_speed"]:.3f}'
          f' eff {last["prey_efficiency"]:.3f}'
          f' vig {last["prey_vigilance"]:.3f}'
          f' res {last["prey_resist"]:.3f}')


def events(rows, tag):
    """Timeline of crashes/overshoots: prey pop min/max per 10k."""
    print(f'  {tag} events:', end='')
    for t0 in range(0, 100000, 10000):
        w = window(rows, t0, t0 + 10000)
        if not w:
            break
        pv = [r['pop_prey'] for r in w]
        qv = [r['pop_pred'] for r in w]
        print(f'  {t0//1000}k:[{min(pv):.0f}-{max(pv):.0f}]p'
              f'[{min(qv):.0f}-{max(qv):.0f}]', end='')
    print()


def main():
    data = {k: load(v) for k, v in RUNS.items()}
    for tag, rows in data.items():
        report(rows, tag)
    print('\n== event timelines (prey range / pred range per 10k) ==')
    for tag, rows in data.items():
        events(rows, tag)
    # cross-seed late-window agreement
    print('\n== cross-seed late-window (80-100k) comparison ==')
    keys = ('pop_prey', 'pop_pred', 'prey_speed', 'prey_efficiency',
            'prey_vigilance', 'prey_resist', 'prey_families')
    for k in keys:
        vals = []
        for tag, rows in data.items():
            m, s, lo, hi = stats(window(rows, 80000, 100001), k)
            vals.append((tag, m, s))
        spread = max(v[1] for v in vals) - min(v[1] for v in vals)
        line = ' '.join(f'{t}:{m:.2f}' for t, m, _ in vals)
        print(f'  {k:18s} {line}  spread={spread:.2f}')


if __name__ == '__main__':
    main()
