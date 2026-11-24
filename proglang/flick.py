"""flick.py — Flick: маленький язык (~190 строк).

Спека: целые числа, let x = expr, print expr,
if cond { stmts }, while cond { stmts },
функции: let f = fn(a, b) { return expr } — замыкания,
рекурсия (имя видно через внешний env).
Комментарий: # до конца строки.

    let fib = fn(n) {
        if n < 2 { return n }
        return fib(n - 1) + fib(n - 2)
    }

Лексер -> Pratt-парсер -> tree-walk интерпретатор.
"""

import re

KEYWORDS = {'let', 'print', 'if', 'while', 'fn', 'return'}
TOKRE = re.compile(r'\s*(?:(\d+)|([A-Za-z_]\w*)|(==|!=|<=|>=)|(.))')


def tokenize(src):
    # комментарий — # до конца строки (строк в языке нет, стрипать безопасно)
    src = '\n'.join(line.split('#')[0] for line in src.split('\n'))
    for m in TOKRE.finditer(src):
        num, word, op2, ch = m.groups()
        if ch and ch.isspace():
            continue
        yield ('num', int(num)) if num else \
              ('kw' if word in KEYWORDS else 'id', word) if word else \
              ('op', op2 or ch)


def parse(toks):
    toks = list(toks)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else ('eof', '')

    def eat(expect=None):
        t = toks[pos[0]]
        pos[0] += 1
        if expect and t[1] != expect:
            raise SyntaxError(f'expected {expect}, got {t}')
        return t

    def block():
        eat('{')
        body = []
        while peek()[1] != '}':
            if peek()[1] == ';':
                eat()
                continue
            body.append(stmt())
            if peek()[1] == ';':
                eat()
        eat('}')
        return body

    def expr(prec=0):
        t = eat()
        if t[0] == 'num':
            left = ('num', t[1])
        elif t[0] == 'id':
            left = ('var', t[1])
        elif t[1] == '-':
            left = ('neg', expr(9))
        elif t[1] == '(':
            left = expr()
            eat(')')
        elif t[0] == 'kw' and t[1] == 'fn':
            eat('(')
            params = []
            while peek()[1] != ')':
                params.append(eat()[1])
                if peek()[1] == ',':
                    eat()
            eat(')')
            left = ('fn', params, block())
        else:
            err(t)
        PREC = {'==': 1, '!=': 1, '<': 2, '>': 2, '<=': 2, '>=': 2,
                '+': 3, '-': 3, '*': 4, '/': 4, '%': 4}
        while True:
            if peek()[1] == '(':                  # вызов, высший приоритет
                eat()
                args = []
                while peek()[1] != ')':
                    args.append(expr())
                    if peek()[1] == ',':
                        eat()
                eat(')')
                left = ('call', left, args)
            elif peek()[1] in PREC and PREC[peek()[1]] > prec:
                op = eat()[1]
                left = ('bin', op, left, expr(PREC[op]))
            else:
                break
        return left

    def err(t):
        raise SyntaxError(f'unexpected {t}')

    def stmt():
        t = peek()
        if t[0] == 'kw' and t[1] == 'let':
            eat()
            name = eat()[1]
            eat('=')
            return ('let', name, expr())
        if t[0] == 'kw' and t[1] == 'print':
            eat()
            return ('print', expr())
        if t[0] == 'kw' and t[1] in ('if', 'while'):
            kw = eat()[1]
            cond = expr()
            return (kw, cond, block())
        if t[0] == 'kw' and t[1] == 'return':
            eat()
            return ('ret', expr())
        if t[1] == ';':
            eat()
            return stmt()
        return ('print', expr())

    out = []
    while pos[0] < len(toks):
        out.append(stmt())
    return out


class Env(dict):
    """Окружение с родителем — лексический скоп замыканий."""

    def __init__(self, parent=None):
        self.parent = parent

    def lookup(self, k):
        e = self
        while e is not None:
            if k in e:
                return e[k]
            e = e.parent
        return 0

    def assign(self, k, v):
        """let: обновить ближайшую привязку, иначе создать локальную."""
        e = self
        while e is not None:
            if k in e:
                e[k] = v
                return
            e = e.parent
        self[k] = v


class _Ret(Exception):
    def __init__(self, v):
        self.v = v


def run(ast, env, out):
    def ev(e):
        k = e[0]
        if k == 'num':
            return e[1]
        if k == 'var':
            return env.lookup(e[1])
        if k == 'neg':
            return -ev(e[1])
        if k == 'fn':
            return ('closure', e[1], e[2], env)   # захват env по ссылке
        if k == 'call':
            f = ev(e[1])
            if f[0] != 'closure':
                raise TypeError('not a function')
            local = Env(f[3])
            for p, a in zip(f[1], e[2]):
                local[p] = ev(a)
            try:
                run(f[2], local, out)
            except _Ret as r:
                return r.v
            return 0
        op, a, b = e[1], ev(e[2]), ev(e[3])
        if op == '+':
            return a + b
        if op == '-':
            return a - b
        if op == '*':
            return a * b
        if op == '/':
            return int(a / b)
        if op == '%':
            return a % b
        if op == '==':
            return int(a == b)
        if op == '!=':
            return int(a != b)
        if op == '<':
            return int(a < b)
        if op == '>':
            return int(a > b)
        if op == '<=':
            return int(a <= b)
        if op == '>=':
            return int(a >= b)
    for s in ast:
        k = s[0]
        if k == 'let':
            env.assign(s[1], ev(s[2]))
        elif k == 'print':
            out.append(ev(s[1]))
        elif k == 'ret':
            raise _Ret(ev(s[1]))
        elif k == 'if':
            if ev(s[1]):
                run(s[2], env, out)
        elif k == 'while':
            while ev(s[1]):
                run(s[2], env, out)


def flick(src):
    env, out = Env(), []
    run(parse(tokenize(src)), env, out)
    return out


if __name__ == '__main__':
    demo = '''
    let n = 5
    let fact = 1
    while n > 1 {
        let fact = fact * n
        let n = n - 1
    }
    print fact                    # 120
    let fib = fn(n) {             # рекурсия + замыкание
        if n < 2 { return n }
        return fib(n - 1) + fib(n - 2)
    }
    print fib(10)                 # 55
    let add = fn(a) {             # каррирование
        return fn(b) { return a + b }
    }
    let add5 = add(5)
    print add5(37)                # 42
    let counter = fn() {          # замыкание захватывает env
        let c = 0
        return fn() {
            let c = c + 1
            return c
        }
    }
    let tick = counter()
    print tick()                  # 1
    print tick()                  # 2
    if fact > 100 { print 42 }
    '''
    res = flick(demo)
    print(' '.join(map(str, res)))
    expect = [120, 55, 42, 1, 2, 42]
    print('VERDICT:', 'OK' if res == expect else f'FAIL {res} vs {expect}')
