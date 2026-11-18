"""Code-generated music samples for the satisfying-videos channel.

Renders three ~40s stereo clips, all synthesized from scratch with numpy:
  1. ambient_pad      - slow evolving chords + soft bells (lava lamp / ambient)
  2. marble_race      - light beat + pitched collision plinks + winner chime (races)
  3. music_box        - glassy generative arpeggios (physics toys / pendulums)

The instruments (pad_note, bell, plink, kick, hat, whoosh) and the *_bed()
generators are also imported by engine/audio.py, which builds each video's
soundtrack from on-screen events on top of one of these beds.
Run `python audio/synth.py` to regenerate the three approved samples.
"""
import subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

SR = 44100
rng = np.random.default_rng(7)
_RNG = rng  # default stream used by the sample pieces below


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def adsr(n, a, r, sustain_len=None):
    env = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    env[:na] = np.linspace(0, 1, na) ** 2
    if nr:
        env[-nr:] *= np.linspace(1, 0, nr) ** 2
    return env


def place(buf, sig, start, pan=0.0):
    """Mix mono sig into stereo buf at start seconds with constant-power pan."""
    i = int(start * SR)
    if i < 0:                                   # starts before the buffer: keep only the audible tail
        sig, i = sig[-i:], 0
    j = min(len(buf), i + len(sig))
    if j <= i:
        return
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    buf[i:j, 0] += sig[: j - i] * l
    buf[i:j, 1] += sig[: j - i] * r


def reverb(x, decay=3.5, wet=0.35, tone=6000, rng=None):
    rng = rng if rng is not None else _RNG
    n = int(decay * SR)
    tt = np.arange(n) / SR
    out = np.zeros_like(x)
    sos = butter(2, tone, "low", fs=SR, output="sos")
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-6.9 * tt / decay)
        ir = sosfilt(sos, ir)
        ir /= np.sqrt(np.sum(ir ** 2))
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return x * (1 - wet) + out * wet * 1.5


def master(x, name):
    x = x / (np.max(np.abs(x)) + 1e-9) * 1.2
    x = np.tanh(x) * 0.89
    fade = int(1.5 * SR)
    x[:fade] *= np.linspace(0, 1, fade)[:, None]
    x[-fade * 2:] *= np.linspace(1, 0, fade * 2)[:, None]
    wav = f"audio/samples/{name}.wav"
    wavfile.write(wav, SR, (x * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "192k",
                    wav.replace(".wav", ".mp3")], check=True)
    print("wrote", name)


# ---------- instruments ----------

def pad_note(f, dur, a=2.5, r=3.0, rng=None):
    rng = rng if rng is not None else _RNG
    tt = t_axis(dur)
    sig = np.zeros_like(tt)
    bright = 0.5 + 0.35 * np.sin(2 * np.pi * tt / dur * 0.7 + rng.uniform(0, 6))
    for cents in (-8, 0, 8):
        fd = f * 2 ** (cents / 1200)
        ph = rng.uniform(0, 2 * np.pi)
        for n in range(1, 9):
            sig += np.sin(2 * np.pi * fd * n * tt + ph * n) * np.exp(-n / (1.2 + 3 * bright)) / n
    return sig * adsr(len(tt), a, r) / 6


def bell(f, dur=4.0, index=2.5, ratio=3.5):
    tt = t_axis(dur)
    env = np.exp(-tt * 1.6)
    mod = index * np.exp(-tt * 3) * np.sin(2 * np.pi * f * ratio * tt)
    sig = np.sin(2 * np.pi * f * tt + mod) * env
    sig[: int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))
    return sig


def plink(f, dur=0.8):
    tt = t_axis(dur)
    sig = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 7)
           + 0.35 * np.sin(2 * np.pi * f * 4 * tt) * np.exp(-tt * 25)
           + 0.1 * np.sin(2 * np.pi * f * 9.2 * tt) * np.exp(-tt * 60))
    sig[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return sig


def kick():
    tt = t_axis(0.35)
    freq = 45 + 90 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9)


def hat(rng=None):
    rng = rng if rng is not None else _RNG
    n = int(0.05 * SR)
    sos = butter(2, 7000, "high", fs=SR, output="sos")
    return sosfilt(sos, rng.standard_normal(n)) * np.exp(-np.arange(n) / SR * 80)


def whoosh(dur=0.6, rng=None):
    """Filtered noise swell - used for ring breaks / gate opens."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    tt = np.arange(n) / SR
    sos = butter(2, [400, 3000], "band", fs=SR, output="sos")
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
    return sosfilt(sos, rng.standard_normal(n)) * env * 0.5


# ---------- Foundry machine sounds (dark-toned: low-passed harder than Bright Lights) ----------

def _lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def _bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def _smooth_noise(n, rate, rng):
    """Slowly wandering 0..1 control signal, `rate` changes per second."""
    k = max(2, int(n / SR * rate) + 2)
    pts = rng.uniform(0, 1, k)
    return np.interp(np.arange(n), np.linspace(0, n, k), pts)


def sizzle(dur, rng=None):
    """Molten metal landing in a mold: hissing noise bed + sparse crackles, with a tail."""
    rng = rng if rng is not None else _RNG
    tail = 0.7
    n = int((dur + tail) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.08, 0, 1) * np.where(tt < dur, 1.0, np.exp(-(tt - dur) * 6))
    hiss = _bp(rng.standard_normal(n), 1800, 6500) * (0.55 + 0.45 * _smooth_noise(n, 9, rng))
    pops = np.zeros(n)
    t = rng.exponential(1 / 28)
    while t < dur + tail * 0.5:
        i = int(t * SR)
        m = min(n - i, int(0.012 * SR))
        pops[i:i + m] += rng.standard_normal(m) * np.exp(-np.arange(m) / SR * 500) * rng.uniform(0.4, 1.4)
        t += rng.exponential(1 / 28)
    pops = _bp(pops, 1200, 7000)
    return _lp(hiss * 0.35 + pops * 0.8, 7000) * env


def crackle(dur=0.2, rng=None):
    """A few tiny high crackles - sparks."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    out = np.zeros(n)
    for _ in range(rng.integers(3, 7)):
        i = int(rng.uniform(0, 0.75) * n)
        m = min(n - i, int(0.006 * SR))
        out[i:i + m] += rng.standard_normal(m) * np.exp(-np.arange(m) / SR * 900) * rng.uniform(0.5, 1)
    return _lp(_bp(out, 2500, 9000), 8000) * 0.6


def clack(f, dur=0.3):
    """Conveyor clack: short pitched wood/metal tick (follows a scale like the plinks)."""
    tt = t_axis(dur)
    rng = np.random.default_rng(int(f * 10))
    body = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 38)
            + 0.3 * np.sin(2 * np.pi * f * 2.71 * tt) * np.exp(-tt * 70))
    click = _bp(rng.standard_normal(len(tt)), 900, 4000) * np.exp(-tt * 160) * 0.5
    sig = _lp(body + click, 4500)
    sig[:40] *= np.linspace(0, 1, 40)
    return sig


def clunk(f, dur=1.4):
    """Heavy two-layer thud (low sine sweep + noise thump) with a small metallic ring at f."""
    tt = t_axis(dur)
    rng = np.random.default_rng(int(f * 10) + 1)
    thud = np.sin(2 * np.pi * np.cumsum(42 + 70 * np.exp(-tt * 25)) / SR) * np.exp(-tt * 9)
    thump = _lp(rng.standard_normal(len(tt)), 380) * np.exp(-tt * 28) * 1.6
    ring = sum(w * np.sin(2 * np.pi * f * r * tt) for r, w in ((1, 1), (2.76, 0.5), (5.4, 0.25)))
    ring = ring * np.exp(-tt * 3.5) * 0.18
    sig = thud + thump + _lp(ring, 3000)
    sig[:30] *= np.linspace(0, 1, 30)
    return sig


def hiss(dur, rng=None):
    """Steam hiss: filtered noise that swells in and tails off."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.5) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.25, 0, 1) * np.clip((dur + 0.5 - tt) / 0.7, 0, 1) ** 1.5
    sig = _bp(rng.standard_normal(n), 1500, 5000) * (0.7 + 0.3 * _smooth_noise(n, 4, rng))
    return _lp(sig, 5500) * env * 0.5


def slide(dur, rng=None):
    """Metal bar sliding down a steel chute: low gritty scrape with a rising pitch."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.3) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.05, 0, 1) * np.clip((dur + 0.3 - tt) / 0.4, 0, 1)
    grit = _bp(rng.standard_normal(n), 250, 1600) * (0.5 + 0.5 * _smooth_noise(n, 30, rng))
    f = 140 + 90 * np.clip(tt / max(dur, 1e-3), 0, 1)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    return _lp(grit * 0.6 + tone, 2200) * env


def thud(f=None, dur=1.2):
    """Press hit: low sine sweep + noise thump, no ring."""
    tt = t_axis(dur)
    rng = np.random.default_rng(3)
    body = np.sin(2 * np.pi * np.cumsum(34 + 90 * np.exp(-tt * 18)) / SR) * np.exp(-tt * 5)
    thump = _lp(rng.standard_normal(len(tt)), 300) * np.exp(-tt * 22) * 2.0
    sig = body + thump
    sig[:30] *= np.linspace(0, 1, 30)
    return sig


def weld(dur, rng=None):
    """Welding arc: buzzy mains-hum noise with sparse crackles."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.15) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.03, 0, 1) * np.clip((dur + 0.15 - tt) / 0.15, 0, 1)
    buzz = _bp(rng.standard_normal(n), 900, 4200) * (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 100 * tt)))
    return (_lp(buzz, 5000) * 0.35 + crackle(dur + 0.15, rng)[:n] * 0.8) * env


def servo(dur, rng=None):
    """Robot arm joint: soft gliding whine, low-passed so it stays dark."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = np.clip(tt / max(dur, 1e-3), 0, 1)
    f = 190 + 110 * np.sin(np.pi * u)
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    env = np.sin(np.pi * u) ** 0.6
    return _lp(tone * 0.5 + _bp(rng.standard_normal(n), 300, 1200) * 0.12, 1300) * env


def spray(dur, rng=None):
    """Spray gun: pink-noise burst with a soft swell."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.3) * SR)
    spec = np.fft.rfft(rng.standard_normal(n))
    spec /= np.sqrt(np.maximum(np.arange(len(spec)), 1))
    pink = np.fft.irfft(spec, n)
    pink /= np.max(np.abs(pink)) + 1e-9
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.12, 0, 1) * np.clip((dur + 0.3 - tt) / 0.35, 0, 1)
    return _lp(_bp(pink, 400, 7000), 6000) * env * 0.9


def clap(dur=0.15, rng=None):
    """One hand clap: three tiny noise bursts a few ms apart, band-passed, kept soft."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    out = np.zeros(n)
    for k, ms in enumerate((0, 7, 15)):
        i = int(ms / 1000 * SR)
        m = n - i
        out[i:] += rng.standard_normal(m) * np.exp(-np.arange(m) / SR * (90 if k == 2 else 260)) * (0.6 + 0.2 * k)
    return _lp(_bp(out, 800, 3200), 4500) * 0.5


def motor(dur, rng=None):
    """Electric hoist / conveyor motor: low hum that spins up and down, plus gear noise."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.4) * SR)
    tt = np.arange(n) / SR
    spin = np.clip(tt / 0.35, 0, 1) * np.clip((dur + 0.4 - tt) / 0.5, 0, 1)
    f = 46 * (0.75 + 0.25 * spin)
    ph = 2 * np.pi * np.cumsum(f) / SR
    hum = sum(np.sin(k * ph) / k for k in range(1, 7))
    gear = _bp(rng.standard_normal(n), 220, 900) * 0.35
    return _lp(hum * 0.5 + gear, 1400) * spin ** 1.5


# ---------- tree-monster sounds (Foundry, docs/engines/foundry_monsters.md) ----------

def saw(dur, rng=None):
    """Circular saw biting into wood: a low buzzing whine with gritty chatter, kept dark."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.25) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.06, 0, 1) * np.clip((dur + 0.25 - tt) / 0.3, 0, 1)
    f = 118 * (1 - 0.12 * np.clip(tt / max(dur, 1e-3), 0, 1))      # bogs down a little in the cut
    ph = 2 * np.pi * np.cumsum(f) / SR
    buzz = sum(np.sin(k * ph) / k ** 0.8 for k in range(1, 9))
    chatter = _bp(rng.standard_normal(n), 600, 2600) * (0.4 + 0.6 * _smooth_noise(n, 40, rng))
    return _lp(buzz * 0.22 + chatter * 0.5, 2600) * env


def creak(dur, rng=None):
    """Tree starting to tip: slow, low wooden groan with a few cracks."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = np.clip(tt / max(dur, 1e-3), 0, 1)
    f = 70 + 40 * u + 8 * _smooth_noise(n, 12, rng)
    ph = 2 * np.pi * np.cumsum(f) / SR
    pulses = (np.sin(2 * np.pi * np.cumsum(18 + 20 * u) / SR) > 0.6).astype(float)
    body = (np.sin(ph) + 0.5 * np.sin(2.3 * ph)) * _lp(pulses, 60)
    cracks = crackle(dur, rng)[:n] * 1.5
    env = np.sin(np.pi * u) ** 0.5
    return _lp(body * 0.5 + _lp(cracks, 2500), 1600) * env


def rustle(dur, rng=None):
    """Leaves shaking: soft broadband noise in little bursts."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.3) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.05, 0, 1) * np.exp(-np.clip(tt - dur * 0.3, 0, None) * 3.0)
    bursts = _smooth_noise(n, 25, rng) ** 3
    return _lp(_bp(rng.standard_normal(n), 1200, 6000), 5000) * bursts * env * 0.8


def leaf_settle(dur, rng=None):
    """Dry leaves blown up and settling back down: a warm, papery patter that thins out (kept below ~1.6 kHz:
    the owner hears 1-5 kHz noise as harsh)."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.3) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.04, 0, 1) * np.exp(-tt * 2.2 / max(0.3, dur))
    bursts = _smooth_noise(n, 30, rng) ** 4
    return _lp(_bp(rng.standard_normal(n), 250, 1500), 1500) * bursts * env * 1.1


def splash(dur=0.6, rng=None):
    """Something dropping into thick liquid: low plop + bubbly tail."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.4) * SR)
    tt = np.arange(n) / SR
    plop = np.sin(2 * np.pi * np.cumsum(220 * np.exp(-tt * 9) + 60) / SR) * np.exp(-tt * 14)
    wash = _bp(rng.standard_normal(n), 300, 2400) * np.exp(-tt * 5) * 0.4
    return _lp(plop * 0.8 + wash + bubble(dur + 0.4, rng)[:n] * 0.4, 3000)


def bubble(dur, rng=None):
    """Thick liquid bubbling: random little resonant blips."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    out = np.zeros(n)
    t = rng.exponential(1 / 9)
    while t < dur - 0.1:
        i = int(t * SR)
        m = min(n - i, int(0.09 * SR))
        tb = np.arange(m) / SR
        f0 = rng.uniform(180, 520)
        out[i:i + m] += np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2.5 * tb)) / SR) * np.exp(-tb * 45) * rng.uniform(0.3, 1)
        t += rng.exponential(1 / 9)
    return _lp(out, 2200) * 0.6


def rush(dur, rng=None):
    """Rushing water: deep, rolling filtered noise (kept low and warm - no hiss on top)."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.6) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.4, 0, 1) * np.clip((dur + 0.6 - tt) / 0.9, 0, 1) ** 1.3
    body = _bp(rng.standard_normal(n), 90, 900) * (0.65 + 0.35 * _smooth_noise(n, 3, rng))
    churn = _bp(rng.standard_normal(n), 400, 1400) * _smooth_noise(n, 9, rng) ** 2 * 0.35
    return _lp(body + churn, 1500) * env * 0.9


def air_blow(dur, rng=None):
    """A small hairdryer from a little way off: soft, low airy whoosh with a faint fan hum (no hiss on top -
    the owner hears 1-5 kHz noise as harsh)."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.5) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.3, 0, 1) * np.clip((dur + 0.5 - tt) / 0.5, 0, 1) ** 1.4
    air = _bp(rng.standard_normal(n), 140, 1100) * (0.8 + 0.2 * _smooth_noise(n, 5, rng))
    hum = 0.12 * np.sin(2 * np.pi * 118 * tt + 0.3 * np.sin(2 * np.pi * 0.7 * tt))
    return _lp(air + hum, 1300) * env * 0.8


def gurgle(dur, rng=None):
    """Plug pulled: swirling low drain with bubbles."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.4) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / 0.3, 0, 1) * np.clip((dur + 0.4 - tt) / 0.6, 0, 1)
    swirl = _bp(rng.standard_normal(n), 120, 700) * (0.5 + 0.5 * np.sin(2 * np.pi * 3.5 * tt))
    return _lp(swirl * 0.7 + bubble(dur + 0.4, rng)[:n] * 0.9, 1800) * env


# ---------- beds (duration-flexible, no random melodic events) ----------
# Each bed returns (stereo_buffer, scale) where `scale` is the MIDI note set
# that on-screen events should draw from so they stay consonant with the bed.

AMBIENT_CHORDS = [[48, 55, 59, 62, 64], [45, 52, 55, 59, 60], [41, 48, 52, 55, 59], [40, 47, 50, 55, 57]]
AMBIENT_SCALE = [72, 74, 76, 79, 81, 84]
RACE_SCALE = [69, 72, 74, 76, 79, 81, 84, 86, 88]
MUSIC_BOX_CHORDS = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 66]]
MUSIC_BOX_SCALE = [69, 72, 74, 76, 79, 81, 84, 86, 88, 91, 93]
INDUSTRIAL_SCALE = [57, 60, 62, 64, 67, 69, 72, 74]     # A minor pentatonic, kept low and dark


def ambient_bed(dur, rng, step=9.0, gain=0.5):
    """Same slow open-voiced chords as ambient_pad(), any length, no bells."""
    buf = np.zeros((int(dur * SR), 2))
    k = 0
    while k * step < dur:
        ch = AMBIENT_CHORDS[k % 4]
        for i, m in enumerate(ch):
            place(buf, pad_note(midi(m), step + 3.5, rng=rng) * gain, k * step, pan=(i / 4 - 0.5) * 0.8)
        k += 1
    return buf, AMBIENT_SCALE


def race_bed(dur, rng, bpm=104, start=2.0, beat_gain=1.0):
    """Beat + bass + pad from marble_race(); collision plinks come from events."""
    beat = 60 / bpm
    buf = np.zeros((int(dur * SR), 2))
    b = start
    while b < dur - 1.5:
        place(buf, kick() * 0.55 * beat_gain, b)
        place(buf, hat(rng) * 0.12 * beat_gain, b + beat / 2, pan=0.3)
        b += beat
    roots = [45, 41, 48, 43]
    for k in range(int(dur / (8 * beat)) + 1):
        root = roots[k % 4]
        for m in (root, root + 12 + 7, root + 12 + 16 if root != 45 else root + 24):
            place(buf, pad_note(midi(m), 8 * beat + 1, a=0.4, r=1.0, rng=rng) * 0.18, k * 8 * beat)
    return buf, RACE_SCALE


def music_box_bed(dur, rng, bar=4.48, gain=0.25):
    """Soft low drone following music_box() chords; the bells come from events."""
    buf = np.zeros((int(dur * SR), 2))
    k = 0
    while k * bar < dur:
        ch = MUSIC_BOX_CHORDS[k % 4]
        place(buf, pad_note(midi(ch[0] - 12), bar + 2, a=1.0, r=1.5, rng=rng) * gain, k * bar)
        place(buf, pad_note(midi(ch[2] - 12), bar + 2, a=1.5, r=1.5, rng=rng) * gain * 0.5, k * bar, pan=0.3)
        k += 1
    return buf, MUSIC_BOX_SCALE


def chord_bed(dur, rng, chords=(), gain=0.3):
    """Soft pad following an explicit chord timeline: chords = [[start_s, len_s, [midi...]], ...].

    Used when events play a real melody, so the accompaniment matches its harmony.
    """
    buf = np.zeros((int(dur * SR), 2))
    for start, length, notes in chords:
        for j, m in enumerate(notes):
            place(buf, pad_note(midi(m), length + 1.5, a=0.25, r=1.2, rng=rng) * gain / len(notes) * 2,
                  start, pan=(j / max(1, len(notes) - 1) - 0.5) * 0.6)
    return buf, MUSIC_BOX_SCALE


def metal_resonance(f, dur=5.0):
    """Distant struck girder: inharmonic partials, slow decay, dull."""
    tt = t_axis(dur)
    sig = sum(w * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * d)
              for r, w, d in ((1, 1, 0.9), (2.76, 0.6, 1.4), (5.40, 0.35, 2.2), (8.93, 0.2, 3.5)))
    sig[:200] *= np.linspace(0, 1, 200)
    return _lp(sig, 2200)


def industrial_bed(dur, rng, root=33, gain=1.0, clang_gap=(5.0, 10.0), bell_gap=(8.0, 14.0),
                   pulse_from=None, pulse_bpm=96, pulse_gain=1.0):
    """Foundry bed: low detuned drone (root A1) with slow filter movement, room rumble,
    distant metallic resonances and a sparse low bell. No drums - except, from `pulse_from`
    (the finale race), a soft dark pulse that fades in."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    buf = np.zeros((n, 2))
    # drone: root, fifth, octave, 12th; detuned copies spread left/right; the harmonic
    # roll-off breathes slowly, which reads as a slow low-pass sweep
    for m, g in ((root, 1.0), (root + 7, 0.5), (root + 12, 0.45), (root + 19, 0.16)):
        for cents, pan in ((-7, -0.6), (0, 0.0), (6, 0.6)):
            f = midi(m) * 2 ** (cents / 1200)
            bright = 0.5 + 0.5 * np.sin(2 * np.pi * tt / rng.uniform(11, 19) + rng.uniform(0, 6.3))
            sig = np.zeros(n)
            for k in range(1, 11):
                sig += np.sin(2 * np.pi * f * k * tt + rng.uniform(0, 6.3)) * np.exp(-k / (0.8 + 2.4 * bright)) / k
            place(buf, sig * g * 0.12, 0, pan=pan)
    rumble = _lp(np.cumsum(rng.standard_normal(n)) * 0.002, 140, order=4)
    rumble -= _lp(rumble, 20)
    buf += rumble[:, None] * 0.6
    t = rng.uniform(1.0, 3.0)
    while t < dur - 1:
        f = midi(rng.choice([45, 48, 52, 57]))
        place(buf, metal_resonance(f) * 0.05, t, pan=rng.uniform(-0.8, 0.8))
        t += rng.uniform(*clang_gap)
    t = rng.uniform(3.0, 6.0)
    while t < dur - 2:
        place(buf, bell(midi(rng.choice([45, 52, 57])), dur=5.0, index=0.9) * 0.07, t, pan=rng.uniform(-0.4, 0.4))
        t += rng.uniform(*bell_gap)
    if pulse_from is not None:
        beat = 60.0 / pulse_bpm
        tt_k = t_axis(0.5)
        thump = np.sin(2 * np.pi * np.cumsum(48 + 40 * np.exp(-tt_k * 20)) / SR) * np.exp(-tt_k * 9)
        tick = _lp(_bp(rng.standard_normal(int(0.06 * SR)), 1500, 5000), 4000) * np.exp(-np.arange(int(0.06 * SR)) / SR * 60)
        b, i = pulse_from, 0
        while b < dur - 0.5:
            fade = min(1.0, (b - pulse_from) / (8 * beat))
            place(buf, thump * 0.22 * pulse_gain * fade, b)
            if i % 2 == 1:
                place(buf, tick * 0.05 * pulse_gain * fade, b + beat / 2, pan=0.25)
            b += beat
            i += 1
    for ch in range(2):
        buf[:, ch] = _lp(buf[:, ch], 1800)
    return buf * gain, INDUSTRIAL_SCALE


def crickets(dur, rng, density=0.6):
    """Night crickets: little three-pulse chirps around 4 kHz from a few 'insects', soft and far."""
    n = int(dur * SR)
    buf = np.zeros((n, 2))
    for _ in range(5):
        f = rng.uniform(3600, 4600)
        pan = rng.uniform(-0.8, 0.8)
        gap = rng.uniform(0.7, 1.4) / density
        t = rng.uniform(0, 2)
        tt = t_axis(0.12)
        chirp = np.sin(2 * np.pi * f * tt) * (np.sin(2 * np.pi * 28 * tt) > 0.2) * np.exp(-tt * 10)
        while t < dur - 0.2:
            if rng.uniform() < 0.8:
                place(buf, chirp * rng.uniform(0.004, 0.012), t, pan=pan)
            t += gap * rng.uniform(0.85, 1.15)
    return buf


# ---------- playful monster sounds (Forest Keepers) ----------

def boing(f, dur=0.6):
    """Cartoon spring: a wobbling tone that bends down and settles, soft and round."""
    tt = t_axis(dur)
    wob = 1 + 0.22 * np.sin(2 * np.pi * 16 * tt) * np.exp(-tt * 5)
    glide = 1.0 + 0.35 * np.exp(-tt * 9)
    ph = 2 * np.pi * np.cumsum(f * wob * glide) / SR
    sig = (np.sin(ph) + 0.25 * np.sin(2 * ph)) * np.exp(-tt * 4.5)
    sig[:40] *= np.linspace(0, 1, 40)
    return _lp(sig, 3000) * 0.8


def quack(f, dur=0.2):
    """Biscuit the duckling's quack: a short nasal 'wak' - a buzzy tone that drops in pitch, through an 'a' vowel
    and a nasal hump, with a soft little 'k' at the start. Round and small; nothing above ~2.4 kHz (the owner hears
    1-5 kHz as harsh)."""
    tt = t_axis(dur)
    u = tt / dur
    ph = np.cumsum(f * (1.18 - 0.36 * u ** 0.8) * (1 + 0.03 * np.sin(2 * np.pi * 34 * tt))) / SR
    saw = 2 * (ph % 1.0) - 1
    env = np.clip(tt / 0.008, 0, 1) * np.exp(-np.clip(tt - 0.05, 0, None) * 16)
    vowel = _bp(saw, 650, 1150) * 1.3 + _bp(saw, 1300, 1900) * 0.5 + _bp(saw, 200, 380) * 0.5
    rng = np.random.default_rng(int(f) + 7)
    n = int(0.018 * SR)
    k = np.zeros_like(tt)
    k[:n] = _bp(rng.standard_normal(n), 900, 2000) * np.exp(-np.arange(n) / SR * 260) * 0.25
    return _lp(vowel * env * 1.5 + k, 2400)


DUCK_STYLES = {        # (dur, lift, fall, rasp, nasal formant Hz, bright, semitones) - owner 2026-11-12 (TW0012): Biscuit's quack
    "a": (0.13, 0.12, 0.27, 0.25, 860.0, 0.12, 0),    # "can be cuter and even more duck-like": A cute little 'wak'
    "b": (0.18, 0.08, 0.32, 0.5, 800.0, 0.12, -5),     # B a ducky, raspier quack, a fourth lower
    "c": (0.10, 0.22, 0.22, 0.15, 900.0, 0.05, 0),    # C a soft high 'peep-wak'
}


def duckling(f, style="a"):
    """Biscuit's quack from Day 4 on: a pulse-train voice (reedy, many harmonics) with a duck's raspy flutter (every
    other pulse louder), a quick lift then a fall in pitch, through a nasal formant with a notch below it; soft
    onset, low-passed under ~2 kHz (1-5 kHz 5-17% for a quack-quack-quack, the old `quack` 1.8%)."""
    dur, lift, fall, rasp, nasal, bright, semi = DUCK_STYLES[style]
    f = f * 2 ** (semi / 12)
    tt = t_axis(dur)
    u = tt / dur
    contour = 1 + lift * np.sin(np.pi * np.clip(u / 0.35, 0, 1)) * (u < 0.35) - fall * np.clip((u - 0.3) / 0.7, 0, 1) ** 1.3
    ph = np.cumsum(f * contour) / SR
    src = (np.exp(-(ph % 1.0) / 0.12) - 0.12) * (1 + rasp * np.sign(np.sin(np.pi * ph)))
    env = np.clip(tt / 0.012, 0, 1) ** 1.5 * np.clip((dur - tt) / 0.05, 0, 1) ** 1.2
    v = _bp(src, nasal * 0.8, nasal * 1.25) * 1.4 + _bp(src, 250, 520) * 0.6 + _bp(src, 1600, 2100) * bright
    v = v - 0.5 * _bp(v, 560, 700)
    return _lp(_lp(v * env, 1900), 2200) * 4.2     # (as loud as the old quack, rms)


def cluck(f):
    """A hen's soft 'buk' (Day 5, the hens and their crate): a short throaty pulse-train syllable, its pitch dropping,
    through a round ~650 Hz formant; low-passed under ~1.8 kHz (the owner hears 1-5 kHz as harsh). Three or four in a
    row (0.13-0.16 s apart) make a contented buk-buk-buk."""
    dur = 0.085
    tt = t_axis(dur)
    u = tt / dur
    ph = np.cumsum(f * (1.12 - 0.3 * u)) / SR
    src = np.exp(-(ph % 1.0) / 0.15) - 0.15
    env = np.clip(tt / 0.006, 0, 1) * np.clip((dur - tt) / 0.03, 0, 1) ** 1.3
    v = _bp(src, 500, 820) * 1.5 + _bp(src, 200, 420) * 0.7
    return _lp(_lp(v * env, 1700), 2000) * 4.0


def bloop(f, dur=0.35):
    """Soft bubble 'bloop': a quick upward pitch sweep."""
    tt = t_axis(dur)
    ph = 2 * np.pi * np.cumsum(f * (0.7 + 0.6 * (1 - np.exp(-tt * 18)))) / SR
    sig = np.sin(ph) * np.exp(-tt * 9)
    sig[:30] *= np.linspace(0, 1, 30)
    return _lp(sig, 2500)


VOICE_DUR = {"up": 0.34, "down": 0.34, "hum": 0.34, "cheer": 0.34, "ooh": 0.62, "hehe": 0.5, "brr": 0.55,
             "uhoh": 0.5, "wee": 0.9, "huff": 0.22, "hey": 0.42, "aww": 0.6}


def voice(f, contour="up", dur=None, fs=1.0):
    """Tiny creature voice: a buzzy tone through two vowel formants with a pitch contour.
    up = curious 'oo-ip?', down = content 'mm-ah', hum = two-note 'hm-hm', cheer = 'ya-ay!',
    ooh = wonder (slow rise and fall, round 'oo'), hehe = a three-step giggle, brr = a shiver (lip trill, falling),
    uhoh = two notes down a minor third, wee = a long happy glide up and down, huff = short effort,
    hey = calling to someone (two notes up), aww = soft and fond (falls slowly).
    fs scales the vowel formants: < 1 deeper and rounder (Hans), > 1 brighter (Springs)."""
    dur = VOICE_DUR.get(contour, 0.34) if dur is None else dur
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = tt / dur
    step = lambda a, b: np.clip((u - a) / max(1e-3, b - a), 0, 1)
    shape = {"up": 0.85 + 0.45 * u ** 1.5, "down": 1.25 - 0.4 * u, "hum": 1.0 + 0.12 * (u > 0.5),
             "cheer": 1.0 + 0.5 * np.sin(np.pi * np.clip(u * 1.2, 0, 1)),
             "ooh": 0.92 + 0.3 * np.sin(np.pi * np.clip(u * 1.1, 0, 1)) ** 1.5,
             "hehe": 1.26 - 0.1 * np.floor(u * 3) - 0.04 * (u * 3 % 1),
             "brr": 1.15 - 0.3 * u,
             "uhoh": 1.19 - 0.19 * (u > 0.45),
             "wee": 0.9 + 0.55 * np.sin(np.pi * np.clip(u * 0.85, 0, 1)) - 0.12 * step(0.8, 1.0),
             "huff": 1.05 - 0.15 * u,
             "hey": 1.0 + 0.26 * (u > 0.4) + 0.05 * step(0.4, 1.0),
             "aww": 1.12 - 0.22 * u ** 0.7}[contour]
    vib = 1 + 0.02 * np.sin(2 * np.pi * 7 * tt)
    ph = np.cumsum(f * shape * vib) / SR
    saw = 2 * (ph % 1.0) - 1
    env = np.clip(tt / 0.02, 0, 1) * np.clip((dur - tt) / 0.08, 0, 1)
    if contour == "hum":
        env *= 0.35 + 0.65 * (np.abs(u - 0.25) < 0.22) + 0.65 * (np.abs(u - 0.75) < 0.22)
    elif contour == "hehe":                       # three bouncy syllables
        env *= np.clip(np.sin(np.pi * (u * 3 % 1)) * 1.4, 0, 1)
    elif contour == "uhoh":
        env *= np.clip(np.abs(u - 0.45) / 0.06, 0.15, 1)
    elif contour == "hey":
        env *= np.clip(np.abs(u - 0.4) / 0.05, 0.2, 1)
    elif contour == "brr":                        # lips flapping ~26 times a second
        env *= 0.55 + 0.45 * np.sin(2 * np.pi * 26 * tt)
    elif contour == "huff":
        env *= np.exp(-u * 2.5)
    lo, hi = (380, 760) if contour in ("ooh", "aww") else (450, 900)       # 'oo' is rounder than 'ah'
    vowel = _bp(saw, lo * fs, hi * fs) * 1.2 + _bp(saw, 1100 * fs, 1700 * fs) * (0.35 if contour == "ooh" else 0.6)
    return _lp(vowel, 2400) * env * 1.4


def keepers_bed(dur, rng, forest_from=None, pulse_from=None, pulse_to=None, pulse_bpm=88, gain=1.0,
                forest_spans=None):
    """Forest Keepers: the industrial factory bed (a soft pulse only while they train) crossfading at
    `forest_from` into a calmer night-forest bed (approved ambient pad chords + crickets).
    `forest_spans` [[t0, t1], ...] instead: outdoors in each span, in the factory between them
    (episode 3 goes forest -> factory -> forest); 4 s crossfades centred on each act cut."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    ind, _ = industrial_bed(dur, rng)
    if pulse_from is not None:
        beat = 60.0 / pulse_bpm
        tk = t_axis(0.5)
        thump = np.sin(2 * np.pi * np.cumsum(48 + 40 * np.exp(-tk * 20)) / SR) * np.exp(-tk * 9)
        b = pulse_from
        end = pulse_to if pulse_to is not None else dur
        while b < min(end, dur - 0.5):
            fade = min(1.0, (b - pulse_from) / (8 * beat)) * min(1.0, (end - b) / (4 * beat))
            place(ind, _lp(thump, 1800) * 0.22 * fade, b)
            b += beat
    if forest_spans:
        forest, _ = ambient_bed(dur, rng, gain=0.42)
        forest += crickets(dur, rng)
        x = np.zeros(n)
        for t0, t1 in forest_spans:
            up = np.clip((tt - (t0 - 2.0)) / 4.0, 0, 1) if t0 > 0.5 else np.ones(n)
            down = np.clip(((t1 + 2.0) - tt) / 4.0, 0, 1) if t1 < dur - 0.5 else np.ones(n)
            x = np.maximum(x, np.minimum(up, down))
        x = x[:, None]
        return (ind * (1 - x) + forest * x) * gain, INDUSTRIAL_SCALE
    if forest_from is None or forest_from >= dur:
        return ind * gain, INDUSTRIAL_SCALE
    forest, _ = ambient_bed(dur, rng, gain=0.42)
    forest += crickets(dur, rng)
    x = np.clip((tt - (forest_from - 2.0)) / 4.0, 0, 1)[:, None]
    return (ind * (1 - x) + forest * x) * gain, INDUSTRIAL_SCALE


def keepers_song_bed(dur, rng, chords=(), gain=0.32, crickets_gain=0.7):
    """Forest Keepers engine (owner 2026-10-27: lighthearted, all ages, never the dark Foundry sound): a warm
    pad following the song's chords, chords = [[start_s, len_s, [midi...]], ...], low-passed so it stays
    soft, plus faint night crickets. The tune, the bass and every SFX come from events."""
    buf = np.zeros((int(dur * SR), 2))
    for start, length, notes in chords:
        for j, m in enumerate(notes):
            place(buf, pad_note(midi(m), length + 1.6, a=0.5, r=1.4, rng=rng) * gain / len(notes) * 2,
                  start, pan=(j / max(1, len(notes) - 1) - 0.5) * 0.6)
    buf = sosfilt(butter(2, 1800, "low", fs=SR, output="sos"), buf, axis=0)
    if crickets_gain > 0:
        buf += crickets(dur, rng, density=0.5) * crickets_gain
    return buf, None


# ---------- Sandglass: soft, close-mic'd ASMR textures (docs/engines/sandglass.md) ----------
# The continuous textures are queued as short overlapping chunks (EventTrack.fx every ~2/3 of a
# chunk), each with a sine-in / cosine-out envelope so neighbours sum to constant power and the
# chunk velocities can follow what is on screen (stream flow, landing rate).

SAND_CHORDS = [[41, 57, 60, 64, 67], [45, 57, 60, 64, 69], [38, 57, 60, 62, 65], [46, 58, 62, 65, 69]]
SAND_SCALE = [60, 62, 64, 67, 69, 72, 74, 76]      # lower than MUSIC_BOX_SCALE; stays inside MIDI 36-96


def _tile_env(n, fade):
    env = np.ones(n)
    f = min(int(fade * SR), n // 2)
    ph = np.linspace(0, np.pi / 2, f)
    env[:f] = np.sin(ph)
    env[n - f:] = np.cos(ph)
    return env


def _colored(n, rng, slope):
    """Noise with a 1/f**slope power spectrum (slope 1 = pink, 2 = brown): warmer than white noise."""
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[1:] /= f[1:] ** (slope / 2)
    spec[0] = 0
    x = np.fft.irfft(spec, n)
    return x / (x.std() + 1e-12)


def _soft_grains(n, rate, rng, length=0.004, fc=2500):
    """Grains as tiny smooth noise puffs (Hann-windowed, a few ms) rather than single-sample clicks:
    the texture stays sandy without spiky, crackly transients. Amplitudes are gentle (uniform)."""
    imp = (rng.random(n) < rate / SR) * rng.uniform(0.3, 1.0, n)
    k = max(8, int(length * SR))
    burst = np.convolve(imp, np.hanning(k), mode="same") * _colored(n, rng, 1.0)
    return _bp(burst, 200, fc, order=2)


def sand_pour(dur, rng=None):
    """Sand slipping through the funnel: a soft, smooth, airy hiss sitting above the midrange
    (~4-8 kHz). Pure smooth noise - no grain layer, so nothing crackles (owner on SG0003: the pour
    was too mid-toned and crackly). SG0005 (owner: still a bit harsh): pinkish instead of white
    noise, a steeper low side so less of the ear-sensitive 2.5-5 kHz band, a rounder top with no
    sizzle above 10 kHz, and ~3.5 dB quieter."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    x = sosfilt(butter(3, 4200, "high", fs=SR, output="sos"), _colored(n, rng, 0.8))
    hiss = _lp(x, 7500, order=3)
    hiss *= 0.9 + 0.1 * _smooth_noise(n, 3, rng)          # slow breath, no flutter
    return hiss * 0.52 * _tile_env(n, dur / 3)


def sand_patter(dur, rng=None):
    """Grains settling on the pile: a soft, low sifting whisper. Tens of thousands of tiny contacts
    per second merge into one smooth texture - no individual drops (owner on SG0002: the landing
    sounded hard, heavy and tinny, like rain rather than sand)."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    # SG0005 (owner: still a bit harsh): softer, longer puffs, lower cut-offs, more of the warm
    # hush than the sift, ~2.5 dB quieter
    sift = _soft_grains(n, 30000, rng, length=0.004, fc=700)
    warm = _lp(_bp(_colored(n, rng, 1.5), 100, 600), 550, order=2)
    mod = 0.85 + 0.15 * _smooth_noise(n, 5, rng)          # slow, gentle swell, not flutter
    return (sift * 0.3 + warm * 0.7) * mod * 0.045 * _tile_env(n, dur / 3)


def sand_slice(dur, rng=None):
    """A blade gliding down through kinetic sand: a soft, dense, slightly crunchy whisper - thousands
    of tiny smooth grain puffs over a warm hush, all kept under ~2 kHz (owner: nothing harsh)."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    grains = _soft_grains(n, 6000, rng, length=0.003, fc=1600)
    hush = _lp(_bp(_colored(n, rng, 1.2), 150, 1200), 1000, order=2)
    mod = 0.8 + 0.2 * _smooth_noise(n, 6, rng)
    env = np.minimum(1, np.minimum(np.arange(n) / (0.06 * SR), (n - np.arange(n)) / (0.12 * SR)))
    return (grains / (grains.std() + 1e-12) * 0.45 + hush * 0.55) * mod * env * 0.17


def sand_thump(dur=0.5, rng=None):
    """A soft clump of kinetic sand landing: a round, padded thud with a short crumbly whisper
    after it. No click, nothing ringing (rounded 5 ms attack, everything under ~1 kHz); pitched high
    enough (~95 Hz + its octave) that phone speakers still play it."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(95 * (1 + 0.4 * np.exp(-tt * 40))) / SR
    body = (np.sin(ph) + 0.35 * np.sin(2 * ph)) * np.exp(-tt * 18)
    thud = _lp(rng.standard_normal(n), 600, order=2)
    thud *= np.exp(-tt * 28) / (np.abs(thud[:int(0.03 * SR)]).max() + 1e-9)
    tail = _soft_grains(n, 9000, rng, length=0.004, fc=900)
    tail *= np.exp(-tt * 10) / (tail.std() + 1e-12) * 0.12
    sig = body * 0.8 + thud * 0.45 + tail
    a = int(0.005 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    return _lp(sig, 1100) * 0.6


def sand_scrape(dur, rng=None):
    """A bench scraper pushing kinetic sand along the table: a smooth, low shush with a soft grainy
    edge, swelling gently (warm: mostly 150 Hz - 1.5 kHz)."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    shush = _lp(_bp(_colored(n, rng, 1.0), 180, 1400), 1200, order=2)
    grains = _soft_grains(n, 3000, rng, length=0.004, fc=1200)
    mod = 0.8 + 0.2 * _smooth_noise(n, 3, rng)
    return (shush * 0.7 + grains / (grains.std() + 1e-12) * 0.3) * mod * 0.16 * _tile_env(n, min(0.2, dur / 3))


def paint_pour(dur, rng=None):
    """Thick acrylic paint pouring from a cup into a puddle: a soft, low, glossy ribbon of sound with
    the odd round 'blub' as the stream folds onto itself. Warm: almost everything under ~900 Hz, no
    clicks (rounded blub attacks)."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    tt = np.arange(n) / SR
    ribbon = _lp(_bp(_colored(n, rng, 1.3), 150, 900), 850, order=2)
    ribbon /= ribbon.std() + 1e-12
    ribbon *= 0.8 + 0.2 * _smooth_noise(n, 4, rng)
    blubs = np.zeros(n)
    t0 = rng.uniform(0.1, 0.5)
    while t0 < dur - 0.2:
        m = int(rng.uniform(0.07, 0.13) * SR)
        i = int(t0 * SR)
        u = np.arange(min(m, n - i)) / SR
        f0 = rng.uniform(190, 300)       # high enough for phone speakers
        ph = 2 * np.pi * np.cumsum(f0 * (1 - 0.35 * u / (m / SR))) / SR
        env = np.sin(np.pi * u / (m / SR)) ** 2
        blubs[i:i + len(u)] += np.sin(ph) * env * rng.uniform(0.5, 1.0)
        t0 += rng.uniform(0.3, 0.8)
    sig = _lp(ribbon * 0.75 + blubs * 0.5, 1000)
    return sig / (sig.std() + 1e-12) * 0.063 * _tile_env(n, min(0.4, dur / 3))


def paint_spread(dur, rng=None):
    """Paint sliding across a tilted canvas: a slow, smooth, very soft silky whoosh (no hiss - kept
    low and warm, 120-800 Hz), swelling in and out."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    x = _lp(_bp(_colored(n, rng, 1.3), 150, 800), 700, order=2)
    x *= 0.85 + 0.15 * _smooth_noise(n, 2, rng)
    return x / (x.std() + 1e-12) * 0.04 * _tile_env(n, dur / 2.5)


def paint_wipe(dur, rng=None):
    """A silicone squeegee pulling wet paint across a canvas: a smooth, low, slightly wet shush with
    a gentle squelchy wobble (warm: mostly 150 Hz - 1.3 kHz)."""
    rng = rng if rng is not None else _RNG
    n = int(dur * SR)
    tt = np.arange(n) / SR
    shush = _lp(_bp(_colored(n, rng, 1.1), 150, 1300), 1100, order=2)
    wet = _bp(_colored(n, rng, 1.0), 200, 500) * (0.6 + 0.4 * np.sin(2 * np.pi * 6.5 * tt + rng.uniform(0, 6)))
    mod = 0.85 + 0.15 * _smooth_noise(n, 3, rng)
    sig = (shush * 0.75 + wet * 0.35) * mod
    return sig / (sig.std() + 1e-12) * 0.063 * _tile_env(n, min(0.3, dur / 3))


def warm_bell(f, dur=4.0):
    """Soft, round bell (felt music box / celesta): mostly fundamental plus a gentle octave, with a
    12 ms rounded attack - none of bell()'s metallic FM sidebands or click."""
    tt = t_axis(dur)
    sig = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 1.3)
           + 0.22 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 3.0)
           + 0.06 * np.sin(6 * np.pi * f * tt) * np.exp(-tt * 6.0))
    a = int(0.012 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    return sig


def deep_bell(f, dur=11.0):
    """Deep Sky bell: a slow, round singing-bowl tone - long fundamental, a soft octave and a faint
    inharmonic bowl partial, 30 ms rounded attack. Nothing above ~3x the fundamental."""
    tt = t_axis(dur)
    sig = (np.sin(2 * np.pi * f * tt) * np.exp(-tt / 4.5)
           + 0.16 * np.sin(4 * np.pi * f * tt) * np.exp(-tt / 1.8)
           + 0.035 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt / 1.4)
           + 0.03 * np.sin(6 * np.pi * f * tt) * np.exp(-tt / 0.8))
    a = int(0.03 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    r = int(0.6 * SR)
    sig[-r:] *= np.linspace(1, 0, r) ** 2
    return sig


def sky_glow(f, dur=4.5, attack=0.09, decay=1.3):
    """Deep Sky Short: one planet joining the line-up. Soft, not struck - a 90 ms raised-sine onset (no click,
    no mallet) and a slow exponential fade, the sky_swell timbre (two copies a hair apart, soft octave, trace
    of the fifth above it), so nothing above 3x the fundamental."""
    tt = t_axis(dur)
    sig = np.zeros(len(tt))
    for df, g in ((-0.11, 0.5), (0.13, 0.5)):
        ph = 2 * np.pi * (f + df) * tt
        sig += g * (np.sin(ph) + 0.25 * np.sin(2 * ph + 0.4) + 0.04 * np.sin(3 * ph + 1.1))
    env = np.exp(-tt / decay)
    a = int(attack * SR)
    env[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    env[-int(0.3 * SR):] *= np.linspace(1, 0, int(0.3 * SR))
    return sig * env


def sky_swell(f, dur=10.0, rise=4.0, fall=5.0):
    """Deep Sky line-up tone (SK0002 on; owner: SK0001's struck bells were 'what I would want to wake up
    to'): no attack at all - a warm tone that breathes in over `rise` seconds and fades over `fall`, two
    copies a hair apart for a slow shimmer, a soft octave and a trace of the fifth above it. Nothing above
    3x the fundamental."""
    tt = t_axis(dur)
    sig = np.zeros(len(tt))
    for df, g in ((-0.11, 0.5), (0.13, 0.5)):
        ph = 2 * np.pi * (f + df) * tt
        sig += g * (np.sin(ph) + 0.22 * np.sin(2 * ph + 0.4) + 0.05 * np.sin(3 * ph + 1.1))
    hold = max(0.0, dur - rise - fall)
    env = np.ones(len(tt))
    a, h = int(rise * SR), int((rise + hold) * SR)
    env[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    env[h:] = np.cos(np.linspace(0, np.pi / 2, len(tt) - h)) ** 2
    return sig * env


def space_drone(dur, rng, chords, partials=6, max_hz=1000.0, detune_hz=0.12, swells=(1, 2, 3, 4, 5),
                xfade=0.4, voice_gains=(1.0, 0.62, 0.42, 0.3), wind=0.05, wind_band=(70.0, 420.0),
                chunk=1 << 19):
    """Deep Sky bed: a deep, slowly evolving drone that repeats *exactly* every `dur` seconds, so a loop
    can be played back to back with no seam.

    `chords` (lists of MIDI notes, low to high, 36-66) share the loop equally, each crossfading into the
    next over `xfade` of its span. Every frequency is a whole number of cycles per loop (rounding moves a
    note by at most 1/(2*dur) Hz - inaudible), each partial swells on its own LFO that also repeats a whole
    number of times per loop, and the left and right copies of each voice are detuned by `detune_hz`
    (also whole cycles), so the drone breathes slowly across the stereo field. Partials stop below
    `max_hz` (warm: owner hears 1-5 kHz as harsh). A breath of band-limited "space wind" on top, made
    periodic with an equal-power crossfade of its own tail onto its head. Returns float32 (n, 2)."""
    n_tot = int(round(dur * SR))
    out = np.zeros((n_tot, 2), np.float32)
    n_ch = len(chords)
    seg = n_tot / n_ch
    X = xfade * seg
    phases, lfo = {}, {}
    d = max(1, int(round(detune_hz * dur)))
    for s0 in range(0, n_tot, chunk):
        n = np.arange(s0, min(n_tot, s0 + chunk), dtype=np.int64)
        u = n / n_tot
        for c, chord in enumerate(chords):
            # raised-cosine window: 1 inside the chord's span, cosine ramps of width X across its edges;
            # neighbouring windows sum to exactly 1 (wraps round the loop)
            pos = (n - c * seg) % n_tot                        # samples since this chord's start
            w = np.zeros(len(n))
            core = (pos >= X / 2) & (pos <= seg - X / 2)
            w[core] = 1.0
            rise = pos < X / 2
            w[rise] = 0.5 + 0.5 * np.sin(np.pi * pos[rise] / X)
            fall = (pos > seg - X / 2) & (pos < seg + X / 2)
            w[fall] = 0.5 - 0.5 * np.sin(np.pi * (pos[fall] - seg) / X)
            rise2 = pos > n_tot - X / 2                         # the ramp in before the start, wrapped
            w[rise2] = 0.5 + 0.5 * np.sin(np.pi * (pos[rise2] - n_tot) / X)
            if not w.any():
                continue
            for v, note in enumerate(chord):
                f = midi(note)
                m = int(round(f * dur))
                if note not in phases:                         # same note, same phase in every chord
                    phases[note] = rng.uniform(0, 2 * np.pi, partials)
                g = voice_gains[min(v, len(voice_gains) - 1)]
                pan = 0.0 if v == 0 else (0.45 if v % 2 else -0.45) * min(1.0, 0.6 + 0.2 * v)
                for h in range(1, partials + 1):
                    if h * f > max_hz:
                        break
                    key = (note, h)
                    if key not in lfo:
                        lfo[key] = (int(rng.choice(swells)), rng.uniform(0, 2 * np.pi), rng.uniform(0.25, 0.5))
                    q, ps, depth = lfo[key]
                    amp = g * h ** -1.7 * (1 - 0.6 * (h * f / max_hz) ** 2)
                    sw = (1 - depth) + depth * np.sin(2 * np.pi * q * u + ps)
                    env = (w * sw * amp).astype(np.float32)
                    for ch, mm in ((0, h * (m - d)), (1, h * (m + d))):
                        ph = 2 * np.pi * ((mm * n) % n_tot) / n_tot + phases[note][h - 1]
                        k = np.cos((pan + 1) * np.pi / 4) if ch == 0 else np.sin((pan + 1) * np.pi / 4)
                        out[s0:s0 + len(n), ch] += env * np.sin(ph).astype(np.float32) * np.float32(k * 1.41)
    if wind > 0:
        F = int(min(20 * SR, n_tot // 4))
        sos = butter(2, wind_band, "bandpass", fs=SR, output="sos")
        for ch in range(2):
            x = sosfilt(sos, rng.standard_normal(n_tot + F)).astype(np.float32)
            x /= np.std(x) + 1e-9
            fade = np.linspace(0, np.pi / 2, F, dtype=np.float32)
            head = x[:F] * np.sin(fade) + x[n_tot:n_tot + F] * np.cos(fade)   # continues from x[n_tot - 1]
            x = x[:n_tot]
            x[:F] = head
            # two slow gust LFOs, whole cycles per loop
            uu = np.arange(n_tot, dtype=np.float32) / n_tot
            gust = 0.55 + 0.3 * np.sin(2 * np.pi * 3 * uu + 1.3 + ch) + 0.15 * np.sin(2 * np.pi * 7 * uu + 0.4)
            out[:, ch] += x * gust.astype(np.float32) * np.float32(wind * 0.3)
    return out


def sand_bed(dur, rng, bar=7.2, gain=0.22, bells=0.13):
    """Sandglass bed: a very soft, slow felt music box (lower and slower than music_box_bed) over a
    warm low pad. Three notes per bar; layer-change events use SAND_SCALE so they sit inside it."""
    buf = np.zeros((int(dur * SR), 2))
    k = 0
    while k * bar < dur:
        root, *tones = SAND_CHORDS[k % 4]
        place(buf, pad_note(midi(root), bar + 2.5, a=2.0, r=2.5, rng=rng) * gain, k * bar)
        place(buf, pad_note(midi(tones[0]), bar + 2.5, a=2.5, r=2.5, rng=rng) * gain * 0.3, k * bar, pan=-0.25)
        for off, j in ((0.4, 1), (2.8, 3), (5.0, 2)):
            place(buf, warm_bell(midi(tones[j]), dur=4.5) * bells * rng.uniform(0.75, 1.0),
                  k * bar + off + rng.uniform(0, 0.15), pan=rng.uniform(-0.4, 0.4))
        k += 1
    return buf, SAND_SCALE


# ---------- pieces ----------

def ambient_pad():
    dur = 44
    buf = np.zeros((int(dur * SR), 2))
    # Cmaj9 - Am9 - Fmaj7#11 - Gsus/E, slow and open-voiced
    chords = [[48, 55, 59, 62, 64], [45, 52, 55, 59, 60], [41, 48, 52, 55, 59], [40, 47, 50, 55, 57]]
    step = 9.0
    for k in range(5):
        ch = chords[k % 4]
        for i, m in enumerate(ch):
            place(buf, pad_note(midi(m), step + 3.5) * 0.5, k * step, pan=(i / 4 - 0.5) * 0.8)
    # sparse bells on a pentatonic
    scale = [72, 74, 76, 79, 81, 84]
    t = 3.0
    while t < dur - 5:
        place(buf, bell(midi(rng.choice(scale)), index=1.5) * 0.12, t, pan=rng.uniform(-0.7, 0.7))
        t += rng.uniform(1.8, 4.5)
    master(reverb(buf, decay=5.5, wet=0.5, tone=4000), "1_ambient_pad")


def marble_race():
    dur = 40
    bpm = 104
    beat = 60 / bpm
    buf = np.zeros((int(dur * SR), 2))
    # soft beat
    b = 2 * beat
    while b < dur - 5:
        place(buf, kick() * 0.55, b)
        place(buf, hat() * 0.12, b + beat / 2, pan=0.3)
        b += beat
    # bass + pad underneath
    roots = [45, 41, 48, 43]
    for k in range(int(dur / (8 * beat)) + 1):
        root = roots[k % 4]
        for m in (root, root + 12 + 7, root + 12 + 16 if root != 45 else root + 24):
            place(buf, pad_note(midi(m), 8 * beat + 1, a=0.4, r=1.0) * 0.18, k * 8 * beat)
    # collisions: density builds as the race heats up
    scale = [69, 72, 74, 76, 79, 81, 84, 86, 88]
    t = 1.0
    while t < dur - 6:
        progress = t / dur
        place(buf, plink(midi(rng.choice(scale))) * rng.uniform(0.15, 0.3), t, pan=rng.uniform(-0.9, 0.9))
        t += rng.exponential(0.35 - 0.22 * progress)
    # winner chime
    win = dur - 5.5
    for i, m in enumerate([72, 76, 79, 84, 88, 91]):
        place(buf, bell(midi(m), index=2.0, ratio=2.0) * 0.25, win + i * 0.09, pan=(i / 5 - 0.5))
    master(reverb(buf, decay=2.0, wet=0.25), "2_marble_race")


def music_box():
    dur = 42
    buf = np.zeros((int(dur * SR), 2))
    chords = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 66]]
    note_len = 0.28
    t = 0.5
    bar = 0
    while t < dur - 5:
        ch = chords[bar % 4]
        place(buf, pad_note(midi(ch[0] - 12), 16 * note_len + 2, a=1.0, r=1.5) * 0.25, t)
        pattern = [0, 1, 2, 3, 2, 1, 2, 3] if bar % 2 == 0 else [0, 2, 1, 3, 2, 3, 1, 2]
        for rep in range(2):
            for i, idx in enumerate(pattern):
                m = ch[idx] + 24 if (i + rep) % 5 else ch[idx] + 12
                place(buf, bell(midi(m), dur=2.5, index=1.2, ratio=4.0) * 0.18,
                      t + (rep * 8 + i) * note_len, pan=np.sin((rep * 8 + i) * 0.7) * 0.6)
        t += 16 * note_len
        bar += 1
    master(reverb(buf, decay=3.5, wet=0.45, tone=5000), "3_music_box")


# ---------- Chain Reaction (docs/engines/chain_reaction.md section 5) ----------
# Warm by design (owner: 1-5 kHz / clicky / saturated reads as harsh): fundamental-heavy tones,
# rounded attacks, padded knocks, everything low-passed well under 4 kHz.

def wood_clack(f, dur=0.9):
    """Domino clack tuned to a note: a soft wooden bar (felt-mallet marimba) plus a short padded knock.
    Higher notes ring shorter, like real bars; the bright 3.9x partial is quiet and gone in ~25 ms."""
    tt = t_axis(dur)
    rng = np.random.default_rng(int(f * 10) + 11)
    dec = 5.0 * (f / 440.0) ** 0.5
    tone = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * dec)
            + 0.16 * np.sin(2 * np.pi * 2.0 * f * tt + 0.6) * np.exp(-tt * dec * 2.6)
            + 0.05 * np.sin(2 * np.pi * 3.93 * f * tt) * np.exp(-tt * 40))
    n = int(0.04 * SR)
    knock = np.zeros_like(tt)
    k = _bp(rng.standard_normal(n), 220, 1300) * np.exp(-np.arange(n) / SR * 170)
    knock[:n] = k / (np.max(np.abs(k)) + 1e-9) * 0.35
    body = 0.2 * np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 55)         # the little wooden block itself
    sig = tone + knock + body
    a = int(0.0025 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    return _lp(sig, 3000)


def wood_thud(f=73.0, dur=1.4):
    """Last domino landing flat on the tabletop: a deep, round wooden thud (low sweep + soft knock +
    a hollow table resonance). No ring, no click."""
    tt = t_axis(dur)
    rng = np.random.default_rng(int(f * 10) + 12)
    body = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.5 * np.exp(-tt * 28))) / SR) * np.exp(-tt * 6.5)
    knock = _lp(rng.standard_normal(len(tt)), 520) * np.exp(-tt * 32)
    knock *= 0.9 / (np.max(np.abs(knock[:int(0.05 * SR)])) + 1e-9)
    hollow = 0.22 * np.sin(2 * np.pi * f * 3.1 * tt) * np.exp(-tt * 11)
    sig = body + knock + hollow
    a = int(0.003 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    return _lp(sig, 1600)


def gear_tick(f, dur=0.5):
    """Soft brass ratchet tick tuned to a note: a padded knock and a short, quiet ring - more felt
    than click (everything under 2.5 kHz)."""
    tt = t_axis(dur)
    rng = np.random.default_rng(int(f * 10) + 13)
    n = int(0.02 * SR)
    knock = np.zeros_like(tt)
    k = _bp(rng.standard_normal(n), 300, 1500) * np.exp(-np.arange(n) / SR * 260)
    knock[:n] = k / (np.max(np.abs(k)) + 1e-9) * 0.5
    ring = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 16)
            + 0.25 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt * 45)) * 0.55
    sig = knock + ring
    a = int(0.002 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    return _lp(sig, 2500)


def brass_bell(f, dur=3.0):
    """Little brass desk bell, rung by a marble: near-harmonic partials (sweet, not a church bell's
    minor third), a soft 5 ms strike, low-passed so the top partials stay round."""
    tt = t_axis(dur)
    sig = np.zeros_like(tt)
    for ratio, amp, dec in ((1.0, 1.0, 1.4), (2.0, 0.3, 2.6), (3.0, 0.1, 4.5), (4.07, 0.05, 7.0), (0.5, 0.12, 1.8)):
        sig += amp * np.sin(2 * np.pi * f * ratio * tt) * np.exp(-tt * dec)
    a = int(0.005 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    return _lp(sig, 3200)


def marble_roll(dur, rng=None):
    """A marble rolling along a wooden rail: a low, soft rumble with a gentle ripple, no hiss."""
    rng = rng if rng is not None else _RNG
    n = int((dur + 0.08) * SR)
    tt = np.arange(n) / SR
    body = _bp(rng.standard_normal(n), 70, 420, order=2)
    body /= np.std(body) + 1e-9
    wood = _bp(rng.standard_normal(n), 500, 1100) * 0.18
    ripple = 0.75 + 0.25 * np.sin(2 * np.pi * (5.5 + 1.5 * _smooth_noise(n, 2, rng)) * tt)
    env = np.clip(tt / 0.03, 0, 1) * np.clip((dur + 0.08 - tt) / 0.08, 0, 1)
    return _lp(body * ripple + wood * 0.5, 1400) * env * 0.35


def lamp_click(dur=0.3, rng=None):
    """Desk lamp push switch: press and latch, two padded knocks 35 ms apart with a little body."""
    rng = rng if rng is not None else _RNG
    n = int(max(dur, 0.25) * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for t0, amp in ((0.0, 0.8), (0.035, 0.55)):
        i = int(t0 * SR)
        m = int(0.03 * SR)
        k = _bp(rng.standard_normal(m), 250, 1800) * np.exp(-np.arange(m) / SR * 220)
        out[i:i + m] += k / (np.max(np.abs(k)) + 1e-9) * amp
    out += 0.35 * np.sin(2 * np.pi * 185 * tt) * np.exp(-tt * 40)
    a = int(0.002 * SR)
    out[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    return _lp(out, 2200)


def table_bed(dur, rng, chords=(), gain=0.3, tone=2200):
    """Chain Reaction bed: a soft pad that follows the run's harmony, chords = [[start_s, len_s, [midi...],
    level], ...]. `level` lets it swell with the tension and drop out for the hush before the payoff."""
    buf = np.zeros((int(dur * SR), 2))
    for start, length, notes, level in chords:
        for j, m in enumerate(notes):
            sig = pad_note(midi(m), length + 1.1, a=min(0.35, 0.3 * length), r=1.0, rng=rng)
            place(buf, sig * gain * level / len(notes) * 2, start, pan=(j / max(1, len(notes) - 1) - 0.5) * 0.5)
    return sosfilt(butter(2, tone, "low", fs=SR, output="sos"), buf, axis=0), None


# ---------- Tiny World (docs/engines/tiny_world.md section 5) ----------
# Cozy lo-fi without the clicky parts (owner hears 1-5 kHz clicks as harsh): mellow electric-piano chords with a
# slow tape wobble, a round bass, a few music-box notes, the sea washing softly. No hats, no crackle.

def epiano(f, dur=2.4, start=0.0, wobble=0.0028):
    """Warm, mellow electric piano (FM tine without the bright bell partial), with a slow tape wobble that
    depends on `start` so every chord drifts together."""
    tt = t_axis(dur)
    drift = 1 + wobble * np.sin(2 * np.pi * 0.47 * (tt + start)) + 0.4 * wobble * np.sin(2 * np.pi * 1.9 * (tt + start))
    ph = 2 * np.pi * np.cumsum(f * drift) / SR
    index = 0.15 + 1.1 * np.exp(-tt * 3.0)
    sig = np.sin(ph + index * np.sin(ph)) * np.exp(-tt * 1.15) + 0.12 * np.sin(2 * ph) * np.exp(-tt * 2.5)
    a = int(0.006 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    r = int(0.25 * SR)
    sig[-r:] *= np.linspace(1, 0, r) ** 2
    return _lp(sig, 2200)


def soft_bass(f, dur=1.2):
    tt = t_axis(dur)
    sig = (np.sin(2 * np.pi * f * tt) + 0.22 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 2.2)
    a = int(0.012 * SR)
    sig[:a] *= np.linspace(0, 1, a)
    r = int(0.15 * SR)
    sig[-r:] *= np.linspace(1, 0, r)
    return _lp(sig, 520)


def sea_wash(dur, rng, period=7.5):
    """Gentle waves on the shore: low band-passed noise that swells and recedes."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    noise = _bp(rng.standard_normal(n), 120, 900)
    swell = (0.35 + 0.65 * np.sin(np.pi * tt / period) ** 4) * (0.8 + 0.2 * _smooth_noise(n, 0.3, rng))
    return _lp(noise * swell, 700)


def hammer_tok(f, dur=0.6):
    """A tiny hammer tapping a wooden piece, tuned to a note: soft wooden knock + a short woody tone.
    Everything round, under ~2.8 kHz."""
    tt = t_axis(dur)
    rng = np.random.default_rng(int(f * 10) + 21)
    dec = 7.0 * (f / 440.0) ** 0.4
    tone = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * dec)
            + 0.12 * np.sin(2 * np.pi * 2.0 * f * tt) * np.exp(-tt * dec * 2.2))
    n = int(0.03 * SR)
    knock = np.zeros_like(tt)
    k = _bp(rng.standard_normal(n), 250, 1600) * np.exp(-np.arange(n) / SR * 200)
    knock[:n] = k / (np.max(np.abs(k)) + 1e-9) * 0.45
    body = 0.25 * np.sin(2 * np.pi * 240 * tt) * np.exp(-tt * 60)
    sig = tone + knock + body
    a = int(0.002 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    return _lp(sig, 2800)


def cozy_bed(dur, rng, bar=3.1, chords=(), final_at=None, final_chord=(), melody=(), gain=0.3, sea=0.05,
             swing=2 / 3):
    """Tiny World bed. chords: one list of MIDI notes per bar (root first), repeated; from `final_at` (seconds)
    the final chord rings out with its bass to the end. melody: [(time_s, midi)] music-box notes on top."""
    buf = np.zeros((int(dur * SR), 2))
    beat = bar / 4
    k = 0
    while k * bar < (final_at if final_at is not None else dur) - 1e-6:
        t0 = k * bar
        notes = chords[k % len(chords)]
        root, voicing = notes[0], notes[1:]
        stop = final_at if final_at is not None else dur
        for off, length, vel in ((0.0, 1.7, 1.0), (1 + swing, 1.0, 0.55), (2.0, 1.5, 0.8), (3 + swing, 0.8, 0.45)):
            ts = t0 + off * beat
            if ts >= stop - 0.05:
                continue
            ln = min(length * beat + 0.6, stop - ts + 0.4)
            for j, m in enumerate(voicing):
                place(buf, epiano(midi(m), ln, ts) * gain * vel * 0.32, ts + 0.008 * j, pan=(j / 3 - 0.5) * 0.4)
        for off, step in ((0.0, 0), (2 + swing, 7)):
            ts = t0 + off * beat
            if ts < stop - 0.05:
                place(buf, soft_bass(midi(root + step), min(1.3 * beat + 0.3, stop - ts + 0.2)) * gain * 0.9, ts)
        k += 1
    if final_at is not None and final_chord:
        ln = dur - final_at + 0.5
        for j, m in enumerate(final_chord[1:]):
            place(buf, epiano(midi(m), ln, final_at, wobble=0.0018) * gain * 0.42, final_at + 0.03 * j,
                  pan=(j / 3 - 0.5) * 0.4)
        place(buf, soft_bass(midi(final_chord[0]), ln) * gain, final_at)
    for ts, m in melody:
        place(buf, warm_bell(midi(m), dur=3.0) * gain * 0.35, ts, pan=rng.uniform(-0.3, 0.3))
    if sea:
        w = sea_wash(dur, rng)
        buf[:, 0] += w * sea
        buf[:, 1] += np.roll(w, int(0.37 * SR)) * sea
    return buf, None



# Upbeat Tiny World bed (owner 2026-10-30 after TW0001: happy and positive like a cheerful game soundtrack, a bit
# more upbeat and more interesting than the lo-fi bed, and it may change through longer videos). Bouncy plucked
# bass, a rolling 16th-note arpeggio, offbeat piano stabs, a soft kick with a wooden backbeat (still no hats, no
# clap, nothing bright), and a catchy lead. Original tune, built in 4-bar phrases whose sections change.

# IV - iii - vi - V7 in F major, one chord per bar: (bass root, voicing...). Bass roots stay at MIDI 36+.
SUNNY_PROG = [[46, 62, 65, 69, 72], [45, 60, 64, 67, 72], [38, 62, 65, 69, 72], [36, 60, 64, 67, 70]]
# lead phrases, one bar per chord above: (16th step, midi, length in 16ths)
SUNNY_MELODY = {
    "a": [[(0, 77, 2), (2, 74, 1), (3, 77, 2), (6, 81, 2), (10, 79, 1), (11, 77, 1), (12, 74, 4)],
          [(0, 76, 2), (3, 72, 1), (4, 76, 2), (6, 79, 2), (10, 77, 1), (11, 76, 1), (12, 72, 4)],
          [(0, 74, 2), (2, 77, 1), (3, 81, 2), (6, 84, 3), (10, 81, 1), (11, 79, 1), (12, 77, 2), (14, 74, 2)],
          [(0, 76, 3), (4, 79, 2), (6, 76, 1), (7, 74, 1), (8, 72, 4), (14, 74, 1), (15, 76, 1)]],
    "b": [[(0, 81, 2), (2, 79, 1), (3, 77, 2), (6, 74, 2), (8, 77, 2), (10, 81, 2), (12, 84, 3)],
          [(0, 84, 2), (2, 81, 1), (3, 79, 2), (6, 76, 2), (8, 79, 1), (9, 81, 1), (10, 79, 2), (12, 76, 4)],
          [(0, 77, 2), (2, 81, 2), (4, 84, 2), (6, 86, 2), (8, 84, 1), (9, 81, 1), (10, 77, 2), (12, 74, 4)],
          [(0, 76, 2), (2, 79, 2), (4, 82, 2), (6, 79, 1), (7, 76, 1), (8, 72, 3), (12, 74, 1), (13, 76, 1),
           (14, 77, 2)]],
    "slow": [[(0, 77, 8), (8, 74, 8)], [(0, 76, 8), (8, 72, 8)], [(0, 74, 6), (6, 77, 2), (8, 81, 8)],
             [(0, 79, 8), (8, 76, 4), (12, 74, 4)]],
}
# what plays in each section (levels; lead = which phrase)
SUNNY_SECTIONS = {
    "groove": dict(arp=1.0, bass=1.0, kick=1.0, tock=1.0, stabs=1.0, lead=None, bells=0.0, pad=0.0),
    "melody": dict(arp=0.85, bass=1.0, kick=1.0, tock=1.0, stabs=0.9, lead="a", bells=0.0, pad=0.0),
    "answer": dict(arp=0.85, bass=1.0, kick=1.0, tock=1.0, stabs=0.9, lead="b", bells=1.0, pad=0.0),
    "break": dict(arp=0.45, bass=0.6, kick=0.0, tock=0.0, stabs=0.0, lead="slow", bells=0.0, pad=1.0),
    "lift": dict(arp=1.0, bass=1.0, kick=1.1, tock=1.1, stabs=1.0, lead="a", bells=1.0, pad=0.4),
}
SUNNY_FORM = ["melody", "answer", "groove", "break", "melody", "lift"]   # repeats for long videos
ARP_STEPS = [0, 1, 2, 3, 2, 1, 2, 3, 0, 1, 2, 3, 4, 3, 2, 1]


def pluck(f, dur=0.32):
    """Soft rounded pluck for the arpeggio: the brightness fades fast, nothing above ~2.4 kHz."""
    tt = t_axis(dur)
    sig = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 18)
           + 0.12 * np.sin(6 * np.pi * f * tt) * np.exp(-tt * 30)) * np.exp(-tt * 9)
    a = int(0.003 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    r = int(0.04 * SR)
    sig[-r:] *= np.linspace(1, 0, r)
    return _lp(sig, 2400)


def bouncy_bass(f, dur=0.3):
    """Short round bass note with a little pluck, so the line bounces; the upper harmonics carry it on phones."""
    tt = t_axis(dur)
    sig = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 10)
           + 0.18 * np.sin(6 * np.pi * f * tt) * np.exp(-tt * 22)) * np.exp(-tt * 4.5)
    a = int(0.006 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    r = int(0.05 * SR)
    sig[-r:] *= np.linspace(1, 0, r)
    return _lp(sig, 900)


def soft_lead(f, dur):
    """Friendly game-like lead: a rounded pulse (odd harmonics, gently filtered) with a late, light vibrato."""
    tt = t_axis(dur)
    vib = 1 + 0.004 * np.clip((tt - 0.12) / 0.2, 0, 1) * np.sin(2 * np.pi * 5.2 * tt)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    sig = np.sin(ph) + 0.15 * np.sin(2 * ph) + 0.26 * np.sin(3 * ph) + 0.08 * np.sin(5 * ph)
    env = 0.6 + 0.4 * np.exp(-tt * 6.0)
    a = int(0.015 * SR)
    env[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    r = min(len(tt) // 2, int(0.07 * SR))
    env[-r:] *= np.linspace(1, 0, r) ** 2
    return _lp(sig * env, 2000)


def soft_tock(rng, dur=0.18):
    """Wooden backbeat instead of a snare: a low knock with a little woody noise, under ~1.8 kHz."""
    tt = t_axis(dur)
    f = 170 + 110 * np.exp(-tt * 40)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 26)
    noise = _bp(rng.standard_normal(len(tt)), 250, 1400) * np.exp(-tt * 55) * 0.45
    return _lp(body + noise, 1800)



def soft_vibes(f, dur=3.0):
    """Mellow vibraphone with soft yarn mallets for happy moments (owner, TW0002: the house-done chime was too bright
    and chimey; wanted something rounder and more wooden). Mostly the fundamental, the bar's 4th partial very quiet
    and gone in ~40 ms, a little woody knock, a slow motor tremolo, and nothing above ~1.6 kHz."""
    tt = t_axis(dur)
    trem = 1 - 0.18 * (0.5 - 0.5 * np.cos(2 * np.pi * 4.6 * tt)) * np.clip(tt / 0.25, 0, 1)
    sig = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 1.1) * trem
           + 0.05 * np.sin(2 * np.pi * 3.98 * f * tt) * np.exp(-tt * 25)
           + 0.1 * np.sin(2 * np.pi * 0.5 * f * tt) * np.exp(-tt * 18))
    a = int(0.012 * SR)
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    r = int(0.2 * SR)
    sig[-r:] *= np.linspace(1, 0, r) ** 2
    return _lp(sig, 1600)


def sunny_chord(k, start=0):
    return SUNNY_PROG[(k + start) % len(SUNNY_PROG)]


def sunny_bed(dur, rng, bar=2.18, t0=0.0, start=0, final_at=None, final_chord=(), form=None, gain=0.3,
              sea=0.03, swing=0.08):
    """Bars start at t0 + k * bar (t0 <= 0 lets a downbeat land exactly on `final_at`); bar k plays
    sunny_chord(k, start). Bar 0 is a build-up and the bars up to the first IV chord finish an "answer" phrase;
    after that each 4-bar phrase takes the next section of `form`. From `final_at` the groove stops with a kick and the final chord rings."""
    n = int(dur * SR)
    music = np.zeros((n, 2))       # melodic layer, dips a little under each kick (gentle pump)
    low = np.zeros((n, 2))         # bass and drums
    s16 = bar / 16
    stop = final_at if final_at is not None else dur
    form = list(form or SUNNY_FORM)
    first = next(k for k in range(4) if (k + start) % 4 == 0)
    kicks = []
    tock = soft_tock(rng)
    kick_s = _lp(kick(), 300)
    bass_cache, pluck_cache = {}, {}

    def at(k, step):
        return t0 + k * bar + step * s16 + (swing * s16 if step % 2 else 0.0)

    k = 0
    while t0 + k * bar < stop - 1e-6:
        notes = sunny_chord(k, start)
        root, voicing = notes[0], notes[1:]
        if k == 0 and first > 0:                       # one bar of build-up: arpeggio, bass, a soft kick and stabs
            L = dict(arp=0.7, bass=0.7, kick=0.6, tock=0.0, stabs=0.6, lead=None, bells=0.0, pad=0.0)
            in_phrase = False
        elif k < first:                                # then the tail of an "answer" phrase, so the tune starts early
            L = SUNNY_SECTIONS["answer"]
            in_phrase = True
        else:
            L = SUNNY_SECTIONS[form[((k - first) // 4) % len(form)]]
            in_phrase = True
        last_bar = final_at is not None and t0 + (k + 1) * bar >= stop - 1e-6
        ci = (k + start) % 4
        # arpeggio over the chord tones
        if L["arp"]:
            tones = sorted(voicing)
            tones = tones + [tones[1] + 12]
            for step in range(16):
                ts = at(k, step)
                if ts >= stop - 0.02 or ts < -0.3:
                    continue
                m = tones[ARP_STEPS[step] % len(tones)]
                if m not in pluck_cache:
                    pluck_cache[m] = pluck(midi(m))
                vel = (1.0 if step % 4 == 0 else 0.7 if step % 2 == 0 else 0.55) * L["arp"]
                place(music, pluck_cache[m] * gain * 0.22 * vel, ts, pan=0.35 * np.sin(step * np.pi / 4))
        # offbeat piano stabs, a softer chord on the one
        if L["stabs"]:
            for step, ln, vel in ((0, 0.9, 0.5), (2, 0.35, 0.8), (6, 0.35, 0.6), (10, 0.35, 0.8), (14, 0.35, 0.6)):
                ts = at(k, step)
                if ts >= stop - 0.05:
                    continue
                for j, m in enumerate(voicing):
                    place(music, epiano(midi(m), min(ln, stop - ts + 0.3) + 0.26, ts) * gain * 0.1 * vel * L["stabs"],
                          ts + 0.004 * j, pan=(j / 3 - 0.5) * 0.5)
        if L["pad"]:
            ln = min(bar + 0.6, stop - at(k, 0) + 0.5)
            for j, m in enumerate(voicing):
                place(music, epiano(midi(m), ln, at(k, 0), wobble=0.002) * gain * 0.2 * L["pad"], at(k, 0) + 0.01 * j,
                      pan=(j / 3 - 0.5) * 0.4)
        # bouncy bass: root, octave and fifth on a syncopated line (long notes in the break)
        if L["bass"]:
            line = ((0, 0, 3), (3, 0, 1), (4, 12, 2), (6, 0, 2), (8, 7, 2), (10, 0, 1), (11, 12, 2), (14, 7, 2))
            if L["pad"] >= 1.0:
                line = ((0, 0, 8), (8, 7, 6))
            for step, iv, ln in line:
                ts = at(k, step)
                if ts >= stop - 0.03:
                    continue
                m = root + iv
                if (m, ln) not in bass_cache:
                    bass_cache[(m, ln)] = bouncy_bass(midi(m), ln * s16 + 0.12)
                place(low, bass_cache[(m, ln)] * gain * 0.3 * L["bass"], ts)
        # drums: kick on 1 and 3 (plus a pickup), wooden tock on 2 and 4; a little fill into the final
        if L["kick"]:
            for step in ((0, 8) if last_bar else (0, 8, 14)):
                ts = at(k, step)
                if ts < stop - 0.03:
                    place(low, kick_s * gain * 0.45 * L["kick"] * (0.6 if step == 14 else 1.0), ts)
                    kicks.append(ts)
        if L["tock"]:
            steps = (((4, 1.0), (10, 0.5), (12, 0.65), (13, 0.75), (14, 0.85), (15, 1.0)) if last_bar
                     else ((4, 1.0), (12, 1.0)))
            for step, v in steps:
                ts = at(k, step)
                if ts < stop - 0.03:
                    place(low, tock * gain * 0.4 * v * L["tock"], ts, pan=0.1)
        # lead and counter-bells
        if L["lead"] and in_phrase:
            for step, m, ln in SUNNY_MELODY[L["lead"]][ci]:
                ts = at(k, step)
                if ts >= stop - 0.05:
                    continue
                d = min(ln * s16 * 0.92, stop - ts + 0.15) + 0.08
                place(music, soft_lead(midi(m), d) * gain * 0.2, ts, pan=-0.08)
                if L["lead"] == "slow":
                    place(music, warm_bell(midi(m), dur=2.5) * gain * 0.12, ts, pan=0.2)
        if L["bells"]:
            ts = at(k, 8)
            if ts < stop - 0.05:
                m = max(voicing) + 12 if max(voicing) + 12 <= 88 else max(voicing)
                place(music, warm_bell(midi(m), dur=2.0) * gain * 0.08 * L["bells"], ts, pan=0.3)
        k += 1
    if final_at is not None and final_chord:
        ln = dur - final_at + 0.5
        for j, m in enumerate(final_chord[1:]):
            place(music, epiano(midi(m), ln, final_at, wobble=0.0018) * gain * 0.22, final_at + 0.02 * j,
                  pan=(j / 3 - 0.5) * 0.4)
        place(low, soft_bass(midi(final_chord[0]), ln) * gain * 0.45, final_at)
        place(low, kick_s * gain * 0.45, final_at)
        top = final_chord[-1] + 5 if final_chord[-1] + 5 <= 84 else final_chord[-1]
        place(music, soft_lead(midi(top), 2.2) * gain * 0.16, final_at, pan=-0.08)
    if kicks:
        duck = np.ones(n)
        for ts in kicks:
            i = int(ts * SR)
            if 0 <= i < n:
                m = min(n - i, int(0.25 * SR))
                duck[i:i + m] = np.minimum(duck[i:i + m], 1 - 0.22 * np.exp(-np.arange(m) / SR * 14))
        music *= duck[:, None]
    buf = music + low
    if sea:
        w = sea_wash(dur, rng)
        buf[:, 0] += w * sea
        buf[:, 1] += np.roll(w, int(0.37 * SR)) * sea
    return buf, None


if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    ambient_pad()
    marble_race()
    music_box()


# ---------- Robot Rescue Squad (families/foundry/stations/robot_rescue.py) ----------

def robot_boot(dur=0.9, rng=None):
    """A robot starting up, made to be heard over music (owner 2026-11-17: the darker machine sounds "don't appear
    at all"): three relay clicks, a rising run of five square-ish beeps, a servo whine sweeping up through the
    mid range, and a low contactor thunk at the end. Nothing above ~5 kHz, so it is bright but not harsh."""
    rng = rng if rng is not None else _RNG
    n = int(max(dur, 0.6) * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for t0 in (0.0, 0.055, 0.11):                                  # relay clicks
        i = int(t0 * SR)
        m = min(n - i, int(0.012 * SR))
        out[i:i + m] += _bp(rng.standard_normal(m + 64), 1200, 4500)[:m] * np.exp(-np.arange(m) / SR * 500) * 0.9
    for j, f in enumerate((392.0, 523.3, 659.3, 784.0, 1046.5)):   # rising beeps
        i0 = int((0.16 + 0.062 * j) * SR)
        m = min(n - i0, int(0.055 * SR))
        if m <= 0:
            break
        ts = np.arange(m) / SR
        sq = sum(np.sin(2 * np.pi * f * k * ts) / k for k in (1, 3, 5))
        out[i0:i0 + m] += sq * np.clip(ts / 0.004, 0, 1) * np.clip((0.055 - ts) / 0.012, 0, 1) * 0.42
    u = np.clip((tt - 0.12) / 0.5, 0, 1)                            # servo whine, sweeping up
    f = 320 + 1100 * u ** 1.4 + 18 * np.sin(2 * np.pi * 31 * tt)
    ph = 2 * np.pi * np.cumsum(f) / SR
    whine = (np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)) * np.sin(np.pi * u) ** 0.7 * (tt > 0.12)
    out += _lp(whine, 4200) * 0.30
    i0 = int(0.60 * SR)                                             # contactor thunk
    if i0 < n:
        ts = np.arange(n - i0) / SR
        out[i0:] += (np.sin(2 * np.pi * (95 - 40 * np.clip(ts / 0.1, 0, 1)) * ts) * np.exp(-ts * 16) * 0.8
                     + _bp(rng.standard_normal(n - i0), 300, 1600) * np.exp(-ts * 60) * 0.35)
    return _lp(out, 5000) * 1.0


def siren(dur=6.0, rng=None):
    """An alarm siren: a slow two-tone wail (rises and falls about 0.8 times a second), soft-edged and
    low-passed so it reads as an alarm without being piercing. Fades in over 0.3 s and out over 1.5 s."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 640 + 190 * np.sin(2 * np.pi * 0.8 * tt - np.pi / 2)
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.28 * np.sin(3 * ph) + 0.12 * np.sin(4 * ph)
    env = np.clip(tt / 0.3, 0, 1) * np.clip((dur - tt) / 1.5, 0, 1)
    return _lp(tone, 3200) * env * 0.42
