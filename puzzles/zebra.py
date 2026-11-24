"""zebra.py — Einstein-style logic grid puzzle: generator +
solver + uniqueness proof. Same law as nonogram: a puzzle
isn't a puzzle until the solver proves exactly one solution.

Classic 5-house zebra set. A solution is a permutation per
category. Clues: pos / same / next / leftof / immed_left.
Generator: seed a random solution, draw candidate clues true
of it, add greedily until the solver counts exactly 1, then
minimize (drop clues that stay redundant).

Solver: backtracking over category permutations (5!^4 worst
case, but clue-checked incrementally -> prunes to nothing in
practice for clue-consistent sets). count_solutions caps at 2.

Output: a solvable puzzle sheet printed + saved zebra.txt.
"""

import random
from itertools import permutations

CATS = {
    'nation': ['Englishman', 'Spaniard', 'Ukrainian',
               'Norwegian', 'Japanese'],
    'color': ['red', 'green', 'ivory', 'yellow', 'blue'],
    'drink': ['coffee', 'tea', 'milk', 'juice', 'water'],
    'pet': ['dog', 'snails', 'fox', 'horse', 'zebra'],
    'cigar': ['Old Gold', 'Kools', 'Chesterfields',
              'Lucky Strike', 'Parliaments'],
}
CAT_NAMES = list(CATS)


def rand_solution(rng):
    return {c: rng.sample(CATS[c], 5) for c in CAT_NAMES}


def pos_of(sol, cat, val):
    return sol[cat].index(val)


def clue_ok(clue, assign):
    """Check clue against a (possibly partial) assignment:
    assign = {cat: perm}. Unassigned categories -> vacuous."""
    def p(attr):
        cat, val = attr
        return assign[cat].index(val) if cat in assign else None

    kind, a, b = clue
    if kind == 'pos':
        pa = p(a)
        return pa is None or pa == b
    pa, pb = p(a), p(b)
    if pa is None or pb is None:
        return True                      # can't refute yet
    if kind == 'same':
        return pa == pb
    if kind == 'next':
        return abs(pa - pb) == 1
    if kind == 'leftof':
        return pa < pb
    if kind == 'immed_left':
        return pa == pb - 1
    raise ValueError(kind)


def count_solutions(clues, cap=2):
    """Backtrack over category permutations; count to cap."""
    order = CAT_NAMES
    perms = {c: list(permutations(range(5))) for c in CAT_NAMES}
    assign, found = {}, 0

    def bt(i):
        nonlocal found
        if found >= cap:
            return
        if i == len(order):
            found += 1
            return
        cat = order[i]
        for perm in perms[cat]:
            assign[cat] = perm
            if all(clue_ok(cl, {
                    c: [CATS[c][j] for j in assign[c]]
                    for c in assign}) for cl in clues):
                bt(i + 1)
            del assign[cat]
    bt(0)
    return found


def make_clues(sol, rng):
    """All clue types true of the planted solution, shuffled."""
    attrs = [(c, v) for c in CAT_NAMES for v in CATS[c]]
    clues = []
    for i in range(5):
        for c in CAT_NAMES:
            clues.append(('pos', (c, sol[c][i]), i))
    for a in attrs:
        for b in attrs:
            if a[0] == b[0] or a >= b:
                continue
            pa, pb = pos_of(sol, *a), pos_of(sol, *b)
            if pa == pb:
                clues.append(('same', a, b))
            if abs(pa - pb) == 1:
                clues.append(('next', a, b))
            if pa < pb:
                clues.append(('leftof', a, b))
            if pa == pb - 1:
                clues.append(('immed_left', a, b))
    rng.shuffle(clues)
    return clues


def generate(rng):
    sol = rand_solution(rng)
    pool, chosen = make_clues(sol, rng), []
    for cl in pool:
        chosen.append(cl)
        if count_solutions(chosen) == 1:
            break
    # minimize: drop clues that leave the puzzle unique
    i = 0
    while i < len(chosen):
        test = chosen[:i] + chosen[i + 1:]
        if count_solutions(test) == 1:
            chosen = test
        else:
            i += 1
    return sol, chosen


VERB = {'pos': '{a} lives in house {b}',
        'same': '{a} and {b} live in the same house',
        'next': '{a} lives next to {b}',
        'leftof': '{a} lives somewhere left of {b}',
        'immed_left': '{a} lives immediately left of {b}'}


ROLE = {'nation': '{v}', 'color': 'the {v}-house resident',
        'drink': 'the {v}-drinker', 'pet': 'the {v} owner',
        'cigar': 'the {v} smoker'}


def attr_str(a):
    return ROLE[a[0]].format(v=a[1])


def sheet(clues):
    lines = ['ZEBRA PUZZLE — 5 houses, positions 1..5 '
             'left to right', '']
    for c in CAT_NAMES:
        lines.append(f'  {c}: {", ".join(CATS[c])}')
    lines.append('')
    for i, (k, a, b) in enumerate(clues, 1):
        lines.append(f'{i:2}. ' + VERB[k].format(
            a=attr_str(a), b=(b + 1) if k == 'pos'
            else attr_str(b)))
    lines.append('')
    lines.append('Who drinks water? Who owns the zebra?')
    return '\n'.join(lines)


if __name__ == '__main__':
    rng = random.Random(42)
    sol, clues = generate(rng)
    print(sheet(clues))
    n = count_solutions(clues, cap=5)
    water = sol['drink'].index('water') + 1
    zebra = sol['pet'].index('zebra') + 1
    same = sol['drink'].index('water') == sol['pet'].index('zebra')
    print(f'\nsolutions: {n} (planted: water@{water}, '
          f'zebra@{zebra}, same house={same})')
    print('VERDICT:', 'OK' if n == 1 else 'FAIL')
    open('zebra.txt', 'w', encoding='utf-8').write(sheet(clues))
