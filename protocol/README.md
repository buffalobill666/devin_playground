# protocol — протокол и модель данных

Направление «вне мира» из `INTERESTS.md` (пункт I),
предложено хозяином. Свой формат: фрейминг, CRC,
версионирование, самоописание — вещь со спекой.
Пока пусто — первый ход: спека пакета + экспортер/импортер.

## tornify.py — TORN на реальных данных

csv -> torn конвертер: schema-кадр + кадр на строку.
Прогон на runs/family/families.csv: 7773 записи, roundtrip
построчно идентичен, overhead x1.41. Порча одного байта
в середине -> потеряна РОВНО одна запись, ресинх после 152B
пропущенных. CSV при той же порче не читается дальше строки —
а с порчей разделителя ломается весь парсинг.

## torn3.py — TORN v0.3 (cycle4 i13)
TYPE BLOCK: N payloads zlib-packed in one record, seq-chain
semantics kept (block seq + count). Measured on 200 records:
3.5x smaller than v0.2; byte-flip mid-file loses exactly one
block (8 records) — compression trades loss granularity for
overhead, block size is the knob. Roundtrip identical.
