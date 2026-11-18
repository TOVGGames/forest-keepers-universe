"""Forest Keepers episode 11, Who's Awake Tonight?, in the flat picture-book look (a remake of FK0008: the approved
story, narration and animals of docs/engines/forest_keepers_night_animals.md, with the owner's notes; staging:
docs/engines/forest_keepers_night_flat.md). The world is night_flat_world.py.

Stateless: every frame is a pure function of time t (s), so frames render in parallel (experiments/keepers_flat/
ep11.py). Six Keepers (no Sprout yet: she comes in ep 12), the new faces, the ep 14 walks.

A night walk to meet six night-time neighbours, one spotted by each Keeper, in six clearings along the path. Owner
(FK0019): no long walks - they walk in from the edge of each clearing (a few steps), and when they set off again a
soft dip into the dark takes them on to the next one. At each: the narrator's hint, the animal shows itself and does
what it does, Glo's light turns the Field Guide's pages to the match and ticks the box, the name card while the
narrator reads its line, the animal goes on its way, the Keepers set off.

    plan().end                              the timeline
    frame(pg, valley, t)                    draw one frame onto a flat.FlatPage
"""
import math

import numpy as np
import skia

from families.foundry.keepers.common import smoothstep
from families.foundry.products.monster import TURN_NARROW, TWIGS_FORE, TWIGS_UPPER, WHEELS_FORE, WHEELS_UPPER

from . import illustrate as il
from . import night_flat_world as NW
from .animals import ANIMALS, F, _c, cute_eye, draw_animal, raccoon_wash, walk_leg
from .flat_motion import Hopper, WaveGait, arm_swing, biped, hans_mood, heading, roll_swing, walk_path
from .storybook import C, oval, rrect, smooth, tone

W, H, K, GB = NW.W, NW.H, NW.K, NW.GB
FPS = 60
STEP = 1.0 / FPS
ORDER = ["digger", "springs", "teeth", "tentacles", "wheels", "lantern"]
WALKERS = ["digger", "springs", "teeth", "tentacles", "wheels"]
BACK = ["digger", "springs", "teeth", "tentacles"]                 # the line behind Wheels, left to right
NAMES = {"teeth": "Twigs", "wheels": "Wheels", "digger": "Digs", "springs": "Springs", "tentacles": "Hans",
         "lantern": "Glo"}
KH = {"wheels": 420, "tentacles": 610, "teeth": 760, "springs": 340, "lantern": 600, "digger": 300}
HALF = {"wheels": 112, "tentacles": 118, "teeth": 92, "springs": 110, "lantern": 105, "digger": 135}
V_WALK = 95.0
EASE = 1.0
ENTER = 250.0                       # the few steps they walk into each clearing, and on out of it
ENTER_IN = {"deer": 120.0}           # the deer's clearing: they creep in slowly, so fewer steps
ENTER_OUT = {"fox": 50.0}            # (advisor FK0023 r8: 250 px on walked the cart into the sitting fox's tail) out of
                                     # the fox's clearing they take just a step before the picture dips
CRUISE = 160.0                      # Glo floats this high
GAP = 40.0                          # between two Keepers in the line

# ----------------------------------------------------------------------------------------------- narration
# the approved FK0008 script (owner after its first render: she talks a little less and slower, never more). One fix:
# Glo is "he" in every episode (the old line said "her").

OPEN = "The moon is up, and the forest is quiet. Tonight, the Keepers are going to meet the neighbours who stay up late."
FINDS = [
    dict(kind="raccoon", finder="tentacles", zone=0, x=NW.RACCOON_X, s=152.0,
         hint="Hans has spotted little ripples on the pond...",
         line="A raccoon. Its little hands are so sensitive, it can feel its food without even looking."),
    dict(kind="owl", finder="teeth", zone=1, x=NW.OWL_X, s=148.0,
         hint="Twigs hears something, high in the old oak. Who... who's there?",
         line="A barred owl. It calls, who cooks for you? And it flies almost without a sound."),
    dict(kind="opossum", finder="lantern", zone=2, x=(NW.LOG[0] + NW.LOG[1]) / 2, s=170.0,
         hint="Glo turns his light down low, so he won't startle anyone.",
         line="An opossum, with her babies riding on her back. She's North America's only marsupial."),
    dict(kind="squirrel", finder="springs", zone=3, x=(NW.TREE_A + NW.TREE_B) / 2, s=150.0,
         hint="Springs bounces up for a better look. Something is up in that tree...",
         line="A flying squirrel. It doesn't really fly... it glides, on a furry skin between its legs."),
    dict(kind="fox", finder="wheels", zone=4, x=NW.FOX_X, s=133.0,
         hint="Out in the meadow, Wheels stops, very still.",
         line="A red fox. Its big ears can hear a mouse squeak, under the leaves."),
    dict(kind="deer", finder="digger", zone=5, x=NW.DEER_X, s=249.0,
         hint="At the edge of the forest... shh. Slowly now.",
         line="A white-tailed deer, and her fawn. Her white tail is a little flag that says: watch out."),
]
FINALE = "Six night-time neighbours, all found. Goodnight, forest."
SIGNOFF = "What should the Keepers do next? Tell us in the comments."
END_TEXT = "WHAT SHOULD THEY DO NEXT?"             # owner, FK0008
HOLD_END = 4.5
PAIR_ROOM = 55.0
RACCOON_TURN = 0.6
OPOSSUM_TURN = 0.8
OWL_FLIGHT = 4.5
SPRINGS_STEP = 70.0

# where everyone stands at each find: the cart this far short of the animal, the finder this far
CART_DX = {"raccoon": 560.0, "owl": 470.0, "opossum": 440.0, "squirrel": 590.0, "fox": 450.0, "deer": 560.0}
FINDER_DX = {"raccoon": 250.0, "owl": 200.0, "opossum": 330.0, "squirrel": 350.0, "fox": 0.0, "deer": 300.0}
RIGHT = {"raccoon": NW.HIDE[0] + 150.0, "owl": NW.OAK_X + 140.0, "opossum": NW.HIDE[2] + 40.0,
         "squirrel": NW.TREE_B + 170.0, "fox": NW.HIDE[4] + 40.0, "deer": NW.DEER_X + 480.0}
WATCH = {"raccoon": 5.5, "owl": 5.0, "opossum": 6.0, "squirrel": 5.0, "fox": 5.0, "deer": 6.0}   # from the reveal to
                                    # the guide's page (advisor r1: 18 s of nothing, then the narration explained it)
LEAVE = {"raccoon": 6.0, "owl": 3.0, "opossum": 10.0, "squirrel": 7.0, "fox": 6.5, "deer": 9.0}
CHECK_HW = {"wheels": 114.5, "tentacles": 150.3, "teeth": 73.4, "springs": 71.7, "digger": 108.0}


def word_times(text, t0):
    """{word: when the narrator says it} for a line starting at t0 (its take's word timings)."""
    from .narrator import take
    out = {}
    for w_ in take(text).get("words") or []:
        k = "".join(ch for ch in (w_.get("word") or w_.get("text") or "").lower() if ch.isalpha())
        out.setdefault(k, t0 + float(w_.get("start", 0.0)))
    return out


def apart(a, b):
    """How far apart two Keepers stand in the line: their walk-through boxes (ep11.py) may overlap only a little
    (under a fifth of the narrower one), and a little room besides."""
    extra = PAIR_ROOM if {a, b} == {"springs", "teeth"} else 0.0      # (advisor FK0023 r2: Twigs' arm hung over
    return CHECK_HW[a] + CHECK_HW[b] - 0.4 * min(CHECK_HW[a], CHECK_HW[b]) + 14.0 + extra   # Springs' face)
PUSH = 196.0                        # Wheels stands this far behind the cart's middle (his pincer on its handle)
CART_HW = 92.0
BOOK_Y = GB - 330.0                 # the open book's middle (on the cart's lectern, at the Keepers' eye level)
BOOK_W, BOOK_H = 150.0, 96.0        # one page


def _dur(text):
    from .narrator import take
    return take(text)["duration"]


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-9), 0.0), 1.0)


def ease(t, a, b):
    return smoothstep(_seg(t, a, b))


def bump(t, a, d):
    u = _seg(t, a, a + d)
    return math.sin(math.pi * u) if 0 < u < 1 else 0.0


def lerp(a, b, u):
    return a + (b - a) * u


def lerp2(p, q, u):
    return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)


class Cuts:
    """A gait (or hopper) per stretch between two dips: no foot is planted across a cut."""

    def __init__(self, segs):
        self.segs = segs                                           # [(t_end, gait)]

    def pick(self, t):
        for b, g in self.segs:
            if t < b:
                return g
        return self.segs[-1][1]

    def __getattr__(self, k):
        attr = getattr(self.segs[0][1], k)
        if not callable(attr):
            return attr

        def f(*args, **kw):
            t = args[-1] if args else kw["t"]
            return getattr(self.pick(t), k)(*args, **kw)
        return f


def hw(kd):
    return HALF[kd] * K


# ----------------------------------------------------------------------------------------------- the plan

class Plan:
    def __init__(self):
        self.say = []                                              # (t, text)
        self.cuts = []                                             # the dips into the dark (the act breaks)
        self.walks = {kd: [] for kd in WALKERS}
        self.glo_keys = []
        self.cam_keys = []
        self.voice_events = []
        self.flares = []                                           # (t0, t1) Glo's light flares (pages, ticks)
        self.hans = {s: [] for s in (-2, -1, 0, 1, 2)}
        self.springs_hops = []                                     # (t0, t1, height) a big bounce up to look
        self.F = []
        self.pages = []                                            # (t, from page, to page) the book's page turns
        t = self._open()
        for i, f in enumerate(FINDS):
            if i > 0:
                t = self._dip(i, t)
            t = self._find(i, f, t)
        self._finale(t)
        self._finish()
        self.voices = voices(self)

    # ---------------------------------------------------------------- helpers
    def slots(self, i):
        """Where everyone stands at find i: the finder nearest the animal, the cart between, Wheels pushing it, the
        others in a line behind him (nobody walks past a wild animal); Glo over the cart (or, when it's his find,
        out in front)."""
        f = FINDS[i]
        A, kind, fk = f["x"], f["kind"], f["finder"]
        cart = A - CART_DX[kind]
        pos = {"wheels": cart - PUSH}
        if fk in BACK:
            pos[fk] = A - FINDER_DX[kind]
        prev = "wheels"
        for kd in reversed(BACK):
            if kd in pos:
                continue
            pos[kd] = pos[prev] - apart(prev, kd)
            prev = kd
        # (advisor r1: he hid behind Twigs and behind the field guide.) Over Digs' head at the back of the line (Digs
        # is the shortest: Glo floats clear above him, nobody in front), or, for his own find, out past the guide
        over = min(BACK, key=lambda k: pos[k])
        pos["lantern"] = (A - 200.0) if fk == "lantern" else (pos[over] + 10.0)
        return pos

    def walk(self, kd, t0, x1, v=V_WALK):
        keys = self.walks[kd]
        x0 = keys[-1][1]
        t0 = max(t0, keys[-1][0])
        if abs(x1 - x0) < 1:
            return t0
        keys.append((t0, x0))
        t1 = t0 + abs(x1 - x0) / v + EASE
        keys.append((t1, x1))
        return t1

    def glo_to(self, t0, x1, v=V_WALK):
        x0 = self.glo_keys[-1][1]
        t0 = max(t0, self.glo_keys[-1][0])
        if abs(x1 - x0) < 1:
            return t0
        self.glo_keys.append((t0, x0))
        t1 = t0 + abs(x1 - x0) / v + EASE
        self.glo_keys.append((t1, x1))
        return t1

    def line(self, t, text):
        self.say.append((t, text))
        return t + _dur(text)

    def hans_hold(self, slot, t0, t1, fn, reach=0.8, back=0.8):
        self.hans[slot].append((t0 - reach, t1 + back, fn, (t0 - reach, t0, t1, t1 + back)))

    def shift(self, t):
        return self.cam(t) - W / 2

    def cam_for(self, i, enter=False):
        S = self.slots(i)
        lo = min(S[k] - CHECK_HW[k] for k in BACK + ["wheels"]) - 24.0
        hi = RIGHT[FINDS[i]["kind"]]
        return (lo + hi) / 2

    # ---------------------------------------------------------------- the opening (by the pond)
    def _open(self):
        S = self.slots(0)
        for kd in WALKERS:
            self.walks[kd].append((0.0, S[kd] - ENTER))
        self.glo_keys.append((0.0, S["lantern"] - ENTER))
        c0 = self.cam_for(0)
        self.cam_keys += [(0.0, c0 - ENTER)]
        t = self.line(1.5, OPEN)
        self.tags = (2.0, max(9.0, t - 1.0))                       # the name tags, while she sets the scene
        self.book_open = t - 0.5                                   # Glo's light opens the Field Guide
        self.flares.append((self.book_open - 0.3, self.book_open + 1.1))
        self.pages.append((self.book_open, -1, 0))
        self.voice_events.append((self.book_open + 1.2, "wheels", "ooh", None))
        self.title = (self.book_open + 1.6, self.book_open + 9.6)
        self.voice_events.append((self.title[0] + 2.0, "springs", "hehe", None))
        go = self.title[1] - 1.5
        arrive = self._walk_in(0, go)
        self.cam_keys += [(go, c0 - ENTER), (arrive, c0)]
        return arrive

    def _walk_in(self, i, t0):
        S = self.slots(i)
        ends = []
        v = V_WALK * (0.6 if FINDS[i]["kind"] == "deer" else 1.0)  # "shh... slowly now": they creep in
        for j, kd in enumerate(sorted(WALKERS, key=lambda k: -S[k])):  # the front of the line sets off first
            ends.append(self.walk(kd, t0 + 0.15 * j, S[kd], v=v))
        ends.append(self.glo_to(t0 + 0.2, S["lantern"], v=v))
        return max(ends)

    # ---------------------------------------------------------------- on to the next clearing (a soft dip)
    def _dip(self, i, t):
        """They set off (a few steps on), the picture dips into the dark, and they walk into the next clearing."""
        Sp = self.slots(i - 1)
        out = ENTER_OUT.get(FINDS[i - 1]["kind"], ENTER)
        ends = []
        for j, kd in enumerate(sorted(WALKERS, key=lambda k: -Sp[k])):
            ends.append(self.walk(kd, t + 0.12 * j, Sp[kd] + out))
        ends.append(self.glo_to(t + 0.2, Sp["lantern"] + out))
        c = max(ends) + 0.05                                       # the cut: everyone has stopped, in the dark
        self.cuts.append(c)
        S = self.slots(i)
        en = ENTER_IN.get(FINDS[i]["kind"], ENTER)                 # (advisor FK0023 r3: the slow creep to the deer
        for kd in WALKERS:                                         # took 6.5 s from 250 px: a shorter way in)
            self.walks[kd] += [(c, self.walks[kd][-1][1]), (c + 0.002, S[kd] - en)]
        self.glo_keys += [(c, self.glo_keys[-1][1]), (c + 0.002, S["lantern"] - en)]
        cprev, cnext = self.cam_for(i - 1), self.cam_for(i)
        self.cam_keys += [(c, cprev + 0.0), (c + 0.002, cnext - en * 0.6)]
        arrive = self._walk_in(i, c + 0.3)
        self.cam_keys += [(c + 0.3, cnext - en * 0.6), (arrive + 0.5, cnext)]
        return arrive

    # ---------------------------------------------------------------- a find
    def _find(self, i, f, arrive):
        kind, fk = f["kind"], f["finder"]
        T = dict(arrive=arrive)
        T["hint"] = arrive - 1.6
        T["hint_end"] = self.line(T["hint"], f["hint"])
        T["reveal"] = T["hint_end"] + 0.2
        self.voice_events += [(T["hint_end"] + 0.4, fk, "ooh", None)]
        others = [k for k in ORDER if k != fk]
        self.voice_events += [(T["hint_end"] + 1.4, others[1], "ooh", None),
                              (T["hint_end"] + 2.0, others[3], "mm", None)]
        b = T["reveal"] + WATCH[kind]
        T["book"] = b
        T["flips"] = [b + 0.3]                                     # one turn, straight to its page (advisor r1: the
        cur = self.pages[-1][2]                                    # in-between blank pages confused)
        self.pages.append((b + 0.3, cur, i + 1))
        T["tick"] = b + 1.7
        self.flares += [(b, b + 1.4), (T["tick"] - 0.3, T["tick"] + 0.9)]
        t_l = b + 2.6
        e_l = self.line(t_l, f["line"])
        T["line"] = t_l
        T["words"] = word_times(f["line"], t_l)                    # its key moment on the narrator's own words
        T["card"] = (t_l - 0.3, e_l + 3.6)
        self.voice_events += [(e_l + 0.6, others[0], "aww", None), (e_l + 1.6, others[2], "hehe", None)]
        self.voice_events.append((T["tick"] + 0.3, fk, "yay", None))
        T["leave"] = T["card"][1] - 1.0
        T["gone"] = T["leave"] + LEAVE[kind]
        self.voice_events.append((T["leave"] + 1.6, fk, "aww", None))
        if fk == "tentacles":                                      # Hans points at the ripples on the pond
            tip = (f["x"] - 175.0, NW.POND_NEAR - 24.0)               # (advisor r3: not across its face)
            self.hans_hold(1, T["hint"] + 1.6, T["hint"] + 5.2, lambda tt, tip=tip: tip)
        if fk == "springs":                                        # two big bounces up to see into the tree
            for q in range(2):
                a = max(T["arrive"] + 0.8, T["hint"] + 0.8) + q * 1.5
                self.springs_hops.append((a, a + 1.1, 200.0 - 40.0 * q))
        T["point"] = (max(T["arrive"] + 0.6, T["hint"] + 1.2), T["hint"] + 7.5)   # Twigs points up at the owl
        self.F.append(T)
        return T["gone"] + (0.5 if kind != "owl" else 1.5)

    # ---------------------------------------------------------------- the end
    def _finale(self, t):
        # (advisor FK0023 r2: at the end sign Springs stood half behind Twigs' arm and the group filled only the
        # left of the frame) Springs takes a step to his left, Glo floats along over him, and the camera eases over
        # to put the whole group in the middle of the frame
        S = self.slots(len(FINDS) - 1)
        self.walk("springs", t + 0.2, S["springs"] - SPRINGS_STEP)
        self.glo_to(t + 0.2, self.glo_keys[-1][1] - SPRINGS_STEP)
        lo = S["springs"] - SPRINGS_STEP - CHECK_HW["springs"]
        hi = max(S[k] + CHECK_HW[k] for k in WALKERS)
        c0 = sorted(self.cam_keys)[-1][1]
        self.cam_keys += [(t, c0), (t + 3.5, (lo + hi) / 2)]
        cur = self.pages[-1][2]
        self.fin_flip = t + 0.5
        self.pages.append((self.fin_flip, cur, 0))
        self.flares.append((self.fin_flip - 0.3, self.fin_flip + 1.1))
        t_f = self.fin_flip + 4.0
        e_f = self.line(t_f, FINALE)
        self.fin_card = (self.fin_flip + 3.5, e_f + 2.2)
        self.cheer = self.fin_card[1] - 1.6
        self.voice_events += [(self.cheer + 0.3 * j, kd, "yay", None) for j, kd in enumerate(ORDER)]
        self.fire_up = self.F[-1]["leave"]
        self.signoff = self.fin_card[1] + 1.5
        self.line(self.signoff, SIGNOFF)
        self.sign = (self.signoff - 0.6, self.signoff + 0.4)
        self.end = self.signoff + _dur(SIGNOFF) + 2.5

    # ---------------------------------------------------------------- paths, gaits, camera
    def _finish(self):
        cuts = self.cuts + [1e9]

        def part(keys, a, b):
            ks = [k for k in keys if a + 0.001 < k[0] <= b]        # after a cut: from the new spot on
            before = [k for k in keys if k[0] <= a + 0.001]
            if before and a < 0:
                ks = [(a + 1e-3, before[-1][1])] + ks
            return walk_path(ks or [(a, keys[-1][1])], EASE)

        self.paths = {kd: walk_path(self.walks[kd], EASE) for kd in WALKERS}
        self.paths["lantern"] = walk_path(self.glo_keys, EASE)
        self.turns = {kd: heading(self.paths[kd], ahead=0.8) for kd in ORDER}
        bounds = list(zip([-1e9] + self.cuts, cuts))
        narrow = lambda kd, f=1.0: (lambda t: 1.0 - TURN_NARROW * f * abs(self.turns[kd](t)))   # noqa: E731
        self.gaits = {}
        for kd in ("teeth", "digger"):
            self.gaits[kd] = Cuts([(b, biped(kd, part(self.walks[kd], a, b), GB, K, spread=narrow(kd)))
                                   for a, b in bounds])
        self.gaits["tentacles"] = Cuts([(b, WaveGait(GB, K, part(self.walks["tentacles"], a, b),
                                                     spread=narrow("tentacles", 0.5))) for a, b in bounds])
        self.hopper = Cuts([(b, Hopper(part(self.walks["springs"], a, b), GB, K)) for a, b in bounds])
        self.cam = walk_path(sorted(self.cam_keys), 2.5)

    def glo_x(self, t):
        return self.paths["lantern"](t)

    def glo_y(self, t):
        return GB - CRUISE

    def find_at(self, t):
        """(i, T) of the find going on at t (the last one after the end)."""
        for i, T in enumerate(self.F):
            nxt = self.cuts[i] if i < len(self.cuts) else 1e9
            if t < nxt:
                return i, T
        return len(self.F) - 1, self.F[-1]

    def found(self, t):
        return sum(1 for T in self.F if t >= T["tick"])

    def cart_x(self, t):
        return self.paths["wheels"](t) + PUSH

    def narration(self):
        return sorted(self.say)

    def lamp(self, t):
        """Glo's lamp: dimmed low for the opossum, flaring up to turn pages and tick boxes."""
        T = self.F[2]
        dim = ease(t, T["hint"], T["hint"] + 2.5) * (1 - ease(t, T["gone"] - 1.0, T["gone"] + 2.0))
        return (1.0 - 0.62 * dim) + 0.9 * glo_flare(self, t)


PLAN = None


def plan():
    global PLAN
    if PLAN is None:
        PLAN = Plan()
    return PLAN


def glo_flare(P, t):
    u = 0.0
    for a, b in P.flares:
        u = max(u, ease(t, a - 0.3, a + 0.2) * (1 - ease(t, b - 0.2, b + 0.4)))
    return u


def glo_reach(P, t):
    """How far the flare's beam has reached from the lantern to the book (it gets there before the page moves)."""
    u = 0.0
    for a, b in P.flares:
        if a - 0.3 <= t <= b + 0.4:
            u = max(u, ease(t, a - 0.3, a + 0.2))
    return u


def glo_bob(t):
    return 14 * K * math.sin(t * 1.3)


# ----------------------------------------------------------------------------------------------- the animals

BOOK_ARC = 340.0      # and on their way to the book (over the friends standing between Glo and the cart)
RACCOON_ARC = 340.0   # how high Glo's sparkles arc on their way to the raccoon (over Twigs' antlers and Hans' head)


def raccoon_lit(T, t):
    """0 (a shadow by the dark pond) .. 1 (in Glo's light, found)."""
    return ease(t, T["reveal"] - 0.4, T["reveal"] + 1.0)


def _dim(col, k):
    """col darkened into the night shadow by k (0 none .. 1 the shadow colour)."""
    return tuple(int(a + (b - a) * k) for a, b in zip(col, (18, 20, 34)))


def animal(P, i, t):
    """-> (x, y, pose kw, visible, what it's doing) of find i's animal at t (world px; y = where it stands). Each one
    does its key thing on the narrator's words (advisor r1: the glide came 18 s before "it glides", the raccoon never
    washed, the owl had no discovery, the opossum popped onto its log)."""
    f, T = FINDS[i], P.F[i]
    k, x0, s = f["kind"], f["x"], f["s"]
    r0, lv, w = T["reveal"], T["leave"], T["words"]
    if k == "raccoon":
        # already at the water's edge, washing (the ripples Hans spots); it looks up at us when it's found and on
        # "without even looking" (still washing); then back behind the bush
        hx = NW.HIDE[0] + 140.0
        if t < lv:                                                 # (advisor FK0023 r4: it walked in in plain view
            look = max(ease(t, r0 + 0.3, r0 + 1.2) * (1 - ease(t, r0 + 3.2, r0 + 4.1)),   # before the ripples line:
                       ease(t, w["without"] - 0.3, w["without"] + 0.5) * (1 - ease(t, lv - 2.4, lv - 1.4)))
            wash = 1.0 - ease(t, lv - 1.4, lv - 0.2)               # now it is there from the start, washing in the
            kw = dict(face=-1, wash=wash, walk=0.0, gait=0.0, look=look,   # dark, a shadow till Glo's light finds it)
                      blink=bump(t % 4.7, 0.0, 0.22), lit=raccoon_lit(T, t))
            return x0, NW.FLOOR, kw, True, "washes"
        q = _seg(t, lv, lv + RACCOON_TURN)                         # turns round on the spot (advisor FK0023 r2: it
        u = _seg(t, lv + RACCOON_TURN, lv + RACCOON_TURN + 5.0)    # flipped in one frame), then back to the bush
        x = lerp(x0, hx + 260.0, smoothstep(u))
        kw = dict(face=-1 if q < 0.5 else 1, squash=max(0.12, abs(math.cos(math.pi * q))),
                  walk=1.0 if 0 < u < 1 else 0.0, gait=(x - x0) / (0.44 * s))
        return x, NW.FLOOR, kw, x < hx + 240.0, "walks" if 0 < u < 1 else "turns"
    if k == "owl":
        # dark in the dark tree till Glo's light finds it (only its eyes shine); it calls on "who cooks for you"
        hd = 0.6 * math.sin(t * 0.35) if t < r0 else 0.7 * math.sin((t - r0) * 0.5)
        call = min(1.0, bump(t, T["hint"] + 1.5, 0.9) + bump(t, T["hint"] + 2.8, 0.9) +
                   sum(bump(t, w[k_], 0.45) for k_ in ("who", "cooks", "for", "you") if k_ in w))
        lit = ease(t, r0 - 0.4, r0 + 1.0)
        fl = owl_takeoff(P, i)                                     # on "it flies": wings open on the branch, then off
        sp = ease(t, fl - 0.8, fl)                                 # over the oak into the dark, slow soft wingbeats
        u = _seg(t, fl, fl + OWL_FLIGHT)                           # (advisor FK0023 r2: it never flew)
        x = x0 + 1150.0 * u ** 1.4
        y = NW.OWL_Y + 60.0 * math.sin(math.pi * min(1.0, u * 1.8)) - 420.0 * u * u
        flap = math.sin(2 * math.pi * 0.9 * (t - fl)) if u > 0 else 0.0
        kw = dict(head=hd * (1 - sp) + 0.7 * sp, call=call, blink=bump(t % 5.3, 0.0, 0.25), lit=lit, wings=sp,
                  flap=flap * sp, tilt=0.22 * smoothstep(min(1.0, u * 3.0)))
        return x, y, kw, x - P.shift(t) < W + 400, "flies" if u > 0 else "perches"
    if k == "opossum":
        # out from behind the bush on the log's far side, along the ground to the log's end, up onto it (her feet on
        # its top), and along it with the babies on her back; later back down off that end and behind the bush
        a, b = NW.LOG[0] + 60.0, NW.LOG[1] - 40.0
        hx = NW.HIDE[2]
        xm = lerp(a, b, 0.45)
        # (advisor FK0023 r3: she walked off the log's end at its top's height and floated down into the bush, her
        # body over the cut end.) On the ground she keeps clear of the log's end; she climbs up and down that end
        # nose first (tilted), her front feet at the very end on top
        e_top = NW.LOG[1] - 0.3 * s                                # on top, her front feet at the end
        e_gnd = NW.LOG[1] + 0.62 * s                               # on the ground beside the end (nose at it)
        t_out, t_end, t_up = r0 - 0.4, r0 + 2.6, r0 + 4.0
        tilt = 0.0
        if t < lv:
            if t < t_end:                                          # on the ground, to the log's end
                x = lerp(hx, e_gnd, smoothstep(_seg(t, t_out, t_end)))
                y = NW.FLOOR
                walking = t_out < t < t_end
            elif t < t_up:                                          # up the end, nose first
                u = smoothstep(_seg(t, t_end, t_up))
                x = lerp(e_gnd, e_top, u)
                y = lerp(NW.FLOOR, NW.LOG_TOP, u)
                tilt = 0.6 * math.sin(math.pi * u)
                walking = True
            else:                                                  # along its top, during the line
                u = smoothstep(_seg(t, t_up + 0.3, T["line"] + 4.0))
                x = lerp(e_top, xm, u)
                y = NW.LOG_TOP
                walking = 0 < u < 1
            kw = dict(face=-1, walk=1.0 if walking else 0.0, gait=(hx - x) / (0.4 * s), babies=3,
                      sniff=0.5 * math.sin(t * 3.0), blink=bump(t % 5.1, 0.0, 0.2), tilt=tilt)
            return x, y, kw, x < hx - 30.0 or t > t_end, "walks" if walking else "sniffs"
        l2 = lv + OPOSSUM_TURN                                     # she turns round on the spot first (advisor
        tb = l2 + max(1.5, (e_top - xm) / 45.0)                    # FK0023 r5: a one-frame mirror flip on the log)
        tc = tb + 1.4
        td = max(lv + LEAVE[k] - 1.0, tc + 1.5)
        if t < l2:
            q = _seg(t, lv, l2)                                    # facing left, seen from behind, facing right
            kw = dict(face=-1 if q < 0.3 else (0 if q < 0.7 else 1), squash=turn_squash(q), walk=0.0, gait=0.0,
                      babies=3, sniff=0.0)
            return xm, NW.LOG_TOP, kw, True, "turns"
        if t < tb:                                                 # along the top to the end
            x, y = lerp(xm, e_top, smoothstep(_seg(t, l2, tb))), NW.LOG_TOP
        elif t < tc:                                               # down the end, nose first
            u = smoothstep(_seg(t, tb, tc))
            x, y = lerp(e_top, e_gnd, u), lerp(NW.LOG_TOP, NW.FLOOR, u)
            tilt = 0.6 * math.sin(math.pi * u)
        else:                                                      # and along the ground behind the bush
            x, y = lerp(e_gnd, NW.HIDE[2] + 200.0, smoothstep(_seg(t, tc, td))), NW.FLOOR
        kw = dict(face=1, walk=1.0 if l2 < t < td else 0.0, gait=(x - a) / (0.4 * s), babies=3,
                  sniff=0.5 * math.sin(t * 3.0), tilt=tilt)
        return x, y, kw, x < NW.HIDE[2] + 180.0, "walks"
    if k == "squirrel":
        sx, sy, sp, phi, climb = squirrel_at(P, i, t)
        g0, _, ln = squirrel_times(P, i)
        return sx, sy, dict(spread=sp, phi=phi, climb=climb), sy > NW.CROWN_Y + 60.0, \
            "glides" if g0 <= t < ln else "climbs"
    if k == "fox":
        # sitting very still in the long grass; its ears turn on "its big ears can hear"; it stays as they go on
        # (advisor FK0023 r5: frozen like a cut-out for 33 s) it breathes, its tail tip curls, it blinks, and once
        # found its ears swivel as it listens - a quick double flick on "its big ears"
        ears = math.sin(t * 0.9) * ease(t, r0, r0 + 1.0) * 0.8 + bump(t, w.get("ears", r0) - 0.3, 1.4) * \
            math.sin((t - w.get("ears", r0)) * 9.0)
        ears -= 1.6 * bump(t, T["gone"] + 0.4, 1.6)                 # flicked back at them as they set off
        ears = max(-1.0, min(1.0, ears))
        return x0, NW.FLOOR, dict(face=1, sit=1.0, ears=ears, tail=math.sin(t * 1.1), blink=bump(t % 3.7, 0, 0.2),
                                  alive=1.0), True, "sits"
    if k == "deer":
        # out of the trees at the forest's edge when they're found, grazing; head up during the line; her tail up like
        # a flag on "flag"; then away into the trees
        xin = x0 + 560.0
        come = smoothstep(_seg(t, r0 - 0.6, r0 + 3.2))
        up = ease(t, r0 + 3.4, r0 + 4.6) * (1 - ease(t, T["line"] + 1.2, T["line"] + 2.2)) + \
            ease(t, w["her"] - 0.4, w["her"] + 0.4)
        go = _seg(t, lv + 1.5, lv + LEAVE[k] + 3.0)
        x = lerp(xin, x0, come) + 900.0 * smoothstep(go) ** 1.2
        flag = ease(t, w["flag"] - 0.3, w["flag"] + 0.2) * (1 - ease(t, w["out"] + 0.8, w["out"] + 1.6)) + \
            ease(t, lv, lv + 1.2)
        walking = 0 < go < 1 or 0 < come < 1
        t0 = lv + 1.5 - DEER_TURN - 0.1
        kw = dict(face=deer_face(t, t0), squash=turn_squash(_seg(t, t0, t0 + DEER_TURN)), walk=1.0 if walking else 0.0,
                  dist=abs(x - x0),
                  flag=min(1.0, flag),
                  head_up=0.15 + 0.85 * min(1.0, up), ears=math.sin(t * 0.8))
        return x, NW.FLOOR, kw, x - P.shift(t) < W + 200, "walks" if walking else "grazes"
    return x0, NW.FLOOR, {}, True, ""


DEER_TURN = 0.9      # the doe and fawn turn round over this long before they go (FK0023 r4: a one-frame flip)


def deer_face(t, t0):
    """-1 (facing the Keepers, left) until t0, then turning round: seen from behind (0) in the middle, then 1."""
    q = _seg(t, t0, t0 + DEER_TURN)
    return -1 if q < 0.3 else (0 if q < 0.7 else 1)


def turn_squash(q):
    """How wide the side view is drawn as it turns (narrowing into the back view, widening out of it) so the turn reads
    as one movement, not a pose swap (FK0023 r5)."""
    if q <= 0.0 or q >= 1.0:
        return 1.0
    if q < 0.3:
        return 1.0 - 0.45 * smoothstep(q / 0.3)
    if q < 0.7:
        return 1.0
    return 0.55 + 0.45 * smoothstep((q - 0.7) / 0.3)


def fawn(P, t):
    f, T = FINDS[5], P.F[5]
    x0 = f["x"] + 250.0
    r0 = T["reveal"]
    come = smoothstep(_seg(t, r0 + 0.2, r0 + 3.8))
    up = ease(t, r0 + 4.0, r0 + 5.0) * (1 - ease(t, r0 + 8.0, r0 + 9.0)) + ease(t, T["leave"] - 1.0, T["leave"])
    go = _seg(t, T["leave"] + 1.8, T["leave"] + LEAVE["deer"] + 3.3)
    x = lerp(x0 + 520.0, x0, come) + 900.0 * smoothstep(go) ** 1.2
    walking = 0 < go < 1 or 0 < come < 1
    t0 = T["leave"] + 1.8 - DEER_TURN - 0.1
    return x, NW.FLOOR, dict(face=deer_face(t, t0), squash=turn_squash(_seg(t, t0, t0 + DEER_TURN)), fawn=True, walk=1.0 if walking else 0.0, dist=abs(x - x0),
                             head_up=0.25 + 0.75 * up, ears=math.sin(t * 1.3 + 1)), x - P.shift(t) < W + 200, "walks"


def squirrel_times(P, i):
    """(take-off, end of the glide, landed on B) for the flying squirrel."""
    g0 = P.F[i]["words"]["glides"] - 0.25                         # on "it glides"
    return g0, g0 + 2.4, g0 + 2.85


def owl_takeoff(P, i):
    return P.F[i]["words"].get("flies", P.F[i]["leave"] - 1.5) - 0.1


SQ_K = 1.3                           # the squirrel is drawn this much bigger than its find's s (advisor r3: tiny)
SQ_GLIDE = math.radians(100.0)       # its heading while it glides: to the right, a little nose-down


def squirrel_at(P, i, t):
    """The flying squirrel, seen from its back on the face of the trunk (so it never has to turn round): clinging on
    tree A below the leaves, it turns towards B and pushes off, its legs spread and the skin between them opens like a
    sail, it glides down to B, brings its nose up, folds in and lands head-up on B's trunk, then climbs up into B's
    crown. -> (x, y of its middle, spread 0..1, heading (rad, 0 = head up, + clockwise), climb).
    (advisor FK0023 r3: the cling and glide poses swapped in one frame and it squashed to a sliver to turn about.)"""
    T, s = P.F[i], FINDS[i]["s"] * SQ_K
    g0, g1, ln = squirrel_times(P, i)
    ax, ay = NW.TREE_A, SQ_A_Y
    bx, by = NW.TREE_B, SQ_B_Y
    if t < g0:
        return ax, ay + 5.0 * bump(t, g0 - 0.35, 0.5), 0.0, 0.0, 0.0
    if t < ln:
        u = smoothstep(_seg(t, g0, ln))
        x = lerp(ax, bx, u)
        y = lerp(ay, by, u) + 70.0 * math.sin(math.pi * u) * (1 - 0.5 * u)
        phi = SQ_GLIDE * smoothstep(_seg(t, g0, g0 + 0.45)) * (1 - smoothstep(_seg(t, g1 - 0.2, ln)))
        sp = smoothstep(_seg(t, g0 + 0.05, g0 + 0.55)) * (1 - smoothstep(_seg(t, g1 - 0.1, ln)))
        return x, y, sp, phi, 0.0
    up = smoothstep(_seg(t, T["leave"], T["leave"] + LEAVE["squirrel"] - 1.0))
    y = by - (by - (NW.CROWN_Y - 10.0)) * up
    return bx, y, 0.0, 0.0, (by - y) / (0.35 * s)


SQ_A_Y, SQ_B_Y = 600.0, 700.0        # its middle on tree A (head clear below the leaves) and where it lands on B


def squirrel_feet(P, i, t):
    """The point the storycheck follows: its middle (it's drawn about its middle the whole way now)."""
    x, y = squirrel_at(P, i, t)[:2]
    return x, y


def glider(c, x, y, s, t, spread=0.0, phi=0.0, climb=0.0):
    """The flying squirrel from its back: head up at phi 0 (phi turns it, + clockwise). spread 0: clinging, its feet
    gripping the bark and the furry skin folded along its sides; 1: gliding, legs straight out and the skin stretched
    between them like a little sail, the flat tail behind. climb: the feet take turns as it goes up."""
    BROWN, DARK, PALE = _c(160, 138, 114), _c(70, 58, 50), _c(222, 212, 196)
    ca, sa = math.cos(phi), math.sin(phi)

    def P(u, v):
        X, Y = u * s, -v * s
        return x + X * ca - Y * sa, y + X * sa + Y * ca

    def poly(uv, col):
        c.polygon([P(u, v) for u, v in uv], col)

    step = math.sin(2 * math.pi * climb * 2.5) * (1 - spread)
    sway = 0.05 * math.sin(t * 1.7) * (1 - spread)
    feet = {}
    for side in (-1, 1):
        f0 = (side * 0.13, 0.16 + side * 0.03 * step)
        h0 = (side * 0.13, -0.15 - side * 0.03 * step)
        f1, h1 = (side * 0.31, 0.2), (side * 0.29, -0.2)
        feet[side] = (lerp(f0[0], f1[0], spread), lerp(f0[1], f1[1], spread),
                      lerp(h0[0], h1[0], spread), lerp(h0[1], h1[1], spread))
    tail = [(-0.05, -0.15), (-0.075, -0.3), (-0.06, -0.45), (0.0, -0.52), (0.06, -0.45), (0.075, -0.3), (0.05, -0.15)]
    poly([(u + sway * (-v - 0.15) / 0.37, v) for u, v in tail], BROWN * 0.92)        # the flat tail
    for side in (-1, 1):                                                             # the furry skin, side to side
        fx, fy, hx, hy = feet[side]
        mx, my = (fx + hx) / 2 - side * 0.035 * spread, (fy + hy) / 2
        poly([(side * 0.05, 0.1), (fx, fy), (mx, my), (hx, hy), (side * 0.05, -0.11)], BROWN * 0.9)
        c.polyline([P(fx, fy), P(mx, my), P(hx, hy)], PALE * 0.9, 0.014 * s)
    for side in (-1, 1):                                                             # the legs and little paws
        fx, fy, hx, hy = feet[side]
        for (jx, jy), (px_, py_) in (((side * 0.06, 0.09), (fx, fy)), ((side * 0.06, -0.1), (hx, hy))):
            c.polyline([P(jx, jy), P(px_, py_)], BROWN * 0.84, 0.05 * s)
            c.circle(*P(px_, py_), 0.032 * s, PALE)
    poly([(0.1 * math.cos(a), 0.17 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 24, False)], BROWN)
    for side in (-1, 1):
        poly([(side * 0.06 + 0.03 * math.cos(a), 0.325 + 0.034 * math.sin(a)) for a in np.linspace(0, 6.28, 12, False)],
             BROWN * 0.88)                                                           # ears
    poly([(0.095 * math.cos(a), 0.24 + 0.1 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 24, False)],
         BROWN * 1.05)                                                               # round head
    for side in (-1, 1):                                                             # big dark eyes
        c.circle(*P(side * 0.068, 0.255), 0.036 * s, DARK * 0.45)
        c.circle(*P(side * 0.06, 0.27), 0.012 * s, _c(240, 240, 236))
    c.circle(*P(0.0, 0.335), 0.017 * s, _c(110, 80, 76))                            # nose


def deer_walk(c, x, y, s, t, face=1, fawn=False, walk=0.0, dist=0.0, flag=0.0, head_up=1.0, ears=0.0):
    """The white-tailed deer of animals.py (same shape, colours and markings) with walking legs on planted hooves:
    a hoof stays put on the ground while the body goes over it, then lifts and swings forward (animals.deer swings
    them as pendulums, which slides them along the ground)."""
    from .animals import deer, deer_back
    if face == 0:                                                  # seen from behind, as it turns round
        return deer_back(c, x, y, s * (0.92 if fawn else 1.0), t, flag=flag)
    if walk <= 0:
        return deer(c, x, y, s, t, face=face, fawn=fawn, flag=flag, head_up=head_up, ears=ears)
    stride = 0.3
    ph = (dist / (s * 0.84)) / (2 * stride)
    f = F(x, y, s, face, kx=0.84)
    COAT = _c(152, 108, 70) if not fawn else _c(180, 110, 62)
    WHITE, HOOF = _c(240, 234, 224), _c(38, 30, 26)

    def leg(hip, p, col, hind):
        _, kn, ft = walk_leg((hip[0], 0.0), 0.0, 0.0, p % 1.0, stride, 0.07)
        if hind:
            st = (hip[0] + 0.06, 0.36 + ft[1] * 0.6)
            hk = ((st[0] + ft[0]) / 2 - 0.07, 0.2 + ft[1])
            f.blob(c, [(hip[0] - 0.1, hip[1] + 0.06), (hip[0] + 0.1, hip[1] + 0.04), (st[0] + 0.04, st[1]),
                       (st[0] - 0.05, st[1] - 0.02)], col, 4)
            f.limb(c, st, hk, ft, 0.05, 0.026, col)
        else:
            kn2 = ((hip[0] + ft[0]) / 2 + 0.02, 0.22 + ft[1])
            f.limb(c, (hip[0] + 0.02, hip[1] + 0.06), (hip[0], hip[1] - 0.06), kn2, 0.07, 0.03, col)
            f.limb(c, (hip[0], hip[1] - 0.06), kn2, ft, 0.05, 0.026, col)
        f.oval(c, ft[0] + 0.015, ft[1] + 0.012, 0.025, 0.016, HOOF, 10)

    leg((-0.33, 0.54), ph + 0.5, COAT * 0.72, True)
    leg((0.28, 0.48), ph, COAT * 0.72, False)
    tail_up = 0.18 * flag
    f.blob(c, [(-0.46, 0.66), (-0.54, 0.66 + tail_up), (-0.58, 0.56 + tail_up * 1.3), (-0.5, 0.56)],
           WHITE if flag > 0.4 else COAT * 0.85, 4)
    body = [(-0.48, 0.58), (-0.44, 0.68), (-0.1, 0.66), (0.22, 0.7), (0.36, 0.72), (0.44, 0.6), (0.38, 0.4),
            (0.16, 0.36), (-0.2, 0.38), (-0.42, 0.44)]
    f.blob(c, body, COAT)
    f.blob(c, [(-0.36, 0.42), (-0.1, 0.38), (0.16, 0.37), (0.34, 0.42), (0.1, 0.45), (-0.2, 0.46)], WHITE * 0.96)
    leg((-0.36, 0.52), ph, COAT * 0.95, True)
    leg((0.32, 0.46), ph + 0.5, COAT * 0.95, False)
    if fawn:
        rs = np.random.default_rng(11)
        for k in range(22):
            f.oval(c, rs.uniform(-0.4, 0.3), rs.uniform(0.52, 0.66), 0.018, 0.014, WHITE, 8)
    hu, hv = 0.52 + 0.06 * head_up, 0.62 + 0.36 * head_up
    f.blob(c, [(0.3, 0.7), (0.4, 0.74), (hu - 0.02, hv + 0.02), (hu + 0.06, hv - 0.04), (0.5, 0.56), (0.42, 0.52)],
           COAT)
    f.oval(c, (0.46 + hu) / 2 + 0.04, (0.6 + hv) / 2 - 0.0, 0.04, 0.05, WHITE, 14)
    for k, du in enumerate((-0.03, 0.03)):
        tilt = 0.04 * ears * (1 if k else -1)
        f.blob(c, [(hu + du - 0.02, hv + 0.05), (hu + du - 0.12 + tilt, hv + 0.15), (hu + du - 0.07 + tilt, hv + 0.18),
                   (hu + du + 0.03, hv + 0.07)], COAT * (0.8 if k == 0 else 1.02), 4)
        if k:
            f.blob(c, [(hu + du - 0.02, hv + 0.06), (hu + du - 0.1 + tilt, hv + 0.15), (hu + du + 0.01, hv + 0.08)],
                   WHITE * 0.85, 3)
    f.blob(c, [(hu - 0.06, hv + 0.02), (hu + 0.0, hv + 0.08), (hu + 0.1, hv + 0.06), (hu + 0.24, hv - 0.04),
               (hu + 0.25, hv - 0.08), (hu + 0.14, hv - 0.09), (hu + 0.0, hv - 0.06)], COAT * 1.05)
    f.oval(c, hu + 0.08, hv + 0.028, 0.034, 0.03, WHITE, 14)
    cute_eye(c, f, hu + 0.08, hv + 0.028, 0.025)
    f.blob(c, [(hu + 0.16, hv - 0.02), (hu + 0.2, hv - 0.01), (hu + 0.21, hv - 0.08), (hu + 0.16, hv - 0.08)],
           WHITE, 3)
    f.oval(c, hu + 0.235, hv - 0.065, 0.022, 0.02, HOOF, 10)


def draw_one(pg, kind, x, y, s, t, kw, sh):
    if kw.get("face") == 0:
        kw.pop("squash", None)
    if kind == "opossum" and kw.get("face") == 0:                    # seen from behind as she turns round
        from .animals import opossum_back
        il.creature(pg, lambda cv: opossum_back(cv, x - sh, y, s, t, babies=kw.get("babies", 3)), x - sh, y,
                    shadow=0.35 * s)
        return
    sq, tilt = kw.pop("squash", 1.0), kw.pop("tilt", 0.0)
    if sq < 0.999 or abs(tilt) > 1e-4:                             # turning round (squashed side to side), banking
        c = pg.c
        c.save()
        cy = y - (0.6 * s if kind == "owl" else 0.0)
        c.translate(x - sh, cy)
        c.rotate(math.degrees(tilt))
        c.scale(sq, 1.0)
        c.translate(-(x - sh), -cy)
        draw_one(pg, kind, x, y, s, t, kw, sh)
        c.restore()
        return
    lit = kw.pop("lit", None)
    if lit is not None and lit < 0.999:                              # in the dark: a shadow with shining eyes
        c = pg.c
        c.saveLayer()
        il.creature(pg, lambda cv: draw_animal(cv, kind, x - sh, y, s, t, **kw), x - sh, y, shadow=None)
        c.drawPaint(skia.Paint(Color=skia.Color(18, 20, 34, int(235 * (1 - lit))), BlendMode=skia.BlendMode.kSrcATop))
        c.restore()
        if lit < 0.6 and kind == "owl":
            for d in (-1, 1):
                pg.glow(x - sh + d * 0.11 * s, y - 0.86 * s, 10, "#ffe2a0", 0.6 * (1 - lit / 0.6))
                pg.flat(oval(x - sh + d * 0.11 * s, y - 0.86 * s, 3.2, 3.2), "#fff0c0", 1 - lit / 0.6)
        return
    if kind == "squirrel":
        il.creature(pg, lambda cv: glider(cv, x - sh, y, s * SQ_K, t, **kw), x - sh, y, shadow=None)
        return
    if kind == "deer":
        il.creature(pg, lambda cv: deer_walk(cv, x - sh, y, s, t, **kw), x - sh, y, shadow=0.3 * s)
    else:
        shadow = None if kind in ("owl", "squirrel") else 0.35 * s
        il.creature(pg, lambda cv: draw_animal(cv, kind, x - sh, y, s, t, **kw), x - sh, y, shadow=shadow)


def draw_animals(pg, P, t, sh):
    i, T = P.find_at(t)
    f = FINDS[i]
    x, y, kw, vis, _ = animal(P, i, t)
    if f["kind"] == "deer":
        fx, fy, fkw, fvis, _ = fawn(P, t)
        if fvis:
            draw_one(pg, "deer", fx, fy, f["s"] * 0.7, t, fkw, sh)
    if vis and -600 < x - sh < W + 600:
        wash = kw.get("wash", 0.0) if f["kind"] == "raccoon" else 0.0
        dk = 0.92 * (1 - kw["lit"]) if "lit" in kw and f["kind"] == "raccoon" else 0.0   # in the shadow with it
        face = kw.get("face", 1)
        sq = kw.get("squash", 1.0)
        draw_one(pg, f["kind"], x, y, f["s"], t, dict(kw), sh)
        lift = ease(t, T["leave"] - 1.4, T["leave"] - 0.5) if f["kind"] == "raccoon" else 0.0
        if wash > 0.1 or lift > 0.0:                               # the food it's washing, rubbed between its paws;
            s_ = f["s"]                                            # then up to its mouth, and away with it (advisor
            rf, rn, pv = raccoon_wash(t, wash)                    # FK0023 r2: it vanished from its paw); between
            px_, py_ = x - sh + face * (0.5 + 0.5 * (rf + rn)) * s_, y - (pv + 0.03) * s_   # the paws as they roll it
            mx_, my_ = x - sh + face * sq * 0.6 * s_, y - 0.47 * s_
            fx, fy = lerp(px_, mx_, lift), lerp(py_, my_, lift)
            # (advisor FK0023 r3: a 15 px red dot, nobody could tell what it was) a little apple, stem and leaf
            r_ = 0.1 * s_ * (1 - 0.25 * lift)
            pg.shape(oval(fx, fy, r_, r_ * 0.92), _dim((196, 58, 48), dk), 0.12)
            spin = math.sin(t * 5.0) * wash * (1 - lift)          # its shine rolls round as the paws turn it
            pg.flat(oval(fx - 0.35 * r_ + 0.4 * r_ * spin, fy - 0.35 * r_, 0.28 * r_ * (1 - 0.4 * abs(spin)), 0.2 * r_),
                    _dim((236, 140, 120), dk), 0.8)
            pg.stroke(skia.Path().moveTo(fx, fy - 0.85 * r_).lineTo(fx + 0.12 * r_, fy - 1.3 * r_),
                      _dim((92, 64, 44), dk), 0.16 * r_)
            pg.flat(oval(fx + 0.42 * r_, fy - 1.2 * r_, 0.34 * r_, 0.16 * r_), _dim((110, 160, 80), dk))


# ----------------------------------------------------------------------------------------------- arms and shoulders

WR = 46.0 * K
SPRINGS_ARM = 47.0 * K
WHEELS_R = (WHEELS_UPPER + WHEELS_FORE) * K
TWIGS_R = (TWIGS_UPPER + TWIGS_FORE) * K
REST_A = math.radians(12.0)


def wheels_shoulder(x, y, sx, t):
    return x + sx * 100 * K, y - 210 * K + 3 * math.sin(t * 2.2) * K + 10 * K


def twigs_shoulder(x, y, sx, t):
    sway = 4 * math.sin(t * 1.1) * K
    return x + sway + sx * 82 * K, y - 350 * K + sway * 0.3 + 10 * K


def handle(P, t):
    """The cart's push handle (world): where Wheels' right pincer holds it."""
    return P.cart_x(t) - CART_HW - 8.0, GB - 150.0


def wheels_left(P, x, y, t):
    sh = wheels_shoulder(x, y, -1, t)
    sw = -roll_swing(P.paths["wheels"], t, WR)
    a = REST_A + math.radians(6.0) * sw
    R = WHEELS_R * 0.9
    return sh[0] - math.sin(a) * R, sh[1] + math.cos(a) * R


def twigs_point(P, t, x, y):
    """Twigs' right hand pointing up at the owl (while it's his find)."""
    i, T = P.find_at(t)
    if FINDS[i]["kind"] != "owl":
        return None, 0.0
    u = ease(t, T["point"][0], T["point"][0] + 0.9) * (1 - ease(t, T["point"][1] - 0.9, T["point"][1]))
    if u <= 0:
        return None, 0.0
    sh = twigs_shoulder(x, y, 1, t)
    rest = (sh[0] + math.sin(0.16) * TWIGS_R * 0.93, sh[1] + math.cos(0.16) * TWIGS_R * 0.93)
    dx, dy = NW.OWL_X - sh[0], NW.OWL_Y - 40 - sh[1]
    d = math.hypot(dx, dy)
    up = (sh[0] + dx / d * TWIGS_R * 0.92, sh[1] + dy / d * TWIGS_R * 0.92)
    from .harvest_flat import arc
    return arc(sh, rest, up, u, 1, ext=TWIGS_R * 0.99), u           # round the shoulder (no elbow flip)


# ----------------------------------------------------------------------------------------------- voices

VOICE_DUR_S = 0.6


def voices(P):
    """The Keepers' little noises at their story beats, each moved to the nearest quiet moment (never over her)."""
    lines = [(t0, t0 + _dur(tx)) for t0, tx in P.narration()]
    out = []

    def free(tv):
        return not any(a - 0.7 <= tv <= b + 0.7 for a, b in lines) and all(abs(tv - o[0]) >= 1.0 for o in out) and \
            not any(abs(tv - c) < 1.6 for c in P.cuts)
    for tv, kd, mood, pic in sorted(P.voice_events, key=lambda e: e[0]):
        for d in [0.0] + [s_ * 0.3 * n for n in range(1, 11) for s_ in (1, -1)]:
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

def watching(P, t):
    """0..1: everyone turned a little towards the animal (it's on their right), while it's there."""
    i, T = P.find_at(t)
    return ease(t, T["reveal"], T["reveal"] + 1.2) * (1 - ease(t, T["gone"] - 1.0, T["gone"]))


def keeper(kd, t):
    """(world x, screen y of its feet, monster attrs) of Keeper kd at time t."""
    x, y, a = _keeper(kd, t)
    P = plan()
    lt = P.turns[kd](t)
    a["legs_turn"] = lt
    look = 0.4 * watching(P, t) if kd != "lantern" else 0.25 * watching(P, t)
    a["turn"] = lt if abs(lt) > 0.05 else look * (1 - abs(lt) / 0.05)
    m, lk, hop = talking(P, kd, t)
    if m > 0 or lk > 0:
        a = dict(a, talk=m, attend=max(a.get("attend", 0.0), lk), turn=a["turn"] * (1 - lk))
        if kd in ("wheels", "springs", "lantern") and not a.get("_fixed"):
            y -= hop
    a.pop("_fixed", None)
    return x, y, a


def _keeper(kd, t):
    P = plan()
    sh = P.shift(t)
    if kd in ("teeth", "digger", "tentacles"):
        g = P.gaits[kd]
        x = g.body_x(t)
        a = dict(feet=[(fx - sh, fy) for fx, fy in g.feet(t)], attend=0.25)
        if kd == "tentacles":
            a.update(float=0.2, **hans_mood("happy"))
            return x, GB + g.bob(t), a
        a["arm_swing"] = arm_swing(g, t)
        if kd == "teeth":
            a.update(hands=True, saws=False, blades=0.0, blades_l=0.0, knee_fwd=True, clamp_reach=True)
            hd, u = twigs_point(P, t, x, GB)
            if hd is not None:
                a.update(arm_to={1: (hd[0] - sh, hd[1])}, arm_swing=a["arm_swing"] * (1 - u))
        return x, GB, a
    if kd == "springs":
        x, yr, sq = P.hopper.state(t)
        for a0, a1, hgt in P.springs_hops:                          # a big bounce up to see into the tree
            u = _seg(t, a0 - 0.3, a0)
            if 0 < u < 1:
                sq = max(sq, 0.5 * math.sin(math.pi * u))
            if a0 <= t < a1:
                e = (t - a0) / (a1 - a0)
                yr -= hgt * math.sin(math.pi * e) ** 2            # an eased push off and landing
                sq = -0.25 * math.sin(math.pi * e)
            u = _seg(t, a1, a1 + 0.3)
            if 0 < u < 1:
                sq = max(sq, 0.45 * math.sin(math.pi * u))
        a = dict(spring=sq, attend=0.25, arm_swing=0.0)
        if yr != GB:
            a["_fixed"] = True
        return x, yr, a
    if kd == "wheels":
        x = P.paths[kd](t)
        a = dict(wheel_rot=x / WR, attend=0.25, arm_swing=0.0, clamp_reach=True, grip=0.6)
        hx, hy = handle(P, t)
        lx, ly = wheels_left(P, x, GB, t)
        a["arm_to"] = {1: (hx - sh, hy), -1: (lx - sh, ly)}
        return x, GB, a
    x = P.glo_x(t)
    return x, P.glo_y(t), dict(attend=0.25, lamp=P.lamp(t))


def hans_targets(P, t):
    out = []
    for slot, jobs in P.hans.items():
        for t0, t1, fn, (a, b, c, d) in jobs:
            if t0 <= t < t1:
                if t < b:
                    g, tg = ease(t, a, b), fn(b)
                elif t < c:
                    g, tg = 1.0, fn(t)
                else:
                    g, tg = 1.0 - ease(t, c, d), fn(c)
                out.append((slot, tg, g, None))
    return out


def hans_extra(t, sh):
    P = plan()

    def draw(cv, m):
        m.work = []
        for slot, (tx, ty), grip, leg in hans_targets(P, t):
            if grip <= 0.001:
                continue
            root_rest = (m.x + slot * 40 * K, m.y - 305 * K + 150 * K)
            gx, gy = lerp2(root_rest, (tx - sh, ty), grip)
            root, L = m.work_tentacle(cv, gx, gy, t, slot=slot, grip=max(grip, 0.3))
            m.work.append((slot, root, (gx, gy), L))
    return draw


def figure(pg, kd, x, y, t, sh, a, extra=None):
    return il.figure(pg, kd, x - sh, y, K, 6, t=t, extra=extra, **a)


# ----------------------------------------------------------------------------------------------- the cart + the book

WOOD, WOOD_D = NW.HW.WOOD, NW.HW.WOOD_D
COVER, COVER_D = (92, 122, 70), (74, 98, 56)
PAPER, PAPER_D = (246, 236, 214), (216, 200, 170)
INK = (70, 52, 44)
TICK = (79, 154, 79)
CARD = (246, 238, 220)


def draw_cart(pg, P, t, sh):
    """Wheels' reading cart: a little wooden bed on two wheels (they roll as it goes), a handle at the back, a post up
    to a slanted lectern with the Keeper Field Guide on it."""
    x = P.cart_x(t) - sh
    if not (-300 < x < W + 300):
        return
    r = 30.0
    rot = P.cart_x(t) / r
    bed = GB - 66.0
    pg.shape(rrect(x - CART_HW, bed - 22, x + CART_HW, bed + 8, 6), WOOD, 0.1)
    pg.flat(rrect(x - CART_HW + 6, bed - 18, x + CART_HW - 6, bed - 12, 3), tone(WOOD, 0.1), 0.8)
    hx, hy = handle(P, t)
    pg.shape(rrect(x - CART_HW - 4, hy - 4, x - CART_HW + 10, bed, 4), WOOD_D, 0.08)       # the handle's upright
    pg.shape(oval(hx - sh, hy, 9, 9), WOOD_D, 0.08)                                       # its knob (he holds it)
    pg.shape(rrect(x - 7, BOOK_Y + BOOK_H / 2 - 4, x + 7, bed - 18, 4), WOOD_D, 0.08)      # the lectern's post
    pg.shape(rrect(x - BOOK_W - 14, BOOK_Y + BOOK_H / 2 - 6, x + BOOK_W + 14, BOOK_Y + BOOK_H / 2 + 8, 4), WOOD, 0.08)
    for wx in (x - CART_HW + 34, x + CART_HW - 34):
        pg.shape(oval(wx, GB - r, r, r), (70, 62, 58), 0.1)
        pg.flat(oval(wx, GB - r, r * 0.55, r * 0.55), (150, 140, 130))
        for q in range(4):
            a = rot + q * math.pi / 2
            pg.stroke(skia.Path().moveTo(wx, GB - r).lineTo(wx + math.cos(a) * r * 0.5, GB - r + math.sin(a) * r * 0.5),
                      (96, 88, 82), 3.0)
        pg.flat(oval(wx, GB - r, 6, 6), WOOD_D)
    draw_book(pg, P, t, x)


def book_state(P, t):
    """(left page, right page, turning (from, to, u) or None)."""
    page = -1
    for ft, a, b in P.pages:
        if t < ft:
            return page, None
        if t < ft + 0.8:
            return a, (a, b, (t - ft) / 0.8)
        page = b
    return page, None


def draw_book(pg, P, t, x):
    y0, y1 = BOOK_Y - BOOK_H / 2, BOOK_Y + BOOK_H / 2
    page, turn = book_state(P, t)
    if page == -1 and turn is None:                                    # closed: the green cover, its title
        pg.shape(rrect(x - BOOK_W * 0.55, y0 - 4, x + BOOK_W * 0.55, y1 + 4, 6), COVER, 0.1)
        _text(pg, "FIELD", x, BOOK_Y - 4, 22, col=PAPER, center=True)
        _text(pg, "GUIDE", x, BOOK_Y + 22, 22, col=PAPER, center=True)
        return
    pg.shape(rrect(x - BOOK_W - 8, y0 - 6, x + BOOK_W + 8, y1 + 8, 6), COVER_D, 0.1)
    cover_turn = turn is not None and turn[0] == -1
    left = page if turn is None else turn[0]
    right = page if turn is None else turn[1]
    for side, p in ((-1, left), (1, right)):
        if side < 0 and p == -1:
            continue
        xa, xb = (x - BOOK_W, x - 2) if side < 0 else (x + 2, x + BOOK_W)
        pg.flat(rrect(xa, y0, xb, y1, 3), PAPER)
        page_art(pg, P, t, p, side, xa, xb, y0, y1)
    pg.stroke(skia.Path().moveTo(x, y0).lineTo(x, y1), PAPER_D, 2.0)
    if turn is not None:                                               # the turning page: over from right to left
        a, b, u = turn
        w = BOOK_W * math.cos(math.pi * u)
        lift = 4 * math.sin(math.pi * u)                               # (advisor FK0023 r3: 16 rose out of the frame)
        tip = x + w
        pts = [(x, y0), (tip, y0 - lift), (tip, y1 - lift * 0.4), (x, y1)]
        col = COVER if cover_turn else PAPER
        shade = 0.84 + 0.16 * abs(math.cos(math.pi * u))
        pg.flat(_poly(pts), tuple(v * shade for v in col))
        if u > 0.5 and not cover_turn:                                 # its back: the new left page coming down
            lo, hi = min(x, tip), max(x, tip)
            c = pg.c
            c.save()
            c.clipPath(_poly([(lo, y0 - lift), (hi, y0 - lift), (hi, y1), (lo, y1)]), doAntiAlias=True)
            c.saveLayer(None, skia.Paint(Alphaf=smoothstep((u - 0.5) / 0.5)))
            page_art(pg, P, t, b, -1, x - BOOK_W, x - 2, y0, y1)
            c.restore()
            c.restore()


def _poly(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def picture(pg, kind, rect, t=1.0):
    """An animal's picture fitted inside rect (x0, y0, x1, y1) and clipped to it (nothing spills off a page)."""
    x0, y0, x1, y1 = rect
    if kind == "squirrel":                                             # gliding, from above (as it was seen)
        s = 0.95 * min((x1 - x0) / 0.9, (y1 - y0) / 0.7)
        c = pg.c
        c.save()
        c.clipRect(skia.Rect(x0, y0, x1, y1), doAntiAlias=True)
        cx, cy = (x0 + x1) / 2 + 0.0925 * s, (y0 + y1) / 2
        il.creature(pg, lambda cv: glider(cv, cx, cy, s, t, spread=1.0, phi=math.pi / 2), cx, cy)
        c.restore()
        return
    s = PIC_S[kind] * min((x1 - x0) / PIC_W[kind], (y1 - y0) / PIC_H[kind])
    kw = {"squirrel": dict(glide=1.0), "opossum": dict(babies=3), "deer": dict()}.get(kind, {})
    cx = (x0 + x1) / 2 + PIC_DX[kind] * s
    by = y1 - (0.5 * (y1 - y0) - 0.5 * PIC_H[kind] * s / PIC_S[kind] * PIC_S[kind]) if kind == "squirrel" else y1 - 2
    c = pg.c
    c.save()
    c.clipRect(skia.Rect(x0, y0, x1, y1), doAntiAlias=True)
    il.creature(pg, lambda cv: draw_animal(cv, kind, cx, by, s, t, **kw), cx, by)
    c.restore()


# an animal's drawn size per unit s (height, width) and where its middle sits (measured, ep11.py --measure)
PIC_H = {"raccoon": 0.9, "owl": 1.2, "opossum": 0.7, "squirrel": 0.22, "fox": 1.32, "deer": 1.17}
PIC_W = {"raccoon": 1.83, "owl": 0.61, "opossum": 1.88, "squirrel": 1.34, "fox": 1.48, "deer": 1.19}
PIC_DX = {"raccoon": 0.28, "owl": 0.0, "opossum": 0.1, "squirrel": 0.12, "fox": 0.1, "deer": -0.02}
PIC_S = {k: 0.96 for k in PIC_H}


def page_art(pg, P, t, p, side, xa, xb, y0, y1):
    if p == 0:                                                         # the checklist
        if side < 0:
            _text(pg, "WHO'S AWAKE", (xa + xb) / 2, y0 + 30, 16, col=INK, center=True)
            _text(pg, "TONIGHT?", (xa + xb) / 2, y0 + 50, 16, col=INK, center=True)
            mx, my = (xa + xb) / 2, y0 + 74
            pg.flat(oval(mx, my, 12, 12), (226, 214, 170))
            pg.flat(oval(mx + 5, my - 3, 10, 10), PAPER)
            return
        n = P.found(t)
        for q in range(6):
            cx = xa + 26 + (q % 3) * 49
            cy = y0 + 25 + (q // 3) * 46
            rect = (cx - 19, cy - 19, cx + 19, cy + 19)
            pg.stroke(rrect(*rect, 3), tone(INK, 0.3), 1.6)
            if q < n:
                picture(pg, FINDS[q]["kind"], (rect[0] + 2, rect[1] + 2, rect[2] - 2, rect[3] - 2), t)
            else:
                _text(pg, "?", cx, cy + 8, 22, col=tone(INK, 0.4), center=True)
        return
    if p >= 7:                                                         # other pages of the guide (lines of writing)
        if side < 0:
            pg.flat(oval((xa + xb) / 2, (y0 + y1) / 2, 40, 26), PAPER_D)
        else:
            for q in range(6):
                pg.stroke(skia.Path().moveTo(xa + 14, y0 + 20 + q * 12).lineTo(xb - 14 - 18 * (q % 2), y0 + 20 + q * 12),
                          PAPER_D, 2.0)
        return
    kind = FINDS[p - 1]["kind"]
    if side < 0:
        picture(pg, kind, (xa + 6, y0 + 6, xb - 6, y1 - 6), t)
        return
    nm = ANIMALS[kind]["name"].upper()
    _text(pg, nm, (xa + xb) / 2, y0 + 22, 13 if len(nm) > 12 else 15, col=INK, center=True)
    for q in range(4):
        pg.stroke(skia.Path().moveTo(xa + 14, y0 + 38 + q * 11).lineTo(xb - 40 - 14 * (q % 2), y0 + 38 + q * 11),
                  PAPER_D, 2.0)
    bx, by = xb - 22, y1 - 20
    pg.stroke(rrect(bx - 11, by - 11, bx + 11, by + 11, 2), tone(INK, 0.3), 1.6)
    tk = ease(t, P.F[p - 1]["tick"], P.F[p - 1]["tick"] + 0.5)
    if tk > 0:
        p1, p2, p3 = (bx - 8, by), (bx - 2, by + 7), (bx + 11, by - 11)
        path = skia.Path().moveTo(*p1)
        if tk < 0.4:
            path.lineTo(*lerp2(p1, p2, tk / 0.4))
        else:
            path.lineTo(*p2).lineTo(*lerp2(p2, p3, (tk - 0.4) / 0.6))
        pg.stroke(path, TICK, 4.0)


# ----------------------------------------------------------------------------------------------- on screen

_FONT = {}


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


def _panel(pg, x, y, w, h, a, r=18, col=(252, 246, 234)):
    pg.flat(rrect(x + 4, y + 6, x + w + 4, y + h + 6, r), (40, 28, 24), 0.2 * a, blur=8)
    pg.flat(rrect(x, y, x + w, y + h, r), col, 0.95 * a)


TOP = {"wheels": 236, "tentacles": 309, "teeth": 380, "springs": 206, "lantern": 246, "digger": 202}   # drawn
                                    # tops above the feet (Glo: above his y); Twigs: his head, not his antennae


def name_tags(pg, t, a, avoid=()):
    """Each name just over its own Keeper's head, nudged aside (or beside the head) if it would cover another
    Keeper, another name or `avoid` (advisor r1: the 'Hans' tag sat on Glo, 'Glo' floated on a treetop)."""
    from .causecheck import body_box
    P = plan()
    sh = P.shift(t)
    bodies, spots = {}, []
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
        if 60 < cx < W - 60:
            _panel(pg, cx - tw / 2, cy - 34, tw, 46, a)
            _text(pg, NAMES[kd], cx, cy, 30, a=a, center=True)


def card(pg, a, title, lines, kind=None, side=0):
    """The name card (screen space: it never moves), the animal's picture on its left. At the top of the frame, in
    the sky: side 0 in the middle, -1 on the left (under the count), +1 on the right (advisor r1: at the bottom it
    covered the fox, the opossum's log and the whole cast)."""
    if a <= 0.01:
        return
    w, h = (1240, 210) if side == 0 else (930, 190)
    x0 = (W - w) / 2 if side == 0 else (40 if side < 0 else W - 40 - w)
    y0 = 40 if side >= 0 else 128
    c = pg.c
    c.save()                                                       # it grows into place and is solid almost at once
    k = 0.92 + 0.08 * a                                            # (advisor FK0023 r2: half see-through as it faded,
    c.translate(x0 + w / 2, y0 + h / 2)                            # the moon showed through its words)
    c.scale(k, k)
    c.translate(-(x0 + w / 2), -(y0 + h / 2))
    c.saveLayer(None, skia.Paint(Alphaf=min(1.0, a * 3.0)))
    pg.flat(rrect(x0 + 6, y0 + 10, x0 + w + 6, y0 + h + 10, 24), (40, 28, 24), 0.25, blur=10)
    pg.flat(rrect(x0, y0, x0 + w, y0 + h, 24), (150, 108, 72))
    pg.flat(rrect(x0 + 10, y0 + 10, x0 + w - 10, y0 + h - 10, 16), CARD)
    tx0 = x0 + (230 if kind else 60)
    if kind:
        picture(pg, kind, (x0 + 26, y0 + 22, x0 + 216, y0 + h - 22))
    cx = (tx0 + x0 + w - 40) / 2
    big = 60 if side == 0 else 52
    _text(pg, title, cx, y0 + h / 2 - 22, big if len(title) > 16 else big + 4, col=INK, center=True)
    for q, ln in enumerate(lines):
        _text(pg, ln, cx, y0 + h / 2 + 30 + q * 36, 30, col=tone(INK, 0.22), weight="Medium", center=True)
    c.restore()
    c.restore()


def overlays(pg, t):
    P = plan()
    a = ease(t, P.tags[0], P.tags[0] + 1.0) * (1 - ease(t, P.tags[1], P.tags[1] + 1.0))
    if a > 0:
        name_tags(pg, t, a)
    ta = ease(t, P.title[0], P.title[0] + 0.7) * (1 - ease(t, P.title[1], P.title[1] + 0.7))
    card(pg, ta, "WHO'S AWAKE TONIGHT?", ["Can the Keepers find six", "night-time neighbors?"])
    i, T = P.find_at(t)
    ca = ease(t, T["card"][0], T["card"][0] + 0.7) * (1 - ease(t, T["card"][1], T["card"][1] + 0.7))
    kind = FINDS[i]["kind"]
    ax = animal(P, i, t)[0] - P.shift(t)                           # the card on the far side from the animal
    card(pg, ca, ANIMALS[kind]["name"], ANIMALS[kind]["line"], kind, side=-1 if ax > W / 2 else 1)
    fa = ease(t, P.fin_card[0], P.fin_card[0] + 0.7) * (1 - ease(t, P.fin_card[1], P.fin_card[1] + 0.7))
    card(pg, fa, "All six found!", ["Six night-time neighbors,", "all found. Goodnight, forest!"], side=1)
    na = ease(t, P.title[1] - 0.4, P.title[1] + 0.4) * (1 - ease(t, P.sign[0] - 1.0, P.sign[0]))
    if na > 0:                                                         # the count, top left
        n = P.found(t)
        hi = max((bump(t, Tq["tick"], 0.8) for Tq in P.F), default=0.0)
        _panel(pg, 40, 36, 470, 72, na, col=(150, 108, 72))
        col = tuple(v * (1 - 0.3 * hi) + w_ * 0.3 * hi for v, w_ in zip((252, 246, 234), (255, 214, 110)))
        _text(pg, f"NEIGHBORS FOUND  {n} / 6", 275, 84, 32, col=col, a=na, center=True)
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
    _text(pg, END_TEXT, W / 2, y0 + 104, 58, col=(252, 246, 234), a=sa, center=True)
    _text(pg, "Tell us in the comments", W / 2, y0 + 162, 34, col=(250, 232, 200), a=sa, weight="Medium", center=True)
    name_tags(pg, t, sa, avoid=[(x0 - 10, y0 - 10, x0 + bw + 10, y0 + bh + 16)])


def glo_lights(pg, P, t, sh):
    """Glo's lantern glows softly in the dark (a warm pool on the path), and flares up to turn the pages."""
    gx, gy = P.glo_x(t), P.glo_y(t)
    lx, ly = gx - sh, gy - 260 * K + glo_bob(t) + 82 * K
    lamp = P.lamp(t)
    pg.glow(lx, ly, 150, "#ffe2a0", 0.22 * min(1.0, lamp))
    pg.flat(oval(lx, GB + 6, 160, 26), "#ffe2a0", 0.07 * min(1.0, lamp), blur=18)
    i, T = P.find_at(t)
    if FINDS[i]["kind"] in ("owl", "raccoon"):                     # his light reaches up into the oak and finds the
        r0, fo = T["reveal"], FINDS[i]                             # owl (advisor FK0023 r2: it lit up by itself);
        b = ease(t, r0 - 1.0, r0 - 0.5) * (1 - ease(t, r0 + 1.6, r0 + 2.4))   # and over to the pond for the raccoon
        if b > 0.01:
            if fo["kind"] == "owl":
                ox, oy = fo["x"] - sh, NW.OWL_Y - 0.6 * fo["s"]
            else:
                ox, oy = fo["x"] - sh - 0.2 * fo["s"], NW.FLOOR - 0.45 * fo["s"]
            pg.glow(lx, ly, 120, "#ffe7a8", 0.45 * b)
            reach = ease(t, r0 - 1.0, r0 - 0.4)                    # a soft beam, up from the lantern to the branch
            if fo["kind"] == "raccoon":                            # to the pond: a stream of sparkles in a high arc
                for q in range(36):                                # over everyone's heads (never across a face)
                    u = ((t * 0.9 + q / 36) % 1.0) * reach
                    px = lerp(lx, ox, u)
                    py = lerp(ly - 10, oy, u) - RACCOON_ARC * math.sin(math.pi * u)
                    pg.glow(px, py, 14, "#ffe7a8", 0.25 * b)
                    pg.flat(oval(px, py, 5.0, 5.0), "#fff2c8", b * (0.6 + 0.4 * math.sin(t * 11 + q)))
                pg.glow(ox, oy, 0.9 * fo["s"], "#ffe7a8", 0.3 * b * ease(t, r0 - 0.6, r0))
                return_raccoon = True
            else:
                return_raccoon = False
        if b > 0.01 and not return_raccoon:
            ex, ey = lerp(lx, ox, reach), lerp(ly - 10, oy, reach)
            dx, dy = ex - lx, ey - ly
            n = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / n, dx / n
            w0, w1 = 16.0, 16.0 + 0.45 * fo["s"] * reach
            beam = skia.Path()
            beam.moveTo(lx + nx * w0, ly + ny * w0)
            beam.lineTo(ex + nx * w1, ey + ny * w1)
            beam.lineTo(ex - nx * w1, ey - ny * w1)
            beam.lineTo(lx - nx * w0, ly - ny * w0)
            beam.close()
            pg.flat(beam, "#ffe7a8", 0.16 * b, blur=14)
            for q in range(24):
                u = ((t * 0.9 + q / 24) % 1.0) * reach
                px = lerp(lx, ox, u) + 18 * math.sin(7.0 * u + q * 2.1) * (1 - u)
                py = lerp(ly - 10, oy, u)
                pg.flat(oval(px, py, 4.6, 4.6), "#fff2c8", b * (0.6 + 0.4 * math.sin(t * 11 + q)))
            pg.glow(ox, oy, 0.9 * fo["s"], "#ffe7a8", 0.3 * b * ease(t, r0 - 0.6, r0))
    f = glo_flare(P, t)
    if f > 0.01:
        pg.glow(lx, ly, 120, "#ffe7a8", 0.45 * f)
        bx, by = P.cart_x(t) - sh, BOOK_Y
        # (advisor FK0023 r3: 8 tiny sparkles didn't carry ~900 px, the book seemed to turn itself) a soft beam
        # reaches from the lantern to the book first, with a stream of sparkles along it, like the owl's
        # (advisor FK0023 r6: the straight beam ran through Twigs' eye and Hans' head, who stand between him and
        # the book) a stream of sparkles in a high arc over everyone's heads, down onto the book, like the raccoon's
        reach = glo_reach(P, t)
        for q in range(36):
            u = ((t * 0.9 + q / 36) % 1.0) * reach
            px = lerp(lx, bx, u)
            py = lerp(ly - 10, by, u) - BOOK_ARC * math.sin(math.pi * u)
            pg.glow(px, py, 14, "#ffe7a8", 0.25 * f)
            pg.flat(oval(px, py, 5.0, 5.0), "#fff2c8", f * (0.6 + 0.4 * math.sin(t * 11 + q)))
        pg.glow(bx, by, 120, "#ffe7a8", 0.4 * f * reach)


# ----------------------------------------------------------------------------------------------- the frame

def frame(pg, valley, t):
    P = plan()
    sh = P.shift(t)
    i, T = P.find_at(t)
    NW.sky(pg, t, sh)
    valley.draw(pg, sh, only={"far", "far2", "far_trees", "mid", "meadow"})
    if i == 0:
        rip = None
        _, _, kw, vis, what = animal(P, 0, t)
        if vis and kw.get("wash", 0) > 0.05:
            # (advisor FK0023 r8: centred off the water at its tip, they were clipped away) in the water by its paws
            rip = (NW.POND[1] - 40.0, (NW.POND_NEAR + NW.POND_FAR) / 2 + 2.0, kw["wash"], 1.0)
        NW.draw_pond(pg, t, sh, rip)
        NW.draw_reeds(pg, t, sh)                                   # (behind the raccoon: they hid its face)
    draw_animals(pg, P, t, sh)
    for x in NW.HIDE.values():
        NW.draw_hide_bush(pg, x, sh)
    if i == 3:
        NW.draw_crowns(pg, sh)
    gx, gy, ga = keeper("lantern", t)
    if -400 < gx - sh < W + 400:
        il.figure(pg, "lantern", gx - sh, gy, K, 6, t=t, shadow=False, **ga)
    draw_cart(pg, P, t, sh)
    for kd in WALKERS:
        x, y, a = keeper(kd, t)
        if -500 < x - sh < W + 500:
            figure(pg, kd, x, y, t, sh, a, extra=hans_extra(t, sh) if kd == "tentacles" else None)
    valley.draw(pg, sh, only={"fg"})
    NW.apply_light(pg)
    z = NW.zone_of(sh)
    amt = 0.35 + 0.65 * ease(t, P.fire_up, P.fire_up + 6.0)
    NW.fireflies(pg, t, sh, amt, NW.Z(z, -200.0), NW.Z(z, ZONE_W), seed=77 + z)
    glo_lights(pg, P, t, sh)
    if not THUMB:                                                  # (a thumbnail is the scene alone: no cards)
        bubbles(pg, t)
        overlays(pg, t)
    u = max([1 - abs(t - c) / 1.1 for c in P.cuts] + [1 - t / 1.2, ease(t, P.end - 1.8, P.end), 0.0])
    if u > 0:                                                          # a soft dip into the dark between clearings
        pg.flat(skia.Path().addRect(skia.Rect(0, 0, W, H)), (20, 24, 40), smoothstep(min(1.0, u)))
    return {}


ZONE_W = NW.ZONE + 200.0
THUMB = False                       # set by the thumbnail maker


def bubbles(pg, t):
    """The Keepers' little speech bubbles (a heart for 'aww', a sparkle for 'ooh')."""
    from .chatter import MOODS, _back, bubble
    P = plan()
    sh = P.shift(t)
    for tv, kd, mood, pic in P.voices:
        u = t - tv
        pic = pic or MOODS[mood][2]
        if pic is None or pic in ("!", "?") or not (0 <= u < 2.2) or t >= P.sign[0] - 4.0:
            continue
        if any(tv - 0.2 < c < tv + 2.4 for c in P.cuts):
            continue
        x, y, _ = keeper(kd, t)
        top = y - TOP[kd] * K / 0.72
        s = _back(min(u / 0.25, 1.0)) * (1 - smoothstep((u - 1.9) / 0.3))
        if s < 0.3:                                                # (a tiny bubble was a stray stalk in the sky)
            continue
        bx, by = x - sh + 70 * K + 26, top - 52
        gx = P.cart_x(t) - sh                                      # never over the field guide
        if abs(bx - gx) < BOOK_W + 60 and abs(by - BOOK_Y) < BOOK_H + 50:
            bx = x - sh - 70 * K - 26
        il.creature(pg, lambda cv, bx=bx, by=by, s=s, pic=pic: bubble(cv, bx, by, 50.0 * s, pic, (214, 196, 176),
                                                                     1.0, (bx - 62, by + 92)), bx, by)


# ----------------------------------------------------------------------------------------------- the soundtrack

def soundtrack(path):
    """The music box (the episode's own variant, slow and quiet for the night), the Keepers' voices, soft sounds for
    what the animals do, crickets now and then, and the narrator over it all (the music eases down only while she
    speaks; owner after FK0008's first render)."""
    from engine.audio import EventTrack
    from . import music
    from .chatter import MOODS, VOICE, VOWEL
    from .narrator import soundtrack as narr_mix, take
    P = plan()
    track = EventTrack(11)
    chords = music.compose(track, 0.3, P.end - 1.0, gain=0.9, variant="whosawake")
    pan = lambda x: max(-0.6, min(0.6, (x / W) * 1.2 - 0.6))       # noqa: E731

    def px(xw, t):
        return pan(xw - P.shift(t))
    for tv, kd, mood, _ in P.voices:
        contour, st, _ = MOODS[mood]
        track.hit(tv, f"voice_{contour}@{int(round(VOWEL[kd] * 100))}", VOICE[kd] + st, 0.3,
                  px(keeper(kd, tv)[0], tv))
    for ft, a, b in P.pages:                                       # the pages turning, the ticks
        track.fx(ft, "rustle", 0.45, 0.12, px(P.cart_x(ft), ft))
    for T in P.F:
        track.hit(T["tick"], "warm_bell", 72, 0.12, px(P.cart_x(T["tick"]), T["tick"]))
        track.hit(T["tick"] + 0.22, "warm_bell", 79, 0.1, px(P.cart_x(T["tick"]), T["tick"]))
    for a, b in P.flares:
        track.hit(a + 0.5, "plink", 67, 0.05, 0.0)
    for j, (f, T) in enumerate(zip(FINDS, P.F)):
        x, kind = f["x"], f["kind"]
        if kind == "raccoon":                                      # soft water sounds while it washes
            for tq in [T["hint"] + 0.6 + q * 1.6 for q in range(5)] + [T["reveal"] + 3.6 + q * 1.4 for q in range(5)]:
                track.fx(tq, "bubble", 0.5, 0.05, px(x, tq))
        if kind == "owl":                                          # who-cooks-for-you, soft and low
            for base in (T["hint"] + 1.5, T["reveal"] + 2.0):
                for dt_, n in ((0.0, 62), (0.3, 62), (0.55, 64), (0.9, 60)):
                    track.hit(base + dt_, "sky_swell", n, 0.09, px(x, base))
        if kind == "opossum":
            track.fx(T["reveal"] + 0.4, "leaf_settle", 1.2, 0.07, px(x, T["reveal"]))
        if kind == "squirrel":
            land = T["reveal"] + 4.9
            track.hit(land, "wood_thud", 50, 0.06, px(NW.TREE_B, land))
            track.fx(T["leave"] + 0.5, "rustle", 1.5, 0.05, px(NW.TREE_B, T["leave"]))
        if kind in ("fox", "deer"):
            track.fx(T["leave"] + 1.2, "rustle", 2.0, 0.04, px(x, T["leave"]))
        if kind in ("raccoon", "opossum", "fox"):                  # through the bush as it goes
            track.fx(T["gone"] - 1.5, "leaf_settle", 1.0, 0.05, px(NW.HIDE[f["zone"]], T["gone"]))
    rs = np.random.default_rng(5)
    for t0 in np.arange(2.0, P.end - 3.0, 3.1):                    # crickets, far off, now and then
        if rs.random() < 0.55:
            for q in range(3):
                track.hit(t0 + 0.11 * q, "plink", 91 + int(rs.integers(0, 3)), 0.008, float(rs.uniform(-0.6, 0.6)))
    bed = {"type": "procedural", "name": "keepers_song", "gain": 0.9, "chords": chords,
           "reverb": {"decay": 3.8, "wet": 0.42, "tone": 2400}}

    class Shim:
        p = {"audio": {}}
        events_gain = 1.0
        reverb = None
    sc_ = Shim()
    sc_.bed = bed
    sc_.narration = [(t0, take(tx)) for t0, tx in P.narration()]
    wav, stats = narr_mix(sc_, track, P.end)
    import shutil
    shutil.move(wav, path)
    return path, stats, track
