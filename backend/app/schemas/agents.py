"""Pydantic schemas for AI agents."""

from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[int] = None
    session_type: Optional[str] = "general"  # general, security, it_support


class ChatResponse(BaseModel):
    response: str
    agent_used: str
    confidence: Optional[float] = None
    evidence: Optional[List[Dict[str, Any]]] = None
    mitre_mapping: Optional[Dict[str, str]] = None
    actions_taken: Optional[List[str]] = None
    session_id: int
    security_validated: bool = True
    blocked: bool = False
    block_reason: Optional[str] = None


class AgentAnalysisRequest(BaseModel):
    alert_id: Optional[int] = None
    incident_id: Optional[int] = None
    analysis_type: str = "full"  # triage, investigate, remediate, full


class AgentAnalysisResponse(BaseModel):
    triage: Optional[Dict[str, Any]] = None
    investigation: Optional[Dict[str, Any]] = None
    remediation: Optional[Dict[str, Any]] = None
    report: Optional[str] = None
    ticket_created: Optional[int] = None
    confidence: float = 0.0
    processing_time_ms: int = 0


class AgentActivityResponse(BaseModel):
    id: int
    agent_name: str
    action_type: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    confidence: float
    status: str
    duration_ms: Optional[int] = None
    related_alert_id: Optional[int] = None
    related_ticket_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
