# Stamp

A rubber-stamp label that shows a state in one or two words.

**Provide:** the text (one or two words) and a color variant.

- Default (`stamp`): neutral states such as "Day 2", "Joined", "New today".
- `cf-stamp--muted`: "Waiting", "Cleared".
- `cf-stamp--red` (`string`): only "Guilty" on the culprit.
- `cf-stamp--big`: the final "Solved" on the Reveal.
- `cf-stamp--straight`: no tilt, for stamps that sit in a row of text.
- `cf-stamp--thunk`: add when a stamp lands during the Reveal (180ms).

**Rules**

- Never a sentence in a stamp.
- Red only for the culprit.
- At most two stamps on one object.
