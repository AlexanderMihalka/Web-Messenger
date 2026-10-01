# Messenger Web

Навчальний веб-месенджер із приватними діалогами в реальному часі. Бекенд — FastAPI +
PostgreSQL, фронтенд — React + TypeScript, звʼязок у реальному часі — WebSocket.

Повна технічна специфікація: [`docs/TZ_Messenger_FastAPI_React.docx`](docs/TZ_Messenger_FastAPI_React.docx)
(доопрацьована версія — з уточненнями, позначеними на початку документа).

## Можливості

- Реєстрація та вхід (username або email), JWT access-токени, httpOnly refresh-cookie з ротацією
- Приватні діалоги 1-на-1, історія повідомлень зі сторінковою підгрузкою
- У реальному часі: нові повідомлення, редагування, видалення, статус прочитання, «в мережі» / «друкує…»
- Профіль: імʼя, username, опис, аватар (із серверною перевіркою, що це справді зображення)
- Блокування користувачів — забороняє надсилання нових повідомлень в обидва боки
- Адмін-панель: користувачі, статистика, журнал подій безпеки (auth, блокування)

## Стек

| Шар | Технології |
|---|---|
| Бекенд | FastAPI, SQLAlchemy 2, PostgreSQL, Alembic, Argon2id, PyJWT, WebSocket |
| Фронтенд | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router |
| Інфраструктура | Docker Compose, nginx (продакшн-віддача фронтенду + проксі) |

## Швидкий старт (Docker Compose)

```bash
cp .env.example .env
# відредагуйте .env: щонайменше SECRET_KEY (openssl rand -hex 32) і ADMIN_PASSWORD
docker compose up --build
```

- Застосунок: http://localhost:8080
- API напряму: http://localhost:8000, Swagger — http://localhost:8000/docs
- Обліковий запис адміністратора створюється автоматично зі значень `ADMIN_USERNAME` /
  `ADMIN_EMAIL` / `ADMIN_PASSWORD` з `.env` (лише якщо такого користувача ще нема).

## Розробка без Docker

### Бекенд

Потрібен Python 3.12+ і PostgreSQL 16 (локально або в контейнері).

```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # відредагуйте DATABASE_URL під вашу БД
alembic upgrade head
uvicorn app.main:app --reload
```

### Фронтенд

Потрібен Node.js 20+.

```bash
cd client
npm install
cp .env.example .env   # VITE_PROXY_TARGET — адреса бекенду, типово http://localhost:8000
npm run dev
```

Vite-девсервер (типово `:5173`) проксіює `/api`, `/uploads` і `/ws` на бекенд — у розробці
CORS не заважає.

## Тести

```bash
cd server
source .venv/bin/activate
export TEST_DATABASE_URL="postgresql+psycopg://messenger:messenger@localhost:5432/messenger_test"
pytest --cov=app --cov-report=term-missing   # unit + integration (у т.ч. реальні WebSocket-зʼєднання)
ruff check app migrations     # лінт
mypy app                      # типи
```

Якщо `TEST_DATABASE_URL` не задано, тести використовують файлову SQLite — зручно для
швидкого прогону, але деякі особливості PostgreSQL (наприклад точні повідомлення про
порушення обмежень) не перевіряються. У CI (`.github/workflows/ci.yml`) завжди
використовується справжній PostgreSQL.

## Структура репозиторію

```
server/                 FastAPI-застосунок
  app/
    core/                конфігурація, БД, безпека, помилки, rate limiting
    models/               SQLAlchemy ORM-моделі
    schemas/               Pydantic-схеми запитів/відповідей
    repositories/           SQL-запити, ізольовані від бізнес-логіки
    services/                бізнес-логіка (не залежить від FastAPI/HTTP)
    routers/                  REST-ендпоінти
    websocket/                 /ws — менеджер зʼєднань, події, обробник
  migrations/              Alembic-міграції
  tests/
    unit/                   сервіси й утиліти без HTTP
    integration/             повний HTTP- і WebSocket-стек через TestClient

client/                 React-застосунок
  src/
    api/                    типізовані виклики бекенду + axios-клієнт з refresh-flow
    context/, hooks/          автентифікація, React Query хуки для даних
    ws/                        WebSocket-контекст (реконект, presence) і typing-контекст
    components/, pages/         UI

docs/                   Технічна специфікація (доопрацьована) і діаграми
.github/workflows/      CI (лінт, типи, тести бекенду; білд фронтенду)
docker-compose.yml       postgres + backend + frontend одним стеком
```

## Ключові архітектурні рішення

- **Одне WebSocket-зʼєднання на користувача** (`/ws?token=...`), а не на діалог — так лічильники
  непрочитаних і статус «в мережі» оновлюються для всього списку чатів, а не лише відкритого.
  Токен передається query-параметром, бо `WebSocket` у браузері не дозволяє власні заголовки
  під час рукостискання.
- **REST — єдине джерело істини для запису повідомлень**; WebSocket розсилає вже збережену подію
  іншим підключеним учасникам. Клієнт відправляє через `POST`, WS використовує для push.
- **Access-токен — лише в памʼяті JS**, refresh-токен — у httpOnly cookie з ротацією при кожному
  оновленні. Це свідомий компроміс: XSS не може вкрасти довгоживучий токен, а CSRF пом'якшується
  тим, що cookie діє лише на `/api/v1/auth/*` і немає активного `SameSite`-небезпечного стану.
- **Синхронні (не `async def`) REST-роутери.** FastAPI виконує їх у threadpool, тому синхронний
  SQLAlchemy `Session` не блокує event loop. WebSocket-розсилку з такого роутера виконує
  `anyio.from_thread.run(...)` — офіційний спосіб anyio «достукатися» з робочого потоку назад
  у event loop, де живуть відкриті WS-зʼєднання.
- **`is_read` у повідомленні завжди означає «чи прочитав отримувач»**, а не «чи прочитав той, хто
  зараз дивиться» — тому те саме серіалізоване повідомлення коректно розсилається по WS обом
  учасникам діалогу без перерахунку під кожного з них.

## Відомі обмеження

- **Один процес бекенду.** Реєстр активних WebSocket-зʼєднань і rate-limiter живуть у пам'яті
  процесу (`app/websocket/manager.py`, `app/core/rate_limit.py`). З кількома воркерами/репліками
  кожен матиме власний реєстр, і push не долітав би до сокета на іншому воркері. Горизонтальне
  масштабування потребувало б спільного стану (Redis pub/sub + rate limiter) — свідомо поза
  межами цього навчального проєкту.
- **Журнал подій (`/admin/logs`)** фіксує лише події автентифікації й дії адміністратора/
  блокування — не кожне повідомлення чи діалог, щоб залишатись читомим, а не тонути в рутинному
  трафіку чату.
- Аватари зберігаються на локальному диску контейнера (`uploads_data` volume), не в обʼєктному
  сховищі — достатньо для навчального проєкту, але не для кількох реплік бекенду одночасно.
