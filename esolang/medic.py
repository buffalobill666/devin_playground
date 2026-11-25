"""medic.py — death as economics: repair vs migration.

Host's idea (c6): medics cost currency (earned by executed
work), life extension can't be infinite, parts wear at
different rates. Machine extension of the tape universe:

  HARV  — metabolism: +GAIN energy to the organism's account
          (payload stops being decorative: work feeds repair)
  FIX   — spend COST energy, restore target cell's hp to full
          target: TOS relative to the FIX cell

Algebra of sedentary immortality: every execution burns 1 hp
somewhere; FIX converts energy back into hp at rate life/COST.
If fraction f of executions is HARV: income f*GAIN*life/COST
must cover 1 hp per execution -> f >= COST/(GAIN*life).
The metabolic overhead — comparable to migration's copying
overhead. Which strategy of immortality is cheaper?
"""
import sys
sys.path.insert(0, 'esolang')

LIFE = 30
GAIN = 2
COST = 10


def run_medic(tape, cap, size, life=LIFE, gain=GAIN, cost=COST, trace=False):
    cells = [[op, a1, a2, life] for op, a1, a2 in tape]
    cells += [['HALT', 0, 0, 0] for _ in range(size - len(cells))]
    stack, ip, steps = [], 0, 0
    energy = 0
    stats = {'harv': 0, 'fix': 0, 'fixfail': 0, 'spent': 0}
    while 0 <= ip < len(cells) and steps < cap:
        op, a1, a2, hp = cells[ip]
        if hp <= 0:
            # dead cells stay dead unless fixed — in sessile
            # world control just passes through (NOP sea)
            ip += 1
            continue
        cells[ip][3] -= 1
        steps += 1
        cur = ip
        ip += 1
        if op == 'PUSH': stack.append(a1)
        elif op == 'ADD':
            if len(stack) >= 2: stack.append(stack.pop() + stack.pop())
        elif op == 'SUB':
            if len(stack) >= 2:
                a, b = stack.pop(), stack.pop(); stack.append(b - a)
        elif op == 'PRINT': pass
        elif op == 'JMPR': ip = cur + a1
        elif op == 'JNZR':
            if stack: ip = cur + a1 if stack.pop() != 0 else ip
        elif op == 'JZR':
            if stack: ip = cur + a1 if stack.pop() == 0 else ip
        elif op == 'DUP':
            if stack: stack.append(stack[-1])
        elif op == 'DROP':
            if stack: stack.pop()
        elif op == 'HARV':
            energy += gain
            stats['harv'] += 1
        elif op == 'FIX':
            stats['fix'] += 1
            if not stack:
                continue
            tgt = cur + stack.pop()
            if energy >= cost and 0 <= tgt < len(cells):
                if cells[tgt][0] != 'HALT' or cells[tgt][3] > 0:
                    pass
                energy -= cost
                stats['spent'] += cost
                cells[tgt][3] = life
            else:
                stats['fixfail'] += 1
        elif op == 'HALT':
            break
    return steps, energy, stats, cells


# --- the sedentary organism: harvest + repair loop ---------
# design: a loop that executes HARV twice, then FIXes each of
# its N cells in turn (round-robin via counter), repeat.
# v1 simplest: unrolled repair wave — every pass: HARV x k,
# then FIX self cells one by one with constant offsets.

def build_sessile():
    """Minimal sedentary immortal attempt: linear sweep that
    harvests and fixes every body cell each pass, forever.
    Layout: [HARV][HARV][FIX self-k for each k][JMPR back]"""
    n_body = 8          # cells covered by repair wave
    cells = []
    cells.append(('HARV', 0, 0))      # 0
    cells.append(('HARV', 0, 0))      # 1
    # fix cells 0..n_body-1: FIX with offset from current cell
    for k in range(n_body):
        # FIX cell at position 2+k wants to repair cell k:
        # offset = k - (2+k) = -2 ... not uniform. trick:
        # use PUSH offset; FIX pops it. so each fix is two cells:
        pass
    # simpler: PUSH off; FIX — pairs
    cells = [('HARV', 0, 0), ('HARV', 0, 0)]
    pos = len(cells)
    for k in range(n_body):
        # at position len(cells): PUSH (k - (len+1)) then FIX pops
        pushpos = len(cells)
        fixpos = pushpos + 1
        off = k - fixpos
        cells.append(('PUSH', off, 0))
        cells.append(('FIX', 0, 0))
    jpos = len(cells)
    cells.append(('JMPR', -jpos, 0))   # back to cell 0
    return cells


if __name__ == '__main__':
    tape = build_sessile()
    print('sessile genome:', len(tape), 'cells')
    for i, c in enumerate(tape[:8]):
        print(f'  {i}: {c}')
    steps, energy, stats, cells = run_medic(tape, cap=20000, size=2000)
    alive = sum(1 for c in cells[:len(tape)] if c[3] > 0)
    print(f'steps {steps}, energy {energy}, stats {stats}')
    print(f'body cells alive after run: {alive}/{len(tape)}')
    print(f'hp pattern first 10: {[c[3] for c in cells[:10]]}')
