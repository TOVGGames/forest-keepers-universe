"""Forest Keepers ep 6 remake, The Big Tune-Up: the flat second half (docs/engines/forest_keepers_tune_up.md,
"Remake"). The old-look first half is the old engine (tune_up.py + tune_switch.py) re-rendered; at the end of the
factory Glo flares at the STORYBOOK BEACON and its shockwave rolls over the whole picture (shockwave; owner, FK0018
review). Inside the ring the same moment goes on in the flat picture-book look, so nothing jumps: this module re-draws
the OLD scene's own state, frame
by frame (where every Keeper is, its pose and face, the camera, the doors, the animals), in the flat style.

    snap = record(scene, t)         # after scene.update(t, dt): a plain-data snapshot of that frame
    rgb = draw(snap)                # the same frame, flat
    rgb = page_turn(old, flat, u)   # the turn: u 0..1
"""
import math

import numpy as np
import skia

from . import illustrate as il
from .flat import FlatPage, PAL, bush as flat_bush, lolly_tree, treehouse
from .storybook import C, oval, rrect, smooth, tone, tube

KEEP = ("alive", "orb_in", "reach", "wheel_rot", "punch", "walk", "spring", "dig", "rough", "badge", "gait", "saws",
        "saw_spin", "saw_run", "punch_l", "hands", "blades", "grip", "turn", "legs_turn", "float", "wing_phase",
        "wing_up", "talk", "attend", "talk_dy", "flash", "job", "smile", "lid_top", "brow", "cheek", "brow_on",
        "turned", "spin", "wave", "hold_out", "arm_ang", "arm_ang_r", "socket", "mole_claws", "hat_orb", "lamp")
NAMES = {"lantern": "Glo", "wheels": "Wheels", "springs": "Springs", "digger": "Digs", "teeth": "Twigs",
         "tentacles": "Hans"}
NAME_COL = {"lantern": (70, 170, 160), "wheels": (70, 110, 190), "springs": (200, 160, 50), "digger": (190, 70, 60),
            "teeth": (130, 80, 170), "tentacles": (214, 110, 40)}

# night-shift factory, flat and muted
HALL = dict(wall_top="#28324a", wall_low="#36425a", pillar="#3e4b63", beam="#4a5873", floor="#4a4a52",
            floor_low="#3e3e46", walk="#58585f", belt="#2c3140", frame="#55617a", pallet="#c79a4a", lamp="#ffe0a0",
            cone="#f6d28a", steel="#68758e", steel2="#5a667e", sign="#f0dcb4", cover="#a85a48", page="#f2e7cf",
            hills="#9aa35c", sun="#e8b35a", glass="#a9b7c8", frame2="#8a96a8", night="#1c2944", door="#59647a",
            hazard="#c9a050")
# the village at night
VIL = dict(sky_top="#121a33", sky_low="#2b3a5e", star="#f4ecd2", moon="#f3ead0", far="#22304a", far2="#283a4e",
           mid="#2f4a48", ground="#3a4a3a", ground2="#334234", path="#5a5444", leaf="#3f6a4e", leaf2="#4a7a56",
           trunk="#6a4e3e", rock="#5e5248", rock2="#54493f", door_glow="#f2c878", window="#ffd890")


class ZoomPage(FlatPage):
    """FlatPage whose paper grain also scales with the camera zoom (the old camera zooms), so the grain stays fixed
    to what it is painted on (owner: the texture never slides over things)."""
    zoom = 1.0

    def grain_shader(self, dx=0.0, dy=0.0):
        m = skia.Matrix.Translate(dx, dy)
        k = self._sc * self.zoom
        m.preScale(k, k)
        return self._speck.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat,
                                      skia.SamplingOptions(skia.FilterMode.kLinear), m)


# ----------------------------------------------------------------------------------------------- the camera

def project(snap, x, y, par=1.0):
    """World point -> screen, the old engine's camera (Shifted + Xform about the view centre). par < 1: a far layer
    that moves less (parallax)."""
    z, cx, cy, W, H = snap["zoom"], snap["cx"], snap["cy"], snap["W"], snap["H"]
    return W / 2 + z * (x - cx * par), H / 2 + z * (y - cy)


def _view_x(snap, par=1.0):
    z, cx, W = snap["zoom"], snap["cx"], snap["W"]
    return cx * par - W / 2 / z, cx * par + W / 2 / z


# ----------------------------------------------------------------------------------------------- recording

def act_fade(scene, t):
    """The old engine's dip to black between acts (families/foundry/keepers/scene.py draw)."""
    from families.foundry.keepers.common import seg
    a = scene.act_at(t)
    a0, a1 = a.t0, a.t0 + a.dur
    i = scene.acts.index(a)
    nxt = scene.acts[i + 1] if i + 1 < len(scene.acts) else None
    f_in = 0.0 if getattr(a, "joins_prev", False) else 1 - seg(t, a0, a0 + scene.fade)
    f_out = 0.0 if getattr(nxt, "joins_prev", False) else seg(t, a1 - scene.fade, a1)
    return max(f_in, f_out)


def record(scene, t):
    """The old scene's state at t (call right after scene.update(t, dt))."""
    a = scene.act_at(t)
    lt = t - a.t0
    snap = dict(t=t, act=a.name, lt=lt, zoom=scene.zoom, cx=scene.cam_x + scene.w / 2, cy=scene.cam_y + scene.h / 2,
                W=scene.w, H=scene.h, keepers=[], fade=act_fade(scene, t), G=getattr(a, "G", None))
    poses = getattr(a, "poses", {})
    depth = dict(getattr(a, "door_depth", {}) or {})
    reach = dict(getattr(a, "reach", {}) or {})
    back = a.glo_back(lt) if hasattr(a, "glo_back") else False
    for m in scene.monsters:
        if m.kind not in poses:
            continue
        d = {k: getattr(m, k) for k in KEEP if hasattr(m, k)}
        d.update(kind=m.kind, x=m.x, y=m.y, k=m.k, pose=poses[m.kind], hide=set(m.hide), bare=set(m.bare),
                 old=set(m.old), part_dxy=dict(m.part_dxy), arm_to=dict(m.arm_to), arm_len=dict(m.arm_len),
                 arm_w=dict(getattr(m, "arm_w", {})))
        u = depth.get(m.kind, 0.0)
        d["depth"] = u
        d["back"] = bool(back and m.kind == "lantern")
        d["reach_pts"] = list(reach.get(m.kind, []))
        if 0.0 < u < 1.0:
            door = (a.way_out if lt >= getattr(a, "ME", -1e9) else a.way_in) if hasattr(a, "way_out") else \
                getattr(a, "doorway", None)
            if door is not None:
                d["door"] = dict(pose=door.pose(u), opening=[tuple(p) for p in door.opening()])
        snap["keepers"].append(d)
    snap["bubbles"] = _bubbles(scene, t)
    if a.name == "hall":
        from .tune_switch import press_state
        from families.foundry.keepers.common import seg, smootherstep
        snap["press"] = press_state(lt, a.beats)
        snap["door_u"] = smootherstep(seg(lt, *a.door))
        snap["flare"] = a.flare(lt)
    elif a.name == "home":
        snap["wave"] = getattr(a, "wave", None)
        snap["bunny"] = a.bunny_st(lt)
        snap["hog"] = a.hog_st(lt)
        snap["wave_t"] = a.wave_t
    elif a.name == "comment_sign":
        snap["names"] = _sign_names(a, scene, lt)
    return snap


def _bubbles(scene, t):
    from families.foundry.keepers.common import seg, smoothstep
    from .chatter import TOPS, _back
    ch = getattr(scene, "chatter", None)
    out = []
    if ch is None:
        return out
    for tk in ch.talks:
        if tk.icon is None:
            continue
        life = max(1.3, tk.dur + 0.75)
        u = t - tk.t
        if not (0 <= u < life):
            continue
        m = scene.by_kind.get(tk.kind)
        if m is None:
            continue
        pop = _back(min(1.0, u / 0.24))
        fade = 1 - smoothstep(seg(u, life - 0.3, life))
        k = m.k / 0.55
        hx = m.x + 76 * k
        hy = m.y - TOPS[m.kind] * m.k - 62 * k + m.talk_dy - 10 * smoothstep(min(1.0, u / 0.5))
        out.append(dict(icon=tk.icon, x=hx, y=hy, r=54 * k * pop * fade ** 0.5,
                        tail=(m.x + 22 * k, m.y - TOPS[m.kind] * m.k + 6 * k), edge=tuple(m.full)))
    return out


def _sign_names(a, scene, lt):
    from families.foundry.keepers.common import seg, smoothstep
    amt = smoothstep(seg(lt, 1.0, 1.6))
    return amt


# ----------------------------------------------------------------------------------------------- the walks

def tracks(snaps):
    """{act: {kind: (ts, xs, ys)}} from the snapshots: every Keeper's world x, y over time, per act (the flat walks
    are built from these, so they follow the old scene's own moves exactly)."""
    out = {}
    for f in sorted(snaps):
        sn = snaps[f]
        for d in sn["keepers"]:
            ts, xs, ys = out.setdefault(sn["act"], {}).setdefault(d["kind"], ([], [], []))
            ts.append(sn["t"])
            xs.append(d["x"])
            ys.append(d["y"])
    return {a: {k: tuple(np.array(v) for v in tr) for k, tr in kd.items()} for a, kd in out.items()}


class Walks:
    """The flat half walks the way every flat episode from ep 14 on does (owner, approving FK0016): arms hang and swing
    against the legs, Twigs' knees bend forward, Hans ripples along on his six tentacles (WaveGait), Digs takes quick
    little steps, every foot planted (no sliding), and a walker turns to face where it goes. Built on the old scene's
    own x(t), so where each one is never changes; only how its legs and arms move."""
    WALKERS = ("teeth", "digger", "tentacles", "wheels")

    def __init__(self, trk):
        from families.foundry.products.monster import TURN_NARROW
        from .flat_motion import WaveGait, biped, heading
        self.paths, self.turns, self.gaits = {}, {}, {}
        for act, kinds in trk.items():
            for kd, (ts, xs, ys) in kinds.items():
                if kd not in self.WALKERS:
                    continue
                path = (lambda t, ts=ts, xs=xs: float(np.interp(t, ts, xs)))
                self.paths[(act, kd)] = path
                turn = heading(path)
                self.turns[(act, kd)] = turn
                narrow = (lambda f, turn=turn: (lambda t: 1.0 - TURN_NARROW * f * abs(turn(t))))
                ground = float(np.median(ys))
                k = 0.55
                if kd == "tentacles":
                    self.gaits[(act, kd)] = WaveGait(ground, k, path, spread=narrow(0.5))
                elif kd in ("teeth", "digger"):
                    self.gaits[(act, kd)] = biped(kd, path, ground, k, spread=narrow(1.0))

    def attrs(self, act, d, t):
        """-> (extra attrs, dy to use instead of the old walk bob, feet in world coords or None)."""
        from .flat_motion import arm_swing, roll_swing
        kd = d["kind"]
        key = (act, kd)
        if key not in self.paths or d["depth"] > 0.0:
            return None
        turn = self.turns[key](t)
        a = dict(legs_turn=turn, turn=turn * (1 - min(1.0, d.get("attend", 0.0) or 0.0)))
        if kd == "wheels":
            a["arm_swing"] = roll_swing(self.paths[key], t, 46.0 * 0.55)
            a["clamp_reach"] = True
            return a, None, None
        g = self.gaits[key]
        feet = list(g.feet(t))
        if kd == "tentacles":
            return a, g.bob(t), feet
        a["arm_swing"] = arm_swing(g, t)
        if kd == "teeth":
            a.update(knee_fwd=True, clamp_reach=True)
        return a, 0.0, feet


# ----------------------------------------------------------------------------------------------- Keepers

def _keeper(pg, snap, d, t, mirror_x=None):
    walk = WALKS.attrs(snap["act"], d, snap["t"]) if WALKS is not None else None
    d = dict(d)
    kind, x, y, k = d.pop("kind"), d.pop("x"), d.pop("y"), d.pop("k")
    dy, ang = d.pop("pose")
    feet = None
    if walk is not None:
        extra_a, wdy, feet = walk
        d.update(extra_a)
        if wdy is not None:
            dy = wdy
    u, back, pts = d.pop("depth"), d.pop("back"), d.pop("reach_pts")
    door = d.pop("door", None)
    z = snap["zoom"]
    sc, lift, shade, vis = 1.0, 0.0, 1.0, 1.0
    if door is not None:
        sc, lift, shade, vis = door["pose"]
    sx, sy = project(snap, x, y + dy - lift)
    extra = None
    if kind == "tentacles" and pts:
        tps = [project(snap, tx, ty) for tx, ty in pts]

        def extra(cv, m, tps=tps, dy=dy):
            for i, (tx, ty) in enumerate(tps):
                m.work_tentacle(cv, tx, ty, t, slot=i - 0.5, dy=dy * z)
    c = pg.c
    c.save()
    if door is not None:
        q = [project(snap, *p) for p in door["opening"]]
        c.clipPath(smooth(q, closed=True) if False else _poly(q), doAntiAlias=True)
        lp = skia.Paint(Alpha=int(255 * max(0.0, min(1.0, vis))))
        lp.setColorFilter(skia.ColorFilters.Matrix([shade, 0, 0, 0, 0, 0, shade, 0, 0, 0, 0, 0, shade, 0, 0,
                                                    0, 0, 0, 1, 0]))
        c.saveLayer(None, lp)
    if mirror_x is not None:
        mx = project(snap, mirror_x, 0)[0]
        c.translate(2 * mx, 0)
        c.scale(-1, 1)
    if "lamp" in d and d["lamp"] is None:
        d.pop("lamp")
    if feet is not None:
        d["feet"] = [project(snap, fx, fy) for fx, fy in feet]
        d.pop("walk", None)
    il.figure(pg, kind, sx, sy, k * z * sc, 6, t=t, extra=extra, shadow=door is None and mirror_x is None, **d)
    if door is not None:
        c.restore()
    c.restore()


def _poly(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def _rect(snap, x0, y0, x1, y1, par=1.0):
    a = project(snap, x0, y0, par)
    b = project(snap, x1, y1, par)
    return a[0], a[1], b[0], b[1]


def _box(pg, snap, x0, y0, x1, y1, col, shade=0.08, r=0.0, alpha=1.0):
    X0, Y0, X1, Y1 = _rect(snap, x0, y0, x1, y1)
    path = rrect(X0, Y0, X1, Y1, r * snap["zoom"]) if r else _poly([(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)])
    if alpha < 1.0:
        pg.flat(path, col, alpha)
    else:
        pg.shape(path, col, shade)
    return path


def _text(pg, s, x, y, size, col, a=1.0, weight="Bold"):
    from .christmas_flat import _font
    f = _font(size, weight)
    pg.c.drawString(s, x - f.measureText(s) / 2, y, f, skia.Paint(AntiAlias=True, Color=C(col, a)))


# ----------------------------------------------------------------------------------------------- the hall

def _hall_back(pg, snap):
    from .tune_up import EXIT, FY, G, HALL as HX, MIRROR, slot_x
    from .tune_switch import PRESS_X
    z = snap["zoom"]
    W, H = snap["W"], snap["H"]
    vx0, vx1 = _view_x(snap)
    top = G - 1300
    sky = _poly([(0, 0), (W, 0), (W, H), (0, H)])
    pg.grad(sky, HALL["wall_top"], HALL["wall_low"])
    # pillars on the back wall (a little parallax, as in the old hall: they sit on the far wall)
    par = 0.25
    off = snap["cx"] * 0.0
    for gx in np.arange(math.floor((vx0 - 400) / 700) * 700, vx1 + 700, 700):
        _box(pg, snap, gx, top, gx + 46, G, HALL["pillar"], 0.0)
    _box(pg, snap, vx0 - 200, top - 400, vx1 + 200, G - 1180, HALL["beam"], 0.0)
    for gy in (G - 1000, G - 430):
        _box(pg, snap, vx0 - 200, gy - 5, vx1 + 200, gy + 5, HALL["pillar"], 0.0)
    # ceiling lamps, warm light cones (soft)
    for lx in np.arange(HX[0] + 350, HX[1], 700):
        if not (vx0 - 400 < lx < vx1 + 400):
            continue
        a = project(snap, lx - 42, G - 900)
        b = project(snap, lx + 42, G - 900)
        f0 = project(snap, lx - 270, G)
        f1 = project(snap, lx + 270, G)
        pg.flat(_poly([a, b, f1, f0]), HALL["cone"], 0.07, blur=14 * z)
        lt, lb = project(snap, lx, G - 1180), project(snap, lx, G - 905)
        pg.c.drawLine(lt[0], lt[1], lb[0], lb[1], skia.Paint(AntiAlias=True, Color=C(HALL["pillar"]),
                                                             StrokeWidth=max(1.0, 3 * z)))
        p0, p1 = project(snap, lx - 40, G - 868), project(snap, lx + 40, G - 868)
        q0, q1 = project(snap, lx - 22, G - 902), project(snap, lx + 22, G - 902)
        pg.shape(_poly([p0, p1, q1, q0]), HALL["steel2"], 0.06)
        bx, by = project(snap, lx, G - 864)
        pg.flat(oval(bx, by, 22 * z, 22 * z), HALL["lamp"], 0.35, blur=10 * z)
        pg.flat(oval(bx, by, 11 * z, 11 * z), HALL["lamp"])
    # the floor and the walkway
    _box(pg, snap, vx0 - 200, G, vx1 + 200, G + 700, HALL["floor"], 0.0)
    _box(pg, snap, vx0 - 200, FY + 38, vx1 + 200, FY + 44, HALL["walk"], 0.0)
    # the way out: an opening into the night, its roll-up door
    d0, d1 = EXIT
    if vx0 - 200 < d1 and d0 < vx1 + 200:
        u = snap.get("door_u", 0.0)
        _box(pg, snap, d0, G - 520, d1, G, HALL["belt"], 0.0)
        night = _box(pg, snap, d0, G - 520, d1, G, HALL["night"], 0.0, alpha=0.4 + 0.6 * u)
        for q in range(6):
            sx_, sy_ = project(snap, d0 + 40 + q * 66, G - 470 + 37 * ((q * 7) % 5))
            pg.flat(oval(sx_, sy_, 2.6 * z, 2.6 * z), VIL["star"], 0.8 * u)
        _box(pg, snap, d0, G - 30, d1, G, VIL["ground"], 0.0, alpha=u)
        _box(pg, snap, d0 - 24, G - 566, d1 + 24, G - 520, HALL["steel2"], 0.06)
        _box(pg, snap, d0 - 24, G - 520, d0, G, HALL["steel2"], 0.06)
        _box(pg, snap, d1, G - 520, d1 + 24, G, HALL["steel2"], 0.06)


def _hall_door(pg, snap):
    """The roll-up door itself (in front of whoever stands in the doorway)."""
    from .tune_up import EXIT, G
    vx0, vx1 = _view_x(snap)
    d0, d1 = EXIT
    if not (vx0 - 200 < d1 and d0 < vx1 + 200):
        return
    u = snap.get("door_u", 0.0)
    bot = G - 514 * u
    if bot > G - 512:
        _box(pg, snap, d0, G - 520, d1, bot, HALL["door"], 0.05)
        for y in np.arange(G - 490, bot - 10, 34):
            _box(pg, snap, d0 + 6, y, d1 - 6, y + 3, tone(HALL["door"], -0.08), 0.0)
        _box(pg, snap, d0, bot - 14, d1, bot, HALL["hazard"], 0.0)


def _line_end(pg, snap):
    """The end of the old assembly line (its last pallets) where they stepped down."""
    from .tune_up import G, PY, slot_x
    vx0, vx1 = _view_x(snap)
    x1 = slot_x(15) + 210
    if vx0 > x1 + 50:
        return
    x0 = max(vx0 - 100, slot_x(0) - 210)
    _box(pg, snap, x0, PY, x1, G + 24, HALL["belt"], 0.05)
    _box(pg, snap, x0, G + 20, x1, G + 34, HALL["frame"], 0.0)
    for p in range(16):
        px = slot_x(p)
        if vx0 - 300 < px < vx1 + 300:
            _box(pg, snap, px - 150, PY - 6, px + 150, PY + 2, HALL["pallet"], 0.0, r=3)


COPPER = "#c0784a"


def _coil(pg, snap, y, lit, front):
    from .tune_switch import COIL_R, PRESS_X
    rx, ry = COIL_R
    z = snap["zoom"]
    a0, a1 = (0.0, math.pi) if front else (math.pi, 2 * math.pi)
    pts = [project(snap, PRESS_X + rx * math.cos(a), y + ry * math.sin(a)) for a in np.linspace(a0, a1, 24)]
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    base = tone(COPPER, -0.25) if not front else COPPER
    col = tuple(np.array(C_rgb(base)) * (1 - lit) + np.array(C_rgb(HALL["lamp"])) * lit)
    pg.stroke(p, col, 10 * z)
    if lit > 0.01 and front:
        pg.stroke(p, HALL["lamp"], 22 * z, 0.25 * lit, blur=8 * z)


def _press(pg, snap):
    """The STORYBOOK BEACON, flat: the control post with its glass eye, the base with its sign, the column with three
    copper coils, the brass collar and the glass orb (tune_switch.press_geometry)."""
    from .tune_switch import COIL_Y, ORB, ORB_R, PRESS_X, press_geometry
    vx0, vx1 = _view_x(snap)
    if not (vx0 - 400 < PRESS_X < vx1 + 400):
        return
    z = snap["zoom"]
    st = snap.get("press") or dict(eye=1.0, coils=[0.55] * 3, orb=0.5, pulse=0.0, hum=0.55)
    g = press_geometry()
    _box(pg, snap, *g["post"], HALL["steel"], 0.1, r=6)
    _box(pg, snap, *g["post_cap"], HALL["steel2"], 0.06, r=4)
    for q, y in enumerate(COIL_Y):
        _coil(pg, snap, y, st["coils"][q], False)
    _box(pg, snap, *g["column"], HALL["steel"], 0.12, r=6)
    for q, y in enumerate(COIL_Y):
        _coil(pg, snap, y, st["coils"][q], True)
    _box(pg, snap, *g["base"], HALL["steel2"], 0.08, r=8)
    _box(pg, snap, *g["base_top"], HALL["steel"], 0.06, r=6)
    for rx in (-130, 130):
        for ry in (-140, -30):
            cx_, cy_ = project(snap, PRESS_X + rx, g["base"][3] + ry)
            pg.flat(oval(cx_, cy_, 4 * z, 4 * z), HALL["frame"])
    _box(pg, snap, *g["sign"], "#3a4254", 0.0, r=6)
    sx, sy = project(snap, PRESS_X, (g["sign"][1] + g["sign"][3]) / 2 + 8)
    _text(pg, "STORYBOOK BEACON", sx, sy, 22 * z, HALL["sign"], 0.92)
    _box(pg, snap, *g["collar"], "#b89858", 0.1, r=6)
    ox, oy = project(snap, *ORB)
    o, pu = st["orb"], st["pulse"]
    if o > 0 or pu > 0:
        pg.flat(oval(ox, oy, ORB_R * (1.8 + 1.4 * pu) * z, ORB_R * (1.8 + 1.4 * pu) * z), HALL["lamp"],
                0.25 * o + 0.4 * pu, blur=30 * z)
    pg.flat(oval(ox, oy, (ORB_R + 7) * z, (ORB_R + 7) * z), HALL["steel2"])
    glass = tuple(np.array(C_rgb("#7d93a8")) * (1 - o) + np.array(C_rgb(HALL["lamp"])) * o)
    pg.flat(oval(ox, oy, ORB_R * z, ORB_R * z), glass)
    pg.flat(oval(ox - 20 * z, oy - 24 * z, 18 * z, 12 * z), "#f6f4ea", 0.55)
    ex, ey = project(snap, *g["eye"])
    pg.flat(oval(ex, ey, 26 * z, 26 * z), HALL["steel2"])
    e = st["eye"]
    pg.flat(oval(ex, ey, 19 * z, 19 * z), tuple(np.array(C_rgb("#3a4254")) * (1 - e) + np.array(C_rgb(HALL["lamp"]))
                                               * e))
    if e > 0:
        pg.flat(oval(ex, ey, 34 * z, 34 * z), HALL["lamp"], 0.3 * e, blur=12 * z)


def C_rgb(col):
    if isinstance(col, str):
        h = col.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(col)


def _mirror_glass(pg, snap):
    from .tune_up import FY, G, MIRROR
    m0, m1 = MIRROR
    top, bot = G - 470, FY + 6
    return [project(snap, m0, top), project(snap, m1, top), project(snap, m1, bot), project(snap, m0, bot)]


def _mirror(pg, snap, t):
    """The tall polished mirror on the walkway: whoever stands left of it sees themself in it."""
    from .tune_up import FY, G, MIRROR
    m0, m1 = MIRROR
    vx0, vx1 = _view_x(snap)
    if not (vx0 - 600 < m1 and m0 < vx1 + 100):
        return
    z = snap["zoom"]
    glass = _poly(_mirror_glass(pg, snap))
    pg.grad(glass, "#6f7e95", "#8f9db0")
    c = pg.c
    c.save()
    c.clipPath(glass, doAntiAlias=True)
    for d in snap["keepers"]:
        if m0 - 520 < d["x"] < m0 and d["depth"] <= 0.0 and not d["back"]:     # (Glo up on the press: not)
            _keeper(pg, snap, d, t, mirror_x=m0)
    pg.flat(glass, "#b8c6d4", 0.16)
    for q in range(4):
        xx = m0 + 60 + q * 140
        a, b = project(snap, xx, G - 450), project(snap, xx + 80, G - 350)
        c.drawLine(a[0], a[1], b[0], b[1], skia.Paint(AntiAlias=True, Color=C("#ffffff", 0.22),
                                                      StrokeWidth=6 * z, StrokeCap=skia.Paint.kRound_Cap))
    c.restore()
    top, bot = G - 470, FY + 6
    _box(pg, snap, m0 - 16, top - 16, m1 + 16, top, HALL["frame2"], 0.08, r=4)
    _box(pg, snap, m0 - 16, top, m0, bot, HALL["frame2"], 0.06)
    _box(pg, snap, m1, top, m1 + 16, bot, HALL["frame2"], 0.06)
    for fx_ in (m0 + 40, m1 - 40):
        for s_ in (-1, 1):
            a, b = project(snap, fx_, bot), project(snap, fx_ + 20 * s_, bot + 30)
            c.drawLine(a[0], a[1], b[0], b[1], skia.Paint(AntiAlias=True, Color=C(HALL["frame2"]),
                                                          StrokeWidth=6 * z))


def draw_hall(pg, snap):
    t = snap["lt"]
    pg.begin_grain()
    _hall_back(pg, snap)
    _press(pg, snap)
    _line_end(pg, snap)
    o = project(snap, 0.0, 0.0)
    pg.end_grain(o[0], o[1])
    for d in snap["keepers"]:                                      # Glo on the press: behind everyone
        if d["back"]:
            _keeper(pg, snap, d, t)
    for d in sorted([d for d in snap["keepers"] if 0.0 < d["depth"] < 1.0], key=lambda d: -d["depth"]):
        _keeper(pg, snap, d, t)                                    # in the doorway, deepest first
    _hall_door(pg, snap)
    pg.begin_grain()
    _mirror(pg, snap, t)
    pg.end_grain(o[0], o[1])
    for d in snap["keepers"]:
        if not d["back"] and d["depth"] <= 0.0:
            _keeper(pg, snap, d, t)


# ----------------------------------------------------------------------------------------------- the village

def _sky(pg, snap, t):
    W, H = snap["W"], snap["H"]
    z = snap["zoom"]
    pg.grad(_poly([(0, 0), (W, 0), (W, H), (0, H)]), VIL["sky_top"], VIL["sky_low"])
    rs = np.random.default_rng(61)
    for _ in range(140):                                          # stars, fixed to the far sky
        x, y = rs.uniform(-1500, 7000), rs.uniform(-1700, -500)
        sx, sy = project(snap, x, y + 1080, 0.1)
        if -10 < sx < W + 10 and -10 < sy < H:
            tw = 0.65 + 0.35 * math.sin(t * rs.uniform(0.6, 1.6) + rs.uniform(0, 6.3))
            pg.flat(oval(sx, sy, rs.uniform(1.2, 2.4) * max(z, 0.8), rs.uniform(1.2, 2.4) * max(z, 0.8)),
                    VIL["star"], 0.75 * tw)
    mx, my = project(snap, 1450.0, snap["cy"] - 430.0 / max(z, 0.5), 0.1)
    pg.flat(oval(mx, my, 90 * z, 90 * z), VIL["moon"], 0.18, blur=30)
    pg.flat(oval(mx, my, 44 * z, 44 * z), VIL["moon"])
    pg.flat(oval(mx - 12 * z, my - 8 * z, 9 * z, 9 * z), tone(VIL["moon"], -0.06))


def _hills(pg, snap, par, y, amp, col, seed):
    W, H = snap["W"], snap["H"]
    vx0, vx1 = _view_x(snap, par)
    rs = np.random.default_rng(seed)
    ph = rs.uniform(0, 6.3, 3)
    pts = []
    for x in np.linspace(vx0 - 300, vx1 + 300, 40):
        h = amp * (0.55 * math.sin(x / 900 + ph[0]) + 0.3 * math.sin(x / 430 + ph[1]) + 0.15 * math.sin(x / 210 +
                                                                                                         ph[2]))
        pts.append(project(snap, x, y - h, par))
    pts += [(pts[-1][0], H + 10), (pts[0][0], H + 10)]
    pg.flat(smooth(pts[:-2], closed=False) if False else _poly(pts), col)


def _hill_door(pg, snap, t):
    """The hill the factory is built into, with the NIGHT SHIFT door (Hill in halloween.py: door HILL_X+120..+420)."""
    from .tune_up import DOOR_W, HILL_X
    from .animal_houses import G
    z = snap["zoom"]
    d0, d1 = HILL_X + 120, HILL_X + 120 + DOOR_W
    hill = [(HILL_X - 260, G), (HILL_X - 120, G - 620), (HILL_X + 300, G - 820), (HILL_X + 900, G - 900),
            (HILL_X + 1500, G - 860), (HILL_X + 1900, G)]
    pg.shape(smooth([project(snap, *p) for p in hill], closed=True), VIL["rock"], 0.1)
    for (x, y, rx, ry) in ((HILL_X + 60, G - 520, 60, 26), (HILL_X + 700, G - 700, 80, 30),
                           (HILL_X + 1100, G - 480, 70, 28), (HILL_X + 560, G - 300, 50, 20)):
        sx, sy = project(snap, x, y)
        pg.flat(oval(sx, sy, rx * z, ry * z), VIL["rock2"])
    _box(pg, snap, d0 - 30, G - 600, d1 + 30, G, tone(VIL["rock"], -0.12), 0.0, r=10)
    _box(pg, snap, d0, G - 560, d1, G, "#3b2e28", 0.0)
    _box(pg, snap, d0 + 60, G - 470, d1 - 60, G, "#7a5c40", 0.0, alpha=0.55)
    _box(pg, snap, d0 - 40, G - 640, d1 + 40, G - 600, HALL["steel2"], 0.06, r=4)
    sx, sy = project(snap, (d0 + d1) / 2, G - 611)
    _text(pg, "NIGHT SHIFT", sx, sy, 24 * z, HALL["sign"], 0.9)


def _cottage(pg, snap, x, spec, glow=1.0):
    """A little house (the hedgehog's, the bunny's) in the flat look: walls in its own colour, a roof, a lit
    rounded door and (the bunny's) a round window."""
    from .animal_houses import G
    z = snap["zoom"]
    w, h, roof = spec.w, spec.h, spec.roof
    col = tuple(int(v) for v in spec.color)
    _box(pg, snap, x - w / 2, G - h, x + w / 2, G, col, 0.1, r=4)
    rp = [project(snap, x - w / 2 - 14, G - h + 4), project(snap, x, G - h - roof),
          project(snap, x + w / 2 + 14, G - h + 4)]
    pg.shape(smooth(rp, closed=True), tone(col, -0.22), 0.06)
    dr = spec.hole_r
    dx, dy = project(snap, x, G - dr * 1.05)
    door = rrect(dx - dr * z, dy - dr * 1.1 * z, dx + dr * z, dy + dr * 1.05 * z, dr * z)
    pg.flat(door, VIL["window"], 0.9 * glow)
    pg.flat(oval(dx, dy, dr * 2.4 * z, dr * 2.2 * z), VIL["window"], 0.18 * glow, blur=16 * z)
    if spec.window:
        wx, wy = project(snap, x + w * 0.3, G - h * 0.62)
        pg.flat(oval(wx, wy, 13 * z, 13 * z), VIL["window"], 0.9 * glow)


def _birdhouse(pg, snap, x, y, spec, t, j):
    z = snap["zoom"]
    w, h, roof = spec.w * 0.8, spec.h * 0.8, spec.roof * 0.8
    col = tuple(int(v) for v in spec.color)
    _box(pg, snap, x - w / 2, y - h, x + w / 2, y, col, 0.1, r=3)
    rp = [project(snap, x - w / 2 - 8, y - h + 3), project(snap, x, y - h - roof), project(snap, x + w / 2 + 8,
                                                                                         y - h + 3)]
    pg.shape(smooth(rp, closed=True), tone(col, -0.25), 0.05)
    hx, hy = project(snap, x, y - h * 0.6)
    pg.flat(oval(hx, hy, spec.hole_r * 0.8 * z, spec.hole_r * 0.8 * z), "#2a2230")
    from .animal_houses import BIRD_COLS
    out = 0.6 + 0.4 * math.sin(t * 1.1 + j * 1.7)
    bc = tuple(int(v) for v in BIRD_COLS[j][0])
    pg.flat(oval(hx + 3 * out * z, hy + 3 * z, 8.5 * z, 8.5 * z), bc)
    pg.flat(oval(hx + 5 * out * z, hy + 1 * z, 2.2 * z, 2.2 * z), "#141418")


def _village(pg, snap, t):
    from .animal_houses import BUNNY_X, G, HEDGE_X, POST_TOP, POSTS
    from .props import SPECS
    from .tune_up import BUSH
    vx0, vx1 = _view_x(snap)
    z = snap["zoom"]
    _sky(pg, snap, t)
    _hills(pg, snap, 0.35, G - 380, 160, VIL["far"], 3)
    _hills(pg, snap, 0.55, G - 250, 120, VIL["far2"], 5)
    for j, x in enumerate(np.arange(-1200, 7000, 330)):              # the forest behind the village
        if vx0 - 400 < x < vx1 + 400:
            sx, sy = project(snap, x, G - 30, 0.85)
            lolly_tree(pg, sx, sy, (520 + 90 * ((j * 7) % 4)) * z * 0.85, VIL["mid"], tone(VIL["trunk"], -0.2))
    pg.begin_grain()
    _box(pg, snap, vx0 - 300, G, vx1 + 300, G + 800, VIL["ground"], 0.0)
    _box(pg, snap, vx0 - 300, G, vx1 + 300, G + 14, VIL["ground2"], 0.0)
    if vx0 - 1000 < 1880:                                             # the treehouse
        sx, sy = project(snap, 1400.0, G)
        treehouse(pg, sx, sy, 1500 * z)
    for j, x in enumerate((-300, 300, 3900)):
        if vx0 - 400 < x < vx1 + 400:
            sx, sy = project(snap, x, G)
            lolly_tree(pg, sx, sy, (900 + 60 * (j % 3)) * z, VIL["leaf"], VIL["trunk"])
    _hill_door(pg, snap, t)
    for k_ in range(4):                                               # the four birdhouses on their posts
        px = POSTS[k_]
        if vx0 - 200 < px < vx1 + 200:
            _box(pg, snap, px - 13, POST_TOP, px + 13, G + 30, VIL["trunk"], 0.08)
            _box(pg, snap, px - 34, POST_TOP - 8, px + 34, POST_TOP, tone(VIL["trunk"], 0.06), 0.0)
            _birdhouse(pg, snap, px, POST_TOP - 8, SPECS[k_], t, k_)
    for bx, r in ((HEDGE_X - 40, 120), (HEDGE_X + 90, 90), (BUNNY_X + 40, 140), (BUNNY_X - 120, 100)):
        if vx0 - 300 < bx < vx1 + 300:
            sx, sy = project(snap, bx, G - r * 0.45)
            flat_bush(pg, sx, sy + r * 0.45 * z, r * z, VIL["leaf2"])
    _cottage(pg, snap, HEDGE_X, SPECS[4], glow=0.0)
    _cottage(pg, snap, BUNNY_X, SPECS[5], glow=0.0)
    o = project(snap, 0.0, 0.0)
    pg.end_grain(o[0], o[1])
    night_tint(pg)
    _cottage_lights(pg, snap, HEDGE_X, SPECS[4])
    _cottage_lights(pg, snap, BUNNY_X, SPECS[5])
    _hill_light(pg, snap)


def night_tint(pg, mul=(0.62, 0.68, 0.86)):
    """Moonlight over the scenery drawn so far: everything a little darker and cooler (multiply)."""
    col = skia.Color(int(255 * mul[0]), int(255 * mul[1]), int(255 * mul[2]))
    pg.c.drawPaint(skia.Paint(Color=col, BlendMode=skia.BlendMode.kMultiply))


def _cottage_lights(pg, snap, x, spec):
    from .animal_houses import G
    z = snap["zoom"]
    dr = spec.hole_r
    dx, dy = project(snap, x, G - dr * 1.05)
    pg.flat(oval(dx, dy, dr * 2.6 * z, dr * 2.4 * z), VIL["window"], 0.22, blur=18 * z)
    pg.flat(rrect(dx - dr * z, dy - dr * 1.1 * z, dx + dr * z, dy + dr * 1.05 * z, dr * z), VIL["window"], 0.92)
    if spec.window:
        wx, wy = project(snap, x + spec.w * 0.3, G - spec.h * 0.62)
        pg.flat(oval(wx, wy, 13 * z, 13 * z), VIL["window"], 0.92)


def _hill_light(pg, snap):
    from .tune_up import DOOR_W, HILL_X
    from .animal_houses import G
    z = snap["zoom"]
    d0, d1 = HILL_X + 120, HILL_X + 120 + DOOR_W
    gx, gy = project(snap, (d0 + d1) / 2, G - 220)
    pg.flat(oval(gx, gy, 200 * z, 280 * z), VIL["door_glow"], 0.16, blur=36 * z)


def _bush_front(pg, snap):
    from .tune_up import BUSH
    from .animal_houses import G
    z = snap["zoom"]
    x, r = BUSH
    pg.begin_grain()
    for dx, k, f in ((-40, 0.8, 0.0), (50, 0.75, 0.04), (0, 1.0, 0.02)):
        sx, sy = project(snap, x + dx, G)
        flat_bush(pg, sx, sy, r * k * z, tone(VIL["leaf2"], f))
    o = project(snap, 0.0, 0.0)
    pg.end_grain(o[0], o[1])


def bunny_flat(cv_pg, snap, x, y, s, hop, face):
    """A storybook-cute bunny (soft grey-brown, white tummy and tail), sitting or mid-hop."""
    z = snap["zoom"] * s
    sx, sy = project(snap, x, y - hop)
    f = face
    pg = cv_pg
    body = "#b9a698"
    pg.shape(oval(sx, sy - 26 * z, 34 * z, 26 * z), body, 0.12)
    pg.flat(oval(sx + 10 * f * z, sy - 22 * z, 16 * z, 16 * z), "#efe6dc")
    pg.flat(oval(sx - 30 * f * z, sy - 32 * z, 11 * z, 11 * z), "#f6f1ea")
    hx, hy = sx + 26 * f * z, sy - 52 * z
    for e, a in ((-0.25, 0.0), (0.12, 0.25)):
        ex = hx + (e * 22 - 4) * f * z
        pg.shape(oval(ex, hy - 34 * z, 7.5 * z, 24 * z, (a - 0.12) * f * 40), body, 0.1)
        pg.flat(oval(ex, hy - 34 * z, 3.6 * z, 17 * z, (a - 0.12) * f * 40), "#e9b9b0")
    pg.shape(oval(hx, hy, 21 * z, 18 * z), body, 0.1)
    pg.flat(oval(hx + 9 * f * z, hy - 3 * z, 4.6 * z, 5.2 * z), "#2a201c")
    pg.flat(oval(hx + 10.4 * f * z, hy - 4.6 * z, 1.5 * z, 1.5 * z), "#ffffff")
    pg.flat(oval(hx + 19 * f * z, hy + 3 * z, 3.4 * z, 2.6 * z), "#d98e8a")
    pg.flat(oval(hx + 5 * f * z, hy + 6 * z, 4 * z, 2.5 * z), "#e9b9b0", 0.5)
    for dx in (-14, 14):
        pg.flat(oval(sx + dx * z, sy - 2 * z, 10 * z, 5 * z), tone(body, -0.05))


def hedgehog_flat(pg, snap, x, y, s, face, curl, t):
    """The hedgehog: a round spiny back (scalloped, warm brown), a pale face with a pointed snout; curl 1 = a tight
    ball (face tucked in), 0 = uncurled and looking up."""
    z = snap["zoom"] * s
    sx, sy = project(snap, x, y)
    f = face
    k = curl
    r = 34 * z
    cyb = sy - r * (0.95 + 0.1 * k)
    spikes = []
    n = 22
    for i in range(n + 1):
        a = math.pi * (1.0 + i / n) if k < 0.5 else 2 * math.pi * i / n
        rr = r * (1.18 if i % 2 == 0 else 1.0)
        spikes.append((sx + rr * math.cos(a) * (1.25 - 0.25 * k), cyb + rr * math.sin(a) * (0.85 + 0.15 * k)))
    if k < 0.5:
        spikes += [(sx + r * 1.25, sy - 2 * z), (sx - r * 1.25, sy - 2 * z)]
    pg.shape(smooth(spikes, closed=True), "#8a6448", 0.12)
    if k < 0.98:
        a = 1 - k
        hx = sx + f * r * (0.95 + 0.25 * a)
        hy = sy - r * 0.45
        pg.shape(oval(hx, hy, 20 * z * a + 4 * z, 15 * z * a + 3 * z), "#e9d6bf", 0.1)
        pg.flat(oval(hx + f * 19 * z * a, hy + 1 * z, 4 * z * a + 0.5, 3.6 * z * a + 0.5), "#2a201c")
        pg.flat(oval(hx + f * 3 * z, hy - 4 * z, 3.4 * z * a + 0.3, 3.8 * z * a + 0.3), "#2a201c")
        pg.flat(oval(hx + f * 3.8 * z, hy - 5.2 * z, 1.1 * z * a, 1.1 * z * a), "#ffffff")
        for dx in (-0.5, 0.5):
            pg.flat(oval(sx + dx * r, sy - 3 * z, 7 * z * a + 0.5, 4 * z * a + 0.5), "#c9a888")
    else:
        pg.flat(oval(sx + f * r * 0.6, sy - r * 0.5, 6 * z, 5 * z), "#e9d6bf")


def _bird(pg, snap, t, wave_t):
    from .animal_houses import G
    lt = snap["lt"]
    if lt < wave_t - 2:
        return
    bx = 2000 + 150 * (lt - wave_t + 2)
    by = G - 560 - 40 * math.sin((bx - 2000) / 300.0)
    z = snap["zoom"]
    sx, sy = project(snap, bx, by)
    flap = 0.5 + 0.5 * math.sin(lt * 13)
    pg.shape(oval(sx, sy, 15 * z, 10 * z), "#c86a4a", 0.1)
    pg.flat(oval(sx + 12 * z, sy - 5 * z, 8 * z, 7 * z), "#c86a4a")
    pg.flat(oval(sx + 14 * z, sy - 6 * z, 1.6 * z, 1.6 * z), "#1a1414")
    pg.flat(_poly([(sx + 19 * z, sy - 5 * z), (sx + 25 * z, sy - 3 * z), (sx + 19 * z, sy - 2 * z)]), "#e0b050")
    wy = sy - (14 * flap - 4) * z
    pg.flat(_poly([(sx - 6 * z, sy - 2 * z), (sx + 6 * z, sy - 2 * z), (sx - 2 * z, wy)]), "#a85238")


def _fireflies(pg, snap, t):
    from .animal_houses import G
    rs = np.random.default_rng(77)
    z = snap["zoom"]
    for _ in range(40):
        x0, y0 = rs.uniform(1500, 4600), rs.uniform(G - 560, G - 40)
        ph, sp = rs.uniform(0, 6.3), rs.uniform(0.15, 0.4)
        x = x0 + 60 * math.sin(t * sp + ph)
        y = y0 + 30 * math.sin(t * sp * 1.7 + ph * 2)
        a = 0.5 + 0.5 * math.sin(t * 1.3 + ph * 3)
        sx, sy = project(snap, x, y)
        pg.flat(oval(sx, sy, 9 * z, 9 * z), "#d8f08a", 0.18 * a, blur=5)
        pg.flat(oval(sx, sy, 2.4 * z, 2.4 * z), "#eefcb0", 0.8 * a)


def draw_home(pg, snap):
    from .animal_houses import G
    t = snap["lt"]
    _village(pg, snap, t)
    bx, hop, face = snap["bunny"]
    pg.begin_grain()                                   # each animal's grain travels with it
    bunny_flat(pg, snap, bx, G, 1.35, hop, face)
    pg.end_grain(*project(snap, bx, G - hop))
    _bush_front(pg, snap)
    hx, face_h, curl = snap["hog"]
    pg.begin_grain()
    hedgehog_flat(pg, snap, hx, G, 1.0, face_h, curl, t)
    pg.end_grain(*project(snap, hx, G))
    for d in sorted([d for d in snap["keepers"] if 0.0 < d["depth"] < 1.0], key=lambda d: -d["depth"]):
        _keeper(pg, snap, d, t)
    for d in snap["keepers"]:
        if d["depth"] <= 0.0:
            _keeper(pg, snap, d, t)
    _fireflies(pg, snap, t)
    _bird(pg, snap, t, snap["wave_t"])


# ----------------------------------------------------------------------------------------------- the end sign

def draw_sign(pg, snap):
    """The end card: the village at night, everyone in a row with their names, the sign (as in every flat episode)."""
    t = snap["lt"]
    from .christmas_flat import PAPER
    _village(pg, snap, t + 400.0)
    for d in snap["keepers"]:
        _keeper(pg, snap, d, t)
    a = snap.get("names", 1.0)
    W = snap["W"]
    for d in snap["keepers"]:
        from .chatter import TOPS
        hop = 75.0 if d["kind"] == "springs" else 0.0             # above Springs' happy hops (advisor FK0022 r2)
        x, y = project(snap, d["x"], d["y"] - TOPS[d["kind"]] * d["k"] - 40 - hop)
        nm = NAMES[d["kind"]]
        from .christmas_flat import _font
        f = _font(26, "Bold")
        w = f.measureText(nm) + 26
        pg.flat(rrect(x - w / 2, y - 30, x + w / 2, y + 8, 10), NAME_COL[d["kind"]], 0.92 * a)
        _text(pg, nm, x, y - 3, 26, PAPER, a)
    bw, bh = 940, 220
    x0, y0 = (W - bw) / 2, 120
    pg.flat(rrect(x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10, 26), (40, 28, 24), 0.25 * a, blur=10)
    pg.flat(rrect(x0, y0, x0 + bw, y0 + bh, 26), (150, 108, 72), a)
    pg.flat(rrect(x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14, 18), (176, 132, 90), a)
    _text(pg, "WHAT SHOULD THEY DO NEXT?", W / 2, y0 + 108, 58, PAPER, a)
    _text(pg, "Tell us in the comments", W / 2, y0 + 168, 34, (250, 232, 200), a, weight="Medium")


# ----------------------------------------------------------------------------------------------- bubbles, frame

def draw_bubbles(pg, snap):
    from .chatter import bubble
    z = snap["zoom"]
    for b in snap["bubbles"]:
        if b["r"] < 2:
            continue
        bx, by = project(snap, b["x"], b["y"])
        tx, ty = project(snap, *b["tail"])
        r = b["r"] * z
        il.creature(pg, lambda cv, bx=bx, by=by, r=r, b=b, tx=tx, ty=ty: bubble(cv, bx, by, r, b["icon"],
                                                                                 (214, 196, 176), 1.0, (tx, ty)),
                    bx, by)


WALKS = None


def set_walks(trk):
    """Build the flat walks once per process from tracks(snaps) (they need each Keeper's whole path)."""
    global WALKS
    WALKS = Walks(trk) if trk else None


def draw(snap):
    pg = ZoomPage(int(snap["W"]), int(snap["H"]))
    pg.zoom = snap["zoom"]
    act = snap["act"]
    if act == "hall":
        draw_hall(pg, snap)
    elif act == "home":
        draw_home(pg, snap)
    elif act == "comment_sign":
        draw_sign(pg, snap)
    else:
        raise ValueError(f"no flat drawing for act {act}")
    if act != "comment_sign":
        draw_bubbles(pg, snap)
    rgb = pg.finish()
    f = snap["fade"]
    if f > 0.001:
        rgb = (rgb.astype(np.float32) * (1 - f)).astype(np.uint8)
    return rgb


# ----------------------------------------------------------------------------------------------- the shockwave

def wave_radius(u, W, H, cx, cy):
    """How far the ring has rolled at u 0..1: from the orb to past the furthest corner of the picture (it starts
    quick and eases out, so the Keepers by the beacon change first and the far factory last)."""
    far = max(math.hypot(x - cx, y - cy) for x in (0, W) for y in (0, H)) + 160
    e = 1 - (1 - u) ** 2.2
    return far * e


def shockwave(old, flat, u, cx, cy, edge=(255, 236, 190)):
    """The beacon's shockwave: a ring of light rolling out from (cx, cy) (screen px). Inside it the flat picture,
    outside the old one; the ring itself is a soft warm band of light with a faint shimmer just behind it."""
    H, W = old.shape[:2]
    if u <= 0.0:
        return old
    if u >= 1.0:
        return flat
    r = wave_radius(u, W, H, cx, cy)
    ys = np.arange(H, dtype=np.float32)[:, None]
    xs = np.arange(W, dtype=np.float32)[None, :]
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    w = 26.0 + 30.0 * u                                              # the band widens as it travels
    inside = np.clip((r - d) / 10.0 + 0.5, 0.0, 1.0)                 # a soft (antialiased) edge
    out = old.astype(np.float32) * (1 - inside[..., None]) + flat.astype(np.float32) * inside[..., None]
    band = np.exp(-((d - r) / w) ** 2)
    trail = np.exp(-np.clip(r - d, 0, None) / (4 * w)) * (d < r) * 0.35     # a little light left behind it
    fade = 1.0 - 0.55 * u                                            # it softens as it rolls away
    k = ((0.55 * band + 0.25 * trail) * fade)[..., None]
    out = out * (1 - k) + np.array(edge, np.float32)[None, None, :] * k
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def orb_screen(snap):
    """The beacon's orb on screen in this frame (the wave starts there)."""
    from .tune_switch import ORB
    return project(snap, *ORB)


def wave_from_screen(snap):
    from .tune_switch import WAVE_FROM
    return project(snap, *WAVE_FROM)


# ----------------------------------------------------------------------------------------------- the page turn

def page_turn(old, flat, u):
    """A page of the old picture turns over from the right edge to the left (a storybook page), showing the flat
    picture beneath. The turning part shows the page's back (warm paper) with a soft fold shadow. u 0..1."""
    H, W = old.shape[:2]
    if u <= 0.0:
        return old
    if u >= 1.0:
        return flat
    e = u * u * (3 - 2 * u)
    # the fold line: from the right edge, sweeping past the left; a little slanted (the page curls from its corner)
    fx = W * (1.0 - 1.35 * e) + 0.0
    slant = 0.18 * W * math.sin(math.pi * e)
    ys = np.arange(H, dtype=np.float32)
    fold = fx + slant * (ys / H - 0.5)[:, None]                     # x of the fold at each row
    xs = np.arange(W, dtype=np.float32)[None, :]
    # the turned-over flap: it lies left of the fold, as wide as the page has turned (mirror of the turned part)
    turned = (W - fold)                                              # how much of the page has gone past the fold
    flap_w = np.minimum(turned * 0.55, fold + 50)                    # it lifts, so it looks narrower
    revealed = xs >= fold                                            # behind the fold: the new page
    on_flap = (xs < fold) & (xs >= fold - flap_w)
    out = np.where(revealed[..., None], flat, old).astype(np.float32)
    # the flap: warm paper, lighter towards its fold, a soft shadow it throws on the old page beside it
    d = np.clip((fold - xs) / np.maximum(flap_w, 1.0), 0, 1)        # 0 at the fold .. 1 at the flap's edge
    paper = np.array([238, 229, 208], np.float32)
    shade = (0.78 + 0.22 * (1 - d) ** 0.6)[..., None]               # light at the fold, darker where it curls up
    flap = paper[None, None, :] * shade                              # (no texture: it would slide over the page)
    out = np.where(on_flap[..., None], flap, out)
    # shadow on the old page left of the flap, and on the new page right of the fold
    sh_l = np.clip((fold - flap_w - xs) / 60.0, 0, 1)
    sh_l = np.where(xs < fold - flap_w, 1 - 0.25 * np.exp(-((fold - flap_w - xs) / 50.0) ** 2), 1.0)
    sh_r = np.where(revealed, 1 - 0.35 * np.exp(-((xs - fold) / 70.0) ** 2), 1.0)
    out *= (sh_l * sh_r)[..., None]
    # a thin bright edge along the fold
    edge = np.exp(-((xs - fold) / 2.0) ** 2) * on_flap
    out = out + edge[..., None] * 20
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)
