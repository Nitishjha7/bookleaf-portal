"""
Pydantic schemas — the request/response contracts.

These give us automatic input validation (bad input -> 422 with a clear
message, never a 500) and a typed, documented API in Swagger.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from .models import TicketStatus, TicketCategory, TicketPriority


# --- auth -----------------------------------------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


# --- books ----------------------------------------------------------------

class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    book_code: str
    title: str
    isbn: Optional[str]
    genre: Optional[str]
    publication_date: Optional[str]
    status: Optional[str]
    mrp: Optional[float]
    author_royalty_per_copy: Optional[float]
    total_copies_sold: Optional[int]
    total_royalty_earned: Optional[float]
    royalty_paid: Optional[float]
    royalty_pending: Optional[float]
    last_royalty_payout_date: Optional[str]
    print_partner: Optional[str]
    available_on: list[str] = []


# --- author profile -------------------------------------------------------

class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    author_code: str
    name: str
    email: EmailStr
    phone: Optional[str]
    city: Optional[str]
    joined_date: Optional[str]


# --- tickets --------------------------------------------------------------

class TicketCreate(BaseModel):
    # book_id is optional -> "General / Account Level" ticket.
    book_id: Optional[int] = None
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5, max_length=5000)


class ResponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    body: str
    was_ai_drafted: int
    created_at: datetime
    admin_name: Optional[str] = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    body: str
    created_at: datetime
    admin_name: Optional[str] = None


class TicketBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject: str
    description: str
    status: TicketStatus
    category: Optional[TicketCategory]
    priority: Optional[TicketPriority]
    created_at: datetime
    updated_at: datetime
    book_title: Optional[str] = None
    book_code: Optional[str] = None


class TicketAuthorView(TicketBase):
    """What an author sees — responses included, NO internal notes, NO AI meta."""
    responses: list[ResponseOut] = []


class TicketAdminView(TicketBase):
    """What an admin sees — everything, including AI meta and internal notes."""
    author_name: str
    author_email: str
    ai_category: Optional[TicketCategory]
    ai_priority: Optional[TicketPriority]
    category_overridden: int
    priority_overridden: int
    ai_classification_note: Optional[str]
    assigned_admin_id: Optional[int]
    assigned_admin_name: Optional[str] = None
    responses: list[ResponseOut] = []
    notes: list[NoteOut] = []


# --- admin actions --------------------------------------------------------

class StatusUpdate(BaseModel):
    status: TicketStatus


class CategoryUpdate(BaseModel):
    category: TicketCategory


class PriorityUpdate(BaseModel):
    priority: TicketPriority


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=3000)


class RespondCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    was_ai_drafted: bool = False


class AIDraftOut(BaseModel):
    draft: str
    source: str  # "ai" or "fallback" — tells the UI whether the AI actually ran
