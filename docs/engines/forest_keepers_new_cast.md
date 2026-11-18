# Forest Keepers: two new characters and a softer factory (concepts)

**Status (2026-11-14): round 4 of Blossom (lashes) is with the owner (round 1 notes below). Nothing gets built into an episode until they approve
a design.** On 2026-11-14 the owner picked two of four pitches. He said, about Blossom, "I really like the way the flower
works as a card on the sleeve where everybody can see the feelings". He made Melody the factory foreman: "I wanted to
rework the factory soon anyway ... the hard steel, molten metal kind of vibe more goes with our older videos ... a
softer feel ... leaning more into the storybook direction". The same day came the rule that not every Keeper has to be
in every episode (`forest_keepers.md`, standing rules).

Code: `families/keepers/new_cast.py` (`blossom()`, `melody()`).
Sheets: `python experiments/keepers_flat/new_cast_sheet.py docs/engines/forest_keepers_new_cast`.

## Blossom: owner's changes, 2026-11-14 (round 2; these win over anything below)

The owner said "Blossom's pretty good" and asked for these changes:
- **Her orb is the center of her flower**, not on her body. It glows blue. When the flower is shut (sleeping), the
  blue glows through the petals. It flashes the job badges like the others' orbs (the Forest Keeper leaf and so on).
- **No legs.** She floats and flies. Keep the bark-petal bottom.
- **Pollen when she flies.** A little pollen trickles from under her bottom, the same way pollen sometimes comes out
  of her flower. When she flies fast, it's glitter and petals.
- **Her origin:** the Keepers find a magical flower, and it turns into Blossom.
- **Eyelashes:** yes, but compare styles first. The round-1 lashes ran into her eyes ("really weird"). Show one
  different simple style, an Egyptian style, and one or two more.
- One thing at a time: Blossom first, then Melody and the factory.

### Round 3 (owner 2026-11-14, after the round-2 sheets; these win over round 2)

- **Orb placement approved.** Asleep, the whole shut bud is one even light blue, lit by the orb. Don't show a
  darker blue core: you can't tell where the orb is inside.
- **No pollen when she flies** (it read like a stream). Glitter only, shed from **all along her petal hem** and
  scattering as a cloud, never one stream from one spot. A little glitter when she flies, lots when she flies fast,
  with a few tumbling petals when fast.
- **Lashes: "little flicks" picked.** They must never go into the eye. Lash roots sit at `1.21 * er`, outside the
  eye's rim. `python experiments/keepers_flat/lash_check.py` draws 360 cases (every mood, speed, size, lean, moment)
  and counts lash pixels on the eye. It must print TOTAL 0, and did on 2026-11-14.

### Round 4 (owner 2026-11-14: lashes)

- **Root distance.** Round 3's lashes sat a bit too far from the eye, so they moved half the way back: roots at
  `1.17 * er`, down from 1.21. The eye's rim is at 1.08.
- **The lashes go with the eyelid.** As her upper lids lower, the lashes ride down with them. They move together by
  the smallest lid drop under them, so none dips below the lid's edge. As her eyes close they shrink away: full size up
  to `top` 0.35, gone from 0.6. So sleepy and shut eyes have no lashes. The owner OK'd either riding down or
  disappearing. They never stay up on her face.
- **lash_check.** `lash_check.py` now also sweeps her eyes closing in 11 steps, 1,152 cases in all. It counts lash
  pixels on the open part of each eye (inside the rim, below the lid's edge). It printed TOTAL 0 on 2026-11-14.
  - Control: the doll-line style, whose liner lies on the rim, gets flagged (205,019 px). So the check does catch
    lashes on the eye.

Sheets (`python experiments/keepers_flat/blossom_sheet.py docs/engines/forest_keepers_new_cast`):
- `5_blossom_r4_moods.png`: the moods, the blue sleeping bud, the Keeper badge.
- `6_blossom_r4_flying.png`: hovering, flying and flying fast.
- `7_blossom_r4_lashes.png`: little flicks up close, lids lowering to eyes shut.

## Blossom, the new Keeper (`forest_keepers_new_cast/1_blossom_moods.png`, `2_blossom_lashes.png`)

- **Look:**
  - A rounded pink cherry-wood body with a hem of darker bark petals, which gives her a skirt-like silhouette.
  - Short cherry-bark legs and round feet, three-fingered hands, and the orb on her front like the others.
  - She looks feminine but is still a Keeper.
- **Her flower shows how she feels.** The cherry flower on her head is how anyone can tell her mood without words:

  | Mood | What her flower does |
  |---|---|
  | Happy | Wide open, with gold pollen sparkles |
  | Curious | Half open |
  | Sad | Its stem bends over and the half-closed flower hangs |
  | Sleepy or shy | Folds into a closed bud |

  In animation it opens and closes smoothly (`bloom` 0..1, `droop` 0..1).
- **Her job:** decorating and the finishing touches, such as ribbons, bows, garlands and paint. She carries a ribbon spool.
- **Open question:** lashes or no lashes. The other Keepers have none (owner 2026-11-04). Sheet 2 shows both.
- **How she arrives (to choose):** either she's built at the reworked factory, or she grows from a pink seed or
  blossom the Keepers find.

## Melody, foreman of the night-shift factory (`forest_keepers_new_cast/3_melody.png`)

- **Look:**
  - A rosewood music box on two turned-wood legs with brass ball feet.
  - Cream inlay and carved flower inlays, and a pink bow on her lid.
  - Her lid opens backward to show a little oval mirror and the turning brass drum.
  - A brass crank with a wooden handle on her right side.
- **Her job:** she's in charge of the factory. She carries the foreman's clipboard and plans the changes. She cranks
  her tune, and the machines run to it. With her baton, she conducts the machines like an orchestra.
- **Music tie-in:** the Forest Keepers theme is a music box, so her tune can be the show's theme. Factory visits could
  get their own variation of it.
- **On every factory visit from her episode on,** she's the one who has set up the new things, moves things around and
  operates the machines.

## The factory, reworked (`forest_keepers_new_cast/4_factory_mood.png`)

The factory goes from hard steel and molten metal to a soft storybook craft workshop:
- Warm wooden plank walls, round night windows with the moon, and paper lanterns.
- Bunting, shelves of paint pots and yarn, and a round braided rug.
- Wooden gears and a felt conveyor belt, all driven from a big music-box drum.

It's still a place where things are built, and now also where Keepers are trained, but with craft tools (paint, glue,
yarn, carving, sanding) instead of furnaces. The steel and molten-metal look stays with the older bike and robot videos.

## Next once the owner and Toby answer

- Pick or change the details: names, colors, lashes, how Blossom arrives.
- Then a storyboard for the episode where Melody rebuilds the factory, and Blossom's first episode. These could be
  one episode or two.
- Then each becomes a `Monster` kind, with parts the factory can make piece by piece, a place on the end sign, and
  continuity-checked animation (flower bloom and droop, lid, crank, baton).
