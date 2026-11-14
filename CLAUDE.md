# Zimran Hackathon

Хакатон-проект: скорость важнее идеальности, но `main` должен оставаться рабочим (демо в любой момент).

- `web/` — Next.js (App Router, TS, Tailwind). Перед кодом на Next.js сверяйся с `web/AGENTS.md`.
- `api/` — FastAPI на uv. Запуск: `uv run fastapi dev app/main.py`. Тесты: `uv run pytest`. Линт: `uv run ruff check .`.
- Фронт вызывает API относительными путями `/api/...`; `web/next.config.ts` проксирует их на `API_URL` (локально http://localhost:8000). Все роуты бэкенда — под `/api/...`.
- Деплой: личный Vercel (Hobby), два проекта — `zimran-hackathon-web` (root `web/`) и `zimran-hackathon-api` (root `api/`). Деплоит `.github/workflows/deploy.yml` (Vercel-токен в секрете репо `ACTIONS`); Git-автодеплой Vercel отключён в `vercel.json`. Push в `main` → production, другие ветки → preview.
- Секреты — только в `api/.env` и `web/.env.local`; при добавлении новой переменной обновляй соответствующий `.env.example`.
- Всё вместе: `npm run dev` из корня.
