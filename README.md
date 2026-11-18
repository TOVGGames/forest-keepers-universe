# Forest Keepers: a parallel universe

This is a starting copy of the Forest Keepers code from the Dissociate State project, taken on 2026-11-18. It's yours: change anything, rename anything. Nothing here connects to the original channel, and nothing you do here changes it.

## What's in it

- `families/keepers/` holds every Forest Keepers episode's code.
  - `talk/` is the newest format: Keepers who stand, look and talk, with a voice each. Episode 1, "How the Forest Keepers Began", is `talk/ep1.py` (the script and voices) and `talk/ep1_film.py` (the pictures).
  - The older files (`*_flat.py`, `winter_ready.py`, `raft_race.py`, ...) are earlier episodes in earlier styles.
- `engine/` is the shared drawing, audio and video code the episodes use. `engine/assets/fonts` has the font.
- `audio/` has the music and sound synth code and three sample tracks.
- `narration/` has the voice settings. `keepers_cast_voices.yaml` lists which ElevenLabs voice each Keeper uses.
- `renders/forest_keepers_talk/ep1/` has episode 1's recorded voices and timings, so episode 1 renders without paying for new voices.
- `docs/engines/` has the design notes and pictures from the original series. Read them for ideas. They also mention the original channel's rules and sessions; those don't apply here.

## Setup (Windows)

1. Install Python 3.12 from python.org. Tick "Add python.exe to PATH".
2. Install ffmpeg: `winget install Gyan.FFmpeg`.
3. In this folder, run:

   ```
   python -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   The `wgpu` and `numba` lines aren't needed for Forest Keepers; skip them if they fail to install.

## Try it

Stills from episode 1 (chapter:second). They land in `renders\forest_keepers_talk\ep1\stills`:

```
.venv\Scripts\python.exe -m families.keepers.talk.ep1_film --still 1:30 4:20
```

The whole episode (8.5 minutes; it takes a while):

```
.venv\Scripts\python.exe -m families.keepers.talk.ep1_film --render
```

## Voices

Making new voices needs your own ElevenLabs account. Put its API key in `secrets\elevenlabs_key.txt`, one line. Never commit that folder; `.gitignore` already keeps it out. Every new line spoken uses credits, and recorded lines are cached so they're only paid for once.
