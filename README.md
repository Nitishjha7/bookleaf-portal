# BookLeaf Author Support Portal

Support desk for BookLeaf authors. Authors log in, see their books and raise tickets.
Admins get a queue of tickets that is already categorised and prioritised by Gemini, and
can ask for a drafted reply based on BookLeaf's policies before answering.

- Backend: FastAPI + SQLAlchemy (SQLite locally, Postgres in Docker / Cloud SQL)
- Frontend: React + Vite
- AI: Google Gemini (`gemini-3.8-flash`), with keyword rules as a fallback if there is no key or the API fails
- Hosting: Docker Compose locally, Cloud Run on GCP (see [DEPLOYMENT.md](DEPLOYMENT.md))

## Running it

### Docker

```bash
GEMINI_API_KEY=your-key docker compose up --build
```

The key is optional. Without it everything works, triage just uses keyword rules.

| What | URL |
|------|-----|
| Frontend | http://localhost:8080 |
| API docs (Swagger) | http://localhost:8099/docs |
| Postgres | localhost:5433 |

Tables, the dataset and a few sample tickets are loaded on first start. Restarting doesn't
wipe anything (`app/bootstrap.py` skips seeding if there are already authors).

### Without Docker

Needs Python 3.11 or 3.12 and Node 20.

```bash
# backend
cd backend
python -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env              # put GEMINI_API_KEY in here if you have one
python -m app.seed                # authors + books (drops existing tables!)
python -m app.seed_demo           # optional sample tickets
uvicorn app.main:app --reload --port 8099
```

```bash
# frontend, in another terminal
cd frontend
npm install
npm run dev                       # http://localhost:5173, /api is proxied to :8099
```

### Logins

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@bookleaf.com | admin123 |
| Author | priya.sharma@email.com | author123 |

All authors in `backend/seed_data.json` use `author123`.

### Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Tests use a temporary SQLite file and no API key, so they also cover the fallback path. They check
login, that authors and admins can't use each other's routes, that an author can't see another
author's books or tickets, validation errors, and the whole ticket flow.

## How the AI part works

Everything that talks to Gemini is in `backend/app/ai/client.py`. The rest of the code calls
`complete()` and either gets text back or an `AIUnavailable` exception.

**Triage (when a ticket is created).** One call returns category, priority and a short reason as
JSON. Only the subject and description are sent. If the labels in the answer aren't one of our enum
values, or the call fails, `classify_ticket` uses keyword rules instead, so creating a ticket never
fails because of the AI.

**Drafting (when an admin asks).** The knowledge base (`ai/knowledge_base.py`) and the details of the
one book the ticket is about are sent along with instructions on tone. This is the expensive call, so
it only runs when an admin clicks the button, not for every new ticket. If it fails the admin gets a
short template to fill in.

Both results carry `source: "ai" | "fallback"` and the UI shows which one it was. The model's original
category and priority are stored next to the current ones, so you can see when an admin changed them.

The API key is only read by the backend from `GEMINI_API_KEY`, the browser never sees it. Set
`AI_MODEL` to change the model. Thinking is turned off for these calls because they are short and
thinking tokens count against the output limit.

## Code layout

```
backend/app/
  main.py          app, CORS, error handlers, /api/health
  config.py        settings from env vars
  database.py      engine + session
  models.py        tables
  schemas.py       request / response models
  auth.py          bcrypt, JWT, author/admin dependencies
  serializers.py   ticket -> author view / admin view
  seed.py          loads seed_data.json (drops tables first)
  seed_demo.py     sample tickets
  bootstrap.py     used by the Dockerfile, seeds only an empty db
  ai/              client.py (Gemini), service.py (triage + draft), knowledge_base.py
  routers/         auth.py, authors.py (/api/me), admin.py (/api/admin)
backend/tests/     pytest suite
frontend/src/      pages/author, pages/admin, Login, api.js
.github/workflows/ ci.yml, deploy.yml
```

Some choices worth knowing about:

- Authors and admins are separate tables because they hold different things.
- Replies (shown to the author) and internal notes (admins only) are separate tables, and the
  author serializer has no way to include notes.
- Author routes always filter by the logged-in author's id, never an id taken from the URL.
- The ticket list polls every 5 seconds. Simple, and good enough for a support inbox.

## API

All routes are under `/api` and need a Bearer token except login. Swagger is at `/docs`.

| Method | Path | Who | Notes |
|--------|------|-----|-------|
| POST | `/api/auth/login` | anyone | form fields `username` (email) and `password` |
| GET | `/api/auth/me` | any | role and name |
| GET | `/api/me` | author | profile |
| GET | `/api/me/books` | author | own books with royalty numbers |
| GET | `/api/me/tickets` | author | own tickets and replies |
| GET | `/api/me/tickets/{id}` | author | 404 if it isn't theirs |
| POST | `/api/me/tickets` | author | `{book_id?, subject, description}` |
| GET | `/api/admin/tickets` | admin | queue, filters `status`, `category`, `priority` |
| GET | `/api/admin/tickets/{id}` | admin | full ticket with AI fields and notes |
| POST | `/api/admin/tickets/{id}/ai-draft` | admin | generate a draft reply |
| POST | `/api/admin/tickets/{id}/responses` | admin | send a reply |
| PATCH | `/api/admin/tickets/{id}/status` | admin | |
| PATCH | `/api/admin/tickets/{id}/category` | admin | override category |
| PATCH | `/api/admin/tickets/{id}/priority` | admin | override priority |
| POST | `/api/admin/tickets/{id}/notes` | admin | internal note |
| POST | `/api/admin/tickets/{id}/assign` | admin | assign to yourself |
| GET | `/api/health` | anyone | status, and whether the AI key is set |

Bad input returns 422, a missing or bad token 401, the wrong role 403.

## Dataset edge cases

- Books with no payout yet (`last_royalty_payout_date: null`) show "none yet".
- Books still in production (`Midnight in Mysore`, `Raising Roots`) have no MRP or ISBN, shown as "—", and can still be picked when raising a ticket.
- Fully paid books (`royalty_pending: 0`) are fine.
- Authors with one book or several both work in the book dropdown.

## CI/CD

`.github/workflows/ci.yml` runs on every push and PR: pytest for the backend, `npm run build` for the
frontend, then it builds both Docker images.

`.github/workflows/deploy.yml` runs after CI passes on `main` and deploys both services to Cloud Run.
The one-time GCP setup is in [DEPLOYMENT.md](DEPLOYMENT.md).

## Not done

- The token is kept in localStorage. httpOnly cookies would be better.
- The attachment field on the new ticket form is UI only.
- Drafts aren't cached, so asking twice calls Gemini twice.
- No migrations (Alembic), tables are created with `create_all`.
- No rate limiting on login.
