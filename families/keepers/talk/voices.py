"""The talking format's voice track: a voice per character, the narrator's pace, levelling (owner 2026-11-17).

Rules (docs/engines/forest_keepers_talk_handoff.md, each one cost a round with the owner):
- Every character speaks with its own ElevenLabs voice (narration/keepers_cast_voices.yaml, the owner's picks).
- The narrator, Johanna, is voiced on eleven_v4 in ONE take per chapter. Voiced line by line she speeds up ("a speed
  reading contest"). She has no speed setting, since it does nothing on v4. Each of her lines is then slowed to about
  157 words a minute with a pitch-preserving stretch (ffmpeg atempo). He called 157 "perfect".
- Her take is cut into lines in the middle of the REAL pause between them, found from the sound. The service's
  character timings were about 0.3 s off and clipped her last word ("she gets cut off mid-word").
- Every line is brought to the same loudness before mixing, and Springs goes a further 2 dB down ("Springs is much
  louder of a speaker than every other speaker").
Takes are cached by request (engine.narration.tts), so voicing the same script again costs nothing.

A chapter's script is a list of (who, text, pause after it in seconds); who is narrator, sprout, springs, digs, glo.
"""
import json
import os
import shutil
import subprocess

import numpy as np
import yaml

from engine.log import ROOT

SR = 44100
CAST_FILE = os.path.join(ROOT, "narration", "keepers_cast_voices.yaml")
VOICE_RMS = 0.085              # every line's loudness while it is sounding (RMS of its active part)
TRIM_DB = {"springs": -2.0}    # a bright voice sounds louder than its level says
LEAD_IN = 0.5                  # seconds before the first line


def cast():
    with open(CAST_FILE, encoding="utf-8") as f:
        c = yaml.safe_load(f)
    out = {}
    for who in ("narrator", "sprout", "springs", "digs", "glo"):
        v = dict(c[who])
        v["voice_settings"] = c["narrator_settings" if who == "narrator" else "voice_settings"]
        v.setdefault("seed", 1)
        out[who] = v
    return out


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def decode(path):
    raw = subprocess.run([ffmpeg(), "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def stretch(a, factor):
    """Slow (factor < 1) or quicken a clip without changing its pitch (ffmpeg atempo)."""
    if abs(factor - 1.0) < 0.01:
        return a
    p = subprocess.run([ffmpeg(), "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        f"atempo={factor:.4f}", "-f", "f32le", "-"], input=a.astype(np.float32).tobytes(),
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def level(a, who):
    n = int(0.02 * SR)
    fr = np.array([np.sqrt(np.mean(a[i:i + n] ** 2)) for i in range(0, max(1, len(a) - n), n)])
    active = fr[fr > 0.2 * fr.max()]
    g = VOICE_RMS / (float(np.sqrt(np.mean(active ** 2))) + 1e-9) * 10 ** (TRIM_DB.get(who, 0.0) / 20)
    return (a * g).astype(np.float32)


def narrator_cuts(alignment, lines):
    """Where the service says each of her lines starts and ends in the one take (a guide only)."""
    st, en = alignment["character_start_times_seconds"], alignment["character_end_times_seconds"]
    cuts, pos = [], 0
    for t in lines:
        cuts.append(dict(text=t, start=st[pos], end=en[pos + len(t) - 1]))
        pos += len(t) + 1
    return cuts


def narrator_bounds(nar, cuts):
    """Each narrator line's (start, end) sample in her one take: every cut is made in the middle of the longest quiet
    stretch near where the timings say the line ends, never on the timings themselves."""
    hop = SR // 100
    env = np.array([np.sqrt(np.mean(nar[i:i + hop] ** 2)) for i in range(0, len(nar) - hop, hop)])
    quiet = env < 0.035 * env.max()
    cutpts = []
    for a, b in zip(cuts, cuts[1:]):
        lo, hi = int(max(0.0, a["end"] - 0.6) * 100), int(min(len(nar) / SR, b["start"] + 1.2) * 100)
        best, run = None, None
        for j in range(lo, min(hi, len(quiet))):
            if quiet[j]:
                run = (run[0], j) if run else (j, j)
                if best is None or run[1] - run[0] > best[1] - best[0]:
                    best = run
            else:
                run = None
        if best is None or best[1] - best[0] < 8:          # under 0.08 s of quiet: not a real pause between lines
            raise ValueError(f"no clear pause after narrator line {a['text']!r}: voice the take again (new seed)")
        cutpts.append(int((best[0] + best[1]) / 2 / 100 * SR))
    edges = [0] + cutpts + [len(nar)]
    out = []
    for s0, s1 in zip(edges, edges[1:]):                    # trim the silence, keep a little air
        seg = np.abs(nar[s0:s1])
        loud = np.nonzero(seg > 0.02 * np.abs(nar).max())[0]
        out.append((max(s0, s0 + loud[0] - int(0.05 * SR)), min(s1, s0 + loud[-1] + int(0.22 * SR))))
    return out


def characters(script):
    """How many characters a chapter sends to ElevenLabs (about its credits, before caching)."""
    return sum(len(t) for _, t, _ in script)


def voice_chapter(script, out_dir, name, pace_wpm=None, lead_in=LEAD_IN):
    """Voices one chapter (cached) and lays its lines end to end with their pauses. Writes <name>_voices.wav and
    <name>_cues.json in out_dir; -> the cues: [{i, who, text, start, end}] in seconds."""
    from engine.narration import tts
    from scipy.io import wavfile
    V = cast()
    pace = pace_wpm or V["narrator"].get("pace_wpm", 157)
    nar_lines = [t for w, t, _ in script if w == "narrator"]
    nar, bounds = None, []
    if nar_lines:
        mp3, meta = tts(" ".join(nar_lines), V["narrator"])
        nar = decode(mp3)
        bounds = narrator_bounds(nar, narrator_cuts(meta["alignment"], nar_lines))
    t, cues, parts, n = lead_in, [], [], 0
    for i, (who, text, pause) in enumerate(script):
        if who == "narrator":
            a = nar[bounds[n][0]:bounds[n][1]].copy()
            n += 1
            f = int(0.03 * SR)
            a[:f] *= np.linspace(0, 1, f)
            a[-f:] *= np.linspace(1, 0, f)
            want = len(text.split()) / pace * 60 + 0.26                # + the little air kept round the line
            factor = max(0.75, min(1.25, (len(a) / SR) / want))
            a = stretch(a, factor)
        else:
            mp3, _ = tts(text, V[who])
            a = decode(mp3)
            f = int(0.006 * SR)                                        # no click where a take starts on a word
            a[:f] *= np.linspace(0, 1, f)
            a[-f:] *= np.linspace(1, 0, f)
        a = level(a, who)
        cues.append(dict(i=i, who=who, text=text, start=round(t, 3), end=round(t + len(a) / SR, 3)))
        parts.append((t, a))
        t += len(a) / SR + pause
    buf = np.zeros(int((t + 1) * SR), np.float32)
    for t0, a in parts:
        buf[int(t0 * SR):int(t0 * SR) + len(a)] += a
    os.makedirs(out_dir, exist_ok=True)
    wavfile.write(os.path.join(out_dir, f"{name}_voices.wav"), SR, (np.clip(buf, -1, 1) * 32767).astype(np.int16))
    with open(os.path.join(out_dir, f"{name}_cues.json"), "w", encoding="utf-8") as f:
        json.dump(cues, f, indent=1)
    return cues


def credits_report(before):
    """One line for Local Operations after a voicing batch: credits used by it and what is left this period."""
    from engine.elevenlabs import credits
    used, limit = credits()
    return f"ElevenLabs: this batch {used - before[0]:,} credits; used {used:,} of {limit:,} this period"
