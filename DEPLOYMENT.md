# Deployment

Production runs on Google Cloud Run with a Neon Postgres database. Cloud Build builds the root
`Dockerfile` from this repo on every push to `main`. The image contains the API and the built
frontend, so there is one service and no CORS setup.

## Cloud Run

1. Cloud Run, Create service, Continuously deploy from a repository, set up Cloud Build with this
   GitHub repo.
2. Branch `^main$`, build type Dockerfile, source `/Dockerfile`.
3. Region `asia-south1`, allow unauthenticated invocations, container port 8080.
4. Environment variables:

   | Name | Value |
   |------|-------|
   | `DATABASE_URL` | Neon connection string (`postgresql://...?sslmode=require`) |
   | `SECRET_KEY` | long random string |
   | `GEMINI_API_KEY` | key from https://aistudio.google.com/apikey |
   | `AI_MODEL` | `gemini-3.8-flash` |
   | `AI_FALLBACK_MODELS` | optional, defaults to `gemini-3.5-flash,gemini-flash-lite-latest` |

For anything beyond a demo, keep the three secrets in Secret Manager and reference them from the
service instead of plain environment variables.

## Database

Create a project on https://neon.tech and copy its connection string into `DATABASE_URL`. On the
first start `app/bootstrap.py` creates the tables and loads the dataset and sample tickets. It does
nothing if the database already has authors, so redeploys keep the data.

The free tier suspends the database after a few minutes of inactivity, so the first request after
that is slow. `pool_pre_ping` keeps stale connections from causing errors.

## Check

```bash
curl https://<service-url>/api/health
```

`"ai_active": true` means the Gemini key was picked up. Then log in with the accounts from the README.

## CI

`.github/workflows/ci.yml` runs on every push and pull request: pytest, the frontend build, and a
Docker build of both images. Deployment itself is handled by the Cloud Build trigger.
