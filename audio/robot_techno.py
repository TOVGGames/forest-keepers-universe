"""Robot season soundtracks after the FE0017 disco (docs/engines/foundry.md sections 18-19). Owner
(2026-10-30): every robot video gets its own track - similar energy, not the same music - so each video
can succeed on its audio as well as its picture. Same cue-driven arrangement as `robot_disco` (the
Robot Games station records cues: power on, each event, the break, the podium; changes land on the next
downbeat) and the same vocoded robot voice, but a different groove, key and set of instruments per style:

  industrial  (Robot Games II, ~126 BPM, A minor)  four-on-the-floor techno: deep warm kick, rolling
              off-beat 16th bass, a squelchy resonant "acid" line, dark minor chord stabs with an echo,
              metal-shop percussion (an anvil tick on the off-beats, a low clank every four bars, a
              piston hiss swell), open hats on the off-beats; the voice is sparser and lower
  winter      (Robot Winter Games, ~116 BPM, B minor)  icy electro synth-pop: kick and snare
              electro beat, a plucked synth bass on the chords (Bm - G - D - A), a sparkling bell
              arpeggio with a ping-pong echo, a slow warm pad, a soft sleigh shaker; the voice
              only now and then
  finale      (Robot Pentathlon, the season finale, ~122 BPM, D major)  a stadium anthem: four-on-the-floor
              with soft claps, a driving octave bass, wide warm chords (D - A - Bm - G), a synth-brass hook
              over the events, bells in the factory; claps on every beat for the 100 m and the podium

Kept warm for the owner (1-5 kHz harshness): metal hits, hats and shakers low-passed and quiet, no hard
clipping (soft tanh only), every pitched part inside MIDI 36-96.
"""
import numpy as np
from scipy.signal import butter, sosfilt

from audio.synth import SR, midi, place
from audio.robot_disco import syllable, WORDS, SECTION_WORDS, CHOP, _sections, _saw, hat

STYLES = {
    "industrial": dict(bpm=126),
    "winter": dict(bpm=116),
    "finale": dict(bpm=122),
}


def _lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR / 2 - 200), "low", fs=SR, output="sos"), x, axis=0)


def _bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, min(hi, SR / 2 - 200)], "band", fs=SR, output="sos"), x, axis=0)


def _t(n):
    return np.arange(n) / SR


# ---------- industrial instruments ----------

def kick_deep():
    n = int(0.5 * SR)
    t = _t(n)
    f = 44 + 120 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.24)
    return _lp(np.tanh(body * 2.0) * 0.8, 2500)


def anvil(f0=760, decay=1.0):
    """A small struck steel bar: inharmonic partials, short, low-passed so it rings without bite."""
    n = int(0.4 * decay * SR)
    t = _t(n)
    out = np.zeros(n)
    for r, a, tau in ((1.0, 1.0, 0.11), (2.76, 0.45, 0.05), (5.40, 0.2, 0.025), (8.93, 0.08, 0.012)):
        if f0 * r < 9000:
            out += a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t / (tau * decay))
    return _lp(out, 4200) * 0.3


def clank(rng):
    n = int(0.6 * SR)
    t = _t(n)
    body = anvil(205, 2.5)
    body = np.pad(body, (0, max(0, n - len(body))))[:n]
    hit = _lp(rng.normal(0, 1, n) * np.exp(-t / 0.02), 1600) * 0.4
    return (body * 1.6 + hit) * 0.6


def snare_dark(rng):
    n = int(0.25 * SR)
    t = _t(n)
    noise = _bp(rng.normal(0, 1, n) * np.exp(-t / 0.06), 350, 2000)
    tone = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.05)
    return _lp(noise * 0.8 + tone * 0.5, 2800) * 0.8


def hiss_swell(rng, dur):
    n = int(dur * SR)
    t = _t(n)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return _lp(_bp(rng.normal(0, 1, n), 500, 2400) * env, 1800) * 0.18


def roll_bass(m, dur):
    n = int((dur + 0.03) * SR)
    t = _t(n)
    f = midi(m)
    tone = _saw(f, n) + 0.6 * np.sin(2 * np.pi * f * t)
    out = np.zeros(n)
    for b in range(4):                                       # a filter blip on each note
        i0, i1 = n * b // 4, n * (b + 1) // 4
        out[i0:i1] = _lp(tone, 260 + 900 * np.exp(-(i0 / SR) / 0.04))[i0:i1]
    env = np.minimum(1, t / 0.003) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.01))
    return np.tanh(out * env * 1.8) * 0.7


def acid_note(m, dur, cut, accent):
    """Resonant low-pass on a saw (a 303-ish squelch, kept soft): the cutoff opens on the attack."""
    n = int((dur + 0.04) * SR)
    t = _t(n)
    tone = _saw(midi(m), n)
    out = np.zeros(n)
    blocks = 6
    for b in range(blocks):
        i0, i1 = n * b // blocks, n * (b + 1) // blocks
        fc = cut * (1 + (1.6 + 1.4 * accent) * np.exp(-(i0 / SR) / 0.05))
        fc = min(fc, 3200)
        lp = _lp(tone, fc)
        pk = _bp(tone, fc * 0.85, fc * 1.18, 1)
        out[i0:i1] = (lp + (0.8 + 0.8 * accent) * pk)[i0:i1]
    env = np.minimum(1, t / 0.004) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.015))
    return np.tanh(out * env * 1.4) * (0.45 + 0.2 * accent)


def stab(notes, dur):
    n = int((dur + 0.4) * SR)
    t = _t(n)
    out = np.zeros(n)
    for m in notes:
        for d in (-0.08, 0.08):
            out += _saw(midi(m) * 2 ** (d / 12), n)
    env = np.minimum(1, t / 0.006) * np.exp(-t / 0.22)
    return _lp(out * env, 1700) * 0.22


# ---------- winter instruments ----------

def bell_pluck(m, dur):
    """Soft FM bell: icy but rounded (modulation dies away fast, top end rolled off)."""
    n = int((dur + 0.6) * SR)
    t = _t(n)
    f = midi(m)
    idx = 1.3 * np.exp(-t / 0.07)
    sig = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t / 0.35)
    sig += 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.12)
    return _lp(sig * np.minimum(1, t / 0.002), 5000) * 0.3


def pad(notes, dur):
    n = int((dur + 0.8) * SR)
    t = _t(n)
    out = np.zeros(n)
    for m in notes:
        for d in (-0.1, 0.0, 0.1):
            out += _saw(midi(m) * 2 ** (d / 12), n)
    env = np.minimum(1, t / 0.45) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.5))
    return _lp(out * env, 1300) * 0.07


def pluck_bass(m, dur):
    n = int((dur + 0.05) * SR)
    t = _t(n)
    f = midi(m)
    tone = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + 0.7 * np.sin(2 * np.pi * f * t)
    out = _lp(tone, 700) * np.exp(-t / 0.18) * np.minimum(1, t / 0.003)
    return np.tanh(out * 1.6) * 0.6


def kick_round():
    n = int(0.4 * SR)
    t = _t(n)
    f = 50 + 90 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18) * 0.85


def snare_soft(rng):
    n = int(0.3 * SR)
    t = _t(n)
    noise = _bp(rng.normal(0, 1, n), 300, 2600) * np.exp(-t / 0.11)
    tone = np.sin(2 * np.pi * 200 * t) * np.exp(-t / 0.07)
    return _lp(noise * 0.7 + tone * 0.6, 3200) * 0.75


def shaker(rng):
    n = int(0.06 * SR)
    t = _t(n)
    return _lp(_bp(rng.normal(0, 1, n) * np.exp(-t / 0.018), 4500, 9000), 8000) * 0.12


# ---------- the beds ----------

def _voices(vox, dur, secs, sec_at, bar, st, notes_at, sparse, low_shift, rng):
    """Robot words on the bass/chord notes: one call per phrase (two in busy sections)."""
    nbar2 = int(dur / (2 * bar)) + 1
    for k in range(nbar2):
        t0 = k * 2 * bar
        s0, s1, name = sec_at(t0)
        if name in ("factory", "break"):
            if k % (4 if name == "factory" else 2) != 1:
                continue
        elif k % sparse != 0:
            continue
        phrase = (t0 - s0) / (2 * bar)
        pool = SECTION_WORDS.get(name, SECTION_WORDS["factory"])
        words = pool[int(phrase // 4) % len(pool)]
        plan = [(0, words[0], "high"), (16, words[1], "low")] if name not in ("factory", "break") else [(0, words[0], "low")]
        if name in CHOP and name not in ("factory", "break") and phrase % 4 >= 2:
            plan += [(28, words[0], "high"), (30, words[1], "low")]
        for step0, word, voice in plan:
            for j, (onset, vowel, coda) in enumerate(WORDS[word]):
                s = step0 + 2 * j
                m = notes_at(t0 + s * st) + (12 if voice == "high" else 0) + low_shift
                m = int(min(76, max(40, m)))
                ln = 0.1 if step0 >= 28 else 0.17
                sig = syllable(m, ln, onset, vowel, coda, rng)
                place(vox, sig * 0.55, t0 + s * st, pan=-0.25 if voice == "high" else 0.25)


def _industrial(dur, rng, bpm, cues):
    beat = 60.0 / bpm
    bar, st = 4 * beat, beat / 4
    n = int(dur * SR)
    secs = _sections(dur, cues, bar)
    sec_at = lambda t: next((s for s in secs if s[0] <= t < s[1]), secs[-1])
    power_t = next((s[0] for s in secs if s[2] == "power"), dur)
    roots = [45, 45, 41, 43]                                # A A F G, one bar each
    root_at = lambda t: roots[int(t / bar) % 4]
    ACID = [0, None, 12, 0, None, 3, None, 7, 0, 10, None, 12, 3, None, 7, 5]
    ACC = [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0]
    drums, bass, acid, keys, vox = (np.zeros((n, 2)) for _ in range(5))
    K, S = kick_deep(), snare_dark(rng)
    H, HO = hat(rng), hat(rng, True)
    A, CL = anvil(), clank(rng)
    nbeats = int(dur / beat) + 1
    bass_cache, acid_cache = {}, {}
    for b in range(nbeats):
        t = b * beat
        s0, s1, name = sec_at(t)
        in_bar = b % 4
        bar_i = int(t / bar)
        r = root_at(t)
        full = name not in ("factory", "break")
        if name == "break":
            if in_bar == 0 and bar_i % 2 == 0:
                place(drums, K * 0.4, t)
            place(drums, A * 0.5, t + 2 * st, pan=0.3)
            if s1 - t <= 2 * bar and s1 - t > 2 * bar - beat:          # swell into the slam
                place(drums, hiss_swell(rng, 2 * bar) * 1.6, t)
            if in_bar == 0 and bar_i % 2 == 0:
                place(keys, stab([r + 12, r + 15, r + 19], 2 * bar) * 0.5, t, pan=0.0)
            continue
        quiet = name == "factory" and t < 16 * bar
        place(drums, K * (0.75 if name == "factory" else 1.0), t)
        if in_bar in (1, 3) and not quiet:
            place(drums, S * (0.7 if name == "factory" else 1.0), t, pan=-0.05)
        for q in range(4):
            if q == 2:
                place(drums, HO * (0.9 if full else 0.5), t + q * st, pan=0.25)
                place(drums, A * (0.8 if full else 0.45), t + q * st, pan=-0.3)
            elif not quiet:
                place(drums, H * (0.9 if q % 2 else 0.5), t + q * st, pan=0.2)
        if full and in_bar == 3 and bar_i % 4 == 3:
            place(drums, CL * 0.9, t + 2 * st, pan=0.15)
        if full and in_bar == 0 and bar_i % 8 == 4:
            place(drums, hiss_swell(rng, 2 * beat), t)
        # rolling bass: the three 16ths after each kick
        if not quiet:
            for q, vel in ((1, 0.55), (2, 1.0), (3, 0.75)):
                key = (r, round(st * 0.85, 4))
                if key not in bass_cache:
                    bass_cache[key] = roll_bass(r, st * 0.85)
                place(bass, bass_cache[key] * vel * (0.7 if name == "factory" else 1.0), t + q * st)
        # acid line (events, power, podium), the cutoff drifting open and closed every 8 bars
        if full:
            lfo = 0.5 - 0.5 * np.cos(2 * np.pi * t / (8 * bar))
            for q in range(4):
                step = (in_bar * 4 + q) % 16
                off = ACID[step]
                if off is None:
                    continue
                m = r + 12 + off
                cut = 380 + 900 * lfo
                key = (m, round(cut, -1), ACC[step])
                if key not in acid_cache:
                    acid_cache[key] = acid_note(m, st * 0.8, cut, ACC[step])
                place(acid, acid_cache[key], t + q * st, pan=0.1)
            # minor stabs on the off-beat of beat 1 and 3, with an echo
            if in_bar in (0, 2):
                ch = stab([r + 12, r + 15, r + 19], st * 1.5)
                place(keys, ch, t + 2 * st, pan=-0.15)
                place(keys, ch * 0.35, t + 2 * st + 3 * st, pan=0.3)
                place(keys, ch * 0.15, t + 2 * st + 6 * st, pan=-0.3)
    if power_t < dur:                                            # swell into the power-on drop
        place(drums, hiss_swell(rng, 4 * bar) * 1.8, power_t - 4 * bar)
    _voices(vox, dur, secs, sec_at, bar, st, root_at, 2, 12, rng)
    level = np.ones(n)
    for s0, s1, name in secs:
        level[int(s0 * SR):int(s1 * SR)] = {"factory": 0.75, "break": 0.6}.get(name, 1.0)
    tt = _t(n)
    pump = 1 - 0.55 * np.exp(-((tt % beat) / beat) * beat / 0.11)
    music = (bass * 1.0 + acid * 0.55 + keys * 0.9) * (pump * level)[:, None]
    mix = music + drums * 0.8 + vox * pump[:, None] * 2.6
    return mix


def _winter(dur, rng, bpm, cues):
    beat = 60.0 / bpm
    bar, st = 4 * beat, beat / 4
    n = int(dur * SR)
    secs = _sections(dur, cues, bar)
    sec_at = lambda t: next((s for s in secs if s[0] <= t < s[1]), secs[-1])
    power_t = next((s[0] for s in secs if s[2] == "power"), dur)
    CH = [(47, [59, 62, 66]), (43, [59, 62, 67]), (38, [57, 62, 66]), (45, [57, 61, 64])]   # Bm G D A
    ch_at = lambda t: CH[int(t / bar) % 4]
    ARP = [0, 1, 2, 3, 2, 1, 0, 2]                           # chord tone index (3 = top note an octave up)
    drums, bass, arp, pads, vox = (np.zeros((n, 2)) for _ in range(5))
    K, S = kick_round(), snare_soft(rng)
    SH = shaker(rng)
    nbeats = int(dur / beat) + 1
    bell_cache, pad_cache = {}, {}
    for b in range(nbeats):
        t = b * beat
        s0, s1, name = sec_at(t)
        in_bar = b % 4
        bar_i = int(t / bar)
        root, chord = ch_at(t)
        full = name not in ("factory", "break")
        if in_bar == 0:
            if root not in pad_cache:
                pad_cache[root] = pad(chord, bar * 0.98)
            place(pads, pad_cache[root] * (1.3 if name == "break" else 1.0), t, pan=0.0)
        if name == "break":
            if in_bar == 0:
                place(drums, K * 0.35, t)
            if s1 - t <= 2 * bar and s1 - t > 2 * bar - beat:
                place(drums, hiss_swell(rng, 2 * bar) * 1.2, t)
            continue
        quiet = name == "factory" and t < 16 * bar
        # electro beat: kick on 1, the and of 2, and 3; snare on 2 and 4
        if in_bar in (0, 2):
            place(drums, K * (0.75 if name == "factory" else 1.0), t)
        if in_bar == 1 and full:
            place(drums, K * 0.7, t + 2 * st)
        if in_bar in (1, 3) and not quiet:
            place(drums, S * (0.7 if name == "factory" else 1.0), t, pan=0.05)
        if not quiet:
            for q in range(4):
                place(drums, SH * (1.0 if q % 2 else 0.55), t + q * st, pan=0.3 if q % 2 else -0.3)
        # plucked bass on the 8ths (root, root, octave)
        if not quiet:
            for q, m in ((0, root), (2, root), ):
                place(bass, pluck_bass(m, st * 1.6), t + q * st)
            if in_bar == 3:
                place(bass, pluck_bass(root + 12, st), t + 3 * st)
        # the bell arpeggio (16ths in the events, 8ths in the factory), with a ping-pong echo
        if not quiet:
            tones = chord + [chord[0] + 12]
            for q in range(4 if full else 2):
                step = (in_bar * 4 + q * (1 if full else 2)) % 8
                m = tones[ARP[step]] + 12
                m = min(m, 86)
                if m not in bell_cache:
                    bell_cache[m] = bell_pluck(m, st)
                at = t + q * st * (1 if full else 2)
                place(arp, bell_cache[m] * (1.0 if full else 0.7), at, pan=-0.2)
                place(arp, bell_cache[m] * 0.32, at + 3 * st, pan=0.45)
                place(arp, bell_cache[m] * 0.12, at + 6 * st, pan=-0.45)
    if power_t < dur:
        place(drums, hiss_swell(rng, 4 * bar) * 1.4, power_t - 4 * bar)
    _voices(vox, dur, secs, sec_at, bar, st, lambda t: ch_at(t)[0] + 12, 4, 0, rng)
    level = np.ones(n)
    for s0, s1, name in secs:
        level[int(s0 * SR):int(s1 * SR)] = {"factory": 0.8, "break": 0.65}.get(name, 1.0)
    tt = _t(n)
    pump = 1 - 0.35 * np.exp(-((tt % (2 * beat)) / beat) * beat / 0.14)
    music = (bass * 1.0 + arp * 0.9 + pads * 1.0) * (pump * level)[:, None]
    return music + drums * 0.85 + vox * pump[:, None] * 2.2


# ---------- finale instruments ----------

def brass(m, dur):
    """A warm synth-brass note: two detuned saws, the filter swells open after the attack (a slow 'bwah'),
    rolled off well below the harsh band."""
    n = int((dur + 0.25) * SR)
    t = _t(n)
    f = midi(m)
    tone = _saw(f * 2 ** (-0.06 / 12), n) + _saw(f * 2 ** (0.06 / 12), n)
    out = np.zeros(n)
    blocks = 8
    for b in range(blocks):
        i0, i1 = n * b // blocks, n * (b + 1) // blocks
        fc = 700 + 1300 * min(1.0, (i0 / SR) / 0.12)
        out[i0:i1] = _lp(tone, fc)[i0:i1]
    env = np.minimum(1, t / 0.035) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.09))
    return np.tanh(out * env * 1.2) * 0.32


def clap(rng):
    """A soft hand clap: three quick noise bursts, band-limited and low-passed."""
    n = int(0.22 * SR)
    t = _t(n)
    env = np.zeros(n)
    for d in (0.0, 0.011, 0.023):
        env += (t >= d) * np.exp(-np.maximum(0, t - d) / (0.012 if d < 0.02 else 0.07))
    return _lp(_bp(rng.normal(0, 1, n) * env, 700, 2600), 2600) * 0.45


def octave_bass(m, dur):
    n = int((dur + 0.04) * SR)
    t = _t(n)
    f = midi(m)
    tone = _saw(f, n) * 0.6 + np.sin(2 * np.pi * f * t)
    out = _lp(tone, 1000) * np.exp(-t / 0.05) + _lp(tone, 520) * (1 - np.exp(-t / 0.05))   # a brighter attack
    env = np.minimum(1, t / 0.004) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.02))
    return np.tanh(out * env * 1.5) * 0.62


def _finale(dur, rng, bpm, cues):
    """The season finale: a stadium anthem in D major (D - A - Bm - G), four-on-the-floor with soft claps,
    a driving octave bass, wide warm chords, a brass hook over the events and a counter-line of bells in
    the factory; the 100 m and the podium get the full arrangement and claps on every beat."""
    beat = 60.0 / bpm
    bar, st = 4 * beat, beat / 4
    n = int(dur * SR)
    secs = _sections(dur, cues, bar)
    sec_at = lambda t: next((s for s in secs if s[0] <= t < s[1]), secs[-1])
    power_t = next((s[0] for s in secs if s[2] == "power"), dur)
    CH = [(38, [62, 66, 69]), (45, [61, 64, 69]), (47, [62, 66, 71]), (43, [62, 67, 71])]   # D A Bm G
    ch_at = lambda t: CH[int(t / bar) % 4]
    # the hook: two bars of quarter / eighth notes (step in 16ths, MIDI, length in 16ths), answered on the
    # next two bars a step lower
    HOOK = [(0, 78, 3), (4, 81, 2), (6, 83, 2), (8, 81, 4), (12, 78, 2), (14, 76, 2),
            (16, 74, 4), (20, 76, 2), (22, 78, 6), (28, 76, 4)]
    ANSWER = [(0, 76, 3), (4, 78, 2), (6, 81, 2), (8, 78, 4), (12, 76, 2), (14, 74, 2),
              (16, 71, 4), (20, 74, 2), (22, 74, 8)]
    drums, bass, chords, lead, bells, vox = (np.zeros((n, 2)) for _ in range(6))
    K, C = kick_round(), clap(rng)
    H = hat(rng)
    nbeats = int(dur / beat) + 1
    pad_cache, bass_cache, brass_cache, bell_cache = {}, {}, {}, {}
    for b in range(nbeats):
        t = b * beat
        s0, s1, name = sec_at(t)
        in_bar = b % 4
        bar_i = int(t / bar)
        root, chord = ch_at(t)
        full = name not in ("factory", "break")
        big = name in ("sprint", "podium")
        if in_bar == 0:
            key = (root, name == "break")
            if key not in pad_cache:
                pad_cache[key] = pad(chord + [chord[0] - 12], bar * 0.98)
            place(chords, pad_cache[key] * (1.4 if name == "break" else (1.15 if big else 1.0)), t)
        if name == "break":
            if in_bar == 0:
                place(drums, K * 0.35, t)
            if s1 - t <= 2 * bar and s1 - t > 2 * bar - beat:
                place(drums, hiss_swell(rng, 2 * bar) * 1.3, t)
            continue
        quiet = name == "factory" and t < 16 * bar
        place(drums, K * (0.7 if name == "factory" else 1.0), t)
        if (in_bar in (1, 3) and not quiet) or (big and in_bar in (0, 2)):
            place(drums, C * (0.65 if name == "factory" else (1.0 if in_bar in (1, 3) else 0.6)), t, pan=0.1)
        if not quiet:
            for q in (1, 3):
                place(drums, H * (0.55 if q == 3 else 0.35) * (1.2 if full else 0.8), t + q * st, pan=0.25)
        # driving octave bass on the 8ths
        if not quiet:
            for q in range(0, 4, 2):
                m = root + (12 if q == 2 else 0)
                if m not in bass_cache:
                    bass_cache[m] = octave_bass(m, st * 1.7)
                place(bass, bass_cache[m] * (0.75 if name == "factory" else 1.0), t + q * st)
        # bells in the factory (a gentle counter-line on the chord tones)
        if name == "factory" and not quiet and in_bar in (0, 2):
            m = chord[(bar_i + in_bar // 2) % 3] + 12
            if m not in bell_cache:
                bell_cache[m] = bell_pluck(m, 2 * st)
            place(bells, bell_cache[m], t, pan=-0.2)
            place(bells, bell_cache[m] * 0.3, t + 3 * st, pan=0.35)
        # the brass hook over the events: phrase A on bars 0-1, the answer on bars 2-3 of every 4
        if full and in_bar == 0 and bar_i % 2 == 0:
            ph = HOOK if bar_i % 4 == 0 else ANSWER
            if (bar_i // 4) % 2 == 0 or big:
                for step, m, ln in ph:
                    key = (m, ln)
                    if key not in brass_cache:
                        brass_cache[key] = brass(m, ln * st * 0.92)
                    place(lead, brass_cache[key] * (1.15 if big else 1.0), t + step * st, pan=0.05)
    if power_t < dur:
        place(drums, hiss_swell(rng, 4 * bar) * 1.5, power_t - 4 * bar)
    _voices(vox, dur, secs, sec_at, bar, st, lambda t: ch_at(t)[0] + 12, 4, 0, rng)
    level = np.ones(n)
    for s0, s1, name in secs:
        level[int(s0 * SR):int(s1 * SR)] = {"factory": 0.78, "break": 0.65}.get(name, 1.0)
    tt = _t(n)
    pump = 1 - 0.4 * np.exp(-((tt % beat) / beat) * beat / 0.12)
    music = (bass * 1.0 + chords * 1.1 + lead * 0.75 + bells * 0.8) * (pump * level)[:, None]
    return music + drums * 0.85 + vox * pump[:, None] * 2.0


def robot_season_bed(dur, rng, bpm=None, cues=None, gain=1.0, style="industrial", **_):
    bpm = bpm or STYLES[style]["bpm"]
    mix = {"industrial": _industrial, "winter": _winter, "finale": _finale}[style](dur, rng, bpm, cues)
    mix = sosfilt(butter(2, 30, "high", fs=SR, output="sos"), mix, axis=0)
    peak = np.max(np.abs(mix)) + 1e-9
    return mix / peak * 0.9 * gain, None
