"""resolution.py — non-Platonic autopoiesis, checked in my substrate.

arXiv:2407.21086 (found in horizon-scan c5/и23): an ALenia
glider keeps its morphology only at coarse simulation — refine
the grid and it dissolves. The claim, generalized: a creature's
existence is a property of the (creature, resolution) pair,
not of the creature alone.

Test here: nucleate the orbium colony at N=128/R=13 by the
established adiabatic recipe (anneal mu .135→.15, s .03→.015),
then resample the SAME field onto coarser (N=64, R=7) and
finer (N=256, R=26) grids — physical creature size held
constant, kernel radius scaled with N. Evolve all three at
the canonical point for 400 ticks, track total mass.

If existence were Platonic, all three live or all three die.
If the substrate matters, they disagree.
"""

import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orbium                                        # noqa: E402

MU, SIG, TICKS = 0.15, 0.015, 400


def nucleate():
    """The orbium.py recipe, verbatim, at N=128/R=13."""
    orbium.N, orbium.R = 128, 13
    Fk = orbium.fft_kernel()
    rng = np.random.default_rng(7)
    A = orbium.speckle(rng)
    for _ in range(300):
        A = orbium.step(A, Fk, 0.135, 0.03)
    for i in range(600):
        f = i / 600
        A = orbium.step(A, Fk, 0.135 + 0.015 * f,
                        0.03 - 0.015 * f)
    return A


def resample(A, n):
    """Re-grid A to n×n: average-pool down / bilinear up."""
    if n < A.shape[0]:
        f = A.shape[0] // n
        return A.reshape(n, f, n, f).mean((1, 3))
    f = n // A.shape[0]
    return np.kron(A, np.ones((f, f)))


def live_test(A0, n, r, ticks=TICKS):
    """Same canonical regime on the resampled field."""
    orbium.N, orbium.R = n, r
    Fk = orbium.fft_kernel()
    A = A0.copy()
    m0 = A.sum()
    for t in range(ticks):
        A = orbium.step(A, Fk, MU, SIG)
    return A.sum() / m0, A


def main():
    A128 = nucleate()
    print(f'nucleated at 128: mass={A128.sum():.0f}, '
          f'live={100 * (A128 > 0.5).mean():.1f}%')
    for n, r in [(64, 7), (128, 13), (256, 26)]:
        ratio, _ = live_test(resample(A128, n), n, r)
        print(f'N={n:>3} R={r:>2}: mass ratio after {TICKS} '
              f'ticks = {ratio:.3f} '
              f'({"HOLDS" if ratio > 0.7 else "DISSOLVES"})')


if __name__ == '__main__':
    main()
