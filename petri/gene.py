"""Inspect evolved genome weights: which senses drive movement?

Usage: python -m petri.gene runs/herd-*/genomes.npz
"""
import sys
import numpy as np

from .eco import PREY_S, PRED_S, O, T

PREY_SENSES = ['bias', 'food', 'fgx', 'fgy', 'crowd', 'energy', 'noise',
               'pred_gx', 'pred_gy', 'own_gx', 'own_gy']
PRED_SENSES = ['bias', 'prey_dens', 'prey_gx', 'prey_gy', 'crowd',
               'energy', 'noise']
OUTS = ['move_x', 'move_y', 'act', 'repro']
TRAITS = ['t0', 't1', 't2', 't3']


def report(name, g, senses):
    n_out = O
    w = g[:, :len(senses) * n_out].reshape(-1, len(senses), n_out)
    print(f'\n== {name} ({len(g)} genomes) ==')
    print('mean |W| to move_xy per sense (|.| = strength used):')
    for i, s in enumerate(senses):
        m = w[:, i, :2]
        print(f'  {s:>10}: mean={m.mean():+.3f}  |mean|={np.abs(m).mean():.3f}'
              f'   (to mx {m[:,0].mean():+.3f}, my {m[:,1].mean():+.3f})')


def main(path):
    z = np.load(path)
    report('prey', z['prey'], PREY_SENSES)
    report('pred', z['pred'], PRED_SENSES)


if __name__ == '__main__':
    main(sys.argv[1])
