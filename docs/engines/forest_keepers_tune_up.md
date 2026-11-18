# Forest Keepers episode 9: The Big Tune-Up (`FK0006_tune_up`, 6:48, 16:9)

Owner idea (2026-10-31, after approving FK0005): the series turned out much cuter than "monsters", and a few looks
still read as monstery or busy. The Keepers go back to the factory from episodes 1-2 for upgrades. Owner answers
(same day): **6-7 minutes, all six Keepers** get their orbs pulled; **one job badge per episode** flashes in the
orb; Twigs gets **rounded teeth in a big grin**.

The new look is permanent: every episode after this one uses it (episodes 1-8 stay as they are).

## The new look (standing from this episode on)

- **No pinned badge.** The yellow-and-green leaf badge on each body goes. It and the orb together were too much and
  covered the faces, and in motion neither moved exactly with the body.
- **The orb carries the badge.** When an orb goes in, it lights up and flashes the job badge for about a second.
  While a Keeper works it flashes again now and then (about every 20 s, a soft one-second flash; each Keeper on its
  own timer so they don't all blink together). The badge is the job: the Forest Keeper tree (yellow and green) for
  forest keeping, which is most episodes; a special job gets its own (e.g. a snowflake for building sleds, a loaf for
  baking).
- **Orb out = asleep.** Without its orb a Keeper drains to pale grey bare wood, eyes shut, still (the existing
  `alive` 0 look, greyer). Orb back in = colour floods back out from the orb, eyes open, a stretch. This is how
  changes get made: nothing about a Keeper changes while it's awake.
- **The orb is part of the body.** It is drawn in the body's own frame, so it bobs, sways and bounces exactly with
  it (check: talking bounce, walking gait, jumps).
- **Hans:** the face-tentacle beard and moustache are gone. Under his eyes there's now a mouth that smiles and talks
  (the beard wiggle used to stand in for talking). His leg tentacles, wings and colour stay. He keeps working with
  his own tentacles.
- **Twigs:** keeps one eye, but softer: rounder, a bigger iris, an eyelid and a little brow so it can look happy,
  curious or sleepy. The rows of sharp teeth become a few rounded teeth in a wide grin that can open, grin and pout
  like the others' mouths. Antlers, long legs and wrist saws stay.
- The other four (Wheels, Springs, Glo, Digs) keep their faces. They get sanded and polished.

Before the episode is built: a **new-look sheet** for the owner and Toby (all six awake with the new faces, a few
expressions each, the asleep grey look, the orb flash with two badges) to approve. Toby designed the monsters, so his
yes on Hans' and Twigs' new faces comes first.

**New-look sheet (owner approved all of it, 2026-10-31):** `docs/engines/forest_keepers_newlook/` (1 before/after,
2 Hans' expressions, 3 Twigs' expressions, 4 all six, 5 asleep + the orb flash and three badges); regenerate with
`python -m families.keepers.newlook_sheet`. In code: `Monster.newlook = True` switches it on (old episodes draw
pixel-for-pixel as before); expressions `smile` (-1 "ooh" .. 1 big grin), `cheek` (smiling eyes), `lid_top` (sleepy),
`brow` (Twigs), `talk`; the orb flash is `flash` 0..1 with `job` = keeper / loaf / snow. Both new faces have soft
rosy cheeks. Asleep, the new mouths (and Springs' grin) close into a relaxed line.

## Opening for most episodes (after this one)

Owner: the orb dropping in is such a cute moment that a lot of episodes should start with it. A reusable wake-up
opener (~20-25 s): the factory dock at night, the six Keepers standing pale and asleep; a job comes in (a light on
the board shows the job badge); one by one the orbs drop into the sockets, flash the badge and the Keepers wake up,
names float over them; they walk out through the cliff door into the forest. Not every episode; when it's used, the
calm "name tags first" moment is the Keepers waking up.

## Story as built (`families/keepers/tune_up.py`, params `families/keepers/params/tune_up.yaml`)

Acts `trip` (~54 s), `hall` (~5:05), `home` (~37 s), then the end sign. Order of the line, front first: Glo, Wheels,
Springs, Digs, Twigs, Hans.

1. **Trip (the hook).** A calm night in the village, the name tags first (8 s). Hans walks over to the bunny by its
   house and waves hello with a tentacle; his face-tentacle beard wiggles as he talks and the bunny hops away behind a
   bush. Twigs grins at the hedgehog with all his sharp teeth and it curls up into a spiky ball. Hans and Twigs are a
   bit sad; Glo floats over with an idea (an orb in his bubble). Single file to the NIGHT SHIFT door in the hill;
   the door rolls up, in they go.
2. **Hall, in.** They come into the factory hall from the tunnel (behind the hall's end wall); the ceiling lamps
   come on one by one as Glo floats under them. Each walks to its pallet on the old assembly line and steps up.
3. **Orbs out (6 x 8 s).** The ORBS trolley on the ceiling rail rolls over each pallet, lowers its gripper to the
   orb, lifts it out and sets it in its cup in the rack: the Keeper drains to pale grey and falls asleep. Hans first,
   Glo last (his light dims last); the next one in line says goodbye.
4. **The line (10 moves of 3.4 s, 9 s of work at every stop).** The trolley carries the six orbs along the rail
   (behind the stations) to the end of the line while the line moves the sleepers through four stations:
   - UNCLIP: an arm takes off every pinned badge and drops it into the OLD bin; for Hans also the beard, for Twigs
     the sharp mouth.
   - FIT: from the NEW tray the arm fits Hans' smile, Twigs' grin and Twigs' brow; for the others a little driver
     checks two bolts.
   - SAND: two sanding pads, one each side, up and down; sawdust.
   - POLISH: a soft fleece buffing wheel goes round the front; little sparkles.
   The camera closes in on UNCLIP / FIT while Twigs and Hans get their new pieces.
5. **Orbs in (6 x 7.5 s, Hans + 6 s).** The trolley drops each orb back in, Glo first: the orb flashes the Forest
   Keeper badge, the colour comes back, the eyes open, the name shows, and each steps down onto the walkway. Hans
   wakes last, smiles a little, then a big smile; everyone cheers.
6. **The mirror.** Everyone walks towards the way out; Hans stops at a polished steel mirror standing on the
   walkway and sees his smile (the side-mirror cartoon look: the reflection shows inside the glass), then Twigs sees
   his grin. The exit door rolls up; out they go.
7. **Home.** They come out of the hill door into the village, each orb flashing the badge as they step out. Twigs
   grins at the curled-up hedgehog and it uncurls and comes to him; the bunny hops out from behind the bush to Hans,
   who gives it a gentle pat with a tentacle. A wave of voices and badge flashes, a bird flies by, the camera pulls
   back over the village. End sign.

Music: the Keepers theme in its own variant for this episode (`song: variant: tuneup` = F major, 96 BPM, a new C
part; `families/keepers/music.py`). Checks: teleports 0, fast_moves 0, prop_jumps 0, act_cuts 0, cam_fast 0.

Owner approved it 2026-11-01 with one flaw left in: at the NIGHT SHIFT door (and the hall's way in and out) the
Keepers slid into the rock / end wall beside the door instead of walking in through it. Fixed in the code afterwards
for every later episode (`families/keepers/doorway.py`; this episode's acts use it too, so a re-render would have
it): the rock stands behind the path, the doors are 460 wide, each Keeper walks into the opening's depth and fades
into the dark; new check `wall_clips` 0. The approved render has the old doors.

Rendered 2026-10-31 (5.4 h): `renders/Forest Keepers/FK0006_tune_up.mp4`, 6:48; checks all 0, no folded notes. In the
publishing queue (`publish/HANDOFF.md`), awaiting owner review.

Rules that matter most here: [no warping], [slow on purpose] (no cuts; slow pans down into the factory), [the right
layer in motion] (beard and mouth parts carried away), [visible assembly] (a machine visibly does each step), [no
magic changes] (colour drains/returns from the orb, nothing changes while awake), nothing violent (unclipping and
sanding, never cutting into a Keeper). Music: the Keepers music box all the way, with its own variation.

Promise -> payoff (for the HANDOFF entry): the title/thumbnail promise the Keepers' new look (Hans smiling); the
episode teases it in the first minute (the orbs come out) and pays it off when Hans wakes with his smile.

## Remake (ep 6, 2026-11-06): the art style changes at the factory

Owner (2026-11-06, Don's Asks): "remake them all, but [have] the tune-up episode be the one where the art style changes
halfway ... while they're at the factory, it changes the whole art style". The plan was approved with the page-turn
("yes remake them as planned"). Tune-Up now airs first (ep 6), before Marble Run and Raft Race. Every episode after it is flat.

- **Old look until the storybook press.** The old engine is re-rendered (`families/keepers/params/tune_up_remake.yaml`,
  acts `trip, hall_switch, home_switch`), so the doors are walked through (`doorway.py`, wall_clips 0).
- **The switch** (`families/keepers/tune_switch.py`). Everyone is awake and tuned up and heads for the way out.
  Glo floats up onto the STORYBOOK PRESS, the factory's last machine, which stands past the end of the line before
  the mirror. He is in the back layer, so the others walk past in front of him. He flares his light at its glass eye
  (a light flare, never an arm). The eye lights, the plate presses the big open book, which prints little hills and a
  sun, and lifts. The book glows and its right page rises (5:20-5:22). Then a page turns over the whole picture from
  the right edge (`tune_flat.page_turn`, 5:22.3-5:25.9). Behind it is the same moment in the flat look.
- **Flat half** (`families/keepers/tune_flat.py`). The old scene keeps running and the flat drawing re-draws its own
  state every frame: every Keeper's place, pose and face, the camera with its zoom, doors and depths, bubbles, the
  bunny, the hedgehog and the bird. So nothing can jump at the turn. The overlay check (`experiments/keepers_flat/
  tune_proto.py`) shows a 1:1 fit. The paper grain is scaled by the zoom (`ZoomPage`), so it stays on what it is
  painted on.
- **Nobody walks through anybody** (owner rule since this episode first aired). Twigs is ahead of Hans, so Twigs
  looks in the mirror first while Hans waits behind him, then Hans gets his turn. Glo is on the press, so he comes
  down last and goes to the back of the queue. The queue at the door and the spots at home are spaced by body widths.
  The check is `ep6.py --check` "walk-through": 0. teleports, fast_moves, prop_jumps, cam_fast and wall_clips are all 0.
- Twigs keeps his wrist saws (the hands come with the New Friend factory trip, ep 12). Hans keeps his new smile, Digs his
  hat orb (the flat look's).
- Runner: `experiments/keepers_flat/ep6.py`. It has `--check`, `--stills`, and `--render` (parallel parts, resumable,
  Below Normal priority). One soundtrack covers the whole episode (the Keepers theme `tuneup` variant plus the scene's
  events).
