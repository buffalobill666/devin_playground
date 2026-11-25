"""dialect.py — fifth cartographic genre: dialectology of mu.

The continent's fourth map was the sky (climate); this one is
the voice. Mu speakers settled the land; speech innovations
spread like waves — fast along lowlands, slow over ranges,
not at all across sea. A sound law is categorical inside its
area: it either reached you or it did not.

Model — the wave model, made honest:
  1. Hearths: habitable lowland cells, greedily max-min spaced.
  2. Cost-distance through terrain from each hearth
     (mountains expensive, sea infinite) — iterative relaxation.
  3. Innovations are born at hearths at epochs; a cell adopts
     an innovation if the wave had time to reach it:
     cost_dist[hearth][cell] < (now - birth) * speed.
  4. Cell's dialect = set of adopted innovations. Dialect areas
     are EMERGENT — no borders are drawn by hand.

Then the testable part: apply each area's sound laws, in
chronological order, to proto-mu lexicon roots. The output
table shows the same word in different dialects — rules apply
categorically, verified programmatically.
"""
import os
import sys
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from continent import continent                     # noqa: E402

N, SEA = 256, 0.30
rng = np.random.default_rng(42)


def cost_distance(h, hearth):
    """Iterative-relaxation cost distance from hearth over land."""
    cost = 1.0 + 30.0 * np.clip(h - SEA, 0, 1) ** 2   # climbing is slow
    cost[h < SEA] = 1e9                                # sea is no road
    D = np.full_like(h, 1e12)
    D[hearth] = 0.0
    for _ in range(300):
        Dn = D.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            shifted = np.roll(D, (dy, dx), (0, 1)) + cost
            Dn = np.minimum(Dn, shifted)
        Dn[h < SEA] = 1e12
        D = Dn
    D[h < SEA] = np.inf
    return D


def pick_hearths(h, k=6):
    """Habitable lowlands, greedily spaced apart."""
    yy, xx = np.mgrid[0:N, 0:N]
    habit = (h > SEA + 0.02) & (h < SEA + 0.25)        # lowland only
    cand = np.argwhere(habit)
    if len(cand) == 0:
        raise SystemExit('no habitable cells')
    first = cand[rng.integers(len(cand))]
    hs = [tuple(first)]
    while len(hs) < k:
        d = np.min([np.abs(cand - hh).sum(1) for hh in hs], axis=0)
        hs.append(tuple(cand[int(np.argmax(d))]))
    return hs


# sound laws: (name, regex, replacement, birth-hearth-idx, epoch)
LAWS = [
    ('palatalization',  r'ti', 'si', 0, 100),
    ('lenition k>h',    r'k', 'h', 1, 250),
    ('final nasal drop', r'[mn]$', '', 2, 400),
    ('r>l merger',      r'r', 'l', 3, 200),
    ('s weakening',     r's', 'h', 4, 500),
    ('intervocalic p>w', r'(?<=[aeiou])p(?=[aeiou])', 'w', 5, 300),
    ('a>o rotation',    r'a', 'o', 0, 600),
    ('nasal merger m>n', r'm', 'n', 1, 700),
    ('glide deletion',  r'(?<=[aeiou])j(?=[aeiou])', '', 2, 800),
    ('rhotacism s>r',   r'(?<=[aeiou])s(?=[aeiou])', 'r', 3, 900),
]
NOW, SPEED = 1000, 0.55

PROTO = ['pija', 'si', 'mope', 'tinki', 'lokisa', 'napika',
         'komu', 'kuwa', 'rija', 'tamwe', 'sumpilu', 'niromwu']


def apply_laws(word, lawset):
    for idx in sorted(lawset, key=lambda i: LAWS[i][4]):
        word = re.sub(LAWS[idx][1], LAWS[idx][2], word)
    return word


def main():
    h = continent(N)
    hs = pick_hearths(h)
    print('hearths:', hs)
    Ds = [cost_distance(h, hh) for hh in hs]

    # adoption masks per law; cell dialect = bitmask
    sig = np.zeros((N, N), dtype=np.int32)
    for i, (name, pat, rep, hh, epoch) in enumerate(LAWS):
        reach = (NOW - epoch) * SPEED
        mask = Ds[hh] < reach
        sig[mask] |= 1 << i
        print(f'law {i} {name:20s} born h{hh}@{epoch} '
              f'reach {reach:.0f} covers {mask.sum()} cells')

    # dialect areas: dominant signatures on land
    land = h >= SEA
    sigs, counts = np.unique(sig[land], return_counts=True)
    order = np.argsort(-counts)
    top = {int(sigs[i]): r for r, i in enumerate(order[:8])}
    print('top signatures:', [(bin(s), c) for s, c in
                              zip(sigs[order[:8]], counts[order[:8]])])

    # merge fragment signatures into closest top one (hamming <= 2)
    def hamming(a, b):
        return bin(a ^ b).count('1')
    top_list = sorted(top)
    merged = sig.copy()
    uniq = np.unique(sig[land])
    remap = {}
    for sg in uniq:
        sg = int(sg)
        if sg in top:
            continue
        best = min(top_list, key=lambda t: hamming(sg, t))
        remap[sg] = best if hamming(sg, best) <= 2 else -1
    for sg, tgt in remap.items():
        merged[sig == sg] = tgt

    # dialect epithets: pick the proto-word that maximally
    # distinguishes the areas, then name each area by its form
    def area_word(sg, proto):
        laws_here = [i for i in range(len(LAWS)) if sg & (1 << i)]
        return apply_laws(proto, laws_here)
    best_proto, best_n = 'tinki', 0
    for w in PROTO:
        forms = {area_word(sg, w) for sg in top_list}
        if len(forms) > best_n:
            best_proto, best_n = w, len(forms)
    epithet = {}
    seen = {}
    for sg in top_list:
        f = area_word(sg, best_proto)
        seen[f] = seen.get(f, 0) + 1
        epithet[sg] = f if seen[f] == 1 else f + '·' + str(seen[f])
    print(f"epithet source: '{best_proto}' ({best_n} distinct forms)",
          epithet)

    # render — sea reserved exclusively, no palette collision
    colors = [(196, 93, 62), (94, 158, 98), (214, 174, 94),
              (146, 94, 158), (78, 148, 158), (188, 120, 160),
              (120, 120, 118), (60, 90, 60)]
    img = np.zeros((N, N, 3), dtype=np.uint8)
    img[~land] = (43, 67, 89)
    legend = []
    for r, sg in enumerate(top_list):
        col = colors[r % len(colors)]
        img[land & (merged == sg)] = col
        legend.append((col, f'{epithet[sg]}-dialects'))
    img[land & (merged == -1)] = (70, 70, 70)
    for hh in hs:
        img[max(0, hh[0]-2):hh[0]+3, max(0, hh[1]-2):hh[1]+3] = (255, 255, 255)

    from matplotlib.patches import Patch
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.imshow(img, interpolation='nearest')
    ax.set_title("dialect areas of mu — wave model, T=1000; "
                 "areas named by their own word-forms", fontsize=12)
    ax.legend(handles=[Patch(facecolor=np.array(c)/255, label=l)
                       for c, l in legend] +
              [Patch(facecolor=(0.27, 0.27, 0.27),
                     label='mixed fringe (hamming>2)')],
              loc='lower left', fontsize=9, framealpha=0.9)
    ax.axis('off')
    fig.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'dialect.png')
    fig.savefig(out, dpi=130)
    print('saved', out)

    # word table: pick 3 most distinct wide-area signatures
    big = [s for s, _ in
           sorted(top.items(), key=lambda kv: kv[1])[:4]]
    areas = {}
    for s in list(top)[:4]:
        laws_here = [i for i in range(len(LAWS)) if s & (1 << i)]
        areas[s] = laws_here
    print('\nproto ', end='')
    hdr = list(areas)[:4]
    print(' | '.join(f'area{j}' for j in range(len(hdr))))
    for w in PROTO:
        row = [apply_laws(w, areas[s]) for s in hdr]
        print(f'{w:9s} ' + ' | '.join(f'{r:9s}' for r in row))


if __name__ == '__main__':
    main()
