"""Pydantic schemas for alerts."""

from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime


class AlertCreate(BaseModel):
    event_id: Optional[int] = None
    alert_type: str
    severity: str
    confidence: Optional[float] = 0.0
    title: str
    description: Optional[str] = None
    affected_assets: Optional[List[str]] = None
    evidence: Optional[Dict[str, Any]] = None
    mitre_id: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique_name: Optional[str] = None
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    priority: Optional[str] = "P3"


class AlertResponse(BaseModel):
    id: int
    event_id: Optional[int] = None
    alert_type: str
    severity: str
    confidence: float
    title: str
    description: Optional[str] = None
    affected_assets: Optional[Any] = None
    evidence: Optional[Any] = None
    mitre_id: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique_name: Optional[str] = None
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    status: str
    priority: str
    assigned_to: Optional[str] = None
    investigation_summary: Optional[str] = None
    remediation_plan: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    investigation_summary: Optional[str] = None
    remediation_plan: Optional[str] = None
