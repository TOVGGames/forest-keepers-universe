"""Forest Keepers engine (render IDs FK####, docs/engines/forest_keepers.md): the monster series as its own engine
from episode 4 on. Episodes 1-3 (FE0008-FE0014) were rendered by the Foundry engine; their acts, the six Keepers
and the treehouse are shared from families/foundry/keepers and families/foundry/products.

What this engine adds on top of the Foundry Keepers scene, for every video (owner rules, 2026-10-27):
- Lighthearted, all-ages music all the way through: the Forest Keepers theme (music.py) on a music box, a soft
  bouncy bass and a warm pad; no dark factory bed.
- The end card: a hanging sign asking for next-episode ideas in the comments (end_sign.py), appended to every video.
- Twigs has a little circular saw on each wrist.
- Nobody warps (owner, FK0001 review): every frame the scene checks that each Keeper on screen moved on from where it
  was, and warns about any jump (see _check_jumps). Nothing else warps either (owner, FK0005 review: the bread jumped
  to the table and back into Digs' hands, plates popped from under the table log): an act's props(t) lists the
  things that move, and they get the same check (prop_jumps).
- Calm camera (owner, FK0005 review: "slow on purpose", like Mr. Rogers): slow pans only, no dip-to-black cuts inside
  an act (act_cuts), no fast moves (cam_fast).
- Nobody walks through a wall (owner, FK0006 review, 2026-11-01: "they still walk through the wall" at the hill
  door). Doors are walked into, away from the camera (doorway.py); an act lists the solid things it draws in front
  of the walkway in walls(t), and every frame the scene counts a Keeper overlapping one (wall_clips, must be 0).
- The Keepers talk (owner, 2026-10-27, from episode 5): more voices, looking at the audience, a little speech bubble
  with a picture (chatter.py). Acts call act.chat(t, kind, mood); quiet stretches get asides automatically.

    python -m engine.render families/keepers/params/animal_houses.yaml
"""
import copy
import math

import numpy as np

from audio import synth
from families.foundry.keepers import scene as base
from families.foundry.keepers.common import smoothstep

from . import music
from .chatter import CONTOUR_MOOD, Chatter
from .animal_houses import DeliverAct, HousesAct, WakeAct, WheelAct
from .first_snow import FirstSnowAct
from .sled_shop import SledsAct
from .hill_race import CozyAct, HillAct, RaceAct
from .marble_run import BallAct, MarblesAct, RaceAct as MarbleRaceAct, RunAct, CheerAct
from .raft_race import LeafAct, RaftCheerAct, RaftRaceAct, RaftsAct
from .harvest_feast import BakeAct, BuildMillAct, FeastTableAct, MillAct, SupperAct
from .tune_up import HallAct, HomeAct, TripAct
from .tune_switch import HallSwitchAct, HomeSwitchAct, HomeWaveAct
from .new_keeper import NKHallAct, NKHomeAct, NKTripAct
from .winter_ready import WinterAct
from .bug_hunt import HuntAct
from .bug_flat import HuntFlatAct
from .night_animals import NightAct
from .end_sign import CommentSignAct
from .doorway import half_width
from . import narrator

SCALE_C = [60, 62, 64, 67, 69, 72, 74, 76]          # C major pentatonic, for the SFX that pick notes
# a Keeper whose velocity changes by more than this in one frame has jumped (20 px at 60 fps); a real-gravity jump
# take-off is ~700 px/s, the fastest start in the episodes so far
JUMP_DV = 1200.0
# ground moves faster than this (px/s, for a quarter second or more) look like zipping, not walking or rolling
FAST_VX = 1600.0
# the camera (owner after FK0005: "most of the pans and zooms go really fast, it feels shaky"; after its re-render:
# slow on purpose, no jump cuts): the view may pan at most CAM_PAN screen px/s and change its zoom by at most CAM_ZOOM
# (log units) per second; the fade between two acts doesn't count
CAM_PAN = 250.0
CAM_ZOOM = 0.2
# a prop (a loaf, a plate, a board being carried) whose velocity changes by more than this in one frame has jumped
PROP_DV = 600.0


class Scene(base.Scene):
    ACTS = {**base.ACTS, "wake": WakeAct, "wheel": WheelAct, "houses": HousesAct, "deliver": DeliverAct,
            "first_snow": FirstSnowAct, "sleds": SledsAct, "hill": HillAct, "race": RaceAct, "cozy": CozyAct,
            "ball": BallAct, "marbles": MarblesAct, "run": RunAct, "marble_race": MarbleRaceAct, "cheer": CheerAct,
            "leaf": LeafAct, "rafts": RaftsAct, "raft_race": RaftRaceAct, "raft_cheer": RaftCheerAct,
            "build": BuildMillAct, "mill": MillAct, "table": FeastTableAct, "bake": BakeAct, "feast": SupperAct,
            "trip": TripAct, "hall": HallAct, "hall_switch": HallSwitchAct, "home": HomeAct, "home_switch": HomeSwitchAct, "home_wave": HomeWaveAct, "hunt": HuntAct, "hunt_flat": HuntFlatAct, "night": NightAct,
            "nk_trip": NKTripAct, "nk_hall": NKHallAct, "nk_home": NKHomeAct, "winter": WinterAct,
            "comment_sign": CommentSignAct}
    SCALE = SCALE_C

    def __init__(self, params, seed, fmt, track):
        params = copy.deepcopy(params)
        acts = list(params.get("acts", []))
        if params.get("end_sign", True) and "comment_sign" not in acts:
            acts.append("comment_sign")
        params["acts"] = acts
        params["melody"] = {"on": False}             # the theme replaces the per-act phrases
        super().__init__(params, seed, fmt, track)
        for m in self.monsters:
            if m.kind == "teeth":
                m.saws = True
        song = params.get("song", {})
        chords = music.compose(track, 0.6, self.end_t + float(params.get("outro", 2.0)) - 0.5,
                               gain=song.get("gain", 1.0), variant=song.get("variant"))
        self.bed = {"type": "procedural", "name": "keepers_song", "gain": song.get("bed_gain", 1.0),
                    "chords": chords, "reverb": {"decay": 3.5, "wet": 0.4, "tone": 2600}}
        talk = params.get("chatter", {})
        self.chatter = Chatter(self, seed, gap=tuple(talk.get("gap", (3.6, 6.0))), vel=talk.get("vel", 0.34))
        self.chatter_on = talk.get("on", True)
        self._jp, self._jv, self._jlast, self._jact = {}, {}, {}, None
        self.jumps, self.fast = [], []
        self._pp, self._pv, self._plast, self.prop_jumps = {}, {}, {}, []
        self.act_cuts = [a.name for a in self.acts if getattr(a, "cuts", ())]
        self._fast_run = {}
        self._reported = False
        self._cam_prev, self._cam_act = None, None
        self.prev_cut = -1.0
        self.cam_max_pan, self.cam_max_zoom, self.cam_fast = 0.0, 0.0, []
        self.wall_clips, self._wlast = [], {}
        if params.get("narrator"):                  # the grandmother narrator: the scene masters its own soundtrack
            self.render_audio = lambda track, duration: narrator.soundtrack(self, track, duration)

    def say(self, t, kind, contour, x, y, vel=0.45):
        """The acts' old say(contour) calls: a voice with a face and a bubble now (chatter.py)."""
        if not self.chatter_on:
            return super().say(t, kind, contour, x, y, vel)
        icon = "auto" if getattr(self.act_at(t), "bubbles", True) else None
        self.chatter.say(t, kind, CONTOUR_MOOD.get(contour, contour), vel=vel * 0.8, x=x, y=y, icon=icon)

    def overlay(self, c, t):
        if self.chatter_on:
            self.chatter.draw(c, t)
        a = self.act_at(t)
        if hasattr(a, "screen"):                     # on-screen text: fixed screen units, not through the camera
            a.screen(self.scv.__dict__["_cv"], t - a.t0)

    # ----- cuts inside an act: a short dip to black, the camera jumps while it is dark (no fast pan) -----

    CUT_HALF = 0.45                                  # seconds from full picture to black (and back again)

    def _cuts(self, a):
        """Scene times of act a's dip-to-black cuts (act.cuts: act-local times on the act's own clock)."""
        k = getattr(a, "STRETCH", 1.0)
        return [a.t0 + c * k for c in getattr(a, "cuts", ())]

    def cut_dim(self, t):
        a = self.act_at(t)
        d = min([abs(t - c) for c in self._cuts(a)] + [99.0])
        return 1.0 - smoothstep(min(1.0, d / self.CUT_HALF))

    def draw(self, cv, t, frame):
        super().draw(cv, t, frame)
        f = self.cut_dim(t)
        if f > 0.001:
            cv.img[:] = (cv.img.astype(np.float32) * (1 - f)).astype(np.uint8)

    def update(self, t, dt):
        super().update(t, dt)
        a = self.act_at(t)
        if any(self.prev_cut < c <= t for c in self._cuts(a)):
            self._snap(t)                            # the screen is black: the camera starts the next shot
            self._cam_prev = None
        if any(self.prev_cut < a.t0 + c <= t for c in getattr(a, "camera_cuts", ())):
            self._snap(t)                            # a straight cut: the camera starts the next shot at once
        self.prev_cut = t
        if self.chatter_on:
            self.chatter.update(t, self.act_at(t))
        self._check_jumps(t, dt)
        self._check_camera(t, dt)
        self._check_walls(t)
        if self.done and not self._reported:
            self._reported = True
            self.stats["teleports"] = len(self.jumps)
            self.stats["fast_moves"] = len(self.fast)
            self.stats["voices"] = dict(self.chatter.count)
            self.stats["cam_max_pan"] = round(self.cam_max_pan)
            self.stats["cam_max_zoom"] = round(self.cam_max_zoom, 3)
            self.stats["cam_fast"] = len(self.cam_fast)
            self.stats["prop_jumps"] = len(self.prop_jumps)
            self.stats["act_cuts"] = len(self.act_cuts)
            self.stats["wall_clips"] = len(self.wall_clips)
            if self.wall_clips:
                print(f"  WARNING: {len(self.wall_clips)} times a Keeper overlapped a wall drawn in front of it "
                      f"(first: {self.wall_clips[:4]}). Walls stand behind the walkway; doors are walked into "
                      f"(doorway.py). Nobody walks through a wall.", flush=True)
            if self.prop_jumps:
                print(f"  WARNING: {len(self.prop_jumps)} times a carried / moving thing jumped between two frames "
                      f"(first: {self.prop_jumps[:4]}). Move it with whoever carries it; nothing warps.", flush=True)
            if self.act_cuts:
                print(f"  WARNING: dip-to-black cuts inside acts {self.act_cuts}: use a slow pan instead (owner: no "
                      f"jump cuts).", flush=True)
            if self.cam_fast:
                print(f"  WARNING: {len(self.cam_fast)} camera moves faster than {CAM_PAN:.0f} screen px/s or "
                      f"{CAM_ZOOM} zoom/s (first: {self.cam_fast[:3]}). Slow the camera down.", flush=True)
            if self.jumps:
                print(f"  WARNING: {len(self.jumps)} times a Keeper jumped to a new spot between two frames "
                      f"(first: {self.jumps[:3]}). Make it walk/roll/float there; nobody warps.", flush=True)
            if self.fast:
                print(f"  WARNING: {len(self.fast)} ground moves faster than {FAST_VX:.0f} px/s "
                      f"(first: {self.fast[:3]}). Slow them down or give them more time.", flush=True)

    def _camera(self, t, dt):
        """The camera spring, and for acts with cam_snap: once it has all but arrived at a target that holds still,
        it rests exactly there (owner after FK0007: text in the book shimmered while the camera crept the last
        fraction of a pixel; a camera at rest draws every frame the same)."""
        super()._camera(t, dt)
        a = self.act_at(t)
        if not getattr(a, "cam_snap", False):
            return
        x, y, z = a.target(t - a.t0)
        tx, ty = x - self.w / 2, y - self.h / 2
        px = 0.15 / max(self.zoom, 0.1)                              # 0.15 screen pixels, in world units
        if (abs(tx - self.cam_x) < px and abs(ty - self.cam_y) < px and abs(z - self.zoom) < 2e-4
                and abs(self.cam_vx) < 3 * px and abs(self.cam_vy) < 3 * px and abs(self.zoom_v) < 2e-3):
            self.cam_x, self.cam_y, self.zoom = tx, ty, z
            self.cam_vx = self.cam_vy = self.zoom_v = 0.0

    def _check_walls(self, t):
        """A Keeper outside any doorway whose drawn width overlaps a wall the act draws in front of the walkway
        (act.walls) is walking through it: logged as (t, act, kind, x) once per run."""
        a = self.act_at(t)
        walls = a.walls(t - a.t0) if hasattr(a, "walls") else []
        if not walls:
            return
        deep = getattr(a, "door_depth", {})
        for m in self.monsters:
            if m.kind not in getattr(a, "poses", {}) or deep.get(m.kind, 0.0) > 0.0:
                continue
            hw = half_width(m)
            if any(m.x + hw > w0 and m.x - hw < w1 for w0, w1 in walls) and self.visible(m.x - hw, m.x + hw):
                if t - self._wlast.get(m.kind, -1.0) > 0.5:
                    self.wall_clips.append((round(t, 2), a.name, m.kind, round(m.x)))
                self._wlast[m.kind] = t

    def _check_camera(self, t, dt):
        """How fast the view moves on screen: pan (screen px/s) and zoom (log units/s). A cut to a new act under a
        fade (the camera snaps) is not a move, nor is a straight cut the act lists in camera_cuts (act-local times; owner
        2026-11-06: a longer walk gets a cut, angle, crop or zoom change). Runs of too-fast frames go into self.cam_fast as (t, act, pan, zoom)."""
        a = self.act_at(t)
        cut = a is not self._cam_act and not getattr(a, "joins_prev", False)
        self._cam_act = a
        cx, cy, z = self.cam_x + self.w / 2, self.cam_y + self.h / 2, self.zoom
        p, self._cam_prev = self._cam_prev, (cx, cy, z)
        if p is None or cut or dt <= 0 or a.name == "comment_sign":
            return
        if any(t - dt < a.t0 + c <= t + 1e-9 for c in getattr(a, "camera_cuts", ())):
            return                                   # a straight cut to a new angle (act.camera_cuts), not a pan
        pan = math.hypot(cx - p[0], cy - p[1]) / dt * z
        zr = abs(math.log(z / p[2])) / dt
        self.cam_max_pan, self.cam_max_zoom = max(self.cam_max_pan, pan), max(self.cam_max_zoom, zr)
        if pan > CAM_PAN or zr > CAM_ZOOM:
            if not self.cam_fast or t - self.cam_fast[-1][0] > 1.0:
                self.cam_fast.append((round(t, 2), a.name, round(pan), round(zr, 2)))

    def _check_jumps(self, t, dt):
        """Owner rule (FK0001 review, 2026-10-27): no warping, it isn't realistic. Every Keeper on screen has to get
        from one spot to the next through the frames in between. A step change in velocity between two frames (a jump
        to a new place, or a move that starts or stops at full speed) goes into self.jumps as (t, act, kind, from x,
        to x); long fast slides into self.fast. Both are logged in the stats and printed as warnings; treat any as a
        bug and fix the act before rendering. A cut to a new act (with a fade) starts the check fresh;
        a joins_prev act continues it."""
        a = self.act_at(t)
        if a is not self._jact and not getattr(a, "joins_prev", False):
            self._jp, self._jv, self._fast_run = {}, {}, {}
            self._pp, self._pv = {}, {}
        self._jact = a
        if dt <= 0:
            return
        self._check_props(t, dt, a)
        for m in self.monsters:
            p = self._jp.get(m.kind)
            self._jp[m.kind] = (m.x, m.y)
            if p is None:
                continue
            v = ((m.x - p[0]) / dt, (m.y - p[1]) / dt)
            v0 = self._jv.get(m.kind)
            self._jv[m.kind] = v
            on = self.visible(min(m.x, p[0]) - 100, max(m.x, p[0]) + 100)
            if v0 is not None and on and math.hypot(v[0] - v0[0], v[1] - v0[1]) > JUMP_DV:
                if t - self._jlast.get(m.kind, -1.0) > 0.1:      # the frame it stops again is the same jump
                    self.jumps.append((round(t, 2), a.name, m.kind, round(p[0]), round(m.x)))
                self._jlast[m.kind] = t
            run = self._fast_run.get(m.kind)
            if on and abs(v[0]) > FAST_VX and not getattr(a, "fast_ok", False):     # (sleds may go fast)
                if run is None:
                    self._fast_run[m.kind] = run = [t, False]
                if t - run[0] >= 0.25 and not run[1]:
                    run[1] = True
                    self.fast.append((round(run[0], 2), a.name, m.kind, round(abs(v[0]))))
            else:
                self._fast_run.pop(m.kind, None)

    def _check_props(self, t, dt, a):
        """The things an act moves (act.props: {name: (x, y)}) get the Keepers' check: a step change in velocity
        between two frames (it appeared somewhere else, or set off / stopped at full speed) goes into
        self.prop_jumps as (t, act, name, from, to). A thing that leaves the list (put away, eaten) is forgotten."""
        props = a.props(t - a.t0) if hasattr(a, "props") else {}
        for name in list(self._pp):
            if name not in props:
                self._pp.pop(name)
                self._pv.pop(name, None)
        for name, (x, y) in props.items():
            p = self._pp.get(name)
            self._pp[name] = (x, y)
            if p is None:
                continue
            v = ((x - p[0]) / dt, (y - p[1]) / dt)
            v0 = self._pv.get(name)
            self._pv[name] = v
            on = self.visible(min(x, p[0]) - 60, max(x, p[0]) + 60)
            if v0 is not None and on and math.hypot(v[0] - v0[0], v[1] - v0[1]) > PROP_DV:
                if t - self._plast.get(name, -1.0) > 0.1:
                    self.prop_jumps.append((round(t, 2), a.name, name, (round(p[0]), round(p[1])), (round(x), round(y))))
                self._plast[name] = t
