"""periods.py — attractor-class analysis of deeptime runs.

Scan-find arXiv:2512.15534 frames OEE diagnostics in terms of
attractor structure: cyclic phenotypes vs settling. The deeptime
verdict (c6i2) says all three seeds converge to the same calm
old age. The sharper question: WHAT KIND of attractor transition
is that?

Hypothesis: the violent youth is a limit cycle — population
boom/crash oscillations with dominant periods (predator-prey
Lotka-Volterra-ish). The locked old age is a fixed point —
no periodic structure, flat spectrum. Convergence = a change
of attractor CLASS, not just of mean values.

Method: windowed FFT power spectra of prey population (detrended)
in youth (10-30k), mid (40-60k) and late (80-100k) windows.
Dominant period + spectral concentration (share of power in the
top peak) per window per seed.
"""
import csv
import numpy as np

RUNS = {'s11': 'runs/deeptime/dt.csv', 's7': 'runs/deeptime-s7/dt.csv',
        's8': 'runs/deeptime-s8/dt.csv'}
EVERY = 50  # sampling interval, ticks


def load(p):
    rows = list(csv.DictReader(open(p)))
    t = np.array([float(r['tick']) for r in rows])
    prey = np.array([float(r['pop_prey']) for r in rows])
    pred = np.array([float(r['pop_pred']) for r in rows])
    return t, prey, pred


def spectrum(ts, label):
    """Dominant period and peak concentration of the detrended series."""
    x = ts - np.mean(ts)
    x = x - np.polyval(np.polyfit(np.arange(len(x)), x, 1),
                       np.arange(len(x)))  # detrend
    if np.std(x) < 1e-9:
        return 0.0, 0.0, 0.0
    n = len(x)
    win = np.hanning(n)
    F = np.abs(np.fft.rfft(x * win)) ** 2
    F[0] = 0  # kill DC
    freqs = np.fft.rfftfreq(n, d=EVERY)
    pk = int(np.argmax(F))
    period = 1.0 / freqs[pk] if freqs[pk] > 0 else 0.0
    conc = F[pk] / F.sum()
    total = F.sum() / (np.std(x) ** 2 + 1e-12)
    return period, conc, np.std(x)


def main():
    print('attractor structure: dominant period / spectral concentration'
          ' / amplitude (std)')
    print(f'{"seed":4s} {"window":12s} {"prey":38s} {"pred":38s}')
    for tag, p in RUNS.items():
        t, prey, pred = load(p)
        for label, t0, t1 in (('youth 10-30k', 10000, 30000),
                              ('mid   40-60k', 40000, 60000),
                              ('late 80-100k', 80000, 100000)):
            m = (t >= t0) & (t < t1)
            pp, pc, pa = spectrum(prey[m], label)
            qp, qc, qa = spectrum(pred[m], label)
            print(f'{tag:4s} {label:12s} '
                  f'P={pp:7.0f}t conc={pc:4.2f} std={pa:6.0f}     '
                  f'P={qp:7.0f}t conc={qc:4.2f} std={qa:6.1f}')
        print()


if __name__ == '__main__':
    main()
