# VotePicker

The vote: five suspect polaroids as radio buttons and one "Cast your vote" button. Shown when `phase` is `vote`, in place of "Today's evidence".

**Provide:** `suspects`, `my_vote` (pre-select it), how many players voted (count `players[].voted`), and the question from the case brief ("Who broke the record player?").

- Each card is a `<label class="cf-suspect cf-suspect--fluid cf-suspect--pick">` around a visually hidden radio input, so keyboard and screen readers work. Inside a label use `<span>` elements, with `cf-suspect__caption` instead of `figcaption`.
- Selected: a 3px `stamp` outline and a "Your vote" Stamp in place of the role. Keyboard focus: a 3px `ink` outline.
- Cards are straight here (no tilt) so the grid reads as a form.
- After `POST /vote`: caption "You voted for Priya. You can change it until the reveal." If the response has `phase: "reveal"`, load the reveal at once.
