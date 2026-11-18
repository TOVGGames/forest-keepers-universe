# Forest Keepers episode 7: The River Raft Race (`FK0004_raft_race`, ~3:12, 16:9)

Owner pick (2026-10-28), from the options after FK0003 ("Skip the Short, start episode 7: The River Raft Race"). Not a
holiday episode. Races are the channel's strongest format; this one is on water, with real water physics, and every
Keeper has a raft in their colour to cheer for.

Late autumn night, upstream from the water wheel of episode 4: the brook comes down the hillside in steps - a pool,
a riffle over stones, a little falls, a quiet pool with lily pads, rapids, a second falls, a long glide to the finish.

## As built (2026-10-28)

**1. The leaf (0:00-0:28).** The Keepers stroll along the far bank of the brook. A big autumn leaf with a ladybird on
it floats down the riffle, over the first falls (it flies off the lip, splashes, is held in the hole below for a
moment) and drifts out into the pool; the ladybird is fine. Digs has an idea (a raft in his bubble). Springs bounces
off up the rock step beside the falls.

**2. The rafts (0:28-1:51).** The flat bank above the top pool (sign: RAFTS). Six rafts are built side by side, every
Keeper at their own job raft after raft (one raft every 6 s per job), so they all come out the same:
- Wheels brings four logs at a time from the pile on his head.
- Twigs trims every raft's logs at the chalk line with his left wrist saw; the logs lie against a stop board, so every
  raft is the same length (104 px; stats `rafts_even`). The offcuts drop in front.
- Hans lashes each raft with his tentacles (two lashings, twine wound round and round).
- Springs hops from deck to deck and bounces each one tight (three bounces).
- Glo carries the six masts with their pale leaf sails in his short tendrils, sets one in each deck, and his light flares
  over the leaf and turns it the Keeper's colour (as in FK0003; owner: Glo changes things with his light).
- Digs digs a slipway into the bank by the pool and lays two rails.
Then every Keeper lifts their own raft (overhead; Glo's hangs from his tendrils) and they set them on the slipway one
by one, nearest first: each slides down into the pool (splash) and drifts to the log boom.

**3. The race (1:51-2:38).** 3, 2, 1 (Springs at the boom's hinge post on the far bank): the boom swings open and the
six rafts race down the brook. Springs bounces along the far bank beside the pack, Glo floats over the leader lighting
the water, the others watch at the finish on the far bank. A standings strip (sail colours) at the top left.

**4. Cheer (2:38-3:00, no cut).** Hans wins by 0.06 s (`race_seed` 27). The rafts bump against the boom in the finish
pool; Hans hops for joy; a duck and three ducklings come up the brook, hop over the boom one by one and paddle among the
rafts; everyone waves; the camera pulls back over the brook.

**5. End sign** (every Forest Keepers video).

## Owner review of the first cut (2026-10-28) - fixed, re-rendered with `--redo`

- The water streaks ran upstream at "100 miles an hour" in the pull-back: they (and the chop) were laid out from the
  left edge of the view, so they moved with the camera. Now every streak rides through its own fixed cell of the brook
  and fades in and out at its ends; the chop sits on a fixed 60 px grid.
- The opened start boom still lay over the rafts (it was drawn after every lane). Both booms are now drawn a slice at a
  time between the lanes (`draw_boom(..., d0, d1)`): swung open along the far bank it is behind every raft.
- A water-coloured box hid the bottom of each raft (and the leaf): the wrong shade for most lanes, and at the falls it
  dropped to the lower pool before the raft did. Now `hide_under` draws the raft and puts back the water that was
  there below the waterline, so the water shows through in its own shade; no ripple/wake line while a raft is in the
  air over a falls.

## The water physics (`families/keepers/rafts.py`)

Each raft in its own lane (lane 0 nearest us), simulated at 480 Hz:
- the current: every stretch has its own speed (pool 62-80, riffle 175, rapids 235, glide 135 px/s); the fast water
  swings from side to side with the bends, so no lane is faster all the way down;
- drag towards the water's speed (linear + quadratic) and the breeze on the sail;
- buoyancy: a damped spring holds the raft on the surface (waves, the pillow of water over a rock); it lies along the
  surface (pitch from the water under its two ends);
- rocks just under the surface (one per lane): a raft rides up over the pillow and scrapes (slows, more when heavy);
- the falls: over the lip it flies with real gravity, tips nose down, splashes in, dips and bobs back up; below each
  falls the water circles back (the hole), breathing, and a surge now and then flushes a held raft out.
The rafts differ in weight, drag and the size of their leaf; that decides the race. `race_seed: 27` (from 60): 3 lead
changes, the lead taken below the second falls, Hans first by 0.06 s over Springs, all six within 2.1 s.

## Checks

`teleports` 0, `fast_moves` 0, 0 folded notes, `rafts_even`, `raft_*` stats (finish times, order, lead changes, holds).
Audio: 3.4% of the energy at 1-3 kHz, 0.1% at 3-6 kHz (warm), rms 0.164.

## Rules that apply

Everything in `forest_keepers.md`: theme music all the way, end sign, Hans' tentacles, Twigs' wrist saws, Glo's
tendrils only from under his dome (his light does the magic), things line up (stop board), real physics, nobody warps,
the Keepers talk, small touches of life (the ladybird, the ducks).

## Code

`rafts.py` (course, physics, drawing), `raft_race.py` (acts leaf, rafts, raft_race, raft_cheer), params
`raft_race.yaml`; the chatter picture "raft" in `chatter.py`.
