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
  tests/        pytest
```

## Правила команды

- `main` всегда рабочий; фичи — в ветках `feat/<что>` через PR.
- Секреты только в `.env` / `.env.local`, в git не коммитим.
- Новые эндпоинты — с префиксом `/api/...`.
