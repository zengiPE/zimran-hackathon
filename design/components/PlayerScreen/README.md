# PlayerScreen

The player screen at `/play/[id]?token=…`, assembled from the components at phone width. Use it as the layout reference.

**What it shows depends only on `phase`** from `GET /api/cases/{id}/me` (polled every 5 seconds).

`play`, top to bottom:

1. DemoBar, only in a demo case created from this browser.
2. CaseHeader.
3. "Case brief": a `cf-drawer` with `intro` (paragraphs split on blank lines). Open on the player's first visit, collapsed after.
4. "Today's evidence": the player's clue for the current `day`, as a ClueCard with `is-new`.
5. "Your earlier clues (N)": a collapsed drawer with the rest of `my_clues`, newest first.
6. "Your notebook": a collapsed drawer with the Notebook.
7. "Opened for everyone": `shared_clues` as `is-shared` ClueCards. Hidden when empty.
8. The board (BoardPost), oldest at the top.
9. The composer, pinned to the bottom (`cf-composer--bar`).

`vote`: VotePicker takes the place of "Today's evidence". Clues, notebook and board stay below it so people can check before voting.

`reveal`: load `GET /reveal` and show RevealBoard full width on `cork` in place of everything else.

**Behavior**

- When `day` changes between polls, scroll to "Today's evidence" and play the 160ms fade on the new clue.
- Keep the column at 480px max, centered on wider screens.
- Errors: 403 "This link doesn't work. Ask the host for a new one." · 404 "We couldn't find this case." · 409 refresh `/me` quietly. Write them in `ink` on `card`.
