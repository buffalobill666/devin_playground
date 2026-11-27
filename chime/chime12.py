"""chime12 — «Ария без дыхания» (Ария Любы).

Music as marginalia, second piece: on Luba Luft.
Concept: the tell of the android singer is not error — it's the ABSENCE
of breath. A vocal line of inhuman continuity: phrases too long, no
gasping, no vibrato drift, perfect legato, pitch mechanically steady.
Beauty that never needs air. The listener's unease is the test:
not what the voice does wrong, but what it never has to do.

Structure: three ever-longer phrases (each more impossible than the last),
then a human answer — the same melody WITH breath: broken, gasping,
shorter phrases, drifting vibrato. The book's question rendered audible:
which one is alive?
"""
import numpy as np
import wave, struct

SR = 44100
rng = np.random.RandomState(12)

def sine_tone(freq, dur, amp=0.3, attack=0.01, release=0.05, vibrato=0.0, vib_rate=5.0, drift=0.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    if vibrato > 0:
        # drifting vibrato: rate wanders slightly (human), depth constant
        phase = np.cumsum(vib_rate + drift * rng.randn(n) / SR)
        mod = vibrato * np.sin(2 * np.pi * phase * t / max(t) * dur / dur) if False else vibrato * np.sin(2 * np.pi * vib_rate * t + drift * t * t)
        f = freq * (1 + mod)
    else:
        f = freq * np.ones(n)
    phase = 2 * np.pi * np.cumsum(f) / SR
    sig = np.sin(phase)
    # add slight harmonics for vocal-ish timbre
    sig += 0.35 * np.sin(2 * phase)
    sig += 0.12 * np.sin(3 * phase)
    env = np.ones(n)
    na = max(1, int(SR * attack)); nr = max(1, int(SR * release))
    env[:na] = np.linspace(0, 1, na)
    env[-nr:] = np.linspace(1, 0, nr)
    return sig * env * amp

# aria melody (stepwise, Mozart-ish contour) in Hz — mixolydian-ish line
NOTE = {'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00,
        'A4': 440.00, 'B4': 493.88, 'C5': 523.25, 'D5': 587.33, 'E5': 659.25}
melody = ['E4', 'G4', 'A4', 'G4', 'E4', 'D4', 'E4', 'G4', 'A4', 'C5', 'B4', 'A4', 'G4', 'E4']

def render_android(sr_total):
    """Inhuman continuity: the whole melody in three huge seamless arcs, no breaths."""
    out = np.zeros(int(SR * sr_total))
    pos = int(SR * 0.5)
    arcs = [(melody[:5], 1.9), (melody[5:9], 1.7), (melody[9:], 1.55)]
    for notes, note_dur in arcs:
        for nm in notes:
            dur = note_dur  # absurdly long notes, overlapping legato
            tone = sine_tone(NOTE[nm], dur, amp=0.32, attack=0.08, release=0.08,
                             vibrato=0.004, vib_rate=5.0, drift=0.0)  # mechanical vibrato: constant, shallow
            end = min(len(out), pos + len(tone))
            out[pos:end] += tone[:end - pos]
            pos += int(SR * note_dur * 0.97)  # overlap = seamless legato, no air
    return out, pos / SR

def render_human(start, sr_total):
    """Same melody, alive: short phrases, audible breath gaps, drifting vibrato."""
    out = np.zeros(int(SR * sr_total))
    pos = int(SR * start)
    phrases = [melody[:3], melody[3:6], melody[6:9], melody[9:12], melody[12:]]
    for pi, notes in enumerate(phrases):
        for nm in notes:
            dur = 0.55 + rng.rand() * 0.15  # short, uneven
            tone = sine_tone(NOTE[nm], dur, amp=0.30, attack=0.03, release=0.09,
                             vibrato=0.012, vib_rate=4.6 + rng.rand(), drift=0.6)
            end = min(len(out), pos + len(tone))
            out[pos:end] += tone[:end - pos]
            pos += int(SR * dur * 0.9)
        pos += int(SR * (0.5 + rng.rand() * 0.3))  # the breath: audible, irregular
    return out

def main():
    total = 58.0
    android, end_t = render_android(total)
    human = render_human(end_t + 1.5, total)
    mix = android + human
    # soft master
    mix = mix / max(1e-9, np.max(np.abs(mix))) * 0.85
    pcm = (mix * 32767).astype(np.int16)
    with wave.open('chime/chime12.wav', 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'chime12.wav written, {len(pcm)/SR:.1f}s')

if __name__ == '__main__':
    main()
