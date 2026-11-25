"""migr.py — MIGR: the migrating-program machine.

SENEX proved no immortality on a FIXED tape: repair coverage
always loses to the pigeonhole. But the theorem assumed the
organism stays where it is. Biology's actual answer is
migration — copy yourself into fresh substrate and abandon
the aging body. Can a program do that?

Machine: like SENEX, tape cells carry (op, a1, a2, hp);
executing a cell costs it 1 hp; at 0 it is a NOP forever.
Two differences, both forced by the problem:

  * relative addressing (JMPR/JZR/CPYR). ABSOLUTE-addressed
    organisms cannot migrate by verbatim copying — the copy
    would still point at the parent's coordinates. Position
    independence is the migration-enabling feature; this is
    already half the answer.
  * CPYR srel drel — copy the cell at (self+srel) to
    (self+drel), restoring the copy's hp to full. One op,
    one cell, one hp of the executer. No free range-copying:
    replication is paid cell by cell.

The immortality economy, derived not assumed: within one
generation every cell must execute its own copy BEFORE its
hp hits zero. hp = life per generation covers life-1 work
executions + 1 copy. Death of the parent is irrelevant —
the child is fresh. The only fatal failure is a cell that
burns out before replicating.

Demos:
  crystal  — uniform CPYR cells: the boring immortal
  worker   — interleaved payload prints while migrating
"""
OPS = {'PUSH', 'ADD', 'SUB', 'PRINT', 'JMPR', 'JZR', 'CPYR', 'HALT',
       'CPY', 'DUP', 'DROP', 'SWAP', 'JNZR'}


def assemble(src):
    labels, tape = {}, []
    for line in src.split('\n'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        if ':' in line:
            name, line = line.split(':', 1)
            labels[name.strip()] = len(tape)
            line = line.strip()
            if not line:
                continue
        p = line.split()
        a1 = p[1] if len(p) > 1 else 0
        a2 = p[2] if len(p) > 2 else 0
        tape.append((p[0], a1, a2))
    out = []
    for op, a1, a2 in tape:
        for a in (1, 2):
            v = (a1, a2)[a - 1]
            if isinstance(v, str) and not v.lstrip('-').isdigit():
                # label — store as OFFSET from this cell
                tgt = labels[v]
                cur = len(out)
                if a == 1:
                    a1 = tgt - cur
                else:
                    a2 = tgt - cur
            else:
                if a == 1:
                    a1 = int(a1)
                else:
                    a2 = int(a2)
        out.append((op, a1, a2))
    return out


def run(tape, life=3, cap=20000, size=2000, trace_mig=False):
    cells = [[op, a1, a2, life] for op, a1, a2 in tape]
    pad = size - len(cells)
    cells += [['HALT', 0, 0, 0] for _ in range(pad)]  # empty world
    stack, out, ip, steps = [], [], 0, 0
    migrations = 0
    max_ip = 0
    while 0 <= ip < len(cells) and steps < cap:
        op, a1, a2, hp = cells[ip]
        if hp <= 0:
            ip += 1
            continue
        cells[ip][3] -= 1
        steps += 1
        cur = ip
        ip += 1
        if op == 'PUSH':
            stack.append(a1)
        elif op == 'ADD':
            stack.append(stack.pop() + stack.pop())
        elif op == 'SUB':
            a, b = stack.pop(), stack.pop()
            stack.append(b - a)
        elif op == 'PRINT':
            out.append(stack[-1] if stack else None)
        elif op == 'JMPR':
            ip = cur + a1
        elif op == 'JZR':
            ip = cur + a1 if stack.pop() == 0 else ip
        elif op == 'CPYR':
            src, dst = cur + a1, cur + a2
            if 0 <= src < len(cells) and 0 <= dst < len(cells):
                o, x1, x2, _h = cells[src]
                cells[dst] = [o, x1, x2, life]
        elif op == 'CPY':
            # stack-driven: pop dst_rel then src_rel (both relative
            # to the executing cell) — the copy loop's workhorse
            dr = stack.pop()
            sr = stack.pop()
            src, dst = cur + sr, cur + dr
            if 0 <= src < len(cells) and 0 <= dst < len(cells):
                o, x1, x2, _h = cells[src]
                cells[dst] = [o, x1, x2, life]
        elif op == 'DUP':
            stack.append(stack[-1])
        elif op == 'DROP':
            stack.pop()
        elif op == 'SWAP':
            stack[-1], stack[-2] = stack[-2], stack[-1]
        elif op == 'JNZR':
            ip = cur + a1 if stack.pop() != 0 else ip
        elif op == 'HALT':
            break
        max_ip = max(max_ip, ip)
    # alive = program still executing at cap; extinction = ip
    # ran off or execution died inside dead cells
    return steps, out, max_ip


# --- demo 1: the crystal -------------------------------------
# every cell copies itself D forward; after the copying sweep,
# control jumps into the new generation. position-independent
# throughout. The boring immortal: no payload, pure replication.
D = 8
CRYSTAL = []
# cell 0 copies cell 0 -> +D, then falls through to cell 1 etc.
# last cell jumps control forward by D-(n-1) into the new copy.
N = 4
for i in range(N):
    # at cell i: copy self (srel 0) to self+D-i... careful:
    # srel/drel relative to EXECUTING cell. copy of cell i must
    # land at i+D: drel = D. srel = 0 (self).
    CRYSTAL.append('CPYR 0 %d' % D)
# after N cells, ip is at N; want to jump to cell D (= copy of 0)
# relative to cell N-1 executing JMPR at position N-1+1=N... jump
# target D, current ip after increment N+... encoded rel to cur:
# cur = N, target D -> a1 = D - N
CRYSTAL.append('JMPR %d' % (D - N))
CRYSTAL_SRC = '\n'.join(CRYSTAL)


# --- demo 2: the worker --------------------------------------
# payload: print 1 each generation (one work execution per
# generation per work cell — fits the life-1 budget at life 3).
# layout per cell: copier cells copy workers AND themselves.
# simplest honest layout: EVERY cell copies itself, workers
# additionally print. a worker executes twice per generation
# (print path + copy) — with life 3, budget holds (2 <= 2).
def worker_src(n_work, d):
    lines = []
    # block: n_work workers. each worker: PRINT (via push+print)
    # then copy self forward; copiers: copy self forward.
    # order per cell: work first, copy second — the immortality
    # tax ordering: replicate LAST, when work is done.
    total = n_work * 3 + 2   # per worker: PUSH,PRINT,CPYR; + CPYR,JMPR
    for i in range(n_work):
        lines.append('PUSH 1')
        lines.append('PRINT')
        lines.append('CPYR -2 %d' % (d - 2))   # copy the PUSH cell?
    return lines  # placeholder — see build() below


def build_worker(n_work, d):
    """Worker layout, assembled with explicit relative math.

    Per worker i at base b (3 cells): PUSH / PRINT / CPYR.
    The CPYR must copy all three cells — one op copies one
    cell, so each cell copies itself: PUSH copies PUSH,
    PRINT copies PRINT, CPYR copies CPYR. But PUSH can't copy!
    Reorder: every cell is a CPYR carrying its identity...
    trick: since ops are fixed per cell, a cell can only copy
    if it is itself a CPYR. Payload cells must be copied BY
    copier cells. Layout per worker unit (4 cells):
        PUSH 1        # work
        PRINT         # work
        CPYR -2 d     # copy the PUSH forward
        CPYR -2 d     # copy the PRINT forward  (executing cell
                      #  is the second CPYR; -2 points at PRINT? no—)
    Getting the offsets right is the whole game; see migr_demo.
    """
    raise NotImplementedError


if __name__ == '__main__':
    tape = assemble(CRYSTAL_SRC)
    steps, out, max_ip = run(tape, life=3, cap=300)
    print('crystal:', steps, 'steps, max_ip', max_ip,
          '— migrated' if max_ip > len(tape) else '— died in place')
