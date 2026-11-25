"""melgen.py — the Flick x chime synthesis: a melody composed
by my own programming language, played by my own synthesizer.

melody.flk (proglang/) random-walks a pentatonic contour; both
Flick backends must agree byte-for-byte before a single sample
is rendered — the determinism guarantee is part of the piece.
The wind voice carries the tune; the v7 pad holds the floor.

Verification without ears: identical outputs across backends,
peak frequency of the first rendered note within a semitone
of its midi target, file written.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'proglang'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flick       # noqa: E402
import flickvm     # noqa: E402
from chime8 import wind, spectral_peak   # noqa: E402
from chime6 import pad, i2f, voice_lead  # noqa: E402
from chime7 import CHORDS, SPB           # noqa: E402
from chime2 import f2m                   # noqa: E402
import wave                              # noqa: E402

SR = 22050
PROG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    '..', 'proglang', 'melody.flk')


def compose():
    src = open(PROG, encoding='utf-8').read()
    o1 = []
    flick.run(flick.parse(flick.tokenize(src)), flick.Env(), o1)
    o2 = flickvm.flickvm(src)
    a, b = [int(x) for x in o1], [int(x) for x in o2]
    assert a == b, 'backends diverged — the piece does not exist'
    return a[:16], a[16:]


def write_wav(path, sig):
    sig = sig / max(1e-9, np.abs(sig).max()) * 0.85
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((sig * 32767).astype(np.int16).tobytes())


def render():
    mel, rhy = compose()
    print('melody:', mel)
    print('rhythm:', rhy)
    unit = SPB / 2                     # rhythm 1 = eighth note
    total = int(sum(rhy) * unit * SR) + SR
    sig = np.zeros(total)
    # pad underneath: v7 chords, triad voices, stretched long
    t = 0.0
    ci = 0
    while t * SR < total - SR:
        root, tri = CHORDS[ci % len(CHORDS)]
        for m in tri:
            put = pad(f2m(m), 2 * SPB)
            off = int(t * SR)
            sig[off:off + len(put)] += 0.4 * put[:len(sig) - off]
        t += 2 * SPB
        ci += 1
    # melody: wind voice
    t = 0.0
    first_peak = None
    for i, (m, r) in enumerate(zip(mel, rhy)):
        dur = r * unit
        v = wind(i2f(m), dur * 1.1, vol=0.45, q=24, seed=100 + i)
        off = int(t * SR)
        sig[off:off + len(v)] += v[:len(sig) - off]
        if i == 0:
            first_peak = spectral_peak(v[:int(SR * 0.3)])
        t += dur
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'melody.wav')
    write_wav(out, sig)
    print('saved', out)
    # verify: first note 69 = A4 = 440 Hz
    pk, dom = first_peak
    expect = i2f(69)
    cents = 1200 * np.log2(pk / expect)
    print(f'first-note check: peak {pk:.0f} Hz vs target {expect:.0f} '
          f'({cents:+.0f} cents), dominance {dom:.0f}x')
    return out


if __name__ == '__main__':
    render()
