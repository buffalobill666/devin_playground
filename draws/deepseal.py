"""deepseal.py — парные печати deeptime-реплик (s11 vs s7, 100k тиков).

The deeptime question: convergence seen in seed 11 — law or luck?
Seed 7 replicated it (families 73→2, prey locked at capacity).
The terr pairs showed that paired seals make the experiment visible.
Here the pair answers differently: same world, different seed —
the seals should rhyme if convergence is real, differ in WHERE
the drama lives if the seeds had different youths.

Reuses runseal.seal/load — same wreath grammar.
Output: deepseal.png — two seals side by side.
"""

import os
from PIL import Image, ImageDraw
from runseal import seal, load, TILE


def main():
    base = os.path.join(os.path.dirname(__file__), '..', 'runs')
    runs = [
        ('deeptime/dt.csv', 'deeptime · seed 11'),
        ('deeptime-s7/dt.csv', 'deeptime · seed 7'),
        ('deeptime-s8/dt.csv', 'deeptime · seed 8'),
    ]
    plate = Image.new('RGB', (len(runs) * (TILE + 40) + 20,
                              TILE + 120), (24, 24, 28))
    dr = ImageDraw.Draw(plate)
    dr.text((40, 30),
            'deeptime 100k x3: violent youths, one old age — '
            'does the churn-seed seal rhyme too?',
            fill=(140, 140, 140))
    for col, (path, name) in enumerate(runs):
        img = seal(load(os.path.join(base, path)), name)
        plate.paste(img, (20 + col * (TILE + 40), 60))
    out = os.path.join(os.path.dirname(__file__), 'deepseal.png')
    plate.save(out)
    print('saved', out)


if __name__ == '__main__':
    main()
