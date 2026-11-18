# Forest Keepers flat remakes: briefs for the extra build sessions

The owner approved, via Don's Asks on 2026-11-06 (main 6af944ac), a second and third FK build session in parallel: "yes, even a third if needed".
The "Forest Keepers v2 local render" session builds Tune-Up (the page-turn switch). Each brief below is one session's
whole task. Start each session in **its own worktree**, then paste the brief.

## Shared brief (every remake session)

Read these first:
- `docs/engines/forest_keepers.md`: all rules, especially "Natural walks, from ep 14 on", `promise_line` and `water_snap`.
- The old episode's doc and module: the story to keep.
- The flat engine:
  - `families/keepers/flat.py`, `flat_motion.py` (`WaveGait`, `arm_swing`, `roll_swing`), and `illustrate.py` (figure style=6);
  - `storycheck.py`;
  - `winter_flat.py` + `winter_flat_world.py` (ep 13, approved) and `christmas_flat*.py` + `christmas_*.py` (ep 14) as worked examples;
  - `experiments/keepers_flat/ep14.py` as the runner template: `--times`, `--stills`, `--check`, `--render`, resumable segments, log ID, filing.

Episode facts:
- Six Keepers only (Wheels, Hans, Twigs, Springs, Glo, Digs). Sprout arrives in ep 12 (New Friend), so Sprout appears only from there on.
- The new faces apply: Hans smiling with no beard, Twigs' rounded grin.
- Narration uses `families/keepers/narrator.py` (cached ElevenLabs takes; the key is in `secrets/`). Never use the Lindsay voice.
- Give each episode its own music variant in `families/keepers/music.py`, never another episode's track.

Rules:
- Put new code in NEW files only, for example `families/keepers/<name>_flat.py`, `<name>_flat_world.py` and `experiments/keepers_flat/ep<N>.py`.
- Do not edit the shared files: `families/foundry/products/monster.py`, `flat_motion.py`, `storycheck.py`, `illustrate.py`, `flat.py`, `music.py` (except adding your own variant entry).
- If you need a shared change, ask "Forest Keepers v2 local render" through Local Operations.

Done means all of the following:
- Storycheck is at 0 (teleports, `thing_jumps`, `limb_stretch`, `reach_miss`, `size_drift`, wall clips, walk-through, `water_snap`, `promise_line`).
- You did a frame-by-frame self-review of stills: no lazy animation, nothing warping or changing by magic, the action shown, screen text in screen space.
- Races follow sports realism: the whole race on screen, real technique, no kingmaker ending, the winner never thrown first.
- The render is filed in `renders/Forest Keepers/`. Every render runs at **Below Normal** priority with 2 threads left free. Ask Local Operations before a full render, because several FK sessions share this PC.
- There are 4-6 thumbnails, none showing a race winner, screened by a fresh agent with no context.
- A HANDOFF entry is in `publish/HANDOFF.md`, "awaiting owner review", per `docs/PRODUCTION.md`. It has a "Forest Keepers" title, the AI-voice line, Altered content No, Not made for kids, and a Promise -> payoff line.
- The review ask (clickable links, the exact upload title) goes to Local Operations by SendMessage. Never edit `publish/OWNER_QUEUE.md`, and never ask the owner in your own chat.
- Push to main after a fetch and merge, never force-push, committing only your own paths.
- Slide the date rather than rush.

## Session 2: FK0003 Treetop Marble Run, flat (ep 7, air ~Nov 15)

Old build: `docs/engines/forest_keepers_marble_run.md`, `families/keepers/marble_run.py`, `families/keepers/marbles.py`, `families/keepers/params/marble_run.yaml`.
New files: `families/keepers/marble_flat.py`, `marble_flat_world.py`, `experiments/keepers_flat/ep7.py`.

## Session 3: FK0004 River Raft Race, flat (ep 8, air ~Nov 17)

Old build: `docs/engines/forest_keepers_raft_race.md`, `families/keepers/raft_race.py`, `families/keepers/rafts.py`, `families/keepers/params/raft_race.yaml`.
New files: `families/keepers/raft_flat.py`, `raft_flat_world.py`, `experiments/keepers_flat/ep8.py`.
Water rules matter here: `water_snap` is at 0, so anything entering or leaving the water moves smoothly. Rafts lie flat on the water, never nose-up.

## Render IDs (assigned 2026-11-06, Local Operations + FK v2)

| ID | Episode | Air (plan) |
|---|---|---|
| FK0017_christmas_tree | ep 14 Christmas (re-render with the elbow fix keeps this ID) | **Sat Dec 5** (was Nov 29) |
| FK0018_tune_up_remake | ep 6 Tune-Up (page-turn switch) | Nov 8 (fast-track) |
| FK0019_raft_race | ep 8 Raft Race | Sat Nov 14 |
| FK0020 | ep 7 Marble Run | Wed Nov 11 |
| FK0016 | ep 9 Getting Ready for Winter (approved; was ep 13; description renumbered 2026-11-09) | Wed Nov 18 |
| FK0021 | ep 10 Harvest Feast (was ep 9) | **Sat Nov 21** |
| FK0022 | ep 11 Bug Hunt (was ep 10) | **Wed Nov 25** |
| FK0023 | ep 12 Who's Awake (was ep 11) | **Sat Nov 28** |
| FK0024 | ep 13 New Friend (was ep 12) | **Wed Dec 2** |

Slots re-set 2026-11-09 by Local Operations to the owner's Sat + Wed cadence (FK0016 holds Wed Nov 18). Under the 10-day token rule, each episode's work starts 10 days before its slot: FK0021 Nov 11, FK0022 Nov 15, FK0023 Nov 18, FK0024 Nov 22, FK0017 Nov 25.

Before rendering, create `video_log/FK00NN_<name>.json` containing `{"id": "...", "family": "keepers", "status":
"rendering"}`, and resume from it. Don't call `log.next_id` for these. Since 2026-11-06 `next_id` also checks every
worktree's `video_log` and origin/main's, so a number taken elsewhere is skipped.
