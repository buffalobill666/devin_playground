"""senex_work.py — SENEX economics: work output vs program size.

senex_layers established: k-layer programs live
  steps = 2*life*(k+1)*(k+2)   (15 points, exact)
with 4k+5 cells. This file asks the economic question the
law raises: each loop costs ~4k+5 executions but produces
1 PRINT — total work = steps / cells_per_loop. Prints grow
~linearly in k (quadratic lifespan / linear cost) -> deeper
maintenance buys total output. But marginal PRINT per added
cell falls. Open question: (a) does the law hold for k up
to 10 and life up to 8, (b) where does marginal efficiency
turn, (c) is there an optimal k given fixed size N?

Also tests a REAL alternative: 'lean' build where the last
layer repairs only HALF the layer below (partial coverage —
cheaper tail, earlier death?) — does partial coverage still
pay?
"""

from senex import assemble, run
from senex_layers import build


def build_lean(k):
    """Last layer covers only body+JMP, NOT the layer below —
    a cheap tail that saves 4 cells but leaves repairers
    uncovered."""
    lines = ['      PUSH 0', 'loop: PUSH 1', '      ADD',
             '      PRINT']
    jmp_idx = 4 + 4 * (k - 1) + 4 if k else None
    # layers 1..k-1 full coverage; layer k covers body+JMP only
    targets = [1, 2, 3, 4 + 4 * k]
    for layer in range(k - 1):
        nt = []
        for t in targets:
            nt.append(len(lines))
            lines.append(f'      RENEW {t}')
        targets = nt
    for t in [1, 2, 3, 4 + 4 * k]:
        lines.append(f'      RENEW {t}')
    lines.append('      JMP loop')
    return '\n'.join(lines)


def measure(src, life, cap=200000):
    tape = assemble(src)
    steps, out, dead = run(tape, life=life, cap=cap)
    return steps, len(out), len(tape)


if __name__ == '__main__':
    print('== law map: k x life (steps; expect 2*L*(k+1)(k+2))')
    bad = 0
    for k in (0, 1, 3, 6, 10):
        row = []
        for L in (2, 3, 5, 8):
            steps, prints, n = measure(build(k), L)
            pred = 2 * L * (k + 1) * (k + 2) if k else 2 * L + 1
            dev = abs(steps - pred) / pred
            bad += dev > 0.15
            row.append(f'{steps:>7}({dev:+.0%})')
        print(f'k={k:>2}: ' + ' '.join(row))
    print(f'law deviations >15%: {bad}')

    print('\n== economics (life=5): prints per cell by k')
    for k in (0, 1, 2, 4, 6, 8):
        steps, prints, n = measure(build(k), 5)
        print(f'k={k}: prints={prints:>5} cells={n:>3} '
              f'eff={prints/n:.2f} '
              f'marginal={"" if k == 0 else ""}', flush=True)

    print('\n== lean tail (partial last layer), life=5')
    for k in (1, 2, 3, 4):
        src = build_lean(k)
        tape = assemble(src)
        steps, out, dead = run(tape, life=5, cap=200000)
        full_steps, full_out, full_n = measure(build(k), 5)
        print(f'k={k}: lean cells={len(tape)} steps={steps} '
              f'prints={len(out)} | full cells={full_n} '
              f'steps={full_steps} prints={full_out}')
