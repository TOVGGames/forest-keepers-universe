"""Forest Keepers episode 3, act 2: the night shift (docs/engines/foundry_keepers_halloween.md).

The factory hall, left to right in the order the parts flow:
  FORGE   Digs shovels coal into the furnace (it glows hotter with every shovel); the crucible comes up
          out of the furnace, Hans tips it with his tentacles and pours six moulds; the castings cool
          from orange to black iron and Hans lifts them into a tote: little crescents and ovals.
  PRESS   Springs bounces on the ram of a foot press (real-gravity hops); every landing stamps one
          crescent into a scalloped shape; Hans feeds the blanks with a tentacle.
  LATHE   Wheels clamps wood blocks in the lathe, turns them into round balls and puts them on the belt.
  BELT    Hans sands four balls at a time, one per tentacle; the belt carries them through the paint
          booth (they come out orange) and drops them into Wheels' wagon.
  CUT     Twigs bites big circles out of a white cloth sheet; they flutter down onto a stack.
  GLASS   Glo lights glass bulbs on a wire one by one, and four frosted globes.
  TABLE   the reveal: Digs hollows the first orange ball, Wheels pushes a stem in, Twigs carves the
          ribs and a face, Glo drops a lit candle in: a jack-o'-lantern. The board lights up HAPPY
          HALLOWEEN. Then the other seven, the bats (Hans), the ghosts (cloth over the glowing globes,
          eyes bitten by Twigs) and the light string.
Nothing appears on its own: every part is carried, rolled or dropped to where it shows up next.
"""
import math

import numpy as np

from ..products import decor as D
from ..products.monster import Xform, ellipse
from ..style import CABLE, FAR, FLOOR, IRON, MID, STEEL, lighten, molten
from ..tree_monsters import HAZARD, INTERIOR, LAMP, SAWDUST, SIGN_WARM, TRUNK, BARK, machine_block
from .common import GRAVITY, PLANK, lerp, rect, seg, settle, smoothstep, smootherstep
from .halloween import TUNE_HALLOWEEN, KeeperAct, hops, path

BRICK = np.array([96, 54, 42], np.float64)
BRICK_DARK = np.array([66, 38, 32], np.float64)
COAL = np.array([34, 34, 38], np.float64)
FIRE = np.array([255, 140, 40], np.float64)
SIGN_ORANGE = np.array([255, 160, 60], np.float64)
CLOTH = D.CLOTH
GLOBE = np.array([200, 220, 255], np.float64)
BIN = np.array([70, 76, 70], np.float64)


_GLYPHS = {}


def _glyph_widths(text, size):
    """Advance width of each character (scene units) in the sign font, so letters sit where the font puts them."""
    if text not in _GLYPHS:
        import os
        from PIL import ImageFont
        f = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "..", "..", "..", "engine", "assets", "fonts",
                                            "Inter-Bold.otf"), 200)
        full = [f.getlength(text[:i + 1]) for i in range(len(text))]
        _GLYPHS[text] = [(b - a) / 200 for a, b in zip([0.0] + full[:-1], full)]
    return [w * size for w in _GLYPHS[text]]


def claw_point(m, t, side=1):
    """Where Wheels' claw (side +1 right, -1 left) is holding something right now (matches monster.py)."""
    k, a = m.k, m.alive
    by = m.y - 210 * k + a * 3 * math.sin(t * 2.2) * k
    wave = a * 0.25 * math.sin(t * 1.6 + side)
    sh = (m.x + side * 100 * k, by + 10 * k)
    el = (sh[0] + side * 70 * k, sh[1] + 30 * k - wave * 40 * k)
    hd = (el[0] + side * 30 * k, el[1] - 60 * k - wave * 30 * k)
    return hd[0] + side * 22 * k, hd[1] - 18 * k


class WorkshopAct(KeeperAct):
    name = "workshop"
    indoor = True

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        G = self.G
        self.ceil = G - 1200
        self.door_x = -240.0
        # forge
        self.coal_x, self.furnace_x = 30.0, 340.0
        self.mouth_y = G - 120
        self.moulds = [1010.0 + 130 * i for i in range(6)]
        self.bench_y = G - 230
        self.trolley_y = G - 860
        # press
        self.press_x, self.anvil_y, self.ram_rest = 2380.0, G - 250, G - 540
        self.tote_park = 2190.0
        self.bin_x = 2600.0
        # lathe (chuck on the right, Wheels feeds it from the left) + ramp + belt
        self.pallet_x, self.lathe_x, self.spindle_y = 2880.0, 3150.0, G - 205
        self.slot0, self.pitch, self.belt_y = 3420.0, 95.0, G - 140
        self.belt_end = 5000.0
        self.sand_slots = [5, 6, 7, 8]
        self.hans_sand_x = self.slot0 + 6.5 * self.pitch           # on a step behind the belt
        self.booth = (4380.0, 4690.0)
        self.wagon_x = 5110.0
        self.big_r = 44.0
        # cloth + glass
        self.sheet_x, self.sheet_top = 5660.0, G - 560
        self.cut_c = (self.sheet_x, G - 250)                     # centre of each circle Twigs bites out
        self.stack_x = 5870.0
        self.bulb_hooks = [(6090.0, G - 470), (6440.0, G - 470)]
        self.globe_x = [6130.0 + 100 * i for i in range(4)]
        self.globe_y = G - 180
        # assembly
        self.tableA = (6540.0, 7800.0)
        self.table_y = G - 140
        self.pumps = [6650.0 + 150 * i for i in range(8)]
        self.railB = (7980.0, 9140.0, G - 330)
        self.hang = [8050.0 + 115 * i for i in range(10)]
        self.hang_kind = ["bat", "ghost", "bat", "ghost", "bat", "bat", "ghost", "bat", "ghost", "bat"]
        self.sign = (7175.0, G - 860, 1300.0, 180.0)
        self.coil_x = 7880.0                                    # where Glo leaves the light string
        self.disc_x = 8570.0                                    # Twigs' cloth stack, under the middle of the rail
        self.bin_drop = 7900.0                                  # Springs sets the bat parts down here
        self.d = d = dict(enter=6.0, shovel=3.0, n_shovel=4, lift=3.0, to_mould=2.5, pour=2.6, pour_move=0.7,
                          cool=5.5, unload=1.1, push=6.5, stamp_slow=1.05, stamp_fast=0.8, n_slow=3,
                          lathe_slow=5.0, lathe_fast=2.4, n_lathe_slow=2, sand=5.5, advance=2.5, run_out=6.0,
                          cut=3.2, glass=0.85, gather=7.0, place=0.95, first=7.5, sign=4.5, pump=2.4, bat=2.4,
                          ghost=2.8, lights=6.0, hero=7.0)
        d.update(P.get("durations", {}))
        self._timeline()

    # ------------------------------------------------------------------ timeline

    def _timeline(self):
        d, T = self.d, {}
        t = d["enter"] - 1.0
        T["coal"] = t
        self.shovels = [t + k * d["shovel"] for k in range(d["n_shovel"])]
        t += d["n_shovel"] * d["shovel"]
        T["lift"] = t
        t += d["lift"]
        T["to_mould"] = t
        t += d["to_mould"]
        self.pours = [t + i * (d["pour"] + d["pour_move"]) for i in range(6)]
        self.fill_end = [p + 0.5 + 1.6 for p in self.pours]
        t = self.pours[-1] + d["pour"]
        T["pour_end"] = t
        T["unload"] = t + d["cool"]
        self.unloads = [T["unload"] + i * d["unload"] for i in range(6)]
        T["push"] = self.unloads[-1] + d["unload"]
        T["press"] = T["push"] + d["push"]
        # Springs: onto the ram, then one stamp per landing (12 wings)
        self.stamps, s = [], T["press"] + 1.6
        for k in range(12):
            self.stamps.append(s)
            s += d["stamp_slow"] if k < d["n_slow"] else d["stamp_fast"]
        T["press_end"] = self.stamps[-1] + 0.6
        T["bodies"] = T["press_end"] + 0.3
        T["lathe"] = T["press_end"] + 2.6
        self.cycles, s = [], T["lathe"] + 0.6
        for j in range(8):
            D_ = d["lathe_slow"] if j < d["n_lathe_slow"] else d["lathe_fast"]
            self.cycles.append((s, D_))
            s += D_
        T["lathe_end"] = s
        T["sand1"] = s + 0.8
        T["adv1"] = T["sand1"] + d["sand"]
        T["sand2"] = T["adv1"] + d["advance"]
        T["adv2"] = T["sand2"] + d["sand"]
        T["belt_end"] = T["adv2"] + d["run_out"] + 1.5
        T["cut"] = T["belt_end"] + 0.5
        self.cuts = [T["cut"] + 1.2 + k * d["cut"] for k in range(4)]
        T["glass"] = self.cuts[-1] + d["cut"] + 0.8
        self.glows = [T["glass"] + 1.5 + k * d["glass"] for k in range(16)]   # 12 bulbs, then 4 globes
        T["gather"] = self.glows[-1] + 1.2
        self.globe_hang = [self.glows[-1] + 4.5 + i * 0.9 for i in range(4)]
        T["place"] = T["gather"] + d["gather"]
        self.places = [T["place"] + i * d["place"] for i in range(8)]
        T["first"] = self.places[-1] + d["place"] + 0.6
        f = T["first"]
        self.ptimes = [dict(dig=f, stem=f + 1.6, ribs=f + 2.6, face=f + 3.8, candle=f + 5.6, lit=f + d["first"])]
        T["reveal"] = self.ptimes[0]["lit"]
        T["rest"] = T["reveal"] + d["sign"]
        for i in range(1, 8):
            a = T["rest"] + (i - 1) * d["pump"]
            self.ptimes.append(dict(dig=a, stem=a + 0.75, ribs=a + 1.1, face=a + 1.45, candle=a + 2.2, lit=a + 2.75))
        T["bats"] = self.ptimes[-1]["lit"] + 1.0
        self.bats = [T["bats"] + 1.0 + i * d["bat"] for i in range(6)]
        T["ghosts"] = self.bats[-1] + d["bat"] + 0.5
        self.ghosts = [T["ghosts"] + 0.8 + i * d["ghost"] for i in range(4)]
        T["lights"] = self.ghosts[-1] + d["ghost"] + 0.4
        T["hero"] = T["lights"] + d["lights"]
        T["end"] = T["hero"] + d["hero"]
        self.T, self.dur = T, T["end"]
        self.stats = {"workshop_s": round(self.dur, 1), "reveal_local_s": round(T["reveal"], 1)}

    def melodies(self):
        T = self.T
        # no tune while the parts are a mystery; after the reveal a quiet pluck version of the Halloween tune
        return [(T["reveal"] + 2.0, T["end"] - 2.0, "pluck", 0.8, 60.0 / 92, TUNE_HALLOWEEN)]

    # ------------------------------------------------------------------ helpers: where things are

    def heat(self, t):
        """Furnace fire 0.2 .. 1.0, up a step with every shovel of coal."""
        h = 0.25
        for s in self.shovels:
            h += 0.19 * smoothstep(seg(t, s + 2.0, s + 2.6))
        return min(1.0, h)

    def trolley(self, t):
        """(x, chain length, tilt) of the crucible on its gantry."""
        T, d = self.T, self.d
        fx = self.furnace_x
        top = self.G - 600                                      # furnace top
        hang_in = top + 60 - self.trolley_y                     # crucible down inside the furnace
        hang_up = top - 150 - self.trolley_y
        if t < T["lift"]:
            return fx, hang_in, 0.0
        if t < T["to_mould"]:
            return fx, lerp(hang_in, hang_up, smootherstep(seg(t, T["lift"] + 0.3, T["to_mould"]))), 0.0
        hang_pour = self.bench_y - 260 - self.trolley_y
        x = fx
        tilt = 0.0
        if t < self.pours[0]:
            u = smootherstep(seg(t, T["to_mould"], self.pours[0]))
            x = lerp(fx, self.moulds[0] - 70, u)
            return x, lerp(hang_up, hang_pour, u), 0.0
        for i, p in enumerate(self.pours):
            nxt = self.pours[i + 1] if i < 5 else None
            if nxt is None or t < nxt:
                x = self.moulds[i] - 70
                tilt = smoothstep(seg(t, p, p + 0.5)) * (1 - smoothstep(seg(t, p + 2.1, p + 2.6)))
                if nxt is not None and t > p + self.d["pour"]:
                    x = lerp(x, self.moulds[i + 1] - 70, smootherstep(seg(t, p + self.d["pour"], nxt)))
                if nxt is None and t > p + self.d["pour"]:
                    # park it back over the furnace while the castings cool
                    u = smootherstep(seg(t, p + self.d["pour"] + 0.5, p + self.d["pour"] + 4.0))
                    return lerp(x, fx, u), lerp(hang_pour, hang_up, u), 0.0
                return x, hang_pour, tilt
        return fx, hang_up, 0.0

    def mould_temp(self, i, t):
        """0 = empty, then 1.0 hot, cooling to ~0 (cast iron) - and None once unloaded."""
        if t >= self.unloads[i] + 0.02:                          # lifted out by Hans
            return None
        if t < self.pours[i] + 0.5:
            return 0.0
        fill = seg(t, self.pours[i] + 0.5, self.fill_end[i])
        cool = math.exp(-max(0.0, t - self.fill_end[i]) / 2.4)
        return fill * (0.02 + 0.98 * cool) if fill >= 1 else fill * 0.98

    def mould_fill(self, i, t):
        return seg(t, self.pours[i] + 0.5, self.fill_end[i])

    def tote_x(self, t):
        T = self.T
        if t < T["unload"] - 0.5:
            return self.moulds[0] + 30
        if t < T["push"]:
            k = min(5, int((t - T["unload"]) / self.d["unload"]))
            return self.moulds[k] + 40 + 80 * seg(t, self.unloads[k], self.unloads[k] + self.d["unload"])
        return lerp(self.moulds[5] + 120, self.tote_park, smootherstep(seg(t, T["push"], T["press"])))

    def ram_top(self, t):
        """Top of the press ram: pushed down 70 by each landing, then the springs bring it back."""
        y = self.ram_rest
        for s in self.stamps:
            if s - 0.02 <= t < s + 0.5:
                u = (t - s) / 0.5
                y = self.ram_rest + 70 * (math.sin(min(1.0, u / 0.25) * math.pi / 2) if u < 0.25 else
                                         math.exp(-(u - 0.25) * 6) * math.cos((u - 0.25) * 8))
        return y

    def springs_press(self, t):
        """(x, feet y, squash) for Springs while working the press."""
        T, x = self.T, self.press_x
        on = T["press"]
        if t < on:
            return x + 160, self.G, 0.0
        if t < self.stamps[0]:
            # hop up from the floor onto the ram
            u = seg(t, on, self.stamps[0])
            y0, y1 = self.G, self.ram_rest
            dur = self.stamps[0] - on
            vy = (y1 - y0 - 0.5 * GRAVITY * dur * dur) / dur
            tau = u * dur
            return lerp(x + 160, x, u), y0 + vy * tau + 0.5 * GRAVITY * tau * tau, 0.0
        for k, s in enumerate(self.stamps):
            nxt = self.stamps[k + 1] if k < 11 else T["press_end"] + 0.9
            if t < nxt:
                # ballistic hop from landing to landing (same height, so the apex comes out of the period)
                dur = nxt - s
                tau = t - s
                vy = -0.5 * GRAVITY * dur
                lift = -(vy * tau + 0.5 * GRAVITY * tau * tau)
                if k == 11:                                      # last one: hop off to the right
                    y = self.ram_top(t) - lift if tau < 0.05 else lerp(self.ram_rest, self.G, seg(tau, 0, dur)) - lift
                    return lerp(x, x + 200, seg(tau, 0, dur)), y, 0.0
                sq = 0.8 * max(0.0, 1 - tau / 0.12) + 0.8 * max(0.0, 1 - (dur - tau) / 0.08)
                return x, self.ram_top(t) - lift, min(1.0, sq)
        return x + 200, self.G, 0.0

    def belt_shift(self, t):
        """How many slots the belt has moved (float)."""
        T, d = self.T, self.d
        b = 0.0
        for s, D_ in self.cycles:
            b += smootherstep(seg(t, s + D_ * 0.92, s + D_ * 0.92 + 0.5))
        b += 4 * smootherstep(seg(t, T["adv1"], T["adv1"] + d["advance"]))
        b += 13 * seg(t, T["adv2"], T["adv2"] + d["run_out"])
        return b

    def ball_on_belt(self, j, t):
        """(x, y bottom, sanded, paint, state) for big ball j once the lathe is done with it."""
        s, D_ = self.cycles[j]
        t_on = s + D_ * 0.92
        rel = s + D_ * 0.84                                      # the chuck lets go
        if t < t_on:
            # drops onto the ramp under the chuck and rolls down it onto the belt (speeding up)
            u = seg(t, rel, t_on)
            bottom = self.spindle_y + self.big_r
            return lerp(self.lathe_x, self.slot0, u * u), lerp(bottom, self.belt_y, u), 0.35, 0.0, "ramp"
        slot = self.belt_shift(t) - self.belt_shift(t_on)
        x = self.slot0 + slot * self.pitch
        sanded = 0.35
        batch = 0 if j < 4 else 1
        s0 = self.T["sand1"] if batch == 0 else self.T["sand2"]
        sanded += 0.65 * seg(t, s0, s0 + self.d["sand"])
        paint = smoothstep((x - (self.booth[0] + 120)) / 120)
        if x <= self.belt_end:
            return x, self.belt_y, sanded, paint, "belt"
        # off the end of the belt: falls into the wagon (constant belt speed sideways, gravity down)
        v = 13 * self.pitch / self.d["run_out"]
        t_off = t - (x - self.belt_end) / v
        tau = t - t_off
        k = self._wagon_order(j)
        tx, ty = self.wagon_slot(k)
        fall_t = math.sqrt(max(1e-4, 2 * (ty - self.belt_y) / GRAVITY))
        if tau < fall_t:
            u = tau / fall_t
            return lerp(self.belt_end, tx, u), self.belt_y + 0.5 * GRAVITY * tau * tau, 1.0, 1.0, "fall"
        return tx, ty, 1.0, 1.0, "wagon"

    def _wagon_order(self, j):
        return j

    def wagon_pos(self, t):
        """Wagon's centre x: waiting under the end of the belt, then pulled to the table by Wheels."""
        m = self.m("wheels")
        if t < self.T["gather"] - 0.5 or m is None:
            return self.wagon_x
        return m.x - 200

    def wagon_slot(self, k, t=None):
        """Eight balls in the wagon: four on the bed, four nestled on top of them."""
        wx = self.wagon_pos(t if t is not None else self.T["adv2"])
        if k < 4:
            return wx - 75 + 50 * k, self.G - 66
        if k < 7:
            return wx - 50 + 50 * (k - 4), self.G - 66 - 72
        return wx, self.G - 66 - 144

    def pumpkin_state(self, i, t):
        """(x, y, paint, ribs, stem, carve, lit, hollow) for pumpkin i on the table (None before it's there)."""
        T = self.T
        p = self.places[i]
        if t < p:
            return None
        u = smootherstep(seg(t, p, p + 0.6))
        k = self._wagon_order(i)
        wx, wy = self.wagon_slot(k, p)
        x = lerp(wx, self.pumps[i], u)
        y = lerp(wy, self.table_y, u) - 90 * math.sin(math.pi * u)
        pt = self.ptimes[i]
        stem = smoothstep(seg(t, pt["stem"], pt["stem"] + 0.35))
        ribs = smoothstep(seg(t, pt["ribs"], pt["ribs"] + (1.0 if i == 0 else 0.3)))
        carve = seg(t, pt["face"], pt["face"] + (1.6 if i == 0 else 0.7))
        lit = smoothstep(seg(t, pt["lit"] - 0.25, pt["lit"] + 0.2))
        return x, y, 1.0, ribs, stem, carve, lit

    def sign_amount(self, t):
        return seg(t, self.T["reveal"] + 0.4, self.T["reveal"] + 2.6)

    # ------------------------------------------------------------------ camera

    def target(self, t):
        T, G = self.T, self.G
        keys = [(0.0, 80, G - 380, 1.1), (self.d["enter"] - 1.0, 80, G - 380, 1.1), (T["coal"] + 1.5, 230, G - 320, 1.4),
                (T["lift"] - 0.5, 300, G - 330, 1.35), (T["lift"] + 1.2, 560, G - 470, 1.15),
                (T["to_mould"], 700, G - 450, 1.2)]
        cam = None
        if t < T["to_mould"]:
            return self._keys(keys, t)
        if t < T["unload"]:
            x = self.trolley(t)[0] + 90
            if t < self.pours[0]:
                return self._keys([(T["to_mould"], 700, G - 450, 1.2), (self.pours[0], x, G - 400, 1.35)], t)
            if t > T["pour_end"]:                           # stay on the moulds while the castings cool
                return self._keys([(T["pour_end"], min(x, self.moulds[4] - 40), G - 400, 1.35),
                                   (T["pour_end"] + 2.0, (self.moulds[0] + self.moulds[-1]) / 2, G - 380, 1.3)], t)
            return min(x, self.moulds[4] - 40), G - 400, 1.35
        if t < T["press"]:
            hx = self.m("tentacles").x if self.m("tentacles") else 1300
            return float(np.clip(hx + 160, self.moulds[1], self.tote_park + 40)), G - 360, 1.3
        if t < T["lathe"] - 0.8:
            return self.press_x - 60, G - 560, 0.98
        if t < T["sand1"] - 0.5:
            return self._keys([(T["lathe"] - 0.8, self.press_x - 60, G - 560, 0.98),
                               (T["lathe"] + 1.0, self.lathe_x + 20, G - 290, 1.45)], t)
        if t < T["adv2"] + 1.0:
            return self._keys([(T["sand1"] - 0.5, self.lathe_x + 20, G - 290, 1.45),
                               (T["sand1"] + 1.2, self.hans_sand_x, G - 300, 1.4),
                               (T["adv1"] + 0.2, self.hans_sand_x, G - 300, 1.4),
                               (T["sand2"] - 0.2, self.hans_sand_x + 230, G - 320, 1.2),
                               (T["sand2"] + 1.0, self.hans_sand_x + 100, G - 300, 1.3)], t)
        if t < T["cut"]:
            return self._keys([(T["adv2"] + 1.0, self.hans_sand_x + 100, G - 300, 1.3),
                               (T["adv2"] + 3.0, sum(self.booth) / 2, G - 330, 1.15),
                               (T["belt_end"] - 1.5, self.belt_end - 40, G - 300, 1.2)], t)
        if t < T["glass"]:
            return self._keys([(T["cut"], self.belt_end - 40, G - 300, 1.2), (T["cut"] + 1.2, self.sheet_x + 80, G - 330, 1.25)], t)
        if t < T["gather"]:
            gx = lerp(self.bulb_hooks[0][0] + 60, self.bulb_hooks[1][0], seg(t, T["glass"] + 1.5, self.glows[-1]))
            return self._keys([(T["glass"], self.sheet_x + 80, G - 330, 1.25),
                               (T["glass"] + 1.2, self.bulb_hooks[0][0] + 60, G - 380, 1.25)], t) \
                if t < T["glass"] + 1.2 else (gx, G - 380, 1.2)
        if t < T["first"] - 0.5:
            return self._keys([(T["gather"], self.bulb_hooks[1][0], G - 380, 1.25), (T["place"] - 0.5, 6600, G - 420, 0.95),
                               (self.places[-1], 7150, G - 420, 0.9)], t)
        if t < T["reveal"] + 0.6:
            return self._keys([(T["first"] - 0.5, 7150, G - 420, 0.9), (T["first"] + 0.8, self.pumps[0] + 40, G - 260, 1.55)], t)
        if t < T["rest"]:
            return self._keys([(T["reveal"] + 0.6, self.pumps[0] + 40, G - 260, 1.55),
                               (T["reveal"] + 2.6, self.sign[0], G - 520, 0.82)], t)
        if t < T["bats"]:
            i = min(7, 1 + int((t - T["rest"]) / self.d["pump"]))
            return self._keys([(T["rest"], self.sign[0], G - 520, 0.82), (T["rest"] + 1.5, self.pumps[1] + 120, G - 330, 1.2)], t) \
                if t < T["rest"] + 1.5 else (self.pumps[i] + 40 - self.d["pump"] * 0, G - 330, 1.2)
        if t < T["lights"]:
            # close on each bat / ghost as it's put together, gliding from one to the next
            if t < T["ghosts"]:
                i = min(5, max(0, int((t - self.bats[0] + 0.6) / self.d["bat"])))
                x = lerp(self._hang_x("bat", max(0, i - 1)), self._hang_x("bat", i),
                         smootherstep(seg(t, self.bats[i] - 0.8, self.bats[i] + 0.2))) if i else self._hang_x("bat", 0)
                return self._keys([(T["bats"], self.pumps[7], G - 330, 1.2), (self.bats[0], x - 60, G - 330, 1.45)], t)                     if t < self.bats[0] else (x - 60, G - 330, 1.45)
            i = min(3, max(0, int((t - self.ghosts[0] + 0.8) / self.d["ghost"])))
            x = lerp(self._hang_x("ghost", max(0, i - 1)), self._hang_x("ghost", i),
                     smootherstep(seg(t, self.ghosts[i] - 1.0, self.ghosts[i]))) if i else self._hang_x("ghost", 0)
            return x, G - 330, 1.45
        return self._keys([(T["lights"], 8580, G - 400, 1.05), (T["lights"] + 2.5, 7700, G - 540, 0.72),
                           (T["end"], 7650, G - 560, 0.68)], t)

    @staticmethod
    def _keys(keys, t):
        if t <= keys[0][0]:
            return keys[0][1:]
        for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
            if t < t1:
                u = smootherstep((t - t0) / (t1 - t0))
                return tuple(lerp(p, q, u) for p, q in zip(a, b))
        return keys[-1][1:]

    def name_amount(self, kind, t):
        """Each Keeper's nameplate pops up when the camera first arrives at its station."""
        T = self.T
        at = {"digger": T["coal"] + 1.0, "tentacles": T["lift"] + 1.5, "springs": T["press"] + 0.2,
              "wheels": T["lathe"] + 3.6, "teeth": T["cut"] + 1.4, "lantern": T["glass"] + 1.2}.get(kind)
        if at is None:
            return 0.0
        return smoothstep(seg(t, at, at + 0.5)) * (1 - smoothstep(seg(t, at + 3.5, at + 4.3)))

    # ------------------------------------------------------------------ update: monsters

    def update(self, t, dt):
        s = self.s
        self.reach = {}
        self.carry = {}                                         # kind -> draw fn for what it holds
        self._digs(t, dt)
        self._hans(t, dt)
        self._springs(t, dt)
        self._wheels(t, dt)
        self._twigs(t, dt)
        self._glo(t, dt)
        self._particles(t)
        self._sounds(t)

    def _walk(self, m, keys, t, dt, y=None, dy=0.0, ang=0.0):
        """Walk along keyframes [(t, x, y)]; y = 0 in the keys means 'on the floor'."""
        keys = [(k[0], k[1], k[2] if k[2] else self.G) for k in keys]
        x, yy, mv = path(keys, t)
        self.place(m, x, t, dt, y=y if y is not None else yy, dy=dy, ang=ang, walk=1.0 if mv else 0.0)
        return x

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        T, G = self.T, self.G
        m.dig = 0.0
        if t < T["coal"]:
            self._walk(m, [(0.4, self.door_x - 60, 0), (T["coal"], self.coal_x + 100, 0)], t, dt)
            return
        if t < self.shovels[-1] + self.d["shovel"]:
            k = min(len(self.shovels) - 1, int((t - T["coal"]) / self.d["shovel"]))
            u = (t - self.shovels[k]) / self.d["shovel"]
            pile, mouth = self.coal_x + 100, self.furnace_x - 150
            if u < 0.28:                                        # scoop: shovels down into the pile
                x = pile
                m.dig = math.sin(min(1.0, u / 0.28) * math.pi)
            elif u < 0.55:
                x = lerp(pile, mouth, smootherstep((u - 0.28) / 0.27))
                m.dig = 0.15
            elif u < 0.7:                                       # throw
                x = mouth
                m.dig = 0.2 + 0.8 * (1 - math.sin(min(1.0, (u - 0.55) / 0.15) * math.pi / 2))
            else:
                x = lerp(mouth, pile, smootherstep((u - 0.7) / 0.3))
            if u < 0.62:
                self.carry["digger"] = ("coal", k)
            self.place(m, x, t, dt)
            return
        # off to the assembly table (a long walk while the others work), then hollow each pumpkin
        ready = self.ptimes[0]["dig"] - 1.0
        if t < ready:
            self._walk(m, [(self.shovels[-1] + self.d["shovel"] + 1.0, self.coal_x + 100, 0),
                           (self.shovels[-1] + self.d["shovel"] + 2.5, self.coal_x - 60, 0),
                           (T["press"], self.coal_x - 60, 0), (T["press"] + 30.0, self.tableA[0] + 1250, 0),
                           (ready - 2.0, self.tableA[0] + 1250, 0), (ready, self.pumps[0] + 135, 0)], t, dt)
            return
        for i in range(8):
            pt = self.ptimes[i]
            nxt = self.ptimes[i + 1]["dig"] - 0.45 if i < 7 else T["bats"]
            if t < nxt:
                dur = (pt["stem"] - pt["dig"]) * 0.85
                x = self.pumps[i] + 135
                if t < pt["dig"]:
                    x = lerp(self.pumps[i - 1] + 135 if i else x, x, smootherstep(seg(t, nxt - 2.4, pt["dig"])))
                if pt["dig"] <= t < pt["dig"] + dur:
                    m.dig = 0.5 + 0.5 * math.sin((t - pt["dig"]) / dur * 4 * math.pi)
                if t > pt["dig"] + dur:
                    x = lerp(x, self.pumps[min(7, i + 1)] + 135, smootherstep(seg(t, pt["dig"] + dur, nxt)))
                self.place(m, x, t, dt, walk=1.0 if not (pt["dig"] <= t < pt["dig"] + dur) else 0.0)
                return
        hop = -abs(math.sin(t * 6)) * 14 if T["hero"] <= t < T["hero"] + 2 else 0.0
        self._walk(m, [(T["bats"], self.pumps[7] + 135, 0), (T["bats"] + 4, 7200, 0)], t, dt, dy=hop)

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        T, G = self.T, self.G
        reach = []
        if t < T["lift"] + 1.2:
            self._walk(m, [(1.0, self.door_x - 90, 0), (T["lift"] - 1.0, self.furnace_x + 340, 0)], t, dt)
        elif t < T["unload"]:
            x, chain, tilt = self.trolley(t)
            hx = x - 210 if t >= self.pours[0] - 0.3 else self.furnace_x + 340
            if T["to_mould"] <= t < self.pours[0] - 0.3:
                hx = lerp(self.furnace_x + 340, x - 210, smootherstep(seg(t, T["to_mould"], self.pours[0] - 0.3)))
            self.place(m, hx, t, dt)
            if t >= T["lift"] + 1.6 and t < T["pour_end"] + 0.6:
                cx, cy = self._crucible_handle(t)
                reach += [(cx, cy), (cx + 8, cy + 44)]
        elif t < T["push"]:
            k = min(5, int((t - T["unload"]) / self.d["unload"]))
            u = seg(t, self.unloads[k], self.unloads[k] + self.d["unload"])
            hx = self.moulds[k] - 160 + 60 * u
            self.place(m, hx, t, dt, walk=0.6)
            mx = self.moulds[k]
            tx = self.tote_x(t)
            # one tentacle lifts the castings out of the mould in an arc and lets go over the tote
            px, py = self._casting_carry(k, t)
            reach.append((px, py))
            reach.append((tx - 50, G - 150))                    # another holds the tote's handle
        elif t < T["press"]:
            tx = self.tote_x(t)
            self.place(m, tx - 190, t, dt)
            reach.append((tx - 50, G - 150))
        elif t < T["press_end"] + 1.5:
            self.place(m, self.tote_park - 150, t, dt)
            reach.append((self.tote_park - 50, G - 150))
            fp = self._feed_point(t)
            if fp is not None:
                reach.append(fp)
        elif t < T["sand1"] - 0.6:
            self._walk(m, [(T["press_end"] + 1.5, self.tote_park - 150, 0), (T["press_end"] + 3.5, self.tote_park - 150, 0),
                           (T["lathe_end"] - 2.0, self.hans_sand_x - 260, 0),
                           (T["lathe_end"] - 0.6, self.hans_sand_x, self.G - 150)], t, dt)
            if T["bodies"] <= t < T["bodies"] + 1.4:
                u = seg(t, T["bodies"], T["bodies"] + 1.4)
                reach.append((lerp(self.tote_park, self.bin_x, u), self.G - 210 - 120 * math.sin(math.pi * u)))
        elif t < T["adv2"] + self.d["advance"]:
            self.place(m, self.hans_sand_x, t, dt, y=self.G - 150)          # up on the step behind the belt
            sanding = (T["sand1"] <= t < T["adv1"]) or (T["sand2"] <= t < T["adv2"])
            for q, sl in enumerate(self.sand_slots):
                bx = self.slot0 + sl * self.pitch
                ball_top = self.belt_y - 2 * self.big_r
                rub = 16 * math.sin(t * 11 + q * 1.7) if sanding else 0.0
                reach.append((bx + rub, ball_top - 6))
        elif t < T["bats"] - 0.5:
            self._walk(m, [(T["adv2"] + self.d["advance"], self.hans_sand_x, self.G - 150),
                           (T["adv2"] + self.d["advance"] + 1.2, self.hans_sand_x + 250, self.G),
                           (T["gather"] + 4.0, 7450, self.G),
                           (T["rest"], 7450, self.G), (T["bats"] - 0.5, 8000, self.G)], t, dt)
            if T["reveal"] <= t < T["reveal"] + 1.5:
                self.poses["tentacles"] = (-abs(math.sin((t - T["reveal"]) * 7)) * 22, 0.0)
        else:
            # assembling bats at the rail: body in one tentacle, the wings come in from both sides
            i = min(5, max(0, int((t - self.bats[0]) / self.d["bat"]))) if t >= self.bats[0] else 0
            bx = self._hang_x("bat", i)
            if t < T["ghosts"]:
                self._walk(m, [(T["bats"] - 0.5, 8000, 0), (self.bats[0] - 0.3, bx - 200, 0)], t, dt) if t < self.bats[0] \
                    else self.place(m, lerp(self._hang_x("bat", max(0, i - 1)) - 200, bx - 200,
                                             smootherstep(seg(t, self.bats[i] - 0.5, self.bats[i]))) if i else bx - 200, t, dt)
                if t >= self.bats[0]:
                    for p in self._bat_reach(i, t):
                        reach.append(p)
            elif t < T["lights"]:
                self._walk(m, [(T["ghosts"], self._hang_x("bat", 5) - 200, 0), (T["ghosts"] + 3, 8900, 0)], t, dt)
            else:
                hop = -abs(math.sin(t * 6)) * 18 if T["hero"] <= t < T["hero"] + 2 else 0.0
                self._walk(m, [(T["lights"], 8900, 0), (T["lights"] + 3.0, self.sign[0] + 250, 0)], t, dt, dy=hop)
        self.reach["tentacles"] = reach

    def _crucible_handle(self, t):
        x, chain, tilt = self.trolley(t)
        cy = self.trolley_y + chain + 50
        a = tilt * 1.05
        hx, hy = x - 62, cy + 10
        c, s_ = math.cos(a), math.sin(a)
        return x + (hx - x) * c - (hy - cy) * s_, cy + (hx - x) * s_ + (hy - cy) * c

    def _casting_carry(self, k, t):
        """Where mould k's castings are while Hans lifts them out (an arc from mould to tote)."""
        u = seg(t, self.unloads[k], self.unloads[k] + self.d["unload"] * 0.8)
        mx = self.moulds[k]
        tx = self.tote_x(self.unloads[k] + self.d["unload"] * 0.8)
        x = lerp(mx, tx, smootherstep(u))
        y = lerp(self.bench_y - 20, self.G - 200, smootherstep(u)) - 160 * math.sin(math.pi * u)
        return x, y

    def _feed_point(self, t):
        """Hans' tentacle putting the next blank on the anvil while Springs is in the air."""
        for k, s in enumerate(self.stamps):
            prev = self.stamps[k - 1] if k else self.T["press"] + 0.4
            a0, a1 = prev + 0.15, s - 0.02
            if a0 <= t < a1:
                u = seg(t, a0, a1)
                return (lerp(self.tote_park, self.press_x, smootherstep(u)),
                        lerp(self.G - 180, self.anvil_y - 8, smootherstep(u)) - 120 * math.sin(math.pi * u))
        return None

    def _hang_x(self, kind, i):
        idx = [k for k, kk in enumerate(self.hang_kind) if kk == kind][i]
        return self.hang[idx]

    def _bat_reach(self, i, t):
        b = self.bats[i]
        x, rail = self._hang_x("bat", i), self.railB[2]
        by = rail + 90
        u = seg(t, b, b + self.d["bat"] * 0.7)
        if u <= 0:
            return [(x - 60, by + 20)]
        if u >= 1:
            return []
        # body held up to the hook, the two wings pressed on from either side
        return [(x, by + 18), (lerp(x - 160, x - 30, smootherstep(u * 1.6)), by),
                (lerp(x + 160, x + 30, smootherstep(u * 1.6 - 0.3)), by)]

    def bat_state(self, i, t):
        """(wings 0..1, hung, flap) for bat i."""
        b = self.bats[i]
        u = seg(t, b, b + self.d["bat"] * 0.7)
        wings = smoothstep(min(1.0, u * 1.6)) * 0.5 + smoothstep(min(1.0, u * 1.6 - 0.3)) * 0.5
        hung = t >= b + self.d["bat"] * 0.7
        flap = 0.0
        if hung:
            tau = t - (b + self.d["bat"] * 0.7)
            flap = 0.8 * math.sin(tau * 14) * math.exp(-tau * 1.2) + 0.12 * math.sin(t * 2 + i)
        return wings, hung, flap

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        T, G = self.T, self.G
        m.spring = 0.0
        if t < T["press"]:
            x, lift, sq = hops(self.door_x, self.press_x + 160, 1.6, 13.0, t)
            m.spring = sq
            self.place(m, x, t, dt, dy=-lift, walk=0.0)
            return
        if t < T["press_end"] + 1.0:
            x, y, sq = self.springs_press(t)
            m.spring = sq
            self.place(m, x, t, dt, y=y, walk=0.0)
            return
        # carries the bin of bat parts to the rail, hopping
        leave, arrive = T["press_end"] + 1.2, T["press_end"] + 1.2 + 17.0
        x0, x1 = self.press_x + 200, self.bin_drop
        if t < T["reveal"]:
            x, lift, sq = hops(x0, x1, leave, arrive, t)
            m.spring = sq
            self.place(m, x, t, dt, dy=-lift, walk=0.0)
            if leave - 0.6 <= t < arrive + 0.5:
                self.carry["springs"] = ("bin", None)
            return
        # cheers at the reveal (big hops), then stays by the rail
        tau = t - T["reveal"]
        lift = 0.0
        if tau < 2.4:
            ph = (tau % 0.8) / 0.8
            lift = 4 * 120 * ph * (1 - ph)
            m.spring = 0.7 * max(0.0, 1 - min(ph, 1 - ph) / 0.1)
        if T["hero"] <= t < T["hero"] + 2.4:
            ph = ((t - T["hero"]) % 0.8) / 0.8
            lift = 4 * 120 * ph * (1 - ph)
            m.spring = 0.7 * max(0.0, 1 - min(ph, 1 - ph) / 0.1)
        x = lerp(x1, 7450, smootherstep(seg(t, T["rest"], T["rest"] + 3.0)))
        self.place(m, x, t, dt, dy=-lift, walk=0.0)

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        T = self.T
        # right claw reaches the pallet from `pick`, the chuck from `lathe`
        pick, lathe = self.pallet_x - 135, self.lathe_x - 135
        if t < self.cycles[0][0]:
            self._walk(m, [(0.8, self.door_x - 140, 0), (12.0, pick, 0)], t, dt)
            return
        if t < T["lathe_end"] + 0.3:
            j = max(k for k, (s, D_) in enumerate(self.cycles) if t >= s)
            s, D_ = self.cycles[j]
            u = (t - s) / D_
            if u < 0.12:
                x = pick
                self.carry["wheels"] = ("block", j, 0.0) if u > 0.06 else None
            elif u < 0.3:
                x = lerp(pick, lathe, smootherstep((u - 0.12) / 0.18))
                self.carry["wheels"] = ("block", j, 0.0)
            elif u < 0.84:
                x = lathe                                       # holds the tool rest while it turns
            else:
                x = lerp(lathe, pick, smootherstep((u - 0.84) / 0.16))
            self.place(m, x, t, dt)
            return
        if t < T["gather"]:
            self._walk(m, [(T["lathe_end"] + 0.2, lathe, 0), (T["lathe_end"] + 4.6, self.wagon_x + 200, 0)], t, dt)
            return
        if t < T["place"] - 0.2:
            self._walk(m, [(T["gather"], self.wagon_x + 200, 0), (T["place"] - 0.2, self.pumps[0] - 135, 0)], t, dt)
            return
        if t < self.ptimes[0]["dig"]:
            # puts each orange ball on its spot: drives along the table, claw lifts it out of the wagon
            i = min(7, int((t - T["place"]) / self.d["place"]))
            x = lerp(self.pumps[max(0, i - 1)] - 135, self.pumps[i] - 135,
                     smootherstep(seg(t, self.places[i] - 0.45, self.places[i]))) if i else self.pumps[0] - 135
            if t > self.places[-1] + 0.6:
                x = lerp(self.pumps[7] - 135, self.pumps[0] - 260, smootherstep(seg(t, self.places[-1] + 0.6, self.ptimes[0]["dig"])))
            self.place(m, x, t, dt)
            return
        for i in range(8):
            pt = self.ptimes[i]
            nxt = self.ptimes[i + 1]["stem"] - 0.6 if i < 7 else T["bats"]
            if t < nxt:
                x = self.pumps[i] - 135
                if t < pt["stem"] - 0.4:
                    x = lerp(self.pumps[i - 1] - 135 if i else self.pumps[0] - 260, x,
                             smootherstep(seg(t, pt["stem"] - 1.2, pt["stem"] - 0.4)))
                if pt["stem"] - 0.3 <= t < pt["stem"] + 0.3:
                    self.carry["wheels"] = ("stem", i, 0.0)
                self.place(m, x, t, dt)
                return
        self._walk(m, [(T["bats"], self.pumps[7] - 135, 0), (T["bats"] + 3, 6950, 0)], t, dt)

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        T, G = self.T, self.G
        k = m.k
        mouth = 333 * k                                          # mouth height above the feet
        if t < self.cuts[0]:
            self._walk(m, [(1.6, self.door_x - 100, 0), (18.0, self.sheet_x + 210, 0)], t, dt)
            return
        if t < self.cuts[-1] + self.d["cut"]:
            q = min(3, int((t - self.cuts[0]) / self.d["cut"]))
            u = (t - self.cuts[q]) / self.d["cut"]
            cx, cy = self.cut_c
            if 0.15 <= u < 0.75:
                a = -math.pi / 2 + (u - 0.15) / 0.6 * 2 * math.pi
                px, py = cx + math.cos(a) * 80, cy + math.sin(a) * 80
                self.place(m, px + 22, t, dt, dy=(py - (G - mouth)), ang=-0.12, walk=0.0)
            else:
                self.place(m, cx + 160, t, dt, walk=0.0)
            return
        # carries the stack of cloth discs to the table, then carves
        ready = self.ptimes[0]["ribs"] - 0.6
        if t < ready:
            self._walk(m, [(self.cuts[-1] + self.d["cut"], self.cut_c[0] + 160, 0), (T["gather"] + 3.5, self.disc_x, 0),
                           (ready, self.pumps[0] + 120, 0)], t, dt)
            if t < T["gather"] + 3.5:
                self.carry["teeth"] = ("discs", None)
            return
        for i in range(8):
            pt = self.ptimes[i]
            nxt = self.ptimes[i + 1]["ribs"] - 0.4 if i < 7 else T["ghosts"]
            if t < nxt:
                x = self.pumps[i] + 108
                ang = 0.0
                if t < pt["ribs"] - 0.1:
                    x = lerp(self.pumps[i - 1] + 108 if i else x, x, smootherstep(seg(t, pt["ribs"] - 0.9, pt["ribs"] - 0.1)))
                carving = pt["ribs"] <= t < pt["face"] + (1.6 if i == 0 else 0.7)
                if carving:
                    ang = -0.42 + 0.06 * math.sin(t * 15)
                if i == 0:                                       # steps back to watch the candle go in
                    x += 150 * smootherstep(seg(t, pt["face"] + 1.7, pt["face"] + 2.4))
                if T["reveal"] <= t < T["reveal"] + 2.0:
                    self.place(m, x, t, dt, dy=-abs(math.sin((t - T["reveal"]) * 6)) * 30, walk=0.0)
                    return
                self.place(m, x, t, dt, ang=ang, walk=1.0 if abs(x - m.x) > 2 else 0.0)
                return
        # ghosts: bites two eye holes into each draped cloth
        if t < T["lights"]:
            i = min(3, max(0, int((t - self.ghosts[0]) / self.d["ghost"]))) if t >= self.ghosts[0] else 0
            gx = self._hang_x("ghost", i)
            g = self.ghosts[i]
            x = gx + 95
            if t < self.ghosts[0]:
                x = lerp(self.pumps[7] + 108, self._hang_x("ghost", 0) + 95, smootherstep(seg(t, T["bats"], self.ghosts[0])))
            elif i and t < g:
                x = lerp(self._hang_x("ghost", i - 1) + 95, x, smootherstep(seg(t, g - 0.8, g)))
            biting = g + 1.5 <= t < g + 2.3
            head_y = self.railB[2] + 70 + 27
            dy = (head_y - (G - mouth)) * smoothstep(seg(t, g + 1.2, g + 1.5)) * (1 - smoothstep(seg(t, g + 2.3, g + 2.6)))
            self.place(m, x, t, dt, dy=dy, ang=(-0.3 + 0.05 * math.sin(t * 15)) if biting else 0.0, walk=0.0)
            return
        self._walk(m, [(T["lights"], self._hang_x("ghost", 3) + 95, 0), (T["lights"] + 3, 7500, 0)], t, dt,
                   dy=-abs(math.sin(t * 6)) * 24 if T["hero"] <= t < T["hero"] + 2 else 0.0)

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        T, G = self.T, self.G
        k = m.k
        lamp_dy = (260 - 82) * k                                # lantern belly above the "feet" point
        if t < self.glows[0] - 0.6:
            x, y, _ = path([(0.2, self.door_x - 40, G - 40), (14.0, self.bulb_hooks[0][0] - 60, G - 40),
                            (T["glass"] + 0.6, self.bulb_hooks[0][0] - 60, G - 40),
                            (self.glows[0] - 0.6, self.bulb_hooks[0][0], self.bulb_hooks[0][1] + 40 + lamp_dy)], t)
            self.place(m, x, t, dt, y=y)
            return
        if t < self.glows[-1] + 0.6:
            q = min(15, int((t - self.glows[0] + 0.45) / self.d["glass"]))
            tx, ty = self._glow_target(q)
            px, py = self._glow_target(max(0, q - 1))
            u = smootherstep(seg(t, self.glows[q] - 0.45, self.glows[q] - 0.1))
            x, y = lerp(px, tx, u), lerp(py, ty, u)
            self.place(m, x, t, dt, y=y - 30 + lamp_dy)
            return
        if t < self.ptimes[0]["candle"] - 0.6:
            # takes the bulb string and the four globes along: hangs the globes on the rail, leaves the string
            # coiled by the table, then comes back for the candles
            hang_y = self.railB[2] + lamp_dy
            keys = [(self.glows[-1] + 0.6, self.globe_x[-1], self.globe_y - 90 + lamp_dy)]
            for i, th in enumerate(self.globe_hang):
                gx = self._hang_x("ghost", i)
                keys += [(th - 0.45, gx, hang_y), (th + 0.2, gx, hang_y)]
            keys += [(self.globe_hang[-1] + 1.6, self.coil_x, G - 60), (self.globe_hang[-1] + 2.2, self.coil_x, G - 60),
                     (self.ptimes[0]["candle"] - 0.6, self.pumps[0], self.table_y - 160 + lamp_dy)]
            x, y, _ = path(keys, t)
            self.place(m, x, t, dt, y=y)
            if t < self.globe_hang[-1] + 1.9:
                self.carry["lantern"] = ("string", sum(1 for th in self.globe_hang if t < th))
            return
        if t < T["bats"]:
            for i in range(8):
                pt = self.ptimes[i]
                nxt = self.ptimes[i + 1]["candle"] - 0.5 if i < 7 else T["bats"]
                if t < nxt:
                    x = self.pumps[i]
                    if t < pt["candle"]:
                        x = lerp(self.pumps[i - 1] if i else x, x, smootherstep(seg(t, pt["candle"] - 1.2, pt["candle"] - 0.2)))
                    lower = smoothstep(seg(t, pt["candle"], pt["lit"] - 0.3)) * (1 - smoothstep(seg(t, pt["lit"], pt["lit"] + 0.4)))
                    y = self.table_y - 175 + 70 * lower + lamp_dy
                    if i == 0:                                   # floats up and aside so the lit face is seen
                        away = smootherstep(seg(t, pt["lit"] - 0.1, pt["lit"] + 0.9))
                        x += 170 * away
                        y -= 130 * away
                    self.place(m, x, t, dt, y=y)
                    if pt["candle"] - 0.3 <= t < pt["lit"]:
                        self.carry["lantern"] = ("candle", i)
                    return
        # ghosts: floats each cloth disc over a globe hanging on the rail and lets it drape
        if t < T["lights"]:
            i = min(3, max(0, int((t - self.ghosts[0]) / self.d["ghost"]))) if t >= self.ghosts[0] else 0
            gx = self._hang_x("ghost", i)
            g = self.ghosts[i]
            head = self.railB[2] + 70
            up = head - 120 + lamp_dy
            if t < g:
                prev = self.pumps[7] if i == 0 else self._hang_x("ghost", i - 1)
                t_a = g - (2.4 if i == 0 else 1.6)
                x, y, _ = path([(t_a, prev, up), (g - 0.95, self.disc_x, self.G - 150 + lamp_dy),
                                (g - 0.8, self.disc_x, self.G - 150 + lamp_dy), (g, gx, up)], t)
                self.place(m, x, t, dt, y=y)
            else:
                lift = smoothstep(seg(t, g + 0.9, g + 1.4))
                self.place(m, gx - 40 * lift, t, dt, y=up - 40 * lift)
            if g - 0.85 <= t < g + 0.9:
                self.carry["lantern"] = ("disc", i)
            return
        sx, sy, w, h = self.sign
        x, y, _ = path([(T["lights"] - 0.4, self._hang_x("ghost", 3), self.railB[2] - 50 + lamp_dy),
                        (T["lights"] + 0.8, self.coil_x, G - 60), (T["lights"] + 1.0, self.coil_x, G - 60),
                        (T["lights"] + 2.0, sx - w / 2, sy + h / 2 + 10 + lamp_dy),
                        (T["lights"] + 4.5, sx + w / 2, sy + h / 2 + 10 + lamp_dy),
                        (T["hero"] + 1.0, sx + w / 2 + 250, sy + 260 + lamp_dy)], t)
        self.place(m, x, t, dt, y=y)
        if T["lights"] + 0.9 <= t < T["lights"] + 4.5:
            self.carry["lantern"] = ("string_end", 0)

    def _glow_target(self, q):
        if q < 12:
            bx, by = self.bulb_pos(q)
            return bx, by - 10
        return self.globe_x[q - 12], self.globe_y - 60

    def bulb_pos(self, i):
        (x0, y0), (x1, y1) = self.bulb_hooks
        u = (i + 0.5) / 12
        return lerp(x0, x1, u), lerp(y0, y1, u) + 4 * 0.06 * (x1 - x0) * u * (1 - u) + 22

    # ------------------------------------------------------------------ particles + sound

    def _particles(self, t):
        T, P = self.T, self.s.particles
        rng = P.rng
        # furnace sparks rise with the heat
        if rng.uniform() < 0.25 * self.heat(t):
            P.burst(self.furnace_x + rng.uniform(-40, 40), self.mouth_y - 70, 1, FIRE, 160, 1.2, 2.5, g=-260,
                    glow=True, spread=0.5)
        # pour stream splash
        x, chain, tilt = self.trolley(t)
        if tilt > 0.6 and T["to_mould"] < t < T["pour_end"] and rng.uniform() < 0.6:
            i = min(5, max(0, int((t - self.pours[0]) / (self.d["pour"] + self.d["pour_move"]))))
            P.burst(self.moulds[i], self.bench_y - 26, 2, molten(0.9), 220, 0.4, 2.2, g=1800, glow=True, spread=1.0)
        # lathe shavings
        for s, D_ in self.cycles:
            if s + D_ * 0.35 <= t < s + D_ * 0.82 and rng.uniform() < 0.8:
                P.burst(self.lathe_x + 30, self.spindle_y + 30, 2, SAWDUST, 300, 0.7, 3.2, g=900, spread=0.9,
                        direction=-0.3)
        # sanding dust
        if (T["sand1"] <= t < T["adv1"]) or (T["sand2"] <= t < T["adv2"]):
            if rng.uniform() < 0.6:
                sl = self.sand_slots[int(rng.integers(4))]
                P.burst(self.slot0 + sl * self.pitch, self.belt_y - 2 * self.big_r, 1, SAWDUST * 1.1, 90, 1.0, 4,
                        g=-40, spread=math.pi)
        # paint mist in the booth while balls are inside
        if T["adv1"] < t < T["belt_end"] - 1.5 and rng.uniform() < 0.7:
            P.burst(rng.uniform(*self.booth) , self.belt_y - 140, 1, D.ORANGE * 0.9, 60, 0.9, 6, g=40, spread=math.pi)
        # carving chips + hollowing
        for i, pt in enumerate(self.ptimes):
            if pt["ribs"] <= t < pt["face"] + (1.6 if i == 0 else 0.7) and rng.uniform() < 0.7:
                P.burst(self.pumps[i] + 40, self.table_y - 50, 1, D.ORANGE, 240, 0.6, 3, g=1200, spread=1.0,
                        direction=-1.0)
            if pt["dig"] <= t < pt["stem"] - 0.2 and rng.uniform() < 0.6:
                P.burst(self.pumps[i] + 30, self.table_y - 80, 1, np.array([235, 200, 120]), 260, 0.6, 3.5, g=1400,
                        spread=0.8, direction=-1.2)

    def _sounds(self, t):
        T, s, G, d = self.T, self.s, self.G, self.d
        if self.crossed(0.3):
            self.fx(t, "motor", 1.5, 0.3, 300, G - 600)
        for k in range(6):                                   # hall lights come on, bank by bank
            if self.crossed(0.8 + k * 0.45):
                self.hit(t, "clack", 45 + (k % 3) * 2, 0.25, 300 + k * 600, G - 1000)
        for k, sh in enumerate(self.shovels):
            if self.crossed(sh + 0.15):
                self.fx(t, "slide", 0.4, 0.35, self.coal_x + 100, G - 60)
            if self.crossed(sh + 1.95):
                self.fx(t, "crackle", 0.5, 0.5, self.furnace_x, self.mouth_y)
                self.fx(t + 0.1, "sizzle", 1.4, 0.3, self.furnace_x, self.mouth_y)
                self.hit(t, "thud", 40, 0.25, self.furnace_x, self.mouth_y)
        if self.crossed(1.0):
            self.fx(t, "sizzle", T["pour_end"] - 1.0, 0.12, self.furnace_x, self.mouth_y)
        if self.crossed(T["lift"]):
            self.fx(t, "servo", 2.0, 0.4, self.furnace_x, G - 700)
            self.fx(t, "motor", d["lift"] + d["to_mould"], 0.35, self.furnace_x, self.trolley_y)
        for i, p in enumerate(self.pours):
            if self.crossed(p + 0.4):
                self.fx(t, "sizzle", 1.8, 0.5, self.moulds[i], self.bench_y)
            if self.crossed(self.fill_end[i]):
                self.hit(t, "soft_bell", s.note(i, -1), 0.3, self.moulds[i], self.bench_y)
            if self.crossed(self.fill_end[i] + 1.5):
                self.fx(t, "hiss", 1.6, 0.2, self.moulds[i], self.bench_y)
            if i < 5 and self.crossed(p + d["pour"]):
                self.fx(t, "servo", d["pour_move"], 0.2, self.moulds[i], self.trolley_y)
        for k, u0 in enumerate(self.unloads):
            if self.crossed(u0 + 0.15):
                self.hit(t, "clack", s.note(k, 0), 0.3, self.moulds[k], self.bench_y)
            if self.crossed(u0 + d["unload"] * 0.8):
                for q in range(3):
                    self.hit(t + q * 0.06, "clunk", s.note(k + q, -1), 0.3, self.tote_x(t), G - 150)
        if self.crossed(T["push"]):
            self.fx(t, "slide", d["push"] * 0.9, 0.25, self.tote_park, G)
            self.say(t + 0.3, "tentacles", "hum", self.tote_park, G - 200, 0.35)
        # press
        if self.crossed(T["press"] + 0.1):
            self.hit(t, "boing", s.note(2, -1), 0.5, self.press_x, G)
        for k, st in enumerate(self.stamps):
            if self.crossed(st):
                self.hit(t, "boing", s.note(k % 5, -1), 0.45, self.press_x, self.ram_rest)
                self.hit(t + 0.04, "clunk", s.note(k, -1), 0.6, self.press_x, self.anvil_y)
                self.fx(t + 0.04, "hiss", 0.3, 0.15, self.press_x, self.anvil_y)
            if self.crossed(st + 0.35):
                self.fx(t, "slide", 0.3, 0.2, self.bin_x, G - 120)
        if self.crossed(T["bodies"]):
            for q in range(6):
                self.hit(t + 0.2 + q * 0.2, "clack", s.note(q, 0), 0.25, self.bin_x, G - 120)
        # lathe
        for j, (st, D_) in enumerate(self.cycles):
            if self.crossed(st + D_ * 0.3):
                self.hit(t, "clunk", s.note(j, -1), 0.4, self.lathe_x, self.spindle_y)
            if self.crossed(st + D_ * 0.33):
                self.fx(t, "saw", D_ * 0.5, 0.32, self.lathe_x, self.spindle_y)
            if self.crossed(st + D_ * 0.9):
                self.hit(t, "pluck", s.note(j + 2, 0), 0.35, self.slot0, self.belt_y)
            if self.crossed(st + D_ * 0.92):
                self.fx(t, "motor", 0.5, 0.25, self.slot0 + 300, self.belt_y)
        for key in ("sand1", "sand2"):
            if self.crossed(T[key]):
                self.fx(t, "spray", d["sand"], 0.18, 3950, self.belt_y - 80)
                self.say(t + 0.5, "tentacles", "hum", 3950, G - 200, 0.35)
        for key, dur in (("adv1", d["advance"]), ("adv2", d["run_out"])):
            if self.crossed(T[key]):
                self.fx(t, "motor", dur, 0.4, 4300, self.belt_y)
        if self.crossed(T["adv1"] + 0.6):
            self.fx(t, "spray", T["belt_end"] - T["adv1"] - 2.0, 0.28, sum(self.booth) / 2, self.belt_y - 100)
        for j in range(8):
            ts = self._landing_time(j)
            if ts is not None and self.crossed(ts):
                self.hit(t, "thud", 47, 0.35, self.wagon_x, G - 80)
                self.hit(t, "pluck", s.note(j, -1), 0.3, self.wagon_x, G - 80)
        # cloth
        for k, c0 in enumerate(self.cuts):
            for q in range(6):
                if self.crossed(c0 + d["cut"] * (0.17 + q * 0.1)):
                    self.hit(t, "clack", s.note(q + k, 1), 0.18, self.sheet_x, G - 230)
            if self.crossed(c0 + d["cut"] * 0.78):
                self.fx(t, "rustle", 0.6, 0.3, self.sheet_x, G - 230)
            if self.crossed(c0 + d["cut"] * 0.95):
                self.hit(t, "soft_bell", s.note(k, 0), 0.2, self.stack_x, G - 140)
        # glass
        for q, gt in enumerate(self.glows):
            if self.crossed(gt):
                self.hit(t, "bloop", s.note(q, 0), 0.35, *self._glow_target(q))
                self.hit(t + 0.03, "chime", s.note(q + 2, 1 if q < 12 else 0), 0.22, *self._glow_target(q))
        if self.crossed(T["gather"] + 1.0):
            for q, kind in enumerate(("wheels", "springs", "teeth", "lantern")):
                self.say(t + q * 0.3, kind, "up", 6800, G - 300, 0.3)
        for i, p in enumerate(self.places):
            if self.crossed(p + 0.6):
                self.hit(t, "clunk", s.note(i, -1), 0.35, self.pumps[i], self.table_y)
        # the line at the table
        for i, pt in enumerate(self.ptimes):
            x = self.pumps[i]
            if self.crossed(pt["dig"]):
                self.fx(t, "slide", (pt["stem"] - pt["dig"]) * 0.8, 0.25, x, self.table_y)
            if self.crossed(pt["stem"] + 0.3):
                self.hit(t, "clack", s.note(i, 0), 0.35, x, self.table_y - 90)
            if self.crossed(pt["ribs"]):
                self.fx(t, "saw", (pt["face"] - pt["ribs"]) + (1.6 if i == 0 else 0.7), 0.22, x, self.table_y - 60)
            carve_d = 1.6 if i == 0 else 0.7
            for q in range(5):
                if self.crossed(pt["face"] + carve_d * q / 5):
                    self.hit(t, "clack", s.note(q + i, 1), 0.2, x, self.table_y - 60)
            if self.crossed(pt["lit"] - 0.2):
                self.hit(t, "bloop", s.note(i, 0), 0.4, x, self.table_y - 60)
                self.hit(t + 0.05, "chime", s.note(i, 0), 0.4, x, self.table_y - 60)
        if self.crossed(T["reveal"] + 0.4):
            # the board lights up: a rising Halloween arpeggio, then everyone cheers
            for q, n in enumerate((57, 60, 64, 69, 72, 76)):
                self.hit(t + q * 0.33, "soft_bell", n, 0.5, self.sign[0], self.sign[1])
            for q, kind in enumerate(("springs", "wheels", "teeth", "digger", "tentacles", "lantern")):
                self.say(t + 2.3 + q * 0.18, kind, "cheer", self.pumps[0] + 200, G - 300, 0.5)
        for i, b in enumerate(self.bats):
            if self.crossed(b + 0.6):
                self.hit(t, "clack", s.note(i, 0), 0.3, self._hang_x("bat", i), self.railB[2])
            if self.crossed(b + self.d["bat"] * 0.7):
                self.fx(t, "whoosh", 0.4, 0.25, self._hang_x("bat", i), self.railB[2])
                self.hit(t, "pluck", s.note(i + 3, 0), 0.3, self._hang_x("bat", i), self.railB[2])
        for i, g in enumerate(self.ghosts):
            if self.crossed(g + 0.9):
                self.fx(t, "rustle", 0.8, 0.3, self._hang_x("ghost", i), self.railB[2])
            if self.crossed(g + 1.6):
                self.hit(t, "clack", s.note(i, 1), 0.25, self._hang_x("ghost", i), self.railB[2])
            if self.crossed(g + 2.1):
                self.hit(t, "clack", s.note(i + 2, 1), 0.25, self._hang_x("ghost", i), self.railB[2])
                self.say(t + 0.3, "lantern", "hum", self._hang_x("ghost", i), self.railB[2], 0.3)
        for q in range(12):
            if self.crossed(T["lights"] + 4.8 + q * 0.12):
                self.hit(t, "chime", TUNE_HALLOWEEN[q % 8], 0.25, self.sign[0] + (q - 6) * 100, self.sign[1] + 120)
        if self.crossed(T["hero"] + 0.3):
            for q, kind in enumerate(("springs", "wheels", "teeth", "digger", "tentacles", "lantern")):
                self.say(t + q * 0.2, kind, "cheer", 7600, G - 300, 0.45)

    def _landing_time(self, j):
        """When big ball j lands in the wagon (solved once, cached)."""
        if not hasattr(self, "_land"):
            self._land = {}
            T = self.T
            for jj in range(8):
                tt = T["adv2"]
                prev = "belt"
                while tt < T["belt_end"] + 2:
                    st = self.ball_on_belt(jj, tt)[4]
                    if st == "wagon" and prev != "wagon":
                        self._land[jj] = tt
                        break
                    prev = st
                    tt += 1 / 60
        return self._land.get(j)

    # ------------------------------------------------------------------ drawing

    def draw(self, c, t):
        s, T, G = self.s, self.T, self.G
        self._hall(c, t)
        self._sign(c, t)
        self._forge_back(c, t)
        self._press(c, t)
        self._lathe(c, t)
        self._belt(c, t, back=True)
        self._cloth(c, t)
        self._glass(c, t)
        self._tables(c, t)
        self._rail(c, t)
        self._wagon(c, t)
        # Hans works from behind the belt while sanding
        behind = ["tentacles"] if T["lathe_end"] - 0.8 <= t < T["adv2"] + self.d["advance"] + 1.0 else []
        if behind:
            self.draw_monsters(c, t, kinds=behind, before=self._carried)
            self._belt(c, t, back=False)
            self.draw_monsters(c, t, kinds=[k for k in self.poses if k not in behind], before=self._carried)
        else:
            self._belt(c, t, back=False)
            self.draw_monsters(c, t, before=self._carried)
        self._front(c, t)

    # ----- hall -----

    def _hall(self, c, t):
        s, G = self.s, self.G
        vx0, vx1, vy0, vy1 = s.view()
        L, R = vx0 - 200, vx1 + 200
        top = self.ceil
        rect(c, L, top - 400, R, G, INTERIOR)
        lit = [smoothstep(seg(t, 0.8 + k * 0.45, 1.0 + k * 0.45)) for k in range(6)]
        off = s.cam_x * 0.3
        for gx in np.arange(math.floor((L - off) / 340) * 340 + off, R, 340):
            rect(c, gx, top, gx + 28, G, FAR)
        for gy in (top + 140, top + 560, G - 430):
            c.line(L, gy, R, gy, FAR, 9)
        rect(c, L, top, R, top + 40, MID)
        rect(c, L, top + 64, R, top + 86, MID)
        for lx in np.arange(math.floor(L / 700) * 700 + 350, R, 700):
            bank = min(5, max(0, int(lx // 1600)))
            a = lit[bank]
            c.line(lx, top + 40, lx, top + 230, CABLE, 3)
            c.polygon([(lx - 42, top + 262), (lx + 42, top + 262), (lx + 22, top + 230), (lx - 22, top + 230)], STEEL)
            if a > 0:
                s.glow_draw(lambda g, lx=lx, a=a: (g.circle(lx, top + 266, 20, LAMP * 0.7 * a),
                                                   g.polygon([(lx - 42, top + 266), (lx + 42, top + 266), (lx + 230, G),
                                                              (lx - 230, G)], LAMP * 0.035 * a)))
        rect(c, L, G, R, G + 600, FLOOR)
        c.line(L, G, R, G, lighten(FLOOR, 1.9), 2)
        # the inside of the cliff door they came in through
        if L < self.door_x + 200:
            rect(c, self.door_x - 180, G - 540, self.door_x + 120, G, INTERIOR * 0.5)
            machine_block(c, self.door_x - 200, G - 580, self.door_x + 140, G - 540, STEEL)
            rect(c, self.door_x - 200, G - 540, self.door_x - 180, G, STEEL * 0.8)
            rect(c, self.door_x + 120, G - 540, self.door_x + 140, G, STEEL * 0.8)

    def _sign(self, c, t):
        s = self.s
        sx, sy, w, h = self.sign
        if not s.visible(sx - w / 2, sx + w / 2):
            return
        for k in (-w / 3, w / 3):
            c.line(sx + k, self.ceil + 40, sx + k, sy - h / 2, CABLE, 3)
        machine_block(c, sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2, IRON * 0.8)
        c.polyline([(sx - w / 2, sy - h / 2), (sx + w / 2, sy - h / 2), (sx + w / 2, sy + h / 2), (sx - w / 2, sy + h / 2)],
                   STEEL, 4, closed=True)
        text = "HAPPY HALLOWEEN"
        a = self.sign_amount(t)
        n_on = a * len(text.replace(" ", ""))
        size = 104
        # letters light one by one, left to right; unlit there's nothing to read. Spaced by the font's own widths.
        widths = [w_ / size for w_ in _glyph_widths(text, size)]
        tot = sum(widths) * size
        x = sx - tot / 2
        k = 0
        for ch, wd in zip(text, widths):
            cx = x + wd * size / 2
            x += wd * size
            if ch == " ":
                continue
            on = float(np.clip(n_on - k, 0, 1))
            k += 1
            if on <= 0:                                      # unlit: nothing to read yet
                c.circle(cx, sy, 5, IRON * 1.3)
                continue
            col = IRON * 0.8 * (1 - on) + SIGN_ORANGE * on
            flick = 0.85 + 0.15 * math.sin(t * 7 + k)
            c.text(ch, cx, sy + 4, size, col * (flick if on > 0.99 else 1.0))
            if on > 0:
                s.glow_draw(lambda g, cx=cx, on=on: g.circle(cx, sy, 60, SIGN_ORANGE * 0.22 * on))

    # ----- forge -----

    def _forge_back(self, c, t):
        s, G, T = self.s, self.G, self.T
        if not s.visible(-100, self.moulds[-1] + 400):
            return
        fx = self.furnace_x
        h = self.heat(t)
        # coal pile
        rs = np.random.default_rng(5)
        left = 1.0 - 0.12 * sum(1 for sh in self.shovels if t > sh + 0.6)
        for k in range(40):
            a = rs.uniform(0, math.pi)
            r = rs.uniform(0, 1) ** 0.6
            cx = self.coal_x + math.cos(a) * 130 * r
            cy = G - math.sin(a) * 110 * r * left - 10
            c.circle(cx, cy, rs.uniform(12, 20), COAL * rs.uniform(0.8, 1.3))
        # gantry rail for the crucible
        rect(c, fx - 120, self.trolley_y - 14, self.moulds[-1] + 160, self.trolley_y + 6, STEEL)
        for px in (fx - 100, self.moulds[-1] + 140):
            rect(c, px - 12, self.ceil + 40, px + 12, self.trolley_y - 14, STEEL * 0.8)
        # crucible (behind the furnace while it's inside)
        self._crucible(c, t)
        # furnace: brick body, chimney, glowing mouth
        x0, x1, top = fx - 150, fx + 150, G - 600
        rect(c, fx - 60, self.ceil + 40, fx + 60, top - 30, BRICK_DARK)
        rect(c, x0, top, x1, G, BRICK)
        for row, yy in enumerate(np.arange(top + 30, G, 34)):
            c.line(x0, yy, x1, yy, BRICK_DARK, 2)
            for bx in np.arange(x0 + (row % 2) * 30, x1, 60):
                c.line(bx, yy - 34, bx, yy, BRICK_DARK, 2)
        machine_block(c, x0 - 14, top - 30, x1 + 14, top, IRON)
        mouth = ellipse(fx, self.mouth_y, 90, 80, 30, math.pi, 2 * math.pi) + [(fx + 90, G - 30), (fx - 90, G - 30)]
        fl = 0.85 + 0.15 * math.sin(t * 11) * math.sin(t * 7.3)
        c.polygon(mouth, FIRE * (0.25 + 0.6 * h) * fl)
        c.polyline(mouth, BRICK_DARK, 6, closed=True)
        for k in range(5):                                   # flames
            ph = t * 3 + k * 1.7
            fx_ = fx - 60 + k * 30
            fh = (40 + 50 * h) * (0.7 + 0.3 * math.sin(ph))
            c.polygon([(fx_ - 16, G - 32), (fx_ + 16, G - 32), (fx_ + 4 * math.sin(ph), G - 32 - fh)],
                      lighten(FIRE, 1.2) * (0.4 + 0.6 * h))
        s.glow_draw(lambda g: (g.polygon(mouth, FIRE * 0.3 * h * fl),
                               g.polygon([(fx - 90, G - 30), (fx + 90, G - 30), (fx + 260, G + 4), (fx - 260, G + 4)],
                                         FIRE * 0.12 * h)))
        # bench with the six moulds
        b0, b1 = self.moulds[0] - 90, self.moulds[-1] + 90
        rect(c, b0, self.bench_y, b1, self.bench_y + 26, IRON)
        for lx in (b0 + 20, b1 - 40):
            rect(c, lx, self.bench_y + 26, lx + 20, G, IRON * 0.8)
        for i, mx in enumerate(self.moulds):
            self._mould(c, i, mx, t)
        self._tote(c, t)
        self._pour_stream(c, t)

    def _crucible(self, c, t):
        x, chain, tilt = self.trolley(t)
        s = self.s
        rect(c, x - 36, self.trolley_y - 30, x + 36, self.trolley_y + 4, IRON)
        for wx in (x - 20, x + 20):
            c.circle(wx, self.trolley_y - 12, 10, STEEL * 1.3)
        cy = self.trolley_y + chain
        c.line(x - 30, self.trolley_y + 4, x - 46, cy, CABLE, 3)
        c.line(x + 30, self.trolley_y + 4, x + 46, cy, CABLE, 3)
        cc = Xform(c, ang=tilt * 1.05, px=x, py=cy + 50)
        body = [(x - 50, cy), (x + 50, cy), (x + 70, cy - 6), (x + 42, cy + 100), (x - 42, cy + 100)]
        cc.polygon(body, IRON * 0.9)
        cc.polyline(body, STEEL * 1.4, 3, closed=True)
        full = 1.0 - (sum(seg(t, p + 0.5, p + 2.1) for p in self.pours) / 6.0) * 0.85
        T = self.T
        hot = 1.0 if t < T["pour_end"] + 1.0 else max(0.0, 1 - (t - T["pour_end"] - 1.0) / 6)
        if t >= self.T["lift"] - 0.5 and hot > 0:
            surf = cy + 14 + 70 * (1 - full)
            cc.polygon([(x - 46, surf), (x + 46, surf), (x + 42, surf + 8), (x - 42, surf + 8)], molten(0.85 * hot))
            s.glow_draw(lambda g: Xform(g, ang=tilt * 1.05, px=x, py=cy + 50).polygon(
                [(x - 50, surf - 16), (x + 50, surf - 16), (x + 44, surf + 16), (x - 44, surf + 16)],
                molten(0.8) * 0.28 * hot))
        cc.line(x - 62, cy + 10, x - 50, cy + 10, STEEL * 1.3, 8)          # pour handle (Hans holds it)

    def _lip(self, t):
        x, chain, tilt = self.trolley(t)
        cy = self.trolley_y + chain
        a = tilt * 1.05
        lx, ly = x + 70, cy - 6
        px, py = x, cy + 50
        c_, s_ = math.cos(a), math.sin(a)
        return px + (lx - px) * c_ - (ly - py) * s_, py + (lx - px) * s_ + (ly - py) * c_

    def _pour_stream(self, c, t):
        x, chain, tilt = self.trolley(t)
        if tilt < 0.55 or not (self.T["to_mould"] < t < self.T["pour_end"] + 0.5):
            return
        lx, ly = self._lip(t)
        i = min(5, max(0, int((t - self.pours[0]) / (self.d["pour"] + self.d["pour_move"]))))
        tx, ty = self.moulds[i], self.bench_y - 22
        w = 9 * smoothstep((tilt - 0.55) / 0.3)
        pts = []
        for u in np.linspace(0, 1, 14):
            # leaves the lip sideways and falls under gravity: x eases, y accelerates
            pts.append((lerp(lx, tx, 1 - (1 - u) ** 2), lerp(ly, ty, u * u)))
        col = molten(0.88)
        c.polyline(pts, col, w)
        self.s.glow_draw(lambda g: g.polyline(pts, molten(0.8) * 0.45, w * 2.2))

    def _mould(self, c, i, mx, t):
        """A mould tray on the bench, seen a little from above: two wing cavities and a body cavity."""
        y = self.bench_y
        top = [(mx - 58, y - 30), (mx + 58, y - 30), (mx + 64, y), (mx - 64, y)]
        c.polygon(top, IRON * 1.15)
        c.polyline(top, STEEL * 1.2, 2, closed=True)
        rect(c, mx - 64, y, mx + 64, y + 4, IRON * 0.7)
        temp = self.mould_temp(i, t)
        fill = self.mould_fill(i, t)
        for side in (-1, 1):
            pts = np.asarray(D.wing_points(mx + side * 4 - side * 40, y - 15, 0.42, side, 0.0))
            cy = pts[:, 1].mean()
            pts[:, 1] = cy + (pts[:, 1] - cy) * 0.36
            pts[:, 0] = mx + side * 30 + (pts[:, 0] - pts[:, 0].mean()) * 0.9
            col = IRON * 0.45
            if temp is not None and fill > 0:
                col = molten(0.15 + 0.85 * temp) if temp > 0.05 else D.IRON_BAT
            c.polygon(pts, col if temp is not None else IRON * 0.45)
            if temp is not None and temp > 0.25:
                self.s.glow_draw(lambda g, pts=pts, temp=temp: g.polygon(pts, molten(temp) * 0.5 * temp))
        body = ellipse(mx, y - 15, 9, 6, 16)
        bcol = molten(0.15 + 0.85 * temp) if (temp is not None and fill > 0 and temp > 0.05) else (
            D.IRON_BAT if temp is not None and fill > 0 else IRON * 0.45)
        c.polygon(body, bcol)

    def _tote(self, c, t):
        T, G = self.T, self.G
        if t >= T["press_end"] + 30:
            return
        x = self.tote_x(t)
        rect(c, x - 70, G - 150, x + 70, G - 40, BIN)
        c.polyline([(x - 70, G - 150), (x + 70, G - 150), (x + 70, G - 40), (x - 70, G - 40)], BIN * 1.5, 3, closed=True)
        rect(c, x - 82, G - 158, x - 60, G - 140, BIN * 1.3)                # handle
        for wx in (x - 44, x + 44):
            c.circle(wx, G - 20, 20, IRON * 0.6)
            c.circle(wx, G - 20, 7, STEEL * 1.5)
        # castings inside: their tips poke out above the rim
        n_in = sum(1 for u0 in self.unloads if t >= u0 + self.d["unload"] * 0.8)
        taken = sum(1 for k, st in enumerate(self.stamps) if t >= st - 0.6)
        left = max(0, n_in * 2 - taken)
        for q in range(min(left, 9)):
            px = x - 48 + (q % 5) * 24
            c.polygon([(px - 14, G - 150), (px + 14, G - 150), (px + 4, G - 168 - (q % 3) * 6)], D.IRON_BAT)
            c.line(px - 14, G - 150, px + 4, G - 168 - (q % 3) * 6, D.IRON_EDGE, 2)

    # ----- press -----

    def _press(self, c, t):
        s, G, T = self.s, self.G, self.T
        x = self.press_x
        if not s.visible(x - 500, x + 500):
            return
        ry = self.ram_top(t)
        # columns, base, anvil
        for cx in (x - 130, x + 130):
            rect(c, cx - 16, G - 760, cx + 16, G, STEEL)
            c.line(cx - 16, G - 760, cx - 16, G, lighten(STEEL, 1.4), 2)
        machine_block(c, x - 170, G - 120, x + 170, G, IRON)
        machine_block(c, x - 90, self.anvil_y, x + 90, G - 120, STEEL * 1.2)
        # ram: top plate (Springs lands here), body, coil springs that push it back up, the die below
        die = ry + 220
        machine_block(c, x - 110, ry, x + 110, ry + 30, HAZARD * 0.8)
        rect(c, x - 70, ry + 30, x + 70, die - 20, IRON * 1.1)
        machine_block(c, x - 86, die - 20, x + 86, die, STEEL * 1.3)
        for cx in (x - 100, x + 100):                        # return springs between ram plate and base
            n = 8
            pts = [(cx + (14 if q % 2 else -14), lerp(ry + 30, G - 120, q / n)) for q in range(n + 1)]
            c.polyline(pts, CABLE * 1.3, 4)
        # the part on the anvil: blank (smooth crescent) until the die comes down, then scalloped
        k = self._stamp_index(t)
        if k is not None:
            st = self.stamps[k]
            scal = 1.0 if t >= st + 0.03 else 0.0
            if t < st + 0.35:
                D.wing_blank(c, x, self.anvil_y - 4, 0.75, 1, scallop=scal)
            else:
                u = seg(t, st + 0.35, st + 0.65)          # pushed off into the bin
                if u < 1:
                    D.wing_blank(c, lerp(x, self.bin_x, u), self.anvil_y - 4 + 120 * u * u, 0.75, 1, scallop=1.0)
        fp = self._feed_point(t)
        if fp is not None:
            D.wing_blank(c, fp[0], fp[1] + 6, 0.75, 1, scallop=0.0)
        # bin
        bx = self.bin_x
        rect(c, bx - 80, G - 130, bx + 80, G, BIN)
        c.polyline([(bx - 80, G - 130), (bx + 80, G - 130), (bx + 80, G), (bx - 80, G)], BIN * 1.5, 3, closed=True)
        n_in = sum(1 for st in self.stamps if t >= st + 0.65)
        if t < T["press_end"] + 3.4:
            for q in range(min(n_in, 6)):
                px = bx - 56 + q * 22
                c.polygon([(px - 12, G - 130), (px + 12, G - 130), (px + 2, G - 150 - (q % 2) * 6)], D.IRON_BAT)

    def _stamp_index(self, t):
        """Which stamp's blank is on the anvil now (from the moment Hans lets go of it until it's pushed off)."""
        for k, st in enumerate(self.stamps):
            if st - 0.02 <= t < st + 0.65:
                return k
        return None

    # ----- lathe + belt -----

    def _lathe(self, c, t):
        s, G = self.s, self.G
        x, y = self.lathe_x, self.spindle_y
        if not s.visible(x - 500, x + 500):
            return
        # stand + headstock on the right; the chuck grips the work from the right, the spindle turns it
        rect(c, x + 150, G - 170, x + 190, G, IRON * 0.9)
        machine_block(c, x + 70, y - 95, x + 200, G - 170, STEEL * 1.2)
        c.circle(x + 135, y - 40, 14, CABLE * 1.5)
        busy = any(st + D_ * 0.3 <= t < st + D_ * 0.84 for st, D_ in self.cycles)
        spin = t * 18 if busy else 0.0
        for q in range(3):                                   # chuck jaws, turning
            ph = spin + q * 2 * math.pi / 3
            jy = y + 34 * math.sin(ph)
            if math.cos(ph) > -0.2:
                rect(c, x + 46, jy - 7, x + 70, jy + 7, STEEL * (1.2 + 0.4 * math.cos(ph)))
        rect(c, x + 60, y - 46, x + 72, y + 46, STEEL * 1.5)
        # the ramp under the chuck down to the belt
        c.line(x - 30, G - 150, self.slot0, self.belt_y, CABLE * 1.3, 6)
        c.line(x - 30, G - 150, x - 30, G - 178, CABLE * 1.3, 5)
        for lx in (x - 10, x + 120):
            c.line(lx, lerp(G - 150, self.belt_y, (lx - x + 30) / (self.slot0 - x + 30)) + 3, lx, G, CABLE, 4)
        # pallet of blocks
        n_left = 8 - sum(1 for s_, D_ in self.cycles if t >= s_ + D_ * 0.06)
        px = self.pallet_x
        rect(c, px - 60, G - 20, px + 60, G, PLANK * 0.6)
        for q in range(n_left):
            col_, row = q % 2, q // 2
            D.wood_block(c, px - 26 + col_ * 52, G - 20 - row * 52, 26, 0.0)
        # the work in the chuck
        for j, (st, D_) in enumerate(self.cycles):
            if st + D_ * 0.3 <= t < st + D_ * 0.84:
                u = smoothstep(seg(t, st + D_ * 0.36, st + D_ * 0.8))
                r = lerp(36, self.big_r, u)
                D.wood_block(c, x, y + r, r, u)
                # spinning: highlight lines sweep across the face as it turns
                if t < st + D_ * 0.8:
                    for q in range(3):
                        ph = ((t * 6 + q / 3) % 1.0)
                        lx = x - r + 2 * r * ph
                        hh = r * math.sqrt(max(0.0, 1 - ((lx - x) / r) ** 2)) * 0.9
                        c.line(lx, y - hh, lx, y + hh, lighten(D.WOOD, 1.15), 2)
                # the cutting tool comes in from above on its post
                tin = smoothstep(seg(t, st + D_ * 0.34, st + D_ * 0.42)) * (1 - smoothstep(seg(t, st + D_ * 0.78, st + D_ * 0.82)))
                ty = lerp(y - r - 70, y - r + 4, tin)
                c.line(x + 10, ty - 120, x + 10, ty, STEEL * 1.4, 12)
                c.polygon([(x + 4, ty), (x + 16, ty), (x + 10, ty + 12)], lighten(STEEL, 2.2))
        # finished balls rolling down the ramp
        for j, (st, D_) in enumerate(self.cycles):
            if st + D_ * 0.84 <= t < st + D_ * 0.92:
                bx, byb, sanded, paint, _ = self.ball_on_belt(j, t)
                D.pumpkin(c, bx, byb, self.big_r, paint=0.0, sanded=0.35)

    def _belt(self, c, t, back):
        s, G, T = self.s, self.G, self.T
        x0, x1, y = self.slot0 - 60, self.belt_end, self.belt_y
        if not s.visible(x0 - 100, x1 + 300):
            return
        if back:
            rect(c, x0, y, x1, y + 26, IRON)
            c.line(x0, y, x1, y, lighten(IRON, 1.6), 2)
            roll = self.belt_shift(t) * self.pitch * 0.08
            for rx_ in np.arange(x0 + 20, x1, 46):
                c.circle(rx_, y + 13, 9, STEEL)
                c.line(rx_, y + 13, rx_ + 8 * math.cos(roll), y + 13 + 8 * math.sin(roll), STEEL * 0.6, 2)
            for lx in np.arange(x0 + 40, x1, 400):
                rect(c, lx, y + 26, lx + 18, G, IRON * 0.8)
            # Hans' step behind the sanding stretch
            hx = self.hans_sand_x
            machine_block(c, hx - 170, G - 150, hx + 170, G, IRON * 0.85)
            for k in range(3):
                c.line(hx - 160, G - 110 + k * 40, hx + 160, G - 110 + k * 40, IRON * 0.65, 2)
            # booth back wall
            b0, b1 = self.booth
            rect(c, b0, G - 420, b1, y, np.array([40, 34, 30]))
            for k in range(5):
                c.circle(lerp(b0 + 40, b1 - 40, k / 4), G - 380, 10, STEEL * 1.3)
            return
        # balls
        for j in range(8):
            st, D_ = self.cycles[j]
            if t < st + D_ * 0.92:
                continue
            x, yb, sanded, paint, state = self.ball_on_belt(j, t)
            if state == "wagon" and t >= T["gather"] - 0.5 and False:
                continue
            if state in ("belt", "fall") and s.visible(x - 100, x + 100):
                D.pumpkin(c, x, yb, self.big_r, paint=paint, ribs=0.0, stem=0.0, sanded=sanded)
        # booth front: walls with a window, the balls show through the window
        b0, b1 = self.booth
        rect(c, b0, G - 440, b1, G - 400, np.array([60, 52, 44]))
        rect(c, b0 - 10, G - 440, b0 + 30, y, np.array([60, 52, 44]))
        rect(c, b1 - 30, G - 440, b1 + 10, y, np.array([60, 52, 44]))
        c.text("PAINT", (b0 + b1) / 2, G - 420, 26, SIGN_WARM * 0.7)
        if T["adv1"] < t < T["belt_end"]:
            for k in range(3):
                nx = lerp(b0 + 60, b1 - 60, k / 2)
                c.polygon([(nx - 10, G - 400), (nx + 10, G - 400), (nx + 34, G - 300), (nx - 34, G - 300)],
                          D.ORANGE * 0.35)

    def _wagon(self, c, t):
        s, G, T = self.s, self.G, self.T
        wx = self.wagon_pos(t)
        if not s.visible(wx - 200, wx + 200):
            return
        m = self.m("wheels")
        if T["gather"] - 0.5 <= t and m is not None:
            c.line(wx + 70, G - 40, m.x - 60, G - 40, CABLE * 1.5, 5)
        # balls already in the wagon (behind the side board)
        for j in range(8):
            st, D_ = self.cycles[j]
            if t < st + D_ * 0.92:
                continue
            x, yb, sanded, paint, state = self.ball_on_belt(j, t)
            if state != "wagon":
                continue
            if any(t >= p for p in [self.places[j]]):
                continue
            ox, oy = self.wagon_slot(j, t)
            D.pumpkin(c, ox, oy, self.big_r, paint=1.0, ribs=0.0, stem=0.0)
        rect(c, wx - 110, G - 96, wx + 110, G - 34, PLANK * 0.75)
        c.line(wx - 110, G - 96, wx + 110, G - 96, PLANK, 3)
        for wxx in (wx - 70, wx + 70):
            c.circle(wxx, G - 24, 24, np.array([30, 30, 34]))
            c.circle(wxx, G - 24, 9, STEEL * 1.8)

    # ----- cloth + glass -----

    def _cloth(self, c, t):
        s, G = self.s, self.G
        x, top = self.sheet_x, self.sheet_top
        if not s.visible(x - 400, self.stack_x + 200):
            return
        for px in (x - 190, x + 190):
            rect(c, px - 10, top - 60, px + 10, G, STEEL)
        rect(c, x - 190, top - 70, x + 190, top - 50, STEEL * 1.2)
        c.circle(x, top - 30, 34, CLOTH * 0.9)                        # the roll
        c.circle(x, top - 30, 10, STEEL)
        # the sheet scrolls down a little before each cut
        scroll = sum(160 * smootherstep(seg(t, c0 - 0.9, c0 - 0.1)) for c0 in self.cuts)
        rect(c, x - 165, top - 4, x + 165, G - 70, CLOTH)
        for fx_ in (-110, -40, 50, 120):
            c.line(x + fx_, top, x + fx_ * 1.03, G - 70, D.CLOTH_SHADE, 2)
        c.line(x - 165, G - 70, x + 165, G - 70, D.CLOTH_SHADE * 0.8, 3)
        cx, cy = self.cut_c
        for k, c0 in enumerate(self.cuts):
            u = seg(t, c0 + self.d["cut"] * 0.15, c0 + self.d["cut"] * 0.75)
            if u <= 0:
                continue
            own = sum(160 * smootherstep(seg(t, cc - 0.9, cc - 0.1)) for cc in self.cuts[k + 1:])
            hy = cy + own
            if u < 1:
                a0 = -math.pi / 2
                pts = [(cx + math.cos(a0 + a) * 80, hy + math.sin(a0 + a) * 80) for a in np.linspace(0, u * 2 * math.pi, 40)]
                c.polyline(pts, D.CLOTH_SHADE * 0.6, 3)
                continue
            if hy < G - 90:                                           # the hole left in the sheet
                c.polygon(ellipse(cx, hy, 80, 80, 40), INTERIOR * 1.2)
                c.polyline(ellipse(cx, hy, 80, 80, 40), D.CLOTH_SHADE, 2, closed=True)
            # the disc falls: tips from upright to flat as it flutters down onto the stack
            f = seg(t, c0 + self.d["cut"] * 0.75, c0 + self.d["cut"] * 0.98)
            if f < 1:
                fy = lerp(hy, self.G - 140 - k * 6, f * f)
                fxp = lerp(cx, self.stack_x, smoothstep(f)) + 18 * math.sin(f * 9)
                c.polygon(ellipse(fxp, fy, 80, lerp(80, 10, smoothstep(f)), 36), CLOTH)
                c.polyline(ellipse(fxp, fy, 80, lerp(80, 10, smoothstep(f)), 36), D.CLOTH_SHADE, 2, closed=True)
        # stack table
        rect(c, self.stack_x - 110, G - 140, self.stack_x + 110, G - 124, PLANK * 0.7)
        for lx in (self.stack_x - 100, self.stack_x + 86):
            rect(c, lx, G - 124, lx + 14, G, PLANK * 0.5)
        n = sum(1 for c0 in self.cuts if t >= c0 + self.d["cut"] * 0.98)
        if self.carry.get("teeth") is None:
            for k in range(n):
                D.cloth_disc(c, self.stack_x, G - 140 - k * 6, 1.05)

    def _glass(self, c, t):
        s, G = self.s, self.G
        (x0, y0), (x1, y1) = self.bulb_hooks
        if not s.visible(x0 - 200, x1 + 300):
            return
        for px in (x0, x1):
            rect(c, px - 8, y0 - 20, px + 8, G, STEEL)
        if t < self.glows[-1] + 0.6:
            on = [0.0] * 12
            for q in range(12):
                g = self.glows[q]
                on[q] = 0.3 + 0.7 * math.exp(-max(0.0, t - g) / 0.8) if t >= g else 0.0
            D.light_string(c, [(x0, y0), (x1, y1)], 12, 13, glow=s.glow, t=t, sag=0.06, bulbs_on=on)
        # frosted globes on a little shelf (ghost heads)
        rect(c, self.globe_x[0] - 60, self.globe_y, self.globe_x[-1] + 60, self.globe_y + 14, PLANK * 0.7)
        for lx in (self.globe_x[0] - 50, self.globe_x[-1] + 36):
            rect(c, lx, self.globe_y + 14, lx + 14, G, PLANK * 0.5)
        for q, gx in enumerate(self.globe_x):
            if t >= self.glows[-1] + 0.6:
                continue
            g = self.glows[12 + q]
            on = 0.35 + 0.65 * math.exp(-max(0.0, t - g) / 1.0) if t >= g else 0.0
            self._globe(c, gx, self.globe_y - 30, on)

    def _globe_small(self, c, x, y):
        c.circle(x, y, 13, GLOBE * 0.6)
        c.circle(x - 4, y - 4, 4, lighten(GLOBE, 1.3) * 0.6)

    def _globe(self, c, x, y, on):
        c.circle(x, y, 28, GLOBE * (0.35 + 0.55 * on))
        c.circle(x - 9, y - 9, 7, lighten(GLOBE, 1.3) * (0.5 + 0.5 * on))
        if on > 0:
            self.s.glow_draw(lambda g: g.circle(x, y, 60, GLOBE * 0.3 * on))

    # ----- the assembly area -----

    def _tables(self, c, t):
        s, G, T = self.s, self.G, self.T
        a0, a1 = self.tableA
        if not s.visible(a0 - 300, a1 + 300):
            return
        y = self.table_y
        rect(c, a0, y, a1, y + 22, PLANK * 0.8)
        c.line(a0, y, a1, y, PLANK, 3)
        for lx in np.arange(a0 + 20, a1, 300):
            rect(c, lx, y + 22, lx + 18, G, PLANK * 0.55)
        # candle box at the left end
        rect(c, a0 + 10, y - 40, a0 + 70, y, PLANK * 0.6)
        for i in range(8):
            st = self.pumpkin_state(i, t)
            if st is None:
                continue
            x, yb, paint, ribs, stem, carve, lit = st
            hollow = seg(t, self.ptimes[i]["dig"], self.ptimes[i]["stem"] - 0.2)
            D.pumpkin(c, x, yb, self.big_r, paint=1.0, ribs=ribs, stem=stem, carve=carve, lit=lit, t=t, glow=s.glow,
                      seed=i * 1.3, face=i % 2)
            if 0 < hollow < 1:                                # the lid is off while Digs hollows it out
                c.polygon(ellipse(x, yb - 2 * self.big_r * 0.95 + 8, 22, 7, 16), D.CARVED)

    def _rail(self, c, t):
        s, G, T = self.s, self.G, self.T
        r0, r1, ry = self.railB
        if not s.visible(r0 - 200, r1 + 200):
            return
        rect(c, r0, ry - 10, r1, ry, STEEL * 1.2)
        for px in (r0 + 10, r1 - 30):
            rect(c, px, ry, px + 20, G, STEEL)
        for i in range(6):
            x = self._hang_x("bat", i)
            wings, hung, flap = self.bat_state(i, t)
            if t < self.bats[i]:
                continue
            by = self.railB[2] + 90
            c.line(x, ry, x, by - 40, CABLE, 2)
            D.bat(c, x, by, 0.68, flap=flap, t=t, glow=s.glow, wings=wings, eyes=1.0 if hung else 0.0)
        for i in range(4):
            x = self._hang_x("ghost", i)
            g = self.ghosts[i]
            if t < self.globe_hang[i]:
                continue
            head = ry + 70
            c.line(x, ry, x, head - 28, CABLE, 2)
            drape = smoothstep(seg(t, g + 0.9, g + 1.4))
            eyes = 0.5 * smoothstep(seg(t, g + 1.6, g + 1.8)) + 0.5 * smoothstep(seg(t, g + 2.1, g + 2.3))
            on = 0.35 + 0.4 * smoothstep(seg(t, self.T["lights"] + 4.8, self.T["lights"] + 6.2))
            if drape <= 0:
                self._globe(c, x, head, on)
            else:
                sway = 0.3 * math.sin(t * 1.3 + i)
                D.ghost(c, x, head - 34 * 0.8, 0.8, drape=drape, eyes=eyes, t=t, seed=i, sway=sway, ball=False)
                if on > 0:
                    s.glow_draw(lambda gg, x=x, head=head, on=on: gg.circle(x, head + 30, 70, GLOBE * 0.18 * on))
        # left-behind things: the cloth stack on a crate, the coiled string, the bin of bat parts
        if T["gather"] + 3.5 <= t:
            rect(c, self.disc_x - 70, G - 90, self.disc_x + 70, G, PLANK * 0.6)
            n = 4 - sum(1 for g in self.ghosts if t >= g - 0.85)
            for k in range(n):
                D.cloth_disc(c, self.disc_x, G - 90 - k * 6, 0.8)
        if self.globe_hang[-1] + 2.0 <= t < T["lights"] + 0.9:
            for k in range(3):
                c.polyline(ellipse(self.coil_x, G - 22, 40 - k * 8, 14 - k * 3, 24), D.WIRE * 1.3, 3, closed=True)
            for q in range(5):
                D.bulb(c, self.coil_x - 30 + q * 15, G - 40, 8, D.BULB_COLORS[q % 2], 0.3)
        if T["press_end"] + 18.7 <= t:
            bx = self.bin_drop
            rect(c, bx - 70, G - 70, bx + 70, G, BIN)
            n_wings = 12 - sum(2 for b in self.bats if t >= b + 0.3)
            for q in range(max(0, min(5, n_wings // 2))):
                c.polygon([(bx - 50 + q * 24 - 10, G - 70), (bx - 50 + q * 24 + 10, G - 70), (bx - 50 + q * 24, G - 88)],
                          D.IRON_BAT)
        # the light string under the sign
        if t >= T["lights"] + 2.0:
            sx, sy, w, h = self.sign
            # Glo floats the string along under the board, hooking it on as she goes
            u = seg(t, T["lights"] + 2.0, T["lights"] + 4.5)
            hooks = [(sx - w / 2 + w * q / 4, sy + h / 2) for q in range(5)]
            n = max(2, 1 + int(u * 4 + 1e-6) + (1 if u < 1 else 0))
            hooks = hooks[:n]
            if u < 1:
                gx_ = sx - w / 2 + w * u
                hooks[-1] = (gx_, sy + h / 2 + 30)
            nb = 12 if u >= 1 else max(1, int(12 * u))
            on = [smoothstep(seg(t, T["lights"] + 4.8 + q * 0.12, T["lights"] + 5.0 + q * 0.12)) for q in range(nb)]
            D.light_string(c, hooks, nb, 13, glow=s.glow, t=t, sag=0.1, bulbs_on=on)

    # ----- what the Keepers are holding -----

    def _carried(self, kind):
        c, t, s = self.wcv_, self.t_, self.s
        m = self.m(kind)
        if kind == "tentacles" and self.T["unload"] <= t < self.T["push"]:
            # the castings of one mould in the tentacle's grip: two wing crescents and a little body
            k = min(5, int((t - self.T["unload"]) / self.d["unload"]))
            u = seg(t, self.unloads[k], self.unloads[k] + self.d["unload"] * 0.8)
            if 0 < u < 1:
                px, py = self._casting_carry(k, t)
                D.wing_blank(c, px - 4, py + 18, 0.5, -1)
                D.wing_blank(c, px + 4, py + 18, 0.5, 1)
                D.body_blank(c, px, py + 24, 0.45)
        what = self.carry.get(kind)
        if m is None or what is None:
            return
        dy = self.poses.get(kind, (0.0, 0.0))[0]
        if kind == "wheels":
            item, j, u = what
            hx, hy = claw_point(m, t, 1)
            if item == "block":
                st, D_ = self.cycles[j]
                f = smoothstep(seg(t, st + D_ * 0.22, st + D_ * 0.3))      # lifted up into the chuck
                bx, by = lerp(hx, self.lathe_x, f), lerp(hy + 30, self.spindle_y + 36, f)
                D.wood_block(c, bx, by, lerp(28, 36, f), 0.0)
            elif item == "ball":
                D.pumpkin(c, hx, hy + 40, self.big_r, paint=0.0, sanded=0.35)
            elif item == "stem":
                c.polygon([(hx - 6, hy), (hx + 6, hy), (hx + 8, hy - 20), (hx - 4, hy - 22)], D.STEM)
        elif kind == "digger":
            if what[0] == "coal":
                x = m.x + 118 * m.k + 56 * m.k
                y = m.y - 150 * m.k + (30 + 70 * m.dig) * m.k + dy
                for q in range(4):
                    c.circle(x + 14 + (q % 2) * 12, y + 18 - (q // 2) * 10, 8, COAL * 1.2)
        elif kind == "springs":
            top = m.y + dy - 330 * m.k
            x = m.x
            rect(c, x - 70, top - 70, x + 70, top, BIN)
            for q in range(5):
                c.polygon([(x - 50 + q * 24 - 10, top - 70), (x - 50 + q * 24 + 10, top - 70), (x - 50 + q * 24, top - 88)],
                          D.IRON_BAT)
            for sxp in (-1, 1):
                c.line(x + sxp * 50 * m.k, m.y + dy - 190 * m.k, x + sxp * 60, top - 4, m.color * 0.8, 10 * m.k)
        elif kind == "teeth":
            for q in range(4):
                D.cloth_disc(c, m.x, m.y + dy - 120 - q * 6, 0.8)
        elif kind == "lantern":
            lx, ly = m.x, m.y - (260 - 82) * m.k + 60
            if what[0] == "candle":
                D.candle(c, lx, ly + 40, 0.9, lit=1.0, t=t, glow=s.glow)
            elif what[0] == "disc":
                c.polygon(ellipse(lx, ly + 10, 80 * 0.8, 10, 30), CLOTH)
            elif what[0] in ("string", "string_end"):
                c.polyline([(lx - 40, ly), (lx, ly + 20), (lx + 40, ly)], D.WIRE, 3)
                for q, bx in enumerate((-30, -10, 10, 30)):
                    D.bulb(c, lx + bx, ly + 8 + (q % 2) * 6, 9, D.BULB_COLORS[q % 2], 0.3)
                for q in range(what[1] or 0):                      # globes still to hang
                    self._globe_small(c, lx - 45 + q * 30, ly + 60)

    def draw_monsters(self, c, t, kinds=None, before=None):
        self.wcv_, self.t_ = c, t
        super().draw_monsters(c, t, kinds, before)

    def _front(self, c, t):
        pass
