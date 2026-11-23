"""island.py — процедурный остров: шум, море, реки, топонимика.

Шум — октавы интерполированных случайных сеток (numpy only).
Реки — спуск по градиенту с накоплением стока (толщина = сток).
Имена — слоговый генератор; города на побережье, вершины по
высоте.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

rng = np.random.default_rng()
N = 256


def octave_noise(n, cells):
    """Случайная сетка cells x cells, билинейно вздутая до n x n."""
    g = rng.random((cells + 1, cells + 1))
    ys = np.linspace(0, cells, n, endpoint=False)
    xs = np.linspace(0, cells, n, endpoint=False)
    yi, xi = ys.astype(int), xs.astype(int)
    yf, xf = (ys - yi)[:, None], (xs - xi)[None, :]
    a, b = g[yi][:, xi], g[yi][:, xi + 1]
    c, d = g[yi + 1][:, xi], g[yi + 1][:, xi + 1]
    t = yf * yf * (3 - 2 * yf)
    s = xf * xf * (3 - 2 * xf)
    return (a * (1 - s) + b * s) * (1 - t) + (c * (1 - s) + d * s) * t


def heightmap(n):
    h = sum(octave_noise(n, c) * w
            for c, w in [(8, 1.0), (16, 0.5), (32, 0.25), (64, 0.12)])
    h /= 1.87
    # радиальная маска — остров тонет к краям
    y, x = np.mgrid[0:n, 0:n]
    r = np.hypot(x - n / 2, y - n / 2) / (n / 2)
    h -= np.clip((r - 0.55) * 2.2, 0, 1)
    return np.clip(h, 0, 1)


def rivers(h, count=22):
    """Спуск по градиенту; сток утолщает русло."""
    n = h.shape[0]
    flow = np.zeros_like(h)
    ys, xs = np.where(h > 0.55)
    order = rng.permutation(len(ys))[:count]
    for k in order:
        y, x = ys[k], xs[k]
        for _ in range(4 * n):
            if h[y, x] < 0.42:
                break
            flow[y, x] += 1
            best, bh = (y, x), h[y, x]
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < n and 0 <= nx < n and h[ny, nx] < bh:
                        best, bh = (ny, nx), h[ny, nx]
            if best == (y, x):
                break
            y, x = best
    return flow


def name(rng, syll=3):
    v, c = list('aeiou'), list('bcdfghjklmnprstvwz')
    return ''.join(rng.choice(c) + rng.choice(v)
                   for _ in range(syll)).capitalize()


def render(h, flow, path):
    n = h.shape[0]
    img = np.zeros((n, n, 3), np.uint8)
    sea, beach = h < 0.42, (h >= 0.42) & (h < 0.46)
    low = (h >= 0.46) & (h < 0.6)
    mid = (h >= 0.6) & (h < 0.75)
    hi = (h >= 0.75) & (h < 0.88)
    img[sea] = (32, 61, 104)
    img[beach] = (222, 203, 152)
    img[low] = (87, 133, 76)
    img[mid] = (62, 105, 60)
    img[hi] = (112, 104, 90)
    img[h >= 0.88] = (232, 230, 224)
    # тень рельефа: разность с соседом справа-внизу
    shade = np.roll(h, (1, 1), (0, 1)) - h
    img = np.clip(img + (shade[:, :, None] * 160), 0, 255).astype(np.uint8)
    deep = h < 0.35
    img[deep] = (24, 46, 82)
    img[flow > 0] = (64, 108, 158)
    img[flow > 4] = (88, 138, 190)

    pil = Image.fromarray(img).resize((n * 3, n * 3), Image.NEAREST)
    dr = ImageDraw.Draw(pil)
    f = ImageFont.load_default()
    # города на побережье
    coast = np.argwhere(beach)
    for k in rng.permutation(len(coast))[:4]:
        y, x = coast[k]
        dr.text((x * 3 + 4, y * 3), name(rng), fill=(245, 240, 228), font=f)
        dr.point((x * 3, y * 3), fill=(245, 240, 228))
    # вершины
    peaks = np.argwhere(hi)
    if len(peaks):
        y, x = peaks[rng.integers(len(peaks))]
        dr.text((x * 3 + 4, y * 3), 'Mt ' + name(rng, 2),
                fill=(60, 55, 48), font=f)
    pil.save(path)
    return pil


if __name__ == '__main__':
    h = heightmap(N)
    f = rivers(h)
    render(h, f, 'maps/island.png')
    print('island rendered -> maps/island.png')
