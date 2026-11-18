"""Forest Keepers episode 13: Getting Ready for Winter (docs/engines/forest_keepers_winter_ready.md), 16:9, narrated.

The owner approved the storyboard (2026-11-03, "Yes, I approve"; the animals fact-checked, see the doc). One walk,
sunset to night, no cuts. Each of the seven Keepers gives one animal a gentle hand, and nobody touches or chases
them: the animals live in the layer behind the path (burrows, the pond and the lodge, the den, the feeder), the
Keepers walk the path in front of it in one fixed order, Sprout in front and Glo at the back, so nobody ever
passes anyone. At each place the ones ahead walk on past it and the helper stops beside it.

  HOOK      the seven at sunset, the name tags, the narrator: "...And at the very end, watch for the very first
            snowflakes." The counter READY FOR WINTER 0 / 6 comes up.
  CHIPMUNK  Sprout carries acorns from the old stump to a pile by the chipmunk's burrow, one at a time; the chipmunk
            comes out, stuffs its cheek pouches full and pops back down. 1 / 6.
  BEAVER    Twigs slides out one blade and trims a branch off the fallen tree; it drops into Wheels' cart. The beaver
            swims over, takes it, swims back and pushes it into the mud by its lodge. 2 / 6.
  GEESE + GROUNDHOG  Digs sweeps the old leaves out of the groundhog's door; the groundhog comes up and looks round
            while a V of geese goes over honking and Springs bounces up to watch (3 / 6); then the groundhog goes
            down to sleep (4 / 6).
  BEAR      dusk: Hans lifts a low branch out of the way with a tentacle and the bear ambles into its den. 5 / 6.
  CHICKADEE night: Glo's soft light on the feeder; the chickadee takes a seed and fluffs up into a warm ball; the
            first snowflakes. 6 / 6. Goodnight. (End sign appended by the scene.)
"""
import math

import numpy as np

from families.foundry.keepers.common import ellipse, lerp, rect, seg, smoothstep, smootherstep, GRAVITY
from families.foundry.products.monster import ACORN, CAP, Monster, Xform, acorn_nut, lighten
from families.foundry.style import STEEL

from .animal_houses import G
from .animals import F, _c
from .bug_hunt import CARD, INK, PAPER, WOOD
from .book import clipped
from .doorway import HALF_W, fade_clip
from .harvest_feast import cam_keys
from .narrator import say, speaking
from .tune_up import GLO_UP, Route, TuneAct, bump, work_flash
from .winter_animals import WINTER, draw_winter

O7 = ["sprout", "teeth", "wheels", "digger", "springs", "tentacles", "lantern"]     # front (right) to back (left)
BACK = G - 26.0                         # the animals' ground, behind the path
WATER_Y = G - 40.0                      # the pond's surface (behind the path)
PUSH = 185.0                            # Wheels pushes his little cart from this far behind it
TRUNK = np.array([86, 62, 46.0])
BARKC = np.array([92, 70, 52.0])
SOIL = np.array([84, 62, 44.0])
ROCK = np.array([92, 88, 90.0])
GOLD, ORANGE, RED = np.array([226, 170, 64.0]), np.array([214, 118, 48.0]), np.array([176, 70, 44.0])
POND_C = np.array([64, 82, 112.0])
LAMP = np.array([255, 214, 150.0])
CARTW = np.array([140, 100, 64.0])
SNOWC = np.array([236, 240, 250.0])

HOOK = ("The days are getting shorter, and the forest is getting ready for winter. How will each of our "
        "neighbours get ready? And at the very end, watch for the very first snowflakes.")
LINES = {
    "chipmunk": ("Sprout has found a busy little neighbour, by the old stump.",
                 "An eastern chipmunk. It carries seeds home in its stretchy cheek pouches, and stores them "
                 "underground."),
    "beaver": ("Down at the pond, someone is collecting branches.",
               "A beaver. It pushes branches into the mud by its lodge, to eat under the ice all winter."),
    "goose": ("Listen... honking, high up in the sky.",
              "Canada geese. Many fly south for the winter, in a V. Each bird rides the air lifted by the one "
              "ahead."),
    "groundhog": ("Digs knows this little door. Someone is getting sleepy.",
                  "A groundhog. It hibernates all winter in its burrow, its heart beating only a few times a "
                  "minute."),
    "bear": ("Shh. Someone big is looking for a cosy place to sleep.",
             "A black bear. It eats and eats all autumn, then sleeps the winter away in a cosy den."),
    "chickadee": ("The sun has gone, and the stars are out. One little neighbour is staying right here.",
                  "A chickadee. It stays all winter. It fluffs its feathers into a warm coat, and remembers where "
                  "it hid its seeds."),
}
FINALE = "Six neighbours, all ready for winter. And look... the very first snowflakes. Goodnight, forest."
SIGNOFF = "What should the Keepers do next? Tell us in the comments."

# where things are (world x)
STUMP, PILE, BURROW1 = 2060.0, 1880.0, 1780.0              # the chipmunk's acorns, pile and burrow
CART2 = 3200.0                                             # where Wheels parks the cart under the branch
POND = (3060.0, 4380.0)
LODGE = 4150.0
HOLE3 = 5620.0                                             # the groundhog's door
DEN = 7300.0                                               # the bear's den in the rocky bank
FEEDER = 9000.0
ANIMAL_S = {"chipmunk": 150.0, "beaver": 136.0, "goose": 58.0, "groundhog": 150.0, "bear": 182.0, "chickadee": 120.0}


def hw(kind, k=0.55):
    return HALF_W.get(kind, 200.0) * k


def probe(kind, k, x, y, **kw):
    m = Monster(kind, k)
    m.newlook, m.x, m.y, m.alive = True, x, y, 1.0
    for a, v in kw.items():
        setattr(m, a, v)
    return m


def fall(y0, tau):
    return y0 + 0.5 * GRAVITY * tau * tau


def beaver_branch(c, x, y, s, face, dv=0.0, du=0.0):
    """The leafy branch exactly as the beaver carries it (winter_animals.beaver), moved by (du, dv) in its frame:
    lying in the cart, then lifted to its teeth."""
    f = F(x, y, s, face)
    hx, hy = 0.4 + du, 0.36 + dv
    BR = _c(110, 82, 56)
    f.line(c, [(hx + 0.04, hy - 0.13), (hx + 0.16, hy - 0.1), (hx + 0.5, hy - 0.02)], BR, 0.022)
    f.line(c, [(hx + 0.34, hy - 0.06), (hx + 0.44, hy + 0.06)], BR, 0.013)
    for k, (u, v, a) in enumerate(((hx + 0.49, hy - 0.02, 0.2), (hx + 0.44, hy + 0.06, 1.1),
                                   (hx + 0.3, hy - 0.07, -1.2), (hx + 0.4, hy - 0.05, -0.5))):
        col = _c(226, 176, 64) if k % 2 == 0 else _c(206, 132, 52)
        ca, sa = math.cos(a), math.sin(a)
        f.blob(c, [(u, v), (u + 0.06 * ca - 0.025 * sa, v + 0.06 * sa + 0.025 * ca), (u + 0.1 * ca, v + 0.1 * sa),
                   (u + 0.06 * ca + 0.025 * sa, v + 0.06 * sa - 0.025 * ca)], col, 3)


class WinterAct(TuneAct):
    name = "winter"
    STRETCH = 1.2                         # slow on purpose (owner): the whole walk runs a fifth slower
    LEAD = 9.0
    names = (0.8 - LEAD, 7.5 - LEAD)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.mk = scene.k
        for m in scene.monsters:
            m.job = "keeper"
        sp = self.m("sprout")
        if sp is not None:
            sp.acorn = False                     # it planted its acorn in its own episode
        self._plan()
        self.stats = {"animals": list(WINTER), "narrator_lines": len(self.lines)}

    # ====================================================================== the plan

    def _place_row(self, helpers, site):
        """Everyone's spot at a place: helpers at their given x; the ones ahead of the first helper (O7 order) walk on
        past site[1]; the ones behind the last helper stop left of it. -> {kind: x}."""
        k = self.mk
        pos = dict(helpers)
        hi = [O7.index(h) for h in helpers]
        first, last = min(hi), max(hi)
        edge = site[1]                                            # ahead: left to right, the nearest one first
        for kd in reversed(O7[:first]):
            lw = hw(kd, k)
            pos[kd] = edge + lw + 18.0
            edge = pos[kd] + (PUSH + 110.0 if kd == "wheels" else hw(kd, k))
        kd0 = O7[last]                                            # behind: right to left
        edge = pos[kd0] - hw(kd0, k) - 18.0
        for kd in O7[last + 1:]:
            right = PUSH + 110.0 if kd == "wheels" else hw(kd, k)
            pos[kd] = edge - right
            edge = pos[kd] - hw(kd, k) - 18.0
        return pos

    def _walk(self, R, pos, t0, v=165.0):
        """Everyone walks on to pos, the one in front setting off first (nobody catches anyone up)."""
        for j, kd in enumerate(O7):
            R[kd].wait(t0 + 0.4 * j).go(pos[kd], v=v)
        return max(R[kd].t for kd in O7)

    def _plan(self):
        k = self.mk
        self.lines = []
        T = self.T = {}
        sp = probe("sprout", k, 0.0, G)
        _, hd = sp.sprout_arm(0.0)
        self.hand_dx = hd[0]                                      # Sprout's hand, left of its middle
        sp.hold_out = 1.0
        _, hd2 = sp.sprout_arm(0.0)
        self.drop_dx, self.drop_y = hd2[0] - 6 * k, hd2[1] - 14 * k - G
        self.pick_x = STUMP - self.hand_dx                       # Sprout where its hand is over the stump's acorns
        self.drop_x = PILE - self.drop_dx
        R = {}
        # 0: the hook, everyone in a row in the west at sunset
        P0 = self._place_row({"sprout": 1200.0}, (0.0, 0.0))
        for kd in O7:
            R[kd] = Route(P0[kd], -self.LEAD)
        d = say(self, 1.0 - self.LEAD, HOOK)
        T["counter"] = 1.0 - self.LEAD + d + 0.5
        # 1: the chipmunk
        P1 = self._place_row({"sprout": self.pick_x}, (0.0, 0.0))
        behind_edge = BURROW1 - 90.0                             # nobody stands in front of the burrow or the pile
        x = behind_edge
        for kd in O7[1:]:
            right = PUSH + 110.0 if kd == "wheels" else hw(kd, k)
            P1[kd] = x - right
            x = P1[kd] - hw(kd, k) - 18.0
        a = self._walk(R, P1, T["counter"] - 2.0, v=120.0)
        T["c_hint"] = a - 2.0
        dh = say(self, T["c_hint"], LINES["chipmunk"][0])
        t = max(a, T["c_hint"] + dh) + 0.6
        trips = []
        for q in range(3):                                         # pick at the stump, carry, drop on the pile
            pick = t + 0.4
            R["sprout"].wait(pick + 0.8).go(self.drop_x, v=90)
            drop = R["sprout"].t + 0.6
            R["sprout"].wait(drop + 0.9).go(self.pick_x, v=90)
            t = R["sprout"].t
            trips.append((pick, drop))
        T["trips"] = trips
        c0 = t + 1.0
        T["chip"] = dict(up=(c0, c0 + 1.2), go=(c0 + 1.8, c0 + 2.8), eat=[c0 + 3.4 + 1.6 * q for q in range(3)],
                         back=(c0 + 8.6, c0 + 9.6), down=(c0 + 10.0, c0 + 11.0))
        T["tick1"] = c0 + 11.0
        dl = say(self, T["tick1"] + 0.8, LINES["chipmunk"][1])
        T["card1"] = (T["tick1"] + 0.5, T["tick1"] + 0.8 + max(dl + 1.8, 9.0))
        # 2: the beaver
        tw = probe("teeth", k, 0.0, G, hands=True, blades_l=1.0, punch_l=0.9)
        bx, by = tw.blade_tip(-1, 0.0)
        self.bx2 = CART2 + 70.0                                  # where the beaver stands to take the branch
        cutx = self.bx2 - 0.44 * ANIMAL_S["beaver"]              # the branch's thick end (beaver_branch's u = 0.44)
        self.twigs2 = cutx - bx                                  # his left blade at the thick end, over the cart
        self.cut2 = (cutx, by)
        P2 = self._place_row({"teeth": self.twigs2, "wheels": CART2 - PUSH}, (0.0, POND[1] + 40.0))
        a = self._walk(R, P2, T["card1"][1] - 1.0)
        T["b_hint"] = a - 1.5
        dh = say(self, T["b_hint"], LINES["beaver"][0])
        t = max(a, T["b_hint"] + dh) + 0.8
        T["trim"] = (t, t + 1.0, t + 2.2, t + 4.6)                # blade out, lift, saw, cut
        b0 = T["trim"][3] + 1.6
        T["bv"] = dict(swim_in=(b0, b0 + 6.0), climb=(b0 + 6.0, b0 + 6.6), take=(b0 + 7.0, b0 + 8.0),
                       back=(b0 + 8.4, b0 + 9.2), under=(b0 + 9.2, b0 + 10.2), up=(b0 + 10.6, b0 + 11.4),
                       swim_out=(b0 + 11.4, b0 + 17.0), dive=(b0 + 17.4, b0 + 18.8))
        T["tick2"] = b0 + 18.8
        dl = say(self, T["tick2"] + 0.8, LINES["beaver"][1])
        T["card2"] = (T["tick2"] + 0.5, T["tick2"] + 0.8 + max(dl + 1.8, 9.0))
        # 3: the groundhog and the geese
        dg = probe("digger", k, 0.0, G)
        self.digs3 = HOLE3 - 150.0
        P3 = self._place_row({"digger": self.digs3}, (0.0, HOLE3 + 150.0))
        a = self._walk(R, P3, T["card2"][1] - 1.0)
        T["g_hint"] = a - 1.5
        dh = say(self, T["g_hint"], LINES["groundhog"][0])
        t = max(a, T["g_hint"] + dh) + 0.6
        T["sweep"] = (t, t + 4.0)
        h0 = T["sweep"][1] + 0.8
        T["gh"] = dict(up=(h0, h0 + 1.4), look=(h0 + 1.4, h0 + 24.0))
        T["geese_hint"] = h0 + 2.5
        dh = say(self, T["geese_hint"], LINES["goose"][0])
        T["geese"] = (T["geese_hint"] + 1.0, T["geese_hint"] + 1.0 + 13.0)
        T["tick3"] = T["geese"][1] - 1.0
        dl = say(self, T["tick3"] + 0.8, LINES["goose"][1])
        T["card3"] = (T["tick3"] + 0.5, T["tick3"] + 0.8 + max(dl + 1.8, 9.0))
        dn = T["card3"][1] + 0.5
        T["gh"]["look"] = (h0 + 1.4, dn)
        T["gh"]["down"] = (dn, dn + 1.4)
        T["tick4"] = dn + 1.4
        dl = say(self, T["tick4"] + 0.8, LINES["groundhog"][1])
        T["card4"] = (T["tick4"] + 0.5, T["tick4"] + 0.8 + max(dl + 1.8, 9.0))
        # 4: the bear
        self.hans4 = DEN - 330.0
        P4 = self._place_row({"tentacles": self.hans4}, (0.0, DEN + 360.0))
        a = self._walk(R, P4, T["card4"][1] - 1.0)
        T["r_hint"] = a - 1.5
        dh = say(self, T["r_hint"], LINES["bear"][0])
        t = max(a, T["r_hint"] + dh) + 0.4
        T["lift"] = (t, t + 2.0)                                  # Hans lifts the branch out of the way
        T["bear"] = dict(walk=(t - 6.0, t + 8.0), into=(t + 8.4, t + 12.4))
        T["drop"] = (t + 13.2, t + 15.0)                          # and lets it down gently again
        T["tick5"] = t + 12.4
        dl = say(self, T["tick5"] + 0.8, LINES["bear"][1])
        T["card5"] = (T["tick5"] + 0.5, T["tick5"] + 0.8 + max(dl + 1.8, 9.0))
        # 5: the chickadee, the first snowflakes
        self.glo5 = FEEDER - 230.0
        P5 = self._place_row({"lantern": self.glo5}, (0.0, FEEDER + 190.0))
        a = self._walk(R, P5, T["card5"][1] - 1.0)
        T["k_hint"] = a - 2.0
        dh = say(self, T["k_hint"], LINES["chickadee"][0])
        t = max(a, T["k_hint"] + dh) + 0.5
        T["fly"] = (t, t + 1.6)
        T["seed"] = t + 2.4
        T["fluff"] = (t + 3.4, t + 5.0)
        T["tick6"] = t + 5.0
        dl = say(self, T["tick6"] + 0.8, LINES["chickadee"][1])
        T["card6"] = (T["tick6"] + 0.5, T["tick6"] + 0.8 + max(dl + 1.8, 9.0))
        T["snow"] = T["card6"][1] - 2.0
        T["finale"] = T["card6"][1] + 1.2
        df = say(self, T["finale"], FINALE)
        T["cheer"] = T["finale"] + df + 0.6
        self.dur = T["cheer"] + 7.0
        say(self, self._dur_base + 1.5, SIGNOFF)                  # over the end sign
        self.R = R
        self.P = [P0, P1, P2, P3, P4, P5]
        self.ticks = [T["tick%d" % i] for i in range(1, 7)]
        self.cards = [("chipmunk", T["card1"]), ("beaver", T["card2"]), ("goose", T["card3"]),
                      ("groundhog", T["card4"]), ("bear", T["card5"]), ("chickadee", T["card6"])]

    # ====================================================================== the sky (sunset -> night)

    def night_amount(self, t):
        T = self.T
        return smoothstep(seg(t, T["card1"][0], T["k_hint"]))

    def ready(self, t):
        return sum(1 for x in self.ticks if t >= x)

    # ====================================================================== the camera

    def target(self, t):
        T = self.T
        P = self.P
        k = []

        def wide(i, z=1.0):
            xs = [P[i][kd] for kd in O7]
            return ((min(xs) + max(xs)) / 2.0, None, z)
        k += [(-self.LEAD, *wide(0, 0.85)), (T["counter"] - 2.5, *wide(0, 0.85))]
        k += [(T["c_hint"] + 4.0, 1900.0, None, 1.15), (T["trips"][-1][1], 1960.0, None, 1.25),
              (T["chip"]["go"][1], PILE - 20, None, 1.7), (T["chip"]["down"][1], PILE - 40, None, 1.7),
              (T["card1"][1] - 1.5, 1950.0, None, 1.2)]
        k += [(T["b_hint"] + 2.0, CART2 + 300, None, 1.05), (T["trim"][0] + 0.5, CART2 + 120, None, 1.35),
              (T["trim"][3] + 1.5, CART2 + 120, None, 1.35), (T["bv"]["swim_in"][1], CART2 + 400, None, 1.1),
              (T["bv"]["swim_out"][1], LODGE - 250, None, 1.15), (T["card2"][1] - 1.5, LODGE - 250, None, 1.15)]
        k += [(T["g_hint"] + 2.0, HOLE3 - 120, None, 1.2), (T["sweep"][1], HOLE3 - 60, None, 1.45),
              (T["gh"]["up"][1] + 1.0, HOLE3 - 60, None, 1.45), (T["geese"][0] + 4.5, HOLE3 - 250, G - 470.0, 0.85),
              (T["geese"][1] - 2.0, HOLE3 - 350, G - 470.0, 0.85), (T["card3"][1] - 1.0, HOLE3 - 80, None, 1.4),
              (T["card4"][1] - 1.5, HOLE3 - 80, None, 1.4)]
        k += [(T["r_hint"] + 2.0, DEN + 50, None, 1.0), (T["lift"][1], DEN + 120, None, 1.05),
              (T["bear"]["into"][0], DEN - 30, None, 1.3), (T["card5"][1] - 1.5, DEN - 30, None, 1.3)]
        k += [(T["k_hint"] + 2.0, FEEDER + 100, None, 1.05), (T["fly"][1], FEEDER - 80, None, 1.6),
              (T["card6"][1] - 1.5, FEEDER - 80, None, 1.6), (T["cheer"] + 1.0, *wide(5, 0.8)),
              (self._dur_base, *wide(5, 0.76))]
        k.sort(key=lambda e: e[0])
        return cam_keys(k, t)

    # ====================================================================== the Keepers

    def update(self, t, dt):
        self.reach = {}
        T = self.T
        for kd in O7:
            m = self.m(kd)
            if m is None:
                continue
            x = self.R[kd].at(t)
            y, dy = (G - GLO_UP + 6 * math.sin(t * 1.3)) if kd == "lantern" else G, 0.0
            if kd == "springs":
                dy -= self._hop(t)
            if t >= T["cheer"]:
                dy -= 10 * bump(t, T["cheer"] + 0.3 * O7.index(kd), 0.5)
            self.place(m, x, t, dt, y=y, dy=dy)
            self.new_look(m, work_flash(kd, t, 2.0) + bump(t, T["cheer"] + 0.3 * O7.index(kd), 1.1), smile=0.65)
            m.dig, m.punch, m.punch_l = 0.0, 0.0, 0.0
            if kd == "teeth":
                m.saws, m.hands, m.bare = False, True, set()
                a, b, c_, d = T["trim"]
                m.blades = 0.0
                m.blades_l = smootherstep(seg(t, a, b)) * (1 - smootherstep(seg(t, d + 1.2, d + 2.0)))
                m.punch_l = 0.9 * smootherstep(seg(t, b, c_)) * (1 - smootherstep(seg(t, d + 0.2, d + 1.2)))
                if c_ <= t < d:
                    m.punch_l += 0.03 * math.sin((t - c_) * 2 * math.pi * 1.4)
            if kd == "sprout":
                m.acorn = self._sprout_has_acorn(t)
                m.hold_out = 0.0
                for pick, drop in T["trips"]:
                    m.hold_out = max(m.hold_out, smoothstep(seg(t, drop - 0.8, drop - 0.2)) *
                                     (1 - smoothstep(seg(t, drop + 0.4, drop + 1.0))))
                m.water = 0.0
            if kd == "digger":
                a, b = T["sweep"]
                if a <= t < b:
                    m.dig = 0.5 + 0.5 * math.sin((t - a) * 2 * math.pi * 0.7 - math.pi / 2)
            if kd == "lantern":
                m.lamp = 1.0
        self._hans(t)
        self._particles(t)
        self._sounds(t)

    def _hop(self, t):
        for ts, Td, a, b, r in self.R["springs"].legs:
            if ts <= t < ts + Td:
                n = max(1, int(round(abs(b - a) / 170.0)))
                ph = ((t - ts) / Td * n) % 1.0
                self.m("springs").spring = 0.6 if ph < 0.06 or ph > 0.94 else 0.0
                return 4 * 48 * ph * (1 - ph)
        g0, g1 = self.T["geese"]
        if g0 + 1.0 <= t < g1 - 1.0:                               # bounces up to watch the geese go over
            ph = ((t - g0 - 1.0) / 1.3) % 1.0
            return 4 * 90 * ph * (1 - ph)
        return 0.0

    def _sprout_has_acorn(self, t):
        for pick, drop in self.T["trips"]:
            if pick <= t < drop:
                return True
        return False

    def stump_count(self, t):
        return 4 - sum(1 for p, _ in self.T["trips"] if t >= p)

    def pile_count(self, t):
        dropped = sum(1 for _, d in self.T["trips"] if t >= d + 0.35)
        eaten = sum(1 for e in self.T["chip"]["eat"] if t >= e + 0.8)
        return dropped - eaten

    # ----- Hans and the low branch -----

    def branch_end(self, t):
        """The low branch across the den: its end hangs at the den's top, Hans lifts it up out of the bear's way and
        lets it down again afterwards."""
        a, b = self.T["lift"]
        u = smoothstep(seg(t, a, b)) * (1 - smoothstep(seg(t, *self.T["drop"])))
        return lerp(DEN + 150.0, DEN + 110.0, u), lerp(G - 250.0, G - 470.0, u), u

    def _hans(self, t):
        h = self.m("tentacles")
        if h is None:
            return
        a, b = self.T["lift"]
        d0, d1 = self.T["drop"]
        if a - 1.5 <= t < d1 + 1.0:
            ex, ey, _ = self.branch_end(t)
            reach = smoothstep(seg(t, a - 1.5, a)) * (1 - smoothstep(seg(t, d1, d1 + 1.0)))
            hx, hy = h.x + 80, G - 300 * h.k
            self.reach["tentacles"] = [(lerp(hx, ex, reach), lerp(hy, ey, reach))]

    # ====================================================================== the animals

    def chip_state(self, t):
        """(x, y, visible-above-ground clip y or None, pouch, nibble, face)."""
        C = self.T["chip"]
        s = ANIMAL_S["chipmunk"]
        pouch = sum(1.0 / 3 for e in C["eat"] if t >= e + 0.8)
        nib = sum(bump(t, e, 0.8) for e in C["eat"])
        if t < C["up"][0]:
            return None
        if t < C["up"][1]:
            return BURROW1, BACK + s * 0.7 * (1 - smoothstep(seg(t, *C["up"]))), BACK, pouch, nib, 1
        if t < C["go"][1]:
            u = seg(t, *C["go"])
            return lerp(BURROW1, PILE - 60.0, u), BACK - 30 * 4 * u * (1 - u), None, pouch, nib, 1
        if t < C["back"][0]:
            return PILE - 60.0, BACK, None, pouch, nib, 1
        if t < C["back"][1]:
            u = seg(t, *C["back"])
            return lerp(PILE - 60.0, BURROW1, u), BACK - 30 * 4 * u * (1 - u), None, pouch, nib, -1
        if t < C["down"][1]:
            return BURROW1, BACK + s * 0.7 * smoothstep(seg(t, *C["down"])), BACK, pouch, nib, -1
        return None

    def beaver_state(self, t):
        """(x, y, face, swimming, has branch, depth 0..1 under water). It turns round only while it is under water."""
        B = self.T["bv"]
        bx = self.bx2
        if t < B["swim_in"][0] - 0.8 or t >= B["dive"][1]:
            return None
        if t < B["swim_in"][1]:
            u = smoothstep(seg(t, *B["swim_in"]))
            return lerp(LODGE - 60, bx, u), G - 12, -1, True, False, 1 - smoothstep(seg(t, B["swim_in"][0] - 0.8,
                                                                                    B["swim_in"][0] + 0.6))
        if t < B["back"][0]:
            u = smoothstep(seg(t, *B["climb"]))
            return bx, lerp(G - 12, BACK, u), -1, u < 0.98, t >= B["take"][1], 0.0
        if t < B["under"][1]:
            u = smoothstep(seg(t, *B["back"]))
            w = smoothstep(seg(t, *B["under"]))
            return bx + 20 * w, lerp(BACK, G - 12, u), -1, True, True, w
        if t < B["up"][1]:
            return bx + 20, G - 12, 1, True, True, 1 - smoothstep(seg(t, *B["up"]))
        if t < B["swim_out"][1]:
            u = smoothstep(seg(t, *B["swim_out"]))
            return lerp(bx + 20, LODGE - 120, u), G - 12, 1, True, True, 0.0
        return LODGE - 120, G - 12, 1, True, True, smoothstep(seg(t, *B["dive"]))

    def gh_state(self, t):
        H = self.T["gh"]
        s = ANIMAL_S["groundhog"]
        if t < H["up"][0] or t >= H["down"][1]:
            return None
        if t < H["up"][1]:
            return HOLE3, BACK + s * 0.9 * (1 - smoothstep(seg(t, *H["up"])))
        if t < H["down"][0]:
            return HOLE3, BACK
        return HOLE3, BACK + s * 0.9 * smoothstep(seg(t, *H["down"]))

    def bear_state(self, t):
        """(x, y, walking, depth into the den 0..1)."""
        Bw = self.T["bear"]
        if t < Bw["walk"][0] or t >= Bw["into"][1] + 0.2:
            return None
        if t < Bw["walk"][1]:
            u = (t - Bw["walk"][0]) / (Bw["walk"][1] - Bw["walk"][0])
            u = u * u * (3 - 2 * u) * 0.25 + u * 0.75
            return lerp(DEN + 1100.0, DEN + 60.0, u), BACK, True, 0.0
        return DEN + 60.0 - 40.0 * seg(t, *Bw["into"]), BACK, True, smoothstep(seg(t, *Bw["into"]))

    def dee_state(self, t):
        """The chickadee: on its twig in the tree, a hop-flight to the feeder, a seed, fluffed up. -> (x, y, fluff,
        seed, flying)."""
        T = self.T
        a, b = T["fly"]
        p0, p1 = (FEEDER + 200.0, G - 430.0), (FEEDER + 30.0, G - 312.0)
        fl = smoothstep(seg(t, *T["fluff"]))
        sd = 1.0 if T["seed"] <= t < T["fluff"][0] + 0.4 else 0.0
        if t < a:
            return p0[0], p0[1], 0.0, 0.0, False
        if t < b:
            u = smoothstep(seg(t, a, b))
            return lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u) - 50 * math.sin(math.pi * u), 0.0, 0.0, True
        return p1[0], p1[1], fl, sd, False

    def props(self, t):
        out = {}
        cs = self.chip_state(t)
        if cs is not None:
            out["chipmunk"] = cs[:2]
        bs = self.beaver_state(t)
        if bs is not None:
            out["beaver"] = bs[:2]
        rs = self.bear_state(t)
        if rs is not None:
            out["bear"] = rs[:2]
        ex, ey, _ = self.branch_end(t)
        out["low_branch"] = (ex, ey)
        return out

    # ====================================================================== talking, sounds, particles

    def aside_moods(self, t):
        if speaking(self, t, 1.0):
            return []
        if any(a - 0.5 < t < b for _, (a, b) in self.cards):
            return []
        return ["mm", "ooh", "hehe", "aww"]

    def _chat(self, at, kind, mood, **kw):
        if self.crossed(at) and not speaking(self, at, 0.4):
            self.chat(at, kind, mood, **kw)

    def _sounds(self, t):
        T = self.T
        for pick, drop in T["trips"]:
            if self.crossed(drop + 0.35):
                self.hit(drop + 0.35, "pluck", 64, 0.1, PILE, BACK)
        C = T["chip"]
        for e in C["eat"]:
            if self.crossed(e):
                self.hit(e, "pluck", 72, 0.06, PILE - 60, BACK)
        self._chat(C["up"][1] + 0.4, "sprout", "ooh", icon="sparkle")
        a, b, c_, d = T["trim"]
        if self.crossed(c_):
            self.fx(c_, "saw", d - c_, 0.06, *self.cut2)
        if self.crossed(d + 0.4):
            self.hit(d + 0.4, "thud", 52, 0.12, CART2, G - 50)
        self._chat(d + 1.2, "teeth", "hehe", icon="smile")
        B = T["bv"]
        if self.crossed(B["swim_in"][0]):
            self.fx(B["swim_in"][0], "rustle", B["swim_in"][1] - B["swim_in"][0], 0.05, LODGE, WATER_Y)
        if self.crossed(B["dive"][0] + 0.3):
            self.fx(B["dive"][0] + 0.3, "splash", 0.6, 0.08, LODGE - 120, WATER_Y)
        self._chat(B["take"][0] + 0.2, "wheels", "ooh")
        if self.crossed(T["sweep"][0]):
            self.fx(T["sweep"][0], "rustle", T["sweep"][1] - T["sweep"][0], 0.1, HOLE3, BACK)
        self._chat(T["gh"]["up"][1] + 0.3, "digger", "aww", icon="heart")
        g0, g1 = T["geese"]
        for q in range(9):                                        # distant honks as they go over
            tq = g0 + 0.8 + q * 1.3
            if tq < g1 and self.crossed(tq):
                self.hit(tq, "sky_swell", 64 + (q % 3) * 3, 0.05, HOLE3, G - 600)
        self._chat(g0 + 2.0, "springs", "wee")
        a, b = T["lift"]
        self._chat(a - 1.0, "tentacles", "hm")
        if self.crossed(a):
            self.fx(a, "rustle", b - a, 0.08, DEN + 120, G - 300)
        self._chat(T["bear"]["into"][1] + 0.3, "tentacles", "aww", icon="heart")
        if self.crossed(T["seed"]):
            self.hit(T["seed"], "pluck", 79, 0.06, FEEDER, G - 300)
        self._chat(T["fluff"][1] + 0.3, "lantern", "aww", icon="heart")
        for i, x in enumerate(self.ticks):
            if self.crossed(x):
                self.hit(x, "warm_bell", 72 + (i % 3) * 2, 0.13, self.s.cam_x + 300, G - 400)
                self.hit(x + 0.22, "warm_bell", 79, 0.11, self.s.cam_x + 300, G - 400)
        if self.crossed(T["cheer"]):
            self.chorus(T["cheer"], O7, "yay", gap=0.28)

    def _particles(self, t):
        p = self.s.particles
        T = self.T
        vx0, vx1, vy0, _ = self.s.view()
        if t < T["k_hint"] and p.rng.uniform() < 0.06 * (1 - self.night_amount(t)):    # autumn leaves drifting down
            col = (GOLD, ORANGE, RED)[int(p.rng.integers(3))]
            p.burst(p.rng.uniform(vx0, vx1), vy0 - 40, 1, col * 0.8, 60, 7.0, 7, g=60, spread=1.2)
        if T["snow"] <= t:                                        # the very first snowflakes
            rate = 0.32 * smoothstep(seg(t, T["snow"], T["snow"] + 5.0))
            if p.rng.uniform() < rate:
                p.burst(p.rng.uniform(vx0 - 100, vx1 + 100), vy0 - 30, 1, SNOWC, 30, 9.0, 4.0, g=40, spread=1.0)
        a, b = T["sweep"]
        if a <= t < b and p.rng.uniform() < 0.3:                  # old leaves swept out of the door
            col = (GOLD, ORANGE, RED)[int(p.rng.integers(3))] * 0.7
            p.burst(HOLE3 - 20, BACK - 8, 1, col, 160, 0.9, 6, g=700, spread=0.5, direction=-math.pi * 0.25)
        a, b, c_, d = T["trim"]
        if c_ <= t < d and p.rng.uniform() < 0.6:
            p.burst(self.cut2[0], self.cut2[1] + 4, 1, np.array([214, 184, 140]), 140, 0.8, 3.5, g=600, spread=1.0,
                    direction=math.pi / 2)

    # ====================================================================== drawing

    def draw(self, c, t):
        s = self.s
        self._sky(c, t)
        self._far(c, t)
        self._ground(c, t)
        self._places(c, t)
        self._animals_back(c, t)
        self._cart(c, t)
        lg = self.m("lantern")
        if lg is not None and "lantern" in self.poses:
            self.lantern_light(c, lg.x, lg.y - 120, k=0.4 + 0.6 * self.night_amount(t))
        self.draw_monsters(c, t)
        self._front(c, t)
        del s

    def _sky(self, c, t):
        s = self.s
        n = self.night_amount(t)
        vx0, vx1, vy0, vy1 = s.view()
        stops = [  # top, middle, low (sunset -> night)
            (np.array([46, 54, 96.0]), np.array([150, 104, 120.0]), np.array([246, 172, 110.0])),
            (np.array([10, 14, 32.0]), np.array([22, 30, 58.0]), np.array([36, 46, 74.0]))]
        top = stops[0][0] * (1 - n) + stops[1][0] * n
        mid = stops[0][1] * (1 - n) + stops[1][1] * n
        low = stops[0][2] * (1 - n) + stops[1][2] * n
        y0, y1 = vy0 - 50, G
        steps = 24
        for i in range(steps):
            a, b = lerp(y0, y1, i / steps), lerp(y0, y1, (i + 1) / steps)
            q = (i + 0.5) / steps
            col = top + (mid - top) * min(1, q / 0.6) if q < 0.6 else mid + (low - mid) * ((q - 0.6) / 0.4)
            rect(c, vx0 - 50, a, vx1 + 50, b + 1, col)
        # the sun going down (fixed on the screen, sinking), then the stars
        sun = 1 - smoothstep(seg(t, -self.LEAD, self.T["card2"][1]))
        if sun > 0.01:
            sx = s.cam_x + s.w * 0.62 / max(s.zoom, 0.1) if False else (vx0 + vx1) / 2 + (vx1 - vx0) * 0.12
            sy = G - 120 - 260 * sun
            c.circle(sx, sy, 70, np.array([255, 214, 150.0]) * (0.75 + 0.25 * sun))
        if n > 0.3:
            rs = np.random.default_rng(31)
            w = vx1 - vx0
            for _ in range(70):
                x = vx0 + rs.uniform(0, 1) * w
                y = vy0 + rs.uniform(0, 1) * (G - 400 - vy0)
                c.circle(x, y, rs.uniform(1.0, 2.0) / max(s.zoom, 0.5), np.array([220, 226, 240]) * rs.uniform(0.4, 0.9) *
                         smoothstep((n - 0.3) / 0.5))

    def _far(self, c, t):
        """The far tree line (autumn colours dimming into the night), fixed in the world."""
        s = self.s
        n = self.night_amount(t)
        dim = 1.0 - 0.58 * n
        far = np.array([92, 70, 88.0]) * (1 - n) + np.array([22, 30, 42.0]) * n
        vx0, vx1 = s.view()[:2]
        rs = np.random.default_rng(5)
        xs = np.arange(-1000.0, 11500.0, 70.0)
        hs = rs.uniform(220, 360, len(xs))
        for x, hh in zip(xs, hs):
            if vx0 - 200 < x < vx1 + 200:
                c.circle(x, G - 40 - hh * 0.62, hh * 0.3, far)
                c.polygon([(x - 8, G - 40), (x + 8, G - 40), (x + 6, G - 40 - hh * 0.5), (x - 6, G - 40 - hh * 0.5)], far)
        for j, tx in enumerate((900.0, 2400.0, 2750.0, 4800.0, 6300.0, 6950.0, 8400.0, 9250.0, 10200.0)):
            if not (vx0 - 400 < tx < vx1 + 400):
                continue
            th = 900 + 80 * (j % 3)
            c.polygon([(tx - 40, BACK), (tx + 40, BACK), (tx + 26, BACK - th * 0.6), (tx - 26, BACK - th * 0.6)], TRUNK * dim)
            for q in range(9):
                a = q * 0.7
                col = (GOLD, ORANGE, RED)[(q + j) % 3] * (0.78 + 0.05 * (q % 3)) * dim
                c.circle(tx + 160 * math.cos(a) * (q % 3) / 2, BACK - th * 0.72 + 110 * math.sin(a), 140 + 26 * (q % 2), col)

    def _ground(self, c, t):
        s = self.s
        n = self.night_amount(t)
        dim = 1.0 - 0.58 * n
        vx0, vx1, _, vy1 = s.view()
        bank = np.array([92, 66, 46.0]) * dim
        rect(c, vx0 - 50, G - 44, vx1 + 50, vy1 + 50, bank * 0.92)
        # the pond, behind the path
        if vx0 - 100 < POND[1] and POND[0] < vx1 + 100:
            pts = [(POND[0], WATER_Y + 4), (POND[0] + 40, WATER_Y - 6), (POND[1] - 40, WATER_Y - 6), (POND[1], WATER_Y + 4),
                   (POND[1] - 30, G - 14), (POND[0] + 30, G - 14)]
            c.polygon(pts, POND_C * dim)
            for q in range(4):
                xx = POND[0] + 120 + q * 290 + 30 * math.sin(t * 0.6 + q)
                c.line(xx, WATER_Y + 6 + (q % 2) * 8, xx + 120, WATER_Y + 6 + (q % 2) * 8, POND_C * dim * 1.35, 2)
        rect(c, vx0 - 50, G - 10, vx1 + 50, vy1 + 50, np.array([92, 66, 46.0]) * dim)       # the path
        c.line(vx0 - 50, G - 10, vx1 + 50, G - 10, np.array([92, 66, 46.0]) * dim * 1.25, 3)
        rs = np.random.default_rng(17)
        for x in np.arange(math.floor(vx0 / 60) * 60, vx1 + 60, 60):
            r_ = np.random.default_rng(int(x) % 100003 + 7)
            lx, ly = x + r_.uniform(0, 60), G + r_.uniform(0, 160)
            col = (GOLD, ORANGE, RED)[int(r_.integers(3))] * r_.uniform(0.6, 0.85) * dim
            c.polygon(F(lx, ly, 13).pts([(0, 0), (0.6, 0.35), (1.2, 0), (0.6, -0.35)]), col)
        del rs

    def _places(self, c, t):
        """Burrows, the stump and its acorns, the fallen tree, the lodge, the den, the feeder (all behind the path)."""
        s = self.s
        T = self.T
        n = self.night_amount(t)
        dim = 1.0 - 0.5 * n
        # 1: the chipmunk's burrow, its pile, the stump with acorns
        if s.visible(BURROW1 - 300, STUMP + 200):
            c.polygon(F(BURROW1, BACK + 2, 1).pts([(-110, 0), (-70, 34), (0, 46), (80, 34), (120, 0)]), SOIL * dim)
            c.polygon(ellipse(BURROW1, BACK + 2, 38, 12, 20), np.array([30, 22, 18.0]))
            sx, top = STUMP, G - 126 * self.mk + 9
            rect(c, sx - 52, top, sx + 52, BACK + 4, BARKC * dim)
            c.polygon(ellipse(sx, top, 52, 10, 24), lighten(BARKC, 1.5) * dim)
            n_ = self.stump_count(t)
            for q in range(n_):                                   # the last one is right under Sprout's hand
                j = n_ - 1 - q
                acorn_nut(c, sx - 6 * self.mk + 22 * j, top - 9 - (j % 2) * 4, 10.0)
            for q in range(self.pile_count(t)):
                acorn_nut(c, PILE + (q % 2) * 20 - 10 * (q // 2), BACK - 9 - (q // 2) * 14, 10.0)
            for pick, drop in T["trips"]:                         # the acorn falling from Sprout's hand
                if drop <= t < drop + 0.35:
                    sp = self.m("sprout")
                    x0, y0 = sp.x + self.drop_dx, G + self.drop_y
                    acorn_nut(c, x0, min(fall(y0, t - drop), BACK - 9), 10.0)
        # 2: the fallen tree with its dead branch, the lodge
        if s.visible(2700, POND[1] + 200):
            cx, cy = self.cut2
            c.polygon([(2760, BACK + 4), (CART2 + 100, BACK - 120), (CART2 + 120, BACK - 96), (2780, BACK + 30)], TRUNK * dim)
            c.circle(CART2 + 110, BACK - 108, 16, lighten(TRUNK, 1.3) * dim)
            c.line(CART2 - 40, BACK - 90, cx, cy, BARKC * dim, 12)            # the side branch up to the cut
            if t >= T["trim"][3]:
                c.circle(cx, cy, 5, lighten(np.array([132, 96, 62.0]), 1.3))
            lp = [(LODGE - 160, WATER_Y + 4), (LODGE - 110, WATER_Y - 80), (LODGE - 20, WATER_Y - 126),
                  (LODGE + 80, WATER_Y - 112), (LODGE + 150, WATER_Y - 40), (LODGE + 180, WATER_Y + 4)]
            c.polygon(lp, np.array([98, 72, 50.0]) * dim)
            for q in range(12):
                x0 = LODGE - 140 + (q * 47) % 300
                y0 = WATER_Y - (q * 31) % 110
                c.line(x0, y0, x0 + 70, y0 - 18 + (q % 3) * 12, np.array([70, 50, 36.0]) * dim, 7)
            B = T["bv"]
            if t >= B["dive"][0] + 1.0:                          # the branch it pushed into the mud, its end showing
                c.line(LODGE - 150, WATER_Y + 2, LODGE - 120, WATER_Y - 40, np.array([110, 82, 56.0]) * dim, 6)
        # 3: the groundhog's burrow, the old leaves in its door
        if s.visible(HOLE3 - 300, HOLE3 + 300):
            c.polygon(F(HOLE3, BACK + 2, 1).pts([(-170, 0), (-110, 52), (0, 80), (110, 52), (180, 0)]), SOIL * dim)
            c.polygon(ellipse(HOLE3, BACK, 52, 18, 22), np.array([30, 22, 18.0]))
            a, b = T["sweep"]
            left = 1 - smoothstep(seg(t, a, b))
            for q in range(int(round(8 * left))):
                c.polygon(F(HOLE3 - 40 + q * 11, BACK - 2 - (q % 3) * 5, 15).pts([(0, 0), (0.6, 0.35), (1.2, 0), (0.6, -0.35)]),
                          (GOLD, ORANGE, RED)[q % 3] * 0.7 * dim)
            for q in range(int(round(8 * (1 - left)))):           # the swept-out leaves in a heap by the door
                c.polygon(F(HOLE3 + 90 + q * 9, BACK + 4 - (q % 3) * 6, 15).pts([(0, 0), (0.6, 0.35), (1.2, 0), (0.6, -0.35)]),
                          (GOLD, ORANGE, RED)[q % 3] * 0.7 * dim)
        # 4: the rocky bank, the den, the tree and its low branch
        if s.visible(DEN - 700, DEN + 700):
            bank = [(DEN - 520, BACK + 6), (DEN - 380, BACK - 200), (DEN - 120, BACK - 290), (DEN + 200, BACK - 280),
                    (DEN + 480, BACK - 160), (DEN + 600, BACK + 6)]
            c.polygon(bank, ROCK * dim)
            c.polygon([(DEN - 380, BACK - 200), (DEN - 120, BACK - 290), (DEN + 200, BACK - 280), (DEN + 120, BACK - 250),
                       (DEN - 120, BACK - 262)], ROCK * 1.2 * dim)
            c.polygon(self.den_mouth(), np.array([16, 12, 16.0]))
            tx = DEN - 260.0
            c.polygon([(tx - 30, BACK), (tx + 30, BACK), (tx + 20, BACK - 600), (tx - 20, BACK - 600)], TRUNK * dim)
        # 5: the feeder on its post
        if s.visible(FEEDER - 300, FEEDER + 300):
            FX = FEEDER
            c.line(FX, BACK + 4, FX, G - 300, TRUNK * 0.8 * dim, 14)
            c.polygon([(FX - 110, G - 300), (FX + 110, G - 300), (FX + 100, G - 282), (FX - 100, G - 282)], np.array([120, 86, 56.0]) * dim)
            c.polygon([(FX - 130, G - 390), (FX, G - 440), (FX + 130, G - 390), (FX + 120, G - 380), (FX, G - 426),
                       (FX - 120, G - 380)], np.array([100, 70, 46.0]) * dim)
            for q in (-1, 1):
                c.line(FX + q * 96, G - 390, FX + q * 96, G - 300, np.array([100, 70, 46.0]) * dim, 7)
            c.line(9215, G - 432, 9160, G - 426, TRUNK * 0.9 * dim, 6)        # the chickadee's twig
            eaten = 1 if t >= self.T["seed"] else 0
            for q in range(14 - eaten):
                c.circle(FX - 80 + (q * 37) % 160, G - 306 - (q % 3) * 4, 4, np.array([214, 190, 140.0]) * dim)

    def den_mouth(self):
        return F(DEN, BACK + 4, 1).pts([(-150, 0), (-120, 120), (0, 175), (120, 120), (150, 0)])

    def _animals_back(self, c, t):
        s = self.s
        T = self.T
        cs = self.chip_state(t)
        if cs is not None:
            x, y, clip, pouch, nib, face = cs
            draw = lambda: draw_winter(c, "chipmunk", x, y, ANIMAL_S["chipmunk"], t, face=face, pouch=pouch, nibble=nib,
                                       blink=bump(t % 3.7, 0.0, 0.2))
            if clip is not None:
                fade_clip(c, s.glow, [(x - 200, clip - 400), (x + 200, clip - 400), (x + 200, clip), (x - 200, clip)], draw)
            else:
                draw()
        bs = self.beaver_state(t)
        Bt = T["bv"]
        sB = ANIMAL_S["beaver"]
        if bs is not None:
            x, y, face, swim, has, depth = bs
            yy = y + sB * 0.5 * depth
            draw = lambda: draw_winter(c, "beaver", x, yy, sB, t, face=face, walk=0.0 if swim else 0.0, branch=1.0 if has else 0.0,
                                       blink=bump(t % 4.1, 0.0, 0.2))
            if swim:
                wy = WATER_Y + 2 * math.sin(t * 2.0)
                fade_clip(c, s.glow, [(x - 300, wy - 400), (x + 300, wy - 400), (x + 300, wy), (x - 300, wy)], draw)
                c.polyline(ellipse(x + face * sB * 0.2, wy + 2, sB * 0.55, 6, 24), POND_C * 1.5, 2, closed=True)
            else:
                draw()
            if Bt["take"][0] <= t < Bt["take"][1]:              # lifting the branch out of the cart to its teeth
                u = smoothstep(seg(t, *Bt["take"]))
                beaver_branch(c, x, BACK, sB, -1, dv=lerp(self._cart_dv(), 0.0, u))
        rs = self.bear_state(t)
        if rs is not None:
            x, y, walking, depth = rs
            sR = ANIMAL_S["bear"] * (1 - 0.25 * depth)
            gait = (DEN + 1100.0 - x) / 90.0
            draw = lambda: draw_winter(c, "bear", x, y - 18 * depth, sR, t, face=-1, walk=1.0, gait=gait)
            if depth > 0:
                fade_clip(c, s.glow, self.den_mouth(), draw, shade=1 - 0.75 * depth, vis=1 - 0.85 * depth)
            else:
                draw()
        # the low branch across the den (in front of the den, behind the path)
        if s.visible(DEN - 600, DEN + 600):
            ex, ey, _ = self.branch_end(t)
            dim = 1.0 - 0.5 * self.night_amount(t)
            c.line(DEN - 260, BACK - 420, ex, ey, BARKC * dim, 12)
            for q in range(4):
                lx, ly = lerp(DEN - 200, ex, 0.3 + 0.2 * q), lerp(BACK - 400, ey, 0.3 + 0.2 * q)
                for j in range(3):
                    c.polygon(F(lx + j * 18, ly + 12 + (j % 2) * 10, 16).pts([(0, 0), (0.6, 0.35), (1.2, 0), (0.6, -0.35)]),
                              (GOLD, ORANGE, RED)[(q + j) % 3] * 0.65 * dim)
        gh = self.gh_state(t)
        if gh is not None:
            x, y = gh
            sit = 1.0
            fade_clip(c, s.glow, [(x - 220, BACK - 400), (x + 220, BACK - 400), (x + 220, BACK + 2), (x - 220, BACK + 2)],
                      lambda: draw_winter(c, "groundhog", x, y, ANIMAL_S["groundhog"], t, face=-1, sit=sit,
                                          blink=bump(t % 4.4, 0.0, 0.2)))
        dx, dy, fl, sd, flying = self.dee_state(t)
        if s.visible(dx - 100, dx + 100):
            if flying:
                draw_winter(c, "chickadee", dx, dy, ANIMAL_S["chickadee"], t, face=-1, hop=(t * 6) % 1)
            else:
                draw_winter(c, "chickadee", dx, dy, ANIMAL_S["chickadee"], t, face=-1, fluff=fl, seed=sd,
                            blink=bump(t % 3.3, 0.0, 0.2))
        g0, g1 = T["geese"]
        if g0 <= t < g1:
            u = (t - g0) / (g1 - g0)
            x0 = lerp(HOLE3 + 1300, HOLE3 - 1500, u)
            for kq, (gx, gy) in enumerate([(0, 30), (70, 0), (140, -30), (70, 65), (140, 100), (210, 135)]):
                draw_winter(c, "goose", x0 + gx, G - 640 + gy, ANIMAL_S["goose"], t, face=-1, fly=1.0,
                            flap=(t * 1.4 + 0.17 * kq) % 1)

    def _cart_dv(self):
        """The branch lying in the cart, in the beaver's frame (v units above where it carries it)."""
        return (BACK - (G - 66.0)) / ANIMAL_S["beaver"] - 0.26

    def _tree_dv(self):
        return (BACK - self.cut2[1]) / ANIMAL_S["beaver"] - 0.26

    def _cart(self, c, t):
        """Wheels' little cart, pushed in front of him; the branch Twigs cut lies in it until the beaver takes it."""
        w = self.m("wheels")
        if w is None or "wheels" not in self.poses:
            return
        x = w.x + PUSH
        if not self.s.visible(x - 200, x + 200):
            return
        dim = 1.0 - 0.4 * self.night_amount(t)
        rot = w.wheel_rot * 2.0
        for wx in (x - 70, x + 70):
            c.circle(wx, G - 20, 20, CARTW * 0.55 * dim)
            c.circle(wx, G - 20, 7, STEEL * dim)
            for i in range(4):
                a = rot + i * math.pi / 2
                c.line(wx, G - 20, wx + 15 * math.cos(a), G - 20 + 15 * math.sin(a), CARTW * 0.45 * dim, 3)
        rect(c, x - 100, G - 62, x + 100, G - 34, CARTW * dim)
        c.line(x - 100, G - 62, x + 100, G - 62, lighten(CARTW, 1.25) * dim, 3)
        c.line(x - 100, G - 50, w.x + 40, G - 120, CARTW * 0.8 * dim, 6)         # the push handle
        self._piece(c, t)

    def _piece(self, c, t):
        """The dead end of the fallen tree's branch: on the tree, cut off and dropping into the cart, lying there
        until the beaver lifts it out (always the same leafy shape, in the beaver's frame by the cart)."""
        T = self.T
        Bt = T["bv"]
        d = T["trim"][3]
        sB = ANIMAL_S["beaver"]
        if t >= Bt["take"][0]:
            return
        if t < d:
            dv = self._tree_dv()
        else:
            h = (self._tree_dv() - self._cart_dv()) * sB
            land = math.sqrt(2 * h / GRAVITY)
            dv = self._tree_dv() - min(0.5 * GRAVITY * (t - d) ** 2, h) / sB
        beaver_branch(c, self.bx2, BACK, sB, -1, dv=dv)

    def _front(self, c, t):
        pass

    # ====================================================================== on screen: the counter and the cards

    def screen(self, cv, ts):
        t = ts / self.STRETCH - self.LEAD
        T = self.T
        if t >= T["counter"]:
            a = smoothstep(seg(t, T["counter"], T["counter"] + 0.8))
            n = self.ready(t)
            hi = max((bump(t, x, 0.8) for x in self.ticks), default=0.0)
            g = self.s.glow.layer
            k = cv.s
            g[int(36 * k):int(104 * k) + 1, int(40 * k):int(520 * k) + 1] = 0
            bg = cv.target.copy() if a < 0.999 else None
            cv.polygon([(40, 36), (520, 36), (520, 104), (40, 104)], WOOD * 0.8)
            cv.polyline([(40, 36), (520, 36), (520, 104), (40, 104)], WOOD * 0.5, 4, closed=True)
            cv.text(f"READY FOR WINTER  {n} / 6", 280, 70, 30,
                    PAPER * (1 - 0.25 * hi) + np.array([255, 220, 120]) * 0.25 * hi)
            if bg is not None:
                cv.target[:] = (bg * (1 - a) + cv.target * a).astype(np.uint8)
        for kind, (a0, a1) in self.cards:
            if a0 <= t < a1 + 0.8:
                a = smoothstep(seg(t, a0, a0 + 0.7)) * (1 - smoothstep(seg(t, a1, a1 + 0.7)))
                self._card(cv, a, kind, t)

    def _card(self, cv, a, kind, t):
        if a <= 0.01:
            return
        W, H = 1240, 210
        x0, y0 = 960 - W // 2, 1080 - 30 - H
        x1, y1 = x0 + W, y0 + H
        bg = cv.target.copy() if a < 0.999 else None
        g = self.s.glow.layer
        k = cv.s
        g[max(0, int(y0 * k)):int(y1 * k) + 1, max(0, int(x0 * k)):int(x1 * k) + 1] = 0
        cv.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], WOOD * 0.75)
        cv.polygon([(x0 + 8, y0 + 8), (x1 - 8, y0 + 8), (x1 - 8, y1 - 8), (x0 + 8, y1 - 8)], CARD)
        pic = (x0 + 24, y0 + 20, x0 + 214, y1 - 20)
        cv.polygon([(pic[0], pic[1]), (pic[2], pic[1]), (pic[2], pic[3]), (pic[0], pic[3])], np.array([226, 230, 214]))
        s_ = {"chipmunk": 190, "beaver": 150, "goose": 70, "groundhog": 160, "bear": 140, "chickadee": 190}[kind]
        kw = {"chipmunk": dict(pouch=1.0), "goose": dict(fly=1.0, flap=0.3), "chickadee": dict(fluff=1.0),
              "bear": dict(walk=1.0, gait=0.4)}.get(kind, {})
        px_ = (pic[0] + pic[2]) / 2 - (10 if kind != "goose" else -60)
        py_ = pic[3] - 6 - (40 if kind == "goose" else 0)
        clipped(cv, self.s.glow, pic, lambda cc: draw_winter(cc, kind, px_, py_, s_, 0.0, face=1 if kind != "goose" else -1, **kw))
        cx = (x0 + 240 + x1 - 40) // 2
        d = WINTER[kind]
        cv.text(d["name"], cx, y0 + H // 2 - 52, 58 if len(d["name"]) > 16 else 62, INK)
        for q, ln in enumerate(d["line"]):
            cv.text(ln, cx, y0 + H // 2 + 14 + q * 42, 34, INK * 1.25)
        if bg is not None:
            cv.target[:] = (bg * (1 - a) + cv.target * a).astype(np.uint8)
