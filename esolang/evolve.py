"""evolve.py — mutation during copying: does the worker
spontaneously revert to crystal?

Mutation model: each CPY has probability mu of corrupting
the copy — perturb one arg by +-1 or swap the op for a
random one. Neutral on payload content (copies cost the
same), but mutations shrinking n (cell 11 constant) make
shorter genomes: fewer copies per generation, faster
replication — and lose tail cells: payload first.

Verify-first prediction: mutation pressure + speed selection
=> n shrinks, payload dies, crystal reversion evolves.
"""
import random
import sys
sys.path.insert(0, 'esolang')
from worker import build
from migr import OPS

OPL = sorted(OPS)


def run_mut(tape, life, cap, size, mu, rng):
    cells = [[op, a1, a2, life] for op, a1, a2 in tape]
    cells += [['HALT', 0, 0, 0] for _ in range(size - len(cells))]
    stack, out, ip, steps = [], [], 0, 0
    while 0 <= ip < len(cells) and steps < cap:
        op, a1, a2, hp = cells[ip]
        if hp <= 0:
            ip += 1
            continue
        cells[ip][3] -= 1
        steps += 1
        cur = ip
        ip += 1
        if op == 'PUSH': stack.append(a1)
        elif op == 'ADD': stack.append(stack.pop() + stack.pop())
        elif op == 'SUB':
            a, b = stack.pop(), stack.pop(); stack.append(b - a)
        elif op == 'PRINT': out.append((cur, stack[-1] if stack else None))
        elif op == 'JMPR': ip = cur + a1
        elif op == 'JNZR': ip = cur + a1 if stack.pop() != 0 else ip
        elif op == 'JZR': ip = cur + a1 if stack.pop() == 0 else ip
        elif op in ('CPY', 'CPYR'):
            if op == 'CPY':
                dr = stack.pop(); sr = stack.pop()
            else:
                dr, sr = a2, a1
            src, dst = cur + sr, cur + dr
            if 0 <= src < len(cells) and 0 <= dst < len(cells):
                o, x1, x2, _h = cells[src]
                if rng.random() < mu:
                    which = rng.random()
                    if which < 0.5 and o in ('PUSH', 'JMPR', 'JNZR', 'JZR', 'CPYR'):
                        x1 += rng.choice((-1, 1))
                    else:
                        o = rng.choice(OPL)
                cells[dst] = [o, x1, x2, life]
        elif op == 'DUP': stack.append(stack[-1])
        elif op == 'DROP': stack.pop()
        elif op == 'SWAP': stack[-1], stack[-2] = stack[-2], stack[-1]
        elif op == 'HALT': break
    return steps, out, cells


def probe(cells, front):
    """Read the genome at the migration front — find the n
    constant (PUSH n right before SUB/JNZR tail) and payload."""
    seg = cells[max(0, front - 25):front + 5]
    return [(c[0], c[1]) for c in seg]


if __name__ == '__main__':
    base, n, D, pay0 = build()
    rng = random.Random(7)
    for mu in (0.0, 0.005, 0.02):
        rng = random.Random(7)
        steps, out, cells = run_mut(base, 30, 150000, 40000, mu, rng)
        # migration front = furthest alive cell
        alive = [i for i, c in enumerate(cells) if c[3] == 30][:0]  # placeholder
        front = max((i for i, c in enumerate(cells) if c[3] > 0), default=0)
        prints = len(out)
        tail = out[-3:] if out else []
        print(f'mu={mu}: steps {steps}, prints {prints}, front {front}')
        if prints:
            print(f'  print vals tail: {[v for _, v in tail]}')
        # read genome at front: scan back for the loop signature
        seg = cells[max(0, front - 22):front + 1]
        desc = ' '.join(f'{c[0][:3]}{c[1] if c[0] in ("PUSH","JMPR","JNZR") else ""}' for c in seg)
        print(f'  front genome: {desc}')
