# font — шрифт

Направление «вне мира» из `INTERESTS.md` (пункт B).

## freqfont

`freqfont.py` — растровый шрифт, где **ширина буквы кодирует её
частоту в английском**: частые узкие (E,T,A,O → 4px), редкие
широкие (J,Q,X,Z → 6px). Как Морзе: частое получает короткий код.
Текст выравнивается по плотности — форма становится видимой
теорией информации.

Специмен: `specimen.png` (`py -3 font/freqfont.py`).

## lowercase (cycle3 i20)
26 глифов: x-height строки 2-6, восходящие 0-6, нисходящие 2-7.
Ширина по частоте буквы, регистр её не меняет — e и E одинаковы.
`glyph()` — регистро-сохраняющий поиск с fallback на верхний.

## connectfont.py (cycle4 i12)
Second font principle: glyphs are graphs. Each glyph = a
26-bar histogram of P(next|letter) — x-axis is the alphabet,
caret marks the letter's own index. Corpus: this repo's own
English prose (33k digraphs). Sanity: Q's argmax = U (56/62);
E spreads over 25/26 targets with R/S/D/N on top — the
shape of English adjacency is visible. `connectfont.png`.
