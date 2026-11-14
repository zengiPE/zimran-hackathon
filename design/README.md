Casefile is a detective case a group of friends solves together on their phones, one clue a day. Every player screen is the inside of a manila case folder, every clue is a paper document lying on it, and the final reveal is a cork board with red string. Build every screen from those three surfaces.

## Voice and copy

- Write in plain American English and talk to the player: "Your clue for today", "You can't solve this one alone."
- Use sentence case for buttons, text inside documents and help text. Use uppercase only through `case-title`, `screen-title`, `label` and `stamp-text`.
- The case talks like a police file: short, dated, numbered. "Exhibit 3 · Witness statement", "Day 2 of 4", "Cleared".
- Times are US 12-hour ("8:10 PM"). Waits are short ("Next clue in 6 h 12 min").
- Keep the stakes friendly: a smashed record player, a missing ring, a sunk canoe. No blood, weapons or bodies, and never the word "murder".
- No emoji. Show a state with a Stamp and a word. The only glyphs are ✓ and ✗ in the Notebook.

Real copy:

- Landing: "Your group chat went quiet. Crack a case together, five minutes a day."
- Buttons: "Start a case", "Try a demo case", "Next day", "Cast your vote", "Open the next case".
- Loading a new case: "Writing your case file…"
- Empty board: "No theories yet. Share your clue to get the group talking."
- Errors: "This link doesn't work. Ask the host for a new one." · "We couldn't find this case." · "Payments are off in this demo."

## Data

- The screen follows `phase` from the API and nothing else: `play` shows clues, notebook and board; `vote` shows VotePicker; `reveal` shows RevealBoard.
- A clue's `story` is the big text and its `text` is the Fact strip under it. Never show the raw `fact` object. ClueCard has the full mapping.
- A case has five suspects, and five rooms, times and items in `labels`. Players solve it like a logic grid, so the Notebook is part of the core screen, not an extra.
- Players and suspects are different people. Never style a player's name like a suspect's.

## Surfaces

| Surface | Token | Use |
| --- | --- | --- |
| Folder | `folder` | Ground of every player screen. |
| Deeper folder | `folder-deep` | CaseHeader, your own board posts, the earlier-clues drawer, disabled buttons. |
| Paper | `card` | Every document: clues, posts, polaroids, invite cards, inputs. |
| Cork | `cork` | The Reveal board and the Host screen. |

- Lay documents on the folder with `shadow-paper`. Never put a card inside a card.
- On `cork`, text appears only on paper objects, and only in `ink`.

## Color

- `ink` for main text, control borders and the focus ring.
- `ink-muted` for secondary text on `card`, `folder` and `folder-deep`. Never on `cork`.
- `stamp` is the only interactive color: primary buttons, links, today's day and stamps.
- `string` means the solution and nothing else: the red string, pins, the GUILTY stamp. Write errors in `ink` on `card`, not in red.
- `marker` highlights today's new fact, like a highlighter pen.
- `rule-blue` draws index-card rules. It is never text.
- `bubble` fills chat bubbles inside message clues.

## Type

- `case-title` (Big Shoulders Display, uppercase) for the case title and the verdict. `screen-title` for section headings. `stamp-text` only inside stamps.
- `body`, `body-strong` and `caption` (IBM Plex Sans) for everything the app says: posts, buttons, statuses, forms.
- `evidence`, `fact` and `label` (Courier Prime) for everything the case says: clue text, facts, exhibit numbers, folder tabs.
- The rule of thumb: if the app says it, use Plex; if the case says it, use Courier.
- Keep input text at 16px so iPhones don't zoom into form fields.

## Shape, depth and spacing

- `radius-paper` on all paper and controls, `radius-none` on receipts, `radius-bubble` on chat bubbles only, `radius-round` on avatars and pins.
- `shadow-paper` on every document at rest, `shadow-lifted` on the culprit's polaroid and anything being dragged, `shadow-key` under buttons so they read as keys you press.
- Spacing steps: `space-1` 4, `space-2` 8, `space-3` 12, `space-4` 16, `space-6` 24, `space-10` 40. Screen gutter and card padding are `space-4`. Sections sit `space-6` apart.
- Polaroids and stamps tilt between -4° and 4°. Clue cards stay straight so they are easy to read.

## Layout

- Player screens are one column, 360–430px wide, capped at 480px and centered on larger screens.
- Player screen order: DemoBar (demo only), CaseHeader, Case brief, today's ClueCard, earlier clues, Notebook, shared clues, the board, then the composer pinned to the bottom. PlayerScreen shows it assembled.
- The Host screen is landscape for a projector: Player invite cards four in a row on `cork`, "Hint" and "Next day" at the top right.
- Five suspects sit three per row on phones (3 + 2, centered) and five in a row from 640px.
- Touch targets are at least 48px tall.

## Motion

- The Reveal is the one big moment. The counter of possible worlds melts from 1,728,000 while strings draw one at a time from each clue to the culprit, the whole run in about 8 seconds. A CLEARED stamp lands on a suspect as the string that cleared them finishes (180ms). After a 400ms pause, GUILTY lands on the culprit. RevealBoard has the timings.
- Everywhere else: 120–200ms ease-out for button presses and new posts, and nothing more.
- Under `prefers-reduced-motion`, show the final state at once.

## Icons

- Use Lucide (`lucide-react`) at 20px, stroke 1.75, in `ink` or `stamp`, always next to a word.
- Suspects are never drawn. A polaroid shows the suspect's initial in the display face on `ink`.

## Accessibility

- Every text pair named in the token notes meets 4.5:1. The red string meets 3:1 on `cork` thanks to its ink underlay.
- Every state has a word as well as a color: stamps say "Joined", "Cleared", "Guilty".
- Focus is a 3px solid `ink` outline with a 3px offset on every surface.

## In the Next.js app

- Map the tokens into Tailwind `theme.extend`: colors by token name (`bg-folder`, `text-ink`, `bg-stamp`), `fontFamily` `display` / `body` / `type`, `borderRadius` `paper` / `bubble` / `round`, `boxShadow` `paper` / `lifted` / `key`.
- Load the fonts with `next/font/google`: Big Shoulders Display 600/700/800, IBM Plex Sans 400/500/600, Courier Prime 400/700.
- Build each component as a React component with the same name, taking its classes from `components/bundle.css`. The previews are the reference for markup and states.
