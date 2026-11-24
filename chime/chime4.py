"""chime4.py — chime v4: песенная форма и второй голос.

v3 научился форме A-B-A'. v4 — куплет/припев с контрастом
плотности и **контрамелодией**: второй голос отвечает мелодии
каноном на терцию ниже, сдвинутым на полдоли (оффбиты).

Форма: V(4) C(4) V(4) C(4) = 16 тактов.
Куплет: мелодия октавой ниже, 2 ноты на такт, хэты как в v2.
Припев: мелодия октавой выше, 4 ноты на такт, хэты 16-ми,
        + контрамелодия (оффбиты 2,6,10,14), заполнение-
        ролл снейра в последнем такте куплета.

Верификация (без ушей, STFT):
1. энергия припева > энергии куплета (плотность событий);
2. пик спектра на оффбите такта 5 = частота контрамелодии.
"""

import numpy as np

from chime2 import (SR, SPB, CHORDS, PAT_KICK, PAT_SNAR, PAT_HATS,
                    kick, snare, hat, note, f2m, save_wav, spectrogram)

STEPS, BARS = 16, 16

MEL_V = {                      # куплет: сдержанно, октавой ниже
    'A': ['A4', 'E5'], 'F': ['F4', 'C5'],
    'C': ['C5', 'G4'], 'G': ['G4', 'D5'],
}
MEL_C = {                      # припев: 4 ноты, октавой выше
    'A': ['A5', 'C6', 'E6', 'D6'], 'F': ['C6', 'A5', 'F5', 'G5'],
    'C': ['E5', 'G5', 'A5', 'G5'], 'G': ['D5', 'E5', 'G5', 'B5'],
}
COUNTER = {                    # канон: терция ниже, на оффбитах
    'A': ['F5', 'A5', 'C6', 'B5'], 'F': ['A5', 'F5', 'D5', 'E5'],
    'C': ['C5', 'E5', 'F5', 'E5'], 'G': ['B4', 'C5', 'E5', 'G5'],
}
MEL_STEPS_V = [0, 8]
MEL_STEPS_C = [0, 4, 8, 12]
CNT_STEPS = [s + 2 for s in MEL_STEPS_C]          # [2,6,10,14]


def verse(bar):
    return bar < 4 or 8 <= bar < 12


def fill_bar(bar):
    return bar in (3, 11)                       # конец куплета


def render():
    step = SPB / 4
    mix = np.zeros(int(SR * step * STEPS * BARS))

    def put(sig, at):
        i = int(SR * at)
        mix[i:i + len(sig)] += sig[:max(0, len(mix) - i)]

    for bar in range(BARS):
        root, triad = CHORDS[(bar // 2) % 4]
        v = verse(bar)
        mel = MEL_V[root] if v else MEL_C[root]
        mel_steps = MEL_STEPS_V if v else MEL_STEPS_C
        for s in range(STEPS):
            t = (bar * STEPS + s) * step
            if PAT_KICK[s] or (not v and s == 10):
                put(kick(), t)
            if PAT_SNAR[s]:
                put(snare(), t)
            if fill_bar(bar) and s >= 12:       # ролл в переход
                put(snare(0.05) * 0.6, t)
            if PAT_HATS[s] or not v:
                put(hat(), t)                   # припев: хэты 16-ми
            if s % 4 == 0:
                put(note(f2m(root + '2'), SPB * 0.9, 0.5), t)
            arp = triad[s % 3]
            put(note(f2m(arp), step * 0.9, 0.15 if v else 0.22), t)
            if s in mel_steps:
                mi = mel_steps.index(s)
                put(note(f2m(mel[mi]), SPB * 0.9, 0.5, 0.4), t)
            if not v and s in CNT_STEPS:        # второй голос
                ci = CNT_STEPS.index(s)
                put(note(f2m(COUNTER[root][ci]),
                         SPB * 0.5, 0.35, 0.5), t)
    mix *= 0.9 / np.abs(mix).max()
    return mix


def check(mix):
    step = SPB / 4
    seg = lambda bar, s, n=2048: mix[int(SR * (bar * STEPS + s)
                                       * step + SR * 0.02):
                                     int(SR * (bar * STEPS + s)
                                        * step + SR * 0.02) + n]
    def peak(b, s):
        x = seg(b, s) * np.hanning(len(seg(b, s)))
        spec = np.abs(np.fft.rfft(x))
        fr = np.fft.rfftfreq(len(x), 1 / SR)
        band = (fr > 300) & (fr < 3000)
        return fr[band][np.argmax(spec[band])]

    # 1. плотность: RMS энергия припева (такт 5) vs куплета (такт 1)
    ev = np.sqrt(np.mean(seg(1, 0, SR // 2) ** 2))
    ec = np.sqrt(np.mean(seg(5, 0, SR // 2) ** 2))
    # 2. контрамелодия: такт 5 (аккорд C), оффбит 10 -> 'F5'=698 Hz
    p = peak(5, 10)
    return ev, ec, p, ec > ev * 1.15 and abs(p - 698) < 40


if __name__ == '__main__':
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    np.random.seed(4)
    mix = render()
    save_wav(mix, os.path.join(here, 'chime4.wav'))
    spectrogram(mix, os.path.join(here, 'chime4_spec.png'))
    ev, ec, p, ok = check(mix)
    print(f'длина: {len(mix)/SR:.1f}s; энергия V={ev:.3f} '
          f'C={ec:.3f} (x{ec/ev:.2f}); пик оффбита {p:.0f} Hz (698)')
    print('VERDICT:', 'OK' if ok else 'FAIL')
