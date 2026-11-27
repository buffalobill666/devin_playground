"""Render a skeleton-puzzle JSON to human-solvable HTML.

Kakuro-style: thick borders at run boundaries, clue numbers in the corner
of each run's first cell (across clues top-left, down clues top-right).
"""
import json, html

def load(path):
    return json.load(open(path, encoding='utf-8'))

def analyze(puz):
    n = puz['grid_size']
    runs = [([(c[0], c[1]) for c in r['cells']], r['sum']) for r in puz['runs']]
    across = [x for x in runs if len(set(c[0] for c in x[0])) == 1]
    down = [x for x in runs if len(set(c[1] for c in x[0])) == 1]
    # boundaries: for each cell, whether right/bottom neighbor is in same run
    same_right, same_down = {}, {}
    clues = {}
    for cells, s in across:
        first = cells[0]
        clues.setdefault(first, {})['across'] = s
        for a, b in zip(cells, cells[1:]):
            same_right[a] = True
    for cells, s in down:
        first = cells[0]
        clues.setdefault(first, {})['down'] = s
        for a, b in zip(cells, cells[1:]):
            same_down[a] = True
    return n, across, down, same_right, same_down, clues

def render_html(puz, title=None):
    n, across, down, same_right, same_down, clues = analyze(puz)
    rows = []
    for r in range(n):
        tds = []
        for c in range(n):
            cls = []
            style = []
            if not same_right.get((r, c)) and c < n - 1:
                style.append('border-right:3px solid #222')
            if not same_down.get((r, c)) and r < n - 1:
                style.append('border-bottom:3px solid #222')
            cl = clues.get((r, c), {})
            clue_html = ''
            if 'across' in cl:
                clue_html += f'<span class="ca">{cl["across"]}</span>'
            if 'down' in cl:
                clue_html += f'<span class="cd">{cl["down"]}</span>'
            tds.append(f'<td style="{";".join(style)}">{clue_html}<span class="val"></span></td>')
        rows.append('<tr>' + ''.join(tds) + '</tr>')
    grid = '<table>' + ''.join(rows) + '</table>'
    t = html.escape(title or puz.get('title', 'kakuro'))
    return f'''<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>{t}</title>
<style>
body {{ font-family: Georgia, serif; background: #f5f1e8; padding: 2em; color: #222 }}
table {{ border-collapse: collapse; margin: 1.5em 0; background: #fff }}
td {{ width: 64px; height: 64px; border: 1px solid #999; position: relative;
     vertical-align: middle; text-align: center; font-size: 28px }}
td {{ position: relative }}
.ca {{ position: absolute; top: 2px; left: 4px; font-size: 12px; color: #456; font-weight: bold }}
.cd {{ position: absolute; top: 2px; right: 4px; font-size: 12px; color: #645; font-weight: bold }}
.legend {{ font-size: 14px; color: #555; max-width: 560px; line-height: 1.5 }}
h1 {{ font-size: 22px }}
</style></head><body>
<h1>{t}</h1>
<p class="legend">Каждая клетка — цифра 1–9; внутри одного пробега цифры не повторяются.
Левое верхнее число (синее) — сумма горизонтального пробега вправо,
правое верхнее (лиловое) — сумма вертикального вниз.
Жирные линии — границы пробегов.</p>
{grid}
<details><summary>Решение (не подглядывать)</summary><pre>{solution_grid(puz)}</pre></details>
</body></html>'''

def solution_grid(puz):
    n = puz['grid_size']
    sol = puz['solution']
    lines = []
    for r in range(n):
        lines.append(' '.join(str(sol[f'{r},{c}']) for c in range(n)))
    return '\n'.join(lines)

if __name__ == '__main__':
    puz = load('puzzles/k1-first-skeleton.json')
    out = render_html(puz, 'Какуро «Первый скелет» — k1')
    open('puzzles/k1.html', 'w', encoding='utf-8').write(out)
    print('written puzzles/k1.html')
    # sanity: run counts
    n, across, down, *_ = analyze(puz)
    print(f'{len(across)} across runs, {len(down)} down runs, grid {n}x{n}')
