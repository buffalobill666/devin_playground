"""migrate2.py — SENEX-M2: the germline that rebuilds its soma.

migrate.py proved the second SENEX theorem: a migrating
lineage survives only if every cell spends its life copying
— IMMORTAL LINEAGE <=> STERILE LINEAGE. Work can only ride
on cells that die with the body.

But that theorem leaves a biological loophole unexplored:
the germline is sterile but it can *rebuild* workers each
generation. If copiers write a template that CONTAINS soma
code, every new body regrows fresh functional cells — work
happens in the soma, dies with it, and the lineage still
never dies. That is exactly how animals do it.

migrate.py couldn't express this: each cell holds one op
with static args — a copier can only ever write one fixed
(s,d) pair, so copiers can never cover the worker cells
(count them: workers consume write-budget without writing).
M2 dialect: args come off the STACK, so one small copier
ENGINE loops over the whole template:

  tape = [ soma code (w cells) ][ copier engine (~14 cells) ]
  engine loop: for i in 0..T-1: offspring[i] = template[i]
  then jump into the offspring — generation boundary.

Ops (stack-arg dialect):
  PUSH v | DUP | ADD | SUB | JZ rel | COPY (pops d,s —
  relative to the ENGINE's slot start, resolved here by
  absolute write into the offspring region) | HALT | PRINT.

Question: does per-generation work output stay constant
(soma regenerated) instead of dying out like migrate.py's
sterile shedding? Metric: PRINTs per generation.
"""

LIFE = 3


def make_program(soma_work=True):
    """Tape layout: [0..w-1 soma][w.. copier engine].
    Engine loops i=0..T-1 copying template[i] ->
    template[i]+T, where T = whole tape length (the
    offspring slot is exactly one body-length away)."""
    tape = []
    if soma_work:
        tape += [['PUSH', 1], ['PUSH', 1], ['ADD', ()],
                 ['PRINT', ()]]
    e = [['PUSH', 0],                     # 0: i = 0
         ['DUP', ()],                     # 1: loop head; i i
         ['DUP', ()],                     # 2: i i i
         ['PUSH', None], ['ADD', ()],     # 3-4: i i i+T
         ['COPY', ()],                    # 5: pops d=i+T, s=i -> [i]
         ['PUSH', 1], ['ADD', ()],        # 6-7: i+1
         ['DUP', ()], ['PUSH', None],     # 8-9: i+1 i+1 T
         ['SUB', ()],                     # 10: i+1 (i+1-T)
         ['JNZ', -11],                    # 11: nonzero -> index 1
         ['POPJ', None]]                  # 12: ip -> offspring
    tape += e
    T = len(tape)
    for cell in tape:
        if cell[1] is None or cell[1] == (None,):
            cell[1] = T
    return tape


def run(gens=40, max_steps=400_000):
    """cells: (op, arg, hp, hp0). hp0 = the blueprint's own
    lifespan, copied with the code — germline cells carry a
    BIG hp0 (they spend ~T*12 executions per body copying),
    soma cells carry small hp0 (mortal, die with the body).
    The sterility theorem is honoured: the germline's whole
    long life is spent copying; it does nothing else."""
    prog = make_program()
    w = len(prog)
    soma_end = 4                        # first 4 cells = soma
    eng_hp0 = w * 12 + 20               # engine spends a life
    M = (gens + 2) * w
    cells = [['NOP', (), 0, 0] for _ in range(M)]
    for i, (op, arg) in enumerate(prog):
        h = LIFE if i < soma_end else eng_hp0
        cells[i] = [op, arg, h, h]
    stack, out, ip = [], [], 0
    gen = 0
    steps = 0
    gen_marks = []
    while gen < gens and steps < max_steps:
        if not (0 <= ip < M):
            break
        op, arg, hp, hp0 = cells[ip]
        base = ip                       # executing cell pos
        ip += 1
        if hp <= 0 or op == 'NOP':
            continue
        cells[base][2] -= 1
        steps += 1
        if op == 'PUSH':
            stack.append(arg)
        elif op == 'DUP':
            stack.append(stack[-1])
        elif op == 'ADD':
            stack.append(stack.pop() + stack.pop())
        elif op == 'SUB':
            a = stack.pop()
            stack.append(stack.pop() - a)
        elif op == 'PRINT':
            out.append(stack[-1] if stack else 0)
        elif op == 'JNZ':
            if stack.pop() != 0:
                ip += arg
        elif op == 'COPY':
            d = stack.pop()
            s = stack.pop()
            # s,d are ABSOLUTE tape offsets produced by the
            # engine (i and i+T) relative to slot base.
            slot = (base // w) * w
            src = cells[slot + s]
            cells[slot + d] = [src[0], src[1], src[3], src[3]]
        elif op == 'POPJ':
            slot = (base // w) * w
            ip = slot + arg
            gen += 1
            gen_marks.append((gen, len(out)))
            stack.clear()
        elif op == 'HALT':
            break
    return gen, out, gen_marks


if __name__ == '__main__':
    g, out, marks = run()
    prints_per = [marks[i][1] - (marks[i - 1][1] if i else 0)
                  for i in range(len(marks))]
    print(f'generations: {g}, total PRINTs: {len(out)}')
    print('prints per generation (first 12):',
          prints_per[:12])
    const = len(set(prints_per[1:])) == 1
    print('VERDICT:', 'soma regenerates — work output '
          'constant per generation' if const and
          prints_per and prints_per[0] > 0 else
          'work output dies or is absent')
