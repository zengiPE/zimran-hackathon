# Zimran Hackathon

Монорепо: `web/` — Next.js (TypeScript, Tailwind, App Router), `api/` — FastAPI (Python 3.12, uv).

## Требования

- Node.js 22+
- Python 3.12 и [uv](https://docs.astral.sh/uv/)

## Быстрый старт

```bash
npm run setup                     # зависимости web + api
cp web/.env.example web/.env.local
cp api/.env.example api/.env      # вписать ключи LLM
npm run dev                       # web на :3000, api на :8000
```

- Фронт: http://localhost:3000
- API: http://localhost:8000/api/health
- Swagger: http://localhost:8000/docs

## Команды

| Команда | Что делает |
|---|---|
| `npm run dev` | Запускает фронт и бэк одновременно |
| `npm run dev:web` / `npm run dev:api` | По отдельности |
| `npm run lint` | ESLint + ruff |
| `npm run test` | pytest для api |

## Деплой (Vercel)

- Production: фронт https://zimran-hackathon-web.vercel.app, API https://zimran-hackathon-api.vercel.app

Два проекта в личном Vercel владельца репо (Hobby). На Hobby Vercel деплоит только коммиты владельца, поэтому:

1. Каждый работает в своей ветке (`feat/<что>`) и открывает PR в `main`. **Напрямую в `main` не пушим.**
2. Владелец (`zengiPE`) мерджит PR на GitHub кнопкой **«Create a merge commit»** (squash/rebase в репо выключены). Автор merge-коммита — владелец, поэтому Vercel его деплоит.
3. Ветки, кроме `main`, не деплоятся (`git.deploymentEnabled` в `vercel.json`): preview-ссылок нет, проверяем локально через `npm run dev`.

| Проект | Root | Что |
|---|---|---|
| `zimran-hackathon-web` | `web/` | Next.js; проксирует `/api/*` на бэкенд по `API_URL` |
| `zimran-hackathon-api` | `api/` | FastAPI как Vercel Function (`app/main.py`, до 60 с на запрос) |

- Merge в `main` → production-деплой обоих проектов (1–2 минуты).
- Секреты (ключи LLM и т.п.) добавляются в Vercel → Project → Settings → Environment Variables, не в код.
- Новые переменные `API_URL` применяются только после передеплоя (читаются при сборке).

## Структура

```
web/            Next.js фронтенд
  src/app/      страницы (App Router)
api/            FastAPI бэкенд
  app/main.py   точка входа, роуты
  app/config.py настройки из .env
  app/db.py     общая БД (SQLModel): SessionDep, таблицы регистрируются в app/models.py
  app/events.py лог событий: created, joined, clue_opened, voted, paid…
  app/story/    темы и нарратив улик (Ч3)
  app/payments/ Stripe Checkout, paywall (Ч3)
  scripts/      ручные проверки (try_narrative.py)
  tests/        pytest
```

## Темы и нарратив (`api/app/story/`)

Движок решает, что правда; слой истории только подбирает слова.

- `themes.py`: две темы, `lake-house` и `office-party`. В каждой по 5 подозреваемых, комнат, временных слотов (по порядку, от раннего к позднему) и предметов, плюс завязка `intro(room, time)`, свидетели (это не подозреваемые) и форматы улик. `theme.at_room(room)` даёт грамотный предлог: «in the Kitchen», «on the Porch».
- `narrative.py`: `narrate_case(theme, facts)` вызывается **один раз при создании дела**. Он делает один вызов Claude (`claude-sonnet-5-5`) на все улики и возвращает `ClueText` на каждый факт в том же порядке. Функция никогда не падает из-за LLM.

**Контракт для движка.** На каждую улику движок передаёт

```python
ClueFact(id="f7", statement="Maya was not in the Kitchen.", mentions=("Maya", "Kitchen"))
```

`statement` — каноническое английское предложение, оно показывается под текстом улики. `mentions` — значения из темы, которые это предложение утверждает (как в `themes.py`, вместе с артиклем: `"a flashlight"`, время — `"8:00 PM"`).

**Проверка текста.** Текст от Claude принимается, только если в нём есть все `mentions` и нет других подозреваемых, комнат, времён и предметов темы, иначе это была бы подложная улика. Если проверка не прошла или API недоступен, эта улика берётся из шаблона формата («Text from Rosa, the caretaker: "…"»). Без `ANTHROPIC_API_KEY` все улики идут из шаблонов.

Проверить промпт на настоящей модели (нужен ключ в `api/.env`):

```bash
cd api && uv run python -m scripts.try_narrative lake-house
```

## Оплата и лог событий (`api/app/payments/`, `api/app/events.py`)

Stripe Checkout **только в тестовом режиме**: ключи `sk_live_` API отвергает. Цены: `case` — $12 за дело на компанию, `monthly` — $7.99 в месяц.

| Эндпоинт | Что делает |
|---|---|
| `GET /api/plans` | Цены для экрана Paywall (UI их не хардкодит) |
| `POST /api/checkout` `{case_id, plan?: "case"\|"monthly"}` | → `{url, session_id}`; фронт делает редирект на `url` |
| `GET /api/checkout/{session_id}` | Страница успеха вызывает его после возврата из Stripe и **сама подтверждает оплату**, даже если webhook не дошёл (план Б из ТЗ) |
| `GET /api/cases/{case_id}/payment` | `{paid, plan, status}` |
| `POST /api/stripe/webhook` | `checkout.session.completed` / `expired`, подпись проверяется |

**Для фронта (Ч2).** Stripe возвращает игрока на `PUBLIC_WEB_URL/paywall?case_id=…&checkout=success&session_id=…` (или `&checkout=canceled`). Страница `/paywall` при `checkout=success` вызывает `GET /api/checkout/{session_id}` и показывает «оплачено». Тестовая карта: `4242 4242 4242 4242`, любая будущая дата, любой CVC.

**Лог событий.** `log_event(session, "joined", case_id, actor="Maya")` пишет событие в таблицу `event`. Типы: `created`, `joined`, `clue_opened`, `voted`, `revealed`, `checkout_started`, `paid`. `funnel(session)` считает, сколько дел дошло до каждого шага (цифры для слайда). `checkout_started` и `paid` уже пишутся; остальные события пишет API дел (Ч1).

**Webhook локально:** `stripe listen --forward-to localhost:8000/api/stripe/webhook`; выданный `whsec_…` положите в `STRIPE_WEBHOOK_SECRET`. На Vercel: Stripe Dashboard (Test mode) → Developers → Webhooks → endpoint `https://zimran-hackathon-api.vercel.app/api/stripe/webhook`, события `checkout.session.completed`, `checkout.session.expired`.

**БД.** `DATABASE_URL`: локально по умолчанию `sqlite:///./casefile.db`. На Vercel файлы между запросами не живут, поэтому там нужен Postgres (Neon или Supabase); строку `postgres://…` можно вставлять как есть.

## Правила команды

- `main` всегда рабочий; фичи — в ветках `feat/<что>` через PR.
- Секреты только в `.env` / `.env.local`, в git не коммитим.
- Новые эндпоинты — с префиксом `/api/...`.
