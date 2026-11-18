"""Forest Keepers ep 10 remake, Bug Hunt, in the flat picture-book look (docs/engines/forest_keepers_bug_hunt.md,
"Flat remake"). The story, timing, camera and sounds are the approved FK0007 (bug_hunt.py, owner + Toby fixes in);
this module draws that same scene, frame by frame, in the flat style (as tune_flat.py does for the Tune-Up's second
half): where every Keeper is, its pose and face, the camera, the hiding places, the cart and the Field Guide, Glo's
lens and the close-ups, the name cards.

The bugs keep their field-guide drawing (bugs.py: shape, colours, legs, how they walk, checked against photos); they
are painted flat through OldCanvas. From ep 14 on the Keepers walk naturally (tune_flat.Walks: arm swing, Twigs'
knees forward, Hans' staggered ripple).

    snap = record(scene, t)         # after scene.update(t, dt)
    rgb = draw(snap, scene)         # the frame, flat (the live scene supplies the act's own geometry)
"""
import math

import numpy as np
import skia

from families.foundry.keepers.common import lerp, seg, smoothstep

from . import bug_hunt as BH
from . import tune_flat as TF
from .animal_houses import G
BF_G = G
from .bugs import BUGS, draw_bug
from .flat import bush as flat_bush, lolly_tree, pine
from .storybook import C, oval, rrect, smooth, tone, tube
from .tune_flat import VIL, _box, _poly, _text, project

# the night forest, flat and muted (the village palette's night)
FOR = dict(VIL, back="#24384a", back2="#2a4250", mid2="#355a4e", soil="#6a5140", soil2="#584334", soil_in="#3a2c24",
           bark="#6e5240", wood="#b58e64", wood2="#9c774f", ring="#8f6b48", rock="#6c675d", rock2="#878074",
           rock3="#47433c", fern="#4f8a56", fern2="#3f7448", stem="#4f7a46", plant="#5f9a58", plant2="#6daa62",
           cart="#9a7048", cart2="#7d5838", cover="#5c7a46", cover2="#4a6638", paper="#f2e8d2", paper2="#d8c8a6",
           ink="#4a3a30", brass="#c9a35c", brass2="#9a7a40", card="#f6eedc", tick="#4f9a4f", panel="#8a6444",
           lamp="#ffe6a8", lens="#e6eef2")

# Continuity advisor round 1 (video_log/advisor/FK0022_r1.md) fixes:
BH.PUSH = 270.0        # Wheels pushes the cart from further back: the book's shelf no longer cuts across his face
ROCK_BACK = 60.0
PLANT_BACK = 60.0              # the ladybug's plant and the firefly's ferns stand up the path too
LENS_DROP = 45.0       # over a bug on the ground (soil, log, stone) Glo lowers the lens this much, so it is really over it
DIG_CLOSE = (-2.0, 4.5)  # the opening dig in its own close shot (straight cuts in and out): big enough to see
GLO_TEAL = "#1fb3a5"
BH.WORK["tentacles"] = 230.0   # Hans works the log from a leg's length away (his tentacle no longer grows to reach it)
BH.WORK["wheels"] = -130.0     # Wheels parks at the stone's left end: his right pincer reaches its top edge
GLO_UP = 150.0                 # during the opening dig Glo holds the lens up, out of the way of the hole
LENS_UP = 230.0                # and from setting off for a find until the bug is out: the reveal is never behind the
                               # glass (advisor FK0022 r2); it comes down over the bug when it is time to look
LENS_DX = dict(bark=-22.0, plant=15.0)   # (old: where the lens hung beside each bug)
# A true magnifier (advisor FK0022 r3: the lens showed a separate picture-in-a-disc, which shrank into a floating
# ball as it lifted, and two of each bug showed at once): the lens comes down centred on the real bug, and what is
# seen through it is the real scene drawn again at LOOK_M times the zoom about the lens centre. At 1x it is the
# scene itself, so nothing pops; as it lifts it shows whatever is behind it.
LOOK = dict(soil=(-28.0, -14.0), log=(1.0, -12.0), bark=(-22.0, -130.0), rock=(-10.0, -ROCK_BACK - 8.0),
            plant=(27.0, -188.0 - PLANT_BACK), ferns=(30.0, -100.0 - PLANT_BACK))           # (dx from the find, y from G) of the lens centre
LOOK_M = dict(soil=2.6, log=3.5, bark=2.4, rock=3.5, plant=3.5, ferns=4.0)
BARK_TOP_LIFT = 158.0           # the slab's bottom edge goes up to the stump's top (G - 170)
MILLI = dict(dx=-22.0, y=-128.0, L=74.0, hd=0.25)   # the millipede under the bark, slanting down to the right
LENS_M = 2.4                   # the lens magnifies the real millipede this much (same place, same slant)
LOG_BACK = 40.0                # the log rolls this far up the path too, clear of the line they walk along
REVEAL_Z = 2.7                 # the close shot of each uncovered bug (straight cuts in and out)
ROCK = dict(rx=60.0, ry=34.0, back=ROCK_BACK)   # the stone: small enough for Wheels to tip, a little up the path (behind
                                           # the walkers, so the cart passes in front of it, not through it)


# ----------------------------------------------------------------------------------------------- the act

class HuntFlatAct(BH.HuntAct):
    """FK0007's hunt, with one change for the owner's rule since FK0006 (nobody walks through anybody): the queue
    keeps its left-to-right order from one find to the next. So on each walk only the next finder has to get past the
    others, and he does it on the back lane (lanes()), never through them."""

    def _slots(self, f):
        cache = self.__dict__.setdefault("_slot_cache", {})
        if id(f) in cache:
            return cache[id(f)]
        prev = self.__dict__.get("_prev_order", ["springs", "teeth", "digger", "wheels", "tentacles", "lantern"])
        x = f["x"]
        pos = {"wheels": x + f.get("book", BH.BOOK_DX) - BH.PUSH, "lantern": x - 70.0}
        if f["finder"] not in ("wheels", "lantern"):
            pos[f["finder"]] = x + BH.WORK[f["finder"]]
        if f["finder"] == "lantern":
            pos["lantern"] = x
        fx = x + BH.WORK[f["finder"]]
        edge = max(x + 135.0, fx + (self._hw(f["finder"]) if f["finder"] not in ("wheels", "lantern") else 0.0)) + 40
        for k in prev:
            if k in pos:
                continue
            pos[k] = edge + self._hw(k)
            edge = pos[k] + self._hw(k) + 30
        self._prev_order = sorted(pos, key=lambda k: pos[k])
        cache[id(f)] = pos
        return pos

    # ----- the walks between finds, in short shots (owner 2026-11-06, no long walks) -----

    SHOT_HOLD = 3.0        # seconds of walking seen in the wide shot as they set off, and again as they arrive
    SHOT_SPLIT = 1e9       # one travelling shot per walk (advisor FK0022 r3: a second crop jumped 1200 px ahead, so
                           # the next find's plant seemed to stand where the stone had been, and a pass happened
                           # unseen between the two crops); it is on the middle of the whole line, so the last find
                           # goes out at one side as the next comes in at the other
    TRACK_Z = (1.05, 1.6)  # the travelling shot's zoom
    TRACK_FOLLOW = (0.85, 0.6)  # the travelling camera moves this share of their speed (under 250 screen px/s)

    def _plan(self):
        super()._plan()
        for T in self.F:                       # one page turn per bug, straight to its page (no placeholder pages)
            T["flips"] = [T["flips"][1]]
        self._reveal_close = []                # (from, to, x, y, zoom): each uncovered bug, close (advisor FK0022 r2)
        for i, (T, f) in enumerate(zip(self.F, BH.FINDS)):
            x = f["x"]
            if f["place"] == "rock":           # the lens stays up while Wheels tips the stone; then it comes over
                T["lens"] = max(T["lens"], T["lift"] + 4.4)
                T["close"] = max(T["close"], T["lens"] + 4.0)      # (and the camera's push-in after it, unhurried)
                assert T["close"] + 3.5 < T["book"], "the rock's lens comes too late"
                self._reveal_close.append((T["lift"] + 1.4, T["lift"] + 4.2, x - 10.0, G - ROCK["back"] - 20.0,
                                           3.2))
            elif f["place"] == "log":
                self._reveal_close.append((T["reveal"] + 3.3, T["reveal"] + 5.6, x - 30.0, G - 40.0, REVEAL_Z))
            elif f["place"] == "bark":
                self._reveal_close.append((T["reveal"] + 3.2, T["reveal"] + 5.6, x - 10.0, G - 110.0, REVEAL_Z))
        self._shots = {i: self._walk_shots(i) for i in range(1, len(self.F))}
        cuts = list(DIG_CLOSE) + [c for i in sorted(self._shots) for c in self._shots[i]["cuts"]]
        cuts += [c for a, b, *_ in self._reveal_close for c in (a, b)]
        self.camera_cuts = tuple((c + self.LEAD) * getattr(self, "STRETCH", 1.0) for c in cuts)   # act-local

    WALK_ICON = "?"        # (not a ladybug: the next bug is a surprise; advisor FK0022 r2)

    def _extra_moves(self, i, f, T, R):
        if f["finder"] == "teeth":                 # Twigs steps back once the bark is open: the lens needs the room
            R["teeth"].wait(T["reveal"] + 4.3).go(R["teeth"].x + 28.0, v=40.0)

    def _lens_x(self, t):
        """Glo (and the lens under him): beside the find, over the bug for the close-up, then back."""
        i, T = self.find_at(t)
        f = BH.FINDS[i]
        x = f["x"] + LOOK[f["place"]][0]
        base = self.R["lantern"].at(t)
        over = smoothstep(seg(t, T["lens"], T["lens"] + 3.0)) * (1 - smoothstep(seg(t, T["out"], T["out"] + 3.0)))
        return lerp(base, x, over)

    def rock_ang(self, i, t):
        """Wheels tips the stone right up (more than the old 0.42 rad): the beetle under it is plain to see."""
        return BH.HuntAct.rock_ang(self, i, t) * (0.62 / 0.42)

    def milli(self, i, t):
        """(x, y, heading, distance walked) of the real millipede: under the loose bark, slanting down to the right;
        it creeps along a little once uncovered, and at the end climbs up the face, over the top and down behind."""
        T = self.F[i]
        x = BH.FINDS[i]["x"]
        hd = MILLI["hd"]
        x0, y0 = x + MILLI["dx"], G + MILLI["y"]

        def at(tt):
            s = 0.4 * max(0.0, min(tt, T["home"][0]) - (T["reveal"] + 3.0))
            bx, by = x0 + s * math.cos(hd), y0 + s * math.sin(hd)
            if tt <= T["home"][0]:
                return bx, by, s
            pts = [(bx, by), (x - 52.0, G - 146.0), (x - 62.0, G - 192.0), (x - 70.0, G - 250.0)]
            d = 25.0 * (tt - T["home"][0])
            for (ax, ay), (cx_, cy_) in zip(pts, pts[1:]):
                L = math.hypot(cx_ - ax, cy_ - ay)
                if d <= L:
                    return ax + (cx_ - ax) * d / L, ay + (cy_ - ay) * d / L, s + 25.0 * (tt - T["home"][0])
                d -= L
            return pts[-1][0], pts[-1][1], s + 25.0 * (tt - T["home"][0])
        bx, by, dist = at(t)
        if t > T["home"][0]:                    # it faces where it goes (turning smoothly at the corners)
            ax, ay, _ = at(t - 0.3)
            cx_, cy_, _ = at(t + 0.3)
            if math.hypot(cx_ - ax, cy_ - ay) > 1.0:
                hd = math.atan2(cy_ - ay, cx_ - ax)
        return bx, by, hd, dist

    def _flips(self):
        """[(t, from page, to page)]: open on the checklist, then one turn per bug straight to its page, and back to
        the checklist at the end (advisor FK0022 r1: no blank placeholder pages flipping past)."""
        out = [(self.F[0]["open"], -1, 0)]
        cur = 0
        for i, T in enumerate(self.F):
            out.append((T["flips"][0], cur, i + 1))
            cur = i + 1
        out.append((self.FIN["flip"], cur, 0))
        return out

    def lens_drop(self, t):
        """How far Glo has lowered the lens now: over a bug on the ground, and (negative) held up out of the way of
        the opening dig."""
        i, T = self.find_at(t)
        after = LENS_UP * smoothstep(seg(t, T["out"], T["out"] + 2.5))    # up again once the look is over (and
        if i == 0:                                                      # through the walk to the next find)
            up = max(GLO_UP * (1 - smoothstep(seg(t, DIG_CLOSE[1], DIG_CLOSE[1] + 3.0))), after)
        else:                                  # still up from the last find until it comes over this bug
            up = max(LENS_UP * (1 - smoothstep(seg(t, T["lens"], T["lens"] + 2.5))), after)
        over = smoothstep(seg(t, T["lens"], T["lens"] + 3.0)) * (1 - smoothstep(seg(t, T["out"], T["out"] + 3.0)))
        return (G + LOOK[BH.FINDS[i]["place"]][1] - BH.LENS_Y) * over - up    # centred on the real bug

    # ----- the covers: each one moved by a Keeper you can see doing it (advisor FK0022 r1) -----

    def log_xy(self, i, t):
        """Hans pushes the log off the pill bugs: it rolls left, away from him, and stays there."""
        T = self.F[i]
        u = BH.smootherstep(seg(t, T["reveal"] + 0.8, T["reveal"] + 4.4))
        r = 64.0
        return BH.FINDS[i]["x"] - 150.0 * u, G - r - LOG_BACK * u, r

    def bark_open(self, i, t):
        """0..1: Twigs lifts the loose bark slab straight up off the stump's face by its top edge (0..0.6: the
        millipede shows from the bottom up), then tips it back to lie on the stump's top (0.6..1), where it stays
        (advisor FK0022 r3: it folded flat towards us and seemed to vanish by itself, nobody touching it)."""
        T = self.F[i]
        a = T["reveal"]
        return 0.6 * smoothstep(seg(t, a + 1.1, a + 2.7)) + 0.4 * smoothstep(seg(t, a + 2.7, a + 3.5))

    @staticmethod
    def bark_slab(op):
        """The slab's (bottom y, height, dx) for open amount op: lifted, then tipped back flat onto the top's right
        part (dx: clear of the millipede's way home over the left)."""
        lift = BARK_TOP_LIFT * smoothstep(min(1.0, op / 0.6))
        tip = smoothstep(max(0.0, (op - 0.6) / 0.4))
        return G - 12 - lift, 138.0 - (138.0 - 14.0) * tip, 50.0 * tip

    def rock_xy(self, i):
        x = BH.FINDS[i]["x"]
        return x + ROCK["rx"], G - ROCK["back"]                # the pivot: its right foot

    def rock_grip(self, i, t):
        """Where Wheels' pincer holds the stone (its top-left edge), turned with it."""
        px, py = self.rock_xy(i)
        x = BH.FINDS[i]["x"]
        gx, gy = x - ROCK["rx"] * 0.8, G - ROCK["back"] - ROCK["ry"] * 1.55
        ang = self.rock_ang(i, t)
        dx, dy = gx - px, gy - py
        ca, sa = math.cos(ang), math.sin(ang)
        return px + dx * ca - dy * sa, py + dx * sa + dy * ca

    def _work(self, i, T, f, t):
        super()._work(i, T, f, t)
        kind = f["finder"]
        m = self.m(kind)
        if m is None:
            return
        if kind == "tentacles":                                # two tentacles swing out to the log's side, push
            lx, ly, rr = self.log_xy(i, t)                     # it off, and swing back: same length all the way
            k = m.k
            hy = m.y - 305 * k
            out = smoothstep(seg(t, T["reveal"], T["reveal"] + 0.8)) * (1 - smoothstep(seg(t, T["reveal"] + 1.6,
                                                                                            T["reveal"] + 2.4)))
            self.reach.pop("tentacles", None)
            if out > 0.0:
                pts = []
                for q, (fx, fy) in enumerate(((0.95, -0.25), (0.78, -0.62))):
                    rx_, ry_ = m.x - (40 + 22) * k, hy + (64 + 8) * k
                    x0 = BH.FINDS[i]["x"]
                    L0 = math.hypot(x0 + rr * fx - rx_, ly + rr * fy - ry_)
                    a_rest = math.atan2(0.95, -0.3)
                    cx_, cy_ = lx + rr * fx, ly + rr * fy
                    a_hit = math.atan2(cy_ - ry_, cx_ - rx_)
                    a_ = a_rest + (a_hit - a_rest) * out
                    if out >= 0.999:
                        pts.append((cx_, cy_))
                    else:
                        pts.append((rx_ + L0 * math.cos(a_), ry_ + L0 * math.sin(a_)))
                self.reach["tentacles"] = pts
        elif kind == "teeth":                                  # Twigs' left hand on the bark's top edge
            m.punch_l = 0.0
            a = T["reveal"]
            w = smoothstep(seg(t, a + 0.3, a + 1.1)) * (1 - smoothstep(seg(t, a + 3.6, a + 4.2)))
            m.arm_to.pop(-1, None)
            m.arm_w.pop(-1, None)
            if w > 0.0:                                        # his hand on the slab's top edge all the way
                bot, hh, dx = self.bark_slab(self.bark_open(i, t))
                x = BH.FINDS[i]["x"]
                m.arm_to[-1] = (x + 34 + dx, bot - hh)
                m.arm_w[-1] = w
        elif kind == "wheels" and "lift" in T:                  # Wheels' right pincer tips the stone up, holds it,
            m.punch = 0.0                                      # and lowers it back over the beetle
            w = smoothstep(seg(t, T["lift"] - 0.6, T["lift"] + 0.3)) * (1 - smoothstep(seg(t, T["home"][1] - 0.2,
                                                                                         T["home"][1] + 0.6)))
            m.arm_to.pop(1, None)
            m.arm_w.pop(1, None)
            if w > 0.0:
                m.arm_to[1] = self.rock_grip(i, t)
                m.arm_w[1] = w

    def update(self, t, dt):
        super().update(t, dt)
        gl = self.m("lantern")
        if gl is not None:
            gl.y += self.lens_drop(t)
        wm = self.m("wheels")                    # whenever the cart goes with him, his right pincer holds its push
        if wm is not None:                       # bar (advisor FK0022 r3: it rolled along by itself, his claws down)
            i, T = self.find_at(t)
            rock = BH.FINDS[i]["finder"] == "wheels" and "lift" in T and                 T["lift"] - 0.8 <= t <= T["home"][1] + 0.8
            d = abs(self.cart_x(t) - (wm.x + BH.PUSH))
            w = 1.0 - smoothstep(seg(d, 0.0, 40.0))
            if not rock:
                if w > 0.0:
                    wm.arm_to[1] = (wm.x + HANDLE_GRIP[0], G + HANDLE_GRIP[1])
                    wm.arm_w[1] = w
                else:
                    wm.arm_to.pop(1, None)
                    wm.arm_w.pop(1, None)

    def _walk_shots(self, i):
        """Owner 2026-11-06 (FK0019): "if they ever need to do more walking than that, you should change the angle or
        the crop or the zoom". Each walk to the next find (~10-13 s) is cut into short shots with straight cuts:
        the wide shot of the last find as they set off (SHOT_HOLD s), a closer travelling shot (two, the second closer on the front of the line,
        if it is long) that moves a little slower than they walk, then the wide shot of the next find as they arrive
        (SHOT_HOLD s). Nobody jumps: every Keeper keeps walking his own path through the cuts."""
        T = self.F[i]
        walkers = [k for k in BH.ORDER if k != "lantern"]
        t0, t1 = T["walk"], T["reveal"]
        first, last, n = t1, t0, int((t1 - t0) / 0.05) + 1
        for k in walkers:
            r = self.R[k]
            xs = [r.at(t0 + j * 0.05) for j in range(n)]
            for j in range(1, n):
                if abs(xs[j] - xs[j - 1]) > 1.0:                     # 20 px/s
                    first, last = min(first, t0 + (j - 1) * 0.05), max(last, t0 + j * 0.05)
        c1, c2 = first + self.SHOT_HOLD, last - self.SHOT_HOLD
        cuts = [c1, c2]
        if c2 - c1 > self.SHOT_SPLIT:
            cuts = [c1, (c1 + c2) / 2, c2]
        return dict(cuts=cuts, walkers=walkers, span=(first, last))

    def _track(self, i, t, which):
        """The travelling shot: on the back of the line (which 0) or its front (1), moving with them."""
        sh = self._shots[i]

        def grp(tt):
            xs = sorted(self.R[k].at(tt) for k in sh["walkers"])
            g = xs if which == 0 else xs[-3:]                     # (the whole line)
            return sum(g) / len(g)
        ta = sh["cuts"][which]                                     # the shot starts on the group, then the camera
        z = self.TRACK_Z[which]                                    # follows a little slower: they walk on through it
        return grp(ta) + self.TRACK_FOLLOW[which] * (grp(t) - grp(ta)), G - 0.36 * 1080.0 / z, z

    def target(self, t):
        for a, b, x, y, z in getattr(self, "_reveal_close", ()):    # the bug just uncovered, close
            if a <= t < b:
                return x, y, z
        if DIG_CLOSE[0] <= t < DIG_CLOSE[1]:                        # the dig, close: Digs, the hole, the worm
            x0 = BH.FINDS[0]["x"] + 40.0
            z = 1.7
            return x0, G - 0.30 * 1080.0 / z, z
        for i, sh in getattr(self, "_shots", {}).items():
            T = self.F[i]
            cuts = sh["cuts"]
            if not (T["walk"] <= t < T["reveal"] - 1.0):
                continue
            if t < cuts[0]:                                        # setting off: the last find's wide shot, held
                x, _, z = self._wide(i - 1)
                return x, G - 0.36 * 1080.0 / z, z
            if t >= cuts[-1]:                                      # arriving: the next find's wide shot, held
                x, _, z = self._wide(i)
                return x, G - 0.36 * 1080.0 / z, z
            return self._track(i, t, 0 if len(cuts) == 2 or t < cuts[1] else 1)
        return super().target(t)


BACK_EDGE = 84.0                        # the path's back edge, above the walkers' line (G)
HANDLE_GRIP = (102.0, -105.0)           # the push bar's grip, off Wheels' middle and G (see _cart_handle)
LANE_Y, LANE_K = 74.0, 0.86                # the back lane: this much further up the path, drawn this much smaller
CART_HALF = 150.0                          # the cart's half width (its wheels and the open book's ends)


def lanes(trk, act="hunt"):
    """{kind: (ts, depth)} the back lane over time, from the Keepers' paths: when one Keeper's walk takes him past
    another, the one passing steps onto the back lane a second before (drawn behind, a little up the path and
    smaller) and back off it a second after. Glo floats above everyone and never needs it."""
    from .doorway import HALF_W
    kinds = {k: v for k, v in trk.get(act, {}).items() if k not in ("lantern", "_cart")}
    ts = next(iter(kinds.values()))[0]
    depth = {k: np.zeros_like(ts) for k in kinds}
    ks = sorted(kinds)
    cart = trk.get(act, {}).get("_cart")
    if cart is not None and "wheels" in kinds:                   # Wheels never drives through his own cart (advisor
        xw = kinds["wheels"][1]                                  # FK0022 r2): he goes round behind it, on the back
        xc = np.interp(ts, cart[0], cart[1])                     # lane, whenever he passes it
        mv = np.abs(np.gradient(xw - xc))
        bad = (np.abs(xw - xc) < 0.55 * HALF_W.get("wheels", 200) + CART_HALF) & (mv > 1e-3)
        i, n = 0, len(ts)
        while i < n:
            if not bad[i]:
                i += 1
                continue
            j = i
            while j + 1 < n and bad[j + 1]:
                j += 1
            ta, tb = ts[i], ts[j]
            u = np.clip(np.minimum((ts - (ta - 1.0)) / 0.9, ((tb + 1.0) - ts) / 0.9), 0.0, 1.0)
            depth["wheels"] = np.maximum(depth["wheels"], u * u * (3 - 2 * u))
            i = j + 1
    for a in range(len(ks)):
        for b in range(a + 1, len(ks)):
            p, q = ks[a], ks[b]
            xp, xq = kinds[p][1], kinds[q][1]
            k = 0.55
            gap = np.abs(xp - xq) - 0.82 * (HALF_W.get(p, 200) * k + HALF_W.get(q, 200) * k)
            bad = gap < 30.0                                             # with a little room to spare
            if not bad.any():
                continue
            i = 0
            n = len(ts)
            while i < n:
                if not bad[i]:
                    i += 1
                    continue
                j = i
                while j + 1 < n and bad[j + 1]:
                    j += 1
                lo, hi = max(0, i - 1), min(n - 1, j + 1)
                mover = p if abs(xp[hi] - xp[lo]) >= abs(xq[hi] - xq[lo]) else q
                ta, tb = ts[i], ts[j]
                u = np.clip(np.minimum((ts - (ta - 1.6)) / 0.9, ((tb + 1.6) - ts) / 0.9), 0.0, 1.0)
                depth[mover] = np.maximum(depth[mover], u * u * (3 - 2 * u))
                i = j + 1
    return {k: (ts, d) for k, d in depth.items() if d.any()}


LANES = {}


def lane(kind, t):
    v = LANES.get(kind)
    return 0.0 if v is None else float(np.interp(t, v[0], v[1]))


# ----------------------------------------------------------------------------------------------- the old Canvas API

class _Glow:
    def begin(self, cv):
        cv.glowing = True

    def end(self, cv):
        cv.glowing = False


GLOW = _Glow()


class OldCanvas:
    """The old Canvas calls (polygon / polyline / line / circle) painted flat on a page, through the camera (snap) or
    in screen units (snap None, origin ox, oy, scale k). bugs.py and the lens ground draw through it, so the bugs
    keep their checked field-guide shapes."""

    def __init__(self, pg, snap=None, k=1.0, ox=0.0, oy=0.0, alpha=1.0):
        self.pg, self.snap, self.k, self.ox, self.oy, self.alpha = pg, snap, k, ox, oy, alpha
        self.z = snap["zoom"] if snap is not None else k
        self.glowing = False

    def _p(self, x, y):
        if self.snap is not None:
            return project(self.snap, x, y)
        return self.ox + x * self.k, self.oy + y * self.k

    def _path(self, pts, closed=True):
        p = np.asarray(pts, np.float64).reshape(-1, 2)
        path = skia.Path()
        if len(p) < 2:
            return None
        path.moveTo(*self._p(*p[0]))
        for q in p[1:]:
            path.lineTo(*self._p(*q))
        if closed:
            path.close()
        return path

    @staticmethod
    def _c(col):
        return tuple(float(v) for v in np.clip(np.asarray(col, np.float64)[:3], 0, 255))

    def _paint(self, path, col):
        if self.glowing:
            self.pg.flat(path, self._c(col), 0.75 * self.alpha, blur=6 * self.z, blend=skia.BlendMode.kScreen)
        else:
            self.pg.flat(path, self._c(col), self.alpha)

    def polygon(self, pts, col):
        if len(pts) < 3:
            return
        self._paint(self._path(pts), col)

    def polyline(self, pts, col, width=2.0, closed=False):
        path = self._path(pts, closed)
        if path is not None:
            self.pg.stroke(path, self._c(col), width * self.z, self.alpha)

    def line(self, x0, y0, x1, y1, col, width=2.0):
        self.polyline([(x0, y0), (x1, y1)], col, width)

    def circle(self, x, y, r, col, fill=True, width=2.0):
        if r <= 0:
            return
        sx, sy = self._p(x, y)
        path = oval(sx, sy, r * self.z, r * self.z)
        if fill:
            self._paint(path, col)
        else:
            self.pg.stroke(path, self._c(col), width * self.z, self.alpha)

    def text(self, *a, **kw):
        pass


def bug(pg, snap, kind, x, y, L, heading=0.0, t=0.0, gait=0.0, alpha=1.0, **kw):
    if "glow" in kw:
        kw["glow"] = GLOW
    draw_bug(OldCanvas(pg, snap, alpha=alpha), kind, x, y, L, heading, t, gait, **kw)


def bug_screen(pg, kind, x, y, L, heading=0.0, alpha=1.0):
    draw_bug(OldCanvas(pg, None, 1.0, alpha=alpha), kind, x, y, L, heading, 0.0, 0.25)


# ----------------------------------------------------------------------------------------------- helpers

def act_time(snap, act):
    return snap["lt"] / getattr(act, "STRETCH", 1.0) - act.LEAD


def P(snap, x, y):
    return project(snap, x, y)


def path_of(snap, pts, closed=True):
    q = [P(snap, *p) for p in pts]
    return _poly(q) if closed else _open(q)


def _open(q):
    p = skia.Path()
    p.moveTo(*q[0])
    for r in q[1:]:
        p.lineTo(*r)
    return p


def world_oval(snap, x, y, rx, ry, rot=0.0):
    sx, sy = P(snap, x, y)
    z = snap["zoom"]
    return oval(sx, sy, rx * z, ry * z, rot)


def half_oval(snap, x, y, rx, ry, top=True, n=24):
    a0, a1 = (math.pi, 2 * math.pi) if top else (0.0, math.pi)
    pts = [(x + rx * math.cos(a), y + ry * math.sin(a)) for a in np.linspace(a0, a1, n)]
    return path_of(snap, pts)


# ----------------------------------------------------------------------------------------------- the forest

def _forest(pg, snap, t):
    W, H = snap["W"], snap["H"]
    vx0, vx1 = TF._view_x(snap)
    z = snap["zoom"]
    TF._sky(pg, snap, t)
    TF._hills(pg, snap, 0.35, G - 380, 160, FOR["far"], 3)
    TF._hills(pg, snap, 0.55, G - 250, 120, FOR["far2"], 5)
    pg.begin_grain()
    for j, x in enumerate(np.arange(-2400, 13500, 300)):               # far woods (parallax)
        bx0, bx1 = TF._view_x(snap, 0.8)
        if bx0 - 400 < x < bx1 + 400:
            sx, sy = project(snap, x, G - 40, 0.8)
            h = (560 + 90 * ((j * 7) % 4)) * z * 0.8
            if j % 3 == 1:
                pine(pg, sx, sy, h * 1.1, FOR["back"], tone(FOR["trunk"], -0.3))
            else:
                lolly_tree(pg, sx, sy, h, FOR["back2"], tone(FOR["trunk"], -0.3))
    # the path has depth (advisor FK0022 r3: the stone, the log and the back lane stood "up the path" on nothing):
    # the ground starts at its back edge, BACK_EDGE above the line the walkers' feet are on
    _box(pg, snap, vx0 - 300, G - BACK_EDGE, vx1 + 300, G + 900, FOR["ground"], 0.0)
    _box(pg, snap, vx0 - 300, G - BACK_EDGE - 2, vx1 + 300, G - BACK_EDGE + 14, FOR["ground2"], 0.0)
    _box(pg, snap, vx0 - 300, G - BACK_EDGE + 30, vx1 + 300, G - 4, FOR["path"], 0.0, alpha=0.22)
    _box(pg, snap, vx0 - 300, G + 40, vx1 + 300, G + 120, FOR["path"], 0.0, alpha=0.35)
    for j, x in enumerate(np.arange(-600, 12000, 520)):               # the forest along the path (old tree spots)
        if vx0 - 500 < x < vx1 + 500:
            tx = x + 90 * math.sin(j * 1.7)
            h = 700 + 140 * ((j * 7) % 3)
            sx, sy = P(snap, tx, G - BACK_EDGE + 6)                   # (they stand at the path's back edge)
            pg.c.save()                                                # the trunk's round end is cut at the ground
            pg.c.clipRect(skia.Rect(-1e5, -1e5, 1e5, sy))              # (advisor r3: trunks poked out below it)
            lolly_tree(pg, sx, sy + 12 * z, h * 1.25 * z, FOR["leaf"] if j % 2 else FOR["mid2"], FOR["trunk"])
            pg.c.restore()
    for j, x in enumerate(np.arange(-300, 12000, 380)):               # low bushes along the path
        if vx0 - 300 < x < vx1 + 300 and all(abs(x - f["x"]) > 260 for f in BH.FINDS):
            r = 70 + 20 * ((j * 3) % 3)
            sx, sy = P(snap, x, G)
            flat_bush(pg, sx, sy, r * z, FOR["leaf2"] if j % 2 else FOR["leaf"])
    o = P(snap, 0.0, 0.0)
    pg.end_grain(o[0], o[1])
    TF.night_tint(pg)


# ----------------------------------------------------------------------------------------------- the hiding places

def _soil(pg, snap, act, j, t, u, T):
    x = BH.FINDS[j]["x"]
    out = u * (1 - act.restore_u(j, t))
    pg.shape(half_oval(snap, x - 40, G, 70, 22), FOR["soil"], 0.08)
    pg.shape(half_oval(snap, x + 50, G, 60, 18), FOR["soil2"], 0.08)
    pg.flat(world_oval(snap, x, G - 2, 20, 7), FOR["soil_in"])
    if out > 0.0:                                 # it comes out of the hole and goes back in head first: the part
        L = 120.0                                 # still in the hole (right of it, on Digs' side) is hidden, nothing
        wx = x - L / 2 + (1 - out) * L            # pops; it comes out on the open side, away from his shovels
        hx, _ = P(snap, x + 4, G)
        c = pg.c
        c.save()
        c.clipRect(skia.Rect(-1e5, -1e5, hx, 1e5))
        bug(pg, snap, "earthworm", wx, G - 8, L, math.pi + 0.05, t, t * 0.8)
        c.restore()
    pg.flat(half_oval(snap, x - 14, G + 2, 26, 8, top=False), FOR["soil"])


def _log(pg, snap, act, j, t, u, T):
    x = BH.FINDS[j]["x"]
    lx, ly, r = act.log_xy(j, t)
    home = smoothstep(seg(t, T["home"][0], T["home"][1]))
    for q, (bx, ph) in enumerate(((x - 20, 0.0), (x + 22, 1.3))):     # the same two as in the lens
        if u > 0.5:                                                    # home: in under the log where it now lies
            hx = lerp(bx, x - 158 + 16 * q, home)
            hy = lerp(G - 7, G - 46, home)
            hd = math.atan2(hy - (G - 7), hx - bx) if home > 0.0 else 0.0
            roll = 0.0                                             # the first curls up when its log goes, and
            if q == 0:                                             # unrolls under the glass (as the card says)
                roll = smoothstep(seg(t, T["reveal"] + 3.6, T["reveal"] + 4.2)) *                     (1 - smoothstep(seg(t, T["lens"] + 6.0, T["lens"] + 9.0)))
            bug(pg, snap, "pillbug", hx, hy, 26, hd, t, (t * 1.5 + ph) * (1 - roll), roll=roll)
    z = snap["zoom"]
    pg.shape(world_oval(snap, lx, ly, r, r), FOR["bark"], 0.1)
    pg.flat(world_oval(snap, lx, ly, r * 0.84, r * 0.84), FOR["wood"])
    for q in (0.3, 0.52, 0.72):
        sx, sy = P(snap, lx + 3, ly + 2)
        pg.stroke(oval(sx, sy, r * q * z, r * q * 0.95 * z), FOR["ring"], 2.2 * z)
    rot = (lx - x) / r                                         # rolling right turns it clockwise (y down)
    for q in range(3):
        a = rot + q * 2.1
        pg.stroke(path_of(snap, [(lx + math.cos(a) * r * 0.2, ly + math.sin(a) * r * 0.2),
                                 (lx + math.cos(a) * r * 0.78, ly + math.sin(a) * r * 0.78)], False),
                  tone(FOR["ring"], -0.1), 3 * z)


def _bark(pg, snap, act, j, t, u, T):
    x = BH.FINDS[j]["x"]
    z = snap["zoom"]
    sx, top = x, G - 170
    pg.shape(path_of(snap, [(sx - 105, top), (sx + 105, top), (sx + 105, G), (sx - 105, G)]), FOR["bark"], 0.1)
    pg.flat(world_oval(snap, sx, top, 105, 26), FOR["wood"])
    for q in (0.35, 0.65, 0.9):
        cx, cy = P(snap, sx, top)
        pg.stroke(oval(cx, cy, 105 * q * z, 26 * q * z), FOR["ring"], 2 * z)
    for q in range(6):
        bx = sx - 90 + q * 36
        pg.stroke(path_of(snap, [(bx, top + 30), (bx + 6, G - 10)], False), tone(FOR["bark"], -0.18), 3.5 * z)
    pg.flat(path_of(snap, [(sx - 78, G - 150), (sx + 50, G - 150), (sx + 50, G - 12), (sx - 78, G - 12)]),
            FOR["wood"])
    op = act.bark_open(j, t) if t > T["walk"] - 1.0 else 0.0
    if t > T["walk"] - 1.0:                                    # the millipede is there all along, under the bark
        bx, by, hd, dist = act.milli(j, t)                     # (and goes home over the top: clipped to the stump)
        c = pg.c
        c.save()
        sil = path_of(snap, [(sx - 105, top), (sx + 105, top), (sx + 105, G), (sx - 105, G)])
        sil.addPath(world_oval(snap, sx, top, 105, 26))
        c.clipPath(sil, doAntiAlias=True)
        bug(pg, snap, "millipede", bx, by, MILLI["L"], hd, t, dist / 12.0)
        c.restore()
    bot, hh, dx = act.bark_slab(op)                            # the loose slab: lifted up by Twigs, then lying on
    col = tone(FOR["bark"], 0.08)                              # the stump's top (it stays there)
    a0, a1 = sx - 80 + dx, sx + 52 + dx
    pg.shape(path_of(snap, [(a0, bot - hh), (a1, bot - hh), (a1, bot), (a0, bot)]), col, 0.06)
    if hh > 40.0:                                              # its bark grooves (foreshortened as it tips)
        for q in range(4):
            pg.stroke(path_of(snap, [(a0 + 14 + q * 34, bot - hh + 8), (a0 + 16 + q * 34, bot - 6)], False),
                      tone(FOR["bark"], -0.12), 3 * z)
    else:                                                      # lying on the top: its edge, a little darker
        pg.flat(path_of(snap, [(a0, bot - 5), (a1, bot - 5), (a1, bot), (a0, bot)]), tone(FOR["bark"], -0.12))


def bark_h(op):
    """How high the loose bark's top edge stands above its foot (hinged there, swinging down towards us):
    138 shut, then lower and lower, then below the hinge (lying flat in front, its inside up)."""
    return 138.0 * math.cos(op * (math.pi / 2 + 0.3))


def beetle_xy(act, j, t):
    """(x, y, heading, gait) of the real ground beetle at the stone: under it once it is tipped up; it scurries out
    to the front before Wheels sets the stone down, waits, and walks back in under its edge."""
    T = act.F[j]
    x = BH.FINDS[j]["x"]
    gy = G - ROCK["back"]
    h0, h1 = T["home"]
    a = (x - 10 + 18 * math.sin(min(t, h0) * 0.7), gy - 6)
    b = (x + 95, G + 6)
    e = (x + 26, gy - 5)
    def face(tt):                                   # turns round smoothly at each end of its little wander
        return math.pi * smoothstep(seg(-math.cos(tt * 0.7), -0.3, 0.3))
    if t < h0:
        return a[0], a[1], face(t), t * 2.5
    if t < h0 + 1.4:
        u = smoothstep(seg(t, h0, h0 + 1.4))
        h_a, h_s = face(h0), math.atan2(b[1] - a[1], b[0] - a[0])
        d = (h_s - h_a + math.pi) % (2 * math.pi) - math.pi
        hd = h_a + d * smoothstep(seg(t, h0, h0 + 0.35))
        return lerp(a[0], b[0], u), lerp(a[1], b[1], u), hd, h0 * 2.5 + 6 * u
    back = math.atan2(e[1] - b[1], e[0] - b[0])
    if t < h1 + 0.6:
        w = smoothstep(seg(t, h1 - 0.4, h1 + 0.6))
        out = math.atan2(b[1] - a[1], b[0] - a[0])
        return b[0], b[1], out + (back - out) * w, h0 * 2.5 + 6
    u = smoothstep(seg(t, h1 + 0.6, h1 + 3.0))
    return lerp(b[0], e[0], u), lerp(b[1], e[1], u), back, h0 * 2.5 + 6 + 5 * u


def _rock(pg, snap, act, j, t, u, T):
    x = BH.FINDS[j]["x"]
    ang = act.rock_ang(j, t)
    rx_, ry_, bk = ROCK["rx"], ROCK["ry"], ROCK["back"]
    gy = G - bk                                                  # where it sits: a little up the path
    if ang > 0.05 or (T["reveal"] <= t < T["home"][1]):
        pg.flat(world_oval(snap, x, gy - 2, rx_ * 0.9, 9), FOR["soil_in"], 0.8)    # the damp patch under it
    if t >= T["reveal"]:
        bx, by, hd, g = beetle_xy(act, j, t)
        bug(pg, snap, "groundbeetle", bx, by, 28, hd, t, g)
    px, py = act.rock_xy(j)                                      # the left edge lifts about the right foot
    ca, sa = math.cos(ang), math.sin(ang)                      # clockwise (y down): the left edge comes up

    def rp(qx, qy):
        dx, dy = qx - px, qy - py
        return px + dx * ca - dy * sa, py + dx * sa + dy * ca

    def rock_oval(cx, cy, rx, ry, n=36, lump=0.0):
        return [rp(cx + rx * math.cos(a) * (1 + lump * (0.6 * math.sin(3 * a) + 0.4 * math.sin(5 * a + 1.0))),
                   cy + ry * math.sin(a) * (1 + lump * (0.6 * math.sin(3 * a) + 0.4 * math.sin(5 * a + 1.0))))
                for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]
    body = smooth([P(snap, *q) for q in rock_oval(x, gy - ry_, rx_, ry_, 48, lump=0.09)])
    pg.shape(body, FOR["rock"], 0.22)                           # a solid, lumpy stone with a dark edge (advisor r3:
    pg.stroke(body, tone(FOR["rock3"], -0.25), 3.0 * snap["zoom"])   # the pale even oval read as a glass disc)
    pg.flat(smooth([P(snap, *q) for q in rock_oval(x + 4, gy - ry_ * 0.45, rx_ * 0.86, ry_ * 0.42, 24)]), FOR["rock3"],
            0.7)                                                                                     # its underside
    pg.flat(smooth([P(snap, *q) for q in rock_oval(x - 12, gy - ry_ * 1.35, rx_ * 0.62, ry_ * 0.42, 24)]),
            FOR["rock2"])
    for cx_, cy_, r_ in ((x + 22, gy - ry_ * 1.1, 6), (x - 34, gy - ry_ * 0.8, 5)):                   # a few pits
        pg.flat(smooth([P(snap, *q) for q in rock_oval(cx_, cy_, r_, r_ * 0.6, 12)]), FOR["rock3"], 0.6)


def _plant(pg, snap, act, j, t, u, T):
    x = BH.FINDS[j]["x"]
    G = BF_G - PLANT_BACK                      # up the path: everyone passes in front of it (advisor r3)
    z = snap["zoom"]
    px = x + 15
    sway = 0.04 * math.sin(t * 1.1) + 0.12 * BH.bump(t, T["reveal"] + 1.0, 1.5)
    pg.stroke(path_of(snap, [(px, G), (px + 200 * sway * 0.5, G - 125), (px + 200 * sway, G - 250)], False),
              FOR["stem"], 6 * z)
    for q in range(6):
        h = 50 + q * 34
        bx = px + 200 * sway * h / 250
        sgn = 1 if q % 2 else -1
        lc = FOR["plant"] if q % 2 else FOR["plant2"]
        pg.shape(world_oval(snap, bx + sgn * 34, G - h - 6, 40, 13, -sgn * 8), lc, 0.08)
        pg.stroke(path_of(snap, [(bx, G - h), (bx + sgn * 70, G - h - 10)], False), tone(lc, 0.2), 2 * z)
    if u > 0.2:                                   # under the glass it climbs the stalk to the aphids (it eats them)
        up = smoothstep(seg(t, T["lens"] + 5.0, T["lens"] + 10.0))
        h = 172.0 + 22.0 * up
        climbing = BH.bump(t, T["lens"] + 7.5, 5.0)
        bug(pg, snap, "ladybug", px + 200 * sway * h / 250 + 12 - 6 * up, G - h, 17, -1.1 * climbing, t,
            t * (0.3 + 0.7 * climbing))
    for q in range(3):
        BH.aphid(OldCanvas(pg, snap), px + 200 * sway * 0.8 - 4 + 8 * q, G - 200 - 6 * q, 5, t)


def _ferns(pg, snap, act, j, t, u, T):
    x = BH.FINDS[j]["x"]
    G = BF_G - PLANT_BACK                      # (likewise: nobody walks through the ferns)
    z = snap["zoom"]
    for q in range(7):
        a = -math.pi / 2 + (q - 3) * 0.32
        L = 150 + 25 * (q % 3)
        pts = [(x + math.cos(a) * L * w + 30 * w * w * (q - 3) / 3, G + math.sin(a) * L * w + 40 * w * w)
               for w in np.linspace(0, 1, 10)]
        col = FOR["fern"] if q % 2 else FOR["fern2"]
        pg.stroke(path_of(snap, pts, False), tone(col, -0.1), 4 * z)
        for (ax, ay), (bx, by) in zip(pts[1:-1], pts[2:]):
            for sgn in (-1, 1):
                lp = [(ax, ay), (ax + sgn * 18 - (bx - ax) * 0.3, ay + 8)]
                pg.stroke(path_of(snap, lp, False), col, 5 * z)
    if u > 0.3:
        lit = 0.55 + 0.45 * math.sin(t * 2.4)                 # one real firefly on a frond, big enough to see
        bug(pg, snap, "firefly", x + 30, G - 96, 22, 0.3, t, 0.0, glow=True, light=0.35 + 0.65 * lit ** 2)


PLACES = dict(soil=_soil, log=_log, bark=_bark, rock=_rock, plant=_plant, ferns=_ferns)


def _place(pg, snap, act, j, t):
    f = BH.FINDS[j]
    T = act.F[j]
    u = act.reveal_u(j, t) if t > T["walk"] - 1 else 0.0
    if t < T["walk"] - 1 and j > 0:
        u = 0.0
    PLACES[f["place"]](pg, snap, act, j, t, u, T)


# ----------------------------------------------------------------------------------------------- the cart, the book

BOOK_Y = BH.BOOK_Y


def _cart(pg, snap, x, wheel_rot):
    z = snap["zoom"]
    wy = G - 22
    for wx in (x - 90, x + 90):
        pg.shape(world_oval(snap, wx, wy, 22, 22), FOR["cart2"], 0.08)
        pg.flat(world_oval(snap, wx, wy, 15, 15), FOR["cart"])
        for i in range(4):
            a = wheel_rot + i * math.pi / 2
            pg.stroke(path_of(snap, [(wx, wy), (wx + 14 * math.cos(a), wy + 14 * math.sin(a))], False),
                      FOR["cart2"], 3 * z)
        pg.flat(world_oval(snap, wx, wy, 4, 4), tone(FOR["cart2"], -0.2))
    _box(pg, snap, x - 110, G - 52, x + 110, G - 36, FOR["cart"], 0.06, r=4)
    _box(pg, snap, x - 12, G - 150, x + 12, G - 44, FOR["cart2"], 0.06)
    pg.shape(path_of(snap, [(x - 170, BOOK_Y + 88), (x + 170, BOOK_Y + 88), (x + 160, BOOK_Y + 104),
                            (x - 160, BOOK_Y + 104)]), FOR["cart"], 0.06)


def _cart_handle(pg, snap, x):
    """The push bar at the cart's back end, where Wheels' right pincer holds it (drawn behind him, so the pincer
    closes round it; the old handle ran up across his face)."""
    z = snap["zoom"]
    w = x - BH.PUSH                                  # Wheels' middle: his right pincer closes about +93..+111
    pg.stroke(path_of(snap, [(x - 110, G - 44), (w + 101, G - 104)], False), FOR["cart2"], 9 * z)
    pg.stroke(path_of(snap, [(w + 93, G - 102), (w + 111, G - 108)], False), FOR["cart"], 11 * z)


def _closed_book(pg, snap, x):
    z = snap["zoom"]
    y0, y1 = BOOK_Y - 86, BOOK_Y + 86
    pg.shape(path_of(snap, [(x - 4, y0 - 4), (x + 160, y0 - 4), (x + 164, y1 + 8), (x - 4, y1 + 8)]), FOR["cover2"],
             0.0)
    pg.shape(path_of(snap, [(x, y0), (x + 152, y0), (x + 152, y1), (x, y1)]), FOR["cover"], 0.08)
    sx, sy = P(snap, x + 76, y0 + 40)
    _text(pg, "FIELD GUIDE", sx, sy, 15 * z, FOR["paper"])
    lx, ly = P(snap, x + 76, BOOK_Y + 20)
    _leaf_icon(pg, lx, ly, z)


def _leaf_icon(pg, x, y, z):
    pg.flat(oval(x, y, 18 * z, 32 * z), "#c8bf6a")
    pg.stroke(_open([(x, y - 28 * z), (x, y + 30 * z)]), "#968e48", 3 * z)


def _book(pg, snap, act, x, t):
    """The open Keeper Field Guide: the pages, and one sheet turning right to left. Every sheet is printed on both
    faces (advisor FK0022 r1): its front keeps the old right page as it lifts, its back carries the new left page as
    it lands, and nothing appears on a page before the sheet that carries it has landed. The cover is one sheet too
    (outside: FIELD GUIDE; inside: the checklist's left page)."""
    z = snap["zoom"]
    y0, y1 = BOOK_Y - 86, BOOK_Y + 86
    p, u = act._book_page(t)
    a, b = p if isinstance(p, tuple) else (p, p)
    left_page = a if u is not None else b                     # under the turning sheet: the old left page
    has_left = left_page != -1
    pg.shape(path_of(snap, [(x - (160 if has_left else 4), y0 - 4), (x + 160, y0 - 4), (x + 164, y1 + 8),
                            (x - (164 if has_left else 4), y1 + 8)]), FOR["cover2"], 0.0)
    for side in ((-1, 1) if has_left else (1,)):
        xa, xb = (x - 150, x - 4) if side < 0 else (x + 4, x + 150)
        pg_ = left_page if side < 0 else b
        if pg_ != -1:
            pts = [(xa, y0 + (6 if side < 0 else 0)), (xb, y0 + (0 if side < 0 else 6)), (xb, y1), (xa, y1)]
            pg.flat(path_of(snap, pts), FOR["paper"])
            pg.stroke(path_of(snap, [(x + side * 6, y0 + 4), (x + side * 6, y1)], False), FOR["paper2"], 4 * z)
        _page(pg, snap, act, t, side, xa, xb, y0, y1, pg_)
    pg.stroke(path_of(snap, [(x, y0), (x, y1 + 4)], False), tone(FOR["cover2"], -0.2), 3 * z)
    if u is None:
        return
    w = 146 * math.cos(math.pi * u)
    lift = 26 * math.sin(math.pi * u)
    tip = x + w
    front = u < 0.5
    face = (FOR["cover"] if a == -1 else FOR["paper"]) if front else FOR["paper"]
    col = tuple(np.array(TF.C_rgb(face)) * (0.84 + 0.16 * abs(math.cos(math.pi * u))))
    sheet = path_of(snap, [(x, y0), (tip, y0 - lift), (tip, y1 - lift * 0.4), (x, y1)])
    pg.flat(sheet, col)
    sc = abs(math.cos(math.pi * u))
    if sc > 0.04:                                             # its printing, foreshortened with the sheet
        c = pg.c
        c.save()
        c.clipPath(sheet, doAntiAlias=True)
        spx, spy = P(snap, x, BOOK_Y)
        c.translate(spx, spy)
        c.scale(sc, 1.0)
        c.translate(-spx, -spy)
        if front:
            _page(pg, snap, act, t, 1, x + 4, x + 150, y0, y1, a)
        else:
            _page(pg, snap, act, t, -1, x - 150, x - 4, y0, y1, b)
        c.restore()
    pg.stroke(path_of(snap, [(tip, y0 - lift), (tip, y1 - lift * 0.4)], False), FOR["paper2"], 2 * z)


def page_tip(act, x, t):
    """Where the turning sheet's free corner is now (for Glo's light), or None."""
    u = act._flip(t)
    if u is None:
        return None
    return x + 146 * math.cos(math.pi * u), BOOK_Y - 86 - 26 * math.sin(math.pi * u) + 24


def _lines(pg, snap, xa, xb, y, n, w=0.8):
    z = snap["zoom"]
    for i in range(n):
        L = (xb - xa - 30) * (w if i < n - 1 else 0.55)
        pg.stroke(path_of(snap, [(xa + 15, y + i * 14), (xa + 15 + L, y + i * 14)], False), FOR["paper2"], 3 * z)


def _page(pg, snap, act, t, side, xa, xb, y0, y1, p):
    z = snap["zoom"]
    mx = (xa + xb) / 2
    if p == -1:
        if side < 0:
            return
        pg.flat(path_of(snap, [(xa, y0), (xb, y0), (xb, y1), (xa, y1)]), FOR["cover"])
        if side > 0:
            sx, sy = P(snap, mx, y0 + 46)
            _text(pg, "FIELD GUIDE", sx, sy, 15 * z, FOR["paper"])
            lx, ly = P(snap, mx, (y0 + y1) / 2 + 20)
            _leaf_icon(pg, lx, ly, z)
        return
    if p == 0:
        return _checklist(pg, snap, act, t, side, xa, xb, y0, y1)
    if p >= 7:
        if side < 0:
            pg.flat(world_oval(snap, mx, (y0 + y1) / 2, 46, 30), FOR["paper2"])
        else:
            _lines(pg, snap, xa, xb, y0 + 30, 7)
        return
    i = p - 1
    kind = BH.FINDS[i]["kind"]
    if side < 0:
        L = 120 if kind in ("earthworm", "millipede") else 84
        bug(pg, snap, kind, mx, (y0 + y1) / 2 + 6, L, -0.5 if L > 100 else -1.57, 0.0, 0.25)
    else:
        name = BUGS[kind]["name"].split(" (")[0]
        sx, sy = P(snap, mx, y0 + 32)
        _text(pg, name.upper(), sx, sy, (15 if len(name) > 10 else 18) * z, FOR["ink"])
        _lines(pg, snap, xa, xb, y0 + 52, 5)
        bx, by = xb - 32, y1 - 30                                                 # the tick box
        pg.stroke(path_of(snap, [(bx - 14, by - 14), (bx + 14, by - 14), (bx + 14, by + 14), (bx - 14, by + 14)]),
                  tone(FOR["ink"], 0.2), 2 * z)
        tk = smoothstep(seg(t, act.F[i]["tick"], act.F[i]["tick"] + 0.5))
        _tick(pg, snap, bx, by, tk)


def _tick(pg, snap, bx, by, tk):
    if tk <= 0:
        return
    z = snap["zoom"]
    p1, p2, p3 = (bx - 10, by), (bx - 3, by + 9), (bx + 14, by - 14)
    if tk < 0.4:
        q = [p1, (lerp(p1[0], p2[0], tk / 0.4), lerp(p1[1], p2[1], tk / 0.4))]
    else:
        v = (tk - 0.4) / 0.6
        q = [p1, p2, (lerp(p2[0], p3[0], v), lerp(p2[1], p3[1], v))]
    pg.stroke(path_of(snap, q, False), FOR["tick"], 5 * z)


def _checklist(pg, snap, act, t, side, xa, xb, y0, y1):
    z = snap["zoom"]
    mx = (xa + xb) / 2
    if side < 0:
        sx, sy = P(snap, mx, y0 + 42)
        _text(pg, "BUG HUNT", sx, sy, 22 * z, FOR["ink"])
        sx, sy = P(snap, mx, y0 + 68)
        _text(pg, "find all six!", sx, sy, 13 * z, tone(FOR["ink"], 0.25), weight="Medium")
        bug(pg, snap, "ladybug", mx, y1 - 52, 46, -1.57, 0.0, 0.25)
        return
    n = act.found(t)
    for q in range(6):
        cx = xa + 30 + (q % 3) * 45
        cy = y0 + 46 + (q // 3) * 78
        pg.stroke(path_of(snap, [(cx - 20, cy - 30), (cx + 20, cy - 30), (cx + 20, cy + 30), (cx - 20, cy + 30)]),
                  tone(FOR["ink"], 0.25), 2 * z)
        if q < n:
            kind = BH.FINDS[q]["kind"]
            L = 52 if kind in ("earthworm", "millipede") else 30
            bug(pg, snap, kind, cx, cy, L, -1.57, 0.0, 0.25)
        else:
            sx, sy = P(snap, cx, cy + 9)
            _text(pg, "?", sx, sy, 24 * z, tone(FOR["ink"], 0.35))


# ----------------------------------------------------------------------------------------------- Glo: light, lens, flare

def _lamp(act):
    gl = act.m("lantern")
    return (gl.x, gl.y - 120) if gl is not None else None


def _glo_pool(pg, snap, act):
    gl = act.m("lantern")
    if gl is None:
        return
    k = 0.8 * (gl.lamp if gl.lamp is not None else 1.0)
    z = snap["zoom"]
    sx, sy = P(snap, gl.x, G - 10)
    pg.flat(oval(sx, sy, 380 * z, 90 * z), FOR["lamp"], 0.16 * k, blur=40 * z, blend=skia.BlendMode.kScreen)
    lx, ly = P(snap, *_lamp(act))
    pg.glow(lx, ly + 60 * z, 330 * z, FOR["lamp"], 0.22 * k)


def _lens(pg, snap, act, i, T, t, lx):
    vx0, vx1 = TF._view_x(snap)
    if not (vx0 - 300 < lx < vx1 + 300):
        return
    z = snap["zoom"]
    R = BH.LENS_R
    gl = act.m("lantern")
    y = (gl.y + (BH.LENS_Y - BH.GLO_Y)) if gl is not None else BH.LENS_Y + act.lens_drop(t)   # it moves with Glo
    view = smoothstep(seg(t, T["lens"] + 2.0, T["lens"] + 4.0)) * (1 - smoothstep(seg(t, T["out"], T["out"] + 2.0)))
    cx, cy = P(snap, lx, y)
    M = 1.0 + (LOOK_M[BH.FINDS[i]["place"]] - 1.0) * view
    if M > 1.002:                                             # the real scene behind the glass, M times as big
        c = pg.c
        c.save()
        c.clipPath(oval(cx, cy, R * z, R * z), doAntiAlias=True)
        mag = dict(snap, zoom=z * M, cx=lx - (lx - snap["cx"]) / M, cy=y - (y - snap["cy"]) / M)
        pg.zoom = z * M
        _scene(pg, mag, act, t)
        pg.zoom = z
        c.restore()
    pg.flat(oval(cx, cy, R * z, R * z), FOR["lens"], 0.07)                       # the glass, a faint tint
    pg.stroke(oval(cx, cy + 10 * z, (R + 10) * z, (R + 10) * z), "#14161c", 12 * z, 0.25, blur=6 * z)   # rim shadow
    top = (gl.y - 120 + 26) if gl is not None else y - R - 70                  # just under Glo's lantern
    pg.stroke(path_of(snap, [(lx, top), (lx, y - R - 14)], False), FOR["cart"], 16 * z)          # handle, to the rim
    pg.stroke(path_of(snap, [(lx - 5, top + 4), (lx - 5, y - R - 18)], False), tone(FOR["cart"], 0.25), 4 * z)
    if gl is not None:                                        # two of Glo's tendrils, from under his dome, wrap it
        for sgn, dy in ((-1, 16), (1, 30)):
            pts = [(lx + sgn * 26, top - 22), (lx + sgn * 30, top - 2), (lx + sgn * 14, top + dy - 6),
                   (lx - sgn * 10, top + dy), (lx - sgn * 12, top + dy + 8)]
            pg.stroke(path_of(snap, pts, False), tone(GLO_TEAL, -0.12), 9 * z)
            pg.stroke(path_of(snap, pts, False), GLO_TEAL, 6 * z)
    pg.stroke(oval(cx, cy, (R + 10) * z, (R + 10) * z), FOR["brass2"], 14 * z)
    pg.stroke(oval(cx, cy, (R + 10) * z, (R + 10) * z), FOR["brass"], 8 * z)
    sheen = skia.Path()
    sheen.addArc(skia.Rect(cx - 30 * z - R * 0.62 * z, cy - 34 * z - R * 0.5 * z, cx - 30 * z + R * 0.62 * z,
                           cy - 34 * z + R * 0.5 * z), math.degrees(3.6), math.degrees(1.0))
    pg.stroke(sheen, FOR["lens"], 5 * z, 0.55)


def _close_view(pg, snap, act, i, T, t, lx, y):
    f = BH.FINDS[i]
    kind = f["kind"]
    oc = OldCanvas(pg, snap)
    BH.lens_ground(oc, lx, y, BH.LENS_R, f["place"], 300 + i)
    tt = t - T["lens"]
    if kind == "earthworm":
        bug(pg, snap, kind, lx - 18 + 1.2 * tt, y + 10, 205, -0.18, t, tt * 0.7)
    elif kind == "pillbug":
        roll = 1.0 - smoothstep(seg(tt, 4.0, 7.0))
        bug(pg, snap, kind, lx + 30, y + 40, 90, 2.6, t, 0.0)
        hd = -0.3 + 0.2 * math.sin(tt * 0.3)
        gait = max(0.0, tt - 7.0) * 1.4
        bug(pg, snap, kind, lx - 20 + max(0.0, tt - 7.0) * 9, y - 20, 120, hd, t, gait, roll=roll)
    elif kind == "millipede":                                 # the real one under the glass, magnified
        bx, by, hd, dist = act.milli(i, t)
        bug(pg, snap, kind, lx + LENS_M * (bx - lx), y + LENS_M * (by - y), MILLI["L"] * LENS_M, hd, t, dist / 12.0)
    elif kind == "groundbeetle":
        k, run = int(tt // 6.0), tt % 6.0
        d = 1.0 if k % 2 == 0 else -1.0
        want = 0.0 if d > 0 else math.pi
        prev = want if k == 0 else (math.pi if d > 0 else 0.0)
        hd = prev + (want - prev) * smoothstep(seg(run, 0.0, 1.2)) + 0.15 * math.sin(tt * 0.5)   # turns round
        go = smoothstep(seg(run, 1.2, 1.6)) * (1 - smoothstep(seg(run, 3.4, 3.8)))
        x0 = lx - d * 30 + d * 60 * smoothstep(seg(run, 1.2, 3.8))                               # then walks over
        bug(pg, snap, kind, x0, y + 10, 150, hd, t, tt * 2.2 * go + 0.25)
    elif kind == "ladybug":
        for ax, ay in ((45, -40), (70, -10), (60, 30)):
            BH.aphid(oc, lx + ax, y + ay, 30, t)
        bug(pg, snap, kind, lx - 40 + 2.5 * tt, y + 5 - 0.6 * tt, 110, -0.2, t, tt * 1.1)
    elif kind == "firefly":
        lit = 0.5 + 0.5 * math.sin(tt * 2.2 - 1.0)
        bug(pg, snap, kind, lx - 10, y + 10, 150, -0.5, t, 0.0, glow=True, light=lit ** 2, glow_r=0.16)


def _flare(pg, snap, act, T, t):
    """Glo's light turns the pages and ticks the box: a soft beam from his lantern to the book, sparkles down it."""
    cx = act.cart_x(t)
    g = 0.0
    for ft, a, b in act._flips_cache():
        g = max(g, BH.bump(t, ft - 0.3, 1.4))
    g = max(g, BH.bump(t, T["tick"] - 0.3, 1.2), BH.bump(t, act.F[0]["open"] - 0.3, 1.3))
    lamp = _lamp(act)
    if g <= 0.01 or lamp is None:
        return
    z = snap["zoom"]
    tip = page_tip(act, cx, t)
    if tip is not None:                                       # the light holds the turning sheet's corner
        tx, ty = tip
    elif abs(t - T["tick"] - 0.25) < 1.0:                     # the light ticks the box
        tx, ty = cx + 150 - 32, BOOK_Y + 86 - 30
    else:                                                     # (about to lift the next sheet's corner)
        tx, ty = cx + 146, BOOK_Y - 62
    lx, ly = lamp
    pg.flat(path_of(snap, [(lx - 24, ly + 28), (lx + 24, ly + 28), (tx + 22, ty), (tx - 22, ty)]), FOR["lamp"],
            0.3 * g, blur=8 * z, blend=skia.BlendMode.kScreen)
    sx, sy = P(snap, tx, ty)
    pg.glow(sx, sy, (50 + 30 * g) * z, FOR["lamp"], 0.85 * g)
    pg.flat(oval(sx, sy, 9 * z, 9 * z), FOR["lamp"], 0.9 * g)
    ts = snap["t"]
    for q in range(9):
        u = (ts * 0.9 + q / 9) % 1.0
        px = lerp(lx, tx, u) + 14 * math.sin(7.0 * u + q * 2.1) * (1 - u)
        py = lerp(ly + 28, ty, u)
        tw = 0.6 + 0.4 * math.sin(ts * 11 + q * 1.7)
        qx, qy = P(snap, px, py)
        pg.flat(oval(qx, qy, 3.5 * z, 3.5 * z), FOR["lamp"], g * tw)
        pg.flat(oval(qx, qy, 10 * z, 10 * z), FOR["lamp"], 0.25 * g * tw, blur=5 * z)


def _moth(pg, snap, act, t):
    gl = act.m("lantern")
    if gl is None or gl.lamp is None or gl.lamp <= 0.6:
        return
    x = gl.x + 70 * math.cos(t * 2.1) + 20 * math.sin(t * 5.3)
    y = gl.y - 120 + 40 * math.sin(t * 2.9)
    z = snap["zoom"]
    fl = abs(math.sin(t * 22))
    for sx in (-1, 1):
        pg.flat(path_of(snap, [(x, y), (x + sx * 14 * fl, y - 9), (x + sx * 16 * fl, y + 3), (x + sx * 4, y + 6)]),
                "#d8ccae")
    pg.stroke(path_of(snap, [(x, y - 4), (x, y + 7)], False), "#998a70", 3 * z)


def _particles(pg, snap, scene):
    z = snap["zoom"]
    for p in scene.particles.items:
        sx, sy = P(snap, p.x, p.y)
        if p.kind == "firefly":
            fl = 0.5 + 0.5 * math.sin(p.age * 6 + p.r * 5)
            f = min(1.0, p.age / 0.8) * min(1.0, (p.life - p.age) / 1.0) * fl
            pg.flat(oval(sx, sy, p.r * 1.8 * z, p.r * 1.8 * z), "#d8f08a", 0.3 * f, blur=5 * z,
                    blend=skia.BlendMode.kScreen)
            pg.flat(oval(sx, sy, p.r * 0.5 * z, p.r * 0.5 * z), "#eefcb0", 0.4 + 0.6 * f)
        elif p.kind == "leaf":
            continue
        else:                                     # a clod lands on the ground and settles there, never falls
            a = 1 - p.age / p.life                # on below it (advisor FK0022 r3: they dropped through it)
            sx, sy = P(snap, p.x, min(p.y, G - p.r))
            pg.flat(oval(sx, sy, p.r * z, p.r * z), FOR["soil"], 0.4 + 0.6 * a)


# ----------------------------------------------------------------------------------------------- on screen

def _panel(pg, x0, y0, x1, y1, a=1.0):
    pg.flat(rrect(x0 + 5, y0 + 8, x1 + 5, y1 + 8, 18), (40, 28, 24), 0.25 * a, blur=8)
    pg.flat(rrect(x0, y0, x1, y1, 18), FOR["panel"], a)


def _screen(pg, snap, act, t):
    """The count (top left) and the name cards (bottom), in fixed screen units (owner + Toby, FK0007: no jitter)."""
    i, T = act.find_at(t)
    F0 = act.F[0]
    if F0["title"][0] <= t < F0["title"][1] + 1.0:
        a = smoothstep(seg(t, F0["title"][0], F0["title"][0] + 0.7)) * (1 - smoothstep(seg(t, F0["title"][1],
                                                                                     F0["title"][1] + 0.7)))
        _card(pg, a, "BUG HUNT", ["Can the Keepers find six", "different bugs in the forest?"], None)
    a0, a1 = T["card"]
    if a0 <= t < a1 + 0.8:
        a = smoothstep(seg(t, a0, a0 + 0.7)) * (1 - smoothstep(seg(t, a1, a1 + 0.7)))
        kind = BH.FINDS[i]["kind"]
        _card(pg, a, BUGS[kind]["name"], BUGS[kind]["line"], kind)
    Fc = act.FIN["card"]
    if Fc[0] <= t < Fc[1] + 0.8:
        a = smoothstep(seg(t, Fc[0], Fc[0] + 0.7)) * (1 - smoothstep(seg(t, Fc[1], Fc[1] + 0.7)))
        _card(pg, a, "All six found!", ["Every one of them helps", "keep the forest healthy."], None)
    if F0["title"][1] - 0.5 < t:
        n = act.found(t)
        hi = max((BH.bump(t, Tq["tick"], 0.8) for Tq in act.F), default=0.0)
        a = smoothstep(seg(t, F0["title"][1] - 0.5, F0["title"][1] + 0.3))
        _panel(pg, 40, 36, 420, 108, a)
        col = tuple(np.array(TF.C_rgb(FOR["paper"])) * (1 - 0.3 * hi) + np.array([255, 214, 110]) * 0.3 * hi)
        _text(pg, f"BUGS FOUND  {n} / 6", 230, 84, 32, col, a)


def _card(pg, a, title, lines, kind):
    """The name card at the bottom: paper on wood, big friendly letters, the bug's picture; it fades where it stands."""
    if a <= 0.01:
        return
    W, H = 1240, 210
    x0, y0 = 960 - W // 2, 1080 - 30 - H
    x1, y1 = x0 + W, y0 + H
    c = pg.c
    c.saveLayer(None, skia.Paint(Alphaf=a))
    _panel(pg, x0, y0, x1, y1)
    pg.flat(rrect(x0 + 10, y0 + 10, x1 - 10, y1 - 10, 12), FOR["card"])
    tx0 = x0 + (230 if kind else 60)
    if kind:
        L = 190 if kind in ("earthworm", "millipede") else 130
        bug_screen(pg, kind, x0 + 120, y0 + H // 2, L, -0.6 if L > 150 else -1.2)
    cx = (tx0 + x1 - 40) // 2
    _text(pg, title, cx, y0 + H // 2 - 30, 62, FOR["ink"])
    for q, ln in enumerate(lines):
        _text(pg, ln, cx, y0 + H // 2 + 30 + q * 42, 34, tone(FOR["ink"], 0.2), weight="Medium")
    c.restore()


# ----------------------------------------------------------------------------------------------- the frame

def _keeper(pg, snap, d):
    """A Keeper; on the back lane (d['lane'] > 0) he is drawn a little up the path and smaller, about his own feet,
    and a touch darker (further from Glo's light), with his feet still planted."""
    u = d.pop("lane", 0.0)
    sc = 1.0 - (1.0 - LANE_K) * u
    lift = LANE_Y * u
    x, y = d["x"], d["y"]
    sx, sy = P(snap, x, y)
    if d.get("arm_to"):                    # hand targets are world points; the figure draws on the screen (and on
        oy = sy - lift * snap["zoom"]      # the back lane about its own feet, smaller): put them where it draws
        d = dict(d, arm_to={s_: (sx + (P(snap, *q)[0] - sx) / sc, sy + (P(snap, *q)[1] - oy) / sc)
                            for s_, q in d["arm_to"].items()})
    if u <= 0.0:
        return TF._keeper(pg, snap, d, snap["t"])
    c = pg.c
    c.save()
    c.translate(sx, sy - lift * snap["zoom"])
    c.scale(sc, sc)
    c.translate(-sx, -sy)
    sh = 1.0 - 0.2 * u
    c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix([sh, 0, 0, 0, 0, 0, sh, 0, 0, 0, 0, 0, sh, 0,
                                                                       0, 0, 0, 0, 1, 0])))
    TF._keeper(pg, snap, d, snap["t"])
    c.restore()
    c.restore()


def _name_tags(pg, snap, act, t):
    """The name tags over everyone at the start (as in every episode), the end sign's tags."""
    from .chatter import TOPS
    from .christmas_flat import PAPER, _font
    for d in snap["keepers"]:
        a = act.name_amount(d["kind"], t)
        if a <= 0.01:
            continue
        x, y = P(snap, d["x"], d["y"] - TOPS[d["kind"]] * d["k"] - 40)
        nm = TF.NAMES[d["kind"]]
        w = _font(26, "Bold").measureText(nm) + 26
        pg.flat(rrect(x - w / 2, y - 30, x + w / 2, y + 8, 10), TF.NAME_COL[d["kind"]], 0.92 * a)
        _text(pg, nm, x, y - 3, 26, PAPER, a)


def set_lanes(trk):
    global LANES
    LANES = lanes(trk) if trk else {}


def record(scene, t):
    return TF.record(scene, t)


def draw_hunt(pg, snap, scene):
    act = scene.act_at(snap["t"])
    t = act_time(snap, act)
    i, T = act.find_at(t)
    _scene(pg, snap, act, t)
    _name_tags(pg, snap, act, t)
    _lens(pg, snap, act, i, T, t, act._lens_x(t))
    _moth(pg, snap, act, t)
    _flare(pg, snap, act, T, t)
    _particles(pg, snap, scene)
    _bubbles(pg, snap)
    _screen(pg, snap, act, t)


def _bubbles(pg, snap):
    """The Keepers' speech bubbles (advisor FK0022 r3): only one with a picture in it, only for a speaker in shot,
    kept whole inside the frame, and never the tiny 'pin on a stick' as one opens or closes."""
    from .chatter import bubble
    from . import illustrate as il
    z, W, H = snap["zoom"], snap["W"], snap["H"]
    for b in snap["bubbles"]:
        if b["r"] < 14 or not b.get("icon"):
            continue
        bx, by = P(snap, b["x"], b["y"])
        tx, ty = P(snap, *b["tail"])
        if not (0 <= tx <= W and 0 <= ty <= H):
            continue
        r = b["r"] * z
        icon = "?" if b["icon"] == "dots" else b["icon"]      # (the faint dots read as an empty bubble)
        bx = min(max(bx, r + 12), W - r - 12)
        by = min(max(by, r + 12), H - r - 12)
        mark = icon if icon in ("?", "!") else None            # (the style canvas draws no text: the mark goes on
        ic0 = "none" if mark else icon                          # the page, over the bubble)
        il.creature(pg, lambda cv, bx=bx, by=by, r=r, ic=ic0, tx=tx, ty=ty: bubble(cv, bx, by, r, ic,
                                                                                 (214, 196, 176), 1.0, (tx, ty)),
                    bx, by)
        if mark:
            _text(pg, mark, bx, by + r * 0.36, r * 1.05, "#4a3b33")


def _scene(pg, snap, act, t):
    """The world: the forest, the Keepers, the hiding places and their bugs, the cart and its book (drawn again,
    magnified, through the lens)."""
    _forest(pg, snap, t)
    vx0, vx1 = TF._view_x(snap)
    back = [dict(d, lane=lane(d["kind"], snap["t"])) for d in snap["keepers"] if lane(d["kind"], snap["t"]) > 0.5]
    for d in sorted(back, key=lambda d: -d["lane"]):          # further up the path: behind the stump, stone and log
        _keeper(pg, snap, d)
    for j, f in enumerate(BH.FINDS):                       # every hiding place stays where it is
        if vx0 - 500 < f["x"] < vx1 + 500:
            pg.begin_grain()
            _place(pg, snap, act, j, t)
            o = P(snap, 0.0, 0.0)
            pg.end_grain(o[0], o[1])
    _glo_pool(pg, snap, act)
    cx = act.cart_x(t)
    if vx0 - 300 < cx < vx1 + 300:
        pg.begin_grain()
        _cart_handle(pg, snap, cx)
        o = P(snap, cx, 0.0)
        pg.end_grain(o[0], o[1])
    ks = sorted((d for d in snap["keepers"] if lane(d["kind"], snap["t"]) <= 0.5),
                key=lambda d: -lane(d["kind"], snap["t"]))      # the back lane first (behind)
    for d in ks:
        u = lane(d["kind"], snap["t"])
        if u > 0.001:
            d = dict(d, lane=u)
        _keeper(pg, snap, d)
    if vx0 - 300 < cx < vx1 + 300:
        pg.begin_grain()
        _cart(pg, snap, cx, -cx / 22.0)
        if t < act.F[0]["open"]:
            _closed_book(pg, snap, cx)
        else:
            _book(pg, snap, act, cx, t)
        o = P(snap, cx, 0.0)
        pg.end_grain(o[0], o[1])


def draw(snap, scene):
    pg = TF.ZoomPage(int(snap["W"]), int(snap["H"]))
    pg.zoom = snap["zoom"]
    if snap["act"] == "hunt":
        draw_hunt(pg, snap, scene)
    elif snap["act"] == "comment_sign":
        TF.draw_sign(pg, snap)
    else:
        raise ValueError(f"no flat drawing for act {snap['act']}")
    rgb = pg.finish()
    f = snap["fade"]
    if f > 0.001:
        rgb = (rgb.astype(np.float32) * (1 - f)).astype(np.uint8)
    return rgb
