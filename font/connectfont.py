"""connectfont.py — second font principle: glyphs are graphs.

freqfont encoded a letter's marginal frequency in its WIDTH.
connectfont encodes the letter's digraph neighbourhood in its
SHAPE: each glyph is a 26-bar histogram of P(next | letter),
x-axis = the alphabet itself, a caret under the strip marks
the letter's own index. Corpus: this repo's own English
prose (history.md, READMEs, marginalia, prose) — a font
computed from its own author's text.

Sanity checks baked in: Q's argmax must be U (the most
conditional letter in English); E's followers must be a
broad spread, not a spike.
"""

from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ['history.md', 'README.md',
          'marginalia/flatland-part1.md',
          'marginalia/flatland-part2.md',
          'prose/wakeup.md', 'prose/museum.md',
          'prose/letters.md']
ALPH = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
GW, GH = 28, 16          # glyph box: 26 bars + margins
BAR_H = 11


def digraph_counts():
    nxt = {c: Counter() for c in ALPH}
    tot = Counter()
    for rel in CORPUS:
        p = ROOT / rel
        if not p.exists():
            continue
        txt = p.read_text(encoding='utf-8',
                          errors='ignore').upper()
        for a, b in zip(txt, txt[1:]):
            if a in ALPH and b in ALPH:
                nxt[a][b] += 1
                tot[a] += 1
    return nxt, tot


def glyph(nxt, tot, ch):
    """26 bars: P(next|ch) per-target normalized to own max;
    caret under own index."""
    img = Image.new('L', (GW, GH), 255)
    d = ImageDraw.Draw(img)
    mx = max(nxt[ch].values()) if tot[ch] else 1
    for i, t in enumerate(ALPH):
        f = nxt[ch].get(t, 0) / mx if mx else 0
        h = int(f * BAR_H)
        if h:
            d.line([(2 + i, BAR_H), (2 + i, BAR_H - h)], fill=0)
    x = 2 + ALPH.index(ch)
    d.polygon([(x - 1, BAR_H + 2), (x + 1, BAR_H + 2),
               (x, BAR_H + 4)], fill=0)
    return img


def specimen(nxt, tot, path):
    rows, pad = [], 4
    alpha = ''.join(ALPH)
    lines = [alpha, 'CONNECTFONT', 'THE QUICK BROWN FOX']
    w = (GW + 1) * len(alpha) + 2 * pad
    h = (GH + 8) * len(lines) + 2 * pad + 10
    img = Image.new('L', (w, h), 255)
    d = ImageDraw.Draw(img)
    for r, word in enumerate(lines):
        for i, ch in enumerate(word):
            if ch not in ALPH:
                continue
            g = glyph(nxt, tot, ch)
            img.paste(g, (pad + i * (GW + 1),
                          pad + r * (GH + 8)))
    # legend: alphabet labels under row 0
    for i, ch in enumerate(alpha):
        d.text((pad + i * (GW + 1) + 2,
                pad + GH + 2), ch, fill=0)
    img.save(path)


if __name__ == '__main__':
    nxt, tot = digraph_counts()
    out = Path(__file__).parent / 'connectfont.png'
    specimen(nxt, tot, out)
    q_top = max(nxt['Q'], key=nxt['Q'].get)
    e_top = sorted(nxt['E'].items(),
                   key=lambda kv: -kv[1])[:4]
    e_spread = len([v for v in nxt['E'].values() if v > 0])
    print(f'letters covered: {len(tot)}, '
          f'total digraphs: {sum(tot.values())}')
    print(f'Q -> top {q_top} ({nxt["Q"][q_top]}/{tot["Q"]}); '
          f'E top {e_top}; E spread {e_spread}/26')
    ok = q_top == 'U' and e_spread > 15
    print('VERDICT:', 'OK' if ok else 'FAIL')
