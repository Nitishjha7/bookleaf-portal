"""Ticket triage and reply drafting.

Classify + priority is a single small call (subject and description only).
The knowledge base is only sent when an admin asks for a draft, and only with
the one book the ticket is about. If Gemini fails we use keyword rules.
"""
from __future__ import annotations
import json
import re

from ..models import Ticket, Book, TicketCategory, TicketPriority
from .client import complete, AIUnavailable
from .knowledge_base import KNOWLEDGE_BASE, CATEGORIES, PRIORITIES



def _to_category(value: str | None) -> TicketCategory | None:
    if not value:
        return None
    value = value.strip()
    for c in TicketCategory:
        if c.value.lower() == value.lower():
            return c
    return None


def _to_priority(value: str | None) -> TicketPriority | None:
    if not value:
        return None
    for p in TicketPriority:
        if p.value.lower() == value.strip().lower():
            return p
    return None


# classify + priority

_CLASSIFY_SYSTEM = f"""You are a triage assistant for BookLeaf Publishing's author-support desk.
Classify each author query into exactly one category and assign a priority.

Categories (choose one, verbatim):
{chr(10).join('- ' + c for c in CATEGORIES)}

Priorities (choose one, verbatim): {', '.join(PRIORITIES)}

Priority guidance:
- Critical: money owed/overdue, wrong ISBN live, legal/defamation, anything blocking sales or payments for a long time.
- High: ISBN/metadata errors, print defects on delivered copies, book unavailable on a store.
- Medium: production delays, status questions, royalty-breakdown questions.
- Low: general how-to, bio/description edits, informational queries.

Respond with only a compact JSON object, no prose:
{{"category": "<one category>", "priority": "<one priority>", "reason": "<max 12 words>"}}"""


def classify_ticket(subject: str, description: str) -> dict:
    """Returns category, priority, note and source ('ai' or 'fallback'). Doesn't raise."""
    user = f"Subject: {subject}\n\nDescription: {description}"
    try:
        raw = complete(system=_CLASSIFY_SYSTEM, user=user, max_tokens=120, temperature=0.0)
        parsed = _extract_json(raw)
        category = _to_category(parsed.get("category"))
        priority = _to_priority(parsed.get("priority"))
        if category and priority:
            return {
                "category": category,
                "priority": priority,
                "note": f"AI: {parsed.get('reason', '').strip()}"[:200],
                "source": "ai",
            }
        # labels didn't match our enums, use the rules instead
    except AIUnavailable as e:
        reason = str(e)[:90]
    else:
        reason = "unexpected labels from the model"
    result = _rule_based_classify(subject, description)
    result["note"] = f"Rule-based fallback ({reason})"
    result["source"] = "fallback"
    return result


def _extract_json(raw: str) -> dict:
    """model sometimes wraps the json in text, grab the first {...}"""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


# keyword fallback for when gemini is unavailable

_KEYWORDS = [
    (TicketCategory.ROYALTY,      ["royalt", "payment", "payout", "paid", "money", "earning", "bank"]),
    (TicketCategory.ISBN,         ["isbn", "metadata", "barcode", "imprint"]),
    (TicketCategory.PRINTING,     ["print", "quality", "misprint", "binding", "blurry", "page", "defect", "reprint"]),
    (TicketCategory.DISTRIBUTION, ["amazon", "flipkart", "unavailable", "listing", "distribut", "out of stock", "store"]),
    (TicketCategory.STATUS,       ["status", "typeset", "proofread", "cover", "production", "when will", "stuck", "delay"]),
]


def _rule_based_classify(subject: str, description: str) -> dict:
    text = f"{subject} {description}".lower()
    category = TicketCategory.GENERAL
    for cat, words in _KEYWORDS:
        if any(w in text for w in words):
            category = cat
            break

    priority = TicketPriority.LOW
    if any(w in text for w in ["month", "still haven", "never received", "wrong isbn",
                               "overdue", "urgent", "not received", "6 month", "legal"]):
        priority = TicketPriority.CRITICAL
    elif category in (TicketCategory.ISBN, TicketCategory.PRINTING, TicketCategory.DISTRIBUTION):
        priority = TicketPriority.HIGH
    elif category in (TicketCategory.ROYALTY, TicketCategory.STATUS):
        priority = TicketPriority.MEDIUM

    return {
        "category": category,
        "priority": priority,
        "note": "Rule-based fallback (AI unavailable)",
    }


# reply drafting

_DRAFT_SYSTEM = """You are a support representative for BookLeaf Publishing writing a reply to an author.
Write as BookLeaf, using only the policies in the knowledge base below. Follow these tone rules:
empathetic and professional, acknowledge the concern first, use the author's actual numbers/dates/status,
own any BookLeaf mistake directly, give concrete timelines (e.g. 48 hours) when escalating, and END with a
clear next step. Do not invent policies, numbers, or facts that are not provided. Keep it to a few short
paragraphs. Output only the reply body — no subject line, no placeholders like [Name].

KNOWLEDGE BASE
--------------
""" + KNOWLEDGE_BASE


def _book_context(book: Book | None) -> str:
    """only this book's numbers, not the whole catalogue"""
    if book is None:
        return "This ticket is general / account-level (not about a specific book)."
    return (
        f"Book: {book.title} (ISBN {book.isbn}, genre {book.genre})\n"
        f"Status: {book.status}\n"
        f"MRP: Rs.{book.mrp}; royalty per copy: Rs.{book.author_royalty_per_copy}\n"
        f"Copies sold: {book.total_copies_sold}\n"
        f"Royalty earned: Rs.{book.total_royalty_earned}; paid: Rs.{book.royalty_paid}; "
        f"pending: Rs.{book.royalty_pending}\n"
        f"Last payout date: {book.last_royalty_payout_date or 'none yet'}\n"
        f"Print partner: {book.print_partner}; available on: {', '.join(book.available_on or []) or 'not listed yet'}"
    )


def draft_response(ticket: Ticket) -> dict:
    """Returns draft and source ('ai' or 'fallback'). Doesn't raise."""
    user = (
        f"Author name: {ticket.author.name}\n"
        f"Category (triaged): {ticket.category.value if ticket.category else 'Unknown'}\n\n"
        f"{_book_context(ticket.book)}\n\n"
        f"--- Author's query ---\n"
        f"Subject: {ticket.subject}\n"
        f"Message: {ticket.description}\n\n"
        f"Write BookLeaf's reply."
    )
    try:
        draft = complete(system=_DRAFT_SYSTEM, user=user, max_tokens=600, temperature=0.4)
        if draft:
            return {"draft": draft, "source": "ai", "reason": None}
        reason = "empty response from the model"
    except AIUnavailable as e:
        reason = str(e)[:150]
    return {"draft": _fallback_draft(ticket), "source": "fallback", "reason": reason}


def _fallback_draft(ticket: Ticket) -> str:
    """bare template so the admin isn't staring at an empty box"""
    name = ticket.author.name.split()[0] if ticket.author and ticket.author.name else "there"
    return (
        f"Hi {name},\n\n"
        f"Thank you for reaching out, and I'm sorry for any inconvenience regarding "
        f"\"{ticket.subject}\". I completely understand your concern.\n\n"
        f"[AI drafting is not available right now, please complete this reply using the "
        f"relevant BookLeaf policy and the author's specific details.]\n\n"
        f"We'll look into this and get back to you within 48 hours with a clear update.\n\n"
        f"Warm regards,\nBookLeaf Author Support"
    )
