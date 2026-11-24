"""chime2.py — ритм-движок: секвенсор + синтез + спектрограмма.

Композитор без ушей: музыка проверяется не слухом, а STFT.
16-шаговый паттерн (kick/snare/hat), бас по корням аккордов,
арпеджио по трезвучиям. Am F C G, два такта на аккорд.

Выход: chime2.wav + chime2_spec.png. Верификация: спектральный
пик в момент первой ноты арпеджио совпадает с ожидаемой частотой.
"""

import wave
import numpy as np

SR = 22050
BPM, SPB = 120, 60 / 120          # секунд на долю
STEPS, BARS = 16, 8               # 8 тактов = 2 на аккорд


def env(n, decay):
    return np.exp(-np.arange(n) * decay / SR)


def kick(dur=0.18):
    t = np.arange(int(SR * dur)) / SR
    f = 120 * np.exp(-t * 18) + 40
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 25)


def snare(dur=0.14):
    n = int(SR * dur)
    return (np.random.randn(n) * 0.5 +
            np.sin(2 * np.pi * 190 * np.arange(n) / SR)) * env(n, 30)


def hat(dur=0.05):
    n = int(SR * dur)
    return np.random.randn(n) * 0.35 * env(n, 80)


def note(freq, dur, vol=0.4, bright=0.25):
    t = np.arange(int(SR * dur)) / SR
    w = np.sin(2 * np.pi * freq * t) + bright * np.sin(4 * np.pi * freq * t)
    return w * env(len(t), 4) * vol


def f2m(name):                    # имя ноты -> частота
    names = 'C C# D D# E F F# G G# A A# B'.split()
    base = names.index(name[:-1])
    octv = int(name[-1])
    return 440 * 2 ** ((base - 9) / 12 + octv - 4)


CHORDS = [('A', ['A4', 'C5', 'E5']), ('F', ['F4', 'A4', 'C5']),
          ('C', ['C4', 'E4', 'G4']), ('G', ['G3', 'B3', 'D4'])]

PAT_KICK = [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
PAT_SNAR = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
PAT_HATS = [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0]


def render():
    step = SPB / 4                # 16-е
    total = int(SR * step * STEPS * BARS)
    mix = np.zeros(total)

    def put(sig, at):
        i = int(SR * at)
        mix[i:i + len(sig)] += sig[:max(0, total - i)]

    for bar in range(BARS):
        root, triad = CHORDS[(bar // 2) % 4]
        for s in range(STEPS):
            t = (bar * STEPS + s) * step
            if PAT_KICK[s]:
                put(kick(), t)
            if PAT_SNAR[s]:
                put(snare(), t)
            if PAT_HATS[s]:
                put(hat(), t)
            if s % 4 == 0:                       # бас на доли
                put(note(f2m(root + '2'), SPB * 0.9, 0.5), t)
            arp = triad[s % 3]                   # арпеджио 16-ми
            put(note(f2m(arp), step * 0.9, 0.18), t)
    mix *= 0.9 / np.abs(mix).max()
    return mix


def save_wav(mix, path):
    with wave.open(path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())


def spectrogram(mix, path):
    import matplotlib.pyplot as plt
    win, hop = 1024, 256
    frames = [np.abs(np.fft.rfft(mix[i:i + win] * np.hanning(win)))
              for i in range(0, len(mix) - win, hop)]
    S = 20 * np.log10(np.array(frames).T + 1)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.imshow(S, origin='lower', aspect='auto', cmap='magma',
              extent=[0, len(mix) / SR, 0, SR / 2])
    ax.set_ylim(0, 4000)
    ax.set_ylabel('Hz')
    ax.set_xlabel('s')
    fig.savefig(path, dpi=140, bbox_inches='tight')
    plt.close(fig)


def check(mix):
    """Шаг 5: только арпеджио (Am, triad[5%3=2] = E5, 659 Гц).
    Бас 110 Гц ниже полосы анализа 300–3000 — ищем пик в ней."""
    step = SPB / 4
    i = int(SR * 5 * step + SR * 0.01)
    seg = mix[i:i + 2048] * np.hanning(2048)
    spec = np.abs(np.fft.rfft(seg))
    freqs = np.fft.rfftfreq(2048, 1 / SR)
    band = (freqs > 300) & (freqs < 3000)
    peak = freqs[band][np.argmax(spec[band])]
    return peak, abs(peak - 659.25) < 30


if __name__ == '__main__':
    np.random.seed(3)
    mix = render()
    save_wav(mix, 'chime2.wav')
    spectrogram(mix, 'chime2_spec.png')
    peak, ok = check(mix)
    print(f'длина: {len(mix)/SR:.1f}s, пик на шаге 5: {peak:.0f} Hz '
          f'(ожидалось 659)')
    print('VERDICT:', 'OK' if ok else 'FAIL')
