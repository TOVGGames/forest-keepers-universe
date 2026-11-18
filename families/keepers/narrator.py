"""The Forest Keepers narrator (owner, 2026-11-01): an elderly grandmother voice, a gentle sage who now and then gives
hints of what the Keepers are up to, like Puffin Rock's narrator. First used in "Who's Awake Tonight?"
(docs/engines/forest_keepers_night_animals.md). The voice is narration/keepers_voice.yaml (Johanna, owner's pick);
every line goes through engine.narration (ElevenLabs, cached by text + voice, so re-renders reuse the takes).

An act asks for a line with `say(act, at, text)` (act time); the scene collects them in `scene.narration` and, when a
params file has `narrator: true`, masters its own soundtrack (`soundtrack`): the music, the Keepers' noises and the
SFX sit at the usual Keepers loudness and ease down 6 dB only while she speaks; her voice is just above them.
Every narrated upload gets the AI-voice disclosure (AI_LINE).
"""
import os
import tempfile

import numpy as np
import yaml

from engine.log import ROOT
from engine.narration import narrate

VOICE_FILE = os.path.join(ROOT, "narration", "keepers_voice.yaml")
AI_LINE = "Narration voice is AI-generated; script written and fact-checked by a person."


def voice():
    with open(VOICE_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def take(text):
    """-> narrate() dict (audio, duration, words) for one line, from the cache when it was voiced before."""
    return narrate(text, voice())


def say(act, at, text):
    """Schedule a narrator line at act time `at`; -> its length in seconds (the act times its beats around it)."""
    n = take(text)
    act.s.__dict__.setdefault("narration", []).append((act.real(at), n))
    act.__dict__.setdefault("lines", []).append((at, at + n["duration"], text))
    return n["duration"]


def speaking(act, t, pad=0.6):
    """Is the narrator talking around act time t? (the Keepers keep quiet then)"""
    return any(a - pad <= t <= b + pad for a, b, _ in getattr(act, "lines", []))


def _lufs(x, tmp, name):
    """Integrated loudness of a float buffer (mono or stereo)."""
    from scipy.io import wavfile
    from audio.synth import SR
    from engine.video import measure_lufs
    path = os.path.join(tmp, name + ".wav")
    wavfile.write(path, SR, np.asarray(x, np.float32))
    return measure_lufs(path)[0]


def soundtrack(scene, track, duration, music_lufs=-15.0, voice_over_db=1.0, duck_db=6.0):
    """Music + SFX + the Keepers at the usual Keepers loudness, the narrator just above it, the music easing down
    `duck_db` only while she speaks (owner after FK0008's first render: the music was far too quiet between her
    lines - with her at a good volume the rest was lost, with the rest right she was too loud). -> (wav, stats)."""
    from families.space_explained import music as SM
    a = scene.p.get("audio", {})
    m = track._render(duration, bed=a.get("bed", scene.bed), events_gain=a.get("events_gain", scene.events_gain),
                      reverb=a.get("reverb", scene.reverb), fade_out=0.0, _raw=True).astype(np.float32)
    n = m.shape[0]
    tmp = tempfile.mkdtemp(prefix="fk_narr_")
    v = np.zeros(n, np.float32)
    words, lines = [], []
    for k, (t0, nd) in enumerate(sorted(scene.narration, key=lambda e: e[0])):
        os.makedirs(os.path.join(tmp, str(k)), exist_ok=True)
        v += SM.load_voice(nd["audio"], n, t0, os.path.join(tmp, str(k)))
        words += [dict(w, start=w["start"] + t0, end=w["end"] + t0) for w in nd["words"]]
        lines.append({"t": round(t0, 2), "duration": round(nd["duration"], 2), "text": nd["text"],
                      "sha256": nd["sha256"]})
    mask = SM.speech_mask(words, n)
    # the music on its own at the usual level; the voice (measured over her own words) just above it
    gm = 10 ** ((music_lufs - _lufs(m, tmp, "music")) / 20)
    speech = v[mask > 0.5]
    gv = 10 ** ((music_lufs + voice_over_db - _lufs(speech, tmp, "voice")) / 20) if speech.size else 1.0
    duck = (10 ** (-duck_db * mask / 20)).astype(np.float32)
    mix = m * np.float32(gm) * duck[:, None] + (v * np.float32(gv))[:, None]
    lufs = _lufs(mix, tmp, "mix")
    path, stats = SM.master(mix, os.path.join(tmp, "narrated_mix.wav"), lufs)     # keep this balance; limit peaks
    vs = voice()
    stats.update(band_energy=SM.band_energy(mix), music_lufs=music_lufs, voice_over_db=voice_over_db,
                 duck_db=duck_db, narration={"voice_id": vs["voice_id"], "voice_name": vs.get("name"),
                                             "model_id": vs["model_id"], "lines": lines},
                 disclosure=AI_LINE)
    return path, stats
