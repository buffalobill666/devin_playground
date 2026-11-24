"""playfair.py — the digraph cipher (WWI field cipher).

Vigenere broke because a monoalphabetic column leaks letter
frequencies. Playfair encrypts DIGRAPHS on a 5x5 key square:
each pair maps through geometry — same row -> right wrap,
same column -> down wrap, else the rectangle's other corners.
Frequency analysis must now fight 600 digraphs, not 26
letters — and every occurrence of a letter lands differently
depending on its partner.

Rules: I/J merged; doubles split with X; odd tail padded X.
"""

ALPH = 'ABCDEFGHIKLMNOPQRSTUVWXYZ'  # no J


def square(key):
    seen = ''
    for c in (key + ALPH).upper():
        c = 'I' if c == 'J' else c
        if c in ALPH and c not in seen:
            seen += c
    return [seen[i:i + 5] for i in range(0, 25, 5)]


def pos_of(sq):
    return {sq[y][x]: (y, x) for y in range(5) for x in range(5)}


def digraphs(text):
    t = ''.join(c if c != 'J' else 'I' for c in text.upper()
                if c in ALPH or c == 'J')
    out, i = [], 0
    while i < len(t):
        a = t[i]
        b = t[i + 1] if i + 1 < len(t) else 'X'
        if a == b:
            out.append((a, 'X')); i += 1
        else:
            out.append((a, b)); i += 2
    return out


def crypt(pair, sq, pos, d):
    (ay, ax), (by, bx) = pos[pair[0]], pos[pair[1]]
    if ay == by:
        return sq[ay][(ax + d) % 5] + sq[by][(bx + d) % 5]
    if ax == bx:
        return sq[(ay + d) % 5][ax] + sq[(by + d) % 5][bx]
    return sq[ay][bx] + sq[by][ax]


def playfair(text, key, d=1):
    sq = square(key)
    pos = pos_of(sq)
    return ''.join(crypt(p, sq, pos, d) for p in digraphs(text))


if __name__ == '__main__':
    key = 'MONARCHY'
    msg = ('INSTRUMENTS OF INTELLIGENCE INTERFERE WITH '
           'EVERY ATTEMPT AT SECRET WRITING')
    ct = playfair(msg, key)
    rt = playfair(ct, key, d=-1)
    sq = square(key)
    print('key square:')
    for row in sq:
        print('  ' + ' '.join(row))
    print('ct:', ct)
    print('rt:', rt.replace('X', ''))
    flat = rt.replace('X', '')
    ok = all(a == b or (a == 'I' and b == 'J')
             for a, b in zip(flat, msg.replace(' ', '').replace('J', 'I')))
    # diffusion: monograph IC of plaintext vs ciphertext
    from collections import Counter

    def ic(s):
        c = Counter(s)
        n = len(s)
        return sum(v * (v - 1) for v in c.values()) / (n * (n - 1))
    print(f'IC plaintext : {ic(msg.replace(" ", "")):.4f}')
    print(f'IC ciphertext: {ic(ct):.4f}   (random ~0.038)')
    print('VERDICT:', 'OK' if ok else 'CHECK roundtrip')
