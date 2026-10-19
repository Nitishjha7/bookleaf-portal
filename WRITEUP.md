# Approach & Trade-offs — BookLeaf Author Support Portal
*Nitish Kumar Jha*

## What I prioritised
I treated this the way the scoring sheet is weighted: **AI integration and architecture first**,
polish last. My goal was a system that actually works end-to-end — the full ticket lifecycle plus
a thoughtful AI layer — rather than a pretty UI with thin logic underneath.

So I built, in order: the data model and auth/RBAC, then the AI triage and drafting with graceful
degradation, then the REST API, then the two portals. The brief said "working software over
perfect software," so every feature I started, I finished to a working state before moving on.

## Key decisions and the trade-offs behind them
- **AI triage runs at ticket creation, but drafting runs on demand.** Classifying and prioritising
  a ticket the moment it arrives is what makes the admin queue useful (urgent things float up). But
  drafting a full reply is the expensive call, and most of its value is only needed when an admin
  actually opens the ticket — so I made it lazy. This single decision is the backbone of my cost
  strategy.
- **Classification + priority in one call.** Two labels, one small JSON response, subject +
  description only. I deliberately don't send the knowledge base or ticket history to classify,
  because they don't improve the label and they're the biggest token cost.
- **The AI never blocks the product.** If the LLM is down, rate-limited, or no key is configured,
  rule-based triage still runs and admins can still write replies. I'd rather ship something that
  degrades gracefully than something that breaks the moment an external API hiccups.
- **The AI assists, the human decides.** Category, priority and every drafted reply are editable
  and overridable. I store the AI's original guess separately from the human's decision so the two
  are never confused — and so the override data is there if BookLeaf ever wants to measure accuracy.
- **SQLite-or-Postgres via one env var.** Keeps local setup to zero config while giving a real
  relational schema in production. The brief cared about schema design, not the DB brand.
- **Polling over websockets.** For a support inbox, a few-second poll feels instant and removes a
  whole class of connection-management bugs. An honest trade-off I'd revisit only at scale.

## How I'd evolve this into a production system
- **Move auth to httpOnly cookies + refresh tokens**, add rate limiting and audit logging.
- **Switch the ticket feed to Server-Sent Events** and add email/WhatsApp notifications to authors.
- **Build an AI eval harness** from the original-vs-override data I already capture, and use it to
  tune prompts and track classification accuracy over time.
- **Add retrieval** so the draft pulls the *specific* policy paragraph it needs instead of the whole
  knowledge base — cheaper and sharper as the KB grows.
- **Wire up real file attachments** (pre-signed S3/GCS URLs) and an SLA timer per priority so the ops
  team can see what's breaching.
- **Add a proper test suite and CI**, plus structured logging and error tracking.

The core I've built — clean separation of concerns, a single isolated LLM boundary, and
human-in-the-loop AI — is designed so each of those is an addition, not a rewrite.
