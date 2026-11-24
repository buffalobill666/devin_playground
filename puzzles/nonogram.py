"""nonogram.py — генератор нонограмм + солвер + проверка однозначности.

Ключи строк/столбцов не считаются нонограммой, пока солвер не
докажет, что решение ровно одно. Генератор тасует битмапы,
пока не попадётся однозначная.

Демо: генерирует 10x10 головоломку, печатает ключи, решает,
рендерит nonogram.png (лист задачи + решение).
"""

import itertools
import random


def clues_of(line):
    c, out = 0, []
    for v in line:
        if v:
            c += 1
        elif c:
            out.append(c)
            c = 0
    return out + ([c] if c else []) or [0]


def line_fits(clue, n):
    """Все расстановки блоков clue на линии длины n (списки 0/1)."""
    if clue == [0]:
        yield [0] * n
        return
    gaps = len(clue) - 1
    slack = n - sum(clue) - gaps
    for extra in itertools.combinations_with_replacement(
            range(len(clue) + 1), slack):
        pad = [0] * (len(clue) + 1)
        for p in extra:
            pad[p] += 1
        line = [0] * pad[0]
        for i, blk in enumerate(clue):
            line += [1] * blk
            line += [0] * (1 + pad[i + 1] if i < gaps else pad[-1])
        yield line[:n] + [0] * (n - len(line))


def line_deduce(clue, known, n):
    """Дедукция по линии: (новое_known, ок?) — known: -1/0/1."""
    acc = None
    for fit in line_fits(clue, n):
        if all(k == -1 or k == v for k, v in zip(known, fit)):
            if acc is None:
                acc = fit[:]
            else:
                acc = [a if a == b else -1 for a, b in zip(acc, fit)]
    if acc is None:
        return known, False
    return [k if k != -1 else a for k, a in zip(known, acc)], True


def solve(row_clues, col_clues, w, h, limit=2):
    """Количество решений (до limit) + первое решение."""
    solutions = []

    def dfs(grid):
        if len(solutions) >= limit:
            return
        changed = True
        g = [r[:] for r in grid]
        while changed:
            changed = False
            for i in range(h):
                nr, ok = line_deduce(row_clues[i], g[i], w)
                if not ok:
                    return
                if nr != g[i]:
                    g[i], changed = nr, True
            for j in range(w):
                col = [g[i][j] for i in range(h)]
                nc, ok = line_deduce(col_clues[j], col, h)
                if not ok:
                    return
                for i in range(h):
                    if g[i][j] != nc[i]:
                        g[i][j], changed = nc[i], True
        if all(v != -1 for r in g for v in r):
            solutions.append(g)
            return
        for i in range(h):
            for j in range(w):
                if g[i][j] == -1:
                    for v in (1, 0):
                        g2 = [r[:] for r in g]
                        g2[i][j] = v
                        dfs(g2)
                    return

    dfs([[-1] * w for _ in range(h)])
    return solutions


def gen_puzzle(w=10, h=10, density=0.45, rng=None, tries=200):
    rng = rng or random.Random()
    for _ in range(tries):
        grid = [[int(rng.random() < density) for _ in range(w)]
                for _ in range(h)]
        rows = [clues_of(r) for r in grid]
        cols = [clues_of([grid[i][j] for i in range(h)])
                for j in range(w)]
        sols = solve(rows, cols, w, h)
        if len(sols) == 1:
            return grid, rows, cols
    return None, None, None


def render(grid, rows, cols, path):
    import matplotlib.pyplot as plt
    w, h = len(grid[0]), len(grid)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.5))
    for ax, show_sol in ((ax1, False), (ax2, True)):
        ax.set_xlim(-max(map(len, cols)) - .5, w + .5)
        ax.set_ylim(h + .5, -max(map(len, rows)) - .5)
        ax.set_aspect('equal')
        ax.axis('off')
        for i in range(h + 1):
            ax.axhline(i, color='k', lw=2 if i % 5 == 0 else .5)
        for j in range(w + 1):
            ax.axvline(j, color='k', lw=2 if j % 5 == 0 else .5)
        for i, cl in enumerate(rows):
            for k, c in enumerate(reversed(cl)):
                ax.text(-.6 - k, i + .5, str(c), ha='center',
                        va='center', fontsize=9)
        for j, cl in enumerate(cols):
            for k, c in enumerate(reversed(cl)):
                ax.text(j + .5, -.6 - k, str(c), ha='center',
                        va='center', fontsize=9)
        if show_sol:
            for i in range(h):
                for j in range(w):
                    if grid[i][j]:
                        ax.add_patch(plt.Rectangle(
                            (j, i), 1, 1, fc='#222'))
    ax1.set_title('загадка')
    ax2.set_title('решение')
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    rng = random.Random(7)
    grid, rows, cols = gen_puzzle(rng=rng)
    if grid is None:
        print('не нашлось однозначной за 200 попыток')
        raise SystemExit
    print('Ключи строк:', rows)
    print('Ключи столбцов:', cols)
    sols = solve(rows, cols, 10, 10)
    ok = len(sols) == 1 and sols[0] == grid
    print('Решение:')
    for r in sols[0]:
        print(''.join('##' if v else '  ' for v in r))
    render(grid, rows, cols, 'puzzles/nonogram.png')
    print('VERDICT:', 'OK — решение единственное и совпадает'
          if ok else 'FAIL')
