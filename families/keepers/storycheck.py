"""Forest Keepers physics checks for the storybook episodes (owner, FK0012 review 2026-11-04: "this is the kind of
lazy animation that I'm not going to accept. It's got to be much better... much more realistic, the physics").
The full list of what went wrong in FK0012 is in docs/engines/forest_keepers_fk0012_audit.md; each rule below is
one kind of mistake from it, and an episode renders only with every count at 0.

Every frame the episode tells the checker what it draws (Check.frame):

  things  {id: Thing} every loose object (an acorn, a seed, a branch, a leaf, the sun) under ONE id for its whole
          life, whoever holds it: on the stump, in Sprout's hand, falling, on the pile, in the chipmunk's pouch.
          - thing_jumps: its velocity changes by more than DV in one frame (it warped to a new spot);
          - size_snaps / size_drift: its drawn size changes (in one frame, or over its life) - nothing grows in a
            hand, nothing shrinks going into a den; a thing that really grows says so (grows="seedling sprouting")
            and is let off the drift, but never the snap;
          - pops: it appears without a visible source (born="cut off the branch by Twigs") or vanishes without a
            visible place it went (gone=("eaten", mouth xy), checked to be right there).
          - unheld_motion: it moves (in the world, not just with the camera) with nothing moving it: it must be
            held (held=(who, contact xy), checked to be touching it) or say how it moves by itself (moves="falls",
            "rolls", "flies", "walks") (owner, FK0015 review 2026-11-05: "the grass just warps into his hands from
            nowhere");
          - paper_thin: a side-view drawing turning round by squashing its width (flat = its width now / its full
            width) is never seen thinner than PAPER while in view (owner, FK0015: "when it turns around it is
            obviously paper thin") - turn it out of sight, or another way;
          - crab_walk: a Keeper walking (walk=(px/s, heading -1..1)) faster than CRAB_V must have turned to face the
            way it goes (heading at least CRAB_TURN that way) (owner, FK0015: "the way they all walk sideways looks
            too robotic... they need to be able to turn laterally to walk").
          - water_snap: an animal going into or out of water (wet = the share of it below the water line, 0..1)
            changes that share smoothly, never faster than WET_RATE per second, and never steps out of the water
            onto the bank in a jump (owner, FK0016 approval 2026-11-05: "the beaver comes up halfway out of the water
            and then just warps clear onto the land... goes from being full to half a beaver being underwater, just
            warps right into it"). It climbs out or slides in, its position moving with it (thing_jumps too).
  limbs   [Limb] every arm, leg and tentacle drawn: rigid limbs (bones, sticks, metal) keep 0.85-1.15 of their rest
          length (limb_stretch); stretchy ones (Hans' tentacles) reach at most 2x (owner: "maybe a 2-time stretch,
          but not a 6x stretch"), and we aim for 1.6.
          - hans_tentacles: Hans has 8 tentacles in all, never more (owner 2026-11-06: "if his legs are 6, he can
            only use 2. If he wants to use a 3rd or a 4th, some of his leg ones need to pull up and get used... 8 is
            the max"). Every frame, his limbs named leg / arm / tentacle / working tentacle are counted; a leg that
            lifts to work is reported once (as the working tentacle, not also as a leg).
  layers  [(name, z, bbox)] in paint order, z = distance from the camera (bigger is farther). A farther thing painted
          over a nearer one where they overlap is depth_order (owner: the far, tiny geese "flew in front of a very
          close tree").
  sizes   [(name, real_cm, drawn_px, z)] animals and props with a real size: two at the same depth must keep
          their real size ratio, softened for the storybook (ratio ** SOFTEN), within SIZE_BAND (scale_mismatch: a
          black bear drawn barely bigger than a chipmunk).
  helps   [Help] a Keeper's helping move says what it is for: the obstacle it moves must really overlap the path of
          the one it helps (no_reason: "he was moving a branch that wasn't in the way").
  focus   (name, bbox) the action the camera is showing; nearer things may cover at most HIDE of it (hidden_action:
          the beaver taking its branch behind the cart and Twigs' legs).

Check.report() -> {rule: count} plus the first few examples of each, for the render log and the warnings.
"""
import math
import re
from dataclasses import dataclass, field

DV = 600.0              # px/s: a thing whose velocity changes more than this in one frame has jumped (scene.PROP_DV)
SNAP = 0.03             # a size change of more than 3 % in one frame is a snap
DRIFT = 1.12            # over its whole life a thing's size may vary by at most 12 % (wobble, squash) unless it grows
RIGID = (0.85, 1.15)
STRETCH_MAX = 2.0       # owner
STRETCH_AIM = 1.6
SOFTEN = 0.6            # storybook: real size ratios are compressed to ratio ** 0.6 (a bear 7.5x a chipmunk -> 3.4x)
SIZE_BAND = (0.6, 1.7)  # drawn ratio / softened real ratio
SAME_Z = 0.15           # two things within 15 % of each other's depth stand at the same depth
HIDE = 0.35             # nearer things may cover at most 35 % of the action in focus
GONE_NEAR = 2.0         # a thing that goes somewhere must be within 2 sizes (or 30 px) of it when it vanishes
STILL_V = 25.0          # px/s (world): slower than this a thing counts as lying still
HOLD_NEAR = 1.5         # a held thing is within 1.5 sizes (or 20 px) of what holds it
PAPER = 0.5             # never thinner than half its width while in view
CRAB_V, CRAB_TURN = 25.0, 0.6
HANS_MAX = 8            # Hans' tentacles in all (legs + working ones)
HANS = ("Hans", "tentacles")
WET_RATE = 1.5          # share of the body per second into / out of the water (all the way takes at least 0.67 s)


@dataclass
class Thing:
    x: float
    y: float
    size: float                   # drawn radius / height in px, in the same units every frame
    z: float = 1.0
    born: str = None              # the visible cause it appeared ("cut off the branch"), on its first frame
    gone: tuple = None            # (reason, (x, y)) on its last frame: where it visibly went
    grows: str = None             # why its size changes, if it really does
    hidden: bool = False          # out of sight (under water, inside a pocket): still tracked, but may turn round
    held: tuple = None            # (who, (x, y)) what is moving it right now, and where it touches it
    moves: str = None             # how it moves by itself ("falls", "walks", "flies", ...)
    screen: bool = False          # drawn in screen space (the sky, the snow): the camera does not move it
    flat: float = None            # a turning side-view drawing: its width now / its full width
    walk: tuple = None            # a Keeper: (speed px/s in the world, heading -1..1 its legs face)
    wet: float = None             # an animal at the water: the share of it below the water line (0 dry .. 1 under)


@dataclass
class Limb:
    who: str
    name: str
    root: tuple
    tip: tuple
    rest: float                   # its length at rest (straight, root to tip)
    stretchy: bool = False
    length: float = None          # its drawn length along its curve, if it bends (else root to tip is used)


# promise_line (owner, SX0023 review 2026-11-05, docs/PRODUCTION.md): the narrator never announces the payoff as
# "the promise" ("and now the thing we promised", "here's what we waited for"); the payoff simply arrives.
PROMISE_WORDS = re.compile(r"\b(promis\w*|waited|waiting for|been waiting|as we said|like we said|we told you|"
                           r"here it is|the moment we|finally,? here|now for the)\b", re.I)


def script_check(texts):
    """Every narration line that announces the payoff as the promise (all must be 0)."""
    return [(t, m.group(0)) for t in texts for m in [PROMISE_WORDS.search(t)] if m]


@dataclass
class Help:
    helper: str
    action: str
    obstacle: tuple               # bbox (x0, y0, x1, y1) of what is moved, before it is moved
    path: tuple                   # bbox swept by the one helped where it passes the obstacle


def overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0.0, w) * max(0.0, h)


def area(a):
    return max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])


def covered(box, covers, n=24):
    """Fraction of box covered by the union of boxes (sampled on an n x n grid)."""
    if area(box) <= 0 or not covers:
        return 0.0
    hit = 0
    for i in range(n):
        x = box[0] + (i + 0.5) / n * (box[2] - box[0])
        for j in range(n):
            y = box[1] + (j + 0.5) / n * (box[3] - box[1])
            if any(c[0] <= x <= c[2] and c[1] <= y <= c[3] for c in covers):
                hit += 1
    return hit / (n * n)


@dataclass
class Check:
    examples: int = 4
    found: dict = field(default_factory=dict)
    _prev: dict = field(default_factory=dict)       # id -> (t, Thing, vx, vy)
    _sizes: dict = field(default_factory=dict)      # id -> [min, max, grows]
    _last: dict = field(default_factory=dict)       # (rule, key) -> t of the last report (one per stretch of time)
    _t0: float = None
    _done: bool = False
    limb_worst: dict = field(default_factory=dict)  # (who, limb) -> (t, length / rest) furthest from 1

    RULES = ("thing_jumps", "size_snaps", "size_drift", "pops", "unheld_motion", "paper_thin", "crab_walk",
             "water_snap", "limb_stretch", "hans_tentacles", "depth_order", "scale_mismatch", "no_reason",
             "hidden_action")

    def _hit(self, rule, key, t, what, gap=0.5):
        k = (rule, key)
        if t - self._last.get(k, -math.inf) > gap:
            self.found.setdefault(rule, []).append((round(t, 2), *what))
        self._last[k] = t

    def frame(self, t, dt, things=None, limbs=(), layers=(), sizes=(), helps=(), focus=None, cam=None):
        """cam: the camera's x shift this frame (things are in screen px); with it, motion is judged in the world."""
        if self._t0 is None:
            self._t0 = t
        pcam, self._cam = getattr(self, "_cam", None), cam
        things = things or {}
        # things: one id for the whole life
        for name in list(self._prev):
            if name not in things:
                pt, p, _, _ = self._prev.pop(name)
                if p.gone is None:
                    self._hit("pops", name, t, (name, "vanished", round(p.x), round(p.y)))
                else:
                    gx, gy = p.gone[1]
                    d = math.hypot(gx - p.x, gy - p.y)
                    if d > max(GONE_NEAR * p.size, 30.0):
                        self._hit("pops", name, t, (name, f"vanished {round(d)} px from where it went ({p.gone[0]})"))
        for name, th in things.items():
            p = self._prev.get(name)
            if p is None:
                if th.born is None and t > self._t0 + 1e-6:
                    self._hit("pops", name, t, (name, "appeared", round(th.x), round(th.y)))
                self._prev[name] = (t, th, None, None)
                self._sizes.setdefault(name, [th.size, th.size, th.grows])
                continue
            pt, pth, pvx, pvy = p
            vx, vy = (th.x - pth.x) / dt, (th.y - pth.y) / dt
            if pvx is not None and math.hypot(vx - pvx, vy - pvy) > DV and not (th.hidden or pth.hidden):
                self._hit("thing_jumps", name, t, (name, (round(pth.x), round(pth.y)), (round(th.x), round(th.y))))
            if cam is not None and pcam is not None:              # moving in the world, with nothing moving it
                dc = 0.0 if th.screen else cam - pcam
                v = math.hypot(th.x + dc - pth.x, th.y - pth.y) / dt
                if v > STILL_V and not (th.hidden or pth.hidden) and th.moves is None and pth.moves is None:
                    if th.held is None and pth.held is None:
                        self._hit("unheld_motion", name, t, (name, f"moves {round(v)} px/s, nothing holds it"))
                    elif th.held is not None and math.hypot(th.held[1][0] - th.x, th.held[1][1] - th.y) > \
                            max(HOLD_NEAR * th.size, 20.0):
                        self._hit("unheld_motion", name, t, (name, f"{th.held[0]} is not touching it"))
            if th.flat is not None and th.flat < PAPER and not th.hidden:
                self._hit("paper_thin", name, t, (name, f"{round(100 * th.flat)} % of its width"))
            if th.walk is not None and abs(th.walk[0]) > CRAB_V and th.walk[1] * math.copysign(1, th.walk[0]) < CRAB_TURN:
                self._hit("crab_walk", name, t, (name, f"walks {round(th.walk[0])} px/s facing {th.walk[1]:.2f}"))
            if th.wet is not None and pth.wet is not None and abs(th.wet - pth.wet) / dt > WET_RATE:
                self._hit("water_snap", name, t, (name, f"{round(100 * pth.wet)} % -> {round(100 * th.wet)} % "
                                                        f"under water in one frame"))
            if pth.size > 0 and abs(th.size / pth.size - 1) > SNAP:      # even a growing thing grows smoothly
                self._hit("size_snaps", name, t, (name, round(pth.size, 1), round(th.size, 1)))
            s = self._sizes[name]
            s[0], s[1] = min(s[0], th.size), max(s[1], th.size)
            s[2] = s[2] or th.grows
            self._prev[name] = (t, th, vx, vy)
        # limbs
        for lb in limbs:
            L = lb.length if lb.length is not None else math.hypot(lb.tip[0] - lb.root[0], lb.tip[1] - lb.root[1])
            r = L / max(lb.rest, 1e-6)
            bad = r > STRETCH_MAX if lb.stretchy else not (RIGID[0] <= r <= RIGID[1])
            w = self.limb_worst.get((lb.who, lb.name))
            if w is None or abs(math.log(r)) > abs(math.log(w[1])):
                self.limb_worst[(lb.who, lb.name)] = (round(t, 2), round(r, 2))
            if bad:
                self._hit("limb_stretch", (lb.who, lb.name), t, (lb.who, lb.name, round(r, 2)))
        n_hans = sum(1 for lb in limbs if lb.who in HANS and re.match(r"(leg|arm|working tentacle|tentacle)", lb.name))
        if n_hans > HANS_MAX:
            self._hit("hans_tentacles", "Hans", t, ("Hans", f"{n_hans} tentacles drawn (8 at most)"))
        # depth: a farther thing painted over a nearer one
        for j, (nj, zj, bj) in enumerate(layers):
            for ni, zi, bi in layers[:j]:
                if zj > zi * (1 + 1e-3) and overlap(bi, bj) > 0.02 * min(area(bi), area(bj)):
                    self._hit("depth_order", (nj, ni), t, (f"{nj} (z {zj:g}) painted over {ni} (z {zi:g})",))
        # sizes at the same depth
        for j, (nj, cj, pj, zj) in enumerate(sizes):
            for ni, ci, pi, zi in sizes[:j]:
                if abs(zj - zi) > SAME_Z * min(zi, zj):
                    continue
                want = (cj / ci) ** SOFTEN
                got = pj / pi
                q = got / want
                if not (SIZE_BAND[0] <= q <= SIZE_BAND[1]):
                    self._hit("scale_mismatch", (nj, ni), t,
                              (f"{nj} drawn {got:.2f}x {ni}, should be about {want:.2f}x",), gap=1e9)
        for h in helps:
            if overlap(h.obstacle, h.path) <= 0:
                self._hit("no_reason", (h.helper, h.action), t, (h.helper, h.action), gap=1e9)
        if focus is not None:
            fname, fbox, fz = focus
            covers = [b for n, z, b in layers if z < fz * (1 - 1e-3)]
            c = covered(fbox, covers)
            if c > HIDE:
                self._hit("hidden_action", fname, t, (fname, f"{round(100 * c)} % hidden"), gap=2.0)

    def finish(self):
        if self._done:
            return
        self._done = True
        for name, (lo, hi, grows) in self._sizes.items():
            if lo > 0 and hi / lo > DRIFT and not grows:
                self.found.setdefault("size_drift", []).append((name, round(lo, 1), round(hi, 1)))

    def report(self):
        self.finish()
        counts = {r: len(self.found.get(r, [])) for r in self.RULES}
        first = {r: self.found[r][:self.examples] for r in self.RULES if self.found.get(r)}
        return counts, first

    def warn(self):
        counts, first = self.report()
        for r, n in counts.items():
            if n:
                print(f"  WARNING storycheck {r}: {n} (first: {first[r]})", flush=True)
        return counts
