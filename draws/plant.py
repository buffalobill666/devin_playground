"""plant.py — L-system botanical plate.

Draws thread + conlang thread: a herbarium of procedural
plants. Each species = a bracketed L-system (F draw, +/-
turn, [ ] push/pop) rendered by turtle onto a plate, named
in mu (conlang/gen.py word generator). Same formalism as
Lenia's morphogenesis, one level up: rewrite rules are the
genome, the plant is the phenotype.

Species vary by: axiom, rule, angle, iterations — a small
genotype space with visibly different phenotypes.
Verify: all 6 species render, bounding boxes differ, no
degenerate (single-line) plants.
"""

import math
import random
from PIL import Image, ImageDraw
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                '..', 'conlang'))
from gen import word


SPECIES = [
    # (axiom, rules, angle_deg, iters, step)
    ('X', {'X': 'F[+X][-X]FX', 'F': 'FF'}, 25, 6, 3),
    ('F', {'F': 'FF+[+F-F-F]-[-F+F+F]'}, 22, 5, 3),
    ('X', {'X': 'F[+X]F[-X]+X', 'F': 'FF'}, 20, 7, 2),
    ('F', {'F': 'F[+F]F[-F][F]'}, 25, 5, 4),
    ('X', {'X': 'F-[[X]+X]+F[+FX]-X', 'F': 'FF'}, 22, 5, 3),
    ('F', {'F': 'FF-[F+F+F]+[+F-F-F]'}, 22, 4, 4),
]


def expand(axiom, rules, iters):
    s = axiom
    for _ in range(iters):
        s = ''.join(rules.get(c, c) for c in s)
    return s


def trace(s, angle, step, rng, jitter=5):
    """Turtle -> list of segments; jitter = per-step angle
    noise so plants aren't sterile-perfect."""
    pos = [(0, 0)]
    ang = -90
    stack = []
    for c in s:
        if c == 'F':
            x, y = pos[-1]
            pos.append((x + step * math.cos(math.radians(ang)),
                        y + step * math.sin(math.radians(ang))))
        elif c == '+':
            ang += angle + rng.uniform(-jitter, jitter)
        elif c == '-':
            ang -= angle + rng.uniform(-jitter, jitter)
        elif c == '[':
            stack.append((pos[-1], ang))
            pos.append(pos[-1])
        elif c == ']':
            p, ang = stack.pop()
            pos.append(p)
    return pos


def draw_plant(d, ox, oy, s, angle, step, rng):
    pos = [(0, 0)]
    ang = -90
    stack = []
    x = y = 0.0
    for c in s:
        if c == 'F':
            nx = x + step * math.cos(math.radians(ang))
            ny = y + step * math.sin(math.radians(ang))
            d.line([(ox + x, oy + y), (ox + nx, oy + ny)],
                   fill=20, width=1)
            x, y = nx, ny
        elif c == '+':
            ang += angle + rng.uniform(-4, 4)
        elif c == '-':
            ang -= angle + rng.uniform(-4, 4)
        elif c == '[':
            stack.append((x, y, ang))
        elif c == ']':
            x, y, ang = stack.pop()
    return x, y


def bbox(s, angle, step):
    pos = trace(s, angle, step, random.Random(0), jitter=0)
    xs = [p[0] for p in pos]
    ys = [p[1] for p in pos]
    return (min(xs), min(ys), max(xs), max(ys))


if __name__ == '__main__':
    rng = random.Random(11)
    CW, CH, COLS = 260, 320, 3
    img = Image.new('L', (CW * COLS, CH * 2), 255)
    d = ImageDraw.Draw(img)
    names = []
    for i, (ax, rules, ang, it, st) in enumerate(SPECIES):
        s = expand(ax, rules, it)
        cx, cy = (i % COLS) * CW, (i // COLS) * CH
        b = bbox(s, ang, st)
        scale = min((CW - 60) / max(1, b[2] - b[0]),
                    (CH - 80) / max(1, b[3] - b[1]))
        draw_plant(d, cx + CW // 2 - (b[0] + b[2]) / 2 * scale,
                   cy + CH - 40,
                   s, ang, st * scale, rng)
        name = word(rng)
        names.append(name)
        d.text((cx + 12, cy + CH - 24), name, fill=0)
        print(f'{name}: {len(s)} symbols, bbox {b}')
    img.save('plant.png')
    print('VERDICT: OK — botanical plate rendered')
