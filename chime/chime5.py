"""chime5.py — chime v5: FM-тембр и слой динамики.

v4 дал форму и контрамелодию; v5 добавляет два слоя:

1. FM-синтез (fm_note): несущая + модулятор (ratio 3:1) даёт
   металлический, «колокольный» тембр — лид припева поёт FM,
   контрамелодия остаётся аддитивной: тембры различимы.
2. Динамика: ACCENT — кривая громкости по 16-м шагам такта
   (даунбит громче, оффбиты тише), плюс crescendo внутри
   финального припева (такты 12-15: 0.8 -> 1.0).

Верификация (STFT, без ушей):
1. fm_note(880) имеет больше спектральных пиков, чем note(880)
   — сайдбенды FM реально существуют;
2. AB-контроль акцентов: дисперсия RMS на хэт-шагах в такте
   выше при ACCENT, чем при flat-кривой;
3. крещендо: RMS тактов 12->15 растёт.
"""

import numpy as np
import os

from chime2 import (SR, SPB, CHORDS, PAT_KICK, PAT_SNAR, PAT_HATS,
                    kick, snare, hat, note, f2m, env, save_wav,
                    spectrogram)
from chime4 import MEL_V, MEL_C, COUNTER, MEL_STEPS_V, MEL_STEPS_C, \
    CNT_STEPS, verse, fill_bar

STEPS, BARS = 16, 16

ACCENT = [1.00, .55, .70, .50, .90, .55, .70, .50,
          .95, .55, .75, .50, 1.00, .60, .80, .55]


def fm_note(freq, dur, vol=0.4, ratio=3.0, index=2.2):
    t = np.arange(int(SR * dur)) / SR
    mod = index * np.sin(2 * np.pi * freq * ratio * t)
    return np.sin(2 * np.pi * freq * t + mod) * env(len(t), 5) * vol


def render(accents=True):
    step = SPB / 4
    mix = np.zeros(int(SR * step * STEPS * BARS))

    def put(sig, at):
        i = int(SR * at)
        mix[i:i + len(sig)] += sig[:max(0, len(mix) - i)]

    for bar in range(BARS):
        root, triad = CHORDS[(bar // 2) % 4]
        v = verse(bar)
        swell = 0.8 + 0.05 * (bar - 12) if bar >= 12 else 1.0
        mel = MEL_V[root] if v else MEL_C[root]
        mel_steps = MEL_STEPS_V if v else MEL_STEPS_C
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
                     (0.15 if v else 0.22) * a), t)
            if s in mel_steps:
                mi = mel_steps.index(s)
                if v:
                    put(note(f2m(mel[mi]), SPB * 0.9, 0.5 * a,
                             0.4), t)
                else:                     # припев: FM-лид
                    put(fm_note(f2m(mel[mi]), SPB * 0.9,
                                0.5 * a * swell), t)
            if not v and s in CNT_STEPS:
                ci = CNT_STEPS.index(s)
                put(note(f2m(COUNTER[root][ci]),
                         SPB * 0.5, 0.35 * a, 0.5), t)
    mix *= 0.9 / np.abs(mix).max()
    return mix


def n_peaks(sig):
    x = sig * np.hanning(len(sig))
    spec = np.abs(np.fft.rfft(x))
    top = spec.max()
    return int((spec > top * 0.08).sum())


def check():
    # 1. FM сайдбенды: пиков у fm_note больше, чем у note
    p_fm = n_peaks(fm_note(f2m('A5'), SPB, 0.5))
    p_ad = n_peaks(note(f2m('A5'), SPB, 0.5))
    # 2. AB-акценты: дисперсия RMS хэт-полосы на шагах хэта
    step = SPB / 4
    def hatvar(mix):
        out = []
        for s in (2, 6, 10, 14):
            seg = mix[int(SR * s * step + SR * 0.01):
                      int(SR * s * step + SR * 0.01) + 2048]
            spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
            fr = np.fft.rfftfreq(len(seg), 1 / SR)
            out.append(spec[fr > 6000].mean())
        return np.var(out)
    va = hatvar(render(True))
    vf = hatvar(render(False))
    # 3. крещендо: RMS тактов 12->15
    mix = render(True)
    bar_rms = [np.sqrt(np.mean(
        mix[int(b * STEPS * step * SR):
            int((b + 1) * STEPS * step * SR)] ** 2))
        for b in (12, 13, 14, 15)]
    cresc = bar_rms[0] < bar_rms[-1] and bar_rms[1] <= bar_rms[3]
    return (p_fm, p_ad, va, vf, bar_rms,
            p_fm > p_ad * 1.5 and va > vf * 1.5 and cresc)


if __name__ == '__main__':
    np.random.seed(5)
    here = os.path.dirname(os.path.abspath(__file__))
    mix = render(True)
    save_wav(mix, os.path.join(here, 'chime5.wav'))
    spectrogram(mix, os.path.join(here, 'chime5_spec.png'))
    p_fm, p_ad, va, vf, rms, ok = check()
    print(f'FM peaks {p_fm} vs additive {p_ad}; '
          f'accent var {va:.2e} vs flat {vf:.2e}; '
          f'crescendo RMS {[f"{r:.3f}" for r in rms]}')
    print('VERDICT:', 'OK' if ok else 'FAIL')
