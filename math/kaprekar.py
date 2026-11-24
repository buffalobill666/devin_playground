"""kaprekar.py — доказательство константы Капрекара перебором + воронка.

Факт (Kaprekar, 1949): для любого 4-значного числа с неодинаковыми
цифрами итерация D(n) = desc(n) - asc(n) сходится к 6174 не более
чем за 7 шагов. Доказательство — исчерпывающее: 8991 кандидат,
все проверены. Воронка: колонки = глубина, узлы = различные значения
на этой глубине (размер = сколько чисел через них проходит),
рёбра = переход D(n) -> n'. Сильный вывод одной картинкой:
вся вселенная 4-значных чисел — река с одной дельтой.
"""

from collections import Counter, defaultdict

from PIL import Image, ImageDraw, ImageFont


def step(n):
    """D(n): цифры по убыванию минус по возрастанию, 4 позиции."""
    d = f'{n:04d}'
    return int(''.join(sorted(d, reverse=True))) - int(''.join(sorted(d)))


def depth(n):
    k, seen = 0, n
    while seen != 6174:
        seen = step(seen)
        k += 1
    return k


# ---------------- перебор: доказательство ---------------- #

cands = [n for n in range(1000, 10000) if len(set(f'{n:04d}')) > 1]
depths = {}
flows = []                        # цепочки значений для воронки
for n in cands:
    chain, m = [n], n
    while m != 6174:
        m = step(m)
        chain.append(m)
    depths[n] = len(chain) - 1
    flows.append(chain)

maxd = max(depths.values())
dist = Counter(depths.values())
levels = defaultdict(Counter)     # глубина -> {значение: число стекающих}
edges = Counter()                 # (a, b) -> поток
for chain in flows:
    for i, v in enumerate(chain):
        levels[i][v] += 1
        if i + 1 < len(chain):
            edges[(v, chain[i + 1])] += 1

# сходимость гарантирована завершением depth()/chain: цикл выходит
# только на 6174 — осталось проверить покрытие и глубину
ok = len(depths) == len(cands) and maxd <= 7
print(f'кандидатов: {len(cands)}, все -> 6174: {ok}')
print(f'макс. глубина: {maxd}')
print('распределение шагов:', dict(sorted(dist.items())))
print('узлов на уровнях:', {i: len(levels[i]) for i in sorted(levels)})

# ---------------- воронка ---------------- #

W, H, PAD = 1500, 900, 80
L = maxd + 1
im = Image.new('RGB', (W, H), '#10121a')
dr = ImageDraw.Draw(im)
try:
    fnt = ImageFont.truetype('DejaVuSans.ttf', 15)
    fnt_sm = ImageFont.truetype('DejaVuSans.ttf', 12)
except OSError:
    fnt = fnt_sm = ImageFont.load_default()

colw = (W - 2 * PAD) / maxd
col_x = {i: PAD + i * colw for i in range(L)}

# позиции узлов: внутри колонки по вертикали, отсортированы по значению;
# уровень 0 — не узлы а сплошная лента (8991 точку нарисовать нельзя)
pos = {}
rad = {}
vlevel = {}
for i in range(L):
    for v in levels[i]:
        vlevel[v] = i
    if i == 0:
        continue
    vals = sorted(levels[i])
    for j, v in enumerate(vals):
        y = PAD + (H - 2 * PAD) * (j + 0.5) / len(vals)
        pos[v] = (col_x[i], y)
        rad[v] = 2 + 9 * (levels[i][v] / len(cands)) ** 0.35

# лента уровня 0: площадь колонки = вся популяция
dr.rectangle([col_x[0] - 8, PAD, col_x[0] + 8, H - PAD],
             fill='#2a3f66', outline='#8ecae6')

# рёбра: полупрозрачные сегменты, толщина ~ поток; из уровня 0 —
# единый суммарный поток на каждый узел уровня 1 (иначе — стена)
maxfl = max(edges.values())
for (a, b), fl in edges.items():
    if vlevel[a] == 0:
        x1, y1 = col_x[0] + 8, pos[b][1]
        x2, y2 = pos[b]
        dr.line([x1, y1, x2, y2], fill=(50, 70, 110), width=1)
        continue
    x1, y1 = pos[a]
    x2, y2 = pos[b]
    w = 1 + 4 * fl / maxfl
    t = fl / maxfl
    col = (60 + int(140 * t), 90 + int(120 * t), 160 + int(60 * t))
    dr.line([x1, y1, x2, y2], fill=col, width=max(1, int(w)))

# узлы (уровни 1..maxd)
for i in range(1, L):
    for v, cnt in levels[i].items():
        x, y = pos[v]
        r = rad[v]
        sink = (v == 6174)
        c = '#ffd166' if sink else '#8ecae6'
        dr.ellipse([x - r, y - r, x + r, y + r], fill=c,
                   outline='#ffffff' if sink else None, width=2 if sink else 0)
        if v == 6174 or cnt > len(cands) * 0.06:
            dr.text((x - 14, y - r - 16), str(v), fill='#ffffff', font=fnt_sm)

# подписи колонок
for i in range(L):
    n_nodes = len(levels[i])
    lab = f'{i} шаг' if i else f'старт ({len(cands)})'
    dr.text((col_x[i] - 18, H - PAD + 24), lab, fill='#888899', font=fnt)
    dr.text((col_x[i] - 14, H - PAD + 44), f'{n_nodes} узл.',
            fill='#555566', font=fnt_sm)
dr.text((PAD, 26), 'KAPREKAR FUNNEL — every 4-digit number flows to 6174',
        fill='#e8e8f0', font=fnt)
dr.text((PAD, 48), 'columns = iterations of D(n), nodes = distinct values, '
                   'thickness = count', fill='#888899', font=fnt_sm)
im.save('math/kaprekar.png')
print('math/kaprekar.png')
print('VERDICT:', 'OK' if ok and maxd <= 7 else 'FAIL')
