"""
Database models (the schema).

Design notes
------------
- Author and Admin are kept as two separate tables rather than one "users"
  table with a role flag. They genuinely have different data (an author has
  books and tickets; an admin handles tickets), and keeping them apart makes
  the role-based access rules trivial to reason about.
- A Ticket is the centre of the system. It stores the AI's classification,
  priority and draft, PLUS whether a human overrode them — so we never lose
  the fact that the AI's original guess and the human decision differed.
- Responses (visible to the author) and internal notes (admin-only) are two
  separate tables on purpose, so there is no way to accidentally leak an
  internal note to an author.
"""
from datetime import datetime, timezone
import enum

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, JSON
)
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Enums (also used to validate admin overrides) -----------------------

class TicketStatus(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class TicketCategory(str, enum.Enum):
    ROYALTY = "Royalty & Payments"
    ISBN = "ISBN & Metadata Issues"
    PRINTING = "Printing & Quality"
    DISTRIBUTION = "Distribution & Availability"
    STATUS = "Book Status & Production Updates"
    GENERAL = "General Inquiry"


class TicketPriority(str, enum.Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# --- Core tables ----------------------------------------------------------

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    author_code = Column(String, unique=True, index=True)   # "AUTH001" from seed
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String)
    city = Column(String)
    joined_date = Column(String)                            # kept as given in seed
    hashed_password = Column(String, nullable=False)

    books = relationship("Book", back_populates="author", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="author", cascade="all, delete-orphan")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    book_code = Column(String, unique=True, index=True)     # "BK001"
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)

    title = Column(String, nullable=False)
    isbn = Column(String)
    genre = Column(String)
    publication_date = Column(String, nullable=True)
    status = Column(String)
    mrp = Column(Float)
    author_royalty_per_copy = Column(Float)
    total_copies_sold = Column(Integer, default=0)
    total_royalty_earned = Column(Float, default=0)
    royalty_paid = Column(Float, default=0)
    royalty_pending = Column(Float, default=0)
    last_royalty_payout_date = Column(String, nullable=True)
    print_partner = Column(String)
    available_on = Column(JSON, default=list)               # list[str]

    author = relationship("Author", back_populates="books")


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    # Nullable: a ticket can be "General / Account Level" with no book.
    book_id = Column(Integer, ForeignKey("books.id"), nullable=True)

    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False)

    # AI fields: we store BOTH the AI's original guess and the effective value
    # after any human override, so the two are never confused.
    ai_category = Column(Enum(TicketCategory), nullable=True)
    ai_priority = Column(Enum(TicketPriority), nullable=True)
    category = Column(Enum(TicketCategory), nullable=True)   # effective (AI or override)
    priority = Column(Enum(TicketPriority), nullable=True)   # effective (AI or override)
    category_overridden = Column(Integer, default=0)         # 0/1 flag
    priority_overridden = Column(Integer, default=0)
    ai_classification_note = Column(Text, nullable=True)     # one-line AI reasoning / fallback note

    assigned_admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    author = relationship("Author", back_populates="tickets")
    book = relationship("Book")
    assigned_admin = relationship("Admin")
    responses = relationship(
        "TicketResponse", back_populates="ticket",
        cascade="all, delete-orphan", order_by="TicketResponse.created_at"
    )
    notes = relationship(
        "InternalNote", back_populates="ticket",
        cascade="all, delete-orphan", order_by="InternalNote.created_at"
    )


class TicketResponse(Base):
    """A reply from the admin team. VISIBLE to the author."""
    __tablename__ = "ticket_responses"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    body = Column(Text, nullable=False)
    was_ai_drafted = Column(Integer, default=0)  # was this edited down from an AI draft?
    created_at = Column(DateTime, default=utcnow)

    ticket = relationship("Ticket", back_populates="responses")
    admin = relationship("Admin")


class InternalNote(Base):
    """An admin-only note on a ticket. NEVER returned on any author route."""
    __tablename__ = "internal_notes"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    ticket = relationship("Ticket", back_populates="notes")
    admin = relationship("Admin")
