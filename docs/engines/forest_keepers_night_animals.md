# Forest Keepers episode 11: Who's Awake Tonight? (`FK0008_night_animals`, ~7:40, 16:9, narrated)

Owner idea (2026-11-01, after the Bug Hunt): the same idea as the Bug Hunt with the animals of the forest, and the
first episodes to try a **narrator**: an elderly grandmother voice, a gentle female sage (owner was thinking of how
Puffin Rock has a narrator), who now and then gives hints of what the Keepers are up to. The Keepers keep their own
cute noises. A/B: narrated episodes against the caption-only ones (Bug Hunt).

Everything from the Bug Hunt carries over: the animals are drawn in code to field-guide accuracy (real shape,
colours, how they move; checked against photos), the Keeper Field Guide (an "Animals" part) identifies each one, a
name card with a short kid-friendly line, a counter, and every rule in `forest_keepers.md` (on-screen text in screen
space, page turns that land before anything new shows, whole animal in frame, nothing walks through a wall). Nothing
scary: no animal catches or eats another on screen, nobody chases or touches the animals, Glo keeps his light soft
so nobody is dazzled.

## The hook

Night animals are the natural fit for the Keepers (the night shift) and give a clear promise: **who's awake in the
forest at night?** The grandmother opens it: the moon is up, the crickets sing, the Keepers go out for a quiet walk
to meet their night-time neighbours; something with a stripy tail slips behind a log... The guide's checklist shows
six silhouettes to find.

## Draft: six night animals (North American woods)

| Keeper who spots it | Animal | What we see | Line (draft, checked before use) |
|---|---|---|---|
| Hans (by the stream) | Raccoon | washing and feeling its food at the water with its clever hands | Its front paws are so sensitive, it can feel what it's holding without looking. |
| Twigs (looking up) | Barred owl | on a branch, turns its head, calls "who-cooks-for-you" | It can turn its head much further than we can, and its soft feathers let it fly almost silently. |
| Glo (a soft glow on a stump) | Opossum | a mother with babies riding on her back | North America's only marsupial: the babies grow in a pouch, then ride on mum's back. |
| Springs (looking up) | Southern flying squirrel | glides from one tree to the next | It doesn't really fly: it glides on a furry skin between its legs. |
| Wheels (in the meadow) | Red fox | sits very still, big ears turning, listening | It can hear a mouse squeak under the leaves from far away. |
| Digs (at the forest edge) | White-tailed deer | a doe and her spotted fawn; the white tail flashes | It lifts its white tail like a flag to say "watch out" to the others. |

Alternatives: a little brown bat (catches insects in the air), a beaver, a skunk, a porcupine, a great horned owl.

The narrator (if chosen) says the hints between the finds ("Hans has spotted ripples in the stream... who could be
down there?") and reads each animal's name and line while the card is on screen, so the youngest viewers who can't
read yet get it too. The cards stay on screen either way.

## As built (`families/keepers/night_animals.py`, params `families/keepers/params/night_animals.yaml`)

- **Narrator**: Johanna (owner's pick, round 2: `narration/keepers_voice.yaml`), 16 lines (`narrator.py`; the script is
  at the top of `night_animals.py`): the opening, the guide, a hint before each find, each animal's line while its
  card is up, the goodnight, and on the end sign "What should the Forest Keepers do next? Tell us in the comments!".
  The scene masters its own soundtrack when `narrator: true`: music, SFX and the Keepers dip 7 dB under the voice,
  one loudness for the mix (~-17 LUFS). The Keepers keep quiet while she speaks. Upload needs the AI-voice line.
- **The animals** (`families/keepers/animals.py`, sheet `forest_keepers_night_animals/1_the_six_animals.png`): each
  spotted by one Keeper; a slow close-up, then a two-shot with the field guide (Glo's light turns the pages and ticks
  the box; the new page comes into view on the turning page, the old one stays until it lands); the name card while
  the narrator reads; then the animal goes on its way (raccoon, opossum and fox behind bushes in the foreground,
  the squirrel up its tree, the deer and fawn away into the meadow at the end). The owl stays on its branch.
- On-screen text in screen space; the camera rests exactly when it holds still (`cam_snap`), so the book's text
  doesn't shimmer. Music: the theme's `nightwalk` variant (E major, 88 BPM, more quiet bars for the voice).
- Checks: teleports, fast_moves, prop_jumps, act_cuts, cam_fast, wall_clips 0; no folded notes.

Rendered 2026-11-01 (1.9 h): `renders/Forest Keepers/FK0008_night_animals.mp4`, 7:39, checks all 0, no folded
notes, mix -17.5 LUFS; in the publishing queue, awaiting owner review.

Owner approved the re-render 2026-11-01 ("the rest was very good"), with one flaw noted for next time, not to be
fixed here: in the guide, the flying squirrel's tail reached past the edge of its page. Fixed in the code afterwards
for later episodes (`families/keepers/book.py`: fit, clip, and the `page_spills` check, which found 12 small spills
in this episode's art, the squirrel's the worst at 33 units). The approved render has the old pages.

Promise -> payoff (for the HANDOFF entry): the title/cover promise the Keepers meeting real night animals; the goal
(six night-time neighbours) is set at ~0:15, the first animal close-up is at ~0:50, then one animal about every
minute, and the full checklist pays it off at ~7:00.

## Open for the owner

1. **The narrator's voice**: five samples sent 2026-11-01 (`narration/keepers_voice_samples.yaml`, A-E).
2. Defaults unless the owner says otherwise: the narrator reads the hints and each animal's line (cards stay); the six
   animals above; ~6-7 minutes, one walk, no cuts. Narrated uploads: Altered content No, AI-voice credit line in the description (PRODUCTION.md).
