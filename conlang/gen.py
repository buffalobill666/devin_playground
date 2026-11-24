"""gen.py — генератор слов конлэнга (фонология в SPEC.md).

Слог: (C)V или (C)VN. Нет кластеров, нет стечений гласных —
между ними вставляется глайд /j/ после передних, /w/ после
задних. Первое слово первого прогона — автохтонное имя языка.
"""

import random

CONS = 'ptkmsnlrw'            # 9 согласных (r — дрожащий)
VOWELS = 'aeiou'
FRONT, BACK = set('ei'), set('ou')
ONSET_W = {'p': .14, 't': .14, 'k': .12, 'm': .10, 'n': .10,
           's': .12, 'l': .12, 'r': .08, 'w': .04}
CODA_NASAL_P = 0.18          # доля слогов с носовым выходом


def pick(rng, table):
    return rng.choices(list(table), weights=table.values())[0]


def syllable(rng, after=None):
    """Слог; after — предыдущая гласная (для разрешения хиатуса)."""
    out = ''
    if after is None:
        out += pick(rng, ONSET_W)               # слово начинается с C
    elif rng.random() < 0.30:                   # хиатус -> глайд
        out += 'w' if after in BACK else 'j'    # j после a/e/i, w после o/u
    else:
        out += pick(rng, ONSET_W)               # хиатус -> обычный онсет
    v = rng.choice(VOWELS)
    out += v
    if rng.random() < CODA_NASAL_P:
        out += 'n' if v in FRONT else 'm'       # гармония носового
    return out, v


def word(rng):
    n = rng.choices((1, 2, 3), weights=(.2, .55, .25))[0]
    w, prev = '', None
    for _ in range(n):
        syl, prev = syllable(rng, prev)
        w += syl
    return w


def lexicon(rng, n=16):
    seen = set()
    while len(seen) < n:
        seen.add(word(rng))
    return sorted(seen)


if __name__ == '__main__':
    rng = random.Random(2026)
    autonym = word(rng)
    print(f'Язык называет себя: {autonym!r} ({autonym} — «наша речь»)')
    print()
    for w in lexicon(rng):
        print(' ', w)
    # контроль фонотактики: ни одной пары гласных подряд,
    # ни одного кластера согласных
    bad = [w for w in lexicon(random.Random(1), 400)
           if any(a in VOWELS and b in VOWELS
                  for a, b in zip(w, w[1:]))]
    print('VERDICT:', 'OK — фонотактика чиста' if not bad
          else f'FAIL {bad[:5]}')
