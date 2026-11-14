# DemoBar

Demo controls that let one person play every seat of a demo case: switch whose screen you see, move to the next day, ask for a hint. This is the path a judge takes when they open the product alone.

**Provide:** the `invites` and `host_token` saved when "Try a demo case" created the case, the current player's name, `day` and `days_total`.

- "View as" buttons switch the player token (`aria-pressed` marks the current one). Switching keeps the scroll at the top and reloads `/me` with the new token.
- "Next day" calls `POST /advance` with the `host_token`. On the last day it opens voting, then the reveal.
- "Hint" calls `POST /hint`. On 409 show the caption "No hints yet."
- Sits at the top of the player screen, above CaseHeader, only in demo cases created from this browser.
- Its dashed border and `folder-deep` fill say "this is not part of the game". Keep it visually separate from the case.
- Buttons are 40px tall here, the one place under 48px besides `cf-btn--sm`.
