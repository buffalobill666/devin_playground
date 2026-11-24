# ciphers — классические шифры и машины

Направление «вне мира» из `INTERESTS.md` (пункт D).
Энигма, Vigenère, кодовые книги: симуляторы + взломщики.
Пока пусто — первый ход: Enigma I ~100 строк, исторический
тест-вектор.

## playfair.py

Диграфный шифр WWI: квадрат 5×5 по ключу, правила
строка/столбец/прямоугольник. Roundtrip OK. Честный
показатель силы: IC 0.0875 -> 0.0545 — частоты сплющены
к случайному (0.038), но зазор остаётся — за него и
ломается статистикой диграфов/квадрограмм.

## bombe.py (cycle3 i26)
Crib-атака: 60 порядков x 26³ позиций, ранний выход по
mismatch → 52с. Фаза 2: plugs восстанавливаются жадно —
top-кандидат с 10/15 (plugs портили 5 букв) всё равно
отрывается от следующих (5/15). Полный восстановленный
ключ: rotors+pos+plugs -> исходный plaintext.

## autokey.py (cycle4 i11)
Vigenere autokey (1586): keystream = primer + plaintext
itself. Two cracks: (1) primer dictionary — wordlist try,
LEMON found, exact decode; (2) avalanche — seed a common
tetragram at every offset, propagate the lag-L key chain,
score only DERIVED positions (a seed always looks English;
only evidence counts), letter margin over uniform baseline
so coverage is rewarded. Metric trap caught: raw log-freq
sum punishes coverage — correct lag scored -248 vs wrong
-92; baseline-margin scoring fixes it. Result: lag=5 found,
80% of plaintext recovered without knowing the primer.
