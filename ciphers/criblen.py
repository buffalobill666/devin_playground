"""criblen.py — сколько криба достаточно для взлома?

Бомба отвечает «можно ли сломать»; этот прогон отвечает
«насколько длинной должна быть криб». Один полный обход
пространства (60 orders x 17576 positions); для каждого
кандидата — счёт совпадений на КАЖДОМ префиксе криба
(ранний выход запрещён: нам нужны все длины).

Ответ — кривая единственности: для каждого L —
ранг истинной настройки и сколько соперников набирают
столько же или больше. Пока L мал, совпадения случайны
и толпа неотличима; после порога истина вылезает наверх.
"""

import itertools
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from enigma import Enigma                                    # noqa: E402

ROT_NAMES = ['I', 'II', 'III', 'IV', 'V']
TRUTH = (('II', 'IV', 'I'), (17, 4, 22))
CT = 'QRMIRMBDNVLXDHECTSGWGORRU'
CRIB = 'WETTERVORHERSAGE'
OFF = 0
LMAX = len(CRIB)


def main():
    # score[(order,pos)] = список счётов по префиксам 1..LMAX
    truth_scores = None
    best_rival = [0] * (LMAX + 1)      # лучший счёт НЕ-истины на L
    t0 = time.time()
    for order in itertools.permutations(ROT_NAMES, 3):
        for pos in itertools.product(range(26), repeat=3):
            m = Enigma(order, pos=pos)
            pref = [0] * (LMAX + 1)
            run = 0
            for i, a in enumerate(CRIB):
                run += m.enc_char(a) == CT[OFF + i]
                pref[i + 1] = run
            if (order, pos) == TRUTH:
                truth_scores = pref
            else:
                for L in range(1, LMAX + 1):
                    if pref[L] > best_rival[L]:
                        best_rival[L] = pref[L]
    dt = time.time() - t0
    print(f'sweep: {dt:.0f}s; truth {TRUTH}; crib "{CRIB}"')
    print(f'{"L":>3} {"truth":>5} {"best rival":>10} {"unique?":>8}')
    for L in range(1, LMAX + 1):
        ts, br = truth_scores[L], best_rival[L]
        print(f'{L:>3} {ts:>5} {br:>10} '
              f'{"YES" if ts > br else ("tie" if ts == br else "no"):>8}')


if __name__ == '__main__':
    main()
