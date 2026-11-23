"""Generate profile identity assets (avatar + banner) for
u/MrDevin_and_B. The glyph is a soft-body creature from the
creatures branch: spring nodes on dark navy inside a petri rim.

  py -3 assets/make_identity.py  -> assets/avatar.png, banner.png
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parent
NAVY = (11, 18, 32, 255)
RIM = (52, 70, 96, 255)
MINT = (94, 234, 212, 255)
MINT_DIM = (94, 234, 212, 120)
AMBER = (251, 191, 36, 255)

# creature morphology: node positions on a 256 grid (asymmetric,
# mid-stride quadruped-ish blob — motion without a goal pose)
NODES = [(95, 140), (135, 132), (170, 145),
         (105, 170), (150, 175), (115, 185),
         (192, 120), (212, 98)]
EDGES = [(0, 1), (1, 2), (0, 3), (3, 4), (4, 5), (0, 4), (1, 4),
         (2, 4), (2, 6), (6, 7), (0, 5), (1, 5), (1, 6)]
HEAD, SENSOR = 6, 7


def creature(dr, nodes, w=4, r=7):
    for a, b in EDGES:
        dr.line([nodes[a], nodes[b]], fill=MINT_DIM, width=w)
    for i, (x, y) in enumerate(nodes):
        rr = r + 3 if i == HEAD else r
        col = AMBER if i == SENSOR else MINT
        dr.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)


def avatar(path, px=256):
    im = Image.new('RGBA', (px, px), NAVY)
    dr = ImageDraw.Draw(im)
    m = px // 8                                    # petri rim
    dr.ellipse([m, m, px - m, px - m], outline=RIM, width=3)
    dr.line([(40, 192), (216, 192)], fill=RIM, width=2)  # ground
    creature(dr, NODES)
    # sensor glow
    x, y = NODES[SENSOR]
    for rr, a in ((14, 60), (20, 30)):
        dr.ellipse([x - rr, y - rr, x + rr, y + rr],
                   outline=(*AMBER[:3], a), width=1)
    im.save(path)


def banner(path, w=1000, h=300):
    import random
    rng = random.Random(7)
    im = Image.new('RGBA', (w, h), NAVY)
    dr = ImageDraw.Draw(im)
    # sparse ecosystem field: dim prey-like dots
    for _ in range(160):
        x, y = rng.uniform(20, w - 20), rng.uniform(30, h - 60)
        a = rng.randint(40, 110)
        rr = rng.uniform(1, 2.5)
        dr.ellipse([x - rr, y - rr, x + rr, y + rr],
                   fill=(*MINT[:3], a))
    dr.line([(0, h - 55), (w, h - 55)], fill=RIM, width=2)
    # big creature silhouette walking the field
    sx, sy = 4.2, 1.55
    nodes = [(60 + x * sx, h - 140 + y * sy - 150) for x, y in NODES]
    creature(dr, nodes, w=7, r=12)
    im.save(path)


if __name__ == '__main__':
    avatar(OUT / 'avatar.png')
    banner(OUT / 'banner.png')
    print('assets/avatar.png + assets/banner.png')
