"""Space Explained soundtrack: music bed, on-screen sound events, and the V / T mixes (docs/engines/space_explained.md §8).

Bed (proposal for the milestone clip): Deep Sky's approved space_drone warmth with a little more movement - a
slow, quiet soft_vibes arpeggio (Tiny World's round mallet, nothing above ~1.6 kHz) on the drone's chord -
plus event notes the picture causes (a lap completed, a crossing). Every pitched note is checked to stay in
MIDI 36-96 (CLAUDE.md); a note outside is an error here, not folded.

V = voice + the same music ducked under speech (~9 dB); T = the music alone. Both mastered with one constant
gain to their loudness target, so nothing pumps.
"""
import os
import subprocess

import numpy as np
from scipy.io import wavfile

from audio import synth
from audio.synth import SR, midi
from engine.video import measure_lufs

NOTE_MIN, NOTE_MAX = 36, 96


def _note(m):
    if not NOTE_MIN <= m <= NOTE_MAX:
        raise ValueError(f"note {m} outside MIDI {NOTE_MIN}-{NOTE_MAX}")
    return midi(m)


def chord_at(chords, t, dur):
    return chords[min(len(chords) - 1, int(t / dur * len(chords)))]


def tones(chord, lo, hi):
    pcs = {m % 12 for m in chord}
    return [m for m in range(lo, hi + 1) if m % 12 in pcs]


def bed(dur, rng, chords, drone=None, arp=None, drone_gain=0.35):
    """(n, 2) float32: the drone over the whole clip plus the arpeggio. The drone sits lower than in Deep Sky
    (there it is the whole soundtrack; here it's a floor under the notes and the voice)."""
    for c in chords:
        for m in c:
            _note(m)
    out = synth.space_drone(dur, rng, chords, **(drone or {})).astype(np.float64) * drone_gain
    a = {"bar": 4.8, "steps": [0.0, 1.6, 3.2], "range": [57, 74], "gain": 0.07, **(arp or {})}
    buf = np.zeros_like(out)
    k = 0
    while k * a["bar"] < dur:
        t0 = k * a["bar"]
        ts = tones(chord_at(chords, t0, dur), *a["range"])
        for j, off in enumerate(a["steps"]):
            m = ts[(k * 2 + j * 2) % len(ts)]
            synth.place(buf, synth.soft_vibes(_note(m), 3.2) * a["gain"] * rng.uniform(0.8, 1.0),
                        t0 + off + rng.uniform(0, 0.08), pan=rng.uniform(-0.35, 0.35))
        k += 1
    out += synth.reverb(buf, decay=3.8, wet=0.45, tone=2600, rng=rng)
    return out.astype(np.float32)


def events(dur, hits, rng):
    """hits: [(t, instrument, midi, vel, pan)] -> (n, 2) float32, with a soft room."""
    buf = np.zeros((int(round(dur * SR)), 2))
    for t, inst, m, vel, pan in hits:
        f = _note(m)
        sig = synth.soft_vibes(f, 3.5) if inst == "soft_vibes" else synth.sky_swell(f, 7.0, 2.5, 4.0)
        synth.place(buf, sig * vel, t, pan)
    return synth.reverb(buf, decay=4.0, wet=0.5, tone=2400, rng=rng).astype(np.float32)


def speech_mask(words, n, offset=0.0, pre=0.18, post=0.35, bridge=0.7, ramp=0.3):
    """0..1 per sample: 1 while the narrator speaks (gaps under `bridge` s count as speech), smooth ramps."""
    spans = []
    for w in words:
        a, b = w["start"] + offset - pre, w["end"] + offset + post
        if spans and a - spans[-1][1] < bridge:
            spans[-1][1] = b
        else:
            spans.append([a, b])
    m = np.zeros(n, np.float32)
    for a, b in spans:
        m[max(0, int(a * SR)):max(0, int(b * SR))] = 1
    k = int(ramp * SR)
    win = np.hanning(2 * k + 1).astype(np.float32)
    return np.clip(np.convolve(m, win / win.sum(), "same"), 0, 1)


def load_voice(mp3, n, at, tmp):
    """The narration mp3 as mono float32, placed at `at` seconds (negative: its start is cut), length n."""
    wav = os.path.join(tmp, "voice.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), wav], check=True)
    sr, x = wavfile.read(wav)
    x = x.astype(np.float32) / (32768.0 if x.dtype == np.int16 else 1.0)
    out = np.zeros(n, np.float32)
    i = int(round(at * SR))
    src = x[max(0, -i):]
    j0 = max(0, i)
    m = min(n - j0, len(src))
    out[j0:j0 + m] = src[:m]
    return out


def master(mix, path, lufs, fade_in=0.4, fade_out=1.5):
    """One constant gain to `lufs`, stray peaks softly limited under -2 dBFS (AAC adds ~1 dB), 24-bit WAV. -> (path, stats)."""
    mix = mix.astype(np.float32).copy()
    a, b = int(fade_in * SR), int(fade_out * SR)
    mix[:a] *= np.linspace(0, 1, a, dtype=np.float32)[:, None] ** 2
    mix[-b:] *= np.linspace(1, 0, b, dtype=np.float32)[:, None] ** 2
    raw = path + ".raw.wav"
    wavfile.write(raw, SR, mix)
    l0, p0 = measure_lufs(raw)
    gain = lufs - l0
    af = f"volume={gain:.4f}dB"
    if p0 + gain > -1.5:
        # a few transients (a plosive, two notes landing together) would otherwise hold the whole video quiet
        # (SX0003 came out at -20.4 LUFS): a soft limiter takes up to 6 dB off those peaks, the rest is held
        over = p0 + gain + 1.5
        if over > 6.0:
            print(f"  WARNING: {lufs} LUFS would peak at {p0 + gain:.1f} dBFS; held {over - 6:.1f} dB lower", flush=True)
            gain -= over - 6.0
        af = f"volume={gain:.4f}dB,alimiter=limit={10 ** (-2.0 / 20):.4f}:attack=5:release=80:level=false"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", af,
                    "-c:a", "pcm_s24le", path], check=True)
    os.remove(raw)
    l1, p1 = measure_lufs(path)
    return path, {"lufs": round(l1, 2), "peak_dbfs": round(p1, 2), "gain_db": round(gain, 2)}


def band_energy(x, bands=((0, 150), (150, 1000), (1000, 2500), (2500, 5000), (5000, 22050))):
    """Share of energy per band (owner: keep 1-5 kHz low), from 1 s windows of a mono mix."""
    m = x.mean(axis=1).astype(np.float64)
    spec = np.zeros(SR // 2 + 1)
    for i in range(0, max(1, len(m) - SR), SR // 2):
        seg = m[i:i + SR]
        if len(seg) == SR:
            spec += np.abs(np.fft.rfft(seg * np.hanning(SR))) ** 2
    f = np.fft.rfftfreq(SR, 1 / SR)
    tot = spec.sum() + 1e-12
    return {f"{lo}-{hi}": round(float(spec[(f >= lo) & (f < hi)].sum() / tot), 4) for lo, hi in bands}
