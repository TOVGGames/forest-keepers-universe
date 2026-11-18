"""Base class every family scene implements."""
from .core import make_rng


class Scene:
    # audio defaults - override in the family or via params["audio"]
    bed = None            # e.g. {"type": "procedural", "name": "ambient", "gain": 0.6}
    reverb = None         # event reverb, see EventTrack.render
    events_gain = 1.0

    def __init__(self, params, seed, fmt, track):
        self.p = params
        self.seed = seed
        self.fmt = fmt
        self.track = track
        self.w, self.h = fmt.units
        self.rng = make_rng(seed, "scene")
        self.done = False         # set True when the "story" is over; engine adds the outro
        self.stats = {}           # anything worth logging (winner, bounces...)

    # engine hooks
    def canvas_options(self):
        return {}

    def update(self, t, dt):
        raise NotImplementedError

    def draw(self, cv, t, frame):
        raise NotImplementedError

    def flash(self, t):
        """0..1 white flash amount for this frame (big moments)."""
        return 0.0
