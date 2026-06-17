"""Pydantic schemas for incidents."""

from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime


class IncidentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str
    priority: Optional[str] = "P3"
    related_alert_ids: Optional[List[int]] = None
    assigned_to: Optional[str] = None


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    priority: str
    related_alert_ids: Optional[Any] = None
    related_event_ids: Optional[Any] = None
    investigation_results: Optional[Any] = None
    root_cause: Optional[str] = None
    attack_path: Optional[str] = None
    affected_systems: Optional[Any] = None
    remediation_plan: Optional[Any] = None
    remediation_status: str
    assigned_to: Optional[str] = None
    executive_summary: Optional[str] = None
    technical_summary: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    root_cause: Optional[str] = None
    remediation_status: Optional[str] = None
