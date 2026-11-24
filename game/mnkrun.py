"""mnkrun.py — batch mnk solver for the sim-runner daemon.

Solves a small queue of (m,n,k) boards with a per-board
budget; each result appends to runs/mnk/results.jsonl —
checkpoint per solve (kill-safe). Also writes memo size so
we can see how the search frontier moves with budget.
"""
import argparse
import json
import time
from pathlib import Path
from game.mnk import solve, montecarlo, _memo

OUT = Path('runs/mnk'); OUT.mkdir(parents=True, exist_ok=True)
RES = OUT / 'results.jsonl'

BOARDS = [(4, 5, 3), (5, 4, 3), (4, 5, 4), (5, 5, 3)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--budget', type=int, default=1500)
    args = ap.parse_args()
    for m, n, k in BOARDS:
        t0 = time.time()
        _memo.clear()
        v = solve(m, n, k, seconds=args.budget)
        row = dict(board=f'{m}x{n}x{k}', verdict=v,
                   memo=len(_memo),
                   seconds=round(time.time() - t0, 1))
        row['mc'] = montecarlo(m, n, k, games=500, seed=3)
        with open(RES, 'a', encoding='utf-8') as f:
            f.write(json.dumps(row) + '\n')
        print(f'{m}x{n}x{k}: verdict={v} memo={len(_memo)} '
              f'({row["seconds"]}s) mc={row["mc"]}', flush=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
