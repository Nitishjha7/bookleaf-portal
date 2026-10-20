"""Database tables.

Author and Admin are separate tables, and replies and internal notes are separate
tables, so a note can never end up on an author route by mistake.
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


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    author_code = Column(String, unique=True, index=True)   # "AUTH001" from seed
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String)
    city = Column(String)
    joined_date = Column(String)                            # plain string, same as the seed file
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
    # no book = general / account level ticket
    book_id = Column(Integer, ForeignKey("books.id"), nullable=True)

    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False)

    # ai_* is what the model said, category/priority is the current value (may be overridden)
    ai_category = Column(Enum(TicketCategory), nullable=True)
    ai_priority = Column(Enum(TicketPriority), nullable=True)
    category = Column(Enum(TicketCategory), nullable=True)   # current value
    priority = Column(Enum(TicketPriority), nullable=True)   # current value
    category_overridden = Column(Integer, default=0)         # 0/1
    priority_overridden = Column(Integer, default=0)
    ai_classification_note = Column(Text, nullable=True)     # short reason from the model, or the fallback note

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
    """reply to the author, visible to them"""
    __tablename__ = "ticket_responses"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    body = Column(Text, nullable=False)
    was_ai_drafted = Column(Integer, default=0)  # started from an AI draft
    created_at = Column(DateTime, default=utcnow)

    ticket = relationship("Ticket", back_populates="responses")
    admin = relationship("Admin")


class InternalNote(Base):
    """admin-only, never returned by the author routes"""
    __tablename__ = "internal_notes"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    ticket = relationship("Ticket", back_populates="notes")
    admin = relationship("Admin")
