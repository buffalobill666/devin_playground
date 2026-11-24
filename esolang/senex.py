"""senex.py — SENEX: язык, где программа стареет.

Каждая ячейка ленты содержит инструкцию и целостность.
Исполнение стоит клетке 1 жизнь; на нуле она — NOP навсегда.
RENEW восстанавливает чужую клетку — но сам стареет.

ТЕОРЕМА SENEX: вечной жизни нет. Чтобы клетка жила вечно,
ей нужен свой RENEW в цикле — но этот RENEW сам клетка и
тоже стареет; бесконечный регресс покрытия. Ремонт даёт
ОТСРОЧКУ, не бессмертие: слой обслуживания прогорает первым,
тело — через ещё один срок жизни.

Опс: PUSH n / ADD / SUB / PRINT / JMP a / JZ a / RENEW a / HALT
Демо: mortal (цикл без ремонта) vs cared (цикл + слой RENEW).
Вердикт: cared живёт ~2x дольше mortal; оба умирают.
"""

OPS = {'PUSH', 'ADD', 'SUB', 'PRINT', 'JMP', 'JZ', 'RENEW', 'HALT'}


def assemble(src):
    """Строки 'op [arg]' -> лента [(op, arg)]; метки 'name:'."""
    labels, tape = {}, []
    for line in src.split('\n'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        if ':' in line:                        # метка или 'l: op'
            name, line = line.split(':', 1)
            labels[name.strip()] = len(tape)
            line = line.strip()
            if not line:
                continue
        parts = line.split()
        try:
            arg = int(parts[1]) if len(parts) > 1 else None
        except ValueError:
            arg = parts[1]                     # метка — позже
        tape.append((parts[0], arg))
    return [(op, labels.get(str(arg), arg)) for op, arg in tape]


def run(tape, life=3, cap=2000):
    """Исполнение. Возвращает (шагов, вывод, умерла_ли_лента)."""
    cells = [[op, arg, life] for op, arg in tape]
    stack, out, ip, steps = [], [], 0, 0
    while 0 <= ip < len(cells) and steps < cap:
        op, arg, hp = cells[ip]
        ip += 1
        if hp <= 0 or op == 'NOP':
            continue
        cells[ip - 1][2] -= 1                # старение: платится всегда
        steps += 1
        if op == 'PUSH':
            stack.append(arg)
        elif op == 'ADD':
            stack.append(stack.pop() + stack.pop())
        elif op == 'SUB':
            a, b = stack.pop(), stack.pop()
            stack.append(b - a)
        elif op == 'PRINT':
            out.append(stack[-1])
        elif op == 'JMP':
            ip = arg
        elif op == 'JZ':
            ip = arg if stack.pop() == 0 else ip
        elif op == 'RENEW':
            cells[arg][2] = life
        elif op == 'HALT':
            break
    # смерть = программа остановилась без HALT: жизненно нужная
    # клетка прогорела и ip ушёл за край ленты
    dead = ip >= len(cells) or ip < 0
    return steps, out, dead


# mortal: чистый цикл — тело целиком платит жизнью каждый круг
MORTAL = """
      PUSH 0
loop: PUSH 1
      ADD
      PRINT
      JMP loop
"""

# cared: тот же цикл + слой RENEW на каждую клетку тела.
# Сами ремонтники не покрыты — прогорают первыми (life итераций),
# тело умирает следующим сроком.
CARED = """
      PUSH 0
loop: PUSH 1
      ADD
      PRINT
      RENEW 1
      RENEW 2
      RENEW 3
      RENEW 8
      JMP loop
"""


def lifespan(src, life):
    tape = assemble(src)
    steps, out, dead = run(tape, life=life)
    return steps, len(out), dead


if __name__ == '__main__':
    for life in (3, 5):
        s_m, n_m, d_m = lifespan(MORTAL, life)
        s_c, n_c, d_c = lifespan(CARED, life)
        print(f'life={life}: mortal {s_m} шагов ({n_m} выводов), '
              f'cared {s_c} шагов ({n_c} выводов)')
        assert d_m and d_c
        assert s_c > s_m * 1.5
    print('VERDICT: OK — ремонт отсрочил смерть, не отменил')
