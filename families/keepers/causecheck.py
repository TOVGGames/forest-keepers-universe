"""Cause-and-effect continuity check for the Forest Keepers flat episodes (FK remake session 3, 2026-11-07).

Why: the owner turned down FK0021 The Harvest Feast for mistakes that storycheck (positions, jumps, holds, limbs)
could not see. They were all about cause and effect, and what the viewer can see:
- the acorn hitting Digs was tiny and inside Glo's tendrils;
- Digs threw each hole's soil into the other hole;
- the corner that fell off was the one opposite Twigs' blade, and the gear teeth weren't where the blade was;
- Glo hovered in front of the mill, and the acorns showed through him;
- Twigs took six steps to slice the dough, and the slices turned into round rolls by themselves;
- the bread went into the oven through its wall;
- a basket hid the lanterns lighting up;
- the animals came out through their house walls.
He asked for "some kind of new continuity check or some kind of new advisor". This is the check, and it runs on the
plan before anything is rendered. The advisor (advisor.py: fresh agents and speech-to-text on the rendered file)
runs after.

An episode feeds it per frame. Each kind of record is a count that must be 0:

  effect_off_tool   effect(label, effect_xy, cause_xy, tol): a change (a cut, a notch, a mark) happens where the
                    tool touches it, within tol px.
  dump_in_hole      dump(label, heap_rect, holes): soil or offcuts dropped where another hole (or job) is.
  action_hidden     view(label, focus_rect, blockers): something not taking part in the action (a Keeper's body,
                    a held basket) covers more than `cover` of what the viewer must see, for more than `hold` s.
  see_through       layer(front, back): something drawn over another thing that is in front of it (its depth
                    says it is further away), where the two overlap.
  form_snap         form(name, param, value): a thing's shape, cut, bake... changes faster than `rate` a second
                    (a change happens as the work goes, never all at once).
  form_no_cause     ...or changes while nothing works on it (cause=False).
  through_wall      wall(label, rect, opening): something partly hidden by a wall that is not inside the opening it
                    goes in or out by (a thing passes through a door, never the wall beside it).
  too_small         size(label, px, min_px): a story moment's subject is smaller on screen than min_px.
  shuffle_steps     shuffles(walks): three little walks (< 70 px) by one Keeper within 8 s. A small reach is
                    done with the arm, not with steps.

Each problem keeps the first few cases as (time, ...) for the report.
"""
from collections import defaultdict

# A Keeper's body on screen (the part that hides things behind it), from its feet (Glo: from his y):
# (half width, top, bottom) at k = 0.72 (measured off illustrate.figure, flat look). Arms and legs are left out
# (they're thin and move); Hans' body is his head and mantle, not his tentacles.
BODY = {"wheels": (75, -236, -60), "tentacles": (110, -309, -120), "teeth": (62, -350, -160),
        "springs": (72, -206, -90), "lantern": (70, -246, -90), "digger": (100, -202, -50)}


def body_box(kd, x, y, k=0.72):
    hw, top, bot = BODY[kd]
    s = k / 0.72
    return (x - hw * s, y + top * s, x + hw * s, y + bot * s)


def area(r):
    return max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])


def inter(a, b):
    return (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))


def inside(a, b, tol=2.0):
    """Is rect a inside rect b (to within tol px)?"""
    return a[0] >= b[0] - tol and a[1] >= b[1] - tol and a[2] <= b[2] + tol and a[3] <= b[3] + tol


class CauseCheck:
    def __init__(self, dt):
        self.dt = dt
        self.found = defaultdict(list)
        self.runs = {}                               # (label, who) -> frames in a row it has been covering
        self.last = {}                               # (name, param) -> value last frame

    def _add(self, kind, case):
        self.found[kind].append(case)

    def effect(self, t, label, effect_xy, cause_xy, tol=18.0):
        d = ((effect_xy[0] - cause_xy[0]) ** 2 + (effect_xy[1] - cause_xy[1]) ** 2) ** 0.5
        if d > tol:
            self._add("effect_off_tool", (round(t, 2), label, round(d)))

    def dump(self, t, label, heap, holes):
        for name, h in holes:
            if area(inter(heap, h)) > 0:
                self._add("dump_in_hole", (round(t, 2), label, name))

    def view(self, t, label, focus, blockers, cover=0.25, hold=0.4):
        fa = area(focus) or 1.0
        for who, r in blockers:
            key = (label, who)
            if area(inter(focus, r)) / fa > cover:
                self.runs[key] = self.runs.get(key, 0) + 1
                if self.runs[key] * self.dt > hold and self.runs[key] * self.dt <= hold + self.dt + 1e-9:
                    self._add("action_hidden", (round(t - hold, 2), label, who))
            else:
                self.runs[key] = 0

    def layer(self, t, front, back, min_overlap=0.12):
        """front = (name, rect, depth) drawn after back = (name, rect, depth); depth: bigger is nearer."""
        (fn, fr, fd), (bn, br, bd) = front, back
        ov = area(inter(fr, br))
        if ov > min_overlap * min(area(fr) or 1.0, area(br) or 1.0) and fd < bd - 10:
            self._add("see_through", (round(t, 2), fn, bn))

    def form(self, t, name, param, value, cause=True, rate=10.0):
        """rate: the fastest it may change, per second (a 0..1 change in a tenth of a second at the most)."""
        key = (name, param)
        v0 = self.last.get(key)
        self.last[key] = value
        if v0 is None:
            return
        d = abs(value - v0)
        if d > rate * self.dt + 1e-6:
            self._add("form_snap", (round(t, 2), name, param, round(v0, 2), round(value, 2)))
        elif d > 1e-6 and not cause:
            self._add("form_no_cause", (round(t, 2), name, param))

    def wall(self, t, label, rect, opening):
        if not inside(rect, opening):
            self._add("through_wall", (round(t, 2), label))

    def size(self, t, label, px, min_px):
        if px < min_px:
            self._add("too_small", (round(t, 2), label, round(px)))

    def shuffles(self, walks, gap=8.0, short=70.0):
        """walks: {who: [(t0, x0), (t1, x1), ...]} (pairs of keys per walk)."""
        for who, keys in walks.items():
            small = [t0 for (t0, x0), (t1, x1) in zip(keys, keys[1:]) if t1 > t0 + 1e-6 and 1.0 < abs(x1 - x0) < short]
            for a, b in zip(small, small[2:]):                     # three little walks in a row: a shuffle
                if b - a < gap:
                    self._add("shuffle_steps", (round(a, 2), who))

    KINDS = ("effect_off_tool", "dump_in_hole", "action_hidden", "see_through", "form_snap", "form_no_cause",
             "through_wall", "too_small", "shuffle_steps")

    def report(self):
        counts = {k: len(self.found.get(k, ())) for k in self.KINDS}
        first = {k: self.found[k][:6] for k in self.KINDS if self.found.get(k)}
        return counts, first
