# Pharma Connect

A B2B web platform that connects pharmacies with pharmaceutical distributor
companies. Pharmacies search a unified medication catalog, compare distributor
offers using a transparent best-offer ranking, and place orders through an
auditable state machine. Distributors manage their catalog and stock, fulfill
incoming orders, and get explainable stockout warnings.

## Highlights

- **Transparent best-offer ranking** — weighted formula (price 60%, stock
  25%, reliability 15%) with per-offer score breakdown surfaced in the UI.
  See [`docs/ranking-algorithm.md`](docs/ranking-algorithm.md).
- **Explicit order state machine + audit log** — every transition recorded
  in `order_events`. See [`docs/order-state-machine.md`](docs/order-state-machine.md).
- **Grounded RAG chatbot** — lexical retrieval over the medication catalog,
  Claude phrases answers using *only* the retrieved rows. See
  [`docs/chatbot-design.md`](docs/chatbot-design.md).
- **Real-time notifications** via Server-Sent Events with toast UI.
- **Stock-depletion forecast** using a 30-day moving average — no black-box
  ML.
- **REST API with auto-generated Swagger UI** at `/docs`.
- **Responsive UI** (mobile + tablet + desktop) with role-aware navigation
  for three roles: Pharmacy, Distributor, Admin.
- **i18n scaffolded** (English only today, structured for Arabic/RTL).

## Quick start

```bash
cp .env.example .env
# (optional) put an ANTHROPIC_API_KEY in .env to enable the chatbot
docker compose up --build
```

Once everything is up:

- Frontend: <http://localhost:5173>
- Backend Swagger UI: <http://localhost:8000/docs>
- Postgres: localhost:5432 (user/pass/db from `.env`)

The backend runs Alembic migrations and seeds demo data on every startup.

### Demo accounts (default password `Pass1234!`)

| Email                      | Role          |
|----------------------------|---------------|
| `alpha@pharma.local`       | Pharmacy      |
| `beta@pharma.local`        | Pharmacy      |
| `ibnsina@dist.local`       | Distributor   |
| `uniphar@dist.local`       | Distributor   |
| `ediphar@dist.local`       | Distributor   |
| `midpharm@dist.local`      | Distributor   |
| `admin@pharma.local`       | Admin (password `AdminPass123!`) |

## Repository layout

```
backend/          FastAPI service (Python 3.11)
  app/
    models/       SQLAlchemy ORM models
    schemas/      Pydantic request/response DTOs
    routers/      HTTP endpoints (one file per feature)
    services/     Business logic (ranking, FSM, forecast, chatbot...)
    seeds/        Idempotent demo-data seeder
    tests/        pytest suite
  alembic/        DB migrations
frontend/         React + Vite + Tailwind + TypeScript
  src/
    api/          Typed HTTP client
    auth/         AuthContext + route guard
    components/   Shared UI (layout, badges, empty states)
    features/     Per-role page modules: pharmacy/, distributor/, admin/
    hooks/        useNotifications (SSE subscription)
    i18n/         English strings (Arabic to follow)
docs/             ERD, FSM, ranking, chatbot design
docker-compose.yml
.env.example
```

## Architecture

```
       Browser
       │  HTTPS + SSE
       ▼
  ┌──────────────────────────────┐
  │   FastAPI                    │
  │   - Auth (JWT, RBAC)          │
  │   - Ranking, FSM, Forecast    │
  │   - Notification hub (SSE)    │
  │   - RAG chatbot               │
  └─────┬─────────────────┬──────┘
        │                 │
        ▼                 ▼
  ┌──────────┐    ┌──────────────┐
  │ Postgres │    │ Claude API   │
  └──────────┘    └──────────────┘
```

The application is intentionally a single backend service + single SPA.
No microservices, no Redis, no message broker, no vector DB. Every moving
part exists because it earns its place.

## Environment variables

Copy `.env.example` to `.env` and adjust. Key values:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection string |
| `JWT_SECRET` | **Required in production.** HMAC secret for tokens. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Lifetime of access tokens (default 30). |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Lifetime of refresh tokens (default 7). |
| `CORS_ORIGINS` | Comma-separated allowed origins. |
| `SMTP_*` | Optional SMTP config; without it, emails log to stdout. |
| `ANTHROPIC_API_KEY` | Enables the chatbot. Without it, the chatbot returns 503. |
| `CLAUDE_MODEL` | Defaults to `claude-haiku-4-5`. |
| `CHATBOT_DAILY_REQUEST_LIMIT` | Per-user daily question cap. |
| `VITE_API_BASE_URL` | Where the frontend points its API client. |

## Running tests

```bash
# Backend
cd backend && python -m pytest -q

# Frontend
cd frontend && npm test
```

The backend test suite covers:
- ranking formula (worked examples + tie-breaking)
- order state machine (legal transitions + audit log)
- stock-depletion forecast (no-demand and at-risk cases)
- chatbot retrieval (active-ingredient grouping)

## Running without Docker

### Backend

```bash
cd backend
pip install -e ".[dev]"
# point DATABASE_URL at your local Postgres, then:
alembic upgrade head
python -m app.seeds.seed
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Known limitations / future scope

- **Single-process notification hub** — fine for the demo; for multi-replica
  deployments, swap `services/notifications.py` for a Redis-backed pub/sub.
- **No payment processing** — explicitly out of scope per the project book.
- **Lexical RAG only** — the chatbot uses ILIKE-style search; embeddings
  would help if the corpus grows past a few thousand medications.
- **English only at launch** — i18n is wired through `react-i18next` so
  adding Arabic (with RTL support) is purely a translation file + Tailwind
  `dir="rtl"` flip.
- **Money stored as Float** — fine for a demo; production should use
  `Numeric(12, 2)`.

## Project background

This repository implements the **Pharma Connect** graduation project
described in Chapter 1 of the project book. The implementation followed a
five-phase plan: deep reading of the book → critical analysis and upgrade
proposals → planning → milestone-by-milestone build → testing & hardening.
The six upgrades adopted from Phase 2 (transparent ranking, explicit FSM,
Swagger docs, explainable stock forecast, SSE notifications, dockerized
demo) and three user-requested additions (chatbot, responsive UI,
two-role architecture) shape the system above.
