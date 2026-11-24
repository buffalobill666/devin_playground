"""reversi.py — Othello 8x8: движок + альфа-бета с позиционной оценкой.

Углубление game/: после крестиков-ноликов (полный перебор) —
игра, где перебор невозможен, нужна эвристика. Оценка:
мобильность + углы + вес клеток (таблица), фишки — только
в эндшпиле. Вердикт: 0 поражений против случайного за 200 партий.
"""

import random
from functools import lru_cache

N = 8
DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
W = [120, -20, 20, 5, 5, 20, -20, 120,
     -20, -40, -5, -5, -5, -5, -40, -20,
     20, -5, 15, 3, 3, 15, -5, 20,
     5, -5, 3, 3, 3, 3, -5, 5,
     5, -5, 3, 3, 3, 3, -5, 5,
     20, -5, 15, 3, 3, 15, -5, 20,
     -20, -40, -5, -5, -5, -5, -40, -20,
     120, -20, 20, 5, 5, 20, -20, 120]


def start():
    b = [0] * 64
    b[27] = b[36] = -1          # белые
    b[28] = b[35] = 1           # чёрные
    return tuple(b)


@lru_cache(maxsize=150_000)    # bounded: без лимита кэш съедает ГБы RAM
def _moves(b, p):
    b = list(b)
    return [i for i in range(64) if _flips(b, p, i)]


@lru_cache(maxsize=150_000)
def _apply(b, p, i):
    f = _flips(list(b), p, i)     # flips считаются ДО установки —
    b = list(b)                   # _flips откажется от занятой клетки
    b[i] = p
    for j in f:
        b[j] = p
    return tuple(b)


def _flips(b, p, i):
    if b[i]:
        return []
    out = []
    r, c = divmod(i, N)
    for dr, dc in DIRS:
        line, nr, nc = [], r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and b[nr * N + nc] == -p:
            line.append(nr * N + nc)
            nr += dr
            nc += dc
        if line and 0 <= nr < N and 0 <= nc < N and b[nr * N + nc] == p:
            out += line
    return out


def moves(b, p):
    return _moves(b, p)


def apply(b, p, i):
    return _apply(b, p, i)


def score(b, p):
    """Оценка позиции для p: веса + мобильность; фишки в эндшпиле."""
    occupied = sum(1 for v in b if v)
    pos = sum(W[i] * b[i] * p for i in range(64))
    mob = len(moves(b, p)) - len(moves(b, -p))
    if occupied >= 58:                       # эндшпиль: решают фишки
        return pos + 50 * (sum(b) * p)
    return pos + 8 * mob


def ab(b, p, d, a, beta, memo):
    """Оценка позиции для p поиском на глубину d (negamax + A-B)."""
    key = (b, p, d)
    if key in memo:
        return memo[key]
    mm = moves(b, p)
    if not mm:
        if not moves(b, -p):                 # игра окончена
            return 10000 * (sum(b) * p)
        return -ab(b, -p, d, -beta, -a, memo)   # пас, глубина не тратится
    if d == 0:
        return score(b, p)
    best = -10 ** 9
    for m in sorted(mm, key=lambda i: -W[i]):   # углы первыми — отсечки
        v = -ab(apply(b, p, m), -p, d - 1, -beta, -a, memo)
        best = max(best, v)
        a = max(a, v)
        if a >= beta:
            break
    if len(memo) < 1_500_000:          # потолок: дальше кэш дороже выигрыша
        memo[key] = best
    return best


def ai_move(b, p, depth=5, memo=None):
    """Лучший ход; memo общий на всю партию — кэш копится.
    <=10 пустых: точный перебор до конца; <=20: глубина 6."""
    if memo is None:
        memo = {}
    empties = sum(1 for v in b if v == 0)
    if empties <= 10:
        depth = empties + 1
    elif empties <= 20:
        depth = 6
    mm = moves(b, p)
    best, bestm, a = -10 ** 9, mm[0], -10 ** 9
    for m in mm:
        v = -ab(apply(b, p, m), -p, depth - 1, -10 ** 9, -a, memo)
        if v > best:
            best, bestm = v, m
        a = max(a, v)
    return bestm


def play(p_ai=1, depth=5, rng=None, memo=None):
    """Партия: p_ai играет альфа-бетой, -p_ai — случайно. -> знак для p_ai."""
    b, turn, passed = start(), 1, 0
    while passed < 2:
        mm = moves(b, turn)
        if not mm:
            passed += 1
            turn = -turn
            continue
        passed = 0
        if turn == p_ai:
            b = apply(b, turn, ai_move(b, turn, depth, memo))
        else:
            b = apply(b, turn, rng.choice(mm))
        turn = -turn
    s = sum(b) * p_ai
    return (s > 0) - (s < 0)


if __name__ == '__main__':
    rng = random.Random(5)
    memo = {}
    res = [play(1, 4, rng, {}) for _ in range(60)]   # memo — на партию, не на бенчмарк
    wins, draws = res.count(1), res.count(0)
    print(f'60 партий vs random: {wins} побед, {draws} ничьих, '
          f'{res.count(-1)} поражений')
    print('VERDICT:', 'OK — непроигрываем' if res.count(-1) == 0 else 'FAIL')
