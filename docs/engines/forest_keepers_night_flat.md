# Forest Keepers ep 11 – Who's Awake Tonight? (flat remake, `FK0023_whos_awake`)

This is the remake of FK0008 (`docs/engines/forest_keepers_night_animals.md`) in the flat picture-book look, for the
owner's "remake them all" (2026-11-06). It airs around Nov 23. FK remake session 3 built it.
- Code: `families/keepers/night_flat.py` (the episode) and `night_flat_world.py` (the world).
- Runner: `experiments/keepers_flat/ep11.py` (`--times`, `--stills`, `--check`, `--audio`, `--render`).
- Music: its own variant, `whosawake`. D flat (soft), 84 BPM (the slowest yet), a quiet bar after each
  part for the narrator.

## The story (kept from FK0008, which the owner approved)

A narrated night walk to meet six night-time neighbours, each spotted by one Keeper:

| Keeper | Animal | What it does |
|---|---|---|
| Hans | raccoon | Hans points a tentacle at the ripples on the pond. |
| Twigs | barred owl | Twigs points up into the oak. It turns its head and calls "who-cooks-for-you". |
| Glo | opossum | Glo turns his light down low. She climbs up onto the log, walks along it, sniffs, then goes. |
| Springs | flying squirrel | Springs bounces up twice to see. It glides from one tree to the other, clings, and climbs up into the leaves. |
| Wheels | red fox | Wheels stops very still. The fox sits listening in the long grass, ears turning, then trots off. |
| Digs | white-tailed deer and fawn | They graze, look up, graze again; the doe flags her white tail, and they walk away. |

At each find:
1. The narrator gives the hint.
2. The animal shows itself and goes about its business for about 15-18 s.
3. Glo's light turns the Keeper Field Guide's pages to the match (two other pages first, the "looking it up" beat)
   and ticks the box.
4. The name card shows while the narrator reads its line.
5. The animal goes on its way.

At the end:
- The guide turns back to the checklist, with all six pictures in it, and the "All six found!" card shows.
- The narrator says goodnight. Fireflies gather.
- The end sign reads "WHAT SHOULD THEY DO NEXT?", and the narrator asks for ideas in the comments.

## The owner's notes on FK0008, all built in

- Music is at the usual level, ducked only under the narrator (`narrator.soundtrack`, duck 6 dB).
- The narration is slower, with fewer words. The approved script is kept word for word, so the cached takes are
  reused. One fix: Glo is "he" in every episode, so the opossum hint says "his light".
- "Opossum" is said right (`narration/pronunciation.yaml`).
- The animals are storybook-cute with true markings and no speckles (`animals.py` after the owner's fixes):
  - the raccoon's bandit mask, and it looks at us;
  - the squirrel clings to the trunk and climbs;
  - the fox trots;
  - the deer have big eyes with white rings.
  
  The fawn's white spots are its real marking.
- The pond is natural: a wobbly oval seen low from the side, with a muddy rim, reeds and cattails, lily pads with a
  flower, and stones.
- The log is round, with the cut end showing its rings.
- The end sign reads "What should they do next?".

## New since FK0008

- **The flat look.** Animals are painted with `il.creature`, the same way as ep 13. Each is sized from its real
  height, softened by ratio^0.6: raccoon 137 px, owl 180, opossum 120, squirrel 130 (clinging), fox 175, deer 290,
  fawn 205.
- **No long walks** (owner, FK0019 approval). The old episode walked ~1700 px between finds. Now each find is its
  own clearing:
  - The Keepers walk in about 250 px (a few steps, under 4 s) and stop.
  - When they set off again they take a few steps, and a soft dip into the dark takes them on to the next clearing.
  - `night_flat_world.py` lays the six clearings along one strip, 2400 px apart.
  - The dips are cuts: every stretch has its own gaits (`Cuts`), so no foot stays planted across a cut. The
    storycheck checks each stretch on its own.
- **Everyone in frame.** At each find the line is:
  1. the others behind Wheels, spaced by the walk-through check's own boxes (`apart()`: they may overlap less than
     a fifth of the narrower box);
  2. Wheels pushing the reading cart;
  3. the finder;
  4. the animal.
  
  Glo floats over Wheels, clear of the open book. The camera holds each clearing still (no cuts, no zooms), framed
  from the back of the line to the bush the animal leaves behind.
- **The deer walk on planted hooves** (`night_flat.deer_walk`). It has the same shape and markings as `animals.deer`,
  whose legs swing like pendulums and would slide its hooves along the ground.
- **On screen** (screen space):
  - the counter, "NEIGHBOURS FOUND n / 6", top left;
  - the name card at the bottom, with the animal's picture;
  - the title card;
  - the end sign.
  
  Every picture in the book or on a card is clipped to its page, frame or card.
- **Glo** changes things only with his light: a flare turns each page and ticks each box, with sparkles from his
  lantern down to the book. His lantern throws a soft warm pool on the path. He dims it for the opossum.
- **Hans** points with one working tentacle, with all six legs down, so 8 tentacles at most (owner 2026-11-06).

## Checks (`ep11.py --check`, all 0 before a render)

Storycheck covers each stretch between two dips on its own:
- `thing_jumps`, `pops` (each animal says where it came from and where it went), `unheld_motion`, `water_snap` (the
  raccoon's paws at the water), `limb_stretch`, `depth_order`, `size_drift`;
- `teleports`, `foot_slips`, `reach_miss`, `walk_through`, `elbow_snap`, `hans_tentacles`, `promise_line`.

There are no walls or doors here, so `wall_clips` is 0.
