"""Tune-Up remake (ep 6): the hall act with the STORYBOOK BEACON at the end of the factory (old look).

Owner, FK0018 review (2026-11-06): "replace the storybook press with some kind of machine that sends out like a
shockwave that first changes the characters and the night shift factory and then you see it changing the whole
landscape". Everyone is awake and tuned up and heads for the way out. Glo floats on ahead to the beacon, the last
machine of the factory (past the end of the line, before the mirror), and flares his light at its glass eye: the eye
lights, the three copper coils light one by one up its column, the glass orb on top fills with light - and it pulses.
A ring of light rolls out from the orb (tune_flat.shockwave): inside the ring everything is the flat picture-book look,
first the Keepers by the beacon, then the whole factory. Outside, the same wave rolls out of the hill over the forest
and the village (HomeWaveAct), before the Keepers come out of the door. Both looks are drawn from the same frame, so
nothing jumps.

Glo changes things with a light flare, never a floating arm (owner rule); the machine visibly does each step.
"""
import math

import numpy as np

from families.foundry.keepers.common import lerp, seg, smoothstep
from families.foundry.style import CABLE, IRON, STEEL
from families.foundry.tree_monsters import LAMP, SIGN_WARM, machine_block, rect

from .tune_up import EXIT, FY, G, GLO_UP, HallAct, HomeAct, ORDER, Route, slot_x

PRESS_X = 7650.0                      # the beacon stands against the back wall, past the end of the line
PRESS_HW = 175.0                      # half its width (the control post on the left)
BED_Y = G - 170.0                     # the top of the beacon's base (Glo hovers just over its left end)
EYE = (PRESS_X - PRESS_HW, BED_Y - 125.0)   # the glass eye Glo lights (on the control post, beside him)
GLO_AT = PRESS_X - 100.0              # Glo hovers on the beacon, over the base's left end, while it works
GLO_LIFT = 200.0                      # from the walkway (y = G) up onto the beacon (just over the base)
HANS_WAIT = 7400.0                    # Hans waits here, behind Twigs, while Twigs looks in the mirror
ORB = (PRESS_X, G - 590.0)            # the glass orb on top: the wave starts here
ORB_R = 64.0
COIL_Y = (G - 262.0, G - 345.0, G - 428.0)
COIL_R = (74.0, 16.0)
T_FLARE = 319.6                       # (episode time) Glo's flare, before Twigs walks past
FLARE = 0.0                           # beats after the flare
COILS = (0.7, 1.15, 1.6)              # each coil lights
ORB_ON = (1.9, 2.5)                   # the orb fills with light
TURN0, TURN_DUR = 2.7, 3.6            # the pulse, and the wave rolling over the whole picture
WAVE_LEAD = 7.0                       # home: the wave rolls out over the landscape before anyone comes out


def press_beats(t_flare):
    return dict(flare=t_flare + FLARE, coils=[t_flare + c for c in COILS], orb=(t_flare + ORB_ON[0], t_flare +
                ORB_ON[1]), turn0=t_flare + TURN0, turn1=t_flare + TURN0 + TURN_DUR)


def press_state(t, b):
    """The beacon at local hall time t: eye 0..1 (lit), coils [0..1] x3 (lit, bottom up), orb 0..1 (full of light),
    pulse 0..1 (the flash as it sends the wave), hum 0..1 (it is running)."""
    eye = smoothstep(seg(t, b["flare"] + 0.15, b["flare"] + 0.55))
    coils = [smoothstep(seg(t, c, c + 0.3)) for c in b["coils"]]
    orb = smoothstep(seg(t, *b["orb"]))
    p0 = b["turn0"]
    pulse = smoothstep(seg(t, p0 - 0.15, p0 + 0.05)) * (1 - smoothstep(seg(t, p0 + 0.1, p0 + 1.2)))
    after = smoothstep(seg(t, p0 + 0.6, p0 + 2.5))                  # it settles to a soft glow
    k = 1 - 0.45 * after
    return dict(eye=eye, coils=[c * k for c in coils], orb=orb * (1 - 0.5 * after), pulse=pulse, hum=coils[0] * k)


def press_geometry(st=None):
    """Shapes of the beacon (world units), shared by the old look and the flat look."""
    x, hw = PRESS_X, PRESS_HW
    return dict(post=(x - hw - 22, G - 420.0, x - hw + 22, G), post_cap=(x - hw - 30, G - 436.0, x - hw + 30,
                                                                          G - 420.0),
                base=(x - 150.0, BED_Y, x + 150.0, G), base_top=(x - 160.0, BED_Y - 14, x + 160.0, BED_Y + 4),
                column=(x - 24.0, G - 530.0, x + 24.0, BED_Y - 14), collar=(x - 40.0, G - 548.0, x + 40.0, G - 526.0),
                sign=(x - 128.0, G - 128.0, x + 128.0, G - 74.0), eye=EYE, orb=ORB, coils=COIL_Y)


class HallSwitchAct(HallAct):
    """The hall act, with Glo heading on to the storybook press after the wake-up."""
    name = "hall"

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.t_flare = T_FLARE - t0
        self.beats = press_beats(self.t_flare)
        self._reroute()

    def _reroute(self):
        """Rebuild the walk to the way out (tune_up.HallAct.__init__). Nobody walks through anybody (owner rule, after
        this episode first aired): Twigs is ahead of Hans, so Twigs looks in the mirror first while Hans waits behind
        him, then Hans; Glo floats up onto the press (behind everyone) and comes down last, at the back of the queue."""
        self.exit_order = ["wheels", "springs", "digger", "teeth", "tentacles", "lantern"]
        # the queue for the door, spaced by body widths (nobody stands in anybody)
        self.queue_x = {"wheels": 9150.0, "springs": 8935.0, "digger": 8725.0, "teeth": 8515.0, "tentacles": 8255.0,
                        "lantern": 8010.0}
        x0 = {k: slot_x(15 - ORDER.index(k)) + 30 for k in ORDER}
        R = {k: Route(x0[k], 0.0).wait(self.ME + 0.25 * ORDER.index(k)) for k in ORDER}
        R["teeth"].go(self.mirror_spot, v=110)
        self.twigs_at_mirror = tm = R["teeth"].t
        R["teeth"].wait(tm + 3.4).go(self.queue_x["teeth"], v=130)
        R["tentacles"].go(HANS_WAIT, v=115).wait(tm + 3.4).go(self.mirror_spot, v=110)
        self.hans_at_mirror = hm = R["tentacles"].t
        R["tentacles"].wait(hm + 5.0).go(self.queue_x["tentacles"], v=130)
        self.glo_down = hm + 5.6                               # Hans walks on: Glo comes down off the press
        R["lantern"].go(GLO_AT, v=150).wait(self.glo_down + 1.4).go(self.queue_x["lantern"], v=130)
        for k in ("wheels", "springs", "digger"):
            R[k].go(self.queue_x[k], v=130)
        self.door = (hm + 1.0, hm + 4.0)
        self.exit_t, self.at_exit, last, last_door = {}, {}, self.door[1], -1e9
        for k in self.exit_order:
            walk = Route(self.queue_x[k]).go(self.way_out.xc, v=170).t
            last = self.exit_t[k] = max(last + 1.1, R[k].t + 0.5, last_door + 2.4 - walk)
            R[k].wait(last).go(self.way_out.xc, v=170)
            last_door = self.at_exit[k] = R[k].t
        self.out_route = R
        from .doorway import DEPTH_T
        self.gone = {k: self.at_exit[k] + DEPTH_T for k in ORDER}
        self.dur = max(self.gone.values()) + 1.5

    def glo_lift(self, t):
        """Glo floats up onto the press as everyone heads out, and down again once Hans has walked on."""
        up = smoothstep(seg(t, self.ME, self.ME + 2.4))
        down = smoothstep(seg(t, self.glo_down, self.glo_down + 1.4))
        return GLO_LIFT * up * (1 - down)

    def glo_back(self, t):
        """Glo is on the press (the back layer: the others walk past in front of him)."""
        return self.ME + 0.3 <= t < self.glo_down + 1.4

    def outside(self):
        out = super().outside()
        if self.glo_back(self._t):
            out = [k for k in out if k != "lantern"]
        return out

    def update(self, t, dt):
        super().update(t, dt)
        m = self.m("lantern")
        if m is not None and self.door_depth.get("lantern", 0.0) <= 0.0 and t >= self.down_t["lantern"]:
            m.y -= self.glo_lift(t)

    def flare(self, t):
        f = self.beats["flare"]
        return smoothstep(seg(t, f - 0.2, f + 0.2)) * (1 - smoothstep(seg(t, f + 0.6, f + 1.3)))

    def glo_light(self, c, k=1.0, ground=None):
        super().glo_light(c, k=k + 1.6 * self.flare(self._t), ground=ground)

    _t = 0.0

    def draw(self, c, t):
        self._t = t
        super().draw(c, t)

    def _sounds(self, t):
        super()._sounds(t)
        b = self.beats
        x, y = ORB
        if self.crossed(b["flare"] - 1.6):
            self.chat(b["flare"] - 1.6, "lantern", "ooh")
        if self.crossed(b["flare"] + 0.3):
            self.hit(b["flare"] + 0.3, "chime", 79, 0.10, EYE[0], EYE[1])
        for q, (ct, note) in enumerate(zip(b["coils"], (60, 64, 67))):     # each coil lights with a soft rising note
            if self.crossed(ct + 0.1):
                self.hit(ct + 0.1, "soft_bell", note, 0.09, x, COIL_Y[q])
        if self.crossed(b["coils"][0]):
            self.fx(b["coils"][0], "motor", b["turn0"] - b["coils"][0] + 0.4, 0.05, x, COIL_Y[1])   # a low hum
        if self.crossed(b["orb"][0]):
            self.hit(b["orb"][0], "sky_swell", 72, 0.10, x, y)
        if self.crossed(b["turn0"]):                                   # the pulse: a soft whoosh and a warm low bell
            self.fx(b["turn0"], "whoosh", 2.2, 0.16, x, y)
            self.hit(b["turn0"], "deep_bell", 48, 0.12, x, y)
            self.hit(b["turn0"] + 0.25, "soft_bell", 72, 0.08, x, y)
        if self.crossed(b["turn0"] + 1.4):
            self.hit(b["turn0"] + 1.4, "soft_bell", 79, 0.07, x, y)

    def _stations_back(self, c, t):
        super()._stations_back(c, t)
        if self.s.visible(PRESS_X - PRESS_HW - 120, PRESS_X + PRESS_HW + 120):
            draw_press_old(c, press_state(t, self.beats), t, self.s.glow_draw)
        if self.glo_back(t) and "lantern" in super().outside():
            self.draw_monsters(c, t, kinds=["lantern"])

    def target(self, t):
        """The old camera (it follows Hans to the mirror), drawn a little towards the press while it works."""
        x, y, z = super().target(t)
        f = self.beats["flare"]
        w = smoothstep(seg(t, f - 9.0, f - 1.0)) * (1 - smoothstep(seg(t, f + 5.0, f + 13.0)))
        return x + 260.0 * w, y, z

    def props(self, t):
        out = super().props(t)
        out["beacon orb"] = ORB
        return out


COPPER = np.array([184, 112, 64], np.float64)
GLASS = np.array([150, 176, 196], np.float64)


def _coil_old(c, y, lit, front):
    from families.foundry.products.monster import ellipse
    rx, ry = COIL_R
    a0, a1 = (0.0, math.pi) if front else (math.pi, 2 * math.pi)
    col = COPPER * (0.55 if not front else 0.8) * (1 - 0.3 * lit) + LAMP * 0.55 * lit
    c.polyline(ellipse(PRESS_X, y, rx, ry, 24, a0, a1), col, 9)


def draw_press_old(c, st, t, glow=None):
    """The STORYBOOK BEACON in the old look: control post with the glass eye, a riveted base with its sign, a steel
    column wound with three copper coils, a brass collar and the glass orb on top."""
    from families.foundry.products.monster import ellipse
    g = press_geometry()
    machine_block(c, *g["post"], STEEL * 0.92)
    machine_block(c, *g["post_cap"], STEEL * 1.1)
    for q, y in enumerate(COIL_Y):
        _coil_old(c, y, st["coils"][q], False)
    machine_block(c, *g["column"], STEEL * 1.05)
    for q, y in enumerate(COIL_Y):
        _coil_old(c, y, st["coils"][q], True)
    machine_block(c, *g["base"], STEEL * 0.85)
    machine_block(c, *g["base_top"], STEEL * 1.05)
    for rx in (-130, 130):
        for ry in (-140, -30):
            c.circle(PRESS_X + rx, G + ry, 4, STEEL * 1.5)
    rect(c, *g["sign"], IRON * 1.3)
    c.text("STORYBOOK BEACON", PRESS_X, (g["sign"][1] + g["sign"][3]) / 2, 20, SIGN_WARM * 0.85)
    machine_block(c, *g["collar"], np.array([170, 140, 80], np.float64))
    ox, oy = ORB
    o = st["orb"]
    c.circle(ox, oy, ORB_R + 6, IRON * 1.2)
    c.circle(ox, oy, ORB_R, GLASS * 0.45 * (1 - o) + LAMP * o)
    c.polygon(ellipse(ox - 20, oy - 24, 18, 12, 16), np.minimum(255, GLASS * 0.8 + LAMP * 0.4 * o))
    ex, ey = g["eye"]
    c.circle(ex, ey, 26, IRON * 1.2)
    c.circle(ex, ey, 19, IRON * 1.5 * (1 - st["eye"]) + LAMP * st["eye"])
    if st["eye"] > 0:
        c.circle(ex - 6, ey - 6, 5, LAMP * 0.4 * st["eye"] + np.array([255, 250, 230]) * 0.6 * st["eye"])
    if glow is not None:                                        # the light (bloom)
        lit = max(st["coils"] + [o, st["pulse"]])
        if lit > 0.01:
            def fn(gg):
                for q, y in enumerate(COIL_Y):
                    if st["coils"][q] > 0.01:
                        gg.polyline(ellipse(PRESS_X, y, COIL_R[0], COIL_R[1], 24), LAMP * 0.5 * st["coils"][q], 14)
                gg.circle(ox, oy, ORB_R * (1.3 + 1.5 * st["pulse"]), LAMP * (0.35 * o + 0.6 * st["pulse"]))
            glow(fn)


class HomeSwitchAct(HomeAct):
    """Home (flat look): the same walk home, with each Keeper's spot spaced by body widths (nobody stands in
    anybody: owner rule)."""
    SPOT = {"lantern": 2280.0, "wheels": 2500.0, "digger": 2780.0, "springs": 2990.0, "teeth": 3160.0,
            "tentacles": 3800.0}


WAVE_T0, WAVE_DUR = 2.2, 3.0           # home: the wave rolls out of the hill over the landscape (act time)
WAVE_FROM = (4570.0, G - 330.0)        # the factory inside the hill (behind the NIGHT SHIFT door)
DOOR_SHOT = (4800.0, 1.4)              # home: close on the door (it sits left of centre, they walk off the left edge)
HOUSE_SHOT = (3050.0, 1.13)            # home: the houses and every Keeper's spot, as they arrive


class HomeWaveAct(HomeSwitchAct):
    """Home, opening on the whole landscape at night, still in the old look: the beacon's wave rolls out of the hill
    over the forest and the village (tune_flat.shockwave, centred on the factory inside the hill), and only then do
    the Keepers come out of the door, into the storybook world. The same walk home as HomeSwitchAct, WAVE_LEAD later."""
    name = "home"

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        from .doorway import DEPTH_T
        L = WAVE_LEAD
        self.out = {k: 0.8 + L + 1.6 * q for q, k in enumerate(self.OUT_ORDER)}
        self.step = {k: self.out[k] + DEPTH_T for k in self.OUT_ORDER}
        self.walk_home = {k: Route(self.x_in, self.step[k]).go(self.SPOT[k], v=190) for k in self.OUT_ORDER}
        self.home = {k: self.walk_home[k].t for k in self.OUT_ORDER}
        self.hog_t = max(self.home["teeth"], self.home["tentacles"]) + 1.0
        self.bunny_t = self.hog_t + 4.5
        self.wave_t = self.bunny_t + 7.5
        self.dur = self.wave_t + 9.0
        self.wave = (WAVE_T0, WAVE_T0 + WAVE_DUR)
        self.camera_cuts = (self.out["lantern"] - 0.2,              # to the door, just before Glo comes out
                            self.step["tentacles"] + 3.7)           # to the houses, once Hans is off the door shot

    def target(self, t):
        """Owner 2026-11-06 (no long walks): "if they ever need to do more walking than that, you should change the
        angle or the crop or the zoom". The walk from the door to the houses is ~15 s for the cast, so it is two short
        shots with straight cuts (camera_cuts), nobody jumping: the wide landscape and its wave; a cut to close on the
        door, where each Keeper steps out and walks off the left edge in ~3 s; a cut to the houses as they arrive
        (each walks ~2-3 s into his spot). Then the original slow moves at home."""
        from .harvest_feast import cam_keys
        c0, c1 = self.camera_cuts
        keys = [(0.0, 3450.0, None, 0.62), (WAVE_T0 + WAVE_DUR + 0.3, 3450.0, None, 0.62), (c0, 3560.0, None, 0.66),
                (c0, DOOR_SHOT[0], None, DOOR_SHOT[1]), (c1, DOOR_SHOT[0] - 40.0, None, DOOR_SHOT[1] + 0.02),
                (c1, HOUSE_SHOT[0], None, HOUSE_SHOT[1]), (self.hog_t - 0.5, 3300.0, None, 1.08),
                (self.bunny_t + 4.0, 3500.0, None, 1.05), (self.wave_t, 3100.0, None, 0.85),
                (self.dur, 2900.0, None, 0.72)]
        return cam_keys(keys, t)

    def update(self, t, dt):
        super().update(t, dt)
        if self.crossed(WAVE_T0):
            x, y = WAVE_FROM
            self.fx(WAVE_T0, "whoosh", 2.8, 0.14, x, y)
            self.hit(WAVE_T0 + 0.1, "deep_bell", 45, 0.10, x, y)
            self.hit(WAVE_T0 + 0.6, "soft_bell", 76, 0.07, x - 800, y)
            self.hit(WAVE_T0 + 1.5, "soft_bell", 81, 0.06, x - 1600, y)
