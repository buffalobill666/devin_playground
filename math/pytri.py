"""pytri.py — proof without words: where Pythagorean triples live.

The gnomon of a k×k square — the one-cell L-strip needed to grow
it to (k+1)×(k+1) — holds exactly 2k+1 cells. When that number is
itself a square m², the L-strip repacks into an m×m square, and
m² + k² = (k+1)² is a Pythagorean triple. Every odd square gives
one: 9→(3,4,5), 25→(5,12,13), 49→(7,24,25), 81→(9,40,41).

Left panel: the 13² square, its gnomon (25 cells) picked out —
the strip that IS 5². Right panel: the same 25 cells as a 5×5
square. Nothing is proved in words; the cells do it.
"""

from PIL import Image, ImageDraw, ImageFont

CELL = 26
K, M = 12, 5          # the 5-12-13 triple: gnomon of 12² is 5²


def grid(dr, x0, y0, n, fill, edge=(70, 70, 78), hl=None):
    for y in range(n):
        for x in range(n):
            c = hl(x, y) if hl else fill
            dr.rectangle([x0 + x * CELL, y0 + y * CELL,
                          x0 + (x + 1) * CELL - 2,
                          y0 + (y + 1) * CELL - 2],
                         fill=c, outline=edge)


def main():
    W, H = 1120, 620
    img = Image.new('RGB', (W, H), (22, 22, 26))
    dr = ImageDraw.Draw(img)
    f = ImageFont.load_default(20)
    dark, strip, gnomon = (48, 52, 62), (215, 120, 70), (96, 165, 130)

    # left: (k+1)^2 square; last row+column = the gnomon, 2k+1 cells
    gx, gy = 70, 60
    grid(dr, gx, gy, K + 1, dark,
         hl=lambda x, y: gnomon if x == K or y == K else dark)
    dr.text((gx + (K + 1) * CELL // 2, gy + (K + 1) * CELL + 26),
            f'{(K+1)}·{(K+1)} = {K}·{K} + (2·{K}+1)', anchor='mm', font=f,
            fill=(200, 200, 200))
    dr.text((gx + (K + 1) * CELL // 2, gy + (K + 1) * CELL + 54),
            f'the L-strip holds {2*K+1} cells', anchor='mm', font=f,
            fill=(150, 150, 150))

    # arrow
    ax = gx + (K + 1) * CELL + 60
    ay = gy + (K + 1) * CELL // 2
    dr.line([ax, ay, ax + 80, ay], fill=(200, 180, 140), width=3)
    dr.polygon([(ax + 80, ay - 8), (ax + 80, ay + 8),
                (ax + 96, ay)], fill=(200, 180, 140))

    # right: same cells repacked as m×m
    rx = ax + 120
    ry = gy + (K + 1) * CELL // 2 - M * CELL // 2
    grid(dr, rx, ry, M, strip)
    dr.text((rx + M * CELL // 2, ry + M * CELL + 26),
            f'{M}·{M} = {M*M} cells - the same strip', anchor='mm',
            font=f, fill=(200, 200, 200))
    dr.text((rx + M * CELL // 2, ry + M * CELL + 54),
            f'{M}·{M} + {K}·{K} = {(K+1)}·{(K+1)}', anchor='mm', font=f,
            fill=(240, 210, 150))

    # the family line: which k give square gnomons
    triples = [(m, k, k + 1) for k in range(2, 200)
               for m in [int((2 * k + 1) ** 0.5)]
               if m * m == 2 * k + 1]
    dr.text((70, H - 66),
            'gnomon is square only at odd squares: ' +
            '  '.join(f'{m}-{k}-{k+1}' for m, k, _ in triples[:6]) +
            '  …', font=f, fill=(160, 160, 160))
    dr.text((70, H - 36),
            'every odd square is a gnomon, so every odd number '
            'owns exactly one triple', font=f, fill=(120, 120, 120))
    out = __file__.replace('.py', '.png')
    img.save(out)
    print('saved', out, '| triples found:', len(triples))


if __name__ == '__main__':
    main()
