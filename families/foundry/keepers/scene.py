"""Foundry engine - Forest Keepers (tree monsters episode 2, docs/engines/foundry_keepers.md).

A ~10 minute 16:9 episode in acts: the factory makes six monsters (harvest, belly dump, saws, vat,
an indexing assembly line, orbs, intense training), then three forest missions where the monsters
put the forest back (replant the clearing, build a bridge for the animals, build their treehouse and
light it up). Each act has its own world and camera; acts are joined by short fades to black.

    python -m engine.render families/foundry/params/keepers_long.yaml
"""
import math

import numpy as np

from audio import synth
from engine.scene import Scene as BaseScene

from ..products.monster import Monster, Xform
from ..style import BG, HeatGlow, Shifted
from .common import Particles, seg
from .factory import FactoryAct
from .forest import BridgeAct, ReplantAct, TreehouseAct
from .halloween import DecorateAct, HaulAct, ReturnAct
from .workshop import WorkshopAct

ACTS = {"factory": FactoryAct, "replant": ReplantAct, "bridge": BridgeAct, "treehouse": TreehouseAct,
        # episode 3, Halloween (docs/engines/foundry_keepers_halloween.md)
        "return": ReturnAct, "workshop": WorkshopAct, "haul": HaulAct, "decorate": DecorateAct}
# each monster's little voice: base note (MIDI) for the creature-voice instrument (engine/audio.py)
VOICE = {"wheels": 67, "tentacles": 55, "teeth": 50, "springs": 74, "lantern": 71, "digger": 60}


class Scene(BaseScene):
    reverb = {"decay": 3.0, "wet": 0.35, "tone": 3500}
    events_gain = 1.0
    ACTS = ACTS                     # the Forest Keepers engine (families/keepers) adds its own acts
    SCALE = synth.INDUSTRIAL_SCALE

    def __init__(self, params, seed, fmt, track):
        super().__init__(params, seed, fmt, track)
        P = self.p = params
        track.scale = self.SCALE
        self.v = P.get("visual", {})
        self.k = P.get("monster_scale", 0.55)
        self.monsters = [Monster(kd, self.k) for kd in Monster.KINDS[:P.get("monsters", 6)]]
        self.by_kind = {m.kind: m for m in self.monsters}
        for m in self.monsters:
            m.alive, m.orb_in = 0.0, 0.0
        self.particles = Particles(np.random.default_rng(seed + 5))
        self.acts, t = [], 0.0
        for name in P.get("acts", ["factory", "replant", "bridge", "treehouse"]):
            act = self.ACTS[name](self, P.get(name, {}), t)
            self.acts.append(act)
            t += act.dur
        self.end_t = t
        self.fade = P.get("fade", 0.8)
        self.prev_t, self._t = -1.0, 0.0
        self.cur = None
        self.cam_x = self.cam_y = 0.0
        self.cam_vx = self.cam_vy = 0.0
        self.zoom, self.zoom_v = 1.0, 0.0
        self.glow = self.scv = self.wcv = None
        fac = next((a for a in self.acts if a.name == "factory"), None)
        pulse = fac.pulse_window() if fac else None
        self.bed = {"type": "procedural", "name": "keepers", "gain": 1.0,
                    "pulse_from": pulse[0] if pulse else None, "pulse_to": pulse[1] if pulse else None,
                    "reverb": {"decay": 6.0, "wet": 0.5, "tone": 2200}}
        # outdoor stretches get the night-forest bed, indoor acts the factory bed
        spans = []
        for a in self.acts:
            if getattr(a, "indoor", False):
                continue
            if spans and abs(spans[-1][1] - a.t0) < 1e-6:
                spans[-1][1] = a.t0 + a.dur
            else:
                spans.append([a.t0, a.t0 + a.dur])
        if not spans:
            self.bed["forest_from"] = self.end_t
        elif len(spans) == 1 and abs(spans[0][1] - self.end_t) < 1e-6:
            self.bed["forest_from"] = spans[0][0]               # episode 2: factory first, forest to the end
        else:
            self.bed["forest_spans"] = spans
        self.stats = {"acts": {a.name: [round(a.t0, 2), round(a.dur, 2)] for a in self.acts}}
        # playful layer: a light music-box tune over the dark beds in the missions, a quieter pluck version
        # while they train (pitches from the C major pentatonic = same notes as the A minor beds)
        mel = P.get("melody", {})
        if mel.get("on", True):
            rng = np.random.default_rng(seed + 77)
            for a in self.acts:
                if hasattr(a, "melodies"):                     # the act picks its own tunes and windows
                    for m0, m1, inst, g, beat, tune in a.melodies():
                        self._melody(rng, a.t0 + m0, a.t0 + m1, inst, mel.get("gain", 0.24) * g, beat, tune)
                elif not getattr(a, "indoor", False):
                    self._melody(rng, a.t0 + 3.0, a.t0 + a.dur - 2.5, "music_box", mel.get("gain", 0.24),
                                 mel.get("beat", 0.55))
            if pulse:
                self._melody(rng, pulse[0] + 4.0, pulse[1] - 2.0, "pluck", mel.get("train_gain", 0.18),
                             60.0 / 88 / 1.0)
        self._snap(0.0)

    TUNE = [72, 74, 76, 79, 81, 84]                       # C D E G A C (MIDI 72-84, well inside 36-96)

    def _melody(self, rng, t0, t1, inst, gain, beat, tune=None):
        """Short bouncy phrases (stepwise, mostly up, ending on the tune's 1st, 3rd or 4th note) with rests
        between them."""
        tune = self.TUNE if tune is None else tune
        t = t0
        while t < t1 - beat * 8:
            i = int(rng.integers(0, 3))
            n_notes = int(rng.integers(5, 8))
            slots = sorted(rng.choice(8, n_notes, replace=False))
            if 0 not in slots:
                slots[0] = 0
            for k, sl in enumerate(slots):
                step = rng.choice([1, 1, 1, -1, 2, -2, 0])
                i = int(np.clip(i + step, 0, len(tune) - 1))
                if k == len(slots) - 1:
                    i = int(rng.choice([0, 2, 3]))
                vel = gain * (1.0 if sl % 4 == 0 else 0.75)
                self.track.hit(t + sl * beat, inst, tune[i], vel, float(rng.uniform(-0.3, 0.3)))
            t += beat * (8 + int(rng.choice([4, 4, 8])))

    def overlay(self, c, t):
        """Drawn over the act (world coordinates), before the glow and the fades; the FK engine's speech bubbles."""

    # ----- helpers shared with the acts -----

    def act_at(self, t):
        for a in self.acts:
            if t < a.t0 + a.dur:
                return a
        return self.acts[-1]

    def crossed(self, at):
        return self.prev_t < at <= self._t

    def pan(self, x):
        return float(np.clip((x - self.cam_x - self.w / 2) / (self.w / 2), -1, 1)) * 0.6

    def near(self, x, y):
        d = math.hypot(x - self.cam_x - self.w / 2, y - self.cam_y - self.h / 2)
        return float(1.0 / (1.0 + (d / 1500.0) ** 2))

    def hit(self, t, inst, note, vel, x, y):
        self.track.hit(t, inst, note, vel * self.near(x, y), self.pan(x))

    def fx(self, t, name, dur, vel, x, y):
        self.track.fx(t, name, dur, vel * self.near(x, y), self.pan(x))

    def say(self, t, kind, contour, x, y, vel=0.45):
        """A monster makes a little sound: contour up / down / hum / cheer."""
        if kind in VOICE:
            self.hit(t, f"voice_{contour}", VOICE[kind], vel, x, y)

    def note(self, i, octave=0):
        return self.track.note_in_scale(i % 8, octave)

    def glow_draw(self, fn):
        self.glow.begin(self.wcv)
        fn(self.wcv)
        self.glow.end(self.wcv)

    def view(self):
        """World rectangle on screen (x0, x1, y0, y1), zoom included."""
        cx, cy = self.cam_x + self.w / 2, self.cam_y + self.h / 2
        hw, hh = self.w / 2 / self.zoom, self.h / 2 / self.zoom
        return cx - hw, cx + hw, cy - hh, cy + hh

    def visible(self, x0, x1, y0=None, y1=None, pad=80):
        vx0, vx1, vy0, vy1 = self.view()
        if x1 < vx0 - pad or x0 > vx1 + pad:
            return False
        if y0 is not None and (y1 < vy0 - pad or y0 > vy1 + pad):
            return False
        return True

    # ----- camera -----

    def _snap(self, t):
        a = self.act_at(t)
        x, y, z = a.target(t - a.t0)
        self.cam_x, self.cam_y, self.zoom = x - self.w / 2, y - self.h / 2, z
        self.cam_vx = self.cam_vy = self.zoom_v = 0.0
        self.cur = a

    def _camera(self, t, dt):
        a = self.act_at(t)
        if a is not self.cur:
            if getattr(a, "joins_prev", False):  # same world, no cut: the camera just keeps gliding
                self.cur = a
            else:                                # cut (under the fade to black)
                self.particles.items = []
                self._snap(t)
                return
        x, y, z = a.target(t - a.t0)
        tx, ty = x - self.w / 2, y - self.h / 2
        w = self.p.get("camera", {}).get("omega", 1.6) * getattr(a, "cam_omega", 1.0)
        for _ in range(2):
            h = dt / 2
            self.cam_vx += (w * w * (tx - self.cam_x) - 2 * w * self.cam_vx) * h
            self.cam_vy += (w * w * (ty - self.cam_y) - 2 * w * self.cam_vy) * h
            self.zoom_v += (w * w * (z - self.zoom) - 2 * w * self.zoom_v) * h
            self.cam_x += self.cam_vx * h
            self.cam_y += self.cam_vy * h
            self.zoom += self.zoom_v * h

    # ----- engine hooks -----

    def canvas_options(self):
        return {"glow": 0.0, "grain": self.v.get("grain", 1.2), "background": BG,
                "vignette": self.v.get("vignette", 0.45)}

    def update(self, t, dt):
        self._t = t
        self._camera(t, dt)
        a = self.act_at(t)
        a.update(t - a.t0, dt)
        self.particles.update(dt)
        if t >= self.end_t and not self.done:
            self.done = True
            self.stats.update({"summary": self.p.get("summary", "Forest Keepers: 8 trees -> 6 monsters (assembly "
                                                                 "line, training), then replant, bridge, treehouse"),
                               "story_s": round(t, 2)})
            for a2 in self.acts:
                self.stats.update(getattr(a2, "stats", {}))
        self.prev_t = t

    def draw(self, cv, t, frame):
        if self.scv is None:
            self.glow = HeatGlow(cv, self.v.get("glow", 1.0), self.v.get("glow_radius", 1.2))
            self.scv = Shifted(cv)
        self.glow.clear()
        self.scv.dy = self.cam_y
        cx, cy = self.cam_x + self.w / 2, self.cam_y + self.h / 2
        self.wcv = c = Xform(self.scv, -self.cam_x, 0, 0.0, self.zoom, cx, cy)
        a = self.act_at(t)
        a.draw(c, t - a.t0)
        self.particles.draw(c, self.glow_draw)
        self.overlay(c, t)
        self.glow.apply(cv)
        # fades between acts (and at the very start / end)
        a0, a1 = a.t0, a.t0 + a.dur
        i = self.acts.index(a)
        nxt = self.acts[i + 1] if i + 1 < len(self.acts) else None
        f_in = 0.0 if getattr(a, "joins_prev", False) else 1 - seg(t, a0, a0 + self.fade)
        f_out = 0.0 if getattr(nxt, "joins_prev", False) else seg(t, a1 - self.fade, a1)
        f = max(f_in, f_out)
        if f > 0.001:
            cv.img[:] = (cv.img.astype(np.float32) * (1 - f)).astype(np.uint8)
