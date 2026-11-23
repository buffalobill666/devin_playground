"""Frames, GIFs and charts for petri runs."""
import csv
from pathlib import Path

import numpy as np
from PIL import Image

from . import genome as gm


def frame(world, pos, genomes):
    """RGB uint8 image of the world (grid resolution)."""
    size = world.size
    img = np.zeros((size, size, 3), np.uint8)
    g = (world.food / world.food_max * 120).astype(np.uint8)
    img[..., 1] = g
    if len(pos):
        ix = pos[:, 0].astype(np.int32) % size
        iy = pos[:, 1].astype(np.int32) % size
        tr = np.clip(gm.traits(genomes) * 255, 40, 255).astype(np.uint8)
        img[iy, ix] = tr
    return img


def eco_frame(sim):
    """RGB image of the two-species world: prey tinted by traits,
    predators bright red."""
    from .eco import PREY_S, PRED_S, O
    w = sim.world
    img = np.zeros((w.size, w.size, 3), np.uint8)
    img[..., 1] = (w.food / w.food_max * 120).astype(np.uint8)
    if w.land is not None:
        img[w.land == 0] = (10, 25, 70)            # water
        img[..., 2] = np.maximum(img[..., 2],
                                 (w.shelter * 90).astype(np.uint8))
    if getattr(sim, 'grass', None) is not None and sim.grass.max() > 0:
        img[..., 1] = np.maximum(
            img[..., 1],
            (sim.grass / max(sim.grass.max(), 1) * 70).astype(np.uint8))
    if len(sim.prey):
        ix, iy = sim.prey.cells(w.size)
        tr = np.clip(gm.traits(sim.prey.genomes, PREY_S * O) * 255,
                     40, 255).astype(np.uint8)
        # R=speed G=appetite B=vigilance — grazers read as cool pastels
        img[iy, ix] = tr[:, [0, 1, 3]]
    if len(sim.pred):
        ix, iy = sim.pred.cells(w.size)
        tr = gm.traits(sim.pred.genomes, PRED_S * O)
        red = np.stack([np.full(len(tr), 255),
                        (tr[:, 1] * 120).astype(int),
                        np.zeros(len(tr))], 1).astype(np.uint8)
        img[iy, ix] = red
    return img


def save_frame(img, path, scale=4):
    im = Image.fromarray(img)
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(path)


def make_gif(frames_dir, out_path, scale=4, duration=60):
    files = sorted(Path(frames_dir).glob('*.png'))
    if not files:
        return None
    ims = [Image.open(f).convert('P', palette=Image.ADAPTIVE) for f in files]
    if scale != 1:
        ims = [im.resize((im.width * scale, im.height * scale), Image.NEAREST)
               for im in ims]
    ims[0].save(out_path, save_all=True, append_images=ims[1:],
                duration=duration, loop=0)
    return out_path


def write_metrics_csv(log, path):
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(log[0].keys()))
        w.writeheader()
        w.writerows(log)


def charts(log, out_path, title='petri run'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    t = [m['tick'] for m in log]
    fig, ax = plt.subplots(3, 1, figsize=(10, 11), sharex=True)
    fig.suptitle(title)

    ax[0].plot(t, [m['pop'] for m in log], label='population')
    ax[0].plot(t, [m['families'] for m in log], label='families', alpha=.7)
    ax0b = ax[0].twinx()
    ax0b.plot(t, [m['births'] for m in log], color='g', alpha=.3, label='births')
    ax0b.plot(t, [m['deaths'] for m in log], color='r', alpha=.3, label='deaths')
    ax[0].legend(loc='upper left')
    ax0b.legend(loc='upper right')
    ax[0].set_ylabel('count')

    ax[1].plot(t, [m['food'] for m in log], color='seagreen')
    ax[1].set_ylabel('total food')

    for k in ('speed', 'appetite', 'efficiency'):
        ax[2].plot(t, [m[k] for m in log], label=k)
    ax[2].plot(t, [m['energy'] for m in log], label='energy/100',
               alpha=.5, ls='--')
    ax[2].set_ylim(0, 1.05)
    ax[2].set_ylabel('mean trait')
    ax[2].set_xlabel('tick')
    ax[2].legend(loc='upper right')

    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return out_path


def eco_charts(log, out_path, title='eco run', real=None):
    """real: optional (years, counts, ticks_per_year, label) overlay."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    t = [m['tick'] for m in log]
    fig, ax = plt.subplots(4, 1, figsize=(11, 14), sharex=True)
    fig.suptitle(title)

    ax[0].plot(t, [m['pop_prey'] for m in log], color='steelblue',
               label='prey')
    if real:
        years, counts, tpy, label = real
        ax[0].plot([(y - years[0]) * tpy for y in years], counts,
                   'ko--', ms=5, lw=1, label=label, zorder=5)
    ax0b = ax[0].twinx()
    ax0b.plot(t, [m['pop_pred'] for m in log], color='firebrick',
              label='predators')
    ax[0].legend(loc='upper left')
    ax0b.legend(loc='upper right')
    ax[0].set_ylabel('prey')
    ax0b.set_ylabel('predators')

    ax[1].plot(t, [m['b_prey'] for m in log], color='steelblue',
               alpha=.4, label='prey births')
    ax[1].plot(t, [m['d_prey'] for m in log], color='navy', alpha=.4,
               label='prey deaths')
    ax[1].plot(t, [m['b_pred'] for m in log], color='salmon',
               alpha=.7, label='pred births')
    ax[1].plot(t, [m['d_pred'] for m in log], color='firebrick',
               alpha=.7, label='pred deaths')
    ax[1].plot(t, [m['food'] for m in log], color='seagreen',
               alpha=.3, label='food')
    if 'grass' in log[0] and max(m['grass'] for m in log) > 0:
        ax[1].plot(t, [m['grass'] for m in log], color='yellowgreen',
                   alpha=.5, label='grass')
    if 'infected' in log[0] and max(m['infected'] for m in log) > 0:
        ax[1].plot(t, [m['infected'] for m in log], color='purple',
                   alpha=.6, label='infected')
        ax[1].plot(t, [m['d_disease'] for m in log], color='magenta',
                   alpha=.6, ls='--', label='disease deaths')
    if 'storm' in log[0]:
        ax[1].fill_between(t, 0, 1,
                           where=[bool(m['storm']) for m in log],
                           transform=ax[1].get_yaxis_transform(),
                           color='lightsteelblue', alpha=.4,
                           label='storm')
    ax[1].set_ylabel('per log step')
    ax[1].legend(fontsize=7)

    for k in ('speed', 'appetite', 'efficiency', 'vigilance'):
        if f'prey_{k}' in log[0]:
            ax[2].plot(t, [m[f'prey_{k}'] for m in log], label=k)
    if 'prey_resist' in log[0]:
        ax[2].plot(t, [m['prey_resist'] for m in log], color='teal',
                   lw=2, label='resist')
    if 'virulence' in log[0] and max(m['virulence'] for m in log) > 0:
        ax[2].plot(t, [m['virulence'] for m in log], color='purple',
                   ls='-.', lw=2, label='virulence')
    if 'prey_disp' in log[0]:
        ax[2].plot(t, [m['prey_disp'] for m in log], ls='--',
                   color='black', alpha=.5, label='dispersion')
    ax[2].set_ylim(0, 1.05)
    ax[2].set_ylabel('prey mean trait')
    ax[2].legend(fontsize=7)

    for k in ('speed', 'ferocity', 'efficiency', 'sense'):
        ax[3].plot(t, [m[f'pred_{k}'] for m in log], label=k)
    if 'pred_disp' in log[0]:
        ax[3].plot(t, [m['pred_disp'] for m in log], ls='--',
                   color='black', alpha=.5, label='dispersion')
    ax[3].plot(t, [m['pop_pred'] / 1000 for m in log],
               ls=':', color='gray', alpha=.5, label='pop/1000')
    ax[3].set_ylim(0, 1.05)
    ax[3].set_ylabel('pred mean trait')
    ax[3].set_xlabel('tick')
    ax[3].legend(fontsize=7)

    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return out_path
