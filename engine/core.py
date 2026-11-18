"""Formats, palettes and seeded randomness shared by every family."""
from dataclasses import dataclass
import hashlib

import numpy as np


# ---------- output formats ----------

@dataclass(frozen=True)
class Format:
    name: str
    width: int    # output pixels
    height: int
    fps: int = 60

    @property
    def scale(self):
        """Pixels per scene unit. Scenes are authored so the short side = 1080 units."""
        return min(self.width, self.height) / 1080.0

    @property
    def units(self):
        """(width, height) in scene units."""
        return self.width / self.scale, self.height / self.scale

    @property
    def vertical(self):
        return self.height > self.width


FORMATS = {
    "short": Format("short", 1080, 1920),
    "hd": Format("hd", 1920, 1080),
    "4k": Format("4k", 3840, 2160),
    "hd30": Format("hd30", 1920, 1080, 30),        # slow ambient long-form
    "short30": Format("short30", 1080, 1920, 30),  # slow Shorts (Deep Sky): no need for 60 fps
    "4k30": Format("4k30", 3840, 2160, 30),
    # quick previews while tuning params
    "short_preview": Format("short_preview", 540, 960, 30),
    "hd_preview": Format("hd_preview", 960, 540, 30),
}


# ---------- palettes (RGB hex, neon on black) ----------

PALETTES = {
    "neon": ["#00f0ff", "#ff2bd6", "#7b5cff", "#39ff88", "#ffd23f", "#ff6b35"],
    "christmas": ["#ff4a4a", "#3fe07f", "#ffd166", "#ff4a4a", "#3fe07f", "#ffd166", "#ff4a4a", "#3fe07f", "#ffd166",
                  "#ff4a4a", "#3fe07f", "#ffd166"],   # red, green, gold: one each per pendulum of 12
    "ornaments": ["#ff4a4a", "#ffd166", "#6fb6ff", "#f4f0ff", "#ff7ac8", "#ffd166", "#ff4a4a", "#6fb6ff", "#f4f0ff",
                  "#ffd166", "#ff7ac8", "#ff4a4a"],   # tree ornaments: red, gold, blue, silver, pink (no green on green)
    "crackers": ["#ff4a4a", "#ffd166", "#5fd38a", "#6fb6ff", "#ff7ac8", "#f4f0ff", "#f4f0ff", "#ff7ac8", "#6fb6ff",
                 "#5fd38a", "#ffd166", "#ff4a4a"],   # Christmas crackers: pendulum k and 11-k share a colour (one cracker)
    "stockings": ["#ffd166", "#ff4a4a", "#6fb6ff", "#f4f0ff", "#ff7ac8", "#5fd38a", "#ff4a4a", "#6fb6ff", "#f4f0ff",
                  "#ff7ac8", "#5fd38a", "#ff4a4a"],   # the longest pendulum alone is gold; the rest stocking colours
    "candy": ["#ff4a4a", "#f4f0ff", "#ff4a4a", "#f4f0ff", "#ff4a4a", "#f4f0ff", "#ff4a4a", "#f4f0ff", "#ff4a4a",
              "#f4f0ff", "#ff4a4a", "#f4f0ff"],   # candy cane: red and white, one each per pendulum of 12
    # Same three Christmas colours as "christmas", GREEN FIRST. New key, not a change to
    # "christmas", so every published render still reproduces under --redo.
    # Why it exists: a races course always has `pegs` as section 0, and section colour cycles by
    # section INDEX (families/races/scene.py: sec_cols[sec % len]). So the opening screenful and
    # the cover - which crops to the start box and the top of the peg field - are ALWAYS
    # palette[0], whatever the rest of the list holds. On "christmas" that is red, which is why a
    # blind screener read our Christmas covers as Valentine's. The red and gold are NOT missing
    # from those videos: BL30079 measures red 3.0% / green 3.4% / gold 3.8% of lit pixels at
    # mid-race. It is only the first screen that is one colour. Use this key when the opening and
    # the cover should read Christmas rather than the gate colour deciding it.
    "christmas_tree": ["#3fe07f", "#ff4a4a", "#ffd166", "#3fe07f", "#ff4a4a", "#ffd166", "#3fe07f",
                       "#ff4a4a", "#ffd166", "#3fe07f", "#ff4a4a", "#ffd166"],
    # Valentine's. Blush FIRST on purpose: a races course always has `pegs` as section 0 and
    # section colour cycles by section index, so palette[0] is the opening screen and the cover.
    # Every other red-ish palette we have starts on nearly the same red (candy #ff4a4a, sunset
    # #ff3864, synthwave #ff2a6d, lava #ff2e63), which is how two Shorts ended up looking like
    # one video in the December batch. This one opens on soft pink instead, so a Valentine's
    # batch can hold more than one romantic palette without the covers repeating.
    "valentine": ["#ffb3d1", "#ff5fa2", "#ff2e63", "#fff0f5", "#ffd166", "#c353ff"],
    "golden": ["#ffd166", "#ffb347", "#fff1c1", "#ffc857", "#ffe29a", "#f6a54c"],   # warm Christmas-light golds
    "synthwave": ["#ff2a6d", "#d1f7ff", "#05d9e8", "#ff9f1c", "#b967ff", "#01ffc3"],
    "aurora": ["#00ffa3", "#00c2ff", "#6e5bff", "#c353ff", "#ff5ec4", "#7dffda"],
    "valentine": ["#ff3b6b", "#ff6f91", "#ff9ebb", "#ffc6d9", "#e0245e", "#ff85a2"],
    "sunset": ["#ff3864", "#ff7b54", "#ffb26b", "#ffd56f", "#c84bff", "#ff4fa3"],
    "ice": ["#9be7ff", "#55c6ff", "#3d8bff", "#a28bff", "#e0f7ff", "#5cffe4"],
    "lava": ["#ff2e63", "#ff7a00", "#ffcc00", "#ff4ecd", "#b51dff", "#ff5f40"],
    "evergreen": ["#2fe07a", "#7dff6a", "#1fd0a0", "#a8ff5a", "#3cff9a", "#c8ff7a"],   # Christmas tree greens
    "autumn": ["#e8590c", "#d6301e", "#f59f00", "#c2410c", "#b91c1c", "#eab308"],     # amber, maple red, gold
    "rainbow": ["#ff3b3b", "#ff9f1a", "#ffe62e", "#3dff6e", "#2ee6ff", "#3d6bff", "#b03dff", "#ff3dc8"],
    # Foundry engine: one accent per station, in line order (furnace/pour, cooling, stamping,
    # conveyor, paint, assembly) - see docs/engines/foundry.md
    "foundry": ["#ff8a1f", "#4fa3c7", "#1fc7a8", "#c9a227", "#8e5cff", "#f2e8d5"],
    # Sandglass engine (light background): peach, sage, lavender, sky, butter, rose pastels, then the
    # deeper accents terracotta, teal, plum - see docs/engines/sandglass.md
    "sandglass": ["#F4B393", "#A8C3A0", "#B9A7D9", "#9EC9E8", "#F3D98B", "#E8A1B0",
                  "#C8735A", "#5E9C9A", "#7E6A9E"],
    # Chain Reaction engine (lamp-lit wooden table): walnut table, light wood, paper, brass, then the muted
    # painted-domino colors brick, mustard, sage, slate blue, cream, charcoal - see docs/engines/chain_reaction.md
    "chain_reaction": ["#5A3E2B", "#C89B6D", "#EFE6D2", "#C9A24A", "#B5523B", "#D9A441", "#7E9F7A",
                       "#5B7A99", "#F1E9D8", "#3B3634"],
    # Tiny World engine (cozy island diorama): shallow sea, deep sea, sand, grass, dark grass, path stone, wood,
    # cream walls, terracotta / slate-blue / mustard / sage roofs, window glow - see docs/engines/tiny_world.md
    "tiny_world": ["#7FD1CF", "#3E8FB0", "#F2DDB0", "#9CC66B", "#6FA35A", "#D8CDBB", "#B98A5E", "#F4EBDD",
                   "#D9785B", "#6B88A8", "#E3B04B", "#8DAE8A", "#FFD27A"],
}


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)


def palette(name, n=None):
    """List of RGB float arrays (0-255). With n, cycles/interpolates to n colors."""
    cols = [hex_rgb(c) for c in PALETTES[name]]
    if n is None:
        return cols
    if n <= len(cols):
        return cols[:n]
    return [gradient(cols, i / max(1, n - 1)) for i in range(n)]


def gradient(cols, u):
    """Sample a palette as a smooth gradient, u in [0, 1]."""
    u = float(np.clip(u, 0, 1)) * (len(cols) - 1)
    i = min(int(u), len(cols) - 2)
    f = u - i
    return cols[i] * (1 - f) + cols[i + 1] * f


def hot(c, amount=0.5):
    """Push a color toward white - for the bright core of a neon stroke."""
    return np.asarray(c) * (1 - amount) + 255 * amount


def dim(c, k):
    return np.asarray(c) * k


# ---------- seeded randomness ----------

def make_rng(seed, stream="main"):
    """Independent, reproducible RNG streams: same (seed, stream) -> same numbers.

    Separate streams keep e.g. audio randomness from shifting physics when one
    of them changes.
    """
    h = hashlib.sha256(f"{seed}:{stream}".encode()).digest()
    return np.random.default_rng(int.from_bytes(h[:8], "little"))
