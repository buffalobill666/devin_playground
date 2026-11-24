"""chime3.py — chime v3: слои и форма.

Поверх v2 (ударные + бас + арпеджио) — мелодический слой и
структура A–B–A': 12 тактов, секции различаются плотностью и
наличием мелодии. Форма должна читаться на спектрограмме:
границы секций видны как смена плотности событий.

A  (такты 0-3):  ударные, бас, арпеджио
B  (такты 4-7):  + мелодия четвертями, хэты 8-ми
A' (такты 8-11): + мелодия с варьированным ритмом, арп вниз-вверх

Верификация: пик спектра в момент ноты мелодии = её частота.
"""

import numpy as np

from chime2 import (SR, SPB, CHORDS, PAT_KICK, PAT_SNAR, PAT_HATS,
                    kick, snare, hat, note, f2m, save_wav, spectrogram)

STEPS, BARS = 16, 12

# мелодия: по 4 ноты на аккорд (2 такта), ступени лада + проходящие
MELODY = {
    'A': ['A5', 'C6', 'E6', 'D6'],
    'F': ['C6', 'A5', 'F5', 'G5'],
    'C': ['E5', 'G5', 'A5', 'G5'],
    'G': ['D5', 'E5', 'G5', 'B5'],
}
MEL_STEPS_B = [0, 4, 8, 12]           # четверти
MEL_STEPS_A2 = [0, 6, 8, 14]          # вариация


def section(bar):
    return 'A' if bar < 4 else 'B' if bar < 8 else 'A2'


def render():
    step = SPB / 4
    total = int(SR * step * STEPS * BARS)
    mix = np.zeros(total)

    def put(sig, at):
        i = int(SR * at)
        mix[i:i + len(sig)] += sig[:max(0, total - i)]

    for bar in range(BARS):
        root, triad = CHORDS[(bar // 2) % 4]
        sec = section(bar)
        mel = MELODY[root]
        mel_steps = MEL_STEPS_B if sec == 'B' else MEL_STEPS_A2
        for s in range(STEPS):
            t = (bar * STEPS + s) * step
            if PAT_KICK[s] and not (sec == 'A2' and s == 8):
                put(kick(), t)
            if PAT_SNAR[s]:
                put(snare(), t)
            if PAT_HATS[s] or (sec == 'B' and s % 2 == 0):
                put(hat(), t)                      # B: хэты 8-ми
            if s % 4 == 0:
                put(note(f2m(root + '2'), SPB * 0.9, 0.5), t)
            arp = triad[(s % 3) if sec != 'A2' else (2 - s % 3)]
            put(note(f2m(arp), step * 0.9, 0.18), t)
            if sec != 'A' and s in mel_steps:
                mi = mel_steps.index(s)
                put(note(f2m(mel[mi]), SPB * 0.9, 0.5, 0.4), t)
    mix *= 0.9 / np.abs(mix).max()
    return mix


def check(mix):
    """Такт 5, шаг 8: аккорды меняются каждые 2 такта -> такт 5 = C.
    Мелодия C на шаге 8 (индекс 2) = 'A5' = 880 Гц. Мелодия
    доминирует над арпеджио по громкости (0.5 vs 0.18)."""
    step = SPB / 4
    i = int(SR * (5 * STEPS + 8) * step + SR * 0.02)
    seg = mix[i:i + 2048] * np.hanning(2048)
    spec = np.abs(np.fft.rfft(seg))
    freqs = np.fft.rfftfreq(2048, 1 / SR)
    band = (freqs > 300) & (freqs < 3000)
    peak = freqs[band][np.argmax(spec[band])]
    return peak, abs(peak - 880) < 30


if __name__ == '__main__':
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    np.random.seed(3)
    mix = render()
    save_wav(mix, os.path.join(here, 'chime3.wav'))
    spectrogram(mix, os.path.join(here, 'chime3_spec.png'))
    peak, ok = check(mix)
    print(f'длина: {len(mix)/SR:.1f}s, пик мелодии: {peak:.0f} Hz '
          f'(ожидалось 880)')
    print('VERDICT:', 'OK' if ok else 'FAIL')
