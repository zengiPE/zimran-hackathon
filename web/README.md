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
| `/` | Landing, "Try a demo case", Create case form | `GET /api/themes`, `POST /api/cases` |
| `/host/[id]?token=…` | Host screen for a projector: QR invites, who joined, Hint, Next day (demo), the reveal | `GET …/host` every 5 s, `POST …/advance`, `POST …/hint` |
| `/play/[id]?token=…` | Player screen: clues, notebook, board; the vote; the reveal | `GET …/me` every 5 s, `POST …/board`, `POST …/vote`, `GET …/reveal` |
| `/paywall?case_id=…` | Plans and Stripe Checkout, the Paid state after the redirect | `GET /api/plans`, `POST /api/checkout`, `GET /api/checkout/{id}` |
| `/dev/kit` | Every component in every state on real demo data (visual test) | none |

What a game screen shows depends only on `phase` from the API: `play`, `vote` or `reveal`.

## Demo in one minute

1. Open `/` on a phone and press **Try a demo case**. It creates the tested case (seed 7) for Alex, Blake, Casey and Drew.
2. DemoBar at the top: **View as** switches players, **Next day** moves the days, **Hint** opens a key clue for everyone.
3. After day 3 press **Open voting**, vote as two or three players, and the animated reveal starts on its own (**Replay** runs it again).

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
