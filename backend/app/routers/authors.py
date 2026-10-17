"""
Author-facing routes (prefix /api/me).

Every route here depends on `get_current_author`, so an admin token cannot
reach them and — crucially — an author only ever sees their OWN rows, because
we filter by `current.id`, never by an id taken from the URL.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Author, Book, Ticket, TicketStatus, TicketCategory, TicketPriority
from ..auth import get_current_author
from ..schemas import AuthorOut, BookOut, TicketAuthorView, TicketCreate
from ..serializers import author_view
from ..ai.service import classify_ticket

router = APIRouter(prefix="/api/me", tags=["author portal"])


@router.get("", response_model=AuthorOut)
def my_profile(current: Author = Depends(get_current_author)):
    return current


@router.get("/books", response_model=list[BookOut])
def my_books(current: Author = Depends(get_current_author), db: Session = Depends(get_db)):
    return db.query(Book).filter(Book.author_id == current.id).all()


@router.get("/tickets", response_model=list[TicketAuthorView])
def my_tickets(current: Author = Depends(get_current_author), db: Session = Depends(get_db)):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.author_id == current.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )
    return [author_view(t) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=TicketAuthorView)
def my_ticket(ticket_id: int, current: Author = Depends(get_current_author),
              db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id, Ticket.author_id == current.id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return author_view(ticket)


@router.post("/tickets", response_model=TicketAuthorView, status_code=201)
def create_ticket(payload: TicketCreate, current: Author = Depends(get_current_author),
                  db: Session = Depends(get_db)):
    """
    Create a support ticket. If a book is named it must belong to this author.
    The AI triage (category + priority) runs here in ONE cheap call. If the AI
    is down, the rule-based fallback still gives a sensible category/priority,
    so ticket creation NEVER fails because of the AI.
    """
    book = None
    if payload.book_id is not None:
        book = db.query(Book).filter(
            Book.id == payload.book_id, Book.author_id == current.id
        ).first()
        if not book:
            raise HTTPException(status_code=400, detail="That book is not one of yours")

    triage = classify_ticket(payload.subject, payload.description)

    ticket = Ticket(
        author_id=current.id,
        book_id=book.id if book else None,
        subject=payload.subject,
        description=payload.description,
        status=TicketStatus.OPEN,
        ai_category=triage["category"],
        ai_priority=triage["priority"],
        category=triage["category"],      # effective value starts equal to AI
        priority=triage["priority"],
        ai_classification_note=triage["note"],
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return author_view(ticket)
