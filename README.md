# Web Messenger

A learning web messenger with real-time private conversations. The backend is FastAPI + PostgreSQL, the frontend is React + TypeScript, and real-time delivery runs over WebSocket. The interface is available in **English and Ukrainian**.

![Chat](docs/screenshots/chat.png)


## Features

- Sign up and sign in (username or email), JWT access tokens, httpOnly refresh cookie with rotation
- Private 1-to-1 conversations with paginated message history
- Real time: new messages, editing, deleting, read receipts, "online" and "typing…" indicators
- Profile: name, username, bio, avatar (the server checks that the file is really an image)
- Blocking users: prevents sending new messages in both directions
- Admin panel: users, statistics, security event log (auth, blocking)
- **Bilingual interface**: Ukrainian and English, switched with the **UK / EN** buttons; the choice is remembered in the browser

## Tech stack

| Layer | Technologies |
|---|---|
| Backend | FastAPI, SQLAlchemy 2, PostgreSQL, Alembic, Argon2id, PyJWT, WebSocket |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router |
| Infrastructure | Docker Compose, nginx (serves the production frontend and proxies the API) |

## Quick start (Docker Compose)

```bash
cp .env.example .env
# edit .env: fill in POSTGRES_PASSWORD, SECRET_KEY and ADMIN_PASSWORD
# (a random value: openssl rand -hex 32)
docker compose up --build
```

- App: http://localhost:8080
- API directly: http://localhost:8000, Swagger: http://localhost:8000/docs
- The administrator account is created automatically from `ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env` (only if that user does not exist yet).
- The PostgreSQL port is published on `127.0.0.1` only, so the database is not reachable from the network.

`docker compose up` refuses to start until `POSTGRES_PASSWORD`, `SECRET_KEY` and `ADMIN_PASSWORD` are set, so no default passwords ever run by accident. Generate values with any of these:

```bash
# macOS / Linux
openssl rand -hex 32

# Node.js (any OS)
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# Windows PowerShell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
```

> The database password is applied only when the database volume is created. If you already started the project and then change `POSTGRES_PASSWORD`, run `docker compose down -v` first (this deletes the stored data).

## Interface language

Use the **UK / EN** switch in the header of the chat list, or in the top-right corner of the sign-in, sign-up, profile and admin pages.

- The language is stored in the browser's `localStorage` under the key `lang`. The default is Ukrainian.
- All interface texts are in `client/src/i18n/messages.ts`, one dictionary per language. The English dictionary is typed against the Ukrainian keys, so TypeScript will not let you forget a translation.
- Dates and times follow the selected language (`date-fns` locales).
- The API returns error messages in Ukrainian. The interface translates the known ones into the selected language and shows unknown ones as they are.
- User content (names, messages) is never translated.

To add a language, add a dictionary to `messages.ts`, extend `LANGS` in `client/src/i18n/core.ts` and map its date-fns locale in `getDateLocale()`.

## Screenshots

| Sign in | Sign-up validation |
|---|---|
| ![Sign in](docs/screenshots/login.png) | ![Sign-up validation](docs/screenshots/register-validation.png) |

| Chat (English) | Chat (Ukrainian) |
|---|---|
| ![Chat](docs/screenshots/chat.png) | ![Chat in Ukrainian](docs/screenshots/chat-ukrainian.png) |

| Profile | Admin: users |
|---|---|
| ![Profile](docs/screenshots/profile.png) | ![Admin users](docs/screenshots/admin-users.png) |

| Admin: event log |
|---|
| ![Admin event log](docs/screenshots/admin-logs.png) |

## Development without Docker

### Backend

Requires Python 3.12+ and PostgreSQL 16 (local or in a container).

```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # edit DATABASE_URL for your database; set SECRET_KEY and ADMIN_PASSWORD
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

Requires Node.js 20+.

```bash
cd client
npm install
cp .env.example .env   # VITE_PROXY_TARGET is the backend address, http://localhost:8000 by default
npm run dev
```

The Vite dev server (`:5173` by default) proxies `/api`, `/uploads` and `/ws` to the backend, so CORS does not get in the way during development.

## Tests

```bash
cd server
source .venv/bin/activate
export TEST_DATABASE_URL="postgresql+psycopg://messenger:messenger@localhost:5432/messenger_test"
pytest --cov=app --cov-report=term-missing   # unit + integration (including real WebSocket connections)
ruff check app migrations     # lint
mypy app                      # types
```

If `TEST_DATABASE_URL` is not set, the tests use a file-based SQLite database. That is convenient for a quick run, but some PostgreSQL specifics (for example exact constraint-violation messages) are not checked. CI (`.github/workflows/ci.yml`) always uses a real PostgreSQL.

Frontend checks:

```bash
cd client
npm run lint && npm run typecheck && npm run build
```

## Repository structure

```
server/                 FastAPI application
  app/
    core/                configuration, database, security, errors, rate limiting
    models/               SQLAlchemy ORM models
    schemas/               Pydantic request/response schemas
    repositories/           SQL queries, isolated from business logic
    services/                business logic (independent of FastAPI/HTTP)
    routers/                  REST endpoints
    websocket/                 /ws: connection manager, events, handler
  migrations/              Alembic migrations
  tests/
    unit/                   services and utilities without HTTP
    integration/             full HTTP and WebSocket stack through TestClient

client/                 React application
  src/
    api/                    typed backend calls + axios client with refresh flow
    context/, hooks/          authentication, React Query data hooks
    i18n/                      UK/EN dictionaries, language provider and helpers
    ws/                         WebSocket context (reconnect, presence) and typing context
    components/, pages/          UI (LangSwitch.tsx is the language switch)

docs/                   Technical specification (revised), diagrams and screenshots
.github/workflows/      CI (lint, types, backend tests; frontend build)
docker-compose.yml       postgres + backend + frontend as one stack
```

## Key architectural decisions

- **One WebSocket connection per user** (`/ws?token=...`), not per conversation. That way unread counters and "online" status update for the whole chat list, not just the open conversation. The token is passed as a query parameter because the browser `WebSocket` API does not allow custom headers during the handshake.
- **REST is the single source of truth for writing messages**; WebSocket pushes the already-saved event to the other connected participants. The client sends through `POST` and uses WS only for push.
- **The access token lives only in JS memory**; the refresh token lives in an httpOnly cookie that is rotated on every refresh. This is a deliberate trade-off: XSS cannot steal a long-lived token, and CSRF is mitigated because the cookie is only sent to `/api/v1/auth/*`.
- **Synchronous (not `async def`) REST routers.** FastAPI runs them in a threadpool, so the synchronous SQLAlchemy `Session` does not block the event loop. WebSocket fan-out from such a router goes through `anyio.from_thread.run(...)`, the official way to reach back into the event loop where the open WS connections live.
- **`is_read` on a message always means "has the recipient read it"**, not "has whoever is looking read it", so the same serialized message can be sent over WS to both participants without recalculating for each of them.

## Security notes

- Passwords are hashed with Argon2id; access tokens are short-lived (15 minutes) and refresh tokens rotate.
- Rate limiting is enabled by default, avatar uploads are verified server-side, and CORS is limited to the configured origins.
- Nothing secret is stored in the repository: `.env` files are in `.gitignore`, and Docker Compose reads `POSTGRES_PASSWORD`, `SECRET_KEY` and `ADMIN_PASSWORD` from `.env` and refuses to start without them. The backend also refuses to start in production with a default or short `SECRET_KEY`.
- The PostgreSQL port is bound to `127.0.0.1`. Before deploying anywhere public, put the services behind HTTPS and set `COOKIE_SECURE=true`.
- The fonts (Fraunces and Manrope) are loaded from Google Fonts in `client/index.html`. For a fully self-hosted deployment, bundle them locally.

## Known limitations

- **A single backend process.** The registry of active WebSocket connections and the rate limiter live in process memory (`app/websocket/manager.py`, `app/core/rate_limit.py`). With several workers or replicas each would have its own registry, and a push would not reach a socket on another worker. Horizontal scaling would need shared state (Redis pub/sub and a shared rate limiter), which is deliberately out of scope for this learning project.
- **The event log (`/admin/logs`)** records only authentication events and admin/blocking actions, not every message or conversation, so that it stays readable.
- Avatars are stored on the container's local disk (the `uploads_data` volume), not in object storage. That is fine for a learning project, but not for several backend replicas at once.
- The Swagger documentation and the API error messages are in Ukrainian; the web interface translates the known error messages.
