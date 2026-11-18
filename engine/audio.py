"""Soundtrack built from on-screen events, layered over a bed from audio/synth.py.

Scenes call `track.hit(t, ...)` whenever something visible happens (a bounce,
a collision, a pendulum crossing). After the video is rendered, `render()` turns
the event list into audio with the same instruments as the approved samples.
"""
import os
import subprocess
import tempfile

import numpy as np
from scipy.io import wavfile

from audio import synth
from audio import pendulum_tones
from audio import robot_disco
from audio import robot_techno
from audio.synth import SR, midi

from .core import make_rng

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "audio", "samples")

BEDS = {
    "ambient": synth.ambient_bed,
    "race": synth.race_bed,
    "music_box": synth.music_box_bed,
    "chords": synth.chord_bed,
    "industrial": synth.industrial_bed,
    "robot_disco": robot_disco.robot_disco_bed,
    "robot_season": robot_techno.robot_season_bed,
    "keepers": synth.keepers_bed,
    "keepers_song": synth.keepers_song_bed,
    "sand": synth.sand_bed,
    "table": synth.table_bed,
    "cozy": synth.cozy_bed,
    "sunny": synth.sunny_bed,
}

# unpitched effects with a length, queued with EventTrack.fx(t, name, dur)
NOISE_FX = {
    "whoosh": synth.whoosh,
    "sizzle": synth.sizzle,
    "crackle": synth.crackle,
    "motor": synth.motor,
    "hiss": synth.hiss,
    "slide": synth.slide,
    "weld": synth.weld,
    "servo": synth.servo,
    "robot_boot": synth.robot_boot,
    "siren": synth.siren,
    "spray": synth.spray,
    "saw": synth.saw,
    "creak": synth.creak,
    "rustle": synth.rustle,
    "leaf_settle": synth.leaf_settle,
    "splash": synth.splash,
    "bubble": synth.bubble,
    "gurgle": synth.gurgle,
    "rush": synth.rush,
    "air_blow": synth.air_blow,
    "clap": synth.clap,
    "sand_pour": synth.sand_pour,
    "sand_patter": synth.sand_patter,
    "sand_slice": synth.sand_slice,
    "sand_thump": synth.sand_thump,
    "sand_scrape": synth.sand_scrape,
    "paint_pour": synth.paint_pour,
    "paint_spread": synth.paint_spread,
    "paint_wipe": synth.paint_wipe,
    "marble_roll": synth.marble_roll,
    "lamp_click": synth.lamp_click,
}


def _instrument(name, f):
    if name == "plink":
        return synth.plink(f, 0.8)
    if name == "music_box":
        return synth.bell(f, dur=2.5, index=1.2, ratio=4.0)
    if name == "soft_bell":
        return synth.bell(f, dur=4.0, index=1.5)
    if name == "warm_bell":   # Sandglass: soft felt music box, no FM shimmer
        return synth.warm_bell(f, dur=4.0)
    if name == "deep_bell":   # Deep Sky: slow singing-bowl tone
        return synth.deep_bell(f)
    if name == "sky_swell":   # Deep Sky (SK0002 on): a tone that breathes in and out, no attack
        return synth.sky_swell(f)
    if name == "sky_glow":    # Deep Sky Shorts: a planet joining the line-up - soft onset, slow fade
        return synth.sky_glow(f)
    if name == "chime":
        return synth.bell(f, dur=3.0, index=2.0, ratio=2.0)
    if name == "pluck":       # short, rounder - dense marble contacts
        tt = synth.t_axis(0.35)
        sig = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 14) + 0.2 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 30)
        sig[:60] *= np.linspace(0, 1, 60)
        return sig
    if name == "kick":
        return synth.kick()
    if name == "clack":
        return synth.clack(f)
    if name == "wood_clack":  # Chain Reaction: domino clacks tuned to the melody
        return synth.wood_clack(f)
    if name == "wood_thud":
        return synth.wood_thud(f)
    if name == "soft_vibes":  # Tiny World: mellow vibraphone for happy moments
        return synth.soft_vibes(f)
    if name == "hammer_tok":  # Tiny World: little hammer taps tuned to the tune
        return synth.hammer_tok(f)
    if name == "gear_tick":   # contraption: brass ratchet tick
        return synth.gear_tick(f)
    if name == "brass_bell":
        return synth.brass_bell(f)
    if name == "clunk":
        return synth.clunk(f)
    if name == "thud":
        return synth.thud(f)
    if name == "boing":
        return synth.boing(f)
    if name == "quack":       # Tiny Tappers: Biscuit the duckling
        return synth.quack(f)
    if name.startswith("duckling"):   # duckling / duckling_b / duckling_c: Biscuit from Day 4 on
        return synth.duckling(f, name.partition("_")[2] or "a")
    if name == "cluck":       # Tiny Tappers Day 5: the hens
        return synth.cluck(f)
    if name == "bloop":
        return synth.bloop(f)
    if name in pendulum_tones.INSTRUMENTS:     # marimba, kalimba, harp, glass (pendulum twists)
        return pendulum_tones.INSTRUMENTS[name](f)
    if name.startswith("voice_"):              # voice_<contour> or voice_<contour>@<formant scale in %>
        contour, _, fs = name[6:].partition("@")
        return synth.voice(f, contour, fs=int(fs) / 100 if fs else 1.0)
    raise KeyError(name)


# Safe pitch range for pitched events: MIDI 36-96 (C2-C7, 65 Hz-2.1 kHz fundamental). The bell
# and plink instruments add overtones up to ~9x the fundamental, which must stay below the
# Nyquist limit (22 kHz) or they alias into harsh, off-key, noise-like clangs - the
# "choked wind chime underwater" sound in BL0007 (lava_lamp pitch counter ran away).
NOTE_MIN, NOTE_MAX = 36, 96


class EventTrack:
    def __init__(self, seed):
        self.seed = seed
        self.events = []      # (t, inst, midi_note, vel, pan)
        self.scale = synth.AMBIENT_SCALE
        self.folded = []      # (t, inst, requested_note) for notes pulled back into range

    def hit(self, t, inst="plink", note=72, vel=0.7, pan=0.0):
        n = float(note)
        if not NOTE_MIN <= n <= NOTE_MAX:
            # out of range is always a bug in the caller: keep the pitch class, fold by octaves,
            # and record it so the render reports it
            self.folded.append((float(t), inst, n))
            while n > NOTE_MAX:
                n -= 12
            while n < NOTE_MIN:
                n += 12
        self.events.append((float(t), inst, n, float(np.clip(vel, 0, 1)), float(np.clip(pan, -1, 1))))

    def whoosh(self, t, vel=0.6, pan=0.0, dur=0.6):
        self.fx(t, "whoosh", dur, vel, pan)

    def fx(self, t, name, dur, vel=0.6, pan=0.0):
        """Unpitched effect of a given length (see NOISE_FX)."""
        self.events.append((float(t), f"{name}:{dur:.3f}", 0.0, float(np.clip(vel, 0, 1)), float(np.clip(pan, -1, 1))))

    def note_in_scale(self, i, octave_shift=0):
        """i-th note walking up the current bed's scale (wraps by octave)."""
        n = len(self.scale)
        return self.scale[i % n] + 12 * (i // n + octave_shift)

    # ----- rendering -----

    def _thin(self, min_gap=0.022, window=0.12, max_in_window=6):
        """Drop near-duplicate hits and tame very dense passages."""
        ev = sorted(self.events)
        out, last = [], {}
        for e in ev:
            t, inst, note, vel, pan = e
            key = (inst, round(note))
            if t - last.get(key, -1) < min_gap:
                continue
            last[key] = t
            out.append(e)
        times = np.array([e[0] for e in out])
        kept = []
        for i, e in enumerate(out):
            lo = np.searchsorted(times, e[0] - window)
            hi = np.searchsorted(times, e[0] + window)
            dens = hi - lo
            if dens > max_in_window * 2 and (i % 2):
                continue
            g = 1.0 / np.sqrt(max(1.0, dens / max_in_window))
            kept.append((e[0], e[1], e[2], e[3] * g, e[4]))
        return kept

    def _bed(self, spec, dur, rng):
        if not spec:
            return np.zeros((int(dur * SR), 2))
        gain = spec.get("gain", 1.0)
        if spec["type"] == "sample":
            buf = load_sample(spec["name"], dur, loop=spec.get("loop", True))
        else:
            kw = {k: v for k, v in spec.items() if k not in ("type", "name", "gain", "reverb")}
            buf, _ = BEDS[spec["name"]](dur, rng, **kw)
            rv = spec.get("reverb", {"decay": 4.0, "wet": 0.4, "tone": 4500})
            buf = synth.reverb(buf, rng=rng, **rv)
        return buf * gain

    def render(self, duration, bed=None, events_gain=1.0, reverb=None, fade_out=2.0, path=None, loop=False,
               master="tanh"):
        """loop=True: render a few seconds past the end and wrap that tail onto the start, with no
        fades, so the file loops seamlessly (for multi-hour uploads made with ffmpeg -stream_loop).
        master="clean": normalise the peak with headroom and skip the tanh soft-clip (Sandglass: soft
        noise textures, where saturation adds harshness)."""
        if loop:
            tail = 8.0
            full = self._render(duration + tail, bed, events_gain, reverb, fade_out=0, _raw=True)
            n, m = int(duration * SR), int(tail * SR)
            full[:m] += full[n:n + m]
            return self._write(full[:n], path)
        return self._render(duration, bed, events_gain, reverb, fade_out, path, master=master)

    def _write(self, mix, path):
        mix = mix / (np.max(np.abs(mix)) + 1e-9) * 1.1
        mix = np.tanh(mix) * 0.89
        if path is None:
            path = tempfile.mktemp(suffix=".wav")
        wavfile.write(path, SR, (mix * 32767).astype(np.int16))
        return path

    def _render(self, duration, bed=None, events_gain=1.0, reverb=None, fade_out=2.0, path=None, _raw=False,
                master="tanh"):
        rng = make_rng(self.seed, "audio")
        n = int(duration * SR)
        ev_buf = np.zeros((n, 2))
        cache = {}
        for t, inst, note, vel, pan in self._thin():
            if ":" in inst:
                name, dur = inst.split(":")
                sig = NOISE_FX[name](float(dur), rng=rng)
            else:
                key = (inst, round(note, 2))
                if key not in cache:
                    cache[key] = _instrument(inst, midi(note))
                sig = cache[key]
            synth.place(ev_buf, sig * vel * 0.3, t, pan=pan)
        rv = reverb or {"decay": 2.5, "wet": 0.3, "tone": 6000}
        ev_buf = synth.reverb(ev_buf, rng=rng, **rv)
        mix = ev_buf * events_gain + self._bed(bed, duration, rng)
        if _raw:
            return mix
        if master == "clean":
            mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.7
        else:
            mix = mix / (np.max(np.abs(mix)) + 1e-9) * 1.1
            mix = np.tanh(mix) * 0.89
        fi = int(0.05 * SR)
        mix[:fi] *= np.linspace(0, 1, fi)[:, None]
        fo = int(fade_out * SR)
        if fo:
            mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
        if path is None:
            path = tempfile.mktemp(suffix=".wav")
        wavfile.write(path, SR, (mix * 32767).astype(np.int16))
        return path


def load_sample(name, dur, loop=True, xfade=3.0):
    """Decode an approved sample (audio/samples/<name>.mp3) to `dur` seconds, crossfade-looping."""
    path = os.path.join(SAMPLES_DIR, f"{name}.mp3")
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "2",
                          "-ar", str(SR), "-"], check=True, capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    n = int(dur * SR)
    if len(x) >= n or not loop:
        out = np.zeros((n, 2))
        out[:min(n, len(x))] = x[:n]
        return out
    # trim the sample's own fades, then overlap-add with crossfades
    body = x[int(1.5 * SR):-int(3.0 * SR)]
    xf = int(xfade * SR)
    out = np.zeros((n + len(body), 2))
    fade = np.linspace(0, 1, xf)[:, None]
    out[:len(x)] = x
    pos = len(x) - int(3.0 * SR) - xf
    while pos < n:
        seg = body.copy()
        seg[:xf] *= fade
        seg[-xf:] *= fade[::-1]
        out[pos:pos + len(seg)] += seg[:len(out) - pos]
        pos += len(seg) - xf
    return out[:n]
