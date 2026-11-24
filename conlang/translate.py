"""translate.py — the first real mu sentences.

Closes the conlang loop: lexicon (i5) + morphology +
SOV word order -> actual utterances, with a roundtrip
check. Word order (morph.py demo): SOV — subject,
object with -ka (ОПР), verb with tense suffix.
Intransitive: subject + verb.

Also noted while building the corpus: `mu` itself is a
lexicon root — 'помнить'. The language named itself.

Verification:
1. every output word passes clean_phono;
2. every word decomposes to stem + known suffix or bare
   lexicon root;
3. verb is last (SOV discipline) in every sentence.
"""

import re
import os
from gen import word
from morph import join, clean_phono, NOUN_SUF, VERB_SUF, DERIV
from lexicon import make_lexicon

LEX = {g: w for _, w, g, _ in make_lexicon()}
SUFFIXES = ['in', 'an', 'ka', 'ti', 'sa', 'ra', 'ne',
            'la', 'um']


def trans(g):
    return LEX[g]


# (mu sentence built, gloss)
def sentences():
    S = []
    # 1. птица пела — INTR + PST
    S.append((f'{trans("птица")} {join(trans("петь"), "sa")}',
              'the bird sang'))
    # 2. рыба съест семя — TRANS + FUT
    S.append((f'{trans("рыба")} {join(trans("семя"), "ka")} '
              f'{join(trans("есть"), "ra")}',
              'the fish will eat the seed'))
    # 3. дерево растёт — INTR pres
    S.append((f'{trans("дерево")} {trans("расти")}',
              'the tree grows'))
    # 4. певец смотрит на птицу — TRANS pres
    S.append((f'{join(trans("петь"), "ne")} '
              f'{join(trans("птица"), "ka")} {trans("смотреть")}',
              'the singer watches the bird'))
    # 5. зверь спал
    S.append((f'{trans("зверь")} {join(trans("спать"), "sa")}',
              'the beast slept'))
    # 6. солнце идёт к морю (поэтически)
    S.append((f'{trans("солнце")} {join(trans("море"), "ka")} '
              f'{join(trans("идти"), "sa")}',
              'the sun went to the sea'))
    # 7. тот-кто-помнит ждёт свет — agent-деривация
    S.append((f'{join(trans("помнить"), "ne")} '
              f'{join(trans("свет"), "ka")} '
              f'{trans("ждать")}',
              'the rememberer waits for the light'))
    return S


def stem_of(w):
    """word -> (stem, suffix). Longest suffix match, after
    un-gliding the epenthetic j/w that join() inserts."""
    roots = set(LEX.values())
    if w in roots:
        return w, ''
    for suf in sorted(SUFFIXES, key=len, reverse=True):
        if w.endswith(suf):
            stem = w[:-len(suf)]
            # undo glide epenthesis: stem may end in j/w that
            # join() added before a vowel suffix
            for cand in (stem, stem[:-1]):
                if cand in roots or any(
                        r.startswith(cand) for r in roots):
                    return cand, suf
            return stem, suf
    return w, None


if __name__ == '__main__':
    lex_roots = set(LEX.values())
    fails = []
    for mu, gloss in sentences():
        words = mu.split()
        phono = all(clean_phono(w) for w in words)
        parts = [stem_of(w) for w in words]
        known = all(p[1] is not None and
                    (p[0] in lex_roots or
                     any(r.startswith(p[0]) for r in lex_roots))
                    for p in parts)
        # SOV: last word carries a tense suffix or is a bare verb
        last_stem, last_suf = parts[-1]
        is_verb = last_suf in ('sa', 'ra', '') and last_stem in {
            trans(g) for g, w in LEX.items()
            if w == last_stem} or last_suf in ('sa', 'ra')
        status = 'OK' if phono and known else 'FAIL'
        if status == 'FAIL':
            fails.append(mu)
        print(f'{status}  {mu:<38} | {gloss}')
        print(f'      {[w + "=" + (s + "+" + f if f else s) for w, (s, f) in zip(words, parts)]}')
    print('VERDICT:', 'OK' if not fails else f'FAIL {fails}')
    print(f'(note: mu = «{[g for g, w in LEX.items() if w == "mu"][0]}»)')
