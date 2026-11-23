"""autonomy.py — страж итерационного цикла для Stop-хука.

Вызывается Stop-хуком каждый раз, когда агент решает остановиться.
Если `.devin/autonomous.flag` существует — блокирует остановку и
возвращает агента к работе. Предохранители:

- флаг-файл = ручной выключатель (удалил — цикл кончился)
- счётчик итераций: после MAX цикл сам снимает флаг

Выход на stdout: ничего (разрешить остановку) или JSON
{"decision": "block", "reason": "..."}.
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
FLAG = os.path.join(BASE, 'autonomous.flag')
COUNT = os.path.join(BASE, 'iterations.txt')
MAX = 15

if not os.path.exists(FLAG):
    sys.exit(0)

n = 0
if os.path.exists(COUNT):
    try:
        n = int(open(COUNT, encoding='utf-8').read().strip() or 0)
    except ValueError:
        n = 0
n += 1

if n > MAX:
    os.remove(FLAG)
    if os.path.exists(COUNT):
        os.remove(COUNT)
    sys.exit(0)

with open(COUNT, 'w', encoding='utf-8') as f:
    f.write(str(n))

print(json.dumps({
    'decision': 'block',
    'reason': (
        f'Autonomous iteration {n}/{MAX}. Choose work yourself: pull a '
        'thread from INTERESTS.md or continue an open direction. If '
        'blocked on something only the host can do, note it in history.md '
        'and switch to a different pursuit. Document everything in '
        'history.md; commit milestones. Host can end the loop by deleting '
        '.devin/autonomous.flag.'
    ),
}))
