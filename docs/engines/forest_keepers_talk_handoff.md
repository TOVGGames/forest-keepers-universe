# Forest Keepers talking format: hand-back to the Forest Keepers session

**From:** the Creative Director prototype session, 2026-11-17. **To:** the Forest Keepers session, through Local
Operations. The owner that day, after watching three proofs: "Yes, hand it back".

Read this first, then `forest_keepers_talk_format.md` (the full record: every owner quote, every measurement, why
each rule exists). Where this page says "owner", the words are his from 2026-11-17 unless dated otherwise. Anything
marked "suggestion" is this session's and is not approved.

## What the owner decided

1. **Forest Keepers is rebuilt around talk, not building.** "Give each of the characters their own voice... focus
   more on dialogue and less on motion and building... The movement will be limited, like just going from place
   to place and not doing so much action." The reason: the 16 minute acorn-flour remake was "mostly AI slop" with
   physics "not obeyed at all".
2. **Long episodes stay the norm:** "I still want 8+ minute longs to be the norm". Shorts as well ("shorts build
   subs, longs get watch hours").
3. **Stories:** a mix of feelings and nature, "with a goal of a lesson relevant to children in each story and
   something they can relate to".
4. **The look stays the flat 2D look.** He turned down a Blender 2.5D look test ("a bit cursed"). What he wants
   from depth is staging only: Keepers at different distances, smaller when further back. No blur, except a soft
   background behind a close-up where it helps.
5. **Cast:**
   - Stay: Sprout, Glo, Digs, Springs (he did not mention Sprout or Digs; they are in the approved proofs).
   - Wheels and Twigs "can go".
   - Melody "probably needs to go too since she isn't based on a living thing" (he said "probably").
   - Hans "can be someone they see in the water in a special episode or two".
   - Blossom "is a keeper but her origin hasn't happened yet".
6. **No orbs:** "Remove the orb, remove the orb from all of them."
7. **Springs is a frog now:** sitting-frog legs (his pick A of three) and the wide frog smile (his pick 2 of
   three), after "his head and mouth need a rework to be more cute".
8. **Voices** (ElevenLabs library, his picks after two audition rounds): Glo = Lulu Lolipop, Springs = Fergy Frog,
   Digs = Georgee, Sprout = Kavya. The narrator stays Johanna, slower. Ids: `experiments/forest_keepers_talk/cast_voices.yaml`.
9. **Music:** the original theme and key. "As far as the key, I like it where it's at." Never change the music
   without asking him. Under talk it stays down; it only comes up, slowly, in real silences.

## The rules the proofs taught us (each one cost a round with the owner)

**Narrator**
- Johanna on `eleven_v4`, one take per scene. The `speed` setting does nothing on v4, which is why she always
  sounded rushed: `narration/keepers_voice.yaml` asks for 0.88 and it never took effect.
- Slow each of her lines afterwards to about 157 words a minute with a pitch-preserving stretch (ffmpeg `atempo`).
  He called 157 "perfect" and about 183 "a speed reading contest".
- Do not use `eleven_multilingual_v2` for her: its takes varied in tone and a lower speed setting darkened her
  voice ("terrible").
- Never cut her take into lines on the service's character timings: on v4 they were about 0.3 s off and clipped her
  last word. Cut in the middle of the real pause, found from the sound (`proof_b.narrator_bounds`).

**Voices and mix**
- Bring every line to the same loudness before mixing; Springs a further 2 dB down (`proof_b.level`).
- Music: down for a whole conversation (a gap under 4 s between lines does not bring it up), starting down 1.8 s
  before the first word, 9 dB down while down, back up over 4 s only in a real silence (`proof_a_music.py`).
- Theme: `music.VARIANTS[None]` only (C major, 104 beats a minute). The other variants are what changed the key.

**Mouths**
- A mouth follows the loudness of its own lines, runs until the sound of the line is over, and closes slowly; small
  leads at the start (Sprout 0.08 s, Springs 0.04 s, Digs 0): `proof_b.mouth`.
- Sprout's mouth is closed at rest (`SPROUT_SMILE = 0.1`).
- A tongue only shows when the mouth is open wide enough to hold it.
- Glo has no mouth; she talks with her lantern, as before.

**Staging and movement**
- One distance rule per place: a Keeper's size comes from where its feet are on the ground (`scale_at`).
- A flat Keeper travels toward the camera or across it, never away (it would be going backwards).
- Walks are short, on planted feet, turned to walk, arms hanging (`flat_motion.biped`, `stance_drop`).
- A change of place or of framing is a cut; everyone keeps their place across it.
- Nothing is picked up, carried, handed over or built on screen.
- Digs' hard hat turns with his head: dome keeps its shape, ridge and lamp move round (`cast.hard_hat`).

## What exists

- Three proofs the owner has watched and steered, in `renders/forest_keepers_talk/` on the Creative Director's
  laptop (git-ignored; they are prototypes, not episodes: no render IDs, not in HANDOFF):
  - A, "The Dark Is Just the Day, Resting" (46 s): voices and faces only.
  - B, "Springs Is Too Fast" (50 s): a walk, hops toward the camera, distance, a cut to a close shot.
  - C, "Digs Doesn't Want to Share His Hill" (80 s): a story chapter, two places, three voices.
  His last word on them: "It's much better now. All the syncing issues are fixed", then two notes (Springs too
  loud, Sprout's mouth always open) that were fixed and re-rendered. **He has not yet said he watched that last
  round.**
- The code, all in `experiments/forest_keepers_talk/`: `cast.py` (no orbs, frog Springs, hard hat), `proof_a.py`,
  `proof_b.py`, `proof_c.py`, `proof_a_audio.py`, `proof_a_music.py`, `voice_samples.py`.
- Look sheets in `docs/engines/forest_keepers_talk_img/`.

## What the Forest Keepers session needs to do

1. **Move the look changes into the production drawing code** (`families/foundry/products/monster.py` and
   friends), which the prototypes deliberately did not touch: no orbs anywhere (including Sprout's socket rim and
   Digs' hat mount), Springs as the frog with face 2, Digs' turning hard hat, Sprout's closed resting smile.
2. **Build the voice pipeline properly:** per-character voices, the narrator rules above, levelling, the mixing
   rule. `engine/narration.py` and `narration/keepers_voice.yaml` need the slowing step.
3. **Turn the format rules into checks** next to storycheck (suggestion): nothing picked up, travel direction,
   size matches feet position, mouth ends with its line, no music rise inside a conversation.
4. **Make the first long episode** as chapters of about 90 seconds in different places, one story and one lesson,
   the narrator linking them (suggestion; the owner has seen this outline but not approved a script).
5. **Shorts:** upright versions cut from single chapters. Not prototyped.

## Open questions for the owner (not asked yet, or not settled)

- Melody: gone for good, or reworked into something living?
- Blossom's origin story, and whether it is the first long episode.
- The Hans-in-the-water special.
- Whether the earlier episodes on the channel stay up as they are.
- Altered-content disclosure for uploads with AI character voices (the narrated episodes carry an AI-voice credit
  line with Altered content: No, per `docs/PRODUCTION.md`; whether that still fits several character voices has
  not been asked).

## Things to know about the prototype setup

- Laptop: Python 3.12 and a `.venv` with the project's packages were installed with the owner's OK. `imageio-ffmpeg`
  was added for encoding (it is not in `requirements.txt`; the owner's PC has ffmpeg on PATH instead).
- ElevenLabs: the key was pasted into the git-ignored `secrets/elevenlabs_key.txt` on the laptop by the owner.
  Credits used over the whole prototype: not totalled; the account read 208,691 used of 241,000 after the audition
  rounds, before the three proofs were voiced.
- This session cannot hear audio or watch video. Every sound decision was made by the owner's ear from A/B pages;
  the spectrum measurements this session tried did not predict what he heard.

## Taken over by the Forest Keepers session (2026-11-17)

Local Operations gave the go the same day. Done so far:
1. **Look in production:** `Monster.orbless` in `families/foundry/products/monster.py`.
   - It is off by default, so older episodes and Foundry draw as before.
   - On, it gives no orb, socket or rim on anyone, and Digs' plain hard hat turning with his head (`_turning_hat`).
   - `families/keepers/talk/cast.py`: `figure()` (orbless, Sprout's closed smile) and `frog_springs()` (legs A,
     face 2, tongue only when it fits).
2. **Voices:** `families/keepers/talk/voices.py` + `narration/keepers_cast_voices.yaml`.
   - Each character has its own voice.
   - The narrator is one v4 take per chapter, cut at the real pauses and stretched to 157 wpm.
   - Every line is levelled, with Springs 2 dB down.
   - Takes are cached.
3. **Mouths and music:** `families/keepers/talk/mix.py`. Mouth leads and slow close; the theme is `VARIANTS[None]`
   only (asserted), down for whole conversations.
4. **Checks:** `families/keepers/talk/check.py` (talkcheck): holding, direction, size vs feet, warping, mouths, music.
5. **Episode 1 script:** `forest_keepers_talk_ep1_script.md`, "How the Forest Keepers Began", is with the owner.
   Nothing is voiced before he approves it.

## Owner notes on episode 1 (FK0027, approved 2026-11-17, apply from episode 2 and the chapter Shorts)

Owner, word for word: "Spring's voice didn't need to be raised. He seems a little bit too loud. The decibels might be
showing you that they're equal, but his voice is so cutting that he sounds louder. And so his can come down a little bit."
-> `anim.LIFT_DB` Springs -1 dB (3 dB under FK0027). Trust his ear over the loudness meter for Springs.

"Instead of watching Sprout walk off the edge of the screen for 2 seconds or 3 seconds, it could just fade to the next
scene... there's nothing interesting about watching somebody walk off the edge of the screen when a fade out would have
been better." -> a Keeper leaving a place turns, takes a step or two, and the chapter fades out; never hold on the walk
out of the frame (FK0027 ch 1 and 2 did, about 2-3 s).
