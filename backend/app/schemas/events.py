"""Pydantic schemas for events."""

from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime


class EventCreate(BaseModel):
    source_type: str
    source_name: str
    raw_log: str
    normalized_data: Optional[Dict[str, Any]] = None
    severity: Optional[str] = "info"
    confidence: Optional[float] = 0.0
    mitre_technique: Optional[str] = None
    mitre_tactic: Optional[str] = None
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    username: Optional[str] = None
    action: Optional[str] = None
    timestamp: Optional[datetime] = None


class EventResponse(BaseModel):
    id: int
    source_type: str
    source_name: str
    raw_log: str
    normalized_data: Optional[Dict[str, Any]] = None
    severity: str
    confidence: float
    mitre_technique: Optional[str] = None
    mitre_tactic: Optional[str] = None
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    username: Optional[str] = None
    action: Optional[str] = None
    timestamp: Optional[datetime] = None
    ingested_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EventBatchCreate(BaseModel):
    events: List[EventCreate]


class EventFilter(BaseModel):
    source_type: Optional[str] = None
    severity: Optional[str] = None
    source_ip: Optional[str] = None
    username: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0
