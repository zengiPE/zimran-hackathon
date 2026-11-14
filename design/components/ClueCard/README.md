# ClueCard

A clue as a paper document, with its exact fact printed underneath.

**Provide** (a `Clue` from `my_clues` or `shared_clues`): `story`, `text`, `format`, `day`, `from`, plus the clue's position N among the player's clues and whether it is new today.

**Mapping**

- Big text: `story`. If `story` is `null`, use `text` and leave the Fact strip out.
- Label: `Exhibit {N} · {format}`, and `Day {day}` on the right.
- Fact strip: `text`, always visible. It is the source of truth. Never show the `fact` object.
- Kind by `format` (case-insensitive): contains "message" or "text" → `cf-clue--message` with `story` in the bubble; contains "receipt" → `cf-clue--receipt` inside a `cf-drop` wrapper, `story` in `cf-receipt__body` (line breaks kept); anything else → `cf-clue--card`.

**States**

- `is-new`: today's clue. Wrap the fact text in `<mark>` (the `marker` highlighter) and add a "New today" Stamp as `cf-clue__flag`.
- `is-shared`: a clue from `shared_clues`. Dashed outline instead of a shadow, and the label reads "{format} · {from}'s clue, opened for everyone".

**Rules**

- Clue cards are never tilted.
- The story is flavor. If it ever seems to say more than the fact, the fact wins: that is why the strip is always there.
