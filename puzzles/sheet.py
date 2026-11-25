"""sheet.py — a puzzle sheet for a HUMAN solver.

The playground's puzzles were built to prove uniqueness to
machines. This renders them for the other direction: one page,
three genres, pencil-ready. Host plays; solver already knows.
"""
import sys
sys.path.insert(0, 'puzzles')
from PIL import Image, ImageDraw, ImageFont

import sudoku
import nonogram
import random

CELL = 34
W, H = 1000, 760
im = Image.new('RGB', (W, H), (252, 250, 244))
dr = ImageDraw.Draw(im)

def font(sz):
    for path in ('C:/Windows/Fonts/consola.ttf', 'C:/Windows/Fonts/cour.ttf'):
        try:
            return ImageFont.truetype(path, sz)
        except Exception:
            pass
    return ImageFont.load_default()

F = font(20)
FB = font(24)
FT = font(15)

def text(x, y, s, f=F, fill=(30, 30, 40), center=None):
    if center is not None:
        bb = dr.textbbox((0, 0), s, font=f)
        x = center - (bb[2] - bb[0]) / 2
    dr.text((x, y), s, font=f, fill=fill)

# ---------- sudoku (left) ----------
g, sol, removed = sudoku.generate()
x0, y0 = 40, 108
dr.rectangle((x0 - 4, y0 - 4, x0 + 9 * CELL + 4, y0 + 9 * CELL + 4), fill=(255, 255, 255))
for i in range(10):
    lw = 3 if i % 3 == 0 else 1
    dr.line((x0 + i * CELL, y0, x0 + i * CELL, y0 + 9 * CELL), fill=(20, 20, 30), width=lw)
    dr.line((x0, y0 + i * CELL, x0 + 9 * CELL, y0 + i * CELL), fill=(20, 20, 30), width=lw)
for r in range(9):
    for c in range(9):
        if g[r][c]:
            text(0, y0 + r * CELL + 5, str(g[r][c]), f=FB,
                 center=x0 + c * CELL + CELL / 2)
text(x0, y0 - 32, 'SUDOKU — fill 1-9, each row/col/box once', f=FT)

# ---------- nonogram (right) ----------
rng = random.Random(11)
grid, rows, cols = nonogram.gen_puzzle(w=10, h=10, density=0.45, rng=rng)
NC = 26
nx, ny = 480, 175
maxr = max(len(r) for r in rows)
maxc = max(len(c) for c in cols)
dr.rectangle((nx - maxr * 18 - 4, ny - maxc * 18 - 4,
              nx + 10 * NC + 4, ny + 10 * NC + 4), fill=(255, 255, 255))
for j, cl in enumerate(cols):
    for k, v in enumerate(reversed(cl)):
        text(0, ny - (k + 1) * 18, str(v), f=FT,
             center=nx + j * NC + NC / 2)
for i, cl in enumerate(rows):
    for k, v in enumerate(reversed(cl)):
        text(nx - (k + 1) * 18, ny + i * NC + 4, str(v), f=FT)
for i in range(11):
    lw = 2 if i % 5 == 0 else 1
    dr.line((nx + i * NC, ny, nx + i * NC, ny + 10 * NC), fill=(20, 20, 30), width=lw)
    dr.line((nx, ny + i * NC, nx + 10 * NC, ny + i * NC), fill=(20, 20, 30), width=lw)
text(nx - maxr * 18, ny - maxc * 18 - 28, 'NONOGRAM — fill runs, clues are block lengths', f=FT)

# ---------- kakuro (bottom left) ----------
sys.path.insert(0, '.')
from puzzles.kakuro import generate as kgen
res = kgen()
if res:
    white, runs, sums, KW, KH, fill, att = res
    KC = 44
    kx, ky = 60, 500
    for y in range(KH):
        for x in range(KW):
            cx, cy = kx + x * KC, ky + y * KC
            if white[y][x]:
                dr.rectangle((cx, cy, cx + KC, cy + KC), fill=(255, 255, 255), outline=(20, 20, 30), width=2)
            else:
                dr.rectangle((cx, cy, cx + KC, cy + KC), fill=(235, 232, 224), outline=(150, 148, 140))
    # clues: label each run start. across sums at left of run, down sums above.
    idx = 0
    for kind, ri, cellspec in runs:
        cellspec = sorted(cellspec)
        fy, fx = cellspec[0]
        cx, cy = kx + fx * KC, ky + fy * KC
        s = sums[idx]
        idx += 1
        if kind == 'A':
            text(cx - KC + 4, cy + 3, str(s), f=FT, fill=(120, 60, 30))
        else:
            text(cx + 4, cy - KC + 3, str(s), f=FT, fill=(30, 60, 120))
    text(kx, ky - 28, f'KAKURO — digits 1-9 sum to clues, no repeat in a run  (answers exist, uniqueness proven)', f=FT)

# ---------- header ----------
text(40, 20, 'PUZZLE SHEET №1 — for a human', f=FB)
text(40, 52, "uniqueness machine-proven: exactly one solution each.", f=FT, fill=(110, 108, 100))

im.save('puzzles/sheet1.png')
print('sheet1.png written; sudoku givens:', sum(1 for r in g for v in r if v),
      '; nonogram 10x10; kakuro cells:', sum(sum(r) for r in white) if res else 0)
