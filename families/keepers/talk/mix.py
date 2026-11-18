"""Mouths and music for the talking format (owner 2026-11-17, docs/engines/forest_keepers_talk_handoff.md).

Mouths:
- A mouth follows the loudness of its own lines.
- It runs until the sound of the line is over, then closes slowly ("you can still hear them after their mouth is done
  moving").
- Small leads at the start: Sprout 0.08 s, Springs 0.04 s, Digs 0 (Sprout's mouth "a millisecond behind").
- Glo has no mouth; she talks with her lantern (lantern()).

Music: the ORIGINAL theme only, families/keepers/music.py VARIANTS[None] (C major, 104 bpm). The other variants are
what changed the key on the owner. "As far as the key, I like it where it's at"; never change the music without
asking him.
- It is down for a whole conversation: a gap under HOLD s between lines does not bring it up.
- It starts down LEAD s before the first word, is DUCK_DB down while down, and comes back up over RISE s, only in a
  real silence.
- The voices sit VOICE_OVER_DB above its full level.
"""
import numpy as np

SR = 44100
LEAD = {"sprout": 0.08, "springs": 0.04, "digs": 0.0}
HOLD_FRAME = 0.78            # how much of a mouth's opening carries over to the next frame (0 = shuts at once)
VOICE_OVER_DB, DUCK_DB = 2.0, 9.0
HOLD, MUSIC_LEAD, RISE = 4.0, 1.8, 4.0


class Mouths:
    """How open each speaker's mouth is, frame by frame, from the chapter's voice track and cues."""

    def __init__(self, voices, cues, fps):
        self.cues, self.fps = cues, fps
        hop = SR // fps
        n = len(voices) // hop + 2
        e = np.array([np.sqrt(np.mean(voices[i * hop:(i + 1) * hop] ** 2)) if (i + 1) * hop <= len(voices) else 0.0
                      for i in range(n)])
        e = np.clip(e / (np.percentile(e[e > 0], 92) or 1.0), 0, 1.2)
        for i in range(1, len(e)):
            e[i] = max(e[i], e[i - 1] * HOLD_FRAME)
        self.env = e

    def open(self, who, t):
        """0..1, inside `who`'s own lines only, a little ahead of the sound at the start, never ending before it."""
        lead = LEAD.get(who, 0.04)
        h = self.env
        for c in self.cues:
            if c["who"] == who and c["start"] - lead - 0.03 <= t <= c["end"] + 0.4:
                i = min(int((t + lead) * self.fps), len(h) - 2)
                if t + lead > c["end"] + 0.1:                       # the line is over: only the slow close is left
                    i = min(int(t * self.fps), len(h) - 2)
                e = 0.25 * h[max(i - 1, 0)] + 0.5 * h[i] + 0.25 * h[i + 1]
                return float(min(1.0, e * 1.15))
        return 0.0

    def speaking(self, who, t):
        return any(c["who"] == who and c["start"] <= t <= c["end"] for c in self.cues)


def conversations(cues):
    """The stretches of talk (lines closer than HOLD apart), [(start, end)] in seconds."""
    talks, cur = [], None
    for c in cues:
        if cur and c["start"] - cur[1] < HOLD:
            cur[1] = c["end"]
        else:
            cur = [c["start"], c["end"]]
            talks.append(cur)
    return [tuple(x) for x in talks]


def duck_mask(cues, n, sr=SR):
    """0 = music at full level, 1 = music down: down early before talk, back up slowly only in real silences."""
    t = np.arange(n) / sr
    mask = np.zeros(n)
    for a, b in conversations(cues):
        down = np.clip((t - (a - MUSIC_LEAD)) / (MUSIC_LEAD - 0.25), 0, 1)
        up = np.clip(((b + 0.4 + RISE) - t) / RISE, 0, 1)
        ramp = np.minimum(down, up)
        mask = np.maximum(mask, ramp * ramp * (3 - 2 * ramp))
    return mask


def theme(end, path, t0=0.6):
    """The original theme, untouched, from t0 to end - 0.5 s -> (wav path, chords, folded notes)."""
    from engine.audio import EventTrack
    from families.keepers import music
    track = EventTrack(1)
    key, bpm, _ = music.VARIANTS[None]
    assert (key, bpm) == (0, 104.0), "the original theme: C major, 104 bpm (owner 2026-11-17)"
    chords = music.compose(track, t0, end - 0.5, variant=None)
    bed = {"type": "procedural", "name": "keepers_song", "gain": 1.0, "chords": chords,
           "reverb": {"decay": 3.5, "wet": 0.4, "tone": 2600}}
    return track.render(end, bed=bed, path=path), chords, list(track.folded)


def mix(voices_stereo, music_stereo, cues):
    """-> (mix, mask): the voices over the theme by the rule above, normalised to -1 dBFS peak."""
    n = len(music_stereo)
    v = np.vstack([voices_stereo, np.zeros((max(0, n - len(voices_stereo)), 2), np.float32)])[:n]
    said = np.zeros(n, bool)
    for c in cues:
        said[int(c["start"] * SR):int(c["end"] * SR)] = True
    rms = lambda x: float(np.sqrt(np.mean(np.square(x))) + 1e-12)
    gv = rms(music_stereo) * 10 ** (VOICE_OVER_DB / 20) / rms(v[said])
    mask = duck_mask(cues, n)
    out = music_stereo * (10 ** (-DUCK_DB * mask / 20))[:, None] + v * gv
    return out / (np.max(np.abs(out)) + 1e-9) * 0.89, mask


def lantern(mouths, t, base=1.0):
    """Glo talks with her lantern: it brightens a little with her voice (she has no mouth)."""
    return base * (1.0 + 0.3 * mouths.open("glo", t))


def blink(t, phase):
    p = (t + phase) % 4.6
    return max(0.0, 1 - abs(p - 0.1) / 0.1) if p < 0.2 else 0.0


def ease(t, a, b):
    u = min(1.0, max(0.0, (t - a) / (b - a)))
    return u * u * (3 - 2 * u)
