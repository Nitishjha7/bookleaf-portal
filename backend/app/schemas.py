"""Request and response models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from .models import TicketStatus, TicketCategory, TicketPriority


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


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


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    author_code: str
    name: str
    email: EmailStr
    phone: Optional[str]
    city: Optional[str]
    joined_date: Optional[str]


class TicketCreate(BaseModel):
    # no book_id = general ticket
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
    """no internal notes or AI fields"""
    responses: list[ResponseOut] = []


class TicketAdminView(TicketBase):
    """everything"""
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
    source: str  # "ai" or "fallback"
    reason: Optional[str] = None  # why it fell back
