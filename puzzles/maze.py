"""maze.py — mazes with character.

Different generators = different personalities, visible at
a glance:
  backtracker — deep-first carving: long corridors, few
    junctions, the maze "hurries" forward
  wilson — loop-erased random walks to the tree: uniform
    spanning tree (same distribution as Aldous-Broder,
    orders faster), texture like lichen
  prim — frontier-front growth: bushy, many short dead ends

Plus BFS solver + a comparison sheet: three mazes side by
side with corridor stats (mean corridor run, junction %,
dead-end %) — character measured, not just seen.
"""

import random
from collections import deque

import numpy as np
from PIL import Image

W, H = 31, 21  # cells (odd)


def blank(w, h):
    return np.ones((h * 2 + 1, w * 2 + 1), bool)  # True = wall


def backtracker(w, h, rng):
    m = blank(w, h)
    stack = [(1, 1)]  # cells live on ODD coordinates
    m[1, 1] = False
    while stack:
        y, x = stack[-1]
        nbrs = [(y + dy * 2, x + dx * 2, y + dy, x + dx)
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 < y + dy * 2 <= h * 2 - 1
                and 0 < x + dx * 2 <= w * 2 - 1
                and m[y + dy * 2, x + dx * 2]]
        if not nbrs:
            stack.pop()
            continue
        ny, nx, wy, wx = nbrs[rng.randrange(len(nbrs))]
        m[wy, wx] = m[ny, nx] = False
        stack.append((ny, nx))
    return m


def wilson(w, h, rng):
    """Uniform spanning tree via loop-erased random walks."""
    m = blank(w, h)
    cells = [(y, x) for y in range(1, h * 2, 2)
             for x in range(1, w * 2, 2)]
    intree = {cells[0]}
    m[cells[0]] = False
    DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for start in cells:
        if start in intree:
            continue
        path = [start]
        pos = {start: 0}
        y, x = start
        while (y, x) not in intree:
            dy, dx = DIRS[rng.randrange(4)]
            ny, nx = y + dy * 2, x + dx * 2
            if not (0 < ny <= h * 2 - 1 and 0 < nx <= w * 2 - 1):
                continue
            if (ny, nx) in pos:          # loop: erase to revisit
                k = pos[(ny, nx)]
                for c in path[k + 1:]:
                    del pos[c]
                path = path[:k + 1]
            else:
                pos[(ny, nx)] = len(path)
                path.append((ny, nx))
            y, x = ny, nx
        for i in range(len(path) - 1):
            (y1, x1), (y2, x2) = path[i], path[i + 1]
            m[y1, x1] = m[(y1 + y2) // 2, (x1 + x2) // 2] = False
            intree.add((y1, x1))
        intree.add(path[-1])
    m[path[-1]] = False
    intree.add(path[-1])
    return m


def prim(w, h, rng):
    """Frontier of EDGES: pop (wall, cell-to-open); if the cell
    is still closed, open both and push its closed neighbours."""
    m = blank(w, h)
    m[1, 1] = False
    DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
    front = [(1 + DIRS[k][0], 1 + DIRS[k][1],
              1 + DIRS[k][0] * 2, 1 + DIRS[k][1] * 2)
             for k in range(4)]
    while front:
        wy, wx, cy, cx = front.pop(rng.randrange(len(front)))
        if not (0 < cy <= h * 2 - 1 and 0 < cx <= w * 2 - 1) \
                or not m[cy, cx]:
            continue
        m[wy, wx] = m[cy, cx] = False
        for dy, dx in DIRS:
            ny, nx = cy + dy * 2, cx + dx * 2
            if 0 < ny <= h * 2 - 1 and 0 < nx <= w * 2 - 1 \
                    and m[ny, nx]:
                front.append((cy + dy, cx + dx, ny, nx))
    return m


def solve(m):
    h, w = m.shape
    dist = np.full((h, w), -1, np.int32)
    dist[1, 1] = 0
    q = deque([(1, 1)])
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not m[ny, nx] \
                    and dist[ny, nx] < 0:
                dist[ny, nx] = dist[y, x] + 1
                q.append((ny, nx))
    if dist[h - 2, w - 2] < 0:
        return -1, set()          # exit unreachable
    path = set()
    y, x = h - 2, w - 2
    while (y, x) != (1, 1):
        path.add((y, x))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if dist[y + dy, x + dx] == dist[y, x] - 1:
                y, x = y + dy, x + dx
                break
    return dist[h - 2, w - 2], path


def character(m):
    """Measure the personality: corridor runs, junctions, dead ends."""
    open_ = ~m
    runs, junctions, deads = 0, 0, 0
    for y in range(1, m.shape[0] - 1):
        for x in range(1, m.shape[1] - 1):
            if not open_[y, x]:
                continue
            n = sum(open_[y + dy, x + dx]
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if n >= 3:
                junctions += 1
            elif n == 1:
                deads += 1
    # mean straight corridor run
    total, cnt = 0, 0
    for y in range(1, m.shape[0] - 1, 2):
        x = 1
        while x < m.shape[1] - 1:
            if open_[y, x]:
                s = x
                while x < m.shape[1] - 1 and open_[y, x]:
                    x += 1
                total += (x - s) // 2
                cnt += 1
            x += 1
    return total / max(cnt, 1), junctions, deads


def tile(m, path, scale=8):
    img = np.full((*m.shape, 3), 245, np.uint8)
    img[m] = (40, 38, 45)
    for y, x in path:
        img[y, x] = (200, 60, 60)
    img[1, 1] = img[-2, -2] = (60, 160, 90)
    return np.kron(img, np.ones((scale, scale, 1), np.uint8))


if __name__ == '__main__':
    rng = random.Random(11)
    gens = [('backtracker', backtracker), ('wilson', wilson),
            ('prim', prim)]
    tiles, report = [], []
    for name, g in gens:
        m = g(W, H, rng)
        d, path = solve(m)
        run, jn, dd = character(m)
        tiles.append(tile(m, path))
        report.append((name, d, run, jn, dd))
        print(f'{name:<14} path={d:>4} corridor={run:5.2f} '
              f'junctions={jn:>3} dead-ends={dd:>3}')
    sheet = np.concatenate([np.concatenate(
        [t, np.full((t.shape[0], 6, 3), 255, np.uint8)], axis=1)
        for t in tiles[:-1]] + [tiles[-1]], axis=1)
    Image.fromarray(sheet).save('puzzles/maze-chars.png')
    print('-> puzzles/maze-chars.png')
