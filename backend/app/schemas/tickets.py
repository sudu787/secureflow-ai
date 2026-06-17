"""Pydantic schemas for tickets."""

from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime


class TicketCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "other"
    priority: Optional[str] = "P3"
    requester: Optional[str] = None
    owner: Optional[str] = None
    source: Optional[str] = "manual"
    related_incident_id: Optional[int] = None
    related_alert_id: Optional[int] = None
    tags: Optional[List[str]] = None


class TicketResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str
    priority: str
    status: str
    owner: Optional[str] = None
    requester: Optional[str] = None
    source: str
    related_incident_id: Optional[int] = None
    related_alert_id: Optional[int] = None
    diagnosis: Optional[str] = None
    resolution: Optional[str] = None
    escalation_reason: Optional[str] = None
    timeline: Optional[Any] = None
    tags: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    owner: Optional[str] = None
    diagnosis: Optional[str] = None
    resolution: Optional[str] = None
    escalation_reason: Optional[str] = None
