"""chime11 — «Протечка» (Leakage). Music as marginalia after PKD.

Concept from the reading: живое — то, что протекает сквозь
управление. The grid is machine-perfect (quantized exactly —
Penfield time). Leaks are events that refuse the grid: off-grid
placement, jitter, human timing. Three arcs:
  bars 0-3:   the grid alone — flawless, dead
  bars 4-7:   leaks appear — clicks/hat-gestures off-grid
  bars 8-11:  the grid stumbles (missing beats, a late kick),
              and the leak becomes a sparse wind melody
The ear-test of the piece: humanity audible only because the
grid is there to be broken. Leakage needs a vessel.
"""
import numpy as np
from chime2 import SR, SPB, kick, hat, save_wav, f2m
from chime8 import wind

STEPS, BARS = 16, 12

MEL = {8: [69, 67, 64], 9: [62, 64, 67], 10: [69, 71, 69, 67], 11: [64, 62, 60]}


def render(seed=11):
    jr = np.random.RandomState(seed)
    step = SPB / 4
    total = int(SR * step * STEPS * BARS) + SR
    mix = np.zeros(total)

    def put(sig, at):
        i = int(SR * at)
        if 0 <= i < len(mix):
            mix[i:i + len(sig)] += sig[:max(0, len(mix) - i)]

    for bar in range(BARS):
        for s in range(STEPS):
            t = (bar * STEPS + s) * step
            # THE GRID: perfectly quantized, no jitter — machine time
            if s % 4 == 0:
                if bar >= 8 and bar == 9 and s == 4:
                    continue  # the grid stumbles: a missing kick
                late = 0.012 if (bar >= 8 and bar == 10 and s == 8) else 0.0
                put(kick() * 0.8, t + late)
            if s % 8 == 4:
                put(hat() * 0.25, t)
            # THE LEAKS: off-grid events, heavy human jitter
            if 4 <= bar < 8 and jr.random() < 0.10:
                put(hat(0.09) * 0.35, t + jr.uniform(-0.03, 0.05) + step * 0.37)
            if bar >= 8 and jr.random() < 0.06:
                put(hat(0.08) * 0.3, t + jr.uniform(-0.04, 0.04))
        # leak becomes melody in the final arc
        if bar in MEL:
            for k, note in enumerate(MEL[bar]):
                # off-grid placement: melody refuses the 16th grid
                t = (bar * STEPS + 2 + k * 4) * step + jr.uniform(-0.02, 0.03)
                put(wind(440 * 2 ** ((note - 69) / 12), step * 3.2, 0.30, seed=int(jr.randint(1e6))), t)
    save_wav(mix, 'chime11.wav')
    return mix


if __name__ == '__main__':
    render()
    print('rendered chime11.wav')
