"""CLI: python -m creatures.drun --gens 40 --pop 32 --seed 1 --name devo"""
import argparse
import time
from datetime import datetime
from pathlib import Path


def main():
    p = argparse.ArgumentParser(prog='devo')
    p.add_argument('--gens', type=int, default=30)
    p.add_argument('--pop', type=int, default=32)
    p.add_argument('--steps', type=int, default=800)
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--name', default='devo')
    p.add_argument('--record', type=int, nargs='*', default=())
    p.add_argument('--hills', action='store_true',
                   help='evolve on rolling terrain (physics.hills)')
    p.add_argument('--reflex', action='store_true',
                   help='enable REFLEX genes (sensorimotor loop)')
    p.add_argument('--seek', type=float, default=0.0,
                   help='target-seeking task at +-X (enables SENSE genes)')
    p.add_argument('--dwell', nargs='?', const='min', default=False,
                   choices=('min', 'sum', 'combo', True),
                   help='dwell scoring mode: min=worst trial, '
                        'sum=both trials, combo=travel+dwell')
    p.add_argument('--seed-champ', default=None, metavar='PATH',
                   help='npy file with champion DNA to seed half '
                        'the initial population from')
    p.add_argument('--fade', type=int, default=None, metavar='N',
                   help='food signal dies after N steps (memory task)')
    p.add_argument('--flip', type=int, default=None, metavar='N',
                   help='food jumps to the mirror side at step N '
                        '(rewrite-memory task)')
    args = p.parse_args()

    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    out = Path('runs') / f'{args.name}-{stamp}'
    from .devo import devolve
    from . import physics
    seed_seq = None
    if args.seed_champ:
        import numpy as np
        seed_seq = np.load(args.seed_champ)
    t0 = time.time()
    best, fit, log = devolve(pop_size=args.pop, gens=args.gens,
                             steps=args.steps, seed=args.seed, out=out,
                             record_gens=set(args.record),
                             terrain=physics.hills if args.hills else None,
                             n_types=8 if args.seek else
                             (6 if args.reflex else 5),
                             seek=args.seek or None,
                             dwell=args.dwell, seed_seq=seed_seq,
                             fade_at=args.fade, flip_at=args.flip)
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from petri.render import make_gif
    for d in sorted(out.glob('gen*')):
        make_gif(d, out / f'{d.name}.gif', scale=1, duration=70)
    print(f'done: best_fitness={fit:.3f} elapsed={time.time()-t0:.0f}s')
    print(f'artifacts -> {out}')


if __name__ == '__main__':
    main()
