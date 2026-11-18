# Forest Keepers episode 4: The Animal Houses (`FK####_animal_houses`, ~6:53, 16:9)

First episode of the Forest Keepers engine (`forest_keepers.md`). The idea (written up 2026-10-26 as "the forest
workshop", parked for the Halloween episode, started 2026-10-27): the Keepers build their own little factory in
the forest, powered by the stream, and use it to make homes for the forest animals. Episode 1: the factory makes
monsters. Episode 2: the monsters put the forest back. Episode 3: back to the factory for Halloween. This one: the
monsters run a factory of their own, outdoors.

## As built (2026-10-27)

**1. Wake (0:00-0:33).** The treehouse on a cold night, leaves blowing down. Two bunnies and a hedgehog come out
of the dark and huddle under the platform, shivering; a robin and a blue tit land on the platform edge. The camera
goes close on them. Glo's lantern flares (an idea!), everyone climbs down (Hans hand over hand on the rungs with
his tentacles, Springs in one real-gravity jump) and off they go.

**2. The water wheel (0:33-2:42).** By the stream, over the episode 2 bridge (sign: WATER WHEEL).
- Digs digs the mill race from the culvert end back towards the stream; Hans sets the sluice gate with two
  tentacles; Digs opens the last bit to the stream and the water fills up to the closed gate.
- Twigs saws eight paddles with his new wrist saw: Wheels feeds the beam against a stop block (every paddle the
  same length, pencil marks on the beam), Twigs cuts at the line, Hans stacks each paddle (two neat stacks of four).
- Springs jumps the two A-frame legs into the dry race and stomps them in; Hans holds the tops together and fits
  the bearing block; Glo lays a spirit level on the cross bar, the bubble settles in the middle, chime.
- Hans rolls the wheel in and lifts it onto the bearing; then fits all eight paddles, turning the wheel one slot on
  (a ratchet click) after each, so every paddle goes into the same place.
- Hans pulls the drive belt's loop down from the workshop's line shaft onto the axle pulley.
- Digs lifts the gate: the water runs down the race, hits the paddles, the wheel spins up (exponential spin-up,
  splashes as paddles dip) and the belt turns the shaft. The camera follows the belt to the workshop.

**3. The workshop (2:42-4:49, no cut: the camera glides in).** An open-sided forest shed, the line shaft turning
under the roof, belts down to the machines, hanging lanterns, station signs CUT / DRILL / BUILD / PAINT. An indexed
roller line (11 s per step) makes six houses, one after another, every station busy:
- CUT - Twigs slides a board from the rack onto his bench and cuts it with his wrist saw at the line; the pieces
  slide into the house's kit.
- DRILL - Digs treads the foot pedal of the overhead drill: the hole saw goes down through the front panel (small
  holes for the birdhouses, a big door for the hedgehog and bunny houses) and the round plug drops out.
- BUILD - Hans lifts every panel up out of the kit into place with his tentacles (back, sides, front, roof) and
  holds the box square while Springs bounces on top of the nail press; the press stroke is set per house so the
  nail plate just reaches the box top, then the ridge.
- PAINT - Glo paints each house with one tendril, roof first, side to side, then hangs its little lantern.
- Wheels lifts each finished house off the end of the line onto a long flat wagon, all evenly spaced.
The camera follows the first birdhouse station by station, then a wide shot of the whole line, then the hedgehog
house at the drill and the bunny house at the press and the paint stand. Houses: blue, yellow, green and pink
birdhouses, a terracotta hedgehog house and a lavender bunny house with a round window.

**4. Deliver (4:49-6:41).** Back at the treehouse. Wheels pulls the wagon in, Hans carries the bundle of posts.
Digs digs four holes in a row, Hans stands each post up, Springs stomps them down from the top, hopping from post to
post; Glo runs a glowing string line along the tops (it turns green: all level). Wheels drives each birdhouse to its
post and Hans lifts it on top; then the hedgehog and bunny houses go down in front of the bushes. Glo lights all six
lanterns. The birds fly in (two more come from the forest), perch, hop inside and peek out; the hedgehog trundles
and the bunnies hop to their doors and go in; the doors glow. Everyone gathers in front of the treehouse and the
camera pulls back.

**5. End sign (6:41-6:53)**, as every Forest Keepers video.

Checks logged in the stats: `paddles_fitted` 8, `houses_built` 6, `houses_even_gaps`, `posts_even`,
`animals_home` 6.

## Owner review of FK0001_animal_houses (2026-10-27): approved, upload as-is

- ✅ "The music's really good. And the whole thing goes together really good." Cleared to upload unchanged.
- Two notes for future videos (not to be fixed in FK0001):
  - **The treehouse door sat half over the right-hand window.** Now centred between the two windows
    (`House.door_x`).
  - **Hans warped at ~5:40** while putting up the birdhouses: in `DeliverAct._hans` his x was `POSTS[j] + 260`
    inside each birdhouse's time window and `POSTS[0] + 280` outside them, so he snapped 200-700 px between frames.
    The new engine check (`teleports` in the stats) found 75 such jumps in this episode, among them Glo snapping
    from lantern to lantern (5:55-6:03), Wheels at 5:45 and smaller snaps in the water-wheel and workshop acts, plus
    Wheels zipping from post to post at ~3000 px/s (`fast_moves` 5).
    Rule from now on: nobody warps (`forest_keepers.md`).

## Alignment rule (owner feedback on v2)
- Everything is placed on a visible grid: boards, rungs, posts, paddles land square and evenly spaced.
- A short "measure" beat (stop block, spirit level, string line) before a piece goes in, then a click.
- Automatic check after each build that every placed piece is aligned and equally spaced.

## Sound
The Forest Keepers theme from start to finish (music box over a soft bass and warm pad, faint crickets), soft
event sounds on top: shovels, saw, gate creak, splashes and the running wheel, roller clunks, the drill, Springs'
boings and the nail press, brush strokes, lantern pings, bird calls on the music box.

## Not done (ideas for later)
- A seventh Keeper designed by Toby (a beaver or woodpecker type, the carpenter).
- Episode 5: pick an idea from the comments (the end sign asks for them).

## Files
- `families/keepers/animal_houses.py` (acts), `props.py` (houses, birds, wheel, workshop machines),
  `params/animal_houses.yaml`.
