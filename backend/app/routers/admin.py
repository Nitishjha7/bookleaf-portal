"""Admin routes under /api/admin."""
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

_PRIORITY_RANK = {
    TicketPriority.CRITICAL: 0, TicketPriority.HIGH: 1,
    TicketPriority.MEDIUM: 2, TicketPriority.LOW: 3, None: 4,
}


def _get_ticket_or_404(ticket_id: int, db: Session) -> Ticket:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/tickets", response_model=list[TicketAdminView])
def ticket_queue(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    status: TicketStatus | None = Query(None),
    category: TicketCategory | None = Query(None),
    priority: TicketPriority | None = Query(None),
):
    """All tickets, most urgent first. Filters are enums so bad values give a 422."""
    q = db.query(Ticket)
    if status is not None:
        q = q.filter(Ticket.status == status)
    if category is not None:
        q = q.filter(Ticket.category == category)
    if priority is not None:
        q = q.filter(Ticket.priority == priority)

    tickets = q.all()
    # priority first, then oldest first
    tickets.sort(key=lambda t: (_PRIORITY_RANK.get(t.priority, 4), t.created_at))
    return [admin_view(t) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=TicketAdminView)
def get_ticket(ticket_id: int, db: Session = Depends(get_db),
               _: Admin = Depends(get_current_admin)):
    return admin_view(_get_ticket_or_404(ticket_id, db))


@router.post("/tickets/{ticket_id}/ai-draft", response_model=AIDraftOut)
def ai_draft(ticket_id: int, db: Session = Depends(get_db),
             _: Admin = Depends(get_current_admin)):
    """Drafted on request, not at ticket creation, to save tokens."""
    ticket = _get_ticket_or_404(ticket_id, db)
    result = draft_response(ticket)
    return AIDraftOut(draft=result["draft"], source=result["source"])


@router.post("/tickets/{ticket_id}/responses", response_model=TicketAdminView, status_code=201)
def respond(ticket_id: int, payload: RespondCreate, db: Session = Depends(get_db),
            admin: Admin = Depends(get_current_admin)):
    ticket = _get_ticket_or_404(ticket_id, db)
    ticket.responses.append(TicketResponse(
        admin_id=admin.id,
        body=payload.body,
        was_ai_drafted=1 if payload.was_ai_drafted else 0,
    ))
    # first reply moves it out of Open
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    db.commit()
    db.refresh(ticket)
    return admin_view(ticket)


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
    """ai_category stays as it was, we only flag that it was changed"""
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
