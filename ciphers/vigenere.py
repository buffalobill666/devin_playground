"""Vigenere — шифр и его взлом.

Взлом: длина ключа через Kasiski (повторы) и индекс совпадений;
каждая колонка — отдельный шифр Цезаря, решаемый хи-квадратом
против английских частот. Критерий истины жёсткий: ключ либо
восстановлен, либо нет.
"""

ALPH = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ENGFREQ = [8.17, 1.49, 2.78, 4.25, 12.70, 2.23, 2.02, 6.09, 6.97,
           0.15, 0.77, 4.03, 2.41, 6.75, 7.51, 1.93, 0.10, 5.99,
           6.33, 9.06, 2.76, 0.98, 2.36, 0.15, 1.97, 0.07]


def vigenc(text, key):
    out, k = [], 0
    for c in text.upper():
        if c in ALPH:
            out.append(ALPH[(ALPH.index(c) + ALPH.index(key[k % len(key)])) % 26])
            k += 1
    return ''.join(out)


def vigdec(ct, key):
    out, k = [], 0
    for c in ct:
        out.append(ALPH[(ALPH.index(c) - ALPH.index(key[k % len(key)])) % 26])
        k += 1
    return ''.join(out)


def ic(s):
    from collections import Counter
    n = len(s)
    if n < 2:
        return 0.0
    c = Counter(s)
    return sum(v * (v - 1) for v in c.values()) / (n * (n - 1))


def kasiski(ct, minlen=3):
    """Расстояния между повторами -> частота их делителей."""
    from collections import Counter
    dists = []
    for L in range(minlen, 9):
        seen = {}
        for i in range(len(ct) - L):
            seq = ct[i:i + L]
            if seq in seen:
                dists.append(i - seen[seq])
            seen[seq] = i
    factors = Counter()
    for d in dists:
        for p in range(2, 21):
            if d % p == 0:
                factors[p] += 1
    return factors


def guess_period(ct, maxp=20):
    """Средний IC колонок для каждого кандидата; английский ~0.066."""
    scores = {}
    for p in range(1, maxp + 1):
        cols = [ct[i::p] for i in range(p)]
        scores[p] = sum(ic(c) for c in cols) / p
    good = [p for p, s in scores.items() if s > 0.055]
    return min(good) if good else max(scores, key=scores.get), scores


def caesar_break(col):
    """Хи-квадрат против английских частот — лучший сдвиг."""
    from collections import Counter
    n = len(col)
    c = Counter(col)
    best, bestchi = 0, float('inf')
    for s in range(26):
        chi = sum((c.get(ALPH[(i + s) % 26], 0) - ENGFREQ[i] * n / 100) ** 2
                  / (ENGFREQ[i] * n / 100 + 1e-9) for i in range(26))
        if chi < bestchi:
            bestchi, best = chi, s
    return best


def break_vigenere(ct):
    (p, scores) = guess_period(ct)
    key = ''.join(ALPH[caesar_break(ct[i::p])] for i in range(p))
    return p, key, vigdec(ct, key)


if __name__ == '__main__':
    PT = """Cryptanalysis is the study of analyzing information systems in order
to study the hidden aspects of the systems. It is used to breach cryptographic
security systems and gain access to the contents of encrypted messages, even if
the cryptographic key is unknown. The index of coincidence measures how likely
it is to draw two matching letters by randomly selecting two letters from a text.
For a random collection of letters it is about one in twenty six, but for English
text it is noticeably higher because letter frequencies are far from uniform.
This single asymmetry is what allows the columns of a periodic polyalphabetic
cipher to be solved as independent Caesar ciphers once the period is found."""
    ct = vigenc(PT, 'ENIGMA')
    print('ciphertext head:', ct[:60], '...')
    print('kasiski factor votes:', kasiski(ct).most_common(6))
    p, key, dec = break_vigenere(ct)
    print('\nperiod guess:', p, '| recovered key:', key)
    print('decrypted head:', dec[:80])
    print('\nVERDICT:', 'KEY RECOVERED' if key == 'ENIGMA' else 'missed')
