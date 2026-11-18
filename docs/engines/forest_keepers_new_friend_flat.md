# Forest Keepers: A New Friend from the Factory, flat remake (`FK0024_new_friend`, ep 12, air Wed Dec 2)

The same story as FK0011 (`forest_keepers_factory_trip.md`, owner-approved 2026-11-03), redone in the flat picture-book
look. Only the six Keepers set off; Sprout, the seventh, is built at the factory and is with them from then on. It's
narrated by the Keepers' grandmother narrator (Johanna) and has its own music-box variant (`newfriendflat`, registered
from this episode's own module) throughout. Sprout's pronoun is **it** (owner 2026-11-03).

Every owner rule since FK0011 applies:
- Natural walks in **short bursts only** (FK0019). A long trip gets an act break, a carrier, or closer stations.
- Hans has 8 tentacles, never more: six legs and two working tentacles. For a 3rd or 4th arm a leg visibly lifts.
  He works with 2-4 tentacles at once as his thing (FK0011 approval).
- Digs digs like a dog or a mole: alternating front paws, the soil flying back between his legs.
- Physics stays accurate when cutting and putting things together. Every step is done by a visible machine (visible
  assembly), and nothing on a Keeper changes while it's awake (orb out first).
- No warping, grain fixed to objects, no walking through walls (doorway) or each other, storycheck at 0.

Sprout keeps FK0011's fixes: two normal hands (no watering-can hand; it picks up a little can from a stump), and Twigs
has no teeth.

Code (new files only; shared modules untouched):
- `families/keepers/newfriend_flat_world.py`: the village at night, the factory hall, the camera and the page.
- `families/keepers/newfriend_flat.py` (+ `newfriend_flat_*.py` beats): the plan, the Keepers, the frame, the sound.
- `experiments/keepers_flat/ep12.py`: `--times`, `--stills`, `--check`, `--render`.

## Twigs' hands: dropped (owner 2026-11-07, via Don's Asks / OWNER_QUEUE)

Twigs already has hands in the flat remakes of ep 7, 8 and 9. Owner: "It's okay to cut out the part where he gets
hands a second time. We don't need that". So only that beat is gone: Twigs trims dead branches, nobody plants new trees
where they were, and Glo's idea is a new friend who does. The rest of the approved story stays.

## Beats (target ~6:30)

1. **The village at night** (~1 min). The hook is over the opening: "Tonight, the Forest Keepers go back to the
   night-shift factory. And at the very end, a brand-new Keeper plants its very first tree." The first tree stays out
   of every shot until beat 5.
   - Twigs trims a dead branch off the old oak, with one blade out and short strokes. Hans holds the branch with two
     tentacles so it can't drop, then lowers it onto the pile.
   - Where the branch was, there's nothing new growing. Glo's idea bubble: a little acorn Keeper.
   - They set off up the hill path to the factory's lit door. The camera rides ahead with Wheels, and an act break
     (the page dims) takes them inside: no long walk.
2. **The factory hall** (~3.5 min), night-shift muted palette, one compact line.
   - The Keepers come in by the door (doorway: no wall clips) and stand on the walkway at the right end, by the
     PLANT step. From there they watch the whole line, and nobody walks along it.
   - The hoist lowers a round oak log onto the jig cart, and the cart carries it on the rail from station to
     station. The camera eases in on each station and back out for each move.
   - CUT: the saw comes down at the mark, and the push arm slides the offcut into OFFCUTS.
   - TURN: the lathe chucks grip, the log spins, and the cutter runs top to bottom (bark off, the acorn shape, curly
     shavings dropping into the tray).
   - CARVE: the chisel cuts the cap's scales across, the drill cuts the orb socket, and the brush stains the cap.
   - FIT: the arm takes each part from the PARTS tray and fits it, one at a time: legs, the left arm, the right arm,
     the face.
   - PLANT: Twigs takes three steps up to the platform, the PLANT arm hands him the seedling, and he plants it in
     the cap with his hands.
   - ORB: the overhead trolley brings the seventh orb and lowers it into the socket. The badge flashes and green floods
     out from it. Sprout opens its eyes, blinks and waves, and everyone cheers. Name card: "Sprout: the seventh Forest
     Keeper, the gardener".
   - They go out by the door, and an act break takes them home.
3. **Home** (~1.5 min), the village, the night sky starting to get lighter.
   - Twigs trims another dead branch with one blade, and Hans takes it.
   - Digs digs a hole where it was (dog-style, soil flying back onto a little heap).
   - Sprout drops in its acorn, and Digs pushes the soil back over it.
   - Sprout picks up the watering can from the stump, steps up and waters the spot.
   - A tiny two-leaf tree comes up (the water is the visible cause): the hook's payoff.
   - The narrator says goodnight, 4.5 s of quiet, then the end sign with seven Keepers.

## Checks (`experiments/keepers_flat/ep12.py --check`)

storycheck every frame at 30 fps, plus:
- `foot_slips`, `reach_miss`, `walk_through` (Keepers, and the doors' walls), `cam_fast` (250 px/s), `promise_line`,
  `hans_tentacles`.
- The elbow test under 3 px.
- No Twigs or Digs walk on screen longer than ~4 s.
- Nothing on a Keeper changes while `alive` > 0, except planting the seedling, which is done by a visible hand.

## As built (2026-11-07)

Changes against the plan above, each for a reason:
- **Watching from the end of the line.** The Keepers stand on the walkway at the PLANT end, by the door they came in
  by. The camera eases in on each station as the cart reaches it and back out for the moves. Nobody walks along the
  line; Twigs takes a single step to the PLANT step.
- **Act breaks** (the page dims about 1.3 s, holds, comes up) are the two long trips: village to factory, factory to
  home. Each place has its own walks, gaits and turns, so no step or turn carries across a break. The check runs each
  place as its own stretch.
- **The face is painted on** by a fine brush, left to right (the painted face is drawn over the bare one, clipped to the
  brush's sweep). A face carried in by the gripper would have been eyes floating in the air.
- **The orb comes in on a rod beside Sprout**: a short arm holds it in a cup level with the socket, pushes it in, pulls
  back into the rod, and the rod goes up. A cable from above crossed Sprout's face (the thumbnail screen saw it as a
  crack).
- **The CUT disc** is drawn in two halves: its far half before the log, its near half after it, so it really cuts
  through.
- **Twigs' reaches swing round the shoulder** (angle and reach eased separately), never in close to it. A straight-line
  reach cut close to the shoulder and flipped the elbow (a 41 px one-frame snap). Twigs' arm is only ~124 px long, so
  the dead branches hang low enough for his blade.
- **Planting at home**: Digs digs with his right paw from the left of the hole. Sprout drops its acorn (carried since
  FIT) from the right, Digs pats the soil back, then steps back to the oak. Sprout takes the can from the stump at its
  right, walks round in front of the mound and waters it from the left (the can's rose is on its right).
- **Shared-code note for FK v2**: Wheels' elbow shifts 10 px in one frame as he turns to roll (monster.py two_bone,
  turn ~0.4). His hand holds steady.

## Status / resume notes (2026-11-09, paused under the 10-day token rule)
Paused because FK0024 airs Wed Dec 2 (FK Sat + Wed cadence, 69c527d0; eps 9-11 go first), outside the 10-day window (docs/PRODUCTION.md, 2026-11-09). Resume Sun Nov 22 or when Local Operations says.
- Code: rounds 1-8 of the fresh-agent beat-strip reviews are fixed in df01f399. `ep12.py --check` passes with 0 everywhere (0-267 s, round 8). Length is 4:26.7.
- Next: round 9. Draw strips with `experiments/keepers_flat/ep12_strips.py <dir>` (17 beats). Send three fresh reviewers (beats 1-6, 7-12, 13-17) the same prompt as round 8: advisor CHECKLIST, the narration times from `P.narration()`, `--one` close-up strips. Hans has 8 tentacles. When he works, two legs visibly lift and become arms. At the cheer, his two outer legs lift. Repeat until a round has 0 must-fix. Ask Local Ops before the full render (`ep12.py --render 4`, Idle by day). Then run `advisor.py prep/report` to 0 must-fix (Whisper only), make thumbnails with `ep12_thumbs.py`, add the HANDOFF entry, and send the review ask to Local Ops.
- Should-fixes still open (not must): thin or knotted tentacle look. After the cut, the branch hangs level. The socket reads a little like an "O" mouth. The disc is drawn behind the log. The hole reads as a "pit". The tree grows without a visible cause beyond the watering. Glo sits near the frame edge on the walk home.
