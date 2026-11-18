"""Forest Keepers episode 9, The Harvest Feast, in the flat picture-book look (a remake of FK0005, the same story:
docs/engines/forest_keepers_harvest_feast.md, with the owner's notes; staging: docs/engines/forest_keepers_harvest_flat.md).
The world is harvest_flat_world.py.

Stateless: every frame is a pure function of time t (s), so frames render in parallel (experiments/keepers_flat/
ep9.py). Six Keepers (no Sprout yet), the new faces, the ep 14 walks.

Everything that gets moved is a Prop: where it is, how it's turned, and who holds it, as a function of t, from a list
of moves written down once (Prop.move). Hans' working tentacles are worked out from the props he holds, so a tentacle
is always exactly at the thing it carries (owner, FK0005: never a tentacle following a piece 2-3 s behind).

    plan().end                              the timeline
    frame(pg, valley, t)                    draw one frame onto a flat.FlatPage
"""
import math
import os

import numpy as np
import skia

from families.foundry.keepers.common import smoothstep
from families.foundry.products.monster import TURN_NARROW, TWIGS_FORE, TWIGS_UPPER, WHEELS_FORE, WHEELS_UPPER, two_bone

from . import harvest_flat_world as HW
from . import illustrate as il
from . import zoom_figure as ZF
from .flat_motion import (Hopper, MoleDig, Spoil, WaveGait, arm_swing, biped, hans_mood, heading, roll_swing,
                          walk_path)
from .storybook import C, mix, oval, rrect, smooth, tone, tube

W, H, K, GB = HW.W, HW.H, HW.K, HW.GB
FPS = 60
STEP = 1.0 / FPS
ORDER = ["digger", "springs", "tentacles", "teeth", "wheels", "lantern"]
WALKERS = ["digger", "springs", "tentacles", "teeth", "wheels"]
NAMES = {"teeth": "Twigs", "wheels": "Wheels", "digger": "Digs", "springs": "Springs", "tentacles": "Hans",
         "lantern": "Glo"}
GLO_TOP = 280.0                     # r9: the top of Glo's dome above his y (KH 600 put his bubbles in the sky)
KH = {"wheels": 420, "tentacles": 610, "teeth": 760, "springs": 340, "lantern": 600, "digger": 300}
HALF = {"wheels": 112, "tentacles": 118, "teeth": 92, "springs": 110, "lantern": 105, "digger": 135}
V_WALK = 95.0
EASE = 1.0

# ----------------------------------------------------------------------------------------------- narration

HOOK = ("It's autumn in the forest, and the acorns are falling. By tonight, the Keepers will build a little mill, "
        "bake their very own bread... and share a harvest feast with all their forest friends.")
LINES = {
    "bonk": "Bonk! An acorn, right on Digs' hat.",
    "idea": "And that gives Glo an idea. Acorns can be ground into flour... and flour makes bread.",
    "wheel": "The old water wheel by the brook could turn a mill.",
    "holes": "First, Digs digs two holes, for the posts.",
    "posts": "Hans stands a post in each one, and Digs pats the earth back in, nice and firm.",
    "beams": "A beam across the top, and a low one behind, to hold the millstones.",
    "roof": "And two boards for a roof, to keep the rain off.",
    "stones": "In the shallows lie two round, flat stones. Just right for millstones.",
    "dress": "Digs taps a hole through the middle, and cuts the grooves that do the grinding.",
    "gears": "Twigs cuts the corners off two square boards... and then teeth, all the way round.",
    "gears2": "One gear behind each stone. When one turns, it turns the other the other way.",
    "hopper": "A hopper on top, to pour the acorns in.",
    "belt": "Then the belt, from the water wheel to the mill. It's crossed over in the middle, so the stones both "
            "turn inwards, and pull the acorns down between them.",
    "sack": "And a sack underneath, for the flour.",
    "peg": "Springs pulls out the peg...",
    "turn": "...and the water wheel turns the mill.",
    "test": "Glo drops in the very first acorn.",
    "flour": "Flour!",
    "shake": "Now for lots more acorns. Springs bounces on the oak's low branch...",
    "catch": "...and down they drop, into the basket.",
    "pour": "Glo carries it over, and into the hopper they go, one at a time between the stones.",
    "tie": "Hans ties it up tight.",
    "home": "And off they go along the brook, home to the village, as the sun goes down.",
    "clay": "Back home, Digs digs up some clay, and Springs bounces it soft.",
    "balls": "Hans takes the soft clay, a lump at a time, and rolls each one into a ball.",
    "balls2": "Six balls of clay, one for each ring of the oven.",
    "hearth": "Hans lays a stone floor for the oven, and stones around its door.",
    "coils": "Then the clay, round and round, one coil at a time.",
    "smooth": "He smooths the coils together, into one round dome.",
    "fire": "Hans puts some dry sticks inside, and Glo's light sets them glowing.",
    "table": "While the oven warms up, it's time for a table.",
    "planks": "Twigs trims the planks all together at the stop block, so they come out the same length.",
    "lay": "And Hans lays them across two fallen logs, side by side.",
    "dough": "Now the bread. Flour, a little water... and Hans kneads it with his tentacles.",
    "loaves": "Twigs cuts the dough in four, and Hans rounds each piece into a loaf.",
    "oven_in": "Into the warm oven they go.",
    "lanterns": "While they bake, Glo lights the lanterns, one by one.",
    "baked": "And out they come, warm and golden brown.",
    "animals": "Look who smelled the bread. The birds, the bunnies, and the hedgehog, all coming out to join them.",
    "feast": "A harvest feast, for everyone.",
}
FINALE = "Goodnight, little forest."
SIGNOFF = "What should the Keepers build next? Tell us in the comments."
HOLD_END = 4.5


# How a line is spelled for the voice, where it says a word wrong as written (FK0021: "Flour!" came out "floor").
# The script, the captions and the .srt keep the written words; only the voice gets the respelling.
SPOKEN = {"Flour!": "Flower!"}


def voiced(text):
    from .narrator import take
    return take(SPOKEN.get(text, text))


def _dur(text):
    return voiced(text)["duration"]


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-9), 0.0), 1.0)


def ease(t, a, b):
    return smoothstep(_seg(t, a, b))


def lerp(a, b, u):
    return a + (b - a) * u


def lerp2(p, q, u):
    return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)


def ramp_int(t, t0, dur, w):
    """The angle turned by something that speeds up smoothly from rest at t0 to w per s over dur s."""
    if t <= t0:
        return 0.0
    if t < t0 + dur:
        u = (t - t0) / dur
        return w * dur * (u ** 3 - 0.5 * u ** 4)
    return w * dur * 0.5 + w * (t - t0 - dur)


class Split:
    """A gait before the act break and another after it (each from its own path), so no foot is planted across the
    cut."""

    def __init__(self, a, b, tc):
        self.a, self.b, self.tc = a, b, tc

    def __getattr__(self, k):
        attr = getattr(self.a, k)
        if not callable(attr):
            return attr

        def f(*args, **kw):
            t = args[-1] if args else kw["t"]
            return getattr(self.a if t < self.tc else self.b, k)(*args, **kw)
        return f


class Multi:
    """Springs' hopping in segments (split at each big jump and the act break): each its own Hopper."""

    def __init__(self, segs):
        self.segs = segs

    def state(self, t):
        for b, h in self.segs:
            if t < b:
                return h.state(t)
        return self.segs[-1][1].state(t)


class Dig(MoleDig):
    """A MoleDig whose strokes start at t_start (flat_motion's counts strokes from long before: Spoil throws soil
    for all of them, so a dig late in the episode grew a heap hundreds of px high)."""

    def flicks(self, sx, t0, t1, at=None):
        return super().flicks(sx, max(t0, self.t0), t1, at)


CLAY_PUSH = (0.0, -400.0)           # (up: the heap lands where the higher fling put it, x ~3450)
CLAY_THROW_L = 0.15                 # r23 (part 2 must-fix: the left heap grew on the bunny house's doorstep, x
                                    # ~2920): the left paw's clay lands short, between the house and the pit


class LowDig(Dig):
    """r7 (part 2 must-fix: "he digs the clay by swinging his arms out sideways at shoulder height, claws in the air;
    the hole forms where no claw touches"): the same stroke kept low - down and in to the hole, scrape out along the
    ground and flick the clay off beside him, never up past the level of his belly."""
    KEYS = [(0.0, 0.80), (0.3, 1.95), (0.45, 2.12), (0.82, 0.95), (1.0, 0.80)]


class FlungSpoil(Spoil):
    """Spoil flung out sideways and up a bit harder (push = (out, up) added to the paw's velocity): LowDig's flick is low and slow, so the clay would
    land right beside him, where the oven goes; this keeps the heap where it was (r7)."""

    def __init__(self, *a, push=(0.0, 0.0), throw=None, **kw):
        super().__init__(*a, **kw)
        throw = throw or {}                                        # r23: {side: factor} on the sideways speed
        self.flights = [f[:6] + ((f[6] + f[1] * push[0]) * throw.get(f[1], 1.0), f[7] + push[1]) + f[8:]
                        for f in self.flights]
        self.landed = [(f, f[3] + self._fall(f)) for f in self.flights]
        for sx in (-1, 1):
            xs = [self._fly(f, tl)[0] for f, tl in self.landed if f[1] == sx and f[0].endswith(".0")]
            self.cx[sx] = sum(xs) / len(xs)


HOLE_L_THROW = 0.78                 # r21: the left hole's outer clods fly this much (its pile left of the brake post)


class SideSpoil(Spoil):
    """Spoil whose throw is scaled per side (throw={sx: factor} on the clods' sideways speed). The two post holes
    are only 280 px apart and the paw lets go 142 px out, so a full throw landed in the other hole (owner, FK0021:
    "he shoves the dirt directly back into the hole he just dug"). Between the holes the soil is set down right at
    the end of the stroke, one shared pile clear of both holes; outside it is thrown as before."""

    def __init__(self, *a, throw=None, **kw):
        super().__init__(*a, **kw)
        if throw:
            self.flights = [f[:6] + (f[6] * throw[f[1]],) + f[7:] for f in self.flights]
            self.landed = [(f, f[3] + self._fall(f)) for f in self.flights]
            for sx in (-1, 1):
                xs = [self._fly(f, tl)[0] for f, tl in self.landed if f[1] == sx and f[0].endswith(".0")]
                self.cx[sx] = sum(xs) / len(xs)


# ----------------------------------------------------------------------------------------------- props

def soft_fall(u, a=0.7):
    """A fall (u^2) whose last part eases to rest (a soft landing: leaves in the basket), smooth all the way."""
    if u <= a:
        return u * u
    s_ = (u - a) / (1 - a)
    h00, h10, h01 = 2 * s_ ** 3 - 3 * s_ ** 2 + 1, s_ ** 3 - 2 * s_ ** 2 + s_, -2 * s_ ** 3 + 3 * s_ ** 2
    return h00 * a * a + h10 * (1 - a) * 2 * a + h01


def sack_pivot(q, fill):
    """The sack's right foot: it tips about it (world)."""
    return q["x"] + (34 + 18 * fill) * 0.92, q["y"]


def sack_pt(q, fill, dx, dy):
    """The point (dx, dy) from the sack's foot middle, tipped with it (world)."""
    a = math.radians(q.get("tip", 0.0))
    px, py = sack_pivot(q, fill)
    rx, ry = q["x"] + dx - px, q["y"] + dy - py
    return px + rx * math.cos(a) - ry * math.sin(a), py + rx * math.sin(a) + ry * math.cos(a)


class Prop:
    """A thing that gets moved: a list of moves, each (t0, t1, pose0, pose1, how, lift, holder, fn). Its pose is a
    dict (x, y, ang, plus anything its drawing needs: face, tilt, fill...). born/gone: when it exists."""

    def __init__(self, name, kind, z, size, born=-1e9, **pose):
        self.name, self.kind, self.z, self.size = name, kind, z, size
        self.p0 = dict(pose)
        self.p0.setdefault("ang", 0.0)
        self.moves = []
        self.born, self.gone = born, 1e9
        self.why_born = None
        self.why_gone = None

    def end_pose(self):
        return dict(self.moves[-1][3]) if self.moves else dict(self.p0)

    def move(self, t0, t1, how="ease", lift=0.0, holder=None, fn=None, **pose):
        p0 = self.end_pose()
        p1 = dict(p0)
        p1.update(pose)
        self.moves.append((t0, t1, p0, p1, how, lift, holder, fn))
        return t1

    def follow(self, t0, t1, fn, holder=None):
        """Its pose is fn(t) (a dict) from t0 to t1 (it ends where fn(t1) is)."""
        p1 = dict(self.end_pose())
        p1.update(fn(t1))
        self.moves.append((t0, t1, self.end_pose(), p1, "fn", 0.0, holder, fn))
        return t1

    def at(self, t):
        """(pose, holder or None, moving or not). Each move starts from where the one before really ends now (a
        move planned to follow something is evaluated when drawn, so a later change in the plan, such as Hans
        stepping in to reach, never leaves the next move starting from a stale place)."""
        cur = self.p0
        for t0, t1, p0, p1, how, lift, holder, fn in self.moves:
            p0 = dict(p0, **{k_: v_ for k_, v_ in cur.items() if k_ in p0}) if cur is not self.p0 else p0
            if t < t0:
                return cur, None, False
            if t < t1:
                if how == "fn":
                    q = dict(p0)
                    q.update(fn(t))
                    return q, holder, True
                u = (t - t0) / max(t1 - t0, 1e-9)
                if how == "ease":
                    e = smoothstep(u)
                elif how == "lin":
                    e = u
                elif how == "fall":                                # from rest, gravity: y follows u^2
                    e = u
                else:
                    e = 1.0 if how == "jump" else smoothstep(u)
                q = {}
                for k_, v in p1.items():
                    a = p0.get(k_, v)
                    if isinstance(v, (int, float)) and isinstance(a, (int, float)):
                        q[k_] = a + (v - a) * e
                    else:
                        q[k_] = v if e >= 0.5 else a
                if how == "fall":
                    q["y"] = p0["y"] + (p1["y"] - p0["y"]) * u * u
                elif how == "fall_soft":                           # falls, and is caught softly at the end
                    q["y"] = p0["y"] + (p1["y"] - p0["y"]) * soft_fall(u)
                if lift:
                    q["y"] -= lift * math.sin(math.pi * e)
                return q, holder, True
            if how == "fn":                                        # where the followed thing really is at its end
                cur = dict(p0)
                cur.update(fn(t1))
            else:
                cur = p1
        return cur, None, False

    def alive(self, t):
        return self.born <= t < self.gone

    def holder_at(self, t):
        return self.at(t)[1]


# ----------------------------------------------------------------------------------------------- Twigs' cuts

def _bones_ok(sh, hd, sx, k=None):
    """Twigs' arm reaching hd keeps both bones at their length (no elbow swung through the arm's own line)."""
    k = K if k is None else k
    el = two_bone(sh, hd, TWIGS_UPPER * k, TWIGS_FORE * k, sx, (0.4 * sx, 1.0))
    return min(math.dist(sh, el) / (TWIGS_UPPER * k), math.dist(el, hd) / (TWIGS_FORE * k)) > 0.97


def cut_pose(tx, notch, y_mid, sx=-1, slant=None, band=15.0, v_at=0.55, tip_max=None, smax=0.0, sback=0.0,
             kerf=False):
    """Twigs' hand (standing at tx) for a cut: his blade (straight on from his forearm, as monster.py draws it)
    crosses the notch line at y_mid, slanting down and in like a pruning saw. -> (hand, blade direction)."""
    k = K
    sh = (tx + sx * 82 * k, GB - 350 * k + 10 * k)

    def safe(hd):                                                  # well inside the side his elbow stays on
        return math.degrees(math.atan2(sx * (hd[0] - sh[0]), hd[1] - sh[1])) < band
    best = None
    for hx in np.linspace(notch - 90, notch + 90, 91):
        for hy in np.linspace(y_mid - 150, y_mid + 30, 91):
            hd = (hx, hy)
            if math.hypot(hd[0] - sh[0], hd[1] - sh[1]) > (TWIGS_UPPER + TWIGS_FORE) * k * 0.97:
                continue
            el = two_bone(sh, hd, TWIGS_UPPER * k, TWIGS_FORE * k, sx, (0.4 * sx, 1.0))
            ux, uy = hd[0] - el[0], hd[1] - el[1]
            L = math.hypot(ux, uy) or 1.0
            ux, uy = ux / L, uy / L
            if uy < 0.55 or not all(safe((hd[0] - 0.3 * q * sx, hd[1] + 0.95 * q)) for q in (-3.0, 0.0, 15.0)):
                continue
            if sback and not all(safe(p_) and _bones_ok(sh, p_, sx) for p_ in              # r25: his strokes draw
                                 ((hd[0] + ux * q, hd[1] + uy * q) for q in np.linspace(sback, 0.0, 6))):   # back
                continue                                           # along the blade: the elbow stays out all the way
            nx, ny = -uy, ux
            if nx * sx < 0:
                nx, ny = -nx, -ny
            base = (hd[0] + ux * 6 * k + nx * 13 * k, hd[1] + uy * 6 * k + ny * 13 * k)
            tip = (base[0] + ux * 64 * k, base[1] + uy * 64 * k)
            if not (min(base[0], tip[0]) + 6 < notch < max(base[0], tip[0]) - 6):
                continue
            v = (notch - base[0]) / (tip[0] - base[0])
            yc = base[1] + (tip[1] - base[1]) * v
            # r25 (part 3 must-fix "his blade passes straight through the sawhorse's top board"): the drawn tip (its
            # rounded end and outward bend too) at the bottom of the longest stroke stays above tip_max
            if tip_max is not None and tip[1] + uy * (6.5 + 0.0) * k + ny * 8 * k + uy * smax > tip_max:
                continue
            err = abs(yc - y_mid) + 8 * abs(v - v_at)
            if kerf:                                               # r29 (round 28 part 3 must-fix "two big pieces,
                xk_ = base[0] + (y_mid - base[1]) * ux / uy        # two slivers"): the kerf itself (the blade's line at
                err = 3 * abs(xk_ - notch) + 0.3 * abs(yc - y_mid) + 8 * abs(v - v_at)   # y_mid) on its mark
                if slant is not None and abs(ux / uy - slant) > 0.12:   # and the cuts parallel
                    continue
            tot = err + (30.0 * abs(ux / uy - slant) if slant is not None else 0.0)   # at this slant (dx/dy): the
            if err < 12 and (best is None or tot < best[3]):                        # dough's cuts run parallel
                best = (err, hd, (ux, uy), tot)
    assert best is not None and best[0] < 12, f"Twigs cannot cut at {notch}, {y_mid}"
    return best[1], best[2]


# ----------------------------------------------------------------------------------------------- the plan

# where everyone stands (the mill)
MILL = dict(digger=560.0, springs=400.0, tentacles=1580.0, teeth=1990.0, wheels=2150.0)   # (r31: Twigs and Wheels
# further right, was 1958/2120: with the right post at 1555 Hans needs room between Digs at that hole and Twigs;
# Twigs steps up to the rack, TW_MILL, before his first cut)
CAM_MILL = 1281.0                   # the mill shot: Springs by the oak to Wheels past the rack
CAM_OAK = 1100.0                    # the oak and its branch, the basket under it (Springs shakes the acorns down)
GLO_HOME = 690.0                    # Glo floats beside Digs (clear of his hat: the bonk is seen, FK0021 note)
CATCH_DY = 82.0                     # how far down Glo comes to catch the acorn off Digs' hat
CRUISE = 160.0
BELT_LEAD = 75.0                    # r36: Glo holds the belt this far back from its end as he takes it to the pulley
GLO_HOLD = -95.0                    # from Glo's y up to where his tendrils hold things
ACORN_FALL = 2.0                    # r35: each acorn falls this many times a free fall's time (was 1.15: ~0.8 s)
DIGS_BASKET_CLEAR = 170.0           # r35: Digs stands at least this far right of the basket while the acorns drop
ACORN_ZOOM = (1.65, 520.0, 612.0)   # r35: the shot on the acorns dropping into the basket (was 1.4 on 520, 592)
ACORN_S = 1.45                      # the acorns' size (FK0021 note: "the acorns are very tiny")
HOOK_ACORN_S = 2.4                  # the one that bonks Digs, bigger still (part 1 review: "still tiny")
BONK_FALL = 1.05                    # r30: the hook acorn's fall (s): followable, about a second
BONK_ZOOM = 2.25                    # r30: the push-in for that fall and the hit (squirrel's paws to Digs' eyes)
GLO_WAIT_X = 860.0                  # r16: where he waits while the acorns are shaken down (beside Digs, under the belt)
GLO_CLEAR_X = 1780.0                # where Glo waits with the empty basket while the mill grinds (between Hans and
                                    # Twigs, clear of the stones)
TW_MILL = 1960.0                     # (r31: was 1958; his blade just reaches the blanks' rim from here)
POST_LEAN = 76.0                     # r9: a post is carried leaning (foot up), stood upright only over its hole
POST_HANS = dict(R=1780.0)          # r8: where Hans stands to hold post R up (about 230 px from it; for L his step in
                                    # with HANS_REACH_POSTS brings him close)
FILL_LEFT = 30.0                    # r8: Digs fills each hole from a little to its left, clear of Hans
# r18 (part 1 must-fix "no earth is ever put back"): Digs walks each hole's left pile in ahead of his paws, Hans
# walks the right pile in ahead of his front tentacle tips, then Digs steps up and pats it down
PAW_PUSH = 114.0                    # Digs' paw ahead of his middle as he shoves a pile along (his paw at ~25 degrees)
PAW_GAP = 40.0                      # the pile's back from the paw's middle (the paw against it, not on top of it)
PUSH_S = 3.2                        # how long Digs takes to shove the left pile into the hole
HANS_TOE = 115.0                    # Hans' leftmost tentacle tip, standing, left of his middle (the gait's feet)
PATS = 2
PAT_X = 40.0                        # Digs pats the filled hole this far left of the post (its near side)...
CLAY_FILL_DY = 40.0                 # r26: the left clay pile comes forward/down this much onto the pit as it's shoved
CLAY_FILL_DA = 18.0                 # ...and Digs' shoving paw this much lower with it (degrees)
PAT_STAND = 160.0                   # ...standing this far left of it, where his shove ends (his arm reaches down to
                                    # it there; his body clear of the post's foot)
HANS_CLEAR_TW = 215.0               # Hans' middle stays this far left of Twigs' (walk_through)
HANS_REACH_POSTS = 205.0             # r8: tighter while he stands posts and hangs the millstones ("his tentacle
                                    # stretches to about twice his height": 240-295 px there)
POSTS_FX = 23.0                     # r36: the posts shot's middle, right of halfway between the posts
POST_STAND = 165.0                  # r21: where he stands to lower a post into its hole (right of it) (r36, round 35 part 1 must-fix "the post goes in behind his legs": 100 -> 165, his left toes clear of the hole)
POST_V = 140.0                      # ...and how fast he takes post L over (one walk of about 4 s, not two)
POST_GRIP = (100.0, 0.0)            # r19 (part 1 must-fix: the post behind his head, the tentacle across his face):
                                    # he holds a post above his head, where it shows (both behind him)
POST_GRIP_LOW = (35.0, 0.0)        # r36: ...and lower down it as he stands it in its hole (in reach from POST_STAND)
STONE_GRIP = (0.0, -HW.STONE_R + 4.0)   # r19 (part 1 must-fixes "the stone floats, no tentacle on it"): he holds a
                                    # millstone by the top of its rim (it was 30 px in, his tip hidden behind its face)
GEAR_DEMO_STAND = 250.0            # r33: 250 with the gears right behind the stones. Was 300.0            # (r31: 300 with the gears 200 back; r30: +40 with the gears set back) r25: Hans stands this far right of the right gear to turn it (clear of it; 225:
                                    # right where he lifts the far stone from next, no shuffle step in between)
GEAR_DEMO, GEAR_DEMO_T = 90.0, 3.6   # r19: the mounted gears turned by hand to show the mesh: two teeth, slowly
STEADY_AT = 125.0                   # r19: his steadying tentacle on the blank's lower left rim (was 255, the top, where
                                    # each fresh notch went under it two turns later)
HANS_REACH = 210.0                  # how far his working tentacles reach from his middle (about a leg past his body)
CUT_MILL = None                     # filled in the plan (cut_pose)
TEETH = 8
GEAR_MESH_OFF = 22.5                # r38: half a pitch, measured (0 px overlap all the way round; 0 deg overlapped 373 px,
                                    # notch facing notch: round 37 part 1 must-fix). r37 had tried 0 for round 36's "tooth on tooth"
GEAR_REST_PH = 11.25                # r41 (round 40 part 1 must-fix "the teeth point straight at each other, tip to
                                    # tip"): they never did (each sits in the other's notch), but at rest the tooth in the nip
                                    # lay level along the low beam behind it, the two reading as one bar from gear to gear.
                                    # A quarter pitch on, +left / -right (still meshed: mirror images), it sits on a slant.
BLANK = 84.0                        # r34 (round 33 part 1 must-fix "the teeth butt tip to tip and slide over each
                                    # other"): 88 -> 84, each tip 4 px clear of the other gear's notch floor (with NOTCH_D 32
                                    # the root stays at 52; at 88 the tips touched it). r33 (round 32 must-fixes "gears not on the stones' axles", "uneven teeth"): 88, teeth
                                    # 20 px past the stone's rim all round, the gear right behind it on its axle. Was: BLANK = 80.0                        # (r27: 74 -> 90 with GEAR_R 70 -> 86; r28: 80, blocky teeth that mesh at the axles 140 apart) half the side of a square gear blank (a board), its corners cut off
GEAR_CUT = (1886.0, 834.0)          # where Twigs' blade cuts the gear blanks (the blank's right rim)
CORNER_CUT, TOOTH_CUT = 1.5, 1.3    # how long each corner and each notch takes to saw (three strokes; r17: was 0.9,
                                    # too quick to see)
CORNER_GAP, TOOTH_GAP = 2.4, 2.0     # r19 (part 2 must-fix "the notch never reads as cut where the blade touches"):
TURN_OUT, TURN_STILL, TURN_IN = 0.35, 0.35, 0.35   # between cuts the blade comes out of the cut, the blank holds still
                                    # (the fresh notch / cut corner shows at the blade), turns, holds, the blade goes in
OFFCUT_LAND = [1838.0, 1858.0, 1876.0, 1850.0]   # r42: where the cut-off corners land, flat, left of Twigs' feet
OFFCUT_Y = 926.0                    # ...on the path, nearer us than the held board's foot (918), so drawn over it
CHIP_LAND = [1866.0, 1880.0, 1842.0, 1872.0, 1856.0, 1885.0, 1834.0, 1862.0]   # ...and the tooth gaps' wedges
NOTCH_HAND = (1885.0, 823.0)        # r21: Twigs' hand while a gear notch is sawn: the blade (as his arm draws it) in the
NOTCH_S1 = 6.0                      # notch, teeth on its floor, not the mount (inside his elbow's safe band); strokes (px)
BLADE_OUT = (40.0, -6.0)            # how far his hand draws the blade back out of the cut (world px, away from the rim)
V_TURN = 0.8                        # r17 (part 2 must-fix "the notches appear where the blade isn't"): his blade meets
                                    # the blank's rim near its tip, his fist clear of the notch being cut (was 0.55)
BEAM_HX = 1320.0                    # Hans stands in front of the mill to lay the beams (in his reach)
BRANCH_HOP_T = 1.25                 # r29: Springs' one bounce over Digs and up onto the oak's branch (s)
BRANCH_HOP_OVER = 260.0             # ...its arc's rise above the straight line up to the branch (px)
SHAKE_X = 400.0                     # Springs hangs from the oak's branch here
GLO_OVER_HOPPER = -150.0            # Glo rises this much to hold things over the hopper
GLO_PEG_X = 520.0                   # where Glo watches the wheel start: left of its rim, clear of it (r4)
DIGS_ROOF = 900.0
DIGS_WATCH = 700.0                  # Digs watches the milling from here (clear of the basket and the brake post)
BASKET_HANG = 62.0                  # the basket's bottom below Glo's tendrils
BASKET_DY = HW.BASKET_HOME[1] - (GB - CRUISE + GLO_HOLD + BASKET_HANG)   # how far Glo comes down to take it
BASKET_GLO_X = HW.BASKET_HOME[0] + 8.0   # Glo comes down for the basket right over it
BASKET_START = 745.0                # r45: where the basket waits at 0:00 (open grass right of Digs, in view)
BASKET_LIFT = 22.0                  # r45: how high Glo lifts it carrying it over under the oak's branch
UNDER_DY = -100.0                   # ...this far up, so the acorns drop only a little way into it
BELT_ZOOM = 1.8                     # r29: the belt's medium shot (the wheel's hub and the stone's pulley both in it)
PEG = (HW.BRAKE_X, HW.BRAKE_TOP)    # the brake peg in its post (world)
PEG_KNOB, PEG_SHANK = 18.0, 30.0    # r13: the peg's knob above the post top, and its shank in the post
PEG_HOP = 44.0                      # r13: Springs' little hop that pulls the peg out (more than its shank)
PEG_DROP = 0.5                      # r13: he lets it fall to the path as he lands (s after the pull)
PEG_COL = (196, 160, 112)           # r13: pale, so it never reads as part of the dark post
SPRINGS_PEG_X = HW.BRAKE_X - 100.0 * K - 26.0

# where everyone stands in the village (the same order as at the mill: nobody passes anybody on the path)
# r21 (part 2 must-fix "Hans walks straight into the log stack", his legs between its two logs): he stops left of
# the stack (it starts at about 3960), the sack at his right
VIL = dict(springs=2780.0, digger=3170.0, tentacles=3860.0, teeth=4980.0, wheels=5300.0, lantern=3440.0)
CAM_V = 4250.0
GLO_TABLE_X = 4230.0                # r33: Glo waits here (at his cruising height) while the table and the bread are made
CAM_OVEN = 3720.0                   # the oven build: the oven, Digs' clay and Hans in the middle of the frame
CAM_HOUSES = 3150.0
SACK_V = (4070.0, HW.FLOOR - 2)     # (clear of Digs' paws as he digs the clay)
CLAY_V = 3170.0                     # r15: Digs' clay pit, left of the oven's place (its heap lands at ~3420)
MOUNT_GRIP = ((HW.STONE_R - 5.0) * math.cos(math.radians(-55.0)), (HW.STONE_R - 5.0) * math.sin(math.radians(-55.0)))
                                    # r31: by the right rim (where it was turned from, RIM_A; r33: its upper right)
MOUNT_ZOOM = (1.8, 1420.0, 790.0)   # r31: the view while a dressed stone is lifted onto its axle (zoom, world x, screen y)
MOUNT_STAND = (222.0, 170.0)       # r34 (round 33 part 2 must-fix "stone 1 rises onto its axle behind Hans' body,
                                   # no tentacle seen"): 170 -> 222 for stone 1, his body and fin clear of its path (stone 2 is lifted on in the
                                   # close mount view, from 170: further out, its lift walked him back in). r31: Hans stands this far right of a stone's axle to lift it on (his body clear
                                   # of its rim; he keeps the right-rim grip he turned it by, so it stays in reach)
DRESS_ZOOM = (2.05, 1370.0, 805.0)  # r29: the closer view while a stone is dressed (zoom, world x, screen y)
DRESS_BACK = 0.45                   # Digs' claw goes back from the turned groove to the eye over this (s)
GROOVE_AT = -102.0                  # the screen angle each groove is cut at (r8: up from the eye, so it lies on the circle
                                    # his claw tip sweeps round his shoulder: the tip is exactly where the groove grows)
DRESS_HANS = 1540.0                  # r9: Hans stands here while Digs dresses a stone (legs clear of it) (r33: 1560 -> 1540;
                                     # he stayed at 1505 - the stone + STONE_SIDE - with his legs over its right half,
                                     # hiding the turned grooves; now he steps back out to here and holds the rim's upper
                                     # right, RIM_A, at arm's length: the furthest out his reach allows)
DRESS_STAND = 207.0                 # r8: Digs stands this far left of the stone while dressing it (claw tip reaches the groove)
                                    # (r32, round 31 part 2 must-fix "the hole pops in where the claws aren't": 216 -> 207,
                                    # so his claw tip reaches the eye's true middle, his arm's length from his shoulder)
RIM_A = -55.0                       # r14: Hans grips the stone's rim here (screen deg) to turn it (r33: -2 -> -55, its
                                    # upper right: within his reach from where his legs are clear of the stone's face)
DIGS_TIP = (177.0 * K, 5.0 * K)     # his centre claw tip from the shoulder along / across the arm (monster._mole_paw)
DIGS_OVEN = 3010.0                  # Digs watches the oven being built from here (r12: by his clay pit, well left of
                                    # the heap and of Hans; at 3330 he hid the heap, at 4010 Hans walked through him;
                                    # r42: 3060 left a claw at the edge of the oven close-up for two minutes; he stays
                                    # where he shoved the clay back, 3010, no shuffle)
SPRINGS_OVEN = 2640.0               # ...and Springs a step further left (r12: at 3040 he stood in Digs' spot; r26: 2780 was where Digs
                                    # stands to shove the clay back into his pit)
DIGS_CARRY_HOME = 3520.0            # Digs out of Springs' way while he bounces the heap soft
DIGS_TAKE = 3420.0                  # Digs scoops a lump off the soft heap from here...
DIGS_GIVE = 3680.0                  # ...and holds it up for Hans here
OVEN_BASE_Y = HW.FLOOR - 48.0       # the dome's foot, on the hearth slab
OVEN_MOUTH = (HW.OVEN_X, HW.FLOOR - 72.0)
GLO_FIRE_DX = -140.0                # r26: Glo lights the fire from beside the door; r27 (part 2 must-fix "his body hides
                                    # the door as the sticks catch"): off to its left, clear of the opening...
GLO_FIRE_LAMP_Y = HW.FLOOR - 86.0   # ...his lamp level with the opening (it was over the dome)
DOOR_HW, DOOR_TOP = 46.0, HW.FLOOR - 112.0   # the door: half its width, its top (owner, FK0021: the bread went in
                                             # through the clay wall; the door now takes the peel and its loaves)
OVEN_V = (150.0, 30.0)              # (r16: 30 down, was 64) from the peel's blade (in the door) to Glo's tendrils: the handle slants out and
                                    # down to his lower right, so he holds it clear of the oven's front
B_OUT = (HW.OVEN_X, HW.FLOOR - 58.0)  # the blade just in front of the door, its loaves all inside the opening (round
                                      # 4: level with the door, never over the hearth); it goes in 24 px (higher)
G_OUT = (B_OUT[0] + OVEN_V[0], B_OUT[1] + OVEN_V[1])   # Glo's tendrils then
PUSH = 14.0                         # r16: in through the door this far up (the loaves' tops reach the arch)
OVEN_LOW = 36.0                     # r16 (part 3 must-fix: the loaves slid sideways across the door's right
                                    # pillar): carried this much lower, under the dome's foot, then pushed up and in
NEAR_DY, NEAR_SC = 78.0, 0.1  # r33 (round 32 part 3 must-fixes "the loaves slide sideways across the right pillar",
                                    # in and out): 78 lower - the bread crosses on the path below the oven's foot stones,
                                    # clear of all of it, lines up under the door, then rises straight up and back into
                                    # it (a step nearer is lower and bigger); out the same way. Older notes:        # r22 (part 3 must-fix: the loaves slid sideways across the door's right jamb,
                                    # in and out): beside the oven the bread is held nearer us - this much lower and
                                    # bigger - comes across in front of the door like that, then up and back into it
GLO_OVER_MILL = -500.0              # r13: how far Glo rises to cross over the mill's roof
GLO_OVER_HANS = 150.0               # r13: how far Glo rises to float over Hans' head with the bread


def door_rect(sh):
    """The door: the opening the jambs and lintel frame, its sill straight (r37, round 36 part 2: with the bottom
    corners rounded too the coils seen through it read as a dark bowl). r40 (round 39 part 2 must-fix "the doorway
    changes shape from a rectangle to a rounded arch with no visible action"): its top corners only a little rounded,
    so it's the stones' own rectangle before the clay goes round it and after."""
    rr = skia.RRect()
    rr.setRectRadii(skia.Rect(OVEN_MOUTH[0] - DOOR_HW - sh, DOOR_TOP, OVEN_MOUTH[0] + DOOR_HW - sh, HW.FLOOR - 46),
                    [skia.Point(5, 5), skia.Point(5, 5), skia.Point(0, 0), skia.Point(0, 0)])
    p = skia.Path()
    p.addRRect(rr)
    return p
STICKS = (3930.0, HW.FLOOR - 6.0)   # (in his reach from beside the dome: round 4)
STICK_PILE_STAND = 3830.0           # r33: Hans stands here to pick a stick off the pile (all three in his reach)...
STICK_DOOR_STAND = 3745.0           # ...and here to put it in through the oven's door (a step apart, 85 px)
STICK_HOLD = (-115.0, GB - 115.0)   # r33: a stick held low beside him, clear of his face (x from his middle; world y)
# r27 (part 2 must-fix "the stones travel behind his body, none is seen held"): the pile lies on the path in front
# of the oven's place, left of his feet (the same stack, 87 px nearer; clear of the lumps' slab), and each stone is carried low in front of his legs, drawn in front
# of him, and set in its place; they go back to the oven's layer once he's stepped clear (to `HANS_COIL`)
STONE_PILE_DY = 87.0
# r41 (round 40 part 2 must-fix "the bench top floats once its posts are taken"): no bench any more but a neat stack
# that he takes from the top down, in the order he builds: the round stones on top (the top one first), then the
# slab, then the two posts lying flat (ang 90), with the lintel at the bottom on the ground. Nothing he leaves
# behind ever stands on something he has taken.
STONE_GROUND = HW.FLOOR + 91.0
OVEN_STONES = [("base stone 0", "rock", (3650.0, STONE_GROUND - 92), (HW.OVEN_X - 62.0, HW.FLOOR - 16)),
               ("base stone 1", "rock", (3616.0, STONE_GROUND - 72), (HW.OVEN_X, HW.FLOOR - 18)),
               ("base stone 2", "rock", (3684.0, STONE_GROUND - 72), (HW.OVEN_X + 62.0, HW.FLOOR - 16)),
               ("hearth slab", "slab", (3650.0, STONE_GROUND - 47), (HW.OVEN_X, HW.FLOOR - 40)),
               ("jamb L", "jamb", (3620.0, STONE_GROUND - 28), (HW.OVEN_X - 58.0, HW.FLOOR - 80)),
               ("jamb R", "jamb", (3680.0, STONE_GROUND - 28), (HW.OVEN_X + 58.0, HW.FLOOR - 80)),
               ("lintel", "lintel", (3650.0, STONE_GROUND - 9), (HW.OVEN_X, HW.FLOOR - 122))]   # (piled in his reach, at his right foot: r4;
               # r26: 20 px nearer him, he stands nearer the oven)
OVEN_STONE_NAMES = tuple(s_[0] for s_ in OVEN_STONES)
STONE_LOW_Y = 888.0                 # r26 (part 2 must-fix: the lintel across his face, the slab across his body, then
                                    # behind him on the oven): each goes from the pile to the oven low behind his legs,
                                    # on the oven's layer the whole way (never in front of him)
HANS_TABLE = 4780.0
HANS_TABLE_MIN = 4300.0
STACK_DX, STACK_Y = 70.0, 862.0     # the plank stack, held up in front of Hans as he deals them out (r8: on his right,
                                    # away from where he lays them, so he can stand close: his tentacle stretched 286 px)
PLANK_HX = [4210.0, 4330.0, 4450.0, 4570.0, 4690.0, 4690.0]   # where he stands to lay plank k (r8: slot + 170;
                                    # the last clear of Twigs)
HANS_OVEN = 3790.0                  # just right of the oven: he works it from the side
PULLEY_LOW_Y = 885.0               # r22: Hans carries the pulley this low (below his face, in front of his legs)
STONE_FWD_Y = 830.0                # r23: a stone comes forward to this height (r31: where it lay, left of the left post),
                                   # then is walked right in front of the frame
STONE_LIFT = (2.2, 30.0, 2.0)      # r35: up out of the water (s, px), then over to the bank (s)
STONE_GRIP2 = (HW.STONE_R * 0.8, HW.STONE_R * 0.45)   # r35: his second tentacle round its near (right) rim
GEAR_CARRY_Z = 5.3                  # r36 (round 35 part 1 must-fix "the gear passes behind the right post while his
#                                   # tentacle holding it is in front"): carried, over the posts' layer (5; was 4.9)
STONE_POST_CLEAR = 14.0            # r36: a stone comes forward only this far clear of the left post (its middle)
STONE_LOW_DY = 40.0                # r22: stone 2 is carried this much nearer than where it lay (clear of Hans' fin)
STONE_SIDE = 250.0                 # r46 (round 45 part 1 must-fix: the stone was tipped up behind his left fin): 175 -> 250. r10: Hans stands this far right of a stone in the shallows to lift it
HOME_SHOT = 6.2                     # r33 (round 32 part 2 must-fix "nobody sets off"): 6.2 with the camera following (was 4.8)
HOME_PAN = 0.7                      # r33: the camera follows the walk home at this share of their pace, so the mill slides
                                    # away behind them while they still walk across the frame
_HOME_SHOT_OLD = 4.8                     # r20 (r23: 3.8, was 3.4): the set-off home is seen this long, then the dip
                                    # (r32, round 31 part 2 must-fix "they stay standing at the mill": 4.8 s, the front
                                    # ones walking out of shot, and the light only starts to go once they're on their way)
HOME_WALK, HOME_V = 420.0, 180.0   # r10 (r23: 180, was 140): the set-off home along the brook (px, px/s; r21 part 2 must-fix
                                    # "nobody sets off": 100 read as standing still in the wide shot)
BREAD_HOLD, BREAD_ZOOM = 2.2, 2.5   # r10: the golden loaves held close at the oven mouth (s, zoom)
ROOF_FRONT = 50.0                  # r10: the roof stands this much nearer than the frame (on the path)
HOPPER_SIDE = 145.0                 # r26 (part 2 must-fix: 175 stretched his tentacle up to the beam) r11: Hans stands this far right of a hopper board's low end to put it up
HANS_ROOF_L = 1550.0                # Hans stands roof board L up from here (right of Glo at the apex: r5)
HANS_ROOF_R = 1700.0                # ...and board R from here (right of its foot)
HANS_PILE = 1700.0                  # where he lifts board L off the pile from
ROOF_HANG_DX = 140.0                # r22: the roof boards hang from Glo this far right of Hans (clear of the frame)
ROOF_HANG_Y = 630.0                 # ...their hinge this high (in Hans' easy reach)
ROOF_HI_Y = 205.0                   # ...lifted to here: their feet well above the top beam
ROOF_SLIDE = (1.5, 95.0, 0.35)      # r35: the roof boards slide out of the pile first: (s, px, R before L by)
ROOF_PEG_HOME = (1752.0, HW.FLOOR - 186 - 27.0)   # r41: the roof peg, lying on the thin pole on the pile
ROOF_PEG_T = (1.4, 0.7, 0.4)        # r41: carried up to the boards' tops (s), turned and pushed in (s), let go (s)
ROOF_DARK = -0.22                   # the roof boards' wood, a shade darker than the pile's and the frame's
ROOF_OVER_Y = 440.0                 # Glo's y (his tendrils' tips) going over to Hans for them: above the frame
HANS_GEARS = 1590.0                 # where he turns the gear blanks at Twigs' blade from (r5: further left, his fin
                                    # hid half the board)
HANS_POLE = 1700.0                  # ...and where he holds the thin pole from (r4: in reach)
HANS_POLE_HOLD = 1560.0             # r12: where he holds the pole's end down for the cut (the rack in clear view)
TURN_R = 68.0                       # where his tentacles hold the blank (from its middle; r12: at its left rim, 50
                                    # lay across its face)
HANS_RACK = 1640.0                  # where he stands to lay a board on the saw rack and take it off again (r4)
HANS_STONES = 3720.0                # where he lays the oven's stones from (the dome isn't up yet): all in his reach
                                    # (r26, part 2 must-fix "tentacles stretch like rubber": 3765 meant 280 px)
HANS_LUMPS = 3570.0                 # where he takes the clay lumps off the heap (r13, part 2 must-fix "long walks": just
                                    # right of it, a short walk from the slab; r12's 3330 meant 455 px each way, twice)
HANS_COIL = 3810.0                  # r34 (round 33 part 2 must-fix "his body and fin cover the oven's right side through
                                    # the coil build"): 3780 -> 3810. r26 (part 2 must-fix: 3840 stretched his tentacles 1.5x to the dome top; at 3730 his
                                    # fin hid the dome): beside the dome while he lays the coils (clear of it: the coils all in view; r8: 3720
                                    # put his head in front of the dome, hiding the coils)
COIL_REACH = 300.0                  # how far his tentacle reaches to the dome's far side from there
LUMP_SLOTS = (0, -1, -2)            # the tentacle holding each lump (r13: all on the heap's side: none behind him)
LUMP_HOLD = {0: (95.0, 850.0), -1: (-90.0, 866.0), -2: (-165.0, 890.0)}   # r47 (advisor FK0021 r46 must-fix "a lump hangs at his chest with nothing holding it": lump 0 held out at his right, clear of his body, and rolled first; was (-15, 842)) carried low in front (r6: not overhead; r14: apart, not a clump)
LUMP_S = 1.3                        # r6: big enough for a ring each (r9: one ring per lump; r31: 1.3, was 1.7, with
                                    # the bigger heap: six lumps are the heap's worth, round 30 part 2 "clay multiplies")
SLAB = (3752.0, 992.0, 200.0)       # r38 (round 37 part 2 must-fix "the rope runs into the pile"): 40 px longer to the
                                    # right, the pile moved along with it. Was (3712, 992, 160). r13: a flat stone slab on the path in front of him (middle x, front edge y, half
SLAB_TOP = SLAB[1] - 9.0            # its length); he rolls each lump out on it ("a ball turns into a coil mid-air")
_LR = 16.0 * LUMP_S
# r44 (round 44 part 2 must-fix "the clay grows: a ball rolled into a coil 2.5x its volume"): each lump is just
# its ring's coil (ROPE_R thick, as long as the ring) rolled up into a ball, so the rings use the lumps up honestly:
# r = (3/4 ROPE_R^2 Lr)^(1/3). Lump k makes ring LAY_ORDER.index(k) (rings 0..5 are 180..100 long)
LUMP_SK = (1.86, 1.77, 1.60, 1.95, 1.94, 1.91)   # each pile slot's lump size (was LUMP_S 1.3 for all)


def lump_r(k):
    """r44: lump k's radius (world px)."""
    return 16.0 * LUMP_SK[k]


LUMP_PILE = [(3778.0, SLAB_TOP - 2.6 * _LR), (3750.0, SLAB_TOP - _LR), (3806.0, SLAB_TOP - _LR)]   # (r14)
# r15: all six on the slab's right end before the hearth: three along the bottom (trip 1), two on them and one on top
# (trip 2), per trip in LUMP_SLOTS order (his tentacles 0, -1, -2 hold them right to left)
LUMP_PILE6 = [(3912.0, SLAB_TOP - 1.86 * 16.0), (3852.0, SLAB_TOP - 1.77 * 16.0), (3796.0, SLAB_TOP - 1.60 * 16.0),
              (3852.0, SLAB_TOP - 137.0), (3882.0, SLAB_TOP - 83.0), (3824.0, SLAB_TOP - 80.0)]   # (r44: bigger lumps)
LAY_ORDER = (3, 4, 5, 0, 1, 2)       # the top one first, then the middle two, then the bottom row
CLAY_HW, CLAY_HH = 2.84, 3.34         # r15: the clay heap this much wider / taller than a post hole's (six lumps' worth;
                                    # r31: 2.0/2.35, was 1.7/1.8: ~8200 px^2, the six lumps ~8150)
CLAY_STROKES = 6
ROLL_X = 3660.0                     # r26 (was 3628: nearer him) where on the slab each one is rolled out (its open left end, clear of his legs)
ROLL_F = 0.55                       # r26: where along the rope (from its right end) his first tentacle rolls it (was 0.85: its far end)
ROLL_S = 3.0                        # seconds of rolling, back and forth three times (r38, round 37 part 2 must-fix "a ball
                                    # becomes a coil 3x its length in a second": was 1.9)
TW_TABLE = 4980.0
PLANK_DY, PLANK_TH = 7.0, 6.0       # the table planks' spacing in a stack and thickness (thin: a low stack)
FR_NOTCH = TW_TABLE - 68.0          # the foreground rack's notch (Twigs trims at it)
TRIM_Y = HW.RACK_Y - 37.0          # r12: his blade crosses the notch mid-stack (it slants; at -60 it
                                    # only reached the top planks)
TRIM_OFF = 56.0                     # r13: how much Twigs trims off the planks' rough ends (was 20: unseen)
FR_STOP = FR_NOTCH - 200.0          # its stop block: every plank comes out 200 long
DOUGH = (4870.0, HW.RACK_Y - 6.0)   # (r29: 4920 -> 4870, round 28 part 3 must-fix "the dough and pieces hang past the rack's end")
                                    #   # the dough, on the rack's top (r19: no board; its heap bottom is at y + 6)
DOUGH_RX, DOUGH_RY = 32.0, 18.0   # (r29: 40 -> 32, so Twigs' three cuts from one spot make four equal quarters)
                                  #     # the kneaded dough's half width and height (flat enough for the blade to
                                    # go right through it)
DOUGH_CUTS = (-20.2, -0.6, 17.8)    # Twigs' three aims (r29, round 28 part 3 must-fix "two big pieces, two slivers"):
                                    # his slanted kerfs then cut four equal areas (25.9/24.4/24.7/25.0 %)
BLADE_SLIDE = 1.1                   # r25: how long Twigs' blade takes to slide out of its sheath (and back in)
DOUGH_CY = DOUGH[1] - DOUGH_RY + 6.0   # the dough's middle height (his blade crosses each cut line there)
TW_DOUGH = 4915.0                   # (r29: 4960 -> 4915 with the dough) r25 (was 4980, the table spot: one short step nearer, so all three cuts
                                    # keep the blade tip on the rack top with the elbow well out). Where Twigs stands to make all three (his arm reaches each): his place
JUG_HOME = (4722.0, 1048.0)          # the water jug on the near ground by the rack's left leg, in Hans' reach (r5: on
                                    # the rack's end it hid the stop block)
SACK_T = (4640.0, HW.FLOOR - 2)     # the sack set down behind the table's end
SACK_R = (4770.0, HW.RACK_Y - 2)    # (r29: 4830 -> 4770 with the dough)
#    # ...and up on the rack, by the dough (right of Hans' face, left of the dough)
SACK_TIP = 96.0                     # how far he tips it over the dough (degrees, about its right foot; r14: mouth down)
SACK_TIP_UP = 42.0                  # ...lifted this much, so it pours from above, clear of the dough (r14: the stream
                                    # in sight below the mouth, "the flour is never seen pouring")
UNTIE_S = 3.4                       # r14: the untying, slow enough to follow
FLOUR_DX = 24.0                     # (r29: 34 -> 24: the heap all on the rack)
#                     # r14: the flour heap lands under the sack's mouth, right of the board's middle;
                                    # the kneading works it over to the middle
SACK_UP_Y = HW.RACK_Y - 24.0       # r26: lifted clear of the bar first...
SACK_BACK_Y = GB - 2.0              # (r26, unused since r27)
SACK_F = (4806.0, 1050.0)           # ...and down on the ground in front, by the rack's leg (stays in front: no pop)
SACK_OUT = (0.6, 1.3, 3.2)          # r37: up behind his legs, out to his left (still behind), then across in front
SACK_OUT_X = 4530.0                 # (clear of his body and legs on screen, over the table's end)
SACK_OUT_Y = 866.0                  # (its foot above the table top, so it's never behind the table as it comes forward)
SACK_SHOULDER = 30.0                # r37: the grip at the dough this much lower than the neck
PEEL_HOME = (4530.0, HW.TABLE_FRONT - 66.0)  # (r23: 4530, was 4560: its handle end clear left of the stop block)
                                                # r16: lying flat on the table's end, in sight all along (r14 leaned it
PEEL_TILT = 0.0                     # by the table's end, but Hans stood in front of it: its handle swept up across his
                                    # face when he took it)
PEEL_FLAT_DY, PEEL_FLAT_BH = 8.0, 6.0   # r31: lying flat, its paddle face shows: drawn 8 lower (on the table top,
                                    # not over its back edge), 6 taller each side
PEEL_DOWN_Y = HW.TABLE_FRONT - 66.0  # r6: Glo lays the peel along the table's back edge after the bread, in sight
LOAF_STEP = 16.0                    # the loaves' spacing on the peel (one row of four)
HANS_DOUGH = 4685.0                 # (r29: 4740 -> 4685 with the sack and the dough)
HANS_ROLL = 4812.0                  # r16 (part 3 must-fix, tentacle stretched across the rack): a step nearer the
                                    # dough once Twigs has cut it, so he rolls the far quarters at a normal reach
HANS_LOADX = 4760.0                 # r16: a step back left once they're rolled, where he loads the peel:
PEEL_LOAD = (4650.0, 786.0)         # he holds it low at his front, the blade just left of the board, the handle
                                    # (r23 part 3 must-fix "peel skewered through the stop block": y 786, was 834,
                                    # so the blade and handle pass over the block's top at 804)
PEEL_HANDLE = (122.0, 28.0)        # slanting down a little to his tentacle (r23: was up, -10), under his mouth, clear of loaves
                                    # (blade middle to the handle's end), and passes the loaves over a short way...
HANS_LAY = 4550.0                   # ...then carries it a short way left and lays it on the table's end...
PEEL_LAY_X = HANS_LAY - (HANS_LOADX - PEEL_LOAD[0])
HANS_CLEAR = 4800.0                 # ...and steps back, clear of Glo, who picks it up from the table (no handover
                                    # beside Hans' head, no long tentacle)
FEAST_GLO = 4240.0                  # r42 (round 41 part 3 must-fix "Glo parked on top of a post, a lantern on a
                                    # stick"): clear of every pole and lamp (was 4300, the lamp post at 4320; the table
                                    # wait was 4330, now 4230/4200; the fire 3380, the birds' post, now 3440)
DIGS_WAIT, SPRINGS_WAIT = 3390.0, 3214.0   # where they wait for the bread (out of the houses' close shot)
PEEL_LIFT = 60.0                    # r42: held this far up, off the back log, while the last two planks go on
PEEL_ASIDE = 90.0                   # r46: and this far left of where it lay, clear of his body (his tentacle on it shows)
PEEL_GRIP = 120.0                   # where the peel is held: along the handle from the blade's middle
PEEL_HAND_Y = 866.0                 # r20 (part 3 must-fix "a loaf floats over Hans' mouth"): Glo holds the baked bread
                                    # out to Hans this low, under his mouth, so the tentacles taking it show in front
PEEL_UP = (4380.0, 780.0)           # held up high on Hans' left (over the table, clear of everyone; r13: 120 further
                                    # left, so Glo takes the handle beside Hans, not behind his head)
LOAF_ON_BOARD = [(4785.0 + 38.0 * j, HW.RACK_Y - 2.0) for j in range(4)]   # (r29: all on the rack)   # r19: on the rack's top   # r16: right of the peel's handle   # side by side, not overlapping
LOAF_W, LOAF_H = 14.5, 9.4          # r31 (round 30 part 3 must-fix "each sliver becomes a loaf 2-3x its size"): the
                                    # same dough as its quarter (pi*w*h = 428 px^2, the quarters 391-445; was 17/11, 587)
#         # a rolled quarter's half sizes (about the dough's quarter); it rises a quarter
                                    # bigger in the oven
LOAF_UP = 862.0                     # r20 (part 3: held by his mouth corner at 800, "eating the bread"): chest height
LOAF_HX = 4225.0                    # Hans takes the two far loaves along the table to here (r8: was 4330, out of reach)
HANS_BREAD = 4500.0                 # r7: he waits for the bread here (a short walk once the lanterns are lit), so
                                    # Glo brings it in beside him, not behind his head
LOAF_ON_TABLE = [(4080.0, HW.TABLE_FRONT - 34.0), (4250.0, HW.TABLE_FRONT - 34.0),
                 (4460.0, HW.TABLE_FRONT - 34.0), (4620.0, HW.TABLE_FRONT - 34.0)]
FEAST_ZOOM = (4432.0, 790.0)        # r9: the feast close shot (the broken loaf, both bunnies, everyone's faces)
FEAST_Z = 1.6                       # r14: closer (was 1.5: break, bites too small); r15: 1.75, fy 785 (must-fix: Glo cut off at 2.0)
# r40 (round 39: the close shot cut off every face): 1.6 on 4432 (Springs to Wheels), all faces and the table in it
# r40: the Keepers' mouths (from their feet: world x offset, screen y) standing at the feast, measured; who Hans
# tosses a piece to, in order: (Keeper, his tentacle, where it leaves him (dx from him, y), flight s)
MOUTH_AT = dict(springs=(15.0, 852.0), digger=(0.0, 896.0), tentacles=(7.0, 790.0), teeth=(8.0, 744.0),
                wheels=(5.0, 835.0))
# r42 (round 41 part 3 must-fix "a loaf floats free and jumps every half second; in Twigs' mouth with no hand
# raised"): Twigs and Digs, beside him, are fed: his tentacle takes the piece right to their mouths (rel None). Wheels
# and Springs, further off, get a slow high lob over their neighbour's head (was a quick flat toss across Twigs' and
# Digs' chests). (kd, slot, release point or None, flight s, arc px)
TOSSES = [("teeth", 1, "hand", 0.0, 0.0), ("digger", 0, None, 0.0, 0.0), ("wheels", 2, (75.0, 825.0), 1.25, 280.0),
          ("springs", -1, (-75.0, 835.0), 1.2, 170.0)]
FEED_S = 1.6                        # r42: his tentacle brings a piece from the loaf to a neighbour's mouth
TWIGS_TAKE = (-120.0, 822.0)        # r42: Twigs takes his piece in his left paw here (x from his middle), Hans' tentacle
#                                   # brings it over (the tentacle to his mouth went behind his body: the piece floated)
TWIGS_PIECE = (26.0, -2.0)          # r42: the piece at his fingertips (from the hand point): his arm is drawn behind
#                                   # his body, so the paw stays at its edge and he bites at his mouth's corner
TWIGS_BITE = (-34.0, 2.0)           # r42: where the piece meets his mouth (from its middle): the left corner
FEAST_PIECE_R = 21.0               # r42: 17 -> 21, readable in the night sky as it flies (round 41 part 3). r40: a hearty chunk each (the bunnies' are bunny-sized, r 10)
BREAK_S = 2.4                       # r14: the loaf pulled in two (was 1.4 s)
BITES, BITE_EVERY = 6, 1.5          # r14: each bunny eats its piece in bites
FEAST = dict(springs=4060.0, digger=4220.0, tentacles=4440.0, teeth=4640.0, wheels=4805.0)
# r8: the first bunny sits beside Hans (was 4150, past Digs: his tentacle stretched over to hand it its bread)
ANIMALS = [("hedgehog", 2700.0, (3936.0, 1000.0)), ("bunny", 2880.0, (4265.0, HW.TABLE_FRONT - 30.0)),
           ("bunny", 2880.0, (4360.0, HW.TABLE_FRONT - 30.0))]
BIRDS = [((3300.0, HW.BIRD_POST_TOP), (4000.0, HW.TABLE_FRONT - 10.0)),
         ((3380.0, HW.BIRD_POST_TOP), (4150.0, HW.TABLE_FRONT - 10.0)),
         ((5400.0, HW.BIRD_POST_TOP), (4720.0, HW.TABLE_FRONT - 10.0)),
         ((5500.0, HW.BIRD_POST_TOP), (4540.0, HW.TABLE_FRONT - 10.0))]


class Plan:
    def __init__(self):
        self.props = {}
        self.hans = {s: [] for s in (-2, -1, 0, 1, 2)}           # slot -> [(t0, t1, fn(t)->(x, y), grip fn)]
        self.twigs_cuts = []                                      # (reach0, c0, c1, back1, hand, dir, strokes)
        self.digs_jobs = []                                       # (t0, t1, kind, data)
        self.glo_jobs = []
        self.say = {}
        self.cam_keys = []
        self.flares = []                                          # (t0, t1, target fn) Glo's light
        self.voices = []
        self.voice_events = []
        self.light_keys = []
        self.sack_down = (1e9, 1e9)
        self.walk_t = (1e9, 1e9)
        self.walks = {kd: [(0.0, MILL[kd])] for kd in WALKERS}
        self.glo_keys = [(0.0, GLO_HOME)]
        self.glo_dy = []                                          # (t0, t1, dy) Glo floats lower to hold/pick things
        self.glo_fy = []                                          # (t0, t1, t_end, dy, fn): dy * fn(0..1) over t0-t1
        self.springs_special = []                                 # (t0, t1, kind, data)
        self.bubbles = []                                         # (t, kind, picture)
        self.wheels_load = []                                     # (t0, t1, prop) a prop on Wheels' head
        self.acorn_flow = []                                      # (t, acorn prop) acorns going through the nip
        self.wheel_go = 1e9
        self.flour_puff = 1e9
        self.zoom_keys = []
        self._props()
        t = self._hook()
        self.reach_cap = HANS_REACH_POSTS
        t = self._holes_posts(t)
        self.reach_cap = HANS_REACH
        t = self._beams_roof(t)
        t = self._gears(t)                                        # r20 (part 1 must-fix "the finished stone is taken
        self.reach_cap = HANS_REACH_POSTS                         # off its peg for the gear"): the gears go on the
        t = self._stones(t)                                       # bare pegs first, then the stones in front of them
        self.reach_cap = HANS_REACH
        t = self._mesh_pulley(t)
        t = self._hopper_belt(t)
        t = self._start(t)
        t = self._milling(t)
        t = self._walk_home(t)
        t = self._oven(t)
        t = self._table(t)
        t = self._bake(t)
        t = self._feast(t)
        self._retime_lines()
        self.end = self.signoff + _dur(SIGNOFF) + 2.5
        self._finish()
        self.voices = voices(self)

    def _retime_lines(self):
        """r10 (round 9 should-fixes): five lines played well before what they describe; each now starts on its
        action, and any line that would then talk over the one before it waits for it (narration only: nothing is
        timed off these)."""
        self.say["hopper"] = self.hopper_up[0] - 3.0               # as the first hopper board goes up
        self.say["sack"] = self.sack_lift                          # as he picks the sack up
        self.say["coils"] = self.coils[0][0] - 1.5                 # as the first coil goes on
        self.say["planks"] = self.trim_cut[0] - 1.0                # as Twigs starts sawing
        self.say["dough"] = self.pour[0] - 1.0                     # r11: "Flour..." before the flour runs
        self.say["pour"] = self.basket_take - 0.3                  # r11: as Glo takes the basket
        self.say["loaves"] = self.dough_lines[0][3] - 1.0          # r11: as Twigs' first cut starts
        prev = None
        for k, v in sorted(self.say.items(), key=lambda kv: kv[1]):
            if k not in LINES:
                continue
            if prev is not None and v < prev + 0.3:
                self.say[k] = v = prev + 0.3
            prev = v + _dur(LINES[k])

    # ---------------------------------------------------------------- helpers
    def prop(self, name, kind, z, size, born=-1e9, **pose):
        p = Prop(name, kind, z, size, born, **pose)
        self.props[name] = p
        return p

    def walk(self, kd, t0, x1, v=V_WALK):
        """kd walks to x1 from t0; returns the arrival time."""
        x0 = self.walks[kd][-1][1]
        t0 = max(t0, self.walks[kd][-1][0])                         # a walk starts once the last one has ended
        if abs(x1 - x0) < 1:
            return t0
        self.walks[kd].append((t0, x0))
        t1 = t0 + abs(x1 - x0) / v + EASE
        self.walks[kd].append((t1, x1))
        return t1

    def glo_to(self, t0, x1, v=110.0):
        x0 = self.glo_keys[-1][1]
        t0 = max(t0, self.glo_keys[-1][0])
        self.glo_keys.append((t0, x0))
        t1 = t0 + abs(x1 - x0) / v + EASE
        self.glo_keys.append((t1, x1))
        return t1

    def line(self, key, t):
        self.say[key] = t
        return t + _dur(LINES[key])

    def hans_hold(self, slot, t0, t1, fn, reach=0.7, back=0.7):
        """Hans' tentacle `slot` reaches out to fn(t0) over `reach` s before t0, follows fn until t1, lets go and
        draws back over `back` s. When that's further than his tentacles reach from where he stands, he first walks
        over to it (part 1 review: "Hans' tentacles stretch to whatever length the job needs instead of him
        moving"; owner, FK0012: limbs keep their length)."""
        self.hans_step_in(t0 - reach, t0, t1, fn)
        self.hans[slot].append((t0 - reach, t1 + back, fn, (t0 - reach, t0, t1, t1 + back)))

    def hans_step_in(self, ta, t0, t1, fn, reach_max=None):
        """Walk Hans to within reach of everything fn reaches to in [t0, t1], unless he already is (or it can't be
        done standing in one place: then the job itself walks him along)."""
        if getattr(self, "_no_step", False):
            return
        reach_max = reach_max or getattr(self, "reach_cap", HANS_REACH)
        t1 = min(t1, t0 + 12.0)                                    # (a hold "for good" is judged by its start)
        n = max(2, min(49, int((t1 - t0) / 0.25) + 1))
        pts = [fn(t0 + (t1 - t0) * k / (n - 1)) for k in range(n)]
        for jobs in self.hans.values():                            # his other tentacles' jobs at the same time
            for a_, b_, fn_, _ in jobs:
                lo_, hi_ = max(a_, t0), min(b_, t1, a_ + 12.0)
                if lo_ < hi_:
                    pts += [fn_(lo_ + (hi_ - lo_) * k / 4.0) for k in range(5)]
        hx = self.walks["tentacles"][-1][1]
        cy = GB - 200.0 * K / 0.72
        lo, hi = -1e9, 1e9
        for x, y in pts:
            dy = abs(y - cy)
            if dy >= reach_max:
                return
            lim = math.sqrt(reach_max * reach_max - dy * dy)
            lo, hi = max(lo, x - lim), min(hi, x + lim)
        if lo > hi or lo - 1.0 <= hx <= hi + 1.0:
            return
        x_need = lo + 12.0 if hx < lo else hi - 12.0
        if abs(x_need - hx) < 45.0:                                # a little stretch rather than a shuffle
            return
        for kd in WALKERS:                                         # never into another Keeper's place
            if kd != "tentacles" and abs(x_need - self.walks[kd][-1][1]) < HALF[kd] * K + HALF["tentacles"] * K + 10:
                return
        self._no_step = True
        try:
            self.walk("tentacles", ta - abs(x_need - hx) / V_WALK - EASE, x_need)
        finally:
            self._no_step = False

    def carry(self, p, slot, t0, dur, grip=(0.0, 0.0), how="ease", lift=0.0, reach=0.7, back=0.7, rot=True, **pose):
        """Hans picks prop p up at t0 (his tentacle comes to it first), carries it to `pose` over dur and lets go."""
        dur *= 0.85                                                # a touch brisker than first written (length)
        p.move(t0, t0 + dur, how=how, lift=lift, holder=("Hans", slot), **pose)

        def fn(t, p=p, g=grip):
            q = p.at(t)[0]
            g = stone_squash(p, q, g)
            a = math.radians(q.get("ang", 0.0)) if rot else 0.0
            return (q["x"] + g[0] * math.cos(a) - g[1] * math.sin(a), q["y"] + g[0] * math.sin(a) + g[1] * math.cos(a))
        self.hans_hold(slot, t0, t0 + dur, fn, reach, back)
        return t0 + dur

    def cut(self, t0, tx, notch, y_mid, strokes=4, sx=-1, period=0.55, slant=None, v_at=0.55, tip_max=None,
            smax=0.0, band=15.0, sback=0.0, reach_dur=0.8, pre=0.45, lift_dy=22.0, hold=0.0, kerf=False):
        """Twigs reaches to the notch, saws (strokes along the blade), and brings his hand back -> end time.
        r25 (part 3 must-fix "the blade pops into his hand from nothing ... after the cut it is gone again"): the
        blade slides out of its sheath slowly (BLADE_SLIDE s, from `pre` s before the reach) and back in slowly as
        the hand comes back; between back-to-back cuts it stays out and the hand lifts straight across (lift_dy)."""
        hd, dr = cut_pose(tx, notch, y_mid, sx, slant, band=band, v_at=v_at, tip_max=tip_max, smax=smax, sback=sback,
                          kerf=kerf)
        if abs(self.walks["teeth"][-1][1] - tx) > 1.0:            # r31: Twigs steps up to the rack first
            self.walk("teeth", t0 - pre - 1.0 - abs(self.walks["teeth"][-1][1] - tx) / V_WALK - EASE, tx)
        prev = self.twigs_cuts[-1] if self.twigs_cuts else None
        chain = prev is not None and t0 - prev["back"][1] < BLADE_SLIDE + 0.6
        lift, blade = None, (t0 - pre, t0 - pre + BLADE_SLIDE)
        if chain:
            prev["sheath"] = None                                  # stays out until this cut's own end
            lift = ((prev["hand"][0] + hd[0]) / 2, min(prev["hand"][1], hd[1]) - lift_dy)
            prev["back_to"] = lift                                 # and his hand lifts straight over to the next
            t0 = min(t0, prev["c1"] + 0.9)
            prev["back"] = (prev["c1"] + 0.1, t0)
            blade, reach_dur = None, 0.8
        reach = (t0, t0 + reach_dur)
        c0 = max(reach[1], blade[1] if blade else 0.0) + 0.15      # (the blade fully out before the first stroke)
        st = [(c0 + i * period, c0 + (i + 1) * period) for i in range(strokes)]
        c1 = st[-1][1]
        back = (c1 + 0.1 + hold, c1 + 0.1 + hold + max(0.8, reach_dur))   # (hold: the blade mostly in before
        self.twigs_cuts.append(dict(reach_from=lift, reach=reach, blade=blade, c0=c0, c1=c1, back=back,   # he moves
                                    sheath=(c1 + 0.1, c1 + 0.1 + BLADE_SLIDE), hand=hd, dir=dr, strokes=st, sx=sx,
                                    tx=tx))
        return c1, back[1]

    # ---------------------------------------------------------------- the props at the start
    def _props(self):
        P = self.prop
        # the poles on the wood pile (two posts, the top beam, the low beam) and two boards and the thin pole
        P("post R", "pole", 5, 200.0, x=1790.0, y=HW.FLOOR - 28, ang=0.0, L=405.0, w=13.0)
        P("post L", "pole", 5, 200.0, x=1800.0, y=HW.FLOOR - 52, ang=0.0, L=405.0, w=13.0)
        P("top beam", "pole", 5, 240.0, x=1790.0, y=HW.FLOOR - 76, ang=0.0, L=480.0, w=11.0)   # (r31: 480, was 440)
        P("low beam", "pole", 1, 205.0, x=1780.0, y=HW.FLOOR - 98, ang=0.0, L=450.0, w=10.0)   # (r46: 450, the posts are 415 apart now; r31: 410, was 330)
        for i, nm in enumerate(("roof L", "roof R", "hopper L", "hopper R")):
            L = 250.0 if i < 2 else math.hypot(*(np.subtract(*HW.HOPPER[0])))
            P(nm, "board", 6 if i < 2 else 4.5, L / 2, x=1790.0 + (i % 2) * 6, y=HW.FLOOR - 116 - 13 * i, ang=0.0,
              L=L + (18.0 if i < 2 else HOPPER_TRIM), th=12.0, peg=0 if i < 2 else -1,
              dark=0.0 if i < 2 else HOPPER_TONE)
        P("thin pole", "log", 4, 26.0, x=1792.0, y=HW.FLOOR - 186, ang=0.0, x0=-100.0, x1=100.0, r=24.0)
        # r41 (round 40 part 1 must-fix "two boards stand already joined, nobody pegs them"): the peg that joins the
        # roof boards' tops, lying on the thin pole
        P("roof peg", "rpeg", 4.2, 12.0, x=ROOF_PEG_HOME[0], y=ROOF_PEG_HOME[1], ang=0.0, end=0.0)
        for i in range(2):
            P(f"gear {i}", "gear", 2, HW.GEAR_R, x=1800.0 + 10 * i, y=HW.FLOOR - 206 - 13 * i, ang=0.0, face=0.0,
              cut=0.0, corners=0.0, r=BLANK)
        for i, (x, y) in enumerate(HW.IN_BROOK):
            P(f"millstone {i}", "stone", 3, HW.STONE_R, x=x, y=y, ang=0.0, tilt=0.0, grooves=0.0, hole=0.0, wet=1.0,
              wl=y + HW.STONE_R * 0.32 * 0.45)                     # (r35: the water's surface where it lies)
        P("sack", "sack", 3.5, 40.0, x=1860.0, y=HW.FLOOR - 2, ang=0.0, fill=0.0, tied=0.0, folded=1.0, tip=0.0)
        P("basket", "basket", 7, 40.0, x=BASKET_START, y=HW.BASKET_HOME[1], ang=0.0, n=0.0)
        P("belt", "belt_coil", 4, 30.0, x=HW.BRAKE_X + 2.0, y=HW.BRAKE_TOP + 46.0, ang=0.0)
        P("acorn", "acorn", 8, 12.0, x=SQ_X + 21.0 * SQ_S, y=self.branch_y(SQ_X, -1e9) - 6.0 - 26.0 * SQ_S, ang=0.0,
          s=HOOK_ACORN_S)                                          # in the squirrel's paws, at its mouth
        for j in range(6):                                          # the village: the planks stacked on the saw rack
            # (r27, part 3 must-fix "the stack rises by itself onto the sawhorse": it lies on its top from the start)
            P(f"plank {j}", "plank", 22 + 0.01 * j, 80.0, x=FR_STOP + TRIM_OFF / 2 + 100.0, y=HW.RACK_Y - 6.0 - PLANK_DY * j, ang=0.0,
              yaw=0.0, L=200.0 + TRIM_OFF)                         # (r13: rough ends, TRIM_OFF too long)
        P("jug", "jug", 21.5, 20.0, x=JUG_HOME[0], y=JUG_HOME[1], ang=0.0)
        P("peel", "peel", 22.0, 80.0, x=PEEL_HOME[0], y=PEEL_HOME[1], ang=0.0, tilt=PEEL_TILT, hx=PEEL_HOME[0] + 150.0,
          hy=PEEL_HOME[1], gf=0.8, flat=1.0)                       # (on the table, in front of it; r31: lying
        # flat on it, its paddle face up: edge-on it was a thin brown line on the brown planks, round 30 part 3
        # must-fix "the peel pops into existence")

    # ---------------------------------------------------------------- 1. the hook: the acorn and Glo's idea
    def _hook(self):
        self.hook = 1.5
        t_hook = self.hook + _dur(HOOK)
        self.tags = (2.0, max(9.0, t_hook - 2.0))                  # the name tags, a slow drift in
        self.cam_keys += [(0.0, 1230.0), (self.tags[1] + 1.0, CAM_MILL)]
        # the squirrel nibbles, the acorn slips, bonks Digs' hat, and bounces up into Glo's tendrils
        self.nibble = (t_hook - 3.0, t_hook + 1.0)
        t_drop = t_hook + 0.8
        a = self.props["acorn"]
        hat = (SQ_X + 21.0 * SQ_S, GB - 300 * K + 8.0)               # straight below the squirrel's paws
        fall = BONK_FALL                                           # a slow, followable fall (part 1 review; r30: ~1 s)
        y0 = a.p0["y"]
        a.follow(t_drop, t_drop + fall, lambda tt, t0=t_drop, T=fall, y0=y0: dict(
            y=y0 + (hat[1] - y0) * soft_fall(min(1.0, (tt - t0) / T), 0.8)))   # the hit eases over a few frames (r5: 0.9
            # made a 690 px/s velocity flip in one frame against the bounce: storycheck thing_jumps)
        self.bonk = t_drop + fall
        self.acorn_fall = fall
        # it rests a moment on the hat (the bonk), then pops off in a little hop straight into Glo's tendrils beside
        # him (owner, FK0021: "I don't know if Glo is carrying that acorn after that or if it just stays floating")
        # r4: the hit must read - it bounces once and sits on the hat ~1 s while Digs winces and looks up; then Digs
        # gives a little hop that flips it off (r2: it must never jump off by itself)
        rest = 2.1                                                 # (r9: the wince, then Glo comes over for it)
        self.glo_dy.append((self.bonk - 1.4, self.bonk + rest + 3.0, CATCH_DY))
        t_off = self.bonk + rest
        self.digs_hop = t_off                                      # (Digs looks up at Glo from here)
        a.follow(self.bonk, t_off, lambda tt, hx=hat[0], hy=hat[1], b=self.bonk: dict(
            x=hx, y=hy - 26.0 * math.sin(math.pi * min(1.0, (tt - b) / 0.36))))
        # r9 (part 1 must-fix: "nothing knocks it off the hat, it floats over to Glo"; Digs' hop never moved his body):
        # Glo floats over and down to the hat, his tendrils close on the acorn there, and he lifts it away
        gx = hat[0] + 4.0                                          # Glo's x with his hand over the hat
        x0 = self.glo_keys[-1][1]
        self.glo_to(t_off - 0.15 - (abs(gx - x0) / 200.0 + EASE), gx, v=200.0)   # (after the bonk: it's seen clear)
        up = hat[1] - (GB - CRUISE + CATCH_DY + GLO_HOLD + 10.0) - glo_bob(t_off)
        self.glo_dy.append((t_off - 1.0, t_off + 1.2, up))         # (full from t_off - 0.2 to t_off + 0.4)
        self.glo_catch = t_off
        self.glo_to(t_off + 0.5, GLO_HOME)                         # and back beside Digs with it
        self.say_bonk = self.bonk + 0.15
        self.voice_events.append((self.bonk + 0.05, "digger", "uhoh", None))   # Digs feels it
        t = self.line("bonk", self.say_bonk) + 0.5
        a.follow(self.glo_catch, 1e8, lambda tt: dict(zip(("x", "y"), self.glo_hand(tt))), holder=("Glo", 0))
        self.idea_t = max(t, self.glo_catch + 1.2)
        self.flares.append((self.idea_t, self.idea_t + 1.4, None))
        self.bubbles.append((self.idea_t + 0.4, "lantern", "bread"))
        t = self.line("idea", self.idea_t + 1.6) + 0.4
        # owner FK0021 note: "the acorns are very tiny, the squirrel's very tiny... you barely see it hit": the camera
        # comes in close on the squirrel, Digs and Glo for the bonk and the catch, and back out before the wheel idea
        # r30 (round 29 part 1 must-fix "the bonk is still small and a blink"): a closer push-in for the fall and the
        # hit (the squirrel's paws to Digs' eyes), back out to the wider close shot before Glo takes it
        cy_ = hat[1] - 102.0                                        # (hat at ~70 % down, his eyes in)
        def bw(t_, a_=t_drop - 1.6, b_=self.bonk): return ease(t_, a_, a_ + 1.5) * (1.0 - ease(t_, b_ + 0.9, b_ + 2.0))
        self.zoom_on(self.tags[1] + 0.2, self.idea_t + 0.2, lambda t_: 1.85 + (BONK_ZOOM - 1.85) * bw(t_),
                     lambda t_: 610.0 + (hat[0] - 610.0) * bw(t_), lambda t_: 690.0 + (cy_ - 690.0) * bw(t_),
                     rin=2.6, rout=2.0)   # r4: Digs'
                                                                   # whole head in, not cut at the hat   # out before
                                                                   # Glo's idea bubble (it was cut off by the frame)
        self.bubbles.append((t + 0.6, "wheels", "wheel"))
        t = self.line("wheel", t + 1.5) + 0.6
        self.walk("digger", t - 3.0, 880.0, v=130.0)                # Digs heads for the mill (a short walk; r12: brisker,
                                                                   # two short bursts with a stop, owner "no long walks")
        return t

    def glo_hand(self, t):
        """Where Glo's tendrils hold a small thing (the acorn), world."""
        x = self.glo_x(t)
        return x - 4.0, self.glo_y(t) + GLO_HOLD + glo_bob(t) + 10.0

    # ---------------------------------------------------------------- 2. holes and posts
    def _holes_posts(self, t):
        self.cam_keys += [(t, CAM_MILL)]
        # r36 (round 35 part 1 must-fix "after hole 2 Digs walks ~8 s left to the frame's edge and stands there half
        # cut off"): the right hole first, then the left, so he ends by the left pile: one short walk round it
        t = max(self.walk("tentacles", t - 0.5, POST_HANS["R"]), t)
        xm = (self.walks["digger"][-1][1] + HW.PR) / 2              # Digs to the right post's place (a second walk;
        t = self.walk("digger", self.walk("digger", t + 2.5, xm, v=130.0) + 0.8, HW.PR, v=130.0)   # r36: in two)
        t_say = self.line("holes", t - 2.5)
        self.holes = {}
        for side, x in (("R", HW.PR), ("L", HW.PL)):
            if side == "L":
                t = self.walk("digger", t, x)
            d = Dig(K, period=1.1, t_start=t + 0.4)
            dt = (t + 0.4, t + 0.4 + 4 * 1.1)
            bob = lambda tt: 2 * K * math.sin(tt * 2.6)            # noqa: E731
            inner = 1 if side == "L" else -1                        # the side towards the other hole
            sp = SideSpoil(d, x, GB - 40.0, K, dt[1], (118 * K, -150 * K + 4 * K + 40.0), 95 * K, bob,
                           throw={inner: 0.08, -inner: HOLE_L_THROW if side == "L" else 0.08})   # both piles by
            # the hole, in his reach (r21, part 1 must-fix "a pile right on the wheel's rope coil": the left hole's
            # outer pile is thrown a little farther, clear of the brake post and the coil hanging on it)
            self.holes[side] = dict(x=x, dig=d, t=dt, spoil=sp, fill=None, post=None)
            self.digs_jobs.append((dt[0] - 0.3, dt[1], "dig", side))
            t = dt[1] + 0.5
        t = max(t, t_say + 0.3)
        # r9 (part 1 must-fix: post L slid through post R, already standing in its hole): post L goes in first,
        # so nothing stands between the pile and the left hole as he takes it across; then post R
        x_pl = self.push_from("L")                                 # out of Hans' way, left of the left pile
        t = self.walk("digger", t, x_pl, v=150.0)                  # (r36: from the left hole, one short walk)
        self.say["posts"] = t
        tp = self.post_in("post L", HW.PL, t, slot=-1)
        self.holes["L"]["post"] = tp
        t = self.fill("L", tp + 0.1, HW.PL)
        # post R: Hans back to where he holds it from; Digs to the left of the right hole
        t_d = self.walk("digger", t + 0.2, self.push_from("R"))
        t_h = self.walk("tentacles", self.holes["L"]["push"][1][1] + 0.3, HW.PR + POST_STAND)   # (r18: on his way as
        # soon as his pile is in, so Digs' pats are seen; r36: straight to where he lowers it from, no shuffle step)
        t = max(t_d, t_h)
        tp = self.post_in("post R", HW.PR, t, slot=1)
        self.holes["R"]["post"] = tp
        t = self.fill("R", tp + 0.1, HW.PR)
        self.walk("digger", t, DIGS_ROOF)                          # out of the way of the roof work
        self.line("posts", self.say["posts"])
        t_end = max(t, self.say["posts"] + _dur(LINES["posts"])) + 0.5
        self.zoom_on(self.holes["R"]["t"][0] - 3.0, t_end, 1.3, (HW.PL + HW.PR) / 2 + POSTS_FX, 665.0, rin=3.0,
                     rout=3.0)                                     # (r36: +23, was +60: Digs whole by the left pile)
        return t_end

    def post_in(self, name, x, t, slot):
        """Hans lifts a post off the pile, stands it up and lowers it into its hole -> time it's in."""
        p = self.props[name]
        top = HW.FLOOR - 405.0 + 30.0                              # its foot 30 px down in the hole
        q = p.end_pose()
        t1 = self.carry(p, slot, t, 2.2, grip=POST_GRIP, lift=60.0, x=q["x"] - 60, y=q["y"] - 140, ang=-POST_LEAN, back=0.0)
        # r21 (part 1 must-fix "Hans walks ~7.5 s carrying post 1": a walk to 290 px off, then a step-in walk right
        # after it): one short walk straight to where he lowers it from, a little brisker
        hx = x + POST_STAND
        if hx < self.walks["tentacles"][-1][1] - 20:                 # step closer to the hole, the post with him
            hx0 = self.walks["tentacles"][-1][1]
            tw = self.walk("tentacles", t1, hx, v=POST_V if hx0 - hx > 250.0 else V_WALK)
            dx = q["x"] - 60 - hx0
            p.follow(t1, tw, lambda tt: dict(x=self.hans_x(tt) + dx), holder=("Hans", slot))
            self.hans_hold(slot, t1, tw, lambda tt: self.grip_rot(p, tt, POST_GRIP), reach=0.0, back=0.0)
            t1 = tw
        # r36 (round 35 part 1 must-fix "the post goes into its hole behind his legs"): he lowers it from further
        # right (POST_STAND 165, his toes clear of the hole), his tentacle sliding down it as it swings over the hole
        # (held lower, it is in his reach from there)
        d_ = 3.4 * 0.85
        p.move(t1, t1 + d_, how="ease", holder=("Hans", slot), x=x, y=top + 202.0 - 60.0, ang=-POST_LEAN)
        self.hans_hold(slot, t1, t1 + d_, lambda tt, a=t1, b=t1 + d_: self.grip_rot(
            p, tt, (POST_GRIP[0] + (POST_GRIP_LOW[0] - POST_GRIP[0]) * smoothstep(_seg(tt, a, b)), 0.0)),
            reach=0.0, back=0.0)
        t2 = t1 + d_
        t2 = self.carry(p, slot, t2, 0.8, grip=POST_GRIP_LOW, x=x, y=top + 202.0 - 26.0, ang=-90.0, reach=0.0,
                        back=0.0)                                  # r9: upright over it
        t3 = self.carry(p, slot, t2, 0.9, grip=POST_GRIP_LOW, x=x, y=top + 202.0, ang=-90.0, reach=0.0, back=0.7)
        # r6 (part 1 must-fix): the post slid across his face and through the first post. He swings it behind him
        # the whole way (behind the post already standing too), and it stays behind him in its hole
        p.zf = [(t, 3.9), (t3, 5.0)]
        return t3

    def fill(self, side, t, x):
        """r18: the soil goes back in where it's seen going. Digs (left of the hole) walks the left pile in ahead of
        his paws while Hans walks the right pile in ahead of his front tentacle tips; the dark hole closes as each
        pile drops in. Then Digs steps up to the post and pats the earth down -> end time."""
        h = self.holes[side]
        a = t + 0.6
        d0, d1 = self.push_from(side), x - PAT_STAND                # he walks the pile along ahead of his paws
        tb = self.walk("digger", a, d1, v=(d1 - d0) / (PUSH_S - EASE))   # its last bit drops in
        h["shove"] = (d0, d1)
        self.digs_jobs.append((a - 0.4, tb, "push", side))
        # Hans walks the right pile in the same way, its far side against his front tentacle tips (the pile is seen
        # the whole way, left of his feet; owner rule: no tentacle stretched out to it)
        e0, e1 = h["spoil"].cx[1] + 52.0, x + 36.0
        hs = min(e0 + 10.0 + HANS_TOE, self.walks["teeth"][-1][1] - HANS_CLEAR_TW)   # (r18: never into Twigs: for
        e0 = hs - 10.0 - HANS_TOE                                  # hole R his tips start a little into the pile)
        th = self.walk("tentacles", t, hs)
        th0 = max(th, a + 0.2)
        th1 = self.walk("tentacles", th0, e1 + 10.0 + HANS_TOE, v=(e0 - e1) / (PUSH_S - EASE))
        h["push"] = {-1: (a, tb), 1: (th0, th1)}
        h["hshove"] = (e0, e1)
        tb = max(tb, th1)
        tw = tb + 0.2                                              # he pats it from where he is (the post seen)
        h["pats"] = [(tw + 0.2 + 0.7 * k, tw + 0.2 + 0.7 * (k + 1)) for k in range(PATS)]
        h["fill"] = (a, h["pats"][-1][1])
        self.digs_jobs.append((tw, h["pats"][-1][1], "pat", side))
        return h["pats"][-1][1] + 0.4

    def fill_clay(self, t):
        """r26: Digs walks round behind the left clay pile and shoves it back into the pit ahead of his paws (the
        dark hole closes as it drops in), then pats it down flat -> end time."""
        h = self.holes["clay"]
        d0, d1 = self.push_from("clay"), h["x"] - PAT_STAND
        t = self.walk("digger", t, d0, v=150.0)
        a = t + 0.4
        tb = self.walk("digger", a, d1, v=(d1 - d0) / (PUSH_S - EASE))
        h["shove"] = (d0, d1)
        h["push"] = {-1: (a, tb)}
        self.digs_jobs.append((a - 0.4, tb, "push", "clay"))
        tw = tb + 0.2
        h["pats"] = [(tw + 0.2 + 0.7 * k, tw + 0.2 + 0.7 * (k + 1)) for k in range(PATS)]
        h["fill"] = (a, h["pats"][-1][1])
        h["pat_y"] = GB + 4.0
        self.digs_jobs.append((tw, h["pats"][-1][1], "pat", "clay"))
        return h["pats"][-1][1] + 0.4

    def clay_shove(self, t):
        """r26: how far (0..1) Digs has walked the left clay pile along to his pit."""
        h = self.holes["clay"]
        if "shove" not in h or not hasattr(self, "paths"):
            return 0.0
        d0, d1 = h["shove"]
        if t < h["push"][-1][0] - 0.5:
            return 0.0
        return min(max((self.paths["digger"](t) - d0) / (d1 - d0), 0.0), 1.0)

    def push_from(self, side):
        """Where Digs stands to start shoving a hole's left pile: his paw at its outer edge."""
        h = self.holes[side]
        return h["spoil"].cx[-1] - 46.0 - PAW_GAP - PAW_PUSH

    def soil_pile(self, side, sx, t):
        """(centre x, scale 0..1) of a hole's pile on side sx: it slides towards the hole (the left one ahead of
        Digs' paws as he walks it along, the right one ahead of Hans' front tentacle tips) and gets smaller only
        once its front is over the hole, as it drops in."""
        h = self.holes[side]
        cx = h["spoil"].cx[sx]
        if "push" not in h or sx not in h["push"]:                 # (r26: the clay pit's right heap is the oven's)
            return cx, 1.0
        if sx < 0 and hasattr(self, "paths") and h["push"][-1][0] - 0.5 <= t <= h["push"][-1][1] + 2.0:
            # r21 (part 1 must-fix "the holes change shape without digging", a pile from nowhere): by his paws only
            # while he walks it in (as he dug, standing over the hole, it read as half filled)
            d0, d1 = h["shove"]
            u = min(max((self.paths["digger"](t) - d0) / (d1 - d0), 0.0), 1.0)
        elif sx > 0 and hasattr(self, "gaits") and h["push"][1][0] - 0.5 <= t <= h["push"][1][1] + 2.0:
            e0, e1 = h["hshove"]                                   # moved only by his tentacle tips
            edge = min(f_[0] for f_ in self.gaits["tentacles"].feet(t)) - 10.0
            u = min(max((e0 - edge) / (e0 - e1), 0.0), 1.0)
        else:
            u = ease(t, *h["push"][sx])
        return cx + (h["x"] + sx * 30.0 - cx) * u, min(1.0, 2.0 * (1.0 - u))

    def soil_edge(self, side, sx, t):
        """The pile's outer edge (where the paw or tentacle pushing it is)."""
        cx, sc = self.soil_pile(side, sx, t)
        return cx + sx * (40.0 * sc + 6.0)

    def filled(self, side, t):
        """How much of the hole's soil is back in (0..1)."""
        h = self.holes[side]
        if "push" not in h:
            return 0.0
        if h.get("clay"):                                          # r26: only the left pile goes back in
            return 1.0 - self.soil_pile(side, -1, t)[1]
        return 0.5 * ((1.0 - self.soil_pile(side, -1, t)[1]) + (1.0 - self.soil_pile(side, 1, t)[1]))

    def patted(self, side, t):
        h = self.holes[side]
        if "pats" not in h:
            return 0.0
        return sum(ease(t, a + 0.25, a + 0.4) for a, b in h["pats"]) / len(h["pats"])

    def hole_state(self, side, t):
        """(open 0..1, the larger pile's scale 0..1) of a post hole."""
        h = self.holes[side]
        o = ease(t, h["t"][0], h["t"][1])
        if "push" in h:
            return o * (1.0 - self.filled(side, t)), max(self.soil_pile(side, -1, t)[1], self.soil_pile(side, 1, t)[1])
        return o, 1.0

    # ---------------------------------------------------------------- 3. beams and roof
    def _beams_roof(self, t):
        t0 = self.line("beams", t)
        b, lb = self.props["top beam"], self.props["low beam"]
        # r16 (part 1 must-fixes, round 16: the top beam held overhead on a tentacle twice his length; Glo rose up
        # through the oak's branch from the basket): Glo pops his acorn into the basket first (his tendrils free),
        # floats over low (rising only once he's clear of the branch) and takes the top beam from Hans' side; he
        # lifts it above the post tops right of the frame, carries it in up there and sets it down onto them. Hans
        # only lifts things to his side, in his easy reach.
        a = self.props["acorn"]
        assert a.moves[-1][0] == self.glo_catch and a.moves[-1][1] > 1e7
        hand0 = GB - CRUISE + GLO_HOLD + 10.0                       # Glo's hand at his cruising height
        hand_dy = lambda y: y - hand0
        bk = HW.BASKET_HOME
        bkp = self.props["basket"]
        # r45 (round 44 part 1 must-fix "a basket suddenly appears in Springs' hand at ~32 s as Digs walks off": it
        # stood behind Digs from 0:00): the basket waits on the open grass right of Digs, in view from the start;
        # Glo floats down to it, pops his acorn in, takes its handle and carries it low over to the grass under the
        # oak's branch tip, where he sets it down
        t_s0 = self.glo_to(t, BASKET_START + 8.0, v=150.0)
        rim = lambda tt: (bkp.at(tt)[0]["x"] + 2.0, bkp.at(tt)[0]["y"] - 50.0)   # just in over its rim
        tp = t_s0 + 0.25
        take0 = t_s0 + 1.0
        t_arr = self.glo_to(take0 + 0.3, bk[0] + 8.0, v=90.0)
        t_b = t_arr + 0.3                                          # set down under the branch
        self.glo_dy += [(t_s0 - 0.6, t_b + 0.8, BASKET_DY),         # down to its handle (his hand at its rim)
                        (take0 + 0.1, t_arr + 0.2, -BASKET_LIFT)]   # carried just clear of the grass
        bkp.follow(take0, t_b, lambda tt: self.basket_pose(tt, None), holder=("Glo", 1))
        rest = self.basket_pose(t_b, None)                         # then it stands there (a fixed pose: the plan
        bkp.move(t_b, t_b + 0.001, x=rest["x"], y=rest["y"], ang=0.0)   # later adds Glo keys)
        put = rim(t_b)
        dip = put[1] - hand0
        t_go = t_b + 1.0
        t_rise = t_go + 0.5 + (760.0 - bk[0]) / 200.0              # (clear of the oak's branch first)
        self.glo_dy.append((t_b + 0.1, t_rise + 0.8, 45.0))        # (r17: low under the branch till then)
        t0_, _, p0_, p1_, how_, lift_, holder_, fn_ = a.moves[-1]
        a.moves[-1] = (t0_, tp, p0_, dict(p1_, x=rim(tp)[0], y=rim(tp)[1]), how_, lift_, holder_, fn_)
        a.follow(tp, tp + 0.3, lambda tt, tp=tp: dict(zip(("x", "y"), lerp2(self.glo_hand(tt), rim(tt),
                                                                             ease(tt, tp, tp + 0.3)))), holder=("Glo", 0))
        a.follow(tp + 0.3, t_b, lambda tt: dict(zip(("x", "y"), rim(tt))), holder=("the basket", 0))
        a.zf = [(tp + 0.15, 6.9)]                                  # in the basket, behind its front, till he takes
        self.acorn_put = (put, tp, dip)                            # it back out for the first drop (_start)
        hold = {0: (160.0, 630.0), 1: (130.0, 640.0)}               # at his right side, in his easy reach
        t = self.walk("tentacles", t, MILL["tentacles"])           # back by the pile first
        hx0 = MILL["tentacles"]
        BX = hx0 + hold[0][0]
        ta = self.carry(b, 0, t, 3.0, lift=40.0, x=BX, y=hold[0][1], ang=0.0, back=0.0, grip=(-60.0, 0.0))
        b.zf = [(t, 3.9)]                                          # r19 (part 1 must-fix "the beam slides up
        # through his face"): it comes up behind him (his tentacle on it behind him too) and stays behind him
        tgb = self.glo_to(t_go, BX + 4.0, v=200.0)
        tk = max(ta + 0.5, tgb + 0.6, t_rise + 1.0)                # his tendrils round its middle
        b.follow(ta, tk, lambda tt: dict(x=BX, y=hold[0][1]), holder=("Hans", 0))
        self.hans_hold(0, ta, tk + 0.3, lambda tt: self.grip_pt(b, tt, (-60.0, 0.0)), reach=0.0, back=0.5)
        HI = HW.BEAM_Y - 2.0                                       # its underside clear above the post tops
        bx_end = (HW.PL + HW.PR) / 2
        tin = self.glo_to(tk + 1.1, bx_end + 4.0, v=120.0)
        t_free = tin + 1.0
        # r29 (round 28 part 1 must-fix "Glo sinks through the beam he set down"): he lifts off it a little and keeps
        # that height until he's past its left end, then sinks, outside the posts
        t_past = t_free + 0.4 + (bx_end + 4.0 - (bx_end - 240.0 - GLO_CLEAR_X)) / 120.0 + EASE / 2
        self.glo_dy += [(t_rise, t_past + 0.8, hand_dy(hold[0][1] - 6.0)),
                        (tk + 0.2, t_past + 0.8, HI - hold[0][1]),
                        (tin + 0.1, t_past + 0.8, HW.BEAM_Y + 11.0 - HI),
                        (t_free, t_past + 0.8, -30.0)]             # (only once the beam is down: cc76)
        b.follow(tk, t_free, lambda tt: dict(x=self.glo_hand(tt)[0] + 4.0 - 4.0,
                                             y=self.glo_hand(tt)[1] + 6.0 - glo_bob(tt) * ease(tt, t_free - 0.8, t_free),
                                             ang=0.0), holder=("Glo", 0))
        b.move(t_free, t_free + 0.01, x=bx_end, y=HW.BEAM_Y + 11.0, ang=0.0)
        b.zf.append((t_free, b.z))                                 # on the posts: its own layer again
        self.glo_to(t_free + 0.4, HW.PL - 300.0, v=120.0)           # out of the frame (left) for the low beam
        # the low beam: once Glo is away with the top one (it would cross him), up at Hans' side, walked in, lifted
        # into place
        t1 = self.carry(lb, 1, tk + 1.2, 3.0, lift=40.0, x=hx0 + hold[1][0], y=hold[1][1], ang=0.0, back=0.0)
        tw = self.walk("tentacles", max(t1, t_free + 1.5) + 0.3, bx_end - hold[1][0])
        lb.follow(t1, tw, lambda tt: dict(x=self.hans_x(tt) + hold[1][0], y=hold[1][1]), holder=("Hans", 1))
        self.hans_hold(1, t1, tw, lambda tt: self.grip_pt(lb, tt, (0.0, 0.0)), reach=0.0, back=0.0)
        t = self.carry(lb, 1, tw, 3.4, x=bx_end, y=HW.AXLE_BEAM_Y, ang=0.0, reach=0.0)
        t_lb = t                                                   # (the low beam in: Glo can come over for the roof)
        t = self.walk("tentacles", t + 0.3, MILL["tentacles"])
        t = max(t, t0) + 0.4
        self.say["roof"] = t
        # r22 (round-21 part 2 must-fix "the boards are joined under the top beam and Glo lifts the A-frame up
        # through the beam and the posts"): nothing is put together under the beam any more. Hans lifts the two
        # boards off the pile by their tops at his right side, right of the frame and clear of it, and gives the
        # tops to Glo; they hang from his tendrils like a closed pair of compasses. Glo lifts them straight up there
        # till their feet are above the beam, floats them in over the frame, and sets their feet down on the beam's
        # middle; as he lowers the top the feet slide apart along the beam to its ends and the roof stands on them
        # (how a hinged A-frame is set on a wall). No board ever crosses the beam or a post.
        rL, rR = self.props["roof L"], self.props["roof R"]
        # r40 (round 39 part 1 must-fix "the roof is two thin rods that don't meet at the peak"): full length (268,
        # over the 263 span: they overlap at the ridge), each centred on its span, and drawn as wide planks (their
        # broad top face going back, ROOF_DEPTH) - was 250 long and shifted, 12 px apart at the ridge
        A = HW.ROOF_L[1]                                           # the apex: the boards' hinge
        fin = {nm: dict(x=(a_[0] + b_[0]) / 2, y=(a_[1] + b_[1]) / 2,
                        ang=math.degrees(math.atan2(b_[1] - a_[1], b_[0] - a_[0])))
               for nm, (a_, b_) in (("roof L", HW.ROOF_L), ("roof R", HW.ROOF_R))}
        FOLD = {"roof L": -76.0, "roof R": 76.0}                   # hanging closed: a narrow V, feet a little apart

        def ang_s(nm, s):
            return FOLD[nm] + (fin[nm]["ang"] - FOLD[nm]) * s

        def rot(v, d):
            r_ = math.radians(d)
            return v[0] * math.cos(r_) - v[1] * math.sin(r_), v[0] * math.sin(r_) + v[1] * math.cos(r_)

        def hinge_pose(nm, P, s):
            d = ang_s(nm, s) - fin[nm]["ang"]
            v = rot((fin[nm]["x"] - A[0], fin[nm]["y"] - A[1]), d)
            return dict(x=P[0] + v[0], y=P[1] + v[1], ang=ang_s(nm, s))

        def foot_dy(s):                                            # the feet below the hinge (both the same)
            d = ang_s("roof L", s) - fin["roof L"]["ang"]
            return rot((HW.ROOF_L[0][0] - A[0], HW.ROOF_L[0][1] - A[1]), d)[1]
        REST = HW.BEAM_Y - 2.0                                     # the feet on the beam's top

        def hinge_y(s):                                            # hinge height with the feet on the beam, s open
            return REST + (HW.ROOF_L[0][1] - REST) * s * s - foot_dy(s)

        def spread(py):                                            # how far open the feet on the beam let it be
            if py <= hinge_y(0.0):
                return 0.0
            lo, hi = 0.0, 1.0
            for _ in range(32):
                m = (lo + hi) / 2
                lo, hi = (m, hi) if hinge_y(m) < py else (lo, m)
            return min(1.0, lo)

        def grip_of(q, g):
            r_ = math.radians(q["ang"])
            return q["x"] + g[0] * math.cos(r_) - g[1] * math.sin(r_), q["y"] + g[0] * math.sin(r_) + g[1] * math.cos(r_)
        rL.p0["ang"] = -180.0                                      # (on the pile its top end lies left, like R's)
        for rb in (rL, rR):                                        # (darker roof boards: they read against the
            rb.p0["dark"] = ROOF_DARK                              # wood pile they hang by, and on the frame)
        P0 = (MILL["tentacles"] + ROOF_HANG_DX, ROOF_HANG_Y)        # where the boards hang from Glo, right of the frame
        HOLD_DY = 6.0                                              # the hinge just under Glo's hand
        self.line("roof", t)
        t = self.walk("tentacles", t, MILL["tentacles"])
        tg = self.glo_to(t_lb + 0.3, P0[0] + 4.0, v=110.0)        # over high, above the frame and Hans' head,
        t_dn = t_lb + 0.3                                          # and down beside Hans to take the tops
        dy1 = P0[1] - HOLD_DY - (self.glo_y(tg + 1.2) + GLO_HOLD + 10.0)
        over = ROOF_OVER_Y - (self.glo_y(tg + 1.2) + dy1)
        self.glo_dy += [(t_dn, tg + 0.3 + 0.6 * k, over / 3.0) for k in range(3)]   # (down gently, in three)
        gR, gL = (-72.0, 0.0), (72.0, 0.0)                         # by their top ends (r41: a little lower, so the
        # peak is clear for the peg)
        qR, qL = hinge_pose("roof R", P0, 0.0), hinge_pose("roof L", P0, 0.0)
        # both at once, one tentacle on each top, just as Glo comes down for them (they hang in front of the wood
        # pile, the same wood colour, only a moment before they go up)
        # r35 (round 34 part 1 must-fix "the roof boards appear out of nowhere"): first he slides each one out of
        # the stack along its length, flat, so they are seen leaving the pile, then swings it up to hang
        t_c = max(t + 0.2, tg + 1.6 - (ROOF_SLIDE[0] + 2.6) * 0.85 - ROOF_SLIDE[2])
        ends = []
        for k, (rb, sl, g, q) in enumerate(((rR, 1, gR, qR), (rL, 0, gL, qL))):
            p0 = rb.p0
            # r41 (round 40 part 1 must-fix "a board slides out of the stack with no tentacle on it"): out to the
            # right, away from him - to the left the end he held went in behind his body
            ts = self.carry(rb, sl, t_c + k * ROOF_SLIDE[2], ROOF_SLIDE[0], reach=0.6, back=0.0, grip=g,
                            x=p0["x"] + ROOF_SLIDE[1], y=p0["y"] - 10.0, ang=p0["ang"])
            ends.append(self.carry(rb, sl, ts, 2.6, reach=0.0, back=0.0, grip=g, **q))
        t1, t1L = ends
        # r41 (round 40 part 1 must-fix "by 138 two boards stand already joined; nobody puts them together"): with
        # both tops held together, his third tentacle takes the peg off the pile, turns it end on and pushes it
        # through the two tops; it stays there, at the roof's peak
        peg = self.props["roof peg"]
        A_R = (A[0] - fin["roof R"]["x"], A[1] - fin["roof R"]["y"])   # the hinge from roof R's middle

        def peg_at(tt):
            q_ = rR.at(tt)[0]
            v_ = rot(A_R, q_["ang"] - fin["roof R"]["ang"])
            return dict(x=q_["x"] + v_[0], y=q_["y"] + v_[1])
        tp0 = t1L + 0.1
        tp1 = self.carry(peg, 2, tp0, ROOF_PEG_T[0], grip=(-14.0, 0.0), lift=-30.0, reach=0.7, back=0.0,
                         x=P0[0], y=P0[1] - 26.0, ang=-90.0)       # (by its lower end: the peg shows above the tip)
        tp2 = tp1 + ROOF_PEG_T[1]
        peg.move(tp1, tp2, holder=("Hans", 2), x=P0[0], y=P0[1], end=1.0)

        def peg_push(tt):                                          # under it, then pressing its head in
            q_ = peg.at(tt)[0]
            return q_["x"], q_["y"] + 14.0 - 6.0 * q_.get("end", 0.0)
        self.hans_hold(2, tp1, tp2 + ROOF_PEG_T[2], peg_push, reach=0.0, back=0.7)
        peg.why_born = "lies on the wood pile from the start"
        peg.follow(tp2, 1e8, peg_at)
        t_tkR = t_tkL = max(tp2 + ROOF_PEG_T[2], tg + 1.6) + 0.4
        self.hans_hold(1, t1, t_tkR, lambda tt, pt=grip_of(qR, gR): pt, reach=0.0, back=0.7)
        self.hans_hold(0, t1L, t_tkL, lambda tt, pt=grip_of(qL, gL): pt, reach=0.0, back=0.7)
        t_up = t_tkL + 0.3
        HI = ROOF_HI_Y                                             # the feet well above the beam's top
        ups = [(t_up + 0.55 * k, (HI - P0[1]) / 5.0) for k in range(5)]
        tin = self.glo_to(t_up + 3.1, A[0] + 4.0, v=120.0)        # in over the frame, up there
        t_dn2 = tin + 0.1
        y0 = hinge_y(0.0)                                          # its feet just on the beam
        downs = [(t_dn2, y0 - HI)]
        t_sp = t_dn2 + 0.8                                         # then the top comes down at an even pace of
        T_SP = 3.4                                                 # opening (s), the feet sliding out evenly
        self.glo_fy.append((t_sp, t_sp + T_SP, 0.0, A[1] - y0,
                            lambda u: (hinge_y(smoothstep(u)) - y0) / (A[1] - y0)))
        t_l1 = t_sp + T_SP + 0.1
        t_rel = t_l1 + 0.2
        t_a = self.glo_to(t_rel, HW.ROOF_L[0][0] - 90.0, v=150.0)  # out to the left, clear of the eave
        self.glo_dy.append((t_dn, t_a + 3.3, dy1))
        self.glo_dy += [(s0, t_a + 0.8 + 0.5 * k, d_) for k, (s0, d_) in enumerate(ups)]
        self.glo_dy += [(s0, t_a + 0.3, d_) for s0, d_ in downs]  # (he rises as he goes, then sinks out left)
        self.glo_fy[-1] = self.glo_fy[-1][:2] + (t_a + 0.3,) + self.glo_fy[-1][3:]
        self.roof_hold = (t_tkR, t_rel)

        def held(tt, nm):
            hx = self.glo_x(tt) - 4.0 if hasattr(self, "paths") else A[0]
            hy = self.glo_y(tt) + GLO_HOLD + 10.0 + HOLD_DY
            s = spread(hy) if tt >= t_dn2 else 0.0
            w = ease(tt, t_up, t_up + 0.6) * (1.0 - ease(tt, tin - 0.8, tin))
            return hinge_pose(nm, (hx, hy + glo_bob(tt) * w), s)
        rR.follow(t_tkR, t_l1, lambda tt: held(tt, "roof R"), holder=("Glo", 0))
        rL.follow(t_tkL, t_l1, lambda tt: held(tt, "roof L"), holder=("Glo", 0))
        for nm in ("roof L", "roof R"):
            self.props[nm].move(t_l1, t_l1 + 0.01, **fin[nm])     # (exactly on the beam's ends)
        for rb in (rL, rR):                                        # in front of the wood pile while they hang by
            rb.zf = [(t_c, 19.0), (tin - 1.5, rb.z)]               # it (high over the frame: their own layer)
        peg.zf = [(tp0, 19.5), (tin - 1.5, rR.z + 0.2)]            # (r41: the peg over the boards' tops)
        self.glo_to(t_a + 2.2, GLO_HOME, v=150.0)
        return t_rel + 0.8

    def trim_board(self, nm, t, a, b, slot=0, z_board=12.0, trim=True, side=0.0):
        """Hans lays board nm on the rack against the stop block; Twigs trims its end at the notch (the offcut drops
        behind the rack); Hans takes it to its place, from a to b (world) -> end time."""
        p = self.props[nm]
        tr = HOPPER_TRIM if trim else 18.0                         # r33: how much is sawn off (the offcut)
        L = p.p0["L"] - tr
        h_at = HANS_RACK if trim else MILL["tentacles"]
        t = self.walk("tentacles", t, h_at)                        # (r4: by the rack, not reaching to it)
        if trim:
            on_rack = dict(x=HW.STOP_X + (L + tr) / 2, y=HW.RACK_Y - 7.0, ang=0.0)
            t1 = self.carry(p, slot, t, 1.8, lift=40.0, grip=(-40.0 if side else 0.0, 0.0), **on_rack)   # (r16: a hopper
            # board by its near half, not its middle on the far side of the pile)
            c1, t_back = self.cut(t1 - 0.3, TW_MILL, HW.NOTCH_X, HW.RACK_Y - 6.0, strokes=4)
            self.rack_trims = getattr(self, "rack_trims", []) + [(t1, self.twigs_cuts[-1]["c0"], c1)]   # r33: mark, kerf
            p.move(c1, c1 + 0.01, L=L, off=-tr / 2)                 # the offcut comes off (its own prop)
            oc = self.prop(nm + " offcut", "board", 2.5, tr / 2, born=c1, x=HW.NOTCH_X + tr / 2, y=HW.RACK_Y - 7.0,
                           ang=0.0, L=tr, th=p.p0["th"], dark=p.p0.get("dark", 0.0))
            oc.why_born = "sawn off by Twigs' blade"
            oc.move(c1, c1 + 0.42, how="fall", x=HW.NOTCH_X + tr / 2 + 11.0, y=HW.FLOOR - 8.0, ang=35.0)
        else:                                                      # a board straight off the pile
            c1 = t - 0.4
            p.p0["L"], p.p0["off"] = L, -9.0
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if trim and tr != 18.0:                                    # r33: the longer offcut moved the board's drawn
            ca_, sa_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))   # middle (off); placed where it was
            mid = (mid[0] + (tr / 2 - 9.0) * ca_, mid[1] + (tr / 2 - 9.0) * sa_)
        hx = min(MILL["tentacles"], mid[0] + 20.0)                   # within his reach of where it goes
        ge = 0.0
        if not trim:                                               # a roof board: held by its low (eave) end
            left = a[1] > b[1]
            ge = -(L / 2) + 25.0 if left else (L / 2) - 25.0
            hx = min(MILL["tentacles"], (a[0] + 40.0) if left else (b[0] + 10.0))
        tw = c1 + 0.4
        if side:                                                   # r11 (part 2 must-fix: a tentacle ran up across
            # his face to the beam): he takes it low, walks it along at his left below his face, and puts it up by
            # its low end from well to the right of it, a side tentacle reaching out (not up past his face)
            ge = L / 2 - 22.0
            hx, hold_y = b[0] + side, HW.FLOOR - 25.0
            off = -150.0 - ge
            hs = h_at + 70.0                                       # (r16: a step along the rack to its end first,
            ts = self.walk("tentacles", c1 + 0.2, hs)              # not reaching 220 px to it)
            t1 = self.carry(p, slot, ts, 1.6, lift=0.0, x=hs + off, y=hold_y, reach=0.4, back=0.0,
                            grip=(ge, 0.0))
            tw = self.walk("tentacles", t1, hx)
            p.follow(t1, tw, lambda tt, off=off: dict(x=self.hans_x(tt) + off, y=hold_y), holder=("Hans", slot))
            self.hans_hold(slot, t1, tw, lambda tt, p=p: self.grip_pt(p, tt, (ge, 0.0)), reach=0.0, back=0.0)
            t2 = self.carry(p, slot, tw, 2.4, lift=10.0, x=mid[0] + 9.0, y=mid[1], ang=ang, reach=0.0, grip=(ge, 0.0))
            self.last_place = t2
            if hasattr(self, "mill_cam"):                          # r31: the camera on the cut, then on the beam
                self.mill_cam += [(t, 2.0, 1.8, HW.NOTCH_X - 90.0, 800.0),    # (t: he's at the rack)
                                  (c1 + 0.6, 0.0, 1.8, HW.NOTCH_X - 90.0, 800.0),
                                  (tw - 0.2, min(2.6, tw - c1 - 0.8), 1.75, mid[0] + 60.0, 640.0),
                                  (t2 + 1.0, 0.0, 1.75, mid[0] + 60.0, 640.0)]
            self.walk("tentacles", t2 + 0.3, MILL["tentacles"])
            return self.walks["tentacles"][-1][0]
        if hx < MILL["tentacles"] - 20:
            t1 = self.carry(p, slot, c1 + 0.4, 1.2, lift=50.0, x=HW.STOP_X + 40.0, y=HW.RACK_Y - 48.0, reach=0.4,
                            back=0.0, grip=(ge, 0.0))
            tw = self.walk("tentacles", t1, hx)
            off = HW.STOP_X + 40.0 - h_at                          # held where he took it, beside him, as he goes
            p.follow(t1, tw, lambda tt, off=off: dict(x=self.hans_x(tt) + off, y=HW.RACK_Y - 48.0), holder=("Hans", slot))
            self.hans_hold(slot, t1, tw, lambda tt, p=p: self.grip_pt(p, tt, (ge, 0.0)), reach=0.0, back=0.0)
            t2 = self.carry(p, slot, tw, 2.2, lift=10.0, x=mid[0] + 9.0, y=mid[1], ang=ang, reach=0.0, grip=(ge, 0.0))
            self.last_place = t2
            self.walk("tentacles", t2 + 0.3, MILL["tentacles"])
            return self.walks["tentacles"][-1][0]
        t2 = self.carry(p, slot, c1 + 0.4, 2.6, lift=70.0 if trim else 20.0, x=mid[0] + 9.0, y=mid[1], ang=ang,
                        reach=0.4, grip=(ge, 0.0))
        self.last_place = t2
        return t2

    # ---------------------------------------------------------------- 4. the millstones
    def _stones(self, t):
        t_say = self.line("stones", t)
        self.dress = []
        self.stone_base = {}
        for i, (sx, sy) in enumerate(HW.STONES):
            s = self.props[f"millstone {i}"]
            q = s.end_pose()
            dress_at = (1330.0, GB - 2 - HW.STONE_R)
            t_c = max(t, t_say - 1.5)
            if i == 0:
                t_fetch0 = t_c
            side = STONE_SIDE
            t_c = self.walk("tentacles", t_c, q["x"] + side, v=125.0) + 0.8   # r10: he stands to its right (not over
            # it) (r31: brisker, it's across the frame now: ~4.5 s)
            # r31 (r30 widened the frame for gear 2, so there was no room left to bring the stones out right of the
            # right post before Twigs): each lies in the shallows just left of the left post. Lifted low at Hans' left
            # (behind the frame), it comes forward right there, clear of the post and the low beam's end (in front
            # from then on), and is walked right in front of the frame to where it's dressed. Nearer one first.
            # (r23: both stones take the same route.)
            s.zf = getattr(s, "zf", []) + [(t_c, 0.5)]             # (behind the low beam, the gears and the posts)
            # r35 (round 34 part 1 must-fix "a flat oval in the water, half a second later an upright disc on the
            # grass"): two tentacles take it, top rim and near rim, it rises slowly out of the water (the water
            # falls away from it, drips run off), tilting up a little at a time as it comes to the bank
            tA = self.carry(s, -1, t_c, STONE_LIFT[0], x=q["x"], y=q["y"] - STONE_LIFT[1], tilt=0.18, wet=0.6,
                            grip=STONE_GRIP, rot=False)            # (up out of the water, still nearly flat)
            # r36 (round 35 part 1 must-fix "the stone goes through the left post": the near one lies right behind
            # it): as it comes out to the bank it is brought left until it is clear of the post (he steps along),
            # and only then comes forward in front of it
            dx = min(0.0, HW.PL - STONE_POST_CLEAR - HW.STONE_R - q["x"])
            x1 = q["x"] + dx
            if dx < 0.0:
                self.walk("tentacles", tA, q["x"] + side + dx)
            # r46 (round 45 part 1 must-fix "the flat oval turns into a big upright disc in 0.4 s": it was tipped up
            # while passing behind his fin): it stays nearly flat until it is out in the open left of him, and is
            # tipped upright there slowly, his tentacle on its top rim turning it over (2.8 s)
            t1 = self.carry(s, -1, tA, STONE_LIFT[2], x=x1, y=q["y"] + STONE_LOW_DY, tilt=0.22, wet=0.25,
                            reach=0.0, grip=STONE_GRIP, rot=False)   # (out, low beside him, under his fin)
            self.hans_hold(0, t_c + 0.3, t1, lambda tt, s=s: self.grip_pt(s, tt, STONE_GRIP2), reach=0.7, back=0.7)
            s.zf.append((t1 + 0.1, s.z))                           # clear of the post: in front from here
            t1 = self.carry(s, -1, t1 + 0.2, 2.8, x=x1, y=STONE_FWD_Y, tilt=0.7, wet=0.0, reach=0.0,
                            grip=STONE_GRIP, rot=False)            # forward, in the open left of the post
            h2 = self.walks["tentacles"][-1][1]                     # r46: where he is (the carry may have stepped him in)
            tw = self.walk("tentacles", t1 + 0.2, dress_at[0] + side)
            s.follow(t1, tw, lambda tt, h2=h2, x0=x1: dict(x=x0 + self.hans_x(tt) - h2, y=STONE_FWD_Y),
                     holder=("Hans", -1))
            self.hans_hold(-1, t1, tw, lambda tt, s=s: self.grip_pt(s, tt, STONE_GRIP), reach=0.0, back=0.0)
            t1 = tw
            t1 = self.carry(s, -1, t1, 2.4, x=dress_at[0], y=dress_at[1], tilt=1.0, reach=0.0,
                            grip=STONE_GRIP, rot=False)
            t_back = t1
            if self.walks["tentacles"][-1][1] < DRESS_HANS - 20.0:   # r9 (part 1 must-fix): he stepped in for it;
                t_back = self.walk("tentacles", t1 + 0.3, DRESS_HANS)   # back out, his legs clear of the stone face
            # Digs comes up on its left, taps the eye through and cuts six grooves
            td = self.walk("digger", max(t1 - 2.0, self.walks["digger"][-1][0]), 1330.0 - DRESS_STAND)
            if i == 0:
                self.say["dress"] = td
            taps = []
            tt = max(td, t1) + 0.3
            for g in range(7):                                      # the eye first, then the six grooves; between
                taps.append((tt, tt + (EYE_TAPS * 0.7 if g == 0 else 1.5)))   # grooves Digs turns the stone a sixth,
                tt += EYE_TAPS * 0.7 + 0.15 if g == 0 else 3.3      # so each groove is cut right under his paw (part 1 review;
                # r33: 1.1 -> 1.5 s a groove, so the claw drawing it out is seen)
                # r5: "grooves appear where his claw never touches" - he now hooks the fresh groove and pulls the stone
                # round a sixth himself, slowly, then goes back to the eye for the next one)
            self.dress.append(dict(stone=i, taps=taps))
            self.digs_jobs.append((taps[0][0] - 0.4, taps[-1][1] + 0.4, "dress", i))
            s.follow(taps[0][0], taps[-1][1] + 0.01, lambda t_, i=i: self.stone_dressing(i, t_))
            # r14 (part 1 must-fix "grooves appear where the claws are not, the stone never turns"): Hans holds the
            # stone up by its right rim the whole time and turns it on a sixth between grooves, his tentacle tip
            # going round with the rim; Digs' claw only cuts, always at the same spot under his paw
            self.hans_hold(-1, max(t_back, t1 + 0.9) + 0.6, tt + 0.2, lambda t_, i=i: self.rim_grip(i, t_),
                           reach=0.6, back=0.4)
            t2 = self.walk("digger", tt + 0.2, 950.0)
            # r31 (round 30 part 2 must-fix "stone 2 is mounted in about 2 s in the wide shot, mostly behind Hans'
            # head"): he first steps right, clear of the axle, then lifts it on slowly, the camera close on the mill
            t_m = tt + 1.4
            if abs(self.walks["tentacles"][-1][1] - (sx + MOUNT_STAND[i])) > 30.0:   # (r33: 5 -> 30; a 20 px
                # shuffle from the dressing spot to the mount spot read as a crab walk: he lifts it from where he is)
                t_m = max(t_m, self.walk("tentacles", tt + 0.4, sx + MOUNT_STAND[i]) + 0.3)
            t3 = self.carry(s, -1, t_m, 4.0, lift=30.0, x=sx, y=sy, tilt=1.0, grip=MOUNT_GRIP, rot=False)
            self.mounts = getattr(self, "mounts", []) + [(taps[-1][1] + 0.2, t3)]
            base = self.stone_dressing(i, taps[-1][1])["ang"]
            s.follow(t3, 1e8, lambda t_, i=i, base=base: dict(ang=self.stone_ang(i, t_) + base))
            self.stone_base[i] = base
            t = t3 + 0.3
            if i == 0:                                              # r46 (round 45 part 1 must-fix "Hans stands right
                # in front of stone 1 and its gear just after mounting it"): he steps back right, clear of the mill,
                # and lets the mounted stone be seen for a beat before he goes for the second one
                t = self.walk("tentacles", t, DRESS_HANS + 20.0) + 2.2
        self.line("dress", self.say["dress"])
        # r23 (part 1 must-fix "the stone's trip from the shallows is barely seen"): the close view starts as the
        # first stone is fetched (it shows the shallows, the post and Hans out right as well as the dressing)
        z_prev = max(k[1] for k in self.zoom_keys if k[0] < t_fetch0)
        # r29 (round 28 part 2 must-fix "the claw stays on one spot while the furrows appear elsewhere"): while each
        # stone is dressed the camera eases closer still, on the stone, so the claw running up each groove and Hans
        # turning the stone a sixth under it read clearly; it eases back out for the next fetch
        wins = [(d["taps"][0][0] - 0.6, d["taps"][-1][1] + 0.2) for d in self.dress]
        def wz(t_, wins=wins):
            return max(ease(t_, a - 1.6, a) * (1.0 - ease(t_, b, b + 1.6)) for a, b in wins)
        # r31: after the second dressing the camera goes straight on to the mount view (not out first), and holds it
        # till that stone is on its axle
        ma, mb = self.mounts[-1]
        def mcam(t_, k):
            base = (1.65, 1300.0, 830.0)[k]                        # (r31: x 1300, was 1440: the stones lie left now)
            v = base + (DRESS_ZOOM[k] - base) * wz(t_)
            return v + (MOUNT_ZOOM[k] - v) * ease(t_, ma, ma + 1.6)
        self.mount_end = mb + 0.3                                  # (the pulley's camera move carries on from here)
        self.zoom_on(max(z_prev, min(t_fetch0 - 0.5, self.dress[0]["taps"][0][0] - 2.5)), self.mount_end,
                     lambda t_: mcam(t_, 0), lambda t_: mcam(t_, 1), lambda t_: mcam(t_, 2), rin=2.0, rout=0.0)
        del self.mounts
        return t

    def rim_grip(self, i, t):
        """Where Hans' tentacle tip holds stone i's rim while Digs dresses it (r14): at RIM_A (screen deg, its right
        side) while a groove is cut; during each turn the grip goes round with the stone (up), then slides back."""
        tp = self.dress[i]["taps"]
        ang = self.stone_dressing(i, t)["ang"]
        a0 = GROOVE_AT - 7.2
        g = RIM_A
        for k in range(1, len(tp) - 1):
            ta, tb = tp[k][1] + 0.1, tp[k + 1][0] - DRESS_BACK
            if t < ta:
                break
            if t < tb:
                g = RIM_A + (ang - (a0 + 60.0 * (k - 1)))         # (r33: clockwise, down the right side)
                break
            g = RIM_A + 60.0 * (1.0 - ease(t, tb, tb + 0.6))
        s = self.props[f"millstone {i}"].at(t)[0]
        rr = HW.STONE_R - 5.0
        a = math.radians(g)
        return s["x"] + rr * math.cos(a), s["y"] + rr * math.sin(a)

    def stone_dressing(self, i, t):
        """The eye, the grooves cut so far, and how the stone is turned: groove g (at the stone's own angle
        60g + 14) is cut at its left, under Digs' paw, and he turns it a sixth between grooves."""
        d = self.dress[i]
        eye = eye_open(t, *d["taps"][0])
        g = sum(ease(t, a + 0.15, b - 0.05) for a, b in d["taps"][1:])
        tp = d["taps"]
        ang = GROOVE_AT - 7.2                                       # (r3: across the claw's sweep, so it runs out along it)
        for k in range(1, 6):                                       # turning on after groove k-1 to groove k
            ang += 60.0 * ease(t, tp[k][1] + 0.1, tp[k + 1][0] - DRESS_BACK)   # r33 (round 32 part 2 must-fix
            # "grooves appear far from the claw"): clockwise, so each fresh groove comes out from under his paw to the
            # upper right, in plain sight, instead of passing under his arm. r8: anticlockwise, Digs pulling
            # the hooked groove round towards himself, his claw tip sliding in it (it stays on his reach circle)
        return dict(hole=eye, grooves=g, ang=ang)

    # ---------------------------------------------------------------- 5. the gears and the pulley
    def _gears(self, t):
        """Each gear starts as a square board. Hans holds it up face-on with its lower edge at Twigs' blade and turns
        it a quarter at a time: Twigs cuts each corner off (they drop), then a tooth at a time all the way round."""
        self.say["gears"] = t
        self.line("gears", t)
        self.discs = []
        self.demo = (1e9, 1e9 + 1.0)                              # r19: when the two mounted gears are turned to show
        hold = (GEAR_CUT[0] - BLANK, GEAR_CUT[1])                # its right rim at the blade, clear of Twigs' body
        for i in range(2):
            d = self.props[f"gear {i}"]
            t = self.walk("tentacles", t - (1.0 if i == 0 else 0.0), HANS_GEARS)   # (r4: close to the blade, no stretch)
            a_in = math.radians(225.0)                            # the turning tentacle's first spot (upper left)
            # r35 (round 34 part 1 must-fix "the square boards pop into his tentacle across the push-in"): he lifts
            # it off the pile first, edge-on, in the wide shot, then turns it face-on into his hold; the push-in
            # only starts once it is there (see the zoom_on below)
            g_in = (TURN_R * math.cos(a_in), TURN_R * math.sin(a_in))
            q0 = d.p0
            t_off = self.carry(d, 1, t, 1.6, lift=30.0, x=q0["x"] - 45.0, y=q0["y"] - 34.0, face=0.25, ang=-10.0,
                               grip=g_in, back=0.0)
            t1 = self.carry(d, 1, t_off, 2.4, lift=20.0, x=hold[0], y=hold[1], face=1.0, ang=-45.0,
                            grip=g_in, reach=0.0, back=0.0)       # a corner at the blade
            # the corners: turn, cut, turn, cut... (the corner at the bottom is the one at the blade)
            cuts = []                                              # (part 1 review: the sawing must be seen, and
            tc = t1 + 2.0                                          # each turn slow enough to follow; r35: 2.0, was
            # 0.9: the push-in is in before the first corner)
            for j in range(4):
                cuts.append(("corner", (tc, tc + CORNER_CUT)))
                tc += CORNER_CUT + CORNER_GAP                      # (r5: a quarter turn in 1.45 s, not 0.75)
            for j in range(TEETH):
                cuts.append(("tooth", (tc, tc + TOOTH_CUT)))
                tc += TOOTH_CUT + TOOTH_GAP                        # (r5: "jumps 30-45 degrees in 0.2 s")
            self.twigs_cuts.append(self._turn_cuts(t1 - 0.2, cuts))
            d.follow(t1, tc + 0.3, lambda tt, cuts=cuts: self.blank_turn(cuts, tt), holder=("Hans", 1))
            # r5 ("the board turns with nothing turning it"): one tentacle lies on its face and drags it round each
            # step, then slides back while the blade cuts; the other steadies its top while it's cut
            self.hans_hold(1, t1, tc + 0.3, lambda tt, d=d, cuts=cuts: self.turn_grip(d, cuts, tt, "turn"),
                           reach=0.0, back=0.0)
            self.hans_hold(2, t1 + 0.3, tc + 0.3, lambda tt, d=d, cuts=cuts: self.turn_grip(d, cuts, tt, "steady"),
                           reach=0.6, back=0.6)
            g_end = self.turn_grip(d, cuts, tc + 0.3, "turn")
            g_end = (g_end[0] - d.at(tc + 0.3)[0]["x"], g_end[1] - d.at(tc + 0.3)[0]["y"])
            # r42 (round 42 part 1 must-fix "nothing comes off the boards: the corners and tooth gaps vanish"): each
            # corner (a right triangle, its long side the cut) and each tooth gap (a little wedge) drops from the
            # blade as it's cut free and lies flat on the ground, left of Twigs' feet where it's seen (the corners
            # used to land behind his leg as round brown blobs)
            for j in range(4):
                c1 = cuts[j][1][1]
                oc = self.prop(f"gear {i} corner {j}", "corner", 5.5, 24.0, born=c1, x=GEAR_CUT[0] + 17.5,
                               y=GEAR_CUT[1], ang=90.0, fy=1.0)
                oc.why_born = "cut off the corner by Twigs' blade"
                oc.move(c1, c1 + 0.42, how="fall", x=OFFCUT_LAND[j] - 6.0 * i, y=OFFCUT_Y + 3.0 * i,
                        ang=(0.0, 180.0, 0.0, 180.0)[j], fy=0.42)
            for m in range(TEETH):
                c1 = cuts[4 + m][1][1]
                ch = self.prop(f"gear {i} chip {m}", "chip", 5.6, 14.0, born=c1,
                               x=GEAR_CUT[0] - NOTCH_D / 2 + 2.0, y=GEAR_CUT[1], ang=0.0, fy=1.0)
                ch.why_born = "the wood sawn out of the notch by Twigs' blade"
                ch.move(c1, c1 + 0.38, how="fall", x=CHIP_LAND[m] - 5.0 * i, y=OFFCUT_Y + 6.0 + 2.0 * i,
                        ang=90.0 + (14.0 if m % 2 else -11.0), fy=0.5)
            sx, sy = HW.STONES[i]
            # he walks it over to the stones, held beside him as it was cut (r4: no tentacle across the mill)
            tw = self.walk("tentacles", tc + 0.3, sx + 125.0)              # (r17: was 170, a 236 px reach to the peg)
            off = hold[0] - HANS_GEARS
            d.follow(tc + 0.3, tw, lambda tt, off=off: dict(x=self.hans_x(tt) + off, y=hold[1]), holder=("Hans", 1))
            self.hans_hold(1, tc + 0.3, tw, lambda tt, d=d, g=g_end: self.grip_pt(d, tt, g), reach=0.0, back=0.0)
            tg = tw + 0.3                                          # r20: straight on to its bare peg
            d.follow(tw, tg, lambda tt, x=self.hans_x(tw) + off: dict(x=x, y=hold[1]), holder=("Hans", 1))
            self.hans_hold(1, tw, tg, lambda tt, d=d, g=g_end: self.grip_pt(d, tt, g), reach=0.0, back=0.0)
            d.zf = [(t, GEAR_CARRY_Z), (tg + 3.6 * 0.85 * 0.5, 2.0)]   # in front of the pile while cut; behind the
            base = self.blank_turn(cuts, tc + 0.01)["ang"] + (GEAR_MESH_OFF if i else 0.0)   # meshing at the nip
            base += -GEAR_REST_PH if i else GEAR_REST_PH            # r41: see GEAR_REST_PH
            # r29 (round 28 part 2 must-fix "the gears' upper right teeth hidden by the stone's thickness"): the gear
            # goes on at the back of its axle, a stone's thickness behind the axle's end (DV), so once the stone is
            # slid on in front of it its teeth show evenly all round the stone's back rim
            # r30 (round 29 part 2 must-fix "the gears hidden behind the stones, a few tabs"): the gear goes onto the
            # axle's end, then is slid back along it (`GEAR_GAP` far behind the stone), so it shows up-right of the
            # stone with most of its teeth and the mesh above the nip; its axle runs forward over it to the peg end
            gbx, gby = gear_back()
            # r45: straight onto the axle at its hub (the axle end on at the hub, no slide back along it)
            t_on = self.carry(d, 1, tg, 3.6, lift=150.0, x=sx + gbx, y=sy + gby, grip=g_end, reach=0.0, ang=base)
            t2 = t_on + 0.6
            self.hans_hold(1, t_on, t2 + 0.2, lambda tt, d=d, g=g_end: self.grip_pt(d, tt, g), reach=0.0, back=0.5)
            self.gear_on = getattr(self, "gear_on", {})
            self.gear_on[d.name] = (t_on, sx + gbx, sy + gby)
            d.follow(t2, 1e8, lambda tt, i=i, base=base: dict(ang=self.stone_ang(i, tt) + base + self.mesh_demo(i, tt),
                                                             face=1.0))
            self.discs.append(dict(cuts=cuts, fit=t2, held=t1))
            t_z1 = t2 + 1.5
            if i == 1:                                             # r23 (round-22 part 2 must-fix: the line "one gear
                t_cl = self.walk("tentacles", t2 + 0.2, sx + GEAR_DEMO_STAND)   # r24 (part 1: he stood in front of the
                td0 = t_cl + 0.6                                   # dark gear while turning it) a step right, clear of it
                # (r23) the line "one gear behind each stone..." came with both gears hidden
                self.demo = (td0, td0 + GEAR_DEMO_T)               # behind the stones): right after the second one
                self.line("gears2", td0 - 0.6)                     # goes on, both on bare pegs in plain sight, Hans
                a0 = math.radians(-20.0 - base)                    # turns it slowly by its right rim and the other
                g_rim = ((HW.GEAR_R - 4.0) * math.cos(a0), (HW.GEAR_R - 4.0) * math.sin(a0))   # turns the other way
                self.hans_hold(2, td0, td0 + GEAR_DEMO_T + 0.2, lambda tt, d=d, g=g_rim: self.grip_rot(d, tt, g),
                               reach=0.7, back=0.6)
                t_z1 = td0 + GEAR_DEMO_T + 1.4
                t2 = td0 + GEAR_DEMO_T + 0.7
            self.zoom_on(tw - 2.0, t_z1, 1.5, sx + 60.0, 780.0, rin=2.0, rout=2.0)   # the gear going on its peg
            t = t2 + 0.3
        for dc in self.discs:                                      # r5: closer on the cutting (the corners and
            self.zoom_on(dc["held"] - 0.3, dc["cuts"][-1][1][1] + 3.0, 1.9, GEAR_CUT[0] - 120.0, 800.0,   # r42 (+3.0, was
                         # +0.6: round 41 part 1 must-fix "the last teeth pop in across the cut": the last notch is
                         # sawn while still close, and held a beat)
                         rin=2.0, rout=2.0)                        # teeth were small, half hidden)
        return t

    def mesh_demo(self, i, tt):
        """r19/r20: the mesh shown: stone 1 (and its gear) turned slowly by hand, stone 0 and its gear the other way."""
        return (-GEAR_DEMO if i == 0 else GEAR_DEMO) * ease(tt, *self.demo)

    def _mesh_pulley(self, t):
        """r20: both stones on, in front of their gears: Hans turns the right one slowly by its rim and the left one
        turns the other way (the gears behind them mesh, their teeth showing round the rims). Then the pulley."""
        (sx0, sy0), (sx, sy) = HW.STONES
        s = self.props["millstone 1"]
        t_st = t if self.walks["tentacles"][-1][1] >= sx + MOUNT_STAND[1] - 1.0 else             self.walk("tentacles", t + 0.2, sx + 210.0)              # a step right, clear of the stone (r31: he
        # already is, from the mount: no extra little steps)
        t = t_st + 0.5                                             # (r23: the turn by hand is done on the bare
                                                                   # gears now, before the stones go on)
        # the pulley: a slice off the thin pole on the rack
        tp = self.props["thin pole"]
        # r12 (part 2 must-fix: the pole vanished behind him on the rack and the slice appeared with no cut seen): he
        # stands back to the left, lays it on the rack by its left end, holds that end down while Twigs saws the
        # slice off at the notch, all in a close shot
        t = self.walk("tentacles", t + 0.2, HANS_POLE_HOLD)
        t1 = self.carry(tp, 2, t, 1.8, lift=30.0, x=HW.NOTCH_X - 100.0 + 12.0, y=HW.RACK_Y - 24.0, grip=(-88.0, 0.0),
                        back=0.0)
        c1, tb = self.cut(t1 + 0.2, TW_MILL, HW.NOTCH_X, HW.RACK_Y - 24.0, strokes=5)
        self.hans_hold(2, t1, c1 + 0.2, lambda tt: self.grip_pt(tp, tt, (-88.0, 0.0)), reach=0.0, back=0.6)
        e = self.mount_end                                         # r31: straight on from the mount view, a pan
        self.mill_cam = [(e, e, *MOUNT_ZOOM[:1], MOUNT_ZOOM[1], MOUNT_ZOOM[2]),   # over to the rack
                         (t1 + 0.4, max(1.5, t1 + 0.4 - e), 1.8, HW.NOTCH_X - 90.0, 800.0)]   # r31: one camera move from the
        # slice on (round 30 part 2 must-fixes "the hopper/pulley build is one 48 s wide shot", "the pulley appears
        # unseen"): see _hopper_belt
        t = self.walk("tentacles", c1 + 0.9, HANS_POLE)
        pu = self.prop("pulley", "pulley", 4, HW.PULLEY_R, born=c1, x=HW.NOTCH_X + 6.0, y=HW.RACK_Y - 24.0, ang=0.0,
                       face=0.0)
        pu.why_born = "sliced off the thin pole by Twigs' blade"
        tp.move(c1, c1 + 0.01, x1=100.0 - 24.0)
        # r22 (round-21 part 2 must-fix "the pulley floats across Hans' face, the tentacle hidden behind him"): he
        # carries it low at his right side, below his face, stops right of the stone, passes it across low in front
        # of his legs to his left side and only there lifts it onto the axle's end
        y_c = PULLEY_LOW_Y
        t_in = self.carry(pu, 1, t + 0.1, 1.2, lift=20.0, x=HANS_POLE + 110.0, y=y_c, back=0.0)
        tw = self.walk("tentacles", t_in, HW.STONES[0][0] + 170.0)  # walked over to the stone (r4: no stretch)
        pu.follow(t_in, tw, lambda tt: dict(x=self.hans_x(tt) + 110.0, y=y_c), holder=("Hans", 1))
        self.hans_hold(1, t_in, tw, lambda tt: self.grip_pt(pu, tt, (0.0, 0.0)), reach=0.0, back=0.0)
        t_sl = tw + 1.8
        pu.move(tw, t_sl, x=HW.STONES[0][0], y=y_c, holder=("Hans", 1))
        self.hans_hold(1, tw, t_sl, lambda tt: self.grip_pt(pu, tt, (0.0, 0.0)), reach=0.0, back=0.0)
        t2 = self.carry(pu, 1, t_sl, 2.0, x=HW.STONES[0][0], y=HW.STONES[0][1], face=1.0, reach=0.0)
        pu.follow(t2, 1e8, lambda tt: dict(ang=self.stone_ang(0, tt), face=1.0))
        self.mill_cam.append((tw, tw - t_in, 2.0, HW.STONES[0][0] + 70.0, 790.0))   # (along with him, on the stone)
        self.mill_cam.append((t2 + 1.0, 0.0, 2.0, HW.STONES[0][0] + 70.0, 790.0))
        return t2 + 0.4

    @staticmethod
    def turn_win(cuts, j):
        """r19: when the blank turns on to cut j: after the blade is out and the cut has shown, before it goes back in."""
        return cuts[j - 1][1][1] + TURN_OUT + TURN_STILL, cuts[j][1][0] - TURN_IN

    def turn_grip(self, d, cuts, t, hand):
        """Hans turning a gear blank hand over hand (r5). "turn": lies on its face at TURN_R, moves with it through each
        turn (exactly as blank_turn turns it), then slides back round (lifting a little) while the next cut is made.
        "steady": rests on its top while it's cut, eased off while it turns."""
        q = d.at(t)[0]
        X, Y = q["x"], q["y"]
        ends = [b for _, (a, b) in cuts]
        starts = [a for _, (a, b) in cuts]
        steps = [tooth_step(cuts, j) for j in range(len(cuts))]
        if hand == "steady":
            off = 0.0
            for j in range(1, len(cuts)):
                a0, a1 = self.turn_win(cuts, j)
                if a0 - 0.2 <= t <= a1 + 0.2:
                    off = max(off, ease(t, a0 - 0.2, a0 + 0.1) * (1.0 - ease(t, a1 - 0.1, a1 + 0.2)))
            r, th = TURN_R + 6.0 + 12.0 * off, math.radians(STEADY_AT)
            return X + r * math.cos(th), Y + r * math.sin(th)
        th, r = 180.0 + steps[min(1, len(cuts) - 1)] / 2.0, TURN_R
        for j in range(1, len(cuts)):
            a0, a1 = self.turn_win(cuts, j)
            if t < a0:
                break
            th, r = 180.0 + steps[j] / 2.0 - steps[j] * ease(t, a0, a1), TURN_R   # turning with it
            if t <= a1 or j + 1 >= len(cuts):
                break
            u = ease(t, starts[j] + 0.1, ends[j] - 0.1)            # sliding back round while it's cut
            th = 180.0 - steps[j] / 2.0 + (steps[j] + steps[j + 1]) / 2.0 * u
            r = TURN_R + 10.0 * math.sin(math.pi * u)
        th = math.radians(th)
        return X + r * math.cos(th), Y + r * math.sin(th)

    def grip_pt(self, p, t, g):
        q = p.at(t)[0]
        g = stone_squash(p, q, g)
        return q["x"] + g[0], q["y"] + g[1]

    def grip_rot(self, p, t, g):
        """A point g on prop p in its own (turned) frame, like carry's grip."""
        q = p.at(t)[0]
        a = math.radians(q.get("ang", 0.0))
        return q["x"] + g[0] * math.cos(a) - g[1] * math.sin(a), q["y"] + g[0] * math.sin(a) + g[1] * math.cos(a)

    def _turn_cuts(self, t0, cuts):
        """Twigs holds his blade at the turning blank's lower rim: three strokes through each corner, a nick for each
        tooth."""
        if abs(self.walks["teeth"][-1][1] - TW_MILL) > 1.0:       # r31: Twigs steps up to the rack first
            dx = abs(self.walks["teeth"][-1][1] - TW_MILL)
            self.walk("teeth", t0 - 3.0 - dx / V_WALK - EASE, TW_MILL)
        hd, dr = cut_pose(TW_MILL, GEAR_CUT[0], GEAR_CUT[1], -1, band=11.0, v_at=V_TURN)   # (r6: out of the shared two_bone's
        # elbow swing band, which drew his forearm short, limb_stretch 0.83, while he sawed the gears)
        st = []
        for kind, (a, b) in cuts:                                  # saw strokes, back and forth along the blade
            n = 3
            st += [(a + (b - a) * q / n, a + (b - a) * (q + 1) / n) for q in range(n)]
        c1 = cuts[-1][1][1]
        gaps = [(cuts[j - 1][1][1], cuts[j][1][0]) for j in range(1, len(cuts))]   # r19: blade out between cuts
        teeth = [w for kind, w in cuts if kind == "tooth"]          # r21: the notches' windows (blade set in them)
        return dict(reach=(t0, t0 + 0.9), blade=(t0 - 0.45, t0 - 0.45 + BLADE_SLIDE), c0=cuts[0][1][0], c1=c1,
                    back=(c1 + 0.1, c1 + 0.9), sheath=(c1 + 0.1, c1 + 0.1 + BLADE_SLIDE),
                    hand=hd, dir=dr, strokes=st, sx=-1, tx=TW_MILL, kind="turn", gaps=gaps, teeth=teeth)

    def blank_turn(self, cuts, t):
        """The blank between cuts. Twigs' blade is at its right (screen angle 0, y down), so the part of the blank at
        the blade is the one at its own angle -ang. Hans turns it on (anticlockwise on screen, ang
        going down) so that corner k (at 45 + 90k) and then notch m (at 45m) come to the blade in turn: each corner
        is cut off and each notch deepens only while the blade goes through that very spot (owner, FK0021: the
        corner cut used to be the opposite one, and the teeth appeared where the blade wasn't). The blade is at the
        blank's right (screen angle 0), so the blank starts as a diamond (ang -45), a corner pointing at it."""
        ends = [b for _, (a, b) in cuts]
        starts = [a for _, (a, b) in cuts]
        ang = -45.0
        for j in range(1, len(cuts)):
            ang -= tooth_step(cuts, j) * ease(t, *self.turn_win(cuts, j))
        corners = float(sum(1 for kind, (a, b) in cuts if kind == "corner" and t >= b))
        cut = sum(notch_depth(t, a, b) for kind, (a, b) in cuts if kind == "tooth")
        return dict(ang=ang, corners=corners, cut=cut)

    def blade_part(self, cuts, t):
        """For the continuity check: the blank's own angle (deg) at the blade now, and which corner / notch the cut
        going on now removes (kind, index, its own angle), or None."""
        q = self.blank_turn(cuts, t)
        at = (-q["ang"]) % 360.0
        k_c = k_t = 0
        for kind, (a, b) in cuts:
            if a <= t < b:
                return at, (kind, k_c if kind == "corner" else k_t,
                            (45.0 + 90.0 * k_c) % 360.0 if kind == "corner" else notch_own(k_t))
            if kind == "corner":
                k_c += 1
            else:
                k_t += 1
        return at, None

    # ---------------------------------------------------------------- 6. hopper, belt, sack
    def _hopper_belt(self, t):
        self.say["hopper"] = t
        self.line("hopper", t)
        self.hopper_up = []
        for nm, (a, b) in (("hopper L", HW.HOPPER[0]), ("hopper R", HW.HOPPER[1])):
            t = self.trim_board(nm, t, a, b, slot=-2, side=HOPPER_SIDE)
            self.hopper_up.append(t)
        mc = self.mill_cam                                         # r31: one slow camera move, closer, from the
        del self.mill_cam                                          # pulley's slice to the hopper's second board

        def cam(t_, k):                                            # (each target reached by its time, eased in over
            v = mc[0][2 + k]                                       # its pan time; a held target has pan 0)
            for ta, d, *tg in mc[1:]:
                if d > 0:
                    v += (tg[k] - v) * ease(t_, ta - d, ta)
                elif t_ >= ta:
                    v = tg[k]
            return v
        self.zoom_on(mc[0][0], mc[-1][0] + 1.6, lambda t_: cam(t_, 0), lambda t_: cam(t_, 1), lambda t_: cam(t_, 2),
                     rin=0.0, rout=1.6)                            # (r31: rin 0: it carries on the mount's view)
        # the belt: r11 (part 2 must-fix: Hans' tentacle stretched up across his face to the wheel's hub, the coil held
        # over his eye) - Glo, who floats, takes the coil off the brake post, rises to the wheel's hub and loops it
        # on, then carries its end down, crossed over, to the mill's pulley
        t0 = t + 0.3
        self.walk("digger", t0, DIGS_WATCH)
        self.walk("tentacles", t0, MILL["tentacles"])
        bc = self.props["belt"]
        q0 = bc.end_pose()
        hand_dy = lambda y: y - (GB - CRUISE + GLO_HOLD + 10.0)     # noqa: E731  Glo's dip to hold a thing at y
        gx0 = self.glo_keys[-1][1]
        ta = self.glo_to(t0, q0["x"] + 4.0, v=140.0)
        tk = ta + 0.25
        tb = tk + 0.9                                              # he rises with it
        self.glo_dy.append((ta - 0.8, tb, hand_dy(q0["y"])))
        self.say["belt"] = tk - 0.3
        bc.follow(tk, tk + 0.3, lambda tt, tk=tk, q0=dict(q0): dict(x=lerp(q0["x"], self.glo_hand(tt)[0], ease(tt, tk, tk + 0.3)),
                                                        y=lerp(q0["y"], self.glo_hand(tt)[1], ease(tt, tk, tk + 0.3))),
                  holder=("Glo", 0))
        tr = tb + 1.8                                              # at the hub
        tc = tr + 1.4                                              # (looped on) and down with its end
        hub = hand_dy(HW.WY)
        self.glo_dy += [(tb - 0.8 + 0.6 * k, tc + 0.6 * k, hub / 4.0) for k in range(4)]
        self.glo_to(tb - 0.6, HW.WX + 4.0, v=120.0)
        bc.follow(tk + 0.3, tr + 0.2, lambda tt: dict(zip(("x", "y"), self.glo_hand(tt))), holder=("Glo", 0))
        bc.move(tr + 0.2, tr + 0.6, holder=("Glo", 0), x=HW.WX, y=HW.WY)
        (a0, a1), (b0, b1) = HW.tangents_crossed((HW.WX, HW.WY), HW.WHEEL_PULLEY_R, HW.STONES[0], HW.PULLEY_R + 2)
        self.belt_path = [(HW.WX + HW.WHEEL_PULLEY_R, HW.WY), a0, a1,
                          (HW.STONES[0][0] + HW.PULLEY_R, HW.STONES[0][1]), b1]
        # r36 (round 35 part 2 must-fix "Glo's dome and lantern sit right over the pulley as the belt goes on"): he
        # holds the belt a little way back from its end (BELT_LEAD along it), so he stays up-left of the stone while
        # its end goes round the pulley; and he's off up and away the moment it's on
        ux, uy = b1[0] - HW.WX, b1[1] - HW.WY
        ul = math.hypot(ux, uy)
        self.belt_u = (ux / ul, uy / ul)
        hx1, hy1 = b1[0] - BELT_LEAD * self.belt_u[0], b1[1] - BELT_LEAD * self.belt_u[1]
        self.glo_dy.append((tc - 0.8, tc + 4.6, hand_dy(hy1)))
        tx = self.glo_to(tc - 0.8, hx1 + 4.0, v=150.0)
        tf = max(tx, tc + 1.8) + 0.4
        self.belt_fit = (tr + 0.6, tf)
        self.belt_glo = True
        self.glo_to(tf + 0.2, gx0, v=150.0)
        self.glo_dy[-1] = (tc - 0.8, tf + 0.8, hand_dy(hy1))
        t = self.belt_fit[1] + 0.6
        tb = self.line("belt", self.say["belt"])
        # r29 (round 28 part 2 must-fix "the belt line plays in the extreme wide shot, the crossing can't be seen"):
        # a medium shot of the whole belt, wheel hub to the stone's pulley, while the line explains the crossing
        self.zoom_on(self.say["belt"] - 0.6, max(tf, tb) + 0.8, BELT_ZOOM, (HW.WX + HW.STONES[0][0]) / 2 - 5.0,
                     (HW.WY + HW.STONES[0][1]) / 2 + 2.0, rin=1.6, rout=1.6)
        t = self.walk("tentacles", t, MILL["tentacles"])
        # the sack: off the pile, opened, stood under the nip
        sk = self.props["sack"]
        t = max(t, tb - 1.0)
        self.say["sack"] = t
        # r8: he walks over to the pile and carries it across (his tentacle swept it 540 px standing still)
        q0 = sk.end_pose()
        ta = self.walk("tentacles", t, q0["x"] - 150.0)
        tw = self.walk("tentacles", ta + 0.6, HW.SACK_X + 150.0)
        self.sack_lift = ta + 0.6
        t1 = self.carry(sk, 1, ta + 0.6, (tw - ta - 0.6) / 0.85, lift=60.0, x=HW.SACK_X, y=HW.FLOOR - 2, folded=0.0)
        self.walk("tentacles", t1 + 0.9, MILL["tentacles"])
        self.line("sack", t)
        return max(t1, t + _dur(LINES["sack"])) + 0.5

    def belt_end(self, t):
        if getattr(self, "belt_glo", False) and hasattr(self, "paths"):
            hx, hy = self.glo_hand(min(t, self.belt_fit[1]))       # r11: its end in Glo's tendrils (r36: held
            k = BELT_LEAD * _seg(t, self.belt_fit[0], self.belt_fit[0] + 1.0)   # BELT_LEAD back from its end)
            return hx + k * self.belt_u[0], hy + k * self.belt_u[1]
        u = _seg(t, *self.belt_fit)
        pts = self.belt_path
        segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
        d = smoothstep(u) * sum(segs)
        for (a, b), L in zip(zip(pts, pts[1:]), segs):
            if d <= L:
                return lerp2(a, b, d / L)
            d -= L
        return pts[-1]

    def belt_state(self, t):
        """None (coiled), ('fitting', end) or ('on', run px)."""
        if t < self.belt_fit[0]:
            return None
        if t < self.belt_fit[1]:
            return ("fitting", self.belt_end(t))
        return ("on", self.wheel_ang(t) * -math.pi / 180.0 * HW.WHEEL_PULLEY_R)

    # ---------------------------------------------------------------- 7. the peg out, the first acorn
    def springs_over(self, t0, x1, v=110.0):
        """Springs hops to Digs, jumps right over him (a big spring jump; Digs stands still), and hops on to x1."""
        xd = self.walks["digger"][-1][1]
        x0 = self.walks["springs"][-1][1]
        s = 1 if x1 > x0 else -1
        gap = 300.0                                                  # far enough to be well over Digs as he passes
        xa, xb = xd - s * gap, xd + s * gap
        ta = self.walk("springs", t0, xa, v)
        tj = ta + 1.0                                                # settles, crouches, and springs
        dur = 2 * math.sqrt(2 * APEX / 1500.0)
        self.walks["springs"] += [(tj, xa), (tj + dur, xb)]
        self.springs_special.append((tj, tj + dur, "jump", (xa, xb)))
        self.digs_still = getattr(self, "digs_still", []) + [(ta - 1.0, tj + dur + 0.5, xd)]
        gx = self.glo_x(tj)                                          # r20 (part 2 must-fix "his hop goes straight
        if min(xa, xb) - 160.0 <= gx <= max(xa, xb) + 160.0:         # through Glo"): Glo floats up out of his way
            self.glo_dy.append((tj - 1.2, tj + dur + 0.9, -GLO_HOP_CLEAR))
        self.voice_events.append((tj + 0.2, "springs", "wee", None))
        return self.walk("springs", tj + dur + 0.45, x1, v)

    def _start(self, t):
        # Springs jumps over Digs to the brake post and pulls the peg; the rope slips off; the wheel turns the mill
        t = self.springs_over(t, SPRINGS_PEG_X)
        # r4: Glo was in front of the wheel as it began to turn: once Springs has landed he drifts left, clear of the
        # wheel's rim (and of the belt and the brake rope), until the wheel and the mill have been seen turning
        j_end = self.springs_special[-1][1]
        tg = self.glo_to(j_end + 0.3, GLO_PEG_X, v=110.0)
        self.pin = (max(t + 0.3, tg - 0.6), max(t + 0.3, tg - 0.6) + 1.1)   # (r4: a slower, readable pull)
        self.say["peg"] = self.pin[0] - 0.9
        tp = self.line("peg", self.say["peg"])
        self.zoom_on(self.pin[0] - 1.8, self.pin[1] + 2.0, 2.3, PEG[0] + 10.0, 790.0, rin=1.4, rout=1.5)   # r4: the
                                                                   # pull close, then out as the wheel turns
        self.wheel_go = self.pin[1] + 0.3
        self.say["turn"] = max(tp + 0.1, self.wheel_go + 0.2)
        self.line("turn", self.say["turn"])
        self.voice_events += [(self.wheel_go + 0.8, "wheels", "ooh", None), (self.wheel_go + 2.0, "teeth", "yay", None)]
        t = self.say["turn"] + _dur(LINES["turn"]) + 1.0
        # Glo floats over the hopper and lets the acorn go
        t_go = max(t - 5.0, self.glo_keys[-1][0])
        a = self.props["acorn"]                                    # r5: his acorn, out of the basket he left it in
        put, tp, dip = self.acorn_put
        bx = HW.BASKET_HOME[0] + 4.0
        t_b2 = self.glo_to(t_go, bx, v=90.0)
        self.glo_dy.append((t_b2 - 0.6, t_b2 + 1.4, dip))
        tk = t_b2 + 0.25
        a.follow(tk, tk + 0.3, lambda tt, tk=tk: dict(zip(("x", "y"), lerp2(put, self.glo_hand(tt),
                                                                             ease(tt, tk, tk + 0.3)))), holder=("Glo", 0))
        a.follow(tk + 0.3, 1e8, lambda tt: dict(zip(("x", "y"), self.glo_hand(tt))), holder=("Glo", 0))
        a.zf = [(tp + 0.15, 6.9), (tk + 0.15, 8.0)]
        self.acorn_basket = (tp, tk)
        t_go = t_b2 + 1.0
        t1 = self.glo_to(t_go + 0.8, HW.NIP_X + 4.0, v=150.0)
        t_up = t_go + 0.8 + (HW.WX + HW.WR + 40.0 - bx) / 150.0      # r4: he passes low under the wheel's
                                                                   # hub and rises once he is past its rim
        self.say["test"] = t1 - 1.2
        tl = self.line("test", self.say["test"])
        self.test_drop = max(t1 + 0.4, tl - 0.6)
        # (part 2 review: he crossed in front of the stones and sank in front of the hopper as the acorn ground)
        self.glo_dy.append((t_up, 1e9, GLO_OVER_HOPPER))           # up first (he crosses the stones high) ...
        q_drop = self.glo_hand(self.test_drop)                     # (where he is when he lets it go)
        # r16 (part 2 must-fix "a 12 s trip across the top of the sky"): he waits by the oak side of the mill (out
        # past the left post, under the belt) while Springs shakes the acorns down, not off right of it
        t_clear = self.glo_to(self.test_drop + 0.5, GLO_WAIT_X, v=150.0)
        self.glo_dy[-1] = (t_up, t_clear, GLO_OVER_HOPPER)         # ... and down only once he's clear of the post
        q = q_drop
        t0_, _, p0_, p1_, how_, lift_, holder_, fn_ = a.moves[-1]      # Glo holds it until he lets it go
        a.moves[-1] = (t0_, self.test_drop, p0_, dict(p1_, x=q[0], y=q[1]), how_, lift_, holder_, fn_)
        f_ = math.sqrt(2 * max(1.0, HW.HOPPER[0][1][1] - 14.0 - q[1]) / 1500.0)
        self.acorn_into(a, self.test_drop, q[0], q[1], t_nip=self.test_drop + f_ + 0.8, slow=2.6)
        self.flour_puff = a.gone
        self.zoom_on(min(self.test_drop - 2.6, self.pin[1] + 2.0), self.flour_puff + 3.2, 1.9, HW.NIP_X, 690.0, rin=2.2,
                     rout=2.0)   # r29 (round 28 part 2 must-fix): in on the stones as the peg shot ends, so the two
                                 # are seen close, turning inwards, from when the mill starts
        self.say["flour"] = self.flour_puff + 0.3
        self.line("flour", self.say["flour"])
        self.voice_events += [(self.flour_puff + 0.2, "lantern", "ooh", None), (self.flour_puff + 1.6, "digger",
                                                                                 "yay", None)]
        return self.say["flour"] + 2.0

    def acorn_into(self, a, t, x, y, t_nip=None, slow=1.0):
        """An acorn let go over the hopper: it falls in, rolls down to the nip and goes between the stones."""
        top = HW.HOPPER[0][1][1] - 14.0
        f = math.sqrt(2 * max(1.0, top - y) / 1500.0)
        a.move(t, t + f, how="fall", x=HW.NIP_X + max(-6.0, min(6.0, x - HW.NIP_X)), y=top)   # (r3: it landed on
        self.acorn_nip(a, t + f if t_nip is None else t_nip, slow)                  # the V's outside)

    def acorn_nip(self, a, t_nip, slow=1.0):
        """From the hopper's spout down between the turning stones (slow > 1: the first one, taken in slowly)."""
        a.move(t_nip, t_nip + 0.5 * slow, how="lin", x=HW.NIP_X, y=HW.STONES[0][1] - 20.0, crush=0.0)
        a.move(t_nip + 0.5 * slow, t_nip + 0.95 * slow, how="ease", x=HW.NIP_X, y=HW.STONES[0][1] - 2.0,
               crush=1.0)                                          # r16: squeezed flat between the stones
        a.gone = t_nip + 0.95 * slow
        a.why_gone = ("crushed between the millstones", (HW.NIP_X, HW.STONES[0][1]))
        self.acorn_flow.append((a.gone, a.name))

    def wheel_ang(self, t):
        """The water wheel's angle (deg; it turns anticlockwise, the water pushing its bottom paddles right)."""
        return -ramp_int(t, self.wheel_go, 2.5, 26.0)

    def stone_ang(self, i, t):
        """The left stone turns clockwise (the crossed belt), the right one anticlockwise (the gears): both move
        down at the nip."""
        a = -self.wheel_ang(t) * HW.WHEEL_PULLEY_R / HW.PULLEY_R
        return a if i == 0 else -a

    # ---------------------------------------------------------------- 8. milling: two basketfuls
    def _milling(self, t):
        """Springs hangs from the oak's low branch and bounces: the acorns drop into the basket on the grass. Glo
        takes it to the hopper and tips it; they go through the stones one at a time. Twice."""
        bk = self.props["basket"]
        self.loads = []
        self.say["shake"] = t
        t_s = self.line("shake", t)
        # r29 (round 28 part 2 must-fix "Springs bounces up by the oak, is back on the ground, then pops up onto the
        # branch in 0.2 s"): one bounce, right over Digs and up onto the branch, landing on it (no landing between)
        xd = self.walks["digger"][-1][1]
        if abs(xd - HW.BASKET_HOME[0]) < DIGS_BASKET_CLEAR:          # r35: Digs stood right in front of the basket
            xd = HW.BASKET_HOME[0] + DIGS_BASKET_CLEAR               # (it was hidden as they dropped in): he steps
            self.walk("digger", max(t - 1.5, self.walks["digger"][-1][0]), xd)   # aside to its right first
        xa = xd + 300.0
        ta = self.walk("springs", t, xa, 110.0)
        tj = ta + 1.0                                                # settles, crouches, and springs
        self.walks["springs"] += [(tj, xa), (tj + BRANCH_HOP_T, SHAKE_X)]
        self.digs_still = getattr(self, "digs_still", []) + [(ta - 1.0, tj + BRANCH_HOP_T + 0.5, xd)]
        gx = self.glo_x(tj)
        if min(xa, SHAKE_X) - 160.0 <= gx <= max(xa, SHAKE_X) + 160.0:
            self.glo_dy.append((tj - 1.2, tj + BRANCH_HOP_T + 0.9, -GLO_HOP_CLEAR))
        self.voice_events.append((tj + 0.2, "springs", "wee", None))
        self.cam_keys += [(t - 0.5, CAM_MILL), (t + 2.5, CAM_OAK)]
        # the basket waits on the grass under the branch tip; Springs shakes the acorns down into it (they land
        # softly in its lining of leaves); then Glo comes down for it and floats it over to the hopper
        shake = dict(t0=tj - 0.4, hop=(tj, tj + BRANCH_HOP_T), hop_x0=xa)
        shake["bounces"] = [(shake["hop"][1] + 0.2 + 0.9 * i, shake["hop"][1] + 1.1 + 0.9 * i) for i in range(3)]
        shake["let_go"] = shake["bounces"][-1][1] + 0.3
        shake["end"] = shake["let_go"] + 1.0
        self.springs_special.append((shake["t0"] - 0.5, shake["end"] + 0.5, "shake", shake))
        self.voice_events.append((shake["bounces"][0][0] + 0.2, "springs", "wee", None))
        rs = np.random.default_rng(90)
        acorns = []
        for j in range(12):
            b_ = shake["bounces"][j % 3]
            off = b_[0] + 0.3 + 0.07 * j + rs.uniform(0, 0.08)
            dx = (j % 5 - 2) * 11.0
            dy = -44.0 - (j // 5) * 9.0
            bx = HW.BASKET_HOME[0] + dx
            a = self.prop(f"acorn 0.{j}", "acorn", 8, 9.0, x=bx, y=0.0, ang=rs.uniform(-30, 30), on_branch=1.0,
                          s=ACORN_S)
            a.p0["y"] = self.branch_y(bx, -1e9) + 10.0
            land = self.in_basket(dx, dy, off)
            f = math.sqrt(2 * max(1.0, land["y"] - a.p0["y"]) / 1500.0) * ACORN_FALL   # (r35: slower, followable)
            tl = off + f
            a.move(off, off + 0.001, on_branch=0.0, y=a.p0["y"] + 0.5)  # it lets go of its twig
            a.move(off, tl, how="fall_soft", x=land["x"], y=land["y"])
            a.land_t = tl                                            # in front of Glo only until it's in the basket
            acorns.append([a, tl, dx, dy])
        land_end = max(o for _, o, _, _ in acorns)
        # r35 (round 34 part 2 must-fix "the falling acorns are tiny dots, a basket suddenly full"): closer, the
        # branch and the basket both in the shot, Springs whole (1.4 -> 1.9), and in before the first one drops
        self.zoom_on(max(shake["bounces"][0][0] - 1.8, shake["hop"][1] - 0.6), land_end + 1.6, ACORN_ZOOM[0],
                     ACORN_ZOOM[1], ACORN_ZOOM[2], rin=1.6, rout=1.6)   # (r29: in once he's landing on the branch)
        self.say["catch"] = max(t_s + 0.2, land_end - 2.0)
        self.line("catch", self.say["catch"])
        self.cam_keys += [(land_end + 0.6, CAM_OAK), (land_end + 4.0, CAM_MILL)]   # and back for the pour
        t_go = max(land_end - 1.0, self.glo_keys[-1][0])
        # r16: from where he waited (left of the mill) he floats low under the wheel to the basket, as he came
        tg = self.glo_to(t_go, BASKET_GLO_X, v=120.0)
        take = tg + 1.0
        self.basket_take = take
        self.glo_dy.append((tg - 0.6, take + 0.8, BASKET_DY))
        bk.follow(take, 1e8, lambda tt: self.basket_pose(tt, getattr(self, "tip_t", None)), holder=("Glo", 1))
        # r4: he rose only over the stones, carrying the basket in front of them: he goes to just outside the left
        # post, rises there, and comes in over the stones high
        t_out = self.glo_to(take + 0.6, HW.PL - 110.0)
        tg2 = self.glo_to(t_out + 0.6, HW.NIP_X + 40.0)
        tip = (tg2 + 0.5, tg2 + 1.5)
        self.tip_t = tip
        self.glo_dy.append((t_out - 0.4, tip[1] + 1.2, GLO_OVER_HOPPER - BASKET_HANG + 10.0))
        for j, (a, tl, dx, dy) in enumerate(acorns):
            tq = tip[0] + 0.45 + 0.07 * j
            a.follow(tl, tq, lambda tt, dx=dx, dy=dy: self.in_basket(dx, dy, tt), holder=("the basket", 0))
            q = HOPPER_SLOTS[j]
            a.move(tq, tq + 0.45, how="ease", x=q[0], y=q[1])
        tns = [tip[1] + 1.8 + 0.62 * j for j in range(len(acorns))]   # once Glo is clear of the stones
        for j, (a, tl, dx, dy) in enumerate(acorns):               # each sits in the pile, slipping down a place as
            tq = tip[0] + 0.45 + 0.07 * j                          # each one under it goes through
            a.follow(tq + 0.45, tns[j], lambda tt, j=j: hopper_slot(j - sum(ease(tt, tn, tn + 0.35) for tn in
                                                                             tns[:j])), holder=None)
            self.acorn_nip(a, tns[j])
        self.loads.append(dict(acorns=acorns, tip=tip, shake=shake))
        # owner, FK0021: "Glo shouldn't be standing right in front of the mill so that the viewer can't see what's
        # going on": once the basket is empty he floats off to the gap past Hans and sets it down on the grass, so the
        # acorns going through the stones are in clear view (and he isn't still holding it at the lanterns). (After
        # the acorns: while planning, Glo's place at a later time is his last planned spot.)
        tg3 = self.glo_to(tip[1] + 0.3, GLO_CLEAR_X, v=170.0)
        hi = self.glo_dy.index((t_out - 0.4, tip[1] + 1.2, GLO_OVER_HOPPER - BASKET_HANG + 10.0))
        self.glo_dy[hi] = (t_out - 0.4, tg3 + 0.6, GLO_OVER_HOPPER - BASKET_HANG + 10.0)   # r4: high till clear
        self.basket_down = (tg3 + 0.9, tg3 + 1.9)
        self.glo_dy.append((tg3, self.basket_down[1] + 0.8, BASKET_DY))         # down only once he's clear
        qb = self.basket_pose(self.basket_down[1], None)
        m_ = bk.moves[-1]
        bk.moves[-1] = (m_[0], self.basket_down[1], m_[2], dict(m_[3], **qb)) + m_[4:]
        self.voice_events.append((tip[1] + 0.3, "lantern", "hehe", None))
        self.say["pour"] = tip[0] - 0.4
        self.line("pour", self.say["pour"])
        t = tip[1] + 1.8 + 0.62 * 12 + 0.6
        t_say = t
        # Hans ties the sack (r13, "no string and no tying: the mouth closes by itself"): one tentacle gathers the
        # mouth into a neck, the other winds a red-brown cord round it three times and pulls a bow; he stands off to
        # its right so the sack isn't behind him
        self.say["tie"] = t
        t = self.walk("tentacles", t - 1.6, HW.SACK_X + 215.0)
        T0 = max(t + 0.6, max(tc for tc, _ in self.acorn_flow) + 1.6)   # (once the flour has stopped running)
        g1, w1 = T0 + 0.9, T0 + 2.7
        self.tie = (T0, w1 + 0.7)
        self.tie_wind = (g1, w1)
        neck = HW.FLOOR - 2 - 84 - 12.0
        def tied(tt):
            return 0.3 * ease(tt, T0, g1) + 0.45 * min(max((tt - g1) / (w1 - g1), 0.0), 1.0) + 0.25 * ease(tt, w1, self.tie[1])
        def winder(tt):
            if tt < g1:                                            # the drawstring's tail picked up, drawn round
                u = ease(tt, T0, g1)
                return HW.SACK_X + 32.0 - 2.0 * u, neck + 30.0 - 28.0 * u
            if tt < w1:
                u = (tt - g1) / (w1 - g1)
                ph = 2 * math.pi * 3 * u
                r = 30.0 - 10.0 * min(1.0, u * 4)                     # in from where he waited, then round and round
                return HW.SACK_X + r * math.cos(ph), neck + 2.0 + 6.0 * math.sin(ph)
            u = ease(tt, w1, self.tie[1])
            return HW.SACK_X + 20.0 + 18.0 * u, neck + 2.0 - 12.0 * u   # pulled out tight into the bow
        self.tie_cord = winder
        def behind(tt):                                            # his tentacle tips are behind the neck, except
            if g1 <= tt < w1:                                      # on the front half of each turn of the cord
                return math.sin(2 * math.pi * 3 * (tt - g1) / (w1 - g1)) < 0.35
            return True
        self.tie_behind = behind
        sk = self.props["sack"]
        sk.follow(self.tie[0], self.tie[1], lambda tt: dict(tied=tied(tt)), holder=("Hans", 2))
        self.hans_hold(2, T0, self.tie[1], lambda tt: (HW.SACK_X + 12.0 - 4.0 * ease(tt, T0, g1), neck))
        self.hans_hold(1, T0, self.tie[1], winder)
        self.zoom_on(tg2 - 3.0, max(t_say + 4.5, self.tie[1] + 3.2), 1.35, HW.NIP_X + 60.0, 650.0, rin=3.0, rout=3.0)
        t = t_say
        tt = self.line("tie", t)
        return max(tt, self.tie[1]) + 0.4

    def basket_pose(self, t, tip):
        """The basket in Glo's tendrils (under his dome), tipped towards the hopper while he pours."""
        x = self.glo_x(t)
        y = self.glo_y(t) + GLO_HOLD + glo_bob(t) + BASKET_HANG
        ang = 0.0
        if tip is not None and not isinstance(tip, tuple):
            tip = None
        if tip is not None:
            ang = -75.0 * ease(t, tip[0], tip[0] + 0.6) * (1 - ease(t, tip[1] + 0.3, tip[1] + 1.0))
        return dict(x=x - 8.0, y=y, ang=ang)

    def in_basket(self, dx, dy, t):
        b = self.props["basket"].at(t)[0]
        a = math.radians(b.get("ang", 0.0))
        px, py = b["x"], b["y"] - 26.0                              # it tips about its middle
        return dict(x=px + dx * math.cos(a) - (dy + 26.0) * math.sin(a),
                    y=py + dx * math.sin(a) + (dy + 26.0) * math.cos(a))

    def branch_y(self, x, t):
        """The oak's low branch's underside at x (it bends down with Springs on it)."""
        (x0, y0), (x1, y1) = HW.OAK_BRANCH[1], HW.OAK_BRANCH[2]
        u = min(max((x - x0) / (x1 - x0), 0.0), 1.0)
        return y0 + (y1 - y0) * u + self.branch_bend(t) * u ** 1.6 + 6.0

    def branch_bend(self, t):
        for t0, t1, kind, s in self.springs_special:
            if kind != "shake":
                continue
            if s["hop"][1] <= t < s["let_go"]:
                return 14.0 * ease(t, s["hop"][1] - 0.1, s["hop"][1] + 0.25) + \
                    10.0 * sum(math.sin(math.pi * _seg(t, a, b)) for a, b in s["bounces"])
            if s["let_go"] <= t < s["let_go"] + 0.8:
                u = t - s["let_go"]
                return 14.0 * math.exp(-4 * u) * math.cos(14 * u)
        return 0.0

    # ---------------------------------------------------------------- 9. home along the brook
    def _walk_home(self, t):
        """Everyone walks along the path to the village (the same order: nobody passes anybody); Hans carries the
        sack, Glo the basket. The camera follows at a walking pace; the sun goes down."""
        # r16 (part 2 must-fix "nobody goes anywhere"): they set off only once the camera has zoomed back out and
        # stands still (the zoom-out over the first steps made the walk read as the camera moving, not them)
        zend = max([k[1] for k in self.zoom_keys if k[0] < t + 0.4], default=0.0)
        t0 = max(t + 0.4, zend + 0.2)
        sk = self.props["sack"]
        t_pick = max(t0 - 1.2, self.tie[1] + 0.05)
        self.sack_pick = t_pick
        sk.follow(t_pick, 1e8, lambda tt: self.sack_carried(tt), holder=("Hans", 2))
        sk.zf = [(t_pick, 19.0)]                                   # r21 (part 2 must-fix: the sack slid behind the
        # oven's stone stand while the tentacle holding it was in front): in front of the stand, the sticks and the
        # stack's back log from when he lifts it (still behind him and his tentacles)
        self.hans_hold(2, t_pick, 1e8, lambda tt: self.sack_grip(tt), reach=0.0, back=0.0)
        # a few steps along the path, a soft dip into the evening, and the last few steps into the village (owner,
        # FK0019: no long stretches of watching them walk; the dip is between two acts, never inside one)
        self.say["home"] = t0 + 0.6
        tl = self.line("home", self.say["home"])
        # r10 (part 2 must-fix: 240 px at a stroll in a wide still shot, "nobody moves"): a proper set-off, the
        # camera holding still so they plainly walk away along the brook (the front ones out of shot) into the dip
        # r19 (part 2 must-fix "nobody moves" before the dissolve): they keep walking right into it (they stood
        # still the last 1.6 s)
        # r20 (part 2 must-fix "a 7 s walk in one wide shot"): 3.4 s of walking, then the dip (the line runs on
        # over the dissolve into the village, where they walk the last few steps)
        target = t0 + HOME_SHOT
        dist = HOME_V * (target - t0 - EASE)
        we = [self.walk(kd, t0, self.walks[kd][-1][1] + dist, v=HOME_V) for kd in WALKERS]
        self.glo_to(t0, self.glo_keys[-1][1] + dist, v=HOME_V)
        self.act_cut = max(target, max(we)) + 0.02                 # (the dissolve's darkest moment as they arrive)
        self.walk_t = (t0, self.act_cut + 4.5)
        ends = {}
        for kd in WALKERS:
            xv = VIL[kd] - 260.0
            self.walks[kd] += [(self.act_cut, self.walks[kd][-1][1]), (self.act_cut + 0.002, xv)]
            ends[kd] = self.walk(kd, self.act_cut + 0.6, VIL[kd])
        self.glo_keys += [(self.act_cut, self.glo_keys[-1][1]), (self.act_cut + 0.002, VIL["lantern"] - 260.0)]
        self.glo_to(self.act_cut + 0.6, VIL["lantern"])
        self.voice_events += [(self.act_cut + 2.0, "springs", "hey", None)]
        self.cam_keys += [(t0, CAM_MILL), (t0 + 0.6, CAM_MILL), (self.act_cut, CAM_MILL + HOME_PAN * dist),
                          (self.act_cut + 0.002, CAM_OVEN),
                          (self.act_cut + 1.0, CAM_OVEN)]          # act 2 opens on the oven's place (part 2 review)
        self.light_keys += [(t0 + 1.5, "gold"), (self.act_cut, "sunset"), (self.act_cut + 0.002, "sunset")]
        return ends["tentacles"] + 0.5

    def sack_carried(self, t):
        """The sack, in Hans' tentacle at his right side as he walks, until he sets it down by the oven."""
        if t >= self.sack_down[1]:
            return dict(x=SACK_V[0], y=SACK_V[1])
        x = self.paths["tentacles"](t) if hasattr(self, "paths") else VIL["tentacles"]
        side = 1.0 if t >= getattr(self, "act_cut", 1e9) else -1.0   # at his left along the brook; in the village
        # (r21) at his right, so he sets it down beside him, right of the sticks, never across his body
        hold = dict(x=x + side * 125.0, y=GB - 40.0 + 4.0 * math.sin(t * 3.0))
        if t < self.walk_t[0]:                                       # lifts it from under the nip
            u = ease(t, self.sack_pick, self.walk_t[0])
            return dict(x=lerp(HW.SACK_X, hold["x"], u), y=lerp(HW.FLOOR - 2, hold["y"], u) - 40 * math.sin(math.pi * u))
        if t >= self.sack_down[0]:
            u = ease(t, *self.sack_down)
            return dict(x=lerp(hold["x"], SACK_V[0], u), y=lerp(hold["y"], SACK_V[1], u) - 30 * math.sin(math.pi * u))
        return hold

    def sack_grip(self, t):
        q = self.props["sack"].at(t)[0]
        dy = -92.0
        sd = getattr(self, "sack_down2", None)
        if sd is not None and sd[0] < 1e8:                          # r37: held up in front of him at the dough, his
            a_ = sd[0] + SACK_OUT[1] - 0.4                          # tentacle round its shoulder, under the neck
            dy += SACK_SHOULDER * ease(t, a_, a_ + 0.6)            # (its curled tip stays under his mouth)
        return sack_pt(q, self.sack_fill(t), 0.0, dy)

    def sack_bow(self, t):
        """Where the second tentacle has the cord as he unties it (r14): the bow's tail pulled out, then the end
        taken round the neck three times the other way (the turns come off one by one), then laid down by the mouth
        (where its drawstring tail hangs). Matches tied = 1 - u in draw_sack."""
        q = self.props["sack"].at(t)[0]
        f = self.sack_fill(t)
        u = _seg(t, *self.untie)
        h = 40 + 44 * f
        nx, ny = q["x"], q["y"] - h - 14.0                         # the neck
        if u < 0.25:                                               # the bow's tail pulled: it comes undone
            w = ease(u, 0.0, 0.25)
            return nx + 8.0 + 30.0 * w, ny - 6.0 + 2.0 * w
        if u < 0.7:                                                # unwound: three turns off, round the neck
            v = (u - 0.25) / 0.45
            a = -2 * math.pi * 3 * v
            r = 24.0 + 6.0 * v
            return nx + 14.0 + r * math.cos(a), ny + 2.0 + 0.3 * r * math.sin(a)
        w = ease(u, 0.7, 1.0)                                      # the end laid down by the mouth
        return nx + 38.0 + 4.0 * w, ny - 4.0 + 26.0 * w

    # ---------------------------------------------------------------- 10. the oven
    def _oven(self, t):
        self.sack_down = (t, t + 1.4)
        P = self.prop
        self.hans[2][-1] = self.hans[2][-1][:1] + (self.sack_down[1] + 0.7,) + self.hans[2][-1][2:3] + \
            ((self.hans[2][-1][3][0], self.hans[2][-1][3][1], self.sack_down[1], self.sack_down[1] + 0.7),)
        t = self.sack_down[1] + 0.3
        # r15 (part 2 must-fixes): Digs digs his clay pit left of the oven's place, right over it, flinging the clay
        # onto a big heap just left of the oven's place; Springs leaps over him onto it, bounces it soft, leaps back
        self.say["clay"] = t
        tl = self.line("clay", t)
        d = LowDig(K, period=1.1, t_start=t + 0.4)
        dt = (t + 0.4, t + 0.4 + CLAY_STROKES * 1.1)
        bob = lambda tt: 2 * K * math.sin(tt * 2.6)                  # noqa: E731
        sp = FlungSpoil(d, CLAY_V, GB - 40.0, K, dt[1], (118 * K, -150 * K + 4 * K + 40.0), 95 * K, bob, heap_h0=34.0,
                        push=CLAY_PUSH, throw={-1: CLAY_THROW_L})
        self.holes["clay"] = dict(x=CLAY_V, dig=d, t=dt, spoil=sp, fill=None, post=None, clay=True, w=70.0)
        self.digs_jobs.append((dt[0] - 0.3, dt[1], "dig", "clay"))
        t = dt[1] + 0.4
        heap_x = sp.heap(1, dt[1])[0]
        self.clay_heap = heap_x
        g_x0 = self.glo_keys[-1][1]
        self.glo_to(t - 4.5, HW.OVEN_X + 90.0, v=90.0)               # (out of Springs' way)
        x_sp = self.walks["springs"][-1][1]
        dur = 2 * math.sqrt(2 * LEAP_APEX / 1500.0)
        tj = t + 0.6                                                # he crouches, and springs right over Digs
        self.walks["springs"] += [(tj, x_sp), (tj + dur, heap_x)]
        self.springs_special.append((tj, tj + dur, "leap", dict(x0=x_sp, x1=heap_x, on0=False, on1=True)))
        self.voice_events.append((tj + 0.2, "springs", "wee", None))
        bounces = [(tj + dur + 0.35 + 0.8 * i, tj + dur + 1.05 + 0.8 * i) for i in range(4)]
        self.springs_special.append((bounces[0][0], bounces[-1][1], "stomp", dict(x=heap_x, b=bounces, pre=0.35,
                                                                                     post=0.0, held=True)))
        self.soft = (bounces[0][0], bounces[-1][1])
        tk = bounces[-1][1]                                         # and back over him, off the top of the heap
        self.walks["springs"] += [(tk, heap_x), (tk + dur, SPRINGS_OVEN)]
        self.springs_special.append((tk, tk + dur, "leap", dict(x0=heap_x, x1=SPRINGS_OVEN, on0=True, on1=False)))
        self.voice_events.append((bounces[1][0], "springs", "hehe", None))
        self.zoom_on(self.say["clay"] - 0.5, tk + dur + 1.0, 1.7, (CLAY_V + heap_x) / 2 - 120.0, 790.0, rin=2.2, rout=1.6)
        clay_zk = len(self.zoom_keys) - 1
        self.glo_to(tk + dur + 0.5, g_x0, v=90.0)
        # r26 (part 3 must-fix "the bunny hops right over the open clay pit"): Digs shoves the clay he flung left
        # back into his pit and pats it down, in the same close shot, before he goes to watch the oven
        t_f = self.fill_clay(tk + dur + 0.6)
        self.walk("digger", t_f, DIGS_OVEN)
        zk = self.zoom_keys[clay_zk]                               # (the close shot held till he's done)
        self.zoom_keys[clay_zk] = zk[:1] + (max(zk[1], t_f + 1.0),) + zk[2:]
        # r15 (part 2 must-fixes "the balls come from nowhere", "Hans hides the oven"): Hans takes all six lumps off
        # the heap, three at a time, while the oven's place is still bare, and piles them on the slab
        self.coils = []
        self.lumps = []
        self.pile = []
        self.clay_cam_end = self.zoom_keys[clay_zk][1]             # r46: the camera pans on to the oven shot from here
        t = max(self.walks["tentacles"][-1][0], tk - 1.0)
        self._no_step = True                                       # (his places here are set by hand)
        for trip in range(RINGS // 3):
            t = self._lump_fetch(trip, t, heap_x)
        self._no_step = False
        # r38 (round 37 part 2 must-fix "a minute of fetch-and-stack, no narration, the balls' purpose untold"): a line
        # as the first one is rolled, and one as the last trip's are
        self.line("balls", min(e[1].roll_top[0] for e in self.pile[:3]) - 0.4)
        # r39 (round 38 part 2 must-fix "'Six balls of clay' while only three are on the slab"): said once the sixth
        # is set on the pile
        tl = max(tl, self.line("balls2", t - 0.2))
        self.voice_events += [(self.lumps[0] + 0.4, "digger", "mm", None), (self.lumps[3] + 0.4, "lantern", "mm", None)]
        # r46 (round 45 part 2: the camera went out to the wide shot and back in during the first roll): the close
        # clay shot hands on to the oven shot directly, the camera panning and easing in from one to the other
        zk = self.zoom_keys[clay_zk]
        t_h = self.clay_cam_end
        self.zoom_keys[clay_zk] = zk[:1] + (t_h,) + zk[2:6] + (0.0,)
        z0, fx0, fy0 = zk[2], zk[3], zk[4]
        def hand(a, b, t_h=t_h):
            return lambda tt: a + (b - a) * ease(tt, t_h, t_h + 3.0)
        self.zoom_on(t_h, None, hand(z0, 2.2), hand(fx0, HW.OVEN_X + 40.0), hand(fy0, 770.0),   # (the oven shot's framing)
                     rin=0.0, rout=2.2)   # (ends at the fire)
        t = self.walk("tentacles", t + 0.2, HANS_STONES)
        t = max(t, tl + 0.2)
        # Hans lays the oven's stones: three base stones, the hearth slab, two jambs and the lintel round the door
        self.say["hearth"] = t
        self.line("hearth", t)
        self._no_step = True                                       # r26: all in his reach from here (no shuffling)
        stones = []
        for i, (nm, kind, home, place) in enumerate(OVEN_STONES):
            p = P(nm, kind, 21 + 0.05 * i, 30.0, x=home[0], y=home[1], ang=90.0 if kind == "jamb" else 0.0)   # (r27: in front, see OVEN_STONES)
            stones.append(p)
            lift = min(14.0, (home[1] + place[1]) / 2 - STONE_LOW_Y)     # r26: low behind his legs (a dip for the
            t = self.carry(p, i % 2 - 1, t, 2.2, lift=lift, x=place[0], y=place[1], ang=0.0) + 0.1   # high ones), not past his face
        self._no_step = False
        # the clay coils: from the pile, one lump per ring, rolled out on the slab into a rope and laid round
        t = self.walk("tentacles", t, HANS_COIL)
        for i, p in enumerate(stones):                             # r27: back on the oven's layer, him clear of it
            p.zf = list(getattr(p, "zf", [])) + [(t, 9 + 0.05 * i)]
        self.say["coils"] = t
        self.line("coils", t)
        self._no_step = True                                       # (his places here are set by hand)
        for n, k in enumerate(LAY_ORDER):
            t = self._lay_lump(n, k, t if n == 0 else self.coils[-1][1] + 1.3)
        t = max(t, max(j[1] for jobs in self.hans.values() for j in jobs) + 0.6)   # r17 (part 3 must-fix: a 3rd arm while
        # the last lump's tentacle was still drawing back): his other tentacles are home first
        # r30 (round 29 part 2 must-fix "smoothed where no tentacle touches"): a step nearer, so both tips reach the
        # whole width; the clay is smooth only where a tip has stroked it (`smooth_swept`)
        self.line("smooth", t)
        self.say["smooth"] = t
        # (two passes: the right half from where he stands, then a step left for the left half; by then his body
        # covers only the half that's already smooth)
        # r38 (round 38 part 3 must-fix "two tentacles stretch to twice his leg length over the dome"): a step nearer
        # for each half, so every stroke is within his usual reach (HANS_REACH)
        t = self.walk("tentacles", t, HANS_SMOOTH_R)
        a0 = t + 0.2
        a1 = a0 + SMOOTH_S
        b0 = self.walk("tentacles", a1 + 0.3, HANS_SMOOTH) + 0.2
        self.smooth_wins = [(a0, a1, 0.40, 0.97), (b0, b0 + SMOOTH_S, 0.03, 0.40)]   # (r42: 0.46 -> 0.40, reach from 3355; r38: 0.42/0.58, reach)
        self.smooth = (a0, b0 + SMOOTH_S)
        # r12 (part 2 must-fix: the whole stack turned into a smooth dome at once): band by band from the foot up,
        # his two tentacles stroking side to side just at the line being smoothed
        for s, ph in ((-1, 0.0), (1, math.pi)):
            for w0, w1, _, _ in self.smooth_wins:
                self.hans_hold(s, w0, w1, lambda tt, ph=ph: self.smooth_tip(tt, ph))
        t = self.smooth[1] + 0.5
        self._no_step = False
        # the fire: Hans puts three dry sticks inside; Glo's light sets them glowing
        t_fire0 = t
        # r33 (round 32 part 3 must-fix "he shoots a tentacle twice his legs' length out to the stick pile and back,
        # never stepping over"): the pile and the door are too far apart for one stand, so for each stick he steps
        # over to the pile, picks it up, steps back to the door with it held beside him and puts it in
        for i in range(3):
            # r43 (round 43 part 3 must-fix "the sticks come from nowhere"): the three lay flat and stacked against
            # the lantern post's foot and read as part of it; now a crossed little pile on the path in front of it
            p = P(f"stick {i}", "stick", 9.5, 14.0, x=STICKS[0] - 28.0 + 12.0 * i, y=HW.FLOOR + 8.0 - 3.0 * i,
                  ang=(-22.0, 14.0, -6.0)[i])
            p.why_born = "lies on the stick pile from the start"
            t = self.walk("tentacles", t, STICK_PILE_STAND)
            hx, hy = STICK_PILE_STAND + STICK_HOLD[0], STICK_HOLD[1]
            t1 = self.carry(p, 0, t, 1.3, lift=30.0, x=hx, y=hy, ang=-10.0, back=0.0)
            tw = self.walk("tentacles", t1 + 0.1, STICK_DOOR_STAND)
            p.follow(t1, tw, lambda tt, hx=hx: dict(x=hx + self.hans_x(tt) - STICK_PILE_STAND, y=hy),
                     holder=("Hans", 0))
            self.hans_hold(0, t1, tw, lambda tt, p=p: self.grip_pt(p, tt, (0.0, 0.0)), reach=0.0, back=0.0)
            t = self.carry(p, 0, tw, 1.8, lift=20.0, x=OVEN_MOUTH[0] - 14.0 + 14.0 * i, y=OVEN_MOUTH[1] - 6.0,
                           ang=-20.0 + 20.0 * i, reach=0.0) + 0.1
        tg = self.glo_to(t - 1.5, HW.OVEN_X + GLO_FIRE_DX)
        # r26 (part 2 must-fix "Glo sits on top of the dome and his light goes through the clay"): he floats down
        # in front of the door, his lamp level with the opening, and his light goes in through it to the sticks;
        # then he rises again
        t_dn = max(t + 0.4, tg)
        self.glo_dy.append((t_dn, t_dn + 4.6, GLO_FIRE_LAMP_Y + 128.0 - (GB - CRUISE)))
        self.fire_t = (t_dn + 1.8, t_dn + 3.2)
        # r36 (round 35 part 3 must-fix "the narration says Glo's light sets them glowing ~18 s before the fire"):
        # the line is timed so "...sets them glowing" ends just as the sticks catch
        tf = self.line("fire", max(t_fire0, self.fire_t[0] + 1.0 - _dur(LINES["fire"])))
        self.flares.append((self.fire_t[0] - 0.8, self.fire_t[0] + 0.6, lambda tt: OVEN_MOUTH))
        zk = self.zoom_keys[-1] if self.zoom_keys[-1][1] is None else [k for k in self.zoom_keys if k[1] is None][0]
        self.zoom_keys[self.zoom_keys.index(zk)] = (zk[0], self.fire_t[1] + 1.5) + tuple(zk[2:])
        self.voice_events += [(self.fire_t[1] + 0.3, "lantern", "ooh", None), (self.fire_t[1] + 1.4, "digger", "yay",
                                                                                 None)]
        self.light_keys += [(self.fire_t[0], "sunset"), (self.fire_t[0] + 30.0, "dusk")]
        return max(self.fire_t[1], tf) + 0.8

    def _lump_fetch(self, trip, t, heap_x):
        """r15: Hans takes three lumps off the soft heap (standing on the oven's bare place, right of it), carries them
        low in front of him over to the slab and piles them on its right end -> end time."""
        t = self.walk("tentacles", t, HANS_LUMPS, v=120.0)
        lumps, held = [], []
        for i, sl in enumerate(LUMP_SLOTS):                        # one, two, three off the heap, held low
            tp = t + 0.2 + 0.9 * i
            ln = len(self.lumps)
            top = clay_top(self, tp)
            bx, by = heap_x - 30.0 + 30.0 * i, top + 0.6 * lump_r(ln)
            lump = self.prop(f"clay lump {ln}", "lump", 9.9, 16.0, born=tp, x=bx, y=by, s=LUMP_SK[ln])
            lump.why_born = ("taken off the soft clay heap by Hans", (bx, by))
            self.lumps.append(tp)
            dx, hy = LUMP_HOLD[sl]
            held.append(self.carry(lump, sl, tp, 1.2, lift=30.0, x=HANS_LUMPS + dx, y=hy, back=0.0))
            lumps.append(lump)
        t = self.walk("tentacles", held[-1] + 0.2, HANS_COIL)
        t_set = t
        tn = t + 0.2
        if trip == 0:                                              # r46: the first one is rolled once the camera has
            tn = max(tn, self.clay_cam_end + 1.6)                  # panned on to him (it pans over 3 s)
        for i in (0, 1, 2):                                        # r47: the one at his right first (was 1, 2, 0)
            lump, sl = lumps[i], LUMP_SLOTS[i]
            dx, hy = LUMP_HOLD[sl]
            # r29 (round 28 part 2 must-fix "the lumps turn into round balls by themselves while he just holds them"):
            # carried rough; then, held up in front of him, his free tentacle rolls it to and fro on top (it turns
            # with each stroke and rounds only as it is rolled), then it goes on the pile
            hold = lambda tt, dx=dx, hy=hy: dict(x=self.hans_x(tt) + dx, y=hy)   # noqa: E731
            lump.follow(held[i], tn, hold, holder=("Hans", sl))
            self.hans_hold(sl, held[i], tn, lambda tt, h=hold: (h(tt)["x"], h(tt)["y"]), reach=0.0, back=0.0)
            # r34 (round 33 part 2 must-fix "the lumps turn into round balls with no visible rolling": rolled in front
            # of his orange body it didn't read): handed to his right tentacle and held out at his right side, the
            # grass behind it, it is rolled to and fro under the tip of his other right tentacle (it rolls along
            # under the tip, turning as it goes) and rounds only as it is rolled; then that tentacle sets it on the pile
            hx = self.hans_x(tn)
            hp = (hx + LUMP_PASS[0], LUMP_PASS[1])
            tp_ = self.carry(lump, sl, tn, 0.8, x=hp[0], y=hp[1], reach=0.0, back=0.3)
            rp = (hx + LUMP_ROLL_AT[0], LUMP_ROLL_AT[1])
            r0 = self.carry(lump, 1, tp_, 0.9, x=rp[0], y=rp[1], reach=0.45, back=0.0)   # (the giver home before the
            # roller reaches in: four working tentacles at most, his other four legs)
            r1 = r0 + LUMP_ROLL_T
            lump.roundw, lump.roll_top = (r0 + 0.2, r1 - 0.1), (r0, r1)
            lump.zf = [(tn, 10.5)]                                 # (r30: in front of the lumps he still holds)
            lump.follow(r0, r1, lambda tt, rp=rp, r0=r0, r1=r1: dict(x=rp[0] + 0.5 * lump_roll_d(tt, r0, r1), y=rp[1]),
                        holder=("Hans", 1))
            k = 3 * trip + i
            lr_ = lump_r(k)                                        # r44: its own size
            self.hans_hold(1, r0, r1, lambda tt, rp=rp, r0=r0, r1=r1, lr_=lr_: (rp[0] + 0.5 * lump_roll_d(tt, r0, r1),
                                                                     rp[1] + 0.85 * lr_), reach=0.0, back=0.0)
            self.hans_hold(2, r0, r1, lambda tt, rp=rp, r0=r0, r1=r1, lr_=lr_: (
                rp[0] + lump_roll_d(tt, r0, r1), rp[1] - 0.9 * lr_), reach=0.4, back=0.6)   # (the other tip on its top)
            t_end = self.carry(lump, 1, r1 + 0.1, 1.3, lift=12.0, x=LUMP_PILE6[k][0], y=LUMP_PILE6[k][1],
                               reach=0.0, back=0.4)
            lump.zf.append((r1 + 0.1 + 1.3 * 0.85, 21.0 + 0.1 * k))  # on the slab, in front of him
            self.pile.append((k, lump, tn, sl))
            t_set = max(t_set, t_end)
            tn = t_end + 0.25                                      # (r34: his right tentacle free for the next)
        return t_set + 0.3

    def _lay_lump(self, n, k, t_take):
        """r15: Hans takes lump k off the pile on the slab, rolls it out into a rope on the slab's open left end and
        lays ring n of the dome from it -> end time."""
        _, lump, _, sl = [e for e in self.pile if e[0] == k][0]
        i = n                                                      # the ring it makes
        c0 = self.coil_end(i, 0.0)
        c1_ = self.coil_end(i, 1.0)
        Lr = math.hypot(c1_[0] - c0[0], c1_[1] - c0[1]) / 0.96     # r19: the rope as long as its course
        rx = max(ROLL_X, SLAB[0] - SLAB[2] + Lr / 2 + 6.0)         # (and all on the slab)
        so = 1 if sl == 0 else 0                                   # his other tentacle: the rope's right end
        pile = LUMP_PILE6[k]
        hold = lambda tt, pile=pile: dict(x=pile[0], y=pile[1])                 # noqa: E731
        self.hans_hold(sl, t_take - 0.7, t_take, lambda tt, pile=pile: pile, reach=0.7, back=0.0)   # his tip to it
        roll = (t_take, t_take + 0.8 + ROLL_S)
        lump.zf.append((roll[1] + 0.45, 9.9))                      # (on the slab: in front of it till lifted clear)

        lr_ = lump_r(k)                                            # r44: its own size

        def roll_q(tt, h=hold, roll=roll, rx=rx, Lr=Lr, lr_=lr_):                # r13: over onto the slab, then rolled out on it
            a_ = ease(tt, roll[0], roll[0] + 0.8)
            p_ = h(tt)
            rl = ease(tt, roll[0] + 0.8, roll[1])
            rr = lr_ + (ROPE_R - lr_) * rl
            u = _seg(tt, roll[0] + 0.8, roll[1])
            d = 18.0 * math.sin(2 * math.pi * 3 * u)               # pushed away and drawn back, three times (r38: 12 -> 18)
            x1, y1 = rx + DV[0] * d, SLAB_TOP - rr + DV[1] * d * 0.5
            return dict(x=p_["x"] + (x1 - p_["x"]) * a_, y=p_["y"] + (y1 - p_["y"]) * a_, roll=rl, ang=-180.0,
                        c=0.5, rem=1.0, spin=d / (2 * math.pi * rr), flat=1.0, len=Lr)
        lump.follow(roll[0], roll[0] + 0.8, roll_q, holder=("Hans", sl))       # (a ball, onto the slab)
        lump.follow(roll[0] + 0.8, roll[1], roll_q, holder=("Hans", so))       # r19: held by the end he lifts it by
        self.hans_hold(sl, roll[0], roll[1], lambda tt, lump=lump: rope_top(lump.at(tt)[0], ROLL_F),
                       reach=0.0, back=0.0)
        self.hans_hold(so, roll[0] + 0.8, roll[1], lambda tt, lump=lump: rope_top(lump.at(tt)[0], 0.15),
                       reach=0.5, back=0.0)
        self.hans[sl][-1] = self.hans[sl][-1][:1] + (roll[1] + 0.6,) + self.hans[sl][-1][2:3] +             ((self.hans[sl][-1][3][0], self.hans[sl][-1][3][1], roll[1], roll[1] + 0.6),)   # r19: lets go of it
        # over to the dome's foot, its left end on the course (r14: off the slab it droops, soft clay). r40 (round 39
        # part 2 must-fix "carries each coil straight across the doorway, in front of the posts and the lintel"): up
        # the oven's right side first, then across above the door's stones (or along its own course, higher up), and
        # only then down onto its start, left of the door
        rope = dict(c=1.0, ang=rope_ang(i, 0.0), roll=1.0, rem=1.0, flat=0.0, len=Lr)
        across = dict(rope, ang=max(rope["ang"], -205.0), flat=0.0)   # (r43: 25 degrees, was 45: held no higher than that,
        ya = min(c0[1], LINTEL_TOP - 20.0)                         # his tip clear of Glo; steeper as it goes down)
        tA = roll[1] + 0.8
        # r43 (round 43 part 2 must-fix "each coil lifted high over his head on a stretched tentacle, stiff as a
        # stick"): it hangs straight down from his tip beside the oven, its low end just off the ground (was: stood
        # upright with its low end at the lintel, its top far over his head), then swings up onto its course
        lump.move(roll[1], tA, holder=("Hans", so), x=HW.OVEN_X + COIL_HANG_DX, y=HW.FLOOR - 45.0,
                  **dict(rope, ang=-268.0, flat=1.0))
        # (lifted upright beside the oven: the rope hangs from his tip, not across his face; it tilts as it goes over)
        t1 = tA + 1.1
        lump.move(tA, t1, lift=8.0, holder=("Hans", so), x=c0[0], y=ya, **across)
        if c0[1] > ya + 1.0:
            lump.move(t1, t1 + 0.7, holder=("Hans", so), x=c0[0], y=c0[1], **rope)
            t1 += 0.7
        gf = lambda tt, a=roll[1], b=t1: 0.15 - 0.15 * ease(tt, a, b)           # noqa: E731
        self.hans_hold(so, roll[1], t1, lambda tt, lump=lump, gf=gf: rope_at(lump.at(tt)[0], gf(tt)),
                       reach=0.0, back=0.0)
        lay = (t1, t1 + LAY_S)
        self.coils.append(lay)
        lump.behind_door = (t1 - 0.3, t1 + LAY_S + 0.5)            # r37: laid behind the door's stones

        def lay_q(tt, i=i, lay=lay, Lr=Lr):
            u = _seg(tt, *lay)
            x_, y_ = self.coil_end(i, u)
            return dict(x=x_, y=y_, rem=1.0 - u, ang=rope_ang(i, u), c=1.0, roll=1.0, flat=0.0, len=Lr)
        lump.follow(lay[0], lay[1], lay_q, holder=("Hans", so))
        lump.gone = lay[1]
        lump.why_gone = ("laid round the oven as a coil", self.coil_end(i, 1.0))
        self.hans_hold(so, lay[0], lay[1], lambda tt, lump=lump: rope_at(lump.at(tt)[0], 0.0), reach=0.0)   # its end
        return lay[1] + 0.2

    def coil_end(self, i, u):
        """The rope's end as lump i is laid (u 0..1): its first ring left to right, then its second, on top of it,
        back right to left."""
        k, ux = ring_of(i, u)
        lv = (k + 0.5) / RINGS
        x, y = self.dome_pt(ux, lv)
        if door_ring(k):                                           # r40 (round 39 part 2 must-fix "each coil laid
            # straight across the doorway"): a ring at the door's height can't cross the opening; behind the jambs it
            # goes round the back, so between them it's laid along the back wall, seen through the door
            w = smoothstep(min(1.0, max(0.0, (JAMB_DX + 6.0 - abs(x - HW.OVEN_X)) / 12.0)))
            y += (self.dome_pt(ux, lv, True)[1] - y) * w
        return x, y

    def smooth_tip(self, tt, ph):
        """r30: where a smoothing tentacle tip is: side to side across the whole dome, just at the rising front.
        r33 (round 32 part 3 must-fix "the tips curl in the air; the coil lines fade where nothing touches"): the
        point his tentacle is drawn to, so that its wrapped tip (which lies left of and below that point, the rig's
        curl) presses on the clay at smooth_press."""
        x, y = self.smooth_press(tt, ph)
        return x + SMOOTH_CURL[0], y + SMOOTH_CURL[1]

    def smooth_press(self, tt, ph):
        """r33: where a smoothing tentacle's wrapped tip presses the clay (the middle of its curl): side to side
        across this pass's half, just at the rising front, kept SMOOTH_IN inside the dome's outline so the whole curl
        lies on the clay; beside the door only up and down the clay at its side (never stroking the open hole)."""
        w = self.smooth_wins[0] if tt < self.smooth_wins[1][0] - 0.1 else self.smooth_wins[1]
        w0, w1, u0, u1 = w
        lv = min(SMOOTH_LV1, SMOOTH_LV0 + (1.0 - SMOOTH_LV0) * _seg(tt, w0, w1) + 0.03 * math.cos(3.1 * tt + ph))
        X, base = HW.OVEN_X, OVEN_BASE_Y
        half = (HW.OVEN_W / 2 - SMOOTH_IN) * math.sqrt(max(0.0, 1 - lv * lv))
        y = base - (HW.OVEN_H - SMOOTH_IN) * lv
        xl, xr = X - half + 2 * half * u0, X - half + 2 * half * u1
        k = smoothstep(min(1.0, max(0.0, (y - (DOOR_TOP - 30.0)) / 30.0)))   # 1 beside the door, 0 well above it
        jamb = X + (1 if u1 > 0.9 else -1) * (DOOR_HW + 14.0)       # up the clay beside it (its curl, 50 px across,
        # is wider than that strip: it takes in the door's stone at its side rather than hang out past the dome)
        xl, xr = xl + (jamb - 4.0 - xl) * k, xr + (jamb + 4.0 - xr) * k
        x = xl + (xr - xl) * (0.5 + 0.5 * math.sin(SMOOTH_W * (tt - w0) + ph - math.pi / 2))
        hf = HW.OVEN_W / 2 * math.sqrt(max(0.0, 1 - lv * lv))     # r38: on the ring's bowed front (dome_pt)
        return x, self.dome_pt((x - X + hf) / (2 * hf) if hf > 1 else 0.5, lv)[1] + (y - (base - HW.OVEN_H * lv))

    def smooth_swept(self, t, sh, extra=0.0):
        """r30: the part of the dome the two tips have stroked smooth by t (screen px), or None for all of it.
        extra (r32): that much wider (the soft fringe at its edge)."""
        if t >= self.smooth[1]:
            return None
        out = skia.Path()
        for w0, w1, _, _ in self.smooth_wins:
            n = int((min(t, w1) - w0) / 0.04) + 1
            if n < 2:
                continue
            for ph in (0.0, math.pi):
                pl = skia.Path()
                for j in range(n + 1):
                    x, y = self.smooth_press(min(t, w1, w0 + 0.04 * j), ph)   # (r33: where the curl presses)
                    (pl.moveTo if j == 0 else pl.lineTo)(x - sh, y)
                st = skia.Path()
                skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=SMOOTH_STROKE + extra, StrokeCap=skia.Paint.kRound_Cap,
                           StrokeJoin=skia.Paint.kRound_Join).getFillPath(pl, st)
                out = skia.Op(out, st, skia.PathOp.kUnion_PathOp)
        return out

    def smooth_front(self, t):
        """How far up (lv 0..1) the dome has been smoothed."""
        return _seg(t, *self.smooth) if hasattr(self, "smooth") else 0.0

    def smooth_pt(self, i, u):
        """Where his second tentacle presses the new coil down, just behind its end: on the near (right) part of
        the dome only, within his reach (round 4: no tentacle stretched across the oven)."""
        k, ux = ring_of(i, u)
        return self.dome_pt(max(ux, 0.4), (k + 0.5) / RINGS)

    def dome_pt(self, ux, lv, back=False):
        """A point on the oven's dome: ux 0 left .. 1 right across it, lv 0 its foot .. 1 its top. r38 (round 37 part 2
        must-fix "each coil is a straight bar across the door; nothing goes round"): seen a little from above, each
        ring's front bows down in the middle (its sides higher, the door's middle where it was), and its back (seen
        through the door, `back`) bows up, so the coils read as rings round the oven, the back ones further in."""
        base = OVEN_BASE_Y
        h = HW.OVEN_H * lv
        s_ = math.sqrt(max(0.0, 1 - lv * lv))
        half = HW.OVEN_W / 2 * s_
        sn = math.sin(math.pi * min(max(ux, 0.0), 1.0))
        g_ = min(1.0, lv * RINGS)                                  # (its foot flat on the hearth slab)
        bow = -DOME_BOW * s_ * g_ * ((1.0 + sn) if back else (1.0 - sn))
        return HW.OVEN_X - half + 2 * half * ux, base - h + bow

    # ---------------------------------------------------------------- 11. the table
    def _table(self, t):
        self.say["table"] = t
        self.cam_keys += [(t - 0.5, CAM_OVEN), (t + 5.0, CAM_V)]      # a slow pan over to the table
        # r33 (round 32 part 3 must-fix: Glo waited by the oven till the bread and then floated 1,200 px across one
        # still shot to the peel): he comes over with the others as the camera pans, and waits above the table's end
        self.glo_to(t - 0.3, GLO_TABLE_X, v=170.0)
        tl = self.line("table", t)
        sk = self.props["sack"]
        t0_, _, p0_, p1_, how_, lift_, holder_, fn_ = sk.moves[-1]
        sk.moves[-1] = (t0_, t, p0_, dict(p1_, x=SACK_V[0], y=SACK_V[1]), how_, lift_, None, fn_)
        ts = self.walk("tentacles", t, SACK_V[0] + 130.0, v=130.0)   # r8: he walks up to the sack first (his
        # tentacle stretched 270 px to it); it is lifted where it lies, then carried along beside him
        sk.move(ts, ts + 1.2, holder=("Hans", 2), lift=30.0, x=SACK_V[0], y=GB - 40.0)
        th = self.walk("tentacles", ts + 1.2, HANS_TABLE, v=130.0)
        # r27 (part 3 should-fix "9 s on Glo hovering over the oven, Hans cut off"): the oven's close shot ends as the
        # line starts, the wide shot pans along with Hans to the table, and the rack's close shot is in before he's there
        k_ = self.zoom_keys[-1]
        if k_[1] > t - 3.5:
            self.zoom_keys[-1] = (k_[0], max(t + 1.0, self.fire_t[1] + 4.0), k_[2],
                                  k_[3] if callable(k_[3]) else HW.OVEN_X + 40.0,   # (r46: the hand-on pan keeps its
                                  k_[4] if callable(k_[4]) else 770.0, k_[5], 2.0)   # own path to this framing)
        self.planks_zoom0 = th - 1.6
        sk.follow(ts + 1.2, th, lambda tt: dict(x=self.hans_x(tt) - 130.0, y=GB - 40.0), holder=("Hans", 2))
        sk.move(th, th + 1.0, holder=("Hans", 2), x=SACK_T[0], y=SACK_T[1])
        self.hans_hold(2, ts, th + 1.0, lambda tt: self.sack_grip(tt))
        th += 1.0
        t = max(th, tl) + 0.2
        # the stack of planks already lies on the rack; Twigs trims them all at once at the notch
        self.say["planks"] = t
        pl = [self.props[f"plank {j}"] for j in range(6)]
        t1 = t + 1.2
        c1, tb = self.cut(t1 - 0.3, TW_TABLE, FR_NOTCH, TRIM_Y, strokes=6)   # from above the stack, in view (r2:
                                                                   # his hand was inside it)
        self.trim_cut = (self.twigs_cuts[-1]["c0"], c1)              # the kerf opens through the stack as he saws
        self.twigs_cuts[-1]["kind"] = "trim"                          # r13: the blade sinks through the stack
        d_ = self.twigs_cuts[-1]["dir"]
        self.trim_line = (d_[0] / d_[1], TRIM_Y)                     # r12: the kerf runs along his blade
        self.zoom_on(self.planks_zoom0, c1 + 2.4, 1.8, FR_NOTCH - 20.0, 800.0, rin=2.0, rout=2.0)   # r13: closer
        for j, p in enumerate(pl):
            p.move(c1, c1 + 0.01, L=200.0, off=-TRIM_OFF / 2)
        oc = self.prop("plank offcuts", "plank_offcut", 21, 9.0, born=c1, x=FR_NOTCH + TRIM_OFF / 2, y=HW.RACK_Y - 36.0,
                       ang=0.0)
        oc.why_born = "sawn off by Twigs' blade"
        oc.move(c1, c1 + 0.5, how="ease", x=FR_NOTCH + TRIM_OFF / 2 + 14.0, y=990.0, ang=20.0)
        self.line("planks", t)
        t = c1 + 0.6
        # one by one off the top of the stack, turned across, and laid on the two logs (from the left end)
        self.planks = []
        self.stack_up = t                                           # (the stack lifted off the rack)
        pl = [self.props[f"plank {j}"] for j in range(6)]
        held = lambda tt, j: dict(x=self.hans_x(tt) + STACK_DX, y=STACK_Y - PLANK_DY * j, yaw=0.0)   # noqa: E731
        hx0 = self.walks["tentacles"][-1][1]
        t1 = t + 1.6 * 0.85
        for j, p in enumerate(pl):                                  # up off the rack, in front of him
            p.move(t, t1, lift=30.0, holder=("Hans", -1), x=hx0 + STACK_DX, y=STACK_Y - PLANK_DY * j, yaw=0.0)
        tw = self.walk("tentacles", t1, PLANK_HX[0])
        for j, p in enumerate(pl):
            p.follow(t1, tw, lambda tt, j=j: held(tt, j), holder=("Hans", -1))
        t = tw + 0.2
        for k in range(6):                                          # the top one first (the last one cut)
            j = 5 - k
            p = pl[j]
            slot_x = HW.TABLE[0] + (k + 0.5) * HW.PLANK_W
            if abs(PLANK_HX[k] - self.walks["tentacles"][-1][1]) > 5:   # a step along the table, the stack with him
                ts = t
                t = self.walk("tentacles", t, PLANK_HX[k], v=80.0)
                for jj in range(j + 1):
                    pl[jj].follow(ts, t, lambda tt, jj=jj: held(tt, jj), holder=("Hans", -1))
            t_last = t                                              # (r8: the stack's holds let go as the last one goes)
            if k == 4:                                              # r42 (round 41 part 3: the peel lay on the back
                peel = self.props["peel"]                           # log and stayed on top of the planks laid under
                ta = t - 1.5                                        # it): his free tentacle lifts it off first...
                pk = dict(x=PEEL_HOME[0] - PEEL_ASIDE, y=PEEL_HOME[1] - PEEL_LIFT, hx=PEEL_HOME[0] - PEEL_ASIDE + 150.0,
                          hy=PEEL_HOME[1] - PEEL_LIFT)
                t_up = self.carry(peel, 2, ta, 1.4, grip=(PEEL_GRIP, 0.0), lift=0.0, **pk)
            t2 = self.carry(p, 0, t, 1.8, lift=40.0, x=slot_x + 25.0, y=HW.TABLE_FRONT - 35.0, yaw=90.0)
            self.planks.append((slot_x, t2))
            t = t2 + 0.1
        t_dealt = t
        # r42 (Glo off the lamp posts): in the plank close shot he hangs whole in its top left (4230); in the wide
        # shot after it he drifts a little left (4200), so the next close shot (its left edge at 4294) leaves him out
        self.glo_to(self.planks[2][1], GLO_TABLE_X - 30.0, v=15.0)
        # r42: ...and lays it back down on the new planks once the last one is on
        self.hans_hold(2, t_up, t_dealt + 0.2, lambda tt: (PEEL_HOME[0] - PEEL_ASIDE + PEEL_GRIP, PEEL_HOME[1] - PEEL_LIFT),
                       reach=0.0, back=0.0)
        # r46 (round 45 part 3 must-fix "the peel rises by itself and hangs in mid-air ~5 s, no tentacle on it"): held
        # in his tentacle the whole time (so drawn in front of him with the grip, not left lying on the air behind him)
        peel.follow(t_up, t_dealt + 0.2, lambda tt, pk=pk: dict(pk), holder=("Hans", 2))
        self.carry(peel, 2, t_dealt + 0.2, 1.4, grip=(PEEL_GRIP, 0.0), lift=0.0, x=PEEL_HOME[0], y=PEEL_HOME[1],
                   hx=PEEL_HOME[0] + 150.0, hy=PEEL_HOME[1], reach=0.0)
        self.say["lay"] = max(self.planks[0][1] - 2.4, t1)          # r20 (part 3: the line came 8 s before the
        self.line("lay", self.say["lay"])                           # first plank was laid)
        self.hans_hold(-1, t - (t - t1) - 1.6 * 0.85, t_last - 0.1,
                       lambda tt: (pl[0].at(tt)[0]["x"] - 80.0, pl[0].at(tt)[0]["y"] + 4.0), back=0.6)
        self.hans_hold(1, t - (t - t1) - 1.6 * 0.85, t_last - 0.1,
                       lambda tt: (pl[0].at(tt)[0]["x"] + 80.0, pl[0].at(tt)[0]["y"] + 4.0), back=0.6)
        t = self.walk("tentacles", t, HANS_TABLE) + 0.2
        return t

    def hans_x_plan(self):
        return self.walks["tentacles"][-1][1]

    def hans_x(self, t):
        return self.paths["tentacles"](t) if hasattr(self, "paths") else self.walks["tentacles"][-1][1]

    def plank_carry(self, t):
        return dict(x=self.hans_x(t) - 140.0, y=HW.RACK_Y - 90.0)

    # ---------------------------------------------------------------- 12. the bread
    def _bake(self, t):
        P = self.prop
        # the sack to the table's end; flour, water, kneading
        sk = self.props["sack"]
        self.say["dough"] = t
        td = self.line("dough", t)
        self.dough_zoom_t0 = t - 0.5
        t = self.walk("tentacles", t, HANS_DOUGH)                  # a step back, room for Twigs at the dough
        self.sack_down2 = (t, t + 2.6)
        # (r4: low across in front of him the whole way, under his face, never over his head and round behind it)
        # (r5: first straight up beside him, clear of the table top, and only then in front; then low across,
        # dipping under his mouth, onto the rack right of his face)
        # r37 (round 36 part 3 must-fix "from behind his legs to in front of his chest"): first up and out to his
        # left from behind his legs, still behind him, over the table's end, clear of his body; only there in front
        a0, a1, a2 = SACK_OUT
        sk.move(t, t + a0, holder=("Hans", 2), x=SACK_T[0], y=SACK_OUT_Y)
        sk.move(t + a0, t + a1, holder=("Hans", 2), x=SACK_OUT_X, y=SACK_OUT_Y - 6.0)
        sk.move(t + a1, t + a2, holder=("Hans", 2), lift=-50.0, x=SACK_R[0], y=SACK_R[1])
        sk.zf = getattr(sk, "zf", []) + [(t + a1, 21.0)]
        self.hans_hold(2, t, t + a1, lambda tt: self.sack_grip(tt), back=0.0)
        self.hans_hold(2, t + a1, t + a2, lambda tt: self.sack_grip(tt), reach=0.0)
        t += a2 + 0.2
        # r5 ("the flour shows up on its own: the sack is never opened, tipped or poured"): a second tentacle pulls
        # the bow open, he lifts the sack and tips it over the dough, the flour runs out of its mouth, back upright
        U = UNTIE_S                                                # r14 (part 3: "the bow vanishes, no untying
        self.untie = (t, t + U)                                    # motion"): the bow pulled, the turns unwound
        sk.move(t, t + U, how="lin", holder=("Hans", 2), tied=0.0)   # one by one, the end dropped by the mouth
        self.hans_hold(1, t - 0.3, t + U + 0.3, lambda tt: self.sack_bow(tt), reach=0.5, back=0.5)
        t0_ = t
        t += U - 0.8
        self.pour = (t + 0.9, t + 3.9)                             # (the flour runs from pour[0] + 0.6 to pour[1])
        sk.move(t + 0.9, t + 1.6, holder=("Hans", 2), tip=SACK_TIP, y=SACK_R[1] - SACK_TIP_UP)
        sk.move(t + 3.9, t + 4.6, holder=("Hans", 2), tip=0.0, y=SACK_R[1], tied=0.3)   # r32 (round 31 part 3
        # must-fix "the empty sack turns into a pail"): his tentacle at its top gathers the mouth shut into a neck as
        # he stands it up again, so it stays a soft cloth sack (its drawstring's tail still hanging)
        self.hans_hold(2, t0_, t + 4.6, lambda tt: self.sack_grip(tt), reach=0.6)
        t += 4.8
        # r26 (part 3 must-fix "the sack sinks straight down through the sawhorse's top board"): lifted up off the
        # board first; r27 (part 3 must-fix "pale, behind his legs, then pops in front"): then brought forward and
        # lowered in front of the sawhorse and his legs to its place, in front of everything the whole way
        sk.zf += [(t, 21.0)]
        sk.move(t, t + 0.6, holder=("Hans", 2), x=SACK_R[0], y=SACK_UP_Y)
        sk.move(t + 0.6, t + 1.4, holder=("Hans", 2), x=(SACK_R[0] + SACK_F[0]) / 2, y=SACK_UP_Y + 30.0)
        sk.move(t + 1.4, t + 2.6, holder=("Hans", 2), x=SACK_F[0], y=SACK_F[1])
        self.hans_hold(2, t, t + 2.6, lambda tt: self.sack_grip(tt), reach=0.0)
        t += 0.2
        jug = self.props["jug"]
        # r9 (part 3 must-fixes): the jug only once the sack is down (it crossed the sack as that went down, and the
        # sack seemed to sink by itself), and his tentacle stays round it through the pour (it hung there alone)
        t1 = self.carry(jug, 1, t + 2.5, 1.8, lift=40.0, x=DOUGH[0] + FLOUR_DX + 37.0, y=DOUGH[1] - 60.0, ang=-50.0,
                        back=0.0)                                  # (r42: its low lip right over the heap's top)
        self.water = (t1, t1 + 2.2)                                # poured while it's tipped over the dough (r42: 2.2 s,
        self.hans_hold(1, t1, t1 + 2.4, lambda tt: (jug.at(tt)[0]["x"], jug.at(tt)[0]["y"]), reach=0.0, back=0.0)
        # (round 41 part 3: the 1.4 s hairline stream was invisible; it's a ribbon with a wet patch now)
        t1 = self.carry(jug, 1, t1 + 2.4, 1.6, x=JUG_HOME[0], y=JUG_HOME[1], ang=0.0, reach=0.0)
        t = t1 + 0.2
        self.knead = (t, t + 6.0)
        for s, ph in ((-1, 0.0), (0, math.pi)):
            self.hans_hold(s, self.knead[0], self.knead[1], lambda tt, ph=ph: (flour_x(self, tt) + 10 * math.sin(4 * tt + ph),
                                                                               DOUGH[1] - 22 + 8 * math.cos(4 * tt + ph)))
        t = max(self.knead[1], td) + 0.4
        # r29 (cc77): the sack carry stepped him in to ~4748; one step back after the kneading, room for Twigs
        self.walk("tentacles", self.knead[1] + 0.2, HANS_DOUGH, v=60.0)
        # Twigs cuts it in four; Hans rounds each into a loaf
        self.say["loaves"] = t
        tl = self.line("loaves", t)
        cuts = []
        # owner, FK0021: "he has to take like 6 steps to slice the dough. Why doesn't he just move his hand": one
        # short step to the dough, then three cuts with his arm alone, at the quarters
        tc = max(t, self.walks["teeth"][-1][0]) + 0.2              # (he is at the table: one short step nearer)
        tc = self.walk("teeth", tc, TW_DOUGH, v=22.0) + 0.2       # (slow: a small side step, not a crab walk)
        self.dough_lines = []                                      # each cut: (x, y, dx/dy) of the blade's line
        for i_, dx in enumerate(DOUGH_CUTS):
            # r13: aimed where the line is by then (the pieces left of it already pushed over PIECE_GAP each; the
            # blade sawed a hand's width left of its own kerf)
            c1, tb = self.cut(tc, TW_DOUGH, DOUGH[0] + dx + PIECE_GAP * i_, DOUGH_CY, strokes=3, slant=0.8,
                              v_at=0.85, tip_max=HW.RACK_Y + 2.0, smax=0.0, sback=-10.0, reach_dur=0.9,
                              pre=-0.5, lift_dy=10.0, hold=0.6)   # r25: tip on the board; blade out as he reaches
            c_ = self.twigs_cuts[-1]
            c_["kind"] = "dough"                                   # r4: full, clear saw strokes
            # r25: the kerf runs exactly along the blade's own line (the drawn blade's middle, as cut_pose has it),
            # in the dough's frame (the pieces right of the earlier cuts pushed over PIECE_GAP each)
            (hx_, hy_), (ux_, uy_) = c_["hand"], c_["dir"]
            nx_, ny_ = -uy_, ux_
            if nx_ * c_["sx"] < 0:
                nx_, ny_ = -nx_, -ny_
            bx_, by_ = hx_ + ux_ * 6 * K + nx_ * 13 * K, hy_ + uy_ * 6 * K + ny_ * 13 * K
            xk = bx_ + (DOUGH_CY - by_) * ux_ / uy_ - PIECE_GAP * i_
            self.dough_lines.append((xk, DOUGH_CY, ux_ / uy_, c_["c0"], c_["c1"]))
            cuts.append(c1)
            tc = tb
        self.dough_cuts = cuts
        self.loaves, self.loaf_rolls = [], []
        self.walk("teeth", tc + 0.2, TW_DOUGH + 105.0, v=80.0)     # r16: one short step back, out of Hans' way
        # (r29: +105, back to where r28's step ended, with the nearer dough spot: Hans at HANS_ROLL, cc76)
        t = max(tc + 0.6, self.walk("tentacles", tc + 0.6, HANS_ROLL) + 0.1)   # r16: a step nearer the dough
        # the four quarters are born exactly as cut (each a slice of the dough, nothing rounder); Hans rolls each one
        # round under his tentacle tip, where it lies, and only then lifts it onto the board ("not cheap, chintzy
        # warping of things from one form to another")
        for j in range(4):
            cx_, _ = slice_centre(self, j)
            p = P(f"loaf {j}", "loaf", 23, 26.0, born=cuts[-1], x=cx_ + piece_off(self, j, cuts[-1]), y=DOUGH[1],
                  ang=0.0, shape=0.0, bake=0.0, piece=float(j))
            p.why_born = "cut from the dough by Twigs' blade"
            if j == 3:                                             # the last piece slides off the last cut
                p.move(cuts[-1], cuts[-1] + PIECE_SLIDE, how="ease", x=cx_ + piece_off(self, j, 1e9))
            self.loaves.append(p)
            sl = j % 2 - 1
            roll = (t, t + 0.5 + ROLL_N * ROLL_PER)               # (tip down first, then the strokes)
            self.loaf_rolls = getattr(self, "loaf_rolls", []) + [(sl, roll[0], roll[1])]   # r38: drawn over it
            x_r = p.end_pose()["x"]
            p.follow(roll[0], roll[1], lambda tt, r0=roll[0], x_r=x_r: roll_pose(tt, r0, x_r), holder=("Hans", sl))
            self.hans_hold(sl, roll[0], roll[1], lambda tt, p=p, r0=roll[0]: (    # r14: the tip circles on top of it,
                p.at(tt)[0]["x"] - 2.0 + 12.0 * math.sin(2 * math.pi * roll_k(tt, r0)),   # cupping it round ("the
                p.at(tt)[0]["y"] - LOAF_TIP_DY + 3.0 * math.cos(2 * math.pi * roll_k(tt, r0))),  # pieces turn into rolls by
                reach=0.6, back=0.0)                                                      # themselves")
            t = self.carry(p, sl, roll[1], 1.4, x=LOAF_ON_BOARD[j][0], y=LOAF_ON_BOARD[j][1], reach=0.0) + 0.1
        t = max(t, tl) + 0.4
        # onto the peel; Glo floats it over to the oven and slides it in (owner, FK0019: no long walks), lights the
        # lanterns while the bread bakes, and brings it back golden; Hans sets the loaves on the table
        peel = self.props["peel"]
        # r16 (part 3 must-fix: his tentacle grew 1.5 body widths to carry the loaves across to the peel held far
        # out at his left, and again to the dough): he holds the peel at his front, the blade just left of the board,
        # and lifts each loaf over the handle onto it, a short pass
        t = self.walk("tentacles", t - 0.3, HANS_LOADX)              # a step back left, by the table's end
        hx_ = HANS_LOADX - PEEL_LOAD[0]                            # (where the blade is, left of his middle)
        t1 = t + 1.6 * 0.85
        # (he takes it by the handle off the table's end and lifts it up level to his front, the handle low; r23 part 3
        # must-fix "peel through the stop block": straight up first, left of the block, then over its top to him)
        tm = t + 0.9
        peel.move(t, tm, holder=("Hans", 1), x=PEEL_HOME[0], y=PEEL_LOAD[1], ang=0.0, tilt=0.0,
                  hx=PEEL_HOME[0] + 150.0, hy=PEEL_LOAD[1], flat=0.0)   # (r31: tipped up on edge as it rises)
        t1 += 0.3
        peel.move(tm, t1, holder=("Hans", 1), x=PEEL_LOAD[0], y=PEEL_LOAD[1], ang=0.0, tilt=0.0,
                  hx=PEEL_LOAD[0] + PEEL_HANDLE[0], hy=PEEL_LOAD[1] + PEEL_HANDLE[1])
        peel.zf = [(t + 0.3, 22.0)]                                # (in front of him and the rack while he has it)
        t_hold0 = t

        def grip(tt):                                              # his tentacle near the handle's end, all along
            q = peel.at(tt)[0]                                     # (from the moment he takes it up, leaning)
            ux, uy = q.get("hx", q["x"] + 150.0) - q["x"], q.get("hy", q["y"]) - q["y"]
            vis = math.radians(q.get("tilt", 0.0)) + math.atan2(uy, ux)
            L = q.get("gf", 0.8) * math.hypot(ux, uy)
            return q["x"] + L * math.cos(vis), q["y"] + L * math.sin(vis)
        for j, p in enumerate(self.loaves):
            qj = self.on_peel(j, t1)
            t1 = self.carry(p, 0, t1, 1.3, lift=30.0, x=qj["x"], y=qj["y"], s=qj["s"]) + 0.05   # (over the handle,
            # under his mouth)
            p.follow(t1, 1e8, lambda tt, j=j: self.on_peel(j, tt), holder=("the peel", 0))
        self.zoom_on(self.dough_zoom_t0, t1 + 0.4, 2.1, DOUGH[0] - 90.0, 790.0, rin=2.0, rout=2.0)   # r4: closer (the
        # cuts were too small to see; r16: till the loaves are on the peel)
        # a short walk left with it, and he lays it on the table's end
        tw0 = t1 + 0.3
        tw1 = self.walk("tentacles", tw0, HANS_LAY, v=85.0)

        def carried(tt):                                           # (the handle comes level as he goes)
            u = ease(tt, tw0, tw1)
            x = self.hans_x(tt) - hx_
            return dict(x=x, y=PEEL_LOAD[1], ang=0.0, tilt=0.0, hx=x + lerp(PEEL_HANDLE[0], 150.0, u),
                        hy=PEEL_LOAD[1] + lerp(PEEL_HANDLE[1], 0.0, u))
        peel.follow(tw0, tw1, carried, holder=("Hans", 1))
        t_lay = tw1 + 0.2 + 1.3 * 0.85
        peel.move(tw1 + 0.2, t_lay, holder=("Hans", 1), x=PEEL_LAY_X, y=PEEL_DOWN_Y, ang=0.0, tilt=0.0,
                  hx=PEEL_LAY_X + 150.0, hy=PEEL_DOWN_Y, flat=1.0)   # (r31: laid flat)
        self.hans_hold(1, t_hold0, t_lay, grip)
        t_clr = self.walk("tentacles", t_lay + 0.6, HANS_CLEAR, v=85.0)   # and steps back, out of Glo's way
        hand_dy = lambda y: y - (GB - CRUISE + GLO_HOLD + 10.0)     # noqa: E731  Glo's dip to hold the handle at y
        up_x = PEEL_LAY_X + PEEL_GRIP + 4.0                       # (his tendrils are 4 px left of his middle)
        gx0 = self.glo_keys[-1][1]
        tg = self.glo_to(t_clr + 0.4 - abs(up_x - gx0) / 150.0 - EASE, up_x, v=150.0)   # (once Hans is clear)
        take = tg + 1.0
        lift_t = take + 0.9                                        # up off the table before he floats away
        # Glo floats to the oven's lower right, the peel turning as he goes to point into the door; he pushes it
        # in (blade and loaves through the door, behind the front wall), lets go, and the handle rests on the path
        # (round 4: the bread came down over the oven's face. Now the peel is turned and lowered to the door's height
        # off to the oven's right, clear of it, and only then carried straight across, level, into the door)
        glo_x_oven = G_OUT[0] + 4.0
        x_pre = glo_x_oven + 460.0                                 # the loaves clear of the dome's right side
        # (r47, advisor FK0021 r46 must-fix "the peel's shaft runs through the lamp post": +460, the whole peel right of it)
        # (r42: +340, was +200: Glo held the bread right in front of the lamp post at 3960)
        tp = self.glo_to(lift_t, x_pre, v=170.0)
        self.peel_keys = dict(m_in=(lift_t, tp))
        ta = self.glo_to(tp + 1.0, glo_x_oven, v=90.0)
        rise = (ta + 0.3, ta + 2.5)                                # r33: up from the path to the door's sill, under it
        self.peel_keys["n_in"] = (tp - 1.2, tp + 0.4) + rise       # r22/r33: near us (on the path) across, then up
        self.slide_in = (rise[1] + 0.2, rise[1] + 1.6)             # r20: slow enough to read (was 0.8 s)
        self.peel_keys["d_in"] = self.slide_in
        release = self.slide_in[1] + 0.4
        self.glo_dy += [(tg - 0.8, take + 0.8, hand_dy(PEEL_DOWN_Y)), (take, tp + 0.8, hand_dy(PEEL_UP[1])),
                        (tp, release + 0.9, hand_dy(G_OUT[1])), (self.slide_in[0], release + 0.9, -PUSH),
                        ]   # r20 (part 3 must-fix "the loaves come in low over the base slab, then jump up into the
        # door"): no dip under the door any more: the peel is at the door's height from where it is clear of the
        # oven, then slides straight across in front and in
        m_ = peel.moves[-1]                                        # (the peel lies exactly where his tendrils take
        peel.moves[-1] = m_[:3] + (dict(m_[3], y=PEEL_DOWN_Y + glo_bob(take), hy=PEEL_DOWN_Y + glo_bob(take)),) + m_[4:]   # it: his bob included)
        peel.follow(take, release, lambda tt: dict(self.peel_in_glo(tt), flat=1.0 - ease(tt, take, lift_t)),
                    holder=("Glo", 0))                             # (r31: tipped up on edge as he lifts it)
        peel.zf.append((take, 9.8))
        for p in self.loaves:
            p.zf = [(take, 9.9)]
        q = self.peel_in_glo(release)
        peel.move(release, release + 0.01, **q)                    # it rests in the oven's door
        a0 = self.peel_keys["n_in"][0]
        self.glo_fy.append((a0, release, 1e8, NEAR_DY, lambda u, a0=a0, r=release: self.peel_near(a0 + u * (r - a0))))
        # r33 (round 32 part 3 must-fix "Glo floats all the way across one static wide shot"): a cut to the oven
        # just after he lifts the peel off the table, so he comes in from the right of the oven's shot (was a 3 s pan)
        self.zoom_on(lift_t + 1.2, release + 1.6, 1.4, HW.OVEN_X + 120.0, 760.0, rin=0.0, rout=2.2)
        self.say["oven_in"] = self.slide_in[0] - 1.6
        self.line("oven_in", self.say["oven_in"])
        # Glo lights the lanterns, one by one
        self.say["lanterns"] = release + 1.4
        self.line("lanterns", self.say["lanterns"])
        self.lit = []
        tg = self.say["lanterns"] + 0.3
        for j, (lx, ly) in enumerate(HW.LANTERNS):
            # owner, FK0021: the basket blocked the lanterns lighting up. The basket stayed at the mill; Glo hovers
            # beside each lantern (his lamp level with it, never in front of it) and his light floats across to it
            tg = self.glo_to(tg, lx + 28.0 - 170.0, v=150.0)
            self.glo_dy.append((tg - 0.6, tg + 2.4, (ly - 16.0 + 128.0) - (GB - CRUISE)))
            self.flares.append((tg + 0.4, tg + 1.6, lambda tt, lx=lx, ly=ly: (lx + 28.0, ly - 16.0)))
            self.lit.append(tg + 1.2)
            tg += 2.6
        self.light_keys += [(self.say["lanterns"], "dusk"), (tg + 6.0, "night")]
        self.zoom_on(release + 1.7, self.lit[-1] + 1.6, 1.45, HW.LANTERNS[1][0] + 28.0, 640.0, rin=2.5, rout=1.6)
        tz = tp + 1.6                                              # r32 (round 31 part 3 must-fix "Digs appears out of
        # nowhere by the oven"): they come over in the oven's shot, seen arriving (it was while the camera was on the
        # lanterns, out of shot)
        self.walk("digger", tz, DIGS_WAIT)                         # a step nearer the path, clear of the
        self.walk("springs", tz + 1.8, SPRINGS_WAIT)               # oven's door (r12: Springs a moment after Digs,
                                                                   # so he never catches him up)

        # back to the oven: he takes the peel and draws it out, the bread golden
        self.walk("tentacles", self.lit[-1] + 2.0, HANS_BREAD)      # r7: Hans along the table, behind Glo
        tb = self.glo_to(max(tg, self.slide_in[1] + 13.0), glo_x_oven, v=150.0)
        grab = tb + 0.9
        self.slide_out = (grab + 0.3, grab + 1.5)                  # he draws it back out through the door
        self.peel_keys["d_out"] = self.slide_out
        tout = self.slide_out[1]
        self.bake_t = (self.slide_in[1], grab)
        # r22: out of the door towards us (lower, bigger) before he turns away with it
        # r41 (round 40 part 3 must-fix "the loaves slide out and down at a slant across the oven's front wall"):
        # first straight out towards us, level with the sill (it grows: nearer), and only then down
        self.peel_keys["ns_out"] = (tout + 0.1, tout + 0.9)
        down = (tout + 0.9, tout + 2.7)                            # r33: then straight down towards us, under the door
        # (r40, round 39 part 3 must-fix "drops 70 px in 0.3 s through the sill": back to a slow 2 s, growing as it
        # comes towards us)
        t_clr = self.glo_to(down[1], x_pre, v=170.0)               # and along below the oven, until the
        # r39 (round 38 part 3 must-fix "the loaves slid along the dirt path for 5 s"): a quick dip under the door and
        # out to the right, then straight back up the moment they are clear of the oven; held up there, not low
        rise = (t_clr - 0.1, t_clr + 1.1)
        t_hold = rise[1] + BREAD_HOLD                              # r10 (part 3 must-fix): he holds the bread
        self.bread_shot = (rise[1], t_hold)                        # there, close, warm and steaming, a moment
        self.glo_dy += [(tb - 0.8, t_hold + 0.8, hand_dy(G_OUT[1]) - PUSH),   # loaves are clear of the oven (round 4)
                        (self.slide_out[0], t_hold + 0.8, PUSH)]          # (r20: and out level, no dip)
        tup = self.glo_to(t_hold + 0.2, HANS_BREAD + 270.0, v=170.0)   # r7: beside Hans, on his right (r16: nearer
        # and the handover went out of sight behind his head, "the peel vanishes")
        self.peel_keys["m_out"] = (t_hold + 0.2, tup)                # and turns it flat again as he floats back
        self.peel_keys["n_out"] = down + rise
        b0 = tout + 0.1
        self.glo_fy.append((b0, rise[1], 1e8, NEAR_DY,
                            lambda u, b0=b0, r=rise[1]: self.peel_near(b0 + u * (r - b0))))
        self.glo_dy.append((t_hold, tup + 6.0, hand_dy(PEEL_HAND_Y)))   # (stretched to the set-down below)
        i_up = len(self.glo_dy) - 1
        # r13 (part 3 must-fix: he carried the hot loaves back behind Hans' head): up over Hans' head on the way, and
        # down again only once he is past him, on his right
        self.glo_dy.append((t_hold - 0.4, tup + 0.6, -GLO_OVER_HANS))
        peel.follow(grab, tup + 6.0, lambda tt: self.peel_in_glo(tt), holder=("Glo", 0))
        self.zoom_on(tb - 3.0, t_hold + 2.0, BREAD_ZOOM, x_pre - 154.0, 850.0, rin=3.0, rout=2.2)   # r10: the bread big
        self.say["baked"] = self.slide_out[1] + 0.3
        self.line("baked", self.say["baked"])
        self.voice_events += [(self.slide_out[1] + 0.5, "tentacles", "yay", None),
                              (self.slide_out[1] + 1.8, "springs", "mm", None)]
        tt = tup + 0.5
        for j, p in enumerate(self.loaves):
            t0_, _, p0_, p1_, how_, lift_, holder_, fn_ = p.moves[-1]
            q = self.on_peel(j, tt + 0.5 * j)
            p.moves[-1] = (t0_, tt + 0.5 * j, p0_, dict(p1_, **q), how_, lift_, holder_, fn_)
            p.zf.append((tt + 0.5 * j, 23.0))
        for j in (3, 2):                                            # the near half of the table
            self.carry(self.loaves[j], {3: 0, 2: 1}[j], tt + 0.5 * j, 1.4, lift=30.0, x=LOAF_ON_TABLE[j][0],
                       y=LOAF_ON_TABLE[j][1], reach=0.4, s=1.0)
        t_up = tt + 0.5
        hold = {0: -110.0, 1: -60.0}
        hx0 = self.walks["tentacles"][-1][1]
        for j in (0, 1):                                            # held up at his left, walked along
            sl = j - 1 if j == 0 else 2
            te = self.carry(self.loaves[j], sl, tt + 0.5 * j, 1.2, lift=20.0, x=hx0 + hold[j],
                            y=LOAF_UP, reach=0.4, back=0.0, s=1.0)
            # r11 (part 3 must-fix: they hung by his cheek with nothing holding them): his tentacle stays on it
            self.loaves[j].follow(te, tt + 3.4, lambda t_, j=j: dict(x=hx0 + hold[j], y=LOAF_UP), holder=("Hans", sl))
            self.hans_hold(sl, te, tt + 3.4, lambda t_, j=j: (hx0 + hold[j], LOAF_UP - 10.0), reach=0.0, back=0.0)
        ta = self.walk("tentacles", tt + 3.4, LOAF_HX, v=90.0)
        for j in (0, 1):
            sl = j - 1 if j == 0 else 2
            self.loaves[j].follow(tt + 3.4, ta + 0.4 * j, lambda t_, j=j: dict(x=self.hans_x(t_) + hold[j], y=LOAF_UP),
                                  holder=("Hans", sl))
            self.hans_hold(sl, tt + 3.4, ta + 0.4 * j, lambda t_, j=j: (self.loaves[j].at(t_)[0]["x"],
                                                              self.loaves[j].at(t_)[0]["y"] - 10.0), reach=0.0, back=0.0)
            self.carry(self.loaves[j], sl, ta + 0.4 * j, 1.4, lift=10.0, x=LOAF_ON_TABLE[j][0], y=LOAF_ON_TABLE[j][1],
                       reach=0.0)
        tt = ta - 1.6
        # Glo sets the peel down behind the table and floats up
        td = tt + 2.0 + 1.6
        self.glo_to(td - 3.2, self.glo_keys[-1][1] - 150.0, v=90.0)   # r7: over the table, so the whole peel lies on it
        self.glo_dy.append((tup + 5.2, td + 1.6, hand_dy(PEEL_DOWN_Y) - hand_dy(PEEL_HAND_Y)))
        self.glo_dy[i_up] = self.glo_dy[i_up][:1] + (td + 1.6,) + self.glo_dy[i_up][2:]
        q = self.peel_in_glo(td)                                   # (r5: the whole pose - the handle's end kept a
        peel.moves[-1] = peel.moves[-1][:1] + (td,) + (peel.moves[-1][2], dict(q)) + peel.moves[-1][4:]   # stale height)
        peel.move(td, td + 0.2, how="fall", x=q["x"], y=PEEL_DOWN_Y, hx=q["x"] + 150.0, hy=PEEL_DOWN_Y)   # let go
        peel.move(td + 0.2, td + 0.5, flat=1.0)                    # (r31: and it settles flat on the table)
        peel.zf = list(getattr(peel, "zf", [])) + [(td, 22.0)]     # on the table, in front of it (behind the loaves)
        return td + 1.2

    def peel_in_glo(self, t):
        """The peel by its handle in Glo's tendrils: flat along the screen, or turned to point into the oven's door
        (then without his bob: the blade lies still on the door's floor)."""
        hx, hy = self.glo_hand(t)
        om, dz = self.peel_mode(t)
        hy -= glo_bob(t) * om
        vx, vy = lerp(PEEL_GRIP, OVEN_V[0], om), lerp(0.0, OVEN_V[1], om)
        L = math.hypot(vx, vy) or 1.0
        # r27 (part 3 must-fixes "the row of loaves is wider than the opening, drawn over both jambs, then shrinks"):
        # at the door's size (0.8) from the moment it's turned toward the oven till it's clear of it again, so the
        # row always fits the opening and never changes size at the door
        sc = 1.0 - NEAR_SC * om * (1.0 - self.peel_near(t, True)) - 0.1 * dz   # r33: near (on the path) 1.0, in front of
        # the door 0.9, in it 0.8: a step further back is a step smaller
        return dict(x=hx - vx, y=hy - vy, ang=0.0, om=om, dz=dz, sc=sc, hx=hx + 30.0 * vx / L,
                    hy=hy + 30.0 * vy / L)

    def on_peel(self, j, t):
        """Loaf j on the peel's blade, two by two and staggered so all four show: 0 and 1 at the back (a little
        higher, half a loaf along, smaller, drawn first), 2 and 3 at the front; the same layout whichever way the
        peel points, so they never shuffle about on it."""
        q = self.props["peel"].at(t)[0]
        sc = q.get("sc", 1.0)
        return dict(x=q["x"] + (-1.5 + j) * LOAF_STEP * sc, y=q["y"] + (-4.0 + PEEL_FLAT_DY * q.get("flat", 0.0)) * sc,   # r5: one row of four, each a
                    bake=self.bake_amount(t), s=sc)          # little over the one before (all four show, all in the door)

    def peel_near(self, t, size=False):
        """0..1: how much nearer us than the oven's door the peel is held (r22): across in front of the door.
        size (r41): for its size, which on the way out grows first, level at the sill (ns_out), before it's lowered."""
        k = getattr(self, "peel_keys", {})
        n = 0.0
        for key in ("n_in", "n_out"):
            if key in k:
                a0, a1, b0, b1 = k[key]
                if size and key == "n_out" and "ns_out" in k:
                    a0, a1 = k["ns_out"]
                n = max(n, ease(t, a0, a1) * (1 - ease(t, b0, b1)))
        return n

    def peel_mode(self, t):
        """(om, dz): how far the peel has turned to point into the oven's door, and how far in through it."""
        k = getattr(self, "peel_keys", {})
        om = ease(t, *k.get("m_in", (1e9, 1e9 + 1))) * (1 - ease(t, *k.get("m_out", (1e9, 1e9 + 1))))
        dz = ease(t, *k.get("d_in", (1e9, 1e9 + 1))) * (1 - ease(t, *k.get("d_out", (1e9, 1e9 + 1))))
        return om, dz

    def bake_amount(self, t):
        return ease(t, self.bake_t[0] + 2.0, self.bake_t[1] - 2.0) if hasattr(self, "bake_t") else 0.0

    # ---------------------------------------------------------------- 13. the feast
    def _feast(self, t):
        """The animals come out of their houses: the camera drifts to them and comes back with them. Everyone at the
        table: Hans breaks a loaf and gives each animal a piece."""
        # Digs and Springs come to the table (they were by the oven)
        for kd in ("tentacles", "teeth", "wheels"):
            self.walk(kd, t, FEAST[kd])
        # Digs and Springs come over from the oven while the camera is on the houses: they set off out of its right
        # side and are at the table when it comes back (r2 review: an 8 s walk in view)
        self.voice_events.append((t + 5.6, "digger", "mm", None))
        t_go = t + 1.0 + 7.0 + 3.0                                 # (the doors + 3: the close shot of the houses)
        self.walk("digger", t_go, FEAST["digger"], v=130.0)
        self.walk("springs", t_go + 0.3, FEAST["springs"], v=130.0)   # (same pace: he never catches Digs up)
        self.glo_to(t, FEAST_GLO)
        self.glo_dy.append((t + 1.0, 1e8, -70.0))                  # Glo hangs over the table like a lamp
        t_c = t + 1.0
        self.cam_keys += [(t_c, CAM_V), (t_c + 8.0, CAM_HOUSES)]
        self.say["animals"] = t_c + 6.0
        ta = self.line("animals", self.say["animals"])
        self.doors = t_c + 7.0
        self.animals = []
        for j, (kind, home, seat) in enumerate(ANIMALS):
            t0 = self.doors + 1.0 + 2.2 * j
            self.animals.append(dict(kind=kind, home=home, seat=seat, out=(t0, t0 + 2.0), go=(t0 + 2.0, None),
                                     lane=GB + ANIMAL_LANES[j]))
        tb = self.doors + 1.0
        self.birds = []
        for j, (home, perch) in enumerate(BIRDS):
            self.birds.append(dict(home=home, perch=perch, fly=(tb + 0.8 * j + 2.0, tb + 0.8 * j + 6.0)))
        # the animals go along the path to the table (hop / trundle), the camera comes back with them
        arrive = 0.0
        for a in self.animals:
            v = 120.0 if a["kind"] == "bunny" else 70.0
            d = abs(a["seat"][0] - a["home"]) + 60.0
            a["go"] = (a["out"][1], a["out"][1] + d / v)
            arrive = max(arrive, a["go"][1])
        self.cam_keys += [(self.doors + 3.0, CAM_HOUSES), (arrive - 1.0, CAM_V)]
        for j, b_ in enumerate(self.birds):                        # two take off in the houses' close shot and land
            if j < 2:                                              # as the camera comes back; the other two fly in
                # r26 (part 3 must-fix "the birds never come out"): in the close shot each peeps out of its
                # birdhouse's round door, hops out onto the little ledge, looks round and flies down and away
                # towards the table (low, never up out of the shot)
                p0 = self.doors + 5.5 + 1.0 * j                    # (once the zoom has settled, both houses in it)
                b_["out"] = (p0, p0 + 0.8, p0 + 1.2)               # peep out, hop to the ledge, sit
                b_["fly"] = (p0 + 1.7, p0 + 6.2)                   # from the right once it is at the table
            else:
                b_["fly"] = (arrive - 1.0 + 0.8 * (j - 2), arrive + 3.5 + 0.8 * (j - 2))
        self.zoom_on(self.doors + 2.0, self.animals[-1]["out"][1] + 3.0, 1.7, (HW.HEDGE_X + HW.BUNNY_X) / 2, 820.0,
                     rin=2.0, rout=3.0)
        t = max(arrive, ta) + 0.6
        # Hans breaks a loaf and hands round the pieces; they nibble
        self.say["feast"] = t
        self.line("feast", t)
        self.pieces = []
        loaf = self.loaves[2]                                      # the one in front of him (r8: his tentacles and the pieces at its place, LOAF_ON_TABLE[2])
        BR = BREAK_S                                               # r14: slower ("no one is seen breaking a loaf")
        self.break_t = (t, t + BR)
        loaf.follow(t, t + BR, lambda tt: dict(split=ease(tt, t, t + BR)), holder=("Hans", 0))
        self.hans_hold(0, t, t + BR, lambda tt: (LOAF_ON_TABLE[2][0], LOAF_ON_TABLE[2][1] - 20.0))
        self.hans_hold(-1, t, t + BR, lambda tt: (LOAF_ON_TABLE[2][0] + 8.0, LOAF_ON_TABLE[2][1] - 18.0))
        tp = t + BR + 0.2
        for j, a in enumerate(self.animals):
            if a["kind"] != "bunny":
                continue
            pc = self.prop(f"bread piece {j}", "piece", 24, 10.0, born=t + BR, x=LOAF_ON_TABLE[2][0] - 10 + 10 * j,
                           y=LOAF_ON_TABLE[2][1] - 6.0, ang=0.0, s=1.0)
            pc.why_born = ("broken off the loaf by Hans", LOAF_ON_TABLE[2])
            dest = (a["seat"][0] + 40.0, a["seat"][1] - 30.0)   # r14: out in front of its nose, in sight
            tp = self.carry(pc, j % 2 - 1, tp, 1.8, lift=40.0, x=dest[0], y=dest[1]) + 0.2
            nib = (tp + 0.4, tp + 14.0)
            # r14 ("nobody eats"): bite by bite, the bunny dipping its head to each one; the piece gets smaller
            # with each bite (not a slow shrink)
            a["bites"] = [nib[0] + 0.3 + BITE_EVERY * k + 0.35 * j for k in range(BITES)]
            for k, b in enumerate(a["bites"]):
                pc.move(b, b + 0.7, how="lin", s=1.0 - 0.75 * (k + 1) / BITES)   # (chewed off, not snapped)
            self.pieces.append(nib)
        # r40 (round 39 part 3 must-fix "the feast: nobody eats, the bread only tiny dots"): Hans breaks off a piece
        # for each Keeper and tosses it over; each catches it in its mouth (open wide, chomp) and munches. Then he
        # eats one himself, bite by bite. (Their own arms can't bring food to their mouths: Springs' and Wheels' are
        # drawn behind their bodies, Digs' are shovels.)
        self._no_step = True
        self.chews = {}
        src = (LOAF_ON_TABLE[2][0], LOAF_ON_TABLE[2][1] - 6.0)
        tz = tp + 0.3
        for n, (kd, slot, rel, T, arc) in enumerate(TOSSES):
            mx, my = FEAST[kd] + MOUTH_AT[kd][0], MOUTH_AT[kd][1]
            pc = self.prop(f"feast piece {n}", "piece", 24, 2 * FEAST_PIECE_R, born=tz, x=src[0] - 8.0 + 5.0 * n,
                           y=src[1], ang=0.0, s=1.0, r=FEAST_PIECE_R)
            pc.why_born = ("broken off the loaf by Hans", src)
            if rel == "hand":                                      # r42: Twigs reaches out, takes it, eats it
                tx_, ty_ = FEAST[kd] + TWIGS_TAKE[0], TWIGS_TAKE[1]
                t_at = self.carry(pc, slot, tz + 0.3, FEED_S - 0.4, lift=10.0, x=tx_ + TWIGS_PIECE[0],
                                  y=ty_ + TWIGS_PIECE[1], reach=0.6, back=0.7)
                hm = (mx + TWIGS_BITE[0] - TWIGS_PIECE[0], my + TWIGS_BITE[1] - TWIGS_PIECE[1])
                self.twigs_feast = dict(reach=(tz, tz + 0.9), take=(tx_, ty_), lift=(t_at + 0.25, t_at + 1.15),
                                        mouth=hm, back=(t_at + 1.55, t_at + 2.45))
                t_eat_ = t_at + 1.3

                def in_paw(tt, f=self.twigs_feast):
                    hx_, hy_ = lerp2(f["take"], f["mouth"], ease(tt, *f["lift"]))
                    return dict(x=hx_ + TWIGS_PIECE[0], y=hy_ + TWIGS_PIECE[1])
                pc.follow(t_at, t_eat_, in_paw, holder=("Twigs", -1))
                pc.gone, pc.why_gone = t_eat_, ("eaten", (mx, my))
                self.chews.setdefault(kd, []).append((t_eat_, t_eat_ + 2.2))
                self.voice_events.append((t_eat_ + 1.2, kd, ("mm", "yay", "mm", "hehe")[n], None))
                tz = t_at + 0.5
                continue
            if rel is None:                                        # r42: fed, right into the mouth
                t_at = self.carry(pc, slot, tz, FEED_S, lift=12.0, x=mx, y=my, reach=0.6, back=0.0)
                self.hans_hold(slot, t_at, t_at + 0.6, lambda tt, m=(mx, my): m, reach=0.0, back=0.7)
                pc.gone, pc.why_gone = t_at + 0.15, ("eaten", (mx, my))
                self.chews.setdefault(kd, []).append((t_at + 0.15, t_at + 2.35))
                self.voice_events.append((t_at + 1.35, kd, ("mm", "yay", "mm", "hehe")[n], None))
                tz = t_at + 0.5
                continue
            rx, ry = FEAST["tentacles"] + rel[0], rel[1]
            t_up = self.carry(pc, slot, tz, 1.2, how="lin", lift=0.0, x=rx, y=ry, reach=0.6, back=0.7)
            # r46 (cc108 thing_jumps: the toss left the slow lift at full speed): a flick, it speeds up off his tip
            # over the first quarter of the flight (C1: no jump in its speed), then flies its arc
            def flick(u, a=0.25):
                u = min(max(u, 0.0), 1.0)
                return (u * u / (2 * a) if u < a else u - a / 2) / (1.0 - a / 2)
            pc.follow(t_up, t_up + T, lambda tt, r=(rx, ry), m=(mx, my), t0=t_up, T=T, arc=arc: (lambda w: dict(
                x=r[0] + (m[0] - r[0]) * w,
                y=r[1] + (m[1] - r[1]) * w - arc * 4.0 * w * (1.0 - w)))(flick((tt - t0) / T)))
            pc.gone, pc.why_gone = t_up + T, ("eaten", (mx, my))
            self.chews.setdefault(kd, []).append((t_up + T, t_up + T + 2.2))
            self.voice_events.append((t_up + T + 1.2, kd, ("mm", "yay", "mm", "hehe")[n], None))
            tz = t_up + 0.4
        mx, my = FEAST["tentacles"] + MOUTH_AT["tentacles"][0], MOUTH_AT["tentacles"][1] + 10.0
        pc = self.prop("feast piece hans", "piece", 24, 2 * FEAST_PIECE_R, born=tz, x=src[0] + 10.0, y=src[1], ang=0.0,
                       s=1.0, r=FEAST_PIECE_R)
        pc.why_born = ("broken off the loaf by Hans", src)
        t_at = self.carry(pc, 1, tz, 1.3, lift=10.0, x=mx, y=my, reach=0.6, back=0.0)
        bites = [t_at + 0.4 + 1.0 * k for k in range(3)]
        self.hans_hold(1, t_at, bites[-1] + 0.9, lambda tt: (mx, my), reach=0.0, back=0.7)
        for k, b in enumerate(bites):                              # (each bite over 0.9 s: under 3 % a frame)
            pc.move(b, b + 0.9, how="lin", s=(0.72, 0.5, 0.32)[k])
        pc.gone, pc.why_gone = bites[-1] + 0.9, ("eaten", (mx, my))
        self.chews["tentacles"] = [(b, b + 0.9) for b in bites]
        self.voice_events.append((bites[-1] + 1.2, "lantern", "mm", None))
        self._no_step = False
        t_eat = bites[-1] + 1.0
        # r9 (part 3 must-fix: "the feast never happens" - it did, but too small in the wide shot): the camera
        # comes in on the table for the break, the sharing and the eating, and back out for the goodnight
        self.zoom_on(self.say["feast"] - 0.8, max(tp + 7.0, t_eat + 1.5), FEAST_Z, FEAST_ZOOM[0], FEAST_ZOOM[1],
                     rin=2.0, rout=3.0)
        self.finale = max(tp + 7.5, t_eat + 2.0)
        self.say_finale = self.finale
        self.signoff = self.finale + _dur(FINALE) + HOLD_END
        self.sign = (self.signoff - 0.6, self.signoff + 0.4)
        return self.signoff

    # ---------------------------------------------------------------- paths, camera
    def _finish(self):
        self.paths = {kd: walk_path(self.walks[kd], EASE) for kd in WALKERS}
        c = getattr(self, "act_cut", 1e9)
        pa = {kd: walk_path([k_ for k_ in self.walks[kd] if k_[0] <= c], EASE) for kd in WALKERS}
        pb = {kd: walk_path([k_ for k_ in self.walks[kd] if k_[0] > c] or [(c, self.walks[kd][-1][1])], EASE)
              for kd in WALKERS}
        self.paths["lantern"] = walk_path(self.glo_keys, EASE)
        self.turns = {kd: heading(self.paths[kd], ahead=0.8) for kd in ORDER}
        narrow = lambda kd, f=1.0: (lambda t: 1.0 - TURN_NARROW * f * abs(self.turns[kd](t)))   # noqa: E731
        self.gaits = {kd: Split(biped(kd, pa[kd], GB, K, spread=narrow(kd)), biped(kd, pb[kd], GB, K,
                                                                                    spread=narrow(kd)), c)
                      for kd in ("teeth", "digger")}
        self.gaits["tentacles"] = Split(WaveGait(GB, K, pa["tentacles"], spread=narrow("tentacles", 0.5)),
                                        WaveGait(GB, K, pb["tentacles"], spread=narrow("tentacles", 0.5)), c)
        cuts = sorted([s_[0] for s_ in self.springs_special if s_[2] in ("jump", "leap")] +    # (r15: leaps too, or
                      [s_[1] for s_ in self.springs_special if s_[2] in ("jump", "leap")] + [c])  # he hopped 36 px back)
        segs, prev = [], -1e9
        keys = self.walks["springs"]
        for b_ in cuts + [1e9]:
            ks = [k_ for k_ in keys if prev < k_[0] <= b_]
            before = [k_ for k_ in keys if k_[0] <= prev]
            if before and abs(prev - c) > 1e-6:
                ks = [(prev + 1e-3, before[-1][1])] + ks
            segs.append((b_, Hopper(walk_path(ks or [(prev, keys[-1][1])], EASE), GB, K)))
            prev = b_
        self.hopper = Multi(segs)
        self.cam = walk_path(sorted(self.cam_keys), 2.5)
        keys = sorted(self.light_keys)
        HW.LIGHT[:] = [(0.0, "gold")] + keys

    def glo_x(self, t):
        return self.paths["lantern"](t) if hasattr(self, "paths") else self.glo_keys[-1][1]

    def glo_y(self, t):
        y = GB - CRUISE
        for t0, t1, dy in self.glo_dy:
            y += dy * ease(t, t0, t0 + 0.8) * (1 - ease(t, t1 - 0.8, t1))
        for t0, t1, t_end, dy, fn in self.glo_fy:                 # (r22: the roof set down at its own pace)
            if t > t0:
                y += dy * fn(_seg(t, t0, t1)) * (1 - ease(t, t_end - 0.8, t_end))
        return y

    def shift(self, t):
        return self.cam(t) - W / 2

    def zoom_on(self, t0, t1, z, fx, fy, rin=2.5, rout=3.0):
        """A slow camera zoom from t0 (in over rin s) to t1 (out over rout s), on world x fx and screen y fy."""
        self.zoom_keys.append((t0, t1, z, fx, fy, rin, rout))

    def zoom(self, t):
        """(zoom, cx, cy): how far the camera is zoomed in and the unzoomed screen point at the frame's middle, kept
        so the zoomed view never leaves the frame."""
        for t0, t1, z, fx, fy, rin, rout in self.zoom_keys:
            if t0 <= t <= t1:
                z, fx, fy = (v(t) if callable(v) else v for v in (z, fx, fy))   # r29: a key may move (the dressing)
                u = ((smoothstep(min(1.0, (t - t0) / rin)) if rin > 0 else 1.0)     # (r31: 0 = no ease: one key
                     * (1 - (smoothstep(max(0.0, (t - (t1 - rout)) / rout)) if rout > 0 else 0.0)))   # hands on)
                zz = 1 + (z - 1) * u
                cx = W / 2 + (fx - self.shift(t) - W / 2) * u
                cy = H / 2 + (fy - H / 2) * u
                hx, hy = W / (2 * zz), H / (2 * zz)                # the zoomed view stays inside the frame
                return zz, min(max(cx, hx), W - hx), min(max(cy, hy), H - hy)
        return 1.0, W / 2, H / 2

    def narration(self):
        out = [(self.hook, HOOK)] + [(t, LINES[k]) for k, t in self.say.items() if k in LINES]
        out += [(self.say_finale, FINALE), (self.signoff, SIGNOFF)]
        return sorted(out)


PLAN = None


def plan():
    global PLAN
    if PLAN is None:
        PLAN = Plan()
    return PLAN


def stone_squash(p, q, g):
    """r22 (round-21 part 2 must-fix "the tentacle tip curls in the air above the stone, not gripping it"): a stone
    tipped toward lying flat is drawn squashed up and down; a grip on its rim goes with the rim."""
    if p.kind != "stone":
        return g
    return g[0], g[1] * (0.32 + 0.68 * q.get("tilt", 1.0))


def glo_bob(t):
    return 14 * K * math.sin(t * 1.3)


# ----------------------------------------------------------------------------------------------- arms and shoulders

WR = 46.0 * K
SPRINGS_ARM = 47.0 * K
DIGS_ARM = 95.0 * K
WHEELS_R = (WHEELS_UPPER + WHEELS_FORE) * K
REST_A = math.radians(12.0)


def wheels_shoulder(x, y, sx, t):
    return x + sx * 100 * K, y - 210 * K + 3 * math.sin(t * 2.2) * K + 10 * K


def twigs_shoulder(x, y, sx, t):
    sway = 4 * math.sin(t * 1.1) * K
    return x + sway + sx * 82 * K, y - 350 * K + sway * 0.3 + 10 * K


def twigs_rest(x, y, sx, t):
    sh = twigs_shoulder(x, y, sx, t)
    R = (TWIGS_UPPER + TWIGS_FORE) * K * 0.93
    return sh[0] + sx * math.sin(0.16) * R, sh[1] + math.cos(0.16) * R


def digs_shoulder(x, y, sx, t):
    return x + sx * 118 * K, y - 150 * K + 2 * K * math.sin(t * 2.6) + 4 * K


def springs_shoulder(x, y, sx, t, sq):
    s = sq + 0.06 * math.sin(t * 3.0)
    return x + sx * 100 * K, y - (170 - 46 * s) * K + 10 * K


def arm_angle(sh, p, sx):
    dx, dy = (p[0] - sh[0]) * sx, p[1] - sh[1]
    return math.atan2(dx, dy), math.hypot(dx, dy)


def arc(sh, p0, p1, u, sx, ext=None, phi=26.6):
    """A hand going from p0 to p1 round the shoulder (see raft_flat.arc: the arm straight where its elbow would turn
    over)."""
    lo = math.radians(phi) - math.pi
    a0, r0 = arm_angle(sh, p0, sx)
    a1, r1 = arm_angle(sh, p1, sx)
    a0 = lo + (a0 - lo) % (2 * math.pi)
    a1 = lo + (a1 - lo) % (2 * math.pi)
    e = smoothstep(min(max(u, 0.0), 1.0))
    a = a0 + (a1 - a0) * e
    r = r0 + (r1 - r0) * e
    if ext is not None:
        near = max(0.0, 1.0 - abs(a - math.radians(phi)) / math.radians(12.0))
        r += (ext - r) * max(smoothstep(min(1.0, 2.5 * math.sin(math.pi * e))), smoothstep(near))
    return sh[0] + sx * math.sin(a) * r, sh[1] + math.cos(a) * r


def wheels_rest_at(P, x, y, sx, t):
    sh = wheels_shoulder(x, y, sx, t)
    sw = roll_swing(P.paths["wheels"], t, WR) * sx
    a = REST_A + math.radians(6.0) * sw
    R = WHEELS_R * 0.9
    return sh[0] + sx * math.sin(a) * R, sh[1] + math.cos(a) * R


# ----------------------------------------------------------------------------------------------- voices

VOICE_DUR_S = 0.6
BUBBLE_R = 50.0


def voices(P):
    """The Keepers' little noises at their story beats, each moved to the nearest quiet moment (bubbles stay on
    their beat)."""
    lines = [(t0, t0 + _dur(tx)) for t0, tx in P.narration()]
    out = [(tb, kd, "idea", pic) for tb, kd, pic in P.bubbles]

    def free(tv):
        return not any(a - 0.7 <= tv <= b + 0.7 for a, b in lines) and all(abs(tv - o[0]) >= 1.2 for o in out)
    for tv, kd, mood, pic in sorted(P.voice_events, key=lambda e: e[0]):
        for d in [0.0] + [s_ * 0.3 * n for n in range(1, 9) for s_ in (1, -1)]:
            if free(tv + d):
                out.append((tv + d, kd, mood, pic))
                break
    return sorted(out, key=lambda e: e[0])


def talking(P, kd, t):
    m, look, hop = 0.0, 0.0, 0.0
    for tv, k, mood, _ in P.voices:
        if k != kd or not (tv - 0.4 <= t <= tv + VOICE_DUR_S + 0.6):
            continue
        u = (t - tv) / VOICE_DUR_S
        if 0 <= u <= 1:
            m = max(m, 0.7 * math.sin(math.pi * u) * (0.75 + 0.25 * math.sin(u * 18)))
            hop = max(hop, 7 * K * math.sin(math.pi * u))
        look = max(look, smoothstep((t - tv + 0.4) / 0.4) * (1 - smoothstep((t - tv - VOICE_DUR_S - 0.2) / 0.4)))
    return m, look, hop


# ----------------------------------------------------------------------------------------------- the Keepers

def keeper(kd, t):
    """(world x, screen y of its feet, monster attrs) of Keeper kd at time t, talking when it says something."""
    x, y, a = _keeper(kd, t)
    P = plan()
    a["legs_turn"] = P.turns[kd](t)
    a["turn"] = a["legs_turn"] * (1 - a.pop("face_us", 0.0))
    if P.voices:
        m, look, hop = talking(P, kd, t)
        if m > 0 or look > 0:
            a = dict(a, talk=m, attend=max(a.get("attend", 0.0), look), turn=a["turn"] * (1 - look))
            if kd in ("wheels", "springs", "lantern") and not a.get("_fixed"):
                y -= hop
    ch = chewing(P, kd, t)
    if ch > 0:
        a = dict(a, talk=max(a.get("talk", 0.0), ch))
    a.pop("_fixed", None)
    return x, y, a


def chewing(P, kd, t):
    """r40: how far kd's mouth is open eating at the feast: wide open just before a tossed piece lands in it (or a
    bite), shut on it, then munching."""
    m = 0.0
    for tc, te in getattr(P, "chews", {}).get(kd, ()):
        if tc - 0.45 <= t < tc:
            m = max(m, 0.85 * ease(t, tc - 0.45, tc - 0.15))
        elif tc <= t < te:
            m = max(m, 0.3 * abs(math.sin(math.pi * (t - tc) / 0.4)) * (1.0 - ease(t, te - 0.3, te)))
    return m


def _keeper(kd, t):
    P = plan()
    sh = P.shift(t)
    if kd in ("teeth", "digger", "tentacles"):
        g = P.gaits[kd]
        x = g.body_x(t)
        a = dict(feet=[(fx - sh, fy) for fx, fy in g.feet(t)], attend=0.25)
        if kd == "tentacles":
            a["feet"] = a["feet"][:6 - hans_lifted(P, t)]              # legs in use as arms are up
            a.update(float=0.2, **hans_mood("happy"))
            return x, GB + g.bob(t), a
        a["arm_swing"] = arm_swing(g, t)
        if kd == "teeth":
            a.update(hands=True, saws=False, blades=0.0, blades_l=0.0, knee_fwd=True, clamp_reach=True)
            hd, blade, grip = twigs_hand(P, t, x, GB)
            if hd is not None:
                a.update(arm_to={-1: (hd[0] - sh, hd[1])}, blades_l=blade, grip=grip)
            return x, GB, a
        ang = digs_paw(P, t, x, GB)
        if ang is not None:
            a["paw_ang"] = ang
        a.update(digs_bonk_face(P, t))
        return x, GB, a
    if kd == "springs":
        x, y, sq, hand = springs_state(P, t)
        a = dict(spring=sq, attend=0.25, arm_swing=0.0)
        if y != GB:
            a["_fixed"] = True
        if hand is not None:
            a["arm_to"] = {1: (hand[0] - sh, hand[1])}
        return x, y, a
    if kd == "wheels":
        x = P.paths[kd](t)
        a = dict(wheel_rot=x / WR, attend=0.25, arm_swing=roll_swing(P.paths[kd], t, WR), clamp_reach=True)
        hands = {sx: wheels_rest_at(P, x, GB, sx, t) for sx in (-1, 1)}
        a.update(arm_to={s_: (hx - sh, hy) for s_, (hx, hy) in hands.items()}, grip=0.3)
        return x, GB, a
    x = P.glo_x(t)
    return x, P.glo_y(t), dict(attend=0.25, lamp=1.0 + 0.9 * glo_flare(P, t))


def twigs_hand(P, t, x, y):
    """Twigs' left hand (world), his blade 0..1 and grip: reaching to each cut, sawing (strokes along the blade),
    nicking teeth, and back."""
    rest = twigs_rest(x, y, -1, t)
    f = getattr(P, "twigs_feast", None)                            # r42: his piece of bread, taken and eaten
    if f is not None and f["reach"][0] <= t < f["back"][1]:
        if t < f["lift"][0]:
            return lerp2(rest, f["take"], ease(t, *f["reach"])), 0.0, 0.25
        if t < f["back"][0]:
            u = ease(t, *f["lift"])                                # r42 (cc99 limb_stretch 0.82): the paw swings
            hx_, hy_ = lerp2(f["take"], f["mouth"], u)             # up in an arc out in front of him (70: 0.85 at 40)
            return (hx_ + 70.0 * math.sin(math.pi * u), hy_), 0.0, 0.25   # past his shoulder
        return lerp2(f["mouth"], rest, ease(t, *f["back"])), 0.0, 0.25
    for c in P.twigs_cuts:
        bl, sh_ = c.get("blade"), c.get("sheath", c["back"])
        t_a = bl[0] if bl else c["reach"][0]
        t_b = max(sh_[1], c["back"][1]) if sh_ else c["back"][1]
        if not (t_a <= t < t_b):
            continue
        out = ease(t, *bl) if bl else 1.0                          # r25: slid out slowly (or out already)
        if t < c["reach"][0]:
            return rest, out, 0.25                                 # (his hand still at rest)
        if t >= c["back"][1]:
            return rest, 1.0 - ease(t, *sh_), 0.25                 # sliding back in, his hand down
        hd = c["hand"]
        dx, dy = c["dir"]
        if t < c["c0"]:
            return lerp2(c.get("reach_from") or rest, hd, ease(t, *c["reach"])), out, 0.25
        if t < c["c1"]:
            s = 0.0
            for i, stv in enumerate(c["strokes"]):
                a, b = stv[0], stv[1]
                if a <= t < b:
                    u = _seg(t, a, b)
                    if c.get("kind") == "nick" or len(stv) > 2:                    # a short nick into the rim, then out
                        s = 7.0 * math.sin(math.pi * u)
                    elif c.get("kind") == "part":                  # sawing in the groove as the log turns
                        s = 6.0 + 6.0 * math.sin(2 * math.pi * u)
                    elif c.get("kind") == "dough":                 # r4: through the dough, long clear strokes
                        s = -5.0 - 5.0 * math.cos(2 * math.pi * u)   # r25: drawn up along the blade and
                        # pushed back down to the board, never past it (was 5 + 9 sin: the tip went through the
                        # sawhorse's top board; r5: 1 + 12 pulled the hand into his shoulder on the far cut)
                    elif c.get("kind") == "trim":                  # r13 ("nothing is cut"): long strokes, the
                        pz = _seg(t, c["c0"], c["c1"])             # blade going deeper through the stack each one
                        s = 2.0 + 26.0 * pz + 8.0 * math.sin(2 * math.pi * u)
                    elif c.get("kind") == "turn":                  # sawing the turning blank: full strokes
                        s = 10.0 + 15.0 * math.sin(2 * math.pi * u)     # (r3: the saw barely moved)
                        for a_, b_ in c.get("teeth", ()):          # r21 (part 1 must-fix "the teeth hang in the air
                            if a_ <= t < b_:                       # past the rim, the notch forms under the bar"):
                                s = NOTCH_S1 * math.sin(2 * math.pi * u)   # a notch is sawn with the whole
                                # blade over it (the hand moved there, below), short strokes along it
                    else:
                        s = 6.0 + 6.0 * math.sin(2 * math.pi * u) + (i - 1.5) * 1.0
            ox = oy = 0.0
            if c.get("kind") == "turn":
                for a_, b_ in c.get("teeth", ()):
                    if a_ <= t < b_:
                        w = min(1.0, 2.5 * math.sin(math.pi * _seg(t, a_, b_)))   # (eased in and back out:
                        ox += (NOTCH_HAND[0] - hd[0]) * w                         # nothing jumps)
                        oy += (NOTCH_HAND[1] - hd[1]) * w
            for g0, g1 in c.get("gaps", ()):                       # r19: the blade drawn out of the cut between
                if g0 <= t < g1:                                   # cuts, so the cut shows at the blade
                    w = ease(t, g0, g0 + TURN_OUT) * (1.0 - ease(t, g1 - TURN_IN, g1))
                    ox, oy = BLADE_OUT[0] * w, BLADE_OUT[1] * w
            return (hd[0] + dx * s + ox, hd[1] + dy * s + oy), 1.0, 0.25
        sh_out = (1.0 - ease(t, *sh_)) if sh_ else 1.0
        u = ease(t, *c["back"])
        return lerp2(hd, c.get("back_to") or rest, u), sh_out, 0.25
    return None, 0.0, 0.0


def digs_paw(P, t, x, y):
    """Digs' paw angles: digging a hole (a mole's strokes), pushing the soil back in and patting it, tapping a
    stone."""
    rest = {-1: math.radians(112.0), 1: math.radians(68.0)}
    for t0, t1, kind, d in P.digs_jobs:
        if not (t0 <= t < t1 + 0.6):
            continue
        if kind == "dig":
            h = P.holes[d]
            u = ease(t, h["t"][0] - 0.3, h["t"][0]) * (1 - ease(t, h["t"][1], h["t"][1] + 0.6))
            ang = h["dig"].angles(t)
            return {s: rest[s] + (ang[s] - rest[s]) * u for s in (-1, 1)}
        if kind in ("push", "pat"):                                # r18: his right paw on the pile's edge, shoving
            h = P.holes[d]                                         # it in; then patting the filled hole down
            u = ease(t, t0, t0 + 0.4) * (1 - ease(t, t1, t1 + 0.5))
            shx = digs_shoulder(x, y, 1, t)[0]
            if kind == "push":                                     # paw on the pile's back, shoving (25 degrees
                tgt = math.radians(25.0) + math.radians(5.0) * math.sin(t * 9.0)   # down: claws at the pile)
                if h.get("clay"):                                  # r26: lower as it goes forward into the pit
                    tgt += math.radians(CLAY_FILL_DA) * P.clay_shove(t)
            else:
                shy = digs_shoulder(x, y, 1, t)[1]                 # (monster.py: from the horizontal, y down)
                down = math.atan2(h.get("pat_y", GB - 48.0) - shy, h["x"] - PAT_X - shx)   # the paw on the earth by the post's foot
                lift = 1.0
                for a, b in h["pats"]:
                    if a <= t < b:
                        if t < a + 0.25:
                            lift = 1.0 - ease(t, a, a + 0.25)
                        elif t < a + 0.4:
                            lift = 0.0
                        else:
                            lift = ease(t, a + 0.4, b)
                tgt = down - math.radians(45.0) * lift              # raised out to the side between pats
            return {1: rest[1] + (tgt - rest[1]) * u, -1: rest[-1]}
        if kind == "dress":                                        # the right paw taps the stone's face
            dd = P.dress[d]
            s = P.props[f"millstone {d}"].at(t)[0]
            shp = digs_shoulder(x, y, 1, t)
            out = 0.0
            for j_, (a, b) in enumerate(dd["taps"]):
                if a <= t < b:
                    out = math.sin(math.pi * (EYE_TAPS if j_ == 0 else 1) * _seg(t, a, b)) ** 2   # (three at the eye)
            off = 0.0                                              # (r33: 1 = his paw down at his side)
            ex_, ey_ = s["x"], s["y"]                              # the eye (r32: its middle, where the hole is drawn;
            tgt = (ex_, ey_)                                       # it struck 12 px left of it)
            lift = 0.14 * (1 - out)                                # (off the eye between strikes)
            tp_ = dd["taps"]
            for k in range(1, len(tp_)):
                a, b = tp_[k]
                na = tp_[k + 1][0] if k + 1 < len(tp_) else None
                g0 = a - 0.3 if k == 1 else a + 0.15
                if g0 <= t < b + 0.1 or (na is None and b + 0.1 <= t < b + 0.3):
                    tgt = groove_tip(s, k - 1, ease(t, a + 0.15, b - 0.05))   # a groove: the claw tip is where the
                    lift = 0.0                                     # groove has got to (r8: exactly, not near it)
                    break
                if na is not None and b + 0.1 <= t < na - DRESS_BACK:   # r14: off the stone while Hans turns it
                    # r33 (round 32 part 2 must-fix "the claw stays at the hub while the grooves appear"): his paw
                    # drops to his side, clear of the stone's face, so the fresh groove is seen turning away
                    tgt = groove_tip(s, k - 1, 1.0)
                    lift, off = 0.0, ease(t, b + 0.1, b + 0.6)
                    break
                if na is not None and na - DRESS_BACK <= t < na + 0.15:   # and back up to the next groove's start
                    tgt = groove_tip(s, k, 0.0)
                    lift, off = 0.0, 1.0 - ease(t, na - DRESS_BACK, na + 0.15)
                    break
            ang = math.atan2(tgt[1] - shp[1], tgt[0] - shp[0]) - math.atan2(DIGS_TIP[1], DIGS_TIP[0]) - lift
            ang += (rest[1] - ang) * off
            u = ease(t, t0, t0 + 0.4) * (1 - ease(t, t1, t1 + 0.6))
            return {-1: rest[-1], 1: rest[1] + (ang - rest[1]) * u}
    return None


EYE_TAPS = 3                        # r6: Digs taps the eye open in three strokes (it popped in at once)


def eye_hits(a, b):
    """When his claw strikes the stone's eye: the middle of each of the EYE_TAPS strokes of the first tap job."""
    d = (b - a) / EYE_TAPS
    return [a + (j + 0.5) * d for j in range(EYE_TAPS)]


def eye_open(t, a, b):
    """How far the eye has been opened: a third more at each strike."""
    return sum(ease(t, h, h + 0.12) for h in eye_hits(a, b)) / EYE_TAPS


def reach_u(s, g, shp):
    """Where along groove g (u 0 eye .. 1 rim) Digs' claw tip can be, his arm being a fixed length: the point of the
    groove nearest his reach circle round the shoulder shp (r8: the hooked claw slides in the groove as he pulls)."""
    R = math.hypot(*DIGS_TIP)
    return min((abs(math.hypot(*(np.subtract(groove_tip(s, g, j / 40), shp))) - R), j / 40) for j in range(41))[1]


def groove_tip(s, g, u):
    """Where groove g of millstone pose s has been cut to (u 0 at the eye .. 1 at the rim), as draw_stone draws it."""
    (x0, y0), (x1, y1) = HW.groove_line(s["x"], s["y"], math.radians(s["ang"]), g)   # r26: along its straight line
    return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u


def draw_stone_dust(pg, P, t, sh):
    """Grit flicking off the claw tip as each groove is cut."""
    for dd in getattr(P, "dress", ()):
        s = P.props[f"millstone {dd['stone']}"].at(t)[0]
        a0, b0 = dd["taps"][0]
        for h in eye_hits(a0, b0):                                 # chips off the eye at each strike (r6)
            for j in range(5):
                v = t - h - 0.02 * j
                if 0 <= v < 0.45:
                    x, y = s["x"], s["y"]                          # (r32: at the eye's middle, under the claw)
                    pg.flat(oval(x - sh + (-34 + 17 * j) * v, y - 60 * v + 0.5 * 700 * v * v, 2.2, 2.0),
                            (150, 142, 132), 1.0 - v / 0.45)
        for k, (a, b) in enumerate(dd["taps"]):
            if k and a + 0.15 <= t < b + 0.5:
                # r40 (round 40 part 2 must-fix "the claw only dabs at the hub, the grooves appear by themselves"):
                # a steady spray of pale grit off the claw tip all the way out along the groove, flicking right and
                # up, clear of his paw (it flew left, under the paw, 2 px and stone-grey: unseen)
                for j in range(16):
                    t0 = a + 0.15 + (b - a - 0.2) * j / 16
                    v = t - t0
                    if 0 <= v < 0.5:
                        x, y = groove_tip(s, k - 1, ease(t0, a + 0.15, b - 0.05))
                        vx = 45.0 + 30.0 * ((j * 7) % 5) / 4.0
                        vy = -70.0 - 25.0 * ((j * 3) % 4) / 3.0
                        pg.flat(oval(x - sh + vx * v, y + vy * v + 0.5 * 700 * v * v, 3.2 - 0.6 * (j % 2), 2.8),
                                (232, 226, 214), 1.0 - v / 0.5)


def glo_flare(P, t):
    u = 0.0
    for a, b, _ in P.flares:
        u = max(u, ease(t, a - 0.3, a + 0.2) * (1 - ease(t, b - 0.2, b + 0.4)))
    return u


# ----------------------------------------------------------------------------------------------- Springs

GLO_HOP_CLEAR = 230.0               # r20: how far Glo rises when Springs jumps over Digs under him
APEX = 330.0                        # a jump over Digs (his hat is 216 px up)
LEAP_APEX = 250.0                   # r15: his leap over Digs and the clay pit (in the close shot: his head stays in it)


def springs_state(P, t):
    """(x, feet y, squash, right hand world or None): hopping about, jumping over Digs, hanging from the branch,
    pulling the brake peg."""
    for t0, t1, kind, s in P.springs_special:
        if kind == "jump" and t0 <= t < t1:
            x0, x1 = s
            u = (t - t0) / (t1 - t0)
            e = smoothstep(u)
            return x0 + (x1 - x0) * e, GB - APEX * math.sin(math.pi * e) ** 0.6, -0.25 * math.sin(math.pi * u), None
        if kind == "shake" and t0 <= t < t1:
            r = springs_shake(P, s, t)
            w = _seg(t, t0, t0 + 0.4)                                # (cc79: he was still mid-hop from his walk when
            if w < 1.0:                                            # the shake took over, a 25 px drop: blend from it)
                hx, hy, hs = P.hopper.state(t)
                e = smoothstep(w)
                r = (hx + (r[0] - hx) * e, hy + (r[1] - hy) * e, hs + (r[2] - hs) * e, r[3])
            return r
        if kind == "leap" and t0 <= t < t1:                     # r15: over Digs and his pit, onto / off the heap
            u = (t - t0) / (t1 - t0)
            e = smoothstep(u)
            y0 = clay_top(P, t0) if s["on0"] else GB
            y1 = clay_top(P, t1) if s["on1"] else GB
            return (s["x0"] + (s["x1"] - s["x0"]) * e, y0 + (y1 - y0) * e - LEAP_APEX * math.sin(math.pi * e) ** 0.6,
                    -0.25 * math.sin(math.pi * u), None)
        if kind == "stomp" and t0 - s.get("pre", 0.5) <= t < t1 + s.get("post", 0.5):
            r = springs_stomp(P, s, t)
            w = 1.0 if s.get("held") else _seg(t, t0 - 0.5, t0 - 0.2)                        # r6: he was still mid-hop when the stomp took
            if w < 1.0:                                            # over (a 22 px drop): blend from his hop
                hx, hy, hs = P.hopper.state(t)
                e = smoothstep(w)
                r = (hx + (r[0] - hx) * e, hy + (r[1] - hy) * e, hs + (r[2] - hs) * e, r[3])
            return r
    x, yr, sq = P.hopper.state(t)
    yr -= peg_hop(P, t)                                            # r13: a little spring hop draws the peg right up
                                                                   # out of its post (his arm alone lifted it 20 px)
    for t0, t1, kind, s in P.springs_special:                      # the crouch into and out of a big jump
        if kind == "leap":                                         # (r15: only where it takes off / lands on the path)
            if not s["on0"]:
                u = _seg(t, t0 - 0.35, t0)
                if 0 < u < 1:
                    sq = max(sq, 0.5 * math.sin(math.pi * u))
            if not s["on1"]:
                u = _seg(t, t1, t1 + 0.35)
                if 0 < u < 1:
                    sq = max(sq, 0.45 * math.sin(math.pi * u))
            w = min(_seg(t, t1, t1 + 0.5) if (t >= t1 and not s["on1"]) else 1.0,
                    1.0 - _seg(t, t0 - 0.5, t0) if (t < t0 and not s["on0"]) else 1.0)
            if w < 1.0:
                yr = GB + (yr - GB) * smoothstep(w)
        if kind == "jump":
            u = _seg(t, t0 - 0.35, t0)
            if 0 < u < 1:
                sq = max(sq, 0.5 * math.sin(math.pi * u))
            u = _seg(t, t1, t1 + 0.35)
            if 0 < u < 1:
                sq = max(sq, 0.45 * math.sin(math.pi * u))
            w = min(_seg(t, t1, t1 + 0.5) if t >= t1 else 1.0,    # r9: a jump lands (and takes off) on the
                    1.0 - _seg(t, t0 - 0.5, t0) if t < t0 else 1.0)  # ground; the hopper's own hop eases in
            if w < 1.0:
                yr = GB + (yr - GB) * smoothstep(w)
    return x, yr, sq, springs_peg_hand(P, t, x, yr, sq)


def clay_top(P, t):
    """The soft clay heap's top (screen y) right now, as draw_holes draws it."""
    h = P.holes["clay"]
    cx, hh = h["spoil"].heap(1, t)
    h0 = h["spoil"].h0
    got, tot = hh - h0, h["spoil"].heap(1, 1e9)[1] - h0              # (as draw_holes: r7)
    hh = (got + h0 * (got / tot if tot > 0 else 1.0)) * P.clay_left(1, t) * CLAY_HH
    if hasattr(P, "soft"):
        hh *= 1.0 - 0.35 * ease(t, *P.soft)
    return GB - 34 - hh


def springs_stomp(P, s, t):
    """Springs hops up onto the clay heap and bounces on it until it's soft and flat, then hops off (part 2 review:
    he bounced beside it, on the path)."""
    b = s["b"]
    on = 1.0 if s.get("held") else ease(t, b[0][0] - 0.45, b[0][0]) * (1 - ease(t, b[-1][1], b[-1][1] + 0.45))
    y = GB + (clay_top(P, t) - GB) * on
    lift, sq = 0.0, 0.0
    for a, b_ in b:
        if a <= t < b_:
            u = _seg(t, a, b_)
            lift = 34.0 * math.sin(math.pi * u)
            sq = 0.4 * (1.0 - math.sin(math.pi * u)) ** 2
    return s["x"], y - lift * on, sq * on, None


def springs_shake(P, s, t):
    """Springs hops up onto the oak's low branch and bounces on it (it bends under him), then hops down (part 2
    review: hanging under it, he read as standing at the brook's edge, not "on the branch")."""
    x = SHAKE_X
    hang = GB - (P.branch_y(x, t) - 10.0)                             # his feet on the branch's top
    x0 = s.get("hop_x0", x)
    if t < s["hop"][0]:
        u = _seg(t, s["hop"][0] - 0.4, s["hop"][0])
        return x0, GB, 0.5 * math.sin(math.pi * u), None
    if t < s["hop"][1]:                                            # r29: one arc from the ground (over Digs) up
        u = _seg(t, *s["hop"])                                     # onto the branch, landing on it
        u0 = 0.1                                                   # (cc76: the push-off and the touch-down each take
        if u < u0:                                                 # ~0.12 s, not one frame: storycheck thing_jumps)
            u = u * u / (2.0 * u0)
        elif u > 1.0 - u0:
            u = 1.0 - u0 - (1.0 - u) ** 2 / (2.0 * u0)
        else:
            u = u - u0 / 2.0
        u /= 1.0 - u0
        h = hang * u + 4.0 * BRANCH_HOP_OVER * u * (1.0 - u)
        sq = -0.3 * math.sin(math.pi * min(1.0, u / 0.6)) + 0.4 * math.sin(math.pi * max(0.0, (u - 0.85) / 0.15))
        return x0 + (x - x0) * u, GB - h, sq, None
    if t < s["let_go"]:                                            # bouncing on it: squash as it bends
        sq = 0.0
        for a, b in s["bounces"]:
            if a <= t < b:
                sq = 0.45 * math.sin(math.pi * _seg(t, a, b))
        return x, GB - hang, sq, None
    fall = 1.3 * math.sqrt(2 * hang / 1500.0)
    u = _seg(t, s["let_go"], s["let_go"] + fall)
    if u < 1:                                                       # down, the spring taking up the landing
        return x, GB - hang * (1 - smoothstep(u)), -0.4 * (1 - u) + 0.45 * math.sin(math.pi * u) ** 4, None
    u = _seg(t, s["let_go"] + fall, s["let_go"] + fall + 0.5)
    return x, GB, 0.5 * math.sin(math.pi * u), None


def peg_hop(P, t):
    """How high Springs is off the ground in the little hop that pulls the brake peg (r13)."""
    if not hasattr(P, "pin"):
        return 0.0
    return PEG_HOP * ease(t, P.pin[0] + 0.3, P.pin[1]) * (1.0 - ease(t, P.pin[1] + 0.35, P.pin[1] + 0.75))


def springs_peg_hand(P, t, x, y, sq):
    """Springs' right hand on the brake peg: he takes it, pulls it up out of its post, and drops it on the path."""
    if not hasattr(P, "pin") or not (P.pin[0] - 0.4 <= t < P.pin[1] + 1.2):
        return None
    sh = springs_shoulder(x, y, 1, t, sq)
    tg = (PEG[0], PEG[1] - PEG_KNOB - peg_hop(P, t))               # (r13: his hand on its knob, up with his hop)
    if t >= P.pin[1]:
        tg = lerp2(tg, (sh[0] + 22.0, sh[1] + 20.0), ease(t, P.pin[1], P.pin[1] + 0.6))
    d = math.hypot(tg[0] - sh[0], tg[1] - sh[1]) or 1.0
    return sh[0] + (tg[0] - sh[0]) / d * SPRINGS_ARM, sh[1] + (tg[1] - sh[1]) / d * SPRINGS_ARM


def peg_pos(P, t):
    """The brake peg (world): in its post, in Springs' hand, dropped on the path."""
    if t < P.pin[0] + 0.3:
        return PEG, "post"
    td = P.pin[1] + PEG_DROP
    tq = min(t, td - 1e-3)

    def at(tt):                                                    # the peg where his hand holds it by the knob
        x, y, sq, hd = springs_state(P, tt)
        if hd is None:
            hd = (x + 60 * K, y - 120 * K)
        return hd[0], hd[1] + PEG_KNOB
    h0 = at(P.pin[0] + 0.3)                                        # r13: any gap at the grip is closed over the
    f = 1.0 - ease(tq, P.pin[0] + 0.3, P.pin[0] + 0.7)             # first moment of the pull (it jumped 16 px down
    p = at(tq)                                                     # into his hand, and never rose)
    p = (p[0] + (PEG[0] - h0[0]) * f, p[1] + (PEG[1] - h0[1]) * f)
    if t < td:
        return p, "hand"
    u = t - td
    y = min(GB - 12, p[1] + 0.5 * 1500 * u * u)                   # (r13: it tips over as it falls and lies on the
    return (p[0], y), ("falling" if y < GB - 12 else "ground")     # path: it stood up on end before)


# ----------------------------------------------------------------------------------------------- Hans' tentacles

def hans_k(P, t):
    """How many of Hans' working tentacles are out at time t."""
    return sum(1 for jobs in P.hans.values() if any(t0 <= t < t1 for t0, t1, _, _ in jobs))


def hans_lifted(P, t):
    """How many of his six legs are up being used as arms (owner 2026-11-06: Hans has 8 tentacles in all; 6 legs
    down leaves 2 arms, a 3rd or 4th arm is a leg that lifts off the ground). The outermost right legs go first."""
    return min(2, max(0, hans_k(P, t) - 2))


def hans_targets(P, t):
    """[(slot, world target, grip 0..1, leg)] for every working tentacle now. leg: the leg it lifts from (or goes back
    down to) while it reaches out (or draws back), when it's a 3rd or 4th arm; None for his two own arms."""
    out = []
    for slot, jobs in P.hans.items():
        best = None
        for t0, t1, fn, (a, b, c, d) in jobs:
            if t0 <= t < t1:
                leg = None
                if t < b:
                    g, tg = (ease(t, a, b) if b > a else 1.0), fn(b)
                    n0, n1 = hans_lifted(P, t0 - 1e-4), hans_lifted(P, t0 + 1e-4)
                    leg = 6 - n1 if n1 > n0 else None
                elif t < c:
                    g, tg = 1.0, fn(t)
                else:
                    g, tg = (1.0 - ease(t, c, d) if d > c else 0.0), fn(c)
                    n0, n1 = hans_lifted(P, t1 - 1e-4), hans_lifted(P, t1 + 1e-4)
                    leg = 6 - n0 if n0 > n1 else None
                if best is None or g > best[2] + 1e-9:
                    best = (slot, tg, g, leg)
        if best is not None:
            out.append(best)
    return out


def hans_slot_behind(P, slot, t):
    """r19 (part 1 must-fixes: the post behind his head with the tentacle holding it across his face; the top beam
    up through his face): is what tentacle `slot` works on now drawn behind Hans? Then the tentacle is drawn behind
    his body too (one depth for a thing and the tentacle on it). Judged while it holds it (reaching in and letting
    go take the depth of the hold)."""
    best = None
    for t0, t1, fn, (a, b, c, d) in P.hans.get(slot, ()):
        if t0 <= t < t1:
            g = ease(t, a, b) if t < b and b > a else (1.0 if t < c else (1.0 - ease(t, c, d) if d > c else 0.0))
            if best is None or g > best[0] + 1e-9:
                best = (g, b, c, (t0, t1, fn, (a, b, c, d)))
    if best is None:
        return False
    if hold_high(P, slot, best[3]):
        return True
    th = min(max(t, best[1] + 1e-3), max(best[1] + 1e-3, best[2] - 1e-3))
    for p in P.props.values():
        if not p.alive(th):
            continue
        q, hd, _ = p.at(th)
        if hd == ("Hans", slot):
            return p.name != "low beam" and not hans_front(P, p, hd, q, th) and zof(p, th) < 20
    return False


MOUTH_Y = GB - 305 * K + 46 * K    # r19: his mouth's height (world y); a hold reaching above it is drawn behind him


def hold_high(P, slot, job):
    """r19 (part 1 must-fix "the tentacle comes out of his mouth", up across his face): does this hold reach higher
    than his mouth while it holds? Then the whole hold is drawn behind his body (it comes up past his head from
    behind), never switching depth half-way."""
    cache = P.__dict__.setdefault("_high", {})
    key = (slot, job[3])
    if key not in cache:
        t0, t1, fn, (a, b, c, d) = job
        lo, hi = b, max(b, min(c, b + 12.0))
        cache[key] = any(fn(lo + (hi - lo) * k / 8.0)[1] < MOUTH_Y for k in range(9))
    return cache[key]


def hans_extra(t, sh, which=None, only=None):
    """Hans' working tentacles: all of them (which=None, the checks), or only those behind his body ("behind") or
    in front of it ("front")."""
    P = plan()

    def draw(cv, m):
        if which != "front" or not hasattr(m, "work"):
            m.work = []
        g = P.gaits["tentacles"]
        for slot, (tx, ty), grip, leg in hans_targets(P, t):
            if grip <= 0.001 or (only is not None and slot not in only):
                continue
            if which in ("front", "behind") and hans_slot_behind(P, slot, t) != (which == "behind"):
                continue
            if leg is not None:                                    # a leg lifting off the ground to become it
                fx, fy, _, _ = g.foot(leg, t)
                root_rest = (fx - sh, fy)
            else:
                root_rest = (m.x + slot * 40 * K, m.y - 305 * K + 150 * K)
            gx, gy = lerp2(root_rest, (tx - sh, ty), grip)
            rt = None
            if leg is None and slot in (-1, 1) and hasattr(P, "smooth") and P.smooth[0] - 1.0 <= t <= P.smooth[1] + 1.0:
                hy = m.y - 305 * K + getattr(m, "alive", 1.0) * 5 * math.sin(t * 1.4) * K * getattr(m, "float", 1.0)
                rt = (m.x + (1 if gx >= m.x else -1) * (50 + 12 * abs(slot)) * K, hy + SMOOTH_ROOT * K)   # r33: low
            elif which in ("front", "over") and leg is None:       # r19: a tentacle working low in front of him
                hy = m.y - 305 * K + getattr(m, "alive", 1.0) * 5 * math.sin(t * 1.4) * K * getattr(m, "float", 1.0)
                sd = 1 if gx >= m.x else -1                        # comes from his body's lower edge, under his
                rt = (m.x + sd * (50 + 12 * abs(slot)) * K, hy + 100 * K)   # mouth (never out of its corner)
            clip = low_beam_posts(P, slot, t, sh)                  # r28: on the low beam, behind the posts too
            if not hasattr(getattr(cv, "c", None), "clipPath"):     # (the checks' stub canvas)
                clip = None
            if clip is not None:
                cv.c.save()
                cv.c.clipPath(clip, skia.ClipOp.kDifference, True)
            root, L = m.work_tentacle(cv, gx, gy, t, slot=slot, grip=max(grip, 0.3), root=rt)
            if clip is not None:
                cv.c.restore()
            m.work.append((slot, root, (gx, gy), L))
    return draw


def low_beam_posts(P, slot, t, sh):
    """r28 (round 27 part 1 must-fix: the low beam read as in front of the right post while it slid in, then behind
    it): the beam goes in behind the posts, so the tentacle gripping it does too where it crosses a post: the posts'
    outlines (to clip the tentacle by), while tentacle `slot` reaches for, holds or lets go of the low beam."""
    lb = P.props.get("low beam")
    if lb is None:
        return None
    if not any(lb.alive(t + dt) and lb.at(t + dt)[1] == ("Hans", slot) for dt in (0.0, -1.2, 1.2)):
        return None
    out = None
    for n in ("post R", "post L"):
        p = P.props.get(n)
        if p is None or not p.alive(t) or zof(p, t) <= zof(lb, t):
            continue
        q = p.at(t)[0]
        a, L = math.radians(q["ang"]), q["L"] / 2
        w = q.get("w", 12.0) + 2.0
        path = HW.tube([(q["x"] - math.cos(a) * L - sh, q["y"] - math.sin(a) * L),
                        (q["x"] + math.cos(a) * L - sh, q["y"] + math.sin(a) * L)], w, w)
        out = path if out is None else skia.Op(out, path, skia.PathOp.kUnion_PathOp)
    return out


# ----------------------------------------------------------------------------------------------- drawing props

NOTCH_D = 32.0                      # r34: 32 with BLANK 84 (root 52 as before). r33: 36 with BLANK 88 (root 52 as before). Was: NOTCH_D = 28.0                      # (r27: 24 -> 50 with GEAR_R 86, the axles 140 apart) a notch's depth (deep enough for the other gear's tooth to sit in it; r14: 17 left no gap)
NOTCH_TW, NOTCH_BW = 44.0, 18.0     # r33: 44 at the rim with the longer teeth (straight-sided, not dovetailed). Was 38/18     # (r29: 40/22 -> 38/18 with GEAR_INSET) r28: a notch's width at the rim and at its floor (px; sloped flanks)
GLO_CLEAR_X = 110.0                 # r29: Glo's half width and a margin, clear of a beam's end
GEAR_INSET = 3.0                    # r29: the gear's outline eased in (px), a visible gap where the teeth mesh
NOTCH_W = 0.42                      # (r27: 0.36 -> 0.42 with GEAR_R 86: 0 px overlap through the demo and the mill) a notch's half width, in pitches (r4: wider than a tooth, so they mesh clear; r14: 0.28
                                    # left the teeth touching at the nip, read as overlapping - now a 6 px gap all round)


def notch_own(m):
    """Notch m's own angle on the blank (deg): r28 (part 1 must-fix "the gears are 8 long thin spikes, a ship's
    wheel"): at the octagon's corners, half a pitch round from its flats, so the teeth are the flat sides."""
    return (360.0 / TEETH * (m + 0.5)) % 360.0


def notch_depth(t, a, b, n=3):
    """r42 (round 42 part 1 must-fix "a whole notch appears in under half a second"): a notch deepens stroke by
    stroke - a third deeper on each push of the blade (the first 60% of each of its n strokes), still between."""
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a) * n
    q = int(u)
    return min(0.999, (q + smoothstep(min(1.0, (u - q) / 0.6))) / n)   # whole only once the cut is over


def tooth_step(cuts, j):
    """How far the blank is turned before cut j: a quarter turn to each corner, half a pitch more to the first
    notch (at a corner of the octagon, r28), then a pitch to each next notch."""
    if j == 0:
        return 0.0
    if cuts[j][0] == "corner":
        return 90.0
    return 360.0 / TEETH * (1.5 if cuts[j - 1][0] == "corner" else 1.0)


def gear_shape(X, y, ang, r, corners, cut, face=1.0, teeth=TEETH):
    """A gear blank: a square board (half side r) with `corners` of its corners cut off (corner k at its own angle
    45 + 90k), then notch m cut `cut - m` of the way (0..1) in. r28 (part 1 must-fix "8 long thin spikes, a ship's
    wheel"): each notch is a straight-sided trapezoid sawn in at a corner of the octagon (`notch_own`), NOTCH_TW wide
    at the rim and NOTCH_BW at its floor, NOTCH_D deep, so the teeth are the octagon's flat sides: short, blocky,
    wide at the root. The rim is never rounded off. Turned by ang (deg)."""
    pts = []
    a0 = math.radians(ang)
    n = 144
    cc = [math.radians(45.0 + 90.0 * k) for k in range(4)]
    for i in range(n):
        a = 2 * math.pi * i / n                                    # in the blank's own frame
        rr = r / max(abs(math.cos(a)), abs(math.sin(a)))
        for k in range(4):
            if corners >= k + 1:
                d = math.cos(a - cc[k])
                if d > 0.05:
                    rr = min(rr, r / d)                    # r33: a regular octagon (1.02 made the flats
                    # alternate 78/69 px: uneven teeth, round 32 part 1 must-fix)
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    for m in range(teeth):
        u = min(max(cut - m, 0.0), 1.0)
        if u <= 0:
            continue
        am = math.radians(notch_own(m))
        ca, sa = math.cos(am), math.sin(am)
        r_out, r_in = r * 1.2, r - NOTCH_D * u
        wb = NOTCH_TW / 2 + (NOTCH_BW - NOTCH_TW) / 2 * u        # (the floor narrows as the saw goes deeper)
        wo = NOTCH_TW / 2 + (NOTCH_TW - NOTCH_BW) / 2 * (r_out - r) / NOTCH_D   # (the flanks carried on past the rim)
        quad = [(r_out, -wo), (r_out, wo), (r_in, wb), (r_in, -wb)]
        nq = skia.Path()
        for j, (rad, w) in enumerate(quad):
            xq, yq = rad * ca - w * sa, rad * sa + w * ca
            (nq.moveTo if j == 0 else nq.lineTo)(xq, yq)
        nq.close()
        p = skia.Op(p, nq, skia.PathOp.kDifference_PathOp)
    if GEAR_INSET > 0.0:                                           # r29 (round 28 part 1 must-fix "tooth sits on a
        rim = skia.Path()                                          # tooth"): the outline eased in all round, so a
        skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=2 * GEAR_INSET,   # tooth in the other gear's notch
                   StrokeJoin=skia.Paint.kMiter_Join).getFillPath(p, rim)       # shows a clear gap round it
        p = skia.Op(p, rim, skia.PathOp.kDifference_PathOp)
    mtx = skia.Matrix()
    mtx.setRotate(math.degrees(a0))
    mtx.postScale(face, 1.0)
    mtx.postTranslate(X, y)
    return p.makeTransform(mtx) if hasattr(p, "makeTransform") else _xform(p, mtx)


def _xform(p, mtx):
    q = skia.Path(p)
    q.transform(mtx)
    return q


def corner_kerf(P, p, q, t):
    """While a corner is being sawn off: the cut so far, from the blank's edge across the corner (screen points)."""
    if not p.name.startswith("gear ") or not hasattr(P, "discs"):
        return None
    i = int(p.name.split()[1])
    if i >= len(P.discs):
        return None
    k_c = 0
    for kind, (a, b) in P.discs[i]["cuts"]:
        if kind != "corner":
            break
        if a <= t < b:
            u = (t - a) / (b - a)
            r = q["r"]
            th = math.radians(90.0 * k_c)                           # corner k_c (its own angle 45 + 90k)
            ends = []
            for ex, ey in ((r, 0.44 * r), (0.44 * r, r)):
                xr, yr = ex * math.cos(th) - ey * math.sin(th), ex * math.sin(th) + ey * math.cos(th)
                a0 = math.radians(q["ang"])
                ends.append((q["x"] - P.shift(t) + xr * math.cos(a0) - yr * math.sin(a0),
                             q["y"] + xr * math.sin(a0) + yr * math.cos(a0)))
            (x0, y0), (x1, y1) = ends
            return (x0, y0), (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u)
        k_c += 1
    return None


def draw_slice_pulley(pg, x, y, ang, sh, r=None):
    """r37 (round 36 part 2 must-fix "the pale ringed slice turns into a dark spoked wheel"): the pulley is the very
    slice Twigs sawed off the thin pole, as it was cut: pale end grain, growth rings, the bark round its rim; a crack
    from the middle shows it turning."""
    r = HW.PULLEY_R if r is None else r
    X = x - sh
    pg.shape(oval(X, y, r, r), HW.WOOD, 0.1)                      # the bark rim
    pg.flat(oval(X, y, r - 4, r - 4), HW.WOOD_END)
    for f_ in (0.3, 0.55, 0.78):
        rr_ = (r - 4) * f_
        pg.stroke(skia.Path().addOval(skia.Rect(X - rr_, y - rr_, X + rr_, y + rr_)), HW.WOOD_RING, 1.3, 0.7)
    a = math.radians(ang)
    pg.stroke(skia.Path().moveTo(X + math.cos(a) * 3, y + math.sin(a) * 3)
              .lineTo(X + math.cos(a + 0.12) * (r - 6), y + math.sin(a + 0.12) * (r - 6)), tone(HW.WOOD_RING, -0.25), 1.8)
    pg.flat(oval(X + math.cos(a + 2.4) * (r - 11), y + math.sin(a + 2.4) * (r - 11), 2.6, 2.0), tone(HW.WOOD_RING, -0.1))


def draw_axle_end(pg, x, y, sh, ang):
    """The round end of a wooden axle seen end on (it sticks out of the low beam; a millstone's eye fits on it), with
    a cross slot that turns with it."""
    X = x - sh
    pg.shape(oval(X, y, 9.0, 9.0), HW.WOOD_END, 0.12)
    pg.stroke(skia.Path().addOval(skia.Rect(X - 5.5, y - 5.5, X + 5.5, y + 5.5)), tone(HW.WOOD_END, -0.25), 1.2, 0.6)
    a = math.radians(ang)
    pg.stroke(skia.Path().moveTo(X - 7 * math.cos(a), y - 7 * math.sin(a)).lineTo(X + 7 * math.cos(a), y + 7 * math.sin(a)),
              tone(HW.WOOD, -0.35), 2.0, 0.85)


STONE_THICK = 44.0                  # r17 (part 1 must-fix "the millstones read as plates on a rail"): a stone this thick
GEAR_GAP = 0.0                      # r33 (round 32 part 2 must-fix "the gears aren't concentric with the stones"): right
                                    # behind the stone's back face, its teeth showing all round it. Was: GEAR_GAP = 200.0                    # (r31: 200, round 30 parts 1+2 must-fixes "the gears aren't on the axles, hidden
                                    # behind the stones": their hubs and the mesh now show clear of the stones' rims) (r30: 6 -> 106, round 29 part 2: gears up-right of the stones, mesh above the nip) r29: how far behind a mounted stone's back face its gear sits on the axle
GEAR_SLIDE_T = 1.8                  # r30: a gear slid back along its axle from the peg end (s; r31: 1.8, further back)
AXLE_COL = tone(HW.WOOD, -0.38)     # r32: the stones' axles, a darker wood than the gears so the shaft reads
HOPPER_TRIM = 30.0                  # r33: the hopper boards' offcut (was 18: too small to see drop)
HOPPER_DEPTH = 64.0                 # r37: how wide the hopper boards are (their top face, going back)
ROOF_DEPTH = 90.0                   # r40: and the roof boards (a roof that would keep the rain off)
HOPPER_TONE = 0.22                  # r33 (round 32 part 2 must-fix "Twigs saws air"): the hopper boards are fresh pale wood, so
                                    # they read on the darker rack bar and the log bench behind it while he trims them


def gear_back():
    """r29: where a mounted gear sits from its axle's end (the stone's face). r43 (round 43 part 1 must-fix "the
    axle pin sits 20-30 px off each gear's centre, an angled slot"): straight behind it, concentric with its stone,
    the axle seen end on at the hub (was back along the axle in the oblique view, DV * (STONE_THICK + GEAR_GAP)).
    r45 (round 44 part 2 must-fix "the gears are hidden behind the stones, a few teeth lower left only; the stones'
    thickness shows upper right, so a gear behind them should stick out there"): back against the stone's back face
    again (DV * (STONE_THICK + GEAR_GAP)), its teeth showing evenly along the top and right of each stone and meeting
    in the gap above the nip; the r43 pin stays fixed: on a bare peg the axle is seen end on at the gear's own hub
    (no oblique shaft), and the low beam's axle ends sit at the hubs too."""
    return DV[0] * (STONE_THICK + GEAR_GAP), DV[1] * (STONE_THICK + GEAR_GAP)


def draw_axle_shaft(pg, x, y, sh):
    """r29: the axle's round shaft running back (DV) from its end at (x, y) to the gear on it."""
    bx, by = gear_back()
    d = math.hypot(bx, by)
    if d >= 0.0:                                                   # r43/r45: seen end on, no shaft shows
        return
    nx, ny = -by / d * 9.0, bx / d * 9.0
    X = x - sh
    band = skia.Path().moveTo(X + nx, y + ny).lineTo(X + nx + bx, y + ny + by).lineTo(X - nx + bx, y - ny + by)         .lineTo(X - nx, y - ny).close()
    pg.shape(band, AXLE_COL, 0.12)                                 # (r32: the same dark rod as on the gear)
    for e_ in (1.0, -1.0):
        pg.stroke(skia.Path().moveTo(X + e_ * nx, y + e_ * ny).lineTo(X + e_ * nx + bx, y + e_ * ny + by),
                  tone(HW.WOOD, -0.6), 1.6, 0.9)


def draw_stone_side(pg, r=None):
    """The millstone's thickness seen in the oblique view (DV): its back rim and the band joining it to the face, at
    (0, 0) in the current transform (r17: a heavy round stone, its rolling side showing at the nip)."""
    r = HW.STONE_R if r is None else r
    bx, by = DV[0] * STONE_THICK, DV[1] * STONE_THICK
    d = math.hypot(bx, by)
    nx, ny = -by / d * r, bx / d * r                               # the band's two edges, square to the depth step
    band = skia.Path()
    band.addOval(skia.Rect(bx - r, by - r, bx + r, by + r))
    quad = skia.Path().moveTo(nx, ny).lineTo(nx + bx, ny + by).lineTo(-nx + bx, -ny + by).lineTo(-nx, -ny).close()
    band = skia.Op(band, quad, skia.PathOp.kUnion_PathOp) or band
    pg.shape(band, tone(HW.MILLSTONE, -0.22), 0.12)


def draw_stone_lap(pg, q, sh, t):
    """r34: a millstone lying in the shallows: the water laps round its lower rim (a ripple of water over its near
    edge and a pale line where it meets the stone), fading as he lifts it out (wet 1 -> 0)."""
    w = q.get("wet", 0.0)
    if w <= 0.01:
        return
    X, y = q["x"] - sh, q["y"]
    r = HW.STONE_R
    hh = r * (0.32 + 0.68 * q.get("tilt", 1.0))
    yl = q.get("wl", y + hh * 0.45)                               # the waterline across its near half (r35: the
    if y + hh + 2.0 < yl:                                          # water's own surface: it stays as he lifts it)
        return
    xs = np.linspace(-r - 10.0, r + 10.0, 25)
    top = [(X + x, yl + hh * 0.55 * (1.0 - min(1.0, (x / r) ** 2)) ** 0.5 * 0.35 + 1.2 * math.sin(x * 0.12 + t * 2.6))
           for x in xs]
    band = smooth(top + [(X + x, y + hh + 10.0 + 4.0 * (1.0 - (x / (r + 10)) ** 2)) for x in xs[::-1]])
    pg.flat(band, mix(HW.WATER_C, HW.WATER_DEEP, 0.3), 0.88 * w)
    p_ = skia.Path()
    for i, (x_, y_) in enumerate(top):
        (p_.moveTo if i == 0 else p_.lineTo)(x_, y_)
    pg.stroke(p_, HW.FOAM, 2.0, 0.75 * w)


def draw_prop(pg, P, p, q, sh, t):
    k = p.kind
    X = q["x"] - sh
    if k == "pole":
        a = math.radians(q["ang"])
        L = q["L"] / 2
        HW.draw_pole(pg, q["x"] - math.cos(a) * L, q["y"] - math.sin(a) * L, q["x"] + math.cos(a) * L,
                     q["y"] + math.sin(a) * L, sh, q.get("w", 12.0))
        on_ = getattr(P, "gear_on", {})
        if p.name == "low beam" and "gear 1" in on_ and t >= on_["gear 1"][0]:
            # r38 (round 37 part 1 must-fix "the gears' contact is hidden behind the beam"): the beam just behind the
            # two meshed gears is in their shade, so the gap round the tooth in the other gear's notch reads dark
            (gx0, _), (gx1, _) = HW.STONES
            sx0, sx1 = gx0 + 30.0 - sh, gx1 - 30.0 - sh
            pg.flat(rrect(sx0, q["y"] - 9.0, sx1, q["y"] + 9.0, 3), (42, 30, 22),
                    0.6 * ease(t, on_["gear 1"][0], on_["gear 1"][0] + 0.8))
        if p.name == "low beam":                                  # r12 (round 11 must-fix: the stones hung in the
            for sx_, sy_ in HW.STONES:                             # air): the two axles stand out of the low beam,
                dx_ = sx_ - (HW.PL + HW.PR) / 2                    # and each stone is slid onto its own
                bx_, by_ = q["x"] + dx_ * math.cos(a), q["y"] + dx_ * math.sin(a)
                dy_ = sy_ - HW.AXLE_BEAM_Y                         # (a little cleat on the beam carries it, so it
                gbx_, gby_ = gear_back()                           # r45: the axle end on at its gear's hub
                pg.c.save()                                        # sits at the stone's middle)
                pg.c.translate(bx_ - sh + gbx_, by_)
                pg.c.rotate(q["ang"])
                pg.shape(rrect(-9, -6, 9, dy_ + gby_ + 4, 3), tone(HW.WOOD, -0.08), 0.12)
                pg.c.restore()
                draw_axle_end(pg, bx_ + gbx_ - (dy_ + gby_) * math.sin(a), by_ + (dy_ + gby_) * math.cos(a), sh, q["ang"])
    elif k == "board":
        a_ = math.radians(q["ang"])
        o = q.get("off", 0.0)
        if p.name.startswith(("hopper", "roof")):                  # r37 (round 36 part 2 must-fix "the hopper is two
            # sticks, it couldn't hold acorns"): the hopper boards are wide planks; their broad top face shows going
            # back (the oblique view), so the two make a trough along the stones' nip, the acorns lying in it
            cx_, cy_ = q["x"] + o * math.cos(a_) - sh, q["y"] + o * math.sin(a_)
            hl = q["L"] / 2
            e0 = (cx_ - hl * math.cos(a_), cy_ - hl * math.sin(a_))
            e1 = (cx_ + hl * math.cos(a_), cy_ + hl * math.sin(a_))
            dep_ = HOPPER_DEPTH if p.name.startswith("hopper") else ROOF_DEPTH
            dx_, dy_ = DV[0] * dep_, DV[1] * dep_
            face = [e0, e1, (e1[0] + dx_, e1[1] + dy_), (e0[0] + dx_, e0[1] + dy_)]
            fc = tone(HW.WOOD, q.get("dark", 0.0) + (0.06 if p.name.endswith("L") else -0.06))
            fp_ = skia.Path().moveTo(*face[0])
            for pt_ in face[1:]:
                fp_.lineTo(*pt_)
            pg.shape(fp_.close(), fc, 0.1)
            for g_ in (0.33, 0.66):                                # the grain along it
                pg.stroke(skia.Path().moveTo(e0[0] + dx_ * g_, e0[1] + dy_ * g_).lineTo(e1[0] + dx_ * g_, e1[1] + dy_ * g_),
                          tone(fc, -0.12), 1.0, 0.5)
        HW.draw_board(pg, q["x"] + o * math.cos(a_), q["y"] + o * math.sin(a_), q["L"], q["ang"], sh, q.get("th", 12.0),
                      col=tone(HW.WOOD, q.get("dark", 0.0)), peg=q.get("peg", 0))
    elif k == "log":
        HW.draw_log(pg, q["x"] + q["x0"], q["x"] + q["x1"], q["y"], sh, q["r"])
    elif k == "stone":
        pg.c.save()
        tilt = q.get("tilt", 1.0)
        pg.c.translate(X, q["y"])
        pg.c.scale(1.0, 0.32 + 0.68 * tilt)
        draw_stone_side(pg)                                        # r17: a thick round stone, not a plate
        HW.draw_stone(pg, 0.0, 0.0, q["ang"], 0.0, q.get("grooves", 6.0), q.get("hole", 1.0), 0.0)
        pg.c.restore()
        w_ = q.get("wet", 0.0)
        if 0.02 < w_ < 0.97 and "wl" in q:                         # r35: lifted out wet, water drips off its rim
            hh_ = HW.STONE_R * (0.32 + 0.68 * tilt)
            for j in range(5):
                ph = (t * 1.3 + j * 0.37) % 1.0
                dx_ = HW.STONE_R * (-0.7 + 0.35 * j)
                y0_ = q["y"] + hh_ * (1.0 - (dx_ / HW.STONE_R) ** 2) ** 0.5
                yd = y0_ + 4.0 + 46.0 * ph * ph
                if yd > q["wl"] + 2.0 and q["y"] < q["wl"] + 40.0:
                    continue                                       # (into the water: gone)
                a_ = min(1.0, 2.0 * w_) * (1.0 - ph) * 0.9
                pg.flat(smooth([(X + dx_ + 2.6 * math.cos(u), yd + 3.6 * math.sin(u)) for u in np.linspace(0, 6.2832, 9)]),
                        mix(HW.WATER_C, HW.FOAM, 0.4), a_)
        i_ = int(p.name.split()[-1])
        ax_, ay_ = HW.STONES[i_]
        er_ = 11.0 * q.get("hole", 0.0)                            # r42 (round 42 part 2 must-fix "the eye turns into
        if er_ > 1.0 and q.get("tilt", 1.0) > 0.98 and math.hypot(q["x"] - ax_, q["y"] - ay_) < er_ + 9.0:
            pg.c.save()                                            # a brass cap in one frame"): the axle's end shows
            pg.c.clipPath(oval(q["x"] - sh, q["y"], er_, er_), skia.ClipOp.kIntersect, True)   # through the eye as
            draw_axle_end(pg, ax_, ay_, sh, q["ang"])              # the stone slides onto it, clipped to the eye
            pg.c.restore()
    elif k == "gear":
        # r40 (round 39 part 1 must-fix "a long thin plank vanishes off the pile and a square board appears in his
        # tentacle"): the square board lying flat on the pile is the same board seen edge on - squashed top to bottom
        # to its thickness - and it turns up face-on smoothly as he lifts it (was a separate plank drawing below
        # face 0.3 and the square squashed sideways above it: a jump), in its own wood from the start
        fy_ = max(q.get("face", 1.0), 12.0 / (2.0 * q["r"]))
        f = 1.0
        if fy_ < 0.999:
            pg.c.save()
            pg.c.translate(0.0, q["y"])
            pg.c.scale(1.0, fy_)
            pg.c.translate(0.0, -q["y"])
        if True:
            path = gear_shape(X, q["y"], q["ang"], q["r"], q.get("corners", 4.0), q.get("cut", float(TEETH)), f)
            # r18 (part 2 must-fix "the notches can't be seen forming at the blade"): the board's thickness, a darker
            # copy just behind and below, shows down each notch's walls the moment it is cut
            # r22 (part 2 must-fix "the light gear's teeth uneven"): the edge is the gear's own wood a shade darker,
            # straight behind it (it showed as a dark sliver down one side of each tooth, so the teeth read unequal)
            g_col = mix(HW.WOOD, HW.WOOD_END, 0.6) if p.name.endswith("0") else tone(HW.WOOD, -0.18)   # (r14: the
            side = gear_shape(X + 2.0 * f, q["y"] + 4.0, q["ang"], q["r"], q.get("corners", 4.0),       # two gears
                              q.get("cut", float(TEETH)), f)                                            # apart in tone)
            pg.shape(side, tone(g_col, -0.22), 0.04)
            pg.shape(path, g_col, 0.12)
            c_ = pg.c
            c_.save()
            c_.clipPath(path, skia.ClipOp.kIntersect, True)
            a_ = math.radians(q["ang"])
            for off in (-0.62, -0.3, 0.12, 0.48):                  # the board's grain, turning with it
                gp = skia.Path()
                for k_, v_ in enumerate((-1.4, 1.4)):
                    gx_ = X + (v_ * math.cos(a_) - off * math.sin(a_)) * q["r"] * f
                    gy_ = q["y"] + v_ * math.sin(a_) * q["r"] + off * math.cos(a_) * q["r"]
                    (gp.moveTo if k_ == 0 else gp.lineTo)(gx_, gy_)
                pg.stroke(gp, tone(HW.WOOD, -0.2), 1.6, 0.6)
            kx_, ky_ = 0.5 * q["r"], -0.18 * q["r"]                # r18: a knot off the middle, so every 45 degree
            kX, kY = X + (kx_ * math.cos(a_) - ky_ * math.sin(a_)) * f, q["y"] + kx_ * math.sin(a_) + ky_ * math.cos(a_)
            pg.flat(oval(kX, kY, 9.0 * f, 6.0), tone(g_col, -0.12), 0.9)   # turn of the octagon is seen (r22: a
            pg.stroke(oval(kX, kY, 9.0 * f, 6.0), tone(g_col, -0.3), 1.6, 0.8)   # ringed knot, lighter than the
            pg.flat(oval(kX, kY, 3.0 * f, 2.0), tone(g_col, -0.3), 0.9)          # axle hole: it read as a 2nd hole)
            c_.restore()
            pg.stroke(path, tone(HW.WOOD, -0.35), 2.2, 0.9)
            kerf = corner_kerf(P, p, q, t)
            if kerf is not None:                                   # the saw cut running across the corner
                pg.stroke(skia.Path().moveTo(*kerf[0]).lineTo(*kerf[1]), tone(HW.WOOD, -0.5), 2.6)
            for rr in (q["r"] * 0.55, q["r"] * 0.3):
                pg.stroke(skia.Path().addOval(skia.Rect(X - rr * f, q["y"] - rr, X + rr * f, q["y"] + rr)),
                          HW.WOOD_RING, 1.4, 0.6)
            pg.flat(oval(X, q["y"], 8 * f, 8), (96, 70, 50))
            if fy_ < 0.999:
                pg.c.restore()
            on = getattr(P, "gear_on", {}).get(p.name)
            if on is not None and t >= on[0]:                     # r30: on its axle: the shaft from its hub forward
                ex, ey = on[1], on[2]                              # to the peg end, over it (the gear is behind)
                dx, dy = q["x"] - ex, q["y"] - ey
                dd = math.hypot(dx, dy)
                if dd > 1.0:
                    nx, ny = -dy / dd * 9.0, dx / dd * 9.0
                    band = skia.Path().moveTo(ex - sh + nx, ey + ny).lineTo(X + nx, q["y"] + ny)\
                        .lineTo(X - nx, q["y"] - ny).lineTo(ex - sh - nx, ey - ny).close()
                    # r32 (round 31 part 2 must-fix "no shaft joins any gear to a stone"): the shaft was the gear's
                    # own brown and didn't show; now a darker round rod with edges and a sheen, from the hub to the stone
                    pg.shape(band, AXLE_COL, 0.12)
                    for e_ in (1.0, -1.0):
                        pg.stroke(skia.Path().moveTo(ex - sh + e_ * nx, ey + e_ * ny).lineTo(X + e_ * nx, q["y"] + e_ * ny),
                                  tone(HW.WOOD, -0.6), 1.6, 0.9)
                    pg.stroke(skia.Path().moveTo(ex - sh + 0.35 * nx, ey + 0.35 * ny).lineTo(X + 0.35 * nx, q["y"] + 0.35 * ny),
                              tone(HW.WOOD, 0.1), 1.8, 0.5)
                    pg.shape(oval(X, q["y"], 9.0, 9.0), AXLE_COL, 0.12)   # r31: the shaft fills the hub
                    pg.stroke(oval(X, q["y"], 9.0, 9.0), tone(HW.WOOD, -0.35), 1.4, 0.7)   # (round 30 part 2: "its
                    # centre is an empty hole with no axle")
                draw_axle_end(pg, ex, ey, sh, 0.0)
    elif k in ("corner", "chip"):
        # r42: the gear blanks' offcuts in the board's own wood (gear 0 light, gear 1 darker) with its edge line:
        # a corner is a right triangle with its long side the saw cut; a chip is the wedge sawn out of a notch.
        # Lying on the ground they are seen flat (fy squashes them to a sliver)
        a = math.radians(q["ang"])
        fy = q.get("fy", 1.0)
        if k == "corner":
            pts = [(0.0, -17.5), (35.0, 17.5), (-35.0, 17.5)]
        else:
            h_ = NOTCH_D / 2
            pts = [(h_, -NOTCH_TW / 2), (h_, NOTCH_TW / 2), (-h_, NOTCH_BW / 2), (-h_, -NOTCH_BW / 2)]
        g_col = mix(HW.WOOD, HW.WOOD_END, 0.6) if p.name.startswith("gear 0") else tone(HW.WOOD, -0.18)
        path = skia.Path()
        for j, (x_, y_) in enumerate(pts):
            xx, yy = X + x_ * math.cos(a) - y_ * math.sin(a), q["y"] + (x_ * math.sin(a) + y_ * math.cos(a)) * fy
            (path.moveTo if j == 0 else path.lineTo)(xx, yy)
        path.close()
        pg.shape(path, g_col, 0.08)
        pg.stroke(path, tone(HW.WOOD, -0.35), 2.0, 0.9)
    elif k == "pulley":
        if q.get("face", 1.0) < 0.3:                               # the slice seen edge on: its bark side
            HW.draw_board(pg, q["x"], q["y"], 2 * HW.PULLEY_R, 90.0, sh, 12.0, HW.WOOD)
        else:
            draw_slice_pulley(pg, q["x"], q["y"], q["ang"], sh)
            sx_, sy_ = HW.STONES[0]
            if math.hypot(q["x"] - sx_, q["y"] - sy_) < 1.5:        # on the axle: its end through the slice
                draw_axle_end(pg, q["x"], q["y"], sh, q["ang"])
    elif k == "sack":
        if q.get("folded", 0.0) > 0.5:
            pg.shape(rrect(X - 40, q["y"] - 14, X + 40, q["y"], 5), HW.SACK, 0.1)
        else:
            tip = q.get("tip", 0.0)
            if abs(tip) > 1e-3:
                px, py = sack_pivot(q, P.sack_fill(t))
                pg.c.save()
                pg.c.rotate(tip, px - sh, py)
            ct = P.tie_cord(t) if P.tie[0] - 0.05 <= t < P.tie_wind[1] else None
            if hasattr(P, "untie") and P.untie[0] <= t < P.untie[1]:
                ct = P.sack_bow(t)                                 # r14: the cord's end in his tentacle as it unwinds
            HW.draw_sack(pg, q["x"], q["y"], P.sack_fill(t), q.get("tied", 0.0), sh, cord_to=ct,
                         slump=min(1.0, abs(tip) / 80.0))               # r16: soft cloth as it tips
            if abs(tip) > 1e-3:
                pg.c.restore()
            draw_flour_stream(pg, P, t, sh)                        # r14: in front of the sack, out of its mouth
    elif k == "basket":
        # r45 (round 44 part 1: it read as floating at Springs' hand): a soft contact shadow on the grass, fading as
        # it's lifted off it
        sa_ = 0.16 * max(0.0, 1.0 - abs(q["y"] - HW.BASKET_HOME[1]) / 30.0) * (1.0 - min(1.0, abs(q["ang"]) / 20.0))
        if sa_ > 0.005:
            pg.shadow(X, HW.BASKET_HOME[1] + 3.0, 40.0, 8.0, sa_)
        HW.draw_basket(pg, q["x"], q["y"], q["ang"], 0, sh)
    elif k == "acorn":
        y = q["y"]
        if q.get("on_branch", 0.0) > 0.5:
            y = P.branch_y(q["x"], t) + 10.0
        c_ = q.get("crush", 0.0)
        # r43 (round 43 part 2 must-fix "the acorn slides down over the front of both stones"): in the V above the
        # nip it goes in between the stones, so their front faces hide it - only what's in the gap shows
        nip_clip = False
        if abs(q["x"] - HW.NIP_X) < 40.0 and HW.STONES[0][1] - 110.0 < y < HW.STONES[0][1] + 20.0:
            st_ = [P.props[f"millstone {i}"].at(t)[0] for i in (0, 1)]
            if all(math.hypot(s_["x"] - HW.STONES[i][0], s_["y"] - HW.STONES[i][1]) < 1.5
                   and s_.get("tilt", 1.0) > 0.98 for i, s_ in enumerate(st_)):
                nip_clip = True
                pg.c.save()
                for s_ in st_:
                    pg.c.clipPath(oval(s_["x"] - sh, s_["y"], HW.STONE_R, HW.STONE_R), skia.ClipOp.kDifference, True)
        if c_ > 0.0:                                               # r16: squeezed in the nip (narrower, a bit taller)
            pg.c.save()
            pg.c.translate(X, y)
            pg.c.scale(1.0 - 0.62 * c_, 1.0 + 0.12 * c_)
            HW.draw_acorn(pg, 0.0, 0.0, q.get("s", 1.0), q["ang"] * (1.0 - c_))
            pg.c.restore()
        else:
            HW.draw_acorn(pg, X, y, q.get("s", 1.0), q["ang"])
        if nip_clip:
            pg.c.restore()
    elif k == "belt_coil":
        for r in (16, 22, 28):
            pg.stroke(skia.Path().addOval(skia.Rect(X - r, q["y"] - r * 0.7, X + r, q["y"] + r * 0.7)), (122, 84, 58),
                      4.0)


# ----------------------------------------------------------------------------------------------- the mill, live

def draw_wheel(pg, P, t, sh):
    """The old water wheel in the brook: its post behind, the rim, spokes and paddles turning, its pulley in front."""
    X, Y = HW.WX - sh, HW.WY
    if not (-HW.WR - 200 < X < W + HW.WR + 200):
        return
    ang = P.wheel_ang(t) if hasattr(P, "wheel_go") else 0.0
    pg.shape(rrect(X - 14, Y - 10, X + 14, HW.water_y(HW.WX) + 30, 6), HW.POLE, 0.1)       # its post (behind)
    a0 = math.radians(ang)
    for k in range(16):                                            # the paddles
        a = a0 + 2 * math.pi * k / 16
        cx, cy = X + math.cos(a) * (HW.WR - 6), Y + math.sin(a) * (HW.WR - 6)
        p = rrect(cx - 26, cy - 6, cx + 26, cy + 6, 2)
        p.transform(skia.Matrix.RotateDeg(math.degrees(a), (cx, cy)))
        pg.shape(p, HW.WOOD_D, 0.08)
    for r, w in ((HW.WR - 30, 7.0), (HW.WR + 2, 7.0)):
        pg.stroke(skia.Path().addOval(skia.Rect(X - r, Y - r, X + r, Y + r)), HW.WOOD, w)
    for k in range(8):
        a = a0 + 2 * math.pi * k / 8
        pg.stroke(skia.Path().moveTo(X + math.cos(a) * 18, Y + math.sin(a) * 18)
                  .lineTo(X + math.cos(a) * (HW.WR - 30), Y + math.sin(a) * (HW.WR - 30)), HW.WOOD, 6.0)
    pg.shape(oval(X, Y, 24, 24), HW.WOOD_D, 0.1)
    if t >= P.wheel_go:                                             # splashes where the paddles meet the water
        for k in range(5):
            ph = (t * 1.6 + k * 0.37) % 1.0
            sx = X - 40 + 26 * k + 10 * math.sin(t + k)
            pg.flat(oval(sx, HW.water_y(HW.WX) - 6 - 18 * math.sin(math.pi * ph), 5, 4), HW.FOAM, 0.7 * (1 - ph))


def draw_wheel_front(pg, P, t, sh):
    X, Y = HW.WX - sh, HW.WY
    ang = P.wheel_ang(t) if hasattr(P, "wheel_go") else 0.0
    HW.draw_pulley(pg, HW.WX, Y, ang, sh, HW.WHEEL_PULLEY_R)


def draw_brake(pg, P, t, sh):
    """The brake post on the bank, its peg, and the rope from the peg round a paddle (it holds the wheel still)."""
    X = HW.BRAKE_X - sh
    if not (-100 < X < W + 100):
        return
    # r24 (round-23 part 2 must-fix "the pulled peg is still standing in its spot": the bare post read as the peg):
    # a stout post, twice the peg's width, with a dark capped top, so it can't be taken for the peg
    pg.shape(rrect(X - 14, HW.BRAKE_TOP - 4, X + 14, HW.FLOOR + 4, 3), tone(HW.POLE, -0.12), 0.1)
    pg.shape(rrect(X - 16, HW.BRAKE_TOP - 6, X + 16, HW.BRAKE_TOP + 4, 2), tone(HW.POLE, -0.3), 0.1)
    st = P.peg_state(t) if hasattr(P, "pin") else "post"
    paddle = (HW.WX + HW.WR * math.cos(math.radians(24.0)), HW.WY + HW.WR * math.sin(math.radians(24.0)))
    rope = (150, 116, 74)
    neck = PEG_KNOB - 8.0                                          # r13: the rope's loop round the peg's neck
    if st == "post":
        ny = HW.BRAKE_TOP - neck
        pg.stroke(skia.Path().moveTo(X, ny).quadTo((X + paddle[0] - sh) / 2 + 26, (ny + paddle[1]) / 2,
                                                   paddle[0] - sh, paddle[1]), rope, 3.0)
        pg.stroke(oval(X, ny, 8, 3), tone(rope, -0.15), 2.5)
    else:
        pg.flat(oval(X, HW.BRAKE_TOP - 1, 7, 3.2), (40, 28, 22))   # the empty hole in the post's top
        # r22 (part 2 must-fix "the rope vanishes after the peg is pulled"; it fell behind Springs): the loop stays
        # round the peg's neck, so the rope comes away with the peg in his hand and trails from it where he drops it
        # on the path; its other end slips off the paddle as the wheel turns and falls on the bank
        end = peg_neck(P, t)
        u = 1.0
        off = ease(t, P.wheel_go + 0.5, P.wheel_go + 1.2)          # and slips off the paddle as the wheel turns
        a = math.radians(24.0 + (P.wheel_ang(t) if t >= P.wheel_go else 0.0))
        pad = (HW.WX + HW.WR * math.cos(a), HW.WY + HW.WR * math.sin(a))
        tip = lerp2(pad, (HW.BRAKE_X - 110, HW.FLOOR - 10), off)
        # r22 (part 2 must-fix "the rope vanishes after the peg is pulled"): the whole rope lies slack on the bank
        # (its full length, in loose loops, outlined) once it has fallen, not a short thin line lost in the grass
        lie = min(u, off)
        pts = []
        for k in range(41):
            v = k / 40.0
            bx, by = lerp2(end, tip, v)
            by += (1.0 - lie) * 26.0 * 4.0 * v * (1.0 - v)          # (the sag while it falls)
            bx += lie * 16.0 * math.sin(2 * math.pi * 3.0 * v)       # (loops on the ground)
            by += lie * 5.0 * math.cos(2 * math.pi * 3.0 * v) - lie * 4.0
            pts.append((bx - sh, by))
        rp = smooth(pts, closed=False)
        pg.stroke(rp, tone(rope, -0.35), 5.0)
        pg.stroke(rp, rope, 3.2)
    if hasattr(P, "pin"):
        pp, ps = peg_pos(P, t)
    else:
        pp, ps = PEG, "post"
    if ps == "post":
        draw_peg(pg, pp, sh, out=False)


def peg_neck(P, t):
    """Where the rope's loop sits on the brake peg (world): its neck under the knob, turned as the peg lies down."""
    neck = PEG_KNOB - 8.0
    pp, st = peg_pos(P, t)
    if st == "post":
        return pp[0], pp[1] - neck
    td_ = P.pin[1] + PEG_DROP
    a = math.radians(-90.0 * ease(t, td_, td_ + 0.3))             # (as draw_peg turns it, about 6 px below p)
    vx, vy = 0.0, -(neck + 6.0)
    return pp[0] + vx * math.cos(a) - vy * math.sin(a), pp[1] + 6.0 + vx * math.sin(a) + vy * math.cos(a)


def draw_peg(pg, p, sh, out=True, ang=0.0):
    """The brake peg, p where it goes into the post: a pale knob, and (out of the post) its long shank (r13: it read
    as a second stub of the post). ang: tipped over (about its middle) as it falls."""
    X, Y = p[0] - sh, p[1]
    if ang:
        pg.c.save()
        pg.c.rotate(ang, X, Y + 6.0)
    pg.shape(rrect(X - 5, Y - PEG_KNOB, X + 5, Y + (PEG_SHANK + 10.0 if out else 4), 3), PEG_COL, 0.1)
    pg.shape(oval(X, Y - PEG_KNOB, 11, 8), tone(PEG_COL, 0.08), 0.1)   # (r24: a bit bigger, so it reads lying down)
    if ang:
        pg.c.restore()


TOPSOIL = (106, 80, 60)             # r40: the dark top layer Digs throws left off his clay pit (and later puts back)


def draw_holes(pg, P, t, sh, near=None):
    """The post holes (dark, opening as Digs digs) and the soil heaps beside them. near=x: only the post holes' piles
    within reach of x again (r18: the left pile sits in front of the brake post and its hanging belt coil)."""
    for side, h in P.holes.items():
        o, hs = P.hole_state(side, t)
        X = h["x"] - sh
        if not (-200 < X < W + 200):
            continue
        if near is not None and h.get("clay"):
            continue
        if near is not None:
            pass
        elif o > 0.01:
            if h.get("clay"):                                       # r15: on the path right in front of his feet,
                pg.flat(oval(X, GB + 14, h["w"] * o + 4, 12 * o + 2), (88, 64, 48))   # where his claws scrape it
            else:
                pg.flat(oval(X, GB - 40, h.get("w", 34.0) * o + 4, 9 * o + 2), (88, 64, 48))
        if "push" in h and near is None and h.get("clay"):         # r26: the clay pit filled level, patted flat
            u = P.filled(side, t)
            if u > 0.01:
                pt = P.patted(side, t)
                hm = 5.0 * u - 4.0 * pt
                # r42 (round 41 part 2 must-fix "the hole opens again with nobody digging"): patted down it takes on
                # the path's own colour and fades to a faint flat mark (a brown oval read as the open hole once the
                # evening light came in)
                col = mix(mix(TOPSOIL, (204, 172, 128), 0.35), HW.PAL["path"], 0.7 * pt)
                pg.flat(oval(X, GB + 14 - hm * 0.5, (h["w"] + 4) * min(1.0, 0.5 + 0.5 * u), 12 + hm * 0.5),
                        col, min(1.0, 2.0 * u) * (1.0 - 0.6 * pt))   # (r40: the topsoil, patted: lighter than the hole)
        elif "push" in h and near is None:                         # r18: the soil that's gone back in, heaped
            u = P.filled(side, t)                                  # round the post, then patted down firm
            if u > 0.01:
                hm = 16.0 * u - 6.0 * P.patted(side, t)
                pg.shape(smooth([(X - 40, GB - 36), (X - 16, GB - 36 - hm), (X + 16, GB - 36 - hm), (X + 40, GB - 36)]),
                         HW.EARTH, 0.1)
        if t < h["t"][0]:
            continue
        for sx in (-1, 1):
            cx, hh = h["spoil"].heap(sx, t)
            h0 = h["spoil"].h0
            got, tot = hh - h0, h["spoil"].heap(sx, 1e9)[1] - h0  # r7: it grows only as the soil lands on it ("a
            hh = (got + h0 * (got / tot if tot > 0 else 1.0)) * hs    # pile is there before the first scoop")
            wp = 1.0
            if "push" in h:                                        # r18: each pile on its own, pushed in
                cx, sc = P.soil_pile(side, sx, t)
                hh = (got + h0 * (got / tot if tot > 0 else 1.0)) * sc
                wp = 0.4 + 0.6 * sc                                # (narrower too as it drops in)
            dy = 0.0
            if h.get("clay"):
                hh *= P.clay_left(sx, t)
                if sx < 0 and "push" in h:                         # r26: shoved forward and down into the pit
                    dy = CLAY_FILL_DY * P.clay_shove(t)            # (it's on the path, in front)
            if near is not None and abs(cx - near) > 90.0:
                continue
            if hh > 1.0:
                col = HW.EARTH
                wf = wp
                if h.get("clay") and sx < 0:                       # r40 (round 39 part 2 must-fix "Digs pushes the
                    col = TOPSOIL                                  # same clay back into his pit, undoing his work"):
                    # the left paw throws out the dark topsoil, the right the clay; only the topsoil goes back in
                elif h.get("clay"):
                    col = mix(HW.CLAY, HW.CLAY_SOFT, ease(t, *P.soft) if sx > 0 and hasattr(P, "soft") else 0.0)
                    if sx > 0:                                       # r15: the oven's heap, six lumps' worth
                        hh *= CLAY_HH
                        wf = CLAY_HW * P.clay_left(sx, t)            # (r31: narrower too as it's used up)
                        if hasattr(P, "soft"):                       # bounced flat
                            hh *= 1.0 - 0.35 * ease(t, *P.soft)
                pg.shape(smooth([(cx - 46 * wf - sh, GB - 34 + dy), (cx - 14 * wf - sh, GB - 34 - hh + dy),
                                 (cx + 16 * wf - sh, GB - 34 - hh + dy), (cx + 46 * wf - sh, GB - 34 + dy)]), col, 0.1)
        if t < h["t"][1] + 0.6 and near is None:
            for name, px, py, size, carried, lands in h["spoil"].pieces(t, STEP):
                pg.flat(oval(px - sh, py, size, size * 0.8),       # (r40: the clay pit's right clods are clay)
                        (HW.CLAY if name.startswith("soil R") else TOPSOIL) if h.get("clay") else HW.EARTH)


def draw_branch(pg, P, t, sh):
    """The oak's live outer branch (it bends with Springs) and its leaves."""
    (x0, y0), (x1, y1) = HW.OAK_BRANCH[1], HW.OAK_BRANCH[2]
    if not (-500 < x0 - sh < W + 200):
        return
    pts = [(x0 + (x1 - x0) * u - sh, P.branch_y(x0 + (x1 - x0) * u, t) - 6.0) for u in np.linspace(0, 1, 6)]
    pg.shape(tube(pts, 9, 5), HW.TRUNK, 0.1, (0.0, -0.4))
    for k, u in enumerate((0.3, 0.55, 0.8, 1.0)):
        x = x0 + (x1 - x0) * u
        y = P.branch_y(x, t) - 18
        pg.shape(oval(x - sh, y, 34, 22), (PAL_OLIVE if k % 2 else PAL_OCHRE), 0.1)


PAL_OLIVE, PAL_OCHRE = (142, 154, 80), (207, 162, 76)


def draw_squirrel(pg, P, t, sh):
    """The squirrel, storybook-big (owner, FK0021: "the squirrel's very tiny"), on the branch right over Digs, facing
    him; the acorn in its paws is the hook's acorn prop itself (one acorn, never a drawn copy)."""
    x = SQ_X
    y = P.branch_y(x, t) - 6.0
    c = pg.c
    c.save()
    c.translate(x - sh, y)
    c.scale(SQ_S, SQ_S)
    c.translate(-(x - sh), -y)
    HW.squirrel(pg, x, y, 1, t, sh=sh, nibble=0.0)
    c.restore()


SQ_X, SQ_S = 520.0, 1.7


HOP_DY = 0.0                        # (r4 hop dropped in r9: talk_dy never moved his body; Glo picks the acorn off)


def digs_hop_dy(P, t):
    """How far up Digs is in his little hop (0 when he isn't hopping): up over 0.2 s to the flip, down over 0.3 s."""
    t0 = getattr(P, "digs_hop", None)
    if t0 is None or not t0 - 0.2 <= t <= t0 + 0.3:
        return 0.0
    if t <= t0:
        return HOP_DY * smoothstep((t - t0 + 0.2) / 0.2)
    return HOP_DY * (1 - smoothstep((t - t0) / 0.3))


def digs_bonk_face(P, t):
    """Digs' face round the bonk: a wince as it hits, then he looks up (at the squirrel, then at Glo)."""
    if not hasattr(P, "digs_hop") or not P.bonk - 0.1 <= t <= P.glo_catch + 1.0:
        return {}
    w = ease(t, P.bonk, P.bonk + 0.08) * (1 - ease(t, P.bonk + 0.45, P.bonk + 0.75))
    lk = ease(t, P.bonk + 0.5, P.bonk + 0.8) * (1 - ease(t, P.glo_catch + 0.2, P.glo_catch + 0.9))
    to_glo = ease(t, P.digs_hop - 0.1, P.glo_catch)
    out = dict(lid_top=0.8 * w, cheek=0.8 * w, smile=0.6 - 1.2 * w, talk_dy=digs_hop_dy(P, t))
    if lk > 0:
        idx = 5 * 2.3                                              # (Monster's own idle look for Digs, to blend)

        def look(tt, lk=lk, g=to_glo):
            lx, ly = math.sin(tt * 0.7 + idx), 0.4 * math.sin(tt * 0.45)
            ux, uy = -0.2 + 0.9 * g, -0.95 + 0.35 * g
            return lx + (ux - lx) * lk, ly + (uy - ly) * lk
        out["_look"] = look
    return out


def bonk_ticks(pg, P, t, sh):
    """Four little strokes flick out round Digs' hat as the acorn hits it (a storybook "bonk")."""
    u = (t - P.bonk) / 0.8
    if not 0.0 <= u < 1.0:
        return
    hx, hy = SQ_X + 21.0 * SQ_S - sh, GB - 300 * K + 8.0
    for ang in (-150, -115, -65, -30):
        a = math.radians(ang)
        r0, r1 = 22 + 26 * u, 34 + 34 * u
        pth = skia.Path()
        pth.moveTo(hx + r0 * math.cos(a), hy + r0 * math.sin(a))
        pth.lineTo(hx + r1 * math.cos(a), hy + r1 * math.sin(a))
        pg.stroke(pth, (255, 244, 214), 4.0, 1.0 - u)                                            # the squirrel's feet on the branch, its size


def draw_flour(pg, P, t, sh):
    """Flour coming out under the stones into the sack: a puff for the first acorn, a soft stream after each."""
    X = HW.NIP_X - sh
    y0 = HW.STONES[0][1] + HW.STONE_R * 0.4
    mouth = HW.FLOOR - 2 - 40 - 44 * P.sack_fill(t) - 6
    y0 = HW.STONES[0][1] + 6.0                                    # r16: from the nip's lower lip, as it's crushed
    for tc, name in P.acorn_flow:
        u = (t - tc + 0.3) / 1.7
        if 0 <= u < 1:
            for q in range(7):
                f = (u * 1.6 + q / 7) % 1.0
                yy = y0 + (mouth - y0) * f
                pg.flat(oval(X + 3 * math.sin(q * 2.1 + t * 5), yy, 3.5, 3.5), HW.FLOUR, 0.9 * (1 - u))
    u = (t - P.flour_puff) / 2.6
    if 0 <= u < 1:                                                 # the first flour: a bright stream into the sack
        for q in range(12):
            f = (u * 2.6 + q / 12) % 1.0
            yy = y0 + (mouth - y0) * f
            pg.flat(oval(X + 4 * math.sin(q * 1.7 + t * 6), yy, 5.0, 5.0), HW.FLOUR, 1.0 - 0.6 * u)
        for q in range(7):                                         # r16: it settles in the sack's mouth (a low
            a = (q - 3) / 3.0                                      # heap spreading sideways, never a rising puff)
            pg.flat(oval(X + a * (10 + 16 * u), mouth - 3 - 5 * (1 - abs(a)) * min(1.0, 3 * u), 7 + 4 * u, 4 + 2 * u),
                    HW.FLOUR, 0.8 * (1 - 0.5 * u))


def sack_fill(P, t):
    n = sum(ease(t, tc, tc + 1.4) for tc, _ in P.acorn_flow)
    tot = max(1, len(P.acorn_flow))
    poured = 0.5 * ease(t, P.pour[0] + 0.6, P.pour[1]) if hasattr(P, "pour") else 0.0   # r14: it slims as it pours
    return min(1.0, n / tot) - poured


Plan.sack_fill = sack_fill


# ----------------------------------------------------------------------------------------------- overlays

_FONT = {}
INK, PAPER = (70, 52, 44), (252, 246, 234)


def _font(size, weight="Bold"):
    key = (size, weight)
    if key not in _FONT:
        import os
        _FONT[key] = skia.Font(skia.Typeface.MakeFromFile(os.path.join("engine", "assets", "fonts",
                                                                        f"Inter-{weight}.otf")), size)
    return _FONT[key]


def _text(pg, s, x, y, size, col=INK, a=1.0, weight="Bold", center=False):
    f = _font(size, weight)
    if center:
        x -= f.measureText(s) / 2
    pg.c.drawString(s, x, y, f, skia.Paint(AntiAlias=True, Color=C(col, a)))


def _card(pg, x, y, w, h, a, r=18):
    pg.flat(rrect(x + 4, y + 6, x + w + 4, y + h + 6, r), (40, 28, 24), 0.18 * a, blur=8)
    pg.flat(rrect(x, y, x + w, y + h, r), PAPER, 0.94 * a)


TOP = {"wheels": 236, "tentacles": 309, "teeth": 380, "springs": 206, "lantern": 246, "digger": 202}   # drawn
                                    # tops above the feet (Glo: above his y); Twigs: his head, not his antennae


def tag_spots(P, t, avoid=()):
    """Where each Keeper's name tag goes: just over its own head, nudged sideways or put beside the head if that
    would cover another Keeper, another tag or `avoid` (the sign). (owner's notes: the 'Hans' tag sat on Glo's
    dome and 'Glo' floated far above him.)"""
    from .causecheck import body_box
    sh = P.shift(t)
    bodies, spots, out = {}, [], {}
    for kd in ORDER:
        x, y, _ = keeper(kd, t)
        bodies[kd] = (x - sh, y, body_box(kd, x - sh, y, K))

    def hit(r, own):
        for kd, (_, _, b) in bodies.items():
            if kd != own and r[0] < b[2] and b[0] < r[2] and r[1] < b[3] and b[1] < r[3]:
                return True
        return any(r[0] < q[2] and q[0] < r[2] and r[1] < q[3] and q[1] < r[3] for q in list(spots) + list(avoid))
    for kd in sorted(ORDER, key=lambda k: bodies[k][1] - TOP[k] * K / 0.72):
        X, Y, b = bodies[kd]
        tw = _font(30).measureText(NAMES[kd]) + 32
        top = Y - TOP[kd] * K / 0.72 - 20
        cands = [(X, top)] + [(X + d, top) for d in (-60, 60, -120, 120)] + \
                [(b[0] - tw / 2 - 8, (b[1] + b[3]) / 2), (b[2] + tw / 2 + 8, (b[1] + b[3]) / 2)]
        for cx, cy in cands:
            r = (cx - tw / 2, cy - 34, cx + tw / 2, cy + 12)
            if r[0] > 8 and r[2] < W - 8 and not hit(r, kd):
                break
        spots.append(r)
        out[kd] = (cx, cy, tw)
    return out


_TAG_FIX = {}


def name_tags(pg, t, a, avoid=(), t_fix=None):
    """r42 (round 41 part 1 must-fix "the Digs tag jumps beside his body, Springs' 45 px right"): each tag's spot is
    chosen once, at t_fix (when the tags come up), and kept on its Keeper from there until they've faded (the spots
    were chosen afresh every frame and flipped as the Keepers bobbed)."""
    P = plan()
    if t_fix is None:
        spots = tag_spots(P, t, avoid)
    else:
        key = (round(t_fix, 3), tuple(avoid))
        if key not in _TAG_FIX:
            sh0 = P.shift(t_fix)
            _TAG_FIX[key] = {kd: (cx - (keeper(kd, t_fix)[0] - sh0), cy - keeper(kd, t_fix)[1], tw)
                             for kd, (cx, cy, tw) in tag_spots(P, t_fix, avoid).items()}
        sh = P.shift(t)
        spots = {kd: (keeper(kd, t)[0] - sh + dx, keeper(kd, t)[1] + dy, tw) for kd, (dx, dy, tw) in _TAG_FIX[key].items()}
    for kd, (cx, cy, tw) in spots.items():
        if 60 < cx < W - 60:
            _card(pg, cx - tw / 2, cy - 34, tw, 46, a)
            _text(pg, NAMES[kd], cx, cy, 30, a=a, center=True)


def overlays(pg, t):
    P = plan()
    a = ease(t, P.tags[0], P.tags[0] + 1.0) * (1 - ease(t, P.tags[1], P.tags[1] + 1.0))
    if a > 0:
        name_tags(pg, t, a, t_fix=P.tags[0] + 1.0)
    end_sign(pg, t)


def end_sign(pg, t):
    P = plan()
    sa = ease(t, *P.sign)
    if sa <= 0:
        return
    bw, bh = 1120, 210
    x0, y0 = (W - bw) / 2, 70
    pg.flat(rrect(x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10, 26), (40, 28, 24), 0.25 * sa, blur=10)
    pg.flat(rrect(x0, y0, x0 + bw, y0 + bh, 26), (150, 108, 72), sa)
    pg.flat(rrect(x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14, 18), (176, 132, 90), sa)
    _text(pg, "WHAT SHOULD THEY BUILD NEXT?", W / 2, y0 + 104, 54, col=PAPER, a=sa, center=True)
    _text(pg, "Tell us in the comments", W / 2, y0 + 162, 34, col=(250, 232, 200), a=sa, weight="Medium", center=True)
    name_tags(pg, t, sa, avoid=((x0 - 10, y0 - 10, x0 + bw + 10, y0 + bh + 16),), t_fix=P.sign[1])


def bubbles(pg, t):
    from .chatter import MOODS, bubble, _back
    P = plan()
    sh = P.shift(t)
    for tv, kd, mood, pic in P.voices:
        u = t - tv
        pic = pic or MOODS[mood][2]
        if pic is None or pic in ("!", "?") or not (0 <= u < 2.2) or t >= P.sign[0] - 4.0:
            continue
        x, y, _ = keeper(kd, t)
        top = y - (GLO_TOP if kd == "lantern" else KH[kd]) * K   # r9: Glo's dome top (his float height is in y)
        s = _back(min(u / 0.25, 1.0)) * (1 - smoothstep((u - 1.9) / 0.3))
        bx, by = x - sh + 70 * K + 26, top - 62
        z, zcx, zcy = P.zoom(tv)                                   # r9: never off the top of the (zoomed) frame
        if abs(x - sh - zcx) > W / (2 * z) - 20 / z:               # r42 (round 41 part 3: a star bubble with nobody
            continue                                               # in shot): no bubble for a Keeper out of frame
        z, zcx, zcy = P.zoom(t)
        by = max(by, zcy - H / (2 * z) + BUBBLE_R * s + 14 / z)
        bx = min(bx, zcx + W / (2 * z) - 1.12 * BUBBLE_R * s - 20 / z)   # r12: ...nor off its right side
        def draw(cv, bx=bx, by=by, s=s, pic=pic):
            bubble(cv, bx, by, BUBBLE_R * s, pic, (214, 196, 176), 1.0, (bx - 62, by + 92))
            if pic == "wheel" and BUBBLE_R * s >= 2:              # r12 (round 11: Wheels' idea bubble was empty -
                wheel_icon(cv, bx, by, BUBBLE_R * s * 0.62)        # chatter has no wheel picture): a little water wheel
        il.creature(pg, draw, bx, by)


def wheel_icon(cv, x, y, r):
    """A little water wheel for an idea bubble: rim, eight spokes and paddles, a hub."""
    from .chatter import ellipse
    wood, dark = (176, 122, 72), (110, 72, 44)
    for i in range(8):
        a = i * math.pi / 4 + 0.2
        ca, sa = math.cos(a), math.sin(a)
        cv.line(x, y, x + ca * r * 0.8, y + sa * r * 0.8, wood, max(1.5, r * 0.09))
        px, py = x + ca * r * 0.92, y + sa * r * 0.92                # a paddle across the rim
        cv.line(px - sa * r * 0.16, py + ca * r * 0.16, px + sa * r * 0.16, py - ca * r * 0.16, dark, max(2.0, r * 0.14))
    cv.polyline(ellipse(x, y, r * 0.8, r * 0.8, 32), wood, max(2.0, r * 0.12), closed=True)
    cv.circle(x, y, r * 0.16, dark)


def bread_steam(pg, t, sh):
    """r10 (part 3 must-fix, "the bread is never shown"): soft wisps of steam off the warm loaves, from the moment they
    come out of the oven; they thin away over the feast."""
    P = plan()
    if not hasattr(P, "slide_out"):
        return
    t0 = P.slide_out[1]
    a = ease(t, t0, t0 + 0.8) * (1.0 - ease(t, t0 + 40.0, t0 + 48.0))
    if a <= 0.01:
        return
    # r41 (round 40 part 3 must-fix "the steam is drawn over Hans' forehead while the bread is behind him"): while
    # the loaves are on a layer behind him, his head and fins cover their steam too
    hx_, hy_, ha_ = keeper("tentacles", t)
    hx_ -= sh
    hy_ -= 305 * K
    near_ = abs(P.loaves[0].at(t)[0]["x"] - sh - hx_) < 400 if P.loaves else False
    clip_ = None
    if near_ and zof(P.loaves[0], t) < 20 and not hans_front(P, P.loaves[0], P.loaves[0].at(t)[1], P.loaves[0].at(t)[0], t):
        clip_ = skia.Path().addOval(skia.Rect(hx_ - 128 * K, hy_ - 138 * K, hx_ + 128 * K, hy_ + 138 * K))
        clip_.addOval(skia.Rect(hx_ - 215 * K, hy_ - 120 * K, hx_ + 215 * K, hy_ + 20 * K))   # (his fins)
        pg.c.save()
        pg.c.clipPath(clip_, skia.ClipOp.kDifference, True)
    for j, p in enumerate(P.loaves):
        q = p.at(t)[0]
        x, y = q["x"] - sh, q["y"] - LOAF_H - 6.0
        for k in range(2):
            ph = t * 0.9 + j * 1.7 + k * 2.9
            u0 = ph % 1.0                                          # each wisp rises, then a new one starts
            path = skia.Path()
            for n in range(9):
                v = n / 8.0
                yy = y - 46.0 * (u0 * 0.6 + v * 0.7)
                xx = x + (k - 0.5) * 10.0 + 6.0 * math.sin(6.0 * v + ph * 2.0) * v
                path.moveTo(xx, yy) if n == 0 else path.lineTo(xx, yy)
            pg.stroke(path, "#fff8ec", 3.2, 0.32 * a * math.sin(math.pi * u0), blur=1.6)
    if clip_ is not None:
        pg.c.restore()


def glo_lights(pg, t, sh):
    """Glo's flare: light gathers in his lantern (and floats to what it lights)."""
    P = plan()
    gx, gy = P.glo_x(t), P.glo_y(t)
    lx, ly = gx - sh, gy - 260 * K + glo_bob(t) + 82 * K
    for a, b, target in P.flares:
        if target is None or not (a - 0.3 <= t < b + 0.4):
            continue
        tx, ty = target(t)
        u = ease(t, a, a + 0.8)
        fade = 1 - ease(t, b, b + 0.4)
        x = lx + (tx - sh - lx) * u
        y = ly + (ty - ly) * u - 40 * math.sin(math.pi * u)
        pg.glow(x, y, 70, "#ffe7a8", 0.75 * fade)
        pg.flat(oval(x, y, 7, 7), "#fff4d0", fade)
    f = glo_flare(P, t)
    if f > 0.01:
        pg.glow(lx, ly, 110, "#ffe7a8", 0.45 * f)




def _peg_state(P, t):
    if t < P.pin[0] + 0.3:
        return "post"
    return "hand" if t < P.pin[1] + PEG_DROP else "ground"


Plan.peg_state = _peg_state


# ----------------------------------------------------------------------------------------------- the village, drawn

DV = (0.25, -0.35)                  # the oblique view: a step back in depth goes this far right and up on screen


def zof(p, t):
    """A prop's drawing depth now (the peel and the sack change sides while held high in the air)."""
    z = p.z
    for tz, zz in getattr(p, "zf", ()):
        if t >= tz:
            z = zz
    return z


def box_faces(cx, cy, L, wd, yaw, th, sh, off=0.0):
    """A plank (L long, wd wide, th thick) lying flat, its middle at screen (cx, cy), turned by yaw in the ground
    plane -> (top, front, side) screen polygons."""
    a = math.radians(yaw)
    d1 = (math.cos(a), math.sin(a))                              # along its length: (x, depth)
    d2 = (-math.sin(a), math.cos(a))

    def scr(u, v):
        u += off
        x = u * d1[0] + v * d2[0]
        d = u * d1[1] + v * d2[1]
        return cx - sh + x + DV[0] * d, cy + DV[1] * d
    c = [scr(-L / 2, -wd / 2), scr(L / 2, -wd / 2), scr(L / 2, wd / 2), scr(-L / 2, wd / 2)]
    deps = [(-L / 2) * d1[1] + (-wd / 2) * d2[1], (L / 2) * d1[1] + (-wd / 2) * d2[1],
            (L / 2) * d1[1] + (wd / 2) * d2[1], (-L / 2) * d1[1] + (wd / 2) * d2[1]]
    top = c
    # the front face: the edge nearest us (least depth); the side face: the edge on the right
    edges = [(i, (i + 1) % 4) for i in range(4)]
    near = min(edges, key=lambda e: deps[e[0]] + deps[e[1]])
    right = max(edges, key=lambda e: c[e[0]][0] + c[e[1]][0])
    def face(e):
        p, q = c[e[0]], c[e[1]]
        return [p, q, (q[0], q[1] + th), (p[0], p[1] + th)]
    return top, face(near), face(right) if right != near else None


def draw_plank(pg, q, sh, L=None):
    top, front, side = box_faces(q["x"], q["y"], q.get("L", 220.0) if L is None else L, 86.0, q.get("yaw", 0.0),
                                 PLANK_TH, sh, q.get("off", 0.0))
    if side is not None:
        pg.flat(smooth(side, closed=True) if False else _poly(side), tone(HW.WOOD, -0.18))
    pg.flat(_poly(front), tone(HW.WOOD, -0.1))
    pg.shape(_poly(top), tone(HW.WOOD, 0.06), 0.06)
    pg.stroke(_poly(top), tone(HW.WOOD, -0.2), 1.2, 0.5)


def _poly(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def draw_rack(pg, x0, x1, top, foot, sh, stop, notch):
    """A saw rack (a sawhorse): its top bar, a stop block at one end, a notch for the trim, two A-frame legs."""
    X0, X1 = x0 - sh, x1 - sh
    for lx in (X0 + 24, X1 - 24):
        for d in (-1, 1):
            pg.shape(tube([(lx, top + 6), (lx + d * 26, foot)], 6, 6), HW.WOOD_D, 0.08)
    pg.shape(rrect(X0, top, X1, top + 16, 3), tone(HW.WOOD, -0.22), 0.1)   # r33: darker than the boards laid on it
    # the stop block (r5: "no stop block can be seen"): a chunky block pegged to the bar, taller than a plank stack
    pg.shape(rrect(stop - sh - 22, top - 48, stop - sh, top + 4, 3), HW.WOOD_D, 0.12)
    for py in (top - 34, top - 8):
        pg.flat(oval(stop - sh - 11, py, 3.2, 3.2), tone(HW.WOOD_D, -0.3))
    pg.flat(rrect(notch - sh - 2, top, notch - sh + 2, top + 9, 1), (110, 80, 56))


LUMP_WOB = 6.0                      # r21: how far his tentacle tip circles as it rolls a lump round (px)
LUMP_SPIN = 7.0                     # ...and how fast the lump turns as it's rolled (rad/s)
LUMP_ROLL_AT = (118.0, 862.0)        # (r34: out at his right side, was (50, 845)) (r30, round 29 part 2: at -30/872 the lump he still held in slot 0 hid it) r29: where each lump is held up in front of him (dx from his middle, y) to be rolled
LUMP_ROLL_T, LUMP_ROLL_DX, LUMP_ROLL_N = 4.2, 58.0, 3.0   # r46 (round 45 part 2 must-fix "the lumps go round with no
#                                   # rolling seen"): longer strokes (34 -> 58 px: it turns ~35 deg each way, not ~20) over 4.2 s
#                                   # (was 3.4), and creases on it that turn with it and smooth away as it's rolled. r36 (round 35 part 2 must-fix "each lump rounds
#                                   # itself in ~0.8 s while the tip just holds it"): longer, wider strokes (was 2.6 s,
#                                   # 26 px, 2.5), and it rounds evenly all through the rolling (lump_rough)
#   # r29: how long, how far his top tentacle rolls it (px), how often
# r34: 2.0/16 -> 2.6/26, and it is held out at his right side (LUMP_ROLL_AT was (50, 845), in front of his body)
LUMP_PASS = (40.0, 858.0)           # r34: where the lump is handed to his right tentacle (dx from his middle, y)


LUMP_CREASES = ((0.5, 0.5, 1.1), (2.4, 0.58, 0.9), (4.1, 0.42, 1.0))   # r46: (angle, how far out, arc) of a lump's creases


def lump_roll_d(t, r0, r1):
    """r34: how far the top tentacle's tip has pushed a lump being rolled (the lump rolls half as far under it)."""
    return LUMP_ROLL_DX * math.sin(2 * math.pi * LUMP_ROLL_N * _seg(t, r0, r1))


def lump_roll_pt(x, y, t, w):
    """r21: where a lump is held while his tentacle tip rolls it round: little circles, easing in and out (still at
    both ends of the roll, so nothing jumps)."""
    u = _seg(t, *w)
    a = LUMP_WOB * math.sin(math.pi * u)
    f = 2 * math.pi * 2.2 * t
    return dict(x=x + a * math.cos(f), y=y + 0.6 * a * math.sin(f))


def lump_rough(p, t):
    """r21: how rough lump p still is (1 torn off the heap, 0 rolled round) and how far it has turned."""
    w = getattr(p, "roundw", None)
    if w is None:
        return 0.0, 0.0
    return 1.0 - _seg(t, *w), LUMP_SPIN * (min(max(t, w[0]), w[1]) - w[0])   # (r36: evenly, not eased)


DOME_BOW = 9.0                      # r38: how far a ring's front bows down from its sides (the oblique view; see dome_pt)
RINGS = 6                           # the oven's rope coils (r9: one from each lump, six lumps)
SMOOTH_COL = tone(HW.CLAY, -0.02)   # r12: a smoothed ring
INSIDE_COL = mix(tone(HW.CLAY, -0.3), (60, 40, 34), 0.6)   # r12: the back wall's inside, in the door's shadow
SMOOTH_S = 6.0                      # (r30: each half, 6 s: strokes that overlap) r12: seconds to smooth the dome, foot to top
SMOOTH_W = 2.2                      # r30: the tips' side to side rate (rad/s)
SMOOTH_STROKE = 40.0                # r30: how wide a band one stroke of a tip smooths (px) (r33: 60 -> 40, about its
                                    # curl: with the old band and fringe the first pass smoothed most of the left half too)
SMOOTH_IN = 26.0                    # r33: the curl's middle is kept this far inside the dome's outline (its radius)
SMOOTH_LV0 = 0.2                    # r33: the curl starts this far up the dome (its 60 px band still takes in the foot):
                                    # every point stays above the tentacle's root (SMOOTH_ROOT), so the rig wraps the tip
                                    # the same way all through (below its root it wraps it the other way: a flip)
SMOOTH_LV1 = 0.85                   # r38 (round 38 part 3 must-fix: reach): the strokes go this high (was 0.95); the stroke's
                                    # band (SMOOTH_STROKE) still takes in the dome's top
SMOOTH_ROOT = 125.0                 # r33: the smoothing tentacles come from his body's lower edge (this far below its
                                    # middle, monster units), working low
SMOOTH_CURL = (17.0, -6.0)          # r33: the tentacle's end point from the middle of its wrapped tip (probe97: the rig
                                    # wraps it left of and below the point it is drawn to, about 25 px round)
HANS_SMOOTH_R = 3800.0              # r47 (advisor FK0021 r46 must-fix "his body covers the dome's right side while he smooths it"): 3780 -> 3800. r38: where he stands to smooth the right half (was where he laid the coils, 3810)
HANS_SMOOTH = 3355.0                # r42 (round 41 part 3 must-fix "the left coils vanish behind his fin"): 3395 -> 3355, his fin clear of the dome. r38: 3375 -> 3395 (round 38 part 3: reach). r30: where Hans stands to smooth the dome's left half (<= 227 px) (r36, round 35
#                                   # part 3 must-fix "his head and body cover the dome while he smooths it": at 3700
#                                   # he stood in front of it; now left of it, his body clear of its foot at 3490)
LAY_S = 3.6                         # seconds to lay one ring (r11: 2.4 read as a band appearing at once)
COIL_HANG_DX = 120.0                # r43: where a rolled coil hangs from his tip on its way up (clear of the oven's right side)
ROPE_L, ROPE_R = 130.0, 15.0        # a clay lump rolled out between two tentacles: the rope's length, half-thickness


def rope_pts(q):
    """The ends of a clay lump rolled (part way) into a rope (round 4: "the balls become rows by themselves"): roll
    0 a ball .. 1 a rope, rem how much of it is still unlaid, ang its direction, c 0 the rope starts at (x, y) .. 0.5
    centred on it."""
    L = q.get("len", ROPE_L) * q.get("roll", 0.0) * q.get("rem", 1.0)
    a = math.radians(q.get("ang", 0.0))
    c = q.get("c", 0.5)
    s0 = (q["x"] - c * L * math.cos(a), q["y"] - c * L * math.sin(a))
    return s0, (s0[0] + L * math.cos(a), s0[1] + L * math.sin(a)), L


def rope_at(q, f):
    """The point f (0..1) along the rope from its start."""
    (ax, ay), (bx, by), _ = rope_pts(q)
    return ax + (bx - ax) * f, ay + (by - ay) * f


def rope_top(q, f):
    """r13: the top of the rope (or ball) at f along it, where a tentacle tip presses as it rolls it on the slab."""
    x, y = rope_at(q, f)
    rr = 16.0 * q.get("s", LUMP_S)
    rr += (ROPE_R - rr) * q.get("roll", 0.0)
    return x, y - 0.8 * rr


def ring_of(i, u):
    """(ring, across 0..1) where lump i's rope end is, u of the way through laying it (r9: one ring per lump, the
    even ones laid left to right, the odd ones back right to left, each on top of the last)."""
    return i, 0.02 + 0.96 * u                     # r19: every ring laid from the left, Hans lowering the rope by
                                                  # its right end (he stands right of the dome)


def rope_ang(i, u=1.0):
    """The direction of the rope as ring i is laid (from its held right end down to where it meets the course):
    r19 (part 2 must-fix "each coil shrinks into his curled tentacle"), he holds its right end up and to the right and
    lowers it, so it settles onto the wall from the left, the course appearing exactly where it touches. r40: the
    rings at the door's height held higher, so the rope in his tentacle rises up out of the doorway over its corner
    rather than lying along across the opening: steep (70 degrees) at their start, left of the door, 45 once its
    end is behind the jamb (u: how far it's laid)."""
    if door_ring(i):
        return -180.0 - (70.0 - 25.0 * smoothstep(min(1.0, u / 0.25)))
    return -180.0 - 28.0


JAMB_DX = 58.0                      # the door's side stones: from the oven's middle (door_stones_clip)
LINTEL_TOP = HW.FLOOR - 132.0       # the lintel's top (door_stones_clip)


def door_ring(k):
    """r40: is ring k (one per lump) at the door's height (its middle below the lintel)?"""
    return (k + 0.5) / RINGS * HW.OVEN_H < OVEN_BASE_Y - DOOR_TOP


def door_stones_clip(sh):
    """The door's two side stones and lintel: the clay is laid up against them and never over them."""
    pth = skia.Path()
    for dx in (-58.0, 58.0):
        pth.addRRect(skia.RRect.MakeRectXY(skia.Rect(HW.OVEN_X + dx - 11 - sh, HW.FLOOR - 109, HW.OVEN_X + dx + 11 - sh,
                                                     HW.FLOOR - 51), 6, 6))
    pth.addRRect(skia.RRect.MakeRectXY(skia.Rect(HW.OVEN_X - 71 - sh, HW.FLOOR - 132, HW.OVEN_X + 71 - sh,
                                                 HW.FLOOR - 112), 6, 6))
    return pth


def draw_oven(pg, P, t, sh):
    """The oven, as far as it's built: the clay coils (each laid from the left as Hans goes round), smoothed into one
    dome, the door's stones (drawn as props), the fire inside, soot over the door."""
    if not hasattr(P, "coils") or abs(HW.OVEN_X - sh - W / 2) > W:
        return
    c = pg.c
    front = P.smooth_front(t)
    swept = P.smooth_swept(t, sh) if hasattr(P, "smooth") and t >= P.smooth[0] else None
    # r32 (round 31 part 3 must-fix "a smooth patch with a hard diagonal edge"): the coils fade into the smoothed part
    # over a soft fringe round it, not a cut line
    fringe = [(P.smooth_swept(t, sh, 20.0), 0.3), (P.smooth_swept(t, sh, 10.0), 0.45)] if swept is not None else []   # (r33: was 36/18)
    mouth = door_rect(sh)
    rc = mix(HW.CLAY, HW.CLAY_SOFT, ease(t, *P.soft) if hasattr(P, "soft") else 0.0)   # r14: the coils are the
    # rope's own clay colour ("dark-brown rod, terracotta ring")
    c.save()
    c.clipPath(mouth, skia.ClipOp.kDifference, True)
    c.clipPath(door_stones_clip(sh), skia.ClipOp.kDifference, True)
    back = []                                                      # the coils laid so far (the oven's back wall)
    ends = []
    for k in range(RINGS):                                         # each rope coil, as far as it's been laid
        i, half = k, k % 2                                         # (r9: one ring per lump)
        if i >= len(P.coils):
            break
        uu = _seg(t, *P.coils[i])
        if uu <= 0:
            continue
        a, b = k / RINGS, (k + 1) / RINGS
        if k == RINGS - 1:
            b = 0.97
        u0, u1 = 0.0, 0.02 + 0.96 * uu                             # r19: all laid from the left
        vs = np.linspace(u0, u1, 16)
        lo = [(x - sh, y) for x, y in (P.dome_pt(v, a) for v in vs)]
        hi = [(x - sh, y) for x, y in (P.dome_pt(v, b) for v in vs)]
        col = mix(rc, tone(rc, -0.06), 0.5 * (k % 2))
        sk = 0.0 if t < P.smooth[0] else (1.0 if swept is None else 0.0)   # r30: smooth only where stroked
        pg.shape(smooth(lo + hi[::-1], closed=True), col, 0.08 * (1 - sk))
        if sk > 0:                                                 # (over its seam with the ring below too)
            pg.flat(smooth([(x, y + 2.0) for x, y in lo] + hi[::-1], closed=True), mix(rc, tone(rc, -0.06), 0.25), sk)
            # (r26 part 2 must-fix "the whole dome switches to a lighter colour": the coils' own clay, just even)
        back.append([(x - sh, y) for x, y in (P.dome_pt(v, a, True) for v in vs)] +
                    [(x - sh, y) for x, y in (P.dome_pt(v, b, True) for v in vs[::-1])])   # r38: its back, further in
        end_v = u1                                                 # the rope's rounded end, where it meets it
        if uu < 0.999:
            (ex, ey), (fx, fy) = P.dome_pt(end_v, a), P.dome_pt(end_v, b)
            r_ = max(3.0, (ey - fy) / 2)
            pg.shape(oval(ex - sh, (ey + fy) / 2, r_, r_), col, 0.08)
            (ex2, ey2), (fx2, fy2) = P.dome_pt(end_v, a, True), P.dome_pt(end_v, b, True)
            ends.append((ex2 - sh, (ey2 + fy2) / 2, r_, k))       # (r38: through the door it's the back's end)
        if sk < 1:                                                 # the round top of each coil and its seam
            if len(hi) >= 2:
                # r41 (round 40 part 3 must-fix "the left half's grooves vanish before he rubs it"): they were
                # there, but too faint to read at a glance; a clearer lit top and a darker seam
                pg.stroke(smooth([(x, y + 4) for x, y in hi], closed=False), tone(rc, 0.16), 3.4,
                          0.85 * (1 - sk))
                pg.stroke(smooth(lo, closed=False), tone(rc, -0.28), 2.6, 0.85 * (1 - sk))
        if swept is not None and t >= P.smooth[0]:                # r30: smoothed where the tips have stroked it
            for fp, fa in fringe:
                c.save()
                c.clipPath(fp, skia.ClipOp.kIntersect, True)
                pg.flat(smooth([(x, y + 2.0) for x, y in lo] + hi[::-1], closed=True), mix(rc, tone(rc, -0.06), 0.25), fa)
                c.restore()
            c.save()
            c.clipPath(swept, skia.ClipOp.kIntersect, True)
            pg.flat(smooth([(x, y + 2.0) for x, y in lo] + hi[::-1], closed=True), mix(rc, tone(rc, -0.06), 0.25))
            c.restore()
    if front > 0:                                                  # finger marks where it's been smoothed
        rs = np.random.default_rng(14)
        for k in range(9):
            ux, lv = rs.uniform(0.2, 0.8), rs.uniform(0.08, 0.85)
            a_ = min(max((front - lv) * RINGS, 0.0), 1.0)
            x, y = P.dome_pt(ux, lv)
            if swept is not None and not swept.contains(x - sh, y):   # (r30: only where stroked)
                a_ = 0.0
            if a_ > 0:
                pg.stroke(skia.Path().moveTo(x - sh - 9, y).quadTo(x - sh, y - 4, x - sh + 9, y), tone(HW.CLAY, -0.1),
                          2.0, 0.5 * a_)
    c.restore()
    if t >= P.coils[0][0]:                                         # inside the door: dark, then the fire
        # (part 2 review: "the doorway goes dark before a wall or back exists") - only as far up as the coils behind
        # it have been laid, ring by ring; the whole opening once the dome is one smooth piece
        # r11 (part 2 must-fix: "the dark half-oval interior appears with it"): through the door it's the inside
        # of the back wall, the same clay coils in shade, growing with the rope; dark only once the dome is closed
        c.save()
        c.clipPath(mouth, skia.ClipOp.kIntersect, True)
        c.clipPath(door_stones_clip(sh), skia.ClipOp.kDifference, True)
        # r37 (round 36 part 2 must-fix "the laid coil turns into a flat dark band"): through the door, the back of
        # each coil is the same round rope in shade (its top, its seam, its end where it's still being laid); the
        # inside only darkens once the dome is closed over it
        # r38 (round 37 part 3 must-fix "the doorway fades dark by itself after the last coil"): it darkens as each
        # coil goes on over it (the higher rings roof it more), only while that coil is being laid
        dk = 0.4 + 0.6 * sum((k + 1) ** 2 * ease(t, a_, b_) for k, (a_, b_) in enumerate(P.coils[:RINGS])) /             sum((k + 1) ** 2 for k in range(RINGS))                # (r38: the ring's inside is in its shade)
        if hasattr(P, "smooth"):
            dk = max(dk, ease(t, P.smooth[0], P.smooth[0] + 2.0))
        for k, poly in enumerate(back):                            # (r12: one shadowed look, before and after
            shade = mix(tone(rc, -0.2 - 0.04 * (k % 2)), mix(INSIDE_COL, (60, 40, 34), 0.15 * (k % 2)), dk)
            pg.flat(smooth(poly, closed=True), shade)
            n_ = len(poly) // 2                                    # the door is an opening all along)
            pg.stroke(smooth(poly[:n_], closed=False), (58, 38, 32), 1.6, 0.5)
            if dk < 1:                                             # the rope's round top, lit a little
                pg.stroke(smooth([(x, y + 4) for x, y in poly[n_:][::-1]], closed=False), tone(rc, -0.04), 3.0,
                          0.7 * (1 - dk))
        for ex_, ey_, r_, k in ends:                               # the end of the coil still being laid
            pg.flat(oval(ex_, ey_, r_, r_), tone(rc, -0.2 - 0.04 * (k % 2)))
            pg.stroke(oval(ex_, ey_, r_, r_), tone(rc, -0.35), 1.5, 0.6)
        c.restore()
        f = P.fire(t)
        if f > 0:
            for k in range(5):
                fl = 0.6 + 0.4 * math.sin(t * (7 + k) + k * 1.7)
                x = OVEN_MOUTH[0] - sh - 18 + 9 * k
                pg.flat(smooth([(x - 7, HW.FLOOR - 48), (x + 1, HW.FLOOR - 48 - 30 * fl * f), (x + 7, HW.FLOOR - 48)]),
                        (238, 150 + 30 * (k % 2), 60), 0.9 * f)
        e = embers(P, t)                                           # the coals' warm glow on the oven floor
        if e > 0:
            pg.glow(OVEN_MOUTH[0] - sh, HW.FLOOR - 52, 46, "#ff9a4a", 0.55 * e)
            for k in range(6):
                fl = 0.75 + 0.25 * math.sin(t * (2.1 + 0.37 * k) + 2.3 * k)
                pg.flat(oval(OVEN_MOUTH[0] - sh - 25 + 10 * k, HW.FLOOR - 49 - 2 * (k % 2), 6.5, 3.6),
                        (236, 96 + 40 * (k % 3) * fl, 44), 0.85 * e * fl)
        soot = ease(t, P.fire_t[1], P.fire_t[1] + 40.0) if hasattr(P, "fire_t") else 0.0
        if soot > 0:
            pg.flat(oval(OVEN_MOUTH[0] - sh, DOOR_TOP - 24, 40, 20), (70, 58, 54), 0.5 * soot, blur=8)


def fire(P, t):
    """The fire: lit by Glo's light, then it burns down to glowing embers while the bread is shaped (the bread goes
    in over embers, never over flames)."""
    f = ease(t, *P.fire_t) if hasattr(P, "fire_t") else 0.0
    if hasattr(P, "peel_keys") and "m_in" in P.peel_keys:
        f *= 1.0 - 0.7 * ease(t, P.peel_keys["m_in"][0] - 12.0, P.peel_keys["m_in"][0] - 2.0)
    return f


Plan.fire = fire


def embers(P, t):
    """The glowing coals the sticks burn down to: they keep the oven hot through the baking (r2 review: the fire
    died by itself and the bread went into a cold, dark oven), and fade long after the bread is out."""
    if not hasattr(P, "fire_t"):
        return 0.0
    e = ease(t, P.fire_t[0] + 1.0, P.fire_t[1] + 8.0)
    if hasattr(P, "bake_t"):
        e *= 1.0 - 0.6 * ease(t, P.bake_t[1] + 10.0, P.bake_t[1] + 60.0)
    return e


def char(P, t):
    """How far the sticks have burnt: from when the fire is lit to when the bread goes in (then they're coals)."""
    if not hasattr(P, "fire_t"):
        return 0.0
    end = P.peel_keys["m_in"][0] - 2.0 if hasattr(P, "peel_keys") and "m_in" in P.peel_keys else P.fire_t[1] + 60.0
    return ease(t, P.fire_t[0] + 0.5, end)


def draw_vprop(pg, P, p, q, sh, t):
    """The village's props."""
    k = p.kind
    X = q["x"] - sh
    if k == "rock":
        pg.shape(oval(X, q["y"], 30, 18), HW.STONE, 0.14)
    elif k == "slab":
        pg.shape(rrect(X - 100, q["y"] - 9, X + 100, q["y"] + 9, 7), HW.STONE_D, 0.12)
    elif k == "jamb":                                              # (r37: a shade darker: solid, not faded)
        a_ = q.get("ang", 0.0)                                     # r41: lies flat in the stack, stood up as laid
        if a_:
            pg.c.save(); pg.c.rotate(a_, X, q["y"])
        pg.shape(rrect(X - 10, q["y"] - 28, X + 10, q["y"] + 28, 6), tone(HW.STONE, -0.12), 0.16)
        if a_:
            pg.c.restore()
    elif k == "lintel":
        pg.shape(rrect(X - 70, q["y"] - 9, X + 70, q["y"] + 9, 6), tone(HW.STONE, -0.12), 0.16)
    elif k == "lump":
        r = 16.0 * max(q.get("s", 1.0), 0.15)
        soft = ease(t, *P.soft) if hasattr(P, "soft") else 0.0
        col = mix(HW.CLAY, HW.CLAY_SOFT, soft)
        roll = q.get("roll", 0.0)
        if roll <= 0:
            rough, spin = lump_rough(p, t)
            if hasattr(p, "roll_top"):                             # r29: turned by the tentacle rolling its top
                r0_, r1_ = p.roll_top
                spin = -0.5 * lump_roll_d(t, r0_, r1_) / r              # (r34: as far as it rolls along)
            if rough <= 0.01:
                pg.shape(oval(X, q["y"], r * 1.2, r), col, 0.12)
                pg.flat(oval(X - 0.35 * r, q["y"] - 0.4 * r, 0.32 * r, 0.18 * r), tone(col, 0.1), 0.5)   # (r46)
            else:                                                  # r21: torn off the heap, rolled round
                pts_ = []
                for j in range(14):
                    a = 2 * math.pi * j / 14
                    b = a + spin
                    k_ = 1.0 + rough * (0.2 * math.sin(3 * b + 0.7) + 0.11 * math.sin(5 * b + 2.1) +
                                        0.07 * math.sin(7 * b + 4.0))
                    pts_.append((X + r * 1.2 * (1.0 + 0.12 * rough) * k_ * math.cos(a),
                                 q["y"] + r * (1.0 - 0.1 * rough) * k_ * math.sin(a)))
                pg.shape(smooth(pts_, closed=True), col, 0.12)
                # r46 (round 45 part 2 must-fix "rounded with no rolling seen"): finger creases in the torn clay turn
                # with it as it rolls (the same way as its rough outline) and fade out as the rolling smooths it
                for a0_, rr_, ln_ in LUMP_CREASES:
                    a_ = a0_ - spin
                    cpath = skia.Path()
                    for j in range(7):
                        u_ = a_ + ln_ * (j / 6.0 - 0.5)
                        cx_ = X + r * 1.2 * rr_ * math.cos(u_)
                        cy_ = q["y"] + r * rr_ * math.sin(u_)
                        if j == 0:
                            cpath.moveTo(cx_, cy_)
                        else:
                            cpath.lineTo(cx_, cy_)
                    pg.stroke(cpath, tone(col, -0.3), max(1.4, 0.14 * r), 0.85 * min(1.0, rough * 1.4))
                hl_ = (X - 0.35 * r, q["y"] - 0.4 * r)              # (the light on its top stays put: it's the
                pg.flat(oval(hl_[0], hl_[1], 0.32 * r, 0.18 * r), tone(col, 0.1), 0.5)   # clay that turns)
        else:                                                      # rolled out into a rope (and laid, as it shrinks)
            (ax, ay), (bx, by), L = rope_pts(q)
            rr = (r + (ROPE_R - r) * roll) * min(1.0, q.get("rem", 1.0) / 0.05)
            if L < 2.0:
                pg.shape(oval((ax + bx) / 2 - sh, (ay + by) / 2, rr, rr), col, 0.12)
            else:
                nx, ny = -(by - ay) / L, (bx - ax) / L               # a soft clay rope sags a little, never a stick
                if ny < 0:
                    nx, ny = -nx, -ny
                sg = 0.2 * L * (1.0 - min(1.0, q.get("flat", 0.0)))               # (lying on the slab: straight; r14: soft, it droops)
                pts_ = [(ax + (bx - ax) * f + nx * sg * math.sin(math.pi * f) - sh,
                         ay + (by - ay) * f + ny * sg * math.sin(math.pi * f)) for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
                pg.shape(tube(pts_, rr, rr * 0.92), col, 0.06)
                if "spin" in q and q.get("rem", 1.0) > 0.99:       # r13: marks on it turning as it's rolled
                    for k_ in range(2):
                        ph = 2 * math.pi * (q["spin"] + k_ * 0.5)
                        if math.sin(ph) > 0:
                            o = rr * 0.8 * math.cos(ph)
                            pg.stroke(smooth([(x_ + nx * o, y_ + ny * o) for x_, y_ in pts_[1:4]], closed=False),
                                      tone(col, -0.16), 1.6, min(1.0, math.sin(ph) * 2))
    elif k == "rpeg":                                              # r41: the roof's peg (end on once pushed in)
        a = math.radians(q["ang"])
        e = q.get("end", 0.0)
        L_ = 17.0 * (1.0 - e) + 0.5 * e                            # (turned end on, towards us, as it goes in)
        seg = skia.Path().moveTo(X - L_ * math.cos(a), q["y"] - L_ * math.sin(a)).lineTo(
            X + L_ * math.cos(a), q["y"] + L_ * math.sin(a))
        pg.stroke(seg, (98, 68, 46), 11.0 + 2.0 * e)
        pg.stroke(seg, (176, 132, 88), 8.0 + 2.0 * e)
        if e > 0.3:                                                # its round head
            pg.stroke(skia.Path().addCircle(X, q["y"], 2.6), (98, 68, 46), 1.4, min(1.0, (e - 0.3) / 0.5))
    elif k == "stick":
        a = math.radians(q["ang"])
        ch = char(P, t) if p.holder_at(t) is None and abs(q["x"] - OVEN_MOUTH[0]) < 40 else 0.0
        L_ = 30.0 * (1 - 0.45 * ch)                                # burning down: shorter, black, glowing
        seg = skia.Path().moveTo(X - L_ * math.cos(a), q["y"] - L_ * math.sin(a)).lineTo(
            X + L_ * math.cos(a), q["y"] + L_ * math.sin(a))
        pg.stroke(seg, mix((128, 92, 62), (44, 32, 30), ch), 6.0 - 1.5 * ch)
        if ch > 0.05:
            pg.stroke(seg, (246, 120, 52), 2.2, min(1.0, 2.5 * ch) * (0.7 + 0.3 * math.sin(t * 3.1 + q["ang"])))
    elif k == "plank":
        draw_plank(pg, q, sh)
    elif k == "plank_offcut":
        hw_ = TRIM_OFF / 2 - 2                                     # r13: six short plank ends, a little pile
        for j in range(6):
            pg.shape(rrect(X - hw_ + 3 * j, q["y"] - 6 + 12 * j * 0.3, X + hw_ + 3 * j, q["y"] + 4 + 12 * j * 0.3, 2),
                     HW.WOOD, 0.08)
    elif k == "jug":
        c = pg.c
        c.save()
        c.rotate(q["ang"], X, q["y"])
        pg.shape(smooth([(X - 14, q["y"] - 40), (X + 14, q["y"] - 40), (X + 20, q["y"] - 10), (X + 14, q["y"]),
                         (X - 14, q["y"]), (X - 20, q["y"] - 10)]), (176, 110, 90), 0.12)
        pg.stroke(skia.Path().moveTo(X + 16, q["y"] - 34).quadTo(X + 34, q["y"] - 24, X + 18, q["y"] - 10),
                  (150, 92, 76), 4.0)
        c.restore()
        if hasattr(P, "water") and P.water[0] <= t < P.water[1]:
            u = _seg(t, *P.water)
            fl = min(1.0, u / 0.12, (1.0 - u) / 0.15)              # r42: a clear ribbon (was a 3 px hairline)
            wob = 1.5 * math.sin(t * 23.0)
            ca, sa = math.cos(math.radians(q["ang"])), math.sin(math.radians(q["ang"]))
            lx, ly = X - 14 * ca + 40 * sa, q["y"] - 14 * sa - 40 * ca   # out over its low lip, then down
            ex, ey = flour_x(P, t) - sh, DOUGH[1] - 21.0            # into the wet well in the heap's top
            st = skia.Path().moveTo(lx, ly).quadTo(lx - 5 + wob, ly + 8, ex, ey)
            pg.stroke(st, (120, 170, 205), 8.0, 0.85 * fl)
            pg.stroke(st, (225, 240, 250), 3.0, 0.8 * fl)
            for j in range(3):                                     # little splashes where it lands
                a_ = t * 9.0 + j * 2.1
                pg.flat(oval(ex + 12 * math.cos(a_), ey - 2 - 6 * abs(math.sin(a_)), 3.0, 3.0),
                        (225, 240, 250), 0.8 * fl)
    elif k == "peel":
        draw_peel(pg, P, q, sh)
    elif k == "loaf":
        shp = q.get("shape", 1.0)
        bk = q.get("bake", 0.0)
        col = mix(HW.BREAD_DOUGH, HW.BREAD, bk)
        split = q.get("split", 0.0)
        sc_ = q.get("s", 1.0)
        w, h = LOAF_W * sc_ * (1 + 0.12 * bk), LOAF_H * sc_ * (1 + 0.12 * bk)
        if shp < 0.999 and split <= 0:                             # a slice of the dough, rolling round
            mp = loaf_morph(P, X, q["y"], int(q.get("piece", 0)), shp, w, h, rot=q.get("rock", 0.0))
            pg.shape(mp, col, 0.12)
            if shp > 0.3:                                          # r20 (part 3 must-fix "the outline pops on as he
                pg.stroke(mp, tone(col, -0.32), 1.6, 0.85 * ((shp - 0.3) / 0.7) ** 2)   # lets go"): it firms up
                                                                   # as it's rolled
        elif split > 0:
            for d in (-1, 1):
                pg.shape(oval(X + d * (w * 0.5 + 6 * split), q["y"] - h * 0.8, w * 0.55, h), col, 0.12)
        else:
            pg.shape(oval(X, q["y"] - h * 0.8, w, h), col, 0.12)
            pg.stroke(oval(X, q["y"] - h * 0.8, w, h), tone(col, -0.32), 1.6, 0.85)   # its own edge: four, not a slab
    elif k == "piece":
        s, r = q.get("s", 1.0), q.get("r", 10.0)                   # r40: the Keepers' pieces are hearty chunks
        pg.shape(oval(X, q["y"], r * s, 0.7 * r * s), HW.BREAD, 0.1)
        if r > 12.0:                                               # (golden crust on top, soft crumb under it)
            pg.flat(oval(X - 0.15 * r * s, q["y"] + 0.18 * r * s, 0.55 * r * s, 0.32 * r * s), (238, 214, 160), 0.9)
    elif k == "dough":
        pass


def draw_peel(pg, P, q, sh):
    """The bread peel: its blade (pose x, y is the blade's middle) and its handle out to (hx, hy). Seen from the side
    (om 0) it lies flat along the screen; pointing into the oven's door (om 1) the blade is seen end-on, a little
    smaller the further in it goes (sc), and once it's through the door (dz >= 0.5) only what shows in the door is
    drawn: it's behind the oven's front wall. The handle comes out of the door towards us, so it's always in front."""
    fl = q.get("flat", 0.0)                                        # r31: lying flat on the table, its paddle face
    X, Y = q["x"] - sh, q["y"] + PEEL_FLAT_DY * fl                 # up (seen from above in the oblique view)
    om, dz, sc = q.get("om", 0.0), q.get("dz", 0.0), q.get("sc", 1.0)
    hx, hy = q.get("hx", q["x"] + 150.0) - sh, q.get("hy", q["y"]) + PEEL_FLAT_DY * fl
    bw = (50.0 + (44.0 - 50.0) * om) * sc
    bh = (5.0 + PEEL_FLAT_BH * fl) * sc
    ux, uy = hx - X, hy - Y
    L = math.hypot(ux, uy) or 1.0
    ux, uy = ux / L, uy / L
    a = (X + ux * bw * (1 - om), Y + uy * bw * (1 - om) + bh * om)  # the handle starts at the blade's near edge
    pth = skia.Path()
    pth.moveTo(*a)
    pth.lineTo(hx, hy)
    c = pg.c
    tilt = q.get("tilt", 0.0)                                      # r14: leaning (blade down), turned about the blade
    if abs(tilt) > 1e-3:
        c.save()
        c.rotate(tilt, X, Y)
    if dz >= 0.55:                                                 # r16: through the door's plane (not before:
        c.save()                                                   # it comes up from under the door)
        c.clipPath(door_rect(sh), skia.ClipOp.kIntersect, True)
    blade = rrect(X - bw, Y - bh, X + bw, Y + bh, (3.0 + 7.0 * fl) * sc)
    pg.shape(blade, tone(HW.WOOD, 0.1 * fl), 0.1)
    if fl > 0.02:                                                  # (r31: a dark rim, so it reads on the planks)
        pg.stroke(blade, HW.WOOD_D, 2.5 * fl)
    if dz >= 0.55:
        c.restore()
    pg.stroke(pth, HW.WOOD_D, 7.0)                                 # r16: a lighter handle with dark edges, so it
    pg.stroke(pth, tone(HW.WOOD, -0.04), 3.6)                      # shows in front of the rack's dark stop block
    if abs(tilt) > 1e-3:
        c.restore()


def _dough_hit(P, x0, y0, c, si, gap=0.8):
    """From (x0, y0) along (c, si) (dough frame, centre (0, 0)): the distance to the dough's edge or to a cut line,
    whichever is nearer. Each cut is the line its blade went through: x = xk + kk * (y - yk)."""
    rx, ry = DOUGH_RX, DOUGH_RY
    a = c * c / rx ** 2 + si * si / ry ** 2
    b = 2 * (x0 * c / rx ** 2 + y0 * si / ry ** 2)
    cc = x0 * x0 / rx ** 2 + y0 * y0 / ry ** 2 - 1
    r = (-b + math.sqrt(max(b * b - 4 * a * cc, 0.0))) / (2 * a)
    for xk, yk, kk, _, _ in getattr(P, "dough_lines", ()):
        xk, yk = xk - DOUGH[0], yk - DOUGH_CY
        den = c - kk * si
        if abs(den) < 1e-6:
            continue
        rr = (kk * (y0 - yk) - (x0 - xk)) / den
        side = (x0 - xk) - kk * (y0 - yk)                            # which side of the cut it starts on
        rr -= gap / max(abs(den), 0.3) * (1 if side < 0 else 1)
        if rr > 0:
            r = min(r, rr)
    return max(r, 0.0)


def slice_centre(P, j):
    """Quarter j's middle (world), between cut j-1 and cut j at the dough's middle height."""
    xs = [-DOUGH_RX] + [ln[0] - DOUGH[0] for ln in getattr(P, "dough_lines", [])] + [DOUGH_RX]
    if len(xs) < 5:
        xs = [-DOUGH_RX, -20.0, 0.0, 20.0, DOUGH_RX]
    return DOUGH[0] + (xs[j] + xs[j + 1]) / 2, DOUGH_CY


def slice_points(P, j, n=72):
    """Quarter j's outline, as cut (dough frame, relative to its middle)."""
    cx, cy = slice_centre(P, j)
    x0, y0 = cx - DOUGH[0], cy - DOUGH_CY
    out = []
    for i in range(n):
        th = 2 * math.pi * i / n
        c, si = math.cos(th), math.sin(th)
        r = _dough_hit(P, x0, y0, c, si)
        out.append((r * c, r * si))
    return out


def draw_sawdust(pg, P, t, sh):
    """A little sawdust falling from the blade as Twigs saws the gear blanks (the cut is happening right there)."""
    draw_stone_dust(pg, P, t, sh)
    for t_on, c0, c1 in getattr(P, "rack_trims", ()):              # r33 (round 32 part 2 must-fix "Twigs saws air,
        if not (t_on + 0.3 <= t < c1 + 0.7):                       # nothing is cut"): a pencil mark across the board
            continue                                               # at the notch, then the kerf opening down through
        X, top = HW.NOTCH_X - sh, HW.RACK_Y - 13.0                 # it under the blade, sawdust falling from it
        if t < c0:
            pg.stroke(skia.Path().moveTo(X, top + 1).lineTo(X, top + 11), tone(HW.WOOD, -0.7),
                      1.6 * ease(t, t_on + 0.3, t_on + 0.7))
        elif t < c1:
            u = _seg(t, c0, c1)
            pg.stroke(skia.Path().moveTo(X, top).lineTo(X, top + 12.0 * u), tone(HW.WOOD, -0.6), 3.2)
        for k in range(12):
            t0 = c0 + (c1 - c0) * k / 12
            v = t - t0
            if 0 <= v < 0.7:
                x = X + 6 * math.sin(k * 2.3) + 12 * v * math.cos(k)
                pg.flat(oval(x, top + 12 + 0.5 * 900 * v * v, 2.6, 2.2), HW.WOOD_END, 1.0 - v / 0.7)
    for d in getattr(P, "discs", ()):
        for kind, (a, b) in d["cuts"]:
            if a <= t < b + 0.7:                                   # r42 (round 42: "no sawdust"): pale, fuller
                x0 = GEAR_CUT[0] - (NOTCH_D * 0.5 if kind == "tooth" else 0.0) - sh   # (at the kerf: a notch's floor)
                for k in range(18):
                    t0 = a + (b - a) * k / 18
                    u = t - t0
                    if 0 <= u < 0.7:
                        x = x0 + 5 * math.sin(k * 2.3) + 14 * u * math.cos(k * 1.7)
                        y = GEAR_CUT[1] + 4 + 0.5 * 900 * u * u
                        if y < HW.FLOOR - 2:
                            pg.flat(oval(x, y, 3.0 + (k % 3) * 0.6, 2.6), (236, 206, 156), 1.0 - u / 0.7)



def twigs_arm_front(pg, x, y, t, a):
    """r13: Twigs' left arm, hand and blade alone (no legs, no body, no other arm), drawn again over the work he
    is sawing, which stands in front of him. The same drawing as zoom_figure.figure, with only his arms attached
    and his body and right side clipped off, so nothing of his legs ever comes along."""
    M = pg.c.getTotalMatrix()
    m = il.Monster("teeth", k=K)
    m.x, m.y, m.newlook = x, y, True
    m.hands, m.saws = True, False
    for k_, v in a.items():
        setattr(m, k_, v)
    m.attach = {"arms": 1.0}
    cv = il.StyleCanvas(pg.W, pg.H, 6, seed=il.Monster.KINDS.index("teeth") + 1)
    cv.eye_scale = 1.15
    cv.c.setMatrix(M)
    m.draw(cv, t, il.Glow())
    if hasattr(pg, "grain_on"):
        pg.grain_on(cv.surface.getCanvas(), x, y, getattr(cv, "bounds", None))
    fig = cv.surface.makeImageSnapshot()
    sway = m.alive * 4 * math.sin(t * 1.1) * K
    bx, cy = x + sway, y - 230 * K - 120 * K + sway * 0.3
    c = pg.c
    c.save()
    c.clipRect(skia.Rect(bx - 2000, cy - 2000, bx, cy + 2000), skia.ClipOp.kIntersect, True)   # his left side
    body = skia.Path()
    body.addOval(skia.Rect(bx - 93 * K, cy - 151 * K, bx + 93 * K, cy + 151 * K))
    c.clipPath(body, skia.ClipOp.kDifference, True)                                          # not his body
    c.resetMatrix()
    c.drawImage(fig, 0, 0)
    c.restore()

def cut_front(pg, P, t, sh):
    """r12 (round 12 must-fixes: the cut lines drew themselves, the blade hidden behind the dough, the plank stack,
    the gear blank and his own leg): while Twigs saws, his hand and blade are drawn again over the work, so the
    blade is always seen in the cut; for the gear blanks the bit of the blank at the blade is drawn over his leg
    first."""
    for c in P.twigs_cuts:
        if not (c["reach"][0] <= t <= c["back"][1]):
            continue
        x, y, a = keeper("teeth", t)
        if not -400 < x - sh < W + 400:
            return
        hd = twigs_hand(P, t, x, y)[0]
        if hd is None:
            return
        if c.get("kind") == "turn":                                # the blank's rim at the blade, over his leg
            for i in range(2):
                p = P.props[f"gear {i}"]
                if not p.alive(t):
                    continue
                q, hd_, mv = p.at(t)
                if abs(q["x"] - (GEAR_CUT[0] - BLANK)) < 4 and abs(q["y"] - GEAR_CUT[1]) < 4:
                    pg.c.save()
                    pg.c.clipRect(skia.Rect(GEAR_CUT[0] - 26 - sh, GEAR_CUT[1] - 120, GEAR_CUT[0] + 80 - sh,
                                            GEAR_CUT[1] + 120), skia.ClipOp.kIntersect, True)
                    draw_any(pg, P, p, q, sh, t)
                    pg.c.restore()
        twigs_arm_front(pg, x - sh, y, t, a)
        return


def draw_trim(pg, P, t, sh):
    """The stop block the planks butt against (standing up above the stack, so it shows), and the saw cut through
    all six at the notch: a kerf down the stack's end from the top as Twigs' strokes go through."""
    if not hasattr(P, "trim_cut") or not (-300 < FR_STOP - sh < W + 300):
        return
    if P.say.get("planks", 1e9) - 1.0 <= t <= getattr(P, "stack_up", 1e9) + 0.5:
        pg.shape(rrect(FR_STOP - 16 - sh, HW.RACK_Y - 84, FR_STOP - 2 - sh, HW.RACK_Y + 2, 3), tone(HW.WOOD, -0.25),
                 0.06)
    c0, c1 = P.trim_cut
    if c0 <= t < c1:                                               # r12: along the blade's own line (it slants),
        u = (t - c0) / max(c1 - c0, 1e-6)                          # opening down from the top under the blade
        kk, ym = P.trim_line
        yf = HW.RACK_Y - 6.0 - PLANK_DY * 5 + 43.0 * -DV[1]        # the top plank's near top edge
        top, bot = yf, HW.RACK_Y - 6.0 + 43.0 * -DV[1] + PLANK_TH
        yb = top + (bot - top) * u
        xk = FR_NOTCH + kk * (yf - ym) - sh                        # r13: the slot across the top face, front to back
        pg.stroke(skia.Path().moveTo(xk, yf).lineTo(xk + DV[0] * 86.0, yf + DV[1] * 86.0), tone(HW.WOOD, -0.6), 3.6)
        pg.stroke(skia.Path().moveTo(FR_NOTCH + kk * (top - ym) - sh, top).lineTo(FR_NOTCH + kk * (yb - ym) - sh, yb),
                  tone(HW.WOOD, -0.55), 3.6)
        for k in range(14):                                        # r13: sawdust from the cut, falling to the path
            t0 = c0 + (c1 - c0) * k / 14
            v = t - t0
            if 0 <= v < 0.7:
                x = FR_NOTCH + kk * (yb - ym) - sh + 8 * math.sin(k * 2.3) + 14 * v * math.cos(k)
                pg.flat(oval(x, yb + 4 + 0.5 * 900 * v * v, 2.8, 2.3), HW.WOOD_END, 1.0 - v / 0.7)


LOAF_TIP_DY = 24.0                  # r38 (round 37 part 3 must-fix "the piece turns into a loaf, the tentacle never
                                    # rolls it"): the tip down on the piece's top (was 30: hovering over it), drawn over it
ROLL_N, ROLL_PER = 4, 0.85           # Hans rolls each dough piece round in this many strokes, this long each (r6)


def roll_k(t, r0):
    """How many rolling strokes are done (0..ROLL_N, fractional), the tentacle tip landing first (0.5 s)."""
    return min(max((t - r0 - 0.5) / ROLL_PER, 0.0), float(ROLL_N))


def roll_pose(t, r0, x_r):
    """A dough piece rolled under Hans' tentacle: back and forth by its spot, rocking with each stroke; it rounds on
    each push (the first 60% of the stroke) and holds as the tip comes back."""
    k = roll_k(t, r0)
    n = math.floor(k)
    f = k - n
    shape = (n + smoothstep(min(1.0, f / 0.6))) / ROLL_N if n < ROLL_N else 1.0
    return dict(x=x_r + 7.0 * math.sin(2 * math.pi * k), shape=shape, rock=15.0 * math.sin(2 * math.pi * k))   # r14:
                                                                   # rocks further, so each stroke reads


def loaf_morph(P, X, y, j, s, w, h, n=72, rot=0.0):
    """Dough quarter j (exactly as the blade cut it: between the cut lines, inside the kneaded dough's oval) rolled s
    of the way (0..1) to a round loaf (half sizes w, h). Each outline point moves straight from the slice to the
    loaf, so it changes shape smoothly under Hans' tentacle, never all at once."""
    sp = slice_points(P, j, n)
    c0 = (X, y - DOUGH_RY + 6.0)
    c1 = (X, y - h * 0.8)
    pts = []
    for i, (px, py) in enumerate(sp):
        th = 2 * math.pi * i / n
        c, si = math.cos(th), math.sin(th)
        rl = 1.0 / math.sqrt(c * c / w ** 2 + si * si / h ** 2)
        rp = math.hypot(px, py)
        r = rp + (rl - rp) * s
        cx, cy = c0[0] + (c1[0] - c0[0]) * s, c0[1] + (c1[1] - c0[1]) * s
        pts.append((cx + r * c, cy + r * si))
    if rot:                                                        # rocking as it's rolled (about its middle)
        a = math.radians(rot)
        mx, my = sum(q[0] for q in pts) / n, sum(q[1] for q in pts) / n
        pts = [(mx + (px - mx) * math.cos(a) - (py - my) * math.sin(a), my + (px - mx) * math.sin(a) +
                (py - my) * math.cos(a)) for px, py in pts]
    return smooth(pts)


def dough_state(P, t):
    """The dough on its board: none, a heap of flour, wet, kneaded into a ball, cut (then it's the loaves)."""
    if not hasattr(P, "pour") or t < P.pour[0] + 0.6:
        return None
    if hasattr(P, "dough_cuts") and t >= P.dough_cuts[-1]:
        return None
    f = ease(t, P.pour[0] + 0.6, P.pour[1])
    w = ease(t, *P.water) if hasattr(P, "water") else 0.0
    k = ease(t, *P.knead) if hasattr(P, "knead") else 0.0
    sq = 0.12 * math.sin(4 * t) * (P.knead[0] <= t < P.knead[1]) if hasattr(P, "knead") else 0.0
    cuts = sum(1 for c in getattr(P, "dough_cuts", []) if t >= c)
    return f, w, k, sq, cuts


PIECE_GAP, PIECE_SLIDE = 3.0, 0.5   # r4: each cut opens into a gap (the blade pushes the piece over; r31: 3, was 7,
                                    # "gaps wider than a saw blade, dough missing")


def piece_off(P, j, t):
    """How far dough piece j (0..3, left to right) has been pushed right by the cuts left of it."""
    return PIECE_GAP * sum(ease(t, c, c + PIECE_SLIDE) for c in getattr(P, "dough_cuts", [])[:j])


def _cut_x(ln, y):
    xk, yk, kk = ln[0], ln[1], ln[2]
    return xk + kk * (y - yk)


def draw_dough(pg, P, t, sh):
    d = dough_state(P, t)
    X, Y = DOUGH[0] - sh, DOUGH[1]
    # r19 (part 3 must-fix "loaves float left of the board"): no board (it popped in at the pour and was too short
    # for the loaves); the flour, dough and loaves lie straight on the rack's top
    if d is None:
        return
    f, w, k, sq, cuts = d
    # r27 (part 3 must-fix "the flour turns into a dough disc by itself while the water pours"): the water only
    # makes a wet well in the heap's top; the heap becomes dough (colour and shape) under his tentacles as he kneads
    col = mix(HW.FLOUR, HW.BREAD_DOUGH, k)
    rx, ry = 22 + 18 * f * (1 - k) + (DOUGH_RX - 22) * k, 6 + 6 * f + 6 * k + 4 * f * (1 - k)   # r14: a heap, not a disc
    X = flour_x(P, t) - sh
    lines = getattr(P, "dough_lines", ())
    act = [i for i, ln in enumerate(lines) if t >= P.dough_cuts[i]]   # cuts made (only those split it: no seams)
    if not act:
        m = k                                                      # r14: a flat-bottomed heap of flour on the board
        if m < 0.999:                                              # (it read as a floating plate), rounding into
            cy_, rx_, ry_ = Y - ry + 6, rx * (1 + sq), ry * (1 - sq)   # the dough ball as it is wetted and kneaded
            pts = []
            for j in range(24):
                th = 2 * math.pi * j / 24
                ex, ey = X + rx_ * math.cos(th), cy_ - ry_ * math.sin(th)
                dy = Y + 6 - 2 * ry_ * max(0.0, math.sin(th)) ** 0.8
                pts.append((ex, ey + (dy - ey) * (1 - m)))
            pg.shape(smooth(pts), col, 0.1)
            if w > 0.0 and k < 1.0:                                # the wet well in its top, mixed away as he kneads
                pg.flat(oval(X, Y + 6 - 2 * ry_ + 6, rx_ * 0.55 * w, 5.0 * w), mix(HW.FLOUR, HW.BREAD_DOUGH, 0.9),
                        1.0 - k)
        else:
            pg.shape(oval(X, Y - ry + 6, rx * (1 + sq), ry * (1 - sq)), col, 0.1)
    else:                                                          # cut: each piece pushed over by its cuts
        ya, yb = Y - 80, Y + 20
        for n_, j in enumerate([0] + [i + 1 for i in act]):
            off = piece_off(P, j, t)
            xl = (lambda y: X - 200) if n_ == 0 else (lambda y, ln=lines[act[n_ - 1]]: _cut_x(ln, y) - sh)
            xr = (lambda y: X + 200) if n_ == len(act) else (lambda y, ln=lines[act[n_]]: _cut_x(ln, y) - sh)
            clip = skia.Path()
            clip.moveTo(xl(ya), ya)
            clip.lineTo(xr(ya), ya)
            clip.lineTo(xr(yb), yb)
            clip.lineTo(xl(yb), yb)
            clip.close()
            pg.c.save()
            pg.c.translate(off, 0)
            pg.c.clipPath(clip, skia.ClipOp.kIntersect, True)
            pg.shape(oval(X, Y - ry + 6, rx, ry), col, 0.1)
            pg.c.restore()
    for i, (xk, yk, kk, c0, c1) in enumerate(lines):               # each cut along the blade's own line, opening
        if t < c0:                                                 # from the top down as the strokes go through
            continue
        u = min(1.0, (t - c0) / max(c1 - c0, 1e-6))
        ya, yb = Y - 2 * ry + 6 + 2, Y + 4                         # the dough's top and the board
        yb = ya + (yb - ya) * u
        o = piece_off(P, i, t) + 0.5 * (piece_off(P, i + 1, t) - piece_off(P, i, t))
        g = ease(t, P.dough_cuts[i], P.dough_cuts[i] + PIECE_SLIDE) if hasattr(P, "dough_cuts") else 0.0
        if g < 1:
            pg.stroke(skia.Path().moveTo(xk - sh + o + kk * (ya - yk), ya).lineTo(xk - sh + o + kk * (yb - yk), yb),
                      tone(col, -0.35), 3.0, 1.0 - g)


def flour_x(P, t):
    """The flour heap's middle (world x): under the sack's mouth, worked over to the board's middle as he kneads."""
    k = ease(t, *P.knead) if hasattr(P, "knead") else 0.0      # r27: moved only by his kneading, not the water
    return DOUGH[0] + FLOUR_DX * (1.0 - k)


def draw_flour_stream(pg, P, t, sh):
    """r14: the flour running out of the tipped sack's mouth straight down onto the heap, with a few grains."""
    if not (hasattr(P, "pour") and P.pour[0] + 0.6 <= t < P.pour[1]):
        return
    q = P.props["sack"].at(t)[0]
    f = P.sack_fill(t)
    mx, my = sack_pt(q, f, 0.0, -(40 + 44 * f) - 8.0)                # its open mouth, tipped over the dough
    d = dough_state(P, t)
    hy = DOUGH[1] + 6 - 2 * (6 + 10 * d[0]) if d else DOUGH[1]       # the heap's top
    a = ease(t, P.pour[0] + 0.6, P.pour[0] + 0.9) * (1 - ease(t, P.pour[1] - 0.3, P.pour[1]))
    x0, x1 = mx - sh, flour_x(P, t) - sh
    pg.stroke(skia.Path().moveTo(x0, my).cubicTo(x0 + 2, my + 12, x1, hy - 20, x1, hy), HW.FLOUR, 3.0 + 6.0 * a,
              0.95 * a)
    for j in range(7):                                             # grains falling beside it
        v = (t * 2.3 + j / 7.0) % 1.0
        pg.flat(oval(x0 + (x1 - x0) * v + 5 * math.sin(j * 2.1), my + (hy - my) * v, 1.6, 1.6), HW.FLOUR, 0.9 * a)


def draw_houses(pg, P, t, sh, glow):
    """The animals' houses (left of the oven) and the birdhouses on their posts; at night the doors and windows
    glow (drawn again over the light)."""
    door = ease(t, P.doors, P.doors + 0.8) if hasattr(P, "doors") else 0.0
    g_only = glow > 0
    if -300 < HW.HEDGE_X - sh < W + 300:
        HW.cottage(pg, HW.HEDGE_X, HW.FLOOR, *HW.HEDGE_HOUSE[:3], (196, 150, 104), sh, HW.HEDGE_HOUSE[3], False, glow,
                   door, glow_only=g_only)
    if -300 < HW.BUNNY_X - sh < W + 300:
        HW.cottage(pg, HW.BUNNY_X, HW.FLOOR, *HW.BUNNY_HOUSE[:3], (214, 186, 150), sh, HW.BUNNY_HOUSE[3], True, glow,
                   door, glow_only=g_only)
    for j, x in enumerate(HW.BIRD_POSTS):
        if -200 < x - sh < W + 200:
            pg.c.save()
            for b in getattr(P, "birds", []):                      # r26: the lit door never over a bird in it
                if g_only and b["home"][0] == x:
                    st = bird_state(P, b, t)
                    if st is not None and st[4] in ("door", "air") and abs(st[0] - x) < 60:
                        X_, Y_ = st[0] - sh, st[1]
                        pg.c.clipPath(skia.Path().addOval(skia.Rect(X_ - 16 * BIRD_S, Y_ - 23 * BIRD_S, X_ + 16 * BIRD_S,
                                                                    Y_ - 1 * BIRD_S)), skia.ClipOp.kDifference, True)
                        hx_ = X_ + 11 * st[2] * BIRD_S
                        pg.c.clipPath(skia.Path().addOval(skia.Rect(hx_ - 8 * BIRD_S, Y_ - 28 * BIRD_S, hx_ + 8 * BIRD_S,
                                                                    Y_ - 13 * BIRD_S)), skia.ClipOp.kDifference, True)
            HW.birdhouse(pg, x, HW.BIRD_POST_TOP, j, sh, glow, glow_only=g_only, door_r=BIRD_DOOR_R)
            pg.c.restore()


def draw_lanterns(pg, P, t, sh, glow_only=False):
    for j, (x, y) in enumerate(HW.LANTERNS):
        if not (-200 < x - sh < W + 200):
            continue
        lit = ease(t, P.lit[j], P.lit[j] + 0.6) if hasattr(P, "lit") else 0.0
        if glow_only:
            if lit > 0:
                pg.glow(x - sh, y, 110, "#ffd68a", 0.35 * lit)
            continue
        pg.shape(rrect(x - sh - 6, y - 60, x - sh + 6, HW.FLOOR + 4, 3), HW.TRUNK, 0.08)
        pg.shape(rrect(x - sh - 6, y - 64, x - sh + 34, y - 56, 2), HW.TRUNK, 0.06)
        HW.lantern(pg, x + 28, y - 16, lit, t, sh)


def animal_state(P, a, t):
    """(x, y, face, hop, where): at home (inside), coming out of the door, on the path, on its seat."""
    if not hasattr(P, "doors") or t < a["out"][0]:
        return None
    if t < a["go"][0]:
        o0, o1 = a["out"]
        tm = o0 + 0.6 * (o1 - o0)
        if t < tm:                                                 # in the doorway, coming out of the dark
            d = 1.0 - smoothstep((t - o0) / (tm - o0))
            return a["home"], HW.FLOOR - 8.0 * d, 1, 0.0, "door", d
        u = ease(t, tm, o1)                                        # over the doorstep, down onto the path
        return a["home"], HW.FLOOR + (a["lane"] - HW.FLOOR) * u, 1, 0.0, "step"
    if t < a["go"][1]:
        u = _seg(t, *a["go"])
        x0, x1 = a["home"], a["seat"][0]
        x = x0 + (x1 - x0) * u
        ln = a["lane"]                                             # each on its own line along the path (the
        y = ln + (a["seat"][1] - ln) * max(0.0, (x - (x1 - 220)) / 220.0) if x > x1 - 220 else ln   # bunnies pass
                                                                   # the hedgehog in front of it, never through)
        hop = 0.0
        if a["kind"] == "bunny":
            ph = (t - a["go"][0]) / 0.55
            hop = 26.0 * abs(math.sin(math.pi * ph))
        where = "path" if x < 3950 else "seat"
        return x, y, 1, hop, where
    hop = 0.0
    for b in a.get("bites", ()):                                   # r14: a little hop-and-dip with each bite
        if b <= t < b + 0.36:
            hop = 7.0 * math.sin(math.pi * (t - b) / 0.36)
    return a["seat"][0], a["seat"][1], 1, hop, "seat"


ANIMAL_S = {"bunny": 0.72, "hedgehog": 0.6}
BIRD_S = 2.0                        # the birds (part 3 review: specks)
ANIMAL_LANES = (-6.0, 20.0, 40.0)   # hedgehog, bunny, bunny: from the path's middle, nearer = lower and in front   # their sizes (each fits its doorway: bunny 64 x 81, hedgehog 56 x 33)


def draw_animal(pg, P, a, st, t, sh, light=None):
    """An animal; in its doorway it's drawn only inside the opening (the wall is in front of it), a little smaller
    and darker the further in. light: the night's colour, for the pass over the darkening (it's in front of the
    lit doorway then)."""
    from .tune_flat import bunny_flat, hedgehog_flat
    x, y, face, hop, where = st[:5]
    d = st[5] if len(st) > 5 else 0.0
    snap = dict(zoom=1.0, cx=sh + W / 2, cy=H / 2, W=W, H=H)
    c = pg.c
    c.save()
    if light is not None:
        c.saveLayer()
    if where == "door":
        door_r = HW.BUNNY_HOUSE[3] if a["kind"] == "bunny" else HW.HEDGE_HOUSE[3]
        c.clipPath(HW.house_door(a["home"], sh, door_r), skia.ClipOp.kIntersect, True)
        k = 1.0 - 0.3 * d
        c.translate(x - sh, y)
        c.scale(k, k)
        c.translate(-(x - sh), -y)
    if a["kind"] == "bunny":
        pg.begin_grain()
        bunny_flat(pg, snap, x, y, ANIMAL_S["bunny"], hop, face)
        pg.end_grain(x - sh, y - hop)
    else:
        pg.begin_grain()
        hedgehog_flat(pg, snap, x, y, ANIMAL_S["hedgehog"], face, 0.0, t)
        pg.end_grain(x - sh, y)
    if where == "door" and d > 0:                                  # the dark inside the house
        pg.c.drawPaint(skia.Paint(Color=skia.Color(40, 30, 28, int(200 * d)), BlendMode=skia.BlendMode.kSrcATop))
    if light is not None:
        col = skia.Color(*(int(round(255 * min(1.0, float(m)))) for m in light))
        c.drawPaint(skia.Paint(Color=col, BlendMode=skia.BlendMode.kModulate))
        c.restore()
    c.restore()


BIRD_DOOR_R = 15.0                  # r26: the birdhouses' round doors (the birds come out of them)


def bird_state(P, b, t):
    if not hasattr(P, "doors"):
        return None
    (hx, hy), (px, py) = b["home"], b["perch"]
    f = 1 if px > hx else -1
    if "out" in b and t < b["fly"][0]:
        p0, p1, p2 = b["out"]
        if t < p0:
            return None
        hd = (11 * f * BIRD_S, -20 * BIRD_S)                       # its head's centre from its feet
        if t < p1:                                                 # r26: peeping out of the door (only what's in
            u = smoothstep(_seg(t, p0, p1))                        # the round hole shows)
            return hx - hd[0] - f * 14.0 * (1 - u), hy - 40 - hd[1] + 4.0 * (1 - u), f, None, "door"
        if t < p2:                                                 # the hop out, down onto the ledge
            u = _seg(t, p1, p2)
            x0, y0 = hx - hd[0], hy - 40 - hd[1]
            return x0 + (hx - x0) * u, y0 + (hy + 2 - y0) * u - 26 * math.sin(math.pi * u), f, 0.5, "air"
        return hx, hy + 2, f, None, "air"                          # on the ledge, a look round
    if t < b["fly"][0]:
        return None
    if "out" in b and t < b["fly"][1]:                             # r26: down and away to the table, low
        u = _seg(t, *b["fly"])
        e = smoothstep(u)
        x = hx + (px - hx) * e
        y = hy + 2 + (py - hy - 2) * e ** 1.4 - 40 * math.sin(math.pi * u)
        return x, y, f, 0.5 + 0.5 * math.sin(t * 16), "air" if u < 0.6 else "table"
    if t < b["fly"][1]:
        u = _seg(t, *b["fly"])
        e = smoothstep(u)
        x = hx + (px - hx) * e
        y = hy - 40 + (py - hy + 40) * e - 160 * math.sin(math.pi * e)
        return x, y, (1 if px > hx else -1), 0.5 + 0.5 * math.sin(t * 16), "air" if u < 0.6 else "table"
    peck = max(0.0, math.sin(t * 3 + px)) ** 8
    return px, py + 4 * peck, (1 if px > hx else -1), None, "table"


def draw_stump(pg, x, y, sh):
    X = x - sh
    pg.shape(rrect(X - 34, y - 4, X + 34, y + 46, 8), HW.TRUNK, 0.1)
    pg.flat(oval(X, y - 4, 34, 10), HW.WOOD_END)
    pg.stroke(skia.Path().addOval(skia.Rect(X - 18, y - 9, X + 18, y + 1)), HW.WOOD_RING, 1.4, 0.8)


def draw_table_back(pg, P, t, sh):
    """The table's back log (the Keepers stand just behind it)."""
    x0, x1 = HW.TABLE[0] + 30, HW.TABLE[1] + 50
    if x1 - sh < -100 or x0 - sh > W + 100:
        return
    HW.draw_log(pg, x0, x1, HW.TABLE_FRONT - 70 + 34, sh, 34.0, tone(HW.WOOD, -0.08))


def draw_table_front(pg, P, t, sh):
    x0, x1 = HW.TABLE[0] - 20, HW.TABLE[1]
    if x1 - sh < -100 or x0 - sh > W + 100:
        return
    HW.draw_log(pg, x0, x1, HW.TABLE_FRONT + 40, sh, 40.0)


# ----------------------------------------------------------------------------------------------- the frame

def hans_over(pg, t, sh, slots, clip_out=None):
    """r37 (round 36 part 3 must-fixes: the flour sack rose in front of his chest and floated down to the ground
    with nothing holding it): Hans' tentacles `slots` drawn again, over a thing he holds in front of everything (the
    sack), so the tentacle wrapped round its neck shows. His figure's own layer, without the body."""
    x, y, a = keeper("tentacles", t)
    M = pg.c.getTotalMatrix()
    m = il.Monster("tentacles", k=K)
    m.x, m.y, m.newlook = x - sh, y, True
    from .flat_motion import HANS_COLOURS
    m.parts_col = dict(HANS_COLOURS, wings=(214, 100, 28))
    for a_, v in a.items():
        setattr(m, a_, v)
    cv = il.StyleCanvas(pg.W, pg.H, 6, seed=il.Monster.KINDS.index("tentacles") + 1)
    cv.eye_scale = 1.15
    cv.c.setMatrix(M)
    hans_extra(t, sh, "over", only=slots)(cv, m)
    if hasattr(pg, "grain_on"):
        pg.grain_on(cv.surface.getCanvas(), x - sh, y, getattr(cv, "bounds", None))
    fig = cv.surface.makeImageSnapshot()
    c = pg.c
    c.save()
    if clip_out is not None:                                       # (in the world's coordinates, under the zoom)
        c.clipPath(clip_out, skia.ClipOp.kDifference, True)
    c.resetMatrix()
    c.drawImage(fig, 0, 0)
    c.restore()


def sack_body_clip(P, t, sh):
    """r41 (round 40 part 3 must-fix "the sack is see-through: his whole curled tentacle shows through the cloth"):
    the sack's body below its mouth, where the tentacle he holds it with is behind it; only over the neck, the cord
    and the mouth is it drawn again in front."""
    q = P.props["sack"].at(t)[0]
    f = P.sack_fill(t)
    w, h = 34 + 18 * f, 40 + 44 * f
    X = q["x"] - sh
    r = skia.Path().addRect(X - w - 14, q["y"] - h - 6, X + w + 14, q["y"] + 40)
    tip = q.get("tip", 0.0)
    if abs(tip) > 1e-3:
        px, py = sack_pivot(q, f)
        r.transform(skia.Matrix.RotateDeg(tip, skia.Point(px - sh, py)))
    return r


def sack_over_slots(P, t):
    """The tentacles on the sack while he holds it up in front of everything at the dough (r37)."""
    sd = getattr(P, "sack_down2", None)
    if sd is None or t < sd[0]:
        return ()
    sk = P.props.get("sack")
    if sk is None or zof(sk, t) < 20:
        return ()
    hd = sk.at(t)[1]
    if hd is None or hd[0] != "Hans":
        return ()
    sl = [hd[1]]
    u = getattr(P, "untie", (1e9, 1e9))
    if u[0] - 0.3 <= t < u[1] + 0.3:
        sl.append(1)
    return tuple(sl)


def figure(pg, kd, x, y, t, sh, a, extra=None, shadow=True, extra_behind=None):
    """A Keeper, sharp under the camera zoom too (zoom_figure). r19: `extra_behind(cv, m)` is drawn on his layer
    before his body (Hans' tentacles holding something that is behind him)."""
    if extra_behind is None:
        return ZF.figure(pg, kd, x - sh, y, K, t=t, extra=extra, shadow=shadow, **a)
    if not ZF.zoomed(pg):
        return il.figure(pg, kd, x - sh, y, K, 6, t=t, eye_scale=1.15, extra=extra, shadow=shadow,
                         extra_behind=extra_behind, **a)
    return _figure_zoomed(pg, kd, x - sh, y, K, t, extra, shadow, extra_behind, a)


def _figure_zoomed(pg, kind, x, y, k, t, extra, shadow, extra_behind, attrs):
    """zoom_figure.figure (zoomed branch) with a layer behind the body: the same steps, in the same order."""
    M = pg.c.getTotalMatrix()
    st = il.STYLES[6]
    m = il.Monster(kind, k=k)
    m.x, m.y, m.newlook = x, y, True
    if kind == "tentacles":
        from .flat_motion import HANS_COLOURS
        m.parts_col = dict(HANS_COLOURS, wings=(214, 100, 28))
    for a_, v in attrs.items():
        setattr(m, a_, v)
    cv = il.StyleCanvas(pg.W, pg.H, 6, seed=il.Monster.KINDS.index(kind) + 1)
    cv.eye_scale = 1.15
    cv.c.setMatrix(M)
    extra_behind(cv, m)
    m.draw(cv, t, il.Glow())
    if extra is not None:
        extra(cv, m)
    if hasattr(pg, "grain_on"):
        pg.grain_on(cv.surface.getCanvas(), x, y, getattr(cv, "bounds", None))
    fig = cv.surface.makeImageSnapshot()
    c = pg.c
    from .doorway import HALF_W
    hw = HALF_W.get(kind, 200.0) * k
    if shadow:
        pg.shadow(x, y + 4, hw * 0.75, 14 + 10 * k, st["shadow"])
    c.save()
    c.resetMatrix()
    c.drawImage(fig, 0, 0)
    c.restore()
    for path, col in cv.glows:
        b = path.getBounds()
        r = max(b.width(), b.height()) * 0.5
        pg.glow(b.centerX(), b.centerY(), r * 2.2, col, 0.38)
        p_ = skia.Paint(AntiAlias=True, Color=il.C(col, 0.55), BlendMode=skia.BlendMode.kScreen)
        p_.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.35 + 1))
        c.drawPath(path, p_)
    return m


def dome_path(sh):
    pts = [(HW.OVEN_X - sh - math.cos(math.pi * k / 40) * HW.OVEN_W / 2,
            OVEN_BASE_Y - math.sin(math.pi * k / 40) * HW.OVEN_H - DOME_BOW * abs(math.cos(math.pi * k / 40)) *
            min(1.0, math.sin(math.pi * k / 40) * RINGS))
           for k in range(41)]                                     # (r38: the rings' sides are higher, dome_pt)
    return smooth(pts + [(HW.OVEN_X - sh + HW.OVEN_W / 2, OVEN_BASE_Y + 30), (HW.OVEN_X - sh - HW.OVEN_W / 2,
                                                                             OVEN_BASE_Y + 30)], closed=True)


def inside_oven(P, p, q, t):
    """Is this thing in (or going into) the oven's door, so only what shows through the door is drawn?"""
    if p.kind == "stick":
        return abs(q["x"] - OVEN_MOUTH[0]) < 40 and abs(q["y"] - OVEN_MOUTH[1]) < 30
    if p.kind == "loaf" and hasattr(P, "slide_in"):              # on the peel, through the door
        return P.slide_in[0] <= t < P.slide_out[1] and P.peel_mode(t)[1] >= 0.55   # (r16: all within the door by then)
    return False


def _hopper_slots():
    """Where the acorns sit in the hopper, from the spout up: 2, 3, 3, 4 to a row, inside the V."""
    out = []
    for r, n in enumerate((2, 3, 3, 4)):
        y = HW.HOPPER[0][1][1] - 22.0 - 12.0 * r
        for k in range(n):
            out.append((HW.NIP_X + (k - (n - 1) / 2) * 14.0 + (3.0 if r % 2 else 0.0), y))
    return out


HOPPER_SLOTS = _hopper_slots()


def hopper_slot(s_):
    """The place for pile position s_ (fractional: on its way down from one place to the next)."""
    s_ = max(0.0, s_)
    i = min(int(s_), len(HOPPER_SLOTS) - 2)
    u = s_ - i
    (x0, y0), (x1, y1) = HOPPER_SLOTS[i], HOPPER_SLOTS[i + 1]
    return dict(x=x0 + (x1 - x0) * u, y=y0 + (y1 - y0) * u)


HANS_FRONT = ("pole", "board", "stone", "rock", "slab", "jamb", "lintel", "stick", "log", "pulley", "corner",
              "belt_coil", "lump")


def hans_front(P, p, holder, q, t):
    """A thing in Hans' tentacle is in front of him while he carries it (part 2 review: the hopper boards, the oven's
    stones and the sticks passed behind his body and "popped" into place). It goes back to its own layer where
    he sets it down, clear of him. Not the low beam (it goes in behind the posts), not a gear once it's up high
    (behind the stones), not a stick going in through the oven's door."""
    if holder is None or holder[0] != "Hans" or p.kind not in HANS_FRONT or p.name == "low beam":
        return False
    if p.name in OVEN_STONE_NAMES:                                 # r26: low behind his legs, on the oven's layer
        return False
    if p.name in ("roof L", "roof R"):                             # r37 (round 36 part 1 must-fix: the boards across his
        return False                                               # face): off the pile behind him, his head in front
    if p.name == "sack":                                           # r26: going down behind the rack's bar
        return P.__dict__.get("sack_mid", (0, 0))[0] <= t < P.__dict__.get("sack_mid", (0, 0))[1]
    if p.name.startswith("millstone"):                             # r19 (part 1 must-fixes: a stone floating up in
        return False                                               # front of his face, then jumping behind him onto
    # the beam): a millstone rests behind him and hangs on the beam behind him, so it's behind him the whole way
    if getattr(p, "zf", ()) and zof(p, t) < 4.0:                  # (r6: any step back behind him, not only the last)
        return False
    return not inside_oven(P, p, q, t)


def held_by_glo(p, holder):
    """A small thing Glo carries in his tendrils (the first acorn): it's drawn in front of them, with two tendril
    tips curled round it, so it's plainly held, not floating (owner, FK0021)."""
    return p.kind in ("acorn", "belt_coil") and holder is not None and holder[0] == "Glo"


def draw_glo_grip(pg, p, q, sh, t):
    draw_prop(pg, plan(), p, q, sh, t)
    X, y, s_ = q["x"] - sh, q["y"], q.get("s", 1.0)
    col = tone(HW.COLS["lantern"], -0.06)
    for f in (-1, 1):                                              # from above, round its side, the tip under it
        pts = [(X + f * 4 * s_, y - 26 * s_), (X + f * 10 * s_, y - 8 * s_), (X + f * 9 * s_, y + 8 * s_),
               (X + f * 3 * s_, y + 13 * s_)]
        pg.stroke(smooth(pts, closed=False), col, 4.2 * s_)


def draw_roof_grip(pg, P, q, sh, t):
    """r22 (part 1 must-fix: the two roof boards hung in a fixed A under Glo with nothing holding them): a tendril
    from under his dome down the board's outer side, wrapped twice round it a little below the ridge, so each board
    is plainly clamped in his tendrils (they open about that grip as the feet slide out on the beam)."""
    a_ = math.radians(q["ang"])
    ux, uy = math.cos(a_), math.sin(a_)
    o = q.get("off", 0.0)
    cx, cy = q["x"] + o * ux - sh, q["y"] + o * uy
    h = q["L"] / 2.0
    e1, e2 = (cx - h * ux, cy - h * uy), (cx + h * ux, cy + h * uy)
    top, bot = (e1, e2) if e1[1] < e2[1] else (e2, e1)
    dx, dy = bot[0] - top[0], bot[1] - top[1]
    L = math.hypot(dx, dy) or 1.0
    dx, dy = dx / L, dy / L
    f = 1.0 if dx > 0 else -1.0                                    # the board's outer side
    nx, ny = -dy * f, dx * f
    if nx * f < 0:
        nx, ny = -nx, -ny
    hx, hy = P.glo_hand(t)
    hx -= sh
    col = tone(HW.COLS["lantern"], -0.06)
    th = q.get("th", 12.0) / 2.0 + 3.0
    for k, d in enumerate((22.0, 40.0)):                           # two wraps, one under the other
        gx, gy = top[0] + dx * d, top[1] + dy * d
        start = (hx + f * (5.0 + 4.0 * k), hy - 18.0)
        pts = [start, (gx + nx * (th + 10.0), gy - 16.0 + 4.0 * k), (gx + nx * th, gy - 2.0),
               (gx + dx * 4.0, gy + dy * 4.0 + 1.0), (gx - nx * th, gy + 2.0), (gx - nx * (th - 2.0) - dx * 6.0,
                                                                                gy - dy * 6.0 - 4.0)]
        pg.stroke(smooth(pts, closed=False), col, 4.2)


def on_branch_or_falling(p, holder, t=-1e9):
    P_ = plan()
    if p.name == "acorn" and holder is None and P_.bonk - P_.acorn_fall - 0.05 <= t < P_.glo_catch:   # (r30: the whole fall)
                                                                   # (was bonk - 0.8: the fall's start hid in the leaves)
                                                                      # falling and bouncing: in
        return True                                                # front of Glo (r2: it flew in behind him)
    """The shaken acorns until they're in the basket: on the branch, falling (in front of Glo, like the branch)."""
    return p.name.startswith("acorn 0.") and holder is None and t < getattr(p, "land_t", 1e9)


def draw_any(pg, P, p, q, sh, t):
    bd = getattr(p, "behind_door", None)
    if bd is not None and bd[0] <= t < bd[1]:                      # r37 (round 36 part 2 must-fix: the rope over the
        pg.c.save()                                                # right jamb, the left one over the rope): the door's
        # stones in front of the coil all round. r40 (round 39 part 2 must-fix "drawn in front of the posts and the
        # lintel"; "depth order wrong"): of the rope only its end where it's being laid on the course (the course is
        # behind the stones, like the ring); the part he holds up is in the air in front of the oven
        loc = skia.Path().addCircle(q["x"] - sh, q["y"], 26.0)
        pg.c.clipPath(skia.Op(door_stones_clip(sh), loc, skia.PathOp.kIntersect_PathOp), skia.ClipOp.kDifference, True)
        p.behind_door, bd_ = None, bd
        draw_any(pg, P, p, q, sh, t)
        p.behind_door = bd_
        pg.c.restore()
        return
    if p.kind in ("pole", "board", "log", "stone", "gear", "corner", "pulley", "sack", "basket", "acorn", "belt_coil"):
        draw_prop(pg, P, p, q, sh, t)
    else:
        draw_vprop(pg, P, p, q, sh, t)


def frame(pg, valley, t):
    P = plan()
    sh = P.shift(t)
    dark = HW.darkness(t)
    z, zcx, zcy = P.zoom(t)
    pg.c.save()
    if z > 1.0005:                                                 # the camera's zoom (the world only, not the cards)
        pg.c.translate(W / 2, H / 2)
        pg.c.scale(z, z)
        pg.c.translate(-zcx, -zcy)
    HW.sky(pg, t, sh)
    ca = 1.0 - 0.9 * dark                                          # day clouds fade into the night
    if ca > 0.02:
        pg.c.saveLayerAlpha(None, int(255 * ca))
        valley.draw(pg, sh, only={"clouds"})
        pg.c.restore()
    valley.draw(pg, sh, only={"far", "far2", "far_trees", "mid", "far_bank"})
    HW.draw_water(pg, t, sh, 0.0 if t < P.wheel_go else 110.0)
    draw_wheel(pg, P, t, sh)
    props = [(p, *p.at(t)) for p in P.props.values() if p.alive(t)]
    props = [(p, q, hd, mv) for p, q, hd, mv in props if -400 < q["x"] - sh < W + 400]

    def in_water(e):
        return e[0].kind == "stone" and e[1].get("wet", 0.0) > 0.0 and e[1]["y"] < HW.near_edge(e[1]["x"]) - 4
    HW.draw_brook_front(pg, t, sh)
    for e in sorted([e for e in props if in_water(e)], key=lambda e: e[1]["y"]):   # the millstones in the shallows
        draw_prop(pg, P, e[0], e[1], sh, t)                        # (r34: over the brook's front band, which ended
        draw_stone_lap(pg, e[1], sh, t)                            # square across one; the water laps their rims)
    draw_wheel_front(pg, P, t, sh)
    valley.draw(pg, sh, only={"meadow"})
    draw_brake(pg, P, t, sh)
    if -300 < HW.STOP_X - sh < W + 100:
        draw_rack(pg, HW.STOP_X - 12, HW.NOTCH_X + 30, HW.RACK_Y, HW.FLOOR + 4, sh, HW.STOP_X, HW.NOTCH_X)
    draw_houses(pg, P, t, sh, 0.0)
    draw_lanterns(pg, P, t, sh)
    draw_holes(pg, P, t, sh)
    behind = sorted([e for e in props if not in_water(e) and zof(e[0], t) < 20], key=lambda e: zof(e[0], t))
    front = sorted([e for e in props if zof(e[0], t) >= 20], key=lambda e: zof(e[0], t))
    belt = P.belt_state(t)
    drew = set()
    for p, q, hd, mv in behind:
        z = zof(p, t)
        if z >= 4 and "belt" not in drew:
            if belt is not None:
                HW.draw_belt(pg, sh, belt[1]) if belt[0] == "on" else HW.draw_belt(pg, sh, end=belt[1])
                draw_holes(pg, P, t, sh, near=HW.BRAKE_X)          # r18: the pile in front of the belt's coil
            drew.add("belt")
        if z >= 9.35 and "oven" not in drew:
            draw_oven(pg, P, t, sh)
            drew.add("oven")
        if p.kind == "belt_coil" and belt is not None:
            continue
        if on_branch_or_falling(p, hd, t):                         # drawn with the branch, in front of Glo
            continue
        if held_by_glo(p, hd):                                     # in front of his tendrils, wrapped by them
            continue
        if hans_front(P, p, hd, q, t):                             # in Hans' tentacle: in front of him
            continue
        if inside_oven(P, p, q, t):
            c = pg.c
            if p.kind != "loaf":                                   # a stick half in: outside the dome as it is
                c.save()
                c.clipPath(dome_path(sh), skia.ClipOp.kDifference, True)
                draw_any(pg, P, p, q, sh, t)
                c.restore()
            c.save()
            c.clipPath(door_rect(sh), skia.ClipOp.kIntersect, True)
            draw_any(pg, P, p, q, sh, t)
            c.restore()
        else:
            draw_any(pg, P, p, q, sh, t)
            if p.kind == "belt_coil":                              # r18: the pile in front of it, over it
                draw_holes(pg, P, t, sh, near=HW.BRAKE_X)
    if "oven" not in drew:
        draw_oven(pg, P, t, sh)
    draw_flour(pg, P, t, sh)
    gx, gy, ga = keeper("lantern", t)
    if -400 < gx - sh < W + 400:
        figure(pg, "lantern", gx, gy, t, sh, ga, shadow=False)
    for p, q, hd, mv in behind:
        if held_by_glo(p, hd):
            draw_glo_grip(pg, p, q, sh, t)
        elif p.name in ("roof L", "roof R") and hd is not None and hd[0] == "Glo":
            draw_roof_grip(pg, P, q, sh, t)
    bs = P.belt_state(t)
    if bs is not None and bs[0] == "fitting" and getattr(P, "belt_glo", False):   # r11: the belt's end in his
        X, y = bs[1][0] - sh, bs[1][1]                             # tendrils, two tips curled round it
        col = tone(HW.COLS["lantern"], -0.06)
        for f in (-1, 1):
            pg.stroke(smooth([(X + f * 4, y - 26), (X + f * 10, y - 8), (X + f * 9, y + 8), (X + f * 3, y + 13)],
                             closed=False), col, 4.2)
    draw_branch(pg, P, t, sh)                                      # the oak's low branch is nearer than Glo
    draw_squirrel(pg, P, t, sh)
    for p, q, hd, mv in behind:
        if on_branch_or_falling(p, hd, t):
            draw_prop(pg, P, p, q, sh, t)
    animals = []
    for a in getattr(P, "animals", []):
        st = animal_state(P, a, t)
        if st is not None:
            animals.append((a, st))
    for a, st in sorted(animals, key=lambda e: e[1][4] != "door"):    # one in a doorway is behind one stepping out
        if st[4] in ("path", "door", "step"):
            draw_animal(pg, P, a, st, t, sh)
    for b in getattr(P, "birds", []):
        st = bird_state(P, b, t)
        if st is not None and st[4] == "door":                     # r26: only what shows in its round door
            pg.c.save()
            pg.c.clipPath(skia.Path().addOval(skia.Rect(b["home"][0] - sh - BIRD_DOOR_R, b["home"][1] - 40 - BIRD_DOOR_R,
                                                        b["home"][0] - sh + BIRD_DOOR_R, b["home"][1] - 40 + BIRD_DOOR_R)),
                          skia.ClipOp.kIntersect, True)
            HW.bird(pg, st[0], st[1], st[2], t, HW.BIRD_COLS[P.birds.index(b)], st[3], sh, s=BIRD_S)
            pg.c.restore()
        elif st is not None and st[4] == "air":
            HW.bird(pg, st[0], st[1], st[2], t, HW.BIRD_COLS[P.birds.index(b)], st[3], sh, s=BIRD_S)
    if P.wheel_go < 1e8:
        pp, stt = peg_pos(P, t)
        if stt != "post":
            td_ = P.pin[1] + PEG_DROP
            draw_peg(pg, pp, sh, ang=-90.0 * ease(t, td_, td_ + 0.3))   # (knob toward Springs, lying down)
            nx_, ny_ = peg_neck(P, t)                              # r22: the rope's loop still round its neck
            lie_ = ease(t, td_, td_ + 0.3)
            pg.stroke(oval(nx_ - sh, ny_, 8.0 - 5.0 * lie_, 3.0 + 5.0 * lie_), tone((150, 116, 74), -0.15), 2.5)
    for kd in WALKERS:
        x, y, a = keeper(kd, t)
        if -500 < x - sh < W + 500:
            if kd == "tentacles":                                  # r19: tentacles on things behind him, behind
                figure(pg, kd, x, y, t, sh, a, extra=hans_extra(t, sh, "front"),
                       extra_behind=hans_extra(t, sh, "behind"))
            else:
                figure(pg, kd, x, y, t, sh, a)
            if kd == "tentacles":                                  # what he's carrying: in front of him
                for p, q, hd, mv in behind:
                    if hans_front(P, p, hd, q, t):
                        draw_any(pg, P, p, q, sh, t)
    if any(f0 <= t < f1 for f0, f1 in getattr(P, "glo_front", ())):   # r13: Glo in front of Hans (the handover)
        gx, gy, ga = keeper("lantern", t)
        figure(pg, "lantern", gx, gy, t, sh, ga, shadow=False)
    if P.tie[0] - 0.7 <= t < P.tie[1] + 0.7 and P.tie_behind(t):     # r13: the neck and cord over his tentacle tips
        q = P.props["sack"].at(t)[0]
        ct = P.tie_cord(t) if t < P.tie_wind[1] else None
        HW.draw_sack(pg, q["x"], q["y"], P.sack_fill(t), q.get("tied", 0.0), sh, cord_to=ct, neck_only=True)
    # in front of the path: the table, the saw rack by it, what's on them, the animals at the table
    if -400 < HW.TABLE[0] - sh < W + 300:
        draw_table_back(pg, P, t, sh)
    if -300 < FR_STOP - sh < W + 300:
        draw_rack(pg, FR_STOP - 12, FR_NOTCH + 30, HW.RACK_Y, 1062.0, sh, FR_STOP, FR_NOTCH)
        draw_dough(pg, P, t, sh)
    if -400 < HW.TABLE[0] - sh < W + 300:
        draw_table_front(pg, P, t, sh)
    planks = [e for e in front if e[0].kind == "plank"]
    for p, q, hd, mv in sorted(planks, key=lambda e: -e[1]["y"] if e[1].get("yaw", 0) < 45 else e[1]["x"]):
        draw_vprop(pg, P, p, q, sh, t)
    if abs(SLAB[0] - sh - W / 2) < W:
        draw_slab(pg, sh)
    for p, q, hd, mv in front:
        if p.kind != "plank":
            draw_any(pg, P, p, q, sh, t)
            if p.name == "sack" and sack_over_slots(P, t):        # r37: his tentacle round its neck, over it
                hans_over(pg, t, sh, sack_over_slots(P, t), clip_out=sack_body_clip(P, t, sh))
    rl = tuple(sl for sl, r0, r1 in getattr(P, "loaf_rolls", ()) if r0 <= t < r1)
    if rl:                                                         # r38: the tip rolling a dough piece, on top of it
        hans_over(pg, t, sh, rl)
    draw_trim(pg, P, t, sh)
    draw_sawdust(pg, P, t, sh)
    cut_front(pg, P, t, sh)
    if hasattr(P, "animals"):
        draw_stump(pg, ANIMALS[0][2][0], ANIMALS[0][2][1], sh)
    for a, st in animals:
        if st[4] == "seat":
            draw_animal(pg, P, a, st, t, sh)
    for b in getattr(P, "birds", []):
        st = bird_state(P, b, t)
        if st is not None and st[4] == "table":
            HW.bird(pg, st[0], st[1], st[2], t, HW.BIRD_COLS[P.birds.index(b)], st[3], sh, s=BIRD_S)
    valley.draw(pg, sh, only={"fg"})
    HW.apply_light(pg, t)
    if z > 1.0005 and dark > 0.02:
        # r44 (round 44 part 3 must-fix "the close shots look like daytime between dusk/night wide shots"): a close
        # shot shows no sky, so it carries the sky's evening colour as a cast (the wide shots show it in the sky)
        a_, b_, u_ = HW.light_at(t)
        kz = min(1.0, (z - 1.0) / 0.6) * min(1.0, dark / 0.35)

        def cast(j, k_):                                           # the sky's colour j (0 top, 1 mid), normalised
            ms = [HW.PRESETS[a_][j], HW.PRESETS[b_][j]]
            mc = [[int(m.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)] for m in ms]
            rgb = [mc[0][i] + (mc[1][i] - mc[0][i]) * u_ for i in range(3)]
            mx_ = max(rgb)
            return skia.Color(*(int(round(255 * (1.0 - k_ + k_ * v / mx_))) for v in rgb))
        g = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [cast(0, 0.55 * kz), cast(1, 0.3 * kz)])
        pg.c.save()                                                # (strongest at the top, where the sky would be)
        pg.c.resetMatrix()
        pg.c.drawPaint(skia.Paint(Shader=g, BlendMode=skia.BlendMode.kMultiply))
        pg.c.restore()
    if dark > 0.05:                                                # what glows in the dark, over the light
        draw_houses(pg, P, t, sh, dark)
        for a, st in sorted(animals, key=lambda e: e[1][4] != "door"):   # in front of their lit doorways
            if st[4] in ("door", "step"):
                draw_animal(pg, P, a, st, t, sh, light=HW.light_mul(t))
        draw_lanterns(pg, P, t, sh, glow_only=True)
        HW.fireflies(pg, t, sh, max(0.0, dark - 0.5) * 2)
    f = P.fire(t)
    if f > 0 and abs(HW.OVEN_X - sh - W / 2) < W:
        pg.glow(OVEN_MOUTH[0] - sh, OVEN_MOUTH[1], 130, "#ffb060", 0.35 * f * (0.9 + 0.1 * math.sin(t * 9)))
    bonk_ticks(pg, P, t, sh)
    glo_lights(pg, t, sh)
    bread_steam(pg, t, sh)
    bubbles(pg, t)
    pg.c.restore()
    overlays(pg, t)
    u = 1 - abs(t - P.act_cut) / 1.0 if hasattr(P, "act_cut") else 0.0
    if u > 0:                                                      # the dip between the mill and the village
        pg.flat(skia.Path().addRect(skia.Rect(0, 0, W, H)), (34, 26, 30), smoothstep(u))


def draw_slab(pg, sh):
    """r13: the flat stone slab on the path by the oven that Hans rolls the clay out on."""
    x, y, hw = SLAB[0] - sh, SLAB[1], SLAB[2]
    dp = 52.0
    bx, by = DV[0] * dp, DV[1] * dp
    pg.shape(smooth([(x - hw, y - 2), (x + hw, y - 2), (x + hw + 4, y + 14), (x - hw + 3, y + 16)]), tone(HW.STONE, 0.0), 0.12)
    pg.shape(smooth([(x - hw, y), (x - hw + bx + 6, y + by), (x + hw + bx, y + by - 2), (x + hw + 2, y)]),
             tone(HW.STONE, 0.3), 0.12)
    for fx, fy, r in ((-0.55, 0.5, 5.0), (0.2, 0.35, 4.0), (0.62, 0.6, 3.5)):   # a few pits in its top
        pg.flat(oval(x + hw * fx + bx * fy, y + by * fy, r * 1.6, r * 0.6), tone(HW.STONE, 0.12))


def _clay_left(P, sx, t):
    """The share of the clay heap still there (Hans takes a lump off the soft one for each coil)."""
    if sx < 0 or not hasattr(P, "lumps"):                          # (r15: the right heap is the oven's)
        return 1.0
    # r31 (round 30 part 2 must-fix "the pile doesn't shrink"): a sixth of it goes with each lump (its width and
    # height both scale by the square root, so its area goes down a sixth a time); a scrap is left at the end
    # r35 (round 34 part 2 must-fix "the pile stays the same size for three lumps, then most of it vanishes in
    # under 2 s"): by the square root it went 100 -> 73 % over the first three and 73 -> 24 % over the last; now
    # its size goes down the same step for every lump (a scrap left at the end)
    return max(0.0, 1.0 - 0.13 * sum(ease(t, a, a + 0.6) for a in P.lumps))


Plan.clay_left = _clay_left


# ----------------------------------------------------------------------------------------------- the soundtrack

def soundtrack(path):
    """The music box (the episode's own variant), the Keepers' voices, soft warm sounds for what happens on screen,
    the brook at the mill, and the narrator over it all (the music eases down only while she speaks)."""
    from engine.audio import EventTrack
    from . import music
    from .chatter import MOODS, VOICE, VOWEL
    from .narrator import soundtrack as narr_mix, take
    P = plan()
    track = EventTrack(8)
    chords = music.compose(track, 0.3, P.end - 1.0, gain=0.9, variant="harvestfeast")
    pan = lambda x: max(-0.6, min(0.6, (x / W) * 1.2 - 0.6))       # noqa: E731

    def px(xw, t):
        return pan(xw - P.shift(t))
    for tv, kd, mood, _ in P.voices:
        contour, st, _ = MOODS[mood]
        track.hit(tv, f"voice_{contour}@{int(round(VOWEL[kd] * 100))}", VOICE[kd] + st, 0.3,
                  px(keeper(kd, tv)[0], tv))
    for t0 in np.arange(0.0, P.act_cut - 1.0, 8.0):                 # the brook, at the mill
        track.fx(t0, "rush", min(8.6, P.act_cut - t0), 0.03, -0.2)
    for t0 in np.arange(P.wheel_go, P.act_cut - 1.0, 2.6):         # the wheel's paddles, the stones grinding
        track.fx(t0, "gurgle", 1.4, 0.03, px(HW.WX, t0))
        track.fx(t0 + 1.0, "creak", 1.2, 0.015, px(HW.NIP_X, t0))
    track.fx(P.bonk, "sand_thump", 0.2, 0.06, px(MILL["digger"], P.bonk))
    for side, h in P.holes.items():
        for sx in (-1, 1):
            for tt in h["dig"].scrapes(sx, *h["t"]):
                track.fx(tt, "sand_scrape", 0.4, 0.05, px(h["x"], tt))
    for c in P.twigs_cuts:                                         # the saw strokes, the nicks
        for stv in c["strokes"]:
            track.fx(stv[0] + 0.05, "sand_slice", 0.35, 0.04, px(c["tx"], stv[0]))
    for p in P.props.values():                                     # something set down: a soft wooden knock
        for t0, t1, p0, p1, how, lift, holder, fn in p.moves:
            if holder is not None and holder[0] == "Hans" and how != "fn" and t1 - t0 > 0.8:
                if p.kind in ("pole", "board", "stone", "gear", "plank", "rock", "slab", "jamb", "lintel"):
                    track.fx(t1 - 0.05, "sand_thump", 0.2, 0.04, px(p1.get("x", 0.0), t1))
    for t0, t1, kind, s in P.springs_special:
        if kind == "shake":
            for a, b in s["bounces"]:
                track.fx(a, "rustle", 0.8, 0.06, px(SHAKE_X, a))
        elif kind == "stomp":
            for a, b in s["b"]:
                track.fx(a + 0.2, "sand_thump", 0.2, 0.05, px(s["x"], a))
    for ld in P.loads:
        for a, tl, dx, dy in ld["acorns"]:
            track.hit(tl, "plink", 60 + (int(dx) % 5), 0.04, px(HW.BASKET_HOME[0], tl))
    for tc, name in P.acorn_flow:                                  # each acorn between the stones: a soft crunch
        track.fx(tc - 0.3, "sand_scrape", 0.3, 0.035, px(HW.NIP_X, tc))
    track.fx(P.flour_puff, "bubble", 0.8, 0.04, px(HW.NIP_X, P.flour_puff))
    track.hit(P.pin[1] - 0.2, "pluck", 62, 0.05, px(HW.BRAKE_X, P.pin[1]))
    track.fx(P.wheel_go, "creak", 1.6, 0.05, px(HW.WX, P.wheel_go))
    for a, b in P.coils:
        track.fx(a, "rustle", b - a, 0.025, px(HW.OVEN_X, a))
    track.fx(P.fire_t[0], "rustle", 2.0, 0.04, px(HW.OVEN_X, P.fire_t[0]))
    for t0 in np.arange(P.fire_t[1], P.end - 3.0, 6.0):           # the fire, a soft crackle now and then
        track.fx(t0, "crackle", 1.2, 0.012, px(HW.OVEN_X, t0))
    for a, b, tg in P.flares:
        track.hit(a + 0.5, "plink", 67, 0.06, 0.0)
    track.fx(P.knead[0], "rustle", P.knead[1] - P.knead[0], 0.03, px(DOUGH[0], P.knead[0]))
    for j, a in enumerate(getattr(P, "animals", [])):
        track.hit(a["out"][0] + 0.4, "pluck", 64 + 2 * j, 0.04, px(a["home"], a["out"][0]))
    for j, b in enumerate(getattr(P, "birds", [])):                # a little chirp as each bird lands
        track.hit(b["fly"][1], "plink", 79 + 2 * (j % 3), 0.035, px(b["perch"][0], b["fly"][1]))
    bed = {"type": "procedural", "name": "keepers_song", "gain": 0.9, "chords": chords,
           "reverb": {"decay": 3.5, "wet": 0.4, "tone": 2600}}

    class Shim:
        p = {"audio": {}}
        events_gain = 1.0
        reverb = None
    sc_ = Shim()
    sc_.bed = bed
    sc_.narration = [(t0, voiced(tx)) for t0, tx in P.narration()]
    wav, stats = narr_mix(sc_, track, P.end)
    import shutil
    shutil.move(wav, path)
    return path, stats, track
