# Notebook

The player's private logic grid: each suspect against every room, time and item, marked by tapping.

**Provide** (from `/me`): `suspects` (rows) and `labels.room`, `labels.time`, `labels.item` (three column groups, in that order). For item headers, drop the leading article ("a flashlight" → "flashlight").

- Tap cycles a box: blank → ✗ ruled out (`ink-muted`) → ✓ confirmed (`stamp`) → blank. ✓ and ✗ are the only glyphs allowed in the product; they are text, not emoji.
- Every box is a button with an `aria-label` in words: "Priya, Sunroom: ruled out".
- The marks live only in the browser: `localStorage` key `notebook:{case_id}:{token}`, read and written inside try/catch. Nothing is sent to the server.
- On phones the grid scrolls sideways inside its card; the name column stays pinned. Boxes are 44px.
- Column headers are vertical, set in `evidence` type. Groups are separated by a 2px `ink-muted` rule, boxes by `rule-blue` hairlines.
- On the player screen it sits in a collapsed drawer, "Your notebook", between the clues and the board.
- Legend under the grid: "Tap a box: ✗ ruled out, ✓ confirmed. Only you can see your notebook."
