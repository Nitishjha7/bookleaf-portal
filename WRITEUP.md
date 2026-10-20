# Approach and trade-offs

Nitish Kumar Jha

## What I focused on

The AI part and the structure of the code mattered most, so I built those first: data model and
auth, then triage and drafting with a fallback, then the API, and the two portals last. I'd rather
have the whole ticket flow working with a plain UI than a nice UI on top of half the logic.

## Decisions

- **Triage when a ticket is created, drafting only when an admin asks.** Triage is what makes the
  queue useful, since urgent tickets go to the top. A drafted reply is a bigger call and only needed
  when someone is about to answer, so it waits for a click. This is the main way I keep token usage down.
- **Category and priority in one call**, with only the subject and description. The knowledge base
  doesn't help pick a label and would be most of the tokens.
- **Gemini 2.5 Flash.** Classifying and writing a short policy-based reply doesn't need a bigger model,
  and Flash is quick and cheap enough that the admin isn't left waiting. The model name is an env var.
- **The AI can't break the app.** No key, rate limit or timeout: triage falls back to keyword rules and
  the admin gets a template to fill in. The UI says when a fallback was used.
- **Admins have the last word.** Category and priority can be overridden. I keep what the model said in
  separate columns, so it's possible to see later how often it was wrong.
- **SQLite or Postgres from one env var.** No setup locally, Postgres (Cloud SQL) when deployed.
- **Polling instead of websockets.** Refreshing every few seconds is fine for a support inbox and there
  is less to go wrong.
- **Cloud Run for hosting.** Both services are containers, it scales to zero, and the deploy is one
  GitHub Actions workflow. Secrets are in Secret Manager and GitHub authenticates with Workload
  Identity, so no key files in the repo.

## What I'd do next

- httpOnly cookies and refresh tokens instead of localStorage, plus rate limiting on login.
- Server-sent events for the ticket feed, and email notifications to authors.
- Use the stored AI-vs-admin values to measure how accurate the classification is and tune the prompt.
- Pull only the relevant policy section into the draft prompt instead of the whole knowledge base.
- Real file attachments (signed upload URLs), and SLA timers per priority.
- Alembic migrations, and more tests (the current ones cover auth, access rules and the ticket flow).
