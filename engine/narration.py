"""Narration: approved script text -> ElevenLabs speech + word timings, cached by hash (ported from
science-animations; docs/engines/space_explained.md §5).

Text may carry cue marks like "{ca_binds}Calcium binds"; they are stripped before speech and resolve to
the start time of the next word, so scenes wait for words, not hand-typed seconds. Pronunciation
respellings (narration/pronunciation.yaml, `apply:` only) change what is sent to ElevenLabs; timings
and captions map back to the real spelling.

    .venv\\Scripts\\python.exe -m engine.narration --say "text" --voice <voice_id>   # quick take -> path
"""
import argparse
import base64
import hashlib
import json
import os
import re

import requests
import yaml

from .elevenlabs import API, api_key, shared_root
from .log import ROOT

CACHE = os.path.join(shared_root(), "narration", "cache")   # main checkout: takes survive worktrees (git-ignored)
VOICE_FILE = os.path.join(ROOT, "narration", "voice.yaml")
PRON_FILE = os.path.join(ROOT, "narration", "pronunciation.yaml")
CUE = re.compile(r"\{(\w+)\}")
FORMATS = ("mp3_44100_192", "mp3_44100_128")


def load_voice(path=VOICE_FILE):
    """The voice config; env NARRATION_VOICE_ID swaps only the voice (for auditions - see engine.render --voice)."""
    with open(path, encoding="utf-8") as f:
        v = yaml.safe_load(f)
    if os.environ.get("NARRATION_VOICE_ID"):
        v.update(voice_id=os.environ["NARRATION_VOICE_ID"], name=os.environ.get("NARRATION_VOICE_NAME", "audition"))
    return v


def pronunciations():
    with open(PRON_FILE, encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("apply") or {}


def strip_cues(text):
    """-> (clean text, {cue: char index in clean text})."""
    cues, out, pos = {}, [], 0
    for m in CUE.finditer(text):
        out.append(text[pos:m.start()])
        cues[m.group(1)] = sum(map(len, out))
        pos = m.end()
    out.append(text[pos:])
    return "".join(out), cues


def respell(text, table):
    """Apply pronunciation respellings. -> (spoken text, orig_index[i] for each spoken char i)."""
    if not table:
        return text, list(range(len(text)))
    pat = re.compile(r"(?<![\w-])(" + "|".join(re.escape(k) for k in sorted(table, key=len, reverse=True)) + r")(?![\w-])")
    spoken, idx, pos = [], [], 0
    for m in pat.finditer(text):
        spoken.append(text[pos:m.start()]); idx.extend(range(pos, m.start()))
        rep = table[m.group(1)]
        spoken.append(rep); idx.extend([m.start()] * len(rep))
        pos = m.end()
    spoken.append(text[pos:]); idx.extend(range(pos, len(text)))
    return "".join(spoken), idx


def words(text, starts, ends, orig_index):
    """Word timings in the original text from character alignment of the spoken text."""
    spans = [(m.start(), m.end(), m.group()) for m in re.finditer(r"\S+", text)]
    t0 = {}; t1 = {}
    for i, j in enumerate(orig_index):
        if i < len(starts):
            t0[j] = min(t0.get(j, 1e9), starts[i]); t1[j] = max(t1.get(j, 0), ends[i])
    out = []
    for a, b, w in spans:
        s = [t0[k] for k in range(a, b) if k in t0]
        e = [t1[k] for k in range(a, b) if k in t1]
        if s:
            out.append({"word": w, "char": a, "start": min(s), "end": max(e)})
    return out


def request(spoken, voice, previous_text=None, next_text=None):
    """-> (request body, cache key) for one take."""
    body = {"text": spoken, "model_id": voice["model_id"], "voice_settings": voice.get("voice_settings") or {},
            "seed": voice.get("seed", 1)}
    if previous_text: body["previous_text"] = previous_text
    if next_text: body["next_text"] = next_text
    return body, hashlib.sha256(json.dumps([voice["voice_id"], body], sort_keys=True).encode()).hexdigest()[:20]


def tts(spoken, voice, previous_text=None, next_text=None):
    """One ElevenLabs call (cached). -> (mp3 path, alignment dict)."""
    body, key = request(spoken, voice, previous_text, next_text)
    mp3, meta = os.path.join(CACHE, key + ".mp3"), os.path.join(CACHE, key + ".json")
    if os.path.exists(mp3) and os.path.exists(meta):
        with open(meta, encoding="utf-8") as f:
            return mp3, json.load(f)
    os.makedirs(CACHE, exist_ok=True)
    for fmt in FORMATS:
        r = requests.post(f"{API}/text-to-speech/{voice['voice_id']}/with-timestamps",
                          headers={"xi-api-key": api_key()}, params={"output_format": fmt}, json=body, timeout=180)
        if r.status_code in (400, 403) and "format" in r.text.lower() and fmt != FORMATS[-1]:
            continue
        if r.status_code == 400 and (previous_text or next_text) and "previous" in r.text.lower():
            return tts(spoken, voice)               # model doesn't take context; voice it alone
        r.raise_for_status()
        break
    j = r.json()
    with open(mp3, "wb") as f:
        f.write(base64.b64decode(j["audio_base64"]))
    meta_d = {"alignment": j["alignment"], "format": fmt, "request": body, "voice_id": voice["voice_id"],
              "sha256": hashlib.sha256(open(mp3, "rb").read()).hexdigest()}
    with open(meta, "w", encoding="utf-8") as f:
        json.dump(meta_d, f)
    return mp3, meta_d


def narrate(text, voice=None, previous_text=None, next_text=None):
    """Script text (with optional {cue} marks) -> dict(audio, duration, words, cues, sha256, request)."""
    voice = voice or load_voice()
    clean, cue_chars = strip_cues(text)
    spoken, orig = respell(clean, pronunciations())
    mp3, meta = tts(spoken, voice, previous_text, next_text)
    a = meta["alignment"]
    ws = words(clean, a["character_start_times_seconds"], a["character_end_times_seconds"], orig)
    cues = {}
    for name, c in cue_chars.items():
        nxt = [w for w in ws if w["char"] >= c]
        cues[name] = nxt[0]["start"] if nxt else ws[-1]["end"]
    return {"audio": mp3, "text": clean, "spoken": spoken, "duration": a["character_end_times_seconds"][-1],
            "words": ws, "cues": cues, "sha256": meta["sha256"], "request": meta["request"],
            "voice_id": meta["voice_id"], "format": meta["format"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--say", required=True)
    ap.add_argument("--voice", help="voice_id (default: narration/voice.yaml)")
    a = ap.parse_args()
    v = load_voice()
    if a.voice:
        v["voice_id"] = a.voice
    n = narrate(a.say, v)
    print(n["audio"], f"{n['duration']:.2f}s")
