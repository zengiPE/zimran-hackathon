# Zimran Hackathon

Хакатон-проект: скорость важнее идеальности, но `main` должен оставаться рабочим (демо в любой момент).

- `web/` — Next.js (App Router, TS, Tailwind). Перед кодом на Next.js сверяйся с `web/AGENTS.md`.
- `api/` — FastAPI на uv. Запуск: `uv run fastapi dev app/main.py`. Тесты: `uv run pytest`. Линт: `uv run ruff check .`.
- Фронт ходит в API по `NEXT_PUBLIC_API_URL` (по умолчанию http://localhost:8000), все роуты под `/api/...`.
- Секреты — только в `api/.env` и `web/.env.local`; при добавлении новой переменной обновляй соответствующий `.env.example`.
- Всё вместе: `npm run dev` из корня.
