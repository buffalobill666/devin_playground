"""autokey.py — Vigenere autokey cipher + two honest cracks.

Autokey (Blaise de Vigenere, 1586): keystream = short primer
prepended to the plaintext itself.
    k_i = primer[i]            i < L
    k_i = p[i - L]             i >= L
    c_i = (p_i + k_i) mod 26

Two attacks:

1. PRIMER DICTIONARY — the realistic weakness: primers are
   words. Try each candidate primer (len 1..12), decode the
   whole chain, score by English-ness. Small space, full
   recovery when the primer is a common word.

2. AVALANCHE — the structural one: plaintext doubles as key,
   so one guessed plaintext fragment at position i unlocks
   positions i+L, i+2L... (key lag = primer length). Seed
   common tetragrams at every offset, try L in 1..15, score
   recovered islands. The RIGHT seed grows readable islands;
   wrong seeds grow noise. Recovers plaintext even with an
   unguessable primer — the cipher leaks its own structure.
"""

import math
import random

ALPH = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ENGFREQ = [8.17, 1.49, 2.78, 4.25, 12.70, 2.23, 2.02, 6.97,
           6.09, 6.97, .15, .77, 4.03, 2.41, 6.75, 7.51, .19,
           .10, 5.99, 6.33, 9.06, 2.76, .98, 2.36, .15, 1.97, .07]
LOGF = [math.log(f / 100) for f in ENGFREQ]
TOPBIGRAMS = set('TH HE IN ER AN RE ON AT EN ND TI ES OR TE OF '
                 'ED IS IT AL AR ST TO NT NG SE HA AS OU IO LE '
                 'VE CO ME DE HI RI'.split())


def enc(text, primer):
    p = [ALPH.index(c) for c in text]
    k = [ALPH.index(c) for c in primer] + p
    return ''.join(ALPH[(p[i] + k[i]) % 26] for i in range(len(p)))


def dec(ct, primer):
    c = [ALPH.index(ch) for ch in ct]
    L = len(primer)
    p = [(c[i] - ALPH.index(primer[i])) % 26 for i in range(L)]
    for i in range(L, len(c)):
        p.append((c[i] - p[i - L]) % 26)
    return ''.join(ALPH[v] for v in p)


def score(text):
    """English-ness: letter log-prob + bigram bonuses."""
    s = sum(LOGF[ALPH.index(c)] for c in text if c in ALPH)
    s += 4.0 * sum(1 for i in range(len(text) - 1)
                   if text[i:i + 2] in TOPBIGRAMS)
    return s


def primer_attack(ct, wordlist):
    """Try each primer candidate; return best decode."""
    best = (-1e18, None, None)
    for primer in wordlist:
        if len(primer) > len(ct) or not primer.isalpha():
            continue
        pt = dec(ct, primer.upper())
        sc = score(pt)
        if sc > best[0]:
            best = (sc, primer.upper(), pt)
    return best


def run_score(derived, run):
    """Score one island run of consecutive derived positions —
    letters + internal bigrams. Seed positions are excluded:
    the seed always 'looks English'; only evidence counts."""
    # letter score = margin over the uniform baseline:
    # real plaintext gains ~+0.36/char, wrong-key noise ~0 —
    # so coverage is REWARDED, not punished by the sum.
    s = sum(LOGF[derived[j]] + math.log(26) for j in run)
    s += 4.0 * sum(1 for a, b in zip(run, run[1:])
                   if ALPH[derived[a]] + ALPH[derived[b]]
                   in TOPBIGRAMS)
    return s


def avalanche(ct, max_lag=15):
    """Seed common tetragrams at every offset; for each lag L
    propagate the key chain (p[j] -> k[j+L] -> p[j+L] and back).
    Score only DERIVED positions, run by run. Return (L,
    recovered, coverage) for the best seed."""
    c = [ALPH.index(ch) for ch in ct]
    n = len(c)
    seeds = ['TION', 'THER', 'THAT', 'WITH', 'MENT', 'IONS',
             'THIS', 'HERE', 'FROM', 'ATIO', 'EVER', 'IGHT']
    best = (-1e18, None, None, 0)
    for L in range(2, max_lag + 1):
        for w in seeds:
            for i in range(n - len(w) + 1):
                seed = {i + k: ALPH.index(ch)
                        for k, ch in enumerate(w)}
                known = dict(seed)
                grown = True
                while grown:
                    grown = False
                    for j, pv in list(known.items()):
                        fwd = j + L            # p[j] is key at j+L
                        if fwd < n and fwd not in known:
                            known[fwd] = (c[fwd] - pv) % 26
                            grown = True
                        back = j - L           # k[j] = p[j-L]
                        if back >= 0 and back not in known:
                            known[back] = (c[j] - pv) % 26
                            grown = True
                derived = {j: v for j, v in known.items()
                           if j not in seed}
                if not derived:
                    continue
                js, sc, run = sorted(derived), 0.0, None
                for j in js:
                    if run and j == run[-1] + 1:
                        run.append(j)
                    else:
                        if run:
                            sc += run_score(derived, run)
                        run = [j]
                sc += run_score(derived, run)
                if sc > best[0]:
                    best = (sc, L, dict(known), len(known) / n)
    sc, L, known, cov = best
    rec = ''.join(ALPH[known[i]] if i in known else '?'
                  for i in range(n))
    return L, rec, cov


def demo():
    rng = random.Random(11)
    pt = ('THEAUTOKEYCIPHERIMPROVESONTHEPLAINVIGENERE' +
          'BYUSINGTHEMESSAGEITSELFASPARTOFTHEKEYSTREAM' +
          'BUTTHATSAMEPROPERTYMAKESITLEAKITSOWNSTRUCTURE')
    primer = 'LEMON'
    ct = enc(pt, primer)
    wl = ['KEY', 'SECRET', 'LEMON', 'CIPHER', 'ORANGE',
          'APPLE', 'LIME', 'GRAPE', 'MANGO', 'QUEEN']
    sc, found, decd = primer_attack(ct, wl)
    ok1 = decd == pt
    L, rec, cov = avalanche(ct)
    blanks = rec.count('?')
    print(f'ciphertext: {ct[:48]}...')
    print(f'primer attack: found {found!r}, exact={ok1}')
    print(f'avalanche: lag={L}, coverage={cov:.0%}, '
          f'recovered: {rec[:60]}...')
    print(f'  blanks: {blanks}/{len(rec)}')
    ok2 = (L == len(primer)
           and sum(a == b for a, b in zip(rec, pt))
           / len(pt) > 0.6)
    print('VERDICT:', 'OK' if ok1 and ok2 else
          f'partial (primer={ok1}, avalanche={ok2})')


if __name__ == '__main__':
    demo()
