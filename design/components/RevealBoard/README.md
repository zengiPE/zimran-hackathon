# RevealBoard

The final reveal: a counter of possible worlds melting down, each clue pinned at the top, the five suspects below, and red string drawn from every clue to the culprit.

**Provide** (from `GET /api/cases/{id}/reveal`):

- `stats.worlds_total` and `stats.worlds_public` for the counter's start;
- `chain`: one `cf-note` per item, in order. Label "{from} · Day {day}", text `text`. Each item also carries `eliminated` (names to stamp "Cleared") and `worlds_left` (where the counter goes);
- `culprit` (the polaroid that gets "Guilty"), `truth` (the verdict line), `votes` (who got it right);
- the suspects from `/me`, as `SuspectCard` with `cf-suspect--fluid`. Map `eliminated` names to suspects by name.

**Sequence** (the one orchestrated animation in the product)

1. The counter starts at `worlds_total` (1,728,000) and drops to `worlds_public` over 500ms: the case brief alone already rules most worlds out.
2. For each chain item, step length = `min(850ms, 8000ms / chain.length)`, so the whole reveal stays under about 8 seconds. In the first 70% of the step, draw its string to the culprit's pin and tween the counter to its `worlds_left`. When the string lands, stamp "Cleared" on each of its `eliminated` (180ms thunk).
3. 400ms after the last string, stamp "Guilty" on the culprit and lift the polaroid.
4. Show the verdict card: "{culprit} broke the record player.", then `truth` for the culprit as "Sunroom · 7:00 PM · a guitar", then the votes with "Correct" (`stamp`) or "Missed" (muted) stamps, then "Open the next case" → `/paywall?case_id=…`.

**Strings:** a 2.5px `string` path over a 4.5px `ink` underlay at 35% opacity, sagging 36px below the midpoint, a knot dot at the clue end. The underlay keeps the string at 3:1 on `cork`.

**Counter:** display face, 44px, `tabular-nums`, `toLocaleString("en-US")`, on its own paper card with the label "Possible worlds left". It's the visible proof that the solver did the work. Put `aria-live="polite"` on it.

**Layout:** clue notes two per row on phones, three from 640px. Suspects 3 + 2 on phones, five in a row from 640px.

**In React:** measure pin positions with `getBoundingClientRect` after `document.fonts.ready`, redraw on resize, animate each path's `pathLength` with Framer Motion. Keep a Replay button for the demo.

**Reduced motion:** draw everything in its final state at once.
