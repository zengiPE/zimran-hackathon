# Casefile API — контракт для фронтенда

Все роуты под `/api/...`. Фронт ходит относительными путями (`fetch("/api/cases")`),
`web/next.config.ts` проксирует их на бэкенд. Живая схема — Swagger на
`http://localhost:8000/docs`. Ответы ниже сняты с реального прогона (`seed: 7`, demo,
без ключа LLM — поэтому `story` шаблонный).

## Карта экранов

| Экран (страница фронта) | Запросы |
|---|---|
| Landing / Create `/` | `GET /api/themes` → `POST /api/cases` |
| «Try a demo case» на лендинге | `POST /api/cases {"solo": {"me": "<имя>"}}` → сразу на `invites[0].url` |
| Invite (QR и ссылки) | ответ `POST /api/cases`: `invites[].url`, `host_url` |
| Host screen `/host/{case_id}?token=…` | `GET /api/cases/{id}/host` (опрос 5 с), кнопки `POST …/advance`, `POST …/hint` |
| Player `/play/{case_id}?token=…` | `GET /api/cases/{id}/me` (опрос 5 с), `POST …/board` |
| Vote (на странице игрока, `phase === "vote"`) | `POST /api/cases/{id}/vote` |
| Reveal (`phase === "reveal"`) | `GET /api/cases/{id}/reveal` |
| Reveal → «Next case» | `next_access` из `/me` или `/reveal`: оплачено → `POST /api/cases/{id}/next`, нет → на Paywall |
| Paywall `/paywall?case_id=…` | `GET /api/plans` → `POST /api/checkout` → редирект на Stripe → `GET /api/checkout/{session_id}` → `POST /api/cases/{id}/next` |

Аккаунтов нет. Токен игрока и токен ведущего приходят в query-параметре `token` из ссылки,
фронт просто пробрасывает его в API. Ссылки уже полные (домен из `PUBLIC_WEB_URL` бэкенда).

## Игровой цикл

- `day` — текущий день (1…`days_total`). В обычном режиме день = 24 часа с момента
  создания (таймер: `next_unlock_at`). В demo дни переключает ведущий кнопкой `advance`.
- `phase`: `"play"` → `"vote"` (после последнего дня) → `"reveal"`.
  В reveal переходит, когда проголосовали все зашедшие игроки, или ещё одним `advance`.
- Фронт решает, что показывать, **только по `phase`**: play → улики и доска,
  vote → выбор подозреваемого, reveal → запросить `/reveal` и показать развязку.
- Открыть улику = загрузить `/me` в этот день. Неоткрытая до конца дня улика игрока
  становится общей и появляется у всех в `shared_clues` (правило выбывшего).
- Опрос: `/me` и `/host` раз в 5 секунд. Realtime нет.

## TypeScript-типы

```ts
export type Phase = "play" | "vote" | "reveal";

export interface Theme { id: string; title: string; tagline: string }

export interface Suspect { id: number; name: string; role: string }

export interface Labels {
  room: string[];   // "Sunroom", "Porch"…
  time: string[];   // по порядку времени: "7:00 PM", "7:30 PM"…
  item: string[];   // с артиклем: "a flashlight"
}

export interface Clue {
  id: string;            // "d1p0" = день 1, игрок 0
  day: number;
  text: string;          // точный факт, источник правды — показывать мелко под story
  story: string | null;  // текст в стиле темы — показывать крупно
  format: string | null; // подпись документа: "Text message", "Photo caption"…
  fact: Record<string, string | number>; // структура факта, для UI не нужна
  from: string;          // имя игрока, которому выпала улика
}

export interface BoardPost {
  author: string;
  text: string;          // может быть "", если к посту прикреплена улика
  ts: string;
  is_ai: boolean;        // пост ИИ-напарника → пометка «AI teammate»
  fact: Clue | null;     // прикреплённая улика («Share this clue») — рисовать карточкой
}

export interface PlayerRow {
  idx: number; name: string;
  is_ai: boolean;        // ИИ-напарник
  joined: boolean; opened_today: boolean; voted: boolean;
  token?: string; url?: string; // только в /host
}

interface CaseCommon {
  case_id: string;
  title: string;
  intro: string;          // публичная завязка, абзацы через "\n\n"
  demo: boolean;
  day: number;
  days_total: number;
  phase: Phase;
  next_unlock_at: string; // ISO, когда откроется следующий день (в demo не нужен)
  suspects: Suspect[];
  labels: Labels;
}

export interface CreateCaseIn {
  theme?: string;         // id из /api/themes, по умолчанию "lake-house"
  // 3–6 мест: имя (человек) или {name, ai: true} (место ИИ-напарника). Не нужно при solo.
  players?: (string | { name: string; ai?: boolean })[];
  solo?: { me: string };  // соло: ты + 3 ИИ-напарника, 3 дня, demo включён
  demo?: boolean;         // демо-режим: дни переключает ведущий
  days?: number;          // 2–5; по умолчанию 3 в demo, 5 иначе
}

export interface CreateCaseOut {
  case_id: string;
  host_token: string;
  host_url: string;
  days: number;
  // токены ИИ-мест тоже приходят: для переключателя «Смотреть как»
  invites: { idx: number; name: string; token: string; url: string; ai: boolean }[];
}

export interface MeOut extends CaseCommon {
  me: { idx: number; name: string; is_ai: boolean };
  my_clues: Clue[];       // свои улики за все открытые дни
  shared_clues: Clue[];   // чужие улики, ставшие общими (выбывшие, подсказки)
  board: BoardPost[];     // последние 100, старые сверху
  typing: string[];       // имена ИИ-напарников, которые «печатают» → индикатор
  players: PlayerRow[];
  my_vote: number | null; // id подозреваемого
  crew: Crew;             // всегда
  next_case?: { case_id: string; url: string | null } | null; // только в reveal
  next_access?: NextAccess;                                   // только в reveal
}

// Компания друзей, которая играет дело за делом (механика возврата)
export interface Crew {
  case_number: number;    // «Case #2» — какое это дело компании
  cases_played: number;   // законченных дел
  cases_solved: number;   // раскрытых (половина людей назвала виновного)
  streak: number;         // раскрыто подряд — «🔥 2 in a row»
  history: { case_id: string; title: string; culprit: string; solved: boolean }[];
  members: { name: string; is_ai: boolean; played: number; correct: number }[];
}

export interface NextAccess {
  requires_payment: boolean; // true → кнопка ведёт на /paywall?case_id=…
  paid: boolean;
  plan: "case" | "monthly" | null;
  payments_enabled: boolean;
}

export interface HostOut extends CaseCommon {
  players: PlayerRow[];   // с token и url — для QR
  votes_count: number;
  crew: Crew;
  next_case?: { case_id: string; url: null; host_url: string } | null; // в reveal
  next_access?: NextAccess;
}

export interface RevealOut {
  case_id: string; title: string; intro: string;
  culprit: Suspect;
  truth: { suspect: string; room: string; time: string; item: string }[];
  chain: {
    clue_id: string; day: number; player: number; from: string;
    text: string;
    eliminated: string[]; // кого исключила эта улика
    remaining: string[];  // кто ещё под подозрением после неё
    worlds_left: number;  // сколько возможных миров осталось
  }[];
  votes: { player: string; suspect: string; correct: boolean }[];
  crew: Crew;
  next_case_id: string | null;
  next_access: NextAccess;
  stats: {
    worlds_total: number;   // 1 728 000
    worlds_public: number;  // после публичной завязки
    worlds_left: number;
    candidates_by_day: number[];
    seed: number;
  };
}

export interface Plan {
  key: "case" | "monthly"; name: string; description: string;
  amount_cents: number; interval: string | null;
}

export interface PaymentOut {
  case_id: string; paid: boolean; plan: string | null; status: string | null;
}
```

## Эндпоинты

### `GET /api/themes` → `Theme[]`
```json
[{"id": "lake-house", "title": "The Lake House Weekend",
  "tagline": "Five old friends, one rented cabin, and a very expensive accident."},
 {"id": "office-party", "title": "The Office Holiday Party", "tagline": "…"}]
```

### `POST /api/cases` → 201 `CreateCaseOut`
```json
{"theme": "lake-house", "players": ["Ann", "Bo", "Cy", "Di"], "demo": true}
```
```json
{
  "case_id": "fAtg5pIP",
  "host_token": "bUpp1GCfJ1JLRhDf",
  "host_url": "http://localhost:3000/host/fAtg5pIP?token=bUpp1GCfJ1JLRhDf",
  "days": 3,
  "invites": [
    {"idx": 0, "name": "Ann", "token": "xDC3O9HTZbQa",
     "url": "http://localhost:3000/play/fAtg5pIP?token=xDC3O9HTZbQa"}
  ]
}
```
Создание занимает до нескольких секунд (тексты улик пишет LLM) — нужен лоадер.

Соло (кнопка «Try a demo case»):
```json
{"solo": {"me": "Ann"}, "theme": "lake-house"}
```
→ тот же ответ, 4 места: `invites[0]` — человек, `invites[1..3]` — ИИ (`"ai": true`,
имена Nora, Felix, Kai). `days: 3`, demo включён: `host_token` нужен для кнопки «Next day».
Места можно смешивать: `"players": ["Ann", "Bo", {"name": "Kai", "ai": true}]`.

### `GET /api/cases/{id}/me?token=…` → `MeOut`
```json
{
  "case_id": "fAtg5pIP",
  "title": "The Lake House Weekend",
  "intro": "Five college friends rented a cabin on Lake Wendell…\n\nThe owner's prized 1970s record player was found smashed in the Sunroom. The downstairs clock stopped when it fell: 7:00 PM. Whoever was in the Sunroom at 7:00 PM broke it.",
  "demo": true, "day": 1, "days_total": 3, "phase": "play",
  "next_unlock_at": "2026-11-15T11:08:29+00:00",
  "suspects": [
    {"id": 0, "name": "Priya", "role": "The doctor on call all weekend"},
    {"id": 1, "name": "Jordan", "role": "The ex-roommate who never grew up"},
    {"id": 2, "name": "Leo", "role": "The guy who brought his guitar"},
    {"id": 3, "name": "Maya", "role": "The planner who booked the cabin"},
    {"id": 4, "name": "Sam", "role": "The newcomer, someone's plus-one"}
  ],
  "labels": {
    "room": ["Porch", "Kitchen", "Boathouse", "Loft", "Sunroom"],
    "time": ["7:00 PM", "7:30 PM", "8:00 PM", "8:30 PM", "9:00 PM"],
    "item": ["a bottle of rosé", "a flashlight", "a fishing rod", "a guitar", "a deck of cards"]
  },
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
Идеи для UI:
- Карточка улики: `format` маленькой плашкой, `story` основным текстом, `text` серой строкой
  «Fact: …» снизу.
- `suspects` × `labels` — блокнот-сетка, где игрок сам ставит ✓/✗ (состояние только на фронте,
  например в `localStorage`).
- `players` — кто зашёл и кто уже открыл сегодняшнюю улику (давление группы).

### `GET /api/cases/{id}/host?token=<host_token>` → `HostOut`
Общие поля как в `/me`, плюс `players[]` с `token` и `url` (для QR каждого игрока) и
`votes_count`. Улик игроков здесь нет.

### `POST /api/cases/{id}/board` → 201 `BoardPost`
`{"token": "…", "text": "до 280 символов", "fact_id": "d1p0"}` → `BoardPost`.
- `fact_id` (необязательно) — кнопка «Share this clue» у своей улики: id из `my_clues`.
  Можно без текста. Чужую или ещё закрытую улику прикрепить нельзя (403).
- Нужен текст или `fact_id` (иначе 422).
- В игре с ИИ после поста отвечает 1–2 ИИ-напарника. Их ответы появятся в `board` через
  2–6 с (пока они в `typing`) — фронт увидит их при обычном опросе `/me`.

### `POST /api/cases/{id}/vote` → `{ok: true, phase: Phase}`
`{"token": "…", "suspect": 0}`. Только при `phase === "vote"`, иначе 409. Голос можно
менять до развязки. Если в ответе `phase: "reveal"` — сразу грузить `/reveal`.

### `POST /api/cases/{id}/advance` → `HostOut` (только demo)
`{"host_token": "…"}`. Каждое нажатие: следующий день → после последнего голосование →
ещё раз развязка. 409, если дело не demo.

### `POST /api/cases/{id}/hint` → `{shared: Clue}`
`{"host_token": "…"}`. Делает одну ключевую улику общей (на случай, если группа застряла).
409, если подсказок пока нет.

### `GET /api/cases/{id}/reveal` → `RevealOut`
409 до `phase === "reveal"`. Токен не нужен.
```json
{
  "culprit": {"id": 0, "name": "Priya", "role": "The doctor on call all weekend"},
  "truth": [{"suspect": "Priya", "room": "Sunroom", "time": "7:00 PM", "item": "a guitar"}],
  "chain": [{
    "clue_id": "d1p0", "day": 1, "player": 0, "from": "Ann",
    "text": "Jordan was not seen at 7:00 PM.",
    "eliminated": ["Jordan"], "remaining": ["Priya", "Leo", "Maya", "Sam"],
    "worlds_left": 276480
  }],
  "votes": [{"player": "Ann", "suspect": "Priya", "correct": true}],
  "stats": {"worlds_total": 1728000, "worlds_public": 345600, "worlds_left": 64,
            "candidates_by_day": [4, 3, 1], "seed": 7}
}
```
Вау-момент демо: проиграть `chain` по шагу (≈1 с на улику) — карточки подозреваемых
зачёркиваются по `eliminated`, счётчик `worlds_left` тает от 1 728 000 до финала, в конце
остаётся `culprit`. Подпись под каждым шагом: «from Ann». Затем `votes` — кто угадал.
Под развязкой — рекорд компании из `crew` и кнопка «Next case» (см. ниже).

### `POST /api/cases/{id}/next` → 201 `CreateCaseOut & {theme, you}`
Механика возврата: после развязки та же компания открывает следующее дело.
`{"token": "<токен игрока этого дела>"}` (или `{"host_token": "…"}`), необязательно `"theme"`.
- Те же места (имена, ИИ-напарники с теми же персонами), новая загадка, следующая тема по
  кругу (Lake House → Office Party → …).
- `you` — твоё приглашение в новом деле: `window.location.href = you.url`.
- Идемпотентно: если кто-то уже открыл следующее дело, все получают его же.
- Остальным ничего пересылать не нужно: в их старой ссылке `/me` отдаёт `next_case.url` —
  личную ссылку в новое дело (показать «Case #2 is open → Join»).
- 409 — дело ещё не закончено; 403 — неверный токен.
- **402 — нужна оплата:** первое дело бесплатно, следующее открывается после оплаты этого
  дела ($12) или если в компании есть подписка Casefile Club ($7.99/мес, тогда все следующие
  бесплатно). Заранее видно по `next_access.requires_payment`. Если Stripe на бэкенде не
  настроен, оплата не требуется.

### Оплата (Stripe test mode)

- `GET /api/plans` → `Plan[]` — цены не хардкодить:
  `[{"key": "case", "name": "Casefile: your next case", "amount_cents": 1200, "interval": null},
  {"key": "monthly", "name": "Casefile Club", "amount_cents": 799, "interval": "month"}]`
- `POST /api/checkout` `{"case_id": "…", "plan": "case" | "monthly"}` → `{url, session_id}`.
  Делаем `window.location.href = url`.
- Stripe возвращает на `/paywall?case_id=…&checkout=success&session_id=…`
  (или `checkout=canceled`). На этой странице вызвать `GET /api/checkout/{session_id}` →
  `PaymentOut` (подтверждает оплату, даже если вебхук опоздал).
- После `paid: true` кнопка «Start the next case» вызывает `POST /api/cases/{case_id}/next`
  (нужен токен игрока — передать его в `/paywall?case_id=…&token=…`) и ведёт на `you.url`.
  Сейчас эта кнопка ведёт на `/#create` — заменить.
- `GET /api/cases/{id}/payment` → `PaymentOut` — оплачено ли дело.
- 503, если Stripe на бэкенде не настроен.
- Тестовая карта: `4242 4242 4242 4242`, любая будущая дата, любой CVC.

## ИИ-напарники (соло-режим)

Чтобы судья (или новый игрок) прошёл дело один. Всё делает сервер, отдельных эндпоинтов нет.

- **Каждый день** каждый ИИ выкладывает на доску свою улику дня (`board[].fact`) с короткой
  репликой.
- **Ты пишешь пост** — отвечает 1 ИИ (2, если твоя улика изменила их версии): гипотеза
  «по моим уликам это Priya или Leo», вопрос «Ann, anything on Leo?» или реакция.
- **Открылось голосование** — все ИИ голосуют сразу и пишут «Going with …». Развязка
  наступает, когда проголосуешь ты.
- ИИ знает только свои улики и то, что выложено на доску. Его версия считается солвером,
  поэтому он никогда не называет того, кто уже исключён, и не выдумывает факты. Чтобы ИИ
  сузили круг, делись уликами — в этом и игра.
- Задержка 2–6 с: пост уже создан, но в `board` его ещё нет, а автор есть в `typing`.

UI (Диас): кнопка «Try a demo case», аватар ИИ с пометкой «AI teammate» (`is_ai`),
индикатор «Nora is typing…» (`typing`), кнопка «Share this clue» на карточке своей улики,
переключатель «Смотреть как» (токены ИИ из `invites`, чтобы на демо показать, что у
каждого свои улики).

## Ошибки

Тело ошибки всегда `{"detail": "…"}` (у 422 от валидации `detail` — массив).

| Код | Когда | Что делать на фронте |
|---|---|---|
| 402 | следующее дело без оплаты | на `/paywall?case_id=…` |
| 403 | неверный `token` / `host_token`; чужая улика в `fact_id` | «Ссылка недействительна» |
| 404 | дело не найдено | «Дело не найдено» |
| 409 | действие не в той фазе (`vote` раньше времени, `reveal` до конца) | обновить состояние через `/me` |
| 422 | неверное тело (меньше 3 игроков, пустое имя, неизвестная тема) | показать ошибку формы |
| 409 | ИИ-напарники выключены (`AI_FRIENDS_ENABLED=false`) при `solo` | скрыть «Try a demo case» |
| 503 | оплата не настроена | скрыть оплату / показать заглушку |

## Локальный запуск

```bash
npm run dev            # из корня: web :3000 + api :8000
# или только API:
cd api && uv run fastapi dev app/main.py
```

Быстро получить демо-дело для вёрстки:
```bash
curl -s -X POST localhost:8000/api/cases -H 'content-type: application/json' \
  -d '{"players":["Ann","Bo","Cy","Di"],"demo":true,"seed":7}'
```
С одним и тем же `seed` дело всегда одно и то же (удобно для демо).

---

## Как устроен движок (`app/engine/`, для README и питча)

- **Мир** — каждого из 5 подозреваемых видели один раз: в одном месте, в одно время, с одним
  предметом. Всего 120³ = 1 728 000 миров; `solver.py` перебирает их все, каждая улика —
  булева маска (numpy). Публичная завязка («кто был в {room} в {time}») — тоже маска.
- **Сборка** (`generate.py`): случайная истина по seed → жадно набираем слабые улики, пока
  виновный не станет единственным → выкидываем лишние → раскладываем по игрокам и дням.
- **Гарантии** (каждое дело, и `tests/test_engine.py` на 300 seed): единственный виновный ·
  никто не решит в одиночку · без любого игрока не решить · ответ только в последний день ·
  все улики правдивы. ~0.1 с на дело.
- **ИИ-напарники** (`app/ai/`): знания ИИ = свои улики + общие + выложенные на доску;
  версия = `engine.candidates(...)`. Ходы детерминированы по seed, LLM (OpenAI) только формулирует
  реплику, и каждая проверяется (имена — только из кандидатов, места/время/предметы — только
  из известных улик), иначе шаблон. Персоны и шаблоны: `app/ai/personas.py` (тексты — Ернур).
- Продакшен: `DATABASE_URL` (Postgres), `PUBLIC_WEB_URL` (домен фронта),
  `OPENAI_API_KEY` + `OPENAI_MODEL` (тексты улик и реплики ИИ; без ключа шаблоны),
  `AI_FRIENDS_ENABLED` (по умолчанию true). Новые колонки в существующих таблицах
  добавляются автоматически при старте (`db.add_missing_columns`).
