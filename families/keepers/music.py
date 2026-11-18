"""The Forest Keepers theme (owner, 2026-10-27): lighthearted, upbeat and all-ages, carried by a music box from
the first second to the last, inside and outside. A real little tune, not random notes: an 8-bar theme in C major
over I-vi-IV-V, a B part, and a quiet bar-rest section so it never wears out, with a soft
bouncy bass pluck (root + fifth) and a warm pad (synth.keepers_song_bed) following the same chords.

Every note stays inside MIDI 36-96 (CLAUDE.md). The music box sits at C4-E5, the bass at E2-D3.
"""

BPM = 104.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
EIGHTH = BEAT / 2

# pad voicings (warm, close, around middle C) and bass roots
PAD = {"C": [48, 55, 60, 64], "Am": [45, 52, 57, 60], "F": [41, 48, 53, 57], "G": [43, 50, 55, 59],
       "Em": [40, 47, 52, 55], "Dm": [50, 53, 57, 62]}
ROOT = {"C": 48, "Am": 45, "F": 41, "G": 43, "Em": 40, "Dm": 38}

_ = None
# the theme, one bar of eighth notes per line (None = rest)
A = [("C", [76, _, 79, _, 84, _, 79, 76]),
     ("Am", [81, _, 84, _, 81, 79, 76, _]),
     ("F", [77, _, 81, _, 84, _, 81, 77]),
     ("G", [79, _, _, 83, 86, _, 83, _]),
     ("C", [76, _, 79, _, 84, _, 79, 76]),
     ("Am", [81, _, 84, 88, 84, 81, 79, _]),
     ("F", [77, 81, 84, 81, 79, _, 77, 76]),
     ("C", [72, _, 76, _, 72, _, _, _])]
B = [("F", [84, _, 84, 81, 84, _, 86, _]),
     ("G", [83, _, 79, _, 74, _, 79, _]),
     ("Em", [76, 79, 83, 79, 76, _, 74, _]),
     ("Am", [72, _, 76, _, 81, _, _, _]),
     ("F", [77, _, 81, _, 84, _, 81, _]),
     ("G", [79, _, 83, _, 86, _, 83, 79]),
     ("C", [84, _, 79, _, 76, _, 79, _]),
     ("C", [72, _, _, _, _, _, _, _])]
REST = [("C", None), ("Am", None), ("F", None), ("G", None), ("C", None), ("Am", None), ("F", None), ("G", None)]
# A, A, B, A, then 8 quiet bars of pad + bass + a bell now and then. Played an octave down (C4-E5): warm, round
# music box with almost nothing above 1 kHz (owner hears bright 1-5 kHz as harsh)
FORM = [(A, -12), (A, -12), (B, -12), (A, -12), (REST, -12)]

# a second B part for episodes that get their own variant (owner 2026-10-30: every video its own soundtrack)
C = [("F", [72, _, 74, _, 77, _, 74, 72]),
     ("C", [76, _, 74, 72, _, _, 67, _]),
     ("Dm", [74, _, 77, _, 81, _, 79, 77]),
     ("G", [79, _, _, _, 74, _, _, _]),
     ("F", [77, _, 79, _, 81, _, 84, _]),
     ("C", [79, _, 76, _, 72, _, 76, _]),
     ("Dm", [74, _, 77, _, 76, _, 74, _]),
     ("G", [71, _, 74, _, 79, _, _, _])]
# a tiptoeing, curious part for the Bug Hunt (episode 10): short notes with rests, like peeking under things
D = [("C", [79, _, _, 76, 79, _, _, 76]),
     ("F", [77, _, 81, _, _, _, 77, _]),
     ("Dm", [74, _, 77, _, 81, _, 77, 74]),
     ("G", [79, _, _, _, 83, _, _, _]),
     ("Am", [76, _, _, 72, 76, _, _, 72]),
     ("F", [77, _, 81, _, 84, _, 81, _]),
     ("G", [79, _, 83, _, 79, _, 74, _]),
     ("C", [72, _, _, _, 76, _, _, _])]
# per-episode variants of the theme: key (semitones up), tempo and form
VARIANTS = {None: (0, BPM, FORM),
            "tuneup": (5, 96.0, [(A, -12), (C, -12), (B, -12), (A, -12), (REST, -12), (C, -12)]),
            "bughunt": (2, 100.0, [(A, -12), (D, -12), (B, -12), (D, -12), (REST, -12), (A, -12), (C, -12)]),
            # the narrated night walk: slower, in E, more quiet bars so the narrator has room
            "nightwalk": (4, 88.0, [(A, -12), (REST, -12), (C, -12), (REST, -12), (D, -12), (REST, -12), (B, -12),
                                     (REST, -12)]),
            # a new friend from the factory: in G, a little brighter, the curious part and the second B part
            "newfriend": (7, 98.0, [(A, -12), (C, -12), (D, -12), (B, -12), (REST, -12), (A, -12), (C, -12)]),
            # getting ready for winter: narrated, so quiet bars for her; in D, a little slower, the B part first
            "winterready": (2, 90.0, [(B, -12), (REST, -12), (A, -12), (REST, -12), (C, -12), (REST, -12), (D, -12),
                                      (REST, -12)]),
            # Sprout's Christmas tree (ep 14): narrated, in E flat, a touch slower and cosier, the second B part
            # first, quiet bars for her
            "christmastree": (3, 86.0, [(C, -12), (REST, -12), (A, -12), (B, -12), (REST, -12), (D, -12), (REST, -12),
                                        (A, -12), (C, -12), (REST, -12)]),
            # the river raft race (ep 8, flat remake): narrated, in A, a little brisker for a race, the curious part
            # second, quiet bars for her
            "raftrace": (9, 100.0, [(A, -12), (D, -12), (REST, -12), (B, -12), (C, -12), (REST, -12), (A, -12),
                                    (B, -12), (REST, -12)]),
            # the harvest feast (ep 9, flat remake): narrated, in B flat (warm, a little lower), slow and cosy, the
            # second B part first, many quiet bars for her
            "harvestfeast": (-2, 90.0, [(C, -12), (REST, -12), (A, -12), (D, -12), (REST, -12), (B, -12), (A, -12),
                                        (REST, -12)]),
            # who's awake tonight (ep 11, flat remake): narrated, in D flat (soft for the night), the slowest
            # yet, the curious part first, a quiet bar after every part for her
            "whosawake": (1, 84.0, [(D, -12), (REST, -12), (A, -12), (REST, -12), (B, -12), (REST, -12), (C, -12),
                                     (A, -12), (REST, -12)])}


def bars(form=FORM):
    """Endless sequence of (chord, melody or None, octave shift)."""
    while True:
        for section, octave in form:
            for chord, mel in section:
                yield chord, mel, octave


def compose(track, t0, t1, gain=1.0, rng=None, variant=None):
    """Write the song into `track` from t0 to t1 (seconds) and return the pad chord timeline for the bed.
    The last bar is a held C chord with a little rising arpeggio, so the video ends on home. `variant` picks the
    episode's own key, tempo and form (VARIANTS)."""
    key, bpm, form = VARIANTS[variant]
    BEAT = 60.0 / bpm
    BAR, EIGHTH = 4 * BEAT, BEAT / 2
    PADK = {ch: [n + key for n in v] for ch, v in PAD.items()}
    ROOTK = {ch: n + key for ch, n in ROOT.items()}
    chords = []
    t = t0
    n = 0
    for chord, mel, octave in bars(form):
        if t + 2 * BAR > t1:
            break
        chords.append([t, BAR, PADK[chord]])
        root = ROOTK[chord]
        # bass: root on 1, fifth on 3, a soft pickup on the "and" of 4 in every other bar
        track.hit(t, "pluck", root, 0.34 * gain)
        track.hit(t + 2 * BEAT, "pluck", root + 7, 0.26 * gain)
        if n % 2 == 1:
            track.hit(t + 3.5 * BEAT, "pluck", root + 12, 0.16 * gain)
        if mel is not None:
            for i, note in enumerate(mel):
                if note is None:
                    continue
                accent = 1.0 if i % 4 == 0 else 0.78
                track.hit(t + i * EIGHTH, "music_box", note + octave + key, 0.27 * gain * accent,
                          0.2 * (1 if i % 2 else -1))
        elif n % 2 == 0:
            tone = PADK[chord][-1] + (7 if n % 4 == 0 else 0)
            track.hit(t + BEAT * 0.5, "music_box", min(tone, 72 + key), 0.16 * gain, -0.2)
        t += BAR
        n += 1
    # home: a held C with a rising arpeggio
    chords.append([t, max(BAR, t1 - t), PADK["C"]])
    track.hit(t, "pluck", ROOTK["C"], 0.34 * gain)
    for i, note in enumerate(n + key for n in (60, 64, 67, 72)):
        track.hit(t + i * EIGHTH, "music_box", note, 0.28 * gain, 0.3 * (i - 1.5) / 1.5)
    return chords
