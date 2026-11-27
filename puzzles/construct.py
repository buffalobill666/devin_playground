"""Constructor v3 — proof-writer: grows the deduction chain, board is its shadow.

Algorithm: adaptive fill. After each placement run the propagation solver;
the next cell is chosen among those the solver can already derive, and given
its true value. The final puzzle is thus provably deductively solvable.
Entry: seeded force-cell via tail sums (sum 3 / sum 4 pair crossing).
"""
import sys, random
sys.path.insert(0, 'puzzles')
from deduce import solve_propagation

def paired_runs(n):
    """Rows and cols split into 2-cell pairs: (r,0)-(r,1), (r,2)-(r,3), ..."""
    runs = []
    for r in range(n):
        for c0 in range(0, n - 1, 2):
            runs.append([(r, c0), (r, c0 + 1)])
    for c in range(n):
        for r0 in range(0, n - 1, 2):
            runs.append([(r0, c), (r0 + 1, c)])
    return runs

def build_puzzle(n, rng):
    runs = paired_runs(n)
    # entry: cell (0,0). row-partner (0,1)=2 forced sum 3; col-partner (1,0)=3 forced sum 4 -> (0,0)=1
    fill = {(0, 0): 1, (0, 1): 2, (1, 0): 3}
    # fill everything else randomly first (true solution), distinctness per run
    cells = [(r, c) for r in range(n) for c in range(n)]
    for cell in cells:
        if cell in fill:
            continue
        # collect used digits in all runs containing cell
        used = set()
        for run in runs:
            if cell in run:
                for cc in run:
                    if cc != cell and cc in fill:
                        used.add(fill[cc])
        choices = [d for d in range(1, 10) if d not in used]
        if not choices:
            return None
        fill[cell] = rng.choice(choices)
    # enforce distinctness inside every run (repair pass, simple resample)
    for run in runs:
        vals = [fill[c] for c in run]
        if len(set(vals)) != len(vals):
            return None
    def make_puz(fill):
        return {'runs': [{'cells': run, 'sum': sum(fill[c] for c in run)} for run in runs]}
    # adaptive verification: the propagation solver must crack it fully
    rep = solve_propagation(make_puz(fill))
    if rep['full']:
        return make_puz(fill), fill, rep
    return None

def try_build(n, seed):
    rng = random.Random(seed)
    return build_puzzle(n, rng)

if __name__ == '__main__':
    ok = 0
    for seed in range(60):
        res = try_build(4, seed)
        if res:
            ok += 1
    print(f'entry-seeded paired 4x4: full skeleton {ok}/60')
