"""flick.py — Flick: маленький язык (~150 строк).

Спека: целые числа, let x = expr, print expr,
if cond { stmts }, while cond { stmts }.
Комментарий: # до конца строки.

    let x = 10
    while x > 0 { print x; let x = x - 1 }

Лексер -> Pratt-парсер -> tree-walk интерпретатор.
"""

import re

KEYWORDS = {'let', 'print', 'if', 'while'}
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

    def expr(prec=0):
        t = eat()
        left = ('num', t[1]) if t[0] == 'num' else \
               ('var', t[1]) if t[0] == 'id' else \
               ('neg', expr(9)) if t[1] == '-' else err(t)
        PREC = {'==': 1, '!=': 1, '<': 2, '>': 2, '<=': 2, '>=': 2,
                '+': 3, '-': 3, '*': 4, '/': 4, '%': 4}
        while peek()[1] in PREC and PREC[peek()[1]] > prec:
            op = eat()[1]
            left = ('bin', op, left, expr(PREC[op]))
        if peek()[1] == ')':
            pass
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
            return (kw, cond, body)
        if t[1] == ';':
            eat()
            return stmt()
        return ('print', expr())

    out = []
    while pos[0] < len(toks):
        out.append(stmt())
    return out


def run(ast, env, out):
    def ev(e):
        k = e[0]
        if k == 'num':
            return e[1]
        if k == 'var':
            return env.get(e[1], 0)
        if k == 'neg':
            return -ev(e[1])
        op, a, b = e[1], ev(e[2]), ev(e[3])
        return {'+': a + b, '-': a - b, '*': a * b, '/': int(a / b),
                '%': a % b, '==': int(a == b), '!=': int(a != b),
                '<': int(a < b), '>': int(a > b),
                '<=': int(a <= b), '>=': int(a >= b)}[op]
    for s in ast:
        k = s[0]
        if k == 'let':
            env[s[1]] = ev(s[2])
        elif k == 'print':
            out.append(ev(s[1]))
        elif k == 'if':
            if ev(s[1]):
                run(s[2], env, out)
        elif k == 'while':
            while ev(s[1]):
                run(s[2], env, out)


def flick(src):
    env, out = {}, []
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
    let f0 = 0
    let f1 = 1
    let i = 0
    while i < 8 {                 # ряд фибоначчи
        print f1
        let t = f0 + f1
        let f0 = f1
        let f1 = t
        let i = i + 1
    }
    if fact > 100 { print 42 }
    '''
    res = flick(demo)
    print(' '.join(map(str, res)))
    expect = [120, 1, 1, 2, 3, 5, 8, 13, 21, 42]
    print('VERDICT:', 'OK' if res == expect else f'FAIL {res} vs {expect}')
