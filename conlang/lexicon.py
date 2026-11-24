"""lexicon.py — ядерный словарь mu: корни по семантическим доменам.

Топонимика (c3i11) дала первые значения, но они жили в коде
карты. Здесь — системный лексикон: корни генерируются gen.word
(seed 42), курируются по доменам, проверяются на фонотактику
и уникальность. Деривации — через morph.join.

Выход: conlang/LEXICON.md — словарная таблица + фразы-пробы.
"""

import random
import os

from gen import word, VOWELS
from morph import join, clean_phono, paradigm, derive

SEED = 42

# домен -> [(глосс, часть речи)]
DOMAINS = {
    'вода и земля': [('вода', 'n'), ('море', 'n'), ('река', 'n'),
                     ('дождь', 'n'), ('земля', 'n'), ('гора', 'n'),
                     ('камень', 'n'), ('песок', 'n'), ('остров', 'n')],
    'живое': [('дерево', 'n'), ('лист', 'n'), ('трава', 'n'),
              ('зверь', 'n'), ('птица', 'n'), ('рыба', 'n'),
              ('семя', 'n'), ('корень', 'n')],
    'небо и время': [('небо', 'n'), ('солнце', 'n'), ('звезда', 'n'),
                     ('ветер', 'n'), ('день', 'n'), ('ночь', 'n'),
                     ('время', 'n')],
    'тело и дом': [('тело', 'n'), ('рука', 'n'), ('глаз', 'n'),
                   ('сердце', 'n'), ('дом', 'n'), ('тропа', 'n'),
                   ('огонь', 'n'), ('еда', 'n')],
    'действия': [('идти', 'v'), ('петь', 'v'), ('смотреть', 'v'),
                 ('нести', 'v'), ('расти', 'v'), ('спать', 'v'),
                 ('помнить', 'v'), ('звать', 'v'), ('есть', 'v'),
                 ('строить', 'v'), ('ждать', 'v'), ('искать', 'v')],
    'качества': [('большой', 'n'), ('малый', 'n'), ('новый', 'n'),
                ('старый', 'n'), ('свет', 'n'), ('тьма', 'n')],
}

HERE = os.path.dirname(os.path.abspath(__file__))


def make_lexicon():
    rng = random.Random(SEED)
    roots, used = [], set()
    for domain, entries in DOMAINS.items():
        for gloss, pos in entries:
            w = word(rng)
            while w in used or w[-1] not in VOWELS \
                    or not clean_phono(w):
                w = word(rng)
            used.add(w)
            roots.append((domain, w, gloss, pos))
    return roots


def render(roots):
    out = ['# LEXICON — ядерный словарь mu', '',
           'Корни — gen.word(seed 42), глоссы курированы.',
           'Полный парадигм корня: `morph.paradigm`.', '']
    cur = None
    for domain, w, gloss, pos in roots:
        if domain != cur:
            out += ['', f'## {domain}', '', '| mu | глосс |', '|---|---|']
            cur = domain
        out.append(f'| {w} | {gloss} |')
    return '\n'.join(out) + '\n'


def samples(roots):
    by = {g: (w, p) for _, w, g, p in roots}
    sea = join(by['море'][0], 'ka')
    hill = by['гора'][0]
    go = by['идти'][0]
    see = by['смотреть'][0]
    bird = by['птица'][0]
    sing = by['петь'][0]
    s1 = f'{hill} {sea} {join(go, "sa")}'
    s2 = f'{join(sing, "ne")} {join(bird, "ka")} {see}'
    return [(s1, 'гора ОПР-море ПРОШ-идти'),
            (s2, 'певец ОПР-птицу НАСТ-смотреть')]


if __name__ == '__main__':
    roots = make_lexicon()
    md = render(roots)
    md += '\n## пробы\n\n'
    for s, g in samples(roots):
        md += f'- `{s}` — {g}\n'
    open(os.path.join(HERE, 'LEXICON.md'), 'w',
         encoding='utf-8').write(md)
    bad = [w for _, w, _, _ in roots if not clean_phono(w)]
    dup = len(roots) - len({w for _, w, _, _ in roots})
    print(f'roots: {len(roots)}, bad_phono: {len(bad)}, dups: {dup}')
    print('VERDICT:', 'OK' if not bad and not dup else 'FAIL')
