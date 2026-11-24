"""chime8.py — the noise voice: pitched wind.

Percussion noise is cheap — white noise + envelope, done since
v2. A *melodic* noise voice is different: white noise through a
narrow resonant filter centered on the note's frequency gives a
breathy, flute-like tone — the pitch lives in the filter, the
texture lives in the noise. Wind instruments are literally this.

Implementation: FFT the noise, multiply by a gaussian mask at f0
(plus a weaker one at 2f0 — a hint of overtone), inverse FFT,
envelope. No oscillator anywhere in the signal path — the pitch
you hear is the filter's center frequency.

Verification without ears: render wind(440), take its spectrum —
the peak bin must sit at 440±8 Hz, and the peak must dominate
the median spectral energy by ~8x+ (noise makes the floor high,
that's the point — it's breath, not a sine). A pitched *sine*
would give a much higher ratio; a pitched *voice* gives a peak
on a noisy floor.
"""

import numpy as np
from chime2 import SR, env, save_wav


def wind(freq, dur, vol=0.5, q=30, seed=0):
    """Pitched noise: white noise through a gaussian spectral
    mask at f0 (and a 0.3-weight one at 2f0). q = sharpness."""
    n = int(SR * dur)
    spec = np.fft.rfft(np.random.default_rng(seed).standard_normal(n))
    freqs = np.fft.rfftfreq(n, 1 / SR)
    mask = np.exp(-0.5 * ((freqs - freq) / (freq / q)) ** 2)
    mask += 0.3 * np.exp(-0.5 * ((freqs - 2 * freq) / (freq / q)) ** 2)
    sig = np.fft.irfft(spec * mask, n)
    sig /= max(1e-9, np.abs(sig).max())
    return sig * env(n, 3) * vol


def spectral_peak(sig):
    """Peak bin frequency and peak-to-median ratio."""
    spec = np.abs(np.fft.rfft(sig))
    freqs = np.fft.rfftfreq(len(sig), 1 / SR)
    k = spec.argmax()
    return freqs[k], spec[k] / np.median(spec)


def check():
    sig = wind(440, 0.5, seed=7)
    f, ratio = spectral_peak(sig)
    print(f'peak: {f:.1f} Hz (target 440), dominance {ratio:.1f}x')
    ok = abs(f - 440) < 8 and ratio > 8
    print('VERDICT:', 'OK — pitched noise' if ok else 'FAIL')
    return ok


def render():
    """A breathy phrase over the v7 pad — the noise voice
    carrying a melody, not marking time."""
    from chime6 import pad, i2f, voice_lead
    from chime7 import CHORDS, SPB
    from chime2 import f2m
    step = SPB / 4
    notes = [67, 69, 71, 69, 67, 64, 62, 64]   # one breath per 2 steps
    mix = np.zeros(int(SR * step * 32) + SR)
    for b, (root, tri) in enumerate(CHORDS):
        for m in tri:
            put = pad(f2m(m), 2 * SPB)
            i = int(SR * b * 8 * step)
            mix[i:i + len(put)] += put * 0.5
    for i, m in enumerate(notes):
        sig = wind(i2f(m), step * 2.2, seed=i)
        at = int(SR * i * 4 * step)
        mix[at:at + len(sig)] += sig
    save_wav(mix, __file__.replace('.py', '.wav'))
    print('saved chime8.wav')


if __name__ == '__main__':
    check()
    render()
