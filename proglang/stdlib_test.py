"""stdlib_test.py — стандартная библиотека гоняется обоими бэкендами.

Дисциплина как у ядра: один и тот же исходник (stdlib.flk +
тестовая программа) исполняется tree-walk и VM, выводы должны
совпасть — и совпасть с ожиданием.
"""

import os
from flick import flick
from flickvm import flickvm

LIB = 'use "' + os.path.join(os.path.dirname(__file__),
                             'stdlib.flk') + '"\n'

TEST = '''
let xs = map(fn(x) { return x * x }, [1, 2, 3, 4])
print xs[0]
print xs[3]
let ys = filter(fn(x) { return x % 2 == 0 }, xs)
print len(ys)
print sum(xs)
print reverse(xs)[0]
print min(xs)
print max(xs)
'''

EXPECT = [1, 16, 2, 30, 16, 1, 16]

if __name__ == '__main__':
    src = LIB + TEST
    t, v = flick(src), flickvm(src)
    print('tree-walk:', t)
    print('stack-vm :', v)
    print('expect   :', EXPECT)
    ok = t == v == EXPECT
    print('VERDICT:', 'OK — stdlib portable' if ok else 'FAIL')
