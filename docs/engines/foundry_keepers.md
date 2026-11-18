# Foundry – Forest Keepers (tree monsters, episode 2, ~10 min 16:9)

Owner brief (2026-10-25): a 6–12 minute version with up to 6 monsters. The factory part, both the
assembly and the training, should be **more intense**. After that they go out and do things: they
become caretakers of the forest. **Never fighting, always peaceful**, but highly entertaining to
watch. Creative choices are Claude's; owner reviews the render. Choices agreed before the build: Claude designs
3 new monsters; ~10 min at 1080p (1920x1080, 60 fps); build everything, then report.

Builds on `foundry_monsters.md` (episode 1). Character rules carry over: asleep before the orb
(faint colour, eyes shut, still), the orb wakes them, and every monster's look lives in
`families/foundry/products/monster.py`.

## The idea: the forest is the next assembly line

Episode 1 cut five trees down to make three monsters. Episode 2 closes that loop. The factory
makes six monsters, and then they **put the forest back**, using the same satisfying
step-by-step production-line rhythm as the factory, only outdoors. Every mission is a little
assembly line where each monster's body is its tool:

| Monster | Colour | Body = tool |
|---|---|---|
| Wheels (Toby's) | blue | fast roller; claws carry saplings, planks, lanterns |
| Tentacles | orange | many arms: waters with several cans at once, holds planks in place |
| Teeth | purple | tall, so it reaches high branches; its sharp teeth chew stumps and logs into mulch and planks (a wood chipper, not a weapon) |
| **Springs** (new) | gold | coil-spring legs: huge bounces up into treetops, pats soil flat with a stomp |
| **Lantern** (new) | teal | floats, with a glowing lantern belly: lights every night job, and leads the fireflies at the end |
| **Digger** (new) | red | low and wide, with steel shovel hands and a hard hat with a little lamp: digs holes and post holes |

## Structure (~10:10)

**Act 1 – Factory (~5:30)**
1. **Harvest, 8 trees.** Same night forest and saw truck. Owner feedback on ep. 1 applied: **no
   turnaround**. The truck pulls forward onto a steel grate over the pit and **belly-dumps**: the
   hopper floor swings open and the logs drop straight down.
2. **Shaft, saws, vat.** 8 logs through the saw bank, 48 chunks splash into the green vat, and
   **6 grow**. The drain swirls the rest away.
3. **Intense assembly** (6 bays, the camera visits each). Every body goes through a sequence of
   stations, the way the go-karts did:
   - **carve**: a spinning cutter head shapes the lump while wood shavings fly
   - **sand**: an orbital sander polishes it, with a dust puff
   - **parts**: two arms at once bring parts in from both sides
   - **bolt**: nut-runners spin, click-click, with a little spark of light
   - **inspection**: a green scan line sweeps up the sleeping monster and the bay lamp turns green
4. **Orbs**: six orbs, one after another down the line; each monster wakes up in full colour.
5. **Intense training** (bigger room, a pulse in the music):
   - stations in rotation: punching bag, trampoline flips, balance beam, **log lift** (they lift a
     log over their head), **hurdles**
   - then the **obstacle course run**: one at a time, each against a big lap clock, every one
     different (blue rolls, springs bounces the hurdles, lantern floats over them)
   - the sign changes **TRAINING → THEY PASSED → FOREST KEEPERS**; each gets a little glowing badge
6. **Exit**: the cliff door rolls up and they march out in a line.

**Act 2 – Mission 1: Replant the clearing (~1:40).** Back on the plateau where the 8 stumps are
(their own trees). A wooden mission sign: **REPLANT**. The forest version of the assembly line
moves along the stumps:
purple chews the stump into mulch → digger digs a hole → blue rolls in a sapling → orange waters
with three cans at once → springs stomps the soil flat → lantern lights each step. At the end the
lantern hovers over the row and all 8 saplings grow in a time-lapse into young trees.

**Act 3 – Mission 2: The bridge (~1:30).** A stream. Small forest animals (bunnies and a
hedgehog) wait on one bank. Purple chews a fallen log into planks (chips fly, planks pop out),
digger digs post holes on both banks, springs bounces across with the rope, orange holds planks
while blue fixes them, plank by plank (satisfying clunks on a scale). Then the animals hop across
one by one.

**Act 4 – Mission 3: The treehouse and the lights (finale, ~1:40).** A huge old tree. They build
their home: platform, ladder, walls, roof and round windows. Springs bounces boards up and purple
reaches high. Orange hangs glass lanterns along the branches; the lantern monster lights them one by one
(warm glow) and a cloud of fireflies rises around it. All six climb in, the windows glow, then go
out one by one. Moon, fireflies, end.

Fades to black between acts; each mission opens on its in-world wooden sign (no on-screen titles).

## Sound
Industrial bed inside the factory (pulse during training) crossfades to a softer night-forest bed
outside (the approved ambient pad + crickets). New SFX: chisel/carve, sander, nut-runner, shovel
dig, water pour, plank thunk, bunny hop. Pitched events stay in MIDI 36–96.

## Build notes (2026-10-25)

- Act lengths (params `keepers_long.yaml`): factory 4:17, replant 1:47, bridge 1:31, treehouse 2:04;
  total ~9:41 at 1920x1080 / 60 fps.
- Factory: 11-cycle indexing line (move 1.4 s + work 7.6 s). The camera follows Toby's blue monster
  through all five stations, then visits the others. Monsters stand on pallets with a support post
  until the orb wakes them; the claws hand the rough lumps to the line queue. The carve station's
  cutter orbits the lump and its `rough` outline smooths out. Training: 6 stations × 4 rounds,
  then the course run, one monster after another, with a run/time board.
- Forest acts share `keepers/common.py` (night sky, ground, wooden signs, bunny/hedgehog,
  fireflies). Each mission is driven by a small timeline in `keepers/forest.py`.
- Sound: `synth.keepers_bed` crossfades the industrial bed into ambient pad + crickets at the
  first forest act. The training pulse only plays from training to THEY PASSED.

## Owner feedback on v1 (FE0010_monsters, 2026-10-25) and v2 changes

- ✅ **Names**: Wheels (blue, Toby's), Hans (orange), Twigs (purple), Springs (gold), Glo (teal jellyfish),
  Digs (red mole). Each one's nameplate pops up above its head when its SCAN finishes (the moment it is
  made), stays through the factory, and shows again for the first seconds of every mission.
- ✗ ~2:45 the camera sat on an empty assembly line for ~18 s ("looks like it crashed"). Fixed: the last
  (empty) line cycle is gone, the camera follows the last unit (Digs) to its SCAN, then glides right
  along the row of sleeping monsters to where Wheels gets the first orb. Rule: **the camera always
  moves or holds on something that is happening.**
- ✗ "Realistic physics" is a channel promise. Fixed in v2: jumps use real gravity (`keepers/common.py`
  `Jump`, g = 2600 units/s², the same as the falling logs), and **nothing appears on its own**:
  Springs carries every platform plank / wall board / roof panel / bridge post on the jump that puts it
  there; Twigs chews the boards out of logs at a pile and slides the bridge beams across; Hans sets
  each ladder rung with a tentacle and hangs the lanterns from the platform within reach.
- ✅ Playful layer: creature voices (curious / content / hum / cheer, one pitch per monster), cartoon
  boings for every Springs jump, bloops when Glo lights a lantern, and a light music-box tune over the
  dark beds in the missions (pluck version during training). Instruments in `audio/synth.py`.
- OK as is: monsters small in the wide training shots.

## Owner feedback on v2 (FE0012_monsters, 2026-10-25): approved for upload

- ✅ Physics "a lot better"; approved and cleared to upload as is.
- For future versions (episode 3+), not for FE0012:
  - Hans's working arm (setting ladder rungs, hanging lanterns) looks **nothing like his tentacles** -
    it reads as a stiff stick. Hans must work **with his own tentacles**, and they must look like his
    tentacles when he uses them (same colour, taper, suckers, curling motion). (Owner clarified
    2026-10-26: no factory "upgrade" for this; just fix it.)
  - Things should line up better: boards, rungs, posts and parts should sit neatly aligned where they
    are placed.
  - "If it takes longer, just do it": quality and realism over speed.

## From episode 4 on: its own engine

Owner (2026-10-27): the Keepers are their own engine now, **Forest Keepers** (`FK####`, `families/keepers/`,
`docs/engines/forest_keepers.md`), with the theme song, the end sign and Twigs' saws built in. The rules below
carry over.

## Standing rules from episode 3 (FE0014_halloween, approved 2026-10-27)
- Tentacles are always drawn the FE0014 way (`reach_tentacle` / `Monster.work_tentacle`): owner
  "however you did the tentacles is how we're going to do them from now on".
- Twigs (the cutter) should get small circular saws on his hands/wrists.
- Monsters walking through a doorway are hidden only by the far jamb, never by the wall before it.
- **Music (owner, 2026-10-27): Forest Keepers videos are lighthearted and all-ages, never the dark
  Foundry sound.** An upbeat, playful music-box tune leads the whole video, including the scenes inside
  the factory; the industrial bed and machine sounds sit quietly under it. (FE0014 still had the dark
  factory bed for most of its factory act, with the tune only after the reveal: OK for Halloween, not
  again.) Keep it warm and soft, not bright or clicky.
  Details: `foundry_keepers_halloween.md`, "Owner feedback on FE0014".

## Files
- Scene: `families/foundry/keepers/` (`scene.py` driver, `factory.py`, `forest.py`)
- Params: `families/foundry/params/keepers_long.yaml` (`name: monsters`, so renders are `FE####_monsters`)
