# Casefile API

Бэкенд асинхронного детектива: движок дел + игровое API. Все роуты под `/api/...`,
Swagger на `/docs`. Ответы ниже сняты с живого прогона (`seed: 7`, demo).

## Поток игры

```
POST /api/cases            организатор создаёт дело → ссылки игрокам + ссылка ведущего
GET  /api/cases/{id}/me    игрок открывает свою ссылку (опрос раз в 5 с)
POST /api/cases/{id}/board игрок пишет версию на общую доску
POST /api/cases/{id}/advance  [demo] ведущий переключает день → после последнего дня голосование → развязка
POST /api/cases/{id}/vote  игрок голосует (только в фазе vote)
GET  /api/cases/{id}/reveal развязка (только в фазе reveal)
```

Аккаунтов нет. У каждого игрока свой `token` в ссылке, у организатора отдельный
`host_token` для экрана ведущего. Ссылки: `/play/{case_id}?token=…` и
`/host/{case_id}?token=…` — это страницы фронта.

## Фазы и дни

- `day` — текущий день дела (1…`days_total`). В реальном режиме день = 24 часа от
  создания, в demo дни переключает ведущий через `advance`.
- `phase`: `play` → `vote` (день после последнего) → `reveal` (когда проголосовали все
  зашедшие игроки, или ещё через день, или ещё один `advance`).
- **Правило выбывшего:** если владелец не открыл улику до конца её дня, она попадает в
  `shared_clues` у всех. Открыть улику = зайти на `/me` в этот день.
- `hint` (ведущий) делает одну ключевую улику из открытых дней общей.

## Эндпоинты

### `GET /api/themes`
`[{"id": "lake-house", "title": "The Lake House Weekend", "tagline": "…"}, {"id": "office-party", …}]`

### `POST /api/cases` → 201
```json
{"theme": "lake-house", "players": ["Ann", "Bo", "Cy", "Di"], "demo": true}
```
Необязательно: `days` (2–5; по умолчанию 3 в demo, 5 иначе), `suspects` (5; 4 только для
маленьких дел), `seed` (одно и то же дело при одном seed).
```json
{
  "case_id": "vlxdQvn1",
  "host_token": "w7-cR6SY0nXvzSNk",
  "host_url": "/host/vlxdQvn1?token=w7-cR6SY0nXvzSNk",
  "days": 3,
  "invites": [{"idx": 0, "name": "Ann", "token": "PzYIpkY9oI2w",
               "url": "/play/vlxdQvn1?token=PzYIpkY9oI2w"}, "…"]
}
```

### `GET /api/cases/{id}/me?token=…`
```json
{
  "case_id": "vlxdQvn1",
  "title": "The Lake House Weekend",
  "intro": "Five college friends rented a cabin…\n\nThe owner's prized 1970s record player was found smashed in the Sunroom. … Whoever was in the Sunroom at 7:00 PM broke it.",
  "demo": true, "day": 2, "days_total": 3, "phase": "play",
  "next_unlock_at": "2026-11-15T11:08:29+00:00",
  "suspects": [{"id": 0, "name": "Priya", "role": "the college roommate"}, "…5 шт."],
  "labels": {"room": ["kitchen", "…"], "time": ["6:00 pm", "…"], "item": ["camera", "…"]},
  "me": {"idx": 0, "name": "Ann"},
  "my_clues": [{
    "id": "d1p0", "day": 1,
    "text": "Jordan was not seen at 7:00 PM.",
    "story": "Caption on a blurry group-chat photo: Jordan was not seen at 7:00 PM.",
    "format": "Photo caption",
    "fact": {"kind": "not", "a": "time", "s": 1, "v": 0},
    "from": "Ann"
  }],
  "shared_clues": [],
  "board": [{"author": "Ann", "text": "Bo looks nervous", "ts": "2026-11-14T11:08:29+00:00"}],
  "players": [{"idx": 0, "name": "Ann", "joined": true, "opened_today": true, "voted": false}],
  "my_vote": null
}
```
- `text` — точная формулировка факта (источник правды). `story` — текст в стиле темы
  (Claude, а без ключа или при провале проверки — шаблон), `format` — подпись документа
  («Text message», «Receipt note»). Показываем `format` + `story`, а `text` строкой ниже.
- `intro` — публичная завязка: место и время происшествия известны всем с первого дня.
- `labels` + `suspects` хватает, чтобы нарисовать блокнот-сетку «подозреваемый × комната/время/предмет».
- `time` в `labels` идёт по порядку времени.

### `GET /api/cases/{id}/host?token=<host_token>`
То же, что `common` часть `/me`, плюс `players[]` с `token` и `url` (для QR) и `votes_count`.

### `POST /api/cases/{id}/board` → 201
`{"token": "…", "text": "до 280 символов"}` → `{"author", "text", "ts"}`

### `POST /api/cases/{id}/vote`
`{"token": "…", "suspect": 1}` → `{"ok": true, "phase": "vote" | "reveal"}`. 409 вне фазы vote.
Голос можно менять до развязки.

### `POST /api/cases/{id}/advance` (только demo)
`{"host_token": "…"}` → состояние ведущего (как `/host`). 409 если дело не demo.

### `POST /api/cases/{id}/hint`
`{"host_token": "…"}` → `{"shared": <clue>}`. 409 если подсказок нет.

### `GET /api/cases/{id}/reveal`
409 до фазы reveal.
```json
{
  "culprit": {"id": 0, "name": "Priya", "role": "The doctor on call all weekend"},
  "truth": [{"suspect": "Priya", "room": "Sunroom", "time": "7:00 PM", "item": "a guitar"}, "…"],
  "chain": [{
    "clue_id": "d1p0", "day": 1, "player": 0, "from": "Ann",
    "text": "Jordan was not seen at 7:00 PM.",
    "eliminated": ["Jordan"], "remaining": ["Priya", "Leo", "Maya", "Sam"],
    "worlds_left": 276480
  }, "…"],
  "votes": [{"player": "Ann", "suspect": "Priya", "correct": true}],
  "stats": {"worlds_total": 1728000, "worlds_public": 345600, "worlds_left": 64,
            "candidates_by_day": [4, 3, 1], "seed": 7}
}
```
`chain` — анимация развязки: улика за уликой, кто кого исключил, сколько из 1 728 000
возможных миров осталось.

## Как устроен движок (`app/engine/`)

- **Мир** — каждого из 5 подозреваемых видели один раз: в одном месте, в одно время, с одним
  предметом (три перестановки). Всего 120³ = 1 728 000 миров; `solver.py` перебирает их все
  один раз, каждая улика — векторная булева маска (numpy). Публичная завязка («кто был в
  {room} в {time}») — тоже маска, с неё начинаются все проверки. Виновный — тот, кто был в
  комнате происшествия.
- **Улики** (`facts.py`) — атомарные факты, истинные в скрытом мире: «X was not in the Kitchen»,
  «X was either in A or on B», «the person with a flashlight was seen later than Y» и т.д.
  Темы и тексты — `app/story` (нарратив), движок берёт оттуда имена, места, время, предметы.
- **Сборка** (`generate.py`): случайная истина по seed → жадно набираем слабые улики, пока
  виновный не станет единственным → выкидываем лишние (каждая оставшаяся необходима) →
  раскладываем по игрокам и дням, добиваем нейтральными уликами → проверяем гарантии.
- **Гарантии** (проверяются для каждого дела и в `tests/test_engine.py` на 300 seed):
  единственный виновный · никто не решит в одиночку · без любого игрока не решить ·
  ответ появляется только в последний день · все улики правдивы.
- Скорость: ~0.1 с на дело (5 подозреваемых, до 6 игроков × 5 дней).

## Запуск

```bash
cd api
uv run fastapi dev app/main.py   # http://localhost:8000/docs
uv run pytest                    # ~35 с, 300 seed; быстро: ENGINE_SEEDS=20 uv run pytest
```

Продакшен: нужна переменная `DATABASE_URL` (Postgres, например Neon из Vercel
Marketplace). Без неё на Vercel используется SQLite в `/tmp` — у каждого инстанса своя,
игры будут теряться. `PUBLIC_WEB_URL` — домен фронта: на него ведут ссылки в `invites`
(и возврат из Stripe).
