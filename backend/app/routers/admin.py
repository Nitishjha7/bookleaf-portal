"""
Admin-facing routes (prefix /api/admin).

Every route depends on `get_current_admin`. Admins can see and act on ALL
tickets. This is where ticket management, overrides, notes, responses and the
on-demand AI draft live.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Admin, Ticket, TicketResponse, InternalNote,
    TicketStatus, TicketCategory, TicketPriority,
)
from ..auth import get_current_admin
from ..schemas import (
    TicketAdminView, TicketBase, StatusUpdate, CategoryUpdate, PriorityUpdate,
    NoteCreate, RespondCreate, AIDraftOut,
)
from ..serializers import admin_view
from ..ai.service import draft_response

router = APIRouter(prefix="/api/admin", tags=["admin portal"])

# Sort order so the most urgent tickets float to the top of the queue.
_PRIORITY_RANK = {
    TicketPriority.CRITICAL: 0, TicketPriority.HIGH: 1,
    TicketPriority.MEDIUM: 2, TicketPriority.LOW: 3, None: 4,
}


def _get_ticket_or_404(ticket_id: int, db: Session) -> Ticket:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


# --- ticket queue ---------------------------------------------------------

@router.get("/tickets", response_model=list[TicketAdminView])
def ticket_queue(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    status: TicketStatus | None = Query(None),
    category: TicketCategory | None = Query(None),
    priority: TicketPriority | None = Query(None),
    assigned_to_me: bool = Query(False),
    me_id: int | None = None,
):
    """
    The full queue, newest first within priority. Optional filters by status,
    category and priority. Invalid filter values are rejected by FastAPI with a
    422 automatically, because the query params are typed as the enums.
    """
    q = db.query(Ticket)
    if status is not None:
        q = q.filter(Ticket.status == status)
    if category is not None:
        q = q.filter(Ticket.category == category)
    if priority is not None:
        q = q.filter(Ticket.priority == priority)

    tickets = q.all()
    # Urgent first, then oldest unresolved first (so nothing languishes).
    tickets.sort(key=lambda t: (_PRIORITY_RANK.get(t.priority, 4), t.created_at))
    return [admin_view(t) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=TicketAdminView)
def get_ticket(ticket_id: int, db: Session = Depends(get_db),
               _: Admin = Depends(get_current_admin)):
    return admin_view(_get_ticket_or_404(ticket_id, db))


# --- AI draft (on demand) -------------------------------------------------

@router.post("/tickets/{ticket_id}/ai-draft", response_model=AIDraftOut)
def ai_draft(ticket_id: int, db: Session = Depends(get_db),
             _: Admin = Depends(get_current_admin)):
    """
    Generate an AI draft reply for this ticket, grounded in the knowledge base
    and the one relevant book. Called only when an admin opens a ticket and
    asks for it — not at ticket creation — which is the core of the cost plan.
    `source` tells the UI whether the AI actually ran or we fell back.
    """
    ticket = _get_ticket_or_404(ticket_id, db)
    result = draft_response(ticket)
    return AIDraftOut(draft=result["draft"], source=result["source"])


# --- send a response (visible to the author) ------------------------------

@router.post("/tickets/{ticket_id}/responses", response_model=TicketAdminView, status_code=201)
def respond(ticket_id: int, payload: RespondCreate, db: Session = Depends(get_db),
            admin: Admin = Depends(get_current_admin)):
    ticket = _get_ticket_or_404(ticket_id, db)
    ticket.responses.append(TicketResponse(
        admin_id=admin.id,
        body=payload.body,
        was_ai_drafted=1 if payload.was_ai_drafted else 0,
    ))
    # Sending a reply moves an Open ticket to In Progress (sensible default).
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    db.commit()
    db.refresh(ticket)
    return admin_view(ticket)


# --- management: status / category / priority / notes / assign ------------

@router.patch("/tickets/{ticket_id}/status", response_model=TicketAdminView)
def update_status(ticket_id: int, payload: StatusUpdate, db: Session = Depends(get_db),
                  _: Admin = Depends(get_current_admin)):
    ticket = _get_ticket_or_404(ticket_id, db)
    ticket.status = payload.status
    db.commit()
    db.refresh(ticket)
    return admin_view(ticket)


@router.patch("/tickets/{ticket_id}/category", response_model=TicketAdminView)
def override_category(ticket_id: int, payload: CategoryUpdate, db: Session = Depends(get_db),
                      _: Admin = Depends(get_current_admin)):
    """Admin override of the AI category. We keep ai_category untouched and
    flag that a human changed it."""
    ticket = _get_ticket_or_404(ticket_id, db)
    ticket.category = payload.category
    ticket.category_overridden = 1 if payload.category != ticket.ai_category else 0
    db.commit()
    db.refresh(ticket)
    return admin_view(ticket)


@router.patch("/tickets/{ticket_id}/priority", response_model=TicketAdminView)
def override_priority(ticket_id: int, payload: PriorityUpdate, db: Session = Depends(get_db),
                      _: Admin = Depends(get_current_admin)):
    ticket = _get_ticket_or_404(ticket_id, db)
    ticket.priority = payload.priority
    ticket.priority_overridden = 1 if payload.priority != ticket.ai_priority else 0
    db.commit()
    db.refresh(ticket)
    return admin_view(ticket)


@router.post("/tickets/{ticket_id}/notes", response_model=TicketAdminView, status_code=201)
def add_note(ticket_id: int, payload: NoteCreate, db: Session = Depends(get_db),
             admin: Admin = Depends(get_current_admin)):
    """Internal note — admin only, never surfaced on any author route."""
    ticket = _get_ticket_or_404(ticket_id, db)
    ticket.notes.append(InternalNote(admin_id=admin.id, body=payload.body))
    db.commit()
    db.refresh(ticket)
    return admin_view(ticket)


@router.post("/tickets/{ticket_id}/assign", response_model=TicketAdminView)
def assign_to_me(ticket_id: int, db: Session = Depends(get_db),
                 admin: Admin = Depends(get_current_admin)):
    ticket = _get_ticket_or_404(ticket_id, db)
    ticket.assigned_admin_id = admin.id
    db.commit()
    db.refresh(ticket)
    return admin_view(ticket)
