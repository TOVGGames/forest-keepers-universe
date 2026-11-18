# Forest Keepers: A New Friend from the Factory (`FK####_new_keeper`, ~6-7 min, 16:9)

**Status: storyboard APPROVED by the owner 2026-11-03 ("Approved", via Don's Asks); built and rendered as
`FK0009_new_keeper` (episode 12), awaiting the owner's review of the video.** Owner, 2026-11-03: "Another trip to the
night shift factory, I want twigs to have hands and can also have retractable blades. Maybe make a 7th keeper"; he
picked **Sprout** from three ideas (`forest_keepers_seventh.md`). "Getting Ready for Winter" comes next (episode 13).

**Promise -> payoff:** the title and thumbnail promise a brand-new Keeper built at the factory (and Twigs' new hands),
the opening narration names the payoff ("at the very end, a brand-new Keeper plants its very first tree"), the Short teases Sprout's silhouette on the line, and the episode shows every build step and Sprout waking up and
planting a first tree.

Same rules as the Tune-Up (`forest_keepers_tune_up.md`) and every Keepers rule in `forest_keepers.md`: lighthearted
music box all the way through (its own variant of the theme), the Keepers' cute noises, no walking through walls at
the factory doors (`doorway.py`, wall_clips 0), nothing changes while a Keeper is awake (orb out first), every step
done by a visible machine, carried pieces stay in their layer the whole way, all checks at 0, end sign appended (now
with seven Keepers).

## Beats

0. **The hook** (first ~15 s, owner's long-form rule: say what's coming early and name one thing we only see at the
   end). The Keepers set off through the night forest towards the factory's lit door on the hill, and the storybook
   narrator Johanna (slow, sparse; her only lines are here and on the name card) says: "Tonight the Forest Keepers go
   back to the night-shift factory. And at the very end, a brand-new Keeper plants its very first tree." Sprout's
   first tree stays out of every shot until beat 5.
1. **The village at night** (~1 min). The Keepers finish trimming dead branches. Twigs trims beautifully, but when he
   tries to pick up an acorn to plant, his wrist saws just nudge it and it rolls away. Twigs: "?". Glo has an idea
   (sparkle bubble): back to the factory. They walk to the hill door and in.
2. **Twigs' new hands** (~1.5 min). Twigs steps onto a pallet on the line. The orb trolley lifts his orb out: he goes
   pale grey and falls asleep. UNCLIP: the arm takes off each wrist saw into the OLD bin. FIT: the gripper brings
   each new hand from the NEW tray and slides it on, one side at a time. The blades test once: out, then back in.
   The orb goes back in, the colour floods back, and Twigs wiggles his new fingers.
3. **Building Sprout** (~2.5 min). A round oak log rolls in. CUT trims it to length, TURN spins it into the acorn
   body (curly shavings), CARVE cuts the scaly cap, and FIT adds the root feet, the arm with its little hand, the other
   hand, the eyes and the smile, one at a time. Sprout is pale and asleep the whole time. PLANT: Twigs'
   first job with his hands is to plant the seedling in Sprout's cap.
4. **Orb in** (~45 s). The trolley brings a new, seventh orb. It drops in, flashes the Forest Keeper badge, and green
   floods out from it. Sprout opens its eyes, blinks, waves. Everyone cheers. Name card: "Sprout / The seventh Forest
   Keeper, the gardener: / plants a new tree for every branch Twigs trims."
5. **Home** (~1 min). Back in the forest, Twigs slides a blade out (only the one he cuts with), trims a dead branch,
   and slides it back in. Sprout plants an acorn where the branch was and waters it, and a tiny two-leaf sprout comes
   up. End sign, seven Keepers.

## Storyboard stills (`forest_keepers_factory_trip/`, made by `families/keepers/factory_trip_board.py`)

0. `0_storyboard_hook.png`: the opening hook: the Keepers set off for the factory on the hill, with the narrator's
   line written out (on the storyboard only; in the episode it is spoken, with an .srt).
1. `1_storyboard.png`: the village at night. Twigs' saws can't pick up an acorn; Glo has an idea.
2. `2_storyboard.png`: the factory. Twigs asleep, orb out; his saws in the OLD bin; the FIT arm bringing his second
   hand.
3. `3_storyboard.png`: Sprout built and still asleep; Twigs plants the seedling with his new hands.
4. `4_storyboard.png`: orb in; Sprout green and awake; everyone cheers; the name card in screen space.
5. `5_storyboard.png`: home. Twigs trims with one blade out; Sprout plants and waters a new tree.

## For the build

- Sprout becomes a seventh `Monster` kind (`seventh_keeper.sprout` moves in, with `PARTS` so the line can fit them,
  `TOPS`, `body_center`, `orb_pos`, a name, its colour `#4c9f48`). Every place that lists six Keepers (end sign,
  chatter, ORDER lists, name tags) needs a seventh.
- Twigs: `Monster.hands`, `blades` / `blades_l`, `grip`, `bare` (an empty wrist socket while the hands are fitted),
  `blade_tip()`.
- Sprout's pronoun: **it** (owner 2026-11-03, "It"): narration, titles and descriptions use it.

**Owner review 2026-11-03 (FK0009 NOT approved, two changes), done in FK0011_new_keeper:** Sprout has two normal
hands, no watering-can hand (it picks up a little watering can from a stump by the oak to water its tree); once
the factory has given Twigs his hands he has no teeth (same mouth). Both apply to every later episode.

## As built (`families/keepers/new_keeper.py`, params `families/keepers/params/new_keeper.yaml`)

Acts `nk_trip`, `nk_hall`, `nk_home`, then the end sign (now seven Keepers, Sprout in the middle). Narrated by Johanna:
the hook over the opening, "This is Sprout, the seventh Forest Keeper." over the name card, the finale ("And there it
is: Sprout's very first tree. Goodnight, forest.") and the sign-off over the end sign; no line needed a pronoun for
Sprout. Music variant `newfriend` (G major, 98 bpm). Times in the 5:56 render:

- 0:00 the hook; 0:12 Twigs saws off a dead branch; 0:18 his saw nudges the acorn off the stump; 0:23 Glo's idea;
  0:52 the factory.
- 1:15 Twigs' orb out; 1:29 UNCLIP (both saws into the OLD bin); 1:44 FIT (each hand from the NEW tray, then each
  sheath tapped: the blade slides out and back in); 2:00 his orb back in, 2:06 he wiggles his new fingers.
- 2:14 the hoist lowers an oak log onto the jig; 2:28 CUT (the offcut with the eye bolt pushed into OFFCUTS);
  2:43 TURN (the bark comes off top to bottom into the acorn shape, curly shavings); 2:59 CARVE (the cap's scales,
  the orb socket, the brush stains the cap); 3:18 FIT (legs, the little hand with its acorn, the other hand,
  the face); 3:45 the PLANT arm hands Twigs the seedling, 3:53 he plants it in the cap; 3:56 the seventh orb in;
  4:02 Sprout wakes up and waves; 4:05 the name card.
- 4:46 home; 5:04 Twigs trims a dead branch with only his left blade out; 5:12 Digs digs a hole, 5:18 Sprout drops
  its acorn in, Digs covers it, Sprout (which picked up the watering can waiting on a little stump by the oak) steps and hops over the mound and
  waters it; 5:28-5:34 the little tree comes up (the
  hook's payoff); 5:44 the end sign.

Checks (whole video): teleports 0, fast moves 0, prop jumps 0, act cuts 0, camera too fast 0 (max pan 216 px/s),
wall clips 0; no two Keepers pass through each other (own check, queue spacing from each Keeper's width).
`Monster` now has the seventh kind `sprout` with its build stages (`log_top`, `turned`, `spin`, `carved`, `socket`,
`stained`, parts `legs`, `arm`, `can`, `face`, `seed` carried by machine arms via `part_dxy`).
