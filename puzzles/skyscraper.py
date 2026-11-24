"""skyscraper.py — skyscraper puzzle generator + uniqueness proof.

Puzzle genre #3 (nonogram, zebra, now skyscraper). An N×N
Latin square of building heights 1..N; edge clues count the
visible buildings looking in from that side (a building is
visible iff taller than everything before it).

The standing law — to pose is to prove uniqueness:
  1. plant a random Latin square (cyclic base + shuffled
     rows/cols/symbols preserves Latin-ness);
  2. compute all 4N clues;
  3. greedily drop clues while the solver still proves
     exactly one completion (same protocol as zebra.py:
     count solutions capped at 2).
"""

import itertools
import random

N = 5
PERMS = list(itertools.permutations(range(1, N + 1)))


def visible(seq):
    v, hi = 0, 0
    for x in seq:
        if x > hi:
            v += 1
            hi = x
    return v


def plant(rng):
    base = [[(r + c) % N + 1 for c in range(N)] for r in range(N)]
    rows = list(range(N)); rng.shuffle(rows)
    cols = list(range(N)); rng.shuffle(cols)
    syms = list(range(1, N + 1)); rng.shuffle(syms)
    return [[syms[base[rows[r]][cols[c]] - 1]
             for c in range(N)] for r in range(N)]


def clues_of(g):
    """(top, bottom, left, right) clue lists."""
    top = [visible(g[r][c] for r in range(N)) for c in range(N)]
    bot = [visible(g[r][c] for r in range(N - 1, -1, -1))
           for c in range(N)]
    left = [visible(g[r]) for r in range(N)]
    right = [visible(g[r][::-1]) for r in range(N)]
    return top, bot, left, right


def solve(top, bot, left, right, limit=2):
    """Backtrack row-by-row over clue-legal permutations;
    count solutions up to `limit`."""
    row_ok = []
    for r in range(N):
        cand = []
        for p in PERMS:
            if left[r] and visible(p) != left[r]:
                continue
            if right[r] and visible(p[::-1]) != right[r]:
                continue
            cand.append(p)
        row_ok.append(cand)

    sols, grid = [], []

    def fits(p, r):
        return all(grid[i][c] != p[c]
                   for i in range(r) for c in range(N))

    def bt(r):
        if len(sols) >= limit:
            return
        if r == N:
            for c in range(N):
                col = [grid[i][c] for i in range(N)]
                if top[c] and visible(col) != top[c]:
                    return
                if bot[c] and visible(col[::-1]) != bot[c]:
                    return
            sols.append(tuple(tuple(x) for x in grid))
            return
        for p in row_ok[r]:
            if fits(p, r):
                grid.append(p)
                bt(r + 1)
                grid.pop()

    bt(0)
    return sols


def minimize(top, bot, left, right, rng):
    """Drop clues while uniqueness survives. Clues are indexed
    (side, pos); side 0..3 = top/bottom/left/right."""
    allc = [(s, i) for s in range(4) for i in range(N)]
    rng.shuffle(allc)
    lists = [list(top), list(bot), list(left), list(right)]

    def get():
        return lists[0], lists[1], lists[2], lists[3]

    for s, i in allc:
        keep = lists[s][i]
        lists[s][i] = 0                     # clue removed
        if len(solve(*get())) != 1:
            lists[s][i] = keep              # still needed
    return get()


def render(grid, clues):
    top, bot, left, right = clues
    out = ['    ' + ' '.join(str(x or ' ') for x in top)]
    for r in range(N):
        out.append(f' {left[r] or " "}  ' +
                   ' '.join(map(str, grid[r])) +
                   f'  {right[r] or " "}')
    out.append('    ' + ' '.join(str(x or ' ') for x in bot))
    return '\n'.join(out)


def main():
    rng = random.Random(11)
    g = plant(rng)
    assert len(solve(*clues_of(g))) == 1          # sanity
    clues = minimize(*clues_of(g), rng)
    n_clues = sum(sum(1 for x in side if x) for side in clues)
    sols = solve(*clues)
    print(f'{n_clues} clues kept, solutions: {len(sols)}')
    print(render(g, clues))
    assert len(sols) == 1 and \
        [list(r) for r in sols[0]] == g
    print('VERDICT: OK — unique solution proven')


if __name__ == '__main__':
    main()
