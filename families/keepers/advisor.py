"""FK continuity advisor (required before any Forest Keepers review ask; owner 2026-11-07).

The owner turned down FK0021 The Harvest Feast over misses that every code check passed ("gross negligence";
"You're going to need some kind of new continuity check or some kind of new advisor to go through these"). The
code checks (storycheck, staging, teleports) only test what someone thought to measure. This tool makes the
finished video reviewable by FRESH agents that never saw the build, the way a viewer sees it:

  prep    sample the rendered file densely (contact sheets every 0.5 s, 0.1 s strips around every sharp
          motion), transcribe the narration with local speech-to-text and compare it word by word with the
          script (wrong / misheard words, a homophone list), and write one review prompt per ~75 s chunk.
  (agents) the maker session starts one fresh general-purpose Agent per prompt file, all in one message:
          "Read <prompt file> and do exactly what it says." Each agent reviews its chunk scene by scene against
          the owner's checklist and writes findings_NN.json (timestamps, must-fix / should-fix).
  report  merge the agents' findings and the speech-to-text check into one report (video_log/advisor/),
          print the counts; exit code 1 while anything is must-fix.
  frame / strip   helpers the agents call to zoom in (a full-resolution frame or crop at a time, or a strip of
          frames between two times).

The maker fixes every must-fix, re-renders those parts and runs the advisor again until it reports 0 must-fix.
The report's path and counts go in the HANDOFF entry and with the review ask. See
docs/engines/forest_keepers_continuity.md (with the plan-level cause-and-effect check, causecheck.py, that runs
before the render).

Written by the FK0022 Bug Hunt session (2026-11-07) and handed to FK remake session 3, which owns the FK continuity
advisor (Local Operations). `--audio` (added by remake session 3): run the speech-to-text on a soundtrack .wav,
e.g. before the render.

    python families/keepers/advisor.py prep "<video.mp4>" --id FK0021 [--script lines.json] [--about "..."]
                                               [--from S --to S] [--chunk 75]
    python families/keepers/advisor.py report FK0021
    python families/keepers/advisor.py frame "<video.mp4>" 14.2 [x0 y0 x1 y1]
    python families/keepers/advisor.py strip "<video.mp4>" 13.5 15.0 [step]

--script is a JSON list of [time_s, "line"] (the narrator's lines as written; write it with write_script()).
Runs at Idle priority 7 AM-9 PM (Studio stalls at 100% CPU), Below Normal overnight.
"""
import argparse
import ctypes
import difflib
import glob
import json
import os
import re
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
ME = os.path.abspath(__file__)
LOG_DIR = os.path.join(ROOT, "video_log", "advisor")
DOC = os.path.join(ROOT, "docs", "engines", "forest_keepers_continuity.md")

SHEET_STEP = 0.5          # s between contact-sheet frames
GRID = (3, 3)             # tiles per sheet (cols, rows): 9 frames = 4.5 s per sheet
TILE = (640, 360)
STRIP_STEP = 0.1          # s between frames in a motion strip (9 frames = 0.9 s around the moment)
CHUNK = 75.0              # s of video per review agent
OVERLAP = 3.0             # s shared with the next chunk
MOMENT_GAP = 3.0          # s between two detected moments, at least
MOMENTS_PER_MIN = 6       # at most this many detected moments a minute (the sharpest)
STT_MODEL = "small.en"


def low_priority():
    """Idle 7 AM-9 PM, Below Normal overnight (Local Operations 2026-11-07); ffmpeg children inherit it."""
    if os.name == "nt":
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = ctypes.c_void_p
        k.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        k.SetPriorityClass(k.GetCurrentProcess(), 0x40 if 7 <= time.localtime().tm_hour < 21 else 0x4000)


def stamp(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def out_dir(vid_id):
    return os.path.join(ROOT, "renders", "_advisor", vid_id)


def duration(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def _font(size):
    for f in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def grab(video, t, size=None):
    """One frame at time t as a PIL image (full resolution unless size)."""
    vf = ["-vf", f"scale={size[0]}:{size[1]}"] if size else []
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", *vf,
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True)
    from io import BytesIO
    return Image.open(BytesIO(r.stdout)).convert("RGB")


def frames_at(video, t0, t1, step, size):
    """Frames every `step` s in [t0, t1] (one decode pass) -> list of (t, PIL image)."""
    w, h = size
    n = int(round((t1 - t0) / step)) + 1
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t0:.3f}", "-i", video, "-t", f"{(n - 1) * step + 0.02:.3f}",
                        "-vf", f"fps={1 / step:.6f}:start_time=0,scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True)
    a = np.frombuffer(r.stdout, np.uint8)
    k = a.size // (w * h * 3)
    a = a[:k * w * h * 3].reshape(k, h, w, 3)
    return [(t0 + i * step, Image.fromarray(a[i])) for i in range(min(k, n))]


def sheet(tiles, path, title=""):
    """Contact sheet: tiles = [(t, image)], GRID layout, each tile labelled with its time."""
    cols, rows = GRID
    tw, th = TILE
    pad = 34
    S = Image.new("RGB", (cols * tw, rows * th + pad), (20, 20, 20))
    d = ImageDraw.Draw(S)
    d.text((8, 4), title, fill=(255, 255, 255), font=_font(24))
    f = _font(26)
    for i, (t, im) in enumerate(tiles[:cols * rows]):
        x, y = (i % cols) * tw, pad + (i // cols) * th
        S.paste(im.resize((tw, th)), (x, y))
        d.rectangle((x, y, x + 112, y + 34), fill=(0, 0, 0))
        d.text((x + 6, y + 3), stamp(t), fill=(255, 230, 80), font=f)
        d.rectangle((x, y, x + tw - 1, y + th - 1), outline=(60, 60, 60))
    S.save(path, quality=88)
    return path


# ----- motion: where the sharp, small, quick things happen -----

def motion(video, t0, t1, fps=10):
    """-> times, whole-frame change, sharpest 8x8-block change (per frame, 0-255 scale)."""
    w, h = 192, 108
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t0:.3f}", "-i", video, "-t", f"{t1 - t0:.3f}",
                        "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True, check=True)
    a = np.frombuffer(r.stdout, np.uint8).astype(np.float32)
    n = a.size // (w * h)
    a = a[:n * w * h].reshape(n, h, w)
    d = np.abs(np.diff(a, axis=0))
    whole = d.mean(axis=(1, 2))
    hb, wb = h // 8 * 8, w // 8 * 8                                  # whole 8-px blocks only (108 rows = 13 blocks)
    blocks = d[:, :hb, :wb].reshape(n - 1, hb // 8, 8, wb // 8, 8).mean(axis=(2, 4)).reshape(n - 1, -1)
    sharp = blocks.max(axis=1)
    ts = t0 + (np.arange(1, n) / fps)
    return ts, whole, sharp


def cuts_and_moments(video, t0, t1):
    ts, whole, sharp = motion(video, t0, t1)
    med = np.median(whole) + 1e-3
    cuts = [float(t) for t, v in zip(ts, whole) if v > max(25.0, 12 * med)]          # straight camera cuts
    base = np.array([np.median(sharp[max(0, i - 30):i + 30]) for i in range(len(sharp))]) + 1.0
    score = sharp / base
    cand = sorted(((score[i], float(ts[i])) for i in range(1, len(ts) - 1)
                   if score[i] >= score[i - 1] and score[i] >= score[i + 1] and score[i] > 2.0
                   and not any(abs(ts[i] - c) < 0.3 for c in cuts)), reverse=True)
    cap = max(1, int((t1 - t0) / 60.0 * MOMENTS_PER_MIN))
    picked = []
    for s, t in cand:
        if len(picked) >= cap:
            break
        if all(abs(t - p) >= MOMENT_GAP for p in picked):
            picked.append(t)
    return cuts, sorted(picked)


# ----- narration: speech-to-text against the script -----

HOMOPHONES = [  # heard one of these where the script has another: the same sound, not an error
    "flour flower", "kneads needs", "knead need", "kneading needing", "kneaded needed", "glo glow", "glos glows",
    "digs digs", "hans hands hans's hans'", "twigs twig's", "their there they're", "to too two", "its it's",
    "by buy bye", "for four fore", "hear here", "know no", "knew new", "one won", "right write", "sea see",
    "son sun", "tail tale", "wait weight", "wood would", "whole hole", "piece peace", "bear bare", "dough doe",
    "berry bury", "pail pale", "pair pear", "flea flee", "meet meat", "night knight", "rose rows", "weather whether",
    "wear where", "which witch", "ate eight", "aloud allowed", "roll role", "sew so sow", "poll pole", "sail sale",
    "plain plane", "steal steel", "board bored", "heard herd", "hair hare", "hall haul", "toe tow", "dear deer",
    "moose mousse", "flu flew", "blue blew", "through threw", "way weigh", "great grate", "break brake",
    "made maid", "mail male", "nose knows", "rain reign rein", "red read", "lead led", "tied tide", "bean been",
    "cents sense scents", "seam seem", "creek creak", "peak peek", "lone loan", "cellar seller", "chews choose",
    "ok okay", "alright all right",
]
EQUIV = {}
for g in HOMOPHONES:
    ws = g.split()
    for w_ in ws:
        EQUIV.setdefault(w_, set()).update(ws)

# Words a voice can say two ways (or that the TTS has said wrong before: "flour" came out "floor", FK0021).
RISKY = set("""flour read lead wind winds wound tear tears bow bows live lives close closes dove bass sow row rows
minute content desert object present record produce refuse does polish use excuse house moped resume sewer axes
console buffet entrance invalid separate wicked aged learned blessed tower bowed slough sow sewn graduate
estimate moderate alternate appropriate deliberate""".split())

NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
       "8": "eight", "9": "nine", "10": "ten", "11": "eleven", "12": "twelve"}


def words(text):
    out = []
    for w_ in re.findall(r"[A-Za-z0-9']+", text.replace("’", "'")):
        w_ = w_.lower().strip("'")
        if w_:
            out.append(NUM.get(w_, w_))
    return out


def same(a, b):
    return a == b or b in EQUIV.get(a, ()) or a.rstrip("s") == b.rstrip("s") and len(a) > 3


def _audio(video, t0=0.0, dur=None):
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", f"{t0:.3f}", "-i", video]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    raw = subprocess.run(cmd + ["-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True,
                         check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


_MODEL = None


def _model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel   # local; no credits (ElevenLabs is saved for the narration)
        _MODEL = WhisperModel(STT_MODEL, device="cpu", compute_type="int8", cpu_threads=4)
    return _MODEL


def transcribe(video, t0=0.0, t1=None, prompt=None):
    """-> [(t, word)] heard in [t0, t1] (absolute times)."""
    a = _audio(video, t0, (t1 - t0) if t1 else None)
    segs, _ = _model().transcribe(a, language="en", word_timestamps=True, condition_on_previous_text=False,
                                  beam_size=5, initial_prompt=prompt)
    out = []
    for s in segs:
        for w_ in s.words or []:
            for x in words(w_.word):
                out.append((t0 + w_.start, x))
    return out


def stt_check(video, script, t0, t1):
    """Every script word against what the speech-to-text heard. A wrong word heard twice (also with the script as a
    hint, which pulls the model toward the written word) is must-fix; heard wrong only once is should-fix."""
    lines = [(float(t), s) for t, s in script if t0 - 1 <= float(t) <= t1]
    heard = transcribe(video, t0, t1)
    sw = [(t, w_, li) for li, (t, s) in enumerate(lines) for w_ in words(s)]
    hw = [w_ for _, w_ in heard]
    sm = difflib.SequenceMatcher(None, [w_ for _, w_, _ in sw], hw, autojunk=False)
    issues, risky = [], []
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            continue
        if op == "insert":
            continue                         # extra words heard (the Keepers' noises, music) - not the script's
        sws = sw[a0:a1]
        hws = heard[b0:b1]
        if op == "replace":
            pairs = list(zip(sws, hws))
            for (st_, s_w, li), (ht, h_w) in pairs:
                if not same(s_w, h_w):
                    issues.append(dict(t=ht, line=lines[li][1], script=s_w, heard=h_w))
            for st_, s_w, li in sws[len(pairs):]:
                issues.append(dict(t=st_, line=lines[li][1], script=s_w, heard=""))
        else:  # delete: script words nobody heard
            for st_, s_w, li in sws:
                issues.append(dict(t=hws[0][0] if hws else st_, line=lines[li][1], script=s_w, heard=""))
    # heard-wrong words: listen again around them with the line as the hint
    for it in issues:
        if not it["heard"]:
            it["severity"] = "should-fix"
            it["why"] = "a script word the speech-to-text did not hear (missing, swallowed or under the music?)"
            continue
        a = max(0.0, it["t"] - 2.5)
        again = [w_ for _, w_ in transcribe(video, a, a + 5.0, prompt=it["line"])]
        it["heard_again"] = " ".join(again)
        if it["script"] in again or any(same(it["script"], w_) for w_ in again):
            it["severity"] = "should-fix"
            it["why"] = "heard wrong once, right with the line as a hint: unclear pronunciation, check it"
        else:
            it["severity"] = "must-fix"
            it["why"] = "heard wrong twice, even with the line as a hint: the voice says another word"
    pos = {}
    for k, (op, a0, a1, b0, b1) in enumerate(sm.get_opcodes()):
        if op == "equal":
            for j in range(a1 - a0):
                pos[a0 + j] = heard[b0 + j]
    for i, (st_, s_w, li) in enumerate(sw):
        if s_w in RISKY:
            h = pos.get(i)
            risky.append(dict(t=h[0] if h else st_, word=s_w, line=lines[li][1], heard=h[1] if h else "?"))
    return dict(lines=len(lines), script_words=len(sw), heard_words=len(hw), issues=issues, risky=risky,
                transcript=[[round(t, 2), w_] for t, w_ in heard])


def write_script(lines, path):
    """lines = [(time_s, text)] -> the --script JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump([[round(float(t), 2), s] for t, s in lines], f, indent=1, ensure_ascii=False)
    return path


# ----- the review prompt -----

CHECKLIST = """\
THE CHECKLIST (the owner's own rejection notes; every one of these reached him once - catch them first):
 1. TOO SMALL / TOO QUICK: a key moment (something hitting, landing, appearing, changing) so small on screen or so
    quick that a viewer can't see what happened. If the story needs it seen, it must be big and last long enough.
    (FK0021: the acorn hitting Digs' head at 0:14 was tiny and over in a blink.) Also: where does a thing go after
    the moment - carried, put down, or left hanging in the air?
 2. ACTIONS THAT UNDO THEMSELVES OR MAKE NO SENSE: a character's work that cancels other work or a real person
    would never do it that way. (FK0021: Digs threw the dirt from each new hole straight into the hole he had just
    dug for the other post.) Ask of every action: where does the material go, and does the result make sense?
 3. TOOLS TOUCHING THE WRONG SPOT: the change (cut, mark, hole, chips) must happen exactly where the tool touches,
    at the moment it touches. (FK0021: Twigs sawed one corner and the opposite corner fell off.) Zoom in on every
    cut / tool contact (use the frame command below).
 4. MECHANISMS THAT COULDN'T WORK: gears whose teeth are uneven, missing on part of the wheel, not meshing, or cut
    where no blade went; wheels, axles, levers, ropes, hinges that could not do what they are shown doing.
    (FK0021: gear teeth appeared at random places and only round half the wheel.)
 5. NARRATION: the speech-to-text check below lists words the voice may have said wrong ("floor" for "flour" in
    FK0021). Also flag narration that describes something the picture does not show at that time.
 6. SEE-THROUGH AND BLOCKED ACTION: something visible through a body or object that is in front of it (FK0021:
    acorns visible through Glo); a character or prop standing in front of the main action (FK0021: Glo stood in
    front of the mill while it worked; a basket in Glo's hands hid the lanterns lighting up). Check what is in
    front of what in every overlap.
 7. TOO MANY STEPS FOR A SIMPLE JOB: a character walking/shuffling several steps for something a hand movement
    would do. (FK0021: Twigs took 6 steps to slice the dough.)
 8. SHAPES MORPHING: anything changing shape, size, colour or contents without a visible cause. (FK0021: cut dough
    pieces turned into perfect round rolls by themselves.) Every change needs the action that causes it, on screen.
 9. PASSING THROUGH SOLID THINGS: a body, tool or object going through a wall, floor, table, oven, door frame or
    another character. Things go in and out through openings only. (FK0021: the bread went through the oven's clay
    wall; the rabbit and hedgehog came out through their house walls, half in and half out.)

AND THE STANDING RULES (these were caught before; still check):
 10. No warping: nobody jumps to a new spot between two frames (a straight camera cut is fine; the characters must
     be where they were, seen from the new angle).
 11. No long walks: walking only in short bursts (about 3-4 s per shot); a longer trip has a cut, a new angle, crop
     or zoom.
 12. Hans has at most 8 limbs (6 legs + 2 tentacles; if he works with a 3rd arm, one leg is lifted off the ground).
 13. Depth order: something going behind another thing is drawn behind it all the way, not only on arrival.
 14. Glo: his tendrils come only from under his dome; he changes things with a light flare.
 15. Everything inside a sign, book, page or frame stays inside it.
 16. Anything else that a careful viewer would call a mistake, lazy, cheap or confusing.
"""

PROMPT = """\
You are the continuity advisor for a Forest Keepers cartoon episode (a calm 2D picture-book cartoon: six friendly
tree creatures - Wheels, Hans, Twigs, Springs, Glo and Digs - build things in the forest, with a narrator). You have
NOT seen how it was made. Review it exactly as a careful viewer would, frame by frame. The owner has rejected
episodes for mistakes nobody checked for, and called it "gross negligence": your job is to find every such mistake
before he does. Do not assume anything is fine because it was probably intended. Report what you see.

Video: {video}
Your part: {t0} to {t1} (chunk {n} of {total}; the neighbouring chunks overlap yours by a few seconds).
{about}
How to look:
- Contact sheets, one frame every {step} s (9 per sheet, time in the corner of each frame). Read ALL of them:
{sheets}
- Motion strips: 9 frames 0.1 s apart around each sharp, small movement the tool detected (hits, landings, cuts,
  things appearing). Read ALL of them:
{strips}
- Straight camera cuts the tool detected at: {cuts}. A cut itself is fine; check that nobody jumps across it.
- ZOOM IN whenever something is small or unclear (always on tool contacts, gears, overlaps, doorways, things
  going into or out of anything). Full-resolution frame, optionally cropped to x0 y0 x1 y1 of 1920x1080:
    "{py}" "{me}" frame "{video}" <seconds> [x0 y0 x1 y1]
  Frames between two times (a new strip): "{py}" "{me}" strip "{video}" <t0> <t1> [step]
  Each prints the path of an image; Read it. Use these as much as you need.
- Narration in your part (as written, with the time it starts):
{script}
- What the speech-to-text heard in your part:
{heard}
- Speech-to-text check (script vs heard) for your part:
{stt}

{checklist}
Severity: must-fix = a viewer would notice it as a mistake, or the story moment is lost; should-fix = a small
blemish or a doubt worth a look. When unsure if something is real, zoom in first; if still unsure, should-fix.

Work scene by scene. For each scene say in one line what happens, then check it against every item above.

Write your result as JSON (UTF-8) to: {out}
{{"chunk": {n}, "reviewed": [{t0s}, {t1s}],
 "scenes": [{{"t0": s, "t1": s, "what": "one line"}}],
 "findings": [{{"t": s, "t_end": s, "check": <1-16>, "severity": "must-fix" | "should-fix",
               "what": "what is wrong, precisely (who, what, where on screen)",
               "fix": "what it should look like instead", "evidence": "image path(s) that show it"}}]}}
Times in seconds from the start of the video. Then reply with one line: the number of must-fix and should-fix.
"""


def _list(paths):
    return "\n".join(f"    {p}" for p in paths) if paths else "    (none)"


def prep(a):
    low_priority()
    video = os.path.abspath(a.video)
    D = out_dir(a.id)
    os.makedirs(os.path.join(D, "sheets"), exist_ok=True)
    os.makedirs(os.path.join(D, "strips"), exist_ok=True)
    for old in glob.glob(os.path.join(D, "findings_*.json")) + glob.glob(os.path.join(D, "prompt_*.md")):
        os.remove(old)                       # a fresh round: stale findings never count
    dur = duration(video)
    T0 = max(0.0, a.start or 0.0)
    T1 = min(dur, a.end if a.end else dur)
    t_start = time.time()
    print(f"{a.id}: {stamp(T0)}-{stamp(T1)} of {stamp(dur)}")

    script = json.load(open(a.script, encoding="utf-8")) if a.script else []
    snd = os.path.abspath(a.audio) if getattr(a, "audio", None) else video
    stt = stt_check(snd, script, T0, T1) if script else dict(lines=0, issues=[], risky=[],
                                                             transcript=[[round(t, 2), w_] for t, w_ in transcribe(snd, T0, T1)])
    print(f"  speech-to-text: {len(stt['issues'])} word issues "
          f"({sum(i['severity'] == 'must-fix' for i in stt['issues'])} must-fix), {len(stt['risky'])} risky words, "
          f"{time.time() - t_start:.0f}s")

    cuts, moments = cuts_and_moments(video, T0, T1)
    print(f"  {len(cuts)} camera cuts, {len(moments)} motion moments")

    # chunks
    edges, t = [], T0
    while t < T1 - 1.0:
        edges.append((max(T0, t - (OVERLAP if t > T0 else 0)), min(T1, t + a.chunk)))
        t += a.chunk
    if len(edges) > 1 and edges[-1][1] - edges[-1][0] < 25:          # fold a short tail into the one before
        edges[-2] = (edges[-2][0], edges[-1][1])
        edges.pop()
    per = GRID[0] * GRID[1]
    prompts = []
    for n, (c0, c1) in enumerate(edges, 1):
        tiles = frames_at(video, c0, c1, SHEET_STEP, TILE)
        sheets = []
        for k in range(0, len(tiles), per):
            grp = tiles[k:k + per]
            p = os.path.join(D, "sheets", f"c{n:02d}_{k // per:03d}_{grp[0][0]:07.2f}.jpg")
            sheets.append(sheet(grp, p, f"{a.id}  {stamp(grp[0][0])} - {stamp(grp[-1][0])}  every {SHEET_STEP} s"))
        strips = []
        for m in moments:
            if c0 <= m < c1:
                s0 = max(0.0, m - 0.4)
                tl = frames_at(video, s0, s0 + 8 * STRIP_STEP, STRIP_STEP, TILE)
                p = os.path.join(D, "strips", f"m_{m:07.2f}.jpg")
                strips.append(sheet(tl, p, f"{a.id}  motion at {stamp(m)}  frames {STRIP_STEP} s apart"))
        lines = [f"    {stamp(float(t))}  {s}" for t, s in script if c0 - 6 <= float(t) <= c1]
        heard = " ".join(f"[{stamp(t)}] {w_}" if i % 12 == 0 else w_
                         for i, (t, w_) in enumerate((t, w_) for t, w_ in stt["transcript"] if c0 <= t <= c1))
        st = [i for i in stt["issues"] if c0 - 1 <= i["t"] <= c1 + 1]
        stt_txt = "\n".join(f"    {stamp(i['t'])} {i['severity']}: script \"{i['script']}\", heard \"{i['heard']}\" "
                            f"({i['why']}) in: {i['line']}" for i in st) or "    no word issues"
        rk = [r for r in stt["risky"] if c0 - 1 <= r["t"] <= c1 + 1]
        if rk:
            stt_txt += "\n    words that can be said two ways (speech-to-text can't always tell): " + \
                       "; ".join(f"{stamp(r['t'])} \"{r['word']}\" heard \"{r['heard']}\"" for r in rk)
        out = os.path.join(D, f"findings_{n:02d}.json")
        txt = PROMPT.format(video=video, t0=stamp(c0), t1=stamp(c1), t0s=round(c0, 2), t1s=round(c1, 2), n=n,
                            total=len(edges), step=SHEET_STEP, sheets=_list(sheets), strips=_list(strips),
                            cuts=", ".join(stamp(c) for c in cuts if c0 <= c <= c1) or "none",
                            py=PY, me=ME, script="\n".join(lines) or "    (no narration here)",
                            heard="    " + (heard or "(nothing)"), stt=stt_txt, checklist=CHECKLIST, out=out,
                            about=("What the episode is about (from its maker): " + a.about + "\n") if a.about else "")
        p = os.path.join(D, f"prompt_{n:02d}.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
        prompts.append(p)
        print(f"  chunk {n}: {stamp(c0)}-{stamp(c1)}  {len(sheets)} sheets, {len(strips)} strips")
    meta = dict(id=a.id, video=video, window=[T0, T1], duration=dur, chunks=edges, cuts=cuts, moments=moments,
                stt={k: v for k, v in stt.items() if k != "transcript"}, script=a.script, about=a.about,
                prepared=time.strftime("%Y-%m-%d %H:%M"), prep_seconds=round(time.time() - t_start))
    with open(os.path.join(D, "advisor.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    with open(os.path.join(D, "transcript.json"), "w", encoding="utf-8") as f:
        json.dump(stt["transcript"], f)
    print(f"\nprep done in {time.time() - t_start:.0f}s. Now start {len(prompts)} FRESH general-purpose agents in ONE "
          f"message (no fork, no build context), each with the prompt:")
    for p in prompts:
        print(f'  Read "{p}" and do exactly what it says.')
    print(f"then: \"{PY}\" \"{ME}\" report {a.id}")


def report(a):
    D = out_dir(a.id)
    meta = json.load(open(os.path.join(D, "advisor.json"), encoding="utf-8"))
    chunks = meta["chunks"]
    found, missing = [], []
    for n in range(1, len(chunks) + 1):
        p = os.path.join(D, f"findings_{n:02d}.json")
        if not os.path.exists(p):
            missing.append(n)
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except ValueError as e:
            missing.append(n)
            print(f"chunk {n}: unreadable findings ({e})")
            continue
        for f_ in d.get("findings", []):
            f_["chunk"] = n
            found.append(f_)
    for i in meta["stt"]["issues"]:
        found.append(dict(t=i["t"], t_end=i["t"], check=5, severity=i["severity"], chunk="stt",
                          what=f"narration: script \"{i['script']}\", heard \"{i['heard']}\""
                               + (f" (again: \"{i.get('heard_again', '')}\")" if i.get("heard_again") else "")
                               + f" - {i['why']}. Line: {i['line']}",
                          fix="re-voice the line (respell the word in the narration lexicon) or reword it"))
    # the same thing seen by two neighbouring chunks: keep one
    found.sort(key=lambda f_: (float(f_.get("t", 0)), f_.get("severity") != "must-fix"))
    dedup = []
    for f_ in found:
        if any(abs(float(f_.get("t", 0)) - float(g.get("t", 0))) < 1.0 and f_.get("check") == g.get("check")
               and g["chunk"] != f_["chunk"] for g in dedup):
            continue
        dedup.append(f_)
    must = [f_ for f_ in dedup if f_.get("severity") == "must-fix"]
    should = [f_ for f_ in dedup if f_.get("severity") != "must-fix"]
    os.makedirs(LOG_DIR, exist_ok=True)
    rounds = sorted(glob.glob(os.path.join(LOG_DIR, f"{a.id}_r*.md")))
    rn = len(rounds) + 1
    T0, T1 = meta["window"]
    L = [f"# Continuity advisor - {a.id}, round {rn}",
         "",
         f"- Video: `{os.path.relpath(meta['video'], ROOT)}` ({stamp(meta['duration'])}); reviewed "
         f"{stamp(T0)}-{stamp(T1)} by {len(chunks)} fresh agents (no build context), prepared {meta['prepared']}.",
         f"- Sampled every {SHEET_STEP} s + 0.1 s strips round {len(meta['moments'])} sharp movements; "
         f"{len(meta['cuts'])} camera cuts; speech-to-text ({STT_MODEL}) vs {meta['stt']['lines']} script lines.",
         f"- **{len(must)} must-fix, {len(should)} should-fix**"
         + (f"; chunks with no findings file yet: {missing} (NOT a pass)" if missing else "") + ".",
         ""]
    for title, items in (("Must-fix", must), ("Should-fix", should)):
        L.append(f"## {title} ({len(items)})")
        L.append("")
        for f_ in items:
            t, te = float(f_.get("t", 0)), float(f_.get("t_end", f_.get("t", 0)) or 0)
            when = stamp(t) + (f"-{stamp(te)}" if te > t + 0.05 else "")
            L.append(f"- **{when}** [check {f_.get('check')}] {f_.get('what', '').strip()}"
                     + (f" -> {f_['fix'].strip()}" if f_.get("fix") else ""))
        L.append("")
    rk = meta["stt"].get("risky", [])
    if rk:
        L.append("## Words that can be said two ways (listen to these)")
        L.append("")
        L += [f"- {stamp(r['t'])} \"{r['word']}\" (heard \"{r['heard']}\"): {r['line']}" for r in rk]
        L.append("")
    txt = "\n".join(L)
    p = os.path.join(LOG_DIR, f"{a.id}_r{rn}.md")
    if missing:
        p = os.path.join(D, "report_incomplete.md")       # not a round until every chunk is in
    with open(p, "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)
    print(f"\nreport: {p}")
    sys.exit(1 if must or missing else 0)


def frame_cmd(a):
    video = os.path.abspath(a.video)
    D = out_dir("_zoom")
    os.makedirs(D, exist_ok=True)
    im = grab(video, a.t)
    name = f"{os.path.splitext(os.path.basename(video))[0][:12]}_{a.t:08.3f}"
    if a.box:
        x0, y0, x1, y1 = a.box
        im = im.crop((x0, y0, x1, y1))
        name += f"_{x0}_{y0}_{x1}_{y1}"
        if im.width < 800:                                    # small crops get blown up so details read
            s = 800 / im.width
            im = im.resize((800, int(im.height * s)), Image.LANCZOS)
    p = os.path.join(D, name + ".png")
    im.save(p)
    print(p)


def strip_cmd(a):
    video = os.path.abspath(a.video)
    D = out_dir("_zoom")
    os.makedirs(D, exist_ok=True)
    step = a.step or max(0.05, (a.t1 - a.t0) / 8)
    tl = frames_at(video, a.t0, a.t1, step, TILE)
    per = GRID[0] * GRID[1]
    for k in range(0, len(tl), per):
        grp = tl[k:k + per]
        p = os.path.join(D, f"{os.path.splitext(os.path.basename(video))[0][:12]}_strip_{grp[0][0]:08.3f}_{step:.2f}.jpg")
        print(sheet(grp, p, f"{stamp(grp[0][0])} - {stamp(grp[-1][0])}  every {step:.2f} s"))


def stt_cmd(a):
    """Only the narration check: every script word against what the speech-to-text heard (prints the issues)."""
    low_priority()
    script = json.load(open(a.script, encoding="utf-8"))
    snd = os.path.abspath(a.sound)
    t1 = a.end if a.end else duration(snd)
    r = stt_check(snd, script, a.start, t1)
    for i in r["issues"]:
        print(f"{stamp(i['t'])} {i['severity']}: script \"{i['script']}\", heard \"{i['heard']}\""
              + (f" (again: \"{i.get('heard_again', '')}\")" if i.get("heard_again") else "") + f"  | {i['line']}")
    for k in r["risky"]:
        print(f"{stamp(k['t'])} risky \"{k['word']}\" heard \"{k['heard']}\"  | {k['line']}")
    must = sum(i["severity"] == "must-fix" for i in r["issues"])
    print(f"{r['script_words']} script words, {len(r['issues'])} issues ({must} must-fix), {len(r['risky'])} risky")
    sys.exit(1 if must else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep")
    p.add_argument("video")
    p.add_argument("--id", required=True)
    p.add_argument("--script")
    p.add_argument("--about", default="")
    p.add_argument("--from", dest="start", type=float)
    p.add_argument("--to", dest="end", type=float)
    p.add_argument("--chunk", type=float, default=CHUNK)
    p.add_argument("--audio", help="speech-to-text on this sound file instead of the video's own track")
    p = sub.add_parser("stt", help="only the narration check, on a video or a soundtrack .wav")
    p.add_argument("sound")
    p.add_argument("--script", required=True)
    p.add_argument("--from", dest="start", type=float, default=0.0)
    p.add_argument("--to", dest="end", type=float)
    p = sub.add_parser("report")
    p.add_argument("id")
    p = sub.add_parser("frame")
    p.add_argument("video")
    p.add_argument("t", type=float)
    p.add_argument("box", type=int, nargs="*")
    p = sub.add_parser("strip")
    p.add_argument("video")
    p.add_argument("t0", type=float)
    p.add_argument("t1", type=float)
    p.add_argument("step", type=float, nargs="?")
    a = ap.parse_args()
    {"prep": prep, "report": report, "frame": frame_cmd, "strip": strip_cmd, "stt": stt_cmd}[a.cmd](a)


if __name__ == "__main__":
    main()
