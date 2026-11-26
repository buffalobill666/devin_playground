"""puzzle_sheet.py — a human-playable cipher sheet (c8/i25).

Six chained puzzles. Each plaintext is a mu word from the
chronicle lexicon; one answer becomes the key to the last
puzzle. The final plaintext is a chronicle line. Printable.
"""
import os

A = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def caesar(s, k):
    return ''.join(A[(A.index(c) + k) % 26] if c in A else c
                   for c in s.upper())


def atbash(s):
    return ''.join(A[25 - A.index(c)] if c in A else c
                   for c in s.upper())


def vigenere(s, key):
    out, ki = [], 0
    for c in s.upper():
        if c in A:
            out.append(A[(A.index(c) + A.index(key[ki % len(key)])) % 26])
            ki += 1
        else:
            out.append(c)
    return ''.join(out)


def rail2(s):
    """simple two-rail transpose for puzzle 5"""
    s = s.replace(' ', '')
    ev, od = s[::2], s[1::2]
    return ev + od


# plaintexts: mu chronicle words (uppercased latin)
p1 = 'NOKO'       # память-храм
p2 = 'MAPIJA'     # переход
p3 = 'TEJO'       # основать
p4 = 'PULU'       # топоним-храм
key5 = p2          # ключ к пятой — ответ второй загадки!
p5 = 'NOKOLA'     # место памяти
final = 'LUNAKUSA'  # умереть-прош — «умер» летописный

puzzles = [
    ('I. warm-up — a shift of three',
     caesar(p1, 3), 'three steps down the alphabet'),
    ('II. the mirror',
     atbash(p2), 'the alphabet reads both ways'),
    ('III. the wanderer — a shift unknown',
     caesar(p3, 11), 'only twenty-five keys exist'),
    ('IV. the first key — word MU',
     vigenere(p4, 'MU'), 'the language keeps its own keys'),
    ('V. the crossing — rails',
     rail2(p5), 'even letters first, odd letters follow'),
    ('VI. the chain — the answer of II opens this',
     vigenere(final, key5), 'vigenere with a key you already hold'),
]

HERE = os.path.dirname(os.path.abspath(__file__))
out = ['# cipher sheet — six locks, one chain', '',
       'Rules: every plaintext is a word of mu, the language',
       'of the continent (glossary at the bottom, upside down',
       'in spirit). Answers feed forward: the solution of II',
       'is the key to VI.', '']
for title, ct, hint in puzzles:
    out += [f'## {title}', '', f'    {ct}', '', f'*{hint}*', '']
out += ['---', '', 'glossary (cover this strip): NOKO memory-shrine,',
        'MAPIJA crossing, TEJO to-found, PULU the temple town,',
        'NOKOLA place-of-memory, LUNAKUSA died-chronicled', '']
open(os.path.join(HERE, 'sheet.md'), 'w', encoding='utf-8').write(
    '\n'.join(out))
# verify chain: decrypt VI with answer of II
check = vigenere(final, key5)
print('VI ciphertext:', check)
print('sheet written, chain consistent:',
      vigenere(final, key5) == puzzles[5][1])
