# BookLeaf — Author Support & Communication Portal

A two-portal support system (author-facing + admin-facing) with AI-assisted ticket
triage and reply drafting, built for BookLeaf's technical assignment.

Authors raise support queries about their books; the system automatically classifies
each query, scores its priority, and — when an admin opens it — drafts a reply grounded
in BookLeaf's actual policies. Admins can override anything the AI decides and always
stay in control of what gets sent.

---

## Tech stack (and why I chose it)

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | **Python + FastAPI** | Fast to build, typed request/response models give me free validation and Swagger docs, and it's a clean fit for calling an LLM API. |
| Database | **PostgreSQL** (SQLAlchemy ORM) | Relational data (authors → books, authors → tickets → responses/notes) maps naturally to tables with foreign keys. SQLAlchemy keeps the code DB-agnostic — it runs on **SQLite with zero setup** for a quick local run, and on Postgres in Docker/production via `DATABASE_URL`. |
| Frontend | **React (Vite)** | The assignment doesn't need SSR, so a lightweight SPA with React Router is the simplest thing that works. |
| AI / LLM | **Anthropic Claude 3.5 Haiku** | Cheap, fast, and more than capable for classification and short policy-grounded replies. Model choice is justified in detail below. |
| Real-time | **Polling** | The ticket feed polls every few seconds. For a support inbox this feels instant, needs no socket infrastructure, and never drops a connection. |

---

## Architecture

I kept a clean separation of concerns so nothing turns into spaghetti:

```
backend/app/
├── main.py           # app wiring: CORS, routers, global error handlers, /health
├── config.py         # all env-driven settings in one place (DB, secret, AI key)
├── database.py       # SQLAlchemy engine + session dependency
├── models.py         # the schema (Author, Book, Admin, Ticket, Response, Note)
├── schemas.py        # Pydantic request/response contracts (validation lives here)
├── auth.py           # password hashing, JWT, and the RBAC dependencies
├── serializers.py    # ticket -> author view / admin view (leak-proof by design)
├── seed.py           # load the provided dataset (10 authors, 18 books)
├── seed_demo.py      # optional: a few realistic demo tickets for the live demo
├── ai/
│   ├── knowledge_base.py  # BookLeaf's policies as context (server-side only)
│   ├── client.py          # the ONLY place that calls the LLM; isolates failures
│   └── service.py         # classify + prioritise + draft, with rule-based fallback
└── routers/
    ├── auth.py       # POST /api/auth/login  (authors and admins)
    ├── authors.py    # /api/me/*   (author-only, own data only)
    └── admin.py      # /api/admin/* (admin-only, all tickets)
```

**Design decisions worth calling out:**

- **Two user tables (Author, Admin), not one "users" table with a role flag.** They
  genuinely hold different data, and it makes the access rules trivial to reason about.
- **Responses and internal notes are separate tables.** An internal note can never
  accidentally be returned on an author route, because the author serializer has no code
  path that touches notes.
- **The ticket stores both the AI's original guess and the effective value.** `ai_category`
  / `ai_priority` are kept untouched; `category` / `priority` hold the current value; a flag
  records whether a human overrode it. So we never lose the fact that the AI and the human
  disagreed — useful signal if you ever want to measure the model.
- **One place talks to the LLM** (`ai/client.py`). Everything else calls `complete()` and
  either gets text or a clean `AIUnavailable` error. That's what makes graceful degradation
  simple rather than scattered.

---

## How the AI integration works

This was the highest-weighted part of the assignment, so I was deliberate about it.

### 1. Prompt engineering
- **Classification + priority** use one tightly-scoped system prompt that lists the six exact
  categories and the four priorities verbatim, plus short priority guidance (money owed and
  wrong-ISBN-live are Critical; bio edits are Low). The model must reply with a compact JSON
  object, which I parse and map back onto my enums — if the label doesn't match an enum, I fall
  back to rules rather than trust free text.
- **Drafting** uses a separate system prompt that injects BookLeaf's **Knowledge Base** and the
  **tone guidelines** (acknowledge first, use real numbers/dates, own BookLeaf's mistakes, give
  48-hour timelines, always end with a next step). It's explicitly told not to invent policies or
  numbers. The result sounds like a BookLeaf rep, not generic AI filler.

### 2. API key security
The key is read only on the backend from an environment variable (`ANTHROPIC_API_KEY`). It is
never hardcoded and never sent to the frontend. The frontend has no idea the LLM exists — it just
calls `/api/admin/tickets/{id}/ai-draft`.

### 3. Graceful degradation (AI down / rate-limited / no key)
- **Classification never blocks ticket creation.** If the AI call fails for any reason, a
  rule-based classifier (keyword + urgency heuristics) assigns a sensible category and priority,
  and the ticket is marked so the admin knows it was a fallback.
- **Drafting degrades to a safe, tone-correct skeleton** the admin can complete by hand, so an
  admin is never stuck staring at a blank box.
- Every AI result carries a `source: "ai" | "fallback"` field, and the UI shows which one ran.

### 4. Cost awareness
Three concrete choices keep token usage down:
1. **Classification and priority are one call, not two** — the model returns both in one small JSON object.
2. **That call sends only the subject + description.** It does *not* send the knowledge base or
   any ticket history — they aren't needed to pick a label and would be the biggest token cost.
3. **The knowledge base is sent only on the draft call, and only when an admin actually opens a
   ticket** (lazy, on demand) — never on every ticket at creation. I also pass just the *one*
   relevant book's figures, not the author's whole catalogue.

Net effect: creating a ticket costs one tiny call; the expensive context is spent once, only when
a human is about to use it.

### 5. Model choice
I went with **Claude 3.5 Haiku**. Classification and short, policy-grounded replies don't need a
frontier model — Haiku is accurate enough, noticeably cheaper, and fast enough that the admin
isn't left waiting for a draft. The LLM client is a thin wrapper, so switching models (or providers)
is a one-line change in `config.py`.

---

## Running it locally

### Option A — Docker (one command)
```bash
# optional: export ANTHROPIC_API_KEY=sk-ant-...   (works without it too)
docker compose up --build
```
- Frontend: http://localhost:8080
- API + Swagger docs: http://localhost:8099/docs
- Postgres: localhost:5433

The backend seeds the provided dataset and a few demo tickets on boot.

### Option B — Run the two parts by hand
**Backend** (uses SQLite automatically if you don't set `DATABASE_URL`):
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your ANTHROPIC_API_KEY (optional)
python -m app.seed            # loads 10 authors + 18 books
python -m app.seed_demo       # optional: adds demo tickets
uvicorn app.main:app --reload --port 8099
```
**Frontend:**
```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173 (proxies /api to :8099)
```

### Demo logins
| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@bookleaf.com` | `admin123` |
| Author | `priya.sharma@email.com` | `author123` |

Every author in the dataset logs in with their email and the password `author123`
(printed by `python -m app.seed`).

---

## API reference

All routes are under `/api`. Every route except login requires a `Bearer` JWT.
Full interactive docs (and a Swagger "Authorize" button) are at **`/docs`**.

### Auth
| Method | Endpoint | Who | Description |
|--------|----------|-----|-------------|
| POST | `/api/auth/login` | public | Email + password (form fields `username`, `password`). Returns a JWT + role. |
| GET | `/api/auth/me` | any | Current user's role and name. |

### Author portal (author token; always scoped to the caller's own data)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/me` | The author's profile. |
| GET | `/api/me/books` | The author's books with full royalty details. |
| GET | `/api/me/tickets` | All the author's tickets with responses (no internal notes). |
| GET | `/api/me/tickets/{id}` | A single ticket (404 if it isn't theirs). |
| POST | `/api/me/tickets` | Raise a ticket `{book_id?, subject, description}`. Runs AI triage. |

### Admin portal (admin token; all tickets)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/tickets` | Full queue. Filters: `?status=&category=&priority=`. Sorted urgent-first. |
| GET | `/api/admin/tickets/{id}` | Full ticket incl. AI metadata and internal notes. |
| POST | `/api/admin/tickets/{id}/ai-draft` | Generate an AI draft reply (on demand). |
| POST | `/api/admin/tickets/{id}/responses` | Send a reply `{body, was_ai_drafted}` (shows to the author). |
| PATCH | `/api/admin/tickets/{id}/status` | Update status. |
| PATCH | `/api/admin/tickets/{id}/category` | Override the AI category. |
| PATCH | `/api/admin/tickets/{id}/priority` | Override the AI priority. |
| POST | `/api/admin/tickets/{id}/notes` | Add an internal note (admin-only). |
| POST | `/api/admin/tickets/{id}/assign` | Assign the ticket to the current admin. |

Validation errors return `422` with details; auth failures return `401`; a forbidden
cross-role or cross-author access returns `403` — never a bare `500`.

---

## Handling the dataset's edge cases
The provided data is intentionally varied, and the app handles each case:
- **Zero royalties / never paid** (`royalty_pending` with `last_royalty_payout_date: null`) — shown as "none yet", no crash.
- **Books still in production** (`Midnight in Mysore`, `Raising Roots`) with `null` MRP/ISBN — rendered as "—" and still selectable when raising a ticket.
- **Fully-paid books** (`royalty_pending: 0`) — shown correctly.
- **Authors with one book vs several** — the UI and the "which book?" dropdown both adapt.

---

## Known limitations / what I'd do with more time
- **Auth hardening:** tokens are stored in `localStorage` for simplicity; in production I'd move to httpOnly cookies and add refresh tokens.
- **Real-time:** polling is intentionally simple. At higher volume I'd switch the ticket feed to Server-Sent Events.
- **File attachments:** the upload field is UI-only (as the brief allowed). I'd wire it to object storage (S3/GCS) with pre-signed URLs.
- **AI eval harness:** I store the AI's original vs overridden labels, which is exactly the data I'd use to build a small accuracy eval and tune the prompt.
- **Caching the draft:** right now a draft is regenerated each time; I'd cache the last draft per ticket to avoid repeat calls.
- **Tests:** I verified the backend end-to-end against every endpoint (auth, RBAC, lifecycle, AI fallback, note isolation); given more time I'd commit that as an automated pytest suite.
