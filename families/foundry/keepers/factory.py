"""Forest Keepers act 1: the factory makes six monsters (docs/engines/foundry_keepers.md).

Same world idea as episode 1 (night forest plateau, cut-away factory underneath), extended:
  harvest 8 trees -> the truck pulls forward over the pit and BELLY-DUMPS (no turnaround)
  -> logs fall flat onto a bank of 5 saws -> 6 chunks each -> green vat -> 6 grow
  -> six claws carry them to the start of an indexing assembly line:
       CARVE (cutter orbits the rough lump) -> SAND -> PARTS -> BOLT -> SCAN
  -> the line ends at a dock: orbs drop, one per monster, and they wake up
  -> training room: 6 stations in rotation, then an obstacle-course run, one after another
  -> TRAINING / THEY PASSED / FOREST KEEPERS sign, badges, the cliff door opens, out they go.
"""
import math

import numpy as np

from ..products.monster import ORB, WOOD_BODY, Xform, ellipse, blob, grain
from ..style import FAR, MID, STEEL, IRON, FLOOR, CABLE
from ..tree_monsters import (EARTH, EARTH_DARK, GRASS, TRUNK, BARK, LEAF_FAR, INTERIOR, GREEN, GREEN_DEEP,
                             SAWDUST, MACHINE, HAZARD, LAMP, SIGN_WARM, SIGN_GREEN, RUBBER_DARK)
from .common import (Act, Night, lerp, lighten, machine_block, rect, saw_blade, seg, settle, smoothstep,
                     smootherstep, tree)

STATIONS = ["CARVE", "SAND", "PARTS", "BOLT", "SCAN"]
SCAN_GREEN = np.array([110, 255, 150], np.float64)
GOLD = np.array([255, 214, 120], np.float64)


class FactoryAct(Act):
    name = "factory"
    indoor = True

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        W = P.get("world", {})
        self.GF = 1600.0
        self.GF2 = self.GF + 1650.0
        self.n = len(scene.monsters)
        self.trees_x = W.get("trees", [700 + i * 330 for i in range(8)])
        self.tree_h = 700
        self.pit = W.get("pit", [3520, 3880])
        self.pc = (self.pit[0] + self.pit[1]) / 2
        self.shaft = [self.pc - 160, self.pc + 160]
        self.saw_y = self.GF + 820
        self.saws_x = [self.pc - 80 + 40 * i for i in range(5)]
        self.vat = W.get("vat", [3200, 4200])
        self.vat_rim = self.GF + 1170
        self.vat_full = self.vat_rim + 70
        self.vat_bottom = self.GF2 - 110
        self.rail_y = self.GF + 980
        self.ceil = self.GF + 300
        self.grow_x = [3300 + i * 160 for i in range(self.n)]
        self.D = W.get("line_pitch", 380)
        self.line0 = W.get("line0", 6700)
        self.pallet_y = self.GF2 - 34                     # monster feet while on the line
        self.room = W.get("room", [10900, 13300])
        self.door_x = self.room[1] + 100
        self.interior = [3080, self.door_x]
        self.night = Night(scene.particles.rng, self.GF, -1500, 15000)
        self.low_night = Night(scene.particles.rng, self.GF2, self.door_x, self.door_x + 3000)
        self._timeline(P.get("durations", {}))
        self._plan_logs()
        self.stats = {}

    # ------------------------------------------------------------------ timeline

    def _timeline(self, D):
        d = dict(intro=2.0, drive=0.9, cut=1.4, fall=1.2, load=0.7, to_pit=3.0, dump=4.0, drop=3.5, settle=2.0,
                 grow=5.0, grab=3.0, carry=6.0, move=1.4, work=6.8, dock_pan=5.5, orb=1.6, wake=2.0, step_down=2.0, walk=5.0,
                 rounds=3, round=7.0, swap=1.4, course_gap=2.2, course_run=7.0, passed=3.0, badge=0.8,
                 door=3.0, exit=6.0)
        d.update(D)
        self.d = d
        T, t = {}, d["intro"]
        for i in range(len(self.trees_x)):
            for k in ("drive", "cut", "fall", "load"):
                T[f"{k}{i}"] = t
                t += d[k]
        for k in ("to_pit", "dump", "drop", "settle", "grow", "grab", "carry"):
            T[k] = t
            t += d[k]
        self.cycles = 5 + self.n                         # index steps until every unit is on the dock
        T["line"] = t
        # the last unit's last work (SCAN) is in cycle n + 4; cycle n + 5 is only the move onto the dock
        t += (self.cycles - 1) * (d["move"] + d["work"]) + d["move"]
        T["dock_pan"] = t                                # camera glides right along the finished row
        t += d["dock_pan"]
        T["orbs"] = t
        t += self.n * d["orb"]
        for k in ("wake", "step_down", "walk"):
            T[k] = t
            t += d[k]
        T["train"] = t
        t += d["rounds"] * d["round"] + (d["rounds"] - 1) * d["swap"]
        T["course"] = t
        t += (self.n - 1) * d["course_gap"] + d["course_run"] + 0.8
        T["passed"] = t
        t += d["passed"]
        T["badges"] = t
        t += self.n * d["badge"] + 1.0
        for k in ("door", "exit"):
            T[k] = t
            t += d[k]
        T["end"] = t
        self.T = T
        self.dur = t

    def pulse_window(self):
        return self.t0 + self.T["train"], self.t0 + self.T["passed"] + 1.0

    # ------------------------------------------------------------------ harvester

    def harvester(self, t):
        """(center x, belly-door opening 0..1, moving)"""
        T, d = self.T, self.d
        L = 560
        front = lambda i: self.trees_x[i] - 100
        cx = lambda f: f - L / 2 - 40
        start = cx(self.trees_x[0] - 760)
        n = len(self.trees_x)
        if t < T["drive0"]:
            return start, 0.0, 0.0
        for i in range(n):
            if t < T[f"cut{i}"]:
                prev = start if i == 0 else cx(front(i - 1) + 60)
                u = smootherstep(seg(t, T[f"drive{i}"], T[f"cut{i}"]))
                return lerp(prev, cx(front(i)), u), 0.0, 1.0
            if t < T[f"fall{i}"]:
                return cx(front(i)) + 60 * smoothstep(seg(t, T[f"cut{i}"], T[f"fall{i}"])), 0.0, 0.3
            if i == n - 1 or t < T[f"drive{i + 1}"]:
                if i < n - 1:
                    return cx(front(i) + 60), 0.0, 0.0
        last = cx(front(n - 1) + 60)
        over = self.pc + 130                             # hopper center right over the pit
        if t < T["dump"]:
            u = smootherstep(seg(t, T["to_pit"], T["dump"]))
            return lerp(last, over, u), 0.0, 1.0 if 0 < u < 1 else 0.0
        if t < T["settle"]:
            op = smoothstep(seg(t, T["dump"], T["dump"] + 0.8)) * (1 - smoothstep(seg(t, T["drop"] + 1.0, T["drop"] + 2.0)))
            return over, op, 0.0
        u = seg(t, T["settle"], T["settle"] + 5.0)
        return over + 1800 * u * u, 0.0, 1.0 if u < 1 else 0.0

    def _plan_logs(self):
        rs = np.random.default_rng(self.s.seed + 21)
        T, d = self.T, self.d
        n = len(self.trees_x)
        g = 2600.0
        self.logs = []
        for i in range(n):
            rel = T["dump"] + 0.7 + i * (d["dump"] - 1.0) / n
            dist = self.saw_y - (self.GF - 130)
            t_f = math.sqrt(2 * dist / g)
            self.logs.append(dict(rel=rel, x=self.pc + rs.uniform(-8, 8), t_saw=rel + t_f, v=g * t_f,
                                  tilt=rs.uniform(-0.12, 0.12)))
        self.chunks = []
        slots = np.linspace(self.vat[0] + 50, self.vat[1] - 50, n * 6)
        rs.shuffle(slots)
        k = 0
        for li, lg in enumerate(self.logs):
            for j in range(6):
                x0 = lg["x"] - 100 + 40 * j
                y0 = self.saw_y
                v0 = lg["v"] * 0.55
                dist = self.vat_full - y0
                tf = (-v0 + math.sqrt(v0 * v0 + 2 * g * dist)) / g
                self.chunks.append(dict(log=li, j=j, x0=x0, y0=y0, vx=(j - 2.5) * rs.uniform(40, 110), v0=v0,
                                        t0=lg["t_saw"], t_hit=lg["t_saw"] + tf, rest_x=float(slots[k]),
                                        rot0=lg["tilt"], spin=rs.uniform(-5, 5), bob=rs.uniform(0, 6.28),
                                        w=rs.uniform(34, 42), h=rs.uniform(30, 38), grow=None))
                k += 1
        used = set()
        for mi, gx in enumerate(self.grow_x):
            best = min((c for c in self.chunks if id(c) not in used), key=lambda c: abs(c["rest_x"] - gx))
            used.add(id(best))
            best["grow"] = mi
            best["rest_x"] = gx

    def liquid_y(self, t):
        dr = smoothstep(seg(t, self.T["carry"] + 0.5, self.T["line"]))
        return lerp(self.vat_full, self.vat_bottom - 6, dr)

    def chunk_pos(self, c, t):
        if t < c["t_hit"]:
            dt = t - c["t0"]
            return c["x0"] + c["vx"] * dt, c["y0"] + c["v0"] * dt + 1300 * dt * dt, c["rot0"] + c["spin"] * dt, "fall"
        u = smootherstep(seg(t, c["t_hit"], c["t_hit"] + 1.4))
        xh = c["x0"] + c["vx"] * (c["t_hit"] - c["t0"])
        x = lerp(xh, c["rest_x"], u)
        y = self.liquid_y(t) - 6 + 5 * math.sin(t * 1.6 + c["bob"]) + 30 * (1 - u) * math.exp(-(t - c["t_hit"]) * 3)
        rot = c["rot0"] + c["spin"] * (c["t_hit"] - c["t0"]) * (1 - u) + 0.15 * math.sin(t + c["bob"])
        if c["grow"] is None and t > self.T["carry"]:
            dr = seg(t, self.T["carry"] + 0.5, self.T["line"])
            cx = (self.vat[0] + self.vat[1]) / 2
            order = abs(c["rest_x"] - cx) / ((self.vat[1] - self.vat[0]) / 2)
            v = smoothstep((dr - 0.5 - 0.3 * (1 - order)) / 0.35)
            x = lerp(x, cx + 20 * math.sin(t * 6 + c["bob"]), v)
            y = lerp(y, self.vat_bottom + 80, v * v)
            if v >= 1:
                return x, y, rot, "gone"
            return x, y, rot + v * 6, "drain"
        return x, y, rot, "float"

    def grow_amount(self, mi, t):
        return smootherstep(seg(t, self.T["grow"] + mi * 0.3, self.T["grow"] + self.d["grow"] * 0.75 + mi * 0.15))

    # ------------------------------------------------------------------ line

    def queue_x(self, j):
        return self.line0 - (j + 1) * self.D

    def line_state(self, t):
        """(cycle index 1.., phase 'move'/'work', progress 0..1) or None before/after the line."""
        T, d = self.T, self.d
        if t < T["line"] or t >= T["dock_pan"]:
            return None
        cl = d["move"] + d["work"]
        k = int((t - T["line"]) // cl)
        r = t - T["line"] - k * cl
        if r < d["move"]:
            return k + 1, "move", r / d["move"]
        return k + 1, "work", (r - d["move"]) / d["work"]

    def unit_p(self, j, t):
        """Line position (float): -1 - j = queue, 0..4 = stations, 5.. = dock."""
        T, d = self.T, self.d
        if t < T["line"]:
            return -1.0 - j
        cl = d["move"] + d["work"]
        k = min(self.cycles, int((t - T["line"]) // cl))
        r = t - T["line"] - k * cl
        steps = k + (smootherstep(r / d["move"]) if (r < d["move"] and k < self.cycles) else (1.0 if k < self.cycles else 0.0))
        steps = min(steps, float(self.cycles))
        return -1.0 - j + steps

    def unit_x(self, j, t):
        return self.line0 + self.unit_p(j, t) * self.D

    def station_unit(self, i, cycle):
        """Which unit sits at station i during cycle `cycle` (or None)."""
        j = cycle - 1 - i
        return j if 0 <= j < self.n else None

    def dock_x(self, j):
        return self.line0 + (self.cycles - 1 - j) * self.D

    def orb_times(self, j):
        o0 = self.T["orbs"] + j * self.d["orb"]
        return o0, o0 + self.d["orb"] * 0.7

    # ------------------------------------------------------------------ training

    def stations(self):
        R = self.room
        return [("rope", R[0] + 220), ("bag", R[0] + 560), ("tramp", R[0] + 930), ("beam", R[0] + 1280),
                ("logs", R[0] + 1640), ("hurdles", R[0] + 2000)]

    def spot(self, j, r):
        st = self.stations()
        return st[(j + r) % len(st)]

    def course_t(self, j):
        T, d = self.T, self.d
        t0 = T["course"] + j * d["course_gap"]
        return t0, t0 + d["course_run"] * (0.92 + 0.16 * ((j * 0.618) % 1.0))

    def pose(self, j, t):
        """(x, feet y, dx, dy, ang, walking) for monster j once it is awake."""
        T, d = self.T, self.d
        m = self.s.monsters[j]
        dx0 = self.dock_x(j)
        if t < T["step_down"]:
            return dx0, self.pallet_y, 0, 0, 0, 0.0
        if t < T["walk"]:
            u = seg(t, T["step_down"] + j * 0.15, T["step_down"] + 0.9 + j * 0.15)
            return dx0 + 60 * u, lerp(self.pallet_y, self.GF2, u), 0, -90 * math.sin(math.pi * u), 0, 0.0
        sx = self.spot(j, 0)[1]
        if t < T["train"]:
            u = smootherstep(seg(t, T["walk"] + j * 0.25, T["train"] - 0.2))
            return lerp(dx0 + 60, sx, u), self.GF2, 0, -abs(math.sin(u * 22)) * 10 * (m.kind not in ("wheels", "lantern")), 0, 1.0 if 0 < u < 1 else 0.0
        R, rd, sw = d["rounds"], d["round"], d["swap"]
        if t < T["course"]:
            tr = t - T["train"]
            r = int(min(R - 1, tr // (rd + sw)))
            inr = tr - r * (rd + sw)
            if inr > rd:
                u = smootherstep((inr - rd) / sw)
                x0, x1 = self.spot(j, r)[1], self.spot(j, r + 1)[1]
                return lerp(x0, x1, u), self.GF2, 0, -abs(math.sin(u * math.pi * 3)) * 14, 0, 1.0
            st, x = self.spot(j, r)
            return self._station_pose(j, st, x, inr, t)
        m.punch = 0.0
        m.spring = 0.0
        c0, c1 = self.course_t(j)
        start_x, end_x = self.room[0] + 120 - j * 130, self.room[1] - 220 - j * 190
        lastx = self.spot(j, R - 1)[1]
        if t < c0:                                   # line up at the start
            u = smootherstep(seg(t, T["course"] - 0.2, T["course"] + 1.6))
            return lerp(lastx, start_x, u), self.GF2, 0, 0, 0, 1.0 if 0 < u < 1 else 0.0
        if t < c1:
            u = (t - c0) / (c1 - c0)
            x = lerp(start_x, end_x, u)
            return x, self.GF2, 0, -self._course_dy(x, t, j), self._course_ang(x, j), 1.0
        # after the run: wait at the finish; then gather in front of the sign / walk out of the door
        if t < T["door"] + 0.5:
            return end_x, self.GF2, 0, 0, 0, 0.0
        u = seg(t, T["door"] + 0.6 + (self.n - 1 - j) * 0.35, T["end"] - 1.2)
        out = self.door_x + 260 + (self.n - 1 - j) * 190         # a spread-out line just outside the door
        x = lerp(end_x, out, smootherstep(u))
        return x, self.GF2, 0, -abs(math.sin(u * 30)) * 10 * (0 < u < 1), 0, 1.0 if 0 < u < 1 else 0.0

    def _course_dy(self, x, t, j):
        st = dict(self.stations())
        h = 0.0
        for hx in (st["hurdles"] - 120, st["hurdles"] + 120, st["rope"] + 160):
            if abs(x - hx) < 90:
                h = max(h, 150 * math.cos((x - hx) / 90 * math.pi / 2))
        tx = st["tramp"]
        if abs(x - tx) < 200:
            h = max(h, 380 * math.cos((x - tx) / 200 * math.pi / 2) ** 0.7)
        b0, b1 = st["beam"] - 160, st["beam"] + 160
        if b0 - 40 < x < b1 + 40:
            h = max(h, 130 * smoothstep((x - (b0 - 40)) / 40) * smoothstep(((b1 + 40) - x) / 40))
        return h

    def _course_ang(self, x, j):
        tx = dict(self.stations())["tramp"]
        if abs(x - tx) < 200:
            u = (x - (tx - 200)) / 400
            return 2 * math.pi * smootherstep(seg(u, 0.2, 0.8)) * (1 if j % 2 == 0 else -1)
        return 0.0

    def _station_pose(self, j, st, x, u_t, t):
        m = self.s.monsters[j]
        m.punch = 0.0
        m.spring = 0.0
        G = self.GF2
        if st == "bag":
            ph = (u_t / 0.6) % 1.0
            hit = max(0.0, math.sin(ph * math.pi)) ** 2
            m.punch = hit
            return x - 120, G, 34 * hit, 0, 0.06 * hit, 0.0
        if st == "tramp":
            n = int(u_t // 0.95)
            ph = (u_t % 0.95) / 0.95
            hgt = 360 if n % 2 else 250
            m.spring = 0.8 * max(0.0, 1 - min(ph, 1 - ph) / 0.12) if m.kind == "springs" else 0.0
            ang = 2 * math.pi * smootherstep(seg(ph, 0.15, 0.85)) * (1 if n % 2 else 0) * (1 if j % 2 else -1)
            return x, G - 70, 0, -4 * hgt * ph * (1 - ph), ang, 0.0
        if st == "beam":
            ph = (u_t / 3.2) % 1.0
            xx = x + 120 * math.sin(ph * 2 * math.pi)
            hop = max(0.0, math.sin(ph * 4 * math.pi)) ** 8 * 60
            return xx, G - 130, 0, -hop, 0.07 * math.sin(t * 3.1 + j), 1.0
        if st == "logs":                                 # lift a log overhead, squat, up
            ph = (u_t / 1.6) % 1.0
            return x, G, 0, 18 * (0.5 - 0.5 * math.cos(ph * 2 * math.pi)), 0, 0.0
        if st == "rope":                                 # climb up the rope and slide down
            ph = (u_t / 3.4) % 1.0
            up = math.sin(ph * math.pi) ** 1.5
            return x, G, 0, -460 * up, 0.05 * math.sin(t * 6), 0.0
        # hurdles: back and forth, hopping both
        ph = (u_t / 2.6) % 1.0
        xx = x + 160 * math.sin(ph * 2 * math.pi)
        h = 0.0
        for hx in (x - 120, x + 120):
            if abs(xx - hx) < 70:
                h = max(h, 130 * math.cos((xx - hx) / 70 * math.pi / 2))
        if m.kind == "springs":
            m.spring = 0.5 * (h < 5)
        return xx, G, 0, -h, 0, 1.0

    # ------------------------------------------------------------------ camera

    def target(self, t):
        T, d = self.T, self.d
        h = self.s.h
        fy = self.GF - h * 0.3
        ry = self.GF2 - h * 0.33
        if t < T["dump"]:
            return self.harvester(t)[0] + 160, fy, 1.0
        if t < T["drop"] + 0.6:
            # watch the doors open, then ride down with the logs to the saws
            u = smootherstep(seg(t, T["dump"] + 1.0, T["dump"] + 2.6))
            return self.pc, lerp(fy, self.saw_y - 160, u), 1.0
        if t < T["settle"]:
            u = smootherstep(seg(t, T["drop"] + 0.6, T["settle"]))
            return self.pc, lerp(self.saw_y - 160, self.vat_rim - 120, u), lerp(1.0, 1.05, u)
        if t < T["carry"]:
            return (self.vat[0] + self.vat[1]) / 2, self.vat_rim - 60, 1.05
        if t < T["line"]:
            u = smootherstep(seg(t, T["carry"], T["line"]))
            midq = (self.queue_x(0) + self.queue_x(self.n - 1)) / 2
            return lerp((self.vat[0] + self.vat[1]) / 2, midq + 300 * u, u), lerp(self.vat_rim - 60, ry, u), 1.0
        ls = self.line_state(t)
        if ls is not None:
            cyc, ph, u = ls
            focus = self._focus_station(cyc)
            if focus is None:                            # final move onto the dock: start the pan
                return self.line0 + 4 * self.D, self.pallet_y - 300, 1.5
            fx = self.line0 + focus * self.D
            j = self.station_unit(focus, cyc)
            m = self.s.monsters[j]
            hgt = m.y - m.body_center()[1]
            return fx, self.pallet_y - max(260, hgt + 40), 1.7
        if t < T["orbs"]:
            # glide right along the row of finished (still sleeping) monsters to where the first orb drops
            u = smootherstep(seg(t, T["dock_pan"] - 0.6, T["orbs"]))
            return lerp(self.line0 + 4 * self.D, self.dock_x(0), u), self.pallet_y - 300, lerp(1.5, 1.35, u)
        if t < T["walk"]:
            # follow the orbs along the dock, then pull back to see the whole row awake
            j = min(self.n - 1, int((t - T["orbs"]) / d["orb"])) if t < T["wake"] else None
            if j is not None:
                return self.dock_x(j), self.GF2 - h * 0.3 / 1.5, 1.5
            u = smootherstep(seg(t, T["wake"], T["walk"]))
            mid = (self.dock_x(0) + self.dock_x(self.n - 1)) / 2
            return mid, lerp(self.GF2 - h * 0.2, ry, u), lerp(1.5, 1.0, u)
        if t < T["train"]:
            u = smootherstep(seg(t, T["walk"], T["train"]))
            mid = (self.dock_x(0) + self.dock_x(self.n - 1)) / 2
            return lerp(mid, (self.room[0] + self.room[1]) / 2, u), self.GF2 - h * 0.42, lerp(1.0, 0.85, u)
        if t < T["door"]:
            if T["course"] <= t < T["passed"]:
                xs = [self.pose(j, t)[0] for j in range(self.n)]
                c0 = [self.course_t(j) for j in range(self.n)]
                act = [xs[j] for j in range(self.n) if c0[j][0] <= t < c0[j][1]]
                if act:
                    return float(np.clip(np.mean(act), self.room[0] + 900, self.room[1] - 700)), self.GF2 - h * 0.46, 0.88
            return (self.room[0] + self.room[1]) / 2, self.GF2 - h * 0.42, 0.85
        u = smootherstep(seg(t, T["door"], T["end"] - 1.0))
        return lerp((self.room[0] + self.room[1]) / 2, self.door_x + 250, u), self.GF2 - h * 0.4, lerp(0.85, 1.0, u)

    def _focus_station(self, cyc):
        """Cycles 1-5 follow unit 0 (Toby's Wheels) through every station; then the last unit (Digs) gets
        carved, the next-to-last gets its parts, and the camera stays with Digs to its SCAN. Every
        focused station is busy, so the camera never sits on an empty line."""
        if cyc <= 5:
            return cyc - 1
        last = self.n - 1
        if cyc == 6:
            f = 0 if self.station_unit(0, cyc) is not None else 2
        elif cyc == 7:
            f = 2
        else:
            f = cyc - 1 - last                           # wherever the last unit is
        if not 0 <= f <= 4 or self.station_unit(f, cyc) is None:
            return None
        return f

    # ------------------------------------------------------------------ update (state + sound)

    def update(self, t, dt):
        T, d = self.T, self.d
        s, P = self.s, self.s.particles
        hx, door, mov = self.harvester(t)
        for i, x in enumerate(self.trees_x):
            if self.crossed(T[f"drive{i}"]):
                self.fx(t, "motor", d["drive"] + 0.2, 0.45, hx, self.GF)
            if self.crossed(T[f"cut{i}"]):
                self.fx(t, "saw", d["cut"], 0.7, x, self.GF)
            if T[f"cut{i}"] < t <= T[f"fall{i}"]:
                P.burst(x - 20, self.GF - 60, 2, SAWDUST, 420, 0.7, 3.5, g=900, up=100, spread=1.2)
            if self.crossed(T[f"fall{i}"]):
                self.fx(t, "creak", d["fall"] * 0.9, 0.55, x, self.GF - 300)
            if self.crossed(T[f"load{i}"]):
                self.hit(t, "thud", 45, 0.85, x - 300, self.GF - 200)
                self.fx(t, "rustle", 0.9, 0.6, x - 300, self.GF - 400)
                ang = -math.radians(84)
                L = self.tree_h * 0.74
                P.leaves(x + math.sin(ang) * L, self.GF - 40 - math.cos(ang) * L, 26)
            if self.crossed(T[f"load{i}"] + d["load"] * 0.9):
                self.hit(t, "clunk", s.note(i, -1), 0.55, hx, self.GF - 200)
        if self.crossed(T["to_pit"]):
            self.fx(t, "motor", d["to_pit"], 0.55, hx, self.GF)
        if self.crossed(T["dump"]):
            self.fx(t, "servo", 0.8, 0.45, hx, self.GF)
            self.hit(t + 0.6, "clunk", 45, 0.7, hx, self.GF)
        if self.crossed(T["settle"]):
            self.fx(t, "motor", 3.0, 0.5, hx, self.GF)
        for lg in self.logs:
            if self.crossed(lg["rel"]):
                self.fx(t, "slide", 0.4, 0.35, lg["x"], self.GF)
            if self.crossed(lg["t_saw"]):
                self.fx(t, "saw", 0.4, 0.6, lg["x"], self.saw_y)
                for k, sx in enumerate(self.saws_x):
                    self.hit(t + k * 0.04, "clack", s.note(k + 2), 0.35, sx, self.saw_y)
                    P.burst(sx, self.saw_y, 8, SAWDUST, 480, 0.8, 3.2, g=700)
        for c in self.chunks:
            if self.crossed(c["t_hit"]):
                xh = c["x0"] + c["vx"] * (c["t_hit"] - c["t0"])
                if c["j"] in (0, 3):
                    self.fx(t, "splash", 0.5, 0.4, xh, self.vat_full)
                P.burst(xh, self.vat_full, 6, GREEN, 360, 0.55, 5, g=1800, glow=True, spread=0.7)
        if self.crossed(T["drop"]):
            self.fx(t, "bubble", T["line"] - T["drop"], 0.3, self.pc, self.vat_full)
        for mi in range(self.n):
            if self.crossed(T["grow"] + mi * 0.3):
                for k in range(3):
                    self.hit(t + k * 0.25, "soft_bell", s.note(mi + k * 2, -1), 0.3, self.grow_x[mi], self.vat_full)
            if self.crossed(T["grab"] + mi * 0.12):
                self.fx(t, "servo", 1.0, 0.3, self.grow_x[mi], self.rail_y)
        if self.crossed(T["carry"]):
            self.fx(t, "motor", d["carry"] * 0.8, 0.4, self.pc + 800, self.rail_y)
        if self.crossed(T["carry"] + 0.5):
            self.fx(t, "gurgle", T["line"] - T["carry"] - 0.5, 0.5, self.pc, self.vat_bottom)
        # monster states through the factory
        for j, m in enumerate(s.monsters):
            if t < T["line"]:
                m.rough, m.attach = 1.0, {p: 0.0 for p in self._parts(m)}
            self._line_unit_state(j, m, t)
        self._line_sounds(t)
        # orbs + wake
        for j, m in enumerate(s.monsters):
            o0, o1 = self.orb_times(j)
            if self.crossed(o0):
                self.fx(t, "whoosh", o1 - o0, 0.35, self.dock_x(j), self.GF2 - 500)
            if self.crossed(o1 + 0.9):
                self.say(t, m.kind, "up", self.dock_x(j), self.GF2 - 300, 0.55)
            if self.crossed(o1):
                for k, nn in enumerate((0, 2, 4)):
                    self.hit(t + k * 0.09, "chime", s.note(nn + j, 0), 0.5, self.dock_x(j), self.GF2 - 300)
                ox, oy = m.orb_pos()
                P.burst(ox, oy, 30, ORB, 380, 0.8, 4, g=0, glow=True)
            if t >= T["orbs"]:
                m.orb_in = smoothstep(seg(t, o1 - 0.05, o1 + 0.12))
                m.alive = smootherstep(seg(t, o1 + 0.1, o1 + 0.1 + d["wake"]))
        if t >= T["orbs"]:
            for j, m in enumerate(s.monsters):
                x, y, *_, walking = self.pose(j, t)
                vx = (x - m.x) / dt if dt > 0 else 0.0
                m.x, m.y, m.walk = x, y, walking
                m.gait += dt * 9 * walking
                m.wheel_rot += vx * dt / (46 * m.k)
        if self.crossed(T["step_down"]):
            for j in range(self.n):
                self.hit(t + j * 0.15 + 0.5, "thud", 43, 0.4, self.dock_x(j), self.GF2)
        if self.crossed(T["walk"]):
            for k in range(int(d["walk"] / 0.3)):
                self.hit(t + k * 0.3, "clack", s.note(k % 3, -1), 0.22, self.dock_x(2), self.GF2)
        self._training_sounds(t)
        if self.crossed(T["passed"]):
            for k, nn in enumerate((0, 2, 4)):
                self.hit(t + k * 0.12, "soft_bell", s.note(nn), 0.55, (self.room[0] + self.room[1]) / 2, self.GF2 - 900)
        for j, m in enumerate(s.monsters):
            b0 = T["badges"] + j * d["badge"]
            m.badge = settle(seg(t, b0, b0 + 0.35), 0.15)
            if self.crossed(b0):
                self.hit(t, "chime", s.note(j + 1, 0), 0.45, m.x, self.GF2 - 300)
                self.say(t + 0.15, m.kind, "cheer", m.x, self.GF2 - 300, 0.5)
                bx, by = m.body_center()
                P.burst(bx, by, 14, np.array([150, 240, 170]), 260, 0.6, 3, g=0, glow=True)
        if self.crossed(T["badges"] + self.n * d["badge"]):
            for k, nn in enumerate((0, 4, 7)):
                self.hit(t + k * 0.15, "soft_bell", s.note(nn) if nn < 7 else s.note(0, 1), 0.6,
                         (self.room[0] + self.room[1]) / 2, self.GF2 - 900)
        if self.crossed(T["door"]):
            for j, m in enumerate(s.monsters):
                self.say(t + 1.0 + j * 0.25, m.kind, "up", m.x, self.GF2 - 300, 0.4)
            self.fx(t, "motor", d["door"], 0.6, self.door_x, self.GF2 - 300)
            self.fx(t, "hiss", 0.8, 0.3, self.door_x, self.GF2 - 300)
        if self.crossed(T["exit"]):
            self.fx(t, "rustle", 2.0, 0.4, self.door_x + 400, self.GF2 - 300)
        self.stats = {"factory_monsters": [m.kind for m in s.monsters], "factory_s": round(self.dur, 1)}

    def _parts(self, m):
        from ..products.monster import PARTS
        return list(PARTS[m.kind])

    def _line_unit_state(self, j, m, t):
        T, d = self.T, self.d
        if t < T["line"]:
            return
        if t < T["orbs"]:
            m.x, m.y = self.unit_x(j, t), self.pallet_y
        cl = d["move"] + d["work"]
        for i in range(5):
            cyc = i + j + 1                                # the cycle in which unit j works at station i
            w0 = T["line"] + (cyc - 1) * cl + d["move"]
            w1 = w0 + d["work"]
            u = seg(t, w0, w1)
            if i == 0:
                m.rough = 1.0 - smootherstep(seg(u, 0.05, 0.92))
            elif i == 2:
                names = self._parts(m)
                for pi, name in enumerate(names):
                    a0 = 0.05 + 0.85 * pi / len(names)
                    a1 = a0 + 0.85 / len(names) * 0.8
                    m.attach[name] = settle(seg(u, a0, a1), 0.04)

    def _line_sounds(self, t):
        T, d = self.T, self.d
        s = self.s
        if t < T["line"] or t >= T["orbs"] + 0.1:
            return
        cl = d["move"] + d["work"]
        for cyc in range(1, self.cycles + 1):
            m0 = T["line"] + (cyc - 1) * cl
            w0 = m0 + d["move"]
            if self.crossed(m0):
                self.fx(t, "motor", d["move"], 0.45, self.line0 + 2 * self.D, self.pallet_y)
            if self.crossed(m0 + d["move"] * 0.95):
                self.hit(t, "clunk", s.note(cyc, -1), 0.4, self.line0 + 2 * self.D, self.pallet_y)
            for i in range(5):
                j = self.station_unit(i, cyc)
                if j is None:
                    continue
                x = self.line0 + i * self.D
                if i == 0 and self.crossed(w0 + 0.2):
                    self.fx(t, "saw", d["work"] * 0.75, 0.4, x, self.pallet_y - 200)
                if i == 1 and self.crossed(w0 + 0.3):
                    self.fx(t, "spray", d["work"] * 0.6, 0.35, x, self.pallet_y - 200)
                if i == 2:
                    names = self._parts(s.monsters[j])
                    for pi in range(len(names)):
                        a1 = 0.05 + 0.85 * pi / len(names) + 0.85 / len(names) * 0.8
                        a0 = 0.05 + 0.85 * pi / len(names)
                        if self.crossed(w0 + a0 * d["work"]):
                            self.fx(t, "servo", 0.8, 0.25, x, self.pallet_y - 300)
                        if self.crossed(w0 + a1 * d["work"]):
                            self.hit(t, "clunk", s.note(pi + j), 0.5, x, self.pallet_y - 200)
                if i == 3:
                    for b in range(4):
                        tb = w0 + 0.5 + b * 1.4
                        if self.crossed(tb):
                            for q in range(5):
                                self.hit(t + q * 0.07, "clack", s.note(5 + (q % 2), 0), 0.22, x, self.pallet_y - 200)
                if i == 4:
                    if self.crossed(w0 + 0.3):
                        self.fx(t, "hiss", d["work"] * 0.5, 0.15, x, self.pallet_y - 200)
                    if self.crossed(w0 + d["work"] * 0.72):
                        self.hit(t, "chime", s.note(4 + j, 0), 0.4, x, self.pallet_y - 300)

    def _training_sounds(self, t):
        T, d = self.T, self.d
        s = self.s
        if not (T["train"] <= t < T["passed"]):
            return
        if T["course"] > t:
            R, rd, sw = d["rounds"], d["round"], d["swap"]
            for r in range(R):
                r0 = T["train"] + r * (rd + sw)
                for j in range(self.n):
                    st, x = self.spot(j, r)
                    period = {"bag": 0.6, "tramp": 0.95, "beam": 1.6, "logs": 1.6, "rope": 1.7, "hurdles": 1.3}[st]
                    k = 0
                    while k * period < rd:
                        if self.crossed(r0 + k * period + (0.3 if st == "bag" else 0.001)):
                            if st == "bag":
                                self.hit(t, "thud", 40, 0.55, x, self.GF2 - 200)
                            elif st == "tramp":
                                self.hit(t, "pluck", s.note(k + j, -1), 0.45, x, self.GF2 - 70)
                                if s.monsters[j].kind == "springs":
                                    self.hit(t, "boing", s.note(k, -1), 0.5, x, self.GF2 - 70)
                            elif st == "logs":
                                self.hit(t, "thud", 45, 0.35, x, self.GF2)
                            else:
                                self.hit(t, "clack", s.note(k * 2 + j, -1), 0.25, x, self.GF2 - 130)
                        k += 1
        for j in range(self.n):
            c0, c1 = self.course_t(j)
            if self.crossed(c0):
                self.hit(t, "chime", s.note(0, 0), 0.35, self.room[0] + 200, self.GF2 - 600)
            if self.crossed(c1):
                self.say(t + 0.1, s.monsters[j].kind, "cheer", self.room[1] - 200, self.GF2 - 300, 0.5)
                for k, nn in enumerate((2, 4)):
                    self.hit(t + k * 0.1, "chime", s.note(nn + j, 0), 0.4, self.room[1] - 200, self.GF2 - 600)

    # ------------------------------------------------------------------ drawing

    def draw(self, c, t):
        s = self.s
        self.night.draw(s, c, t)
        if s.cam_x + s.w > self.door_x:
            self.low_night.draw(s, c, t, moon=False)
        self._ground(c)
        self._interior(c, t)
        self._shaft(c, t)
        self._vat(c, t, True)
        self._chunks(c, t)
        self._vat(c, t, False)
        self._line(c, t, back=True)
        self._dock(c, t)
        self._room(c, t)
        self._claws(c, t)
        self._monsters(c, t)
        self._line(c, t, back=False)
        self._trees(c, t)
        self._harvester(c, t)
        self._falling_logs(c, t)
        self._saws(c, t)
        self._cliff(c, t)

    # ----- outside -----

    def _ground(self, c):
        s = self.s
        GF, GF2, X1 = self.GF, self.GF2, self.door_x
        L, R = s.cam_x - 1200, s.cam_x + s.w + 1200
        deep = GF2 + 2500
        if L < X1:
            rect(c, L, GF, min(R, X1), deep, EARTH)
            for y in np.arange(GF + 60, deep, 90):
                c.line(L, y + 10 * math.sin(y), min(R, X1), y - 10 * math.sin(y * 0.7), EARTH_DARK, 3)
            rect(c, L, GF - 6, min(R, X1), GF + 4, GRASS)
        if R > X1:
            rect(c, max(L, X1), GF2, R, deep, EARTH)
            rect(c, max(L, X1), GF2 - 6, R, GF2 + 4, GRASS)

    def _trees(self, c, t):
        s, T = self.s, self.T
        for i, x in enumerate(self.trees_x):
            if not s.visible(x - 900, x + 300):
                continue
            sy = self.GF - 40
            rect(c, x - 25, sy, x + 25, self.GF, TRUNK)
            if t < T[f"fall{i}"]:
                cut = seg(t, T[f"cut{i}"], T[f"fall{i}"])
                tree(c, x, self.GF, self.tree_h, 100 + i)
                if cut > 0:
                    c.line(x - 25, sy, x - 25 + 50 * cut, sy, EARTH_DARK, 4)
            elif t < T[f"load{i}"]:
                u = seg(t, T[f"fall{i}"], T[f"load{i}"])
                tc = Xform(c, ang=-math.radians(84) * u * u, px=x, py=sy)
                tree(tc, x, sy, self.tree_h - 40, 100 + i)
            c.polygon([(x - 22, sy), (x + 22, sy), (x + 20, sy - 4), (x - 20, sy - 4)], SAWDUST * 0.7)
        for j, x in enumerate(np.arange(4400, self.door_x - 200, 420)):
            if s.visible(x - 250, x + 250):
                tree(c, x, self.GF, self.tree_h * (0.85 + 0.1 * (j % 3)), 300 + j)
        for j, x in enumerate(np.arange(self.door_x + 420, self.door_x + 3200, 360)):
            if s.visible(x - 250, x + 250):
                tree(c, x, self.GF2, self.tree_h * (0.9 + 0.1 * (j % 2)), 400 + j)

    def _harvester(self, c, t):
        s = self.s
        hx, door, mov = self.harvester(t)
        if not s.visible(hx - 500, hx + 500):
            return
        GF, L, x = self.GF, 560, hx
        # tracks
        tr0, tr1 = x - L / 2 + 10, x + L / 2 - 120
        rect(c, tr0 + 30, GF - 70, tr1 - 30, GF, RUBBER_DARK)
        c.circle(tr0 + 35, GF - 35, 35, RUBBER_DARK)
        c.circle(tr1 - 35, GF - 35, 35, RUBBER_DARK)
        roll = (hx * 0.05) % (2 * math.pi)
        for wx in np.linspace(tr0 + 35, tr1 - 35, 5):
            c.circle(wx, GF - 35, 22, STEEL)
            c.line(wx, GF - 35, wx + math.cos(roll) * 18, GF - 35 + math.sin(roll) * 18, STEEL * 0.6, 3)
        machine_block(c, x - L / 2, GF - 120, x + L / 2 - 90, GF - 70, MACHINE)
        for sx_ in np.arange(x - L / 2 + 10, x + L / 2 - 100, 40):
            c.line(sx_, GF - 80, sx_ + 20, GF - 110, HAZARD * 0.6, 4)
        cab0, cab1 = x + 40, x + L / 2 - 100
        machine_block(c, cab0, GF - 330, cab1, GF - 120, MACHINE)
        rect(c, cab0 + 20, GF - 310, cab1 - 16, GF - 220, np.array([40, 60, 72]))
        c.line(cab0 + 30, GF - 300, cab0 + 70, GF - 230, np.array([80, 104, 118]), 3)
        c.circle(cab0 + 70, GF - 260, 16, np.array([28, 30, 36]))
        rect(c, cab0 + 58, GF - 244, cab0 + 82, GF - 226, np.array([28, 30, 36]))
        machine_block(c, cab0 - 6, GF - 346, cab1 + 6, GF - 330, MACHINE * 0.9)
        beacon = 0.5 + 0.5 * math.sin(t * 6)
        c.circle(cab0 + 30, GF - 356, 9, HAZARD * (0.6 + 0.4 * beacon))
        c.circle(cab1 - 6, GF - 200, 10, LAMP)
        s.glow_draw(lambda g: (g.circle(cab0 + 30, GF - 356, 14, HAZARD * 0.5 * beacon),
                               g.circle(cab1 - 6, GF - 200, 18, LAMP * 0.55),
                               g.polygon([(cab1, GF - 210), (cab1 + 420, GF - 300), (cab1 + 420, GF - 40),
                                          (cab1, GF - 190)], LAMP * 0.07)))
        sx_, sy_ = x + L / 2 + 40, GF - 70
        c.line(cab1 - 20, GF - 150, sx_, sy_, MACHINE * 1.1, 26)
        c.line(cab1 - 20, GF - 150, sx_, sy_, lighten(MACHINE, 1.3), 3)
        cutting = any(self.T[f"cut{i}"] <= t < self.T[f"fall{i}"] for i in range(len(self.trees_x)))
        saw_blade(c, sx_, sy_, 62, t * (24 if cutting else 9))
        rect(c, sx_ - 70, sy_ - 78, sx_ + 10, sy_ - 56, HAZARD * 0.75)
        # hopper with belly doors
        hp0, hp1 = x - L / 2 + 10, x + 10
        n_loaded = sum(1 for i in range(len(self.trees_x)) if t >= self.T[f"load{i}"] + self.d["load"])
        for k in range(n_loaded):
            if t >= self.logs[k]["rel"]:
                continue
            ly = GF - 150 - k * 22
            self._log(c, (hp0 + hp1) / 2 + ((k * 37) % 24 - 12), ly, 0.0)
        for i, tx in enumerate(self.trees_x):
            T0, T1 = self.T[f"load{i}"], self.T[f"load{i}"] + self.d["load"]
            if T0 <= t < T1:
                u = smootherstep(seg(t, T0, T1))
                ang = -math.radians(84)
                Lt = self.tree_h * 0.35
                sx0, sy0 = tx + math.sin(ang) * Lt, GF - 40 - math.cos(ang) * Lt
                ly = GF - 150 - i * 22
                lx = (hp0 + hp1) / 2 + ((i * 37) % 24 - 12)
                self._log(c, lerp(sx0, lx, u), lerp(sy0, ly - 60 * math.sin(math.pi * u), u),
                          lerp(ang + math.pi / 2, 0.0, u))
        c.polygon([(hp0, GF - 120), (hp0 - 30, GF - 330), (hp0 - 14, GF - 330), (hp0 + 12, GF - 120)], MACHINE * 0.75)
        c.polygon([(hp1, GF - 120), (hp1 + 20, GF - 330), (hp1 + 4, GF - 330), (hp1 - 12, GF - 120)], MACHINE * 0.75)
        c.polygon([(hp0, GF - 120), (hp1, GF - 120), (hp1 + 12, GF - 178), (hp0 - 12, GF - 176)], MACHINE)
        c.line(hp0 - 12, GF - 176, hp1 + 12, GF - 178, lighten(MACHINE, 1.4), 3)
        # belly doors hinge at both ends and swing down
        a = door * math.radians(80)
        half = (hp1 - hp0) / 2
        for sgn, hxp in ((1, hp0), (-1, hp1)):
            ex = hxp + sgn * math.cos(a) * half
            ey = GF - 120 + math.sin(a) * half
            c.line(hxp, GF - 120, ex, ey, HAZARD * 0.8, 8)

    def _log(self, c, x, y, ang, L=220, r=19):
        ca, sa = math.cos(ang), math.sin(ang)
        hx, hy = ca * L / 2, sa * L / 2
        nx, ny = -sa * r, ca * r
        c.polygon([(x - hx + nx, y - hy + ny), (x + hx + nx, y + hy + ny), (x + hx - nx, y + hy - ny),
                   (x - hx - nx, y - hy - ny)], TRUNK)
        c.line(x - hx * 0.9 + nx * 0.3, y - hy * 0.9 + ny * 0.3, x + hx * 0.9 + nx * 0.3, y + hy * 0.9 + ny * 0.3, BARK, 3)
        c.circle(x + hx, y + hy, r, SAWDUST * 0.85)
        c.circle(x + hx, y + hy, r * 0.55, SAWDUST * 0.7)

    def _falling_logs(self, c, t):
        for lg in self.logs:
            if not (lg["rel"] <= t < lg["t_saw"]):
                continue
            dt = t - lg["rel"]
            self._log(c, lg["x"], self.GF - 130 + 1300 * dt * dt, lg["tilt"] * min(1.0, dt * 2), L=240)

    # ----- factory interior -----

    def _interior(self, c, t):
        s = self.s
        X0, X1 = self.interior
        top, bot = self.ceil, self.GF2
        L, R = max(X0, s.cam_x - 1200), min(X1, s.cam_x + s.w + 1200)
        if R <= L:
            return
        rect(c, L, top, R, bot, INTERIOR)
        off = s.cam_x * 0.35
        for gx in np.arange(X0 + 120 - (off % 300), X1, 300):
            if L - 40 < gx < R + 40:
                rect(c, gx, top, gx + 30, bot, FAR)
        for gy in (top + 120, top + 520, bot - 420):
            c.line(L, gy, R, gy, FAR, 9)
        for gx in np.arange(X0 + 270 - (off % 600), X1, 600):
            if L - 300 < gx < R:
                c.line(gx, top + 120, gx + 300, top + 520, FAR, 6)
                c.line(gx + 300, top + 120, gx, top + 520, FAR, 6)
        rect(c, L, top, R, top + 36, MID)
        for py, th in ((top + 60, 22), (top + 96, 12)):
            rect(c, L, py, R, py + th, MID)
        for lx in np.arange(X0 + 380, X1 - 100, 640):
            if L - 200 < lx < R + 200:
                c.line(lx, top + 36, lx, top + 220, CABLE, 3)
                c.polygon([(lx - 40, top + 250), (lx + 40, top + 250), (lx + 22, top + 220), (lx - 22, top + 220)], STEEL)
                s.glow_draw(lambda g, lx=lx: (g.circle(lx, top + 254, 18, LAMP * 0.6),
                                              g.polygon([(lx - 40, top + 254), (lx + 40, top + 254), (lx + 190, bot),
                                                         (lx - 190, bot)], LAMP * 0.03)))
        rect(c, L, bot, R, bot + 40, FLOOR)
        c.line(L, bot, R, bot, lighten(FLOOR, 1.9), 2)
        c.line(L, top, R, top, EARTH_DARK, 4)

    def _shaft(self, c, t):
        s = self.s
        p0, p1 = self.pit
        s0, s1 = self.shaft
        GF, sy = self.GF, self.saw_y
        if not s.visible(p0 - 100, p1 + 100, GF - 200, sy + 400):
            return
        c.polygon([(p0, GF), (p1, GF), (s1, GF + 200), (s1, sy + 100), (s0, sy + 100), (s0, GF + 200)], INTERIOR * 0.85)
        for a, b in (((p0, GF), (s0, GF + 200)), ((p1, GF), (s1, GF + 200))):
            c.line(*a, *b, STEEL, 14)
        for x in (s0, s1):
            c.line(x, GF + 200, x, sy + 100, STEEL, 14)
            c.line(x, GF + 200, x, sy + 100, lighten(STEEL, 1.3), 2)
        # grate rails the truck drives onto
        for dx in (-6, 6):
            c.line(p0 - 40, GF - 4 + dx * 0, p1 + 40, GF - 4, STEEL * 0.9, 10)
        for x in np.arange(p0, p1 + 1, 60):
            c.line(x, GF - 8, x, GF + 14, STEEL * 0.8, 6)
        for x in (p0, p1):
            rect(c, x - 30, GF + 4, x + 30, GF + 16, HAZARD * 0.8)
        machine_block(c, s0 - 60, sy - 60, s0 + 4, sy + 60, IRON)
        machine_block(c, s1 - 4, sy - 60, s1 + 60, sy + 60, IRON)

    def _saws(self, c, t):
        s = self.s
        if not s.visible(self.shaft[0] - 100, self.shaft[1] + 100, self.saw_y - 200, self.saw_y + 200):
            return
        busy = any(lg["t_saw"] - 0.3 < t < lg["t_saw"] + 0.4 for lg in self.logs)
        spin = t * (22 if busy else 10)
        for i, x in enumerate(self.saws_x):
            saw_blade(c, x, self.saw_y + (12 if i % 2 else -12), 30, spin * (1 if i % 2 else -1) + i)
        c.line(self.shaft[0], self.saw_y, self.shaft[1], self.saw_y, STEEL * 0.7, 5)

    def _vat(self, c, t, back):
        s = self.s
        v0, v1 = self.vat
        rim, bot = self.vat_rim, self.vat_bottom
        if not s.visible(v0 - 80, v1 + 80, rim - 600, self.GF2 + 50):
            return
        lvl = self.liquid_y(t)
        if back:
            rect(c, v0, rim, v1, bot, IRON * 0.7)
            if lvl < bot - 2:
                wave = [(x, lvl + 4 * math.sin(x * 0.03 + t * 2)) for x in np.linspace(v0 + 14, v1 - 14, 50)]
                body = wave + [(v1 - 14, bot - 10), (v0 + 14, bot - 10)]
                c.polygon(body, GREEN_DEEP)
                c.polyline(wave, GREEN * 0.8, 4)
                s.glow_draw(lambda g: (g.polygon(body, GREEN * 0.16), g.polyline(wave, GREEN * 0.55, 6)))
                for b in range(14):
                    ph = (t * 0.6 + b * 0.37) % 1.0
                    bx = lerp(v0 + 40, v1 - 40, (b * 0.618) % 1.0)
                    by = lerp(bot - 20, lvl, ph)
                    if by > lvl + 6:
                        c.circle(bx, by, 4 + 3 * ph, GREEN * 0.7)
            if self.T["carry"] + 0.5 < t < self.T["line"]:
                cx = (v0 + v1) / 2
                for k in range(3):
                    a = t * 5 + k * 2.1
                    c.arc(cx, bot - 30, 30 + 14 * k, math.degrees(a), math.degrees(a) + 120, GREEN * 0.9, 3)
            return
        c.polyline([(v0, rim - 10), (v0, bot), (v1, bot), (v1, rim - 10)], STEEL, 16)
        for lx in (v0 + 40, (v0 + v1) / 2 - 200, (v0 + v1) / 2 + 200, v1 - 40):
            rect(c, lx - 14, bot, lx + 14, self.GF2, STEEL * 0.8)
        cx = (v0 + v1) / 2
        rect(c, cx - 24, bot, cx + 24, self.GF2 + 40, IRON)
        rect(c, cx - 40, bot - 8, cx + 40, bot + 6, HAZARD * (0.9 if self.T["carry"] + 0.5 < t else 0.5))

    def _chunks(self, c, t):
        if t < self.logs[0]["t_saw"]:
            return
        for ch in self.chunks:
            if t < ch["t0"]:
                continue
            x, y, rot, st = self.chunk_pos(ch, t)
            if st == "gone":
                continue
            mi = ch["grow"]
            if mi is not None and t >= self.T["grow"]:
                if t < self.T["line"]:
                    self._grower(c, mi, ch, x, y, t)
                continue
            w, h = ch["w"], ch["h"]
            pts = [(x + math.cos(rot) * dx - math.sin(rot) * dy, y + math.sin(rot) * dx + math.cos(rot) * dy)
                   for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
            c.polygon(pts, TRUNK)
            c.polyline(pts, BARK, 2, closed=True)
            c.circle(x, y, min(w, h) * 0.25, SAWDUST * 0.7)

    def claw(self, mi, t):
        """(x, grip y, carrying, open 0..1) of transfer claw mi."""
        T, d = self.T, self.d
        m = self.s.monsters[mi]
        rx, ry = m.body_size()
        gx, qx = self.grow_x[mi], self.queue_x(mi)
        y_float = self.vat_full - 6 - ry * 0.35
        carry_y = self.vat_rim - ry - 40
        bc_h = m.y - m.body_center()[1]                 # body center height above the feet
        line_y = self.pallet_y - bc_h
        park = self.rail_y + 40
        g0, c0 = T["grab"] + mi * 0.12, T["carry"] + mi * 0.12
        if t < g0:
            return gx, park, False, 1.0
        if t < c0:
            u = seg(t, g0, c0)
            if u < 0.4:
                return gx, lerp(park, y_float - ry, smootherstep(u / 0.4)), False, 1.0
            if u < 0.55:
                return gx, y_float - ry, True, 1 - smoothstep((u - 0.4) / 0.15)
            return gx, lerp(y_float - ry, carry_y - ry, smootherstep((u - 0.55) / 0.45)), True, 0.0
        L0 = T["line"]
        if t < L0 - 0.8:
            u = smootherstep(seg(t, c0, L0 - 1.2))
            x = lerp(gx, qx, u)
            y = carry_y - ry if u < 0.8 else lerp(carry_y - ry, line_y - ry, smootherstep((u - 0.8) / 0.2))
            return x, y, True, 0.0
        u = seg(t, L0 - 0.8, L0)
        return qx, lerp(line_y - ry, park, smootherstep(seg(u, 0.3, 1.0))), u < 0.3, smoothstep(u / 0.3)

    def _grower(self, c, mi, ch, x, y, t):
        m = self.s.monsters[mi]
        g = self.grow_amount(mi, t)
        rx, ry = m.body_size()
        cx_, cy_, carrying, _ = self.claw(mi, t)
        held = carrying and t >= self.T["grab"]
        if held:
            bx, by = cx_, cy_ + ry
        else:
            bx, by = x, lerp(y, self.vat_full - 6 - ry * 0.35, g)
        w, h = lerp(ch["w"] / 2, rx, g), lerp(ch["h"] / 2, ry, g)
        body = ellipse(bx, by, w, h, 44)
        # rough lump while growing (the carving station smooths it later)
        p = np.asarray(body)
        ang = np.linspace(0, 2 * np.pi, len(p), endpoint=False)
        bump = 0.10 * np.sin(ang * 5 + mi * 1.7) + 0.07 * np.sin(ang * 9 + mi * 3.9) + 0.05 * np.sin(ang * 14 + mi)
        p = np.array([bx, by]) + (p - np.array([bx, by])) * (1 + bump * g)[:, None]
        blob(c, p, WOOD_BODY)
        if g > 0.3:
            grain(c, bx, by + h * 0.5, w * 0.6, h * 0.25, WOOD_BODY)
        if not held:
            pulse = 0.6 + 0.4 * math.sin(t * 5 + mi)
            self.s.glow_draw(lambda gg: gg.polyline(p, GREEN * 0.35 * pulse, 6, closed=True))

    def _claws(self, c, t):
        s, T = self.s, self.T
        if t > T["line"] + 0.5:
            return
        x0, x1 = self.grow_x[0] - 140, self.queue_x(0) + 160
        if not s.visible(x0, x1, self.rail_y - 50, self.GF2):
            return
        ry_ = self.rail_y
        rect(c, x0, ry_ - 16, x1, ry_ + 6, STEEL)
        c.line(x0, ry_ - 16, x1, ry_ - 16, lighten(STEEL, 1.4), 2)
        for hx in np.arange(x0 + 60, x1, 500):
            c.line(hx, self.ceil + 36, hx, ry_ - 16, STEEL * 0.8, 10)
        for mi in range(self.n):
            x, gy, carrying, opn = self.claw(mi, t)
            rect(c, x - 30, ry_ - 8, x + 30, ry_ + 28, IRON)
            c.line(x, ry_ + 28, x, gy - 26, CABLE, 3)
            rect(c, x - 20, gy - 32, x + 20, gy - 10, HAZARD * 0.75)
            rx = s.monsters[mi].body_size()[0] if carrying else 46
            spread = lerp(rx * 0.78, rx * 1.15, opn)
            for sg in (-1, 1):
                p1, p2, p3 = (x + sg * 16, gy - 20), (x + sg * spread, gy + 26), (x + sg * (spread - 14), gy + 60)
                c.line(*p1, *p2, STEEL, 8)
                c.line(*p2, *p3, STEEL, 7)

    # ----- assembly line -----

    def _line(self, c, t, back):
        s, T, d = self.s, self.T, self.d
        x0 = self.queue_x(self.n - 1) - 200
        x1 = self.dock_x(0) + 250
        if not s.visible(x0, x1):
            return
        G, py = self.GF2, self.pallet_y
        if back:
            # conveyor bed with rollers
            rect(c, x0, py + 4, x1, G, IRON)
            c.line(x0, py + 4, x1, py + 4, lighten(IRON, 1.5), 2)
            roll = 0.0
            if T["line"] <= t < T["orbs"]:
                roll = (self.unit_p(0, t) * self.D) * 0.05
            for rx_ in np.arange(x0 + 20, x1, 48):
                c.circle(rx_, py + 16, 9, STEEL)
                c.line(rx_, py + 16, rx_ + 8 * math.cos(roll), py + 16 + 8 * math.sin(roll), STEEL * 0.6, 2)
            # station frames, labels, status lamps
            ls = self.line_state(t)
            for i, name in enumerate(STATIONS):
                sx = self.line0 + i * self.D
                rect(c, sx - 170, self.ceil + 36, sx - 150, py, STEEL * 0.55)
                rect(c, sx + 150, self.ceil + 36, sx + 170, py, STEEL * 0.55)
                machine_block(c, sx - 110, G - 600, sx + 110, G - 540, IRON)
                c.text(name, sx - 10, G - 570, 34, SIGN_WARM * 0.8)
                busy = ls is not None and ls[1] == "work" and self.station_unit(i, ls[0]) is not None
                done = busy and i == 4 and ls[2] > 0.72
                col = SCAN_GREEN if done else (HAZARD if busy else STEEL * 0.6)
                c.circle(sx + 90, G - 570, 9, col)
                if busy:
                    s.glow_draw(lambda g, sx=sx, col=col: g.circle(sx + 90, G - 570, 16, col * 0.6))
            return
        # station tools in front of the units
        ls = self.line_state(t)
        if ls is None:
            return
        cyc, ph, u = ls
        for i in range(5):
            j = self.station_unit(i, cyc)
            sx = self.line0 + i * self.D
            if j is None or ph != "work":
                self._tool_idle(c, i, sx)
                continue
            m = s.monsters[j]
            getattr(self, "_tool_" + STATIONS[i].lower())(c, m, sx, u, t)

    def _tool_idle(self, c, i, sx):
        top = self.ceil + 36
        y = self.GF2 - 640
        c.line(sx, top, sx, y, STEEL * 0.7, 10)
        rect(c, sx - 24, y, sx + 24, y + 30, IRON)

    def _tool_carve(self, c, m, sx, u, t):
        bx, by = m.body_center()
        rx, ry = m.body_size()
        ang = -math.pi / 2 + u * 2 * math.pi * 1.6
        hx, hy = bx + math.cos(ang) * (rx + 18), by + math.sin(ang) * (ry + 18)
        top = self.ceil + 36
        c.line(sx, top, sx, self.GF2 - 640, STEEL * 0.7, 10)
        c.line(sx, self.GF2 - 640, hx, hy, STEEL, 9)
        c.line(sx, self.GF2 - 640, hx, hy, lighten(STEEL, 1.3), 2)
        saw_blade(c, hx, hy, 22, t * 30)
        if self.s.particles.rng.uniform() < 0.9 and u < 0.95:
            self.s.particles.burst(hx, hy, 3, SAWDUST, 380, 0.7, 3.5, g=900, spread=1.6, direction=ang)

    def _tool_sand(self, c, m, sx, u, t):
        bx, by = m.body_center()
        rx, ry = m.body_size()
        side = -1 if u < 0.5 else 1
        vib = 4 * math.sin(t * 60)
        py_ = by + ry * 0.5 * math.sin(u * 2 * math.pi * 3)
        px = bx + side * (rx + 14) + vib
        top = self.ceil + 36
        c.line(sx + side * 120, top, sx + side * 120, py_ - 120, STEEL * 0.7, 10)
        c.line(sx + side * 120, py_ - 120, px + side * 20, py_, STEEL, 8)
        rect(c, px - 10 + side * 6, py_ - 34, px + 10 + side * 6, py_ + 34, HAZARD * 0.8)
        rect(c, px - 4 - side * 2, py_ - 30, px + 4 - side * 2, py_ + 30, SAWDUST * 0.6)
        if self.s.particles.rng.uniform() < 0.5:
            self.s.particles.burst(px, py_, 2, SAWDUST * 1.1, 160, 1.0, 5, g=-60, spread=math.pi)

    def _tool_parts(self, c, m, sx, u, t):
        top = self.ceil + 36
        for name in self._parts(m):
            a = m.attach.get(name, 0.0)
            if a <= 0.0 or a >= 0.999:
                continue
            ax, ay = m.part_anchor(name)
            ox, oy = m.part_offset(name)
            gx, gy = ax + ox, ay + oy
            c.line(gx, top, gx, gy - 30, STEEL * 0.85, 12)
            rect(c, gx - 26, top - 4, gx + 26, top + 16, IRON)
            rect(c, gx - 16, gy - 34, gx + 16, gy - 18, HAZARD * 0.75)
            for sd in (-1, 1):
                c.line(gx + sd * 12, gy - 20, gx + sd * 20, gy - 2, STEEL, 6)

    def _tool_bolt(self, c, m, sx, u, t):
        names = self._parts(m)
        k = min(len(names) - 1, int(u * len(names)))
        top = self.ceil + 36
        for side, idx in ((-1, k), (1, (k + 1) % len(names))):
            ax, ay = m.part_anchor(names[idx])
            tx, ty = ax + side * 40, ay
            bx = sx + side * 150
            c.line(bx, top, bx, ty - 80, STEEL * 0.7, 10)
            c.line(bx, ty - 80, tx, ty, STEEL, 8)
            rect(c, tx - 9, ty - 9, tx + 9, ty + 9, IRON)
            spin = (t * 40) % (2 * math.pi)
            c.line(tx, ty, tx + 9 * math.cos(spin), ty + 9 * math.sin(spin), GOLD, 3)
            ph = (u * len(names) * 3) % 1.0
            if ph < 0.15:
                self.s.glow_draw(lambda g, tx=tx, ty=ty: g.circle(tx, ty, 14, GOLD * 0.7))

    def _tool_scan(self, c, m, sx, u, t):
        bx, by = m.body_center()
        rx, ry = m.body_size()
        top_y = m.y - (self.pallet_y - by) * 2.2 - 60
        if u < 0.7:
            y = lerp(m.y, top_y, u / 0.7)
            w = rx + 140
            c.line(bx - w, y, bx + w, y, SCAN_GREEN * 0.9, 3)
            self.s.glow_draw(lambda g: (g.line(bx - w, y, bx + w, y, SCAN_GREEN * 0.8, 8),
                                        g.polygon([(bx - w, y), (bx + w, y), (bx + w * 0.3, y + 120), (bx - w * 0.3, y + 120)],
                                                  SCAN_GREEN * 0.05)))
        rect(c, sx - 60, self.ceil + 36, sx + 60, self.ceil + 70, IRON)

    # ----- dock, orbs -----

    def _dock(self, c, t):
        s, T = self.s, self.T
        if not (T["orbs"] - 2 <= t <= T["walk"] + 1):
            return
        top = self.ceil + 36
        for j, m in enumerate(s.monsters):
            dx = self.dock_x(j)
            if not s.visible(dx - 200, dx + 200):
                continue
            ox, oy = m.orb_pos()
            tend = oy - 260
            c.line(dx - 16, top, dx - 16, tend, STEEL * 0.7, 4)
            c.line(dx + 16, top, dx + 16, tend, STEEL * 0.7, 4)
            rect(c, dx - 22, tend - 8, dx + 22, tend + 4, IRON)
            o0, o1 = self.orb_times(j)
            if t < o1:
                u = seg(t, o0, o1)
                yy = lerp(top + 40, tend, smoothstep(min(1.0, u * 1.6))) if u < 0.62 else lerp(tend, oy, ((u - 0.62) / 0.38) ** 2)
                r = 16 * m.k / 0.55
                c.circle(dx, yy, r, ORB)
                c.circle(dx - r * 0.3, yy - r * 0.3, r * 0.3, lighten(ORB, 1.6))
                s.glow_draw(lambda g, yy=yy, dx=dx, r=r: g.circle(dx, yy, r * 1.6, ORB * 0.8))
            else:
                f = max(0.0, 1 - (t - o1) / 0.8)
                if f > 0:
                    s.glow_draw(lambda g, ox=ox, oy=oy, f=f: g.circle(ox, oy, 60 + 120 * (1 - f), ORB * 0.5 * f))

    def _monsters(self, c, t):
        s, T = self.s, self.T
        if t < T["line"] - 0.05:
            return
        for j, m in enumerate(s.monsters):
            if not s.visible(m.x - 400, m.x + 400):
                continue
            if t < T["step_down"]:
                # pallet + support post under the body
                bx, by = m.body_center()
                rx, ry = m.body_size()
                rect(c, m.x - 120, self.pallet_y, m.x + 120, self.pallet_y + 14, HAZARD * 0.55)
                if t < T["walk"]:
                    c.line(m.x, self.pallet_y, m.x, by + ry * 0.6, STEEL * 0.9, 12)
                m.draw(c, t, s.glow)
                m.draw_name(c, self.name_amount(j, t), 30)
                continue
            x, y, dx, dy, ang, _ = self.pose(j, t)
            bc = m.body_center()
            mc = Xform(c, dx, dy, ang, 1.0, bc[0], bc[1]) if (dx or dy or ang) else c
            m.draw_name(Xform(c, dx, dy) if (dx or dy) else c, self.name_amount(j, t), 30)
            st = self._current_station(j, t)
            if st == "logs":
                lift = 0.5 - 0.5 * math.cos(((t - T["train"]) % (self.d["round"] + self.d["swap"])) / 1.6 * 2 * math.pi)
                top_y = m.y - (m.y - bc[1]) * 2.1 - 40 + dy * 0.5 - 60 * lift
                self._log(c, m.x, top_y, 0.0, L=260, r=20)
            if st == "rope":
                c.line(m.x, self.ceil + 36, m.x, self.GF2, np.array([150, 120, 80]), 6)
            m.draw(mc, t, s.glow)

    def name_t(self, j):
        """When monster j's nameplate appears: as its SCAN finishes (the moment it is 'made')."""
        cl = self.d["move"] + self.d["work"]
        w0 = self.T["line"] + (4 + j) * cl + self.d["move"]
        return w0 + self.d["work"] * 0.72

    def name_amount(self, j, t):
        return settle(seg(t, self.name_t(j), self.name_t(j) + 0.45), 0.12)

    def _current_station(self, j, t):
        T, d = self.T, self.d
        if not (T["train"] <= t < T["course"]):
            return None
        tr = t - T["train"]
        r = int(min(d["rounds"] - 1, tr // (d["round"] + d["swap"])))
        if tr - r * (d["round"] + d["swap"]) > d["round"]:
            return None
        return self.spot(j, r)[0]

    # ----- training room -----

    def _room(self, c, t):
        s, T = self.s, self.T
        X0, X1 = self.room
        G = self.GF2
        if not s.visible(X0 - 200, X1 + 200):
            return
        rect(c, X0 - 30, self.ceil, X0 + 30, G - 560, STEEL * 0.8)
        rect(c, X0 + 40, G - 6, X1 - 40, G + 6, np.array([40, 52, 70]))
        st = dict(self.stations())
        # sign
        sx, sy = (X0 + X1) / 2, G - 980
        rect(c, sx - 380, sy - 70, sx + 380, sy + 70, IRON * 0.8)
        c.polyline([(sx - 380, sy - 70), (sx + 380, sy - 70), (sx + 380, sy + 70), (sx - 380, sy + 70)], STEEL, 4, closed=True)
        for k in (-260, 260):
            c.line(sx + k, self.ceil + 36, sx + k, sy - 70, CABLE, 3)
        txt, col = "TRAINING", SIGN_WARM
        if t >= T["badges"]:
            txt, col = "FOREST KEEPERS", SIGN_GREEN
        elif t >= T["passed"] + 0.5:
            txt, col = "THEY PASSED", SIGN_GREEN
        flick = (T["passed"] <= t < T["passed"] + 0.5 or T["badges"] - 0.4 <= t < T["badges"]) and int(t * 20) % 2 == 0
        lit = 1.0 if t >= T["walk"] else 0.22
        col = col * (0.25 if flick else lit)
        c.text(txt, sx, sy, 84 if len(txt) < 12 else 70, col)
        if lit > 0.5:
            s.glow_draw(lambda g: g.polygon([(sx - 360, sy - 50), (sx + 360, sy - 50), (sx + 360, sy + 50), (sx - 360, sy + 50)], col * 0.10))
        # lap board during the course
        if T["course"] - 1 <= t < T["badges"]:
            bx_, by_ = X1 - 420, G - 700
            rect(c, bx_ - 220, by_ - 60, bx_ + 220, by_ + 60, np.array([20, 22, 26]))
            c.polyline([(bx_ - 220, by_ - 60), (bx_ + 220, by_ - 60), (bx_ + 220, by_ + 60), (bx_ - 220, by_ + 60)],
                       STEEL, 3, closed=True)
            run = [j for j in range(self.n) if self.course_t(j)[0] <= t]
            if run:
                j = run[-1]
                c0, c1 = self.course_t(j)
                el = min(t, c1) - c0
                done = sum(1 for k in range(self.n) if self.course_t(k)[1] <= t)
                c.text(f"RUN {done}/{self.n}   {el:4.1f}s", bx_, by_, 54, SCAN_GREEN * 0.9)
        # rope
        c.line(st["rope"], self.ceil + 36, st["rope"], G - 40, np.array([150, 120, 80]), 6)
        # bag
        bx = st["bag"]
        swing = max([m.punch for m in s.monsters] + [0.0]) if T["train"] <= t < T["course"] else 0.0
        top = G - 480
        c.line(bx, self.ceil + 36, bx, top, CABLE, 3)
        bc = Xform(c, ang=-0.25 * swing, px=bx, py=top)
        bc.line(bx, top, bx, top + 50, CABLE, 3)
        bc.polygon(ellipse(bx, top + 170, 40, 120, 30), np.array([110, 40, 34]))
        bc.polyline(ellipse(bx, top + 170, 40, 120, 30), np.array([70, 26, 22]), 3, closed=True)
        # trampoline
        tx = st["tramp"]
        c.line(tx - 150, G, tx - 130, G - 70, STEEL, 8)
        c.line(tx + 150, G, tx + 130, G - 70, STEEL, 8)
        c.polyline([(tx - 140, G - 70), (tx, G - 66), (tx + 140, G - 70)], np.array([30, 34, 46]), 10)
        # beam
        b0, b1 = st["beam"] - 160, st["beam"] + 160
        rect(c, b0, G - 130, b1, G - 110, np.array([150, 120, 84]))
        for lx in (b0 + 30, b1 - 30):
            c.line(lx, G - 110, lx - 20, G, STEEL, 7)
            c.line(lx, G - 110, lx + 20, G, STEEL, 7)
        # log rack
        lx = st["logs"]
        for k in range(3):
            self._log(c, lx + 150, G - 22 - k * 34, 0.0, L=150, r=17)
        # hurdles
        for hx in (st["hurdles"] - 120, st["hurdles"] + 120):
            c.line(hx - 40, G, hx - 40, G - 90, STEEL, 6)
            c.line(hx + 40, G, hx + 40, G - 90, STEEL, 6)
            rect(c, hx - 46, G - 98, hx + 46, G - 84, HAZARD * 0.8)
        # course hurdle by the rope + finish line
        hx = st["rope"] + 160
        c.line(hx - 40, G, hx - 40, G - 90, STEEL, 6)
        c.line(hx + 40, G, hx + 40, G - 90, STEEL, 6)
        rect(c, hx - 46, G - 98, hx + 46, G - 84, HAZARD * 0.8)
        fx = X1 - 120
        for k in range(8):
            rect(c, fx - 8, G - 8 - k * 30, fx + 8, G - k * 30 - 22, SIGN_WARM if k % 2 else np.array([30, 30, 34]))

    def _cliff(self, c, t):
        s = self.s
        X1, GF, GF2 = self.door_x, self.GF, self.GF2
        if not s.visible(X1 - 200, X1 + 200):
            return
        dh = 620
        c.polygon([(X1 - 40, GF), (X1 + 60, GF), (X1 + 60, GF2 - dh), (X1 - 40, GF2 - dh)], EARTH)
        rect(c, X1 - 40, GF - 6, X1 + 60, GF + 4, GRASS)
        fx0, fx1 = X1 - 40, X1 + 60
        machine_block(c, fx0, GF2 - dh - 40, fx1, GF2 - dh, STEEL)
        u = smootherstep(seg(t, self.T["door"], self.T["door"] + self.d["door"]))
        bottom = lerp(GF2, GF2 - dh + 30, u)
        if bottom > GF2 - dh + 32:
            rect(c, fx0 + 10, GF2 - dh, fx1 - 10, bottom, IRON)
            for y in np.arange(GF2 - dh + 30, bottom, 40):
                c.line(fx0 + 10, y, fx1 - 10, y, IRON * 0.7, 2)
            rect(c, fx0 + 10, bottom - 14, fx1 - 10, bottom, HAZARD * 0.7)
        lamp = SIGN_GREEN if u > 0 else LAMP
        c.circle(X1 + 10, GF2 - dh - 20, 9, lamp)
        s.glow_draw(lambda g: g.circle(X1 + 10, GF2 - dh - 20, 14, lamp * 0.6))
