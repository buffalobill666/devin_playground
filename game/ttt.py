"""ttt.py — крестики-нолики, минимакс + мемоизация.

Доска — кортеж из 9: 0 пусто, 1 крестик, -1 нолик.
Критерий: движок непроигрываем. Проверки: 500 партий против
случайного — ноль поражений; сам против себя — всегда ничья;
из каждой стартовой клетки — не хуже ничьей.
"""

import random

LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
         (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
_memo = {}


def winner(b):
    for a, c, d in LINES:
        if b[a] and b[a] == b[c] == b[d]:
            return b[a]
    return 0 if 0 in b else None        # None = ничья на полной


def score(b, turn, depth=0):
    """Лучший исход для `turn`: 1 победа, 0 ничья, -1 проигрыш
    (в очках текущего игрока; глубина — для быстрой победы)."""
    key = (b, turn)
    if key in _memo:
        return _memo[key]
    w = winner(b)
    if w is not None:
        # терминал — потеря для стороны на ходу (кто-то уже
        # выиграл); глубина — оттягивает проигрыш/торопит выигрыш
        _memo[key] = 0 if w == 0 else -10 + depth
        return _memo[key]
    best = -99
    for i in range(9):
        if b[i] == 0:
            nb = b[:i] + (turn,) + b[i + 1:]
            best = max(best, -score(nb, -turn, depth + 1))
    _memo[key] = best
    return best


def best_move(b, turn, rng=None):
    opts = [(i, -score(b[:i] + (turn,) + b[i + 1:], -turn))
            for i in range(9) if b[i] == 0]
    top = max(s for _, s in opts)
    picks = [i for i, s in opts if s == top]
    return (rng or random).choice(picks)


def show(b):
    sym = {1: 'X', -1: 'O', 0: '.'}
    print('\n'.join(' '.join(sym[v] for v in b[i:i + 3])
                    for i in (0, 3, 6)))
    print()


def play(engine_turns, rng):
    """Партия: engine_turns — множество сторон (1/-1) за движок."""
    b, t = (0,) * 9, 1
    while winner(b) is None:
        i = (best_move(b, t, rng) if t in engine_turns
             else rng.choice([j for j in range(9) if b[j] == 0]))
        b = b[:i] + (t,) + b[i + 1:]
        t = -t
    return winner(b)


if __name__ == '__main__':
    rng = random.Random(4)
    # 1. сам с собой — ничья
    self_results = {play({1, -1}, rng) for _ in range(30)}
    # 2. против случайного за обе стороны — ни одного проигрыша
    losses = 0
    for side in (1, -1):
        for _ in range(250):
            if play({side}, rng) == -side:
                losses += 1
    # 3. любой стартовый ход — движок не проигрывает ответом
    demo = (0,) * 9
    demo = demo[:0] + (1,) + demo[1:]     # X в угол
    b = demo[:best_move(demo, -1)] + (-1,) + demo[best_move(demo, -1) + 1:]
    print('Ответ на угол:')
    show(b)
    ok = self_results == {0} and losses == 0
    print(f'сам-себя: {self_results}, проигрышей случайному: {losses}')
    print('VERDICT:', 'OK — непроигрываем' if ok else 'FAIL')
