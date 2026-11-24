"""subleq.py — OISC: компьютер с одной инструкцией.

subleq a b c : mem[b] -= mem[a]; если mem[b] <= 0 — goto c.
Всё. Этого достаточно для Тьюринг-полноты: сложение — два
вычитания через нулевую ячейку, безусловный прыжок — Z Z c,
останов — прыжок в -1.

Ассемблер с метками + машина. Демо: ACC = X * Y = 6 * 7
повторным сложением.
"""

PROG = """
loop:   Y   Z   s1      # Z = -Y
s1:     Z   ACC s2      # ACC += Y
s2:     Z   Z   s3      # Z = 0
s3:     ONE X   s4      # X -= 1
s4:     Z   X   done    # if X <= 0 -> done (X не меняется: X-=0)
        Z   Z   loop    # безусловно назад
done:   Z   Z   halt    # halt = -1
# данные
Z:      0
ONE:    1
X:      6
Y:      7
ACC:    0
"""


def assemble(src):
    """Строки 'a b c' (инструкция) или 'v' (ячейка данных)."""
    labels, cells = {}, []
    for line in src.split('\n'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        if ':' in line:
            name, rest = line.split(':')
            labels[name.strip()] = len(cells)
            line = rest.strip()
            if not line:
                continue
        cells += line.split()
    labels.setdefault('halt', -1)
    return [int(labels.get(t, t)) for t in cells]


def run(mem, cap=10000):
    ip, steps = 0, 0
    while ip >= 0 and steps < cap:
        a, b, c = mem[ip], mem[ip + 1], int(mem[ip + 2])
        mem[b] -= mem[a]
        ip = c if mem[b] <= 0 else ip + 3
        steps += 1
    return mem, steps


if __name__ == '__main__':
    mem = assemble(PROG)
    acc = len(mem) - 1              # ACC — последняя ячейка
    mem, steps = run(mem)
    print(f'шагов: {steps}, ACC = {mem[acc]}')
    print('VERDICT:', 'OK' if mem[acc] == 42
          else f'FAIL: {mem[acc]}')
