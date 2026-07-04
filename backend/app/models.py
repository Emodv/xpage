"""Pydantic schemas shared across the API layer."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Channel(str, Enum):
    whatsapp = "whatsapp"
    telegram = "telegram"


class LeadStatus(str, Enum):
    new = "new"
    qualified = "qualified"
    booked = "booked"
    lost = "lost"


class Lead(BaseModel):
    id: str
    tenant_id: str
    channel: Channel
    external_id: str
    display_name: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None
    service_needed: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    status: LeadStatus
    ai_enabled: bool = True
    created_at: datetime
    updated_at: datetime


class Message(BaseModel):
    id: str
    tenant_id: str
    lead_id: str
    direction: str
    channel: Channel
    body: str
    ai_generated: bool = False
    created_at: datetime


class Appointment(BaseModel):
    id: str
    tenant_id: str
    lead_id: str
    calendar_event_id: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str
    revenue_amount: Optional[float] = None
    created_at: datetime


class InboundMessage(BaseModel):
    """Normalized shape both webhook parsers convert their payloads into."""

    tenant_slug: str
    channel: Channel
    external_id: str
    display_name: Optional[str] = None
    phone: Optional[str] = None
    text: str


class ManualReplyRequest(BaseModel):
    lead_id: str
    text: str


class AIQualification(BaseModel):
    """Structured output the GPT-4o responder must return for every reply."""

    reply_text: str
    language: str  # "fa" or "en"
    service_needed: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    ready_to_book: bool = False
    chosen_slot_index: Optional[int] = None  # 1-based index into offered slots, if lead picked one
    lead_status: LeadStatus = LeadStatus.new
