# Approach and trade-offs

Nitish Kumar Jha

## Priorities

I built the parts that carry the most risk first: data model and auth, then AI triage and drafting
with a fallback, then the API, then the two portals. The goal was a complete ticket flow that works
end to end, with a plain UI, rather than a polished UI over partial logic.

## Decisions

- **Triage at creation, drafting on request.** Triage is a small call and is what makes the queue
  useful. A draft is a larger call and is only needed when an admin is about to reply, so it waits
  for a click. This is the main cost control.
- **One call for category and priority**, sending only the subject and description. The knowledge
  base doesn't help choose a label and would make up most of the tokens.
- **Gemini Flash.** Classification and short policy-based replies don't need a large model. The
  model name is an environment variable. I started on `gemini-2.5-flash`, found it closed to new
  users, and moved to `gemini-3.8-flash` with a config change.
- **The AI can't block the product.** With no key, a timeout or a rate limit, triage uses keyword
  rules and the admin gets a template. The UI shows which path ran.
- **Admins decide.** Category and priority can be overridden. The model's original values are kept
  in separate columns, so its accuracy can be measured later.
- **Access control in one place.** Role checks are dependencies in `auth.py`. Author routes filter
  by the logged-in id, and notes live in their own table so they can't reach an author response.
- **Postgres in production, SQLite for quick local runs**, switched by `DATABASE_URL`.
- **Polling over websockets.** A few seconds of delay is fine for a support inbox and there is less
  to go wrong.
- **One container on Cloud Run.** The API serves the built frontend, which avoids CORS and a
  build-time API URL. Cloud Build deploys it on every push, and CI runs tests before that.

## Trade-offs I accepted

- Neon's free tier sleeps when idle, so the first request after a pause is slow.
- Seeding runs at container start, guarded by an empty-database check, instead of a migration step.
- The token is in localStorage for simplicity.

## Next

- httpOnly cookies, refresh tokens and login rate limiting.
- Server-sent events for the ticket feed, and email notifications to authors.
- Use the stored AI-versus-admin values to measure classification accuracy and tune the prompt.
- Retrieve only the relevant policy section for a draft instead of sending the whole knowledge base.
- Real attachments with signed upload URLs, and SLA timers per priority.
- Alembic migrations and wider test coverage.
