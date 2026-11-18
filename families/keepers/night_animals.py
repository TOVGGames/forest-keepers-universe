"""Forest Keepers episode 11: Who's Awake Tonight? (docs/engines/forest_keepers_night_animals.md), 16:9, ~7 min.

The animals of the forest at night, and the first narrated episode (owner, 2026-11-01): a gentle grandmother narrator
(narrator.py, Johanna) gives hints of what the Keepers are up to and reads each animal's line; the Keepers keep their
own cute noises. The animals are drawn in code to field-guide accuracy (animals.py). One act, one night walk, no cuts:

  OPEN   the name tags while the narrator sets the scene; Wheels pushes the Keeper Field Guide over, Glo's light
         opens it on the checklist: six "?" frames. "WHO'S AWAKE TONIGHT?"
  FINDS  six neighbours, one spotted by each Keeper: Hans sees ripples in the stream (a raccoon washing its food),
         Twigs hears a hoot up in the oak (a barred owl), Glo turns her light down low by the old log (an opossum
         with her babies on her back), Springs bounces up and sees something leap from a treetop (a flying squirrel
         gliding to the next tree), Wheels stops still in the meadow (a red fox listening), Digs finds the forest's
         edge (a white-tailed deer and her fawn). Each: the narrator's hint, a slow close-up, the guide's pages turn
         to the match and the box is ticked, the name card while the narrator reads its line, the animal goes on
         its way, the camera pulls back and the walk goes on.
  END    the checklist full, "All six found!", fireflies, goodnight; the end sign, where the narrator asks what the
         Keepers should do next.
"""
import math

import numpy as np

from families.foundry.keepers.common import Night, ellipse, lerp, rect, seg, smoothstep, smootherstep, tree
from families.foundry.keepers.forest import _firefly
from families.foundry.products.monster import lighten
from families.foundry.tree_monsters import LEAF as TREE_LEAF

from .animal_houses import G
from .animals import ANIMALS, draw_animal
from .bug_hunt import (BOOK_Y, CARD, COVER, INK, PAPER, PAPER_DARK, PUSH, TICK, WOOD, closed_book, draw_cart,
                       page_lines)
from .book import check_art, clipped, fit
from .doorway import fade_clip, half_width
from .harvest_feast import cam_keys
from .narrator import say, speaking
from .tune_up import GLO_UP, ORDER, Route, TuneAct, bump, work_flash

WATER = np.array([46, 70, 96], np.float64)
BARK_C = np.array([82, 60, 44], np.float64)
MEADOW = np.array([58, 82, 52], np.float64)
BOOK_DX = -600.0                                    # the cart stops this far short of the animal
RIGHT = {"raccoon": 90.0, "owl": 260.0, "opossum": 260.0, "squirrel": 300.0, "fox": 120.0, "deer": 420.0}
TOP = {"raccoon": G - 160.0, "owl": G - 720.0, "opossum": G - 200.0, "squirrel": G - 700.0, "fox": G - 260.0,
       "deer": G - 340.0}

# the narrator's script (owner: hints of what the Keepers are up to; lines checked; nothing about how anything began)
# owner after the first render: she may talk a little less and slower, never more (to relax to, not to rush)
OPEN = "The moon is up, and the forest is quiet. Tonight, the Keepers are going to meet the neighbours who stay up late."
GUIDE = None
FINDS = [
    dict(kind="raccoon", finder="tentacles", x=2000.0, s=118.0, zoom=2.5,
         hint="Hans has spotted little ripples on the pond...",
         line="A raccoon. Its little hands are so sensitive, it can feel its food without even looking."),
    dict(kind="owl", finder="teeth", x=3700.0, s=150.0, zoom=2.2,
         hint="Twigs hears something, high in the old oak. Who... who's there?",
         line="A barred owl. It calls, who cooks for you? And it flies almost without a sound."),
    dict(kind="opossum", finder="lantern", x=5400.0, s=105.0, zoom=2.2,
         hint="Glo turns her light down low, so she won't startle anyone.",
         line="An opossum, with her babies riding on her back. She's North America's only marsupial."),
    dict(kind="squirrel", finder="springs", x=7100.0, s=120.0, zoom=2.4,
         hint="Springs bounces up for a better look. Something is up in that tree...",
         line="A flying squirrel. It doesn't really fly... it glides, on a furry skin between its legs."),
    dict(kind="fox", finder="wheels", x=8800.0, s=150.0, zoom=2.0,
         hint="Out in the meadow, Wheels stops, very still.",
         line="A red fox. Its big ears can hear a mouse squeak, under the leaves."),
    dict(kind="deer", finder="digger", x=10500.0, s=250.0, zoom=1.6,
         hint="At the edge of the forest... shh. Slowly now.",
         line="A white-tailed deer, and her fawn. Her white tail is a little flag that says: watch out."),
]
FINALE = "Six night-time neighbours, all found. Goodnight, forest."
SIGNOFF = "What should the Keepers do next? Tell us in the comments."
OWL_BRANCH = G - 520.0
TREE_A, TREE_B = 6870.0, 7330.0                    # the flying squirrel glides from A to B
LOG = (5200.0, 5640.0)                              # the opossum's log
STREAM = (1560.0, 2560.0)
# bushes in the foreground: an animal that goes on its way slips behind one, out of the Keepers' path
HIDE = {"raccoon": 2800.0, "opossum": 5990.0, "fox": 9640.0}


class NightAct(TuneAct):
    """The whole night walk."""
    name = "night"
    LEAD = 8.0
    names = (0.8 - LEAD, 7.0 - LEAD)
    cam_snap = True

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.night = Night(np.random.default_rng(scene.seed + 101), G, -1500, 13000)
        for m in scene.monsters:
            m.job = "keeper"
        self._plan()
        spills = check_art(self.book_art())
        if spills:
            print(f"  WARNING: {len(spills)} pictures reach past the edge of their page / frame / card: {spills}. "
                  f"Everything in the book stays in the book (book.py).", flush=True)
        self.stats = {"animals": [f["kind"] for f in FINDS], "narrator_lines": len(self.lines),
                      "page_spills": len(spills)}

    # ----- the timeline (built around the narrator's lines) -----

    def _slots(self, f):
        """Where everyone stands at a find: the finder between the guide and the animal, Wheels behind the cart,
        the others behind him (nobody walks past a wild animal)."""
        x = f["x"]
        fk = f["finder"]
        pos = {"wheels": x + BOOK_DX - PUSH}
        if fk == "lantern":
            pos["lantern"] = x - 230.0
        elif fk != "wheels":
            pos[fk] = x - (150.0 if f["kind"] in ("owl", "squirrel") else 250.0)
        edge = pos["wheels"] - self._hw("wheels") - 30.0
        for k in ["lantern", "springs", "teeth", "digger", "tentacles"]:
            if k in pos:
                continue
            pos[k] = edge - self._hw(k)
            edge = pos[k] - self._hw(k) - 30.0
        return pos

    def _hw(self, kind):
        m = self.m(kind)
        return half_width(m) if m is not None else 150.0

    def _plan(self):
        self.lines = []
        R = {}
        S0 = self._slots(FINDS[0])
        start = {k: x - 1500.0 for k, x in S0.items()}
        start["wheels"] = S0["wheels"] - 1500.0 - 300.0
        start[FINDS[0]["finder"]] = start["wheels"] + PUSH + 210.0 + self._hw(FINDS[0]["finder"])
        for k in ORDER:
            R[k] = Route(start[k], -self.LEAD)
        d_open = say(self, -self.LEAD + 1.0, OPEN)
        self.T0 = T0 = {}
        R["wheels"].wait(max(1.0, -self.LEAD + 1.0 + d_open - 6.0)).go(start["wheels"] + 300.0, v=120)
        T0["book_in"] = R["wheels"].t
        T0["open"] = T0["book_in"] + 0.8
        T0["title"] = (T0["open"] + 1.5, T0["open"] + 10.0)
        T0["settle"] = T0["title"][1] + 5.0              # the camera eases back out before the walk
        t = T0["settle"]
        self.F = []
        for i, f in enumerate(FINDS):
            S = self._slots(f)
            T = {"walk": t, "slots": S}
            order = sorted(ORDER, key=lambda k: -R[k].x)
            for j, k in enumerate(order):
                R[k].wait(t + 0.3 * j).go(S[k], v=165 if k != "lantern" else 170)
            arrive = max(R[k].t for k in ORDER)
            T["hint"] = arrive - 1.0
            d_h = say(self, T["hint"], f["hint"])
            T["reveal"] = arrive + 0.5
            T["zin"] = (arrive, arrive + (15.0 if f["kind"] in ("owl", "squirrel") else 13.0 if f["zoom"] > 2.3 else 11.0))
            T["close"] = (T["zin"][1], T["zin"][1] + 5.0)
            T["to_book"] = (T["close"][1], T["close"][1] + (7.0 if f["kind"] in ("owl", "squirrel", "deer") else 5.0))
            b = T["to_book"][1]
            T["flips"] = [b + 0.3, b + 1.3, b + 2.3]
            T["tick"] = b + 3.2
            d_l = say(self, b + 4.8, f["line"])
            T["card"] = (b + 4.5, b + 4.8 + max(d_l + 1.8, 9.0))
            T["leave"] = T["card"][1] - 1.0
            T["out"] = (T["card"][1], T["card"][1] + 11.0)
            T["end"] = T["out"][1]
            T["hint_end"] = T["hint"] + d_h
            t = T["end"]
            self.F.append(T)
        last = self.F[-1]
        self.FIN = dict(flip=last["end"] + 0.5, rise=last["out"][0])
        d_f = say(self, self.FIN["flip"] + 4.5, FINALE)
        self.FIN["card"] = (self.FIN["flip"] + 4.0, self.FIN["flip"] + 4.5 + d_f + 2.0)
        self.FIN["cheer"] = self.FIN["card"][1] - 1.5
        self.FIN["back"] = self.FIN["card"][1]
        self.dur = self.FIN["back"] + 12.0
        say(self, self._dur_base + 1.5, SIGNOFF)           # over the end sign (dur includes the LEAD)
        self.R = R

    def find_at(self, t):
        for i, T in enumerate(self.F):
            if t < T["end"]:
                return i, T
        return len(self.F) - 1, self.F[-1]

    def found(self, t):
        return sum(1 for T in self.F if t >= T["tick"])

    def cart_x(self, t):
        return self.R["wheels"].at(t) + PUSH

    # ----- camera -----

    def _wide(self, i):
        S = self.F[i]["slots"]
        x = FINDS[i]["x"]
        lo = min(x + BOOK_DX - PUSH - 160, min(S.values()) - 170)
        hi = max(x + 260, max(S.values()) + 190)
        z = min(0.9, 1920.0 / (hi - lo + 160))
        return (lo + hi) / 2, None, z

    def _close(self, i, t=None):
        f = FINDS[i]
        ax, ay = self.animal_focus(i, t if t is not None else self.F[i]["close"][0])
        return ax - 60.0, ay, f["zoom"]

    def _two(self, i):
        """The two-shot: the open guide and the animal together (the match, the tick, the name card)."""
        f = FINDS[i]
        lo, hi = f["x"] + BOOK_DX - 190.0, f["x"] + RIGHT[f["kind"]]
        top, bot = min(TOP[f["kind"]], BOOK_Y - 120.0), G + 50.0
        z = min(1.9, 1920.0 / (hi - lo + 160.0), 1080.0 / (bot - top + 260.0))
        return (lo + hi) / 2, (top + bot) / 2 + 60.0 / z, z

    def target(self, t):
        keys = [(-self.LEAD, *self._open_wide()), (self.T0["open"] - 2.0, *self._open_wide()),
                (self.T0["open"] + 4.5, *self._open_book()), (self.T0["title"][1] - 1.0, *self._open_book()),
                (self.T0["settle"] + 1.5, *self._open_wide2())]
        for i, T in enumerate(self.F):
            w = self._wide(i)
            c = self._close(i)
            b = self._two(i)
            mid = ((w[0] + c[0]) / 2, None, math.sqrt(w[2] * c[2]))
            mid2 = ((w[0] + b[0]) / 2, None, math.sqrt(w[2] * b[2]))
            keys += [(T["walk"] + 1.5, *(self._open_wide2() if i == 0 else self._wide(i - 1))),
                     (T["zin"][0] - 0.8, *w), (T["zin"][0] + 0.2, *w), ((T["zin"][0] + T["zin"][1]) / 2, *mid),
                     (T["zin"][1], *c), (T["close"][1], *c), (T["to_book"][1], *b), (T["out"][0], *b),
                     ((T["out"][0] + T["out"][1]) / 2, *mid2), (T["out"][1], *w)]
        Fn = self.FIN
        last = len(self.F) - 1
        bk = self._two(last)
        keys += [(Fn["flip"] - 0.5, *self._wide(last)), (Fn["flip"] + 6.0, *bk), (Fn["back"], *bk),
                 (self._dur_base, FINDS[-1]["x"] - 300.0, G - 420.0, 0.62)]
        keys = [(k[0], k[1], (G - 0.36 * 1080.0 / k[3]) if k[2] is None else k[2], k[3]) for k in keys]
        keys.sort(key=lambda e: e[0])
        for i in range(len(self.F)):                      # the walks: a steady pan with the Keepers, eased ends
            T = self.F[i]
            a, b = max(T["walk"] + 1.5, self.T0["settle"] + 1.5), T["zin"][0] - 0.8
            if a <= t < b:
                pa = self._open_wide2() if i == 0 else self._wide(i - 1)
                pb = self._wide(i)
                u = Route(0.0, a).go(1.0, v=1.0 / max(0.1, b - a - 2.5), ramp=2.5).at(t)
                z = math.exp(lerp(math.log(pa[2]), math.log(pb[2]), u))
                ya = G - 0.36 * 1080.0 / pa[2] if pa[1] is None else pa[1]
                yb = G - 0.36 * 1080.0 / pb[2] if pb[1] is None else pb[1]
                return lerp(pa[0], pb[0], u), lerp(ya, yb, u), z
        return cam_keys(keys, t)

    def _open_wide(self):
        S0 = self._slots(FINDS[0])
        x = (min(S0.values()) - 1500.0 + max(S0.values()) - 1500.0) / 2 - 150
        return x, None, 0.85

    def _open_wide2(self):
        """After the title: everyone and the cart, ready to walk."""
        x = self.R["wheels"].at(self.T0["book_in"]) + PUSH - 450.0 if hasattr(self, "R") else 0.0
        return x, None, 0.85

    def _open_book(self):
        x = self.R["wheels"].at(self.T0["book_in"]) + PUSH if hasattr(self, "R") else 0.0
        return x + 30.0, G - 200.0, 1.75

    # ----- the animals -----

    def animal_focus(self, i, t):
        """Where the close-up looks: the middle of the animal."""
        f = FINDS[i]
        x, y = self.animal_xy(i, t)
        h = {"raccoon": 0.5, "owl": 0.6, "opossum": 0.4, "squirrel": 0.2, "fox": 0.55, "deer": 0.62}[f["kind"]]
        return x, y - h * f["s"]

    def animal_xy(self, i, t):
        f = FINDS[i]
        T = self.F[i]
        x = f["x"]
        k = f["kind"]
        if k == "raccoon":
            go = seg(t, T["leave"], T["leave"] + 11.0)
            return lerp(x, HIDE[k] + 60.0, smoothstep(go)), G
        if k == "owl":
            return x, OWL_BRANCH
        if k == "opossum":
            u = seg(t, T["reveal"] - 1.0, T["zin"][1]) * 0.55 + 0.45 * seg(t, T["leave"], T["leave"] + 9.0)
            ox = lerp(LOG[0] + 40.0, LOG[1] - 30.0, u)
            off = seg(t, T["leave"] + 9.0, T["leave"] + 17.0)                # down off the end and away
            if off > 0:
                ox = lerp(LOG[1] - 30.0, HIDE[k] + 60.0, off)
                return ox, G - 62.0 * (1 - smoothstep(seg(ox, LOG[1] - 10.0, LOG[1] + 70.0)))
            return ox, G - 62.0
        if k == "squirrel":
            return self.squirrel_xy(t, T)[:2]
        if k == "fox":
            go = seg(t, T["leave"] + 1.0, T["leave"] + 9.0)
            return lerp(x, HIDE[k] + 60.0, smoothstep(go)), G
        if k == "deer":
            go = smoothstep(seg(t, T["leave"] + 1.5, T["leave"] + 14.0))
            return x + 650.0 * go ** 1.5, G
        return x, G

    def squirrel_xy(self, t, T):
        """The flying squirrel: on tree A high up, a glide down to tree B, clinging there, then up out of sight.
        -> (x, y, glide 0/1, angle)."""
        g0 = T["reveal"] + 1.5
        g1 = g0 + 2.6
        ax, ay = TREE_A + 34.0, G - 640.0                     # trunk edges: it clings to the bark
        bx, by = TREE_B - 34.0, G - 380.0
        if t < g0:
            return ax, ay, 0.0, 0.0
        if t < g1:
            u = (t - g0) / (g1 - g0)
            x = lerp(ax, bx, u)
            y = lerp(ay, by, u) - 90.0 * math.sin(math.pi * u) * 0.4 + 40 * u * (1 - u)
            return x, y, 1.0, 0.18
        climb = smoothstep(seg(t, T["leave"], T["leave"] + 6.0))
        return bx, by - 420.0 * climb, 0.0, 0.0

    def gone(self, i, t):
        """Has the animal gone behind its bush (not drawn any more)?"""
        k = FINDS[i]["kind"]
        return k in HIDE and self.animal_xy(i, t)[0] > HIDE[k] + 50.0

    def draw_find(self, c, i, t):
        f = FINDS[i]
        T = self.F[i]
        k, s = f["kind"], f["s"]
        if self.gone(i, t):
            return
        x, y = self.animal_xy(i, t)
        if k == "raccoon":
            walking = t > T["leave"] + 0.5
            look = smoothstep(seg(t, T["close"][0] - 1.5, T["close"][0])) * \
                (1 - smoothstep(seg(t, T["card"][1] - 3.0, T["card"][1] - 1.5)))
            bl = bump(t % 4.7, 0.0, 0.22)
            draw_animal(c, k, x, y, s, t, face=1, wash=0.0 if walking else 1.0 - look, walk=1.0 if walking else 0.0,
                        gait=(x - f["x"]) / 60.0, look=look, blink=bl)
        elif k == "owl":
            hd = math.sin(t * 0.35) * 0.6 if t < T["close"][0] else 0.8 * math.sin(t * 0.5)
            call = bump(t, T["hint"] + 1.5, 0.9) + bump(t, T["hint"] + 2.8, 0.9) + bump(t, T["close"][0] + 1.0, 1.2)
            bl = bump(t % 5.3, 0.0, 0.25)
            draw_animal(c, k, x, y, s, t, head=hd, call=min(1.0, call), blink=bl)
        elif k == "opossum":
            moving = (T["reveal"] - 1.0 < t < T["zin"][1]) or (T["leave"] < t < T["leave"] + 17.0)
            draw_animal(c, k, x, y, s, t, walk=1.0 if moving else 0.0, gait=(x - LOG[0]) / 50.0, babies=3,
                        sniff=math.sin(t * 3.0) * 0.5)
        elif k == "squirrel":
            sx, sy, gl, ang = self.squirrel_xy(t, T)
            if gl > 0.5:
                draw_animal(c, k, sx, sy, s, t, glide=1.0, ang=ang)
            else:
                on_b = sx > (TREE_A + TREE_B) / 2
                face = 1 if on_b else -1                      # it faces its trunk: tree B on its right, A on its left
                climb = (G - 380.0 - sy) / (0.35 * s) if on_b else 0.0
                draw_animal(c, k, sx - face * 0.17 * s, sy + 0.3 * s, s, t, face=face, climb=climb)
        elif k == "fox":
            trot = t > T["leave"] + 1.0
            draw_animal(c, k, x, y, s, t, sit=0.0 if trot else 1.0, ears=math.sin(t * 0.9) * (0.0 if trot else 1.0),
                        walk=1.0 if trot else 0.0, gait=(x - f["x"]) / 70.0, tail=0.3 * math.sin(t * 2))
        elif k == "deer":
            up = smoothstep(seg(t, T["reveal"] + 0.5, T["reveal"] + 2.5))
            go = t > T["leave"] + 1.5
            flag = smoothstep(seg(t, T["leave"], T["leave"] + 1.2))
            draw_animal(c, k, x + 230.0, y, s * 0.62, t, fawn=True, walk=1.0 if go else 0.0,
                        gait=(x - f["x"]) / 75.0 + 0.3, head_up=0.25 + 0.75 * up, ears=math.sin(t * 1.3 + 1))
            draw_animal(c, k, x, y, s, t, walk=1.0 if go else 0.0, gait=(x - f["x"]) / 85.0, flag=flag,
                        head_up=0.15 + 0.85 * up, ears=math.sin(t * 0.8))

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        i, T = self.find_at(t)
        f = FINDS[i]
        for kind in ORDER:
            m = self.m(kind)
            if m is None:
                continue
            x = self.R[kind].at(t)
            y, dy = (G - GLO_UP + 6 * math.sin(t * 1.3)) if kind == "lantern" else G, 0.0
            if kind == "springs":
                dy -= self._hop(t, i, T)
            self.place(m, x, t, dt, y=y, dy=dy)
            self.new_look(m, work_flash(kind, t, 2.0), smile=0.6)
            m.dig, m.punch, m.punch_l = 0.0, 0.0, 0.0
            if kind == "lantern":
                m.lamp = 1.0
        self._work(i, T, f, t)
        self._particles(t)
        self._sounds(t)

    def _hop(self, t, i, T):
        for ts, Td, a, b, r in self.R["springs"].legs:
            if ts <= t < ts + Td:
                n = max(1, int(round(abs(b - a) / 170.0)))
                ph = ((t - ts) / Td * n) % 1.0
                return 4 * 48 * ph * (1 - ph)
        if FINDS[i]["finder"] == "springs":
            return 4 * 70 * bump(t, T["hint"] + 0.6, 1.0) ** 2
        return 0.0

    def _work(self, i, T, f, t):
        gl = self.m("lantern")
        if f["finder"] == "lantern" and gl is not None:
            gl.lamp = 1.0 - 0.65 * smoothstep(seg(t, T["hint"], T["hint"] + 2.5)) * \
                (1 - smoothstep(seg(t, T["out"][0], T["out"][0] + 4.0)))
        hans = self.m("tentacles")
        if f["finder"] == "tentacles" and hans is not None:                   # Hans points at the ripples
            u = bump(t, T["hint"] - 0.5, 4.5)
            if u > 0:
                hx, hy = hans.x + 60, G - 300 * hans.k
                self.reach["tentacles"] = [(lerp(hx, f["x"] + 60, u), lerp(hy, G - 40, u))]
        twigs = self.m("teeth")
        if f["finder"] == "teeth" and twigs is not None:
            twigs.punch = 0.8 * bump(t, T["hint"] + 1.5, 5.0)                 # points up at the owl

    def _particles(self, t):
        s = self.s
        if t > self.FIN["rise"] and s.particles.rng.uniform() < 0.4:
            p = _firefly(s.particles.rng, FINDS[-1]["x"] + s.particles.rng.uniform(-1300, 600), G - 220, G)
            s.particles.items.append(p)
        elif s.particles.rng.uniform() < 0.05:
            vx0, vx1 = s.view()[:2]
            s.particles.items.append(_firefly(s.particles.rng, s.particles.rng.uniform(vx0, vx1), G - 300, G))

    # ----- talking and sounds -----

    def aside_moods(self, t):
        if speaking(self, t, 1.0):
            return []
        i, T = self.find_at(t)
        if T["card"][0] - 0.5 < t < T["card"][1]:
            return []
        return ["mm", "ooh", "hehe", "hm"]

    def _chat(self, at, kind, mood, **kw):
        if self.crossed(at) and not speaking(self, at, 0.4):
            self.chat(at, kind, mood, **kw)

    def _sounds(self, t):
        for i, (T, f) in enumerate(zip(self.F, FINDS)):
            x, fk = f["x"], f["finder"]
            others = [k for k in ORDER if k != fk]
            self._chat(T["hint_end"] + 0.3, fk, "ooh", icon="sparkle")
            if self.crossed(T["hint_end"] + 1.2) and not speaking(self, T["hint_end"] + 1.2, 0.4):
                self.chorus(T["hint_end"] + 1.2, others[:2], "ooh", gap=0.4)
            for ft in T["flips"]:
                if self.crossed(ft):
                    self.fx(ft, "rustle", 0.35, 0.14, x + BOOK_DX, BOOK_Y)
            if self.crossed(T["tick"]):
                self.hit(T["tick"], "warm_bell", 72, 0.14, x + BOOK_DX, BOOK_Y)
                self.hit(T["tick"] + 0.22, "warm_bell", 79, 0.12, x + BOOK_DX, BOOK_Y)
            self._chat(T["tick"] + 0.15, fk, "yay")
            self._chat(T["out"][0] + 1.0, fk, "aww", icon="heart")
            if f["kind"] == "owl":                                        # who-cooks-for-you, soft and low
                for base in (T["hint"] + 1.5, T["close"][0] + 1.0):
                    for q, (dt_, n) in enumerate(((0.0, 62), (0.3, 62), (0.55, 64), (0.9, 60))):
                        if self.crossed(base + dt_):
                            self.hit(base + dt_, "sky_swell", n, 0.1, x, OWL_BRANCH)
            if f["kind"] == "raccoon":
                for q in range(6):
                    tq = T["walk"] + 4.0 + q * 3.1
                    if self.crossed(tq):
                        self.fx(tq, "bubble", 0.6, 0.06, x + 40, G + 20)
            if f["kind"] == "squirrel" and self.crossed(T["reveal"] + 4.1):
                self.hit(T["reveal"] + 4.1, "wood_thud", 50, 0.06, TREE_B, G - 380)
            if f["kind"] == "opossum" and self.crossed(T["reveal"]):
                self.fx(T["reveal"], "leaf_settle", 1.2, 0.08, x, G - 60)
        if self.crossed(self.T0["open"]):
            self.fx(self.T0["open"], "rustle", 0.6, 0.18, self.cart_x(self.T0["open"]), BOOK_Y)
        Fn = self.FIN
        if self.crossed(Fn["flip"]):
            self.fx(Fn["flip"], "rustle", 0.6, 0.16, FINDS[-1]["x"] + BOOK_DX, BOOK_Y)
        if self.crossed(Fn["cheer"]):
            self.chorus(Fn["cheer"], ORDER, "yay", gap=0.3)

    # ----- what moves (for the warp check) -----

    def props(self, t):
        out = {"cart": (self.cart_x(t), G)}
        for i in range(len(FINDS)):
            T = self.F[i]
            if T["walk"] - 2 <= t <= T["end"] + 10:
                out["animal%d" % i] = self.animal_xy(i, t)
        return out

    # ----- drawing -----

    def draw(self, c, t):
        s = self.s
        self.night.draw(s, c, t)
        self.night.ground_slab(s, c)
        self._forest(c, t)
        for i, f in enumerate(FINDS):
            if s.visible(f["x"] - 1100, f["x"] + 1100) and f["kind"] not in ("raccoon",):
                self.draw_find(c, i, t)
        gl = self.m("lantern")
        self.glo_light(c, k=0.8 * (gl.lamp if gl is not None and gl.lamp is not None else 1.0))
        self.draw_monsters(c, t)
        if s.visible(FINDS[0]["x"] - 1100, FINDS[0]["x"] + 1100):
            self.draw_find(c, 0, t)                                    # the raccoon at the water, in front
        self._stream(c, t)
        vx0, vx1 = s.view()[:2]
        for k, bx in HIDE.items():                                     # the bushes in front
            if vx0 - 200 < bx < vx1 + 200:
                for dx, r, sh in ((-40, 78, 0.5), (45, 70, 0.56), (0, 96, 0.52)):
                    c.circle(bx + dx, G + 30 - r * 0.45, r, TREE_LEAF[1] * sh)
        cx = self.cart_x(t)
        if s.visible(cx - 300, cx + 300):
            draw_cart(c, cx, -cx / 22.0)
            self._book(c, t, cx)
        self._flare(c, t)

    def _forest(self, c, t):
        s = self.s
        vx0, vx1 = s.view()[:2]
        for j, x in enumerate(np.arange(-1800, 9800, 520)):                       # the wood (thins to a meadow)
            if vx0 - 400 < x < vx1 + 400 and not (8100 < x < 9400) and abs(x - 3700) > 300:
                tree(c, x + 90 * math.sin(j * 1.7), G, 700 + 140 * ((j * 7) % 3), 400 + j)
        if vx0 - 600 < 3580 < vx1 + 600:                                          # the old oak with the owl's branch
            rect(c, 3540, G - 900, 3640, G, BARK_C)
            c.polygon([(3600, OWL_BRANCH - 10), (3900, OWL_BRANCH - 20), (3910, OWL_BRANCH + 6), (3600, OWL_BRANCH + 22)],
                      BARK_C * 1.1)
            for q in range(6):
                c.circle(3590 + (q - 2.5) * 110, G - 950 - 60 * (q % 2), 170, TREE_LEAF[1] * 0.55)
        for tx in (TREE_A, TREE_B):                                               # the squirrel's two trees
            if vx0 - 300 < tx < vx1 + 300:
                rect(c, tx - 34, G - 980, tx + 34, G, BARK_C * 0.95)
                for q in range(4):
                    c.circle(tx + (q - 1.5) * 90, G - 1040 - 50 * (q % 2), 150, TREE_LEAF[1] * 0.55)
        if vx1 > 8000:                                                            # the meadow and the forest's edge
            for j, gx in enumerate(np.arange(8000, 13000, 46)):
                if vx0 - 50 < gx < vx1 + 50:
                    h = 26 + 14 * math.sin(j * 1.9)
                    c.line(gx, G, gx + 6 * math.sin(t * 0.8 + j), G - h, MEADOW * (0.8 + 0.2 * math.sin(j)), 3)
        if vx0 - 600 < LOG[1] and LOG[0] < vx1 + 600:                              # the opossum's old log
            a0, a1, r = LOG[0], LOG[1], 31.0
            c.polygon(ellipse(a0, G - r, 14, r, 24), BARK_C * 0.8)                   # the far end (bark rim)
            rect(c, a0, G - 2 * r, a1, G, BARK_C * 1.05)
            c.line(a0, G - 2 * r + 4, a1, G - 2 * r + 4, BARK_C * 1.3, 4)              # moonlit top
            c.line(a0, G - 3, a1, G - 3, BARK_C * 0.7, 5)
            for q in range(6):                                                        # bark furrows
                xq = a0 + 40 + q * 66
                c.line(xq, G - 52, xq + 50, G - 48 + 4 * (q % 2), BARK_C * 0.75, 3)
                c.line(xq + 20, G - 22, xq + 64, G - 18, BARK_C * 0.78, 3)
            c.polygon(ellipse(a1, G - r, 16, r, 28), BARK_C * 0.85)                   # the near cut end, its rings
            c.polygon(ellipse(a1, G - r, 13, r - 4, 28), np.array([186, 150, 108]))
            for q in (0.35, 0.6, 0.85):
                c.polyline(ellipse(a1, G - r, 13 * q, (r - 4) * q, 24), np.array([156, 120, 82]), 2)
        for j, x in enumerate(np.arange(-1500, 8000, 410)):                       # low bushes, not at the finds
            if vx0 - 200 < x < vx1 + 200 and all(abs(x - f["x"]) > 450 for f in FINDS) and \
                    not (STREAM[0] - 100 < x < STREAM[1] + 100):
                r = 70 + 20 * ((j * 3) % 3)
                c.circle(x, G - r * 0.5, r, TREE_LEAF[1] * 0.6)

    def _stream(self, c, t):
        s = self.s
        if not s.visible(STREAM[0] - 50, STREAM[1] + 50):
            return
        a, b = STREAM
        cx, rx = (a + b) / 2, (b - a) / 2
        # owner after the first render: the pond was a flat rectangle on what looked like planks. Now an organic
        # pond seen low from the side: a wobbly oval with a muddy bank, reeds and cattails, stones, lily pads.
        def edge(q, k=1.0):
            return [(cx + rx * k * math.cos(u) * (1 + 0.06 * math.sin(3 * u + 1) + 0.04 * math.sin(7 * u)),
                     G + 44 + 38 * k * math.sin(u) * (1 + 0.1 * math.sin(5 * u + 2)) + q)
                    for u in np.linspace(0, 2 * math.pi, 64, endpoint=False)]
        c.polygon(edge(4, 1.06), np.array([60, 48, 36]))                              # muddy bank
        c.polygon(edge(0, 1.0), WATER)
        c.polygon(edge(-6, 0.78), WATER * 1.12)
        for k in range(7):                                                         # moonlight on the water
            yy = G + 22 + k * 8
            w = rx * math.sqrt(max(0.0, 1 - ((yy - G - 44) / 40.0) ** 2)) * 0.8
            off = (t * 18 + k * 37) % 110
            for x0 in np.arange(cx - w + off, cx + w - 40, 150):
                c.line(x0, yy, x0 + 34 + 8 * math.sin(k), yy, WATER * 1.7, 2)
        for q, (lx, ly) in enumerate(((cx + 210, G + 50), (cx + 290, G + 62), (cx - 280, G + 58))):   # lily pads
            c.polygon(ellipse(lx, ly, 26, 8, 20, 0.4, 2 * math.pi - 0.1), np.array([60, 110, 64]) * (0.9 + 0.08 * q))
        for sxx, syy, r in ((a + 40, G + 30, 22), (a + 10, G + 60, 16), (b - 30, G + 40, 20)):          # stones
            c.polygon(ellipse(sxx, syy, r * 1.3, r * 0.8, 18), np.array([104, 100, 94]))
            c.polygon(ellipse(sxx - r * 0.3, syy - r * 0.3, r * 0.5, r * 0.25, 12), np.array([132, 128, 120]))
        for j in range(14):                                                        # reeds and cattails at the ends
            for base in (a - 30 + j * 9, b - 90 + j * 8):
                h = 80 + 40 * math.sin(j * 2.3 + base)
                sw = 4 * math.sin(t * 0.9 + j)
                c.line(base, G + 26, base + sw, G + 26 - h, np.array([70, 104, 58]) * (0.8 + 0.03 * (j % 4)), 3)
                if j % 4 == 0:
                    c.polygon(ellipse(base + sw, G + 26 - h + 12, 5, 14, 12), np.array([110, 74, 48]))
        rx = FINDS[0]["x"] + 40
        i, T = 0, self.F[0]
        if t < T["leave"] + 1:                                                    # ripples round the raccoon's paws
            for q in range(3):
                ph = (t * 0.6 + q / 3) % 1.0
                c.polyline(ellipse(rx, G + 12, 14 + 50 * ph, 4 + 8 * ph, 24), WATER * (2.2 - 1.2 * ph), 2)

    # ----- the book (a page turn shows nothing new until the page comes down) -----

    def _flips(self):
        if hasattr(self, "_fl"):
            return self._fl
        out = [(self.T0["open"], -1, 0)]
        cur = 0
        for i, T in enumerate(self.F):
            seq = [7 + (i % 3), 8 + ((i + 1) % 3), i + 1]
            for ft, to in zip(T["flips"], seq):
                out.append((ft, cur, to))
                cur = to
        out.append((self.FIN["flip"], cur, 0))
        self._fl = out
        return out

    def _book_state(self, t):
        page = -1
        for ft, a, b in self._flips():
            if t < ft:
                return page, None, None
            if t < ft + 0.8:
                return a, b, (t - ft) / 0.8
            page = b
        return page, None, None

    def _book(self, c, t, x):
        if t < self.T0["open"]:
            closed_book(c, x)
            return
        a, b, u = self._book_state(t)
        y0, y1 = BOOK_Y - 86, BOOK_Y + 86
        cover = a == -1 and u is not None
        left_open = not (cover and u < 0.5)
        c.polygon([(x - (160 if left_open else 4), y0 - 4), (x + 160, y0 - 4), (x + 164, y1 + 8),
                   (x - (164 if left_open else 4), y1 + 8)], COVER * 0.8)
        right = b if u is not None else a
        left = a if u is not None else a                       # the old left page stays until the turn lands
        for side, page in ((-1, left), (1, right)):
            if side < 0 and (not left_open or page == -1):
                continue
            xa, xb = (x - 150, x - 4) if side < 0 else (x + 4, x + 150)
            c.polygon([(xa, y0 + (6 if side < 0 else 0)), (xb, y0 + (0 if side < 0 else 6)), (xb, y1), (xa, y1)], PAPER)
            c.line(x + side * 6, y0 + 4, x + side * 6, y1, PAPER_DARK, 4)
            self._page(c, t, page, side, xa, xb, y0, y1)
        c.line(x, y0, x, y1 + 4, COVER * 0.6, 3)
        if u is not None:
            w = 146 * math.cos(math.pi * u)
            lift = 26 * math.sin(math.pi * u)
            tip = x + w
            pts = [(x, y0), (tip, y0 - lift), (tip, y1 - lift * 0.4), (x, y1)]
            col = COVER if cover else PAPER
            c.polygon(pts, col * (0.82 + 0.18 * abs(math.cos(math.pi * u))))
            c.line(tip, y0 - lift, tip, y1 - lift * 0.4, PAPER_DARK, 2)
            if u > 0.5 and not cover:                          # the new left page, printed on the turning page
                v = smoothstep((u - 0.5) / 0.5)
                lo, hi = min(x, tip), max(x, tip)
                clip = [(lo, y0 - lift), (hi, y0 - lift), (hi, y1), (lo, y1)]
                fade_clip(c, self.s.glow, clip, lambda: self._page(c, t, b, -1, x - 150, x - 4, y0, y1), 1.0, v)

    PAGE_PAD = 4.0

    def _page_rect(self, xa, xb, y0, y1):
        k = self.PAGE_PAD
        return xa + k, y0 + k, xb - k, y1 - k

    @staticmethod
    def _pic(kind):
        """draw_at(c, x, y, s) for an animal's picture (the squirrel shown gliding, the way it's found)."""
        kw = {"squirrel": dict(glide=1.0)}.get(kind, {})
        return lambda c, x, y, s: draw_animal(c, kind, x, y, s, 0.0, **kw)

    def _fitted(self, c, kind, rect, margin):
        """The animal's picture, sized and placed to sit inside rect (never past its edge)."""
        if not hasattr(self, "_fits"):
            self._fits = {}
        key = (kind, tuple(round(v, 2) for v in rect), margin)
        if key not in self._fits:
            self._fits[key] = fit(self._pic(kind), rect, margin, grow=True,
                                  valign="middle" if kind == "squirrel" else "bottom")
        x, y, sz = self._fits[key]
        self._pic(kind)(c, x, y, sz)

    def _page_pic(self, c, kind, xa, xb, y0, y1):
        """The animal's picture on its left page."""
        self._fitted(c, kind, self._page_rect(xa, xb, y0, y1), 10.0)

    def _frame_rect(self, cx, cy):
        return cx - 19, cy - 29, cx + 19, cy + 29

    def _frame_pic(self, c, kind, cx, cy):
        """A found animal's little picture in its checklist frame."""
        self._fitted(c, kind, self._frame_rect(cx, cy), 3.0)

    def _card_rect(self, x0, y0, H):
        return x0 + 14, y0 + 12, x0 + 236, y0 + H - 12

    def _card_pic(self, cv, kind, x0, y0, H):
        self._fitted(cv, kind, self._card_rect(x0, y0, H), 6.0)

    def _cover_owl(self, c, xa, xb, y0, y1):
        """The owl under the checklist's title (below the two lines of text)."""
        self._fitted(c, "owl", (xa + 4, y0 + 66, xb - 4, y1 - 4), 4.0)

    def book_art(self):
        """Every picture that goes in the book or on a card, with the edge it must stay inside (for check_art)."""
        x, y0, y1 = 0.0, BOOK_Y - 86, BOOK_Y + 86
        xa, xb = x - 150, x - 4
        items = [("cover owl", lambda c: self._cover_owl(c, xa, xb, y0, y1), self._page_rect(xa, xb, y0, y1))]
        for q, f in enumerate(FINDS):
            k = f["kind"]
            items.append(("page " + k, lambda c, k=k: self._page_pic(c, k, xa, xb, y0, y1),
                          self._page_rect(xa, xb, y0, y1)))
            cx, cy = 4 + 30 + (q % 3) * 45, y0 + 46 + (q // 3) * 78
            items.append(("frame " + k, lambda c, k=k, cx=cx, cy=cy: self._frame_pic(c, k, cx, cy),
                          self._frame_rect(cx, cy)))
            W, H = 1240, 210
            cx0, cy0 = 960 - W // 2, 1080 - 30 - H
            items.append(("card " + k, lambda c, k=k: self._card_pic(c, k, cx0, cy0, H), self._card_rect(cx0, cy0, H)))
        return items

    def _page(self, c, t, p, side, xa, xb, y0, y1):
        if p == -1:
            c.polygon([(xa, y0), (xb, y0), (xb, y1), (xa, y1)], COVER)
            if side > 0:
                c.text("FIELD GUIDE", (xa + xb) / 2, y0 + 40, 15, PAPER)
            return
        if p == 0:
            return self._checklist(c, t, side, xa, xb, y0, y1)
        if p >= 7:
            if side < 0:
                c.polygon(ellipse((xa + xb) / 2, (y0 + y1) / 2, 46, 30, 20), PAPER_DARK)
            else:
                page_lines(c, xa, xb, y0 + 30, 7)
            return
        kind = FINDS[p - 1]["kind"]
        if side < 0:
            clipped(c, self.s.glow, self._page_rect(xa, xb, y0, y1),
                    lambda cc: self._page_pic(cc, kind, xa, xb, y0, y1))
        else:
            name = ANIMALS[kind]["name"]
            c.text(name.upper(), (xa + xb) / 2, y0 + 26, 14 if len(name) > 10 else 18, INK)
            page_lines(c, xa, xb, y0 + 52, 5)
            bx, by = xb - 32, y1 - 30
            c.polyline([(bx - 14, by - 14), (bx + 14, by - 14), (bx + 14, by + 14), (bx - 14, by + 14)], INK * 1.4, 2,
                       closed=True)
            tk = smoothstep(seg(t, self.F[p - 1]["tick"], self.F[p - 1]["tick"] + 0.5))
            if tk > 0:
                p1, p2, p3 = (bx - 10, by), (bx - 3, by + 9), (bx + 14, by - 14)
                if tk < 0.4:
                    c.line(*p1, lerp(p1[0], p2[0], tk / 0.4), lerp(p1[1], p2[1], tk / 0.4), TICK, 5)
                else:
                    v = (tk - 0.4) / 0.6
                    c.line(*p1, *p2, TICK, 5)
                    c.line(*p2, lerp(p2[0], p3[0], v), lerp(p2[1], p3[1], v), TICK, 5)

    def _checklist(self, c, t, side, xa, xb, y0, y1):
        if side < 0:
            c.text("WHO'S AWAKE", (xa + xb) / 2, y0 + 30, 17, INK)
            c.text("TONIGHT?", (xa + xb) / 2, y0 + 54, 17, INK)
            clipped(c, self.s.glow, self._page_rect(xa, xb, y0, y1), lambda cc: self._cover_owl(cc, xa, xb, y0, y1))
            return
        n = self.found(t)
        for q in range(6):
            cx = xa + 30 + (q % 3) * 45
            cy = y0 + 46 + (q // 3) * 78
            c.polyline([(cx - 20, cy - 30), (cx + 20, cy - 30), (cx + 20, cy + 30), (cx - 20, cy + 30)], INK * 1.4, 2,
                       closed=True)
            if q < n:
                kind = FINDS[q]["kind"]
                clipped(c, self.s.glow, self._frame_rect(cx, cy),
                        lambda cc, kind=kind, cx=cx, cy=cy: self._frame_pic(cc, kind, cx, cy))
            else:
                c.text("?", cx, cy, 24, INK * 1.6)

    def _flare(self, c, t):
        cx = self.cart_x(t)
        g = 0.0
        for ft, a, b in self._flips():
            g = max(g, bump(t, ft - 0.3, 1.4))
        for T in self.F:
            g = max(g, bump(t, T["tick"] - 0.3, 1.2))
        if g > 0.01:
            self.flare(c, cx + 60, BOOK_Y - 40, g)

    # ----- on screen: the name card and the count, in fixed screen units -----

    def screen(self, cv, ts):
        t = ts / self.STRETCH - self.LEAD
        i, T = self.find_at(t)
        T0 = self.T0
        if T0["title"][0] <= t < T0["title"][1] + 0.8:
            a = smoothstep(seg(t, T0["title"][0], T0["title"][0] + 0.7)) * (1 - smoothstep(seg(t, T0["title"][1],
                                                                                         T0["title"][1] + 0.7)))
            self._card(cv, a, "WHO'S AWAKE TONIGHT?", ["Can the Keepers find six", "night-time neighbours?"], None)
        a0, a1 = T["card"]
        if a0 <= t < a1 + 0.8:
            a = smoothstep(seg(t, a0, a0 + 0.7)) * (1 - smoothstep(seg(t, a1, a1 + 0.7)))
            kind = FINDS[i]["kind"]
            self._card(cv, a, ANIMALS[kind]["name"], ANIMALS[kind]["line"], kind)
        Fc = self.FIN["card"]
        if Fc[0] <= t < Fc[1] + 0.8:
            a = smoothstep(seg(t, Fc[0], Fc[0] + 0.7)) * (1 - smoothstep(seg(t, Fc[1], Fc[1] + 0.7)))
            self._card(cv, a, "All six found!", ["Every one of them helps", "keep the forest healthy."], None)
        if T0["title"][1] - 0.5 < t:
            n = self.found(t)
            hi = max((bump(t, Tq["tick"], 0.8) for Tq in self.F), default=0.0)
            self._unglow(cv, 40, 36, 470, 104)
            cv.polygon([(40, 36), (470, 36), (470, 104), (40, 104)], WOOD * 0.8)
            cv.polyline([(40, 36), (470, 36), (470, 104), (40, 104)], WOOD * 0.5, 4, closed=True)
            cv.text(f"NEIGHBOURS FOUND  {n} / 6", 255, 70, 30,
                    PAPER * (1 - 0.25 * hi) + np.array([255, 220, 120]) * 0.25 * hi)

    def _unglow(self, cv, x0, y0, x1, y1):
        g = self.s.glow.layer
        k = cv.s
        g[max(0, int(y0 * k)):int(y1 * k) + 1, max(0, int(x0 * k)):int(x1 * k) + 1] = 0

    def _card(self, cv, a, title, lines, kind):
        if a <= 0.01:
            return
        W, H = 1240, 210
        x0, y0 = 960 - W // 2, 1080 - 30 - H
        x1, y1 = x0 + W, y0 + H
        bg = cv.target.copy() if a < 0.999 else None
        self._unglow(cv, x0, y0, x1, y1)
        cv.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], WOOD * 0.75)
        cv.polygon([(x0 + 8, y0 + 8), (x1 - 8, y0 + 8), (x1 - 8, y1 - 8), (x0 + 8, y1 - 8)], CARD)
        tx0 = x0 + (240 if kind else 60)
        if kind:
            clipped(cv, self.s.glow, self._card_rect(x0, y0, H), lambda cc: self._card_pic(cc, kind, x0, y0, H))
        cx = (tx0 + x1 - 40) // 2
        cv.text(title, cx, y0 + H // 2 - 52, 58 if len(title) > 16 else 62, INK)
        for q, ln in enumerate(lines):
            cv.text(ln, cx, y0 + H // 2 + 14 + q * 42, 34, INK * 1.25)
        if bg is not None:
            cv.target[:] = (bg * (1 - a) + cv.target * a).astype(np.uint8)
