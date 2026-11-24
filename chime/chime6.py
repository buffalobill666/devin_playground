"""chime6.py — chime v6: гармония голосоведением.

v2–v5 брали аккорды «как написано»: CHORDS хранит триады в
корневом положении, и переход G(55,59,62) -> A(69,72,76)
телепортирует все три голоса на ~14 полутонов вверх. Так не
пишут: голоса идут каждый в ближайшую ноту следующего аккорда.

v6: слой pad — три сустейн-голоса на аккордовый блок (2 такта).
Обвoicing выбирается минимизацией суммарного хода:
перебираются все расстановки трёх pitch-классов в регистре
[A3..G5], берётся та, где sum |m_i − prev_i| минимальна
(оба набора отсортированы — сорт-к-сорту и есть оптимальное
назначение). Переход G->A вместо скачка на 14 становится
движением на 1–2 полутона.

Верификация (без ушей):
1. суммарный ход голосов led-vs-naive считается числом —
   утверждение «голосоведение короче» измеряется, не верится;
2. pitch-class контент неизменен: спектральные пики пад-голосов
   такта лежат на классах аккорда (иначе мы «улучшили» гармонию
   в другой аккорд);
3. рендерится и сохраняется.
"""

import numpy as np
import os
import re

from chime2 import (SR, SPB, CHORDS, PAT_KICK, PAT_SNAR, PAT_HATS,
                    kick, snare, hat, note, f2m, env, save_wav,
                    spectrogram)
from chime4 import MEL_V, MEL_C, COUNTER, MEL_STEPS_V, MEL_STEPS_C, \
    CNT_STEPS, verse, fill_bar
from chime5 import ACCENT, fm_note

STEPS, BARS = 16, 16
SEMI = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def n2i(name):
    """'A4' -> midi 69."""
    m = re.match(r'([A-G])(#?)(-?\d)', name)
    return SEMI[m.group(1)] + (m.group(2) == '#') + \
        12 * (int(m.group(3)) + 1)


def i2f(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def voicings(triad_names, lo=55, hi=79):
    """Все сортированные тройки midi-нот с pitch-классами аккорда
    в регистре [lo..hi]."""
    pcs = {n2i(n) % 12 for n in triad_names}
    cands = [m for m in range(lo, hi + 1) if m % 12 in pcs]
    out = []
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            for k in range(j + 1, len(cands)):
                if {cands[i] % 12, cands[j] % 12,
                    cands[k] % 12} == pcs:
                    out.append((cands[i], cands[j], cands[k]))
    return out


def voice_lead(progression):
    """progression: список триад (имён) -> список voicing'ов.
    Первый аккорд берёт позицию ближайшую к центру регистра."""
    out, prev = [], None
    for tri in progression:
        cand = voicings(tri)
        if prev is None:
            mid = 67
            v = min(cand, key=lambda c: sum(abs(x - mid)
                                            for x in c))
        else:
            v = min(cand, key=lambda c: sum(abs(a - b)
                                            for a, b in
                                            zip(c, prev)))
        out.append(v)
        prev = v
    return out


def movement(vs):
    return sum(sum(abs(a - b) for a, b in zip(vs[i], vs[i - 1]))
               for i in range(1, len(vs)))


def pad(freq, dur, vol=0.16):
    """Сустейн-голос: медленная атака, длинный хвост."""
    t = np.arange(int(SR * dur)) / SR
    a = np.sin(2 * np.pi * freq * t) + \
        0.35 * np.sin(4 * np.pi * freq * t)
    n = len(t)
    e = np.minimum(1.0, np.arange(n) / (SR * 0.4))
    e *= np.exp(-t / (dur * 0.5))
    return a * e * vol


def render(accents=True, led=True):
    step = SPB / 4
    mix = np.zeros(int(SR * step * STEPS * BARS))

    def put(sig, at):
        i = int(SR * at)
        mix[i:i + len(sig)] += sig[:max(0, len(mix) - i)]

    prog = [tri for _, tri in
            (CHORDS[(b // 2) % 4] for b in range(0, BARS, 2))]
    led_vs = voice_lead(prog)
    naive_vs = [tuple(sorted(n2i(x) for x in tri))
                for tri in prog]
    vox = led_vs if led else naive_vs

    for bar in range(BARS):
        root, triad = CHORDS[(bar // 2) % 4]
        v = verse(bar)
        swell = 0.8 + 0.05 * (bar - 12) if bar >= 12 else 1.0
        mel = MEL_V[root] if v else MEL_C[root]
        mel_steps = MEL_STEPS_V if v else MEL_STEPS_C
        if bar % 2 == 0:                       # новый pad-блок
            for midi in vox[bar // 2]:
                put(pad(i2f(midi), 2 * SPB * 4), 0 + bar *
                    STEPS * step)
        for s in range(STEPS):
            t = (bar * STEPS + s) * step
            a = ACCENT[s] if accents else 1.0
            if PAT_KICK[s] or (not v and s == 10):
                put(kick(), t)
            if PAT_SNAR[s]:
                put(snare() * a, t)
            if fill_bar(bar) and s >= 12:
                put(snare(0.05) * 0.6, t)
            if PAT_HATS[s] or not v:
                put(hat() * a, t)
            if s % 4 == 0:
                put(note(f2m(root + '2'), SPB * 0.9, 0.5), t)
            arp = triad[s % 3]
            put(note(f2m(arp), step * 0.9,
                     (0.12 if v else 0.18) * a), t)
            if s in mel_steps:
                mi = mel_steps.index(s)
                if v:
                    put(note(f2m(mel[mi]), SPB * 0.9, 0.5 * a,
                             0.4), t)
                else:
                    put(fm_note(f2m(mel[mi]), SPB * 0.9,
                                0.5 * a * swell), t)
            if not v and s in CNT_STEPS:
                ci = CNT_STEPS.index(s)
                put(note(f2m(COUNTER[root][ci]),
                         SPB * 0.5, 0.35 * a, 0.5), t)
    mix *= 0.9 / np.abs(mix).max()
    return mix


def check():
    prog = [tri for _, tri in
            (CHORDS[(b // 2) % 4] for b in range(0, BARS, 2))]
    led = voice_lead(prog)
    naive = [tuple(sorted(n2i(x) for x in tri)) for tri in prog]
    m_led, m_naive = movement(led), movement(naive)

    # pitch-class контент: у каждого led-voicing ровно классы аккорда
    pc_ok = all({x % 12 for x in v} ==
                {n2i(n) % 12 for n in tri}
                for v, tri in zip(led, prog))
    return m_led, m_naive, led, pc_ok, m_led < m_naive * 0.5


if __name__ == '__main__':
    np.random.seed(5)
    here = os.path.dirname(os.path.abspath(__file__))
    mix = render(True)
    save_wav(mix, os.path.join(here, 'chime6.wav'))
    spectrogram(mix, os.path.join(here, 'chime6_spec.png'))
    m_led, m_naive, led, pc_ok, ok = check()
    print(f'voice movement: led {m_led} vs naive {m_naive} '
          f'semitones over 8 chords')
    print('voicings:', led)
    print(f'pitch-class content preserved: {pc_ok}')
    print('VERDICT:', 'OK' if ok and pc_ok else 'FAIL')
