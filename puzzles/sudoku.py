"""sudoku.py — четвёртый жанр: классическое судоку.

Тот же закон, что зебра, нонограмма и небоскрёбы доказали
трижды: загадать головоломку = ДОКАЗАТЬ единственность
решения, а не надеяться на неё.

Схема: полное решение строится перестановкой базового
паттерна (r*3 + r//3 + c) % 9 — сдвиг Латинского квадрата
по блокам — плюс перемешивание строк/бэндов/столбцов/
стеков и перемаркировка цифр. Подсказки снимаются
симметричными парами (поворот 180° сохраняет узор),
после каждой пары — проверка солвером: решений должно
быть ровно одно. Солвер — бэктрекинг с MRV.
"""

import random

rng = random.Random(20261124)
N, B = 9, 3


def solved():
    """Полная валидная сетка из перестановок базового паттерна."""
    base = [[(r * B + r // B + c) % N for c in range(N)]
            for r in range(N)]

    def perm(k):                       # перестановка внутри троек
        bands = [list(range(i * B, (i + 1) * B))
                 for i in range(k // B)]
        for band in bands:
            rng.shuffle(band)
        rng.shuffle(bands)
        return [x for band in bands for x in band]

    rows, cols = perm(N), perm(N)
    g = [[base[rows[r]][cols[c]] + 1 for c in range(N)]
         for r in range(N)]
    d = list(range(1, N + 1))
    rng.shuffle(d)
    return [[d[v - 1] for v in row] for row in g]


def candidates(g, r, c):
    used = set(g[r]) | {g[i][c] for i in range(N)} | \
        {g[i][j] for i in range(r // B * B, r // B * B + B)
         for j in range(c // B * B, c // B * B + B)}
    return [v for v in range(1, N + 1) if v not in used]


def solve(g, limit=2):
    """Число решений (стоп на limit). MRV — самая тесная клетка."""
    best, bc = None, None
    for r in range(N):
        for c in range(N):
            if g[r][c] == 0:
                cs = candidates(g, r, c)
                if bc is None or len(cs) < len(bc):
                    best, bc = (r, c), cs
    if best is None:
        return 1
    n = 0
    for v in bc:
        g[best[0]][best[1]] = v
        n += solve(g, limit)
        g[best[0]][best[1]] = 0
        if n >= limit:
            return n
    return n


def first_solution(g):
    """Первое решение как копия (или None) — для сверки с посевом."""
    for r in range(N):
        for c in range(N):
            if g[r][c] == 0:
                for v in candidates(g, r, c):
                    g[r][c] = v
                    res = first_solution(g)
                    if res:
                        return res
                    g[r][c] = 0
                return None
    return [row[:] for row in g]


def generate():
    """Решение -> снятие симметричных пар с доказательством."""
    sol = solved()
    g = [row[:] for row in sol]
    cells = [(r, c) for r in range(N) for c in range(N)]
    rng.shuffle(cells)
    removed = 0
    for r, c in cells:
        r2, c2 = N - 1 - r, N - 1 - c
        if g[r][c] == 0:
            continue
        a, b = g[r][c], g[r2][c2]
        g[r][c] = g[r2][c2] = 0
        if solve([row[:] for row in g]) != 1:
            g[r][c], g[r2][c2] = a, b
        else:
            removed += 1 if (r, c) == (r2, c2) else 2
    return g, sol, removed


def show(g):
    return '\n'.join(' '.join(str(v) or '·' for v in row[:3]) + ' | ' +
                     ' '.join(str(v) or '·' for v in row[3:6]) + ' | ' +
                     ' '.join(str(v) or '·' for v in row[6:])
                     for row in g[:3]) + '\n' + '- ' * 11 + '\n' + \
           '\n'.join(' '.join(str(v) or '·' for v in row[:3]) + ' | ' +
                     ' '.join(str(v) or '·' for v in row[3:6]) + ' | ' +
                     ' '.join(str(v) or '·' for v in row[6:])
                     for row in g[3:6]) + '\n' + '- ' * 11 + '\n' + \
           '\n'.join(' '.join(str(v) or '·' for v in row[:3]) + ' | ' +
                     ' '.join(str(v) or '·' for v in row[3:6]) + ' | ' +
                     ' '.join(str(v) or '·' for v in row[6:])
                     for row in g[6:])


if __name__ == '__main__':
    import time
    t = time.time()
    g, sol, removed = generate()
    clues = sum(v != 0 for row in g for v in row)
    print(f'подсказок: {clues} (снято {removed}); '
          f'{time.time() - t:.1f}s')
    print(show(g))
    check = [row[:] for row in g]
    n = solve(check)
    found = first_solution([row[:] for row in g])
    print('VERDICT:', 'OK — единственное решение, совпадает с посевом'
          if n == 1 and found == sol else f'FAIL (solutions={n})')
