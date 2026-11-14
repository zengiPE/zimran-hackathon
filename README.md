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
