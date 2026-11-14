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
  app/story/    темы и нарратив улик (Ч3)
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

## Правила команды

- `main` всегда рабочий; фичи — в ветках `feat/<что>` через PR.
- Секреты только в `.env` / `.env.local`, в git не коммитим.
- Новые эндпоинты — с префиксом `/api/...`.
