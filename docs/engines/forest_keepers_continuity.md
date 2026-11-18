# Forest Keepers: the continuity check and the continuity advisor

The owner turned down FK0021 The Harvest Feast on 2026-11-07 (notes in `publish/OWNER_QUEUE.md`, Answered). Every
code check had passed. He called the misses "gross negligence" and asked for "some kind of new continuity check or
some kind of new advisor". There are now both, and every Forest Keepers episode goes through both before its review
ask.

The misses were all about cause and effect, and about what the viewer can actually see:
- the acorn bonk was tiny, and nobody could tell whether Glo carried the acorn or it floated;
- Digs threw each hole's soil into the other hole;
- Twigs sawed one corner and the opposite corner fell off;
- the gear teeth were cut where the blade wasn't, round only half the wheel;
- the narrator said "floor" for "flour";
- Glo hovered in front of the mill, and the acorns showed through him;
- Twigs took six steps to slice the dough, and the slices turned into round rolls by themselves;
- the bread went into the oven through its wall;
- a basket in Glo's tendrils hid the lanterns lighting up;
- the animals came out through their house walls.

## 1. The cause-and-effect check (on the plan, before the render)

`families/keepers/causecheck.py` holds the rules. The episode's `--check` feeds it every frame, next to storycheck,
and every count must be 0:

| rule | catches |
| --- | --- |
| `effect_off_tool` | a cut, notch or mark that isn't where the tool touches (the corner opposite the blade) |
| `dump_in_hole` | soil or offcuts dropped on another hole's spot (Digs' soil) |
| `action_hidden` | someone not doing the job covering what the viewer must see for more than 0.4 s (Glo at the mill, the basket at the lanterns) |
| `see_through` | something drawn over a thing that is in front of it (acorns through Glo) |
| `form_snap` / `form_no_cause` | a shape or contents changing all at once, or with nothing working on it (dough into rolls) |
| `through_wall` | something partly hidden by a wall that isn't inside the opening it goes through (bread, animals) |
| `too_small` | a story moment's subject too small on screen (the acorn bonk) |
| `shuffle_steps` | little walks where an arm would do (Twigs at the dough) |

The episode says what each beat's action is: what the viewer must see, where the tool touches, and who is doing it.
`experiments/keepers_flat/ep9.py` (`cause_frame`) is the example.

`experiments/keepers_flat/causecheck_selftest.py` puts old FK0021 mistakes back, one at a time, and checks that each
is caught. It catches 5 of 5: Glo in front of the mill, a door too small, a tiny acorn, Glo over Digs' hat, and the
blank turning the wrong way.

## 2. The continuity advisor (fresh agents and speech-to-text)

`families/keepers/advisor.py` was written by the FK0022 Bug Hunt session and is owned by FK remake session 3. It
puts the episode in front of fresh agents with no build context, the way a viewer sees it.

- **Before the render:** frame strips of every beat, drawn from the plan (`experiments/keepers_flat/strips.py`), go
  to three fresh general-purpose agents with the owner's checklist (`advisor.CHECKLIST`). They can draw any moment
  closer, cropped, with `strips.py`.
- **After the render:**
  1. Run `advisor.py prep "<video.mp4>" --id <ID> --script <lines.json>`. It makes contact sheets every 0.5 s and
     0.1 s strips round every sharp movement, and checks the narration with speech-to-text.
  2. Start one fresh agent per prompt.
  3. Run `advisor.py report <ID>`. It writes `video_log/advisor/<ID>_rN.md` and exits with 1 while anything is
     must-fix.
- **Narration alone:** `advisor.py stt <video or soundtrack .wav> --script <lines.json>`. It uses the local
  faster-whisper in the shared .venv, with no ElevenLabs credits. A word heard wrong twice (the second time with the
  line as a hint) is must-fix. "Floor" for "flour" was caught this way.

Fix every must-fix, re-render only the segments it touches, and run the advisor again until it reports 0 must-fix.
The report's path and counts go in the HANDOFF entry and in the review ask.

## The checklist the agents use

`advisor.CHECKLIST` has the owner's FK0021 notes as items 1-9, then the standing rules: no warping, no long walks,
Hans' 8 limbs, depth order all the way, Glo's tendrils and light, nothing spilling out of a page, and anything a
careful viewer would call a mistake.
