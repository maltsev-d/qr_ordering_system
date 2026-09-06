# QR ordering system

QR-меню с онлайн-заказом для ресторанов в Лаосе/ЮВА. Гость сканирует QR на столе, выбирает язык, заказывает сам — заказ
мгновенно появляется у администратора на дашборде и дублируется в Telegram.

Демо-прототип, портфолио-проект. Первый рынок: Вьентьян, Луанг Прабанг, Ванг Вьенг.

---

## Стек

```
Backend:     FastAPI + SQLAlchemy (синхронный) + SQLite / PostgreSQL (Supabase)
Frontend:    Jinja2 + Alpine.js + чистый CSS (без npm/webpack)
Уведомления: Telegram Bot API
Флаги:       flag-icons (CDN)
Хостинг:     Render (план) + Supabase (БД)
```

---

## Структура проекта

```
qr_ordering_system/
├── main.py                 # FastAPI роуты, вся бизнес-логика
├── .env                    # DATABASE_URL, TG_BOT_TOKEN, TG_CHAT_ID
│
├── db/
│   ├── __init__.py
│   ├── database.py         # SQLAlchemy ORM-модели, create_tables(), get_db()
│   ├── models.py           # Pydantic-схемы, Enum (OrderType, OrderStatus, Language)
│   └── seed.py             # Заполнение БД демо-данными
│
├── static/
│   ├── logo.png            # Логотип ресторана (fallback → эмодзи 🍜)
│   └── img/                # Фото блюд (12 файлов, fallback → серый блок)
│
└── templates/
    ├── menu.html            # Customer: язык-пикер + меню + корзина + детали блюда
    ├── order_done.html       # Customer: подтверждение заказа + live-статус
    └── admin/
        ├── dashboard.html    # Admin: live-заказы + звонки официанту (poll 5 сек)
        ├── analytics.html    # Admin: аналитика (заказы, выручка, топ-блюда)
        └── menu.html          # TODO — управление меню
```

---

## База данных

8 таблиц: `restaurants`, `tables`, `categories`, `dishes`, `modifier_groups`, `modifiers`, `orders`, `order_items`,
`waiter_calls`.

Мультиязычность — отдельные колонки на каждый язык (`name_en`, `name_lo`, `name_cn`, `name_ru`, `name_th`, `name_ko`,
`name_fr`, `name_ar`), а не таблица переводов. Простое решение для 8 фиксированных языков.

Демо-данные (`seed.py`):

- 1 ресторан (Sabaidee Kitchen), 8 столов
- 4 категории, 12 блюд с модификаторами (острота, сладость)
- ~438 фейковых заказов за 30 дней с реалистичным распределением по времени суток
- ~25 фейковых вызовов официанта

---

## Запуск

```bash
pip install fastapi uvicorn jinja2 python-multipart sqlalchemy psycopg2-binary httpx python-dotenv qrcode[pil]

python db/seed.py        # один раз — заполнить БД
uvicorn main:app --reload
```

Открыть в браузере:

- Customer: `http://localhost:8000/menu/1/1` (id ресторана/стола — проверить в БД после seed)
- Admin dashboard: `http://localhost:8000/admin/dashboard`
- Admin analytics: `http://localhost:8000/admin/analytics`

---

## `.env`

```
DATABASE_URL=postgresql://postgres.xxxxx:PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
TG_BOT_TOKEN=your_bot_token
TG_CHAT_ID=your_chat_id
```

Если `DATABASE_URL` не задан — приложение падает на локальный `sqlite:///./qrmenu.db` (см. `db/database.py`).

**Supabase:** брать **Session pooler** connection string (порт 5432), не Direct connection — иначе возможна ошибка
резолвинга хоста на некоторых сетях/провайдерах.

---

## Customer Flow

```
Скан QR → /menu/{restaurant_id}/{table_id}
    │
    ├─ lang не указан → экран выбора языка (8 языков, флаги)
    │
    └─ lang указан → меню
         ├─ Категории (горизонтальный скролл) + "Все"
         ├─ Карточки блюд (фото/фолбэк, цена, теги)
         ├─ 🎲 Surprise me — случайное рекомендованное блюдо
         ├─ Карточка блюда → модификаторы, Popular with this
         ├─ Корзина → Dine-in/Takeaway → Place order
         └─ 🔔 Call Waiter (idle → calling → answered, с poll)
              │
              ▼
         POST /order → редирект /order-done/{id}?lang={lang}
              │
              ▼
         Экран подтверждения: статус заказа (live poll),
         WiFi пароль, повторный Call Waiter
```

Язык хранится только в URL (`?lang=`), без localStorage — по требованию "чтобы работало на время сессии, не более".

---

## Admin Flow

- **Dashboard** (`/admin/dashboard`) — live-заказы (poll 5 сек), звонки официанта, статы дня. Один клик — статус заказа
  двигается (new → accepted → ready → done).
- **Analytics** (`/admin/analytics`) — период (7/30/90 дней), заказы по времени суток, топ-5 блюд, разбивка по статусам,
  выручка по дням.
- **Menu management** — не реализовано, оставлено как TODO.

---

## Ключевые архитектурные решения

- **Синхронный SQLAlchemy** вместо async — проще для текущего масштаба, меньше багов с lazy loading.
- **Мультиязычность через колонки**, не через таблицу переводов — осознанный компромисс ради простоты при фиксированном
  наборе языков.
- **i18n на фронте через JS-объект** (`I18N` в `menu.html`/`order_done.html`) — все статичные UI-строки (кнопки, лейблы)
  не зависят от бэкенда, меняются мгновенно через Alpine.js.
- **Модификаторы хранятся как `{group_id: modifier_id}` в JSON** — расшифровываются на сервере
  (`build_modifier_label()`) в нужный язык при рендере `order_done` и dashboard.
- **Call Waiter — трёхстадийный статус** (`idle` → `calling` → `answered`) с poll каждые 5 сек, идентичная логика на
  клиентском экране и экране подтверждения заказа.
- **Live-обновления через polling**, не WebSocket — осознанное упрощение для MVP (задача из исходного плана: "poll
  каждые 5 сек достаточно для демо").
- **Telegram как MVP-канал уведомлений** вместо WhatsApp Business API — WA требует верифицированный бизнес-аккаунт,
  Telegram работает сразу и бесплатно.

---

## Что реализовано

- [x] `models.py`, `database.py`, `seed.py`
- [x] `main.py` — все customer + admin роуты
- [x] `menu.html` — язык-пикер, меню, корзина, детали блюда, i18n на 8 языков
- [x] `order_done.html` — статус заказа live, i18n, Call Waiter
- [x] `admin/dashboard.html` — live-заказы, звонки, статы
- [x] `admin/analytics.html` — период, топ-блюда, разбивка статусов, график выручки
- [x] Telegram-уведомления (новый заказ + вызов официанта)
- [x] Модификаторы блюд с расшифровкой на нужный язык
- [x] Миграция на Supabase (PostgreSQL)
- [x] QR-код генератор — эндпоинт `/admin/qr/{restaurant_id}/{table_id}` (набросан, не подключён к UI)

## Что осталось / TODO

- [ ] `admin/menu.html` — управление меню (86 блюда, редактирование)
- [ ] Деплой на Render
- [ ] Alembic-миграции (сейчас — `create_tables()` = `CREATE TABLE IF NOT EXISTS`, без версионирования схемы)
- [ ] WhatsApp-уведомления (опционально, после проверки Telegram-версии)

---

## Известные нюансы

- **SQLite vs Postgres**: SQLite не всегда enforce'ит foreign keys — багов с "битыми" `table_id` в seed-данных не было
  видно до переезда на Supabase. При миграции на Postgres обнаружились несовпадения ID (`seed.py` предполагал 8 столов,
  а создавался 1) — исправлено, теперь `seed.py` создаёт 8 реальных столов и использует их id для рандомных
  ордеров/звонков.
- **Прежде чем деплоить на Render** — БД должна быть внешней (Supabase), т.к. файловая система Render эфемерна и
  SQLite-файл будет сбрасываться при каждом деплое.
- **`create_tables()` при каждом старте** — безопасно (`CREATE TABLE IF NOT EXISTS`), не пересоздаёт существующие
  данные. Для реальных изменений схемы в будущем потребуется Alembic.

---

## Портфолио-контекст

Проект — часть портфолио для позиций в AI/LLM-development и Python backend. Демонстрирует: FastAPI + SQLAlchemy
архитектуру, мультиязычный i18n (сервер + клиент), интеграцию с Telegram Bot API, real-time-подобный UX через polling,
продуманный UX для низкотехнологичной аудитории (турист без приложений, официант без обучения).

Презентационные материалы (`instruction_ru_v2.md`) описывают ценность продукта для нетехнической аудитории —
владельцев/менеджеров кафе — с последующим переводом на английский и лаосский.