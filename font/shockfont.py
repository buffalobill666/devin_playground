"""shockfont.py — third font principle: the token-level one.

freqfont (v1): glyph WIDTH = the letter's marginal frequency —
a property of the letter TYPE.
connectfont (v2): glyph SHAPE = the letter's digraph
distribution — still a property of the type: every 'E' is
identical.
shockfont (v3): glyph HEIGHT = surprisal -log2 P(char|prev) —
a property of the TOKEN. The same letter renders differently
every time, because what it carries is not what it IS but how
predictable its arrival was. Rendered text becomes a skyline
of its own information density: 'QU' sinks to the baseline
(u|q ~ certain), rare digraphs spike like an ECG.

Corpus: the repo's own English (same files as connectfont).
Sanity checks: 'U' after 'Q' must sit near the floor;
'E' after 'U' (EU digraph is rare) must spike hard.
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from connectfont import digraph_counts, ALPH

SAMPLE = 'THE QUICK BROWN FOX JUMPS OVER A LAZY EURO ZONE'
MAX_S = 12.0          # cap on surprisal axis (bits)
BAR_W, FLOOR = 22, 30


def surprisal(nxt, tot, prev, cur):
    """-log2 P(cur|prev) with add-one smoothing; prev=None ->
    marginal against total stream."""
    if prev is None or tot[prev] == 0:
        p = sum(tot.values()) and (tot[cur] + 1) / \
            (sum(tot.values()) + 26)
    else:
        p = (nxt[prev].get(cur, 0) + 1) / (tot[prev] + 26)
    return -math.log2(p)


def render(text, nxt, tot, path):
    pad, top = 24, 30
    w = pad * 2 + len(text) * BAR_W
    h = top + int(MAX_S * 12) + FLOOR + 46
    img = Image.new('L', (w, h), 255)
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default(14)
    base = top + int(MAX_S * 12) + FLOOR
    d.line([(pad, base), (w - pad, base)], fill=160)
    heights = []
    prev = None
    for i, ch in enumerate(text):
        x = pad + i * BAR_W + BAR_W // 2
        if ch == ' ':
            heights.append(None)
            prev = None
            continue
        s = min(MAX_S, surprisal(nxt, tot, prev, ch))
        bh = int(s / MAX_S * (MAX_S * 12))
        heights.append(s)
        d.line([(x - 8, base), (x - 8, base - bh)], fill=200)
        d.line([(x + 8, base), (x + 8, base - bh)], fill=200)
        d.line([(x - 8, base - bh), (x + 8, base - bh)], fill=60)
        d.text((x, base - bh - 18), ch, anchor='mm', font=f, fill=0)
        prev = ch
    d.text((pad, 8), 'shockfont: glyph height = surprisal '
           '-log2 P(char|prev), capped at 12 bits',
           font=f, fill=90)
    img.save(path)
    return heights


def check():
    nxt, tot = digraph_counts()
    qu = surprisal(nxt, tot, 'Q', 'U')
    eu = surprisal(nxt, tot, 'E', 'U')
    print(f'surprisal U|Q = {qu:.2f} bits (expect near 0)')
    print(f'surprisal U|E = {eu:.2f} bits (expect high)')
    ok = qu < 2.0 and eu > 4.0
    print('VERDICT:', 'OK' if ok else 'FAIL')
    return ok


if __name__ == '__main__':
    nxt, tot = digraph_counts()
    check()
    h = render(SAMPLE, nxt, tot,
               str(Path(__file__).with_suffix('.png')))
    print('saved shockfont.png;',
          'peaks:', [(c, round(s, 1)) for c, s in
                     zip(SAMPLE.replace(' ', ''), h)
                     if s and s > 8][:8])
