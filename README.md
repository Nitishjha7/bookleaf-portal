# BookLeaf Author Support Portal

A support desk for BookLeaf authors. Authors raise tickets about their books. Admins work from a
queue that Gemini has already categorised and prioritised, and can generate a policy-based draft
reply before answering.

**Live demo:** https://bookleaf-906520260355.asia-south1.run.app
(API docs at `/docs`, health at `/api/health`)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@bookleaf.com | admin123 |
| Author | priya.sharma@email.com | author123 |

Every author in `backend/seed_data.json` uses `author123`. The free database may be asleep, so
the first request can take a few seconds.

## Stack

| | |
|---|---|
| Backend | FastAPI, SQLAlchemy, Alembic migrations, JWT auth (httpOnly cookie) with role checks |
| Frontend | React, Vite |
| Database | PostgreSQL (Neon in production, Postgres in Docker locally, SQLite if `DATABASE_URL` is unset) |
| AI | Google Gemini (`gemini-3.8-flash`), keyword rules as fallback |
| Hosting | Google Cloud Run, built from this repo by Cloud Build on every push to `main` |
| CI | GitHub Actions: backend tests, frontend build, Docker builds |

## Run locally

With Docker:

```bash
GEMINI_API_KEY=your-key docker compose up --build
```

Frontend on http://localhost:8080, API docs on http://localhost:8099/docs. The key is optional;
without it triage uses keyword rules. The first start runs the migrations and loads the dataset
and a few sample tickets (triaged with keyword rules, so seeding uses no Gemini quota). Later starts
leave existing data alone.

Without Docker (Python 3.11 or 3.12, Node 20):

```bash
cd backend
python -m venv venv && source venv/bin/activate     # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env                                # add GEMINI_API_KEY
python -m app.bootstrap                           # migrations + sample data (only if the db is empty)
uvicorn app.main:app --reload --port 8099

cd frontend
npm install && npm run dev                          # http://localhost:5173
```

Tests:

```bash
cd backend && pip install -r requirements-dev.txt && pytest
```

They run on a temporary SQLite file with no API key, so they also cover the fallback path:
login, role separation, author data isolation, validation errors and the full ticket flow.

## How the AI is used

All Gemini calls go through `backend/app/ai/client.py`. The rest of the code calls `complete()` and
either gets text or an `AIUnavailable` error.

- **Triage, on ticket creation.** One small call returns category, priority and a short reason as
  JSON, using only the subject and description. If the call fails or the labels don't match our
  enums, keyword rules are used instead. Creating a ticket never depends on the AI.
- **Drafting, on request.** When an admin asks, the knowledge base and the figures for the one
  book in question are sent. This is the expensive call, so it doesn't run for every ticket. If it
  fails, the admin gets a short template.

Each result carries `source: "ai" | "fallback"`, which the UI shows. The model's original category
and priority are stored next to the current values, so admin overrides stay visible.

The key is read from `GEMINI_API_KEY` on the backend only. Change the model with `AI_MODEL`.
Quotas are per model, so if the main model is rate limited or down, `AI_FALLBACK_MODELS`
(comma separated) are tried in order before falling back to keyword rules.

## Design notes

- Authors and admins are separate tables. Replies (visible to the author) and internal notes
  (admin only) are separate tables, and the author serializer has no path to notes.
- Author routes always filter by the logged-in author's id, never an id from the URL.
- Role checks live in `auth.py` as dependencies, not in each route.
- The browser session is an httpOnly, SameSite=Lax cookie, so JavaScript never sees the token.
  Swagger and scripts can still send a Bearer header.
- Failed logins are limited to 5 per 15 minutes per IP and email (in memory, per instance).
- Schema changes go through Alembic (`alembic/versions`). `app/bootstrap.py` runs them on start,
  and stamps a database that was created before migrations existed.
- `/api/health` checks the database, so a free uptime pinger also keeps Neon awake.
- The ticket list polls every 5 seconds. Simple and enough for a support inbox.

```
backend/app/
  main.py, config.py, database.py, models.py, schemas.py, serializers.py
  auth.py            bcrypt, JWT, role dependencies
  seed.py            loads seed_data.json (drops tables), seed_demo.py adds sample tickets
  bootstrap.py       container start: migrate, then seed only an empty database
  ratelimit.py       failed-login limiter
  ai/                client.py (Gemini), service.py (triage, draft), knowledge_base.py
  routers/           auth.py, authors.py (/api/me), admin.py (/api/admin)
backend/alembic/     migrations
backend/tests/       pytest suite
frontend/src/        pages/author, pages/admin, Login, api.js
Dockerfile           single image (API + built frontend) used on Cloud Run
```

## API

All routes are under `/api` and need a Bearer token except login.

| Method | Path | Who | |
|--------|------|-----|---|
| POST | `/auth/login` | anyone | form fields `username` (email), `password`; sets the session cookie |
| POST | `/auth/logout` | anyone | clears the cookie |
| GET | `/auth/me` | any | role and name |
| GET | `/me`, `/me/books` | author | profile, own books |
| GET | `/me/tickets`, `/me/tickets/{id}` | author | own tickets with replies |
| POST | `/me/tickets` | author | `{book_id?, subject, description}` |
| GET | `/admin/tickets` | admin | queue, filters `status`, `category`, `priority` |
| GET | `/admin/tickets/{id}` | admin | ticket with AI fields and notes |
| POST | `/admin/tickets/{id}/ai-draft` | admin | generate a draft |
| POST | `/admin/tickets/{id}/responses` | admin | send a reply |
| PATCH | `/admin/tickets/{id}/status` `/category` `/priority` | admin | update or override |
| POST | `/admin/tickets/{id}/notes` | admin | internal note |
| POST | `/admin/tickets/{id}/assign` | admin | assign to yourself |
| GET | `/health` | anyone | database check, whether the AI key is set |

Invalid input returns 422, a missing or bad session 401, the wrong role 403, too many failed logins 429.

## Dataset edge cases

Books with no payout yet show "none yet". Books still in production have no MRP or ISBN and show
"—", and can still be selected on a ticket. Fully paid books and authors with one or many books
are handled.

Deployment steps are in [DEPLOYMENT.md](DEPLOYMENT.md), design reasoning in [WRITEUP.md](WRITEUP.md).
