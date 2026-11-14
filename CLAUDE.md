# Zimran Hackathon

Хакатон-проект: скорость важнее идеальности, но `main` должен оставаться рабочим (демо в любой момент).

- `web/` — Next.js (App Router, TS, Tailwind). Перед кодом на Next.js сверяйся с `web/AGENTS.md`.
- `api/` — FastAPI на uv. Запуск: `uv run fastapi dev app/main.py`. Тесты: `uv run pytest`. Линт: `uv run ruff check .`.
- Фронт вызывает API относительными путями `/api/...`; `web/next.config.ts` проксирует их на `API_URL` (локально http://localhost:8000). Все роуты бэкенда — под `/api/...`.
- Деплой: личный Vercel владельца (Hobby), два проекта — `zimran-hackathon-web` (root `web/`) и `zimran-hackathon-api` (root `api/`). Деплоится только `main`. Работаем в ветках через PR; владелец `zengiPE` мерджит merge-коммитом — только такие коммиты Vercel Hobby деплоит. Не пушь напрямую в `main`.
- Секреты — только в `api/.env` и `web/.env.local`; при добавлении новой переменной обновляй соответствующий `.env.example`.
- Всё вместе: `npm run dev` из корня.
