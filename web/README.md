# Casefile — web

The browser app for Casefile: a detective case a group of friends cracks together, one clue a day.
Next.js 16 (App Router, `cacheComponents`), React 19, Tailwind 4, SWR, Framer Motion.

## Run it

From the repo root (starts the web app on :3000 and the API on :8000):

```bash
npm run dev
```

Only the web app: `npm run dev` in `web/`. The browser calls the API with relative `/api/...` paths;
`next.config.ts` proxies them to `API_URL` (see `.env.example`, locally `http://localhost:8000`).

Before a commit (CI runs the same):

```bash
npm run lint --prefix web
npm run build --prefix web
```

## Pages

| Route | What it does | API |
| --- | --- | --- |
| `/` | Landing, jury path, "Try a demo case", Create case form | `GET /api/themes`, `POST /api/cases` |
| `/host/[id]?token=…` | Host screen for a projector: QR invites, who joined, Hint, Next day (demo), the reveal | `GET …/host` every 5 s, `POST …/advance`, `POST …/hint` |
| `/play/[id]?token=…` | Player screen: clues, notebook, board; the vote; the reveal | `GET …/me` every 5 s, `POST …/board`, `POST …/vote`, `GET …/reveal` |
| `/paywall?case_id=…` | Plans, Stripe Checkout with the test card on screen, Paid opens the next case | `GET /api/plans`, `POST /api/checkout`, `GET /api/checkout/{id}` |
| `/dev/kit` | Every component in every state on real demo data (visual test) | none |

What a game screen shows depends only on `phase` from the API: `play`, `vote` or `reveal`.

## Demo in one minute

1. Open `/` and press **Try a demo case**, type your name, press **Start the demo**. It creates the
   tested case (seed 7) for you plus three AI teammates: Nora, Felix and Kai.
2. The AI teammates post their clue of the day on the board. Press **Share this clue** under yours
   or write a theory: one or two of them reply within a few seconds ("Nora is typing…").
3. The dashed **demo bar** at the top: **Next day** twice, then **Open voting**. **View as** shows any
   seat's screen (an AI seat is read only). **Hint** opens a key clue for everyone.
4. Pick a suspect and press **Cast your vote**: the AI teammates have already voted, so the animated
   reveal starts (**Replay** runs it again). Under the votes: your crew's record.
5. **Open the next case**: case #2 with the same crew, or the paywall first when Stripe is on
   (test card `4242 4242 4242 4242`, any future date, any CVC, any ZIP).

If the API has AI teammates turned off (409) or is older (422 on `solo`), the button falls back to
the classic demo: one person plays all four seats (you, Blake, Casey, Drew) via **View as**.

## Code map

```
src/app/            pages (each game page renders its client screen inside <BrowserOnly>)
  globals.css       Tailwind + app-only pieces built from the tokens
  tokens.css        design tokens from design/tokens.json as CSS variables
  casefile.css      the design system's component classes (cf-…), from design/components/bundle.css
src/components/cf/  one React component per design-system component
src/lib/
  types.ts          API types, copied from docs/api-contract.md
  api.ts            one function per endpoint, ApiError with the {detail} text, errorText()
  useCase.ts        SWR hooks: /me and /host polled every 5 s, /reveal once
  storage.ts        localStorage helpers (demo case seats, host token)
  fixtures.ts       real API responses for /dev/kit
```

Rules we keep: colors only from tokens (Tailwind is for layout), no dark theme, no emoji (✓ and ✗ in
the Notebook are text), English UI copy from `design/README.md`, phone first (360–430 px, one
480 px column), host screen at 1280×720.

## Gotchas

- Game pages read the link token and localStorage, so they render only in the browser
  (`components/cf/BrowserOnly.tsx`, React's `use(browser())`). Prerendering never touches them.
- On Windows the dev server sometimes misses CSS edits. If a style change does not show up,
  stop `npm run dev`, delete `web/.next/dev` and start it again.
- Payments need a Stripe **test** key in `api/.env`. Without it checkout answers 503 and the
  paywall shows "Payments are off in this demo." Test card: `4242 4242 4242 4242`.
