"""flickvm.py — Flick bytecode backend: AST -> stack VM.

Second backend for the language (first: tree-walk in flick.py).
Same front-end (tokenize+parse), different execution model:
compiler emits a flat instruction list, VM runs a value stack
plus call frames. Closures stay env-objects — the VM is a
stack machine for expressions and control flow, not for scope.

ISA:
  CONST v / LOAD n / STORE n / NEG / OP sym
  JMP a / JZ a / CALL n / RET / PRINT / MAKEFN k / HALT

Closure value: ('fn', params, code, captured_env).
"""

from flick import tokenize, parse, BUILTINS, Env, _Ret


def compile_ast(ast, funcs=None):
    """AST -> (code, funcs). funcs — table of compiled bodies,
    SHARED across nested fn bodies so MAKEFN indices stay
    in one namespace (each call still emits its own code list)."""
    funcs = [] if funcs is None else funcs
    code = []

    def emit(*ins):
        code.append(ins)
        return len(code) - 1

    def expr(e):
        k = e[0]
        if k == 'num':
            emit('CONST', e[1])
        elif k == 'str':
            emit('CONST', e[1])
        elif k == 'arr':
            for x in e[1]:
                expr(x)
            emit('ARR', len(e[1]))
        elif k == 'idx':
            expr(e[1])
            expr(e[2])
            emit('IDX')
        elif k == 'var':
            emit('LOAD', e[1])
        elif k == 'neg':
            expr(e[1])
            emit('NEG')
        elif k == 'bin':
            expr(e[2])
            expr(e[3])
            emit('OP', e[1])
        elif k == 'fn':
            funcs.append((e[1], compile_ast(e[2], funcs)[0]))
            emit('MAKEFN', len(funcs) - 1)
        elif k == 'call':
            name = e[1][1] if e[1][0] == 'var' else ''
            if name in BUILTINS:
                for a in e[2]:
                    expr(a)
                emit('BUILTIN', name, len(e[2]))
            else:
                expr(e[1])
                for a in e[2]:
                    expr(a)
                emit('CALL', len(e[2]))

    def stmt(s):
        k = s[0]
        if k == 'let':
            expr(s[2])
            emit('STORE', s[1])
        elif k == 'set':
            expr(s[2])
            expr(s[3])
            emit('SET', s[1])
        elif k == 'print':
            expr(s[1])
            emit('PRINT')
        elif k == 'ret':
            expr(s[1])
            emit('RET')
        elif k == 'if':
            expr(s[1])
            jz = emit('JZ', None)
            for x in s[2]:
                stmt(x)
            code[jz] = ('JZ', len(code))
        elif k == 'while':
            top = len(code)
            expr(s[1])
            jz = emit('JZ', None)
            for x in s[2]:
                stmt(x)
            emit('JMP', top)
            code[jz] = ('JZ', len(code))

    for s in ast:
        stmt(s)
    emit('HALT')
    return code, funcs


BIN = {'+': lambda a, b: a + b, '-': lambda a, b: a - b,
       '*': lambda a, b: a * b, '/': lambda a, b: int(a / b),
       '%': lambda a, b: a % b,
       '==': lambda a, b: int(a == b), '!=': lambda a, b: int(a != b),
       '<': lambda a, b: int(a < b), '>': lambda a, b: int(a > b),
       '<=': lambda a, b: int(a <= b), '>=': lambda a, b: int(a >= b)}


def run(code, funcs, env=None):
    env = env or Env()
    stack, frames, out = [], [], []
    ip = 0
    while ip < len(code):
        ins, *arg = code[ip]
        ip += 1
        if ins == 'CONST':
            stack.append(arg[0])
        elif ins == 'LOAD':
            stack.append(env.lookup(arg[0]))
        elif ins == 'STORE':
            env.assign(arg[0], stack.pop())
        elif ins == 'NEG':
            stack.append(-stack.pop())
        elif ins == 'OP':
            b, a = stack.pop(), stack.pop()
            stack.append(BIN[arg[0]](a, b))
        elif ins == 'ARR':
            stack.append([stack.pop() for _ in range(arg[0])][::-1])
        elif ins == 'IDX':
            ix, a = stack.pop(), stack.pop()
            stack.append(a[int(ix)])
        elif ins == 'SET':
            v, ix = stack.pop(), stack.pop()
            env.lookup(arg[0])[int(ix)] = v
        elif ins == 'BUILTIN':
            args = [stack.pop() for _ in range(arg[1])][::-1]
            stack.append(BUILTINS[arg[0]](*args))
        elif ins == 'PRINT':
            out.append(stack.pop())
        elif ins == 'JMP':
            ip = arg[0]
        elif ins == 'JZ':
            if stack.pop() == 0:
                ip = arg[0]
        elif ins == 'MAKEFN':
            params, fcode = funcs[arg[0]]
            stack.append(('fn', params, fcode, env))
        elif ins == 'CALL':
            args = [stack.pop() for _ in range(arg[0])][::-1]
            f = stack.pop()
            if f[0] != 'fn':
                raise TypeError('not a function')
            frames.append((ip, env, code))
            local = Env(f[3])
            for p, a in zip(f[1], args):
                local[p] = a
            env, code, ip = local, f[2], 0
        elif ins == 'RET':
            v = stack.pop()
            ip, env, code = frames.pop()
            stack.append(v)
        elif ins == 'HALT':
            break
    return out


def flickvm(src):
    ast = parse(tokenize(src))
    code, funcs = compile_ast(ast)
    return run(code, funcs)


DEMO = '''
let n = 5
let fact = 1
while n > 1 { let fact = fact * n; let n = n - 1 }
print fact
let fib = fn(n) {
    if n < 2 { return n }
    return fib(n - 1) + fib(n - 2)
}
print fib(10)
let add = fn(a) { return fn(b) { return a + b } }
let add5 = add(5)
print add5(37)
print "fli" + "ck"
let a = [10, 20, 30]
print a[1]
let a[0] = 99
print a[0]
print len(a)
'''

if __name__ == '__main__':
    from flick import flick
    ref = flick(DEMO)
    got = flickvm(DEMO)
    print('tree-walk:', ref)
    print('stack-vm :', got)
    print('VERDICT:', 'OK — backends agree' if ref == got else 'FAIL')
