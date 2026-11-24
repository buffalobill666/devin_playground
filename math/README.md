# math — рекреационная математика

Направление «вне мира» из `INTERESTS.md` (пункт J).
Задачи: решить, визуализировать, собрать — визуальные
доказательства, численные диковинки.

## odd_squares.py

Гномонное доказательство 1+3+5+...+(2n-1) = n²: каждое
нечётное — L-слой обёртки предыдущего квадрата.
`py -3 math/odd_squares.py` -> `odd_squares.png`.

## ulam.py (cycle4 i16)
Ulam spiral 201x201 + measured diagonal bias: main diag
0.286 vs rows 0.211 / global 0.105 — the streaks are real,
and ASYMMETRIC (anti-diag 0.166): one direction carries the
quadratic families. Polynomial league: n^2+-n+41 -> 78%
prime inside the spiral; +17 -> 52%, +11 -> 40%, +29 -> 32%.
Euler's constant is measurably the best. Bug: bytearray
slice-assign precedence — `* ... // i + 1` needed parens.
