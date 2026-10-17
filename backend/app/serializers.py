"""
Turn ORM Ticket objects into the right response shape.

Two separate functions so the author view and the admin view can never be
confused: the author serializer simply has no code path that emits internal
notes or AI metadata.
"""
from .models import Ticket
from .schemas import (
    TicketAuthorView, TicketAdminView, ResponseOut, NoteOut
)


def _responses(ticket: Ticket) -> list[ResponseOut]:
    return [
        ResponseOut(
            id=r.id, body=r.body, was_ai_drafted=r.was_ai_drafted,
            created_at=r.created_at,
            admin_name=r.admin.name if r.admin else "BookLeaf Support",
        )
        for r in ticket.responses
    ]


def author_view(ticket: Ticket) -> TicketAuthorView:
    return TicketAuthorView(
        id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        category=ticket.category,
        priority=ticket.priority,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        book_title=ticket.book.title if ticket.book else None,
        book_code=ticket.book.book_code if ticket.book else None,
        responses=_responses(ticket),
    )


def admin_view(ticket: Ticket) -> TicketAdminView:
    return TicketAdminView(
        id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        category=ticket.category,
        priority=ticket.priority,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        book_title=ticket.book.title if ticket.book else None,
        book_code=ticket.book.book_code if ticket.book else None,
        author_name=ticket.author.name,
        author_email=ticket.author.email,
        ai_category=ticket.ai_category,
        ai_priority=ticket.ai_priority,
        category_overridden=ticket.category_overridden,
        priority_overridden=ticket.priority_overridden,
        ai_classification_note=ticket.ai_classification_note,
        assigned_admin_id=ticket.assigned_admin_id,
        assigned_admin_name=ticket.assigned_admin.name if ticket.assigned_admin else None,
        responses=_responses(ticket),
        notes=[
            NoteOut(id=n.id, body=n.body, created_at=n.created_at,
                    admin_name=n.admin.name if n.admin else "Admin")
            for n in ticket.notes
        ],
    )
