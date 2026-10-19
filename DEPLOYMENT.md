# Deployment guide

Two easy paths. Either gives BookLeaf a live URL to test both portals.

## Option 1 — Render (backend + Postgres) + Vercel (frontend)

### Backend on Render
1. Push this repo to GitHub, then on Render: **New → Web Service**, point it at the repo,
   root directory `backend`.
2. Environment: **Docker** (the `backend/Dockerfile` is picked up automatically), or
   **Python** with build `pip install -r requirements.txt` and start
   `python -m app.seed && python -m app.seed_demo && uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Add a **Render PostgreSQL** instance and set these env vars on the web service:
   - `DATABASE_URL` → the Render Postgres *internal* URL
   - `SECRET_KEY` → a long random string (`python -c "import secrets;print(secrets.token_hex(32))"`)
   - `ANTHROPIC_API_KEY` → your key
   - `AI_MODEL` → `claude-3-5-haiku-20241022`
   - `CORS_ORIGINS` → your Vercel URL (e.g. `https://bookleaf-portal.vercel.app`)
4. Deploy. Your API is at `https://<service>.onrender.com` (docs at `/docs`).

### Frontend on Vercel
1. On Vercel: **Add New → Project**, import the repo, set **Root Directory** to `frontend`.
2. Framework preset: **Vite**. Build `npm run build`, output `dist`.
3. Add env var `VITE_API_BASE` = your Render backend URL (e.g. `https://<service>.onrender.com`).
4. Deploy. Share the Vercel URL as the live demo.

## Option 2 — Railway (all-in-one)
1. New project → Deploy from repo.
2. Add a **PostgreSQL** plugin; Railway injects `DATABASE_URL`.
3. Add a service for `backend/` (Dockerfile) and one for `frontend/` (static) — set the same
   env vars as above.

## Option 3 — Local, one command
```bash
export ANTHROPIC_API_KEY=sk-ant-...   # optional
docker compose up --build
# frontend http://localhost:8080 · API http://localhost:8099/docs
```

## After deploying
- Confirm `GET /api/health` returns `{"status":"ok","ai_active":true,...}` (ai_active is `true`
  once the key is set).
- Log in with the demo credentials in the README and check both portals.
- The live demo comes **pre-seeded** with the provided dataset and a few sample tickets.
