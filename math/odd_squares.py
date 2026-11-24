"""odd_squares.py — визуальное доказательство: 1+3+5+...+(2n-1) = n^2.

Гномонная картинка: каждое нечётное число — L-образный слой,
который оборачивает предыдущий квадрат. Без слов: площадь слоёв
складывается в квадрат n x n.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mp

N = 7
COLORS = ['#e8e3d5', '#d4a94e', '#c97b4a', '#9b5de5',
          '#5b8c5a', '#4a7fbf', '#d1495b']


def draw(n, path):
    fig, ax = plt.subplots(figsize=(7, 7))
    for r in range(n):
        for c in range(n):
            k = max(r, c)  # номер гномона (0-индекс): слой k имеет 2k+1 клеток
            ax.add_patch(mp.Rectangle((c, n - 1 - r), 1, 1,
                                      facecolor=COLORS[k % len(COLORS)],
                                      edgecolor='white', lw=2))
            # подписываем размер гномона один раз — в угловой клетке
            if r == k and c == k:
                ax.text(c + 0.5, n - 1 - r + 0.5, str(2 * k + 1),
                        ha='center', va='center', fontsize=16,
                        fontweight='bold', color='#1a263f')
    ax.set_xlim(-0.05, n + 0.05)
    ax.set_ylim(-0.05, n + 0.05)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'1 + 3 + 5 + ... + {2 * n - 1}  =  {n}²  =  {n * n}',
                 fontsize=18, color='#1a263f', pad=16)
    fig.patch.set_facecolor('#f4f0e8')
    fig.savefig(path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    print('saved', path)


if __name__ == '__main__':
    draw(N, 'math/odd_squares.png')
