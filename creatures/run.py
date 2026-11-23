"""CLI: python -m creatures.run --gens 40 --pop 32 --seed 1 --name evo"""
import argparse
import time
from datetime import datetime
from pathlib import Path


def main():
    p = argparse.ArgumentParser(prog='creatures')
    p.add_argument('--gens', type=int, default=30)
    p.add_argument('--pop', type=int, default=32)
    p.add_argument('--steps', type=int, default=800)
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--mut', type=float, default=0.10)
    p.add_argument('--name', default='evo')
    p.add_argument('--record', type=int, nargs='*', default=(),
                   help='generations to render best-creature frames')
    args = p.parse_args()

    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    out = Path('runs') / f'{args.name}-{stamp}'
    from .evo import evolve
    t0 = time.time()
    best, fit, log = evolve(pop_size=args.pop, gens=args.gens,
                            steps=args.steps, mut=args.mut,
                            seed=args.seed, out=out,
                            record_gens=set(args.record))
    # GIFs for any rendered generations
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from petri.render import make_gif
    gifs = []
    for d in sorted(out.glob('gen*')):
        g = make_gif(d, out / f'{d.name}.gif', scale=1, duration=70)
        if g:
            gifs.append(str(g))
    print(f'done: best_fitness={fit:.3f} elapsed={time.time()-t0:.0f}s')
    print(f'artifacts -> {out}')
    for g in gifs:
        print(' ', g)


if __name__ == '__main__':
    main()
