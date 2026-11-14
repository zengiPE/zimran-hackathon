# Player

Two views of the people in a case: invite cards for the Host screen and roster rows for player screens.

**Invite card** (`cf-invite`, on `cork`)

- Provide (a `PlayerRow` from `GET /api/cases/{id}/host`): `name`, `url`, `joined`.
- Render a real QR code of `url` with `qrcode.react` at 132px. The preview draws a placeholder pattern.
- When `joined` is true, add `is-joined`: the QR fades and a "Joined" Stamp sits over it.
- Show the link as text under the QR so people can type it.
- The Host screen shows one card per player, up to six, four in a row on a projector. Above them: "3 of 4 joined", and the host buttons "Hint" and "Next day" (demo only) at the top right.

**Roster row** (`cf-roster__row`, on `folder`)

- Provide (a `PlayerRow` from `/me`): `name`, `joined`, `opened_today`, `voted`, and whether it is you (`idx === me.idx`).
- Status in words, first match wins: "Voted" (vote phase), "Opened today's clue", "Hasn't opened today's clue", "Hasn't joined yet". "Voted" and "Opened…" use `cf-roster__status--done` (`ink`), the rest stay `ink-muted`.
- Order: you first, then the rest by `idx`.
