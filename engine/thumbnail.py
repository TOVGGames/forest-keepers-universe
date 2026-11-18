"""YouTube thumbnail (1280x720) from a rendered video frame + big glowing text.

    python -m engine.thumbnail renders/BL0006_races.mp4 --at 12 --crop 420,0,1080,608 \
        --text "WHO SURVIVES?" --sub "12 marbles · 1 champion" --color "#ff2bd6" --out thumbnails/BL0006_races.png

Shorts cover (vertical): add --size 1080x1920.

Long videos need 4-6 really different options on one labelled contact sheet for the owner to pick
from (owner rule 2026-11-03, docs/PRODUCTION.md "Long-form: quality first, several thumbnails").
Make each option with a separate run of the command above, then tile them:

    python -m engine.thumbnail --sheet thumbnails/BL0000_A.png thumbnails/BL0000_B.png ...         --out thumbnails/BL0000_options.png
"""
import argparse
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")


def grab(video, at, size=(1280, 720), crop=None):
    pre = f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else ""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(at), "-i", video, "-frames:v", "1",
                          "-vf", pre + f"scale={size[0]}:{size[1]}:force_original_aspect_ratio=increase,"
                                 f"crop={size[0]}:{size[1]}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    return Image.frombytes("RGB", size, raw)


def make(video, at, text, sub=None, color="#00f0ff", out="thumb.png", anchor="top", darken=0.25, boost=1.25,
         allow_busy=False,
         crop=None, size=(1280, 720)):
    return decorate(grab(video, at, size=size, crop=crop), text, sub, color, out, anchor, darken, boost,
                    allow_busy=allow_busy)


def _text_band(ty, fs, sub):
    """Rows the headline block actually paints on, given its baseline."""
    return ty - 0.75 * fs, ty + (0.85 * fs + 40 if sub else 0.75 * fs)


def _lit_rows(a):
    """Per-row fraction of BRIGHT pixels.

    Count only bright ones. On these neon-on-black frames a dim peg field covers the whole
    picture, so a low threshold calls every frame "full" and the check becomes noise. Marbles,
    name labels and scoreboards are the bright things, and they are what must not be covered;
    pegs are decoration and text sits on them happily.
    """
    grey = a.mean(axis=2)
    bg = float(np.percentile(grey, 5))
    thr = bg + 0.60 * (float(np.percentile(grey, 99)) - bg)
    return (grey > thr).mean(axis=1)


def _band_ink(a, ty, fs, sub):
    """Worst row of bright pixels under the headline block at baseline `ty`."""
    lit = _lit_rows(a)
    h = a.shape[0]
    t0, t1 = _text_band(ty, fs, sub)
    t0, t1 = int(max(0, t0)), int(min(h, t1))
    return float(lit[t0:t1].max()) if t1 > t0 else 1.0


def _quietest_ty(a, fs, sub):
    """anchor="auto": put the headline on a band that is actually EMPTY.

    Returns (ty, worst_row_ink). The caller warns when nothing clean exists.

    The fixed anchors place the text at a constant height whatever is underneath, so on a
    cover whose subject happens to sit there the headline lands on top of it. Five sheets
    screened on 2026-11-04 had that fault: captions burying two of eight racers on a roster
    card, or the top two rows of the leaderboard the title was selling.

    The first attempt at this minimised MEAN edge energy and reproduced the bug exactly - on
    the reindeer roster it chose the second marble row, because a row holding two marbles is
    quieter on average than a row holding six, though it is just as fatal to cover. What
    matters is whether a band is empty, not whether it is quiet, so score each band by the
    ink in its WORST row: the fraction of pixels lit well above the background. An empty
    band scores ~0; a band with two marbles in it does not.
    """
    h = a.shape[0]
    lit = _lit_rows(a)                               # per-row fraction of BRIGHT pixels
    # Keep the WHOLE block on the picture. Scanning a flat 8-92% range let the quietest band
    # sit so low that the subtitle fell off the bottom edge - which is how BL30041's B and C
    # lost their sub-lines entirely on the first cut.
    above, below = _text_band(0, fs, sub)
    lo = int(-above + 12)
    hi = int(h - below - 12)
    if hi <= lo:                                     # text taller than the frame: centre it
        lo = hi = int(h / 2)
    best, best_score, best_ink = None, None, 1.0
    for ty in range(lo, hi + 1, max(2, h // 240)):
        t0, t1 = _text_band(ty, fs, sub)
        t0, t1 = int(max(0, t0)), int(min(h, t1))
        if t1 <= t0:
            continue
        ink = float(lit[t0:t1].max())
        score = ink * (1.0 + 0.25 * (1.0 - abs(ty - h / 2) / (h / 2)))   # favour top/bottom
        if best_score is None or score < best_score:
            best, best_score, best_ink = ty, score, ink
    return float(best if best is not None else 0.2 * h), best_ink


def race_cover_crop(img, pad=70, top_frac=0.17):
    """Crop a pre-gate races frame tight on the start box, measured rather than guessed.

    Why (Dons office, 2026-11-05): a full-frame pre-gate cover puts the twelve marbles in a
    thin band in the upper third and fills the rest with an empty peg grid. At 350 px the name
    labels are about 3 px per character - unreadable - so the "find yours" hook, which is the
    whole format, dies on the thumbnail. A blind A/B at phone size preferred a tight crop on
    all four Shorts tested, for exactly that reason.

    A FIXED crop does not work: the marbles settle anywhere along the two start ramps, so a
    box tuned on one seed clips the outermost marble on another (the first prototype cut "Gym"
    to "ym" and "Skiing" to "kiing"). So find the pile: take the brightest rows, measure how
    far the lit pixels actually spread across them, and build a 9:16 box around that with a
    margin. Clamped to the frame, so a wide pile just means less zoom.
    """
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    # Find the marbles by COLOUR, not brightness. Brightness picks the wrong things: the pinned
    # hook band is full-width white text and the two start rails are full-width white lines, so
    # a brightness search returns "the whole frame" and crops nothing (measured - the first
    # version of this returned 1080x1920 on all four test Shorts). Marbles are saturated; rails,
    # text and the grid are pale or dim.
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    sat = (a.max(axis=2) - a.min(axis=2))
    lit = a.max(axis=2)
    # band to search: below the hook band, above the peg field - the start box lives here
    y_lo, y_hi = int(h * 0.18), int(h * 0.50)
    region_s, region_l = sat[y_lo:y_hi], lit[y_lo:y_hi]
    mask = (region_s > 60) & (region_l > 110)
    # Keep only THICK vertical runs. With `tags_all` the name labels are drawn in each marble's
    # own colour, so they are saturated too - without this the labels counted as marbles, which
    # widened the span and dragged the crop up into the in-video hook band (measured: the crop
    # started at y=104 and swallowed the band). A marble is ~2r tall; label strokes are thin.
    thick = np.ones_like(mask)
    run = max(8, int(h * 0.012))
    for d in range(run):
        thick[:mask.shape[0] - run] &= mask[d:mask.shape[0] - run + d]
    thick[mask.shape[0] - run:] = False
    mask = thick
    if mask.sum() < 50:
        return None
    rows = mask.mean(axis=1)
    band = int(np.argmax(rows)) + y_lo
    lo_r = max(y_lo, band - int(h * 0.06)) - y_lo
    hi_r = min(y_hi, band + int(h * 0.06)) - y_lo
    # The two course WALLS are drawn in a palette colour too, and they sit at the extreme left
    # and right of every frame, so a bare any()-over-columns always returns the full width -
    # which is what made the first two attempts crop nothing. Ignore a margin at each edge, and
    # require a column to be lit on several rows so a one-pixel wall or rail cannot count.
    edge = int(w * 0.07)
    dens = mask[lo_r:hi_r].sum(axis=0)
    dens[:edge] = 0
    dens[-edge:] = 0
    xs = np.flatnonzero(dens >= 3)
    if xs.size < 2:
        return None
    x0, x1 = int(xs[0]) - pad, int(xs[-1]) + pad
    cw = max(int(w * 0.5), x1 - x0)                  # never zoom past 2x
    cx = (x0 + x1) / 2
    cw = min(cw, w)
    ch = int(round(cw * h / w))                      # keep the source aspect, so no re-crop
    cx = min(max(cx, cw / 2), w - cw / 2)
    # Reserve room above the CONTENT, not above the marbles. With `tags_all` the name tags sit
    # in rows above the pile, and measuring from the pile alone put them under the headline
    # (Local Operations, 2026-11-05). So find the top of whatever is drawn above the band - the
    # tag rows when they exist, the pile itself when they do not - and leave `top_frac` of the
    # crop height clear above THAT for the headline.
    y_from = max(0, band - int(h * 0.16))
    # Look only INSIDE the crop's own width and ignore thin verticals: the two course walls are
    # bright and run the full height of the frame, so a naive search finds them at the very top
    # of the window and reserves space above nothing (measured: it dragged the crop up into the
    # in-video hook band twice).
    x0c, x1c = int(max(0, cx - cw / 2) + 0.06 * cw), int(min(w, cx + cw / 2) - 0.06 * cw)
    look = lit[y_from:band, x0c:x1c]
    content_top = band
    if look.size:
        bright = np.flatnonzero((look > 150).sum(axis=1) >= 6)
        if bright.size:
            content_top = y_from + int(bright[0])
    cy0 = int(content_top - top_frac * ch)
    cy0 = min(max(cy0, 0), h - ch)
    return [int(cx - cw / 2), cy0, int(cw), ch]


def race_cover_outlier(img, gap_frac=0.055):
    """Is one marble sitting apart from the pack in a pre-gate cover? Returns its x, or None.

    Why this matters (Local Operations, 2026-11-05): on a pre-gate frame the marbles have only
    settled along the start ramps, so a marble sitting alone and higher up one ramp is NOT in
    the lead - but at 350 px it reads as a breakaway. A blind screener flagged exactly that on
    two of four covers ("the isolated cyan marble far left looks like a breakaway leader").
    Harmless until that marble happens to be the one that wins, at which point the cover is
    making an accidental promise about the result. The caller compares the returned x against
    the winner's position and, if they match, grabs a different pre-gate moment.

    Detection is the same column mask the crop uses: find the lit columns, then look for a run
    of empty columns wider than `gap_frac` of the frame separating the first or last group from
    the main mass.
    """
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    sat = a.max(axis=2) - a.min(axis=2)
    lit = a.max(axis=2)
    y_lo, y_hi = int(h * 0.18), int(h * 0.50)
    mask = (sat[y_lo:y_hi] > 60) & (lit[y_lo:y_hi] > 110)
    if mask.sum() < 50:
        return None
    rows = mask.mean(axis=1)
    band = int(np.argmax(rows))
    lo_r, hi_r = max(0, band - int(h * 0.06)), min(mask.shape[0], band + int(h * 0.06))
    edge = int(w * 0.07)
    dens = mask[lo_r:hi_r].sum(axis=0)
    dens[:edge] = 0
    dens[-edge:] = 0
    xs = np.flatnonzero(dens >= 3)
    if xs.size < 2:
        return None
    gaps = np.diff(xs)
    big = np.flatnonzero(gaps > gap_frac * w)
    if big.size == 0:
        return None
    # a detached group at either end is what reads as a breakaway; the middle is just the pack
    first_grp, last_grp = xs[: big[0] + 1], xs[big[-1] + 1:]
    if first_grp.size <= last_grp.size:
        return int(first_grp.mean())
    return int(last_grp.mean())


def _quiet_band(a, need, lo, hi):
    """Top row of the darkest `need`-tall window between lo and hi. Where a motif can go
    without covering anything."""
    grey = a.mean(axis=2)
    rows = grey.mean(axis=1)
    lo, hi = int(max(0, lo)), int(min(a.shape[0] - need, hi))
    if hi <= lo:
        return lo
    best, best_v = lo, None
    for y in range(lo, hi + 1, max(2, (hi - lo) // 120)):
        v = float(rows[y:y + need].mean())
        if best_v is None or v < best_v:
            best, best_v = y, v
    return best


def _motif_shapes(kind, cx, y0, h):
    """Polylines for one neon motif, in pixels. Line art only, to match the engine's look."""
    out = []
    if kind == "tree":
        tiers, w0 = 3, h * 0.62
        for k in range(tiers):
            w = w0 * (0.55 + 0.45 * (k + 1) / tiers)
            ty = y0 + h * (0.16 + 0.26 * k)
            out.append([(cx - w / 2, ty + h * 0.20), (cx, ty), (cx + w / 2, ty + h * 0.20)])
        out.append([(cx, y0 + h * 0.90), (cx, y0 + h)])                      # trunk
        s = h * 0.09                                                          # star on top
        out.append([(cx - s, y0 + s), (cx + s, y0 + s)])
        out.append([(cx, y0), (cx, y0 + 2 * s)])
    elif kind == "gift":
        w = h * 0.92
        l, r, t, b = cx - w / 2, cx + w / 2, y0 + h * 0.22, y0 + h
        out.append([(l, t), (r, t), (r, b), (l, b), (l, t)])                 # box
        out.append([(cx, t), (cx, b)])                                       # ribbon down
        out.append([(l, (t + b) / 2), (r, (t + b) / 2)])                     # ribbon across
        k = h * 0.20                                                          # bow
        out.append([(cx, t), (cx - k, t - k), (cx - k * 0.4, t)])
        out.append([(cx, t), (cx + k, t - k), (cx + k * 0.4, t)])
    # --- added 2026-11-07. Two motifs was not enough: the Dec 9-24 batch is eight Shorts going
    # out over sixteen days, and eight covers carrying the same tree or the same gift is the
    # "templated" look we are explicitly trying to avoid. All line art, same as the two above.
    elif kind == "star":
        import math
        r, ri, cy = h * 0.50, h * 0.20, y0 + h * 0.50
        pts = []
        for k in range(11):                       # 5 points, closed (11th == 1st)
            ang = -math.pi / 2 + k * math.pi / 5
            rad = r if k % 2 == 0 else ri
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        out.append(pts)
    elif kind == "snowflake":
        import math
        r, cy = h * 0.50, y0 + h * 0.50
        for k in range(3):                        # three full spokes = six arms
            ang = k * math.pi / 3
            dx, dy = r * math.cos(ang), r * math.sin(ang)
            out.append([(cx - dx, cy - dy), (cx + dx, cy + dy)])
        for k in range(6):                        # a V branch near the tip of each arm
            ang = k * math.pi / 3
            bx, by = cx + r * 0.62 * math.cos(ang), cy + r * 0.62 * math.sin(ang)
            for s in (+1, -1):
                a2 = ang + s * math.pi / 4
                out.append([(bx, by), (bx + r * 0.26 * math.cos(a2),
                                       by + r * 0.26 * math.sin(a2))])
    elif kind == "bell":
        # The first cut of this read as a tree: the body was a straight taper, so at 350 px it
        # was a triangle with a line under it. A bell is told apart from a tree by the FLARE -
        # the sides must bow outwards and the lip must overhang the body - so the shoulders are
        # pulled in and the skirt pushed out well past them.
        w = h * 0.86
        top, shoulder, lip = y0 + h * 0.18, y0 + h * 0.40, y0 + h * 0.74
        out.append([(cx - w * 0.12, top), (cx + w * 0.12, top),           # crown
                    (cx + w * 0.20, shoulder), (cx + w * 0.34, lip - h * 0.10),
                    (cx + w * 0.50, lip),
                    (cx - w * 0.50, lip), (cx - w * 0.34, lip - h * 0.10),
                    (cx - w * 0.20, shoulder), (cx - w * 0.12, top)])
        out.append([(cx - w * 0.50, lip), (cx - w * 0.44, lip + h * 0.09),  # the overhanging
                    (cx + w * 0.44, lip + h * 0.09), (cx + w * 0.50, lip)])  # skirt
        out.append([(cx - h * 0.09, y0 + h * 0.95),                       # clapper
                    (cx + h * 0.09, y0 + h * 0.95)])
    elif kind == "candycane":
        import math
        # No diagonal stripes: at 350 px they broke the shaft into dashes and the whole thing
        # read as a cracked line rather than a cane. The silhouette alone carries it.
        # Image y grows DOWNWARD, so the arc needs -sin: with +sin the hook bowed under the
        # shaft and the whole motif read as a figure 4.
        r = h * 0.26
        hook_cy = y0 + r
        pts = [(cx - r + r * math.cos(math.pi - k * math.pi / 16),
                hook_cy - r * math.sin(math.pi - k * math.pi / 16)) for k in range(17)]
        out.append(pts)                                                   # the hook
        out.append([(cx, hook_cy), (cx, y0 + h)])                         # the shaft
    elif kind == "heart":
        # For the Valentine's batch (2026-11-07). The classic parametric heart, sampled and
        # then normalised to the band, so it fills `h` the same way the other motifs do rather
        # than depending on the curve's own units. Image y grows downward, hence -ry.
        import math
        pts = []
        for k in range(49):
            a = k * 2 * math.pi / 48
            pts.append((16 * math.sin(a) ** 3,
                        13 * math.cos(a) - 5 * math.cos(2 * a)
                        - 2 * math.cos(3 * a) - math.cos(4 * a)))
        xs = [q[0] for q in pts]
        ys = [q[1] for q in pts]
        sx, sy = (max(xs) - min(xs)), (max(ys) - min(ys))
        s = h / sy
        midx = (max(xs) + min(xs)) / 2
        out.append([(cx + (rx - midx) * s, y0 + (max(ys) - ry) * s) for rx, ry in pts])
    elif kind == "bauble":
        import math
        r, cy = h * 0.40, y0 + h * 0.56
        out.append([(cx + r * math.cos(k * math.pi / 12), cy + r * math.sin(k * math.pi / 12))
                    for k in range(25)])                                  # the ball
        cw, ct = h * 0.16, y0 + h * 0.10
        out.append([(cx - cw / 2, cy - r), (cx - cw / 2, ct),
                    (cx + cw / 2, ct), (cx + cw / 2, cy - r)])            # the cap
        out.append([(cx - cw * 0.5, ct), (cx, y0), (cx + cw * 0.5, ct)])  # the hanger
    return out


def draw_motif(img, kind, color="#39ff88", n=3, lo=None, hi=None, scale=1.0):
    """Draw a row of neon Christmas motifs into the quietest band of the picture.

    Why this exists (Dons office, 2026-11-05): a races cover has to be taken BEFORE the gate
    opens, or the leader is visibly ahead and the cover points at a racer. But section 0 of
    every course is `pegs`, and it is tall enough to fill the frame, so a pre-gate cover cannot
    contain the course's own Christmas geometry (`tree`, `boxes`) however the seed is gated.
    Three independent blind screens at 350 px said the same thing: with the text covered up,
    nothing in the imagery says December. Frames taken deep enough to show a tree were worse -
    they leak the running order and still read as "neon outlines".

    So the shape is drawn onto the cover instead. It is line art in the engine's own style, it
    goes in a band that is actually empty (measured, not assumed), and it is honest: these
    courses really are built out of tree cascades and walls of presents.
    """
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    mh = int(h * 0.11 * scale)
    y0 = _quiet_band(a, int(mh * 1.25), lo if lo is not None else h * 0.19,
                     hi if hi is not None else h * 0.34)
    col = tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    glow = Image.new("RGB", (w, h))
    gd = ImageDraw.Draw(glow)
    kinds = [kind] * n if isinstance(kind, str) else list(kind)
    for i, k in enumerate(kinds):
        cx = w * (i + 1) / (len(kinds) + 1)
        for pts in _motif_shapes(k, cx, y0, mh):
            gd.line(pts, fill=col, width=max(5, int(h / 230)), joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    img = Image.fromarray(np.clip(a + np.asarray(glow).astype(np.float32) * 1.15, 0, 255)
                          .astype(np.uint8))
    d = ImageDraw.Draw(img)
    for i, k in enumerate(kinds):
        cx = w * (i + 1) / (len(kinds) + 1)
        for pts in _motif_shapes(k, cx, y0, mh):
            d.line(pts, fill=(255, 255, 255), width=max(3, int(h / 420)), joint="curve")
    return img


def decorate(img, text, sub=None, color="#00f0ff", out="thumb.png", anchor="top", darken=0.25,
             boost=1.25, allow_busy=False):
    """The headline treatment of make() on any picture (a frame, a collage of frames ...).

    anchor: "top" | "bottom" | "auto" (auto = the band that covers the least picture).
    """
    # punchier: lift saturation/brightness a touch, darken behind the text
    a = np.asarray(img).astype(np.float32) * boost
    h, w = a.shape[:2]

    if not text:                         # no overlay: the picture already says it
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(out)
        return out

    big = ImageFont.truetype(os.path.join(FONT_DIR, "Inter-Bold.otf"), 128)
    small = ImageFont.truetype(os.path.join(FONT_DIR, "Inter-Bold.otf"), 52)
    # shrink the headline until it fits
    fs = 128
    while big.getlength(text) > w - 80 and fs > 60:
        fs -= 6
        big = ImageFont.truetype(os.path.join(FONT_DIR, "Inter-Bold.otf"), fs)
    k = h / 720 if h > w else 1          # vertical cover: keep the text off the very edge
    if anchor == "auto":
        ty, ink = _quietest_ty(a, fs, sub)
    else:
        ty = 120 * k if anchor == "top" else h - 190 * k
        ink = _band_ink(a, ty, fs, sub)
    # STOP, don't warn (Local Operations 2026-11-12). This used to print a WARNING that nobody
    # read, and only for anchor="auto" - the FIXED anchors were never measured at all, which is
    # how BL30016's published cover came to bury two of its eight reindeer and both their names
    # behind the caption. On a pick-yours video that breaks the format: a viewer whose marble is
    # hidden cannot find it. Three more were caught by eye on option sheets in 2026-11-11/12.
    # Pass allow_busy=True (CLI --allow-busy) to overlay anyway, deliberately.
    if ink > 0.05 and not allow_busy:
        raise SystemExit(
            "thumbnail: the headline would cover the picture (worst row %.0f%% lit at y=%d, "
            "anchor=%s). Pick a less busy moment, shorten the headline, use the frame with no "
            "overlay at all, or pass --allow-busy if you mean it." % (100 * ink, ty, anchor))

    yy = np.linspace(0, 1, h)[:, None]
    if anchor == "auto":                 # darken a band centred on wherever the text landed
        t0, t1 = _text_band(ty, fs, sub)
        centre = (t0 + t1) / 2 / h
        band = np.clip(1 - np.abs(yy - centre) / 0.28, 0, 1)
    else:
        band = (1 - yy) if anchor == "top" else yy
    a *= (1 - darken * np.clip(band * 1.6, 0, 1))[..., None]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    col = tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

    glow = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(glow)
    d.text((w / 2, ty), text, font=big, fill=col, anchor="mm", stroke_width=10, stroke_fill=col)
    if sub:
        d.text((w / 2, ty + fs * 0.85), sub, font=small, fill=col, anchor="mm", stroke_width=6, stroke_fill=col)
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img = Image.fromarray(np.clip(np.asarray(img).astype(np.int32) + np.asarray(glow) * 0.9, 0, 255)
                          .astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.text((w / 2, ty), text, font=big, fill=(255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(10, 5, 20))
    if sub:
        d.text((w / 2, ty + fs * 0.85), sub, font=small, fill=(255, 255, 255), anchor="mm",
               stroke_width=4, stroke_fill=(10, 5, 20))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out)
    return out


def _title_line(d, sh, x, y, text, font):
    """Draw `text` left to right from (x, y) (y = vertical middle); emoji come from the system emoji font."""
    emoji_font = None
    size = font.size
    for ch in text:
        if ch == "\ufe0f":
            continue
        if ord(ch) >= 0x2600:
            if emoji_font is None:
                for path, sz in (("/System/Library/Fonts/Apple Color Emoji.ttc", 64),     # macOS
                                 ("C:/Windows/Fonts/seguiemj.ttf", 64)):                 # Windows (Segoe UI Emoji)
                    try:
                        emoji_font = ImageFont.truetype(path, sz)
                        break
                    except OSError:
                        continue
            g = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
            ImageDraw.Draw(g).text((40, 40), ch, font=emoji_font, embedded_color=True, anchor="mm")
            g = g.crop(g.getbbox() or (0, 0, 80, 80))
            k = size * 1.05 / max(g.size)
            g = g.resize((max(1, int(g.width * k)), max(1, int(g.height * k))), Image.LANCZOS)
            sh.paste(g, (int(x), int(y - g.height / 2)), g)
            x += g.width + size * 0.15
        else:
            d.text((x, y), ch, font=font, fill=(255, 255, 255), anchor="lm")
            x += font.getlength(ch)
    return x


def _title_width(text, font):
    return sum(font.size * 1.2 if ord(c) >= 0x2600 else font.getlength(c) for c in text if c != "\ufe0f")


def sheet(paths, out, cols=3, tile=(640, 360), title=None):
    """One contact sheet of thumbnail options, labelled A, B, C... for the owner to pick from.

    The options themselves stay as their own full-size files; this is only the picking sheet. `title` is the video's
    exact upload title, printed across the top (owner rule 2026-11-05: every thumbnail ask shows the upload title).
    """
    first = Image.open(paths[0])
    if first.height > first.width and tile == (640, 360):                 # vertical Shorts covers: portrait tiles
        tile = (360, 640)
    tw, th = tile
    pad, strip = 18, 72
    head = 92 if title else 0
    cols = min(cols, len(paths))
    rows = -(-len(paths) // cols)
    sh = Image.new("RGB", (pad + cols * (tw + pad), head + pad + rows * (th + strip + pad)), (12, 12, 18))
    d = ImageDraw.Draw(sh)
    letter = ImageFont.truetype(os.path.join(FONT_DIR, "Inter-Bold.otf"), 44)
    name = ImageFont.truetype(os.path.join(FONT_DIR, "Inter-Bold.otf"), 20)
    if title:
        tf = ImageFont.truetype(os.path.join(FONT_DIR, "Inter-Bold.otf"), 30)
        while _title_width(title, tf) > sh.width - 2 * pad and tf.size > 16:
            tf = ImageFont.truetype(os.path.join(FONT_DIR, "Inter-Bold.otf"), tf.size - 1)
        d.text((pad, pad + 12), "UPLOAD TITLE (word for word)", font=name, fill=(150, 150, 170), anchor="lm")
        _title_line(d, sh, pad, pad + 52, title, tf)
    for i, path in enumerate(paths):
        x = pad + (i % cols) * (tw + pad)
        y = head + pad + (i // cols) * (th + strip + pad)
        sh.paste(Image.open(path).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y))
        d.text((x + tw / 2, y + th + 26), chr(65 + i), font=letter, fill=(255, 255, 255), anchor="mm")
        nf = name
        while nf.getlength(os.path.basename(path)) > tw - 8 and nf.size > 11:   # fit the file name under its tile
            nf = ImageFont.truetype(os.path.join(FONT_DIR, "Inter-Bold.otf"), nf.size - 1)
        d.text((x + tw / 2, y + th + 58), os.path.basename(path), font=nf, fill=(150, 150, 170),
               anchor="mm")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    sh.save(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?")
    ap.add_argument("--sheet", nargs="+", metavar="PNG", help="tile these option files into one labelled sheet")
    ap.add_argument("--cols", type=int, default=3, help="columns on the sheet")
    ap.add_argument("--sheet-title", help="the video's exact upload title, printed across the top of the sheet")
    ap.add_argument("--at", type=float, help="frame time (s)")
    ap.add_argument("--text")
    ap.add_argument("--sub")
    ap.add_argument("--color", default="#00f0ff")
    ap.add_argument("--allow-busy", action="store_true",
                    help="overlay even where the headline would cover the picture "
                         "(normally a hard stop)")
    ap.add_argument("--anchor", default="top", choices=["top", "bottom", "auto"],
                    help="auto puts the headline on the quietest band, so it stops burying "
                         "rosters, leaderboards and puzzle tiles")
    ap.add_argument("--motif", help="draw neon Christmas line art in the emptiest band: "
                                    "tree, gift, star, snowflake, bell, candycane, bauble, "
                                    "or a comma list like tree,gift,tree")
    ap.add_argument("--motif-color", default="#39ff88")
    ap.add_argument("--race-cover", action="store_true",
                    help="DEFAULT FRAMING FOR NEW RACES SHORTS: crop the pre-gate frame tight on "
                         "the start box, measured from the frame, so the marble names are "
                         "readable at 350 px. Pass --at before gate_open_s (1.7 when the gate "
                         "opens at 2.0) and a short all-caps --text; the in-video hook band is "
                         "cropped away, so the headline carries the question.")
    ap.add_argument("--crop", help="x,y,w,h region of the source frame to use")
    ap.add_argument("--size", default="1280x720", help="output WxH, e.g. 1080x1920 for a Shorts cover")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.sheet:
        print(sheet(a.sheet, a.out, cols=a.cols, title=a.sheet_title))
        raise SystemExit
    # --text "" is allowed and means "no overlay": use the frame as it is. Intro/roster cards
    # already carry their own title, rule line and call to action, so a headline on top both
    # repeats them and buries the racers the card exists to show.
    if not (a.video and a.at is not None and a.text is not None):
        ap.error("a single thumbnail needs video, --at and --text (--text \"\" for no overlay, "
                 "or use --sheet)")
    crop = [int(v) for v in a.crop.split(",")] if a.crop else None
    size = tuple(int(v) for v in a.size.split("x"))
    if a.race_cover and not crop:
        full = grab(a.video, a.at, size=size)          # unscaled source is already 9:16 here
        crop = race_cover_crop(full)
        if crop is None:
            print("WARNING: --race-cover found no marble pile to crop to; using the full frame")
        ox = race_cover_outlier(full)
        if ox is not None:
            print("WARNING: a marble is sitting apart from the pack at about x=%d (%.0f%% across "
                  "the frame). On a pre-gate frame that is start position, not a lead - but it "
                  "READS as a breakaway. Check it is not the winner; if it is, grab a different "
                  "moment before the gate (--at) and rebuild." % (ox, 100.0 * ox / full.size[0]))
    if a.motif:
        kinds = a.motif.split(",")
        img = grab(a.video, a.at, size=size, crop=crop)
        img = draw_motif(img, kinds if len(kinds) > 1 else kinds[0], a.motif_color,
                         n=3 if len(kinds) == 1 else len(kinds))
        print(decorate(img, a.text, a.sub, a.color, a.out, a.anchor, allow_busy=a.allow_busy))
    else:
        print(make(a.video, a.at, a.text, a.sub, a.color, a.out, a.anchor, crop=crop, size=size,
                   allow_busy=a.allow_busy))
