"""Foundry engine - Tree Monsters (Toby's story, docs/engines/foundry_monsters.md).

A night forest on a plateau; the factory is cut away underneath it, like a diagram:

  surface (GF):  harvester cuts 5 trees -> drives on -> turns round -> tips its load into a pit
  shaft:         logs drop down the shaft, through a bank of spinning saws -> chunks
  vat:           chunks splash into glowing green liquid; 3 of them grow big
  claws:         the big ones are lifted out and carried right; the vat drains, the rest go
                 down the plug
  build bay:     ceiling arms stick parts on (asleep: faint colour, eyes shut)
  orbs:          a blue orb drops into each one -> full colour, eyes open, they move
  training room: punching bag, trampoline, balance beam; TRAINING sign -> THEY PASSED
  exit:          a door in the cliff opens onto the lower forest and they run off into the trees

The whole thing is a scripted timeline (durations from params, so the same scene makes the
60 s Short and the 2-3 min version); only particles are simulated. Everything is seeded.
"""
import math

import numpy as np

from audio import synth
from engine.scene import Scene as BaseScene

from .products.monster import Monster, Xform, WOOD_BODY, ORB, ellipse, blob, grain
from .style import BG, FAR, MID, STEEL, IRON, FLOOR, CABLE, HeatGlow, Shifted, lighten, smoothstep, \
    smootherstep, settle

# ----- palette (night forest + the factory's own) -----
SKY_STAR = np.array([150, 160, 190], np.float64)
MOON = np.array([214, 214, 196], np.float64)
EARTH = np.array([31, 25, 24], np.float64)
EARTH_DARK = np.array([22, 18, 18], np.float64)
GRASS = np.array([30, 52, 38], np.float64)
TRUNK = np.array([82, 60, 44], np.float64)
BARK = np.array([62, 45, 34], np.float64)
LEAF = [np.array(c, np.float64) for c in ((34, 72, 50), (40, 84, 56), (28, 60, 44))]
LEAF_FAR = np.array([20, 34, 30], np.float64)
INTERIOR = np.array([17, 20, 30], np.float64)
GREEN = np.array([92, 230, 120], np.float64)       # vat liquid (glows)
GREEN_DEEP = np.array([30, 96, 52], np.float64)
SAWDUST = np.array([190, 160, 112], np.float64)
MACHINE = np.array([60, 66, 52], np.float64)       # harvester: dark olive
HAZARD = np.array([201, 162, 39], np.float64)       # dim gold (Foundry conveyor accent)
LAMP = np.array([255, 196, 110], np.float64)
SIGN_WARM = np.array([242, 232, 213], np.float64)
SIGN_GREEN = np.array([120, 255, 150], np.float64)


def lerp(a, b, u):
    return a + (b - a) * u


def seg(t, t0, t1):
    """0..1 progress of t through [t0, t1]."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return min(1.0, max(0.0, (t - t0) / (t1 - t0)))


def rect(cv, x0, y0, x1, y1, col):
    cv.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], col)


def machine_block(cv, x0, y0, x1, y1, col, edge=1.45):
    rect(cv, x0, y0, x1, y1, col)
    yb = y1 - (y1 - y0) * 0.22
    rect(cv, x0, yb, x1, y1, np.asarray(col) * 0.72)
    cv.line(x0, y0, x1, y0, lighten(col, edge), 2)
    cv.line(x0, y0, x0, y1, lighten(col, edge * 0.85), 1.5)


def saw_blade(cv, x, y, r, rot, col=STEEL, teeth=14):
    pts = []
    for i in range(teeth * 2):
        a = rot + i * math.pi / teeth
        rr = r if i % 2 == 0 else r * 0.86
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    cv.polygon(pts, lighten(col, 1.5))
    cv.circle(x, y, r * 0.8, lighten(col, 1.15))
    for i in range(3):
        a = rot * 1.0 + i * 2 * math.pi / 3
        cv.line(x, y, x + math.cos(a) * r * 0.65, y + math.sin(a) * r * 0.65, col, max(2.0, r * 0.08))
    cv.circle(x, y, r * 0.18, col * 0.7)


def tree(cv, x, base_y, h, seed, leaf_k=1.0):
    """Ordinary tree: trunk + round leafy top. (x, base_y) = foot of the trunk."""
    rs = np.random.default_rng(seed)
    tw = 50
    top = base_y - h * 0.58
    cv.polygon([(x - tw / 2, base_y), (x + tw / 2, base_y), (x + tw * 0.36, top), (x - tw * 0.36, top)], TRUNK)
    cv.line(x - tw * 0.1, base_y, x - tw * 0.05, top + 20, BARK, 4)
    cv.line(x + tw * 0.25, base_y - 30, x + tw * 0.18, top + 60, BARK, 3)
    if leaf_k <= 0:
        return
    cy = base_y - h * 0.74
    for i in range(7):
        a = rs.uniform(0, 2 * math.pi)
        d = rs.uniform(0, h * 0.13)
        r = rs.uniform(0.17, 0.24) * h * leaf_k
        cv.circle(x + math.cos(a) * d * 1.3, cy + math.sin(a) * d - (i == 0) * h * 0.1, r, LEAF[i % 3])
    cv.circle(x - h * 0.06, cy - h * 0.08, h * 0.12 * leaf_k, lighten(LEAF[1], 1.12))


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "age", "r", "col", "kind", "g", "glow")

    def __init__(self, x, y, vx, vy, life, r, col, kind="dot", g=1400.0, glow=False):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.age, self.r, self.col, self.kind, self.g, self.glow = life, 0.0, r, col, kind, g, glow


class Scene(BaseScene):
    bed = {"type": "procedural", "name": "industrial", "gain": 1.0,
           "reverb": {"decay": 6.0, "wet": 0.5, "tone": 2200}}
    reverb = {"decay": 3.0, "wet": 0.35, "tone": 3500}
    events_gain = 1.0

    def __init__(self, params, seed, fmt, track):
        super().__init__(params, seed, fmt, track)
        P = self.p = params
        track.scale = synth.INDUSTRIAL_SCALE
        self.bed = dict(Scene.bed)
        self.v = P.get("visual", {})
        W = P.get("world", {})
        self.GF = W.get("ground", 1600.0)
        self.GF2 = self.GF + W.get("drop", 1650.0)
        self.k = P.get("monster_scale", 0.55)
        self.trees_x = W.get("trees", [900, 1250, 1600, 1950, 2300])
        self.tree_h = W.get("tree_h", 700)
        self.pit = W.get("pit", [3300, 3800])                 # funnel opening at the surface
        self.shaft = W.get("shaft", [3420, 3680])
        self.saw_y = self.GF + W.get("saw_dy", 820)
        self.vat = W.get("vat", [3250, 3850])
        self.vat_rim = self.GF + W.get("vat_rim_dy", 1170)
        self.vat_full = self.vat_rim + 70
        self.vat_bottom = self.GF2 - 110
        self.rail_y = self.GF + W.get("rail_dy", 980)
        self.interior = W.get("interior", [3150, 7400])       # cut-away factory under the forest
        self.ceil = self.GF + W.get("ceiling_dy", 300)
        self.stands = W.get("stands", [4470, 4830, 5190])
        self.room = W.get("room", [5520, 7400])
        self.bag_x = W.get("bag_x", 6010)
        self.tramp_x = W.get("tramp_x", 6350)
        self.beam = W.get("beam", [6580, 6900])
        self.bag_gap = W.get("bag_gap", 130)              # monster stands this far left of the bag
        self.door_x = self.interior[1]
        self.grow_x = W.get("grow_x", [3400, 3550, 3700])
        self.outside_trees = W.get("outside_trees", [7780, 8120, 8480, 8820, 9180, 9560])
        self.end_x = W.get("end_x", [7860, 8090, 8320])
        self.prs = np.random.default_rng(seed + 11)

        self._build_timeline(P.get("durations", {}))
        self.monsters = [Monster(kd, self.k) for kd in Monster.KINDS]
        for mi, m in enumerate(self.monsters):
            m.x, m.y = self.stands[mi], self.GF2       # build spot (the camera aims at it before they appear)
            m.reach = W.get("part_reach", 330)
            m.alive, m.orb_in = 0.0, 0.0
            m.attach = {name: 0.0 for name in self._parts(m)}
        self._plan_logs()
        self.parts_t = self._plan_parts()
        self.particles = []
        self.prev_t = -1.0
        self.zoom, self.zoom_v = 1.0, 0.0
        self.cam_vx = self.cam_vy = 0.0
        self._camera(0.0, 0.0)
        self.glow = self.scv = None
        self.stars = [(self.prs.uniform(0, 4000), self.prs.uniform(0, 4000),
                       self.prs.uniform(0.8, 2.2), self.prs.uniform(0.3, 1.0)) for _ in range(160)]
        self.far_trees = [(self.prs.uniform(-1200, 11000), self.prs.uniform(0.6, 1.1)) for _ in range(70)]
        self.stats = {"trees_cut": 0, "chunks": len(self.chunks), "grown": 3}

    # ------------------------------------------------------------------ timeline

    def _build_timeline(self, D):
        d = dict(intro=0.6, drive=0.55, cut=0.75, fall=0.75, load=0.4, to_pit=1.4, turn=0.9, reverse=0.9,
                 tip=1.5, drop=2.8, settle=0.9, grow=2.4, grab=1.5, carry=2.2, build=8.4, orbs=2.4,
                 wake=1.3, release=0.8, walk=2.6, rounds=2, round=3.4, swap=0.8, passed=1.8, door=1.6,
                 exit=3.6, hold=1.0)
        d.update(D)
        self.d = d
        T, t = {}, d["intro"]
        for i in range(len(self.trees_x)):
            T[f"drive{i}"] = t; t += d["drive"]
            T[f"cut{i}"] = t; t += d["cut"]
            T[f"fall{i}"] = t; t += d["fall"]
            T[f"load{i}"] = t; t += d["load"]
        for name in ("to_pit", "turn", "reverse", "tip", "drop", "settle", "grow", "grab", "carry", "build",
                     "orbs", "wake", "release", "walk"):
            T[name] = t
            t += d[name]
        T["train"] = t
        t += d["rounds"] * d["round"] + (d["rounds"] - 1) * d["swap"]
        for name in ("passed", "door", "exit", "hold"):
            T[name] = t
            t += d[name]
        T["end"] = t
        self.T = T

    def _parts(self, m):
        from .products.monster import PARTS
        return list(PARTS[m.kind])

    def _plan_parts(self):
        """Each monster's parts get equal slots in the build window; arms bring them in."""
        out = {}
        t0, dur = self.T["build"], self.d["build"]
        for mi, m in enumerate(self.monsters):
            names = self._parts(m)
            slot = dur / len(names)
            for j, name in enumerate(names):
                s = t0 + j * slot + mi * 0.18
                out[(mi, name)] = (s, s + slot * 0.78)
        return out

    # ----- harvester -----

    def harvester(self, t):
        """(center x, facing +1/-1, turn squash -1..1, hopper tip angle, moving speed 0..1)"""
        T, d = self.T, self.d
        L = 560
        n = len(self.trees_x)
        front = lambda i: self.trees_x[i] - 100                      # saw touching trunk i
        x_of_front = lambda f: f - L / 2 - 40                        # center from saw-center x
        start = x_of_front(self.trees_x[0] - 760)
        if t < T["drive0"]:
            return start, 1, 1.0, 0.0, 0.0
        for i in range(n):
            if t < T[f"cut{i}"]:
                prev = start if i == 0 else x_of_front(front(i - 1) + 60)
                u = smootherstep(seg(t, T[f"drive{i}"], T[f"cut{i}"]))
                return lerp(prev, x_of_front(front(i)), u), 1, 1.0, 0.0, 1.0
            if t < T[f"fall{i}"]:
                u = seg(t, T[f"cut{i}"], T[f"fall{i}"])
                return x_of_front(front(i)) + 60 * smoothstep(u), 1, 1.0, 0.0, 0.3
            if i == n - 1 or t < T[f"drive{i + 1}"]:
                if i < n - 1:
                    return x_of_front(front(i) + 60), 1, 1.0, 0.0, 0.0
        last = x_of_front(front(n - 1) + 60)
        stop = self.pit[0] - 40 - L / 2 + 520                       # drive on past where it will reverse to
        rev = self.pit[0] - 10 - L / 2                              # rear bumper at the pit edge after turning
        if t < T["turn"]:
            u = smootherstep(seg(t, T["to_pit"], T["turn"]))
            return lerp(last, stop, u), 1, 1.0, 0.0, 1.0 if 0 < u < 1 else 0.0
        if t < T["reverse"]:
            u = seg(t, T["turn"], T["reverse"])
            return stop, 1, math.cos(math.pi * smootherstep(u)), 0.0, 0.5
        if t < T["tip"]:
            u = smootherstep(seg(t, T["reverse"], T["tip"]))
            return lerp(stop, rev, u), -1, -1.0, 0.0, 1.0 if 0 < u < 1 else 0.0
        up = smoothstep(seg(t, T["tip"], T["tip"] + self.d["tip"] * 0.5))
        down = smoothstep(seg(t, T["drop"] + self.d["drop"] * 0.4, T["drop"] + self.d["drop"] * 0.9))
        tip = math.radians(48) * up * (1 - down)
        if t >= T["settle"]:                                        # drives away (back to the forest)
            u = seg(t, T["settle"], T["settle"] + 4.0)
            return rev - 1400 * u * u, -1, -1.0, 0.0, 1.0 if u < 1 else 0.0
        return rev, -1, -1.0, tip, 0.0

    # ----- logs + chunks -----

    def _plan_logs(self):
        T, d, rs = self.T, self.d, self.prs
        n = len(self.trees_x)
        self.log_len = 240
        self.logs = []
        drop0 = T["tip"] + d["tip"] * 0.45
        span = d["tip"] * 0.55 + d["drop"] * 0.25
        g = 2600.0
        for i in range(n):
            rel = drop0 + span * i / (n - 1) * 0.9
            # slide 0.35 s out of the hopper, short fall into the funnel, then free fall down the shaft
            x_in = lerp(self.shaft[0] + 40, self.shaft[1] - 40, rs.uniform(0.2, 0.8))
            v0 = 250.0
            dist = self.saw_y - (self.GF + 60)
            t_fall = (-v0 + math.sqrt(v0 * v0 + 2 * g * dist)) / g
            self.logs.append(dict(release=rel, x_in=x_in, t_shaft=rel + 0.45, t_saw=rel + 0.45 + t_fall,
                                  v_saw=v0 + g * t_fall, spin=rs.uniform(-1, 1)))
        self.chunks = []
        vat_w = self.vat[1] - self.vat[0]
        slots = np.linspace(self.vat[0] + 50, self.vat[1] - 50, n * 6)
        rs.shuffle(slots)
        k = 0
        for li, lg in enumerate(self.logs):
            for j in range(6):
                vx = rs.uniform(-160, 160)
                y0 = self.saw_y + (j - 2.5) * 40
                # fall from the saw line to the liquid
                dist = self.vat_full - y0
                v0 = lg["v_saw"] * 0.6
                tf = (-v0 + math.sqrt(v0 * v0 + 2 * g * dist)) / g
                self.chunks.append(dict(log=li, j=j, x0=lg["x_in"] + rs.uniform(-12, 12), y0=y0, vx=vx, v0=v0,
                                        t0=lg["t_saw"], t_hit=lg["t_saw"] + tf, rest_x=float(slots[k]),
                                        rot0=rs.uniform(0, 6.28), spin=rs.uniform(-6, 6),
                                        bob=rs.uniform(0, 6.28), w=rs.uniform(34, 44), h=rs.uniform(26, 34),
                                        grow=None))
                k += 1
        # the three that grow: the chunks resting nearest each grow spot
        used = set()
        for mi, gx in enumerate(self.grow_x):
            best = min((c for c in self.chunks if id(c) not in used), key=lambda c: abs(c["rest_x"] - gx))
            used.add(id(best))
            best["grow"] = mi
            best["rest_x"] = gx
        _ = vat_w

    def chunk_pos(self, c, t):
        """(x, y, rot, state) of a chunk; state: 'fall', 'float', 'drain', 'gone'."""
        if t < c["t_hit"]:
            dt = t - c["t0"]
            return (c["x0"] + c["vx"] * dt * 0.6, c["y0"] + c["v0"] * dt + 1300 * dt * dt,
                    c["rot0"] + c["spin"] * dt, "fall")
        u = smootherstep(seg(t, c["t_hit"], c["t_hit"] + 1.2))
        x_hit = c["x0"] + c["vx"] * (c["t_hit"] - c["t0"]) * 0.6
        x = lerp(x_hit, c["rest_x"], u)
        lvl = self.liquid_y(t)
        y = lvl - 6 + 5 * math.sin(t * 1.6 + c["bob"]) + 30 * (1 - u) * math.exp(-(t - c["t_hit"]) * 3)
        rot = c["rot0"] + c["spin"] * (c["t_hit"] - c["t0"]) * (1 - u) + 0.15 * math.sin(t + c["bob"])
        if c["grow"] is None and t > self.T["carry"]:
            # draining: everything sinks with the level and swirls into the plug
            dr = seg(t, self.T["carry"] + 0.4, self.T["build"] - 0.2)
            cx = (self.vat[0] + self.vat[1]) / 2
            order = abs(c["rest_x"] - cx) / ((self.vat[1] - self.vat[0]) / 2)
            v = smoothstep((dr - 0.55 - 0.3 * (1 - order)) / 0.3)
            x = lerp(x, cx + 20 * math.sin(t * 6 + c["bob"]), v)
            y = lerp(y, self.vat_bottom + 80, v * v)
            if v >= 1:
                return x, y, rot, "gone"
            return x, y, rot + v * 6, "drain"
        return x, y, rot, "float"

    def liquid_y(self, t):
        dr = smoothstep(seg(t, self.T["carry"] + 0.4, self.T["build"] - 0.2))
        return lerp(self.vat_full, self.vat_bottom - 6, dr)

    # ----- claws -----

    def claw_state(self, mi, t):
        """(x, grip y, carrying, opening 0..1) of transfer claw mi."""
        T, d = self.T, self.d
        m = self.monsters[mi]
        gx, sx = self.grow_x[mi], self.stands[mi]
        bc_h = m.body_center()[1] - m.y                         # body center above the feet (negative)
        rx, ry = m.body_size()
        y_float = self.vat_full - 6 - ry * 0.35
        carry_y = self.vat_rim - ry - 30
        build_y = self.GF2 + bc_h
        park = self.rail_y + 40
        stagger = mi * 0.15
        g0, c0 = T["grab"] + stagger, T["carry"] + stagger
        if t < g0:
            return gx, park, False, 1.0
        if t < c0:
            u = seg(t, g0, c0)
            if u < 0.4:
                return gx, lerp(park, y_float - ry, smootherstep(u / 0.4)), False, 1.0
            if u < 0.55:
                return gx, y_float - ry, True, 1 - smoothstep((u - 0.4) / 0.15)
            return gx, lerp(y_float - ry, carry_y - ry, smootherstep((u - 0.55) / 0.45)), True, 0.0
        b = T["build"]
        if t < b:
            u = smootherstep(seg(t, c0, b - 0.3))
            x = lerp(gx, sx, u)
            y = carry_y - ry if u < 0.75 else lerp(carry_y - ry, build_y - ry, smootherstep((u - 0.75) / 0.25))
            return x, y, True, 0.0
        r0 = T["release"]
        if t < r0:
            return sx, build_y - ry, True, 0.0
        u = seg(t, r0, r0 + self.d["release"])
        return sx, lerp(build_y - ry, park, smootherstep(seg(u, 0.25, 1.0))), u < 0.25, smoothstep(u / 0.25)

    def grow_amount(self, mi, t):
        return smootherstep(seg(t, self.T["grow"] + mi * 0.35, self.T["grow"] + self.d["grow"] * 0.8 + mi * 0.2))

    # ----- training -----

    def stations(self):
        return [("bag", self.bag_x - self.bag_gap), ("tramp", self.tramp_x), ("beam", (self.beam[0] + self.beam[1]) / 2)]

    def train_spot(self, mi, r):
        st = self.stations()
        return st[(mi + r) % 3]

    def monster_pose(self, mi, t):
        """Position + transform of a monster after it wakes: (x, y, dx, dy, ang, walking)."""
        T, d = self.T, self.d
        sx = self.stands[mi]
        m = self.monsters[mi]
        if t < T["walk"]:
            return sx, self.GF2, 0, 0, 0, 0.0
        tr0 = T["train"]
        if t < tr0:                                       # walk/roll into the training room
            u = smootherstep(seg(t, T["walk"] + mi * 0.2, tr0 - 0.1))
            x = lerp(sx, self.train_spot(mi, 0)[1], u)
            return x, self.GF2, 0, -abs(math.sin(u * math.pi * 6)) * 10 * (m.kind != "wheels"), 0, 1.0 if 0 < u < 1 else 0.0
        R, rd, sw = d["rounds"], d["round"], d["swap"]
        t_rel = t - tr0
        r = int(min(R - 1, t_rel // (rd + sw)))
        in_r = t_rel - r * (rd + sw)
        if t >= T["passed"]:
            st, x = self.train_spot(mi, R - 1)
            return self._exit_pose(mi, t, x)
        if in_r > rd:                                     # moving to the next station
            u = smootherstep((in_r - rd) / sw)
            x0, x1 = self.train_spot(mi, r)[1], self.train_spot(mi, r + 1)[1]
            return lerp(x0, x1, u), self.GF2, 0, -abs(math.sin(u * math.pi * 3)) * 12, 0, 1.0
        st, x = self.train_spot(mi, r)
        return self._station_pose(mi, st, x, in_r, t)

    def _station_pose(self, mi, st, x, u_t, t):
        m = self.monsters[mi]
        if st == "bag":
            ph = (u_t / 0.7) % 1.0
            hit = max(0.0, math.sin(ph * math.pi)) ** 2
            m.punch = hit
            return x, self.GF2, 34 * hit, 0, 0.06 * hit, 0.0
        m.punch = 0.0
        if st == "tramp":
            per = 1.0
            n = int(u_t // per)
            ph = (u_t % per) / per
            hgt = 330 if n % 2 else 240
            dy = -4 * hgt * ph * (1 - ph)
            ang = 2 * math.pi * smootherstep(seg(ph, 0.15, 0.85)) * (1 if n % 2 else 0) * (1 if mi != 1 else -1)
            return x, self.GF2 - 70, 0, dy, ang, 0.0
        # beam: along it and back, a little wobble, a hop in the middle
        bx0, bx1 = self.beam[0] + 50, self.beam[1] - 50
        ph = (u_t / 3.0) % 1.0
        x = lerp(bx0, bx1, 0.5 - 0.5 * math.cos(ph * 2 * math.pi))
        hop = max(0.0, math.sin(ph * 4 * math.pi)) ** 8 * 60
        return x, self.GF2 - 130, 0, -hop, 0.07 * math.sin(t * 3.1 + mi), 1.0

    def _exit_pose(self, mi, t, x_last):
        T = self.T
        if t < T["exit"] + mi * 0.35:
            # gather by the door while it opens
            u = smootherstep(seg(t, T["passed"] + 0.4, T["exit"] - 0.1))
            tx = self.door_x - 520 + mi * 170
            return lerp(x_last, tx, u), self.GF2, 0, 0, 0, 1.0 if 0 < u < 1 else 0.0
        u = seg(t, T["exit"] + mi * 0.35, T["hold"] + 0.4)
        x = lerp(self.door_x - 520 + mi * 170, self.end_x[mi], smoothstep(u))
        return x, self.GF2, 0, -abs(math.sin(u * 30)) * 14 * (self.monsters[mi].kind != "wheels"), 0, 1.0

    # ------------------------------------------------------------------ camera

    def _cam_target(self, t):
        """Center of interest (world) for the camera."""
        T = self.T
        hx, face = self.harvester(t)[:2]
        fy = self.GF - self.h * 0.30                   # forest: ground about 80% down the frame
        ry = self.GF2 - self.h * 0.33                  # factory floor rooms
        if t < T["turn"]:
            return hx + 130, fy
        if t < T["tip"]:
            return hx + 150, fy
        if t < T["drop"] + 0.4:
            return (self.pit[0] + self.pit[1]) / 2 - 80, lerp(fy, self.GF - 120, smootherstep(seg(t, T["tip"], T["drop"])))
        if t < T["settle"]:
            u = smootherstep(seg(t, T["drop"] + 0.4, T["settle"]))
            return (self.pit[0] + self.pit[1]) / 2, lerp(self.GF - 100, self.vat_rim - 150, u)
        if t < T["carry"]:
            return (self.vat[0] + self.vat[1]) / 2, self.vat_rim - 60
        if t < T["build"]:
            u = smootherstep(seg(t, T["carry"] + 0.3, T["build"]))
            return lerp((self.vat[0] + self.vat[1]) / 2, self.stands[1], u), lerp(self.vat_rim - 60, ry, u)
        cx_room = self.room_center()
        if t < T["walk"]:
            return self.stands[1], ry
        if t < T["train"]:
            u = smootherstep(seg(t, T["walk"], T["train"]))
            return lerp(self.stands[1], cx_room, u), ry
        if t < T["passed"]:
            return cx_room, ry
        if t < T["exit"]:
            u = smootherstep(seg(t, T["passed"] + 0.6, T["exit"]))
            return lerp(cx_room, self.door_x - 120, u), ry
        u = smootherstep(seg(t, T["exit"], T["hold"]))
        return lerp(self.door_x - 120, self.door_x + 560, u), ry

    def room_center(self):
        xs = [self.bag_x - self.bag_gap - 140, self.beam[1] - 40]
        return (xs[0] + xs[1]) / 2

    def _zoom_focus(self, t, tx, ty):
        """Camera zoom per beat (params camera.zoom); in the build bay and for the orbs the camera
        moves in on one monster at a time when `visit` is on (narrow vertical frames)."""
        T, d = self.T, self.d
        Z = {"forest": 1.0, "vat": 1.2, "build": 1.0, "orbs": 1.0, "train": 1.0, "exit": 1.0, "end": 1.0}
        Z.update(self.p.get("camera", {}).get("zoom", {}))
        visit = self.p.get("camera", {}).get("visit", False)
        if t < T["drop"] + 0.4:
            return Z["forest"], tx, ty
        if t < T["settle"]:
            return lerp(Z["forest"], Z["vat"], smoothstep(seg(t, T["drop"], T["settle"]))), tx, ty
        if t < T["carry"]:
            return Z["vat"], tx, ty
        if t < T["build"]:
            u = smootherstep(seg(t, T["carry"] + 0.3, T["build"]))
            return lerp(Z["vat"], Z["build"], u), tx, ty
        m_of = lambda mi: self.monsters[mi]
        if t < T["orbs"]:
            if not visit:
                return Z["build"], tx, ty
            # visit each monster for a third of the build (blue first)
            u = (t - T["build"]) / d["build"] * 3
            mi = min(2, int(u))
            return Z["build"], self.stands[mi], self.GF2 - self.h * 0.33 / Z["build"]
        if t < T["release"]:
            if not visit:
                return Z["orbs"], tx, ty
            # follow the orbs one by one, then pull back to see all three awake
            o_last = self.orb_times(2)[1]
            if t < o_last + 0.3:
                mi = 0 if t < self.orb_times(0)[1] + 0.3 else 1 if t < self.orb_times(1)[1] + 0.3 else 2
                return Z["orbs"], self.stands[mi], self.GF2 - self.h * 0.36 / Z["orbs"]
            u = smootherstep(seg(t, o_last + 0.3, T["release"]))
            return lerp(Z["orbs"], Z["train"], u), lerp(self.stands[2], tx, u), lerp(self.GF2 - self.h * 0.36 / Z["orbs"], ty, u)
        if t < T["exit"]:
            return Z["train"], tx, ty
        u = smootherstep(seg(t, T["exit"], T["end"]))
        return lerp(Z["exit"], Z["end"], u), tx, ty

    def _camera(self, t, dt):
        tx, ty = self._cam_target(t)
        tz, tx, ty = self._zoom_focus(t, tx, ty)
        if dt <= 0:
            self.zoom = tz
        else:
            w = self.p.get("camera", {}).get("omega", 2.0)
            for _ in range(2):
                h = dt / 2
                self.zoom_v += (w * w * (tz - self.zoom) - 2 * w * self.zoom_v) * h
                self.zoom += self.zoom_v * h
        tx -= self.w / 2
        ty -= self.h / 2 + self.h * self.p.get("camera", {}).get("y_bias", 0.0)
        if dt <= 0:
            self.cam_x, self.cam_y = tx, ty
            return
        w = self.p.get("camera", {}).get("omega", 2.0)
        for _ in range(2):
            h = dt / 2
            self.cam_vx += (w * w * (tx - self.cam_x) - 2 * w * self.cam_vx) * h
            self.cam_vy += (w * w * (ty - self.cam_y) - 2 * w * self.cam_vy) * h
            self.cam_x += self.cam_vx * h
            self.cam_y += self.cam_vy * h

    # ------------------------------------------------------------------ simulation + sound

    def crossed(self, at):
        return self.prev_t < at <= self._t

    def pan(self, x):
        return float(np.clip((x - self.cam_x - self.w / 2) / (self.w / 2), -1, 1)) * 0.6

    def near(self, x, y):
        d = math.hypot(x - self.cam_x - self.w / 2, y - self.cam_y - self.h / 2)
        return float(1.0 / (1.0 + (d / 1400.0) ** 2))

    def note(self, i, octave=0):
        return self.track.note_in_scale(i % 8, octave)

    def fx(self, t, name, dur, vel, x, y):
        self.track.fx(t, name, dur, vel * self.near(x, y), self.pan(x))

    def hit(self, t, inst, note, vel, x, y):
        self.track.hit(t, inst, note, vel * self.near(x, y), self.pan(x))

    def burst(self, x, y, n, col, speed, life, r, kind="dot", g=1400.0, up=0.0, glow=False, spread=math.pi):
        for _ in range(n):
            a = -math.pi / 2 + self.rng.uniform(-spread, spread)
            s = speed * self.rng.uniform(0.4, 1.0)
            self.particles.append(Particle(x, y, math.cos(a) * s, math.sin(a) * s - up,
                                           life * self.rng.uniform(0.6, 1.2), r * self.rng.uniform(0.6, 1.3),
                                           col, kind, g, glow))

    def update(self, t, dt):
        self._t = t
        T, d = self.T, self.d
        self._camera(t, dt)
        hx, face, turn, tip, mov = self.harvester(t)
        # harvester engine + saw
        if self.crossed(T["drive0"]) or self.crossed(T["to_pit"]) or self.crossed(T["reverse"]) or \
                self.crossed(T["settle"]):
            self.fx(t, "motor", 1.6, 0.55, hx, self.GF)
        for i, x in enumerate(self.trees_x):
            if i > 0 and self.crossed(T[f"drive{i}"]):
                self.fx(t, "motor", d["drive"] + 0.2, 0.4, hx, self.GF)
            if self.crossed(T[f"cut{i}"]):
                self.fx(t, "saw", d["cut"], 0.75, x, self.GF)
            if T[f"cut{i}"] < t <= T[f"fall{i}"] and self.rng.uniform() < 0.8:
                self.burst(x - 20, self.GF - 60, 3, SAWDUST, 420, 0.7, 3.5, g=900, up=100, spread=1.2)
            if self.crossed(T[f"fall{i}"]):
                self.fx(t, "creak", d["fall"] * 0.9, 0.6, x, self.GF - 300)
            if self.crossed(T[f"load{i}"]):
                self.hit(t, "thud", 45, 0.9, x - 300, self.GF - 200)
                self.fx(t, "rustle", 0.9, 0.7, x - 300, self.GF - 400)
                ang = self.fall_angle(1.0)
                L = self.tree_h * 0.74
                cx, cy = x + math.sin(ang) * L, self.GF - 40 - math.cos(ang) * L
                for _ in range(26):
                    self.particles.append(Particle(cx + self.rng.uniform(-90, 90), cy + self.rng.uniform(-60, 60),
                                                   self.rng.uniform(-220, 220), self.rng.uniform(-260, 40),
                                                   self.rng.uniform(1.4, 2.6), self.rng.uniform(7, 13),
                                                   LEAF[self.rng.integers(3)], "leaf", 260))
                self.stats["trees_cut"] = i + 1
            if self.crossed(T[f"load{i}"] + d["load"] * 0.9):
                self.hit(t, "clunk", self.note(i, -1), 0.6, hx, self.GF - 200)
        if self.crossed(T["turn"]):                       # reversing beeps
            n = int(d["reverse"] / 0.32) + int(d["turn"] / 0.32)
            for j in range(n):
                self.hit(t + j * 0.32, "clack", 81, 0.25, hx, self.GF)
        if self.crossed(T["tip"]):
            self.fx(t, "motor", d["tip"] * 0.6, 0.45, hx, self.GF)
        for lg in self.logs:
            if self.crossed(lg["release"]):
                self.fx(t, "slide", 0.5, 0.5, self.pit[0], self.GF)
            if self.crossed(lg["t_shaft"]):
                self.hit(t, "thud", 40, 0.5, lg["x_in"], self.GF + 200)
            if self.crossed(lg["t_saw"]):
                self.fx(t, "saw", 0.35, 0.6, lg["x_in"], self.saw_y)
                for j in range(5):
                    self.hit(t + j * 0.05, "clack", self.note(j + 2), 0.35, lg["x_in"], self.saw_y)
                self.burst(lg["x_in"], self.saw_y, 34, SAWDUST, 520, 0.9, 3.5, g=700, spread=math.pi)
        for c in self.chunks:
            if self.crossed(c["t_hit"]):
                xh = c["x0"] + c["vx"] * (c["t_hit"] - c["t0"]) * 0.6
                if c["j"] in (0, 3):
                    self.fx(t, "splash", 0.5, 0.45, xh, self.vat_full)
                self.burst(xh, self.vat_full, 7, GREEN, 380, 0.55, 5, g=1800, glow=True, spread=0.7)
        if self.crossed(T["drop"]):
            self.fx(t, "bubble", T["build"] - T["drop"], 0.35, (self.vat[0] + self.vat[1]) / 2, self.vat_full)
        for mi in range(3):
            if self.crossed(T["grow"] + mi * 0.35):
                for j in range(4):
                    self.hit(t + j * 0.28, "soft_bell", self.note(mi * 2 + j, -1), 0.35, self.grow_x[mi], self.vat_full)
            if self.crossed(T["grab"] + mi * 0.15):
                self.fx(t, "servo", 0.9, 0.4, self.grow_x[mi], self.rail_y)
            if self.crossed(T["carry"] + mi * 0.15):
                self.fx(t, "servo", 1.4, 0.35, self.grow_x[mi], self.rail_y)
        if self.crossed(T["carry"] + 0.4):
            self.fx(t, "gurgle", T["build"] - T["carry"] - 0.4, 0.6, (self.vat[0] + self.vat[1]) / 2, self.vat_bottom)
        # build: parts fly in on arms; clunk on contact
        for (mi, name), (s, e) in self.parts_t.items():
            m = self.monsters[mi]
            m.attach[name] = settle(seg(t, s, e), 0.04)
            if self.crossed(s):
                self.fx(t, "servo", e - s, 0.3, self.stands[mi], self.GF2 - 300)
            if self.crossed(e):
                j = list(self.parts_t).index((mi, name))
                self.hit(t, "clunk", self.note(j), 0.55, self.stands[mi], self.GF2 - 200)
        # orbs + waking up
        for mi, m in enumerate(self.monsters):
            o0, o1 = self.orb_times(mi)
            if self.crossed(o0):
                self.fx(t, "whoosh", o1 - o0, 0.4, self.stands[mi], self.GF2 - 500)
            if self.crossed(o1):
                for j, n in enumerate((0, 2, 4)):
                    self.hit(t + j * 0.09, "chime", self.note(n + mi, 0), 0.5, self.stands[mi], self.GF2 - 300)
                ox, oy = m.orb_pos()
                self.burst(ox, oy, 30, ORB, 380, 0.8, 4, g=0, glow=True)
            m.orb_in = smoothstep(seg(t, o1 - 0.05, o1 + 0.12))
            m.alive = smootherstep(seg(t, o1 + 0.1, o1 + 0.1 + d["wake"]))
            if m.alive > 0 and t < T["walk"]:
                m.x, m.y = self.stands[mi], self.GF2
        if self.crossed(T["release"]):
            self.fx(t, "servo", d["release"], 0.35, self.stands[1], self.rail_y)
        # walking / training / exit
        if t >= T["walk"]:
            for mi, m in enumerate(self.monsters):
                x, y, *_ , walking = self.monster_pose(mi, t)
                vx = (x - m.x) / dt if dt > 0 else 0.0
                m.x, m.y = x, y
                m.walk = walking
                m.gait += dt * 9 * walking
                m.wheel_rot += vx * dt / (46 * m.k)
        if self.crossed(T["walk"]) or self.crossed(T["passed"] + 0.4):
            for j in range(int(d["walk"] / 0.3)):
                self.hit(t + j * 0.3, "clack", self.note(j % 3, -1), 0.25, self.stands[1], self.GF2)
        if self.crossed(T["train"]):
            self.bed.update({"pulse_from": t, "pulse_bpm": self.p.get("pulse_bpm", 84), "pulse_gain": 0.8})
        self._training_sounds(t)
        if self.crossed(T["passed"]):
            for j, n in enumerate((0, 2, 4, 7)):
                self.hit(t + j * 0.12, "soft_bell", self.note(n, 0) if n < 7 else self.note(0, 1), 0.6,
                         self.tramp_x, self.GF2 - 900)
        if self.crossed(T["door"]):
            self.fx(t, "motor", d["door"], 0.6, self.door_x, self.GF2 - 300)
            self.fx(t, "hiss", 0.8, 0.3, self.door_x, self.GF2 - 300)
        if self.crossed(T["exit"]):
            self.fx(t, "rustle", 2.0, 0.4, self.door_x + 400, self.GF2 - 300)
        # particles
        alive = []
        for p in self.particles:
            p.age += dt
            if p.age >= p.life:
                continue
            p.vy += p.g * dt
            if p.kind == "leaf":
                p.vx *= 1 - 1.5 * dt
                p.vy = min(p.vy, 120)
                p.x += math.sin(p.age * 5 + p.r) * 40 * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.particles = alive
        if t >= T["end"] and not self.done:
            self.done = True
            self.stats.update({"summary": "Tree Monsters: 5 trees -> 30 chunks -> 3 monsters (blue wheels, "
                                          "orange tentacles, purple teeth), trained, out to the forest",
                               "story_s": round(t, 2), "timeline": {k: round(v, 2) for k, v in T.items()}})
        self.prev_t = t

    def orb_times(self, mi):
        """(orb leaves the tube, orb lands) - Toby's blue one first."""
        d = self.d
        o0 = self.T["orbs"] + mi * d["orbs"] / 3.4
        return o0, o0 + d["orbs"] / 3.4 * 0.9

    def _training_sounds(self, t):
        T, d = self.T, self.d
        if not (T["train"] <= t < T["passed"]):
            return
        R, rd, sw = d["rounds"], d["round"], d["swap"]
        for r in range(R):
            r0 = T["train"] + r * (rd + sw)
            for mi in range(3):
                st, x = self.train_spot(mi, r)
                if st == "bag":
                    k = 0
                    while k * 0.7 + 0.35 < rd:
                        if self.crossed(r0 + k * 0.7 + 0.35):
                            self.hit(t, "thud", 40, 0.7, self.bag_x, self.GF2 - 200)
                        k += 1
                elif st == "tramp":
                    k = 0
                    while k * 1.0 < rd:
                        if self.crossed(r0 + k * 1.0 + 0.001):
                            self.hit(t, "pluck", self.note(k + mi, -1), 0.55, self.tramp_x, self.GF2 - 70)
                        k += 1
                else:
                    k = 0
                    while k * 0.75 < rd:
                        if self.crossed(r0 + k * 0.75 + 0.2):
                            self.hit(t, "clack", self.note(k * 2 + mi, -1), 0.3, x, self.GF2 - 130)
                        k += 1

    # ------------------------------------------------------------------ drawing

    def canvas_options(self):
        return {"glow": 0.0, "grain": self.v.get("grain", 1.2), "background": BG,
                "vignette": self.v.get("vignette", 0.45)}

    def fall_angle(self, u):
        return -math.radians(84) * (u * u)

    def draw(self, cv, t, frame):
        if self.scv is None:
            self.glow = HeatGlow(cv, self.v.get("glow", 1.0), self.v.get("glow_radius", 1.2))
            self.scv = Shifted(cv)
        self.glow.clear()
        # world -> screen: Shifted handles y; x by an Xform offset
        self.scv.dy = self.cam_y
        # zoom about the frame center (world point under it stays put)
        cx, cy = self.cam_x + self.w / 2, self.cam_y + self.h / 2
        c = Xform(self.scv, -self.cam_x, 0, 0.0, self.zoom, cx, cy)
        self.wcv = c
        self._draw_sky(cv, c, t)
        self._draw_ground(c, t)
        self._draw_interior(c, t)
        self._draw_training_room(c, t, back=True)
        self._draw_shaft(c, t)
        self._draw_vat(c, t, back=True)
        self._draw_chunks(c, t)
        self._draw_vat(c, t, back=False)
        self._draw_build_bay(c, t)
        self._draw_claws(c, t)
        self._draw_monsters(c, t)
        self._draw_training_room(c, t, back=False)
        self._draw_trees(c, t)
        self._draw_harvester(c, t)
        self._draw_falling_logs(c, t)
        self._draw_saws(c, t)
        self._draw_particles(c)
        self._draw_cliff_front(c, t)
        self.glow.apply(cv)

    def visible(self, x0, x1, y0=None, y1=None):
        if x1 < self.cam_x - 50 or x0 > self.cam_x + self.w + 50:
            return False
        if y0 is not None and (y1 < self.cam_y - 50 or y0 > self.cam_y + self.h + 50):
            return False
        return True

    def _glow(self, fn):
        self.glow.begin(self.wcv)
        fn(self.wcv)
        self.glow.end(self.wcv)

    # ----- sky, ground, earth -----

    def _draw_sky(self, cv, c, t):
        # stars + moon nearly fixed on screen (slow parallax); the ground and the factory cover them
        W, H = self.w + 200, self.h
        for sx, sy, r, b in self.stars:
            x = (sx - self.cam_x * 0.08) % W - 100 + self.cam_x
            y = (sy - self.cam_y * 0.08) % H + self.cam_y
            tw = 0.75 + 0.25 * math.sin(t * 1.3 + sx)
            c.circle(x, y, r, SKY_STAR * b * tw * 0.6)
        mx, my = self.cam_x + self.w * 0.76, self.cam_y + self.h * 0.13 - self.cam_y * 0.03
        ground = self.GF if mx < self.door_x else self.GF2
        if my < ground - 120 and not (self.interior[0] - 100 < mx < self.interior[1] + 160 and my > self.GF - 100):
            c.circle(mx, my, 70, MOON * 0.85)
            c.circle(mx - 18, my - 14, 16, MOON * 0.7)
            c.circle(mx + 22, my + 18, 10, MOON * 0.72)
            self._glow(lambda g: g.circle(mx, my, 80, MOON * 0.28))
        # far tree line silhouettes on both levels (parallax 0.4)
        for fx_, s in self.far_trees:
            x = fx_ + self.cam_x * 0.4
            for base in (self.GF, self.GF2):
                if base == self.GF2 and x < self.door_x + 100:
                    continue
                if not self.visible(x - 120, x + 120):
                    continue
                h = 380 * s
                c.polygon([(x - 14, base), (x + 14, base), (x + 10, base - h * 0.5), (x - 10, base - h * 0.5)], LEAF_FAR)
                c.circle(x, base - h * 0.72, h * 0.28, LEAF_FAR)
                c.circle(x - h * 0.15, base - h * 0.6, h * 0.2, LEAF_FAR)
                c.circle(x + h * 0.16, base - h * 0.62, h * 0.21, LEAF_FAR)

    def _draw_ground(self, c, t):
        GF, GF2, X1 = self.GF, self.GF2, self.door_x
        L = self.cam_x - 200
        R = self.cam_x + self.w + 200
        deep = GF2 + 2000
        # plateau earth (left of the cliff), lower ground (right)
        if L < X1:
            rect(c, L, GF, min(R, X1), deep, EARTH)
            for y in np.arange(GF + 60, deep, 90):        # strata
                c.line(L, y + 10 * math.sin(y), min(R, X1), y - 10 * math.sin(y * 0.7), EARTH_DARK, 3)
            rect(c, L, GF - 6, min(R, X1), GF + 4, GRASS)
        if R > X1:
            rect(c, max(L, X1), GF2, R, deep, EARTH)
            rect(c, max(L, X1), GF2 - 6, R, GF2 + 4, GRASS)

    def _draw_cliff_front(self, c, t):
        """Cliff face around the exit door (drawn over the room edge)."""
        X1, GF, GF2 = self.door_x, self.GF, self.GF2
        if not self.visible(X1 - 120, X1 + 140):
            return
        dh = 620
        c.polygon([(X1 - 40, GF), (X1 + 60, GF), (X1 + 60, GF2 - dh), (X1 - 40, GF2 - dh)], EARTH)
        c.line(X1 + 60, GF, X1 + 60, GF2 - dh, EARTH_DARK, 4)
        rect(c, X1 - 40, GF - 6, X1 + 60, GF + 4, GRASS)
        # door frame + the rolling door
        fx0, fx1 = X1 - 40, X1 + 60
        machine_block(c, fx0, GF2 - dh - 40, fx1, GF2 - dh, STEEL)
        u = smootherstep(seg(self._t, self.T["door"], self.T["door"] + self.d["door"]))
        bottom = lerp(GF2, GF2 - dh + 30, u)
        if bottom > GF2 - dh + 32:
            rect(c, fx0 + 10, GF2 - dh, fx1 - 10, bottom, IRON)
            for y in np.arange(GF2 - dh + 30, bottom, 40):
                c.line(fx0 + 10, y, fx1 - 10, y, IRON * 0.7, 2)
            rect(c, fx0 + 10, bottom - 14, fx1 - 10, bottom, HAZARD * 0.7)
        lamp = SIGN_GREEN if u > 0 else LAMP
        c.circle(X1 + 10, GF2 - dh - 20, 9, lamp)
        self._glow(lambda g: g.circle(X1 + 10, GF2 - dh - 20, 14, lamp * 0.6))

    def _draw_trees(self, c, t):
        T = self.T
        for i, x in enumerate(self.trees_x):
            if not self.visible(x - 900, x + 300):
                continue
            stump_y = self.GF - 40
            c.polygon([(x - 25, self.GF), (x + 25, self.GF), (x + 22, stump_y), (x - 22, stump_y)], TRUNK)
            if t < T[f"fall{i}"]:
                cut = seg(t, T[f"cut{i}"], T[f"fall{i}"])
                tree(c, x, self.GF, self.tree_h, 100 + i)
                if cut > 0:     # the cut line
                    c.line(x - 25, stump_y, x - 25 + 50 * cut, stump_y, EARTH_DARK, 4)
                    c.polygon([(x - 25, stump_y - 4), (x - 25 + 50 * cut, stump_y - 2), (x - 25, stump_y + 4)], SAWDUST * 0.8)
            elif t < T[f"load{i}"]:
                u = seg(t, T[f"fall{i}"], T[f"load{i}"])
                ang = self.fall_angle(u)
                tc = Xform(c, ang=ang, px=x, py=stump_y)
                tree(tc, x, stump_y, self.tree_h - 40, 100 + i)
            c.polygon([(x - 22, stump_y), (x + 22, stump_y), (x + 20, stump_y - 4), (x - 20, stump_y - 4)],
                      SAWDUST * 0.7)
        # decorative trees on the plateau beyond the pit, and the lower forest outside
        for j, x in enumerate((4050, 4420, 4900, 5350, 5800, 6250, 6700, 7150)):
            if self.visible(x - 250, x + 250):
                tree(c, x, self.GF, self.tree_h * (0.85 + 0.1 * (j % 3)), 300 + j)
        for j, x in enumerate(self.outside_trees):
            if self.visible(x - 250, x + 250):
                tree(c, x, self.GF2, self.tree_h * (0.9 + 0.1 * (j % 2)), 400 + j)

    # ----- harvester -----

    def _draw_harvester(self, c, t):
        hx, face, turn, tip, mov = self.harvester(t)
        if not self.visible(hx - 500, hx + 500):
            return
        GF = self.GF
        hc = Xform(c, fx=face * abs(turn) if abs(turn) > 0.02 else 0.02, px=hx, py=GF)
        x = hx
        L = 560
        # tracks
        tr0, tr1 = x - L / 2 + 10, x + L / 2 - 120
        rect(hc, tr0 + 30, GF - 70, tr1 - 30, GF, RUBBER_DARK)
        hc.circle(tr0 + 35, GF - 35, 35, RUBBER_DARK)
        hc.circle(tr1 - 35, GF - 35, 35, RUBBER_DARK)
        roll = (hx * 0.05) % (2 * math.pi)
        for wx in np.linspace(tr0 + 35, tr1 - 35, 5):
            hc.circle(wx, GF - 35, 22, STEEL)
            hc.line(wx, GF - 35, wx + math.cos(roll) * 18, GF - 35 + math.sin(roll) * 18, STEEL * 0.6, 3)
        off = (hx * 0.7) % 26
        for k_ in range(int((tr1 - tr0) / 26) + 1):
            px = tr0 + 30 + ((k_ * 26 + off) % (tr1 - tr0 - 60))
            hc.line(px, GF - 2, px, GF - 8, STEEL * 0.8, 3)
        # chassis
        machine_block(hc, x - L / 2, GF - 120, x + L / 2 - 90, GF - 70, MACHINE)
        for sx_ in np.arange(x - L / 2 + 10, x + L / 2 - 100, 40):
            hc.line(sx_, GF - 80, sx_ + 20, GF - 110, HAZARD * 0.6, 4)
        # cab (front)
        cab0, cab1 = x + 40, x + L / 2 - 100
        machine_block(hc, cab0, GF - 330, cab1, GF - 120, MACHINE)
        rect(hc, cab0 + 20, GF - 310, cab1 - 16, GF - 220, np.array([40, 60, 72]))
        hc.line(cab0 + 30, GF - 300, cab0 + 70, GF - 230, np.array([80, 104, 118]), 3)
        hc.circle(cab0 + 70, GF - 260, 16, np.array([28, 30, 36]))     # driver silhouette
        rect(hc, cab0 + 58, GF - 244, cab0 + 82, GF - 226, np.array([28, 30, 36]))
        machine_block(hc, cab0 - 6, GF - 346, cab1 + 6, GF - 330, MACHINE * 0.9)
        # roof beacon + headlight
        beacon = 0.5 + 0.5 * math.sin(t * 6)
        hc.circle(cab0 + 30, GF - 356, 9, HAZARD * (0.6 + 0.4 * beacon))
        hc.circle(cab1 - 6, GF - 200, 10, LAMP)
        gl = Xform(self.wcv, fx=face * abs(turn) if abs(turn) > 0.02 else 0.02, px=hx, py=GF)
        self.glow.begin(self.wcv)
        gl.circle(cab0 + 30, GF - 356, 14, HAZARD * 0.5 * beacon)
        gl.circle(cab1 - 6, GF - 200, 18, LAMP * 0.55)
        if turn > 0.5:
            gl.polygon([(cab1, GF - 210), (cab1 + 420, GF - 300), (cab1 + 420, GF - 40), (cab1, GF - 190)], LAMP * 0.07)
        self.glow.end(self.wcv)
        # boom + saw (front)
        sx_, sy_ = x + L / 2 + 40, GF - 70
        hc.line(cab1 - 20, GF - 150, sx_, sy_, MACHINE * 1.1, 26)
        hc.line(cab1 - 20, GF - 150, sx_, sy_, lighten(MACHINE, 1.3), 3)
        spin = t * (24 if self._cutting(t) else 9)
        saw_blade(hc, sx_, sy_, 62, spin)
        rect(hc, sx_ - 70, sy_ - 78, sx_ + 10, sy_ - 56, HAZARD * 0.75)    # blade guard
        # hopper (back), tips about its rear-bottom corner
        hp0, hp1 = x - L / 2 + 10, x + 10
        piv = (hp0, GF - 120)
        hpc = Xform(hc, ang=-tip, px=piv[0], py=piv[1])
        # logs inside (drawn first, the near wall hides their lower half)
        n_loaded = sum(1 for i in range(len(self.trees_x)) if t >= self.T[f"load{i}"] + self.d["load"])
        for j in range(n_loaded):
            if self._log_released(j, t):
                continue
            ly = GF - 168 - (j % 3) * 26 - (j // 3) * 30
            lx = (hp0 + hp1) / 2 + ((j * 37) % 30 - 15)
            self._log(hpc, lx, ly, 0.0)
        # log being loaded (from the fallen tree into the hopper)
        for i, tx in enumerate(self.trees_x):
            T0, T1 = self.T[f"load{i}"], self.T[f"load{i}"] + self.d["load"]
            if T0 <= t < T1:
                u = smootherstep(seg(t, T0, T1))
                ang = self.fall_angle(1.0)
                Lt = self.tree_h * 0.35
                sx0, sy0 = tx + math.sin(ang) * Lt, GF - 40 - math.cos(ang) * Lt
                j = i
                ly = GF - 168 - (j % 3) * 26 - (j // 3) * 30
                lx = (hp0 + hp1) / 2 + ((j * 37) % 30 - 15)
                self._log(c, lerp(sx0, lx, u), lerp(sy0, ly - 60 * math.sin(math.pi * u), u),
                          lerp(ang + math.pi / 2, 0.0, u))
        hpc.polygon([(hp0, GF - 120), (hp1, GF - 120), (hp1 + 20, GF - 300), (hp0 - 30, GF - 290)], MACHINE * 0.75)
        hpc.polygon([(hp0, GF - 120), (hp1, GF - 120), (hp1 + 14, GF - 180), (hp0 - 14, GF - 178)], MACHINE)
        hpc.line(hp0 - 14, GF - 178, hp1 + 14, GF - 180, lighten(MACHINE, 1.4), 3)
        hpc.line(hp0 - 30, GF - 290, hp1 + 20, GF - 300, lighten(MACHINE, 1.2), 3)
        for k_ in range(4):
            xx = lerp(hp0 + 20, hp1 - 20, k_ / 3)
            hpc.line(xx, GF - 125, xx, GF - 175, MACHINE * 0.8, 4)
        # tipping ram
        if tip > 0:
            hc.line(hp1 - 40, GF - 120, hp1 - 60, GF - 120 - 140 * math.sin(tip), STEEL, 12)

    def _cutting(self, t):
        return any(self.T[f"cut{i}"] <= t < self.T[f"fall{i}"] for i in range(len(self.trees_x)))

    def _log(self, c, x, y, ang, L=None, r=22):
        L = L or self.log_len
        ca, sa = math.cos(ang), math.sin(ang)
        hx, hy = ca * L / 2, sa * L / 2
        nx, ny = -sa * r, ca * r
        c.polygon([(x - hx + nx, y - hy + ny), (x + hx + nx, y + hy + ny), (x + hx - nx, y + hy - ny),
                   (x - hx - nx, y - hy - ny)], TRUNK)
        c.line(x - hx * 0.9 + nx * 0.3, y - hy * 0.9 + ny * 0.3, x + hx * 0.9 + nx * 0.3, y + hy * 0.9 + ny * 0.3, BARK, 3)
        c.circle(x + hx, y + hy, r, SAWDUST * 0.85)
        c.circle(x + hx, y + hy, r * 0.55, SAWDUST * 0.7)

    def _log_released(self, j, t):
        return t >= self.logs[j]["release"]

    def _draw_falling_logs(self, c, t):
        hx, face, turn, tip, mov = self.harvester(t)
        GF = self.GF
        for j, lg in enumerate(self.logs):
            r0 = lg["release"]
            if not (r0 <= t < lg["t_saw"]):
                continue
            if t < lg["t_shaft"]:
                u = (t - r0) / (lg["t_shaft"] - r0)
                # slide off the hopper lip (rear = right side after turning) into the funnel
                x0, y0 = hx + 290, GF - 170
                x = lerp(x0, lg["x_in"], u)
                y = y0 - 80 * math.sin(math.pi * u) + (GF + 60 - y0) * u * u
                ang = lerp(-0.3, math.pi / 2 * 0.6, u) + lg["spin"] * 0.2
            else:
                dt = t - lg["t_shaft"]
                x = lg["x_in"]
                y = GF + 60 + 250 * dt + 1300 * dt * dt
                ang = lerp(math.pi / 2 * 0.6, math.pi / 2, min(1.0, dt * 3)) + lg["spin"] * 0.15 * math.sin(dt * 4)
            self._log(c, x, y, ang)

    # ----- shaft + saws -----

    def _draw_interior(self, c, t):
        """Cut-away factory interior under the forest: back wall, girders, pipes, lamps."""
        X0, X1 = self.interior
        top, bot = self.ceil, self.GF2
        L, R = max(X0, self.cam_x - 50), min(X1, self.cam_x + self.w + 50)
        if R <= L:
            return
        rect(c, L, top, R, bot, INTERIOR)
        # parallax girders on the back wall
        par = 0.35
        off = self.cam_x * par
        for gx in np.arange(X0 + 120 - (off % 300), X1, 300):
            if L - 40 < gx < R + 40:
                rect(c, gx, top, gx + 30, bot, FAR)
                c.line(gx + 2, top, gx + 2, bot, lighten(FAR, 1.2), 2)
        for gy in (top + 120, top + 520, bot - 420):
            c.line(L, gy, R, gy, FAR, 9)
        for gx in np.arange(X0 + 270 - (off % 600), X1, 600):
            if L - 300 < gx < R:
                c.line(gx, top + 120, gx + 300, top + 520, FAR, 6)
                c.line(gx + 300, top + 120, gx, top + 520, FAR, 6)
        # ceiling slab + pipes
        rect(c, L, top, R, top + 36, MID)
        c.line(L, top + 36, R, top + 36, lighten(MID, 1.4), 2)
        for py, th in ((top + 60, 22), (top + 96, 12)):
            rect(c, L, py, R, py + th, MID)
            c.line(L, py + 2, R, py + 2, lighten(MID, 1.3), 2)
        # hanging lamps (warm, dim)
        for lx in np.arange(X0 + 380, X1 - 100, 640):
            if L - 100 < lx < R + 100:
                c.line(lx, top + 36, lx, top + 220, CABLE, 3)
                c.polygon([(lx - 40, top + 250), (lx + 40, top + 250), (lx + 22, top + 220), (lx - 22, top + 220)], STEEL)
                self._glow(lambda g, lx=lx: (g.circle(lx, top + 254, 18, LAMP * 0.6),
                                             g.polygon([(lx - 40, top + 254), (lx + 40, top + 254), (lx + 190, bot),
                                                        (lx - 190, bot)], LAMP * 0.035)))
        # floor
        rect(c, L, bot, R, bot + 40, FLOOR)
        c.line(L, bot, R, bot, lighten(FLOOR, 1.9), 2)
        # earth band above the ceiling is part of the ground layer; edge lines
        c.line(L, top, R, top, EARTH_DARK, 4)

    def _draw_shaft(self, c, t):
        p0, p1 = self.pit
        s0, s1 = self.shaft
        GF, sy = self.GF, self.saw_y
        if not self.visible(p0 - 50, p1 + 50, GF - 100, sy + 400):
            return
        c.polygon([(p0, GF), (p1, GF), (s1, GF + 260), (s1, sy + 140), (s0, sy + 140), (s0, GF + 260)], INTERIOR * 0.85)
        for a, b in (((p0, GF), (s0, GF + 260)), ((p1, GF), (s1, GF + 260))):
            c.line(*a, *b, STEEL, 14)
            c.line(*a, *b, lighten(STEEL, 1.4), 2)
        for x in (s0, s1):
            c.line(x, GF + 260, x, sy + 140, STEEL, 14)
            c.line(x, GF + 260, x, sy + 140, lighten(STEEL, 1.3), 2)
        # hazard band on the pit rim
        for x in (p0, p1):
            rect(c, x - 30, GF - 10, x + 30, GF + 4, HAZARD * 0.8)
        # saw housing
        machine_block(c, s0 - 60, sy - 70, s0 + 4, sy + 70, IRON)
        machine_block(c, s1 - 4, sy - 70, s1 + 60, sy + 70, IRON)

    def _draw_saws(self, c, t):
        s0, s1 = self.shaft
        sy = self.saw_y
        if not self.visible(s0 - 100, s1 + 100, sy - 200, sy + 200):
            return
        busy = any(lg["t_saw"] - 0.3 < t < lg["t_saw"] + 0.4 for lg in self.logs)
        spin = t * (22 if busy else 10)
        n = 4
        for i in range(n):
            x = lerp(s0 + 20, s1 - 20, i / (n - 1))
            saw_blade(c, x, sy, 46, spin * (1 if i % 2 else -1) + i)
        c.line(s0, sy, s1, sy, STEEL * 0.7, 6)

    # ----- vat -----

    def _draw_vat(self, c, t, back):
        v0, v1 = self.vat
        rim, bot = self.vat_rim, self.vat_bottom
        if not self.visible(v0 - 80, v1 + 80, rim - 600, self.GF2 + 50):
            return
        lvl = self.liquid_y(t)
        if back:
            rect(c, v0, rim, v1, bot, IRON * 0.7)
            # liquid (glows)
            if lvl < bot - 2:
                wave = [(x, lvl + 4 * math.sin(x * 0.03 + t * 2)) for x in np.linspace(v0 + 14, v1 - 14, 40)]
                body = wave + [(v1 - 14, bot - 10), (v0 + 14, bot - 10)]
                c.polygon(body, GREEN_DEEP)
                c.polyline(wave, GREEN * 0.8, 4)
                self._glow(lambda g: (g.polygon(body, GREEN * 0.16), g.polyline(wave, GREEN * 0.55, 6)))
                # bubbles
                for b in range(10):
                    ph = (t * 0.6 + b * 0.37) % 1.0
                    bx = lerp(v0 + 40, v1 - 40, ((b * 0.618) % 1.0))
                    by = lerp(bot - 20, lvl, ph)
                    if by > lvl + 6:
                        c.circle(bx, by, 4 + 3 * ph, GREEN * 0.7)
            # drain swirl
            if self.T["carry"] + 0.4 < t < self.T["build"]:
                cx = (v0 + v1) / 2
                for k_ in range(3):
                    a = t * 5 + k_ * 2.1
                    c.arc(cx, bot - 30, 30 + 14 * k_, math.degrees(a), math.degrees(a) + 120, GREEN * 0.9, 3)
            return
        # front wall (cut-away: low front lip so the inside shows), legs, plug pipe, label stripe
        c.polyline([(v0, rim - 10), (v0, bot), (v1, bot), (v1, rim - 10)], STEEL, 16)
        c.polyline([(v0, rim - 10), (v0, bot), (v1, bot), (v1, rim - 10)], lighten(STEEL, 1.35), 2)
        rect(c, v0 - 14, rim - 22, v0 + 14, rim, lighten(STEEL, 1.2))
        rect(c, v1 - 14, rim - 22, v1 + 14, rim, lighten(STEEL, 1.2))
        for lx in (v0 + 40, v1 - 40):
            rect(c, lx - 14, bot, lx + 14, self.GF2, STEEL * 0.8)
        cx = (v0 + v1) / 2
        rect(c, cx - 24, bot, cx + 24, self.GF2 + 40, IRON)
        plug_open = self.T["carry"] + 0.4 < t
        rect(c, cx - 40, bot - 8, cx + 40, bot + 6, HAZARD * (0.9 if plug_open else 0.5))
        for x in np.arange(v0 + 30, v1 - 30, 60):
            c.line(x, bot - 40, x + 30, bot - 40, HAZARD * 0.35, 6)

    def _draw_chunks(self, c, t):
        if t < min(ch["t0"] for ch in self.chunks):
            return
        for ch in self.chunks:
            if t < ch["t0"]:
                continue
            x, y, rot, st = self.chunk_pos(ch, t)
            if st == "gone":
                continue
            mi = ch["grow"]
            if mi is not None and t >= self.T["grow"]:
                self._draw_grower(c, mi, ch, x, y, t)
                continue
            w, h = ch["w"], ch["h"]
            pts = [(x + math.cos(rot) * dx - math.sin(rot) * dy, y + math.sin(rot) * dx + math.cos(rot) * dy)
                   for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
            c.polygon(pts, TRUNK if st == "fall" else TRUNK * 0.85)
            c.polyline(pts, BARK, 2, closed=True)
            c.circle(x, y, min(w, h) * 0.25, SAWDUST * 0.7)

    def _draw_grower(self, c, mi, ch, x, y, t):
        m = self.monsters[mi]
        g = self.grow_amount(mi, t)
        rx, ry = m.body_size()
        cx_, cy_, _, _ = self.claw_state(mi, t)
        held = t >= self.T["grab"] + mi * 0.15 + self.d["grab"] * 0.55
        if held:
            bx, by = cx_, cy_ + ry
        else:
            bx, by = x, lerp(y, self.vat_full - 6 - ry * 0.35, g)
        if t >= self.T["build"] - 0.3:
            return              # the Monster object takes over (drawn in the build bay)
        w = lerp(ch["w"] / 2, rx, g)
        h = lerp(ch["h"] / 2, ry, g)
        body = ellipse(bx, by, w, h, 44)
        blob(c, body, WOOD_BODY)
        if g > 0.3:
            grain(c, bx, by + h * 0.5, w * 0.6, h * 0.25, WOOD_BODY)
        if 0 < g < 1 or not held:
            pulse = 0.6 + 0.4 * math.sin(t * 5 + mi)
            self._glow(lambda gg: gg.polyline(body, GREEN * 0.35 * pulse * (1 - 0.6 * g * held), 6, closed=True))

    # ----- claws, build bay -----

    def _draw_claws(self, c, t):
        T = self.T
        if t > T["walk"] + 1:
            return
        x0 = self.grow_x[0] - 120
        x1 = self.stands[-1] + 160
        if not self.visible(x0, x1, self.rail_y - 50, self.GF2):
            return
        ry_ = self.rail_y
        rect(c, x0, ry_ - 16, x1, ry_ + 6, STEEL)
        c.line(x0, ry_ - 16, x1, ry_ - 16, lighten(STEEL, 1.4), 2)
        for hx in np.arange(x0 + 60, x1, 500):
            c.line(hx, self.ceil + 36, hx, ry_ - 16, STEEL * 0.8, 10)
        for mi in range(3):
            x, gy, carrying, opn = self.claw_state(mi, t)
            rect(c, x - 34, ry_ - 8, x + 34, ry_ + 30, IRON)
            c.circle(x - 18, ry_ - 4, 8, STEEL)
            c.circle(x + 18, ry_ - 4, 8, STEEL)
            c.line(x, ry_ + 30, x, gy - 26, CABLE, 3)
            rect(c, x - 22, gy - 34, x + 22, gy - 10, HAZARD * 0.75)
            rx = self.monsters[mi].body_size()[0] if carrying else 50
            spread = lerp(rx * 0.78, rx * 1.15, opn)
            for s in (-1, 1):
                p1 = (x + s * 18, gy - 20)
                p2 = (x + s * spread, gy + 26)
                p3 = (x + s * (spread - 14), gy + 60)
                c.line(*p1, *p2, STEEL, 9)
                c.line(*p2, *p3, STEEL, 8)

    def _draw_build_bay(self, c, t):
        T = self.T
        if not self.visible(self.stands[0] - 300, self.stands[-1] + 300):
            return
        top = self.ceil + 36
        # carrier arms for parts in flight
        for (mi, name), (s, e) in self.parts_t.items():
            if not (s - 0.3 <= t <= e + 0.6):
                continue
            m = self.monsters[mi]
            ax, ay = m.part_anchor(name)
            ox, oy = m.part_offset(name)
            gx, gy = ax + ox, ay + oy
            back = smoothstep(seg(t, e, e + 0.6))
            if back > 0:
                gy = lerp(gy, top + 200, back)
            c.line(gx, top, gx, gy - 30, STEEL * 0.85, 12)
            c.line(gx, top, gx, gy - 30, lighten(STEEL, 1.3), 2)
            rect(c, gx - 26, top - 4, gx + 26, top + 16, IRON)
            rect(c, gx - 16, gy - 34, gx + 16, gy - 18, HAZARD * 0.75)
            for sd in (-1, 1):
                c.line(gx + sd * 12, gy - 20, gx + sd * 20, gy - 2, STEEL, 6)
        # orb tubes
        if T["orbs"] - 1.5 <= t <= T["walk"] + 1:
            for mi, m in enumerate(self.monsters):
                ox, oy = m.orb_pos()
                tx = ox
                tend = oy - 260
                c.line(tx - 16, top, tx - 16, tend, STEEL * 0.7, 4)
                c.line(tx + 16, top, tx + 16, tend, STEEL * 0.7, 4)
                rect(c, tx - 22, tend - 8, tx + 22, tend + 4, IRON)
                o0, o1 = self.orb_times(mi)
                if t < o1:
                    u = seg(t, o0, o1)
                    yy = lerp(top + 40, tend, smoothstep(min(1.0, u * 1.6))) if u < 0.62 else lerp(tend, oy, ((u - 0.62) / 0.38) ** 2)
                    if t >= o0 - 1.2:
                        r = 16 * m.k / 0.55
                        c.circle(tx, yy, r, ORB)
                        c.circle(tx - r * 0.3, yy - r * 0.3, r * 0.3, lighten(ORB, 1.6))
                        self._glow(lambda g, yy=yy, tx=tx, r=r: g.circle(tx, yy, r * 1.6, ORB * 0.8))
        # stand plinths
        for sx in self.stands:
            rect(c, sx - 110, self.GF2 - 10, sx + 110, self.GF2 + 4, HAZARD * 0.5)

    def _draw_monsters(self, c, t):
        T = self.T
        if t < T["build"] - 0.3:
            return
        for mi, m in enumerate(self.monsters):
            if t < T["walk"]:
                m.x, m.y = self.stands[mi], self.GF2
                # held by the claw until released: body sits where the claw holds it
                cx_, gy, _, _ = self.claw_state(mi, t)
                rx, ry = m.body_size()
                bc = m.body_center()
                dy = (gy + ry) - bc[1]
                mc = Xform(c, cx_ - m.x, dy) if abs(dy) > 0.5 or abs(cx_ - m.x) > 0.5 else c
            else:
                x, y, dx, dy, ang, _ = self.monster_pose(mi, t)
                bc = m.body_center()
                mc = Xform(c, dx, dy, ang, 1.0, bc[0], bc[1]) if (dx or dy or ang) else c
            if not self.visible(m.x - 300, m.x + 300):
                continue
            m.draw(mc, t, self.glow)
            if T["orbs"] <= t < T["walk"]:
                o0, o1 = self.orb_times(mi)
                flash = max(0.0, 1 - (t - o1) / 0.8) if t >= o1 else 0.0
                if flash > 0:
                    ox, oy = m.orb_pos()
                    self._glow(lambda g, ox=ox, oy=oy, f=flash: g.circle(ox, oy, 60 + 120 * (1 - f), ORB * 0.5 * f))

    # ----- training room -----

    def _draw_training_room(self, c, t, back):
        X0, X1 = self.room
        GF2 = self.GF2
        if not self.visible(X0 - 100, X1 + 100):
            return
        if back:
            # partition with a wide opening, mats, equipment, sign
            rect(c, X0 - 30, self.ceil, X0 + 30, GF2 - 520, STEEL * 0.8)
            c.line(X0 - 30, GF2 - 520, X0 + 30, GF2 - 520, lighten(STEEL, 1.3), 2)
            rect(c, X0 + 40, GF2 - 6, X1 - 40, GF2 + 6, np.array([40, 52, 70]))
            # sign
            sx, sy = self.room_center(), GF2 - min(940, self.h * 0.72)
            rect(c, sx - 300, sy - 70, sx + 300, sy + 70, IRON * 0.8)
            c.polyline([(sx - 300, sy - 70), (sx + 300, sy - 70), (sx + 300, sy + 70), (sx - 300, sy + 70)],
                       STEEL, 4, closed=True)
            c.line(sx - 200, self.ceil + 36, sx - 200, sy - 70, CABLE, 3)
            c.line(sx + 200, self.ceil + 36, sx + 200, sy - 70, CABLE, 3)
            T = self.T
            passed = t >= T["passed"] + 0.5
            flick = T["passed"] <= t < T["passed"] + 0.5 and int(t * 20) % 2 == 0
            if t >= T["walk"]:
                txt, col = ("THEY PASSED", SIGN_GREEN) if passed else ("TRAINING", SIGN_WARM)
                if flick:
                    col = col * 0.25
                c.text(txt, sx, sy, 78 if passed else 88, col)
                self._glow(lambda g: g.polygon([(sx - 280, sy - 50), (sx + 280, sy - 50), (sx + 280, sy + 50),
                                                (sx - 280, sy + 50)], col * 0.10))
            else:
                c.text("TRAINING", sx, sy, 88, SIGN_WARM * 0.22)
            # punching bag
            bx = self.bag_x
            swing = 0.0
            for mi in range(3):
                if self.monsters[mi].punch > 0 and T["train"] <= t < T["passed"]:
                    swing = max(swing, self.monsters[mi].punch)
            ang = 0.25 * swing
            top = GF2 - 480
            c.line(bx, self.ceil + 36, bx, top, CABLE, 3)
            bc = Xform(c, ang=-ang, px=bx, py=top)
            bc.line(bx, top, bx, top + 50, CABLE, 3)
            bc.polygon(ellipse(bx, top + 170, 40, 120, 30), np.array([110, 40, 34]))
            bc.polyline(ellipse(bx, top + 170, 40, 120, 30), np.array([70, 26, 22]), 3, closed=True)
            bc.line(bx - 36, top + 110, bx + 36, top + 110, np.array([70, 26, 22]), 4)
            bc.line(bx - 36, top + 230, bx + 36, top + 230, np.array([70, 26, 22]), 4)
            # trampoline
            tx = self.tramp_x
            dip = 0.0
            for mi in range(3):
                st, _ = self.train_spot(mi, self._round(t))
                if st == "tramp" and T["train"] <= t < T["passed"]:
                    ph = ((t - self._round_start(t)) % 1.0)
                    dip = max(0.0, 1 - min(ph, 1 - ph) / 0.12) * 26
            c.line(tx - 150, GF2, tx - 130, GF2 - 70, STEEL, 8)
            c.line(tx + 150, GF2, tx + 130, GF2 - 70, STEEL, 8)
            c.polyline([(tx - 140, GF2 - 70), (tx, GF2 - 70 + dip), (tx + 140, GF2 - 70)], np.array([30, 34, 46]), 10)
            rect(c, tx - 150, GF2 - 80, tx - 120, GF2 - 64, HAZARD * 0.6)
            rect(c, tx + 120, GF2 - 80, tx + 150, GF2 - 64, HAZARD * 0.6)
            # balance beam
            b0, b1 = self.beam
            rect(c, b0, GF2 - 130, b1, GF2 - 110, np.array([150, 120, 84]))
            c.line(b0, GF2 - 130, b1, GF2 - 130, np.array([190, 160, 112]), 2)
            for lx in (b0 + 30, b1 - 30):
                c.line(lx, GF2 - 110, lx - 20, GF2, STEEL, 7)
                c.line(lx, GF2 - 110, lx + 20, GF2, STEEL, 7)
        else:
            pass

    def _round(self, t):
        d = self.d
        return int(min(d["rounds"] - 1, max(0.0, t - self.T["train"]) // (d["round"] + d["swap"])))

    def _round_start(self, t):
        d = self.d
        return self.T["train"] + self._round(t) * (d["round"] + d["swap"])

    # ----- particles -----

    def _draw_particles(self, c):
        for p in self.particles:
            a = 1 - p.age / p.life
            if p.kind == "leaf":
                ang = p.age * 4 + p.r
                dx, dy = math.cos(ang) * p.r, math.sin(ang) * p.r * 0.5
                c.polygon([(p.x - dx, p.y - dy), (p.x + dy * 0.6, p.y - dx * 0.3), (p.x + dx, p.y + dy),
                           (p.x - dy * 0.6, p.y + dx * 0.3)], p.col * (0.4 + 0.6 * a))
            elif p.glow:
                self._glow(lambda g, p=p, a=a: g.circle(p.x, p.y, p.r, p.col * a))
                c.circle(p.x, p.y, p.r * 0.7, p.col * a)
            else:
                c.circle(p.x, p.y, p.r, p.col * (0.3 + 0.7 * a))


RUBBER_DARK = np.array([24, 24, 28], np.float64)
