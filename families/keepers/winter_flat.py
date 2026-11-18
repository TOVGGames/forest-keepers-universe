"""Forest Keepers episode 13, Getting Ready for Winter, in the flat picture-book look (owner approved the look on FK0014,
2026-11-04: "Yes, start ep 13"). The remake of FK0012 (NOT approved: docs/engines/forest_keepers_fk0012_audit.md):
the same approved storyboard (docs/engines/forest_keepers_winter_ready.md), every mistake in the audit fixed, every
frame through storycheck.

Stateless: every frame is a pure function of time t (s), so frames render in parallel (experiments/keepers_flat/
ep13.py). The world is winter_flat_world.py; the walking and digging kit is flat_motion.py.

    PLAN.beats, PLAN.end                    the timeline
    frame(pg, valley, t) -> metrics         draw one frame onto a flat.FlatPage
    checks(t, metrics) -> storycheck input  (things, limbs, layers, focus) for that frame
"""
import math

import numpy as np
import skia

from families.foundry.keepers.common import smoothstep
from families.foundry.products.monster import TURN_NARROW, Xform, acorn_nut

from . import illustrate as il
from . import storycheck as sc
from . import winter_flat_world as WF
from .flat_motion import (HANS_LEG, Hopper, TripodGait, biped, hans_mood, heading, smooth_path,  # noqa: F401
                          stance_drop, walk_path)
from .storybook import C, oval, rrect, tone
from .winter_animals import (BEAVER_STRIDE, bear, beaver, beaver_mouth, chickadee, chickadee_bill, chipmunk,
                             chipmunk_cheek, chipmunk_paws, per_s)

W, H, G, BACK = WF.W, WF.H, WF.G, WF.BACK
FPS = 60
STEP = 1.0 / FPS                            # a frame (the checks may step coarser: they set this)
K = 0.72                                    # px per Keeper unit (Hans 440 px tall)
ORDER = ["sprout", "teeth", "wheels", "digger", "springs", "tentacles", "lantern"]   # front (right) to back
V_WALK = 100.0                              # px/s: their pace on a walk between stops (owner 2026-11-05: the old
EASE = 1.0                                  #   58 px/s was too slow); they speed up / slow down over EASE s
GAP = 230.0
NAMES = {"sprout": "Sprout", "teeth": "Twigs", "wheels": "Wheels", "digger": "Digs", "springs": "Springs",
         "tentacles": "Hans", "lantern": "Glo"}


def _line(front):
    return {kd: front - i * GAP for i, kd in enumerate(ORDER)}


# where each Keeper stands at each stop (world x). The helper stands on the side the animal doesn't use; those ahead
# wait past its route, those behind short of it (docs: remake layout)
STOPS = {
    "start": _line(1440.0),
    "chip": _line(2250.0),
    "beaver": dict(sprout=5100.0, teeth=WF.WILLOW - 15 + 95, wheels=WF.WILLOW - 165 - 135, digger=2770.0,
                   springs=2540.0, tentacles=2310.0, lantern=2080.0),
    "ground": dict(sprout=6660.0, teeth=6430.0, wheels=6200.0, digger=5500.0, springs=5100.0, tentacles=4900.0,
                   lantern=4700.0),
    "bear": dict(sprout=8870.0, teeth=8640.0, wheels=8410.0, digger=8180.0, springs=7950.0,
                 tentacles=WF.DEN + 500.0, lantern=5950.0),
    "dee": dict(sprout=11100.0, teeth=10870.0, wheels=10640.0, digger=10410.0, springs=10180.0, tentacles=9950.0,
                lantern=WF.FEEDER - 150.0),
}

# ----------------------------------------------------------------------------------------------- narration

HOOK = ("The days are getting shorter, and the forest is getting ready for winter. How will each of our "
        "neighbours get ready? And at the very end, watch for the very first snowflakes.")
LINES = {
    "chickadee": ("The sun has gone, and the stars are out. One little neighbour is staying right here.",
                  "A chickadee. It stays all winter. It fluffs its feathers into a warm coat, and remembers where "
                  "it hid its seeds."),
    "bear": ("Shh. Someone big is looking for a cosy place to sleep.",
             "A black bear. It eats and eats all autumn, then sleeps the winter away in a cosy den."),
    "goose": ("Listen... honking, high up in the sky.",
              "Canada geese. Many fly south for the winter, in a V. Each bird rides the air lifted by the one "
              "ahead."),
    "groundhog": ("Digs knows this little door. Someone is getting sleepy.",
                  "A groundhog. It hibernates all winter in its burrow, its heart beating only a few times a "
                  "minute."),
    "beaver": ("Down at the pond, someone is collecting branches.",
               "A beaver. It pushes branches into the mud by its lodge, to eat under the ice all winter."),
    "chipmunk": ("Sprout has found a busy little neighbour, by the old stump.",
                 "An eastern chipmunk. It carries seeds home in its stretchy cheek pouches, and stores them "
                 "underground."),
}


FINALE = "Six neighbours, all ready for winter. And look... the very first snowflakes. Goodnight, forest."
SIGNOFF = "What should the Keepers do next? Tell us in the comments."
HOLD_END = 4.0                              # s of quiet after "Goodnight, forest" (owner 2026-11-05: 3-5 s more)


def _dur(text):
    from .narrator import take
    return take(text)["duration"]


# ----------------------------------------------------------------------------------------------- the chipmunk

# the animals are drawn bigger than "real" next to the Keepers (tree monsters have no real size) so the action fills
# the frame (owner rule); between themselves they keep their real size ratios ** 0.6 (FK0012 audit 17)
ANIMAL = 0.66 * 300.0 * K                    # the chipmunk sitting up: about two thirds of Digs
ACORN_R = 0.14 * ANIMAL / 2                  # an acorn ~2.8 cm against the chipmunk's ~20
SPROUT_L = 57.0 * K                          # Sprout's arm (monster.sprout_arm), shoulder to hand
SPROUT_V = 85.0                              # px/s, Sprout's pace on his little errands
CHIP_H = ANIMAL
GRAV = 1500.0                                # px/s^2


def _sprout_shoulder_r(x, t, dy=0.0):
    by = G - 150 * K + 2 * K * math.sin(t * 2.0) + dy
    return x + 78 * K, by + 4 * K


def _reach_x(hx, hy, t):
    """Where Sprout stands so its right hand is exactly at (hx, hy) (arm out and up to the right)."""
    sy = G - 150 * K + 4 * K                 # (the 2 px idle bob is small; the hand rides it while it holds)
    dy = hy - sy
    dx = math.sqrt(max(SPROUT_L ** 2 - dy * dy, 0.0))
    return hx - dx - 78 * K


class Chip:
    """Sprout picks three acorns off a young oak's low twig by the old stump and carries them to a pile at the path's
    edge, one at a time, always the same size; each drops from its hand, lands, and rolls against the others (1-3). Then the chipmunk comes up out
    of its burrow with empty paws, hops to the pile, leans down, takes each acorn in its paws and tucks it into a
    cheek; its pouches fill smoothly, one acorn at a time (4-5); it hops home and goes down its burrow."""

    def __init__(self, t0):
        self.t0 = t0
        self.on_stump = list(WF.ACORNS)                          # hanging under the young oak's low twig
        pile_y = G - 26 - ACORN_R * 1.1
        self.rest = [(WF.PILE, pile_y), (WF.PILE + 2 * ACORN_R + 1, pile_y),
                     (WF.PILE + ACORN_R + 0.5, pile_y - 1.75 * ACORN_R)]
        t = t0 + 0.5
        self.intro = t
        t += _dur(LINES["chipmunk"][0]) + 0.4
        self.trips = []
        x = STOPS["chip"]["sprout"]
        # one fluid errand, three times (owner 2026-11-05: smoother, more human): he turns and walks over, already
        # lifting his arm as he arrives; picks it; sets off again while his arm comes down; holds it out as he gets
        # to the pile and lets it go; and turns back for the next one without a pause
        for j in range(3):
            ax, ay = self.on_stump[2 - j]                         # the nearest one first
            px = _reach_x(ax, ay + 12 * K, t)                     # stand where the hand reaches it
            walk1 = (t, t + max(1.0, abs(px - x) / SPROUT_V + EASE))
            reach = (walk1[1] - 0.35, walk1[1] + 0.45)            # the arm goes up to it as he comes to a stop
            down = (reach[1] + 0.2, reach[1] + 0.8)               # grasped; brought down to carry
            rx, ry = self.rest[j]
            dx = rx + (0.0, 7.0, 2.0)[j]                          # the second lands beside and rolls in, the third
                                                                  # settles into the groove on top
            sx = dx - (78 * K + SPROUT_L * math.cos(-0.15))       # stand so the hand is above the drop point
            walk2 = (down[0] + 0.25, down[0] + 0.25 + abs(sx - px) / SPROUT_V + EASE)
            out = (walk2[1] - 0.35, walk2[1] + 0.35)              # the arm out level as he arrives; fingers open
            drop = out[1]
            self.trips.append(dict(px=px, sx=sx, walk1=walk1, reach=reach, down=down, walk2=walk2, out=out,
                                   drop=drop, dx=dx))
            x, t = sx, drop + 0.35
        self.sprout_done = t
        self.sprout_x_end = WF.ACORNS[0][0] - 20.0                # Sprout walks back to watch, by the oak
        self.home = self.trips[-1]["drop"] + 0.6 + abs(self.trips[-1]["sx"] - self.sprout_x_end) / SPROUT_V + EASE
        # the chipmunk
        self.up = (self.trips[-1]["drop"] + 3.0, self.trips[-1]["drop"] + 4.0)     # comes up out of its burrow
        self.fact = self.up[1] + 0.6
        self.stand = WF.PILE + 3 * ACORN_R + 38                  # where it sits by the pile (facing left)
        self.hop_to = (self.up[1] + 0.3, self.up[1] + 0.3 + 1.9)
        self.takes = []
        t = self.hop_to[1] + 0.3
        for j in (2, 1, 0):                                      # the top acorn first
            self.takes.append(dict(j=j, lean=(t, t + 0.5), lift=(t + 0.5, t + 1.0), tuck=(t + 1.25, t + 1.75),
                                   up=(t + 1.0, t + 1.4)))
            t += 2.3
        self.hop_back = (t + 0.3, t + 2.2)
        self.down = (self.hop_back[1] + 0.2, self.hop_back[1] + 1.2)
        self.card = self.down[1] + 0.3
        self.end = max(self.card + 5.5, self.fact + _dur(LINES["chipmunk"][1]) + 1.0)
        s = CHIP_H / per_s("chipmunk", seed=False)
        self.s = s
        # how deep it bows for each acorn (its paws down to it), and where it sits so they land right on them
        y0 = BACK + 14
        def paws(x, lean):
            f = Xform(None, ang=-lean, px=x, py=y0)
            return f._p(*chipmunk_paws(x, y0, s, -1))
        self.bow, need = {}, []
        for j, (rx, ry) in enumerate(self.rest):
            lo, hi = 0.0, 1.4
            for _ in range(40):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if paws(0.0, mid)[1] < ry else (lo, mid)
            self.bow[j] = (lo + hi) / 2
            need.append(rx - paws(0.0, self.bow[j])[0])
        self.stand = sum(need) / len(need)
        self.hop = Hopper(smooth_path([(self.hop_to[0], WF.BURROW1), (self.hop_to[1], self.stand),
                                       (self.hop_back[0], self.stand), (self.hop_back[1], WF.BURROW1)]),
                          BACK + 14, K, period=0.42, duty=0.45, height=26.0)
        self.flip = self.hop_back[0]                             # it spins round at the top of its first hop home
        tt = self.hop_back[0]
        while tt < self.hop_back[1] and self.hop.state(tt)[1] > BACK + 14 - 0.8 * 26.0 * K:
            tt += 1.0 / 240
        self.flip = tt

    # --- Sprout
    def sprout_keys(self):
        keys = []
        for tr in self.trips:
            keys += [(tr["walk1"][1], tr["px"]), (tr["walk2"][0], tr["px"]), (tr["walk2"][1], tr["sx"]),
                     (tr["drop"] + 0.35, tr["sx"])]
        keys.append((self.home, self.sprout_x_end))
        return keys

    def sprout_arm(self, t):
        """Sprout's right arm angle (rad) and its grip, at time t (None outside the beat)."""
        if not (self.trips[0]["walk1"][0] <= t <= self.home):
            return None, 0.0
        rest = math.atan2(34, 46)
        carry = 0.25
        for j, tr in enumerate(self.trips):
            ax, ay = self.on_stump[2 - j]
            shx, shy = _sprout_shoulder_r(tr["px"], t)
            up = math.atan2(ay + 12 * K - shy, ax - shx)
            if t < tr["reach"][0]:
                return rest, 0.0
            if t < tr["reach"][1]:
                u = smoothstep((t - tr["reach"][0]) / (tr["reach"][1] - tr["reach"][0]))
                return rest + (up - rest) * u, 0.0
            if t < tr["down"][0]:
                return up, smoothstep((t - tr["reach"][1]) / 0.25)
            if t < tr["down"][1]:
                u = smoothstep((t - tr["down"][0]) / (tr["down"][1] - tr["down"][0]))
                return up + (carry - up) * u, 1.0
            if t < tr["out"][0]:
                return carry, 1.0
            if t < tr["out"][1]:
                u = smoothstep((t - tr["out"][0]) / (tr["out"][1] - tr["out"][0]))
                return carry + (-0.15 - carry) * u, 1.0
            if t < tr["drop"] + 0.35:
                return -0.15, 1.0 - smoothstep((t - tr["drop"]) / 0.2)
            if j < 2 and t < self.trips[j + 1]["reach"][0]:       # on his way back, empty-handed: his arm
                u = smoothstep((t - tr["drop"] - 0.35) / 0.7)     # comes down to his side
                return -0.15 + (rest + 0.15) * u, 0.0
        u = smoothstep((t - self.trips[-1]["drop"] - 0.35) / 0.8)
        return -0.15 + (rest + 0.15) * u, 0.0

    # --- the acorns
    def acorn(self, j, t, sprout_x):
        """(x, y) of acorn j (0..2, in the order carried) at time t, or None once it is in the chipmunk's pouch."""
        tr = self.trips[j]
        if t < tr["reach"][1] + 0.12:
            return self.on_stump[2 - j]
        if t < tr["drop"]:                                       # in Sprout's hand (on its curled fingers)
            ang, _ = self.sprout_arm(t)
            shx, shy = _sprout_shoulder_r(sprout_x, t, _sink("sprout", t, sprout_x))
            return shx + math.cos(ang) * SPROUT_L, shy + math.sin(ang) * SPROUT_L - 12 * K
        ang, _ = self.sprout_arm(tr["drop"] - 1e-3)               # falls, lands, rolls into its place
        shx, shy = _sprout_shoulder_r(tr["sx"], tr["drop"], _sink("sprout", tr["drop"], tr["sx"]))
        x0, y0 = shx + math.cos(ang) * SPROUT_L, shy + math.sin(ang) * SPROUT_L - 12 * K
        rx, ry = self.rest[j]
        land_y = ry if j < 2 else ry
        tf = math.sqrt(max(2 * (land_y - y0) / GRAV, 0.0))
        tau = t - tr["drop"]
        take = [tk for tk in self.takes if tk["j"] == j][0]
        if t >= take["tuck"][1]:                                 # in its pouch now
            return None
        if t >= take["lean"][1]:
            return self._in_chipmunk(j, t, take)
        if tau < tf:
            return x0, y0 + 0.5 * GRAV * tau * tau
        u = smoothstep(min((tau - tf) / 0.45, 1.0))              # rolls the last little way (decelerating)
        return x0 + (rx - x0) * u, land_y

    def _in_chipmunk(self, j, t, tk):
        cx, cy, face, lean = self.chip_state(t)
        f = Xform(None, ang=face * lean, px=cx, py=cy)
        paws = f._p(*chipmunk_paws(cx, cy, self.s, face))
        cheek = f._p(*chipmunk_cheek(cx, cy, self.s, face))
        rx, ry = self.rest[j]
        if t < tk["lift"][1]:                                    # its paws close on it and lift it from the pile
            cs0 = self.chip_state(tk["lean"][1])                 # (it stays against them the whole way)
            f0 = Xform(None, ang=cs0[2] * cs0[3], px=cs0[0], py=cs0[1])
            p0 = f0._p(*chipmunk_paws(cs0[0], cs0[1], self.s, cs0[2]))
            u = smoothstep((t - tk["lean"][1]) / (tk["lift"][1] - tk["lean"][1]))
            return paws[0] + (rx - p0[0]) * (1 - u), paws[1] + (ry - p0[1]) * (1 - u)
        if t < tk["tuck"][0]:
            return paws
        if t < tk["tuck"][1]:
            u = smoothstep((t - tk["tuck"][0]) / (tk["tuck"][1] - tk["tuck"][0]))
            return paws[0] + (cheek[0] - paws[0]) * u, paws[1] + (cheek[1] - paws[1]) * u
        return None

    def chip_state(self, t):
        """(x, ground y, face, lean rad) of the chipmunk, or None while it is down its burrow."""
        if t < self.up[0] or t > self.down[1]:
            return None
        x, y, _ = self.hop.state(t)
        face = -1 if t < self.flip else 1
        lean = 0.0
        for tk in self.takes:
            if tk["lean"][0] <= t < tk["up"][1]:
                if t < tk["lean"][1]:
                    lean = self.bow[tk["j"]] * smoothstep((t - tk["lean"][0]) / 0.5)
                elif t < tk["lift"][1]:
                    lean = self.bow[tk["j"]] * (1 - smoothstep((t - tk["lift"][0]) / 0.5))
        if t < self.up[1]:                                       # coming up out of the hole
            y += (1 - smoothstep((t - self.up[0]) / (self.up[1] - self.up[0]))) * CHIP_H
        if t > self.down[0]:
            y += smoothstep((t - self.down[0]) / (self.down[1] - self.down[0])) * CHIP_H
        return x, y, face, lean

    def pouch(self, t):
        return sum(smoothstep((t - tk["tuck"][1] + 0.1) / 0.4) / 3.0 for tk in self.takes)

    def draw(self, pg, t, sh, sprout_x):
        for j in range(3):                                       # the acorns not in Sprout's hand: behind him
            p = self.acorn(j, t, sprout_x)
            if p is not None and not (self.trips[j]["reach"][1] + 0.12 <= t < self.trips[j]["drop"]):
                _acorn(pg, p[0] - sh, p[1])
        cs = self.chip_state(t)
        if cs is not None:
            x, y, face, lean = cs
            hole = skia.Path().addOval(skia.Rect(WF.BURROW1 - 48 - sh, BACK - 36, WF.BURROW1 + 48 - sh, BACK + 22))
            clip = skia.Op(skia.Path().addRect(skia.Rect(-W, -H, 2 * W, BACK + 14)), hole, skia.PathOp.kUnion_PathOp)
            pg.c.save()
            if t < self.up[1] or t > self.down[0]:               # down to the edge of its hole
                pg.c.clipPath(clip, doAntiAlias=True)
            il.creature(pg, lambda cv: chipmunk(Xform(cv, ang=face * lean, px=x - sh, py=y), x - sh, y, self.s,
                                                t, face=face, pouch=self.pouch(t), seed=False,
                                                blink=1.0 if (t % 3.7) < 0.12 else 0.0),
                        x - sh, y, shadow=None if t < self.up[1] or t > self.down[0] else 24 * K)
            pg.c.restore()

    def draw_held(self, pg, t, sh, sprout_x):
        for j, tr in enumerate(self.trips):                      # in Sprout's hand: in front of him
            if tr["reach"][1] + 0.12 <= t < tr["drop"]:
                p = self.acorn(j, t, sprout_x)
                _acorn(pg, p[0] - sh, p[1])

    def holder(self, j, t, sprout_x):
        """(who, xy) holding acorn j at time t, or how it moves by itself (a str), or None (lying still)."""
        tr = self.trips[j]
        take = [tk for tk in self.takes if tk["j"] == j][0]
        p = self.acorn(j, t, sprout_x)
        if tr["reach"][1] + 0.12 <= t < tr["drop"]:
            return ("Sprout's hand", (p[0], p[1] + 12 * K))
        if take["lean"][1] <= t < take["tuck"][1]:
            cs = self.chip_state(t)
            f = Xform(None, ang=cs[2] * cs[3], px=cs[0], py=cs[1])
            paws = f._p(*chipmunk_paws(cs[0], cs[1], self.s, cs[2]))
            if t < take["tuck"][0]:
                return ("the chipmunk's paws", paws)
            return ("the chipmunk's paws, pushing it into its cheek", p)
        if t >= tr["drop"] and t < take["lean"][1]:
            return "falls and rolls"
        return None

    def things(self, t, sh, sprout_x):
        out = {}
        for j in range(3):
            p = self.acorn(j, t, sprout_x)
            nxt = self.acorn(j, t + STEP, sprout_x)
            if p is None:
                continue
            gone = None
            if nxt is None:
                cs = self.chip_state(t)
                cheek = chipmunk_cheek(cs[0], cs[1], self.s, cs[2])
                gone = ("tucked into its cheek pouch", (cheek[0] - sh, cheek[1]))
            h = self.holder(j, t, sprout_x)
            out[f"acorn {j + 1}"] = sc.Thing(p[0] - sh, p[1], ACORN_R, gone=gone,
                                             held=(h[0], (h[1][0] - sh, h[1][1])) if isinstance(h, tuple) else None,
                                             moves=h if isinstance(h, str) else None)
        cs = self.chip_state(t)
        if cs is not None:
            out["chipmunk"] = sc.Thing(cs[0] - sh, cs[1], CHIP_H, born="comes up out of its burrow",
                                       gone=("down its burrow", (WF.BURROW1 - sh, cs[1])) if
                                       self.chip_state(t + STEP) is None else None, moves="hops", flat=1.0)
        return out


def _acorn(pg, x, y):
    il.creature(pg, lambda cv: acorn_nut(cv, x, y, ACORN_R), x, y)


# ----------------------------------------------------------------------------------------------- the beaver

BEAVER_H = ANIMAL * (35 / 20) ** 0.6           # on all fours, ~35 cm against the chipmunk's ~20
TWIG_BASE = (WF.WILLOW - 15.0, BACK - 160.0)   # a fresh green willow shoot on the trunk's left, hanging down to the
TWIG_TIP = (WF.WILLOW - 165.0, BACK - 88.0)    #   left, between Twigs (right of it) and Wheels (left): in plain view
BRANCH_L = math.hypot(TWIG_BASE[0] - TWIG_TIP[0], TWIG_BASE[1] - TWIG_TIP[1])
CARRY = 215.0                                  # they carry it this far right, to the water's edge
HELD_Y = BACK - 92.0                           # how low they can hold it (Twigs' long arms, Wheels' pincers)
ON_BANK = (TWIG_BASE[0] + CARRY, BACK - 6.0)   # where its cut end comes to rest on the bank
MUD = (WF.LODGE - 290.0, WF.WATER + 70.0)                # pushed into the mud by the lodge: its thick end down there,
MUD_ANG = math.radians(-118.0)                 #   its leafy end sticking up out of the water
WILLOW_G = (124, 150, 72)


class Beaver:
    """Twigs trims a fresh green willow shoot (beavers store fresh branches: audit 14) while Wheels holds its far
    end in his pincers; together they lay it at the water's edge and step back. The beaver swims over from its
    lodge, climbs out, takes the same branch's cut end in its teeth, backs into the water towing it, turns, swims it
    to the lodge and pushes its thick end into the mud, the leafy end left showing (6). Twigs and Wheels stand to
    the left, the beaver works on the right (20)."""

    def __init__(self, t0):
        self.t0 = t0
        self.intro = t0 + 0.5
        t = t0 + 0.8
        self.grip_w = (t, t + 1.0)                                # Wheels reaches out, closes his pincers on the tip
        self.reach_t = (t + 0.6, t + 1.6)                         # Twigs' left hand to the shoot's base
        self.blade = (self.reach_t[1], self.reach_t[1] + 0.6)     # his left blade slides out
        self.cut = (self.blade[1], self.blade[1] + 1.8)           # three small strokes; it comes free
        self.carry = (self.cut[1] + 0.4, self.cut[1] + 4.6)       # together they carry it to the water's edge
        self.lower = (self.carry[1], self.carry[1] + 0.8)         # lower it as far as they can reach
        self.let_go = (self.lower[1], self.lower[1] + 0.4)        # and let go: it drops onto the bank
        self.fall = math.sqrt(2 * (BACK - 6.0 - HELD_Y) / GRAV)
        self.back = (self.let_go[1] + 0.4, self.let_go[1] + 3.4)  # both step back, out of the beaver's way
        b = self.back[1] + 0.6
        self.s = BEAVER_H / per_s("beaver", branch=0.0)
        self.mouth_off = 0.555 * self.s                           # mouth ahead of its middle (local u)
        self.up = (b, b + 1.2)                                    # its head comes up by the lodge
        self.fact = b + 0.6
        self.swim1 = (self.up[1], self.up[1] + 6.0)               # swims over (left)
        land_x = ON_BANK[0] + self.mouth_off
        self.climb = (self.swim1[1], self.swim1[1] + 1.6)         # walks up the bank to the branch's cut end
        self.bite = (self.climb[1], self.climb[1] + 0.7)
        self.backup = (self.bite[1], self.bite[1] + 2.4)          # backs into the water, towing it
        self.turn = (self.backup[1], self.backup[1] + 2.2)        # ducks under, turns round, comes up
        self.swim2 = (self.turn[1], self.turn[1] + 5.5)           # tows it to the lodge
        self.dive = (self.swim2[1], self.swim2[1] + 1.8)          # dives and pushes it into the mud
        self.gone = self.dive[1]
        self.card = self.gone + 0.4
        self.end = max(self.card + 5.5, self.fact + _dur(LINES["beaver"][1]) + 1.0)
        self.swim_y = WF.WATER + 0.52 * BEAVER_H                  # its feet down there: back, head and nose above
        self.xk = [(self.up[0], WF.LODGE - 280.0), (self.swim1[0], WF.LODGE - 280.0), (self.swim1[1], land_x + 40),
                   (self.climb[1], land_x), (self.bite[1], land_x), (self.backup[1], land_x + 70),
                   (self.turn[1], land_x + 70), (self.swim2[1], MUD[0] - 0.2 * self.s), (self.gone, MUD[0])]
        self.xp = smooth_path(self.xk)
        self._sim()

    # --- the beaver
    def state(self, t):
        """(x, ground y, orientation -1..1, on land) or None."""
        if t < self.up[0] or t >= self.gone:
            return None
        x = self.xp(t)
        if t < self.up[1]:
            y = self.swim_y + (1 - smoothstep((t - self.up[0]) / 1.2)) * BEAVER_H
        elif t < self.climb[0]:
            y = self.swim_y
        elif t < self.climb[1]:
            y = self.swim_y + (BACK - self.swim_y) * smoothstep((t - self.climb[0]) / 1.6)
        elif t < self.bite[1]:
            y = BACK
        elif t < self.backup[1]:
            y = BACK + (self.swim_y - BACK) * smoothstep((t - self.backup[0]) / 2.4)
        elif t < self.dive[0]:
            y = self.swim_y
            if self.turn[0] <= t < self.turn[1]:                  # under, round, and up again
                u = (t - self.turn[0]) / (self.turn[1] - self.turn[0])
                y += BEAVER_H * 1.05 * (smoothstep(min(u / 0.3, 1.0)) - smoothstep(max((u - 0.7) / 0.3, 0.0)))
        else:
            y = self.swim_y + smoothstep((t - self.dive[0]) / 1.8) * BEAVER_H
        o = -1.0
        if t >= self.turn[0]:                                     # it turns round only while it is under
            u = (t - self.turn[0]) / (self.turn[1] - self.turn[0])
            o = -1.0 + 2.0 * smoothstep(min(max((u - 0.32) / 0.36, 0.0), 1.0))
        on_land = self.climb[0] <= t < self.backup[1]
        return x, y, o, on_land

    def mouth(self, t):
        x, y, o, _ = self.state(t)
        return beaver_mouth(x, y, self.s, 1, o)

    def _gait(self, t):
        """Walk cycles so far on land: its feet stay planted (one cycle = 2 strides of ground)."""
        d = 0.0
        if t > self.climb[0]:
            d += abs(self.xp(min(t, self.climb[1])) - self.xp(self.climb[0]))
        if t > self.backup[0]:
            d += abs(self.xp(min(t, self.backup[1])) - self.xp(self.backup[0]))
        return d / (2 * BEAVER_STRIDE * self.s)

    # --- the branch: a rigid stick, its cut end (base) and leafy tip
    def _bank(self):
        b = np.array(ON_BANK)
        return b, b + BRANCH_L * np.array([-0.9998, 0.02])

    def _held(self, t):
        """(base, tip) while the two of them hold it: cut, carried right, lowered."""
        A, B = np.array(TWIG_BASE), np.array(TWIG_TIP)
        d = np.array([CARRY * smoothstep((t - self.carry[0]) / (self.carry[1] - self.carry[0])), 0.0])
        lo = smoothstep((t - self.lower[0]) / (self.lower[1] - self.lower[0]))
        base = A + d + np.array([0.0, (HELD_Y - A[1]) * lo])
        a0 = math.atan2(*(B - A)[::-1])
        a1 = math.atan2(*(np.array([-1.0, 0.03]))[::-1])           # nearly level as they lower it
        ang = a0 + (a1 - a0) * lo
        return base, base + BRANCH_L * np.array([math.cos(ang), math.sin(ang)])

    def _sim(self):
        """The towed branch trails behind its cut end like a towed log (path-dependent, so worked out once). It
        starts at the bite: the beaver lifts the cut end off the bank into its mouth."""
        ts = np.arange(self.bite[0], self.dive[0] + 1e-9, 1.0 / FPS)
        _, tip = self._bank()
        self.tow = []
        bank_b, _ = self._bank()
        x0, x1 = WF.POND
        surf = WF.WATER + 3.0
        for t in ts:
            b = np.array(self.mouth(t))
            if t < self.bite[1]:
                u = smoothstep((t - self.bite[0]) / (self.bite[1] - self.bite[0]))
                b = bank_b + (b - bank_b) * u
            if x0 + 30 < b[0] < x1 - 30 or self.turn[0] <= t < self.turn[1]:   # in the water it floats at the
                b[1] = min(b[1], surf)                            # surface (the beaver turning round under it)
            d = tip - b
            tip = b + d / (np.linalg.norm(d) or 1.0) * BRANCH_L
            if x0 + 30 < tip[0] < x1 - 30 and tip[1] > surf:      # its leafy end floats too: lying along the
                dy = surf - b[1]                                  # water behind it, at its full length
                dx = math.sqrt(max(BRANCH_L ** 2 - dy * dy, 0.0))
                tip = np.array([b[0] + math.copysign(dx, tip[0] - b[0]), surf])
            self.tow.append((t, b.copy(), tip.copy()))

    def branch(self, t):
        """(base, tip) of the willow branch at time t (world)."""
        if t < self.let_go[0]:
            return self._held(t)
        bank_b, bank_t = self._bank()
        if t < self.let_go[0] + self.fall:                        # dropped: it falls flat onto the bank
            b0, t0 = self._held(self.let_go[0])
            u = ((t - self.let_go[0]) / self.fall) ** 2
            return b0 + (bank_b - b0) * u, t0 + (bank_t - t0) * u
        if t < self.bite[0]:
            return bank_b, bank_t
        if t < self.dive[0]:
            i = min(int(round((t - self.bite[0]) * FPS)), len(self.tow) - 1)
            _, b, tp = self.tow[i]
            return b, tp
        _, b0, t0 = self.tow[-1]                                  # pushed into the mud: thick end down, tip up
        u = smoothstep(min((t - self.dive[0]) / 1.8, 1.0))
        a0 = math.atan2(*(t0 - b0)[::-1])
        base = b0 + (np.array(MUD) - b0) * u
        ang = a0 + (MUD_ANG - a0) * u
        return base, base + BRANCH_L * np.array([math.cos(ang), math.sin(ang)])

    # --- the helpers' hands
    def _hand(self, t, rest, end, grab):
        """A hand going from `rest` to the branch end `end`(t), holding it, and back after letting go."""
        if t < grab[0]:
            return None
        u = smoothstep((t - grab[0]) / (grab[1] - grab[0]))
        if t > self.let_go[0]:
            u = 1 - smoothstep((t - self.let_go[0]) / 1.0)
        e = end(min(t, self.let_go[0]))
        return rest[0] + (e[0] - rest[0]) * u, rest[1] + (e[1] - rest[1]) * u

    T_OFF, W_OFF = 95.0, 135.0                                    # Twigs stands this far right of the base it holds,
                                                                  # Wheels this far left of the tip

    def twigs_hand(self, t, sh, tx):
        """Twigs' left hand target (screen), his grip and his left blade (0..1); None when he isn't working."""
        if not (self.reach_t[0] <= t <= self.let_go[1] + 1.0):
            return None, 0.0, 0.0
        hd = self._hand(t, (tx - 150 * K, G - 230 * K), lambda q: self._held(q)[0] + np.array([0.0, 6.0]),
                        self.reach_t)
        saw = 0.0
        if self.cut[0] <= t < self.cut[1]:                        # three small strokes across the cut
            saw = 5.0 * math.sin((t - self.cut[0]) / (self.cut[1] - self.cut[0]) * 3 * 2 * math.pi)
        grip = smoothstep((t - self.cut[0]) / 0.4) * (1 - smoothstep((t - self.let_go[0]) / 0.2))
        blade = smoothstep((t - self.blade[0]) / 0.6) * (1 - smoothstep((t - self.cut[1]) / 0.6))
        return (hd[0] - sh, hd[1] + saw), grip, blade

    def wheels_hand(self, t, sh, wx):
        if not (self.grip_w[0] <= t <= self.let_go[1] + 1.0):
            return None, 0.0
        hd = self._hand(t, (wx + 150 * K, G - 260 * K), lambda q: self._held(q)[1], self.grip_w)
        grip = smoothstep((t - self.grip_w[1] + 0.3) / 0.3) * (1 - smoothstep((t - self.let_go[0]) / 0.2))
        return (hd[0] - sh, hd[1]), grip

    def helper_keys(self, kd):
        """Twigs and Wheels walk along with the branch they carry, then step back."""
        x = STOPS["beaver"][kd]
        return [(self.carry[0], x), (self.carry[1], x + CARRY), (self.back[0], x + CARRY), (self.back[1], x)]

    # --- drawing
    def _water_clip(self, sh, below=-2.0):
        """Everything but the pond's water below its surface (what is in the water is hidden under it)."""
        x0, x1 = WF.POND
        under = skia.Path().addRect(skia.Rect(x0 + 30 - sh, WF.WATER + below, x1 - 30 - sh, 3 * H))
        return skia.Op(skia.Path().addRect(skia.Rect(-W, -H, 2 * W, 2 * H)), under, skia.PathOp.kDifference_PathOp)

    def _draw_branch(self, pg, t, sh):
        base, tip = self.branch(t)
        pg.c.save()
        if t >= self.dive[0]:                                     # pushed down: under the surface
            pg.c.clipPath(self._water_clip(sh, 6.0), doAntiAlias=True)
        _willow_branch(pg, base[0] - sh, base[1], tip[0] - sh, tip[1])
        pg.c.restore()

    def draw(self, pg, t, sh):
        towing = self.bite[0] <= t < self.dive[0]                 # in its teeth, beside it on the near side
        if not towing:
            self._draw_branch(pg, t, sh)
        st = self.state(t)
        if st is None:
            return
        x, y, o, land = st
        pg.c.save()
        if not land:                                             # swimming: all of it below the surface is under
            pg.c.clipRect(skia.Rect(-W, -H, 2 * W, WF.WATER - 2))  # water, wherever it is (its tail too)
            for j in range(3):                                   # a soft V of ripples behind it while it swims
                dx = -o * (40 + 34 * j)
                pg.stroke(skia.Path().moveTo(x - sh + dx, WF.WATER - 2 - 6 * j)
                          .lineTo(x - sh + dx * 1.3, WF.WATER + 4 + 4 * j), "#e2ecee", 2.5, 0.5 - 0.12 * j)
        il.creature(pg, lambda cv: beaver(cv, x - sh, y, self.s, t, face=1, kx=o, walk=1.0 if land else 0.0,
                                          gait=self._gait(t), branch=0.0,
                                          blink=1.0 if (t % 4.1) < 0.12 else 0.0),
                    x - sh, y, shadow=BEAVER_H * 0.4 if land else None)
        pg.c.restore()
        if towing:
            self._draw_branch(pg, t, sh)

    def things(self, t, sh):
        out = {}
        base, tip = self.branch(t)
        held, moves = None, None
        if self.cut[1] <= t < self.let_go[0]:
            held = ("Twigs' and Wheels' hands", (base[0] - sh, base[1]))
        elif self.let_go[0] <= t < self.let_go[0] + self.fall:
            moves = "falls onto the bank"
        elif self.bite[0] <= t:
            held = ("the beaver's teeth", (base[0] - sh, base[1]))
        mid = ((base[0] + tip[0]) / 2 - sh, (base[1] + tip[1]) / 2)
        out["willow branch"] = sc.Thing(*mid, float(np.linalg.norm(tip - base)), hidden=t > self.dive[0],
                                        held=None if held is None else (held[0], mid), moves=moves)
        st = self.state(t)
        if st is not None:
            nxt = self.state(t + STEP)
            out["beaver"] = sc.Thing(st[0] - sh, st[1], BEAVER_H, born="comes up by its lodge",
                                     gone=("into its lodge, under the water", (MUD[0] - sh, st[1]))
                                     if nxt is None else None, hidden=st[1] > self.swim_y + 0.3 * BEAVER_H,
                                     moves="swims and walks", flat=abs(st[2]))
        return out


def _willow_branch(pg, x0, y0, x1, y1):
    """A fresh willow shoot: a slim green stick, long narrow leaves along its outer two thirds."""
    from .storybook import tube
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    pg.shape(tube([(x0, y0), (x1, y1)], 7.0, 3.0), (118, 108, 62), 0.0)
    for j in range(13):
        q = 0.22 + 0.78 * j / 12
        px, py = x0 + ux * L * q, y0 + uy * L * q
        side = 1 if j % 2 else -1
        a = math.atan2(uy, ux) + side * 0.55
        lx, ly = px + math.cos(a) * 34, py + math.sin(a) * 34
        nx, ny = -math.sin(a) * 8, math.cos(a) * 8
        path = skia.Path()
        path.moveTo(px, py)
        path.quadTo((px + lx) / 2 + nx, (py + ly) / 2 + ny, lx, ly)
        path.quadTo((px + lx) / 2 - nx, (py + ly) / 2 - ny, px, py)
        pg.flat(path, WILLOW_G if j % 3 else tone(WILLOW_G, 0.15))


# ----------------------------------------------------------------------------------------------- groundhog + geese

GH_H = ANIMAL * (45 / 20) ** 0.6               # sitting up, ~45 cm against the chipmunk's ~20
DOOR_R = 70.0                                  # the groundhog's door (radius)
TUFT_S = 40.0
DIGS_ARM = 95.0 * K
DIGS_V = 80.0                                  # px/s, Digs' pace on his errands


def _digs_paws(x, t, ar, al, dy=0.0):
    """Digs' paws (world) for arm angles ar (right) and al (left) (monster: shoulders at +-118, arm 95); dy = how far
    his body has sunk (walking)."""
    by = G - 150 * K + 2 * K * math.sin(t * 2.6) + 4 * K + dy
    return ((x + 118 * K + math.cos(ar) * DIGS_ARM, by + math.sin(ar) * DIGS_ARM),
            (x - 118 * K + math.cos(al) * DIGS_ARM, by + math.sin(al) * DIGS_ARM))


def _left_paw(x, t, al):
    return _digs_paws(x, t, 1.85, al, _sink("digger", t, x))[1]


class Ground:
    """Digs brings the groundhog dry grass for its bed (groundhogs line their sleeping chamber with dry grass and
    leaves: audit 15). Twice: he stands beside a bunch of the dry grass, takes hold of it low down in his left paw
    and pulls it up out of the ground, carries it held out at his side to the groundhog's door, and sets it down
    beside the door. He steps back; the groundhog comes up, leans out, bites the bunch and pulls it down its burrow
    (owner 2026-11-05: the grass never moves by itself - it is always in a paw or a mouth, or lying still).
    Meanwhile a V of geese goes over high above the treetops (16) and Springs bounces up beside the door to watch.
    Then the groundhog goes in and plugs its door with soil from inside. Digs works on the door's right, Springs
    watches from its left (22). The grass is always drawn behind Digs (in his paw beside him, never across him)."""

    REST = math.pi - 1.85                      # his left arm hanging down
    GRAB = math.pi - 1.0                       # down beside him, his paw low on the bunch
    HOLD = math.pi - 0.55                      # lifted, held out at his side
    LEAN = 1.0                                 # how far the groundhog leans out to bite the bunch

    def __init__(self, t0):
        self.t0 = t0
        self.intro = t0 + 0.5
        self.s = GH_H / per_s("groundhog")
        rs = np.random.default_rng(41)
        centres = [WF.GRASS - 45.0, WF.GRASS + 45.0]               # two bunches of dry grass, 8 tufts each
        self.tufts = []
        for c in centres:
            xs = sorted(c + rs.uniform(-30, 30) for _ in range(8))
            self.tufts += [(x_, BACK + rs.uniform(0, 6)) for x_ in xs]
        self.bite = self._mouth((WF.DOOR3, BACK + 8, self.LEAN))   # where it bites a bunch set down by its door
        paw_dx = 118 * K + math.cos(math.pi - self.GRAB) * DIGS_ARM   # his left paw's reach to the side, low
        t = t0 + 0.5 + _dur(LINES["groundhog"][0]) + 0.3
        self.trips = []
        x = STOPS["ground"]["digger"]
        self.cache = {}
        for n in range(2):
            gx = centres[n] + paw_dx                               # he stands with the bunch at his left paw
            px = self.bite[0] + paw_dx                             # and sets it down where the groundhog can bite it
            walk0 = (t, t + abs(gx - x) / DIGS_V + EASE)
            reach = (walk0[1] - 0.2, walk0[1] + 0.6)               # paw down to the bunch as he stops
            grip = (reach[1], reach[1] + 0.25)                     # takes hold of it
            pull = (grip[1], grip[1] + 0.8)                        # pulls it up out of the ground
            walk = (pull[1] + 0.1, pull[1] + 0.1 + abs(gx - px) / DIGS_V + EASE)   # carries it to the door
            put = (walk[1], walk[1] + 0.8)                         # lowers it onto the ground
            back = (put[1] + 0.35, put[1] + 0.35 + 150.0 / DIGS_V + EASE)          # lets go, steps back out of
            self.trips.append(dict(gx=gx, px=px, walk0=walk0, reach=reach, grip=grip, pull=pull, walk=walk,
                                   put=put, back=back, tufts=list(range(8 * n, 8 * n + 8))))   # its way
            gh = back[1] - 0.4                                     # the groundhog comes for it
            self.trips[-1].update(up=(gh, gh + 1.0), lean=(gh + 1.1, gh + 1.9), grab=gh + 1.9,
                                  rise=(gh + 2.0, gh + 2.8), down=(gh + 3.0, gh + 4.0))
            x = px + 150.0
            t = max(back[1], gh + 1.0) + 0.4
        self.put_x = self.bite[0]
        self.stand = self.trips[0]["px"]
        g = self.trips[0]["put"][1] + 0.4                          # the geese, while Digs fetches the second bunch
        self.geese_intro = g
        self.geese = (g + 0.6, g + 15.0)
        self.geese_fact = g + _dur(LINES["goose"][0]) + 0.8
        self.goose_card = self.geese_fact + _dur(LINES["goose"][1]) + 0.3
        last = self.trips[-1]
        self.plug = (last["down"][1] + 0.6, last["down"][1] + 2.4)  # soil pushed into the doorway from inside
        self.gh_fact = max(self.plug[1] + 0.3, self.goose_card + 5.8)
        self.gh_card = self.gh_fact + _dur(LINES["groundhog"][1]) + 0.3
        self.end = self.gh_card + 5.8

    # --- Digs
    def digs_keys(self):
        keys = []
        for tr in self.trips:
            keys += [(tr["walk0"][1], tr["gx"]), (tr["walk"][0], tr["gx"]), (tr["walk"][1], tr["px"]),
                     (tr["back"][0], tr["px"]), (tr["back"][1], tr["px"] + 150.0)]
        last = self.trips[-1]["back"][1]
        home = STOPS["ground"]["digger"]
        keys.append((last + abs(self.trips[-1]["px"] + 150.0 - home) / DIGS_V + EASE, home))
        return keys

    def left_arm(self, t):
        """His left arm's angle at time t (the right one rests)."""
        def ease(a, b, span):
            return a + (b - a) * smoothstep(min(max((t - span[0]) / (span[1] - span[0]), 0.0), 1.0))
        for tr in self.trips:
            if t < tr["reach"][0]:
                return self.REST
            if t < tr["grip"][1]:
                return ease(self.REST, self.GRAB, tr["reach"])
            if t < tr["put"][0]:
                return ease(self.GRAB, self.HOLD, tr["pull"])
            if t < tr["back"][0]:
                return ease(self.HOLD, self.GRAB, tr["put"])
            if t < tr["back"][1]:
                return ease(self.GRAB, self.REST, (tr["back"][0], tr["back"][0] + 0.8))
        return self.REST

    def digs_arms(self, t):
        """(right, left) arm angles, or None outside his work."""
        if not (self.trips[0]["reach"][0] <= t <= self.trips[-1]["back"][1]):
            return None
        return 1.85, self.left_arm(t)

    # --- the grass
    def _grip_offsets(self, tr):
        """Each tuft of a bunch relative to the paw that holds it (fixed from the moment he takes hold)."""
        key = ("grip", tr["gx"])
        if key not in self.cache:
            pw = _left_paw(tr["gx"], tr["grip"][0], self.GRAB)
            self.cache[key] = [(self.tufts[j][0] - pw[0], self.tufts[j][1] - pw[1]) for j in tr["tufts"]]
        return self.cache[key]

    def _laid(self, tr):
        """Where each tuft lies once he has let go of it by the door."""
        key = ("laid", tr["gx"])
        if key not in self.cache:
            pw = _left_paw(tr["px"], tr["put"][1], self.GRAB)
            self.cache[key] = [(pw[0] + ox, pw[1] + oy) for ox, oy in self._grip_offsets(tr)]
        return self.cache[key]

    def tuft(self, j, t, digs_x):
        """(x, y, holder) of tuft j, or None once the groundhog has it down its burrow. holder: None (lying still),
        or (who, (x, y) of the paw / mouth holding it)."""
        tr = self.trips[j // 8]
        q = j % 8
        if t < tr["grip"][0]:
            return (*self.tufts[j], None)
        if t < tr["put"][1]:                                       # in his paw: pulled up, carried, set down
            pw = _left_paw(digs_x, t, self.left_arm(t))
            ox, oy = self._grip_offsets(tr)[q]
            return pw[0] + ox, pw[1] + oy, ("Digs' left paw", pw)
        sx_, sy_ = self._laid(tr)[q]
        if t < tr["grab"]:
            return sx_, sy_, None
        if t >= tr["down"][1]:                                     # down the burrow with the groundhog
            return None
        cs = self.gh_state(t)
        if cs is None:
            return None
        m = self._mouth(cs)
        m0 = self.bite
        g = 1.0 - 0.65 * smoothstep((t - tr["rise"][0]) / (tr["rise"][1] - tr["rise"][0]))   # bunched in its mouth
        return m[0] + (sx_ - m0[0]) * g, m[1] + (sy_ - m0[1]) * g, ("the groundhog's mouth", m)

    # --- the groundhog
    def gh_state(self, t):
        """(x, y, lean) of the groundhog, or None while it is down its burrow."""
        for tr in self.trips:
            if tr["up"][0] <= t < tr["down"][1]:
                y = BACK + 8
                if t < tr["up"][1]:
                    y += (1 - smoothstep((t - tr["up"][0]) / 1.0)) * GH_H
                if t >= tr["down"][0]:
                    y += smoothstep((t - tr["down"][0]) / 1.0) * GH_H
                lean = 0.0
                if tr["lean"][0] <= t < tr["rise"][1]:
                    if t < tr["rise"][0]:
                        lean = self.LEAN * smoothstep((t - tr["lean"][0]) / (tr["lean"][1] - tr["lean"][0]))
                    else:
                        lean = self.LEAN * (1 - smoothstep((t - tr["rise"][0]) / (tr["rise"][1] - tr["rise"][0])))
                return WF.DOOR3, y, lean
        return None

    def _mouth(self, cs):
        x, y, lean = cs
        f = Xform(None, ang=lean, px=x, py=y)
        from .animals import F as AF
        return f._p(*AF(x, y, self.s, 1).p(0.23, 0.64))

    # --- the geese: a V high over the treetops, flying left (south)
    def goose(self, i, t):
        if not (self.geese[0] <= t <= self.geese[1]):
            return None
        u = (t - self.geese[0]) / (self.geese[1] - self.geese[0])
        lead = W * 1.15 - u * W * 1.4                              # screen x of the leader (they are far away:
        row = (i + 1) // 2                                         # the sky does not pan)
        side = 1 if i % 2 else -1
        return lead + row * 58, H * 0.17 + side * row * 26 + 6 * math.sin(t * 0.9 + i)

    def springs_hop(self, t):
        """Springs bounces up to see the geese (straight up and down: his feet stay where they are)."""
        if not (self.geese[0] + 1.5 <= t <= self.geese[0] + 6.0):
            return 0.0, 0.0
        u = ((t - self.geese[0] - 1.5) / 1.5) % 1.0
        h = 26.0 * K * max(0.0, math.sin(math.pi * min(u / 0.6, 1.0))) if u < 0.6 else 0.0
        sq = 0.4 * math.sin(math.pi * (u - 0.6) / 0.4) if u >= 0.6 else 0.0
        return h, sq

    # --- drawing
    def draw_back(self, pg, t, sh, digs_x):
        for i in range(7):                                         # the geese, in the sky behind everything
            p = self.goose(i, t)
            if p is not None:
                il.creature(pg, lambda cv, p=p, i=i: draw_winter_goose(cv, p[0], p[1], t, i), p[0], p[1])
        x = WF.DOOR3 - sh
        plug = smoothstep((t - self.plug[0]) / (self.plug[1] - self.plug[0])) if t >= self.plug[0] else 0.0
        mouthful = []
        for j in range(16):                                        # the grass: on the ground or in Digs' paw
            p = self.tuft(j, t, digs_x)                            # (behind him), or in the groundhog's mouth
            if p is None:
                continue
            if p[2] is not None and p[2][0].startswith("the groundhog"):
                mouthful.append(p)
            else:
                tuft_at(pg, p[0] - sh, p[1])
        cs = self.gh_state(t)
        hole = skia.Path().addOval(skia.Rect(x - DOOR_R, BACK - DOOR_R * 0.72 - 6, x + DOOR_R, BACK + 12))
        clip = skia.Op(skia.Path().addRect(skia.Rect(-W, -H, 2 * W, BACK + 8)), hole, skia.PathOp.kUnion_PathOp)
        if cs is not None:
            gx, gy, lean = cs
            pg.c.save()
            pg.c.clipPath(clip, doAntiAlias=True)
            from .winter_animals import groundhog
            il.creature(pg, lambda cv: groundhog(Xform(cv, ang=lean, px=gx - sh, py=gy), gx - sh, gy, self.s, t,
                                                 blink=1.0 if (t % 3.9) < 0.12 else 0.0), gx - sh, gy)
            for p in mouthful:                                     # the bunch it carries in its mouth
                tuft_at(pg, p[0] - sh, p[1])
            pg.c.restore()
        if plug > 0:                                               # soil pushed up into the doorway from inside
            pg.c.save()
            pg.c.clipPath(hole, doAntiAlias=True)
            top = BACK + 12 - (DOOR_R * 0.72 + 18) * plug
            pg.shape(skia.Path().addRect(skia.Rect(x - DOOR_R, top, x + DOOR_R, BACK + 14)), WF.SOIL, 0.1)
            pg.c.restore()

    def draw_front(self, pg, t, sh, digs_x):
        """(Nothing: the grass is never drawn across Digs - it is in his paw at his side, behind him.)"""

    def things(self, t, sh, digs_x):
        out = {}
        for j in range(16):
            p = self.tuft(j, t, digs_x)
            if p is None:
                continue
            gone = None
            if self.tuft(j, t + STEP, digs_x) is None:
                m = self._mouth(self.gh_state(t))
                gone = ("pulled down the burrow in the groundhog's mouth", (m[0] - sh, m[1]))
            held = None if p[2] is None else (p[2][0], (p[2][1][0] - sh, p[2][1][1]))
            out[f"dry grass {j + 1}"] = sc.Thing(p[0] - sh, p[1], TUFT_S, gone=gone, hidden=p[1] > BACK + 14,
                                                 held=held)
        cs = self.gh_state(t)
        if cs is not None:
            nxt = self.gh_state(t + STEP)
            out["groundhog"] = sc.Thing(cs[0] - sh, cs[1], GH_H, born="comes up out of its door",
                                        gone=("down its burrow", (cs[0] - sh, cs[1])) if nxt is None else None,
                                        moves="climbs up and down by itself")
        for i in range(7):
            p = self.goose(i, t)
            if p is not None:
                out[f"goose {i + 1}"] = sc.Thing(p[0], p[1], 40.0, born="flies in from the edge of the sky",
                                                 gone=("flies on out of the sky", p) if self.goose(i, t + STEP)
                                                 is None else None, moves="flies", screen=True)
        return out


def tuft_at(pg, x, y, ang=0.0):
    """A tuft of dry grass (tipped over by ang degrees about its base), its paper grain fixed to it."""
    from .flat import tuft
    r = TUFT_S * 1.3
    pg.begin_grain((x - r, y - r, x + r, y + r))
    if ang:
        pg.c.save()
        pg.c.rotate(ang, x, y)
    tuft(pg, x, y, TUFT_S, (214, 190, 120))
    if ang:
        pg.c.restore()
    pg.end_grain(x, y)


def draw_winter_goose(cv, x, y, t, i):
    from .winter_animals import draw_winter
    draw_winter(cv, "goose", x, y, 52.0, t=t, face=-1, fly=1.0, flap=(t * 1.6 + i * 0.37) % 1.0)


# ----------------------------------------------------------------------------------------------- the bear

BEAR_H = ANIMAL * (90 / 20) ** 0.6             # on all fours, ~90 cm to the top of its head
BEAR_STRIDE = 0.18                             # winter_animals.bear's walk_leg stride (local units)
LIMB_UP = math.radians(34.0)                   # how far Hans lifts the low limb (about its root on the trunk)
GRIPS = (0.05, 0.15)                           # where his two tentacles hold it (near the trunk: the den in view)


class Bear:
    """Dusk. A bear comes along the bank from the left, looking for its den. A low limb really hangs across the
    den's way in, at its head height (audit 13); it stops. Hans, standing on the far side, lifts the limb with two
    tentacles at once, each well within 1.6x its length (11); the bear walks on in at its own size and fades into
    the den's darkness (8), and Hans lets the limb down gently. Nobody stands between the camera and the bear (21):
    Glo waits back to the left, everyone else past the rocky bank."""

    def __init__(self, t0):
        self.t0 = t0
        self.intro = t0 + 0.5
        self.s = BEAR_H / per_s("bear")
        self.head = 0.68 * self.s                                  # its nose ahead of its middle
        self.rear = 0.62 * self.s                                  # its back end behind it
        cam = WF.DEN + 150.0
        self.x0 = cam - W / 2 - self.head - 20                    # just out of the frame on the left
        self.x_wait = WF.DEN + WF.LIMB_TIP[0] - 80 - self.head     # its nose just short of the limb
        self.x_in = WF.DEN + 0.5 * WF.DEN_IN + self.rear          # its back end deep in the den's dark
        t = t0 + 2.0
        self.walk1 = (t, t + (self.x_wait - self.x0) / 70.0)
        self.look = (self.walk1[1], self.walk1[1] + 1.4)           # it stops, the limb in its way
        self.lift = (self.look[0] + 0.4, self.look[0] + 2.0)       # Hans lifts it
        self.walk2 = (self.lift[1] + 0.3, self.lift[1] + 0.3 + (self.x_in - self.x_wait) / 65.0)
        self.gone = self.walk2[1]
        self.lower = (self.gone + 0.6, self.gone + 2.4)            # and lets it down gently
        self.fact = self.walk2[0] + 0.5
        self.card = max(self.lower[1], self.fact + _dur(LINES["bear"][1])) + 0.3
        self.end = self.card + 5.8
        self.xp = smooth_path([(self.walk1[0], self.x0), (self.walk1[1], self.x_wait), (self.walk2[0], self.x_wait),
                               (self.walk2[1], self.x_in)])

    def state(self, t):
        if t < self.walk1[0] or t >= self.gone:
            return None
        return self.xp(t), BACK + 8

    def _gait(self, t):
        return (self.xp(t) - self.x0) / (2 * BEAR_STRIDE * self.s)

    def limb_angle(self, t):
        """0 = hanging across the way in; LIMB_UP = lifted out of the way."""
        u = smoothstep((t - self.lift[0]) / (self.lift[1] - self.lift[0]))
        if t >= self.lower[0]:
            u *= 1 - smoothstep((t - self.lower[0]) / (self.lower[1] - self.lower[0]))
        return LIMB_UP * u

    def limb(self, t):
        """(root, tip) of the low limb (world): it turns about where it leaves the trunk."""
        px, py = WF.DEN + WF.LIMB_PIVOT[0], BACK + 10 + WF.LIMB_PIVOT[1]
        tx, ty = WF.DEN + WF.LIMB_TIP[0], BACK + 10 + WF.LIMB_TIP[1]
        a = self.limb_angle(t)
        dx, dy = tx - px, ty - py
        ca, sa = math.cos(a), math.sin(a)                          # turning it up: the tip (left) rises
        return (px, py), (px + dx * ca - dy * sa, py + dx * sa + dy * ca)

    def grips(self, t):
        (px, py), (tx, ty) = self.limb(t)
        return [(px + (tx - px) * f, py + (ty - py) * f + 4) for f in GRIPS]

    def hans_hold(self, t):
        """How much Hans' two tentacles are on the limb (0..1): they reach out before the lift and let go after."""
        on = smoothstep((t - (self.lift[0] - 1.2)) / 1.0)
        off = 1 - smoothstep((t - (self.lower[1] + 0.2)) / 1.0)
        return on * off

    def obstacle(self, t):
        (px, py), (tx, ty) = self.limb(t)
        return (min(px, tx), min(py, ty) - 12, max(px, tx), max(py, ty) + 12)

    def bear_path_box(self):
        return (self.x_wait - self.rear, BACK + 8 - BEAR_H, self.x_in + self.head, BACK + 8)

    def draw(self, pg, t, sh):
        st = self.state(t)
        if st is not None:
            x, y = st
            far = WF.DEN + WF.DEN_IN                               # inside the den: hidden past its far wall,
            pg.c.save()                                            # darker the deeper in it is
            pg.c.clipRect(skia.Rect(-W, -H, far - sh, 2 * H))
            pg.c.saveLayer()
            il.creature(pg, lambda cv: bear(cv, x - sh, y, self.s, t, face=1, walk=1.0, gait=self._gait(t),
                                            blink=1.0 if (t % 4.3) < 0.12 else 0.0), x - sh, y,
                        shadow=BEAR_H * 0.45 if x + self.head < WF.DEN else None)
            dark = skia.GradientShader.MakeLinear([(WF.DEN - 30 - sh, 0), (far - sh, 0)],
                                                  [skia.Color4f(0.11, 0.09, 0.1, 0.0).toColor(),
                                                   skia.Color4f(0.11, 0.09, 0.1, 0.97).toColor()])
            pg.c.drawPaint(skia.Paint(Shader=dark, BlendMode=skia.BlendMode.kSrcATop))
            pg.c.restore()
            pg.c.restore()
        (px, py), (tx, ty) = self.limb(t)                          # the low limb, in front of the den
        from .storybook import tube
        pg.begin_grain((min(px, tx) - 40 - sh, min(py, ty) - 60, max(px, tx) + 40 - sh, max(py, ty) + 60))
        pg.shape(tube([(px - sh, py), ((px + tx) / 2 - sh, (py + ty) / 2 + 8), (tx - sh, ty)], 13, 5),
                 WF.TRUNK, 0.1, (0.0, -0.5))
        for j in range(7):                                         # a few autumn leaves on it
            q = 0.3 + 0.7 * j / 6
            lx, ly = px + (tx - px) * q, py + (ty - py) * q
            from .flat import leaf
            leaf(pg, lx - sh, ly - 10 + (j % 2) * 18, 16, 30 + 40 * j, (WF.PAL["orange"], WF.PAL["ochre"])[j % 2])
        pg.end_grain(-sh, 0)

    def things(self, t, sh):
        out = {}
        st = self.state(t)
        if st is not None:
            nxt = self.state(t + STEP)
            out["bear"] = sc.Thing(st[0] - sh, st[1], BEAR_H, born="walks in from the left",
                                   gone=("into its den", (WF.DEN + WF.DEN_IN - sh, st[1])) if nxt is None else None,
                                   hidden=st[0] - self.rear > WF.DEN + WF.DEN_IN * 0.5, moves="walks", flat=1.0)
        (px, py), (tx, ty) = self.limb(t)
        mid = ((px + tx) / 2 - sh, (py + ty) / 2)
        out["low limb"] = sc.Thing(*mid, math.hypot(tx - px, ty - py),
                                   held=("Hans' tentacles", mid) if self.hans_hold(t) > 0.5 else None)
        return out


# ----------------------------------------------------------------------------------------------- the chickadee

DEE_H = ANIMAL * (10 / 20) ** 0.6              # perched, ~10 cm against the chipmunk's ~20
TRAY_Y = BACK + 6 - 318                        # the feeder tray's top (winter_flat_world._feeder_post)
SEED_R = 5.0
SEEDS = [WF.FEEDER - 62.0, WF.FEEDER - 34.0, WF.FEEDER - 8.0, WF.FEEDER + 16.0, WF.FEEDER + 42.0]


class Dee:
    """Night. Glo floats up beside the feeder and his lantern lights it softly. A chickadee flies in, lands beside a
    seed, takes that seed (audit 9), pecks it open and eats it, then fluffs its feathers up into a warm round ball.
    Then the first snowflakes (the hook's promise), the goodnight, and the end sign."""

    def __init__(self, t0):
        self.t0 = t0
        self.intro = t0 + 0.5
        self.s = DEE_H / per_s("chickadee")
        self.land_x = WF.FEEDER + 70.0
        t = t0 + 0.5 + _dur(LINES["chickadee"][0]) * 0.6
        self.fly = (t, t + 3.2)                                    # flies in from the upper right
        self.hop = (self.fly[1] + 0.3, self.fly[1] + 0.9)          # one hop along to the seed beside it
        self.stand_x = SEEDS[-1] + 0.24 * self.s                    # bill over the last seed
        self.take = (self.hop[1] + 0.3, self.hop[1] + 0.6)         # takes it in its bill
        self.peck = (self.take[1] + 0.3, self.take[1] + 2.4)       # pecks it open, and eats it
        self.fact = self.take[0]
        fd = _dur(LINES["chickadee"][1])
        self.fluff = (self.fact + fd * 0.45, self.fact + fd * 0.45 + 1.4)   # as she says "fluffs its feathers"
        self.card = self.fact + fd + 0.3
        self.finale = self.card + 5.0                             # "Six neighbours... And look..."
        self.snow0 = self.finale + 2.6                            # the very first snowflakes
        self.signoff = self.finale + _dur(FINALE) + 1.2 + HOLD_END   # the quiet before the end sign
        self.sign = (self.signoff - 0.4, self.signoff + 0.6)       # the end sign comes up
        self.end = self.signoff + _dur(SIGNOFF) + 4.5
        rs = np.random.default_rng(57)
        self.flakes = []                                           # (t born, x, speed, size, sway phase)
        tt = self.snow0
        while tt < self.end:
            near = rs.random() < 0.15                              # a few nearer, bigger, quicker flakes
            self.flakes.append((tt, rs.uniform(40, W - 40), rs.uniform(55, 80) if near else rs.uniform(30, 50),
                                rs.uniform(8, 11) if near else rs.uniform(4, 6.5), rs.uniform(0, 6.3)))
            tt += rs.uniform(0.12, 0.35) * (1.6 if tt < self.snow0 + 3 else 1.0)

    # --- the bird
    def state(self, t, sh):
        """(x world, y, face, fly 0/1, flap, fluff, hop) or None before it comes."""
        if t < self.fly[0]:
            return None
        if t < self.fly[1]:
            u = (t - self.fly[0]) / (self.fly[1] - self.fly[0])
            x0 = sh + W + 60                                       # from just off the frame's right edge, high
            x = x0 + (self.land_x - x0) * smoothstep(min(u / 0.7, 1.0))   # over everyone, then down onto the tray
            high = TRAY_Y - 380                                    # (never behind a Keeper)
            y = high + (TRAY_Y - high) * smoothstep(max(0.0, (u - 0.45) / 0.55))
            return x, y, -1, 1.0, (t * 7.0) % 1.0, 0.0, 0.0
        x = self.land_x
        hop = 0.0
        if t < self.hop[1]:
            u = smoothstep((t - self.hop[0]) / (self.hop[1] - self.hop[0])) if t >= self.hop[0] else 0.0
            x = self.land_x + (self.stand_x - self.land_x) * u
            hop = math.sin(math.pi * u) if t >= self.hop[0] else 0.0
        else:
            x = self.stand_x
        fl = smoothstep((t - self.fluff[0]) / (self.fluff[1] - self.fluff[0])) if t >= self.fluff[0] else 0.0
        return x, TRAY_Y, -1, 0.0, 0.0, fl, hop

    def seed(self, j, t, sh):
        """(x, y) of seed j on the tray, in the bird's bill, or None once eaten."""
        home = (SEEDS[j], TRAY_Y - SEED_R * 0.7)
        if j != len(SEEDS) - 1 or t < self.take[0]:
            return home
        if t >= self.peck[1]:
            return None
        st = self.state(t, sh)
        bill = chickadee_bill(st[0], st[1], self.s, st[2], st[5], st[6])
        u = smoothstep((t - self.take[0]) / (self.take[1] - self.take[0]))
        return home[0] + (bill[0] - home[0]) * u, home[1] + (bill[1] - home[1]) * u

    def glo_light(self, t):
        return smoothstep((t - self.t0 + 1.0) / 2.5)

    def snow(self, t):
        """[(id, x, y, size)] snowflakes in the frame (screen: they fall everywhere, the camera is still)."""
        out = []
        for i, (tb, x0, v, r, ph) in enumerate(self.flakes):
            if t < tb:
                break
            y = -10 + v * (t - tb)
            ground = G + 40 if r > 7.5 else BACK + 10
            if y > ground:
                continue
            out.append((f"snowflake {i}", x0 + 14 * math.sin(t * 0.8 + ph), y, r))
        return out

    def draw(self, pg, t, sh):
        for j in range(len(SEEDS)):
            p = self.seed(j, t, sh)
            if p is not None:
                pg.flat(oval(p[0] - sh, p[1], SEED_R * 1.3, SEED_R * 0.8), (92, 72, 52))
        st = self.state(t, sh)
        if st is not None:
            x, y, face, fly, flap, fl, hop = st
            sing = 0.6 * abs(math.sin((t - self.peck[0]) * 9.0)) if self.peck[0] <= t < self.peck[1] else 0.0
            il.creature(pg, lambda cv: chickadee(cv, x - sh, y, self.s, t, face=face, fluff=fl, hop=hop, sing=sing,
                                                 fly=fly, flap=flap, blink=1.0 if (t % 3.3) < 0.1 else 0.0),
                        x - sh, y)

    def draw_lights(self, pg, t, sh, glo):
        """After the night: Glo's lantern lights the feeder (drawn after the tint, so it glows)."""
        gx, gy = glo
        a = self.glo_light(t)
        if a > 0:
            pg.glow(gx - sh, gy - 178 * K, 280, (255, 214, 150), 0.5 * a)
            pg.glow(WF.FEEDER - sh, TRAY_Y, 170, (255, 214, 150), 0.32 * a)

    def draw_snow(self, pg, t):
        for _, x, y, r in self.snow(t):
            pg.flat(oval(x, y, r, r), "#f8f6f0", 0.9)

    def things(self, t, sh):
        out = {}
        st = self.state(t, sh)
        if st is not None:
            out["chickadee"] = sc.Thing(st[0] - sh, st[1], DEE_H, born="flies in", moves="flies and hops")
        for j in range(len(SEEDS)):
            p = self.seed(j, t, sh)
            if p is not None:
                gone = ("eaten", (p[0] - sh, p[1])) if self.seed(j, t + STEP, sh) is None else None
                held = None
                if j == len(SEEDS) - 1 and t >= self.take[0]:
                    st = self.state(t, sh)
                    bill = chickadee_bill(st[0], st[1], self.s, st[2], st[5], st[6])
                    held = ("the chickadee's bill", (bill[0] - sh, bill[1]) if t >= self.take[1] else (p[0] - sh, p[1]))
                out[f"seed {j + 1}"] = sc.Thing(p[0] - sh, p[1], SEED_R, gone=gone, held=held)
        nxt = {n for n, *_ in self.snow(t + STEP)}
        for n, x, y, r in self.snow(t):
            out[n] = sc.Thing(x, y, r, born="falls from the sky", gone=("lands", (x, y)) if n not in nxt else None,
                              moves="falls", screen=True)
        return out


# ----------------------------------------------------------------------------------------------- on-screen text

_FONT = {}


def _font(size, weight="Bold"):
    key = (size, weight)
    if key not in _FONT:
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "..", "engine", "assets", "fonts", f"Inter-{weight}.otf")
        _FONT[key] = skia.Font(skia.Typeface.MakeFromFile(os.path.abspath(path)), size)
    return _FONT[key]


INK, PAPER = (92, 64, 54), (250, 242, 228)


def _text(pg, s, x, y, size, col=INK, a=1.0, weight="Bold", center=False):
    f = _font(size, weight)
    if center:
        x -= f.measureText(s) / 2
    pg.c.drawString(s, x, y, f, skia.Paint(AntiAlias=True, Color=C(col, a)))


def _card(pg, x, y, w, h, a):
    pg.flat(rrect(x + 4, y + 7, x + w + 4, y + h + 7, 22), (60, 40, 34), 0.18 * a, blur=8)
    pg.flat(rrect(x, y, x + w, y + h, 22), PAPER, 0.96 * a)


CARDS = ("chipmunk", "beaver", "goose", "groundhog", "bear", "chickadee")


def overlays(pg, t):
    """Screen-space text: the name tags at the start, the counter, a name card for each animal, the end sign."""
    P = plan()
    if t < P.hook + 13.0:                                         # the seven, by name, as they set out
        a = smoothstep((t - 1.0) / 0.8) * (1 - smoothstep((t - P.hook - 11.5) / 1.0))
        sh = P.shift(t)
        for kd in ORDER:
            x, y, _ = keeper(kd, t)
            if 0 < x - sh < W:
                top = y - {"wheels": 420, "tentacles": 560, "teeth": 700, "springs": 330, "lantern": 470,
                           "digger": 300, "sprout": 330}[kd] * K - 26
                f = _font(30)
                tw = f.measureText(NAMES[kd])
                _card(pg, x - sh - tw / 2 - 16, top - 34, tw + 32, 46, a)
                _text(pg, NAMES[kd], x - sh, top, 30, a=a, center=True)
    times = P.card_times()
    n = sum(1 for k in CARDS if t >= times[k])
    ca = smoothstep((t - P.hook - 11.0) / 1.0) * (1 - smoothstep((t - P.dee.sign[0]) / 0.8))
    if ca > 0:                                                    # READY FOR WINTER n / 6
        _card(pg, W - 470, 30, 440, 78, ca)
        _text(pg, f"READY FOR WINTER  {n} / 6", W - 450, 82, 32, a=ca)
    from .winter_animals import WINTER
    for k in CARDS:
        u = t - times[k]
        if 0 <= u < 6.0:
            a = smoothstep(u / 0.6) * (1 - smoothstep((u - 5.3) / 0.7))
            name, lines = WINTER[k]["name"], WINTER[k]["line"]
            _card(pg, 36, 30, 900, 178, a)
            _text(pg, name, 64, 92, 46, a=a)
            for j, ln in enumerate(lines):
                _text(pg, ln, 64, 138 + 40 * j, 31, col=(120, 92, 80), a=a, weight="Medium")
    sa = smoothstep((t - P.dee.sign[0]) / (P.dee.sign[1] - P.dee.sign[0]))
    if sa > 0:                                                    # the end sign
        bw, bh = 940, 220
        x0, y0 = (W - bw) / 2, 120
        pg.flat(rrect(x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10, 26), (40, 28, 24), 0.25 * sa, blur=10)
        pg.flat(rrect(x0, y0, x0 + bw, y0 + bh, 26), (150, 108, 72), sa)
        pg.flat(rrect(x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14, 18), (176, 132, 90), sa)
        _text(pg, "WHAT SHOULD THEY DO NEXT?", W / 2, y0 + 108, 58, col=PAPER, a=sa, center=True)
        _text(pg, "Tell us in the comments", W / 2, y0 + 168, 34, col=(250, 232, 200), a=sa, weight="Medium",
              center=True)


# ----------------------------------------------------------------------------------------------- voices + sound

BUBBLE_R = 50.0                                # px (owner 2026-11-05: the 30 px bubbles were too small)
VOICE_DUR_S = 0.6                              # how long a voice moves the mouth (the synth voices are 0.34-0.62)
ASIDES = ("hm", "mm", "hehe", "wee", "ooh")


def narration_lines(P):
    """[(t, text)] the narrator's lines, at their beats (the 15 approved FK0012 lines, already voiced)."""
    c, b, g, be, d = P.chip, P.beaver, P.ground, P.bear, P.dee
    return [(P.hook, HOOK), (c.intro, LINES["chipmunk"][0]), (c.fact, LINES["chipmunk"][1]),
            (b.intro, LINES["beaver"][0]), (b.fact, LINES["beaver"][1]),
            (g.intro, LINES["groundhog"][0]), (g.geese_intro, LINES["goose"][0]),
            (g.geese_fact, LINES["goose"][1]), (g.gh_fact, LINES["groundhog"][1]),
            (be.intro, LINES["bear"][0]), (be.fact, LINES["bear"][1]),
            (d.intro, LINES["chickadee"][0]), (d.fact, LINES["chickadee"][1]),
            (d.finale, FINALE), (d.signoff, SIGNOFF)]


def voices(P):
    """[(t, kind, mood)]: the Keepers' cute noises to the camera, at story moments and as asides on the walks,
    never while the narrator speaks (owner: they talk often, to us; she speaks alone)."""
    c, b, g, be, d = P.chip, P.beaver, P.ground, P.bear, P.dee
    ev = [(c.trips[0]["drop"] + 0.6, "sprout", "hehe"), (c.up[1] + 0.3, "teeth", "ooh"),
          (c.down[1] + 0.3, "sprout", "aww"), (b.cut[1] + 0.1, "teeth", "mm"), (b.let_go[1] + 0.4, "wheels", "yay"),
          (b.up[1] + 0.3, "digger", "ooh"), (b.gone + 0.5, "teeth", "aww"),
          (g.trips[0]["pull"][1], "digger", "huff"), (g.trips[0]["grab"] + 0.4, "digger", "mm"),
          (g.geese[0] + 1.5, "springs", "ooh"), (g.geese[0] + 3.6, "springs", "wee"), (g.plug[1] + 0.3, "digger", "aww"),
          (be.walk1[0] + 3.0, "springs", "ooh"), (be.lift[0] + 0.2, "tentacles", "huff"),
          (be.gone + 0.5, "tentacles", "mm"), (d.fly[1] + 0.3, "lantern", "ooh"), (d.fluff[1] + 0.4, "digger", "aww"),
          (d.snow0 + 1.4, "springs", "brr"), (d.snow0 + 2.2, "tentacles", "ooh"), (d.sign[1] + 0.2, "wheels", "yay")]
    rs = np.random.default_rng(73)
    for ta, tb in [(0.0, c.t0), (c.end, b.t0), (b.end, g.t0), (g.end, be.t0), (be.end, d.t0)]:
        t = ta + rs.uniform(3.0, 5.0)
        while t < tb - 2.0:                                        # asides on the walks: one on screen turns to us
            sh = P.shift(t)
            seen = [kd for kd in ORDER if 120 < P.paths[kd](t) - sh < W - 120]
            if seen:
                ev.append((t, seen[rs.integers(len(seen))], ASIDES[rs.integers(len(ASIDES))]))
            t += rs.uniform(4.0, 6.5)
    lines = [(t0, t0 + _dur(tx)) for t0, tx in narration_lines(P)]
    ev = [e for e in sorted(ev) if not any(a - 0.7 <= e[0] <= b_ + 0.7 for a, b_ in lines)]
    out = []
    for e in ev:                                                   # at least 1.2 s between two voices
        if not out or e[0] - out[-1][0] >= 1.2:
            out.append(e)
    return out


def talking(P, kd, t):
    """(mouth open 0..1, eyes on us 0..1, little bounce px) for Keeper kd at time t."""
    m, look, hop = 0.0, 0.0, 0.0
    for tv, k, mood in P.voices:
        if k != kd or not (tv - 0.4 <= t <= tv + VOICE_DUR_S + 0.6):
            continue
        u = (t - tv) / VOICE_DUR_S
        if 0 <= u <= 1:
            m = max(m, 0.7 * math.sin(math.pi * u) * (0.75 + 0.25 * math.sin(u * 18)))
            hop = max(hop, 7 * K * math.sin(math.pi * u))
        look = max(look, smoothstep((t - tv + 0.4) / 0.4) * (1 - smoothstep((t - tv - VOICE_DUR_S - 0.2) / 0.4)))
    return m, look, hop


def bubbles(pg, t):
    """A small bubble with a picture over whoever speaks (never words)."""
    from .chatter import MOODS, _back, bubble
    P = plan()
    sh = P.shift(t)
    for tv, kd, mood in P.voices:
        u = t - tv
        pic = MOODS[mood][2]
        if pic is None or pic in ("!", "?") or not (0 <= u < 1.4):
            continue
        x, y, _ = keeper(kd, t)
        top = y - {"wheels": 420, "tentacles": 560, "teeth": 700, "springs": 330, "lantern": 470, "digger": 300,
                   "sprout": 330}[kd] * K
        s = _back(min(u / 0.25, 1.0)) * (1 - smoothstep((u - 1.1) / 0.3))
        bx, by = x - sh + 70 * K + 26, top - 62
        il.creature(pg, lambda cv, bx=bx, by=by, s=s, pic=pic: bubble(cv, bx, by, BUBBLE_R * s, pic, (214, 196, 176),
                                                                     1.0, (bx - 62, by + 92)), bx, by)


def soundtrack(path):
    """The music box (the episode's own variant), the Keepers' voices, soft sounds for what happens on screen, and
    the narrator over it all (narrator.soundtrack: the music eases down only while she speaks). -> (wav, stats)"""
    from engine.audio import EventTrack
    from . import music
    from .chatter import MOODS, VOICE, VOWEL
    from .narrator import soundtrack as narr_mix, take
    P = plan()
    track = EventTrack(13)
    chords = music.compose(track, 0.3, P.end - 1.0, gain=0.9, variant="winterready")
    pan = lambda x: max(-0.6, min(0.6, (x / W) * 1.2 - 0.6))       # noqa: E731
    for tv, kd, mood in P.voices:                                  # the Keepers
        contour, st, _ = MOODS[mood]
        x = keeper(kd, tv)[0] - P.shift(tv)
        track.hit(tv, f"voice_{contour}@{int(round(VOWEL[kd] * 100))}", VOICE[kd] + st, 0.3, pan(x))
    c, b, g, be, d = P.chip, P.beaver, P.ground, P.bear, P.dee
    for tr in c.trips:                                             # acorns: a soft wooden tock as each lands
        tock = tr["drop"] + math.sqrt(max(2 * 50.0 / GRAV, 0.0))
        track.hit(tock, "pluck", 64, 0.16, pan(tr["dx"] - P.shift(tock)))
    for tk in c.takes:
        track.fx(tk["tuck"][0], "rustle", 0.25, 0.08)
    for k in range(3):                                             # the willow: three little cuts, the drop
        track.fx(b.cut[0] + k * (b.cut[1] - b.cut[0]) / 3, "rustle", 0.3, 0.12)
    track.fx(b.let_go[0] + b.fall, "leaf_settle", 0.5, 0.14)
    track.fx(b.up[0], "splash", 0.5, 0.08)
    track.fx(b.backup[1] - 0.6, "splash", 0.6, 0.12)
    track.fx(b.turn[0] + 0.3, "splash", 0.6, 0.1)                  # it ducks under to turn round
    track.fx(b.turn[1] - 0.5, "splash", 0.5, 0.08)
    track.fx(b.dive[0] + 0.4, "splash", 0.8, 0.14)
    for tr in g.trips:                                             # the dry grass
        track.fx(tr["pull"][0], "rustle", 1.0, 0.1)
        track.fx(tr["put"][0] + 0.4, "leaf_settle", 0.4, 0.1)
        track.fx(tr["grab"], "rustle", 0.6, 0.09)
    track.fx(g.plug[0], "sand_scrape", 1.4, 0.1)
    for k in range(6):                                             # the geese, far off: soft low honks
        tt = g.geese[0] + 1.0 + k * 1.7 + (0.4 if k % 2 else 0.0)
        track.hit(tt, "voice_hey@64", 57 + (k % 3), 0.07, -0.3 + 0.1 * k)
    track.fx(be.lift[0], "creak", 1.2, 0.08)
    track.fx(be.lift[0] + 0.3, "rustle", 1.0, 0.08)
    track.fx(be.lower[0], "rustle", 1.0, 0.06)
    track.fx(d.fly[1] - 0.3, "rustle", 0.4, 0.07)                  # the chickadee's wings as it lands
    for k in range(4):                                             # it pecks the seed open
        track.hit(d.peck[0] + 0.2 + k * 0.45, "pluck", 84, 0.06, -0.2)
    bed = {"type": "procedural", "name": "keepers_song", "gain": 0.9, "chords": chords,
           "reverb": {"decay": 3.5, "wet": 0.4, "tone": 2600}}

    class Shim:                                                    # what narrator.soundtrack reads off a scene
        p = {"audio": {}}
        events_gain = 1.0
        reverb = None
    sc_ = Shim()
    sc_.bed = bed
    sc_.narration = [(t0, take(tx)) for t0, tx in narration_lines(P)]
    wav, stats = narr_mix(sc_, track, P.end)
    import shutil
    shutil.move(wav, path)
    return path, stats, track


# ----------------------------------------------------------------------------------------------- the plan

class Plan:
    """The timeline and everyone's way through it: walk, beat, walk, beat... (all seven walk together between stops:
    they start and stop at once, so the order holds and nobody passes anyone)."""

    def __init__(self):
        self.hook = 2.0
        # they stand together while the hook is told (their name tags up), then set off, arriving as it ends
        self.set_off = max(0.0, self.hook + _dur(HOOK) + 0.6 - (self._walk("start", "chip", 0.0)))
        t = self._walk("start", "chip", self.set_off)
        self.chip = Chip(t)
        t1 = self._walk("chip", "beaver", self.chip.end)
        self.beaver = Beaver(t1)
        t2 = self._walk("beaver", "ground", self.beaver.end)
        self.ground = Ground(t2)
        t3 = self._walk("ground", "bear", self.ground.end)
        self.bear = Bear(t3)
        WF.DUSK = (self.ground.end, self.bear.t0 + 10.0)          # dusk falls on the way to the bear,
        WF.NIGHT = (self.bear.end - 10.0, self.bear.end + 35.0)   # night on the way to the feeder
        t4 = self._walk("bear", "dee", self.bear.end)
        self.dee = Dee(t4)
        self.end = self.dee.end
        self.legs = [("start", self.set_off, "chip", self.chip.t0), ("chip", self.chip.end, "beaver", self.beaver.t0),
                     ("beaver", self.beaver.end, "ground", self.ground.t0), ("ground", self.ground.end, "bear",
                                                                             self.bear.t0),
                     ("bear", self.bear.end, "dee", self.dee.t0)]
        self.paths = self._paths()
        mid = lambda a, b: (a + b) / 2                            # noqa: E731
        self.cam = walk_path([(0.0, STOPS["start"]["springs"] + 200), (self.set_off, STOPS["start"]["springs"] + 200),
                                (self.chip.t0 - 2, mid(WF.STUMP, WF.BURROW1) - 60),
                                (self.chip.end, mid(WF.STUMP, WF.BURROW1) - 60),
                                (self.beaver.t0, mid(WF.WILLOW, WF.LODGE) - 260),
                                (self.beaver.end, mid(WF.WILLOW, WF.LODGE) - 260),
                                (self.ground.t0, mid(WF.DOOR3, WF.GRASS) - 10),
                                (self.ground.end, mid(WF.DOOR3, WF.GRASS) - 10),
                                (self.bear.t0, WF.DEN + 150.0), (self.bear.end, WF.DEN + 150.0),
                                (self.dee.t0, WF.FEEDER + 250.0), (self.end, WF.FEEDER + 250.0)], 2.0)
        self.turns = {kd: heading(self.paths[kd]) for kd in ORDER}  # they turn to face where they walk
        narrow = lambda kd, f=1.0: (lambda t: 1.0 - TURN_NARROW * f * abs(self.turns[kd](t)))   # noqa: E731
        self.gaits = {}
        for kd in ("teeth", "digger", "sprout"):
            self.gaits[kd] = biped(kd, self.paths[kd], G, K, spread=narrow(kd))
        self.gaits["tentacles"] = TripodGait(0, 0, G, K, period=0.8, path=self.paths["tentacles"],
                                             spread=narrow("tentacles", 0.5))
        self.hopper = Hopper(self.paths["springs"], G, K)
        self.voices = []
        self.voices = voices(self)

    def _walk(self, a, b, t0):
        """How long the walk from stop a to stop b takes: the farthest walker at V_AVG (Glo floats, so he may
        glide twice as fast)."""
        d = max(abs(STOPS[b][kd] - STOPS[a][kd]) / (2.0 if kd == "lantern" else 1.0) for kd in ORDER)
        return t0 + d / V_WALK + EASE

    def card_times(self):
        return dict(chipmunk=self.chip.card, beaver=self.beaver.card, goose=self.ground.goose_card,
                    groundhog=self.ground.gh_card, bear=self.bear.card, chickadee=self.dee.card)

    def _paths(self):
        out = {}
        for kd in ORDER:
            keys = []
            for a, ta, b, tb in self.legs:
                xa = self.chip.sprout_x_end if (kd == "sprout" and a == "chip") else STOPS[a][kd]
                keys += [(ta, xa), (tb, STOPS[b][kd])]
                if kd == "sprout" and b == "chip":
                    keys += self.chip.sprout_keys()
            if kd in ("teeth", "wheels"):
                keys += self.beaver.helper_keys(kd)
            if kd == "digger":
                keys += self.ground.digs_keys()
            out[kd] = walk_path(sorted(set(keys)), EASE)
        return out

    def shift(self, t):
        return max(0.0, self.cam(t) - W / 2)


PLAN = None


def plan():
    global PLAN
    if PLAN is None:
        PLAN = Plan()
    return PLAN


# ----------------------------------------------------------------------------------------------- the Keepers

WR = 46.0 * K


def keeper(kd, t):
    """(world x, y, monster attrs) of Keeper kd at time t, talking when it says something."""
    x, y, a = _keeper(kd, t)
    P = plan()
    a["legs_turn"] = P.turns[kd](t)
    a["turn"] = a["legs_turn"] * (1 - a.pop("face_us", 0.0))
    if P.voices:
        m, look, hop = talking(P, kd, t)
        if m > 0 or look > 0:
            a = dict(a, talk=m, attend=max(a.get("attend", 0.0), look), turn=a["turn"] * (1 - look))
            if kd not in ("teeth", "digger", "sprout", "tentacles"):   # (walkers' feet stay put: no hop)
                y -= hop
    return x, y, a


LEG = {"digger": (62.0, 78.0), "sprout": (38.0, 70.0)}         # knee-less walkers: hip offset, leg length (units)


def _sink(kd, t, x):
    """Digs and Sprout (straight legs, no knees) sink a touch as their feet spread, so each leg keeps its length."""
    hip, leg = LEG[kd]
    P = plan()
    n = 1.0 - TURN_NARROW * abs(P.turns[kd](t))
    return stance_drop(P.gaits[kd], lambda t_: (x - hip * K * n, x + hip * K * n), leg * K, t)


def _keeper(kd, t):
    P = plan()
    sh = P.shift(t)
    if kd in ("teeth", "digger", "sprout", "tentacles"):
        g = P.gaits[kd]
        a = dict(feet=[(fx - sh, fy) for fx, fy in g.feet(t)], attend=0.25)
        if kd == "tentacles":                                     # excited by the first snowflakes
            d = P.dee
            u = (t - d.snow0 - 0.4) / 0.6
            a.update(float=0.2, **hans_mood("calm", "excited", u) if u > 0 else hans_mood("calm"))
            return g.body_x(t), G + g.bob(t), a
        if kd == "sprout":
            ang, grip = P.chip.sprout_arm(t)
            a.update(arm_ang_r=ang, grip=grip)
        if kd == "digger":
            arms = P.ground.digs_arms(t)
            if arms is not None:
                a["paw_ang"] = {1: arms[0], -1: arms[1]}
        if kd == "teeth":
            hd, grip, blade = P.beaver.twigs_hand(t, sh, g.body_x(t))
            a.update(hands=True, saws=False, blades=0.0, blades_l=blade, grip=grip)
            if hd is not None:
                a["arm_to"] = {-1: hd}
            return g.body_x(t), G, a
        return g.body_x(t), G + _sink(kd, t, g.body_x(t)), a
    if kd == "springs":
        x, y, sq = P.hopper.state(t)
        h, sq2 = P.ground.springs_hop(t)
        return x, y - h, dict(spring=sq + sq2, attend=0.25)
    if kd == "wheels":
        x = P.paths[kd](t)
        a = dict(wheel_rot=x / WR, attend=0.25)
        hd, grip = P.beaver.wheels_hand(t, sh, x)
        if hd is not None:
            a.update(arm_to={1: hd}, grip=grip)
        return x, G, a
    u = P.dee.glo_light(t)                                     # Glo floats along; at the feeder he rises
    return P.paths[kd](t), G - 40 * K - 190 * u, dict(attend=0.25, lamp=1.0 + 0.6 * u)   # up beside its tray


def hans_extra(t, sh):
    """Hans' two working tentacles on the low limb (bear beat), drawn on his own layer; records m.work."""
    P = plan()
    hold = P.bear.hans_hold(t)

    def draw(cv, m):
        m.work = []
        if hold <= 0.001:
            return
        hy = m.y - 305 * K
        for (gx, gy), slot in zip(P.bear.grips(t), (-1, -2)):
            rest = (m.x - (60 + 20 * abs(slot)) * K, hy + 150 * K)
            tx, ty = rest[0] + (gx - sh - rest[0]) * hold, rest[1] + (gy - rest[1]) * hold
            root, L = m.work_tentacle(cv, tx, ty, t, slot=slot, grip=hold)
            m.work.append((slot, root, (tx, ty), L))
    return draw


def frame(pg, valley, t):
    """Draw the frame at time t onto pg; -> metrics for the checks."""
    P = plan()
    sh = P.shift(t)
    WF.sky(pg, t)
    valley.draw(pg, sh, paint=skia.Paint(Alphaf=WF.cloud_alpha(t)), only={"clouds"})
    valley.draw(pg, sh, only={"far", "far2", "far_trees", "mid", "field", "ground"})
    sx = keeper("sprout", t)[0]
    P.chip.draw(pg, t, sh, sx)
    P.beaver.draw(pg, t, sh)
    dx = keeper("digger", t)[0]
    P.ground.draw_back(pg, t, sh, dx)
    P.bear.draw(pg, t, sh)
    P.dee.draw(pg, t, sh)
    ms = {}
    for kd in reversed(ORDER):                                    # back first: Glo, Hans, ...
        x, y, a = keeper(kd, t)
        if -500 < x - sh < W + 500:
            ms[kd] = il.figure(pg, kd, x - sh, y, K, 6, t=t, extra=hans_extra(t, sh) if kd == "tentacles" else None,
                               **a)
        if kd == "sprout":
            P.chip.draw_held(pg, t, sh, sx)
        if kd == "digger":
            P.ground.draw_front(pg, t, sh, dx)
    P.dee.draw_snow(pg, t)
    WF.apply_light(pg, t)
    P.dee.draw_lights(pg, t, sh, keeper("lantern", t)[:2])
    bubbles(pg, t)
    overlays(pg, t)
    return {kd: list(getattr(m, "leg_len", [])) for kd, m in ms.items()}
