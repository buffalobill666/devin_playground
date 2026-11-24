"""bombe.py — crib-атака на Enigma: перебор + восстановление plugs.

Сценарий Блетчли: перехвачен шифротекст, известна криб
(обязательный фрагмент — «WETTER...» в прогнозе погоды).
Без коммутатора пространство = 60 порядков x 26^3 позиций
(кольца считаем известными/AAA, как в упрощённых атаках).
Настоящая бомба Тьюринга резала это меню-петлями; здесь —
честный перебор с ранним выходом по первому же mismatch.

Фаза 2 (самое интересное): plugboard добивается жадно —
для топ-кандидатов подбираем пары, чинящие оставшиеся
позиции криба. Plugs были главной защитой машины; показано,
как криб всё равно их раскалывает, когда часть букв нетронута.
"""

import itertools
import time

from enigma import Enigma, ALPH

ROT_NAMES = list('IIIIIIVV'[:5])          # I..V
ROT_NAMES = ['I', 'II', 'III', 'IV', 'V']


def decrypt_at(rotors, pos, ct, offset, n, reflector='B'):
    """Расшифровать n символов ct с позиции offset."""
    m = Enigma(rotors, reflector=reflector, pos=pos)
    for _ in range(offset):
        m.enc_char('A')                     # дойти до оффсета
    return m.enc(ct[offset:offset + n])


def phase1(ct, crib, offset, reflector='B', top=5):
    """Перебор orders x positions; счёт совпадений криба.
    Ранний выход: больше max_miss промахов подряд -> стоп."""
    hits = []
    max_miss = 2
    for order in itertools.permutations(ROT_NAMES, 3):
        for pos in itertools.product(range(26), repeat=3):
            m = Enigma(order, reflector=reflector, pos=pos)
            for _ in range(offset):
                m.enc_char('A')
            score = miss = 0
            for a, b in zip(crib, ct[offset:offset + len(crib)]):
                if m.enc_char(a) == b:
                    score += 1
                else:
                    miss += 1
                    if miss > max_miss:
                        break
            if score >= 3:
                hits.append((score, order, pos))
    hits.sort(key=lambda h: -h[0])
    return hits[:top]


def plug_fix(m, order, pos, offset, crib, ct, used, pt_i, ct_c):
    """Найти пару plugs, которая переведёт вывод в ct_c,
    не трогая уже выведенные верно позиции."""
    base = Enigma(order, pos=pos, plugs=''.join(used))
    for _ in range(offset + pt_i):
        base.enc_char('A')
    cur = base.enc_char(crib[pt_i])
    if cur == ct_c:
        return used
    # перебор неиспользованных пар: подставляем plug и смотрим
    free = [c for c in ALPH if c not in used]
    for a, b in itertools.combinations(free, 2):
        trial = Enigma(order, pos=pos, plugs=''.join(used) + a + b)
        for _ in range(offset):
            trial.enc_char('A')
        if all(trial.enc_char(crib[j]) ==
               ct[offset + j] for j in range(pt_i + 1)):
            return used + a + b
    return None


def phase2(order, pos, ct, crib, offset, max_plugs=6):
    """Жадно добавляем plugs, чиня позиции криба слева направо."""
    used = ''
    for j in range(len(crib)):
        m = Enigma(order, pos=pos, plugs=used)
        for _ in range(offset + j):
            m.enc_char('A')
        if m.enc_char(crib[j]) == ct[offset + j]:
            continue
        fixed = plug_fix(m, order, pos, offset, crib, ct,
                         used, j, ct[offset + j])
        if fixed is None or len(fixed) // 2 > max_plugs:
            return None
        used = fixed
    return used


if __name__ == '__main__':
    # --- сценарий: противник шифрует прогноз -----------------
    PT = 'WETTERVORHERSAGEKLUHHEUTE'
    TRUTH = dict(rotors=('II', 'IV', 'I'), pos=(17, 4, 22),
                 plugs='BFDG')
    crib, off = 'WETTERVORHERSAGE', 0
    m = Enigma(TRUTH['rotors'], pos=TRUTH['pos'],
               plugs=TRUTH['plugs'])
    CT = m.enc(PT)
    print(f'ct: {CT}\ncrib: "{crib}" @ {off}; truth: {TRUTH}')

    t0 = time.time()
    hits = phase1(CT, crib, off)
    print(f'phase1: {len(hits)} кандидатов за {time.time()-t0:.0f}с '
          f'(top: {hits[:3]})')

    for score, order, pos in hits:
        used = phase2(order, pos, CT, crib, off)
        if used is None:
            print(f'  {order} {pos}: plugs не подобрались')
            continue
        # верификация: восстановленная машина расшифровывает всё
        m2 = Enigma(order, pos=pos, plugs=used)
        dec = m2.enc(CT)
        ok = dec == PT
        print(f'  {order} pos={pos} plugs="{used}": '
              f'dec="{dec}" {"VERDICT: OK" if ok else "FAIL"}')
        if ok:
            break
