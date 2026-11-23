"""Tiny DSP engine: oscillators, ADSR, Schroeder reverb, WAV out."""
import numpy as np
import wave

SR = 44100


def sine(freq, dur, sr=SR):
    t = np.arange(int(dur * sr)) / sr
    return np.sin(2 * np.pi * freq * t)


def fm(freq, dur, ratio=2.0, index=3.0, sr=SR):
    """FM voice: carrier freq, modulator freq*ratio."""
    t = np.arange(int(dur * sr)) / sr
    mod = np.sin(2 * np.pi * freq * ratio * t)
    return np.sin(2 * np.pi * freq * t + index * mod)


def adsr(n, a=0.01, d=0.08, s=0.6, r=0.15, sr=SR):
    """Envelope of n samples; s = sustain level."""
    env = np.ones(n, np.float32) * s
    na, nd, nr = int(a * sr), int(d * sr), int(r * sr)
    na = min(na, n); nd = min(nd, n - na); nr = min(nr, n)
    env[:na] = np.linspace(0, 1, na)
    env[na:na + nd] = np.linspace(1, s, nd)
    env[n - nr:] *= np.linspace(1, 0, nr)
    return env


def note(freq, dur, kind='fm', amp=0.3, **kw):
    env = adsr(int(dur * SR), **{k: v for k, v in kw.items()
                                 if k in 'adsr'})
    if kind == 'fm':
        x = fm(freq, dur, kw.get('ratio', 2.0), kw.get('index', 3.0))
    elif kind == 'bass':
        x = np.sign(sine(freq, dur)) * 0.4 + sine(freq, dur) * 0.6
    else:
        x = sine(freq, dur)
    return x * env * amp


def reverb(x, sr=SR, wet=0.28):
    """Schroeder reverb: 4 comb filters + 2 allpass."""
    out = x.copy()
    for dt in (0.0297, 0.0371, 0.0411, 0.0437):
        d = int(dt * sr)
        y = np.zeros_like(out)
        y[d:] = out[:-d]
        out = out + y * 0.773
    for dt in (0.005, 0.0017):
        d = int(dt * sr)
        y = np.zeros_like(out)
        y[d:] = out[:-d]
        out = out + y * 0.5 - out * 0.5 * 0.0
    return (1 - wet) * x + wet * out


def save_wav(path, x, sr=SR):
    x = np.tanh(x * 1.2)              # soft clip
    pcm = (x / np.abs(x).max() * 32767 * 0.9).astype(np.int16)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return len(pcm) / sr


def place(mix, x, at, sr=SR):
    """Add x into mix starting at `at` seconds."""
    i = int(at * sr)
    j = min(i + len(x), len(mix))
    if j > i:
        mix[i:j] += x[:j - i]
