"""atlas.py — the (F,k) phase map of Gray-Scott.

One equation family, a landscape of regimes: spots, stripes,
corals, mitosis, death. The atlas lays a 4x4 grid of micro-
worlds over the (F,k) plane — each tile a full simulation,
read together as a phase portrait of pattern space.

Named next step for the rd thread. Small N + shorter runs:
the regime reads fine at 128^2 x 6000 steps.
"""

import numpy as np
from PIL import Image

from grayscott import lap

N, DT = 128, 1.0
DU, DV = 0.2097, 0.105
STEPS = 6000

FS = [0.025, 0.037, 0.046, 0.058]   # feed columns
KS = [0.055, 0.060, 0.064, 0.068]   # kill rows


def run(f, k, seed=7):
    rng = np.random.default_rng(seed)
    u = np.ones((N, N))
    v = np.zeros((N, N))
    for _ in range(5):
        y, x = rng.integers(10, N - 10, 2)
        u[y:y + 6, x:x + 6] = 0.5
        v[y:y + 6, x:x + 6] = 0.25
    v += rng.random((N, N)) * 0.02
    for _ in range(STEPS):
        uvv = u * v * v
        u += DT * (DU * lap(u) - uvv + f * (1 - u))
        v += DT * (DV * lap(v) + uvv - (f + k) * v)
    return v


def tile(v, label):
    t = np.clip((v - v.min()) / (v.max() - v.min() + 1e-9), 0, 1)
    img = np.zeros((*t.shape, 3), np.uint8)
    img[..., 0] = (26 + t * 200)
    img[..., 1] = (38 + t * 190)
    img[..., 2] = (63 + t * 160)
    return img


if __name__ == '__main__':
    import os
    gap = 6
    cols, rows = len(FS), len(KS)
    from PIL import ImageDraw, ImageFont
    head = 22
    sheet = np.full((rows * (N + gap) + gap + head,
                     cols * (N + gap) + gap + head, 3), 18, np.uint8)
    tiles = {}
    for ri, k in enumerate(KS):
        for ci, f in enumerate(FS):
            v = run(f, k)
            print(f'F={f} k={k}: V range {v.min():.3f}..{v.max():.3f}',
                  flush=True)
            tiles[(ri, ci)] = tile(v, None)
    ft = ImageFont.load_default()
    for (ri, ci), t in tiles.items():
        sheet[head + ri * (N + gap):head + ri * (N + gap) + N,
              head + ci * (N + gap):head + ci * (N + gap) + N] = t
    pil = Image.fromarray(sheet)
    dr = ImageDraw.Draw(pil)
    for ci, f in enumerate(FS):
        dr.text((head + ci * (N + gap) + N // 2 - 18, 6),
                f'F={f}', fill=(210, 210, 200), font=ft)
    for ri, k in enumerate(KS):
        dr.text((2, head + ri * (N + gap) + N // 2 - 4),
                f'k={k}', fill=(210, 210, 200), font=ft)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'atlas.png')
    pil.save(out)
    print('F cols:', FS)
    print('k rows:', KS)
    print('-> rd/atlas.png')
