"""CLI entry: run a petri experiment and dump artifacts to runs/<name>-<ts>/.

Usage (from devin_playground/):
    python -m petri.run --name baseline --ticks 20000          # grazers only
    python -m petri.run --eco --name royale --ticks 20000      # + predators, sex
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from .sim import Sim, DEFAULTS
from . import render

# Parameter presets emulating real documented cases.
# Values are order-of-magnitude analogies, not fitted constants —
# documented in history.md alongside sources.
PRESETS = {
    # St. Matthew Island reindeer (Klein 1968; Miller & Barry 2005):
    # 29 introduced 1944 -> 6000 by 1963 -> crash to 42 by 1966, gone ~1985.
    # No predators, isolated island (no immigration), slow lichen regrowth,
    # sexual reproduction, rare severe winters.
    'stmatthew': dict(
        prey_start=29, pred_start=0,
        prey_start_cluster=10,   # released as one tight group, like 1944
        prey_start_energy=90.0,  # healthy yearlings — fertile at once
        prey_founder_bias=1.0,   # real animals have working brains
        prey_reseed_below=0, pred_reseed_below=0,
        regrowth=0.008, food_init=0.8, food_floor=0.3,
        food_energy=4.0, bite_max=3.0,  # lichen is energy-rich forage
        # "sedges & grasses expanded into sites previously occupied by
        # lichens" (Klein 1968) — fast, lean fallback forage:
        grass_regrowth=0.05, grass_max=6.0, grass_energy=1.5,
        grass_floor=0.2, grass_init=0.5,
        prey_mate_block=4, prey_cap=8000,
        prey_repro_urge=0.5,     # near-universal drive, like real reindeer
        season_amp=0.25, season_period=1200,
        storm_period=3500, storm_len=400,
        storm_regrowth=0.05, storm_cost=3.0,
        prey_age_max=4500,
        # real geography: bounded island + shelter valleys where some
        # animals survived the storm (the actual 42 did)
        island_radius=0.42, island_rough=0.15,
        shelter_n=10, shelter_radius=20.0,
    ),
    # Density-driven epidemic: the pathogen as a third coevolving actor.
    # Virulence lives inside carriers and mutates on transmission;
    # prey evolve 'resist'. No storms — crashes must be endogenous.
    'epidemic': dict(
        disease=0.35, disease_intro=0.002,
        disease_cost=0.6, disease_mort=0.02, disease_recover=0.03,
        disease_mut=0.08, disease_vert=0.4,
    ),
    # Same world, but lethality is quadratic in virulence — hot strains
    # burn their host out before spreading. Tests whether virulence
    # then evolves to an interior optimum (moderation).
    'epidemic2': dict(
        disease=0.35, disease_intro=0.002,
        disease_cost=0.6, disease_mort=0.04, disease_mort_exp=2.0,
        disease_recover=0.03, disease_mut=0.08, disease_vert=0.4,
    ),
}


def main():
    import sys
    preset = None
    if '--preset' in sys.argv:
        i = sys.argv.index('--preset')
        preset = sys.argv[i + 1]
        del sys.argv[i:i + 2]
    p = argparse.ArgumentParser(prog='petri')
    p.add_argument('--eco', action='store_true',
                   help='two-trophic world: predators + sexual reproduction')
    p.add_argument('--name', default='run')
    p.add_argument('--ticks', type=int, default=20000)
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--frame-every', type=int, default=100)
    p.add_argument('--ticks-per-year', type=int, default=300,
                   help='tick->year scale for real-data overlays')
    p.add_argument('--out', default='runs')
    for key, default in DEFAULTS.items():
        p.add_argument(f'--{key.replace("_", "-")}', type=type(default),
                       default=default)
    from .eco import DEFAULTS as ECO_DEFAULTS
    for key, default in ECO_DEFAULTS.items():
        if key not in DEFAULTS:
            p.add_argument(f'--{key.replace("_", "-")}', type=type(default),
                           default=default)
    args = p.parse_args()

    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    out = Path(args.out) / f'{args.name}-{stamp}'
    frames = out / 'frames'
    frames.mkdir(parents=True)

    if args.eco:
        from .eco import EcoSim
        cfg = {k: getattr(args, k) for k in ECO_DEFAULTS}
        if preset:
            cfg.update(PRESETS[preset])
        sim = EcoSim(cfg, seed=args.seed)
    else:
        cfg = {k: getattr(args, k) for k in DEFAULTS}
        sim = Sim(cfg, seed=args.seed)

    with open(out / 'config.json', 'w') as fh:
        json.dump({'cfg': cfg, 'seed': args.seed, 'ticks': args.ticks,
                   'name': args.name, 'eco': args.eco}, fh, indent=2)

    t0 = time.time()

    def on_tick(s):
        if s.world.tick % args.frame_every == 0:
            render.save_frame(render.eco_frame(s) if args.eco else
                              render.frame(s.world, s.pos, s.genomes),
                              frames / f'{s.world.tick:06d}.png')
        if s.world.tick % 1000 == 0:
            if args.eco:
                print(f'tick {s.world.tick:>6}  prey={len(s.prey):>5}  '
                      f'pred={len(s.pred):>4}  '
                      f'food={s.world.food.sum():>9.0f}  '
                      f'({time.time() - t0:.0f}s)', flush=True)
            else:
                print(f'tick {s.world.tick:>6}  pop={s.n:>5}  '
                      f'food={s.world.food.sum():>9.0f}  '
                      f'({time.time() - t0:.0f}s)', flush=True)

    sim.run(args.ticks, on_tick)

    render.write_metrics_csv(sim.log, out / 'metrics.csv')
    title = f'{args.name} seed={args.seed}'
    if args.eco:
        real = None
        if preset == 'stmatthew':
            import csv as _csv
            with open('data/stmatthew.csv') as fh:
                rows = [r for r in _csv.reader(fh) if r and not
                        r[0].startswith('#')]
            years = [int(r[0]) for r in rows[1:]]
            counts = [float(r[1]) for r in rows[1:]]
            real = (years, counts, getattr(args, 'ticks_per_year', 300),
                    'real reindeer')
        render.eco_charts(sim.log, out / 'charts.png', title=title,
                          real=real)
    else:
        render.charts(sim.log, out / 'charts.png', title=title)
    render.make_gif(frames, out / 'world.gif')
    if args.eco:
        import numpy as _np
        _np.savez(out / 'genomes.npz',
                  prey=sim.prey.genomes, pred=sim.pred.genomes,
                  prey_family=sim.prey.family, pred_family=sim.pred.family,
                  prey_pos=sim.prey.pos, pred_pos=sim.pred.pos)
    last = sim.log[-1] if sim.log else {}
    if args.eco:
        summary = {
            'ticks': args.ticks, 'final_prey': len(sim.prey),
            'final_pred': len(sim.pred),
            'b_prey': sim.b_prey, 'd_prey': sim.d_prey,
            'b_pred': sim.b_pred, 'd_pred': sim.d_pred,
            'elapsed_s': round(time.time() - t0, 1), 'last': last,
        }
    else:
        summary = {
            'ticks': args.ticks, 'final_pop': sim.n,
            'births_total': sim.births, 'deaths_total': sim.deaths,
            'elapsed_s': round(time.time() - t0, 1), 'last': last,
        }
    with open(out / 'summary.json', 'w') as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))
    print(f'artifacts -> {out}')


if __name__ == '__main__':
    main()
