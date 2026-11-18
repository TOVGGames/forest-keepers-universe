"""Sound effects for Curiosity Unknown (docs/engines/facts_cartoons.md §4-5): ElevenLabs sound generation for the sounds a
synth can't fake (thunder, a rocket), cached by prompt in the main checkout like narration takes; small cartoon sounds
(pops, the glow chord) come from audio/synth through engine.audio.EventTrack.

    .venv\\Scripts\\python.exe -m families.curiosity.sfx          # generate (or reuse) the episode-1 library, print costs
"""
import hashlib
import json
import os
import subprocess

import numpy as np
import requests

from engine.elevenlabs import API, api_key, credits, shared_root

CACHE = os.path.join(shared_root(), "narration", "cache", "sfx")
SR = 44100

LIBRARY = {  # name: (prompt, seconds)
    "thunder_close": ("a single close lightning strike: sharp electric crack, then deep rolling thunder fading out, "
                      "no rain, no music", 4.5),
    "thunder_far": ("distant soft rolling thunder rumble, gentle, no rain, no music", 4.0),
    "rocket_launch": ("small model rocket launching with a quick fizzing whoosh going up and away, no music", 2.5),
    # episode 2, ocean gold: soft and warm, nothing bright (warm() cuts the treble; coins keep a little more to read
    # as coins, still under the harsh 1-5 kHz band's peak)
    "waves": ("gentle calm sea waves lapping against a small wooden rowboat, soft and relaxing, no seagulls, no music", 4.0),
    "splash": ("a soft single splash of a small box dropped into calm sea water, no music", 1.5),
    "coins": ("a few gold coins gently clinking together in a hand, soft and warm, no music", 1.5),
    "bubbles": ("soft underwater bubbles rising, muffled and calm, no music", 3.0),
    "pump": ("a big water pump starting up and running with a low steady hum and rushing water, no music", 3.0),
    "horn": ("a distant deep ship horn, one long low warm blast, no music", 3.0),
    # dig to the center: low and calm, nothing clanky
    "wind": ("soft cold arctic wind blowing over snow, calm and quiet, no music", 3.0),
    "drill": ("a big drilling rig motor starting up and humming steadily, low and smooth, no clanking, no music", 3.0),
    "rumble": ("a soft low distant earthquake rumble, gentle and short, nothing breaking, no music", 3.0),
    "lift": ("an old mine lift cage gliding fast down a deep shaft, a smooth steady rush of air, no music", 3.0),
    # the end card (every episode, owner 2026-11-03: "the ending, it's so abrupt"): a short warm sign-off, not a music bed
    "outro_sting": ("a short gentle closing jingle for a calm cartoon: three soft warm marimba notes going up, then one "
                    "low plucked upright bass note, mellow, no vocals, no drums", 3.0),
}
TOP = {"coins": 1800, "splash": 700, "waves": 650}   # warm() cut per sound (default 1,000 Hz); judged on each one's loudest 0.3 s


def generate(prompt, seconds, influence=0.5):
    """-> mp3 path (cached by prompt + length)."""
    key = hashlib.sha256(json.dumps([prompt, seconds, influence]).encode()).hexdigest()[:20]
    path = os.path.join(CACHE, key + ".mp3")
    if os.path.exists(path):
        return path
    os.makedirs(CACHE, exist_ok=True)
    r = requests.post(f"{API}/sound-generation", headers={"xi-api-key": api_key()},
                      json={"text": prompt, "duration_seconds": seconds, "prompt_influence": influence}, timeout=120)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    with open(path[:-4] + ".json", "w", encoding="utf-8") as f:
        json.dump({"prompt": prompt, "seconds": seconds, "influence": influence}, f)
    return path


def load(path, sr=SR):
    """Decode any audio file to a mono float array at `sr` (ffmpeg)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def synth_thunder(seconds=4.0, close=True, seed=1):
    """Fallback thunder: a crack, then several rolling swells (thunder arrives in rolls from different parts of the
    channel). Owner 2026-11-02: he never heard the first version, which sat almost entirely below 160 Hz, where laptop
    and phone speakers play next to nothing. So the body now lives at 70-450 Hz with a soft saturation (its harmonics
    let small speakers carry the rumble), still kept out of the harsh 1-5 kHz band (owner hears that as "AM radio")."""
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    body = sosfilt(butter(2, [70, 450], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
    body /= np.abs(body).max() + 1e-9
    rolls = ((0.0, 1.0, 0.6), (0.32, 0.8, 0.7), (0.85, 0.65, 0.9), (1.7, 0.4, 1.1)) if close else \
        ((0.0, 0.6, 0.8), (0.55, 1.0, 1.0), (1.4, 0.55, 1.1))
    att = 0.015 if close else 0.25
    env = np.zeros(n)
    for t0, amp, dec in rolls:
        d = np.clip(t - t0, 0, None)
        env += np.where(t >= t0, amp * (1 - np.exp(-d / att)) * np.exp(-d / dec), 0)
    out = np.tanh(2.2 * body * env) / np.tanh(2.2)
    if close:                                                 # the crack: short, warm, a few crackles in the first 0.3 s
        crack = sosfilt(butter(2, [180, 1100], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
        sparks = np.zeros(n)
        for at in rng.uniform(0, 0.3, 14):
            sparks[int(at * SR)] = rng.uniform(0.5, 1.0)
        sparks = sosfilt(butter(2, [250, 1200], btype="band", fs=SR, output="sos"), sparks)
        crack = crack / (np.abs(crack).max() + 1e-9) * np.exp(-t / 0.07) + sparks / (np.abs(sparks).max() + 1e-9) * 0.5
        out += 0.8 * crack
    out = sosfilt(butter(4, 1500, fs=SR, output="sos"), out)  # nothing up in the harsh band
    out *= np.clip((seconds - t) / 0.4, 0, 1)                 # fade at the end of the clip
    return (out / (np.abs(out).max() + 1e-9)).astype(np.float32)


def warm(x, top=1000, order=4):
    """Owner's ear (2026-11-02): ElevenLabs thunder came back either almost all below 150 Hz (inaudible on laptop and
    phone speakers: "I never heard it") or with a bright crack in the harsh 1-5 kHz band. So: a cut above `top`, plus
    soft-saturated harmonics of the low rumble (150-500 Hz) that let small speakers carry it. A gentle 2,200 Hz cut
    (CU0003) left the crack's first 0.3 s at 70% 1-5 kHz, at speech loudness; 1,000 Hz / 4th order takes it to 18%
    (~10 dB less treble) with the rumble just as loud. Judge the crack window, not the whole clip's average."""
    from scipy.signal import butter, sosfilt
    x = x / (np.abs(x).max() + 1e-9)
    low = sosfilt(butter(2, 150, fs=SR, output="sos"), x)
    harm = np.tanh(4 * low / (np.abs(low).max() + 1e-9))
    harm = sosfilt(butter(2, [150, 500], btype="band", fs=SR, output="sos"), harm)
    y = sosfilt(butter(order, top, fs=SR, output="sos"), x) + 0.8 * harm / (np.abs(harm).max() + 1e-9) * np.abs(low).max()
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


SYNTH = {"thunder_close": lambda: synth_thunder(4.5, True), "thunder_far": lambda: synth_thunder(4.0, False, 2)}


def library():
    """{name: mono float array}: ElevenLabs sounds where the key allows sound generation, else the synth fallbacks
    (the key had no sound_generation permission on 2026-11-02; the owner can add it in ElevenLabs)."""
    out = {}
    for name, (prompt, sec) in LIBRARY.items():
        try:
            out[name] = warm(load(generate(prompt, sec)), TOP.get(name, 1000))
        except requests.HTTPError as e:
            if e.response is None or e.response.status_code != 401:
                raise
            if name in SYNTH:                                  # no stand-in (rocket): that sound is left out
                out[name] = SYNTH[name]()
    return out


if __name__ == "__main__":
    used0, limit = credits()
    for name, (prompt, sec) in LIBRARY.items():
        print(name, generate(prompt, sec))
    used1, _ = credits()
    print(f"credits used: {used1 - used0:,}; left {limit - used1:,} of {limit:,}")
