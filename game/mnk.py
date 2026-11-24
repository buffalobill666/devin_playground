"""mnk.py — крестики-нолики (m,n,k): доска m на n, линия k.

Обобщение ttt.py: линии генерируются, движок негамакс +
альфа-бета + мемоизация. Решаемо там, где хватает бюджета;
дальше — честное «неизвестно» и статистика Монте-Карло.

Известные факты жанра для сверки:
  (3,3,3) — ничья;  (4,4,3) — ничья;  (5,5,3) — победа 1-го.
"""

import random
import time

_memo = {}
_budget = {'deadline': 0.0, 'ok': True}


def lines(m, n, k):
    """Все прямые k-отрезка на доске m x n (индексы)."""
    out = []
    for y in range(n):
        for x in range(m):
            for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
                pts = [(x + dx * i, y + dy * i) for i in range(k)]
                if all(0 <= px < m and 0 <= py < n for px, py in pts):
                    out.append(tuple(py * m + px for px, py in pts))
    return out


def winner(b, ln):
    """v — победа, 0 — ничья (полная доска), None — игра идёт."""
    for seg in ln:
        v = b[seg[0]]
        if v and all(b[i] == v for i in seg):
            return v
    return None if 0 in b else 0


def negamax(b, turn, ln, a=-2, beta=2):
    key = (b, turn)
    if key in _memo:
        return _memo[key]
    if time.time() > _budget['deadline']:
        _budget['ok'] = False
        return 0
    w = winner(b, ln)
    if w is not None:
        return w if w == 0 else -1    # сторона на ходу проиграла
    best = -2
    for i, c in enumerate(b):
        if not c:
            nb = b[:i] + (turn,) + b[i + 1:]
            best = max(best, -negamax(nb, -turn, ln, -beta, -a))
            a = max(a, best)
            if a >= beta:
                break
    _memo[key] = best
    return best


def solve(m, n, k, seconds=60):
    """+1 победа 1-го, 0 ничья, None — не хватило бюджета."""
    _memo.clear()
    _budget['deadline'] = time.time() + seconds
    _budget['ok'] = True
    ln = lines(m, n, k)
    v = negamax((0,) * (m * n), 1, ln)
    return v if _budget['ok'] else None


def montecarlo(m, n, k, games=2000, seed=7):
    """Случайные игроки: доля побед X / O / ничьих."""
    rng = random.Random(seed)
    ln = lines(m, n, k)
    res = {1: 0, -1: 0, 0: 0}
    for _ in range(games):
        b, turn = (0,) * (m * n), 1
        while winner(b, ln) is None:
            empt = [i for i, c in enumerate(b) if not c]
            i = rng.choice(empt)
            b = b[:i] + (turn,) + b[i + 1:]
            turn = -turn
        res[winner(b, ln)] += 1
    return {k2: v / games for k2, v in res.items()}


if __name__ == '__main__':
    table = [(3, 3, 3), (4, 4, 3), (5, 5, 3), (4, 4, 4),
             (5, 5, 4), (6, 6, 4)]
    print(f'{"(m,n,k)":>10} {"exact":>10} {"MC x/o/=":>20}')
    for m, n, k in table:
        t0 = time.time()
        v = solve(m, n, k, seconds=45)
        dt = time.time() - t0
        exact = {1: 'X wins', 0: 'draw',
                 -1: 'O wins'}.get(v, f'unsolved ({dt:.0f}s)')
        mc = montecarlo(m, n, k)
        print(f'({m},{n},{k})  {exact:>16}   '
              f'{mc[1]:.0%}/{mc[-1]:.0%}/{mc[0]:.0%}')
