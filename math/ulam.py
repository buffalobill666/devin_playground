"""ulam.py — Ulam spiral: primes on a square spiral show
diagonal streaks — quadratic families that are prime-rich.

N x N spiral (1 at center, spiraling out), sieve of
Eratosthenes, render: prime = dark cell. Then the honest
measurement: are diagonal directions really denser? Score
prime density along both diagonal families and compare to
row/column density. Also score the famous polynomial
f(n) = n^2 + n + 41 against its neighbors along its spiral
direction — is Euler's polynomial visibly the best streak?

Output: math/ulam.png + density report.
"""

import math
from PIL import Image


def spiral_coords(n):
    """n^2 spiral: value -> (x,y). 1 at center; right,up,left,down."""
    coord = {1: (0, 0)}
    x = y = 0
    dx, dy = 1, 0
    seg, step, cnt = 1, 0, 0
    for v in range(2, n * n + 1):
        x += dx; y += dy; step += 1
        coord[v] = (x, y)
        if step == seg:
            step = 0; cnt += 1
            dx, dy = -dy, dx          # turn left
            if cnt % 2 == 0:
                seg += 1
    return coord


def sieve(m):
    p = bytearray([1]) * (m + 1)
    p[0:2] = b'\x00\x00'
    for i in range(2, int(m ** .5) + 1):
        if p[i]:
            p[i * i::i] = b'\x00' * ((len(p) - i * i - 1) // i + 1)
    return p


def render(n, primes, coord, path):
    img = Image.new('L', (n, n), 255)
    px = img.load()
    c = n // 2
    for v, (x, y) in coord.items():
        if primes[v]:
            px[c + x, c - y] = 0
    img.save(path)


def density(n, primes, coord):
    """Prime density along diagonals vs rows (same lengths)."""
    c = n // 2
    grid = {}
    for v, (x, y) in coord.items():
        grid[(x, y)] = 1 if primes[v] else 0
    def line(vals):
        vals = list(vals)
        return sum(vals) / len(vals)
    # density over the two main-diagonal families
    d_main = line(grid[(i, i)] for i in range(-c + 1, c))
    d_anti = line(grid[(i, -i)] for i in range(-c + 1, c))
    row = line(grid[(i, 0)] for i in range(-c + 1, c))
    col = line(grid[(0, i)] for i in range(-c + 1, c))
    return d_main, d_anti, row, col


def poly_score(n, primes, coord, a, b, cc, upto):
    """Density of primes among f(v)=v^2+a v+... restricted
    to values inside the spiral — compares quadratic families."""
    vals = [v * v + a * v + cc for v in range(upto)]
    inside = [p for p in vals if 0 < p <= n * n]
    if not inside:
        return 0, 0
    hits = sum(primes[p] for p in inside)
    return hits, len(inside)


if __name__ == '__main__':
    N = 201
    primes = sieve(N * N)
    coord = spiral_coords(N)
    render(N, primes, coord, 'ulam.png')
    d1, d2, dr, dc = density(N, primes, coord)
    print(f'density: main-diag {d1:.3f} anti-diag {d2:.3f} '
          f'row {dr:.3f} col {dc:.3f} '
          f'(global {sum(primes)/(N*N):.3f})')
    for name, a, cc in (("n^2+n+41", 1, 41), ("n^2+n+17", 1, 17),
                        ("n^2+n+11", 1, 11), ("n^2+n+29", 1, 29),
                        ("n^2-n+41", -1, 41)):
        h, m = poly_score(N, primes, coord, a, 0, cc, 400)
        print(f'{name}: {h}/{m} = {h/m:.2f} prime '
              f'inside spiral')
    ok = d1 > dr * 1.1 and d1 > dc * 1.1
    print('VERDICT:', 'OK — diagonals prime-rich' if ok
          else 'no diagonal bias')
