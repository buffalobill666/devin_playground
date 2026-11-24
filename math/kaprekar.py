"""kaprekar.py — Kaprekar's routine, proven exhaustively.

Math thread: for a 4-digit number with non-identical digits,
repeat: sort digits descending minus ascending -> reaches
6174 (the Kaprekar constant). Claim: every valid start gets
there in <= 7 steps.

Don't believe it — enumerate it: there are only 8991 valid
4-digit starts, so "converges always" is checkable in full,
and the step-count distribution is a free histogram. Also
check the 3-digit analog (495) and note where the routine
fails (identical digits -> 0, a different fixed point).

Outputs: kaprekar.png (histogram of steps to convergence),
verdict line. A numeric claim you can enumerate is a proof,
not a conjecture — same discipline as the zebra generator.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def kaprekar_step(n, digits):
    s = f'{n:0{digits}d}'
    return int(''.join(sorted(s, reverse=True))) - \
        int(''.join(sorted(s)))


def converge(n, digits, limit=100):
    seen = [n]
    for _ in range(limit):
        n = kaprekar_step(n, digits)
        if n == seen[-1]:
            return n, len(seen) - 1
        seen.append(n)
    return None, -1


def census(digits):
    """Every start -> (fixed point, steps). Returns step counts
    for the main attractor and a list of non-convergers."""
    steps, odd = {}, []
    for n in range(10 ** (digits - 1), 10 ** digits):
        if len(set(f'{n:0{digits}d}')) == 1:
            continue                    # repdigits -> 0 instantly
        fp, k = converge(n, digits)
        if fp is None:
            odd.append(n)
        else:
            steps.setdefault((fp, k), 0)
            steps[(fp, k)] = steps.get((fp, k), 0) + 1
    return steps, odd


def main():
    for digits, const in ((3, 495), (4, 6174)):
        steps, odd = census(digits)
        main_fp = max({fp for fp, _ in steps},
                      key=lambda f: sum(v for (p, _), v
                                        in steps.items() if p == f))
        fps = {fp for fp, _ in steps}
        maxk = max(k for _, k in steps)
        allmain = fps == {main_fp}
        print(f'{digits}-digit: fixed points {sorted(fps)}, '
              f'main {main_fp} (expected {const}), '
              f'max steps {maxk}, non-convergers {len(odd)}')
        assert main_fp == const and allmain and not odd
        if digits == 4:
            hist = {k: steps.get((6174, k), 0)
                    for k in range(1, 8)}
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(hist.keys(), hist.values(), color='#445588')
            ax.set_xlabel('steps to 6174')
            ax.set_ylabel('count of 4-digit starts')
            ax.set_title('Kaprekar routine — convergence '
                         'speed census (n=8991)')
            for k, v in hist.items():
                ax.text(k, v + 20, str(v), ha='center',
                        fontsize=9)
            fig.savefig('math/kaprekar.png', dpi=140,
                        bbox_inches='tight')
            print('histogram:', hist)
    print('VERDICT: OK — convergence proven by enumeration')


if __name__ == '__main__':
    main()
