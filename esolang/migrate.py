"""migrate.py — SENEX-M: escaping senescence by migration.

The no-immortality theorem binds a FIXED program: a program
that copies itself into fresh memory resets its wear. That
is the biological loophole: lineage immortality, somatic
death — germline is immortal, bodies die.

Dialect additions (relative args, self-copy safe):
  COPY s d   — cells[ip+d] = cells[ip+s]  (fresh hp)
  MJMP s d j — same, then ip += j          (migrate-jump)

SECOND SENEX THEOREM (found while designing this):
covering all T cells of the next generation needs T writes;
one execution writes at most one cell -> every executing
cell must spend its life copying. Any functional cell is a
mortality debt the copier cannot pay:
  IMMORTAL LINEAGE <=> STERILE LINEAGE.
Work can only ride on cells that die with the body.

Demo: pure replicator (all cells self-copy to +OFF) vs
workers (w cells replaced by PUSH/PRINT work ops).
"""

OPS = {'PUSH', 'ADD', 'SUB', 'PRINT', 'JZ', 'RENEW',
       'HALT', 'COPY', 'MJMP', 'NOP'}


def make_program(T, work_cells=0, off=None):
    """Program of T cells: every cell copies itself to +off,
    except the last (MJMP: copies + jumps) and the first
    `work_cells` cells (they do WORK instead of copying)."""
    off = off or T
    tape = [['COPY', (0, off), None] for _ in range(T)]
    tape[T - 1] = ['MJMP', (0, off, off), None]
    work = ['PUSH', 'PRINT', 'ADD', 'PRINT']  # count & show a tick
    for i in range(min(work_cells, len(work))):
        tape[i] = [work[i], (1,) if work[i] == 'PUSH' else (), None]
    return tape


def run_migrate(T, life=3, work_cells=0, buffers=6, max_gens=400):
    """Ring of `buffers` slots of size T. Returns generations
    survived + how many cells were alive at the last birth."""
    M = buffers * T
    cells = [['NOP', (), 0] for _ in range(M)]
    prog = make_program(T, work_cells, T)
    for i, (op, arg, _) in enumerate(prog):
        cells[i] = [op, arg, life]
    stack, out, ip, gen = [], [], 0, 0
    steps = 0
    while gen < max_gens and steps < 2_000_000:
        if not (0 <= ip < M):
            break
        op, arg, hp = cells[ip]
        ip += 1
        if hp <= 0 or op == 'NOP':
            continue
        cells[ip - 1][2] -= 1
        steps += 1
        if op == 'PUSH':
            stack.append(1)
        elif op == 'ADD':
            if len(stack) >= 2:
                stack.append(stack.pop() + stack.pop())
        elif op == 'PRINT':
            out.append(stack[-1] if stack else None)
        elif op == 'JZ':
            if stack.pop() == 0:
                ip += arg[0]
        elif op == 'COPY':
            s, d = arg
            src = cells[(ip - 1 + s) % M]
            cells[(ip - 1 + d) % M] = [src[0], src[1], life]
        elif op == 'MJMP':
            s, d, j = arg
            src = cells[(ip - 1 + s) % M]
            cells[(ip - 1 + d) % M] = [src[0], src[1], life]
            ip = (ip - 1 + j) % M
            gen += 1
            if not any(c[2] > 0 for c in cells):
                break
        elif op == 'HALT':
            break
    alive = sum(c[2] > 0 and c[0] != 'NOP' for c in cells)
    return gen, steps, alive, out


if __name__ == '__main__':
    print(f'{"work cells":>10} | {"gens":>5} | {"PRINTS(work)":>12} | '
          f'{"alive copier cells":>18}')
    print('-' * 60)
    for w in (0, 1, 2, 3):
        g, s, a, o = run_migrate(T=10, life=3, work_cells=w)
        print(f'{w:>10} | {g:>5} | {len(o):>12} | {a:>18}')
    print()
    print('lineages never die; WORK dies — every migrant sheds')
    print('its functional cells and finishes as a pure replicator')
