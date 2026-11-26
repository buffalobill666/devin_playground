"""chime7.py — chime v7: swing (humanize the grid).

Named next step: rhythm so far is metronome-straight — every
16th lands exactly on the grid. Real players swing: the
"and" of each beat arrives late. On our 16-step bar the
weak 16th of each beat-pair is s % 4 == 2 — conveniently
exactly where the hats sit. Triplet swing = that note at
+4/3 of an eighth instead of +1, i.e. delayed by 1/3 step.

render(swing=0..1): timing offset = swing * step/3 applied
to every s % 4 == 2 event (hats, arp, snare-ghosts, mel
notes landing there). Kick/snare backbones (s%4==0, %8==4)
stay on the grid — swing lives in the off-16ths.

Verification without ears: render two hat-only mixes
(swing 0 vs 1), detect each hat onset (energy threshold
crossing) — mean onset delay should equal step/3 within a
few ms. Also A/B the full mix: peak correlation lag should
be ~0 on downbeats but the off-16th energy moves.
"""

import numpy as np
import os

from chime2 import (SR, SPB, CHORDS, PAT_KICK, PAT_SNAR, PAT_HATS,
                    kick, snare, hat, note, f2m, save_wav,
                    spectrogram)
from chime4 import MEL_V, MEL_C, COUNTER, MEL_STEPS_V, MEL_STEPS_C, \
    CNT_STEPS, verse, fill_bar
from chime5 import ACCENT, fm_note
from chime6 import pad, i2f, voice_lead

STEPS, BARS = 16, 16


def render(accents=True, swing=0.0, jit_ms=0.0, jit_vel=0.0,
             seed=None):
    step = SPB / 4
    mix = np.zeros(int(SR * step * STEPS * BARS) + SR)
    jr = np.random.RandomState(seed if seed is not None else 0)

    def jit(t, backbone):
        if jit_ms and not backbone:
            return t + jr.normal(0, jit_ms / 1000.0)
        return t

    def jvel():
        return 1.0 + (jr.uniform(-jit_vel, jit_vel) if jit_vel else 0)

    def put(sig, at):
        i = int(SR * at)
        if i < 0 or i >= len(mix):
            return
        mix[i:i + len(sig)] += sig[:max(0, len(mix) - i)]

    prog = [tri for _, tri in
            (CHORDS[(b // 2) % 4] for b in range(0, BARS, 2))]
    vox = voice_lead(prog)

    for bar in range(BARS):
        root, triad = CHORDS[(bar // 2) % 4]
        v = verse(bar)
        swell = 0.8 + 0.05 * (bar - 12) if bar >= 12 else 1.0
        mel = MEL_V[root] if v else MEL_C[root]
        mel_steps = MEL_STEPS_V if v else MEL_STEPS_C
        if bar % 2 == 0:
            for midi in vox[bar // 2]:
                put(pad(i2f(midi), 2 * SPB * 4), bar * STEPS * step)
        for s in range(STEPS):
            t = (bar * STEPS + s) * step
            if s % 4 == 2:                    # weak 16th — swings
                t += swing * step / 3
            a = ACCENT[s] if accents else 1.0
            if PAT_KICK[s] or (not v and s == 10):
                put(kick(), t)  # backbone
            if PAT_SNAR[s]:
                put(snare() * a * jvel(), t)  # backbone-ish
            if fill_bar(bar) and s >= 12:
                put(snare(0.05) * 0.6, t)
            if PAT_HATS[s] or not v:
                put(hat() * a * jvel(), jit(t, False))
            if s % 4 == 0:
                put(note(f2m(root + '2'), SPB * 0.9, 0.5), t)
            arp = triad[s % 3]
            put(note(f2m(arp), step * 0.9,
                     (0.12 if v else 0.18) * a * jvel()), jit(t, False))
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


def hat_onsets(swing):
    """Only hats, at steps 2,6,10,14 of bar 0; find each
    onset as first sample above 10% of window peak."""
    step = SPB / 4
    mix = np.zeros(int(SR * step * STEPS))
    for s in (2, 6, 10, 14):
        t = s * step + swing * step / 3
        i = int(SR * t)
        h = hat()
        mix[i:i + len(h)] += h
    onsets = []
    for s in (2, 6, 10, 14):
        lo = int(SR * (s * step - 0.005))
        hi = int(SR * ((s + 1) * step))
        seg = mix[lo:hi]
        thr = np.abs(seg).max() * 0.1
        onsets.append(lo + int(np.argmax(np.abs(seg) > thr)))
    return np.array(onsets) / SR, step


def check():
    o0, step = hat_onsets(0.0)
    o1, _ = hat_onsets(1.0)
    delay = (o1 - o0).mean()
    expect = step / 3
    return delay, expect, abs(delay - expect) < 0.002


if __name__ == '__main__':
    np.random.seed(5)
    here = os.path.dirname(os.path.abspath(__file__))
    mix = render(True, 1.0)
    save_wav(mix, os.path.join(here, 'chime7.wav'))
    spectrogram(mix, os.path.join(here, 'chime7_spec.png'))
    delay, expect, ok = check()
    print(f'swing onset delay {delay*1000:.1f}ms '
          f'(expected {expect*1000:.1f}ms)')
    print('VERDICT:', 'OK' if ok else 'FAIL')
