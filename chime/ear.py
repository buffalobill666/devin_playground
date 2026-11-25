"""ear.py — prosthetic hearing: spectral anatomy of a wav.

The composer has no ears; this is the procedural substitute.
Not a spectrogram for looking at — a dissection that reports
what a listener would feel, in numbers:

  envelope  — attack/decay shape: is the sound plucked, blown, bowed?
  pitch     — per-frame fundamental via autocorrelation: the melody
              contour the composer wrote blind, now read back
  brightness — spectral centroid over time: where the energy sits
  harmonicity — share of energy near integer multiples of f0:
              a flute is harmonic, wind noise is not
  onsets    — energy-flux peaks: the rhythm grid

Output: text report + anatomy plate png. First patient: the
composer's own melody.wav, heard for the first time.
"""
import sys
import wave
import numpy as np

def load(path):
    w = wave.open(path, 'rb')
    sr = w.getframerate()
    n = w.getnframes()
    raw = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768
    if w.getnchannels() == 2:
        raw = raw.reshape(-1, 2).mean(axis=1)
    w.close()
    return raw, sr


def framesig(x, sr, win=2048, hop=512):
    n = (len(x) - win) // hop + 1
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    return x[idx] * np.hanning(win)[None, :], n


def pitch_track(fr, sr, win=2048, hop=512, fmin=60, fmax=2000):
    """autocorrelation pitch per frame; 0 if unvoiced."""
    out = np.zeros(len(fr))
    for i, f in enumerate(fr):
        if np.sqrt(np.mean(f ** 2)) < 0.005:
            continue
        ac = np.correlate(f, f, 'full')[win - 1:]
        ac /= ac[0] + 1e-12
        lo, hi = int(sr / fmax), int(sr / fmin)
        seg = ac[lo:hi]
        if len(seg) == 0:
            continue
        peak = np.argmax(seg)
        if seg[peak] > 0.3:
            out[i] = sr / (lo + peak)
    return out


def spectrum_stats(fr, sr, win=2048):
    spec = np.abs(np.fft.rfft(fr, axis=1))
    freqs = np.fft.rfftfreq(win, 1 / sr)
    tot = spec.sum(axis=1) + 1e-12
    centroid = (spec * freqs[None, :]).sum(axis=1) / tot
    return spec, freqs, centroid


def harmonicity(spec, freqs, pitch, sr):
    """share of spectral energy within +-2% of integer multiples of f0."""
    out = np.zeros(len(pitch))
    for i, f0 in enumerate(pitch):
        if f0 <= 0:
            continue
        s = spec[i]
        mask = np.zeros(len(freqs), dtype=bool)
        for h in range(1, int(freqs[-1] / f0) + 1):
            mask |= np.abs(freqs - h * f0) < 0.02 * h * f0
        out[i] = s[mask].sum() / (s.sum() + 1e-12)
    return out


def onsets(fr, hop, sr):
    energy = (fr ** 2).sum(axis=1)
    flux = np.diff(energy, prepend=energy[0])
    flux[flux < 0] = 0
    thr = flux.mean() + 2.5 * flux.std()
    peaks, last = [], -10 ** 9
    for i, v in enumerate(flux):
        if v > thr and i - last > sr / hop * 0.08:
            peaks.append(i * hop / sr)
            last = i
    return peaks, energy


def lead_track(spec, freqs, lo=250, hi=1200):
    """strongest peak in the lead band — follows the melodic voice,
    not the mix's autocorrelation (which the bass floor confounds)."""
    band = (freqs >= lo) & (freqs <= hi)
    out = np.zeros(len(spec))
    for i, s in enumerate(spec):
        sb = s * band
        if sb.max() > 1e-9:
            out[i] = freqs[np.argmax(sb)]
    return out


def dissect(path):
    x, sr = load(path)
    fr, nfr = framesig(x, sr)
    pit = pitch_track(fr, sr)
    spec, freqs, cent = spectrum_stats(fr, sr)
    harm = harmonicity(spec, freqs, pit, sr)
    ons, energy = onsets(fr, 512, sr)
    lead = lead_track(spec, freqs)

    voiced = pit[pit > 0]
    dur = len(x) / sr
    lines = []
    lines.append(f'== dissection: {path} ==')
    lines.append(f'duration {dur:.1f}s, sr {sr}')
    lines.append(f'voiced frames: {len(voiced) / nfr * 100:.0f}%')
    if len(voiced):
        lines.append(f'pitch: median {np.median(voiced):.0f}Hz, '
                     f'range {voiced.min():.0f}-{voiced.max():.0f}Hz')
        semi = 12 * np.log2(voiced.max() / max(voiced.min(), 1))
        lines.append(f'melodic span: {semi:.1f} semitones')
    hv = harm[pit > 0]
    if len(hv):
        lines.append(f'harmonicity: mean {hv.mean():.2f} '
                     f'(1=flute-pure, 0=noise)')
    cv = cent[energy > energy.max() * 0.01]
    lines.append(f'brightness (spectral centroid): median {np.median(cv):.0f}Hz, '
                 f'spread {cv.std():.0f}Hz')
    lv = lead[(lead > 0) & (energy > energy.max() * 0.02)]
    if len(lv):
        lines.append(f'lead voice (250-1200Hz band peak): median '
                     f'{np.median(lv):.0f}Hz, range {lv.min():.0f}-{lv.max():.0f}Hz')
    lines.append(f'onsets: {len(ons)} in {dur:.1f}s = {len(ons) / dur:.2f}/s')
    if len(ons) > 2:
        ioi = np.diff(ons)
        lines.append(f'inter-onset intervals: median {np.median(ioi):.2f}s, '
                     f'regularity (cv) {ioi.std() / ioi.mean():.2f}')
    # envelope shape of the loudest onset region
    if len(ons):
        t0 = int(ons[len(ons) // 2] * sr)
        seg = x[t0:t0 + sr // 2]
        if len(seg) > 100:
            e = np.sqrt(np.convolve(seg ** 2, np.ones(256) / 256, 'same'))
            pk = np.argmax(e)
            attack = pk / sr * 1000
            decay = (len(e) - pk) / sr * 1000
            lines.append(f'typical event: attack {attack:.0f}ms, '
                         f'decay-tail {decay:.0f}ms '
                         f'({"plucked" if attack < 20 else "blown/bowed"})')
    report = '\n'.join(lines)
    print(report)
    return dict(pitch=pit, cent=cent, harm=harm, ons=ons, energy=energy,
                x=x, sr=sr, report=report)


if __name__ == '__main__':
    dissect(sys.argv[1] if len(sys.argv) > 1 else 'chime/melody.wav')
