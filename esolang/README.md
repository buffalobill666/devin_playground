# esolang — язык как произведение

Направление «рядом с миром» из `INTERESTS.md` (пункт 3).
Пара к Flick (proglang/): тот — инструмент, этот — объект.

## subleq.py

OISC — one instruction set computer. Единственная
инструкция: `subleq a b c` = mem[b] -= mem[a]; if ≤0 goto c.
Тьюринг-полна. Мини-ассемблер с метками (~20 строк),
машина (~10 строк). Демо: 6×7=42 через повторное сложение,
36 шагов, VERDICT: OK.

Идиомы: сложение — два вычитания через Z; JMP — `Z Z c`;
HALT — прыжок в -1; тест X≤0 — `Z X c` (X не меняется).

**Следующее:** hello world на subleq (I/O-ячейки) или
эзолэнг другого типа — двумерный / очередевый.

## senex.py

SENEX — язык, где программа стареет (концептуальный эзолэнг
по нити Temkin). Исполнение инструкции стоит ей 1 жизнь;
на нуле — NOP. RENEW чинит чужую клетку, но сам платит.

**Теорема SENEX** (доказана конструкцией + эмпирикой):
вечной жизни нет — клетке нужен свой RENEW, RENEW сам
стареет, регресс покрытия бесконечен. Ремонт = отсрочка:
слой обслуживания прогорает первым, тело — следующим сроком.
mortal 13 шагов vs cared 36 (life=3); 21 vs 60 (life=5).

Следующее: слои обслуживания 2-го порядка (RENEW чинит
RENEW'ы) — лифт лайфспана ~life на слой?

## migrate.py (SENEX-M)

Мигрирующие программы: диалект COPY/MJMP, кольцо буферов.
Вторая теорема: бессмертная линия <=> стерильная линия —
покрытие T клеток требует T записей, значит каждая клетка
обязана копировать. Линия мигрантов бессмертна, но сбрасывает
все рабочие клетки в первом же поколении (0-1 принт работы
на 400 поколений). Зародшевая линия в коде.

## senex_work.py (cycle4 i15)
SENEX economics. Law verified on 20 more points: k=1..10 x
life=2..8 — steps = 2*life*(k+1)*(k+2) EXACT (0% deviation);
k=0: steps = 4*life+1 (one init + 4 body cells x life).
Work output: prints = life*(k+1) — marginal print per cell
is constant life/4 = 1.25: maintenance is a LINEAR ANNUITY,
no interior optimum, no diminishing returns in this regime.
Partial-coverage 'lean' tail: strictly dominated — same
cell count, less lifespan (coverage must be total; the
uncovered-tail lesson confirmed from the other side).
