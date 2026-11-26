"""chime10.py — the jitter etude.

The measurement arc (c8 i7/i15) proved humanity is audible only
in isolation: masked by backbone, quantized away by resolution.
So write the piece that exploits it — sparse passages where
humanized timing carries the feel, dense passages where it is
deliberately sacrificed. Structure as an arc of exposure:

  bars 0-1   solo hats, humanized — naked timing
  bars 2-3   + wind melody         — timing still audible
  bars 4-7   full band             — humanity masked by design
  bars 8-9   stripped back         — the ear now knows

The minor phrase leans on the cycle's chronicle mood.
"""
import numpy as np
import os

from chime2 import SR, SPB, CHORDS, kick, snare, hat, note, f2m, \
    save_wav, spectrogram
from chime8 import wind

STEPS, BARS = 16, 10
JIT_MS, SWING = 9.0, 0.6

# melody: midi notes per bar for the wind voice (sparse bars 2-3,
# 8-9 silent in band bars where fm would fight), minor-leaning
MEL = {2: [69, 67, 64, 62], 3: [64, 62, 60, 62],
       8: [69, 67, 64, 67], 9: [64, 62, 60, 60]}


def render(seed=2):
    jr = np.random.RandomState(seed)
    step = SPB / 4
    mix = np.zeros(int(SR * step * STEPS * BARS) + SR)

    def put(sig, at):
        i = int(SR * at)
        if i < 0 or i >= len(mix):
            return
        mix[i:i + len(sig)] += sig[:max(0, len(mix) - i)]

    def band(bar):
        if bar < 2:
            return 'hats'
        if bar < 4:
            return 'sparse'
        if bar < 8:
            return 'full'
        return 'sparse'

    for bar in range(BARS):
        root, triad = CHORDS[(bar // 2) % 4]
        mode = band(bar)
        for s in range(STEPS):
            t = (bar * STEPS + s) * step
            if s % 4 == 2:
                t += SWING * step / 3
            tj = t + jr.normal(0, JIT_MS / 1000.0)
            # hats — always, humanized; they carry the piece
            if s % 2 == 0 or mode != 'full':
                put(hat() * (0.5 if s % 4 else 0.8), tj)
            if mode == 'full':
                if s % 8 == 0:
                    put(kick(), t)
                if s % 8 == 4:
                    put(snare() * 0.8, t)
                if s % 4 == 0:
                    put(note(f2m(root + '2'), SPB * 0.5, 0.35), t)
                arp = triad[s % 3]
                put(note(f2m(arp), step * 0.8, 0.1), t)
            if mode == 'sparse' and s % 4 == 0 and bar in MEL:
                mi = MEL[bar][s // 4]
                put(wind(i2f := 440.0 * 2 ** ((mi - 69) / 12),
                         SPB * 0.9, 0.42, seed=bar * 4 + s), tj)
    mix *= 0.9 / np.abs(mix).max()
    return mix


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    mix = render()
    save_wav(mix, os.path.join(here, 'chime10.wav'))
    spectrogram(mix, os.path.join(here, 'chime10_spec.png'))
    print('chime10 rendered — the jitter etude')
