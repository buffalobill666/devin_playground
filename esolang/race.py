"""race.py — two migrants, one tape, round-robin time.

The evolution question needs a population; the population
needs a scheduler. Each organism is an (ip, stack) context;
the world executes one instruction per context per round.
Copies overwrite whatever is at the destination — including
another organism's cells. Speed becomes fitness: the crystal
(5 cells, ~7 steps/gen) chases the worker (18 cells,
~239 steps/gen). What happens when the fast front reaches
the slow body?
"""
import sys
sys.path.insert(0, 'esolang')
from worker import build as build_worker

CRYSTAL = [('CPYR', 0, 8), ('CPYR', 0, 8), ('CPYR', 0, 8),
           ('CPYR', 0, 8), ('JMPR', 4, 0)]  # stride 8, fallthrough tail


def run_race(tape_inits, life, cap_rounds, size=8000):
    """tape_inits: list of (start_pos, genome). Returns log."""
    cells = [['HALT', 0, 0, 0] for _ in range(size)]
    ctxs = []
    for pos, genome in tape_inits:
        for i, (op, a1, a2) in enumerate(genome):
            cells[pos + i] = [op, a1, a2, life]
        ctxs.append({'ip': pos, 'stack': [], 'alive': True,
                     'start': pos, 'max_ip': pos})
    log = []
    for rnd in range(cap_rounds):
        for ci, ctx in enumerate(ctxs):
            if not ctx['alive']:
                continue
            ip = ctx['ip']
            if not (0 <= ip < size):
                ctx['alive'] = False
                continue
            op, a1, a2, hp = cells[ip]
            if hp <= 0:
                ctx['ip'] += 1
                continue
            cells[ip][3] -= 1
            cur = ip
            ctx['ip'] += 1
            st = ctx['stack']
            if op == 'PUSH': st.append(a1)
            elif op == 'ADD':
                if len(st) >= 2: st.append(st.pop() + st.pop())
            elif op == 'SUB':
                if len(st) >= 2:
                    a, b = st.pop(), st.pop(); st.append(b - a)
            elif op == 'PRINT': pass
            elif op == 'JMPR': ctx['ip'] = cur + a1
            elif op == 'JNZR':
                if st: ctx['ip'] = cur + a1 if st.pop() != 0 else ctx['ip']
            elif op == 'JZR':
                if st: ctx['ip'] = cur + a1 if st.pop() == 0 else ctx['ip']
            elif op in ('CPY', 'CPYR'):
                if op == 'CPY':
                    if len(st) < 2: continue
                    dr = st.pop(); sr = st.pop()
                else:
                    dr, sr = a2, a1
                src, dst = cur + sr, cur + dr
                if 0 <= src < size and 0 <= dst < size:
                    o, x1, x2, _h = cells[src]
                    cells[dst] = [o, x1, x2, life]
            elif op == 'DUP':
                if st: st.append(st[-1])
            elif op == 'DROP':
                if st: st.pop()
            elif op == 'HALT':
                ctx['alive'] = False
            ctx['max_ip'] = max(ctx['max_ip'], ctx['ip'])
        if rnd % 2000 == 0:
            log.append((rnd, [c['max_ip'] for c in ctxs],
                        [c['alive'] for c in ctxs]))
    return cells, ctxs, log


if __name__ == '__main__':
    worker, n, D, pay0 = build_worker()
    print(f'worker n={n} D={D}; crystal len={len(CRYSTAL)} stride=8')
    # chase: worker starts 400 ahead, crystal behind at 0
    cells, ctxs, log = run_race(
        [(400, worker), (0, CRYSTAL)], life=30, cap_rounds=60000)
    for rnd, fronts, alives in log[-8:]:
        print(f'round {rnd:6d}: worker front {fronts[0]:5d} '
              f'crystal front {fronts[1]:5d} alive {alives}')
    print('final:', [(c['alive'], c['max_ip']) for c in ctxs])
