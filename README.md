# Casefile

A detective case your group of friends cracks together, five minutes a day. Every player gets a
different clue each day, nobody can solve it alone, and after the last day everyone votes and
watches the reveal prove why only one answer is possible.

**Live:** https://zimran-hackathon-web.vercel.app (no login)

## Judging? Your first case in 3 minutes

1. Open the link and press **Take the case**, type your name, press **Start the demo**. You play
   with three AI teammates: Nora, Felix and Kai.
2. Read **Today's evidence**, press **Share this clue**, tap boxes in **Your notebook**, read the board.
3. In the dashed demo bar, press **Next day** twice, then **Open voting**.
4. Pick a suspect, press **Cast your vote** and watch the reveal.
5. Press **Open the next case**: the paywall takes the Stripe test card `4242 4242 4242 4242`
   (any future date, any CVC, any ZIP).

The landing page opens on the demo case itself and repeats these steps under "New here? Your first case". The demo is marked as a demo on screen; first-visit tips on the player screen explain each part. For a real group, use **Create case** on the landing page:
the host screen shows a QR code per player.

## How it works, and why it isn't hardcoded

Every case is generated from a seed by a logic engine (`api/app/engine/`):

- **The world.** Five suspects, each seen once: in one room, at one time, with one item. That is
  120 × 120 × 120 = **1,728,000 possible worlds**. The solver enumerates all of them as numpy
  arrays, and every clue is a boolean mask over that space (`solver.py`).
- **Building a case** (`generate.py`): a random truth from the seed, then weak true facts are added
  until only one culprit is left, redundant ones are dropped, and the rest are dealt to players and
  days.
- **Guarantees, re-verified from scratch on 300 seeds** (`api/tests/test_engine.py`):
  - exactly one culprit;
  - nobody can solve it alone, and every player is needed;
  - the answer appears only on the last day;
  - every clue is true in the hidden world.
- **The reveal** replays the chain: each clue's mask shrinks the possible worlds from 1,728,000
  down to the last ones, and every one of them points at the same culprit.
- **AI teammates** (`api/app/ai/`) know only their own clues and what is posted on the board. Their
  suspicions come from the same solver, so they never name someone already cleared and never
  invent facts. The LLM only phrases what they say; each line is checked, with a template fallback.

### Where the LLM comes in

The LLM (OpenAI, model set by `OPENAI_MODEL`, default `gpt-5-mini` with `OPENAI_REASONING_EFFORT=minimal`
for speed) never decides what is true.
When a case is created it rewrites each clue as an in-world document (a text message, a receipt,
a guestbook entry). The text is accepted only if it mentions every name and value of the fact and
no other suspect, room, time or item; otherwise that clue uses a template. In short: the LLM
**narrates when `OPENAI_API_KEY` is set, template wording otherwise**. The exact fact is always
shown under the story.

## Product

- **Landing / Create case:** pick a story (The Lake House Weekend, The Office Holiday Party), add
  3–6 friends; demo mode lets the host move the days.
- **Host screen:** QR invite per player, who joined and opened today's clue, Hint and Next day.
- **Player screen:** today's clue as a paper document, earlier and shared clues, a private logic-grid
  notebook, the theory board (polled every 5 s, no realtime needed).
- **Dropout rule:** a clue nobody opened by the end of its day becomes visible to everyone, so the
  case stays solvable.
- **Vote and reveal:** counter of possible worlds melting down, red strings from every clue to the
  culprit, who voted right.
- **Retention:** the crew's record (cases solved, streak) and **Open the next case**: same friends,
  new mystery. The first case is free; the next one is $12 per case or $7.99/month (Stripe Checkout,
  test mode).

## Stack and dependencies

| Part | What |
| --- | --- |
| `web/` | Next.js 16 (App Router), React 19, Tailwind 4, SWR, Framer Motion, qrcode.react, lucide-react |
| `api/` | FastAPI, SQLModel, numpy (solver), OpenAI SDK, Stripe, psycopg |
| Data | Postgres (Neon) on Vercel, SQLite locally |
| Payments | Stripe Checkout in test mode (live keys are rejected by the API) |
| Hosting | Vercel, two projects: `web/` and `api/` (FastAPI as a Vercel Function) |
| Design | `design/`: tokens and component specs ("case folder, evidence, cork board") |

## Run locally

Needs Node.js 22+, Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
npm run setup                       # web + api dependencies
cp web/.env.example web/.env.local
cp api/.env.example api/.env        # optional: OPENAI_API_KEY, Stripe test keys
npm run dev                         # web on :3000, api on :8000
```

- App: http://localhost:3000 · API docs (Swagger): http://localhost:8000/docs
- Without `OPENAI_API_KEY` clues use template wording; without Stripe keys the paywall shows
  "Payments are off in this demo."

Checks (the same run in CI on every pull request):

```bash
npm run test          # pytest: 437 tests, including the 300-seed engine properties
npm run lint          # ESLint (web) + ruff (api)
npm run build --prefix web
```

## Repository

```
web/                Next.js app (see web/README.md for pages, components and the demo flow)
api/
  app/engine/       facts, solver (1,728,000 worlds as numpy masks), case generator
  app/story/        themes and LLM narration with validation and templates
  app/llm_client.py the single OpenAI client both LLM features use
  app/ai/           AI teammates: personas, turns, validated replies
  app/cases.py      game API: create, /me, /host, board, vote, advance, hint, reveal, next case
  app/crew.py       crews playing case after case: record, streak, access to the next case
  app/payments/     Stripe Checkout and webhook
  tests/            pytest
design/             design system: tokens, component specs and previews
docs/               API contract for the frontend, product spec (in Russian)
```

The full API contract is in `api/API.md`.

## Team workflow

- Work in `feat/<name>` branches and open a pull request into `main`; `main` stays demo-ready.
- CI (lint, build, tests) must pass. The repo owner merges with a merge commit: the Vercel Hobby
  plan deploys only the owner's commits, so merges by anyone else don't reach production.
- Secrets live only in `api/.env`, `web/.env.local` and Vercel environment variables. When adding a
  variable, update the matching `.env.example`.

Ops notes:

- `API_URL` (web) is read at build time: redeploy the web project after changing it.
- Stripe webhook: `https://zimran-hackathon-api.vercel.app/api/stripe/webhook` with
  `checkout.session.completed` and `checkout.session.expired` (test mode). Locally:
  `stripe listen --forward-to localhost:8000/api/stripe/webhook`, then put the `whsec_…` into
  `STRIPE_WEBHOOK_SECRET`. The paywall also confirms payment itself after the redirect.
- Try the narration prompt on the real model (needs `OPENAI_API_KEY` in `api/.env`):
  `cd api && uv run python -m scripts.try_narrative lake-house`.
