"""ringviz.py — spacetime diagram of the ring war.

Time downward, ring position across. Color encodes genome:
  empty/NOP      — black
  crystal CPYR stride-8 — green
  degenerate CPYR stride-1 — red
  other CPYR strides — yellow-blue gradient by stride
  non-copy ops   — dim violet

The extinction of diversity should be visible as the green
world bleeding red — or whatever actually happened, drawn
honestly. The migram precedent: the organism as wave, here
the war as weather.
"""
import sys
sys.path.insert(0, 'esolang')
import numpy as np
from PIL import Image
from ring import run_ring, CRYSTAL

SIZE = 4000
cells, ctxs, census, snaps = run_ring(
    [(i * (SIZE // 6), CRYSTAL) for i in range(6)],
    life=30, cap_rounds=60000, size=SIZE, mu=0.002,
    snap_every=150)

H = len(snaps)
img = np.zeros((H, SIZE, 3), dtype=np.uint8)
for t, (snap, ips) in enumerate(snaps):
    for x, (op, a1, a2) in enumerate(snap):
        if op == 'NOP' or op == 'HALT':
            continue
        if op == 'CPYR':
            if a2 == 8:
                img[t, x] = (40, 180, 80)      # crystal green
            elif a2 == 1:
                img[t, x] = (220, 60, 50)      # degenerate red
            else:
                f = min(1.0, abs(a2) / 8)
                img[t, x] = (int(60 + 160 * f), int(180 - 100 * f), 120)
        else:
            img[t, x] = (90, 60, 130)          # dim violet other ops

# context traces: white dots where a living organism's ip sits
for t, (snap, ips) in enumerate(snaps):
    for ip in ips:
        if ip >= 0:
            img[t, ip] = (255, 255, 255)
im = Image.fromarray(img).resize((1600, 400), Image.NEAREST)
im.save('draws/ringwar.png')
print('ringwar.png written', img.shape)
# quick color census: red vs green area at start/mid/end
for label, t in [('start', 10), ('mid', H // 2), ('end', H - 1)]:  # noqa
    row = img[t]
    red = np.sum((row[:, 0] == 220))
    green = np.sum((row[:, 1] == 180))
    print(f'{label}: red {red} green {green}')
