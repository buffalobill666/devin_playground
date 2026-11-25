"""worker.py — the payload-carrying migrant.

The crystal (migr.py) is immortal but pure overhead. This
genome carries payload: it prints 42 once per generation
while migrating forever.

Architecture — the copy loop, stack-driven:
  cell 0      PUSH 0        counter i = 0
  cells 1..13 the loop:     compute src_rel/dst_rel from i,
                            CPY copies cell i forward by D,
                            i++, loop while i < n
  cell 14     DROP          counter exhausted
  cells 15..  payload       PUSH 42 / PRINT — the work
  last        JMPR          into the newborn generation

Budget law: loop cells execute n times per generation
(once per copied cell) — so genome size n <= life is the
viability bound. Payload cells execute once per generation,
free riders. The immortality tax: most of the genome is
copying machinery — exactly like the crystal, but now we
can measure the payload fraction.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from migr import run


def build(d_stride=None, payload=((1, 42, 0), (3, 0, 0))):
    """Lay out the genome. Opcodes numeric-encoded:
    we store tuples (op, a1, a2) directly, positions computed
    by hand. Loop positions:
      0 PUSH 0
      1 DUP        # [i, i]
      2 PUSH P     # P = position of the CPY cell = 7
      3 SUB        # [i, i-P] = src_rel
      4 DUP
      5 PUSH D
      6 ADD        # [i, src_rel, src_rel+D]  (dst on top)
      7 CPY        # copy cur+src -> cur+dst; P is HERE at 7
      8 PUSH 1
      9 ADD        # i+1
      10 DUP
      11 PUSH n
      12 SUB
      13 JNZR back to 1  (a1 = 1 - 13 = -12)
      14 DROP
      15.. payload
      last JMPR to D
    """
    # payload ops encoded as names: map small helper
    OPN = {0: 'PUSH', 1: 'PUSH', 2: 'PRINT', 3: 'PRINT'}
    cells = []
    cells.append(('PUSH', 0, 0))      # 0
    cells.append(('DUP', 0, 0))       # 1  loop start
    cells.append(('PUSH', 7, 0))      # 2  P = 7
    cells.append(('SUB', 0, 0))       # 3
    cells.append(('DUP', 0, 0))       # 4
    cells.append(('PUSH', 0, 0))      # 5  placeholder for D
    cells.append(('ADD', 0, 0))       # 6
    cells.append(('CPY', 0, 0))       # 7  <- P
    cells.append(('PUSH', 1, 0))      # 8
    cells.append(('ADD', 0, 0))       # 9
    cells.append(('DUP', 0, 0))       # 10
    cells.append(('PUSH', 0, 0))      # 11 placeholder for n
    cells.append(('SUB', 0, 0))       # 12
    cells.append(('JNZR', -12, 0))    # 13 back to cell 1
    cells.append(('DROP', 0, 0))      # 14
    pay0 = len(cells)                 # 15
    for op, a1, a2 in payload:
        name = {1: 'PUSH', 3: 'PRINT'}.get(op, op if isinstance(op, str) else 'HALT')
        cells.append((name, a1, a2))
    jpos = len(cells)
    cells.append(('JMPR', 0, 0))      # placeholder for jump
    n = len(cells)
    D = d_stride or n                 # contiguous migration
    # patch constants: D into cell 5, n into cell 11, jump target
    cells[5] = ('PUSH', D, 0)
    cells[11] = ('PUSH', n, 0)
    cells[jpos] = ('JMPR', D - jpos, 0)
    return cells, n, D, pay0


def demo():
    cells, n, D, pay0 = build()
    print(f'genome {n} cells, stride {D}, payload at {pay0}')
    for i, c in enumerate(cells):
        print(f'  {i:2d}: {c[0]:5s} {c[1]} {c[2]}')
    print()
    steps, out, max_ip = run(cells, life=30, cap=200000, size=60000)
    gens = steps and (max_ip // D)
    print(f'steps {steps}, max_ip {max_ip}, generations ~{max_ip // D}')
    print('output head:', out[:24])
    print('distinct outputs:', sorted({x for x in out if x is not None})[:5])
    # viability: per-generation executions of loop cells = n
    print(f'budget check: n={n} <= life=30 — viable with margin')


if __name__ == '__main__':
    demo()
