"""Generative composition: Markov melody over drifting pads.

A minor pentatonic. The melody is a Markov walk on scale degrees;
phrase rests and octave jumps give it breathing. Two FM pad chords
sustain underneath; a square-ish bass follows the chord roots.
"""
import numpy as np
from pathlib import Path
from chime.synth import SR, note, reverb, save_wav, place

OUT = Path('runs/chime'); OUT.mkdir(parents=True, exist_ok=True)
SEED = 55
rng = np.random.default_rng(SEED)

# A minor pentatonic across 3 octaves
PENTA = [0, 3, 5, 7, 10]
A3 = 220.0


def freq_of(deg):
    oct_, st = divmod(deg, len(PENTA))
    return A3 * 2 ** oct_ * 2 ** (PENTA[st] / 12)


# chord progression (scale-degree roots): i - VII - v - IV feel
PROG = [(0, [0, 2, 4]), (3, [3, 5, 7]), (2, [2, 4, 6]), (4, [4, 6, 8])]
BAR = 2.0                       # seconds per bar
BARS = 36
DUR = BARS * BAR + 4

mix = np.zeros(int(DUR * SR), np.float32)

# --- pads: soft FM chords, one per bar --------------------------------
for b in range(BARS):
    root, tones = PROG[b % len(PROG)]
    for d in tones:
        f = freq_of(d + 5)      # pad sits an octave up
        n = note(f, BAR * 1.05, kind='fm', amp=0.05,
                 ratio=1.0, index=1.2, a=0.4, r=0.5)
        place(mix, n, b * BAR)

# --- bass: root each bar, sparse --------------------------------------
for b in range(BARS):
    root, _ = PROG[b % len(PROG)]
    n = note(freq_of(root - 5) / 2, 0.5, kind='bass', amp=0.16,
             a=0.005, r=0.1)
    place(mix, n, b * BAR)

# --- melody: Markov walk on scale degrees -----------------------------
# transition: prefer steps +-1, allow +-2, rare rests and octave jumps
STEP_P = {-2: .08, -1: .30, 0: .10, 1: .32, 2: .12}
steps = list(STEP_P)
probs = np.array(list(STEP_P.values()))
probs /= probs.sum()

deg = 7                          # start mid-scale
b = 2                            # leave 2 bars intro
while b < BARS - 2:
    if rng.random() < 0.14:      # rest
        b += 1
        continue
    if rng.random() < 0.08:      # phrase breath: octave hop
        deg += rng.choice([-5, 5])
    else:
        deg += rng.choice(steps, p=probs)
    deg = int(np.clip(deg, 2, 14))
    nlen = 0.5 if rng.random() < .75 else 1.0
    n = note(freq_of(deg), nlen * BAR * .92, kind='fm',
             amp=0.22, ratio=2.0, index=2.6, a=0.01, r=0.2)
    place(mix, n, b * BAR)
    b += 1 if nlen <= .5 else 2

# sparse sparkle: high grace notes on strong bars
for b in range(4, BARS - 2, 8):
    n = note(freq_of(rng.integers(10, 15)), 0.35, kind='sine',
             amp=0.07, a=0.005, r=0.3)
    place(mix, n, b * BAR + 0.5)

mix = reverb(mix)
secs = save_wav(OUT / 'chime1.wav', mix)
print(f'chime1.wav: {secs:.1f}s, seed={SEED}')
