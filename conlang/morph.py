"""morph.py — морфология mu v0.1: агглютинация + алломорфы.

Ядро системы — встреча аффиксов с фонотактикой (SPEC.md):
- суффиксы на согласную стыкуются свободно (нос+согл через
  границу легален: tam.ka)
- суффиксы на гласную после гласной-финальной основы дают
  хиатус -> эпентеза глайда: j после a/e/i, w после o/u
  (luno + -in = lunowin, peliti + -in = pelitijin)

Система:
  существительные:  -in МН, -an СОБИР, -ka ОПР, -ti УМЕНЬШ
  глаголы:          -sa ПРОШ, -ra БУД (настоящее = основа)
  деривация:        -ne «тот, кто X», -la «место X», -um «действие X»
"""

import random

from gen import VOWELS, FRONT, BACK, word


def glide_for(v):
    return 'w' if v in BACK else 'j'          # j после a/e/i (+a), w после o/u


def join(stem, suffix):
    """Стыковка основы и суффикса по правилам фонотактики."""
    if suffix[0] in VOWELS and stem[-1] in VOWELS:
        return stem + glide_for(stem[-1]) + suffix
    return stem + suffix


NOUN_SUF = [('МН', '-in'), ('СОБИР', '-an'), ('ОПР', '-ka'), ('УМЕНЬШ', '-ti')]
VERB_SUF = [('ПРОШ', '-sa'), ('БУД', '-ra')]
DERIV = [('АГЕНТ', '-ne'), ('МЕСТО', '-la'), ('ДЕЙСТВИЕ', '-um')]

GLOSSES_N = ['холм', 'вода', 'тропа', 'звезда', 'дом', 'лист', 'песня', 'камень']
GLOSSES_V = ['идти', 'петь', 'смотреть', 'нести', 'расти', 'спать', 'помнить', 'звать']


def paradigm(stem, kind):
    """Полный парадигматический ряд основы."""
    rows = [(stem, 'основа')]
    for gloss, suf in (NOUN_SUF if kind == 'n' else VERB_SUF):
        rows.append((join(stem, suf.lstrip('-')), gloss))
    return rows


def derive(stem):
    return [(join(stem, suf.lstrip('-')), g) for g, suf in DERIV]


def clean_phono(w):
    """Контроль: ни пары гласных, ни кластера без носового."""
    for a, b in zip(w, w[1:]):
        if a in VOWELS and b in VOWELS:
            return False
        if a not in VOWELS and b not in VOWELS and a not in 'mn':
            return False
    return True


if __name__ == '__main__':
    rng = random.Random(77)
    stems = []
    while len(stems) < 8:
        w = word(rng)
        if w[-1] in VOWELS:               # основы берём гласно-финальные
            stems.append(w)
    nouns, verbs = stems[:4], stems[4:]
    allw = []

    print('== СУЩЕСТВИТЕЛЬНЫЕ ==')
    for s, g in zip(nouns, GLOSSES_N):
        print(f'  {s} «{g}»')
        for w, gl in paradigm(s, 'n')[1:]:
            print(f'    {w:<14} {gl}')
            allw.append(w)

    print('== ГЛАГОЛЫ ==')
    for s, g in zip(verbs, GLOSSES_V):
        print(f'  {s} «{g}»')
        for w, gl in paradigm(s, 'v')[1:]:
            print(f'    {w:<14} {gl}')
            allw.append(w)
        for w, gl in derive(s):
            print(f'    {w:<14} {gl}')
            allw.append(w)

    print('== ПРЕДЛОЖЕНИЯ ==')
    # SOV: подлежащее - дополнение-ОПР - глагол-время
    n1, n2, v = nouns[0], nouns[1], verbs[0]
    s1 = f'{n1} {join(n2, "ka")} {join(v, "sa")}'
    print(f'  {s1}  — «{GLOSSES_N[0]} ОПР-{GLOSSES_N[1]} ПРОШ-{GLOSSES_V[0]}»')
    n3, v2 = nouns[2], verbs[3]
    s2 = f'{join(join(v2, "ne"), "in")} {join(n3, "ka")} {v2}'
    print(f'  {s2}  — «АГЕНТ-МН-{GLOSSES_V[3]} ОПР-{GLOSSES_N[2]} НАСТ-{GLOSSES_V[3]}»')
    allw += s1.split() + s2.split()

    bad = [w for w in allw if not clean_phono(w)]
    print(f'форм проверено: {len(allw)}')
    print('VERDICT:', 'OK — вся морфология в фонотактике' if not bad
          else f'FAIL {bad[:5]}')
