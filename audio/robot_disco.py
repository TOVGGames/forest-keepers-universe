"""Robot disco: the soundtrack for the Foundry Robot Games (docs/engines/foundry.md section 17).

Owner brief (2026-10-28): a mid-tempo electronic dance track, ~120-125 BPM, 4/4 - steady kick on every
beat, a sharp clap on 2 and 4, tight ticking 16th hi-hats; built on a short, repeating two-bar funk riff
(fat rubbery synth bass doubled by a muted, slightly driven guitar) that sounds like a loop lifted from an
old disco record; the loop is compressed and pumps with the kick; a fully robotic vocoded voice sings
short two-syllable action words in clipped pairs, each word on a note of the riff, later stacked, sped up
and chopped into call-and-response bursts between a higher and a lower robot voice; a resonant low-pass
filter sweeps slowly open and closed over the loop; midway the arrangement strips down to a sparse
filtered break before the full beat and vocals slam back in. Bright, punchy, mechanical, funky.

Everything is synthesized here (no samples). The arrangement follows the video: `cues` are times the
Robot Games station records while the video runs (power on, each event, the break, the podium), each
snapped to the next bar so changes land on the downbeat:

  factory  (0 .. power)   kick + hats + the loop with the filter mostly closed, claps join later,
                          a lone low robot voice now and then ("BUILD-ING", "RO-BOT")
  power on                riser into the drop; full beat, the filter opens; "POW-ER / ON-LINE"
  events                  full groove; words for each event, call and response, faster and stacked
                          as the games go on (16th-note stutters in the hurdles and the javelin)
  break    (hurdles -> shot put)  kick and claps out, loop filtered right down, sparse hats, one voice
  podium                  everything, "CHAM-PION / WIN-NER"
Kept warm for the owner (docs: 1-5 kHz harshness): hats and claps low-passed and quiet, the guitar
band-limited, the voices' top formant soft, no hard clipping.
"""
import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi

from audio.synth import SR, midi, place

# two-bar funk riff in E dorian: (16th step, MIDI note, length in 16ths)
RIFF = [(0, 40, 2), (3, 40, 1), (4, 52, 1), (6, 50, 1), (7, 52, 1), (8, 43, 2), (10, 45, 1), (11, 45, 1),
        (14, 47, 1), (15, 50, 1),
        (16, 40, 2), (19, 40, 1), (20, 43, 1), (22, 45, 2), (24, 45, 1), (25, 47, 1), (26, 50, 2), (28, 52, 1),
        (30, 50, 1), (31, 47, 1)]
GHOSTS = [2, 5, 9, 13, 18, 21, 23, 27, 29]           # muted guitar "chk" on empty 16ths

VOWELS = {"a": (730, 1090, 2440), "e": (530, 1840, 2480), "i": (390, 1990, 2550), "ee": (280, 2250, 2900),
          "o": (570, 840, 2410), "uh": (640, 1190, 2390), "u": (320, 870, 2240), "er": (490, 1350, 1690),
          "aw": (590, 880, 2400)}
GLIDES = {"au": ("a", "u"), "ai": ("a", "ee"), "oi": ("o", "ee")}
STOPS = {"p": 700, "b": 500, "t": 2600, "d": 1800, "k": 1500, "g": 1100}
FRICS = {"s": (3500, 6500), "sh": (2000, 4200), "f": (1500, 5000), "th": (1800, 5000), "ch": (2000, 4500)}
NASALS = {"m": (280, 1000), "n": (280, 1500), "ng": (280, 2000), "l": (360, 1100), "r": (420, 1150),
          "w": (320, 800), "y": (300, 2100)}

# two-syllable action words: each syllable (onset, vowel, coda)
WORDS = {
    "BUILD-ING": [("b", "i", "l"), (None, "i", "ng")], "RO-BOT": [("r", "o", None), ("b", "aw", "t")],
    "POW-ER": [("p", "au", None), (None, "er", None)], "ON-LINE": [(None, "aw", "n"), ("l", "ai", "n")],
    "SYS-TEM": [("s", "i", "s"), ("t", "e", "m")], "BOOT-UP": [("b", "u", "t"), (None, "uh", "p")],
    "RUN-NING": [("r", "uh", "n"), ("n", "i", "ng")], "SPEED-UP": [("s", "ee", "d"), (None, "uh", "p")],
    "GO-GO": [("g", "o", None), ("g", "o", None)], "FAST-ER": [("f", "a", "s"), ("t", "er", None)],
    "JUMP-ING": [("ch", "uh", "m"), ("p", "i", "ng")], "HUR-DLE": [(None, "er", "d"), ("l", "uh", None)],
    "UP-UP": [(None, "uh", "p"), (None, "uh", "p")], "THROW-ING": [("th", "o", None), ("w", "i", "ng")],
    "HEA-VY": [(None, "e", None), ("w", "ee", None)], "PUSH-IT": [("p", "u", "sh"), (None, "i", "t")],
    "LAUNCH-ING": [("l", "aw", "n"), ("ch", "i", "ng")], "HIGH-ER": [(None, "ai", None), (None, "er", None)],
    "FAR-THER": [("f", "a", None), ("th", "er", None)], "CHAM-PION": [("ch", "a", "m"), ("p", "ee", "n")],
    "WIN-NER": [("w", "i", "n"), ("n", "er", None)], "MA-CHINE": [("m", "uh", None), ("sh", "ee", "n")],
    "SPIN-NING": [("s", "i", "n"), ("n", "i", "ng")], "BA-TON": [("b", "a", None), ("t", "aw", "n")],
    "FLY-ING": [("f", "ai", None), (None, "i", "ng")], "SWEEP-ING": [("s", "ee", "p"), (None, "i", "ng")],
    "SLID-ING": [("s", "ai", "d"), (None, "i", "ng")],
    "WALK-ING": [("w", "aw", "k"), (None, "i", "ng")], "STEP-STEP": [("s", "e", "p"), ("s", "e", "p")],
    "FLIP-PING": [("f", "i", "p"), ("p", "i", "ng")], "CLIMB-ING": [("k", "ai", "m"), (None, "i", "ng")],
    "PULL-ING": [("p", "u", "l"), ("l", "i", "ng")], "DIS-CUS": [("d", "i", "s"), ("k", "uh", "s")],
    "FI-NAL": [("f", "ai", None), ("n", "uh", "l")],
}
SECTION_WORDS = {
    "factory": [["BUILD-ING", "RO-BOT"], ["MA-CHINE", "BUILD-ING"]],
    "power": [["POW-ER", "ON-LINE"], ["SYS-TEM", "BOOT-UP"]],
    "sprint": [["RUN-NING", "SPEED-UP"], ["GO-GO", "FAST-ER"]],
    "hurdles": [["JUMP-ING", "HUR-DLE"], ["UP-UP", "JUMP-ING"]],
    "break": [["RO-BOT", "MA-CHINE"]],
    "shot": [["THROW-ING", "HEA-VY"], ["PUSH-IT", "POW-ER"]],
    "javelin": [["LAUNCH-ING", "HIGH-ER"], ["FAR-THER", "LAUNCH-ING"]],
    "podium": [["CHAM-PION", "WIN-NER"], ["RO-BOT", "CHAM-PION"]],
    # Robot Games II
    "longjump": [["JUMP-ING", "FAR-THER"], ["LAUNCH-ING", "UP-UP"]],
    "hammer": [["SPIN-NING", "THROW-ING"], ["HEA-VY", "SPIN-NING"]],
    "vault": [["HIGH-ER", "UP-UP"], ["JUMP-ING", "HIGH-ER"]],
    "walk": [["WALK-ING", "FAST-ER"], ["STEP-STEP", "WALK-ING"]],
    # Winter Games
    "skate": [["SLID-ING", "FAST-ER"], ["GO-GO", "SPEED-UP"]],
    "skijump": [["FLY-ING", "HIGH-ER"], ["LAUNCH-ING", "FAR-THER"]],
    "bobsled": [["PUSH-IT", "FAST-ER"], ["GO-GO", "SLID-ING"]],
    "curling": [["SWEEP-ING", "SLID-ING"], ["PUSH-IT", "SWEEP-ING"]],
    # Obstacle course
    "course": [["RUN-NING", "JUMP-ING"], ["UP-UP", "FAST-ER"]],
    # Pentathlon
    "tireflip": [["FLIP-PING", "HEA-VY"], ["PUSH-IT", "FLIP-PING"]],
    "rope": [["CLIMB-ING", "UP-UP"], ["PULL-ING", "HIGH-ER"]],
    "discus": [["SPIN-NING", "DIS-CUS"], ["THROW-ING", "FAR-THER"]],
    "highjump": [["JUMP-ING", "HIGH-ER"], ["UP-UP", "FLY-ING"]],
}
CHOP = ("hurdles", "javelin", "vault", "walk", "skijump", "curling", "course", "rope", "highjump")           # sections whose phrases get chopped into bursts


# ---------- instruments ----------

def _env(n, a, d, hold=0.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-np.maximum(0.0, t - a - hold) / max(d, 1e-4))
    return e


def _saw(f, n, phase=0.0):
    """Band-limited sawtooth (additive, harmonics below 9 kHz)."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    k = 1
    while k * f < 9000 and k < 60:
        out += np.sin(2 * np.pi * k * f * t + phase * k) / k
        k += 1
    return out * 0.6


def kick():
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 48 + 95 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.16)
    click = np.sin(2 * np.pi * 1200 * t) * np.exp(-t / 0.004) * 0.12
    return (body + click) * 0.85


def clap(rng):
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    env = np.zeros(n)
    for d in (0.0, 0.009, 0.018):                       # three hands, a hair apart
        env += np.where(t >= d, np.exp(-(t - d) / 0.008), 0.0) * 0.6
    env += np.where(t >= 0.026, np.exp(-(t - 0.026) / 0.07), 0.0)
    sig = sosfilt(butter(2, [700, 2600], "band", fs=SR, output="sos"), noise * env)
    return sosfilt(butter(2, 3000, "low", fs=SR, output="sos"), sig) * 0.9


def hat(rng, open_=False):
    n = int((0.11 if open_ else 0.035) * SR)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n) * np.exp(-t / (0.04 if open_ else 0.009))
    sig = sosfilt(butter(2, 6500, "high", fs=SR, output="sos"), noise)
    return sosfilt(butter(2, 10000, "low", fs=SR, output="sos"), sig) * 0.35


def bass_note(m, dur):
    """Fat, rubbery: saw + square-ish + sub, a quick filter 'blip' at the start of each note."""
    f = midi(m)
    n = int((dur + 0.05) * SR)
    t = np.arange(n) / SR
    tone = _saw(f, n) + 0.5 * np.sign(np.sin(2 * np.pi * f * t)) * 0.4 + 0.45 * np.sin(2 * np.pi * f * t)
    out = np.zeros(n)
    # time-varying low-pass in a few blocks: bright on the attack, closing fast (the "rubber")
    blocks = 8
    for b in range(blocks):
        i0, i1 = n * b // blocks, n * (b + 1) // blocks
        fc = 480 + 1900 * np.exp(-(i0 / SR) / 0.06)
        out[i0:i1] = sosfilt(butter(2, fc, "low", fs=SR, output="sos"), tone)[i0:i1]
    env = np.minimum(1, t / 0.004) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.012)) * (0.75 + 0.25 * np.exp(-t / 0.08))
    return np.tanh(out * env * 1.6) * 0.8


def guitar_note(m, dur, rng):
    """Muted, slightly driven electric guitar: a short damped pluck (Karplus-Strong), band-limited."""
    f = midi(m)
    n = int((dur * 0.6 + 0.06) * SR)
    p = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, p)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.985   # palm mute: heavy damping
    out *= np.exp(-np.arange(n) / SR / 0.07)
    out = np.tanh(out * 3.0) * 0.5
    return sosfilt(butter(2, [220, 2200], "band", fs=SR, output="sos"), out)


def guitar_chk(rng):
    n = int(0.05 * SR)
    noise = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR / 0.012)
    return sosfilt(butter(2, [400, 1800], "band", fs=SR, output="sos"), noise) * 0.35


def _formant(src, fmts, gains=(1.0, 0.5, 0.18), bw=(90, 120, 170)):
    out = np.zeros_like(src)
    for f, g, b in zip(fmts, gains, bw):
        lo, hi = max(60, f - b), min(SR / 2 - 200, f + b)
        out += sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), src) * g
    return out


def syllable(m, dur, onset, vowel, coda, rng):
    """One robot syllable on pitch m: buzzy carrier through vowel formants, hard-gated (vocoder style),
    consonants as filtered noise bursts / nasal hums."""
    f = midi(m)
    n = int(dur * SR)
    car = _saw(f, n) + 0.6 * _saw(f / 2, n)                   # an octave-down layer: thick, machine-like
    t = np.arange(n) / SR
    v0, v1 = GLIDES.get(vowel, (vowel, vowel))
    a = _formant(car, VOWELS[v0])
    b = _formant(car, VOWELS[v1]) if v1 != v0 else a
    x = np.clip((t - 0.25 * dur) / (0.5 * dur), 0, 1)
    voiced = a * (1 - x) + b * x
    on = int(0.035 * SR)
    off = int(0.045 * SR)
    gate = np.ones(n)
    ka, kr = on // 3, off // 3
    gate[:ka] = np.linspace(0, 1, ka)
    gate[n - kr:] = np.linspace(1, 0, kr)
    out = voiced * gate
    if onset in NASALS or coda in NASALS:                      # nasal / liquid: low formants for a moment
        for c, sl in ((onset, slice(0, on)), (coda, slice(n - off, n))):
            if c in NASALS:
                seg = _formant(car, (NASALS[c][0], NASALS[c][1], 2500), gains=(1.0, 0.25, 0.05))
                out[sl] = seg[sl] * 0.8 * gate[sl]
    for c, at_start in ((onset, True), (coda, False)):
        if c in STOPS or c in FRICS:
            ln = int((0.02 if c in STOPS else 0.06) * SR)
            noise = rng.normal(0, 1, ln) * np.exp(-np.arange(ln) / SR / (0.008 if c in STOPS else 0.03))
            if c in STOPS:
                fc = STOPS[c]
                burst = sosfilt(butter(2, [max(200, fc * 0.6), min(4000, fc * 1.5)], "band", fs=SR, output="sos"), noise)
            else:
                lo, hi = FRICS[c]
                burst = sosfilt(butter(2, [lo, min(hi, 6000)], "band", fs=SR, output="sos"), noise) * 0.5
            if at_start:
                out[:ln] = out[:ln] * 0.3 + burst * 0.35
            else:
                out[-ln:] = out[-ln:] * 0.2 + burst * 0.3
    out = np.round(out * 24) / 24                              # a touch of quantisation: no human warmth
    return sosfilt(butter(2, 5200, "low", fs=SR, output="sos"), out) * 0.55


# ---------- arrangement ----------

def _snap(t, bar):
    return np.ceil(t / bar - 1e-6) * bar


def _sections(dur, cues, bar):
    """[(start, end, name)] covering the whole video, starts snapped to bars."""
    c = dict(cues or {})
    marks = [(0.0, "factory")]
    for key, t in c.items():                                  # every cue the video recorded, in time order
        marks.append((_snap(t, bar), key))
    marks.sort()
    out = []
    for (s, name), (e, _) in zip(marks, marks[1:] + [(dur, None)]):
        if e > s:
            out.append((s, e, name))
    return out


def robot_disco_bed(dur, rng, bpm=122, cues=None, gain=1.0, **_):
    beat = 60.0 / bpm
    bar = 4 * beat
    st = beat / 4                                            # a 16th
    n = int(dur * SR)
    secs = _sections(dur, cues, bar)
    sec_at = lambda t: next((s for s in secs if s[0] <= t < s[1]), secs[-1])
    power_t = next((s[0] for s in secs if s[2] == "power"), dur)

    # --- the loop (bass + muted guitar), lifted-from-a-record: rendered once, tiled ---
    L = int(round(2 * bar * SR))
    loop_b = np.zeros((L + SR, 2))
    loop_g = np.zeros((L + SR, 2))
    for step, m, ln in RIFF:
        place(loop_b, bass_note(m, ln * st * 0.92), step * st, pan=0.0)
        place(loop_g, guitar_note(m + 12, ln * st, rng), step * st + 0.004, pan=0.25)
    for step in GHOSTS:
        place(loop_g, guitar_chk(rng), step * st, pan=0.25)
    loop_b[:SR // 2] += loop_b[L:L + SR // 2]
    loop_g[:SR // 2] += loop_g[L:L + SR // 2]
    loop = (loop_b[:L] * 0.6 + loop_g[:L] * 2.3)
    loop = sosfilt(butter(1, 6500, "low", fs=SR, output="sos"), loop, axis=0)   # old-record top end
    reps = n // L + 1
    tiled = np.tile(loop, (reps, 1))[:n]

    # --- resonant low-pass sweep over the loop (block-wise, state carried across blocks) ---
    tt = np.arange(n) / SR
    out_loop = np.zeros_like(tiled)
    blk = 1024
    zi = None
    for i0 in range(0, n, blk):
        t0 = i0 / SR
        s0, s1, name = sec_at(t0)
        lfo = 0.5 - 0.5 * np.cos(2 * np.pi * t0 / (16 * bar))          # slow open-close every 16 bars
        if name == "factory":
            lo, hi = 260, 1300 + 900 * min(1.0, t0 / max(power_t, 1))
        elif name == "break":
            lo, hi = 220, 700
        elif name == "power":
            lo, hi = 900, 6500
            lfo = min(1.0, (t0 - s0) / (4 * bar))                       # it opens up as they power on
        else:
            lo, hi = 1000, 7500
        fc = lo * (hi / lo) ** lfo
        sos = butter(2, fc, "low", fs=SR, output="sos")
        # resonance: a narrow peak at the cutoff on top of the low-pass
        peak = butter(1, [fc * 0.8, min(fc * 1.25, SR / 2 - 100)], "band", fs=SR, output="sos")
        seg = tiled[i0:i0 + blk]
        if zi is None:
            zi = [np.zeros((sos.shape[0], 2, 2)), np.zeros((peak.shape[0], 2, 2))]
        y1, zi[0] = sosfilt(sos, seg, axis=0, zi=zi[0])
        y2, zi[1] = sosfilt(peak, seg, axis=0, zi=zi[1])
        out_loop[i0:i0 + blk] = y1 + 0.9 * y2
    # compressed, pumping with the kick
    ph = (tt % beat) / beat
    pump = 1 - 0.68 * np.exp(-ph * beat / 0.12)
    drums = np.zeros((n, 2))
    vox = np.zeros((n, 2))
    K, C = kick(), clap(rng)
    H, HO = hat(rng), hat(rng, True)
    nb = int(dur / beat) + 1
    for b in range(nb):
        t = b * beat
        s0, s1, name = sec_at(t)
        bar_i = int(round((t - s0) / bar))
        in_bar = b % 4
        if name == "break":
            if in_bar == 0 and bar_i % 2 == 0:
                place(drums, K * 0.45, t)
            for q in (2,):
                place(drums, H * 0.7, t + q * st)
            # riser into the slam at the end of the break
            if s1 - t <= 2 * bar and s1 - t > 2 * bar - beat:
                r = int(2 * bar * SR)
                rt = np.arange(r) / SR
                noise = rng.normal(0, 1, r) * (rt / (2 * bar)) ** 2
                rs = np.zeros(r)
                for j in range(8):
                    i0, i1 = r * j // 8, r * (j + 1) // 8
                    rs[i0:i1] = sosfilt(butter(2, 400 + 3500 * (j / 8) ** 2, "low", fs=SR, output="sos"), noise)[i0:i1]
                place(drums, rs * 0.35, t)
            continue
        quiet = name == "factory" and t < 24 * bar
        place(drums, K * (0.8 if name == "factory" else 1.0), t)
        if in_bar in (1, 3) and not quiet:
            place(drums, C * (0.9 if name == "factory" else 1.3), t, pan=0.05)
        for q in range(4):
            acc = 1.0 if q == 2 else (0.55 if q in (1, 3) else 0.4)
            hh = HO if (q == 2 and in_bar == 3 and name not in ("factory",)) else H
            place(drums, hh * acc * (1.5 if name == "factory" else 2.2), t + q * st, pan=0.3 if q % 2 else -0.2)
    # riser into the power-on drop
    if power_t < dur:
        r = int(4 * bar * SR)
        rt = np.arange(r) / SR
        noise = rng.normal(0, 1, r) * (rt / (4 * bar)) ** 2
        rs = np.zeros(r)
        for j in range(16):
            i0, i1 = r * j // 16, r * (j + 1) // 16
            rs[i0:i1] = sosfilt(butter(2, 300 + 4000 * (j / 16) ** 2, "low", fs=SR, output="sos"), noise)[i0:i1]
        place(drums, rs * 0.3, power_t - 4 * bar)

    # --- the robot voices: words on riff notes, call (high) and response (low) ---
    riff_notes = {s: m for s, m, _ in RIFF}
    onsets = [s for s, _, _ in RIFF]
    nbar2 = int(dur / (2 * bar)) + 1
    for k in range(nbar2):
        t0 = k * 2 * bar
        s0, s1, name = sec_at(t0)
        phrase = (t0 - s0) / (2 * bar)                                 # loops since the section began
        pool = SECTION_WORDS.get(name, SECTION_WORDS["factory"])
        words = pool[int(phrase // 4) % len(pool)]
        if name == "factory":
            if t0 < 32 * bar or k % 4 != 1:
                continue
            plan = [(0, words[0], "low")]
        elif name == "break":
            if k % 2:
                continue
            plan = [(0, words[0], "low")]
        else:
            heat_ = min(3, int(phrase // 4))                            # the longer a section runs, the busier
            if name in ("power", "podium"):
                heat_ = max(heat_, 1)
            plan = [(0, words[0], "high"), (16, words[1], "low")]
            if heat_ >= 1:
                plan += [(8, words[0], "high"), (24, words[1], "low")]
            if heat_ >= 2 or name in CHOP:
                plan += [(28, words[0], "high"), (30, words[1], "low")]   # chopped, sped-up bursts
        for step0, word, voice in plan:
            syl = WORDS[word]
            # each syllable lands on the next riff note at/after step0
            cands = [s for s in onsets if s >= step0][:2]
            if len(cands) < 2:
                cands = [step0, step0 + 2]
            for (onset_c, vowel, coda), s in zip(syl, cands):
                m = riff_notes.get(s, 40) + (24 if voice == "high" else 12)
                ln = 0.18 if (s - step0) < 6 else 0.14
                if name in CHOP and step0 >= 28:
                    ln = 0.1
                sig = syllable(m, ln, onset_c, vowel, coda, rng)
                place(vox, sig * (0.55 if voice == "high" else 0.6), t0 + s * st, pan=-0.25 if voice == "high" else 0.25)
                if step0 >= 28 and name in CHOP:                         # stutter: chop and repeat
                    place(vox, sig[: int(0.06 * SR)] * 0.5, t0 + s * st + st, pan=0.35 if voice == "high" else -0.35)

    # mix: the loop and voices pump with the kick
    level = np.ones(n)
    for s0, s1, name in secs:
        i0, i1 = int(s0 * SR), int(s1 * SR)
        level[i0:i1] = {"factory": 0.75, "break": 0.6}.get(name, 1.0)
    mix = out_loop * (pump * level)[:, None] * 0.75 + drums * 0.8 + vox * pump[:, None] * 3.4
    mix = sosfilt(butter(2, 30, "high", fs=SR, output="sos"), mix, axis=0)
    peak = np.max(np.abs(mix)) + 1e-9
    return mix / peak * 0.9 * gain, None
