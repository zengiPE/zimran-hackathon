# Frontend TODO

## Phase 5 — polish

General: visible focus, aria labels, buttons at least 48px, no horizontal scroll,
no console errors, clean lint and build, a frontend section in `web/README.md`.

### Notebook improvements (from the Murdle / Clues by Sam research, `research/murdle-cluesbysam.md`)

Only ✓ and ✗ in the notebook, no "?" state (design README).

1. **Automatic ✗ (~1.5 h).** localStorage keeps only manual marks; automatic marks are computed at render.
   If a suspect has ✓ in a group (Room, Time or Item), the other boxes of that group in their row and the
   boxes of that column for the other suspects show a faint ✗ (`ink-muted`, 50% opacity). Remove the ✓ and
   the automatic marks go away; manual marks stay. Tapping an automatic mark turns it into a manual one.
   aria-label: "Priya, Sunroom: ruled out (automatic)".
2. **"Your clues" strip inside the notebook (~1–1.5 h).** Above the grid in the open "Your notebook" drawer,
   a collapsible "Your clues (N)" strip: the facts (`text`) of your clues and `shared_clues`, newest first,
   in `--font-type`, today's fact with `marker`. No more scrolling between ClueCard and the grid at 390px.
3. **Undo and crosshair (~1.5 h).** An "Undo" button under the grid (stack of 20 actions, in the same
   localStorage key). While a box is focused or pressed, highlight its row and column (`marker` at 25%
   opacity). Protects against mis-taps on 44px boxes while scrolling sideways.
