"""epwave.py — pilot verdict for the disease-pressure design.

The design question: with a maintenance cost on resist, does
immunity become a real tradeoff trait? Signatures to check:

1. resist rises DURING waves (benefit dominates)
2. resist sags BETWEEN waves (cost dominates) — the anti-ratchet;
   in the costless model it only ever rose
3. disease neither explodes forever nor dies permanently —
   waves recur on the pilot horizon
4. population survives: no extinction lockstep

Reads runs/ep300-pilot/dt.csv, prints wave timeline and the
resist-vs-infected lag correlation.
"""
import csv
import statistics as st


def main():
    rows = list(csv.DictReader(open('runs/ep300-pilot/dt.csv')))
    for r in rows:
        for k in r:
            r[k] = float(r[k])

    # wave timeline per 1000 ticks
    print('== waves (per 1k: peak infected / mean resist) ==')
    for t0 in range(0, 15000, 1000):
        w = [r for r in rows if t0 <= r['tick'] < t0 + 1000]
        if not w:
            break
        pk = max(r['infected'] for r in w)
        mr = st.mean(r['prey_resist'] for r in w)
        mv = st.mean(r['virulence'] for r in w)
        pop = w[-1]['pop_prey']
        bar = '#' * int(pk / 40)
        print(f'  {t0//1000:2d}k: inf {pk:5.0f} {bar:30s}'
              f' res {mr:.3f} vir {mv:.2f} prey {pop:.0f}')

    # the tradeoff test: correlate resist CHANGE with current infection
    print('\n== tradeoff test: does resist follow pressure? ==')
    xs, ys_up, ys_dn = [], [], []
    for a, b in zip(rows, rows[20:]):
        if b['tick'] - a['tick'] != 1000:
            continue
        dr = b['prey_resist'] - a['prey_resist']
        inf = a['infected']
        if inf > 30:
            ys_up.append(dr)
        elif inf < 1:
            ys_dn.append(dr)
    if ys_up:
        print(f'  during waves (inf>30): mean dResist/1k = '
              f'{st.mean(ys_up):+.4f}  (n={len(ys_up)})')
    if ys_dn:
        print(f'  in lulls   (inf<1) : mean dResist/1k = '
              f'{st.mean(ys_dn):+.4f}  (n={len(ys_dn)})')
    print('  tradeoff confirmed if waves push up and lulls pull down')

    last = rows[-1]
    print(f'\nfinal t={last["tick"]:.0f}: prey {last["pop_prey"]:.0f}'
          f' pred {last["pop_pred"]:.0f} inf {last["infected"]:.0f}'
          f' res {last["prey_resist"]:.3f} vir {last["virulence"]:.3f}'
          f' fam {last["prey_families"]:.0f}')


if __name__ == '__main__':
    main()
