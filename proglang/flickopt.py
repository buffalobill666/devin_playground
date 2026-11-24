"""flickopt.py — peephole optimizer for the Flick bytecode.

Three passes over compile_ast output:
  1. const fold  — CONST a; CONST b; OP s -> CONST (a s b)
  2. dead code   — unreachable after RET/JMP until a jump target
  3. jump threading — JMP/JZ pointing at a JMP get retargeted

Honest metric: count EXECUTED instructions in an instrumented
run, not just code size — dead code removal shrinks the file,
folding shrinks the trace.
"""

from flick import tokenize, parse, BUILTINS
from flickvm import compile_ast, BIN, Env


def _const_fold(code):
    """CONST a; CONST b; OP s -> CONST (a s b); NOP; NOP.
    NOPs keep every index stable — jump remap happens in _sweep."""
    out = []
    for ins in code:
        if (ins[0] == 'OP' and len(out) >= 2
                and out[-2][0] == 'CONST' and out[-1][0] == 'CONST'):
            a = out[-2][1]; b = out[-1][1]
            try:
                v = BIN[ins[1]](a, b)
            except Exception:
                out.append(ins)  # div by zero — keep runtime path
                continue
            out[-2] = ('CONST', v)
            out[-1] = ('NOP',)
            out.append(('NOP',))
            continue
        out.append(ins)
    return out


def _sweep(code):
    """Renumber: build live-only code, remap jump targets.
    Instruction i is live if reachable — conservative sweep:
    everything after HALT/RET/JMP until the next jump target."""
    targets = {a for ins in code for a in ins[1:]
               if ins[0] in ('JMP', 'JZ') and isinstance(a, int)}
    live = [ins[0] != 'NOP' for ins in code]
    dead = False
    for i, ins in enumerate(code):
        if i in targets:
            dead = False
        if dead:
            live[i] = False
        elif ins[0] in ('RET', 'JMP', 'HALT'):
            dead = True
    remap = {}
    ni = 0
    for i, l in enumerate(live):
        if l:
            remap[i] = ni
            ni += 1
    out = []
    for i, l in enumerate(live):
        if not l:
            continue
        ins = list(code[i])
        for k in range(1, len(ins)):
            if ins[0] in ('JMP', 'JZ') and isinstance(ins[k], int):
                ins[k] = remap[ins[k]]
        out.append(tuple(ins))
    return out


def _thread(code):
    """JMP/JZ -> JMP target: chase the chain to the real address."""
    def chase(a):
        seen = set()
        while a < len(code) and code[a][0] == 'JMP' and a not in seen:
            seen.add(a)
            a = code[a][1]
        return a
    return tuple((ins[0], chase(ins[1])) if ins[0] in ('JMP', 'JZ')
                 else ins for ins in code)


def optimize(code):
    prev = None
    while prev != code:           # iterate to a fixpoint
        prev = code
        code = _sweep(_thread(_sweep(_const_fold(code))))
    return code


def run_counted(code, funcs, env=None):
    """run() with an executed-instruction counter -> (out, steps)."""
    env = env or Env()
    stack, frames, out = [], [], []
    ip, steps = 0, 0
    while ip < len(code):
        ins, *arg = code[ip]
        ip += 1; steps += 1
        if ins == 'CONST': stack.append(arg[0])
        elif ins == 'LOAD': stack.append(env.lookup(arg[0]))
        elif ins == 'STORE': env.assign(arg[0], stack.pop())
        elif ins == 'NEG': stack.append(-stack.pop())
        elif ins == 'OP':
            b, a = stack.pop(), stack.pop(); stack.append(BIN[arg[0]](a, b))
        elif ins == 'ARR':
            stack.append([stack.pop() for _ in range(arg[0])][::-1])
        elif ins == 'IDX':
            ix, a = stack.pop(), stack.pop(); stack.append(a[int(ix)])
        elif ins == 'SET':
            v, ix = stack.pop(), stack.pop()
            env.lookup(arg[0])[int(ix)] = v
        elif ins == 'BUILTIN':
            args = [stack.pop() for _ in range(arg[1])][::-1]
            stack.append(BUILTINS[arg[0]](*args))
        elif ins == 'PRINT': out.append(stack.pop())
        elif ins == 'JMP': ip = arg[0]
        elif ins == 'JZ':
            if stack.pop() == 0: ip = arg[0]
        elif ins == 'MAKEFN':
            params, fcode = funcs[arg[0]]
            stack.append(('fn', params, fcode, env))
        elif ins == 'CALL':
            args = [stack.pop() for _ in range(arg[0])][::-1]
            f = stack.pop()
            frames.append((ip, env, code))
            local = Env(f[3])
            for p, a in zip(f[1], args): local[p] = a
            env, code, ip = local, f[2], 0
        elif ins == 'RET':
            v = stack.pop()
            ip, env, code = frames.pop()
            stack.append(v)
        elif ins == 'HALT': break
    return out, steps


from flickvm import DEMO

OPTDEMO = '''
print 2 + 3 * 4
let f = fn(x) {
    if x > 0 { return x; print 999 }
    return 0
}
print f(7)
let i = 0
while i < 3 { let i = i + 1 }
print i
'''

if __name__ == '__main__':
    for label, src in (('DEMO (real program)', DEMO),
                       ('OPTDEMO (patterns)', OPTDEMO)):
        ast = parse(tokenize(src))
        raw, funcs = compile_ast(ast)
        opt = optimize(raw)
        ofuncs = [(p, optimize(fc)) for p, fc in funcs]
        out_r, st_r = run_counted(raw, funcs)
        out_o, st_o = run_counted(opt, ofuncs)
        sz_r = len(raw) + sum(len(fc) for _, fc in funcs)
        sz_o = len(opt) + sum(len(fc) for _, fc in ofuncs)
        print(f'--- {label} ---')
        print('output   :', out_r, '==', out_o, '->', out_r == out_o)
        print('size     :', sz_r, '->', sz_o)
        print('executed :', st_r, '->', st_o,
              f'({100 * (1 - st_o / st_r):+.1f}%)')
